/* ═══════════════════════════════════════════════════════════════
   ONDA Slides — Runtime
   - viewport scaling (화면 모드)
   - keyboard / click 네비게이션
   - fullscreen 토글 (F)
   - auto-fit: 슬라이드별 base font-size 자동 조정 (콘텐츠 양에 맞춤)

   v2.0.0 bug fixes:
   - fit이 show() 안에서 활성 슬라이드에 대해 재실행 → 화면 네비 시 6px 깨짐 차단
   - gen_pdf.mjs도 active 토글 후 __fitContent 호출 → PDF에서도 같은 fix
   - getAvailable()가 .body 자체 vertical padding도 차감 → wide 모드 오버플로우 차단
   - .slide의 display는 CSS @media 분기 안에만 → modifier specificity 함정 차단
   ═══════════════════════════════════════════════════════════════ */
(function () {
  const slides = document.querySelectorAll('.slide');
  const total = slides.length;
  let cur = 0;

  // Headless(=PDF 캡처)에서는 viewport scale 적용 금지 — element screenshot 해상도가 줄어든다
  const isHeadless = /HeadlessChrome/.test(navigator.userAgent);

  // 슬라이드 사이즈 — wide(16:9) 또는 A4 landscape
  const isWide = document.body.classList.contains('mode-wide');
  const SW = isWide ? 1280 : 1123;  // wide: 13.33in@96dpi, a4: 297mm@96dpi
  const SH = isWide ? 720  : 794;   // wide: 7.5in@96dpi,   a4: 210mm@96dpi

  // ── viewport fit (화면 모드 전용) ────────────────────────────
  function fitViewport() {
    if (isHeadless) return;
    const W = window.innerWidth, H = window.innerHeight;
    const s = Math.min(W / SW, H / SH) * 0.95;
    slides.forEach((el) => {
      el.style.transform = `translate(-50%, -50%) scale(${s})`;
    });
  }

  // ── auto wrapper inject ─────────────────────────────────────
  // 모델은 .body에 콘텐츠를 직접 넣음. JS가 첫 fit 직전에 .body-fit으로 자동 wrap.
  function ensureFitWrapper(slide) {
    const body = slide.querySelector(':scope > .body');
    if (!body) return null;
    let fit = body.querySelector(':scope > .body-fit');
    if (fit) return fit;
    if (body.children.length === 0 && body.textContent.trim() === '') return null;
    fit = document.createElement('div');
    fit.className = 'body-fit';
    while (body.firstChild) fit.appendChild(body.firstChild);
    body.appendChild(fit);
    return fit;
  }

  // ── content fit (슬라이드별 base font-size 자동 조정) ────────
  // 가용 영역 = 슬라이드 height - slide padding(top+bottom) - hbar(height+margin) - body padding(top+bottom)
  // base 변경 시 hbar/padding도 비례 축소되므로 매 iteration마다 재측정.
  function fitContent(slide) {
    // canvas(차트) 슬라이드는 fit 대상에서 제외 — Chart.js의 px 폰트가 base와 따로 놀아 균형 깨짐
    if (slide.querySelector('canvas')) return;
    const body = slide.querySelector(':scope > .body');
    const fit = ensureFitWrapper(slide);
    if (!body || !fit) return;
    const hbar = slide.querySelector(':scope > .hbar');

    function getAvailable() {
      const slideCs = getComputedStyle(slide);
      const bodyCs = getComputedStyle(body);
      const slidePadV = (parseFloat(slideCs.paddingTop) || 0) + (parseFloat(slideCs.paddingBottom) || 0);
      const bodyPadV  = (parseFloat(bodyCs.paddingTop)  || 0) + (parseFloat(bodyCs.paddingBottom)  || 0);
      const hbarH = hbar ? hbar.offsetHeight : 0;
      const hbarMb = hbar ? parseFloat(getComputedStyle(hbar).marginBottom) || 0 : 0;
      // hidden 슬라이드는 clientHeight=0 → 음수 가능. 호출자가 false 받고 처리.
      return slide.clientHeight - slidePadV - bodyPadV - hbarH - hbarMb;
    }

    const MAX = 16, MIN = 6;
    // 1차: max base로 시도
    slide.style.fontSize = MAX + 'px';
    void fit.offsetHeight;
    const avail = getAvailable();
    if (avail <= 0) {
      // 슬라이드가 hidden 상태(=clientHeight 0) — fit 보류, MAX 유지
      // show()가 활성화 후 다시 fit을 호출해서 정확히 측정한다
      return;
    }
    if (fit.scrollHeight <= avail) return;  // 콘텐츠 적음 → 큰 폰트 그대로

    // 2차: binary search
    let lo = MIN, hi = MAX;
    for (let i = 0; i < 12 && hi - lo > 0.25; i++) {
      const mid = (lo + hi) / 2;
      slide.style.fontSize = mid + 'px';
      void fit.offsetHeight;
      if (fit.scrollHeight <= getAvailable()) lo = mid;
      else hi = mid;
    }
    slide.style.fontSize = lo + 'px';
  }

  function fitAllContent() {
    slides.forEach(fitContent);
  }

  // ── 슬라이드 네비게이션 ─────────────────────────────────────
  function show(i) {
    cur = (i + total) % total;
    slides.forEach((el, j) => el.classList.toggle('active', j === cur));
    // fix: 화면 모드에서 hidden 시점에 fit이 잘못 측정된 슬라이드를 활성화 직후 재측정
    // headless(PDF)는 gen_pdf.mjs가 직접 __fitAllContent를 호출하므로 중복 호출 무방
    fitContent(slides[cur]);
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
  window.addEventListener('resize', fitViewport);
  document.addEventListener('fullscreenchange', fitViewport);

  // 폰트/이미지 로드 후 초기화
  Promise.resolve(document.fonts ? document.fonts.ready : null).then(() => {
    fitAllContent();
    // gen_pdf.mjs가 슬라이드 토글 후 다시 부를 수 있도록 노출
    window.__fitContent = fitContent;
    window.__fitAllContent = fitAllContent;
    fitViewport();
    show(0);
  });
})();
