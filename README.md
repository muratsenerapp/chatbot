# Chatbot

<!-- CI/CD Status -->
![CI](https://img.shields.io/github/actions/workflow/status/muratsenerapp/chatbot/ci.yml?label=CI)
![Version Bump](https://img.shields.io/github/actions/workflow/status/muratsenerapp/chatbot/version-bump.yml?label=version-bump)
![Version](https://img.shields.io/github/v/tag/muratsenerapp/chatbot?label=version)

<!-- Code Coverage -->
![Backend Coverage](https://img.shields.io/codecov/c/github/muratsenerapp/chatbot/develop?flag=backend&label=backend%20coverage)
![Frontend Coverage](https://img.shields.io/codecov/c/github/muratsenerapp/chatbot/develop?flag=frontend&label=frontend%20coverage)

<!-- Tech Stack -->
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.120-009688?logo=fastapi&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.3-1C3C3C?logo=langchain&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-22-339933?logo=node.js&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-7-646CFF?logo=vite&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-06B6D4?logo=tailwindcss&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)

A privacy-first, fully offline chatbot that runs entirely on your machine. No cloud services, no API keys, no data leaving your computer.

> **Why This Project?**
>
> Most AI chatbots require sending your conversations to external servers. This project gives you a powerful conversational AI that:
> - **Runs 100% locally** - Your data never leaves your machine
> - **Works offline** - After initial setup, no internet required
> - **Zero cost per query** - No API fees or subscriptions
> - **Full control** - Customize the model, parameters, and behavior
>
> Perfect for sensitive conversations, air-gapped environments, or anyone who values privacy.

## Overview

This chatbot application provides an interactive conversational interface powered by the Qwen2.5 7B Instruct model running locally through Ollama. The application features real-time streaming responses, persistent conversation sessions, and a responsive dark/light theme UI.

## Architecture

### High-Level Design

```
┌─────────────┐      HTTP/SSE       ┌─────────────┐      HTTP API      ┌─────────────┐
│   Browser   │ ◄─────────────────► │   FastAPI   │ ◄────────────────► │   Ollama    │
│  (React UI) │   Streaming Chat    │   Backend   │   Model Queries    │  Container  │
└─────────────┘                     └─────────────┘                    └─────────────┘
     :5173                               :8000                              :11434
```

### Technology Stack

**Frontend:**
- **React 19** - Modern UI library with hooks
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **Server-Sent Events (SSE)** - Real-time token streaming

**Backend:**
- **FastAPI** - High-performance async web framework
- **LangChain** - LLM orchestration and abstractions
- **Pydantic** - Data validation and settings management
- **Uvicorn** - ASGI server

**Infrastructure:**
- **Docker Compose** - Container orchestration
- **Ollama** - Local LLM runtime
- **Qwen2.5 7B Instruct** - Language model

### Key Features

- **Real-time Streaming**: Token-by-token response streaming via Server-Sent Events
- **Session Management**: Maintains conversation context across multiple exchanges
- **Theme Support**: Dark and light mode with system preference detection
- **Error Handling**: Graceful error recovery with retry functionality
- **Type Safety**: End-to-end TypeScript and Pydantic validation
- **Configurable LLM**: Adjustable temperature, context window, and generation parameters
- **Testing**: Comprehensive test suites for both frontend and backend

## Project Structure

```
chatbot/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/         # API endpoints (chat, health)
│   │   ├── core/        # Configuration and logging
│   │   ├── services/    # LLM client and memory management
│   │   ├── schemas/     # Pydantic models
│   │   └── utils/       # Utilities (sessions, token counting)
│   ├── tests/           # Backend test suite
│   └── requirements.txt # Python dependencies
│
├── frontend/            # React application
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── lib/         # SSE client library
│   │   └── types/       # TypeScript definitions
│   ├── tests/           # Frontend test suite
│   └── package.json     # Node dependencies
│
├── docker-compose.yml   # Full stack container orchestration
└── docs/                # Additional documentation
```

## Getting Started

### Prerequisites

- **Docker & Docker Compose** - For running the entire stack
- **8GB+ RAM** - Recommended for running the 7B model
- **~5GB free disk space** - For the Qwen2.5 7B model download

**For local development (optional):**
- Python 3.12+ - Backend development
- Node.js 22.x - Frontend development

### Quick Start (Docker)

The easiest way to run the application is with Docker Compose:

```bash
# Clone the repository
git clone https://github.com/muratsenerapp/chatbot.git
cd chatbot

# Start all services (Ollama, Backend, Frontend)
docker compose up -d
```

> **Note:** The first run may take several minutes as Docker downloads the Qwen2.5 7B model (~5GB).

Once running, access the application:
- **Chat UI:** http://localhost:5173
- **API Docs:** http://localhost:8000/api/docs
- **Ollama API:** http://localhost:11434

To stop all services:
```bash
docker compose down
```

### Local Development

For development with hot-reload, see the component READMEs:

- **[Backend README](backend/README.md)** - Python environment, configuration options, API documentation
- **[Frontend README](frontend/README.md)** - Node.js setup, available scripts, component development

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Author

**Murat Şener**
