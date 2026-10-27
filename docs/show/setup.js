/* Вкладка «Сетап». Данные в data/setup-data.js, разметка здесь, стили в setup.css. */
(()=>{
  const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
  const list=xs=>xs?.length?`<ul class="setup-points">${xs.map(x=>`<li>${esc(x)}</li>`).join("")}</ul>`:"";

  function section(s){
    let body="";
    if(s.compare)body+=`<div class="setup-compare"><div><b>${esc(s.compare.left)}</b><p>${esc(s.compare.leftText)}</p></div><div class="is-ours"><b>${esc(s.compare.right)}</b><p>${esc(s.compare.rightText)}</p></div></div>`;
    if(s.layers)body+=`<ol class="setup-layers">${s.layers.map((l,i)=>`<li><span>${String(i+1).padStart(2,"0")}</span><div><b>${esc(l.name)}</b><small>${esc(l.role)}</small><p>${esc(l.text)}</p></div></li>`).join("")}</ol>`;
    if(s.agents)body+=`<div class="setup-agents">${s.agents.map(a=>`<article><small>${esc(a.where)}</small><b>${esc(a.name)}</b><p>${esc(a.text)}</p></article>`).join("")}</div>`;
    return `<section class="setup-section" id="setup-${esc(s.id)}"><p class="overline">${esc(s.kicker)}</p><h2>${esc(s.title)}</h2><p class="setup-lead">${esc(s.lead)}</p>${body}${list(s.points)}</section>`;
  }

  function render(view){
    const d=window.LAB_SETUP;if(!d)return;
    view.innerHTML=`<div class="setup-shell">
      <header class="setup-head"><p class="overline">Агенты и модели · сверено ${esc(d.verified)}</p><h1>${esc(d.title)}</h1><p>${esc(d.intro)}</p></header>
      <dl class="setup-numbers">${d.numbers.map(n=>`<div><dt>${esc(n.value)}</dt><dd><b>${esc(n.label)}</b><span>${esc(n.note)}</span></dd></div>`).join("")}</dl>
      <section class="setup-turn"><p class="overline">Модели</p><h2>${esc(d.turn.title)}</h2><p class="setup-lead">${esc(d.turn.lead)}</p>
        <ol class="setup-stages">${d.turn.stages.map((st,i)=>`<li><span class="setup-event">шаг ${String(i+1).padStart(2,"0")}</span><b>${esc(st.title)}</b>
          <ul>${st.hooks.map(h=>`<li><strong>${esc(h.name)}</strong><p>${esc(h.text)}</p>${h.file?`<code>${esc(h.file)}</code>`:""}</li>`).join("")}</ul></li>`).join("")}</ol>
      </section>
      <nav class="setup-nav" aria-label="Разделы">${d.sections.map(s=>`<a href="#setup/${esc(s.id)}" data-setup-jump="${esc(s.id)}">${esc(s.kicker)}</a>`).join("")}</nav>
      <div class="setup-sections">${d.sections.map(section).join("")}</div>
    </div>`;
    view.querySelectorAll("[data-setup-jump]").forEach(a=>a.onclick=e=>{
      e.preventDefault();history.replaceState(null,"",`#setup/${a.dataset.setupJump}`);
      view.querySelector(`#setup-${CSS.escape(a.dataset.setupJump)}`)?.scrollIntoView({behavior:"smooth",block:"start"});
    });
  }

  window.LAB_SETUP_PAGE={render};
})();
