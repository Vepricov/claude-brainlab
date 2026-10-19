/* Public setup guide. Diagram examples never read personal notes or queues. */
window.LAB_OBSIDIAN_SETUP = (() => {
  const repository = 'https://github.com/brain-lab-research/claude-brainlab/tree/main/obsidian-setup';
  const plugins = [['Operon','3.0.1',"Tasks and boards"],['Dataview','0.5.68',"Views inside notes"],['Homepage','4.4.0',"Start screen"],['Templater','2.19.1',"Templates and execution"],['Calendar','1.5.10',"Daily notes"],['Next TOC','2.4.0',"Document outline"],['Iconic','1.1.8',"Icons"],['File Color','1.1.0',"File colors"],['Style Settings','1.0.9',"Theme settings"],['Multi-Column Markdown','0.9.1',"Columns inside notes"],['Banners','1.3.3',"Banners"],['Checklist','2.2.14',"Checkbox lists"],['Tasks','7.23.1',"Task queries"],['Zotero Integration','3.2.1',"Import from your Zotero"]];
  function setup() {
    const {header, node, wires, section} = window.LAB_SURFACE_PAGES;
    return `<div class="sp-page sp-personal" data-surface-page="obsidian" data-obsidian-setup>
      ${header('Obsidian', "Vault = the lab tree", "Your own notes and the lab's shared knowledge.<br>One folder, one window.", '◇')}
      <section class="sp-obsidian-map sp-map" data-sp-map data-sp-links='[["reading","project"],["tasks","project"],["project","diary"],["project","hermes"]]' aria-label="What sits around your work">
        ${wires}
        ${node('reading', "Theme literature", "Paper reviews", "One page per paper: the review and BibTeX with a citation key. Shared across the whole theme.")}
        <article class="sp-personal-project" data-sp-node="project"><span class="sp-label">Copy of the work repository</span><div class="sp-crystal" aria-hidden="true">◇</div><h2>Your work</h2><p>Claims, the manuscript and the code go to GitLab. Notes, the diary and local logs are hidden from git and stay on the machine.</p><div class="sp-file-lines" aria-hidden="true"><i></i><i></i><i></i></div><small>Plain Markdown files<br>and plain git</small></article>
        ${node('diary', "Personal, not in git", "Notes and diary", "Drafts, plans, run logs. They sync with the server where Hermes works.")}
        ${node('tasks', "Personal plan", "Tasks and reading", "Two personal boards: tasks and a reading queue. Every card is a plain file.")}
        ${node('hermes', "Agent work", "Hermes board", "The server agent's queue, progress and results, in the notes of the work they belong to.")}
      </section>
      <div class="sp-obsidian-note"><p>Obsidian opens the lab tree, the same one as in GitLab: direction → theme → work, with the theme literature, the handbook, the journal and the servers alongside. Links between notes work both in Obsidian and in GitLab.</p><a class="os-download sp-primary-link" href="${repository}" target="_blank" rel="noopener">Set it up yourself (GitHub) ↗</a></div>
      <section class="sp-section sp-operon">
        ${section("Personal boards", "Your tasks and reading, in the same files.", "Two boards: one for personal commitments, one for papers. They help pick the next step, while tasks stay plain files next to the work.")}
        <div class="sp-operon-lanes"><article><h3>My tasks</h3><div><span>To do</span><i>→</i><span>Doing</span><i>→</i><span>Review</span><i>→</i><span>Done</span></div><p>Assignee, priority and comments live inside the task.</p></article><article><h3>Reading</h3><div><span>Inbox</span><i>→</i><span>Queue</span><i>→</i><span>Reading</span><i>→</i><span>Read</span></div><p>A paper goes from discovery to read, and postponed ones are shown separately.</p></article></div>
      </section>
      <section class="sp-section" data-hermes-guide>
        ${section("Hermes next to the project", "The agent works. You see its progress.", "The overview refreshes itself every 15 minutes, no model involved: a simple script copies statuses and comments from the Hermes board into the work folder.")}
        <div class="sp-hermes-map sp-map" data-sp-map data-sp-links='[["queue","export"],["export","folder"]]'>${wires}
          ${node('queue', "On the server", "Hermes board", "The server agent's tasks, messages and results.")}
          ${node('export', "Every 15 minutes", "A script, no model", "Pulls entries from the server and copies them as they are, inventing nothing.")}
          ${node('folder', "In the work folder", "Hermes overview", "Active board and history. The overview is read-only and does not go to git.")}
        </div>
        <div class="sp-hermes-preview"><header><span>Sample overview · fictional tasks</span><span>View only</span></header><div><span class="sp-status sp-running">In progress</span><b>Compare three launches</b><span>demo-server · GPU 0, 1</span></div><div><span class="sp-status sp-help">Needs help</span><b>Clarify the base model budget</b><span>A step limit has to be chosen</span></div><div><span class="sp-status">Next</span><b>Assemble the final report</b><span>Run not started yet</span></div></div>
        <p class="sp-small">In Obsidian the cards expand: readable dates, the result and the latest messages. The server and GPUs show up when Hermes has specified them. If the server is unreachable, the overview shows the last known state.</p>
        <p class="sp-under-map">Each work has its own overview of Hermes's progress, with your own notes right beside it.</p>
      </section>
      <section class="sp-section sp-setup-details">
        ${section("Set it up yourself", "One command.", "For a lab member, the installer sets up the lab command, the agent rules and this setup, and assembles the lab tree. Outside the lab, the same kit installs into a new folder.")}
        <details class="sp-fold" data-setup-install><summary>Installation <span>The lab tree or a new folder</span></summary><div class="sp-fold-body"><p>A lab member installs everything with one command; after that <code>lab sync</code> pulls in their works, their literature, <code>handbook</code>, <code>journal</code> and <code>servers</code>:</p><pre><code>git clone https://github.com/brain-lab-research/claude-brainlab
bash claude-brainlab/docs/lab/install.sh</code></pre><p>Vault conventions (icons, folder colors, boards) live in the vault itself.</p><p>Outside the lab: install Obsidian, Git and Python 3.10+, download the kit and pick a new folder:</p><pre><code>git clone --depth 1 https://github.com/brain-lab-research/claude-brainlab.git
cd claude-brainlab/obsidian-setup
python3 install.py --vault "$HOME/My Research" --owner "Researcher"</code></pre><p>Windows PowerShell:</p><pre><code>py -3 -m pip install tzdata
py -3 install.py --vault "$env:USERPROFILE\\My Research" --owner "Researcher"</code></pre><p>In Obsidian: <b>Open folder as vault</b> → the created folder → allow community plugins → <b>START HERE</b>. The “Start” workspace opens both boards.</p><p>First task: command palette → <b>Operon: Create New Operon Task</b> → title → <b>Pick a Template → Task → File</b>. The template fills in your assignee name.</p><p>The installer only creates a new vault, downloads pinned versions and checks SHA-256. Change an existing vault selectively, with a backup and with Obsidian closed.</p><p class="sp-small">A full run of the kit has been tested in Obsidian on macOS.</p></div></details>
        <details class="sp-fold" data-setup-plugins><summary>Theme and 14 plugins <span>Contents and versions</span></summary><div class="sp-fold-body"><p>Border 1.13.6, three CSS snippets and the enabled set:</p><div class="sp-plugin-list">${plugins.map(([name,version,role]) => `<div><b>${name}</b><span>${role}</span><code>${version}</code></div>`).join('')}</div><p>File Tree Alternative 2.6.0 and Notebook Navigator 2.6.2 are recorded as disabled. The <code>--include-disabled</code> flag downloads them too.</p></div></details>
        <details class="sp-fold" data-setup-hermes><summary>Connecting Hermes <span>Server → work folder</span></summary><div class="sp-fold-body"><p>In <code>examples/hermes-config.json</code>, set the Hermes board, the server address and the work folder: the overview lands in that work's notes. One config file links several works.</p><pre><code>python3 sync_hermes.py --config /path/to/hermes-config.json</code></pre><p>Test a single run first. Then turn on a 15-minute interval: the kit includes launchd templates for Mac, systemd for Linux and Task Scheduler instructions for Windows. The computer has to stay on.</p><p>The script only reads the Hermes board and never changes its tasks.</p></div></details>
      </section>
      <footer class="sp-footer"><p>Personal stays on the machine. Shared knowledge goes to GitLab as a proposal, and team tasks live in the work repository.</p><nav><a href="#memory">Map of shared knowledge ↗</a><a href="#surface/gitlab">Tasks and proposals in GitLab ↗</a></nav></footer>
    </div>`;
  }
  function render(id) {
    if (['obsidian-project-memory','operon-obsidian-setup','hermes','paperscout'].includes(id)) return "<p class=\"os-reference\"><a href=\"#surface/obsidian\" data-obsidian-surface>Obsidian: install, plugins and Hermes boards ↗</a></p>";
    return '';
  }
  return {render, page:setup};
})();
