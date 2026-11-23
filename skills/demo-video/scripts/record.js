// Records one scene at 1440x900 with no subtitles: a slide (HTML file) or an app screen.
//
//   node record.js --scenes scenes.json --clips <clips-dir> --id <scene id> [options]
//     --slides <dir>     folder with <id>.html for slide scenes (default: <scenes.json folder>/slides)
//     --base <url>       base URL for app scenes whose "url" starts with "/"
//     --storage <file>   Playwright storage state (a saved login) for app scenes
//     --theme <dir>      folder whose files are copied next to the slides (default: ../theme in this skill)
//
// Needs <clips-dir>/<id>.cues.json from `scene.py narrate`. Writes <clips-dir>/<id>.webm and <clips-dir>/<id>.offset
// (seconds to cut from the start of the recording; pass it to `scene.py mux`).
//
// Scene kinds in scenes.json: "slide" (anything but "app"), or
//   {"id","kind":"app","url":"/path","ready":{"text":"..."},"sents":[{"text":"...","act":[STEP,...]}, "plain sentence"]}
// STEP: {"target": LOC or [LOC,...], "z":1.5, "pad":10, "click":true, "fill":"text", "press":"Enter", "goto":true, "waitUrl":"regex"}
//   press: a key on the target after fill (more reliable than clicking a send button); goto: open the target's href in
//   this page (for links with target=_blank). Targets are scrolled into view before they are pointed at.
// LOC: {"role":"button","name":"Save","exact":true} | {"text":"..."} | {"placeholder":"..."} | {"testid":"..."} | {"selector":"css"}, optional "nth".
const fs = require('fs'), path = require('path'), os = require('os');
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const scenesFile = arg('scenes'), clips = arg('clips'), id = arg('id');
if (!scenesFile || !clips || !id) { console.error('usage: node record.js --scenes <scenes.json> --clips <dir> --id <id> [--slides dir] [--base url] [--storage file] [--theme dir]'); process.exit(2); }
const slidesDir = arg('slides', path.join(path.dirname(path.resolve(scenesFile)), 'slides'));
const theme = arg('theme', path.join(__dirname, '..', 'theme'));
const home = process.env.DEMO_VIDEO_HOME || path.join(os.homedir(), '.local/share/demo-video-tts');
const base = arg('base', ''), storage = arg('storage');

const { chromium } = require(require.resolve('playwright-core', { paths: [path.join(home, 'node'), process.cwd()] }));
const s = JSON.parse(fs.readFileSync(scenesFile)).find(x => x.id === id);
if (!s) { console.error('no scene ' + id); process.exit(2); }
const app = s.kind === 'app';
const cues = JSON.parse(fs.readFileSync(path.join(clips, id + '.cues.json')));
const LEAD_IN = 0.3;

// Page-side helpers: spotlight, animated cursor, click ripple, zoom
const init=()=>{
 window.DV={};
 const mk=()=>{
  if(document.getElementById('dv-spot'))return;
  const st=document.createElement('style');
  st.textContent=`html{overflow:hidden!important}body{transform-origin:0 0;width:1440px!important;height:900px!important;overflow:hidden!important;position:relative}nextjs-portal{display:none!important}
  #dv-spot{position:fixed;z-index:99990;pointer-events:none;border-radius:10px;box-shadow:0 0 0 4000px rgba(0,0,0,.5);outline:4px solid #2f6fed;opacity:0;transition:all .45s ease;animation:dvp 1.2s ease-in-out infinite}
  @keyframes dvp{50%{outline-color:#fff;outline-offset:5px}}
  #dv-cur{position:fixed;z-index:99995;pointer-events:none;width:30px;height:30px;transition:left .9s cubic-bezier(.4,0,.2,1),top .9s cubic-bezier(.4,0,.2,1)}
  #dv-rip{position:fixed;z-index:99994;pointer-events:none;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;border:4px solid #2f6fed;opacity:0}
  @keyframes dvr{from{opacity:1;transform:scale(.3)}to{opacity:0;transform:scale(1.6)}}`;
  document.documentElement.appendChild(st);
  const sp=document.createElement('div');sp.id='dv-spot';document.documentElement.appendChild(sp);
  const c=document.createElement('div');c.id='dv-cur';c.innerHTML='<svg viewBox="0 0 24 24" width="30" height="30"><path d="M3 2l16 9-7 2-3 7z" fill="#111" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>';
  const pos=JSON.parse(sessionStorage.getItem('dvcur')||'[1000,700]');c.style.left=pos[0]+'px';c.style.top=pos[1]+'px';document.documentElement.appendChild(c);
  const r=document.createElement('div');r.id='dv-rip';document.documentElement.appendChild(r);
 };
 document.addEventListener('DOMContentLoaded',mk);
 DV.zoomed=false;
 DV.spot=(x,y,w,h)=>{const e=document.getElementById('dv-spot');Object.assign(e.style,{left:x+'px',top:y+'px',width:w+'px',height:h+'px',opacity:1})};
 DV.clear=()=>{const e=document.getElementById('dv-spot');if(e)e.style.opacity=0};
 DV.cur=(x,y)=>{const c=document.getElementById('dv-cur');c.style.left=x+'px';c.style.top=y+'px';sessionStorage.setItem('dvcur',JSON.stringify([x,y]))};
 DV.ripple=(x,y)=>{const r=document.getElementById('dv-rip');r.style.left=x+'px';r.style.top=y+'px';r.style.animation='none';void r.offsetWidth;r.style.animation='dvr .6s ease-out'};
 // zoom z times around the centre of box b (null = back to the full view)
 DV.zoom=(b,z)=>{const bd=document.body;bd.style.transition='transform .6s cubic-bezier(.4,0,.2,1)';
  if(!b){bd.style.transform='none';DV.zoomed=false;return}
  let tx=720-z*(b.x+b.width/2),ty=450-z*(b.y+b.height/2);tx=Math.min(0,Math.max(1440-1440*z,tx));ty=Math.min(0,Math.max(900-900*z,ty));
  bd.style.transform=`translate(${tx}px,${ty}px) scale(${z})`;DV.zoomed=true};
};
const sleepUntil = (p, t0, ms) => { const w = ms - (Date.now() - t0); return w > 0 ? p.waitForTimeout(w) : 0; };
const locator = (p, l) => {
  const loc = l.role ? p.getByRole(l.role, l.name ? { name: l.name, exact: !!l.exact } : {}) : l.text ? p.getByText(l.text, { exact: !!l.exact })
    : l.placeholder ? p.getByPlaceholder(l.placeholder) : l.testid ? p.getByTestId(l.testid) : p.locator(l.selector);
  return l.nth !== undefined ? loc.nth(l.nth) : loc.first();
};
const union = bs => { const x = Math.min(...bs.map(b => b.x)), y = Math.min(...bs.map(b => b.y)); return { x, y, width: Math.max(...bs.map(b => b.x + b.width)) - x, height: Math.max(...bs.map(b => b.y + b.height)) - y }; };
const boxOf = (p, t) => async () => union(await Promise.all([].concat(t).map(async l => { await locator(p, l).scrollIntoViewIfNeeded(); const b = await locator(p, l).boundingBox(); if (!b) throw new Error('no box'); return b; })));

