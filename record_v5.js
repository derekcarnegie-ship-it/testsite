/**
 * Records carbon_emissions_gdp_v5.html as an MP4.
 * Uses puppeteer-core (existing Chrome) + ffmpeg-static.
 * Captures one full animation loop (~31 s) at ~30 fps.
 */

const puppeteer  = require('puppeteer-core');
// Use system FFmpeg (installed via winget) — more reliable than npm binary on Windows
const ffmpegPath = 'C:/Users/derek/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.0.1-full_build/bin/ffmpeg.exe';
const { spawnSync } = require('child_process');
const fs   = require('fs');
const path = require('path');

const CHROME   = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const HTML     = 'file:///C:/Users/derek/Desktop/Claudetests/carbon_emissions_gdp_v5.html';
const OUTPUT   = 'C:/Users/derek/Desktop/Claudetests/carbon_emissions_gdp_v5.mp4';
const TMPDIR   = path.join('C:/Users/derek/Desktop/Claudetests', 'tmp_frames');
const RECORD_MS = 34000;   // one full loop ≈ 31.2 s, +3 s safety margin
const WIDTH    = 1280;
const HEIGHT   = 720;

async function main() {
  // Prepare temp directory
  if (fs.existsSync(TMPDIR)) fs.rmSync(TMPDIR, { recursive: true });
  fs.mkdirSync(TMPDIR);

  console.log('Launching browser…');
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu'],
    defaultViewport: { width: WIDTH, height: HEIGHT },
  });

  const page = await browser.newPage();

  // Create CDP session (API differs across puppeteer-core versions)
  const client = typeof page.createCDPSession === 'function'
    ? await page.createCDPSession()
    : await page.target().createCDPSession();

  console.log('Loading page…');
  await page.goto(HTML, { waitUntil: 'networkidle0', timeout: 30000 });

  const frames = [];
  let frameIdx = 0;

  client.on('Page.screencastFrame', async (event) => {
    const idx  = frameIdx++;
    const fname = path.join(TMPDIR, `f${String(idx).padStart(7, '0')}.jpg`);
    fs.writeFileSync(fname, Buffer.from(event.data, 'base64'));
    frames.push({ fname, ts: event.metadata.timestamp });
    try {
      await client.send('Page.screencastFrameAck', { sessionId: event.sessionId });
    } catch (_) {}
  });

  await client.send('Page.startScreencast', {
    format: 'jpeg',
    quality: 92,
    maxWidth: WIDTH,
    maxHeight: HEIGHT,
    everyNthFrame: 1,
  });

  console.log(`Recording ${RECORD_MS / 1000} s…`);
  await new Promise(r => setTimeout(r, RECORD_MS));

  await client.send('Page.stopScreencast');
  await browser.close();

  console.log(`Captured ${frames.length} frames`);

  // Build ffmpeg concat file with accurate per-frame durations from CDP timestamps
  const lines = [];
  for (let i = 0; i < frames.length; i++) {
    const dur = i < frames.length - 1
      ? (frames[i + 1].ts - frames[i].ts).toFixed(6)
      : '0.033333';
    lines.push(`file '${frames[i].fname.replace(/\\/g, '/')}'`);
    lines.push(`duration ${dur}`);
  }
  // ffmpeg concat demuxer requires the last file listed twice
  if (frames.length > 0) {
    lines.push(`file '${frames[frames.length - 1].fname.replace(/\\/g, '/')}'`);
  }

  const concatFile = path.join(TMPDIR, 'frames.txt');
  fs.writeFileSync(concatFile, lines.join('\n'));

  console.log('Encoding MP4…');
  const args = [
    '-f', 'concat', '-safe', '0',
    '-i', concatFile,
    '-vf', `scale=${WIDTH}:${HEIGHT}:force_original_aspect_ratio=disable`,
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
    '-pix_fmt', 'yuv420p',
    '-movflags', '+faststart',
    '-y', OUTPUT,
  ];

  const result = spawnSync(ffmpegPath, args, { stdio: 'inherit', windowsVerbatimArguments: false });
  if (result.status !== 0) {
    throw new Error(`FFmpeg exited with code ${result.status}. Error: ${result.error || ''}`);
  }

  // Clean up temp frames
  fs.rmSync(TMPDIR, { recursive: true });

  console.log(`\nDone → ${OUTPUT}`);
}

main().catch(err => { console.error(err); process.exit(1); });
