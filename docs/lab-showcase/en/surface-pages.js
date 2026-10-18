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
        <ol class="sp-recall-path"><li><span>Short query</span><p>Keywords, project, and the topic you need.</p></li><li><span>Meaning and words</span><p>Vector candidates; word matches refine the order.</p></li><li><span>Source fragment</span><p>Text, its place in memory, and a link to the source.</p></li><li><span>Check now</span><p>Server status, code, and results may have changed.</p></li></ol>
        <div class="sp-memory-foot"><div><h3>Need to pick up quickly?</h3><p>The latest diary entries give the next actions. Project search helps recover an older decision.</p></div><div><h3>Need to understand a connection?</h3><p>A graph query finds relations between entities and their history. An old fact can be closed in time while keeping its provenance.</p></div></div>
        <details class="sp-fold"><summary>Storage and tools <span>Technical details</span></summary><div class="sp-fold-body"><p>In the tested setup, texts and vectors live in a local Chroma. Search first gets candidates by meaning; topic summaries can bring up related sources, and BM25 refines the order by words. This is a search over saved material, with no new text generated inside the search tool.</p><p>Typed relations with a validity period are stored separately in SQLite. The diary can be written in the compact AAAK format; source fragments are saved as plain text so they can be read and checked.</p><dl class="sp-api"><dt>Write</dt><dd>mempalace_diary_write · mempalace_add_drawer · mempalace_kg_add</dd><dt>Recall</dt><dd>mempalace_diary_read · mempalace_search · mempalace_get_drawer · mempalace_kg_query</dd></dl></div></details>
      </section>
      <footer class="sp-footer"><p>MemPalace returns the history of work. Shared scientific claims and their grounds live in the Lab GitLab.</p><nav><a href="#memory">Map of shared knowledge ↗</a><a href="https://github.com/MemPalace/mempalace" target="_blank" rel="noopener">MemPalace on GitHub ↗</a></nav></footer>
    </div>`;
  }

  function tasks() {
    return `<div class="sp-page sp-team" data-surface-page="tasks">
      ${header("GitLab issues", "Shared team workspace", "Every work has its own repository.<br>Every issue has a clear result.", '⌘')}
      <section class="sp-team-map sp-map" data-sp-map data-sp-links='[["research","theme"],["theme","area"],["area","project"],["management","delivery"],["delivery","project"]]' aria-label="Research and management sides of a work">
        ${wires}
        ${node('research', "Top-level group", "Direction", "An area of the lab: what we study and which questions we answer.")}
        ${node('theme', "Inside a direction", "Theme", "Related works and a shared literature repository.")}
        ${node('area', "Within a topic", "Work", "One repository: claims, manuscript, and code.")}
        <article class="sp-project-sheet" data-sp-node="project"><span class="sp-label">Work repository</span><h3>Question → result</h3><p>README: what we claim, who leads, who is on the team, and what is open.</p><div><b>Issues</b><span>The work's board: what is being done and by whom</span></div><div><b>Merge requests</b><span>Every record in a work is a merge request</span></div></article>
        ${node('management', "Operations", "Commitments", "Grants, commercial projects, stages, and acceptance: the ops group.", 'sp-management')}
        <article class="sp-delivery" data-sp-node="delivery"><span class="sp-label">Commitment repository</span><h3>What we deliver and when</h3><p>Client or program, stages, deadlines, documents, and acceptance criteria.</p><span class="sp-crosslink">Links to the works the result comes from ↗</span></article>
      </section>
      <p class="sp-under-map"><b>Commercial research uses both sides.</b> The scientific work stays in the lab tree, contract materials stay in operations. A work has one issue board.</p>
      <section class="sp-section">
        ${section("Inside a work", "From an agreement to a task.", "A person sees the expected result, the assignee, and how the work moves. Details stay in the issue itself.")}
        <div class="sp-task-layout"><article class="sp-task-example"><span class="sp-label">Illustrative issue</span><h3>Compare two methods<br>at the same budget</h3><dl><dt>Assignee</dt><dd>A member of the work</dd><dt>Claim</dt><dd>The issue names the claim it affects</dd><dt>Done when</dt><dd>There is a series of runs and a link to it in the claim</dd><dt>Result</dt><dd>A merged merge request with the line “Closes #N”</dd></dl></article><div class="sp-task-explainer"><h3>The status reflects how the work goes.</h3><ol class="sp-task-path"><li><b>Open</b><span>The goal and the assignee are clear</span></li><li><b>In progress</b><span>There is progress or a specific blocker</span></li><li><b>In review</b><span>The merge request is open and can be assessed</span></li><li><b>Closed</b><span>The merge request is merged and the issue closed itself</span></li></ol><p class="sp-small">Board columns are issue labels. An issue is closed by merging the merge request, not by a manual tick.</p></div></div>
      </section>
      <section class="sp-section">
        ${section("People and agents", "Work on one board.", "Issues live in the same work repository that knowledge is written to. There is no second board next to it.")}
        <div class="sp-team-actors"><article><span class="sp-label">Person</span><h3>Sets and checks</h3><p>Defines the result, assigns the assignee, discusses progress, and merges the merge request that closes the issue.</p></article><article><span class="sp-label">Agent in a clone</span><h3>Prepares and submits</h3><p>At session start it sees what it has been assigned. It takes the issue, does the work in the clone, and opens a merge request that links the issue.</p></article><article><span class="sp-label">Agent on the server</span><h3>Handles long jobs</h3><p>Watches runs and reports what came out in the same issue. The person stays the assignee.</p></article></div>
        <p class="sp-under-map">A closed issue and the assessment of a scientific claim are different results: the issue says the work is done, the claim's state says what follows from it.</p>
      </section>
      <aside class="sp-common"><span class="sp-label">General information</span><h3>An entry point for everyone.</h3><p>The lab's front page in GitLab, the handbook, and the journal: how everything is set up, how to join a work, and what changed recently.</p></aside>
      <footer class="sp-footer"><p>Personal tasks are in Operon. Team work is the work's issues and boards in GitLab. Drafts stay in the notes/ of your work.</p><nav><a href="https://github.com/brain-lab-research/claude-brainlab/blob/main/docs/onboarding.md" target="_blank" rel="noopener">How to set it up ↗</a></nav><small>The base address comes in a message from the access bot.</small></footer>
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
  return {header, node, wires, section, page:id => ({mempalace, tasks}[id]?.() || ''), bind, disconnect};
})();
