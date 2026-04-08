# tport-skills

tport 팀이 공유하는 [Claude Code](https://claude.ai/code) 스킬 플러그인 마켓플레이스입니다.
공통 템플릿과 자동화 도구를 스킬로 만들어, 팀 누구나 동일한 품질의 결과물을 빠르게 만들 수 있습니다.

## 설치

Claude Code에서 아래 두 명령을 순서대로 실행하세요.

```
/plugin marketplace add tportio/skills
/plugin install onda-slides@tportio-skills
```

설치가 완료되면 `/onda-slides` 같은 슬래시 명령으로 스킬을 바로 사용할 수 있습니다.

## 플러그인 목록

| 플러그인 | 설명 | 사용 예시 |
|----------|------|-----------|
| [onda-slides](plugins/onda-slides) | ONDA 공통 템플릿 기반 슬라이드(HTML + PDF) 생성 | `/onda-slides 1분기 매출 보고서` |

## 새 플러그인 기여

플러그인 추가 방법은 [CLAUDE.md](CLAUDE.md)를 참고하세요.
