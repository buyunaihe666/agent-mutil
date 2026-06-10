# M3 — 任务编排引擎 (`orchestration_engine`)

> 模块职责：实现主管-工人协作模式的核心逻辑——任务拆解→依赖分析→并行/串行调度→结果汇总。

---

## 子任务

### 1. 任务拆解

- [ ] 1.1 实现 `start_orchestration(conversation_id, user_message)` — 编排入口
- [ ] 1.2 加载数字主管 Agent 配置（system_prompt 含任务拆解指令 + tools）
- [ ] 1.3 构建数字主管上下文（通过 Conversation Service 获取全量会话历史）
- [ ] 1.4 调用 LLM Gateway（chat_completion）让数字主管拆解任务，返回结构化子任务列表
- [ ] 1.5 解析 LLM 返回值 → 提取子任务数组（description + assigned_agent + depends_on + confirm_required）
- [ ] 1.6 验证拆解结果：每个子任务必须有有效的 assigned_agent 引用

### 2. 执行计划生成与推送

- [ ] 2.1 根据拆解结果构建 TaskOrchestration + TaskStep 记录，写入数据库
- [ ] 2.2 分析依赖关系 → 标记并行组（无依赖步骤）和串行组（有依赖步骤）
- [ ] 2.3 通过 WebSocket 推送 `task_plan` 消息到前端（含步骤列表 + parallel_groups）
- [ ] 2.4 执行计划包含：每步骤的 index、description、assigned_agent、confirm_required、depends_on

### 3. 并行/串行调度

- [ ] 3.1 实现依赖图分析：对 depends_on 数组进行拓扑排序，识别可并行执行的步骤组
- [ ] 3.2 并行组：通过 arq 任务队列同时入队（asyncio.gather 或 arq job 批量提交）
- [ ] 3.3 串行组：按依赖顺序依次入队，每个步骤完成后检查下一个步骤的前置条件
- [ ] 3.4 按会话限制并发数：每个会话最多 N 个并行 Worker（默认3，从配置读取）
- [ ] 3.5 使用信号量（Semaphore）控制会话级并发数

### 4. arq 消息队列优先级

- [ ] 4.1 配置 arq 队列，数字主管的编排任务使用高优先级队列
- [ ] 4.2 定义 arq job 数据结构（orchestration_id + step_index + agent_id + context）
- [ ] 4.3 Worker Agent 的 job 使用默认优先级队列（FIFO）

### 5. Worker 子任务执行

- [ ] 5.1 实现 Worker 执行流程：加载 Worker Agent 配置 → 构建 Worker 上下文（仅子任务上下文）→ 注入工具定义 → 调用 LLM Gateway
- [ ] 5.2 构建 Worker 上下文：仅包含分配给该 Worker 的子任务描述 + 变量表引用
- [ ] 5.3 支持多轮工具调用循环（LLM 可能需要多次 tool call）
- [ ] 5.4 每一步执行状态变更通过 WebSocket 推送 `step_status`
- [ ] 5.5 Worker 结果写入变量表

### 6. 上下文隔离

- [ ] 6.1 实现主管全量上下文策略：build_context 传入数字主管 agent_id → 返回完整会话历史
- [ ] 6.2 实现 Worker 隔离上下文策略：build_context 传入 Worker agent_id → 仅返回分配的子任务上下文

### 7. 变量表管理

- [ ] 7.1 定义 VariableTable ORM 模型（variable_table 表：conversation_id + var_key + var_value[JSONB] + var_type + created_by_agent + created_by_step）
- [ ] 7.2 实现 `get_variables(conversation_id)` — 读取当前会话所有变量
- [ ] 7.3 实现 `set_variable(conversation_id, key, value, agent_id)` — 写入/更新变量
- [ ] 7.4 变量更新时通过 WebSocket 推送 `variable_update` 消息
- [ ] 7.5 会话结束时清理变量表
- [ ] 7.6 支持变量类型标记：str / int / float / DataFrame / image / path

### 8. 结果汇总

- [ ] 8.1 所有子任务完成后（success/failed/skipped），重新加载数字主管
- [ ] 8.2 构建汇总上下文：完整会话 + 变量表 + 各 Worker 执行结果
- [ ] 8.3 调用 LLM Gateway 生成最终回复（流式）
- [ ] 8.4 流式推送 text_delta 到前端
- [ ] 8.5 推送 `done` 消息（含 token_usage）

### 9. 人工介入机制

- [ ] 9.1 判断子任务 confirm_required 标记
- [ ] 9.2 confirm_required=true 的步骤：Worker 执行到该步骤时暂停，推送 `step_status: confirm_required`
- [ ] 9.3 等待用户 WebSocket 发送 `confirm_action`（确认/拒绝）
- [ ] 9.4 用户确认后继续执行，拒绝则标记为 skipped
- [ ] 9.5 实现全自动模式（默认，confirm_required 步骤自动跳过确认）和确认模式切换

### 10. 任务控制（暂停/恢复/取消）

- [ ] 10.1 实现 `pause(orchestration_id)` — 暂停所有进行中的 Worker，状态写入 DB
- [ ] 10.2 实现 `resume(orchestration_id)` — 从断点恢复执行
- [ ] 10.3 实现 `cancel(orchestration_id)` — 取消所有未完成的步骤
- [ ] 10.4 接收 WebSocket `control` 消息（pause/resume/cancel）并路由到对应方法
- [ ] 10.5 浏览器关闭后后端继续执行（任务状态已在 DB 持久化）
- [ ] 10.6 重新打开浏览器 → 前端重新连接 WS → 查询当前编排状态 → 恢复 UI

### 11. 断点恢复

- [ ] 11.1 TaskOrchestration 状态实时写入 DB（planning → executing → completed/failed/cancelled）
- [ ] 11.2 TaskStep 状态实时更新（pending → running → completed/failed/skipped）
- [ ] 11.3 应用重启后检查进行中的编排任务并恢复
- [ ] 11.4 记录 current_step + progress 字段用于恢复定位

### 12. Agent 间通信

- [ ] 12.1 实现 Agent 间消息传递（agent_comm 工具执行器）
- [ ] 12.2 支持四种通信类型：委派任务 / 请求数据 / 通知 / 汇总请求
- [ ] 12.3 通信消息使用预定义 JSON 结构
- [ ] 12.4 所有 Agent 间通信记录到审计日志

### 13. API 端点

- [ ] 13.1 `GET /api/tasks/{conversation_id}` — 获取当前编排状态
- [ ] 13.2 `POST /api/tasks/{conversation_id}/pause` — 暂停
- [ ] 13.3 `POST /api/tasks/{conversation_id}/resume` — 恢复
- [ ] 13.4 `POST /api/tasks/{conversation_id}/cancel` — 取消
- [ ] 13.5 `GET /api/tasks/{conversation_id}/variables` — 获取变量表

### 14. 数据模型

- [ ] 14.1 定义 TaskOrchestration ORM 模型
- [ ] 14.2 定义 TaskStep ORM 模型
- [ ] 14.3 定义 VariableTable ORM 模型

### 15. 测试

- [ ] 15.1 Mock LLM Gateway，测试任务拆解解析逻辑
- [ ] 15.2 测试依赖分析 → 并行/串行分组
- [ ] 15.3 测试变量表读写
- [ ] 15.4 测试暂停/恢复/取消
- [ ] 15.5 测试上下文隔离（主管全量 vs Worker 隔离）
- [ ] 15.6 端到端集成测试：用户消息 → 拆解 → 执行 → 汇总
