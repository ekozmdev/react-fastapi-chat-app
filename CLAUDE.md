# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a React + FastAPI chat application with real-time Server-Sent Events (SSE) communication and OpenAI GPT integration. The project uses a monorepo structure with clear frontend/backend separation and modern layered architecture:

- **Frontend**: React + TypeScript (Node.js 22+, Vite 7+)
  - React Router v6 with Outlet pattern for protected routes
  - Modern folder structure: pages/, auth/ (2025 best practices)
  - Biome for linting and formatting
- **Backend**: FastAPI (Python 3.13+) with layered architecture
  - Core layer: config.py, deps.py, security.py
  - Database layer: session.py with SQLAlchemy 2.0
  - Models layer: user.py, conversation.py with UUID-based design
  - Schemas layer: Pydantic validation
  - External API management: clients.py with Dependency Injection
- **Database**: PostgreSQL 16 with Alembic migrations
- **Infrastructure**: Docker Compose with Nginx reverse proxy
- **LLM**: OpenAI GPT-4o-mini via openai-agents-python SDK
  - RunItemStreamEvent for stable tool processing
  - Real-time tool detection with ResponseOutputItemAddedEvent
- **Package Management**: uv (Python), npm (Node.js)
- **Real-time Communication**: SSE with JWT authentication headers
- **Tool Integration**: get_current_time, calculate, web_search (mock)

## Development Commands

### Frontend (in `/frontend/`)
```bash
npm run dev          # Start Vite dev server on :3000
npm run build        # Build for production (runs tsc + vite build)  
npm run lint         # Biome lint with fix and error-on-warnings
npm run format       # Biome format
npm run check        # Biome check
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

### Dependency Management with uv

#### Requirements Export Commands
```bash
# Export production requirements
uv export --format requirements-txt --output-file requirements.txt

# Export development requirements (includes dev dependencies)
uv export --format requirements-txt --dev --output-file requirements_dev.txt
```

**Note**: When testing or debugging changes, the user should start servers manually using the commands above. Claude should not attempt to start development servers (frontend/backend) or view server logs during development/testing sessions. 

**User responsibilities**: Development server startup, server log monitoring, browser-based testing
**Claude responsibilities**: Test code execution (pytest), API response verification (curl), code quality checks (lint/format)

### Docker Environment
```bash
docker-compose up -d    # Start all services (PostgreSQL, FastAPI, Nginx)
docker-compose logs -f  # View logs
docker-compose ps       # Check service status
```

## Project Structure

```
/frontend/              # React TypeScript app (2025 best practices)
  /src/                 # React source code
    /auth/              # Authentication components
      AuthContext.tsx   # Authentication state management context
      LoginRoute.tsx    # Login route (authenticated redirect support)
      ProtectedRoute.tsx # Protected route (Outlet pattern)
    /pages/             # Page components (routing units)
      Chat.tsx          # Main chat page
      Login.tsx         # Login page
      NotFound.tsx      # 404 error page
    /styles/            # Stylesheets
      App.css           # Application-wide styles
      index.css         # Global styles
    App.tsx             # Routing definition (25 lines, optimized)
    main.tsx            # Entry point (BrowserRouter placement)
    types.ts            # TypeScript type definitions
    utils.ts            # Utility functions
  vite.config.ts        # Vite configuration with proxy to backend
  
/backend/               # FastAPI application
  /app/                 # Application code
    /core/              # Core infrastructure layer
      config.py         # Application settings and configuration
      constants.py      # Default values and constants
      deps.py           # Dependency injection utilities
      security.py       # JWT authentication and password handling
      utils.py          # Utility functions
    /db/                # Database layer
      session.py        # Database connection and session management
    /models/            # SQLAlchemy database models
      __init__.py       # Model imports for app-wide access
      base.py           # SQLAlchemy Base declaration
      conversation.py   # Conversation and Message models
      user.py           # User model
    /schemas/           # Pydantic data validation schemas
      auth.py           # Authentication request/response schemas
      common.py         # Common shared schemas (ChatRequest, SSEEvent)
    clients.py          # External API client management (OpenAI, Agents)
    main.py             # FastAPI app with routes and business logic
    tools.py            # Tool definitions for agent interactions
  /alembic/             # Database migrations
  /scripts/             # Management scripts (user management, etc.)
  pyproject.toml        # uv dependencies and ruff configuration
  
