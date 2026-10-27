/* «Показ»: вставки в готовые страницы атласа. Данные в data/show-data.js. */
(()=>{
  const S=window.LAB_SHOW||{},esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
  const items=xs=>xs.map(([b,t])=>`<li><b>${esc(b)}</b><span>${esc(t)}</span></li>`).join("");
  // Экран этапа: один экран без прокрутки — главная мысль, «в любой компании», «как у нас», шаги.
  function stage(id){
    const d=(S.stage||{})[id],p=(window.RESEARCH_LOOP?.processes||[]).find(x=>x.id===id);
    if(!d||!p)return "";
    return `<section class="show-stage">
      <header><span class="show-num">${esc(p.number)}</span><div><h1 tabindex="-1">${esc(p.title)}</h1><p class="show-key">${esc(d.key)}</p></div>
        ${d.stat?`<div class="show-stat"><b>${esc(d.stat[0])}</b><span>${esc(d.stat[1])}</span></div>`:""}</header>
      <div class="show-cols">
        <article class="is-any"><p class="section-label">В любой компании</p><ul>${items(d.any)}</ul></article>
        <article class="is-ours"><p class="section-label">Как у нас</p><ul>${items(d.ours)}</ul></article>
      </div>
      <ol class="show-steps">${(p.stages||[]).map((s,i)=>`<li><small>${String(i+1).padStart(2,"0")}</small><b>${esc(s.title)}</b><span>${esc(s.result)}</span></li>`).join("")}</ol>
    </section>`;
  }
  function decorate(){
    const view=document.getElementById("process-view"),shell=view&&!view.hidden&&view.querySelector(".process-shell");
    const id=location.hash.replace(/^#/,"").split("/")[0];
    if(shell&&!shell.querySelector(".show-stage")){const html=stage(id);if(html){shell.classList.add("show-compact");shell.querySelector(".back-button")?.insertAdjacentHTML("afterend",html);}}
    // База знаний: диагональная лента в правом верхнем углу.
    const hub=document.querySelector(".hub-hero");
    if(hub&&!hub.querySelector(".show-ribbon")&&S.ribbon)hub.insertAdjacentHTML("afterbegin",`<div class="show-ribbon">${esc(S.ribbon[0])}<small>${esc(S.ribbon[1])}</small></div>`);
  }
  new MutationObserver(decorate).observe(document.body,{childList:true,subtree:true});
  decorate();
})();
