// Claude independent tests: permanent-write policy (mock only, no hardware).
import test from 'node:test'; import assert from 'node:assert/strict';
const SRC = new URL('../desktop/linux/assets/controller-lab/media/remteh-gamepad/calibration-20261020b/service-mode.js',import.meta.url).href;
const {createPermanentPolicy} = await import(SRC);
const mem = () => { const m = new Map(); return {getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,String(v))}; };
const ID = 'a'.repeat(64), P = [1,2,3,4,5,6,7,8,9,10,11,12];
test('write blocked when service mode off (default)', async () => {
  const s=mem(); const pol=createPermanentPolicy(s, async()=>true); let ran=false;
  assert.equal(pol.enabled(), false);
  const rec=pol.preserve(ID,P);
  await assert.rejects(pol.write({},ID,rec,()=>{ran=true;}), /service_mode_required/); assert.equal(ran,false);
});
test('low-level flash outside an approved write is refused', () => {
  const s=mem(); const pol=createPermanentPolicy(s, async()=>true); pol.setEnabled(true);
  assert.throws(()=>pol.assertPermitted({}), /service_mode_required/);
});
test('cancel in dialog blocks write', async () => {
  const s=mem(); const pol=createPermanentPolicy(s, async()=>false); pol.setEnabled(true); const rec=pol.preserve(ID,P); let ran=false;
  await assert.rejects(pol.write({},ID,rec,()=>{ran=true;}), /confirmation_required/); assert.equal(ran,false);
});
test('disabling service mode while dialog is open blocks write', async () => {
  const s=mem(); let pol; pol=createPermanentPolicy(s, async()=>{ pol.setEnabled(false); return true; }); pol.setEnabled(true);
  const rec=pol.preserve(ID,P); let ran=false;
  await assert.rejects(pol.write({},ID,rec,()=>{ran=true;}), /service_mode_required/); assert.equal(ran,false);
});
test('missing or tampered backup blocks write', async () => {
  const s=mem(); const pol=createPermanentPolicy(s, async()=>true); pol.setEnabled(true);
  await assert.rejects(pol.write({},ID,null,()=>{}), /persistent_backup_required/);
  const rec=pol.preserve(ID,P); s.setItem('deckivo:permanent-backup:v1:'+ID, JSON.stringify({...rec,original:[0,0,0,0,0,0,0,0,0,0,0,0]}));
  await assert.rejects(pol.write({},ID,rec,()=>{}), /persistent_backup_required/);
});
test('permit exists only during the approved operation', async () => {
  const s=mem(); const pol=createPermanentPolicy(s, async()=>true); pol.setEnabled(true); const ctrl={};
  const rec=pol.preserve(ID,P);
  await pol.write(ctrl,ID,rec,()=>{ pol.assertPermitted(ctrl); });
  assert.throws(()=>pol.assertPermitted(ctrl), /service_mode_required/);
});
