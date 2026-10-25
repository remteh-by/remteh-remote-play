const number=(value,fallback)=>Number.isFinite(Number(value))?Number(value):fallback;
const clamp=(value,min,max,fallback)=>Math.min(max,Math.max(min,number(value,fallback)));
const oneOf=(value,allowed,fallback)=>allowed.includes(value)?value:fallback;

export function adaptiveOptions(values={}){
 return {
  mode:oneOf(values.mode,['resistance','single','machinegun'],'resistance'),
  side:oneOf(values.side,['left','right','both'],'both'),
  strength:clamp(values.strength,10,80,40),
  start:clamp(Math.round(number(values.start,30)/10)*10,20,70,30),
  frequency:clamp(values.frequency,1,30,12),
  duration:clamp(values.duration,1000,8000,5000),
 };
}

export function lightOptions(values={}){
 const color=/^#[0-9a-f]{6}$/i.test(values.color??'')?String(values.color).toLowerCase():'#0066ff';
 return {
  mode:oneOf(values.mode,['color','rgb','player','mute'],'color'),
  color,
  brightness:clamp(values.brightness,10,100,50),
  duration:clamp(values.duration,100,8000,1500),
 };
}

export function rumbleOptions(values={}){
 return {
  pattern:oneOf(values.pattern,['steady','pulse','alternate','ramp'],'steady'),
  side:oneOf(values.side,['left','right','both'],'both'),
  strength:clamp(values.strength,10,80,40),
 };
}

export function progressState(start,duration,now){
 const safeDuration=Math.max(1,number(duration,1)),elapsed=Math.max(0,number(now,start)-number(start,0));
 return {percent:Math.min(100,elapsed/safeDuration*100),remainingMs:Math.max(0,safeDuration-elapsed)};
}
