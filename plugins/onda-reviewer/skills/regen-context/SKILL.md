---
name: regen-context
description: onda-reviewer 의 diff-밖 가시성 컨텍스트 팩(context/repos/<owner>__<repo>.md)을 재생성/생성한다. 대상 repo 에서 onda-reviewer 오탐 패턴(사람 반박 답글)을 마이닝하고, 로컬 클론에서 컨벤션 anchor 를 갱신해 팩을 다시 쓴 뒤 검증한다. 인자로 대상 repo 를 받는다 (예: `regen-context hub`). 새 repo 온보딩, 또는 오탐이 늘거나 anchor 가 stale 해졌을 때 실행.
argument-hint: "<repo> (예: hub, 또는 owner/repo)"
---

# regen-context

Regenerate (or create) onda-reviewer's **out-of-diff visibility pack** for a target repo. The pack tells the diff-only reviewer about repo conventions it cannot see from a PR diff, so it stops emitting false-positive 🚫/⚠️ findings. This skill *writes* the pack; the running bot only *reads* it.

**Canonical reference (read first):** `~/Workspaces/tport/ai/onda-reviewer/docs/DIFF_VISIBILITY.md` — the architecture, the runtime injection path, the pack format, and this method. This SKILL is the executable wrapper; that doc is the source of truth. If they disagree, the doc wins and should be updated.

## Argument

`$1` = target repo. Accepts a bare name (`hub` → assume owner `tportio`) or `owner/repo`. If omitted, ask which repo.

## Paths (verify with `ls` before starting)

- onda-reviewer repo (always): `~/Workspaces/tport/ai/onda-reviewer`
- pack output: `<onda-reviewer>/context/repos/<owner>__<repo>.md`
- target repo local clone (anchor source of truth): search under `~/Workspaces/tport/` — e.g. hub is at `~/Workspaces/tport/gds/hub`. If not found, ask for the clone path. Pull it ff-only if stale (`git -C <clone> pull --ff-only`).

Prereqs: `gh` authenticated (read access to the target repo); semble available for the clone.

## Procedure (see DIFF_VISIBILITY.md §"Regenerating a pack" for rationale)

### 1 — Mine false-positive patterns (delegate to a read-only subagent)
Enumerate recent PRs the bot reviewed and collect onda-reviewer findings + the **human reply** refuting them:
- `gh api 'repos/<owner>/<repo>/pulls?state=all&per_page=100&sort=updated&direction=desc' --jq '.[].number'` (cap ~30–60 that actually have onda-reviewer[bot] reviews; report how many examined).
- per PR: `gh api repos/<owner>/<repo>/pulls/<n>/reviews` (filter `onda-reviewer[bot]`; read findings + the 증분 "반영 상태" tables) and `.../pulls/<n>/comments` (use `in_reply_to_id` to link human replies). Refutation signals: "✅ 이미 충족", "✅ 등록됨", "보류 (의도적 유지)" with file evidence.
- Categorize. A category earns a pack card when it recurs (≥2 PRs) AND a pre-extracted out-of-diff fact would prevent it. Absorb only the ranked catalog.

### 2 — Extract/refresh conventions + anchors from the clone
For each card, re-verify the convention and its anchor against the **current** clone (anchors drift). Use semble (`repo=<clone>`) then Read. Record `file › symbol` (line is a hint only). Drop cards whose convention no longer holds; add newly-recurring ones. For a brand-new repo, derive the cards from the Step-1 catalog + a structural read of the repo (validation/middleware, auth mounting, ORM/association, error/response contract, DI/module system, config).

### 3 — Write the pack
Write `<onda-reviewer>/context/repos/<owner>__<repo>.md` in the format of `context/repos/tportio__hub.md`: AUTO-GENERATED comment (source HEAD sha via `git -C <clone> rev-parse --short HEAD` + date) → how-to-use preamble → layout → convention cards (one-line / `file › symbol` anchor / "FP it prevents" / stability) → migration-parity posture. Terse, English (injected into every review prompt).

### 4 — Validate
Before running, confirm `<owner>`/`<repo>` are plain slugs (`[A-Za-z0-9._-]`) and `<pr#>` is numeric — pass them as separate, quoted args, never interpolated into a shell string. Then:
`cd ~/Workspaces/tport/ai/onda-reviewer && node scripts/validate-hub-context.js <pr#> <owner> <repo>` — confirms the pack loads and assembles into the WITH-pack prompt only. Deeper: replay one FP-heavy PR before/after (two reviewers given the with/without-pack prompts) and confirm the known FPs drop or downgrade to ❓ while true positives survive.

### 5 — Deploy
`git -C ~/Workspaces/tport/ai/onda-reviewer diff context/repos/` → review. Then commit + push `main` (self-deploy ships it; see `docs/DEPLOY.md`). **Get user approval before commit/push.** If run unattended (e.g. a scheduled batch), open a PR instead of pushing to `main` so a human gates the deploy.

## Notes
- No prompt/code change is needed to add a repo — `loadContextPack` is generic and the `<out_of_diff_severity_gate>` rule + `❓ 확인 필요` category are repo-agnostic. Only the pack file is new.
- This skill is intended to run periodically (high-churn repos go stale). It is NOT wired to a scheduler yet — invoke manually, or wire a routine that opens a PR.
