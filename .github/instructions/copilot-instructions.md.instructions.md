---
description: Describe when these instructions should be loaded by the agent based on task context
# applyTo: 'Describe when these instructions should be loaded by the agent based on task context' # when provided, instructions will automatically be added to the request context when the pattern matches an attached file
---

Load these instructions for any task in this repository that involves planning, coding, testing, refactoring, debugging, documentation, or review.

Core behavior:

- Always check `docs/mvp-build.md` before starting implementation to align with current build status and priorities.
- Always update `docs/mvp-build.md` after completing meaningful work to record what was implemented, fixed, tested, or deferred.
- Keep updates concise and factual (what changed, where, and current status).
- If a requested change conflicts with `docs/mvp-build.md`, call out the conflict and propose the minimal aligned path.

Documentation workflow:

- Treat `docs/mvp-build.md` as the execution log for MVP progress.
- When work is split across multiple files or services, summarize outcomes in one short entry rather than verbose notes.
- If no code change was made, do not add noise; only update the document when progress or decisions changed.

Quality expectations:

- Prefer small, verifiable changes with tests where applicable.
- Validate behavior after edits (tests or targeted checks) when possible.
- Keep changes consistent with existing project structure and conventions.
