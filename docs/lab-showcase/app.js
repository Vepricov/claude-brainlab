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
  function spec(title,values){const xs=arr(values);return xs.length?`<div><dt>${esc(title)}</dt><dd>${xs.map(x=>`<span>${esc(x)}</span>`).join("")}</dd></div>`:""}
  function toolVisual(t){if(!t.visual?.nodes?.length)return"";return `<div class="tool-map ${esc(t.visual.kind||"path")}"><span>${esc(t.visual.label||"Как устроено")}</span><ol>${t.visual.nodes.map((node,index)=>`<li><i>${String(index+1).padStart(2,"0")}</i><span>${esc(node)}</span></li>`).join("")}</ol></div>`}
  const previewIds={literature:["paperscout","paper-ingest","alphaxiv-mcp"],ideation:["research-ideation","grill-me","lab-knowledge-hypothesis"],calls:["brain-call","call-notes","yonote-call"],experiments:["hermes","experiment-log","run-monitoring"],results:["results-analysis","results-report","evidence-mcp"],writing:["astar-paper-review","review-response","ml-paper-writing"],presentation:["presentation-skill","paper-to-social"],"paper-qa":["literature-reviewer","citation-verification"]};
  const supportPreviewIds={access:["server-access-bot","server-fleet","server-status"]};
  function previews(p){const ids=previewIds[p.id]||[],picked=ids.map(id=>(p.tools||[]).find(t=>t.id===id)).filter(Boolean),shown=[...picked,...(p.tools||[]).filter(t=>!picked.includes(t))].slice(0,3);return `${shown.slice(0,2).map(t=>`<button data-open="${esc(p.id)}" data-tool="${esc(t.id)}" type="button"><small>${esc(t.type||"tool")}</small>${esc(t.title)}</button>`).join("")}${(p.tools||[]).length>2?`<button class="more" data-open="${esc(p.id)}" type="button">Все ${p.tools.length} →</button>`:""}`}

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
    // Числа берутся из снимка базы: на первом экране должно быть видно, что там не пусто.
    const tally=$("loop-tally");
    if(tally){
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
  function toolStory(t){const capabilities=arr(t.capabilities||t.inside).slice(0,5),useCases=arr(t.useCases||t.when).slice(0,3),outcomes=arr(t.outcomes||t.outputs).slice(0,3),important=arr(t.important||t.limits).slice(0,2);return {value:t.purpose||t.value||t.role,capabilities,useCases,outcomes,afterSetup:t.afterSetup||outcomes[0]||t.role,important}}
  // Три колонки на 1280 растягивали короткие строки в четверть экрана пустоты.
  // «Когда пригодится» дублировало первую фразу описания и убрано.
  function toolValue(t){const story=toolStory(t);return `<div class="tool-value">${focusList("Что делает",story.capabilities.slice(0,4))}<section class="tool-outcome"><b>Что остаётся после</b>${story.outcomes.slice(0,2).map(x=>`<span>${esc(x)}</span>`).join("")}</section></div>`}
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
    let dialog=$("quick-tool-dialog");if(!dialog){dialog=document.createElement("dialog");dialog.id="quick-tool-dialog";dialog.className="quick-tool-dialog";document.body.append(dialog)}
    const story=toolStory(tool),source=links(tool.links||[]);dialog.innerHTML=`<article class="quick-tool-card" style="--accent:${esc(process.color||"#b9ff66")}"><button class="quick-close" type="button" aria-label="Закрыть">×</button><small>${esc(process.title)} · ${esc(tool.type||"Инструмент")}</small><h2 tabindex="-1">${esc(tool.title)}</h2><p>${esc(story.value)}</p><section><b>Что дает</b>${story.outcomes.slice(0,3).map(x=>`<span>${esc(x)}</span>`).join("")}</section><section><b>Что умеет</b>${story.capabilities.slice(0,4).map(x=>`<span>${esc(x)}</span>`).join("")}</section>${toolVisual(tool)}<footer>${source}<button data-full-map type="button">Открыть карту «${esc(process.title)}» →</button></footer></article>`;
    dialog.querySelector(".quick-close").onclick=()=>dialog.close();dialog.querySelector("[data-full-map]").onclick=()=>{dialog.close();openProcess(processId,toolId)};dialog.onclick=e=>{if(e.target===dialog)dialog.close()};dialog.addEventListener("close",()=>trigger?.focus({preventScroll:true}),{once:true});dialog.showModal();dialog.querySelector("h2")?.focus({preventScroll:true})
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
  function controls(p){if(!arr(p.controls).length&&!p.example)return"";const cards=arr(p.controls).map((x,i)=>typeof x==="string"?{title:x.replace(/\.$/,""),explanation:"Это обязательная граница процесса; подробное значение терминов раскрыто в словаре ниже."}:x),exampleText=typeof p.example==="string"?p.example:p.example?.text||p.example?.story||"";return `<section class="process-section control-section">${head("Контроль качества","Почему процесс останавливается или просит человека")}<div class="control-grid">${cards.map(x=>`<article class="control"><small>${esc(x.kind||"Проверка")}</small><h3>${esc(x.title)}</h3><p>${esc(x.explanation||x.text||"")}</p>${x.example?`<div><b>Например</b>${esc(x.example)}</div>`:""}${links(x.links||[],x.title)}</article>`).join("")}</div>${p.example?`<div class="example"><span>${esc(typeof p.example==="object"&&p.example.title?p.example.title:"Разбор одного реального маршрута")}</span><p>${esc(exampleText)}</p>${typeof p.example==="object"?links(p.example.links||[],"Пример"):""}</div>`:""}</section>`}

  // Команда установки — то, за чем посетитель и пришёл. Ровно один блок на карточку,
  // чтобы выделялся и копировался целиком; кнопка копирования не нужна.
  // Владелец: «тут не должна быть такой штуки, должна быть просто ссылка на GitHub, и всё.
  // Не надо это отдельно прописывать и размусоливать». Осталось ровно то, что нужно
  // сделать: команда, если она есть, и ссылка на источник.
  function setup(t){
    const a=t.adoption||{},lines=Array.isArray(a.install)?a.install:a.install?[a.install]:[],src=(t.links||[]).map(liveSource).filter(x=>x.url);
    if(!lines.length&&!src.length)return a.installNote?`<section class="setup-closed"><p>${esc(a.installNote)}</p></section>`:"";
    return `<section class="tool-take" id="setup-${esc(t.id)}">${lines.length?`<pre class="setup-install"><code>${lines.map(esc).join("\n")}</code></pre>`:""}${a.installNote?`<p>${esc(a.installNote)}</p>`:""}${src.length?`<div class="tool-links">${src.map(x=>`<a class="source-link" href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.label||"GitHub")} <span aria-hidden="true">↗</span></a>`).join("")}</div>`:""}</section>`;
  }
  // Посетитель пришёл посмотреть, что можно унести к себе. Это решается одним
  // свойством, поэтому оно стоит прямо в строке заголовка карточки.
  const TAKEABLE=new Set(["toolkit-skill","toolkit-command","toolkit-agent","toolkit-qa","mempalace","zotero","source-only","connector-unpackaged","hermes"]);
  const takeBadge=t=>{const k=t.adoption?.kind||"internal";
    return TAKEABLE.has(k)?`<span class="take-badge is-open">можно забрать</span>`:k==="privileged"?`<span class="take-badge is-gated">по заявке</span>`:`<span class="take-badge is-closed">внутреннее</span>`};
  function toolCard(t){const story=toolStory(t);return `<details class="tool" id="tool-${esc(t.id)}"><summary><span class="tool-type">${esc(t.type||"Инструмент")}</span>${takeBadge(t)}<strong>${esc(t.title)}</strong><span class="tool-role">${esc(story.value)}</span><i class="tool-toggle">+</i></summary><div class="tool-body">${toolValue(t)}<details class="tool-mechanics"><summary>Как работает внутри</summary><div>${toolVisual(t)}<dl class="tool-spec">${spec("Что нужно на вход",t.inputs)}${spec("Как устроено внутри",t.inside)}${spec("Где и как хранится",t.storage)}${spec("Куда сохраняет",t.writes)}${spec("Что важно проверить",t.gates)}${spec("Ограничения",arr(t.limits))}</dl></div></details>${setup(t)}</div></details>`}
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
  function page(p){const map=p.id==="memory"?knowledgeArchitecture(p):`${compactSectionMap(p)}`;return `<div class="process-shell${p.id==="memory"?" memory-shell":""}" style="--accent:${esc(p.color||"#426aff")}"><button class="back-button" data-back type="button">← Вернуться к общей карте</button><header class="process-hero compact"><div class="process-index">${esc(p.number)}</div><div class="process-title"><h1 tabindex="-1">${esc(p.title)}</h1><p class="verb">${esc(p.verb)}</p></div><div class="process-purpose"><p>${esc(p.purpose)}</p></div></header><nav class="process-jump" aria-label="Разделы процесса"><a href="#map">Карта раздела</a>${p.pipeline?'<a href="#pipeline">Как это устроено внутри</a>':""}${p.spotlight?'<a href="#spotlight">Пользуйтесь только этим</a>':""}${p.toMcp?'<a href="#mcp">Что уходит в базу</a>':""}${(p.gallery||[]).length?'<a href="#gallery">Как это выглядит</a>':""}<a href="#tools">Досье инструментов</a></nav>${map}${pipelineBlock(p)}${spotlightBlock(p)}${toMcpBlock(p)}${galleryBlock(p)}${controls(p)}${tools(p)}${implementation(p)}${nav(p)}</div>`}
  function bind(root,p){root.querySelectorAll("[data-back]").forEach(b=>b.onclick=showOverview);root.querySelectorAll("[data-open]").forEach(b=>b.onclick=()=>openProcess(b.dataset.open,b.dataset.tool));root.querySelectorAll("[data-capability]").forEach(b=>b.onclick=()=>showCapability(b.dataset.capability));root.querySelectorAll(".process-jump a").forEach(a=>a.onclick=e=>{e.preventDefault();root.querySelector(a.getAttribute("href"))?.scrollIntoView({behavior:"smooth"})});if(p){const focus=root.querySelector(".map-focus"),toolsById=Object.fromEntries((p.tools||[]).map(t=>[t.id,t])),reset=()=>{root.querySelectorAll(".section-map-canvas button").forEach(x=>x.classList.remove("is-dim","is-active"));focus?.classList.remove("is-open");if(focus)focus.innerHTML=focusDefault(p);replaceHash(p.id)};root.querySelectorAll("[data-focus-tool]").forEach(b=>b.onclick=()=>{root.querySelectorAll(".map-tool").forEach(x=>x.classList.toggle("is-dim",x!==b));b.classList.remove("is-dim");b.classList.add("is-active");if(focus){focus.innerHTML=focusTool(toolsById[b.dataset.focusTool]);focus.classList.add("is-open")}replaceHash(`${p.id}/${b.dataset.focusTool}`)});root.querySelector("[data-map-reset]")?.addEventListener("click",reset);root.querySelectorAll("[data-map-title]").forEach(b=>b.onclick=()=>{root.querySelectorAll(".section-map-canvas button").forEach(x=>x.classList.remove("is-dim","is-active"));b.classList.add("is-active");replaceHash(p.id)});root.onclick=e=>{const dossier=e.target.closest("[data-open-dossier]"),openSetup=e.target.closest("[data-open-setup]");if(e.target.closest("[data-reset-focus]"))reset();if(dossier||openSetup){const id=(dossier||openSetup).dataset.openDossier||(dossier||openSetup).dataset.openSetup,d=root.querySelector(`#tool-${CSS.escape(id)}`);if(d){d.open=true;let focusTarget=d.querySelector("summary"),scrollTarget=d;if(openSetup){const s=root.querySelector(`#setup-${CSS.escape(id)}`);if(s){s.open=true;focusTarget=s.querySelector("summary");scrollTarget=s}}focus?.classList.remove("is-open");scrollTarget.scrollIntoView({behavior:"smooth",block:"start"});focusTarget?.focus({preventScroll:true})}}}}}

  function relationIndex(p){
    const map=normalizedMap(p),index=new Map();
    for(const relation of map.relations){
      const refs=[`stage:${relation.stage}`,...arr(relation.tools).map(x=>`tool:${x}`),...arr(relation.destinations).map(x=>`destination:${x}`),...arr(relation.outcomes).map(x=>`outcome:${x}`),...arr(relation.qa).map(x=>`qa:${x}`)];
      for(const ref of refs){if(!index.has(ref))index.set(ref,new Set());for(const other of refs)index.get(ref).add(other)}
    }
    return {map,index};
  }

  function bindGraphMap(root,p){
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
    scope.addEventListener("click",e=>{if(e.target.closest("[data-reset-knowledge]")){reset(true);return}const tech=e.target.closest("[data-open-knowledge-tech]");if(tech){const details=scope.querySelector(".knowledge-technical");if(details){details.open=true;details.scrollIntoView({behavior:"smooth",block:"start"});details.querySelector("summary")?.focus()}return}const jump=e.target.closest("[data-knowledge-jump]");if(jump){const target=jump.dataset.knowledgeJump;if(target.startsWith("process:")){openProcess(target.slice(8));return}const targetNode=scope.querySelector(`[data-knowledge="${CSS.escape(target)}"]`);targetNode?.click();targetNode?.focus({preventScroll:true});return}const button=e.target.closest("[data-knowledge]");if(!button)return;lastTrigger=button;const key=button.dataset.knowledge,[kind,id]=key.split(":"),term=(model.shared?.glossary||[]).find(x=>x.id===id||x.id.replace("foreign-","")===id),item=groups[kind]?.[id]||{title:button.querySelector("strong")?.textContent||id,detail:term?.meaning||button.querySelector("span,small")?.textContent||""},connectionObjects=arr(item.connections).filter(x=>x&&typeof x==="object"&&x.to),relatedKeys=new Set(connectionObjects.map(x=>x.to));for(const [groupName,items] of Object.entries(groups))for(const [itemId,candidate] of Object.entries(items))if(arr(candidate.connections).some(x=>x?.to===key))relatedKeys.add(`${groupName}:${itemId}`);if(key==="boundary:mcp")scope.querySelectorAll("[data-knowledge]").forEach(x=>relatedKeys.add(x.dataset.knowledge));scope.querySelectorAll("[data-knowledge]").forEach(x=>{const active=x.dataset.knowledge===key,related=relatedKeys.has(x.dataset.knowledge);x.classList.toggle("is-active",active);x.classList.toggle("is-related",!active&&related);x.classList.toggle("is-muted",!active&&!related);x.setAttribute("aria-pressed",String(active))});const kindLabel={object:"Тип общей записи",flow:"Шаг безопасной публикации",read:"Шаг безопасного чтения",guard:"Обязательное правило",bridge:"Связь внешнего источника с нашей работой",producer:"Источник информации",consumer:"Потребитель знания",corpus:"Раздел общей базы",boundary:"Компонент системы",personal:"Отдельный личный слой"}[kind]||"Часть системы",connections=arr(item.related||item.connections||item.usedBy).map(x=>typeof x==="string"?{label:x}:x),clickableConnections=connections.filter(x=>x.to),notes=connections.filter(x=>!x.to),targetTitle=target=>scope.querySelector(`[data-knowledge="${CSS.escape(target)}"] strong`)?.textContent||target.replace(/^\w+:/,"");focus.innerHTML=`<div class="focus-head"><small>${esc(kindLabel)}</small><button data-reset-knowledge type="button" aria-label="Закрыть карточку">×</button><h3 tabindex="-1">${esc(item.label||item.title_ru||item.title||id)}</h3><p>${esc(item.detail||item.summary||item.action||item.plain||"")}</p></div><div class="focus-detail-grid">${focusList("Что находится внутри",item.contains)}${focusList("Кто и как получает доступ",item.access)}${focusList("Что происходит",item.behavior)}${focusList("Обязательные данные",item.required)}</div>${clickableConnections.length?`<div class="focus-related"><b>Перейти к связанному узлу</b>${clickableConnections.map(x=>`<button data-knowledge-jump="${esc(x.to)}" type="button"><small>${esc(x.label||"Связь")}</small>${esc(targetTitle(x.to))}</button>`).join("")}</div>`:""}${notes.length?`<div class="focus-notes"><b>Важно</b>${notes.map(x=>`<p>${esc(x.label||x.name||x.role||"")}</p>`).join("")}</div>`:""}${item.operations?.length?`<div class="focus-operations"><b>Настоящие инструменты MCP</b>${arr(item.operations).map(x=>`<code>${esc(x)}</code>`).join("")}</div>`:""}<div class="map-focus-actions"><button data-open-knowledge-tech type="button">Подключение и техническая схема</button>${links(item.links||[],item.title||id)}</div>`;focus.classList.add("is-open");if(matchMedia("(max-width:1100px)").matches)focus.scrollIntoView({behavior:"smooth",block:"nearest"})});
    const closeFocusPanel=()=>{if(focus.classList.contains("is-open"))reset(true)};document.addEventListener("keydown",e=>{if(e.key==="Escape"&&focus.classList.contains("is-open")){e.preventDefault();closeFocusPanel()}});document.addEventListener("pointerdown",e=>{if(!focus.classList.contains("is-open"))return;if(focus.contains(e.target)||(e.target.closest&&e.target.closest("[data-node],[data-knowledge],[data-surface-process]")))return;closeFocusPanel()},true);
  }
  function sourceButtons(items=[]){return `<div class="special-links">${items.map(x=>{const url=safe(x.url);return url?`<a href="${esc(url)}" target="_blank" rel="noopener">${esc(x.label)} <span>↗</span></a>`:""}).join("")}</div>`}
  function hidePrimaryViews(){$("overview").hidden=true;$("process-view").hidden=true;$("dykaf-view").hidden=true;$("mcp-live-view").hidden=true;$("examples-view").hidden=true}
  function showSurface(id,navigate=true){const s=systemData.surfaces?.[id];if(!s)return;if(navigate)updateHash(`surface/${id}`);hidePrimaryViews();active("none");const view=$("process-view");view.hidden=false;view.innerHTML=`<div class="process-shell surface-page" style="--accent:#b9ff66"><button class="back-button" data-back type="button">← Вернуться к общей карте</button><header class="surface-hero"><p>${esc(s.kicker)}</p><span>${esc(s.number)}</span><h1 tabindex="-1">${esc(s.title)}</h1><strong>${esc(s.promise)}</strong></header><section class="surface-map" aria-label="Карта ${esc(s.title)}"><div class="surface-orbit"><div class="surface-center"><small>Отвечает за</small><strong>${esc(s.title)}</strong><span>${esc(s.promise)}</span></div>${s.owns.map((x,i)=>`<article style="--i:${i}"><small>Хранит ${String(i+1).padStart(2,"0")}</small><strong>${esc(x)}</strong></article>`).join("")}</div>${s.facts?.length?`<div class="surface-facts">${s.facts.map(x=>`<span>${esc(x)}</span>`).join("")}</div>`:""}<div class="surface-flow"><p>Как используется</p>${s.path.map((x,i)=>`<article><span>${String(i+1).padStart(2,"0")}</span><strong>${esc(x)}</strong></article>`).join("")}</div>${s.routes?.length?`<nav class="surface-routes" aria-label="Связанные карты">${s.routes.map(x=>`<button data-surface-process="${esc(x.process)}" data-surface-tool="${esc(x.tool||"")}" type="button"><small>${esc(x.kind||"Связанная карта")}</small><strong>${esc(x.title)}</strong><span>${esc(x.text||"")}</span><i>Открыть →</i></button>`).join("")}</nav>`:""}</section><section class="surface-boundary"><div><p>Это место не заменяет</p>${s.doesNotOwn.map(x=>`<span>${esc(x)}</span>`).join("")}</div><div><p>Связь с общей системой</p><span>Обмен идёт через ссылки и явные сценарии. Изменяемая копия у каждого типа данных остаётся одна.</span>${sourceButtons(s.links)}</div></section></div>`;view.querySelector("[data-back]").onclick=showOverview;view.querySelectorAll("[data-surface-process]").forEach(b=>b.onclick=()=>openProcess(b.dataset.surfaceProcess,b.dataset.surfaceTool));window.scrollTo({top:0,behavior:"instant"});view.querySelector("h1")?.focus({preventScroll:true})}
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
      ${step("add_paper_section",`Разделы: ${p.nc}`,"сохранённый текст, с которым потом сверяется каждая цитата","is-rec")}
      ${step("record_paper_claim",`Утверждения статьи: ${p.nm}`,"формулировка от 80 знаков, дословная цитата от 25, сверка с сохранённым текстом","is-rec")}
      ${step("link_paper",`Связей с нашей работой: ${ls.length}`,tie,"is-tie")}
    </ol>`;
  }
  function libCard(x,q){
    const p=x.p,ls=linksByPaper[p.id]||[];
    const claims=(p.c||[]).map((c,k)=>`<li class="${x.hits.includes(k)?"is-hit":""}"><small>${esc(CKIND[c.k]||c.k||"")}${c.v?" · цитата сверена":" · цитата не сверена"}</small>${esc(c.s)}</li>`).join("");
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
  const PROXY="http://127.0.0.1:8799";
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
  const ANSWER_TYPES=["hypothesis","evidence","derivation","decision","paper_claim"];
  const MCP_CALL={mode:"semantic",scope:"all",limit:20};
  let liveOk=null,mcpSeq=0;
  function callLine(q){
    const args=`query: "${q}", mode: "${MCP_CALL.mode}", scope: "${MCP_CALL.scope}", `
      +`limit: ${MCP_CALL.limit},\n         entity_types: [${ANSWER_TYPES.map(t=>`"${t}"`).join(", ")}]`;
    return `<pre class="mcp-call"><code>search_lab(${esc(args)})</code></pre>`;
  }
  async function liveHealth(){
    try{const r=await fetch(`${PROXY}/health`,{cache:"no-store"});liveOk=r.ok}
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
        const r=await fetch(url,{cache:"no-store"});
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
    scope.querySelectorAll("[data-open-paper]").forEach(b=>b.onclick=()=>show(paperCard(b.dataset.openPaper)));
    scope.querySelectorAll("[data-open-folder]").forEach(b=>b.onclick=()=>show(folderPage(b.dataset.openFolder)));
    scope.querySelectorAll("[data-open-theme]").forEach(b=>b.onclick=()=>show(themePage(b.dataset.openTheme)));
    scope.querySelectorAll("[data-open-section]").forEach(b=>b.onclick=()=>show(sectionPage(b.dataset.openSection)));
    scope.querySelectorAll("[data-open-subtopic]").forEach(b=>b.onclick=()=>{
      const [folder,slug]=b.dataset.openSubtopic.split("|");show(subtopicPage(folder,slug))});
    scope.querySelectorAll("[data-force-ask]").forEach(b=>b.onclick=()=>{
      const q=b.dataset.forceAsk;forceAsk.add(q);
      const inp=$("mcp-search-input");inp.value=q;askedByHand=true;runSearch(q)});
    scope.querySelectorAll("[data-mcp-home]").forEach(b=>b.onclick=()=>{
      const inp=$("mcp-search-input");inp.value="";runSearch("")});
  }
  // «Всё равно спросить утверждения» — запрос, для которого человек сознательно отказался от
  // карты темы. Помним такие, иначе кнопка не сработает: карта перехватит его снова.
  const forceAsk=new Set();
  // Ответ лежит под тремя колонками способов, и после нажатия «Спросить» человек оставался
  // наверху: список тем по запросу был на экран ниже. Раз запрос теперь отправляют явно,
  // явным должен быть и переход к ответу.
  // Прокрутка допустима только если вопрос отправил человек. Любая прокрутка «сама» во время
  // работы с полем воспринимается как то, что страницу выдернули из-под рук.
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
    if(searchIndex)return snapshotRanked(q);
    return snapshotLegacy(q);
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
      else context.add(item.id);
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
        const claim=(paper?.c||[]).slice().sort((a,b)=>(b.s||"").length-(a.s||"").length)[0];
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
      // У статьи в снимке показываем её самое длинное разобранное утверждение: именно оно
      // отвечает на вопрос, а не название статьи.
      const claim=(p.c||[]).slice().sort((a,b)=>(b.s||"").length-(a.s||"").length)[0];
      out.push({entity_type:"paper_claim",entity_id:p.id,
                title:`${p.t} — ${claim?claim.s:p.sr||p.s||""}`,
                snippet:claim?claim.s:(p.sr||p.s||""),score:null,
                extra:{paper_id:p.id,library_folder:p.f,arxiv_id:p.ax}});
    }
    return out;
  }

  // Записи под картой. Идут отдельно и не мешают карте: она уже на экране, а это дозагрузка.
  async function fillMapRecords(q,seq){
    const box=$("map-records");if(!box)return;
    let items=[];
    if(liveOk!==false){
      try{const data=await liveSearch(q);items=data.items||[]}
      catch{items=snapshotItems(q)}
    }else items=snapshotItems(q);
    if(seq!==mcpSeq||!$("map-records"))return;
    const target=$("map-records");
    target.innerHTML=items.length
      ? `<p class="overline">Записи по этой теме</p>`+answerPage(items,q)
      : `<p class="map-records-wait">По этой теме отдельных записей не нашлось — смотрите разделы выше.</p>`;
    bindResults(target);
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
    // Широкий запрос («Muon», «lora_base») отвечается картой темы и не идёт в службу:
    // ранжировать по нему отдельные утверждения нечем, их сотни и все про то же самое.
    // Карта отвечает на «что тут есть», но не отвечает на «покажи записи». Раньше на этом
    // всё и заканчивалось: по запросу «нижние оценки» человек получал два узла карты, хотя в
    // базе одиннадцать записей и двадцать две статьи по теме, и должен был сам догадаться
    // нажать «всё равно спросить». Теперь карта показывается сразу, а записи догружаются под
    // ней сами: карта видна мгновенно, записи приходят через те секунды, что считает служба.
    // Код записи — не вопрос, а адрес. Служба по нему тоже что-то найдёт, но искать смысл в
    // «H-WBD-004» бессмысленно: запись есть в снимке, открываем сразу и без ожидания.
    const code=(q.trim().match(/^[A-ZА-Я]-[A-Z]{2,4}-\d{2,4}$/i)||[])[0];
    if(code&&byCode[code.toUpperCase()]){
      const record=byCode[code.toUpperCase()];
      box.innerHTML=record.k==="project"?projectCard(code.toUpperCase()):recordCard(code.toUpperCase());
      if(found)found.textContent="запись по коду";
      if(call)call.innerHTML=`<p class="mcp-call is-local">Открыто по коду из локального снимка: искать смысл в коде записи незачем.</p>`;
      bindResults(box);scrollToResults();return;
    }
    const map=forceAsk.has(q.trim())?"":isBroad(q)?mapPage(q):"";
    if(map){
      box.innerHTML=map+`<div class="map-records" id="map-records"><p class="map-records-wait">Ищу записи по этой теме…</p></div>`;
      if(found)found.textContent="карта темы";
      // Службу мы здесь не звали, поэтому и вызов показывать нельзя: строка вызова на этой
      // странице обещает «то же, что делает агент», и обманывать в ней нечестно.
      // Карта собирается локально, но записи под ней ищет служба — значит вызов есть, и
      // показывать надо его, а не только пояснение про карту. Иначе строка вызова обещает
      // «то же, что делает агент» и при этом скрывает настоящий вызов.
      if(call)call.innerHTML=`<p class="mcp-call is-local">Сверху карта базы: она собрана локально из дерева разделов. Записи под ней ищет служба этим вызовом.</p>`
        +callLine(q.trim());
      bindResults(box);scrollToResults();
      fillMapRecords(q,seq);
      return;
    }
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
        :`<p class="mcp-empty">По снимку ничего не нашлось, и это ожидаемо: снимок ищет словами, а не по смыслу. Поднимите живой поиск, и та же строка уйдёт в службу так, как её отправляет агент.</p>`;
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
      liveOk=null;syncLiveBadge();
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
  const treeFolders={};for(const f of tree.folders||[])treeFolders[f.f]=f;
  const treeSections={};for(const x of tree.sections||[])treeSections[x.name]=x;
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
  const searchIndex=(window.LabSearch&&window.LAB_TREE)
    ? window.LabSearch.build({tree,base,lib}) : null;

  // Кто есть кто в выдаче индекса: узел это то, чем начинают, запись — то, чем отвечают.
  const NODE_KINDS=new Set(["section","folder","subtopic","direction","theme","project"]);

  function mapMatches(q){
    if(searchIndex)return mapMatchesRanked(q);
    return mapMatchesLegacy(q);
  }

  // Узлы из общего ранжирования. Сюда попадает то, что индекс сам поставил высоко, а не то,
  // что совпало по подстроке в названии: раньше именно это давало «Отбор студентов в
  // лабораторию» на запрос про дообучение.
  function mapMatchesRanked(q){
    const found=searchIndex.search(q,60);
    const folders=[],subtopics=[],directions=[],projects=[],themes=[];
    const byFolder={};for(const f of tree.folders||[])byFolder[f.f]=f;
    for(const item of found){
      if(!NODE_KINDS.has(item.kind))continue;
      const hit=item.score;
      if(item.kind==="folder"&&byFolder[item.id])folders.push({node:byFolder[item.id],hit});
      else if(item.kind==="subtopic"){
        const [folder,slug]=String(item.id).split("|");
        const parent=byFolder[folder];
        const topic=(parent?.sub||[]).find(t=>t.slug===slug);
        if(parent&&topic)subtopics.push({folder:parent,node:topic,hit});
      }
      else if(item.kind==="direction"){
        const node=(tree.directions||[]).find(d=>d.slug===item.id);
        if(node)directions.push({node,hit});
      }
      else if(item.kind==="project"||item.kind==="theme"){
        const node=byCode[item.id];
        if(node)(item.kind==="theme"?themes:projects).push({node,hit});
      }
    }
    // Двадцать восемь узлов на один запрос человек не читает: после первой трети идёт хвост,
    // где оценка вдвое ниже лучшей и узел уже про другое. Режем по доле от лучшего, как и
    // записи, и только потом применяем потолки по родам.
    const all=[...folders,...subtopics,...directions,...projects,...themes];
    const best=all.reduce((n,x)=>Math.max(n,x.hit),0);
    const keep=(xs,n)=>{const strong=xs.filter(x=>x.hit>=best*0.45);
      return (strong.length?strong:xs.slice(0,1)).slice(0,n)};
    return {folders:keep(folders,4),subtopics:keep(subtopics,6),
            directions:keep(directions,3),projects:keep(projects,5),
            themes:keep(themes,4)};
  }

  function mapMatchesLegacy(q){
    const folders=[],subtopics=[],directions=[],projects=[];
    for(const f of tree.folders||[]){
      const hit=Math.max(nodeHit(f.f,q),nodeHit(f.f.split("/").pop().replace(/_/g," "),q),
                         nodeHitDeep(f.f,f.a,q));
      if(hit)folders.push({node:f,hit});
      for(const t of f.sub||[]){
        const th=Math.max(nodeHit(t.t,q),nodeHit(t.slug.replace(/-/g," "),q),
                          nodeHitDeep(t.t,t.a,q));
        if(th)subtopics.push({folder:f,node:t,hit:th});
      }
    }
    for(const d of tree.directions||[]){
      const hit=Math.max(nodeHit(d.t,q),nodeHit(d.slug.replace(/-/g," "),q),
                         nodeHitDeep(d.t,d.a,q));
      if(hit)directions.push({node:d,hit});
    }
    const themes=[];
    for(const r of base.records||[]){
      if(r.k!=="project")continue;
      // У темы в базе вместо описания машинная склейка вида «Тема объединяет 3 работ…», и
      // искать по ней бессмысленно: «Отбор студентов в лабораторию» всплывал на запрос про
      // дообучение. Для темы берём написанную аннотацию, для проекта — его сводку, она живая.
      const text=isTheme(r)?(themeAbstract[r.code]||""):(r.s||"");
      const hit=Math.max(nodeHit(r.t,q),nodeHit(r.code,q),nodeHit(r.pn,q),
                         nodeHitDeep(r.t,text,q));
      if(!hit)continue;
      // Тема и проект лежат в одной таблице, но это разные вещи: тема объединяет проекты,
      // а работу ведут в проекте. На витрине они не должны стоять в одном списке.
      (isTheme(r)?themes:projects).push({node:r,hit});
    }
    const rank=(a,b)=>b.hit-a.hit;
    return {folders:folders.sort(rank).slice(0,6),subtopics:subtopics.sort(rank).slice(0,8),
            directions:directions.sort(rank).slice(0,4),projects:projects.sort(rank).slice(0,8),
            themes:themes.sort(rank).slice(0,6)};
  }

  // Широкий ли запрос. Вопрос («нужен ли прогрев», «когда выигрывает Muon») спрашивают у
  // службы: там ответ — утверждение. Имя темы («Muon», «lora_base») спрашивают у карты.
  // Границу слова \b в JS определяет \w, то есть [A-Za-z0-9_], и кириллица в неё не входит.
  // Поэтому регулярка с \b(ли|почему|…)\b на русский вопрос не срабатывала вообще, и
  // «нужен ли прогрев» уходило в карту темы вместо службы. Сравниваем по словам, а не
  // регуляркой с границами.
  //
  // Само правило «карта или записи» живёт в ядре поиска (search-core.js, wantsMap): там же,
  // где ранжирование, и там же, где его проверяет набор tests/test_routing.mjs. Здесь была
  // вторая копия правила, и она разошлась с первой — на прямой вопрос витрина отвечала
  // оглавлением.
  const ASK_WORDS=LabSearch.ASK_WORDS;
  function isBroad(q){
    if(!q.trim())return false;
    // Индекс строится из тех же трёх файлов, что и страница, и не строится только если
    // один из них не загрузился. Тогда узлы ищутся вхождением подстроки, как раньше.
    if(!searchIndex){
      const words=(q.toLowerCase().match(/[a-zа-яё0-9_-]+/g)||[]);
      if(words.some(w=>MAP_WORDS.has(w)))return true;
      if(q.includes("?")||words.some(w=>ASK_WORDS.has(w))||words.length>4)return false;
      const m=mapMatchesLegacy(q);
      return !!(m.folders.length||m.subtopics.length||m.directions.length||m.projects.length);
    }
    return LabSearch.wantsMap(q,searchIndex);
  }

  function mapPage(q){
    const m=mapMatches(q);
    const parts=[];
    // Владелец: «где мой список тем по мюону? че за хуйня вылезает?» — на запрос «muon»
    // подраздел библиотеки с шестью подтемами стоял ниже шести проектов, за тремя тысячами
    // пикселей прокрутки, и его просто не было видно.
    //
    // Раньше своя работа шла первой всегда. Но «muon» — точное имя подраздела и лишь
    // вхождение в названия проектов, а точное совпадение сильнее. Теперь порядок задаёт
    // сила совпадения, и только при равной силе проекты идут первыми.
    const strength=xs=>xs.reduce((n,x)=>Math.max(n,x.hit),0);
    const groups=[];
    if(m.projects.length)groups.push({rank:strength(m.projects),own:0,
      html:`<section class="map-group is-lead"><p class="overline">Проекты лаборатории</p>${
        m.projects.map(({node})=>projectTeaser(node)).join("")}</section>`});
    if(m.themes.length)groups.push({rank:strength(m.themes),own:1,
      html:`<section class="map-group"><p class="overline">Темы лаборатории</p>${
        m.themes.map(({node})=>themeTeaser(node)).join("")}</section>`});
    if(m.folders.length||m.subtopics.length){
      const rows=m.folders.map(({node})=>{
        const st=folderStats(node.f);
        const subs=(node.sub||[]).map(t=>
          `<button type="button" data-open-subtopic="${esc(node.f)}|${esc(t.slug)}">${esc(t.t)}<span>${esc(String(t.p.length))}</span></button>`).join("");
        return `<article class="map-node">
          <header><span class="map-node-kind">подраздел библиотеки</span>
            <code>${esc(node.f)}</code>
            <span class="map-node-count">${esc(String(st.papers))} статей · ${esc(String(st.claims))} утверждений</span></header>
          <p class="map-node-abstract">${esc(unmark(node.a||""))}</p>
          ${subs?`<div class="map-node-subs"><b>Подтемы</b>${subs}</div>`:""}
          <div class="map-node-go"><button type="button" data-open-folder="${esc(node.f)}">Открыть все статьи подраздела →</button></div>
        </article>`}).join("");
      const loose=m.subtopics.filter(x=>!m.folders.some(f=>f.node.f===x.folder.f)).map(({folder,node})=>
        `<article class="map-node is-sub">
          <header><span class="map-node-kind">подтема</span>
            <code>${esc(folder.f)}</code>
            <span class="map-node-count">${esc(String(node.p.length))} статей</span></header>
          <h3>${esc(node.t)}</h3>
          <p class="map-node-abstract">${esc(unmark(node.a||""))}</p>
          <div class="map-node-go"><button type="button" data-open-subtopic="${esc(folder.f)}|${esc(node.slug)}">Открыть подтему →</button></div>
        </article>`).join("");
      groups.push({rank:Math.max(strength(m.folders),strength(m.subtopics)),own:2,
        html:`<section class="map-group"><p class="overline">Разделы библиотеки</p>${rows}${loose}</section>`});
    }
    if(m.directions.length){
      // Направления раньше приклеивались после всех групп и в сортировке не участвовали:
      // на прямой вопрос «какие направления есть в лаборатории» они оказывались последними,
      // ниже тем и разделов библиотеки.
      groups.push({rank:strength(m.directions),own:3,
        html:`<section class="map-group"><p class="overline">Научные направления лаборатории</p>${
        m.directions.map(({node})=>{
          const projects=(base.records||[]).filter(r=>r.k==="project"&&
            (r.f||[]).some(f=>f[0]==="направление"&&(node.raw||[]).includes(f[1])));
          const list=projects.slice(0,10).map(p=>
            `<button type="button" data-open-record="${esc(p.code)}">${esc(p.t)}<span>${esc(String((p.hy||[]).length))}</span></button>`).join("");
          return `<article class="map-node is-dir">
            <header><span class="map-node-kind">направление</span>
              <span class="map-node-count">${esc(String(projects.length))} проектов</span></header>
            <h3>${esc(node.t)}</h3>
            <p class="map-node-abstract">${esc(unmark(node.a||""))}</p>
            ${list?`<div class="map-node-subs"><b>Проекты</b>${list}</div>`:""}
          </article>`}).join("")}</section>`});
    }
    // Сильное совпадение выше слабого: «muon» — точное имя подраздела и лишь вхождение в
    // названия проектов. При равной силе своя работа идёт первой.
    groups.sort((a,b)=>b.rank-a.rank||a.own-b.own);
    const body=[...groups.map(g=>g.html),...parts].join("");
    // Если по теме в карте ничего нет, отвечать «в карте базы такой темы нет» — тупик:
    // человек спросил, а витрина не поискала. Возвращаем пусто, и вызывающий уходит в поиск.
    if(!body)return "";
    return `<div class="map-answer">
      <div class="map-head">
        <p class="map-lead"><b>«${esc(q.trim())}»</b> — это тема, а не вопрос, поэтому вот что по ней есть в базе. Начните с аннотации, а за отдельными утверждениями идите внутрь.</p>
        <button class="map-force" type="button" data-force-ask="${esc(q.trim())}">Всё равно спросить утверждения у службы →</button>
      </div>
      ${mapIndex(m,q)}
      ${body}</div>`;
  }

  // Оглавление ответа. Владелец искал «muon» и не нашёл список подтем: подраздел с шестью
  // подтемами стоял ниже шести проектов, за 3300 пикселями прокрутки. Оглавление ставит то,
  // ради чего задан широкий запрос, на первый экран: сколько чего нашлось и сразу — сами
  // подтемы, потому что это и есть ответ на вопрос «что тут есть по этой теме».
  function mapIndex(m,q=""){
    const counts=[];
    if(m.projects.length)counts.push(`<b>${esc(String(m.projects.length))}</b> ${esc(plural(m.projects.length,["проект","проекта","проектов"]))}`);
    if(m.themes.length)counts.push(`<b>${esc(String(m.themes.length))}</b> ${esc(plural(m.themes.length,["тема","темы","тем"]))}`);
    if(m.folders.length)counts.push(`<b>${esc(String(m.folders.length))}</b> ${esc(plural(m.folders.length,["подраздел","подраздела","подразделов"]))}`);
    if(m.directions.length)counts.push(`<b>${esc(String(m.directions.length))}</b> ${esc(plural(m.directions.length,["направление","направления","направлений"]))}`);
    // Подтемы найденных подразделов плюс подтемы, совпавшие сами: это тот самый список,
    // который человек и хочет увидеть по имени темы.
    // Подтемы найденного подраздела попадают сюда всегда: выиграл сам подраздел, а это его
    // содержимое. А подтема, совпавшая сама по себе, обязана быть сопоставима с победителем.
    // Замер: на настоящих тематических запросах («muon», «LoRA», «scaling laws») верхняя
    // подтема держит от 0.35 до 0.82 балла лучшего узла. На запросе «безградиентное
    // предобучение языковых моделей» проект ZO Pretraining набирает 332, а подтема «Muon за
    // пределами предобучения LLM» — 50, то есть 0.15, и всё равно стояла над проектом:
    // оглавление поднимало подтемы безусловно. Человек спрашивал про ZO и первым читал Muon.
    // Порядок здесь такой же, как в самой выдаче, и порог общий. Раньше сначала шли подтемы
    // найденных подразделов — все и без разбора, — а уже за ними те, что совпали сами.
    // На запросе «какие направления есть в лаборатории» это выводило наверх подтемы про
    // ZO, потому что в одной из них есть «выбор направлений возмущения»: подраздел попал в
    // шестьдесят найденных узлов, и все его подтемы поднялись выше настоящих направлений.
    // На «статьи про слияние адаптеров» так же поднимались четыре подтемы Reference/rndm_papers
    // вместо подтемы «Слияние адаптеров и геометрия обновлений», которая и стояла первой.
    const best=Math.max(0,...[m.projects,m.themes,m.folders,m.subtopics,m.directions]
      .flat().map(x=>x.hit||0));
    const seen=new Set(),topics=[];
    const add=(folder,topic,hit)=>{const key=folder+"|"+topic.slug;
      if(seen.has(key)||(best&&(hit||0)<best*0.3))return;
      seen.add(key);topics.push({folder,topic,hit:hit||0})};
    // Сначала те, что совпали сами: у них свой балл, и он выше балла папки. Если добавлять
    // папки первыми, подтема «Слияние адаптеров и геометрия обновлений» получала 122 балла
    // своей папки вместо собственных 167 и уходила вниз под чужие подтемы.
    for(const {folder,node,hit} of m.subtopics)add(folder.f,node,hit);
    // Затем содержимое найденных подразделов: выиграл подраздел, балл наследуется от него.
    for(const {node,hit} of m.folders)for(const t of node.sub||[])add(node.f,t,hit);
    topics.sort((a,b)=>b.hit-a.hit);
    if(!counts.length&&!topics.length)return "";
    return `<div class="map-index">
      ${counts.length?`<p class="map-index-counts">${counts.join(" · ")}</p>`:""}
      ${topics.length?`<div class="map-index-topics">
        <p class="overline">Темы по запросу${
          new Set(topics.map(t=>t.folder)).size===1?` · ${esc(topics[0].folder)}`:""}</p>
        <ol>${topics.map(({folder,topic})=>`<li><button type="button" data-open-subtopic="${esc(folder)}|${esc(topic.slug)}">
          <strong>${esc(topic.t)}</strong><span>${
          new Set(topics.map(t=>t.folder)).size===1?"":esc(folder.split("/").pop().replace(/_/g," "))+" · "
        }${esc(String(topic.p.length))} ${esc(plural(topic.p.length,["статья","статьи","статей"]))}</span>
          <em>${esc(shorten(unmark(topic.a||""),150))}</em></button></li>`).join("")}</ol>
      </div>`:""}
    </div>`;
  }

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
    source:["источник","источника","источников"],
    source_ref:["источник","источника","источников"],
    paper_chunk:["раздел статьи","раздела статьи","разделов статей"]};
  function plural(n,forms){
    if(!forms)return "";
    const a=Math.abs(n)%100,b=a%10;
    if(a>10&&a<20)return forms[2];
    if(b>1&&b<5)return forms[1];
    if(b===1)return forms[0];
    return forms[2];
  }
  const ANSWER_ORDER=["hypothesis","paper_claim","evidence","experiment","derivation","decision","project"];
  const ANSWER_SOURCES=6;

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
    if(x.entity_type==="paper_claim"){
      const e=x.extra||{};
      const whole=String(x.title||""),cut=whole.indexOf(" — ");
      return {key:"paper:"+(shortId(e.paper_id)||whole),kind:"paper",id:shortId(e.paper_id),
              title:cut>0?whole.slice(0,cut):whole,folder:e.library_folder||""};
    }
    const snap=snapById[String(x.entity_id||"").slice(0,8)];
    if(snap?.pj)return {key:"project:"+snap.pj,kind:"project",id:snap.pj,
                        title:snap.pn||snap.pj,folder:""};
    return {key:"loose",kind:"loose",id:"",title:"Записи без проекта",folder:""};
  }

  // Служба отдаёт двадцать записей, но отвечают на вопрос обычно первые пять-восемь: дальше
  // идёт хвост, где оценка кросс-энкодера падает вдвое и запись уже про другое. Владелец,
  // увидев такой хвост: «че за хуйня вылезает?» — и это справедливо, потому что на запрос
  // про прогрев в ответе стояло «Метод устойчив к T/K».
  //
  // Поэтому ответ режется по самой оценке службы: то, что слабее половины лучшего, уходит
  // под раскрытие. Порог относительный, потому что абсолютные значения у разных вопросов
  // разные: на «прогрев» лучший 0.42, на «Muon» 0.47.
  function splitByScore(items){
    const scored=items.filter(x=>typeof x.score==="number");
    if(scored.length<4)return [items,[]];
    const best=Math.max(...scored.map(x=>x.score));
    const floor=best*0.5;
    const strong=items.filter(x=>typeof x.score!=="number"||x.score>=floor);
    // Если порог срезал почти всё, значит выдача ровная и резать нечего.
    if(strong.length<3)return [items,[]];
    return [strong,items.filter(x=>!strong.includes(x))];
  }

  function answerPage(items,q){
    const [items_,weak]=splitByScore(items);
    items=items_;
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
    const theirs=(by.paper_claim||[]).length;
    const gist=ours&&theirs?`Отвечает и своя работа, и разобранные статьи.`
      :ours?`Отвечает своя работа: записи из прогонов и измерений.`
      :theirs?`В своей работе ответа нет — отвечают разобранные статьи.`:"";
    const head=`<div class="answer-head"><p class="answer-tally">${tally}</p>${gist?`<p class="answer-gist">${esc(gist)}</p>`:""}</div>`;
    // Владелец: «проекты лаборатории… должны выделяться и быть важными». При прочих равных
    // проект встаёт выше статьи, дальше — у кого больше попаданий, дальше — порядок службы.
    groups.sort((a,b)=>
      (a.src.kind==="project"?0:1)-(b.src.kind==="project"?0:1)
      || b.items.length-a.items.length
      || a.best-b.best);
    const cards=groups.map(g=>sourceGroup(g,q));
    // Хвост показываем отдельно и честно называем: это то, что служба поставила заметно
    // ниже. Прятать его совсем нельзя — иногда нужное лежит именно там.
    const weakBlock=weak.length
      ? `<details class="answer-weak"><summary>Ещё ${esc(String(weak.length))} ${esc(plural(weak.length,["запись","записи","записей"]))}, которые служба поставила заметно ниже</summary>
         <ol class="src-claims">${weak.map((x,i)=>claimRow(x,q,items.length+i+1)).join("")}</ol></details>`
      : "";
    if(cards.length<=ANSWER_SOURCES)return head+cards.join("")+weakBlock;
    return head+cards.slice(0,ANSWER_SOURCES).join("")+
      `<details class="answer-rest"><summary>Ещё ${esc(String(cards.length-ANSWER_SOURCES))} источников по порядку службы</summary>${cards.slice(ANSWER_SOURCES).join("")}</details>`+weakBlock;
  }

  // Источник и его утверждения. Аннотация стоит сразу: владелец «сделай так, чтобы в
  // выпадающем проекте (статье) писалось еще и аннотация его».
  function sourceGroup(group,q){
    const {src,items}=group;
    const snap=src.kind==="project"?byCode[src.id]:null;
    const paper=src.kind==="paper"?papersById[src.id]:null;
    const abstract=unmark(src.kind==="project"?(snap?.s||""):shorten(paper?.sr||paper?.s||paper?.ab||"",320));
    const who=snap?.who||{};
    const team=[...(who.leads||[]),...(who.members||[])];
    const meta=src.kind==="project"
      ? [snap?.st,(snap?.f||[]).find(f=>f[0]==="направление")?.[1]].filter(Boolean).join(" · ")
      : [paper?.au?authorLine(paper.au):"",paper?.y,src.folder].filter(Boolean).join(" · ");
    const open=src.kind==="project"
      ? `<button type="button" data-open-record="${esc(src.id)}">Открыть проект: аннотация, все утверждения, терминология →</button>`
      : src.id?`<button type="button" data-open-paper="${esc(src.id)}">Открыть статью: аннотация и все её утверждения →</button>`:"";
    return `<article class="src-group is-${esc(src.kind)}">
      <header>
        <span class="src-kind">${esc(src.kind==="project"?"проект лаборатории":src.kind==="paper"?"статья":"без источника")}</span>
        ${src.kind==="project"&&src.id?`<code>${esc(src.id)}</code>`:""}
        <span class="src-count">${esc(String(items.length))} ${esc(plural(items.length,["утверждение по запросу","утверждения по запросу","утверждений по запросу"]))}</span>
      </header>
      <h3>${esc(src.title||"")}</h3>
      ${meta?`<p class="src-meta">${esc(meta)}</p>`:""}
      ${abstract?`<p class="src-abstract">${esc(abstract)}</p>`:""}
      ${team.length?`<p class="src-team"><b>${esc(who.leads?.length?"Ведёт":"Работали")}</b> ${esc((who.leads||[]).join(", "))}${who.members?.length?` · <b>с</b> ${esc((who.members||[]).join(", "))}`:""}</p>`:""}
      <ol class="src-claims">${items.map(({item,place})=>claimRow(item,q,place)).join("")}</ol>
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
    return `<details class="mcp-browse" id="mcp-browse"><summary>Смотреть по разделам, не спрашивая <span>${esc(String((tree.directions||[]).length))} направлений · ${esc(String((tree.sections||[]).length))} разделов · ${esc(String((lib.folders||[]).length))} подразделов · ${esc(String(subtopics))} подтем</span></summary>
      <section><b>Направления лаборатории</b><p>Своя работа: направление объединяет темы, тема — проекты, у проекта свои утверждения, состав и терминология.</p><div class="browse-tree">${dirs}</div></section>
      <section><b>Разделы библиотеки</b><p>Чужие работы в вашей же раскладке. Большие подразделы разбиты на подтемы, у каждого узла аннотация.</p><div class="browse-tree">${sections}</div></section>
      <section><b>Термины</b><p>Поперечная ось: сколько раз термин встречается в утверждениях статей, наших утверждениях и измерениях.</p><div class="mcp-chips is-terms">${terms}</div></section></details>`;
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
        <ol>${xs.map(c=>`<li class="${c.v?"is-verified":"is-unverified"}"><p>${mark(c.s,q)}</p>${c.q&&c.q!==c.s?`<blockquote>${esc(c.q.slice(0,300))}</blockquote>`:""}<small>${c.v?"цитата сверена с текстом":"цитата не сверена"}</small></li>`).join("")}</ol></section>`;
    }).join("");
    const body=p.sr||p.ab||p.s||"";
    return `<article class="paper-page">
      <header><span class="base-kind">статья</span>${p.f?`<button class="base-folder" type="button" data-open-folder="${esc(p.f)}">${esc(p.f)}</button>`:""}${p.y?`<span class="base-status">${esc(String(p.y))}</span>`:""}</header>
      <h2>${esc(p.t)}</h2>
      <p class="paper-authors">${esc(p.au||"")}${p.v?` · ${esc(p.v)}`:""}</p>
      ${body?`<p class="paper-abstract">${mark(body,q)}</p>`:""}
      <div class="paper-counts"><span>утверждений <b>${esc(String((p.c||[]).length))}</b></span><span>разделов <b>${esc(String(p.ns??p.nc??0))}</b></span>${p.key?`<span>ключ <b>${esc(p.key)}</b></span>`:""}</div>
      <div class="claim-links">${p.ax?`<a href="https://arxiv.org/abs/${esc(p.ax)}" target="_blank" rel="noopener">arXiv ${esc(p.ax)} ↗</a>`:""}<button type="button" data-mcp-home>← к поиску</button></div>
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
    try{const r=await fetch(`${PROXY}/tools`,{cache:"no-store"});agentTools=(await r.json()).tools||[]}
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
      const r=await fetch(url,{cache:"no-store"});
      const data=await r.json();
      if(out)out.textContent=JSON.stringify(data,null,1).slice(0,20000);
    }catch(error){if(out)out.textContent=String(error)}
  }
  function syncLiveBadge(){
    const badge=$("mcp-live-badge");if(!badge)return;
    badge.className=`mcp-live-badge ${liveOk?"is-live":"is-snapshot"}`;
    // В публичной сборке живой службы нет и быть не может: там выдуманная лаборатория.
    // Предлагать поднять прокси к чужому серверу нечестно, поэтому текст другой.
    badge.innerHTML=liveOk
      ? `<b>живая служба</b><span>тот же вызов, что делают агенты лаборатории: lab-knowledge на brain_lab, порядок задаёт кросс-энкодер</span>`
      : demo
      ? `<b>показательная сборка</b><span>${esc(demo.lab||"выдуманная лаборатория")}: одно направление, один проект, восемь статей. Данные выдуманы, живой службы здесь нет. У себя ставите ту же витрину на свою базу и получаете эту страницу на своих записях.</span>`
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
    return `<section class="tally" aria-label="Что лежит в общей базе">
      <div class="tally-row">
        <div class="is-their"><b>${esc(String((lib.papers||[]).length))}</b><span>статей разобрано</span></div>
        <div class="is-their"><b>${esc(String(claims))}</b><span>утверждений из статей</span></div>
        <div class="is-our"><b>${esc(String(hyp.length))}</b><span>наших утверждений</span></div>
        <div class="is-our"><b>${esc(String(count("experiment")))}</b><span>прогонов</span></div>
        <div class="is-our"><b>${esc(String(count("evidence")))}</b><span>измерений</span></div>
        <div class="is-our"><b>${esc(String(count("derivation")))}</b><span>доказательств</span></div>
      </div>
      <p class="tally-note"><b class="is-our">${esc(String(both))}</b> утверждений закрыты и выкладкой, и числами.
        Всё, что ниже, читает ту же базу, что и агенты лаборатории.</p>
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

  // ============ Три входа ============
  // Владелец: «разные случаи пользования этим MCP: от поиска отдельной гипотезы до изучения
  // какого-то раздела оптимизации». Каждый вход показывает настоящее содержимое базы, а не
  // пустую форму: область идёт со своим объёмом, коды записей взяты из снимка.
  // Публичная сборка витрины показывает выдуманную лабораторию, поэтому вопросы-примеры и
  // код записи в форме берутся из её данных: иначе демонстрация предлагает спросить про
  // Muon у базы, в которой Muon нет, и выглядит сломанной.
  const demo=window.LAB_DEMO||null;
  const WAY_QUESTIONS=demo?.hints||["нужен ли прогрев и когда он помогает","когда выигрывает Muon",
    "что мы знаем про квантование по кривизне","где метод не сработал"];
  const CODE_EXAMPLE=demo?.code||"H-WBD-001";
  function waysBlock(){
    // Здесь стояли первые семь подпапок по алфавиту — то есть случайная выборка одного
    // уровня. Владелец: «надо в больших разделах добавлять ещё разбиение, чтобы было
    // читаемо». Теперь это разделы верхнего уровня: раздел → подразделы → подтемы.
    const areas=(tree.sections||[]).map(sec=>{
      const stats=sec.folders.reduce((acc,f)=>{const st=folderStats(f);
        return {papers:acc.papers+st.papers,claims:acc.claims+st.claims}},{papers:0,claims:0});
      return {name:sec.name,n:stats.papers,claims:stats.claims,folders:sec.folders.length};
    }).sort((a,b)=>b.n-a.n);
    const most=Math.max(1,...areas.map(a=>a.n));
    const recent=(base.records||[]).filter(r=>r.k==="hypothesis"&&r.code&&r.sup==="proof_and_numbers").slice(0,4);
    return `<div class="ways">
      <section class="way"><span>Один вопрос</span>
        <h3>Спросить словами</h3>
        <p>Служба считает вектор вопроса и переранжирует ответ кросс-энкодером. Отвечают утверждения и измерения, а не список статей. Ответ идёт 6-14 секунд, поэтому вопрос отправляется по «Спросить», а не на каждую букву.</p>
        <div class="way-body">
          <form class="way-form" id="mcp-search-form" role="search">
            <label class="sr-only" for="mcp-search-input">Вопрос к общей базе</label>
            <input id="mcp-search-input" type="search" autocomplete="off" placeholder="нужен ли прогрев">
            <button type="submit">Спросить</button></form>
          <div class="way-examples">${WAY_QUESTIONS.map(q=>`<button type="button" data-way-ask="${esc(q)}">${esc(q)}</button>`).join("")}</div>
        </div></section>

      <section class="way"><span>Целая область</span>
        <h3>Изучить раздел</h3>
        <p>У раздела есть аннотация, внутри подразделы, у больших подразделов — подтемы. Так до статьи можно дойти, не спрашивая, а у каждой статьи её разобранные утверждения с дословными цитатами.</p>
        <div class="way-body"><div class="way-areas">
          ${areas.map(a=>`<button class="way-area" type="button" data-open-section="${esc(a.name)}">
            <span>${esc(a.name)}</span><i style="width:${Math.round(a.n/most*100)}%"></i><em>${esc(String(a.n))}</em></button>`).join("")}
        </div></div></section>

      <section class="way"><span>Одна запись</span>
        <h3>Открыть по коду</h3>
        <p>У каждой записи есть код и постоянная ссылка. По ней видно все поля, чем утверждение закрыто и с чем связано в базе.</p>
        <div class="way-body">
          <form class="way-code" id="mcp-code-form">
            <label class="sr-only" for="mcp-code-input">Код записи</label>
            <input id="mcp-code-input" placeholder="${esc(CODE_EXAMPLE)}" autocomplete="off">
            <button type="submit">Открыть</button></form>
          <div class="way-recent">${recent.map(r=>`<button type="button" data-open-record="${esc(r.code)}"><code>${esc(r.code)}</code><span>${esc((r.t||"").slice(0,52))}</span></button>`).join("")}</div>
        </div></section></div>`;
  }
  function showMcpLive(navigate=true){
    const m=systemData.liveMcp;if(!m)return;
    if(navigate)updateHash("mcp-live");
    hidePrimaryViews();active("mcp-live");
    const view=$("mcp-live-view");
    view.hidden=false;
    view.innerHTML=`<div class="special-shell mcp-page">
      <header class="mcp-hero"><p>Живая служба · ${esc(m.verifiedAt)}</p><h1>Спросите общую базу</h1>
        <strong>Общая память лаборатории: что уже проверяли, чем это закончилось и на какие чужие работы опирались. Спросите словами, откройте целую область или одну запись по коду. Отвечает та же служба, которой пользуются агенты, и порядок задаёт кросс-энкодер, а не совпадение слов.</strong>
        ${sourceButtons(m.links)}</header>
      <div class="mcp-live-badge" id="mcp-live-badge"></div>
      ${tallyBlock()}
      ${waysBlock()}
      <output id="mcp-found" class="mcp-found"></output>
      <div id="mcp-call-line"></div>
      <div id="mcp-results"></div>
      ${browseBlock()}
      ${mcpPipeline()}
      <details class="for-agents" id="mcp-agent"><summary>Для агентов: те же 17 читающих вызовов службы</summary>
        <p>Человеку это не нужно: выше то же самое обычными словами. Ничего не меняют, писать со страницы нельзя.</p>
        <p class="agent-map">Карта базы, по которой построена навигация выше — разделы, подразделы, подтемы, направления и их аннотации — лежит рядом файлом: <code>docs/lab-atlas/data/atlas-tree.json</code>. Агенту она отвечает на тот же вопрос, что человеку: с чего начинать, если запрос широкий.</p>
        <div class="mcp-chips" id="mcp-agent-tools"></div>
        <form class="agent-form" id="mcp-agent-form">
          <label>вызов<input id="mcp-agent-name" value="list_themes" autocomplete="off"></label>
          <label>аргументы<input id="mcp-agent-args" value="{}" autocomplete="off"></label>
          <button type="submit">Вызвать</button></form>
        <pre class="agent-out" id="mcp-agent-out">Ответ появится здесь.</pre></details>
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
    $("mcp-code-form").onsubmit=e=>{e.preventDefault();
      const code=$("mcp-code-input").value.trim().toUpperCase(),box=$("mcp-results");
      if(!code)return;
      replaceHash(`mcp-live/${code}`);
      box.innerHTML=byCode[code]?.k==="project"?projectCard(code):recordCard(code);
      bindResults(box);
      window.scrollTo({top:Math.max(0,box.getBoundingClientRect().top+scrollY-150),behavior:"smooth"})};
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
    const deep=(location.hash.slice(1).split("/")[1]||"").trim();
    if(deep&&byCode[deep]){
      const box=$("mcp-results");
      box.innerHTML=byCode[deep].k==="project"?projectCard(deep):recordCard(deep);
      bindResults(box);
    }else runSearch("");
    liveHealth().then(()=>{syncLiveBadge();if(input.value.trim())runSearch(input.value)});
    window.scrollTo({top:0,behavior:"instant"});
    input.focus({preventScroll:true});
  }
  // ============ Примеры: шесть путей, а не шесть плиток ============
  // Шесть одинаковых прямоугольников с одним радиусом сообщали только «здесь шесть чего-то».
  // Но в самих заголовках уже стоит структура: «от найденной работы до проверенного
  // утверждения», «от разговора до решений». Это путь, и он читается как путь: откуда,
  // чем, и что остаётся в конце. Рода записи слева — то, что различает пути между собой,
  // поэтому нумерации нет: это не последовательность, а шесть независимых маршрутов.
  function showExamples(navigate=true){
    if(navigate)updateHash("examples");
    hidePrimaryViews();active("examples");
    const view=$("examples-view");view.hidden=false;
    const examples=systemData.examples||[];
    const splitTitle=t=>{
      const m=String(t).match(/^От\s+(.+?)\s+до\s+(.+)$/i);
      return m?[m[1],m[2]]:[null,t];
    };
    view.innerHTML=`<div class="special-shell examples-page">
      <header class="examples-head">
        <p class="overline">Выходы инструментов</p>
        <h1>Что остаётся после работы</h1>
        <p>Шесть путей через систему. У каждого видно, с чего он начинается, чем идёт и что остаётся в общей базе, когда он закончен.</p>
      </header>
      <ol class="paths">${examples.map(x=>{
        const [from,to]=splitTitle(x.title);
        // Куда ведёт строка, видно до нажатия: имя инструмента стоит в левой колонке рядом
        // с родом. Раньше там было пусто, а под каждым маршрутом висела своя кнопка
        // «Открыть инструмент» — шесть одинаковых кнопок подряд и ни одной подсказки, что
        // за ними. Владелец: «я бы везде убрал это как кнопки, надо встроить в дизайн,
        // чтобы было не так перегружено».
        const tool=byId[x.id]?.tools?.find(t=>t.id===x.tool);
        return `<li class="path"><div class="path-kind"><span>${esc(x.kind)}</span>
            ${tool?`<i>${esc(tool.title)}</i>`:""}</div>
          <div class="path-body">
            <h2${from?` class="is-journey"`:""}>${from?`<em>от ${esc(from)}</em>`:""}<b>${
              // Нажимается сам заголовок и вместе с ним вся строка: у маршрута одна цель,
              // и отдельная кнопка под текстом только повторяла её словами.
              ""}<button class="path-open" type="button" data-example-process="${esc(x.id)}"
              data-example-tool="${esc(x.tool||"")}">${from?`до ${esc(to)}`:esc(to)}</button></b></h2>
            <p>${esc(x.text)}</p>
            <p class="path-outcome">${esc(x.outcome)}</p>
          </div></li>`}).join("")}</ol></div>`;
    view.querySelectorAll("[data-example-process]").forEach(b=>b.onclick=()=>
      openProcess(b.dataset.exampleProcess,b.dataset.exampleTool));
    window.scrollTo({top:0,behavior:"instant"});
  }
  function active(v){document.querySelectorAll("[data-view]").forEach(b=>{const selected=b.dataset.view===v;b.classList.toggle("active",selected);b.setAttribute("aria-pressed",String(selected))});if(v==="mcp-live"||v==="examples")requestAnimationFrame(()=>{const heading=document.querySelector(`#${v==="mcp-live"?"mcp-live-view":"examples-view"} h1`);if(heading){heading.tabIndex=-1;heading.focus({preventScroll:true})}})}
  function openProcess(id,toolId,navigate=true){const p=byId[id];if(!p)return;if(toolId&&!p.tools?.some(t=>t.id===toolId)){toolId="";replaceHash(id)}if(navigate)updateHash(`${id}${toolId?`/${toolId}`:""}`);hidePrimaryViews();$("process-view").hidden=false;$("process-view").innerHTML=page(p);bind($("process-view"),p);bindGraphMap($("process-view"),p);active("none");window.scrollTo({top:0,behavior:"instant"});$("process-view").querySelector("h1")?.focus({preventScroll:true});if(toolId)setTimeout(()=>{
    const view=$("process-view"),node=view.querySelector(`[data-node="tool:${CSS.escape(toolId)}"]`);
    if(node){node.click();return}
    // На карте теперь только самое важное, но ссылка на любой инструмент обязана работать:
    // если его узла нет, раскрываем его пункт в досье и подводим к нему.
    const card=view.querySelector(`#tool-${CSS.escape(toolId)}`);
    if(card){card.open=true;card.scrollIntoView({behavior:"smooth",block:"start"});
      card.querySelector("summary")?.focus({preventScroll:true})}
  },50)}
