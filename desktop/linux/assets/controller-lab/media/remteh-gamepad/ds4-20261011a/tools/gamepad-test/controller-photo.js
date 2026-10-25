import {DS4_BODY_PATH} from '/photo-masks.js';
// Photographs hosted by RemTeh. Every moving front control is cut from the same image.
// DualShock 4: official PlayStation product media; provenance accompanies the release.
// All layers use its 1000 × 1000 coordinate space; they never alter input data.
// Factory colors use SVG materials on the same photo, preserving alignment.
const images={
  ds4:new URL('./artwork/dualshock-4-front.png',import.meta.url).href,
  dualsense:new URL('/media/remteh-gamepad/v20261011/tools/gamepad-test/artwork/dualsense-front.png',import.meta.url).href,
  'xbox-series':new URL('/media/remteh-gamepad/xbox-20261011a/tools/gamepad-test/artwork/xbox-series-front.png',import.meta.url).href,
};

export function photoModel(source,profile=null){
  if(!source)return 'hybrid-preview';
  if(source.standard===false)return 'hybrid-preview';
  if(/edge|elite|adaptive/i.test(`${source.model??''} ${source.name??''}`))return 'hybrid-preview';
  if(profile?.id==='generic'&&profile.canChooseModel===true)return 'hybrid-preview';
  // Prefer the normalized profile supplied by the input layer. In particular,
  // a generic XInput name is not enough evidence to call a controller Series.
  if(profile)return profile.id==='xbox-series'?'xbox-series':profile.id==='dualsense'?'dualsense':profile.id==='ds4'?'ds4':null;
  const id=`${source.model??''} ${source.name??''}`.toLowerCase();
  if(/edge|elite|adaptive/.test(id))return 'hybrid-preview';
  if(source.model==='DS4'||/dualshock|\bds4\b|054c.*(?:05c4|09cc)/.test(id))return 'ds4';
  if(source.model==='DS5'||/dualsense/.test(id)||/054c.*0ce6/.test(id))return 'dualsense';
  if(/xbox series/.test(id)||/045e.*0b1[23]/.test(id))return 'xbox-series';
  return 'hybrid-preview';
}

// Some browsers expose the Xbox family but omit the USB model identifier.
// This chooses an illustration only; the input mapping remains unchanged.
export function isXboxFamilyReference(source,profile){
  return source?.standard===true&&profile?.id==='xbox'&&!/360|xbox\s*one|elite|adaptive/i.test(`${source.model??''} ${source.name??''}`);
}

