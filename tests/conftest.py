import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "cookbooks" / "01-first-agent"))
sys.path.insert(0, str(ROOT / "cookbooks" / "02-knowledge-pinecone"))
sys.path.insert(0, str(ROOT / "cookbooks" / "03-grounding-tavily"))
sys.path.insert(0, str(ROOT / "cookbooks" / "04-orchestration-langgraph"))
sys.path.insert(0, str(ROOT / "cookbooks" / "05-thread-memory"))
sys.path.insert(0, str(ROOT / "cookbooks" / "06-user-memory-postgres"))
sys.path.insert(0, str(ROOT / "cookbooks" / "07-observability-langsmith"))
sys.path.insert(0, str(ROOT / "cookbooks" / "08-guardrails"))
sys.path.insert(0, str(ROOT / "cookbooks" / "09-actions-mcp-stripe"))
sys.path.insert(0, str(ROOT / "cookbooks" / "10-simulation-snowglobe"))
