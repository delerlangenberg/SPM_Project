import json


class _FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_academic_ai_api_call_is_advisory_only(monkeypatch):
    from core.ai import academic_ai_client

    captured = {}

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["timeout"] = timeout
        captured["body"] = json.loads(req.data.decode("utf-8"))
        captured["client_id"] = req.headers["X-client-id"]
        captured["client_secret"] = req.headers["X-client-secret"]
        return _FakeResponse(
            {
                "data": {
                    "content": json.dumps(
                        {
                            "recommendation": ["Review Z approach telemetry before motion."],
                            "risk": "medium",
                            "target_phase": "2.3",
                            "reasoning": "Telemetry must be verified before live motion.",
                        }
                    ),
                    "usage": {"totalTokens": 88},
                }
            }
        )

    monkeypatch.setenv("ACADEMIC_AI_BASE_URL", "https://academic-ai.example/v1/advice")
    monkeypatch.setenv("ACADEMIC_AI_CHAT_ENDPOINT", "/api/v1/llm/chat")
    monkeypatch.setenv("ACADEMIC_AI_CLIENT_ID", "client-test-id")
    monkeypatch.setenv("ACADEMIC_AI_CLIENT_SECRET", "secret-test-key")
    monkeypatch.setenv("ACADEMIC_AI_MODEL", "academic-spm-advisor")
    monkeypatch.setenv("ACADEMIC_AI_TIMEOUT_SECONDS", "3")
    monkeypatch.setenv("ACADEMIC_AI_DISABLE_LOCAL_FILE", "1")
    monkeypatch.setattr(academic_ai_client.request, "urlopen", fake_urlopen)

    payload = academic_ai_client.build_ai_recommendation(
        "measurement planning",
        context={"phase": "2.3", "surface": "bravais_lattice"},
    )

    assert payload["api_configured"] is True
    assert payload["execution_allowed"] is False
    assert payload["role"] == "advisory_only"
    assert payload["recommendation"] == ["Review Z approach telemetry before motion."]
    assert payload["ai_api_response"]["usage"]["totalTokens"] == 88
    assert captured["url"] == "https://academic-ai.example/v1/advice/api/v1/llm/chat"
    assert captured["timeout"] == 3
    assert captured["client_id"] == "client-test-id"
    assert captured["client_secret"] == "secret-test-key"
    assert captured["body"]["model"] == "academic-spm-advisor"
    assert captured["body"]["maxTokens"] == 700
    assert captured["body"]["messages"][0]["role"] == "user"
    assert "senior SPM instrumentation engineer" in captured["body"]["messages"][0]["content"]
    embedded_json = captured["body"]["messages"][0]["content"].split("SPM request payload:", 1)[1].strip()
    user_payload = json.loads(embedded_json)
    assert user_payload["execution_allowed"] is False
    assert user_payload["context"]["surface"] == "bravais_lattice"


def test_academic_ai_default_model_tracks_newest_project_model(monkeypatch):
    from core.ai import academic_ai_client

    monkeypatch.setenv("ACADEMIC_AI_DISABLE_LOCAL_FILE", "1")
    monkeypatch.setenv("ACADEMIC_AI_CLIENT_ID", "client-test-id")
    monkeypatch.setenv("ACADEMIC_AI_CLIENT_SECRET", "secret-test-key")
    monkeypatch.delenv("ACADEMIC_AI_MODEL", raising=False)

    assert academic_ai_client._academic_ai_config().model == "GPT-5.2"


def test_academic_ai_api_failure_keeps_local_safety(monkeypatch):
    from core.ai import academic_ai_client

    def fake_urlopen(_req, timeout=None):
        assert timeout is not None
        raise OSError("offline")

    monkeypatch.setenv("ACADEMIC_AI_BASE_URL", "https://academic-ai.example")
    monkeypatch.setenv("ACADEMIC_AI_CLIENT_ID", "client-test-id")
    monkeypatch.setenv("ACADEMIC_AI_CLIENT_SECRET", "secret-test-key")
    monkeypatch.setenv("ACADEMIC_AI_MODEL", "academic-spm-advisor")
    monkeypatch.setenv("ACADEMIC_AI_DISABLE_LOCAL_FILE", "1")
    monkeypatch.setattr(academic_ai_client.request, "urlopen", fake_urlopen)

    payload = academic_ai_client.build_ai_recommendation("approach", context={})

    assert payload["api_configured"] is True
    assert payload["execution_allowed"] is False
    assert payload["risk"] == "medium"
    assert "ai_api_error" in payload
    assert "Do not execute motion" in " ".join(payload["recommendation"])


def test_local_open_source_ai_provider_uses_openai_compatible_endpoint(monkeypatch):
    from core.ai import academic_ai_client

    captured = {}

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["timeout"] = timeout
        captured["body"] = json.loads(req.data.decode("utf-8"))
        return _FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "recommendation": [
                                        "Compare expected raster path with measured contact-Z map.",
                                        "Use the feature detector only as advisory output.",
                                    ],
                                    "risk": "medium",
                                    "target_phase": "2.3",
                                    "reasoning": "Scan interpretation must not bypass motion gates.",
                                }
                            )
                        }
                    }
                ],
                "usage": {"total_tokens": 99},
            }
        )

    monkeypatch.setenv("SPM_AI_PROVIDER", "local")
    monkeypatch.setenv("SPM_LOCAL_AI_BASE_URL", "http://127.0.0.1:11434/v1")
    monkeypatch.setenv("SPM_LOCAL_AI_CHAT_ENDPOINT", "/chat/completions")
    monkeypatch.setenv("SPM_LOCAL_AI_MODEL", "qwen3-coder-next")
    monkeypatch.setenv("SPM_LOCAL_AI_TIMEOUT_SECONDS", "4")
    monkeypatch.setenv("ACADEMIC_AI_DISABLE_LOCAL_FILE", "1")
    monkeypatch.setattr(academic_ai_client.request, "urlopen", fake_urlopen)

    payload = academic_ai_client.build_ai_recommendation(
        "feature detection and autoapproach logic",
        context={"scan_mode": "foil_tap", "feature": "edge"},
    )

    assert payload["ai_provider"] == "local"
    assert payload["ai_mode"] == "local_open_source"
    assert payload["execution_allowed"] is False
    assert "Compare expected raster path" in payload["recommendation"][0]
    assert payload["local_ai_status"]["model"] == "qwen3-coder-next"
    assert captured["url"] == "http://127.0.0.1:11434/v1/chat/completions"
    assert captured["timeout"] == 4
    assert captured["body"]["model"] == "qwen3-coder-next"
    assert captured["body"]["stream"] is False
    assert "never executes motion" in captured["body"]["messages"][0]["content"]
    assert captured["body"]["messages"][1]["role"] == "user"


def test_local_open_source_ai_failure_is_safe(monkeypatch):
    from core.ai import academic_ai_client

    def fake_urlopen(_req, timeout=None):
        assert timeout is not None
        raise OSError("ollama offline")

    monkeypatch.setenv("SPM_AI_PROVIDER", "local")
    monkeypatch.setenv("SPM_LOCAL_AI_MODEL", "qwen3-coder-next")
    monkeypatch.setenv("ACADEMIC_AI_DISABLE_LOCAL_FILE", "1")
    monkeypatch.setattr(academic_ai_client.request, "urlopen", fake_urlopen)

    payload = academic_ai_client.build_ai_recommendation("scan logic", context={})

    assert payload["ai_provider"] == "local"
    assert payload["execution_allowed"] is False
    assert "ai_api_error" in payload
    assert "Local open-source AI is not reachable" in " ".join(payload["recommendation"])
