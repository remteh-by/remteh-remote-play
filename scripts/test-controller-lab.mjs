import {chromium} from 'playwright';
import {parse} from 'acorn';
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import assert from 'node:assert/strict';
import os from 'node:os';
const root=path.resolve('desktop/linux/assets/controller-lab');
const output=process.env.DECKIVO_QA_DIR??path.join(os.tmpdir(),'deckivo-controller-qa');
fs.mkdirSync(output,{recursive:true});
const server=http.createServer((request,response)=>{
 const url=new URL(request.url,'http://localhost');
 if(url.pathname.endsWith('/firmware.php')) {
  if(url.search){response.writeHead(400).end('Version catalog only');return;}
  response.writeHead(200,{'Content-Type':'application/json'}).end(JSON.stringify({checked_at:'2026-10-26T00:00:00Z',stale:false,versions:{'0004':'0x0458','000B':'0x0458','000E':'0x0458','0044':'0x0270'}}));return;
 }
 const filename=path.resolve(root,'.'+decodeURIComponent(url.pathname==='/'?'/index.html':url.pathname));
 if(!filename.startsWith(root+path.sep)){response.writeHead(403).end();return;}
 const types={'.js':'text/javascript','.json':'application/json','.css':'text/css','.html':'text/html','.svg':'image/svg+xml','.png':'image/png','.woff2':'font/woff2'};
 try{response.writeHead(200,{'Content-Type':types[path.extname(filename)]??'application/octet-stream'}).end(fs.readFileSync(filename));}
 catch{response.writeHead(404).end();}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const url='http://127.0.0.1:'+server.address().port;
const executable=process.env.DECKIVO_CHROME??(process.platform==='darwin'?'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome':undefined);
const browser=await chromium.launch({headless:true,...(executable?{executablePath:executable}:{}),args:['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream','--mute-audio']});
const results=[];
const protocolFixture = String.raw`export function createSonyEngine({onFrame,onState}) {
 const model=globalThis.__qaHidModel??'DS5',name=model==='DS4'?'DualShock 4':'DualSense';
 const state={connected:false,busy:false,fault:false,mode:null,dirty:false,saved:false,nvLocked:true,revision:0,
  info:{model,name,verified:true,readable:true,blocked:0,persistentSave:true,tuningId:'a'.repeat(64),fields:{'FW Update':'0x0458','FW Update Info':'0x41','SW Version':'1.0','Board Model':'TEST','Serial Number':'SYNTHETIC'},nv:'locked'},battery:{level:85,charging:false}};
 const parameters=[0,0,0,0,65535,65535,65535,65535,32768,32768,32768,32768];
 let interval;
 const frame=()=>({connection:1,axisBytes:[128,128,128,128],axes:[0,0,0,0],buttons:{cross:false,circle:false,square:false,triangle:false,l1:false,r1:false,l2:false,r2:false,options:false,create:false,l3:false,r3:false,ps:false,touchpad:false},triggers:[0.25,0.75],touch:[{id:1,x:0.5,y:0.4}],imu:{gyro:{x:1,y:2,z:3},accel:{x:0,y:0,z:1}},timestamp:performance.now()});
 const notify=()=>onState({...state});
 const api={get state(){return {...state};},get connection(){return 1;},guard(){if(!state.connected)throw Error('disconnected');},outputGuard(){api.guard();},
  async connect(){await navigator.hid.requestDevice({filters:[]});state.connected=true;notify();onFrame(frame());interval=setInterval(()=>onFrame(frame()),16);},
  async disconnect(){clearInterval(interval);state.connected=false;notify();},
  async testEffect(){return {completed:true,cancelled:false};},async stopEffects(){},async rumble(){return {completed:true};},
  async beginTuning(){state.mode='fine-tune';notify();return {identity:state.info.tuningId,parameters:[...parameters],original:[...parameters],connection:1,revision:state.revision};},
  endTuning(){state.mode=null;notify();},
  async readTuning(){return {identity:state.info.tuningId,parameters:[...parameters],connection:1,revision:state.revision};},
  async writeTuning(values){state.dirty=true;state.revision++;notify();return {parameters:[...values],connection:1,revision:state.revision};},
  async restoreTuning(){state.dirty=false;notify();},
  async beginCenter(){state.mode='center';notify();},async sampleCenter(){},async endCenter(){state.mode=null;state.dirty=true;state.revision++;notify();},
  async beginRange(){state.mode='range';notify();},async endRange(){state.mode=null;state.dirty=true;state.revision++;notify();},
  async autoCenter(){state.dirty=true;notify();},async savePermanent(){throw Error('test_policy_must_gate_permanent_write');},async saveTuning(){throw Error('test_policy_must_gate_permanent_write');}};
 return api;
}`;
function sourceCases() {
 const values=new Set();
 const add=value=>{
  if(!/[А-Яа-яЁё]/.test(value)||value==='Русский')return;
  if(/<[a-z/!]/i.test(value)) {
   for(const match of value.matchAll(/(?:^|>)([^<]+)/g))if(/[А-Яа-яЁё]/.test(match[1]))values.add(match[1].trim());
   for(const match of value.matchAll(/(?:title|placeholder|aria-label|alt)=["']([^"']+)["']/g))if(/[А-Яа-яЁё]/.test(match[1]))values.add(match[1].trim());
  }else values.add(value.trim());
 };
 const walk=node=>{
  if(!node||typeof node!=='object')return;
  if(node.type==='Literal'&&typeof node.value==='string')add(node.value);
  if(node.type==='TemplateElement')add(node.value.cooked??node.value.raw);
  for(const value of Object.values(node))if(Array.isArray(value))value.forEach(walk);else if(value&&typeof value==='object')walk(value);
 };
 const visit=directory=>{for(const entry of fs.readdirSync(directory,{withFileTypes:true})){const file=path.join(directory,entry.name);if(entry.isDirectory())visit(file);else if(entry.name.endsWith('.js'))walk(parse(fs.readFileSync(file,'utf8'),{ecmaVersion:'latest',sourceType:'module'}));}};
 visit(path.join(root,'media'));
 return [...values].filter(Boolean);
}

async function reportContrast(page,label){
 await settle(page);
 const measurements=await page.evaluate(()=>{
  const canvas=document.createElement('canvas'),ctx=canvas.getContext('2d');
  const rgb=color=>{ctx.clearRect(0,0,1,1);ctx.fillStyle=color;ctx.fillRect(0,0,1,1);return [...ctx.getImageData(0,0,1,1).data].slice(0,3).map(x=>x/255);};
  const luminance=c=>rgb(c).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4).reduce((a,x,i)=>a+x*[.2126,.7152,.0722][i],0);
  const root=document.querySelector('#gpd'),rows=[];
  for(const kind of ['info','pass','fail']){
   const pill=document.createElement('span');pill.className='gp-result-pill '+kind;pill.textContent='Contrast fixture';root.append(pill);
   const s=getComputedStyle(pill),a=luminance(s.color),b=luminance(s.backgroundColor);rows.push({kind,color:s.color,background:s.backgroundColor,ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)});pill.remove();
  }
  return rows;
 });
 for(const row of measurements)assert.ok(row.ratio>=4.5,label+' '+JSON.stringify(row));
 results.push({label:label+' contrast',measurements});
 await page.screenshot({path:path.join(output,label+'-report.png'),fullPage:true});
}

