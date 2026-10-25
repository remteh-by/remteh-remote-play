// Precision measurements consume unmodified USB axes. Parameter predictions are
// provisional: only a fresh measured improvement can be accepted or saved.
export const EDGE_AXES=[[0,4,8],[1,5,9],[2,6,10],[3,7,11]];
const TAU=2*Math.PI,N=120;
const rms=a=>Math.sqrt(a.reduce((s,v)=>s+v*v,0)/a.length);
export const median=a=>{const s=[...a].sort((x,y)=>x-y),n=s.length;return n?(s[(n-1)>>1]+s[n>>1])/2:NaN;};
const norm=a=>Math.atan2(Math.sin(a),Math.cos(a));
const emptyBins=()=>Array.from({length:N},()=>[]);
const rest=samples=>Array.from({length:4},(_,i)=>{const a=samples.map(s=>s[i]),mean=a.reduce((a,b)=>a+b,0)/a.length;return {mean,noise:rms(a.map(x=>x-mean))};});
export function validParameters(v){return Array.isArray(v)&&v.length===12&&v.every(x=>Number.isInteger(x)&&x>=0&&x<=65535)&&EDGE_AXES.every(([lo,hi,c])=>v[c]-v[lo]>=64&&v[hi]-v[c]>=64);}
export function validProfile(p){
 const vector=(a,n)=>Array.isArray(a)&&a.length===n&&a.every(Number.isFinite);
 return p?.version===1&&Array.isArray(p.axes)&&p.axes.length===4&&p.axes.every(a=>Number.isFinite(a.mean)&&Number.isFinite(a.noise))&&Array.isArray(p.sticks)&&p.sticks.length===2&&p.sticks.every(s=>['rms','worst','p95','repeat','spread','center','noise'].every(k=>Number.isFinite(s[k])&&s[k]>=0)&&Array.isArray(s.points)&&s.points.length===120&&s.points.every(a=>vector(a,2))&&Array.isArray(s.holds)&&s.holds.length===8&&s.holds.every(a=>vector(a,2))&&vector(s.travel,4));
}
export function boundedParameters(v,origin,limit=.2){return validParameters(v)&&validParameters(origin)&&EDGE_AXES.every(([lo,hi,c])=>Math.abs(v[c]-origin[c])<=Math.min(origin[c]-origin[lo],origin[hi]-origin[c])*.08&&[lo,hi].every(k=>Math.abs(v[k]-origin[k])<=Math.abs(origin[k]-origin[c])*limit));}

