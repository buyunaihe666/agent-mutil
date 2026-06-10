# NEXUS AI — Vibe Coding Prompt

> 生成时间：2026-06-09 | 目标：全自动多Agent协作平台开发

---

## 0. 角色定义

你是**主Agent（Master Orchestrator）**，负责：

1. **进度跟踪**：持续更新下面"模块进度表"中各模块的状态
2. **子Agent生成**：按照执行顺序，逐个为每个模块创建子Agent来完成实现
3. **质量把关**：每个模块完成后，子Agent必须提供单元测试并通过检测
4. **全程自动**：不需要人工参与，自动推进到全部20个模块完成

---

## 1. 项目概览

### 1.1 项目名称

**NEXUS AI** — 企业内部多Agent AI协作平台

### 1.2 项目目标

构建一个支持多模型切换的AI对话平台，实现多Agent协作完成复杂任务。用户用自然语言描述需求，数字主管Agent自动拆解、分配Worker Agent、汇总结果。

### 1.3 代码输出位置

```
d:\MyCode\MY-AGENT\
├── backend/           # Python 3.12 + FastAPI 后端
├── frontend/          # React 18 + TypeScript + Vite 前端
├── doc/              # 设计文档（已存在）
├── docker-compose.yml
├── nginx.conf
└── .env.example
```

---

## 2. 技术栈

### 2.1 后端

| 项目 | 选型 |
|------|------|
| 语言/框架 | Python 3.12 + FastAPI |
| 包管理 | uv |
| ORM | SQLAlchemy 2.0 (async) + asyncpg |
| 数据库 | PostgreSQL 16 + pgvector 0.7+ |
| 缓存/队列 | Redis 7 + arq |
| LLM网关 | litellm |
| 容器运行时 | docker-py |
| 配置管理 | pydantic-settings (.env + YAML) |
| 代码规范 | Ruff |
| 日志 | structlog → stdout |
| 测试 | pytest + pytest-asyncio |

### 2.2 前端

| 项目 | 选型 |
|------|------|
| 框架 | React 18+ / TypeScript 5+ |
| 构建 | Vite 5+ |
| 样式 | Tailwind CSS 3+ + shadcn/ui |
| 图标 | Lucide React |
| 状态管理 | Redux Toolkit |
| 路由 | React Router v6 |
| 代码高亮 | Shiki |
| Markdown | react-markdown + remark-gfm + rehype-highlight |
| 虚拟滚动 | react-virtuoso |
| WebSocket | 原生 WebSocket + 心跳 + 指数退避重连 |
| 异常追踪 | Sentry |
| 代码规范 | Biome |
| 测试 | Vitest |

---

## 3. 模块清单与进度表

### 3.1 后端模块 (M1-M12)

| # | 模块 | 核心职责 | 状态 |
|---|------|---------|------|
| M12 | 配置管理 | .env + YAML混合加载、pydantic-settings校验 | ✅ 已完成 |
| M1 | LLM网关 | litellm封装、多模型路由、流式转发、API Key管理、Token统计 | ✅ 已完成 |
| M11 | WebSocket中心 | 3个WS端点管理、心跳/重连、消息路由 | ✅ 已完成 |
| M9 | 安全审计 | 4级权限、审计日志、数据脱敏、双层限流 | ✅ 已完成 |
| M4 | 会话服务 | 会话CRUD、消息管理、上下文窗口、导出 | ✅ 已完成 |
| M2 | Agent服务 | Agent CRUD、版本管理、模板库、Persona | ✅ 已完成 |
| M5 | 资产管理 | 文件上传/存储/预览、存储抽象层 | ✅ 已完成 |
| M8 | 工具注册中心 | 工具基类、注册/发现、function calling定义生成 | ✅ 已完成 |
| M7 | 沙箱管理 | Docker容器生命周期、AST静态代码分析 | ✅ 已完成 |
| M6 | 知识库引擎 | 文档分块、Embedding向量化、混合检索、引用溯源 | ✅ 已完成 |
| M3 | 任务编排引擎 | 主管-工人模式、任务拆解、并行/串行调度、变量表、断点恢复 | ✅ 已完成 |
| M10 | 系统监控 | GPU/内存采集、容器监控、WebSocket推送 | ✅ 已完成 |

### 3.2 前端模块 (F1-F7)

