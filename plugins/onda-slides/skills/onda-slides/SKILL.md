---
name: onda-slides
description: ONDA 공통 템플릿으로 슬라이드 프레젠테이션(HTML + PDF)을 생성한다. 차트, 표, 그리드 레이아웃 지원.
disable-model-invocation: false
argument-hint: "<슬라이드 데이터 또는 지시사항>"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent, AskUserQuestion
---

# Presentation PDF Generator

HTML 단일 파일로 슬라이드를 만들고, Puppeteer 스크린샷 방식으로 PDF를 생성한다.

## Input

`$ARGUMENTS`

사용자가 슬라이드 데이터(제목, 내용, 차트, 표 등)를 자연어로 제공한다.

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
Primary Blue   : #0047BA
Dark Text      : #1a1a1a
Body Text      : #444
Secondary Text : #888
Light Text     : #aaa
Border         : #e8ecf2
Row Stripe     : #f8f9fc
Background     : #fff
Accent Line    : #0047BA (5px)
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
  color: #1a1a1a;
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
  background: #0047ba;
}

/* ─── 슬라이드 헤더 (악센트 라인 아래) ─── */
.hbar {
  padding: 40px 48px 0;
}
.hbar h2 {
  font-size: 22px;
  font-weight: 700;
  color: #0047ba;
  letter-spacing: -0.3px;
}
.hbar .hdesc {
  font-size: 13px;
  font-weight: 400;
  color: #888;
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
  border-top: 1px solid #e8ecf2;
}
.foot .copyright {
  font-size: 9px;
  font-weight: 400;
  color: #bbb;
}
.foot .snum {
  font-size: 9px;
  font-weight: 500;
  color: #aaa;
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
  background: #0047ba;
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
  color: #aaa;
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
  color: #0047ba;
  line-height: 1.2;
  letter-spacing: -0.5px;
}
.cover-body .sub {
  font-size: 15px;
  color: #666;
  line-height: 1.6;
  margin-top: 16px;
  max-width: 520px;
}
.cover-body .date {
  font-size: 13px;
  color: #aaa;
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
  border: 52px solid rgba(0, 71, 186, 0.08);
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
  border-top: 1px solid #eee;
}
.cover-foot .products {
  display: flex;
  gap: 12px;
}
.cover-foot .pill {
  font-size: 10px;
  font-weight: 500;
  color: #0047ba;
  padding: 4px 14px;
  border-radius: 20px;
  border: 1px solid rgba(0, 71, 186, 0.2);
  background: rgba(0, 71, 186, 0.04);
}
.cover-foot .web {
  font-size: 10px;
  color: #bbb;
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
  color: #0047ba;
}
.section-content .sub {
  font-size: 14px;
  color: #888;
  margin-top: 10px;
}

/* ═══════════════════════════════════════
   콘텐츠 컴포넌트
   ═══════════════════════════════════════ */

/* 섹션 타이틀 */
.stitle {
  font-size: 15px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 10px;
  margin-top: 18px;
  padding-left: 10px;
  border-left: 3px solid #0047ba;
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
  color: #444;
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
  background: #0047ba;
}

/* 하이라이트 텍스트 — 문장 내 강조 */
.hl {
  color: #0047ba;
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
  color: #0047ba;
}
.stat-label {
  font-size: 10px;
  font-weight: 500;
  color: #aaa;
  letter-spacing: 1px;
  text-transform: uppercase;
  margin-top: 4px;
}
.stat-divider {
  width: 1px;
  height: 36px;
  background: #ddd;
}

/* Pill 태그 */
.pill {
  display: inline-block;
  font-size: 11px;
  font-weight: 500;
  color: #0047ba;
  padding: 5px 14px;
  border-radius: 20px;
  border: 1px solid rgba(0, 71, 186, 0.2);
  background: rgba(0, 71, 186, 0.04);
}

/* 카드 박스 */
.card {
  background: #fff;
  border: 1px solid #e8ecf2;
  border-radius: 8px;
  padding: 20px;
}
.card .card-title {
  font-size: 14px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 8px;
}
.card .card-value {
  font-size: 26px;
  font-weight: 800;
  color: #0047ba;
}
.card .card-desc {
  font-size: 12px;
  color: #888;
  margin-top: 4px;
}

/* 표 */
table.dt {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
table.dt thead th {
  background: #0047ba;
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
  border-bottom: 1px solid #e8ecf2;
  color: #444;
}
table.dt tbody tr:nth-child(even) {
  background: #f8f9fc;
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
  background: #e8ecf2;
  margin: 16px 0;
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
```

### HTML 패턴

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
- Chart.js: CDN `https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js`
- 화면 프레젠테이션 JS (방향키/클릭 전환, 뷰포트 스케일링)

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
Chart.defaults.font.size = 11;
Chart.defaults.plugins.legend.display = false;
Chart.defaults.animation.duration = 0; // 필수 — PDF 캡처 시 빈 차트 방지

// 차트 색상 팔레트 — ONDA 브랜드
// Primary: #0047BA, Secondary: #4A90D9, Tertiary: #A0C4F1
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
| **ONDA 로고 필수**               | 커버에 반드시 `https://cdn.prod.website-files.com/...onda.svg` 사용 |
| **Pretendard 폰트**              | `@import` 반드시 `<style>` 최상단에 포함                            |
| **브랜드 컬러 #0047BA**          | 헤더, 타이틀, 악센트, Stat 등 모든 강조에 사용                      |
| **악센트 라인 5px**              | 모든 슬라이드 상단에 `.accent` div 포함                             |
| **Footer 필수**                  | 모든 콘텐츠 슬라이드에 `.foot` 포함 (copyright + 슬라이드 번호)     |
| Chart.js `autoSkip: false`       | 수평 바 y축 라벨 자동 생략 방지                                     |
| Chart.js `animation.duration: 0` | 스크린샷 시 빈 차트 방지                                            |
| `maintainAspectRatio: false`     | 차트가 컨테이너 높이를 채우도록                                     |
| 차트 컨테이너 높이 명시          | `height: 360px` 등. `flex:1`은 print에서 무시됨                     |
| `.stitle` border-left            | 3px solid #0047BA — 섹션 구분 역할                                  |
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
