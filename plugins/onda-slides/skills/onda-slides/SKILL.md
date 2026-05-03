---
name: onda-slides
description: ONDA 공통 템플릿으로 슬라이드 프레젠테이션(HTML + PDF)을 생성한다. 차트, 표, 그리드 레이아웃 지원. 모디파이어로 simple(비전문가 대상 큰 폰트) 모드 선택 가능.
disable-model-invocation: false
argument-hint: "[modifier...] <슬라이드 데이터 또는 지시사항>"
allowed-tools: Bash, Bash(pip3 install *), Bash(python3 *), Read, Write, Edit, Glob, Grep, Agent, AskUserQuestion
---

# Presentation PDF Generator

HTML 단일 파일로 슬라이드를 만들고, Puppeteer 스크린샷 방식으로 PDF를 생성한다.

## Input

`$ARGUMENTS` — `[modifier...] <슬라이드 데이터>`

사용자가 슬라이드 데이터(제목, 내용, 차트, 표 등)를 자연어로 제공한다.

### Modifier (선택, 공백 구분, `$ARGUMENTS` 맨 앞, 여러 개 조합 가능)

각 modifier는 직교 축이라 자유롭게 조합한다.

| modifier | 축 | 효과 |
| --- | --- | --- |
| `simple` | 오디언스 | 비전문가 대상. 큰 폰트, 한 슬라이드 한 메시지, 그리드 `.g2`만, 불렛 3개 이하 |
| `wide` | 화면 비율 | 16:9 (13.33in × 7.5in, PowerPoint/Google Slides 표준). 기본은 A4 landscape |
| `dark` | 테마 | 다크 모드. 검은 배경 + 밝은 텍스트. 야간 행사/어두운 발표장 |
| `en` | 언어 | 영문 폰트(Inter). 기본은 Pretendard. 영문 자료/외부 IR |

**파싱 규칙**

`$ARGUMENTS`를 공백으로 split한 뒤, **앞에서부터** 위 표에 있는 토큰을 modifier로 빨아들인다. 모르는 토큰을 만나면 멈추고 나머지는 슬라이드 데이터.

```
/onda-slides 매출 보고서                  → modifiers = [], content = "매출 보고서"
/onda-slides simple 매출 보고서           → modifiers = [simple], content = "매출 보고서"
/onda-slides simple wide 매출 보고서      → modifiers = [simple, wide], content = "매출 보고서"
/onda-slides wide dark en IR deck         → modifiers = [wide, dark, en], content = "IR deck"
/onda-slides 매출 simple                  → modifiers = [], content = "매출 simple"
                                          (첫 토큰이 modifier가 아니면 즉시 멈춤)
```

**body 클래스 부여**: `<body class="mode-XXX mode-YYY ...">`. modifier 없으면 `<body class="mode-default">` (생략 금지).

```html
<body class="mode-default">          <!-- /onda-slides ... -->
<body class="mode-simple">           <!-- /onda-slides simple ... -->
<body class="mode-simple mode-wide"> <!-- /onda-slides simple wide ... -->
<body class="mode-wide mode-dark mode-en">  <!-- /onda-slides wide dark en ... -->
```

콘텐츠 원칙(불렛 개수 등)도 modifier에 따라 다르게 적용 — 아래 "콘텐츠 원칙" 섹션 참조.

## 콘텐츠 원칙 (modifier 별)

### default 모드 — 정보 밀도 높음

내부 회의/팀 보고/IR 등. 한 슬라이드에 여러 정보를 압축 표현.

- 불렛 개수 제한 없음 (단, 가독성 위해 7개 이하 권장)
- 그리드 `.g2`, `.g2w`, `.g3`, `.g4` 모두 허용
- 차트 적극 활용 (데이터 포인트 제한 없음)
- 표 행 수 제한 없음

### simple 모드 — 비전문가 대상 (`/onda-slides simple ...`)

숙박업주, 일반 고객 등 큰 화면에서 멀리서 보는 청중. 한 슬라이드 한 메시지가 원칙.

1. **한 슬라이드 = 한 메시지**: 하나의 핵심 전달 내용만 담는다
2. **불렛 최대 3개**: 넘으면 슬라이드를 분할한다
3. **그리드 `.g2`만**: `.g3`, `.g4`, `.g2w` 사용 금지
4. **차트는 심플하게**: 범례 최소화, 데이터 포인트 7개 이하
5. **텍스트 짧게**: 불렛 1개는 1줄(25자 이내), 문장보다 키워드
6. **표 행 수 최소**: 4행 이하, 넘으면 슬라이드 분할
7. **한 슬라이드에 여러 컴포넌트 금지**: 불렛/Stat/카드/표 중 하나만

