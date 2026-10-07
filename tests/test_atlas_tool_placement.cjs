'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const site = path.join(__dirname, '../docs/lab-showcase');
for (const prefix of ['', 'en/']) {
  const context = {window:{}};
  for (const file of ['research-loop-data', 'system-examples', 'atlas-public'])
    vm.runInNewContext(fs.readFileSync(path.join(site, prefix, 'data', file + '.js'), 'utf8'), context);
  const model = context.window.RESEARCH_LOOP;
  const chapters = new Map([...model.processes, model.shared].map(p => [p.id, p]));
  const all = [...model.processes, model.shared];
  const tools = new Set(all.flatMap(p => p.tools.map(t => t.id)));
  const skills = new Set(all.flatMap(p => p.tools.map(t => t.skillId).filter(Boolean)));
  const installed = fs.readdirSync(path.join(__dirname, '../skills'))
    .filter(name => fs.existsSync(path.join(__dirname, '../skills', name, 'SKILL.md')));
  const privateSkills = new Set(['lab-knowledge', 'lab-project-onboarding']);
  assert.equal(model.meta.skillCatalog.publicCount, installed.filter(name => !privateSkills.has(name)).length);
  for (const name of installed) assert(skills.has(name), `Missing skill: ${name}`);
  assert(!skills.has('new-paper'));
  assert(!context.window.LAB_ATLAS_DATA.capabilities.some(c => c.id === 'skill:new-paper'));
  for (const p of all) {
    const own = new Set(p.tools.map(t => t.id)), c = p.constellation;
    const cores = c.cores ? c.cores.map(x => x.toolId) : [c.core];
    const placed = [...cores, ...c.groups.flatMap(g => g.toolIds)];
    assert.equal(placed.length, new Set(placed).size, `Duplicate star in ${p.id}`);
    assert.deepEqual(new Set(placed), own, `Unplaced tool in ${p.id}`);
    for (const group of c.groups) {
      if (!group.independent) assert(cores.includes(group.core || c.core), `Missing parent in ${p.id}`);
      if (group.externalFrom) assert(own.has(group.externalFrom));
    }
    for (const tool of p.tools) {
      for (const link of tool.relations || []) assert(tools.has(link.toolId), `Broken relation: ${link.toolId}`);
      for (const link of tool.processRelations || []) {
        const dest = chapters.get(link.processId);
        assert(dest && dest.tools.some(t => t.id === tool.id), `Wrong chapter for ${tool.id}`);
      }
    }
  }
  function checkRoutes(value) {
    if (Array.isArray(value)) return value.forEach(checkRoutes);
    if (!value || typeof value !== 'object') return;
    if (value.process && value.tool)
      assert(chapters.get(value.process)?.tools.some(t => t.id === value.tool), `Broken scenario: ${value.process}/${value.tool}`);
    Object.values(value).forEach(checkRoutes);
  }
  checkRoutes(context.window.SYSTEM_EXAMPLES);
  const ideas = chapters.get('ideation');
  assert.equal(ideas.constellation.core, 'autoresearch');
  assert(ideas.tools.every(t => !['grill-me','grill-with-docs','new-paper','miro','lab-knowledge-hypothesis','publish-hypothesis'].includes(t.id)));
  assert(!ideas.toMcp);
  const autoresearch = ideas.tools.find(t => t.id === 'autoresearch');
  assert.equal(autoresearch.status, 'in-development');
  assert(autoresearch.links.some(l => l.url.endsWith('/claude-brainlab/tree/main/autoresearch')));
  assert(autoresearch.inside.length >= 4);
  assert(chapters.get('literature').tools.some(t => t.id === 'paper-claim-validator'));
  assert(!chapters.get('writing').tools.some(t => t.id === 'paper-claim-validator'));
  const web = chapters.get('presentation').constellation.groups.find(g => g.toolIds.includes('frontend-design'));
  assert(web.independent);
  assert(web.toolIds.includes('webapp-testing'));
}
console.log('PASS: both locales have complete tool coverage, valid routes, and evidence-based placement');
