"""Sentinel — compact regulatory compliance auditor (Blueprint case study).

Official Sentinel uses Pinecone, LangGraph, Jira, and 200 SOPs.
This module keeps the same pipeline:

  regulation change -> match article -> match SOPs -> classify gap -> file a ticket stub.

Pinecone is a local token-overlap index. Jira is a JSONL ticket log.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.env import load_env
from shared.token_factory import TokenFactoryClient

load_env()

ROOT = Path(__file__).resolve().parent
SOP_DIR = ROOT / "data" / "sops"
REG_DIR = ROOT / "data" / "regulations"
TICKET_LOG = ROOT / "data" / "tickets.jsonl"


@dataclass
class Citation:
    source_id: str
    source_type: str
    snippet: str


@dataclass
class Finding:
    sop_id: str
    sop_title: str
    framework: str
    severity: str
    gap: str
    ticket_id: str
    citations: list[Citation] = field(default_factory=list)


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def load_markdown_dir(directory: Path) -> list[dict]:
    items = []
    for path in sorted(directory.glob("*.md")):
        text = path.read_text()
        title = text.splitlines()[0].lstrip("# ").strip() if text else path.stem
        items.append({"id": path.stem, "title": title, "text": text, "path": str(path)})
    return items


def load_sops() -> list[dict]:
    return load_markdown_dir(SOP_DIR)


def load_regulations() -> list[dict]:
    return load_markdown_dir(REG_DIR)


def score(query: str, doc: str) -> float:
    q = set(tokenize(query))
    d = set(tokenize(doc))
    if not q or not d:
        return 0.0
    return len(q & d) / len(q | d)


def overlap_snippet(query: str, doc: str, limit: int = 160) -> str:
    shared = set(tokenize(query)) & set(tokenize(doc))
    if not shared:
        return doc[:limit]
    return " ".join(sorted(shared))[:limit]


def match_ranked(query: str, docs: list[dict], top_k: int = 3) -> list[dict]:
    ranked = sorted(docs, key=lambda s: score(query, s["text"]), reverse=True)
    out = []
    for item in ranked[:top_k]:
        s = score(query, item["text"])
        if s > 0:
            row = dict(item)
            row["score"] = s
            out.append(row)
    return out


def match_regulations(change: str, top_k: int = 2) -> list[dict]:
    return match_ranked(change, load_regulations(), top_k=top_k)


def match_sops(change: str, top_k: int = 3) -> list[dict]:
    return match_ranked(change, load_sops(), top_k=top_k)


def infer_framework(text: str) -> str:
    t = text.lower()
    if "gdpr" in t or "erasure" in t or "data-subject" in t or "data subject" in t:
        return "GDPR"
    if "ai act" in t or "high-risk" in t:
        return "EU_AI_ACT"
    if "nist" in t or "bias" in t:
        return "NIST_AI_RMF"
    if "phi" in t or "hipaa" in t or "baa" in t:
        return "HIPAA"
    return "SOC2"


def infer_severity(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ("phi", "gdpr", "erasure", "high-risk")):
        return "high"
    if any(k in t for k in ("encrypt", "logging", "bias")):
        return "medium"
    return "low"


def classify(change: str, sop: dict, regs: list[dict], client: TokenFactoryClient | None = None) -> Finding:
    citations = [
        Citation(sop["id"], "sop", overlap_snippet(change, sop["text"])),
    ]
    for reg in regs:
        citations.append(Citation(reg["id"], "regulation", overlap_snippet(change, reg["text"])))

    if client is None:
        blob = change + " " + sop["text"] + " " + " ".join(r["text"] for r in regs)
        return Finding(
            sop["id"],
            sop["title"],
            infer_framework(blob),
            infer_severity(blob),
            f"{sop['id']} may not cover: {change[:120]}",
            "",
            citations,
        )

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
        citations,
    )


def file_ticket(finding: Finding) -> Finding:
    TICKET_LOG.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    if TICKET_LOG.exists():
        n = sum(1 for _ in TICKET_LOG.open())
    finding.ticket_id = f"SEN-{n + 1:04d}"
    payload = asdict(finding)
    with TICKET_LOG.open("a") as fh:
        fh.write(json.dumps(payload) + "\n")
    return finding


def audit(change: str, live: bool = False) -> list[Finding]:
    client = None
    if live:
        probe = TokenFactoryClient()
        if probe.api_key:
            client = probe
    regs = match_regulations(change)
    findings = []
    query = change + " " + " ".join(r["text"] for r in regs)
    for sop in match_sops(query):
        findings.append(file_ticket(classify(change, sop, regs, client=client)))
    return findings


if __name__ == "__main__":
    change = "New HIPAA guidance requires encryption of PHI at rest in all regions."
    if len(sys.argv) > 1:
        change = " ".join(sys.argv[1:])
    for item in audit(change, live=False):
        print(asdict(item))
