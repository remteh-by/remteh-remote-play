import {CalibrationCapture, decodeAxis, makeProbe, fitCalibration, assessCalibration, validParameters, boundedParameters, validProfile, sameParameters, buildProfile} from './calibration-core.js';

import {loadTuningBackup} from './calibration-backup-v1.js';
import {calibrationErrorCode} from './calibration-errors.js';

const storageKey = id => 'remteh:calibration:v2:' + id;
const clone = value => JSON.parse(JSON.stringify(value));
export function loadCalibration(storage, identity) {
  const raw = storage.getItem(storageKey(identity));
  if (!raw) return null;
  if (raw.length > 2000000) throw new Error('backup_invalid');
  let record;
  try { record = JSON.parse(raw); } catch { throw new Error('backup_invalid'); }
  if (!record || record.version !== 2 || record.identity !== identity || !validParameters(record.original)
    || !boundedParameters(record.checkpoint?.parameters, record.original)
    || (record.checkpoint.profile && !validProfile(record.checkpoint.profile))
    || (record.baseline && !validProfile(record.baseline))
    || (record.verification && (!validProfile(record.verification.profile)
      || (record.verification.powerCycleConfirmed !== undefined && record.verification.powerCycleConfirmed !== true)))
    || (record.saveIntent && (!boundedParameters(record.saveIntent.parameters, record.original) || !validProfile(record.saveIntent.profile)))
    || (record.pending && !boundedParameters(record.pending.parameters, record.original))
    || (record.saved && (!boundedParameters(record.saved.parameters, record.original) || !validProfile(record.saved.profile)))
    || !Array.isArray(record.history) || record.history.length > 3) throw new Error('backup_invalid');
  // Rebuild all derived values from the stored observations. Cached summary
  // numbers are presentation, never authority for a later hardware decision.
  const rebuild = profile => profile ? buildProfile(profile.sticks.map(s=>s.passes), profile.sticks.map(s=>s.holds), profile.returns, profile.probe, profile.protocol) : null;
  record.baseline = rebuild(record.baseline);
  record.checkpoint.profile = rebuild(record.checkpoint.profile);
  if (record.saved) record.saved.profile = rebuild(record.saved.profile);
  if (record.saveIntent) record.saveIntent.profile = rebuild(record.saveIntent.profile);
  if (record.verification) record.verification.profile = rebuild(record.verification.profile);
  return record;
}
export function storeCalibration(storage, record) {
  try {
    const value = JSON.stringify(record);
    if (value.length > 2000000) throw new Error('size');
    storage.setItem(storageKey(record.identity), value);
    if (storage.getItem(storageKey(record.identity)) !== value) throw new Error('readback');
  } catch { throw new Error('storage_failed'); }
}

