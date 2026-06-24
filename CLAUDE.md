# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 工作原则 (Work Principles)

**在开始任何非平凡工作前，必须先判断是否有对应的 skill 可以使用。** 这不是可选项，而是强制流程。

### 任务分类 → 对应 Skill

| 场景 | 必须使用的 Skill |
|------|------------------|
| 新功能、新组件、行为变更 | `brainstorming` — 先对齐意图、需求和设计 |
| 多步骤实施任务 | `writing-plans` — 先写计划再执行 |
| 有独立并行子任务 | `subagent-driven-development` — 并行派发子智能体 |
| 遇到任何 bug、测试失败、异常行为 | `systematic-debugging` — 系统化诊断，不要直接猜 |
| 编码完成后、宣布完成前 | `verification-before-completion` — 先验证再声明 |
| 需要确认改动是否生效 | `verify` — 运行项目实际观察 |
| 代码修改完成、提交前 | `code-review` — 审查正确性和简洁性 |
| 需要查库/框架/API 文档 | `context7` MCP 工具 — 不要凭记忆 |
| 复杂问题的结构化分析 | `sequential-thinking` MCP 工具 — 步步推理 |
| 设计前端界面/组件 | `frontend-design` — 高质量 UI 设计 |
| 启动项目、截图、确认效果 | `run` — 启动并观察 |
| 从 spec 写实现计划 | `writing-plans` |
| 按计划执行实现 | `executing-plans` |
| 完成开发分支 | `finishing-a-development-branch` |
| Docker 部署后验证 | `verify` + `run` |

### 简单任务例外

只有以下情况可以跳过 skill 直接执行：
- 单行/少行修复（拼写错误、明显 bug、小调整）
- 纯信息查询（"这个文件在哪"、"某某函数做什么"）
- 用户明确说"直接改不用计划"

## Commands

```bash
make help                     # Show all available commands

# Development servers (backend :8000 + frontend :5173)
make dev

# Docker operations
make build                    # Build all images (backend + frontend + sandbox)
make build-sandbox            # Build sandbox image separately
make up                       # docker compose up -d (includes arq-worker)
make down                     # docker compose down

# Testing
make test                     # All tests (backend 170 + frontend 136 = 306)
make test-backend             # cd backend && uv run pytest -v
make test-frontend            # cd frontend && npm run test
cd backend && uv run python -m pytest tests/test_core_services.py -k "orchestration" -v  # single test filter
cd backend && uv run python -m pytest tests/test_orchestration_integration.py -v         # integration tests
cd backend && uv run python -m pytest tests/test_core_services.py -k "web_search" -v     # tool-specific tests
cd frontend && npx vitest run src/__tests__/components/layout/LayoutShell.test.tsx -t "renders"  # single test

# Linting
make lint                     # Backend (ruff) + Frontend (biome)
make lint-backend             # cd backend && uv run ruff check .
make lint-frontend            # cd frontend && npx biome check .
# Ruff is NOT installed as a standalone — always use `uv run ruff`

make clean                    # Remove __pycache__, .pytest_cache, node_modules
```

## Architecture

NEXUS AI is a multi-Agent AI collaboration platform: **SPA frontend (React 18/TypeScript/Vite) + backend (Python 3.12/FastAPI)** communicating via REST + WebSocket, deployed with Docker Compose behind Nginx.

### Backend (`backend/`)

All business logic lives in `app/core/` — each module is an independent Python file. Modules communicate through global singletons, not direct imports across modules.

**Core modules** in `backend/app/core/`:

