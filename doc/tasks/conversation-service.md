# M4 — 会话服务 (`conversation_service`)

> 模块职责：管理会话生命周期、消息存储与查询、上下文窗口。

---

## 子任务

### 1. 会话 CRUD

- [ ] 1.1 定义 Conversation ORM 模型（conversations 表）
- [ ] 1.2 实现 `list_conversations(filters)` — 支持搜索标题、筛选状态(active/archived)、排序(updated_at DESC)
- [ ] 1.3 实现 `create_conversation(first_message)` — 创建会话 + 调用 LLM 自动生成标题
- [ ] 1.4 实现 `get_conversation(conv_id)` — 获取会话详情
- [ ] 1.5 实现 `update_conversation(conv_id, data)` — 更新（重命名/置顶/归档/切换模型/修改置顶空间）
- [ ] 1.6 实现 `delete_conversation(conv_id)` — 级联删除会话及所有消息
- [ ] 1.7 实现 LLM 生成标题：提取首条消息 → 调 LLM 生成简短标题（<20字）→ 写入 title 字段

### 2. 置顶空间

- [ ] 2.1 is_pinned 字段标记置顶状态
- [ ] 2.2 pinned_space 字段标记所属置顶空间名称（如"产品运营"/"项目开发"）
- [ ] 2.3 list_conversations 支持按 pinned_space 分组排序

### 3. 消息管理

- [ ] 3.1 定义 Message ORM 模型（messages 表）— 含 role, agent_id, content, content_blocks(JSONB), tool_calls(JSONB), token_count, is_edited, parent_message_id
- [ ] 3.2 实现消息存储：Redis 缓冲（List）+ 批量写入 PostgreSQL（每10条或每5秒批量 flush）
- [ ] 3.3 实现 `get_messages(conv_id, cursor, limit)` — cursor-based 分页查询（按 created_at 倒序），默认50条/页
- [ ] 3.4 实现 `edit_message(msg_id, new_content)` — 编辑用户消息，标记 is_edited=true + edited_at
- [ ] 3.5 编辑消息后触发 Agent 重新生成回复（调用 Orchestration Engine）
- [ ] 3.6 实现 `regenerate_response(conv_id, msg_id)` — 重新生成 Agent 回复，记录 parent_message_id 关系链

### 4. 上下文窗口管理（混合策略）

- [ ] 4.1 实现 `build_context(conv_id, agent_id, max_tokens)` — 核心上下文构建方法
- [ ] 4.2 近期消息：完整保留最近 N 条消息（滑动窗口，N 从配置读取）
- [ ] 4.3 远期消息：超出窗口的消息调用 LLM 生成压缩摘要
- [ ] 4.4 摘要缓存（Redis）：同一会话的摘要不重复生成
- [ ] 4.5 摘要 + 近期消息合并注入 LLM 上下文
- [ ] 4.6 上下文隔离：agent_id=主管 → 全量；agent_id=Worker → 仅子任务上下文

### 5. 会话导出

- [ ] 5.1 实现 `export_conversation(conv_id, format)` — 支持 Markdown / PDF / JSON
- [ ] 5.2 Markdown 导出：消息按时间排序，含 Agent 标识 + Markdown 内容
- [ ] 5.3 JSON 导出：完整消息结构（含 content_blocks + tool_calls 等）
- [ ] 5.4 PDF 导出：服务端生成 PDF（如 weasyprint 或 reportlab）
- [ ] 5.5 API 返回文件流 + Content-Disposition header

### 6. 消息流持久化（Redis Buffer）

- [ ] 6.1 消息到达时先写入 Redis List（按 conversation_id 分 key）
- [ ] 6.2 实现定时批量 flush：每10条消息或每5秒触发一次
- [ ] 6.3 flush 后将消息写入 PostgreSQL messages 表
- [ ] 6.4 应用关闭时 force flush 所有 Redis 缓冲中的消息

### 7. API 端点

- [ ] 7.1 `GET /api/conversations` — 会话列表（分页+搜索+筛选+排序）
- [ ] 7.2 `POST /api/conversations` — 创建新会话
- [ ] 7.3 `GET /api/conversations/{id}` — 会话详情
- [ ] 7.4 `PATCH /api/conversations/{id}` — 更新会话
- [ ] 7.5 `DELETE /api/conversations/{id}` — 删除会话
- [ ] 7.6 `GET /api/conversations/{id}/messages` — 消息列表（cursor分页）
- [ ] 7.7 `PATCH /api/conversations/{id}/messages/{msg_id}` — 编辑消息
- [ ] 7.8 `POST /api/conversations/{id}/regenerate` — 重新生成回复
- [ ] 7.9 `GET /api/conversations/{id}/export` — 导出会话（?format=md|pdf|json）

### 8. Pydantic Schema

- [ ] 8.1 ConversationCreate / ConversationUpdate / ConversationSummary / ConversationDetail Schema
- [ ] 8.2 MessageCreate / MessagePage / MessageEdit Schema
- [ ] 8.3 ExportRequest / ExportFormat 枚举 Schema

### 9. 测试

- [ ] 9.1 测试会话 CRUD
- [ ] 9.2 测试 LLM 生成标题
- [ ] 9.3 测试 cursor-based 分页
- [ ] 9.4 测试消息编辑 + 重新生成
- [ ] 9.5 测试上下文构建（滑动窗口 + 摘要）
- [ ] 9.6 测试 Redis 缓冲 + 批量写入
- [ ] 9.7 测试会话导出（三种格式）
