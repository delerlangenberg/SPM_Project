# Academic AI API Integration Plan

Date: 2026-06-12

## Purpose

The Academic AI API can be useful for documentation, experiment notes, interpretation support, and educational explanations. It must not be placed in the real-time motion-control or safety path.

## Safety Boundary

Allowed:

- Summarize logs.
- Summarize scan metadata.
- Explain scan results.
- Draft lab notes.
- Suggest next non-motion analysis steps.
- Help classify experiment quality after data is saved.

Not allowed:

- Directly send G-code.
- Decide whether real motion is safe.
- Override limits.
- Start scans.
- Change Z approach thresholds automatically.
- Control emergency stop or safe park logic.

## Proposed Future Phases

### AI Phase 1 - Offline Report Assistant

Input:

- CSV scan output.
- PNG image.
- Metadata JSON.
- Raw serial log.

Output:

- Human-readable experiment summary.
- Possible failure causes.
- Suggested next supervised test.

### AI Phase 2 - Documentation Assistant

Input:

- Operator log.
- Hardware test log.
- Phase roadmap.

Output:

- Clean project handoff.
- Test checklist.
- Phase status update.

### AI Phase 3 - Optional GUI Analysis Panel

Input:

- Saved data only.

Output:

- Explanation and report text.

Rule:

- GUI panel must be analysis-only.
- It must not have motion buttons or command permissions.

## Configuration Needed Later

The API details are not stored yet. Before implementation, define:

- API base URL.
- Authentication method.
- Environment variable name for API key.
- Request/response schema.
- Rate limits.
- Whether data can be sent externally.

Recommended environment variable placeholder:

`ACADEMIC_AI_API_KEY`

## First Implementation Target

Create a small offline report command:

```powershell
.\.venv\Scripts\python.exe -m core.application.academic_ai_report --input data\scan.metadata.json
```

Default behavior should be local/dry-run summary until API configuration is confirmed.
