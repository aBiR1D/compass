# Compass — AI Life Strategist

## CLAUDE.md

### Project Overview
Compass is an AI-powered life strategist that interviews you, builds a complete model of your life, and generates personalized daily micro-actions that compound into massive change.

### Architecture
- **compass/models.py** — Pydantic data models (LifeArea, LifeScore, UserProfile, Goal, DailyAction, WeeklyPlan, ProgressEntry, LifeMap)
- **compass/ai.py** — LLM abstraction (Anthropic / OpenAI)
- **compass/interviewer.py** — AI-powered life interview that builds a UserProfile
- **compass/strategist.py** — Strategy engine (life maps, weekly plans, daily actions)
- **compass/tracker.py** — SQLite-backed progress persistence
- **compass/cli.py** — Typer CLI with Rich output
- **compass/api/app.py** — FastAPI REST API
- **compass/mcp/server.py** — MCP server (FastMCP)

### Key Commands
```bash
# CLI
compass start       # Begin life interview
compass today       # Today's actions
compass week        # Weekly plan
compass log         # Log progress
compass checkin     # Weekly AI check-in
compass map         # Display life map
compass score       # Life area scores

# API
uvicorn compass.api.app:app --reload

# MCP
python -m compass.mcp.server

# Tests
python -m pytest tests/ -v
```

### Configuration
Copy `.env.example` to `.env` and set your API key.
Default LLM provider is Anthropic (Claude). Set `COMPASS_LLM_PROVIDER=openai` to use OpenAI.

### Style
- Python 3.10+, type hints everywhere
- Pydantic v2 models with strict validation
- Async-first architecture
- Rich terminal output
