// Device-independent calibration mathematics. No DOM, storage, HID or network.
// USB coordinates are firmware output, not raw ADC measurements. An expanded,
// temporary range supplies uncensored observations; every prediction still needs
// a new physical verification before it may be offered for permanent storage.
export const AXES = [[0, 4, 8], [1, 5, 9], [2, 6, 10], [3, 7, 11]];
export const QUANTUM = 2 / 255;
const TAU = Math.PI * 2;
const SECTORS = 120;
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const mean = a => a.reduce((sum, x) => sum + x, 0) / a.length;
const rms = a => Math.sqrt(mean(a.map(x => x * x)));
const variance = a => a.length > 1 ? a.reduce((sum, x) => sum + (x - mean(a)) ** 2, 0) / (a.length - 1) : 0;
export const median = a => {
  const b = [...a].sort((x, y) => x - y);
  return b.length ? (b[(b.length - 1) >> 1] + b[b.length >> 1]) / 2 : NaN;
};
const angleDelta = a => Math.atan2(Math.sin(a), Math.cos(a));
export const decodeAxis = byte => byte / 127.5 - 1;
export const sameParameters = (a, b) => Array.isArray(a) && Array.isArray(b) && a.length === 12 && b.length === 12 && a.every((v, i) => v === b[i]);
export const validParameters = a => Array.isArray(a) && a.length === 12 && a.every(v => Number.isInteger(v) && v >= 0 && v <= 65535) && AXES.every(([lo, hi, c]) => a[c] - a[lo] >= 64 && a[hi] - a[c] >= 64);
export function boundedParameters(a, origin) {
  return validParameters(a) && validParameters(origin) && AXES.every(([lo, hi, c]) => Math.abs(a[c] - origin[c]) <= Math.min(origin[c] - origin[lo], origin[hi] - origin[c]) * .08 && [lo, hi].every(k => Math.abs(a[k] - origin[k]) <= Math.abs(origin[k] - origin[c]) * .2));
}
const rest = rows => AXES.map((_, i) => {
  const a = rows.map(row => row[i]), m = mean(a);
  return {mean: m, noise: rms(a.map(v => v - m))};
});

class Rotation {
  constructor(direction) { this.direction = direction; this.passes = []; this.reset(); }
  reset(arm = true) { this.arm = arm; this.last = null; this.time = null; this.start = null; this.travel = 0; this.bins = Array.from({length: SECTORS}, () => []); }
  add(x, y, time) {
    if (this.passes.length >= 2) return;
    if (Math.hypot(x, y) < .5) { this.reset(); return; }
    const angle = Math.atan2(y, x);
    if (this.last !== null) {
      const delta = angleDelta(angle - this.last) * this.direction;
      if (time - this.time > 150 || Math.abs(delta) > .28 || this.travel + delta < -.2) this.reset();
      else this.travel += delta;
    }
    if (this.last === null) this.start = time;
    this.last = angle; this.time = time;
    if (this.arm) {
      if (this.travel < Math.PI / 6 || time - this.start < 250) return;
      this.reset(false); this.last = angle; this.time = time; this.start = time;
    }
    const bin = Math.min(SECTORS - 1, Math.floor((angle + Math.PI) / TAU * SECTORS));
    if (this.bins[bin].length < 64) this.bins[bin].push([x, y]);
    if (this.travel >= TAU && time - this.start >= 1600 && this.bins.every(b => b.length >= 2)) {
      this.passes.push({direction: this.direction, points: this.bins.map(b => [median(b.map(p => p[0])), median(b.map(p => p[1]))])});
      this.reset(false);
    }
  }
  get progress() { return (this.passes.length + (this.arm ? 0 : clamp(this.travel / TAU, 0, .99))) / 2; }
}

