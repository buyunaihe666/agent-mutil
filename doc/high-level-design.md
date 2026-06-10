# NEXUS AI — 多Agent协作平台 概要设计文档

> 版本：v1.0 | 日期：2026-06-09 | 状态：初稿

---

## 1. 引言

### 1.1 编写目的

本文档依据《[NEXUS AI 需求文档](proposal.md)》和《[原型图](web.html)》，对系统进行概要设计，明确：

- 系统的**模块划分**及各模块职责
- 模块之间的**依赖关系**和**接口约定**
- 关键**数据流**和**控制流**
- 模块**独立测试策略**

本文档不涉及具体代码实现、数据库语句或详细API参数——这些内容由详细设计文档和接口规格说明覆盖。

### 1.2 范围

覆盖需求文档中描述的全部功能模块：

- 多模型管理（DeepSeek / OpenAI / Claude）
- Agent系统（预设+自定义、版本管理、模板库）
- Agent协作编排（主管-工人模式、并行/串行调度）
- 工具系统（代码沙箱/SQL查询/文件操作/网络搜索/外部API/Agent通信）
- 资产管理（文件+知识库RAG）
- 安全体系（权限+审计+代码审查+脱敏+限流）
- 系统监控（GPU/内存/容器）
- 会话管理（列表/归档/导出）
- 前端完整页面体系

### 1.3 术语定义

本文档沿用需求文档第1.4节定义的全部术语。以下为关键术语的简要复述：

| 术语 | 说明 |
|------|------|
| **Agent** | 具有特定角色和能力的AI智能体 |
| **主管Agent (Orchestrator)** | 任务拆解、分配、汇总的协调者 |
| **Worker Agent** | 执行具体子任务的专业Agent |
| **会话 (Conversation)** | 用户与Agent系统之间的对话线程 |
| **资产 (Asset)** | 用户上传的文件和知识库文档 |
| **知识库 (Knowledge Base)** | 向量化文档集合，支持RAG检索 |
| **沙箱 (Sandbox)** | Docker容器隔离的代码执行环境 |
| **变量表 (Variable Table)** | 跨Agent步骤共享的键值存储 |

---

## 2. 总体设计

### 2.1 系统架构概述

系统采用**前后端分离 + 微服务风格模块**的架构。前端为SPA单页应用，后端为Python FastAPI服务，通过REST API + WebSocket双通道通信。LLM调用通过litellm网关统一管理。

```
┌───────────────────────────────────────────────────────────────┐
│                    前端 SPA (React 18 + Vite + TS)              │
│                                                                │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │Layout   │  │Conv. UI  │  │Agent Mgr │  │Monitor   │       │
│  │Shell    │  │          │  │UI        │  │Panel     │       │
│  └────┬────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       └─────────────┼─────────────┼─────────────┘              │
│                     │             │                             │
│            Redux Toolkit (状态管理)                              │
│            React Router (路由)                                   │
└─────────────────────┼─────────────┼─────────────────────────────┘
                      │ fetch + WS  │
              ┌───────┴──────┐      │
              │  Nginx :80   │      │
              └───────┬──────┘      │
                      │             │
┌─────────────────────┼─────────────┼─────────────────────────────┐
│               FastAPI 后端 (Python 3.12)                         │
│                      │             │                             │
│  ┌───────────────────┼─────────────┼──────────────────────┐     │
│  │            WebSocket Hub        │   REST API Layer      │     │
│  │  /ws/chat  /ws/monitor  /ws/agents │  9组API端点         │     │
│  └───────────────────┼─────────────┼──────────────────────┘     │
│                      │             │                             │
│  ┌───────────────────┴─────────────┴──────────────────────┐     │
│  │                    服务层 (12个模块)                     │     │
│  │                                                        │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │     │
│  │  │LLM       │ │Agent     │ │Orch.     │ │Conv.     │  │     │
│  │  │Gateway   │ │Service   │ │Engine    │ │Service   │  │     │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │     │
│  │  │Asset     │ │RAG       │ │Sandbox   │ │Tool      │  │     │
│  │  │Service   │ │Engine    │ │Manager   │ │Registry  │  │     │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │     │
│  │  │Security  │ │Monitor   │ │WS Hub    │ │Config    │  │     │
│  │  │Service   │ │Service   │ │          │ │Manager   │  │     │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │     │
│  └───────────────────────┬────────────────────────────────┘     │
│                          │                                      │
│  ┌───────────────────────┴────────────────────────────────┐     │
│  │              基础设施层                                  │     │
│  │  PostgreSQL 16   Redis 7    Docker    文件系统           │     │
│  │  (+pgvector)     (+arq)     (docker-py)                 │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈总览

| 层次 | 技术选型 |
|------|----------|
| **前端框架** | React 18+ (TypeScript 5+) |
| **构建工具** | Vite 5+ |
| **UI样式** | Tailwind CSS 3+ + shadcn/ui |
| **状态管理** | Redux Toolkit |
| **前端路由** | React Router v6 |
| **代码高亮** | Shiki |
| **Markdown** | react-markdown + remark-gfm + rehype-highlight |
| **虚拟滚动** | react-virtuoso |
| **后端框架** | FastAPI (Python 3.12) |
| **ORM** | SQLAlchemy 2.0 (async) + asyncpg |
| **数据库** | PostgreSQL 16 + pgvector 0.7+ |
| **缓存/队列** | Redis 7 + arq |
| **LLM网关** | litellm |
| **容器运行时** | docker-py |
| **配置管理** | .env + YAML → pydantic-settings |
| **代码规范(Python)** | Ruff |
| **代码规范(前端)** | Biome |
| **日志** | structlog → stdout → Docker日志驱动 |
| **异常追踪** | Sentry (前端) |
| **测试(Python)** | pytest + pytest-asyncio |
| **测试(前端)** | Vitest |
| **部署** | Docker Compose v2 + Nginx |

### 2.3 系统部署视图

```
Docker Compose 服务编排:

┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ postgres │   │  redis   │   │ backend  │   │  arq-    │   │ frontend │
│ :5432    │   │  :6379   │   │  :8000   │   │  worker  │   │  :3000   │
└────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘
     │              │              │              │              │
     └──────────────┴──────────────┴──────────────┴──────────────┘
                                    │
                              ┌─────┴─────┐
                              │   nginx   │
                              │   :80     │
                              └───────────┘
