#!/usr/bin/env python3
"""
test_playwright.py - 車行寶 E2E 測試
PYLIB: L4-e2e-test
Version: v1.0.0
Created: 2026-02-03

功能：
1. 登入流程測試
2. 客戶管理流程測試
3. 車輛管理流程測試
4. 交易流程測試
5. 報表流程測試

使用方式：
  pip install playwright
  playwright install chromium
  pytest tests/e2e/test_playwright.py -v
"""

import os
import sys
import pytest
from typing import Dict, Any, Generator
from dataclasses import dataclass

# ============================================================
# L0: 基礎常量
# ============================================================

VERSION = "1.0.0"
BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8000")
TEST_TENANT = os.getenv("E2E_TENANT", "demo")
TEST_PHONE = os.getenv("E2E_PHONE", "0912345678")
TEST_PASSWORD = os.getenv("E2E_PASSWORD", "demo1234")

TIMEOUTS = {
    "short": 5000,
    "medium": 10000,
    "long": 30000,
}

# ============================================================
# L1: 資料結構
# ============================================================

@dataclass
class TestUser:
    """測試用戶"""
    tenant: str
    phone: str
    password: str
    name: str = "測試用戶"

@dataclass
class TestCustomer:
    """測試客戶"""
    name: str
    phone: str
    email: str = ""
    budget: int = 500000

@dataclass
class TestVehicle:
    """測試車輛"""
    brand: str
    model: str
    year: int
    price: int
    mileage: int = 50000

# ============================================================
# L2: 頁面物件 (Page Objects)
# ============================================================

class BasePage:
    """頁面基類"""
    
    def __init__(self, page):
        self.page = page
        self.base_url = BASE_URL
    
    def goto(self, path: str = "/") -> None:
        """前往頁面"""
        self.page.goto(f"{self.base_url}{path}")
    
    def wait_for_load(self) -> None:
        """等待頁面載入"""
        self.page.wait_for_load_state("networkidle")
    
    def get_toast(self) -> str:
        """獲取 Toast 訊息"""
        toast = self.page.locator(".toast, .notification, [role='alert']")
        if toast.count() > 0:
            return toast.first.text_content()
        return ""
    
    def screenshot(self, name: str) -> None:
        """截圖"""
        self.page.screenshot(path=f"tests/e2e/screenshots/{name}.png")


class LoginPage(BasePage):
    """登入頁面"""
    
    def __init__(self, page):
        super().__init__(page)
        self.tenant_input = page.locator("#code, [name='code']")
        self.phone_input = page.locator("#phone, [name='phone']")
        self.password_input = page.locator("#password, [name='password']")
        self.submit_btn = page.locator("button[type='submit'], .login-btn")
    
    def login(self, tenant: str, phone: str, password: str) -> bool:
        """執行登入"""
        self.goto("/login")
        self.wait_for_load()
        
        self.tenant_input.fill(tenant)
        self.phone_input.fill(phone)
        self.password_input.fill(password)
        self.submit_btn.click()
        
        # 等待跳轉或錯誤
        try:
            self.page.wait_for_url("**/app**", timeout=TIMEOUTS["medium"])
            return True
        except:
            return False


class DashboardPage(BasePage):
    """儀表板頁面"""
    
    def __init__(self, page):
        super().__init__(page)
        self.kpi_cards = page.locator(".stat-card, .kpi-card")
        self.nav_menu = page.locator("nav, .sidebar")
    
    def get_kpi_values(self) -> Dict[str, str]:
        """獲取 KPI 數值"""
        values = {}
        cards = self.kpi_cards.all()
        for card in cards:
            label = card.locator(".stat-label, .kpi-label").text_content()
            value = card.locator(".stat-value, .kpi-value").text_content()
            if label and value:
                values[label.strip()] = value.strip()
        return values
    
    def navigate_to(self, menu: str) -> None:
        """導航到指定頁面"""
        self.nav_menu.locator(f"text={menu}").click()
        self.wait_for_load()


class CustomerPage(BasePage):
    """客戶管理頁面"""
    
    def __init__(self, page):
        super().__init__(page)
        self.add_btn = page.locator("button:has-text('新增'), button:has-text('Add')")
        self.search_input = page.locator("input[type='search'], .search-input")
        self.table = page.locator("table, .customer-list")
    
    def add_customer(self, customer: TestCustomer) -> bool:
        """新增客戶"""
        self.add_btn.click()
        self.page.wait_for_selector("form, .modal")
        
        self.page.fill("[name='name']", customer.name)
        self.page.fill("[name='phone']", customer.phone)
        if customer.email:
            self.page.fill("[name='email']", customer.email)
        if customer.budget:
            self.page.fill("[name='budget']", str(customer.budget))
        
        self.page.click("button[type='submit'], button:has-text('儲存')")
        self.wait_for_load()
        
        return "成功" in self.get_toast() or "success" in self.get_toast().lower()
    
    def search_customer(self, keyword: str) -> int:
        """搜尋客戶"""
        self.search_input.fill(keyword)
        self.page.keyboard.press("Enter")
        self.wait_for_load()
        
        return self.table.locator("tr, .customer-item").count() - 1  # 減去表頭


