/* No registration data or analytics. English is the first-visit default. */
(() => {
  const names={en:'English',ru:'Русский',uk:'Українська',pl:'Polski',de:'Deutsch',fr:'Français',es:'Español',it:'Italiano',pt:'Português',tr:'Türkçe',zh:'简体中文',ja:'日本語',ko:'한국어',ar:'العربية',hi:'हिन्दी',id:'Bahasa Indonesia'};
  const picker=document.getElementById('language');
  const saved=()=>{try{return localStorage.getItem('deckivo.language')||'en'}catch{return'en'}};
  function apply(choice){
    const lang=DeckivoLanguagePolicy.resolve(choice,navigator.languages||[navigator.language]);
    const copy={...DeckivoContent.en,...DeckivoContent[lang]};
    document.documentElement.lang=lang;document.documentElement.dir=lang==='ar'?'rtl':'ltr';
    picker.value=(choice==='auto'||names[choice])?choice:'en';
    for(const item of document.querySelectorAll('[data-i]'))if(copy[item.dataset.i])item.textContent=copy[item.dataset.i];
    for(const item of document.querySelectorAll('.guide-link'))item.href=`https://github.com/remteh-by/remteh-remote-play/blob/main/docs/guides/${lang}.md${item.dataset.anchor?'#'+item.dataset.anchor:''}`;
    for(const item of document.querySelectorAll('#language-links a'))item.classList.toggle('selected',item.lang===lang);
  }
  const links=document.getElementById('language-links');
  for(const [code,name] of Object.entries(names)){const a=document.createElement('a');a.href=`https://github.com/remteh-by/remteh-remote-play/blob/main/docs/guides/${code}.md`;a.lang=code;a.hreflang=code;a.textContent=name;links.append(a)}
  picker.addEventListener('change',()=>{try{localStorage.setItem('deckivo.language',picker.value)}catch{}apply(picker.value)});
  window.addEventListener('languagechange',()=>{if(saved()==='auto')apply('auto')});apply(saved());
})();
