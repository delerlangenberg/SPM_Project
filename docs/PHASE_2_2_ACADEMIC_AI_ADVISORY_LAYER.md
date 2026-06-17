# Phase 2.2 Academic AI Advisory Layer

## Purpose

This phase adds the Academic AI API as a professional advisory layer for the SPM Prusa MK4S web operator console.

Academic AI should support the operator, not directly control the machine.

## Safety model

Academic AI is advisory-only.

It may:

- recommend safe Z approach steps
- recommend scan bounds, resolution, and feedrate
- explain current status and logs
- support simulation planning
- help diagnose errors
- explain the SPM workflow for educational use

It may not:

- directly send G-code
- directly move X/Y/Z
- enable real motion without local safety gates
- bypass operator confirmation
- bypass configured MK4S limits

## Web GUI placement

Academic AI appears in the web console as:

- an AI status strip in the Status / Live Log section
- an Academic AI Assistant floating window opened from Tools or the AI button

## Backend endpoints

Phase 2.2 adds:

- `/api/ai/status`
- `/api/ai/recommendation?task=approach`
- `/api/ai/recommendation?task=scan`
- `/api/ai/recommendation?task=simulation`
- `/api/ai/recommendation?task=diagnosis`

## Environment configuration planned for later phase

The real API should be configured through environment variables only:

- `ACADEMIC_AI_BASE_URL`
- `ACADEMIC_AI_API_KEY`
- `ACADEMIC_AI_MODEL` or `ACADEMIC_AI_ASSISTANT_ID`

No API key should be committed to Git.

## Next integration phases

- Phase 2.3: connect local system ON/OFF/STATUS/CLOSE to existing safe hardware services
- Phase 2.4: connect Z approach/retract/readback
- Phase 2.5: connect XY scan setup and preview
- Phase 2.6: connect live view/export/simulation
- Phase 2.7: connect real Academic AI API call behind the advisory interface
