# M2 — Agent服务 (`agent_service`)

> 模块职责：管理Agent的全生命周期——创建、配置、版本、模板、启用/禁用。

---

## 子任务

### 1. Agent CRUD

- [ ] 1.1 定义 Agent ORM 模型（agents 表）— 含所有字段：name, emoji, system_prompt, persona, tools(JSONB), permission_level, default_model, temperature, max_tokens, timeout_seconds, is_preset, is_active, template_id, config_json
- [ ] 1.2 实现 `list_agents(filters)` — 支持搜索（名称）+ 分类筛选（角色/权限/工具/活跃状态）+ 分页
- [ ] 1.3 实现 `get_agent(agent_id)` — 获取 Agent 详情
- [ ] 1.4 实现 `create_agent(data)` — 创建自定义 Agent（校验权限级别 1-4、工具列表引用有效性）
- [ ] 1.5 实现 `update_agent(agent_id, data)` — 更新 Agent 配置（自动触发版本快照）
- [ ] 1.6 实现 `delete_agent(agent_id)` — 删除 Agent（is_preset=true 时拒绝删除）
- [ ] 1.7 实现 `toggle_agent(agent_id, active)` — 启用/禁用 Agent

### 2. 系统预设 Agent

- [ ] 2.1 通过 YAML 配置文件定义三个预设 Agent（数字主管/风控顾问/数据专家）的初始数据
- [ ] 2.2 在应用启动时检查预设 Agent 是否存在，不存在则自动创建
- [ ] 2.3 预设 Agent 禁止删除（delete_agent 校验 is_preset 字段）

### 3. Persona 与 Emoji 头像

- [ ] 3.1 Agent 创建/编辑时分配 Emoji 头像（预设 Agent 固定 emoji：🎯🛡️📊）
- [ ] 3.2 自定义 Agent 提供 Emoji 选择器数据（emoji 列表）
- [ ] 3.3 Persona 风格字段存储为 VARCHAR，描述 Agent 的语气风格

### 4. Agent 版本管理

- [ ] 4.1 定义 AgentVersion ORM 模型（agent_versions 表）
- [ ] 4.2 update_agent 时自动创建版本快照：记录变更前 system_prompt, tools, permission_level, default_model, temperature, max_tokens
- [ ] 4.3 version_number 自增（当前最大版本号 + 1）
- [ ] 4.4 实现 `list_versions(agent_id)` — 返回版本历史列表（按版本号降序）
- [ ] 4.5 实现 `get_version(agent_id, version)` — 获取特定版本配置
- [ ] 4.6 实现 `rollback_version(agent_id, version)` — 回滚到指定版本（回滚 = 创建新版本，内容拷贝自目标版本）

### 5. Agent 模板库

- [ ] 5.1 通过 YAML 文件定义 Agent 模板（市场分析/代码审查/文档撰写/数据分析/安全审计等）
- [ ] 5.2 实现 `list_templates()` — 返回模板列表，支持分类筛选
- [ ] 5.3 实现 `instantiate_template(template_id)` — 基于模板创建 Agent（拷贝 template 配置，写入 agents 表，记录 template_id + template_category 来源）

### 6. Agent 发现与搜索

- [ ] 6.1 list_agents 支持按关键词搜索（名称模糊匹配）
- [ ] 6.2 支持按角色/权限级别/启用的工具/活跃状态筛选
- [ ] 6.3 支持按使用频率排序（关联 conversation 表的 agent_id 出现次数）或最近使用排序（updated_at）

### 7. API 端点

- [ ] 7.1 `GET /api/agents` — Agent 列表（搜索+筛选+分页）
- [ ] 7.2 `POST /api/agents` — 创建自定义 Agent
- [ ] 7.3 `GET /api/agents/{id}` — Agent 详情
- [ ] 7.4 `PATCH /api/agents/{id}` — 更新 Agent 配置
- [ ] 7.5 `DELETE /api/agents/{id}` — 删除自定义 Agent
- [ ] 7.6 `PUT /api/agents/{id}/toggle` — 启用/禁用
- [ ] 7.7 `GET /api/agents/{id}/versions` — 版本历史
- [ ] 7.8 `GET /api/agents/{id}/versions/{version}` — 特定版本
- [ ] 7.9 `POST /api/agents/{id}/versions/{version}/rollback` — 回滚
- [ ] 7.10 `GET /api/agents/templates` — 模板列表
- [ ] 7.11 `POST /api/agents/templates/{template_id}/instantiate` — 基于模板创建

### 8. Pydantic Schema

- [ ] 8.1 AgentCreate / AgentUpdate / AgentInfo / AgentDetail / AgentFilter Schema
- [ ] 8.2 AgentVersion / AgentVersionDiff Schema
- [ ] 8.3 AgentTemplate / AgentTemplateCategory Schema

### 9. 测试

- [ ] 9.1 测试 Agent CRUD 完整流程
- [ ] 9.2 测试预设 Agent 不可删除
- [ ] 9.3 测试版本自动创建 + 回滚
- [ ] 9.4 测试模板实例化
