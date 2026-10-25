// Compatibility reader for existing v1 backups; the v2 wizard never runs the old optimizer.
import {validProfile,validParameters,boundedParameters} from './circle-profile.js';
const key=id=>'remteh:circle-tuning:v1:'+id;
const same=(a,b)=>Array.isArray(a)&&Array.isArray(b)&&a.length===12&&b.length===12&&a.every((x,i)=>x===b[i]);
export function loadTuningBackup(storage,id){
 const raw=storage.getItem(key(id));if(!raw)return null;
 const r=JSON.parse(raw);
 if(raw.length>150000||r.version!==1||r.identity!==id||!validParameters(r.original)||!boundedParameters(r.best?.parameters,r.original)||(r.pending&&!boundedParameters(r.pending,r.original))||(r.baseline&&!validProfile(r.baseline))||(r.best?.profile&&!validProfile(r.best.profile))||(r.saved&&(!boundedParameters(r.saved.parameters,r.original)||!validProfile(r.saved.profile))))throw new Error('tuning_backup_mismatch');
 if(r.attempts!==undefined&&(!Array.isArray(r.attempts)||r.attempts.length>6||r.attempts.some(x=>typeof x.reason!=='string'||x.reason.length>400||typeof x.accepted!=='boolean'||!['before','after'].every(k=>Array.isArray(x[k])&&x[k].length===2&&x[k].every(s=>['rms','center','repeat','worst','noise'].every(f=>Number.isFinite(s[f])&&s[f]>=0))))))throw new Error('tuning_backup_mismatch');
 return r;
}
export function persistTuningBackup(storage,record){
 try{const value=JSON.stringify(record);storage.setItem(key(record.identity),value);if(storage.getItem(key(record.identity))!==value)throw new Error();}
 catch{throw new Error('storage_failed');}
}
// Pending is an intent journal, not proof that this browser wrote the values.
// A reconnect may only read it: recovery always requires an explicit UI action.
export async function openTuningSession(storage,engine,id){
 let record=loadTuningBackup(storage,id);
 const snapshot=await engine.beginTuning(record?{identity:id,parameters:record.original}:null);
 const current=[...snapshot.parameters];
 if(!record)record={version:1,identity:id,original:[...snapshot.original],baseline:null,best:{parameters:[...current],profile:null},pending:null,createdAt:new Date().toISOString()};
 if(record.pending&&same(current,record.best.parameters))record.pending=null;
 try{persistTuningBackup(storage,record);}catch(error){engine.endTuning();throw error;}
 return {record,snapshot,current,recoveryRequired:Boolean(record.pending)};
}
