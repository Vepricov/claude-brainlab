/* Explanatory maps contain no private records and read nothing from the lab's GitLab. */
window.LAB_MEMORY_MAP = (() => {
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const origins = {
    projects:["Project","create-project · context"],
    literature:["Literature",'Hermes · paper-ingest'],
    ideation:["Ideas",'research-ideation'],
    calls:["Calls",'Brain Call · call-notes'],
    experiments:["Experiments",'Hermes · coding agents'],
    results:["Results","analysis · academic-plotting"],
    writing:["Writing and review",'ML Paper Writing · Astar'],
    presentation:["Publication",'paper-to-social · presentation']
  };
  const dot = '<i class="mem-star" aria-hidden="true"></i>';
  const arrow = '<i class="mem-inline-arrow" aria-hidden="true">→</i>';
  const station = (id, label, title, body, extra='') => `<article class="mem-station ${extra}" data-point="${id}">${dot}<span class="mem-label">${label}</span><h3>${title}</h3>${body}</article>`;
  const api = (...names) => `<span class="mem-api-names">${names.map(n=>`<code>${n}</code>`).join(' · ')}</span>`;
  const svg = '<svg class="mem-connections" aria-hidden="true"></svg>';
  const inlets = {
    ingest:[['scout',"Literature Hermes","Finds papers on the topic"],['search','paper-search',"Suggests candidates"],['alphaxiv','alphaXiv / arXiv',"Link to a paper"],['social',"X / colleagues","Share a paper"],['reader',"Researcher","Selects a paper for analysis"]],
    project:[['hermes',"Hermes for experiments","Runs and results"],['agents','Codex / Claude Code',"Code, checks, and conclusions"],['call','Brain Call / call-notes',"Meeting ideas and decisions"],['person',"Researcher","Hypotheses and materials"]]
  };
  const feeders = kind => `<div class="mem-feeders" aria-label="${kind==='ingest'?"Where papers come from":"Where work materials come from"}">${inlets[kind].map(([id,title,caption])=>`<div class="mem-inlet" data-inlet="${kind}" data-point="${kind}-via-${id}"><b>${title}</b><small>${caption}</small></div>`).join('')}</div>`;

  // Устройство записей сверено со сводом правил базы (brainlab/handbook, canon.md), 18-10-2026.
  const recordGuide = {
    hypothesis: {title:"Our claim",code:'claims/H-XXX/',text:"One testable idea about a method is a folder in the work repository. The H-XXX code is given once and stays after testing: it shows the grounds, the history, and the conclusion.",fields:[["Title","One sentence you can read aloud: what we claim and under which conditions. Code checks this, not the writer's good faith."],["Falsification","What exactly would refute the idea. Without a falsification criterion it is not a claim."],["Grounds","Runs and series in runs/ and series/, derivations in theory/, figures in figures/: next to it, in the same folder."],["State","draft → testing → supported, refuted, or inconclusive, and it changes only by its own criterion."],["Provenance","The work and theme are visible from the path, the history from git: who wrote it, when, and with which merge request."]],example:"“At the same budget, method A reduces error relative to B.” Falsification criterion: the advantage disappears when the specified comparison is repeated."},
    empirical: {title:"Tested by experiment",code:'claims/H-XXX/ · runs · series',text:"A claim tested by measurement. Code writes the runs, and series gather them to answer one question.",fields:[["What it establishes","An effect, relationship, method comparison, or scope of applicability."],["What supports it","By series of runs: every number has an address where it can be seen."]],example:"“With a fixed number of steps, method A yields lower error on the held-out set.”"},
    theoretical: {title:"Tested by derivation",code:'claims/H-XXX/ · theory',text:"A claim tested by mathematical derivation. The assumptions and the proof live in a derivation file next to the claim.",fields:[["What it establishes","An equality, bound, convergence result, or another mathematical result."],["What supports it","By a derivation with explicit assumptions and a “Proof” section."]],example:"“Under the stated assumptions, the error decreases at least as fast as the specified bound.”"},
    unspecified: {title:"Both",code:'claims/H-XXX/',text:"An ideal claim holds both theory and experiments about one technique: a theorem and runs about the same thing are one folder, not two.",fields:[["Why this way","So that a work has a handful of claims rather than a hundred, and each one can be read in full."]]},
    paperClaim: {title:"Paper claim",code:"literature/<Title>.md",text:"An idea from an external work: what its authors claim and where to find it. A paper analysis is a page in the theme literature repository, one per paper.",fields:[["Content","A statement with its conditions of applicability. Paraphrasing is allowed."],["Kind","A result, theorem, method, or definition."],["Source","A section, table, formula, or theorem of the paper; the citation key and BibTeX are in the page header."],["Relationships","Our work links to the analysis: background, baseline, supports, or contradicts. A link alone does not complete our own check."]],example:"“The authors report lower error in Table 2 on dataset X under the stated conditions.”"},
    paperEmpirical: {title:"Authors' result",code:"literature · result",text:"A measurement or observation reported by the paper. Essential conditions are preserved: model, data, metric, and comparison.",fields:[["Use","You can compare the reported result with your own run and find the original table."]],example:"“In Table 3, method A outperforms B on two of three datasets.”"},
    paperTheoretical: {title:"Authors' theoretical result",code:"literature · theorem",text:"A theorem, lemma, bound, or derivation from the paper. The statement keeps the assumptions, and the pointer leads to where the proof is.",fields:[["Use","Helps apply the result in your own work under the conditions for which it was proved."]],example:"“Theorem 1 gives a convergence bound under a Lipschitz gradient assumption.”"},
    paperMethod: {title:"Method from a paper",code:"literature · method",text:"What the authors propose to do: an algorithm, a training technique, or a procedure. The method description is kept apart from the claim about its effectiveness.",fields:[["Use","Lets you recover the method's idea and connect it to your implementation."]],example:"“The authors normalize the update by its spectral norm before the optimizer step.”"},
    paperDefinition: {title:"Definition from a paper",code:"literature · definition",text:"How the authors define a concept or a quantity. Helps compare works in which the same word means different things.",fields:[["Use","Preserves the term's precise meaning in this publication."]],example:"“Definition 2 specifies effective rank through the matrix spectrum.”"},
    assessment: {title:"Claim state",code:'status',text:"The state changes on the same claim and only by its own criterion. A finished run does not change the state by itself: a person or an agent formulates the conclusion, and a person merges it.",fields:[["Before a conclusion","draft → testing with the first series."],["After testing","supported, refuted, or inconclusive."],["Conclusion","Only a fully examined claim has a “Conclusion” section: under draft and testing there is none, otherwise it promises what is not there yet."],["History","Every change is a merge commit: you can see who changed the state, when, and on what grounds."]],example:"The runs finished, but the results differ between repeats. Claim: inconclusive, and the series says why."},
    experiment: {title:"Run",code:'runs/E-XXX.md',text:"The page of a single launch. Code writes it: the lab_run.py recorder knows the hyperparameters, numbers, commit, and hardware, and copying them by hand is forbidden.",fields:[["Contents","Command, configuration, environment, commit, hardware, and metrics, as the recorder wrote them."],["From the agent","Exactly one thing: what is seen in these numbers."]],example:"Comparing A and B on one model and dataset with the same budget: three seeds, each with its own page."},
    evidence: {title:"Series",code:'series/S-XXX.md',text:"A set of runs that answers one question, and a verdict on it. A series enters the claim as a paragraph.",fields:[["Fact","A table of runs and numbers; every number has an address where it can be seen."],["Meaning","Verdict and limits: “not established” is also a valid verdict."],["Cleanliness","Incomparable runs are not pulled into a series; a run outside a series says so on its own page."]],example:"Mean error is 0.18 for A and 0.20 for B across three repeats. Limitation: tested on one dataset."},
    derivation: {title:"Derivation",code:'theory/D-XXX.md',text:"The mathematical basis of a claim: statement, assumptions, and a “Proof” section. One file per storyline, not per lemma.",fields:[["Statement","Reads from scratch and contains no numbers from a specific run."],["Role in the work","A derivation lives only if it says where it works in the claim."]],example:"Derive an upper error bound from smoothness assumptions and explicitly identify a lemma that remains unproved."},
    project: {title:"Work",code:"<direction>/<theme>/<work>",text:"One repository per work. The front page answers in one order: what we claim, what it has been tested with, what is open.",fields:[["Contents","claims/ is knowledge; paper/ and code/ are the manuscript and code as nested repositories; socials/ and calls/ are posters and calls."],["People","The “Leads” and “Team” lines in the README: the bot uses them to call people to decide access requests, and merge requests are assigned to the lead."]]},
    paper: {title:"Theme literature",code:"<theme>/literature/",text:"Every theme has its own repository of analyses: one page per paper, named after the paper, with the citation key in the header. The literature README is assembled from the pages themselves.",fields:[["Use","From a statement in our work you can go back to the full analysis. One paper can be needed by many works."]]},
    decision: {title:"Merge request",code:'merge request',text:"Every record in a work comes in as a merge request: branch, commit, git push, and the merge request opens by itself. The gates count numbers and judge prose, a person merges.",fields:[["Body","Three things: what changed, what it rests on, what is still open."],["Who merges","The lead of the work. An agent merges only on a named person's word and writes in the merge request on whose word."],["Record","The merge is the record. A branch, a draft, and a note are not records."]],example:"Branch claim/H-XXX-001: a new series of runs and a paragraph in the claim. The gates are green, the lead merged."},
    journal: {title:"Journal",code:'brainlab/journal',text:"A chronicle of how the lab works: a new rule, a new place, a disabled tool, with a date, newest on top.",fields:[["What goes here","What someone will look for in a month and be upset not to find."],["How it is written","A plain push to main after git pull --rebase: this is a service repository."]],example:"“The lab is installed as one tree ~/brainlab: lab sync gathers everything you can see”."},
    term: {title:"Glossary",code:'literature/glossary/',text:"The definition of an internal name: a method, run, metric, or protocol. A name is defined before its first use.",fields:[["Use","A person or an agent will decode an old record without its author."]]},
    resource: {title:"Servers",code:'brainlab/servers',text:"What matters about the hardware: what changed, what does not work, where access changed. Ephemeral state such as a free GPU is not here; it is checked with a command.",fields:[["Use","A run does not start or an address does not respond: look here first."]]},
    source: {title:"History",code:'git log · merge requests',text:"Where a record came from and how it changed: the commit, its author and time, the merge request with its discussion and the gates' verdict.",fields:[["Use","A conclusion can be checked against the history, and you can reconstruct how it changed. Nothing is stored apart from the file itself."]]},
    relations: {title:"Links",code:"[Title](path.md)",text:"Records are linked with plain relative links: both GitLab and Obsidian render them, and they lead to the same file.",fields:[["Inside a work","Claim → runs, series, derivations, figures."],["Between repositories","Work → analysis in the theme literature, by full GitLab address."],["Structure","A run lives under a claim; a series gathers runs; a derivation grounds a claim; a merge request carries a change."]]}
  };
  const typeButton = (id,title,caption='',cls='') => `<button type="button" class="mem-type ${cls}" data-record="${id}" aria-haspopup="dialog"><span>${title}</span>${caption?`<small>${caption}</small>`:''}</button>`;
  function anatomy(){
    return `<section class="mem-anatomy" data-chapter="anatomy" aria-labelledby="mem-anatomy-title">
      <header class="mem-anatomy-heading"><span class="mem-label">GitHub for ideas</span><h1 id="mem-anatomy-title" tabindex="-1">What <em>knowledge</em> is made of</h1><p>The world has GitHub for code. This is the same thing for ideas: a claim is a folder in the work repository, and everything that grounds it sits next to it as files with an address and a history.</p></header>
      <div class="mem-anatomy-map mem-diagram" data-map="anatomy">${svg}
        <article class="mem-anatomy-paper" data-point="paper-claim"><span class="mem-label">What the authors report</span>${typeButton('paperClaim',"From a paper","literature/&lt;Title&gt;.md",'mem-type-major')}<div class="mem-kind-stars" aria-label="Kinds of paper claims">${typeButton('paperEmpirical',"Result")}${typeButton('paperTheoretical',"Theory")}${typeButton('paperMethod',"Method")}${typeButton('paperDefinition',"Definition")}</div><p>An analysis in the theme literature.<br>One page per paper.</p><small class="mem-anatomy-relation">Linked from our work →</small></article>
        <article class="mem-anatomy-claim" data-point="our-claim"><span class="mem-label">What we test</span>${typeButton('hypothesis',"Our claim","claims/H-XXX/ · one code before and after testing",'mem-type-major')}<div class="mem-kind-stars" aria-label="How the claim is tested">${typeButton('empirical',"By experiment")}${typeButton('theoretical',"By derivation")}${typeButton('unspecified',"By both")}</div><div class="mem-claim-parts"><span><b>Idea</b>a one-sentence title</span><span><b>Conditions</b>when it holds</span><span><b>Falsification</b>what would refute the idea</span><span><b>Plan</b>how we will test it</span><span><b>Source</b>links to runs and papers</span><span><b>State</b>the conclusion and its reason</span></div></article>
        <article class="mem-anatomy-assessment" data-point="verdict"><span class="mem-label">How the assessment changes</span>${typeButton('assessment',"State","in the header of the same README",'mem-type-major')}<p class="mem-status-path">draft → testing<br>with the first series</p><div class="mem-status-outcomes"><span>supported</span><span>refuted</span><span>inconclusive</span></div><small>Changes only by its own criterion.<br>Every change is a merged merge request.</small></article>
        <article class="mem-anatomy-ground" data-point="run"><span class="mem-label">How it was tested</span>${typeButton('experiment',"Run","runs/E-XXX.md · written by code")}<p>What was launched, on which commit and hardware, with which numbers.</p></article>
        <article class="mem-anatomy-ground" data-point="observation"><span class="mem-label">Empirical ground ↑</span>${typeButton('evidence',"Series","series/S-XXX.md · verdict")}<p>Runs that answer one question, and what they show.</p></article>
        <article class="mem-anatomy-ground mem-proof-ground" data-point="proof"><span class="mem-label">Theoretical ground ↖</span>${typeButton('derivation',"Derivation","theory/D-XXX.md · proof")}<p>Assumptions, statement, and proof.</p></article>
      </div>
      <div class="mem-context-atlas"><span class="mem-label">Around the scientific records</span><div>${[['project',"Work","one repository"],['paper',"Theme literature","paper analyses"],['decision',"Merge request","how a record comes in"],['journal',"Journal","how we work"],['term',"Glossary","what names mean"],['resource',"Servers","where we compute"],['source',"History","git log and discussions"],['relations',"Links","how records are linked"]].map(([id,title,caption])=>typeButton(id,title,caption)).join('')}</div></div>
    </section>`;
  }

  function overview(processes){
    return `<div class="mem-overview mem-diagram" data-map="overview">${svg}
      <div class="mem-origins" data-point="origins"><span class="mem-label">All work in Atlas</span><div class="mem-source-stars">${processes.map(p=>`<div class="mem-origin" data-origin="${esc(p.id)}" style="--star:${esc(p.color)}"><i aria-hidden="true"></i><span><b>${origins[p.id][0]}</b><small>${origins[p.id][1]}</small></span></div>`).join('')}</div></div>
      <div class="mem-writer" data-point="writer">${dot}<div><b>The agent works in a clone</b><p>Task / skill <span class="mem-trigger-arrow">↘</span> <span class="mem-hook-trigger">Hook · where to write ↗</span><br>Edits files in the ~/brainlab tree and opens a merge request.</p></div></div>
      <div class="mem-main-lanes">
        <div class="mem-lane mem-literature-lane">
          ${station('paper',"From the literature","Paper","<p>An analysis in the theme literature:<br>written straight into main.</p>")}
          ${station('extract',"Analysis","Individual claims","<p>Sections → results, theorems, methods, and definitions.</p>")}
        </div>
        <div class="mem-lane mem-research-lane">
          ${station('question',"Our work","Work","<p>A repository: claims,<br>runs, manuscript, and code.</p>",'mem-project-node')}
          ${station('check',"Testing","Merge request and gates","<p>Branch → git push → merge request.<br>The gates count numbers and judge prose.</p><small>A merge by a person is the record.</small>")}
        </div>
      </div>
      <article class="mem-assertion" data-point="assertion" aria-label="What lives in GitLab: a claim">
        <header><span class="mem-label">Lab GitLab · git</span><h2>Claim</h2><p>One testable idea<br>with conditions and provenance.</p></header>
        <div class="mem-assertion-origin mem-from-paper" data-point="paper-result"><span class="mem-label">From a paper <code>literature/</code></span><p><b>What the authors claim</b></p><dl><dt>Source</dt><dd>Paper + section, table, or theorem</dd><dt>Content</dt><dd>Statement, kind, and conditions of applicability</dd></dl></div>
        <div class="mem-assertion-origin mem-from-project" data-point="project-result"><span class="mem-label">From a work <code>claims/H-XXX/</code></span><p><b>What we test</b></p><dl><dt>Grounds</dt><dd>Runs and series or a derivation</dd><dt>State</dt><dd>draft → testing → supported, refuted, or inconclusive</dd></dl><small>One code before and after testing. The conclusion follows its own criterion.</small></div>
        <footer>Plain files in git.<br>Each one has an address, a history, and review.</footer>
      </article>
      <div class="mem-personal"><span class="mem-label">The same agent keeps personal material nearby</span><div class="mem-personal-stores">
        <article class="mem-obsidian" data-point="obsidian"><span class="mem-store-mark" aria-hidden="true">◇</span><h3>Obsidian</h3><p>The same ~/brainlab tree. Notes, diary, and logs live in the notes/, daily/, and runs/ of your work and do not go to GitLab.</p></article>
        <article class="mem-palace" data-point="mempalace"><span class="mem-store-mark" aria-hidden="true">⌘</span><h3>MemPalace</h3><p>A diary of sessions, source fragments, and decisions. Context for the agent's next turn.</p></article>
      </div></div>
      <div class="mem-context"><span><b>Journal</b> how we work</span><span><b>Handbook</b> how everything is set up</span><span><b>Glossary</b> what names mean</span><span><b>Servers</b> where we compute</span><p>These are repositories of the tree too. Service ones accept a plain push to main, works only a merge request.</p></div>
    </div>`;
  }

  function ingestion(){
    return `<section class="mem-chapter" aria-labelledby="mem-ingest-title" data-chapter="ingest">
      <header class="mem-chapter-heading"><div><span class="mem-label">Who adds knowledge and how</span><h2 id="mem-ingest-title">From a paper. From a work.<br><em>From a working conversation.</em></h2></div><p>People and agents bring the materials. Every path ends in a file in git: an analysis goes straight into the theme literature, a work's knowledge comes in as a merged merge request.</p></header>
      <header class="mem-flow-heading"><h3>Paper → analysis in the theme literature</h3><p>Search and recommendation give a candidate. The theme literature gets the paper that was selected and analyzed.</p></header>
      <div class="mem-ingest-map mem-diagram" data-map="ingest">${svg}${feeders('ingest')}
        ${station('document',"Material","Paper and source",`<div class="mem-paper-sheet"><span>arXiv / DOI</span><b>Full text</b><div aria-hidden="true"><i></i><i></i><i></i><i></i></div><small>Tables · formulas · appendices</small></div><p>First we check whether an analysis already exists: across all literature/ folders of the tree at once. Zotero keeps the bibliography and the PDF.</p>${api('git grep','paper-ingest')}`)}
        ${station('reader',"The agent extracts meaning","Read and analyze",`<p>Literature Hermes or any agent with the paper-ingest skill reads the paper, checks numbers and assumptions, and separates the authors' conclusions from its own checks.</p><div class="mem-model"><span>Literature profile model</span><b>gpt-5.6-sol</b></div><p>The analysis is written straight into the theme literature repository, with no separate database.</p>`)}
        ${station('sections',"One page per paper","Write the analysis",`<div class="mem-section-stack"><span>Method</span><span>Theory</span><span>Experiments</span><span>Limitations</span></div><p>The file name is the paper title. The citation key and BibTeX are in the header, figures next to it in _attachments/.</p><small>One paper, one copy, however many works link to it.</small>${api("literature/&lt;Title&gt;.md")}`)}
        ${station('claims',"Scientific output of the analysis","Extract claims",`<p>The agent states each independent idea in its own words, keeping the conditions.</p><div class="mem-claim-fan"><div><b>Result</b><span>Metric, number, model, data</span></div><div><b>Theorem</b><span>Assumptions and the derived conclusion</span></div><div><b>Method / definition</b><span>What is proposed and what it means</span></div></div><small>The title is one sentence with no formulas and no percentages without a baseline. Code checks this.</small>${api('paper_claims_lint.py')}`)}
      </div>
      <div class="mem-ingest-end"><div class="mem-claim-schema"><span class="mem-label">Every page</span><p><b>Statement</b>${arrow}<b>Kind and conditions</b>${arrow}<b>Paper + location</b>${arrow}<b>Citation key</b></p><small>A quote is optional. A link to the source and the exact location are needed for checking.</small></div><div class="mem-claim-relations"><span class="mem-label">Link to our work</span><p>The paper's claim ${arrow} <b>our claim</b></p><small>Background · baseline · supports · contradicts · reproduces. The link is set by whoever read the paper and can justify it.</small>${api("link to the analysis")}</div></div>
      ${projectIngestion()}${checkpointIngestion()}
      <div class="mem-save-route"><h3>One order of recording</h3><ol><li><b>Find what is already recorded</b><p>git pull and a search over the tree. A free claim code is taken from the clone: the highest number, not the count.</p></li><li><b>Open a merge request</b><p>Branch claim/H-XXX, commit, git push: the merge request opens by itself and is assigned to the lead of the work.</p></li><li><b>Pass the gates and the merge</b><p>The gates count numbers and judge prose within a minute. A person merges, and the merge is the record.</p></li></ol></div>
    </section>`;
  }

  function projectIngestion(){
    return `<div class="mem-project-flow"><header class="mem-flow-heading"><h3>Work → our claims and grounds</h3><p>A work is a repository. Its materials are sorted into claim folders, and the manuscript and code are attached next to them.</p></header>
      <div class="mem-project-map mem-diagram" data-map="project">${svg}${feeders('project')}
        ${station('workspace',"Research materials","The work and its place",`<div class="mem-project-sheet"><span>WORK</span><b>Our research</b><div><span>claims/: knowledge</span><span>paper/ and code/</span><span>calls/ and socials/</span></div></div><p>The work's path in the tree matches its address in GitLab: direction, theme, work.</p>${api('lab sync','lab here')}`)}
        ${station('claim',"What we want to find out","Formulate",`<p>One testable idea: a one-sentence title, conditions, the expected result, and a falsification criterion.</p><div class="mem-section-stack"><span>Tested by experiment</span><span>Tested by derivation</span></div><small>A claim gets a code at the start and keeps it after testing.</small>${api('claims/H-XXX/README.md')}`)}
        ${station('grounds',"Two forms of evaluation","Lay down the grounds",`<div class="mem-research-branches"><div><b>Run → series</b><p>The run page is written by the lab_run.py recorder: hyperparameters, numbers, commit, hardware. A series answers one question with a verdict.</p>${api('runs/E-XXX.md','series/S-XXX.md')}</div><div><b>Mathematical derivation</b><p>Statement from scratch → assumptions → proof.</p>${api('theory/D-XXX.md')}</div></div>`)}
        ${station('assessment',"Scientific conclusion","Assess the claim",`<p>The grounds are compared with the original criterion, and contradictions are named out loud.</p><div class="mem-verdicts"><b>Supported</b><b>Refuted</b><b>Inconclusive</b></div><small>The state and the conclusion are written in the README of the same claim and come in as a merge request.</small>${api('git push','lab checks')}`)}
      </div>
      <div class="mem-operational-paths"><span><b>The way of working changed</b>${arrow}<span>Journal</span>${api('brainlab/journal')}</span><span><b>How a tool works</b>${arrow}<span>Handbook</span>${api('brainlab/handbook')}</span><span><b>Server, access, failure</b>${arrow}<span>Servers</span>${api('brainlab/servers')}</span></div>
      <p class="mem-flow-note">Finished results are added to existing claims rather than starting new ones. A call analysis brings ideas and agreements; an expected result stays a hypothesis until tested.</p>
    </div>`;
  }

  function checkpointIngestion(){
    return `<div class="mem-checkpoint-flow"><header class="mem-flow-heading"><h3>Hook → where to record the outcome of a turn</h3><p>One more entry into the same base: save what is useful from the work, even without an explicit command to record.</p></header>
      <div class="mem-hook-map mem-diagram" data-map="hook">${svg}
        ${station('session',"During work","Context accumulates","<div class=\"mem-session-lines\"><span>A result is obtained</span><span>A limitation is found</span><span>The next step is chosen</span></div><p>Codex, Claude Code, and autonomous Hermes agents encounter facts the next agent will need.</p>")}
        ${station('checkpoint',"Automatic hint","The hook triggers","<div class=\"mem-cadence\"><span><b>Codex / Claude Code</b>names where to write at the end of a turn</span><span><b>Autonomous Hermes</b>every 5 working turns</span></div><small>The place is chosen from the repository descriptions on the site. The hook names the address but writes nothing and merges nothing.</small>")}
        ${station('curator',"The agent acts","Select and save","<p>The agent reads the context, picks what is durable, and writes into the clone of the right repository in the tree.</p><small>The base gets what someone will look for in a month. If there is nothing to record, nothing extra appears.</small>")}
        ${station('ack',"Confirmation","Get it into main","<div class=\"mem-checkpoint-stores\"><span><b>GitLab</b>knowledge, branch, merge request</span><span><b>Obsidian</b>notes in notes/</span><span><b>MemPalace</b>context and history</span></div><small>The hook sees unsaved and unpushed changes in the clone and reminds you before an edit gets lost.</small>")}
      </div><p class="mem-flow-note">The hint is advice, not an order: the agent chooses the place. Neither the hook nor the gates replace scientific assessment and a merge by a person.</p>
    </div>`;
  }

  function analysisScenarios(){
    const cases=[
      ['compare',"Compare results","Which test provides stronger support?",`<b>Runs and series</b>${api('runs/','series/')}`,`<b>The agent compares protocols</b><small>Data, baseline, seeds, units, and limitations</small>`,`<b>Comparisons and plots</b><small>results-analysis · academic-plotting, when the underlying data is available</small>`, "Numbers are compared under matching conditions. Missing repeats and metrics remain explicit gaps."],
      ['assess',"Check a conclusion","What is already supported?",`<b>Claim and criterion</b>${api('claims/H-XXX/README.md')}`,`<b>Series or a derivation</b>${api('series/','theory/')}`,`<b>Assessment with grounds</b><small>The state and the limits of the conclusion</small>`, "A new assessment is an edit to the claim README through a merge request; the gates' verdict arrives within a minute, and the lead merges."],
      ['literature-check',"Compare with the literature","Where do our results differ?",`<b>Our claim</b>${api("grep over literature/")}`,`<b>The paper's claims</b>${api("literature/&lt;Title&gt;.md")}`,`<b>Agreement or contradiction</b><small>Accounting for data, assumptions, and scope of applicability</small>`, "Search suggests neighboring works. The substantive link is set by whoever read the paper; similar text does not prove support."],
      ['gaps',"Find open issues","What is missing for a conclusion?",`<b>Work state</b>${api('lab checks')}`,`<b>Check the gap you found</b><small>No falsification criterion, no series verdict, or a number without an address</small>`,`<b>A clear next step</b><small>What to record, clarify, or test</small>`, "The gates catch omissions by the canon. A person judges the scientific quality at merge time."],
      ['resume',"Resume work","What has changed since last time?",`<b>What reached main</b>${api('git pull','git log')}`,`<b>Merge requests and issues</b>${api('lab pull','lab tasks')}`,`<b>Change summary</b><small>New results, decisions, and remaining questions</small>`, "The session-start hook runs git pull by itself and prints what changed, what is open, and what is assigned to you."]
    ];
    return `<div class="mem-analysis-scenarios"><header class="mem-flow-heading"><h3>After the search, make sense of the result</h3><p>The tree gives files and links. A researcher or an agent checks the meaning, compares the data, and formulates a conclusion.</p></header>${cases.map(([id,label,title,a,b,c,note])=>`<article class="mem-analysis-case" data-scenario="${id}"><div><span class="mem-label">${label}</span><h4>${title}</h4></div><div class="mem-walk-path"><span>${a}</span>${arrow}<span>${b}</span>${arrow}<span>${c}</span></div><p>${note}</p></article>`).join('')}<div class="mem-useful-context"><span><b>Who leads the work</b>${api("“Leads” in the README")}</span><span><b>Which servers are available</b>${api('brainlab/servers')}</span><span><b>What the terms mean</b>${api('literature/glossary/')}</span></div></div>`;
  }

  function retrieval(){
    return `<section class="mem-chapter" aria-labelledby="mem-search-title" data-chapter="search">
      <header class="mem-chapter-heading"><div><span class="mem-label">Working with accumulated knowledge</span><h2 id="mem-search-title">Find. Compare.<br><em>Understand what follows from the results.</em></h2></div><p>All of the lab's knowledge sits on your machine, so you can search with ordinary tools: grep, git log, Obsidian search, and GitLab search.</p></header>
      <div class="mem-readers"><span class="mem-label">Who uses the base</span><span>Researcher</span><span>Codex / Claude Code</span><span>Literature Hermes</span><span>Experiment Hermes</span><small>Question → ~/brainlab tree → files with an address and history</small></div>
      <div class="mem-search-map mem-diagram" data-map="search">${svg}
        ${station('query',"Start with a question","Search by query",`<blockquote>“What is known about the method and its limitations?”</blockquote><p>The whole lab, one theme, or one work: these are just folders of the tree.</p>${api('lab sync')}`)}
        ${station('words',"Text","By words","<p>git grep and ripgrep go through the tree in a fraction of a second. Obsidian search reads the same files.</p>")}
        ${station('vectors',"Site","GitLab search","<p>Group search on the site, for when the tree is not at hand. You see exactly what you have access to.</p>")}
        ${station('merge',"Literature","Across all themes at once","<p>An analysis lives in the theme where it was filed, not where it is needed. So you have to search all literature/ folders at once.</p><small>By citation key or paper title.</small>")}
        ${station('graph',"Context","Follow the links","<p>From a claim to its runs, series, derivations, and paper analyses.</p><small>Both Obsidian and GitLab render relative links.</small>")}
        ${station('rerank',"History","git log and merge requests","<p>Who changed a record, when, and why: in the commit and in the merge request discussion, together with the gates' verdict.</p>")}
        ${station('answer',"Result","A file with an address","<ul class=\"mem-answer-fields\"><li>Path and code</li><li>Statement</li><li>Work and theme</li><li>Related files</li></ul><p>The answer points to a file and a commit: anyone with access can open it by its address.</p>")}
      </div>
      <div class="mem-search-settings"><p><b>No separate index:</b> search runs over the files themselves. There is no second copy, so nothing can drift from the truth.</p><p><b>Freshness:</b> lab sync pulls the whole tree, and session start runs git pull in the current work by itself.</p></div>
      ${analysisScenarios()}
      <div class="mem-walks"><h3>Start from a theme, a work, or a known record</h3>
        <div class="mem-walk" data-route="theme"><div><span class="mem-label">Explore a direction</span><h4>From a theme to works</h4></div><div class="mem-walk-path"><span><b>Direction → themes</b>${api("~/brainlab/&lt;direction&gt;/")}</span>${arrow}<span><b>Theme page</b><small>Subject, works, who leads</small></span>${arrow}<span><b>Works and claims</b><small>Our own science + literature</small></span></div></div>
        <div class="mem-walk" data-route="library"><div><span class="mem-label">Browse the library</span><h4>From a theme to a paper</h4></div><div class="mem-walk-path"><span><b>Theme → literature</b>${api("&lt;theme&gt;/literature/")}</span>${arrow}<span><b>Subtopic → papers</b><small>The literature README is organized by subtopic</small></span>${arrow}<span><b>Paper → claims</b>${api("literature/&lt;Title&gt;.md")}</span></div><p>The literature README is assembled from the pages themselves: full titles, authors, and a summary, untruncated.</p></div>
        <div class="mem-walk" data-route="known"><div><span class="mem-label">You have a specific object</span><h4>From a work or code</h4></div><div class="mem-walk-path"><span><b>Work</b>${api("lab here &lt;work&gt;")}</span>${arrow}<span><b>Front page → claim</b>${api('README.md')}</span>${arrow}<span><b>Complete record</b>${api('claims/H-XXX/')}</span></div><p>The work's front page answers in one order: what we claim, what it has been tested with, what is open.</p></div>
        <div class="mem-walk" data-route="evidence"><div><span class="mem-label">Check a ground</span><h4>From a claim to its test</h4></div><div class="mem-walk-path"><span><b>Known record</b><small>Code H-XXX</small></span>${arrow}<span><b>Runs and series</b>${api("page links")}</span>${arrow}<span><b>Change history</b>${api('git log -- claims/H-XXX')}</span></div><p>These are explicit links and git history. Their provenance can be checked, and state changes can be read from the commits.</p></div>
        <div class="mem-walk" data-route="neighbors"><div><span class="mem-label">Widen the question</span><h4>Find neighboring ideas</h4></div><div class="mem-neighbor-paths"><span><b>Shared terms</b>${api('literature/glossary/')}<small>Topical proximity, not a proven link</small></span><span><b>Literature around the claim</b>${api("grep over literature/")}<small>By statement and mechanism</small></span><span><b>Similar records before a write</b>${api("grep over claims/")}<small>Duplicate candidates; the agent decides</small></span></div></div>
      </div>
      <div class="mem-vector-cache"><div><span class="mem-label">Why this way</span><h3>One place, no copies</h3><p>Knowledge lives in git and only in git: no database on the side, no publishing from one into the other.</p></div><div class="mem-cache-path"><span><b>File</b><small>Edit in the clone</small></span>${arrow}<span><b>Branch</b><small>claim/H-XXX</small></span>${arrow}<span><b>Merge request</b><small>Gates and discussion</small></span>${arrow}<span><b>main</b><small>Merged by a person</small></span></div><p>A shared base where any agent writes anything is useless: nobody in it says “no”. A file in git goes through a merge request, and a person accepts it. What is merged into main is the lab's knowledge.</p></div>
    </section>`;
  }

  function accessGuide(){
    return `<section class="mem-chapter mem-access" id="lab-access" aria-labelledby="mem-access-title">
      <header class="mem-chapter-heading"><div><span class="mem-label">Person · role · work</span><h2 id="mem-access-title">Access to the lab.<br><em>Rights in your own work.</em></h2></div><p>One GitLab account per person. The role at the lab root is the floor for the whole tree: it can be raised in any theme and work, but not lowered.</p></header>
      <div class="mem-access-steps"><span>Full name, username, and referrer</span><i>→</i><span>Requested role</span><i>→</i><span>Any lead approves</span><i>→</i><span>Account, git key, and the ~/brainlab tree</span></div>
      <div class="mem-access-roles mem-access-roles-4">
        <article><span class="mem-label">Guest</span><h3>Guest</h3><p>Sees the tree of directions, themes, and works, and all the literature. The contents of works are closed. Everyone starts here.</p></article>
        <article><span class="mem-label">Reporter</span><h3>Student</h3><p>Reads all works in full: claims, runs, manuscripts, discussions. Cannot write, can discuss.</p></article>
        <article><span class="mem-label">Developer</span><h3>Researcher</h3><p>Student rights plus work: branches and merge requests in any work, new works of their own in any theme. Cannot merge.</p></article>
        <article><span class="mem-label">Maintainer</span><h3>Lead</h3><p>Merges merge requests in all works, creates themes, and owns those where they lead a work. Decides access requests to their own places.</p></article>
      </div>
      <div class="mem-access-project"><h3>Every work has its own people</h3><dl><div><dt>Lead <code>Owner</code></dt><dd>Merges merge requests and decides access requests to their work.</dd></div><div><dt>Team <code>Developer</code></dt><dd>Branches and merge requests: those who do the work.</dd></div><div><dt>Reader <code>Reporter</code></dt><dd>Sees the whole work, does not write.</dd></div></dl><p>To join a theme or a work, use the Request access button on its page: the request goes by Telegram to whoever leads it. Who leads and who is on the team is recorded in the “Leads” and “Team” lines of the work's README.</p></div>
      <footer><a href="https://t.me/brainlab_server_access_bot" target="_blank" rel="noopener noreferrer">Open the access bot ↗</a><p>Press “Get access”, select the knowledge base in the list of resources, and choose a role. The role takes effect after approval; then one installer sets up Obsidian and builds the ~/brainlab tree with the lab sync command.</p></footer>
    </section>`;
  }

  function anyTeam(){
    return `<section class="mem-chapter" aria-labelledby="mem-team-title" data-chapter="team">
      <header class="mem-chapter-heading"><div><span class="mem-label">Not only for science</span><h2 id="mem-team-title">A shared GitLab for ideas,<br><em>for any team.</em></h2></div><p>The setup does not know that scientific claims are inside. Product, analytics, market research, or engineering: wherever decisions rest on verifiable grounds, the same order works.</p></header>
      <div class="mem-save-route mem-save-route-4"><h3>Four rules</h3><ol><li><b>A work is a repository</b><p>Each has its own place, its own people, and its own history. Rights are inherited down the tree, as with GitLab groups.</p></li><li><b>An idea is a folder</b><p>A claim and everything that grounds it sit next to each other as files. No form for form's sake: the page is read by eye.</p></li><li><b>A record is a merge</b><p>Agents and people propose, the gates check numbers and prose, a person accepts. Junk does not get into the base.</p></li><li><b>Everyone has the tree</b><p>The whole base sits locally as one tree and opens in Obsidian. Work is plain git: edit, branch, push.</p></li></ol></div>
    </section>`;
  }

  function render(p, processes){
    return `<div class="process-shell memory-observatory" style="--accent:#b9ff66">
      <header class="mem-header"><div><button class="back-button" data-back type="button">← All of Atlas</button><span class="mem-coordinate">BRAIn Lab / Lab GitLab</span></div></header>
      ${anatomy()}
      <header class="mem-chapter-heading mem-overview-heading"><div><span class="mem-label">Where knowledge comes from</span><h2>How work becomes <em>knowledge</em></h2></div></header>
      <section class="mem-first-map" aria-label="Overview: sources, claims, and personal memory" data-chapter="overview">${overview(processes)}<div class="mem-practice-notes"><p><b>When it is saved:</b> as the work goes. At the end of a turn the hook names where to write, and the agent edits the clone and submits.</p><p><b>Where tasks are:</b> shared ones are issues of the work repository in GitLab, personal ones are in Operon. The session-start hook shows what is assigned to you.</p></div></section>
      ${ingestion()}${retrieval()}${accessGuide()}${anyTeam()}
      <footer class="mem-footer"><p>The diagrams show how the system is built, without data from the private base. Checked against the base canon on 18-10-2026.</p><details class="mem-tools"><summary>Skills and tools of this layer</summary><div>${p.tools.map(t=>`<button type="button" data-skill="${esc(t.id)}">${esc(t.title)}</button>`).join('')}</div></details><a href="https://github.com/brain-lab-research/claude-brainlab/blob/main/docs/onboarding.md" target="_blank" rel="noopener noreferrer">How to set it up ↗</a></footer>
      <dialog class="skill-dialog" aria-labelledby="skill-dialog-title"></dialog>
      <dialog class="skill-dialog mem-record-dialog" aria-labelledby="mem-record-title"></dialog>
    </div>`;
  }

  const edges={
    overview:[['writer','paper','paper'],['writer','question','project'],['paper','extract','paper'],['question','check','project'],['extract','paper-result','paper'],['check','project-result','project']],
    ingest:[['document','reader','paper'],['reader','sections','paper'],['sections','claims','paper']],
    project:[['workspace','claim','project'],['claim','grounds','project'],['grounds','assessment','project']],
    hook:[['session','checkpoint','violet'],['checkpoint','curator','violet'],['curator','ack','project']],
    search:[['query','words','paper'],['query','vectors','violet'],['words','merge','paper'],['vectors','merge','violet'],['merge','graph','project'],['graph','rerank','project'],['rerank','answer','project']]
  };
  let observer;
  function drawAnatomy(map){
    const box=map.getBoundingClientRect(),surface=map.querySelector('.mem-connections');
    if(!box.width||!box.height)return;
    const rect=id=>{const r=map.querySelector(`[data-point="${id}"]`).getBoundingClientRect();return {l:r.left-box.left,r:r.right-box.left,t:r.top-box.top,b:r.bottom-box.top,x:r.left-box.left+r.width/2}};
    const line=(a,b,color,vertical=false)=>{
      const from=rect(a),to=rect(b);let d;
      if(matchMedia('(max-width:760px)').matches){
        const rail=5;d=`M${from.l+5},${from.b+5} H${rail} V${to.t-10} H${to.l+5}`;
      }else if(vertical){
        const y=(from.t+to.b)/2;d=`M${from.x},${from.t-8} V${y} H${to.x} V${to.b+8}`;
      }else{
        d=`M${from.r+7},${from.t+57} H${to.l-7}`;
      }
      return `<path class="mem-line-${color}" data-edge="${a}:${b}" d="${d}"/>`;
    };
    surface.setAttribute('viewBox',`0 0 ${box.width} ${box.height}`);
    surface.innerHTML=matchMedia('(max-width:760px)').matches?'':line('paper-claim','our-claim','paper')+line('our-claim','verdict','project')+line('run','observation','project')+line('observation','our-claim','project',true)+line('proof','our-claim','violet',true);
  }
  function draw(map){
    if(map.dataset.map==='anatomy'){drawAnatomy(map);return}
    const box=map.getBoundingClientRect();if(!box.width||!box.height)return;
    const svg=map.querySelector('.mem-connections'),kind=map.dataset.map,compact=matchMedia('(max-width:760px)').matches;
    const bounds=id=>map.querySelector(`[data-point="${id}"]`).getBoundingClientRect();
    const path=(from,to,color)=>{
      const a=bounds(from),b=bounds(to);let d;
      if(kind==='overview'&&from==='writer'){
        if(matchMedia('(max-width:1100px)').matches)return '';
        const rail=b.left-box.left-16,ay=a.top-box.top+11,bx=b.left-box.left+4,by=b.top-box.top+35;
        d=`M${a.left-box.left+4},${ay} H${rail} V${by} H${bx}`;
      }else if(b.left>=a.right-3){
        const node=map.querySelector(`[data-point="${from}"]`),heading=node.querySelector('h3')?.getBoundingClientRect();
        const ax=(heading?Math.min(a.right,heading.right+12):a.right)-box.left,ay=a.top-box.top+35,bx=b.left-box.left-2,by=b.top-box.top+(to.endsWith('result')?23:35),mid=(ax+bx)/2;
        d=`M${ax},${ay} C${mid},${ay} ${mid},${by} ${bx},${by}`;
      }else{
        const ax=a.left-box.left+12,ay=a.bottom-box.top+5,bx=b.left-box.left+12,by=b.top-box.top-8;
        const rail=compact?3:Math.min(ax,bx)-17;
        d=`M${ax},${ay} H${rail} V${by-6} Q${rail},${by} ${rail+6},${by} H${bx}`;
      }
      return `<path data-edge="${from}:${to}" class="mem-line-${color}" d="${d}" marker-end="url(#mem-arrow-${kind}-${color})"/>`;
    };
    let lines=edges[kind].map(e=>path(...e)).join('');
    if(inlets[kind]){
      const target=kind==='ingest'?'document':'workspace',b=bounds(target),group=map.querySelector('.mem-feeders').getBoundingClientRect(),bx=b.left-box.left+4,by=b.top-box.top+35;
      for(const [id] of inlets[kind]){
        const source=`${kind}-via-${id}`,a=bounds(source),ax=a.left-box.left+4,ay=a.top-box.top+8,rail=compact?group.left-box.left-10:group.bottom-box.top+20;
        const d=compact?`M${ax},${ay} H${rail} V${by} H${bx}`:`M${ax},${ay+8} V${rail-6} Q${ax},${rail} ${Math.max(bx,ax-6)},${rail} H${bx} V${by}`;
        lines+=`<path data-edge="${source}:${target}" class="mem-line-${kind==='ingest'?'paper':'project'} mem-line-feeder" d="${d}" marker-end="url(#mem-arrow-${kind}-${kind==='ingest'?'paper':'project'})"/>`;
      }
    }
    if(kind==='overview'&&matchMedia('(min-width:1101px)').matches){
      const b=bounds('writer');map.querySelectorAll('[data-origin]').forEach(el=>{const a=el.getBoundingClientRect(),ax=a.right-box.left,ay=a.top-box.top+a.height/2,bx=b.left-box.left+4,by=b.top-box.top+11,mid=(ax+bx)/2;lines+=`<path class="mem-line-input" d="M${ax},${ay} C${mid},${ay} ${mid},${by} ${bx},${by}"/>`});
      for(const id of ['obsidian','mempalace']){
        const a=bounds(id),rail=b.left-box.left-16,x=a.left-box.left+7,y=a.top-box.top;
        lines+=`<path data-edge="writer:${id}" class="mem-line-private" d="M${b.left-box.left+4},${b.top-box.top+11} H${rail} V${y-6} H${x} V${y+10}"/>`;
      }
    }
    const colors={paper:'#9ec9d8',project:'#c5df94',violet:'#bba8e1'};
    svg.setAttribute('viewBox',`0 0 ${box.width} ${box.height}`);
    svg.innerHTML=`<defs>${Object.entries(colors).map(([c,fill])=>`<marker id="mem-arrow-${kind}-${c}" viewBox="0 0 6 6" refX="6" refY="3" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0 L6 3 L0 6" fill="none" stroke="${fill}"/></marker>`).join('')}</defs>${lines}`;
  }
  function bind(root){
    observer?.disconnect();const scope=root.querySelector('.memory-observatory');if(!scope)return;
    const maps=[...scope.querySelectorAll('.mem-diagram')];
    observer=new ResizeObserver(()=>maps.forEach(draw));maps.forEach(m=>observer.observe(m));
    requestAnimationFrame(()=>maps.forEach(draw));
    const dialog=scope.querySelector('.mem-record-dialog');let trigger,savedScroll;
    scope.querySelectorAll('[data-record]').forEach(button=>button.addEventListener('click',()=>{
      const entry=recordGuide[button.dataset.record];if(!entry)return;
      trigger=button;savedScroll={left:scrollX,top:scrollY,behavior:'instant'};
      dialog.innerHTML=`<button type="button" class="mem-record-close" aria-label="Close description">×</button><span class="mem-label">How the base is built <code>${esc(entry.code)}</code></span><h2 id="mem-record-title" tabindex="-1">${esc(entry.title)}</h2><p>${esc(entry.text)}</p><dl>${entry.fields.map(([title,text])=>`<div><dt>${esc(title)}</dt><dd>${esc(text)}</dd></div>`).join('')}</dl>${entry.example?`<aside><span class="mem-label">Illustrative example</span><p>${esc(entry.example)}</p></aside>`:''}`;
      dialog.querySelector('.mem-record-close').onclick=()=>dialog.close();dialog.showModal();dialog.scrollTop=0;dialog.querySelector('h2').focus({preventScroll:true});window.scrollTo(savedScroll);
    }));
    dialog.addEventListener('click',event=>{if(event.target!==dialog)return;const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close()});
    dialog.addEventListener('close',()=>{if(!dialog.isConnected||root.hidden)return;trigger?.focus({preventScroll:true});if(savedScroll)window.scrollTo(savedScroll)});
  }
  return {render,bind};
})();
