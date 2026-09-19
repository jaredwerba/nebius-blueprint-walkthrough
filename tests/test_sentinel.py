def _load(name, rel):
    import importlib.util
    import sys
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / rel
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_sentinel_matches_phi_sop():
    mod = _load("sentinel", "blueprints/sentinel/app.py")
    change = "HIPAA requires encryption of PHI at rest"
    hits = mod.match_sops(change)
    ids = {h["id"] for h in hits}
    assert "sop-002-phi" in ids or "sop-009-encryption" in ids
    regs = mod.match_regulations(change)
    assert any("hipaa" in r["id"] for r in regs)
    findings = mod.audit(change, live=False)
    assert findings
    assert findings[0].ticket_id.startswith("SEN-")
    assert findings[0].severity in {"low", "medium", "high"}
    assert findings[0].citations
    assert len(mod.load_sops()) >= 12


def test_sentinel_gdpr_erasure():
    mod = _load("sentinel_gdpr", "blueprints/sentinel/app.py")
    findings = mod.audit("GDPR right to erasure for data-subject requests", live=False)
    assert findings
    assert findings[0].framework in {"GDPR", "SOC2"}


def test_deep_research_offline():
    mod = _load("deep_research", "blueprints/deep-research/app.py")
    report = mod.research("What is Token Factory?", live=False)
    assert len(report.subquestions) == 3
    assert report.sources
    assert report.sources[0]["url"].startswith("https://")
    assert "Citations:" in report.answer


def test_cost_benchmark_picks_cheapest_correct():
    mod = _load("cost_bench", "blueprints/cost-benchmark/app.py")
    result = mod.benchmark("Name Token Factory", "Token Factory", mod.FIXTURE)
    assert result["cheapest_correct"] == "meta-llama/Llama-3.3-70B-Instruct"
    assert len(result["runs"]) == 3
    glm = next(r for r in result["runs"] if r["model"].startswith("zai-org"))
    assert glm["correct"] is False
