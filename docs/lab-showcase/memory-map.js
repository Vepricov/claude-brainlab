/* Explanatory maps contain no private records and read nothing from the lab's GitLab. */
window.LAB_MEMORY_MAP = (() => {
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const origins = {
    projects:['Проект','create-project · контекст'],
    literature:['Литература','Hermes · paper-ingest'],
    ideation:['Идеи','research-ideation'],
    calls:['Созвоны','Brain Call · call-notes'],
    experiments:['Эксперименты','Hermes · coding agents'],
    results:['Результаты','анализ · academic-plotting'],
    writing:['Статья и ревью','ML Paper Writing · Astar'],
    presentation:['Публикация','paper-to-social · presentation']
  };
  const dot = '<i class="mem-star" aria-hidden="true"></i>';
  const arrow = '<i class="mem-inline-arrow" aria-hidden="true">→</i>';
  const station = (id, label, title, body, extra='') => `<article class="mem-station ${extra}" data-point="${id}">${dot}<span class="mem-label">${label}</span><h3>${title}</h3>${body}</article>`;
  const api = (...names) => `<span class="mem-api-names">${names.map(n=>`<code>${n}</code>`).join(' · ')}</span>`;
  const svg = '<svg class="mem-connections" aria-hidden="true"></svg>';
  const inlets = {
    ingest:[['scout','Литературный Hermes','находит по теме'],['search','paper-search','предлагает кандидатов'],['alphaxiv','alphaXiv / arXiv','ссылка на работу'],['social','X / коллеги','делятся статьёй'],['reader','Исследователь','выбирает для разбора']],
    project:[['hermes','Экспериментальный Hermes','прогоны и результаты'],['agents','Codex / Claude Code','код, проверки, выводы'],['call','Brain Call / call-notes','идеи и решения встречи'],['person','Исследователь','гипотезы и материалы']]
  };
  const feeders = kind => `<div class="mem-feeders" aria-label="${kind==='ingest'?'Откуда приходит статья':'Откуда приходят материалы работы'}">${inlets[kind].map(([id,title,caption])=>`<div class="mem-inlet" data-inlet="${kind}" data-point="${kind}-via-${id}"><b>${title}</b><small>${caption}</small></div>`).join('')}</div>`;

  // Устройство записей сверено со сводом правил базы (brainlab/handbook, canon.md), 18-10-2026.
  const recordGuide = {
    hypothesis: {title:'Наше утверждение',code:'claims/H-XXX/',text:'Одна проверяемая мысль о методе — папка в репозитории работы. Код H-XXX даётся один раз и остаётся после проверки: по нему видны основания, история и вывод.',fields:[['Заголовок','Одна фраза, которую можно прочесть вслух: что утверждаем и при каких условиях. Это проверяет код, а не добросовестность пишущего.'],['Опровержение','Что именно опровергнет мысль. Без критерия опровержения это не утверждение.'],['Основания','Прогоны и серии в runs/ и series/, выкладки в theory/, рисунки в figures/ — рядом, в той же папке.'],['Состояние','draft → testing → supported, refuted или inconclusive, и меняется только по своему критерию.'],['Происхождение','Работа и тема видны из пути, история — из git: кто, когда и каким предложением это записал.']],example:'«При одинаковом бюджете метод A снижает ошибку относительно B». Критерий опровержения: преимущество исчезает при повторении заданного сравнения.'},
    empirical: {title:'Проверяется опытом',code:'claims/H-XXX/ · runs · series',text:'Утверждение, которое проверяют измерением. Прогоны пишет код, серии собирают их в ответ на один вопрос.',fields:[['Что устанавливаем','Эффект, зависимость, сравнение методов или границы применимости.'],['Чем обосновываем','Сериями прогонов: у каждого числа есть адрес, по которому его видно.']],example:'«При фиксированном числе шагов метод A даёт меньшую ошибку на отложенной выборке».'},
    theoretical: {title:'Проверяется выкладкой',code:'claims/H-XXX/ · theory',text:'Утверждение, которое проверяют математическим выводом. Предпосылки и доказательство лежат в файле выкладки рядом с утверждением.',fields:[['Что устанавливаем','Равенство, оценку, сходимость или другой математический результат.'],['Чем обосновываем','Выкладкой с явными предпосылками и разделом «Доказательство».']],example:'«При указанных предпосылках ошибка убывает не медленнее заданной оценки».'},
    unspecified: {title:'И то, и другое',code:'claims/H-XXX/',text:'Идеальное утверждение держит и теорию, и опыты про один приём: теорема и прогоны про одно и то же — одна папка, а не две.',fields:[['Зачем так','Чтобы в работе были единицы утверждений, а не сотня, и каждое читалось целиком.']]},
    paperClaim: {title:'Утверждение из статьи',code:'literature/<Название>.md',text:'Мысль внешней работы: что утверждают её авторы и где это найти. Разбор статьи — страница в репозитории литературы темы, одна на статью.',fields:[['Содержание','Формулировка с условиями применимости. Пересказ допустим.'],['Вид','Результат, теорема, метод или определение.'],['Источник','Раздел, таблица, формула или теорема статьи; ключ цитирования и BibTeX — в шапке страницы.'],['Связи','Наша работа ссылается на разбор: предыстория, baseline, поддерживает или противоречит. Ссылка сама по себе нашу проверку не завершает.']],example:'«Авторы сообщают снижение ошибки в таблице 2 на наборе X при таких-то условиях».'},
    paperEmpirical: {title:'Результат авторов',code:'literature · результат',text:'Измерение или наблюдение, о котором сообщает статья. Сохраняются существенные условия: модель, данные, метрика и сравнение.',fields:[['Польза','Можно сопоставить заявленный результат со своим прогоном и найти исходную таблицу.']],example:'«В таблице 3 метод A превосходит B на двух из трёх наборов данных».'},
    paperTheoretical: {title:'Теоретический результат авторов',code:'literature · теорема',text:'Теорема, лемма, оценка или вывод из статьи. Формулировка сохраняет предпосылки, а указатель ведёт к месту доказательства.',fields:[['Польза','Помогает использовать результат в своей работе, учитывая условия, при которых он доказан.']],example:'«Теорема 1 даёт оценку сходимости при липшицевом градиенте».'},
    paperMethod: {title:'Метод из статьи',code:'literature · метод',text:'Что предлагают делать авторы: алгоритм, приём обучения или процедура. Описание метода отделено от заявления о его эффективности.',fields:[['Польза','Можно восстановить идею метода и связать её со своей реализацией.']],example:'«Авторы нормируют обновление по спектральной норме перед шагом оптимизатора».'},
    paperDefinition: {title:'Определение из статьи',code:'literature · определение',text:'Как авторы определяют понятие или величину. Помогает сравнивать работы, в которых одно слово значит разное.',fields:[['Польза','Сохраняет точный смысл термина в контексте этой публикации.']],example:'«В определении 2 эффективный ранг задаётся через спектр матрицы».'},
    assessment: {title:'Состояние утверждения',code:'status',text:'Состояние меняется у того же утверждения и только по его собственному критерию. Законченный прогон сам по себе состояния не меняет: вывод формулирует человек или агент, и сливает его человек.',fields:[['До вывода','Черновик (draft) → проверяется (testing) с первой серией.'],['После проверки','Подтверждено (supported), опровергнуто (refuted) или без вывода (inconclusive).'],['Вывод','Раздел «Вывод» есть только у досмотренного: при draft и testing его нет, иначе он обещает то, чего ещё нет.'],['История','Каждое изменение — коммит со слиянием: видно, кто, когда и на каком основании поменял состояние.']],example:'Прогоны завершились, но результаты расходятся между повторами. Утверждение: inconclusive, и в серии написано почему.'},
    experiment: {title:'Прогон',code:'runs/E-XXX.md',text:'Страница одного запуска. Её пишет код: рекордер lab_run.py знает гиперпараметры, числа, коммит и железо, а переписывать их руками запрещено.',fields:[['Внутри','Команда, конфигурация, окружение, коммит, железо и метрики — так, как их записал рекордер.'],['От агента','Ровно одно: что в этих числах видно.']],example:'Сравнение A и B на одной модели и данных с одинаковым бюджетом: три затравки, у каждой своя страница.'},
    evidence: {title:'Серия',code:'series/S-XXX.md',text:'Набор прогонов, отвечающий на один вопрос, и вердикт по нему. Серия входит в утверждение абзацем.',fields:[['Факт','Таблица прогонов и чисел; у каждого числа адрес, по которому его видно.'],['Смысл','Вердикт и границы: «не установлено» тоже законный вердикт.'],['Чистота','Несравнимое в серию не тянут; прогон вне серии объявляется на своей странице.']],example:'Средняя ошибка A — 0,18, B — 0,20 в трёх повторах. Ограничение: проверено на одном наборе данных.'},
    derivation: {title:'Выкладка',code:'theory/D-XXX.md',text:'Математическое основание утверждения: формулировка, предпосылки и раздел «Доказательство». Файл на сюжет, а не на лемму.',fields:[['Формулировка','Читается с нуля и не содержит чисел конкретного прогона.'],['Место работы','Выкладка живёт, только если названо, где она работает в утверждении.']],example:'Из предпосылок о гладкости вывести верхнюю оценку ошибки и явно отметить ещё не доказанную лемму.'},
    project: {title:'Работа',code:'<направление>/<тема>/<работа>',text:'Один репозиторий на работу. Первая страница отвечает в одном порядке: что утверждаем, чем это проверено, что открыто.',fields:[['Внутри','claims/ — знание; paper/ и code/ — рукопись и код вложенными репозиториями; socials/ и calls/ — постеры и созвоны.'],['Люди','Строки «Ведут» и «Команда» в README: по ним бот зовёт решать заявки, а предложение встаёт на ведущего.']]},
    paper: {title:'Литература темы',code:'<тема>/literature/',text:'У каждой темы свой репозиторий разборов: одна страница на статью, названная по статье, с ключом цитирования в шапке. README литературы собирается из самих страниц.',fields:[['Польза','От тезиса в нашей работе можно вернуться к полному разбору. Одна статья может быть нужна многим работам.']]},
    decision: {title:'Предложение',code:'merge request',text:'Любая запись в работу входит предложением: ветка, коммит, git push — и предложение открывается само. Ворота считают числа и судят прозу, сливает человек.',fields:[['Тело','Три вещи: что изменилось, на чём это основано, что осталось открытым.'],['Кто сливает','Ведущий работы. Агент сливает только по названному слову человека и пишет в предложение, по чьему.'],['Запись','Слияние и есть запись. Ветка, черновик и заметка записью не являются.']],example:'Ветка claim/H-XXX-001: новая серия прогонов и абзац в утверждении. Ворота зелёные, ведущий слил.'},
    journal: {title:'Журнал',code:'brainlab/journal',text:'Хроника способа работы лаборатории: новое правило, новое место, выключенный инструмент — с датой, свежее сверху.',fields:[['Что сюда','То, что через месяц кто-то будет искать и расстроится, не найдя.'],['Как пишут','Обычный push в main после git pull --rebase: это служебный репозиторий.']],example:'«Лаборатория ставится одним деревом ~/brainlab: lab sync собирает всё, что видно».'},
    term: {title:'Словарь',code:'literature/glossary/',text:'Определение внутреннего имени: метода, прогона, метрики или протокола. Имя определяется до первого употребления.',fields:[['Польза','Человек или агент расшифрует старую запись без автора.']]},
    resource: {title:'Серверы',code:'brainlab/servers',text:'Что важно знать про железо: что изменилось, что не работает, где сменился доступ. Эфемерного состояния вроде свободной карты здесь нет — его смотрят командой.',fields:[['Польза','Прогон не стартует или адрес не отвечает — первым делом сюда.']]},
    source: {title:'История',code:'git log · merge requests',text:'Откуда взялась запись и как менялась: коммит, его автор и время, предложение с обсуждением и вердиктом ворот.',fields:[['Польза','Вывод можно проверить по истории и восстановить, как он менялся. Ничего не хранится отдельно от самого файла.']]},
    relations: {title:'Ссылки',code:'[Название](путь.md)',text:'Записи связаны обычными относительными ссылками: их рисуют и GitLab, и Obsidian, и ведут они в один и тот же файл.',fields:[['Внутри работы','Утверждение → прогоны, серии, выкладки, рисунки.'],['Между репозиториями','Работа → разбор в литературе темы — полным адресом GitLab.'],['Структура','Прогон лежит под утверждением; серия собирает прогоны; выкладка обосновывает утверждение; предложение несёт изменение.']]}
  };
  const typeButton = (id,title,caption='',cls='') => `<button type="button" class="mem-type ${cls}" data-record="${id}" aria-haspopup="dialog"><span>${title}</span>${caption?`<small>${caption}</small>`:''}</button>`;
  function anatomy(){
    return `<section class="mem-anatomy" data-chapter="anatomy" aria-labelledby="mem-anatomy-title">
      <header class="mem-anatomy-heading"><span class="mem-label">GitHub для идей</span><h1 id="mem-anatomy-title" tabindex="-1">Из чего состоит <em>знание</em></h1><p>Для кода у мира есть GitHub. Это то же самое для идей: утверждение — папка в репозитории работы, а всё, чем оно обосновано, лежит рядом файлами с адресом и историей.</p></header>
      <div class="mem-anatomy-map mem-diagram" data-map="anatomy">${svg}
        <article class="mem-anatomy-paper" data-point="paper-claim"><span class="mem-label">Что сообщают авторы</span>${typeButton('paperClaim','Из статьи','literature/&lt;Название&gt;.md','mem-type-major')}<div class="mem-kind-stars" aria-label="Виды утверждений статьи">${typeButton('paperEmpirical','Результат')}${typeButton('paperTheoretical','Теория')}${typeButton('paperMethod','Метод')}${typeButton('paperDefinition','Определение')}</div><p>Разбор в литературе темы.<br>Одна страница на статью.</p><small class="mem-anatomy-relation">Ссылкой из нашей работы →</small></article>
        <article class="mem-anatomy-claim" data-point="our-claim"><span class="mem-label">Что проверяем мы</span>${typeButton('hypothesis','Наше утверждение','claims/H-XXX/ · один код до и после проверки','mem-type-major')}<div class="mem-kind-stars" aria-label="Чем проверяется утверждение">${typeButton('empirical','Опытом')}${typeButton('theoretical','Выкладкой')}${typeButton('unspecified','Тем и другим')}</div><div class="mem-claim-parts"><span><b>Мысль</b>заголовок в одну фразу</span><span><b>Условия</b>когда это верно</span><span><b>Опровержение</b>что опровергнет мысль</span><span><b>План</b>как проверим</span><span><b>Источник</b>ссылки на прогоны и статьи</span><span><b>Состояние</b>вывод и его причина</span></div></article>
        <article class="mem-anatomy-assessment" data-point="verdict"><span class="mem-label">Как меняется оценка</span>${typeButton('assessment','Состояние','в шапке того же README','mem-type-major')}<p class="mem-status-path">draft → testing<br>с первой серией</p><div class="mem-status-outcomes"><span>supported</span><span>refuted</span><span>inconclusive</span></div><small>Меняется только по своему критерию.<br>Каждое изменение — слитое предложение.</small></article>
        <article class="mem-anatomy-ground" data-point="run"><span class="mem-label">Как проверяли</span>${typeButton('experiment','Прогон','runs/E-XXX.md · пишет код')}<p>Что запустили, на каком коммите и железе, с какими числами.</p></article>
        <article class="mem-anatomy-ground" data-point="observation"><span class="mem-label">Эмпирическое основание ↑</span>${typeButton('evidence','Серия','series/S-XXX.md · вердикт')}<p>Прогоны, отвечающие на один вопрос, и что из них видно.</p></article>
        <article class="mem-anatomy-ground mem-proof-ground" data-point="proof"><span class="mem-label">Теоретическое основание ↖</span>${typeButton('derivation','Выкладка','theory/D-XXX.md · доказательство')}<p>Предпосылки, формулировка и доказательство.</p></article>
      </div>
      <div class="mem-context-atlas"><span class="mem-label">Вокруг научных записей</span><div>${[['project','Работа','один репозиторий'],['paper','Литература темы','разборы статей'],['decision','Предложение','так входит запись'],['journal','Журнал','как мы работаем'],['term','Словарь','что значат имена'],['resource','Серверы','где считаем'],['source','История','git log и обсуждения'],['relations','Ссылки','как записи связаны']].map(([id,title,caption])=>typeButton(id,title,caption)).join('')}</div></div>
    </section>`;
  }

  function overview(processes){
    return `<div class="mem-overview mem-diagram" data-map="overview">${svg}
      <div class="mem-origins" data-point="origins"><span class="mem-label">Вся работа в Atlas</span><div class="mem-source-stars">${processes.map(p=>`<div class="mem-origin" data-origin="${esc(p.id)}" style="--star:${esc(p.color)}"><i aria-hidden="true"></i><span><b>${origins[p.id][0]}</b><small>${origins[p.id][1]}</small></span></div>`).join('')}</div></div>
      <div class="mem-writer" data-point="writer">${dot}<div><b>Агент работает в клоне</b><p>Задание / навык <span class="mem-trigger-arrow">↘</span> <span class="mem-hook-trigger">Hook · куда записать ↗</span><br>Правит файлы в дереве ~/brainlab и открывает предложение.</p></div></div>
      <div class="mem-main-lanes">
        <div class="mem-lane mem-literature-lane">
          ${station('paper','Из литературы','Статья','<p>Разбор в литературе темы:<br>пишется прямо в main.</p>')}
          ${station('extract','Разбор','Отдельные мысли','<p>Разделы → результаты, теоремы, методы и определения.</p>')}
        </div>
        <div class="mem-lane mem-research-lane">
          ${station('question','Наша работа','Работа','<p>Репозиторий: утверждения,<br>прогоны, рукопись и код.</p>','mem-project-node')}
          ${station('check','Проверка','Предложение и ворота','<p>Ветка → git push → предложение.<br>Ворота считают числа и судят прозу.</p><small>Слияние человеком и есть запись.</small>')}
        </div>
      </div>
      <article class="mem-assertion" data-point="assertion" aria-label="Что лежит в GitLab: утверждение">
        <header><span class="mem-label">GitLab лаборатории · git</span><h2>Утверждение</h2><p>Одна проверяемая мысль<br>с условиями и происхождением.</p></header>
        <div class="mem-assertion-origin mem-from-paper" data-point="paper-result"><span class="mem-label">Из статьи <code>literature/</code></span><p><b>Что утверждают авторы</b></p><dl><dt>Источник</dt><dd>Статья + раздел, таблица или теорема</dd><dt>Содержание</dt><dd>Формулировка, вид и условия применимости</dd></dl></div>
        <div class="mem-assertion-origin mem-from-project" data-point="project-result"><span class="mem-label">Из работы <code>claims/H-XXX/</code></span><p><b>Что проверяем мы</b></p><dl><dt>Основания</dt><dd>Прогоны и серии или выкладка</dd><dt>Состояние</dt><dd>draft → testing → supported, refuted или inconclusive</dd></dl><small>Один код до и после проверки. Вывод — по своему критерию.</small></div>
        <footer>Обычные файлы в git.<br>У каждого — адрес, история и ревью.</footer>
      </article>
      <div class="mem-personal"><span class="mem-label">Тот же агент ведёт личное рядом</span><div class="mem-personal-stores">
        <article class="mem-obsidian" data-point="obsidian"><span class="mem-store-mark" aria-hidden="true">◇</span><h3>Obsidian</h3><p>То же дерево ~/brainlab. Заметки, дневник и логи лежат в notes/, daily/ и runs/ своей работы и в GitLab не едут.</p></article>
        <article class="mem-palace" data-point="mempalace"><span class="mem-store-mark" aria-hidden="true">⌘</span><h3>MemPalace</h3><p>Дневник сессий, исходные фрагменты и решения. Контекст для следующего хода агента.</p></article>
      </div></div>
      <div class="mem-context"><span><b>Журнал</b> как мы работаем</span><span><b>Справочник</b> как всё устроено</span><span><b>Словарь</b> что значат имена</span><span><b>Серверы</b> где считаем</span><p>Это тоже репозитории дерева. Служебные принимают обычный push в main, работы — только предложением.</p></div>
    </div>`;
  }

  function ingestion(){
    return `<section class="mem-chapter" aria-labelledby="mem-ingest-title" data-chapter="ingest">
      <header class="mem-chapter-heading"><div><span class="mem-label">Кто и как добавляет знание</span><h2 id="mem-ingest-title">Из статьи. Из работы.<br><em>Из рабочего разговора.</em></h2></div><p>Материалы приносят люди и агенты. Каждый путь заканчивается файлом в git: разбор — прямо в литературу темы, знание работы — слитым предложением.</p></header>
      <header class="mem-flow-heading"><h3>Статья → разбор в литературе темы</h3><p>Поиск и рекомендация дают кандидата. В литературу темы попадает выбранная и разобранная работа.</p></header>
      <div class="mem-ingest-map mem-diagram" data-map="ingest">${svg}${feeders('ingest')}
        ${station('document','Материал','Статья и источник',`<div class="mem-paper-sheet"><span>arXiv / DOI</span><b>Полный текст</b><div aria-hidden="true"><i></i><i></i><i></i><i></i></div><small>Таблицы · формулы · приложения</small></div><p>Сначала ищем, нет ли разбора: по всем literature/ дерева сразу. Zotero хранит библиографию и PDF.</p>${api('git grep','paper-ingest')}`)}
        ${station('reader','Смысл выделяет агент','Прочитать и разобрать',`<p>Литературный Hermes или любой агент с навыком paper-ingest читает статью, сверяет числа и предпосылки, отделяет выводы авторов от собственных проверок.</p><div class="mem-model"><span>Модель литературного профиля</span><b>gpt-5.6-sol</b></div><p>Разбор пишется сразу в репозиторий литературы темы — никакой отдельной базы.</p>`)}
        ${station('sections','Одна страница на статью','Записать разбор',`<div class="mem-section-stack"><span>Метод</span><span>Теория</span><span>Эксперименты</span><span>Ограничения</span></div><p>Имя файла — название статьи. Ключ цитирования и BibTeX — в шапке, рисунки — рядом, в _attachments/.</p><small>Одна статья — один экземпляр, сколько бы работ на неё ни ссылалось.</small>${api('literature/&lt;Название&gt;.md')}`)}
        ${station('claims','Научный результат разбора','Выделить утверждения',`<p>Агент формулирует каждую независимую мысль своими словами, сохраняя условия.</p><div class="mem-claim-fan"><div><b>Результат</b><span>Метрика, число, модель, данные</span></div><div><b>Теорема</b><span>Предпосылки и полученный вывод</span></div><div><b>Метод / определение</b><span>Что предложено и что означает</span></div></div><small>Заголовок — одна фраза без формул и процентов без базы. Это проверяет код.</small>${api('paper_claims_lint.py')}`)}
      </div>
      <div class="mem-ingest-end"><div class="mem-claim-schema"><span class="mem-label">Каждая страница</span><p><b>Формулировка</b>${arrow}<b>Вид и условия</b>${arrow}<b>Статья + место</b>${arrow}<b>Ключ цитирования</b></p><small>Цитата необязательна. Ссылка на источник и точное место нужны для проверки.</small></div><div class="mem-claim-relations"><span class="mem-label">Связь с нашей работой</span><p>Утверждение статьи ${arrow} <b>наше утверждение</b></p><small>Предыстория · baseline · поддерживает · противоречит · воспроизводит. Ссылку ставит тот, кто прочитал и может обосновать.</small>${api('ссылка на разбор')}</div></div>
      ${projectIngestion()}${checkpointIngestion()}
      <div class="mem-save-route"><h3>Один порядок записи</h3><ol><li><b>Найти уже записанное</b><p>git pull и поиск по дереву. Свободный код утверждения берётся из клона: наибольший номер, а не количество.</p></li><li><b>Открыть предложение</b><p>Ветка claim/H-XXX, коммит, git push — предложение откроется само и встанет на ведущего работы.</p></li><li><b>Пройти ворота и слияние</b><p>Ворота считают числа и судят прозу за минуту. Сливает человек, и слияние — это и есть запись.</p></li></ol></div>
    </section>`;
  }

  function projectIngestion(){
    return `<div class="mem-project-flow"><header class="mem-flow-heading"><h3>Работа → наши утверждения и основания</h3><p>Работа — это репозиторий. Её материалы раскладываются по папкам утверждений, а рукопись и код подключены рядом.</p></header>
      <div class="mem-project-map mem-diagram" data-map="project">${svg}${feeders('project')}
        ${station('workspace','Материалы исследования','Работа и её место',`<div class="mem-project-sheet"><span>WORK</span><b>Наше исследование</b><div><span>claims/ — знание</span><span>paper/ и code/</span><span>calls/ и socials/</span></div></div><p>Путь работы в дереве совпадает с её адресом в GitLab: направление, тема, работа.</p>${api('lab sync','lab here')}`)}
        ${station('claim','Что хотим выяснить','Сформулировать',`<p>Одна проверяемая мысль: заголовок в одну фразу, условия, ожидаемый результат и критерий опровержения.</p><div class="mem-section-stack"><span>Проверяется опытом</span><span>Проверяется выкладкой</span></div><small>Утверждение получает код в начале и сохраняет его после проверки.</small>${api('claims/H-XXX/README.md')}`)}
        ${station('grounds','Две формы проверки','Положить основания',`<div class="mem-research-branches"><div><b>Прогон → серия</b><p>Страницу прогона пишет рекордер lab_run.py: гиперпараметры, числа, коммит, железо. Серия отвечает на один вопрос вердиктом.</p>${api('runs/E-XXX.md','series/S-XXX.md')}</div><div><b>Математический вывод</b><p>Формулировка с нуля → предпосылки → доказательство.</p>${api('theory/D-XXX.md')}</div></div>`)}
        ${station('assessment','Научный итог','Оценить утверждение',`<p>Основания сопоставляются с исходным критерием, противоречия называются вслух.</p><div class="mem-verdicts"><b>Подтверждено</b><b>Опровергнуто</b><b>Без вывода</b></div><small>Состояние и вывод пишутся в README того же утверждения и входят предложением.</small>${api('git push','lab checks')}`)}
      </div>
      <div class="mem-operational-paths"><span><b>Изменился способ работы</b>${arrow}<span>Журнал</span>${api('brainlab/journal')}</span><span><b>Как устроен инструмент</b>${arrow}<span>Справочник</span>${api('brainlab/handbook')}</span><span><b>Сервер, доступ, сбой</b>${arrow}<span>Серверы</span>${api('brainlab/servers')}</span></div>
      <p class="mem-flow-note">Готовые результаты дописываются к существующим утверждениям, а не заводят новые. Разбор созвона приносит идеи и договорённости; предполагаемый результат остаётся гипотезой до проверки.</p>
    </div>`;
  }

  function checkpointIngestion(){
    return `<div class="mem-checkpoint-flow"><header class="mem-flow-heading"><h3>Hook → куда записать итог хода</h3><p>Ещё один вход в ту же базу: сохранить полезное из работы, даже если отдельной команды на запись не было.</p></header>
      <div class="mem-hook-map mem-diagram" data-map="hook">${svg}
        ${station('session','В ходе работы','Накапливается контекст','<div class="mem-session-lines"><span>Получили результат</span><span>Нашли ограничение</span><span>Выбрали следующий шаг</span></div><p>У Codex, Claude Code и автономных Hermes появляются факты, которые понадобятся следующему агенту.</p>')}
        ${station('checkpoint','Автоматическая подсказка','Срабатывает hook','<div class="mem-cadence"><span><b>Codex / Claude Code</b>в конце хода называет место записи</span><span><b>Автономный Hermes</b>каждые 5 рабочих ходов</span></div><small>Место выбирается по описаниям репозиториев на сайте. Hook называет адрес, но сам не пишет и ничего не сливает.</small>')}
        ${station('curator','Действует агент','Отобрать и записать','<p>Агент читает контекст, выбирает долговечное и пишет в клон нужного репозитория в дереве.</p><small>В базу идёт то, что через месяц кто-то будет искать. Если записывать нечего, лишнего не появляется.</small>')}
        ${station('ack','Подтверждение','Довести до main','<div class="mem-checkpoint-stores"><span><b>GitLab</b>знание, ветка, предложение</span><span><b>Obsidian</b>заметки в notes/</span><span><b>MemPalace</b>контекст и история</span></div><small>Хук видит в клоне несохранённое и неотправленное и напоминает, пока правка не потерялась.</small>')}
      </div><p class="mem-flow-note">Подсказка — совет, а не приказ: место выбирает агент. Ни hook, ни ворота не заменяют научную оценку и слияние человеком.</p>
    </div>`;
  }

  function analysisScenarios(){
    const cases=[
      ['compare','Сравнить результаты','Какая проверка сильнее?',`<b>Прогоны и серии</b>${api('runs/','series/')}`,`<b>Агент сверяет протоколы</b><small>Данные, baseline, затравки, единицы и ограничения</small>`,`<b>Сравнение и графики</b><small>results-analysis · academic-plotting, если исходные данные доступны</small>`, 'Числа сравниваются в одинаковых условиях. Отсутствующие повторы и метрики остаются видимыми пробелами.'],
      ['assess','Проверить вывод','Что уже подтверждено?',`<b>Утверждение и критерий</b>${api('claims/H-XXX/README.md')}`,`<b>Серии или выкладка</b>${api('series/','theory/')}`,`<b>Оценка с основаниями</b><small>Состояние и границы вывода</small>`, 'Новая оценка — правка README утверждения предложением; вердикт ворот приходит через минуту, сливает ведущий.'],
      ['literature-check','Сопоставить с литературой','Где наши результаты расходятся?',`<b>Наше утверждение</b>${api('grep по literature/')}`,`<b>Утверждения статьи</b>${api('literature/&lt;Название&gt;.md')}`,`<b>Сходство или противоречие</b><small>С учётом данных, предпосылок и области применимости</small>`, 'Поиск предлагает соседние работы. Содержательную связь ставит тот, кто прочитал; похожий текст не доказывает поддержку.'],
      ['gaps','Найти незакрытое','Чего не хватает для вывода?',`<b>Состояние работы</b>${api('lab checks')}`,`<b>Проверить найденный пробел</b><small>Нет критерия опровержения, вердикта серии или адреса у числа</small>`,`<b>Понятный следующий шаг</b><small>Что записать, уточнить или проверить</small>`, 'Ворота ловят пропуски по своду правил. Научное качество оценивает человек при слиянии.'],
      ['resume','Продолжить работу','Что изменилось с прошлого раза?',`<b>Что пришло в main</b>${api('git pull','git log')}`,`<b>Предложения и задачи</b>${api('lab pull','lab tasks')}`,`<b>Сводка изменений</b><small>Новые результаты, решения и оставшиеся вопросы</small>`, 'Хук начала сессии сам делает git pull и печатает, что изменилось, что открыто и что поручено тебе.']
    ];
    return `<div class="mem-analysis-scenarios"><header class="mem-flow-heading"><h3>После поиска — разобраться в результате</h3><p>Дерево отдаёт файлы и ссылки. Исследователь или агент проверяет смысл, сравнивает данные и формулирует вывод.</p></header>${cases.map(([id,label,title,a,b,c,note])=>`<article class="mem-analysis-case" data-scenario="${id}"><div><span class="mem-label">${label}</span><h4>${title}</h4></div><div class="mem-walk-path"><span>${a}</span>${arrow}<span>${b}</span>${arrow}<span>${c}</span></div><p>${note}</p></article>`).join('')}<div class="mem-useful-context"><span><b>Кто ведёт работу</b>${api('«Ведут» в README')}</span><span><b>Какие серверы доступны</b>${api('brainlab/servers')}</span><span><b>Что означают термины</b>${api('literature/glossary/')}</span></div></div>`;
  }

  function retrieval(){
    return `<section class="mem-chapter" aria-labelledby="mem-search-title" data-chapter="search">
      <header class="mem-chapter-heading"><div><span class="mem-label">Работа с накопленным знанием</span><h2 id="mem-search-title">Найти. Сопоставить.<br><em>Понять, что следует из результатов.</em></h2></div><p>Всё знание лаборатории лежит у тебя локально, поэтому искать можно обычными инструментами: grep, git log, поиском Obsidian и поиском GitLab.</p></header>
      <div class="mem-readers"><span class="mem-label">Кто обращается к базе</span><span>Исследователь</span><span>Codex / Claude Code</span><span>Литературный Hermes</span><span>Экспериментальный Hermes</span><small>Вопрос → дерево ~/brainlab → файлы с адресом и историей</small></div>
      <div class="mem-search-map mem-diagram" data-map="search">${svg}
        ${station('query','Есть вопрос','Поиск по запросу',`<blockquote>«Что известно о методе и его ограничениях?»</blockquote><p>Вся лаборатория, одна тема или одна работа — это просто папки дерева.</p>${api('lab sync')}`)}
        ${station('words','Текст','По словам','<p>git grep и ripgrep проходят дерево за доли секунды. Поиск Obsidian читает те же файлы.</p>')}
        ${station('vectors','Сайт','Поиск GitLab','<p>Поиск по группе на сайте — когда дерева нет под рукой. Видно ровно то, к чему есть доступ.</p>')}
        ${station('merge','Литература','Во всех темах сразу','<p>Разбор лежит в той теме, куда его занесли, а не там, где он нужен. Поэтому искать надо по всем literature/ сразу.</p><small>По ключу цитирования или названию статьи.</small>')}
        ${station('graph','Контекст','Пройти по ссылкам','<p>От утверждения — к его прогонам, сериям, выкладкам и разборам статей.</p><small>Относительные ссылки рисуют и Obsidian, и GitLab.</small>')}
        ${station('rerank','История','git log и предложения','<p>Кто, когда и почему поменял запись — в коммите и в обсуждении предложения, вместе с вердиктом ворот.</p>')}
        ${station('answer','Результат','Файл с адресом','<ul class="mem-answer-fields"><li>Путь и код</li><li>Формулировка</li><li>Работа и тема</li><li>Связанные файлы</li></ul><p>Ответ ссылается на файл и коммит: по адресу его откроет любой, у кого есть доступ.</p>')}
      </div>
      <div class="mem-search-settings"><p><b>Без отдельного индекса:</b> поиск идёт по самим файлам. Нет второй копии — нечему расходиться с правдой.</p><p><b>Свежесть:</b> lab sync подтягивает всё дерево, а начало сессии само делает git pull в текущей работе.</p></div>
      ${analysisScenarios()}
      <div class="mem-walks"><h3>Начать с темы, работы или знакомой записи</h3>
        <div class="mem-walk" data-route="theme"><div><span class="mem-label">Изучить направление</span><h4>От темы к работам</h4></div><div class="mem-walk-path"><span><b>Направление → темы</b>${api('~/brainlab/&lt;направление&gt;/')}</span>${arrow}<span><b>Страница темы</b><small>Предмет, работы, кто ведёт</small></span>${arrow}<span><b>Работы и утверждения</b><small>Своя наука + литература</small></span></div></div>
        <div class="mem-walk" data-route="library"><div><span class="mem-label">Осмотреть библиотеку</span><h4>От темы к статье</h4></div><div class="mem-walk-path"><span><b>Тема → литература</b>${api('&lt;тема&gt;/literature/')}</span>${arrow}<span><b>Подтема → статьи</b><small>README литературы ведёт по подтемам</small></span>${arrow}<span><b>Статья → утверждения</b>${api('literature/&lt;Название&gt;.md')}</span></div><p>README литературы собирается из самих страниц: полные названия, авторы и пересказ, без обрезки.</p></div>
        <div class="mem-walk" data-route="known"><div><span class="mem-label">Есть конкретный объект</span><h4>От работы или кода</h4></div><div class="mem-walk-path"><span><b>Работа</b>${api('lab here &lt;работа&gt;')}</span>${arrow}<span><b>Первая страница → утверждение</b>${api('README.md')}</span>${arrow}<span><b>Полная запись</b>${api('claims/H-XXX/')}</span></div><p>Первая страница работы отвечает в одном порядке: что утверждаем, чем это проверено, что открыто.</p></div>
        <div class="mem-walk" data-route="evidence"><div><span class="mem-label">Проверить основание</span><h4>От утверждения к проверке</h4></div><div class="mem-walk-path"><span><b>Известная запись</b><small>Код H-XXX</small></span>${arrow}<span><b>Прогоны и серии</b>${api('ссылки страницы')}</span>${arrow}<span><b>История изменений</b>${api('git log -- claims/H-XXX')}</span></div><p>Это явные ссылки и история git. Их происхождение можно проверить, а смену состояния — прочитать по коммитам.</p></div>
        <div class="mem-walk" data-route="neighbors"><div><span class="mem-label">Расширить вопрос</span><h4>Найти соседние идеи</h4></div><div class="mem-neighbor-paths"><span><b>Общие термины</b>${api('literature/glossary/')}<small>Тематическое соседство, не доказанная связь</small></span><span><b>Литература вокруг утверждения</b>${api('grep по literature/')}<small>По формулировке и механизму</small></span><span><b>Похожая запись до добавления</b>${api('grep по claims/')}<small>Кандидаты на дубль; решение за агентом</small></span></div></div>
      </div>
      <div class="mem-vector-cache"><div><span class="mem-label">Почему так</span><h3>Одно место, без копий</h3><p>Знание живёт в git и только в git: ни базы рядом, ни публикации из одного в другое.</p></div><div class="mem-cache-path"><span><b>Файл</b><small>Правка в клоне</small></span>${arrow}<span><b>Ветка</b><small>claim/H-XXX</small></span>${arrow}<span><b>Предложение</b><small>Ворота и обсуждение</small></span>${arrow}<span><b>main</b><small>Слито человеком</small></span></div><p>Общая база, в которую любой агент пишет что угодно, бесполезна: в ней нет никого, кто скажет «нет». Файл в git проходит предложение, и его принимает человек. Что слито в main, то и есть знание лаборатории.</p></div>
    </section>`;
  }

  function accessGuide(){
    return `<section class="mem-chapter mem-access" id="lab-access" aria-labelledby="mem-access-title">
      <header class="mem-chapter-heading"><div><span class="mem-label">Человек · роль · работа</span><h2 id="mem-access-title">Доступ к лаборатории.<br><em>Права в своей работе.</em></h2></div><p>Одна учётка GitLab на человека. Роль в корне лаборатории — пол для всего дерева: выше её можно поднять в любой теме и работе, ниже нельзя.</p></header>
      <div class="mem-access-steps"><span>ФИО, ник и рекомендатель</span><i>→</i><span>Запрошенная роль</span><i>→</i><span>Одобряет любой лид</span><i>→</i><span>Учётка, ключ git и дерево ~/brainlab</span></div>
      <div class="mem-access-roles mem-access-roles-4">
        <article><span class="mem-label">Guest</span><h3>Гость</h3><p>Видит дерево направлений, тем и работ и всю литературу. Содержимое работ закрыто. С этого начинают все.</p></article>
        <article><span class="mem-label">Reporter</span><h3>Студент</h3><p>Читает все работы целиком: утверждения, прогоны, рукописи, обсуждения. Писать нельзя, обсуждать можно.</p></article>
        <article><span class="mem-label">Developer</span><h3>Исследователь</h3><p>Права студента плюс работа: ветки и предложения в любой работе, свои новые работы в любой теме. Сливать не может.</p></article>
        <article><span class="mem-label">Maintainer</span><h3>Лид</h3><p>Сливает предложения во всех работах, заводит темы и владеет теми, где ведёт работу. Заявки в свои места решает сам.</p></article>
      </div>
      <div class="mem-access-project"><h3>В каждой работе — свои люди</h3><dl><div><dt>Ведущий <code>Owner</code></dt><dd>Сливает предложения и решает заявки в свою работу.</dd></div><div><dt>Команда <code>Developer</code></dt><dd>Ветки и предложения: те, кто работу делает.</dd></div><div><dt>Читатель <code>Reporter</code></dt><dd>Видит работу целиком, не пишет.</dd></div></dl><p>Попасть в тему или работу — кнопка Request access на её странице: заявка приходит в телеграм тому, кто её ведёт. Кто ведёт и кто в команде, записано строками «Ведут» и «Команда» в README работы.</p></div>
      <footer><a href="https://t.me/brainlab_server_access_bot" target="_blank" rel="noopener noreferrer">Открыть бот доступа ↗</a><p>Нажмите «Получить доступ», отметьте базу знаний в списке ресурсов и выберите роль. Роль действует после одобрения; дальше один установщик ставит Obsidian и собирает дерево ~/brainlab командой lab sync.</p></footer>
    </section>`;
  }

  function anyTeam(){
    return `<section class="mem-chapter" aria-labelledby="mem-team-title" data-chapter="team">
      <header class="mem-chapter-heading"><div><span class="mem-label">Не только для науки</span><h2 id="mem-team-title">Общий GitLab для идей —<br><em>для любой команды.</em></h2></div><p>Устройство не знает, что внутри научные утверждения. Продукт, аналитика, исследования рынка или инженерия: везде, где решения опираются на проверяемые основания, работает тот же порядок.</p></header>
      <div class="mem-save-route mem-save-route-4"><h3>Четыре правила</h3><ol><li><b>Работа — репозиторий</b><p>У каждой своё место, свои люди и своя история. Права наследуются по дереву, как у групп GitLab.</p></li><li><b>Мысль — папка</b><p>Утверждение и всё, чем оно обосновано, лежат рядом файлами. Формы ради формы нет: страницу читают глазами.</p></li><li><b>Запись — слияние</b><p>Агенты и люди предлагают, ворота проверяют числа и прозу, человек принимает. Мусор в базу не проходит.</p></li><li><b>Дерево у каждого</b><p>Вся база лежит локально одним деревом и открывается в Obsidian. Работа — обычным git: правка, ветка, push.</p></li></ol></div>
    </section>`;
  }

  function render(p, processes){
    return `<div class="process-shell memory-observatory" style="--accent:#b9ff66">
      <header class="mem-header"><div><button class="back-button" data-back type="button">← Весь Atlas</button><span class="mem-coordinate">BRAIn Lab / GitLab лаборатории</span></div></header>
      ${anatomy()}
      <header class="mem-chapter-heading mem-overview-heading"><div><span class="mem-label">Откуда приходит знание</span><h2>Как работа становится <em>знанием</em></h2></div></header>
      <section class="mem-first-map" aria-label="Общая карта: источники, утверждения и личная память" data-chapter="overview">${overview(processes)}<div class="mem-practice-notes"><p><b>Когда сохраняется:</b> по ходу работы. В конце хода hook называет место записи, агент правит клон и отправляет.</p><p><b>Где задачи:</b> общие — задачи (issues) репозитория работы в GitLab, личные — в Operon. Хук начала сессии показывает, что поручено тебе.</p></div></section>
      ${ingestion()}${retrieval()}${accessGuide()}${anyTeam()}
      <footer class="mem-footer"><p>Схемы показывают устройство системы, без данных частной базы. Сверено со сводом правил базы 18-10-2026.</p><details class="mem-tools"><summary>Навыки и инструменты этого слоя</summary><div>${p.tools.map(t=>`<button type="button" data-skill="${esc(t.id)}">${esc(t.title)}</button>`).join('')}</div></details><a href="https://github.com/brain-lab-research/claude-brainlab/blob/main/docs/onboarding.md" target="_blank" rel="noopener noreferrer">Как поставить себе ↗</a></footer>
      <dialog class="skill-dialog" aria-labelledby="skill-dialog-title"></dialog>
      <dialog class="skill-dialog mem-record-dialog" aria-labelledby="mem-record-title"></dialog>
    </div>`;
  }

  const edges={
    overview:[['writer','paper','paper'],['writer','question','project'],['paper','extract','paper'],['question','check','project'],['extract','paper-result','paper'],['check','project-result','project']],
    ingest:[['document','reader','paper'],['reader','sections','paper'],['sections','claims','paper']],
    project:[['workspace','claim','project'],['claim','grounds','project'],['grounds','assessment','project']],
    hook:[['session','checkpoint','violet'],['checkpoint','curator','violet'],['curator','ack','project']],
    search:[['query','words','paper'],['query','vectors','violet'],['words','merge','paper'],['vectors','merge','violet'],['merge','graph','project'],['graph','rerank','project'],['rerank','answer','project']]
  };
  let observer;
  function drawAnatomy(map){
    const box=map.getBoundingClientRect(),surface=map.querySelector('.mem-connections');
    if(!box.width||!box.height)return;
    const rect=id=>{const r=map.querySelector(`[data-point="${id}"]`).getBoundingClientRect();return {l:r.left-box.left,r:r.right-box.left,t:r.top-box.top,b:r.bottom-box.top,x:r.left-box.left+r.width/2}};
    const line=(a,b,color,vertical=false)=>{
      const from=rect(a),to=rect(b);let d;
      if(matchMedia('(max-width:760px)').matches){
        const rail=5;d=`M${from.l+5},${from.b+5} H${rail} V${to.t-10} H${to.l+5}`;
      }else if(vertical){
        const y=(from.t+to.b)/2;d=`M${from.x},${from.t-8} V${y} H${to.x} V${to.b+8}`;
      }else{
        d=`M${from.r+7},${from.t+57} H${to.l-7}`;
      }
      return `<path class="mem-line-${color}" data-edge="${a}:${b}" d="${d}"/>`;
    };
    surface.setAttribute('viewBox',`0 0 ${box.width} ${box.height}`);
    surface.innerHTML=matchMedia('(max-width:760px)').matches?'':line('paper-claim','our-claim','paper')+line('our-claim','verdict','project')+line('run','observation','project')+line('observation','our-claim','project',true)+line('proof','our-claim','violet',true);
  }
  function draw(map){
    if(map.dataset.map==='anatomy'){drawAnatomy(map);return}
    const box=map.getBoundingClientRect();if(!box.width||!box.height)return;
    const svg=map.querySelector('.mem-connections'),kind=map.dataset.map,compact=matchMedia('(max-width:760px)').matches;
    const bounds=id=>map.querySelector(`[data-point="${id}"]`).getBoundingClientRect();
    const path=(from,to,color)=>{
      const a=bounds(from),b=bounds(to);let d;
      if(kind==='overview'&&from==='writer'){
        if(matchMedia('(max-width:1100px)').matches)return '';
        const rail=b.left-box.left-16,ay=a.top-box.top+11,bx=b.left-box.left+4,by=b.top-box.top+35;
        d=`M${a.left-box.left+4},${ay} H${rail} V${by} H${bx}`;
      }else if(b.left>=a.right-3){
        const node=map.querySelector(`[data-point="${from}"]`),heading=node.querySelector('h3')?.getBoundingClientRect();
        const ax=(heading?Math.min(a.right,heading.right+12):a.right)-box.left,ay=a.top-box.top+35,bx=b.left-box.left-2,by=b.top-box.top+(to.endsWith('result')?23:35),mid=(ax+bx)/2;
        d=`M${ax},${ay} C${mid},${ay} ${mid},${by} ${bx},${by}`;
      }else{
        const ax=a.left-box.left+12,ay=a.bottom-box.top+5,bx=b.left-box.left+12,by=b.top-box.top-8;
        const rail=compact?3:Math.min(ax,bx)-17;
        d=`M${ax},${ay} H${rail} V${by-6} Q${rail},${by} ${rail+6},${by} H${bx}`;
      }
      return `<path data-edge="${from}:${to}" class="mem-line-${color}" d="${d}" marker-end="url(#mem-arrow-${kind}-${color})"/>`;
    };
    let lines=edges[kind].map(e=>path(...e)).join('');
    if(inlets[kind]){
      const target=kind==='ingest'?'document':'workspace',b=bounds(target),group=map.querySelector('.mem-feeders').getBoundingClientRect(),bx=b.left-box.left+4,by=b.top-box.top+35;
      for(const [id] of inlets[kind]){
        const source=`${kind}-via-${id}`,a=bounds(source),ax=a.left-box.left+4,ay=a.top-box.top+8,rail=compact?group.left-box.left-10:group.bottom-box.top+20;
        const d=compact?`M${ax},${ay} H${rail} V${by} H${bx}`:`M${ax},${ay+8} V${rail-6} Q${ax},${rail} ${Math.max(bx,ax-6)},${rail} H${bx} V${by}`;
        lines+=`<path data-edge="${source}:${target}" class="mem-line-${kind==='ingest'?'paper':'project'} mem-line-feeder" d="${d}" marker-end="url(#mem-arrow-${kind}-${kind==='ingest'?'paper':'project'})"/>`;
      }
    }
    if(kind==='overview'&&matchMedia('(min-width:1101px)').matches){
      const b=bounds('writer');map.querySelectorAll('[data-origin]').forEach(el=>{const a=el.getBoundingClientRect(),ax=a.right-box.left,ay=a.top-box.top+a.height/2,bx=b.left-box.left+4,by=b.top-box.top+11,mid=(ax+bx)/2;lines+=`<path class="mem-line-input" d="M${ax},${ay} C${mid},${ay} ${mid},${by} ${bx},${by}"/>`});
      for(const id of ['obsidian','mempalace']){
        const a=bounds(id),rail=b.left-box.left-16,x=a.left-box.left+7,y=a.top-box.top;
        lines+=`<path data-edge="writer:${id}" class="mem-line-private" d="M${b.left-box.left+4},${b.top-box.top+11} H${rail} V${y-6} H${x} V${y+10}"/>`;
      }
    }
    const colors={paper:'#9ec9d8',project:'#c5df94',violet:'#bba8e1'};
    svg.setAttribute('viewBox',`0 0 ${box.width} ${box.height}`);
    svg.innerHTML=`<defs>${Object.entries(colors).map(([c,fill])=>`<marker id="mem-arrow-${kind}-${c}" viewBox="0 0 6 6" refX="6" refY="3" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0 L6 3 L0 6" fill="none" stroke="${fill}"/></marker>`).join('')}</defs>${lines}`;
  }
  function bind(root){
    observer?.disconnect();const scope=root.querySelector('.memory-observatory');if(!scope)return;
    const maps=[...scope.querySelectorAll('.mem-diagram')];
    observer=new ResizeObserver(()=>maps.forEach(draw));maps.forEach(m=>observer.observe(m));
    requestAnimationFrame(()=>maps.forEach(draw));
    const dialog=scope.querySelector('.mem-record-dialog');let trigger,savedScroll;
    scope.querySelectorAll('[data-record]').forEach(button=>button.addEventListener('click',()=>{
      const entry=recordGuide[button.dataset.record];if(!entry)return;
      trigger=button;savedScroll={left:scrollX,top:scrollY,behavior:'instant'};
      dialog.innerHTML=`<button type="button" class="mem-record-close" aria-label="Закрыть описание">×</button><span class="mem-label">Устройство базы <code>${esc(entry.code)}</code></span><h2 id="mem-record-title" tabindex="-1">${esc(entry.title)}</h2><p>${esc(entry.text)}</p><dl>${entry.fields.map(([title,text])=>`<div><dt>${esc(title)}</dt><dd>${esc(text)}</dd></div>`).join('')}</dl>${entry.example?`<aside><span class="mem-label">Условный пример</span><p>${esc(entry.example)}</p></aside>`:''}`;
      dialog.querySelector('.mem-record-close').onclick=()=>dialog.close();dialog.showModal();dialog.scrollTop=0;dialog.querySelector('h2').focus({preventScroll:true});window.scrollTo(savedScroll);
    }));
    dialog.addEventListener('click',event=>{if(event.target!==dialog)return;const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close()});
    dialog.addEventListener('close',()=>{if(!dialog.isConnected||root.hidden)return;trigger?.focus({preventScroll:true});if(savedScroll)window.scrollTo(savedScroll)});
  }
  return {render,bind};
})();