## Phase 1: 정보 수집

### 기본 출력 경로

출력 경로를 별도로 지정하지 않으면 현재 작업 디렉토리(`$PWD`)에 저장한다.
파일명은 제목에서 자동 생성 (공백 → `_`, 특수문자 제거).

- HTML: `$PWD/{파일명}.html`
- PDF: `$PWD/{파일명}.pdf`

인수가 충분하지 않으면 아래를 확인한다:

1. **출력 경로**: (선택) 별도 지정 시에만 질문. 기본값은 `$PWD`.
2. **기본 정보**: 제목, 부제목, 날짜
3. **로고**: 이미지 파일 경로 또는 base64 data URI (없으면 기본 ONDA 로고 사용)
4. **슬라이드 내용**: 각 슬라이드별 헤더, 불렛, 차트, 표, 그리드 구성

사용자가 이미 충분한 정보를 제공했으면 바로 Phase 2로 진행한다.

## Phase 2: HTML 생성

아래 CSS/HTML 규칙을 **반드시** 따른다.

### 브랜드 토큰

```
Primary Blue   : #004FC5
Dark Text      : #191F28
Body Text      : #333D4B
Secondary Text : #4E5968
Light Text     : #8B95A1
Border         : #E5E8EB
Row Stripe     : #F2F4F6
Background     : #fff
Accent Line    : #004FC5 (5px)
```

### CSS 핵심 규칙

