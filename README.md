# Medicare Benefits Guide - Prototype

A static, single-page prototype to test task-based “Care Cards” and “Learn Cards” with follow-up questions.

## Run locally
- Option A: Open `index.html` directly in your browser.
- Option B: Use any static server, e.g. `python3 -m http.server` from this folder, then visit `http://localhost:8000`.

## What’s included
- Intent picker (Do vs Learn).
- Intake (ZIP, plan type, optional phrase).
- Four seed topics:
  - Do: shingles vaccine, MRI
  - Learn: deductible vs coinsurance, Part B overview
- Follow-ups:
  - Suggested questions
  - Free-text question box
  - “Explain this step” micro-expansions
- Simple router based on keywords.

## Edit content
- Update `assets/seed.json` in a text editor (vi) to change topics, labels, steps, follow-ups, and routing.
- The app hot-loads the JSON on refresh.

## Notes
- This is guidance, not benefits determination. Numbers are estimates.
- No backend or analytics are included in this static build. Instrumentation is shown via `console.info(...)` calls.

## Next steps
- Add a tiny logging endpoint to capture events.
- Swap heuristic Q&A with a rules file.
- Add EOB explainer and SMS adapter.
