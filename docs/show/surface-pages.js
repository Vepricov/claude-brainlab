/* Explanatory maps only. No connection to personal memory or task services. */
window.LAB_SURFACE_PAGES = (() => {
  const header = (name, label, lead, glyph) => `<header class="sp-hero"><div><span class="sp-label">${label}</span><h1 tabindex="-1">${name}</h1><p>${lead}</p></div><div class="sp-emblem" aria-hidden="true"><i></i><i></i><i></i><span>${glyph}</span></div></header>`;
  const node = (id, label, title, text, extra = '') => `<article class="sp-node ${extra}" data-sp-node="${id}"><span class="sp-label">${label}</span><h3><i class="sp-star" aria-hidden="true"></i>${title}</h3><p>${text}</p></article>`;
  const wires = '<svg class="sp-wires" aria-hidden="true"></svg>';
  const section = (label, title, text) => `<header class="sp-section-head"><div><span class="sp-label">${label}</span><h2>${title}</h2></div><p>${text}</p></header>`;

  function mempalace() {
    return `<div class="sp-page sp-memory" data-surface-page="mempalace">
      ${header('MemPalace', 'Личная долговременная память агента', 'Новый разговор.<br>Работа продолжается с того же места.<br><b class="sp-hero-fact">Больше 37 600 записей на 19-10-2026.</b>', '✧')}
      <section class="sp-memory-map sp-map" data-sp-map data-sp-links='[["session","diary"],["session","fragment"],["session","relation"],["diary","resume"],["fragment","resume"],["relation","resume"]]' aria-label="Из рабочего хода в память и следующую сессию">
        ${wires}
        ${node('session', 'Сейчас', 'Рабочий ход', 'Разговор, найденная причина ошибки, принятое решение, измеренное число. Что из этого пригодится, решает агент.', 'sp-session')}
        <div class="sp-memory-channels">
          ${node('diary', 'Дневник агента', 'Сжатый итог', 'Что сделано, что осталось и откуда продолжать. Пишется в сжатом виде, с датой и темой.')}
          ${node('fragment', 'Ящики проекта', 'Дословно', 'Слова владельца, решение с причиной, команда, кусок кода. Не пересказ: пересказ теряет именно то, за чем возвращаются.')}
          ${node('relation', 'Граф знаний', 'Связи и факты', 'Кто ведёт проект, с чем связано решение, когда факт был действителен.')}
        </div>
        <article class="sp-resume" data-sp-node="resume"><span class="sp-label">Следующая сессия</span><h3>«На чём мы остановились?»</h3><p>Агент читает свой дневник, ищет историю проекта и открывает нужные фрагменты.</p><div class="sp-resume-result"><i class="sp-star" aria-hidden="true"></i><strong>Контекст восстановлен</strong><span>Решение · причина · следующий шаг</span></div></article>
      </section>
      <p class="sp-under-map"><b>Конец хода проверяет быстрая модель Джев.</b> Если в ходе есть что сохранить, агент получает одну строку: что записать и куда. Содержание выбирает и записывает сам агент.</p>
      <section class="sp-section">
        ${section('Как устроен дворец', 'У каждого фрагмента есть адрес.', 'Иерархия сужает поиск: сначала проект, затем аспект работы, затем конкретный источник.')}
        <div class="sp-palace-address">
          <article><span class="sp-label">Крыло</span><h3>Проект</h3><p>Общий контекст одной работы.</p><span class="sp-address-example">проект-пример</span></article>
          <span class="sp-arrow" aria-hidden="true">→</span>
          <article><span class="sp-label">Комната</span><h3>Аспект</h3><p>Решения, ошибки, встречи, технические детали.</p><span class="sp-address-example">решения</span></article>
          <span class="sp-arrow" aria-hidden="true">→</span>
          <article class="sp-drawer"><span class="sp-label">Ящик</span><blockquote>«Для сравнения фиксируем одинаковый бюджет обучения».</blockquote><p>Текст, источник, дата и номер</p></article>
        </div>
        <p class="sp-small">Условный пример.</p>
      </section>
      <section class="sp-section">
        ${section('Как вспоминает агент', 'От вопроса — к исходному контексту.', 'Поиск возвращает сохранённые ящики. Агент читает их и сопоставляет с текущим состоянием работы.')}
        <ol class="sp-recall-path"><li><span>Короткий запрос</span><p>Ключевые слова, проект и нужная тема.</p></li><li><span>Смысл и слова</span><p>Поиск идёт по смыслу, а точные слова уточняют порядок.</p></li><li><span>Исходный фрагмент</span><p>Текст, место в памяти и ссылка на источник.</p></li><li><span>Сверка с сегодняшним днём</span><p>Память могла устареть, поэтому агент сверяет её с текущим кодом и сервером.</p></li></ol>
        <div class="sp-memory-foot"><div><h3>Нужно быстро продолжить?</h3><p>Последние записи дневника дают ближайшие действия. Поиск по проекту помогает восстановить более старое решение.</p></div><div><h3>Нужно понять связь?</h3><p>Запрос к графу находит отношения сущностей и их историю. Старый факт можно завершить по времени, сохранив его происхождение.</p></div></div>
        <details class="sp-fold"><summary>Хранилище и инструменты <span>Технические детали</span></summary><div class="sp-fold-body"><p>Тексты и их смысловые отпечатки лежат локально, на машине исследователя. Поиск сначала находит кандидатов по смыслу, затем уточняет порядок по словам. Он возвращает сохранённое, а не сочиняет новое.</p><p>Связи между людьми, проектами и решениями хранятся отдельно, с периодом, когда факт был верен. Исходные фрагменты лежат обычным текстом, чтобы их можно было прочитать и проверить.</p><dl class="sp-api"><dt>Записать</dt><dd>итог в дневник · дословный фрагмент · связь в граф</dd><dt>Вспомнить</dt><dd>дневник · поиск · фрагмент целиком · связи</dd></dl></div></details>
      </section>
      <footer class="sp-footer"><p>MemPalace — память одного агента, а не база лаборатории. Общее знание (утверждения, прогоны, разборы статей) живёт в GitLab и попадает туда только слитым предложением.</p><nav><a href="#memory">Карта общего знания ↗</a><a href="https://github.com/MemPalace/mempalace" target="_blank" rel="noopener">MemPalace на GitHub ↗</a></nav></footer>
    </div>`;
  }

  function yonote() {
    return `<div class="sp-page sp-team" data-surface-page="yonote">
      ${header('GitLab', 'Задачи, доски и предложения', 'Задача, проверка и запись — в одном репозитории.<br>Последнее слово за человеком.', '⎇')}
      <section class="sp-team-map sp-map" data-sp-map data-sp-links='[["research","theme"],["theme","area"],["area","project"],["management","delivery"],["delivery","project"]]' aria-label="Наука и операционка в GitLab лаборатории">
        ${wires}
        ${node('research', 'Группа brainlab', 'Направление', 'Семь направлений исследований лаборатории.')}
        ${node('theme', 'Внутри направления', 'Тема', 'Родственные работы и общая литература темы.')}
        ${node('area', 'Внутри темы', 'Работа', 'Отдельный репозиторий. Ведущие записаны на первой странице работы, и сливают только они.')}
        <article class="sp-project-sheet" data-sp-node="project"><span class="sp-label">Внутри работы</span><h3>Задача → запись</h3><p>Задачи, доска и предложения живут рядом с самим знанием: утверждениями, статьёй и кодом.</p><div><b>Задачи и доска</b><span>Колонки доски строятся по ярлыкам</span></div><div><b>Предложения правок</b><span>Проверки сверяют, ведущий сливает</span></div></article>
        ${node('management', 'Группа ops', 'Операционка', 'Гранты, менеджмент, образование, коммуникации. Закрытая группа, отдельно от науки.', 'sp-management')}
        <article class="sp-delivery" data-sp-node="delivery"><span class="sp-label">Поток = ярлык</span><h3>Что и когда передаём</h3><p>Задачи операционки разложены по потокам-ярлыкам, например контент-план и разборы статей. Фильтр по ярлыку работает и в списке, и на доске.</p><span class="sp-crosslink">Ход дела: «делается» → «на проверке»</span></article>
      </section>
      <p class="sp-under-map"><b>Наука и операционка — в одном GitLab, но в разных группах.</b> Доступ к науке не даёт доступа к операционке. У работы одна доска — в её репозитории.</p>
      <section class="sp-section">
        ${section('Внутри работы', 'Из договорённости — в задачу.', 'Задача живёт в репозитории работы. В её теле стоит код утверждения: сразу видно, под какое утверждение пойдёт результат.')}
        <div class="sp-task-layout"><article class="sp-task-example"><span class="sp-label">Условный пример задачи</span><h3>Сравнить два метода<br>при одинаковом бюджете</h3><dl><dt>Исполнитель</dt><dd>Тот, кто взял задачу одной командой</dd><dt>Утверждение</dt><dd>Код утверждения, которое задача подтвердит или опровергнет</dd><dt>Готово, когда</dt><dd>Прогоны записаны рекордером и лежат под утверждением</dd><dt>Закрытие</dt><dd>Слияние предложения закрывает задачу само</dd></dl></article><div class="sp-task-explainer"><h3>Статус отражает ход работы.</h3><ol class="sp-task-path"><li><b>Открыта</b><span>Понятны цель и утверждение</span></li><li><b>Делается</b><span>Взявший задачу стал исполнителем</span></li><li><b>На проверке</b><span>Предложение открыто, идут проверки</span></li><li><b>Закрыта</b><span>Ведущий слил предложение</span></li></ol><p class="sp-small">Колонки доски строятся по ярлыкам «делается» и «на проверке».</p></div></div>
      </section>
      <section class="sp-section">
        ${section('Люди и агенты', 'Работают в одном репозитории.', 'Агент не пишет в базу напрямую. Он открывает предложение, его сверяют автоматические проверки, сливает человек. Слияние и есть запись.')}
        <div class="sp-team-actors"><article><span class="sp-label">Человек</span><h3>Ставит и сливает</h3><p>Ставит задачу и назначает исполнителя. Ведущий работы читает предложение и решает, войдёт ли оно в базу.</p></article><article><span class="sp-label">Claude Code</span><h3>Готовит предложение</h3><p>В начале сессии сам забирает свежие правки и показывает, что поручено. Берёт задачу, работает в отдельной ветке, одной командой открывает предложение на ведущего и видит вердикт проверок.</p></article><article><span class="sp-label">Гермес</span><h3>Держит свою доску</h3><p class="sp-fact"><b>На своей доске одного проекта Гермес закрыл 381 задачу.</b></p><p>У агента на сервере своя доска задач, общая для всех его проектов: взять, заблокировать, прокомментировать. Обзор доски приходит в Obsidian, в папку работы.</p></article></div>
        <p class="sp-under-map">Проверки считает код: число, которого нет ни в одном прогоне, останавливает слияние, а модель-судья может задержать его до правки текста. Непройденное GitLab слить не даст. Закрытая задача и принятое утверждение — разные результаты.</p>
      </section>
      <aside class="sp-common"><span class="sp-label">Общая информация</span><h3>Точка входа для всех.</h3><p>Справочник — как всё устроено и свод правил записи. Журнал — что и когда изменилось в способе работы. Серверы — где считать и как получить доступ. Все три открыты каждому, кто вошёл.</p></aside>
      <footer class="sp-footer"><p>Личные задачи и черновики — в Obsidian. Работа команды — задачи и предложения в GitLab.</p><nav><a href="#surface/obsidian">Obsidian и дерево лаборатории ↗</a><a href="#memory">Карта общего знания ↗</a></nav><small>Доступ выдаёт бот лаборатории в Telegram: гость, студент, исследователь или руководитель направления.</small></footer>
    </div>`;
  }

  let observer;
  let frame;
  function disconnect() { observer?.disconnect(); observer = null; cancelAnimationFrame(frame); }
  function bind(root) {
    disconnect();
    const draw = () => {
      if (!root.isConnected || root.closest('[hidden]')) return;
      root.querySelectorAll('[data-sp-map]').forEach(map => {
        const svg = map.querySelector('.sp-wires');
        if (!svg) return;
        const box = map.getBoundingClientRect();
        svg.setAttribute('viewBox', `0 0 ${box.width} ${box.height}`);
        svg.replaceChildren();
        for (const [from, to] of JSON.parse(map.dataset.spLinks || '[]')) {
          const a = map.querySelector(`[data-sp-node="${from}"]`)?.getBoundingClientRect();
          const b = map.querySelector(`[data-sp-node="${to}"]`)?.getBoundingClientRect();
          if (!a || !b) continue;
          const right = b.left >= a.right - 2;
          const left = b.right <= a.left + 2;
          const x1 = (right ? a.right : left ? a.left : a.left + a.width / 2) - box.left;
          const x2 = (right ? b.left : left ? b.right : b.left + b.width / 2) - box.left;
          const y1 = ((right || left) ? a.top + a.height / 2 : b.top >= a.bottom - 2 ? a.bottom : a.top) - box.top;
          const y2 = ((right || left) ? b.top + b.height / 2 : b.top >= a.bottom - 2 ? b.top : b.bottom) - box.top;
          const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
          path.dataset.edge = `${from}:${to}`;
          let d = (right || left) ? `M${x1},${y1} C${(x1+x2)/2},${y1} ${(x1+x2)/2},${y2} ${x2},${y2}` : `M${x1},${y1} C${x1},${(y1+y2)/2} ${x2},${(y1+y2)/2} ${x2},${y2}`;
          // Stacked branches travel in the margin, never through another node's text.
          const stacked = matchMedia('(max-width:540px)').matches && !map.classList.contains('sp-hermes-map');
          const obstructed = !right && !left && [...map.querySelectorAll('[data-sp-node]')].some(el => {
            if ([from, to].includes(el.dataset.spNode)) return false;
            const r = el.getBoundingClientRect();
            const minX = Math.min(a.left+a.width/2,b.left+b.width/2) - 1;
            const maxX = Math.max(a.left+a.width/2,b.left+b.width/2) + 1;
            return r.right > minX && r.left < maxX && r.top < Math.max(a.top,b.top) && r.bottom > Math.min(a.bottom,b.bottom);
          });
          if (stacked || obstructed) {
            const onRight = map.classList.contains('sp-memory-map') && to === 'resume';
            const rail = onRight ? box.width + 8 : -8;
            const sx = (onRight ? a.right : a.left) - box.left;
            const tx = (onRight ? b.right : b.left) - box.left;
            const ay = a.top + a.height / 2 - box.top;
            const by = b.top + b.height / 2 - box.top;
            const dy = Math.sign(by - ay) * 8;
            const corner = rail + (onRight ? -8 : 8);
            d = `M${sx},${ay} H${corner} Q${rail},${ay} ${rail},${ay+dy} V${by-dy} Q${rail},${by} ${corner},${by} H${tx}`;
          }
          path.setAttribute('d', d);
          svg.append(path);
        }
      });
    };
    observer = new ResizeObserver(() => { cancelAnimationFrame(frame); frame = requestAnimationFrame(draw); });
    root.querySelectorAll('[data-sp-map]').forEach(map => observer.observe(map));
    frame = requestAnimationFrame(draw);
  }
  return {header, node, wires, section, page:id => ({mempalace, yonote}[id]?.() || ''), bind, disconnect};
})();
