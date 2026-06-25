---
name: delegation
description: "Delegation of complex or parallel tasks to adaptive sub-workers, or seeking an external opinion (peer review, security audit)."
tools:
  - spawn_adaptive_worker
---
1. If you receive a request requiring multiple complex steps, massive code exploration, or parallelizable tasks, use `spawn_adaptive_worker` to spin up sub-workers.
2. **External Review / Second Opinion**: Don't hesitate to use `spawn_adaptive_worker` to get a neutral external opinion or a code review (peer review) on your own work or design decisions. Configure the worker with appropriate persona directives (e.g., "Act as a highly critical code auditor" or "Look for logical flaws in this algorithm").
3. Formulate the sub-query in a clear and self-contained manner for the sub-worker.
4. If the task requires specific rigor, use the `directives` parameter to enforce a persona on the worker (e.g., "Act as a security expert", "Act as a software architect").
5. Always ask the sub-worker to write its findings to a file so as not to bloat your own context window.
6. **Reference Paths, Don't Copy-Paste**: When delegating the review of a file, draft, or code to a sub-worker, do not copy-paste the content into the delegation prompt. Instead, provide the file path and instruct the worker to read it.
