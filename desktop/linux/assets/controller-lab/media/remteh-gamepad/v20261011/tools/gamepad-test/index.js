import {tool, t, esc, png} from '/media/remteh-gamepad/v20261011/common.js';
import {createLab} from '/media/remteh-gamepad/xbox-rumble-20261011a/tools/gamepad-test/lab.js';
import {CircleTrace, restStats, verdict, flatten, round} from '/media/remteh-gamepad/v20261011/tools/gamepad-test/measurements.js';
import {createCalibrationGuide} from '/media/remteh-gamepad/v20261011/tools/gamepad-test/calibration-guidance.js';
import {createCircleTuning, precisionResultStatus} from '/media/remteh-gamepad/calibration-20261020b/circle-tuning.js';
import {controllerBattery} from '/media/remteh-gamepad/v20261011/tools/gamepad-test/controller-identity.js';
import {teardownGamepadSession} from '/media/remteh-gamepad/v20261011/tools/gamepad-test/teardown.js';
import {getControllerProfile,standardButtonKey,buttonLabel} from '/media/remteh-gamepad/xbox-detection-20261011a/tools/gamepad-test/controller-profile.js';
import {controllerFingerprint,matchingFingerprintCount,createModelChoiceStore} from '/media/remteh-gamepad/photo-fix-20261011a/tools/gamepad-test/model-choice.js';

const signed=n=>`${n>=0?'+':''}${n.toFixed(4)}`;
const percent=n=>`${n.toFixed(2)}%`;
const fresh=frame=>frame && performance.now()-frame.at<1500;

