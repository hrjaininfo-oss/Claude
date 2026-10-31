// Render composition.html frame-by-frame with headless Chromium, encode with ffmpeg.
// Usage: node video/pro/render.js [--fps 30] [--workers 4] [--frames t1,t2,...  (stills only)]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs'), path = require('path');

const HERE = __dirname;
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : d; };
const FPS = +opt('fps', 30), WORKERS = +opt('workers', 4), STILLS = opt('frames', null);
const OUTDIR = opt('out', path.join(HERE, 'build'));
fs.mkdirSync(OUTDIR, { recursive: true });

function html() {
  let h = fs.readFileSync(path.join(HERE, 'composition.html'), 'utf8');
  const b64 = f => 'data:font/ttf;base64,' + fs.readFileSync(path.join(HERE, 'fonts', f)).toString('base64');
  return h.replace('FONT_SERIF_REGULAR', b64('InstrumentSerif-Regular.ttf')).replace('FONT_SERIF_ITALIC', b64('InstrumentSerif-Italic.ttf'));
}

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('page error:', e.message));
  await page.setContent(html(), { waitUntil: 'load' });
  await page.evaluate(async () => {
    await Promise.all(['400 100px "Instrument Serif"', 'italic 400 100px "Instrument Serif"', '700 100px "Inter Display"', '600 100px "Inter Display"',
      '400 30px Inter', '500 30px Inter', '700 30px Inter', '500 30px "JetBrains Mono"', '400 30px "JetBrains Mono"'].map(f => document.fonts.load(f)));
    await document.fonts.ready;
  });
  return page;
}

(async () => {
  const browser = await chromium.launch();
  if (STILLS) {
    const page = await openPage(browser);
    for (const t of STILLS.split(',').map(Number)) {
      await page.evaluate(t => window.seek(t), t);
      await page.screenshot({ path: path.join(OUTDIR, `still_${t.toFixed(2)}.png`) });
    }
    await browser.close(); return;
  }
  const DUR = 62.5, N = Math.round(DUR * FPS), per = Math.ceil(N / WORKERS);
  const t0 = Date.now();
  await Promise.all([...Array(WORKERS).keys()].map(async w => {
    const a = w * per, b = Math.min(N, a + per);
    const page = await openPage(browser);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-pix_fmt', 'yuv420p', path.join(OUTDIR, `seg${w}.mp4`)], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let f = a; f < b; f++) {
      await page.evaluate(t => window.seek(t), f / FPS);
      const buf = await page.screenshot({ type: 'jpeg', quality: 96 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (w === 0 && f % 60 === 0) console.log(`worker0 ${f - a}/${b - a}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }));
  fs.writeFileSync(path.join(OUTDIR, 'segs.txt'), [...Array(WORKERS).keys()].map(w => `file 'seg${w}.mp4'`).join('\n'));
  console.log('frames done in', ((Date.now() - t0) / 1000).toFixed(0), 's');
  await browser.close();
})();
