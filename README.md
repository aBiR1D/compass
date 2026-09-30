# 🧭 Compass — AI Life Strategist

> Like having a $500/hr executive coach for $10/month.

Compass interviews you, builds a complete model of your life, and generates **personalized daily micro-actions** that compound into massive change. Not generic advice — **YOUR** specific next step based on **YOUR** situation.

## Features

- 🎤 **AI Life Interview** — guided conversation that builds your complete profile
- 🎯 **Personalized Actions** — daily micro-actions tailored to your goals, constraints, and energy
- 📊 **Life Scores** — track satisfaction across 6 life areas (career, finances, health, relationships, personal growth, creativity)
- 📈 **Progress Tracking** — streaks, mood/energy trends, weekly summaries
- 🔄 **Adaptive Strategy** — plans evolve as your life changes
- 🤖 **Weekly Check-ins** — AI reviews your progress and adjusts the plan

## Quick Start

```bash
# Install
pip install -e .

# Set up your API key
cp .env.example .env
# Edit .env with your Anthropic or OpenAI API key

# Start the interview
compass start

# See today's actions
compass today

# Log your progress
compass log

# Weekly check-in
compass checkin
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `compass start` | Begin the life interview |
| `compass today` | Show today's personalized actions |
| `compass week` | Show this week's plan |
| `compass log` | Log today's progress (interactive) |
| `compass checkin` | Weekly AI check-in |
| `compass map` | Display your life map |
| `compass score` | Show life area scores |

## API Server

```bash
uvicorn compass.api.app:app --reload --port 8000
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/interview` | Start/continue interview |
| `GET` | `/api/v1/today` | Today's actions |
| `GET` | `/api/v1/week` | Weekly plan |
| `POST` | `/api/v1/progress` | Log progress |
| `GET` | `/api/v1/map` | Full life map |
| `GET` | `/health` | Health check |

## MCP Server

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "compass": {
      "command": "python",
      "args": ["-m", "compass.mcp.server"]
    }
  }
}
```

### Tools

- `get_daily_actions` — Today's personalized actions
- `get_life_map` — Your current life map
- `weekly_checkin` — Run a weekly check-in
- `log_progress` — Log daily progress

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `COMPASS_LLM_PROVIDER` | `anthropic` | LLM provider (`anthropic` or `openai`) |
| `ANTHROPIC_API_KEY` | — | Your Anthropic API key |
| `OPENAI_API_KEY` | — | Your OpenAI API key |
| `COMPASS_DB_PATH` | `~/.compass/compass.db` | SQLite database path |

## Development

```bash
# Install with dev dependencies
pip install -e '.[dev]'

# Run tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=compass --cov-report=html
```

## License

MIT