```

各服务通过Docker网络互联。Nginx作为唯一对外端口（:80），将请求反向代理到前端（:3000）和后端（:8000），并处理WebSocket升级。

---

## 3. 模块划分

### 3.1 模块总览

#### 后端模块（12个）

| # | 模块标识 | 模块名称 | 核心职责 | 层级 |
|---|---------|---------|---------|------|
| M1 | `llm_gateway` | LLM网关 | 多模型路由、流式转发、API Key管理、Token统计 | 基础设施服务 |
| M2 | `agent_service` | Agent服务 | Agent CRUD、Persona、版本管理、模板库 | 核心业务 |
| M3 | `orchestration_engine` | 任务编排引擎 | 任务拆解调度、并行/串行分析、变量表、断点恢复 | 核心业务 |
| M4 | `conversation_service` | 会话服务 | 会话管理、消息持久化、上下文窗口、导出 | 核心业务 |
| M5 | `asset_service` | 资产管理 | 文件上传/存储/预览、存储抽象层 | 基础设施服务 |
| M6 | `rag_engine` | 知识库引擎 | 文档分块、Embedding向量化、混合检索、引用溯源 | 领域服务 |
| M7 | `sandbox_manager` | 沙箱管理 | Docker容器生命周期、AST代码分析 | 基础设施服务 |
| M8 | `tool_registry` | 工具注册中心 | 工具基类、注册/发现、function calling定义生成 | 基础设施服务 |
| M9 | `security_service` | 安全审计 | 权限控制、审计日志、数据脱敏、限流 | 横切关注点 |
| M10 | `monitor_service` | 系统监控 | 硬件采集、容器监控、实时推送 | 横切关注点 |
| M11 | `ws_hub` | WebSocket中心 | 端点管理、心跳/重连、消息路由 | 通信基础设施 |
| M12 | `config_manager` | 配置管理 | 环境变量+YAML加载、配置校验 | 基础设施服务 |

#### 前端模块（7个）

| # | 模块标识 | 模块名称 | 核心职责 | 对应区域 |
|---|---------|---------|---------|---------|
| F1 | `layout_shell` | 布局框架 | 三栏容器、标题栏/状态栏、主题切换 | 全局 |
| F2 | `conversation_ui` | 会话交互 | 会话列表、聊天区、消息气泡、输入区 | 主聊天界面 |
| F3 | `agent_manager_ui` | Agent管理 | Agent列表/编辑、版本历史、模板库 | Agent页面群 |
| F4 | `asset_ui` | 资产面板 | 文件浏览/搜索/预览 | 左侧栏资产Tab |
| F5 | `monitor_panel` | 监控面板 | 性能/安全Tab、Agent活动列表 | 右侧面板 |
| F6 | `code_display` | 代码展示 | Shiki代码块、编辑面板、进度条 | 聊天嵌入 |
| F7 | `shared_components` | 共享组件 | 模型选择器、导出对话框、Modal等 | 跨模块复用 |

### 3.2 模块依赖关系图

```
后端模块依赖（箭头方向 = "依赖/调用"）:

                    ┌──────────────────────────────┐
                    │      Orchestration Engine     │
                    │           (M3)                │
                    └──────────┬───────┬───────────┘
                      │        │       │
            ┌─────────┘        │       └──────────┐
            ▼                  ▼                   ▼
    ┌──────────────┐  ┌──────────────┐   ┌──────────────┐
    │Agent Service │  │Conv. Service │   │Tool Registry │
    │    (M2)      │  │    (M4)      │   │    (M8)      │
    └──────┬───────┘  └──────┬───────┘   └──┬───────┬───┘
           │                 │               │       │
           ▼                 │               ▼       ▼
    ┌──────────────┐         │       ┌──────────┐ ┌──────────┐
    │ LLM Gateway  │◄────────┘       │Sandbox   │ │RAG Engine│
    │    (M1)      │                 │Manager(M7│ │   (M6)   │
    └──────┬───────┘                 └────┬─────┘ └────┬─────┘
           │                              │            │
           ▼                              ▼            ▼
    ┌──────────────────────────────────────────────────────┐
    │           基础设施: Config(M12) / Asset Service(M5)    │
    └──────────────────────────────────────────────────────┘
                              │
    ┌─────────────────────────┴──────────────────────────┐
    │  横切关注点: Security Service(M9) / Monitor(M10)    │
    │  通信层: WebSocket Hub(M11)                         │
    └────────────────────────────────────────────────────┘


前端模块依赖:

    ┌──────────────────────────────────────┐
    │         Layout Shell (F1)             │
    │   TitleBar + StatusBar + ThemeToggle  │
    └──────────────┬───────────────────────┘
                   │
    ┌──────────────┼───────────────────────┐
    │              │                       │
    ▼              ▼                       ▼
┌──────────┐ ┌──────────┐          ┌──────────┐
│Conv. UI  │ │Asset UI  │          │Monitor   │
│  (F2)    │ │  (F4)    │          │Panel (F5)│
└────┬─────┘ └──────────┘          └──────────┘
     │
     ▼
┌──────────┐    ┌──────────────┐    ┌──────────────┐
│Code      │    │Shared Comp.  │    │Agent Mgr UI  │
│Display   │    │    (F7)      │    │    (F3)      │
│ (F6)     │    └──────────────┘    └──────────────┘
└──────────┘
```

### 3.3 模块依赖原则

1. **单向依赖**：上层模块依赖下层，下层模块不感知上层模块（通过回调、事件或观察者模式解耦）
2. **接口隔离**：模块间通过Python抽象基类（ABC）定义的接口契约通信，不直接导入实现类
3. **横切模块以拦截器/中间件模式注入**：Security Service和WS Hub通过FastAPI中间件/依赖注入融入请求管道，不影响业务模块的内聚性
4. **模块可独立部署**：每个模块在开发阶段可独立运行单元测试，通过Mock/Stub隔离外部依赖

---

## 4. 后端模块详细设计

### 4.1 LLM网关模块 (`llm_gateway`)

**模块职责：** 封装对 litellm 的调用，为上层提供统一的多模型LLM访问接口。

**核心功能：**

| 功能 | 说明 |
|------|------|
| 模型路由 | 根据请求中指定的模型ID，路由到对应提供商的API |
| 流式转发 | 将 litellm 的 stream 响应以 async generator 逐块返回 |
| API Key管理 | AES-256加密存储Key，支持多Key轮换，速率限制时自动切换 |
| Token统计 | 记录每次调用的 prompt/completion tokens，按会话/Agent/模型维度聚合 |
| 超时控制 | 模型级超时（DeepSeek 120s / OpenAI 120s / Claude 180s）+ Agent级超时，先到为准 |
| 速率限制 | 对接模型提供商的rate limit，前端限流由Security Service负责 |

**模块接口（Abstract）：**

```python
class LLMGateway(ABC):
    async def chat_completion(self, request: ChatRequest) -> ChatResponse: ...
    async def chat_completion_stream(self, request: ChatRequest) -> AsyncGenerator[Delta, None]: ...
    async def get_embedding(self, text: str, model: str) -> list[float]: ...
    def get_available_models(self) -> list[ModelInfo]: ...
    def get_token_usage(self, filters: TokenUsageFilter) -> TokenUsageReport: ...
```

**依赖关系：**
- 上层调用者：Agent Service, RAG Engine
- 下层依赖：litellm, Config Manager（获API Key和endpoint配置）
- 不依赖其他业务模块

---

### 4.2 Agent服务模块 (`agent_service`)

**模块职责：** 管理Agent的全生命周期——创建、配置、版本、模板、启用/禁用。

**核心功能：**

| 功能 | 说明 |
|------|------|
| Agent CRUD | 创建/查询/更新/删除Agent。系统预设Agent（数字主管/风控顾问/数据专家）不可删除 |
| Persona管理 | 每个Agent有独立的System Prompt、Emoji头像、语气风格 |
| 版本管理 | System Prompt或配置变更时自动创建快照，支持浏览/对比/回滚 |
| 模板库 | 预设Agent模板（市场分析/代码审查/文档撰写等），用户可一键基于模板创建Agent |
| 工具关联 | 每个Agent记录启用的工具列表（JSONB字段），由Tool Registry在调用时动态注入 |
| 权限赋值 | 用户为Agent设置1-4级权限，创建时校验权限范围 |

**模块接口（Abstract）：**

```python
class AgentService(ABC):
    # CRUD
    async def list_agents(self, filters: AgentFilter) -> list[AgentInfo]: ...
    async def get_agent(self, agent_id: str) -> AgentDetail: ...
    async def create_agent(self, data: AgentCreate) -> AgentDetail: ...
    async def update_agent(self, agent_id: str, data: AgentUpdate) -> AgentDetail: ...
    async def delete_agent(self, agent_id: str) -> None: ...
    async def toggle_agent(self, agent_id: str, active: bool) -> None: ...
    # 版本管理
    async def list_versions(self, agent_id: str) -> list[AgentVersion]: ...
    async def get_version(self, agent_id: str, version: int) -> AgentVersion: ...
    async def rollback_version(self, agent_id: str, version: int) -> AgentDetail: ...
    # 模板
    async def list_templates(self) -> list[AgentTemplate]: ...
    async def instantiate_template(self, template_id: str) -> AgentDetail: ...
```

**依赖关系：**
- 上层调用者：Orchestration Engine, Conversation Service
- 下层依赖：数据库（agents/agent_versions表）、LLM Gateway（生成默认System Prompt时可选调用）
- 不依赖其他业务模块

---

### 4.3 任务编排引擎 (`orchestration_engine`)

**模块职责：** 实现主管-工人协作模式的核心逻辑——任务拆解→依赖分析→并行/串行调度→结果汇总。

**核心功能：**

| 功能 | 说明 |
|------|------|
| 任务拆解 | 调用数字主管Agent（LLM），将用户自然语言任务拆解为结构化子任务列表 |
| 依赖分析 | 分析子任务间的依赖关系（子任务B需要子任务A的输出），标记depends_on |
| 并行/串行判断 | 无依赖子任务→并行执行（arq异步任务）；有依赖→串行执行 |
| 执行计划生成 | 生成完整执行计划（步骤、分配Worker、依赖图），通过WS推送前端展示 |
| Worker调度 | 通过arq任务队列分发子任务，按会话限制并发（默认最多3个并行） |
| 主管优先 | 数字主管的编排任务在arq队列中享有最高优先级 |
| 变量表管理 | 维护跨步骤的键值存储，Agent可读写共享数据（类似Jupyter变量机制） |
| 断点恢复 | 任务状态实时写入数据库，支持暂停/恢复/取消，浏览器关闭后后端继续执行 |
| 人工介入 | 确认模式下，关键步骤（代码执行/数据库写入）需用户确认后执行 |
| 结果汇总 | 所有子任务完成后，调用数字主管汇总结果，生成最终回复 |

**模块接口（Abstract）：**

```python
class OrchestrationEngine(ABC):
    async def start_orchestration(self, conversation_id: str, user_message: Message) -> Orchestration: ...
    async def pause(self, orchestration_id: str) -> None: ...
    async def resume(self, orchestration_id: str) -> None: ...
    async def cancel(self, orchestration_id: str) -> None: ...
    async def confirm_step(self, orchestration_id: str, step_index: int) -> None: ...
    async def get_status(self, conversation_id: str) -> OrchestrationStatus: ...
    # 变量表
    async def get_variables(self, conversation_id: str) -> dict[str, Variable]: ...
    async def set_variable(self, conversation_id: str, key: str, value: Any, agent_id: str) -> None: ...
```

**依赖关系：**
- 上层调用者：WebSocket Hub（用户消息触发编排），Conversation Service
- 下层依赖：Agent Service, LLM Gateway, Conversation Service, Tool Registry, Redis(arq)
- 被Security Service拦截：步骤执行前检查Agent权限级别

---

### 4.4 会话服务 (`conversation_service`)

**模块职责：** 管理会话生命周期、消息存储与查询、上下文窗口。

**核心功能：**

| 功能 | 说明 |
|------|------|
| 会话CRUD | 创建（LLM自动生成标题）/查询/更新（重命名/置顶/归档）/删除 |
| 消息管理 | 消息存储（Redis缓冲 + 批量写PostgreSQL）、cursor-based分页查询（默认50条/页） |
| 上下文窗口 | 混合策略：最近N条完整保留（滑动窗口）+ 超出部分LLM摘要压缩 |
| 消息编辑 | 用户编辑已发送消息，标记is_edited，触发Agent重新生成回复 |
| 重新生成 | 点击按钮重新生成Agent回复，记录parent_message_id关系链 |
| 会话导出 | 支持导出为Markdown/PDF/JSON格式 |

**模块接口（Abstract）：**

```python
class ConversationService(ABC):
    # 会话
    async def list_conversations(self, filters: ConvFilter) -> list[ConversationSummary]: ...
    async def create_conversation(self, first_message: str) -> Conversation: ...
    async def get_conversation(self, conv_id: str) -> Conversation: ...
    async def update_conversation(self, conv_id: str, data: ConvUpdate) -> Conversation: ...
    async def delete_conversation(self, conv_id: str) -> None: ...
    async def export_conversation(self, conv_id: str, format: str) -> bytes: ...
    # 消息
    async def get_messages(self, conv_id: str, cursor: str | None, limit: int) -> MessagePage: ...
    async def edit_message(self, msg_id: str, new_content: str) -> Message: ...
    async def regenerate_response(self, conv_id: str, msg_id: str) -> None: ...
    # 上下文
    async def build_context(self, conv_id: str, agent_id: str, max_tokens: int) -> ContextPayload: ...
```

`build_context` 的上下文隔离策略：
- 当 `agent_id` 是数字主管 → 返回完整会话上下文（全量历史 + 摘要）
- 当 `agent_id` 是Worker Agent → 仅返回分配给该Worker的子任务上下文 + 变量表引用

**依赖关系：**
- 上层调用者：Orchestration Engine, WebSocket Hub
- 下层依赖：数据库（conversations/messages表）、Redis（消息缓冲）
- 不依赖其他业务模块

---

### 4.5 资产管理 (`asset_service`)

**模块职责：** 文件的上传、存储、预览、管理。通过存储抽象层支持本地文件系统和未来S3切换。

**核心功能：**

| 功能 | 说明 |
|------|------|
| 文件上传 | 接收多格式文件（CSV/Excel/JSON/TXT/PNG/JPG/PDF/Word），单文件≤50MB |
| 存储抽象 | 定义StorageBackend接口，第一版实现LocalStorage，预留S3Storage |
| 文件预览 | 图片缩略图、PDF内嵌查看、文本/代码高亮预览、CSV/Excel表格渲染 |
| 文件管理 | 浏览、搜索、标签分类、下载、删除 |
| Agent访问 | 通过Tool Registry的文件操作工具，Agent可读取资产目录中的文件 |

**模块接口（Abstract）：**

```python
class AssetService(ABC):
    async def upload(self, file: UploadFile, tags: list[str] | None) -> Asset: ...
    async def list_assets(self, filters: AssetFilter) -> list[Asset]: ...
    async def get_asset(self, asset_id: str) -> AssetDetail: ...
    async def download(self, asset_id: str) -> tuple[bytes, str]: ...  # (content, content_type)
    async def get_preview(self, asset_id: str) -> PreviewData: ...
    async def delete_asset(self, asset_id: str) -> None: ...
    async def reprocess(self, asset_id: str) -> None: ...  # 重新处理知识库文档

class StorageBackend(ABC):
    async def save(self, path: str, data: bytes) -> str: ...
    async def read(self, path: str) -> bytes: ...
    async def delete(self, path: str) -> None: ...
    async def exists(self, path: str) -> bool: ...
```

**依赖关系：**
- 上层调用者：RAG Engine（获取文档进行向量化）, Tool Registry（文件操作工具）
- 下层依赖：文件系统（当前）/ S3（预留）
- 不依赖其他业务模块

---

### 4.6 知识库引擎 (`rag_engine`)

**模块职责：** 文档处理流水线（解析→分块→向量化→存储）和RAG检索。

**核心功能：**

| 功能 | 说明 |
|------|------|
| 文档解析 | 解析PDF/Word/Markdown/TXT，提取纯文本内容 |
| 混合分块 | 优先按段落/标题语义分块，超长段落(>512token)按固定大小切割，相邻块10%重叠 |
| Embedding | 调用DeepSeek Embedding API（通过LLM Gateway）生成向量 |
| 向量存储 | 通过pgvector存储向量，创建ivfflat索引 |
| 混合检索 | 向量相似度(Cosine) + 关键词匹配(BM25/PostgreSQL full-text search)加权融合 |
| 引用溯源 | Agent回答中标注信息来源文档和片段 |

**模块接口（Abstract）：**

```python
class RAGEngine(ABC):
    async def index_document(self, asset_id: str) -> None: ...  # 完整流水线
    async def reindex_document(self, asset_id: str) -> None: ...
    async def search(self, query: str, top_k: int = 5) -> list[ChunkResult]: ...
    async def get_chunks(self, asset_id: str) -> list[Chunk]: ...
    async def delete_chunks(self, asset_id: str) -> None: ...
```

**依赖关系：**
- 上层调用者：Tool Registry（知识库检索工具）
- 下层依赖：LLM Gateway（Embedding API）、Asset Service（获取文档）、pgvector
- 不依赖其他业务模块

---

### 4.7 沙箱管理 (`sandbox_manager`)

**模块职责：** 管理Docker沙箱容器的创建→执行→销毁全生命周期，以及代码安全审查。

**核心功能：**

| 功能 | 说明 |
|------|------|
| 容器管理 | 每次代码执行创建独立临时容器（docker-py），执行完立即销毁 |
| 自建镜像 | 预装numpy/pandas/matplotlib/requests/beautifulsoup4，支持动态pip install |
| AST静态分析 | 使用Python ast模块解析代码AST，检测危险节点（os.system/subprocess/eval/exec等） |
| 安全限制 | 网络策略（允许出站，禁止内网）、内存512MB、CPU 1核、执行超时60秒、seccomp profile |
| 代码审查 | 危险操作标记为「需用户确认」，安全代码直接执行，执行后分析异常行为 |
| 文件挂载 | 只读挂载用户文件，可写临时目录，执行后自动清理 |

**模块接口（Abstract）：**

```python
class SandboxManager(ABC):
    async def execute_code(self, request: CodeExecRequest) -> CodeExecResult: ...
    async def build_image(self) -> str: ...  # 构建沙箱镜像
    async def cleanup_containers(self) -> None: ...  # 清理残留容器

class CodeAnalyzer(ABC):
    def analyze(self, code: str) -> CodeAnalysisResult: ...  # AST静态分析
```

`CodeExecRequest` 包含：代码文本、可选文件路径、可选变量表键引用。
`CodeExecResult` 包含：stdout/stderr、生成文件列表、写入变量表的数据、分析报告。

**依赖关系：**
- 上层调用者：Tool Registry（代码执行工具）
- 下层依赖：docker-py、Docker daemon
- 被Security Service拦截：执行前调用AST分析，危险代码需用户确认

---

### 4.8 工具注册中心 (`tool_registry`)

**模块职责：** 管理Agent可用工具的注册、发现和function calling定义生成。

**核心功能：**

| 功能 | 说明 |
|------|------|
| 工具注册 | 通过Python类注册工具，定义工具的name/description/parameters schema |
| function calling生成 | 根据注册的工具类，自动生成符合OpenAI function calling格式的tool definitions |
| 动态注入 | Agent创建/执行时，根据其tools配置字段动态注入对应的tool definitions到LLM请求 |
| 运行时扩展 | Agent可在对话中请求启用新工具（需用户确认） |
| 统一调度 | 提供统一的工具调用入口，根据tool name路由到对应执行器 |

**已注册工具清单：**

| 工具ID | 工具名称 | 执行器 | 说明 |
|--------|---------|--------|------|
| `code_exec` | 代码执行 | Sandbox Manager | Python代码沙箱执行 |
| `db_query` | 数据库查询 | 内置（SQLAlchemy） | 只读SELECT自动允许，写操作需确认 |
| `file_read` | 文件读取 | Asset Service | 读取资产目录中的文件 |
| `file_write` | 文件写入 | Asset Service | 生成文件存入资产库 |
| `web_search` | 网络搜索 | 阿里云IQS MCP | 互联网信息搜索 |
| `api_call` | 外部API | 内置（HTTP客户端） | 调用白名单内的外部API |
| `agent_comm` | Agent通信 | Orchestration Engine | Agent间消息传递和任务委派 |

**模块接口（Abstract）：**

```python
class ToolRegistry(ABC):
    def register(self, tool: BaseTool) -> None: ...
    def get_tool(self, name: str) -> BaseTool: ...
    def get_definitions_for_agent(self, agent_id: str) -> list[ToolDefinition]: ...
    async def execute(self, tool_name: str, params: dict, context: ExecutionContext) -> ToolResult: ...

class BaseTool(ABC):
    @property
    def name(self) -> str: ...
    @property
    def description(self) -> str: ...
    @property
    def parameters(self) -> dict: ...  # JSON Schema
    async def execute(self, params: dict, context: ExecutionContext) -> ToolResult: ...
```

**依赖关系：**
- 上层调用者：Orchestration Engine（Worker执行时获取工具定义并执行工具调用）
- 下层依赖：Sandbox Manager, RAG Engine, Asset Service, 数据库
- 被Security Service拦截：工具执行前检查Agent权限级别

---

### 4.9 安全审计 (`security_service`)

**模块职责：** 贯穿全系统的横切安全关注点——权限控制、审计记录、数据脱敏、限流。

**核心功能：**

| 功能 | 说明 |
|------|------|
| 权限控制 | Agent 4级权限体系（Level 1只读→Level 4管理），操作前校验Agent权限是否匹配所需权限 |
| 审计日志 | 记录所有Agent操作（操作类型/发起Agent/时间/参数/结果/会话ID），不可删除仅追加，支持筛选导出 |
| 数据脱敏 | 自动检测输出中的敏感数据（手机号/身份证/银行卡/API Key/邮箱），自动脱敏（如138****1234） |
| 双层限流 | IP限流（FastAPI middleware + Redis滑动窗口）+ API Key限流（litellm网关控制） |
| 输入过滤 | SQL注入/XSS过滤 |

**权限-操作对照表：**

| 操作 | 所需权限 | 说明 |
|------|---------|------|
| 读取消息/会话/Agent信息 | Level 1 | 只读 |
| 执行SQL查询 | Level 2 | 分析 |
| 代码分析（AST only） | Level 2 | 分析 |
| 文件读取 | Level 2 | 分析 |
| 网络搜索 | Level 2 | 分析 |
| 知识库检索 | Level 2 | 分析 |
| 代码执行 | Level 3 | 操作（需AST预审） |
| 文件写入 | Level 3 | 操作 |
| SQL写操作 | Level 3 | 操作（需确认） |
| API调用 | Level 3 | 操作 |
| Agent通信（委派/通知） | Level 3 | 操作 |
| 管理Agent配置 | Level 4 | 管理 |
| 管理模型提供商 | Level 4 | 管理 |

**模块接口（Abstract）：**

```python
class SecurityService(ABC):
    # 权限
    def check_permission(self, agent_id: str, required_level: int) -> bool: ...
    # 审计
    async def log_action(self, event: AuditEvent) -> None: ...
    async def query_logs(self, filters: AuditFilter) -> list[AuditRecord]: ...
    async def export_logs(self, filters: AuditFilter) -> bytes: ...
    # 脱敏
    def sanitize(self, text: str) -> str: ...
    # 限流
    async def check_rate_limit(self, identifier: str) -> bool: ...
```

**集成方式：**
- 权限检查：通过FastAPI依赖注入（`Depends(check_permission)`）在API层拦截
- 审计记录：通过事件钩子——各服务模块在操作前后发出AuditEvent，Security Service异步消费写入数据库
- 数据脱敏：在WebSocket消息推送到前端之前，作为输出过滤器调用
- 限流：FastAPI middleware层拦截所有HTTP请求

**依赖关系：**
- 被几乎所有业务模块依赖（作为横切关注点注入）
- 下层依赖：数据库（audit_logs表）、Redis（限流窗口）

---

### 4.10 系统监控 (`monitor_service`)

**模块职责：** 采集系统硬件资源和Docker容器的运行数据，通过WebSocket推送到前端。

**核心功能：**

| 功能 | 说明 |
|------|------|
| GPU监控 | 采集GPU显存/利用率/温度（通过NVIDIA Container Toolkit），无GPU环境优雅降级 |
| 系统内存 | 采集系统总内存/已用内存/使用率 |
| Docker容器监控 | 采集运行中容器列表及CPU/内存/网络IO |
| 定时采集 | 每5秒采集一次系统指标 |
| WebSocket推送 | 通过/ws/monitor推送到前端右侧面板 |
| 异常告警 | 容器异常状态检测和通知 |

**模块接口（Abstract）：**

```python
class MonitorService(ABC):
    async def get_hardware_stats(self) -> HardwareStats: ...
    async def get_container_stats(self) -> list[ContainerStats]: ...
    async def start_collection_loop(self) -> None: ...  # 后台定时采集+推送
    async def stop_collection(self) -> None: ...
```

**依赖关系：**
- 上层调用者：WebSocket Hub（推送监控数据）
- 下层依赖：系统API（psutil）、Docker daemon
- 不依赖其他业务模块

---

### 4.11 WebSocket中心 (`ws_hub`)

**模块职责：** 管理三大WebSocket端点、处理连接生命周期、消息路由。

**端点列表：**

| 路径 | 方向 | 说明 |
|------|------|------|
| `/ws/chat/{conversation_id}` | 双向 | 聊天消息流——客户端发用户消息，服务端推流式回复/任务计划/步骤状态/代码进度/变量表更新 |
| `/ws/monitor` | 服务端→客户端 | 硬件监控数据推送（5秒间隔） |
| `/ws/agents` | 服务端→客户端 | Agent状态变更推送（idle/working/blocked/error） |

**核心功能：**

| 功能 | 说明 |
|------|------|
| 连接管理 | 接受WebSocket连接，验证会话ID，维护连接池 |
| 心跳机制 | 30秒ping/pong，超时断开自动清理 |
| 消息路由 | 客户端消息按type字段路由到对应处理器；服务端消息按topic推送到对应连接 |
| 重连支持 | 服务端维护连接状态，客户端断开后重连可恢复消息流（通过Redis缓存未确认消息） |
| 错误处理 | 统一错误码和recoverable标记 |

**消息类型汇总（客户端→服务端）：**

| type | 说明 | 处理器 |
|------|------|--------|
| `user_message` | 用户发送消息（含@Agent/#文件//命令/附件） | Orchestration Engine |
| `confirm_action` | 用户确认/拒绝高危操作 | Orchestration Engine |
| `control` | 暂停/恢复/取消任务 | Orchestration Engine |
| `ping` | 心跳 | WS Hub自身 |

**消息类型汇总（服务端→客户端）：**

| type | 说明 | 来源模块 |
|------|------|---------|
| `text_delta` | LLM流式文本增量 | LLM Gateway |
| `task_plan` | 任务执行计划 | Orchestration Engine |
| `step_status` | 步骤状态变更 | Orchestration Engine |
| `code_progress` | 代码执行进度 | Sandbox Manager |
| `action_result` | 操作结果卡片（含操作按钮） | Orchestration Engine |
| `variable_update` | 变量表更新 | Orchestration Engine |
| `agent_status` | Agent状态变更 | Agent Service |
| `done` | 任务完成 + Token用量 | Orchestration Engine |
| `error` | 错误信息 | 各服务模块 |
| `pong` | 心跳响应 | WS Hub自身 |
| `hardware_stats` | 硬件监控数据 | Monitor Service |

**依赖关系：**
- 上层调用者：前端WebSocket客户端
- 下层依赖：Orchestration Engine, Agent Service, Monitor Service, Conversation Service, LLM Gateway
- 被Security Service拦截：消息输入过滤

---

### 4.12 配置管理 (`config_manager`)

**模块职责：** 统一管理应用配置，支持.env + YAML混合加载，通过pydantic-settings进行类型校验。

**配置域：**

| 配置域 | 来源 | 说明 |
|--------|------|------|
| 数据库连接 | `.env` | DATABASE_URL, REDIS_URL |
| API Keys | `.env` | 各LLM提供商的API Key |
| 模型配置 | `YAML` | 提供商列表、模型列表、超时/限流参数 |
| Agent预设 | `YAML` | 预设Agent的System Prompt、工具集、权限 |
| 沙箱配置 | `YAML` | 内存限制/CPU限制/超时/seccomp文件路径 |
| 安全配置 | `YAML` | 脱敏正则规则、限流参数 |
| 文件存储 | `YAML` | 存储后端类型、本地路径/S3配置 |
| Embedding | `YAML` | Embedding模型ID、向量维度 |
| WebSocket | `YAML` | 心跳间隔、重连退避参数 |

**依赖关系：**
- 被所有模块依赖（提供配置值）
- 不依赖任何业务模块

---

## 5. 数据流设计

### 5.1 用户对话主流程

```
用户输入(富文本: @Agent, #文件, /命令)
    │
    ▼
[WS Hub] 接收 user_message
    │
    ▼
[Conversation Service] 存储用户消息
    │
    ▼
[Orchestration Engine] 启动编排
    │
    ├─→ [LLM Gateway] 调用数字主管 → 拆解任务
    │       │
    │       ▼
    │   [WS Hub → 前端] 推送 task_plan
    │
    ├─→ [全自动模式] 或 [确认模式: 等待用户确认]
    │
    ▼
[Orchestration Engine] 依赖分析 → 并行/串行判断
    │
    ├── 并行子任务 ──→ [arq Queue]
    │       │
    │       ├─→ Worker A → [LLM Gateway] + [Tool Registry]
    │       ├─→ Worker B → [LLM Gateway] + [Tool Registry]
    │       └─→ Worker C → [LLM Gateway] + [Tool Registry]
    │
    └── 串行子任务 ──→ Worker X → 等待结果 → Worker Y
    │
    ▼
[Variable Table] 收集各Worker中间结果
    │
    ▼
[Orchestration Engine] → [LLM Gateway] 调用数字主管 → 汇总结果
    │
    ▼
[WS Hub → 前端] 流式推送 text_delta → done
    │
    ▼
[Conversation Service] Redis缓冲 → 批量写入PostgreSQL
```

### 5.2 RAG检索流程

```
用户问题
    │
    ▼
[Tool Registry] 触发 knowledge_search 工具
    │
    ▼
[RAG Engine] search(query, top_k)
    │
    ├─→ [LLM Gateway] get_embedding(query) → 查询向量
    │       │
    │       ▼
    │   [pgvector] Cosine相似度搜索 → 向量结果集 R1
    │
    ├─→ [PostgreSQL] full-text search (BM25) → 关键词结果集 R2
    │
    ▼
[加权融合排序] score = α × cosine_score + (1-α) × bm25_score
    │
    ▼
[Top-K结果] 返回最相关文档片段
    │
    ▼
[LLM Gateway] 将片段 + 引用信息注入LLM上下文 → 生成带引用的回复
```

### 5.3 Agent协作编排流程

```
┌─────────────────────────────────────────┐
│            Orchestration Engine           │
│                                           │
│  1. 收到 user_message                     │
│  2. 加载数字主管Agent (system_prompt, tools)│
│  3. 构建主管上下文 (全量会话历史)          │
│  4. 调用 LLM Gateway → 拆解为子任务列表    │
│  5. 解析结构化子任务 (description, agent,  │
│     depends_on, confirm_required)         │
│  6. 生成执行计划 → WS推送 task_plan       │
│  7. 依赖分析 → 标记并行/串行组            │
│  8. 调度执行:                              │
│     - 并行组: 同时入队 arq tasks           │
│     - 串行组: 按序入队，等前一个完成       │
│  9. 每个Worker:                            │
│     - 加载Worker Agent                     │
│     - 构建Worker上下文 (仅子任务上下文)     │
│     - 注入工具定义 (Tool Registry)         │
│     - 调用 LLM Gateway (可能多轮工具调用)  │
│     - 结果写入变量表                       │
│     - WS推送 step_status                   │
│  10. 全部完成后                           │
│     - 加载数字主管                        │
│     - 汇总变量表和Worker结果              │
│     - 生成最终回复                        │
│     - WS推送 text_delta → done            │
└─────────────────────────────────────────┘
```

### 5.4 WebSocket消息流

```
┌──────────┐                      ┌──────────┐
│  前端     │                      │  后端     │
│  Client  │                      │  Server  │
└────┬─────┘                      └────┬─────┘
     │  CONNECT /ws/chat/{id}          │
     │  ──────────────────────────────>│ (1) 连接验证
     │  <──────────────────────────────│ (2) 连接成功
     │                                 │
     │  {"type":"user_message", ...}   │
     │  ──────────────────────────────>│ (3) 路由到Orchestration Engine
     │                                 │
     │  {"type":"task_plan", ...}      │
     │  <──────────────────────────────│ (4) 推送执行计划
     │                                 │
     │  {"type":"step_status", ...}    │
     │  <──────────────────────────────│ (5) 推送步骤状态
     │                                 │
     │  {"type":"text_delta", ...}     │
     │  <──────────────────────────────│ (6) 流式推送Token
     │  {"type":"text_delta", ...}     │
     │  <──────────────────────────────│
     │  ...                            │
     │                                 │
     │  {"type":"done", ...}           │
     │  <──────────────────────────────│ (7) 完成
     │                                 │
     │  {"type":"ping"}                │
     │  ──────────────────────────────>│ (8) 心跳
     │  {"type":"pong"}                │
     │  <──────────────────────────────│
```

---

## 6. 接口设计

### 6.1 REST API总览

API遵循RESTful设计风格，以 `/api/` 为前缀。以下按职责域列出端点组，完整定义见需求文档第6.1节。

| API组 | 端点数量 | 主要操作 | 对应服务模块 |
|-------|---------|---------|-------------|
| 会话管理 | 9个 | CRUD + 消息分页 + 消息编辑 + 重新生成 + 导出 | Conversation Service |
| Agent管理 | 10个 | CRUD + 启用/禁用 + 版本历史 + 回滚 + 模板 | Agent Service |
| 资产管理 | 6个 | 上传 + 列表 + 下载 + 预览 + 删除 + 重处理 | Asset Service |
| 模型管理 | 3个 | 模型列表 + 提供商添加/更新 | LLM Gateway |
| 系统 | 6个 | 健康检查 + 硬件监控 + 容器监控 + 审计日志 + Token统计 | Monitor + Security |
| 任务编排 | 5个 | 状态查询 + 暂停/恢复/取消 + 变量表 | Orchestration Engine |

共 **39个REST端点**。

### 6.2 WebSocket协议

三大WS端点及消息协议完整定义见需求文档第6.2节。

### 6.3 模块间内部接口

模块间通过Python抽象基类（ABC）定义的接口通信。各模块的ABC定义见第4节各模块的"模块接口"部分。

**关键调用链汇总：**

| 调用链 | 调用路径 |
|--------|---------|
| 用户对话 | WS Hub → Orchestration Engine → LLM Gateway / Agent Service / Conversation Service / Tool Registry |
| RAG检索 | Tool Registry → RAG Engine → LLM Gateway / Asset Service |
| 代码执行 | Tool Registry → Sandbox Manager → docker-py |
| 文件操作 | Tool Registry → Asset Service → Storage Backend |
| 安全拦截 | Security Service (middleware) → 各服务模块 |
| 监控推送 | Monitor Service → WS Hub → 前端 |

---

## 7. 安全设计

### 7.1 安全分层架构

```
输入层                 处理层                  输出层
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│ 输入过滤  │ ──→ │ 权限校验      │ ──→ │ 数据脱敏      │
│ XSS/SQL  │     │ 4级权限检查   │     │ 敏感信息遮蔽  │
│ 注入防护  │     │              │     │              │
└──────────┘     └──────────────┘     └──────────────┘
     │                  │                     │
     ▼                  ▼                     ▼
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│ 限流层    │     │ AST预审      │     │ 审计记录      │
│ IP + API │     │ 危险代码检测  │     │ 全操作追加    │
│ Key双层  │     │ 需确认/阻断  │     │ 不可删除      │
└──────────┘     └──────────────┘     └──────────────┘
```

### 7.2 权限模型

```
Level 1 (只读)
  └─→ Level 2 (分析)        ← 包含Level 1的所有权限
        └─→ Level 3 (操作)   ← 包含Level 1+2的所有权限
              └─→ Level 4 (管理) ← 包含所有权限
```

### 7.3 系统预设Agent权限

| Agent | 权限级别 | 说明 |
|-------|---------|------|
| 数字主管 🎯 | Level 4 | 管理级别，可编排所有操作 |
| 风控顾问 🛡️ | Level 3 | 操作级别，可执行/审计 |
| 数据专家 📊 | Level 2 | 分析级别，可查询/分析 |

### 7.4 审计追踪

所有Agent操作（代码执行、SQL查询、文件读写、API调用、Agent通信、配置变更）均记录审计日志，包含：操作类型、发起Agent、时间、参数、结果状态（success/failed/blocked/confirm_required）、会话ID。

日志存储在 `audit_logs` 表中，仅支持INSERT和SELECT，不支持UPDATE/DELETE。

---

## 8. 数据模型概要

核心数据表按模块归类：

| 归属模块 | 表名 | 说明 |
|---------|------|------|
| Agent Service | `agents` | Agent定义 |
| Agent Service | `agent_versions` | Agent配置版本历史 |
| Conversation Service | `conversations` | 会话 |
| Conversation Service | `messages` | 消息 |
| Orchestration Engine | `task_orchestrations` | 任务编排状态 |
| Orchestration Engine | `task_steps` | 子任务步骤 |
| Orchestration Engine | `variable_table` | 跨步骤变量表 |
| Asset Service | `assets` | 文件资产+知识库文档 |
| RAG Engine | `knowledge_chunks` | 知识库分块（含pgvector embedding） |
| LLM Gateway | `model_providers` | 模型提供商配置 |
| Security Service | `audit_logs` | 审计日志（仅追加） |

完整表结构（DDL）见需求文档第5节。

---

## 9. 模块独立测试策略

### 9.1 各模块可测试性分析

| 模块 | 外部依赖 | Mock策略 | 测试类型 |
|------|---------|---------|---------|
| LLM Gateway | litellm API | Mock litellm响应 | 单元测试 |
| Agent Service | 数据库 | 使用测试DB（或Mock Repository） | 集成测试 + 单元测试 |
| Orchestration Engine | LLM Gateway, Agent Service, arq, Tool Registry | Mock所有外部服务 | 单元测试（核心编排逻辑） + 集成测试（端到端） |
| Conversation Service | 数据库, Redis | 使用测试DB + 测试Redis（或Mock） | 集成测试 |
| Asset Service | 文件系统 | 使用临时目录 | 单元测试 |
| RAG Engine | LLM Gateway(Embedding), pgvector | Mock Embedding API, 测试DB | 单元测试(分块逻辑) + 集成测试(检索) |
| Sandbox Manager | Docker daemon | Mock docker-py（或使用测试容器） | 单元测试(AST分析) + 集成测试(容器执行) |
| Tool Registry | 各工具执行器 | Mock各执行器 | 单元测试 |
| Security Service | 数据库, Redis | 测试DB + 测试Redis | 单元测试(脱敏/权限) + 集成测试(日志) |
| Monitor Service | 系统API, Docker daemon | Mock系统调用 | 单元测试 |
| WS Hub | 所有服务模块 | Mock服务模块 | 单元测试(消息路由) + 集成测试(WS连接) |
| Config Manager | 文件系统(.env/YAML) | 使用测试配置文件 | 单元测试 |

### 9.2 模块间隔离策略

1. **Repository模式**：数据访问通过Repository抽象，服务模块不直接操作SQLAlchemy session
2. **ABC接口抽象**：模块间通过第4节定义的ABC接口通信，测试时注入Mock实现
3. **事件总线**（可选）：模块间松耦合通知（如Security Service的审计记录）可通过事件总线解耦
4. **FastAPI依赖注入**：利用FastAPI的Depends机制，测试时替换依赖实现

### 9.3 测试层次与范围

```
        ┌───────────────┐
        │  E2E测试      │  ← 完整用户对话流程（WebSocket→编排→回复）
        │  (少量)       │
        └───────┬───────┘
                │
        ┌───────┴───────┐
        │  集成测试      │  ← 多模块协作（如编排+Agent+LLM Gateway）
        │  (中等)       │
        └───────┬───────┘
                │
        ┌───────┴───────┐
        │  单元测试      │  ← 单模块逻辑（Mock所有外部依赖）
        │  (大量)       │
        └───────────────┘
```

目标覆盖率：核心模块 **60-80%**。

---

## 附录

### A. 参考文档

- [NEXUS AI 需求文档 v2.0](proposal.md)
- [原型图](web.html)
- 技术决策记录：见需求文档附录B（70项已确认决策）

### B. 与需求文档的对应关系

| 需求文档章节 | 对应本设计模块 |
|-------------|---------------|
| 2.1 多模型管理 | M1 (LLM Gateway), M12 (Config Manager) |
| 2.2 Agent系统 | M2 (Agent Service) |
| 2.3 Agent协作机制 | M3 (Orchestration Engine), M11 (WS Hub) |
| 2.4 Agent工具集 | M8 (Tool Registry), M7 (Sandbox Manager) |
| 2.5 资产管理 | M5 (Asset Service), M6 (RAG Engine) |
| 2.6 安全体系 | M9 (Security Service) |
| 2.7 系统监控 | M10 (Monitor Service) |
| 2.8 会话管理 | M4 (Conversation Service) |
| 2.9 LLM调用策略 | M1 (LLM Gateway), M3 (Orchestration Engine) |
| 2.10 前端UI布局 | F1-F7 (前端7个模块) |
