(() => {
  "use strict";
  const model=window.RESEARCH_LOOP||{}, registry=window.LAB_ATLAS_DATA||{}, systemData=window.SYSTEM_EXAMPLES||{};
  const all=[model.shared,...(model.processes||[]),...(model.support||[]),...(model.contours||[])].filter(Boolean), byId=Object.fromEntries(all.map(x=>[x.id,x]));
  const $=id=>document.getElementById(id), arr=v=>(Array.isArray(v)?v:v?[v]:[]).filter(Boolean);
  const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
  const safe=v=>{try{const u=new URL(v);return u.protocol==="https:"?u.href:null}catch{return null}};
  // 06-09-2026 набор доложен на main: русские инструкции по базе, хук проверки цитат и
  // проверка вылезаний опубликованы, поэтому из списка непубликованного они ушли.
  // Осталось то, что закрыто намеренно: служба базы, её навыки и начинка созвонов.
  const unpublishedMainPaths=["commands/publish-hypothesis.md","services/lab-knowledge/src/lab_knowledge/mcp_server.py","services/lab-knowledge/src/lab_knowledge/service.py","skills/call-notes/references/analysis-contract.md","skills/call-notes/references/evaluation-fixture.md","skills/call-notes/references/obsidian-meeting-template.md","skills/lab-knowledge/SKILL.md","skills/lab-project-onboarding/SKILL.md"];
  const liveSource=x=>{const url=safe(x.url),privateKnowledge=url?.startsWith("https://github.com/brain-lab-research/lab-knowledge"),missing=url&&url.startsWith("https://github.com/Vepricov/claude-brainlab/blob/main/")&&unpublishedMainPaths.some(path=>url.endsWith(path));return privateKnowledge?{label:"Внутренний репозиторий · доступ у участников",url:"https://github.com/Vepricov/claude-brainlab/blob/main/docs/knowledge-base.md"}:missing?{label:`${x.label||"Исходник"} · deployed source пока не опубликован`,url:"https://github.com/Vepricov/claude-brainlab/blob/main/docs/knowledge-base.md"}:{...x,url}};
  const qualityProcesses=()=>[...(model.qualityContour||[]),...(model.contours||[]),...(model.processes||[]).filter(x=>arr(x.touches).length)];
  const updateHash=value=>{if(location.hash!==`#${value}`)history.pushState(null,"",`#${value}`)};
  const replaceHash=value=>{if(location.hash!==`#${value}`)history.replaceState(null,"",`#${value}`)};

  function links(items=[]){const unique=[...new Map(items.map(liveSource).filter(x=>x.url).map(x=>[x.url,x])).values()],chosen=unique.find(x=>x.canonical)||unique[0];if(!chosen)return"";const label=chosen.label||(chosen.url.includes("github.com/")?"GitHub":"Документация");return `<a class="source-link" href="${esc(chosen.url)}" target="_blank" rel="noopener">${esc(label)} <span>↗</span></a>`}
  function head(label,title,text=""){return `<p class="section-label">${esc(label)}</p><div class="section-heading"><h2>${esc(title)}</h2>${text?`<p>${esc(text)}</p>`:""}</div>`}
  const previewIds={literature:["paperscout","paper-ingest","alphaxiv-mcp"],ideation:["research-ideation","grill-me","lab-knowledge-hypothesis"],calls:["brain-call","call-notes","yonote-call"],experiments:["hermes","experiment-log","run-monitoring"],results:["results-analysis","results-report","evidence-mcp"],writing:["astar-paper-review","review-response","ml-paper-writing"],presentation:["presentation-skill","paper-to-social"],"paper-qa":["literature-reviewer","citation-verification"]};
  const supportPreviewIds={access:["server-access-bot","server-fleet","server-status"]};
  function previews(p){const ids=p.mapFeatured||previewIds[p.id]||[],picked=ids.map(id=>(p.tools||[]).find(t=>t.id===id)).filter(Boolean),shown=[...picked,...(p.tools||[]).filter(t=>!picked.includes(t))].slice(0,3);return `${shown.slice(0,2).map(t=>`<button data-open="${esc(p.id)}" data-tool="${esc(t.id)}" type="button"><small>${esc(t.type||"tool")}</small>${esc(t.title)}</button>`).join("")}${(p.tools||[]).length>2?`<button class="more" data-open="${esc(p.id)}" type="button">Все ${p.tools.length} →</button>`:""}`}

  // Одна установка на весь набор. Владелец: «нужно, чтобы человек мог условно одной
  // кнопкой себе его скачать полностью». Стоит на первом экране, под опорными разделами.
  // Владелец: «там же ещё есть Гермес, и Брейн-кол, и MCP… сделай так, чтобы это всё было
  // написано, но аккуратно, минималистично и без лишних слов». Одна строка на часть:
  // имя, что это, как достаётся, ссылка. Свёрнутый список из семи фактов установки убран.
  function renderToolkit(){
    const box=$("toolkit"),k=model.meta?.toolkit;if(!box)return;
    if(!k){box.hidden=true;return}
    const pieces=(k.pieces||[]).map(x=>{const u=safe(x.url);
      return `<li><b>${esc(x.name)}</b><span>${esc(x.what)}</span><i>${esc(x.access)}</i>${u?`<a href="${esc(u)}" target="_blank" rel="noopener">GitHub <span aria-hidden="true">↗</span></a>`:`<em>ссылки пока нет</em>`}</li>`}).join("");
    box.innerHTML=`<div class="toolkit-head"><p class="overline">Забрать себе</p><h2 id="toolkit-title">${esc(k.title)}</h2><p>${esc(k.lead)}</p></div>
      <div class="toolkit-body"><pre><code>${(k.install||[]).map(esc).join("\n")}</code></pre>
      ${k.after?`<p class="toolkit-after">${esc(k.after)}</p>`:""}
      <div class="toolkit-links">${(k.links||[]).map(x=>`<a class="source-link" href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.label)}<i aria-hidden="true">↗</i></a>`).join("")}</div></div>
      ${pieces?`<ul class="toolkit-pieces">${pieces}</ul>`:""}`;
  }
  function renderLoop(){
    $("verified-date").textContent=`проверено ${model.meta?.verified||""}`;
    const loopItems=[...(model.processes||[]),...(model.contours||[])];
    $("loop-nodes").innerHTML=loopItems.map(p=>`<article class="loop-node${p.id==="paper-qa"?" loop-node-quality":""}" style="--node:${esc(p.color)}"><button class="loop-node-main" data-open="${esc(p.id)}" type="button"><span class="num">${esc(p.number)}</span><strong>${esc(p.title)}</strong><span class="verb">${esc(p.verb)}</span><span class="result">${esc(p.result)}</span></button><div class="node-satellites">${previews(p)}</div></article>`).join("");
    // Опорного слоя больше нет: код уехал в эксперименты, доступ к серверам — в нулевую точку.
    document.querySelectorAll("#overview [data-open]").forEach(b=>b.onclick=()=>b.dataset.tool?openQuickTool(b.dataset.open,b.dataset.tool,b):openProcess(b.dataset.open));
    document.querySelectorAll("#overview [data-surface]").forEach(b=>b.onclick=()=>showSurface(b.dataset.surface));
    $("knowledge-core").onclick=()=>openProcess("memory");
    renderTally();
  }
  function renderTally(){
    const tally=$("loop-tally");
    if(!tally)return;
    const base=window.LAB_BASE,lib=window.LAB_LIBRARY;
    tally.hidden=!(base&&lib);
    if(base&&lib){
      const n=k=>(base.records||[]).filter(r=>r.k===k).length;
      const both=(base.records||[]).filter(r=>r.k==="hypothesis"&&r.sup==="proof_and_numbers").length;
      const rows=[[n("hypothesis"),"утверждений",""],[n("experiment"),"прогонов",""],
        [n("evidence"),"измерений",""],[(lib.papers||[]).length,"статей разобрано",""],
        [both,"закрыты выкладкой и числами","is-lit"]].filter(([v])=>v);
      tally.innerHTML=rows.map(([v,label,cls])=>`<span class="${cls}"><b>${esc(String(v))}</b>${esc(label)}</span>`).join("")
        +`<em>Столько лежит в общей базе на сегодня. Каждая запись пришла одним вызовом MCP и связана с тем, из чего выросла.</em>`;
    }
  }

  const layouts={memory:"knowledge",literature:"observatory",ideation:"branches",calls:"routing",experiments:"control",results:"prism",writing:"spine",presentation:"storyboard",projects:"ports",engineering:"workbench",orchestration:"relay",access:"airlock","paper-qa":"quality"};
  // Первая фраза роли. Точка внутри имени файла (.tex, kanban.db, .bib) — не конец
  // предложения, поэтому режем только там, где за точкой идёт пробел и заглавная.
  function compactRole(text=""){const stop=text.indexOf(":");const head=stop>20?text.slice(0,stop):text;
    const m=head.match(/^[\s\S]*?[.!?](?=\s+[«"A-ZА-ЯЁ])/);return (m?m[0]:head).replace(/[.\s]+$/,"")}
  function toolLocation(id,currentProcessId=""){const ordered=currentProcessId?[byId[currentProcessId],...all.filter(x=>x.id!==currentProcessId)].filter(Boolean):all;for(const process of ordered){const tool=(process.tools||[]).find(x=>x.id===id);if(tool)return {process,tool}}return null}
  // Владелец: «я бы вообще вот это вот брал в каждом разделе, это как будто бы бесполезная
  // информация». До выбора узла панели просто нет; CSS скрывает пустую.
  function focusDefault(p){return ""}
  function focusList(title,values){const xs=arr(values);return xs.length?`<section><b>${esc(title)}</b>${xs.map(x=>`<span>${esc(x)}</span>`).join("")}</section>`:""}
  function toolStory(t){return {value:t.purpose||t.value||t.role,capabilities:arr(t.inside?.length?t.inside:t.capabilities),useCases:arr(t.when||t.useCases),outcomes:arr(t.outputs?.length?t.outputs:t.outcomes),afterSetup:t.afterSetup||arr(t.outputs)[0]||t.role,important:arr(t.limits||t.important)}}
  function toolValue(t){const story=toolStory(t);return `<div class="tool-value">${focusList("Как работает",story.capabilities)}${focusList("Результат",story.outcomes)}</div>`}
  const uniqueText=values=>[...new Set(arr(values).flatMap(arr).map(x=>String(x).trim()).filter(Boolean))];
  function dossierSection(title,values,cls="",ordered=false){const xs=uniqueText(values);if(!xs.length)return "";const tag=ordered?"ol":"ul";return `<section class="dossier-section ${cls}"><h3>${esc(title)}</h3><${tag}>${xs.map(x=>`<li>${esc(x)}</li>`).join("")}</${tag}></section>`}
  function dossierHead(t,p,titleId=""){return `<header class="dossier-head"><p class="dossier-kicker">${esc(t.type||"Инструмент")} · ${esc(p.title||"Atlas")}</p><h2${titleId?` id="${esc(titleId)}"`:""} tabindex="-1">${esc(t.title)}</h2><p class="dossier-lead">${esc(toolStory(t).value)}</p>${t.status==='in-development'?'<p class="sky-pending">В доработке</p>':''}</header>`}
  function dossierBody(t){
    const story=toolStory(t),start=t.start||t.adoption?.invoke||'',invoke=t.skillId?`$${t.skillId}`:'',src=(t.links||[]).map(liveSource).filter(x=>x.url),install=arr(t.adoption?.install);
    return `<div class="dossier-body"><div class="dossier-entry">${dossierSection("Когда пригодится",story.useCases)}<section class="dossier-section dossier-start"><h3>С чего начать</h3><p>${esc(start)}</p>${invoke?`<code>${esc(invoke)}</code>`:''}</section></div><div class="dossier-flow">${dossierSection("Как проходит работа",story.capabilities,"dossier-steps",true)}<aside class="dossier-result">${dossierSection("Результат",story.outcomes)}${dossierSection("Куда сохраняется",t.writes)}</aside></div>${dossierSection("Данные и хранение",t.storage,"dossier-storage")}${window.LAB_OBSIDIAN_SETUP?.render(t.id)||''}${t.adoption?.installNote||install.length||src.length?`<footer class="dossier-footer">${install.length?`<details class="dossier-install"><summary>Команды подключения</summary>${t.adoption?.installNote?`<p>${esc(t.adoption.installNote)}</p>`:''}<pre class="setup-install"><code>${install.map(esc).join("\n")}</code></pre></details>`:t.adoption?.installNote?`<p>${esc(t.adoption.installNote)}</p>`:''}${src.length?`<div class="dossier-links">${src.map(x=>`<a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.label||"Исходный код")} ↗</a>`).join('')}</div>`:''}</footer>`:''}</div>`;
  }
  function adoptionLabel(kind="internal"){return ({"toolkit-skill":"Навык из набора BRAIn Lab","toolkit-command":"Команда из набора BRAIn Lab","toolkit-agent":"Агент из набора BRAIn Lab","toolkit-qa":"Проверка из набора BRAIn Lab",mempalace:"Публичный пакет MemPalace",zotero:"Zotero MCP","connector-unpackaged":"Отдельное подключение AlphaXiv","brain-call":"Отдельный закрытый репозиторий Brain Call",hermes:"Среда Hermes Agent","hermes-profile-missing":"Профиль Hermes пока не опубликован","lab-hermes-component":"Агент проекта на сервере",privileged:"Только через заявку и одобрение","source-only":"Ставится по документации источника",private:"Нужен доступ к лаборатории",internal:"Внутренний компонент"})[kind]||"Отдельный компонент"}
  // Владелец: «как работает внутри или полную карточку — я бы убирал, это просто тупо
  // занимает место», «нужна большая кнопка: установить себе или подробнее». Осталось
  // описание, что делает, и ссылка на настоящий репозиторий. Подробности — в досье ниже.
  function focusTool(t,related=[],currentProcessId=""){
    const story=toolStory(t),src=(t.links||[]).map(liveSource).filter(x=>x.url),
      neighbours=arr(t.relations).map(x=>({...x,location:toolLocation(x.toolId,x.processId||currentProcessId)})).filter(x=>x.location).slice(0,4);
    return `<div class="focus-head"><span class="map-focus-kicker">${esc(t.type||"Инструмент")}</span><button data-reset-focus type="button" aria-label="Закрыть карточку">×</button><h3 tabindex="-1">${esc(t.title)}</h3><p>${esc(story.value)}</p></div>${toolValue(t)}${src.length?`<div class="focus-take">${src.map((x,i)=>`<a class="focus-take-link${i?"":" is-primary"}" href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.label||"Исходник на GitHub")}<i aria-hidden="true">↗</i></a>`).join("")}</div>`:`<p class="focus-take-none">${esc(adoptionLabel(t.adoption?.kind))}</p>`}${neighbours.length?`<div class="focus-related"><b>Работает вместе с</b>${neighbours.map(x=>`<button data-open-process="${esc(x.location.process.id)}" data-open-tool="${esc(x.location.tool.id)}" type="button">${esc(x.title||x.location.tool.title)}</button>`).join("")}</div>`:""}`
  }
  function openQuickTool(processId,toolId,trigger){
    const process=byId[processId],tool=process?.tools?.find(x=>x.id===toolId);if(!tool)return;
    if(process.constellation){openProcess(processId,toolId);return}
    let dialog=$("quick-tool-dialog");if(!dialog){dialog=document.createElement("dialog");dialog.id="quick-tool-dialog";dialog.className="quick-tool-dialog";document.body.append(dialog)}
    dialog.classList.add("dossier-dialog");dialog.setAttribute("aria-labelledby","quick-tool-title");
    dialog.innerHTML=`<article class="dossier" style="--accent:${esc(process.color||"#b9ff66")}"><div class="dossier-toolbar"><button class="quick-close dossier-close" type="button" aria-label="Закрыть карточку">×</button></div>${dossierHead(tool,process,"quick-tool-title")}${dossierBody(tool)}</article>`;
    dialog.querySelector(".quick-close").onclick=()=>dialog.close();dialog.onclick=e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close()}};dialog.addEventListener("close",()=>trigger?.focus({preventScroll:true}),{once:true});dialog.showModal();dialog.scrollTop=0;dialog.querySelector("h2")?.focus({preventScroll:true})
  }
  function sectionMap(p){return `<section class="section-map process-section" id="map" data-layout="${esc(layouts[p.id]||"system")}"><div class="map-heading"><div><p class="section-label">Интерактивная карта раздела</p><h2>${esc(p.verb)}</h2></div><div class="map-legend"><span><i class="legend-tool"></i>инструмент</span><span><i class="legend-stage"></i>этап</span><span><i class="legend-gate"></i>решение</span><span><i class="legend-destination"></i>хранилище</span></div></div><div class="section-map-canvas"><div class="map-context"><span>Когда начинается</span>${arr(p.when).map((x,i)=>`<button data-map-copy="${esc(x)}" data-map-title="Сигнал ${i+1}" type="button">${esc(x)}</button>`).join("")}</div><div class="map-tools"><span>Курируемое ядро · ${(p.tools||[]).length}</span>${(p.tools||[]).map((t,i)=>`<button class="map-tool" data-focus-tool="${esc(t.id)}" style="--i:${i}" type="button"><small>${esc(t.type||"Инструмент")}</small><strong>${esc(t.title)}</strong><em>${esc(compactRole(toolStory(t).value))}</em><i>Что умеет →</i></button>`).join("")}</div><button class="map-core" data-map-reset type="button"><small>${esc(p.number)}</small><strong>${esc(p.title)}</strong><span>${esc(p.result)}</span></button><div class="map-journey"><span>Путь работы</span>${(p.stages||[]).map((s,i)=>`<button class="map-stage${s.human?" is-gate":""}" data-map-title="${esc(s.title)}" data-map-copy="${esc(s.summary)}" data-map-result="${esc(s.result)}" type="button"><small>${String(i+1).padStart(2,"0")}${s.human?" · человек":""}</small><strong>${esc(s.title)}</strong><em>${esc(s.result)}</em></button>`).join("")}</div><div class="map-destinations"><span>Что остается и где</span>${(p.destinations||[]).map(x=>`<button data-map-title="${esc(x.name)}" data-map-copy="${esc(x.what)}" data-map-result="${esc(x.why)}" type="button"><small>Хранилище</small><strong>${esc(x.name)}</strong><em>${esc(x.what)}</em></button>`).join("")}${(p.outcomes||[]).map(x=>`<button class="map-output" data-map-title="Результат" data-map-copy="${esc(x)}" type="button"><small>Объект</small><strong>${esc(x)}</strong></button>`).join("")}</div></div><aside class="map-focus" tabindex="-1" aria-live="polite">${focusDefault(p)}</aside></section>`}

  function normalizedMap(p){
    const stages=(p.stages||[]).map((s,i)=>({...s,id:s.ref||s.id||`s${i+1}`}));
    const destinations=(p.destinations||[]).map((d,i)=>({...d,id:d.ref||d.id||`d${i+1}`}));
    const outcomes=(p.outcomes||[]).map((o,i)=>typeof o==="string"?{id:`o${i+1}`,text:o}:{...o,id:o.ref||o.id||`o${i+1}`});
    const fallback=stages.map((stage,i)=>({id:`r${i+1}`,stage:stage.id,tools:(p.tools||[]).filter((_,j)=>j%stages.length===i).map(t=>t.id),destinations:destinations.length?[destinations[i%destinations.length].id]:[],outcomes:outcomes.length?[outcomes[i%outcomes.length].id]:[],qa:[]}));
    let relations=p.mapRelations?.length?p.mapRelations:fallback;
    if(relations[0]?.from){
      const edges=relations,toolIds=new Set((p.tools||[]).map(t=>t.id)),destinationIds=new Set(destinations.map(d=>d.id)),outcomeIds=new Set(outcomes.map(o=>o.id));
      relations=stages.map((stage,i)=>{const clusterTools=(p.toolClusters||[]).filter(c=>c.stageRef===stage.id).flatMap(c=>c.toolIds||[]),reachable=new Set([stage.id,...clusterTools]);for(let hop=0;hop<3;hop++)for(const edge of edges)if(reachable.has(edge.from)&&(toolIds.has(edge.to)||destinationIds.has(edge.to)||outcomeIds.has(edge.to)))reachable.add(edge.to);return {id:`r${i+1}`,stage:stage.id,tools:[...reachable].filter(x=>toolIds.has(x)),destinations:[...reachable].filter(x=>destinationIds.has(x)),outcomes:[...reachable].filter(x=>outcomeIds.has(x)),qa:arr(stage.qa)}});
    }
    relations=stages.map((stage,i)=>{const current=relations.find(x=>x.stage===stage.id);return current===undefined?fallback[i]:current});
    const applicableQa=qualityProcesses().filter(q=>arr(q.processIds||q.touches).includes(p.id)).map(q=>q.id);
    if(applicableQa.length)relations=relations.map(relation=>({...relation,qa:[...new Set([...arr(relation.qa),...applicableQa])]}));
    return {stages,destinations,outcomes,relations};
  }

  function clustersFor(p){
    if(p.toolClusters?.length)return p.toolClusters;
    const tools=p.tools||[],size=Math.max(1,Math.ceil(tools.length/3));
    return ["Ориентироваться","Выполнить","Проверить"].map((title,i)=>({id:`c${i+1}`,title,toolIds:tools.slice(i*size,(i+1)*size).map(t=>t.id)})).filter(c=>c.toolIds.length);
  }

  function knowledgeRuntime(km){
    const boundary=km.boundary||{},cards=[
      {title:"Что является системой",text:boundary.mcp,items:(km.corpora||[]).map(x=>`${x.title}: ${arr(x.contains).join(", ")}`)},
      {title:"Что делает навык lab-knowledge",text:boundary.skill,items:[km.read?.default,...arr(km.read?.behavior)]},
      {title:"Как читать",text:"Сначала область и права, затем поиск и только потом ответ с происхождением.",items:arr(km.read?.tools)},
      {title:"Как записывать",text:"Личный черновик не уезжает в общую память сам: сначала показать человеку, потом подтверждение, потом запись нужного типа, потом перечитывание записанного.",items:[...arr(km.write?.tools),...arr(km.write?.behavior)]},
      {title:"Как подключить агента",text:boundary.personal,items:arr(km.agentConnection)},
      {title:"Права и происхождение",text:"Политика применяется до поиска и записи; скрытые записи не угадываются по ответам сервиса.",items:[...arr(km.acl),...arr(km.provenance)]}
    ].filter(x=>x.text||x.items.some(Boolean));
    return `<div class="knowledge-runtime">${cards.map(x=>`<details><summary>${esc(x.title)}</summary>${x.text?`<p>${esc(x.text)}</p>`:""}<ul>${x.items.filter(Boolean).map(v=>`<li>${esc(v)}</li>`).join("")}</ul></details>`).join("")}</div><div class="knowledge-source-links">${links(km.sources||[],"Lab Knowledge")}</div>`;
  }

  function compactSectionMap(p){
    const map=normalizedMap(p),tools=Object.fromEntries((p.tools||[]).map(t=>[t.id,t])),qas=qualityProcesses().filter(q=>q.id!==p.id&&arr(q.touches).includes(p.id));
    const journey=`<nav class="journey-strip" style="--steps:${Math.min(map.stages.length,7)}" aria-label="Путь работы">${map.stages.map((s,i)=>`<button class="journey-step${s.human?" is-gate":""}" data-node="stage:${esc(s.id)}" aria-pressed="false" type="button"><small>${String(i+1).padStart(2,"0")}${s.human?" · решение человека":""}</small><strong>${esc(s.title)}</strong><span>${esc(s.result)}</span></button>`).join("")}</nav>`;
    const clusters=clustersFor(p).map(c=>`<section class="tool-cluster" data-cluster="${esc(c.id)}"><h3>${esc(c.title)}</h3><div>${arr(c.toolIds).map(id=>tools[id]).filter(Boolean).map(t=>{const story=toolStory(t),steps=arr(t.visual?.nodes).slice(0,5);return `<button class="tool-node${steps.length?" tool-node-major":""}" data-node="tool:${esc(t.id)}" aria-pressed="false" type="button"><small>${esc(t.type||"Инструмент")}</small><strong>${esc(t.title)}</strong><span>${esc(compactRole(story.value))}</span>${steps.length?`<ol>${steps.map(x=>`<li>${esc(x)}</li>`).join("")}</ol>`:""}<i aria-hidden="true">↗</i></button>`}).join("")}</div></section>`).join("");
    const destinations=`<aside class="destination-cluster"><h3>Результаты и места хранения</h3>${map.destinations.map(d=>`<button class="destination-node" data-node="destination:${esc(d.id)}" aria-pressed="false" type="button"><strong>${esc(d.name)}</strong><span>${esc(d.what)}</span></button>`).join("")}<div class="outcome-nodes"><p class="overline">Остаётся на этом этапе</p>${map.outcomes.map(o=>`<button data-node="outcome:${esc(o.id)}" aria-pressed="false" type="button">${esc(o.text)}</button>`).join("")}</div></aside>`;
    return `<section class="section-overview process-section" id="map" data-layout="${esc(layouts[p.id]||"system")}" data-process="${esc(p.id)}"><div class="map-heading"><div><p class="section-label">Интерактивная карта раздела</p><h2>${esc(p.verb)}</h2></div><div class="map-legend"><span><i class="legend-tool"></i>инструмент</span><span><i class="legend-stage"></i>этап</span><span><i class="legend-gate"></i>решение</span><span><i class="legend-destination"></i>хранилище</span></div></div>${journey}<div class="system-map"><div class="map-context-compact"><span>Когда включается</span>${arr(p.when).map(x=>`<p>${esc(x)}</p>`).join("")}</div><button class="process-hub" data-map-reset type="button"><small>${esc(p.number)}</small><strong>${esc(p.title)}</strong><span>${esc(p.result)}</span></button><div class="tool-clusters">${clusters}</div>${destinations}<i class="map-orbit one" aria-hidden="true"></i><i class="map-orbit two" aria-hidden="true"></i></div><aside class="map-focus graph-focus" id="map-focus-${esc(p.id)}" role="dialog" aria-modal="false" aria-label="Досье выбранного узла" tabindex="-1" aria-live="polite">${focusDefault(p)}</aside></section>`;
  }

  // ============ Центральная карта MCP, версия 4 ============
  // Владелец: «очень много текста, непонятно, что где связано, что откуда происходит… это может
  // быть много разных схем». Одна схема = одна мысль, у каждой явная ось, направление читается
  // без чтения текста: зелёное — путь записи, синее — путь чтения, янтарное — ворота.
  function kmFlow(steps,dir="right"){
    return `<ol class="km-flow" data-dir="${esc(dir)}">${(steps||[]).map(x=>`<li class="km-step${x.human?" is-human":""}"${x.id?` data-knowledge="intake:${esc(x.id)}"`:""}>
      <small>${x.human?"решает человек":(x.ops||[]).length?"через MCP":"шаг"}</small>
      <strong>${esc(x.title||"")}</strong>
      ${(x.ops||[]).length?`<span class="km-ops">${x.ops.map(o=>`<code>${esc(o)}</code>`).join("")}</span>`:""}
      ${x.note?`<p>${esc(x.note)}</p>`:""}</li>`).join("")}</ol>`;
  }
  function kmOverview(km){
    const src=(km.producers||[]),dst=(km.consumers||[]);
    return `<section class="km-block km-rail-block"><header><p class="section-label">Форма системы</p><h3>Четыре входа, одна база, три потребителя</h3></header>
      <div class="km-rail">
        <aside class="km-side"><span>Откуда приходит</span>${src.map(x=>`<button class="km-node" data-knowledge="producer:${esc(x.id)}" type="button"><strong>${esc(x.title)}</strong><em>${esc(x.short||"")}</em></button>`).join("")}</aside>
        <div class="km-core"><button class="km-node is-core" data-knowledge="boundary:mcp" type="button"><small>Единая точка чтения и записи</small><strong>Lab Knowledge</strong><em>общая проверяемая история лаборатории</em></button></div>
        <aside class="km-side"><span>Кто использует</span>${dst.map(x=>`<button class="km-node" data-knowledge="consumer:${esc(x.id)}" type="button"><strong>${esc(x.title)}</strong><em>${esc(x.short||"")}</em></button>`).join("")}</aside>
      </div></section>`;
  }
  function kmRecordTree(km,objectById,friendly){
    const t=km.tree;if(!t)return "";
    const node=(id,kind="Запись")=>{const x=objectById[id];return x?`<button class="km-leaf" data-knowledge="object:${esc(id)}" type="button"><small>${esc(kind)}</small><strong>${esc(friendly[id]||x.title)}</strong><span>${esc(x.plain||"")}</span></button>`:""};
    return `<section class="km-block"><header><p class="section-label">Что лежит в базе</p><h3>Два корня и общий контекст</h3></header>
      <div class="km-tree">${(t.roots||[]).map(r=>`<article class="km-branch"><h4>${esc(r.title)}</h4>${r.note?`<p>${esc(r.note)}</p>`:""}
        ${(r.chains||[]).map(c=>`<div class="km-chain"><span>${esc(c.label)}</span><div>${(c.objectIds||[]).map(id=>node(id)).join("")}</div></div>`).join("")}</article>`).join("")}</div>
      ${t.bridge?`<button class="km-bridge" data-knowledge="bridge:paper-to-work" type="button"><small>Пунктирная связь</small><strong>${esc(friendly[t.bridge.fromId]||t.bridge.fromId)} ⇢ ${(t.bridge.toIds||[]).map(x=>esc(friendly[x]||x)).join(", ")}</strong><em>${esc(t.bridge.label||"")}</em></button>`:""}
      <div class="km-context-bar"><span>Рабочий контекст: помогает понимать записи, но их типа не меняет</span><div>${(t.contextIds||[]).map(id=>node(id,"Контекст")).join("")}</div></div></section>`;
  }
  function kmIntake(km){
    const lanes=km.intake||[];if(!lanes.length)return "";
    return `<section class="km-block" id="km-intake"><header><p class="section-label">Как запись попадает в базу</p><h3>Четыре пути, и они различаются тем, кто решает</h3></header>
      <div class="km-lanes">${lanes.map(l=>`<article class="km-lane"><header><small>${esc(l.who||"")}</small><strong>${esc(l.title)}</strong><em>Решает ${esc(l.decides||"")}</em></header>${kmFlow(l.steps)}</article>`).join("")}</div>
      <div class="km-terminal">Все четыре пути кончаются одной записью в одной базе</div></section>`;
  }
  function kmHook(km){
    const h=km.hook;if(!h)return "";
    return `<section class="km-block km-hook"><header><p class="section-label">Хук</p><h3>Он не разбирает текст, он останавливает и требует</h3>
      <p>Срабатывает на ${esc(h.trigger||"")}. Стоит на ${esc(h.where||"")}. Решает ${esc(h.decides||"")}.</p></header>
      ${kmFlow(h.steps)}
      <div class="km-fanout">${(h.outputs||[]).map(o=>`<article class="${o.conditional?"is-conditional":""}"><strong>${esc(o.title)}</strong><p>${esc(o.what||"")}</p>${o.conditional?`<em>${esc(o.conditional)}</em>`:""}</article>`).join("")}</div>
      ${(h.ops||[]).length?`<div class="km-hook-ops"><b>Что он предлагает записать</b>${h.ops.map(o=>`<code>${esc(o)}</code>`).join("")}</div>`:""}
      ${(h.rules||[]).length?`<details class="km-hook-rules"><summary>Правила, по которым он живёт <span>${h.rules.length}</span></summary><ul>${h.rules.map(r=>`<li>${esc(r)}</li>`).join("")}</ul></details>`:""}
      ${h.history?`<div class="km-hook-history"><b>${esc(h.history.title||"Что попробовали и выбросили")}</b><p>${esc(h.history.what||"")}</p><p>${esc(h.history.why||"")}</p></div>`:""}
      ${links(h.links||[])}</section>`;
  }
  function knowledgeArchitecture(p){
    const km=p.knowledgeModel||{},objects=km.objectTypes||[],flow=km.publishFlow||[],producers=km.producers||[],consumers=km.consumers||[],friendly={hypothesis:"Утверждение",experiment:"Прогон",evidence:"Измерение",derivation:"Доказательство",decision:"Правило","paper-claim":"Утверждение статьи","paper-chunk":"Раздел статьи",paper:"Статья",journal:"Наблюдение",term:"Термин",resource:"Ресурс",project:"Работа",theme:"Тема","source-ref":"Источник"},objectById=Object.fromEntries(objects.map(x=>[x.id,x]));
    const objectButton=(id,kind="Запись")=>{const x=objectById[id];return x?`<button class="knowledge-record" data-knowledge="object:${esc(x.id)}" type="button"><small>${esc(kind)}</small><strong>${esc(friendly[x.id]||x.label||x.title_ru||x.title)}</strong><span>${esc(x.plain||x.summary||"")}</span></button>`:""};
    const personal=[{id:"obsidian",title:"Obsidian",action:"Личный черновик. В общую память попадает только после показа человеку и подтверждения."},{id:"mempalace",title:"MemPalace",action:"Память агента и история сессий. Помогает продолжить работу, но не является научным результатом."},{id:"yonote",title:"Yonote",action:"Общие задачи и страницы проектов. Ссылается на знание, но не заменяет его."}];
    const readSteps=[{id:"question",title:"Задать вопрос",summary:"Что уже проверяли?"},{id:"scope",title:"Определить область",summary:"Проект, тип записи и время"},{id:"policy",title:"Проверить доступ",summary:"Ответ по всей общей базе"},{id:"search",title:"Найти и пройти связи",summary:"Текст + граф отношений"},{id:"answer",title:"Ответить с источниками",summary:"коды записей, их происхождение и границы"}];
    const lc=km.lifecycle||{};
    const lifecycleBlock=lc.tracks?`<section class="knowledge-lifecycle process-section"><header><p class="section-label">Жизненный цикл записи</p><h2>Два пути от утверждения до правила</h2><p>${esc(lc.intro||"")}</p></header><div class="lifecycle-tracks">${lc.tracks.map(t=>`<article class="lifecycle-track"><h3>${esc(t.title)}</h3><span class="lifecycle-chain">${esc(t.chain)}</span><ol>${t.steps.map(x=>`<li><code>${esc(x.op)}</code><strong>${esc(x.title)}</strong><span class="lifecycle-needs">${esc(x.needs)}</span><em>${esc(x.gives)}</em><p>${esc(x.note)}</p></li>`).join("")}</ol></article>`).join("")}</div>${lc.verdictOnEdge?`<p class="lifecycle-verdict">${esc(lc.verdictOnEdge)}</p>`:""}<details class="lifecycle-statuses"><summary>Статусы и их переходы <span>${(lc.statuses||[]).length} рода записей</span></summary><div>${(lc.statuses||[]).map(g=>`<article><h4>${esc(g.title)}<code>${esc(g.tool)}</code></h4><p>${esc(g.rule)}</p><dl>${g.values.map(v=>`<dt><code>${esc(v.value)}</code> ${esc(v.means)}</dt>${v.exit?`<dd>Выход: ${esc(v.exit)}</dd>`:""}`).join("")}</dl></article>`).join("")}</div></details><details class="lifecycle-kinds"><summary>Роды внутри типов <span>чем один род отличается от другого</span></summary><table><thead><tr><th>Род чего</th><th>Значения</th><th>Зачем различать</th></tr></thead><tbody>${(lc.kinds||[]).map(k=>`<tr><td>${esc(k.of)}</td><td><code>${esc(k.values)}</code></td><td>${esc(k.why)}</td></tr>`).join("")}</tbody></table></details></section>`:"";
    const route=(name,kind,items)=>`<nav class="knowledge-route ${kind}-route" aria-label="${esc(name)}"><h3>${esc(name)}</h3>${items.map((x,i)=>`<button data-knowledge="${kind}:${esc(x.id)}" type="button"><small>${String(i+1).padStart(2,"0")}</small><strong>${esc(x.title)}</strong><span>${esc(x.summary||"")}</span></button>`).join("")}</nav>`;
    return `<section class="knowledge-architecture knowledge-atlas-v3 process-section" id="map"><header class="knowledge-intro"><p class="section-label">Центральная карта</p><h2>Как знание проходит через лабораторию</h2><p>Запись проходит две обязательные границы: доступ до действия и происхождение после сохранения. Чтение возвращает не только ответ, но и проверяемые источники.</p></header><div class="knowledge-map-frame"><div class="knowledge-stack"><div class="km-gates"><button class="km-gate" data-knowledge="guard:access" type="button"><small>До чтения и записи</small><strong>Доступ</strong><span>Личность по ключу · роль в лаборатории · роль в работе для записи</span></button><button class="km-gate" data-knowledge="guard:provenance" type="button"><small>Для каждой сохранённой записи</small><strong>Происхождение</strong><span>Источник · автор или агент · время · история изменений</span></button></div>${kmOverview(km)}${kmRecordTree(km,objectById,friendly)}${kmIntake(km)}${kmHook(km)}<section class="km-block km-read"><header><p class="section-label">Как из базы читают</p><h3>Вопрос ничего не меняет</h3></header>${route("Прочитать","read",readSteps)}</section><section class="km-block km-neighbours"><header><p class="section-label">Соседние системы</p><h3>Не вторая копия общей памяти</h3></header><div>${personal.map(x=>`<button data-knowledge="personal:${esc(x.id)}" type="button"><strong>${esc(x.title)}</strong><span>${esc(x.action)}</span></button>`).join("")}</div><p class="km-blocked">Обмен идёт ссылками и явными сценариями: изменяемая копия у каждого типа данных остаётся одна.</p></section></div><aside class="knowledge-inspector" id="knowledge-inspector" role="region" aria-label="Досье выбранного узла Lab Knowledge" tabindex="-1" aria-live="polite"></aside></div>${lifecycleBlock}<details class="knowledge-technical"><summary>Техническое устройство и подключение <span>PostgreSQL · MCP · права доступа · журнал изменений</span></summary>${knowledgeRuntime(km)}</details></section>`;
  }

  function glossaryBlock(p){
    const terms=(model.glossary||model.shared?.glossary||p.glossary||[]).filter(t=>!t.processIds?.length||t.processIds.includes(p.id));
    if(!terms.length)return"";
    // Четыре термина одинаковы на всех тринадцати страницах. Разворачивать их
    // на каждой значило бы тринадцать раз повторить одно и то же, поэтому здесь
    // они свёрнуты, а на странице общего знания, где они и есть предмет, открыты.
    return `<section class="process-section glossary-section"><details class="glossary-details"${p.id==="memory"?" open":""}><summary>Словарь карты <span>что означают слова здесь</span></summary><div class="glossary-grid">${terms.map(t=>`<article id="term-${esc(t.id)}"><small>${esc(t.scope||"Термин")}</small><h3>${esc(t.term)}</h3><p>${esc(t.definition||t.meaning)}</p>${t.example?`<div><b>Пример</b>${esc(t.example)}</div>`:""}${t.not?`<div><b>Не означает</b>${esc(t.not)}</div>`:""}${links((t.links||[]),t.term)}</article>`).join("")}</div></details></section>`;
  }

  // Команда установки — то, за чем посетитель и пришёл. Ровно один блок на карточку,
  // чтобы выделялся и копировался целиком; кнопка копирования не нужна.
  // Владелец: «тут не должна быть такой штуки, должна быть просто ссылка на GitHub, и всё.
  // Не надо это отдельно прописывать и размусоливать». Осталось ровно то, что нужно
  // сделать: команда, если она есть, и ссылка на источник.
  // Посетитель пришёл посмотреть, что можно унести к себе. Это решается одним
  // свойством, поэтому оно стоит прямо в строке заголовка карточки.
  const TAKEABLE=new Set(["toolkit-skill","toolkit-command","toolkit-agent","toolkit-qa","mempalace","zotero","source-only","connector-unpackaged","hermes"]);
  const takeBadge=t=>{const k=t.adoption?.kind||"internal";
    return TAKEABLE.has(k)?`<span class="take-badge is-open">можно забрать</span>`:k==="privileged"?`<span class="take-badge is-gated">по заявке</span>`:`<span class="take-badge is-closed">внутреннее</span>`};
  function toolCard(t){return `<details class="tool" id="tool-${esc(t.id)}"><summary><span class="tool-type">${esc(t.type||"Инструмент")}</span>${takeBadge(t)}<strong>${esc(t.title)}</strong><span class="tool-role">${esc(toolStory(t).value)}</span><i class="tool-toggle">+</i></summary><div class="tool-body dossier">${dossierBody(t)}</div></details>`}
  // Владелец: «команды не нужны, оставляем только навыки, потому что по факту это дубликат».
  function related(p){const ids=new Set(p.registryProcessIds||[]);return (registry.capabilities||[]).filter(c=>c.type!=="command"&&arr(c.process_ids).some(id=>ids.has(id)))}
  function capCard(c){return `<button class="capability" data-capability="${esc(c.id)}" type="button"><span>${esc(capType(c.type))}</span><strong>${esc(c.title_ru||c.name)}</strong><p>${esc(c.description_ru||c.description||"")}</p><i>Подробно →</i></button>`}
  // Тип возможности приходит из машинного реестра по-английски. На витрине он
  // стоит подписью над названием, поэтому переводится здесь, а не в данных.
  const CAP_TYPE={agent:"Агент",skill:"Навык",command:"Команда",hook:"Хук","mcp-tool":"Инструмент MCP",service:"Служба",documentation:"Документация",repository:"Репозиторий"};
  const capType=t=>CAP_TYPE[t]||t||"Возможность";
  function capabilityGroups(caps){const labels={agent:"Агенты",skill:"Навыки",command:"Команды",hook:"Хуки","mcp-tool":"Инструменты MCP",service:"Службы",documentation:"Документация",repository:"Репозитории"},groups=caps.reduce((out,c)=>{const archived=c.current_status==="archived"?"archived":c.type||"other";(out[archived]||=[]).push(c);return out},{});return `<div class="capability-groups">${Object.entries(groups).map(([key,xs])=>`<details class="capability-group"><summary>${esc(key==="archived"?"Архивные и устаревшие":labels[key]||key)} <span>${xs.length}</span></summary><div class="capability-list">${xs.map(capCard).join("")}</div></details>`).join("")}</div>`}
  function tools(p){const caps=related(p);return `<section class="process-section" id="tools">${head("Инструменты","Досье инструментов")}<div class="tools-intro"><span class="tools-count">${(p.tools||[]).length} основных${caps.length?` · ${caps.length} в полном реестре`:""}</span></div><div class="tool-list">${(p.tools||[]).map(toolCard).join("")}</div>${caps.length?`<details class="all-capabilities"><summary>Всё, что связано с этим разделом в репозитории <span>${caps.length}</span></summary>${capabilityGroups(caps)}</details>`:""}</section>`}
  function implementation(p){return p.implementation?`<details class="implementation"><summary>Техническая реализация <span>для поддержки и отладки</span></summary><div class="implementation-box"><p>${esc(p.implementation.summary)}</p><ul>${arr(p.implementation.items).map(x=>`<li>${esc(x)}</li>`).join("")}</ul>${p.implementation.links?.length?`<div class="tool-links">${links(p.implementation.links)}</div>`:""}</div></details>`:""}
  function nav(p){const seq=[...(model.processes||[]),...(model.contours||[])],i=seq.findIndex(x=>x.id===p.id);if(i<0)return `<nav class="process-nav"><button data-back type="button"><small>Вернуться</small><strong>← Карта работы</strong></button></nav>`;const prev=seq[(i-1+seq.length)%seq.length],next=seq[(i+1)%seq.length];return `<nav class="process-nav"><button data-open="${esc(prev.id)}" type="button"><small>Предыдущий этап</small><strong>← ${esc(prev.title)}</strong></button><button data-open="${esc(next.id)}" type="button"><small>Следующий этап</small><strong>${esc(next.title)} →</strong></button></nav>`}
  // ============ «Что уходит в общую базу» ============
  // Владелец: «нужно прям подробно расписать, прям подробный путь прохождения туда и как
  // это всё работает». Та же форма, что у пути статьи в поиске по базе: шаг = операция плюс
  // что именно на этом шаге появляется и по каким правилам. Ничего не сворачиваем.
  const TOMCP_TYPE={skill:"навык",command:"команда",mcp:"операция MCP",script:"скрипт",hook:"хук"};
  function toMcpStep(l,k){
    const cls=l.lane==="record"?"is-rec":l.lane==="tie"?"is-tie":"is-work";
    const op=k===0?"—":(l.via?.tool||"—");
    const kind=l.kind?`<em>${esc(l.kind)}${l.code&&l.code!=="—"?" · "+esc(l.code):""}</em>`:"";
    const items=(l.items||[]).length?`<ul>${l.items.map(x=>`<li>${esc(x)}</li>`).join("")}</ul>`:"";
    const via=k===0?"":`<small>${esc(TOMCP_TYPE[l.via?.type]||"")}${l.via?.gate?" · "+esc(l.via.gate):""}</small>`;
    // Тип шага стоит рядом с именем операции, а не последней строкой под описанием: там он
    // читался обрывком текста. Поэтому <small> — прямой ребёнок <li>, и сетка кладёт его
    // во вторую строку левой колонки, под <code>.
    return `<li class="${cls}"><code>${esc(op)}</code><div><strong>${esc(l.title||"")}</strong>${kind}${l.detail?`<span>${esc(l.detail)}</span>`:""}${items}</div>${via}</li>`;
  }
  function toMcpBlock(p){
    const t=p.toMcp;if(!t)return "";
    const paths=(t.paths||[]).map(x=>`<article class="tomcp-path">
      <header><small>${esc(x.actor||"")}</small><strong>${esc(x.title||"")}</strong>${x.line?`<span>${esc(x.line)}</span>`:""}</header>
      <ol class="tomcp-steps">${(x.chain||[]).map(toMcpStep).join("")}</ol></article>`).join("");
    const none=t.nothing?`<div class="tomcp-none"><strong>Отсюда в общую базу не уходит ничего</strong><p>${esc(t.nothing.why||"")}</p>${t.nothing.back?`<p>${esc(t.nothing.back)}</p>`:""}${t.nothing.instead?`<button data-open-process="${esc(String(t.nothing.instead).replace(/^process:/,""))}" type="button">${esc(t.nothing.insteadLabel||"Раздел, который пишет")}</button>`:""}</div>`:"";
    const kept=(t.kept||[]).length?`<p class="tomcp-kept"><b>Остаётся на месте:</b> ${esc(t.kept.join("; "))}.</p>`:"";
    return `<section class="process-section tomcp" id="mcp">
      <p class="section-label">Что уходит в общую базу</p>
      <h2>${esc(t.lead||"")}</h2>
      ${none}${paths?`<div class="tomcp-paths">${paths}</div>`:""}${kept}</section>`;
  }
  // Владелец: «их надо как-то красиво выделить, потому что кроме них ничем больше
  // пользоваться не надо. Главное — не запутать пользователей, потому что они могут
  // использовать не тот скилл, и он будет плохим».
  function pipelineSteps(steps){
    return `<ol>${steps.map(x=>`<li><code>${esc(x.op)}</code><div><strong>${esc(x.t)}</strong><em>${esc(x.m)}</em><p>${esc(x.d)}</p>${(x.n||[]).length?`<ul>${x.n.map(y=>`<li>${esc(y)}</li>`).join("")}</ul>`:""}</div></li>`).join("")}</ol>`;
  }
  // Владелец: «в брейн-коле тоже распиши, каким образом делается разбор речи, какая
  // моделька, как это передаётся, какой промпт у агента. Это всё важно, это интересно».
  function pipelineBlock(p){
    const pl=p.pipeline;if(!pl?.steps?.length)return "";
    return `<section class="process-section pipeline-section" id="pipeline">
      ${head("Как это устроено внутри",pl.title)}
      <div class="mcp-pipeline is-open">${pipelineSteps(pl.steps)}
      ${pl.note?`<p class="mcp-pipeline-note">${esc(pl.note)}</p>`:""}</div></section>`;
  }
  function spotlightBlock(p){
    const sp=p.spotlight;if(!sp?.toolIds?.length)return "";
    const picked=sp.toolIds.map(id=>(p.tools||[]).find(t=>t.id===id)).filter(Boolean);
    if(!picked.length)return "";
    return `<section class="process-section spotlight" id="spotlight"><p class="section-label">Пользуйтесь только этим</p>
      <p class="spotlight-lead">${esc(sp.lead||"")}</p>
      <div class="spotlight-grid">${picked.map(t=>{const src=(t.links||[]).map(liveSource).find(x=>x.url);
        return `<article><span>${esc(t.type||"Навык")}</span><h3>${esc(t.title)}</h3><p>${esc(compactRole(toolStory(t).value))}</p>
        <div class="spotlight-actions"><button data-open-dossier="${esc(t.id)}" type="button">Что делает и как поставить</button>${src?`<a href="${esc(src.url)}" target="_blank" rel="noopener">Исходник ↗</a>`:""}</div></article>`}).join("")}</div></section>`;
  }
  function galleryBlock(p){
    const g=p.gallery;if(!(g||[]).length)return "";
    return `<section class="process-section gallery" id="gallery"><div class="gallery-head"><p class="section-label">Как это выглядит</p><h2>Учебные примеры из навыка</h2></div>
      <div class="gallery-grid">${g.map(x=>`<figure><img src="${esc(x.src)}" alt="${esc(x.caption||"")}" loading="lazy" width="1200" height="675"><figcaption><strong>${esc(x.caption||"")}</strong>${x.note?`<span>${esc(x.note)}</span>`:""}</figcaption></figure>`).join("")}</div></section>`;
  }
  function skyName(t){return t.skyTitle||(t.id==='paperscout'?'Hermes Agent':t.skillId||t.title)}
  function skyKind(t){return t.skillId?'skill':/Агент|Среда|Agent|Environment/i.test(t.type||'')||t.id==='hermes'?'agent':/MCP|Интеграция|Хук|Integration|Hook/i.test(t.type||'')?'connection':'system'}
  function skyNode(t,p,index){
    const major=p.mapFeatured.includes(t.id),kind=skyKind(t);
    return `<button class="sky-node${major?' is-major':''}${index===0?' is-anchor':''}" data-skill="${esc(t.id)}" data-kind="${kind}" type="button" aria-haspopup="dialog" title="${esc(toolStory(t).value)}"><i class="star-pin" aria-hidden="true"></i><span><strong>${esc(skyName(t))}</strong>${t.status==='in-development'?'<span class="sky-pending">В доработке</span>':major?`<span class="sky-node-description">${esc(t.skySummary||t.catalogSummary||compactRole(toolStory(t).value))}</span>`:''}</span></button>`;
  }
  function externalBranch(t){
    if(!t.externalResources?.length)return '';
    return `<aside class="sky-external" data-external-from="${esc(t.id)}" aria-label="Сторонние сервисы для ${esc(skyName(t))}"><h3>Сторонние сервисы</h3>${t.externalResources.map(link=>
      `<a href="${esc(link.url)}" target="_blank" rel="noopener"><i class="external-pin" aria-hidden="true"></i><span>${esc(link.label)} <b aria-hidden="true">↗</b>${link.note?`<small>${esc(link.note)}</small>`:''}</span></a>`).join('')}</aside>`;
  }
  function constellationPage(p){
    const c=p.constellation,byTool=Object.fromEntries(p.tools.map(t=>[t.id,t])),cores=c.cores||[{toolId:c.core,area:'core',caption:c.caption}];
    const groups=c.groups.map((g,i)=>`<section class="sky-cluster" data-area="${esc(g.area)}" data-orbit="${g.independent?'':esc(g.core||c.core)}" style="grid-area:${esc(g.area)};--cluster:${i}">${g.externalFrom?externalBranch(byTool[g.externalFrom]):''}${g.title?`<h2>${esc(g.title)}</h2>`:''}<div>${g.toolIds.map((id,index)=>skyNode(byTool[id],p,index)+externalBranch(byTool[id])).join('')}</div></section>`).join('');
    const notes=[p.knowledgeModel?`<details class="chapter-note knowledge-chapter"><summary>Записи и связи в общей базе <i aria-hidden="true">+</i></summary>${knowledgeArchitecture(p).replace('id="map"','id="knowledge-map"')}</details>`:'',p.pipeline||p.implementation?`<details class="chapter-note"><summary>Внутреннее устройство <i aria-hidden="true">+</i></summary>${pipelineBlock(p)}${implementation(p)}</details>`:''].join('');
    const signal=p.id==='calls'?`<span class="core-signal" aria-hidden="true">${[15,27,42,23,52,34,19,44,26,38,16].map(h=>`<i style="height:${h}px"></i>`).join('')}</span>`:'<span class="core-moons" aria-hidden="true"><i></i><i></i><i></i></span>';
    const bodies=cores.map((entry,i)=>{const core=byTool[entry.toolId];return `<button class="sky-core" data-skill="${esc(core.id)}" data-core style="grid-area:${esc(entry.area)};--orbit-angle:${-65+i*43}deg" type="button" aria-haspopup="dialog"><span class="core-orbit" aria-hidden="true"></span>${signal}<span class="core-copy"><small>${esc(core.type||'Система')}</small><strong>${esc(skyName(core))}</strong><span>${esc(entry.caption)}</span>${c.cores?'':'<em>Открыть инструмент ↗</em>'}</span></button>`}).join('');
    return `<div class="process-shell sky-shell" style="--accent:${esc(p.color)}" data-chapter="${esc(p.id)}">
      <button class="back-button" data-back type="button">← Общая карта</button>
      <header class="sky-heading"><div><p class="sky-eyebrow">Созвездие ${esc(p.number)} · исследовательская система</p><h1 tabindex="-1">${esc(p.title)}</h1><p>${esc(p.verb)}</p></div><p class="sky-intro">${esc(p.purpose)}</p></header>
      <div class="sky-frame"><section class="sky-map${c.cores?' has-peers':''}" id="map" data-system="${esc(p.id)}" aria-label="Созвездие инструментов: ${esc(p.title)}">
        <svg class="sky-lines" aria-hidden="true"></svg><div class="sky-dust" aria-hidden="true"></div>
        ${bodies}${groups}<span class="sky-count" aria-label="Инструментов: ${p.tools.length}">${p.tools.length}</span>
      </section></div>
      ${galleryBlock(p)}<section class="chapter-notes" aria-label="Подробности процесса">${notes}</section>${nav(p)}
      <dialog class="skill-dialog" aria-labelledby="skill-dialog-title"></dialog>
    </div>`;
  }
  function drawConstellation(root,p){
    const map=root.querySelector('.sky-map'),svg=map?.querySelector('.sky-lines');if(root.hidden||!map||!svg)return;
    const frame=map.parentElement;
    if(matchMedia('(min-width:1024px)').matches){
      const available=innerHeight-(frame.getBoundingClientRect().top+scrollY)-16;
      const scale=Math.min(1,Math.max(1,available)/map.offsetHeight);
      map.style.setProperty('--sky-scale',scale);
      frame.style.height=`${map.offsetHeight*scale}px`;
    }else{map.style.removeProperty('--sky-scale');frame.style.removeProperty('height')}
    const box=map.getBoundingClientRect();
    const point=pin=>{const r=pin.getBoundingClientRect();return {x:r.left-box.left+r.width/2,y:r.top-box.top+r.height/2}};
    const cores=Object.fromEntries([...map.querySelectorAll('[data-core]')].map(e=>[e.dataset.skill,{...point(e),radius:e.getBoundingClientRect().width/2}]));
    const rim=(core,target)=>{const dx=target.x-core.x,dy=target.y-core.y,length=Math.hypot(dx,dy)||1;return {x:core.x+dx/length*core.radius,y:core.y+dy/length*core.radius}};
    const line=(a,b,kind,control)=>`<path class="${kind}" d="M${a.x.toFixed(1)},${a.y.toFixed(1)} ${control?`Q${control.x.toFixed(1)},${control.y.toFixed(1)} `:'L'}${b.x.toFixed(1)},${b.y.toFixed(1)}"/>`;
    let paths='';
    for(const [from,to] of p.constellation.links||[]){
      const a=cores[from],b=cores[to];
      // Bow long horizontal links around the helper clusters between the main bodies.
      const control=Math.abs(a.y-b.y)<1&&Math.abs(a.x-b.x)>a.radius+b.radius+200?{x:(a.x+b.x)/2,y:a.y+(a.y<box.height/2?-160:160)}:null;
      paths+=line(rim(a,control||b),rim(b,control||a),'sky-peer-link',control);
    }
    for(const group of map.querySelectorAll('.sky-cluster')){
      const stars=[...group.querySelectorAll('.star-pin')].map(point);if(!stars.length)continue;
      if(cores[group.dataset.orbit])paths+=line(rim(cores[group.dataset.orbit],stars[0]),stars[0],'sky-ray');
      for(let i=1;i<stars.length;i++)paths+=line(stars[i-1],stars[i],'sky-thread');
    }
    for(const branch of map.querySelectorAll('[data-external-from]')){
      const parent=map.querySelector(`[data-skill="${CSS.escape(branch.dataset.externalFrom)}"]`);
      const origin=cores[branch.dataset.externalFrom]||{...point(parent.querySelector('.star-pin')),radius:4};
      const stars=[...branch.querySelectorAll('.external-pin')].map(point);
      paths+=line(rim(origin,stars[0]),stars[0],'sky-external-ray');
      for(let i=1;i<stars.length;i++)paths+=line(stars[i-1],stars[i],'sky-external-thread');
    }
    svg.setAttribute('viewBox',`0 0 ${box.width} ${box.height}`);svg.innerHTML=paths;
  }
  let skyResizeObserver=null,skyResizeHandler=null;
  function bindSkillCatalog(root,p){
    skyResizeObserver?.disconnect();
    if(skyResizeHandler)window.removeEventListener('resize',skyResizeHandler);
    skyResizeHandler=()=>drawConstellation(root,p);
    window.addEventListener('resize',skyResizeHandler);
    skyResizeObserver=new ResizeObserver(skyResizeHandler);
    skyResizeObserver.observe(root);
    const sky=root.querySelector('.sky-map');if(sky)skyResizeObserver.observe(sky);
    const dialog=root.querySelector('.skill-dialog');if(!dialog)return;
    let trigger=null, savedScroll=null;
    root.querySelectorAll('[data-skill]').forEach(button=>button.addEventListener('click',()=>{
      const t=(p.tools||[]).find(x=>x.id===button.dataset.skill);if(!t)return;
      trigger=button;savedScroll={left:scrollX,top:scrollY,behavior:"instant"};dialog.classList.add("dossier-dialog");dialog.innerHTML=`<article class="dossier" id="tool-${esc(t.id)}" style="--accent:${esc(p.color)}"><div class="dossier-toolbar"><button type="button" class="skill-dialog-close dossier-close" aria-label="Закрыть карточку">×</button></div>${dossierHead(t,p,"skill-dialog-title")}${dossierBody(t)}</article>`;
      dialog.querySelector('.skill-dialog-close').onclick=()=>dialog.close();
      replaceHash(`${p.id}/${t.id}`);dialog.showModal();dialog.scrollTop=0;dialog.querySelector('h2').focus({preventScroll:true});window.scrollTo(savedScroll);
    }));
    dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close()}});
    dialog.addEventListener('close',()=>{if(root.hidden||!dialog.isConnected)return;replaceHash(p.id);trigger?.focus({preventScroll:true});if(savedScroll)window.scrollTo(savedScroll)});
  }

  function page(p){if(p.id==="memory"&&window.LAB_MEMORY_MAP)return window.LAB_MEMORY_MAP.render(p,model.processes);if(p.constellation)return constellationPage(p);const map=p.id==="memory"?knowledgeArchitecture(p):`${compactSectionMap(p)}`;return `<div class="process-shell${p.id==="memory"?" memory-shell":""}" style="--accent:${esc(p.color||"#426aff")}"><button class="back-button" data-back type="button">← Вернуться к общей карте</button><header class="process-hero compact"><div class="process-index">${esc(p.number)}</div><div class="process-title"><h1 tabindex="-1">${esc(p.title)}</h1><p class="verb">${esc(p.verb)}</p></div><div class="process-purpose"><p>${esc(p.purpose)}</p></div></header><nav class="process-jump" aria-label="Разделы процесса"><a href="#map">Карта раздела</a>${p.pipeline?'<a href="#pipeline">Как это устроено внутри</a>':""}${p.spotlight?'<a href="#spotlight">Пользуйтесь только этим</a>':""}${p.toMcp?'<a href="#mcp">Что уходит в базу</a>':""}${(p.gallery||[]).length?'<a href="#gallery">Как это выглядит</a>':""}<a href="#tools">Досье инструментов</a></nav>${map}${pipelineBlock(p)}${spotlightBlock(p)}${toMcpBlock(p)}${galleryBlock(p)}${tools(p)}${implementation(p)}${nav(p)}</div>`}
  function bind(root,p){root.querySelectorAll("[data-back]").forEach(b=>b.onclick=showOverview);root.querySelectorAll("[data-open]").forEach(b=>b.onclick=()=>openProcess(b.dataset.open,b.dataset.tool));root.querySelectorAll("[data-capability]").forEach(b=>b.onclick=()=>showCapability(b.dataset.capability));root.querySelectorAll(".process-jump a").forEach(a=>a.onclick=e=>{e.preventDefault();root.querySelector(a.hash)?.scrollIntoView({behavior:"smooth"})});if(p){const focus=root.querySelector(".map-focus"),toolsById=Object.fromEntries((p.tools||[]).map(t=>[t.id,t])),reset=()=>{root.querySelectorAll(".section-map-canvas button").forEach(x=>x.classList.remove("is-dim","is-active"));focus?.classList.remove("is-open");if(focus)focus.innerHTML=focusDefault(p);replaceHash(p.id)};root.querySelectorAll("[data-focus-tool]").forEach(b=>b.onclick=()=>{root.querySelectorAll(".map-tool").forEach(x=>x.classList.toggle("is-dim",x!==b));b.classList.remove("is-dim");b.classList.add("is-active");if(focus){focus.innerHTML=focusTool(toolsById[b.dataset.focusTool]);focus.classList.add("is-open")}replaceHash(`${p.id}/${b.dataset.focusTool}`)});root.querySelector("[data-map-reset]")?.addEventListener("click",reset);root.querySelectorAll("[data-map-title]").forEach(b=>b.onclick=()=>{root.querySelectorAll(".section-map-canvas button").forEach(x=>x.classList.remove("is-dim","is-active"));b.classList.add("is-active");replaceHash(p.id)});root.onclick=e=>{const dossier=e.target.closest("[data-open-dossier]"),openSetup=e.target.closest("[data-open-setup]");if(e.target.closest("[data-reset-focus]"))reset();if(dossier||openSetup){const id=(dossier||openSetup).dataset.openDossier||(dossier||openSetup).dataset.openSetup,d=root.querySelector(`#tool-${CSS.escape(id)}`);if(d){d.open=true;let focusTarget=d.querySelector("summary"),scrollTarget=d;if(openSetup){const s=root.querySelector(`#setup-${CSS.escape(id)}`);if(s){s.open=true;focusTarget=s.querySelector("summary");scrollTarget=s}}focus?.classList.remove("is-open");scrollTarget.scrollIntoView({behavior:"smooth",block:"start"});focusTarget?.focus({preventScroll:true})}}}}}

  function relationIndex(p){
    const map=normalizedMap(p),index=new Map();
    for(const relation of map.relations){
      const refs=[`stage:${relation.stage}`,...arr(relation.tools).map(x=>`tool:${x}`),...arr(relation.destinations).map(x=>`destination:${x}`),...arr(relation.outcomes).map(x=>`outcome:${x}`),...arr(relation.qa).map(x=>`qa:${x}`)];
      for(const ref of refs){if(!index.has(ref))index.set(ref,new Set());for(const other of refs)index.get(ref).add(other)}
    }
    return {map,index};
  }

  function bindGraphMap(root,p){
    if(p.id==="memory"&&window.LAB_MEMORY_MAP){bindSkillCatalog(root,p);window.LAB_MEMORY_MAP.bind(root);return}
    if(p.constellation){bindSkillCatalog(root,p);drawConstellation(root,p);if(p.knowledgeModel)bindKnowledgeMap(root,p);return}
    if(p.id==="memory"){bindKnowledgeMap(root,p);return}
    const scope=root.querySelector(".section-overview"),focus=scope?.querySelector(".graph-focus");if(!scope||!focus)return;
    const {map,index}=relationIndex(p),tools=Object.fromEntries((p.tools||[]).map(t=>[t.id,t])),stages=Object.fromEntries(map.stages.map(x=>[x.id,x])),destinations=Object.fromEntries(map.destinations.map(x=>[x.id,x])),outcomes=Object.fromEntries(map.outcomes.map(x=>[x.id,x])),qas=Object.fromEntries(qualityProcesses().map(x=>[x.id,x]));let lastTrigger=null;
    const reset=(returnFocus=false)=>{scope.querySelectorAll("[data-node]").forEach(x=>{x.classList.remove("is-active","is-related","is-muted");x.setAttribute("aria-pressed","false")});focus.classList.remove("is-open");focus.innerHTML=focusDefault(p);replaceHash(p.id);if(returnFocus)lastTrigger?.focus()};
    const describeRef=ref=>{const [kind,id]=ref.split(":");if(kind==="tool")return {ref,kind:"Инструмент",label:tools[id]?.title};if(kind==="stage")return {ref,kind:"Этап",label:stages[id]?.title};if(kind==="destination")return {ref,kind:"Хранилище",label:destinations[id]?.name};if(kind==="outcome")return {ref,kind:"Результат",label:outcomes[id]?.text};return {ref,kind:"Обязательная проверка",label:qas[id]?.title}};
    const relationFocus=ref=>{
      const [kind,id]=ref.split(":"),related=index.get(ref)||new Set(),relatedCards=[...related].filter(x=>x!==ref).map(describeRef).filter(x=>x.label);
      if(kind==="tool")return focusTool(tools[id],relatedCards,p.id);
      const item=kind==="stage"?stages[id]:kind==="destination"?destinations[id]:kind==="outcome"?outcomes[id]:qas[id]||{},title=item.title||item.name||item.text||"Узел карты",copy=item.detail||item.purpose||item.summary||item.what||item.definition||item.text||"",kindLabel=kind==="stage"?"Этап":kind==="destination"?"Хранилище":kind==="outcome"?"Результат":"Обязательная проверка";
      const qaTools=kind==="qa"?arr(item.tools):[];
      return `<div class="focus-head"><span class="map-focus-kicker">${kindLabel} · полное описание</span><button data-reset-focus type="button" aria-label="Закрыть карточку">×</button><h3 tabindex="-1">${esc(title)}</h3><p>${esc(copy)}</p></div><div class="focus-detail-grid">${focusList("Что получается",item.result||item.text)}${focusList("Когда включается",item.when)}${focusList("Что хранится",item.what)}${focusList("Почему здесь",item.why)}${focusList("Затрагивает разделы",item.touches)}</div>${qaTools.length?`<div class="focus-related"><b>Инструменты этой проверки</b>${qaTools.map(t=>`<button data-open-process="${esc(item.id)}" data-open-tool="${esc(t.id)}" type="button"><small>${esc(t.type||"Инструмент")}</small>${esc(t.title)}</button>`).join("")}</div>`:""}${relatedCards.length?`<div class="focus-related"><b>Связано на этой карте</b>${relatedCards.map(x=>`<button data-jump-node="${esc(x.ref)}" type="button"><small>${esc(x.kind)}</small>${esc(x.label)}</button>`).join("")}</div>`:""}${kind==="qa"?`<div class="map-focus-actions"><button data-open-process="${esc(item.id)}" type="button">Открыть карту этапа 08</button></div>`:""}`;
    };
    scope.addEventListener("click",e=>{const open=e.target.closest("[data-open-process]");if(open){openProcess(open.dataset.openProcess,open.dataset.openTool);return}const jump=e.target.closest("[data-jump-node]");if(jump){focus.classList.remove("is-open");scope.querySelector(`[data-node="${CSS.escape(jump.dataset.jumpNode)}"]`)?.click();return}const trigger=e.target.closest("[data-node]");if(!trigger)return;lastTrigger=trigger;const ref=trigger.dataset.node,related=index.get(ref)||new Set([ref]);scope.querySelectorAll("[data-node]").forEach(node=>{const active=node===trigger,isRelated=related.has(node.dataset.node);node.classList.toggle("is-active",active);node.classList.toggle("is-related",!active&&isRelated);node.classList.toggle("is-muted",!isRelated);node.setAttribute("aria-pressed",String(active))});if(ref.startsWith("stage:")){focus.classList.remove("is-open");replaceHash(p.id);return}focus.innerHTML=relationFocus(ref);focus.classList.add("is-open");focus.querySelector("h3")?.focus({preventScroll:true});if(ref.startsWith("tool:"))replaceHash(`${p.id}/${ref.slice(5)}`);else replaceHash(p.id)});
    scope.querySelector("[data-map-reset]")?.addEventListener("click",()=>reset());scope.addEventListener("click",e=>{if(e.target.closest("[data-reset-focus]"))reset(true)});const closeFocusPanel=()=>{if(focus.classList.contains("is-open"))reset(true)};document.addEventListener("keydown",e=>{if(e.key==="Escape"&&focus.classList.contains("is-open")){e.preventDefault();closeFocusPanel()}});document.addEventListener("pointerdown",e=>{if(!focus.classList.contains("is-open"))return;if(focus.contains(e.target)||(e.target.closest&&e.target.closest("[data-node],[data-knowledge],[data-surface-process]")))return;closeFocusPanel()},true);
  }

  function bindKnowledgeMap(root,p){
    const scope=root.querySelector(".knowledge-architecture"),focus=scope?.querySelector(".knowledge-inspector"),km=p.knowledgeModel||{};if(!scope||!focus)return;
    const boundary={mcp:{title:"Lab Knowledge MCP",detail:km.boundary?.mcp,operations:[...arr(km.read?.tools),...arr(km.write?.tools)],behavior:km.agentConnection,links:km.sources},skill:{title:"навык lab-knowledge",detail:km.boundary?.skill,behavior:[km.read?.default,...arr(km.write?.behavior)],links:(p.tools||[]).find(x=>x.id==="lab-knowledge-skill")?.links||[]}},personal={obsidian:{title:"Obsidian",detail:"Личные заметки, полные разборы и черновики сотрудника. Публикуются в общую память только после показа человеку и подтверждения.",connections:[{to:"flow:preview",label:"передаёт только после показа человеку"}]},mempalace:{title:"MemPalace",detail:"История сессий и рабочий контекст агента. Помогает продолжать работу, но не считается научным доказательством.",connections:[{to:"producer:agents",label:"возвращает контекст агенту"}]},yonote:{title:"Yonote",detail:"Рабочие задачи, сроки и исполнители. Статус задачи не меняет статус научной гипотезы.",connections:[{to:"consumer:public",label:"показывает человеческую проекцию"}]}},read={question:{title:"Задать вопрос",detail:"Сформулировать, какое прошлое знание нужно для следующего решения.",connections:[{to:"read:scope",label:"уточнить область"}]},scope:{title:"Определить область",detail:"Ограничить чтение проектом, типом записи и временным срезом.",connections:[{to:"read:policy",label:"проверить доступ"}]},policy:{title:"Проверить доступ",detail:"Проверить ключ до поиска. Читать общую базу может любой участник лаборатории: закрытого контура для чтения нет.",connections:[{to:"guard:access",label:"проходит через общую проверку"},{to:"read:search",label:"разрешает поиск"}]},search:{title:"Найти и пройти связи",detail:"Совместить текстовый поиск с типизированными связями между гипотезами, экспериментами, результатами и статьями.",operations:arr(km.read?.tools),connections:[{to:"boundary:mcp",label:"читает общую память"},{to:"read:answer",label:"собирает ответ"}]},answer:{title:"Ответить с источниками",detail:"Вернуть короткий ответ вместе с кодами записей, их происхождением и границами найденного.",connections:(km.consumers||[]).map(x=>({to:`consumer:${x.id}`,label:"передает ответ"}))}},guard={access:{title:"Доступ",detail:"Проверяется до любого чтения или записи. Чтение открыто всем участникам, а запись в чужую работу требует роли в ней.",required:["действующий ключ и человек за ним","глобальная роль","роль в проекте — только для записи"],connections:[...arr(km.publishFlow).map(x=>({to:`flow:${x.id}`,label:"защищает запись"})),{to:"read:policy",label:"защищает чтение"}]},provenance:{title:"Происхождение записи",detail:"Позволяет восстановить, откуда взялся факт, кто его опубликовал и что изменялось.",required:arr(km.provenance),connections:(km.objectTypes||[]).map(x=>({to:`object:${x.id}`,label:"сопровождает запись"}))}},bridge={"paper-to-work":{title:"Как статья связывается с нашей работой",detail:"Утверждение внешней статьи получает типизированную связь prior art, supports, contradicts, baseline, inspired или reproduces. Эта связь не превращает чужое утверждение в наш результат.",connections:[{to:"object:paper-claim",label:"начинается с проверенного утверждения"},{to:"object:hypothesis",label:"может мотивировать гипотезу"},{to:"object:experiment",label:"может задать точку отсчёта"},{to:"object:evidence",label:"может дать контекст сравнения"},{to:"object:decision",label:"может лечь в обоснование"}]}},groups={intake:Object.fromEntries([...(km.intake||[]).flatMap(l=>(l.steps||[]).map(x=>[x.id,{title:x.title,detail:x.note||"",operations:x.ops||[],connections:[{to:"boundary:mcp",label:"кончается записью в базе"}]}])),...((km.hook||{}).steps||[]).map(x=>[x.id,{title:x.title,detail:x.note||"",connections:[{to:"boundary:mcp",label:"хук предлагает записать"}]}])]),object:Object.fromEntries((km.objectTypes||[]).map(x=>[x.id,x])),flow:Object.fromEntries((km.publishFlow||[]).map(x=>[x.id,x])),read,guard,bridge,producer:Object.fromEntries((km.producers||[]).map(x=>[x.id,x])),consumer:Object.fromEntries((km.consumers||[]).map(x=>[x.id,x])),corpus:Object.fromEntries((km.corpora||[]).map(x=>[x.id,x])),boundary,personal};
    personal.yonote.connections=[{to:"consumer:projections",label:"показывает человеческую проекцию"}];
    guard.provenance.connections=(km.objectTypes||[]).filter(x=>!["journal","term","resource","paper","paper-claim"].includes(x.id)).map(x=>({to:`object:${x.id}`,label:"сопровождает строгую научную запись"}));
    let lastTrigger=null;
    scope.querySelectorAll("[data-knowledge]").forEach(x=>{x.setAttribute("aria-pressed","false");x.setAttribute("aria-controls","knowledge-inspector")});
    const reset=(returnFocus=false)=>{scope.querySelectorAll("[data-knowledge]").forEach(x=>{x.classList.remove("is-active","is-related","is-muted");x.setAttribute("aria-pressed","false")});focus.classList.remove("is-open");focus.innerHTML=``;if(returnFocus)lastTrigger?.focus()};
    scope.addEventListener("click",e=>{if(e.target.closest("[data-reset-knowledge]")){reset(true);return}const tech=e.target.closest("[data-open-knowledge-tech]");if(tech){const details=scope.querySelector(".knowledge-technical");if(details){details.open=true;details.scrollIntoView({behavior:"smooth",block:"start"});details.querySelector("summary")?.focus()}return}const jump=e.target.closest("[data-knowledge-jump]");if(jump){const target=jump.dataset.knowledgeJump;if(target.startsWith("process:")){openProcess(target.slice(8));return}const targetNode=scope.querySelector(`[data-knowledge="${CSS.escape(target)}"]`);targetNode?.click();targetNode?.focus({preventScroll:true});return}const button=e.target.closest("[data-knowledge]");if(!button)return;lastTrigger=button;const key=button.dataset.knowledge,[kind,id]=key.split(":"),term=(model.shared?.glossary||[]).find(x=>x.id===id||x.id.replace("foreign-","")===id),item=groups[kind]?.[id]||{title:button.querySelector("strong")?.textContent||id,detail:term?.meaning||button.querySelector("span,small")?.textContent||""},connectionObjects=arr(item.connections).filter(x=>x&&typeof x==="object"&&x.to),relatedKeys=new Set(connectionObjects.map(x=>x.to));for(const [groupName,items] of Object.entries(groups))for(const [itemId,candidate] of Object.entries(items))if(arr(candidate.connections).some(x=>x?.to===key))relatedKeys.add(`${groupName}:${itemId}`);if(key==="boundary:mcp")scope.querySelectorAll("[data-knowledge]").forEach(x=>relatedKeys.add(x.dataset.knowledge));scope.querySelectorAll("[data-knowledge]").forEach(x=>{const active=x.dataset.knowledge===key,related=relatedKeys.has(x.dataset.knowledge);x.classList.toggle("is-active",active);x.classList.toggle("is-related",!active&&related);x.classList.toggle("is-muted",!active&&!related);x.setAttribute("aria-pressed",String(active))});const kindLabel={object:"Тип общей записи",flow:"Шаг безопасной публикации",read:"Шаг безопасного чтения",guard:"Обязательное правило",bridge:"Связь внешнего источника с нашей работой",producer:"Источник информации",consumer:"Потребитель знания",corpus:"Раздел общей базы",boundary:"Компонент системы",personal:"Отдельный личный слой"}[kind]||"Часть системы",connections=arr(item.related||item.connections||item.usedBy).map(x=>typeof x==="string"?{label:x}:x),clickableConnections=connections.filter(x=>x.to),notes=connections.filter(x=>!x.to),targetTitle=target=>scope.querySelector(`[data-knowledge="${CSS.escape(target)}"] strong`)?.textContent||target.replace(/^\w+:/,"");focus.innerHTML=`<div class="focus-head"><small>${esc(kindLabel)}</small><button data-reset-knowledge type="button" aria-label="Закрыть карточку">×</button><h3 tabindex="-1">${esc(item.label||item.title_ru||item.title||id)}</h3><p>${esc(item.detail||item.summary||item.action||item.plain||"")}</p></div><div class="focus-detail-grid">${focusList("Что находится внутри",item.contains)}${focusList("Кто и как получает доступ",item.access)}${focusList("Что происходит",item.behavior)}${focusList("Обязательные данные",item.required)}</div>${clickableConnections.length?`<div class="focus-related"><b>Перейти к связанному узлу</b>${clickableConnections.map(x=>`<button data-knowledge-jump="${esc(x.to)}" type="button"><small>${esc(x.label||"Связь")}</small>${esc(targetTitle(x.to))}</button>`).join("")}</div>`:""}${notes.length?`<div class="focus-notes"><b>Важно</b>${notes.map(x=>`<p>${esc(x.label||x.name||x.role||"")}</p>`).join("")}</div>`:""}${item.operations?.length?`<div class="focus-operations"><b>Настоящие инструменты MCP</b>${arr(item.operations).map(x=>`<code>${esc(x)}</code>`).join("")}</div>`:""}<div class="map-focus-actions"><button data-open-knowledge-tech type="button">Подключение и техническая схема</button>${links(item.links||[],item.title||id)}</div>`;focus.classList.add("is-open");focus.querySelector("h3")?.focus({preventScroll:true});if(matchMedia("(max-width:1100px)").matches)focus.scrollIntoView({behavior:"smooth",block:"nearest"})});
    const closeFocusPanel=()=>{if(focus.classList.contains("is-open"))reset(true)};document.addEventListener("keydown",e=>{if(e.key==="Escape"&&focus.classList.contains("is-open")){e.preventDefault();closeFocusPanel()}});document.addEventListener("pointerdown",e=>{if(!focus.classList.contains("is-open"))return;if(focus.contains(e.target)||(e.target.closest&&e.target.closest("[data-node],[data-knowledge],[data-surface-process]")))return;closeFocusPanel()},true);
  }
  function sourceButtons(items=[]){return `<div class="special-links">${items.map(x=>{const url=safe(x.url);return url?`<a href="${esc(url)}" target="_blank" rel="noopener">${esc(x.label)} <span>↗</span></a>`:""}).join("")}</div>`}
  let navigationRevision=0;
  function hidePrimaryViews(){navigationRevision++;window.LAB_SURFACE_PAGES?.disconnect();document.querySelectorAll('.skill-dialog[open]').forEach(d=>d.close());$("overview").hidden=true;$("process-view").hidden=true;$("dykaf-view").hidden=true;$("mcp-live-view").hidden=true;$("examples-view").hidden=true}
  function showSurface(id,navigate=true){
    if(!systemData.surfaces?.[id])return;
    if(navigate)updateHash(`surface/${id}`);
    hidePrimaryViews();active("none");
    const view=$("process-view");view.hidden=false;
    const content=id==="obsidian"?window.LAB_OBSIDIAN_SETUP.page():window.LAB_SURFACE_PAGES.page(id);
    view.innerHTML=`<div class="process-shell sp-shell"><button class="back-button" data-back type="button">← Вернуться к общей карте</button>${content}</div>`;
    view.querySelector("[data-back]").onclick=showOverview;
    window.LAB_SURFACE_PAGES.bind(view.querySelector(".sp-page"));
    window.scrollTo({top:0,behavior:"instant"});
    view.querySelector("h1")?.focus({preventScroll:true});
  }
  // The existing MCP renderer and all its indexes are initialized only after data arrives.
  function createMcpWorkspace(){
  // ============ Страница MCP: поиск по содержимому базы ============
  // Владелец: «я должен написать, когда выигрывает Muon… по этим связям… нужно максимально
  // информативно показать путь от объекта: как статья добавляется, как раскладывается на
  // компоненты и как они дальше идут в MCP». Ищем по живому снимку библиотеки (547 статей,
  // 9255 утверждений статей), а каждый результат разворачивается в полный путь с именами
  // настоящих операций на каждом шаге.
  const lib=window.LAB_LIBRARY||{papers:[],links:[]};
  // Владелец: «там прям ВСЁ, ЧТО ЕСТЬ на brain_lab, должно отображаться, реально вся
  // информация; я должен понимать, как работает мой MCP, и проверять, что там всё норм».
  // Снимок собирается локально из живой базы и наружу не публикуется: в нём имена
  // проектов, неопубликованные утверждения и внутренние адреса.
  const base=window.LAB_BASE||{records:[],relations:[]};
  const KIND={project:"проект",hypothesis:"утверждение",experiment:"прогон",evidence:"измерение",
    derivation:"доказательство",decision:"правило",journal:"журнал",term:"термин",
    resource:"ресурс",source:"источник",source_ref:"источник",
    paper:"статья",paper_chunk:"раздел статьи",paper_claim:"утверждение статьи"};
  // Каждая запись в базе появляется ровно одной операцией MCP. Это и есть ответ на вопрос
  // «как она сюда попала», поэтому операция стоит на карточке, а не в пояснении.
  const KIND_OP={project:"upsert_project",hypothesis:"create_hypothesis",experiment:"record_experiment",
    evidence:"record_evidence",derivation:"record_derivation",decision:"propose_decision",
    journal:"record_journal",term:"upsert_term",resource:"upsert_resource",source:"attach_source_ref",
    source_ref:"attach_source_ref",paper:"upsert_paper",paper_chunk:"add_paper_section",
    paper_claim:"record_paper_claim"};
  const KIND_ORDER=["project","hypothesis","derivation","experiment","evidence","decision","journal","term","resource","source"];
  // Владелец: «есть и доказательства, и эксперимент — это вообще идеальный вариант».
  // Из 709 утверждений так закрыты 146, и это должно читаться прямо с карточки.
  const SUPPORT={proof_and_numbers:["и выкладка, и числа","is-both"],proof:["выкладка","is-proof"],
    numbers:["числа","is-numbers"],runs_without_numbers:["прогон без измерений","is-partial"],
    open:["пока не закрыто","is-open"]};
  const supportBadge=snap=>{const x=SUPPORT[snap?.sup];
    return x?`<span class="base-support ${x[1]}">${esc(x[0])}</span>`:""};
  const baseById={};for(const r of base.records||[])if(r.id)baseById[r.k+":"+r.id]=r;
  const relIndex={};
  for(const r of base.relations||[]){
    (relIndex[r.a+":"+r.ai]||=[]).push({ref:r.b+":"+r.bi,label:r.r,dir:"→"});
    (relIndex[r.b+":"+r.bi]||=[]).push({ref:r.a+":"+r.ai,label:r.r,dir:"←"});
  }
  const baseCounts=(base.records||[]).reduce((o,r)=>((o[r.k]=(o[r.k]||0)+1),o),{});

  const linksByPaper=(lib.links||[]).reduce((o,l)=>((o[l.p]||=[]).push(l),o),{});
  const REL={prior_art:"предшествующая работа",supports:"поддерживает",contradicts:"противоречит",
    baseline:"точка отсчёта",inspired:"натолкнула",reproduces:"воспроизводит"};
  const CKIND={empirical:"эмпирическое",theoretical:"теоретическое",method:"о методе",definition:"определение"};
  // Запрос раскладывается на корни: русская морфология тут — отсечение окончания, плюс
  // словарь предметной области, чтобы «когда выигрывает Muon» находило нужное.
  const LIB_SYN={"выигрывает":"лучше превосход преимуществ outperform wins","выигрыш":"преимуществ лучше",
    "проигрывает":"хуже уступ","сходимость":"converg сходит","обучение":"training обучен",
    "предобучение":"pretrain предобучен","дообучение":"finetun дообучен","квантование":"quantiz квантов",
    "разреженность":"sparse разряж","оптимизатор":"optimizer оптимизатор adam muon sgd",
    "прогрев":"warmup прогрев","затухание":"decay затухан","градиент":"gradient градиент",
    "внимание":"attention внимани","память":"memory памят","скорость":"speed быстр время",
    // Пополнено по замеру: те же пары, что подставляет прокси живой службе. Без них снимок
    // не находит по-русски то, что в базе записано латиницей, а именно снимком витрина
    // отвечает, когда сервер лаборатории занят.
    "безградиент":"zeroth-order zo безградиент","нижние":"lower bound нижн",
    "оценки":"bound оценк","теорема":"theorem теорем лемма","доказательство":"proof доказ",
    "ортогонализация":"orthogonal ортогонал","кривизна":"curvature кривизн",
    "низкоранг":"low-rank низкоранг lora","адаптер":"adapter адаптер lora",
    "батч":"batch батч","шаг":"step шаг learning rate","расписание":"schedule расписан",
    "матрица фишера":"fisher матриц фишер","предобучение":"pretrain предобучен",
    "разреженность":"sparse разреж","слияние":"merging слиян merge"};
  // Владелец печатает «дикаф» и «муон», а в базе DyKAF и Muon: имена методов живут на
  // латинице, а спрашивают их по-русски. Транслитерация плюс сравнение по костяку слова
  // (без гласных) сводит «дикаф» и «DyKAF» к одному «dkf», поэтому запрос находит запись.
  const RU2LAT={а:"a",б:"b",в:"v",г:"g",д:"d",е:"e",ё:"e",ж:"zh",з:"z",и:"i",й:"y",к:"k",л:"l",
    м:"m",н:"n",о:"o",п:"p",р:"r",с:"s",т:"t",у:"u",ф:"f",х:"h",ц:"c",ч:"ch",ш:"sh",щ:"sh",
    ъ:"",ы:"y",ь:"",э:"e",ю:"yu",я:"ya"};
  const translit=w=>w.toLowerCase().replace(/[а-яё]/g,c=>RU2LAT[c]??c);
  const skeleton=w=>translit(w).replace(/[aeiouy]/g,"");
  function libSkels(q){
    const out=[];
    for(const w of (q.toLowerCase().match(/[a-zа-яё0-9\-]+/g)||[])){
      if(w.length<4)continue;
      const sk=skeleton(w);
      if(sk.length>=2&&!out.includes(sk))out.push(sk);
    }
    return out;
  }
  const skelHit=(text="",skels=[])=>{
    if(!skels.length)return 0;
    const words=(text.toLowerCase().match(/[a-zа-яё0-9]+/g)||[]).map(skeleton);
    return skels.filter(sk=>words.includes(sk)).length;
  };
  function libStems(q){
    const stop=new Set(["как","что","где","для","или","под","при","это","мне","все","всё","когда","чем","the","and","for","with","это","есть"]);
    const words=(q.toLowerCase().match(/[a-zа-яё0-9\-]+/g)||[]).filter(w=>w.length>2&&!stop.has(w));
    return [...new Set(words.flatMap(w=>{
      const st=w.length>5?w.slice(0,w.length-2):w;
      return [w,st,...(LIB_SYN[w]||"").split(" ")];
    }))].filter(Boolean);
  }
  function libSearch(q,limit=12){
    const stems=libStems(q),skels=libSkels(q);
    if(!stems.length&&!skels.length)return [];
    return (lib.papers||[]).map(p=>{
      const title=(p.t||"").toLowerCase(),body=((p.s||"")+" "+(p.f||"")+" "+(p.th||[]).join(" ")).toLowerCase();
      const claims=(p.c||[]).map(c=>(c.s||"").toLowerCase());
      let score=0,hits=[];
      score+=4*skelHit((p.t||"")+" "+(p.f||""),skels);
      for(const st of stems){
        if(title.includes(st))score+=8;
        if(body.includes(st))score+=3;
        claims.forEach((cs,k)=>{if(cs.includes(st)){score+=4;if(!hits.includes(k))hits.push(k)}});
      }
      if((linksByPaper[p.id]||[]).length&&score)score+=5;
      return {p,score,hits};
    }).filter(x=>x.score>0).sort((a,b)=>b.score-a.score).slice(0,limit);
  }
  function baseSearch(q,limit=40,kind=""){
    const stems=libStems(q),skels=libSkels(q);
    if(!stems.length&&!skels.length&&!kind)return [];
    return (base.records||[]).map(r=>{
      if(kind&&r.k!==kind)return null;
      const title=(r.t||"").toLowerCase(),code=(r.code||"").toLowerCase();
      const proj=((r.pj||"")+" "+(r.pn||"")+" "+(r.th||"")).toLowerCase();
      const body=(r.s||"").toLowerCase();
      const fields=(r.f||[]).map(f=>String(f[1]||"").toLowerCase());
      let score=0,hits=[];
      if(!stems.length&&!skels.length)return {r,score:1,hits};
      score+=3*skelHit((r.t||"")+" "+(r.code||"")+" "+(r.pj||"")+" "+(r.pn||""),skels);
      for(const st of stems){
        if(code.includes(st))score+=12;
        if(title.includes(st))score+=8;
        if(proj.includes(st))score+=6;
        if(body.includes(st))score+=4;
        fields.forEach((v,i)=>{if(v.includes(st)){score+=2;if(!hits.includes(i))hits.push(i)}});
      }
      return score>0?{r,score,hits}:null;
    }).filter(Boolean).sort((a,b)=>b.score-a.score||KIND_ORDER.indexOf(a.r.k)-KIND_ORDER.indexOf(b.r.k)).slice(0,limit);
  }
  function baseRelations(r){
    const xs=relIndex[r.k+":"+r.id]||[];
    return xs.map(x=>{const o=baseById[x.ref];return o?{o,label:x.label,dir:x.dir}:null}).filter(Boolean).slice(0,10);
  }
  // В базе утверждения записаны из разбора статьи, и часть текстов несёт следы markdown:
  // «*Abstract и Introduction.**», «## Разбор», ведущие дефисы списка. На сайте это читается
  // как мусор в начале фразы, поэтому такая разметка снимается при выводе. Сам текст
  // остаётся дословным: убираются только звёздочки, решётки и маркеры списка.
  function unmark(text=""){
    return String(text)
      .replace(/^\s*[#>]+\s*/,"")
      .replace(/^\s*[-*+]\s+/,"")
      .replace(/\*{1,3}/g,"")
      .replace(/`{1,3}/g,"")
      .replace(/\s{2,}/g," ")
      .trim();
  }
  // Владелец: «не как сейчас — сейчас слова отмечаются, какой-то кринж и как будто всё ещё
  // поиск по словам (проверь, что это не так)».
  //
  // Проверено: поиск не по словам. Служба считает вектор вопроса моделью e5, смешивает его
  // с BM25 через RRF, расширяет по графу связей и переранжирует кросс-энкодером
  // jina-reranker-v2 — отсюда и оценка на карточке. Но подсветка совпавших слов
  // рассказывала обратное, потому что видно было ровно совпадение слов. Поэтому её больше
  // нет: текст показывается как он записан, а место в ответе объясняет оценка службы.
  //
  // Функция оставлена как точка вывода текста: она снимает следы markdown и экранирует.
  function mark(text="",q=""){
    return esc(unmark(text));
  }
  function baseCard(x,q){
    const r=x.r,rels=baseRelations(r);
    const fields=(r.f||[]).map((f,i)=>`<div class="${x.hits.includes(i)?"is-hit":""}"><dt>${esc(f[0])}</dt><dd>${mark(f[1],q)}</dd></div>`).join("");
    return `<article class="base-card" data-kind="${esc(r.k)}">
      <header><span class="base-kind">${esc(KIND[r.k]||r.k)}</span>${r.code?`<code class="base-code">${esc(r.code)}</code>`:""}${supportBadge(r)}${r.st?`<span class="base-status">${esc(r.st)}</span>`:""}${r.pj?`<span class="base-proj">${esc(r.pn||r.pj)} · ${esc(r.pj)}</span>`:""}</header>
      <h3>${mark(r.t||"без названия",q)}</h3>
      ${r.s&&r.s!==r.t?`<p>${mark(r.s,q)}</p>`:""}
      <p class="base-op">попала в базу вызовом <code>${esc(KIND_OP[r.k]||"—")}</code></p>
      ${fields?`<details class="base-fields"><summary>Все поля записи <span>${(r.f||[]).length}</span></summary><dl>${fields}</dl></details>`:""}
      ${rels.length?`<div class="base-rels"><b>Связано в базе</b>${rels.map(y=>`<button type="button" data-base-jump="${esc(y.o.code||y.o.t||"")}"><small>${esc(y.dir)} ${esc(y.label)} · ${esc(KIND[y.o.k]||y.o.k)}</small>${esc(y.o.code||"")} ${esc((y.o.t||"").slice(0,70))}</button>`).join("")}</div>`:""}
    </article>`;
  }
  // Полный путь одной статьи в общую базу: шесть шагов, у каждого настоящая операция.
  function libPath(p){
    const ls=linksByPaper[p.id]||[];
    const step=(op,title,detail,cls="")=>`<li class="${cls}"><code>${esc(op)}</code><strong>${esc(title)}</strong><span>${esc(detail)}</span></li>`;
    const tie=ls.length
      ? ls.map(l=>`${REL[l.rel]||l.rel} → ${l.code||l.et}${l.pn?" ("+l.pn+")":""}`).join("; ")
      : "связи с нашей работой пока нет: статья лежит в библиотеке и ждёт, пока понадобится";
    return `<ol class="lib-path">
      ${step("—","Найдена и отобрана","карточка в очереди чтения, разрешение владельца","is-work")}
      ${step("paper-ingest","Собран локальный комплект","PDF, исходник, BibTeX, заметка в Obsidian","is-work")}
      ${step("upsert_paper",`Статья в базе${p.ax?" · arXiv "+p.ax:""}`,`ключ ${p.key||"—"}; повторная отправка обновит, а не задвоит`,"is-rec")}
      ${step("add_paper_section",`Разделы: ${p.nc}`,"сохранённые смысловые части статьи для поиска и проверки происхождения тезисов","is-rec")}
      ${step("record_paper_claim",`Утверждения статьи: ${p.nm}`,"тезис своими словами, источник и место в статье; цитата необязательна","is-rec")}
      ${step("link_paper",`Связей с нашей работой: ${ls.length}`,tie,"is-tie")}
    </ol>`;
  }
  function libCard(x,q){
    const p=x.p,ls=linksByPaper[p.id]||[];
    const claims=(p.c||[]).map((c,k)=>`<li class="${x.hits.includes(k)?"is-hit":""}"><small>${esc(CKIND[c.k]||c.k||"")}${c.q?(c.v?" · цитата сверена":" · цитата не сверена"):""}</small>${esc(c.s)}</li>`).join("");
    return `<article class="lib-card">
      <header><h3>${esc(p.t)}</h3>
        <p>${esc(p.au||"")}${p.y?" · "+p.y:""}${p.v?" · "+esc(p.v):""}</p>
        <div class="lib-tags">${p.f?`<span>${esc(p.f)}</span>`:""}${(p.th||[]).map(t=>`<span>${esc(t)}</span>`).join("")}${ls.length?`<span class="is-linked">связана с нашей работой</span>`:""}</div>
      </header>
      ${p.s?`<p class="lib-sum">${esc(p.s)}</p>`:""}
      ${claims?`<details class="lib-claims"${x.hits.length?" open":""}><summary>Утверждения статьи <span>${p.nm}</span></summary><ul>${claims}</ul></details>`:""}
      <details class="lib-way"><summary>Как эта статья попала в общую базу <span>6 шагов</span></summary>${libPath(p)}</details>
    </article>`;
  }
  // ============ Живой поиск по базе ============
  // Владелец: «сделай реальный, как будто я LLM-агент и ищу информацию семантическим
  // поиском… он должен искать конкретные утверждения, где задан вопрос, и искать ответ на
  // этот вопрос во всей базе. Почему он ищет просто ключевые слова и статьи?»
  //
  // Поиск по снимку в браузере искал подстрокой: «fisher» находил три записи вместо ста
  // двух. Теперь страница спрашивает живой search_lab через локальный прокси, режим
  // semantic, и получает настоящие оценки близости по эмбеддингам службы. Снимок остаётся
  // запасным вариантом, когда прокси не запущен, и об этом честно написано на странице.
  const demo=window.LAB_DEMO||null;
  const PROXY="http://127.0.0.1:8799";
  async function proxyFetch(url, options){
    if(demo)throw new Error("Live MCP is unavailable in the public demo");
    return fetch(url, options);
  }
  // Живой ответ несёт тип, оценку и отрывок. Поля записи и её связи берём из снимка по
  // первым восьми знакам идентификатора: так карточка остаётся подробной.
  const snapById={};for(const r of base.records||[])if(r.id)snapById[r.id]=r;
  // Утверждение статьи приходит в виде «Название статьи — сама формулировка», и рядом с ним
  // лежат раздел, папка библиотеки и arXiv. Показываем формулировку крупно, а статью —
  // подписью, по которой открывается её карточка со всеми утверждениями.
  function claimCard(item,q,place=0){
    const x=item.extra||{},score=typeof item.score==="number"?item.score.toFixed(3):"";
    const whole=String(item.title||"");
    const cut=whole.indexOf(" — ");
    const paper=cut>0?whole.slice(0,cut):(x.section?whole:"");
    const claim=cut>0?whole.slice(cut+3):whole;
    return `<article class="base-card is-claim" data-kind="paper_claim">
      <header>${place?`<span class="base-place">${esc(String(place))}</span>`:""}<span class="base-kind">${esc(KIND.paper_claim)}</span><span class="base-score" title="оценка кросс-энкодера">${esc(score)}</span>${x.library_folder?`<button class="base-folder" type="button" data-open-folder="${esc(x.library_folder)}">${esc(x.library_folder)}</button>`:""}</header>
      <h3>${mark(claim,q)}</h3>
      <p class="claim-of">${paper?`<button type="button" data-open-paper="${esc(shortId(x.paper_id))}">${esc(paper)}</button>`:""}${x.section?`<span>раздел «${esc(x.section)}»</span>`:""}</p>
      <p class="base-op">попала в базу вызовом <code>record_paper_claim</code></p>
      <div class="claim-links">${x.paper_id?`<button type="button" data-open-paper="${esc(shortId(x.paper_id))}">Все утверждения этой статьи →</button>`:""}${x.arxiv_id?`<a href="https://arxiv.org/abs/${esc(x.arxiv_id)}" target="_blank" rel="noopener">arXiv ${esc(x.arxiv_id)} ↗</a>`:""}</div>
    </article>`;
  }
  function liveCard(item,q,place=0){
    if(item.entity_type==="paper_claim")return claimCard(item,q,place);
    const kind=item.entity_type,short=String(item.entity_id||"").slice(0,8);
    const snap=snapById[short];
    const score=typeof item.score==="number"?item.score.toFixed(3):"";
    const code=(String(item.snippet||"").match(/^([A-ZА-Я]-[A-Z]{2,4}-\d{2,4})/)||[])[1]||snap?.code||"";
    const body=String(item.snippet||"").replace(/^\S+\s/,"").slice(0,700);
    const rels=snap?baseRelations(snap):[];
    const fields=(snap?.f||[]).map((f,i)=>`<div><dt>${esc(f[0])}</dt><dd>${mark(f[1],q)}</dd></div>`).join("");
    return `<article class="base-card" data-kind="${esc(kind)}">
      <header>${place?`<span class="base-place">${esc(String(place))}</span>`:""}<span class="base-kind">${esc(KIND[kind]||kind)}</span>${code?`<code class="base-code">${esc(code)}</code>`:""}<span class="base-score" title="оценка кросс-энкодера: насколько запись отвечает на вопрос">${esc(score)}</span>${supportBadge(snap)}${snap?.pn?`<span class="base-proj">${esc(snap.pn)}</span>`:""}</header>
      <h3>${mark(item.title||"без названия",q)}</h3>
      <p>${mark(body,q)}</p>
      <p class="base-op">попала в базу вызовом <code>${esc(KIND_OP[kind]||"—")}</code></p>
      ${fields?`<details class="base-fields"><summary>Все поля записи <span>${(snap.f||[]).length}</span></summary><dl>${fields}</dl></details>`:""}
      ${rels.length?`<div class="base-rels"><b>Связано в базе</b>${rels.map(y=>`<button type="button" data-base-jump="${esc(y.o.code||y.o.t||"")}"><small>${esc(y.dir)} ${esc(y.label)} · ${esc(KIND[y.o.k]||y.o.k)}</small>${esc(y.o.code||"")} ${esc((y.o.t||"").slice(0,70))}</button>`).join("")}</div>`:""}
    </article>`;
  }
  // Владелец: «оставь только поиск по MCP, который делают агенты, без всякой хуйни —
  // только то, что делают агенты». Агент не жмёт чипы и не переключает режимы: он делает
  // один вызов search_lab и получает один упорядоченный список. Страница показывает ровно
  // это, вместе с самим вызовом, и порядок не переставляет.
  // Владелец: «про это всё распиши в MCP, это самое интересное: видно, какая модель строит
  // эмбеддинг. Это самая важная часть сайта». Ниже — то, что реально происходит с вопросом
  // внутри одного вызова search_lab, по шагам, с именами моделей.
  const PIPELINE=[
    {op:"query_embed",t:"Вопрос становится вектором",
     m:"intfloat/multilingual-e5-large · 1024 измерения · ONNX",
     d:"Модель считается на самом сервере, наружу вопрос не уходит. У e5 роли разные: вопрос кодируется как вопрос, запись как запись, поэтому короткий вопрос сравним с длинным абзацем.",
     n:["модель лежит в кеше, из сети не тянется","весь разброс близости у e5 умещается в 0.85–0.95, поэтому один косинус порядок не решает"]},
    {op:"ts_rank_cd",t:"Одновременно ищется по словам",
     m:"полнотекстовый индекс Postgres",
     d:"Второй канал ловит то, что вектор пропускает: точный код записи, имя метода, номер прогона.",
     n:["точное совпадение с названием отдаёт запись сразу и без переранжировки"]},
    {op:"cosine",t:"Близость ко всем кандидатам разом",
     m:"17 492 вектора · одно матричное умножение",
     d:"Векторы записей лежат в базе и в памяти службы. Для вопроса считается косинус ко всем кандидатам сразу, а не по одному.",
     n:["вектор есть у каждой записи всех родов, дырок нет"]},
    {op:"rrf",t:"Два канала сводятся в один список",
     m:"reciprocal rank fusion · пул 60 кандидатов",
     d:"Смысл и слова дают разные списки. Их складывают по местам, а не по оценкам: оценки двух каналов несравнимы.",
     n:["пул не зависит от размера ответа: дешёвый этап берёт с запасом, иначе переранжировывать нечего",
        "при пуле, равном ответу, на вопрос про матрицу Фишера в десятку попадала работа про низкоранговую проекцию градиента"]},
    {op:"graph",t:"Добираются соседи по связям",
     m:"утверждение → прогон → измерение → правило",
     d:"К трём верхним попаданиям добираются записи, связанные с ними в базе: ответ часто лежит не в самой записи, а в измерении рядом с ней.",
     n:["сосед отвечает не на вопрос, а на связь"]},
    {op:"rerank",t:"Кросс-энкодер решает порядок",
     m:"jinaai/jina-reranker-v2-base-multilingual",
     d:"Он читает вопрос вместе с записью и отвечает на один вопрос: отвечает эта запись или нет. Это единственное место, где решается порядок, и после него весь список сравним по одной мере.",
     n:["до 06-09-2026 в режиме «по смыслу» он не вызывался совсем, и порядок решало совпадение слов",
        "читает по 400 знаков каждой из шестидесяти записей, поэтому запрос стоит секунды, а не миллисекунды",
        "на мерке из десяти микрозапросов девять десятых выдачи попадают в тему, мусора нет"]}];
  function mcpPipeline(){
    return `<details class="mcp-pipeline"><summary>Что происходит внутри одного вызова <span>${PIPELINE.length} шагов</span></summary>
      ${pipelineSteps(PIPELINE)}
      <p class="mcp-pipeline-note">Всё считается на brain_lab: и вектор вопроса, и переранжировка. Ни вопрос, ни текст записей за пределы сервера не уходят.</p></details>`;
  }
  // Владелец: «мне в поиске отдаётся статья, мы же разбивали каждую статью специально!
  // Статья должна быть в таком же виде, как утверждения по проектам». Поэтому спрашиваем
  // рода, которые несут ответ: наши утверждения, измерения, доказательства, правила и
  // утверждения, вынутые из статей. Статья целиком становится карточкой, куда переходят
  // с утверждения, а не результатом поиска.
  // Родов у ответа не выбираем. Так было не всегда: витрина просила у службы только
  // утверждения — гипотезы, измерения, выкладки, решения и утверждения статей, — а статью
  // целиком не просила вовсе. Владелец: «зачем то высвечивается Narrowing the Focus… а
  // например fantastic optimizers вообще не вышла! Там еще много других статей и вообще
  // ничего не вышло! … Надо сделать статьи как проекты чтобы хорошо в поиске высвечивались».
  //
  // Так и было устроено: статья попадала в выдачу только через какое-нибудь своё
  // утверждение, поэтому у «Benchmarking Optimizers» всплывала цитата про прогрев, а
  // «Fantastic Pretraining Optimizers» не всплывала никак. Замер 10-09-2026 на запросе «как
  // выбрать оптимизатор в претрейне»: без фильтра служба ставит эти статьи на 3, 6 и 7
  // места целыми карточками, с фильтром их в ответе нет совсем.
  //
  // Теперь спрашиваем всё, что служба умеет искать, и она же решает порядок. Статья, проект,
  // подраздел и подтема приходят такими же полноправными ответами, как утверждение.
  const ANSWER_TYPES=[];
  // Режим один: смысловой поиск с переранжировкой кросс-энкодером. Быстрый режим (только
  // полнотекстовый Postgres) был убран по требованию владельца: «мне быстрый поиск прям не
  // нравится, удали его вообще с сайта». Замер 09-09-2026 на тридцати настоящих вопросах
  // объясняет, почему выбор здесь и не нужен: первый ответ попадал по теме 21 раз из 30 за
  // 1.1 секунды у быстрого и 27 из 30 за 7.5 секунды у тщательного. Шесть лишних секунд
  // против шести правильных ответов — выбор в пользу правильного, и делать его каждый раз
  // заново человеку незачем.
  const MCP_CALL={mode:"semantic",scope:"all",limit:20};
  let liveOk=demo?false:null,mcpSeq=0;
  function callLine(q){
    if(demo)return `<p class="mcp-call is-local">${demoScenario(q)?"Подборка по теме · публичная демобаза":"Поиск по открытой демобазе в браузере"}</p>`;
    const args=`query: "${q}", mode: "${MCP_CALL.mode}", scope: "${MCP_CALL.scope}", `
      +`limit: ${MCP_CALL.limit}`;
    return `<pre class="mcp-call"><code>search_lab(${esc(args)})</code></pre>`;
  }
  async function liveHealth(){
    if(demo){liveOk=false;return false}
    try{const r=await proxyFetch(`${PROXY}/health`,{cache:"no-store"});liveOk=r.ok}
    catch{liveOk=false}
    return liveOk;
  }
  // Туннель к brain_lab рвётся под нагрузкой сервера: прокси это видит и поднимает его
  // заново, но запрос, попавший в разрыв, уже провалился. Одна такая осечка не значит, что
  // службы нет, поэтому запрос повторяется — к моменту повтора туннель обычно уже живой.
  async function liveSearch(q,types=ANSWER_TYPES){
    const url=`${PROXY}/search?q=${encodeURIComponent(q)}&limit=${MCP_CALL.limit}&mode=${MCP_CALL.mode}`
      +(types.length?`&types=${encodeURIComponent(types.join(","))}`:"");
    let last=null;
    for(let attempt=0;attempt<3;attempt++){
      if(attempt)await new Promise(done=>setTimeout(done,1500*attempt));
      try{
        const r=await proxyFetch(url,{cache:"no-store"});
        if(r.ok)return r.json();
        last=new Error(`служба ответила ${r.status}`);
        // 502 и 503 — это разрыв туннеля или перегруженный сервер, их имеет смысл повторить.
        // Остальные коды означают, что вопрос не тот, и повтор ничего не изменит.
        if(r.status!==502&&r.status!==503)break;
      }catch(error){last=error}
    }
    throw last||new Error("служба недоступна");
  }
  // Переходы рисуются всегда в области результатов, а не в том блоке, откуда нажали:
  // иначе чипы обзора подменяли сами себя и после первого перехода исчезали.
  function bindResults(scope){
    const out=()=>$("mcp-results");
    const ask=value=>{const inp=$("mcp-search-input");inp.value=value;runSearch(value);
      window.scrollTo({top:0,behavior:"smooth"})};
    const show=html=>{const box=out();if(!box)return;box.innerHTML=html;bindResults(box);
      // Поле поиска прилипшее: без запаса заголовок карточки уезжает под него.
      const top=box.getBoundingClientRect().top+scrollY-150;
      window.scrollTo({top:Math.max(0,top),behavior:"smooth"})};
    // Клик по утверждению ведёт на его карточку, а не подставляет код в поиск:
    // поиск по коду ничего не находил, и переход выглядел как поломка.
    scope.querySelectorAll("[data-base-jump]").forEach(b=>b.onclick=()=>{
      const code=b.dataset.baseJump;
      if(byCode[code])show(recordCard(code));else ask(code)});
    scope.querySelectorAll("[data-open-record]").forEach(b=>b.onclick=()=>{
      const code=b.dataset.openRecord;
      if(!code)return;
      replaceHash(`mcp-live/${code}`);
      show(byCode[code]?.k==="project"?projectCard(code):recordCard(code))});
    scope.querySelectorAll("[data-ask-tool]").forEach(b=>b.onclick=()=>{
      const box=$("mcp-agent");if(box)box.open=true;
      $("mcp-agent-name").value=b.dataset.askTool;
      $("mcp-agent-args").value=b.dataset.askArgs||"{}";
      callAgentTool(b.dataset.askTool,b.dataset.askArgs||"{}");
      $("mcp-agent")?.scrollIntoView({behavior:"smooth",block:"start"})});
    scope.querySelectorAll("[data-copy-link]").forEach(b=>b.onclick=async()=>{
      const link=`${location.origin}${location.pathname}#mcp-live/${b.dataset.copyLink}`;
      try{await navigator.clipboard.writeText(link);b.textContent="ссылка скопирована"}
      catch{b.textContent=link}});
    scope.querySelectorAll("[data-open-term]").forEach(b=>b.onclick=()=>ask(b.dataset.openTerm.replace(/_/g," ")));
    scope.querySelectorAll("[data-open-paper]").forEach(b=>b.onclick=()=>{replaceHash(`mcp-live/paper/${b.dataset.openPaper}`);show(paperCard(b.dataset.openPaper))});
    scope.querySelectorAll("[data-open-folder]").forEach(b=>b.onclick=()=>show(folderPage(b.dataset.openFolder)));
    scope.querySelectorAll("[data-open-theme]").forEach(b=>b.onclick=()=>show(themePage(b.dataset.openTheme)));
    scope.querySelectorAll("[data-open-section]").forEach(b=>b.onclick=()=>show(sectionPage(b.dataset.openSection)));
    scope.querySelectorAll("[data-open-subtopic]").forEach(b=>b.onclick=()=>{
      const [folder,slug]=b.dataset.openSubtopic.split("|");show(subtopicPage(folder,slug))});
    scope.querySelectorAll("[data-mcp-home]").forEach(b=>b.onclick=()=>{
      const inp=$("mcp-search-input");inp.value="";runSearch("")});
  }
  // Results follow the search and topic-navigation panels.
  // Scroll only after an explicit user search; typing must not move the page.
  let askedByHand=false;
  function scrollToResults(){
    if(!askedByHand)return;
    askedByHand=false;
    const box=$("mcp-results");if(!box)return;
    const top=box.getBoundingClientRect().top+scrollY-120;
    window.scrollTo({top:Math.max(0,top),behavior:"smooth"});
  }
  // Снимок и служба отвечают по-разному, а показывать их надо одинаково. Здесь записи
  // снимка приводятся к форме ответа службы: род, идентификатор, заголовок, текст, оценка.
  // Оценки у снимка нет — вместо неё ставится пусто, и на карточке её просто не видно.
  function snapshotItems(q){
    const scenario=demoScenario(q);
    if(scenario)return scenarioItems(scenario,q);
    if(searchIndex)return snapshotRanked(q);
    return snapshotLegacy(q);
  }

  // Curated examples belong only to the public showcase, never to live MCP ranking.
  function demoScenario(q){
    const normalize=value=>String(value).toLowerCase().trim().replace(/[?!.]+$/u,"").trim().replace(/\s+/g," ");
    return demo?.scenarios?.find(s=>normalize(s.text)===normalize(q));
  }

  function scenarioItems(scenario,q){
    return [scenario.paper,...scenario.related].flatMap(id=>{
      const paper=papersById[id];
      if(!paper)return [];
      const featured=id===scenario.paper;
      const extra={paper_id:id,library_folder:paper.f,demo_featured:featured};
      const claims=featured?paper.c:[paperClaim(paper,q)].filter(Boolean);
      return [{entity_type:"paper",entity_id:id,title:paper.t,snippet:paper.s,extra},
        ...claims.map(claim=>({entity_type:"paper_claim",entity_id:id,
          title:paper.t+" — "+claim.s,snippet:"",
          extra:{...extra,claim_kind:claim.k}}))];
    });
  }

  function paperClaim(paper,q){
    const claims=paper?.c||[];
    if(!window.LabSearch)return claims[0];
    const index=new window.LabSearch.Index();
    for(const claim of claims)index.add(claim,[[claim.s,1]]);
    return index.build().search(q,1)[0]||claims[0];
  }

  // Записи из общего индекса в форме ответа службы. Оценка BM25 приводится к 0…1 делением на
  // лучшую: сравнивать её с оценкой кросс-энкодера нельзя, а показывать порядок — можно.
  function snapshotRanked(q){
    // Контекст запроса: области, которые этот же запрос поднял наверх. Нужен из-за омонимов
    // внутри одной базы — «прогрев» это и warmup в обучении, и прогрев кеша векторов в
    // журнале службы. Записи из найденной области весят больше, из чужой меньше.
    const context=new Set();
    for(const item of searchIndex.search(q,8)){
      if(!NODE_KINDS.has(item.kind))continue;
      if(item.kind==="project"||item.kind==="theme"){context.add(item.title);context.add(item.code)}
      else{
        context.add(item.id);
        if(item.kind==="subtopic"&&item.folder)context.add(item.folder);
      }
    }
    const found=searchIndex.search(q,40,{context}).filter(x=>!NODE_KINDS.has(x.kind));
    if(!found.length)return [];
    const best=found[0].score||1;
    // Хвост режется так же, как у живой службы: запись слабее сорока процентов от лучшей
    // отвечает уже на другой вопрос. Без этого на «нужен ли прогрев» в ответ попадали
    // «Агентские скиллы» — там слово «прогрев» встречается в служебной записи.
    return found.filter(x=>x.score>=best*0.4).slice(0,20).map(x=>{
      const snap=x.code?byCode[x.code]:null;
      if(x.kind==="paper"){
        const paper=papersById[x.id];
        const claim=paperClaim(paper,q);
        return {entity_type:"paper_claim",entity_id:x.id,
                title:`${x.title} — ${claim?claim.s:x.text||""}`,
                snippet:claim?claim.s:(x.text||""),score:x.score/best,
                extra:{paper_id:x.id,library_folder:paper?.f,arxiv_id:paper?.ax}};
      }
      return {entity_type:x.kind,entity_id:snap?.id||x.id,title:x.title||"",
              snippet:x.text||"",score:x.score/best,extra:{}};
    });
  }

  function snapshotLegacy(q){
    const out=[];
    for(const x of baseSearch(q,MCP_CALL.limit)){
      const r=x.r||x;
      out.push({entity_type:r.k,entity_id:r.id||r.code||"",title:r.t||"",
                snippet:r.s||"",score:null,extra:{}});
    }
    for(const x of libSearch(q,8)){
      const p=x.p||x;
      const claim=paperClaim(p,q);
      out.push({entity_type:"paper_claim",entity_id:p.id,
                title:`${p.t} — ${claim?claim.s:p.sr||p.s||""}`,
                snippet:claim?claim.s:(p.sr||p.s||""),score:null,
                extra:{paper_id:p.id,library_folder:p.f,arxiv_id:p.ax}});
    }
    return out;
  }

  async function runSearch(q){
    const box=$("mcp-results"),found=$("mcp-found"),call=$("mcp-call-line");if(!box)return;
    const seq=++mcpSeq;
    if(call)call.innerHTML=q.trim()?callLine(q.trim()):"";
    if(!q.trim()){
      box.innerHTML="";
      if(found)found.textContent="";
      return;
    }
    const code=(q.trim().match(/^[A-ZА-Я]-[A-Z]{2,4}-\d{2,4}$/i)||[])[0];
    if(code&&byCode[code.toUpperCase()]){
      const record=byCode[code.toUpperCase()];
      box.innerHTML=record.k==="project"?projectCard(code.toUpperCase()):recordCard(code.toUpperCase());
      if(found)found.textContent="запись по коду";
      if(call)call.innerHTML=`<p class="mcp-call is-local">Открыто по коду из локального снимка: искать смысл в коде записи незачем.</p>`;
      bindResults(box);scrollToResults();return;
    }
    /* Развилки «карта или записи» здесь больше нет.
     *
     * Витрина решала её сама, своим списком слов, и решала иначе, чем служба: на «как
     * выбирать направления в zo» она подменяла верный ответ службы локальным оглавлением.
     * Владелец: «как то не консистентно, давай делать всезде одинаково! выглядит как
     * костыль именно на этот запрос». Правило перенесено в службу целиком
     * (`_asks_for_structure` в retrieval.py) — там оно одно и для человека, и для агента.
     *
     * Раздел, подраздел и подтема теперь приходят от службы такими же ответами, как
     * утверждение, и рисуются карточкой узла со своим содержимым. Спуск по дереву руками
     * никуда не делся: он в блоке «Смотреть по разделам» и доступен всегда.
     */
    // liveOk===null — состояние «не проверяли или последняя попытка сорвалась»: пробуем
    // службу. false ставится только когда health явно не ответил при загрузке страницы.
    if(liveOk===false){
      // Снимок ищет словами, и это не то, что делает агент: об этом сказано прямо.
      // Ветка снимка отдавала ленту разрозненных карточек — ровно то, на что владелец
      // жаловался с самого начала: «выглядит супер непонятно без какого-то контекста».
      // Служба падает часто (общий сервер), и в эти минуты витрина не должна выглядеть
      // хуже, чем обычно. Поэтому снимок приводится к тому же виду, что живой ответ:
      // источник сверху, его записи внутри.
      const items=snapshotItems(q);
      if(found)found.textContent=items.length?`${items.length} по снимку`:"ничего";
      box.innerHTML=items.length?answerPage(items,q)
        :demo?`<p class="mcp-empty">В демобазе нет ответа. Попробуйте один из примеров выше.</p>`:`<p class="mcp-empty">По снимку ничего не нашлось, и это ожидаемо: снимок ищет словами, а не по смыслу. Поднимите живой поиск, и та же строка уйдёт в службу так, как её отправляет агент.</p>`;
      bindResults(box);scrollToResults();return;
    }
    // Кросс-энкодер отвечает 6-14 секунд, и на такой паузе молчащий экран читается как
    // зависание. Счётчик показывает, что ответа ждут, и заодно называет обе стадии.
    box.innerHTML=`<p class="mcp-wait"><b>Служба считает вектор вопроса, затем переранжирует
      ответ кросс-энкодером.</b><span id="mcp-wait-clock">0 с</span></p>`;
    const started=Date.now();
    const clock=setInterval(()=>{const el=$("mcp-wait-clock");
      if(!el){clearInterval(clock);return}
      el.textContent=`${Math.round((Date.now()-started)/1000)} с`},500);
    try{
      let data=await liveSearch(q);
      // Служба считает вектор вопроса отдельным сервисом эмбеддингов. Под нагрузкой сервера
      // он отвечает от 0.9 до 6 секунд, и когда не успевает, служба МОЛЧА переходит на поиск
      // по словам: в логе это «semantic search degraded to lexical». На русском запросе это
      // катастрофа — «прогрев» по словам не находит warmup и выдаёт случайный шум с оценками
      // 0.03 вместо 0.5. Снаружи это видно по matched_by: у здорового ответа там semantic и
      // rerank, у деградировавшего — только lexical. Такой ответ показывать нельзя, его надо
      // переспросить: деградация случайна и со второй попытки обычно не повторяется.
      const degraded=d=>{const xs=d.items||[];
        return xs.length>0&&xs.every(x=>!(x.matched_by||[]).some(m=>m==="semantic"||m==="rerank"))};
      let lexicalOnly=degraded(data);
      if(lexicalOnly){
        const el=$("mcp-wait-clock");
        if(el)el.textContent="векторный поиск не успел, спрашиваю ещё раз";
        try{const again=await liveSearch(q);if(!degraded(again)){data=again;lexicalOnly=false}}
        catch{/* оставляем первый ответ: он хуже, но это ответ */}
      }
      clearInterval(clock);
      if(seq!==mcpSeq)return;
      const items=data.items||[];
      if(found)found.textContent=`${items.length} записей, порядок службы`;
      const warn=lexicalOnly
        ? `<p class="mcp-warn">Служба отвечала без векторного поиска: сервис эмбеддингов не успел, и она перешла на совпадение слов. На русском запросе это даёт мимо: в базе термины записаны латиницей. Спросите ещё раз — обычно со второй попытки вектор считается.</p>`
        : "";
      box.innerHTML=items.length?warn+answerPage(items,q)
        : warn+`<p class="mcp-empty">Служба по этому вопросу ничего не нашла. База знает только то, что кто-то записал явно.</p>`;
      bindResults(box);scrollToResults();
    }catch(error){
      clearInterval(clock);
      if(seq!==mcpSeq)return;
      // Показываем ответ по снимку, но службу мёртвой не объявляем: следующий вопрос снова
      // пойдёт в неё. Раньше одна осечка сажала витрину на снимок до перезагрузки страницы,
      // и человек этого не замечал — он видел просто плохие ответы.
      liveOk=demo?false:null;syncLiveBadge();
      const items=snapshotItems(q);
      box.innerHTML=`<p class="mcp-warn">Служба не ответила (${esc(String(error.message||error))}). Ниже — ответ по локальному снимку: он ищет словами, а не по смыслу. Следующий вопрос снова уйдёт в службу.</p>`
        +(items.length?answerPage(items,q):"");
      if(found)found.textContent=`${items.length} по снимку`;
      bindResults(box);scrollToResults();
    }
  }
  // ============ Карта темы: ответ на широкий запрос ============
  // Владелец: «если поиск как бы просто Muon, то пусть в ответах высвечиваются не конкретные
  // утверждения, а как бы папки, где они лежат… нужно, чтобы пользователь сначала изучил
  // что-то базовое, а потом уже смотрел какие-то клеймы. То есть нужен абстракт к каждой
  // папке и подпапке».
  //
  // Причина простая: по запросу «Muon» ранжировать утверждения нечем. Их в базе сотни, все
  // про Muon, и любое отдельное утверждение вырвано из контекста. А узел дерева отвечает на
  // тот вопрос, который человек на самом деле задал: что здесь есть и с чего начинать.
  const tree=window.LAB_TREE||{sections:[],folders:[],directions:[],themes:[]};
  let treeFolders={};for(const f of tree.folders||[])treeFolders[f.f]=f;
  let treeSections={};for(const x of tree.sections||[])treeSections[x.name]=x;

  /* Форма библиотеки берётся у службы, а файл рядом со страницей — только запасной.
   *
   * Пока форма жила файлом, человек на витрине и агент через MCP видели разное: у агента
   * подтем не было вовсе. Теперь они лежат в базе (миграция 035), и страница спрашивает их
   * тем же вызовом, каким спросил бы агент, — library_tree. Файл остаётся ровно на случай,
   * когда службы нет: тогда витрина честно говорит «снимок» и рисует последнее известное.
   *
   * Идентификаторы статей служба отдаёт целиком, а снимок библиотеки на странице хранит
   * первые восемь знаков. Укорачиваем, иначе дерево ссылается на статьи, которых на
   * странице «нет».
   */
  async function treeFromService(){
    const answer=await proxyFetch(`${PROXY}/tool?name=library_tree&args=${
      encodeURIComponent(JSON.stringify({full:true}))}`,{cache:"no-store"});
    if(!answer.ok)throw new Error(`служба ответила ${answer.status}`);
    const payload=await answer.json();
    if(!Array.isArray(payload.sections))throw new Error("служба вернула не дерево");
    const short=id=>String(id).slice(0,8);
    const folders=[],sections=[];
    for(const section of payload.sections){
      sections.push({name:section.slug,abstract:section.abstract,
        folders:(section.folders||[]).map(f=>f.folder)});
      for(const folder of section.folders||[]){
        folders.push({
          f:folder.folder,a:folder.abstract,
          sub:(folder.subtopic_list||[]).map(t=>
            ({slug:t.slug,t:t.title,a:t.abstract,p:(t.papers||[]).map(short)})),
          rest:(folder.papers_outside_subtopics||[]).map(short),
        });
      }
    }
    return {...tree,sections,folders};
  }
  const themeAbstract={};for(const x of tree.themes||[])themeAbstract[x.code]=x.a;
  const dirOf={};for(const d of tree.directions||[])for(const raw of d.raw||[])dirOf[raw]=d;
  const isTheme=r=>(r.f||[]).some(f=>f[0]==="род"&&f[1]==="theme");
  const fieldsOf=r=>Object.fromEntries((r.f||[]).filter(f=>f.length>=2));

  // Совпадение по узлу: имя папки латиницей, название подтемы по-русски, термин. Поэтому
  // сравниваем и напрямую, и по костяку слова — «муон» должен находить «muon».
  function nodeHit(text,q){
    const t=String(text||"").toLowerCase(), needle=q.toLowerCase().trim();
    if(!needle)return 0;
    if(t===needle)return 3;
    if(t.includes(needle))return 2;
    const skels=libSkels(q);
    return skels.length&&skelHit(t,skels)?1:0;
  }

  const MAP_WORDS=new Set(["направление","направления","направлений","тема","темы","тем",
    "раздел","разделы","разделов","подраздел","подразделы","подтема","подтемы",
    "обзор","структура","список","карта","области","область","проекты","проектов"]);

  // Имя узла — не единственное, чем он описан. «Дообучение» не встречается в названии
  // «Низкоранговая адаптация и PEFT», но стоит в её аннотации, и человек, спросивший про
  // дообучение, ищет именно это направление. Совпадение по аннотации слабее, чем по имени:
  // оно поднимает узел в список, но не выше точного попадания.
  function nodeHitDeep(name,abstract,q){
    const byName=nodeHit(name,q);
    if(byName)return byName;
    // Слова, которыми просят показать устройство базы, из поиска по тексту исключаются.
    // Иначе запрос «какие есть направления в дообучении» цеплял каждую тему, в аннотации
    // которой стоит слово «направление» — и в ответ шли «Отбор студентов в лабораторию» и
    // «Программа A2 Pro». Человек спрашивал не про них.
    const words=(q.toLowerCase().match(/[a-zа-яё0-9-]{4,}/g)||[])
      .filter(w=>!MAP_WORDS.has(w)&&!["какие","какая","есть","этом","этой","наши",
        "лаборатории","лаборатория","показать","покажи"].includes(w));
    if(!words.length)return 0;
    const text=String(abstract||"").toLowerCase();
    // Стем берём от слова целиком и от его основы, плюс английские синонимы из словаря:
    // «дообучении» → «дообучен» → fine-tuning, иначе русское окончание не совпадёт с базой.
    const stems=words.flatMap(w=>{
      const base=w.length>5?w.slice(0,w.length-2):w;
      return [w,base,...(LIB_SYN[w]||"").split(" "),...(LIB_SYN[base]||"").split(" ")];
    }).filter(st=>st&&st.length>3);
    return stems.some(st=>text.includes(st))?1:0;
  }

  const folderStats=folder=>{
    const ps=(lib.papers||[]).filter(p=>p.f===folder);
    return {papers:ps.length,claims:ps.reduce((n,p)=>n+(p.c||[]).length,0)};
  };

  // Что нашлось в карте базы по этому запросу: подразделы, подтемы, направления, проекты.
  // Единый индекс: узлы дерева, записи базы и статьи в одной коллекции, ранжирование BM25.
  // Пока индекс не построен, витрина работает по-старому — это лишь на случай, если файл
  // ядра не загрузился.
  let searchIndex=(window.LabSearch&&window.LAB_TREE)
    ? window.LabSearch.build({tree,base,lib}) : null;

  /* Подменить дерево на то, что отдала служба, и пересобрать всё, что от него зависит.
   *
   * Собирается заново индекс поиска и два указателя, по которым страница открывает узлы.
   * Делается один раз при заходе на раздел MCP: дерево меняется редко, а лишний вызов на
   * каждое действие стоил бы секунды на пустом месте.
   */
  let treeIsLive=false;
  async function adoptServiceTree(){
    if(treeIsLive)return true;
    try{
      const fresh=await treeFromService();
      tree.sections=fresh.sections;tree.folders=fresh.folders;
      treeFolders={};for(const f of tree.folders)treeFolders[f.f]=f;
      treeSections={};for(const x of tree.sections)treeSections[x.name]=x;
      if(window.LabSearch)searchIndex=window.LabSearch.build({tree,base,lib});
      treeIsLive=true;
      const view=$("mcp-live-view"),areas=view?.querySelector(".way-areas");
      if(areas&&!view.hidden){
        const fragment=document.createElement("div");fragment.innerHTML=waysBlock();
        const freshAreas=fragment.querySelector(".way-areas");
        areas.replaceWith(freshAreas);bindResults(freshAreas);
      }
      return true;
    }catch(error){
      // Службы нет — работаем по снимку, и плашка об этом уже говорит. Молчать нельзя,
      // но и ломать страницу из-за дерева тоже: поиск по записям от него не зависит.
      console.warn("дерево библиотеки взято из снимка:",error.message);
      return false;
    }
  }

  // Кто есть кто в выдаче локального индекса. Нужно только запасной ветке по снимку: она
  // берёт узлы как контекст запроса, а отвечает записями. К развилке «карта или записи»
  // отношения не имеет — та живёт в службе.
  const NODE_KINDS=new Set(["section","folder","subtopic","direction","theme","project"]);

  // Широкий ли запрос. Вопрос («нужен ли прогрев», «когда выигрывает Muon») спрашивают у
  // службы: там ответ — утверждение. Имя темы («Muon», «lora_base») спрашивают у карты.
  // Границу слова \b в JS определяет \w, то есть [A-Za-z0-9_], и кириллица в неё не входит.
  // Поэтому регулярка с \b(ли|почему|…)\b на русский вопрос не срабатывала вообще, и
  // «нужен ли прогрев» уходило в карту темы вместо службы. Сравниваем по словам, а не
  // регуляркой с границами.
  //

  // Проект в списке: аннотация и состав сразу, без перехода. Владелец: «должна быть инфа,
  // кто над этим проектом работал, чтобы видно было и на сайте, и агенту».
  // Тема: аннотация написана для витрины, потому что в базе у темы вместо описания стоит
  // машинная склейка вида «Тема объединяет 3 работ. MuonMuon (muon-muon): …».
  function themeTeaser(t){
    const fields=fieldsOf(t);
    const projects=(base.records||[]).filter(r=>r.k==="project"&&!isTheme(r)&&
      fieldsOf(r)["тема"]===fields["тема"]);
    const list=projects.map(p=>
      `<button type="button" data-open-record="${esc(p.code)}">${esc(p.t)}<span>${esc(String((p.hy||[]).length))}</span></button>`).join("");
    return `<article class="map-node is-theme">
      <header><span class="map-node-kind">тема</span>
        <span class="map-node-count">${esc(String(projects.length))} ${esc(plural(projects.length,["проект","проекта","проектов"]))}</span></header>
      <h3>${esc(t.t||"")}</h3>
      <p class="map-node-abstract">${esc(unmark(themeAbstract[t.code]||t.s||""))}</p>
      ${fields["направление"]?`<p class="map-node-where">${esc(fields["направление"])}</p>`:""}
      ${list?`<div class="map-node-subs"><b>Проекты темы</b>${list}</div>`:""}
    </article>`;
  }

  function projectTeaser(p){
    const fields=Object.fromEntries((p.f||[]).filter(f=>f.length>=2));
    const who=p.who||{};
    const team=[...(who.leads||[]),...(who.members||[])];
    return `<article class="map-node is-project">
      <header><span class="map-node-kind">проект</span><code>${esc(p.code||"")}</code>
        <span class="map-node-count">${esc(String((p.hy||[]).length))} утверждений</span>
        ${p.st?`<span class="base-status">${esc(p.st)}</span>`:""}</header>
      <h3>${esc(p.t||"")}</h3>
      <p class="map-node-abstract">${esc(unmark(p.s||""))}</p>
      ${team.length?`<p class="map-node-team"><b>${esc(who.leads?.length?"Ведёт":"Работали")}</b> ${esc((who.leads||[]).join(", "))}${who.members?.length?` · <b>с</b> ${esc((who.members||[]).join(", "))}`:""}</p>`:""}
      ${fields["направление"]?`<p class="map-node-where">${esc([fields["направление"],
        fields["тема"]!==fields["направление"]?fields["тема"]:""].filter(Boolean).join(" · "))}</p>`:""}
      <div class="map-node-go"><button type="button" data-open-record="${esc(p.code)}">Открыть проект целиком →</button></div>
    </article>`;
  }

  // ============ Ответ на вопрос ============
  // Служба возвращает двадцать пять записей одной лентой, и в таком виде это читает агент,
  // а не человек: двадцать пять карточек подряд без разбора невозможно просмотреть глазами.
  // Здесь то же самое, но сверху сказано, из чего состоит ответ, а лента режется на первые
  // восемь и остальное под раскрытием. Порядок службы не меняется: он и есть ответ.
  // «2 измерений» и «3 решений» — так по-русски не говорят, а сводка это первое, что читают.
  // Три формы на каждый род записи: 1 измерение, 2 измерения, 5 измерений.
  const ANSWER_FORMS={
    hypothesis:["наше утверждение","наших утверждения","наших утверждений"],
    paper_claim:["утверждение из статьи","утверждения из статей","утверждений из статей"],
    evidence:["измерение","измерения","измерений"],
    experiment:["прогон","прогона","прогонов"],
    derivation:["выкладка","выкладки","выкладок"],
    decision:["решение","решения","решений"],
    project:["проект","проекта","проектов"],
    paper:["статья","статьи","статей"],
    // Эти рода в ответ попадают редко, и без форм в сводке выходило «3 термин».
    term:["термин","термина","терминов"],
    journal:["запись журнала","записи журнала","записей журнала"],
    resource:["ресурс","ресурса","ресурсов"],
    library_folder:["подраздел библиотеки","подраздела библиотеки","подразделов библиотеки"],
    library_subtopic:["подтема библиотеки","подтемы библиотеки","подтем библиотеки"],
    source:["источник","источника","источников"],
    source_ref:["источник","источника","источников"],
    paper_chunk:["раздел статьи","раздела статьи","разделов статей"]};
  function plural(n,forms){
    if(!forms)return "";
    if(document.documentElement.lang==="en")return forms[Math.abs(n)===1?0:2];
    const a=Math.abs(n)%100,b=a%10;
    if(a>10&&a<20)return forms[2];
    if(b>1&&b<5)return forms[1];
    if(b===1)return forms[0];
    return forms[2];
  }
  const ANSWER_ORDER=["hypothesis","paper_claim","evidence","experiment","derivation","decision","project"];

  // Владелец: «логичнее было бы, чтобы в поиске выскакивал сразу проект или статья, с которой
  // находилось нужное утверждение, а не просто оно оторванное. Потому что сейчас выглядит
  // супер непонятно без какого-то контекста».
  //
  // Поэтому ответ службы не лента карточек, а список источников: проект лаборатории или
  // статья, а внутри — те её утверждения, которые служба посчитала подходящими. Порядок
  // источников задаёт лучшее место его утверждения в ответе службы, то есть ранжирование
  // остаётся её, а не наше.
  // Служба отдаёт полный UUID, а снимок хранит первые восемь знаков: снимок собирается так,
  // чтобы не тащить 36 байт на каждую ссылку. Без приведения переход «открыть статью» из
  // живого ответа не находил статью вообще, и авторы с аннотацией не подхватывались.
  const shortId=v=>String(v||"").slice(0,8);
  function answerSource(x){
    const e=x.extra||{};
    const whole=String(x.title||""),cut=whole.indexOf(" — ");
    // Статья, её раздел и её утверждение — один источник: сама статья. Раньше витрина
    // просила у службы только утверждения, поэтому статья попадала сюда исключительно
    // через них. Теперь служба отдаёт и статью целиком, и её разделы, и они обязаны
    // сойтись в одну карточку, а не встать тремя подряд.
    if(x.entity_type==="paper"){
      const id=shortId(x.entity_id);
      return {key:"paper:"+(id||whole),kind:"paper",id,
              title:whole,folder:e.library_folder||""};
    }
    if(x.entity_type==="paper_claim"||x.entity_type==="paper_chunk"){
      const id=shortId(e.paper_id);
      return {key:"paper:"+(id||(cut>0?whole.slice(0,cut):whole)),kind:"paper",id,
              title:cut>0?whole.slice(0,cut):whole,folder:e.library_folder||""};
    }
    // Узлы библиотеки приходят от службы такими же ответами, как записи: развилки «карта
    // или записи» на витрине больше нет, решает служба. Узел — сам себе источник.
    if(x.entity_type==="library_folder")
      return {key:"folder:"+whole,kind:"folder",id:whole,title:whole,folder:whole};
    if(x.entity_type==="library_subtopic"){
      const folder=e.library_folder||e.folder||"",slug=e.section||e.slug||"";
      const snippet=String(x.snippet||"");
      return {key:"subtopic:"+folder+"|"+(slug||whole),kind:"subtopic",
              id:folder+"|"+slug,title:whole,folder,
              abstract:snippet.startsWith(whole)?snippet.slice(whole.length).trim():snippet};
    }
    const snap=snapById[String(x.entity_id||"").slice(0,8)];
    if(x.entity_type==="project"){
      const code=snap?.code||snap?.pj||"";
      return {key:"project:"+(code||whole),kind:"project",id:code,title:whole,folder:""};
    }
    if(snap?.pj)return {key:"project:"+snap.pj,kind:"project",id:snap.pj,
                        title:snap.pn||snap.pj,folder:""};
    return {key:"loose",kind:"loose",id:"",title:"Записи без проекта",folder:""};
  }

  // Попал ли сам источник, или только что-то внутри него. Статья, найденная целиком, не
  // должна выглядеть как статья, у которой «0 утверждений по запросу»: она и есть ответ.
  const SELF_HIT=new Set(["paper","project","library_folder","library_subtopic"]);

  /* Ответ витрины — ответ службы, без изъятий и без перестановок.
   *
   * Здесь стояли две собственные надстройки. Первая резала выдачу по оценке: всё слабее
   * половины лучшего пряталось под раскрытие. Вторая сворачивала всё после шестого
   * источника. Обе прятали, а не удаляли, и обе появились по делу — владелец про хвост
   * выдачи: «че за хуйня вылезает?».
   *
   * Но это было решение витрины поверх решения кросс-энкодера, и у агента такого нет.
   * Владелец: «проверь также что нет приколов типо фильтрация или что то в этом роде… прям
   * убрать надо все! достало уже это». Убраны обе. Витрина показывает ровно то, что
   * вернула служба, в том порядке, в каком она вернула. Сколько записей просить — это
   * параметр вызова (`limit`), он виден в строке вызова и одинаков для человека и агента.
   */
  function answerPage(items,q){
    const groups=[],index={};
    items.forEach((x,i)=>{
      const src=answerSource(x);
      if(!index[src.key]){index[src.key]={src,items:[],best:i+1};groups.push(index[src.key])}
      index[src.key].items.push({item:x,place:i+1});
    });
    const by={};for(const x of items){const k=x.entity_type||"?";(by[k]=by[k]||[]).push(x)}
    const parts=[...ANSWER_ORDER.filter(k=>by[k]),...Object.keys(by).filter(k=>!ANSWER_ORDER.includes(k))];
    const tally=parts.map(k=>`<span><b>${esc(String(by[k].length))}</b> ${esc(plural(by[k].length,ANSWER_FORMS[k])||KIND[k]||k)}</span>`).join("");
    const ours=(by.hypothesis||[]).length+(by.evidence||[]).length+(by.experiment||[]).length;
    const theirs=(by.paper_claim||[]).length+(by.paper||[]).length;
    const gist=demoScenario(q)?`Работа лаборатории и статьи по теме.`
      :ours&&theirs?`Отвечает и своя работа, и разобранные статьи.`
      :ours?`Отвечает своя работа: записи из прогонов и измерений.`
      :theirs?`В своей работе ответа нет — отвечают разобранные статьи.`:"";
    const head=`<div class="answer-head"><p class="answer-tally">${tally}</p>${gist?`<p class="answer-gist">${esc(gist)}</p>`:""}</div>`;
    // Порядок источников — порядок службы, и только он. Раньше здесь проект безусловно
    // поднимался над статьёй: владелец просил, чтобы «проекты лаборатории выделялись». Но
    // выделять надо видом, а не местом: подъём означал второе ранжирование поверх
    // кросс-энкодера. Проект по-прежнему виден сразу — плашкой, кодом и составом, — но
    // стоит там, куда его поставила служба.
    groups.sort((a,b)=>a.best-b.best);
    return head+groups.map(g=>sourceGroup(g,q)).join("");
  }

  // Источник и его утверждения. Аннотация стоит сразу: владелец «сделай так, чтобы в
  // выпадающем проекте (статье) писалось еще и аннотация его».
  const SRC_KIND={project:"проект лаборатории",paper:"статья",
    folder:"подраздел библиотеки",subtopic:"подтема библиотеки",loose:"без источника"};

  function sourceGroup(group,q){
    const {src,items}=group;
    const snap=src.kind==="project"?byCode[src.id]:null;
    const paper=src.kind==="paper"?papersById[src.id]:null;
    const featured=!!(demo&&paper&&items.some(({item})=>item.extra?.demo_featured));
    const node=src.kind==="folder"?treeFolders[src.id]:null;
    const [subFolder,subSlug]=src.kind==="subtopic"?String(src.id).split("|"):[];
    const topic=src.kind==="subtopic"
      ? ((treeFolders[subFolder]?.sub)||[]).find(t=>t.slug===subSlug) : null;
    // Родные записи источника показываем только тогда, когда сам источник и есть ответ:
    // подраздел раскрывается подтемами, подтема — своими статьями. Это тот самый спуск,
    // ради которого раньше держали отдельную карту, только теперь его открывает служба.
    const children=src.kind==="folder"
      ? (node?.sub||[]).map(t=>`<button type="button" data-open-subtopic="${esc(src.id)}|${esc(t.slug)}">${esc(t.t)}<span>${esc(String(t.p.length))}</span></button>`).join("")
      : src.kind==="subtopic"
      ? (topic?.p||[]).map(id=>papersById[id]).filter(Boolean)
          .sort((a,b)=>(b.c||[]).length-(a.c||[]).length).slice(0,8)
          .map(p=>`<button type="button" data-open-paper="${esc(p.id)}">${esc(p.t)}${p.y?`<span>${esc(String(p.y))}</span>`:""}</button>`).join("")
      : "";
    const abstract=unmark(
      src.kind==="project"?(snap?.s||"")
      :src.kind==="folder"?shorten(node?.a||"",320)
      :src.kind==="subtopic"?shorten(topic?.a||src.abstract||"",320)
      :featured?(paper?.sr||paper?.s||paper?.ab||"")
      :shorten(paper?.sr||paper?.s||paper?.ab||"",320));
    const who=snap?.who||{};
    const team=[...(who.leads||[]),...(who.members||[])];
    const meta=src.kind==="project"
      ? [snap?.st,(snap?.f||[]).find(f=>f[0]==="направление")?.[1]].filter(Boolean).join(" · ")
      : src.kind==="folder"
      ? `${(node?.sub||[]).length} подтем`
      : src.kind==="subtopic"
      ? [subFolder,topic?`${(topic.p||[]).length} ${plural((topic.p||[]).length,["статья","статьи","статей"])}`:""].filter(Boolean).join(" · ")
      : [paper?.au?authorLine(paper.au):"",paper?.v||paper?.y,featured?"":src.folder].filter(Boolean).join(" · ");
    const open=src.kind==="project"
      ? `<button type="button" data-open-record="${esc(src.id)}">Открыть проект: аннотация, все утверждения, терминология →</button>`
      : src.kind==="folder"
      ? `<button type="button" data-open-folder="${esc(src.id)}">Открыть подраздел: все статьи по подтемам →</button>`
      : src.kind==="subtopic"&&topic
      ? `<button type="button" data-open-subtopic="${esc(subFolder)}|${esc(subSlug)}">Открыть подтему: все её статьи →</button>`
      : src.kind==="paper"&&src.id
      ? `<button type="button" data-open-paper="${esc(src.id)}">${featured?"Открыть работу":"Открыть статью: аннотация и все её утверждения"} →</button>`:"";
    // Строки утверждений — только те, что не сам источник: карточка статьи, найденной
    // целиком, не должна показывать саму себя ещё и строкой внутри себя.
    const rows=items.filter(({item})=>!SELF_HIT.has(item.entity_type));
    const count=rows.length
      ? `${rows.length} ${plural(rows.length,["утверждение по запросу","утверждения по запросу","утверждений по запросу"])}`
      : "нашлось целиком";
    return `<article class="src-group is-${featured?"project is-publication":esc(src.kind)}" data-source-id="${esc(src.id)}" data-source-kind="${esc(src.kind)}">
      <header>
        <span class="src-kind">${featured?"Работа лаборатории · статья":esc(SRC_KIND[src.kind]||src.kind)}</span>
        ${src.kind==="project"&&src.id?`<code>${esc(src.id)}</code>`:""}
        <span class="src-count">${esc(count)}</span>
      </header>
      <h3>${esc(src.title||"")}</h3>
      ${meta?`<p class="src-meta">${esc(meta)}</p>`:""}
      ${abstract?`<p class="src-abstract">${esc(abstract)}</p>`:""}
      ${team.length?`<p class="src-team"><b>${esc(who.leads?.length?"Ведёт":"Работали")}</b> ${esc((who.leads||[]).join(", "))}${who.members?.length?` · <b>с</b> ${esc((who.members||[]).join(", "))}`:""}</p>`:""}
      ${children?`<div class="src-children">${children}</div>`:""}
      ${rows.length?`<ol class="src-claims">${rows.map(({item,place})=>claimRow(item,q,place)).join("")}</ol>`:""}
      ${open?`<div class="src-go">${open}</div>`:""}
    </article>`;
  }

  // Утверждение внутри источника. Владелец: «в начале важные утверждения обязаны
  // подсвечиваться как важные. Но не как сейчас — сейчас слова отмечаются, какой-то кринж и
  // как будто всё ещё поиск по словам». Поэтому подсветки слов здесь нет вовсе, а важность
  // берётся из того, чем утверждение закрыто в базе: выкладка и числа — это высшая проба.
  const WEIGHT={proof_and_numbers:3,proof:2,numbers:2,runs_without_numbers:1,open:0};
  function claimRow(item,q,place){
    const kind=item.entity_type;
    const snap=snapById[String(item.entity_id||"").slice(0,8)];
    const whole=String(item.title||""),cut=whole.indexOf(" — ");
    const title=kind==="paper_claim"&&cut>0?whole.slice(cut+3):whole;
    // Служба кладёт в snippet и заголовок, и текст, поэтому тело часто начинается ровно тем
    // же предложением. Показывать его дважды — шум: отрезаем повтор, а не прячем тело.
    let raw=unmark(String(item.snippet||"").replace(/^\S+\s/,""));
    const head=unmark(title);
    if(head&&raw.toLowerCase().startsWith(head.toLowerCase()))raw=raw.slice(head.length).trim();
    if(head&&raw.toLowerCase().includes(head.toLowerCase()))
      raw=raw.split(new RegExp(head.replace(/[.*+?^${}()|[\]\\]/g,"\\$&"),"i")).join(" ").trim();
    const body=shorten(raw.replace(/^[\s—–-]+/,""),260);
    const weight=WEIGHT[snap?.sup]??(kind==="paper_claim"?1:0);
    const score=typeof item.score==="number"?item.score.toFixed(3):"";
    const code=snap?.code||"";
    const x=item.extra||{};
    return `<li class="claim-row${weight>=3?" is-key":""}" data-kind="${esc(kind)}">
      <span class="claim-place">${esc(String(place))}</span>
      <div>
        <p class="claim-text">${esc(unmark(title))}</p>
        ${body.length>15?`<p class="claim-body">${esc(body)}</p>`:""}
        <p class="claim-meta">
          <span class="claim-kind">${esc(KIND[kind]||kind)}</span>
          ${code?`<button class="claim-code" type="button" data-open-record="${esc(code)}">${esc(code)}</button>`:""}
          ${supportBadge(snap)}
          ${x.section?`<span class="claim-section">раздел «${esc(x.section)}»</span>`:""}
          <span class="base-score" title="оценка кросс-энкодера: насколько запись отвечает на вопрос. Порядок задаёт она, а не совпадение слов">${esc(score)}</span>
        </p>
      </div>
    </li>`;
  }
  const shorten=(text="",n=300)=>{const t=String(text).trim();
    return t.length<=n?t:t.slice(0,n).replace(/\s+\S*$/,"")+"…"};
  // Владелец: «в статье аналогично можно писать авторов (ну или et al если много)».
  function authorLine(au=""){
    const names=String(au).split(/,\s*/).filter(Boolean);
    const people=[];for(let i=0;i<names.length;i+=2){
      const last=names[i],first=names[i+1]||"";
      people.push(first?`${last}, ${first[0]}.`:last);
    }
    if(people.length<=2)return people.join(", ");
    return `${people[0]} et al.`;
  }

  // ============ Обзор базы по темам ============
  // Владелец: «надо сделать так, чтобы на сайте можно было всё аккуратно смотреть по темам,
  // не только поиск. Можно условно тыкнуть в тему scaling laws или learning rate и смотреть,
  // какие статьи с гипотезами и проекты с гипотезами есть в базе».
  // theme_slug в базе почти пустой, поэтому осей три настоящие: папки библиотеки (38),
  // темы проектов (23) и термины (59).
  const papersById={};for(const x of (lib.papers||[]))papersById[x.id]=x;
  const CLAIM_KIND={empirical:"эмпирические",theoretical:"теоретические",method:"о методе",definition:"определения"};
  const CLAIM_ORDER=["theoretical","empirical","method","definition"];

  function browseBlock(){
    // Владелец: «в MCP я бы хотел большее дробление, не просто optimization/muon условно, а
    // например ещё поставить один уровень глубины… аналогично надо помещать проекты. Можно
    // подсмотреть, как всё организовано в Yonote».
    //
    // Поэтому обзор идёт тремя осями, и каждая начинается сверху дерева, а не с плоского
    // списка: научные направления → темы → проекты, разделы библиотеки → подразделы →
    // подтемы, и термины поперёк всего. Раскрывать надо руками, поэтому каждый узел здесь
    // свёрнут: одновременно открытых сорока папок никто не читает.
    const dirs=(tree.directions||[]).map(d=>{
      const projects=(base.records||[]).filter(r=>r.k==="project"&&!isTheme(r)&&
        (d.raw||[]).includes(fieldsOf(r)["направление"]));
      const themes=(base.records||[]).filter(r=>r.k==="project"&&isTheme(r)&&
        (d.raw||[]).includes(fieldsOf(r)["направление"]));
      const claims=projects.reduce((n,p)=>n+(p.hy||[]).length,0);
      return `<details class="browse-node">
        <summary><b>${esc(d.t)}</b><span>${esc(String(projects.length))} ${esc(plural(projects.length,["проект","проекта","проектов"]))} · ${esc(String(claims))} ${esc(plural(claims,["утверждение","утверждения","утверждений"]))}</span></summary>
        <p class="browse-abstract">${esc(unmark(d.a||""))}</p>
        ${themes.length?`<div class="browse-list"><em>темы</em>${themes.map(t=>
          `<button type="button" data-open-record="${esc(t.code)}">${esc(t.t)}</button>`).join("")}</div>`:""}
        ${projects.length?`<div class="browse-list"><em>проекты</em>${projects.map(pr=>
          `<button type="button" data-open-record="${esc(pr.code)}">${esc(pr.t)}<span>${esc(String((pr.hy||[]).length))}</span></button>`).join("")}</div>`:""}
      </details>`}).join("");

    const sections=(tree.sections||[]).map(sec=>{
      const stats=sec.folders.reduce((acc,f)=>{const st=folderStats(f);
        return {papers:acc.papers+st.papers,claims:acc.claims+st.claims}},{papers:0,claims:0});
      const rows=sec.folders.map(f=>{
        const node=treeFolders[f],st=folderStats(f);
        const subs=(node?.sub||[]).map(t=>
          `<button type="button" data-open-subtopic="${esc(f)}|${esc(t.slug)}">${esc(t.t)}<span>${esc(String(t.p.length))}</span></button>`).join("");
        return `<details class="browse-node is-folder">
          <summary><b>${esc(f.split("/").pop().replace(/_/g," "))}</b><span>${esc(String(st.papers))} ${esc(plural(st.papers,["статья","статьи","статей"]))} · ${esc(String(st.claims))} ${esc(plural(st.claims,["утверждение","утверждения","утверждений"]))}</span></summary>
          <p class="browse-abstract">${esc(unmark(node?.a||""))}</p>
          ${subs?`<div class="browse-list"><em>подтемы</em>${subs}</div>`:""}
          <div class="browse-go"><button type="button" data-open-folder="${esc(f)}">Все статьи подраздела →</button></div>
        </details>`}).join("");
      return `<details class="browse-node is-section">
        <summary><b>${esc(sec.name)}</b><span>${esc(String(stats.papers))} ${esc(plural(stats.papers,["статья","статьи","статей"]))} · ${esc(String(sec.folders.length))} ${esc(plural(sec.folders.length,["подраздел","подраздела","подразделов"]))}</span></summary>
        <p class="browse-abstract">${esc(unmark(sec.abstract||""))}</p>
        ${rows}
      </details>`}).join("");

    const terms=(base.terms||[]).slice(0,40).map(t=>
      `<button type="button" data-open-term="${esc(t.t)}">${esc(t.t.replace(/_/g," "))}<span>${esc(String(t.n))}</span></button>`).join("");
    const subtopics=(tree.folders||[]).reduce((n,f)=>n+(f.sub||[]).length,0);
    return `<details class="mcp-browse" id="mcp-browse"><summary>Смотреть по разделам, не спрашивая <span>${esc(String((tree.directions||[]).length))} направлений · ${esc(String((tree.sections||[]).length))} разделов · ${esc(String((tree.folders||[]).length))} подразделов · ${esc(String(subtopics))} подтем</span></summary>
      <section><b>Направления лаборатории</b><p>Своя работа: направление объединяет темы, тема — проекты, у проекта свои утверждения, состав и терминология.</p><div class="browse-tree">${dirs}</div></section>
      <section><b>Разделы библиотеки</b><p>Чужие работы в вашей же раскладке. Большие подразделы разбиты на подтемы, у каждого узла аннотация.</p><div class="browse-tree">${sections}</div></section>
      <section><b>Термины</b><p>Поперечная ось: сколько раз термин встречается в утверждениях статей, наших утверждениях и измерениях.</p><div class="mcp-chips is-terms">${terms}</div></section></details>`;
  }

  /* Перерисовать обзор, когда дерево пришло от службы.
   *
   * Обзор рисуется сразу по снимку: ждать ответа службы с пустой страницей хуже, чем
   * секунду показывать последнее известное. Когда ответ пришёл, узлы могли уже раскрыть
   * руками, поэтому раскрытое запоминаем по подписи и возвращаем как было.
   */
  function redrawBrowse(){
    const old=$("mcp-browse");
    if(!old)return;
    const wasOpen=old.open;
    const opened=new Set([...old.querySelectorAll("details[open]")]
      .map(d=>d.querySelector("summary b")?.textContent||"").filter(Boolean));
    old.outerHTML=browseBlock();
    const fresh=$("mcp-browse");
    fresh.open=wasOpen;
    if(opened.size)fresh.querySelectorAll("details").forEach(d=>{
      if(opened.has(d.querySelector("summary b")?.textContent||""))d.open=true});
    bindResults(fresh);
  }

  // Карточка статьи: аннотация и все её утверждения по родам. Владелец: «я должен мочь
  // тыкнуть на эту гипотезу и попасть на карточку статьи, где будет аннотация и список всех
  // гипотез, экспериментов, теорем в этой статье».
  function paperCard(id,q=""){
    const p=papersById[id];
    if(!p)return `<p class="mcp-empty">Этой статьи нет в локальном снимке. Обновить: <code>bash scripts/refresh-snapshots.sh</code></p>`;
    const groups=CLAIM_ORDER.map(k=>{
      const xs=(p.c||[]).filter(c=>c.k===k);
      if(!xs.length)return "";
      return `<section class="paper-claims"><h4>${esc(CLAIM_KIND[k]||k)}<span>${xs.length}</span></h4>
        <ol>${xs.map(c=>`<li class="${c.v?"is-verified":"is-unverified"}"><p>${mark(c.s,q)}</p>${c.q&&c.q!==c.s?`<blockquote>${esc(c.q.slice(0,300))}</blockquote>`:""}${c.q?`<small>${c.v?"цитата сверена с текстом":"цитата не сверена"}</small>`:""}</li>`).join("")}</ol></section>`;
    }).join("");
    const body=p.sr||p.ab||p.s||"";
    return `<article class="paper-page">
      <header><span class="base-kind">${["author-publication","related-publication"].includes(p.origin)?"открытая публикация":demo?"учебная статья":"статья"}</span>${p.f?`<button class="base-folder" type="button" data-open-folder="${esc(p.f)}">${esc(p.f)}</button>`:""}${p.y?`<span class="base-status">${esc(String(p.y))}</span>`:""}</header>
      <h2>${esc(p.t)}</h2>
      <p class="paper-authors">${esc(p.au||"")}${p.v?` · ${esc(p.v)}`:""}</p>
      ${body?`<p class="paper-abstract">${mark(body,q)}</p>`:""}${p.reading_scope?`<p class="paper-authors">Краткий разбор: ${esc(p.reading_scope)}. Утверждения изложены своими словами.</p>`:""}
      <div class="paper-counts"><span>утверждений <b>${esc(String((p.c||[]).length))}</b></span><span>разделов <b>${esc(String(p.ns??p.nc??0))}</b></span>${p.key?`<span>ключ <b>${esc(p.key)}</b></span>`:""}</div>
      <div class="claim-links">${p.ax?`<a href="https://arxiv.org/abs/${esc(p.ax)}" target="_blank" rel="noopener">arXiv ${esc(p.ax)} ↗</a>`:p.source_url?`<a href="${esc(p.source_url)}" target="_blank" rel="noopener">Оригинал статьи ↗</a>`:""}${p.venue_url&&p.venue_url!==p.source_url?`<a href="${esc(p.venue_url)}" target="_blank" rel="noopener">${esc(p.v)} ↗</a>`:""}${p.code_url?`<a href="${esc(p.code_url)}" target="_blank" rel="noopener">Код ↗</a>`:""}<button type="button" data-mcp-home>← к поиску</button></div>
      ${groups||`<p class="mcp-empty">У этой статьи в снимке нет разобранных утверждений.</p>`}</article>`;
  }

  // Страница подтемы: третий уровень библиотеки. Владелец: «надо в больших разделах добавлять
  // ещё разбиение, чтобы было читаемо» — по подразделу из 67 статей идти невозможно.
  function subtopicPage(folder,slug){
    const node=treeFolders[folder];
    const topic=(node?.sub||[]).find(t=>t.slug===slug);
    if(!topic)return `<p class="mcp-empty">Такой подтемы в дереве нет. Пересобрать: <code>python3 scripts/build_tree.py</code></p>`;
    const xs=topic.p.map(id=>papersById[id]).filter(Boolean)
      .sort((a,b)=>(b.c||[]).length-(a.c||[]).length);
    const claims=xs.reduce((n,p)=>n+(p.c||[]).length,0);
    const siblings=(node.sub||[]).filter(t=>t.slug!==slug).map(t=>
      `<button type="button" data-open-subtopic="${esc(folder)}|${esc(t.slug)}">${esc(t.t)}<span>${esc(String(t.p.length))}</span></button>`).join("");
    return `<article class="paper-page is-node">
      <header><span class="base-kind">подтема</span>
        <button class="base-folder" type="button" data-open-folder="${esc(folder)}">${esc(folder)}</button></header>
      <h2>${esc(topic.t)}</h2>
      <p class="node-abstract">${esc(unmark(topic.a||""))}</p>
      <div class="paper-counts"><span>статей <b>${esc(String(xs.length))}</b></span><span>их утверждений <b>${esc(String(claims))}</b></span></div>
      <div class="claim-links"><button type="button" data-open-folder="${esc(folder)}">Весь подраздел ${esc(folder)} →</button><button type="button" data-mcp-home>← к поиску</button></div>
      <ol class="folder-list is-rich">${xs.map(p=>`<li><button type="button" data-open-paper="${esc(p.id)}"><strong>${esc(p.t)}</strong><span>${esc(String((p.c||[]).length))} ${esc(plural((p.c||[]).length,["утверждение","утверждения","утверждений"]))}${p.y?` · ${esc(String(p.y))}`:""}${p.au?` · ${esc(authorLine(p.au))}`:""}</span>${p.sr||p.s?`<em>${esc(shorten(p.sr||p.s,200))}</em>`:""}</button></li>`).join("")}</ol>
      ${siblings?`<div class="node-siblings"><b>Другие подтемы этого подраздела</b>${siblings}</div>`:""}
    </article>`;
  }

  // Страница раздела верхнего уровня: аннотация и подразделы со своими аннотациями. Это
  // верхняя ступень навигации по библиотеке, с которой человек начинает, если не знает,
  // что именно искать.
  function sectionPage(name){
    const sec=treeSections[name];
    if(!sec)return `<p class="mcp-empty">Такого раздела в дереве нет. Пересобрать: <code>python3 scripts/build_tree.py</code></p>`;
    const stats=sec.folders.reduce((acc,f)=>{const st=folderStats(f);
      return {papers:acc.papers+st.papers,claims:acc.claims+st.claims}},{papers:0,claims:0});
    const rows=sec.folders.map(f=>{
      const node=treeFolders[f],st=folderStats(f);
      const subs=(node?.sub||[]).map(t=>
        `<button type="button" data-open-subtopic="${esc(f)}|${esc(t.slug)}">${esc(t.t)}<span>${esc(String(t.p.length))}</span></button>`).join("");
      return `<article class="map-node">
        <header><span class="map-node-kind">подраздел</span><code>${esc(f)}</code>
          <span class="map-node-count">${esc(String(st.papers))} ${esc(plural(st.papers,["статья","статьи","статей"]))} · ${esc(String(st.claims))} ${esc(plural(st.claims,["утверждение","утверждения","утверждений"]))}</span></header>
        <p class="map-node-abstract">${esc(unmark(node?.a||""))}</p>
        ${subs?`<div class="map-node-subs"><b>Подтемы</b>${subs}</div>`:""}
        <div class="map-node-go"><button type="button" data-open-folder="${esc(f)}">Все статьи подраздела →</button></div>
      </article>`}).join("");
    return `<article class="paper-page is-node">
      <header><span class="base-kind">раздел библиотеки</span><code class="base-code">${esc(name)}</code></header>
      <h2>${esc(name)}</h2>
      <p class="node-abstract">${esc(unmark(sec.abstract||""))}</p>
      <div class="paper-counts"><span>статей <b>${esc(String(stats.papers))}</b></span><span>их утверждений <b>${esc(String(stats.claims))}</b></span><span>подразделов <b>${esc(String(sec.folders.length))}</b></span></div>
      <div class="claim-links"><button type="button" data-mcp-home>← к поиску</button></div>
      <div class="map-group">${rows}</div></article>`;
  }

  function folderPage(folder){
    const node=treeFolders[folder];
    const all=(lib.papers||[]).filter(p=>p.f===folder);
    const claims=all.reduce((n,p)=>n+(p.c||[]).length,0);
    // У большого подраздела статьи показываются не одним списком на 67 строк, а по подтемам:
    // сначала аннотация подтемы, потом её статьи. Список без подтем остаётся у маленьких
    // папок, где дробить нечего.
    const subs=(node?.sub||[]);
    const paperRow=p=>`<li><button type="button" data-open-paper="${esc(p.id)}"><strong>${esc(p.t)}</strong><span>${esc(String((p.c||[]).length))} ${esc(plural((p.c||[]).length,["утверждение","утверждения","утверждений"]))}${p.y?` · ${esc(String(p.y))}`:""}${p.au?` · ${esc(authorLine(p.au))}`:""}</span>${p.sr||p.s?`<em>${esc(shorten(p.sr||p.s,200))}</em>`:""}</button></li>`;
    const groups=subs.map(t=>{
      const xs=t.p.map(id=>papersById[id]).filter(Boolean).sort((a,b)=>(b.c||[]).length-(a.c||[]).length);
      return `<section class="paper-claims"><h4>${esc(t.t)}<span>${xs.length}</span></h4>
        <p class="node-abstract is-sub">${esc(unmark(t.a||""))}</p>
        <ol class="folder-list is-rich">${xs.map(paperRow).join("")}</ol></section>`}).join("");
    const restIds=new Set((node?.rest)||[]);
    const rest=subs.length
      ? all.filter(p=>restIds.has(p.id)).sort((a,b)=>(b.c||[]).length-(a.c||[]).length)
      : all.slice().sort((a,b)=>(b.c||[]).length-(a.c||[]).length);
    const restBlock=rest.length
      ? `<section class="paper-claims">${subs.length?`<h4>Вне подтем<span>${rest.length}</span></h4>
          <p class="node-abstract is-sub">Эти статьи не попали ни в одну подтему: по отдельности сюжета не образуют, но из папки их не убирали.</p>`:""}
        <ol class="folder-list is-rich">${rest.map(paperRow).join("")}</ol></section>`:"";
    return `<article class="paper-page is-node">
      <header><span class="base-kind">подраздел библиотеки</span>
        <code class="base-code">${esc(folder)}</code></header>
      <h2>${esc(folder.split("/").pop().replace(/_/g," "))}</h2>
      ${node?.a?`<p class="node-abstract">${esc(unmark(node.a))}</p>`:""}
      <div class="paper-counts"><span>статей <b>${esc(String(all.length))}</b></span><span>их утверждений <b>${esc(String(claims))}</b></span>${subs.length?`<span>подтем <b>${esc(String(subs.length))}</b></span>`:""}</div>
      <div class="claim-links"><button type="button" data-mcp-home>← к поиску</button></div>
      ${groups}${restBlock}</article>`;
  }

  function themePage(slug){
    const t=(base.themes||[]).find(x=>x.th===slug);
    const projects=(base.records||[]).filter(r=>r.k==="project"&&r.th===slug);
    const byCode={};for(const r of (base.records||[]))if(r.k==="hypothesis"&&r.code)byCode[r.code]=r;
    return `<article class="paper-page"><header><span class="base-kind">тема лаборатории</span></header>
      <h2>${esc(t?.t||slug)}</h2>
      <p class="paper-authors">${esc(String(projects.length))} проектов</p>
      <div class="claim-links"><button type="button" data-mcp-home>← к поиску</button></div>
      ${projects.map(pr=>{
        const hyp=(pr.hy||[]).map(code=>byCode[code]).filter(Boolean);
        return `<section class="theme-project"><h3><code class="base-code">${esc(pr.code||"")}</code> <button type="button" data-open-record="${esc(pr.code||"")}">${esc(pr.t)}</button></h3>
          ${pr.s?`<p>${esc(pr.s)}</p>`:""}
          ${hyp.length?`<ol class="folder-list is-rich">${hyp.map(h=>recordRow(h)).join("")}</ol>`
            :`<p class="mcp-empty">У проекта пока нет утверждений в снимке.</p>`}</section>`}).join("")}</article>`;
  }
  // ============ Карточка проекта ============
  // Владелец: «аналогично с проектом лабы, только там будет сильно больше». Всё берётся из
  // снимка, поэтому открывается мгновенно; рядом кнопка спросить живую службу вызовом
  // get_project_by_slug — тем же, которым пользуется агент.
  const byCode={};for(const r of (base.records||[]))if(r.code)byCode[r.code]=r;
  const PROJECT_PARTS=[["hypothesis","Утверждения"],["derivation","Доказательства"],
    ["experiment","Прогоны"],["evidence","Измерения"],["decision","Правила"],
    ["journal","Журнал"],["term","Термины"],["source","Источники"]];
  const field=(r,name)=>((r.f||[]).find(f=>f[0]===name)||[])[1]||"";

  function recordRow(r,q=""){
    const why=field(r,"критерий опровержения")||field(r,"на чём основано")||field(r,"числа")
      ||field(r,"протокол")||field(r,"выкладка")||field(r,"когда");
    return `<li><button type="button" data-open-record="${esc(r.code||r.id||"")}">
      <strong>${mark(r.t||"",q)}</strong>
      ${r.s&&r.s!==r.t?`<em>${mark(String(r.s).slice(0,260),q)}</em>`:""}
      ${why?`<em class="row-why">${esc(String(why).slice(0,220))}</em>`:""}
      <span>${esc(r.code||"")}${r.st?` · ${esc(r.st)}`:""}${r.sup?` · ${esc((SUPPORT[r.sup]||[""])[0])}`:""}</span>
      </button></li>`;
  }

  // Владелец: «должна быть инфа, кто над этим проектом работал, и так далее, чтобы видно
  // было и на сайте, и агенту, и если что можно было бы обратиться». Имена берутся из полей
  // проекта в базе; рабочие адреса в снимок не выгружаются, поэтому здесь только имена.
  // Часть полей проекта хранится в базе массивом (открытые вопросы, предпосылки), и в
  // снимок он попадает строкой вида `["первый", "второй"]`. Показывать человеку сырой JSON
  // нельзя, поэтому массив разбирается в список, а обычная строка остаётся строкой.
  function fieldValue(value=""){
    const text=String(value).trim();
    if(text.startsWith("[")){
      try{
        const items=JSON.parse(text.endsWith("…")?text.slice(0,-1)+"]":text);
        if(Array.isArray(items)&&items.length)
          return `<ul class="field-list">${items.map(x=>`<li>${esc(unmark(String(x)))}</li>`).join("")}</ul>`;
      }catch{
        // Строка обрезана при экспорте и уже не разбирается как JSON: снимаем скобки и
        // кавычки, чтобы читалось как текст, а не как обломок разметки.
        return esc(unmark(text.replace(/^\[/,"").replace(/\]$/,"").replace(/","/g,"; ").replace(/^"|"$/g,"")));
      }
    }
    return esc(unmark(text));
  }

  function teamBlock(pr){
    const who=pr.who||{};
    const leads=who.leads||[],members=who.members||[];
    if(!leads.length&&!members.length)return "";
    const row=(label,names)=>names.length
      ? `<div><dt>${esc(label)}</dt><dd>${names.map(n=>`<span class="person">${esc(n)}</span>`).join("")}</dd></div>`:"";
    return `<dl class="project-team">${row("кто ведёт",leads)}${row("кто работал",members)}</dl>`;
  }

  // Терминология проекта: свои определения, на которые опираются его утверждения. Владелец:
  // «можно было бы тыкнуть на проект и прочитать его аннотацию, список утверждений и
  // терминологию, чтобы прям полностью понять».
  function termsBlock(code){
    const xs=(base.records||[]).filter(r=>r.k==="term"&&r.pj===code);
    if(!xs.length)return "";
    return `<details class="project-terms"><summary>Терминология проекта <span>${esc(String(xs.length))}</span></summary>
      <dl>${xs.map(t=>`<div><dt>${esc(t.t||"")}</dt><dd>${esc(shorten(t.s||"",400))}</dd></div>`).join("")}</dl></details>`;
  }

  function projectWorkspace(pr){
    if(field(pr,"род")==="theme")return "";
    const workspace=window.LAB_PROJECT_WORKSPACES?.projects?.[field(pr,"слаг")];
    const safeUrl=value=>{try{const u=new URL(value);return u.protocol==="https:"&&!u.username&&!u.password?u.href:""}catch{return ""}};
    const links=[["Страница проекта",workspace?.page_url],["Общая доска задач",workspace?.board_url]]
      .map(([label,value])=>[label,safeUrl(value)]).filter(([,url])=>url);
    const tasks=demo?(workspace?.example_tasks||[]):[];
    return `<section class="project-workspace" aria-label="Работа команды"><div class="project-workspace-heading"><div><span>Работа команды</span><h3>Задачи проекта</h3></div>${links.length?`<nav aria-label="Ссылки проекта">${links.map(([label,url])=>`<a href="${esc(url)}" target="_blank" rel="noopener">${esc(label)} ↗</a>`).join("")}</nav>`:""}</div>
      <p>${demo?"Пример общей доски: человек остаётся исполнителем, Hermes помогает выполнять порученную ему работу.":links.length?"Задачи, исполнители и сроки — на общей доске Yonote. Hermes может выполнять задачи, назначенные его владельцу.":!window.LAB_PROJECT_WORKSPACES?"Загружаю ссылки на Yonote…":window.LAB_PROJECT_WORKSPACES.unavailable?"Ссылки на Yonote сейчас не загрузились.":"Доска Yonote пока не привязана к этому проекту."}</p>
      ${tasks.length?`<ul class="project-task-preview">${tasks.map(t=>`<li><span class="project-task-state">${esc(t.status)}</span><strong>${esc(t.title)}</strong><span>${esc(t.assignee)}</span></li>`).join("")}</ul><small>Учебный пример. Карточки выдуманы; действия с настоящей доской здесь недоступны.</small>`:""}
      ${!demo&&links.length?"<small>Смена статусов через Hermes ещё проходит проверку. Ссылка открывает исходную доску.</small>":""}</section>`;
  }

  function projectCard(code,q=""){
    const pr=byCode[code];
    if(!pr||pr.k!=="project")return recordCard(code,q);
    const own=(base.records||[]).filter(r=>r.pj===code&&r.k!=="project");
    const slug=field(pr,"слаг");
    // У большого проекта записей на 28 тысяч пикселей: 45 утверждений, 60 прогонов, столько
    // же измерений. Утверждения — то, за чем сюда приходят, они открыты. Остальное свёрнуто:
    // прогоны и измерения читают, когда уже понятно, какое утверждение проверяют.
    const parts=PROJECT_PARTS.map(([k,label])=>{
      const xs=own.filter(r=>r.k===k);
      if(!xs.length)return "";
      const list=`<ol class="folder-list is-rich">${xs.map(r=>recordRow(r,q)).join("")}</ol>`;
      if(k==="hypothesis")
        return `<section class="paper-claims"><h4>${esc(label)}<span>${xs.length}</span></h4>${list}</section>`;
      return `<details class="paper-claims is-folded"><summary>${esc(label)}<span>${xs.length}</span></summary>${list}</details>`;
    }).join("");
    const about=(pr.f||[]).filter(f=>["задача","подход","состояние","открытые вопросы","направление","тема"].includes(f[0]));
    return `<article class="paper-page" data-project="${esc(code)}">
      <header><span class="base-kind">проект</span><code class="base-code">${esc(code)}</code>${pr.st?`<span class="base-status">${esc(pr.st)}</span>`:""}${pr.th?`<button class="base-folder" type="button" data-open-theme="${esc(pr.th)}">${esc(pr.th)}</button>`:""}</header>
      <h2>${mark(pr.t||"",q)}</h2>
      ${pr.s?`<p class="paper-abstract">${mark(pr.s,q)}</p>`:""}
      ${teamBlock(pr)}
      ${projectWorkspace(pr)}
      ${about.length?`<dl class="project-about">${about.map(f=>`<div><dt>${esc(f[0])}</dt><dd>${fieldValue(f[1])}</dd></div>`).join("")}</dl>`:""}
      ${termsBlock(code)}
      <div class="paper-counts">${PROJECT_PARTS.map(([k,label])=>{const n=own.filter(r=>r.k===k).length;
        return n?`<span>${esc(label.toLowerCase())} <b>${n}</b></span>`:""}).join("")}</div>
      <div class="claim-links">${slug?`<button type="button" data-ask-tool="get_project_by_slug" data-ask-args='{"slug":"${esc(slug)}"}'>Спросить службу: get_project_by_slug ↗</button>`:""}<button type="button" data-mcp-home>← к поиску</button></div>
      ${parts}</article>`;
  }

  // Постоянная ссылка на одну запись по её коду: #mcp-live/H-WBD-001
  function recordCard(code,q=""){
    const r=byCode[code];
    if(!r)return `<p class="mcp-empty">Записи с кодом ${esc(code)} в снимке нет. Обновить: <code>bash scripts/refresh-snapshots.sh</code></p>`;
    if(r.k==="project")return projectCard(code,q);
    const rels=baseRelations(r);
    const fields=(r.f||[]).map(f=>`<div><dt>${esc(f[0])}</dt><dd>${mark(f[1],q)}</dd></div>`).join("");
    return `<article class="paper-page">
      <header><span class="base-kind">${esc(KIND[r.k]||r.k)}</span><code class="base-code">${esc(r.code||"")}</code>${supportBadge(r)}${r.st?`<span class="base-status">${esc(r.st)}</span>`:""}${r.pj?`<button class="base-folder" type="button" data-open-record="${esc(r.pj)}">${esc(r.pn||r.pj)}</button>`:""}</header>
      <h2>${mark(r.t||"",q)}</h2>
      ${r.s&&r.s!==r.t?`<p class="paper-abstract">${mark(r.s,q)}</p>`:""}
      <p class="base-op">попала в базу вызовом <code>${esc(KIND_OP[r.k]||"—")}</code></p>
      <div class="claim-links"><button type="button" data-copy-link="${esc(r.code||"")}">Скопировать ссылку на запись</button><button type="button" data-mcp-home>← к поиску</button></div>
      ${fields?`<dl class="project-about">${fields}</dl>`:""}
      ${rels.length?`<section class="paper-claims"><h4>Связано в базе<span>${rels.length}</span></h4>
        <ol class="folder-list">${rels.map(y=>`<li><button type="button" data-open-record="${esc(y.o.code||"")}"><strong>${esc(y.o.t||"")}</strong><span>${esc(y.dir)} ${esc(y.label)} · ${esc(KIND[y.o.k]||y.o.k)}${y.o.code?` · ${esc(y.o.code)}`:""}</span></button></li>`).join("")}</ol></section>`:""}
    </article>`;
  }

  // ============ Читать как агент ============
  // Владелец: «надо сделать, чтобы этот MCP был как читаем людьми, так и агентами, там
  // должен быть полный функционал». Прокси открывает семнадцать читающих вызовов службы;
  // здесь их можно вызвать руками и увидеть сырой ответ, ровно как его видит агент.
  let agentTools=[];
  async function loadAgentTools(){
    if(demo)return;
    try{const r=await proxyFetch(`${PROXY}/tools`,{cache:"no-store"});agentTools=(await r.json()).tools||[]}
    catch{agentTools=[]}
    const box=$("mcp-agent-tools");
    if(box)box.innerHTML=agentTools.length
      ? agentTools.map(t=>`<button type="button" data-agent-tool="${esc(t)}">${esc(t)}</button>`).join("")
      : `<p class="mcp-empty">Живой службы нет, вызовы недоступны.</p>`;
  }
  async function callAgentTool(name,args){
    const out=$("mcp-agent-out");if(out)out.textContent="спрашиваю службу…";
    try{
      const url=`${PROXY}/tool?name=${encodeURIComponent(name)}&args=${encodeURIComponent(args)}`;
      const r=await proxyFetch(url,{cache:"no-store"});
      const data=await r.json();
      if(out)out.textContent=JSON.stringify(data,null,1).slice(0,20000);
    }catch(error){if(out)out.textContent=String(error)}
  }
  function syncLiveBadge(){
    const badge=$("mcp-live-badge");if(!badge)return;
    badge.className=`mcp-live-badge ${!demo&&liveOk?"is-live":"is-snapshot"}`;
    // Public papers and teaching records are served locally without the private MCP.
    // Предлагать поднять прокси к чужому серверу нечестно, поэтому текст другой.
    badge.innerHTML=!demo&&liveOk
      ? `<b>живая служба</b><span>Поиск по смыслу. Тот же ответ и порядок, что получают агенты.</span>`
      : demo
      ? `<b>показательная сборка</b><span>${esc(demo.note)}</span>`
      // Раньше здесь стояло «Поднять: python3 scripts/mcp-proxy.py». Это требование к
      // человеку, которому делать нечего: туннель держит служба входа в систему и поднимает
      // его сама, как только brain_lab начнёт отвечать. Сервер общий и под нагрузкой иногда
      // не успевает даже на ssh-приветствие — это его состояние, а не поломка витрины.
      : `<b>ищу по снимку</b><span>Общая база лаборатории сейчас не отвечает: сервер занят. Витрина ищет по локальной выгрузке — она полная, но подбирает по словам, а не по смыслу. Связь восстановится сама, обновите страницу через несколько минут.</span>`;
  }
  // ============ Что вообще есть в базе ============
  // Владелец: «дизайн MCP не созвездие, а просто удобная юзер-френдли штука, где можно
  // разное поспрашивать и посмотреть во всей базе». Поэтому сверху не картинка, а счёт:
  // сколько чего лежит и в какой форме. Цвет несёт смысл — тёплый белый наше знание,
  // холодный синий чужие работы, янтарь то, что ещё не закрыто.
  function tallyBlock(){
    const claims=(lib.papers||[]).reduce((n,p)=>n+(p.c||[]).length,0);
    const hyp=(base.records||[]).filter(r=>r.k==="hypothesis");
    const both=hyp.filter(r=>r.sup==="proof_and_numbers").length;
    const open=hyp.filter(r=>r.sup==="open").length;
    const count=k=>(base.records||[]).filter(r=>r.k===k).length;
    return `<section class="tally" aria-label="Состав снимка базы"><p class="tally-caption">В доступном снимке базы</p>
      <div class="tally-row">
        <div class="is-their"><b>${esc(String((lib.papers||[]).length))}</b><span>статей в подборке</span></div>
        <div class="is-their"><b>${esc(String(claims))}</b><span>утверждений из статей</span></div>
        <div class="is-our"><b>${esc(String(hyp.length))}</b><span>наших утверждений</span></div>
        <div class="is-our"><b>${esc(String(count("experiment")))}</b><span>прогонов</span></div>
        <div class="is-our"><b>${esc(String(count("evidence")))}</b><span>измерений</span></div>
        <div class="is-our"><b>${esc(String(count("derivation")))}</b><span>доказательств</span></div>
      </div>
      <p class="tally-note"><b class="is-our">${esc(String(both))}</b> утверждений закрыты и выкладкой, и числами.
        ${demo?"Прогоны и измерения здесь вымышлены. Настоящие публикации находятся в разделах «Публикации Андрея» и «Другие исследования».":"Всё, что ниже, читает ту же базу, что и агенты лаборатории."}</p>
      ${openBlock(hyp)}
    </section>`;
  }

  // Владелец про строку «110 пока ничем»: «вот это исправь!!!!».
  //
  // Цифра врала, и потому раздражала. В эти 110 попадали три совершенно разные вещи:
  // 20 архивных утверждений, которые уже никто не проверяет; 52 черновика и предложения,
  // которые ещё и не заявлялись к проверке; и 38, которые реально стоят в проверке. Одним
  // числом это читается как «110 недоделок», хотя недоделка — только последняя группа.
  // Поэтому число разложено по состояниям, а сами утверждения открываются списком: видно,
  // какому чего не хватает, и с чем идти к автору.
  const OPEN_GROUPS=[
    ["testing","в проверке","эти утверждения проверяются прямо сейчас: прогон идёт или запланирован"],
    ["draft","черновики","сформулированы, но к проверке ещё не заявлены"],
    ["proposed","предложены","ждут решения, брать ли их в работу"],
    ["archived","архив","сняты с проверки, оставлены как история"]];
  function openBlock(hyp){
    const open=hyp.filter(r=>r.sup==="open");
    if(!open.length)return "";
    const groups=OPEN_GROUPS.map(([status,title,why])=>
      ({status,title,why,rows:open.filter(r=>r.st===status)})).filter(g=>g.rows.length);
    const other=open.filter(r=>!OPEN_GROUPS.some(([st])=>st===r.st));
    if(other.length)groups.push({status:"",title:"прочие состояния",why:"",rows:other});
    const summary=groups.map(g=>`<b>${esc(String(g.rows.length))}</b> ${esc(g.title)}`).join(" · ");
    return `<details class="open-claims">
      <summary>Ещё не закрыто ничем: ${summary}</summary>
      ${groups.map(g=>`<section>
        <h4>${esc(g.title)}<span>${esc(String(g.rows.length))}</span></h4>
        ${g.why?`<p>${esc(g.why)}</p>`:""}
        <ol>${g.rows.map(r=>`<li><button type="button" data-open-record="${esc(r.code||"")}">
          <code>${esc(r.code||"")}</code><strong>${esc(r.t||"")}</strong>
          <span>${esc(r.pn||"без проекта")}</span></button></li>`).join("")}</ol>
      </section>`).join("")}
    </details>`;
  }

  // Search and topic navigation use the active dataset.
  // The public demo supplies its own questions.
  const WAY_QUESTIONS=demo?.hints||["нужен ли прогрев и когда он помогает","когда выигрывает Muon",
    "что мы знаем про квантование по кривизне","где метод не сработал"];
  function waysBlock(){
    // Здесь стояли первые семь подпапок по алфавиту — то есть случайная выборка одного
    // уровня. Владелец: «надо в больших разделах добавлять ещё разбиение, чтобы было
    // читаемо». Теперь это разделы верхнего уровня: раздел → подразделы → подтемы.
    const areas=(tree.sections||[]).map(sec=>{
      const stats=sec.folders.reduce((acc,f)=>{const st=folderStats(f);
        return {papers:acc.papers+st.papers,claims:acc.claims+st.claims}},{papers:0,claims:0});
      // Show two examples from populated folders, giving different folders priority.
      const previews=sec.folders.map(f=>({f,n:folderStats(f).papers}))
        .filter(f=>f.n).sort((a,b)=>b.n-a.n).flatMap(({f})=>{
          const topics=[...(treeFolders[f]?.sub||[])].filter(t=>t.p?.length)
            .sort((a,b)=>b.p.length-a.p.length);
          return topics.length?topics.map((t,rank)=>({title:t.t,rank})):
            [{title:f.split("/").pop().replace(/_/g," "),rank:0}];
        }).sort((a,b)=>a.rank-b.rank);
      const examples=[...new Set(previews.map(t=>t.title))].slice(0,2);
      return {name:sec.name,n:stats.papers,claims:stats.claims,folders:sec.folders.length,examples};
    }).sort((a,b)=>b.n-a.n);
    const most=Math.max(1,...areas.map(a=>a.n));
    return `<div class="ways">
      <section class="way way-search"><span>Поиск по общей базе</span>
        <h3>Что хотите узнать?</h3>
        <p>${demo?"Найдите метод или результат из статьи. Поиск по словам работает прямо в браузере.":"Задайте вопрос своими словами. В ответе — утверждения, результаты и их источники."}</p>
        <div class="way-body">
          <form class="way-form" id="mcp-search-form" role="search">
            <label class="sr-only" for="mcp-search-input">Вопрос к общей базе</label>
            <input id="mcp-search-input" type="search" autocomplete="off" placeholder="${esc(demo?WAY_QUESTIONS[0]:"Например, когда помогает прогрев?")}">
            <button type="submit">Спросить</button></form>
          <div class="way-examples">${WAY_QUESTIONS.map(q=>`<button type="button" data-way-ask="${esc(q)}">${esc(q)}</button>`).join("")}</div>
        </div>
        <div id="mcp-call-line" class="way-call"></div></section>

      <section class="way way-explore"><span>От общего к частному</span>
        <h3>Пройти по темам</h3>
        <p>Раздел → подтема → статья → утверждения.</p>
        <div class="way-body"><div class="way-areas">
          ${areas.map(a=>`<button class="way-area" type="button" data-open-section="${esc(a.name)}">
            <span>${esc(a.name)}</span><i style="width:${Math.round(a.n/most*100)}%"></i><em>${esc(String(a.n))}</em>
            ${a.examples.length?`<small class="way-area-topics">${a.examples.map(t=>`<span>${esc(t)}</span>`).join("")}</small>`:""}</button>`).join("")}
        </div></div></section></div>`;
  }
  function showMcpLive(navigate=true){
    const m=systemData.liveMcp;if(!m)return;
    if(navigate)updateHash("mcp-live");
    hidePrimaryViews();active("mcp-live");
    const view=$("mcp-live-view");
    view.hidden=false;
    view.innerHTML=`<div class="special-shell mcp-page knowledge-workspace">
      <header class="mcp-hero"><p>${esc(demo?.label||"Lab Knowledge · BRAIn Lab")}</p><h1>Спросите лабораторию<span aria-hidden="true">.</span></h1>
        <strong>${demo?"Статьи Андрея Веприкова и соавторов: что предложено, как это работает и где прочитать оригинал.":"Что уже проверяли, чем это закончилось и на какие работы опирались."}</strong>
        ${sourceButtons(m.links)}${demo?.publication_folder?`<div class="claim-links"><button type="button" data-open-folder="${esc(demo.publication_folder)}">Все публикации <span>${esc(String(demo.publication_count))}</span> →</button></div>`:""}</header>
      <div class="mcp-live-badge" id="mcp-live-badge"></div>
      ${waysBlock()}
      <output id="mcp-found" class="mcp-found"></output>
      <div id="mcp-results"></div>
      ${tallyBlock()}
      ${browseBlock()}
      ${demo?'':mcpPipeline()}
      ${demo?'':`<details class="for-agents" id="mcp-agent"><summary>Для агентов: те же 17 читающих вызовов службы</summary>
        <p>Человеку это не нужно: выше то же самое обычными словами. Ничего не меняют, писать со страницы нельзя.</p>
        <p class="agent-map">Карта базы, по которой построена навигация выше — разделы, подразделы, подтемы и их аннотации — приходит из самой службы: <code>library_tree</code>, с <code>full: true</code> ещё и подтемы со статьями. Агенту она отвечает на тот же вопрос, что человеку: с чего начинать, если запрос широкий.</p>
        <div class="mcp-chips" id="mcp-agent-tools"></div>
        <form class="agent-form" id="mcp-agent-form">
          <label>вызов<input id="mcp-agent-name" value="list_themes" autocomplete="off"></label>
          <label>аргументы<input id="mcp-agent-args" value="{}" autocomplete="off"></label>
          <button type="submit">Вызвать</button></form>
        <pre class="agent-out" id="mcp-agent-out">Ответ появится здесь.</pre></details>`}
      </div>`;
    const input=$("mcp-search-input");
    let timer=0;
    // Живой запрос стоит службе 6-11 секунд: она считает вектор вопроса и прогоняет
    // кросс-энкодер. Искать на каждую букву значит гонять это по разу на слово, а ответ
    // на экране будет прыгать, пока человек ещё печатает. Поэтому по вводу ищет только
    // снимок — он локальный и бесплатный, — а живую службу спрашивают явно.
    // Поиск по вводу пришлось убрать совсем. Пока служба отвечает, он не запускался, а когда
    // она недоступна, каждая буква запускала поиск по снимку: страница перерисовывалась и
    // уезжала к результатам прямо под руками. Печатать было невозможно.
    //
    // Теперь ввод только рисует строку вызова — она ничего не стоит и показывает, во что
    // превратится вопрос. Ищем по «Спросить» или по Enter.
    input.oninput=()=>{clearTimeout(timer);
      const call=$("mcp-call-line");
      if(call)call.innerHTML=input.value.trim()?callLine(input.value.trim()):"";};
    $("mcp-search-form").onsubmit=e=>{e.preventDefault();clearTimeout(timer);
      askedByHand=true;runSearch(input.value)};
    // Готовый вопрос спрашивается сразу: человек нажал на него именно чтобы получить ответ.
    view.querySelectorAll("[data-way-ask]").forEach(b=>b.onclick=()=>{
      input.value=b.dataset.wayAsk;askedByHand=true;runSearch(input.value);
      $("mcp-results")?.scrollIntoView({behavior:"smooth",block:"start"})});
    bindResults(view);
    const browse=$("mcp-browse");
    if(browse)bindResults(browse);
    const agentForm=$("mcp-agent-form");
    if(agentForm){
      agentForm.onsubmit=e=>{e.preventDefault();
        callAgentTool($("mcp-agent-name").value.trim(),$("mcp-agent-args").value.trim()||"{}")};
      $("mcp-agent")?.addEventListener("click",e=>{
        const b=e.target.closest("[data-agent-tool]");if(!b)return;
        $("mcp-agent-name").value=b.dataset.agentTool;
        callAgentTool(b.dataset.agentTool,$("mcp-agent-args").value.trim()||"{}")});
    }
    loadAgentTools();
    syncLiveBadge();
    // Ссылка вида #mcp-live/H-WBD-001 открывает саму запись, а не пустой поиск.
    const [,deep="",paperId=""]=location.hash.slice(1).split("/");
    if(deep==="paper"&&papersById[paperId]){
      const box=$("mcp-results");
      box.innerHTML=paperCard(paperId);
      bindResults(box);
    }else if(deep&&byCode[deep]){
      const box=$("mcp-results");
      box.innerHTML=byCode[deep].k==="project"?projectCard(deep):recordCard(deep);
      bindResults(box);
    }else runSearch("");
    liveHealth().then(()=>{syncLiveBadge();if(input.value.trim())runSearch(input.value)});
    // Форму базы спрашиваем у службы тем же вызовом, каким её спросил бы агент. Снимок на
    // странице остаётся только запасным: если службы нет, обзор рисуется по нему.
    adoptServiceTree().then(live=>{if(live)redrawBrowse()});
    window.scrollTo({top:0,behavior:"instant"});
    input.focus({preventScroll:true});
  }
    showMcpLive.refreshWorkspace=()=>{
      const article=$("mcp-results")?.querySelector(".paper-page[data-project]");
      const pr=byCode[article?.dataset.project],panel=article?.querySelector(".project-workspace");
      if(pr&&panel)panel.outerHTML=projectWorkspace(pr);
    };
    return showMcpLive;
  }

  let mcpRenderer=null,mcpLoading=null;
  const snapshotLoads=new Map();
  function loadSnapshot(src,globalName){
    if(window[globalName])return Promise.resolve();
    if(!snapshotLoads.has(src)){
      const promise=new Promise((resolve,reject)=>{
        const script=document.createElement("script");
        script.src=window.LAB_I18N?.asset(src)||src;script.async=true;
        script.onload=()=>window[globalName]?resolve():reject(new Error("Snapshot did not initialize"));
        script.onerror=()=>{script.remove();reject(new Error("Snapshot could not be loaded"))};
        document.head.appendChild(script);
      }).catch(error=>{snapshotLoads.delete(src);throw error});
      snapshotLoads.set(src,promise);
    }
    return snapshotLoads.get(src);
  }
  function prepareMcpWorkspace(){
    if(!mcpLoading){
      loadSnapshot("data/project-workspaces.js","LAB_PROJECT_WORKSPACES")
        .catch(()=>{window.LAB_PROJECT_WORKSPACES={projects:{},unavailable:true}})
        .then(()=>mcpRenderer?.refreshWorkspace());
      mcpLoading=Promise.all([
        loadSnapshot("data/library-snapshot.js?v=general-questions-20260916","LAB_LIBRARY"),
        loadSnapshot("data/base-snapshot.js","LAB_BASE"),
        loadSnapshot("data/atlas-tree.js?v=general-questions-20260916","LAB_TREE"),
      ]).then(()=>{mcpRenderer=createMcpWorkspace();renderTally()})
        .catch(error=>{mcpLoading=null;throw error});
    }
    return mcpLoading;
  }
  async function showMcpLive(navigate=true){
    if(mcpRenderer){mcpRenderer(navigate);return}
    if(navigate)updateHash("mcp-live");
    hidePrimaryViews();active("mcp-live");
    const revision=navigationRevision,view=$("mcp-live-view");
    view.hidden=false;
    view.innerHTML=`<div class="special-shell mcp-page knowledge-workspace">
      <header class="mcp-hero"><p>${esc(window.LAB_DEMO?.label||"Lab Knowledge · BRAIn Lab")}</p><h1>Спросите лабораторию<span aria-hidden="true">.</span></h1></header>
      <div class="mcp-load-state" data-mcp-loading><span aria-hidden="true">◌</span><p role="status">Загружаем библиотеку и записи для поиска…</p></div>
      <button class="back-button" data-loading-back type="button">← Вернуться к общей карте</button></div>`;
    view.querySelector("[data-loading-back]").onclick=showOverview;
    window.scrollTo({top:0,behavior:"instant"});
    try{
      await prepareMcpWorkspace();
      if(revision===navigationRevision)mcpRenderer(false);
    }catch(error){
      if(revision!==navigationRevision)return;
      view.querySelector("[data-mcp-loading]").innerHTML=`<p role="alert">Не удалось загрузить данные. Проверьте соединение и попробуйте ещё раз.</p><button type="button" data-mcp-retry>Повторить загрузку</button>`;
      view.querySelector("[data-mcp-retry]").onclick=()=>showMcpLive(false);
    }
  }
  // Journey links retain the selected stage when returning from a tool dossier.
  function showExamples(navigate=true,journeyId="",stageId=""){
    const journeys=systemData.journeys||[];
    if(!navigate)[,journeyId,stageId]=location.hash.slice(1).split("/");
    const journey=journeys.find(x=>x.id===journeyId)||journeys[0];
    if(!journey)return;
    const stage=journey.stages.find(x=>x.id===stageId)||journey.stages[0];
    if(navigate)updateHash(`examples/${journey.id}/${stage.id}`);
    hidePrimaryViews();active("examples");
    const view=$("examples-view");view.hidden=false;
    const pathFor=([from,to])=>{
      const a=journey.stages[from].point,b=journey.stages[to].point,m=(a[0]+b[0])/2;
      return `M ${a[0]} ${a[1]} C ${m} ${a[1]}, ${m} ${b[1]}, ${b[0]} ${b[1]}`;
    };
    view.innerHTML=`<div class="special-shell examples-page" style="--journey-color:${esc(journey.color)}">
      <nav class="journey-choices" aria-label="Исследовательские маршруты">${journeys.map(x=>
        `<a href="#examples/${esc(x.id)}/${esc(x.stages[0].id)}" data-journey="${esc(x.id)}"${x===journey?' aria-current="page"':""}>${esc(x.label)}</a>`).join("")}</nav>
      <header class="journey-head"><p class="overline">Маршруты</p><h1>${esc(journey.title)}</h1><p>${esc(journey.intro)}</p></header>
      <div class="journey-body">
        <div class="journey-chart">
          <div class="journey-map" data-journey-map="${esc(journey.id)}">
            <svg class="journey-lines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
              ${journey.edges.map(edge=>`<path class="journey-thread" d="${pathFor(edge)}"/><path class="journey-direction" d="${pathFor(edge)}" pathLength="100"/>`).join("")}
            </svg>
            <ol class="journey-stages" aria-label="Этапы маршрута">${journey.stages.map((x,i)=>
              `<li style="--stage-x:${x.point[0]}%;--stage-y:${x.point[1]}%"${journey.id==="share"&&i>1?' class="journey-branch"':""}>
                <button type="button" class="journey-star${i===0||i===journey.stages.length-1||(journey.id==="share"&&i===2)?' is-endpoint':""}" data-stage="${esc(x.id)}" aria-pressed="${x===stage}" aria-controls="journey-detail">
                  <span class="journey-orb" aria-hidden="true"><i></i></span><strong>${esc(x.title)}</strong><small>${esc(x.caption)}</small>
                </button></li>`).join("")}</ol>
          </div>
          <p class="journey-note">${esc(journey.note)}</p>
        </div>
        <section id="journey-detail" class="journey-detail" aria-labelledby="journey-stage-title"></section>
      </div></div>`;
    function selectStage(id,navigate=false){
      const selected=journey.stages.find(x=>x.id===id);if(!selected)return;
      if(navigate)updateHash(`examples/${journey.id}/${id}`);
      view.querySelectorAll("[data-stage]").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.stage===id)));
      const detail=view.querySelector(".journey-detail");
      detail.innerHTML=`<p class="journey-stage-label">${esc(selected.caption)}</p>
        <h2 id="journey-stage-title" tabindex="-1">${esc(selected.title)}</h2><p class="journey-action">${esc(selected.action)}</p>
        <dl><dt>С чем начать</dt><dd>${esc(selected.inputs)}</dd><dt>Перед следующим шагом</dt><dd>${esc(selected.check)}</dd></dl>
        <nav class="journey-tools" aria-label="Инструменты этапа">${selected.tools.map(ref=>{
          const tool=byId[ref.process].tools.find(t=>t.id===ref.tool);
          return `<a href="#${esc(ref.process)}/${esc(ref.tool)}" data-journey-process="${esc(ref.process)}" data-journey-tool="${esc(ref.tool)}">${esc(skyName(tool))}<span aria-hidden="true">↗</span></a>`;
        }).join("")}</nav>`;
      detail.querySelectorAll("[data-journey-tool]").forEach(a=>a.onclick=e=>{
        e.preventDefault();
        replaceHash(`examples/${journey.id}/${id}`);
        openProcess(a.dataset.journeyProcess,a.dataset.journeyTool);
      });
    }
    selectStage(stage.id);
    view.querySelectorAll("[data-journey]").forEach(a=>a.onclick=e=>{
      e.preventDefault();showExamples(true,a.dataset.journey);
      requestAnimationFrame(()=>view.querySelector('[data-journey][aria-current="page"]')?.focus({preventScroll:true}));
    });
    view.querySelectorAll("[data-stage]").forEach(b=>{
      b.onclick=()=>{
        selectStage(b.dataset.stage,true);
        if(innerWidth<760){view.querySelector(".journey-detail").scrollIntoView({block:"start",behavior:"instant"});view.querySelector("#journey-stage-title").focus({preventScroll:true})}
      };
      b.onkeydown=e=>{
        const buttons=[...view.querySelectorAll("[data-stage]")],index=buttons.indexOf(b);
        const next=e.key==="Home"?0:e.key==="End"?buttons.length-1:["ArrowRight","ArrowDown"].includes(e.key)?(index+1)%buttons.length:["ArrowLeft","ArrowUp"].includes(e.key)?(index+buttons.length-1)%buttons.length:-1;
        if(next<0)return;e.preventDefault();buttons[next].focus();selectStage(buttons[next].dataset.stage,true);
      };
    });
    window.scrollTo({top:0,behavior:"instant"});
  }
  function active(v){document.querySelectorAll("[data-view]").forEach(b=>{const selected=b.dataset.view===v;b.classList.toggle("active",selected);b.setAttribute("aria-pressed",String(selected))});if(v==="mcp-live"||v==="examples")requestAnimationFrame(()=>{const heading=document.querySelector(`#${v==="mcp-live"?"mcp-live-view":"examples-view"} h1`);if(heading){heading.tabIndex=-1;heading.focus({preventScroll:true})}})}
  function openProcess(id,toolId,navigate=true){const p=byId[id];if(!p)return;if(toolId&&!p.tools?.some(t=>t.id===toolId)){toolId="";replaceHash(id)}if(navigate)updateHash(`${id}${toolId?`/${toolId}`:""}`);hidePrimaryViews();$("process-view").hidden=false;$("process-view").innerHTML=page(p);bind($("process-view"),p);bindGraphMap($("process-view"),p);active("none");window.scrollTo({top:0,behavior:"instant"});$("process-view").querySelector("h1")?.focus({preventScroll:true});if(toolId)setTimeout(()=>{
    const view=$("process-view"),skill=view.querySelector(`[data-skill="${CSS.escape(toolId)}"]`);
    if(skill){let parent=skill.parentElement;while(parent&&parent!==view){if(parent.tagName==='DETAILS')parent.open=true;parent=parent.parentElement}skill.click();return}
    const node=view.querySelector(`[data-node="tool:${CSS.escape(toolId)}"]`);
    if(node){node.click();return}
    // На карте теперь только самое важное, но ссылка на любой инструмент обязана работать:
    // если его узла нет, раскрываем его пункт в досье и подводим к нему.
    const card=view.querySelector(`#tool-${CSS.escape(toolId)}`);
    if(card){card.open=true;card.scrollIntoView({behavior:"smooth",block:"start"});
      card.querySelector("summary")?.focus({preventScroll:true})}
  },50)}
