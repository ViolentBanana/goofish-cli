"""Installer must preserve existing settings and refuse ambiguous replacements."""
from __future__ import annotations

import importlib.util
import stat
from pathlib import Path

import pytest


def helper():
    path = Path(__file__).resolve().parents[1] / "scripts/configure_codex_mcp.py"
    assert path.exists(), "Codex configuration helper not implemented"
    spec = importlib.util.spec_from_file_location("codex_helper", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse(text):
    import tomllib
    return tomllib.loads(text)


def test_configure_preserves_settings_and_is_idempotent(tmp_path):
    module = helper()
    path = tmp_path / "config.toml"
    original = 'model = "test-model"\n\n[mcp_servers.other]\ncommand = "test-command"\n'
    path.write_text(original)
    assert module.configure(path, "/usr/local/bin/docker") == "added"
    first = path.read_text()
    assert first.startswith(original)
    data = parse(first)
    assert data["mcp_servers"]["other"]["command"] == "test-command"
    goofish = data["mcp_servers"]["goofish"]
    assert goofish["args"] == ["exec", "-i", "goofish-cli", "goofish-cli"]
    assert goofish["tool_timeout_sec"] == 180
    assert "auth_login" in goofish["disabled_tools"]
    assert goofish["default_tools_approval_mode"] == "prompt"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    backups = list(tmp_path.glob("config.toml.backup-*"))
    assert len(backups) == 1
    assert backups[0].read_text() == original
    assert stat.S_IMODE(backups[0].stat().st_mode) == 0o600
    assert module.configure(path, "/usr/local/bin/docker") == "already-configured"
    assert path.read_text() == first
    assert len(list(tmp_path.glob("config.toml.backup-*"))) == 1


def test_conflicting_server_is_not_overwritten(tmp_path):
    path = tmp_path / "config.toml"
    original = '[mcp_servers.goofish]\ncommand = "another-server"\n'
    path.write_text(original)
    with pytest.raises(ValueError, match="goofish"):
        helper().configure(path, "/usr/local/bin/docker")
    assert path.read_text() == original
    assert not list(tmp_path.glob("config.toml.backup-*"))


def test_invalid_toml_is_not_overwritten(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('[broken\n')
    with pytest.raises(ValueError):
        helper().configure(path, "/usr/local/bin/docker")
    assert path.read_text() == '[broken\n'


def test_fresh_config_with_spaces_and_quotes_in_command(tmp_path):
    path = tmp_path / "custom home" / "config.toml"
    command = '/tmp/tools with "quotes"/docker'
    assert helper().configure(path, command) == "added"
    assert parse(path.read_text())["mcp_servers"]["goofish"]["command"] == command
    assert not list(path.parent.glob("config.toml.backup-*"))


@pytest.mark.parametrize("option", [
    "enabled = false\n",
    'enabled_tools = ["auth_status"]\n',
])
def test_existing_disabled_or_filtered_server_is_not_reported_as_ready(tmp_path, option):
    module = helper()
    path = tmp_path / "config.toml"
    module.configure(path, "/usr/local/bin/docker")
    original = path.read_text() + option
    path.write_text(original)
    with pytest.raises(ValueError, match="goofish"):
        module.configure(path, "/usr/local/bin/docker")
    assert path.read_text() == original


def test_existing_conflicting_disabled_tools_are_not_reported_as_ready(tmp_path):
    module = helper()
    path = tmp_path / "config.toml"
    module.configure(path, "/usr/local/bin/docker")
    original = path.read_text().replace('"auth_login", ', '"search_items", ')
    path.write_text(original)
    with pytest.raises(ValueError, match="goofish"):
        module.configure(path, "/usr/local/bin/docker")
    assert path.read_text() == original
