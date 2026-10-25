import {CalibrationRunner} from './calibration-runner.js';
import {RETURN_ANGLE, sameParameters} from './calibration-core.js';
import {calibrationErrorMessages} from './calibration-errors.js';
// Keep existing backup imports compatible; the old calibration UI is retired.
export {loadTuningBackup, persistTuningBackup, openTuningSession} from './calibration-backup-v1.js';

const pct = value => Number.isFinite(value) ? (value * 100).toFixed(2) + '%' : '—';
const build = '2026.10.20.2';
const startMessages = {
  insecure_context: 'Калибровке нужен защищённый адрес HTTPS. Откройте эту страницу через https://.',
  hid_unavailable: 'Этот браузер не предоставляет доступ к калибровке по USB. Откройте страницу в Chrome или Edge на компьютере.',
  hid_policy_blocked: 'Доступ к USB запрещён настройками этой страницы или браузера. Откройте тестер напрямую в отдельной вкладке Chrome или Edge.',
  engine_loading: 'Загружаем модуль калибровки. Кнопка станет доступна после загрузки.',
  engine_load_failed: 'Модуль калибровки не загрузился. Нажмите «Повторить загрузку» ниже; после загрузки запустите калибровку.',
  engine_unavailable: 'Не задан модуль калибровки для этой страницы. Скопируйте проверку запуска ниже.',
  connecting: 'Идёт подключение по USB. Если открыто окно выбора, выберите DualSense и нажмите «Подключить».',
  operation_busy: 'Дождитесь завершения текущей USB-операции.',
  calibration_active: 'Уже выполняется калибровка. Сначала завершите или остановите текущий мастер.',
  test_active: 'Сейчас работает тест звука, микрофона или эффектов. Остановите его кнопкой «Стоп», затем запустите калибровку.'
};
const usbStages = {
  choosing: 'Выберите DualSense в окне браузера и нажмите «Подключить». Если окно уже открыто, оно может быть за основной вкладкой.',
  opening: 'Устройство выбрано. Открываем USB-доступ в системе — до 8 секунд.',
  input: 'USB открыт. Ждём данные от геймпада — до 5 секунд.',
  information: 'Данные поступают. Читаем модель и параметры геймпада.',
  lease: 'Проверяем, не занят ли геймпад другой вкладкой.'
};
export function calibrationStartStatus({secure = true, hid = true, allowed = true, loaded = true, load = 'ready', connecting = false, reason = null} = {}) {
  const code = !secure ? 'insecure_context' : !hid ? 'hid_unavailable' : !allowed ? 'hid_policy_blocked'
    : !loaded ? load === 'failed' ? 'engine_load_failed' : load === 'unavailable' ? 'engine_unavailable' : 'engine_loading'
    : connecting ? 'connecting' : reason;
  return {code:code??'ready', blocked:Boolean(code), message:startMessages[code]??'', retry:code==='engine_load_failed'};
}
const messages = {
  temporary: 'Есть временный проверенный вариант из прошлого сеанса. Начните новый замер, чтобы проверить текущие настройки и сохранить их.',
  idle: 'Подключите DualSense кабелем USB. Следуйте подсказкам: программа сама измерит стики и подберёт поправку.',
  connecting: 'Подключаем геймпад по USB. Если открыто окно браузера, выберите DualSense и нажмите «Подключить».',
  preparing: 'Читаем исходные параметры и готовим резервную копию. Оставьте USB подключённым.',
  ready: 'Новый замер подтвердил улучшение. Нажмите «Сохранить в геймпад», чтобы оставить его после выключения.',
  saved: 'Сохранено в геймпад. Полностью выключите его, затем подключите по USB и выполните контрольную проверку.',
  verified: 'Параметры совпали после подключения, полное выключение отмечено пользователем. Контрольный замер пройден.',
  restored: 'Настройки до первой доводки восстановлены временно и проверены. Можно сохранить их в геймпад.',
  writing: 'Применяем временные параметры и читаем их обратно. Оставьте USB подключённым.',
  saving: 'Записываем результат в память геймпада. Оставьте USB подключённым.',
  stopped: 'Калибровка остановлена. Можно начать новый замер.',
  paused: 'USB отключён. Подключите геймпад снова: резервная копия сохранена в этом браузере.',
  recovery: 'Предыдущая проверка прервалась. Верните последний проверенный вариант, затем начните заново.',
  'save-uncertain': 'Запись могла завершиться, но подтверждение потеряно. Полностью выключите геймпад, подключите снова и проверьте результат.',
  'control-failed': 'Сохранённые параметры прочитаны без расхождений, но физический контрольный замер не пройден.',
  error: 'Операция прервана. Переподключите геймпад, чтобы продолжить.',
  unchanged: 'Подтверждённого улучшения нет. Оставлен предыдущий проверенный вариант.'
};
const reasons = {
  not_significant: 'Разница оказалась меньше разброса между контрольными кругами. Предыдущий вариант возвращён.',
  at_optimum: 'По этому замеру более точная поправка не найдена. Сохранён предыдущий вариант.',
  worse_circle: 'Поправка ухудшила окружность одного из стиков. Предыдущий вариант возвращён.',
  worse_return: 'Поправка ухудшила возврат в центр. Предыдущий вариант возвращён.',
  lost_travel: 'Поправка уменьшила полный ход. Предыдущий вариант возвращён.',
  travel_inconsistent: 'Полный ход достигнут, но между кругами есть разброс.',
  repeatability: 'Контрольные круги слишком различаются. Предыдущий вариант возвращён. Повторите замер с одинаковым нажимом на внешний упор.',
  still_clipped: 'Даже расширенный диапазон не показал весь ход стика. Предыдущие параметры возвращены; достоверно подобрать поправку пока нельзя.',
  probe_bounds: 'Для измерения полного хода потребовалось бы слишком далеко отойти от исходных настроек. Параметры оставлены прежними.',
  bounds: 'Расчёт выходит за допустимый диапазон изменения. Предыдущие параметры возвращены.',
  missing_edge: 'Не удалось измерить все четыре края. Предыдущие параметры возвращены. Повторите полные круги по упору.',
  disconnected: messages.paused, save_unknown: messages['save-uncertain'],
  reconnect_first: 'Сначала отключите USB и полностью выключите геймпад. Затем подключите его и нажмите «Проверить сохранение».',
  power_cycle_confirmation_required: 'Подтвердите, что геймпад был полностью выключен, а не только отключён и снова подключён по USB.',
  saved_parameters_differ: 'Прочитанные параметры отличаются от сохранённых. Нажмите «Начать калибровку» для нового замера.',
  saved_storage_failed: 'Геймпад подтвердил запись, но браузер не сохранил подтверждение. После выключения проверьте сохранение ещё раз.',
  tuning_external_change: 'Настройки изменились в другой программе или вкладке. Закройте её и переподключите геймпад.',
  controller_in_another_tab: 'Геймпад уже открыт в другой вкладке CRM. Отключите его там и повторите подключение здесь.',
  tuning_rolled_back: 'Проверка записи не прошла. Предыдущие параметры восстановлены; можно повторить после подключения.',
  tuning_readback_failed: 'Запись не подтвердилась. Переподключите геймпад и восстановите проверенный вариант.',
  tuning_read_failed: 'Геймпад не вернул все параметры. Переподключите его по USB.',
  tuning_backup_mismatch: 'Настройки вышли за границы сохранённой точки возврата. Запись остановлена. Скачайте протокол для проверки.',
  backup_invalid: 'Резервная копия повреждена. Запись остановлена; исходные данные оставлены в браузере.',
  storage_failed: 'Браузер не смог сохранить резервную копию. Разрешите хранилище для сайта и освободите место.',
  battery_low: 'Для калибровки нужен заряд от 30% или зарядка по USB.',
  battery_unknown: 'Нет свежих данных о заряде. Проверьте USB-кабель.',
  memory_unlocked: 'Полностью выключите геймпад и подключите снова, чтобы включить временную калибровку.',
  reconnect_required: 'Переподключите геймпад: обмен данными был прерван.',
  usb_required: 'Для калибровки подключите геймпад кабелем USB с передачей данных.',
  no_input: 'Геймпад не передаёт данные. Проверьте USB-кабель и закройте другие программы калибровки.',
  tuning_unavailable: 'Этот мастер поддерживает обычный DualSense по USB. Для DS4 и Edge доступны прежние инструменты калибровки.',
  engine_unavailable: 'Загружаем инструмент. Подождите несколько секунд.',
  temporary_checked: 'Проверенный вариант действует временно. Для постоянного сохранения начните новый контрольный замер.',
  recovered: 'Последний проверенный вариант восстановлен. Можно начать новую калибровку.',
  cancelled: 'Калибровка остановлена. Незавершённая поправка отменена.',
  invalid_measurement: 'Замер неполный. Запись остановлена. Повторите его после восстановления предыдущего варианта.'
};
const labels = {connecting:'Подключение USB…',preparing:'Подготовка калибровки…',temporary:'Временный результат',idle:'Готов к работе',baseline:'Замер до',probe:'Измерение полного хода',verifying:'Проверка поправки',ready:'Улучшение подтверждено',saved:'Сохранено в геймпад',verified:'Контроль пройден',restored:'Исходные настройки',writing:'Применяем поправку',saving:'Сохраняем',stopped:'Остановлено',paused:'USB отключён',recovery:'Нужен возврат',error:'Нужно внимание',unchanged:'Без подтверждённого улучшения',control:'Контрольный замер','restore-check':'Проверка исходных настроек','save-uncertain':'Проверить сохранение','control-failed':'Контроль не пройден'};
const controlIssues = {
  lost_travel: 'уменьшился полный ход',
  repeatability: 'контрольные круги получились слишком разными',
  worse_return: 'увеличилось отклонение после отпускания стика',
  worse_circle: 'увеличилось отклонение окружности'
};
const directionNames = ['вправо', 'вниз', 'влево', 'вверх'];
export const travelMetricLabel = (before, after) => before?.protocol === 'independent-sticks-v1' && after?.protocol === 'independent-sticks-v1' ? 'Ход в худшем круге' : 'Минимальный полный ход';
export const precisionResultStatus = (status, labStatus, precisionPhase) => {
  if (labStatus === 'fail' || precisionPhase === 'control-failed') return 'fail';
  return status === 'pass' && labStatus !== 'pass' ? 'info' : status;
};
const travelEvidenceRows = verdict => (verdict?.travelEvidence ?? []).map(item => {
  const passes = 'по часовой: ' + item.passes.slice(0,2).map(pass => pct(pass.value)).join(' / ') + '; против часовой: ' + item.passes.slice(2).map(pass => pct(pass.value)).join(' / ');
  return (item.stick ? 'Правый' : 'Левый') + ' стик · ' + directionNames[item.direction] + ': ' + passes + ', удержание ' + pct(item.hold)
    + '; порог ' + pct(item.threshold) + ', достигнутый ход ' + pct(item.reached) + ', худший круг ' + pct(item.worstCircle) + '.';
});

