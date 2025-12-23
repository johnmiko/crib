# AI Coding Assistant Instructions for Crib Backend

## Project Overview
FastAPI backend for a Cribbage game exposing a REST API. Core game logic lives in `cribbage/` (players, dealing, pegging, scoring). The API orchestrates rounds and exposes a clean, stable contract for the frontend.

## Architecture
- API: FastAPI app in `app.py`
- Game engine: `cribbage/` package (`CribbageGame`, `CribbageRound`, scoring functions)
- Session control: `GameSession`, `ResumableRound` in `app.py`
- Tests: Pytest under `test/`

## API Conventions
- Player names mapped for frontend:
  - Internal `"human"` → frontend `"you"`
  - Always use helper `_to_frontend_name()` and `_map_scores_for_frontend()`
- Response fields:
  - `scores`: keys `you`, `computer`
  - `dealer`: `you | computer | none`
  - `winner`: `you | computer | null`
  - `table_value`: reflects current active sequence only
- Don’t break these shape/keys; update tests if contracts expand.

## Key Helpers
- `_to_frontend_name(obj)`: maps internal player/strings to `"you"|"computer"`
- `_map_scores_for_frontend(game)`: returns `{ you, computer }`
- Use these for all future fields that include player names.

## Development Workflow
- Run tests: `python -m pytest -q`
- Local server: `python -m uvicorn app:app --host 127.0.0.1 --port 8001`
- Keep changes minimal and focused; preserve existing public API shapes.

## Testing
- Prefer deterministic pegging tests; see `conftest.py` fixture `deterministic_computer`.
- Validate scoring events: pairs, fifteens, 31, runs; also `table_value` across sequences.
- When changing name mapping or response shapes, add invariant tests asserting keys and allowed values.

## Coding Conventions
- Type hints throughout `app.py`
- Clear, small helpers rather than inline ad-hoc mapping
- Avoid renaming API keys; map at boundary instead (internal → frontend)

## Notes
- Sequence boundaries reset only at `go_or_31_reached()`
- Keep logs helpful but not noisy; `debug()` shows pegging steps
