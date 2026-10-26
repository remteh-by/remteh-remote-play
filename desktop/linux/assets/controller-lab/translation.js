export function createTranslator(phrases) {
 const dictionary=new Map(Object.entries(phrases));
 const keys=[...dictionary.keys()].filter(Boolean).sort((a,b)=>b.length-a.length);
 const escape=key=>[...key].map(c=>'\\^$.*+?()[]{}|'.includes(c)?String.fromCharCode(92)+c:c).join('');
 const fragments=new RegExp('(?<![А-Яа-яЁё])(?:'+keys.map(escape).join('|')+')(?![А-Яа-яЁё])','gu');
 return value=>{
  if(!/[А-Яа-яЁё]/u.test(value))return value;
  const trimmed=value.trim();
  if(dictionary.has(trimmed))return value.replace(trimmed,dictionary.get(trimmed));
  return value.replace(fragments,match=>dictionary.get(match));
 };
}
export function translateTree(root,translate) {
 if(!root?.nodeType)return;
 const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);let node;
 while((node=walker.nextNode())) {
  if(/^(SCRIPT|STYLE)$/.test(node.parentElement?.tagName)||node.parentElement?.closest('#language'))continue;
  const value=translate(node.nodeValue);if(value!==node.nodeValue)node.nodeValue=value;
 }
 for(const element of [...(root.matches?.('[title],[aria-label],[placeholder],[alt]')?[root]:[]),...(root.querySelectorAll?.('[title],[aria-label],[placeholder],[alt]')??[])]) {
  for(const key of ['title','aria-label','placeholder','alt']) {
   const value=element.getAttribute(key);if(value!==null){const next=translate(value);if(next!==value)element.setAttribute(key,next);}
  }
 }
}
