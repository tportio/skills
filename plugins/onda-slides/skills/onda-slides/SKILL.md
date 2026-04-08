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
3. **로고**: 이미지 파일 경로 또는 base64 data URI (없으면 조직명 텍스트)
4. **슬라이드 내용**: 각 슬라이드별 헤더, 불렛, 차트, 표, 그리드 구성

사용자가 이미 충분한 정보를 제공했으면 바로 Phase 2로 진행한다.

## Phase 2: HTML 생성

아래 CSS/HTML 규칙을 **반드시** 따른다.

### CSS 핵심 규칙

```css
@page { size: A4 landscape; margin: 0; }

.slide {
  width: 297mm;
  height: 210mm;
  position: relative;
  overflow: hidden;
  page-break-after: always;
  background: #fff;
}

/* 헤더 바 */
.hbar {
  height: 70px;
  background: #2a3f5f;
  display: flex;
  align-items: center;
  padding-left: 44px;
}
.hbar h2 {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
}

/* 본문 — 헤더와 충분한 여백 */
.body {
  padding: 36px 44px 16px;
}

/* 슬라이드 번호 */
.snum {
  position: absolute;
  bottom: 6px; right: 14px;
  font-size: 10px;
  color: #aaa;
}

/* 커버 */
.cover-content {
  width: 100%; height: 210mm;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}
.cover-content h1 {
  font-size: 36px;
  font-weight: 700;
  color: #1a2a44;
}
.cover-content .sub { font-size: 15px; color: #666; margin-top: 10px; }
.cover-content .date { font-size: 14px; color: #999; margin-top: 28px; }
.cover-content .logos { margin-top: 32px; display: flex; align-items: center; gap: 16px; }
.cover-content .logos .onda-logo { height: 32px; width: auto; }

/* 섹션 타이틀 */
.stitle {
  font-size: 15px;
  font-weight: 700;
  color: #1a2a44;
  margin-bottom: 10px;
  margin-top: 18px;
}

/* 불렛 */
ul.bl li {
  font-size: 14px;
  line-height: 1.7;
  margin-bottom: 10px;
}

/* 표 */
table.dt th { padding: 10px 14px; }
table.dt td { padding: 10px 14px; }

/* 그리드 */
.g2 { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.g2w { display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 24px; }
.g3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
```

### HTML 패턴

```html
<!-- 표지 -->
<div class="slide active" id="s0">
  <div class="cover-content">
    <h1>제목</h1>
    <div class="sub">부제목</div>
    <div class="date">2026.04</div>
    <div class="logos">
      <img class="onda-logo" src="..." alt="ONDA">
    </div>
  </div>
</div>

<!-- 일반 슬라이드 -->
<div class="slide" id="s1">
  <div class="hbar"><h2>슬라이드 제목</h2></div>
  <div class="body">
    <ul class="bl"><li>불렛 항목</li></ul>
    <div class="g2">
      <div>좌측</div>
      <div>우측</div>
    </div>
  </div>
  <div class="snum">2 / 8</div>
</div>
```

### 필수 포함 요소

- Google Fonts: `Noto Sans KR` (wght 300;400;500;600;700)
- Chart.js: CDN `https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js`
- 화면 프레젠테이션 JS (방향키/클릭 전환, 뷰포트 스케일링)

### Chart.js 주의사항

```javascript
Chart.defaults.font.family = "'Noto Sans KR', sans-serif";
Chart.defaults.font.size = 11;
Chart.defaults.plugins.legend.display = false;
Chart.defaults.animation.duration = 0; // 필수 — PDF 캡처 시 빈 차트 방지

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

### 로고 처리

로고 이미지가 제공되면:
- SVG/PNG 파일을 base64 data URI로 인라인 삽입
- GitHub private repo 파일은 `gh api repos/{owner}/{repo}/contents/{path} --jq '.content' | base64 -d`로 다운로드
- CSS로 `height: 32px; width: auto;` 제어

로고가 없으면 텍스트 span으로 대체:
```html
<span style="font-size:24px;font-weight:700;color:#1a2a44;letter-spacing:0.06em">조직명</span>
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

| 항목 | 설명 |
|------|------|
| Chart.js `autoSkip: false` | 수평 바 y축 라벨 자동 생략 방지 |
| Chart.js `animation.duration: 0` | 스크린샷 시 빈 차트 방지 |
| `maintainAspectRatio: false` | 차트가 컨테이너 높이를 채우도록 |
| 차트 컨테이너 높이 명시 | `height: 360px` 등. `flex:1`은 print에서 무시됨 |
| 헤더 높이 70px | 너무 낮으면 상단 쏠림 |
| body padding-top 36px | 헤더-본문 여백 |
| 불렛 margin-bottom 10px | 줄 간격 |
| `.stitle` margin-top 18px | 섹션 간 여백 |
| screen 모드 CSS 분리 | `@media screen {}` 안에 프레젠테이션 전용 스타일 |

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
