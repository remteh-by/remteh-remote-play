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
  let history=[];try{const old=JSON.parse(previous);if(old?.identity===identity&&valid(old.original))history=[...(old.history??[]),{original:old.original,at:old.at}].slice(-3);}catch{}
  const record={schema:1,identity,original:[...parameters],at:new Date().toISOString(),history};
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