const DIRECTIONS = ['вправо →', 'вправо-вниз ↘', 'вниз ↓', 'влево-вниз ↙', 'влево ←', 'влево-вверх ↖', 'вверх ↑', 'вправо-вверх ↗'];
export const RETURN_ANGLE = Math.PI / 9; // A visible 40-degree target, not an invisible 15-degree gate.
const HOLD_MS = 240, SETTLE_MS = 650, RELEASE_MS = 1200;

// Each stick owns its complete sequence. A finished left-stick movement never
// waits for the right stick, and a slow right stick cannot discard left data.
class StickCapture {
  constructor(probe, initialRest) {
    this.probe = probe; this.stage = 'cw'; this.turn = new Rotation(1);
    this.passes = []; this.holds = []; this.returns = [initialRest]; this.direction = 0;
    this.started = null; this.last = null; this.rows = []; this.elapsed = 0; this.inTarget = false;
  }
  pause() { this.started = null; this.last = null; this.rows = []; this.elapsed = 0; this.inTarget = false; this.turn.reset(); }
  transition(stage) { this.stage = stage; this.started = null; this.rows = []; this.elapsed = 0; this.inTarget = false; }
  get done() { return this.stage === 'done'; }
  get targetRadius() {
    if (this.radiusDirection === this.direction) return this.cachedRadius;
    const target = this.direction * Math.PI / 4;
    const radii = this.passes.flatMap(p => p.points.filter(v => Math.abs(angleDelta(Math.atan2(v[1], v[0]) - target)) <= RETURN_ANGLE).map(v => Math.hypot(...v)));
    this.radiusDirection = this.direction; this.cachedRadius = radii.length ? median(radii) : 1;
    return this.cachedRadius;
  }
  add(point, time, gap) {
    if (this.done) return;
    this.last = time;
    if (this.stage === 'cw' || this.stage === 'ccw') {
      this.turn.add(...point, time);
      if (this.turn.passes.length === 2) {
        this.passes.push(...this.turn.passes);
        if (this.stage === 'cw') { this.turn = new Rotation(-1); this.transition('ccw'); }
        else this.transition(this.probe ? 'release' : 'aim');
      }
      return;
    }
    if (this.stage === 'aim') {
      const target = this.direction * Math.PI / 4;
      this.inTarget = gap <= 150 && Math.hypot(...point) >= Math.max(.5, this.targetRadius * .88) && Math.abs(angleDelta(Math.atan2(point[1], point[0]) - target)) <= RETURN_ANGLE;
      if (!this.inTarget) { this.started = null; this.rows = []; this.elapsed = 0; return; }
      if (this.started === null) this.started = time;
      this.elapsed = time - this.started;
      if (this.rows.length < 500) this.rows.push([...point]);
      if (this.elapsed >= HOLD_MS && this.rows.length >= 40) {
        this.holds[this.direction] = [0, 1].map(a => median(this.rows.map(v => v[a])));
        this.transition('release');
      }
      return;
    }
    if (this.stage === 'release') {
      // Waiting for release is not a noise abort: drift/noise is measured and
      // reported. A held stick must not become a spurious center observation.
      if (Math.hypot(...point) > .45 || gap > 150) { this.started = null; this.rows = []; this.elapsed = 0; return; }
      if (this.started === null) this.started = time;
      this.elapsed = time - this.started;
      if (this.elapsed >= SETTLE_MS && this.rows.length < 1800) this.rows.push([...point]);
      if (this.elapsed >= RELEASE_MS && this.rows.length >= 100) {
        this.returns.push([0,1].map(i => {
          const values = this.rows.map(v => v[i]), m = mean(values);
          return {mean: m, noise: rms(values.map(v => v - m))};
        }));
        if (this.probe || ++this.direction === 8) this.transition('done');
        else this.transition('aim');
      }
    }
  }
  get actionProgress() {
    if (this.stage === 'cw' || this.stage === 'ccw') return this.turn.progress;
    if (this.stage === 'aim') return clamp(this.elapsed / HOLD_MS, 0, 1);
    if (this.stage === 'release') return clamp(this.elapsed / RELEASE_MS, 0, 1);
    return 1;
  }
  get progress() {
    if (this.done) return 1;
    if (this.stage === 'cw' || this.stage === 'ccw') return (this.stage === 'cw' ? 0 : .32) + this.turn.progress * .32;
    if (this.probe) return .64 + this.actionProgress * .36;
    return .64 + (this.direction + (this.stage === 'release' ? .3 + .7 * this.actionProgress : .3 * this.actionProgress)) / 8 * .36;
  }
  get instruction() {
    if (this.stage === 'cw') return '↻ Два круга по часовой стрелке';
    if (this.stage === 'ccw') return '↺ Два круга против часовой стрелки';
    if (this.stage === 'aim') return this.inTarget ? 'Удерживайте ещё мгновение' : 'До упора ' + DIRECTIONS[this.direction];
    if (this.stage === 'release') return this.elapsed ? 'Не трогайте стик — измеряем центр' : 'Отпустите стик';
    return '✓ Этот стик готов';
  }
  get detail() {
    if (this.stage === 'cw' || this.stage === 'ccw') return this.turn.passes.length + '/2 круга · примерно 3 секунды на круг';
    if (this.stage === 'aim') return 'Направление ' + (this.direction + 1) + '/8 · белая точка должна попасть в жёлтый сектор';
    if (this.stage === 'release') return (this.probe ? 'Завершаем замер' : 'Возврат ' + (this.direction + 1) + '/8') + ' · осталось ' + Math.max(0, (RELEASE_MS - this.elapsed) / 1000).toFixed(1) + ' с';
    return 'Можно закончить второй стик';
  }
}

