/* Explanatory maps only. No connection to personal memory or task services. */
window.LAB_SURFACE_PAGES = (() => {
  const header = (name, label, lead, glyph) => `<header class="sp-hero"><div><span class="sp-label">${label}</span><h1 tabindex="-1">${name}</h1><p>${lead}</p></div><div class="sp-emblem" aria-hidden="true"><i></i><i></i><i></i><span>${glyph}</span></div></header>`;
  const node = (id, label, title, text, extra = '') => `<article class="sp-node ${extra}" data-sp-node="${id}"><span class="sp-label">${label}</span><h3><i class="sp-star" aria-hidden="true"></i>${title}</h3><p>${text}</p></article>`;
  const wires = '<svg class="sp-wires" aria-hidden="true"></svg>';
  const section = (label, title, text) => `<header class="sp-section-head"><div><span class="sp-label">${label}</span><h2>${title}</h2></div><p>${text}</p></header>`;

  function mempalace() {
    return `<div class="sp-page sp-memory" data-surface-page="mempalace">
      ${header('MemPalace', "Context between sessions", "A new conversation.<br>Continue where you left off.", '✧')}
      <section class="sp-memory-map sp-map" data-sp-map data-sp-links='[["session","diary"],["session","fragment"],["session","relation"],["diary","resume"],["fragment","resume"],["relation","resume"]]' aria-label="From a working turn to memory and the next session">
        ${wires}
        ${node('session', "Now", "Working turn", "A conversation, the cause of a bug, or an agreed decision. The agent chooses what will be useful later.", 'sp-session')}
        <div class="sp-memory-channels">
          ${node('diary', "Agent diary", "Brief summary", "What is done, what remains, and where to continue. Each entry has a date and topic.")}
          ${node('fragment', "Project fragments", "Exact context", "The original wording of a decision, command, or code, with its source and the record's author.")}
          ${node('relation', "Knowledge graph", "Relationships and facts", "Who leads the project, what a decision relates to, and when a fact was valid.")}
        </div>
        <article class="sp-resume" data-sp-node="resume"><span class="sp-label">Next session</span><h3>“Where did we leave off?”</h3><p>The agent reads its diary, searches project history, and opens the relevant fragments.</p><div class="sp-resume-result"><i class="sp-star" aria-hidden="true"></i><strong>Context restored</strong><span>Decision · reason · next step</span></div></article>
      </section>
      <p class="sp-under-map"><b>The hook reminds the agent to save results.</b> The agent chooses and writes the content. A successful save is verified by reading the record back.</p>
      <section class="sp-section">
        ${section("How the palace is organized", "Every fragment has an address.", "The hierarchy narrows the search: first the project, then an aspect of the work, then the specific source.")}
        <div class="sp-palace-address">
          <article><span class="sp-label">Wing</span><h3>Project</h3><p>The shared context of one project.</p><span class="sp-address-example">example-project</span></article>
          <span class="sp-arrow" aria-hidden="true">→</span>
          <article><span class="sp-label">Room</span><h3>Aspect</h3><p>Decisions, bugs, meetings, or technical details.</p><span class="sp-address-example">decisions</span></article>
          <span class="sp-arrow" aria-hidden="true">→</span>
          <article class="sp-drawer"><span class="sp-label">Drawer · fragment</span><blockquote>“Keep the training budget equal for this comparison.”</blockquote><p>Text + source + date + ID</p></article>
        </div>
        <p class="sp-small">An illustrative example. The diary is stored separately under the agent's name; one agent can work with several projects' memory.</p>
      </section>
      <section class="sp-section">
        ${section("How the agent recalls", "From a question to the original context.", "Search returns saved fragments. The agent reads them and checks them against the current work.")}
        <ol class="sp-recall-path"><li><span>Short query</span><p>Keywords, project, and the relevant topic.</p></li><li><span>Meaning and words</span><p>Vector retrieval finds candidates; word matches refine their order.</p></li><li><span>Original fragment</span><p>Text, its address in memory, and a source link.</p></li><li><span>Check the current state</span><p>Server status, code, and results may have changed.</p></li></ol>
        <div class="sp-memory-foot"><div><h3>Need to resume quickly?</h3><p>Recent diary entries give the immediate next steps. Searching the project helps recover an older decision.</p></div><div><h3>Need to understand a relationship?</h3><p>A graph query finds entity relationships and their history. An old fact's validity period can be closed while preserving its provenance.</p></div></div>
        <details class="sp-fold"><summary>Storage and tools <span>Technical details</span></summary><div class="sp-fold-body"><p>In the verified installation, text and vectors are stored in local Chroma. Search first retrieves semantic candidates; topic summaries can promote related sources, and BM25 refines their order using words. The search tool retrieves stored material without generating new text.</p><p>Typed relationships with validity periods are stored separately in SQLite. Diary entries may use the compact AAAK format; original fragments are saved as ordinary text so they can be read and checked.</p><dl class="sp-api"><dt>Save</dt><dd>mempalace_diary_write · mempalace_add_drawer · mempalace_kg_add</dd><dt>Recall</dt><dd>mempalace_diary_read · mempalace_search · mempalace_get_drawer · mempalace_kg_query</dd></dl></div></details>
      </section>
      <footer class="sp-footer"><p>MemPalace retrieves work history. Shared scientific claims and their supporting grounds are maintained in Lab Knowledge MCP.</p><nav><a href="#memory">Shared knowledge map ↗</a><a href="https://github.com/MemPalace/mempalace" target="_blank" rel="noopener">MemPalace on GitHub ↗</a></nav></footer>
    </div>`;
  }

  function yonote() {
    return `<div class="sp-page sp-team" data-surface-page="yonote">
      ${header('Yonote', "Shared team workspace", "A home for every project.<br>A clear outcome for every task.", '⌘')}
      <section class="sp-team-map sp-map" data-sp-map data-sp-links='[["research","theme"],["theme","area"],["area","project"],["management","delivery"],["delivery","project"]]' aria-label="Research and management sides of a project">
        ${wires}
        ${node('research', "Scientific work", "Research", "What we study and which question we are trying to answer.")}
        ${node('theme', "Within research", "Research topic", "An area that brings related projects together.")}
        ${node('area', "Within a topic", "Subsection", "A narrower area or family of methods.")}
        <article class="sp-project-sheet" data-sp-node="project"><span class="sp-label">Research project</span><h3>Question → result</h3><p>Goal, approach, participants, current status, and links to knowledge.</p><div><b>CODE · Tasks</b><span>One research board</span></div><div><b>CODE · Calls</b><span>Discussion outcomes and agreements</span></div></article>
        ${node('management', "Team commitments", "Management", "Commercial projects, milestones, acceptance, and administrative work.", 'sp-management')}
        <article class="sp-delivery" data-sp-node="delivery"><span class="sp-label">Management page</span><h3>What we deliver and when</h3><p>Client or program, commitments, deadlines, documents, and acceptance criteria.</p><span class="sp-crosslink">Links in both directions to the research project ↗</span></article>
      </section>
      <p class="sp-under-map"><b>Commercial research uses both sides.</b> Scientific work stays in Research, while contractual materials stay in Management. Each project has one research board.</p>
      <section class="sp-section">
        ${section("Inside a project", "From an agreement to a task.", "People can see the expected result, assignee, and progress. Details stay in the task card.")}
        <div class="sp-task-layout"><article class="sp-task-example"><span class="sp-label">Illustrative task</span><h3>Compare two methods<br>at the same budget</h3><dl><dt>Assignee</dt><dd>Project member</dd><dt>Brief</dt><dd>What to compare and which conditions to hold fixed</dd><dt>Done when</dt><dd>A results table and a link to a verified run are available</dd><dt>Result</dt><dd>An artifact, short conclusion, and linked MCP records</dd></dl></article><div class="sp-task-explainer"><h3>Status reflects progress.</h3><ol class="sp-task-path"><li><b>Assigned</b><span>The goal and assignee are clear</span></li><li><b>In progress</b><span>There is progress or a specific obstacle</span></li><li><b>In review</b><span>The result is attached and ready to assess</span></li><li><b>Done</b><span>The completion criterion is met</span></li></ol><p class="sp-small">This illustrates a task's progress. The available statuses and their names come from the project's existing board.</p></div></div>
      </section>
      <section class="sp-section">
        ${section("People and agents", "Work on one board.", "The agent writes to the same project the team opens. The binding is configured in advance using existing IDs.")}
        <div class="sp-team-actors"><article><span class="sp-label">Person</span><h3>Assigns and reviews</h3><p>Defines the result, assigns the work, discusses progress, and accepts the completed task.</p></article><article><span class="sp-label">Authorized agent</span><h3>Prepares and updates</h3><p>Finds the bound board, checks the proposed write, saves the task, and reads the result back. Retrying a call uses the same task key.</p></article><article><span class="sp-label">Hermes</span><h3>Receives an assignment</h3><p>Reads tasks in this project assigned to its owner. It can accept an assignment and add the outcome while keeping the person as assignee. Hermes keeps its personal queue separate; a view is available in Obsidian.</p></article></div>
        <p class="sp-under-map">Hermes checks assignments in its regular work loop. Before making a change, it verifies the assignee and card version; when blocked, it explains what help is needed. Completing a task and assessing a scientific claim in MCP are separate outcomes.</p>
      </section>
      <aside class="sp-common"><span class="sp-label">General information</span><h3>A starting point for everyone.</h3><p>Placement rules, the team directory, and links to shared resources. Research and management pages reference these rules.</p></aside>
      <footer class="sp-footer"><p>Personal tasks stay in Operon. Team work lives on the project's Yonote board. Complete personal drafts stay in Obsidian.</p><nav><a href="https://brain-lab.yonote.ru/" target="_blank" rel="noopener">Open Yonote ↗</a><a href="https://brain-lab.yonote.ru/doc/kak-ustroen-yonote-proekty-zadachi-i-fajly-nBdlvLwAXi" target="_blank" rel="noopener">Laboratory rules ↗</a></nav><small>Yonote links require membership and access to the workspace.</small></footer>
    </div>`;
  }

  let observer;
  let frame;
  function disconnect() { observer?.disconnect(); observer = null; cancelAnimationFrame(frame); }
  function bind(root) {
    disconnect();
    const draw = () => {
      if (!root.isConnected || root.closest('[hidden]')) return;
      root.querySelectorAll('[data-sp-map]').forEach(map => {
        const svg = map.querySelector('.sp-wires');
        if (!svg) return;
        const box = map.getBoundingClientRect();
        svg.setAttribute('viewBox', `0 0 ${box.width} ${box.height}`);
        svg.replaceChildren();
        for (const [from, to] of JSON.parse(map.dataset.spLinks || '[]')) {
          const a = map.querySelector(`[data-sp-node="${from}"]`)?.getBoundingClientRect();
          const b = map.querySelector(`[data-sp-node="${to}"]`)?.getBoundingClientRect();
          if (!a || !b) continue;
          const right = b.left >= a.right - 2;
          const left = b.right <= a.left + 2;
          const x1 = (right ? a.right : left ? a.left : a.left + a.width / 2) - box.left;
          const x2 = (right ? b.left : left ? b.right : b.left + b.width / 2) - box.left;
          const y1 = ((right || left) ? a.top + a.height / 2 : b.top >= a.bottom - 2 ? a.bottom : a.top) - box.top;
          const y2 = ((right || left) ? b.top + b.height / 2 : b.top >= a.bottom - 2 ? b.top : b.bottom) - box.top;
          const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
          path.dataset.edge = `${from}:${to}`;
          let d = (right || left) ? `M${x1},${y1} C${(x1+x2)/2},${y1} ${(x1+x2)/2},${y2} ${x2},${y2}` : `M${x1},${y1} C${x1},${(y1+y2)/2} ${x2},${(y1+y2)/2} ${x2},${y2}`;
          // Stacked branches travel in the margin, never through another node's text.
          const stacked = matchMedia('(max-width:540px)').matches && !map.classList.contains('sp-hermes-map');
          const obstructed = !right && !left && [...map.querySelectorAll('[data-sp-node]')].some(el => {
            if ([from, to].includes(el.dataset.spNode)) return false;
            const r = el.getBoundingClientRect();
            const minX = Math.min(a.left+a.width/2,b.left+b.width/2) - 1;
            const maxX = Math.max(a.left+a.width/2,b.left+b.width/2) + 1;
            return r.right > minX && r.left < maxX && r.top < Math.max(a.top,b.top) && r.bottom > Math.min(a.bottom,b.bottom);
          });
          if (stacked || obstructed) {
            const onRight = map.classList.contains('sp-memory-map') && to === 'resume';
            const rail = onRight ? box.width + 8 : -8;
            const sx = (onRight ? a.right : a.left) - box.left;
            const tx = (onRight ? b.right : b.left) - box.left;
            const ay = a.top + a.height / 2 - box.top;
            const by = b.top + b.height / 2 - box.top;
            const dy = Math.sign(by - ay) * 8;
            const corner = rail + (onRight ? -8 : 8);
            d = `M${sx},${ay} H${corner} Q${rail},${ay} ${rail},${ay+dy} V${by-dy} Q${rail},${by} ${corner},${by} H${tx}`;
          }
          path.setAttribute('d', d);
          svg.append(path);
        }
      });
    };
    observer = new ResizeObserver(() => { cancelAnimationFrame(frame); frame = requestAnimationFrame(draw); });
    root.querySelectorAll('[data-sp-map]').forEach(map => observer.observe(map));
    frame = requestAnimationFrame(draw);
  }
  return {header, node, wires, section, page:id => ({mempalace, yonote}[id]?.() || ''), bind, disconnect};
})();