function fitLoopMap(){const overview=document.getElementById("overview"),map=overview?.querySelector(".loop-map");if(!map||overview.hidden)return;
  // Measure the orbit afresh, including when returning from a narrower fallback layout.
  overview.classList.remove("map-stacked");
  // Ниже 1261 карта раскладывается в колонку средствами CSS, масштабировать нечего.
  if(innerWidth<821||innerWidth<=1260){map.style.removeProperty("--map-scale");
    map.style.removeProperty("margin-left");return}
  // Карта нарисована под 760 пикселей высоты. Свободное место — окно минус шапка, заголовок и
  // поля; берём реальную высоту заголовка, а не константы вёрстки, иначе замер разъедется при
  // первой же правке шрифта.
  // Меряем от реальной верхней кромки карты, а не от суммы констант: так масштаб получается
  // ровно под свободное место, и внизу не остаётся пустоты, а сверху ничего не срезается.
  map.style.setProperty("--map-scale","1");
  const top=map.getBoundingClientRect().top+scrollY;
  // Свободное место по ширине — это содержимое родителя, без его полей. Раньше здесь стоял
  // getBoundingClientRect().width, а он считает вместе с полями: на 1280 это 1280 вместо
  // 1177, масштаб выходил 0.883 вместо 0.812, и карта шириной ровно в окно уезжала под
  // поля с обеих сторон. У .overview стоит overflow:hidden, поэтому наружу это выглядело не
  // как прокрутка, а как отрезанные карточки «Созвоны» и «Эксперименты».
  const host=map.parentElement||document.body;
  const pad=getComputedStyle(host);
  const room=host.clientWidth-parseFloat(pad.paddingLeft)-parseFloat(pad.paddingRight);
  // Ниже 0.85 текст на карте становится нечитаемым (замер: 6.8 пикселя на 1440×900), поэтому
  // сильнее не ужимаем, а переходим в две колонки — там кегль остаётся прежним.
  const wanted=Math.min(1,(innerHeight-top-24)/628,room/1450);
  if(wanted<.80){map.style.removeProperty("--map-scale");document.getElementById("overview")?.classList.add("map-stacked");return}
  document.getElementById("overview")?.classList.remove("map-stacked");
  const scale=wanted;
  map.style.setProperty("--map-scale",scale.toFixed(3));
  // Отсчёт масштаба идёт от левого верхнего угла, поэтому центрируем сами: свободное место
  // за вычетом уменьшенной карты, пополам. Иначе карта прижата к левому полю, а на узких
  // экранах правым краем уходила за окно.
  map.style.marginLeft=`${Math.max(0,(room-1450*scale)/2).toFixed(1)}px`}
