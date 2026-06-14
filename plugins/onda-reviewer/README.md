# onda-reviewer

onda-reviewer PR 리뷰 봇 운영 도구.

## Skills

### `onda-reviewer:regen-context <repo>`

대상 repo 의 **diff-밖 가시성 컨텍스트 팩**(`context/repos/<owner>__<repo>.md`)을 재생성한다.

onda-reviewer 는 PR diff 만 보고 리뷰하므로, diff 밖 파일에 사는 컨벤션(미들웨어 부수효과·router 공통 auth·ORM association·응답 계약·config 상수 등)을 몰라 오탐(🚫/⚠️)을 낸다. 이 skill 은 최근 PR 에서 오탐 패턴을 마이닝하고 로컬 클론에서 컨벤션 anchor 를 갱신해 팩을 다시 쓴다. 봇은 이 팩을 매 리뷰 프롬프트에 주입해 오탐을 차단한다.

```
onda-reviewer:regen-context hub
onda-reviewer:regen-context <repo>
```

high-churn repo 는 anchor 가 stale 해지므로 주기적으로(또는 오탐이 늘면) 실행한다.

전체 아키텍처와 방법론: onda-reviewer 레포의 `docs/DIFF_VISIBILITY.md`.
