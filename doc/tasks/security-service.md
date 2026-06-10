# M9 — 安全审计 (`security_service`)

> 模块职责：贯穿全系统的横切安全关注点——权限控制、审计记录、数据脱敏、限流。

---

## 子任务

### 1. Agent 权限控制

- [ ] 1.1 实现 `check_permission(agent_id, required_level)` — 权限校验核心方法
- [ ] 1.2 定义权限-操作对照表（见概要设计文档第 4.9 节）
- [ ] 1.3 通过 FastAPI Depends 注入权限检查到 API 层
- [ ] 1.4 工具执行前通过 Tool Registry 调用权限检查
- [ ] 1.5 权限不足时返回 403 Forbidden + 错误信息

### 2. 审计日志

- [ ] 2.1 定义 AuditLog ORM 模型（audit_logs 表）
- [ ] 2.2 实现 `log_action(event: AuditEvent)` — 记录审计事件
- [ ] 2.3 审计表仅支持 INSERT 和 SELECT（不允许 UPDATE/DELETE）— 通过 ORM 层限制或 DB 权限限制
- [ ] 2.4 支持按时间 / Agent / 操作类型筛选查询
- [ ] 2.5 实现 `query_logs(filters)` — 分页查询
- [ ] 2.6 实现 `export_logs(filters)` — 导出审计日志（CSV/JSON）
- [ ] 2.7 各模块通过事件钩子发出 AuditEvent：代码执行 / SQL查询 / 文件读写 / API调用 / Agent通信 / 配置变更
- [ ] 2.8 审计事件采集使用异步模式（不阻塞主业务流程）

### 3. 数据脱敏

- [ ] 3.1 实现 `sanitize(text: str) → str` — 脱敏主方法
- [ ] 3.2 定义脱敏规则（从 YAML 配置加载）：
  - 手机号：`138****1234`
  - 身份证号：`320***********1234`
  - 银行卡号：`6222****1234`
  - API Key/Token：`sk-****...****abc`
  - 邮箱：`u***@example.com`
- [ ] 3.3 脱敏在 WebSocket 消息推送到前端之前执行（输出过滤层）
- [ ] 3.4 脱敏规则支持通过 YAML 配置更新（热加载或重启生效）

### 4. 双层限流

- [ ] 4.1 实现 IP 限流：FastAPI middleware + Redis 滑动窗口（如 60次/分钟，可配置）
- [ ] 4.2 实现 API Key 限流：对接 litellm 网关的速率限制（与模型提供商限制对齐）
- [ ] 4.3 限流触发时返回 429 Too Many Requests + Retry-After header
- [ ] 4.4 限流参数从 YAML 配置读取

### 5. 输入过滤

- [ ] 5.1 实现 SQL 注入过滤（参数化查询优先，附加输入模式检测）
- [ ] 5.2 实现 XSS 过滤（对用户输入 HTML 实体转义）

### 6. API 端点

- [ ] 6.1 `GET /api/audit/logs` — 查询审计日志（筛选+分页）
- [ ] 6.2 `GET /api/audit/logs/export` — 导出审计日志

### 7. 测试

- [ ] 7.1 测试权限检查各 Level 的拦截逻辑
- [ ] 7.2 测试审计日志写入 + 查询 + 导出
- [ ] 7.3 测试数据脱敏规则匹配
- [ ] 7.4 测试 IP 限流滑动窗口
