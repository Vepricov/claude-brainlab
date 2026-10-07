"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.join(__dirname, "../docs/lab-showcase");
function load(locale) {
  const prefix = locale === "en" ? "en/" : "";
  const context = {window:{}};
  for (const file of ["research-loop-data", "atlas-public", "system-examples", "base-snapshot", "library-snapshot", "atlas-tree", "demo-flag"])
    vm.runInNewContext(fs.readFileSync(path.join(root, prefix, `data/${file}.js`), "utf8"), context);
  return JSON.parse(JSON.stringify(context.window));
}
const ru=load("ru"), en=load("en");
// Machine identifiers, source links and scientific numbers must survive localization.
function compare(a,b,at="root") {
  assert.equal(typeof b,typeof a,at);
  if(Array.isArray(a)) {assert.equal(b.length,a.length,at);a.forEach((v,i)=>compare(v,b[i],`${at}/${i}`));return}
  if(a&&typeof a==="object") {
    assert.deepEqual(Object.keys(b).sort(),Object.keys(a).sort(),at);
    for(const key of Object.keys(a)) compare(a[key],b[key],`${at}/${key}`);
    return;
  }
  if(typeof a!=="string"||!/[А-Яа-яЁё]/.test(a)) {
    if(at.endsWith("/src")&&a.startsWith("assets/slides/")) assert.equal(b,a.replace("assets/slides/","assets/slides/en/"),at);
    else assert.equal(b,a,at);
  }
}
// Object keys in UI modules may be display labels; structural data keys are stable.
for(const name of ["RESEARCH_LOOP","LAB_ATLAS_DATA","LAB_BASE","LAB_LIBRARY","LAB_TREE","LAB_DEMO"]) compare(ru[name],en[name],name);
assert.equal(en.LAB_LIBRARY.papers.length,50);
assert.equal(en.LAB_LIBRARY.papers.reduce((n,p)=>n+p.c.length,0),161);
const papers=new Map(en.LAB_LIBRARY.papers.map(p=>[p.id,p]));
assert.deepEqual(en.LAB_DEMO.hints,en.LAB_DEMO.scenarios.map(x=>x.text));
for(const scenario of en.LAB_DEMO.scenarios) {
  assert.equal(papers.get(scenario.paper).origin,"author-publication");
  assert.equal(scenario.related.length,2);
  for(const id of scenario.related)assert(papers.has(id));
}
assert.equal(en.LAB_LIBRARY.papers.filter(p=>p.f===en.LAB_DEMO.publication_folder).length,22);
for(const paper of en.LAB_LIBRARY.papers)assert(en.LAB_TREE.folders.some(f=>f.path===paper.f||f.name===paper.f||f.f===paper.f)||JSON.stringify(en.LAB_TREE).includes(JSON.stringify(paper.f)),`Unbound folder: ${paper.f}`);
const search=require(path.join(root,"en/search-core.js"));
const index=search.build({lib:en.LAB_LIBRARY,base:en.LAB_BASE,tree:en.LAB_TREE});
for(const paper of en.LAB_LIBRARY.papers) {
  const hits=index.search(paper.t).filter(x=>x.kind==="paper");
  assert.equal(hits[0]?.id,paper.id,paper.t);
}
console.log("PASS: both locales preserve IDs, sources, 50 papers, 161 claims, and search links");
