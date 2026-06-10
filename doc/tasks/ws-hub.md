# M11 — WebSocket中心 (`ws_hub`)

> 模块职责：管理三大 WebSocket 端点、处理连接生命周期、消息路由。

---

## 子任务

### 1. WebSocket 连接管理

- [ ] 1.1 配置 FastAPI WebSocket 路由：`/ws/chat/{conversation_id}`, `/ws/monitor`, `/ws/agents`
- [ ] 1.2 实现连接验证：验证 conversation_id 是否存在（chat 端点）
- [ ] 1.3 维护连接池（字典：conversation_id → WS 连接，或全局连接集合）
- [ ] 1.4 连接断开时自动清理连接池
- [ ] 1.5 预留 JWT 认证（第一版通过会话ID验证）

### 2. 心跳机制

- [ ] 2.1 实现服务端 ping/pong：每 30 秒发送 ping，等待 pong 响应
- [ ] 2.2 连续 3 次未收到 pong → 断开连接
- [ ] 2.3 前端实现心跳：收到 ping 后回复 pong，超时自动重连（指数退避）

### 3. 聊天消息路由 (`/ws/chat/{conversation_id}`)

- [ ] 3.1 接收客户端消息，按 `type` 字段路由：
  - `user_message` → Orchestration Engine.start_orchestration
  - `confirm_action` → Orchestration Engine.confirm_step
  - `control` → Orchestration Engine.pause/resume/cancel
  - `ping` → 回复 pong
- [ ] 3.2 服务端推送消息时，根据 conversation_id 找到对应连接发送
- [ ] 3.3 实现消息确认机制（可选）：Redis 缓存未确认消息，客户端重连后重发

### 4. 监控数据推送 (`/ws/monitor`)

- [ ] 4.1 服务端→客户端单向推送
- [ ] 4.2 Monitor Service 定时采集数据 → WS Hub 广播到所有 monitor 连接
- [ ] 4.3 推送消息类型：`hardware_stats`

### 5. Agent 状态推送 (`/ws/agents`)

- [ ] 5.1 服务端→客户端单向推送
- [ ] 5.2 Agent 状态变更时推送 `agent_status` 消息（idle/working/blocked/error）
- [ ] 5.3 消息包含：agent_id, agent_name, agent_emoji, status, message, timestamp

### 6. 错误处理

- [ ] 6.1 定义统一错误消息格式：type='error', code, message, agent_id, step_index, recoverable
- [ ] 6.2 捕获 WebSocket 处理过程中的异常 → 转换为错误消息推送
- [ ] 6.3 错误码体系：EXECUTION_TIMEOUT, PERMISSION_DENIED, RATE_LIMITED, MODEL_ERROR, SANDBOX_ERROR 等
- [ ] 6.4 recoverable=true 的错…供重试或人工介入

### 7. 消息序列化

- [ ] 7.1 定义 WebSocket 消息的 Pydantic Schema（客户端→服务端 + 服务端→客户端）
- [ ] 7.2 实现消息 JSON 序列化/反序列化
- [ ] 7.3 使用 Pydantic 验证消息格式

### 8. 测试

- [ ] 8.1 测试 WS 连接建立 + 心跳 + 断开
- [ ] 8.2 测试消息路由（各 type → 对应处理器）
- [ ] 8.3 Mock 客户端，测试消息推送
- [ ] 8.4 测试错误处理与错误消息格式
