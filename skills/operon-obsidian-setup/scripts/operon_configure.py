#!/usr/bin/env python3
"""Configure Operon data.json for the project/task setup (idempotent).

Usage: python3 operon_configure.py /path/to/vault OWNER
Backs up data.json before writing. Safe to re-run. Applies cleanly to a fresh
Operon install; on an existing install it MERGES (replaces the status pipeline,
appends the project field/filter if absent). Restart Obsidian afterwards.
"""
import json
import shutil
import sys
import time
from pathlib import Path

if len(sys.argv) < 3:
    sys.exit("usage: operon_configure.py <vault> <owner>")
vault = Path(sys.argv[1]).expanduser().resolve()
owner = sys.argv[2]
dj = vault / ".obsidian/plugins/operon/data.json"
if not dj.exists():
    sys.exit(f"not found: {dj} (install & open Operon once first)")

d = json.loads(dj.read_text(encoding="utf-8"))
shutil.copy2(dj, dj.with_name(f"data.json.bak-{int(time.time())}"))

# --- 1. status pipeline (single pipeline named "Project") ---
PIPELINE = {
    "version": 1,
    "pipelines": [{
        "id": "pl_project", "name": "Project",
        "statuses": [
            {"id": "st_project_brainstorming", "label": "Brainstorming", "color": "#239eaf",
             "isFinished": False, "isCancelled": False, "isScheduledTarget": False,
             "isTrackingTarget": False, "propertyMapping": None},
            {"id": "st_project_planned", "label": "Planned", "color": "#ff7b0f",
             "isFinished": False, "isCancelled": False, "isScheduledTarget": True,
             "isTrackingTarget": False, "propertyMapping": None},
            {"id": "st_project_in_progress", "label": "InProgress", "color": "#f31212",
             "isFinished": False, "isCancelled": False, "isScheduledTarget": False,
             "isTrackingTarget": True, "propertyMapping": None},
            {"id": "st_project_finished", "label": "Finished", "color": "#787878",
             "isFinished": True, "isCancelled": False, "isScheduledTarget": False,
             "isTrackingTarget": False, "propertyMapping": None},
            {"id": "st_project_paused", "label": "Paused", "color": "#1a7ebc",
             "isFinished": False, "isCancelled": False, "isScheduledTarget": False,
             "isTrackingTarget": False, "propertyMapping": None},
            {"id": "st_project_dropped", "label": "Dropped", "color": "#1f1f1f",
             "isFinished": False, "isCancelled": True, "isScheduledTarget": False,
             "isTrackingTarget": False, "propertyMapping": None},
        ],
        "description": "Outcome-based work with a clear deliverable.",
    }],
    "defaultPipelineName": "Project",
}
tax = d.setdefault("taxonomy", {})
tax["pipelines"] = PIPELINE

# --- 2. custom multi-value field `project` ---
km = tax.setdefault("keyMappings", {})
custom = km.setdefault("custom", [])
if not any(c.get("canonicalKey") == "project" for c in custom):
    custom.append({
        "canonicalKey": "project", "visiblePropertyName": "project", "type": "list",
        "sync": "yes", "enabled": True, "hideInFileTaskView": False, "icon": "folders",
        "isSystem": False, "isInternal": False, "customOrder": 0,
        "showInEditor": True, "showInCreator": True, "showInChips": False,
        "showInKanbanSwimlane": False,
    })

# --- 3. excluded folders ---
s = d.setdefault("settings", {})
ex = s.setdefault("excludedFolders", [])
for f in ("Operon/Archives", "Operon/Projects"):
    if f not in ex:
        ex.append(f)

# --- 4. Task Creator: folders + default file-task template ---
ui = d.setdefault("ui", {}).setdefault("taskCreationProfile", {})
ui["fileTasksFolder"] = "Operon/Tasks"
ui["fileTaskTemplateFolder"] = "Operon/Templates"
ui["taskCreatorDefaultFileTemplateId"] = "folder-file-task-template:Operon/Templates/Task.md"

# --- 5. native auto-archive OFF (external cron handles day-boundary archiving) ---
auto = d.setdefault("automation", {}).setdefault("taskAutomationPolicy", {})
auto["fileTaskAutoArchiveEnabled"] = False
auto["fileTaskArchiveFolder"] = "Operon/Archives"

# --- 6. "my tasks" filter (assignees anyContains OWNER) ---
views = d.setdefault("views", {})
filters = views.setdefault("filters", {"version": 1, "filterIds": [], "itemsById": {}})
filters.setdefault("filterIds", [])
filters.setdefault("itemsById", {})
if "fs_mytasks" not in filters["itemsById"]:
    filters["filterIds"].append("fs_mytasks")
cond = {"id": "cond_mine", "field": "assignees", "fieldType": "list",
        "operator": "anyContains", "value": owner}
filters["itemsById"]["fs_mytasks"] = {
    "id": "fs_mytasks", "name": "Мои задачи", "icon": "user",
    "rootGroup": {"id": "fg_fs_mytasks", "logic": "all", "children": [cond]},
    "sorts": [{"field": "priority", "order": "asc"}],
    "matchLogic": "all", "conditions": [cond],
    "sortBy": "priority", "sortOrder": "asc",
}

dj.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"configured: {dj}")
print("restart Obsidian to apply.")
