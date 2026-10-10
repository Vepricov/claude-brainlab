/* Public setup guide. Diagram examples never read personal notes or queues. */
window.LAB_OBSIDIAN_SETUP = (() => {
  const repository = 'https://github.com/brain-lab-research/claude-brainlab/tree/main/obsidian-setup';
  const plugins = [['Operon','3.0.1','Задачи и доски'],['Dataview','0.5.68','Представления в заметках'],['Homepage','4.4.0','Стартовый экран'],['Templater','2.19.1','Шаблоны и запуск'],['Calendar','1.5.10','Ежедневные заметки'],['Next TOC','2.4.0','Оглавление документа'],['Iconic','1.1.8','Иконки'],['File Color','1.1.0','Цвета файлов'],['Style Settings','1.0.9','Настройки темы'],['Multi-Column Markdown','0.9.1','Колонки в заметках'],['Banners','1.3.3','Баннеры'],['Checklist','2.2.14','Список чекбоксов'],['Tasks','7.23.1','Запросы к задачам'],['Zotero Integration','3.2.1','Импорт из своего Zotero']];
  function setup() {
    const {header, node, wires, section} = window.LAB_SURFACE_PAGES;
    return `<div class="sp-page sp-personal" data-surface-page="obsidian" data-obsidian-setup>
      ${header('Obsidian', 'Личное пространство исследователя', 'Проект, мысли и следующий шаг.<br>Всё связано, всё под рукой.', '◇')}
      <section class="sp-obsidian-map sp-map" data-sp-map data-sp-links='[["reading","project"],["tasks","project"],["project","diary"],["project","hermes"]]' aria-label="Материалы вокруг вашего проекта">
        ${wires}
        ${node('reading', 'Источники', 'Литература', 'Заметки по статьям и ссылки на свою библиотеку Zotero.')}
        <article class="sp-personal-project" data-sp-node="project"><span class="sp-label">В папке вашей работы</span><div class="sp-crystal" aria-hidden="true">◇</div><h2>Ваш проект</h2><p>Главная заметка связывает идею, планы, результаты и материалы.</p><div class="sp-file-lines" aria-hidden="true"><i></i><i></i><i></i></div><small>Обычные Markdown-файлы<br>и ссылки между ними</small></article>
        ${node('diary', 'Ход исследования', 'Заметки и дневник', 'Гипотезы, созвоны, протоколы, графики и причины решений.')}
        ${node('tasks', 'Личный план', 'Задачи и чтение', 'Две доски Operon. Те же задачи доступны в таблице и Markdown.')}
        ${node('hermes', 'Работа агента', 'Доска Hermes', 'Очередь, прогресс и результаты — рядом с тем проектом, к которому относятся.')}
      </section>
      <div class="sp-obsidian-note"><p>У проекта своя папка. Статьи живут в библиотеке, а ссылки связывают их с исследованием.</p><a class="os-download sp-primary-link" href="${repository}" target="_blank" rel="noopener">Взять сетап на GitHub ↗</a></div>
      <section class="sp-section sp-operon">
        ${section('Operon', 'Два спокойных потока.', 'Для личных обязательств и для чтения. Доски помогают выбрать следующий шаг, сохраняя задачи в обычных файлах.')}
        <div class="sp-operon-lanes"><article><h3>Мои задачи</h3><div><span>Надо</span><i>→</i><span>Делаю</span><i>→</i><span>Проверка</span><i>→</i><span>Готово</span></div><p>Исполнитель, приоритет и комментарии — внутри задачи.</p></article><article><h3>Чтение</h3><div><span>Инбокс</span><i>→</i><span>Очередь</span><i>→</i><span>Читаю</span><i>→</i><span>Прочитано</span></div><p>Отдельные состояния для отложенных статей и ожидания публикации.</p></article></div>
      </section>
      <section class="sp-section" data-hermes-guide>
        ${section('Hermes рядом с проектом', 'Агент работает. Вы видите ход.', 'Раз в 15 минут обычный Python обновляет обзор. Статусы, исходные ID и комментарии приходят из очереди Hermes.')}
        <div class="sp-hermes-map sp-map" data-sp-map data-sp-links='[["queue","export"],["export","folder"]]'>${wires}
          ${node('queue', 'На вашем сервере', 'Очередь Hermes', 'Задачи, сообщения и результаты из существующей kanban.db.')}
          ${node('export', 'По расписанию', 'Python · без LLM', 'Читает SQLite через SSH и детерминированно преобразует записи.')}
          ${node('folder', 'В папке проекта', 'Knowledge / Hermes', 'Активная доска и история. Обзор предназначен для чтения.')}
        </div>
        <div class="sp-hermes-preview"><header><span>Пример обзора · вымышленные задачи</span><span>Только просмотр</span></header><div><span class="sp-status sp-running">В работе</span><b>Сравнить три запуска</b><span>demo-server · GPU 0, 1</span></div><div><span class="sp-status sp-help">Нужна помощь</span><b>Уточнить бюджет baseline</b><span>Нужно выбрать лимит шагов</span></div><div><span class="sp-status">Далее</span><b>Собрать итоговый отчёт</b><span>Прогон ещё не начат</span></div></div>
        <p class="sp-small">В Obsidian карточки раскрываются: понятные даты, результат и последние сообщения. Сервер и GPU показываются, когда они указаны у Hermes. При недоступном сервере остаётся последний успешный снимок.</p>
        <p class="sp-under-map">Источник статусов — Hermes. Экспорт не требует Operon. У каждого проекта свой обзор; собственные заметки можно хранить рядом.</p>
      </section>
      <section class="sp-section sp-setup-details">
        ${section('Повторить у себя', 'Один набор на GitHub.', 'Настройки, тема, плагины и примеры. Свои заметки, Zotero и подключение к Hermes вы добавляете у себя.')}
        <details class="sp-fold" data-setup-install><summary>Установка из GitHub <span>В новую папку Obsidian</span></summary><div class="sp-fold-body"><p>Установите Obsidian, Git и Python 3.10+. Скачайте набор и выберите новую папку:</p><pre><code>git clone --depth 1 https://github.com/brain-lab-research/claude-brainlab.git
cd claude-brainlab/obsidian-setup
python3 install.py --vault "$HOME/My Research" --owner "Researcher"</code></pre><p>Windows PowerShell:</p><pre><code>py -3 -m pip install tzdata
py -3 install.py --vault "$env:USERPROFILE\\My Research" --owner "Researcher"</code></pre><p>В Obsidian: <b>Open folder as vault</b> → созданная папка → разрешить community plugins → <b>START HERE</b>. Рабочее пространство «Старт» открывает обе доски.</p><p>Первая задача: палитра команд → <b>Operon: Create New Operon Task</b> → название → <b>Pick a Template → Task → File</b>. Шаблон подставит ваше имя исполнителя.</p><p>Установщик создаёт только новый vault, скачивает закреплённые версии и проверяет SHA-256. Существующее хранилище меняйте выборочно, с резервной копией и при закрытом Obsidian.</p><p class="sp-small">Полный запуск набора проверен в Obsidian на macOS. Установка в приложении на Windows и Linux ещё не подтверждена.</p></div></details>
        <details class="sp-fold" data-setup-plugins><summary>Тема и 14 плагинов <span>Состав и версии</span></summary><div class="sp-fold-body"><p>Border 1.13.6, три CSS-сниппета и включённый набор:</p><div class="sp-plugin-list">${plugins.map(([name,version,role]) => `<div><b>${name}</b><span>${role}</span><code>${version}</code></div>`).join('')}</div><p>File Tree Alternative 2.6.0 и Notebook Navigator 2.6.2 записаны как выключенные. Параметр <code>--include-disabled</code> скачает и их. Автоархиватор не включён.</p></div></details>
        <details class="sp-fold" data-setup-hermes><summary>Подключение Hermes <span>Сервер → папка проекта</span></summary><div class="sp-fold-body"><p>В <code>examples/hermes-config.json</code> укажите существующие board slug, SSH alias и папку проекта. Один конфиг связывает несколько проектов.</p><pre><code>python3 sync_hermes.py --config /path/to/hermes-config.json</code></pre><p>Сначала проверьте один запуск. Затем включите интервал 15 минут: в наборе есть шаблоны launchd для Mac, systemd для Linux и инструкция Task Scheduler для Windows. Компьютер должен быть включён.</p><p>Контракт <code>kanban.db</code> относится к нашему профилю Hermes: такая очередь должна существовать на вашем сервере. Экспорт читает её и не меняет задачи Hermes или Yonote.</p></div></details>
      </section>
      <footer class="sp-footer"><p>Личные файлы остаются в вашем Obsidian. Общие утверждения — в MCP, задачи команды — в Yonote.</p><nav><a href="#memory">Карта общего знания ↗</a><a href="#surface/yonote">Как устроен Yonote ↗</a></nav></footer>
    </div>`;
  }
  function render(id) {
    if (['obsidian-project-memory','operon-obsidian-setup','hermes','paperscout'].includes(id)) return '<p class="os-reference"><a href="#surface/obsidian" data-obsidian-surface>Obsidian: установка, плагины и доски Hermes ↗</a></p>';
    return '';
  }
  return {render, page:setup};
})();
