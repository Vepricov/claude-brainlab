"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = process.env.ATLAS_URL || "http://127.0.0.1:8884/";
const evidence = process.env.ATLAS_EVIDENCE || "/private/tmp/atlas-i18n-evidence";
fs.mkdirSync(evidence,{recursive:true});
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROME_PATH,headless:true});
 const context=await browser.newContext({viewport:{width:1440,height:1000}});
 const page=await context.newPage(), errors=[], violations=[], checked=[];
 page.on("pageerror",error=>errors.push(error.message));
 page.on("request",request=>{
  const url=new URL(request.url());
  if(url.protocol.startsWith("http") && (url.origin!==new URL(base).origin || /\/api\/|8799|8001/.test(url.pathname)))violations.push(request.url());
 });
 async function inspect(label){
  const result=await page.evaluate(()=>{
   const russian=[];
   const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
   let text;
   while((text=walker.nextNode())){
    const element=text.parentElement;
    if(!element||element.closest('script,style,[data-language="ru"]')||!element.checkVisibility())continue;
    const value=text.textContent.replaceAll('Старт','').replaceAll('Получить доступ','').replaceAll('База знаний MCP','');
    if(/[А-Яа-яЁё]/.test(value))russian.push(value.trim().slice(0,180));
   }
   for(const element of document.querySelectorAll('body *')){if(!element.checkVisibility())continue;for(const pseudo of ['::before','::after']){const value=getComputedStyle(element,pseudo).content;if(/[А-Яа-яЁё]/.test(value))russian.push(value)}}
   const attrs=[...document.querySelectorAll('[aria-label],[placeholder],[alt]')].filter(x=>x.checkVisibility()&&!x.matches('[data-language="ru"]')).flatMap(x=>['aria-label','placeholder','alt'].map(a=>x.getAttribute(a)||'')).filter(x=>/[А-Яа-яЁё]/.test(x));
   return {russian:[...new Set([...russian,...attrs])],overflow:document.documentElement.scrollWidth>innerWidth+2};
  });
  assert.deepEqual(result.russian,[],`${label}: untranslated visible text`);
  assert.equal(result.overflow,false,`${label}: horizontal overflow`);
  checked.push(label);
 }
 try{
  await page.goto(base);await page.waitForSelector('.loop-node');
  assert.equal(await page.locator('html').getAttribute('lang'),'en');
  await inspect('English default');
  const routes=await page.evaluate(()=>[...window.RESEARCH_LOOP.processes.map(p=>p.id),'memory','surface/obsidian','surface/mempalace','surface/yonote',...window.SYSTEM_EXAMPLES.journeys.map(j=>`examples/${j.id}/${j.stages[0].id}`)]);
  for(const route of routes){
   await page.goto(`${base}?lang=en#${route}`);await page.waitForSelector('#process-view:not([hidden]),#examples-view:not([hidden])');
   await page.locator('details').evaluateAll(xs=>xs.forEach(x=>x.open=true));await inspect(route);
  }
  await page.goto(`${base}?lang=en#memory`);await page.waitForSelector('[data-record]');
  const records=await page.locator('[data-record]').evaluateAll(xs=>[...new Set(xs.map(x=>x.dataset.record))]);
  for(const record of records){await page.locator(`[data-record="${record}"]`).first().click();await inspect(`record guide ${record}`);await page.keyboard.press('Escape')}
  const tools=await page.evaluate(()=>window.RESEARCH_LOOP.processes.flatMap(p=>p.tools.map(t=>`${p.id}/${t.id}`)));
  for(const route of tools){
   await page.goto(`${base}?lang=en#${route}`);await page.waitForSelector('.skill-dialog[open]');
   await page.locator('dialog[open] details').evaluateAll(xs=>xs.forEach(x=>x.open=true));await inspect(route);
  }
  await page.goto(`${base}?lang=en#mcp-live`);await page.waitForSelector('#mcp-search-input');await inspect('demo landing');
  const scenarios=await page.evaluate(()=>window.LAB_DEMO.scenarios);
  for(const scenario of scenarios){
   await page.locator('#mcp-search-input').fill(scenario.text);await page.locator('#mcp-search-form').evaluate(f=>f.requestSubmit());
   await page.waitForSelector('#mcp-results [data-open-paper]');
   const ids=await page.locator('#mcp-results [data-open-paper]').evaluateAll(xs=>[...new Set(xs.map(x=>x.dataset.openPaper))]);
   assert.deepEqual(ids,[scenario.paper,...scenario.related],scenario.text);await inspect(scenario.text);
  }
  await page.locator('#mcp-results [data-open-paper]').first().click();const paperHash=new URL(page.url()).hash;
  assert.match(paperHash,/^#mcp-live\/paper\//);await inspect('English paper');
  await page.locator('[data-language=ru]').click();await page.waitForSelector('#mcp-results .paper-page');
  assert.equal(new URL(page.url()).hash,paperHash);assert.equal(await page.locator('html').getAttribute('lang'),'ru');
  assert.match(await page.locator('#mcp-results').innerText(),/[А-Яа-яЁё]/);
  await page.locator('[data-language=en]').click();await page.waitForSelector('#mcp-results .paper-page');await inspect('paper after language round trip');
  for(const width of [375,560,640,768,1024,1440]){
   await page.setViewportSize({width,height:900});
   for(const route of ['','literature','memory','surface/obsidian','surface/yonote','mcp-live']){
    await page.goto(`${base}?lang=en#${route}`);await page.waitForSelector(route==='mcp-live'?'#mcp-search-input':route?'#process-view:not([hidden])':'.loop-node');await inspect(`${width}px ${route||'home'}`);
    const bounds=await page.locator('.topbar').evaluate(header=>{const h=header.getBoundingClientRect();return [...header.children].filter(x=>x.checkVisibility()).every(x=>{const b=x.getBoundingClientRect();return b.top>=h.top&&b.bottom<=h.bottom+1})});
    assert(bounds,`${width}px header contains every control`);
   }
   await page.goto(`${base}?lang=en`);await page.waitForSelector('.loop-node');await page.screenshot({path:path.join(evidence,`home-${width}.png`)});
  }
  // No preference store is needed to keep Russian internal links in Russian.
  const isolated=await browser.newContext();await isolated.addInitScript(()=>{Object.defineProperty(window,'localStorage',{get(){throw new Error('Storage unavailable')}})});
  const ruPage=await isolated.newPage();await ruPage.goto(`${base}ru/index.html?lang=ru#surface/mempalace`);await ruPage.waitForSelector('.sp-footer');
  await ruPage.locator('.sp-footer a[href="#memory"]').click();await ruPage.waitForSelector('.memory-observatory');
  assert.equal(await ruPage.locator('html').getAttribute('lang'),'ru');assert.match(ruPage.url(),/\/ru\/index.html\?lang=ru#memory$/);await isolated.close();
  // Saved choice and explicit query override work independently of browser language.
  await page.locator('[data-language=ru]').click();await page.waitForURL(/\/ru\//);await page.goto(base);await page.waitForURL(/\/ru\//);
  await page.goto(`${base}?lang=en`);await page.waitForSelector('.loop-node');assert.equal(await page.locator('html').getAttribute('lang'),'en');
  assert.deepEqual(errors,[],'JavaScript errors');assert.deepEqual(violations,[],'No private API or external resource requests');
  fs.writeFileSync(path.join(evidence,'browser-results.json'),JSON.stringify({checked,errors,violations},null,2));
  console.log(`PASS: ${checked.length} English pages/cards, language round trips, responsive layouts, no private requests`);
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exitCode=1});
