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
await page.setViewport({ width: 1280, height: 720, deviceScaleFactor: 2 });
await page.goto(htmlUrl, { waitUntil: 'networkidle0', timeout: 15000 });
await new Promise(r => setTimeout(r, 2000));

const slideCount = await page.evaluate(() => document.querySelectorAll('.slide').length);
const pngPaths = [];

for (let i = 0; i < slideCount; i++) {
  await page.evaluate((idx) => {
    document.querySelectorAll('.slide').forEach((s, j) => {
      s.classList.toggle('active', j === idx);
    });
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
  const pg = pdfDoc.addPage([841.89, 595.28]); // A4 landscape
  pg.drawImage(img, { x: 0, y: 0, width: 841.89, height: 595.28 });
}

const pdfBytes = await pdfDoc.save();
fs.writeFileSync(pdfPath, pdfBytes);
console.log(`PDF saved: ${pdfPath} (${(pdfBytes.length / 1024 / 1024).toFixed(1)}MB, ${slideCount} slides)`);

pngPaths.forEach(p => fs.unlinkSync(p));