```css
@import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css");

@page {
  size: A4 landscape;
  margin: 0;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family:
    "Pretendard Variable",
    "Pretendard",
    -apple-system,
    "Noto Sans KR",
    sans-serif;
  color: #191F28;
  -webkit-font-smoothing: antialiased;
}

/* ─── 슬라이드 컨테이너 ─── */
.slide {
  width: 297mm;
  height: 210mm;
  position: relative;
  overflow: hidden;
  page-break-after: always;
  background: #fff;
}

/* ─── 상단 악센트 라인 (모든 콘텐츠 슬라이드) ─── */
.accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 5px;
  background: #004FC5;
}

/* ─── 슬라이드 헤더 (악센트 라인 아래) ─── */
.hbar {
  padding: 40px 48px 0;
}
.hbar h2 {
  font-size: 22px;
  font-weight: 700;
  color: #004FC5;
  letter-spacing: -0.3px;
}
.hbar .hdesc {
  font-size: 13px;
  font-weight: 400;
  color: #4E5968;
  margin-top: 4px;
}

/* ─── 본문 ─── */
.body {
  padding: 24px 48px 16px;
}

/* ─── Footer ─── */
.foot {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 48px;
  border-top: 1px solid #E5E8EB;
}
.foot .copyright {
  font-size: 9px;
  font-weight: 400;
  color: #B0B8C1;
}
.foot .snum {
  font-size: 9px;
  font-weight: 500;
  color: #8B95A1;
}

/* ═══════════════════════════════════════
   커버 슬라이드
   ═══════════════════════════════════════ */
.cover-accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 5px;
  background: #004FC5;
}
.cover-header {
  position: absolute;
  top: 40px;
  left: 48px;
  right: 48px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.cover-header .onda-logo {
  height: 28px;
  width: auto;
}
.cover-header .tagline {
  font-size: 11px;
  color: #8B95A1;
  letter-spacing: 0.5px;
  font-weight: 400;
}
.cover-body {
  position: absolute;
  top: 50%;
  left: 48px;
  transform: translateY(-55%);
  max-width: 65%;
}
.cover-body h1 {
  font-size: 38px;
  font-weight: 800;
  color: #004FC5;
  line-height: 1.2;
  letter-spacing: -0.5px;
}
.cover-body .sub {
  font-size: 15px;
  color: #4E5968;
  line-height: 1.6;
  margin-top: 16px;
  max-width: 520px;
}
.cover-body .date {
  font-size: 13px;
  color: #8B95A1;
  margin-top: 24px;
}
/* 커버 우측 장식 — O 심볼 */
.cover-deco {
  position: absolute;
  right: -40px;
  top: 50%;
  transform: translateY(-50%);
  width: 340px;
  height: 340px;
  border-radius: 50%;
  border: 52px solid rgba(0, 79, 197, 0.08);
}
.cover-foot {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 48px;
  border-top: 1px solid #E5E8EB;
}
.cover-foot .products {
  display: flex;
  gap: 12px;
}
.cover-foot .pill {
  font-size: 10px;
  font-weight: 500;
  color: #004FC5;
  padding: 4px 14px;
  border-radius: 20px;
  border: 1px solid rgba(0, 79, 197, 0.2);
  background: rgba(0, 79, 197, 0.04);
}
.cover-foot .web {
  font-size: 10px;
  color: #B0B8C1;
  font-weight: 400;
}

/* ═══════════════════════════════════════
   섹션 구분 슬라이드 (중간 타이틀)
   ═══════════════════════════════════════ */
.section-content {
  width: 100%;
  height: 210mm;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}
.section-content h1 {
  font-size: 32px;
  font-weight: 800;
  color: #004FC5;
}
.section-content .sub {
  font-size: 14px;
  color: #4E5968;
  margin-top: 10px;
}

/* ═══════════════════════════════════════
   콘텐츠 컴포넌트
   ═══════════════════════════════════════ */

/* 섹션 타이틀 */
.stitle {
  font-size: 15px;
  font-weight: 700;
  color: #191F28;
  margin-bottom: 10px;
  margin-top: 18px;
  padding-left: 10px;
  border-left: 3px solid #004FC5;
}

/* 불렛 */
ul.bl {
  list-style: none;
  padding: 0;
}
ul.bl li {
  font-size: 14px;
  line-height: 1.7;
  margin-bottom: 8px;
  color: #333D4B;
  padding-left: 14px;
  position: relative;
}
ul.bl li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 9px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #004FC5;
}

/* 하이라이트 텍스트 — 문장 내 강조 */
.hl {
  color: #004FC5;
  font-weight: 700;
}

/* Stat 카드 — 숫자 강조 */
.stats {
  display: flex;
  gap: 32px;
  align-items: center;
}
.stat-item {
  text-align: center;
}
.stat-num {
  font-size: 30px;
  font-weight: 800;
  color: #004FC5;
}
.stat-label {
  font-size: 10px;
  font-weight: 500;
  color: #8B95A1;
  letter-spacing: 1px;
  text-transform: uppercase;
  margin-top: 4px;
}
.stat-divider {
  width: 1px;
  height: 36px;
  background: #D1D6DB;
}

/* Pill 태그 */
.pill {
  display: inline-block;
  font-size: 11px;
  font-weight: 500;
  color: #004FC5;
  padding: 5px 14px;
  border-radius: 20px;
  border: 1px solid rgba(0, 79, 197, 0.2);
  background: rgba(0, 79, 197, 0.04);
}

/* 카드 박스 */
.card {
  background: #fff;
  border: 1px solid #E5E8EB;
  border-radius: 8px;
  padding: 20px;
}
.card .card-title {
  font-size: 14px;
  font-weight: 700;
  color: #191F28;
  margin-bottom: 8px;
}
.card .card-value {
  font-size: 26px;
  font-weight: 800;
  color: #004FC5;
}
.card .card-desc {
  font-size: 12px;
  color: #4E5968;
  margin-top: 4px;
}

/* 표 */
table.dt {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
table.dt thead th {
  background: #004FC5;
  color: #fff;
  font-weight: 600;
  padding: 10px 14px;
  text-align: left;
  font-size: 12px;
}
table.dt thead th:first-child {
  border-radius: 6px 0 0 0;
}
table.dt thead th:last-child {
  border-radius: 0 6px 0 0;
}
table.dt tbody td {
  padding: 10px 14px;
  border-bottom: 1px solid #E5E8EB;
  color: #333D4B;
}
table.dt tbody tr:nth-child(even) {
  background: #F2F4F6;
}
table.dt tbody tr:last-child td {
  border-bottom: none;
}
table.dt tbody tr:last-child td:first-child {
  border-radius: 0 0 0 6px;
}
table.dt tbody tr:last-child td:last-child {
  border-radius: 0 0 6px 0;
}

/* 구분선 */
.divider {
  width: 100%;
  height: 1px;
  background: #E5E8EB;
  margin: 16px 0;
}

/* AI 생성 이미지 */
.slide-img {
  width: 100%;
  height: auto;
  max-height: 420px;
  object-fit: contain;
  border-radius: 8px;
}
.slide-img-full {
  position: absolute;
  top: 45px;
  left: 0;
  right: 0;
  bottom: 36px;
  object-fit: cover;
}
.slide-img-caption {
  font-size: 10px;
  color: #8B95A1;
  text-align: center;
  margin-top: 6px;
}

/* 그리드 */
.g2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}
.g2w {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 24px;
}
.g3 {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
}
.g4 {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: 16px;
}

/* ═══════════════════════════════════════
   simple 모드 — 비전문가 대상, 큰 폰트
   <body class="mode-simple">에만 적용
   ═══════════════════════════════════════ */
body.mode-simple .slide {
  display: flex;
  flex-direction: column;
  justify-content: center;     /* 헤더 + 본문이 슬라이드 정중앙 */
  padding: 24px 0 60px;        /* footer 공간 확보 */
}
body.mode-simple .hbar {
  flex-shrink: 0;
  padding: 0 80px;
  margin-bottom: 36px;
}
body.mode-simple .hbar h2     { font-size: 44px; }
body.mode-simple .hbar .hdesc { font-size: 22px; margin-top: 10px; }

body.mode-simple .body {
  flex-shrink: 0;
  padding: 0 80px;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 24px;
}

body.mode-simple .stitle {
  font-size: 30px;
  margin-bottom: 18px;
  margin-top: 0;
  padding-left: 14px;
  border-left: 5px solid #004FC5;
}

body.mode-simple ul.bl li {
  font-size: 32px;
  line-height: 1.6;
  margin-bottom: 24px;
  padding-left: 28px;
}
body.mode-simple ul.bl li:last-child { margin-bottom: 0; }
body.mode-simple ul.bl li::before {
  width: 10px; height: 10px; top: 18px;
}

body.mode-simple .stats          { gap: 64px; justify-content: center; }
body.mode-simple .stat-num       { font-size: 72px; line-height: 1.1; }
body.mode-simple .stat-label     { font-size: 18px; margin-top: 10px; }
body.mode-simple .stat-divider   { height: 64px; }

body.mode-simple .pill           { font-size: 18px; padding: 8px 22px; border-radius: 22px; }

body.mode-simple .card           { padding: 36px; border-radius: 12px; }
body.mode-simple .card .card-title { font-size: 26px; margin-bottom: 14px; }
body.mode-simple .card .card-value { font-size: 56px; line-height: 1.1; }
body.mode-simple .card .card-desc  { font-size: 20px; margin-top: 10px; }

body.mode-simple table.dt              { font-size: 24px; }
body.mode-simple table.dt thead th     { font-size: 22px; padding: 18px 24px; }
body.mode-simple table.dt tbody td     { padding: 18px 24px; }

body.mode-simple .section-content h1   { font-size: 64px; }
body.mode-simple .section-content .sub { font-size: 28px; margin-top: 18px; }

/* simple 모드는 .g3, .g4 사용 금지. .g2 gap만 살짝 키움 */
body.mode-simple .g2 { gap: 28px; }

/* ═══════════════════════════════════════
   wide 모드 — 16:9 (PowerPoint/Google Slides 표준)
   13.33in × 7.5in = 338.67mm × 190.5mm
   ═══════════════════════════════════════ */
body.mode-wide .slide {
  width: 338.67mm;
  height: 190.5mm;
}
/* 16:9는 A4보다 가로가 넓고 세로가 짧다. 본문 padding을 조금 키워 균형. */
body.mode-wide .hbar       { padding: 36px 56px 0; }
body.mode-wide .body       { padding: 24px 56px 16px; }
body.mode-wide .foot       { padding: 0 56px; }
body.mode-wide .cover-header,
body.mode-wide .cover-foot { padding: 0 56px; }

/* simple + wide 조합: simple의 정중앙 정렬 + wide 사이즈에 맞춰 padding */
body.mode-simple.mode-wide .hbar { padding: 0 96px; }
body.mode-simple.mode-wide .body { padding: 0 96px; }

/* ═══════════════════════════════════════
   dark 모드 — 다크 테마
   ═══════════════════════════════════════ */
body.mode-dark {
  background: #0F1419;
  color: #E5E8EB;
}
body.mode-dark .slide      { background: #0F1419; }
body.mode-dark .hbar h2    { color: #4A90D9; }       /* 진한 블루는 어두운 배경에 잘 안 보임 */
body.mode-dark .hbar .hdesc{ color: #8B95A1; }
body.mode-dark .accent,
body.mode-dark .cover-accent { background: #4A90D9; }
body.mode-dark .stitle     { color: #E5E8EB; border-left-color: #4A90D9; }
body.mode-dark ul.bl li    { color: #C8CDD5; }
body.mode-dark ul.bl li::before { background: #4A90D9; }
body.mode-dark .hl         { color: #4A90D9; }
body.mode-dark .stat-num   { color: #4A90D9; }
body.mode-dark .stat-label { color: #8B95A1; }
body.mode-dark .stat-divider { background: #2A3038; }
body.mode-dark .pill {
  color: #4A90D9;
  border-color: rgba(74, 144, 217, 0.3);
  background: rgba(74, 144, 217, 0.1);
}
body.mode-dark .card {
  background: #181E26;
  border-color: #2A3038;
}
body.mode-dark .card .card-title { color: #E5E8EB; }
body.mode-dark .card .card-value { color: #4A90D9; }
body.mode-dark .card .card-desc  { color: #8B95A1; }
body.mode-dark table.dt thead th { background: #4A90D9; }
body.mode-dark table.dt tbody td { color: #C8CDD5; border-bottom-color: #2A3038; }
body.mode-dark table.dt tbody tr:nth-child(even) { background: #181E26; }
body.mode-dark .divider    { background: #2A3038; }
body.mode-dark .foot,
body.mode-dark .cover-foot { border-top-color: #2A3038; }
body.mode-dark .foot .copyright,
body.mode-dark .cover-foot .web { color: #4E5968; }
body.mode-dark .foot .snum      { color: #8B95A1; }
body.mode-dark .cover-body h1   { color: #4A90D9; }
body.mode-dark .cover-body .sub { color: #C8CDD5; }
body.mode-dark .cover-body .date{ color: #8B95A1; }
body.mode-dark .cover-deco      { border-color: rgba(74, 144, 217, 0.12); }
body.mode-dark .cover-header .tagline { color: #8B95A1; }
body.mode-dark .section-content h1   { color: #4A90D9; }
body.mode-dark .section-content .sub { color: #8B95A1; }
/* 다크 모드 화면 모드 배경도 살짝 다르게 */
@media screen {
  body.mode-dark { background: #050709; }
}

/* ═══════════════════════════════════════
   en 모드 — 영문 자료
   Pretendard → Inter (영문에 더 적합)
   ═══════════════════════════════════════ */
body.mode-en {
  font-family:
    "Inter",
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    sans-serif;
}
/* en 모드는 별도 폰트 CDN을 추가로 import — <head>에 아래 한 줄 추가 */
/* <link rel="stylesheet" href="https://rsms.me/inter/inter.css"> */
```