/nginx/                 # Nginx reverse proxy configuration
compose.yaml            # Docker Compose orchestration
```

## Key Architecture Patterns

### Communication
- **Development**: Vite dev server proxies `/api/*` to FastAPI backend
- **Production**: Nginx serves React app and proxies API to FastAPI
- **Real-time**: Server-Sent Events (SSE) streaming for chat responses at `/api/chat/stream/{conversation_id}`
  - **Standard Compliance**: HTML5 SSE specification compliant (`text/event-stream`, `event:`/`data:` format)
  - **Event Types**: Standard `event: done` completion events with backward compatibility
  - **Encoding**: UTF-8 with proper Japanese character support (`ensure_ascii=False`)
- **REST API**: CRUD operations for conversations and messages
- **Authentication**: JWT tokens via Authorization header for secure SSE connections

**Note**: Legacy WebSocket configurations (`/ws/`) remain in nginx.conf and vite.config.ts but are not actively used since migration to SSE.

### Database Schema
- `conversations`: id (String), title, user_id (FK), created_at, updated_at
- `messages`: id (String), conversation_id (FK), role, content, created_at
- `users`: id (String), email, hashed_password, is_active, created_at
- Uses String primary keys with UUID-like values and proper foreign key relationships
- Simplified schema with tool information stored directly as role:tool messages

### Architecture & Database Design Best Practices
- **Model Separation**: SQLAlchemy model separation with models/ directory structure
- **Migration Management**: Alembic dependency management and version control
- **Progressive Tool Integration**: @function_tool decorator for extensible design with role:tool message format
- **Two-stage Status Management**: Comprehensive status tracking with migration and database design best practices
- **Layered Architecture**: Zero-downtime introduction of core/ (config, auth, dependencies), schemas/ (type definitions), db/ (data layer) separation

### Frontend Architecture
- **React Router v6**: Outlet pattern for protected routes with ProtectedRoute component
- **Authentication Flow**: LoginRoute handles authenticated user redirection
- **Page Structure**: Dedicated pages/ folder for routing components (Chat, Login, NotFound)
- **State Management**: AuthContext for authentication state, optimized useEffect hooks
- **Error Handling**: Dedicated 404 page at `/not-found-error` for missing conversations
- **Screen Refresh Recovery**: Automatic conversation history restoration after page reload
- **UX Improvements**: Smart conversation deletion (preserves current session), seamless navigation
- **Code Optimization**: App.tsx simplified from 878→27 lines (92% reduction) for focused routing
- **Browser Router**: Optimally placed in main.tsx following 2025 best practices

### Advanced Frontend Features
- **UI/UX Design Patterns**:
  - Intuitive toggle UI with `<`/`>` icons and smooth CSS transitions
  - Flexbox layout optimization with margin-top: auto for bottom positioning
  - Compact button design with CSS centering best practices (margin: auto)
  - ChatGPT-style sidebar design with progressive UI simplification
- **State Management & Error Handling**:
  - Authentication timing optimization with useEffect dependency analysis
  - Infinite loop prevention and proper state transitions
  - useEffect responsibility separation for conversation restoration and URL clearing
  - Performance optimization with dependency optimization for single execution
  - Comprehensive 404 error handling with user-friendly error display and home link recovery
  - Automatic redirect on fetchConversation 404 to prevent user confusion
- **Architecture Evolution**:
  - Three-file refactoring: main.tsx (BrowserRouter), App.tsx (routing-only), ChatApp.tsx (chat functionality)
  - Pages/ folder structure with unified naming (ChatPage→Chat, LoginPage→Login)
  - ProtectedRoute Outlet pattern with nested route structure optimization

### Technology Migration Notes
- **Dependency Management**: Migrated from Poetry to uv
- **Development Environment**: Vite v7.0.5, Node.js 22+ requirements
- **Real-time Communication**: Migrated from WebSocket to Server-Sent Events (SSE)
  - **Standards Compliance**: Full HTML5 SSE specification compliance (2025 update)
  - **Event Format**: Standardized `event: name\ndata: content\n\n` format
  - **Content-Type**: Proper `text/event-stream` MIME type for optimal browser compatibility
- **LLM Integration**: Migrated from direct OpenAI API calls to openai-agents-python SDK
- **Architecture**: Implemented layered architecture with core/, db/, schemas/ separation
- **External API Management**: Implemented clients.py with Dependency Injection + Lifespan Events
- **Tool Execution**: Simplified role:tool message format with database persistence
  - Database structure simplification: removed tool_execution table and tool_metadata column
  - Unified role:tool format stored directly as messages with role='tool'
  - OpenAI Agents SDK complete integration with SSE streaming stabilization
  - Mixed sessions support: seamless tool and non-tool conversations
- **Real-time Tool Detection**: Instant tool decision detection via ResponseOutputItemAddedEvent
- **Web Search Integration**: Mock web search functionality via web_search tool
- **Frontend Modernization**: React Router v6 Outlet pattern, pages/ structure
- **Code Quality**: Technical debt elimination, code optimization, unified architecture
- Uses openai-agents SDK with Agent/ModelSettings pattern for LLM interactions
- SSE provides foundation for Function Calling/MCP tool status display
- Agent-based architecture enables multi-agent and tool integration features

### Tool Use Implementation
- **Current Implementation**: Simplified and stable tool functionality
  - **Tool Definitions**: Tools defined in `app/tools.py` with `@function_tool` decorator
  - **Available Tools**: 
    - `get_current_time`: Current timestamp retrieval
    - `calculate`: Mathematical calculations with safe character validation
    - `web_search`: Mock web search functionality (foundational implementation)
  - **Architecture**: 
    - `AVAILABLE_TOOLS` list for easy extension
    - Direct role:tool SSE streaming with real-time transmission
    - Simplified database storage as role:tool messages in messages table
    - Replaced complex tool_execution table with unified role:tool format

- **Advanced Features**: 
  - **Real-time Tool Detection**: Instant tool decision detection via ResponseOutputItemAddedEvent
    - LLM decision moment with immediate spinner display (zero artificial delay)
    - Bidirectional duplicate prevention logic for order-independent processing  
    - Comprehensive edge case handling including empty string scenarios
    - `tool_decision` SSE event type with 100% backward compatibility
  - **SDK Integration**: OpenAI Agents Python SDK with RunItemStreamEvent processing
    - High-level event processing for improved code quality (57% reduction)
    - ResponseTextDeltaEvent vs ResponseFunctionCallArgumentsDeltaEvent separation
    - Clean conversation experience with complete AI response/tool argument isolation
    - Simplified `active_tools` mapping replacing complex tracking dictionaries
  - **Mixed Session Support**: Seamless tool and non-tool conversation integration
    - Error-free mixed sessions with consistent data flow
    - Conversation continuity maintained after tool execution
    - Production-ready stability for all interaction patterns

## Environment Setup

### Required Environment Variables (in `/.env`)
- `OPENAI_API_KEY`: OpenAI API key for GPT integration
- `JWT_SECRET_KEY`: 512-bit secure key for JWT token signing (use `python3 -c "import secrets; print(secrets.token_urlsafe(64))"`)
- Individual Database Components:
  - `DB_PROTOCOL`: Database protocol (default: postgresql+psycopg)
  - `DB_HOST`: Database host (default: localhost, docker: postgres)
  - `DB_PORT`: Database port (default: 5432)
  - `DB_USER`: Database username (default: chatuser)
  - `DB_PASSWORD`: Database password (default: chatpassword - change for production)
  - `DB_NAME`: Database name (default: chatdb)

### Environment Variable Best Practices

#### Docker Compose Environment Variables
When using environment variables in Docker Compose, a **two-stage setup** is required:

1. **Docker Compose Variable Substitution**: Read variables from project root `.env` file
2. **Container Environment Variables**: Explicitly pass variables to containers via `environment` section

```yaml
# compose.yaml
services:
  fastapi:
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY}  # Substituted from .env
      DATABASE_URL: ${DATABASE_URL}      # Substituted from .env
```

#### Python Environment Variable Loading Best Practices
```python
# Recommended pattern
from dotenv import find_dotenv, load_dotenv

dotenv_path = find_dotenv()
print(f"[CONFIG] Loading .env from: {dotenv_path}")  # For debugging
load_dotenv(dotenv_path)
```

**Benefits**:
- Reliable detection of project root .env file
- Robust execution independent of current directory
- Enhanced visibility through logging output

#### Environment Variable Management Patterns

**1. Constants & Validation Pattern**
```python
# app/core/constants.py - Centralized default values
DEFAULT_OPENAI_MODEL = "gpt-4o"
DEFAULT_DB_HOST = "localhost"

# app/core/config.py - Environment variable loading with validation
def validate_required_env(key: str) -> str:
    """Validate and get required environment variable (stops app startup if unset)"""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"{key} environment variable is required")
    return value

def validate_optional_env(key: str, default: str) -> str:
    """Validate and get optional environment variable (with warning)"""
    value = os.getenv(key, default)
    if value == default:
        logging.warning(f"[CONFIG] {key} is using default value.")
    return value

class Settings:
    # Required settings (security critical)
    JWT_SECRET_KEY: str = validate_required_env("JWT_SECRET_KEY")
    OPENAI_API_KEY: str = validate_required_env("OPENAI_API_KEY")
    
    # Optional settings (with default values)
    OPENAI_MODEL: str = validate_optional_env("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
```

**2. Individual Database Components Pattern**
```python
# Individual component management
DB_PROTOCOL: str = validate_required_env("DB_PROTOCOL")
DB_HOST: str = validate_required_env("DB_HOST")
DB_PORT: int = int(validate_required_env("DB_PORT"))
DB_USER: str = validate_required_env("DB_USER")
DB_PASSWORD: str = validate_required_env("DB_PASSWORD")
DB_NAME: str = validate_required_env("DB_NAME")

@property
def DATABASE_URL(self) -> str:
    """Dynamic URL construction for centralized management"""
    return f"{self.DB_PROTOCOL}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
```

**3. Security-First Priority**
- 🔥 **Critical**: JWT_SECRET_KEY, CORS settings (authentication & security)
- 🟡 **High Priority**: Operational improvements (OpenAI, DB connections)
- 🟢 **Medium Priority**: Infrastructure standardization (PostgreSQL)
- 🔧 **Low Priority**: Debug and special-purpose settings

### Development Dependencies
- Node.js 22+ 
- Python 3.13+
- PostgreSQL 16

## Code Conventions

### Python (Backend)
- Uses ruff for linting and formatting (line length: 88)
- Target Python version: 3.13+
- SQLAlchemy 2.0 async patterns
- FastAPI dependency injection for database sessions
- Pydantic models for validation
- Layered architecture: core/, schemas/, db/, models/ separation

### TypeScript (Frontend)
- Strict TypeScript configuration
- Biome for linting and formatting with `--fix --error-on-warnings` options
- Minimal external dependencies (only React essentials)
- Component-based architecture

### Code Quality Standards
- **Technical Debt Elimination**: Complete removal of redundant files, debug comment simplification
- **Dead Code Removal**: Systematic elimination of unreachable code (case 'tool' statements, unused state variables, duplicate CSS definitions)
- **Type Definition Cleanup**: Removal of unused TypeScript interfaces (ToolCall interface, obsolete tool_calls properties)
- **CSS Architecture**: Unified color system with CSS variables replacing hardcoded values, elimination of duplicate spinner definitions
- **Conditional Logic Simplification**: Extracted should_include_message() function for improved testability
- **ID Generation Unification**: Unified generate_unique_id() function across 6 locations for consistency
- **Future Extensibility**: Easy migration to numeric IDs or other formats when needed
- **Clean Architecture**: Separation of concerns with proper layering and dependency injection

### Advanced Code Quality Practices
- **Frontend Standards**: 
  - CSS Variables (Custom Properties) for unified color management (30+ variables replacing hardcoded colors)
  - Dead code elimination (unreachable case statements, unused type definitions)
  - SVG accessibility compliance (WCAG 2.1 AA)
  - Keyboard navigation implementation
  - TypeScript safety improvements (removed non-null assertions)
- **Backend Standards**:
  - Modern type annotations (Dict→dict, List→list, Optional→T|None)
  - Safe expression evaluation with character validation before eval()
  - Unused import removal
- **Automation & Tooling**:
  - Unified code formatting with Biome/Ruff
  - Appropriate lint warning suppression techniques
- **Refactoring Strategies**:
  - Zero-downtime layered architecture introduction
  - Systematic dead code and duplicate code elimination (30% reduction achieved)
  - Import dependency tracking for code consistency
  - Unified dependency management with uv

## Testing

### Unit Testing
- Backend: pytest with asyncio support
- Run tests with: `uv run pytest`

### API Testing with curl

#### Authentication Token Acquisition
```bash
curl -X POST "http://127.0.0.1:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com", "password": "test1234"}'
```
**🚨 IMPORTANT - TOKEN USAGE**: In Claude Code environment, environment variable configuration is difficult, so obtain the access_token from the response and **ALWAYS SPECIFY TOKENS DIRECTLY** in curl commands for testing. Do not use environment variables like `$TOKEN`.

#### Basic Test Examples
```bash
# Test without tools
curl -X POST "http://127.0.0.1:8000/api/chat/stream/test-$(date +%s)" \
  -H "Authorization: Bearer [TOKEN]" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello! How are you?"}'

# Test with tools
curl -X POST "http://127.0.0.1:8000/api/chat/stream/test-$(date +%s)" \
  -H "Authorization: Bearer [TOKEN]" \
  -H "Content-Type: application/json" \
  -d '{"message": "Please tell me the current time using the get_current_time tool"}'
```

#### Mixed Session Testing (Tool and Non-Tool Conversations)
```bash
CONV_ID="mixed-test-$(date +%s)"

# 1. Non-tool conversation
curl -X POST "http://127.0.0.1:8000/api/chat/stream/$CONV_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'

# 2. Tool execution
curl -X POST "http://127.0.0.1:8000/api/chat/stream/$CONV_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Please get the current time using the get_current_time tool"}'

# 3. Calculate tool
curl -X POST "http://127.0.0.1:8000/api/chat/stream/$CONV_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Please calculate 10 + 15"}'
```

#### Data Consistency Verification
```bash
# Get conversation history
curl -X GET "http://127.0.0.1:8000/api/conversations/$CONV_ID" \
  -H "Authorization: Bearer $TOKEN"
```

#### Expected Results

**SSE streaming format (HTML5 standard compliant):**
```
Content-Type: text/event-stream

data: {"role": "tool", "content": "{\"tool_call_id\": \"call_abc123\", \"tool_name\": \"get_current_time\", \"output\": \"2025-08-02 02:56:41 UTC\", \"status\": \"success\"}", "id": "call_abc123", "timestamp": "2025-08-02T02:56:41.118683+00:00"}

data: {"role": "assistant", "content": "Current", "id": "assistant_id"}

event: done
data: {"id": "assistant_id"}

```

**Database storage format:**
```json
{
  "role": "tool",
  "content": "{\"tool_call_id\": \"call_abc123\", \"tool_name\": \"get_current_time\", \"output\": \"2025-08-02 02:56:41 UTC\", \"status\": \"success\"}"
}
```

#### Verification Points
- ✅ **SSE transmission**: `role: "tool"` events are correctly sent
- ✅ **DB storage**: Tool information is stored in JSON format
- ✅ **tool_name**: Correct tool name (not empty string)
- ✅ **Error-free**: No API errors in mixed sessions
- ✅ **Conversation continuity**: Normal conversation continues after tool execution
- ✅ **Standards compliance**: HTML5 SSE format with proper `Content-Type: text/event-stream`
- ✅ **Event format**: Standard `event: done` completion events properly parsed

## Pre-Commit Checklist

Follow these verification steps before committing:

### 1. Code Quality Checks

#### Frontend (`/frontend/`)
```bash
npm run lint         # Biome lint with fix and error-on-warnings
npm run format       # Biome format (if needed)
npm run check        # Biome check
```

#### Backend (`/backend/`)
```bash
uv run ruff check    # Ruff lint check
uv run ruff format   # Ruff format (if needed)
uv run pytest       # Run tests (when possible)
```

### 2. Staging Content Self-Review

```bash
git status           # Check changed files
git diff --staged    # Review staged content details
```

**Review Points:**
- No unintended changes included
- Understand changes to include in commit message
- No sensitive information (API keys, passwords) included
- No debug code or comments remaining

### 3. Commit Execution

After quality checks and self-review are complete, execute the commit:

```bash
git commit -m "Appropriate commit message"
```

**Note**: This process ensures codebase quality maintenance and improves review efficiency.