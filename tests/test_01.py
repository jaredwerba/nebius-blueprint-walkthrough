from shared.token_factory import TokenFactoryClient, TokenFactoryError


class FakeClient(TokenFactoryClient):
    def __init__(self) -> None:
        super().__init__(api_key="test", base_url="http://example.invalid", model="fake")

    def chat(self, messages, temperature=0.2) -> str:
        return f"echo:{messages[-1]['content']}"


def test_first_agent_uses_injected_client():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "cookbooks/01-first-agent/app.py"
    spec = importlib.util.spec_from_file_location("agent01", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert "echo:hi" == mod.run_agent("hi", client=FakeClient())


def test_missing_key_raises():
    client = TokenFactoryClient(api_key="")
    try:
        client._headers()
        raise AssertionError("expected error")
    except TokenFactoryError:
        pass
