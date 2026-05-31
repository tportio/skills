# tport-skills

ONDA 팀이 공유하는 [Claude Code](https://claude.ai/code) 스킬 플러그인 마켓플레이스입니다.
공통 템플릿과 자동화 도구를 스킬로 만들어, 팀 누구나 동일한 품질의 결과물을 빠르게 만들 수 있습니다.

## 설치

Claude Code에서 아래 명령을 순서대로 실행하세요.

> Private 레포이므로 SSH URL로 추가해야 합니다. tportio org 접근 권한과 GitHub에 등록된 SSH 키가 필요합니다.

```
/plugin marketplace add git@github.com:tportio/skills.git
/plugin install onda-slides@tport-skills
/plugin install product-docs@tport-skills
/plugin install llm-wiki@tport-skills
/plugin install gemini-image@tport-skills
/plugin install ondadrop@tport-skills
```

설치가 완료되면 `/onda-slides`, `/product-docs`, `/llm-wiki`, `/gemini-image`, `/ondadrop` 같은 슬래시 명령으로 스킬을 바로 사용할 수 있습니다.

## 플러그인 목록

| 플러그인 | 설명 | 사용 예시 |
|----------|------|-----------|
| [onda-slides](plugins/onda-slides) | ONDA 공통 템플릿 기반 슬라이드(HTML + PDF) 생성 | `/onda-slides 1분기 매출 보고서` |
| [product-docs](plugins/product-docs) | ONDA 제품 문서 레포에 문서 생성/업데이트 + PR 자동 생성 | `/product-docs feature 로그인` |
| [llm-wiki](plugins/llm-wiki) | ONDA LLM Wiki 검색(읽기 전용) — index 기반으로 관련 페이지를 찾아 답변 | `/llm-wiki GBP 최적화 핵심 요소는?` |
| [gemini-image](plugins/gemini-image) | 마크다운 글의 `[IMAGE]` 블록에서 Gemini API(Nano Banana)로 이미지 생성 | `/gemini-image article.md` |
| [ondadrop](plugins/ondadrop) | `drop.tport.io`에 정적 사이트(폴더/파일) 배포 — 사내 비공개 URL + 외부 공유 링크 | `/ondadrop ./dist` |

## 새 플러그인 기여

플러그인 추가 방법은 [CLAUDE.md](CLAUDE.md)를 참고하세요.