const names={cross:'Крестик',circle:'Круг',square:'Квадрат',triangle:'Треугольник',up:'Вверх',down:'Вниз',left:'Влево',right:'Вправо',create:'Create',options:'Options',ps:'PS',mute:'Микрофон — Mute',touchpad:'Нажатие тачпада',share:'Share',l3:'Нажатие левого стика — L3',r3:'Нажатие правого стика — R3',l1:'L1',r1:'R1',l2:'L2',r2:'R2'};
let photoSequence=0,asset='',prefix='',cutouts=[];
// Preserve the manufacturer image intact; position it in the shared photo space.
const photoAttributes=()=>asset===images.ds4?'x="-399.36" y="-28" width="1792" height="1008"':'width="1000" height="1000"';
const paint=(shape,attributes)=>shape.replace('class="gp-photo-hit"',attributes);
function kind(name){
  if(['up','down','left','right'].includes(name))return 'dpad';
  if(['l1','r1'].includes(name))return 'bumper';
  if(name==='touchpad')return 'touchpad';
  if(['create','options','share','ps','mute'].includes(name))return 'utility';
  return 'face';
}
// PlayStation mark: Font Awesome Free 6.7.2, Fonticons, Inc., CC BY 4.0.
// Source and attribution are retained in artwork/playstation-mark-LICENSE.txt.
const psMark='M570.9 372.3c-11.3 14.2-38.8 24.3-38.8 24.3L327 470.2v-54.3l150.9-53.8c17.1-6.1 19.8-14.8 5.8-19.4-13.9-4.6-39.1-3.3-56.2 2.9L327 381.1v-56.4c23.2-7.8 47.1-13.6 75.7-16.8 40.9-4.5 90.9.6 130.2 15.5 44.2 14 49.2 34.7 38 48.9zm-224.4-92.5v-139c0-16.3-3-31.3-18.3-35.6-11.7-3.8-19 7.1-19 23.4v347.9l-93.8-29.8V32c39.9 7.4 98 24.9 129.2 35.4C424.1 94.7 451 128.7 451 205.2c0 74.5-46 102.8-104.5 74.6zM43.2 410.2c-45.4-12.8-53-39.5-32.3-54.8 19.1-14.2 51.7-24.9 51.7-24.9l134.5-47.8v54.5l-96.8 34.6c-17.1 6.1-19.7 14.8-5.8 19.4 13.9 4.6 39.1 3.3 56.2-2.9l46.4-16.9v48.8c-51.6 9.3-101.4 7.3-153.9-10z';
function symbol(name,x,y,label){
  const shapes={
    triangle:'<path d="M0-16.5 16 12H-16Z"/>',
    circle:'<circle r="15"/>',
    cross:'<path d="m-12-12 24 24m0-24-24 24"/>',
    square:'<rect x="-13" y="-13" width="26" height="26"/>'
  };
  const xboxColor=asset===images['xbox-series']?{A:'#6cc04a',B:'#ef4c45',X:'#4eb1e4',Y:'#f5ca43'}[label]:null;
  return ['△','○','×','□'].includes(label)?`<g class="gp-photo-face-symbol" transform="translate(${x},${y})">${shapes[name]}</g>`:
    label?`<text class="gp-photo-symbol" x="${x}" y="${y}" dominant-baseline="central" text-anchor="middle"${xboxColor?` style="fill:${xboxColor}"`:''}>${label}</text>`:'';
}
function check(name,x,y){
  const positions={up:[x,y-44],down:[x,y+42],left:[x-42,y],right:[x+42,y],l1:[x-77,y-2],r1:[x+77,y-2],create:[x+25,y-17],options:[x-25,y-17],touchpad:[x+143,y-58],ps:[x+31,y+3],mute:[x+37,y]};
  if(asset===images['xbox-series'])Object.assign(positions,{
    cross:[x+39,y+22],circle:[x+39,y-22],square:[x-39,y-22],triangle:[x,y-40],
    share:[x+37,y],create:[x-31,y-7],options:[x+31,y-7],ps:[x+37,y-20]
  });
  if(asset===images.ds4)Object.assign(positions,{touchpad:[x+120,y-47],ps:[x+33,y+4],create:[x-24,y-12],options:[x+24,y-12],l1:[x-73,y-8],r1:[x+73,y-8]});
  const [cx,cy]=positions[name]??[x+32,y-29];
  return checkAt(cx,cy);
}
function checkAt(x,y){
  return `<g class="gp-photo-check" transform="translate(${x},${y})" aria-hidden="true"><circle r="8.5"/><path d="m-3.5 0 2.4 2.5 4.7-5"/></g>`;
}
function key(name,x,y,shape,label='',extra='',title=names[name],content=''){
  const clip=`${prefix}-${name}`;
  if(extra.startsWith('transform=')){shape=paint(shape,`class="gp-photo-hit" ${extra}`);extra='';}
  cutouts.push(paint(shape,'fill="black" stroke="black" stroke-width=".6"'));
  return `<g class="gp-photo-key" data-photo-key="${name}" data-photo-kind="${kind(name)}" ${extra}><title>${title}</title>
    <defs><clipPath id="${clip}">${paint(shape,'')}</clipPath></defs>
    ${paint(shape,`class="gp-photo-cavity" fill="url(#${prefix}-well)"`)}
    ${paint(shape,'class="gp-photo-contact"')}
    ${paint(shape,'class="gp-photo-halo"')}
    <g class="gp-photo-button" data-photo-button data-cx="${x}" data-cy="${y}">
      <g class="gp-photo-surface"><image href="${asset}" ${photoAttributes()} clip-path="url(#${clip})" data-photo-material="${name==='touchpad'?'shell':['face','dpad'].includes(kind(name))||['create','options'].includes(name)?'cap':'original'}"/>
        ${paint(shape,`class="gp-photo-pressure-shade" fill="url(#${prefix}-pressure)"`)}
        ${paint(shape,`class="gp-photo-lip" fill="none" stroke="url(#${prefix}-edge)"`)}
        ${content||symbol(name,x,y,label)}${dpadMark(name)}
      </g>
      ${paint(shape,'class="gp-photo-hit"')}
    </g>
    ${check(name,x,y)}
  </g>`;
}
function dpadMark(name){
 const positions={up:[214,285,0],right:[278,349,90],down:[214,413,180],left:[150,349,270]};
 const p=positions[name];
 return asset===images.dualsense&&p?`<path class="gp-photo-dpad-mark" transform="translate(${p[0]} ${p[1]}) rotate(${p[2]})" d="M0-4-6 4H6Z"/>`:'';
}
const face=(name,x,y,label,title)=>key(name,x,y,`<circle class="gp-photo-hit" cx="${x}" cy="${y}" r="26"/>`,label,'',title);
const rect=(name,x,y,w,h,label='',extra='',title)=>key(name,x,y,`<rect class="gp-photo-hit" x="${x-w/2}" y="${y-h/2}" width="${w}" height="${h}" rx="${Math.min(10,h/2)}"/>`,label,extra,title);
function stick(name,i,x,y,r=53){
  const clip=`${prefix}-cap-${i}`,caption=asset===images['xbox-series']?(i?'RS':'LS'):name.toUpperCase();
  cutouts.push(`<circle cx="${x}" cy="${y}" r="${r+2}" fill="black"/>`);
  return `<g class="gp-photo-key gp-photo-thumb" data-photo-key="${name}" data-photo-kind="stick"><title>${names[name]}</title><circle cx="${x}" cy="${y}" r="${r+8}" fill="url(#${prefix}-socket)"/><g data-photo-stick="${i}" data-cx="${x}" data-cy="${y}"><g data-photo-button data-cx="${x}" data-cy="${y}" class="gp-photo-button"><defs><clipPath id="${clip}"><circle cx="${x}" cy="${y}" r="${r}"/></clipPath></defs><circle class="gp-photo-cap-shadow" cx="${x}" cy="${y+4}" r="${r}"/><g class="gp-photo-surface"><image href="${asset}" ${photoAttributes()} clip-path="url(#${clip})"/><circle class="gp-photo-pressure-shade" cx="${x}" cy="${y}" r="${r}" fill="url(#${prefix}-pressure)"/></g><circle class="gp-photo-hit" cx="${x}" cy="${y}" r="${r-1}"/></g></g><circle class="gp-photo-thumb-ring" cx="${x}" cy="${y}" r="${r+11}"/>${checkAt(x+28,y+77)}</g><text class="gp-photo-stick-label" x="${x}" y="${y+82}" text-anchor="middle">${caption}</text>`;
}
function trigger(i,label,x){
  return `<g class="gp-photo-trigger gp-photo-key" data-photo-key="${i?'r2':'l2'}" data-photo-kind="trigger"><title>${label}: ход курка</title>
    <path class="gp-photo-leader" d="M${x} 145V170"/>
    <path class="gp-photo-trigger-well" d="M${x-67} 74Q${x} 59 ${x+67} 74L${x+76} 124Q${x+78} 147 ${x+61} 150H${x-61}Q${x-78} 147 ${x-76} 124Z"/>
    <g class="gp-photo-trigger-cap" data-photo-trigger-body="${i}" data-cx="${x}">
      <path class="gp-photo-trigger-side" d="M${x-78} 114H${x+78}V129Q${x+78} 146 ${x+62} 148H${x-62}Q${x-78} 146 ${x-78} 129Z" fill="url(#${prefix}-trigger-side)"/>
      <path class="gp-photo-trigger-bg" d="M${x-70} 73Q${x} 58 ${x+70} 73L${x+79} 120Q${x+80} 136 ${x+63} 138H${x-63}Q${x-80} 136 ${x-79} 120Z" fill="url(#${prefix}-trigger-face)"/>
      <path class="gp-photo-trigger-glint" d="M${x-62} 76Q${x} 63 ${x+62} 76"/>
      <text x="${x-54}" y="99" class="gp-photo-trigger-name">${label}</text><text x="${x+54}" y="99" text-anchor="end" class="gp-photo-trigger-value" data-photo-percentage="${i}">—</text>
      <rect x="${x-58}" y="115" width="116" height="5" rx="2.5" class="gp-photo-track"/><rect x="${x-58}" y="115" width="0" height="5" rx="2.5" data-photo-trigger="${i}" class="gp-photo-travel"/>
    </g>${checkAt(x+94,106)}</g>`;
}
function dualsense(){
  const dpad=[['up',214,299,'M193 271Q214 267 235 272V308L214 329L193 308Z'],['down',214,401,'M193 424Q214 428 235 424V390L214 369L193 390Z'],['left',165,349,'M136 330Q133 349 136 368H170L191 349L170 330Z'],['right',262,349,'M291 330Q294 349 291 368H257L236 349L257 330Z']];
  return `${trigger(0,'L2',218)}${trigger(1,'R2',782)}${key('l1',216,191,'<path class="gp-photo-hit" d="M156 211L158 197Q159 194 163 192Q211 169 255 174Q271 175 275 179L277 197Q223 198 156 217Z"/>','L1')}${key('r1',784,191,'<path class="gp-photo-hit" d="M844 211L842 197Q841 194 837 192Q789 169 745 174Q729 175 725 179L723 197Q777 198 844 217Z"/>','R1')}${dpad.map(([n,x,y,d])=>key(n,x,y,`<path class="gp-photo-hit" d="${d}"/>`)).join('')}${face('triangle',784,280,'△')}${face('circle',850,349,'○')}${face('cross',784,414,'×')}${face('square',716,348,'□')}${rect('create',289,243,18,40,'','transform="rotate(-13 289 243)"')}${rect('options',711,243,18,40,'','transform="rotate(13 711 243)"')}${key('touchpad',500,276,'<path class="gp-photo-hit" d="M340 197Q500 184 660 197Q679 199 674 227L651 354Q646 384 613 387H387Q354 384 349 354L326 227Q321 199 340 197Z"/>')}${stick('l3',0,343,485)}${stick('r3',1,656,485)}${key('ps',500,482,`<path class="gp-photo-hit" d="${psMark}" transform="translate(478 462.6) scale(.0764)"/>`,'','',names.ps,`<path class="gp-photo-ps-mark" d="${psMark}" transform="translate(478 462.6) scale(.0764)" fill="url(#${prefix}-ps-material)"/>`)}${rect('mute',500,530,46,7)}<text class="gp-photo-small-label" x="500" y="567" text-anchor="middle">MIC</text><g class="gp-photo-touch" data-photo-touch="0" opacity="0"><circle class="gp-photo-touch-aura" r="20"/><circle r="11"/><text text-anchor="middle" dominant-baseline="central">1</text></g><g class="gp-photo-touch" data-photo-touch="1" opacity="0"><circle class="gp-photo-touch-aura" r="20"/><circle r="11"/><text text-anchor="middle" dominant-baseline="central">2</text></g>`;
}
// CUH-ZCT2 front photograph. Coordinates below use original image pixels.
const ds4X=x=>Number((x*1.12-399.36).toFixed(3));
const ds4Y=y=>Number((y*1.12-28).toFixed(3));
function dualshock4(){
  const shape=d=>`<path class="gp-photo-hit" d="${d}" transform="matrix(1.12 0 0 1.12 -399.36 -28)"/>`;
  const part=(name,x,y,d,title=names[name])=>key(name,ds4X(x),ds4Y(y),shape(d),'','',title);
  const round=(name,x,y,r,title=names[name])=>key(name,ds4X(x),ds4Y(y),`<circle class="gp-photo-hit" cx="${ds4X(x)}" cy="${ds4Y(y)}" r="${r*1.12}"/>`,'','',title);
  const dpad=[
    ['up',561,311,'M543 292Q560 285 578 292Q581 295 580 305L578 324L561 340L543 324L540 303Q539 295 543 292Z'],
    ['down',561,396,'M544 382L560 367L577 382L580 406Q581 413 575 415Q560 420 544 415Q539 413 540 406Z'],
    ['left',518,354,'M498 339Q500 333 507 335L528 337L545 354L528 371L506 374Q498 375 497 368Q493 354 498 339Z'],
    ['right',604,354,'M595 337L616 335Q623 335 624 342Q627 354 624 367Q623 374 616 374L595 371L578 354Z']
  ];
  return `${trigger(0,'L2',ds4X(568))}${trigger(1,'R2',ds4X(1029))}`+
    part('l1',567,221,'M516 217Q562 200 609 216L615 230Q566 222 513 230Z')+
    part('r1',1032,221,'M992 216Q1035 201 1083 217L1087 230Q1035 222 988 230Z')+
    dpad.map(([name,x,y,d])=>part(name,x,y,d)).join('')+
    round('triangle',1044,295,25.5)+round('circle',1101,354,25.5)+round('cross',1044,412,25.5)+round('square',988,354,25.5)+
    part('create',643,278,'M633 264Q635 255 643 255Q652 255 653 265V288Q653 297 644 299Q634 299 632 289Z','SHARE')+
    part('options',961,278,'M949 265Q950 255 960 255Q970 255 972 265L970 289Q969 298 960 299Q950 297 949 288Z','OPTIONS')+
    part('touchpad',803,319,'M682 234H923Q930 234 930 244V359Q930 379 911 379H694Q675 379 675 360V245Q675 234 682 234Z')+
    stick('l3',0,ds4X(680),ds4Y(460),52.64)+stick('r3',1,ds4X(925),ds4Y(460),52.64)+round('ps',803,465,19)+
    `<g class="gp-photo-touch" data-photo-touch="0" opacity="0"><circle class="gp-photo-touch-aura" r="20"/><circle r="11"/><text text-anchor="middle" dominant-baseline="central">1</text></g><g class="gp-photo-touch" data-photo-touch="1" opacity="0"><circle class="gp-photo-touch-aura" r="20"/><circle r="11"/><text text-anchor="middle" dominant-baseline="central">2</text></g>`;
}
function xbox(){
  const dpadTop='<path class="gp-photo-hit" d="M375 432A65 65 0 0 1 421 451L389 483Q375 497 361 483L329 451A65 65 0 0 1 375 432Z"/>';
  const dpad=[['up',375,458,0],['right',414,497,90],['down',375,536,180],['left',337,497,270]];
  const xboxMark='<circle cx="500" cy="258" r="17" fill="#f4f6f7"/><path d="M488 246Q500 238 512 246L506 250Q500 246 494 250ZM487 250Q482 257 485 266L495 254ZM513 250Q518 257 515 266L505 254ZM489 270Q500 276 511 270L500 257Z" fill="#107c10"/>';
  return `${trigger(0,'LT',280)}${trigger(1,'RT',720)}`+
    `${key('l1',273,187,'<path class="gp-photo-hit" d="M174 194Q203 165 266 169Q316 171 361 189L350 207Q296 195 238 208Q202 213 174 194Z"/>','LB','','LB')}`+
    `${key('r1',727,187,'<path class="gp-photo-hit" d="M826 194Q797 165 734 169Q684 171 639 189L650 207Q704 195 762 208Q798 213 826 194Z"/>','RB','','RB')}`+
    `${face('cross',743,407,'A','A')}${face('circle',805,349,'B','B')}${face('square',684,349,'X','X')}${face('triangle',743,285,'Y','Y')}`+
    `${key('create',432,344,'<circle class="gp-photo-hit" cx="432" cy="344" r="22"/>','','','View')}`+
    `${key('options',568,344,'<circle class="gp-photo-hit" cx="568" cy="344" r="22"/>','','','Menu')}`+
    `${rect('share',500,397,49,31,'','','Share')}`+
    `${key('ps',500,258,'<circle class="gp-photo-hit" cx="500" cy="258" r="26"/>','','','Xbox',xboxMark)}`+
    `${dpad.map(([n,x,y,angle])=>key(n,x,y,dpadTop,'',`transform="rotate(${angle} 375 497)"`)).join('')}`+
    `${stick('l3',0,263,344)}${stick('r3',1,625,493)}`;
}
export function photoSvg(model){
  if(model==='hybrid-preview'){
    // Display only transparent margins outside each genuine product photograph.
    // The bitmap, controller proportions and every photographed detail stay intact.
    const frames={ds4:[1600,900,415,208,775,488],dualsense:[1254,1254,50,216,1153,807],'xbox-series':[1254,1254,41,211,1171,824]};
    return `<div class="gp-photo-gallery" data-photo-model="model-gallery">${Object.entries(images).map(([key,url])=>{const [w,h,x,y,cw,ch]=frames[key],maskId='gp-gallery-mask-'+(++photoSequence),clip=key==='ds4'?`<defs><clipPath id="${maskId}"><path d="${DS4_BODY_PATH}"/></clipPath></defs>`:'',title=key==='ds4'?'DualShock 4':key==='dualsense'?'DualSense':'Xbox Series';return `<figure><svg viewBox="${x} ${y} ${cw} ${ch}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="${title}" class="gp-gallery-photo">${clip}<image clip-path="${key==='ds4'?'url(#'+maskId+')':'none'}" data-controller-photo href="${url}" x="0" y="0" width="${w}" height="${h}" preserveAspectRatio="xMidYMid meet"/></svg><figcaption>${title}</figcaption></figure>`;}).join('')}</div>`;
  }
  const title=model==='dualsense'?'DualSense':model==='ds4'?'DualShock 4':'Xbox Series';
  asset=images[model];prefix=`gp-photo-${++photoSequence}`;cutouts=[];
  const controls=model==='dualsense'?dualsense():model==='ds4'?dualshock4():xbox();
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 65 1000 780" role="img" aria-label="${title}: изображение геймпада с живой индикацией кнопок, стиков и курков" class="gp-controller gp-photo" data-photo-model="${model}"><defs>${model==='ds4'?`<clipPath id="${prefix}-photo-body"><path d="${DS4_BODY_PATH}" transform="translate(-399.36 -28) scale(1.12)"/></clipPath>`:''}
    <filter id="${prefix}-shell-material" data-photo-filter="shell" color-interpolation-filters="sRGB" x="0" y="0" width="100%" height="100%">
      <feColorMatrix in="SourceGraphic" type="saturate" values="0" result="luminance"/>
      <feComponentTransfer in="luminance" result="tinted"><feFuncR type="linear" slope="1" data-material-channel="0"/><feFuncG type="linear" slope="1" data-material-channel="1"/><feFuncB type="linear" slope="1" data-material-channel="2"/></feComponentTransfer>
      <feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  .5325 1.7875 .18 0 -1.3" result="material-mask"/>
      <feComposite in="tinted" in2="material-mask" operator="in" result="colored"/>
      <feComposite in="SourceGraphic" in2="material-mask" operator="out" result="original"/>
      <feMerge><feMergeNode in="original"/><feMergeNode in="colored"/></feMerge>
    </filter>
    <filter id="${prefix}-cap-material" data-photo-filter="cap" color-interpolation-filters="sRGB"><feColorMatrix type="saturate" values="0"/><feComponentTransfer><feFuncR type="linear" slope=".23" intercept=".01"/><feFuncG type="linear" slope=".23" intercept=".01"/><feFuncB type="linear" slope=".23" intercept=".01"/></feComponentTransfer></filter>
    <radialGradient id="${prefix}-socket"><stop offset="0" stop-color="#07090c"/><stop offset=".82" stop-color="#10171d"/><stop offset="1" stop-color="#283038"/></radialGradient>
    <linearGradient id="${prefix}-well" x2="0" y2="1"><stop stop-color="#08111b"/><stop offset=".55" stop-color="#253342"/><stop offset="1" stop-color="#101a25"/></linearGradient>
    <linearGradient id="${prefix}-pressure" x2=".25" y2="1"><stop stop-color="#030b18" stop-opacity=".62"/><stop offset=".38" stop-color="#172a3e" stop-opacity=".24"/><stop offset=".8" stop-color="#d9f2ff" stop-opacity=".02"/><stop offset="1" stop-color="#d9f2ff" stop-opacity=".22"/></linearGradient>
    <linearGradient id="${prefix}-edge" x2="0" y2="1"><stop stop-color="#fff" stop-opacity=".75"/><stop offset=".35" stop-color="#fff" stop-opacity="0"/><stop offset=".75" stop-color="#000" stop-opacity=".08"/><stop offset="1" stop-color="#000" stop-opacity=".36"/></linearGradient>
    <linearGradient id="${prefix}-trigger-face" x2=".25" y2="1"><stop stop-color="#5e6b7b"/><stop offset=".22" stop-color="#354353"/><stop offset=".7" stop-color="#263444"/><stop offset="1" stop-color="#182331"/></linearGradient>
    <linearGradient id="${prefix}-trigger-side" x2="0" y2="1"><stop stop-color="#1b2635"/><stop offset="1" stop-color="#050b12"/></linearGradient>
    <linearGradient id="${prefix}-ps-material" x2=".2" y2="1"><stop stop-color="#a2a7ac"/><stop offset=".3" stop-color="#626b72"/><stop offset=".7" stop-color="#414a51"/><stop offset="1" stop-color="#222a30"/></linearGradient>
    <radialGradient id="${prefix}-floor"><stop stop-color="#010710" stop-opacity=".7"/><stop offset="1" stop-color="#010710" stop-opacity="0"/></radialGradient>
    <mask id="${prefix}-body"><rect width="1000" height="1000" fill="white"/>${cutouts.join('')}</mask>
    </defs><image href="${asset}" ${photoAttributes()} clip-path="${model==='ds4'?'url(#'+prefix+'-photo-body)':'none'}" data-controller-photo data-photo-material="shell" mask="url(#${prefix}-body)"/><g>${controls}</g></svg>`;
  return model==='dualsense'?`<div class="gp-photo-scene"><div class="gp-photo-hardware" aria-live="polite"><strong data-photo-revision>Версия и ревизия —</strong><span data-photo-edition>Чёрно-белый · по умолчанию</span></div><div class="gp-photo-battery" data-photo-battery data-status="unknown" role="img" aria-label="Заряд аккумулятора: нет данных"><svg viewBox="0 0 32 18" aria-hidden="true"><rect x="1" y="3" width="26" height="12" rx="3" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M30 7v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><rect x="4" y="6" width="0" height="6" rx="1" fill="currentColor" data-photo-battery-fill/><path d="m17 1-7 9h5l-2 7 9-10h-6Z" class="gp-photo-battery-bolt" opacity="0" data-photo-battery-bolt/></svg><strong data-photo-battery-value>—</strong></div>${svg}<div class="gp-photo-identity"><span class="gp-photo-serial-caption">Серийный номер</span><button type="button" data-photo-serial disabled aria-label="Серийный номер не прочитан">Не прочитан</button><span data-photo-copy-status role="status" aria-live="polite" aria-atomic="true"></span></div><span class="gp-photo-edition-note" data-photo-edition-note hidden></span></div>`:svg;
}

// The touch surface narrows towards its lower edge in the front photograph.
export function photoTouchPoint(point,model='dualsense'){
  if(model==='ds4'){
    const u=Math.max(0,Math.min(1,point.x/1920)),v=Math.max(0,Math.min(1,point.y/943));
    return [ds4X(680+245*u),ds4Y(262+111*v)];
  }
  const u=Math.max(0,Math.min(1,point.x/1920)),v=Math.max(0,Math.min(1,point.y/1080));
  return [331+338*u+v*(25-50*u),201+180*v];
}