export class CalibrationCapture {
  constructor({probe = false} = {}) {
    this.probe = probe; this.stage = 'rest'; this.started = null; this.last = null; this.samples = [];
    this.returns = []; this.lanes = []; this.done = false; this.result = null;
  }
  pause() {
    this.started = null; this.samples = []; this.last = null;
    this.lanes.forEach(lane => lane.pause());
  }
  add(axes, time) {
    if (this.done || !Array.isArray(axes) || axes.length !== 4 || axes.some(v => !Number.isFinite(v) || Math.abs(v) > 1.001) || !Number.isFinite(time)) return;
    if (this.last !== null && time - this.last < 2) return;
    const gap = this.last === null ? Infinity : time - this.last; this.last = time;
    if (this.stage === 'rest') {
      if (axes.some(v => Math.abs(v) > .6)) { this.started = null; this.samples = []; return; }
      if (this.started === null || gap > 150) { this.started = time; this.samples = []; }
      if (time - this.started >= 900 && this.samples.length < 1800) this.samples.push([...axes]);
      if (time - this.started >= 2600 && this.samples.length >= 100) {
        const initial = rest(this.samples); this.returns = [initial]; this.samples = [];
        this.lanes = [0,1].map(i => new StickCapture(this.probe, initial.slice(i*2, i*2+2))); this.stage = 'work';
      }
      return;
    }
    this.lanes.forEach((lane,i) => lane.add(axes.slice(i*2,i*2+2), time, gap));
    if (this.lanes.every(lane => lane.done)) {
      // Pair independent observations by release index, not by acquisition time.
      this.returns = this.lanes[0].returns.map((left, i) => [...left, ...this.lanes[1].returns[i]]);
      this.result = buildProfile(this.lanes.map(l=>l.passes), this.lanes.map(l=>l.holds), this.returns, this.probe, 'independent-sticks-v1');
      this.done = true; this.stage = 'done';
    }
  }
  get progress() {
    if (this.done) return 1;
    if (this.stage === 'rest') return this.started === null ? 0 : clamp((this.last - this.started) / 2600, 0, 1) * .06;
    return .06 + mean(this.lanes.map(l=>l.progress)) * .94;
  }
  get instruction() {
    if (this.stage === 'rest') return 'Положите геймпад и отпустите оба стика.';
    if (this.done) return 'Замер завершён.';
    return 'Следуйте подсказке над каждым стиком';
  }
  get detail() {
    if (this.stage === 'rest') return this.started === null ? 'Ждём отпускания стиков' : 'Начнём через ' + Math.max(0, (2600 - (this.last-this.started)) / 1000).toFixed(1) + ' с';
    if (this.done) return 'Все движения приняты';
    return 'Можно полностью пройти левый, затем правый — или двигать оба одновременно. Каждый шаг засчитывается отдельно.';
  }
  export() {
    return {protocol:'independent-sticks-v1',stage:this.stage,progress:this.progress,probe:this.probe,
      sticks:this.lanes.map(l=>({stage:l.stage,direction:l.direction,progress:l.progress,passes:[...l.passes,...(['cw','ccw'].includes(l.stage)?l.turn.passes:[])],holds:l.holds,returns:l.returns,
        partial_circle:['cw','ccw'].includes(l.stage)?l.turn.bins.map(b=>b.at(-1)??null):null}))};
  }
}

