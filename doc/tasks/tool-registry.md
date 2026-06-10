# M8 — 工具注册中心 (`tool_registry`)

> 模块职责：管理 Agent 可用工具的注册、发现和 function calling 定义生成。

---

## 子任务

### 1. 工具基类设计

- [ ] 1.1 定义 `BaseTool` ABC：name, description, parameters (JSON Schema) 三个属性 + execute 方法
- [ ] 1.2 定义 `ToolResult` 数据类：success, output, artifacts, error
- [ ] 1.3 定义 `ExecutionContext` 数据类：conversation_id, agent_id, user_id, variables
- [ ] 1.4 实现 `get_function_definition()` — 从 BaseTool 自动生成 OpenAI function calling 格式的 tool definition

### 2. 工具注册与发现

- [ ] 2.1 实现 `ToolRegistry` 类：register / get_tool / list_tools / get_definitions_for_agent
- [ ] 2.2 应用启动时自动注册所有内置工具
- [ ] 2.3 根据 Agent 的 tools JSONB 字段动态注入对应的 tool definitions 到 LLM 请求
- [ ] 2.4 支持运行时扩展：Agent 在对话中请求启用新工具 → 标记待确认 → 用户确认后动态注册

### 3. 工具执行调度

- [ ] 3.1 实现 `execute(tool_name, params, context)` — 统一工具调用入口
- [ ] 3.2 根据 tool_name 路由到对应执行器
- [ ] 3.3 执行前调用 Security Service 检查 Agent 权限级别
- [ ] 3.4 执行结果记录审计日志

### 4. 代码执行工具 (`code_executor.py`)

- [ ] 4.1 实现 CodeExecutorTool（extends BaseTool）
- [ ] 4.2 function calling parameters schema：code_text, language, files, variable_keys
- [ ] 4.3 execute 方法：调用 AST 分析 → 安全检查 → Sandbox Manager 执行
- [ ] 4.4 返回 CodeExecResult（stdout + stderr + 生成的文件 + 写入变量表的数据）

### 5. 数据库查询工具 (`db_query.py`)

- [ ] 5.1 实现 DbQueryTool（extends BaseTool）
- [ ] 5.2 function calling parameters schema：query_text
- [ ] 5.3 安全限制：只读 SELECT 默认允许，写操作（INSERT/UPDATE/DELETE/DDL）需用户确认
- [ ] 5.4 禁止操作系统表（pg_catalog 等）
- [ ] 5.5 查询结果行数 ≤ 1000 行，超时 30 秒
- [ ] 5.6 返回查询结果（列名 + 行数据）

### 6. 文件操作工具 (`file_ops.py`)

- [ ] 6.1 实现 FileReadTool + FileWriteTool（extends BaseTool）
- [ ] 6.2 读文件：验证路径在用户资产目录范围内
- [ ] 6.3 写文件：生成的文件存入 Asset Service，返回 asset_id
- [ ] 6.4 文件类型限制：CSV, XLSX, JSON, TXT, PNG, PDF

### 7. 网络搜索工具 (`web_search.py`)

- [ ] 7.1 实现 WebSearchTool（extends BaseTool）
- [ ] 7.2 对接阿里云 IQS MCP Server（配置 endpoint 从 Config Manager 获取）
- [ ] 7.3 搜索结果缓存（Redis，TTL 可配置）避免重复调用
- [ ] 7.4 返回搜索结果摘要（title + snippet + url）

### 8. 外部 API 调用工具 (`api_caller.py`)

- [ ] 8.1 实现 ApiCallerTool（extends BaseTool）
- [ ] 8.2 支持预设集成：Slack 通知 / 邮件发送 / Jira 工单 / 企业微信
- [ ] 8.3 安全限制：仅调用白名单内的 URL
- [ ] 8.4 支持 OAuth2 / API Key 认证
- [ ] 8.5 调用参数和响应记录审计日志

### 9. 测试

- [ ] 9.1 测试工具注册 + function calling 定义生成
- [ ] 9.2 Mock 各执行器，测试统一调度路由
- [ ] 9.3 测试权限检查拦截

### 10. 数据模型（如需要）

- [ ] 10.1 工具注册表不需要独立 DB 表（内存注册 + Agent.tools JSONB 字段存储工具列表）
- [ ] 10.2 预留 ToolExecutionLog（可用审计日志 audit_logs 表替代）
