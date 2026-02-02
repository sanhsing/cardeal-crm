"""
車行寶 CRM v5.2 - 統一驗證服務
北斗七星文創數位 × 織明

功能：
1. 資料驗證
2. Schema 定義
3. 清理與正規化
4. 錯誤訊息標準化
"""
import re
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime


# ============================================================
# 1. 驗證結果
# ============================================================

@dataclass
class ValidationResult:
    """驗證結果"""
    valid: bool
    errors: List[str] = field(default_factory=list)
    cleaned_data: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, field: str, message: str):
        """添加錯誤"""
        self.errors.append(f"{field}: {message}")
        self.valid = False
    
    def to_dict(self) -> Dict:
        """轉換為字典"""
        return {
            'valid': self.valid,
            'errors': self.errors,
            'data': self.cleaned_data if self.valid else None
        }


# ============================================================
# 2. 驗證器定義
# ============================================================

class Validators:
    """內建驗證器"""
    
    @staticmethod
    def required(value: Any) -> Tuple[bool, str]:
        """必填驗證"""
        if value is None or value == '':
            return False, "此欄位為必填"
        return True, ""
    
    @staticmethod
    def string(value: Any, min_len: int = 0, max_len: int = 255) -> Tuple[bool, str]:
        """字串驗證"""
        if not isinstance(value, str):
            return False, "必須是字串"
        if len(value) < min_len:
            return False, f"長度不能少於 {min_len} 字元"
        if len(value) > max_len:
            return False, f"長度不能超過 {max_len} 字元"
        return True, ""
    
    @staticmethod
    def integer(value: Any, min_val: int = None, max_val: int = None) -> Tuple[bool, str]:
        """整數驗證"""
        try:
            val = int(value)
            if min_val is not None and val < min_val:
                return False, f"不能小於 {min_val}"
            if max_val is not None and val > max_val:
                return False, f"不能大於 {max_val}"
            return True, ""
        except (TypeError, ValueError):
            return False, "必須是整數"
    
    @staticmethod
    def phone(value: str) -> Tuple[bool, str]:
        """手機號碼驗證（台灣格式）"""
        if not isinstance(value, str):
            return False, "必須是字串"
        pattern = r'^09\d{8}$'
        if not re.match(pattern, value):
            return False, "請輸入有效的手機號碼（09開頭，共10碼）"
        return True, ""
    
    @staticmethod
    def email(value: str) -> Tuple[bool, str]:
        """Email 驗證"""
        if not isinstance(value, str):
            return False, "必須是字串"
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, value):
            return False, "請輸入有效的 Email"
        return True, ""
    
    @staticmethod
    def plate_number(value: str) -> Tuple[bool, str]:
        """車牌號碼驗證（台灣格式）"""
        if not isinstance(value, str):
            return False, "必須是字串"
        # 新式：ABC-1234 或 1234-AB
        # 舊式：AB-1234
        patterns = [
            r'^[A-Z]{2,3}-\d{4}$',
            r'^\d{4}-[A-Z]{2}$'
        ]
        for pattern in patterns:
            if re.match(pattern, value.upper()):
                return True, ""
        return False, "請輸入有效的車牌號碼"
    
    @staticmethod
    def year(value: Any, min_year: int = 1990, max_year: int = None) -> Tuple[bool, str]:
        """年份驗證"""
        max_year = max_year or datetime.now().year + 1
        try:
            val = int(value)
            if val < min_year or val > max_year:
                return False, f"年份必須在 {min_year}-{max_year} 之間"
            return True, ""
        except (TypeError, ValueError):
            return False, "必須是有效的年份"
    
    @staticmethod
    def enum(value: Any, choices: List[str]) -> Tuple[bool, str]:
        """枚舉驗證"""
        if value not in choices:
            return False, f"必須是以下之一：{', '.join(choices)}"
        return True, ""
    
    @staticmethod
    def date(value: str, format: str = '%Y-%m-%d') -> Tuple[bool, str]:
        """日期驗證"""
        try:
            datetime.strptime(value, format)
            return True, ""
        except (TypeError, ValueError):
            return False, f"日期格式必須是 {format}"


# ============================================================
# 3. Schema 定義
# ============================================================

