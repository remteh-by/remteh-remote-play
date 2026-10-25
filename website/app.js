/* Progressive enhancement only: every language and support link works without JS. */
(() => {
  const c=JSON.parse(document.getElementById('page-config').textContent);
  function suggest() {
    const lang=(navigator.languages||[navigator.language]).map(x=>x.toLowerCase().split('-')[0]).find(x=>c.languages[x]);
    if(!lang||lang===c.lang||document.querySelector('.language-suggestion'))return;
    const box=document.createElement('aside');box.className='language-suggestion wrap';
    const a=document.createElement('a');a.href=c.prefix+(lang==='en'?'':lang+'/')||'./';a.lang=lang;a.textContent=c.languages[lang]+' →';
    const close=document.createElement('button');close.type='button';close.textContent='×';close.setAttribute('aria-label','Close');close.onclick=()=>box.remove();box.append(a,close);
    document.querySelector('header').after(box);
  }
  document.getElementById('auto-lang')?.addEventListener('click',suggest);
  // A suggestion never redirects or replaces the server-rendered language.
  suggest();
  if(!c.counter)return;
  const script=document.createElement('script');script.src='https://gc.zgo.at/count.js';script.async=true;
  script.dataset.goatcounter='https://'+c.counter+'.goatcounter.com/count';script.dataset.goatcounterSettings=JSON.stringify({no_onload:true});
  const send=(path,event=false)=>window.goatcounter?.count({path,title:document.title,referrer:'',event});
  script.onload=()=>send(location.pathname);
  document.addEventListener('click',e=>{const a=e.target.closest('[data-event]');if(a)send(a.dataset.event,true)});
  document.head.append(script);
})();
