"""Test dropdowns open/close with Playwright."""
from playwright.sync_api import sync_playwright

BASE = "http://localhost:5000"
PASS = 0
FAIL = 0

def check(label, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  ✅ {label}")
    else:
        FAIL += 1
        print(f"  ❌ {label} - {detail}")

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    
    # Login
    page.goto(f"{BASE}/login")
    page.fill('input[name="email"]', 'admin@sistema.com')
    page.fill('input[name="senha"]', 'admin123')
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    page.goto(f"{BASE}/dashboard")
    page.wait_for_load_state("networkidle")
    
    print("\n═══ Dropdown Tests ═══")
    
    # Test 1: Language switcher opens
    lang_dropdown = page.locator('#lang-dropdown')
    lang_btn = page.locator('button[title*="Idioma"], button[title*="Language"]')
    
    check("Language button visible", lang_btn.is_visible())
    check("Language dropdown hidden initially", not lang_dropdown.is_visible())
    
    lang_btn.click()
    page.wait_for_timeout(200)
    check("Dropdown opens on click", lang_dropdown.is_visible())
    
    # Test 2: Language dropdown closes on clicking outside
    page.locator('main').click(position={"x": 50, "y": 50})
    page.wait_for_timeout(200)
    check("Dropdown closes on outside click", not lang_dropdown.is_visible())
    
    # Test 3: User menu works
    user_btn = page.locator('#user-menu button').first
    user_dropdown = page.locator('#user-dropdown')
    
    check("User button visible", user_btn.is_visible())
    check("User dropdown hidden initially", not user_dropdown.is_visible())
    
    user_btn.click()
    page.wait_for_timeout(200)
    check("User dropdown opens on click", user_dropdown.is_visible())
    
    # Test 4: User dropdown closes on outside click
    page.locator('main').click(position={"x": 50, "y": 50})
    page.wait_for_timeout(200)
    check("User dropdown closes on outside click", not user_dropdown.is_visible())
    
    # Test 5: Opening one closes the other
    lang_btn.click()
    page.wait_for_timeout(200)
    check("Lang dropdown opens", lang_dropdown.is_visible())
    
    user_btn.click()
    page.wait_for_timeout(200)
    check("User dropdown opens (closes lang)", user_dropdown.is_visible())
    check("Lang dropdown closed", not lang_dropdown.is_visible())
    
    # Test 6: Clicking same button toggles
    user_btn.click()
    page.wait_for_timeout(200)
    check("User toggles closed on second click", not user_dropdown.is_visible())
    
    # Test 7: Re-open lang and click a language link
    lang_btn.click()
    page.wait_for_timeout(200)
    check("Lang re-opens", lang_dropdown.is_visible())
    
    # Click first language link
    first_lang = lang_dropdown.locator('a').first
    first_lang.click()
    page.wait_for_timeout(500)
    check("Page navigates after lang click", "lang" in page.url or "dashboard" in page.url)
    
    print(f"\n{'='*50}")
    print(f"RESULTADO: {PASS}/{PASS+FAIL} passaram, {FAIL} falharam")
    
    browser.close()
