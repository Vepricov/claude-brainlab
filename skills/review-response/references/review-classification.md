# Compatibility entrypoint: review classification

This filename is retained for legacy `rebuttal-writer` integrations. Use `concern-ledger.md` as the canonical classification contract.

Do not classify a whole review as only major, minor, typo, or misunderstanding. Split it into stable atomic concern IDs. Record concern type, severity, requested action, hidden decision test, evidence need, dependencies, status, and stance using the shared enums in `concern-ledger.md` and `agent-prompts.md`.

Before answering, ground every concern in the submitted paper and classify new evidence under `experiment-triage.md`. A concern is resolved only when the requested decision test is satisfied by traceable evidence. Otherwise mark it partial, blocked, or unresolved.
