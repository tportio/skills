# llm-wiki

ONDA `product-docs` 위키 라이프사이클을 통째로 다루는 Claude Code 플러그인입니다. **검색(읽기 전용) + 인제스트 + 대화 보존 + 건강 점검** — 4개 스킬을 한 플러그인에 묶었습니다. tport 어느 디렉토리에서든 호출 가능하도록 `product-docs` 경로를 자동 해석합니다.

## 왜 만들었나

기존에는 위키 관리 워크플로우(`ingest`·`filing`·`lint`)가 `product-docs/.claude/skills/` 하위에 project-local 로만 있어, 해당 리포 디렉토리 안에서만 자동 로드됐습니다. 이 플러그인은 그걸 팀 마켓플레이스로 끌어올려 어느 tport 서브 레포에서든 `/query`, `/ingest`, `/filing`, `/lint` 를 호출할 수 있게 만듭니다.

---

## 포함 스킬 한눈에

| 스킬 | 한 줄 용도 | 쓰기 여부 |
|---|---|---|
| `/query <질문>` (또는 `/llm-wiki:query <질문>`) | LLM Wiki 검색 (`tport/product-docs/llm-wiki`) | 읽기 전용 |
| `/ingest <자료>` | 원천 자료 → 위키 문서 통합 | 쓰기 (수정/생성) |
| `/filing` | 대화 결과 → 위키 문서로 보존 | 쓰기 (수정/생성) |
| `/lint [범위]` | 위키 건강 점검(깨진 링크 등) | 읽기 + 사용자 승인 후 수정 |

> 모든 쓰기 스킬은 **자동 commit/push 하지 않습니다.** 변경 후 사용자에게 commit/PR 진행 여부를 확인합니다.

---

## 사용법 1 — `/query` (검색)

LLM 관련 개념·도구·인물·분석 자료를 위키에서 찾아 한국어로 답합니다. 위키 파일은 절대 수정하지 않습니다. (`/query` 가 다른 플러그인과 충돌하면 `/llm-wiki:query` 로 명시.)

### 호출

```
/query <질문>
```

### 예시

```
/query RAG 와 fine-tuning 의 차이가 뭐야?
/query 우리 위키에 정리된 임베딩 모델 비교는?
/query Andrej Karpathy 가 누구지?
/query llms.txt 가 뭐야?
```

### 내부 동작

1. `llm-wiki/index.md` Read → Sources·Concepts·Entities·Analyses 카탈로그 확인
2. 질문 ↔ 인덱스 항목 매칭 (모호하면 `Grep` 으로 `wiki/` 전체 검색)
3. 후보 페이지 Read, `[[위키링크]]` follow 필요 시 추가 Read
4. 근거 페이지 경로 포함해 한국어 답변
5. 위키에 없으면 "위키에 해당 내용 없음" 으로 답하고 **추측하지 않음**

---

## 사용법 2 — `/ingest` (원천 자료 → 위키 통합)

회의록·외부 문서·Notion 내보내기·블로그 글 등을 위키에 체계적으로 통합합니다. 원본 보존 → 요약 페이지 생성 → 관련 문서 업데이트 → 인덱스/로그 기록까지 자동.

### 호출

```
/ingest <자료 경로 또는 설명>
```

또는 파일을 첨부하면서 자연어로:

```
"이 회의록 위키에 통합해줘"
"방금 받은 Notion 문서 정리해줘"
"이 블로그 글 위키에 ingest"
```

### 워크플로우 예시 — 회의록 인제스트

```
사용자: /ingest ./onda-llm-roadmap-meeting-2026-05-20.md

스킬:
  1. product-docs 경로 자동 해석 → cd → git pull
  2. 사용자에게 확인:
     - 대상 프로젝트: ONDA-LLM-Roadmap?
     - 문서 유형: 회의록?
     - 담당자: jade?
  3. 원본을 `_workspace/jade/ONDA-LLM-Roadmap/raw/2026-05-20-roadmap.md` 에 보존
  4. 핵심 내용 요약해 사용자에게 보고
  5. 위키 문서 생성: `projects/ONDA-LLM-Roadmap/meetings/MEET-007-roadmap-2026-05-20.md`
  6. 관련 기존 문서 업데이트 (마일스톤, 관련 인물 페이지 등)
  7. `projects/ONDA-LLM-Roadmap/README.md` 문서 목록 갱신
  8. `changelog/CHANGELOG-2026.md` 기록
  9. `LOG.md` 상단에 ingest 엔트리 추가
  10. 결과 요약 보고 + commit 진행 여부 확인
```

