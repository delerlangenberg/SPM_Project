# SPM AI Provider Strategy

Date: 2026-06-23

## Engineering Decision

Academic AI is useful, but it should not be the only intelligence layer for this SPM project.

Use three layers:

1. Deterministic Python control for all hardware motion and safety gates.
2. Local/open-source AI for self-development, scan-logic explanation, feature interpretation, auto-approach reasoning, and code assistance.
3. Academic AI as an external advisory provider when available.

AI must never execute MK4S motion directly.

## Recommended First Local Provider

Start with Ollama using an OpenAI-compatible local endpoint:

```powershell
ollama pull qwen3-coder-next
ollama serve
```

Then launch the SPM software with:

```powershell
cd D:\SPM_Prusa_Project
.\spm_local_ai.bat
```

Default local AI settings:

- `SPM_AI_PROVIDER=local`
- `SPM_LOCAL_AI_BASE_URL=http://127.0.0.1:11434/v1`
- `SPM_LOCAL_AI_CHAT_ENDPOINT=/chat/completions`
- `SPM_LOCAL_AI_MODEL=qwen3-coder-next`

The model can be changed without editing code:

```powershell
$env:SPM_LOCAL_AI_MODEL='another-open-model'
.\spm_local_ai.ps1
```

## What Local AI Should Help With

- explain scan logic and failure cases
- suggest safer auto-approach settings
- interpret line/topography features
- compare expected simulation with measured data
- review logs and recommend next tests
- help write/refactor project code
- propose feature detectors for edges, bumps, drift, no-contact, and crash-risk signatures

## What Local AI Must Not Do

- send G-code directly
- bypass Safe Standby, Stop, or Disconnect
- change hardware gates by itself
- decide that a Z approach is safe without deterministic checks
- replace sensor validation

## Future Direction

The long-term architecture should add an SPM intelligence layer with explicit tools:

- `scan_profile_analyzer`
- `z_approach_advisor`
- `feature_detector`
- `log_diagnoser`
- `simulation_vs_real_comparator`
- `code_reviewer`

Each tool should return structured JSON that the UI can display, while the operator confirms every real hardware action.