(async () => {
  const br = await chromium.launch();
  const ctx = await br.newContext({ viewport: { width: 1440, height: 900 }, ...(storage ? { storageState: storage } : {}), recordVideo: { dir: path.join(clips, 'vid-' + id), size: { width: 1440, height: 900 } } });
  if (app) await ctx.addInitScript(init);
  const p = await ctx.newPage(); const t00 = Date.now();
  if (app) {
    await p.goto(s.url.startsWith('http') ? s.url : base + s.url);
    if (s.ready) await locator(p, s.ready).waitFor();
    await p.waitForTimeout(800);
  } else {
    const stage = fs.mkdtempSync(path.join(os.tmpdir(), 'demo-slides-'));
    for (const f of fs.readdirSync(slidesDir)) fs.copyFileSync(path.join(slidesDir, f), path.join(stage, f));
    for (const f of fs.readdirSync(theme)) fs.copyFileSync(path.join(theme, f), path.join(stage, f));
    await p.goto('file://' + path.join(stage, id + '.html'));
    await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(300);
  }
  const off = (Date.now() - t00) / 1000;
  if (!app) await p.evaluate(() => document.getElementById('root').classList.add('go'));
  const t0 = Date.now();
  // point at an element: cursor and spotlight, zoom only when z > 1; click when asked
  const point = async (getBox, o = {}) => {
    const { z = 1, pad = 10, click = false } = o;
    await p.evaluate(() => { DV.clear(); DV.zoom(null); });
    let b = await getBox();
    const pt = bb => click ? [bb.x + bb.width / 2, bb.y + bb.height / 2] : [bb.x + Math.max(bb.width * 0.8, bb.width - 30), bb.y + Math.max(bb.height * 0.7, bb.height - 8)];
    if (z > 1) { await p.evaluate(([b, z]) => DV.zoom(b, z), [b, z]); await p.waitForTimeout(650); b = await getBox(); }
    await p.evaluate(([c, b, pad]) => { DV.cur(c[0], c[1]); DV.spot(b.x - pad, b.y - pad, b.width + 2 * pad, b.height + 2 * pad); }, [pt(b), b, pad]);
    await p.waitForTimeout(z > 1 ? 500 : 800);
    if (click) { await p.evaluate(() => DV.clear()); await p.evaluate(([x, y]) => DV.ripple(x, y), [b.x + b.width / 2, b.y + b.height / 2]); await p.mouse.click(b.x + b.width / 2, b.y + b.height / 2); }
  };
  if (app) for (let k = 0; k < s.sents.length; k++) {
    await sleepUntil(p, t0, (cues.cues[k].start - LEAD_IN) * 1000);
    for (const st of (s.sents[k].act || [])) {
      try {
        await point(boxOf(p, st.target), st);
        const loc = locator(p, [].concat(st.target)[0]);
        if (st.fill !== undefined) await loc.fill(st.fill);
        if (st.press) await loc.press(st.press);
        if (st.goto) await p.goto(new URL(await loc.getAttribute('href'), p.url()).href);
        if (st.waitUrl) await p.waitForURL(new RegExp(st.waitUrl));
      } catch (e) { console.log('ACT FAIL', id, k, e.message.split('\n')[0]); }
    }
    await sleepUntil(p, t0, (cues.cues[k].end + 0.05) * 1000);
    try { await p.evaluate(() => { DV.clear(); DV.zoom(null); }); } catch (e) { }
  }
  await sleepUntil(p, t0, cues.duration * 1000 + 300);
  const v = p.video(); await ctx.close();
  fs.renameSync(await v.path(), path.join(clips, id + '.webm')); fs.rmSync(path.join(clips, 'vid-' + id), { recursive: true, force: true });
  fs.writeFileSync(path.join(clips, id + '.offset'), off.toFixed(3));
  await br.close(); console.log(id, 'recorded, offset', off.toFixed(3));
})();
