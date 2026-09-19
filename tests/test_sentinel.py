def test_sentinel_matches_phi_sop():
    import importlib.util
    import sys
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "blueprints/sentinel/app.py"
    spec = importlib.util.spec_from_file_location("sentinel", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["sentinel"] = mod
    spec.loader.exec_module(mod)
    change = "HIPAA requires encryption of PHI at rest"
    hits = mod.match_sops(change)
    ids = {h["id"] for h in hits}
    assert "sop-002-phi" in ids
    findings = mod.audit(change, live=False)
    assert findings
    assert findings[0].ticket_id.startswith("SEN-")
    assert findings[0].severity in {"low", "medium", "high"}
