---
name: ondadrop
description: drop.tport.io에 정적 사이트(폴더/파일)를 배포한다. ondadrop CLI로 빌드 산출물을 사내 비공개 URL로 올리고, 이미 배포된 사이트는 URL로 가져와(import) 재배포하며, 배포물의 파일을 로컬로 내려받을(get) 수 있다. 필요시 공유 링크 발급을 안내. 정적 사이트·빌드 결과·미리보기 공유 요청 시 사용.
disable-model-invocation: false
argument-hint: "<dir|file> [--name 이름] [--expire 14d] [--update id]"
allowed-tools: Bash, Read, Glob
---

# ondadrop — 사내 정적 사이트 배포

`drop.tport.io`(ONDA 사내 Netlify Drop)에 정적 사이트를 배포하는 ondadrop CLI 래퍼.

## 배포물 모델
- 배포물은 **기본 비공개** — 사내 Okta 로그인으로만 열람.
- **외부 공유**는 `drop.tport.io` 전체 목록에서 **공유 링크**(기본 7일·철회 가능)를 발급.
- 배포 만료 기본 14일, `--expire 30d|permanent`로 변경.
- **같은 URL로 업데이트**: 매 배포는 새 랜덤 URL이므로, 기존 주소를 갱신하려면 `--update <id>`로 파일을 교체한다(URL·공유 링크 유지).

## 절차

1. **CLI 확인**: `which ondadrop`
   - 없으면 플랫폼 바이너리 다운로드 안내(무인증): `https://drop.tport.io/download/cli/<os>/<arch>` (os=linux|darwin, arch=amd64|arm64). 예: `curl -fsSL https://drop.tport.io/download/cli/darwin/arm64 -o ondadrop`.
     macOS는 `chmod +x ondadrop && xattr -d com.apple.quarantine ondadrop` 후 PATH에 둔다.

2. **토큰 확인**: `~/.config/ondadrop/token` 존재 또는 `$DROP_TOKEN` 설정 여부.
   - 없으면 cli.html에서 토큰 발급 → `ondadrop login <token>` 안내.

3. **배포 대상 결정**: 사용자가 지정한 폴더/파일. 빌드가 필요한 프로젝트(예: `dist/`, `build/`, `out/`)면 먼저 빌드 후 산출물 디렉토리를 사용.

4. **배포**: `ondadrop deploy <dir|file> [--name "이름"] [--expire 14d]`
   - 단일 HTML/파일도 가능(root에서 서빙됨).
   - 성공 시 출력된 `https://<id>.drop.tport.io` URL을 사용자에게 전달.
   - **재배포(같은 URL 유지)**: 이전 URL의 id로 `ondadrop deploy <dir> --update <id>`.

5. **외부 공유가 필요하면**: 배포물은 비공개이므로 `drop.tport.io` 목록에서 해당 항목의 "공유 링크"를 발급하라고 안내(로그인 없는 외부 접근용, 기본 7일).

## URL로 가져오기 (import)

이미 배포된 정적 사이트를 주소로 가져와 drop에 올린다: `ondadrop import <url> [--name "이름"] [--expire 30d]`. 성공 시 새 `https://<id>.drop.tport.io` URL을 사용자에게 전달한다.

- **지원**: 자기완결형 HTML 페이지(+ same-origin 정적 자산).
- **미지원**: JavaScript 렌더링이 필요한 동적 사이트(SPA), 비-HTML 응답, 내부·사설 주소 — "지원하지 않는 형식입니다" 등의 메시지로 거부된다. 거부되면 그 사유를 사용자에게 그대로 전달한다(우회 시도 금지).

## 배포물 내려받기 (get)

배포물의 파일을 로컬로 받는다: `ondadrop get <id|url> [--out <dir>]`. 인자는 배포 id(`brave-otter-1234`) 또는 그 URL(`https://brave-otter-1234.drop.tport.io/...`) 둘 다 된다. 기본 저장 위치는 `./<id>`.

- `deploy`의 역방향이므로, 받은 폴더를 고쳐 `ondadrop deploy <dir> --update <id>`로 같은 URL에 되올릴 수 있다.
- 배포 메타(`.drop-meta.json`)와 공유 링크 정보는 포함되지 않는다 — 서빙되는 파일만.
- 없는 id는 404, 형식이 잘못된 id는 요청 전에 CLI가 거부한다.

## 예시

```bash
ondadrop deploy ./dist --name "마케팅 랜딩 시안"
ondadrop deploy ./report --expire 30d
ondadrop deploy index.html
ondadrop deploy ./dist --update brave-otter-1234   # 같은 URL 갱신
ondadrop import https://example.com --name "외부 시안"   # 배포된 사이트를 URL로 가져오기
ondadrop get brave-otter-1234                      # 배포물을 ./brave-otter-1234로 내려받기
ondadrop get https://brave-otter-1234.drop.tport.io --out ./site
```

CI에서는 바이너리를 `/download/cli/<os>/<arch>`로 받고(무인증), `DROP_TOKEN` 환경변수로 토큰을 주입한다.
