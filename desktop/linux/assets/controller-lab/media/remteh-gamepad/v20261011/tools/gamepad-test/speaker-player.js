const AUDIO_URL=new URL('./audio/ps5-dualsense-speaker.mp3',import.meta.url);
const MAX_DURATION_MS=30000;

const failure=code=>Object.assign(new Error(code),{code});
const aborted=()=>Object.assign(new Error('aborted'),{name:'AbortError',code:'aborted'});
const isDefaultOutput=device=>!device?.deviceId||device.deviceId==='default'||device.deviceId==='communications';
const controllerLabel=device=>{const label=String(device?.label??'').trim().replace(/\s+/g,' ');return /dual\s*sense/i.test(label)||label.toLowerCase()==='wireless controller';};

export function controllerAudioOutputs(devices=[]){
 const list=[...devices],controllerGroups=new Set(list.filter(controllerLabel).map(device=>device.groupId).filter(Boolean));
 const seen=new Set();
 return list.filter(device=>{
  if(device?.kind!=='audiooutput'||isDefaultOutput(device)||seen.has(device.deviceId))return false;
  const matches=controllerLabel(device)||(device.groupId&&controllerGroups.has(device.groupId));
  if(matches)seen.add(device.deviceId);
  return matches;
 }).sort((a,b)=>String(a.label).localeCompare(String(b.label),'ru'));
}

export function buildFourChannelBuffer(context,decoded,volume=.45){
 const level=Math.max(0,Math.min(1,Number(volume)||0)),sourceRate=Number(decoded?.sampleRate)||48000;
 if(!decoded||!Number.isFinite(decoded.length)||decoded.length<1||typeof context?.createBuffer!=='function')throw failure('audio_decode_failed');
 const length=Math.max(1,Math.ceil(decoded.length*48000/sourceRate)),buffer=context.createBuffer(4,length,48000),left=buffer.getChannelData(0),right=buffer.getChannelData(1);
 const channels=[];for(let channel=0;channel<Math.max(1,decoded.numberOfChannels||1);channel++)channels.push(decoded.getChannelData(channel));
 for(let i=0;i<length;i++){
  const position=i*sourceRate/48000,index=Math.min(decoded.length-1,Math.floor(position)),next=Math.min(decoded.length-1,index+1),part=position-index;
  let sample=0;for(const data of channels)sample+=(data[index]??0)+((data[next]??0)-(data[index]??0))*part;
  sample=sample/channels.length*level;left[i]=sample;right[i]=sample;
 }
 // Channels 2 and 3 intentionally remain zero: they must never drive the rear/haptics pair.
 return buffer;
}

export function speakerPlayerMessage(error){
 const code=error?.code??error?.message;
 return {
  audio_output_unsupported:'Этот браузер не умеет направлять звук в выбранное устройство. Откройте тест в Chrome.',
  output_not_found:'Аудиовыход DualSense не найден. Подключите геймпад по USB и повторите поиск.',
  output_not_controller:'Выбран не аудиовыход DualSense. Выберите «DualSense» или «Wireless Controller».',
  output_selection_required:'Найдено несколько выходов контроллера. Выберите нужный в списке.',
  output_changed:'Выбранный аудиовыход больше недоступен. Подключите DualSense по USB повторно.',
  output_route_failed:'Chrome не подтвердил вывод звука в DualSense. Звук не запускался.',
  output_channels_failed:'Аудиовыход контроллера не предоставляет 4 канала. Звук не запускался.',
  audio_fetch_failed:'Не удалось загрузить тестовый звук. Обновите страницу и повторите.',
  audio_decode_failed:'Не удалось подготовить тестовый звук. Обновите страницу и повторите.',
  audio_too_long:'Тестовый звук длиннее 30 секунд и заблокирован.',
  audio_playback_timeout:'Воспроизведение не завершилось вовремя и остановлено.',
  audio_context_failed:'Не удалось запустить аудиосистему браузера. Нажмите кнопку ещё раз.',
  permission_denied:'Без разрешения Chrome не показал названия аудиовыходов. Запись микрофона не выполняется.',
  aborted:'Тест остановлен. Звук не запускался.',
 }[code]??'Не удалось подготовить звук для динамика DualSense.';
}