### HTML 패턴

`<body>`에 modifier 클래스를 반드시 부여한다 — 위 simple 모드 CSS는 이 클래스가 있어야 적용된다.

```html
<body class="mode-default">  <!-- /onda-slides ... -->
<body class="mode-simple">   <!-- /onda-slides simple ... -->
```

```html
<!-- ─── 표지 ─── -->
<div class="slide active" id="s0">
  <div class="cover-accent"></div>
  <div class="cover-header">
    <img
      class="onda-logo"
      src="https://cdn.prod.website-files.com/62fc3cdcd1a5bb1370c2d067/63c0a7b567846c336d75f050_onda.svg"
      alt="ONDA"
    />
    <div class="tagline">Hospitality Connectivity Platform</div>
  </div>
  <div class="cover-body">
    <h1>제목</h1>
    <div class="sub">부제목 설명 텍스트</div>
    <div class="date">2026.04</div>
  </div>
  <div class="cover-deco"></div>
  <div class="cover-foot">
    <div class="products">
      <!-- 필요 시 pill 태그 추가 -->
    </div>
    <div class="web">onda.me</div>
  </div>
</div>

<!-- ─── 섹션 구분 슬라이드 (선택) ─── -->
<div class="slide" id="s1">
  <div class="accent"></div>
  <div class="section-content">
    <h1>01</h1>
    <div class="sub">섹션 제목</div>
  </div>
  <div class="foot">
    <div class="copyright">&copy; ONDA Inc.</div>
    <div class="snum">2 / 8</div>
  </div>
</div>

<!-- ─── 일반 콘텐츠 슬라이드 ─── -->
<div class="slide" id="s2">
  <div class="accent"></div>
  <div class="hbar">
    <h2>슬라이드 제목</h2>
    <div class="hdesc">슬라이드 부제 (선택)</div>
  </div>
  <div class="body">
    <!-- 섹션 타이틀 + 불렛 -->
    <div class="stitle">섹션 제목</div>
    <ul class="bl">
      <li>불렛 항목 — <span class="hl">강조 텍스트</span> 가능</li>
      <li>일반 불렛 항목</li>
    </ul>

    <!-- 그리드 + 카드 -->
    <div class="g3">
      <div class="card">
        <div class="card-title">카드 제목</div>
        <div class="card-value">1,234</div>
        <div class="card-desc">설명 텍스트</div>
      </div>
      <div class="card">...</div>
      <div class="card">...</div>
    </div>

    <!-- Stat 바 -->
    <div class="stats">
      <div class="stat-item">
        <div class="stat-num">37K+</div>
        <div class="stat-label">Properties</div>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <div class="stat-num">71+</div>
        <div class="stat-label">Channels</div>
      </div>
    </div>

    <!-- 표 -->
    <table class="dt">
      <thead>
        <tr>
          <th>항목</th>
          <th>값</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>데이터</td>
          <td>값</td>
        </tr>
      </tbody>
    </table>
  </div>
  <div class="foot">
    <div class="copyright">&copy; ONDA Inc.</div>
    <div class="snum">3 / 8</div>
  </div>
</div>
```