function fitLoopMap(){const map=document.querySelector("#overview .loop-map");if(!map)return;
  // Ниже 1261 карта раскладывается в колонку средствами CSS, масштабировать нечего.
  if(innerWidth<821||innerWidth<=1260){map.style.removeProperty("--map-scale");
    map.style.removeProperty("margin-left");return}
  // Карта нарисована под 760 пикселей высоты. Свободное место — окно минус шапка, заголовок и
  // поля; берём реальную высоту заголовка, а не константы вёрстки, иначе замер разъедется при
  // первой же правке шрифта.
  // Меряем от реальной верхней кромки карты, а не от суммы констант: так масштаб получается
  // ровно под свободное место, и внизу не остаётся пустоты, а сверху ничего не срезается.
  map.style.setProperty("--map-scale","1");
  const top=map.getBoundingClientRect().top;
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
  function capabilityStory(c){const purpose=c.description_ru||c.description||"Подробный сценарий использования пока не описан.",special=String(c.what_is_special||"").split(/Связан с процессами:|Минимальная проверка:|Назначение:/)[0].trim(),plainSpecial=/ACL|provenance|типизирован|схем|entrypoint|ограниченной ответственностью/i.test(special)?"":special,contexts=arr(c.process_ids).map(id=>processNames[id]).filter(Boolean).slice(0,3),type=c.type||"возможность",action=humanCapabilityTitle(c),lowerPurpose=purpose.charAt(0).toLowerCase()+purpose.slice(1),after=type==="agent"?`Сможете поручить агенту конкретную задачу: ${lowerPurpose}`:type==="skill"?`Сможете попросить агента провести весь сценарий: ${lowerPurpose}`:type==="command"?`Сможете одним действием запустить процесс: ${lowerPurpose}`:type==="hook"?`Проверка будет срабатывать автоматически и остановит ошибочное действие до изменения проекта.`:type==="mcp-tool"?`Агенты с подходящими правами смогут ${action.charAt(0).toLowerCase()+action.slice(1)} через общую лабораторную систему.`:type==="documentation"?`Сможете быстро найти актуальный порядок действий и сверить свою настройку.`:type==="repository"?`Сможете использовать и обновлять лабораторные инструменты из одного версионированного источника.`:type==="service"?`Подключенные агенты и приложения получат эту возможность как общий сервис.`:`Сможете использовать эту возможность в своем рабочем процессе.`,categoryCapability=type==="agent"?"самостоятельно выполнить ограниченную задачу и вернуть результат для проверки":type==="skill"?"провести повторяемый рабочий сценарий от исходных данных до проверенного итога":type==="command"?"собрать несколько шагов работы в один управляемый запуск":type==="hook"?"автоматически проверить действие до того, как оно изменит проект":type==="mcp-tool"?"выполнить это действие через общую систему без ручного редактирования базы":type==="documentation"?"сверить порядок действий и ограничения по актуальному источнику":type==="repository"?"работать с версионированными исходниками и видеть историю изменений":type==="service"?"дать нескольким инструментам одну общую возможность и состояние":"использовать возможность в связанном рабочем процессе",rawOutputs=arr(c.outputs_ru||c.outputs).filter(x=>!/типизированный результат|квитанция записи|проверенный профильный артефакт|выводы специалиста или артефакт/i.test(x)),fallbackOutcome=type==="agent"?`Проверенный результат работы агента «${action}»`:type==="skill"?`Завершенный рабочий сценарий «${action}»`:type==="command"?`Результат процесса «${action}»`:type==="hook"?"Автоматическая проверка с понятным решением":type==="mcp-tool"?`Ответ или сохраненное изменение: «${action}»`:type==="documentation"?`Понятный порядок действий по теме «${action}»`:type==="repository"?"Доступ к версионированным исходникам":type==="service"?"Доступный ответ или сохраненное состояние сервиса":`Практический результат по задаче «${action}»`,outcomes=rawOutputs.length?rawOutputs.slice(0,3):[fallbackOutcome],capabilities=[purpose,categoryCapability,...(plainSpecial&&plainSpecial!==purpose?[plainSpecial]:[])];return {purpose,capabilities,useCases:contexts.length?contexts:[`когда требуется именно это действие в исследовательском процессе`],outcomes,after}}
  function capSources(c){const own=arr(c.github_urls);if(own.length)return own;const query=encodeURIComponent(c.name||c.source_path||"");return [{label:`Найти ${c.name||"исходник"} в repository`,url:`https://github.com/Vepricov/claude-brainlab/search?q=${query}&type=code`,canonical:true}]}
  function capDetails(c){const story=capabilityStory(c);return `<div class="search-group capability-dossier"><p class="section-label">${esc(capType(c.type))}</p><h2>${esc(humanCapabilityTitle(c))}</h2><p>${esc(story.purpose)}</p><div class="tool-value"><section class="tool-outcome"><b>После подключения</b><span>${esc(story.after)}</span>${story.outcomes.map(x=>`<span>${esc(x)}</span>`).join("")}</section>${focusList("Что позволяет сделать",story.capabilities.slice(0,4))}</div><details class="tool-mechanics"><summary>Условия и ограничения</summary><dl class="tool-spec">${spec("Что понадобится",c.inputs_ru||c.inputs)}${spec("Что проверить",c.quality_gates_ru||c.quality_gates)}${spec("Ограничения",c.known_limitations_ru||c.known_limitations)}</dl></details><div class="tool-links">${links(capSources(c))}</div></div>`}
  function showCapability(id){const c=(registry.capabilities||[]).find(x=>x.id===id);if(!c)return;$("search-input").value="";$("search-results").innerHTML=capDetails(c);if(!$("search-dialog").open)$("search-dialog").showModal();const heading=$("search-results").querySelector("h2");if(heading){heading.tabIndex=-1;heading.focus()}}
  function searchItems(){return [...all.map(p=>({kind:"Процесс",key:p.id,title:p.title,text:`${p.verb} ${p.purpose} ${arr(p.when).join(" ")} ${arr(p.outcomes).join(" ")}`,go:()=>openProcess(p.id)})),...all.flatMap(p=>(p.tools||[]).map(t=>{const story=toolStory(t);return {kind:"Инструмент",key:t.id,title:t.title,text:`${p.title} ${story.value} ${story.capabilities.join(" ")} ${story.useCases.join(" ")} ${story.outcomes.join(" ")}`,go:()=>openQuickTool(p.id,t.id)}})),...(registry.capabilities||[]).filter(c=>c.type!=="command").map(c=>({kind:"Полный реестр",key:c.name||c.id,title:humanCapabilityTitle(c),text:`${c.name||""} ${capabilityStory(c).purpose} ${arr(c.process_ids).join(" ")}`,go:()=>showCapability(c.id)}))].filter(x=>!`${x.title} ${x.text}`.toLowerCase().includes("dykaf"))}
  const searchExamples=["разобрать созвон","найти статьи про метод","запустить эксперимент через Hermes","проверить цитату","добавить доступ к серверу","ответить рецензентам"];
  const searchConcepts=[{words:["созвон","разговор","встреч","аудио"],expand:["brain call","call-notes","transcript","решения","задачи"]},{words:["стать","литератур","paper","arxiv"],expand:["paper-search","paper-ingest","literature","zotero","alphaxiv"]},{words:["эксперимент","запуск","обучен","run"],expand:["hermes","experiment","monitoring","protocol","gpu"]},{words:["цитат","ссылк","bibtex"],expand:["citation-verification","paperclaim","references.bib","проверка статей"]},{words:["сервер","доступ","gpu","аккаунт"],expand:["server access bot","managed host","credentials","mlsub"]},{words:["rebuttal","реценз","ответ"],expand:["review-response","writing","paper-self-review"]}];
  const searchIntents={"разобрать созвон":["calls","brain-call","call-notes"],"найти статьи про метод":["literature","paper-search","paperscout"],"запустить эксперимент через Hermes":["experiments","hermes","hermes-experiment-launch"],"проверить цитату":["paper-qa","citation-verification","literature-reviewer"],"добавить доступ к серверу":["access","server-access-bot","hermes-add-user"],"ответить рецензентам":["writing","review-response","rebuttal-command","rebuttal-writer"]};
  function searchScore(item,query){const normalized=query.toLowerCase(),base=`${item.title} ${item.text}`.toLowerCase(),tokens=normalized.match(/[a-zа-яё0-9-]+/g)||[],expanded=[...tokens];for(const concept of searchConcepts)if(concept.words.some(word=>tokens.some(token=>token.includes(word))))expanded.push(...concept.expand);const preferred=searchIntents[normalized]||[],position=preferred.indexOf(item.key),intentBoost=position<0?0:120-position*12;return intentBoost+[...new Set(expanded)].reduce((score,token)=>score+(item.title.toLowerCase().includes(token)?8:base.includes(token)?2:0),0)}
  function renderSearch(q=""){const s=q.trim(),items=searchItems(),exact=items.filter(item=>item.key?.toLowerCase()===s.toLowerCase()),ranked=(exact.length?exact:items.map(item=>({...item,score:s?searchScore(item,s):0})).filter(item=>!s||item.score>0).sort((a,b)=>b.score-a.score||a.title.localeCompare(b.title,"ru")).slice(0,s?15:18)),groups=ranked.reduce((a,x)=>((a[x.kind]||=[]).push(x),a),{}),examples=`<div class="search-examples"><span>Попробуйте описать задачу</span>${searchExamples.map(x=>`<button data-search-example="${esc(x)}" type="button">${esc(x)}</button>`).join("")}</div>`;$("search-results").innerHTML=examples+(ranked.length?Object.entries(groups).map(([kind,xs])=>`<section class="search-group"><h3>${esc(kind)} <span>${xs.length}</span></h3>${xs.map((x,i)=>`<button class="search-item" data-key="${esc(kind)}-${i}" type="button"><strong>${esc(x.title)}</strong><p>${esc(x.text)}</p><i>Открыть →</i></button>`).join("")}</section>`).join(""):`<p class="empty-search">Совпадений нет. Опишите действие другими словами.</p>`);$("search-results").querySelectorAll("[data-search-example]").forEach(b=>b.onclick=()=>{$("search-input").value=b.dataset.searchExample;renderSearch(b.dataset.searchExample)});Object.entries(groups).forEach(([kind,xs])=>xs.forEach((x,i)=>{const b=document.querySelector(`[data-key="${CSS.escape(`${kind}-${i}`)}"]`);if(b)b.onclick=()=>{$("search-dialog").close();x.go()}}))}
  function openSearch(){renderSearch();if(!$("search-dialog").open)$("search-dialog").showModal();requestAnimationFrame(()=>$("search-input").focus())}


  renderLoop();renderToolkit();fitLoopMap();$("home").onclick=showOverview;$("search-open").onclick=openSearch;$("search-input").oninput=e=>renderSearch(e.target.value);document.querySelectorAll("[data-view]").forEach(b=>b.onclick=()=>b.dataset.view==="mcp-live"?showMcpLive():b.dataset.view==="examples"?showExamples():showOverview());document.addEventListener("keydown",e=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==="k"){e.preventDefault();openSearch()}});
  // Разделы слились, но ссылки на прежние адреса могли уже разойтись по чатам.
  const MOVED={"paper-qa":"writing","orchestration":"experiments","engineering":"experiments","access":"projects"};
  let [initial,initialTool]=location.hash.slice(1).split("/");if(MOVED[initial])initial=MOVED[initial];if(initial==="mcp-live")showMcpLive(false);else if(initial==="examples")showExamples(false);else if(initial==="surface")showSurface(initialTool,false);else if(byId[initial])openProcess(initial,initialTool);
  const routeLocation=()=>{let [route,tool]=location.hash.slice(1).split("/");if(MOVED[route])route=MOVED[route];if(route==="mcp-live")showMcpLive(false);else if(route==="examples")showExamples(false);else if(route==="surface")showSurface(tool,false);else if(byId[route])openProcess(route,tool,false);else showOverview(false)};
  window.addEventListener("popstate",routeLocation);

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
