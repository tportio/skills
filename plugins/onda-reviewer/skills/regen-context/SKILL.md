---
name: regen-context
description: onda-reviewer 의 diff-밖 가시성 컨텍스트 팩(context/repos/<owner>__<repo>.md)을 재생성/생성한다. 대상 repo 에서 onda-reviewer 오탐 패턴(사람 반박 답글)을 마이닝하고, 로컬 클론에서 컨벤션 anchor 를 갱신해 팩을 다시 쓴 뒤 검증·커밋한다. 인자로 대상 repo 를 받는다 (예: `regen-context hub`). 새 repo 온보딩, 또는 오탐이 늘거나 anchor 가 stale 해졌을 때 실행.
argument-hint: "<repo> (예: hub, 또는 owner/repo)"
---

# regen-context

Regenerate onda-reviewer's **out-of-diff visibility pack** (`context/repos/<owner>__<repo>.md`) for a target repo, so the diff-only reviewer stops false-positiving on conventions it cannot see from a PR diff. This skill *writes* the pack; the running bot only *reads* it.

`$1` = target repo — a bare name (`hub` → owner `tportio`) or `owner/repo`. If omitted, ask which repo.

## Run the runbook — single source of truth

The full executable procedure (repo-root resolution, mining, convention extraction, writing, validation, commit) lives in the onda-reviewer repo:

**`<onda-reviewer>/docs/regen-context-runbook.md`** — locally usually `~/Workspaces/tport/ai/onda-reviewer/docs/regen-context-runbook.md`.

Read it and follow it for `$1`. Do **not** re-derive the steps here — the runbook is authoritative (it covers dynamic path resolution, the no-op skip, committing only the pack file, and the push → self-deploy behavior). Architecture / why: `docs/DIFF_VISIBILITY.md` in the same repo.

## Notes
- This is the **local** entry point. The scheduled cloud routine runs the same runbook directly from the attached onda-reviewer checkout — locally-installed plugins are not available in the cloud routine env, so the runbook (in the repo), not this skill, is what both share.
- No prompt/code change is needed to add a repo — the loader is generic and the severity-gate / `❓ 확인 필요` category are repo-agnostic. Only the pack file changes.
