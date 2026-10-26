// Deckivo service operations. No permanent controller write without durable backup and consent.
export const SERVICE_KEY='deckivo:service-mode:v1';
const BACKUP_PREFIX='deckivo:permanent-backup:v1:';
const valid=v=>Array.isArray(v)&&v.length===12&&v.every(n=>Number.isInteger(n)&&n>=0&&n<=65535);
export function createPermanentPolicy(storage,confirm) {
 const permits=new WeakSet();
 const enabled=()=>{try{return storage.getItem(SERVICE_KEY)==='true';}catch{return false;}};
 function setEnabled(value) {
  const text=value?'true':'false';storage.setItem(SERVICE_KEY,text);
  if(storage.getItem(SERVICE_KEY)!==text)throw new Error('storage_failed');
 }
 function preserve(identity,parameters) {
  if(!/^[a-f0-9]{64}$/i.test(identity??'')||!valid(parameters))throw new Error('persistent_backup_required');
  const key=BACKUP_PREFIX+identity,previous=storage.getItem(key);
  // Never overwrite the earliest surviving backup with current RAM parameters.
  // Legacy records retain only three history entries; older lost copies cannot
  // be reconstructed and are never described as factory calibration.
  if(previous!==null){
   let old;try{old=JSON.parse(previous);}catch{throw new Error('persistent_backup_required');}
   if(old?.identity!==identity||!valid(old.original))throw new Error('persistent_backup_required');
   if(old.immutable===true)return old;
   const first=(Array.isArray(old.history)?old.history:[]).find(item=>valid(item?.original))??old;
   const migrated={schema:1,identity,original:[...first.original],at:first.at,immutable:true,provenance:'earliest-surviving-legacy',history:[]};
   const encoded=JSON.stringify(migrated);storage.setItem(key,encoded);
   if(storage.getItem(key)!==encoded)throw new Error('storage_failed');
   return migrated;
  }
  const record={schema:1,identity,original:[...parameters],at:new Date().toISOString(),immutable:true,provenance:'user-confirmed-power-cycle',history:[]};
  const value=JSON.stringify(record);storage.setItem(key,value);
  if(storage.getItem(key)!==value)throw new Error('storage_failed');
  return record;
 }
 function requireBackup(identity,record) {
  if(!record||record.identity!==identity||!valid(record.original))throw new Error('persistent_backup_required');
  let saved;try{saved=JSON.parse(storage.getItem(BACKUP_PREFIX+identity));}catch{}
  if(!saved||JSON.stringify(saved)!==JSON.stringify(record))throw new Error('persistent_backup_required');
 }
 function assertPermitted(controller) {
  if(!enabled()||!permits.has(controller))throw new Error('service_mode_required');
 }
 async function write(controller,identity,record,operation) {
  if(!enabled())throw new Error('service_mode_required');
  requireBackup(identity,record);
  if(!await confirm())throw new Error('confirmation_required');
  if(!enabled())throw new Error('service_mode_required');
  requireBackup(identity,record);
  permits.add(controller);
  try{return await operation();}finally{permits.delete(controller);}
 }
 return {enabled,setEnabled,preserve,requireBackup,assertPermitted,write};
}
// A browser reconnect is not a power cycle. Require a physical HID disconnect
// observed by this page, a new connection, and an explicit user acknowledgement.
export function createBaselineGate(){
 const disconnected=new Set(),reconnected=new Set(),confirmed=new Set();
 return {
  disconnected(id){if(id){disconnected.add(id);reconnected.delete(id);confirmed.delete(id);}},
  connected(id){if(disconnected.delete(id))reconnected.add(id);},
  async require(id,confirm){
   if(confirmed.has(id))return;
   const fail=()=>{const e=new Error('power_cycle_required');e.recovered=true;throw e;};
   if(!id||!reconnected.has(id))fail();
   if(!await confirm())fail();
   if(!reconnected.has(id))fail();
   confirmed.add(id);
  }
 };
}
export function confirmPowerCycle(){
 if(typeof document==='undefined')return Promise.resolve(false);
 const ru=document.documentElement.lang==='ru';
 return new Promise(resolve=>{
  const dialog=document.createElement('dialog');dialog.className='deckivo-service-dialog';
  const title=document.createElement('h2');title.textContent=ru?'Исходные параметры геймпада':'Controller baseline';
  const text=document.createElement('p');text.textContent=ru?'Протокол читает параметры из оперативной памяти. Перед первой калибровкой на этой странице отключите USB, полностью выключите геймпад и подключите заново. Простого переподключения вкладки недостаточно. Сохраняется самая ранняя доступная копия, а не гарантированные заводские настройки.':'The protocol reads RAM parameters. Before the first calibration on this page, unplug USB, fully power off the controller, then reconnect. Reopening the tab is not enough. The earliest available backup is retained; it is not guaranteed factory calibration.';
  const label=document.createElement('label'),check=document.createElement('input');check.type='checkbox';check.id='baseline-power-cycle-confirmation';
  label.append(check,document.createTextNode(ru?' Геймпад был полностью выключен перед переподключением.':' The controller was fully powered off before reconnecting.'));
  const cancel=document.createElement('button');cancel.textContent=ru?'Отмена':'Cancel';
  const proceed=document.createElement('button');proceed.textContent=ru?'Продолжить':'Continue';proceed.disabled=true;
  let settled=false;const finish=value=>{if(settled)return;settled=true;dialog.close();dialog.remove();resolve(value);};
  check.onchange=()=>{proceed.disabled=!check.checked;};cancel.onclick=()=>finish(false);proceed.onclick=()=>{if(check.checked)finish(true);};
  dialog.oncancel=event=>{event.preventDefault();finish(false);};dialog.append(title,text,label,cancel,proceed);document.body.append(dialog);dialog.showModal();cancel.focus();
 });
}
function ask() {
 if(typeof document==='undefined')return Promise.resolve(false);
 const ru=document.documentElement.lang==='ru';
 return new Promise(resolve=>{
  const dialog=document.createElement('dialog');dialog.className='deckivo-service-dialog';
  const title=document.createElement('h2');title.textContent=ru?'Постоянная запись калибровки':'Permanent calibration write';
  const warning=document.createElement('p');warning.textContent=ru?'Необратимая запись во флеш геймпада. Только для опытных. Сделана резервная копия параметров.':'Irreversible write to controller flash. Experienced users only. The original parameters have been backed up.';
  const label=document.createElement('label'),check=document.createElement('input');check.type='checkbox';check.id='permanent-write-confirmation';
  label.append(check,document.createTextNode(ru?' Подтверждаю риск и наличие резервной копии параметров.':' I confirm the risk and the backup of the original parameters.'));
  const cancel=document.createElement('button');cancel.textContent=ru?'Отмена':'Cancel';
  const save=document.createElement('button');save.textContent=ru?'Записать во флеш':'Write to flash';save.disabled=true;save.dataset.permanentConfirm='';
  let settled=false;const finish=value=>{if(settled)return;settled=true;dialog.close();dialog.remove();resolve(value);};
  check.addEventListener('change',()=>{save.disabled=!check.checked;});
  cancel.addEventListener('click',()=>finish(false));save.addEventListener('click',()=>{if(check.checked)finish(true);});
  dialog.addEventListener('cancel',event=>{event.preventDefault();finish(false);});
  dialog.append(title,warning,label,cancel,save);document.body.append(dialog);dialog.showModal();cancel.focus();
 });
}
const unavailable={getItem(){return null;},setItem(){throw new Error('storage_failed');}};
let storage;try{storage=globalThis.localStorage;}catch{}storage??=unavailable;
export const permanentPolicy=createPermanentPolicy(storage,ask);
export const serviceModeEnabled=()=>permanentPolicy.enabled();
export const setServiceMode=value=>permanentPolicy.setEnabled(value);
export const preserveOriginal=(identity,values)=>permanentPolicy.preserve(identity,values);
export const requireFlashPermit=controller=>permanentPolicy.assertPermitted(controller);
export const permanentWrite=(controller,identity,backup,operation)=>permanentPolicy.write(controller,identity,backup,operation);
