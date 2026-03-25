# Deployment

## Docker Compose (Recommended)

The simplest way to run Bitig.

### 1. Clone and configure

```bash
git clone https://github.com/ezberci/bitig.git
cd bitig
cp .env.example .env
```

Edit `.env`:
- **Required:** Set `API_KEY` to a secure random string
- **Optional:** Configure connector credentials (Gmail, Jira)
- **Optional:** Set `LLM_PROVIDER=claude` and `CLAUDE_API_KEY` if not using Ollama

### 2. Start services

```bash
# Backend + Qdrant (minimal)
docker compose up backend qdrant -d

# With Ollama (local LLM)
docker compose --profile with-ollama up -d

# All services including frontend
docker compose --profile with-ollama up -d
```

### 3. Verify

```bash
# Health check
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/health

# Check connector status
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/connectors
```

### 4. Pull an Ollama model

If using Ollama, pull a model before querying:

```bash
docker compose exec ollama ollama pull llama3
```

## Local Development

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Qdrant running locally (or via Docker)
- Ollama running locally (optional)

### Setup

```bash
# Create venv and install
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Copy env
cp .env.example .env
# Edit .env: set QDRANT_URL=http://localhost:6333, OLLAMA_URL=http://localhost:11434

# Start Qdrant (if not already running)
docker run -d -p 6333:6333 qdrant/qdrant:latest

# Run backend
uvicorn src.main:app --reload
```

### Running tests

```bash
pytest tests/ -v
```

Tests mock all external services -- no Qdrant, Ollama, or API credentials needed.

### Linting

```bash
ruff check --fix src/ tests/
ruff format src/ tests/
```

## Services

| Service | Port | Purpose |
|---------|------|---------|
| Backend (FastAPI) | 8000 | REST API |
| Frontend (Next.js) | 3000 | Web UI |
| Qdrant | 6333 | Vector database |
| Ollama | 11434 | Local LLM inference |

## API Endpoints

All endpoints require `X-API-Key` header (except `/api/health`).

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check (Qdrant + Ollama status) |
| POST | `/api/chat` | Ask a question (RAG) |
| GET | `/api/chat/history` | Get chat history |
| GET | `/api/connectors` | List all connectors and status |
| POST | `/api/connectors/{type}/sync` | Trigger sync for a connector |
| GET | `/api/connectors/{type}/status` | Get connector status |
| GET | `/api/entities` | List entities (filterable) |
| GET | `/api/entities/graph` | Get entity graph data |
| GET | `/api/entities/{id}` | Get single entity |
| GET | `/api/ingestion/stats` | Get ingestion statistics |

## Environment Variables

See `.env.example` for all available configuration options with descriptions.

## Data Persistence

| Data | Location | Backed by |
|------|----------|-----------|
| Chunk vectors | `qdrant_data` volume | Qdrant |
| Metadata, entities, relations, chat history | `bitig_data` volume (`data/bitig.db`) | SQLite |
| Ollama models | `ollama_data` volume | Ollama |

## Security Notes

- Change the default `API_KEY` before exposing to any network
- Never commit `.env` or credential files
- Bitig is designed for single-user self-hosting; it has no multi-tenant auth
- When using Ollama, all inference stays local -- no data leaves your machine
