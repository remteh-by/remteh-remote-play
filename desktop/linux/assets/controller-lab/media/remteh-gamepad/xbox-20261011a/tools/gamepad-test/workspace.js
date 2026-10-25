import {esc} from '/media/remteh-gamepad/v20261011/common.js';

const icons={
 test:'<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
 calibration:'<circle cx="12" cy="12" r="7"/><path d="M12 2v4m0 12v4M2 12h4m12 0h4"/><circle cx="12" cy="12" r="1"/>',
 triggers:'<path d="M7 4h10l2 6v8a2 2 0 0 1-2 2h-3v-7h-4v7H7a2 2 0 0 1-2-2v-8zM2 8v8m20-8v8"/>',
 touch:'<rect x="3" y="4" width="18" height="14" rx="3"/><circle cx="9" cy="10" r="1"/><circle cx="15" cy="12" r="1"/><path d="M8 21h8"/>',
 audio:'<path d="M3 10v4m4-7v10m5-14v18m5-14v10m4-7v4"/>',
 device:'<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4m6-4v4M9 18v4m6-4v4M2 9h4m-4 6h4m12-6h4m-4 6h4"/>',
 comparison:'<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9zM14 3v6h6M8 13h8m-8 4h5"/>',
 expand:'<path d="M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5"/>',
};
export const icon=key=>`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icons[key]??icons.test}</svg>`;
export function tabMarkup(key,name,index){
 const short={test:'Обзор',calibration:'Стики',triggers:'Курки',touch:'Тачпад',audio:'Звук',device:'Устройство',comparison:'Отчёт'}[key];
 return `<button type="button" role="tab" id="gp-tab-${key}" aria-label="${esc(name)}" aria-controls="gp-panel-${key}" aria-selected="${index===0}" tabindex="${index===0?0:-1}" data-tab="${key}" data-tab-name="${esc(name)}" data-tab-short="${short}">${icon(key)}<span class="gp-tab-full">${esc(name)}</span><span class="gp-tab-short" aria-hidden="true">${short}</span></button>`;
}

const profileTabNames={
 xbox:{calibration:['Стики','Стики'],triggers:['LT / RT и вибрация','LT / RT'],device:['Устройство','Устройство']},
 generic:{calibration:['Стики','Стики'],triggers:['Курки и вибрация','Курки'],device:['Устройство','Устройство']},
};

function tabName(profile,key,fallback){
 const family=profile?.isXbox?'xbox':profile?.family==='sony'?'sony':'generic';
 return profileTabNames[family]?.[key]??fallback;
}
export function overviewMarkup(button){
 return `<section class="gp-module gp-map-card"><header><div><span class="gp-eyebrow" data-overview-eyebrow>КНОПКИ И ТАЧПАД</span><h3>Нажимайте на геймпаде</h3></div><span class="gp-live-badge" data-lab-connected>Ожидание геймпада</span></header><div data-controller-diagram></div><div class="gp-map-legend"><span><i class="gp-legend-pressed"></i>Нажато сейчас</span><span><i class="gp-legend-seen"></i>Уже проверено</span></div><p class="gp-small" data-map-note></p><div class="gp-button-check"><p data-button-hint role="status">Нажмите и отпустите каждую кнопку</p><div data-button-pending class="gp-button-pending" aria-label="Ещё не проверены"></div><details class="gp-button-details"><summary>Счётчики нажатий и повторов</summary><p class="gp-small">Цикл — нажатие и отпускание. Повторы быстрее 80 мс помогают найти подозрительную кнопку, но сами по себе не доказывают дребезг.</p><div data-button-counters class="gp-button-counters"></div></details>${button('reset-buttons','Начать проверку кнопок заново','gp-text-action')}</div><div data-button-zone></div><div class="gp-overview-stats"><div><small>Нажаты и отпущены</small><strong data-overview-buttons>0 / 0</strong></div><div><small data-overview-trigger-label>Полный ход курков</small><strong data-overview-triggers>0 / 2</strong></div><div title="Быстрые повторные нажатия — повод перепроверить кнопку, а не автоматический диагноз дребезга."><small>Повторы &lt; 80 мс</small><strong data-repeat-count>0</strong></div></div></section>
 <section class="gp-module gp-live-card"><header><div><span class="gp-eyebrow">ТОЧНОСТЬ СТИКОВ</span><h3>Положение и замеры</h3></div>${button('go-calibration','Калибровка →','gp-text-action')}</header><div data-overview-instruments></div><div class="gp-trigger-summary"><header><h3 data-overview-trigger-title>Ход курков</h3>${button('go-triggers','Полный тест →','gp-text-action')}</header><div data-trigger-zone></div></div><div class="gp-overview-next"><span data-quick-report>Результаты появятся по мере проверки</span>${button('go-report','Открыть отчёт','gp-text-action')}</div></section>`;
}

