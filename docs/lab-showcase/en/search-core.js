/* Ядро поиска витрины: один индекс на всё, что можно найти, и одно ранжирование.
 *
 * Зачем отдельный файл. Раньше поиск был размазан по app.js: узлы дерева искались вхождением
 * подстроки в название, записи — самописной суммой баллов, а решение «показать карту или
 * записи» принимала цепочка условий про вопросительные слова. Каждый новый случай лечился
 * ещё одним условием, и на «какие есть направления в дообучении» витрина отвечала тремя
 * несвязанными проектами.
 *
 * Здесь по-другому. Раздел библиотеки, подтема, научное направление, проект, утверждение и
 * статья — всё это документы одного индекса. У каждого есть поля с разными весами: название
 * весит больше аннотации, код весит много и точно. Ранжирует BM25 — та же мера, что стоит в
 * поисковых движках: частота слова в документе, редкость слова в коллекции, поправка на длину
 * документа. Списков «слов-указателей» для темы здесь нет: если человек спросил про
 * направления, слово «направление» само окажется частым в направлениях и редким в
 * утверждениях, и BM25 это учтёт.
 *
 * Один список слов всё же остался, и он про другое — про форму ответа, а не про тему.
 * Развилку «карта или записи» ядро не принимает: её принимает служба.
 *
 * Русский и английский живут вместе, потому что база двуязычна: термины записаны латиницей, а
 * спрашивают по-русски. Поэтому каждое слово попадает в индекс тремя формами — как есть, без
 * окончания и словарным английским эквивалентом.
 *
 * Файл не зависит от браузера: его подключает и страница, и набор проверок в node.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.LabSearch = api;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  // ---------------------------------------------------------------- словари

  // Русское имя → английское. Нужен не для перевода, а для того, чтобы русский запрос вообще
  // встретился с латинской записью в базе. Пары добавляются только после замера.
  const TERMS = {
    "прогрев": "warmup", "разогрев": "warmup", "затухание": "decay",
    "дообучение": "fine-tuning finetuning", "предобучение": "pretraining pretrain",
    "обучение": "training", "сходимость": "convergence", "расходимость": "divergence",
    "квантование": "quantization", "разреженность": "sparsity", "разрежённость": "sparsity",
    "оптимизатор": "optimizer", "градиент": "gradient", "безградиентный": "zeroth-order",
    "безградиентная": "zeroth-order", "безградиентное": "zeroth-order",
    "нижняя": "lower", "оценка": "bound estimate", "оценки": "bounds",
    "теорема": "theorem", "доказательство": "proof", "лемма": "lemma",
    "кривизна": "curvature", "ортогонализация": "orthogonalization",
    "низкоранговый": "low-rank", "низкоранговая": "low-rank", "низкоранговое": "low-rank",
    "адаптер": "adapter", "адаптеры": "adapters", "слияние": "merging merge",
    "память": "memory", "скорость": "speed throughput", "точность": "accuracy precision",
    "батч": "batch", "шаг": "step", "расписание": "schedule", "спектральный": "spectral",
    "внимание": "attention", "матрица": "matrix", "фишера": "fisher",
    "выкладка": "derivation", "прогон": "experiment run", "измерение": "measurement evidence",
    "утверждение": "claim hypothesis", "гипотеза": "hypothesis",
    "статья": "paper", "статьи": "papers", "проект": "project", "проекты": "projects",
    "направление": "direction", "направления": "directions",
    "раздел": "section", "разделы": "sections", "тема": "theme topic", "темы": "themes",
  };

  // Слова, которые не несут смысла в запросе к этой базе.
  const STOP = new Set([
    "и", "в", "во", "на", "по", "за", "из", "от", "до", "для", "при", "про", "над", "под",
    "что", "как", "где", "когда", "чем", "это", "этот", "эта", "эти", "тот", "так", "там",
    "или", "но", "а", "же", "ли", "бы", "не", "ни", "мы", "я", "он", "она", "они", "все",
    "всё", "есть", "быть", "был", "была", "было", "были", "нам", "мне", "наш", "наши",
    "нужно", "нужен", "можно", "какие", "какой", "какая", "каких", "сколько", "почему",
    "зачем", "the", "and", "for", "with", "that", "this", "from", "are", "was", "were",
    "does", "did", "have", "has", "our", "you", "your", "what", "which", "when", "how",
  ]);

  // ------------------------------------------------------------ токенизация

  const RU2LAT = { а: "a", б: "b", в: "v", г: "g", д: "d", е: "e", ё: "e", ж: "zh", з: "z",
    и: "i", й: "y", к: "k", л: "l", м: "m", н: "n", о: "o", п: "p", р: "r", с: "s", т: "t",
    у: "u", ф: "f", х: "h", ц: "c", ч: "ch", ш: "sh", щ: "sh", ъ: "", ы: "y", ь: "", э: "e",
    ю: "yu", я: "ya" };

  const translit = (word) => word.replace(/[а-яё]/g, (c) => (c in RU2LAT ? RU2LAT[c] : c));

  /* Очень простое усечение русских окончаний. Полноценный стеммер тут не нужен и вреден:
     термины наполовину английские, а ошибки стеммера на них дороже пользы. */
  const RU_ENDINGS = ["иями", "ями", "ами", "иях", "ях", "ах", "ого", "ему", "ому", "ыми",
    "ими", "ей", "ой", "ый", "ий", "ая", "ое", "ые", "ие", "ов", "ев", "ам", "ям", "ом",
    "ем", "ах", "ях", "ую", "юю", "ия", "ии", "ью", "ья", "ей", "у", "ю", "а", "я", "ы",
    "и", "е", "о", "ь"];

  function stem(word) {
    if (word.length <= 5 || !/[а-яё]/.test(word)) return word;
    for (const ending of RU_ENDINGS) {
      // Основа не короче шести букв: иначе «адаптации» и «адаптивность» схлопываются в
      // «адапт», и запрос про низкоранговую адаптацию поднимает записи про адаптивность.
      if (word.length - ending.length >= 6 && word.endsWith(ending)) {
        return word.slice(0, word.length - ending.length);
      }
    }
    return word;
  }

  /* Скелет слова: транслитерация без гласных. Имя метода человек пишет как слышит, и «дикаф»
     превращается в «dikaf», тогда как в базе «DyKAF» → «dykaf». Побуквенно они разные, а по
     согласным одинаковые: «dkf». Это обычный приём нечёткого сопоставления имён, и он ловит
     именно тот случай, ради которого нужен: имя собственное, записанное на слух.

     Скелет считается только для слов длиннее четырёх букв: у коротких он схлопывает разные
     слова в одно («шаг» и «шок»). И помечается решёткой, чтобы не смешаться с обычным словом. */
  function skeleton(word) {
    const latin = translit(word).replace(/[^a-z0-9]/g, "");
    if (latin.length < 5) return "";
    const bones = latin.replace(/[aeiouy]/g, "");
    return bones.length >= 3 ? "#" + bones : "";
  }

  /* Слово превращается в набор форм: само слово, его основа, английский эквивалент,
     транслитерация и скелет согласных. */
  function expand(word) {
    const out = new Set([word]);
    const base = stem(word);
    out.add(base);
    const english = TERMS[word] || TERMS[base];
    if (english) english.split(" ").forEach((x) => out.add(x));
    if (/[а-яё]/.test(word)) {
      out.add(translit(word));
      out.add(translit(base));
    }
    const bones = skeleton(word);
    if (bones) out.add(bones);
    return [...out].filter((x) => x && x.length > 1);
  }

  function tokenize(text) {
    const words = String(text || "").toLowerCase().match(/[a-zа-яё0-9][a-zа-яё0-9_-]*/g) || [];
    const out = [];
    for (const word of words) {
      if (STOP.has(word)) continue;
      if (word.length < 2) continue;
      out.push(...expand(word));
    }
    return out;
  }

  // ------------------------------------------------------------------ индекс

  const K1 = 1.2;   // насыщение по частоте слова: дальше третьего вхождения роста почти нет
  const B = 0.6;    // поправка на длину: у нас документы очень разной длины, полная (1.0) вредит

  class Index {
    constructor() {
      this.docs = [];
      this.postings = new Map();   // слово → [{doc, tf}]
      this.avgLen = 0;
    }

    /* Документ приходит полями с весами: {название: 3, аннотация: 1}. Вес умножает частоту,
       поэтому слово в названии весит как три вхождения в тексте. */
    add(payload, fields) {
      const doc = { payload, len: 0, terms: new Map() };
      for (const [text, weight] of fields) {
        for (const term of tokenize(text)) {
          doc.terms.set(term, (doc.terms.get(term) || 0) + weight);
          doc.len += weight;
        }
      }
      if (!doc.terms.size) return;
      const id = this.docs.push(doc) - 1;
      for (const [term, tf] of doc.terms) {
        let list = this.postings.get(term);
        if (!list) this.postings.set(term, (list = []));
        list.push({ id, tf });
      }
    }

    build() {
      this.avgLen = this.docs.reduce((sum, d) => sum + d.len, 0) / Math.max(1, this.docs.length);
      return this;
    }

    /* BM25 плюс два множителя, которые в поисковых системах называются boosting: по роду
       документа и по его весу в коллекции.
     *
     * Род зависит от того, насколько конкретен запрос. «Muon» — это запрос про область, и
     * человек ждёт раздел, проект, подтему: с чего начать. «Почему Muon лучше Adam на 720M» —
     * запрос про факт, и там нужна запись. Сигнал берём не из списка слов, а из самого
     * запроса: сколько в нём значимых слов и есть ли в нём код записи. Один-два слова — почти
     * всегда навигация, пять слов — почти всегда вопрос.
     *
     * Вес в коллекции — это объём узла: подраздел из 67 статей отвечает на «Muon» лучше, чем
     * одна статья про Muon, потому что за ним стоит больше. Логарифм, чтобы крупный узел не
     * задавил всё остальное.
     */
    /* options.context — коды проектов и имена разделов, которые оказались наверху выдачи.
     * Нужен потому, что слова у нас многозначные внутри одной базы: «прогрев» — это и warmup
     * в обучении, и прогрев кеша векторов в журнале службы. BM25 их не различает, а человек
     * различает мгновенно. Контекст берётся из той же выдачи: если наверху стоят проект
     * «Адаптивный warmup» и подраздел Optimization/warmup, значит спрашивают про обучение, и
     * записи оттуда весят больше, чем записи из инфраструктурного проекта.
     */
    search(query, limit = 40, options = {}) {
      /* Слова про устройство базы («подтемы», «разделы», «направления») говорят, какой
         формы ответ нужен, а не о чём он. В тематическом ранжировании они только шумят:
         те же слова стоят в аннотациях узлов, где речь идёт про устройство подраздела.
         Замер: на запросе «какие есть подтемы в PEFT» папка Optimization/optimization_rndm
         набирала 142 балла против 111 у PEFT/lora_base, потому что слово «подтемы» есть в
         её аннотации. Человек получал подтемы про Adam вместо подтем про PEFT.
         Убираем их из запроса — на ранжирование они только шумят. Если после
         этого не остаётся ничего («направления лаборатории»), ищем как есть. */
      const raw = String(query).toLowerCase().match(/[a-zа-яё0-9][a-zа-яё0-9_-]*/g) || [];
      const kept = raw.filter((w) => !MAP_WORDS.has(w));
      // Выбрасывать их совсем нельзя: «тема» и «направление» — это ещё и настоящие уровни
      // базы, и на запросе «какие темы есть по оптимизации» без них наверх лезли проекты.
      // Поэтому вес, а не удаление: структурное слово всё ещё склоняет выдачу к узлам, но
      // не перевешивает тему запроса.
      const structural = new Set();
      const askedKinds = new Set();
      for (const word of raw) {
        if (!MAP_WORDS.has(word)) continue;
        for (const t of tokenize(word)) structural.add(t);
        // Структурное слово называет уровень, на котором человек ждёт ответ. Пусть оно и
        // поднимает этот уровень, а не свои же вхождения в чужих аннотациях: «какие темы
        // есть по оптимизации» — вопрос про темы, а не про проекты, у которых слово
        // «оптимизация» стоит в описании.
        const kind = LEVEL_WORDS[word];
        if (kind) for (const k of kind) askedKinds.add(k);
      }
      const terms = tokenize(query);
      if (!terms.length) return [];
      const words = (kept.length ? kept : raw).filter((w) => !STOP.has(w) && w.length > 1);
      const hasCode = /\b[a-zа-яё]-[a-z]{2,4}-\d{2,4}\b/i.test(query);
      // 1 значимое слово → 1.0 навигации, 5 и больше → 0.0. Промежуточные значения плавные.
      const navigational = hasCode ? 0 : Math.max(0, Math.min(1, (4 - words.length) / 3));
      const NODE_KINDS = new Set(["section", "folder", "subtopic", "direction", "theme", "project"]);
      /* Служебные рода записей. Источник — это привязка «откуда взято», и заголовок у него
         шаблонный: «Помечено в работе: <участник>» повторяется десятками, «Рабочая сессия» —
         сорока с лишним. Такой документ короткий, поэтому BM25 даёт ему высокий балл, и на
         запрос по фамилии человек получал дюжину одинаковых строк вместо своих проектов.
         Понижаем: содержания в них нет, они нужны как ссылка, а не как ответ. */
      const CHORE_KINDS = new Set(["source", "journal"]);
      const context = options.context instanceof Set ? options.context : null;
      /* Точная фраза. BM25 — мешок слов: он не отличает документ, в названии которого запрос
         стоит подряд, от документа, где те же слова разбросаны. На запросе «LoRA Low-Rank
         Adaptation of Large» это стоило самой статьи LoRA: наверх выходили OLoRA, TLoRA+ и
         прочие, у которых те же слова встречаются чаще относительно длины текста.
         Человек, набравший название подряд, ищет именно его. Порог в три слова — чтобы
         «Muon» или «LoRA» не давали фразового совпадения половине базы. */
      const flatten = (text) => ` ${String(text || "").toLowerCase()
        .replace(/[^a-zа-яё0-9]+/g, " ").trim()} `;
      const phrase = words.length >= 3 ? flatten(query).trim() : "";
      const boost = (payload) => {
        const isNode = NODE_KINDS.has(payload.kind);
        const inContext = context && (context.has(payload.project) || context.has(payload.folder)
          || context.has(payload.code));
        // При навигационном запросе узел получает до +120%, запись — до −40%.
        const byKind = isNode ? 1 + 1.2 * navigational : 1 - 0.4 * navigational;
        const byChore = CHORE_KINDS.has(payload.kind) ? 0.45 : 1;
        const size = payload.size || 0;
        const bySize = isNode ? 1 + 0.25 * Math.log1p(size) : 1;
        // Запись из области, которую этот же запрос поднял наверх, весит больше. Множитель
        // умеренный: он меняет порядок внутри похожих, а далёкое не вытягивает.
        const byContext = inContext ? 1.9 : (context ? 0.55 : 1);
        const byPhrase = phrase && flatten(payload.title).includes(` ${phrase} `) ? 2.2 : 1;
        const byLevel = askedKinds.size && askedKinds.has(payload.kind) ? 1.6 : 1;
        return byKind * byChore * bySize * byContext * byPhrase * byLevel;
      };
      const N = this.docs.length;
      const scores = new Map();
      const seen = new Set();
      for (const term of terms) {
        if (seen.has(term)) continue;
        seen.add(term);
        const list = this.postings.get(term);
        if (!list) continue;
        const idf = Math.log(1 + (N - list.length + 0.5) / (list.length + 0.5));
        const weight = structural.has(term) ? 0.08 : 1;
        for (const { id, tf } of list) {
          const len = this.docs[id].len;
          const norm = tf * (K1 + 1) / (tf + K1 * (1 - B + B * len / this.avgLen));
          scores.set(id, (scores.get(id) || 0) + weight * idf * norm);
        }
      }
      return [...scores.entries()]
        .map(([id, score]) => {
          const payload = this.docs[id].payload;
          return { ...payload, score: score * boost(payload) };
        })
        .sort((a, b) => b.score - a.score)
        .slice(0, limit);
    }
  }

  // ------------------------------------------------------- сборка индекса витрины

  /* Веса полей подобраны по замеру, а не на глаз:
     - код записи весит много и матчится точно: «H-WBD-004» должен находить ровно её;
     - название весит втрое против текста: по названию узнают, в тексте уточняют;
     - у узлов дерева аннотация — основной текст, поэтому её вес выше, чем у сводки записи. */
  function build({ tree, base, lib }) {
    const index = new Index();
    const add = (payload, fields) => index.add(payload, fields);

    for (const section of tree.sections || []) {
      const sectionSize = (section.folders || []).reduce((sum, f) =>
        sum + (lib.papers || []).filter((p) => p.f === f).length, 0);
      add({ kind: "section", id: section.name, title: section.name, text: section.abstract,
            size: sectionSize },
        [[section.name, 4], [section.abstract, 1.5]]);
    }
    for (const folder of tree.folders || []) {
      const name = folder.f.split("/").pop().replace(/_/g, " ");
      const folderSize = (lib.papers || []).filter((p) => p.f === folder.f).length;
      add({ kind: "folder", id: folder.f, title: folder.f, text: folder.a, size: folderSize },
        [[folder.f.replace(/[/_]/g, " "), 4], [name, 2], [folder.a, 1.5]]);
      for (const topic of folder.sub || []) {
        add({ kind: "subtopic", id: `${folder.f}|${topic.slug}`, title: topic.t, text: topic.a,
              folder: folder.f, size: (topic.p || []).length },
          [[topic.t, 4], [topic.slug.replace(/-/g, " "), 2], [topic.a, 1.5]]);
      }
    }
    for (const direction of tree.directions || []) {
      const directionSize = (base.records || []).filter((r) => r.k === "project" &&
        (r.f || []).some((f) => ["направление", "research area"].includes(f[0]) && (direction.raw || []).includes(f[1]))).length;
      add({ kind: "direction", id: direction.slug, title: direction.t, text: direction.a,
            size: directionSize },
        [[direction.t, 4], [direction.a, 1.5], ["research area research areas", 2]]);
    }
    const themeAbstract = {};
    for (const theme of tree.themes || []) themeAbstract[theme.code] = theme.a;

    const isTheme = (record) =>
      (record.f || []).some((field) => field[0] === "kind" && field[1] === "theme");

    for (const record of base.records || []) {
      if (record.k === "project") {
        const abstract = isTheme(record) ? (themeAbstract[record.code] || "") : (record.s || "");
        const fields = (record.f || [])
          .filter((f) => !["slug", "kind"].includes(f[0]))
          .map((f) => String(f[1] || "")).join(" ");
        // Состав проекта тоже ищется: фамилия участника должна приводить к его проектам,
        // а не к служебным записям об источниках, где она просто упомянута.
        const who = record.who || {};
        const team = [...(who.leads || []), ...(who.members || [])].join(" ");
        add({ kind: isTheme(record) ? "theme" : "project", id: record.code,
              title: record.t, text: abstract, code: record.code,
              size: (record.hy || []).length, team },
          [[record.code, 6], [record.t, 4], [abstract, 1.5], [fields, 0.7],
           [team, 2.5], [isTheme(record) ? "topic topics" : "project projects", 2]]);
        continue;
      }
      add({ kind: record.k, id: record.code || record.id, title: record.t, text: record.s,
            code: record.code, project: record.pn },
        [[record.code || "", 6], [record.t, 3], [record.s, 1], [record.pn || "", 0.5]]);
    }

    for (const paper of lib.papers || []) {
      const claims = (paper.c || []).map((c) => c.s).join(" ");
      add({ kind: "paper", id: paper.id, title: paper.t, text: paper.sr || paper.s || "",
            folder: paper.f },
        [[paper.t, 3], [paper.sr || paper.s || "", 1], [claims, 0.8],
         [(paper.f || "").replace(/[/_]/g, " "), 0.6], [paper.au || "", 0.4]]);
    }

    return index.build();
  }

  // ------------------------------------------------- карта или записи
  // Витрина умеет ответить двумя способами: картой раздела («вот что тут вообще есть») и
  // списком утверждений («вот ответ на вопрос»). Выбирает она сама, и ошибка тут заметнее
  // любой ошибки ранжирования: на прямой вопрос человек получает оглавление и читает это
  // как отказ отвечать.
  //
  // Ранжированием одним эту развилку не решить, и вот почему. «Нужен ли прогрев и когда он
  // помогает» — одно содержательное слово на пять служебных. У раздела текст короче, чем у
  // утверждения, поэтому по BM25 раздел на таком запросе выигрывает честно и заслуженно.
  // Индекс отвечает на вопрос «что здесь про это», а спрашивали «правда ли это».
  //
  // Поэтому форму ответа задаёт форма вопроса, и только потом ранжирование:
  //   1. слова про устройство базы («направления», «разделы», «темы») → карта, даже в
  //      вопросительной форме: «какие есть направления в дообучении» спрашивает оглавление;
  //   2. вопросительная форма без таких слов → записи: спрашивают факт;
  //   3. всё остальное (имя метода, код, название темы) → решает ранжирование: если
  //      верхушка выдачи наполовину состоит из узлов, запрос про область.
  //
  // Это не список синонимов и не заплатка под конкретный запрос: здесь только служебные
  // слова, которые в обоих языках означают вопрос, и только имена уровней самой базы.
  /* Какой уровень базы называет структурное слово. «Темы» — это theme, «разделы» — раздел
     библиотеки и подраздел, «направления» — direction. Слова вроде «обзор» или «список»
     уровня не называют и сюда не попадают: они говорят только, что ответ должен быть картой. */
  const LEVEL_WORDS = {
    area: ["direction"], areas: ["direction"], direction: ["direction"], directions: ["direction"],
    topic: ["theme"], topics: ["theme"], theme: ["theme"], themes: ["theme"],
    section: ["section", "folder"], sections: ["section", "folder"],
    folder: ["folder"], folders: ["folder"],
    subtopic: ["subtopic"], subtopics: ["subtopic"], project: ["project"], projects: ["project"],
    "направление": ["direction"], "направления": ["direction"], "направлений": ["direction"],
    "тема": ["theme"], "темы": ["theme"], "тем": ["theme"],
    "раздел": ["section", "folder"], "разделы": ["section", "folder"],
    "разделов": ["section", "folder"],
    "подраздел": ["folder"], "подразделы": ["folder"],
    "подтема": ["subtopic"], "подтемы": ["subtopic"],
    "проекты": ["project"], "проектов": ["project"],
  };

  const MAP_WORDS = new Set([...Object.keys(LEVEL_WORDS), "overview", "structure", "list", "map", "направление", "направления", "направлений", "тема", "темы", "тем",
    "раздел", "разделы", "разделов", "подраздел", "подразделы", "подтема", "подтемы",
    "обзор", "структура", "список", "карта", "области", "область", "проекты", "проектов"]);

  const NODE_KINDS = new Set(["section", "folder", "subtopic", "direction", "theme", "project"]);

  return { build, Index, tokenize, stem, expand, TERMS, MAP_WORDS, NODE_KINDS };
});
