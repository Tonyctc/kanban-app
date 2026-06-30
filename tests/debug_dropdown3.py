"""Debug Alpine v3 on body component."""
from playwright.sync_api import sync_playwright

BASE = "http://localhost:5000"

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 720})
    page = context.new_page()
    
    page.goto(f"{BASE}/login")
    page.fill('input[name="email"]', 'admin@sistema.com')
    page.fill('input[name="senha"]', 'admin123')
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    
    page.goto(f"{BASE}/dashboard")
    page.wait_for_load_state("networkidle")
    
    # Alpine version check
    alpine_info = page.evaluate("""() => {
        return JSON.stringify({
            alpineExists: typeof Alpine !== 'undefined',
            version: typeof Alpine !== 'undefined' ? Alpine.version || 'unknown' : 'N/A',
            bodyHasXData: document.body.hasAttribute('x-data'),
            bodyXData: document.body.getAttribute('x-data'),
            bodyHasAlpine: !!document.body.__x
        });
    }""")
    print("Alpine info:", alpine_info)
    
    if alpine_info:
        # Check body Alpine data
        body_data = page.evaluate("""() => {
            const body = document.body;
            if (!body.__x) return JSON.stringify({error: 'Alpine not initialized on body'});
            const data = body.__x.$data;
            return JSON.stringify({
                isDark: data.isDark,
                langOpen: data.langOpen,
                userOpen: data.userOpen
            });
        }""")
        print("Body data:", body_data)
    
    # Check if the globe button exists and click it
    btn = page.locator('button[title*="Idioma"], button[title*="Language"]').first
    print(f"Globe exists: {btn.count()}")
    if btn.count():
        btn.click()
        page.wait_for_timeout(500)
        
        after = page.evaluate("""() => {
            const body = document.body;
            if (!body.__x) return JSON.stringify({error: 'no data'});
            const data = body.__x.$data;
            return JSON.stringify({
                langOpen: data.langOpen,
                userOpen: data.userOpen
            });
        }""")
        print("After globe click:", after)
        
        # Check dropdown visibility
        dropdown = page.locator('[x-show="langOpen"]')
        print(f"Dropdown visible count: {dropdown.count()}")
        if dropdown.count():
            print(f"Dropdown display: {dropdown.first.evaluate('el => el.style.display')}")
        
        # Click on main content
        page.locator('main').first.click(position={"x": 50, "y": 50})
        page.wait_for_timeout(500)
        
        after2 = page.evaluate("""() => {
            const body = document.body;
            if (!body.__x) return JSON.stringify({error: 'no data'});
            const data = body.__x.$data;
            return JSON.stringify({langOpen: data.langOpen, userOpen: data.userOpen});
        }""")
        print("After clicking main:", after2)
    
    browser.close()
