# INFRA — 基础设施与部署

> 模块职责：项目骨架搭建、数据库/Redis/Docker 环境配置、CI/CD、部署。

---

## 子任务

### 1. 后端项目骨架

- [ ] 1.1 初始化 uv Python 项目（pyproject.toml，Python 3.12）
- [ ] 1.2 配置 Ruff 代码规范（pyproject.toml 中 ruff 配置段）
- [ ] 1.3 搭建 FastAPI 应用入口（main.py：应用创建 + CORS + 生命周期管理）
- [ ] 1.4 配置 structlog 结构化日志（输出到 stdout，JSON 格式）
- [ ] 1.5 创建 FastAPI 全局异常处理中间件（middleware/error_handler.py）
- [ ] 1.6 创建基础的 `/api/health` 端点（检查 DB + Redis + Docker daemon）
- [ ] 1.7 配置开发环境 CORS（允许 localhost:5173）

### 2. 数据库

- [ ] 2.1 配置 SQLAlchemy 2.0 (async) engine + async session（config.py 读取 DATABASE_URL）
- [ ] 2.2 配置 asyncpg 驱动
- [ ] 2.3 第一阶段：使用 create_all 自动建表（从 SQLAlchemy metadata）
- [ ] 2.4 配置 pgvector 扩展（CREATE EXTENSION IF NOT EXISTS vector）
- [ ] 2.5 第二阶段（稳定后）：切换到 Alembic 迁移管理
- [ ] 2.6 创建 Alembic 初始化（alembic init + env.py 配置 async SQLAlchemy）
- [ ] 2.7 数据库连接池配置（pool_size + pool_overflow）

### 3. Redis + arq 任务队列

- [ ] 3.1 配置 Redis 连接（redis.asyncio 客户端）
- [ ] 3.2 配置 arq Worker（worker.py：WorkerSettings 定义）
- [ ] 3.3 定义 arq job 队列（默认队列 + 高优先级队列）
- [ ] 3.4 实现 arq job 延迟/重试机制

### 4. Docker Compose 配置

- [ ] 4.1 编写 docker-compose.yml（5个服务：postgres + redis + backend + arq-worker + frontend + nginx）
- [ ] 4.2 配置 postgres 服务（pgvector/pgvector:pg16，环境变量，volume，healthcheck）
- [ ] 4.3 配置 redis 服务（redis:7-alpine，healthcheck）
- [ ] 4.4 配置 backend 服务（Dockerfile + depends_on + 环境变量 + 挂载 docker.sock + healthcheck）
- [ ] 4.5 配置 arq-worker 服务（同 backend image，command 不同）
- [ ] 4.6 配置 frontend 服务（Dockerfile + port 3000）
- [ ] 4.7 配置 nginx 服务（反向代理 :80 → frontend:3000 + backend:8000，WebSocket 升级）
- [ ] 4.8 编写 nginx.conf（/ 代理前端，/api/ 代理后端，/ws/ 代理 WebSocket 长连接）
- [ ] 4.9 配置 Docker 日志驱动（json-file，max-size 10m，max-file 3）
- [ ] 4.10 定义 volumes（pgdata, assets, sandbox_tmp）

### 5. 后端 Dockerfile

- [ ] 5.1 编写 backend/Dockerfile（基于 python:3.12-slim）
- [ ] 5.2 安装 uv + 项目依赖
- [ ] 5.3 配置 ENTRYPOINT（uvicorn main:app --host 0.0.0.0 --port 8000）

### 6. 前端 Dockerfile

- [ ] 6.1 编写 frontend/Dockerfile（多阶段构建：node:20 build → nginx:alpine serve）
- [ ] 6.2 nginx 配置 SPA fallback（try_files）

### 7. 环境变量与配置

- [ ] 7.1 创建 .env.example 模板文件（列出所有环境变量及说明）
- [ ] 7.2 .env 文件加入 .gitignore
- [ ] 7.3 敏感配置标记（API Key 等通过环境变量注入，不入 Git）

### 8. 沙箱 Docker 镜像

- [ ] 8.1 编写 sandbox/Dockerfile（基于 python:3.12-slim，预装 5 核心库）
- [ ] 8.2 创建 seccomp profile 文件（限制系统调用）
- [ ] 8.3 编写镜像构建脚本 + 构建说明

### 9. 前端项目骨架（补充 F1 未覆盖的）

- [ ] 9.1 Vite 配置：server port 5173 + proxy /api → backend:8000
- [ ] 9.2 TypeScript 配置（tsconfig.json：strict + paths）
- [ ] 9.3 Tailwind CSS 配置（tailwind.config.ts：content paths + theme extends + dark mode）
- [ ] 9.4 shadcn/ui 初始化（components.json）
- [ ] 9.5 Vitest 配置（vitest.config.ts）
- [ ] 9.6 Biome 配置（biome.json：linter + formatter rules）

### 10. 测试基础设施

- [ ] 10.1 配置 pytest（pytest.ini 或 pyproject.toml 中的 [tool.pytest]）
- [ ] 10.2 配置 pytest-asyncio（asyncio_mode = auto）
- [ ] 10.3 创建 conftest.py：测试 fixtures（test DB + test Redis + test client）
- [ ] 10.4 创建前端 test setup（vitest setup file + mocks）

### 11. 开发工具脚本

- [ ] 11.1 编写 Makefile 或 npm scripts：
  - `make dev` — 启动前后端开发环境
  - `make build` — 构建 Docker 镜像
  - `make up` — 启动 Docker Compose
  - `make test` — 运行所有测试
  - `make lint` — 运行 Ruff + Biome
- [ ] 11.2 编写 .gitignore（Python + Node + Docker 常见忽略项）

### 12. 测试

- [ ] 12.1 测试 Docker Compose 启动 → 所有服务健康检查通过
- [ ] 12.2 测试 DB 连接 + pgvector 扩展可用
- [ ] 12.3 测试 Redis 连接 + arq job 入队/执行
- [ ] 12.4 测试前端 Vite HMR 正常