addEventListener("resize",fitLoopMap);
  function showOverview(navigate=true){requestAnimationFrame(fitLoopMap);if(navigate)updateHash("loop");hidePrimaryViews();$("overview").hidden=false;active("loop");window.scrollTo({top:0,behavior:"instant"})}
  const processNames={"agent-orchestration":"нужно поручить работу отдельному агенту","code-engineering":"нужно изменить или проверить код","discussion":"нужно разобрать обсуждение","experiment-design":"нужно спроектировать проверку идеи","experiment-run":"нужно провести эксперимент","external-review":"нужна независимая проверка","knowledge-maintenance":"нужно сохранить или восстановить знание","literature-discovery":"нужно найти релевантные статьи","literature-ingest":"нужно добавить статью в библиотеку","presentation":"нужно подготовить научный доклад","project-lifecycle":"нужно создать, связать или закрыть проект","publication":"нужно подготовить результат к публикации","research-direction":"нужно уточнить исследовательское направление","results":"нужно разобраться в результатах","theory":"нужно проверить теоретическое рассуждение","writing":"нужно написать или проверить научный текст"};
  const mcpTitles={add_paper_section:"Добавить раздел статьи",assign_public_code:"Назначить публичный код",create_hypothesis:"Сохранить гипотезу",create_project:"Создать проект знаний",define_term:"Определить термин проекта",delete_project:"Удалить пустой проект",delete_record:"Удалить запись",find_related_papers:"Найти связанные статьи",find_similar:"Найти похожие записи",get_hypothesis:"Открыть гипотезу",get_paper:"Открыть статью",get_project_by_slug:"Открыть проект по адресу",get_project_context:"Получить контекст проекта",get_related:"Посмотреть связанные записи",get_theme_context:"Получить контекст темы",get_timeline:"Посмотреть историю изменений",invite_member:"Пригласить участника",issue_agent_token:"Выдать доступ агенту",lab_health:"Проверить состояние лабораторного знания",link_paper:"Связать статью с работой",list_agent_tokens:"Посмотреть доступы агентов",list_derivations:"Посмотреть теоретические выводы",list_hypotheses:"Посмотреть гипотезы",list_journal:"Посмотреть журнал",list_lab_resources:"Посмотреть ресурсы лаборатории",list_paper_claims:"Посмотреть утверждения статьи",list_projects:"Посмотреть проекты",list_recent_papers:"Посмотреть новые статьи",list_terms:"Посмотреть термины",list_themes:"Посмотреть исследовательские темы",list_yonote_tasks:"Посмотреть задачи Yonote",preview_yonote_task:"Проверить задачу перед записью",propose_decision:"Предложить решение",provision_project_workspace:"Подготовить рабочее пространство проекта",publish_source_note:"Опубликовать ссылку на заметку",recent_changes:"Посмотреть последние изменения",record_derivation:"Сохранить теоретический вывод",record_evidence:"Сохранить результат эксперимента",record_experiment:"Сохранить эксперимент",record_journal:"Добавить запись в журнал",record_paper_claim:"Сохранить утверждение статьи",related_by_terms:"Найти связи по терминам",revoke_agent_token:"Отозвать доступ агента",search_lab:"Найти знание лаборатории",set_project_links:"Сохранить ссылки проекта",set_project_open_questions:"Сохранить открытые вопросы",set_project_status:"Изменить статус проекта",set_project_theme:"Связать проект с темой",set_record_papers:"Связать запись со статьями",update_decision:"Утвердить или заменить решение",update_derivation_status:"Обновить статус теоретического вывода",update_experiment_status:"Обновить статус эксперимента",update_hypothesis:"Обновить гипотезу",upsert_call_note:"Сохранить конспект созвона",upsert_paper:"Сохранить статью",upsert_projection_ref:"Связать запись с публичной страницей",upsert_resource:"Сохранить ресурс лаборатории",upsert_yonote_task:"Сохранить задачу Yonote",who_works_on_what:"Понять, кто над чем работает"};
  function humanCapabilityTitle(c){if(c.type!=="mcp-tool"||mcpTitles[c.name])return mcpTitles[c.name]||c.title_ru||c.name;const names={hypothesis:"гипотезу",experiment:"эксперимент",evidence:"результат",claim:"утверждение",paper:"статью",decision:"решение",project:"проект",member:"участника",resource:"ресурс",context:"контекст",journal:"журнал"},parts=String(c.name||"").split("_"),verbs={create:"Сохранить",record:"Сохранить",upsert:"Сохранить",get:"Посмотреть",list:"Посмотреть",search:"Найти",find:"Найти",update:"Обновить",set:"Обновить",assign:"Связать",link:"Связать",preview:"Проверить",validate:"Проверить",issue:"Выдать",invite:"Пригласить",provision:"Подключить",delete:"Удалить",revoke:"Отозвать"},verb=verbs[parts.shift()]||"Выполнить",object=parts.map(x=>names[x]||x).join(" ");return `${verb} ${object}`.trim()}
  function capabilityStory(c){const purpose=c.description_ru||c.description||"Подробный сценарий использования пока не описан.",special=String(c.what_is_special||"").split(/Связан с процессами:|Минимальная проверка:|Назначение:|Related processes:|Related workflows?:|Minimum check:|Purpose:/)[0].trim(),plainSpecial=/ACL|provenance|типизирован|схем|entrypoint|ограниченной ответственностью|typed|schema|defined scope/i.test(special)?"":special,contexts=arr(c.process_ids).map(id=>processNames[id]).filter(Boolean).slice(0,3),type=c.type||"возможность",action=humanCapabilityTitle(c),lowerPurpose=purpose.charAt(0).toLowerCase()+purpose.slice(1),after=type==="agent"?`Сможете поручить агенту конкретную задачу: ${lowerPurpose}`:type==="skill"?`Сможете попросить агента провести весь сценарий: ${lowerPurpose}`:type==="command"?`Сможете одним действием запустить процесс: ${lowerPurpose}`:type==="hook"?`Проверка будет срабатывать автоматически и остановит ошибочное действие до изменения проекта.`:type==="mcp-tool"?`Агенты с подходящими правами смогут ${action.charAt(0).toLowerCase()+action.slice(1)} через общую лабораторную систему.`:type==="documentation"?`Сможете быстро найти актуальный порядок действий и сверить свою настройку.`:type==="repository"?`Сможете использовать и обновлять лабораторные инструменты из одного версионированного источника.`:type==="service"?`Подключенные агенты и приложения получат эту возможность как общий сервис.`:`Сможете использовать эту возможность в своем рабочем процессе.`,categoryCapability=type==="agent"?"самостоятельно выполнить ограниченную задачу и вернуть результат для проверки":type==="skill"?"провести повторяемый рабочий сценарий от исходных данных до проверенного итога":type==="command"?"собрать несколько шагов работы в один управляемый запуск":type==="hook"?"автоматически проверить действие до того, как оно изменит проект":type==="mcp-tool"?"выполнить это действие через общую систему без ручного редактирования базы":type==="documentation"?"сверить порядок действий и ограничения по актуальному источнику":type==="repository"?"работать с версионированными исходниками и видеть историю изменений":type==="service"?"дать нескольким инструментам одну общую возможность и состояние":"использовать возможность в связанном рабочем процессе",rawOutputs=arr(c.outputs_ru||c.outputs).filter(x=>!/типизированный результат|квитанция записи|проверенный профильный артефакт|выводы специалиста или артефакт|typed result|write receipt|verified artifact appropriate to the task|specialist findings or an artifact/i.test(x)),fallbackOutcome=type==="agent"?`Проверенный результат работы агента «${action}»`:type==="skill"?`Завершенный рабочий сценарий «${action}»`:type==="command"?`Результат процесса «${action}»`:type==="hook"?"Автоматическая проверка с понятным решением":type==="mcp-tool"?`Ответ или сохраненное изменение: «${action}»`:type==="documentation"?`Понятный порядок действий по теме «${action}»`:type==="repository"?"Доступ к версионированным исходникам":type==="service"?"Доступный ответ или сохраненное состояние сервиса":`Практический результат по задаче «${action}»`,outcomes=rawOutputs.length?rawOutputs:[fallbackOutcome],capabilities=[purpose,categoryCapability,...(plainSpecial&&plainSpecial!==purpose?[plainSpecial]:[])];return {purpose,capabilities,useCases:contexts.length?contexts:[`когда требуется именно это действие в исследовательском процессе`],outcomes,after}}
  function capSources(c){const own=arr(c.github_urls);if(own.length)return own;const query=encodeURIComponent(c.name||c.source_path||"");return [{label:`Найти ${c.name||"исходник"} в repository`,url:`https://github.com/Vepricov/claude-brainlab/search?q=${query}&type=code`,canonical:true}]}
  function capDetails(c){const match=all.flatMap(p=>(p.tools||[]).map(t=>({p,t}))).find(({t})=>t.skillId===c.name||t.id===c.id||t.id===c.name);if(match)return `<article class="dossier capability-dossier">${dossierHead(match.t,match.p)}${dossierBody(match.t)}</article>`;const story=capabilityStory(c),t={id:c.id,title:humanCapabilityTitle(c),type:capType(c.type),purpose:story.purpose,inside:story.capabilities,outputs:story.outcomes,inputs:c.inputs_ru||c.inputs,gates:c.quality_gates_ru||c.quality_gates,limits:c.known_limitations_ru||c.known_limitations,links:capSources(c),start:story.after};return `<article class="dossier capability-dossier">${dossierHead(t,{title:"Реестр возможностей"})}${dossierBody(t)}</article>`}
  function showCapability(id){const c=(registry.capabilities||[]).find(x=>x.id===id);if(!c)return;$("search-input").value="";$("search-results").innerHTML=capDetails(c);if(!$("search-dialog").open)$("search-dialog").showModal();const heading=$("search-results").querySelector("h2");if(heading){heading.tabIndex=-1;heading.focus()}}
  function searchItems(){return [...all.map(p=>({kind:"Процесс",key:p.id,title:p.title,text:`${p.verb} ${p.purpose} ${arr(p.when).join(" ")} ${arr(p.outcomes).join(" ")}`,go:()=>openProcess(p.id)})),...all.flatMap(p=>(p.tools||[]).filter(t=>!(p.id==="memory"&&t.skillId&&(model.processes||[]).some(ch=>ch.tools.some(x=>x.skillId===t.skillId)))).map(t=>{const story=toolStory(t);return {kind:"Инструмент",key:t.skillId||t.id,title:t.skillId||t.title,text:`${p.title} ${t.cardTitle||""} ${story.value} ${story.capabilities.join(" ")} ${story.useCases.join(" ")} ${story.outcomes.join(" ")}`,go:()=>openQuickTool(p.id,t.id)}})),...(registry.capabilities||[]).filter(c=>c.type!=="command"&&c.type!=="skill").map(c=>({kind:"Полный реестр",key:c.name||c.id,title:humanCapabilityTitle(c),text:`${c.name||""} ${capabilityStory(c).purpose} ${arr(c.process_ids).join(" ")}`,go:()=>showCapability(c.id)}))].filter(x=>!`${x.title} ${x.text}`.toLowerCase().includes("dykaf"))}
  const searchExamples=["разобрать созвон","найти статьи про метод","запустить эксперимент через Hermes","проверить цитату","добавить доступ к серверу","ответить рецензентам"];
  const searchConcepts=[{words:["созвон","разговор","встреч","аудио"],expand:["brain call","call-notes","transcript","решения","задачи"]},{words:["стать","литератур","paper","arxiv"],expand:["paper-search","paper-ingest","literature","zotero","alphaxiv"]},{words:["эксперимент","запуск","обучен","run"],expand:["hermes","experiment","monitoring","protocol","gpu"]},{words:["цитат","ссылк","bibtex"],expand:["citation-verification","paperclaim","references.bib","проверка статей"]},{words:["сервер","доступ","gpu","аккаунт"],expand:["server access bot","managed host","credentials","mlsub"]},{words:["rebuttal","реценз","ответ"],expand:["review-response","writing","paper-self-review"]}];
  const searchIntents={"разобрать созвон":["calls","brain-call","call-notes"],"найти статьи про метод":["literature","paper-search","paperscout"],"запустить эксперимент через Hermes":["experiments","hermes","hermes-experiment-launch"],"проверить цитату":["paper-qa","citation-verification","literature-reviewer"],"добавить доступ к серверу":["access","server-access-bot","hermes-add-user"],"ответить рецензентам":["writing","review-response","rebuttal-command","rebuttal-writer"]};
  function searchScore(item,query){const normalized=query.toLowerCase(),base=`${item.title} ${item.text}`.toLowerCase(),tokens=normalized.match(/[a-zа-яё0-9-]+/g)||[],expanded=[...tokens];for(const concept of searchConcepts)if(concept.words.some(word=>tokens.some(token=>token.includes(word))))expanded.push(...concept.expand);const preferred=searchIntents[normalized]||[],position=preferred.indexOf(item.key),intentBoost=position<0?0:120-position*12;return intentBoost+[...new Set(expanded)].reduce((score,token)=>score+(item.title.toLowerCase().includes(token)?8:base.includes(token)?2:0),0)}
  function renderSearch(q=""){const s=q.trim(),items=searchItems(),exact=items.filter(item=>item.key?.toLowerCase()===s.toLowerCase()),ranked=(exact.length?exact:items.map(item=>({...item,score:s?searchScore(item,s):0})).filter(item=>!s||item.score>0).sort((a,b)=>b.score-a.score||a.title.localeCompare(b.title,document.documentElement.lang)).slice(0,s?15:18)),groups=ranked.reduce((a,x)=>((a[x.kind]||=[]).push(x),a),{}),examples=`<div class="search-examples"><span>Попробуйте описать задачу</span>${searchExamples.map(x=>`<button data-search-example="${esc(x)}" type="button">${esc(x)}</button>`).join("")}</div>`;$("search-results").innerHTML=examples+(ranked.length?Object.entries(groups).map(([kind,xs])=>`<section class="search-group"><h3>${esc(kind)} <span>${xs.length}</span></h3>${xs.map((x,i)=>`<button class="search-item" data-key="${esc(kind)}-${i}" type="button"><strong>${esc(x.title)}</strong><p>${esc(x.text)}</p><i>Открыть →</i></button>`).join("")}</section>`).join(""):`<p class="empty-search">Совпадений нет. Опишите действие другими словами.</p>`);$("search-results").querySelectorAll("[data-search-example]").forEach(b=>b.onclick=()=>{$("search-input").value=b.dataset.searchExample;renderSearch(b.dataset.searchExample)});Object.entries(groups).forEach(([kind,xs])=>xs.forEach((x,i)=>{const b=document.querySelector(`[data-key="${CSS.escape(`${kind}-${i}`)}"]`);if(b)b.onclick=()=>{$("search-dialog").close();x.go()}}))}
  function openSearch(){renderSearch();if(!$("search-dialog").open)$("search-dialog").showModal();requestAnimationFrame(()=>$("search-input").focus())}

  renderLoop();renderToolkit();fitLoopMap();$("home").onclick=showOverview;$("search-open").onclick=openSearch;$("search-input").oninput=e=>renderSearch(e.target.value);document.querySelectorAll("[data-view]").forEach(b=>b.onclick=()=>b.dataset.view==="mcp-live"?showMcpLive():b.dataset.view==="examples"?showExamples():showOverview());document.addEventListener("keydown",e=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==="k"){e.preventDefault();openSearch()}});
  // Разделы слились, но ссылки на прежние адреса могли уже разойтись по чатам.
  const MOVED={"paper-qa":"writing","orchestration":"experiments","engineering":"experiments","access":"projects"};
  let [initial,initialTool]=location.hash.slice(1).split("/");if(MOVED[initial])initial=MOVED[initial];if(initial==="mcp-live")showMcpLive(false);else if(initial==="examples")showExamples(false);else if(initial==="surface")showSurface(initialTool,false);else if(byId[initial])openProcess(initial,initialTool);
  const routeLocation=()=>{let [route,tool]=location.hash.slice(1).split("/");if(MOVED[route])route=MOVED[route];if(route==="mcp-live")showMcpLive(false);else if(route==="examples")showExamples(false);else if(route==="surface")showSurface(tool,false);else if(byId[route])openProcess(route,tool,false);else showOverview(false)};
  window.addEventListener("popstate",routeLocation);
  document.addEventListener("click",e=>{if(e.target.closest("[data-obsidian-surface]")){e.preventDefault();showSurface("obsidian")}});

  // Клик мимо окна поиска закрывает его: у нативного dialog фон входит в сам элемент,
  // поэтому попадание вне рамки контента приходится считать вручную.
  $("search-dialog").addEventListener("click",e=>{const d=$("search-dialog");if(e.target!==d)return;const r=d.getBoundingClientRect();
    if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close()});

  // Страницы разделов длинные, и возвращаться к началу прокруткой неудобно.
  const toTop=document.createElement("button");
  toTop.className="to-top";toTop.type="button";toTop.hidden=true;
  toTop.setAttribute("aria-label","Наверх");toTop.innerHTML="\u2191";
  toTop.onclick=()=>{scrollTo({top:0,behavior:"smooth"});document.querySelector("main h1")?.focus({preventScroll:true})};
  document.body.appendChild(toTop);
  const syncToTop=()=>{toTop.hidden=scrollY<900};
  addEventListener("scroll",syncToTop,{passive:true});syncToTop();
})();
