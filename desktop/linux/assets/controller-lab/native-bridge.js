/** A narrow local-only adapter. USB writes still pass the original Sony engine guards. */
export function installAndroidBridge(){
 if(!window.DeckivoUsb)return;
 let serial=0;const pending=new Map(),devices=new Map(),hid=new EventTarget();
 const bytes=text=>Uint8Array.from(atob(text),c=>c.charCodeAt(0));
 const encode=data=>btoa(String.fromCharCode(...new Uint8Array(data.buffer??data,data.byteOffset??0,data.byteLength??data.length)));
 const call=(operation,payload={})=>new Promise((resolve,reject)=>{const id=String(++serial);const timer=setTimeout(()=>{pending.delete(id);reject(new Error('Operation timed out'));},operation==='choose'||operation==='saveFile'?180000:15000);pending.set(id,{resolve,reject,timer});window.DeckivoUsb.request(id,operation,JSON.stringify(payload));});
 const device=info=>{
  if(devices.has(info.deviceId))return devices.get(info.deviceId);
  const d=new EventTarget();Object.assign(d,info,{opened:false,open:async()=>{const result=await call('open',{deviceId:info.deviceId});d.collections=result.collections;d.opened=true;},close:async()=>{await call('close',{deviceId:info.deviceId});d.opened=false;},sendFeatureReport:(reportId,data)=>call('featureWrite',{deviceId:info.deviceId,reportId,data:encode(data)}),receiveFeatureReport:async reportId=>new DataView(bytes((await call('featureRead',{deviceId:info.deviceId,reportId})).data).buffer),sendReport:(reportId,data)=>call('outputWrite',{deviceId:info.deviceId,reportId,data:encode(data)})});
  devices.set(info.deviceId,d);return d;
 };
 hid.getDevices=async()=>(await call('granted')).map(device);
 hid.requestDevice=async()=> (await call('choose')).map(device);
 Object.defineProperty(navigator,'hid',{value:hid});
 Object.defineProperty(navigator,'getGamepads',{value:()=>window.__deckivoGamepads??[]});
 document.addEventListener('click',event=>{
  const a=event.target.closest?.('a[download]');if(!a)return;
  const url=new URL(a.href,location.href);if(url.protocol!=='blob:'&&url.origin!==location.origin)return;
  event.preventDefault();
  void fetch(url.href).then(response=>{if(!response.ok)throw new Error('Export failed');return response.arrayBuffer();}).then(buffer=>{
   if(buffer.byteLength>12*1024*1024)throw new Error('Export too large');
   const array=new Uint8Array(buffer);let text='';for(let i=0;i<array.length;i+=8192)text+=String.fromCharCode(...array.subarray(i,i+8192));
   return call('saveFile',{name:a.download||'controller-firmware.bin',data:btoa(text)});
  }).catch(error=>{document.querySelector('#result').textContent=error.message;});
 },true);
 window.DeckivoNative={
  complete(id,value,error){const p=pending.get(id);if(!p)return;pending.delete(id);clearTimeout(p.timer);if(error)p.reject(new Error(error));else p.resolve(value);},
  input(id,reportId,data){const d=devices.get(id);if(!d?.opened)return;const event=new Event('inputreport');Object.assign(event,{device:d,reportId,data:new DataView(bytes(data).buffer)});d.dispatchEvent(event);d.oninputreport?.(event);},
  disconnect(id){const d=devices.get(id);if(!d)return;d.opened=false;const event=new Event('disconnect');event.device=d;hid.dispatchEvent(event);devices.delete(id);},
  gamepads(value){window.__deckivoGamepads=value.map(p=>p?{...p,timestamp:performance.now()}:null);},
 };
}