const radiusError = points => rms(points.map(p => Math.hypot(...p) - 1));
const travelFrom = holds => [Math.abs(holds[0][0]), Math.abs(holds[2][1]), Math.abs(holds[4][0]), Math.abs(holds[6][1])];
const measuredTravel = passes => [0, 2, 4, 6].map(d => {
  const angle = d * Math.PI / 4, axis = d % 4 === 0 ? 0 : 1;
  return Math.min(...passes.map(pass => {
    const near = pass.points.filter(p => Math.abs(angleDelta(Math.atan2(p[1],p[0]) - angle)) < Math.PI / 15);
    return near.length ? Math.max(...near.map(p => Math.abs(p[axis]))) : 0;
  }));
});
export function buildProfile(passes, holds, returns, probe = false, protocol = 'ordered-pair-v1') {
  const axes = AXES.map((_, i) => ({mean: median(returns.map(r => r[i].mean)), noise: Math.max(...returns.map(r => r[i].noise))}));
  const sticks = passes.map((all, i) => {
    const points = Array.from({length: SECTORS}, (_, k) => [0, 1].map(a => median(all.map(pass => pass.points[k][a]))));
    const errors = points.map(p => Math.abs(Math.hypot(...p) - 1));
    const spreadBySector = points.map((p, k) => rms(all.map(pass => Math.hypot(...pass.points[k]) - Math.hypot(...p))));
    const centers = returns.map(r => r.slice(i * 2, i * 2 + 2).map(a => a.mean));
    const c = axes.slice(i * 2, i * 2 + 2).map(a => a.mean);
    const cardinal = protocol === 'independent-sticks-v1' ? measuredTravel(all) : probe ? [0, 2, 4, 6].map(d => {
      const target = d * Math.PI / 4;
      const near = points.filter(p => Math.abs(angleDelta(Math.atan2(p[1], p[0]) - target)) < Math.PI / 24);
      return near.length ? Math.max(...near.map(p => Math.abs(p[d % 4 === 0 ? 0 : 1]))) : 0;
    }) : travelFrom(holds[i]);
    return {points, passes: all, holds: holds[i], centers, rms: radiusError(points), worst: Math.max(...errors),
      p95: [...errors].sort((a, b) => a - b)[Math.floor(SECTORS * .95)],
      passRms: all.map(pass => radiusError(pass.points)), repeat: rms(spreadBySector), spread: Math.max(...spreadBySector),
      center: Math.hypot(...c), returnWorst: Math.max(...centers.map(p => Math.hypot(...p))),
      returnSpread: Math.max(...centers.map(p => Math.hypot(p[0] - c[0], p[1] - c[1]))),
      noise: Math.hypot(...axes.slice(i * 2, i * 2 + 2).map(a => a.noise)), travel: cardinal,
      clipped: points.filter(p => p.some(v => Math.abs(v) >= 1 - 1e-10)).length};
  });
  return {version: 2, axisScale: 'usb-u8-full-range', protocol, probe, axes, returns, sticks};
}

