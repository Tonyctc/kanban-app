"""Debug Alpine - try all access methods."""
from playwright.sync_api import sync_playwright

BASE = "http://localhost:5000"

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()
    
    page.goto(f"{BASE}/login")
    page.fill('input[name="email"]', 'admin@sistema.com')
    page.fill('input[name="senha"]', 'admin123')
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    page.goto(f"{BASE}/dashboard")
    page.wait_for_load_state("networkidle")
    
    # Check Alpine state comprehensively
    result = page.evaluate("""() => {
        const r = {};
        r.alpineExists = typeof Alpine !== 'undefined';
        r.alpineVersion = r.alpineExists ? (Alpine.version || 'unknown') : 'N/A';
        
        // Find all elements with x-data
        const xdataEls = document.querySelectorAll('[x-data]');
        r.xdataCount = xdataEls.length;
        r.xdataInfo = [];
        xdataEls.forEach((el, i) => {
            r.xdataInfo.push({
                i: i,
                tag: el.tagName,
                xdata: el.getAttribute('x-data').substring(0, 60),
                hasAlpine: !!el.__x,
                hasAlpine2: el.__x !== undefined,
                // Try to get data
                dataKeys: el.__x ? Object.keys(el.__x.$data) : []
            });
        });
        
        // Count elements with Alpine processed
        r.alpineProcessed = document.querySelectorAll('[x-init], [x-data], [x-show], [x-cloak]').length;
        
        // Check if Alpine left any clues
        r.alpineElements = document.querySelectorAll('[x-show]').length;
        r.xCloakElements = document.querySelectorAll('[x-cloak]').length;
        
        // Try Alpine.$data
        try {
            const data = Alpine.$data(document.body);
            r.alpineDataWorks = true;
            r.bodyData = JSON.stringify(Object.keys(data));
        } catch(e) {
            r.alpineDataWorks = false;
            r.alpineDataError = e.toString().substring(0, 100);
        }
        
        return JSON.stringify(r);
    }""")
    print("Result:", result)
    
    # Now try to click and see if @click works
    print("\\nTrying globe click...")
    page.locator('button[title*="Idioma"], button[title*="Language"]').first.click()
    page.wait_for_timeout(300)
    
    result2 = page.evaluate("""() => {
        const r = {};
        // Check x-show elements visibility
        const shows = document.querySelectorAll('[x-show]');
        r.showElements = [];
        shows.forEach(el => {
            r.showElements.push({
                xshow: el.getAttribute('x-show'),
                display: el.style.display,
                visible: el.style.display !== 'none'
            });
        });
        return JSON.stringify(r);
    }""")
    print("After click x-show states:", result2)
    
    browser.close()
