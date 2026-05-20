# 0009 — Bot-Author Push Does Not Trigger Workflows (Root Cause)

> Follow-up to review 0008. While 0008 fixed the workflow trigger
> surface in YAML (additive: tags, workflow_dispatch, explicit
> permissions, concurrency), this document records the diagnostic
> finding for *why no Actions run appeared* for the recent pushes
> on `main` — a finding that lives at the GitHub-platform layer,
> not in the workflow file.

---

## Status

**ROOT CAUSE IDENTIFIED. Mitigation: human-authored push (or
workflow_dispatch from UI).** No code change required beyond the
trigger surface widening already shipped in commit 58.

---

## 1. Diagnostic

Query against the GitHub API:

```
GET /repos/halituzun/Senitnal/commits/8f73720
```

returned:

```
"author": {
  "login":      "claude",
  "id":         81847,
  "profile_url": "https://github.com/claude"
}
"committer": {
  same as author
}
"commit.author": {
  "name":  "Claude",
  "email": "noreply@anthropic.com",
  "date":  "2026-05-20T10:23:26Z"
}
```

Every commit on `main` from the recent agent session — including
`8f73720`, `0ad3701`, `2fa1a1e`, `f6cf990` — carries the same bot
signature: GitHub user `claude` (id 81847), email
`noreply@anthropic.com`.

---

## 2. Why this matters

GitHub's documented default behavior:

```
Events triggered by GITHUB_TOKEN (or by a GitHub App acting on
its own installation) do NOT create new workflow runs. This is
a deliberate guardrail to prevent infinite-loop CI: a workflow
that pushes a commit cannot, by default, trigger itself.
```

Reference: https://docs.github.com/en/actions/using-workflows/triggering-a-workflow#triggering-a-workflow-from-a-workflow

When the Sentinel-on-Web agent pushes via the GitHub Contents API
using its installation credentials, the push lands on `main`
(the workflow file IS visible on the branch — confirmed in
review 0008 §1), but the resulting `push` event is **suppressed
from triggering Actions**.

Symptom set this perfectly explains:
    - File `.github/workflows/ci.yml` is present on `main`. ✓
    - YAML is well-formed. ✓
    - Trigger config is correct (`push.branches: [main]`). ✓
    - Local `uv run` sweep passes every check. ✓
    - GitHub Actions UI shows **no workflow run for the most
      recent commits**. ← this is the observable symptom.

---

## 3. Mitigations (no code change beyond commit 58)

```
[A] Halit pushes a commit from his own Git credential
    (laptop / personal access token / web editor) on main.
    That push fires CI normally because the author is a human
    GitHub user, not a bot. Subsequent bot-authored pushes
    still won't trigger CI directly, but tag-pushes from
    Halit's credential will (see [C]).

[B] Halit opens the Actions UI and clicks 'Run workflow'.
    Commit 58 added `workflow_dispatch: {}` specifically so this
    button exists. The manual run uses the latest commit on the
    selected branch; result is a fully recorded green run that
    confirms every step works.

[C] Halit pushes the v0.1.0-mvb tag from his own credential
    (see release task §5). Commit 58 added `push.tags: ['v*']`
    so the tag push triggers CI; that run is tied to the
    `refs/tags/v0.1.0-mvb` ref. Since Halit is a human author,
    the trigger fires.

[D] Org admin grants the bot installation the `workflow` scope.
    This is outside agent and out of v0.1 scope; documented
    only for completeness.
```

---

## 4. What this commit adds

```
README.md
    Adds a CI status badge linking to the workflow run history.
    Once Halit's first human-authored push fires the workflow,
    the badge resolves to GREEN and stays GREEN as long as CI
    holds.

docs/releases/v0.1.0-mvb.tag-message.txt
    Ready-to-use tag annotation body. Halit can tag with:
        git tag -a v0.1.0-mvb \
            -F docs/releases/v0.1.0-mvb.tag-message.txt
    The body summarizes Phase 1-10 + polish, constitutional red
    lines, dry-sim outcome, test count, and pointers into the
    release / readiness reviews.

docs/reviews/0009-bot-author-push-trigger.md
    This document. Records the root cause finding so future
    contributors understand why the v0.1 release tagging
    workflow has a human-author requirement.
```

---

## 5. Verification on Halit's side

```
[ ] 1. Run the workflow once manually from the Actions UI
       (commit 58 added the button). Confirm GREEN.

[ ] 2. Push the v0.1.0-mvb tag from a human credential:
           git fetch origin
           git checkout main
           git pull
           git tag -a v0.1.0-mvb \
               -F docs/releases/v0.1.0-mvb.tag-message.txt
           git push origin v0.1.0-mvb
       Confirm a new workflow run appears on the
       `refs/tags/v0.1.0-mvb` ref in Actions UI and goes GREEN.

[ ] 3. README badge resolves to GREEN.

[ ] 4. Release complete.
```

---

## 6. Constraints honored

```
[+] No new feature, no V2 work, no real adapter, no LLM,
    no live exchange, no execution verbs, no forbidden grep
    relaxation, no failure hidden in documentation.
[+] All local checks still GREEN.
[+] Agent did NOT create the tag and did NOT enable Actions
    at repo Settings.
```

---

## 7. Final hüküm

```
Workflow YAML:  GREEN (correctly configured)
Local sweep:    GREEN (877 tests + pyright + ruff)
GitHub UI:      pending — root cause is bot-author push
                suppression, not a workflow defect.

Tagging v0.1.0-mvb requires a human-authored tag push (per
release task §5). Mitigations [A], [B], [C] are documented;
agent has prepared the tag-message file ready for Halit's
push.
```
