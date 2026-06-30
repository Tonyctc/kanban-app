"""Debug dropdown: inspect Alpine internals."""
from playwright.sync_api import sync_playwright

BASE = "http://localhost:5000"

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    
    page.goto(f"{BASE}/login")
    page.fill('input[name="email"]', 'admin@sistema.com')
    page.fill('input[name="senha"]', 'admin123')
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    
    page.goto(f"{BASE}/dashboard")
    page.wait_for_load_state("networkidle")
    
    # Check Alpine and element
    info = page.evaluate("""() => {
        const el = document.querySelector('[x-data*="langOpen"]');
        if (!el) return JSON.stringify({error: 'no element found'});
        return JSON.stringify({
            tag: el.tagName,
            hasXData: el.hasAttribute('x-data'),
            xDataValue: el.getAttribute('x-data'),
            hasAlpine: !!el.__x,
            dataKeys: el.__x ? Object.keys(el.__x.$data) : [],
            langOpen: el.__x ? el.__x.$data.langOpen : undefined,
        });
    }""")
    print("Element info:", info)
    
    # Click globe
    btn = page.locator('button[title*="Idioma"], button[title*="Language"]').first
    btn.click()
    page.wait_for_timeout(500)
    
    state = page.evaluate("""() => {
        const el = document.querySelector('[x-data*="langOpen"]');
        if (!el || !el.__x) return JSON.stringify({error: 'no data'});
        return JSON.stringify({
            langOpen: el.__x.$data.langOpen,
            display: document.querySelector('[x-show="langOpen"]')?.style?.display
        });
    }""")
    print("After click:", state)
    
    # Try calling Alpine method directly
    page.evaluate("""() => {
        const el = document.querySelector('[x-data*="langOpen"]');
        if (el && el.__x) {
            el.__x.$data.langOpen = false;
        }
    }""")
    page.wait_for_timeout(300)
    
    state2 = page.evaluate("""() => {
        const el = document.querySelector('[x-data*="langOpen"]');
        if (!el || !el.__x) return JSON.stringify({error: 'no data'});
        return JSON.stringify({langOpen: el.__x.$data.langOpen});
    }""")
    print("After JS set false:", state2)
    
    browser.close()
