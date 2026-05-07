# GitHub Workflow

Git/PR mechanics for adapter-system. For the broader engineering process, see `docs/PROFESSIONAL_WORKFLOW.md`.

---

## 1. Branching Model

`main` is the only long-lived branch. Everything else is short-lived and named for its purpose.

| Prefix      | Use for                                | Example                                |
|-------------|----------------------------------------|----------------------------------------|
| `feature/`  | New functionality                      | `feature/stripe-adapter`               |
| `bugfix/`   | Non-urgent bug fix                     | `bugfix/coingecko-empty-response`      |
| `hotfix/`   | Urgent production fix                  | `hotfix/celery-worker-crash`           |
| `refactor/` | Internal restructuring, no user impact | `refactor/extract-http-client`         |
| `docs/`     | Docs-only change                       | `docs/adapter-readme`                  |
| `chore/`    | Tooling / deps / config                | `chore/upgrade-fastapi`                |

Rules:
- Lowercase, kebab-case after the prefix.
- One issue per branch. The branch name should make the intent obvious.
- Delete the branch after merge.

---

## 2. Branch from `main`

```bash
git checkout main
git pull origin main
git checkout -b feature/stripe-adapter
```

Always start from a freshly pulled `main`. If you've drifted, rebase rather than merge:

```bash
git fetch origin
git rebase origin/main
```

Avoid merge commits on feature branches -- they make squash-merging cleaner.

---

## 3. Commits on a Feature Branch

Commit often, but write commit messages as if each will become a permanent line in `git log` -- because the squash-merge will use one of them as the seed.

**Conventional commits** (recommended):

```
feat: add stripe adapter with charges endpoint
fix: handle 429 rate limit in coingecko adapter
refactor: extract retry logic into AssetHttpClient
docs: document scaling test setup
test: add integration test for sync_history DAO
chore: bump httpx to 0.28.1
```

Type prefixes: `feat | fix | refactor | docs | test | chore | perf | ci`.

Keep the subject under 70 chars. Body (if needed) wraps at 100.

---

## 4. Pull Requests

### Open the PR

```bash
git push -u origin feature/stripe-adapter
gh pr create --fill   # uses the PR template
```

Or with explicit body:

```bash
gh pr create --title "feat: add stripe adapter" --body "$(cat <<'EOF'
## Summary
- Implements Stripe adapter (BaseAdapter subclass) for charges endpoint
- Adds StripeConfig with api_key + base_url
- Registers adapter in factory + registry

## Test plan
- [ ] `pytest app/tests/unit/adapters/test_stripe_adapter.py`
- [ ] Integration: trigger sync via API, verify assets in MongoDB
- [ ] Manual: dashboard shows stripe instance with healthy status

Closes #N
EOF
)"
```

### PR template

The repo has `.github/PULL_REQUEST_TEMPLATE.md`. The required sections:

- **Summary** -- 1-3 bullets describing what changed and why
- **Test plan** -- checklist of how this was verified
- **Linked issue** -- `Closes #N` so merge auto-closes the issue

### Size targets

- < 200 lines diff -- ideal
- 200-400 lines -- fine
- 400+ lines -- justify it in the description, or split

### Self-review before requesting review

Read the diff yourself first. Look for:
- Debug prints / `console.log`
- Commented-out code
- TODOs without an issue link
- New dependencies (do they belong in `requirements.txt` or `requirements-dev.txt`?)
- Tests added/updated

---

## 5. CI / Quality Gates

Every PR triggers `.github/workflows/`:

- **tests.yml** -- pytest on Python 3.11 with coverage
- **lint.yml** -- black --check, flake8, mypy (continue-on-error initially)

CI must be green before merge. If CI fails:
1. Read the failure -- don't guess.
2. Fix locally and push. Don't disable hooks (`--no-verify`) to bypass.
3. Force-push only on your own branch (`git push --force-with-lease`).

---

## 6. Merging

**Squash merge** to `main`. Always.

```bash
gh pr merge --squash --delete-branch
```

Why squash:
- One issue --> one commit on `main`. Clean `git log`.
- Force-pushes during review don't leave noise on `main`.
- Bisect actually works.

The squash commit message should be the conventional-commit subject from the PR title.

---

## 7. Hotfixes

For urgent production bugs:

```bash
git checkout main
git pull
git checkout -b hotfix/celery-worker-crash
# fix, test, commit
gh pr create --title "hotfix: ..." --body "..."
# CI green -> squash merge -> deploy
```

Hotfixes still go through PR + CI. Speed comes from a small, focused diff -- not from skipping review.

---

## 8. Useful `gh` commands

```bash
gh pr list                           # open PRs
gh pr view <num>                     # PR details
gh pr checks <num>                   # CI status
gh pr diff <num>                     # see the diff
gh issue list                        # open issues
gh issue create -t "..." -b "..."    # new issue
gh issue view <num>                  # issue details
gh issue close <num> -c "comment"    # close with comment
gh run list --limit 5                # recent workflow runs
gh run view <run-id> --log-failed    # failed step logs
```

---

## 9. Release Cadence

This is currently a single-environment portfolio project. When production deployment is added:

- Tag `main` after each sprint: `v0.X.0`
- `gh release create v0.X.0 --generate-notes`
- Docker images tagged with the same version

Until then: `main` is the source of truth, and Docker Compose is the deployment unit.

---

## 10. References

- `docs/PROFESSIONAL_WORKFLOW.md` -- engineering process
- `.github/PULL_REQUEST_TEMPLATE.md` -- PR template
- `.github/workflows/tests.yml` -- test CI
- `.github/workflows/lint.yml` -- lint CI
- `github-pr-workflow` skill -- automated PR + post-merge issue handling