async function settle(page){await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));}
async function checkEnglish(page,label) {
 await settle(page);
 const missing=await page.evaluate(()=>{
  const result=[];const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let node;
  while((node=walker.nextNode())) {
   if(/^(SCRIPT|STYLE)$/.test(node.parentElement?.tagName)||node.parentElement?.closest('#language'))continue;
   if(/[А-Яа-яЁё]/.test(node.nodeValue))result.push(node.nodeValue.trim());
  }
  for(const el of document.querySelectorAll('[title],[aria-label],[placeholder],[alt]'))for(const key of ['title','aria-label','placeholder','alt']) {
   const text=el.getAttribute(key);if(/[А-Яа-яЁё]/.test(text??''))result.push(key+': '+text);
  }
  return [...new Set(result)];
 });
 results.push({label,cyrillic:missing});
 if(missing.length)fs.writeFileSync(path.join(output,'missing-english.json'),JSON.stringify(results,null,2));
 assert.equal(missing.length,0,label+': untranslated Cyrillic: '+JSON.stringify(missing.slice(0,12)));
}
const mockInput=({id})=>{
 const buttons=Array.from({length:18},()=>({pressed:false,touched:false,value:0}));
 const pad={id,index:0,connected:true,mapping:'standard',timestamp:1,axes:[0,0,0,0],buttons,vibrationActuator:{type:'dual-rumble',playEffect:async()=> 'complete',reset:async()=> 'complete'}};
 window.__qaPad=pad;
 window.__qaInput=(pressed=false)=>{pad.timestamp=performance.now();pad.buttons.forEach((b,i)=>{b.pressed=pressed&&i===0;b.value=b.pressed?1:0;});};
 Object.defineProperty(navigator,'getGamepads',{value:()=>id?[pad]:[]});
 Object.defineProperty(navigator,'hid',{value:{getDevices:async()=>[],requestDevice:async()=>[],addEventListener(){},removeEventListener(){}}});
};
try {
 for(const id of (process.env.DECKIVO_USB_ONLY?[]:['', 'DualSense Wireless Controller (Vendor: 054c Product: 0ce6)','DualShock 4 (Vendor: 054c Product: 09cc)','Xbox Series Controller (Vendor: 045e Product: 0b13)'])) {
  const context=await browser.newContext({viewport:{width:1440,height:1000},permissions:[]});
  const page=await context.newPage(),errors=[];page.on('pageerror',error=>{errors.push(error.message);console.error('BROWSER:',error.message);});
  await page.addInitScript(mockInput,{id});
  await page.goto(url+'/?lang=en');await page.waitForSelector('.gp-workbench');
  await checkEnglish(page,(id||'disconnected')+' initial');
  
  if(id){await page.evaluate(()=>{window.__qaInput(true);window.__qaPad.axes=[0.75,-0.25,-0.5,0.8];window.__qaPad.buttons[6].value=0.4;window.__qaPad.buttons[7].value=0.8;});await checkEnglish(page,id+' live input');await page.evaluate(()=>window.__qaInput(false));}
  const tabs=await page.locator('button[data-tab]').evaluateAll(elements=>elements.map(e=>e.dataset.tab));
  for(const tab of tabs) {
   if(process.env.DECKIVO_REPORT_ONLY && tab!=='comparison')continue;
   const button=page.locator('button[data-tab="'+tab+'"]');
   if(await button.isVisible()&&await button.isEnabled()) {
    await button.click();await checkEnglish(page,(id||'disconnected')+' tab:'+tab);
    if(tab==='comparison'&&id)await reportContrast(page,id.startsWith('Xbox')?'xbox':id.startsWith('DualShock')?'ds4':'dualsense');
    for(const summary of await page.locator('details:not([open]) > summary').all())if(await summary.isVisible()){await summary.click();await checkEnglish(page,'details '+tab);}
   }
  }
  await page.screenshot({path:path.join(output,(id.startsWith('Xbox')?'xbox':id.startsWith('DualShock')?'ds4':id?'dualsense':'disconnected')+'.png')});
  assert.deepEqual(errors,[],'page errors');await context.close();
 }
 for(const model of (process.env.DECKIVO_REPORT_ONLY?[]:['DS5','DS4'])) {
  const context=await browser.newContext({viewport:{width:1440,height:1000}});
  const page=await context.newPage(),errors=[];page.on('pageerror',error=>{errors.push(error.message);console.error('BROWSER:',error.message);});
  await page.addInitScript(({model})=>{
   window.__qaHidModel=model;Object.defineProperty(navigator,'getGamepads',{value:()=>[]});
   Object.defineProperty(navigator,'hid',{value:{getDevices:async()=>[],requestDevice:async()=>[{vendorId:0x054c,productId:model==='DS4'?0x09cc:0x0ce6}],addEventListener(){},removeEventListener(){}}});
  },{model});
  await page.route('**/sony-engine.js',route=>route.fulfill({contentType:'text/javascript',body:protocolFixture}));
  await page.goto(url+'/?lang=en');await page.waitForSelector('.gp-workbench');
  await page.locator('[data-gp="connect"]').click();
  await page.waitForFunction(()=>document.querySelector('[data-source]')?.textContent.includes('USB'));
  await checkEnglish(page,model+' USB connected');
  const tabs=await page.locator('button[data-tab]').evaluateAll(elements=>elements.map(e=>e.dataset.tab));
  for(const tab of tabs) {
   if(process.env.DECKIVO_REPORT_ONLY && tab!=='comparison')continue;
   const button=page.locator('button[data-tab="'+tab+'"]');
   if(!await button.isVisible()||!await button.isEnabled())continue;
   await button.click();await checkEnglish(page,model+' USB '+tab);
   for(const summary of await page.locator('details:not([open]) > summary').all())if(await summary.isVisible()){await summary.click();await checkEnglish(page,model+' USB details '+tab);}
   const actions={triggers:['vib-left','vib-right','adaptive-resistance','adaptive-single','adaptive-machinegun','stop'],touch:['reset-touch'],audio:['speaker','headphones','stop'],device:['firmware','lights','lights-rgb','lights-player','lights-mute','stop']};
   for(const action of actions[tab]??[]) {
    const control=page.locator('[data-lab="'+action+'"]');
    if(await control.count()&&await control.isVisible()&&await control.isEnabled()){await control.click();await checkEnglish(page,model+' action:'+action);}
   }
   if(tab==='comparison') {
    await reportContrast(page,model);
    const control=page.locator('[data-lab="export"]');
    if(await control.count()&&await control.isVisible()&&await control.isEnabled()) {
     const download=page.waitForEvent('download');await control.click();const artifact=await download;
     await artifact.saveAs(path.join(output,model+'-report.json'));await checkEnglish(page,model+' export');
    }
   }
  }
  assert.equal(await page.locator('[data-fw-download]').count(),0,'no firmware binary link');
  await page.locator('button[data-tab="calibration"]').click();
  assert.equal(await page.locator('[data-gp="flash"]').isVisible(),false,'permanent save hidden by default');
  await page.locator('#deckivo-service-mode').check();
  assert.equal(await page.locator('#deckivo-service-mode').isChecked(),true);
  const intent=page.evaluate(async()=>{
   const policy=await import('/media/remteh-gamepad/calibration-20261020b/service-mode.js');
   const parameters=[0,0,0,0,65535,65535,65535,65535,32768,32768,32768,32768],controller={};
   const record=policy.preserveOriginal('b'.repeat(64),parameters);
   try {await policy.permanentWrite(controller,'b'.repeat(64),record,()=>{policy.requireFlashPermit(controller);window.__qaSyntheticWrites=(window.__qaSyntheticWrites??0)+1;});return 'written';}
   catch(error){return error.message;}
  });
  await page.waitForSelector('.deckivo-service-dialog');
  await checkEnglish(page,model+' permanent warning');
  assert.equal(await page.locator('[data-permanent-confirm]').isDisabled(),true);
  await page.locator('.deckivo-service-dialog button').filter({hasText:'Cancel'}).click();
  assert.equal(await intent,'confirmation_required');
  assert.equal(await page.evaluate(()=>window.__qaSyntheticWrites??0),0);
  await page.locator('#deckivo-service-mode').uncheck();
  assert.equal(await page.locator('[data-gp="flash"]').isVisible(),false);
  await checkEnglish(page,model+' after cancel');
  // Probe every source message, including branches requiring unavailable physical states.
  await page.evaluate(values=>{const div=document.createElement('div');div.id='translation-corpus';for(const value of values){const p=document.createElement('p');p.textContent=value;div.append(p);}document.body.append(div);},sourceCases());
  await checkEnglish(page,model+' source message corpus');
  await page.locator('#translation-corpus').evaluate(element=>element.remove());
  assert.deepEqual(errors,[],'USB fixture page errors');await context.close();
 }
 {
  const context=await browser.newContext({viewport:{width:1000,height:900}}),page=await context.newPage();
  await page.goto(url+'/?lang=ru');await page.waitForSelector('#deckivo-service-mode');
  assert.equal(await page.locator('#deckivo-service-mode').isChecked(),false);
  await page.locator('#deckivo-service-mode').check();await page.reload();await page.waitForSelector('#deckivo-service-mode');
  assert.equal(await page.locator('#deckivo-service-mode').isChecked(),true,'service choice persists after reload');
  const operation=page.evaluate(async()=>{const policy=await import('/media/remteh-gamepad/calibration-20261020b/service-mode.js');const id='c'.repeat(64),backup=policy.preserveOriginal(id,Array(12).fill(200));try{await policy.permanentWrite({},id,backup,()=>{throw Error('must not write');});}catch(error){return error.message;}});
  await page.waitForSelector('.deckivo-service-dialog');
  assert.match(await page.locator('.deckivo-service-dialog').innerText(),/Необратимая запись во флеш геймпада/);
  assert.equal(await page.locator('[data-permanent-confirm]').isDisabled(),true);
  await page.locator('#permanent-write-confirmation').check();
  assert.equal(await page.locator('[data-permanent-confirm]').isEnabled(),true);
  await page.locator('.deckivo-service-dialog button').filter({hasText:'Отмена'}).click();
  assert.equal(await operation,'confirmation_required');
  results.push({label:'RU irreversible warning, required checkbox and persisted service mode',cyrillic:[]});
  await context.close();
 }
 fs.writeFileSync(path.join(output,'controller-english-results.json'),JSON.stringify(results,null,2)+'\n');
 console.log('Controller English states passed:',results.length);
} finally {await browser.close();await new Promise(resolve=>server.close(resolve));}
