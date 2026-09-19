export default async function handler(req, res) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ error: "POST only" });
  }

  const key = process.env.NEBIUS_API_KEY;
  const tavily = process.env.TAVILY_API_KEY;
  if (!key) {
    return res.status(500).json({ error: "NEBIUS_API_KEY is not set on Vercel" });
  }

  const question =
    typeof req.body?.question === "string" && req.body.question.trim()
      ? req.body.question.trim().slice(0, 500)
      : "What is Nebius Token Factory?";

  let sources = [];
  if (tavily) {
    const search = await fetch("https://api.tavily.com/search", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        api_key: tavily,
        query: question,
        max_results: 5,
      }),
    });
    if (search.ok) {
      const data = await search.json();
      sources = (data.results || []).map((item) => ({
        title: item.title,
        url: item.url,
        snippet: (item.content || "").slice(0, 240),
      }));
    }
  }

  const sourceBlock = sources
    .map((s) => `- ${s.title} (${s.url}): ${s.snippet}`)
    .join("\n");

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
      temperature: 0.2,
      messages: [
        {
          role: "system",
          content:
            "Answer in short sentences. Use only the provided sources. Cite URLs. If sources are empty, say you lack live grounding.",
        },
        {
          role: "user",
          content: `Question: ${question}\nSources:\n${sourceBlock || "(none)"}`,
        },
      ],
    }),
  });

  if (!completion.ok) {
    const text = await completion.text();
    return res.status(502).json({
      error: "Token Factory request failed",
      status: completion.status,
      detail: text.slice(0, 400),
    });
  }

  const payload = await completion.json();
  const answer = payload?.choices?.[0]?.message?.content || "";
  return res.status(200).json({ question, answer, sources });
}
