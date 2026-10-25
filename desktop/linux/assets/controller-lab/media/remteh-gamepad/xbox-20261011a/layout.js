// Public presentation only. Device commands stay in the shared, verified module.
const root = document.querySelector('#diag-tool');
const page = root?.closest('.rt-gamepad-public');
const launch = document.querySelector('[data-public-connect]');
const help = document.querySelector('[data-public-connect-help]');
const originalHelp=help?.textContent??'';
const testerTitle=document.querySelector('#tester .gpd-section-head h2');
const originalTitle=testerTitle?.textContent??'';
function sync() {
  const connect = root?.querySelector('[data-gp="connect"]');
  const workbench = root?.querySelector('.gp-workbench');
  const connected = workbench?.dataset.hidConnected === 'true';
  const browserConnected=workbench?.dataset.live==='true'&&workbench?.dataset.controllerFamily!=='sony';
  const empty = String(workbench?.dataset.live !== 'true');
  if (page && page.dataset.empty !== empty) page.dataset.empty = empty;
  if(testerTitle){const title=browserConnected?(workbench.dataset.controllerFamily==='xbox'?'Тест Xbox':'Тест геймпада'):originalTitle;if(testerTitle.textContent!==title)testerTitle.textContent=title;}
  if (!launch) return;
  const ready = root?.dataset.publicReady === 'true';
  const disabled = !ready || (Boolean(navigator.hid) && !connected && !browserConnected && !!connect?.disabled);
  if (launch.disabled !== disabled) launch.disabled = disabled;
  const label = browserConnected ? (workbench.dataset.controllerFamily==='xbox'?'Открыть тест Xbox':'Открыть подключённый геймпад') : connected ? 'Открыть подключённый геймпад' : (navigator.hid ? 'Подключить Sony по USB' : 'Открыть тест геймпада');
  if (launch.textContent !== label) launch.textContent = label;
  if(help){const text=browserConnected?'Геймпад определён. Нажимайте кнопки, двигайте стики и проверяйте курки.':!navigator.hid?'Тест кнопок и стиков доступен здесь. Для калибровки Sony откройте страницу в Chrome или Edge на компьютере.':originalHelp;if(help.textContent!==text)help.textContent=text;}
}
function handleLaunch() {
  const connect = root?.querySelector('[data-gp="connect"]');
  const workbench=root?.querySelector('.gp-workbench');
  const connected = workbench?.dataset.hidConnected === 'true'||(workbench?.dataset.live==='true'&&workbench?.dataset.controllerFamily!=='sony');
  // Synchronous forwarding preserves the user's WebHID activation.
  if (!connected && navigator.hid && connect && !connect.hidden && !connect.disabled) connect.click();
  document.querySelector('#tester')?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});
}
launch?.addEventListener('click',handleLaunch);
const observer = new MutationObserver(sync);
if (root) observer.observe(root,{subtree:true,attributes:true,attributeFilter:['data-public-ready','disabled','data-live','data-hid-connected','data-controller-family','data-controller-model']});
sync();
window.addEventListener('pagehide',()=>observer.disconnect());
window.addEventListener('pageshow',event=>{if(event.persisted&&root){observer.observe(root,{subtree:true,attributes:true,attributeFilter:['data-public-ready','disabled','data-live','data-hid-connected','data-controller-family','data-controller-model']});sync();}});
