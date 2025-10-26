import json
import importlib
import logging
import pytest
from pathlib import Path
from app.core.common import config


def test_default_settings_values(monkeypatch):
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

    s2 = config.Settings(astro_combust_orbs=[1, 2, 3])
    assert s2.astro_combust_orbs == {}
    assert any("unsupported format" in rec.message for rec in caplog.records)


def test_global_settings_singleton(monkeypatch):
    assert isinstance(config.settings, config.Settings)
    assert hasattr(config.settings, "database_url")
    assert hasattr(config.settings, "astro_combust_orbs")


# --- NEW TESTS FOR ORB LOGIC ---


def test_orb_inline_json(monkeypatch):
    """Ensure inline JSON in ORB_OVERRIDES is parsed correctly."""
    inline_json = '{"mars-ketu": 4.0, "saturn-rahu": 6.0}'
    s = config.Settings(orb_overrides=inline_json)
    assert s.orb_overrides["mars-ketu"] == 4.0
    assert s.orb_overrides["saturn-rahu"] == 6.0


def test_orb_external_file(monkeypatch, tmp_path):
    """Ensure external file path is read and overrides inline settings."""
    orb_file = tmp_path / "orb_overrides.json"
    orb_data = {"mars-ketu": 3.5, "sun-moon": 11.5}
    orb_file.write_text(json.dumps(orb_data))

    monkeypatch.setenv("ORB_OVERRIDES_FILE", str(orb_file))
    importlib.reload(config)
    s = config.settings

    assert s.orb_overrides["mars-ketu"] == 3.5
    assert s.orb_overrides["sun-moon"] == 11.5


def test_orb_external_file_invalid(monkeypatch, tmp_path, caplog):
    """Ensure gracefully handles missing or invalid JSON file."""
    caplog.set_level(logging.WARNING)
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("not-json")

    monkeypatch.setenv("ORB_OVERRIDES_FILE", str(bad_file))
    importlib.reload(config)
    s = config.settings

    # Should fall back to default
    assert "sun-moon" in s.orb_overrides
    assert isinstance(s.orb_overrides["sun-moon"], float)


def test_orb_file_missing(monkeypatch, caplog):
    """Ensure missing file logs warning and defaults are loaded."""
    caplog.set_level(logging.WARNING)
    monkeypatch.setenv("ORB_OVERRIDES_FILE", "/tmp/nonexistent.json")
    importlib.reload(config)
    s = config.settings

    assert "sun-moon" in s.orb_overrides
    assert any("not found" in rec.message for rec in caplog.records)


def test_orb_priority_file_over_inline(monkeypatch, tmp_path):
    """External file should take priority over inline JSON."""
    orb_file = tmp_path / "orb_file.json"
    orb_file.write_text(json.dumps({"mars-ketu": 3.0}))

    monkeypatch.setenv("ORB_OVERRIDES_FILE", str(orb_file))
    monkeypatch.setenv("ORB_OVERRIDES", '{"mars-ketu": 9.0}')

    importlib.reload(config)
    s = config.settings

    # File should override inline value
    assert s.orb_overrides["mars-ketu"] == 3.0