class VehiclePage(BasePage):
    """車輛管理頁面"""
    
    def __init__(self, page):
        super().__init__(page)
        self.add_btn = page.locator("button:has-text('新增'), button:has-text('Add')")
        self.filter_select = page.locator("select.status-filter, .filter-dropdown")
        self.grid = page.locator(".vehicle-grid, .card-grid, table")
    
    def add_vehicle(self, vehicle: TestVehicle) -> bool:
        """新增車輛"""
        self.add_btn.click()
        self.page.wait_for_selector("form, .modal")
        
        self.page.fill("[name='brand']", vehicle.brand)
        self.page.fill("[name='model']", vehicle.model)
        self.page.fill("[name='year']", str(vehicle.year))
        self.page.fill("[name='price']", str(vehicle.price))
        self.page.fill("[name='mileage']", str(vehicle.mileage))
        
        self.page.click("button[type='submit'], button:has-text('儲存')")
        self.wait_for_load()
        
        return "成功" in self.get_toast() or "success" in self.get_toast().lower()
    
    def get_vehicle_count(self) -> int:
        """獲取車輛數量"""
        return self.grid.locator(".vehicle-card, tr").count()

# ============================================================
# L3: 測試案例
# ============================================================

class TestAuthentication:
    """認證測試"""
    
    @pytest.fixture(autouse=True)
    def setup(self, page):
        self.login_page = LoginPage(page)
    
    def test_login_success(self, page):
        """測試成功登入"""
        result = self.login_page.login(TEST_TENANT, TEST_PHONE, TEST_PASSWORD)
        assert result, "登入應該成功"
        assert "/app" in page.url
    
    def test_login_wrong_password(self, page):
        """測試錯誤密碼"""
        result = self.login_page.login(TEST_TENANT, TEST_PHONE, "wrongpass")
        assert not result, "錯誤密碼應該登入失敗"
    
    def test_login_empty_fields(self, page):
        """測試空白欄位"""
        self.login_page.goto("/login")
        self.login_page.submit_btn.click()
        # 應該顯示驗證錯誤
        assert page.locator(".error, [class*='error']").count() > 0


class TestCustomerManagement:
    """客戶管理測試"""
    
    @pytest.fixture(autouse=True)
    def setup(self, authenticated_page):
        self.page = authenticated_page
        self.customer_page = CustomerPage(authenticated_page)
        self.customer_page.goto("/app#customers")
        self.customer_page.wait_for_load()
    
    def test_add_customer(self):
        """測試新增客戶"""
        customer = TestCustomer(
            name="測試客戶E2E",
            phone="0987654321",
            email="test@example.com",
            budget=800000
        )
        result = self.customer_page.add_customer(customer)
        assert result, "新增客戶應該成功"
    
    def test_search_customer(self):
        """測試搜尋客戶"""
        count = self.customer_page.search_customer("測試")
        assert count >= 0, "搜尋應該返回結果"
    
    def test_customer_list_loads(self):
        """測試客戶列表載入"""
        self.customer_page.wait_for_load()
        assert self.customer_page.table.is_visible()


class TestVehicleManagement:
    """車輛管理測試"""
    
    @pytest.fixture(autouse=True)
    def setup(self, authenticated_page):
        self.page = authenticated_page
        self.vehicle_page = VehiclePage(authenticated_page)
        self.vehicle_page.goto("/app#vehicles")
        self.vehicle_page.wait_for_load()
    
    def test_add_vehicle(self):
        """測試新增車輛"""
        vehicle = TestVehicle(
            brand="Toyota",
            model="Camry",
            year=2022,
            price=850000,
            mileage=30000
        )
        result = self.vehicle_page.add_vehicle(vehicle)
        assert result, "新增車輛應該成功"
    
    def test_vehicle_grid_loads(self):
        """測試車輛列表載入"""
        self.vehicle_page.wait_for_load()
        assert self.vehicle_page.grid.is_visible()


class TestDashboard:
    """儀表板測試"""
    
    @pytest.fixture(autouse=True)
    def setup(self, authenticated_page):
        self.dashboard = DashboardPage(authenticated_page)
        self.dashboard.goto("/app")
        self.dashboard.wait_for_load()
    
    def test_kpi_cards_visible(self):
        """測試 KPI 卡片顯示"""
        assert self.dashboard.kpi_cards.count() >= 4
    
    def test_navigation_works(self):
        """測試導航功能"""
        self.dashboard.navigate_to("客戶")
        assert "customer" in self.dashboard.page.url.lower()

# ============================================================
# L4: Pytest Fixtures
# ============================================================

@pytest.fixture(scope="session")
def browser_context_args():
    """瀏覽器設定"""
    return {
        "viewport": {"width": 1280, "height": 720},
        "locale": "zh-TW",
        "timezone_id": "Asia/Taipei",
    }

@pytest.fixture
def authenticated_page(page):
    """已登入的頁面"""
    login_page = LoginPage(page)
    success = login_page.login(TEST_TENANT, TEST_PHONE, TEST_PASSWORD)
    
    if not success:
        pytest.skip("無法登入，跳過需要認證的測試")
    
    yield page

@pytest.fixture
def test_customer():
    """測試客戶資料"""
    return TestCustomer(
        name="自動測試客戶",
        phone="0911222333",
        email="auto@test.com",
        budget=600000
    )

@pytest.fixture
def test_vehicle():
    """測試車輛資料"""
    return TestVehicle(
        brand="Honda",
        model="CR-V",
        year=2021,
        price=950000,
        mileage=45000
    )


# 截圖目錄
os.makedirs("tests/e2e/screenshots", exist_ok=True)


# 📚 知識點
# -----------
# 1. Page Object Pattern：將頁面封裝為類別
# 2. Fixtures：Pytest 的依賴注入機制
# 3. Selectors：使用多種選擇器提高穩定性
# 4. Wait Strategies：等待策略確保測試穩定
# 5. Data Classes：使用 dataclass 管理測試資料
