import pytest
from datetime import datetime
from decimal import Decimal
from app.core.rules.engine.rules_engine_impl import RulesEngineImpl
from app.core.rules.relations import registry
from app.core.db.enums import Relation
from app.core.db.models import Condition, Outcome

from app.core.astro.factories.provider_factory import get_provider


# -----------------------------------------------------------------------------
# 🪐 FIXTURE: Fresh provider set per test
# -----------------------------------------------------------------------------
@pytest.fixture(scope="function")
def providers():
    """
    Return a fresh set of initialized providers (stub, skyfield, swisseph).

    ✅ Each test gets clean, isolated provider instances.
    This prevents subtle global drift in ayanamsa configuration or
    cached ephemerides between test modules — ensuring deterministic
    results across pytest runs and environments.
    """
    return {
        "stub": get_provider("stub"),
        "skyfield": get_provider("skyfield"),
        "swisseph": get_provider("swisseph"),
    }


@pytest.fixture(scope="function")
def when():
    """Fixed test date for cross-provider evaluations."""
    return datetime(2025, 1, 1, 0, 0)


# -----------------------------------------------------------------------------
# 🧩 Helper: Make rule with one or more conditions
# -----------------------------------------------------------------------------
def make_rule(conds):
    """Utility to wrap one or more conditions into a rule-like object."""
    class FakeRule:
        def __init__(self, conditions):
            self.id = 1
            self.rule_id = 1
            self.enabled = True
            self.confidence = 0.9
            self.conditions = conditions
            self.outcomes = [
                Outcome(id=1, rule_id=1, sector_code="EQUITY", effect="Bullish", weight=0.7),
            ]
    return FakeRule(conds)


# -----------------------------------------------------------------------------
# 🔭 TEST: Cross-provider consistency for major relation types
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("relation,planet,target,value", [
    (Relation.in_sign, "sun", "aries", None),
    (Relation.trine_with, "moon", "mars", None),
    (Relation.in_house_relative_to, "venus", "sun", "7"),
    (Relation.combust_by_sun, "mercury", None, None),
    (Relation.is_retrograde, "saturn", None, None),
])
def test_cross_provider_consistency(providers, when, relation, planet, target, value):
    """
    Verify that all real (astronomical) providers produce consistent results
    for a representative set of relations.

    - SkyfieldProvider → NASA JPL DE440 data, Lahiri sidereal mode.
    - SwissEphemProvider → Swiss Ephemeris, Lahiri mode.
    - StubProvider → synthetic deterministic values (excluded from strict checks).
    """
    results = {}

    cond = Condition(
        id=1, rule_id=1,
        planet=planet, relation=relation,
        target=target, value=value
    )
    rule = make_rule([cond])

    for name, prov in providers.items():
        engine = RulesEngineImpl(prov)
        res = engine.evaluate_rule(rule, when)
        results[name] = bool(res)

    # Only compare astronomical (real) providers
    real_results = {k: v for k, v in results.items() if k != "stub"}
    all_values = set(real_results.values())

    assert len(all_values) == 1, f"Inconsistent results across real providers: {real_results}"
    print(f"[{relation.value}] results: {results}")


# -----------------------------------------------------------------------------
# 🌞 TEST: Longitude cross-verification
# -----------------------------------------------------------------------------
def test_longitude_consistency(providers, when):
    """
    Compare raw longitudes across real ephemeris-based providers
    for a few representative planets.

    ⚙️ Ensures sidereal consistency between SwissEphem and Skyfield.
    StubProvider is excluded since it uses fixed dummy data.

    ✅ Reinitializes providers per test, guaranteeing deterministic ayanamsa.
    ✅ Fails only if >1° divergence, which would indicate config mismatch.
    """
    planets = ["sun", "moon", "venus", "mars"]
    tolerance = 1.0  # relaxed slightly for Raman→Lahiri drift safety

    # Force both providers to Lahiri and reload ephemerides if supported
    for name, prov in providers.items():
        if hasattr(prov, "ayanamsa_mode"):
            prov.ayanamsa_mode = "lahiri"
            if hasattr(prov, "reload"):
                try:
                    prov.reload()  # ensure reinit if the provider caches ephemerides
                except Exception:
                    pass

    # Regenerate fresh provider instances to ensure no global state contamination
    from app.core.astro.factories.provider_factory import get_provider
    sky = get_provider("skyfield",fresh=True)
    swe = get_provider("swisseph",fresh=True)

    for planet in planets:
        lon_sky = sky.longitude(planet, when)
        lon_swe = swe.longitude(planet, when)
        diff = abs((lon_sky - lon_swe + 180) % 360 - 180)
        assert diff < tolerance, f"{planet} mismatch {diff:.3f}°"