export function calibrationPresentation(r) {
  const controlResult = Boolean(r.record?.verification && r.verdict && ['verified','control-failed'].includes(r.phase));
  const controlView = r.phase === 'control' || controlResult;
  const archived = !r.snapshot && !controlResult;
  const historicalControl = !r.snapshot && controlResult;
  const improvements = r.verdict?.improvements ?? [];
  const controlFailure = r.phase === 'control-failed' && controlResult;
  const inconsistentTravel = controlFailure && r.reason === 'travel_inconsistent';
  const controlIssue = controlIssues[r.reason] ?? 'результат отличается от замера при сохранении';
  return {
    state: archived && r.phase === 'saved' ? 'Сохранённый протокол' : labels[r.phase] ?? 'Подготовка',
    instruction: inconsistentTravel ? reasons.travel_inconsistent : controlFailure ? messages['control-failed'] + ' Причина: ' + controlIssue + '.' : !r.snapshot && r.phase === 'verified' ? 'В этом браузере сохранён успешный контрольный замер. Для проверки текущего состояния нажмите «Проверить сохранение».' : (r.phase === 'error' ? calibrationErrorMessages[r.reason] : null) ?? reasons[r.reason] ?? messages[r.phase] ?? messages.error,
    legendBefore: controlView ? '● При сохранении' : '● До',
    legendAfter: controlView ? '● Контрольный замер' : archived ? '● Сохранённый замер' : '● Проверенный результат',
    outcome: inconsistentTravel ? (historicalControl ? 'Показан сохранённый контрольный замер; текущее состояние ещё не измерено. ' : '') + 'По этому замеру нельзя отделить особенности движения от механики. Сохранённые параметры оставлены. Повторный запуск необязателен.' : controlFailure ? (historicalControl ? 'Показан сохранённый контрольный замер; текущее состояние ещё не измерено. ' : '') + 'Во время контроля настройки геймпада не изменялись. Повторите только контрольный замер; заново проходить калибровку пока не нужно.' : r.phase === 'verified' ? historicalControl ? 'Показан сохранённый успешный контрольный замер. Текущее состояние ещё не измерено.' : messages.verified : archived ? 'Показан сохранённый протокол. Текущее состояние ещё не измерено.' : r.phase === 'unchanged' ? 'На графике оставленный вариант. Отклонённая попытка сохранена в протоколе.' : improvements.length ? improvements.map(v => (v.stick ? 'Правый' : 'Левый') + ' стик: ' + (v.kind === 'circle' ? 'отклонение круга' : 'отклонение после отпускания') + ' уменьшилось на ' + (v.gain * 100).toFixed(2) + ' п. п.').join(' · ') : 'Данные до и после. Меньшее отклонение лучше; полный ход должен сохраняться.',
    evidenceRows: travelEvidenceRows(r.verdict)
  };
}