export class CalibrationRunner {
  constructor({engine, storage, onChange = () => {}, now = () => new Date().toISOString()}) {
    this.engine = engine; this.storage = storage; this.onChange = onChange; this.now = now;
    this.phase = 'idle'; this.busy = false; this.active = false; this.capture = null; this.record = null;
    this.snapshot = null; this.parameters = null; this.baseline = null; this.result = null; this.trial = null;
    this.probe = null; this.proposal = null; this.probeParameters = null; this.initial = null;
    this.reason = null; this.verdict = null; this.cancelled = false; this.canSave = false; this.generation = 0;
    this.sessionId = typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : String(Date.now());
  }
  emit() { this.onChange(this); }
  persist() {
    try { storeCalibration(this.storage(), this.record); }
    catch (error) { if (this.durableRecord) this.record = clone(this.durableRecord); throw error; }
    this.durableRecord = clone(this.record);
  }
  connected() { return Boolean(this.engine()?.state.connected); }
  ownsConnection() { return this.connected() && this.snapshot?.connection === this.engine().connection && this.record?.identity === this.engine().state.info?.tuningId; }
  check() { if (!this.ownsConnection()) throw new Error('disconnected'); }
  async perform(operation) {
    if (this.busy) return false;
    this.busy = true; this.reason = null; this.emit();
    const token = ++this.generation;
    try { await operation(); return true; }
    catch (error) {
      if (token === this.generation) {
        this.capture = null; this.canSave = false;
        // A failed read/open is not evidence of a physical USB disconnect.
        this.reason = calibrationErrorCode(error);
        this.phase = this.reason === 'disconnected' ? 'paused' : 'error';
        if (!this.ownsConnection()) this.active = false;
        // No trial has started in these stages. Close a faulted read-only
        // session so the next click does not keep failing on a stale fault.
        if (!this.active && this.engine()?.state.fault && !this.engine().state.mode) {
          await this.engine().disconnect().catch(() => {});
        }
      }
      return false;
    } finally {
      if (token === this.generation) { this.busy = false; this.emit(); }
    }
  }
  inspect(identity) {
    if (this.active || this.busy) return;
    this.record = loadCalibration(this.storage(), identity); this.durableRecord = this.record ? clone(this.record) : null;
    const savedAtCheckpoint = this.record?.saved && sameParameters(this.record.saved.parameters, this.record.checkpoint.parameters);
    const restoredVerification = !this.record?.saveIntent && !this.record?.pending && savedAtCheckpoint
      && this.record.verification?.powerCycleConfirmed === true
      && sameParameters(this.record.verification.parameters, this.record.saved.parameters)
      ? assessCalibration(this.record.saved.profile, this.record.verification.profile, {control: true}) : null;
    this.snapshot = null; this.parameters = null; this.trial = null; this.verdict = restoredVerification;
    this.probe = null; this.proposal = null; this.probeParameters = null; this.initial = null;
    this.baseline = restoredVerification ? this.record.saved.profile : this.record?.baseline ?? null;
    this.result = restoredVerification ? this.record.verification.profile : this.record?.checkpoint?.profile ?? this.record?.saved?.profile ?? null;
    this.phase = this.record?.saveIntent ? 'save-uncertain' : this.record?.pending ? 'recovery' : restoredVerification ? restoredVerification.accepted ? 'verified' : 'control-failed' : savedAtCheckpoint ? 'saved' : this.record?.checkpoint.profile ? 'temporary' : 'idle';
    this.reason = restoredVerification?.reason ?? null; this.canSave = false; this.emit();
  }
  async acquire({verification = false} = {}) {
    const engine = this.engine();
    if (!engine) throw new Error('engine_unavailable');
    // connect() is called from the original click, before storage or lock awaits.
    if (!engine.state.connected) {
      this.phase = 'connecting'; this.emit();
      await engine.connect();
      if (this.cancelled) { this.phase = 'stopped'; this.reason = 'cancelled'; return false; }
    }
    this.phase = 'preparing'; this.emit();
    if (engine.state.info?.model !== 'DS5' || !engine.state.info?.tuningId) throw new Error('tuning_unavailable');
    const identity = engine.state.info.tuningId;
    this.record = loadCalibration(this.storage(), identity); this.durableRecord = this.record ? clone(this.record) : null;
    const legacy = this.record ? null : loadTuningBackup(this.storage(), identity);
    const original = this.record?.original ?? legacy?.original;
    this.snapshot = await engine.beginTuning(original ? {identity, parameters: original} : null);
    this.parameters = [...this.snapshot.parameters]; this.active = true;
    if (!this.record) this.record = {version: 2, identity, original: [...(original ?? this.parameters)], baseline: null,
      checkpoint: {parameters: [...(legacy?.pending ? legacy.best.parameters : this.parameters)], profile: null}, pending: legacy?.pending ? {parameters: [...legacy.pending], purpose: 'legacy-interrupted-trial', at: this.now()} : null, saved: null, history: [], createdAt: this.now()};
    if (this.record.pending && sameParameters(this.parameters, this.record.checkpoint.parameters)) this.record.pending = null;
    try { this.persist(); } catch (error) { engine.endTuning(); this.active = false; throw error; }
    if (this.cancelled) {
      engine.endTuning(); this.active = false; this.phase = 'stopped'; this.reason = 'cancelled';
      return false;
    }
    if (this.record.saveIntent && !verification) { this.phase = 'save-uncertain'; this.reason = 'save_unknown'; return false; }
    if (this.record.pending) { this.phase = 'recovery'; this.reason = 'interrupted_trial'; return false; }
    return true;
  }
  beginCapture(phase, probe = false) {
    this.capture = new CalibrationCapture({probe}); this.phase = phase; this.canSave = false;
    this.reason = null; this.emit();
  }
  async start() {
    if (this.active || this.busy) return false;
    this.cancelled = false;
    return this.perform(async () => {
      if (!await this.acquire()) return;
      this.initial = [...this.parameters]; this.baseline = null; this.result = null; this.trial = null; this.verdict = null;
      this.probe = null; this.proposal = null; this.probeParameters = null;
      if (this.record.verification) { this.record.verification = null; this.persist(); }
      this.probeExpansion = .12; this.beginCapture('baseline');
    });
  }
  async write(parameters, purpose) {
    this.check();
    if (!boundedParameters(parameters, this.record.original)) throw new Error('tuning_bounds');
    this.record.pending = {parameters: [...parameters], purpose, at: this.now()}; this.record.verification = null; this.persist();
    this.snapshot = await this.engine().writeTuning(parameters, this.snapshot.revision);
    this.check();
    if (!sameParameters(parameters, this.snapshot.parameters)) throw new Error('tuning_readback_failed');
    this.parameters = [...this.snapshot.parameters];
  }
  async rollback() {
    this.check();
    const checkpoint = this.record.checkpoint;
    if (!sameParameters(this.parameters, checkpoint.parameters)) await this.write(checkpoint.parameters, 'rollback');
    this.record.pending = null; this.persist(); this.result = checkpoint.profile;
  }
  finish(phase, reason) {
    this.capture = null; this.phase = phase; this.reason = reason; this.canSave = false;
    if (this.ownsConnection()) this.engine().endTuning();
    this.active = false;
  }
  async beginProbe() {
    const parameters = makeProbe(this.initial, this.record.original, this.probeExpansion);
    if (!parameters) { await this.rollback(); this.finish('unchanged', 'probe_bounds'); return; }
    this.phase = 'writing'; this.emit(); await this.write(parameters, 'range-probe');
    if (this.cancelled) { await this.rollback(); this.finish('stopped', 'cancelled'); return; }
    this.probeParameters = [...this.parameters]; this.beginCapture('probe', true);
  }
  async complete(profile, phase) {
    this.check();
    if (phase !== this.phase) throw new Error('invalid_measurement');
    if (!validProfile(profile, {allowProbe: phase === 'probe'})) throw new Error('invalid_measurement');
    if (this.cancelled) { await this.rollback(); this.finish('stopped', 'cancelled'); return; }
    if (phase === 'baseline') {
      this.baseline = profile; this.result = profile;
      this.record.baseline = profile; this.record.checkpoint = {parameters: [...this.parameters], profile}; this.record.pending = null;
      if (!this.record.originalProfile && sameParameters(this.parameters, this.record.original)) this.record.originalProfile = profile;
      this.persist(); await this.beginProbe();
    } else if (phase === 'probe') {
      this.probe = profile;
      const fit = fitCalibration(this.baseline, this.initial, profile, this.probeParameters, this.record.original);
      if (!fit.ok) {
        if (fit.reason === 'still_clipped' && this.probeExpansion < .18) { this.probeExpansion = .18; await this.beginProbe(); return; }
        await this.rollback(); this.finish('unchanged', fit.reason); return;
      }
      if (sameParameters(fit.parameters, this.initial)) { await this.rollback(); this.finish('unchanged', 'at_optimum'); return; }
      this.proposal = fit; this.phase = 'writing'; this.emit(); await this.write(fit.parameters, 'candidate');
      if (this.cancelled) { await this.rollback(); this.finish('stopped', 'cancelled'); return; }
      this.beginCapture('verifying');
    } else if (phase === 'verifying') {
      this.trial = profile;
      this.verdict = assessCalibration(this.baseline, profile);
      this.record.history.push({at: this.now(), parameters: [...this.parameters], verdict: this.verdict, measured: profile});
      this.record.history = this.record.history.slice(-3);
      if (this.verdict.accepted) {
        this.result = profile; this.record.checkpoint = {parameters: [...this.parameters], profile}; this.record.pending = null;
        this.persist(); this.phase = 'ready'; this.canSave = true;
      } else { await this.rollback(); this.finish('unchanged', this.verdict.reason); }
    } else if (phase === 'control') {
      this.verdict = assessCalibration(this.record.saved.profile, profile, {control: true});
      this.result = profile;
      this.record.verification = {at: this.now(), parameters: [...this.parameters], accepted: this.verdict.accepted, powerCycleConfirmed: true, profile}; this.persist();
      this.finish(this.verdict.accepted ? 'verified' : 'control-failed', this.verdict.reason);
    } else if (phase === 'restore-check') {
      this.result = profile; this.record.checkpoint = {parameters: [...this.parameters], profile}; this.record.pending = null;
      this.persist(); this.phase = 'restored'; this.canSave = true;
    }
  }
  accept(frame) {
    if (!this.capture || this.busy || !this.ownsConnection() || frame.connection !== this.snapshot.connection) return;
    const bytes = frame.axisBytes;
    if (!Array.isArray(bytes) || bytes.length !== 4 || bytes.some(b => !Number.isInteger(b) || b < 0 || b > 255)) return;
    this.capture.add(bytes.map(decodeAxis), frame.at);
  }
  tick() {
    if (this.active && !this.ownsConnection() && !this.busy) {
      this.capture = null; this.active = false; this.canSave = false; this.phase = 'paused'; this.reason = 'disconnected'; this.emit();
    }
    if (this.capture?.done && !this.busy) {
      const {result} = this.capture, phase = this.phase; this.capture = null;
      void this.perform(() => this.complete(result, phase));
    }
  }
  pauseCapture() { this.capture?.pause(); this.emit(); }
  async cancel() {
    this.cancelled = true;
    if (this.busy) return;
    return this.perform(async () => {
      this.capture = null;
      if (this.active && this.ownsConnection() && this.record.pending) {
        if (!sameParameters(this.parameters, this.record.pending.parameters) && !sameParameters(this.parameters, this.record.checkpoint.parameters)) throw new Error('tuning_external_change');
        await this.rollback();
      }
      // Accepted temporary settings stay as the last verified checkpoint.
      // Saved/verified results survive closing the wizard.
      const phase = ['verified', 'saved', 'save-uncertain', 'ready', 'restored'].includes(this.phase) ? this.phase : 'stopped';
      const save = this.canSave;
      this.finish(phase, phase === 'stopped' ? 'cancelled' : null);
      this.canSave = false;
      if (save) this.reason = 'temporary_checked';
    });
  }
  async recover() {
    this.cancelled = false;
    return this.perform(async () => {
      if (!this.active) await this.acquire();
      if (this.record.saveIntent) { this.finish('save-uncertain', 'save_unknown'); return; }
      this.check(); await this.rollback(); this.finish('stopped', 'recovered');
    });
  }
  async restore() {
    this.cancelled = false;
    return this.perform(async () => {
      if (this.record?.saveIntent || this.capture || (this.active && !['ready', 'restored', 'error'].includes(this.phase))) return;
      if (!this.active && !await this.acquire()) return;
      this.capture = null; this.check(); await this.write(this.record.original, 'restore-original');
      this.beginCapture('restore-check');
    });
  }
  async save() {
    return this.perform(async () => {
      this.check();
      if (!this.canSave || !['ready', 'restored'].includes(this.phase) || !validProfile(this.result) || this.record.pending || !sameParameters(this.parameters, this.record.checkpoint.parameters)) throw new Error('measurements_required');
      this.phase = 'saving'; this.emit();
      // A failed/unknown NVS write must never be blindly retried on reconnect.
      this.record.saveIntent = {at: this.now(), parameters: [...this.parameters], profile: this.result, session: this.sessionId, connection: this.snapshot.connection}; this.persist();
      await this.engine().saveTuning({verified: true, parameters: [...this.parameters], connection: this.snapshot.connection, revision: this.snapshot.revision});
      this.check();
      this.record.saved = {at: this.now(), parameters: [...this.parameters], profile: this.result, session: this.sessionId, connection: this.snapshot.connection};
      this.record.saveIntent = null; this.record.verification = null;
      let failed = false; try { this.persist(); } catch { failed = true; }
      this.finish('saved', failed ? 'saved_storage_failed' : null);
    });
  }
  async verify({powerCycleConfirmed = false} = {}) {
    this.cancelled = false;
    if (!powerCycleConfirmed) {
      this.phase = this.record?.saveIntent ? 'save-uncertain' : this.record?.saved ? 'saved' : this.phase;
      this.reason = 'power_cycle_confirmation_required'; this.emit(); return false;
    }
    return this.perform(async () => {
      if (this.active) { this.check(); this.engine().endTuning(); this.active = false; }
      if (!await this.acquire({verification: true})) return;
      const saved = this.record.saveIntent ?? this.record.saved;
      if (!saved) throw new Error('no_saved_profile');
      if (saved.session === this.sessionId && saved.connection === this.snapshot.connection) { this.finish(this.record.saveIntent ? 'save-uncertain' : 'saved', 'reconnect_first'); return; }
      if (!sameParameters(saved.parameters, this.parameters)) { this.record.saveIntent = null; this.record.verification = null; this.baseline = null; this.result = null; this.trial = null; this.verdict = null; this.persist(); this.finish('control-failed', 'saved_parameters_differ'); return; }
      if (this.record.saveIntent) { this.record.saved = this.record.saveIntent; this.record.saveIntent = null; }
      this.record.verification = null; this.persist();
      this.baseline = this.record.saved.profile; this.result = null; this.trial = null; this.verdict = null;
      this.beginCapture('control');
    });
  }
  export() {
    return {format: 'remteh-calibration-v2', generated_at: this.now(), device: this.engine()?.state.info?.fields ?? {},
      original_parameters: this.record?.original ?? null, current_parameters: this.ownsConnection() ? this.parameters : null,
      phase: this.phase, reason: this.reason, verdict: this.verdict, capture: this.capture?.export() ?? null, probe: this.probe ?? null, probe_parameters: this.probeParameters ?? null, baseline: this.baseline, result: this.result, trial: this.trial, proposal: this.proposal ?? null,
      save_intent: this.record?.saveIntent ?? null, saved: this.record?.saved ?? null, verification: this.record?.verification ?? null, pending: this.record?.pending ?? null,
      history: this.record?.history ?? [], interpretation: 'Measured USB output; sensor reconstruction and proposal are estimates, not measurements.'};
  }
}
