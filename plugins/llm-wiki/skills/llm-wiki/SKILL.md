---
name: llm-wiki
description: Search the ONDA LLM Wiki (~/Workspaces/tport/product-docs/llm-wiki) to answer questions. Read-only — browses index.md and relevant wiki pages. Use when the user asks about topics likely covered in the team's LLM knowledge base (LLM 관련 개념, 도구, 인물, 분석 등).
disable-model-invocation: false
argument-hint: "<질문>"
allowed-tools: Read, Glob, Grep
---

# LLM Wiki Skill (Search-only)

ONDA 팀 LLM Wiki를 검색해서 질문에 답한다. 쓰기·ingest·git 작업 없음 — ingest는 별도 `/ingest` 스킬을 사용한다.

## 입력

`$ARGUMENTS` — 사용자 질문

## 위키 경로

`~/Workspaces/tport/product-docs/llm-wiki`

경로가 존재하지 않으면 다음 안내 후 중단한다:

```
git clone git@github.com:tportio/product-docs.git ~/Workspaces/tport/product-docs
```

## 절차

1. `llm-wiki/index.md` Read — Sources·Concepts·Entities·Analyses 카탈로그 확인
2. 질문과 인덱스 항목을 매칭해 관련 페이지 후보 선정. 매칭이 모호하면 `Grep`으로 `llm-wiki/wiki/` 전체 검색
3. 선정 페이지 Read. 본문의 `[[위키링크]]`·`관련 페이지` 링크가 답변에 필요하면 추가 Read
4. 근거 페이지 경로를 포함해 한국어로 답변

## 규칙

- 위키 파일 수정·생성·삭제 금지 (read-only)
- 위키에 없는 내용은 "위키에 해당 내용 없음"이라고 답하고 추측하지 않는다
- 외부 웹 검색으로 위키를 우회하지 않는다