| File | Role |
|------|------|
| `config.py` | pydantic-settings: env var > .env > YAML > defaults |
| `yaml_config.py` | YAML loader: model providers, preset agents, sandbox, security rules, orchestration defaults. Contains `DEFAULT_CONFIG` dict (all defaults inline — no external `config.yaml` required) |
| `llm_gateway.py` | litellm wrapper: `chat_completion()`, `chat_completion_stream()`, `get_embedding()` |
| `ws.py` | WebSocket Hub: ConnectionManager singleton, all MessageType/ControlAction enums, ServerMessage schema |
| `security.py` | PermissionLevel(1-4), AuditLogger (append-only, no UPDATE/DELETE), RateLimiter, desensitize() |
| `conversation_service.py` | CRUD, cursor-based message pagination, export (Markdown/JSON/PDF), context window |
| `agent_service.py` | Agent CRUD, version history, rollback, 6 presets (3 undeletable original + 3 Meta-Agent), 5 templates, `auto_execute` field, `is_meta` field |
| `asset_service.py` | File upload, storage abstraction (local/S3), preview type detection |
| `tool_registry.py` | **8 tools** all with real implementations (no placeholders): CodeExecutionTool, CodeExecutionAuditTool, DatabaseQueryTool, FileReadTool, FileWriteTool, WebSearchTool (DuckDuckGo + structured results with `num_results`/`search_type`/`language` params), AgentCommunicationTool. OpenAI function calling definitions. |
| `sandbox_manager.py` | AST static code analysis (safe/warning/dangerous/blocked) + **real Docker sandbox execution** via `docker exec` into nexus-sandbox container. Falls back to mock if Docker unavailable. |
| `rag_engine.py` | DocumentChunker (semantic+token hybrid), EmbeddingService, KnowledgeBaseEngine (vector+keyword hybrid) |
| `orchestration_engine.py` | **Production-grade multi-agent orchestration** — consumed by MetaAgentRouter for Plan generation and execution. See "Orchestration System" below |
| `orchestration_repo.py` | DB persistence layer for plans, steps, and crash recovery (write-through from in-memory cache) |
| `monitor_service.py` | Hardware/container stats collection, agent activity tracking with WebSocket push |
| `database.py` | AsyncSQLAlchemy engine (asyncpg), `init_db()` called at startup, session factory. Use `get_db()` async generator for DB sessions. |
| `arq.py` | ARQ worker settings + `execute_orchestration_plan()` task for background plan execution |

**API layer** (`app/api/`):

| File | Endpoints |
|------|-----------|
| `health.py` | `GET /api/health` |
| `agents.py` | Agent CRUD REST endpoints |
| `orchestration.py` | 11 orchestration REST endpoints (CRUD + control actions). Enqueues execution via ARQ with `asyncio.create_task()` fallback. |
| `ws.py` | 3 WebSocket endpoints: `/ws/chat/{id}`, `/ws/monitor`, `/ws/agents` — handles orchestration approval, control, and retry |

**API schemas**: `backend/app/schemas/orchestration.py` contains Pydantic request/response models. New API endpoints should follow this pattern (schemas in `schemas/`, endpoint in `api/`).

**Data models** (`app/models/`): UUID PKs (`gen_random_uuid()`), TIMESTAMP defaults, JSONB for flexible fields.

**Entry point**: `app/main.py` — lifespan calls `init_db()` → `monitor_service.start_collection()` → `orchestration_engine.recover_from_db()`.

**Model naming**: litellm requires provider prefix — models are passed as `"deepseek/deepseek-chat"`, `"deepseek/deepseek-coder"`, `"anthropic/claude-sonnet-4-20250514"` etc. The prefix is stripped when looking up API keys in YAML config. Never pass bare model names to `ChatRequest`.

**Chat message routing** (`backend/app/api/ws.py` `_handle_user_message()`): Three-path routing:

1. **Meta-Agent 路径** (agent has `"agent_communication"` in tools AND `is_meta=True`): `_handle_meta_agent_message()` → `MetaAgentRouter.route()` → 决策层(triage) → 策略层(generate_plan) → 执行层(execute_plan) → 审查层(review)
2. **扁平编排路径** (agent has `"agent_communication"` but `is_meta=False`): `_handle_orchestrated_message()` → `orchestration_engine.generate_plan()` → `execute_plan()`
3. **单Agent 路径** (no `"agent_communication"`): `_stream_with_tools()` — tool-calling loop with up to 3 rounds

`MetaAgentRouter` falls back to path #2 on `NotImplementedError` or other exceptions.

**Error handling**: `backend/app/middleware/error_handler.py` defines a `AppError` hierarchy (NotFoundError, ValidationError, UnauthorizedError, ForbiddenError). All unhandled exceptions are caught and returned as `{error: {code, message, detail}}` JSON. Use `AppError` subclasses rather than raw `HTTPException` for consistency.

### Orchestration System (多智能体协作)

The most complex subsystem. Key architecture decisions:

**Execution model**: `OrchestrationEngine` is the **single source of truth** for plan creation, execution, and lifecycle. `ws.py` is a thin adapter that subscribes to engine events via callbacks.

**Plan lifecycle**: `create_plan()` / `generate_plan()` → (optional approve) → `execute_plan()` → complete/fail. Execution can be paused/resumed/cancelled mid-flight. Execution is enqueued via ARQ (Redis queue) in production with `asyncio.create_task()` fallback when Redis unavailable.

**`execute_plan()`** iterates through `parallel_groups` (topologically sorted), each group executes concurrently via `asyncio.gather`. Between groups it checks pause/cancel state via `asyncio.Event`.

**Step execution** (`_execute_step`): asyncio.wait_for timeout → retry with exponential backoff (retryable vs non-retryable error classification) → variable table write-through.

