# Chatbot

<!-- CI/CD Status -->
![CI](https://img.shields.io/github/actions/workflow/status/muratsenerapp/chatbot/ci.yml?branch=main&label=CI)
![Version Bump](https://img.shields.io/github/actions/workflow/status/muratsenerapp/chatbot/version-bump.yml?label=version-bump)
![Version](https://img.shields.io/github/v/tag/muratsenerapp/chatbot?label=version)

<!-- Code Coverage -->
![Backend Coverage](https://img.shields.io/codecov/c/github/muratsenerapp/chatbot?flag=backend&label=backend%20coverage)
![Frontend Coverage](https://img.shields.io/codecov/c/github/muratsenerapp/chatbot?flag=frontend&label=frontend%20coverage)

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

A modern, real-time chatbot application built with FastAPI and React that leverages Ollama for local LLM inference. This project demonstrates a full-stack implementation with streaming responses, session management, and a polished user interface.

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
├── docker-compose.yml   # Ollama container setup
└── docs/                # Additional documentation
```

## Getting Started

### Prerequisites

- **Docker & Docker Compose** - For running Ollama
- **Python 3.12+** - Backend runtime
- **Node.js 22.x** - Frontend development
- **8GB+ RAM** - Recommended for running the 7B model

### Quick Start

1. **Start Ollama container:**
   ```bash
   docker-compose up -d
   ```
   This will pull and start the Qwen2.5 7B Instruct model (first run may take several minutes).

2. **Set up and run the backend:**
   ```bash
   cd backend
   # See backend/README.md for detailed setup instructions
   ```

3. **Set up and run the frontend:**
   ```bash
   cd frontend
   # See frontend/README.md for detailed setup instructions
   ```

4. **Access the application:**
- Frontend: http://localhost:5173
- Backend API docs: http://localhost:8000/api/docs
- Ollama: http://localhost:11434

## Development Workflow

### Backend Development

The backend provides a REST API with streaming support. For setup, configuration, and development instructions, see [backend/README.md](backend/README.md).

### Frontend Development

The frontend is a React SPA with hot module replacement. For setup, development, and testing instructions, see [frontend/README.md](frontend/README.md).

### Testing

Both frontend and backend include comprehensive test suites. Refer to the respective README files for running tests.

## Configuration

The application can be configured via environment variables:

- **Backend**: See [backend/README.md](backend/README.md#configuration) for Ollama connection, LLM parameters, and CORS settings
- **Frontend**: Vite proxy configuration in `vite.config.ts` routes API calls to the backend

## API Documentation

Once the backend is running, interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Author

**Murat Şener**

---

For detailed setup and development instructions, please refer to:
- [Backend README](backend/README.md)
- [Frontend README](frontend/README.md)
