"""
車行寶 CRM v5.2 - 類型定義
北斗七星文創數位 × 織明

統一類型定義，提升代碼品質
"""
from typing import (
    Dict, List, Optional, Any, Union, 
    Callable, TypeVar, Generic, Tuple,
    Literal, TypedDict, Protocol
)
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum


# ============================================================
# 1. 基礎類型別名
# ============================================================

# ID 類型
CustomerID = int
VehicleID = int
DealID = int
UserID = int
TenantID = int

# JSON 類型
JSON = Dict[str, Any]
JSONList = List[JSON]

# 回調類型
T = TypeVar('T')
Handler = Callable[..., JSON]


# ============================================================
# 2. 枚舉定義
# ============================================================

class CustomerStatus(str, Enum):
    """客戶狀態"""
    POTENTIAL = 'potential'      # 潛在客戶
    CONTACTED = 'contacted'      # 已聯繫
    INTERESTED = 'interested'    # 有興趣
    NEGOTIATING = 'negotiating'  # 議價中
    DEAL = 'deal'               # 成交
    LOST = 'lost'               # 流失


class VehicleStatus(str, Enum):
    """車輛狀態"""
    AVAILABLE = 'available'      # 可售
    RESERVED = 'reserved'        # 預訂
    SOLD = 'sold'               # 已售
    MAINTENANCE = 'maintenance'  # 維修中


class DealStatus(str, Enum):
    """交易狀態"""
    PENDING = 'pending'          # 待處理
    PROCESSING = 'processing'    # 處理中
    COMPLETED = 'completed'      # 已完成
    CANCELLED = 'cancelled'      # 已取消


class PaymentMethod(str, Enum):
    """支付方式"""
    CASH = 'cash'               # 現金
    CREDIT = 'credit'           # 信用卡
    TRANSFER = 'transfer'       # 轉帳
    LOAN = 'loan'               # 貸款


class AIProvider(str, Enum):
    """AI 提供者"""
    DEEPSEEK = 'deepseek'
    OPENAI = 'openai'


# ============================================================
# 3. TypedDict 定義（API 請求/回應結構）
# ============================================================

class CustomerCreate(TypedDict, total=False):
    """創建客戶請求"""
    name: str
    phone: str
    email: Optional[str]
    line_id: Optional[str]
    source: Optional[str]
    notes: Optional[str]
    budget_min: Optional[int]
    budget_max: Optional[int]
    preferred_brands: Optional[str]


class CustomerResponse(TypedDict):
    """客戶回應"""
    id: int
    name: str
    phone: str
    email: Optional[str]
    status: str
    created_at: str
    updated_at: str


class VehicleCreate(TypedDict, total=False):
    """創建車輛請求"""
    brand: str
    model: str
    year: int
    mileage: int
    price: int
    cost: Optional[int]
    color: Optional[str]
    plate_number: Optional[str]
    vin: Optional[str]
    description: Optional[str]


class VehicleResponse(TypedDict):
    """車輛回應"""
    id: int
    brand: str
    model: str
    year: int
    price: int
    status: str
    created_at: str


class DealCreate(TypedDict, total=False):
    """創建交易請求"""
    customer_id: int
    vehicle_id: int
    sale_price: int
    payment_method: str
    notes: Optional[str]


class APIResponse(TypedDict, total=False):
    """API 標準回應"""
    success: bool
    data: Optional[Any]
    error: Optional[str]
    message: Optional[str]
    total: Optional[int]
    page: Optional[int]


class PaginatedResponse(TypedDict):
    """分頁回應"""
    success: bool
    data: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================
# 4. Dataclass 定義（內部資料結構）
# ============================================================

@dataclass
class QueryResult:
    """查詢結果"""
    success: bool
    data: List[Dict[str, Any]] = field(default_factory=list)
    total: int = 0
    error: Optional[str] = None


@dataclass
class ValidationResult:
    """驗證結果"""
    valid: bool
    errors: List[str] = field(default_factory=list)
    cleaned_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheEntry(Generic[T]):
    """快取項目"""
    key: str
    value: T
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AIRequest:
    """AI 請求"""
    prompt: str
    model: str = 'deepseek-chat'
    max_tokens: int = 1000
    temperature: float = 0.7


@dataclass
class AIResponse:
    """AI 回應"""
    success: bool
    content: str = ''
    model: str = ''
    usage: Dict[str, int] = field(default_factory=dict)
    error: Optional[str] = None


# ============================================================
# 5. Protocol 定義（介面契約）
# ============================================================

class Repository(Protocol[T]):
    """資料庫操作介面"""
    
    def get(self, id: int) -> Optional[T]: ...
    def list(self, **filters) -> List[T]: ...
    def create(self, data: Dict[str, Any]) -> T: ...
    def update(self, id: int, data: Dict[str, Any]) -> Optional[T]: ...
    def delete(self, id: int) -> bool: ...


class Service(Protocol):
    """服務介面"""
    
    def execute(self, *args, **kwargs) -> Any: ...


class Handler(Protocol):
    """處理器介面"""
    
    def handle_request(
        self, 
        method: str, 
        path: str, 
        params: Optional[Dict] = None
    ) -> Dict[str, Any]: ...


# ============================================================
# 6. 輔助函數類型
# ============================================================

# 驗證函數類型
Validator = Callable[[Any], bool]
ValidatorWithMessage = Callable[[Any], Tuple[bool, str]]

# 轉換函數類型
Transformer = Callable[[T], T]
Converter = Callable[[Any], T]

# 過濾函數類型
Predicate = Callable[[T], bool]
Filter = Callable[[List[T]], List[T]]


# 📚 知識點
# -----------
# 1. TypedDict：定義字典的鍵值類型，用於 API 請求/回應
# 2. Protocol：定義介面契約，支持結構化子類型
# 3. Generic[T]：泛型類型，提高代碼複用性
# 4. Literal：限定特定值，增強類型安全
# 5. dataclass：簡化資料類定義，自動生成 __init__ 等方法
