# F7 — 共享组件 (`shared_components`)

> 模块职责：模型选择器、导出对话框、Modal、Toast 等跨模块复用的基础组件。

---

## 子任务

### 1. Redux Store — uiSlice + modelSlice

- [ ] 1.1 定义 `uiSlice`：theme, sidebarTab, rightPanelTab, sidebarExpanded
- [ ] 1.2 定义 `modelSlice`：currentModelId, availableModels, providers
- [ ] 1.3 实现 thunk actions：fetchAvailableModels, fetchProviders, setCurrentModel
- [ ] 1.4 创建 selectors：selectCurrentModel, selectAvailableModels, selectTheme

### 2. 模型选择器 (`ModelSelector`)

- [ ] 2.1 下拉菜单显示所有可用模型，按提供商分组（DeepSeek / OpenAI / Anthropic）
- [ ] 2.2 每个模型项显示：模型名称 + 提供商标签 + 当前 Agent 默认标记
- [ ] 2.3 选中后更新 Redux modelSlice.currentModelId + 持久化到当前会话
- [ ] 2.4 两种样式：顶部标题栏下拉（完整版） + 输入区旁紧凑下拉（简化版），共享状态
- [ ] 2.5 切换即时生效（下一轮对话使用新模型）

### 3. 会话导出对话框 (`ExportDialog`)

- [ ] 3.1 模态框内容：
  - 格式选择：Markdown / PDF / JSON（RadioGroup 或 Tab 切换）
  - 包含选项（多选 checkbox）：
    - 包含代码块
    - 包含 Agent 消息分析
    - 包含附件链接
  - 「导出」按钮 + 「取消」按钮
- [ ] 3.2 点击导出 → API 调用 → 触发浏览器下载（Blob）
- [ ] 3.3 导出中显示 loading 状态

### 4. 通用模态框 (`Modal`)

- [ ] 4.1 基于 shadcn/ui Dialog 封装
- [ ] 4.2 支持：title + children + footer + onClose
- [ ] 4.3 支持尺寸：sm / md / lg / xl / full
- [ ] 4.4 点击背景关闭（可选），ESC 关闭
- [ ] 4.5 AnimatePresence 过渡动画

### 5. 通用下拉 (`Dropdown`)

- [ ] 5.1 基于 shadcn/ui DropdownMenu 或 Select 封装
- [ ] 5.2 支持：trigger + items（label + value + icon + disabled）
- [ ] 5.3 支持分组（group label）
- [ ] 5.4 选中状态标记

### 6. Toast 通知 (`Toast`)

- [ ] 6.1 基于 shadcn/ui Sonner 或 Toast
- [ ] 6.2 支持类型：success / error / warning / info
- [ ] 6.3 自动消失（可配置 duration）
- [ ] 6.4 支持 action 按钮（如 "重试"）
- [ ] 6.5 位置：右下角

### 7. 搜索输入 (`SearchInput`)

- [ ] 7.1 带搜索图标的 input
- [ ] 7.2 支持 debounce（300ms）后触发 onChange
- [ ] 7.3 可清除按钮（clear ×）

### 8. 空状态 (`EmptyState`)

- [ ] 8.1 居中显示：图标 + 标题 + 描述 + 可选操作按钮
- [ ] 8.2 用于：无会话、无 Agent、无资产等场景

### 9. API 服务层 (`services/api.ts`)

- [ ] 9.1 封装 `fetch` 基础方法：base URL + JSON 解析 + 错误处理
- [ ] 9.2 请求拦截器：注入 Content-Type / Accept headers
- [ ] 9.3 响应拦截器：统一错误处理（401/403/429/500 → Toast 提示）
- [ ] 9.4 定义 API 函数：conversationsApi, agentsApi, assetsApi, modelsApi, monitorApi, auditApi, tasksApi, exportApi

### 10. WebSocket 服务层 (`services/ws.ts`)