### 워크플로우 예시 — LLM Wiki 인제스트

```
사용자: /ingest 이 글 LLM 위키에 넣어줘 (블로그 URL 또는 파일 첨부)

스킬:
  1. 원본을 `llm-wiki/raw/2026-05-26-<slug>.md` 에 보존
  2. `llm-wiki/wiki/sources/<slug>.md` 생성 (요약 페이지)
  3. 새 개념·인물·도구를 발견하면:
     - `llm-wiki/wiki/concepts/<name>.md`
     - `llm-wiki/wiki/entities/<name>.md`
  4. `llm-wiki/index.md` 의 Sources/Concepts/Entities 섹션에 항목 추가
  5. `llm-wiki/log.md` 상단에 ingest 엔트리 추가
```

---

## 사용법 3 — `/filing` (대화 → 문서 보존)

LLM 과의 대화에서 만든 비교표·인사이트·의사결정 근거 등 **공식 문서화할 가치가 있는 결과물** 을 위키 문서로 정제해 보존합니다. 채팅이 사라져도 지식이 남도록.

### 호출

```
/filing                        # 직전 대화에서 보존할 내용을 스킬이 제안
/filing 비교표 부분만           # 특정 부분 지정
"이거 위키에 filing 해줘"        # 자연어
"방금 만든 비교표 보존해줘"
```

### Filing 대상 vs 비대상

| ✅ Filing 대상 | ❌ Filing 비대상 |
|---|---|
| 경쟁사/기술 비교표 | 일회성 질문 답변 |
| 데이터 기반 인사이트 | 단순 조회 결과 |
| 의사결정 근거 (기술 선정 등) | 작업 지시 응답 |
| 여러 문서를 종합한 시스템 개요 | 이미 위키에 있는 중복 내용 |
| 시장 분석·포지셔닝 | |

### 워크플로우 예시

```
(대화 중에 RAG 솔루션 5개를 비교한 표를 만들었음)

사용자: /filing 방금 그 RAG 비교표 보존해줘

스킬:
  1. 사용자에게 확인:
     - 대상 위치: products/AI-Call-Responder?
     - 문서 유형: 참고 자료(REF)?
  2. 대화체를 문서체로 정제 (헤더·표 구조화, 맥락 trim)
  3. `products/AI-Call-Responder/reference/REF-003-RAG-솔루션-비교.md` 생성
  4. 기존 관련 문서(예: ARCH-001-시스템-개요.md) 에 새 문서 링크 추가
  5. README 문서 목록 + CHANGELOG + LOG.md 갱신
  6. commit 진행 여부 확인
```

### 자동 매핑 가이드

| 분석 결과 유형 | 권장 유형 | 접두어 | 저장 위치 |
|---|---|---|---|
| 경쟁사/기술 비교 | 참고 자료 | `REF` | `reference/` |
| 의사결정 근거 | 결정 기록 | `DEC` | `decisions/` |
| 아키텍처 정리 | 아키텍처 | `ARCH` | `architecture/` |
| 기능 분석 | 기능 | `FEAT` | `features/` |
| API 정리 | API | `API` | `api/` |
| 데이터 모델 정리 | 데이터 | `DATA` | `data/` |

---

## 사용법 4 — `/lint` (위키 건강 점검)

깨진 링크·고아 문서·INDEX 불일치·양방향 링크 누락 등을 한 번에 점검합니다.

### 호출

```
/lint                                                     # 전체 점검
/lint projects/2026-01-ONDA-CMS-더휴식-Edition             # 특정 프로젝트만
/lint products/OSP                                        # 특정 제품만
```

### 점검 항목

| # | 항목 | 자동 수정 |
|---|---|---|
| 1 | 깨진 링크 (`[text](path.md)` 가 실제 파일 없음) | 경로 오타는 사용자 승인 후 수정 |
| 2 | 고아 문서 (어디서도 링크 안 됨) | 처리 방향은 사용자 판단 |
| 3 | `INDEX.md` ↔ 폴더 구조 불일치 | 누락 항목 추가는 사용자 승인 후 |
| 4 | 프로젝트 ↔ 제품 양방향 링크 일치 | 사용자 승인 후 |
| 5 | 누락된 교차 참조 (관련 문서 간 링크 없음) | 사용자 판단 |
| 6 | 상충하는 내용 (선택, 명시 요청 시) | 사용자 판단 |
| 7 | 누락된 페이지 (언급되지만 전용 문서 없음) | 사용자 판단 |

