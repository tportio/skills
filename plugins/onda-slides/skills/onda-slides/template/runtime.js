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

    // stylesheet 기본값을 MAX로 — wide 모드에선 .slide { font-size: 18px } 자동 반영
    // inline style 비워서 stylesheet 값 다시 읽음 (이전 fit 호출이 줄여놓은 값 무시)
    // 가드: hidden/detached 슬라이드에서 0 또는 NaN 반환되는 엣지 케이스 → 16으로 fallback
    slide.style.fontSize = '';
    const computedFs = parseFloat(getComputedStyle(slide).fontSize);
    const MAX = computedFs > 0 ? computedFs : 16;
    const MIN = 6;
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
  // 양 끝에서 wrap-around 안 함 — 마지막에서 → / 첫 페이지에서 ← 누르면 그대로 멈춤
  // URL hash로 페이지 추적 — `#3`이면 3번째 슬라이드(1-indexed)에서 시작, 공유 가능
  function show(i, opts) {
    const next = Math.max(0, Math.min(total - 1, i));
    const force = opts && opts.force;
    if (!force && next === cur && slides[cur]?.classList.contains('active')) return;
    cur = next;
    slides.forEach((el, j) => el.classList.toggle('active', j === cur));
    // fix: 화면 모드에서 hidden 시점에 fit이 잘못 측정된 슬라이드를 활성화 직후 재측정
    fitContent(slides[cur]);
    const hash = `#${cur + 1}`;
    if (location.hash !== hash) history.replaceState(null, '', hash);
  }

  function slideFromHash() {
    const m = location.hash.match(/^#(\d+)$/);
    if (!m) return 0;
    return Math.max(0, Math.min(total - 1, parseInt(m[1], 10) - 1));
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen?.().catch(() => {});
    } else {
      document.exitFullscreen?.();
    }
  }

  // input/textarea/contenteditable에선 단축키 무시 — 미래에 슬라이드에 폼 넣을 때 안전
  function isFormTarget(t) {
    if (!t) return false;
    const tag = t.tagName;
    return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || t.isContentEditable;
  }
  document.addEventListener('keydown', (e) => {
    if (isFormTarget(e.target)) return;
    if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') show(cur + 1);
    else if (e.key === 'ArrowLeft' || e.key === 'PageUp') show(cur - 1);
    else if (e.key === 'Home') show(0);
    else if (e.key === 'End') show(total - 1);
    else if (e.key === 'f' || e.key === 'F') toggleFullscreen();
  });
  // 클릭으로 다음 슬라이드. 단, 인터랙티브 요소(링크/버튼/폼/canvas) 클릭은 제외
  // → 차트 툴팁, 향후 추가될 링크, 텍스트 선택 시 의도치 않은 페이지 이동 차단
  // → URL hash 공유 사용자가 우연한 클릭으로 hash 깨지는 것도 방지
  document.addEventListener('click', (e) => {
    if (e.target.closest('a, button, input, textarea, select, canvas, [data-no-advance]')) return;
    show(cur + 1);
  });
  window.addEventListener('resize', fitViewport);
  document.addEventListener('fullscreenchange', fitViewport);
  // 외부에서 hash로 점프 (브라우저 ←/→, 링크 클릭). show()의 history.replaceState는
  // hashchange를 발생시키지 않음 — 무한루프 안 생김.
  // pushState로 바꿔서 back-button 지원할 거면 'popstate'도 함께 listen해야 함.
  window.addEventListener('hashchange', () => show(slideFromHash(), { force: true }));

  // 폰트/이미지 로드 후 초기화
  Promise.resolve(document.fonts ? document.fonts.ready : null).then(() => {
    fitAllContent();
    // gen_pdf.mjs가 슬라이드 토글 후 다시 부를 수 있도록 노출
    window.__fitContent = fitContent;
    window.__fitAllContent = fitAllContent;
    fitViewport();
    show(slideFromHash(), { force: true });
  });
})();
