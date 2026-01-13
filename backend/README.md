# Backend - Chatbot API

FastAPI-based backend service that provides a streaming chat API powered by Ollama and LangChain. The service manages conversation sessions, handles LLM interactions, and streams responses in real-time via Server-Sent Events.

## Technology Stack

- **FastAPI 0.120.4+** - Modern async web framework
- **LangChain** - LLM orchestration (Core, Community, Ollama packages)
- **Pydantic 2.9+** - Data validation and settings management
- **SSE-Starlette 2.0+** - Server-Sent Events support
- **Uvicorn** - ASGI server with standard extras
- **Pytest** - Testing framework
- **Black & Ruff** - Code formatting and linting

## Prerequisites

- Python 3.12 or higher
- Docker & Docker Compose (for Ollama)
- 8GB+ RAM recommended for the 7B model

## Local Development Setup

### 1. Set Up Python Environment

Using Conda (recommended):

```bash
# Install Miniforge if not already installed
brew install miniforge

# Initialize shell (if first time)
conda init zsh && exec $SHELL

# Create and activate environment
conda create -n chatbot python=3.12 -y
conda activate chatbot

# Upgrade pip
python -m pip install --upgrade pip
```

Using venv:

```bash
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Start Ollama

Make sure Ollama is running before starting the backend. From the project root:

```bash
docker compose up ollama ollama-init -d
```

> **First run:** The `ollama-init` service downloads the model (~5GB). This only needs to run once. After that, you can use just `docker compose up ollama -d`.

See the [root README](../README.md) for complete Docker setup instructions.

### 4. Run the Backend

Start the server with auto-reload:

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or using the main module directly:

```bash
python -m app.main
```

The API will be available at:
- **Base URL**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

## Configuration

The application is configured via environment variables using Pydantic Settings. Create a `.env` file in the backend directory or set environment variables directly.

### Available Configuration Options

#### General Settings

```bash
# Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# CORS allowed origins (comma-separated or JSON array)
# Use ["*"] to allow all origins (development only)
ALLOW_ORIGINS=["http://localhost:5173"]
```

#### Ollama Connection

```bash
# Ollama server base URL
OLLAMA_BASE_URL=http://localhost:11434

# Model name/tag to use
OLLAMA_MODEL=qwen2.5:7b-instruct
```

#### LLM Generation Parameters

```bash
# Sampling temperature (0.0 = deterministic, higher = more random)
OLLAMA_TEMPERATURE=0.2

# Nucleus sampling threshold (0.0 to 1.0)
OLLAMA_TOP_P=0.9

# Top-k sampling limit
OLLAMA_TOP_K=40

# Repetition penalty factor
OLLAMA_REPEAT_PENALTY=1.1

# Context window size (input tokens)
OLLAMA_NUM_CTX=4096

# Maximum tokens to generate
OLLAMA_NUM_PREDICT=512

# Optional: Deterministic seed for reproducibility
# OLLAMA_SEED=42

# Optional: Stop sequences (comma-separated)
# OLLAMA_STOP=["</s>", "[DONE]"]
```

#### Advanced Parameters (Optional)

```bash
# Mirostat sampling mode (0, 1, or 2)
# OLLAMA_MIROSTAT=0

# Mirostat target surprise parameter
# OLLAMA_MIROSTAT_TAU=5.0

