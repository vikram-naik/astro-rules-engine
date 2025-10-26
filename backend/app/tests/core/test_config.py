import json
import importlib
import logging
import pytest
from app.core.common import config

def test_default_settings_values(monkeypatch):
    # Reload to ensure defaults are applied
    importlib.reload(config)
    s = config.Settings()

    assert s.database_url.endswith("astro_rules.db")
    assert s.log_level == "INFO"
    assert s.provider_type in ("swisseph", "skyfield", "stub")
    assert s.market_provider_type in ("yahoo", "csv")
    assert s.default_sector_ticker == "^GSPC"
    assert isinstance(s.astro_combust_orbs, dict)
    assert s.model_config["env_file"] == ".env"

def test_parse_astro_combust_orbs_from_dict(monkeypatch):
    data = {"Sun": 8, "Moon": "10", "Invalid": "abc"}
    s = config.Settings(astro_combust_orbs=data)
    # Only valid float-parsable keys should remain, normalized to lowercase
    assert "sun" in s.astro_combust_orbs
    assert "moon" in s.astro_combust_orbs
    assert "invalid" not in s.astro_combust_orbs
    assert all(isinstance(v, float) for v in s.astro_combust_orbs.values())

def test_parse_astro_combust_orbs_from_json(monkeypatch, caplog):
    raw = json.dumps({"Sun": 5.5, "Venus": "6"})
    s = config.Settings(astro_combust_orbs=raw)
    assert s.astro_combust_orbs["sun"] == 5.5
    assert s.astro_combust_orbs["venus"] == 6.0

def test_invalid_json_and_unsupported_types(monkeypatch, caplog):
    caplog.set_level(logging.WARNING)
    s1 = config.Settings(astro_combust_orbs="not-json")
    assert s1.astro_combust_orbs == {}

    # invalid type like list
    s2 = config.Settings(astro_combust_orbs=[1, 2, 3])
    assert s2.astro_combust_orbs == {}
    assert any("unsupported format" in rec.message for rec in caplog.records)

def test_global_settings_singleton(monkeypatch):
    # ensures that the module-level `settings` object is an instance of Settings
    assert isinstance(config.settings, config.Settings)
    # ensure defaults are accessible
    assert hasattr(config.settings, "database_url")
    assert hasattr(config.settings, "astro_combust_orbs")
