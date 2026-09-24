// 把 cartoon.html 逐帧渲染成 MP4（带背景音乐）。
// 依赖：playwright、ffmpeg、python3 + numpy
// 用法：node render.js [输出.mp4]
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const path = require('path');
const os = require('os');

const FPS = 30;
const FFMPEG = process.env.FFMPEG || 'ffmpeg';
const out = path.resolve(process.argv[2] || path.join(__dirname, 'health-cartoon.mp4'));

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 720, height: 1280 } });
  await page.goto('file://' + path.join(__dirname, 'cartoon.html') + '?export');
  await page.evaluate(() => document.fonts.ready);
  const total = await page.evaluate(() => TOTAL);

  const wav = path.join(os.tmpdir(), `health-cartoon-${process.pid}.wav`);
  execFileSync('python3', [path.join(__dirname, 'music.py'), wav, String(total)]);

  const ff = spawn(FFMPEG, [
    '-loglevel', 'error', '-y',
    '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
    '-i', wav,
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-preset', 'medium',
    '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-ac', '2', '-ar', '48000', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out,
  ], { stdio: ['pipe', 'inherit', 'inherit'] });

  const frames = Math.round(total * FPS);
  for (let i = 0; i < frames; i++) {
    const b64 = await page.evaluate(t => { render(t); return document.getElementById('c').toDataURL('image/png').split(',')[1]; }, i / FPS);
    if (!ff.stdin.write(Buffer.from(b64, 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 150 === 0) process.stdout.write(`\r${i}/${frames}`);
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on('close', c => (c === 0 ? res() : rej(new Error('ffmpeg exit ' + c)))));
  await browser.close();
  console.log(`\n已生成 ${out}`);
})();
