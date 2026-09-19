const SOPS = [
  {
    id: "sop-001-access",
    title: "Access control",
    text: "Employees receive accounts. No encryption of PHI at rest. No GDPR data-subject requests.",
  },
  {
    id: "sop-002-phi",
    title: "PHI handling",
    text: "PHI in transit uses TLS. Does not require encryption of PHI at rest in every region. HIPAA is in scope.",
  },
  {
    id: "sop-003-vendor",
    title: "Vendor onboarding",
    text: "Vendors must sign a SOC 2 report review. No DPA for GDPR processors.",
  },
  {
    id: "sop-004-incident",
    title: "Incident response",
    text: "Incidents are logged in Jira. EU AI Act logging of high-risk systems is not described.",
  },
  {
    id: "sop-005-model",
    title: "Model deployment",
    text: "Models go to production after peer review. No NIST AI RMF measure or manage mapping.",
  },
  {
    id: "sop-006-retention",
    title: "Data retention",
    text: "Records stay 7 years. GDPR storage limitation is not mapped.",
  },
  {
    id: "sop-009-encryption",
    title: "Encryption",
    text: "TLS 1.2 in transit. PHI at rest encryption is optional. HIPAA.",
  },
  {
    id: "sop-010-dsar",
    title: "Data subject requests",
    text: "No GDPR access, rectification, or erasure SLA.",
  },
];

function tokenize(text) {
  return (text.toLowerCase().match(/[a-z0-9]+/g) || []);
}

function score(query, doc) {
  const q = new Set(tokenize(query));
  const d = new Set(tokenize(doc));
  if (!q.size || !d.size) return 0;
  let inter = 0;
  for (const t of q) if (d.has(t)) inter += 1;
  return inter / new Set([...q, ...d]).size;
}

function matchSops(change, topK = 3) {
  return SOPS.map((s) => ({ ...s, score: score(change, s.text) }))
    .filter((s) => s.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, topK);
}

export default async function handler(req, res) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ error: "POST only" });
  }
  const change =
    typeof req.body?.change === "string" && req.body.change.trim()
      ? req.body.change.trim().slice(0, 500)
      : "New HIPAA guidance requires encryption of PHI at rest in all regions.";

  const matches = matchSops(change);
  const key = process.env.NEBIUS_API_KEY;
  const findings = [];

  for (const sop of matches) {
    let finding = {
      sop_id: sop.id,
      sop_title: sop.title,
      framework: /phi|hipaa/i.test(change + sop.text) ? "HIPAA" : "SOC2",
      severity: /phi|gdpr/i.test(change + sop.text) ? "high" : "medium",
      gap: `${sop.id} may not cover: ${change.slice(0, 120)}`,
      ticket_id: `SEN-${String(findings.length + 1).padStart(4, "0")}`,
    };
    if (key) {
      const base =
        process.env.NEBIUS_BASE_URL || "https://api.tokenfactory.nebius.com/v1";
      const model = process.env.NEBIUS_MODEL || "MiniMaxAI/MiniMax-M3";
      const completion = await fetch(`${base.replace(/\/$/, "")}/chat/completions`, {
        method: "POST",
        headers: {
          authorization: `Bearer ${key}`,
          "content-type": "application/json",
        },
        body: JSON.stringify({
          model,
          temperature: 0,
          messages: [
            { role: "system", content: "Return JSON only with keys framework, severity, gap." },
            {
              role: "user",
              content: `Regulatory change: ${change}\nSOP ${sop.id}: ${sop.text}`,
            },
          ],
        }),
      });
      if (completion.ok) {
        const payload = await completion.json();
        const raw = payload?.choices?.[0]?.message?.content || "";
        const start = raw.indexOf("{");
        const end = raw.lastIndexOf("}") + 1;
        try {
          const data = JSON.parse(raw.slice(start, end));
          finding = {
            ...finding,
            framework: String(data.framework || finding.framework),
            severity: String(data.severity || finding.severity),
            gap: String(data.gap || finding.gap),
          };
        } catch {
          finding.gap = raw.slice(0, 240) || finding.gap;
        }
      }
    }
    findings.push(finding);
  }

  return res.status(200).json({
    change,
    note: "Jira is a stub. Pinecone is a local overlap index over 5 sample SOPs.",
    findings,
  });
}
