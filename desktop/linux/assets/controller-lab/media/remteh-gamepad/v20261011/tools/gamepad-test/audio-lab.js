export function createAudioLab(s,root,onChange,isBlocked=()=>false){
  let stream=null,ac=null,analyser=null,recorder=null,timer=null,url=null,epoch=0,peak=0,noise=null,noiseSamples=null,micLabel='',confirmed=false,report=null,busy=false,recorded=false;
  root.innerHTML=`<div class="gp-panel-heading"><div><h3>Микрофон геймпада</h3><p>Выберите именно микрофон контроллера. Запись остаётся в этом браузере.</p></div></div>
    <div class="gp-actions"><button type="button" data-mic="devices">Найти микрофоны</button><label class="gp-grow">Аудиовход<select data-mic-input aria-label="Микрофон для проверки"><option value="">Сначала разрешите доступ к микрофону</option></select></label><button type="button" data-mic="start" disabled>Слушать уровень</button><button type="button" data-mic="stop">Стоп микрофон</button></div>
    <p class="gp-inline-note" data-mic-message role="status">Для DualSense подключите USB. Если ОС не предоставляет его аудиовход, проверка микрофона геймпада здесь недоступна.</p>
    <label class="gp-checkbox"><input type="checkbox" data-mic-confirm> Подтверждаю: выбран микрофон геймпада</label>
    <div class="gp-audio-meter"><progress max="1" value="0" data-mic-level></progress><strong data-mic-db>— dBFS</strong></div><canvas width="800" height="170" data-mic-spectrum aria-label="Спектр микрофона"></canvas>
    <div class="gp-actions gp-spaced"><button type="button" data-mic="record" disabled>Записать 5 секунд</button><button type="button" data-mic="noise" disabled>Шум в тишине · 3 с</button></div><audio hidden controls data-mic-audio></audio><p data-mic-metrics class="gp-small">Сигнал ещё не измерен</p>`;
  const q=sel=>root.querySelector(sel),btn=key=>q(`[data-mic="${key}"]`),input=q('[data-mic-input]');
  const db=v=>Math.max(-120,20*Math.log10(Math.max(v,1e-6))),message=str=>q('[data-mic-message]').textContent=str;
  const supported=Boolean(navigator.mediaDevices?.getUserMedia&&(window.AudioContext||window.webkitAudioContext));
  function controls(){
    const blocked=isBlocked();
    btn('start').disabled=!supported||busy||blocked||Boolean(stream)||!input.value;
    btn('devices').disabled=!supported||busy||blocked||Boolean(stream);
    btn('stop').disabled=!stream&&!busy;
    input.disabled=busy||Boolean(stream)||blocked;
    q('[data-mic-confirm]').disabled=busy||blocked||!input.value;
    btn('record').disabled=blocked||!stream||!confirmed||recorder?.state==='recording'||Boolean(noiseSamples);
    btn('noise').disabled=btn('record').disabled;
  }
  function changed(){onChange();controls();}
  function clearEvidence(){
    report=null;recorded=false;noise=null;peak=0;micLabel='';
    const audio=q('[data-mic-audio]');audio.pause();audio.hidden=true;audio.removeAttribute('src');
    if(url)URL.revokeObjectURL(url);url=null;
    q('[data-mic-metrics]').textContent='Сигнал ещё не измерен';
    const canvas=q('[data-mic-spectrum]');canvas.getContext('2d').clearRect(0,0,canvas.width,canvas.height);
  }
  function stop(clear=false){
    epoch++;clearTimeout(timer);timer=null;noiseSamples=null;
    if(recorder?.state==='recording')recorder.stop();recorder=null;
    stream?.getTracks().forEach(t=>t.stop());stream=null;analyser=null;void ac?.close().catch(()=>{});ac=null;busy=false;
    q('[data-mic-level]').value=0;q('[data-mic-db]').textContent='Остановлен';
    if(clear){clearEvidence();confirmed=false;q('[data-mic-confirm]').checked=false;}
    controls();
  }
  async function devices(){
    if(!supported||busy||stream||isBlocked())return;
    stop(true);changed();const id=++epoch;busy=true;controls();message('Разрешите доступ, чтобы увидеть названия аудиовходов.');let permission;
    try{
      permission=await navigator.mediaDevices.getUserMedia({audio:true});permission.getTracks().forEach(t=>t.stop());
      const list=(await navigator.mediaDevices.enumerateDevices()).filter(d=>d.kind==='audioinput'&&d.deviceId!=='default'&&d.deviceId!=='communications');
      if(s.dead||id!==epoch)return;
      input.replaceChildren(new Option('Выберите микрофон геймпада',''));
      for(const d of list)input.add(new Option(d.label||'Аудиовход',d.deviceId));
      const sony=list.find(d=>/dualsense|wireless controller|dualshock/i.test(d.label));
      if(sony){input.value=sony.deviceId;message('Найден аудиовход контроллера. Проверьте название и подтвердите выбор.');}
      else message('Выберите вход, который ОС назначила геймпаду. Встроенный микрофон компьютера не подтверждает работу микрофона геймпада.');
    }catch{if(id===epoch)message('Доступ не получен. Разрешите микрофон для сайта РемТех и повторите поиск.');}
    finally{permission?.getTracks().forEach(t=>t.stop());if(id===epoch){busy=false;controls();}}
  }
  async function start(){
    if(!supported||!input.value||busy||stream||isBlocked())return;
    stop();clearEvidence();changed();const id=++epoch;busy=true;controls();
    try{
      const next=await navigator.mediaDevices.getUserMedia({audio:{deviceId:{exact:input.value},echoCancellation:false,noiseSuppression:false,autoGainControl:false}});
      if(s.dead||id!==epoch){next.getTracks().forEach(t=>t.stop());return;}
      stream=next;micLabel=next.getAudioTracks()[0].label||input.selectedOptions[0]?.textContent||'Неизвестный вход';
      ac=new(window.AudioContext||window.webkitAudioContext)();await ac.resume();if(id!==epoch||!stream)return;
      analyser=ac.createAnalyser();analyser.fftSize=2048;ac.createMediaStreamSource(stream).connect(analyser);
      message('Говорите в микрофон геймпада: '+micLabel);
      stream.getTracks().forEach(track=>track.addEventListener('ended',()=>{if(id!==epoch)return;stop(true);message('Аудиовход отключён. Выберите устройство заново.');changed();},{once:true}));
    }catch{if(id===epoch){stop(true);message('Этот аудиовход недоступен. Повторите поиск устройств.');changed();}}
    finally{if(id===epoch){busy=false;controls();}}
  }
  function evidence(){
    if(!confirmed||!micLabel)return;
    report={status:peak<.0001?'warn':'info',mic_input:micLabel,mic_peak_dbfs:+db(peak).toFixed(1),mic_noise_dbfs:noise===null?'not_measured':+db(noise).toFixed(1),mic_sample_rate:ac?.sampleRate??0,mic_recorded:recorded,mic_confirmed:true};
    q('[data-mic-metrics]').textContent=`Пик ${report.mic_peak_dbfs} dBFS · шум ${noise===null?'не измерен':report.mic_noise_dbfs+' dBFS'} · ${report.mic_sample_rate} Гц`;
    changed();
  }
  s.on(btn('devices'),'click',devices);s.on(btn('start'),'click',start);
  s.on(btn('stop'),'click',()=>{if(stream)evidence();stop();message('Микрофон остановлен.');});
  s.on(input,'change',()=>{stop(true);changed();});
  s.on(q('[data-mic-confirm]'),'change',e=>{confirmed=e.target.checked;if(!confirmed){stop();clearEvidence();}changed();});
  s.on(btn('record'),'click',()=>{
    if(!stream||!confirmed||recorder?.state==='recording'||noiseSamples||isBlocked())return;
    if(!window.MediaRecorder){message('Запись не поддерживается этим браузером. Индикатор уровня работает.');return;}
    try{
      const id=epoch,chunks=[],capture=new MediaRecorder(stream);recorder=capture;
      capture.ondataavailable=e=>{if(e.data.size)chunks.push(e.data);};
      capture.onstop=()=>{
        if(id!==epoch||s.dead)return;
        if(!chunks.length){message('Запись пуста. Повторите проверку.');controls();return;}
        if(url)URL.revokeObjectURL(url);url=URL.createObjectURL(new Blob(chunks,{type:capture.mimeType}));
        q('[data-mic-audio]').src=url;q('[data-mic-audio]').hidden=false;recorded=true;
        message('Запись готова. Прослушайте её и отметьте результат ниже.');evidence();
      };
      capture.start();message('Идёт запись · 5 секунд');controls();
      timer=setTimeout(()=>{if(id===epoch&&capture.state==='recording')capture.stop();},5000);
    }catch{message('Не удалось начать запись.');controls();}
  });
  s.on(btn('noise'),'click',()=>{
    if(!stream||!confirmed||noiseSamples||recorder?.state==='recording'||isBlocked())return;
    noiseSamples=[];message('Тишина · 3 секунды. Не касайтесь геймпада.');controls();const id=epoch;
    timer=setTimeout(()=>{
      if(id!==epoch||!noiseSamples)return;
      if(noiseSamples.length<10){noiseSamples=null;message('Недостаточно данных. Повторите замер шума.');controls();return;}
      noise=noiseSamples.reduce((a,b)=>a+b,0)/noiseSamples.length;noiseSamples=null;message('Шум измерен.');evidence();
    },3000);
  });
  function update(){
    controls();if(!analyser)return;
    const wave=new Float32Array(analyser.fftSize);analyser.getFloatTimeDomainData(wave);let sum=0;
    for(const v of wave){sum+=v*v;peak=Math.max(peak,Math.abs(v));}
    const level=Math.sqrt(sum/wave.length);if(noiseSamples)noiseSamples.push(level);
    q('[data-mic-level]').value=Math.min(1,level*6);q('[data-mic-db]').textContent=db(level).toFixed(1)+' dBFS';
    const freq=new Uint8Array(analyser.frequencyBinCount);analyser.getByteFrequencyData(freq);
    const c=q('canvas').getContext('2d');c.fillStyle='#101f32';c.fillRect(0,0,800,170);c.fillStyle='#3ed2c1';
    for(let i=0;i<100;i++){const n=freq[Math.floor(Math.pow(i/100,2)*freq.length)];c.fillRect(i*8,170-n/255*170,5,n/255*170);}
  }
  s.on(document,'visibilitychange',()=>{if(document.hidden)stop();});s.clean(()=>stop(true));controls();
  if(!supported)message('В этом браузере проверка микрофона недоступна. Откройте эту страницу в Chrome или Edge.');
  return {update,stop,reset:()=>{stop(true);changed();},get active(){return Boolean(stream)||busy;},get evidence(){return report;},get metrics(){if(!report)return {};const {status,...metrics}=report;return metrics;}};
}