export function validProfile(p, {allowProbe = false} = {}) {
  const vector = (a, n) => Array.isArray(a) && a.length === n && a.every(v => Number.isFinite(v) && Math.abs(v) <= 1.001);
  const axis = a => a && Number.isFinite(a.mean) && Math.abs(a.mean) <= 1.001 && Number.isFinite(a.noise) && a.noise >= 0 && a.noise <= 2;
  return (!p?.protocol || ['ordered-pair-v1','independent-sticks-v1'].includes(p.protocol)) && p?.version === 2 && p.axisScale === 'usb-u8-full-range' && (allowProbe || !p.probe) && Array.isArray(p.axes) && p.axes.length === 4 && p.axes.every(axis)
    && Array.isArray(p.returns) && p.returns.length === (p.probe ? 2 : 9) && p.returns.every(r => Array.isArray(r) && r.length === 4 && r.every(axis))
    && Array.isArray(p.sticks) && p.sticks.length === 2 && p.sticks.every(s =>
      ['rms', 'worst', 'p95', 'repeat', 'spread', 'center', 'returnWorst', 'returnSpread', 'noise'].every(k => Number.isFinite(s[k]) && s[k] >= 0 && s[k] <= 3)
      && Array.isArray(s.points) && s.points.length === SECTORS && s.points.every(v => vector(v, 2))
      && Array.isArray(s.passes) && s.passes.length === 4 && s.passes.every((r, i) => r.direction === (i < 2 ? 1 : -1) && Array.isArray(r.points) && r.points.length === SECTORS && r.points.every(v => vector(v, 2)))
      && Array.isArray(s.centers) && s.centers.length === p.returns.length && s.centers.every(v => vector(v, 2))
      && Number.isInteger(s.clipped) && s.clipped >= 0 && s.clipped <= SECTORS
      && vector(s.passRms, 4) && vector(s.travel, 4) && Array.isArray(s.holds) && s.holds.length === (p.probe ? 0 : 8) && s.holds.every(v => vector(v, 2)));
}

// Never infer an exact sensor endpoint from a saturated 0/255 report.
export function makeProbe(parameters, origin, expansion = .12) {
  if (!boundedParameters(parameters, origin)) return null;
  const probe = [...parameters];
  for (const [lo, hi, c] of AXES) {
    for (const k of [lo, hi]) {
      const sign = k === lo ? -1 : 1;
      const target = parameters[k] + sign * Math.abs(parameters[k] - parameters[c]) * expansion;
      const low = Math.max(0, Math.ceil(origin[k] - Math.abs(origin[k] - origin[c]) * .2));
      const high = Math.min(65535, Math.floor(origin[k] + Math.abs(origin[k] - origin[c]) * .2));
      probe[k] = clamp(Math.round(target), low, high);
      if (Math.abs(probe[k] - parameters[k]) < Math.abs(parameters[k] - parameters[c]) * .035) return null;
    }
  }
  return boundedParameters(probe, origin) ? probe : null;
}

function toSensorEstimate(v, axis, parameters) {
  const [lo, hi, c] = AXES[axis];
  return parameters[c] + v * (v < 0 ? parameters[c] - parameters[lo] : parameters[hi] - parameters[c]);
}
function fromSensorEstimate(v, axis, parameters) {
  const [lo, hi, c] = AXES[axis];
  return clamp((v - parameters[c]) / (v < parameters[c] ? parameters[c] - parameters[lo] : parameters[hi] - parameters[c]), -1, 1);
}

