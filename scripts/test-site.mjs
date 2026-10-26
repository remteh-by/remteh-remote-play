import {chromium} from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import assert from 'node:assert/strict';
import os from 'node:os';
const root=path.resolve('build/site'),output=process.env.DECKIVO_QA_DIR??path.join(os.tmpdir(),'deckivo-site-qa');
fs.mkdirSync(output,{recursive:true});
let server,base=process.env.DECKIVO_SITE_BASE;
if(!base) {
 server=http.createServer((req,res)=>{
  const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
  let file=path.resolve(root,'.'+pathname);if(pathname.endsWith('/'))file=path.join(file,'index.html');
  if(!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
  const types={'.html':'text/html','.css':'text/css','.js':'text/javascript','.json':'application/json','.jpg':'image/jpeg','.webp':'image/webp','.avif':'image/avif','.svg':'image/svg+xml','.woff2':'font/woff2','.md':'text/markdown'};
  try{res.writeHead(200,{'Content-Type':types[path.extname(file)]??'application/octet-stream'}).end(fs.readFileSync(file));}catch{res.writeHead(404).end();}
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));base='http://127.0.0.1:'+server.address().port+'/';
}
if(!base.endsWith('/'))base+='/';
const languages=process.env.DECKIVO_QA_LANGS?.split(',')??['en','ru','uk','pl','de','fr','es','it','pt','tr','zh','ja','ko','ar','hi','id'];
const executable=process.env.DECKIVO_CHROME??(process.platform==='darwin'?'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome':undefined);
const browser=await chromium.launch({headless:true,...(executable?{executablePath:executable}:{})});
const evidence=[];
const statistics=await (await fetch(base+'download-stats.json')).json();
const threshold=JSON.parse(fs.readFileSync('design-system/site.json','utf8')).site.downloads.public_min_packages;
const expectedStats=Number.isInteger(statistics.package_total)&&statistics.package_total>=threshold?1:0;
const support=JSON.parse(fs.readFileSync('website/support.json','utf8'));
const expectedProgress=support.goals.filter(g=>g.target_usd!==null&&g.raised_usd!==null&&g.target_usd>0).length;
try {
 for(const width of [360,390,414,1440,1920,2560,3840]) {
  const context=await browser.newContext({viewport:{width,height:1000}});
  for(const lang of languages) {
   const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
   const response=await page.goto(base+(lang==='en'?'':lang+'/'));assert.equal(response.status(),200);
   await page.evaluate(()=>document.fonts.ready);
   const state=await page.evaluate(()=>{
    const typed=[];for(const s of document.querySelectorAll('script[type="application/ld+json"]')){const json=JSON.parse(s.textContent);typed.push(...(Array.isArray(json)?json:json['@graph']??[json]));}
    const splitWords=[];
    for(const button of document.querySelectorAll('.install-paths .button')){
     const walker=document.createTreeWalker(button,NodeFilter.SHOW_TEXT);let node;
     while((node=walker.nextNode()))for(const match of node.textContent.matchAll(/[\p{L}\p{N}]+/gu)){
      const range=document.createRange();range.setStart(node,match.index);range.setEnd(node,match.index+match[0].length);
      const lines=new Set([...range.getClientRects()].filter(r=>r.width&&r.height).map(r=>Math.round(r.top)));
      if(lines.size>1)splitWords.push(match[0]);
     }
    }
    const meta=key=>document.querySelector('meta[property="'+key+'"],meta[name="'+key+'"]')?.content;
    const clips=[...document.body.querySelectorAll('*')].filter(el=>{
     const r=el.getBoundingClientRect(),style=getComputedStyle(el);
     return r.width>0&&r.height>0&&r.bottom>0&&r.top<innerHeight&&style.visibility!=='hidden'&&style.display!=='none'&&(r.left<-.75||r.right>innerWidth+.75);
    }).map(el=>el.tagName+'.'+el.className).slice(0,12);
    return {lang:document.documentElement.lang,h1:document.querySelector('h1')?.textContent,
      app:typed.filter(x=>x['@type']==='SoftwareApplication'),faq:typed.filter(x=>x['@type']==='FAQPage'),
      og:{image:meta('og:image'),width:meta('og:image:width'),height:meta('og:image:height'),type:meta('og:image:type'),twitter:meta('twitter:image')},
      downloads:[...document.querySelectorAll('a.package-link')].map(a=>a.href),
      stats:document.querySelectorAll('#download-stats').length,unknownBars:document.querySelectorAll('#support progress').length,
      splitWords,clipped:clips,scrollWidth:document.documentElement.scrollWidth,viewport:innerWidth,
      languageLinks:document.querySelectorAll('.language-menu a').length};
   });
   assert.equal(state.lang,lang);assert.ok(state.h1?.trim());assert.equal(state.app.length,1);assert.equal(state.faq.length,1);
   assert.equal(state.app[0].softwareVersion,'0.8.4');assert.ok(state.faq[0].mainEntity.length>=5);
   assert.equal(state.og.width,'1200');assert.equal(state.og.height,'630');assert.equal(state.og.type,'image/jpeg');
   assert.equal(state.og.image,state.og.twitter);assert.match(state.og.image,/^https:\/\/.*\/github-cover\.jpg(?:\?|$)/);
   assert.equal(state.downloads.length,3);assert.ok(state.downloads.every(u=>u.includes('/v0.8.4/')));
   assert.equal(state.stats,expectedStats,'public counters respect the configured threshold');assert.equal(state.unknownBars,expectedProgress);
   assert.deepEqual(state.splitWords,[],lang+' '+width+' split button words');assert.equal(state.languageLinks,16);assert.deepEqual(state.clipped,[]);assert.equal(state.scrollWidth,width);assert.deepEqual(errors,[]);
   evidence.push({lang,width,passed:true,appSchemas:state.app.length,faqSchemas:state.faq.length,clipped:0});
   if(['en','ru'].includes(lang)){await page.screenshot({path:path.join(output,lang+'-'+width+'.png')});if(width<=414)await page.locator('.device-chooser').screenshot({path:path.join(output,lang+'-'+width+'-downloads.png')});}
   await page.close();
  }
  await context.close();
 }
 const context=await browser.newContext({javaScriptEnabled:false,viewport:{width:1440,height:1000}});
 for(const lang of languages) {
  const page=await context.newPage();await page.goto(base+(lang==='en'?'':lang+'/'));
  assert.equal(await page.locator('a.package-link').count(),3);
  assert.equal(await page.locator('.language-menu a').count(),16);
  assert.equal(await page.locator('script[type="application/ld+json"]').count(),1);
  await page.close();
 }
 const page=await context.newPage();
 const jpg=await page.request.get(base+'assets/github-cover.jpg');assert.equal(jpg.status(),200);assert.match(jpg.headers()['content-type'],/image\/jpeg/);
 const docs=await page.request.get(base+'docs/DOWNLOADS.md');assert.equal(docs.status(),200);assert.match(await docs.text(),/not unique people or installations/);
 await context.close();fs.writeFileSync(path.join(output,'site-results.json'),JSON.stringify({base,cases:evidence,noJS:languages.length,jpegHTTP:200,downloadDocsHTTP:200},null,2)+'\n');
 console.log('Site PASS:',evidence.length,'rendered cases,',languages.length,'no-JS pages, JSON-LD/JPEG/funding/stats checks');
} finally {await browser.close();if(server)await new Promise(resolve=>server.close(resolve));}
