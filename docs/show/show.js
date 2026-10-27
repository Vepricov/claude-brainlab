/* «Показ»: две вставки в готовые страницы атласа. Данные в data/show-data.js. */
(()=>{
  const S=window.LAB_SHOW||{},esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
  function decorate(){
    // Страница этапа: после шапки — как мы этим пользуемся.
    const view=document.getElementById("process-view"),hero=view&&!view.hidden&&view.querySelector(".process-hero");
    const id=location.hash.replace(/^#/,"").split("/")[0],how=(S.how||{})[id];
    if(hero&&how&&!view.querySelector(".show-how"))hero.insertAdjacentHTML("afterend",
      `<section class="process-section show-how"><p class="section-label">Как мы этим пользуемся</p><h2>${esc(how[0])}</h2><p class="show-how-text">${esc(how[1])}</p></section>`);
    // База знаний: диагональная лента в правом верхнем углу.
    const hub=document.querySelector(".hub-hero");
    if(hub&&!hub.querySelector(".show-ribbon")&&S.ribbon)hub.insertAdjacentHTML("afterbegin",`<div class="show-ribbon">${esc(S.ribbon[0])}<small>${esc(S.ribbon[1])}</small></div>`);
  }
  new MutationObserver(decorate).observe(document.body,{childList:true,subtree:true});
  decorate();
})();
