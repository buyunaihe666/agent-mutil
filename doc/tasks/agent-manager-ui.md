# F3 — Agent管理 (`agent_manager_ui`)

> 模块职责：Agent 列表/编辑、版本历史、模板库。

---

## 子任务

### 1. Redux Store — agentSlice

- [ ] 1.1 定义 AgentState 接口（agents, currentAgent, versions, templates, filters）
- [ ] 1.2 实现 thunk actions：fetchAgents, fetchAgent, createAgent, updateAgent, deleteAgent, toggleAgent, fetchVersions, fetchVersion, rollbackVersion, fetchTemplates, instantiateTemplate
- [ ] 1.3 创建 selectors：selectFilteredAgents, selectCurrentAgent, selectVersions, selectTemplates

### 2. Agent 列表页 (`/agents`)

- [ ] 2.1 顶部：SearchInput 搜索框 + FilterDropdown 分类筛选（按角色/权限/工具/活跃状态）
- [ ] 2.2 排序选项：使用频率 / 最近使用 / 名称
- [ ] 2.3 Agent 卡片网格（2-3列，responsive）
- [ ] 2.4 创建 `AgentCard` 组件：
  - Emoji 头像（大号，居中）
  - Agent 名称
  - 角色描述（一行截断，text-ellipsis）
  - 启用的工具图标行（小图标 row）
  - 状态标签（活跃/已禁用，绿色/灰色 badge）
  - 权限级别徽章（L1-L4，不同颜色）
  - 点击卡片 → 导航到 `/agents/:id`
- [ ] 2.5 「新建 Agent」浮动按钮（右下角，+ icon，bg-primary）

### 3. Agent 编辑器 (`/agents/new` 和 `/agents/:id`)

- [ ] 3.1 创建 `AgentForm` 表单组件（左右分栏或上下分节）：
  - **基本信息**：名称 input + Emoji 选择器面板
  - **System Prompt**：大 textarea（等宽字体，monospace）
  - **Persona 风格**：下拉 select + 预览文本
  - **工具集**：`ToolCheckboxGroup` — 多选 checkbox 组（代码执行/SQL/文件读写/网络搜索/API调用），每项带简要描述
  - **默认模型**：`ModelSelector` 下拉
  - **权限级别**：`PermissionSlider` — 滑块或 RadioGroup（L1-L4，带说明文字）
  - **温度参数**：Slider（0-2，步长0.1）+ 数值显示
  - **最大 Token 数**：数字 input
  - **超时时间**：数字 input（秒）
- [ ] 3.2 底部按钮：保存（自动创建版本快照）/ 取消
- [ ] 3.3 编辑模式：预填当前 Agent 配置
- [ ] 3.4 系统预设 Agent 编辑时：「另存为新 Agent」而非覆盖

### 4. Emoji 选择器 (`EmojiPicker`)

- [ ] 4.1 显示常用 emoji 网格（分类：表情/动物/自然/食物/活动/科技/符号）
- [ ] 4.2 搜索 emoji（按名称模糊匹配）
- [ ] 4.3 点击选择 → 更新 Agent.emoji 字段
- [ ] 4.4 预设 Agent 固定 emoji：🎯🛡️📊

### 5. 工具多选 (`ToolCheckboxGroup`)

- [ ] 5.1 显示可用工具列表：代码执行 / SQL查询 / 文件读写 / 网络搜索 / 外部API调用 / Agent通信
- [ ] 5.2 每项带：checkbox + 图标 + 名称 + 简要描述
- [ ] 5.3 已选工具以 JSONB 数组形式提交

### 6. 权限滑块 (`PermissionSlider`)

- [ ] 6.1 显示 4 级权限：L1 只读 / L2 分析 / L3 操作 / L4 管理
- [ ] 6.2 使用 RadioGroup 或 Slider，每级带说明文字
- [ ] 6.3 选中的级别高亮

### 7. Agent 版本历史页 (`/agents/:id/versions`)

- [ ] 7.1 创建 `VersionTimeline` 组件：垂直时间线（竖线 + 节点）
- [ ] 7.2 每个版本节点显示：版本号 + 变更摘要 + 创建时间
- [ ] 7.3 点击节点 → 展开该版本完整配置（只读展示）
- [ ] 7.4 创建 `VersionDiff` 组件：
  - 选择两个版本（A/B）
  - 并排 Diff 视图（System Prompt 变更、工具集增减、参数修改）
  - 高亮变更：绿色新增 / 红色删除
- [ ] 7.5 「回滚到此版本」按钮 → 弹出确认对话框 → 回滚创建新版本
- [ ] 7.6 返回按钮 → 回到 Agent 编辑页

### 8. Agent 模板库页 (`/agents/templates`)

- [ ] 8.1 创建 `CategoryTabs`：全部 / 数据分析 / 代码审查 / 文档撰写 / 市场分析 / 安全审计
- [ ] 8.2 创建 `TemplateCard` 模板卡片网格（2-3列）：
  - 预设 Emoji + 模板名称
  - 简要描述（一句话）
  - 预设 System Prompt 摘要
  - 「使用此模板」按钮
- [ ] 8.3 点击「使用此模板」→ 弹出确认对话框（可修改名称）→ API 创建 Agent → 导航到编辑页

### 9. 测试

- [ ] 9.1 测试 agentSlice reducer + thunks
- [ ] 9.2 测试 AgentCard 渲染
- [ ] 9.3 测试 Agent 编辑表单提交流程
- [ ] 9.4 测试版本时间线渲染
- [ ] 9.5 测试模板实例化
