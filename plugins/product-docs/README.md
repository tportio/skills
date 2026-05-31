# product-docs

ONDA 제품 문서 레포(`tportio/product-docs`)에 문서를 생성·업데이트하고 PR 까지 자동으로 만드는 Claude Code 스킬입니다. 어느 tport 서브 레포에서든 호출할 수 있습니다.

## 설치

```
/plugin marketplace add git@github.com:tportio/skills.git   # 최초 1회
/plugin install product-docs@tport-skills
```

> Private 레포라 SSH URL 로 추가합니다. tportio org 접근 권한과 GitHub 에 등록된 SSH 키가 필요합니다. 전체 플러그인 목록은 [루트 README](../../README.md) 참고.

## 왜 만들었나

제품 문서는 한 곳(`product-docs`)에 모으되, 실제 작업은 본인이 일하던 서브 레포(예: `osp`, `hub`, `backoffice`)에서 컨텍스트를 그대로 들고 시작하고 싶습니다. 이 스킬은 그 두 가지를 잇습니다 — 현재 디렉토리에서 컨텍스트를 모아 docs 레포에 PR 까지 자동으로 만들어 줍니다.

## 사용법

```
/product-docs <doc-type> <title>
```

### 지원 명령

| 명령 | 설명 | 예시 |
|---|---|---|
| `status` | 매핑된 제품의 문서 현황 | `/product-docs status` |
| `feature <title>` | 기능 문서 생성/업데이트 | `/product-docs feature login` |
| `api <title>` | API 문서 | `/product-docs api booking API` |
| `arch <title>` | 아키텍처 문서 | `/product-docs arch system overview` |
| `guide <title>` | 사용자 가이드 | `/product-docs guide getting started` |
| `ops <title>` | 운영 가이드 | `/product-docs ops deployment` |
| `data <title>` | 데이터 모델 문서 | `/product-docs data ERD` |
| `update <doc-path>` | 기존 문서 업데이트 | `/product-docs update FEAT-001-login.md` |
| `config` | 현재 설정 확인/수정 | `/product-docs config` |

자연어로 호출해도 됩니다 — "OSP 에 로그인 기능 문서 추가해줘" → `feature login`.

## 최초 설정

호출하면 현재 디렉토리에 `.product-docs.config.json` 이 없을 때 다음 항목을 물어봅니다:

1. **Docs repo path**: `product-docs` 리포의 절대 경로 (예: `<your-tport-clone>/product-docs`)
2. **Clone URL** (경로가 없을 때만): 기본값 `git@github.com:tportio/product-docs.git`
3. **Product mapping**: 이 레포가 어느 제품과 매핑되는지 (예: `OSP`, `HUB1`, `Pension-plus`, ...)
4. **Author name**: 기본값은 `git config user.name`

생성된 `.product-docs.config.json` 은 **반드시 `.gitignore` 에 추가**하세요 (사용자별 절대 경로 포함).

## 문서 작성 규칙

문서는 **PO·기획자·비즈니스 stakeholder** 가 독자입니다. 다음은 절대 포함하지 않습니다:

- 소스 코드, 코드 블록
- 변수/함수/클래스명, ORM·middleware 같은 구현 용어
- 환경변수, 설정 파일, CLI 명령

대신 비즈니스 가치·사용자 관점으로 한국어로 작성하고, 비교·목록은 표, 프로세스·데이터 흐름은 Mermaid 다이어그램을 적극 사용합니다.

API 문서는 예외로 엔드포인트 경로·JSON 예시 허용. 데이터 모델 문서는 ERD(Mermaid), 아키텍처 문서는 시스템 다이어그램 허용.

자세한 톤·파일명 규칙은 SKILL.md 참고.

## 자동 처리되는 부수 효과

문서 작성 시 자동으로:

- `products/{product}/README.md` 의 문서 목록에 새 문서 링크 추가
- `changelog/CHANGELOG-{year}.md` 에 변경 이력 기록
- 필요 시 `products/INDEX.md` 업데이트

## PR 워크플로우

문서 확정 후 사용자 승인을 받으면:

1. `docs/{product}-{brief}` 브랜치 생성
2. `docs: {product} {title}` 커밋
3. `gh pr create` 로 PR 자동 생성
4. PR URL 보고

## 의존성

- `git`
- `gh` CLI (`brew install gh` + `gh auth login`)
