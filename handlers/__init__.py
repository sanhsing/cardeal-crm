"""
車行寶 CRM v5.1 - Handlers 模組
北斗七星文創數位 × 織明
"""
from typing import Dict, List, Any, Optional, Union, Callable, Tuple


# 基礎工具
from .base import BaseHandler

# 中間件
from . import middleware

# 功能處理器
from . import auth_handler
from . import customer_handler
from . import vehicle_handler
from . import deal_handler
from . import report_handler
from . import webhook_handler
from . import upload_handler
from . import batch_handler
from . import ai_report_handler
from . import system_handler
from . import push_handler
from . import line_handler
from . import monitoring_handler
from . import docs_handler
from . import apm_handler
from . import dashboard_handler

# P11-P15 新增 Handlers
from . import i18n_handler
from . import prediction_handler

