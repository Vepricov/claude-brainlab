/* Explanatory maps only. No connection to personal memory or task services. */
window.LAB_SURFACE_PAGES = (() => {
  const header = (name, label, lead, glyph) => `<header class="sp-hero"><div><span class="sp-label">${label}</span><h1 tabindex="-1">${name}</h1><p>${lead}</p></div><div class="sp-emblem" aria-hidden="true"><i></i><i></i><i></i><span>${glyph}</span></div></header>`;
  const node = (id, label, title, text, extra = '') => `<article class="sp-node ${extra}" data-sp-node="${id}"><span class="sp-label">${label}</span><h3><i class="sp-star" aria-hidden="true"></i>${title}</h3><p>${text}</p></article>`;
  const wires = '<svg class="sp-wires" aria-hidden="true"></svg>';
  const section = (label, title, text) => `<header class="sp-section-head"><div><span class="sp-label">${label}</span><h2>${title}</h2></div><p>${text}</p></header>`;

  function mempalace() {
    return `<div class="sp-page sp-memory" data-surface-page="mempalace">
      ${header('MemPalace', "The agent's personal long-term memory", "A new conversation.<br>The work picks up where it left off.<br><b class=\"sp-hero-fact\">Over 37,600 entries as of 19-10-2026.</b>", '✧')}
      <section class="sp-memory-map sp-map" data-sp-map data-sp-links='[["session","diary"],["session","fragment"],["session","relation"],["diary","resume"],["fragment","resume"],["relation","resume"]]' aria-label="From a working turn to memory and the next session">
        ${wires}
        ${node('session', "Now", "Working turn", "A conversation, the root cause of a bug, a decision taken, a measured number. The agent decides what is worth keeping.", 'sp-session')}
        <div class="sp-memory-channels">
          ${node('diary', "Agent diary", "Compressed summary", "What was done, what is left and where to resume. Written compactly, with a date and a topic.")}
          ${node('fragment', "Project drawers", "Verbatim", "The owner's words, a decision with its reason, a command, a code snippet. Not a paraphrase: a paraphrase loses exactly what you come back for.")}
          ${node('relation', "Knowledge graph", "Relationships and facts", "Who leads the project, what a decision relates to, and when a fact was valid.")}
        </div>
        <article class="sp-resume" data-sp-node="resume"><span class="sp-label">Next session</span><h3>“Where did we leave off?”</h3><p>The agent reads its diary, searches the project history and opens the fragments it needs.</p><div class="sp-resume-result"><i class="sp-star" aria-hidden="true"></i><strong>Context restored</strong><span>Decision · reason · next step</span></div></article>
      </section>
      <p class="sp-under-map"><b>The end of each turn is checked by Jev, a fast model.</b> If the turn has something worth saving, the agent gets one line: what to record and where. The agent itself chooses the content and writes it.</p>
      <section class="sp-section">
        ${section("How the palace is organized", "Every fragment has an address.", "The hierarchy narrows the search: first the project, then an aspect of the work, then the specific source.")}
        <div class="sp-palace-address">
          <article><span class="sp-label">Wing</span><h3>Project</h3><p>The shared context of one work.</p><span class="sp-address-example">example-project</span></article>
          <span class="sp-arrow" aria-hidden="true">→</span>
          <article><span class="sp-label">Room</span><h3>Aspect</h3><p>Decisions, bugs, meetings, technical details.</p><span class="sp-address-example">decisions</span></article>
          <span class="sp-arrow" aria-hidden="true">→</span>
          <article class="sp-drawer"><span class="sp-label">Drawer</span><blockquote>“For the comparison we fix the same training budget.”</blockquote><p>Text, source, date and number</p></article>
        </div>
        <p class="sp-small">Illustrative example.</p>
      </section>
      <section class="sp-section">
        ${section("How the agent recalls", "From a question to the original context.", "Search returns the saved drawers. The agent reads them and checks them against the current state of the work.")}
        <ol class="sp-recall-path"><li><span>Short query</span><p>Keywords, the project and the topic you need.</p></li><li><span>Meaning and words</span><p>Search goes by meaning, and exact words refine the ranking.</p></li><li><span>Source fragment</span><p>The text, its place in memory and a link to the source.</p></li><li><span>Check against today</span><p>Memory may be stale, so the agent checks it against the current code and server.</p></li></ol>
        <div class="sp-memory-foot"><div><h3>Need to resume fast?</h3><p>The latest diary entries give the next actions. Project search helps recover an older decision.</p></div><div><h3>Need to see a connection?</h3><p>A graph query finds relations between entities and their history. An old fact can be closed off in time while keeping its provenance.</p></div></div>
        <details class="sp-fold"><summary>Storage and tools <span>Technical details</span></summary><div class="sp-fold-body"><p>Texts and their semantic fingerprints are stored locally, on the researcher's machine. Search first finds candidates by meaning, then refines the ranking by words. It returns what was saved and never makes up anything new.</p><p>Relations between people, projects and decisions are stored separately, with the period when each fact held. Source fragments are kept as plain text so they can be read and checked.</p><dl class="sp-api"><dt>Write</dt><dd>summary to the diary · verbatim fragment · relation to the graph</dd><dt>Recall</dt><dd>diary · search · full fragment · relations</dd></dl></div></details>
      </section>
      <footer class="sp-footer"><p>MemPalace is the memory of one agent, not the lab base. Shared knowledge (claims, runs, paper reviews) lives in GitLab and gets there only through a merged proposal.</p><nav><a href="#memory">Map of shared knowledge ↗</a><a href="https://github.com/MemPalace/mempalace" target="_blank" rel="noopener">MemPalace on GitHub ↗</a></nav></footer>
    </div>`;
  }

  function yonote() {
    return `<div class="sp-page sp-team" data-surface-page="yonote">
      ${header('GitLab', "Tasks, boards and proposals", "Task, check and record in one repository.<br>A human has the final say.", '⎇')}
      <section class="sp-team-map sp-map" data-sp-map data-sp-links='[["research","theme"],["theme","area"],["area","project"],["management","delivery"],["delivery","project"]]' aria-label="Research and operations in the lab GitLab">
        ${wires}
        ${node('research', "The brainlab group", "Direction", "The lab's seven research directions.")}
        ${node('theme', "Inside a direction", "Theme", "Related works and the theme's shared literature.")}
        ${node('area', "Within a topic", "Work", "A separate repository. The leads are listed on the work's front page, and only they merge.")}
        <article class="sp-project-sheet" data-sp-node="project"><span class="sp-label">Inside a work</span><h3>Task → record</h3><p>Tasks, the board and proposals live next to the knowledge itself: claims, the paper and the code.</p><div><b>Tasks and board</b><span>Board columns are built from labels</span></div><div><b>Edit proposals</b><span>Checks verify, the lead merges</span></div></article>
        ${node('management', "The ops group", "Operations", "Grants, management, education, communications. A closed group, separate from research.", 'sp-management')}
        <article class="sp-delivery" data-sp-node="delivery"><span class="sp-label">Stream = label</span><h3>What we deliver and when</h3><p>Operations tasks are sorted into label streams, such as the content plan and paper reviews. The label filter works both in the list and on the board.</p><span class="sp-crosslink">Progress: “in progress” → “in review”</span></article>
      </section>
      <p class="sp-under-map"><b>Research and operations share one GitLab, but sit in different groups.</b> Access to research gives no access to operations. A work has one board, in its own repository.</p>
      <section class="sp-section">
        ${section("Inside a work", "From an agreement to a task.", "A task lives in the work repository. Its body carries the claim code, so you see at once which claim the result will go under.")}
        <div class="sp-task-layout"><article class="sp-task-example"><span class="sp-label">Illustrative task</span><h3>Compare two methods<br>at the same budget</h3><dl><dt>Assignee</dt><dd>Whoever took the task with one command</dd><dt>Claim</dt><dd>The code of the claim the task will support or refute</dd><dt>Done when</dt><dd>The runs are written by the run recorder and filed under the claim</dd><dt>Closing</dt><dd>Merging the proposal closes the task by itself</dd></dl></article><div class="sp-task-explainer"><h3>Status tracks the work.</h3><ol class="sp-task-path"><li><b>Open</b><span>Goal and claim are clear</span></li><li><b>In progress</b><span>Whoever took the task is the assignee</span></li><li><b>In review</b><span>Proposal open, checks running</span></li><li><b>Closed</b><span>The lead merged the proposal</span></li></ol><p class="sp-small">Board columns are built from the “in progress” and “in review” labels.</p></div></div>
      </section>
      <section class="sp-section">
        ${section("People and agents", "They work in one repository.", "The agent never writes to the base directly. It opens a proposal, automated checks verify it, a human merges. The merge is the record.")}
        <div class="sp-team-actors"><article><span class="sp-label">Human</span><h3>Assigns and merges</h3><p>Sets the task and picks the assignee. The work lead reads the proposal and decides whether it enters the base.</p></article><article><span class="sp-label">Claude Code</span><h3>Prepares the proposal</h3><p>At the start of a session it pulls the latest changes and shows what is assigned. It takes a task, works on a separate branch, opens a proposal to the lead with one command and sees the checks' verdict.</p></article><article><span class="sp-label">Hermes</span><h3>Runs its own board</h3><p class="sp-fact"><b>On its board for a single project, Hermes has closed 381 tasks.</b></p><p>The server agent has its own task board, shared across all its projects: take, block, comment. A board overview arrives in Obsidian, in the work folder.</p></article></div>
        <p class="sp-under-map">The checks are computed by code: a number absent from every run blocks the merge, and a judge model can hold it until the text is fixed. GitLab will not merge what has not passed. A closed task and an accepted claim are different outcomes.</p>
      </section>
      <aside class="sp-common"><span class="sp-label">Shared information</span><h3>One entry point for everyone.</h3><p>The handbook: how everything works and the rulebook for records. The journal: what changed in how we work, and when. Servers: where to compute and how to get access. All three are open to anyone signed in.</p></aside>
      <footer class="sp-footer"><p>Personal tasks and drafts live in Obsidian. Team work means tasks and proposals in GitLab.</p><nav><a href="#surface/obsidian">Obsidian and the lab tree ↗</a><a href="#memory">Map of shared knowledge ↗</a></nav><small>Access is granted by the lab's Telegram bot: guest, student, researcher or direction lead.</small></footer>
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
