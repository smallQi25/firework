"""Chinese mobile controls; system fonts avoid bundling font files.

A bounded JSON queue connects native browser buttons to the Python renderer.
"""

BROWSER_UI = r"""
(() => {
  'use strict';
  if (window.fireworkMobile) return;
  const canvas = document.getElementById('canvas');
  if (!canvas) throw new Error('Firework canvas is missing');
  document.documentElement.lang = 'zh-CN';
  document.title = '\u638c\u4e0a\u70df\u82b1 \u00b7 \u89e6\u6478\u7efd\u653e';
  document.querySelectorAll('meta[name="viewport"]').forEach(meta => meta.remove());
  const viewport = document.createElement('meta');
  viewport.name = 'viewport';
  viewport.content = 'width=device-width, initial-scale=1, viewport-fit=cover';
  document.head.appendChild(viewport);

  const style = document.createElement('style');
  style.textContent = `
    html, body { margin:0 !important; padding:0 !important; overflow:hidden !important;
      width:100%; height:100%; background:#050817 !important; }
    #transfer, #infobox, #crt, #pyconsole, #canvas3d { display:none !important; }
    #fw-app, #fw-app * { box-sizing:border-box; }
    #fw-app { position:fixed; top:0; left:0; z-index:10000; transform-origin:0 0;
      display:grid; grid-template-rows:minmax(0,1fr) auto; overflow:hidden;
      background:#050817; color:#eff4ff; font-family:system-ui,-apple-system,
      'PingFang SC','Microsoft YaHei',sans-serif; -webkit-tap-highlight-color:transparent; }
    #fw-stage { position:relative; min-height:0; overflow:hidden; }
    #fw-app #canvas { position:absolute !important; inset:0 !important; width:100% !important;
      height:100% !important; max-width:none !important; max-height:none !important;
      margin:0 !important; padding:0 !important; border:0 !important; transform:none !important;
      visibility:visible !important; pointer-events:none !important; z-index:1 !important; }
    #fw-sky { position:absolute; inset:0; z-index:2; touch-action:none; outline:none; }
    #fw-sky:focus-visible { outline:2px solid #b4c9ff; outline-offset:-4px; }
    #fw-heading { position:absolute; left:max(16px,env(safe-area-inset-left));
      top:max(14px,env(safe-area-inset-top)); z-index:3; pointer-events:none;
      text-shadow:0 2px 10px #020410; }
    #fw-heading strong { display:block; font-size:18px; font-weight:650; letter-spacing:2px; }
    #fw-heading span { display:block; margin-top:5px; font-size:12px; color:#b7c3dd; }
    #fw-controls { padding:10px max(12px,env(safe-area-inset-right))
      max(10px,env(safe-area-inset-bottom)) max(12px,env(safe-area-inset-left));
      background:linear-gradient(180deg,#10172b,#080d1c); border-top:1px solid #28324a; }
    #fw-buttons { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px;
      width:100%; max-width:1080px; margin:auto; }
    #fw-app button { min-height:48px; min-width:0; margin:0; padding:10px 6px;
      border:1px solid #3d4965; border-radius:12px; color:#edf2ff; background:#192238;
      font:600 14px/1.25 system-ui,-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;
      white-space:nowrap; cursor:pointer; touch-action:manipulation; }
    #fw-app button[aria-pressed="true"] { background:#334871; border-color:#b0cbff; }
    #fw-app button:active { background:#40547d; }
    #fw-app button:focus-visible { outline:3px solid #d0e1ff; outline-offset:2px; }
    #fw-app button:disabled { opacity:.5; cursor:default; }
    #fw-note { margin:8px auto 0; max-width:1080px; font-size:12px;
      color:#afbdd7; line-height:1.45; min-height:18px; }
    #fw-app.fw-wide #fw-buttons { grid-template-columns:repeat(6,minmax(0,1fr)); gap:7px; }
    #fw-app.fw-wide #fw-controls { padding-top:8px; }
    #fw-app.fw-wide #fw-heading strong { font-size:16px; }
  `;
  document.head.appendChild(style);

  const app = document.createElement('main');
  app.id = 'fw-app';
  app.innerHTML = `
    <section id="fw-stage" aria-label="\u70df\u82b1\u5929\u7a7a">
      <div id="fw-sky" role="button" tabindex="0" aria-label="\u70b9\u51fb\u5929\u7a7a\uff0c\u5728\u6b64\u4f4d\u7f6e\u53d1\u5c04\u70df\u82b1"></div>
      <header id="fw-heading"><strong>\u638c\u4e0a\u70df\u82b1</strong><span id="fw-current">\u70b9\u51fb\u6309\u94ae\uff0c\u5373\u523b\u7efd\u653e</span></header>
    </section>
    <section id="fw-controls" aria-label="\u70df\u82b1\u64cd\u4f5c\u533a">
      <div id="fw-buttons">
        <button type="button" data-pattern="heart" aria-pressed="false" disabled>\u7231\u5fc3\u70df\u82b1</button>
        <button type="button" data-pattern="ring" aria-pressed="false" disabled>\u5706\u73af\u70df\u82b1</button>
        <button type="button" data-pattern="willow" aria-pressed="false" disabled>\u5782\u67f3\u70df\u82b1</button>
        <button type="button" id="fw-auto" aria-pressed="true" disabled>\u81ea\u52a8\uff1a\u5f00\u542f</button>
        <button type="button" id="fw-finale" disabled>\u70df\u82b1\u9f50\u653e</button>
        <button type="button" id="fw-landscape" aria-pressed="false">\u6a2a\u5c4f\u663e\u793a</button>
      </div>
      <p id="fw-note" role="status" aria-live="polite">\u6b63\u5728\u8fde\u63a5\u70df\u82b1\u5f15\u64ce\u2026</p>
    </section>
  `;
  document.body.appendChild(app);
  const stage = document.getElementById('fw-stage');
  stage.prepend(canvas);
  const sky = document.getElementById('fw-sky');
  const note = document.getElementById('fw-note');
  const current = document.getElementById('fw-current');
  const autoButton = document.getElementById('fw-auto');
  const landscapeButton = document.getElementById('fw-landscape');
  const names = {heart:'\u7231\u5fc3\u70df\u82b1', ring:'\u5706\u73af\u70df\u82b1', willow:'\u5782\u67f3\u70df\u82b1'};
  const queue = [];
  let ready = false;
  let desiredLandscape = false;
  let softwareRotated = false;
  let fullscreenBusy = false;
  let hadFullscreen = false;
  let renderWidth = 960;
  let renderHeight = 540;
  let lastState = '';
  const clamp = (n, low, high) => Math.max(low, Math.min(high, n));

  function layout() {
    const vv = window.visualViewport;
    const width = Math.max(1, Math.round(vv ? vv.width : window.innerWidth));
    const height = Math.max(1, Math.round(vv ? vv.height : window.innerHeight));
    softwareRotated = desiredLandscape && height > width;
    const localWidth = softwareRotated ? height : width;
    const localHeight = softwareRotated ? width : height;
    app.style.width = localWidth + 'px';
    app.style.height = localHeight + 'px';
    app.style.left = (vv ? vv.offsetLeft : 0) + 'px';
    app.style.top = (vv ? vv.offsetTop : 0) + 'px';
    app.style.transform = softwareRotated ? 'translateX(' + width + 'px) rotate(90deg)' : 'none';
    app.classList.toggle('fw-wide', localWidth >= 650 && localWidth > localHeight);
    const sw = Math.max(1, stage.clientWidth);
    const sh = Math.max(1, stage.clientHeight);
    const scale = Math.min(960 / sw, 800 / sh, Math.max(1, 540 / sw));
    renderWidth = Math.max(160, Math.round(sw * scale));
    renderHeight = Math.max(160, Math.round(sh * scale));
    landscapeButton.textContent = desiredLandscape ? '\u9000\u51fa\u6a2a\u5c4f' : '\u6a2a\u5c4f\u663e\u793a';
    landscapeButton.setAttribute('aria-pressed', String(desiredLandscape));
  }

  function enqueue(command) {
    if (ready && queue.length < 24) queue.push(command);
  }

  window.fireworkMobile = Object.freeze({
    poll() {
      return JSON.stringify({width:renderWidth, height:renderHeight, actions:queue.splice(0,24)});
    },
    setState(serialized) {
      const state = JSON.parse(serialized);
      ready = true;
      app.querySelectorAll('button:disabled').forEach(button => { button.disabled = false; });
      if (serialized === lastState) return;
      lastState = serialized;
      autoButton.textContent = state.autoplay ? '\u81ea\u52a8\uff1a\u5f00\u542f' : '\u81ea\u52a8\uff1a\u5173\u95ed';
      autoButton.setAttribute('aria-pressed', String(Boolean(state.autoplay)));
      autoButton.setAttribute('aria-label', state.autoplay ? '\u81ea\u52a8\u64ad\u653e\u5df2\u5f00\u542f\uff0c\u70b9\u51fb\u5173\u95ed' : '\u81ea\u52a8\u64ad\u653e\u5df2\u5173\u95ed\uff0c\u70b9\u51fb\u5f00\u542f');
      app.querySelectorAll('[data-pattern]').forEach(button => {
        button.setAttribute('aria-pressed', String(button.dataset.pattern === state.pattern));
      });
      current.textContent = state.pattern ? '\u5f53\u524d\uff1a' + names[state.pattern] : '\u5f53\u524d\uff1a\u968f\u673a\u70df\u82b1';
      note.textContent = '\u70b9\u6309\u94ae\u7acb\u5373\u53d1\u5c04\uff1b\u70b9\u5929\u7a7a\u6307\u5b9a\u4f4d\u7f6e\u3002\u81ea\u52a8\u64ad\u653e\u4f7f\u7528\u5f53\u524d\u6837\u5f0f\u3002';
      app.dataset.ready = 'true';
    }
  });

  app.querySelectorAll('[data-pattern]').forEach(button => {
    button.addEventListener('click', () => enqueue({action:'pattern', pattern:button.dataset.pattern}));
  });
  autoButton.addEventListener('click', () => enqueue({action:'toggle-auto'}));
  document.getElementById('fw-finale').addEventListener('click', () => enqueue({action:'finale'}));

  sky.addEventListener('pointerdown', event => {
    if (event.pointerType === 'mouse' && event.button !== 0) return;
    event.preventDefault();
    event.stopPropagation();
    const rect = sky.getBoundingClientRect();
    const u = (event.clientX - rect.left) / rect.width;
    const v = (event.clientY - rect.top) / rect.height;
    // Invert the CSS rotation; SDL's normal coordinates would be incorrect.
    const x = softwareRotated ? v : u;
    const y = softwareRotated ? 1 - u : v;
    enqueue({action:'launch', x:clamp(x,0,1), y:clamp(y,0,1)});
  });
  sky.addEventListener('keydown', event => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      event.stopPropagation();
      enqueue({action:'launch', x:0.5, y:0.35});
    }
  });

  async function exitLandscape() {
    desiredLandscape = false;
    layout();
    try { if (screen.orientation && screen.orientation.unlock) screen.orientation.unlock(); } catch (_) {}
    try {
      if (document.fullscreenElement && document.exitFullscreen) await document.exitFullscreen();
      else if (document.webkitFullscreenElement && document.webkitExitFullscreen) document.webkitExitFullscreen();
    } catch (_) {}
  }

  landscapeButton.addEventListener('click', async () => {
    if (fullscreenBusy) return;
    if (desiredLandscape) { await exitLandscape(); return; }
    desiredLandscape = true;
    layout();
    note.textContent = '\u5df2\u5207\u6362\u6a2a\u5c4f\u663e\u793a\uff0c\u8bf7\u628a\u624b\u673a\u6a2a\u7740\u62ff\uff1b\u70b9\u51fb\u201c\u9000\u51fa\u6a2a\u5c4f\u201d\u53ef\u6062\u590d\u3002';
    fullscreenBusy = true;
    try {
      const root = document.documentElement;
      if (!document.fullscreenElement && root.requestFullscreen) await root.requestFullscreen();
      if (screen.orientation && screen.orientation.lock) await screen.orientation.lock('landscape');
    } catch (_) {
      // A denied native request leaves the CSS rotation and touch mapping active.
    } finally {
      fullscreenBusy = false;
      hadFullscreen = Boolean(document.fullscreenElement || document.webkitFullscreenElement);
      layout();
    }
  });
  document.addEventListener('fullscreenchange', () => {
    const active = Boolean(document.fullscreenElement || document.webkitFullscreenElement);
    if (hadFullscreen && !active) {
      desiredLandscape = false;
      try { if (screen.orientation && screen.orientation.unlock) screen.orientation.unlock(); } catch (_) {}
    }
    hadFullscreen = active;
    layout();
  });
  window.addEventListener('resize', layout);
  if (window.visualViewport) window.visualViewport.addEventListener('resize', layout);
  if (screen.orientation && screen.orientation.addEventListener) screen.orientation.addEventListener('change', layout);
  if (window.ResizeObserver) new ResizeObserver(layout).observe(document.getElementById('fw-controls'));
  layout();
})();
"""