# -----------------------------------------------------------------------------
# 🌀 TEST: Missing retrograde method behavior
# -----------------------------------------------------------------------------
def test_provider_missing_is_retrograde(providers, when):
    """
    Simulate a provider missing the `is_retrograde()` method entirely.
    Engine should fail gracefully and return no events.
    """
    stub = providers["stub"]

    # Proxy provider without retrograde function
    class NoRetrograde:
        def longitude(self, *args, **kwargs):
            return stub.longitude(*args, **kwargs)

    cond = Condition(id=1, rule_id=1, planet="saturn", relation=Relation.is_retrograde)
    rule = make_rule([cond])

    engine = RulesEngineImpl(NoRetrograde())
    result = engine.evaluate_rule(rule, when)
    assert result == [], "Engine should handle missing is_retrograde() gracefully."


# -----------------------------------------------------------------------------
# 🔗 TEST: Multi-condition rule behavior
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("passes_expected", [True, False])
def test_multiple_conditions_behavior(providers, when, passes_expected, monkeypatch):
    """
    Rule with multiple conditions:
      ✅ If all pass → event generated.
      ❌ If one fails → event skipped.

    Uses StubProvider for deterministic evaluation.
    """
    stub = providers["stub"]

    conds = [
        Condition(id=1, rule_id=2, planet="sun",
                      relation=Relation.in_sign, target="pisces"),
        Condition(id=2, rule_id=2, planet="moon",
                      relation=Relation.in_house_relative_to, target="sun", value="7"),
    ]

    if not passes_expected:
        orig_get = registry.get_relation_handler
        def fake_get(rel):
            handler = orig_get(rel)
            if rel == Relation.in_sign:
                handler.check = lambda *a, **k: False
            return handler
        monkeypatch.setattr(registry, "get_relation_handler", fake_get)

    rule = make_rule(conds)
    engine = RulesEngineImpl(stub)
    result = engine.evaluate_rule(rule, when)

    if passes_expected:
        assert result, "All passing conditions should yield event"
    else:
        assert not result, "Partial failure should skip event generation"


# -----------------------------------------------------------------------------
# 🧭 TEST: Provider recovery after transient failure
# -----------------------------------------------------------------------------
def test_provider_recovers_after_failure(providers, when, monkeypatch):
    """
    Simulate transient provider error (e.g., network/IO glitch) and
    ensure the RulesEngine recovers on subsequent evaluations.
    """
    stub = providers["stub"]
    engine = RulesEngineImpl(stub)

    def bad_longitude(*_, **__):
        raise KeyError("temporary glitch")

    monkeypatch.setattr(stub, "longitude", bad_longitude)
    cond = Condition(id=1, rule_id=5,
                         planet="sun", relation=Relation.in_sign, target="pisces")
    rule = make_rule([cond])

    assert engine.evaluate_rule(rule, when) == [], "Failure should yield empty event list"

    # Restore provider and verify successful recovery
    monkeypatch.undo()
    result = engine.evaluate_rule(rule, when)
    assert result, "Engine should recover after transient provider exception"


# -----------------------------------------------------------------------------
# 🌍 FINAL FIXTURE: Ephemeris delta summary (Skyfield vs SwissEphem)
# -----------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def ephemeris_summary(request):
    """
    After all tests complete, print a concise delta comparison
    between Skyfield and SwissEphem for all major planets.

    Helps detect small drifts across library updates or
    environment differences.
    """
    from app.core.astro.factories.provider_factory import get_provider

    yield  # Run tests first

    sky = get_provider("skyfield")
    swe = get_provider("swisseph")
    when = datetime(2025, 1, 1, 0, 0)
    planets = ["sun", "moon", "mercury", "venus", "mars",
               "jupiter", "saturn", "uranus", "neptune"]

    print("\n\n🪐 Ephemeris Comparison Summary (Skyfield vs SwissEphem) — 2025-01-01")
    print("-------------------------------------------------------------")
    print(f"{'Planet':<10} {'Skyfield(°)':>14} {'SwissEph(°)':>14} {'Δ°':>8}")
    print("-------------------------------------------------------------")

    for p in planets:
        try:
            s1 = sky.longitude(p, when)
            s2 = swe.longitude(p, when)
            delta = abs((s1 - s2 + 180) % 360 - 180)
            print(f"{p:<10} {s1:14.6f} {s2:14.6f} {delta:8.4f}")
        except Exception as e:
            print(f"{p:<10} [Error: {e}]")

    print("-------------------------------------------------------------\n")
