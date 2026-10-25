// One readiness decision drives the explanation and the explicit save-button action.
export function calibrationReadiness(s){
 const result=(phase,title,message,canSave=false)=>({phase,title,message,canSave});
 if(s.saved)return result('saved','Калибровка записана в геймпад','Контроллер подтвердил запись. Переподключите его и выполните контрольный тест.');
 if(!s.connected)return result('connect','Подключите геймпад для калибровки',s.connecting?'Подключаемся к геймпаду…':s.connectionNotice||'Подключите Sony кабелем USB и нажмите «Разрешить доступ». Если браузер покажет список устройств, выберите свой геймпад и нажмите «Подключить».');
 if(s.blocked)return result('blocked','Сначала устраните причину блокировки',s.blocked);
 if(s.saving)return result('saving','Сохраняем калибровку','Идёт запись в геймпад. Оставьте USB подключённым до сообщения об успехе.');
 if(s.busy)return result('wait','Выполняется проверка',s.operation||'Дождитесь завершения текущего замера или теста.');
 if(!s.dirty)return result('calibrate','Геймпад подключён — можно калибровать','Откройте калибровку, положите геймпад и выберите «Начать автокалибровку» или «Только автоцентр».');
 if(!s.before)return result('blocked','Не хватает исходного замера','Нужен замер «до» в том же подключении. Полностью выключите геймпад и начните новый сеанс.');
 if(!s.rest)return result('rest','Снимите контрольный замер','Отпустите стики и нажмите «Замер после». После замера запись кругов включится автоматически.');
 const coverage=[0,1].map(i=>Number.isFinite(s.coverage?.[i])?Math.max(0,Math.min(100,s.coverage[i])):0);
 if(coverage.some(n=>n<95))return result('verify','Обведите полный край обоими стиками',`Круги записываются автоматически: левый ${Math.round(coverage[0])}% · правый ${Math.round(coverage[1])}%. Медленно заполните оба круга минимум до 95%. Нажимать отдельную кнопку не нужно.`);
 if(s.circleActive)return result('wait','Завершаем проверку кругов','Дождитесь фиксации результата.');
 if(s.persistentSave===false)return result('save-blocked','Доступна только временная калибровка','Для этой модели проверка параметров перед постоянной записью пока недоступна. Результат действует до выключения геймпада; сохранение в память заблокировано.');
 return result('ready','Можно сохранить калибровку','Нажмите «Сохранить в геймпад». Во время записи оставьте USB подключённым.',true);
}

export function createCalibrationGuide(s,api){
 const q=selector=>s.q(selector),guide=document.createElement('section');guide.className='gp-flow-guide';
 guide.setAttribute('aria-label','Порядок калибровки');
 guide.innerHTML='<ol class="gp-flow-steps">'+['Подключение','Калибровка','Проверка кругов','Сохранение'].map((text,i)=>`<li data-flow-step="${i}"><b>${i+1}</b><span>${text}</span></li>`).join('')+'</ol><div class="gp-flow-copy"><strong data-flow-title></strong><p data-flow-message></p></div><button type="button" data-flow-next class="gp-primary"></button>';
 q('.gp-tabs').before(guide);
 const save=q('[data-gp="flash"]').closest('section');save.className='gp-save-card gp-module';save.setAttribute('aria-label','Сохранение калибровки');
 save.querySelector('h4').textContent='Сохранение калибровки в геймпад';
 const saveIntro=save.querySelector('p');
 const checks=document.createElement('ul');checks.className='gp-save-checks';
 checks.innerHTML=['USB подключён','Калибровка выполнена','Замеры до / после','Оба круга проверены','Модель поддерживает проверяемую запись'].map((text,i)=>`<li data-save-check="${i}"><span aria-hidden="true">○</span> ${text}</li>`).join('');
 save.querySelector('.gp-actions').before(checks);q('.gp-manual').before(save);
 q('.gp-manual summary').textContent='Ручная калибровка — дополнительные настройки';
 q('[data-save-help]').setAttribute('role','status');
 q('[data-gp="flash"]').setAttribute('aria-describedby','gp-save-help');
 let phase='connect';
 s.on(q('[data-flow-next]'),'click',()=>api.next(phase));
 return {update(state){
  const readiness=calibrationReadiness(state);phase=readiness.phase;
  q('[data-flow-title]').textContent=readiness.title;q('[data-flow-message]').textContent=readiness.message;
  const button=q('[data-flow-next]'),actions={connect:'Разрешить доступ к геймпаду',calibrate:'Открыть калибровку',rest:'Замер после · 3 с',verify:'Показать круги',ready:'Сохранить в геймпад'};
  button.hidden=!actions[phase];button.textContent=actions[phase]??'';button.disabled=phase==='connect'&&(!state.available||state.connecting||state.busy);
  if(phase==='connect'&&!state.available)q('[data-flow-message]').textContent=state.unavailable||'Загружаем инструмент…';
  const step=phase==='saved'?4:!state.connected?0:!state.dirty?1:!state.rest||state.coverage?.some(n=>n<95)?2:3;
  for(const el of guide.querySelectorAll('[data-flow-step]')){const n=Number(el.dataset.flowStep);el.classList.toggle('is-done',n<step);el.classList.toggle('is-current',n===step);if(n===step)el.setAttribute('aria-current','step');else el.removeAttribute('aria-current');}
  const checksDone=[state.connected,state.dirty||state.saved,state.before&&state.rest,state.rest&&state.coverage?.length===2&&state.coverage.every(n=>n>=95),state.connected&&state.persistentSave===true];
  for(const el of checks.querySelectorAll('[data-save-check]')){const done=Boolean(checksDone[Number(el.dataset.saveCheck)]);el.classList.toggle('is-done',done);el.querySelector('span').textContent=done?'✓':'○';}
  saveIntro.textContent=state.persistentSave===false?'Для этой модели доступна временная калибровка до выключения геймпада. Проверка параметров перед постоянной записью пока недоступна.':readiness.canSave?'Всё готово. Одно нажатие сохранит настройки в память геймпада.':state.saved?'Калибровка сохранена. После переподключения выполните контрольный тест.':state.dirty?'Изменения пока временные. Постоянная запись станет доступна после контрольного замера и проверки обоих кругов.':'После калибровки и проверки кругов сохраните результат одним нажатием.';
  save.dataset.state=phase;if(q('[data-save-help]').textContent!==readiness.message)q('[data-save-help]').textContent=readiness.message;
  return readiness;
 }};
}