class Schema:
    """資料 Schema"""
    
    def __init__(self, fields: Dict[str, Dict]):
        """
        fields: {
            'name': {
                'type': 'string',
                'required': True,
                'min_len': 2,
                'max_len': 50
            },
            'phone': {
                'type': 'phone',
                'required': True
            }
        }
        """
        self.fields = fields
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """驗證資料"""
        result = ValidationResult(valid=True, cleaned_data={})
        
        for field_name, rules in self.fields.items():
            value = data.get(field_name)
            
            # 必填檢查
            if rules.get('required', False):
                valid, msg = Validators.required(value)
                if not valid:
                    result.add_error(field_name, msg)
                    continue
            elif value is None or value == '':
                # 非必填且為空，跳過
                continue
            
            # 類型驗證
            field_type = rules.get('type', 'string')
            
            if field_type == 'string':
                valid, msg = Validators.string(
                    value,
                    rules.get('min_len', 0),
                    rules.get('max_len', 255)
                )
            elif field_type == 'integer':
                valid, msg = Validators.integer(
                    value,
                    rules.get('min'),
                    rules.get('max')
                )
                if valid:
                    value = int(value)
            elif field_type == 'phone':
                valid, msg = Validators.phone(value)
            elif field_type == 'email':
                valid, msg = Validators.email(value)
            elif field_type == 'plate_number':
                valid, msg = Validators.plate_number(value)
                if valid:
                    value = value.upper()
            elif field_type == 'year':
                valid, msg = Validators.year(value)
                if valid:
                    value = int(value)
            elif field_type == 'enum':
                valid, msg = Validators.enum(value, rules.get('choices', []))
            elif field_type == 'date':
                valid, msg = Validators.date(value, rules.get('format', '%Y-%m-%d'))
            else:
                valid, msg = True, ""
            
            if not valid:
                result.add_error(field_name, msg)
            else:
                result.cleaned_data[field_name] = value
        
        return result


# ============================================================
# 4. 預定義 Schema
# ============================================================

# 客戶 Schema
CustomerSchema = Schema({
    'name': {
        'type': 'string',
        'required': True,
        'min_len': 2,
        'max_len': 50
    },
    'phone': {
        'type': 'phone',
        'required': True
    },
    'email': {
        'type': 'email',
        'required': False
    },
    'line_id': {
        'type': 'string',
        'max_len': 50
    },
    'source': {
        'type': 'enum',
        'choices': ['walk_in', 'referral', 'online', 'phone', 'other']
    },
    'budget_min': {
        'type': 'integer',
        'min': 0
    },
    'budget_max': {
        'type': 'integer',
        'min': 0
    },
    'notes': {
        'type': 'string',
        'max_len': 1000
    }
})


# 車輛 Schema
VehicleSchema = Schema({
    'brand': {
        'type': 'string',
        'required': True,
        'max_len': 50
    },
    'model': {
        'type': 'string',
        'required': True,
        'max_len': 50
    },
    'year': {
        'type': 'year',
        'required': True
    },
    'mileage': {
        'type': 'integer',
        'min': 0,
        'max': 999999
    },
    'price': {
        'type': 'integer',
        'required': True,
        'min': 0
    },
    'cost': {
        'type': 'integer',
        'min': 0
    },
    'color': {
        'type': 'string',
        'max_len': 20
    },
    'plate_number': {
        'type': 'plate_number'
    },
    'vin': {
        'type': 'string',
        'min_len': 17,
        'max_len': 17
    },
    'description': {
        'type': 'string',
        'max_len': 2000
    }
})


# 交易 Schema
DealSchema = Schema({
    'customer_id': {
        'type': 'integer',
        'required': True,
        'min': 1
    },
    'vehicle_id': {
        'type': 'integer',
        'required': True,
        'min': 1
    },
    'sale_price': {
        'type': 'integer',
        'required': True,
        'min': 0
    },
    'payment_method': {
        'type': 'enum',
        'choices': ['cash', 'credit', 'transfer', 'loan']
    },
    'notes': {
        'type': 'string',
        'max_len': 1000
    }
})


# ============================================================
# 5. 便捷函數
# ============================================================

def validate_customer(data: Dict) -> ValidationResult:
    """驗證客戶資料"""
    return CustomerSchema.validate(data)


def validate_vehicle(data: Dict) -> ValidationResult:
    """驗證車輛資料"""
    return VehicleSchema.validate(data)


def validate_deal(data: Dict) -> ValidationResult:
    """驗證交易資料"""
    return DealSchema.validate(data)


def validate_request(schema: Schema, data: Dict) -> Tuple[bool, Dict]:
    """
    驗證請求資料
    
    Returns:
        (valid, result): valid 為 True 時 result 為清理後的資料
                         valid 為 False 時 result 為錯誤資訊
    """
    result = schema.validate(data)
    if result.valid:
        return True, result.cleaned_data
    else:
        return False, {'errors': result.errors}


# 📚 知識點
# -----------
# 1. Schema 模式：定義資料結構和驗證規則
# 2. 驗證器組合：每個欄位可組合多個驗證規則
# 3. 資料清理：驗證同時進行類型轉換和格式化
# 4. 錯誤收集：收集所有錯誤而非遇到第一個就停止
# 5. 預定義 Schema：常用實體的 Schema 預先定義
