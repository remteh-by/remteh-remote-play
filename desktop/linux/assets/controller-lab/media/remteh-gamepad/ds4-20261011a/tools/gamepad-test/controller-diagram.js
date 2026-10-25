import {photoModel,photoSvg,photoTouchPoint,isXboxFamilyReference} from './controller-photo.js';
import {controllerIdentity,materialChannels,controllerBattery} from '/media/remteh-gamepad/v20261011/tools/gamepad-test/controller-identity.js';

const clamp=(value,min,max)=>Number.isFinite(value)?Math.max(min,Math.min(max,value)):0;
const pressure=value=>value===true?1:clamp(value,0,1);
function pressTransform(kind,key,value,x,y){
 // Keep the cap seated in its socket: a short axial press, without lateral wobble.
 let sx=1-.012*value,sy=sx,dy=1.5*value;
 if(kind==='dpad'){sx=1-.008*value;sy=1-.024*value;dy=.9*value;}
 else if(kind==='touchpad'){sx=1;sy=1-.006*value;dy=1*value;}
 else if(kind==='bumper'){sx=1;sy=1-.075*value;dy=2.5*value;}
 else if(kind==='utility'){sx=1-.01*value;sy=1-.018*value;dy=(key==='mute'?.6:1.2)*value;}
 else if(kind==='stick'){sx=1-.02*value;sy=sx;dy=1*value;}
 return value?`translate(${x}px,${y+dy}px) scale(${sx},${sy}) translate(${-x}px,${-y}px)`:'none';
}

