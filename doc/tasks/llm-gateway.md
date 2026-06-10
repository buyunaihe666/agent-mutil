# M1 — LLM网关 (`llm_gateway`)

> 模块职责：封装对 litellm 的调用，为上层提供统一的多模型LLM访问接口。

---

## 子任务

### 1. 模型路由

- [ ] 1.1 配置 litellm 初始化，对接 DeepSeek / OpenAI / Anthropic 的 API 端点
- [ ] 1.2 实现 `get_available_models()` — 返回所有提供商汇总的可用模型列表
- [ ] 1.3 实现 `select_model(model_id)` — 根据模型ID路由到对应提供商的 API 配置
- [ ] 1.4 实现模型列表缓存（Redis，TTL 60秒），减少重复查询

### 2. 聊天补全（非流式）

- [ ] 2.1 封装 `chat_completion(request: ChatRequest) → ChatResponse` 方法
- [ ] 2.2 构建 litellm 请求参数（messages、model、temperature、max_tokens、tools）
- [ ] 2.3 解析 litellm 响应为标准 ChatResponse（content + tool_calls + token_usage）
- [ ] 2.4 处理异常：超时、API错误、速率限制 → 统一错误码
- [ ] 2.5 实现自动重试（指数退避，最多3次）

### 3. 聊天补全（流式）

- [ ] 3.1 封装 `chat_completion_stream(request: ChatRequest) → AsyncGenerator[Delta]`
- [ ] 3.2 将 litellm stream 响应逐 chunk 转为 Delta（text/tool_call_delta）
- [ ] 3.3 处理流式中断（客户端断开连接时取消 litellm 请求）
- [ ] 3.4 流式完成时汇总 token_usage

### 4. Embedding

- [ ] 4.1 封装 `get_embedding(text: str, model: str) → list[float]`
- [ ] 4.2 调用 DeepSeek Embedding API，返回向量
- [ ] 4.3 在运行时确认 DeepSeek Embedding 实际维度并记录到配置

### 5. API Key 管理

- [ ] 5.1 实现 AES-256 加密/解密 API Key（使用环境变量中的加密密钥）
- [ ] 5.2 实现 API Key 存储与读取（加密写入 model_providers 表）
- [ ] 5.3 实现多 Key 轮换逻辑：检测速率限制响应（429）→ 自动切换到备用 Key
- [ ] 5.4 前端 API Key 输入框显示为密码字段，不暴露原始密钥

### 6. Token 统计

- [ ] 6.1 每次 LLM 调用后记录 prompt_tokens + completion_tokens
- [ ] 6.2 实现 `get_token_usage(filters)` — 按 会话/Agent/模型 维度聚合查询
- [ ] 6.3 实现 Token 用量按时间段统计（日/周/月）
- [ ] 6.4 前端底部状态栏展示 Token 用量（通过 /api/stats/tokens 获取）

### 7. 超时控制

- [ ] 7.1 从 model_providers 表读取模型级超时（DeepSeek 120s / OpenAI 120s / Claude 180s）
- [ ] 7.2 从 agents 表读取 Agent 级超时（默认 300s）
- [ ] 7.3 实现组合超时逻辑：以模型级超时和 Agent 级超时中先到达者为准
- [ ] 7.4 超时后取消 litellm 请求，返回 TIMEOUT 错误码

### 8. API 端点

- [ ] 8.1 `GET /api/models` — 获取可用模型列表
- [ ] 8.2 `POST /api/models/providers` — 添加模型提供商配置
- [ ] 8.3 `PATCH /api/models/providers/{id}` — 更新提供商配置
- [ ] 8.4 `GET /api/stats/tokens` — 获取 Token 消耗统计

### 9. 数据模型

- [ ] 9.1 定义 ModelProvider ORM 模型（model_providers 表）
- [ ] 9.2 实现 ModelProvider Repository（CRUD + 加密/解密 Key）

### 10. 测试

- [ ] 10.1 Mock litellm 响应，测试 chat_completion 路由正确性
- [ ] 10.2 测试流式响应 chunk 解析
- [ ] 10.3 测试 API Key 加密/解密往返
- [ ] 10.4 测试超时控制逻辑
- [ ] 10.5 测试多 Key 轮换逻辑
