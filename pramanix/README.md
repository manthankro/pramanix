# Pramanix Project Agent (backend)

A tool-using AI mentor that finds GitHub repositories for student projects, explains them like a
teacher, and helps students build an original version.

## Run
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env        # add ANTHROPIC_API_KEY and GITHUB_TOKEN
    pytest                      # scoring tests
    uvicorn app.main:app --reload

## Try it
    curl -N -X POST localhost:8000/api/chat -H 'Content-Type: application/json' \
      -d '{"session_id":"demo-session-1","message":"I am a 3rd year BCS student, need a medium Python web project with a database."}'

Streams server-sent events: `status` (tool being used), `final` (agent reply), `error`.

## Design rules
- Evidence-first: scoring needs fetched metadata and README; judgments without evidence are capped.
- Scores are computed in code (`app/scoring.py`), never by the LLM.
- Tool output is wrapped as untrusted data to resist prompt injection from READMEs.
- Repository code is never executed.

## Before real students use it
- Replace in-memory sessions with PostgreSQL/Redis.
- Add authentication or at least per-user limits, and set a spending cap in the Anthropic console.
- Run behind HTTPS with `--proxy-headers`.
