#!/usr/bin/env node
/**
 * Presentation PDF Generator
 *
 * Usage: node gen_pdf.mjs <html-path> [pdf-path]
 *   html-path: absolute path to the HTML file (or file:// URL)
 *   pdf-path:  absolute path for the output PDF (default: same as html with .pdf extension)
 */
import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

const htmlArg = process.argv[2];
if (!htmlArg) {
  console.error('Usage: node gen_pdf.mjs <html-path> [pdf-path]');
  process.exit(1);
}

const htmlUrl = htmlArg.startsWith('file://') ? htmlArg : `file://${htmlArg}`;
const htmlPath = htmlArg.replace(/^file:\/\//, '');
const pdfPath = process.argv[3] || htmlPath.replace(/\.html$/, '.pdf');

const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
const page = await browser.newPage();
// viewport는 wide(1280x720)도 들어갈 수 있게 충분히 크게
await page.setViewport({ width: 1400, height: 900, deviceScaleFactor: 2 });
await page.goto(htmlUrl, { waitUntil: 'networkidle0', timeout: 15000 });
await new Promise(r => setTimeout(r, 2000));

// modifier 감지 — wide면 PDF 페이지 사이즈도 16:9
const isWide = await page.evaluate(() => document.body.classList.contains('mode-wide'));
// PDF 페이지 사이즈 (pt 단위, 1pt = 1/72in)
// A4 landscape: 11.69in × 8.27in = 841.89 × 595.28
// 16:9 wide:    13.33in × 7.5in  = 960    × 540
const PAGE_W = isWide ? 960 : 841.89;
const PAGE_H = isWide ? 540 : 595.28;

const slideCount = await page.evaluate(() => document.querySelectorAll('.slide').length);
const pngPaths = [];

for (let i = 0; i < slideCount; i++) {
  await page.evaluate((idx) => {
    document.querySelectorAll('.slide').forEach((s, j) => {
      s.classList.toggle('active', j === idx);
    });
    // active 토글 후 fit 재실행 — display:none이었던 슬라이드는 clientHeight=0이라
    // 초기 fitAllContent에서 측정 못 하고 16px로 남아 있음. 활성화 직후 다시 측정.
    if (typeof window.__fitContent === 'function') {
      window.__fitContent(document.querySelectorAll('.slide')[idx]);
    }
  }, i);
  await new Promise(r => setTimeout(r, 300));

  const p = path.join(path.dirname(pdfPath), `_slide_${i}.png`);
  const el = await page.$('.slide.active');
  await el.screenshot({ path: p, type: 'png' });
  pngPaths.push(p);
  console.log(`Captured slide ${i + 1}/${slideCount}`);
}
await browser.close();

const { PDFDocument } = await import('pdf-lib');
const pdfDoc = await PDFDocument.create();

for (const p of pngPaths) {
  const imgBytes = fs.readFileSync(p);
  const img = await pdfDoc.embedPng(imgBytes);
  const pg = pdfDoc.addPage([PAGE_W, PAGE_H]);
  pg.drawImage(img, { x: 0, y: 0, width: PAGE_W, height: PAGE_H });
}

const pdfBytes = await pdfDoc.save();
fs.writeFileSync(pdfPath, pdfBytes);
console.log(`PDF saved: ${pdfPath} (${(pdfBytes.length / 1024 / 1024).toFixed(1)}MB, ${slideCount} slides)`);

pngPaths.forEach(p => fs.unlinkSync(p));