**Persistence**: Fire-and-forget DB writes after each step result and plan status change. In-memory dicts as fast-path cache, DB as durable source. `recover_from_db()` at startup marks interrupted `running`/`paused` plans as `failed`.

**REST API** (`/api/orchestrations`): POST (create), GET (list/get), PUT (edit), DELETE, /execute, /pause, /resume, /cancel, /retry-step, /variables.

**WebSocket message types**: Existing orchestration types (`plan_created`, `plan_awaiting_approval`, `plan_approved`/`plan_rejected` (C→S), `step_started`/`step_completed`/`step_failed`, `execution_paused`/`execution_resumed`/`execution_cancelled`, `retry_step` (C→S), `control`) **plus 6 Meta-Agent types** (`meta_agent_started`, `meta_agent_completed`, `meta_agent_dispatch`, `triage_result`, `layer_transition`, `plan_saved`).

**Plan generation**: `generate_plan()` calls the orchestrator LLM to decompose tasks with explicit `depends_on` indices, maps agent names to IDs, and computes correct topological `parallel_groups`.

**Variable table**: Cross-step data sharing — upstream step outputs are stored as variables, downstream steps consume them via `input_variables`.

### Tools System

All 8 tools in `tool_registry.py` have **real implementations** (no placeholders):

| Tool | Real Implementation |
|------|-------------------|
| `CodeExecutionTool` | AST audit → Docker sandbox execution via `nexus-sandbox` container |
| `CodeExecutionAuditTool` | AST static analysis (same analyzer as sandbox) |
| `DatabaseQueryTool` | Real asyncpg queries with SQL injection detection + write-statement rejection |
| `FileReadTool` | Real file I/O with path traversal protection, UTF-8 text + binary handling |
| `FileWriteTool` | Real file I/O with path traversal protection + directory auto-creation |
| `WebSearchTool` | DuckDuckGo Instant Answer API via httpx — enhanced with `num_results`, `search_type` (web/news), `language` params; structured results |
| `AgentCommunicationTool` | Real LLM calls to target agent (the only tool that makes actual LLM requests) |

**Adding a new tool**: Inherit from `BaseTool`, define a `ToolDefinition` class attribute, implement `async def execute(self, **kwargs) -> ToolResult`, and register in `ToolRegistry._register_default_tools()`.

### Sandbox Execution

`sandbox_manager.py` executes user code in the `nexus-sandbox` Docker container via docker-py:
1. AST security audit (blocked patterns rejected immediately)
2. Code packed as tar → `container.put_archive()`
3. `container.exec_run(cmd=["python", script_path], user="sandbox")`
4. Cleanup temp file after execution

**Auto-fallback**: If Docker is unavailable, mock execution kicks in (used by tests). Tests set `sb_manager._docker_available = False` to force mock path.

### Frontend (`frontend/src/`)

React 18 SPA with Redux Toolkit, React Router v6, Tailwind CSS dark mode (`class` strategy).

**Key patterns**:
- All user-facing strings use `t('key')` from `i18n.ts` — Chinese only for v1, i18n-ready architecture
- Theme persisted in localStorage via `features/theme/themeSlice.ts`
- WebSocket client (`services/ws-client.ts`) — exponential backoff reconnect (1s→2s→4s→8s, max 30s), 30s heartbeat
- `LayoutShell` renders `<Outlet />` for nested routes, syncs sidebar/right-panel tabs to route via `useLocation()`
- `useWebSocket` hook wraps `WSClient` for React lifecycle management
- Frontend tests use Vitest (NOT Jest) — `renderWithProviders()` from `src/__tests__/test-utils.tsx` wraps components with Redux Provider + MemoryRouter

**Key components**:
| Component | Covers |
|-----------|--------|
| `components/layout/LayoutShell.tsx` | 3-column shell with navigation sidebar, route-synced tabs for left (会话/资产) and right (性能/安全/Agent), blue header bar, status footer |
| `components/conversation/ConversationUI.tsx` | `ConversationSidebar` (list + new/pin/delete) + `ConversationWorkspace` (chat messages, agent selector dropdown, PlanViewer, ChatInput). Redux-driven — no hardcoded fallback data. |
| `components/conversation/PlanViewer.tsx` | DAG-style plan visualization with approval/control buttons, step status icons (○/◑/✓/✗/⏭), retry support, **LayerProgressBar** (决策▸策略▸执行▸审查). Receives WS send callbacks as props. |
| `components/agent/AgentManagerUI.tsx` | Agent grid, inline editor, version history, template library. Has `variant="compact"` for sidebar and `variant="full"` for standalone. |
| `components/asset/AssetPanel.tsx` | File browser with search, preview panel |
| `components/monitor/MonitorPanel.tsx` | Performance (hardware bars, agent activity) + Security (rate limits, audit) tabs |
| `components/code/CodeDisplay.tsx` | CodeBlock (copy/run/edit/download), ProgressBar, CodeEditorPanel |
| `components/conversation/VoiceInput.tsx` | **NEW (2026-06)** — Browser Web Speech API 语音转文字，录音动画+计时，60s自动停止，浏览器不支持时静默隐藏 |

