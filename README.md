# NEXUS AI

<p align="center">
  <strong>🤖 多 Agent AI 协作平台 | Multi-Agent AI Collaboration Platform</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.0-blue" alt="Version 0.1.0">
  <img src="https://img.shields.io/badge/python-3.12+-green" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/react-18-61DAFB" alt="React 18">
  <img src="https://img.shields.io/badge/docker-ready-2496ED" alt="Docker Ready">
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="License MIT">
</p>

---

## 📖 简介

NEXUS AI 是一个企业级多 Agent AI 协作平台，支持多个 AI Agent 在同一工作空间中协同工作。平台采用 **Supervisor-Worker** 架构模式，通过任务分解、并行执行、结果整合的流水线，让多个专业化 Agent 共同完成复杂任务。

### 核心能力

- 🧠 **多 Agent 协作编排** — Supervisor 分配任务，多个 Worker Agent 并行执行，支持变量传递与上下文共享
- 🔗 **多 LLM 网关** — 基于 litellm，统一接入 DeepSeek / OpenAI / Anthropic 等模型，支持流式响应
- 🔍 **RAG 知识引擎** — 文档语义分块 + 向量/关键词混合检索，为 Agent 提供知识库支持
- 🔒 **安全沙箱** — Docker + seccomp 隔离执行代码，AST 静态分析前置审核（安全/警告/危险/阻止）
- 📡 **实时通信** — WebSocket 流式推送 Agent 推理过程、系统监控数据
- 🛡️ **安全审计** — 4 级权限体系、操作审计日志（仅追加不可篡改）、API 速率限制
- 🎨 **响应式 UI** — React 18 + Tailwind CSS 深色/浅色主题，三栏布局自适应断点

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                     Browser (SPA)                       │
│   React 18 · TypeScript · Vite · Tailwind · Redux       │
└──────────────────┬──────────────────┬───────────────────┘
                   │  REST /api/*     │  WebSocket /ws/*
                   ▼                  ▼
┌─────────────────────────────────────────────────────────┐
│                    Nginx (Reverse Proxy)                 │
│        / → Frontend   /api/ → Backend   /ws/ → WS       │
└─────────────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│              Backend (FastAPI + Uvicorn)                 │
│  ┌───────────┬──────────┬───────────┬──────────────┐   │
│  │ LLM       │ Agent    │ Orchestr. │ Conversation │   │
│  │ Gateway   │ Service  │ Engine    │ Service      │   │
│  ├───────────┼──────────┼───────────┼──────────────┤   │
│  │ RAG       │ Sandbox  │ Tool      │ Security     │   │
│  │ Engine    │ Manager  │ Registry  │ + Audit      │   │
│  ├───────────┼──────────┼───────────┼──────────────┤   │
│  │ Asset     │ Monitor  │ WebSocket │ Config       │   │
│  │ Service   │ Service  │ Hub       │ Manager      │   │
│  └───────────┴──────────┴───────────┴──────────────┘   │
└──────────────┬──────────────────┬────────────────────────┘
               │                  │
               ▼                  ▼
┌──────────────────┐   ┌──────────────────┐
│ PostgreSQL 16    │   │   Redis 7        │
│ + pgvector       │   │   + ARQ Queue    │
└──────────────────┘   └──────────────────┘
```

### 后端 12 核心模块

| 模块 | 文件 | 职责 |
|------|------|------|
| **LLM Gateway** | `llm_gateway.py` | litellm 统一封装：chat completion / 流式 / embedding |
| **Agent Service** | `agent_service.py` | Agent CRUD、版本历史、回滚、3 个预设 + 5 个模板 |
| **Orchestration** | `orchestration_engine.py` | Supervisor-Worker 模式：任务规划、并行执行、变量表 |
| **Conversation** | `conversation_service.py` | 会话 CRUD、游标分页、导出（Markdown/JSON/PDF） |
| **Asset Service** | `asset_service.py` | 文件上传、存储抽象（本地/S3）、预览类型检测 |
| **RAG Engine** | `rag_engine.py` | 语义+Token 混合分块、向量+关键词混合检索 |
| **Sandbox Manager** | `sandbox_manager.py` | AST 静态分析、Docker 隔离执行、seccomp 安全策略 |
| **Tool Registry** | `tool_registry.py` | 6 个内置工具，OpenAI function-calling 格式定义 |
| **Security** | `security.py` | 4 级权限、审计日志（仅追加）、速率限制、脱敏 |
| **Monitor** | `monitor_service.py` | 硬件/容器指标采集、Agent 活动追踪 |
| **WebSocket Hub** | `ws.py` | ConnectionManager 单例，管理 3 个 WS 端点连接池 |
| **Config** | `config.py` / `yaml_config.py` | 配置优先级：环境变量 > .env > YAML > 默认值 |

### 前端 7 功能模块

| 模块 | 组件 | 功能 |
|------|------|------|
| **会话** | `ConversationUI.tsx` | 会话列表、聊天消息、@/#// 指令输入 |
| **Agent 管理** | `AgentManagerUI.tsx` | Agent 网格、行内编辑、版本历史、模板库 |
| **资产面板** | `AssetPanel.tsx` | 文件浏览、搜索、预览 |
| **监控面板** | `MonitorPanel.tsx` | 性能（硬件/Agent 活动）+ 安全（速率限制/审计） |
| **代码显示** | `CodeDisplay.tsx` | 代码块（复制/运行/编辑/下载）、进度条 |
| **布局外壳** | `LayoutShell.tsx` | 三栏布局、导航侧栏、主题切换、状态栏 |
| **共享组件** | `shared/` | ModelSelector、Toast、Modal、ExportDialog |

---

## 🚀 快速开始

### 环境要求

| 工具 | 最低版本 |
|------|----------|
| Python | 3.12+ |
| Node.js | 20+ |
| Docker + Docker Compose | 24+ |
| [uv](https://github.com/astral-sh/uv) | 最新版 |
| PostgreSQL + pgvector | 16 |
| Redis | 7 |

### 1. 克隆项目

```bash
git clone <your-repo-url> nexus-ai
cd nexus-ai
```

### 2. 配置环境变量

```bash
cp .env.example .env   # 如不存在，参考下方环境变量说明创建 .env
# 编辑 .env，填入你的 LLM API Key 等信息
```

### 3. 本地开发

```bash
# 一键启动前后端开发服务器
make dev

# Backend → http://localhost:8000
# Frontend → http://localhost:5173
```

### 4. Docker 部署

```bash
make build      # 构建所有镜像
make up         # docker compose up -d
make down       # 停止所有服务

# 访问 http://localhost:80
```

---

## ⚙️ 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `APP_ENV` | `development` | 运行环境 |
| `LOG_LEVEL` | `DEBUG` | 日志级别 |
| `DATABASE_URL` | `postgresql+asyncpg://nexus:nexus_dev@localhost:5432/nexus` | 数据库连接 |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接 |
| `LLM_API_KEYS` | `{"deepseek":"...","openai":"...","anthropic":"..."}` | LLM API Key（JSON） |
| `DEFAULT_LLM_MODEL` | `deepseek-chat` | 默认模型 |
| `ENCRYPTION_KEY` | — | AES-256 加密密钥（`openssl rand -hex 32` 生成） |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:3000` | 允许的跨域来源 |
| `SANDBOX_MEMORY_LIMIT` | `512m` | 沙箱内存限制 |
| `SANDBOX_CPU_LIMIT` | `1.0` | 沙箱 CPU 限制 |
| `SANDBOX_TIMEOUT` | `60` | 沙箱执行超时（秒） |
| `RATE_LIMIT_PER_MINUTE` | `60` | API 速率限制 |
| `RATE_LIMIT_PER_MINUTE_LLM` | `10` | LLM 接口速率限制 |
| `AUDIT_LOG_RETENTION_DAYS` | `90` | 审计日志保留天数 |

---

## 📁 项目结构

```
nexus-ai/
├── backend/                    # Python FastAPI 后端
│   ├── app/
│   │   ├── api/                # REST + WebSocket 端点
│   │   │   ├── health.py       # GET /api/health
│   │   │   └── ws.py           # /ws/chat/{id}, /ws/monitor, /ws/agents
│   │   ├── core/               # 12 个核心业务模块
│   │   │   ├── config.py       # pydantic-settings 配置
│   │   │   ├── yaml_config.py  # YAML 配置加载器
│   │   │   ├── llm_gateway.py  # LLM 网关（litellm）
│   │   │   ├── agent_service.py
│   │   │   ├── orchestration_engine.py
│   │   │   ├── conversation_service.py
│   │   │   ├── asset_service.py
│   │   │   ├── rag_engine.py
│   │   │   ├── sandbox_manager.py
│   │   │   ├── tool_registry.py
│   │   │   ├── security.py
│   │   │   ├── monitor_service.py
│   │   │   ├── ws.py
│   │   │   ├── database.py
│   │   │   ├── redis.py
│   │   │   └── arq.py
│   │   ├── models/             # SQLAlchemy ORM 模型（11 个）
│   │   ├── middleware/         # 异常处理中间件
│   │   └── main.py             # FastAPI 入口
│   ├── tests/                  # Pytest 测试
│   ├── alembic/                # 数据库迁移
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/                   # React 18 SPA 前端
│   ├── src/
│   │   ├── components/         # 7 个功能模块组件
│   │   │   ├── layout/         # LayoutShell 三栏布局
│   │   │   ├── conversation/   # ConversationUI 会话界面
│   │   │   ├── agent/          # AgentManagerUI Agent 管理
│   │   │   ├── asset/          # AssetPanel 资产面板
│   │   │   ├── monitor/        # MonitorPanel 监控面板
│   │   │   ├── code/           # CodeDisplay 代码显示
│   │   │   └── shared/         # 共享组件
│   │   ├── features/           # Redux Toolkit 状态切片（5 个）
│   │   ├── services/           # API 客户端 + WebSocket 客户端
│   │   ├── hooks/              # 自定义 Hooks
│   │   ├── lib/                # 工具函数
│   │   ├── i18n.ts             # 国际化
│   │   └── App.tsx             # 路由配置
│   ├── Dockerfile
│   └── package.json
├── sandbox/                    # 代码执行沙箱
│   ├── Dockerfile              # Python 3.12-slim + numpy/pandas/matplotlib
│   ├── seccomp.json            # 安全策略（禁止 ptrace/mount 等危险系统调用）
│   └── build.sh
├── doc/                        # 设计文档
│   ├── proposal.md             # 需求规格说明
│   ├── high-level-design.md    # 高层架构设计
│   ├── web-ui-design.md        # UI 设计文档
│   └── tasks/                  # 模块任务分解（20 个）
├── docker-compose.yml          # 6 服务编排
├── nginx.conf                  # Nginx 反向代理配置
├── Makefile                    # 开发命令
├── CLAUDE.md                   # Claude Code 指引
└── .env                        # 环境配置
```

---

## 🧪 测试

```bash
make test              # 运行全部测试
make test-backend      # 仅后端（pytest）
make test-frontend     # 仅前端（vitest）

# 运行单个测试文件
cd backend && uv run python -m pytest tests/test_core_services.py -k "rag" -v
```

---

## 🔧 常用命令

```bash
make dev              # 启动开发服务器
make build            # 构建 Docker 镜像
make up               # 启动全部服务
make down             # 停止全部服务
make lint             # 代码检查（Ruff + Biome）
make clean            # 清理生成文件
make help             # 显示所有命令
```

---

## 📦 Docker Compose 服务

| 服务 | 镜像 | 端口 | 用途 |
|------|------|------|------|
| `postgres` | `pgvector/pgvector:pg16` | 5432 | 数据库（含 PGVector 扩展） |
| `redis` | `redis:7-alpine` | 6379 | 缓存 + ARQ 任务队列 |
| `backend` | 自定义 `./backend/Dockerfile` | 8000 | FastAPI 应用 |
| `arq-worker` | 同 backend | — | 异步任务消费者 |
| `frontend` | 自定义 `./frontend/Dockerfile` | 3000 | Nginx 托管 SPA |
| `nginx` | `nginx:alpine` | 80 | 反向代理网关 |

---

## 🛡️ 安全设计

- **API Key 加密** — AES-256 静态加密存储，前端不可见
- **速率限制** — 通⽤ API 60次/分，LLM 接口 10次/分
- **审计日志** — 仅追加（INSERT+SELECT），不可篡改或删除
- **四级权限** — `READONLY` → `USER` → `ADMIN` → `SUPER_ADMIN`
- **代码沙箱** — AST 静态分析 → Docker 隔离执行 → seccomp 系统调用过滤
- **密钥轮换** — 支持定期更换 `ENCRYPTION_KEY` 重新加密

---

## 🗺️ 路线图

- [ ] **v0.2.0** — JWT 用户认证、数据库迁移（Alembic）
- [ ] **v0.3.0** — MCP 协议支持、工具插件市场
- [ ] **v0.4.0** — 多租户隔离、RBAC 权限
- [ ] **v0.5.0** — Agent 市场、社区共享
- [ ] **v1.0.0** — S3 生产存储、Kubernetes 部署方案、完整 i18n

---

## 🤝 贡献

项目当前处于早期开发阶段。欢迎提交 Issue 和 Pull Request。

开发指引请参阅 [CLAUDE.md](CLAUDE.md) 和 [doc/](doc/) 目录中的设计文档。

---

## 📄 许可证

MIT License © 2026

---

<p align="center">
  <sub>Built with ❤️ using FastAPI · React · PostgreSQL · Redis · Docker</sub>
</p>
