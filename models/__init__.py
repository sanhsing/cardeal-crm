"""
車行寶 CRM v5.1 - Models 模組
北斗七星文創數位 × 織明
"""

# 資料庫核心
from .database import get_connection, log_error

# Session 管理
from .session import (
    create_session,
    get_session,
    delete_session,
    extend_session,
    cleanup_sessions,
    log_activity
)

# 租戶管理
from .tenant import (
    get_tenant_by_code,
    get_tenant_by_id,
    get_all_tenants,
    create_tenant,
    update_tenant,
    verify_login,
    check_plan_features
)

# Schema 定義
from .schema import (
    init_master_db,
    init_tenant_database,
    migrate_database,
    MASTER_TABLES,
    TENANT_TABLES
)
