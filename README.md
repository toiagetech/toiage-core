# Toiage Core

Backend API for Toiage — an AI-powered creativity companion for children. Generates stories, hands-on activities, and positive reflections on children's artwork.

## Tech Stack

- **Framework:** FastAPI (Python 3.14)
- **Database:** PostgreSQL via SQLModel + Alembic
- **AI Provider:** OpenRouter (Gemini Flash default, swap to any model)
- **Logging:** Structured JSON logs
- **Analytics:** PostHog (optional, with fallback logging)

## Quick Start

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) package manager
- PostgreSQL running locally

### Setup

```bash
# 1. Clone and enter directory
cd toiage-core

# 2. Copy env file
cp .env.example .env

# 3. Create database (if not exists)
createdb toiage

# 4. Install dependencies
uv sync

# 5. Run migrations
uv run alembic upgrade head

# 6. Start server
uv run uvicorn app.main:app --reload --port 8000
```

Server runs at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

## Project Structure

```
toiage-core/
├── app/
│   ├── api/            # Route handlers
│   │   ├── activities.py
│   │   ├── llm.py
│   │   ├── stories.py
│   │   └── uploads.py
│   ├── core/           # Config & settings
│   │   └── config.py
│   ├── db/             # Database session & base
│   ├── models/         # SQLModel table definitions
│   │   ├── activity.py
│   │   ├── story.py
│   │   └── upload.py
│   ├── prompts/        # External prompt templates
│   │   ├── stories/create.txt
│   │   ├── activities/generate.txt
│   │   ├── reflections/image.txt
│   │   └── system/default.txt
│   ├── schemas/        # Pydantic request/response models
│   ├── services/       # Business logic
│   │   ├── activities.py
│   │   ├── analytics.py
│   │   ├── uploads.py
│   │   └── llm/        # LLM provider abstraction
│   │       ├── base.py
│   │       ├── manager.py
│   │       ├── mock.py
│   │       └── openrouter.py
│   └── utils/          # Logger, exception handlers
├── alembic/            # Database migrations
├── uploads/            # Uploaded images (gitignored)
└── .env.example
```

## Architecture

```
Client → FastAPI → Service Layer → LLM Provider (Mock / OpenRouter)
                  → PostgreSQL (SQLModel)
                  → Analytics (PostHog / Log fallback)
                  → Local File Storage (uploads/)
```

All prompts are external `.txt` files under `app/prompts/` — no hardcoded prompt strings in services.

## API Reference

### LLM

```bash
# Send raw prompt
curl -X POST http://localhost:8000/ai/test \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Tell me a story", "provider": "mock"}'

# Send prompt via template
curl -X POST http://localhost:8000/ai/test-template \
  -H "Content-Type: application/json" \
  -d '{
    "template_category": "stories",
    "template_name": "create",
    "variables": {"age": "5", "theme": "dragons", "child_name": "Arjun", "setting": "forest", "word_count": "200"},
    "provider": "mock"
  }'
```

### Stories

```bash
# Create a story
curl -X POST http://localhost:8000/stories \
  -H "Content-Type: application/json" \
  -d '{"content": "Story text...", "age_group": "3-5", "theme": "adventure"}'

# Get story by ID
curl http://localhost:8000/stories/1

# List all stories
curl http://localhost:8000/stories
```

### Activities

```bash
# Generate from story text (household mode)
curl -X POST http://localhost:8000/activities/generate \
  -H "Content-Type: application/json" \
  -d '{
    "story_text": "A brave rabbit explored the forest...",
    "age_group": "3-5",
    "activity_mode": "household"
  }'

# Generate from existing story (toy-kit mode)
curl -X POST http://localhost:8000/activities/generate \
  -H "Content-Type: application/json" \
  -d '{"story_id": 1, "age_group": "5-7", "activity_mode": "toy-kit"}'

# Get activity by ID
curl http://localhost:8000/activities/1

# List all activities
curl http://localhost:8000/activities
```

### Uploads

```bash
# Upload an image (PNG/JPEG/WEBP/GIF)
curl -X POST http://localhost:8000/uploads/image \
  -F "file=@image.png;type=image/png"

# Get AI reflection on uploaded image
curl -X POST http://localhost:8000/uploads/1/reflect
```

### Health

```bash
# API health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/db-health
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/toiage` | PostgreSQL connection string |
| `OPENROUTER_API_KEY` | (empty) | Set for real AI calls; empty = mock responses |
| `LLM_DEFAULT_MODEL` | `google/gemini-2.0-flash-001` | Model via OpenRouter |
| `LOG_LEVEL` | `INFO` | Logging level |
| `POSTHOG_API_KEY` | (empty) | Set for PostHog analytics; empty = log fallback |
| `MAX_UPLOAD_SIZE_MB` | `10` | Max image upload size |

## Development

```bash
# Auto-generate migration after model changes
uv run alembic revision --autogenerate -m "description"

# Run pending migrations
uv run alembic upgrade head

# View SQL in logs
SQLALCHEMY_WARNINGS=1 uv run uvicorn app.main:app
```

## Database Tables

| Table | Description |
|---|---|
| `stories` | Generated stories with metadata (age_group, theme, skills, difficulty) |
| `activities` | Hands-on activities linked to stories (materials, instructions, challenge) |
| `uploads` | Uploaded image metadata (filename, size, mime_type, url) |
| `alembic_version` | Migration tracking |