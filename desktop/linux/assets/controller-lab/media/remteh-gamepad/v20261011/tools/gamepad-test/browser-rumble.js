// Browser Gamepad API adapter. The caller invalidates `current` before reset,
// so cancelling a pulse sequence cannot queue another motor command.
export async function browserRumble(actuator,{strength=40,side='both',pattern='steady'}={},current=()=>true,wait=ms=>new Promise(resolve=>setTimeout(resolve,ms))){
  if(!['steady','pulse','alternate','ramp'].includes(pattern)||!['left','right','both'].includes(side))throw new Error('feature_unavailable');
  const magnitude=Math.max(.1,Math.min(.8,(Number(strength)||40)/100));
  const levels=pattern==='ramp'?[.25,.5,.75,1,1,.75,.5,.25]:Array(pattern==='pulse'?3:pattern==='alternate'?6:1).fill(1);
  const duration=pattern==='pulse'?180:pattern==='alternate'?250:pattern==='ramp'?200:800;
  for(let i=0;i<levels.length;i++){
    if(!current())return {completed:false};
    const activeSide=pattern==='alternate'?(i%2?'right':'left'):side,value=magnitude*levels[i];
    const result=await actuator.playEffect('dual-rumble',{duration,startDelay:0,strongMagnitude:activeSide==='right'?0:value,weakMagnitude:activeSide==='left'?0:value});
    if(!current()||result==='preempted')return {completed:false};
    if(result!=='complete')throw new Error('effect_failed');
    if(pattern==='pulse'&&i<levels.length-1)await wait(120);
  }
  return {completed:true};
}