- [ ] 10.1 封装原生 WebSocket 连接
- [ ] 10.2 实现自动重连：指数退避（1s → 2s → 4s → 8s，max 30s）
- [ ] 10.3 实现心跳机制：每 30 秒发送 ping，期待 pong
- [ ] 10.4 连接状态管理：connecting / connected / disconnected / reconnecting
- [ ] 10.5 消息分发：onMessage 根据 type dispatch Redux action
- [ ] 10.6 资源清理：组件卸载时断开连接

### 11. 桌面通知服务 (`services/notification.ts`)

- [ ] 11.1 封装 Notification API
- [ ] 11.2 首次使用时请求通知权限
- [ ] 11.3 通知内容：Agent 图标 + 任务简述 + 时间
- [ ] 11.4 点击通知 → 聚焦浏览器 → 跳转到对应会话

### 12. 自定义 Hooks

- [ ] 12.1 `useWebSocket(url)` — WebSocket 连接 Hook（自动重连 + 心跳 + 分发消息）
- [ ] 12.2 `useConversation(convId)` — 会话数据 Hook
- [ ] 12.3 `useAgent(agentId?)` — Agent 数据 Hook
- [ ] 12.4 `useMonitor()` — 监控数据 Hook（WS 连接 /ws/monitor + /ws/agents）
- [ ] 12.5 `useTheme()` — 主题 Hook
- [ ] 12.6 `useNotification()` — 桌面通知 Hook

### 13. 工具函数 (`utils/`)

- [ ] 13.1 `markdown.ts` — react-markdown 配置（remark-gfm + rehype-highlight plugins）
- [ ] 13.2 `shiki.ts` — Shiki highlighter 初始化 + 主题配置
- [ ] 13.3 `format.ts` — 日期格式化（dayjs 或 Intl.RelativeTimeFormat）、文件大小格式化
- [ ] 13.4 `constants.ts` — 常量定义（权限级别、Agent 状态、操作类型等）

### 14. 国际化预留 (`i18n/`)

- [ ] 14.1 安装 react-i18next + i18next
- [ ] 14.2 创建 `i18n/index.ts` — i18n 初始化
- [ ] 14.3 创建 `zh-CN/common.json` — 通用文案（第一版仅中文）
- [ ] 14.4 创建 `zh-CN/chat.json` + `zh-CN/agents.json` + `zh-CN/errors.json`
- [ ] 14.5 预留 `en/` 目录结构
- [ ] 14.6 所有硬编码中文文案替换为 `t('key')` 调用

### 15. 模型配置页 (`/settings`)

- [ ] 15.1 模型提供商列表：名称 + 状态(活跃/禁用) + 模型数量 + 「添加」按钮
- [ ] 15.2 点击进入提供商详情：
  - API Base URL input
  - API Key input（密码字段，显示已配置/未配置）
  - 模型列表（可增删条目：模型ID + 显示名称 + 最大Token + 费率）
  - 速率限制设置
  - 超时设置

### 16. TypeScript 类型定义 (`types/`)

- [ ] 16.1 `index.ts` — 通用类型
- [ ] 16.2 `agent.ts` — Agent 相关类型（AgentInfo, AgentDetail, AgentCreate, AgentUpdate, AgentFilter, AgentVersion, AgentTemplate）
- [ ] 16.3 `conversation.ts` — 会话类型（ConversationSummary, ConversationDetail, ConversationCreate, ConversationUpdate, ConversationFilter）
- [ ] 16.4 `message.ts` — 消息类型（Message, MessagePage, ContentBlock, ToolCall, TaskPlan, StepStatus, VariableUpdate）
- [ ] 16.5 `asset.ts` — 资产类型（AssetInfo, AssetDetail, AssetFilter, PreviewData）
- [ ] 16.6 `ws.ts` — WebSocket 消息类型（全部 message types 的 TypeScript 接口）

### 17. 测试

- [ ] 17.1 测试 modelSlice + uiSlice reducer
- [ ] 17.2 测试 WebSocket 自动重连逻辑
- [ ] 17.3 测试 Toast 通知
- [ ] 17.4 测试 ExportDialog 交互
- [ ] 17.5 测试 i18n 翻译函数
