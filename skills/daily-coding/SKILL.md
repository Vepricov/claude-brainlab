---
name: daily-coding
description: Implement a scoped code change within an existing repository and verify the resulting behavior.
version: 1.1.0
tags: [Coding, Daily]
---

# Scoped code changes

Understand the requested behavior and the relevant existing implementation. Follow local
architecture and conventions; do not impose a new framework or read the whole repository
for a small edit.

Make the smallest change that resolves the task. Preserve unrelated edits, especially in
shared working trees. Add or change dependencies only when the task calls for them.

Choose verification by the failure mode: a focused regression test for a behavior bug,
the relevant build or type check for an interface change, and rendered inspection for a
visual change. A reversible text or configuration edit does not automatically need a new
test. Use the project's existing tests and fixtures before inventing a parallel harness.

Continue through implementation, the relevant checks, and fixes caused by the change.
Repeat or broaden checks when new evidence warrants it, not on a timer. Ask only when an
unresolved requirement or consequential action falls outside the user's authorization.

Report the resulting behavior, what was checked, and any remaining limitation. Do not
claim that a mocked check demonstrates a live integration.