**Orchestration state** (`features/conversation/conversationSlice.ts`):
- `OrchestrationPlan` interface with `plan_id`, `title`, `status` (7 states), `steps`, `parallel_groups`, `meta_agent_layers`, `triage_result`
- `PlanStep` interface with `status` (5 states), `output`, `error`, `retry_count`
- `MetaAgentLayerState` interface with `current_layer` (decision/strategy/execution/strategy_review), `layer_history`, `triage_result`
- Reducers: `createPlan`, `updatePlanStep`, `updatePlan`, `updatePlanStatus`, `setMetaAgentLayer`, `clearMetaAgentLayer`, `setTriageResult`, `updatePlanMetaLayers`, `updatePlanTriageResult`

### Infrastructure

- `docker-compose.yml` — **6 services**: postgres (pgvector:pg16), redis:7-alpine, backend, arq-worker, sandbox, frontend (Nginx embedded, reverse proxy to backend:8000 + `/ws/` Upgrade). Docker socket mounted on backend + arq-worker for sandbox execution (works on Linux/WSL2; comment out on native Windows).
- `frontend/nginx-frontend.conf` — reverse proxy: `/` → SPA, `/api/` → backend:8000, `/ws/` with Upgrade headers. Rate limits: 60r/m API, 10r/m LLM
- `sandbox/Dockerfile` — python:3.12-slim with numpy/pandas/matplotlib/requests/beautifulsoup4. CMD `tail -f /dev/null` keeps container alive for `docker exec`.
- `sandbox/seccomp.json` — Docker seccomp profile blocking dangerous syscalls. **Not active in docker-compose.yml by default** (causes `operation not permitted` on Windows/WSL2). Enable only on native Linux.
- `Makefile` — `dev`, `build`, `build-sandbox`, `up`, `down`, `test`, `lint`, `clean`, `help`

### Design Constraints

- **All tests mock external dependencies** (LLM API, Docker daemon, PostgreSQL, Redis) — no real service connections
- API Keys: AES-256 encrypted at rest, loaded from `.env` (`ENCRYPTION_KEY`), never exposed to frontend
- JWT reserved: `user_id` field present on models, no full auth in v1
- Audit logs: INSERT+SELECT only (no UPDATE/DELETE)
- Preset agents (数字主管/风控顾问/数据专家): undeletable
- Meta-Agent presets (智能决策/策略规划/执行调度): `is_meta=True`, `is_preset=True`, 新增于2026-06
- Code execution: AST check → confirmed → Docker sandbox with seccomp profile. Falls back to mock in dev.
- `init_db()` uses `Base.metadata.create_all` at startup (alembic configured but no migration files yet)
- Frontend responsive: hide right panel <1280px, hide left panel <768px
- Orchestration `auto_execute: true` on preset 数字主管 for backward compatibility
- DB persistence is fire-and-forget (best-effort) — engine works fully in-memory if DB is unavailable
- `config.yaml` is NOT tracked — `yaml_config.py` has complete `DEFAULT_CONFIG` dict; YAML file is for user overrides only
- Ruff is configured in `pyproject.toml` but not installed as standalone — always invoke via `uv run ruff`

### Known Gaps (as of 2026-06)

- **No auth**: `user_id` field exists on models but no JWT/session middleware is wired. All endpoints are open.
- **No Alembic migrations**: Database tables are created via `Base.metadata.create_all()` at startup. Alembic is configured but has no migration files.
- **Sandbox: mock fallback in dev**: `SandboxManager.execute()` makes real Docker calls to `nexus-sandbox` container (`tail -f /dev/null` for long-running CMD), falls back to mock when Docker client unavailable. Tests always use mock path via `_docker_available = False`.
- **WebSearchTool**: DuckDuckGo API with `num_results` (1-20), `search_type` (web/news), `language` (zh-CN/en-US) parameters; structured results with title/url/snippet/source
- **config.yaml missing**: `yaml_config.py` works entirely from `DEFAULT_CONFIG` dict. If users want to customize via config.yaml, they create it themselves. Not an error state.
