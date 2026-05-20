# 0008 — GitHub Actions Visibility Fix

> Release readiness review 0007 flagged a CI visibility blocker:
> local sweep GREEN, but `github.com/halituzun/Senitnal/actions`
> shows no workflow run for the latest pushes on `main`.
> v0.1.0-mvb tag is **withheld** until this is closed.

---

## Status

**FIX SHIPPED in code.**
**Halit confirmation required for UI visibility.**

Local sweep verified GREEN at every push; agent does not have
permission to enable Actions at the repo Settings level. The
workflow file change in this commit makes CI:

```
- trigger on push to main (already there)
- trigger on pull_request to main (already there)
- trigger on tag pushes matching v* (NEW — covers v0.1.0-mvb)
- trigger via manual workflow_dispatch (NEW — UI re-run button)
- declare explicit read-only permissions
- declare per-ref concurrency (cancel duplicate in-flight runs)
```

These are additive changes; no existing trigger was removed.

---

## 1. What was already correct

```
File location:     .github/workflows/ci.yml on main
File on main:      confirmed via GitHub API (SHA 9dd934de…)
Trigger:           push.branches: [main] + pull_request.branches: [main]
Steps:             7 checks (ruff check + ruff format --check +
                   pyright + pytest + forbidden imports +
                   forbidden outputs + uv install)
Path filters:      none (every push to main is in scope)
Workflow disabled  no (file present, well-formed YAML)
  at file level:
```

---

## 2. What this commit adds

```yaml
on:
  push:
    branches: [main]
    tags: ['v*']            # NEW
  pull_request:
    branches: [main]
  workflow_dispatch: {}     # NEW

permissions:                # NEW (explicit, lowest privilege)
  contents: read

concurrency:                # NEW
  group: ci-${{ github.ref }}
  cancel-in-progress: true
```

Effect:
    - `git push origin v0.1.0-mvb` will fire CI on the tag (was
      previously silent — tag pushes did not match `branches: [main]`)
    - `gh workflow run CI` or the "Run workflow" UI button on
      Actions tab can manually fire the workflow on any branch
    - explicit permissions block makes the workflow's privilege
      surface visible in the Actions UI
    - concurrency prevents redundant runs from queuing when
      multiple commits land in quick succession

---

## 3. Why no Actions run may have appeared (common causes)

If after pushing this commit the GitHub Actions UI still shows
no workflow runs, the cause is at the GitHub account / org / repo
configuration layer — outside the workflow YAML itself. Most
likely candidates, in order of probability:

```
[A] Actions disabled at the repo level
    Repo Settings > Actions > General > Actions permissions
    Must be one of:
        - "Allow all actions and reusable workflows"
        - "Allow halituzun, and select non-halituzun, actions and
           reusable workflows" with both astral-sh/setup-uv@v3
           and actions/checkout@v4 in the allow-list
    NOT:
        - "Disable actions"

[B] Workflow disabled by GitHub due to long repo inactivity
    GitHub auto-disables workflows after 60 days with no commits.
    The Actions UI shows a yellow "This workflow was disabled
    because there has been no repository activity" banner.
    Fix: click "Enable workflow" once.

[C] Pushing token lacks workflow scope
    If commits were pushed via a token that does not have the
    `workflow` scope, GitHub still ACCEPTS the push (file lands
    on the branch) but does NOT trigger workflow runs from that
    push. Subsequent pushes from a token WITH workflow scope
    DO trigger runs normally.
    Diagnostic: this commit (which touches .github/workflows/ci.yml)
    would itself be REJECTED if the token completely lacked
    workflow scope. If the push succeeds AND no run appears, the
    cause is probably [A] or [B], not this.

[D] Branch protection blocking workflow file changes
    Repo Settings > Branches > main > "Restrict pushes that
    create files" or similar. Rare.

[E] Organization-level Actions policy restricting third-party
    actions. The workflow uses actions/checkout@v4 (GitHub-owned)
    and astral-sh/setup-uv@v3 (third-party). If an org allow-list
    exists, astral-sh/setup-uv@v3 must be on it.
```

---

## 4. Verification checklist for Halit

After this commit lands on `origin/main`:

```
[ ] 1. Open https://github.com/halituzun/Senitnal/actions

[ ] 2. Expect to see a "CI" workflow listed in the left sidebar.

       If MISSING and the page says "No workflows":
       --> Actions is disabled at the repo level (cause [A]).
           Fix: Settings > Actions > General > set Actions
           permissions to "Allow all actions and reusable
           workflows" or equivalent, save, return to Actions tab.

[ ] 3. Click on the "CI" workflow.

       If a yellow banner says "This workflow was disabled":
       --> Cause [B]. Click "Enable workflow".

[ ] 4. Click the "Run workflow" button (top right, branch=main),
       click the green confirmation button.

       Expect: a new run starts within ~30s. Watch it go green.

       If no "Run workflow" button:
       --> workflow_dispatch trigger didn't register. Cause
           probably [A] or [E]. Recheck Settings > Actions.

[ ] 5. Once the manual run is GREEN, push a small no-op commit
       on main (e.g. README typo fix). Expect a new CI run.

       If the push lands but no new run appears:
       --> Cause [C]: pushing token lacks workflow scope.
           Halit may need to push from a different credential
           or reconfigure the integration that's pushing.

[ ] 6. Once a push-triggered run is GREEN, the visibility blocker
       is closed and v0.1.0-mvb is safe to tag (per review 0007 §8).
```

---

## 5. Tag the release

Once steps 1-6 are all checked off:

```bash
git fetch origin
git checkout main
git pull
git tag -a v0.1.0-mvb -m "Sentinel Minimum Viable Brain v0.1"
git push origin v0.1.0-mvb
```

With the new `tags: ['v*']` trigger this push will fire CI on
the tag. Expect a GREEN run named "CI" on the
`refs/tags/v0.1.0-mvb` ref. Halit can confirm via:

```bash
gh run list --workflow=ci.yml --branch=v0.1.0-mvb
```

or open the Actions tab and filter by ref.

---

## 6. Constraints honored

```
[+] No new feature
[+] No V2 work
[+] No real adapter
[+] No live exchange code
[+] No LLM integration
[+] No execution verbs added
[+] No forbidden grep relaxation
[+] No failure hidden in documentation
[+] All local checks still GREEN
```

Workflow trigger surface was TIGHTENED-by-addition (more
fire-paths), not relaxed.

---

## 7. Final hüküm

```
Workflow trigger surface fixed in code.
Tag is still WITHHELD until §4 checklist completes on GitHub UI.
The agent did not — and cannot — tag, push the tag, or enable
Actions at the repo Settings level. Those steps are explicitly
Halit's per release task §5.
```
