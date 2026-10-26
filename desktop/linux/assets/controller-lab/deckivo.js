import {createTranslator,translateTree} from '/translation.js';
import {serviceModeEnabled,setServiceMode} from '/media/remteh-gamepad/calibration-20261020b/service-mode.js';
import tool from '/media/remteh-gamepad/v20261011/tools/gamepad-test/index.js';
import {installAndroidBridge} from './native-bridge.js';
installAndroidBridge();
const attribution=document.querySelector('#remteh-attribution'),agent=navigator.userAgent||'';
const attributionSource=/Android/i.test(agent)?'deckivo_android':/(Macintosh|Mac OS X)/i.test(agent)?'deckivo_macos':/(Linux|X11)/i.test(agent)?'deckivo_linux':null;
if(attribution&&attributionSource)attribution.href=`https://remteh.by/?utm_source=${attributionSource}&utm_medium=app&utm_campaign=deckivo`;
const language=new URLSearchParams(location.search).get('lang')==='ru'?'ru':'en';
document.documentElement.lang=language;
const picker=document.querySelector('#language');picker.value=language;picker.addEventListener('change',()=>{location.search='?lang='+picker.value;});
const serviceLabel=document.createElement('label'),serviceCheckbox=document.createElement('input');serviceCheckbox.type='checkbox';serviceCheckbox.id='deckivo-service-mode';serviceCheckbox.checked=serviceModeEnabled();
const serviceText=language==='ru'?'Сервисный режим':'Service mode';serviceLabel.append(serviceCheckbox,document.createTextNode(' '+serviceText));serviceLabel.className='deckivo-service-mode';document.querySelector('.deckivo-header').append(serviceLabel);
const applyService=()=>{document.documentElement.dataset.serviceMode=serviceModeEnabled()?'on':'off';};
serviceCheckbox.addEventListener('change',()=>{try{setServiceMode(serviceCheckbox.checked);}catch{serviceCheckbox.checked=false;}applyService();window.dispatchEvent(new Event('deckivo-service-mode'));});applyService();
const config=await (await fetch('/media/remteh-gamepad/v20261011/boot.json')).json();
const privacy=document.querySelector('#privacy');privacy.textContent=language==='ru'?'Измерения остаются на устройстве. Выбор фото не меняет возможности геймпада. Для калибровки Sony нужен USB; постоянная запись требует отдельного подтверждения.':'Measurements stay on this device. A model choice changes the photo, never hardware capabilities. Sony calibration requires USB; permanent writes require separate confirmation.';
if(language==='en'){
 const english=await(await fetch('/en.json')).json();
 config.texts={...config.texts,...english.keys};
 const translateValue=createTranslator(english.phrases);
 const translate=root=>translateTree(root,translateValue);
 const observer=new MutationObserver(records=>{
  for(const record of records) {
   if(record.type==='characterData')translate(record.target.parentElement);
   else if(record.target.nodeType===1)translate(record.target);
  }
 });
 observer.observe(document.body,{childList:true,characterData:true,attributes:true,attributeFilter:['title','aria-label','placeholder','alt'],subtree:true});

 config._translate=()=>translate(document.body);
}
if(language==='ru')Object.assign(config.texts,{
 gp_error_service_mode_required:'Сервисный режим выключен. Постоянная запись заблокирована.',
 gp_error_persistent_backup_required:'Перед записью нужна сохранённая резервная копия параметров.',
 gp_error_confirmation_required:'Постоянная запись отменена. Команда во флеш не отправлена.'
});
config.texts.gp_local=language==='ru'?'Локальная диагностика Deckivo':'Local Deckivo diagnostics';
config.texts.gp_license_text=language==='ru'?'Интерфейс и измерения — RemTeh. Протокол Sony — DualShock Tools (MIT). Рабочие файлы включены в приложение.':'Interface and measurements by RemTeh. Sony protocol by DualShock Tools (MIT). Working files are bundled with the app.';
const root=document.querySelector('#diag-tool');
const context={...config,lang:language,engineUrl:'/media/remteh-gamepad/calibration-20261020b/sony-engine.js',firmwareUrl:'/media/remteh-gamepad/v20261011/firmware.php',onResult(result){document.querySelector('#result').textContent=result.summary??'';},onReset(){document.querySelector('#result').textContent='';}};
let mounted=false,closing=Promise.resolve();
const mount=()=>{if(!mounted){tool.mount(root,context);mounted=true;config._translate?.();}};
mount();
window.DeckivoLabClose=()=>{if(mounted){mounted=false;closing=Promise.resolve(tool.unmount());}return closing;};
window.DeckivoLabResume=()=>closing.then(mount);
config._translate?.();
window.addEventListener('pagehide',()=>tool.unmount(),{once:true});
