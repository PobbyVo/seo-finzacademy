"""Optional Playwright interaction smoke test: generic taxonomy + manual request."""
from pathlib import Path
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1250,'height':960})
    errors=[]
    page.on('pageerror',lambda x:errors.append(str(x)))
    html=(root/'index.html').read_text(encoding='utf-8').replace('<link rel="stylesheet" href="./styles.css" />','').replace('<script src="./app.js" defer></script>','')
    page.set_content(html)
    page.evaluate('''() => {const d={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>d[k]||null,setItem:(k,v)=>{d[k]=v}}});}''')
    page.add_style_tag(content=(root/'styles.css').read_text(encoding='utf-8'))
    page.add_script_tag(content=(root/'app.js').read_text(encoding='utf-8'))
    page.locator('button[data-page="setup"]').first.click()
    fields={'name':'SEO ngành máy pha cà phê','businessGoal':'Tăng nhu cầu tư vấn máy pha cà phê','audience':'Người mua máy pha cà phê','market':'VN','pillar':'THIẾT BỊ','topicCode':'P99','topicName':'Máy pha cà phê','topicType':'Theo sản phẩm','axis':'Theo loại máy','mainTopics':'Máy gia đình; Máy văn phòng; Vệ sinh máy','contentCode':'P99.1','contentTitle':'Máy pha cà phê cho người mới','primary':'máy pha cà phê cho người mới','secondaries':'máy pha cà phê văn phòng\nchọn máy pha cà phê'}
    for name,value in fields.items():
        page.locator(f'#projectForm [name="{name}"]').fill(value)
    page.locator('#projectForm button[type="submit"]').click()
    assert page.locator('#sideProjectDetail').inner_text()=='P99 · Máy pha cà phê'
    assert page.locator('.timeline-block').count()==0
    group=page.locator('#groupForm')
    group.locator('[name="title"]').fill('Máy dùng tại nhà')
    group.locator('[name="need"]').fill('Tìm máy pha phù hợp bếp nhỏ')
    group.locator('[name="seed"]').fill('máy pha cà phê tại nhà')
    group.locator('[name="evidence"]').fill('P99: Chủ đề máy gia đình')
    group.locator('button[type="submit"]').click()
    assert page.get_by_text('Máy dùng tại nhà').count()>=1
    page.locator('button[data-page="requests"]').first.click()
    req=page.locator('#requestForm')
    assert req.locator('[name="seed"]').input_value()=='máy pha cà phê cho người mới'
    req.locator('button[type="submit"]').click()
    assert page.locator('.research-item').count()==1
    assert not errors, errors
    print('Generic project PASS: custom P99, dynamic demand group, dynamic Semrush request, no P01 hardcode')
    browser.close()
