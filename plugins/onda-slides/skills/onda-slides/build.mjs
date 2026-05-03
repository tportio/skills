#!/usr/bin/env node
/**
 * ONDA Slides Builder
 *
 * Combines template/base.html + template/styles.css + template/runtime.js
 * with a slides fragment to produce a self-contained HTML presentation.
 *
 * Usage:
 *   node build.mjs <slides-fragment> <output> [--modifiers a,b,...] [--title "..."]
 *
 * - <slides-fragment>: file containing only <div class="slide">...</div> blocks
 * - <output>:          absolute path for the output HTML
 * - --modifiers:       comma-separated subset of {simple, wide, dark, en}
 * - --title:           HTML <title>. Default: extracted from first <h1>/<h2>, else "ONDA Slides"
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function parseArgs(argv) {
  const positional = [];
  const flags = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      flags[a.slice(2)] = argv[i + 1];
      i++;
    } else {
      positional.push(a);
    }
  }
  return { positional, flags };
}

const { positional, flags } = parseArgs(process.argv.slice(2));
if (positional.length < 2) {
  console.error('Usage: node build.mjs <slides-fragment> <output> [--modifiers a,b,...] [--title "..."]');
  process.exit(1);
}

const [slidesPath, outputPath] = positional;
const modifiers = (flags.modifiers ?? '')
  .split(',')
  .map((s) => s.trim())
  .filter(Boolean);

const ALLOWED_MODIFIERS = new Set(['simple', 'wide', 'dark', 'en']);
for (const m of modifiers) {
  if (!ALLOWED_MODIFIERS.has(m)) {
    console.error(`Unknown modifier: ${m}. Allowed: ${[...ALLOWED_MODIFIERS].join(', ')}`);
    process.exit(1);
  }
}

const slidesFragment = fs.readFileSync(slidesPath, 'utf8');
if (!/<div\s+class=["'][^"']*\bslide\b/.test(slidesFragment)) {
  console.error(`Error: ${slidesPath} contains no <div class="slide ..."> blocks. Aborting.`);
  process.exit(1);
}
const styles = fs.readFileSync(path.join(__dirname, 'template/styles.css'), 'utf8');
const runtime = fs.readFileSync(path.join(__dirname, 'template/runtime.js'), 'utf8');
const baseTemplate = fs.readFileSync(path.join(__dirname, 'template/base.html'), 'utf8');

const isEn = modifiers.includes('en');

let title = flags.title;
if (!title) {
  // 커버의 <h1>이 있으면 우선, 없으면 <h2> fallback
  const h1 = slidesFragment.match(/<h1[^>]*>([^<]+)<\/h1>/);
  const h2 = slidesFragment.match(/<h2[^>]*>([^<]+)<\/h2>/);
  title = (h1?.[1] ?? h2?.[1] ?? 'ONDA Slides').trim();
}

const modeClasses = modifiers.length === 0
  ? 'mode-default'
  : modifiers.map((m) => `mode-${m}`).join(' ');

const extraHead = isEn
  ? '<link rel="stylesheet" href="https://rsms.me/inter/inter.css">'
  : '';

// String.prototype.replace는 $&/$1/$$ 등을 특수 처리한다.
// 콜백 형식으로 두면 replacement 문자열 그대로 박힘 — CSS/JS에 $ 들어가도 안전.
const fill = (tpl, marker, value) => tpl.replace(marker, () => value);

const html = [
  ['{{LANG}}',       isEn ? 'en' : 'ko'],
  ['{{TITLE}}',      title],
  ['{{EXTRA_HEAD}}', extraHead],
  ['{{MODE_CLASS}}', modeClasses],
  ['{{SLIDES}}',     slidesFragment],
  ['{{STYLES}}',     styles],
  ['{{RUNTIME}}',    runtime],
].reduce((acc, [k, v]) => fill(acc, k, v), baseTemplate);

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, html);
console.log(`Built: ${outputPath} (modifiers: ${modifiers.join(',') || 'none'})`);
