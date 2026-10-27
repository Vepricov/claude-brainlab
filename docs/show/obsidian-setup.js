/* Public setup guide. Diagram examples never read personal notes or queues. */
window.LAB_OBSIDIAN_SETUP = (() => {
  const repository = 'https://github.com/brain-lab-research/claude-brainlab/tree/main/obsidian-setup';
  const plugins = [['Operon','3.0.1','Задачи и доски'],['Dataview','0.5.68','Представления в заметках'],['Homepage','4.4.0','Стартовый экран'],['Templater','2.19.1','Шаблоны и запуск'],['Calendar','1.5.10','Ежедневные заметки'],['Next TOC','2.4.0','Оглавление документа'],['Iconic','1.1.8','Иконки'],['File Color','1.1.0','Цвета файлов'],['Style Settings','1.0.9','Настройки темы'],['Multi-Column Markdown','0.9.1','Колонки в заметках'],['Banners','1.3.3','Баннеры'],['Checklist','2.2.14','Список чекбоксов'],['Tasks','7.23.1','Запросы к задачам'],['Zotero Integration','3.2.1','Импорт из своего Zotero']];
  function setup() {
    const {header, node, wires, section} = window.LAB_SURFACE_PAGES;
    return `<div class="sp-page sp-personal" data-surface-page="obsidian" data-obsidian-setup>
      ${header('Obsidian', 'Хранилище = дерево лаборатории', 'Свои заметки и общее знание лаборатории.<br>Одна папка, одно окно.', '◇')}
      <section class="sp-obsidian-map sp-map" data-sp-map data-sp-links='[["reading","project"],["tasks","project"],["project","diary"],["project","hermes"]]' aria-label="Что лежит вокруг вашей работы">
        ${wires}
        ${node('reading', 'Литература темы', 'Разборы статей', 'Одна страница на статью: разбор и BibTeX с ключом цитирования. Общая для всей темы.')}
        <article class="sp-personal-project" data-sp-node="project"><span class="sp-label">Копия репозитория работы</span><div class="sp-crystal" aria-hidden="true">◇</div><h2>Ваша работа</h2><p>Утверждения, рукопись и код едут в GitLab. Заметки, дневник и локальные логи закрыты от git и остаются на машине.</p><div class="sp-file-lines" aria-hidden="true"><i></i><i></i><i></i></div><small>Обычные Markdown-файлы<br>и обычный git</small></article>
        ${node('diary', 'Личное, не в git', 'Заметки и дневник', 'Черновики, планы, логи прогонов. Они синхронизируются с сервером, где работает Гермес.')}
        ${node('tasks', 'Личный план', 'Задачи и чтение', 'Две личные доски: задачи и очередь чтения. Каждая карточка — обычный файл.')}
        ${node('hermes', 'Работа агента', 'Доска Гермеса', 'Очередь, прогресс и результаты серверного агента — в заметках той работы, к которой они относятся.')}
      </section>
      <div class="sp-obsidian-note"><p>Obsidian открывает дерево лаборатории — то же, что в GitLab: направление → тема → работа, рядом литература темы, справочник, журнал и серверы. Ссылки между заметками работают и в Obsidian, и в GitLab.</p><a class="os-download sp-primary-link" href="${repository}" target="_blank" rel="noopener">Повторить у себя (GitHub) ↗</a></div>
      <section class="sp-section sp-operon">
        ${section('Личные доски', 'Свои задачи и чтение — в тех же файлах.', 'Две доски: для личных обязательств и для статей. Они помогают выбрать следующий шаг, а задачи остаются обычными файлами рядом с работой.')}
        <div class="sp-operon-lanes"><article><h3>Мои задачи</h3><div><span>Надо</span><i>→</i><span>Делаю</span><i>→</i><span>Проверка</span><i>→</i><span>Готово</span></div><p>Исполнитель, приоритет и комментарии — внутри задачи.</p></article><article><h3>Чтение</h3><div><span>Входящие</span><i>→</i><span>Очередь</span><i>→</i><span>Читаю</span><i>→</i><span>Прочитано</span></div><p>Статья идёт от находки до прочтения, отложенные видны отдельно.</p></article></div>
      </section>
      <section class="sp-section" data-hermes-guide>
        ${section('Гермес рядом с проектом', 'Агент работает. Вы видите ход.', 'Обзор обновляется сам каждые 15 минут, без модели: простой скрипт переносит статусы и комментарии с доски Гермеса в папку работы.')}
        <div class="sp-hermes-map sp-map" data-sp-map data-sp-links='[["queue","export"],["export","folder"]]'>${wires}
          ${node('queue', 'На сервере', 'Доска Гермеса', 'Задачи, сообщения и результаты серверного агента.')}
          ${node('export', 'Каждые 15 минут', 'Скрипт без модели', 'Забирает записи с сервера и переносит их как есть, ничего не додумывая.')}
          ${node('folder', 'В папке работы', 'Обзор Гермеса', 'Активная доска и история. Обзор только для чтения и в git не едет.')}
        </div>
        <div class="sp-hermes-preview"><header><span>Пример обзора · вымышленные задачи</span><span>Только просмотр</span></header><div><span class="sp-status sp-running">В работе</span><b>Сравнить три запуска</b><span>demo-server · GPU 0, 1</span></div><div><span class="sp-status sp-help">Нужна помощь</span><b>Уточнить бюджет базовой модели</b><span>Нужно выбрать лимит шагов</span></div><div><span class="sp-status">Далее</span><b>Собрать итоговый отчёт</b><span>Прогон ещё не начат</span></div></div>
        <p class="sp-small">В Obsidian карточки раскрываются: понятные даты, результат и последние сообщения. Сервер и видеокарты видны, когда их указал Гермес. Если сервер недоступен, обзор показывает последнее состояние.</p>
        <p class="sp-under-map">У каждой работы свой обзор хода Гермеса, а свои заметки лежат рядом.</p>
      </section>
      <section class="sp-section sp-setup-details">
        ${section('Повторить у себя', 'Одна команда.', 'Участнику лаборатории установщик ставит команду lab, правила агента и этот сетап и собирает дерево лаборатории. Без лаборатории тот же набор ставится в новую папку.')}
        <details class="sp-fold" data-setup-install><summary>Установка <span>Дерево лаборатории или новая папка</span></summary><div class="sp-fold-body"><p>Участник лаборатории ставит всё одной командой; дальше <code>lab sync</code> подтягивает свои работы, их литературу, <code>handbook</code>, <code>journal</code> и <code>servers</code>:</p><pre><code>git clone https://github.com/brain-lab-research/claude-brainlab
bash claude-brainlab/docs/lab/install.sh</code></pre><p>Соглашения хранилища (иконки, цвета папок, доски) лежат в самом хранилище.</p><p>Без лаборатории: установите Obsidian, Git и Python 3.10+, скачайте набор и выберите новую папку:</p><pre><code>git clone --depth 1 https://github.com/brain-lab-research/claude-brainlab.git
cd claude-brainlab/obsidian-setup
python3 install.py --vault "$HOME/My Research" --owner "Researcher"</code></pre><p>Windows PowerShell:</p><pre><code>py -3 -m pip install tzdata
py -3 install.py --vault "$env:USERPROFILE\\My Research" --owner "Researcher"</code></pre><p>В Obsidian: <b>Open folder as vault</b> → созданная папка → разрешить community plugins → <b>START HERE</b>. Рабочее пространство «Старт» открывает обе доски.</p><p>Первая задача: палитра команд → <b>Operon: Create New Operon Task</b> → название → <b>Pick a Template → Task → File</b>. Шаблон подставит ваше имя исполнителя.</p><p>Установщик создаёт только новый vault, скачивает закреплённые версии и проверяет SHA-256. Существующее хранилище меняйте выборочно, с резервной копией и при закрытом Obsidian.</p><p class="sp-small">Полный запуск набора проверен в Obsidian на macOS.</p></div></details>
        <details class="sp-fold" data-setup-plugins><summary>Тема и 14 плагинов <span>Состав и версии</span></summary><div class="sp-fold-body"><p>Border 1.13.6, три CSS-сниппета и включённый набор:</p><div class="sp-plugin-list">${plugins.map(([name,version,role]) => `<div><b>${name}</b><span>${role}</span><code>${version}</code></div>`).join('')}</div><p>File Tree Alternative 2.6.0 и Notebook Navigator 2.6.2 записаны как выключенные. Параметр <code>--include-disabled</code> скачает и их.</p></div></details>
        <details class="sp-fold" data-setup-hermes><summary>Подключение Гермеса <span>Сервер → папка работы</span></summary><div class="sp-fold-body"><p>В <code>examples/hermes-config.json</code> укажите доску Гермеса, адрес сервера и папку работы: обзор ляжет в её заметки. Один файл настроек связывает несколько работ.</p><pre><code>python3 sync_hermes.py --config /path/to/hermes-config.json</code></pre><p>Сначала проверьте один запуск. Затем включите интервал 15 минут: в наборе есть шаблоны launchd для Mac, systemd для Linux и инструкция Task Scheduler для Windows. Компьютер должен быть включён.</p><p>Скрипт только читает доску Гермеса и не меняет его задачи.</p></div></details>
      </section>
      <footer class="sp-footer"><p>Личное остаётся на машине. Общее знание уходит в GitLab предложением, задачи команды живут в репозитории работы.</p><nav><a href="#memory">Карта общего знания ↗</a><a href="#surface/gitlab">Задачи и предложения в GitLab ↗</a></nav></footer>
    </div>`;
  }
  function render(id) {
    if (['obsidian-project-memory','operon-obsidian-setup','hermes','paperscout'].includes(id)) return '<p class="os-reference"><a href="#surface/obsidian" data-obsidian-surface>Obsidian: установка, плагины и доски Гермеса ↗</a></p>';
    return '';
  }
  return {render, page:setup};
})();
