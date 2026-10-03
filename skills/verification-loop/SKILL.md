---
name: verification-loop
description: Select and run the checks needed to verify a code change or release in the current repository.
version: 1.1.0
---

# Verify the requested change

Start from the behavior that must hold and the repository's actual checks. Use its scripts,
configuration, and CI definitions as the authority. Consult
[stack detection](references/STACK-DETECTION.md) only when the appropriate commands are unclear.

Choose the relevant checks, not every possible check:

- A behavior change needs tests of that behavior and meaningful failure cases.
- A build, package, or interface change needs the affected build or type check.
- A UI change needs rendered inspection and relevant interactions.
- Authentication, input handling, or dependency changes may need a focused security check.
- Documentation and low-impact configuration changes need the appropriate syntax, link,
  or read-back check; a new test is not automatically useful.

Run local checks with disposable fixtures when their scope is authorized. Fix failures
caused by the requested change and rerun affected checks. Distinguish pre-existing failures
from regressions. Do not change production data or run a deployment under the name of testing.

Preserve exit status and enough output to diagnose failures. Do not hide a failing command
behind a successful `head` or `tail` pipeline. Do not install tools merely because they
appear in an example; use the repository's environment or report what is unavailable.

Once relevant checks pass, inspect the diff for unintended changes. Broaden or repeat
verification only when the change, a failure, or an unresolved concern justifies it.
No fixed 15-minute rerun or universal coverage percentage is required.

Report the checks actually run, their result, and the boundary of the conclusion.
Skipped checks are not passes; an isolated test is not a live end-to-end run.
