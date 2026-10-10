<%*
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

// Let Homepage and community views finish restoring before cleanup.
await delay(2000);

// Community ribbon buttons register after workspace.json is loaded, so reapply
// the accepted visibility after all plugins are ready.
const ribbonHiddenItems = {
    "switcher:Меню быстрого перехода": false,
    "graph:Граф": false,
    "canvas:Создать новый холст": true,
    "daily-notes:Сегодняшняя заметка": true,
    "templates:Вставить шаблон": true,
    "command-palette:Открыть палитру команд": true,
    "workspaces:Пространства": true,
    "bases:Создать новую базу": true,
    "homepage:Open homepage": true,
    "templater-obsidian:Templater": true,
    "iconic:Открыть свод правил": true,
    "operon:Create New Operon Task": false,
    "operon:Operon Filter View": true,
    "operon:Task Finder": true,
    "operon:Operon Calendar": true,
    "operon:Operon Kanban": false,
    "operon:Operon Table": true,
    "operon:Open Pinned Tasks": true
};

app.workspace.leftRibbon?.load({ hiddenItems: ribbonHiddenItems });
app.workspace.requestSaveLayout();

// Remove both the old and current Checklist view types.
["obsidian-checklist-plugin", "todo"].forEach(type => {
    app.workspace.getLeavesOfType(type).forEach(leaf => leaf.detach());
});

// Open shared TODO note in right sidebar
const filePath = "general/todo.md";

let file = app.vault.getAbstractFileByPath(filePath);
if (!file) {
    file = await app.vault.create(filePath, "# TODO\n\n- [ ] Inbox\n");
}

// Only open if not already open anywhere
const isOpen = app.workspace.getLeavesOfType("markdown")
    .some(l => l.view?.file?.path === filePath);

if (!isOpen) {
    const leaf = app.workspace.getRightLeaf(true);
    if (leaf) await leaf.openFile(file, { active: false });
}

// Initialize both lazy Operon tab titles, then leave Reading active.
const kanbanLeaves = app.workspace.getLeavesOfType("operon-kanban-view");
const byPreset = presetId => kanbanLeaves.find(leaf =>
    leaf.getViewState()?.state?.presetId === presetId
);
const personal = byPreset("kanban-preset-personal");
const reading = byPreset("kanban-preset-reading");

if (personal && reading) {
    app.workspace.setActiveLeaf(personal, { focus: false });
    await delay(50);
    app.workspace.setActiveLeaf(reading, { focus: false });
}

%>