class Turns{
 constructor(direction){this.direction=direction;this.passes=[];this.reset();}
 reset(arming=true){this.arming=arming;this.bins=emptyBins();this.lastAngle=null;this.lastTime=null;this.travel=0;this.start=0;}
 add(x,y,time){
  if(this.passes.length>=2)return;
  if(Math.hypot(x,y)<.6){this.reset();return;}
  const angle=Math.atan2(y,x);
  if(this.lastAngle!==null){const delta=norm(angle-this.lastAngle)*this.direction;
   if(time-this.lastTime>150||Math.abs(delta)>.26||this.travel+delta<-.2){this.reset();}
   else this.travel+=delta;
  }
  if(this.lastAngle===null)this.start=time;
  this.lastAngle=angle;this.lastTime=time;
  // The path from centre to the rim is not part of the circular gate.
  // Arm only after sustained angular motion, then collect every sector anew.
  if(this.arming){
   if(this.travel<Math.PI/6||time-this.start<250)return;
   this.arming=false;this.bins=emptyBins();this.travel=0;this.start=time;
  }
  const bin=Math.min(N-1,Math.floor((angle+Math.PI)/TAU*N));
  // Bound memory while keeping a representative spread at 250 Hz.
  if(this.bins[bin].length<48)this.bins[bin].push([x,y]);
  if(this.travel>=TAU&&time-this.start>=1500&&this.bins.every(b=>b.length>=2)){
   this.passes.push(this.bins.map(b=>[median(b.map(p=>p[0])),median(b.map(p=>p[1]))]));this.reset(false);
  }
 }
 get progress(){if(this.arming)return this.passes.length/2;return Math.min(1,(this.passes.length+Math.max(0,Math.min(1,this.travel/TAU)))/2);}
}
export class PrecisionCapture{
 constructor(){this.stage='rest';this.started=null;this.last=-Infinity;this.samples=[];this.startRest=null;this.turns=[new Turns(1),new Turns(1)];this.cw=null;this.ccw=null;this.holds=[[],[]];this.holdBuffers=[[],[]];this.holdStarted=[null,null];this.direction=0;this.done=false;this.result=null;}
 add(axes,time){
  if(this.done||!Array.isArray(axes)||axes.length<4||!axes.slice(0,4).every(Number.isFinite)||time-this.last<2)return;
  const gap=time-this.last;this.last=time;
  if(this.stage==='rest'||this.stage==='rest-end'){
   if(this.started===null||gap>150){this.started=time;this.samples=[];}
   if(time-this.started>=1000)this.samples.push(axes.slice(0,4));
   if(time-this.started>=4000&&this.samples.length>=100){
    const measured=rest(this.samples);
    if(this.stage==='rest'){this.startRest=measured;this.stage='cw';}
    else{this.result=makeProfile(this.cw,this.ccw,this.holds,measured,this.startRest);this.done=true;this.stage='done';}
    this.started=null;this.samples=[];
   }return;
  }
  if(this.stage==='cw'||this.stage==='ccw'){
   this.turns.forEach((t,i)=>t.add(axes[2*i],axes[2*i+1],time));
   if(this.turns.every(t=>t.passes.length===2)){
    if(this.stage==='cw'){this.cw=this.turns.map(t=>t.passes);this.turns=[new Turns(-1),new Turns(-1)];this.stage='ccw';}
    else{this.ccw=this.turns.map(t=>t.passes);this.stage='holds';}
   }return;
  }
  if(this.stage==='holds'){
   for(let i=0;i<2;i++){
    if(this.holds[i][this.direction])continue;
    const x=axes[2*i],y=axes[2*i+1],a=this.direction*Math.PI/4;
    if(gap>150||Math.hypot(x,y)<.65||Math.abs(norm(Math.atan2(y,x)-a))>Math.PI/12){this.holdBuffers[i]=[];this.holdStarted[i]=null;continue;}
    if(this.holdStarted[i]===null)this.holdStarted[i]=time;
    this.holdBuffers[i].push([x,y]);
    if(time-this.holdStarted[i]>=450&&this.holdBuffers[i].length>=30)this.holds[i][this.direction]=[median(this.holdBuffers[i].map(p=>p[0])),median(this.holdBuffers[i].map(p=>p[1]))];
   }
   if(this.holds.every(h=>h[this.direction])){this.direction++;this.holdStarted=[null,null];this.holdBuffers=[[],[]];if(this.direction===8){this.stage='rest-end';this.started=null;}}
  }
 }
 get progress(){if(!Number.isFinite(this.last))return 0;if(this.done)return 1;if(this.stage==='rest')return Math.min(.08,(this.last-(this.started??this.last))/4000*.08);if(this.stage==='cw'||this.stage==='ccw')return (this.stage==='cw'?.08:.4)+Math.min(...this.turns.map(t=>t.progress))*.32;if(this.stage==='holds')return .72+this.direction/8*.2;return .92+Math.min(.08,(this.last-(this.started??this.last))/4000*.08);}
 get instruction(){
  if(!Number.isFinite(this.last))return 'Отпустите оба стика. Замер покоя: 4 с.';
  if(this.stage==='rest'||this.stage==='rest-end')return `Отпустите оба стика. Замер покоя: ${Math.max(0,4-Math.floor((this.last-(this.started??this.last))/1000))} с.`;
  if(this.stage==='cw'||this.stage==='ccw')return `${this.stage==='cw'?'↻ По часовой':'↺ Против часовой'}: 2 медленных круга по внешнему краю каждым стиком. Левый ${this.turns[0].passes.length}/2 · правый ${this.turns[1].passes.length}/2. Стики можно вращать по очереди.`;
  if(this.stage==='holds'){const names=['вправо ↦','вправо-вниз ↘','вниз ↓','влево-вниз ↙','влево ←','влево-вверх ↖','вверх ↑','вправо-вверх ↗'];return `Удерживайте оба стика до упора ${names[this.direction]}: левый ${this.holds[0][this.direction]?'✓':'…'} · правый ${this.holds[1][this.direction]?'✓':'…'}. Направление ${this.direction+1}/8.`;}
  return 'Подробный замер готов.';
 }
}
function metrics(points,passes,holds,axes){
 const radii=points.map(p=>Math.hypot(...p)),errors=radii.map(r=>Math.abs(r-1)),sorted=[...errors].sort((a,b)=>a-b);
 const spreads=points.map((p,k)=>rms(passes.map(pass=>Math.hypot(...pass[k])-radii[k])));
 return {points,holds,rms:rms(errors),worst:Math.max(...errors),p95:sorted[Math.floor(N*.95)],repeat:rms(spreads),spread:Math.max(...spreads),center:Math.hypot(axes[0].mean,axes[1].mean),noise:Math.hypot(axes[0].noise,axes[1].noise),travel:[Math.abs(holds[0][0]),Math.abs(holds[2][1]),Math.abs(holds[4][0]),Math.abs(holds[6][1])]};
}
function makeProfile(cw,ccw,holds,axes,startRest){return {version:1,axes,startRest,sticks:[0,1].map(i=>{const passes=[...cw[i],...ccw[i]],points=Array.from({length:N},(_,k)=>[median(passes.map(p=>p[k][0])),median(passes.map(p=>p[k][1]))]);return metrics(points,passes,holds[i],axes.slice(2*i,2*i+2));})};}
function remap(value,axis,from,to){const[lo,hi,c]=EDGE_AXES[axis],raw=from[c]+value*(value<0?from[c]-from[lo]:from[hi]-from[c]);return (raw-to[c])/(raw<to[c]?to[c]-to[lo]:to[hi]-to[c]);}
export function predictedProfile(profile,from,to){return {...profile,sticks:profile.sticks.map((s,i)=>{
 const points=s.points.map(p=>p.map((v,j)=>remap(v,2*i+j,from,to))),holds=s.holds.map(p=>p.map((v,j)=>remap(v,2*i+j,from,to))),axes=profile.axes.slice(2*i,2*i+2).map((a,j)=>({...a,mean:remap(a.mean,2*i+j,from,to)}));
 return metrics(points,[points],holds,axes);
})};}
const score=s=>s.rms+.25*s.worst+.2*s.p95+3*s.center+8*s.travel.reduce((sum,x)=>sum+Math.max(0,.975-x)**2,0);
export function proposeCorrection(profile,current,origin,attempt=0){
 if(!boundedParameters(current,origin)||profile.sticks.some(s=>s.repeat>.018||s.spread>.06))return null;
 let best=[...current],bestProfile=profile,bestScore=profile.sticks.reduce((s,p)=>s+score(p),0);
 // Coordinate descent adjusts only the four real edge registers per stick.
 // A previous rejection gets a smaller trust region; it never flips arbitrary axes.
 const stepLimit=.065/2**Math.min(2,attempt);
 for(let pass=0;pass<3;pass++)for(let axis=0;axis<4;axis++){
  const [lo,hi,c]=EDGE_AXES[axis];
  for(const k of [lo,hi,c])for(const sign of [-1,1]){
   const step=Math.max(1,Math.round(Math.abs(current[k===c?hi:k]-current[c])*(k===c?.003:stepLimit)/2**pass));
   const next=[...best];next[k]+=sign*step;
   if(!boundedParameters(next,origin)||!EDGE_AXES.every(([a,b,m])=>[a,b].every(j=>Math.abs(next[j]-current[j])<=Math.abs(current[j]-current[m])*stepLimit*1.5)))continue;
   const projected=predictedProfile(profile,current,next);
   if(projected.sticks.some((s,i)=>s.center>Math.max(.012,profile.sticks[i].center+.004)||s.travel.some((v,j)=>v<Math.min(.975,profile.sticks[i].travel[j]-.006))))continue;
   const value=projected.sticks.reduce((s,p)=>s+score(p),0);
   if(value<bestScore-1e-7){best=next;bestProfile=projected;bestScore=value;}
  }
 }
 const improvement=profile.sticks.reduce((s,x)=>s+x.rms,0)-bestProfile.sticks.reduce((s,x)=>s+x.rms,0);
 const centerImproved=bestProfile.sticks.some((s,i)=>profile.sticks[i].center-s.center>Math.max(.004,2*profile.sticks[i].noise));
 return improvement>Math.max(.0025,...profile.sticks.map(s=>s.repeat*1.5))||centerImproved?{parameters:best,predicted:bestProfile}:null;
}
export function assessImprovement(before,after){
 if(!before?.sticks||!after?.sticks||before.sticks.length!==2||after.sticks.length!==2)return {accepted:false,reason:'Замер не завершён.'};
 let gains=0,centerGains=0;
 for(let i=0;i<2;i++){
  const a=before.sticks[i],b=after.sticks[i],uncertainty=Math.max(.0025,2*Math.hypot(a.repeat,b.repeat));
  if(b.repeat>.018||b.spread>.06)return {accepted:false,reason:'Круги недостаточно повторяемы. Возвращён предыдущий вариант.'};
  if(b.rms>a.rms+uncertainty*.4||b.worst>a.worst+Math.max(.008,uncertainty)||b.center>a.center+Math.max(.008,2*Math.hypot(a.noise,b.noise))||b.noise>a.noise+.008||b.travel.some((v,j)=>v<Math.min(.975,a.travel[j]-.008)))return {accepted:false,reason:'Ухудшился круг, центр или полный ход. Возвращён предыдущий вариант.'};
  if(a.rms-b.rms>uncertainty)gains++;
  const restVariation=p=>{
   const start=p.startRest?.slice(i*2,i*2+2);
   const end=p.axes?.slice(i*2,i*2+2);
   return start?.length===2&&end?.length===2&&[...start,...end].every(x=>Number.isFinite(x.mean))?Math.hypot(...start.map((x,k)=>x.mean-end[k].mean)):0;
  };
  const centerUncertainty=Math.max(.004,2*Math.hypot(a.noise,b.noise),restVariation(before),restVariation(after));
  if(a.center-b.center>centerUncertainty)centerGains++;
 }
 if(gains)return {accepted:true,kind:'circle',reason:'Улучшение окружности подтверждено повторным USB-замером.'};
 if(centerGains)return {accepted:true,kind:'center',reason:'Смещение центра уменьшилось. Изменение окружности пока в пределах погрешности.'};
 return {accepted:false,kind:null,reason:'Изменение меньше погрешности измерения. Возвращён предыдущий вариант.'};
}
export function verifyProfile(saved,measured){
 return Boolean(validProfile(saved)&&validProfile(measured)&&measured.sticks.every((p,i)=>{
  const prior=saved.sticks[i];
  return p.repeat<=.018&&p.spread<=.06&&p.noise<=prior.noise+.008&&Math.abs(p.rms-prior.rms)<=Math.max(.005,2*Math.hypot(p.repeat,prior.repeat))&&p.center<=prior.center+.01&&p.travel.every((v,j)=>v>=Math.min(.975,prior.travel[j]-.01));
 }));
}