export function fitCalibration(baseline, initial, probe, probeParameters, origin) {
  if (!validProfile(baseline) || !validProfile(probe, {allowProbe: true}) || !probe.probe || !boundedParameters(initial, origin) || !boundedParameters(probeParameters, origin)) return {ok: false, reason: 'invalid_measurement'};
  if (probe.sticks.some(s => s.passes.some(p => p.points.some(row => row.some(v => Math.abs(v) >= 1 - 1e-10))))) return {ok: false, reason: 'still_clipped'};
  if (probe.sticks.some(s => s.repeat > .025 || s.spread > .08)) return {ok: false, reason: 'repeatability'};
  const rawPoints = probe.sticks.map((s, i) => s.points.map(p => p.map((v, a) => toSensorEstimate(v, i * 2 + a, probeParameters))));
  const rawReturns = baseline.returns.map(r => r.map((v, axis) => toSensorEstimate(v.mean, axis, initial)));
  const endpoints = AXES.map((_, axis) => {
    const stick = probe.sticks[axis >> 1], a = axis % 2;
    const side = sign => {
      const ends = stick.passes.map(pass => {
        const near = pass.points.filter(p => Math.sign(p[a]) === sign && Math.abs(p[1 - a]) < Math.abs(p[a]) * .14);
        return near.length ? (sign < 0 ? Math.min : Math.max)(...near.map(p => toSensorEstimate(p[a], axis, probeParameters))) : NaN;
      });
      // The least-extreme of four complete passes preserves travel on every pass.
      return sign < 0 ? Math.max(...ends) : Math.min(...ends);
    };
    return [side(-1), side(1)];
  });
  if (endpoints.some(p => p.some(v => !Number.isFinite(v)) || p[1] - p[0] < 128)) return {ok: false, reason: 'missing_edge'};
  const candidate = [...initial];
  for (let axis = 0; axis < 4; axis++) {
    const [lo, hi, c] = AXES[axis], values = rawReturns.map(r => r[axis]);
    const margin = Math.min(origin[c] - origin[lo], origin[hi] - origin[c]) * .08;
    candidate[c] = clamp(Math.round((Math.min(...values) + Math.max(...values)) / 2), Math.ceil(origin[c] - margin), Math.floor(origin[c] + margin));
    candidate[lo] = Math.round(endpoints[axis][0]); candidate[hi] = Math.round(endpoints[axis][1]);
    for (const k of [lo, hi]) candidate[k] = clamp(candidate[k], Math.max(0, Math.ceil(origin[k] - Math.abs(origin[k] - origin[c]) * .2)), Math.min(65535, Math.floor(origin[k] + Math.abs(origin[k] - origin[c]) * .2)));
  }
  const feasible = params => boundedParameters(params, origin) && endpoints.every((ends, axis) => ends.every((v, side) => Math.abs(fromSensorEstimate(v, axis, params)) >= 1 - QUANTUM / 2 && Math.sign(v - params[AXES[axis][2]]) === (side ? 1 : -1)));
  if (!feasible(candidate)) return {ok: false, reason: 'bounds'};
  const score = params => rawPoints.reduce((sum, points, i) => {
    const errors = points.map(p => Math.abs(Math.hypot(...p.map((v, a) => fromSensorEstimate(v, i * 2 + a, params))) - 1));
    return sum + rms(errors) + .2 * Math.max(...errors);
  }, 0);
  let best = candidate, loss = score(candidate);
  // Deterministic bounded descent, with simultaneous center shifts already made.
  // This optimizes a physical-parameter model; it never warps the plotted data.
  for (const fraction of [.02, .005, .001, 0]) {
    for (let iteration = 0; iteration < 8; iteration++) {
      let changed = false;
      for (const [lo, hi, c] of AXES) for (const k of [lo, hi]) for (const sign of [-1, 1]) {
        const next = [...best], step = Math.max(1, Math.round(Math.abs(initial[k] - initial[c]) * fraction));
        next[k] += sign * step;
        if (!feasible(next)) continue;
        const value = score(next);
        if (value < loss - 1e-8) { best = next; loss = value; changed = true; }
      }
      if (!changed) break;
    }
  }
  return {ok: true, parameters: best, predictedRms: rawPoints.map((p, i) => radiusError(p.map(row => row.map((v, a) => fromSensorEstimate(v, i * 2 + a, best))))), endpoints, source: 'expanded-range-estimate', quantization: QUANTUM};
}

