# M7 — 沙箱管理 (`sandbox_manager`)

> 模块职责：管理 Docker 沙箱容器的创建→执行→销毁全生命周期，以及代码安全审查。

---

## 子任务

### 1. 沙箱 Docker 镜像

- [ ] 1.1 编写沙箱 Dockerfile：基于 python:3.12-slim，预装 numpy, pandas, matplotlib, requests, beautifulsoup4
- [ ] 1.2 安装安全隔离工具（seccomp profile 定义）
- [ ] 1.3 镜像中内置 pip install 能力（Agent 按需动态安装其他库）
- [ ] 1.4 编写镜像构建脚本（docker build）
- [ ] 1.5 实现 `build_image()` — 通过 docker-py 构建/验证镜像存在
- [ ] 1.6 Docker Compose 中预留 sandbox 镜像构建步骤

### 2. 容器生命周期管理（docker-py）

- [ ] 2.1 实现 `execute_code(request: CodeExecRequest) → CodeExecResult` — 主执行入口
- [ ] 2.2 创建临时容器（docker-py `containers.run` 或 `create_and_start`）
  - 限制：CPU 1 核 + 内存 512MB + 磁盘 IO 限制
  - 挂载：只读用户文件目录 + 可写临时目录
  - 网络：允许出站（外网），禁止访问 localhost/内网 IP 段
  - seccomp：挂载 seccomp profile 限制系统调用
  - 禁止 `--privileged`
- [ ] 2.3 向容器注入代码（通过 stdin / 文件挂载 / API）
- [ ] 2.4 执行超时 60 秒 → `docker stop` 强杀 → `docker rm` 清理
- [ ] 2.5 执行完成后收集 stdout + stderr + 生成的文件列表
- [ ] 2.6 执行完成后立即销毁容器（`docker rm -f`）
- [ ] 2.7 实现 `cleanup_containers()` — 定期清理残留/僵尸容器

### 3. AST 静态代码分析 (`code_analyzer.py`)

- [ ] 3.1 实现 `analyze(code: str) → CodeAnalysisResult` — AST 解析
- [ ] 3.2 使用 Python `ast` 模块遍历语法树
- [ ] 3.3 检测危险节点：`os.system`, `subprocess.*`, `eval`, `exec`, `compile`, `__import__`, `importlib`, `open(os.path)` 模式
- [ ] 3.4 检测危险导入：`import os`, `from subprocess import ...` 等
- [ ] 3.5 检测文件操作：`open('/etc/...)`, `shutil.rmtree` 等
- [ ] 3.6 分析结果按严重度分级：safe / warning / dangerous
- [ ] 3.7 dangerous 操作标记为「需用户确认」

### 4. 代码执行流程整合

- [ ] 4.1 执行前调用 AST 分析 → safe 代码直接执行，dangerous 代码需用户确认
- [ ] 4.2 用户确认后执行代码
- [ ] 4.3 执行后生成审查报告（记录代码+输出+异常分析）
- [ ] 4.4 代码执行记录写入审计日志（通过 Security Service）
- [ ] 4.5 执行结果推送到前端（WebSocket `code_progress`）

### 5. 测试

- [ ] 5.1 测试 AST 分析对各类危险代码的检测
- [ ] 5.2 Mock docker-py，测试容器生命周期管理逻辑
- [ ] 5.3 集成测试：端到端代码执行（简单 Python 代码）
- [ ] 5.4 测试超时强杀逻辑
