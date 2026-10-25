// Measurements are observations of browser reports, never an estimate of physical latency.
export class TriggerTravel {
  constructor(){this.reset();}
  reset(){this.min=null;this.max=null;this.bins=new Set();this.cycles=0;this.phase='release';this.trace=[];this.samples=0;this.lastAt=null;this.traceAt=null;this.pressBins=new Set();this.returnBins=new Set();this.incomplete=false;}
  add(value,at=performance.now()){
    if(!Number.isFinite(value)||!Number.isFinite(at))return;
    const v=Math.max(0,Math.min(1,value)),bin=Math.min(20,Math.floor(v*20));
    const gap=this.lastAt!==null&&(at<this.lastAt||at-this.lastAt>250);
    if(gap){this.phase='release';this.pressBins.clear();this.returnBins.clear();this.trace.push(null);}
    this.lastAt=at;this.samples++;this.min=Math.min(this.min??v,v);this.max=Math.max(this.max??v,v);this.bins.add(bin);
    if(this.traceAt===null||gap||at-this.traceAt>=16){this.trace.push(v);this.traceAt=at;this.trace=this.trace.slice(-300);}
    if(this.phase==='release'){
      if(v<.04){this.phase='press';this.pressBins=new Set([bin]);}
    }else if(this.phase==='press'){
      this.pressBins.add(bin);
      if(v>.96){this.phase='return';this.returnBins=new Set([bin]);}
      else if(v<.04)this.pressBins=new Set([bin]);
    }else{
      this.returnBins.add(bin);
      if(v<.04){
        const complete=this.pressBins.size>=17&&this.returnBins.size>=17;
        if(complete)this.cycles++;
        this.incomplete=!complete;this.phase='press';this.pressBins=new Set([bin]);this.returnBins.clear();
      }
    }
  }
  get coverage(){return Math.round(this.bins.size/21*100);}
  get complete(){return this.cycles>=2;}
}

// A completed check observes release -> press -> release on one continuous
// stream. A button held during connection/reset is not evidence of a full cycle.
export class ButtonCheck {
  constructor(){this.reset();}
  reset(){this.entries=new Map();this.lastAt=null;}
  add(values,at=performance.now()){
    if(!Number.isFinite(at))return;
    const gap=this.lastAt!==null&&(at<this.lastAt||at-this.lastAt>250);this.lastAt=at;
    const present=new Set();
    for(const [key,raw]of Object.entries(values??{})){
      if(typeof raw!=='boolean'&&!Number.isFinite(raw))continue;
      const value=Number(raw);present.add(key);
      let entry=this.entries.get(key);
      if(!entry){entry={presses:0,cycles:0,repeats:0,lastPress:null,down:false,armed:false,pending:false};this.entries.set(key,entry);}
      if(gap){entry.armed=false;entry.pending=false;entry.lastPress=null;}
      if(value<=.25){
        if(entry.pending&&entry.down)entry.cycles++;
        entry.down=false;entry.pending=false;entry.armed=true;
      }else if(value>.5){
        if(entry.armed&&!entry.down){
          entry.presses++;entry.pending=true;
          if(entry.lastPress!==null&&at-entry.lastPress<80)entry.repeats++;
          entry.lastPress=at;
        }
        entry.down=true;
      }
    }
    for(const [key,entry]of this.entries)if(!present.has(key)){entry.armed=false;entry.pending=false;entry.down=false;entry.lastPress=null;}
  }
  get unchecked(){return [...this.entries].filter(([,v])=>v.cycles===0).map(([key])=>key);}
  get checked(){return this.entries.size-this.unchecked.length;}
  get complete(){return this.entries.size>0&&this.unchecked.length===0;}
  get repeats(){return [...this.entries.values()].reduce((n,v)=>n+v.repeats,0);}
  get report(){return Object.fromEntries([...this.entries].map(([key,{presses,cycles,repeats}])=>[key,{presses,cycles,fast_repeats:repeats}]));}
}
// FW Type is a device-internal enum, not the Sony catalog ID.
// Feature report 0x20 byte 46 identifies image variants A/B/E.
// See nowrep/dualsensectl main.c and Paliverse/DualSense-List-of-Firmwares metadata.
export function firmwareStatus(info,catalog){
  const fields=info?.fields??{},current=fields['FW Update'];
  if(!['DS5','DS5_Edge'].includes(info?.model))return {kind:'unsupported',current:current??null};
  const raw=fields['FW Update Info'];
  const variant=/^0x[0-9a-f]{2}$/i.test(raw??'')?String.fromCharCode(parseInt(raw,16)):null;
  const type=info.model==='DS5_Edge'?'0044':({A:'0004',B:'000B',E:'000E'})[variant];
  if(!type||!/^0x[0-9a-f]{4}$/i.test(current??''))return {kind:'unknown',current:current??null,variant};
  const latest=catalog?.versions?.[type];
  if(!/^0x[0-9a-f]{4}$/i.test(latest??''))return {kind:'unknown',current,type,variant};
  const a=parseInt(current,16),b=parseInt(latest,16);
  return {kind:a<b?'update':a===b?'current':'newer',current,latest,type,variant,checkedAt:catalog.checked_at};
}
export function worstStatus(values){return ['fail','warn','info','pass'].find(v=>values.includes(v))??'info';}