// This view only consumes input frames; it never sends commands to the controller.
export function createControllerDiagram(root,genericMarkup){
 let variant,renderVersion=0,buttons=[],sticks=[],triggers=[],percentages=[],touches=[],triggerBodies=[],identityNodes=null,batteryNodes=null,lastIdentity='',lastBattery='';const failedImages=new Set();
 let copyTimer=null,copyVersion=0;
 function resetCopyFeedback(){
  clearTimeout(copyTimer);copyTimer=null;copyVersion++;
  if(identityNodes){identityNodes.copyStatus.textContent='';delete identityNodes.copyStatus.dataset.error;}
 }
 async function copySerial(){
  const n=identityNodes,serial=n?.serial.dataset.serial;
  if(!serial||n.serial.disabled)return;
  resetCopyFeedback();const version=copyVersion;
  let copied=false;
  try{await navigator.clipboard.writeText(serial);copied=true;}
  catch{
   // Older browsers can still copy during the user's click or key press.
   const field=document.createElement('textarea'),focused=document.activeElement;
   field.value=serial;field.readOnly=true;field.style.cssText='position:fixed;left:-9999px;top:0;opacity:0;font-size:16px';
   document.body.append(field);
   try{field.select();copied=document.execCommand('copy');}catch{}finally{field.remove();if(focused?.isConnected)focused.focus({preventScroll:true});}
  }
  if(identityNodes!==n||version!==copyVersion||n.serial.dataset.serial!==serial)return;
  n.copyStatus.textContent=copied?'Скопировано':'Не удалось скопировать';n.copyStatus.dataset.error=String(!copied);
  copyTimer=setTimeout(resetCopyFeedback,copied?2200:4000);
 }
 function render(model){
  resetCopyFeedback();
  const version=++renderVersion;variant=model;root.innerHTML=model?photoSvg(model):'<p class="gp-small">Photo unavailable</p>'();root.dataset.artwork=model??'generic';
  const all=selector=>[...root.querySelectorAll(selector)];
  buttons=all(model?'[data-photo-key]':'[data-map]').map(el=>{const part=el.querySelector('[data-photo-button]');return {el,part,key:model?el.dataset.photoKey:el.dataset.map,kind:el.dataset.photoKind,x:Number(part?.dataset.cx),y:Number(part?.dataset.cy),last:-1};});
  sticks=all(model?'[data-photo-stick]':'[data-stick-dot]');
  triggers=all('[data-photo-trigger]');percentages=all('[data-photo-percentage]');touches=all('[data-photo-touch]');triggerBodies=all('[data-photo-trigger-body]');
  lastIdentity='';delete root.dataset.factoryColor;delete root.dataset.darkCaps;
  lastBattery='';const battery=root.querySelector('[data-photo-battery]');
  batteryNodes=battery?{root:battery,value:battery.querySelector('[data-photo-battery-value]'),fill:battery.querySelector('[data-photo-battery-fill]'),bolt:battery.querySelector('[data-photo-battery-bolt]')}:null;
  identityNodes=model==='dualsense'?{revision:root.querySelector('[data-photo-revision]'),color:root.querySelector('[data-photo-edition]'),serial:root.querySelector('[data-photo-serial]'),copyStatus:root.querySelector('[data-photo-copy-status]'),editionNote:root.querySelector('[data-photo-edition-note]'),materials:all('[data-photo-material]'),channels:all('[data-material-channel]'),shellFilter:root.querySelector('[data-photo-filter="shell"]').id,capFilter:root.querySelector('[data-photo-filter="cap"]').id}:null;
  identityNodes?.serial.addEventListener('click',copySerial);
  const photos=all('[data-controller-photo]');root.dataset.artworkState=photos.length?'loading':'schematic';
  if(model==='hybrid-preview'){
   let pending=photos.length,loadFailed=false;
   const loaded=()=>{if(version!==renderVersion||variant!==model||loadFailed)return;if(--pending===0)root.dataset.artworkState='ready';};
   const failed=()=>{if(version!==renderVersion||variant!==model||loadFailed)return;loadFailed=true;failedImages.add(model);render(null);};
   photos.forEach(photo=>{photo.addEventListener('load',loaded,{once:true});photo.addEventListener('error',failed,{once:true});});
  }else{
   const photo=photos[0];
   photo?.addEventListener('load',()=>{if(version===renderVersion&&variant===model)root.dataset.artworkState='ready';},{once:true});
   photo?.addEventListener('error',()=>{if(version!==renderVersion||variant!==model)return;failedImages.add(model);render(null);},{once:true});
  }
 }
 function update({source,profile=null,info=null,powerState=null,frame,values={},counts={},fresh=false}){
  const selected=photoModel(source,profile),model=failedImages.has(selected)?null:selected;
  if(variant!==model)render(model);
  const familyReference=isXboxFamilyReference(source,profile),hybridPreview=model==='hybrid-preview';
  root.dataset.artworkMatch=hybridPreview?'preview':profile?.identityOrigin==='manual'?'manual':familyReference?'family-reference':source&&model?'model':'preview';
  if(batteryNodes){
   const battery=controllerBattery(source,powerState),stamp=JSON.stringify(battery);
   if(stamp!==lastBattery){
    const n=batteryNodes;n.root.dataset.status=battery.tone;n.root.setAttribute('aria-label',battery.label);n.root.title=battery.hint;
    n.value.textContent=battery.text;n.fill.setAttribute('width',String((battery.level??0)*.2));n.bolt.setAttribute('opacity',battery.charging?'1':'0');lastBattery=stamp;
   }
  }
  if(identityNodes){
   const identity=controllerIdentity(source,info),stamp=JSON.stringify(identity);
   if(stamp!==lastIdentity){
    const n=identityNodes;
    // HID text is untrusted: only textContent, with validated serial/revision.
    n.revision.textContent=identity.heading;n.revision.title=identity.serialHint;
    n.color.textContent=identity.colorLabel;n.color.title=identity.colorHint;
    if(n.serial.dataset.serial!==(identity.serial??''))resetCopyFeedback();
    n.serial.textContent=identity.serialLabel;n.serial.dataset.serial=identity.serial??'';n.serial.disabled=!identity.serial;
    n.serial.title=identity.serial?'Нажмите, чтобы скопировать серийный номер':identity.serialHint;
    n.serial.setAttribute('aria-label',identity.serial?`Скопировать серийный номер ${identity.serial}`:'Серийный номер не прочитан');
    n.editionNote.hidden=!identity.finish;n.editionNote.textContent=identity.finish==='pattern'?'Основной цвет · без рисунка спецсерии':identity.finish?'Покрытие передано условно':'';
    root.dataset.factoryColor=identity.color??'default';root.dataset.darkCaps=String(identity.caps==='dark');
    const channels=materialChannels(identity.tint);n.channels.forEach((el,i)=>el.setAttribute('slope',String(channels[i])));
    for(const el of n.materials){const material=el.dataset.photoMaterial;
     if(material==='shell'&&identity.color&&identity.color!=='White')el.setAttribute('filter',`url(#${n.shellFilter})`);
     else if(material==='cap'&&identity.caps==='dark')el.setAttribute('filter',`url(#${n.capFilter})`);
     else el.removeAttribute('filter');
    }
    lastIdentity=stamp;
   }
  }
  let active=0;
  for(const entry of buttons){
   const {el,part,key,kind,x,y}=entry;
   const value=fresh?pressure(kind==='trigger'?(frame?.triggers?.[key==='r2'?1:0]??values[key]):values[key]):0;
   // Analog trigger travel remains visible even below the digital button threshold.
   const pressed=value>(kind==='trigger'?.01:.5);
   el.classList.toggle('pressed',pressed);if(pressed)active++;
   if(model&&value!==entry.last){
    el.style.setProperty('--press',String(value));el.dataset.pressure=value.toFixed(3);
    if(part)part.style.transform=pressTransform(kind,key,value,x,y);
    entry.last=value;
   }
   el.classList.toggle('seen',(counts[key]??0)>0);
   el.classList.toggle('unavailable',fresh&&!(key in values));
  }
  root.dataset.pressed=String(active);
  sticks.forEach((el,i)=>{
   const x=fresh?clamp(frame?.axes?.[i*2],-1,1):0,y=fresh?clamp(frame?.axes?.[i*2+1],-1,1):0;
   if(model){el.setAttribute('transform',`translate(${(x*20).toFixed(3)},${(y*20).toFixed(3)})`);el.dataset.x=String(x);el.dataset.y=String(y);}
   else{el.setAttribute('cx',String((i?370:234)+x*16));el.setAttribute('cy',String(203+y*16));}
  });
  triggers.forEach((el,i)=>{
   const value=fresh?clamp(frame?.triggers?.[i],0,1):0;
   el.setAttribute('width',String(116*value));
   percentages[i].textContent=fresh?Math.round(value*100)+'%':'—';
   const cap=triggerBodies[i],x=Number(cap?.dataset.cx);
   if(cap)cap.style.transform=value?`translate(${x}px,${67+value*4}px) scale(1,${1-value*.08}) translate(${-x}px,-67px)`:'none';
  });
  touches.forEach((el,i)=>{
   const point=fresh?frame?.touch?.[i]:null;
   el.setAttribute('opacity',point?.active?'1':'0');
   if(point?.active){const [x,y]=photoTouchPoint(point,model);el.setAttribute('transform',`translate(${x},${y})`);}
  });
  if(failedImages.has(selected))return 'Изображение не загрузилось. Показана резервная схема геймпада.';
  if(hybridPreview)return source?'Браузер не сообщил точную модель. Выберите модель выше — фото и обозначения обновятся. Тест кнопок уже работает по реальным данным браузера.':'Подключите геймпад: Sony — по USB; Xbox — нажмите любую кнопку.';
  return model?(source?(fresh?(familyReference?'Фото Xbox Series; точную модель браузер не сообщил. ':'')+'Нажимайте кнопки: короткое утапливание и тень показывают нажатие. Курки повторяют глубину хода. После проверки рядом с кнопкой остаётся маленькая зелёная галочка.':'Поток данных остановлен. Нажмите кнопку или подключите геймпад снова.'):'Подключите геймпад: Sony — по USB; Xbox — нажмите любую кнопку.'):(source?.standard?'Для этой модели показана условная схема. Названия кнопок — в списке ниже.':'Для нестандартной раскладки смотрите номера кнопок ниже.');
 }
 render('hybrid-preview');
 return {update};
}
