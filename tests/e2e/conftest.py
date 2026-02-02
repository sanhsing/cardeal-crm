"""
E2E 測試配置
"""
import pytest

def pytest_configure(config):
    """配置 pytest"""
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests"
    )

def pytest_collection_modifyitems(config, items):
    """標記所有 E2E 測試"""
    for item in items:
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
