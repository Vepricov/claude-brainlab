/* Explanatory maps contain no private records: they show how the git knowledge base works, not its contents. */
window.LAB_MEMORY_MAP = (() => {
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const origins = {
    projects:["Project","its own page and people"],
    literature:["Literature","Jev selects, Claude reviews"],
    ideation:["Ideas","hypotheses with a criterion"],
    calls:["Calls","recording, transcript, breakdown"],
    experiments:["Experiments","Hermes runs the experiments"],
    results:["Results","comparisons and plots"],
    writing:["Writing and review","text and a strict review"],
    presentation:["Publication","posts and slides"]
  };
  const dot = '<i class="mem-star" aria-hidden="true"></i>';
  const arrow = '<i class="mem-inline-arrow" aria-hidden="true">→</i>';
  const station = (id, label, title, body, extra='') => `<article class="mem-station ${extra}" data-point="${id}">${dot}<span class="mem-label">${label}</span><h3>${title}</h3>${body}</article>`;
  const api = (...names) => `<span class="mem-api-names">${names.map(n=>`<code>${n}</code>`).join(' · ')}</span>`;
  const svg = '<svg class="mem-connections" aria-hidden="true"></svg>';
  const inlets = {
    ingest:[['jev',"Jev","selects against our works"],['search','paper-search',"fresh papers on the topic"],['alphaxiv','alphaXiv / arXiv',"“Want to read” from a phone"],['social',"Colleagues","Share a paper"],['reader',"Researcher","adds to the reading queue"]],
    project:[['hermes',"Hermes","runs experiments on the server"],['agents','Claude Code',"Code, checks, and conclusions"],['call','Brain Call',"call decisions"],['person',"Researcher","idea and criterion"]]
  };
  const feeders = kind => `<div class="mem-feeders" aria-label="${kind==='ingest'?"Where papers come from":"Where work materials come from"}">${inlets[kind].map(([id,title,caption])=>`<div class="mem-inlet" data-inlet="${kind}" data-point="${kind}-via-${id}"><b>${title}</b><small>${caption}</small></div>`).join('')}</div>`;

  // Checked against lab-knowledge canon.md, claim-page.md, what-is-a-claim.md and handbook, 19-10-2026.
  const recordGuide = {
    hypothesis: {title:"Claim",code:"claim folder",text:"One testable idea about a method, together with everything used to test it. It is a folder in the work's repository: the claim page, and next to it runs, series, derivations and figures. A work has a handful of these, not a hundred.",fields:[["Title","One sentence you can read aloud. The method is named, the verb is in place."],["Why we think so","The mechanism: why the effect should exist at all."],["Test conditions","Where the claim must hold."],["What refutes it","Written before the test. Without this section it is a note, not a claim."],["How it was tested · Conclusion","The series and derivations under the claim, a paragraph on each, and the status."]],example:"A claim: “Warmup length affects the final loss only through whether AdamW's second moment has gathered statistics by the time the peak lr is reached”. Not a claim: “halving warmup does not hurt loss at 124M”. That is a measurement."},
    empirical: {title:"A claim, not a measurement",code:"canon rule",text:"If an idea stops being true when a number, a table or a checkpoint changes, it is not a claim. A claim speaks about a mechanism and the domain where it acts, and still makes sense a year later.",fields:[["Claim","A dynamic Fisher approximation beats the SOAP heuristic by more the longer the horizon."],["A brick beneath it","At 210M over 80k steps DyKAF is 0.010 below SOAP. This is a run under the claim, not a folder of its own."]]},
    theoretical: {title:"Short record codes",code:"codes",text:"Every record has its own short code with a type letter. One search command finds the record by it, and a link from a chat leads straight to the file.",fields:[["Claim","Letter H"],["Series and run","Letters S and E"],["Derivation and figure","Letters D and F"]]},
    unspecified: {title:"First read what already exists",code:"no duplicates",text:"All of a work's claims sit in one folder, and reading them takes one command. A new one is created only when none of the existing ones covers it. Otherwise the existing one is edited.",fields:[["Why it matters","Two pages claiming the same thing in different words look like two pieces of knowledge. This is the most common way a base gets corrupted, worse than a wrong number: an error is visible, a duplicate is not."]]},
    paperClaim: {title:"Paper claim",code:"“What the paper claims”",text:"A section inside the review of someone else's paper. No folders and no codes: we did not reproduce it, and what was tested must not be put on par with what was read. One to three claims.",fields:[["What it rests on","Only numbers printed in the paper, with their location: table, figure."],["Setup","Model, data, budget, number of runs, as in the paper."],["What refutes it","Our threshold and our control experiment."],["Our assessment","What to trust. The key line: without it the section becomes an ad for someone else's work."]],example:"Check of 07-10-2026: 450 numbers verified across seventeen reviews, two real errors found, both in “what it rests on”."},
    paperEmpirical: {title:"What it rests on",code:"number check",text:"Only numbers from the paper itself belong here. A script looks up every number in the paper's text and complains if it is not there.",fields:[["Use","A reported result can be opened in the source table and compared with your own run."]],example:"Instead of the printed 28.7 and 23.7, the review had the range “23.7-31.3”. The check caught it."},
    paperTheoretical: {title:"Setup",code:"setup",text:"The authors' settings as printed: model, data, budget, how many runs. Without them the result cannot be carried over to your own task.",fields:[["Use","You can see under which conditions the authors got the result and whether they match ours."]]},
    paperMethod: {title:"What refutes it",code:"what refutes it",text:"What has to be measured for the paper's claim to fall. The numbers here are ours by construction: our threshold and our control experiment.",fields:[["Use","Reading immediately yields a test plan, if the paper matters for our work."]]},
    paperDefinition: {title:"Our assessment",code:"our assessment",text:"What to trust in the paper: how many seeds, whether there are confidence intervals, whether the gap is smaller than the noise, whether the compared methods were tuned equally.",fields:[["Rule","Our remark is not attributed to the authors. Our arithmetic goes here, not in “what it rests on”."]]},
    assessment: {title:"Claim state",code:"status",text:"Changes only by the criterion written into the claim itself before the test. One successful series does not make a claim supported if the criterion demanded more.",fields:[["Before a conclusion","Draft, then “under test” once the first series appears."],["After testing","Supported, refuted or inconclusive. “Not established” is a legitimate outcome."],["Don't confuse","The refutation criterion did not fire — that means “not refuted”, not “supported”."],["What supports it","A met criterion, our own recomputation, or a number in our paper that passed an external milestone: submission, acceptance, a delivered report."]],example:"The numbers come from someone else's report, and the refutation criterion did not fire. Status: inconclusive, and the series says what was missing."},
    experiment: {title:"Run",code:"run page",text:"Numbers are written by code, not by a person. The recorder wraps training before launch and writes the run page itself.",fields:[["Code writes","Hyperparameters, final numbers, environment, commit, hardware, the full metrics log."],["The agent writes","One thing: what these numbers show. Not a retelling of the table, but an observation."],["Where a number lives","Every number has a place where you can see it with your own eyes: a log or a W&B page."],["Forgot to wrap it","The recorder adopts a run already in progress and marks the page as adopted."]]},
    evidence: {title:"Series",code:"an answer to a question",text:"Not a folder for runs, but an answer to one question. Without a verdict a series reads as an abandoned test.",fields:[["Question","One, in your own words. Two questions, two series."],["Shared setup and axis","What is the same across all runs and what was varied."],["Runs","One row per run with a link to its page. Runs that are not comparable do not go into a series."],["Verdict","Mandatory. “No win established” is legitimate, an empty field is not."]],example:"Series: does the WSD gain transfer from 124M to 210M. Three runs, a figure from them, a paragraph on the claim page."},
    derivation: {title:"Derivation",code:"theory",text:"The mathematical basis of a claim. One file per storyline, not per lemma.",fields:[["Contents","A statement that reads from scratch, and a “Proof” section."],["No run numbers","A theorem statement contains no numbers from a specific run."],["Where it applies","A derivation survives only if the place where it is applied is named."]]},
    project: {title:"Work",code:"direction / topic / work",text:"One work, one repository. Knowledge lives in it as claim folders and nowhere else.",fields:[["In GitLab","Claims, manuscript, code, posts and call breakdowns."],["Stays on the machine","Notes, the diary and local logs are excluded from git. Personal and shared sit in one Obsidian window, but only the shared part leaves."],["People","The “Leads” and “Team” lines on the work's front page. The work lead merges proposals."]]},
    paper: {title:"Theme literature",code:"a page per paper",text:"One page per paper, the file named after the paper. Inside: the review, figures and BibTeX with the citation key.",fields:[["Use","A paper is reviewed once and read by every work in the topic."],["Citations","A paper can be cited only by a key already in the work's bibliography: otherwise the edit will not be saved."]]},
    decision: {title:"Merge request",code:"an edit for review",text:"A way of writing, not a stage of knowledge. One proposal per claim, with everything about it inside.",fields:[["A three-part body","What changed and why. What disappeared and why. How it was checked."],["Who merges","The work lead. An agent only on a person's word in the same turn, and it writes in the proposal whose word it was."],["What is not merged","Someone else's work, failed checks, unresolved comments."]]},
    journal: {title:"Journal",code:"chronicle",text:"A dated chronicle of how we work: a new rule, a new place, a tool switched off. Scientific results do not go here, they live in works.",fields:[["How it is written","Directly, without a proposal: it is a chronicle, not knowledge."]],example:"19-10-2026: Jev selects papers against the descriptions of our works, but at judging “is this a good paper at all” he is worse than a coin flip."},
    term: {title:"Handbook",code:"how things work",text:"How the tools and skills work right now. An outdated answer in the handbook is a bug, an outdated entry in the journal is history.",fields:[["Use","A new person or agent learns how to work without the author at hand."]]},
    resource: {title:"Servers",code:"where we compute",text:"Only what is important and lasting: what changed, what is broken, where access changed.",fields:[["Not here","Whether a GPU is free right now and who is computing what. That is checked with a command."]]},
    source: {title:"History",code:"edit history",text:"Every edit is a commit with an author and a time, every merge is recorded with whoever approved it. Nothing is rewritten silently.",fields:[["Find where a number came from","The history shows in which edit a number appeared and who merged it."],["Deletion check","The checks compare deleted files against the proposal's description: unexplained loss is visible."]]},
    relations: {title:"The canon",code:"canon",text:"55 named rules. Each has a “checked by” line: which code enforces it, or that no machine checks it.",fields:[["Examples","Code writes the numbers. Without a refutation criterion it is not a claim. Status changes only by the criterion. A record is a merge. There are no made-up numbers."],["One copy","A separate check catches a second copy of a rule: the canon never diverges from itself."]]}
  };
  const typeButton = (id,title,caption='',cls='') => `<button type="button" class="mem-type ${cls}" data-record="${id}" aria-haspopup="dialog"><span>${title}</span>${caption?`<small>${caption}</small>`:''}</button>`;
  function anatomy(){
    return `<section class="mem-anatomy" data-chapter="anatomy" aria-labelledby="mem-anatomy-title">
      <header class="mem-anatomy-heading"><span class="mem-label">How shared memory is built</span><h1 id="mem-anatomy-title" tabindex="-1">What <em>knowledge</em> is made of</h1><p>The lab's knowledge lives in git. A claim is a folder in the work's repository, with everything used to test it next to it.</p></header>
      <div class="mem-anatomy-map mem-diagram" data-map="anatomy">${svg}
        <article class="mem-anatomy-paper" data-point="paper-claim"><span class="mem-label">What the authors report</span>${typeButton('paperClaim',"From a paper","review section",'mem-type-major')}<div class="mem-kind-stars" aria-label="What a paper's claim is made of">${typeButton('paperEmpirical',"What it rests on")}${typeButton('paperTheoretical',"Setup")}${typeButton('paperMethod',"What refutes it")}${typeButton('paperDefinition',"Our assessment")}</div><p>The paper's numbers with their location.<br>A script checks them against the text.</p><small class="mem-anatomy-relation">We compare with our results →</small></article>
        <article class="mem-anatomy-claim" data-point="our-claim"><span class="mem-label">What we test</span>${typeButton('hypothesis',"Our claim","a folder in the work's repository",'mem-type-major')}<div class="mem-kind-stars" aria-label="How to tell a claim">${typeButton('empirical',"An idea, not a number")}${typeButton('theoretical',"Short record codes")}${typeButton('unspecified',"One idea, one folder")}</div><div class="mem-claim-parts"><span><b>Claim</b>one sentence aloud</span><span><b>Why</b>the mechanism of the effect</span><span><b>Conditions</b>where it must hold</span><span><b>Refutation</b>written before the test</span><span><b>How tested</b>series and derivations</span><span><b>Conclusion</b>status and reason</span></div></article>
        <article class="mem-anatomy-assessment" data-point="verdict"><span class="mem-label">How the assessment changes</span>${typeButton('assessment',"State","only by its own criterion",'mem-type-major')}<p class="mem-status-path">draft → under test<br>with the first series</p><div class="mem-status-outcomes"><span>supported</span><span>refuted</span><span>inconclusive</span></div><small>“Not refuted” does not mean “supported”.<br>“Not established” is a legitimate outcome.</small></article>
        <article class="mem-anatomy-ground" data-point="run"><span class="mem-label">How it was tested</span>${typeButton('experiment',"Run","code writes the numbers")}<p>The recorder wraps training before launch. The agent adds only “what is seen”.</p></article>
        <article class="mem-anatomy-ground" data-point="observation"><span class="mem-label">Empirical basis ↑</span>${typeButton('evidence',"Series","question and verdict")}<p>Runs answer one question. There is no series without a verdict.</p></article>
        <article class="mem-anatomy-ground mem-proof-ground" data-point="proof"><span class="mem-label">Theoretical basis ↖</span>${typeButton('derivation',"Derivation","statement and proof")}<p>What was established mathematically and where it applies.</p></article>
      </div>
      <div class="mem-context-atlas"><span class="mem-label">Around the claims</span><div>${[['project',"Work","one repository"],['paper',"Theme literature","a page per paper"],['decision',"Merge request","how an edit enters the base"],['journal',"Journal","what changed and when"],['term',"Handbook","how things work now"],['resource',"Servers","where we compute"],['source',"History","who edited and when"],['relations',"The canon","55 rules with checks"]].map(([id,title,caption])=>typeButton(id,title,caption)).join('')}</div></div>
    </section>`;
  }

  function overview(processes){
    return `<div class="mem-overview mem-diagram" data-map="overview">${svg}
      <div class="mem-origins" data-point="origins"><span class="mem-label">All of the lab's work</span><div class="mem-source-stars">${processes.map(p=>{const o=origins[p.id]||[p.title,''];return `<div class="mem-origin" data-origin="${esc(p.id)}" style="--star:${esc(p.color)}"><i aria-hidden="true"></i><span><b>${esc(o[0])}</b><small>${esc(o[1])}</small></span></div>`}).join('')}</div></div>
      <div class="mem-writer" data-point="writer">${dot}<div><b>The agent extracts the meaning</b><p>A task or a skill <span class="mem-trigger-arrow">↘</span> <span class="mem-hook-trigger">Jev's check at the end of a turn ↗</span><br>It edits files in its own clone and sends the edit as a proposal.</p></div></div>
      <div class="mem-main-lanes">
        <div class="mem-lane mem-literature-lane">
          ${station('paper',"From the literature","Paper","<p>A page in the topic's literature:<br>review, figures, BibTeX.</p>")}
          ${station('extract',"Analysis","What the paper claims","<p>One to three claims: numbers with their location, setup, our assessment.</p>")}
        </div>
        <div class="mem-lane mem-research-lane">
          ${station('question',"Our work","Work","<p>A separate repository:<br>claims, paper, code.</p>",'mem-project-node')}
          ${station('check',"Testing","Runs and series","<p>The recorder writes the run,<br>the series gives the verdict.</p><small>A claim's status changes only by its own criterion.</small>")}
        </div>
      </div>
      <article class="mem-assertion" data-point="assertion" aria-label="What is stored in the base: a claim">
        <header><span class="mem-label">Lab base · git</span><h2>Claim</h2><p>One testable idea<br>with everything used to test it.</p></header>
        <div class="mem-assertion-origin mem-from-paper" data-point="paper-result"><span class="mem-label">From a paper</span><p><b>What the authors claim</b></p><dl><dt>Source</dt><dd>Paper + a table or figure</dd><dt>Contents</dt><dd>Setup, refutation criterion, our assessment</dd></dl></div>
        <div class="mem-assertion-origin mem-from-project" data-point="project-result"><span class="mem-label">From a work</span><p><b>What we test</b></p><dl><dt>Grounds</dt><dd>Runs, series, derivations, figures</dd><dt>Assessment</dt><dd>under test → supported, refuted or inconclusive</dd></dl><small>Every number is checked against a run. A person does the merge.</small></div>
        <footer>Plain files in git: both people and agents read them,<br>and every line has a history.</footer>
      </article>
      <div class="mem-personal"><span class="mem-label">Personal stays on the machine and never goes to GitLab</span><div class="mem-personal-stores">
        <article class="mem-obsidian" data-point="obsidian"><span class="mem-store-mark" aria-hidden="true">◇</span><h3>Obsidian</h3><p>Notes, the diary and run logs live in the same work but are excluded from git.</p></article>
        <article class="mem-palace" data-point="mempalace"><span class="mem-store-mark" aria-hidden="true">✦</span><h3>MemPalace</h3><p>The agent's personal memory: a compressed session diary, verbatim words and decisions, a graph of links.</p></article>
      </div></div>
      <div class="mem-context"><span><b>Journal</b> what changed</span><span><b>Handbook</b> how things work</span><span><b>Servers</b> where we compute</span><span><b>Operations</b> grants, reports</span><p>The journal, handbook and servers also live in git and are edited directly. A work changes only through a proposal.</p></div>
    </div>`;
  }

  function ingestion(){
    return `<section class="mem-chapter" aria-labelledby="mem-ingest-title" data-chapter="ingest">
      <header class="mem-chapter-heading"><div><span class="mem-label">Who adds knowledge and how</span><h2 id="mem-ingest-title">From a paper. From a work.<br><em>From an agent's working turn.</em></h2></div><p>People and agents bring the material. Every path ends in a file in git, automated checks review the edit, and a person's merge records it.</p></header>
      <header class="mem-flow-heading"><h3>Paper → review in the topic's literature</h3><p>Selection yields candidates. A paper enters the base once someone decides to read it, and it is reviewed once for every work in the topic.</p></header>
      <div class="mem-ingest-map mem-diagram" data-map="ingest">${svg}${feeders('ingest')}
        ${station('document',"Material","Paper and source",`<div class="mem-paper-sheet"><span>arXiv / DOI</span><b>Full text</b><div aria-hidden="true"><i></i><i></i><i></i><i></i></div><small>PDF · LaTeX sources · figures</small></div><p>First we check whether the topic's literature already has a review. The bibliography and PDF go to Zotero.</p>`)}
        ${station('reader',"The agent extracts meaning","Read and analyze",`<p>Claude reads the paper by the lab's canon, checks the numbers and assumptions, and separates the authors' conclusions from ours.</p><div class="mem-model"><span>Review skill</span><b>paper-ingest</b></div><p>The selection before that is done by Jev: he compares the paper with the descriptions of our works and keeps the ones they need.</p>`)}
        ${station('sections',"One page","File it in the topic's literature",`<div class="mem-section-stack"><span>Review</span><span>Figures</span><span>BibTeX</span><span>What the paper claims</span></div><p>The file is named after the paper, and the citation key is inside. The paper's topic is where its page sits in the tree.</p><small>The same page shows up in Obsidian, because Obsidian opens the same tree.</small>`)}
        ${station('claims',"Scientific output of the analysis","Extract claims",`<p>From an important paper: one to three claims in our own words, with conditions.</p><div class="mem-claim-fan"><div><b>What it rests on</b><span>The paper's numbers with their location</span></div><div><b>What refutes it</b><span>Our threshold and control experiment</span></div><div><b>Our assessment</b><span>What to trust here</span></div></div><small>If more than three are picked out, something secondary got in.</small>`)}
      </div>
      <div class="mem-ingest-end"><div class="mem-claim-schema"><span class="mem-label">Every claim of a paper</span><p><b>Statement</b>${arrow}<b>Setup</b>${arrow}<b>Paper + location</b>${arrow}<b>Our assessment</b></p><small class="mem-fact">A script looks up every number in a review in the paper's own text. <b>On 07-10-2026 it checked 450 numbers across seventeen reviews and found two real errors.</b></small></div><div class="mem-claim-relations"><span class="mem-label">Link to our work</span><p>Paper ${arrow} <b>the work's manuscript and claims</b></p><small>The citation key is taken from the review page. An agent cannot write a citation to a paper missing from the work's bibliography: a check will stop the edit.</small></div></div>
      ${projectIngestion()}${checkpointIngestion()}
      <div class="mem-save-route"><h3>One way to save</h3><ol><li><b>An edit on its own branch</b><p>The agent edits files on a separate branch and pushes them with one command: GitLab opens the proposal itself and assigns the work lead.</p></li><li><b>Code runs the checks</b><p>Every number is checked against the runs: a number found in no run blocks the merge. Record codes, links and file deletions are checked the same way. A judge model reads the text separately, looking for filler and for conclusions that do not follow from what is written.</p><p class="mem-fact"><b>The verdict arrives 28 seconds after a proposal is opened, and the text judge costs about $0.3 a month for the whole flow.</b></p></li><li><b>A person's merge = a record</b><p>Nobody writes to a work directly, the admin included. The work lead merges. Until a person merges an edit, it is not in the base.</p></li></ol></div>
    </section>`;
  }

  function projectIngestion(){
    return `<div class="mem-project-flow"><header class="mem-flow-heading"><h3>Work → claims and their grounds</h3><p>Every record is tied to a work and a claim.</p></header>
      <div class="mem-project-map mem-diagram" data-map="project">${svg}${feeders('project')}
        ${station('workspace',"Research materials","A work and its clone",`<div class="mem-project-sheet"><span>the lab tree</span><b>A work in the tree</b><div><span>claims: the knowledge</span><span>manuscript · code</span><span>call breakdowns</span></div></div><p>A copy of the work already sits in the researcher's shared tree, exactly as in GitLab. Edits happen right there.</p>`)}
        ${station('claim',"What we want to find out","Formulate",`<p>First read all of the work's claims. A new one only if none covers this.</p><div class="mem-section-stack"><span>The claim in one sentence</span><span>What refutes it, before the test</span></div><small>A claim has one page, with everything used to test it next to it.</small>`)}
        ${station('grounds',"Two forms of evaluation","Save supporting grounds",`<div class="mem-research-branches"><div><b>Run → series</b><p>The recorder writes hyperparameters, numbers, environment, commit and hardware. A series answers one question with a verdict.</p></div><div><b>Derivation</b><p>A statement from scratch and a “Proof” section. Where it applies is named.</p></div></div>`)}
        ${station('assessment',"Scientific conclusion","Change the status",`<p>The agent checks the series against the criterion written in advance and adds a paragraph to the claim page.</p><div class="mem-verdicts"><b>supported</b><b>refuted</b><b>inconclusive</b></div><small>One successful series does not give “supported” if the criterion demanded more.</small>`)}
      </div>
      <div class="mem-operational-paths"><span><b>A rule or tool changed</b>${arrow}<span>Journal</span></span><span><b>Instructions for others</b>${arrow}<span>Handbook</span></span><span><b>Server, access, breakage</b>${arrow}<span>Servers</span></span></div>
      <p class="mem-flow-note">The journal, handbook and servers are edited directly. A call breakdown goes into the work, and an idea from a call stays an idea until there is a series under it.</p>
    </div>`;
  }

  function checkpointIngestion(){
    return `<div class="mem-checkpoint-flow"><header class="mem-flow-heading"><h3>End-of-turn check → lose nothing</h3><p>Useful things get saved even without a “write it down” command: at the end of every agent turn, Jev notices them.</p></header>
      <div class="mem-hook-map mem-diagram" data-map="hook">${svg}
        ${station('session',"During work","Context accumulates","<div class=\"mem-session-lines\"><span>Got a number</span><span>Hit a dead end</span><span>Made a decision</span></div><p>A month from now someone will look for this. If they can't find it, that is what should have been written down.</p>")}
        ${station('checkpoint',"End of turn","Jev checks the turn","<div class=\"mem-cadence\"><span><b>Jev assesses the turn</b>whether there is anything to save, and stops the agent with one line: what to record and where</span><span><b>Two automatic watchdogs</b>remind you if training was launched without recording its parameters, and show you if a proposal's checks failed</span></div>")}
        ${station('curator',"The agent acts","Select and save","<p>The agent picks what lasts: a measured number, a decision with its reason, a dead end, a bug found.</p><small>Junk in a shared base costs more than emptiness. If there is nothing to record, the agent says so in one line.</small>")}
        ${station('ack',"Where it goes","Two destinations","<div class=\"mem-checkpoint-stores\"><span><b>The lab base in GitLab</b>claims, runs, series, via a proposal</span><span><b>MemPalace</b>the agent's personal memory</span></div><small>A record appears in the base after the merge. If something was not recorded, the agent says so plainly.</small>")}
      </div><p class="mem-flow-note">Hermes on the server works in the same tree and writes to the base the same way, via a proposal. The agent draws the scientific conclusion, and a person records it by merging.</p>
    </div>`;
  }

  function analysisScenarios(){
    const cases=[
      ['compare',"Compare results","Which test provides stronger support?",`<b>Series and runs</b><small>Under the claim</small>`,`<b>The agent checks the setup and axis</b><small>Data, scale, schedule, hardware, what was varied</small>`,`<b>Comparisons and plots</b><small>From run numbers, with analysis and plotting skills</small>`, "Runs that are not comparable do not go into one series. Every number has a location where you can see it with your own eyes."],
      ['assess',"Check a conclusion","What is already supported?",`<b>Claim and criterion</b><small>The claim page</small>`,`<b>Series with verdicts and derivations</b><small>The “How it was tested” section</small>`,`<b>Status with a reason</b><small>Only by the criterion written in advance</small>`, "A mismatch between a run and the statement is called out loud, not smoothed over."],
      ['literature-check',"Compare with the literature","Where do our results differ?",`<b>Our claim</b><small>Full-text search</small>`,`<b>The topic's reviews</b><small>“What the paper claims” and our assessment</small>`,`<b>Agreement or contradiction</b><small>Accounting for setup and scope</small>`, "We did not reproduce someone else's claim, and on its own it does not support ours."],
      ['gaps',"Find open issues","What is missing for a conclusion?",`<b>What the checks said</b><small>And open issues</small>`,`<b>A gap found</b><small>A series without a verdict, a run not under a claim, a number without a run</small>`,`<b>A clear next step</b><small>A GitLab issue with the claim in its body</small>`, "The checks catch the mechanics. Scientific quality is judged by the person who merges."],
      ['resume',"Resume work","What has changed since last time?",`<b>New edits</b><small>Change history</small>`,`<b>The work's front page</b><small>Reading order: five to seven files and why each</small>`,`<b>Change summary</b><small>New series, statuses and open questions</small>`, "A newcomer reads a work in the order given on its front page."]
    ];
    return `<div class="mem-analysis-scenarios"><header class="mem-flow-heading"><h3>After the search: make sense of the result</h3><p>The base returns files with their locations. A researcher or an agent checks the meaning, compares the data and draws the conclusion.</p></header>${cases.map(([id,label,title,a,b,c,note])=>`<article class="mem-analysis-case" data-scenario="${id}"><div><span class="mem-label">${label}</span><h4>${title}</h4></div><div class="mem-walk-path"><span>${a}</span>${arrow}<span>${b}</span>${arrow}<span>${c}</span></div><p>${note}</p></article>`).join('')}<div class="mem-useful-context"><span><b>Who leads the work</b><small>The “Leads” and “Team” lines</small></span><span><b>Where to compute</b><small>Servers</small></span><span><b>How it's done</b><small>Handbook</small></span></div></div>`;
  }

  function retrieval(){
    return `<section class="mem-chapter" aria-labelledby="mem-search-title" data-chapter="search">
      <header class="mem-chapter-heading"><div><span class="mem-label">Working with accumulated knowledge</span><h2 id="mem-search-title">Find. Compare.<br><em>Understand what the results imply.</em></h2></div><p>Everyone has the whole lab locally as one tree, exactly as in GitLab. Search works without a server, without a browser and without waiting.</p></header>
      <div class="mem-readers"><span class="mem-label">Who reads the base</span><span>Researcher · Obsidian</span><span>Claude Code · locally</span><span>Hermes · on the server</span><span>Jev · work descriptions</span><small>Everyone looks into the same tree: question → search over files and history → a file with its address</small></div>
      <div class="mem-search-map mem-diagram" data-map="search">${svg}
        ${station('query',"Start with a question","Where to start",`<blockquote>“Has anyone tried this already?”</blockquote><p>Your own works, the literature of their topics, the handbook, the journal and the servers are already in the tree.</p>`)}
        ${station('words',"Text","By words","<p>Search across claims and literature: a method name, a claim code, a citation key, a number.</p>")}
        ${station('vectors',"History","By time","<p>The history shows in which edit a number appeared and who merged that proposal.</p>")}
        ${station('merge',"Found","Claim","<p>The claim folder: title, refutation criterion, status and paragraphs on the series.</p><small>One folder: everything about one idea.</small>")}
        ${station('graph',"Grounds","Series and verdicts","<p>The series' question, shared setup, comparison axis, table of runs and verdict.</p><small>The work's front page says in which order to read it.</small>")}
        ${station('rerank',"Number","Run page","<p>Code recorded the hyperparameters, environment, commit and hardware. The agent added only “what is seen”.</p><div class=\"mem-model\"><span>Written by</span><b>the run recorder</b><small>no dependencies</small></div>")}
        ${station('answer',"Result","An answer with an address","<ul class=\"mem-answer-fields\"><li>Code and file path</li><li>Statement and status</li><li>Work and its lead</li><li>Where the number lives: log or W&amp;B</li></ul><p>The agent answers with links to files. Any number can be opened and checked.</p>")}
      </div>
      <div class="mem-search-settings"><p><b>Search is git:</b> there is no separate search server. Fresh edits arrive with one command, the whole tree is assembled with another.</p><p><b>Why this is more reliable:</b> the base is plain files. A person reads them in Obsidian and an agent with a command, every line has a history, and nothing depends on whether some separate service is alive.</p></div>
      ${analysisScenarios()}
      <div class="mem-walks"><h3>Start from a topic, a subject or a familiar record</h3>
        <div class="mem-walk" data-route="theme"><div><span class="mem-label">Explore a direction</span><h4>From topic to works</h4></div><div class="mem-walk-path"><span><b>The lab tree</b><small>direction / topic / work</small></span>${arrow}<span><b>The work's front page</b><small>“In short”, who leads it, what it builds on</small></span>${arrow}<span><b>Claims</b><small>The work's folders</small></span></div></div>
        <div class="mem-walk" data-route="subject"><div><span class="mem-label">The question is not “what's the answer” but “what do we have”</span><h4>Get everything on a subject</h4></div><div class="mem-walk-path"><span><b>Subject</b><small>Muon, LoRA, warmup, quantization</small></span>${arrow}<span><b>Every file that mentions it</b><small>Grouped by work, unranked</small></span>${arrow}<span><b>The whole work</b><small>One command</small></span></div><p>To “what do we have at all”, search answers with the full list of files.</p></div>
        <div class="mem-walk" data-route="code"><div><span class="mem-label">An operational question</span><h4>Get to the code</h4></div><div class="mem-walk-path"><span><b>Work</b><small>Code is attached to it as a submodule</small></span>${arrow}<span><b>Code and paper in place</b><small>One command</small></span>${arrow}<span><b>The run's commit</b><small>Recorded by the recorder on the run page</small></span></div><p>Every run names the code it was computed with. A number can always be reproduced from the same commit.</p></div>
        <div class="mem-walk" data-route="library"><div><span class="mem-label">Browse the library</span><h4>From topic to paper</h4></div><div class="mem-walk-path"><span><b>The topic's literature</b><small>Next to the topic's works</small></span>${arrow}<span><b>Paper page</b><small>The file is named after the paper</small></span>${arrow}<span><b>Claims and BibTeX</b><small>With the citation key</small></span></div><p>The tree is read directly, and the literature index builds itself from the paper pages.</p></div>
        <div class="mem-walk" data-route="known"><div><span class="mem-label">You have a specific code</span><h4>From code to files</h4></div><div class="mem-walk-path"><span><b>Claim code</b><small>For example H-WSD-009</small></span>${arrow}<span><b>All its records</b><small>One search command</small></span>${arrow}<span><b>Series, runs, derivations, figures</b><small>Each with its own code</small></span></div><p>Codes are the same in git, in Obsidian and in proposals, so a link from a chat leads straight to the file.</p></div>
        <div class="mem-walk" data-route="evidence"><div><span class="mem-label">Check the grounds</span><h4>From claim to number</h4></div><div class="mem-walk-path"><span><b>Claim</b><small>A paragraph on the series</small></span>${arrow}<span><b>Series</b><small>The “Runs” table</small></span>${arrow}<span><b>Run and the number's location</b><small>Log or W&amp;B</small></span></div><p>At merge time the checks already matched every number against a run. The edit history is kept in git.</p></div>
      </div>
      <div class="mem-vector-cache"><div><span class="mem-label">How a number gets into the base</span><h3>Code writes the numbers</h3><p>The agent does not retype numbers. A number that is not in the runs does not get past the checks.</p></div><div class="mem-cache-path"><span><b>Training</b><small>Wrapped before launch</small></span>${arrow}<span><b>Recorder</b><small>Run page</small></span>${arrow}<span><b>New runs</b><small>Proposal branch</small></span>${arrow}<span><b>Claim</b><small>The run sits under it</small></span></div><p>The recorder itself writes hyperparameters, final numbers, environment, commit, hardware and the full log. The agent moves the page under a claim and adds “what is seen”. Until every run has been moved under a claim, the proposal will not merge. Forgot to wrap it? The recorder adopts a run already in progress, and the end-of-turn check reminds you on its own.</p></div>
    </section>`;
  }

  function accessGuide(){
    return `<section class="mem-chapter mem-access" id="mcp-access" aria-labelledby="mem-access-title">
      <header class="mem-chapter-heading"><div><span class="mem-label">Person · role · work</span><h2 id="mem-access-title">Access to the lab.<br><em>Rights in your own work.</em></h2></div><p>A role in the lab is a role in GitLab, under the same name. An agent works with its own key and writes to the base only through proposals.</p></header>
      <div class="mem-access-steps"><span>Name, handle and role in the bot's form</span><i>→</i><span>The direction lead decides</span><i>→</i><span>Login to the base site and a git key</span><i>→</i><span>One command assembles the tree</span></div>
      <div class="mem-access-roles">
        <article><span class="mem-label">Guest · reader</span><h3>Guest and student</h3><p>A guest sees the tree of topics and works and all the literature. A student reads every work in full but does not write.</p></article>
        <article><span class="mem-label">Researcher</span><h3>Researcher</h3><p>Branches and proposals everywhere, their own works in any topic. A record enters a work only by merge.</p></article>
        <article><span class="mem-label">Lead</span><h3>Direction lead</h3><p>Merges proposals, creates topics, admits new people to the lab.</p></article>
      </div>
      <div class="mem-access-project"><h3>Every work has its own people</h3><dl><div><dt>Leads</dt><dd>Merge the work's proposals. Every proposal is assigned to the first lead.</dd></div><div><dt>Team</dt><dd>The work's students. Both lines sit on the work's front page, and they decide what goes into a researcher's tree.</dd></div><div><dt>Someone else's work</dt><dd>A request-access button on the topic or work. The bot carries the request to its lead.</dd></div></dl><p>Nobody writes to a work directly, the admin included. Protection rests not on roles but on the fact that every record goes through a proposal with passed checks and the work lead's decision.</p></div>
      <footer><a href="https://t.me/brainlab_server_access_bot" target="_blank" rel="noopener noreferrer">Open the access bot ↗</a><p>In the bot's menu, choose access to the knowledge base and fill in the form: name, a Latin-letter handle (it becomes your login) and role. The direction lead decides on the request with one button in Telegram. Once approved, the bot sends a login to the base site and a key the agent uses to pull works and open proposals.</p></footer>
    </section>`;
  }

  function render(p, processes){
    return `<div class="process-shell memory-observatory" style="--accent:#b9ff66">
      <header class="mem-header"><div><button class="back-button" data-back type="button">← Full atlas</button><span class="mem-coordinate">BRAIn Lab / Knowledge base · git</span></div></header>
      ${anatomy()}
      <header class="mem-chapter-heading mem-overview-heading"><div><span class="mem-label">Where knowledge comes from</span><h2>How work becomes <em>knowledge</em></h2></div></header>
      <section class="mem-first-map" aria-label="Overview: sources, claims, and personal memory" data-chapter="overview">${overview(processes)}<div class="mem-practice-notes"><p><b>When it is saved:</b> as work goes on and at the end of a turn. Jev notices what is worth recording and where, the agent writes, the checks verify, a person merges.</p><p><b>Where the tasks are:</b> in GitLab, each work has its own board, and the body of an issue names the claim it affects. Hermes has his own task board on the server.</p></div></section>
      ${ingestion()}${retrieval()}${accessGuide()}
      <footer class="mem-footer"><p>The diagrams show how the system is built, without data from the private base. Checked against the lab's canon and handbook on 19-10-2026.</p><a href="#mcp-live">See the base's records ↗</a><details class="mem-tools"><summary>Skills and tools of this layer</summary><div>${p.tools.map(t=>`<button type="button" data-skill="${esc(t.id)}">${esc(t.title)}</button>`).join('')}</div></details><a href="https://github.com/Vepricov/claude-brainlab/blob/main/skills/lab-knowledge/SKILL.md" target="_blank" rel="noopener noreferrer">The lab-knowledge skill and sources ↗</a></footer>
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
