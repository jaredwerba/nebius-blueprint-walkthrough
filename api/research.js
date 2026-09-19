function subquestions(q) {
  const question = q || "What is Nebius Token Factory?";
  return [question, `Who operates ${question.slice(0, 80)}`, `Sources for ${question.slice(0, 80)}`];
}

export default async function handler(req, res) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ error: "POST only" });
  }
  const question =
    typeof req.body?.question === "string" && req.body.question.trim()
      ? req.body.question.trim().slice(0, 500)
      : "What is Nebius Token Factory?";
  const tavily = process.env.TAVILY_API_KEY;
  const subs = subquestions(question);
  const sources = [];
  if (tavily) {
    for (const sub of subs) {
      const search = await fetch("https://api.tavily.com/search", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ api_key: tavily, query: sub, max_results: 3 }),
      });
      if (search.ok) {
        const data = await search.json();
        for (const item of data.results || []) {
          sources.push({
            title: item.title,
            url: item.url,
            snippet: (item.content || "").slice(0, 160),
            sub,
          });
        }
      }
    }
  } else {
    sources.push({
      title: "Offline fixture: Token Factory docs",
      url: "https://docs.tokenfactory.nebius.com",
      snippet: "OpenAI-compatible inference API for open models.",
      sub: question,
    });
  }
  const seen = new Set();
  const unique = [];
  for (const s of sources) {
    if (!s.url || seen.has(s.url)) continue;
    seen.add(s.url);
    unique.push(s);
  }
  return res.status(200).json({
    question,
    subquestions: subs,
    sources: unique,
    note: tavily ? "Live Tavily used" : "Live Tavily was not used",
  });
}
