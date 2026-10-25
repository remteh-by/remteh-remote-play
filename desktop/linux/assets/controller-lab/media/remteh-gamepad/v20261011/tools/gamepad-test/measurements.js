// Browser-neutral measurement functions. Input values are never rounded or deadzoned.
export const round = (n, digits=3) => Number(n.toFixed(digits));
export function restStats(samples) {
  if (samples.length < 30 || samples.some(a => a.length < 4 || a.slice(0,4).some(v => !Number.isFinite(v)))) return null;
  const axes = Array.from({length:4}, (_,i) => {
    const mean = samples.reduce((s,a) => s+a[i],0)/samples.length;
    return {mean, noise:Math.sqrt(samples.reduce((s,a)=>s+(a[i]-mean)**2,0)/samples.length), peak:Math.max(...samples.map(a=>Math.abs(a[i])))};
  });
  const sticks = [0,2].map(i=>({offset:Math.hypot(axes[i].mean,axes[i+1].mean), noise:Math.hypot(axes[i].noise,axes[i+1].noise), peak:Math.max(...samples.map(a=>Math.hypot(a[i],a[i+1])))}));
  return {axes, sticks, count:samples.length};
}
export class CircleTrace {
  constructor(){this.bins=[Array(72).fill(0),Array(72).fill(0)];this.lastAngles=[null,null];this.lapTravel=[0,0];this.laps=[0,0];this.samples=0;}
  add(axes) {
    this.samples++;
    for(let i=0;i<2;i++) {
      const x=axes[i*2],y=axes[i*2+1],r=Math.hypot(x,y);
      if(!Number.isFinite(r)||r<.8){this.lastAngles[i]=null;this.lapTravel[i]=0;}
      if(!Number.isFinite(r)||r<.5) continue;
      const angle=Math.atan2(y,x),k=Math.floor((angle+Math.PI)/(Math.PI*2)*72)%72;
      this.bins[i][k]=Math.max(this.bins[i][k],r);
      if(r>=.8){
        const previous=this.lastAngles[i];this.lastAngles[i]=angle;
        if(previous===null)continue;
        // Count actual continuous turns, not visits to all 72 measurement bins.
        // Sparse reports may skip bins even during a complete, smooth rotation.
        const delta=Math.atan2(Math.sin(angle-previous),Math.cos(angle-previous));
        if(Math.abs(delta)>Math.PI/4+1e-6){this.lapTravel[i]=0;continue;}
        this.lapTravel[i]+=delta;
        if(Math.abs(this.lapTravel[i])>=Math.PI*2-1e-6){this.laps[i]++;this.lapTravel[i]-=Math.sign(this.lapTravel[i])*Math.PI*2;}
      }
    }
  }
  // Radial RMS error, matching the definition used by DualShock Tools.
  get results(){return this.bins.map(b=>{const a=b.filter(Boolean);const coverage=a.length/72*100;return {coverage, complete:coverage>=95, error:coverage>=95?Math.sqrt(a.reduce((s,r)=>s+(1-r)**2,0)/a.length)*100:null};});}
}
export function verdict(rest, circle, thresholds) {
  if(!rest) return {status:'info', key:'gp_incomplete'};
  const drift=Math.max(...rest.sticks.map(s=>s.offset)), noise=Math.max(...rest.sticks.map(s=>s.noise));
  if(noise>thresholds.noise_fail) return {status:'fail',key:'gp_noise_fail'};
  if(drift>thresholds.center_offset_fail) return {status:'fail',key:'gp_drift_fail'};
  if(noise>thresholds.noise_warn) return {status:'warn',key:'gp_noise_warn'};
  if(drift>thresholds.center_offset_warn) return {status:'warn',key:'gp_drift_warn'};
  if(!circle?.results.every(r=>r.complete)) return {status:'info',key:'gp_circle_pending'};
  if(circle.results.some(r=>r.error>thresholds.circularity_warn)) return {status:'warn',key:'gp_circle_warn'};
  return {status:'pass',key:'gp_sticks_ok'};
}
export function flatten(rest,circle,prefix) {
  const m={};if(rest){m[prefix+'samples']=rest.count;rest.axes.forEach((a,i)=>{m[prefix+['lx','ly','rx','ry'][i]+'_mean']=round(a.mean,5);m[prefix+['lx','ly','rx','ry'][i]+'_noise']=round(a.noise,5);});rest.sticks.forEach((s,i)=>{for(const key of ['offset','noise','peak'])m[prefix+(i?'right_':'left_')+key+'_pct']=round(s[key]*100);});}
  if(circle){m[prefix+'circle_error_method']='radial_rms_72_v1';} // Distinguish new reports from historical mean-absolute values.
  if(circle)circle.results.forEach((s,i)=>{m[prefix+(i?'right_':'left_')+'coverage_pct']=round(s.coverage,1);if(s.error!==null)m[prefix+(i?'right_':'left_')+'circle_error_pct']=round(s.error,2);});
  return m;
}
