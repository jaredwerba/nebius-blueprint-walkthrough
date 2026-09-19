"""Sentinel — compact regulatory compliance auditor (Blueprint case study).

Official Sentinel uses Pinecone, LangGraph, Jira, and 200 SOPs.
This module keeps the same pipeline:

  regulation change -> match SOPs -> classify gap -> file a ticket stub.

Pinecone is a local token-overlap index. Jira is a JSONL ticket log.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.env import load_env
from shared.token_factory import TokenFactoryClient

load_env()

ROOT = Path(__file__).resolve().parent
SOP_DIR = ROOT / "data" / "sops"
TICKET_LOG = ROOT / "data" / "tickets.jsonl"


@dataclass
class Finding:
    sop_id: str
    sop_title: str
    framework: str
    severity: str
    gap: str
    ticket_id: str


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def load_sops() -> list[dict]:
    sops = []
    for path in sorted(SOP_DIR.glob("*.md")):
        text = path.read_text()
        title = text.splitlines()[0].lstrip("# ").strip() if text else path.stem
        sops.append({"id": path.stem, "title": title, "text": text, "path": str(path)})
    return sops


def score(query: str, doc: str) -> float:
    q = set(tokenize(query))
    d = set(tokenize(doc))
    if not q or not d:
        return 0.0
    return len(q & d) / len(q | d)


def match_sops(change: str, top_k: int = 3) -> list[dict]:
    ranked = sorted(load_sops(), key=lambda s: score(change, s["text"]), reverse=True)
    return [s for s in ranked[:top_k] if score(change, s["text"]) > 0]


def classify(change: str, sop: dict, client: TokenFactoryClient | None = None) -> Finding:
    if client is None:
        text = (change + " " + sop["text"]).lower()
        severity = "high" if "phi" in text or "gdpr" in text else "medium"
        framework = "HIPAA" if "phi" in text or "hipaa" in text else "SOC2"
        gap = f"{sop['id']} may not cover: {change[:120]}"
        return Finding(sop["id"], sop["title"], framework, severity, gap, "")

    prompt = (
        "You are a compliance auditor. Reply as JSON with keys "
        "framework, severity (low|medium|high), gap. "
        f"Regulatory change: {change}\nSOP {sop['id']}: {sop['text'][:1500]}"
    )
    raw = client.chat(
        [
            {"role": "system", "content": "Return JSON only."},
            {"role": "user", "content": prompt},
        ]
    )
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        data = json.loads(raw[start:end])
    except json.JSONDecodeError:
        data = {"framework": "UNKNOWN", "severity": "medium", "gap": raw[:240]}
    return Finding(
        sop["id"],
        sop["title"],
        str(data.get("framework", "UNKNOWN")),
        str(data.get("severity", "medium")),
        str(data.get("gap", "")),
        "",
    )


def file_ticket(finding: Finding) -> Finding:
    TICKET_LOG.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    if TICKET_LOG.exists():
        n = sum(1 for _ in TICKET_LOG.open())
    finding.ticket_id = f"SEN-{n + 1:04d}"
    with TICKET_LOG.open("a") as fh:
        fh.write(json.dumps(asdict(finding)) + "\n")
    return finding


def audit(change: str, live: bool = False) -> list[Finding]:
    client = None
    if live:
        probe = TokenFactoryClient()
        if probe.api_key:
            client = probe
    findings = []
    for sop in match_sops(change):
        findings.append(file_ticket(classify(change, sop, client=client)))
    return findings


if __name__ == "__main__":
    change = "New HIPAA guidance requires encryption of PHI at rest in all regions."
    if len(sys.argv) > 1:
        change = " ".join(sys.argv[1:])
    for item in audit(change, live=False):
        print(asdict(item))
