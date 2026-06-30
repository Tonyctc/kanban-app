"""Playwright debug: test dropdown open/close behavior."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from playwright.sync_api import sync_playwright

BASE = "http://localhost:5000"

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()
    
    # Login
    page.goto(f"{BASE}/login")
    page.fill('input[name="email"]', 'admin@sistema.com')
    page.fill('input[name="senha"]', 'admin123')
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    print(f"After login: {page.url}")
    
    # Go to dashboard
    page.goto(f"{BASE}/dashboard")
    page.wait_for_load_state("networkidle")
    print(f"Dashboard loaded")
    
    # Check Alpine.js is loaded
    alpine_loaded = page.evaluate("typeof Alpine !== 'undefined'")
    print(f"Alpine.js loaded: {alpine_loaded}")
    
    if alpine_loaded:
        # Check initial langOpen state
        initial_state = page.evaluate("""
            (() => {
                const el = document.querySelector('[x-data*="langOpen"]');
                if (!el) return 'no element found';
                const alpine = Alpine.$data(el);
                return JSON.stringify({ langOpen: alpine.langOpen });
            })()
        """)
        print(f"Initial state: {initial_state}")
        
        # Count how many elements match the langOpen x-data
        count_elements = page.evaluate("""
            document.querySelectorAll('[x-data*="langOpen"]').length
        """)
        print(f"Elements with langOpen x-data: {count_elements}")
    
    # Click the globe button
    globe = page.locator('button[title*="Idioma"], button[title*="Language"]').first
    print(f"Globe visible: {globe.is_visible()}")
    globe.click()
    page.wait_for_timeout(500)
    
    # Check if dropdown appeared
    if alpine_loaded:
        state = page.evaluate("""
            (() => {
                const el = document.querySelector('[x-data*="langOpen"]');
                if (!el) return 'no element';
                const alpine = Alpine.$data(el);
                return JSON.stringify({ langOpen: alpine.langOpen });
            })()
        """)
        print(f"After click: {state}")
    
    # Check if dropdown panel is visible
    dropdown_visible = page.evaluate("""
        document.querySelector('[x-show="langOpen"]')?.style?.display !== 'none'
    """)
    print(f"Dropdown panel visible: {dropdown_visible}")
    
    # Click on main content area to try to close
    main = page.locator('main')
    main.click(position={"x": 10, "y": 10})
    page.wait_for_timeout(500)
    
    if alpine_loaded:
        state2 = page.evaluate("""
            (() => {
                const el = document.querySelector('[x-data*="langOpen"]');
                if (!el) return 'no element';
                const alpine = Alpine.$data(el);
                return JSON.stringify({ langOpen: alpine.langOpen });
            })()
        """)
        print(f"After clicking main: {state2}")
    
    # Try clicking outside via body
    page.locator('footer').click()
    page.wait_for_timeout(500)
    
    if alpine_loaded:
        state3 = page.evaluate("""
            (() => {
                const el = document.querySelector('[x-data*="langOpen"]');
                if (!el) return 'no element';
                const alpine = Alpine.$data(el);
                return JSON.stringify({ langOpen: alpine.langOpen });
            })()
        """)
        print(f"After clicking footer: {state3}")
    
    # Try directly setting via Alpine
    page.evaluate("""
        const el = document.querySelector('[x-data*="langOpen"]');
        if (el) {
            Alpine.$data(el).langOpen = false;
        }
    """)
    page.wait_for_timeout(300)
    
    after_js = page.evaluate("""
        const el = document.querySelector('[x-data*="langOpen"]');
        if (!el) return 'no element';
        return Alpine.$data(el).langOpen ? 'still open' : 'closed';
    """)
    print(f"After JS direct set: {after_js}")
    
    browser.close()
