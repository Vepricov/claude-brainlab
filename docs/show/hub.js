/* Первая страница «GitHub для идей». Данные — data/hub-data.js, их собирает
   scripts/export_tree_hub.py из дерева ~/brainlab (live.py пересобирает их на каждый коммит). */
(()=>{
  const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
  const num=n=>Number(n||0).toLocaleString(window.LAB_I18N?.language==="en"?"en-US":"ru-RU");
  const form=(n,f)=>{const a=Math.abs(n)%100,b=a%10;return a>10&&a<20?f[2]:b===1?f[0]:b>=2&&b<=4?f[1]:f[2]};
  const ago=t=>{
    const s=Math.max(0,Date.now()/1000-t),m=Math.round(s/60),h=Math.round(s/3600),d=Math.round(s/86400);
    if(m<60)return `${Math.max(m,1)} ${form(Math.max(m,1),["минуту","минуты","минут"])} назад`;
    if(h<24)return `${h} ${form(h,["час","часа","часов"])} назад`;
    if(d<30)return `${d} ${form(d,["день","дня","дней"])} назад`;
    return new Date(t*1000).toLocaleDateString(window.LAB_I18N?.language==="en"?"en-US":"ru-RU");
  };
  const initials=n=>String(n).split(/\s+/).filter(Boolean).slice(0,2).map(x=>x[0]).join("").toUpperCase();
  const hue=n=>[...String(n)].reduce((a,c)=>a+c.charCodeAt(0),0)%360;
  const ext=(url,cls,inner,tag="div")=>url?`<a class="${cls}" href="${esc(url)}" target="_blank" rel="noopener">${inner}</a>`:`<${tag} class="${cls}">${inner}</${tag}>`;
  const avatar=(n,agent)=>`<span class="hub-avatar${agent?" is-agent":""}" style="--h:${hue(n)}" title="${esc(n)}${agent?" · агент":""}">${agent?"✦":esc(initials(n))}</span>`;

  // У каждой пары «для кода → для идей» свой цвет, как у процессов на карте системы.
  const MAP=[
    ["проект","Работа","Один вопрос и всё, что о нём известно: идеи, проверки, документы, код.","#b9ff66","◫"],
    ["гипотеза","Утверждение","Проверяемая мысль и условие, при котором мы признаем её ложной. Условие пишется до проверки.","#8fb4ff","◇"],
    ["проверка","Прогон","Его страницу пишет сама программа, которая считала: настройки, числа, условия.","#ffb86b","▶"],
    ["предложение","Предложение","Новое знание входит предложением. Предлагают и люди, и агенты.","#c79bff","⑂"],
    ["автопроверка","Проверки","Программа сверяет каждое число с данными, судья-агент читает текст.","#5ee6d0","✓"],
    ["решение","Принимает человек","Знанием становится только то, что принял человек, ведущий работы.","#ff8fb1","⇲"],
    ["история","История","У каждого числа в статье есть адрес и автор. Опровергнутое не удаляется.","#ffe17a","↺"],
    ["одно окно","Всё под рукой","Вся база открывается в одном окне, и у каждого сотрудника она под рукой.","#7fd3ff","⇣"],
  ];
  const CHIPS=[["Агенты для всей команды","#b9ff66"],["База знаний, которая проверяет себя","#8fb4ff"],["Работа круглосуточно","#ffb86b"],
    ["Ноль выдуманных чисел","#5ee6d0"],["Люди и агенты в одной базе","#c79bff"]];
  const STATE_CLASS={"подтверждено":"ok","опровергнуто":"no","без вывода":"mid","проверяется":"run","черновик":"draft","завершён":"ok","упал":"no","идёт":"run"};
  const badge=s=>s?`<span class="hub-state is-${STATE_CLASS[s]||"draft"}">${esc(s)}</span>`:"";

  function tabPanel(tab,w,D,ev){
    if(tab==="claims")return `<ul class="hub-rows">${(D.claims||[]).map(c=>`<li><code>${esc(c.code)}</code><div><b>${esc(c.title)}</b><small>${num(c.runs)} прогонов · ${num(c.series)} серий${c.theory?` · ${num(c.theory)} выкладок`:""}</small></div>${badge(c.status)}</li>`).join("")}</ul>`;
    if(tab==="runs")return `<ul class="hub-rows">${(D.runs||[]).map(r=>`<li><code>${esc(r.code)}</code><div><b>${esc(r.title)}</b><small>под утверждением ${esc(r.claim)} · ${esc(r.updated.split("-").reverse().join("."))}</small></div>${badge(r.status)}</li>`).join("")}</ul><p class="hub-rows-more">Показаны последние 8 из ${num(w.runs)}. Каждую страницу записал код, который считал.</p>`;
    if(tab==="issues")return (D.issues||[]).length?`<ul class="hub-rows">${D.issues.map(x=>`<li><code>#${esc(x.n)}</code><div><b>${esc(x.title)}</b><small>${esc(String(x.who).replace(/\s*\(агент\)/,""))}${/агент/.test(x.who)?" · агент":""}</small></div><span class="hub-state is-run">открыта</span></li>`).join("")}</ul>`:`<p class="hub-rows-more">Открытых задач нет.</p>`;
    if(tab==="mrs")return (D.mrs||[]).length?`<ul class="hub-rows">${D.mrs.map(x=>`<li><code>!${esc(x.n)}</code><div><b>${esc(x.title)}</b><small>ждёт решения ведущего работы</small></div><span class="hub-state is-mid">на ревью</span></li>`).join("")}</ul><p class="hub-rows-more">Предложения агентов идут тем же путём, что и людей: проверки, затем решение человека.</p>`:`<p class="hub-rows-more">Все предложения рассмотрены.</p>`;
    return `<h3>${esc(w.title)}</h3><p>${esc(w.lead)}</p>
      <div class="hub-commit">${avatar(ev.who||"",ev.agent)}<b>${esc(ev.who||"")}</b><span>${esc(ev.s||"")}</span><time>${ev.t?esc(ago(ev.t)):""}</time></div>
      <ul class="hub-files">
        <li><span class="is-dir">claims/</span><em>${num(w.claims)} утверждений: что думаем и чем это опровергается</em></li>
        <li><span class="is-dir">paper/</span><em>рукопись, подключена к работе</em></li>
        <li><span class="is-dir">code/</span><em>код, которым считали</em></li>
        <li><span>README.md</span><em>о чём работа и кто её ведёт</em></li>
      </ul>
      <footer>${num(w.commits)} правок · ${num(w.merges)} принятых предложений · ${num(w.authors)} ${form(w.authors,["участник","участника","участников"])}</footer>`;
  }

  function hero(H,tab){
    const w=H.showcase||{},D=H.detail||{},ev=w.last||(H.events||[]).find(e=>e.repo===w.slug)||{};
    const tabs=[["overview","Обзор",""],["claims","Утверждения",w.claims],["runs","Прогоны",w.runs],["issues","Задачи",w.issues],["mrs","Предложения",w.mrs]];
    return `<section class="hub-hero">
      <div class="hub-hero-copy">
        <p class="hub-kicker">BRAIn Lab · МФТИ</p>
        <h1>База<br>знаний.</h1>
        <div class="hub-chips">${CHIPS.map(([c,col])=>`<span style="--c:${col}">${esc(c)}</span>`).join("")}</div>
        <p class="hub-lead">Самый частый вопрос в любой команде: «Мы это уже пробовали? И что вышло?» Обычно ответ лежит в чате, в чьей-то таблице или уходит вместе с сотрудником. А когда агенты за ночь делают десятки проверок, знание без порядка превращается в шум.</p>
        <p class="hub-lead hub-lead-strong">Мы построили базу, где каждая идея, проверка и число лежат с историей, подтверждением и автором. Она настраивается под задачи любой компании.</p>
        <div class="hub-actions">${H.gitlab?`<a class="hub-btn is-primary" href="${esc(H.gitlab)}" target="_blank" rel="noopener">Открыть GitLab лаборатории ↗</a>`:H.cta?`<a class="hub-btn is-primary" href="${esc(H.cta.href)}" target="_blank" rel="noopener">${esc(H.cta.label)}</a>`:""}<a class="hub-btn" href="#" data-hub-jump="chain">Как растёт знание ↓</a></div>
      </div>
      <div class="hub-window" data-hub-window>
        <header><i></i><i></i><i></i><span>brainlab / ${esc((w.path||"").split("/").slice(0,2).join(" / "))} / <b>${esc(w.slug)}</b></span></header>
        <nav role="tablist">${tabs.map(([id,l,n])=>`<button type="button" role="tab" data-hub-tab="${id}" class="${id===tab?"is-on":""}">${esc(l)}${n!==""?` <em>${num(n)}</em>`:""}</button>`).join("")}</nav>
        <div class="hub-window-body">${tabPanel(tab,w,D,ev)}</div>
      </div>
    </section>`;
  }

  function stats(T){
    const items=[[T.works,"работ","у каждой своя история","#b9ff66"],[T.commits,"правок","в работах лаборатории","#8fb4ff"],[T.merges,"предложений принято","каждое принял человек","#c79bff"],
      [T.runs,"прогонов","записаны кодом, не руками","#ffb86b"],[T.papers,"разобранных статей","в литературе тем","#5ee6d0"],[T.agentCommits,"правок от агентов","агент предлагает, человек решает","#ff8fb1"]];
    return `<section class="hub-stats" aria-label="База сейчас">${items.map(([v,l,n,c])=>`<div style="--c:${c}"><b>${num(v)}</b><span>${esc(l)}</span><small>${esc(n)}</small></div>`).join("")}</section>`;
  }

  function mapping(){
    return `<section class="hub-section"><p class="hub-kicker">Как это устроено</p><h2>У каждого знания есть история, проверка и автор</h2>
      <div class="hub-pairs">${MAP.map(([a,b,c,col,ic])=>`<article style="--c:${col}"><header><code>${esc(a)}</code><i aria-hidden="true">→</i></header><b><span aria-hidden="true">${ic}</span>${esc(b)}</b><p>${esc(c)}</p></article>`).join("")}</div></section>`;
  }

  // Как маленький проверяемый кирпич становится статьёй. Пример — настоящая работа dykaf.
  function chain(H){
    const C=(H.detail||{}).chain||{},u=C.urls||{};
    const steps=[
      {c:"#ffb86b",k:"01 · прогон",t:"Один запуск",big:"89,73",unit:"средняя точность LoRA-TSD на шести задачах, Llama-3-8B",p:"Дообучение большой языковой модели на шести задачах на понимание текста. Числа и условия записывает программа, которая считала. Человек и агент числа не переписывают.",who:"проверяет детерминированный код",href:u.run},
      {c:"#8fb4ff",k:"02 · серия",t:"Серия прогонов",big:"3",unit:"прогона отвечают на один вопрос",p:"«Лучше ли LoRA-TSD других способов обучать адаптеры?» Вердикт серии: на моделях 1B и 8B среднее выше всех, 82,49 против 81,60 у ближайшего соперника.",who:"Джев-судья: вердикт следует из чисел",href:u.series},
      {c:"#5ee6d0",k:"03 · рисунок",t:"График в статье",fig:C.figure,p:"Серии становятся рисунками статьи. Этот — точность в зависимости от ранга адаптера: LoRA-TSD держится ровно, а у соседних методов на малых рангах провал до 64.",who:"у рисунка есть адрес: из каких прогонов он собран"},
      {c:"#c79bff",k:"04 · утверждение",t:"Большая гипотеза",big:num(C.runs),unit:`прогонов · ${num(C.series)} серий · ${num(C.theory)} выкладок`,p:C.claim||"",who:"принимает ведущий работы",href:u.claim},
      {c:"#b9ff66",k:"05 · статья",t:"Рукопись",big:"AAAI",unit:"рукопись подаётся из этой же работы",p:"Каждое число в тексте ведёт к прогону, а прогон к коду. Рецензент может пройти весь путь назад.",who:"скрипт находит каждое число статьи в прогонах"}];
    return `<section class="hub-section" id="hub-chain"><p class="hub-kicker">Как растёт знание</p><h2>Большое начинается с малого и проверяемого</h2>
      <p class="hub-sub">Статья не пишется из головы. Она складывается из кирпичей, и каждый кирпич проверен раньше, чем на него что-то положат.</p>
      <ol class="hub-chain">${steps.map(s=>`<li style="--c:${s.c}"><small>${esc(s.k)}</small><b>${esc(s.t)}</b>
        ${s.fig?`<figure><img src="${esc(s.fig)}" alt="Точность в зависимости от ранга адаптера: LoRA-TSD и соседние методы" loading="lazy"></figure>`:`<strong class="${String(s.big).length>5?"is-word":""}">${esc(s.big)}</strong><em>${esc(s.unit)}</em>`}
        <p>${esc(s.p)}</p><span class="hub-who">✓ ${esc(s.who)}</span></li>`).join("")}</ol>
      <div class="hub-checks">
        <b>Ни одного выдуманного числа</b>
        <span style="--c:#5ee6d0"><i>1</i>Детерминированный код сверяет каждое число с прогонами и каждую ссылку с библиографией. Правило либо выполнено, либо нет.</span>
        <span style="--c:#ffb86b"><i>2</i>Джев-судья читает текст: следует ли вывод из чисел, нет ли пересказа вместо результата.</span>
        <span style="--c:#b9ff66"><i>3</i>Человек, ведущий работы, принимает уже проверенное. Без него ничего не становится знанием.</span>
      </div>
      <div class="hub-theory">
        <div style="--c:#ffe17a"><small>теория · выкладка</small><b>Шаг не зависит от выбора факторов</b><p class="hub-formula">X<sub>t+1</sub> = P<sub>T</sub>(msign X<sub>t</sub>)</p><p>Риманова геометрия: шаг ищется в касательном пространстве многообразия матриц низкого ранга и не зависит от того, как разложить адаптер на множители. Доказательство лежит рядом с прогонами.</p></div>
        <i aria-hidden="true">→</i>
        <div style="--c:#ff8fb1" class="is-next"><small>машинная проверка · подключаем</small><b>Формальная проверка</b><p>Следующий шаг: каждую выкладку проверяет программа, у которой нет права на ошибку. Человек читает уже проверенное доказательство.</p></div>
        <i aria-hidden="true">→</i>
        <div style="--c:#c79bff"><small>утверждение</small><b>Теория и опыт сходятся</b><p>Утверждение держится на двух опорах: выкладке и прогонах. Если одна из них падает, это видно сразу.</p></div>
      </div></section>`;
  }

  function why(){
    const cards=[
      ["#ffb86b","Агенты пишут быстрее, чем люди читают","Агент на сервере ведёт проверки ночью, каждое утро приходит разбор нового. Без истории и проверки такой поток становится шумом."],
      ["#8fb4ff","Число без адреса — не знание","У каждого числа в статье есть прогон, из которого оно взято, и его можно открыть. Число, которого нет в прогонах, проверки не пропустят."],
      ["#ff8fb1","Неудача — тоже знание","Опровергнутая идея остаётся в истории со своим прогоном. Следующий человек или агент не пойдёт в тот же тупик."]];
    return `<section class="hub-section"><p class="hub-kicker">Зачем она нужна</p><h2>Знание, которое не теряется и не врёт</h2>
      <div class="hub-why">${cards.map(([c,t,p],i)=>`<article style="--c:${c}"><span>0${i+1}</span><h3>${esc(t)}</h3><p>${esc(p)}</p></article>`).join("")}</div></section>`;
  }

  function works(H,all){
    const list=all?H.works:H.works.slice(0,9);
    const card=w=>ext(w.url,"hub-repo",`
      <header><span class="hub-repo-icon" aria-hidden="true">◫</span><b>${esc(w.slug)}</b></header><small class="hub-repo-theme">${esc(w.theme)}</small>
      <p>${esc(w.lead||w.title)}</p>
      <footer><span class="hub-dot" style="--h:${hue(w.direction)}"></span>${esc(w.direction)}<span>◇ ${num(w.claims)}</span><span>▶ ${num(w.runs)}</span><span>⑂ ${num(w.merges)}</span>${w.mrs?`<span class="is-open">${num(w.mrs)} ждёт ревью</span>`:""}<time>${esc(ago(w.updated))}</time></footer>
      <div class="hub-people">${(w.leads||[]).map(n=>avatar(n,false)).join("")}</div>
    `);
    return `<section class="hub-section" id="hub-works"><div class="hub-section-head"><div><p class="hub-kicker">Работы</p><h2>${H.public?"Открытая работа лаборатории":`Работы лаборатории <em>${num(H.works.length)}</em>`}</h2></div>
      ${H.gitlab?`<a class="hub-btn" href="${esc(H.gitlab)}" target="_blank" rel="noopener">Все в GitLab ↗</a>`:""}</div>
      <p class="hub-legend"><span>◇ утверждения</span><span>▶ прогоны</span><span>⑂ принятые предложения</span></p>
      <div class="hub-repos">${list.map(card).join("")}</div>
      ${all||H.works.length<=9?"":`<button class="hub-more" type="button" data-hub-all>Показать все ${num(H.works.length)}</button>`}</section>`;
  }

  function activity(H){
    return `<section class="hub-section hub-activity"><p class="hub-kicker">Живая лента</p><h2>Что происходит в базе</h2>
      <ol>${(H.events||[]).map(e=>`<li>${ext(e.url,"hub-event",`${avatar(e.who,e.agent)}
        <div><p><b>${esc(e.who)}</b>${e.agent?'<span class="hub-tag is-agent">агент</span>':""}${e.merge?'<span class="hub-tag is-merge">предложение принято</span>':""} <span class="hub-in">в ${esc(e.repo)}${e.more?` и ещё ${num(e.more)}`:""}</span></p><strong>${esc(e.s)}</strong></div>
        <time>${esc(ago(e.t))}</time>`)}</li>`).join("")}</ol></section>`;
  }

  function team(){
    const who=[
      ["Помощник","на рабочем месте","Думает и пишет вместе с сотрудником: идеи, анализ, тексты. Предлагает записи в базу."],
      ["Гермес","на сервере","Ведёт прогоны рядом с картами, сам просыпается, когда прогон закончился. Помнит проект неделями."],
      ["Джев","быстрый судья","За доли секунды отвечает «да или нет» с вероятностью: читает текст каждого предложения, отбирает статьи под наши работы, решает, что из хода сохранить."],
      ["Человек","ведущий работы","Решает, что проверять, и сливает предложения. Без его слияния ничего не становится знанием."]];
    return `<section class="hub-section"><div class="hub-section-head"><div><p class="hub-kicker">Контрибьюторы</p><h2>В команде люди и агенты</h2></div><a class="hub-btn" href="#setup">Как это устроено →</a></div>
      <div class="hub-team">${who.map(([n,w,t],i)=>`<article class="${i===3?"is-human":""}"><small>${esc(w)}</small><b>${esc(n)}</b><p>${esc(t)}</p></article>`).join("")}</div></section>`;
  }

  function render(view,opts={}){
    const H=window.LAB_HUB;
    if(!H){view.innerHTML=`<div class="hub-shell"><p class="hub-lead">Загружаем базу…</p></div>`;return}
    view.innerHTML=`<div class="hub-shell">${hero(H,opts.tab||"overview")}${stats(H.totals||{})}${mapping()}${chain(H)}${window.LAB_SEARCH_DEMO_PAGE?.section()||""}${why()}${works(H,opts.all)}${activity(H)}${team()}
      <section class="hub-cta"><h2>Хотите так же у себя?</h2><p>Расскажем, как устроить такую базу и агентов под задачи вашей компании.</p>${H.gitlab?`<a class="hub-btn is-primary" href="${esc(H.gitlab)}" target="_blank" rel="noopener">Открыть GitLab лаборатории ↗</a>`:H.cta?`<a class="hub-btn is-primary" href="${esc(H.cta.href)}" target="_blank" rel="noopener">${esc(H.cta.label)}</a>`:""}</section></div>`;
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