### 필수 포함 요소

- Google Fonts: Pretendard Variable CDN (위 CSS @import)
- **Noto Sans KR은 fallback으로만** — Pretendard가 우선 로드
- `en` modifier 사용 시: `<link rel="stylesheet" href="https://rsms.me/inter/inter.css">`를 `<head>`에 추가
- Chart.js: CDN `https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js`
- 화면 프레젠테이션 CSS + JS (방향키/클릭 전환, 뷰포트 스케일링) — 아래 표준 패턴 사용

### 화면 모드 CSS (필수)

브라우저로 열었을 때 한 번에 한 슬라이드만 화면에 꽉 차게 보이도록 한다.
PDF 캡처(`gen_pdf.mjs`)는 element screenshot이므로 이 CSS의 영향을 받지 않는다.

```css
@media screen {
  html, body {
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: #1a1a1a;
  }
  .slide {
    display: none;
    position: absolute;
    top: 50%;
    left: 50%;
    transform-origin: center center;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  }
  .slide.active {
    display: flex;
  }
}

@media print {
  html, body { background: #fff; }
  .slide { display: flex; }
}
```

### 화면 모드 JS (필수)

```html
<script>
  (function () {
    const slides = document.querySelectorAll('.slide');
    const total = slides.length;
    let cur = 0;

    // Headless(=PDF 캡처)에서는 scale 적용 금지 — element screenshot 해상도가 줄어든다
    const isHeadless = /HeadlessChrome/.test(navigator.userAgent);

    // 슬라이드 사이즈 — wide(16:9) 또는 A4 landscape
    const isWide = document.body.classList.contains('mode-wide');
    const SW = isWide ? 1280 : 1123;  // wide: 13.33in@96dpi, a4: 297mm@96dpi
    const SH = isWide ? 720  : 794;   // wide: 7.5in@96dpi,   a4: 210mm@96dpi

    function fit() {
      if (isHeadless) return;
      const W = window.innerWidth, H = window.innerHeight;
      const s = Math.min(W / SW, H / SH) * 0.95;
      slides.forEach((el) => {
        el.style.transform = `translate(-50%, -50%) scale(${s})`;
      });
    }

    function show(i) {
      cur = (i + total) % total;
      slides.forEach((el, j) => el.classList.toggle('active', j === cur));
    }

    function toggleFullscreen() {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen?.().catch(() => {});
      } else {
        document.exitFullscreen?.();
      }
    }

    document.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') show(cur + 1);
      else if (e.key === 'ArrowLeft' || e.key === 'PageUp') show(cur - 1);
      else if (e.key === 'Home') show(0);
      else if (e.key === 'End') show(total - 1);
      else if (e.key === 'f' || e.key === 'F') toggleFullscreen();
    });
    document.addEventListener('click', () => show(cur + 1));
    window.addEventListener('resize', fit);
    document.addEventListener('fullscreenchange', fit);

    fit();
    show(0);
  })();
</script>
```