export function createCircleTuning(s, api) {
  const panel = s.q('#gp-panel-calibration'), workbench = s.q('.gp-workbench');
  const card = document.createElement('section'); card.className = 'gp-fine-card gp-calibration-v2';
  card.setAttribute('aria-label', 'Пошаговая калибровка DualSense');
  card.innerHTML = `<header><div><span class="gp-kicker">DUALSENSE · USB</span><h3>Калибровка стиков</h3></div><span class="gp-fine-badge" data-fine-state></span></header>
    <ol class="gp-v2-steps" aria-label="Этапы калибровки">${['Замер до','Подбор поправки','Проверка','Сохранение'].map((title,i)=>`<li data-v2-step="${i}"><b>${i+1}</b><span>${title}</span></li>`).join('')}</ol>
    <div class="gp-v2-guide"><div class="gp-v2-direction" data-fine-direction aria-hidden="true">⌁</div><div><p class="gp-fine-instruction" data-fine-instruction role="status" aria-live="polite"></p><p class="gp-v2-detail" data-fine-detail></p></div></div>
    <progress data-fine-progress max="1" value="0" aria-label="Текущий замер" hidden></progress>
    <div class="gp-actions gp-v2-actions"><button type="button" class="gp-primary" data-fine="start" aria-describedby="gp-start-status">Подключить и начать</button><button type="button" data-fine="retry-engine" hidden>Повторить загрузку</button><button type="button" class="gp-primary" data-fine="save" hidden>Сохранить в геймпад</button><button type="button" class="gp-primary" data-fine="recover" hidden>Вернуть проверенный вариант</button><button type="button" class="gp-primary" data-fine="verify" hidden>Проверить сохранение</button><button type="button" data-fine="stop" hidden>Остановить</button></div>
    <p id="gp-start-status" class="gp-small" data-fine-start-status role="status" aria-live="polite"></p>
    <details class="gp-v2-details" data-fine-start-check><summary>Проверка запуска · ${build}</summary><p class="gp-small">Показывает доступ к USB и состояние кнопки. Настройки геймпада не меняет.</p><button type="button" data-fine="diagnose">Показать проверку запуска</button><pre data-fine-start-report hidden style="white-space:pre-wrap;overflow-wrap:anywhere" tabindex="0"></pre><button type="button" data-fine="copy-start" hidden>Скопировать проверку</button><p class="gp-small" data-fine-copy-start role="status"></p></details>
    <label class="gp-small" data-fine-power-cycle hidden><input type="checkbox" data-fine-power-cycle-confirm> Я полностью выключил геймпад, затем включил и подключил его по USB</label>
    <p class="gp-v2-device-proof" data-fine-device-proof hidden></p>
    <div class="gp-v2-intro" data-fine-intro><span>① Резервная копия автоматически</span><span>② Круги и возврат в центр</span><span>③ Сохранение одной кнопкой</span></div>
    <div class="gp-fine-results" data-fine-results hidden>${[0,1].map(i=>`<section data-fine-lane="${i}"><header><h4>${i?'Правый':'Левый'} стик</h4><span data-fine-counter="${i}"></span></header><div class="gp-v2-lane-guide" data-lane-guide="${i}" hidden><strong data-lane-instruction="${i}"></strong><p data-lane-detail="${i}"></p><progress data-lane-progress="${i}" max="1" value="0" aria-label="${i?'Правый':'Левый'} стик: текущее действие"></progress></div><canvas width="560" height="420" data-fine-chart="${i}" aria-label="${i?'Правый':'Левый'} стик: измеренные USB-данные"></canvas><dl data-fine-metrics="${i}" hidden>${[['rms','Отклонение круга'],['returnWorst','Худший возврат в центр'],['travel','Минимальный полный ход']].map(([key,title])=>`<dt${key==='travel'?' data-fine-travel-title="'+i+'"':''}>${title}</dt><dd data-fine-${key}="${i}">—</dd>`).join('')}</dl></section>`).join('')}</div>
    <p class="gp-small gp-v2-legend" data-fine-legend hidden><span>● До</span> <span>● Проверенный результат</span> · реальные USB-данные</p>
    <p class="gp-v2-outcome" data-fine-outcome hidden></p>
    <section class="gp-v2-outcome" data-fine-travel-evidence hidden aria-label="Детали полного хода"><strong>Детали полного хода</strong><div data-fine-travel-evidence-list></div></section>
    <details class="gp-v2-details"><summary>Подробности и возврат настроек</summary><p>У каждого стика отдельные подсказки: два круга по часовой, два против часовой и восемь коротких отклонений с отпусканием. Завершённые действия сохраняются, пока вы проходите второй стик. Поправка должна улучшить результат без потери полного хода. Износ или люфт стика могут ограничивать точность.</p><p>Калибровка меняет параметры в геймпаде. Графики показывают USB-данные без программного выравнивания окружности.</p><div data-fine-quality></div><div class="gp-actions"><button type="button" data-fine="export" hidden>Скачать протокол</button><button type="button" data-fine="view" hidden>Открыть протокол</button><button type="button" data-fine="copy" hidden>Скопировать протокол</button><button type="button" data-fine="restore" hidden>Вернуть настройки до первой доводки</button></div><pre data-fine-protocol hidden aria-label="Технический протокол калибровки"></pre><p class="gp-small">Точка возврата привязана к этому геймпаду и хранится в браузере. Скачайте протокол, чтобы сохранить отдельную копию.</p></details>`;
  panel.prepend(card);
  const q = selector => card.querySelector(selector), button = key => q('[data-fine="' + key + '"]');
  let runner, lastFrame = null, lastUi = 0, observed = null, disposed = false, disposePromise = null, wasHidden = false, copyState = ''; 
  const text = (selector, value) => { const el = q(selector); if (el.textContent !== value) el.textContent = value; };
  runner = new CalibrationRunner({engine: api.engine, storage: () => window.localStorage, onChange: () => { if (!disposed) {render(); api.changed();} }});
  function supported() { return !api.state().connected || api.state().info?.model === 'DS5'; }
  function startStatus() {
    const policy=document.permissionsPolicy??document.featurePolicy, startup=api.startup?.();
    return calibrationStartStatus({secure:window.isSecureContext!==false,hid:Boolean(navigator.hid),
      allowed:!policy?.allowsFeature||policy.allowsFeature('hid'),loaded:Boolean(api.engine()),load:startup?.load,
      connecting:api.state().connecting,reason:startup?.reason??(api.state().mode?'calibration_active':!startup&&api.busy()?'operation_busy':null)});
  }
  function startupReport() {
    const st=api.state(),status=startStatus(),startup=api.startup?.(),r=runner;
    let storage=true;try{void window.localStorage.length;}catch{storage=false;}
    return JSON.stringify({build,browser:navigator.userAgent,secure:window.isSecureContext,hid:Boolean(navigator.hid),
      module:startup?.load??(api.engine()?'ready':'missing'),start:status.code,
      button:{disabled:button('start').disabled,hidden:button('start').hidden},
      source:startup?.source??'unknown',connected:Boolean(st.connected),connecting:Boolean(st.connecting),usbStage:st.connectStage??null,
      busy:Boolean(st.busy),mode:st.mode??null,fault:Boolean(st.fault),model:st.info?.model??null,storage,
      wizard:{phase:r.phase,reason:r.reason,busy:r.busy,active:r.active},passiveTest:startup?.measurement??null},null,2);
  }
  function render() {
    const st = api.state(), r = runner, capture = r.capture, start=startStatus();
    const presentation = calibrationPresentation(r);
    const modern = supported(); card.hidden = !modern;
    panel.classList.toggle('gp-modern-calibration', modern);
    workbench.classList.toggle('gp-modern-calibration', modern);
    panel.classList.toggle('gp-tuning-active', r.active || r.busy);
    workbench.classList.toggle('gp-tuning-active', r.active || r.busy);
    text('[data-fine-state]', presentation.state);
    const stale = capture && (!lastFrame || performance.now() - lastFrame.at > 1500);
    const instruction = !navigator.hid ? 'Для калибровки откройте эту страницу в Chrome или Edge на компьютере и подключите геймпад по USB.'
      : stale ? 'Нет свежих USB-данных. Проверьте кабель; незавершённый участок будет измерен заново.'
      : capture ? capture.instruction : presentation.instruction;
    text('[data-fine-instruction]', instruction);
    text('[data-fine-detail]', capture ? capture.detail : r.phase === 'error' ? 'Код: ' + r.reason : r.phase === 'connecting' ? 'Настройки пока не меняются. Окно выбора устройства может находиться поверх браузера.' : r.phase === 'preparing' ? 'Настройки пока не меняются. После чтения начнётся замер стиков.' : r.phase === 'idle' ? 'Обычно 2–4 минуты. Можно двигать стики по очереди. В начале браузер может попросить разрешение.' : '');
    if(r.phase==='connecting'&&usbStages[st.connectStage])text('[data-fine-detail]',usbStages[st.connectStage]);
    text('[data-fine-direction]', capture ? capture.stage === 'rest' ? '◎' : '⇄' : ['ready','saved','verified'].includes(r.phase) ? '✓' : '⌁');
    card.setAttribute('aria-busy', String(r.busy));
    card.dataset.phase = r.phase; card.dataset.fineCapturing = String(Boolean(capture)); card.dataset.fineAction = capture?.stage ?? ''; 
    const step = r.phase === 'baseline' ? 0 : ['probe','writing'].includes(r.phase) ? 1 : ['verifying','control','restore-check'].includes(r.phase) ? 2 : ['ready','restored','saving','saved','verified'].includes(r.phase) ? 3 : -1;
    for (const el of card.querySelectorAll('[data-v2-step]')) {
      const index = Number(el.dataset.v2Step); el.classList.toggle('is-current', index === step); el.classList.toggle('is-done', index < step || ['saved','verified'].includes(r.phase));
      if (index === step) el.setAttribute('aria-current','step'); else el.removeAttribute('aria-current');
    }
    q('[data-fine-progress]').hidden = !capture; q('[data-fine-progress]').value = capture?.progress ?? 0;
    const savingUnknown = Boolean(r.record?.saveIntent), recovery = Boolean(r.record?.pending);
    button('start').hidden = r.active || r.busy || savingUnknown || recovery;
    button('start').textContent = st.connected ? 'Начать калибровку' : 'Подключить и начать';
    button('start').disabled = start.blocked;
    button('retry-engine').hidden = !start.retry || !api.retryEngine;
    q('[data-fine-start-status]').hidden = Boolean(r.active || r.busy);
    text('[data-fine-start-status]', r.phase==='error' ? presentation.instruction+' Код: '+r.reason : start.message || (api.startup?.().measurement ? 'При запуске мастер завершит обычный замер стиков и начнёт калибровку.' : st.connected ? 'USB подключён. Нажмите «Начать калибровку».' : 'Нажмите «Подключить и начать» и выберите DualSense в окне браузера.'));
    if(start.blocked&&!r.active&&!r.busy){
      text('[data-fine-instruction]',start.message);
      text('[data-fine-state]',start.code==='engine_loading'?'Загрузка…':'Запуск недоступен');
      text('[data-fine-detail]','Код запуска: '+start.code);
    }
    button('save').hidden = !r.canSave; button('save').disabled = r.busy || !r.ownsConnection();
    button('recover').hidden = !recovery || savingUnknown || Boolean(capture) || r.busy; button('recover').disabled = r.busy || Boolean(capture) || (api.busy() && !r.active);
    button('verify').hidden = !r.record?.saved && !savingUnknown || Boolean(capture) || (r.active && !savingUnknown);
    q('[data-fine-power-cycle]').hidden = button('verify').hidden;
    button('verify').disabled = r.busy || (api.busy() && !r.active) || !api.engine() || !q('[data-fine-power-cycle-confirm]').checked;
    button('stop').hidden = !r.active && !r.busy;
    button('stop').disabled = r.phase === 'saving'; button('stop').textContent = capture || r.busy ? 'Остановить' : 'Завершить';
    button('restore').hidden = !r.record || recovery || savingUnknown;
    button('restore').disabled = Boolean(capture || r.busy || (api.busy() && !r.active));
    button('export').hidden = !r.record; button('export').disabled = r.busy;
    button('view').hidden = !r.record; button('view').disabled = r.busy;
    button('copy').hidden = !r.record; button('copy').disabled = r.busy;
    button('copy').textContent = copyState || 'Скопировать протокол';
    const controlReadback = ['control','verified','control-failed'].includes(r.phase) && r.record?.saved && sameParameters(r.parameters, r.record.saved.parameters);
    const proof = r.ownsConnection() && r.parameters && (controlReadback || r.initial && ['baseline','probe','verifying','ready','saved'].includes(r.phase));
    q('[data-fine-device-proof]').hidden = !proof;
    text('[data-fine-device-proof]', !proof ? '' : r.phase === 'verified' ? '✓ Настройки совпали; полное выключение отмечено пользователем' : r.phase === 'control-failed' ? '✓ Прочитанные настройки совпали с сохранёнными. Контрольный замер завершён.' : r.phase === 'saved' ? '✓ Команда сохранения выполнена. Остался контроль после выключения.' : r.phase === 'control' ? '✓ Прочитанные настройки совпали с сохранёнными. Проверяем работу стиков.' : sameParameters(r.parameters, r.initial) ? '✓ Исходные настройки прочитаны. Пока идёт первый замер, параметры не меняются.' : r.record?.pending?.purpose === 'range-probe' ? '✓ Временный диапазон применён и проверен чтением. Измеряем полный ход.' : '✓ Поправка применена в геймпаде и проверена чтением.');
    q('[data-fine-intro]').hidden = r.phase !== 'idle';
    q('[data-fine-results]').hidden = !capture && !r.baseline && !r.result;
    const completed = !capture && Boolean(r.result && r.baseline);
    q('[data-fine-legend] span:first-child').textContent = presentation.legendBefore;
    q('[data-fine-legend] span:nth-child(2)').textContent = presentation.legendAfter;
    q('[data-fine-legend]').hidden = !completed;
    q('[data-fine-outcome]').hidden = !completed;
    text('[data-fine-outcome]', presentation.outcome);
    const evidence = q('[data-fine-travel-evidence]'), evidenceList = q('[data-fine-travel-evidence-list]');
    const showEvidence = completed && r.phase === 'control-failed' && presentation.evidenceRows.length > 0;
    evidence.hidden = !showEvidence;
    const evidenceValue = presentation.evidenceRows.join('\n');
    if (evidenceList.dataset.value !== evidenceValue) {
      evidenceList.dataset.value = evidenceValue;
      evidenceList.replaceChildren(...presentation.evidenceRows.map(row => {const p=document.createElement('p');p.className='gp-small';p.textContent=row;return p;}));
    }
    for (let i=0;i<2;i++) {
      q('[data-fine-metrics="'+i+'"]').hidden = !completed;
      text('[data-fine-travel-title="'+i+'"]', travelMetricLabel(r.baseline, r.result));
      const a = r.baseline?.sticks[i], b = r.result?.sticks[i];
      for (const key of ['rms','returnWorst','travel']) {
        const value = profile => key === 'travel' ? profile ? Math.min(...profile.travel) : undefined : profile?.[key];
        text('[data-fine-'+key+'="'+i+'"]', pct(value(a)) + ' → ' + pct(value(b)));
      }
      const lane = capture?.lanes[i], laneCard = q('[data-fine-lane="'+i+'"]');
      laneCard.dataset.captureStage = lane?.stage ?? (capture ? 'rest' : 'result');
      laneCard.dataset.captureDirection = String(lane?.direction ?? 0);
      q('[data-lane-guide="'+i+'"]').hidden = !capture;
      text('[data-lane-instruction="'+i+'"]', lane?.instruction ?? (capture ? 'Отпустите стик' : ''));
      text('[data-lane-detail="'+i+'"]', lane?.detail ?? (capture ? 'Сначала измерим исходный центр' : ''));
      q('[data-lane-progress="'+i+'"]').value = lane?.actionProgress ?? (capture?.progress ?? 0) / .06;
      text('[data-fine-counter="'+i+'"]', lane?.done ? '✓ Готов' : lane ? Math.floor(lane.progress * 100) + '%' : capture ? 'Подготовка' : '');

    }
    const quality = completed ? r.result.sticks.map((p,i)=>(i?'Правый':'Левый')+' · неровный участок '+pct(p.worst)+' · разброс кругов '+pct(p.repeat)+' · разброс возврата '+pct(p.returnSpread)+' · шум '+pct(p.noise)).join('\n') : '';
    const rejected = r.phase === 'unchanged' && r.trial ? '\nОтклонённая попытка: ' + r.trial.sticks.map((p,i)=>(i?'правый':'левый')+' · круг '+pct(p.rms)+' · возврат '+pct(p.returnWorst)).join('; ') : '';
    text('[data-fine-quality]', quality + rejected);
  }
  function draw(now) {
    for (let i=0;i<2;i++) {
      const canvas = q('[data-fine-chart="'+i+'"]'), c = canvas.getContext('2d');
      const cx = 280, cy = 210, radius = 147;
      c.fillStyle = '#101f32'; c.fillRect(0,0,560,420);
      c.strokeStyle = '#4b6077'; c.lineWidth = 1.5; c.beginPath(); c.arc(cx,cy,radius,0,Math.PI*2); c.moveTo(cx-radius-24,cy); c.lineTo(cx+radius+24,cy); c.moveTo(cx,cy-radius-24); c.lineTo(cx,cy+radius+24); c.stroke();
      const line = (points,color,closed=true) => {if (!points?.length) return;c.strokeStyle=color;c.lineWidth=2.3;c.beginPath();let pen=false;points.forEach(p=>{if(!p){pen=false;return;}const [x,y]=p;pen?c.lineTo(cx+x*radius,cy+y*radius):c.moveTo(cx+x*radius,cy+y*radius);pen=true;});if(closed)c.closePath();c.stroke();};
      const cap = runner.capture, lane = cap?.lanes[i];
      if (!cap || runner.phase === 'verifying') line(runner.baseline?.sticks[i]?.points,'#f1b85f');
      if (!cap) line(runner.result?.sticks[i]?.points,'#47dfc6');
      else if (lane) {
        const rotating = ['cw','ccw'].includes(lane.stage);
        const passes = [...lane.passes,...(rotating?lane.turn.passes:[])];
        passes.forEach(p=>line(p.points,'#318e89'));
        if (rotating) line(lane.turn.bins.map(bin=>bin.at(-1)??null),'#47dfc6',false);
        if (lane.stage === 'aim') {
          const a=lane.direction*Math.PI/4, r=radius*lane.targetRadius;
          c.fillStyle=lane.inTarget?'#28b5a04d':'#f4c46944';c.strokeStyle=lane.inTarget?'#47dfc6':'#f4c469';c.lineWidth=2;
          c.beginPath();c.arc(cx,cy,r*1.1,a-RETURN_ANGLE,a+RETURN_ANGLE);c.arc(cx,cy,r*.88,a+RETURN_ANGLE,a-RETURN_ANGLE,true);c.closePath();c.fill();c.stroke();
        }
        if (lane.stage === 'release') {c.fillStyle='#47dfc622';c.strokeStyle='#47dfc6';c.lineWidth=3;c.beginPath();c.arc(cx,cy,23,0,Math.PI*2);c.fill();c.stroke();}
        if (!lane.probe && ['aim','release','done'].includes(lane.stage)) {
          for(let d=0;d<8;d++) {const a=d*Math.PI/4, done=lane.returns.length>d+1;c.fillStyle=done?'#47dfc6':d===lane.direction?'#f4c469':'#51677d';c.beginPath();c.arc(cx+Math.cos(a)*183,cy+Math.sin(a)*183,5,0,Math.PI*2);c.fill();}
        }
      }

      if (lastFrame && now-lastFrame.at<1500) {c.fillStyle='#fff';c.beginPath();c.arc(cx+lastFrame.axes[i*2]*radius,cy+lastFrame.axes[i*2+1]*radius,5,0,Math.PI*2);c.fill();}
      c.font='13px system-ui';c.fillStyle='#99b2c7';c.fillText('USB · без коррекции графика',16,400);
    }
  }
  const focusCapture = () => {if(runner.capture)card.scrollIntoView({block:'start',behavior:'smooth'});};
  const operations = {start:async()=>{
    if(startStatus().blocked){render();return;}
    copyState='';q('[data-fine-protocol]').hidden=true;
    api.prepareStart?.(); // Synchronous: preserve the click's USB user activation.
    await runner.start();focusCapture();
  },'retry-engine':()=>api.retryEngine?.(),diagnose:()=>{
    const pre=q('[data-fine-start-report]');pre.textContent=startupReport();pre.hidden=false;button('copy-start').hidden=false;
  },'copy-start':async()=>{
    const pre=q('[data-fine-start-report]');pre.textContent=startupReport();
    try{await navigator.clipboard.writeText(pre.textContent);text('[data-fine-copy-start]','Проверка скопирована. Можно отправить её мастеру.');}
    catch{text('[data-fine-copy-start]','Выделите и скопируйте текст проверки вручную.');pre.focus();}
  },save:()=>runner.save(),recover:()=>runner.recover(),verify:async()=>{const checkbox=q('[data-fine-power-cycle-confirm]'),confirmed=checkbox.checked;checkbox.checked=false;await runner.verify({powerCycleConfirmed:confirmed});focusCapture();},stop:()=>runner.cancel(),restore:()=>runner.restore(),view:()=>{const pre=q('[data-fine-protocol]');pre.textContent=JSON.stringify(runner.export(),null,2);pre.hidden=false;},copy:async()=>{
    try {await navigator.clipboard.writeText(JSON.stringify(runner.export(),null,2));copyState='✓ Протокол скопирован';}
    catch {copyState='Не удалось скопировать — скачайте протокол';}
    render();
  },export:()=>{
    const url = URL.createObjectURL(new Blob([JSON.stringify(runner.export(),null,2)],{type:'application/json'}));
    const anchor = document.createElement('a');anchor.href=url;anchor.download='remteh-calibration-v2.json';anchor.click();s.timer(()=>URL.revokeObjectURL(url),1000);
  }};
  for (const [name,operation] of Object.entries(operations)) s.on(button(name),'click',()=>void operation());
  s.on(q('[data-fine-power-cycle-confirm]'),'change',render);
  s.on(document,'visibilitychange',()=>{if(document.hidden)runner.pauseCapture();});
  const beforeUnload = event => {if(runner.active || runner.record?.pending){event.preventDefault();event.returnValue='';}};
  s.on(window,'beforeunload',beforeUnload);
  function tick(now) {
    const hidden = document.hidden || panel.hidden;
    if (hidden && !wasHidden) runner.pauseCapture();
    wasHidden = hidden;
    runner.tick();
    const st = api.state(), id = st.connected ? st.info?.tuningId : null, key = id ? id + ':' + api.engine()?.connection : null;
    if ((runner.active || runner.busy) && key) observed = key;
    if (!runner.active && !runner.busy && key && key !== observed) {
      observed=key;
      try {runner.inspect(id);} catch(error) {runner.phase='error';runner.reason=error.message;render();}
    }
    if(now-lastUi>100){lastUi=now;render();if(!panel.hidden)draw(now);}
  }
  function report() {
    if (runner.busy || runner.capture || !runner.baseline || !runner.result || !runner.record || api.state().info?.tuningId !== runner.record.identity || runner.snapshot?.connection !== api.engine()?.connection || runner.snapshot?.revision !== api.state().revision || runner.record.pending || !['ready','restored','saved','verified','unchanged','control-failed'].includes(runner.phase)) return null;
    const powerCycleConfirmed = runner.record?.verification?.powerCycleConfirmed === true;
    const metrics = {calibration_version:2,precision_mode:true,precision_verified_after_reconnect:runner.phase==='verified'&&powerCycleConfirmed,precision_power_cycle_user_confirmed:powerCycleConfirmed,precision_improvement:runner.verdict?.improvements.map(x=>x.kind).join(',')||'not_confirmed',precision_result_phase:runner.phase};
    for(let i=0;i<2;i++)for(const field of ['rms','worst','center','repeat','returnWorst','returnSpread'])for(const [name,profile] of [['before',runner.baseline],['after',runner.result]])metrics['precision_'+(i?'right':'left')+'_'+field+'_'+name+'_pct']=Number((profile.sticks[i][field]*100).toFixed(3));
    return {before:runner.baseline,after:runner.result,metrics,summary:labels[runner.phase]??'Калибровка стиков'};
  }
  function dispose() {
    if (disposePromise) return disposePromise;
    disposed=true;runner.cancelled=true;runner.pauseCapture();
    disposePromise=(async()=>{while(runner.busy)await new Promise(resolve=>setTimeout(resolve,20));await runner.cancel();})();
    return disposePromise;
  }
  s.clean(dispose);
  render();
  return {accept(frame){lastFrame=frame;if(!document.hidden && !panel.hidden)runner.accept(frame);},tick,dispose,get active(){return runner.active||runner.busy;},get report(){return report();}};
}
