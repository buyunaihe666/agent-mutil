# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Development servers (backend :8000 + frontend :5173)
make dev

# Docker operations
make build                    # Build all images
make up                       # docker compose up -d
make down                     # docker compose down

# Testing
make test                     # All tests
make test-backend             # cd backend && uv run pytest -v
make test-frontend            # cd frontend && npm run test
cd backend && uv run python -m pytest tests/test_core_services.py -k "rag" -v  # single test filter

# Linting
make lint-backend             # cd backend && uv run ruff check .
make lint-frontend            # cd frontend && npx biome check .

make clean                    # Remove __pycache__, .pytest_cache, node_modules
```

## Architecture

NEXUS AI is a multi-Agent AI collaboration platform: **SPA frontend (React 18/TypeScript/Vite) + backend (Python 3.12/FastAPI)** communicating via REST + WebSocket, deployed with Docker Compose behind Nginx.

### Backend (`backend/`)

All business logic lives in `app/core/` — each module is an independent Python file with an in-memory store (mock for testing; DB-backed Repository planned for production). Modules communicate through abstract classes/global singletons, not direct imports across modules.

**12 core modules** in `backend/app/core/`:
| File | Module | Role |
|------|--------|------|
| `config.py` | M12 Config | pydantic-settings: env var > .env > YAML > defaults |
| `yaml_config.py` | M12 Config | YAML loader: model providers, preset agents, sandbox, security rules |
| `llm_gateway.py` | M1 LLM Gateway | litellm wrapper: `chat_completion()`, `chat_completion_stream()`, `get_embedding()` |
| `ws.py` | M11 WebSocket Hub | ConnectionManager singleton managing 3 WS endpoint pools + message schemas |
| `security.py` | M9 Security | PermissionLevel(1-4), AuditLogger (append-only), RateLimiter, desensitize() |
| `conversation_service.py` | M4 Conversations | CRUD, cursor-based message pagination, export (Markdown/JSON/PDF), context window |
| `agent_service.py` | M2 Agents | CRUD, version history, rollback, 3 presets (undeletable), 5 templates |
| `asset_service.py` | M5 Assets | File upload, storage abstraction (local/S3), preview type detection |
| `tool_registry.py` | M8 Tools | 6 built-in tools with OpenAI function calling definitions |
| `sandbox_manager.py` | M7 Sandbox | AST static code analysis (safe/warning/dangerous/blocked), Docker execution mock |
| `rag_engine.py` | M6 RAG | DocumentChunker (semantic+token hybrid), EmbeddingService, KnowledgeBaseEngine (vector+keyword hybrid) |
| `orchestration_engine.py` | M3 Orchestration | Supervisor-worker pattern: create_plan(), execute_plan() with parallel groups, variable table |
| `monitor_service.py` | M10 Monitor | Hardware/container stats collection, agent activity tracking |

**Data models** in `backend/app/models/`: all use UUID PKs (gen_random_uuid()), TIMESTAMP defaults, JSONB for flexible fields, pgvector Vector(1536) reserved but commented out.

**API layer**: `app/api/health.py` (GET /api/health), `app/api/ws.py` (3 WS endpoints: /ws/chat/{id}, /ws/monitor, /ws/agents with heartbeat).

**Entry point**: `app/main.py` — FastAPI app with CORS, lifespan events, exception handlers from `app/middleware/error_handler.py`.

### Frontend (`frontend/src/`)

React 18 SPA with Redux Toolkit, React Router v6, Tailwind CSS dark mode (`class` strategy), and shadcn/ui patterns (cn() utility in `lib/utils.ts`).

**Key patterns**:
- All user-facing strings use `t('key')` from `i18n.ts` — Chinese only for v1, i18n-ready architecture
- Theme persisted in localStorage via `features/theme/themeSlice.ts`
- WebSocket client (`services/ws-client.ts`) — exponential backoff reconnect (1s→2s→4s→8s, max 30s), 30s heartbeat
- `LayoutShell` renders `<Outlet />` for nested routes; nav icons use react-router NavLink

**7 frontend modules** matching backend:
| Component | Covers |
|-----------|--------|
| `components/layout/LayoutShell.tsx` | F1: 3-column shell, nav sidebar, theme toggle, status bar |
| `components/shared/ModelSelector.tsx`, `Toast.tsx` | F7: Model selector dropdown, toast notifications, WS client |
| `components/conversation/ConversationUI.tsx` | F2: Conversation list, chat messages, input area with @/#/// commands |
| `components/agent/AgentManagerUI.tsx` | F3: Agent grid, inline editor, version history, template library |
| `components/asset/AssetPanel.tsx` | F4: File browser with search, preview panel |
| `components/monitor/MonitorPanel.tsx` | F5: Performance (hardware bars, agent activity) + Security (rate limits, audit) tabs |
| `components/code/CodeDisplay.tsx` | F6: CodeBlock (copy/run/edit/download), ProgressBar, CodeEditorPanel |

### Infrastructure

- `docker-compose.yml` — 6 services: postgres (pgvector:pg16), redis:7-alpine, backend, arq-worker, frontend (multi-stage), nginx
- `nginx.conf` — reverse proxy: `/` → frontend:3000, `/api/` → backend:8000, `/ws/` with Upgrade headers
- `sandbox/Dockerfile` — python:3.12-slim with numpy/pandas/matplotlib/requests/beautifulsoup4
- `sandbox/seccomp.json` — Docker seccomp profile blocking dangerous syscalls (ptrace, mount)

### Design Constraints

- **All tests mock external dependencies** (LLM API, Docker daemon, PostgreSQL, Redis) — no real service connections
- API Keys: AES-256 encrypted at rest, loaded from `.env` (`ENCRYPTION_KEY`), never exposed to frontend
- JWT reserved: `user_id` field present on models, no full auth in v1
- Audit logs: INSERT+SELECT only (no UPDATE/DELETE)
- Preset agents (数字主管/风控顾问/数据专家): undeletable
- Code execution: AST check → confirmed → Docker sandbox with seccomp profile
- pgvector embedding dim: 1536 (runtime confirmation pending)
- alembic configured but create_all used initially
- Frontend responsive: hide right panel <1280px, hide left panel <768px
