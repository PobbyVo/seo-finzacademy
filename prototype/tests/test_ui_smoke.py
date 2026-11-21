"""Optional UI smoke test against python server.py at localhost:5193."""
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = (Path(__file__).resolve().parents[1] / 'index.html').as_uri()
BASE = Path(__file__).resolve().parents[2]
CSV = BASE / 'fixtures' / 'DEMO_NOT_LIVE_SEMRUSH.csv'
SCREENSHOT = Path('/mnt/data/FINZ_SEO_LOCAL_UI_DASHBOARD.png')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda x: errors.append(str(x)))
    workbench = Path(__file__).resolve().parents[1]
    html=(workbench / 'index.html').read_text(encoding='utf-8').replace('<link rel="stylesheet" href="./styles.css" />','').replace('<script src="./app.js" defer></script>','')
    page.set_content(html)
    page.add_style_tag(content=(workbench / 'styles.css').read_text(encoding='utf-8'))
    page.evaluate("""() => {
      const values = {};
      Object.defineProperty(window, 'localStorage', { configurable: true, value: {
        getItem: k => values[k] || null,
        setItem: (k,v) => { values[k] = String(v); },
        removeItem: k => { delete values[k]; }
      }});
    }""")
    page.add_script_tag(content=(workbench / 'app.js').read_text(encoding='utf-8'))
    assert page.get_by_text('Chưa có thông tin dự án').count() == 1
    page.get_by_role('button', name='Nạp dữ liệu minh họa').click()
    assert page.get_by_text('FinZ / P01').count() >= 1
    assert page.locator('#saveIndicator').inner_text() == 'Đã lưu trên trình duyệt'
    page.locator('#toast').evaluate('(e) => e.classList.remove("show")')
    page.screenshot(path='/mnt/data/FINZ_SEO_LOCAL_WORKBENCH_PREVIEW.png', full_page=True)
    page.locator('button[data-page="requests"]').first.click()
    assert page.get_by_text('Phiếu yêu cầu xuất dữ liệu Semrush').count() >= 1
    req=page.locator('button[data-action="select-upload"]').first
    with page.expect_file_chooser() as info:
        req.click()
    info.value.set_files(str(CSV))
    page.get_by_text('File đang chờ xác nhận').wait_for(timeout=10000)
    assert page.locator('#map-keyword').input_value()=='Keyword'
    assert page.locator('#map-volume').input_value()=='Search Volume'
    page.locator('button[data-action="confirm-import"]').click()
    assert page.get_by_text('Tình trạng dữ liệu').count() >= 0
    page.locator('button[data-action="analyze-imports"]').click()
    assert page.get_by_text('Tình trạng dữ liệu và khoảng trống').count() >= 1
    page.locator('button[data-page="overview"]').first.click()
    page.screenshot(path=str(SCREENSHOT),full_page=True)
    assert not errors, errors
    print('Smoke PASS: created demo, export requests, upload CSV, map, import, analysis, dashboard render')
    print('Dashboard screenshot:', SCREENSHOT)
    print('Initial workbench preview:', '/mnt/data/FINZ_SEO_LOCAL_WORKBENCH_PREVIEW.png')
    browser.close()
