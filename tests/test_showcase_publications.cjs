"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "..");
const data = path.join(root, "docs/lab-showcase/data");
const search = require(path.join(root, "docs/lab-showcase/search-core.js"));
const ctx = { window: {} };
for (const name of ["library-snapshot", "base-snapshot", "atlas-tree", "demo-flag"])
  vm.runInNewContext(fs.readFileSync(path.join(data, `${name}.js`), "utf8"), ctx);
const lib = ctx.window.LAB_LIBRARY;
const index = search.build({ lib, base: ctx.window.LAB_BASE, tree: ctx.window.LAB_TREE });
const manifest = JSON.parse(fs.readFileSync(path.join(data, "publications.json"), "utf8"));
for (const paper of [...manifest.papers, ...manifest.references]) {
  const hits = index.search(paper.title).filter(hit => hit.kind === "paper");
  assert.equal(hits[0]?.id, paper.id, paper.title);
}

// Exercise the actual excerpt selector: a question about the method must not
// receive the longest (unrelated) benchmark statement from the same paper.
const app = fs.readFileSync(path.join(root, "docs/lab-showcase/app.js"), "utf8");
const start = app.indexOf("  function paperClaim(");
const end = app.indexOf("\n  }", start) + 4;
assert(start >= 0 && end > start);
const select = vm.runInNewContext(`(${app.slice(start, end).trim()})`, {
  window: { LabSearch: search },
});
const rankedStart = app.indexOf("  function snapshotRanked(");
const rankedEnd = app.indexOf("\n  }", rankedStart) + 4;
const ranked = vm.runInNewContext(`(${app.slice(rankedStart, rankedEnd).trim()})`, {
  Set,
  searchIndex: index,
  NODE_KINDS: search.NODE_KINDS,
  byCode: Object.fromEntries(ctx.window.LAB_BASE.records.map(r => [r.code, r])),
  papersById: Object.fromEntries(lib.papers.map(p => [p.id, p])),
  paperClaim: select,
});
function appFunction(name, sandbox) {
  const start = app.indexOf(`  function ${name}(`);
  const end = app.indexOf("\n  }", start) + 4;
  assert(start >= 0 && end > start);
  return vm.runInNewContext(`(${app.slice(start, end).trim()})`, sandbox);
}
const scenario = appFunction("demoScenario", { demo: ctx.window.LAB_DEMO });
const scenarioItems = appFunction("scenarioItems", {
  papersById: Object.fromEntries(lib.papers.map(p => [p.id, p])), paperClaim: select,
});
const snapshot = appFunction("snapshotItems", {
  demoScenario: scenario, scenarioItems, searchIndex: index, snapshotRanked: ranked,
});
for (const question of manifest.questions) {
  assert(!/[a-z]/i.test(question.text), `General question: ${question.text}`);
  const q = `  ${question.text.toUpperCase().replaceAll(" ", "  ")}?  `;
  const items = snapshot(q);
  assert.deepEqual(Array.from(items.filter(x => x.entity_type === "paper"), x => x.entity_id),
    [question.paper, ...question.related], question.text);
  assert.equal(items[0].extra.demo_featured, true);
  assert(items.every(x => ["paper", "paper_claim"].includes(x.entity_type)), "No invented project records");
  assert(items.filter(x => x.extra.demo_featured).every(x => x.entity_id === question.paper));
  assert(items.some(x => x.entity_id.startsWith("ref")), "Other authors are included");
}
assert.equal(scenario("unrelated query"), undefined);
const arbitrary = "What is stochastic tensor optimization?";
assert.deepEqual(snapshot(arbitrary), ranked(arbitrary), "Ordinary search keeps index ranking");
const liveScenario = appFunction("demoScenario", { demo: null });
assert.equal(liveScenario(manifest.questions[0].text), undefined, "No curated live MCP results");
const weight = lib.papers.find(p => p.id === "pub00014");
assert.match(select(weight, "как выбирать адаптеры WeightLoRA").s, /выбират|выбор|выбира|отбор/);
const fisher = lib.papers.find(p => p.id === "pub00009");
assert.match(select(fisher, "как DyKAF приближает матрицу Фишера").s, /Фишера/);
console.log(`PASS: ${manifest.questions.length} examples, ${manifest.papers.length} titles, relevant excerpts`);
