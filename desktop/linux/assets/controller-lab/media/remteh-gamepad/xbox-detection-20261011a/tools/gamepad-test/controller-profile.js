// Model identity is independent from the capabilities exposed by the browser.
const standardKeys=['cross','circle','square','triangle','l1','r1','l2','r2','create','options','l3','r3','up','down','left','right','ps'];
const sonyLabels={cross:'✕',circle:'○',square:'□',triangle:'△',l1:'L1',r1:'R1',l2:'L2',r2:'R2',l3:'L3',r3:'R3',up:'↑',down:'↓',left:'←',right:'→',create:'Share / Create',options:'Options',ps:'PS',touchpad:'Тачпад',mute:'Mute',fn_left:'Fn L',fn_right:'Fn R',paddle_left:'Paddle L',paddle_right:'Paddle R'};
const xboxLabels={...sonyLabels,cross:'A',circle:'B',square:'X',triangle:'Y',l1:'LB',r1:'RB',l2:'LT',r2:'RT',l3:'LS',r3:'RS',create:'View',options:'Menu',ps:'Xbox',share:'Share'};
const genericLabels={...sonyLabels,cross:'A / ✕',circle:'B / ○',square:'X / □',triangle:'Y / △',l1:'LB / L1',r1:'RB / R1',l2:'LT / L2',r2:'RT / R2',create:'Back',options:'Start',ps:'Home'};

export function getControllerProfile(source,frame){
  const name=String(source?.model||source?.name||frame?.gamepad?.id||'');
  const lower=name.toLowerCase();
  let id='generic',family='generic',label='Геймпад';
  const microsoft=/\b(?:0x)?0?45e\b|\bmicrosoft\b/i.test(name);
  if(!source){id='none';family='none';label='Геймпад не подключён';}
  else if(/dualsense|\bds5(?:_edge)?\b|\b054c\b.*\b(?:0ce6|0df2)\b/i.test(name)){
    id='dualsense';family='sony';label=/edge|0df2/i.test(name)?'DualSense Edge':'DualSense';
  }else if(/dualshock|\bds4\b|\b054c\b.*\b(?:05c4|09cc)\b/i.test(name)){
    id='ds4';family='sony';label='DualShock 4';
  }else if((microsoft&&/\b(?:0x)?0?b1[23]\b/i.test(name))||/xbox\s*series|xboxseriesx/i.test(name)){
    id='xbox-series';family='xbox';label='Xbox Series';
  }else if(/xbox\s*one/i.test(name)){
    id='xbox-one';family='xbox';label='Xbox One';
  }else if(/xbox|xinput/i.test(lower)||(microsoft&&/\b(?:02d1|02dd|02e0|02e3|02ea|02fd|0b00|0b05|0b20|0b21|0b22)\b/i.test(name))){
    id='xbox';family='xbox';label='Xbox / XInput';
  }
  // Anonymous macOS Gamepad API names carry no reliable manufacturer identity.
  // A user's choice changes presentation/mapping, never hardware capabilities.
  const canChooseModel=source?.kind==='gamepad'&&source.standard===true&&
    (id==='generic'||id==='xbox'&&!/360|elite|adaptive/i.test(name));
  const choices={'xbox-series':['xbox','Xbox Series'],'xbox-one':['xbox','Xbox One'],dualsense:['sony','DualSense'],ds4:['sony','DualShock 4']};
  const manual=Boolean(canChooseModel&&Object.hasOwn(choices,source?.userModel??''));
  if(manual){id=source.userModel;[family,label]=choices[id];}
  return {id,family,label,canChooseModel,identityOrigin:manual?'manual':'browser',isXbox:family==='xbox',sonyHid:family==='sony'&&source?.kind==='hid',standard:source?.standard===true};
}

export function standardButtonKey(index,profile){
  const n=Number(index);
  if(!Number.isInteger(n)||n<0)return String(index);
  if(n<standardKeys.length)return standardKeys[n];
  // Extra buttons are outside the W3C standard mapping. Share is not a touchpad.
  if(n===17&&profile?.id==='xbox-series')return 'share';
  if(n===17&&profile?.family==='sony')return 'touchpad';
  return 'b'+n;
}

export function buttonLabel(key,profile){
  const labels=profile?.isXbox?xboxLabels:profile?.family==='sony'?sonyLabels:genericLabels;
  return labels[key]??(/^b\d+$/.test(String(key))?'B'+String(key).slice(1):String(key));
}
