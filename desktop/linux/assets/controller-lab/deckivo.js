import tool from '/media/remteh-gamepad/v20261011/tools/gamepad-test/index.js';
import {installAndroidBridge} from './native-bridge.js';
installAndroidBridge();
const language=new URLSearchParams(location.search).get('lang')==='ru'?'ru':'en';
document.documentElement.lang=language;
const picker=document.querySelector('#language');picker.value=language;picker.addEventListener('change',()=>{location.search='?lang='+picker.value;});
const config=await (await fetch('/media/remteh-gamepad/v20261011/boot.json')).json();
const privacy=document.querySelector('#privacy');privacy.textContent=language==='ru'?'Измерения остаются на устройстве. Выбор фото не меняет возможности геймпада. Для калибровки Sony нужен USB; постоянная запись требует отдельного подтверждения.':'Measurements stay on this device. A model choice changes the photo, never hardware capabilities. Sony calibration requires USB; permanent writes require separate confirmation.';
if(language==='en'){
 const english=await(await fetch('/en.json')).json();
 config.texts={...config.texts,...english.keys};
 const dictionary=new Map(Object.entries(english.phrases));
 // Original modules remain inspectable; translate their exact visible phrases.
 const translate=root=>{
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);let node;
  while((node=walker.nextNode())){if(/^(SCRIPT|STYLE)$/.test(node.parentElement?.tagName))continue;const value=node.nodeValue,trim=value.trim();if(dictionary.has(trim))node.nodeValue=value.replace(trim,dictionary.get(trim));}
  for(const element of root.querySelectorAll?.('[title],[aria-label],[placeholder]')??[]){for(const key of ['title','aria-label','placeholder'])if(dictionary.has(element.getAttribute(key)))element.setAttribute(key,dictionary.get(element.getAttribute(key)));}
 };
 const observer=new MutationObserver(records=>{for(const record of records){if(record.type==='characterData')translate(record.target.parentElement);if(record.type==='childList'&&record.target.nodeType===1)translate(record.target);for(const node of record.addedNodes??[])if(node.nodeType===1)translate(node);}});
 observer.observe(document.querySelector('#diag-tool'),{childList:true,characterData:true,subtree:true});
 config._translate=()=>translate(document.querySelector('#diag-tool'));
}
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
