/* Первая страница «GitHub для идей». Данные — data/hub-data.js, их собирает
   scripts/export_tree_hub.py из дерева ~/brainlab (live.py пересобирает их на каждый коммит). */
(()=>{
  const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
  const num=n=>Number(n||0).toLocaleString(window.LAB_I18N?.language==="en"?"en-US":"ru-RU");
  const form=(n,f)=>{const a=Math.abs(n)%100,b=a%10;return a>10&&a<20?f[2]:b===1?f[0]:b>=2&&b<=4?f[1]:f[2]};
  const ago=t=>{
    const s=Math.max(0,Date.now()/1000-t),m=Math.round(s/60),h=Math.round(s/3600),d=Math.round(s/86400);
    if(m<60)return `${Math.max(m,1)} ${form(Math.max(m,1),["minute","minutes","minutes"])} ago`;
    if(h<24)return `${h} ${form(h,["hour","hours","hours"])} ago`;
    if(d<30)return `${d} ${form(d,["day","days","days"])} ago`;
    return new Date(t*1000).toLocaleDateString(window.LAB_I18N?.language==="en"?"en-US":"ru-RU");
  };
  const initials=n=>String(n).split(/\s+/).filter(Boolean).slice(0,2).map(x=>x[0]).join("").toUpperCase();
  const hue=n=>[...String(n)].reduce((a,c)=>a+c.charCodeAt(0),0)%360;
  const ext=(url,cls,inner,tag="div")=>url?`<a class="${cls}" href="${esc(url)}" target="_blank" rel="noopener">${inner}</a>`:`<${tag} class="${cls}">${inner}</${tag}>`;
  const avatar=(n,agent)=>`<span class="hub-avatar${agent?" is-agent":""}" style="--h:${hue(n)}" title="${esc(n)}${agent?" · agent":""}">${agent?"✦":esc(initials(n))}</span>`;

  // У каждой пары «для кода → для идей» свой цвет, как у процессов на карте системы.
  const MAP=[
    ["repository","Work","One research question and everything known about it: ideas, runs, manuscript, code.","#b9ff66","◫"],
    ["README","Claim","A testable idea and the condition under which we call it false. The condition is written before the test.","#8fb4ff","◇"],
    ["commit","Run","Its page is written by the training code itself: hyperparameters, metrics, commit, hardware.","#ffb86b","▶"],
    ["pull request","Proposal","New knowledge enters through a branch and a proposal. Both people and agents propose.","#c79bff","⑂"],
    ["CI","Checks","Code matches every number against the runs, and a judge model reads the text.","#5ee6d0","✓"],
    ["review · merge","Merge by the lead","Only what the work lead, a human, accepts becomes knowledge.","#ff8fb1","⇲"],
    ["git log · blame","History","Every number in a paper has an address and an author. Refuted results are never deleted.","#ffe17a","↺"],
    ["git clone","lab sync","The whole lab on your machine as one tree, and Obsidian opens the same tree.","#7fd3ff","⇣"],
  ];
  const CHIPS=[["A harness for the whole team","#b9ff66"],["A knowledge base that checks itself","#8fb4ff"],["Autonomous research 24/7","#ffb86b"],
    ["Zero made-up numbers","#5ee6d0"],["People and agents in one git","#c79bff"]];
  const STATE_CLASS={"supported":"ok","refuted":"no","inconclusive":"mid","under test":"run","draft":"draft","completed":"ok","failed":"no","running":"run"};
  const badge=s=>s?`<span class="hub-state is-${STATE_CLASS[s]||"draft"}">${esc(s)}</span>`:"";

  function tabPanel(tab,w,D,ev){
    if(tab==="claims")return `<ul class="hub-rows">${(D.claims||[]).map(c=>`<li><code>${esc(c.code)}</code><div><b>${esc(c.title)}</b><small>${num(c.runs)} runs · ${num(c.series)} series${c.theory?` · ${num(c.theory)} derivations`:""}</small></div>${badge(c.status)}</li>`).join("")}</ul>`;
    if(tab==="runs")return `<ul class="hub-rows">${(D.runs||[]).map(r=>`<li><code>${esc(r.code)}</code><div><b>${esc(r.title)}</b><small>under claim ${esc(r.claim)} · ${esc(r.updated.split("-").reverse().join("."))}</small></div>${badge(r.status)}</li>`).join("")}</ul><p class="hub-rows-more">Showing the latest 8 of ${num(w.runs)}. Each page was written by the code that computed it.</p>`;
    if(tab==="issues")return (D.issues||[]).length?`<ul class="hub-rows">${D.issues.map(x=>`<li><code>#${esc(x.n)}</code><div><b>${esc(x.title)}</b><small>${esc(String(x.who).replace(/\s*\(агент\)/,""))}${/агент/.test(x.who)?" · agent":""}</small></div><span class="hub-state is-run">open</span></li>`).join("")}</ul>`:`<p class="hub-rows-more">No open tasks.</p>`;
    if(tab==="mrs")return (D.mrs||[]).length?`<ul class="hub-rows">${D.mrs.map(x=>`<li><code>!${esc(x.n)}</code><div><b>${esc(x.title)}</b><small>awaiting the work lead's decision</small></div><span class="hub-state is-mid">in review</span></li>`).join("")}</ul><p class="hub-rows-more">Agents' proposals take the same path as people's: checks, then a human decision.</p>`:`<p class="hub-rows-more">All proposals reviewed.</p>`;
    return `<h3>${esc(w.title)}</h3><p>${esc(w.lead)}</p>
      <div class="hub-commit">${avatar(ev.who||"",ev.agent)}<b>${esc(ev.who||"")}</b><span>${esc(ev.s||"")}</span><time>${ev.t?esc(ago(ev.t)):""}</time></div>
      <ul class="hub-files">
        <li><span class="is-dir">claims/</span><em>${num(w.claims)} claims: what we think and what would refute it</em></li>
        <li><span class="is-dir">paper/</span><em>the manuscript, linked to the work</em></li>
        <li><span class="is-dir">code/</span><em>the code that computed it</em></li>
        <li><span>README.md</span><em>what the work is about and who leads it</em></li>
      </ul>
      <footer>${num(w.commits)} commits · ${num(w.merges)} accepted proposals · ${num(w.authors)} ${form(w.authors,["member","members","members"])}</footer>`;
  }

  function hero(H,tab){
    const w=H.showcase||{},D=H.detail||{},ev=w.last||(H.events||[]).find(e=>e.repo===w.slug)||{};
    const tabs=[["overview","Overview",""],["claims","Claims",w.claims],["runs","Runs",w.runs],["issues","Tasks",w.issues],["mrs","Proposals",w.mrs]];
    return `<section class="hub-hero">
      <div class="hub-hero-copy">
        <p class="hub-kicker">BRAIn Lab · MIPT</p>
        <h1>GitHub<br>for ideas.</h1>
        <div class="hub-chips">${CHIPS.map(([c,col])=>`<span style="--c:${col}">${esc(c)}</span>`).join("")}</div>
        <p class="hub-lead">Code has long had git: the history of every line, branches, review, merge. Ideas never had any of that. And when agents launch dozens of runs and review hundreds of papers overnight, knowledge without versions turns into noise.</p>
        <p class="hub-lead hub-lead-strong">We built for research what git became for code: every idea, run and number comes with its history, its checks and its author.</p>
        <div class="hub-actions">${H.gitlab?`<a class="hub-btn is-primary" href="${esc(H.gitlab)}" target="_blank" rel="noopener">Open the lab GitLab ↗</a>`:H.cta?`<a class="hub-btn is-primary" href="${esc(H.cta.href)}" target="_blank" rel="noopener">${esc(H.cta.label)}</a>`:""}<a class="hub-btn" href="#" data-hub-jump="chain">How knowledge grows ↓</a></div>
      </div>
      <div class="hub-window" data-hub-window>
        <header><i></i><i></i><i></i><span>brainlab / ${esc((w.path||"").split("/").slice(0,2).join(" / "))} / <b>${esc(w.slug)}</b></span></header>
        <nav role="tablist">${tabs.map(([id,l,n])=>`<button type="button" role="tab" data-hub-tab="${id}" class="${id===tab?"is-on":""}">${esc(l)}${n!==""?` <em>${num(n)}</em>`:""}</button>`).join("")}</nav>
        <div class="hub-window-body">${tabPanel(tab,w,D,ev)}</div>
      </div>
    </section>`;
  }

  function stats(T){
    const items=[[T.works,"works","each in its own repository","#b9ff66"],[T.commits,"commits","across the lab works","#8fb4ff"],[T.merges,"proposals accepted","each accepted by a human","#c79bff"],
      [T.runs,"runs","written by code, not by hand","#ffb86b"],[T.papers,"papers reviewed","in the theme literature","#5ee6d0"],[T.agentCommits,"commits by agents","the agent proposes, a human decides","#ff8fb1"]];
    return `<section class="hub-stats" aria-label="The base right now">${items.map(([v,l,n,c])=>`<div style="--c:${c}"><b>${num(v)}</b><span>${esc(l)}</span><small>${esc(n)}</small></div>`).join("")}</section>`;
  }

  function mapping(){
    return `<section class="hub-section"><p class="hub-kicker">What code has, ideas have too</p><h2>Everything people love about git, now for knowledge</h2>
      <div class="hub-pairs">${MAP.map(([a,b,c,col,ic])=>`<article style="--c:${col}"><header><code>${esc(a)}</code><i aria-hidden="true">→</i></header><b><span aria-hidden="true">${ic}</span>${esc(b)}</b><p>${esc(c)}</p></article>`).join("")}</div></section>`;
  }

  // Как маленький проверяемый кирпич становится статьёй. Пример — настоящая работа dykaf.
  function chain(H){
    const C=(H.detail||{}).chain||{},u=C.urls||{};
    const steps=[
      {c:"#ffb86b",k:"01 · run",t:"One launch",big:"3,1655",unit:"validation loss for DyKAF vs 3.1743 for SOAP",p:"LLaMA-124M on FineWeb, 128k steps. The run page is written by the code that computed it: config, metrics, commit, hardware. Neither a human nor an agent retypes the numbers.",who:"checked by deterministic code",href:u.run},
      {c:"#8fb4ff",k:"02 · series",t:"A series of runs",big:"6",unit:"runs answer one question",p:"“Is DyKAF better on long horizons?” A series gathers the runs and writes a verdict: at 32–128k steps DyKAF beats everyone, at 8k SOAP is ahead.",who:"Jev the judge: the verdict follows from the numbers",href:u.series},
      {c:"#5ee6d0",k:"03 · figure",t:"A plot in the paper",fig:C.figure,p:"Series become figures in the manuscript. This one is validation loss vs training time: DyKAF starts slower but reaches a lower loss at the same budget.",who:"the figure has an address: which runs it was built from"},
      {c:"#c79bff",k:"04 · claim",t:"The big hypothesis",big:num(C.runs),unit:`runs · ${num(C.series)} series · ${num(C.theory)} derivations`,p:C.claim||"",who:"accepted by the work lead",href:u.claim},
      {c:"#b9ff66",k:"05 · paper",t:"Manuscript",big:"AISTATS",unit:"the manuscript is submitted from this same work",p:"Every number in the text leads to a run, and the run leads to code. A reviewer can walk the whole path back.",who:"a script finds every number in the paper among the runs"}];
    return `<section class="hub-section" id="hub-chain"><p class="hub-kicker">How knowledge grows</p><h2>Big results start small and checkable</h2>
      <p class="hub-sub">A paper is not written off the top of your head. It is built from bricks, and each brick is checked before anything is laid on it.</p>
      <ol class="hub-chain">${steps.map(s=>`<li style="--c:${s.c}"><small>${esc(s.k)}</small><b>${esc(s.t)}</b>
        ${s.fig?`<figure><img src="${esc(s.fig)}" alt="Validation loss vs training time: DyKAF and SOAP" loading="lazy"></figure>`:`<strong class="${String(s.big).length>5?"is-word":""}">${esc(s.big)}</strong><em>${esc(s.unit)}</em>`}
        <p>${esc(s.p)}</p><span class="hub-who">✓ ${esc(s.who)}</span></li>`).join("")}</ol>
      <div class="hub-checks">
        <b>Not a single made-up number</b>
        <span style="--c:#5ee6d0"><i>1</i>Deterministic code matches every number against the runs and every citation against the bibliography. A rule either holds or it does not.</span>
        <span style="--c:#ffb86b"><i>2</i>Jev the judge reads the text: does the conclusion follow from the numbers, is there a retelling in place of a result.</span>
        <span style="--c:#b9ff66"><i>3</i>The work lead, a human, accepts what has already been checked. Without them nothing becomes knowledge.</span>
      </div>
      <div class="hub-theory">
        <div style="--c:#ffe17a"><small>theory · derivation</small><b>Accurate factors give an accurate basis</b><p class="hub-formula">‖off(Q<sup>⊤</sup>HQ)‖<sub>F</sub> ≤ ‖E‖<sub>F</sub></p><p>The proof sits under the same claim, next to the runs. A “Proof” section is mandatory.</p></div>
        <i aria-hidden="true">→</i>
        <div style="--c:#ff8fb1" class="is-next"><small>Lean 4 · in progress</small><b>Formal verification</b><p>Next step: every derivation is checked by Lean, a machine with no room for error. A human reads a proof that is already verified.</p></div>
        <i aria-hidden="true">→</i>
        <div style="--c:#c79bff"><small>claim</small><b>Theory and experiment agree</b><p>A claim stands on two pillars: the derivation and the runs. If one of them falls, you see it at once.</p></div>
      </div></section>`;
  }

  function why(){
    const cards=[
      ["#ffb86b","Agents write faster than people read","The server agent runs experiments overnight, and the paper pipeline reviews fresh papers every morning. Without history and review, that flow becomes noise."],
      ["#8fb4ff","A number without an address is not knowledge","Every number in a paper has the run it came from, and you can open it. A number that is not in the runs will not get past the checks."],
      ["#ff8fb1","Failure is a commit too","A refuted idea stays in the history along with its run. The next person or agent will not walk into the same dead end."]];
    return `<section class="hub-section"><p class="hub-kicker">Why now</p><h2>In the LLM era, ideas need versioning just like code</h2>
      <div class="hub-why">${cards.map(([c,t,p],i)=>`<article style="--c:${c}"><span>0${i+1}</span><h3>${esc(t)}</h3><p>${esc(p)}</p></article>`).join("")}</div></section>`;
  }

  function works(H,all){
    const list=all?H.works:H.works.slice(0,9);
    const card=w=>ext(w.url,"hub-repo",`
      <header><span class="hub-repo-icon" aria-hidden="true">◫</span><b>${esc(w.slug)}</b></header><small class="hub-repo-theme">${esc(w.theme)}</small>
      <p>${esc(w.lead||w.title)}</p>
      <footer><span class="hub-dot" style="--h:${hue(w.direction)}"></span>${esc(w.direction)}<span>◇ ${num(w.claims)}</span><span>▶ ${num(w.runs)}</span><span>⑂ ${num(w.merges)}</span>${w.mrs?`<span class="is-open">${num(w.mrs)} awaiting review</span>`:""}<time>${esc(ago(w.updated))}</time></footer>
      <div class="hub-people">${(w.leads||[]).map(n=>avatar(n,false)).join("")}</div>
    `);
    return `<section class="hub-section" id="hub-works"><div class="hub-section-head"><div><p class="hub-kicker">Repositories</p><h2>${H.public?"An open lab work":`Lab works <em>${num(H.works.length)}</em>`}</h2></div>
      ${H.gitlab?`<a class="hub-btn" href="${esc(H.gitlab)}" target="_blank" rel="noopener">All in GitLab ↗</a>`:""}</div>
      <p class="hub-legend"><span>◇ claims</span><span>▶ runs</span><span>⑂ accepted proposals</span></p>
      <div class="hub-repos">${list.map(card).join("")}</div>
      ${all||H.works.length<=9?"":`<button class="hub-more" type="button" data-hub-all>Show all ${num(H.works.length)}</button>`}</section>`;
  }

  function activity(H){
    return `<section class="hub-section hub-activity"><p class="hub-kicker">Live feed</p><h2>What is happening in the base</h2>
      <ol>${(H.events||[]).map(e=>`<li>${ext(e.url,"hub-event",`${avatar(e.who,e.agent)}
        <div><p><b>${esc(e.who)}</b>${e.agent?"<span class=\"hub-tag is-agent\">agent</span>":""}${e.merge?"<span class=\"hub-tag is-merge\">proposal accepted</span>":""} <span class="hub-in">in ${esc(e.repo)}${e.more?` and ${num(e.more)}`:""}</span></p><strong>${esc(e.s)}</strong></div>
        <time>${esc(ago(e.t))}</time>`)}</li>`).join("")}</ol></section>`;
  }

  function team(){
    const who=[
      ["Claude Code","on the researcher's machine","Thinks and writes: ideas, analysis, the paper text. Opens proposals to the base."],
      ["Hermes","on the server","Runs experiments right next to the GPUs and wakes up on its own when a run finishes. Remembers a project for weeks."],
      ["Jev","fast judge","In a fraction of a second it answers “yes or no” with a probability: it reads the text of every proposal, picks papers for our works, and decides what to save from a turn."],
      ["Human","work lead","Decides what to test and merges proposals. Without their merge nothing becomes knowledge."]];
    return `<section class="hub-section"><div class="hub-section-head"><div><p class="hub-kicker">Contributors</p><h2>The team is people and agents</h2></div><a class="hub-btn" href="#setup">How it works →</a></div>
      <div class="hub-team">${who.map(([n,w,t],i)=>`<article class="${i===3?"is-human":""}"><small>${esc(w)}</small><b>${esc(n)}</b><p>${esc(t)}</p></article>`).join("")}</div></section>`;
  }

  function render(view,opts={}){
    const H=window.LAB_HUB;
    if(!H){view.innerHTML=`<div class="hub-shell"><p class="hub-lead">Loading the base…</p></div>`;return}
    view.innerHTML=`<div class="hub-shell">${hero(H,opts.tab||"overview")}${stats(H.totals||{})}${mapping()}${chain(H)}${window.LAB_SEARCH_DEMO_PAGE?.section()||""}${why()}${works(H,opts.all)}${activity(H)}${team()}
      <section class="hub-cta"><h2>See for yourself</h2><p>${H.public?"The lab's harness, skills and rules are open: install them with one command.":"Everything on this page is a real lab repository."}</p>${H.gitlab?`<a class="hub-btn is-primary" href="${esc(H.gitlab)}" target="_blank" rel="noopener">Open the lab GitLab ↗</a>`:H.cta?`<a class="hub-btn is-primary" href="${esc(H.cta.href)}" target="_blank" rel="noopener">${esc(H.cta.label)}</a>`:""}</section></div>`;
    window.LAB_SEARCH_DEMO_PAGE?.bind(view);
    view.querySelectorAll("[data-hub-jump]").forEach(a=>a.onclick=e=>{e.preventDefault();view.querySelector(`#hub-${a.dataset.hubJump}`)?.scrollIntoView({behavior:"smooth",block:"start"})});
    view.querySelector("[data-hub-all]")?.addEventListener("click",()=>{const y=scrollY;render(view,{...opts,all:true});scrollTo(0,y)});
    // Вкладки окна работы переключаются на месте, без перехода в GitLab.
    view.querySelectorAll("[data-hub-tab]").forEach(b=>b.onclick=()=>{
      const W=window.LAB_HUB,w=W.showcase||{},ev=w.last||(W.events||[]).find(e=>e.repo===w.slug)||{};
      view.querySelectorAll("[data-hub-tab]").forEach(x=>x.classList.toggle("is-on",x===b));
      view.querySelector("[data-hub-window] .hub-window-body").innerHTML=tabPanel(b.dataset.hubTab,w,W.detail||{},ev);
      opts.tab=b.dataset.hubTab;
    });
  }

  window.LAB_HUB_PAGE={render};
})();
