/* Locale routing stays in the public showcase. Private Atlas is unaffected. */
(() => {
  "use strict";
  const root = new URL(".", document.currentScript.src);
  const current = document.documentElement.lang;
  const params = new URLSearchParams(location.search);
  const explicit = params.get("lang");
  let saved;
  try { saved = localStorage.getItem("lab-atlas-language"); } catch (_) {}
  const requested = ["en", "ru"].includes(explicit) ? explicit :
    current === "ru" ? "ru" : saved === "ru" ? "ru" : "en";
  function destination(lang) {
    const url = new URL(lang === "ru" ? "ru/index.html" : "index.html", root);
    url.search = location.search;
    url.searchParams.set("lang", lang);
    url.hash = location.hash;
    return url;
  }
  if (requested !== current) {
    location.replace(destination(requested));
    return;
  }
  try { localStorage.setItem("lab-atlas-language", current); } catch (_) {}
  window.LAB_I18N = {
    language: current,
    asset: src => current === "en" ? `en/${src}` : src,
  };
  // A base URL serves shared assets in ru/. Fragment links still belong to this page.
  document.addEventListener("click", event => {
    const link = event.target.closest?.('a[href^="#"]');
    if (link) link.href = new URL(link.getAttribute("href"), location.href).href;
  }, true);
  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-language]").forEach(link => {
      const lang = link.dataset.language;
      link.href = destination(lang);
      link.setAttribute("aria-label", lang === "en" ? "Read in English" : "Читать по-русски");
      if (lang === current) link.setAttribute("aria-current", "true");
      link.addEventListener("click", event => {
        if (event.button || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        try { localStorage.setItem("lab-atlas-language", lang); } catch (_) {}
        location.assign(destination(lang));
      });
    });
  });
})();
