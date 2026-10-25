// Factory editions reported by the pinned DualShock Tools decoder. The display
// uses the existing photo geometry; it never changes or normalizes input values.
const editions={
 'White':['#ffffff','light'],
 'Midnight Black':['#303139','dark'],
 'Cosmic Red':['#ad2958','dark'],
 'Nova Pink':['#f35aa0','dark'],
 'Galactic Purple':['#69509d','dark'],
 'Starlight Blue':['#46a9dd','dark'],
 'Grey Camouflage':['#8d9492','dark','pattern'],
 'Volcanic Red':['#c42d3b','dark'],
 'Sterling Silver':['#bbc2ca','dark'],
 'Cobalt Blue':['#3264b5','dark'],
 'Chroma Teal':['#6ca39c','dark','iridescent'],
 'Chroma Indigo':['#7371be','dark','iridescent'],
 'Chroma Pearl':['#e4d9d2','light','iridescent'],
 'HyperPop Techno Red':['#ee404e','dark','gradient'],
 'HyperPop Remix Green':['#92e441','dark','gradient'],
 'HyperPop Rhythm Blue':['#329adf','dark','gradient'],
 '30th Anniversary':['#aeb1b4','dark','pattern'],
 'God of War Ragnarok':['#dbe1e4','light','pattern'],
 'Spider-Man 2':['#ad2239','dark','pattern'],
 'Astro Bot':['#e9eef1','light','pattern'],
 'Fortnite':['#e6b94c','dark','pattern'],
 'The Last of Us':['#414346','dark','pattern'],
 'God of War 20th Anniversary':['#e2deda','light','pattern'],
 'Icon Blue Limited Edition':['#166fb2','dark','pattern'],
 'Ghost of Yōtei Limited Edition':['#bd9761','dark','pattern'],
 'Marathon Limited Edition':['#e3e6e1','light','pattern'],
 'Genshin Impact Limited Edition':['#e7e4d9','light','pattern'],
 '007 First Light Limited Edition':['#b98d4f','dark','pattern'],
};
const versions={'BDM-010':1,'BDM-020':2,'BDM-030':3,'BDM-040':4,'BDM-050':5,'BDM-060R':6,'BDM-060M':6,'BDM-060X':6};

export function controllerIdentity(source,info){
 // Never retain a USB identity on the generic browser input of another device.
 const connected=source?.kind==='hid'&&source.model==='DS5'&&info?.model==='DS5'&&info.readable===true;
 const fields=connected?info.fields??{}:{};
 const rawSerial=String(fields['Serial Number']??'').replace(/\0/g,'').trim();
 const serial=/^[a-z0-9]{10,20}$/i.test(rawSerial)&&!/^(0+|f+)$/i.test(rawSerial)?rawSerial.toUpperCase():null;
 const rawBoard=String(fields['Board Model']??'').trim().toUpperCase();
 const board=/^BDM-\d{3}[A-Z]?$/.test(rawBoard)?rawBoard:null;
 const version=versions[board]??null;
 const color=Object.hasOwn(editions,fields.Color)?fields.Color:null;
 const [tint,caps,finish]=editions[color]??['#ffffff','light',null];
 return {
  connected,serial,board,version,color,tint,caps,finish,
  heading:version?`Версия ${version} · ${board}`:board?`Ревизия ${board}`:connected?'Ревизия не определена':'Версия и ревизия —',
  colorLabel:color??(connected?'Цвет не определён':'Чёрно-белый · по умолчанию'),
  colorHint:color?`Заводская расцветка: ${color}. После замены корпуса цвет может отличаться.${finish==='pattern'?' Показан основной цвет, рисунок спецсерии не воспроизведён.':finish?' Покрытие передано условно; оттенок зависит от освещения.':''}`:'Чёрно-белое изображение используется, пока заводская расцветка не определена.',
  serialLabel:serial??'Не прочитан',
  serialHint:connected?'Серийный номер из памяти геймпада.':'Подключите Sony по USB, чтобы прочитать серийный номер и ревизию.',
 };
}

// The photo is shaded in sRGB. Preserve the dark centre and blue light strips,
// recoloring only the bright shell. This is a display-only material filter.
export function materialChannels(hex){
 return [1,3,5].map(i=>Number((parseInt(hex.slice(i,i+2),16)/255).toFixed(5)));
}

// Read the connected controller's fresh HID report, never the computer battery.
export function controllerBattery(source,state,now=performance.now()){
 const battery=state?.battery,level=battery?.charge_level,age=now-(state?.lastInput??0);
 const available=source?.kind==='hid'&&state?.connected===true&&!state.fault&&Number.isFinite(state.lastInput)&&state.lastInput>0&&age>=0&&age<2000&&!battery?.is_error&&Number.isFinite(level)&&level>=0&&level<=100;
 if(!available)return {level:null,charging:false,tone:'unknown',text:'—',label:'Заряд аккумулятора: нет данных',hint:source?.kind==='hid'?'Нет свежих данных о заряде аккумулятора. Проверьте USB-подключение.':'Подключите Sony по USB, чтобы увидеть заряд аккумулятора.'};
 const value=Math.round(level),charging=battery.is_charging===true;
 const label=`Заряд аккумулятора: ${value}%${charging?' · заряжается':''}`;
 return {level:value,charging,tone:charging?'charging':value<=20?'low':'normal',text:`${value}%`,label,hint:label};
}
