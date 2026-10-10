/* Explanatory maps contain no private records and never call the live MCP. */
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
  const feeders = kind => `<div class="mem-feeders" aria-label="${kind==='ingest'?"Where papers come from":"Where project materials come from"}">${inlets[kind].map(([id,title,caption])=>`<div class="mem-inlet" data-inlet="${kind}" data-point="${kind}-via-${id}"><b>${title}</b><small>${caption}</small></div>`).join('')}</div>`;

  // Record kinds and lifecycle values checked against the live MCP schema, 12-09-2026.
  const recordGuide = {
    hypothesis: {title:"Our claim",code:'hypothesis',text:"A standalone statement the laboratory tests. It starts as a hypothesis and keeps the same ID after assessment, preserving access to its supporting grounds and the history of the conclusion.",fields:[["Content","The statement, a short title, motivation, and proposed mechanism."],["Conditions","Assumptions, expected observations, and a falsification criterion."],["Testing","The claim's kind, assessment plan, related experiments, and proofs."],["State","Status with its rationale, open questions, priority, and tags."],["Provenance","Project, topic, source, authorship, ID, public code, and change history."]],example:"“At the same budget, method A reduces error relative to B.” Falsification criterion: the advantage disappears when the specified comparison is repeated."},
    empirical: {title:"Empirical claim",code:'hypothesis · empirical',text:"Describes something that can be tested through observation or measurement. The assessment plan defines comparison conditions. The experiment stores the protocol; evidence stores the actual results.",fields:[["What it establishes","An effect, relationship, method comparison, or scope of applicability."],["What supports it","Measurements with sources, conditions, and limitations."]],example:"“With a fixed number of steps, method A yields lower error on the held-out set.”"},
    theoretical: {title:"Theoretical claim",code:'hypothesis · theoretical',text:"A statement tested by mathematical reasoning. Assumptions and the argument are saved in a derivation linked to this claim.",fields:[["What it establishes","An equality, bound, convergence result, or another mathematical result."],["What supports it","A derivation with explicit assumptions and verification status."]],example:"“Under the stated assumptions, the error decreases at least as fast as the specified bound.”"},
    unspecified: {title:"Kind not yet specified",code:'hypothesis · unspecified',text:"A valid record when it is not yet clear whether the claim will be tested experimentally or through a proof. Its kind can be refined later without changing the ID or losing its history.",fields:[["Why it is useful","Preserves an idea with a falsification criterion without pretending its evaluation method is already settled."]]},
    paperClaim: {title:"Paper claim",code:'paper_claim',text:"One statement from an external work: what its authors claim and where to find it. Stored in the library, it may link to several of our projects.",fields:[["Content","A statement with its conditions of applicability. Paraphrasing is allowed."],["Kind","An empirical result, theoretical result, method, or definition."],["Source","Paper ID and a locator: section, table, equation, or theorem."],["Quotation","Optional. quote_verified checks a match with saved text, not scientific truth."],["Relationships","May motivate our hypothesis, provide a baseline, support it, or challenge it. By itself, it does not complete our evaluation."]],example:"“The authors report lower error in Table 2 on dataset X under the stated conditions.”"},
    paperEmpirical: {title:"Authors' result",code:'paper_claim · empirical',text:"A measurement or observation reported by the paper. Essential conditions are preserved: model, data, metric, and comparison.",fields:[["Use","Lets you compare the reported result with your experiment and locate the original table."]],example:"“In Table 3, method A outperforms B on two of three datasets.”"},
    paperTheoretical: {title:"Authors' theoretical result",code:'paper_claim · theoretical',text:"A theorem, lemma, bound, or derivation from the paper. The statement retains its assumptions, and the locator points to the relevant part of the proof.",fields:[["Use","Helps apply the result in your own work under the conditions for which it was proved."]],example:"“Theorem 1 gives a convergence bound under a Lipschitz gradient assumption.”"},
    paperMethod: {title:"Method from a paper",code:'paper_claim · method',text:"What the authors propose doing: an algorithm, training technique, measurement method, or procedure. The method description is stored separately from claims about its effectiveness.",fields:[["Use","Lets you recover the method's idea and connect it to your implementation."]],example:"“The authors normalize the update by its spectral norm before the optimizer step.”"},
    paperDefinition: {title:"Definition from a paper",code:'paper_claim · definition',text:"How the authors define a concept or quantity. A link to the definition helps compare papers that use the same word differently.",fields:[["Use","Preserves the term's precise meaning in this publication."]],example:"“Definition 2 specifies effective rank through the matrix spectrum.”"},
    assessment: {title:"Claim status",code:'hypothesis.status',text:"The assessment changes on the same record. Saving evidence or completing a run does not automatically change the status: the agent separately states the conclusion and its grounds.",fields:[["Before a conclusion","draft → proposed → testing."],["After testing","Supported, refuted, or inconclusive when the grounds are insufficient."],["Archive","archived retains a record that is no longer under active investigation."],["Rationale","The status applies to the statement under its stated conditions. The reason and linked measurements or proofs explain the assessment."]],example:"The run finished, but results differ across repeats. Experiment: completed. Claim: inconclusive."},
    experiment: {title:"Experiment",code:'experiment',text:"A test of our claim using a reproducible protocol. Contains the goal and actual run parameters; results are stored as linked evidence records.",fields:[["Contents","Primary and additional claims, protocol, parameters, source, and an optional task link."],["State","Planned, running, completed, failed, interrupted, or cancelled."]],example:"Compare A and B using the same model and data, equal budgets, and several repeats."},
    evidence: {title:"Evidence · observation and result",code:'evidence',text:"What the experiment actually produced: a number, observation, artifact, or diagnostic finding. It may support a claim, contradict it, or leave the question open.",fields:[["Fact","A concise result, metrics with units and conditions, and qualitative observations."],["Meaning","Interpretation, limitations, and effects on related claims."],["Provenance","Experiment ID, source, and the result's own ID."],["Kind","A free-form kind field. Examples: metric, artifact, manuscript, diagnostic. The list is open."]],example:"Mean error is 0.18 for A and 0.20 for B across three repeats. Limitation: tested on one dataset."},
    derivation: {title:"Proof / derivation",code:'derivation',text:"Mathematical support for a claim: assumptions → steps of the argument → established result. May depend on other saved derivations.",fields:[["Contents","Claim, assumptions, argument, result, dependencies, and source."],["State","sketch, complete, verified, or gap. A gap must state what is missing."]],example:"Derive an upper error bound from smoothness assumptions and explicitly identify a lemma that remains unproved."},
    project: {title:"Project",code:'project',text:"Research context: problem, goal, approach, participants, current state, and open questions. Groups our scientific records and links to working materials.",fields:[["Organization","A project belongs to a topic. Records can be found by topic, project, and paper tags."],["Linked workspaces","Repository, notes, project page, and shared task board. Task status is separate from the scientific conclusion."]]},
    paper: {title:"Paper and sections",code:'paper · paper_chunk',text:"A paper stores bibliographic details, identifiers, an abstract, and an analysis. Sections store the titles, order, and text of meaningful parts. Claims are extracted into separate records.",fields:[["Use","A short claim leads back to the full context and source. One paper may inform many projects."]]},
    decision: {title:"Decision",code:'decision',text:"A choice the laboratory proposes or accepts: what to do next and why. A scientific decision links to the claims and results supporting it.",fields:[["Kind","A scientific rule (scientific) or operational agreement (operational). Older records may not yet specify a kind."],["Contents","Statement, rationale, source, and links to claims and evidence."],["State","Proposed, accepted, or superseded by a newer decision."]],example:"Choose method B for the next series based on the comparison. Operational example: agree on a deadline for analyzing the results."},
    journal: {title:"Journal",code:'journal_entry',text:"A fact or event worth remembering: an observation, incident, measurement, connection setup, or organizational change. It can be saved immediately, even before a scientific conclusion is formulated.",fields:[["Kinds",'observation · incident · measurement · onboarding · organisational'],["Contents","What happened, when, and which projects, papers, or resources it concerns."]],example:"“The run lost access to storage. Execution was interrupted; logs were saved.”"},
    term: {title:"Terms",code:'project_term',text:"A definition of a name used in records: a method, run, metric, protocol, or artifact. Aliases connect alternate spellings; a broader term places it in the glossary.",fields:[["Kinds","Implementation, run, protocol, metric, data, artifact, or other."],["Use","A person or agent can understand an old record without its author and find related material."]]},
    resource: {title:"Resources",code:'resource',text:"What the laboratory has and on what terms: servers, clusters, quotas, accounts, licenses, datasets, budgets, and services.",fields:[["State","Requested, available, expired, or retired."],["Use","Helps plan work around actual resources and constraints. Accounts are described without publishing secrets."]]},
    source: {title:"Sources and history",code:'source_ref · audit_event',text:"A source explains where a record came from: a working session, call, document, or log. History shows who created or changed it and when.",fields:[["Contents","Source type and location, content or a link. An audit event records the author, action, object, time, and changes."],["Use","A conclusion can be checked against the material, and its evolution can be reconstructed. Each scientific record retains its own stable ID."]]},
    relations: {title:"Relationships between records",code:'paper_link · hypothesis_effects',text:"Explain how records relate to each other. A reference to a paper and the result of our own test carry different meanings.",fields:[["Paper → our work","Prior work (prior_art), support (supports), contradiction (contradicts), baseline, inspiration (inspired), or reproduction (reproduces)."],["Evidence → claim","An assessment and its reason: support, partial support, contradiction, uncertainty, or a narrower scope of applicability."],["Structure","An experiment tests a claim; evidence belongs to an experiment; a derivation supports a claim; a decision references its grounds."]]}
  };
  const typeButton = (id,title,caption='',cls='') => `<button type="button" class="mem-type ${cls}" data-record="${id}" aria-haspopup="dialog"><span>${title}</span>${caption?`<small>${caption}</small>`:''}</button>`;
  function anatomy(){
    return `<section class="mem-anatomy" data-chapter="anatomy" aria-labelledby="mem-anatomy-title">
      <header class="mem-anatomy-heading"><span class="mem-label">Inside shared memory</span><h1 id="mem-anatomy-title" tabindex="-1">What <em>knowledge</em> is made of</h1><p>A claim holds an idea. Linked records show where it came from and what supports it.</p></header>
      <div class="mem-anatomy-map mem-diagram" data-map="anatomy">${svg}
        <article class="mem-anatomy-paper" data-point="paper-claim"><span class="mem-label">What the authors report</span>${typeButton('paperClaim',"From a paper",'paper_claim','mem-type-major')}<div class="mem-kind-stars" aria-label="Kinds of paper claims">${typeButton('paperEmpirical',"Result")}${typeButton('paperTheoretical',"Theory")}${typeButton('paperMethod',"Method")}${typeButton('paperDefinition',"Definition")}</div><p>A statement with its conditions.<br>The paper and an exact location in it.</p><small class="mem-anatomy-relation">Linked to our work →</small></article>
        <article class="mem-anatomy-claim" data-point="our-claim"><span class="mem-label">What we test</span>${typeButton('hypothesis',"Our claim","hypothesis · one ID before and after testing",'mem-type-major')}<div class="mem-kind-stars" aria-label="Kinds of our claims">${typeButton('empirical',"Empirical")}${typeButton('theoretical',"Theoretical")}${typeButton('unspecified',"Not yet specified")}</div><div class="mem-claim-parts"><span><b>Statement</b>what we claim</span><span><b>Conditions</b>when it holds</span><span><b>Falsification</b>what would refute it</span><span><b>Plan</b>how we will test it</span><span><b>Source</b>where it comes from</span><span><b>Status</b>conclusion and reason</span></div></article>
        <article class="mem-anatomy-assessment" data-point="verdict"><span class="mem-label">How the assessment changes</span>${typeButton('assessment',"Status","Of the same record",'mem-type-major')}<p class="mem-status-path">Draft → proposed<br>→ under testing</p><div class="mem-status-outcomes"><span>Supported</span><span>Refuted</span><span>Inconclusive</span></div><small>Assessments follow the supporting grounds.<br>Inactive records stay in the archive.</small></article>
        <article class="mem-anatomy-ground" data-point="run"><span class="mem-label">How we tested it</span>${typeButton('experiment',"Experiment","Protocol · parameters · state")}<p>What ran and under which conditions.</p></article>
        <article class="mem-anatomy-ground" data-point="observation"><span class="mem-label">Empirical support ↑</span>${typeButton('evidence','Evidence',"Measurements · observations · artifacts")}<p>What we found, how it affects the claim, and the limits of the result.</p></article>
        <article class="mem-anatomy-ground mem-proof-ground" data-point="proof"><span class="mem-label">Theoretical support ↖</span>${typeButton('derivation',"Proof","Assumptions → argument → result")}<p>What was established mathematically and whether the argument has been checked.</p></article>
      </div>
      <div class="mem-context-atlas"><span class="mem-label">Context around scientific records</span><div>${[['project',"Project","The research question"],['paper',"Paper and sections","Full context"],['decision',"Decision","What we do and why"],['journal',"Journal","What happened"],['term',"Terms","What the names mean"],['resource',"Resources","What we have"],['source',"Sources and history","How we know"],['relations',"Relationships","How records relate"]].map(([id,title,caption])=>typeButton(id,title,caption)).join('')}</div></div>
    </section>`;
  }

  function overview(processes){
    return `<div class="mem-overview mem-diagram" data-map="overview">${svg}
      <div class="mem-origins" data-point="origins"><span class="mem-label">All work in Atlas</span><div class="mem-source-stars">${processes.map(p=>`<div class="mem-origin" data-origin="${esc(p.id)}" style="--star:${esc(p.color)}"><i aria-hidden="true"></i><span><b>${origins[p.id][0]}</b><small>${origins[p.id][1]}</small></span></div>`).join('')}</div></div>
      <div class="mem-writer" data-point="writer">${dot}<div><b>The agent identifies the substance</b><p>Assignment / skill <span class="mem-trigger-arrow">↘</span> <span class="mem-hook-trigger">Hook · checkpoint ↗</span><br>Reads the context, saves what matters, and checks the record.</p></div></div>
      <div class="mem-main-lanes">
        <div class="mem-lane mem-literature-lane">
          ${station('paper',"From the literature","Paper","<p>Source, full text,<br>and analysis of the paper.</p>")}
          ${station('extract',"Analysis","Individual claims","<p>Sections → results, theorems, methods, and definitions.</p>")}
        </div>
        <div class="mem-lane mem-research-lane">
          ${station('question',"Our work","Project","<p>Claims, protocols,<br>and research results.</p>",'mem-project-node')}
          ${station('check',"Testing","Grounds and assessment","<p>Experiment → measurements<br>or a mathematical derivation.</p><small>The agent updates the same claim’s status.</small>")}
        </div>
      </div>
      <article class="mem-assertion" data-point="assertion" aria-label="What MCP stores: a claim">
        <header><span class="mem-label">Lab Knowledge MCP · PostgreSQL</span><h2>Claim</h2><p>One standalone statement<br>with conditions and provenance.</p></header>
        <div class="mem-assertion-origin mem-from-paper" data-point="paper-result"><span class="mem-label">From a paper <code>paper_claim</code></span><p><b>What the authors claim</b></p><dl><dt>Source</dt><dd>Paper + section, table, or theorem</dd><dt>Content</dt><dd>Statement, kind, and conditions of applicability</dd></dl></div>
        <div class="mem-assertion-origin mem-from-project" data-point="project-result"><span class="mem-label">From a project <code>hypothesis</code></span><p><b>What we test</b></p><dl><dt>Grounds</dt><dd>Metrics and artifacts, or a proof</dd><dt>Assessment</dt><dd>Under testing → supported, refuted, or inconclusive</dd></dl><small>One ID before and after testing. A conclusion needs supporting grounds.</small></div>
        <footer>Two linked record types.<br>Shared topics, relationships, and search.</footer>
      </article>
      <div class="mem-personal"><span class="mem-label">The same agent saves personal context</span><div class="mem-personal-stores">
        <article class="mem-obsidian" data-point="obsidian"><span class="mem-store-mark" aria-hidden="true">◇</span><h3>Obsidian</h3><p>Full analyses, drafts, protocols, and plots in the appropriate project or library folder.</p></article>
        <article class="mem-palace" data-point="mempalace"><span class="mem-store-mark" aria-hidden="true">⌘</span><h3>MemPalace</h3><p>Session diary, original fragments, and decisions. Context for the agent's next turn.</p></article>
      </div></div>
      <div class="mem-context"><span><b>Decisions</b> chosen actions</span><span><b>Journal</b> facts and events</span><span><b>Terms</b> definitions</span><span><b>Resources</b> code, data, servers</span><p>MCP also stores working context. Records have IDs, sources, authorship, and a change history.</p></div>
    </div>`;
  }

  function ingestion(){
    return `<section class="mem-chapter" aria-labelledby="mem-ingest-title" data-chapter="ingest">
      <header class="mem-chapter-heading"><div><span class="mem-label">Who adds knowledge and how</span><h2 id="mem-ingest-title">From papers. From projects.<br><em>From working conversations.</em></h2></div><p>People and agents bring the material. Each path ends with a sourced record and a read-back check of the saved result.</p></header>
      <header class="mem-flow-heading"><h3>Paper → authors' claims</h3><p>Search and recommendations identify candidates. Selected and analyzed papers enter the shared corpus.</p></header>
      <div class="mem-ingest-map mem-diagram" data-map="ingest">${svg}${feeders('ingest')}
        ${station('document',"Material","Paper and source",`<div class="mem-paper-sheet"><span>arXiv / DOI</span><b>Full text</b><div aria-hidden="true"><i></i><i></i><i></i><i></i></div><small>Tables · equations · appendices</small></div><p>First look for an existing record. In the personal workflow, Zotero stores bibliographic details and the PDF.</p>${api('get_paper','upsert_paper')}`)}
        ${station('reader',"The agent extracts meaning","Read and analyze",`<p>The literature Hermes reads the material, checks numbers and assumptions, and separates the authors' conclusions from its own checks.</p><div class="mem-model"><span>Literature profile model</span><b>gpt-5.6-sol</b></div><p>The full analysis stays in Obsidian. Another agent can follow the same workflow through <code>paper-ingest</code>.</p>`)}
        ${station('sections',"Deterministic transfer","Save sections",`<div class="mem-section-stack"><span>Method</span><span>Theory</span><span>Experiments</span><span>Limitations</span></div><p>The parser transfers text by analysis headings: title, order, content, and <code>paper_id</code>.</p><small>Sections retain their names. The PDF is not split into arbitrary chunks.</small>${api('add_paper_section')}`)}
        ${station('claims',"Scientific output of the analysis","Extract claims",`<p>The agent formulates each independent statement in its own words while preserving its conditions.</p><div class="mem-claim-fan"><div><b>Result</b><span>Metric, value, model, data</span></div><div><b>Theorem</b><span>Assumptions and established conclusion</span></div><div><b>Method / definition</b><span>What is proposed and what it means</span></div></div><small>The content determines the number of records. There is no quota.</small>${api('record_paper_claim')}`)}
      </div>
      <div class="mem-ingest-end"><div class="mem-claim-schema"><span class="mem-label">Every record</span><p><b>Statement</b>${arrow}<b>Kind and conditions</b>${arrow}<b>Paper + location</b>${arrow}<b>Stable ID</b></p><small>A quotation is optional. A source link and exact location are needed for verification.</small></div><div class="mem-claim-relations"><span class="mem-label">Link to our work</span><p>Paper claim ${arrow} <b>our claim</b></p><small>Prior work · baseline · support · contradiction · reproduction. The agent adds a relationship when it is justified.</small>${api('link_paper')}</div></div>
      ${projectIngestion()}${checkpointIngestion()}
      <div class="mem-save-route"><h3>One saving procedure</h3><ol><li><b>Find existing records</b><p>By stable ID and meaning. Additions preserve others' records, sections, and relationships.</p></li><li><b>Validate the record</b><p>MCP checks permissions, required fields, and related IDs. Repeating a request with the same key does not create another object where <code>idempotency_key</code> is supported.</p></li><li><b>Save and read back</b><p>The agent retrieves the record and checks its fields. A failed write remains explicitly pending with a reason.</p></li></ol></div>
    </section>`;
  }

  function projectIngestion(){
    return `<div class="mem-project-flow"><header class="mem-flow-heading"><h3>Project → our claims and supporting grounds</h3><p>First identify the existing project. Its material is split into linked scientific and operational records.</p></header>
      <div class="mem-project-map mem-diagram" data-map="project">${svg}${feeders('project')}
        ${station('workspace',"Research materials","Project and source",`<div class="mem-project-sheet"><span>PROJECT</span><b>Our research</b><div><span>Code and protocols</span><span>Logs and tables</span><span>Meeting analyses</span></div></div><p>One project_id connects the work. The source identifies where each fact came from.</p>${api('get_project_by_slug','publish_source_note')}`)}
        ${station('claim',"What we want to find out","Formulate",`<p>One testable statement: wording, conditions, expected result, and a falsification criterion.</p><div class="mem-section-stack"><span>Empirical claim</span><span>Theoretical claim</span></div><small>The claim gets an ID at the start and keeps it after testing.</small>${api('create_hypothesis')}`)}
        ${station('grounds',"Two forms of evaluation","Save supporting grounds",`<div class="mem-research-branches"><div><b>Experiment → measurement</b><p>Protocol and actual run status; metrics, seeds, artifacts, and limitations.</p>${api('record_experiment','record_evidence')}</div><div><b>Mathematical derivation</b><p>Assumptions → argument → result. The proof's completeness is recorded.</p>${api('record_derivation')}</div></div>`)}
        ${station('assessment',"Scientific conclusion","Assess the claim",`<p>The agent compares the grounds with the original criterion and checks for contradictions.</p><div class="mem-verdicts"><b>Supported</b><b>Refuted</b><b>Inconclusive</b></div><small>The conclusion and rationale are written to the same hypothesis. Ongoing evaluation is not reported as complete.</small>${api('update_hypothesis','get_hypothesis')}`)}
      </div>
      <div class="mem-operational-paths"><span><b>Observation or failure</b>${arrow}<span>Journal</span>${api('record_journal')}</span><span><b>An agreed choice</b>${arrow}<span>Decision + grounds</span>${api('propose_decision','update_decision')}</span><span><b>Server, data, quota</b>${arrow}<span>Resource</span>${api('upsert_resource')}</span></div>
      <p class="mem-flow-note">Completed results can be added to existing records. Meeting analysis brings ideas and agreements; an expected result remains a hypothesis until tested.</p>
    </div>`;
  }

  function checkpointIngestion(){
    return `<div class="mem-checkpoint-flow"><header class="mem-flow-heading"><h3>Hook → save the working turn's results</h3><p>Another route into the same database: preserve useful findings from the work, even without a separate request to add them.</p></header>
      <div class="mem-hook-map mem-diagram" data-map="hook">${svg}
        ${station('session',"During work","Context accumulates","<div class=\"mem-session-lines\"><span>A result is obtained</span><span>A limitation is found</span><span>The next step is chosen</span></div><p>Codex, Claude Code, and autonomous Hermes agents encounter facts the next agent will need.</p>")}
        ${station('checkpoint',"Automatic reminder","The hook triggers","<div class=\"mem-cadence\"><span><b>Codex / Claude Code</b>after 10 human messages</span><span><b>Autonomous Hermes</b>every 5 working turns</span></div><small>The hook asks the agent to complete the save. It neither chooses a scientific conclusion nor publishes one itself.</small>")}
        ${station('curator',"The agent acts","Select and save","<p>The agent reads the context, selects durable results, checks existing records, and identifies each fact's type.</p><small>Results enter shared MCP within the authorized publication scope. If nothing needs saving, no unnecessary records are created.</small>")}
        ${station('ack',"Confirmation","Read back","<div class=\"mem-checkpoint-stores\"><span><b>MCP</b>knowledge, grounds, IDs</span><span><b>Obsidian</b>project notes</span><span><b>MemPalace</b>context and history</span></div><small>A successful response and read-back confirm the save. A failure remains pending with a reason.</small>")}
      </div><p class="mem-flow-note">In Hermes, the reminder arrives during the main turn; the completion check applies to turns with edits. Pending material stays in lab-inbox until a write is confirmed. Neither a hook nor a Kanban export replaces the agent's scientific assessment.</p>
    </div>`;
  }

  function analysisScenarios(){
    const cases=[
      ['compare',"Compare results","Which test provides stronger support?",`<b>Experiments and metrics</b>${api('get_project_context','get_related')}`,`<b>The agent checks protocols</b><small>Data, baselines, seeds, units, and limitations</small>`,`<b>Comparisons and plots</b><small>results-analysis · academic-plotting, when the underlying data is available</small>`, "Numbers are compared under matching conditions. Missing repeats and metrics remain explicit gaps."],
      ['assess',"Check a conclusion","What is already supported?",`<b>Claim and criterion</b>${api('get_hypothesis')}`,`<b>Measurements or proof</b>${api('get_related','list_derivations')}`,`<b>An assessment with grounds</b><small>The agent explains the status and limits of the conclusion</small>`, "When a new assessment is justified, the agent updates the same ID through update_hypothesis and reads the result back."],
      ['literature-check',"Compare with the literature","Where do our results differ?",`<b>Our claim</b>${api('find_related_papers')}`,`<b>The paper’s claims and sources</b>${api('get_paper','list_paper_claims')}`,`<b>Agreement or contradiction</b><small>Accounting for data, assumptions, and scope of applicability</small>`, "Search suggests related work. The agent establishes a substantive relationship after reading it; similar wording does not prove support."],
      ['gaps',"Find open issues","What is missing for a conclusion?",`<b>Database state</b>${api('lab_health')}`,`<b>Check the detected gap</b><small>Missing tests, evidence, numerical metrics, or decision support</small>`,`<b>A clear next step</b><small>What to record, clarify, or test</small>`, "Structural checks identify omissions. They do not declare a hypothesis false or automatically assess scientific quality."],
      ['resume',"Resume work","What has changed since last time?",`<b>New records</b>${api('recent_changes')}`,`<b>History and context</b>${api('get_timeline','get_project_context')}`,`<b>Change summary</b><small>New results, decisions, and remaining questions</small>`, "The agent compiles a summary from recorded history and the project’s open questions, preserving links to supporting grounds."]
    ];
    return `<div class="mem-analysis-scenarios"><header class="mem-flow-heading"><h3>After search: understand the result</h3><p>MCP returns records and relationships. A researcher or agent checks their meaning, compares data, and draws a conclusion.</p></header>${cases.map(([id,label,title,a,b,c,note])=>`<article class="mem-analysis-case" data-scenario="${id}"><div><span class="mem-label">${label}</span><h4>${title}</h4></div><div class="mem-walk-path"><span>${a}</span>${arrow}<span>${b}</span>${arrow}<span>${c}</span></div><p>${note}</p></article>`).join('')}<div class="mem-useful-context"><span><b>Who works on this topic</b>${api('who_works_on_what')}</span><span><b>Which resources are available</b>${api('list_lab_resources')}</span><span><b>What the project’s terms mean</b>${api('list_terms')}</span></div></div>`;
  }

  function retrieval(){
    return `<section class="mem-chapter" aria-labelledby="mem-search-title" data-chapter="search">
      <header class="mem-chapter-heading"><div><span class="mem-label">Working with accumulated knowledge</span><h2 id="mem-search-title">Find. Compare.<br><em>Understand what the results imply.</em></h2></div><p>Search retrieves material. Then you can assess a claim, compare experiments, identify gaps, or continue someone else's work with its context.</p></header>
      <div class="mem-readers"><span class="mem-label">Who queries the database</span><span>Researcher</span><span>Codex / Claude Code</span><span>Literature Hermes</span><span>Hermes for experiments</span><small>Question or task → MCP tools → records with sources</small></div>
      <div class="mem-search-map mem-diagram" data-map="search">${svg}
        ${station('query',"Start with a question","Search by query",`<blockquote>“What is known about this method and its limitations?”</blockquote><p>Search the whole database, only our work, or only the library. You can select a record type.</p>${api('search_lab')}`)}
        ${station('words',"Lexical retrieval","By words","<p>PostgreSQL searches words and their forms. Russian, English, and the terminology dictionary help match names.</p>")}
        ${station('vectors',"Semantic retrieval","By meaning","<p>multilingual-E5-large turns the question and documents into vectors. Cosine similarity finds related meaning expressed in different words.</p>")}
        ${station('merge',"Two corpora","Merge","<p>Papers and our records enter one candidate set. Duplicates are removed; matches in both branches strengthen a result.</p><small>RRF breaks ranking ties.</small>")}
        ${station('graph',"Context","Add relationships","<p>Related tests, measurements, and decisions are added to the retrieved records.</p><small>Up to 3 starting records, 2 neighbors each, and 6 additions.</small>")}
        ${station('rerank',"One ranking","Refine relevance","<p>Jina compares the question with each candidate after related records are added.</p><div class=\"mem-model\"><span>Cross-encoder</span><b>Jina reranker v2</b><small>multilingual · INT8</small></div>")}
        ${station('answer',"Result","A record with supporting grounds","<ul class=\"mem-answer-fields\"><li>ID and type</li><li>Statement / excerpt</li><li>Source and project</li><li>Related records</li></ul><p>The agent reads the complete record and answers with references. Search scores indicate relevance, not truth.</p>")}
      </div>
      <div class="mem-search-settings"><p><b>Modes:</b> hybrid combines words and meaning; lexical and semantic use just one branch. Filtering to a specific project excludes the shared library.</p><p><b>Current settings:</b> Jina INT8, 16 threads; up to 60 candidates and 400 characters per document. If E5 is unavailable, lexical search remains; without the reranker, the previous ranking is preserved.</p></div>
      ${analysisScenarios()}
      <div class="mem-walks"><h3>Start with a topic, project, or known record</h3>
        <div class="mem-walk" data-route="topic"><div><span class="mem-label">Explore a research area</span><h4>From topics to projects</h4></div><div class="mem-walk-path"><span><b>Laboratory topics</b>${api('list_themes')}</span>${arrow}<span><b>Topic context</b>${api('get_theme_context')}</span>${arrow}<span><b>Projects and claims</b><small>Our research + literature</small></span></div></div>
        <div class="mem-walk" data-route="library"><div><span class="mem-label">Browse the library</span><h4>From a section to a paper</h4></div><div class="mem-walk-path"><span><b>Section → folder</b>${api('library_tree')}</span>${arrow}<span><b>Subtopic → papers</b><small>Abstracts help choose a branch</small></span>${arrow}<span><b>Paper → claims</b>${api('get_paper','list_paper_claims')}</span></div><p>The tree is read directly, without vectors or ranking. Papers without a subtopic remain visible.</p></div>
        <div class="mem-walk" data-route="known"><div><span class="mem-label">A known object</span><h4>From a project or ID</h4></div><div class="mem-walk-path"><span><b>Project</b>${api('get_project_by_slug')}</span>${arrow}<span><b>Summary → relevant section</b>${api('get_project_context')}</span>${arrow}<span><b>Complete record</b>${api('get_hypothesis','get_paper')}</span></div><p>Start with a compact summary, then open selected records. There is no need to load the project's entire history.</p></div>
        <div class="mem-walk" data-route="evidence"><div><span class="mem-label">Check the grounds</span><h4>From a claim to its test</h4></div><div class="mem-walk-path"><span><b>Known record</b><small>Stable ID</small></span>${arrow}<span><b>Tests and sources</b>${api('get_related')}</span>${arrow}<span><b>Change history</b>${api('get_timeline')}</span></div><p>These are explicit stored relationships. Their provenance can be checked, and the status history can be read.</p></div>
        <div class="mem-walk" data-route="neighbors"><div><span class="mem-label">Broaden the question</span><h4>Find related ideas</h4></div><div class="mem-neighbor-paths"><span><b>Shared terms</b>${api('related_by_terms')}<small>Related subject matter, not an established relationship</small></span><span><b>Literature around a hypothesis</b>${api('find_related_papers')}<small>By statement and mechanism</small></span><span><b>Similar records before a write</b>${api('find_similar')}<small>Potential duplicates; the agent decides</small></span></div></div>
      </div>
      <div class="mem-vector-cache"><div><span class="mem-label">Preparing semantic search</span><h3>Vectors are reused</h3><p>Key: model + record ID + text hash. Changed text requires a new vector.</p></div><div class="mem-cache-path"><span><b>Text</b><small>Warm-up or a new query</small></span>${arrow}<span><b>E5</b><small>Record vector</small></span>${arrow}<span><b>PostgreSQL</b><small>retrieval_embeddings</small></span>${arrow}<span><b>In-memory cache</b><small>Reuse</small></span></div><p>An existing vector is read from memory or the database. <code>warm_all.py</code> computes them ahead of time; a query computes up to 16 missing vectors per corpus. For questions about the laboratory's structure, search returns projects, sections, and subtopics, keeping semantic retrieval and reranking but skipping research-relationship traversal.</p></div>
    </section>`;
  }

  function accessGuide(){
    return `<section class="mem-chapter mem-access" id="mcp-access" aria-labelledby="mem-access-title">
      <header class="mem-chapter-heading"><div><span class="mem-label">Person · role · project</span><h2 id="mem-access-title">Laboratory access.<br><em>Permissions in your project.</em></h2></div><p>The agent acts on your behalf. Your personal key identifies who reads and changes records.</p></header>
      <div class="mem-access-steps"><span>Full name, username, and sponsor</span><i>→</i><span>Requested role</span><i>→</i><span>Andrey's approval</span><i>→</i><span>Personal key and instructions</span></div>
      <div class="mem-access-roles">
        <article><span class="mem-label">member</span><h3>Member</h3><p>Reads the shared database, adds literature, and creates and works in their own projects. Writing to someone else's project requires an invitation.</p></article>
        <article><span class="mem-label">manager</span><h3>Coordinator</h3><p>Member permissions, plus inviting people and managing members' keys. This does not automatically grant permission to change every project or global role.</p></article>
        <article><span class="mem-label">lead</span><h3>Laboratory lead</h3><p>Manages all projects, access, and global roles. Granted by a separate decision of the owner.</p></article>
      </div>
      <div class="mem-access-project"><h3>Each project has its own permissions</h3><dl><div><dt>Reader <code>viewer</code></dt><dd>Read records.</dd></div><div><dt>Contributor <code>contributor</code></dt><dd>Add, edit, and delete project records.</dd></div><div><dt>Project lead <code>lead</code></dt><dd>Work with records and invite contributors.</dd></div></dl><p>A project lead does not become a laboratory-wide lead. Creators receive the lead role in their own project.</p></div>
      <footer><a href="https://t.me/brainlab_server_access_bot" target="_blank" rel="noopener noreferrer">Open the access bot ↗</a><p>Choose Get access (“Получить доступ”), select MCP knowledge base (“База знаний MCP”) in the shared resource list, and choose a role. A requested role takes effect only after approval. The key works until revoked; a repeat application does not downgrade existing permissions.</p></footer>
    </section>`;
  }

  function render(p, processes){
    return `<div class="process-shell memory-observatory" style="--accent:#b9ff66">
      <header class="mem-header"><div><button class="back-button" data-back type="button">← All of Atlas</button><span class="mem-coordinate">BRAIn Lab / Lab Knowledge MCP</span></div></header>
      ${anatomy()}
      <header class="mem-chapter-heading mem-overview-heading"><div><span class="mem-label">Where knowledge comes from</span><h2>How work becomes <em>knowledge</em></h2></div></header>
      <section class="mem-first-map" aria-label="Overview: sources, claims, and personal memory" data-chapter="overview">${overview(processes)}<div class="mem-practice-notes"><p><b>When it is saved:</b> during work and at checkpoints. The hook reminds the agent; the agent selects the content, saves it, and reads it back.</p><p><b>Where tasks live:</b> shared tasks in Yonote, personal tasks in Operon. Hermes keeps its own Kanban; Python updates a read-only view in the project's Obsidian folder.</p></div></section>
      ${ingestion()}${retrieval()}${accessGuide()}
      <footer class="mem-footer"><p>These diagrams explain the system without exposing private database content. Record schema checked on 12-09-2026; search models and settings checked on 10-09-2026.</p><a href="#mcp-live">Explore MCP records ↗</a><details class="mem-tools"><summary>Skills and tools in this layer</summary><div>${p.tools.map(t=>`<button type="button" data-skill="${esc(t.id)}">${esc(t.title)}</button>`).join('')}</div></details><a href="https://github.com/Vepricov/claude-brainlab/blob/main/docs/knowledge-base.md" target="_blank" rel="noopener noreferrer">Contract and source ↗</a></footer>
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
      dialog.innerHTML=`<button type="button" class="mem-record-close" aria-label="Close description">×</button><span class="mem-label">MCP structure <code>${esc(entry.code)}</code></span><h2 id="mem-record-title" tabindex="-1">${esc(entry.title)}</h2><p>${esc(entry.text)}</p><dl>${entry.fields.map(([title,text])=>`<div><dt>${esc(title)}</dt><dd>${esc(text)}</dd></div>`).join('')}</dl>${entry.example?`<aside><span class="mem-label">Illustrative example</span><p>${esc(entry.example)}</p></aside>`:''}`;
      dialog.querySelector('.mem-record-close').onclick=()=>dialog.close();dialog.showModal();dialog.scrollTop=0;dialog.querySelector('h2').focus({preventScroll:true});window.scrollTo(savedScroll);
    }));
    dialog.addEventListener('click',event=>{if(event.target!==dialog)return;const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close()});
    dialog.addEventListener('close',()=>{if(!dialog.isConnected||root.hidden)return;trigger?.focus({preventScroll:true});if(savedScroll)window.scrollTo(savedScroll)});
  }
  return {render,bind};
})();
