"""Local-only LLM advisory layer for the SPM Prusa project.

The LLM may explain, diagnose, and recommend. It must never execute machine
motion or bypass deterministic safety gates.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any
from urllib import error, request


DEFAULT_LOCAL_AI_BASE_URL = "http://127.0.0.1:11434/v1"
DEFAULT_LOCAL_AI_MODEL = "qwen3-coder-next"
SAFETY_RULE = (
    "The local LLM may recommend and explain, but cannot execute machine "
    "motion directly or bypass deterministic safety gates."
)


@dataclass(frozen=True)
class LocalOpenAIConfig:
    base_url: str
    endpoint: str
    model: str
    timeout_s: float
    provider: str


def _local_openai_config() -> LocalOpenAIConfig:
    base_url = os.getenv("SPM_LOCAL_AI_BASE_URL", DEFAULT_LOCAL_AI_BASE_URL).strip().rstrip("/")
    endpoint = os.getenv("SPM_LOCAL_AI_CHAT_ENDPOINT", "/chat/completions").strip()
    if not endpoint.startswith("/"):
        endpoint = f"/{endpoint}"
    model = os.getenv("SPM_LOCAL_AI_MODEL", DEFAULT_LOCAL_AI_MODEL).strip() or DEFAULT_LOCAL_AI_MODEL
    try:
        timeout_s = float(os.getenv("SPM_LOCAL_AI_TIMEOUT_SECONDS", "45"))
    except ValueError:
        timeout_s = 45.0
    return LocalOpenAIConfig(
        base_url=base_url,
        endpoint=endpoint,
        model=model,
        timeout_s=timeout_s,
        provider=os.getenv("SPM_LOCAL_AI_PROVIDER_NAME", "ollama-openai-compatible").strip()
        or "ollama-openai-compatible",
    )


def get_local_ai_status() -> dict[str, Any]:
    """Return local-model configuration without performing network I/O."""
    config = _local_openai_config()
    return {
        "configured": bool(config.base_url and config.model),
        "mode": "local_openai_compatible",
        "provider": config.provider,
        "base_url": config.base_url,
        "model": config.model,
        "role": "advisory_only",
        "safety_rule": SAFETY_RULE,
    }


def _extract_json_object(text: str) -> dict[str, Any] | None:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return None
        try:
            value = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return value if isinstance(value, dict) else None


def _normalize_api_payload(payload: dict[str, Any]) -> dict[str, Any]:
    content = payload.get("content")
    parsed_content = _extract_json_object(content) if isinstance(content, str) else None
    advice_payload = parsed_content or payload
    recommendation = advice_payload.get("recommendation") or advice_payload.get("recommendations") or advice_payload.get("advice")
    if isinstance(recommendation, str):
        recommendation = [recommendation]
    if not isinstance(recommendation, list):
        recommendation = [str(content)] if content else ["Local LLM returned no recommendation list."]
    return {
        "ai_api_response": {"content": content, "usage": payload.get("usage")},
        "recommendation": [str(item) for item in recommendation],
        "risk": str(advice_payload.get("risk", "medium")),
        "target_phase": str(advice_payload.get("target_phase", "2.2")),
        "reasoning": str(advice_payload.get("reasoning", "")),
    }


def _call_local_openai_api(task: str, context: dict[str, Any]) -> dict[str, Any]:
    config = _local_openai_config()
    user_payload = {
        "task": task,
        "context": context,
        "execution_allowed": False,
        "expected_response": {
            "recommendation": "list[str]",
            "risk": "low|medium|high",
            "target_phase": "2.1|2.2|2.3|2.4|2.5",
            "reasoning": "short string",
        },
    }
    body = {
        "model": config.model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are the local LLM advisory layer for an SPM Prusa MK4S scanner. "
                    "Focus on analysis, simulation, anomaly triage, operator safety, and clear "
                    "engineering explanations. Hard rule: "
                    f"{SAFETY_RULE} Return only JSON with keys recommendation, risk, "
                    "target_phase, reasoning."
                ),
            },
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=True)},
        ],
        "temperature": float(os.getenv("SPM_LOCAL_AI_TEMPERATURE", "0.15")),
        "max_tokens": int(os.getenv("SPM_LOCAL_AI_MAX_TOKENS", "900")),
        "stream": False,
    }
    req = request.Request(
        f"{config.base_url}{config.endpoint}",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=config.timeout_s) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, error.URLError, json.JSONDecodeError) as exc:
        return {
            "ai_api_error": repr(exc),
            "recommendation": [
                "The local LLM is not reachable. Keep using deterministic local safety recommendations.",
                "Start the local OpenAI-compatible server and retry.",
            ],
            "risk": "medium",
            "target_phase": "2.2",
            "provider": config.provider,
        }

    choice = (payload.get("choices") or [{}])[0]
    message = choice.get("message") if isinstance(choice, dict) else {}
    content = message.get("content") if isinstance(message, dict) else None
    normalized = _normalize_api_payload({"content": content, "usage": payload.get("usage")})
    normalized["provider"] = config.provider
    normalized["local_model"] = config.model
    return normalized


def _fallback_recommendation(task: str) -> tuple[list[str], str, str]:
    normalized = task.strip().lower()
    if "approach" in normalized or "z" in normalized:
        return (["Confirm position readback before a Z move.", "Use simulation first.", "Require operator confirmation before real motion."], "high", "2.3")
    if "scan" in normalized or "xy" in normalized or "raster" in normalized:
        return (["Start with a small scan inside the safe XY envelope.", "Preview the raster in simulation.", "Only enable a scan after deterministic preflight checks pass."], "medium", "2.4")
    return (["Use the local LLM for explanation and planning.", "Keep physical motion under deterministic local safety control."], "low", "2.2")


def build_ai_recommendation(task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build an advisory response using the configured local LLM only."""
    context = context or {}
    status = get_local_ai_status()
    api_payload = _call_local_openai_api(task, context)
    if "ai_api_error" in api_payload:
        recommendation, risk, target_phase = _fallback_recommendation(task)
    else:
        recommendation = list(api_payload["recommendation"])
        risk = str(api_payload["risk"])
        target_phase = str(api_payload["target_phase"])

    payload = {
        "ai_mode": status["mode"],
        "ai_provider": status["provider"],
        "role": status["role"],
        "task": task,
        "target_phase": target_phase,
        "risk": risk,
        "recommendation": recommendation,
        "context_received": context,
        "execution_allowed": False,
        "safety_note": SAFETY_RULE,
        "api_configured": status["configured"],
        "api_source": "local_only",
        "local_ai_status": status,
    }
    if "ai_api_error" in api_payload:
        payload["ai_api_error"] = api_payload["ai_api_error"]
    if "ai_api_response" in api_payload:
        payload["ai_api_response"] = api_payload["ai_api_response"]
    return payload