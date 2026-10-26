import test from 'node:test';import assert from 'node:assert/strict';
import {createPermanentPolicy,createBaselineGate} from '../desktop/linux/assets/controller-lab/media/remteh-gamepad/calibration-20261020b/service-mode.js';
const id='c'.repeat(64),p=Array.from({length:12},(_,i)=>i+1);
function fixture(){const data=new Map();return {data,storage:{getItem:k=>data.get(k)??null,setItem:(k,v)=>data.set(k,v)}};}
test('earliest original survives more than three sessions and page reload',()=>{
 const {storage}=fixture();const original=createPermanentPolicy(storage,async()=>true).preserve(id,p);
 for(let i=0;i<8;i++)assert.deepEqual(createPermanentPolicy(storage,async()=>true).preserve(id,p.map(x=>x+i+1)),original);
});
test('legacy history migrates its earliest surviving values, without claiming factory',()=>{
 const {storage}=fixture();storage.setItem('deckivo:permanent-backup:v1:'+id,JSON.stringify({identity:id,original:p.map(x=>x+3),at:'later',history:[{original:p,at:'earliest'},{original:p.map(x=>x+1),at:'middle'}]}));
 const value=createPermanentPolicy(storage,async()=>true).preserve(id,p.map(x=>x+5));assert.deepEqual(value.original,p);assert.equal(value.provenance,'earliest-surviving-legacy');
});
test('corrupt existing backup is preserved and blocks overwrite',()=>{
 const {storage}=fixture();storage.setItem('deckivo:permanent-backup:v1:'+id,'broken');assert.throws(()=>createPermanentPolicy(storage,async()=>true).preserve(id,p),/backup/);assert.equal(storage.getItem('deckivo:permanent-backup:v1:'+id),'broken');
});
test('page reload and software reconnect cannot establish a fresh RAM baseline',async()=>{
 const gate=createBaselineGate();gate.connected(id);await assert.rejects(gate.require(id,async()=>true),/power_cycle/);
 gate.disconnected(id);await assert.rejects(gate.require(id,async()=>true),/power_cycle/);
 gate.connected(id);await assert.rejects(gate.require(id,async()=>false),/power_cycle/);
 await gate.require(id,async()=>true);await gate.require(id,async()=>{throw Error('asked twice');});
 const reload=createBaselineGate();reload.connected(id);await assert.rejects(reload.require(id,async()=>true),/power_cycle/);
});
test('another controller or disconnect during acknowledgement cannot authorize calibration',async()=>{
 const gate=createBaselineGate();gate.disconnected(id);gate.connected(id);
 await assert.rejects(gate.require('d'.repeat(64),async()=>true),/power_cycle/);
 await assert.rejects(gate.require(id,async()=>{gate.disconnected(id);return true;}),/power_cycle/);
});