### 예시 결과 보고

```markdown
## 린트 결과 요약 (범위: products/OSP)

| 점검 항목 | 결과 |
|---|---|
| 깨진 링크 | 3건 |
| 고아 문서 | 1건 |
| INDEX 불일치 | 0건 |
| 양방향 링크 누락 | 2건 |
| 누락된 교차 참조 | 5건 |

자동 수정 가능 3건 (깨진 링크 경로 오타). 진행할까요?
```

---

## 사전 설치 / 경로 설정

### 1. product-docs 리포 clone

```bash
git clone git@github.com:tportio/product-docs.git <your-tport-clone>/product-docs
```

### 2. 경로 자동 해석 순서

모든 스킬이 동일한 순서로 `product-docs` 위치를 찾습니다 (별도 설정 없이 후보 경로 중 하나에 있으면 자동 인식):

1. `$PRODUCT_DOCS_PATH` 환경변수
2. `$TPORT_HOME` 환경변수 → `$TPORT_HOME/product-docs`
3. 후보 경로 순차:
   - `~/Workspaces/tport/product-docs` (ONDA 팀 기본)
   - `~/dev/tport/product-docs`
   - `~/code/tport/product-docs`
   - `~/projects/tport/product-docs`
4. 모두 실패 시 사용자에게 경로 문의

> `/query` 검색 스킬은 위와 별개로 `$LLM_WIKI_PATH` 환경변수도 1순위로 인식합니다.

### 3. 비표준 경로 사용 시

```bash
# ~/.zshrc 등에 추가
export PRODUCT_DOCS_PATH="$HOME/myrepos/onda-product-docs"
```

---

## 동작 약속 (공통)

- **자동 commit 안 함**: `/ingest`, `/filing`, `/lint` 모두 변경 후 사용자에게 commit/PR 진행 여부 확인
- **`CLAUDE.md` 절대 수정 안 함**: 규칙 문서이며 카탈로그 아님 (보호 대상)
- **`raw/` 절대 수정 안 함**: 원천 자료는 불변
- **`_workspace/` 는 lint 제외**: 개인 작업 공간
- **위키에 없는 내용 추측 안 함**: 검색은 "위키에 해당 내용 없음" 응답
- **외부 검색 우회 안 함**: 위키 콘텐츠 질문에 웹 검색으로 대체 답변 안 함

---

## 위키 구조 참고

```
product-docs/
├── llm-wiki/                  ← /query, /ingest (llm-wiki 모드)
│   ├── index.md               ← 색인 (Sources, Concepts, Entities, Analyses)
│   ├── log.md                 ← 변경 이력
│   ├── raw/                   ← 원천 자료 (불변)
│   └── wiki/
│       ├── sources/
│       ├── concepts/
│       ├── entities/
│       └── analyses/
├── projects/                  ← /ingest, /filing, /lint
├── products/                  ← 동일
├── _workspace/<담당자>/        ← /ingest 가 원본 보존하는 위치
├── INDEX.md                   ← /lint 가 일관성 검사
└── LOG.md                     ← /ingest, /filing, /lint 가 엔트리 추가
```

---

## 자주 묻는 시나리오

| 상황 | 호출 |
|---|---|
| 위키에서 개념 찾고 싶음 | `/query <질문>` (또는 `/llm-wiki:query <질문>`) |
| 회의록 받았는데 위키 통합해야 함 | `/ingest <회의록 파일>` |
| 블로그 글/뉴스 보고 LLM 위키에 넣고 싶음 | `/ingest <URL 또는 글>` + 자연어로 "LLM 위키에" 명시 |
| 방금 LLM 과 만든 비교표 보존하고 싶음 | `/filing` |
| 분기에 한 번 위키 건강 점검 | `/lint` |
| 특정 제품 문서만 lint | `/lint products/<제품명>` |
| 인제스트 후 깨진 링크 확인 | `/lint` (또는 자동 제안 받음) |