export function createSpeakerPlayer({
 mediaDevices=globalThis.navigator?.mediaDevices,
 AudioContextClass=globalThis.AudioContext??globalThis.webkitAudioContext,
 fetchImpl=globalThis.fetch?.bind(globalThis),
 assetUrl=AUDIO_URL,
 onChange=()=>{},
 onRouteLost=()=>{},
}={}){
 let outputs=[],selectedId='',context=null,contextOwner=null,routeConfirmed=false,decoded=null,playingSource=null,finishPlayback=null,operation=null,generation=0,volume=.45;
 let status={phase:'idle',message:'Найдите аудиовыход DualSense. Звук на динамики компьютера не направляется.'};
 const supported=Boolean(mediaDevices?.enumerateDevices&&AudioContextClass&&typeof AudioContextClass.prototype?.setSinkId==='function'&&fetchImpl);
 const emit=(phase,message)=>{status={phase,message};onChange(state());};
 const currentOutput=()=>outputs.find(device=>device.deviceId===selectedId)??null;
 const assertCurrent=id=>{if(id!==generation)throw aborted();};
 const playbackDuration=()=>decoded?Math.min(MAX_DURATION_MS,Math.ceil(decoded.duration*1000)+1500):0;
 const state=()=>({supported,outputs:[...outputs],selectedId,status:{...status},volume,clipDurationMs:decoded?Math.ceil(decoded.duration*1000):0,durationMs:playbackDuration(),ready:Boolean(decoded&&currentOutput()),active:Boolean(operation||playingSource)});

 const routeLost=code=>{if(!selectedId&&!playingSource&&!operation)return;stop();selectedId='';emit('error',speakerPlayerMessage(failure(code)));onRouteLost(code);};
 const contextRouteCheck=()=>{if(!context||!routeConfirmed||!selectedId)return;if(context.sinkId!==selectedId||(playingSource&&context.state!=='running'))routeLost(context.sinkId!==selectedId?'output_route_failed':'output_changed');};
 const deviceChange=()=>{const expected=selectedId,expectedGeneration=generation;if(!expected)return;void mediaDevices.enumerateDevices().then(devices=>{if(expectedGeneration!==generation||selectedId!==expected)return;const available=controllerAudioOutputs(devices).some(device=>device.deviceId===expected);if(!available)routeLost('output_changed');else void refresh(expectedGeneration).catch(()=>{});}).catch(()=>{if(expectedGeneration===generation&&selectedId===expected)routeLost('output_changed');});};
 mediaDevices?.addEventListener?.('devicechange',deviceChange);

 function releaseContext(owner=null){
  if(owner!==null&&contextOwner!==owner)return;const old=context;context=null;contextOwner=null;routeConfirmed=false;if(!old)return;
  old.removeEventListener?.('sinkchange',contextRouteCheck);old.removeEventListener?.('statechange',contextRouteCheck);try{Promise.resolve(old.close?.()).catch(()=>{});}catch{}
 }

 function boundedResume(audioContext,signal=null){
  if(signal?.aborted)return Promise.resolve({ok:false,error:aborted()});
  let request;try{request=audioContext.resume();}catch(error){request=Promise.reject(error);}let timer,onAbort;
  const resumed=Promise.resolve(request).then(()=>({ok:true}),error=>({ok:false,error}));
  const timeout=new Promise(resolve=>{timer=setTimeout(()=>resolve({ok:false,error:failure('audio_context_failed')}),3000);});
  const waits=[resumed,timeout];if(signal)waits.push(new Promise(resolve=>{onAbort=()=>resolve({ok:false,error:aborted()});signal.addEventListener('abort',onAbort,{once:true});}));
  return Promise.race(waits).finally(()=>{clearTimeout(timer);if(onAbort)signal.removeEventListener('abort',onAbort);});
 }

 function primeContext(id,signal){
  try{
   const ownContext=new AudioContextClass({sampleRate:48000,latencyHint:'interactive'});context=ownContext;contextOwner=id;routeConfirmed=false;ownContext.addEventListener?.('sinkchange',contextRouteCheck);ownContext.addEventListener?.('statechange',contextRouteCheck);
   return {context:ownContext,resume:boundedResume(ownContext,signal)};
  }catch{throw failure('audio_context_failed');}
 }

 async function refresh(id=null,signal=null){
  if(!mediaDevices?.enumerateDevices){outputs=[];selectedId='';throw failure('audio_output_unsupported');}
  const devices=await mediaDevices.enumerateDevices();if(id!==null){assertCurrent(id);if(signal?.aborted)throw aborted();}outputs=controllerAudioOutputs(devices);
  const lostSelection=Boolean(selectedId&&!outputs.some(device=>device.deviceId===selectedId));if(lostSelection){routeLost('output_changed');if(id!==null)throw aborted();}
  if(!selectedId&&!lostSelection&&outputs.length===1)selectedId=outputs[0].deviceId;
  onChange(state());return [...outputs];
 }

 function select(deviceId){
  if(!outputs.some(device=>device.deviceId===deviceId))throw failure('output_not_controller');
  selectedId=deviceId;emit('selected','Выбран аудиовыход: '+(currentOutput()?.label||'DualSense'));return currentOutput();
 }

 async function revealWithPermission(id,signal){
  if(typeof mediaDevices.selectAudioOutput==='function'){
   const chosen=await mediaDevices.selectAudioOutput();assertCurrent(id);if(signal.aborted)throw aborted();
   const devices=await mediaDevices.enumerateDevices();assertCurrent(id);if(signal.aborted)throw aborted();const all=[chosen,...devices.filter(device=>device.deviceId!==chosen?.deviceId)];outputs=controllerAudioOutputs(all);
   if(!chosen||!outputs.some(device=>device.deviceId===chosen.deviceId))throw failure('output_not_controller');
   selectedId=chosen.deviceId;onChange(state());return;
  }
  if(typeof mediaDevices.getUserMedia!=='function')throw failure('output_not_found');
  let stream;
  try{stream=await mediaDevices.getUserMedia({audio:true});}
  catch(error){if(error?.name==='NotAllowedError'||error?.name==='SecurityError')throw failure('permission_denied');throw error;}
  finally{stream?.getTracks?.().forEach(track=>track.stop());}
  assertCurrent(id);if(signal.aborted)throw aborted();await refresh(id,signal);
 }

 async function ensureOutput(id,signal,prompt=true){
  await refresh(id,signal);assertCurrent(id);if(signal.aborted)throw aborted();
  if(currentOutput())return currentOutput();
  if(outputs.length>1)throw failure('output_selection_required');
  if(!prompt)throw failure('output_not_found');
  emit('permission',typeof mediaDevices.selectAudioOutput==='function'?'Выберите аудиовыход DualSense в окне Chrome.':'Chrome может запросить микрофон только для показа названий выходов. Поток сразу закрывается; запись не ведётся.');
  await revealWithPermission(id,signal);assertCurrent(id);if(signal.aborted)throw aborted();
  if(currentOutput())return currentOutput();
  if(outputs.length>1)throw failure('output_selection_required');
  throw failure('output_not_found');
 }

 async function route(id,signal,primed){
  const output=currentOutput();if(!output)throw failure('output_not_found');
  routeConfirmed=false;
  let ownContext;
  try{ownContext=primed?.context??context;if(!ownContext||contextOwner!==id)throw aborted();const resumed=await primed.resume;if(!resumed.ok)throw resumed.error;if(ownContext.state!=='running')throw failure('audio_context_failed');assertCurrent(id);if(signal.aborted||context!==ownContext||contextOwner!==id)throw aborted();await ownContext.setSinkId(output.deviceId);}
  catch(error){releaseContext(id);if(error?.name==='AbortError'||error?.code==='aborted')throw error;throw failure(error?.code==='audio_context_failed'?'audio_context_failed':'output_route_failed');}
  assertCurrent(id);if(signal.aborted||context!==ownContext||contextOwner!==id)throw aborted();
  if(ownContext.sinkId!==output.deviceId){releaseContext(id);throw failure('output_route_failed');}
  if(Number(ownContext.destination?.maxChannelCount)<4){releaseContext(id);throw failure('output_channels_failed');}
  try{ownContext.destination.channelCount=4;ownContext.destination.channelCountMode='explicit';ownContext.destination.channelInterpretation='discrete';}
  catch{releaseContext(id);throw failure('output_channels_failed');}
  routeConfirmed=true;return ownContext;
 }

 async function load(id,signal,audioContext){
  if(decoded)return;
  const url=assetUrl instanceof URL?assetUrl:new URL(String(assetUrl),globalThis.location?.href);
  if(globalThis.location?.origin&&url.origin!==globalThis.location.origin)throw failure('audio_fetch_failed');
  let response;try{response=await fetchImpl(url.href,{signal,credentials:'same-origin',cache:'force-cache'});}catch(error){if(error?.name==='AbortError')throw aborted();throw failure('audio_fetch_failed');}
  if(!response?.ok)throw failure('audio_fetch_failed');
  const bytes=await response.arrayBuffer();assertCurrent(id);if(signal.aborted)throw aborted();
  let result;try{result=await audioContext.decodeAudioData(bytes.slice(0));}catch{throw failure('audio_decode_failed');}
  assertCurrent(id);if(signal.aborted||context!==audioContext||contextOwner!==id)throw aborted();
  if(!Number.isFinite(result?.duration)||result.duration<=0)throw failure('audio_decode_failed');
  if(result.duration*1000>MAX_DURATION_MS)throw failure('audio_too_long');decoded=result;
 }

 async function runPreparation({loadAudio,prompt=true}={}){
  if(!supported)throw failure('audio_output_unsupported');
  stop();const id=++generation,controller=new AbortController();operation=controller;
  emit('preparing',loadAudio?'Подготавливаем аудиовыход и тестовый звук…':'Ищем аудиовыход DualSense…');
  try{
   const primed=primeContext(id,controller.signal);await ensureOutput(id,controller.signal,prompt);const ownContext=await route(id,controller.signal,primed);if(loadAudio)await load(id,controller.signal,ownContext);assertCurrent(id);
   emit(loadAudio?'ready':'selected',loadAudio?'Звук подготовлен для '+(currentOutput()?.label||'DualSense')+'.':'Аудиовыход готов: '+(currentOutput()?.label||'DualSense')+'.');if(!loadAudio)releaseContext(id);
   return state();
  }catch(error){releaseContext(id);if(id===generation)emit('error',speakerPlayerMessage(error));throw error;}
  finally{if(id===generation)operation=null;onChange(state());}
 }

 const connect=()=>runPreparation({loadAudio:false,prompt:true});
 const prepare=()=>runPreparation({loadAudio:true,prompt:true});

 async function play({signal}={}){
  if(!context||!decoded||!currentOutput())throw failure('audio_context_failed');
  const ownContext=context,ownContextOwner=contextOwner;let buffer,source,splitter,merger;
  try{
   if(signal?.aborted)throw aborted();const resumed=await boundedResume(ownContext,signal);if(!resumed.ok)throw resumed.error;
   if(context!==ownContext||contextOwner!==ownContextOwner)throw aborted();
   if(ownContext.state!=='running')throw failure('audio_context_failed');
   if(ownContext.sinkId!==selectedId)throw failure('output_route_failed');if(signal?.aborted)throw aborted();
   buffer=buildFourChannelBuffer(ownContext,decoded,volume);source=ownContext.createBufferSource();splitter=ownContext.createChannelSplitter(4);merger=ownContext.createChannelMerger(4);
   source.buffer=buffer;source.channelCount=4;source.channelCountMode='explicit';source.channelInterpretation='discrete';merger.channelCountMode='explicit';merger.channelInterpretation='discrete';
   source.connect(splitter);for(let channel=0;channel<4;channel++)splitter.connect(merger,channel,channel);merger.connect(ownContext.destination);
  }catch(error){releaseContext(ownContextOwner);throw error;}
  playingSource=source;emit('playing','Воспроизводим через '+(currentOutput()?.label||'DualSense')+'…');
  return new Promise((resolve,reject)=>{
   let settled=false;const timeoutMs=Math.max(1000,playbackDuration());
   const cleanup=()=>{clearTimeout(timer);signal?.removeEventListener('abort',onAbort);source.onended=null;try{source.disconnect();splitter.disconnect();merger.disconnect();}catch{}if(playingSource===source)playingSource=null;finishPlayback=null;releaseContext(ownContextOwner);onChange(state());};
   const done=(error=null)=>{if(settled)return;settled=true;cleanup();if(error){emit('error',speakerPlayerMessage(error));reject(error);}else{emit('ready','Воспроизведение завершено. Отметьте результат после проверки.');resolve();}};
   const onAbort=()=>{try{source.stop();}catch{}done(aborted());};
   const timer=setTimeout(()=>{try{source.stop();}catch{}done(failure('audio_playback_timeout'));},timeoutMs);
   finishPlayback=onAbort;source.onended=()=>done();signal?.addEventListener('abort',onAbort,{once:true});
   try{source.start();}catch{done(failure('audio_context_failed'));}
  });
 }

 function stop(){
  generation++;operation?.abort();operation=null;if(finishPlayback)finishPlayback();else if(playingSource){try{playingSource.stop();}catch{}playingSource=null;releaseContext();}else releaseContext();
  if(status.phase==='playing'||status.phase==='preparing'||status.phase==='permission')emit('stopped','Тест остановлен. Звук не запускался повторно.');
 }
 function setVolume(value){volume=Math.max(0,Math.min(1,Number(value)||0));onChange(state());return volume;}
 async function destroy(){stop();mediaDevices?.removeEventListener?.('devicechange',deviceChange);decoded=null;outputs=[];selectedId='';}

 return {state,refresh,select,connect,prepare,play,stop,setVolume,destroy,get active(){return Boolean(operation||playingSource);},get durationMs(){return playbackDuration();},get supported(){return supported;}};
}
