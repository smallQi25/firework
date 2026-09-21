"""Test the packaged Python/WebAssembly site with mobile touch emulation."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import threading

from playwright.sync_api import sync_playwright

root = Path("build/web").resolve()
if not (root / "index.html").is_file():
    raise SystemExit("Missing packaged index.html")
handler = partial(SimpleHTTPRequestHandler, directory=str(root))
server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
threading.Thread(target=server.serve_forever, daemon=True).start()

try:
    with sync_playwright() as p:
        executable = shutil.which("google-chrome") or shutil.which("chromium")
        browser = p.chromium.launch(executable_path=executable, headless=True,
                                   args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page(viewport={"width":393,"height":851}, is_mobile=True,
                                has_touch=True, device_scale_factor=1)
        page.on("console", lambda message: print("BROWSER:", message.type, message.text, flush=True))
        page.on("pageerror", lambda error: print("PAGE ERROR:", error, flush=True))
        page.add_init_script("""
          Element.prototype.requestFullscreen = () => Promise.reject(new Error('test unsupported'));
        """)
        page.goto(f"http://127.0.0.1:{server.server_port}/", wait_until="domcontentloaded")
        page.wait_for_selector('#fw-app[data-ready="true"]', timeout=180_000)
        assert page.locator("#fw-auto").inner_text() == "自动：开启"
        for pattern, label in [("heart","爱心烟花"),("ring","圆环烟花"),("willow","垂柳烟花")]:
            page.locator(f'[data-pattern="{pattern}"]').tap()
            page.wait_for_function("label => document.getElementById('fw-current').textContent === '当前：' + label", arg=label)
        page.locator("#fw-auto").tap()
        page.wait_for_function("document.getElementById('fw-auto').textContent === '自动：关闭'")
        for width,height in [(393,851),(320,568),(360,640),(851,393)]:
            page.set_viewport_size({"width":width,"height":height})
            page.wait_for_timeout(100)
            for button in page.locator('#fw-buttons button').all():
                box = button.bounding_box()
                assert box['width'] >= 44 and box['height'] >= 44, box
                assert box['x'] >= -1 and box['y'] >= -1, box
                assert box['x']+box['width'] <= width+1 and box['y']+box['height'] <= height+1, box
        page.set_viewport_size({"width":393,"height":851})
        page.wait_for_timeout(100)
        page.locator('#fw-landscape').tap()
        page.wait_for_function("document.getElementById('fw-landscape').textContent === '退出横屏'")
        assert page.locator('#fw-app').evaluate('(e)=>getComputedStyle(e).transform') != 'none'
        page.locator('[data-pattern="heart"]').tap()
        page.wait_for_function("document.getElementById('fw-current').textContent === '当前：爱心烟花'")
        sky = page.locator('#fw-sky').bounding_box()
        page.touchscreen.tap(sky['x']+sky['width']*.6, sky['y']+sky['height']*.25)
        page.wait_for_timeout(1500)
        page.locator('#fw-landscape').tap()
        page.wait_for_function("document.getElementById('fw-landscape').textContent === '横屏显示'")
        assert page.locator('#fw-app').evaluate('(e)=>getComputedStyle(e).transform') == 'none'
        page.locator('#fw-finale').tap()
        print('PASS: WASM startup, Chinese controls, three patterns, auto toggle, mobile layouts, landscape fallback and exit', flush=True)
        browser.close()
finally:
    server.shutdown()
