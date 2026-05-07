<!--
Thanks for the contribution! Fill out each section below. If a section
doesn't apply, write "n/a" -- don't delete it.

For larger changes, see docs/PROFESSIONAL_WORKFLOW.md and
docs/GITHUB_WORKFLOW.md before opening this PR.
-->

## Summary

<!-- 1-3 bullets describing what changed and why. Focus on the why. -->

-
-

## Linked Issue

<!-- Auto-closes the issue on merge. Always reference one. -->

Closes #

## Type of Change

- [ ] Feature (`feat:`) -- new functionality
- [ ] Bug fix (`fix:`) -- non-breaking fix
- [ ] Hotfix (`hotfix:`) -- urgent production fix
- [ ] Refactor (`refactor:`) -- internal restructuring, no user-visible change
- [ ] Tests (`test:`) -- adding or updating tests
- [ ] Docs (`docs:`) -- documentation only
- [ ] Chore (`chore:`) -- tooling, deps, config
- [ ] Performance (`perf:`) -- performance improvement

## Acceptance Criteria

<!-- Copy from the linked issue. Check each item that's verified. -->

- [ ]
- [ ]
- [ ]

## Test Plan

<!-- How was this verified? Local commands run, manual steps taken. -->

- [ ] `pytest app/tests/unit/` passes
- [ ] `pytest app/tests/integration/` passes (when applicable)
- [ ] `cd ui && npm run build` passes (when frontend changed)
- [ ] Manual verification:

## Architecture Notes

<!-- Did this respect the hexagonal architecture (see CLAUDE.md)?
     Did anything cross a layer boundary? If yes, justify here. -->

- [ ] Adapter changes go through `BaseAdapter` (no direct httpx in services)
- [ ] Storage access goes through DAOs in `app/storage/`
- [ ] API routes use the typed Pydantic models
- [ ] Celery tasks delegate to `app/services/sync_engine.py`

## Out of Scope

<!-- What this PR explicitly does NOT include. Prevents scope creep. -->

## Screenshots / Artifacts (optional)

<!-- For UI changes, attach before/after screenshots.
     For new endpoints, attach the OpenAPI snippet or curl example. -->

---

<!-- Reviewer checklist (do not edit) -->

### Reviewer checklist

- [ ] CI is green
- [ ] PR size is reasonable (< 400 lines diff, or split)
- [ ] No debug prints, commented-out code, or unlinked TODOs
- [ ] Tests cover new behavior
- [ ] Documentation updated (CLAUDE.md, README, adapter README, PROGRESS.md)
