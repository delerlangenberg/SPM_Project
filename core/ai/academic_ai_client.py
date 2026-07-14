"""Academic AI advisory layer for the SPM Prusa project.

This module is intentionally conservative.

Academic AI may suggest, explain, diagnose, and simulate.
It must not directly execute MK4S motion commands.
Real movement must always pass through local safety gates and operator confirmation.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import request, error


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ACADEMIC_AI_BASE_URL = "https://it-u-api.academic-ai.at"
DEFAULT_ACADEMIC_AI_MODEL = "GPT-5.2"
DEFAULT_LOCAL_AI_BASE_URL = "http://127.0.0.1:11434/v1"
DEFAULT_LOCAL_AI_MODEL = "qwen3-coder-next"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"


@dataclass(frozen=True)
class AcademicAIStatus:
    configured: bool
    mode: str
    role: str
    safety_rule: str
    source: str = "not_configured"


@dataclass(frozen=True)
class AcademicAIConfig:
    base_url: str
    endpoint: str
    client_id: str
    client_secret: str
    model: str
    timeout_s: float
    source: str


@dataclass(frozen=True)
class LocalOpenAIConfig:
    base_url: str
    endpoint: str
    model: str
    timeout_s: float
    provider: str


@dataclass(frozen=True)
class DeepSeekConfig:
    base_url: str
    endpoint: str
    api_key: str
    model: str
    timeout_s: float


def _academic_ai_config() -> AcademicAIConfig:
    client_id = (
        os.getenv("ACADEMIC_AI_CLIENT_ID", "").strip()
        or os.getenv("CLIENT_ID", "").strip()
        or os.getenv("ACADEMIC_AI_API_KEY", "").strip()
    )
    client_secret = (
        os.getenv("ACADEMIC_AI_CLIENT_SECRET", "").strip()
        or os.getenv("CLIENT_SECRET", "").strip()
        or os.getenv("ACADEMIC_AI_API_SECRET", "").strip()
    )
    base_url = os.getenv("ACADEMIC_AI_BASE_URL", DEFAULT_ACADEMIC_AI_BASE_URL).strip().rstrip("/")
    endpoint = os.getenv("ACADEMIC_AI_CHAT_ENDPOINT", "/api/v1/llm/chat").strip()
    if not endpoint.startswith("/"):
        endpoint = f"/{endpoint}"
    model = os.getenv("ACADEMIC_AI_MODEL", DEFAULT_ACADEMIC_AI_MODEL).strip() or DEFAULT_ACADEMIC_AI_MODEL
    try:
        timeout_s = float(os.getenv("ACADEMIC_AI_TIMEOUT_SECONDS", "30"))
    except ValueError:
        timeout_s = 30.0
    source = "not_configured"
    if client_id and client_secret:
        source = "environment"
    return AcademicAIConfig(
        base_url=base_url,
        endpoint=endpoint,
        client_id=client_id,
        client_secret=client_secret,
        model=model,
        timeout_s=timeout_s,
        source=source,
    )


def _deepseek_config() -> DeepSeekConfig:
    base_url = os.getenv("SPM_DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL).strip().rstrip("/")
    endpoint = os.getenv("SPM_DEEPSEEK_CHAT_ENDPOINT", "/chat/completions").strip()
    if not endpoint.startswith("/"):
        endpoint = f"/{endpoint}"
    api_key = (
        os.getenv("SPM_DEEPSEEK_API_KEY", "").strip()
        or os.getenv("DEEPSEEK_API_KEY", "").strip()
    )
    model = os.getenv("SPM_DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL).strip() or DEFAULT_DEEPSEEK_MODEL
    try:
        timeout_s = float(os.getenv("SPM_DEEPSEEK_TIMEOUT_SECONDS", "45"))
    except ValueError:
        timeout_s = 45.0
    return DeepSeekConfig(
        base_url=base_url,
        endpoint=endpoint,
        api_key=api_key,
        model=model,
        timeout_s=timeout_s,
    )


def _selected_ai_provider() -> str:
    provider = os.getenv("SPM_AI_PROVIDER", "academic").strip().lower()
    if provider in {"local", "ollama", "open_source", "open-source", "local_openai"}:
        return "local"
    if provider in {"deepseek", "deep_seek", "deepseek-api"}:
        return "deepseek"
    if provider in {"auto", "hybrid"}:
        return "auto"
    return "academic"


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


def get_academic_ai_status() -> AcademicAIStatus:
    """Return current Academic AI integration status without exposing secrets."""
    config = _academic_ai_config()
    configured = bool(config.base_url and config.client_id and config.client_secret and config.model)

    return AcademicAIStatus(
        configured=configured,
        mode="configured" if configured else "stub_not_configured",
        role="advisory_only",
        safety_rule="AI may recommend approach, scan, simulation, or diagnosis steps, but cannot execute machine motion directly.",
        source=config.source,
    )


def get_local_ai_status() -> dict[str, Any]:
    config = _local_openai_config()
    return {
        "configured": bool(config.base_url and config.model),
        "mode": "local_open_source_openai_compatible",
        "provider": config.provider,
        "base_url": config.base_url,
        "model": config.model,
        "role": "advisory_only",
        "safety_rule": "Local/open-source AI may recommend and explain, but cannot execute machine motion directly.",
    }


def get_deepseek_ai_status() -> dict[str, Any]:
    config = _deepseek_config()
    return {
        "configured": bool(config.base_url and config.api_key and config.model),
        "mode": "deepseek_openai_compatible",
        "provider": "deepseek",
        "base_url": config.base_url,
        "model": config.model,
        "role": "advisory_only",
        "safety_rule": "DeepSeek AI may recommend and explain, but cannot execute machine motion directly.",
    }


def _academic_ai_headers(config: AcademicAIConfig) -> dict[str, str]:
    return {
        "X-Client-ID": config.client_id,
        "X-Client-Secret": config.client_secret,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _spm_system_prompt(status: AcademicAIStatus) -> str:
    return (
        "You are the Academic AI advisory layer for an SPM Prusa MK4S scanner. "
        "Act like a senior SPM instrumentation engineer. Give concise, practical, "
        "safety-first advice for system control, Z approach, raster measurement, "
        "line signal, topography, logging, and simulation. "
        f"Hard rule: {status.safety_rule} "
        "Return only JSON with keys recommendation, risk, target_phase, reasoning. "
        "recommendation must be a short list of operator/developer actions."
    )


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
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    content = data.get("content") if isinstance(data, dict) else None
    parsed_content = _extract_json_object(content) if isinstance(content, str) else None
    advice_payload = parsed_content or data
    recommendation = advice_payload.get("recommendation") or advice_payload.get("recommendations") or advice_payload.get("advice")
    if isinstance(recommendation, str):
        recommendation = [recommendation]
    if not isinstance(recommendation, list):
        recommendation = [str(content)] if content else ["Academic AI returned a response, but no recommendation list was found."]
    return {
        "ai_api_response": {
            "content": content,
            "usage": data.get("usage") if isinstance(data, dict) else None,
        },
        "recommendation": [str(item) for item in recommendation],
        "risk": str(advice_payload.get("risk", "medium")),
        "target_phase": str(advice_payload.get("target_phase", "2.2")),
        "reasoning": str(advice_payload.get("reasoning", "")),
    }


def _call_academic_ai_api(task: str, context: dict[str, Any], status: AcademicAIStatus) -> dict[str, Any] | None:
    config = _academic_ai_config()
    if not status.configured:
        return None

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
                "role": "user",
                "content": (
                    f"{_spm_system_prompt(status)}\n\n"
                    f"SPM request payload:\n{json.dumps(user_payload, ensure_ascii=True)}"
                ),
            },
        ],
        "temperature": float(os.getenv("ACADEMIC_AI_TEMPERATURE", "0.2")),
        "maxTokens": int(os.getenv("ACADEMIC_AI_MAX_TOKENS", "700")),
    }
    req = request.Request(
        f"{config.base_url}{config.endpoint}",
        data=json.dumps(body).encode("utf-8"),
        headers=_academic_ai_headers(config),
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=config.timeout_s) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        response_text = exc.read().decode("utf-8", errors="replace")[:1000]
        return {
            "ai_api_error": f"HTTP {exc.code}: {response_text}",
            "recommendation": [
                "Academic AI API call failed. Use local safety recommendations.",
                "Do not execute motion based on unavailable AI advice.",
            ],
            "risk": "medium",
            "target_phase": "2.2",
        }
    except (OSError, error.URLError, json.JSONDecodeError) as exc:
        return {
            "ai_api_error": repr(exc),
            "recommendation": [
                "Academic AI API call failed. Use local safety recommendations.",
                "Do not execute motion based on unavailable AI advice.",
            ],
            "risk": "medium",
            "target_phase": "2.2",
        }

    return _normalize_api_payload(payload)


def _call_local_openai_api(task: str, context: dict[str, Any]) -> dict[str, Any] | None:
    config = _local_openai_config()
    status = get_local_ai_status()
    if not status["configured"]:
        return None

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
    system_prompt = (
        "You are the local open-source AI advisory layer for an SPM Prusa MK4S scanner. "
        "Focus on code self-development, scan logic, Z auto-approach reasoning, feature detection, "
        "operator safety, and clear engineering explanations. "
        "Hard rule: AI never executes motion and never bypasses deterministic safety gates. "
        "Return only JSON with keys recommendation, risk, target_phase, reasoning."
    )
    body = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": system_prompt},
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
                "Local open-source AI is not reachable. Keep using deterministic local safety recommendations.",
                "If needed, start Ollama or another OpenAI-compatible local server and retry.",
            ],
            "risk": "medium",
            "target_phase": "2.2",
            "provider": status["provider"],
        }

    choice = (payload.get("choices") or [{}])[0]
    message = choice.get("message") if isinstance(choice, dict) else {}
    content = message.get("content") if isinstance(message, dict) else None
    parsed = _extract_json_object(content) if isinstance(content, str) else None
    normalized = _normalize_api_payload({"data": parsed or {"content": content, "usage": payload.get("usage")}})
    normalized["provider"] = status["provider"]
    normalized["local_model"] = config.model
    return normalized


def _call_deepseek_api(task: str, context: dict[str, Any]) -> dict[str, Any] | None:
    config = _deepseek_config()
    if not config.api_key:
        return None

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
    system_prompt = (
        "You are the DeepSeek AI advisory layer for an SPM Prusa MK4S scanner. "
        "Act like a senior SPM instrumentation engineer. Give concise, practical, "
        "safety-first advice for system control, Z approach, raster measurement, "
        "line signal, topography, logging, simulation, and code self-development. "
        "Hard rule: AI never executes motion and never bypasses deterministic safety gates. "
        "Return only JSON with keys recommendation, risk, target_phase, reasoning."
    )
    body = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=True)},
        ],
        "temperature": float(os.getenv("SPM_DEEPSEEK_TEMPERATURE", "0.15")),
        "max_tokens": int(os.getenv("SPM_DEEPSEEK_MAX_TOKENS", "900")),
        "stream": False,
    }
    req = request.Request(
        f"{config.base_url}{config.endpoint}",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {config.api_key}",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=config.timeout_s) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        response_text = exc.read().decode("utf-8", errors="replace")[:1000]
        return {
            "ai_api_error": f"DeepSeek HTTP {exc.code}: {response_text}",
            "recommendation": [
                "DeepSeek API call failed. Use local safety recommendations.",
                "Do not execute motion based on unavailable AI advice.",
            ],
            "risk": "medium",
            "target_phase": "2.2",
            "provider": "deepseek",
        }
    except (OSError, error.URLError, json.JSONDecodeError) as exc:
        return {
            "ai_api_error": repr(exc),
            "recommendation": [
                "DeepSeek API is not reachable. Keep using deterministic local safety recommendations.",
                "Check network connectivity and your DEEPSEEK_API_KEY.",
            ],
            "risk": "medium",
            "target_phase": "2.2",
            "provider": "deepseek",
        }

    choice = (payload.get("choices") or [{}])[0]
    message = choice.get("message") if isinstance(choice, dict) else {}
    content = message.get("content") if isinstance(message, dict) else None
    parsed = _extract_json_object(content) if isinstance(content, str) else None
    normalized = _normalize_api_payload({"data": parsed or {"content": content, "usage": payload.get("usage")}})
    normalized["provider"] = "deepseek"
    normalized["deepseek_model"] = config.model
    return normalized


def build_ai_recommendation(task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a safe advisory response.

    Phase 2.2 is a shell. It returns deterministic local recommendations.
    Later phases can connect this function to Academic AI API credentials.
    """
    context = context or {}
    normalized = task.strip().lower()
    status = get_academic_ai_status()
    provider = _selected_ai_provider()
    api_payload = None

    if provider == "deepseek":
        api_payload = _call_deepseek_api(task, context)
        if api_payload is not None and "ai_api_error" not in api_payload:
            status = AcademicAIStatus(
                configured=True,
                mode="deepseek",
                role="advisory_only",
                safety_rule="DeepSeek AI may recommend and explain, but cannot execute machine motion directly.",
                source="deepseek_api",
            )

    if api_payload is None and provider in {"local", "auto"}:
        api_payload = _call_local_openai_api(task, context)
        if provider == "local" and api_payload is not None and "ai_api_error" not in api_payload:
            status = AcademicAIStatus(
                configured=True,
                mode="local_open_source",
                role="advisory_only",
                safety_rule="Local/open-source AI may recommend and explain, but cannot execute machine motion directly.",
                source=str(api_payload.get("provider", "local_openai")),
            )

    if api_payload is None and provider in {"academic", "auto"}:
        api_payload = _call_academic_ai_api(task, context, status)

    if api_payload is not None:
        recommendation = list(api_payload["recommendation"])
        risk = str(api_payload["risk"])
        target_phase = str(api_payload["target_phase"])
    elif "approach" in normalized or "z" in normalized:
        recommendation = [
            "Confirm MK4S position readback before any Z move.",
            "Use dry-run or simulation mode first.",
            "Use small Z steps near the surface.",
            "Require operator confirmation before real motion.",
            "Log every approach/retract command.",
        ]
        risk = "high"
        target_phase = "2.3"
    elif "scan" in normalized or "xy" in normalized or "raster" in normalized:
        recommendation = [
            "Start with a small scan area inside the safe XY envelope.",
            "Use low resolution first, for example 5x5 or 10x10.",
            "Preview the raster path before real movement.",
            "Generate CSV and PNG output before connecting live hardware.",
            "Only enable real scan after Z and XY status are valid.",
        ]
        risk = "medium"
        target_phase = "2.4"
    elif "simulation" in normalized or "surface" in normalized or "demo" in normalized:
        recommendation = [
            "Use the simulation layer to generate expected topography first.",
            "Keep simulation parameters separate from real hardware parameters.",
            "Use the same scan profile for simulation and real scan comparison.",
            "Show simulation output in the Live View window.",
        ]
        risk = "low"
        target_phase = "2.4"
    else:
        recommendation = [
            "Use Academic AI as an explanation and planning assistant.",
            "Keep all physical motion under local safety control.",
            "Ask for a recommendation, then let the operator approve any action.",
        ]
        risk = "low"
        target_phase = "2.2"

    payload = {
        "ai_mode": status.mode,
        "ai_provider": provider,
        "role": status.role,
        "task": task,
        "target_phase": target_phase,
        "risk": risk,
        "recommendation": recommendation,
        "context_received": context,
        "execution_allowed": False,
        "safety_note": status.safety_rule,
        "api_configured": status.configured,
        "api_source": status.source,
        "local_ai_status": get_local_ai_status(),
        "deepseek_ai_status": get_deepseek_ai_status(),
    }
    if api_payload and "ai_api_error" in api_payload:
        payload["ai_api_error"] = api_payload["ai_api_error"]
    if api_payload and "ai_api_response" in api_payload:
        payload["ai_api_response"] = api_payload["ai_api_response"]
    return payload