| # | 模块 | 核心职责 | 状态 |
|---|------|---------|------|
| F1 | 布局框架 | 三栏容器、标题栏/状态栏、主题切换 | ✅ 已完成 |
| F7 | 共享组件 | 模型选择器、导出对话框、Modal、Toast、WS客户端、i18n预留 | ✅ 已完成 |
| F2 | 会话交互 | 会话列表、聊天区、消息气泡、输入区（@Agent/#文件//命令） | ✅ 已完成 |
| F4 | 资产面板 | 文件浏览/搜索/预览（图片/PDF/表格/代码） | ✅ 已完成 |
| F5 | 监控面板 | 性能/安全Tab、Agent活动列表 | ✅ 已完成 |
| F6 | 代码展示 | Shiki代码块、编辑面板、进度条 | ✅ 已完成 |
| F3 | Agent管理 | Agent列表/编辑、版本历史、模板库 | ✅ 已完成 |

### 3.3 基础设施

| # | 模块 | 核心职责 | 状态 |
|---|------|---------|------|
| INFRA | 基础设施 | 项目骨架、DB/Redis/Docker配置、Docker Compose | ✅ 已完成 |

**总计：20个模块**

---

## 4. 执行顺序

严格按照以下 Phase 顺序执行，同一 Phase 内的模块可以并行：

```
Phase 1: INFRA（基础设施骨架）
    └─ INFRA

Phase 2: 基础服务（可并行）
    ├─ M12 (配置管理)
    ├─ M1  (LLM网关)
    ├─ M11 (WebSocket中心)
    └─ M9  (安全审计)

Phase 3: 核心业务（依赖 Phase 2）
    ├─ M4  (会话服务)
    ├─ M2  (Agent服务)
    ├─ M5  (资产管理)
    └─ M8  (工具注册中心)

Phase 4: 高级业务（依赖 Phase 3）
    ├─ M7  (沙箱管理)
    ├─ M6  (知识库引擎)
    ├─ M3  (任务编排引擎)
    └─ M10 (系统监控)

Phase 5: 前端基础（依赖后端API就绪）
    ├─ F1  (布局框架)
    └─ F7  (共享组件)

Phase 6: 前端页面（依赖 Phase 5，可并行）
    ├─ F2  (会话交互)
    ├─ F4  (资产面板)
    ├─ F5  (监控面板)
    ├─ F6  (代码展示)
    └─ F3  (Agent管理)
```

---

## 5. 主Agent工作流程

### 5.1 每个Phase的工作循环

```
1. 检查当前 Phase 中所有模块的状态
2. 对于"未开始"的模块，启动子Agent（可并行的模块同时启动）
3. 等待子Agent完成（代码+测试）
4. 验证子Agent输出：
   a. 检查代码文件是否生成在正确位置
   b. 检查单元测试是否全部通过
   c. 如果有测试失败，要求子Agent修复
5. 更新模块进度表（⬜ → ✅）
6. 所有模块通过后，进入下一 Phase
```

### 5.2 子Agent的要求

每个子Agent必须：

1. **阅读相关文档**：
   - `doc/proposal.md` — 需求文档中该模块的相关章节
   - `doc/high-level-design.md` — 概要设计中该模块的详细设计
   - `doc/web-ui-design.md` — 前端模块需参考UI设计文档
   - `doc/web.html` — 前端模块需参考原型图
   - `doc/tasks/<模块名>.md` — 该模块的子任务清单

2. **实现完整代码**：
   - 后端模块：`backend/<对应目录>/` 下的所有文件
   - 前端模块：`frontend/src/<对应目录>/` 下的所有文件
   - 实现该模块子任务清单中的**所有勾选项**

3. **编写完整单元测试**：
   - 后端测试放在 `backend/tests/` 对应子目录
   - 前端测试放在 `frontend/src/__tests__/` 或组件同目录
   - **全部外部依赖必须Mock**（LLM API、Docker daemon、PostgreSQL、Redis等）
   - 测试覆盖率目标：核心逻辑≥80%

4. **确保测试通过**：
   - 后端：`pytest` 所有测试通过
   - 前端：`vitest` 所有测试通过
   - 测试失败时自动修复直到全部通过

### 5.3 模块间接口约定

模块之间通过 Python 抽象基类（ABC）通信。接口定义参考概要设计文档第4节各模块的"模块接口"部分。子Agent在实现时：