**조작법** (브라우저에서 `.html` 열었을 때):
- `→` / `Space` / `PageDown` / 클릭 — 다음 슬라이드
- `←` / `PageUp` — 이전 슬라이드
- `Home` / `End` — 처음/마지막 슬라이드
- `F` — 전체화면 토글 (`Esc`로 종료)

### 기본 로고

로고를 별도로 제공하지 않으면 **반드시** ONDA 공식 로고를 사용한다:

```
https://cdn.prod.website-files.com/62fc3cdcd1a5bb1370c2d067/63c0a7b567846c336d75f050_onda.svg
```

- 커버: `<img class="onda-logo" src="위_URL" alt="ONDA">` (height: 28px)
- Footer에는 텍스트로 `© ONDA Inc.` 표기

### 로고 처리 (커스텀 로고 제공 시)

로고 이미지가 별도 제공되면:

- SVG/PNG 파일을 base64 data URI로 인라인 삽입
- GitHub private repo 파일은 `gh api repos/{owner}/{repo}/contents/{path} --jq '.content' | base64 -d`로 다운로드
- CSS로 `height: 28px; width: auto;` 제어

### Chart.js 주의사항

```javascript
Chart.defaults.font.family = "'Pretendard Variable', 'Pretendard', sans-serif";
Chart.defaults.font.size = 11;          // default 모드. simple 모드는 20으로 키움
Chart.defaults.plugins.legend.display = false;
Chart.defaults.animation.duration = 0;  // 필수 — PDF 캡처 시 빈 차트 방지

// simple 모드인 경우:
// Chart.defaults.font.size = 20;
// scales 옵션의 ticks.font.size도 20으로 같이 키움

// 차트 색상 팔레트 — ONDA 브랜드
// Primary: #004FC5, Secondary: #4A90D9, Tertiary: #A0C4F1
// Accent: #FF8C42, Gray: #C8CDD5

// 수평 바 차트 — 라벨 잘림 방지
options: {
  indexAxis: 'y',
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    y: { ticks: { autoSkip: false } } // 필수
  }
}
```

