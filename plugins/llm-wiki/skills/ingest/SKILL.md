---
name: ingest
description: 새로운 원천 자료(회의록, 외부 문서, Notion 내보내기 등)를 ONDA product-docs 위키에 통합한다. 원본 보존, 요약 페이지 생성, 관련 문서 업데이트, 인덱스·로그 기록까지 체계적으로 수행. tport 어느 디렉토리에서든 호출 가능.
disable-model-invocation: false
argument-hint: "<자료 경로 또는 설명>"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# Ingest 워크플로우

새로운 원천 자료를 읽고, 가공하여, ONDA product-docs 위키에 체계적으로 통합한다.

## Phase 0: product-docs 경로 해석 및 cwd 전환

이 스킬은 `product-docs` 리포 루트를 기준으로 동작한다 (모든 경로 상대). 호출 시 cwd 가 product-docs 가 아닐 수 있으므로 다음 순서로 해석한 뒤 `cd` 한다:

1. `$PRODUCT_DOCS_PATH` 환경변수
2. `$TPORT_HOME` 환경변수 → `$TPORT_HOME/product-docs`
3. 후보 경로 순차 확인:
   - `~/Workspaces/tport/product-docs`
   - `~/dev/tport/product-docs`
   - `~/code/tport/product-docs`
   - `~/projects/tport/product-docs`
4. 모두 실패 시 사용자에게 경로 문의 후 중단

해석된 경로에 `cd` 한 뒤 `git pull origin main --ff-only` 로 최신화.

## 트리거 조건

- 사용자가 원천 자료(회의록, 외부 문서, Notion 내보내기, 이메일, 웹 클리핑 등)를 제공할 때
- "인제스트해줘", "이 자료 반영해줘", "위키에 통합해줘" 등의 요청
- 파일을 첨부하면서 "정리해줘", "프로젝트에 넣어줘" 등의 요청

## 사전 확인

인제스트를 시작하기 전에 사용자에게 확인:

1. **대상 프로젝트/제품**: 어느 프로젝트 또는 제품에 반영할 것인지
2. **문서 유형**: 어떤 유형의 문서로 생성할 것인지 (회의록, 요구사항, 참고 자료 등)
3. **담당자**: `_workspace/` 내 어느 담당자 폴더에 원본을 보존할 것인지

사용자가 명시하지 않은 경우, 자료 내용을 파악한 뒤 적절한 위치를 제안한다.

## 실행 절차

### 1단계: 원천 자료 보존

```
_workspace/[담당자]/[프로젝트명]/raw/
```

- 원본 파일을 위 경로에 저장 (파일명은 원본 유지 또는 날짜 기반)
- `raw/` 폴더가 없으면 생성
- **불변 원칙**: 저장된 원본은 절대 수정하지 않음
- llm-wiki ingest 의 경우 원본은 `llm-wiki/raw/YYYY-MM-DD-[slug].md`

### 2단계: 내용 파악 및 논의

- 자료를 읽고 핵심 내용을 사용자에게 요약 보고
- 주요 포인트, 결정 사항, 액션 아이템 등을 정리
- 기존 위키 문서와 상충하거나 업데이트가 필요한 부분 식별
- 사용자와 논의하여 강조할 내용, 생략할 내용 결정

### 3단계: 위키 문서 생성

대상 프로젝트/제품 폴더에 적절한 문서 생성:

- `CLAUDE.md` 의 파일명 규칙 준수
- 해당 문서 유형의 템플릿 참고 (`templates/project-templates/` 또는 `templates/product-templates/`)
- 문서 상태는 `DRAFT` 로 시작
- llm-wiki ingest 의 경우 `llm-wiki/wiki/{sources,concepts,entities,analyses}/` 하위에 카테고리별로 생성

### 4단계: 관련 문서 업데이트

기존 문서에서 새 자료와 관련된 내용을 업데이트:

- 교차 참조(링크) 추가
- 상충하는 내용이 있으면 명시적으로 표시
- 프로젝트 README 의 마일스톤, 진행 상황 등 갱신
- 프로젝트-제품 양방향 링크 확인 및 추가

### 5단계: 인덱스 갱신

- 루트 `INDEX.md` 업데이트 (해당하는 경우)
- 프로젝트/제품 `README.md` 의 문서 목록에 새 문서 추가
- `products/INDEX.md` 업데이트 (해당하는 경우)
- **llm-wiki ingest 인 경우**: `llm-wiki/index.md` 에 sources/concepts/entities/analyses 항목 추가

#### 5-1. 루트 `llms.txt` 조건부 갱신

`llms.txt` 는 에이전트용 **파일 단위** 사이트맵이므로, 다음 **범주의 신규 파일이 생성된 경우에만** 함께 갱신한다:

- `products/*/README.md`, `products/*/skill.md` (신규 제품 · capability card)
- `policies/*` 신규 정책 최상위 문서
- `apis/*/README.md` (신규 파트너 API 문서)
- `_shared/strategy/*.md` (신규 전략 문서)
- 기타 에이전트가 직접 참조할 만한 루트/최상위 문서

**갱신 내용:**
- 해당 섹션에 `[경로](경로) — 설명 · ~N.NK` 형식으로 추가
- 토큰 추정치는 `chars ÷ 2.5` (한/영 혼합 기준) 를 `~N.NK` 로 반올림

**갱신 제외 (llms.txt 는 건드리지 않음):**
- `llm-wiki/wiki/*` 내부 페이지 (이미 `llm-wiki/index.md` 가 처리)
- 프로젝트 하위 문서(`projects/*/requirements/`, `specs/`, `meetings/` 등)
- changelog, 회의록 등 반복 생성 문서

> **CLAUDE.md 는 절대 수정하지 않는다.** CLAUDE.md 는 규칙 문서이며 카탈로그가 아니다. 수정은 사용자의 명시적 승인이 필요한 보호 대상.

### 6단계: Changelog 기록

해당 프로젝트/제품의 `changelog/CHANGELOG-[년도].md` 에 변경 기록:

- 파일이 없으면 `templates/` 의 changelog 템플릿을 참고하여 생성
- 날짜, 문서 경로, 변경 내용 요약, 변경자 기록

### 7단계: 활동 로그 기록

`LOG.md` (또는 llm-wiki ingest 의 경우 `llm-wiki/log.md`) 상단에 인제스트 엔트리 추가:

```markdown
## [YYYY-MM-DD] ingest | [자료 제목]

- `_workspace/[담당자]/[프로젝트명]/raw/[파일명]` 에 원본 저장
- `[생성된 문서 경로]` 생성
- `[업데이트된 문서 경로]` 업데이트
- `[changelog 경로]` 기록
```

## 완료 보고

모든 단계 완료 후 사용자에게 요약 보고:

- 생성된 문서 목록 (경로 포함)
- 업데이트된 기존 문서 목록
- `llms.txt` 갱신 여부 (갱신 시 추가된 항목 명시)
- 주의사항 또는 후속 조치 필요 사항

## 주의사항

- 한 번에 하나의 자료를 인제스트하는 것을 기본으로 함 (사용자가 일괄 처리를 원하면 순차적으로)
- 원천 자료의 내용이 불명확한 경우 사용자에게 확인 후 진행
- 기존 문서와 상충하는 내용이 발견되면 반드시 사용자에게 알리고 판단 요청
- 작업 완료 후 사용자에게 git commit/PR 진행 여부 확인 (이 스킬은 자동 commit 하지 않음)