# Mirostat learning rate parameter
# OLLAMA_MIROSTAT_ETA=0.1
```

### Getting Started with Environment Variables

Copy the example environment file and adjust as needed:

```bash
cp .env.example .env
```

The `.env.example` file contains all available configuration options with sensible defaults. You only need to modify values if you want to change the default behavior.

For Docker Compose usage, environment variables are pre-configured in `docker-compose.yml`.

## Project Structure

```
backend/
├── app/
│   ├── api/                    # API endpoints
│   │   ├── chat.py            # Chat streaming endpoint
│   │   ├── health.py          # Health check endpoint
│   │   └── __init__.py        # Router registration
│   │
│   ├── core/                   # Core configuration
│   │   ├── config.py          # Pydantic settings
│   │   └── logging.py         # Logging setup
│   │
│   ├── services/               # Business logic
│   │   ├── llm_client.py      # LangChain Ollama wrapper
│   │   └── memory.py          # Session memory management
│   │
│   ├── schemas/                # Pydantic models
│   │   └── chat.py            # Request/response schemas
│   │
│   ├── utils/                  # Utility functions
│   │   ├── chat.py            # Chat utilities
│   │   ├── sessions.py        # Session management
│   │   └── token_counter.py   # Token counting
│   │
│   ├── cli/                    # Command-line interface
│   │   └── chat.py            # CLI chat tool
│   │
│   └── main.py                 # Application factory
│
├── tests/                      # Test suite
│   ├── api/                   # API integration tests
│   ├── services/              # Service unit tests
│   └── conftest.py            # Pytest fixtures
│
├── requirements.txt            # Python dependencies
└── pytest.ini                  # Pytest configuration
```

## API Endpoints

### Health Check

**GET** `/api/health`

Returns service health status and configuration.

**Response:**
```json
{
  "status": "healthy",
  "ollama_url": "http://localhost:11434",
  "model": "qwen2.5:7b-instruct"
}
```

### Stream Chat

**GET** `/api/chat/stream`

Streams chat responses via Server-Sent Events.

**Query Parameters:**
- `message` (required): User message text
- `session_id` (optional): Session ID for conversation continuity

**Response:** Server-Sent Events stream

**Event Types:**
- `token`: Individual response tokens
- `done`: Stream completion with metadata
- `error`: Error information

**Example:**
```bash
curl -N "http://localhost:8000/api/chat/stream?message=Hello"
```

## Development

### Code Quality Tools

Format code with Black:
```bash
black app/ tests/
```

Lint with Ruff:
```bash
ruff check app/ tests/
```

### Pre-commit Hooks

Install pre-commit hooks for automated checks:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test Files

```bash
# API tests
pytest tests/api/test_chat_api.py

# Service tests
pytest tests/services/test_llm_client.py
pytest tests/services/test_memory.py
```

### Test Configuration

Tests are configured in `pytest.ini`:
- Async support via `pytest-asyncio`
- Automatic test discovery in `tests/` directory
- Console output with `-v` verbosity

## CLI Tool

A command-line chat interface is available for testing:

```bash
python -m app.cli.chat
```

This provides an interactive terminal-based chat session using the configured Ollama model.

## Troubleshooting

### Ollama Connection Issues

**Problem:** Cannot connect to Ollama at `http://localhost:11434`

**Solutions:**
1. Verify Ollama container is running:
   ```bash
   docker ps | grep ollama
   ```

2. Check Ollama health:
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. Restart the container:
   ```bash
   docker compose restart ollama
   ```

### Model Not Found

**Problem:** Model `qwen2.5:7b-instruct` not available

**Solutions:**
1. Wait for initial model pull to complete (check logs):
   ```bash
   docker compose logs ollama-init
   ```

2. Manually pull the model:
   ```bash
   docker exec ollama ollama pull qwen2.5:7b-instruct
   ```

### Memory Issues

**Problem:** Out of memory when running the model

**Solutions:**
1. Ensure at least 8GB RAM is available
2. Close other memory-intensive applications
3. Consider using a smaller model (e.g., `qwen2.5:3b`)

### Import Errors

**Problem:** `ModuleNotFoundError` when importing app modules

**Solutions:**
1. Ensure you're in the backend directory
2. Run commands using `python -m` prefix:
   ```bash
   python -m uvicorn app.main:app --reload
   ```

### CORS Errors

**Problem:** Frontend requests blocked by CORS policy

**Solutions:**
1. Verify `ALLOW_ORIGINS` includes the frontend URL
2. For development, use `ALLOW_ORIGINS=["*"]`
3. Restart the backend after configuration changes

## Performance Notes

- **Context Window**: Larger `OLLAMA_NUM_CTX` values increase memory usage
- **Streaming**: SSE streaming reduces perceived latency for long responses
- **Session Memory**: Conversation history is stored in-memory per session (resets on restart)

## Dependencies

Key dependencies and their purposes:

- `fastapi` - Web framework with OpenAPI support
- `uvicorn[standard]` - Production ASGI server
- `pydantic` & `pydantic-settings` - Data validation and configuration
- `langchain-core`, `langchain-community`, `langchain-ollama` - LLM orchestration
- `sse-starlette` - Server-Sent Events for streaming
- `httpx` - Async HTTP client for Ollama communication
- `tenacity` - Retry logic for resilient API calls
- `pytest` & `pytest-asyncio` - Testing framework

## License

MIT License - see [LICENSE](../LICENSE) for details.

## Related Documentation

- [Root README](../README.md) - Project overview
- [Frontend README](../frontend/README.md) - Frontend setup and development
