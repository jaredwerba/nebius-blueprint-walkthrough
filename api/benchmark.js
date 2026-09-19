const PRICES = {
  "MiniMaxAI/MiniMax-M3": [0.3, 1.2],
  "meta-llama/Llama-3.3-70B-Instruct": [0.13, 0.4],
  "zai-org/GLM-5.2": [1.4, 4.4],
};

const FIXTURE = [
  {
    model: "MiniMaxAI/MiniMax-M3",
    prompt_tokens: 120,
    completion_tokens: 80,
    latency_ms: 900,
    answer: "Token Factory is an OpenAI-compatible inference API for open models.",
  },
  {
    model: "meta-llama/Llama-3.3-70B-Instruct",
    prompt_tokens: 120,
    completion_tokens: 60,
    latency_ms: 700,
    answer: "Nebius Token Factory serves open models.",
  },
  {
    model: "zai-org/GLM-5.2",
    prompt_tokens: 120,
    completion_tokens: 90,
    latency_ms: 1100,
    answer: "I do not know.",
  },
];

function usd(model, p, c) {
  const [inp, out] = PRICES[model] || [1, 1];
  return (p * inp + c * out) / 1_000_000;
}

export default async function handler(req, res) {
  if (req.method !== "GET" && req.method !== "POST") {
    res.setHeader("Allow", "GET, POST");
    return res.status(405).json({ error: "GET or POST" });
  }
  const expected = "Token Factory";
  const runs = FIXTURE.map((row) => ({
    model: row.model,
    prompt_tokens: row.prompt_tokens,
    completion_tokens: row.completion_tokens,
    latency_ms: row.latency_ms,
    correct: row.answer.toLowerCase().includes(expected.toLowerCase()),
    usd: Number(usd(row.model, row.prompt_tokens, row.completion_tokens).toFixed(6)),
  }));
  const cheapest = runs.filter((r) => r.correct).sort((a, b) => a.usd - b.usd)[0];
  return res.status(200).json({
    task: "Name Token Factory in one sentence",
    note: "Recorded runs. Not a live Token Factory sweep.",
    runs,
    cheapest_correct: cheapest ? cheapest.model : null,
  });
}
