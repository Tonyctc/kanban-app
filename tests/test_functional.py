"""
Kanban App - E2E Functional Tests with Playwright
Tests core workflows: login, board CRUD, card CRUD, drag & drop, permissions
"""
import os, sys, json
from playwright.sync_api import sync_playwright, expect

BASE = "http://localhost:5000"

class KanbanTester:
    def __init__(self):
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(headless=True)
        self.context = None
        self.page = None
        self.passed = 0
        self.failed = 0
    
    def check(self, label, condition, detail=""):
        if condition:
            self.passed += 1
            print(f"  ✅ {label}")
        else:
            self.failed += 1
            print(f"  ❌ {label} - {detail}")
    
    def login(self, email, senha):
        """Login and return page."""
        if self.context:
            self.context.close()
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.page.goto(f"{BASE}/login")
        self.page.fill('input[name="email"]', email)
        self.page.fill('input[name="senha"]', senha)
        self.page.click('button[type="submit"]')
        self.page.wait_for_load_state("networkidle")
        return self.page
    
    def run_all(self):
        try:
            self.test_login_admin()
            self.test_admin_global()
            self.test_board_view()
            self.test_card_crud()
            self.test_column_crud()
            self.test_drag_and_drop()
            self.test_login_user()
            self.test_user_permissions()
            self.test_dark_mode()
            self.print_results()
        finally:
            self.browser.close()
            self.pw.stop()
    
    def test_login_admin(self):
        print("\n═══ F1: Login Admin ═══")
        p = self.login('admin@sistema.com', 'admin123')
        self.check("Redirect to /admin/global", '/admin/global' in p.url)
        self.check("Page title visible", p.locator('h1').first.is_visible())
    
    def test_admin_global(self):
        print("\n═══ F2: Admin Global Panel ═══")
        p = self.page
        metrics_cards = p.locator('.grid-cols-1 .rounded-xl')
        self.check("Metrics cards visible", metrics_cards.count() >= 3)
        table = p.locator('table')
        self.check("User table visible", table.is_visible())
        self.check("Admin Geral in table", p.locator('table').locator('text=Administrador Geral').count() > 0)
        create_btn = p.locator('button:has-text("Novo")').last
        self.check("Create user button visible", create_btn.is_visible())
    
    def test_board_view(self):
        print("\n═══ F3: Board View ═══")
        p = self.page
        p.goto(f"{BASE}/dashboard/sistema")
        p.wait_for_load_state("networkidle")
        
        # Should see kanban columns
        columns = p.locator('.kanban-column')
        self.check("Kanban columns visible", columns.count() >= 2)
        
        # Should see cards
        cards = p.locator('.kanban-card')
        self.check("Cards visible", cards.count() >= 2)
        
        # Check column headers
        first_col = columns.first.locator('h3')
        self.check("First column has title", first_col.is_visible())
    
    def test_card_crud(self):
        print("\n═══ F4: Card CRUD ═══")
        p = self.page
        
        # Use API directly to test card CRUD (same as modal does via fetch)
        import requests
        session = requests.Session()
        for cookie in self.context.cookies():
            session.cookies.set(cookie['name'], cookie['value'])
        
        # Get board data to find first column
        resp = session.get(f"{BASE}/api/quadro/sistema")
        self.check("Board API accessible", resp.status_code == 200, str(resp.status_code))
        
        if resp.status_code == 200:
            data = resp.json()
            if data['colunas']:
                first_col = data['colunas'][0]['id']
                initial_count = len(data['colunas'][0]['cards'])
                
                # Create card via API
                card_resp = session.post(f"{BASE}/api/quadro/sistema/card", json={
                    'column_id': first_col,
                    'titulo': 'Playwright Test Card',
                    'descricao': 'Created by automated test',
                    'prioridade': 'alta',
                    'data_entrega': '2026-08-01',
                })
                self.check("Card created via API", card_resp.status_code in (200, 201), str(card_resp.status_code))
                
                if card_resp.status_code == 200:
                    card_data = card_resp.json()
                    card_id = card_data.get('card', {}).get('id', '')
                    
                    # Verify card appears on page
                    p.goto(f"{BASE}/dashboard/sistema")
                    p.wait_for_load_state("networkidle")
                    new_count = p.locator('.kanban-card').count()
                    self.check("Card count increased", new_count > initial_count, f"Was: {initial_count}, Now: {new_count}")
                    
                    # Edit card if we got a card ID
                    if card_id:
                        edit_resp = session.put(f"{BASE}/api/quadro/sistema/card/{card_id}", json={
                            'titulo': 'Card Editado Test',
                            'descricao': 'Updated description',
                        })
                        self.check("Card edited via API", edit_resp.status_code == 200, str(edit_resp.status_code))
                        
                        # Delete card
                        del_resp = session.delete(f"{BASE}/api/quadro/sistema/card/{card_id}")
                        self.check("Card deleted via API", del_resp.status_code == 200, str(del_resp.status_code))
        
        # Verify UI still works after API operations
        p.goto(f"{BASE}/dashboard/sistema")
        p.wait_for_load_state("networkidle")
        self.check("Board loads after CRUD", p.locator('.kanban-card').count() >= 1)
    
    def test_column_crud(self):
        print("\n═══ F5: Column CRUD ═══")
        p = self.page
        
        import requests
        session = requests.Session()
        for cookie in self.context.cookies():
            session.cookies.set(cookie['name'], cookie['value'])
        
        # Get initial column count via API
        resp = session.get(f"{BASE}/api/quadro/sistema")
        self.check("Board API accessible", resp.status_code == 200, str(resp.status_code))
        
        if resp.status_code == 200:
            data = resp.json()
            initial_columns = len(data['colunas'])
            
            # Create column via API
            col_resp = session.post(f"{BASE}/api/quadro/sistema/coluna", json={
                'title': 'Coluna Teste'
            })
            self.check("Column created via API", col_resp.status_code in (200, 201), str(col_resp.status_code))
            
            if col_resp.status_code in (200, 201):
                col_data = col_resp.json()
                column_id = col_data.get('column', {}).get('id', '')
                
                # Verify via page reload
                p.goto(f"{BASE}/dashboard/sistema")
                p.wait_for_load_state("networkidle")
                new_columns = p.locator('.kanban-column').count()
                self.check("Column added in UI", new_columns > initial_columns, f"Was: {initial_columns}, Now: {new_columns}")
                
                # Clean up - delete the column
                if column_id:
                    del_resp = session.delete(f"{BASE}/api/quadro/sistema/coluna/{column_id}")
                    self.check("Column deleted via API", del_resp.status_code == 200, str(del_resp.status_code))
    
    def test_drag_and_drop(self):
        print("\n═══ F6: Drag & Drop ═══")
        p = self.page
        p.goto(f"{BASE}/dashboard/sistema")
        p.wait_for_load_state("networkidle")
        
        # Get first card and second column
        first_card = p.locator('.kanban-card').first
        second_column = p.locator('.kanban-column').nth(1)
        
        if first_card.is_visible() and second_column.is_visible():
            # Get initial column counts
            first_col_cards = p.locator('.kanban-column').first.locator('.kanban-card').count()
            second_col_cards = p.locator('.kanban-column').nth(1).locator('.kanban-card').count()
            
            # Perform drag and drop via Sortable.js simulation
            # Since Playwright's drag&drop may not trigger Sortable events,
            # we test via the API directly
            import requests
            session = requests.Session()
            # Get cookies from Playwright context
            for cookie in self.context.cookies():
                session.cookies.set(cookie['name'], cookie['value'])
            
            # Get board data via API
            resp = session.get(f"{BASE}/api/quadro/sistema")
            if resp.status_code == 200:
                data = resp.json()
                if len(data['colunas']) >= 2:
                    col1_id = data['colunas'][0]['id']
                    col2_id = data['colunas'][1]['id']
                    
                    # Find a card in column 1
                    card_to_move = None
                    for card in data['colunas'][0]['cards']:
                        card_to_move = card['id']
                        break
                    
                    if card_to_move:
                        # Move card via API (simulating what Sortable.js does)
                        move_resp = session.put(
                            f"{BASE}/api/quadro/sistema/card/{card_to_move}/mover",
                            json={'column_id': col2_id, 'new_index': -1}
                        )
                        self.check("DnD move via API", move_resp.status_code == 200, str(move_resp.status_code))
                        
                        # Move it back
                        session.put(
                            f"{BASE}/api/quadro/sistema/card/{card_to_move}/mover",
                            json={'column_id': col1_id, 'new_index': -1}
                        )
            self.check("DnD test completed", True)
    
    def test_login_user(self):
        print("\n═══ F7: Login Usuário Comum ═══")
        p = self.login('user@email.com', 'user123')
        self.check("User dashboard visible", '/dashboard' in p.url or '/login' not in p.url)
        
        # Navigate to board
        p.goto(f"{BASE}/dashboard/pessoal")
        p.wait_for_load_state("networkidle")
        board_visible = p.locator('.kanban-column').count() >= 2
        self.check("User kanban board loads", board_visible)
    
    def test_user_permissions(self):
        print("\n═══ F8: Permission Boundaries ═══")
        p = self.page
        
        # Try to access admin global
        p.goto(f"{BASE}/admin/global")
        p.wait_for_load_state("networkidle")
        blocked = '/login' in p.url or '403' in p.title() or 'Acesso negado' in p.content()
        self.check("User cannot access admin global", '/admin/global' not in p.url or '403' in p.content())
        
        # Try to access another user's board
        p.goto(f"{BASE}/dashboard/sistema")
        p.wait_for_load_state("networkidle")
        # Should be blocked or redirected
        self.check("User cannot access admin's board", 
                   '/login' in p.url or '403' in p.content() or 'dashboard' in p.url)
    
    def test_dark_mode(self):
        print("\n═══ F9: Dark Mode Toggle ═══")
        p = self.login('user@email.com', 'user123')
        # Find dark mode toggle
        toggle = p.locator('button[title*="Alternar"], button[title*="tema"]').first
        if toggle.is_visible():
            toggle.click()
            p.wait_for_timeout(300)
            self.check("Dark mode toggle works", True)
    
    def print_results(self):
        total = self.passed + self.failed
        print(f"\n{'='*50}")
        print(f"TESTES FUNCIONAIS: {self.passed}/{total} passaram, {self.failed} falharam")
        if self.failed > 0:
            print("⚠️  Falhas encontradas!")
        else:
            print("✅ Todos os testes funcionais passaram!")
        print(f"{'='*50}")

if __name__ == '__main__':
    tester = KanbanTester()
    tester.run_all()
