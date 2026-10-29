/* «Показ»: вставки в готовые страницы атласа. Данные в data/show-data.js. */
(()=>{
  const S=window.LAB_SHOW||{},esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
  const items=xs=>xs.map(([b,t])=>`<li><b>${esc(b)}</b><span>${esc(t)}</span></li>`).join("");
  const rows=(n,cls="")=>Array.from({length:n},(_,i)=>`<i class="${cls}" style="--i:${i}"></i>`).join("");

  // Анимированные сцены этапов: одна мысль — одна картинка, всё на CSS, без внешних файлов.
  const SCENE={
    projects:()=>`<div class="sc-board">${[["Нужно сделать",["Ч","А"]],["В работе",["Ч"]],["Готово",["А","Ч"]]].map(([h,cs])=>`<div class="sc-col"><small>${h}</small>${cs.map(c=>`<span class="sc-card ${c==="А"?"is-agent":""}"><em>${c}</em><i></i><i></i></span>`).join("")}</div>`).join("")}
      <span class="sc-card sc-mover is-agent"><em>А</em><i></i><i></i></span></div>`,
    literature:()=>`<div class="sc-feed"><div class="sc-stream">${Array.from({length:14},(_,i)=>`<span class="${[2,6,11].includes(i)?"is-hit":""}"><i></i><i></i></span>`).join("")}</div>
      <div class="sc-digest"><small>Сводка на утро</small><b>3</b><span>из 6 000 за ночь</span></div></div>`,
    ideation:()=>`<div class="sc-idea"><div class="sc-doc"><small>Гипотеза</small><i></i><i></i><i style="width:60%"></i>
      <div class="sc-stamp"><small>Чем опровергается</small><i></i><i style="width:70%"></i></div></div>
      <span class="sc-q" style="--d:0s">Уже пробовали?</span><span class="sc-q" style="--d:1.4s">А если иначе?</span><span class="sc-q" style="--d:2.8s">Как проверить?</span></div>`,
    calls:()=>`<div class="sc-call"><div class="sc-wave">${rows(22)}</div><span class="sc-arrow">→</span>
      <div class="sc-out"><span style="--d:.4s">✓ Решение</span><span style="--d:1.2s">☐ Поручение · пт</span><span style="--d:2s">☐ Поручение · пн</span></div></div>`,
    experiments:()=>`<div class="sc-run"><span class="sc-moon">☾ ночь</span><svg viewBox="0 0 300 150" preserveAspectRatio="none"><path class="sc-grid" d="M0 37H300M0 75H300M0 112H300"/>
      <path class="sc-curve a" d="M0 20 C60 60 110 95 170 108 S260 122 300 124"/><path class="sc-curve b" d="M0 20 C50 70 100 112 160 124 S250 134 300 136"/></svg>
      <div class="sc-status"><i></i>идёт · 3 из 3 · сбоев нет</div></div>`,
    results:()=>`<div class="sc-bars">${[[48,"А"],[72,"Б"],[55,"В"]].map(([h,l],i)=>`<div style="--h:${h}%;--i:${i}"><span><em></em></span><small>${l}</small></div>`).join("")}
      <span class="sc-verdict">подтверждено</span></div>`,
    writing:()=>`<div class="sc-paper"><div class="sc-page">${rows(9)}<mark style="--t:15%;--d:.6s"></mark><mark style="--t:52%;--d:1.6s"></mark></div>
      <div class="sc-notes"><span style="--d:.9s">Где источник?</span><span style="--d:1.9s">Число не сходится</span><span class="is-ok" style="--d:3s">✓ исправлено</span></div></div>`,
    presentation:()=>`<div class="sc-spread"><span class="sc-core">одна мысль</span>${["пост","слайды","постер"].map((t,i)=>`<span class="sc-out-tile" style="--i:${i}">${t}</span>`).join("")}
      <svg viewBox="0 0 300 160" preserveAspectRatio="none"><path d="M150 80L45 30M150 80L255 30M150 80L150 145"/></svg></div>`,
  };

  // Экран этапа: один экран — главная мысль, сцена с примером, «в любой компании», «как у нас», шаги.
  function stage(id){
    const d=(S.stage||{})[id],p=(window.RESEARCH_LOOP?.processes||[]).find(x=>x.id===id);
    if(!d||!p)return "";
    return `<section class="show-stage">
      <header><span class="show-num">${esc(p.number)}</span><div><h1 tabindex="-1">${esc(p.title)}</h1><p class="show-key">${esc(d.key)}</p></div>
        ${d.stat?`<div class="show-stat"><b>${esc(d.stat[0])}</b><span>${esc(d.stat[1])}</span></div>`:""}</header>
      <div class="show-grid">
        <figure class="show-scene" data-scene="${esc(id)}">${SCENE[id]?SCENE[id]():""}<figcaption><b>Например</b>${esc(d.case||"")}</figcaption></figure>
        <article class="is-any"><p class="section-label">В любой компании</p><ul>${items(d.any)}</ul></article>
        <article class="is-ours"><p class="section-label">Как у нас</p><ul>${items(d.ours)}</ul></article>
      </div>
      <ol class="show-steps">${(p.stages||[]).map((s,i)=>`<li><small>${String(i+1).padStart(2,"0")}</small><b>${esc(s.title)}</b><span>${esc(s.result)}</span></li>`).join("")}</ol>
    </section>`;
  }

  // Орбиты карты: тонкие линии и бегущие по ним точки, без влияния на раскладку.
  const ORBITS=`<svg class="show-orbits" viewBox="0 0 1000 434" preserveAspectRatio="none" aria-hidden="true">
    <defs><radialGradient id="show-dot"><stop offset="0" stop-color="#66cdff"/><stop offset="1" stop-color="#66cdff" stop-opacity="0"/></radialGradient></defs>
    ${[[470,200,"o1",46],[380,152,"o2",34],[290,112,"o3",26]].map(([rx,ry,id,dur],i)=>`<path id="${id}" class="show-orbit o${i}" d="M${500-rx} 217a${rx} ${ry} 0 1 0 ${2*rx} 0a${rx} ${ry} 0 1 0 ${-2*rx} 0"/>
      <circle r="${7-i}" fill="url(#show-dot)"><animateMotion dur="${dur}s" repeatCount="indefinite" ${i%2?'keyPoints="1;0" keyTimes="0;1" calcMode="linear"':""}><mpath href="#${id}"/></animateMotion></circle>
      <circle r="${5-i}" fill="url(#show-dot)" opacity=".6"><animateMotion dur="${dur}s" begin="-${dur/2}s" repeatCount="indefinite" ${i%2?'keyPoints="1;0" keyTimes="0;1" calcMode="linear"':""}><mpath href="#${id}"/></animateMotion></circle>`).join("")}
  </svg>`;

  // Три круга в центре карты ведут в свои места «Показа».
  const SURFACE={obsidian:["ideas"],mempalace:["setup","memory"],hermes:["setup","team"]};
  document.addEventListener("click",e=>{
    const b=e.target.closest(".memory-surfaces button");if(!b)return;
    const key=b.dataset.surface||b.dataset.satTool,[view,section]=SURFACE[key]||[];if(!view)return;
    e.preventDefault();e.stopImmediatePropagation();
    document.querySelector(`[data-view="${view}"]`)?.click();
    if(section)setTimeout(()=>document.getElementById(`setup-${section}`)?.scrollIntoView({behavior:"smooth",block:"start"}),250);
  },true);

  // Первый экран: плитки не подсвечиваются. Навёл на этап — от него к базе знаний прорисовывается
  // луч, по нему бегут частицы, а от базы расходятся кольца цвета этапа. Владелец 27-10-2026:
  // «не делать, чтобы выделялись плитки… если навожу мышкой, начинается красивая анимация».
  function beams(){
    const map=document.getElementById("loop-map"),core=map&&map.querySelector(".knowledge-core");
    const nodes=map?[...map.querySelectorAll(".loop-node")]:[];
    if(!core||nodes.length<2||matchMedia("(max-width:760px)").matches)return;
    const m=map.getBoundingClientRect(),c=core.getBoundingClientRect(),cx=c.left+c.width/2-m.left,cy=c.top+c.height/2-m.top;
    const rays=nodes.map((n,i)=>{const r=n.getBoundingClientRect(),x=r.left+r.width/2-m.left,y=r.top+r.height/2-m.top;
      const ex=x+(cx-x)*.18,ey=y+(cy-y)*.18,tx=cx-(cx-x)*.22,ty=cy-(cy-y)*.22,qx=(ex+tx)/2+(ty-ey)*.14,qy=(ey+ty)/2-(tx-ex)*.14;
      const col=getComputedStyle(n).getPropertyValue("--node").trim()||"#5e98ff";
      return `<g class="show-ray" data-i="${i}" style="--node:${col}"><path id="show-beam-${i}" class="show-beam" pathLength="1" d="M${ex.toFixed(1)} ${ey.toFixed(1)}Q${qx.toFixed(1)} ${qy.toFixed(1)} ${tx.toFixed(1)} ${ty.toFixed(1)}"/>
        ${[0,1,2,3,4].map(k=>`<circle class="show-spark" r="${3-k*.4}"><animateMotion dur="1.3s" begin="${(-k*.26).toFixed(2)}s" repeatCount="indefinite"><mpath href="#show-beam-${i}"/></animateMotion></circle>`).join("")}</g>`;}).join("");
    map.querySelector(".show-beams")?.remove();
    map.insertAdjacentHTML("afterbegin",`<svg class="show-beams" width="${m.width}" height="${m.height}" aria-hidden="true">${rays}</svg>`);
    map.style.setProperty("--core-x",cx+"px");map.style.setProperty("--core-y",cy+"px");
    nodes.forEach((n,i)=>{if(n.dataset.showHover)return;n.dataset.showHover="1";let t=0;
      const ripple=()=>{const col=getComputedStyle(n).getPropertyValue("--node").trim()||"#5e98ff";
        map.insertAdjacentHTML("beforeend",`<span class="show-ripple" style="--node:${col}"></span>`);
        const el=map.lastElementChild;setTimeout(()=>el.remove(),1800);};
      n.addEventListener("mouseenter",()=>{map.querySelector(`.show-ray[data-i="${i}"]`)?.classList.add("is-on");map.classList.add("is-hovering");setTimeout(ripple,450);t=setInterval(ripple,900);});
      n.addEventListener("mouseleave",()=>{map.querySelector(`.show-ray[data-i="${i}"]`)?.classList.remove("is-on");map.classList.remove("is-hovering");clearInterval(t);});
    });
  }
  let rs;addEventListener("resize",()=>{clearTimeout(rs);rs=setTimeout(beams,150)});

  function decorate(){
    const view=document.getElementById("process-view"),shell=view&&!view.hidden&&view.querySelector(".process-shell");
    const id=location.hash.replace(/^#/,"").split("/")[0];
    if(shell&&!shell.querySelector(".show-stage")){const html=stage(id);if(html){shell.classList.add("show-compact");shell.querySelector(".back-button")?.insertAdjacentHTML("afterend",html);}}
    const map=document.getElementById("loop-map");
    if(map&&!map.querySelector(".show-orbits"))map.insertAdjacentHTML("afterbegin",ORBITS);
    if(map&&!map.querySelector(".show-beams")&&map.querySelector(".loop-node"))requestAnimationFrame(beams);
    const hub=document.querySelector(".hub-hero");
    if(hub&&!hub.querySelector(".show-ribbon")&&S.ribbon)hub.insertAdjacentHTML("afterbegin",`<div class="show-ribbon">${esc(S.ribbon[0])}<small>${esc(S.ribbon[1])}</small></div>`);
  }
  // Светлая тема: кнопка в шапке, выбор помнится в этом браузере.
  const theme=light=>{document.documentElement.classList.toggle("show-light",light);const b=document.getElementById("show-theme");
    if(b){b.textContent=light?"Тёмная тема":"Светлая тема";b.setAttribute("aria-pressed",String(light));}
    try{localStorage.setItem("show-theme",light?"light":"dark")}catch(e){}};
  let saved=false;try{saved=localStorage.getItem("show-theme")==="light"}catch(e){}
  theme(saved);
  document.getElementById("show-theme")?.addEventListener("click",()=>theme(!document.documentElement.classList.contains("show-light")));
  new MutationObserver(decorate).observe(document.body,{childList:true,subtree:true});
  decorate();
})();
