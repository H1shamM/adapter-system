# User Story Template

Use this template when creating a GitHub issue for new work.

For automated story creation, use the `orqestra-create-user-story` skill -- it produces a more thorough INVEST-structured story with linked sub-tasks. This template is the manual / lightweight version for smaller scope.

---

## How to use

1. Open a new GitHub issue.
2. Paste the structure below.
3. Fill in each section. If a section doesn't apply, write "n/a" -- don't delete it.
4. Add labels: `story`, plus area (`adapter`, `api`, `frontend`, `infra`, `tests`, `docs`).
5. Add to the current sprint via `gh issue edit <num> --milestone "Sprint N"`.

---

## Template

```markdown
## Story

As a [user role / persona],
I want [capability],
so that [outcome / value].

## Context

[Why this matters now. Link to PROGRESS.md sprint slot if relevant.
Link to any related issues or PRs.]

## Acceptance Criteria

- [ ] [Specific, observable behavior #1]
- [ ] [Specific, observable behavior #2]
- [ ] [Specific, observable behavior #3]

## Technical Approach (optional)

[Sketch the implementation. Which files change? Which abstractions?
Cite `app/...` paths. Note any architectural decisions.]

## Sub-Tasks

- [ ] **Backend**: [adapter / API / storage / task changes]
- [ ] **Frontend**: [UI changes, new components, API client updates]
- [ ] **Tests**: [unit + integration coverage]
- [ ] **Docs**: [README, adapter README, CLAUDE.md updates]

## Definition of Done

- [ ] All acceptance criteria checked
- [ ] Tests pass locally (`pytest` + `npm run build`)
- [ ] CI is green
- [ ] PR opened with `Closes #<this-issue>`
- [ ] Self-reviewed
- [ ] `docs/PROGRESS.md` updated if this completes a sprint slot

## Out of Scope

[What this story explicitly does NOT include. Prevents scope creep.]

## Links

- Related: #
- PR: #
- Design: [optional doc link]
```

---

## Example (filled in)

```markdown
## Story

As a developer integrating a new SaaS API,
I want a contract test suite that every adapter must pass,
so that I can be confident a new adapter satisfies the BaseAdapter interface
without reading every existing adapter's tests.

## Context

Sprint 4, Story 4.4. The `BaseAdapter` ABC enforces method signatures but not
behavior (e.g., `connect()` should be idempotent, `normalize()` should never
mutate input). A shared parametrized test suite would catch regressions across
all adapters when the contract evolves.

## Acceptance Criteria

- [ ] `app/tests/contract/test_adapter_contract.py` exists
- [ ] Test is parametrized over every adapter in `ADAPTER_REGISTRY`
- [ ] Verifies: connect-fetch-normalize round-trip with mocked HTTP returns
      `List[NormalizedAsset]`
- [ ] Verifies: `normalize()` is pure (input dict not mutated)
- [ ] Verifies: re-calling `connect()` does not raise

## Technical Approach

- New file `app/tests/contract/test_adapter_contract.py`
- Uses `pytest.mark.parametrize` over `ADAPTER_REGISTRY.keys()`
- Each adapter provides a `mock_response` fixture (add to existing test files)
- Pattern from: `app/tests/integration/test_sync_history.py`

## Sub-Tasks

- [ ] **Backend**: Add contract test file
- [ ] **Backend**: Each adapter exports a `mock_response` fixture
- [ ] **Tests**: `pytest app/tests/contract/` runs in CI
- [ ] **Docs**: Update `add-adapter` skill to mention contract requirement

## Definition of Done

- [ ] All acceptance criteria checked
- [ ] CI green
- [ ] PR closes this issue

## Out of Scope

- Performance assertions (covered separately by `perf_test` adapter)
- End-to-end MongoDB write verification (covered by integration tests)

## Links

- Related: #N (BaseAdapter ABC)
```

---

## See also

- `docs/BUG_REPORT_TEMPLATE.md` -- for bugs (different shape)
- `docs/PROFESSIONAL_WORKFLOW.md` -- sprint flow context
- `orqestra-create-user-story` skill -- automated alternative