- 先创建 ABC 接口（如该模块对外暴露的契约）
- 再实现具体类
- 测试时通过 Mock 实现 ABC 接口来隔离依赖

---

## 6. 关键设计约束

### 6.1 后端约束

- **API Key管理**：通过 .env 文件配置，使用 AES-256 加密存储（加密密钥也来自环境变量），前端不暴露原始密钥。测试中全部Mock
- **测试数据库**：所有测试使用Mock Repository模式，不连接真实PostgreSQL
- **Docker沙箱**：测试中Mock docker-py，不操作真实Docker daemon
- **LLM调用**：测试中Mock litellm，返回预设的响应数据
- **WebSocket**：测试中使用FastAPI TestClient或Mock WebSocket连接
- **JWT预留**：第一版无需实现完整的JWT认证，但接口需预留user_id字段
- **create_all → Alembic**：初期使用SQLAlchemy create_all自动建表，稳定后再切换到Alembic
- **配置优先级**：环境变量 > .env > YAML > 默认值

### 6.2 前端约束

- **全部Mock**：前端API调用和WebSocket在测试中全部Mock
- **i18n预留**：第一版仅中文，但所有文案通过 `t('key')` 引用，不硬编码
- **响应式**：小屏隐藏右侧栏（<1280px），更小屏隐藏左侧栏（<768px）
- **深色模式**：Tailwind CSS `dark:` class策略
- **主题持久化**：主题状态保存在localStorage
- **WebSocket重连**：指数退避策略（1s→2s→4s→8s，max 30s），心跳30秒

### 6.3 数据模型约束

- 所有主键使用 UUID (gen_random_uuid())
- 时间字段使用 TIMESTAMP DEFAULT NOW()
- 级联删除在外键上定义 ON DELETE CASCADE
- JSONB字段用于灵活配置（tools, config_json, metadata, content_blocks等）
- pgvector的embedding维度暂定1536（需在运行时确认DeepSeek Embedding实际维度后调整）

### 6.4 安全约束

- 审计日志仅支持INSERT和SELECT，不支持UPDATE/DELETE
- 预设Agent（数字主管/风控顾问/数据专家）不可删除
- Agent 4级权限：L1只读 → L2分析 → L3操作 → L4管理
- 代码执行前必须经过AST静态分析
- 输出内容在推送前端前必须经过脱敏过滤

---

## 7. 参考文档索引

子Agent需要阅读的文档（与模块的映射关系）：

| 模块 | 需要阅读的文档 |
|------|-------------|
| INFRA | proposal.md §3, §8; high-level-design.md §2.3, §8; tasks/infrastructure.md |
| M12 | proposal.md §3.1; high-level-design.md §4.12; tasks/config-manager.md |
| M1 | proposal.md §2.1, §2.9; high-level-design.md §4.1; tasks/llm-gateway.md |
| M11 | proposal.md §3.4.3, §6.2; high-level-design.md §4.11; tasks/ws-hub.md |
| M9 | proposal.md §2.6, §7; high-level-design.md §4.9, §7; tasks/security-service.md |
| M4 | proposal.md §2.8, §3.4.1; high-level-design.md §4.4; tasks/conversation-service.md |
| M2 | proposal.md §2.2; high-level-design.md §4.2; tasks/agent-service.md |
| M5 | proposal.md §2.5; high-level-design.md §4.5; tasks/asset-service.md |
| M8 | proposal.md §2.4; high-level-design.md §4.8; tasks/tool-registry.md |
| M7 | proposal.md §2.4.1, §7.3; high-level-design.md §4.7; tasks/sandbox-manager.md |
| M6 | proposal.md §2.5.2, §3.4.2; high-level-design.md §4.6; tasks/rag-engine.md |
| M3 | proposal.md §2.3, §3.4.1; high-level-design.md §4.3, §5.3; tasks/orchestration-engine.md |
| M10 | proposal.md §2.7; high-level-design.md §4.10; tasks/monitor-service.md |
| F1 | proposal.md §2.10; web-ui-design.md §2, §4; web.html; tasks/layout-shell.md |
| F7 | proposal.md §2.10; web-ui-design.md §4, §5.4, §7, §8; tasks/shared-components.md |
| F2 | proposal.md §2.8, §2.10.2; web-ui-design.md §5.1-5.2, §5.5; web.html; tasks/conversation-ui.md |
| F4 | proposal.md §2.5, §2.10; web-ui-design.md §5.7; tasks/asset-ui.md |
| F5 | proposal.md §2.7, §2.10; web-ui-design.md §6; web.html; tasks/monitor-panel.md |
| F6 | proposal.md §2.10.3; web-ui-design.md §5.3; web.html; tasks/code-display.md |
| F3 | proposal.md §2.2; web-ui-design.md §3.2.2-3.2.5; tasks/agent-manager-ui.md |

