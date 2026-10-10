/* Public setup guide. Diagram examples never read personal notes or queues. */
window.LAB_OBSIDIAN_SETUP = (() => {
  const repository = 'https://github.com/brain-lab-research/claude-brainlab/tree/main/obsidian-setup';
  const plugins = [['Operon','3.0.1',"Tasks and boards"],['Dataview','0.5.68',"Views inside notes"],['Homepage','4.4.0',"Start screen"],['Templater','2.19.1',"Templates and execution"],['Calendar','1.5.10',"Daily notes"],['Next TOC','2.4.0',"Document outline"],['Iconic','1.1.8',"Icons"],['File Color','1.1.0',"File colors"],['Style Settings','1.0.9',"Theme settings"],['Multi-Column Markdown','0.9.1',"Columns inside notes"],['Banners','1.3.3',"Banners"],['Checklist','2.2.14',"Checkbox lists"],['Tasks','7.23.1',"Task queries"],['Zotero Integration','3.2.1',"Import from your Zotero"]];
  function setup() {
    const {header, node, wires, section} = window.LAB_SURFACE_PAGES;
    return `<div class="sp-page sp-personal" data-surface-page="obsidian" data-obsidian-setup>
      ${header('Obsidian', "A researcher's personal workspace", "Project, ideas, and the next step.<br>Connected and close at hand.", '◇')}
      <section class="sp-obsidian-map sp-map" data-sp-map data-sp-links='[["reading","project"],["tasks","project"],["project","diary"],["project","hermes"]]' aria-label="Materials around your project">
        ${wires}
        ${node('reading', "Sources", "Literature", "Paper notes and links to your Zotero library.")}
        <article class="sp-personal-project" data-sp-node="project"><span class="sp-label">In your project's folder</span><div class="sp-crystal" aria-hidden="true">◇</div><h2>Your project</h2><p>The main note connects the idea, plans, results, and materials.</p><div class="sp-file-lines" aria-hidden="true"><i></i><i></i><i></i></div><small>Ordinary Markdown files<br>linked to each other</small></article>
        ${node('diary', "Research progress", "Notes and diary", "Hypotheses, calls, protocols, plots, and the reasons behind decisions.")}
        ${node('tasks', "Personal plan", "Tasks and reading", "Two Operon boards. The same tasks are available as a table and Markdown.")}
        ${node('hermes', "Agent work", "Hermes board", "Queue, progress, and results beside the project they belong to.")}
      </section>
      <div class="sp-obsidian-note"><p>Each project has its own folder. Papers live in the library, linked to the research that uses them.</p><a class="os-download sp-primary-link" href="${repository}" target="_blank" rel="noopener">Get the setup on GitHub ↗</a></div>
      <section class="sp-section sp-operon">
        ${section('Operon', "Two focused workflows.", "One for personal commitments and one for reading. Boards help choose the next step while keeping tasks in ordinary files.")}
        <div class="sp-operon-lanes"><article><h3>My tasks</h3><div><span>To do</span><i>→</i><span>Doing</span><i>→</i><span>Review</span><i>→</i><span>Done</span></div><p>The assignee, priority, and comments are inside each task.</p></article><article><h3>Reading</h3><div><span>Inbox</span><i>→</i><span>Queue</span><i>→</i><span>Reading</span><i>→</i><span>Read</span></div><p>Separate states handle deferred papers and papers awaiting publication.</p></article></div>
      </section>
      <section class="sp-section" data-hermes-guide>
        ${section("Hermes beside your project", "The agent works. You see its progress.", "A regular Python script updates the view every 15 minutes. Statuses, original IDs, and comments come from the Hermes queue.")}
        <div class="sp-hermes-map sp-map" data-sp-map data-sp-links='[["queue","export"],["export","folder"]]'>${wires}
          ${node('queue', "On your server", "Hermes queue", "Tasks, messages, and results from the existing kanban.db.")}
          ${node('export', "On a schedule", "Python · no LLM", "Reads SQLite over SSH and transforms the records deterministically.")}
          ${node('folder', "In the project folder", 'Knowledge / Hermes', "Active board and history. This is a read-only view.")}
        </div>
        <div class="sp-hermes-preview"><header><span>Example view · fictional tasks</span><span>Read only</span></header><div><span class="sp-status sp-running">In progress</span><b>Compare three runs</b><span>demo-server · GPU 0, 1</span></div><div><span class="sp-status sp-help">Needs help</span><b>Clarify the baseline budget</b><span>A step limit needs to be chosen</span></div><div><span class="sp-status">Next</span><b>Compile the final report</b><span>The run has not started</span></div></div>
        <p class="sp-small">Cards expand in Obsidian to show readable dates, the result, and recent messages. Server and GPU details appear when Hermes provides them. If the server is unavailable, the last successful snapshot remains.</p>
        <p class="sp-under-map">Hermes is the source of status information. The export does not require Operon. Each project has its own view, with room for your notes alongside it.</p>
      </section>
      <section class="sp-section sp-setup-details">
        ${section("Set it up yourself", "One toolkit on GitHub.", "Settings, a theme, plugins, and examples. Add your own notes, Zotero library, and Hermes connection locally.")}
        <details class="sp-fold" data-setup-install><summary>Install from GitHub <span>Into a new Obsidian folder</span></summary><div class="sp-fold-body"><p>Install Obsidian, Git, and Python 3.10+. Download the toolkit and choose a new folder:</p><pre><code>git clone --depth 1 https://github.com/brain-lab-research/claude-brainlab.git
cd claude-brainlab/obsidian-setup
python3 install.py --vault "$HOME/My Research" --owner "Researcher"</code></pre><p>Windows PowerShell:</p><pre><code>py -3 -m pip install tzdata
py -3 install.py --vault "$env:USERPROFILE\\My Research" --owner "Researcher"</code></pre><p>In Obsidian: <b>Open folder as vault</b> → the new folder → allow community plugins → <b>START HERE</b>. The Start workspace, named “Старт” in the supplied setup, opens both boards.</p><p>First task: command palette → <b>Operon: Create New Operon Task</b> → title → <b>Pick a Template → Task → File</b>. The template fills in your name as assignee.</p><p>The installer only creates a new vault, downloads pinned versions, and checks SHA-256. Change an existing vault selectively, with a backup and Obsidian closed.</p><p class="sp-small">The full setup has been verified in Obsidian on macOS. Installation in the application on Windows and Linux has not yet been confirmed.</p></div></details>
        <details class="sp-fold" data-setup-plugins><summary>Theme and 14 plugins <span>Components and versions</span></summary><div class="sp-fold-body"><p>Border 1.13.6, three CSS snippets, and these enabled plugins:</p><div class="sp-plugin-list">${plugins.map(([name,version,role]) => `<div><b>${name}</b><span>${role}</span><code>${version}</code></div>`).join('')}</div><p>File Tree Alternative 2.6.0 and Notebook Navigator 2.6.2 are listed as disabled. <code>--include-disabled</code> downloads them too. The automatic archiver is not enabled.</p></div></details>
        <details class="sp-fold" data-setup-hermes><summary>Connect Hermes <span>Server → project folder</span></summary><div class="sp-fold-body"><p>In <code>examples/hermes-config.json</code>, enter the existing board slug, SSH alias, and project folder. One configuration can connect several projects.</p><pre><code>python3 sync_hermes.py --config /path/to/hermes-config.json</code></pre><p>Check one run first. Then enable a 15-minute interval using the supplied launchd templates for Mac, systemd templates for Linux, or Task Scheduler instructions for Windows. The computer must be on.</p><p>The <code>kanban.db</code> contract is specific to our Hermes profile: this queue must exist on your server. The export reads it without changing Hermes or Yonote tasks.</p></div></details>
      </section>
      <footer class="sp-footer"><p>Personal files stay in your Obsidian vault. Shared claims go to MCP, and team tasks go to Yonote.</p><nav><a href="#memory">Shared knowledge map ↗</a><a href="#surface/yonote">How Yonote works ↗</a></nav></footer>
    </div>`;
  }
  function render(id) {
    if (['obsidian-project-memory','operon-obsidian-setup','hermes','paperscout'].includes(id)) return "<p class=\"os-reference\"><a href=\"#surface/obsidian\" data-obsidian-surface>Obsidian: installation, plugins, and Hermes boards ↗</a></p>";
    return '';
  }
  return {render, page:setup};
})();