function circleUncertainty(a, b) {
  const directionBias = s => Math.abs(mean(s.passRms.slice(0, 2)) - mean(s.passRms.slice(2)));
  // Whole revolutions are the experimental units. Angular bins are correlated
  // and must not be treated as hundreds of independent repeat measurements.
  return Math.max(.003, 3.182 * Math.sqrt(variance(a.passRms) / 4 + variance(b.passRms) / 4), directionBias(a) / 2, directionBias(b) / 2);
}
function controlTravelEvidence(before, after) {
  if (before.protocol !== 'independent-sticks-v1' || after.protocol !== 'independent-sticks-v1') return [];
  const labels = ['CW1', 'CW2', 'CCW1', 'CCW2'], evidence = [];
  for (let stick = 0; stick < 2; stick++) for (let direction = 0; direction < 4; direction++) {
    const threshold = Math.min(.995, before.sticks[stick].travel[direction]) - QUANTUM;
    if (after.sticks[stick].travel[direction] >= threshold) continue;
    const angle = direction * Math.PI / 2, axis = direction % 2;
    const passes = after.sticks[stick].passes.map((pass, index) => {
      const near = pass.points.filter(point => Math.abs(angleDelta(Math.atan2(point[1], point[0]) - angle)) < Math.PI / 15);
      return {label: labels[index], value: near.length ? Math.max(...near.map(point => Math.abs(point[axis]))) : 0};
    });
    const hold = Math.abs(after.sticks[stick].holds[direction * 2][axis]);
    const observations = [...passes.map(pass => pass.value), hold];
    const confirming = observations.filter(value => value >= threshold).length;
    evidence.push({stick, direction, passes, hold, threshold, reached: Math.max(...observations), worstCircle: Math.min(...passes.map(pass => pass.value)), confirming,
      fullTravelConfirmed: confirming >= 3 && Math.max(...observations) >= .995});
  }
  return evidence;
}
export function assessCalibration(before, after, {control = false} = {}) {
  if (!validProfile(before) || !validProfile(after)) return {accepted: false, reason: 'invalid_measurement', improvements: []};
  const improvements = [], uncertainty = [], travelEvidence = control ? controlTravelEvidence(before, after) : [];
  for (let i = 0; i < 2; i++) {
    const a = before.sticks[i], b = after.sticks[i], u = circleUncertainty(a, b); uncertainty.push(u);
    if (b.repeat > Math.max(.025, a.repeat + .005) || b.spread > Math.max(.08, a.spread + .02)) return {accepted: false, reason: 'repeatability', improvements, uncertainty};
    if (b.travel.some((v, j) => v < Math.min(.995, a.travel[j]) - QUANTUM)) {
      const inconsistent = travelEvidence.length && travelEvidence.every(item => item.fullTravelConfirmed);
      return {accepted: false, reason: inconsistent ? 'travel_inconsistent' : 'lost_travel', improvements, uncertainty, travelEvidence};
    }
    if (b.returnWorst > a.returnWorst + QUANTUM * 1.5 || b.returnSpread > a.returnSpread + QUANTUM * 1.5 || b.noise > a.noise + QUANTUM) return {accepted: false, reason: 'worse_return', improvements, uncertainty};
    if (b.rms > a.rms + Math.max(.004, u / 2) || b.worst > a.worst + Math.max(.01, u)) return {accepted: false, reason: 'worse_circle', improvements, uncertainty};
    if (a.rms - b.rms > u) improvements.push({stick: i, kind: 'circle', gain: a.rms - b.rms});
    // Centering claims use the worst of nine separate releases, not a lucky rest.
    if (a.returnWorst - b.returnWorst > Math.max(QUANTUM, a.noise * 2, b.noise * 2)) improvements.push({stick: i, kind: 'center', gain: a.returnWorst - b.returnWorst});
  }
  return {accepted: control || improvements.length > 0, reason: control ? 'verified' : improvements.length ? 'improved' : 'not_significant', improvements, uncertainty};
}
