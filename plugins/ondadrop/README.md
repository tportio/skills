# ondadrop

`drop.tport.io`(ONDA 사내 Netlify Drop)에 정적 사이트를 배포하는 `ondadrop` CLI 래퍼 스킬입니다. 빌드 산출물·미리보기·리포트 등 정적 파일을 사내 비공개 URL 로 올리고, 필요 시 외부 공유 링크 발급까지 안내합니다.

## 설치

```
/plugin marketplace add git@github.com:tportio/skills.git   # 최초 1회
/plugin install ondadrop@tport-skills
```

> Private 레포라 SSH URL 로 추가합니다. tportio org 접근 권한과 GitHub 에 등록된 SSH 키가 필요합니다. 전체 플러그인 목록은 [루트 README](../../README.md) 참고.

## 왜 만들었나

시안·리포트·문서 미리보기를 빠르게 공유해야 할 때, 매번 S3 버킷이나 별도 호스팅을 셋업하기는 번거롭습니다. `ondadrop` 은 폴더/파일 하나를 사내 비공개 URL 로 즉시 올려주고, 외부에 보여줘야 하면 만료 가능한 공유 링크를 발급합니다. 이 스킬은 그 흐름(CLI·토큰 확인 → 빌드 → 배포 → 공유)을 대신 챙겨줍니다.

## 사용법

```
/ondadrop <dir|file> [--name 이름] [--expire 14d]
```

자연어로 호출해도 됩니다 — "이 dist 폴더 사내에 올려줘" → `ondadrop deploy ./dist`.

### 배포물 모델

| 항목 | 기본값 | 변경 |
|---|---|---|
| 접근 범위 | **비공개** (사내 Okta 로그인) | — |
| 외부 공유 | 공유 링크 (철회 가능) | `drop.tport.io` 목록에서 발급 |
| 공유 링크 만료 | 7일 | 발급 시 지정 |
| 배포 만료 | 14일 | `--expire 30d \| permanent` |

## 절차

스킬이 호출되면 다음 순서로 진행합니다:

1. **CLI 확인** — `which ondadrop`. 없으면 [drop.tport.io/cli.html](https://drop.tport.io/cli.html) 에서 (로그인 후) 플랫폼 바이너리 다운로드를 안내. macOS 는 `xattr -d com.apple.quarantine ondadrop` 후 PATH 에 둡니다.
2. **토큰 확인** — `~/.config/ondadrop/token` 또는 `$DROP_TOKEN`. 없으면 cli.html 에서 발급 후 `ondadrop login <token>` 안내.
3. **배포 대상 결정** — 지정한 폴더/파일. 빌드가 필요한 프로젝트(`dist/`, `build/`, `out/`)면 먼저 빌드한 뒤 산출물 디렉토리를 사용.
4. **배포** — `ondadrop deploy <dir|file> [--name "이름"] [--expire 14d]`. 단일 HTML/파일도 가능(root 에서 서빙). 성공 시 출력된 `https://<id>.drop.tport.io` URL 을 전달.
5. **외부 공유** — 배포물은 비공개이므로, 필요 시 `drop.tport.io` 목록에서 해당 항목의 "공유 링크"를 발급하도록 안내(로그인 없는 외부 접근용).

## 예시

```bash
ondadrop deploy ./dist --name "마케팅 랜딩 시안"
ondadrop deploy ./report --expire 30d
ondadrop deploy index.html
```

CI 에서는 `DROP_TOKEN` 환경변수로 토큰을 주입합니다.

## 의존성

- `ondadrop` CLI ([drop.tport.io/cli.html](https://drop.tport.io/cli.html) 에서 다운로드)
- 사내 Okta 계정 (배포물 열람·공유 링크 발급용)