### AI 이미지 슬라이드 (Gemini)

도표나 차트로 표현하기 어려운 개념적 일러스트, 사진풍 이미지가 필요한 슬라이드에 Gemini API로 이미지를 생성하여 삽입할 수 있다.

**사용 조건**: `GEMINI_API_KEY` 환경변수 또는 프로젝트 `.env` 파일에 키가 설정되어 있어야 한다.

**생성 방법**:

```bash
# gemini-image 플러그인의 스크립트를 사용
pip3 install google-genai python-dotenv 2>/dev/null
python3 "${CLAUDE_SKILL_DIR}/../../gemini-image/skills/gemini-image/generate_images.py" \
  --prompt "프롬프트" --filename "slide-img.png" --outdir "/tmp" --ratio "16:9"
```

**HTML 삽입**: 생성된 이미지를 base64로 인라인하여 HTML에 삽입한다.

```bash
# base64 인코딩
IMG_B64=$(base64 -i /tmp/slide-img.png)
```

```html
<!-- 이미지 + 텍스트 레이아웃 (2열 그리드) -->
<div class="slide" id="s3">
  <div class="accent"></div>
  <div class="hbar">
    <h2>슬라이드 제목</h2>
  </div>
  <div class="body">
    <div class="g2">
      <div>
        <ul class="bl">
          <li>핵심 포인트</li>
          <li>설명 텍스트</li>
        </ul>
      </div>
      <div>
        <img class="slide-img" src="data:image/png;base64,{IMG_B64}" alt="설명">
      </div>
    </div>
  </div>
  <div class="foot">
    <div class="copyright">&copy; ONDA Inc.</div>
    <div class="snum">4 / 8</div>
  </div>
</div>

<!-- 전면 이미지 슬라이드 -->
<div class="slide" id="s4">
  <div class="accent"></div>
  <img class="slide-img-full" src="data:image/png;base64,{IMG_B64}" alt="설명">
  <div class="foot">
    <div class="copyright">&copy; ONDA Inc.</div>
    <div class="snum">5 / 8</div>
  </div>
</div>
```

