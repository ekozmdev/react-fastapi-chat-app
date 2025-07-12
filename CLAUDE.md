# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a React + FastAPI chat application with real-time WebSocket communication and OpenAI GPT integration. The project uses a monorepo structure with clear frontend/backend separation:

- **Frontend**: React 18 + TypeScript + Vite 5
- **Backend**: FastAPI + Python 3.13 + uv package manager 
- **Database**: PostgreSQL with SQLAlchemy 2.0 + Alembic migrations
- **Infrastructure**: Docker Compose with Nginx reverse proxy
- **LLM**: OpenAI GPT-4.1 via AsyncOpenAI client

## Development Commands

### Frontend (in `/frontend/`)
```bash
npm run dev          # Start Vite dev server on :3000
npm run build        # Build for production (runs tsc + vite build)
npm run lint         # ESLint with TypeScript support
npm run preview      # Preview production build
```

### Backend (in `/backend/`)
```bash
uv run uvicorn app.main:app --reload --port 8000  # Start FastAPI dev server
uv run alembic upgrade head                        # Run database migrations
uv run ruff check                                  # Lint Python code
uv run ruff format                                 # Format Python code
uv run pytest                                      # Run tests
```

### Docker Environment
```bash
docker-compose up -d    # Start all services (PostgreSQL, FastAPI, Nginx)
docker-compose logs -f  # View logs
docker-compose ps       # Check service status
```

## Project Structure

```
/frontend/              # React TypeScript app
  /src/                 # React source code
  vite.config.ts        # Vite configuration with proxy to backend
  
/backend/               # FastAPI application
  /app/                 # Application code
    main.py             # FastAPI app with all routes and models
  /alembic/             # Database migrations
  pyproject.toml        # uv dependencies and ruff configuration
  
/nginx/                 # Nginx reverse proxy configuration
compose.yaml            # Docker Compose orchestration
```

## Key Architecture Patterns

### Communication
- **Development**: Vite dev server proxies `/api/*` and `/ws/*` to FastAPI backend
- **Production**: Nginx serves React app and proxies API/WebSocket to FastAPI
- **Real-time**: WebSocket streaming for chat responses at `/ws/{conversation_id}`
- **REST API**: CRUD operations for conversations and messages

### Database Schema
- `conversations`: id (UUID), title, created_at, updated_at
- `messages`: id (UUID), conversation_id (FK), role, content, created_at
- Uses UUID primary keys and proper foreign key relationships

### Technology Migration Notes
- Recently migrated from Poetry to uv for dependency management
- Uses AsyncOpenAI client for asynchronous API calls
- All code should be written in Japanese documentation style (see existing files)

## Environment Setup

### Required Environment Variables (in `/backend/.env`)
- `OPENAI_API_KEY`: OpenAI API key for GPT integration
- `DATABASE_URL`: PostgreSQL connection string

### Development Dependencies
- Node.js 20.19+ or 22.12+ for Vite
- Python 3.13 for backend
- PostgreSQL 16 for database
- uv for Python package management

## Code Conventions

### Python (Backend)
- Uses ruff for linting and formatting (line length: 88)
- Target Python version: 3.12+
- SQLAlchemy 2.0 async patterns
- FastAPI dependency injection for database sessions
- Pydantic models for validation

### TypeScript (Frontend)
- Strict TypeScript configuration
- ESLint with React hooks rules
- Minimal external dependencies (only React essentials)
- Component-based architecture

## Testing

- Backend: pytest with asyncio support
- Run tests with: `uv run pytest`