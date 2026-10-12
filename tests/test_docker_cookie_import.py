"""Cookie import filtering must never forward unrelated website sessions."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def helper():
    path = Path(__file__).resolve().parents[1] / "docker/import_chrome_cookies.py"
    spec = importlib.util.spec_from_file_location("cookie_helper", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_filter_preserves_scope_and_rejects_lookalike_domains():
    records = [
        {"name": "unb", "value": "test-user", "domain": ".goofish.com", "path": "/"},
        {"name": "_m_h5_tk", "value": "test-token", "domain": ".taobao.com", "path": "/api"},
        {"name": "private", "value": "test", "domain": "evilgoofish.com", "path": "/"},
        {"name": "private", "value": "test", "domain": "goofish.com.evil.test", "path": "/"},
    ]
    assert helper().validate_records(records + records[:1]) == records[:2]


def test_missing_auth_cannot_be_imported():
    with pytest.raises(ValueError):
        helper().validate_records([
            {"name": "unb", "value": "test-user", "domain": ".goofish.com", "path": "/"},
        ])


@pytest.mark.parametrize("output", ['{"valid": false}', '[]', 'null', 'not-json'])
def test_invalid_status_is_never_success(output):
    assert not helper().status_valid(output)


def test_valid_status_is_success():
    assert helper().status_valid('{"valid": true}')