**프롬프트 작성 팁**:
- ONDA 브랜드 컬러(#004FC5 블루)를 포함하면 슬라이드와 통일감 생김
- "professional, clean, minimal, business presentation style" 키워드 추가
- 한글 텍스트는 피하고 아이콘/숫자로 대체 → HTML 텍스트로 오버레이
- `--ratio 16:9`로 슬라이드 비율에 맞추기

**사용 판단 기준**:
- 차트/표/불렛으로 충분 → CSS 컴포넌트 사용 (기본)
- 개념도, 비유적 일러스트, 현장 사진풍 → Gemini 이미지 생성
- `GEMINI_API_KEY`가 없으면 이미지 생성을 건너뛰고 텍스트로 대체

## Phase 3: PDF 생성

HTML 작성이 완료되면 PDF를 생성한다.

### 사전 확인

```bash
npm ls puppeteer pdf-lib 2>/dev/null || npm install puppeteer pdf-lib
```

### 생성 명령

```bash
node "${CLAUDE_SKILL_DIR}/gen_pdf.mjs" <html-path> [pdf-path]
```

- `html-path`: 생성한 HTML 파일의 절대 경로
- `pdf-path`: (선택) PDF 출력 경로. 생략하면 HTML과 같은 경로에 `.pdf` 확장자

### 주의

- `page.pdf()` 방식 사용 금지 — flex/grid 레이아웃이 깨짐
- 반드시 스크린샷 → pdf-lib 방식 사용
- `deviceScaleFactor: 2`로 선명한 PDF 출력

## 삽질 방지 체크리스트

| 항목                             | 설명                                                                |
| -------------------------------- | ------------------------------------------------------------------- |
| **`<body class="mode-...">`**    | `mode-default` 단독 또는 `mode-simple`/`mode-wide`/`mode-dark`/`mode-en` 조합 |
| **simple 모드 콘텐츠 원칙**      | 불렛 3개 이하, `.g2`만, 한 슬라이드 한 메시지, 1줄 25자             |
| **wide 모드 PDF 사이즈**         | `gen_pdf.mjs`가 `body.mode-wide`를 감지해 자동으로 16:9 페이지로 생성 |
| **en 모드 폰트 link**            | `<head>`에 `<link rel="stylesheet" href="https://rsms.me/inter/inter.css">` 추가 |
| **ONDA 로고 필수**               | 커버에 반드시 `https://cdn.prod.website-files.com/...onda.svg` 사용 |
| **Pretendard 폰트**              | `@import` 반드시 `<style>` 최상단에 포함                            |
| **브랜드 컬러 #004FC5**          | 헤더, 타이틀, 악센트, Stat 등 모든 강조에 사용                      |
| **악센트 라인 5px**              | 모든 슬라이드 상단에 `.accent` div 포함                             |
| **Footer 필수**                  | 모든 콘텐츠 슬라이드에 `.foot` 포함 (copyright + 슬라이드 번호)     |
| Chart.js `autoSkip: false`       | 수평 바 y축 라벨 자동 생략 방지                                     |
| Chart.js `animation.duration: 0` | 스크린샷 시 빈 차트 방지                                            |
| `maintainAspectRatio: false`     | 차트가 컨테이너 높이를 채우도록                                     |
| 차트 컨테이너 높이 명시          | `height: 360px` 등. `flex:1`은 print에서 무시됨                     |
| `.stitle` border-left            | 3px solid #004FC5 — 섹션 구분 역할                                  |
| 불렛 커스텀 도트                 | `::before`로 블루 도트 — `list-style: none` 필수                    |
| screen 모드 CSS 분리             | `@media screen {}` 안에 프레젠테이션 전용 스타일                    |

## Phase 4: 완료 보고

생성 완료 후 보고:

- HTML 파일 경로
- PDF 파일 경로 및 용량
- 슬라이드 수
- 브라우저에서 확인하는 방법: `file://` URL

## Error handling

- puppeteer/pdf-lib 미설치 → `npm install puppeteer pdf-lib` 실행
- 차트가 빈 채로 캡처 → `animation.duration: 0` 확인, 대기 시간 증가
- SVG 로고 렌더링 실패 → PNG로 변환 후 사용
- GitHub private repo 접근 불가 → `gh auth status` 확인 안내
- Pretendard 폰트 미로드 → CDN URL 확인, `networkidle0` 대기 확인