export function prepareWorkspace(s,api){
 const q=selector=>s.q(selector),root=q('.gp-workbench'),overview=q('[data-overview-instruments]');
 const instruments=document.createElement('div');instruments.className='gp-instruments';
 const toolbar=document.createElement('div');toolbar.className='gp-plot-tools';
 toolbar.innerHTML='<div role="group" aria-label="Масштаб графиков стиков"><span>Масштаб</span><button type="button" data-zoom="1" aria-pressed="true">1×</button><button type="button" data-zoom="10" aria-pressed="false" title="Увеличить центр для проверки небольшого дрейфа">10× · центр</button></div><button type="button" data-clear-trail>Очистить след</button>';
 let zoom=1;
 function setZoom(value){zoom=value===10?10:1;toolbar.querySelectorAll('[data-zoom]').forEach(el=>el.setAttribute('aria-pressed',String(Number(el.dataset.zoom)===zoom)));}
 toolbar.querySelectorAll('[data-zoom]').forEach(el=>s.on(el,'click',()=>setZoom(Number(el.dataset.zoom))));
 s.on(toolbar.querySelector('[data-clear-trail]'),'click',()=>api.clearTrail());
 instruments.append(toolbar,q('.gp-dials'),q('.gp-measure-bar'),q('[data-wizard]'));
 const calibration=document.createElement('div');calibration.className='gp-calibration-instruments';
 q('#gp-panel-calibration').prepend(calibration);overview.append(instruments);
 q('[data-trigger-zone]').append(q('.gp-triggers'));
 q('[data-button-zone]').append(q('.gp-buttons-block'));
 q('.gp-buttons-block h3').textContent='Проверка кнопок';
 q('.gp-buttons-block > p').textContent='Каждая нажатая кнопка получает отметку.';
 q('#gp-panel-test > .gp-small').hidden=true;
 q('[data-rate]').title='Частота получения данных в браузере. Это не измерение задержки USB.';
 for(const el of s.root.querySelectorAll('[data-trigger]'))el.setAttribute('aria-label',`Ход ${el.dataset.trigger==='0'?'L2 / LT':'R2 / RT'}`);
 for(const el of s.root.querySelectorAll('[data-live-radius]'))el.title='Текущее отклонение от центра. Для оценки дрейфа отпустите стики и выполните замер покоя.';
 const help=document.createElement('details');help.className='gp-measure-help';help.innerHTML='<summary>Как оценивается результат</summary>';
 help.append(q('[data-thresholds]'));q('.gp-footer').prepend(help);
 const extra=document.createElement('p');extra.textContent='Значение «сейчас» меняется при движении стика. Дрейф и шум оцениваются после неподвижного замера; неполный круг не считается проверенным.';help.append(extra);

 const focusButton=document.createElement('button');focusButton.type='button';focusButton.className='gp-focus-toggle';focusButton.setAttribute('aria-pressed','false');focusButton.innerHTML=icon('expand')+'<span>Развернуть</span>';q('.gp-connect-actions').append(focusButton);
 const page=s.root.closest('.diag-page');let focused=false,previousOverflow='',background=[];
 function setFocus(next){
  if(!page||focused===next)return;
  if(next){
   previousOverflow=document.documentElement.style.overflow;
   // Keep keyboard focus in the visible workspace and restore the CRM on exit.
   for(let node=page;node.parentElement;node=node.parentElement){
    for(const sibling of node.parentElement.children){
     if(sibling===node||!(sibling instanceof HTMLElement))continue;
     background.push([sibling,sibling.inert]);sibling.inert=true;
    }
    if(node.parentElement===document.body)break;
   }
  }else{for(const [element,inert]of background)element.inert=inert;background=[];}
  focused=next;page.classList.toggle('gp-focused',next);document.documentElement.style.overflow=next?'hidden':previousOverflow;
  focusButton.setAttribute('aria-pressed',String(next));focusButton.querySelector('span').textContent=next?'Свернуть · Esc':'Развернуть';
  if(next)page.scrollTop=0;
 }
 s.on(focusButton,'click',()=>setFocus(!focused));
 s.on(document,'keydown',event=>{if(event.key==='Escape')setFocus(false);});
 s.clean(()=>setFocus(false));
 function setTab(key){
  root.dataset.activeTab=key;
  const target=key==='test'?overview:calibration;
  if(instruments.parentElement!==target)target.append(instruments);
 }
 function applyProfile(profile,supported){
  const supportedTabs=new Set(supported),family=profile?.family??'none';
  root.dataset.controllerProfile=profile?.id??'none';root.dataset.controllerFamily=family;
  root.classList.toggle('gp-xbox-profile',profile?.isXbox===true);
  root.classList.toggle('gp-sony-profile',family==='sony');
  for(const el of root.querySelectorAll('.gp-tabs [data-tab]')){
   const key=el.dataset.tab,available=supportedTabs.has(key),fallback=[el.dataset.tabName||key,el.dataset.tabShort||key];
   const [full,short]=tabName(profile,key,fallback);
   el.hidden=!available;el.setAttribute('aria-hidden',String(!available));
   el.querySelector('.gp-tab-full').textContent=full;el.querySelector('.gp-tab-short').textContent=short;el.setAttribute('aria-label',full);
  }
  const xbox=profile?.isXbox===true;
  q('[data-overview-eyebrow]').textContent=xbox?'КНОПКИ И СТИКИ':'КНОПКИ И ТАЧПАД';
  q('[data-lab="go-calibration"]').textContent=xbox?'Проверка стиков →':'Калибровка →';
  q('[data-overview-trigger-label]').textContent=xbox?'Полный ход LT / RT':'Полный ход курков';
  q('[data-overview-trigger-title]').textContent=xbox?'Ход LT / RT':'Ход курков';
  for(const el of root.querySelectorAll('[data-trigger]')){
   const left=el.dataset.trigger==='0',label=xbox?(left?'LT':'RT'):(left?'L2 / LT':'R2 / RT');
   el.setAttribute('aria-label',`Ход ${label}`);const text=el.parentElement?.querySelector('span');if(text)text.textContent=label;
  }
 }
 setTab('test');
 return {setTab,applyProfile,setZoom,get zoom(){return zoom;},lockZoom(locked){toolbar.querySelector('[data-zoom="10"]').disabled=locked;if(locked)setZoom(1);}};
}