export default tool('gamepad-test', s => {
  const T=(key,params={})=>Object.entries(params).reduce((str,[k,v])=>str.replaceAll(`{${k}}`,String(v)),t(s.ctx,key));
  const H=key=>esc(T(key));
  const btn=(action,key,classes='')=>`<button type="button" data-gp="${action}" class="${classes}">${H(key)}</button>`;
  s.html(`<style>@media(max-width:760px){#sp-page-builder.page-555 #gpd #diag-tool .gp-tabs button:focus-visible{outline-offset:-3px}}</style><div class="gp-workbench">
    <div class="gp-connect-row"><div class="gp-device-heading"><span class="gp-device-icon" aria-hidden="true">⌁</span><div><h2 data-name>${H('gp_empty')}</h2><p data-connection>${H('gp_intro')}</p></div></div><div class="gp-connect-actions">${btn('connect','gp_connect','gp-primary')}<button type="button" data-gp="choose">Выбрать другой Sony</button>${btn('disconnect','disconnect')}</div></div>
    <div class="gp-select-row"><label for="gp-device-select">${H('gp_picker')}</label><select id="gp-device-select"><option value="">${H('gp_no_pad')}</option></select><span class="gp-chip" data-source>—</span><span class="gp-chip" data-battery>${H('gp_battery')}: —</span><span class="gp-chip" data-rate>${H('gp_rate')}: —</span></div>
    <div data-model-choice hidden><div class="gp-select-row"><label for="gp-model-select">Модель геймпада</label><select id="gp-model-select" aria-describedby="gp-model-help"><option value="">Автоматически</option><option value="xbox-series">Xbox Series</option><option value="xbox-one">Xbox One</option><option value="dualsense">DualSense</option><option value="ds4">DualShock 4</option></select></div><p id="gp-model-help" class="gp-small"></p></div>
    <p class="gp-message" data-message role="status" aria-live="polite"></p>
    <progress data-rest-progress max="3" value="0" hidden></progress>
    <nav class="gp-tabs" role="tablist" aria-label="${H('gp_title')}">${['test','calibration','comparison'].map((key,i)=>`<button type="button" role="tab" id="gp-tab-${key}" aria-controls="gp-panel-${key}" aria-selected="${i===0}" tabindex="${i===0?0:-1}" data-tab="${key}">${H('gp_'+key)}</button>`).join('')}</nav>
    <div class="gp-dials">${[0,1].map(i=>`<section class="gp-dial"><header><h3>${H(i?'gp_right_stick':'gp_left_stick')}</h3><span data-live-radius="${i}">—</span></header><canvas width="520" height="400" data-dial="${i}" aria-label="${H(i?'gp_right_stick':'gp_left_stick')}"></canvas><div class="gp-axis-values"><span>X <b data-axis="${i*2}">—</b></span><span>Y <b data-axis="${i*2+1}">—</b></span></div><div class="gp-dial-metrics"><div><span>${H('gp_offset')}</span><strong data-offset="${i}">—</strong></div><div><span>${H('gp_noise')}</span><strong data-noise="${i}">—</strong></div><div><span title="Среднеквадратичное отклонение радиуса от эталонной окружности. Показатель 0% не обязателен для DualSense.">${H('gp_circle_error')} (RMS)</span><strong data-circle="${i}">—</strong></div></div><div class="gp-coverage"><span>${H('gp_coverage')}</span><progress max="100" value="0" data-coverage="${i}"></progress><b data-coverage-value="${i}">0%</b></div></section>`).join('')}</div>
    <section role="tabpanel" id="gp-panel-test" aria-labelledby="gp-tab-test">
      <div class="gp-measure-bar"><div><h3>${H('gp_stage')}: <span data-stage>${H('gp_before')}</span></h3><p>${H('gp_measure_hint')}</p></div><div class="gp-actions">${btn('before','gp_measure_before','gp-primary')}${btn('after','gp_measure_after')}${btn('circle','gp_circle_start')}${btn('reset','gp_reset')}</div></div>
      <div class="gp-buttons-block"><header><h3>${H('gp_buttons')}</h3><span data-buttons-count>${H('gp_tested')}: 0</span></header><p>${H('gp_buttons_hint')}</p><div class="gp-buttons" data-buttons></div><div class="gp-triggers">${[0,1].map(i=>`<div><span>${i?'R2 / RT':'L2 / LT'}</span><progress data-trigger="${i}" max="1" value="0"></progress><b data-trigger-value="${i}">—</b></div>`).join('')}</div><div class="gp-actions">${btn('rumble-left','gp_rumble_left')}${btn('rumble-right','gp_rumble_right')}${btn('rumble-both','gp_rumble_both')}</div></div>
      <details class="gp-extra" data-sony-extra hidden><summary>${H('gp_touch')} · ${H('gp_motion')}</summary><p>${H('gp_touch_hint')}</p><div class="gp-extra-grid"><canvas width="420" height="220" data-touch aria-label="${H('gp_touch')}"></canvas><dl><dt>${H('gp_motion')}</dt><dd data-gyro>—</dd><dt>${H('gp_accel')}</dt><dd data-accel>—</dd></dl></div></details>
      <p class="gp-small">${H('gp_rate_note')}</p>
    </section>
    <section role="tabpanel" id="gp-panel-calibration" aria-labelledby="gp-tab-calibration" hidden>
      <div class="gp-calib-intro"><h3>${H('gp_calibration')} · DS4 / DualSense / Edge</h3><p>${H('gp_calib_intro')}</p><p data-calib-gate class="gp-gate">${H('gp_no_sony')}</p><dl data-device-info class="gp-device-info"></dl></div>
      <div class="gp-calib-steps"><section><h4>${H('gp_step1')}</h4><p>${H('gp_step1_hint')}</p><div class="gp-actions">${btn('calib-before','gp_measure_before')}${btn('calib-before-circle','gp_circle_start')}</div><span data-before-status class="gp-small">${H('gp_no_measure')}</span></section>
      <section><h4>${H('gp_step2')}</h4><p>${H('gp_step2_hint')}</p><div class="gp-actions">${btn('center','gp_center')}${btn('range','gp_range')}</div></section>
      <section><h4>${H('gp_step3')}</h4><p>${H('gp_step3_hint')}</p><div class="gp-actions">${btn('calib-after','gp_measure_after')}${btn('calib-after-circle','gp_circle_start')}</div><div class="gp-save-row">${btn('flash','gp_save','gp-primary')}</div><p id="gp-save-help" data-save-help class="gp-small">${H('gp_save_need')}</p></section></div>
      <section class="gp-wizard" data-wizard hidden><div><span data-direction class="gp-direction" aria-hidden="true">↖</span><div><h3 data-wizard-title></h3><p data-wizard-instruction></p><p data-wizard-progress class="gp-small"></p></div></div><div class="gp-actions">${btn('center-next','gp_center_next','gp-primary')}${btn('range-end','gp_range_finish','gp-primary')}${btn('cancel','gp_cancel')}</div></section>
      <p data-memory-message class="gp-message"></p>
    </section>
    <section role="tabpanel" id="gp-panel-comparison" aria-labelledby="gp-tab-comparison" hidden><h3>${H('gp_comparison')}</h3><p data-comparison-hint>${H('gp_comparison_hint')}</p><div class="gp-table-scroll"><table class="gp-compare"><thead><tr><th>${H('gp_parameter')}</th><th><span class="gp-before-dot"></span>${H('gp_before')}</th><th><span class="gp-after-dot"></span>${H('gp_after')}</th></tr></thead><tbody data-compare></tbody></table></div><p class="gp-small">${H('gp_result_hint')}</p></section>
    <footer class="gp-footer"><p data-thresholds></p><details><summary>${H('gp_license')}</summary><p>${H('gp_license_text')}</p><a data-license target="_blank" rel="noopener">${H('gp_license_link')}</a></details><span class="gp-local"><span aria-hidden="true">●</span> ${H('gp_local')}</span></footer>
  </div>`);
  const q=selector=>s.q(selector), qa=selector=>[...s.root.querySelectorAll(selector)], action=name=>q(`[data-gp="${name}"]`);
  const $message=q('[data-message]'), $picker=q('#gp-device-select'), $modelPicker=q('#gp-model-select');
  const rememberedModels=createModelChoiceStore(),sessionModels=new Map();
  const dials=qa('[data-dial]'), axisEls=qa('[data-axis]'), triggerEls=qa('[data-trigger]'), triggerValues=qa('[data-trigger-value]');
  let engine=null, engineReady=false, engineState={}, source=null, frame=null, selectedIndex=null, browserSignature='', browserTimestamp=null, optionsKey='', buttonsKey='', seen=new Set(), buttonEls=new Map(), before=null, after=null, stage='before', measure=null, circleActive=false, circleTrace=null, trails=[[],[]], counter=0, rate=0, rateAt=performance.now(), lastDraw=0, lastUi=0, localBusy=false, resultVersion=0, centerStep=0, cornersSeen=[false,false], releasedSince=0, rangeTrace=null, chosenTab='test', rumbleActive=false, reportDirty=false, lastReport=0, triggerMin=[1,1], triggerMax=[0,0];
  const data={before:{rest:null,circle:null},after:{rest:null,circle:null}};
  let tuning=null,lab=null,autoJob=null,autoSerial=0,verificationTrace=null,saving=false,connectionNotice='',engineLoad='loading',engineLoadAttempt=0,engineLoadPromise=null;
  lab=createLab(s,{engine:()=>engine,state:()=>engineState,frame:()=>frame,source:()=>source,profile:()=>getControllerProfile(source,frame),busy:()=>Boolean(localBusy||engineState.busy||measure||circleActive||autoJob||tuning?.active),changed:()=>{markEvidence();},message:text=>{$message.textContent=text;$message.dataset.notice='';},tab:setTab,auto:startAuto,cancelAuto,autoActive:()=>Boolean(autoJob),clearTrail:()=>{trails=[[],[]];},resetButtons:()=>{seen.clear();markEvidence();s.ctx.onReset?.();},measurementHint:()=>!data[stage].rest?'Отпустите стики и выполните замер покоя':!data[stage].circle?.results.every(r=>r.complete)?'Замер покоя готов. Теперь проверьте круги.':'Замеры стиков готовы. Проверьте остальные узлы.',export:()=>({...tuning?.report?.metrics,...flatten(data.before.rest,data.before.circle,'before_'),...flatten(data.after.rest,data.after.circle,'after_')})});
  const guide=createCalibrationGuide(s,{next:phase=>{
    if(phase==='connect'){if(engineReady&&!engineState.connected)void perform(()=>engine.connect());return;}
    if(phase==='ready'){saveCalibration();return;}
    setTab('calibration',true);
    if(phase==='rest')startMeasure('after');
    const target=phase==='verify'?q('.gp-calibration-instruments'):q('.gp-auto-card');
    target.scrollIntoView({block:'center',behavior:'smooth'});
  }});
  tuning=createCircleTuning(s,{changed:()=>{markEvidence();},engine:()=>engine,state:()=>engineState,busy:()=>Boolean(localBusy||engineState.busy||measure||circleActive||autoJob||lab.active),
    startup:()=>({load:engineLoad,reason:engineState.mode||autoJob?'calibration_active':localBusy||engineState.busy?'operation_busy':lab.active?'test_active':null,measurement:circleActive?'circle':measure?'rest':null,source:source?.kind??'none'}),
    retryEngine:()=>loadEngine(),prepareStart:finishPassiveMeasurements});
  const message=(key,params={})=>{$message.textContent=T(key,params);$message.dataset.notice=key;};
  const reportError=e=>message(s.ctx.texts['gp_error_'+e?.message]?'gp_error_'+e.message:'gp_error_generic');
  function resetMeasurements(resetLab=true){verificationTrace=null;autoJob=null;autoSerial++;if(resetLab)lab?.reset();lab?.setZoom(1);q('[data-auto-status]').textContent='';q('[data-auto-progress]').value=0;resultVersion++;before=after=null;data.before={rest:null,circle:null};data.after={rest:null,circle:null};measure=null;circleActive=false;circleTrace=null;stage='before';if(resetLab){seen=new Set();triggerMin=[1,1];triggerMax=[0,0];}reportDirty=!resetLab;trails=[[],[]];counter=0;rate=0;rateAt=performance.now();rangeTrace=null;centerStep=0;cornersSeen=[false,false];releasedSince=0;q('[data-rest-progress]').hidden=true;s.ctx.onReset?.();updateComparison();}
  function markEvidence(){reportDirty=true;resultVersion++;}
  function frameButtonLabel(key){const profile=getControllerProfile(source,frame);return source?.kind==='hid'?buttonLabel(key,profile):source?.standard?buttonLabel(standardButtonKey(Number(key),profile),profile):'B'+key;}
  function updateModelChoiceUi(next,profile=getControllerProfile(next,frame)){
    q('[data-model-choice]').hidden=!profile.canChooseModel;
    $modelPicker.value=profile.identityOrigin==='manual'?next.userModel:'';
    q('#gp-model-help').textContent=profile.identityOrigin==='manual'?(next.modelChoiceRemembered?'Вы выбрали эту модель ранее для геймпада с таким же названием и раскладкой. При необходимости измените выбор или включите «Автоматически». Тесты используют только реальные данные подключённого геймпада.':'Модель выбрана вами. Тесты используют только реальные данные подключённого геймпада.'):(next?.identicalSourceCount>1?'Подключено несколько геймпадов с одинаковым названием и раскладкой. Сохранённая модель не применяется автоматически — выберите модель текущего устройства.':'Браузер не сообщил точную модель. Выберите её для фото и обозначений кнопок.');
  }
  function setSource(next){
    const sameIdentity=source?.key===next?.key&&source?.userModel===next?.userModel&&source?.modelChoiceRemembered===next?.modelChoiceRemembered&&source?.modelChoiceFingerprint===next?.modelChoiceFingerprint;
    if(sameIdentity){const countChanged=source?.identicalSourceCount!==next?.identicalSourceCount;source=next;if(countChanged)updateModelChoiceUi(next);return;}
    // Stop the old actuator while its frame is still reachable.
    resetMeasurements();
    source=next;frame=null;browserTimestamp=null;browserSignature='';buttonsKey='';
    const profile=getControllerProfile(source,frame),workbench=q('.gp-workbench');
    updateModelChoiceUi(source,profile);
    workbench.dataset.controllerFamily=profile.family;workbench.dataset.controllerModel=profile.id;
    q('[data-name]').textContent=next?(profile.family==='generic'?next.name:profile.label):T('gp_empty');
    q('[data-name]').title=next?.name??'';
    q('[data-connection]').textContent=next?(next.kind==='hid'?'Sony · USB · '+next.model:profile.isXbox?'Кнопки, стики, курки и вибрация · Gamepad API':'Gamepad API'):T('gp_intro');
    q('[data-source]').textContent=next?.kind==='hid'?'USB / WebHID':next?'Gamepad API':'—';
    if(next&&profile.family!=='sony')connectionNotice='';
    if(next?.kind==='hid'){connectionNotice='';message('gp_connected');}
    else if(connectionNotice){$message.textContent=connectionNotice;$message.dataset.notice='';}
    else if(next)message('gp_connected');else $message.textContent='';
    lab.update();
    setTab(lab.supportsTab?.(chosenTab)===false?'test':chosenTab);
    updateComparison();
    s.ctx.onEvent?.({type:'gamepad-profile',profile});
  }
  function setTab(key,focus=false){
    if(lab?.supportsTab?.(key)===false)key='test';
    chosenTab=key;lab?.setTab(key);s.ctx.onEvent?.({type:'gamepad-tab',tab:key});
    qa('[data-tab]').forEach(el=>{const active=el.dataset.tab===key&&!el.hidden;el.setAttribute('aria-selected',String(active));el.tabIndex=active?0:-1;if(active&&focus){el.focus({preventScroll:true});const list=el.closest('[role="tablist"]');if(list){const tabRect=el.getBoundingClientRect(),listRect=list.getBoundingClientRect();if(tabRect.left<listRect.left)list.scrollLeft-=listRect.left-tabRect.left;else if(tabRect.right>listRect.right)list.scrollLeft+=tabRect.right-listRect.right;}}q('#gp-panel-'+el.dataset.tab).hidden=!active;});
  }
  qa('[data-tab]').forEach(el=>{s.on(el,'click',()=>setTab(el.dataset.tab));s.on(el,'keydown',e=>{const keys=lab.tabs;let i=keys.indexOf(el.dataset.tab);if(e.key==='ArrowRight')i=(i+1)%keys.length;else if(e.key==='ArrowLeft')i=(i+keys.length-1)%keys.length;else if(e.key==='Home')i=0;else if(e.key==='End')i=keys.length-1;else return;e.preventDefault();setTab(keys[i],true);});});
  q('[data-thresholds]').textContent=T('gp_thresholds',{center:round(s.ctx.thresholds.center_offset_warn*100,1),noise:round(s.ctx.thresholds.noise_warn*100,1),circle:s.ctx.thresholds.circularity_warn});
  const engineUrl=s.ctx.engineUrl;
  if(engineUrl){const url=new URL(engineUrl,location.href);if(url.origin===location.origin)q('[data-license]').href=new URL('/media/remteh-gamepad/recheck-20261011a/licenses/dualshock-tools.html',import.meta.url).href;}
  function loadEngine(){
    if(engineReady||s.dead)return Promise.resolve();
    if(engineLoadPromise)return engineLoadPromise;
    if(!navigator.hid||!engineUrl){engineLoad='unavailable';return Promise.resolve();}
    engineLoad='loading';
    const url=new URL(engineUrl,location.href);
    // A failed module import is cached by the browser. A user-requested retry
    // needs a fresh URL; it only loads code and never opens or writes a device.
    if(engineLoadAttempt++)url.searchParams.set('retry',String(engineLoadAttempt));
    engineLoadPromise=import(url.href).then(({createSonyEngine})=>{
    if(s.dead)return;engine=createSonyEngine({onFrame:input=>acceptFrame({...input,at:performance.now(),standard:true}),onState:state=>{
      const previous=engineState;engineState=state;
      if(previous.connected&&!state.connected)connectionNotice=previous.saved?'USB-сеанс закрыт. Калибровка была сохранена; подключитесь для контрольного теста.':'USB-сеанс калибровки закрыт. Для сохранения нужно снова подключить Sony и выполнить калибровку. Режим обычного теста не записывает настройки в геймпад.';
      if(s.dead){if(state.connected&&!state.busy)void engine.disconnect();return;}
      if(state.connected){const info=state.info;setSource({key:'hid:'+engine.connection,kind:'hid',name:info.name||info.model,model:info.model,standard:true});q('[data-device-info]').replaceChildren();for(const [key,value] of Object.entries(info.fields)){const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=({'Serial Number':'Серийный номер','Color':'Заводская расцветка','SW Version':'ПО','FW Version':'Внутренняя сборка','FW Update':'Версия прошивки','FW Build Date':'Дата сборки','FW Type':'Тип ПО','FW Update Info':'Вариант образа','HW Model':'Аппаратная ревизия','Board Model':T('gp_board')})[key]??key;dd.textContent=value;q('[data-device-info]').append(dt,dd);}}
      else if(source?.kind==='hid') {q('[data-device-info]').replaceChildren();setSource(null);if(!connectionNotice)message('gp_error_disconnected');}
      updateControls();
    }});engineReady=true;engineLoad='ready';updateControls();
    }).catch(()=>{engineLoad='failed';if(!s.dead)message('gp_error_load');})
      .finally(()=>{engineLoadPromise=null;});
    return engineLoadPromise;
  }
  if(!navigator.hid || !engineUrl){engineLoad='unavailable';message('gp_no_hid');action('connect').hidden=true;action('choose').hidden=true;}
  else void loadEngine();

  function finishPassiveMeasurements(){
    // These observations do not write to the controller. Keep the collected
    // circles for comparison, but release the passive test before the wizard.
    measure=null;q('[data-rest-progress]').hidden=true;
    if(circleActive){data[stage].circle=circleTrace;circleActive=false;}
    verificationTrace=null;updateComparison();
  }

  function acceptFrame(input){
    if(!source || input.axes.length<4 || input.axes.some(v=>!Number.isFinite(v)))return;
    frame=input;counter++;
    lab.accept(frame);tuning?.accept(frame);
    for(const [key,value] of Object.entries(frame.buttons))if(value>.5&&!seen.has(key)){seen.add(key);markEvidence();}
    for(let i=0;i<2;i++){if(frame.triggers[i]<triggerMin[i]||frame.triggers[i]>triggerMax[i])markEvidence();triggerMin[i]=Math.min(triggerMin[i],frame.triggers[i]);triggerMax[i]=Math.max(triggerMax[i],frame.triggers[i]);}
    if(measure && performance.now()-measure.last>=2){measure.samples.push(frame.axes.slice(0,4));measure.last=performance.now();}
    if(circleActive)circleTrace.add(frame.axes);
    if(verificationTrace&&!document.hidden&&!measure&&!circleActive&&!autoJob&&!engineState.mode&&!engineState.busy&&!localBusy&&!lab.active)verificationTrace.add(frame.axes);
    if(engineState.mode==='range'&&rangeTrace)rangeTrace.add(frame.axes);
    if(engineState.mode==='center'){
      const target=[[-1,-1],[1,-1],[-1,1],[1,1]][centerStep];
      if(target)for(let i=0;i<2;i++)if(frame.axes[i*2]*target[0]>.5&&frame.axes[i*2+1]*target[1]>.5)cornersSeen[i]=true;
      const released=frame.axes.every(v=>Math.abs(v)<.4);
      if(!released)releasedSince=0;else if(!releasedSince)releasedSince=performance.now();
    }
  }
  function pads(){try{return [...(navigator.getGamepads?.()??[])].filter(p=>p?.connected);}catch{return [];}}
  function browserInput(){
    if(engineState.connected){const key='hid:'+engine.connection;if(optionsKey!==key){optionsKey=key;$picker.replaceChildren(new Option((engineState.info.name||engineState.info.model)+' · USB','hid'));}return;}
    const list=pads(),liveKeys=new Set(list.map(p=>`browser:${p.index}:${p.id}`));for(const key of sessionModels.keys())if(!liveKeys.has(key))sessionModels.delete(key);const nextKey=list.map(p=>p.index+':'+p.id).join('|');
    if(nextKey!==optionsKey){optionsKey=nextKey;$picker.replaceChildren();if(!list.length){const o=new Option(T('gp_no_pad'),'');$picker.add(o);}for(const p of list)$picker.add(new Option(`${p.index+1}. ${p.id}`,String(p.index)));if(!list.some(p=>p.index===selectedIndex))selectedIndex=list[0]?.index??null;$picker.value=String(selectedIndex??'');}
    if(engineState.connected||engineState.connecting||localBusy&&source?.kind==='hid')return;
    const p=list.find(p=>p.index===selectedIndex);
    if(!p){if(source?.kind==='gamepad'){sessionModels.delete(source.key);setSource(null);}return;}
    const standard=p.mapping==='standard'&&p.axes.length>=4;
    const key=`browser:${p.index}:${p.id}`,sourceChanged=source?.key!==key;
    const fingerprint=controllerFingerprint(p),identicalSourceCount=matchingFingerprintCount(list,fingerprint),sessionChoice=sessionModels.get(key);
    if(sessionChoice&&sessionChoice.fingerprint!==fingerprint)sessionModels.delete(key);
    const sessionModel=sessionChoice?.fingerprint===fingerprint?sessionChoice.model:null;
    const baseSource={key,kind:'gamepad',name:p.id,standard,model:p.id},canRemember=getControllerProfile(baseSource,null).canChooseModel;
    const rememberedModel=!sessionModel&&canRemember&&identicalSourceCount===1?rememberedModels.get(fingerprint):null;
    setSource({...baseSource,userModel:sessionModel??rememberedModel??undefined,modelChoiceRemembered:Boolean(!sessionModel&&rememberedModel),modelChoiceFingerprint:fingerprint,identicalSourceCount});if(sourceChanged&&!standard)message('gp_mapping');
    const axes=Array.from({length:4},(_,i)=>p.axes[i]??0),buttons=Object.fromEntries(p.buttons.map((b,i)=>[String(i),b.value]));
    const signature=JSON.stringify([axes,buttons]);const changed=p.timestamp>0?p.timestamp!==browserTimestamp:signature!==browserSignature;
    browserTimestamp=p.timestamp;browserSignature=signature;
    acceptFrame({axes,buttons,triggers:standard?[p.buttons[6]?.value??0,p.buttons[7]?.value??0]:[0,0],standard,at:performance.now(),gamepad:p});
    if(!changed)counter--; // Rest samples are browser observations; update rate counts new reports only.
  }
  s.on($picker,'change',()=>{selectedIndex=Number($picker.value);if(source?.kind==='gamepad')setSource(null);browserInput();});
  s.on($modelPicker,'change',()=>{
    if($modelPicker.disabled||!getControllerProfile(source,frame).canChooseModel)return;
    const model=$modelPicker.value;
    if(model){sessionModels.set(source.key,{fingerprint:source.modelChoiceFingerprint,model});if(source.identicalSourceCount===1)rememberedModels.set(source.modelChoiceFingerprint,model);else rememberedModels.delete(source.modelChoiceFingerprint);}
    else{sessionModels.delete(source.key);rememberedModels.delete(source.modelChoiceFingerprint);}
    browserInput();updateControls();
  });
  s.on(window,'gamepaddisconnected',event=>{if(source?.kind==='gamepad'&&selectedIndex===event.gamepad.index){sessionModels.delete(source.key);setSource(null);message('gp_error_disconnected');}});
  s.on(document,'visibilitychange',()=>{if(document.hidden&&autoJob){cancelAuto();}if(document.hidden&&measure){measure=null;q('[data-rest-progress]').hidden=true;message('gp_error_measurement');s.ctx.onReset?.();}});
  s.on(window,'beforeunload',e=>{if(engineState.busy||engineState.mode||engineState.dirty){e.preventDefault();e.returnValue='';}});
  function gate(){if(engineState.saved)return T('gp_saved');if(!engineState.connected)return T('gp_no_sony');try{engine.guard();return '';}catch(e){return T('gp_error_'+e.message);}}
  function validBefore(){return Boolean(before&&source?.key===before.key&&before.rest);}
  function validAfterRest(){return Boolean(after&&source?.key===after.key&&after.revision===engineState.revision&&after.rest);}
  function validAfter(){return validAfterRest()&&Boolean(after.circle?.results.every(r=>r.complete));}
  function updateControls(){
    lab.lockZoom(Boolean(circleActive||engineState.mode||autoJob));
    const has=fresh(frame), busy=localBusy||engineState.busy||rumbleActive||lab.active||Boolean(autoJob)||Boolean(tuning?.active), inCalib=Boolean(engineState.mode&&engineState.mode!=='fine-tune'), testing=Boolean(measure||circleActive), standard=source?.standard===true;
    const profile=getControllerProfile(source,frame),showSony=!source||profile.family==='sony';
    action('connect').hidden=!showSony||!navigator.hid||!engineUrl;
    action('connect').disabled=!engineReady||Boolean(engineState.connected||engineState.connecting||busy||testing);action('connect').textContent=T(engineState.connecting?'gp_connecting':'gp_connect');
    action('choose').disabled=action('connect').disabled;action('choose').hidden=!showSony||Boolean(engineState.connected)||!navigator.hid;
    action('disconnect').hidden=!engineState.connected;action('disconnect').disabled=Boolean(busy||inCalib);
    $picker.disabled=Boolean(engineState.connected||engineState.connecting||busy||testing);
    $modelPicker.disabled=$picker.disabled;
    for(const name of ['before','calib-before'])action(name).disabled=!has||!standard||busy||inCalib||testing||Boolean(engineState.dirty||engineState.saved);
    for(const name of ['after','calib-after'])action(name).disabled=!has||!standard||busy||inCalib||testing||!validBefore()||!engineState.dirty;
    for(const name of ['circle','calib-before-circle','calib-after-circle']){const phase=name==='calib-before-circle'?'before':name==='calib-after-circle'?'after':stage;action(name).disabled=!has||!standard||busy||inCalib||Boolean(measure)||(circleActive&&phase!==stage)||!data[phase].rest||(phase==='before'&&Boolean(engineState.dirty||engineState.saved))||(phase==='after'&&!engineState.dirty);action(name).textContent=T(circleActive&&phase===stage?'gp_circle_end':'gp_circle_start');}
    action('reset').disabled=busy||inCalib||Boolean(engineState.dirty);
    for(const side of ['left','right','both'])action('rumble-'+side).disabled=!has||busy||inCalib||testing||q(`[data-lab="vib-${side}"]`).disabled;
    const reason=gate();q('[data-calib-gate]').textContent=reason||T('gp_nv_locked');q('[data-calib-gate]').classList.toggle('gp-ready',!reason);
    for(const name of ['center','range'])action(name).disabled=Boolean(reason)||busy||inCalib||testing||!validBefore();
    const nextReady=cornersSeen.every(Boolean)&&releasedSince>0&&performance.now()-releasedSince>450;
    action('center-next').disabled=Boolean(reason)||busy||!nextReady;action('center-next').hidden=engineState.mode!=='center';
    action('range-end').hidden=engineState.mode!=='range';action('range-end').disabled=Boolean(reason)||busy||!rangeTrace?.laps.every(n=>n>=4);
    action('cancel').disabled=busy;
    const ready=guide.update({connected:Boolean(engineState.connected),connecting:Boolean(engineState.connecting),available:engineReady,unavailable:!navigator.hid?T('gp_no_hid'):null,blocked:reason,connectionNotice,saving,busy:busy||inCalib||Boolean(measure),operation:autoJob?q('[data-auto-status]').textContent:inCalib?'Завершите текущий этап ручной калибровки.':null,saved:engineState.saved,dirty:engineState.dirty,persistentSave:engineState.info?.persistentSave,before:validBefore(),rest:validAfterRest(),circleActive,coverage:data.after.circle?.results.map(r=>r.coverage)??[0,0]});
    action('flash').disabled=!ready.canSave;
    action('flash').textContent=engineState.saved?'Сохранено в геймпад':saving?'Сохранение…':'Сохранить в геймпад';
    if(saving)autoText('Сохраняем калибровку. Оставьте USB подключённым.',100);
    else if(engineState.saved)autoText('Постоянная калибровка сохранена в геймпад.',100);
    else if(!autoJob&&engineState.dirty&&reason)autoText(reason,0);
    else if(!autoJob&&engineState.dirty&&validAfter())autoText('Калибровка и проверка кругов завершены. Нажмите «Сохранить в геймпад».',100);
    q('[data-wizard]').hidden=!inCalib||Boolean(autoJob);s.root.classList.toggle('gp-calibrating',inCalib&&!autoJob);
    qa('.gp-calib-steps button').forEach(el=>{if(inCalib)el.disabled=true;});
    q('[data-sony-extra]').hidden=true;
    q('[data-stage]').textContent=showSony?T(stage==='before'?'gp_before':'gp_after'):'Проверка стиков';
    action('before').textContent=showSony?T('gp_measure_before'):'Замер покоя · 3 с';
    action('after').hidden=!showSony;
    q('[data-battery]').hidden=!showSony;
    q('.gp-flow-guide').hidden=!showSony;
    q('[data-before-status]').textContent=validBefore()?`${T('gp_before')}: ${before.rest.count} · ${T('gp_offset')} ${percent(Math.max(...before.rest.sticks.map(x=>x.offset))*100)}`:T('gp_no_measure');
    if(inCalib&&!autoJob){q('[data-wizard-title]').textContent=engineState.mode==='center'?T('gp_center_step',{step:centerStep+1}):T('gp_range_title');q('[data-wizard-instruction]').textContent=T(engineState.mode==='center'?'gp_center_'+centerStep:'gp_range_hint');q('[data-direction]').textContent=engineState.mode==='center'?['↖','↗','↙','↘'][centerStep]:'↻';q('[data-wizard-progress]').textContent=engineState.mode==='center'?T(nextReady?'gp_center_next':'gp_center_wait'):`L ${Math.min(4,rangeTrace?.laps[0]??0)}/4 · R ${Math.min(4,rangeTrace?.laps[1]??0)}/4`;}
    const battery=controllerBattery(source,engine?.state??engineState);q('[data-battery]').textContent=T('gp_battery')+': '+battery.text+(battery.charging?' · '+T('gp_charging'):'');
    for(const name of ['auto-full','auto-center'])q(`[data-lab="${name}"]`).disabled=Boolean(reason)||busy||inCalib||testing||Boolean(engineState.dirty||engineState.saved);
    q('[data-auto-hint]').textContent=reason||(autoJob?'Авторежим выполняется. Следуйте текущему шагу ниже.':inCalib?'Сначала завершите или отмените ручную калибровку.':lab.active?'Остановите тест микрофона, вибрации или другого узла.':measure?'Дождитесь окончания замера покоя.':circleActive?'Завершите текущую проверку кругов.':busy?'Дождитесь завершения текущей операции.':engineState.dirty?(validAfter()?'Круги проверены. Нажмите «Сохранить в геймпад».':'Калибровка временная. Проверка кругов включена автоматически; вращайте оба стика по краю.'):'Доступно: временная калибровка. Постоянная запись — отдельной кнопкой после проверки.');
    q('[data-lab="auto-cancel"]').hidden=!autoJob;
    q('[data-auto-progress]').hidden=!autoJob&&q('[data-auto-progress]').value!==100;
    q('[data-memory-message]').textContent=engineState.saved?T('gp_saved'):engineState.dirty?T('gp_unsaved'):'';
  }
  function startMeasure(phase){
    if(tuning?.active||!fresh(frame)||!source.standard||measure||circleActive||engineState.busy||engineState.mode||localBusy)return;
    if(phase==='after'&&(!validBefore()||!engineState.dirty))return;
    if(phase==='before'&&(engineState.dirty||engineState.saved))return;
    verificationTrace=null;resultVersion++;s.ctx.onReset?.();stage=phase;data[phase]={rest:null,circle:null};if(phase==='before')before=null;else after=null;
    measure={phase,key:source.key,revision:engineState.revision??0,start:performance.now(),last:0,samples:[]};
    q('[data-rest-progress]').hidden=false;q('[data-rest-progress]').value=0;message('gp_measuring');updateControls();
  }
  function endMeasure(){
    const m=measure;measure=null;q('[data-rest-progress]').hidden=true;
    if(!m||m.key!==source?.key||document.hidden||!fresh(frame)){message('gp_error_measurement');return;}
    const rest=restStats(m.samples);if(!rest){message('gp_error_measurement');return;}
    const sample={rest,circle:null,key:m.key,revision:m.revision};data[m.phase]=sample;
    if(m.phase==='before')before=sample;else{after=sample;if(engineState.dirty){verificationTrace=new CircleTrace();sample.circle=verificationTrace;}}
    message('gp_measured');void publish();updateComparison();updateControls();
  }
  function circle(phase=stage){
    if(circleActive){if(phase!==stage)return;const complete=circleTrace.results.every(r=>r.complete);circleActive=false;data[stage].circle=circleTrace;if(stage==='before')before=data[stage];else{after=data[stage];verificationTrace=complete?null:circleTrace;}message(complete?'gp_circle_done':'gp_circle_incomplete');void publish();updateComparison();updateControls();return;}
    if(!data[phase].rest||!fresh(frame)||measure||engineState.mode||localBusy)return;
    verificationTrace=null;lab.setZoom(1);stage=phase;circleTrace=new CircleTrace();data[phase].circle=null;circleActive=true;resultVersion++;s.ctx.onReset?.();message('gp_circle_hint');updateControls();
  }
  async function perform(fn){if(localBusy)return;localBusy=true;updateControls();try{await fn();}catch(e){if(!s.dead)reportError(e);}finally{localBusy=false;if(!s.dead)updateControls();}}
  s.on(action('connect'),'click',()=>perform(()=>engine.connect()));
  s.on(action('choose'),'click',()=>perform(()=>engine.connect({choose:true})));
  s.on(action('disconnect'),'click',()=>perform(async()=>{await engine.disconnect();message('gp_replug');}));
  for(const name of ['before','calib-before'])s.on(action(name),'click',()=>startMeasure('before'));
  for(const name of ['after','calib-after'])s.on(action(name),'click',()=>startMeasure('after'));
  s.on(action('circle'),'click',()=>circle());s.on(action('calib-before-circle'),'click',()=>circle('before'));s.on(action('calib-after-circle'),'click',()=>circle('after'));
  s.on(action('reset'),'click',()=>{resetMeasurements(false);message('gp_measure_hint');updateControls();});
  function invalidateAfter(){verificationTrace=null;data.after={rest:null,circle:null};after=null;s.ctx.onReset?.();resultVersion++;}
  s.on(action('center'),'click',()=>perform(async()=>{if(!validBefore())return;engine.guard();invalidateAfter();centerStep=0;cornersSeen=[false,false];releasedSince=0;await engine.beginCenter();setTab('calibration');q('.gp-tabs').scrollIntoView({block:'start',behavior:'smooth'});message('gp_center_0');}));
  s.on(action('center-next'),'click',()=>perform(async()=>{if(!cornersSeen.every(Boolean)||!releasedSince||performance.now()-releasedSince<450)return;if(centerStep<3){await engine.sampleCenter();centerStep++;cornersSeen=[false,false];releasedSince=0;}else{await engine.endCenter();stage='after';message('gp_temp_done');updateComparison();}}));
  s.on(action('range'),'click',()=>perform(async()=>{if(!validBefore())return;engine.guard();invalidateAfter();rangeTrace=new CircleTrace();await engine.beginRange();setTab('calibration');q('.gp-tabs').scrollIntoView({block:'start',behavior:'smooth'});message('gp_range_hint');}));
  s.on(action('range-end'),'click',()=>perform(async()=>{if(!rangeTrace?.laps.every(n=>n>=4))return;await engine.endRange();stage='after';rangeTrace=null;message('gp_temp_done');updateComparison();}));
  s.on(action('cancel'),'click',()=>perform(async()=>{await engine.disconnect();message('gp_replug');}));
  function saveCalibration(){
    if(saving||localBusy||engineState.busy||engineState.mode||engineState.saved||!engineState.dirty||engineState.info?.persistentSave!==true||measure||circleActive||autoJob||lab.active||rumbleActive||gate()||!validBefore()||!validAfter())return;
    saving=true;
    void perform(async()=>{try{
      message('gp_saving');
      // This legacy adapter token is supplied only by an explicit save-button click.
      // Connection, revision, measurements, battery and memory-lock checks still apply.
      await engine.savePermanent('SAVE',{connection:engine.connection,revision:after.revision,before:Boolean(before.rest),after:Boolean(after.rest)});
      message('gp_saved');void publish();
    }finally{saving=false;}});
  }
  s.on(action('flash'),'click',saveCalibration);
  for(const side of ['left','right','both'])s.on(action('rumble-'+side),'click',()=>q(`[data-lab="vib-${side}"]`).click());

  function autoText(text,progress){q('[data-auto-status]').textContent=text;q('[data-auto-progress]').value=progress;}
  function startAuto(full){
    if(localBusy||engineState.busy||engineState.mode||engineState.dirty||engineState.saved||measure||circleActive||lab.active||autoJob)return;
    try{engine.guard();}catch(e){reportError(e);return;}
    autoJob={id:++autoSerial,full,phase:'before',key:source.key,cancelled:false};
    setTab('calibration');startMeasure('before');
    autoText(`1 / ${full?5:3} · Отпустите стики и положите геймпад. Замер покоя — 3 секунды.`,5);
  }
  async function cancelAuto(reason=''){
    const job=autoJob;if(!job)return;job.cancelled=true;if(reason)job.failure=reason;
    autoText('Остановка. Временные настройки сбрасываются полным отключением питания геймпада.',0);
    if(engineState.busy||localBusy)return;
    autoJob=null;measure=null;circleActive=false;q('[data-rest-progress]').hidden=true;
    if(engineState.dirty||engineState.mode||job.failure){await perform(()=>engine.disconnect());message('gp_replug');}
    if(s.dead)return;
    if(job.failure){autoText(job.failure,0);$message.textContent=job.failure;}
    updateControls();
  }
  async function autoOperation(job,fn){
    localBusy=true;job.phase='working';updateControls();
    try{await fn();}catch(e){if(autoJob===job){job.cancelled=true;reportError(e);job.failure=$message.textContent+' Полностью выключите и переподключите геймпад перед повтором.';}}
    finally{localBusy=false;if(!s.dead){if(autoJob===job&&job.cancelled)void cancelAuto();updateControls();}}
  }
  function advanceAuto(now){
    const job=autoJob;if(!job)return;
    if(job.key!==source?.key){autoJob=null;return;}
    if(job.cancelled){if(!localBusy&&!engineState.busy)void cancelAuto();return;}
    if(job.phase!=='working'&&(!fresh(frame)||engineState.fault)){void cancelAuto('Поток данных прервался. Авторежим остановлен. Полностью выключите и переподключите геймпад.');return;}
    if(job.phase==='before'&&!measure){
      if(!validBefore()){autoJob=null;autoText('Замер не завершён. Проверьте подключение и повторите запуск.',0);return;}
      void autoOperation(job,async()=>{
        autoText(`2 / ${job.full?5:3} · Автоцентр. Не касайтесь стиков.`,25);invalidateAfter();
        // Motion and noise remain diagnostic measurements, not calibration blockers.
        await engine.autoCenter(()=>!job.cancelled&&Boolean(fresh(frame))&&!document.hidden,v=>autoText(`2 / ${job.full?5:3} · Автоцентр. Не касайтесь стиков.`,25+v*15));
        if(job.cancelled)return;
        if(job.full){rangeTrace=new CircleTrace();await engine.beginRange();job.phase='range';autoText('3 / 5 · Сделайте четыре медленных полных круга каждым стиком.',40);}
        else{job.phase='settle';job.settleUntil=performance.now()+1500;autoText('3 / 3 · Автоцентр готов. Отпустите стики для контрольного замера.',60);}
      });
    }else if(job.phase==='range'){
      const laps=rangeTrace?.laps??[0,0];autoText(`3 / 5 · Вращайте оба стика по краю: левый ${Math.min(4,laps[0])}/4 · правый ${Math.min(4,laps[1])}/4.`,40+Math.min(4,...laps)*5);
      if(laps.every(n=>n>=4))void autoOperation(job,async()=>{await engine.endRange();rangeTrace=null;stage='after';job.phase='settle';job.settleUntil=performance.now()+1500;autoText('4 / 5 · Полностью отпустите стики. Готовим замер после калибровки.',65);});
    }else if(job.phase==='settle'){
      autoText(`${job.full?'4 / 5':'3 / 3'} · Отпустите стики. Контрольный замер начнётся через ${Math.max(0,Math.ceil((job.settleUntil-now)/1000))} с.`,65);
      if(now>=job.settleUntil){startMeasure('after');if(measure){job.phase='after';autoText(`${job.full?'4 / 5':'3 / 3'} · Контрольный замер покоя — 3 секунды.`,75);}}
    }else if(job.phase==='after'&&!measure){
      if(!after?.rest){autoJob=null;autoText('Контрольный замер не завершён. Повторите замер после калибровки.',0);return;}
      if(!job.full){
        autoJob=null;autoText('Автоцентр готов. Теперь медленно обведите полный край обоими стиками — проверка кругов уже включена. Затем нажмите «Сохранить в геймпад».',100);updateControls();
      }else{job.phase='circle';circle('after');}
    }else if(job.phase==='circle'){
      const results=circleTrace?.results;
      autoText(`5 / 5 · Контроль круга: левый ${Math.round(results?.[0].coverage??0)}% · правый ${Math.round(results?.[1].coverage??0)}%. Медленно обведите весь край обоими стиками.`,85+Math.min(...(results??[{coverage:0}]).map(r=>r.coverage))*.14);
      if(results?.every(r=>r.complete)){circle('after');autoJob=null;autoText('Готово. Калибровка временная. Сравните результат; постоянное сохранение находится ниже.',100);updateControls();}
    }
  }

  function drawDial(canvas,i){
    const c=canvas.getContext('2d'),w=canvas.width,h=canvas.height,cx=w/2,cy=h/2,r=156,zoom=lab.zoom;
    c.clearRect(0,0,w,h);c.fillStyle='#0c192c';c.fillRect(0,0,w,h);
    for(const fraction of [.25,.5,.75,1]){c.beginPath();c.arc(cx,cy,r*fraction,0,Math.PI*2);c.strokeStyle=fraction===1?'#63788e':'#21334b';c.lineWidth=fraction===1?1.5:1;c.stroke();}
    c.strokeStyle='#3a5067';c.beginPath();c.moveTo(cx-r-20,cy);c.lineTo(cx+r+20,cy);c.moveTo(cx,cy-r-20);c.lineTo(cx,cy+r+20);c.stroke();
    c.fillStyle='rgba(56,189,248,.10)';c.beginPath();c.arc(cx,cy,Math.min(r,Math.max(3,r*s.ctx.thresholds.center_offset_warn*zoom)),0,Math.PI*2);c.fill();
    c.save();c.beginPath();c.rect(cx-r-5,cy-r-5,2*r+10,2*r+10);c.clip();
    const traces=[[data.before.circle,'#f7b955'],[data.after.circle,'#44dfc3']];
    if(circleActive)traces.push([circleTrace,stage==='before'?'#f7b955':'#44dfc3']);if(rangeTrace)traces.push([rangeTrace,'#44dfc3']);
    for(const [trace,color] of traces){if(!trace)continue;c.strokeStyle=color;c.lineWidth=3;const bins=trace.bins[i];for(let k=0;k<72;k++){if(!bins[k])continue;const angle=(k+.5)/72*Math.PI*2-Math.PI;c.beginPath();c.arc(cx,cy,r*bins[k]*zoom,angle-.04,angle+.04);c.stroke();}}
    if(fresh(frame)){
      const x=frame.axes[i*2],y=frame.axes[i*2+1];trails[i].push([x,y]);if(trails[i].length>100)trails[i].shift();
      c.strokeStyle='#4598d97d';c.lineWidth=1.5;c.beginPath();trails[i].forEach(([tx,ty],j)=>{const px=cx+tx*r*zoom,py=cy+ty*r*zoom;j?c.lineTo(px,py):c.moveTo(px,py);});c.stroke();
      c.strokeStyle='#6ebcf0';c.beginPath();c.moveTo(cx,cy);c.lineTo(cx+x*r*zoom,cy+y*r*zoom);c.stroke();c.fillStyle='#76e6d1';c.shadowColor='#44dfc3';c.shadowBlur=10;c.beginPath();c.arc(cx+x*r*zoom,cy+y*r*zoom,5,0,Math.PI*2);c.fill();c.shadowBlur=0;
    }
    c.restore();
    c.fillStyle='#8b9fb5';c.font='13px system-ui';c.textAlign='center';const limit=zoom===10?'0.1':'1';
    c.fillText('−'+limit,cx-r-28,cy-9);c.fillText('+'+limit,cx+r+28,cy-9);c.fillText('−'+limit,cx+18,cy-r-9);c.fillText('+'+limit,cx+18,cy+r+20);
    if(zoom===10){c.fillStyle='#b4cada';c.fillText('10× · центр ±10%',cx,24);if(fresh(frame)&&frame.axes.slice(i*2,i*2+2).some(v=>Math.abs(v)>.1)){c.fillStyle='#f7b955';c.fillText('Стик за пределами увеличенной области',cx,h-10);}}

  }
  function updateLive(){
    const has=fresh(frame);axisEls.forEach((el,i)=>el.textContent=has?signed(frame.axes[i]):'—');
    const stat=data[stage].rest,trace=rangeTrace??(circleActive?circleTrace:data[stage].circle);
    for(let i=0;i<2;i++){
      q(`[data-live-radius="${i}"]`).textContent=has?percent(Math.hypot(frame.axes[i*2],frame.axes[i*2+1])*100):'—';
      q(`[data-offset="${i}"]`).textContent=stat?percent(stat.sticks[i].offset*100):'—';q(`[data-noise="${i}"]`).textContent=stat?percent(stat.sticks[i].noise*100):'—';
      const circleResult=trace?.results[i];q(`[data-circle="${i}"]`).textContent=circleResult?.error!=null?percent(circleResult.error):'—';q(`[data-coverage="${i}"]`).value=circleResult?.coverage??0;q(`[data-coverage-value="${i}"]`).textContent=Math.round(circleResult?.coverage??0)+'%';
      triggerEls[i].value=has?frame.triggers[i]:0;triggerValues[i].textContent=has&&source.standard?Math.round(frame.triggers[i]*100)+'%':'—';
    }
    const keys=has?Object.keys(frame.buttons):[];const key=keys.join('|')+source?.kind+getControllerProfile(source,frame).id;
    if(key!==buttonsKey){buttonsKey=key;buttonEls=new Map();q('[data-buttons]').replaceChildren();for(const k of keys){const el=document.createElement('span');el.textContent=frameButtonLabel(k);el.title=el.textContent;buttonEls.set(k,el);q('[data-buttons]').append(el);}}
    for(const [k,el] of buttonEls){el.classList.toggle('gp-pressed',has&&frame.buttons[k]>.5);el.classList.toggle('gp-seen',seen.has(k));el.setAttribute('aria-label',`${el.title}: ${has&&frame.buttons[k]>.5?'нажата':seen.has(k)?'уже нажималась':'ещё не проверена'}`);}
    q('[data-buttons-count]').textContent=T('gp_tested')+`: ${seen.size} / ${keys.length}`;
    q('[data-rate]').textContent=T('gp_rate')+`: ${has?rate+' Гц':'—'}`;
    if(has&&source?.kind==='hid'&&q('[data-sony-extra]').open){
      const canvas=q('[data-touch]'),c=canvas.getContext('2d');c.fillStyle='#0c192c';c.fillRect(0,0,420,220);for(const touch of frame.touch??[]){if(!touch.active)continue;c.fillStyle='#44dfc3';c.beginPath();c.arc(touch.x/1920*420,touch.y/(source.model==='DS4'?943:1080)*220,9,0,Math.PI*2);c.fill();}
      q('[data-gyro]').textContent=frame.imu?Object.entries(frame.imu.gyro).map(([k,v])=>k.toUpperCase()+': '+v.toFixed(1)).join(' · '):'—';q('[data-accel]').textContent=frame.imu?Object.entries(frame.imu.accel).map(([k,v])=>k.toUpperCase()+': '+v.toFixed(2)).join(' · '):'—';
    }
    lab.update();if(lab.supportsTab?.(chosenTab)===false)setTab('test');updateControls();
  }
  function comparisonRows(){if(tuning?.report){const r=tuning.report;return [0,1].flatMap(i=>[['rms','Отклонение круга (RMS)'],['worst','Самый неровный участок'],['returnWorst','Худший возврат в центр'],['repeat','Повторяемость']].map(([key,label])=>[(i?'Правый':'Левый')+' стик · '+label,percent(r.before.sticks[i][key]*100),percent(r.after.sticks[i][key]*100)]));}const rows=[];for(let i=0;i<2;i++){const label=T(i?'gp_right_stick':'gp_left_stick');for(const [key,text] of [['offset','gp_offset'],['noise','gp_noise'],['peak','gp_peak']])rows.push([label+' · '+T(text),...['before','after'].map(phase=>data[phase].rest?percent(data[phase].rest.sticks[i][key]*100):T('gp_no_measure'))]);rows.push([label+' · '+T('gp_circle_error')+' (RMS)',...['before','after'].map(phase=>{const n=data[phase].circle?.results[i]?.error;return n!=null?percent(n):T('gp_no_measure');})]);}return rows;}
  function updateComparison(){const ordinary=source&&getControllerProfile(source,frame).family!=='sony';q('.gp-compare').classList.toggle('gp-measurement-only',Boolean(ordinary));q('.gp-compare thead th:nth-child(2)').lastChild.textContent=ordinary?'Замер':T('gp_before');q('[data-comparison-hint]').textContent=tuning?.report?'Сравнение исходного профиля этого геймпада с последним проверенным USB-замером. Точка возврата сохраняется между подключениями.':ordinary?'Результаты текущей проверки. Замеры относятся к выбранному геймпаду.':T('gp_comparison_hint');q('[data-compare]').innerHTML=comparisonRows().map(row=>`<tr>${row.map((value,i)=>`<${i?'td':'th'}>${esc(value)}</${i?'td':'th'}>`).join('')}</tr>`).join('');}
  async function publish(){
    const ordinary=source&&getControllerProfile(source,frame).family!=='sony';
    const version=++resultVersion,key=source?.key,tuningReport=tuning?.report;if(!key||(!data[stage].rest&&!lab.hasEvidence&&!tuningReport))return;
    const current=data[stage],v=current.rest?verdict(current.rest,current.circle,s.ctx.thresholds):{status:'info',key:'gp_partial'};v.status=precisionResultStatus(v.status,lab.status,tuningReport?.metrics?.precision_result_phase);
    const metrics={...lab.metrics(),...tuning?.report?.metrics,...flatten(data.before.rest,data.before.circle,'before_'),...flatten(data.after.rest,data.after.circle,'after_'),trigger_left_min_pct:round(triggerMin[0]*100),trigger_left_max_pct:round(triggerMax[0]*100),trigger_right_min_pct:round(triggerMin[1]*100),trigger_right_max_pct:round(triggerMax[1]*100),buttons_checked:[...seen].map(k=>frameButtonLabel(k)).join(', '),buttons_seen:seen.size,buttons_total:Object.keys(frame?.buttons??{}).length,permanent_saved:Boolean(engineState.saved),measurement_stage:tuning?.report?'precision':stage,calibration_revision:engineState.revision??0};
    if(getControllerProfile(source,frame).family!=='sony'){delete metrics.permanent_saved;delete metrics.calibration_revision;}
    const snapshot=document.createElement('canvas');snapshot.width=1120;snapshot.height=870;const c=snapshot.getContext('2d');c.fillStyle='#f4f7fb';c.fillRect(0,0,1120,870);c.fillStyle='#172b43';c.font='bold 26px system-ui';c.fillText(T('gp_title'),28,42);c.font='15px system-ui';c.fillText((source.name??'').slice(0,110),28,71);c.fillText(new Date().toLocaleString('ru-BY')+' · '+(tuning?.report?'Точная доводка':ordinary?'Проверка стиков':T(stage==='before'?'gp_before':'gp_after')),28,98);const reportDials=tuning?.report?qa('[data-fine-chart]'):dials;c.drawImage(reportDials[0],28,120,520,520*reportDials[0].height/reportDials[0].width);c.drawImage(reportDials[1],572,120,520,520*reportDials[1].height/reportDials[1].width);c.fillStyle='#172b43';c.font='bold 16px system-ui';c.fillText(T('gp_parameter'),28,555);c.fillText(ordinary?'Замер':T('gp_before'),685,555);if(!ordinary)c.fillText(T('gp_after'),890,555);c.font='14px system-ui';comparisonRows().forEach((row,i)=>{c.fillText(row[0],28,589+i*28);c.fillText(row[1],685,589+i*28);if(!ordinary)c.fillText(row[2],890,589+i*28);});c.font='12px system-ui';c.fillText(T('gp_tested')+': '+seen.size+(getControllerProfile(source,frame).family==='sony'?' · '+T('gp_saved_metric')+': '+(engineState.saved?'✓':'—'):''),28,842);
    const blob=await png(snapshot);if(s.dead||key!==source?.key||version!==resultVersion)return;
    const fields=engineState.info?.fields??{};
    s.ctx.onResult?.({status:v.status,summary:tuning?.report?.summary??(lab.status==='fail'?'Вы отметили неисправность; подробности в протоколе':current.rest?T(v.key):'Частичная проверка геймпада: отмечено узлов '+lab.checks),metrics,displayMetrics:{[T('gp_stage')]:tuning?.report?'Точная доводка':getControllerProfile(source,frame).family!=='sony'?'Проверка стиков':T(stage==='before'?'gp_before':'gp_after'),[T('gp_offset')]:current.rest?percent(Math.max(...current.rest.sticks.map(x=>x.offset))*100):T('gp_no_measure'),[T('gp_noise')]:current.rest?percent(Math.max(...current.rest.sticks.map(x=>x.noise))*100):T('gp_no_measure'),[T('gp_coverage')]:current.circle?current.circle.results.map(r=>Math.round(r.coverage)+'%').join(' / '):T('gp_no_measure'),[T('gp_tested')]:`${seen.size} / ${metrics.buttons_total}`,'Узлов отмечено':lab.checks},snapshot:blob,device:{model:source.name,transport:source.kind==='hid'?'USB / WebHID':'Gamepad API',firmware:fields['FW Update']??fields['SW Version']??'',board:fields['Board Model']??''}});
  }
  updateComparison();updateControls();
  s.loop(()=>{
    const now=performance.now();tuning?.tick(now);if(document.hidden)return;browserInput();lab.paint();advanceAuto(now);
    if(!autoJob&&circleActive&&circleTrace.results.every(r=>r.complete))circle(stage);
    if(verificationTrace?.results.every(r=>r.complete)){verificationTrace=null;message('gp_circle_done');void publish();updateComparison();updateControls();}
    if(measure){q('[data-rest-progress]').value=Math.min(3,(now-measure.start)/1000);if(now-measure.start>=3000)endMeasure();}
    if(now-rateAt>=1000){rate=Math.round(counter*1000/(now-rateAt));counter=0;rateAt=now;}
    if(now-lastDraw>=30){dials.forEach(drawDial);lastDraw=now;}
    if(now-lastUi>=100){updateLive();lastUi=now;}
    if(reportDirty&&now-lastReport>700&&(data[stage].rest||lab.hasEvidence||tuning?.report)&&!measure&&!circleActive&&(!engineState.mode||Boolean(tuning?.report))&&!engineState.busy&&!localBusy&&!autoJob){reportDirty=false;lastReport=now;updateComparison();void publish();}
  });
  s.clean(()=>teardownGamepadSession({
    cancelAuto:()=>{if(autoJob)autoJob.cancelled=true;autoJob=null;autoSerial++;},
    tuning,
    lab,
    actuator:frame?.gamepad?.vibrationActuator,
    engine
  }));
});
