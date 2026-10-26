import test from 'node:test';
import assert from 'node:assert/strict';
import {createPermanentPolicy,SERVICE_KEY} from '../desktop/linux/assets/controller-lab/media/remteh-gamepad/calibration-20261020b/service-mode.js';
const identity='a'.repeat(64),parameters=Array.from({length:12},(_,i)=>i+100);
function fixture(confirm=async()=>true) {
 const data=new Map(),storage={getItem:key=>data.get(key)??null,setItem:(key,value)=>data.set(key,value)};
 return {data,storage,policy:createPermanentPolicy(storage,confirm)};
}
test('normal diagnostics cannot authorize flash even with a backup',async()=>{
 const {policy}=fixture(),controller={};const backup=policy.preserve(identity,parameters);
 let wrote=false;await assert.rejects(policy.write(controller,identity,backup,()=>{wrote=true;}),/service_mode_required/);
 assert.equal(wrote,false);assert.throws(()=>policy.assertPermitted(controller),/service_mode_required/);
});
test('backup is persisted before confirmation and every flash',async()=>{
 let f;f=fixture(async()=>{assert.ok([...f.data.keys()].some(key=>key.includes('permanent-backup')));return true;});
 const {policy}=f,controller={};policy.setEnabled(true);const backup=policy.preserve(identity,parameters);
 await policy.write(controller,identity,backup,()=>policy.assertPermitted(controller));
 assert.throws(()=>policy.assertPermitted(controller),/service_mode_required/);
 const restored=createPermanentPolicy(f.storage,async()=>false);assert.equal(restored.enabled(),true);
});
test('confirmation, durable backup and current service state all gate writes',async()=>{
 const {policy,data}=fixture(async()=>false),controller={};policy.setEnabled(true);const backup=policy.preserve(identity,parameters);
 await assert.rejects(policy.write(controller,identity,backup,()=>assert.fail('must not write')),/confirmation_required/);
 data.delete([...data.keys()].find(key=>key.includes('permanent-backup')));
 await assert.rejects(policy.write(controller,identity,backup,()=>assert.fail('must not write')),/persistent_backup_required/);
});
test('turning service mode off during confirmation prevents flash',async()=>{
 let policy;({policy}=fixture(async()=>{policy.setEnabled(false);return true;}));policy.setEnabled(true);const backup=policy.preserve(identity,parameters);
 await assert.rejects(policy.write({},identity,backup,()=>assert.fail('must not write')),/service_mode_required/);
});
test('storage failure cannot be mistaken for a backup',()=>{
 const policy=createPermanentPolicy({getItem(){return null;},setItem(){throw new Error('disk full');}},async()=>true);
 assert.throws(()=>policy.preserve(identity,parameters),/disk full/);
});

test('English translation handles dynamic fragments without damaging Russian words',async()=>{
 const {createTranslator}=await import('../desktop/linux/assets/controller-lab/translation.js');
 const translate=createTranslator({'левый':'left','правый':'right','с':'s','Старт':'Start'});
 assert.equal(translate('Старт 25% · левый 2/4 · правый 1/4 · 3 с'),'Start 25% · left 2/4 · right 1/4 · 3 s');
 assert.equal(translate('стик'),'стик');
});
