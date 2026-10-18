/* Explanatory maps only. No connection to personal memory or task services. */
window.LAB_SURFACE_PAGES = (() => {
  const header = (name, label, lead, glyph) => `<header class="sp-hero"><div><span class="sp-label">${label}</span><h1 tabindex="-1">${name}</h1><p>${lead}</p></div><div class="sp-emblem" aria-hidden="true"><i></i><i></i><i></i><span>${glyph}</span></div></header>`;
  const node = (id, label, title, text, extra = '') => `<article class="sp-node ${extra}" data-sp-node="${id}"><span class="sp-label">${label}</span><h3><i class="sp-star" aria-hidden="true"></i>${title}</h3><p>${text}</p></article>`;
  const wires = '<svg class="sp-wires" aria-hidden="true"></svg>';
  const section = (label, title, text) => `<header class="sp-section-head"><div><span class="sp-label">${label}</span><h2>${title}</h2></div><p>${text}</p></header>`;

  function mempalace() {
    return `<div class="sp-page sp-memory" data-surface-page="mempalace">
      ${header('MemPalace', 'Контекст между сессиями', 'Новый разговор.<br>Работа продолжается с того же места.', '✧')}
      <section class="sp-memory-map sp-map" data-sp-map data-sp-links='[["session","diary"],["session","fragment"],["session","relation"],["diary","resume"],["fragment","resume"],["relation","resume"]]' aria-label="Из рабочего хода в память и следующую сессию">
        ${wires}
        ${node('session', 'Сейчас', 'Рабочий ход', 'Разговор, найденная причина ошибки, принятое решение. Агент выбирает, что пригодится дальше.', 'sp-session')}
        <div class="sp-memory-channels">
          ${node('diary', 'Дневник агента', 'Короткий итог', 'Что сделано, что осталось и откуда продолжать. Запись получает дату и тему.')}
          ${node('fragment', 'Фрагменты проекта', 'Точный контекст', 'Исходный текст решения, команды или кода. Рядом — источник и автор записи.')}
          ${node('relation', 'Граф знаний', 'Связи и факты', 'Кто ведёт проект, с чем связано решение, когда факт был действителен.')}
        </div>
        <article class="sp-resume" data-sp-node="resume"><span class="sp-label">Следующая сессия</span><h3>«На чём мы остановились?»</h3><p>Агент читает свой дневник, ищет историю проекта и открывает нужные фрагменты.</p><div class="sp-resume-result"><i class="sp-star" aria-hidden="true"></i><strong>Контекст восстановлен</strong><span>Решение · причина · следующий шаг</span></div></article>
      </section>
      <p class="sp-under-map"><b>Hook напоминает сохранить итоги.</b> Содержание выбирает и записывает агент. Успешное сохранение подтверждается чтением записи обратно.</p>
      <section class="sp-section">
        ${section('Как устроен дворец', 'У каждого фрагмента есть адрес.', 'Иерархия сужает поиск: сначала проект, затем аспект работы, затем конкретный источник.')}
        <div class="sp-palace-address">
          <article><span class="sp-label">Wing · крыло</span><h3>Проект</h3><p>Общий контекст одной работы.</p><span class="sp-address-example">проект-пример</span></article>
          <span class="sp-arrow" aria-hidden="true">→</span>
          <article><span class="sp-label">Room · комната</span><h3>Аспект</h3><p>Решения, ошибки, встречи, технические детали.</p><span class="sp-address-example">decisions</span></article>
          <span class="sp-arrow" aria-hidden="true">→</span>
          <article class="sp-drawer"><span class="sp-label">Drawer · фрагмент</span><blockquote>«Для сравнения фиксируем одинаковый бюджет обучения».</blockquote><p>Текст + источник + дата + ID</p></article>
        </div>
        <p class="sp-small">Условный пример. Дневник хранится отдельно по имени агента; один агент может работать с памятью нескольких проектов.</p>
      </section>
      <section class="sp-section">
        ${section('Как вспоминает агент', 'От вопроса — к исходному контексту.', 'Поиск возвращает сохранённые фрагменты. Агент читает их и сопоставляет с текущим состоянием работы.')}
        <ol class="sp-recall-path"><li><span>Короткий запрос</span><p>Ключевые слова, проект и нужная тема.</p></li><li><span>Смысл и слова</span><p>Векторные кандидаты; совпадения слов уточняют порядок.</p></li><li><span>Исходный фрагмент</span><p>Текст, место в памяти и ссылка на источник.</p></li><li><span>Проверка сейчас</span><p>Статус сервера, код и результаты могли измениться.</p></li></ol>
        <div class="sp-memory-foot"><div><h3>Нужно быстро продолжить?</h3><p>Последние записи дневника дают ближайшие действия. Поиск по проекту помогает восстановить более старое решение.</p></div><div><h3>Нужно понять связь?</h3><p>Запрос к графу находит отношения сущностей и их историю. Старый факт можно завершить по времени, сохранив его происхождение.</p></div></div>
        <details class="sp-fold"><summary>Хранилище и инструменты <span>Технические детали</span></summary><div class="sp-fold-body"><p>В проверенной установке тексты и векторы лежат в локальном Chroma. Поиск сначала получает кандидатов по смыслу; тематические сводки могут поднять связанные источники, а BM25 уточняет порядок по словам. Это поиск сохранённого материала, без генерации нового текста внутри поискового инструмента.</p><p>Типизированные связи с периодом действия хранятся отдельно в SQLite. Дневник может быть записан в компактном формате AAAK; исходные фрагменты сохраняют обычным текстом, чтобы их можно было прочитать и проверить.</p><dl class="sp-api"><dt>Записать</dt><dd>mempalace_diary_write · mempalace_add_drawer · mempalace_kg_add</dd><dt>Вспомнить</dt><dd>mempalace_diary_read · mempalace_search · mempalace_get_drawer · mempalace_kg_query</dd></dl></div></details>
      </section>
      <footer class="sp-footer"><p>MemPalace возвращает историю работы. Общие научные утверждения и их основания живут в GitLab лаборатории.</p><nav><a href="#memory">Карта общего знания ↗</a><a href="https://github.com/MemPalace/mempalace" target="_blank" rel="noopener">MemPalace на GitHub ↗</a></nav></footer>
    </div>`;
  }

  function tasks() {
    return `<div class="sp-page sp-team" data-surface-page="tasks">
      ${header('Задачи GitLab', 'Общее пространство команды', 'У каждой работы — свой репозиторий.<br>У каждой задачи — понятный результат.', '⌘')}
      <section class="sp-team-map sp-map" data-sp-map data-sp-links='[["research","theme"],["theme","area"],["area","project"],["management","delivery"],["delivery","project"]]' aria-label="Исследовательская и управленческая стороны работы">
        ${wires}
        ${node('research', 'Группа верхнего уровня', 'Направление', 'Область лаборатории: что изучаем и какие вопросы решаем.')}
        ${node('theme', 'Внутри направления', 'Тема', 'Родственные работы и общий репозиторий литературы.')}
        ${node('area', 'Внутри темы', 'Работа', 'Один репозиторий: утверждения, рукопись и код.')}
        <article class="sp-project-sheet" data-sp-node="project"><span class="sp-label">Репозиторий работы</span><h3>Вопрос → результат</h3><p>README: что утверждаем, кто ведёт, кто в команде и что открыто.</p><div><b>Задачи</b><span>Доска работы: что делается и кем</span></div><div><b>Предложения</b><span>Каждая запись в работу — merge request</span></div></article>
        ${node('management', 'Операционка', 'Обязательства', 'Гранты, коммерческие проекты, этапы и приёмка — группа ops.', 'sp-management')}
        <article class="sp-delivery" data-sp-node="delivery"><span class="sp-label">Репозиторий обязательства</span><h3>Что и когда передаём</h3><p>Заказчик или программа, этапы, сроки, документы и критерии приёмки.</p><span class="sp-crosslink">Ссылки на работы, из которых берётся результат ↗</span></article>
      </section>
      <p class="sp-under-map"><b>Коммерческое исследование использует обе стороны.</b> Научная работа остаётся в дереве лаборатории, договорные материалы — в операционке. Доска задач у работы одна.</p>
      <section class="sp-section">
        ${section('Внутри работы', 'Из договорённости — в задачу.', 'Человек видит ожидаемый результат, исполнителя и движение работы. Подробности остаются в самой задаче.')}
        <div class="sp-task-layout"><article class="sp-task-example"><span class="sp-label">Условный пример задачи</span><h3>Сравнить два метода<br>при одинаковом бюджете</h3><dl><dt>Исполнитель</dt><dd>Участник работы</dd><dt>Утверждение</dt><dd>Задача называет утверждение, на которое влияет</dd><dt>Готово, когда</dt><dd>Есть серия прогонов и ссылка на неё в утверждении</dd><dt>Результат</dt><dd>Слитое предложение со строкой «Closes #N»</dd></dl></article><div class="sp-task-explainer"><h3>Статус отражает ход работы.</h3><ol class="sp-task-path"><li><b>Открыта</b><span>Понятны цель и исполнитель</span></li><li><b>Делается</b><span>Есть прогресс или конкретное препятствие</span></li><li><b>На проверке</b><span>Предложение открыто, его можно оценить</span></li><li><b>Закрыта</b><span>Предложение слито — задача закрылась сама</span></li></ol><p class="sp-small">Колонки доски — ярлыки задач. Задачу закрывает слияние предложения, а не отметка руками.</p></div></div>
      </section>
      <section class="sp-section">
        ${section('Люди и агенты', 'Работают с одной доской.', 'Задачи живут в репозитории той же работы, в которую пишут знание. Второй доски рядом нет.')}
        <div class="sp-team-actors"><article><span class="sp-label">Человек</span><h3>Ставит и проверяет</h3><p>Определяет результат, назначает исполнителя, обсуждает прогресс и сливает предложение, которое задачу закрывает.</p></article><article><span class="sp-label">Агент в клоне</span><h3>Готовит и отправляет</h3><p>В начале сессии видит, что ему поручено. Берёт задачу, делает работу в клоне и открывает предложение со ссылкой на задачу.</p></article><article><span class="sp-label">Агент на сервере</span><h3>Ведёт долгое</h3><p>Сторожит прогоны и докладывает, что получилось, в ту же задачу. Исполнителем остаётся человек.</p></article></div>
        <p class="sp-under-map">Закрытая задача и оценка научного утверждения — разные результаты: задача говорит, что работа сделана, состояние утверждения — что из неё следует.</p>
      </section>
      <aside class="sp-common"><span class="sp-label">Общая информация</span><h3>Точка входа для всех.</h3><p>Передняя страница лаборатории в GitLab, справочник и журнал: как всё устроено, как попасть в работу и что недавно поменялось.</p></aside>
      <footer class="sp-footer"><p>Личные задачи — в Operon. Работа команды — задачи и доски работы в GitLab. Черновики остаются в notes/ своей работы.</p><nav><a href="https://github.com/brain-lab-research/claude-brainlab/blob/main/docs/onboarding.md" target="_blank" rel="noopener">Как поставить себе ↗</a></nav><small>Адрес базы приходит в сообщении бота доступа.</small></footer>
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
  return {header, node, wires, section, page:id => ({mempalace, tasks}[id]?.() || ''), bind, disconnect};
})();
