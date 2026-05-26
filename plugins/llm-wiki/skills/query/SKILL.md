---
name: query
description: Search the ONDA LLM Wiki (tport/product-docs/llm-wiki) to answer questions. Read-only — browses index.md and relevant wiki pages. Use when the user asks about topics likely covered in the team's LLM knowledge base (LLM 관련 개념, 도구, 인물, 분석 등).
disable-model-invocation: false
argument-hint: "<질문>"
allowed-tools: Read, Glob, Grep
---

# LLM Wiki Query Skill (Search-only)

ONDA 팀 LLM Wiki를 검색해서 질문에 답한다. 쓰기·ingest·git 작업 없음 — ingest는 별도 `/ingest` 스킬을 사용한다.

## 입력

`$ARGUMENTS` — 사용자 질문

## 위키 경로 해석

위키는 `tport/product-docs` 리포의 `llm-wiki/` 디렉토리에 있다. 다음 순서로 해석한다:

1. 환경변수 `$LLM_WIKI_PATH`
2. 환경변수 `$TPORT_HOME` → `$TPORT_HOME/product-docs/llm-wiki`
3. 후보 경로 순차 확인 (Glob 으로 존재 여부 검사):
   - `~/Workspaces/tport/product-docs/llm-wiki`
   - `~/dev/tport/product-docs/llm-wiki`
   - `~/code/tport/product-docs/llm-wiki`
   - `~/projects/tport/product-docs/llm-wiki`
4. 모두 실패 시 사용자에게 경로 문의 후 중단

`product-docs` 리포가 없으면 다음 안내 후 중단한다 (`<your-tport-clone>` 은 사용자 환경에 맞춰 치환):

```
git clone git@github.com:tportio/product-docs.git <your-tport-clone>/product-docs
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
