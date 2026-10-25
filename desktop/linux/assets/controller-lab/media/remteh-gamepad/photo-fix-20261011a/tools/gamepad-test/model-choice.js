const STORAGE_KEY='remteh.gamepad.model-choice.v1';
const VERSION=1;
const LIMIT=12;
const MODELS=new Set(['xbox-series','xbox-one','dualsense','ds4']);

const count=value=>Number.isFinite(value?.length)?value.length:0;

export function controllerFingerprint(gamepad){
  if(!gamepad)return '';
  return JSON.stringify([VERSION,String(gamepad.id??'').trim(),String(gamepad.mapping??''),count(gamepad.axes),count(gamepad.buttons)]);
}

export function matchingFingerprintCount(gamepads,fingerprint){
  if(!fingerprint)return 0;
  return [...(gamepads??[])].filter(gamepad=>gamepad?.connected!==false&&controllerFingerprint(gamepad)===fingerprint).length;
}

function browserStorage(){
  try{return globalThis.localStorage??null;}catch{return null;}
}

function clean(raw){
  if(!raw||raw.version!==VERSION||!Array.isArray(raw.choices))return [];
  return raw.choices.filter(item=>item&&typeof item.fingerprint==='string'&&MODELS.has(item.model)).map(item=>({fingerprint:item.fingerprint,model:item.model,updatedAt:Number(item.updatedAt)||0}));
}

export function createModelChoiceStore(storage=browserStorage()){
  let cached=null;
  const read=()=>{
    if(cached)return cached;
    if(!storage)return cached=[];
    try{return cached=clean(JSON.parse(storage.getItem(STORAGE_KEY)??'null'));}catch{return cached=[];}
  };
  const write=choices=>{
    cached=choices.sort((a,b)=>b.updatedAt-a.updatedAt).slice(0,LIMIT);
    if(!storage)return;
    try{storage.setItem(STORAGE_KEY,JSON.stringify({version:VERSION,choices:cached}));}catch{}
  };
  return {
    key:STORAGE_KEY,
    invalidate(){cached=null;},
    get(fingerprint){return read().find(item=>item.fingerprint===fingerprint)?.model??null;},
    set(fingerprint,model){if(!fingerprint||!MODELS.has(model))return false;write([{fingerprint,model,updatedAt:Date.now()},...read().filter(item=>item.fingerprint!==fingerprint)]);return true;},
    delete(fingerprint){if(!fingerprint)return;write(read().filter(item=>item.fingerprint!==fingerprint));}
  };
}