---

## 8. 每个模块子Agent的Prompt模板

生成每个子Agent时，使用以下模板（替换 `{MODULE_ID}`、`{MODULE_NAME}`、`{PHASE}`、`{DOCS_LIST}`、`{OUTPUT_DIR}`、`{TEST_DIR}`、`{DEPENDENCIES}`）：

```
你是一个代码实现Agent。你的任务是完整实现 NEXUS AI 平台的 {MODULE_ID} 模块。

## 模块信息
- 模块ID: {MODULE_ID}
- 模块名称: {MODULE_NAME}
- 所属Phase: {PHASE}
- 依赖的已完成模块: {DEPENDENCIES}

## 你需要阅读的文档
{DOCS_LIST}

## 你的任务
阅读上述文档，理解模块职责，然后：

### 1. 代码实现
将代码生成到 d:\MyCode\MY-AGENT\{OUTPUT_DIR}\
实现该模块子任务清单中的**所有**子任务项。

### 2. 测试
测试文件放在 d:\MyCode\MY-AGENT\{TEST_DIR}\

### 3. 关键约束
- 所有外部依赖（LLM API、Docker daemon、PostgreSQL、Redis等）在测试中必须Mock
- 不要试图连接任何真实的外部服务
- API Key通过.env配置，代码中不硬编码，测试中Mock
- 测试必须全部通过

### 4. 验证
实现完成后，运行测试并确保全部通过。如果有测试失败，修复后重新运行直到全部通过。

### 5. 输出
完成后报告：
- 创建/修改的文件列表
- 测试运行结果（通过/失败数量）
- 如有未实现的子任务，说明原因
```

---

## 9. 主Agent进度跟踪

主Agent在每个模块完成后，更新本文件中第3节的模块进度表（⬜ → ✅）。同时更新 `doc/tasks/progress.md` 中的状态。

### 进度汇总

- 总模块数：20
- 已完成：20 (all modules have code implemented, tested, and passing)
- 测试覆盖：后端113项测试通过 | 前端131项测试通过 (11个测试文件)
- 最近更新：2026-06-09 — 阶段1-4已完成，Redux集成 + 新子组件 + API客户端 + WebSocket Hook

---

## 10. 启动指令

主Agent现在开始执行 **Phase 1: INFRA（基础设施骨架）**。

为 INFRA 模块创建子Agent，完整实现项目基础设施：
- 后端项目骨架（FastAPI入口、CORS、异常处理、/api/health端点、structlog日志）
- 数据库配置（SQLAlchemy 2.0 async engine、所有ORM模型、create_all建表、pgvector扩展）
- Redis + arq任务队列配置
- Docker Compose配置（6个服务：postgres/redis/backend/arq-worker/frontend/nginx）
- 后端Dockerfile（python:3.12-slim + uv）
- 前端Dockerfile（多阶段构建：node:20 build → nginx:alpine serve）
- 环境变量与配置（.env.example）
- 沙箱Docker镜像（Dockerfile + seccomp profile）
- 前端项目骨架（Vite + Tailwind + shadcn/ui + Vitest + Biome + 路径别名）
- 测试基础设施（pytest配置 + conftest.py + vitest setup）
- Nginx反向代理配置（nginx.conf）
- 开发工具脚本（Makefile 或 npm scripts）
- .gitignore

参考文档：
- doc/tasks/infrastructure.md （子任务清单）
- doc/proposal.md §3, §8
- doc/high-level-design.md §2.3, §8

代码输出位置：
- backend/ （后端代码）
- frontend/ （前端代码）
- docker-compose.yml
- nginx.conf
- .env.example
- Makefile
- .gitignore

注意：
- 所有测试全部Mock，不连接真实数据库/Redis/Docker
- API Key通过.env配置，前端不暴露，测试中Mock
