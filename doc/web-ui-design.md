# NEXUS AI — 多Agent协作平台 网页设计文档

> 版本：v1.0 | 日期：2026-06-09 | 状态：初稿

---

## 1. 引言

### 1.1 设计依据

本文档依据以下输入编写：

- 《[NEXUS AI 需求文档](proposal.md)》——功能需求和UI描述（第2.10节）及前端技术栈（第3.2节）
- 《[原型图](web.html)》——主聊天界面的三栏布局视觉参考
- 《[概要设计文档](high-level-design.md)》——前端模块划分（F1-F7）

### 1.2 前端技术栈

| 项目 | 选型 |
|------|------|
| 框架 | React 18+ (TypeScript 5+) |
| 构建 | Vite 5+ |
| 样式 | Tailwind CSS 3+ |
| 组件库 | shadcn/ui (基于Radix UI) |
| 图标 | Lucide React |
| 状态管理 | Redux Toolkit |
| 路由 | React Router v6 |
| HTTP | 原生 fetch (封装于 services/api.ts) |
| WebSocket | 原生 WebSocket + 自定义心跳 + 指数退避重连 |
| 代码高亮 | Shiki (VS Code同款引擎) |
| Markdown | react-markdown + remark-gfm + rehype-highlight |
| 虚拟滚动 | react-virtuoso |
| 异常追踪 | Sentry |
| 代码规范 | Biome |

### 1.3 设计原则

1. **一致性**：全局统一的深色/浅色主题系统，所有页面共享Layout Shell（标题栏+状态栏）
2. **渐进增强**：核心聊天功能优先，GPU监控等硬件依赖功能优雅降级
3. **即时反馈**：流式渲染、进度条、步骤状态指示、桌面通知——用户始终感知系统状态
4. **性能优先**：虚拟滚动（react-virtuoso）处理长消息列表，无限滚动按需加载历史消息
5. **无障碍基础**：合理的ARIA标签、键盘导航支持、色彩对比度满足WCAG AA

---

## 2. 全局布局

### 2.1 主聊天界面 — 三栏布局

主聊天界面（`/conversations/:id`）采用三栏布局，参考原型图：

```
┌──────────────────────────────────────────────────────┐
│  顶部标题栏: Logo | 品牌名 | 版本 | [模型▾] | 🖥️      │  h-10
├──────────┬─────────────────────┬─────────────────────┤
│ 左栏 24% │   中间主区域 60%     │   右栏 16%          │
│          │                     │                     │
│ Tab:     │  消息展示区          │  Tab: 性能|安全     │
│ 会话|资产 │  (react-virtuoso)  │                     │
│          │  虚拟滚动            │  硬件监控            │
│ 新建对话  │                     │  GPU: ████░░ 52%   │
│          │  ·AI回复卡片         │  内存: ███░░░ 44%  │
│ 置顶空间  │  ·代码块[复制][运行] │                     │
│ ·产品运营│  ·进度条             │  近期活动            │
│ ·项目开发│  ·操作按钮           │  ·数字主管 刚刚     │
│          │                     │  ·风控顾问 1分钟前  │
│ 活跃会话  │                     │  ·数据专家 2分钟前  │
│ ·竞品分析│                     │                     │
│ ·财报数据│  输入区              │                     │
│ ·用户偏好│  [模型▾]            │                     │
│          │  [@Agent][#文件]    │                     │
│          │  [附件][图片][终端]  │                     │
│          │  [输入框]     [发送] │                     │
├──────────┴─────────────────────┴─────────────────────┤
│  底部状态栏: DeepSeek API | Token: 12.5K | 导出日志 │  h-9
└──────────────────────────────────────────────────────┘
```

### 2.2 顶部标题栏 (`TitleBar`)

- 左侧：Logo图标 + 品牌名 + 版本号 + 系统标识（如 "DeepSeek V6.2.0 | NEXUS AI"）
- 中间：**模型切换下拉菜单**（顶部入口，与输入区旁入口联动）
- 右侧：窗口控制按钮（最小化/最大化/关闭，桌面应用风格）
- 高度：`h-10`（40px）
- 颜色：品牌主色背景 + 白色文字（`bg-primary text-white`）

### 2.3 底部状态栏 (`StatusBar`)

- 左侧：
  - API连接状态指示（图标+模型名称+ "API Key已配置" / "未配置" / "连接异常"）
  - Token用量统计（当次会话累计 / 当日累计）
- 右侧：
  - 「导出日志」入口（点击弹出审计日志导出对话框）
  - 「PING XXms」网络延迟显示
- 高度：`h-9`（36px）
- 样式：`border-t border-gray-200` + 浅灰背景

### 2.4 主题切换 (`ThemeToggle`)

- 位于状态栏或设置中，提供深色模式 / 浅色模式切换
- 默认浅色模式
- 通过Redux `uiSlice` 管理当前主题，Tailwind CSS `dark:` 类实现样式切换
- 切换状态持久化到 `localStorage`

---

## 3. 页面体系

系统共有 **8个主要页面/视图**，通过React Router管理。

### 3.1 页面路由表

| 路由 | 页面名称 | 对应模块 | 说明 |
|------|---------|---------|------|
| `/` | 首页/重定向 | — | 重定向到最近的活跃会话，无会话则显示空状态 |
| `/conversations` | 会话列表 | F2 | 无具体会话选中时的会话浏览页 |
| `/conversations/:id` | 主聊天界面 | F1+F2+F4+F5+F6+F7 | 三栏布局聊天核心界面 |
| `/agents` | Agent管理列表 | F3+F7 | 浏览所有Agent，搜索和筛选 |
| `/agents/new` | 新建Agent | F3+F7 | Agent创建表单 |
| `/agents/:id` | Agent编辑 | F3+F7 | Agent配置编辑（含版本历史入口） |
| `/agents/:id/versions` | Agent版本历史 | F3+F7 | 版本列表+对比+回滚 |
| `/agents/templates` | Agent模板库 | F3+F7 | 模板画廊+一键创建 |
| `/assets` | 资产管理 | F4+F7 | 独立的资产管理全页（也可从左侧栏Tab访问） |
| `/settings` | 设置（模型配置等） | F7 | 模型提供商配置 |

### 3.2 页面详述

#### 3.2.1 主聊天界面 (`/conversations/:id`)

**左侧栏（24%）：**
- Tab切换：「会话」|「资产」
- **会话Tab**（默认）：
  - 「新建对话」按钮（`bg-primary text-white`，全宽）
  - 置顶空间区域（拖动排序，展开/折叠）
  - 活跃会话列表（按最近活跃时间排序）
  - 每项显示：图标+标题+最新状态摘要
  - 当前活跃会话高亮（边框色标记）
  - 滚动区域（独立滚动，不随主内容区滚动）
- **资产Tab**：
  - 文件搜索框
  - 按类型筛选（全部/CSV/Excel/PDF/图片/其他）
  - 文件列表（缩略图/图标+名称+大小+日期）
  - 点击触发放大预览或表格渲染

**中间主区域（60%）：**
- 消息展示区：
  - react-virtuoso虚拟滚动，无限向上加载历史消息
  - 消息气泡（用户居右/Agent居左）
  - Agent消息带头像(Emoji)+名称
  - 富内容渲染：Markdown文本、Shiki代码块、进度条、操作按钮卡片、表格
  - 代码块四个按钮：复制/运行/编辑/下载
  - 流式渲染：WebSocket接收text_delta，逐Token追加到消息气泡
- 输入区：
  - 顶部工具栏：📎附件 🖼️图片 🎤麦克风 Wi-Fi 终端图标
  - 输入框（多行textarea，自动增高）：
    - 支持 `@Agent名称` 提及（弹出Agent选择下拉）
    - 支持 `#文件名` 引用资产（弹出文件选择下拉）
    - 支持 `/命令` 快捷操作（/clear, /export, /stop, /help）
  - 右侧发送按钮
  - 快捷键：`Ctrl+Enter` 发送，`Enter` 换行
  - 模型切换按钮（输入区入口，与顶部下拉联动）

**右侧面板（16%）：**
- Tab切换：「性能」|「安全」
- 内容详见第6节

#### 3.2.2 Agent管理列表 (`/agents`)

- 顶部：搜索框 + 分类筛选下拉（按角色/权限/工具/活跃状态）
- 排序选项：使用频率 / 最近使用 / 名称
- Agent卡片网格（2-3列）：
  - Emoji头像（大号，居中）
  - Agent名称
  - 角色描述（一行截断）
  - 启用的工具图标行（小图标）
  - 状态标签（活跃/已禁用）
  - 权限级别徽章（L1-L4）
  - 点击卡片 → 跳转编辑页
- 「新建Agent」浮动按钮（右下角）

#### 3.2.3 Agent编辑器 (`/agents/:id` 和 `/agents/new`)

- 表单布局（左右分栏或上下分节）：
  - **基本信息**：名称输入框、Emoji选择器（emoji picker面板）
  - **System Prompt**：大文本编辑器（等宽字体，支持Markdown语法高亮提示）
  - **Persona风格**：下拉选择 + 预览文本
  - **工具集**：多选勾选框组（代码执行/SQL/文件读写/网络搜索/API调用），每项带简要描述
  - **默认模型**：下拉选择（从可用模型列表中选择）
  - **权限级别**：滑块或单选按钮组（L1-L4，带说明文字）
  - **温度参数**：滑块（0-2，步长0.1）+ 数值显示
  - **最大Token数**：数字输入框
  - **超时时间**：数字输入框（秒）
- 底部按钮：保存（自动创建版本快照）/ 取消
- 系统预设Agent编辑时禁止保存为覆盖（只允许「另存为新Agent」或修改后自动创建新版本）

#### 3.2.4 Agent版本历史 (`/agents/:id/versions`)

- 时间线视图（垂直时间线）：
  - 每个版本节点显示：版本号、变更摘要、创建时间、操作人
  - 点击节点 → 展开该版本的完整配置（只读）
- 版本对比模式：
  - 选择两个版本（A/B）
  - 并排Diff视图，高亮System Prompt变更、工具集增减、参数修改
- 回滚操作：
  - 在特定版本节点 → 点击「回滚到此版本」
  - 弹出确认对话框（回滚会创建新版本，而非覆盖当前版本）
- 返回按钮 → 回到Agent编辑页

#### 3.2.5 Agent模板库 (`/agents/templates`)

- 分类标签页：全部/数据分析/代码审查/文档撰写/市场分析/安全审计/自定义
- 模板卡片网格（2-3列）：
  - 预设Emoji + 模板名称
  - 简要描述（一句话）
  - 预设的System Prompt摘要
  - 「使用此模板」按钮
- 点击「使用此模板」→ 弹出确认对话框（可修改名称）→ 创建Agent → 跳转到编辑页

#### 3.2.6 资产面板（独立页面 `assets` 或左侧栏Tab）

- 详见3.2.1左侧栏「资产Tab」的描述
- 独立页面提供更宽阔的布局：
  - 左侧：目录树（按类型/标签/上传时间组织）
  - 右侧：文件列表 + 预览区
- 预览功能：
  - 图片（PNG/JPG）：缩略图网格 + 点击放大灯箱
  - PDF：内嵌PDF.js查看器
  - 文本/代码/JSON：Shiki代码高亮预览
  - CSV/Excel：表格渲染（ag-grid或自定义表格组件）
  - 其他：文件图标+名称+大小+类型，点击下载

#### 3.2.7 会话导出对话框 (`ExportDialog`)

- 触发方式：底部状态栏、会话列表右键菜单、/export命令
- 对话框内容：
  - 格式选择：Markdown / PDF / JSON（单选按钮或Tab切换）
  - 包含选项（多选）：
    - 包含代码块
    - 包含Agent消息分析
    - 包含附件链接
  - 「导出」按钮 → 调用API下载
  - 「取消」按钮

#### 3.2.8 模型配置页面 (`/settings`)

- 模型提供商列表：
  - 每个提供商显示：名称(DeepSeek/OpenAI/Anthropic)、状态(活跃/禁用)、模型数量
  - 「添加提供商」按钮
- 点击进入提供商详情：
  - API Base URL输入框
  - API Key输入（密码字段，显示已配置/未配置状态）
  - 模型列表（可增删模型条目，每项：模型ID/显示名称/最大Token/费率）
  - 速率限制设置（每分钟请求数）
  - 超时设置（秒）

---

## 4. 组件树设计

### 4.1 完整组件层级

```
<App>                                              ← ThemeProvider + ErrorBoundary + Sentry
  <BrowserRouter>
    <Routes>
      <Route element={<MainLayout/>}>               ← 三栏布局容器 (F1)
        │
        ├── <TitleBar/>                             ← 顶部标题栏 (F1)
        │     ├── <Logo/>
        │     └── <ModelSelector/>                  ← 模型下拉 (F7)
        │
        ├── <div class="flex flex-1">
        │     │
        │     ├── <Sidebar/>                        ← 左侧栏 (F1容器)
        │     │     ├── <TabBar/>                   ← 会话/资产 Tab切换
        │     │     ├── <NewConversationButton/>
        │     │     ├── <ConversationList/>         ← 会话列表 (F2)
        │     │     │     ├── <PinnedSpaces/>       ← 置顶空间 (F2)
        │     │     │     │     └── <SpaceItem/> × N
        │     │     │     └── <ConversationItem/> × N  ← 活跃会话项 (F2)
        │     │     └── <AssetPanel/>               ← 资产面板 (F4)
        │     │           ├── <SearchInput/>         ← (F7)
        │     │           ├── <FileTypeFilter/>
        │     │           ├── <FileList/>
        │     │           └── <AssetPreview/>        ← 文件预览 (F4)
        │     │
        │     ├── <ChatArea/>                       ← 聊天主区域 (F2)
        │     │     ├── <MessageList/>              ← react-virtuoso (F2)
        │     │     │     └── <MessageBubble/> × N  ← 消息气泡 (F2)
        │     │     │           ├── <AgentAvatar/>  ← Emoji头像
        │     │     │           ├── <MarkdownContent/>  ← react-markdown渲染
        │     │     │           ├── <CodeBlock/>    ← Shiki高亮 (F6)
        │     │     │           │     ├── <CopyButton/>
        │     │     │           │     ├── <RunButton/>
        │     │     │           │     ├── <EditButton/>
        │     │     │           │     └── <DownloadButton/>
        │     │     │           ├── <CodeEditorPanel/>  ← 展开编辑面板 (F6)
        │     │     │           ├── <ProgressBar/>      ← 执行进度条 (F6)
        │     │     │           ├── <TaskPlanCard/>     ← 任务计划卡片 (F2)
        │     │     │           ├── <ActionButtons/>    ← 操作按钮组 (F2)
        │     │     │           ├── <VariableTableView/>← 变量表查看 (F2)
        │     │     │           └── <TableRenderer/>    ← 数据表格
        │     │     └── <InputArea/>                 ← 输入区域 (F2)
        │     │           ├── <Toolbar/>             ← 附件/图片/麦克风/WiFi/终端
        │     │           ├── <ModelSelector/>       ← 模型切换 (F7)
        │     │           ├── <MentionInput/>        ← 富交互输入 (@Agent/#文件//命令)
        │     │           └── <SendButton/>
        │     │
        │     └── <RightPanel/>                     ← 右侧面板 (F1容器)
        │           ├── <TabBar/>                   ← 性能/安全 Tab切换
        │           ├── <PerformanceTab/>           ← 性能监控 (F5)
        │           │     ├── <GpuMonitor/>         ← GPU进度条 (F5)
        │           │     └── <MemoryMonitor/>      ← 内存进度条 (F5)
        │           ├── <SecurityTab/>              ← 安全面板 (F5)
        │           │     └── <AuditLogViewer/>     ← 审计日志查看
        │           └── <AgentActivity/>            ← Agent活动列表 (F5)
        │                 └── <AgentActivityItem/> × N
        │
        └── <StatusBar/>                            ← 底部状态栏 (F1)
              ├── <ApiStatus/>                      ← API连接状态
              ├── <TokenUsage/>                     ← Token用量
              ├── <ExportLogButton/>
              └── <PingIndicator/>

      <!-- 独立页面路由（使用MainLayout或独立布局） -->
      <Route path="/agents" element={<AgentListPage/>}/>    (F3)
      │     ├── <SearchInput/>                              (F7)
      │     ├── <FilterDropdown/>                           (F7)
      │     └── <AgentCard/> × N                            (F3)

      <Route path="/agents/new" element={<AgentEditorPage/>}/>  (F3)
      <Route path="/agents/:id" element={<AgentEditorPage/>}/>  (F3)
      │     ├── <AgentForm/>                               (F3)
      │     │     ├── <EmojiPicker/>
      │     │     ├── <SystemPromptEditor/>
      │     │     ├── <ToolCheckboxGroup/>
      │     │     ├── <PermissionSlider/>
      │     │     └── <ConfigParams/>
      │     └── <VersionHistoryLink/>                      → 跳转版本页

      <Route path="/agents/:id/versions" element={<AgentVersionPage/>}/>  (F3)
      │     ├── <VersionTimeline/>                         (F3)
      │     ├── <VersionDiff/>                             (F3)
      │     └── <RollbackButton/>

      <Route path="/agents/templates" element={<AgentTemplatePage/>}/>  (F3)
      │     ├── <CategoryTabs/>
      │     └── <TemplateCard/> × N                        (F3)

      <Route path="/assets" element={<AssetPage/>}/>       (F4)

      <Route path="/settings" element={<SettingsPage/>}/>   (F7)
            ├── <ProviderList/>
            └── <ProviderDetail/>

      <Route path="/conversations" element={<ConversationBrowse/>}/>  (F2)
    </Routes>
  </BrowserRouter>

  <!-- 全局覆盖层 -->
  <ExportDialog/>          ← 会话导出对话框 (F7)
  <Modal/>                 ← 通用模态框 (F7)
  <Toast/>                 ← 全局Toast通知 (F7)
</App>
```

### 4.2 组件与前端模块的归属

| 模块ID | 模块名称 | 包含的组件 |
|--------|---------|-----------|
| F1 | Layout Shell | `MainLayout`, `TitleBar`, `Logo`, `StatusBar`, `ThemeToggle`, `Sidebar`, `RightPanel`, `TabBar` |
| F2 | Conversation UI | `ConversationList`, `PinnedSpaces`, `SpaceItem`, `ConversationItem`, `NewConversationButton`, `ChatArea`, `MessageList`, `MessageBubble`, `AgentAvatar`, `MarkdownContent`, `TaskPlanCard`, `ActionButtons`, `VariableTableView`, `TableRenderer`, `InputArea`, `Toolbar`, `MentionInput`, `SendButton` |
| F3 | Agent Manager UI | `AgentListPage`, `AgentCard`, `AgentEditorPage`, `AgentForm`, `EmojiPicker`, `SystemPromptEditor`, `ToolCheckboxGroup`, `PermissionSlider`, `ConfigParams`, `AgentVersionPage`, `VersionTimeline`, `VersionDiff`, `AgentTemplatePage`, `TemplateCard`, `CategoryTabs` |
| F4 | Asset UI | `AssetPanel`, `AssetPage`, `FileTypeFilter`, `FileList`, `AssetPreview` |
| F5 | Monitor Panel | `PerformanceTab`, `GpuMonitor`, `MemoryMonitor`, `SecurityTab`, `AuditLogViewer`, `AgentActivity`, `AgentActivityItem` |
| F6 | Code Display | `CodeBlock`, `CopyButton`, `RunButton`, `EditButton`, `DownloadButton`, `CodeEditorPanel`, `ProgressBar` |
| F7 | Shared Components | `ModelSelector`, `ExportDialog`, `Modal`, `Dropdown`, `Toast`, `SearchInput`, `EmptyState`, `ApiStatus`, `TokenUsage`, `PingIndicator`, `ExportLogButton`, `FilterDropdown` |

### 4.3 状态管理数据流

#### Redux Store 结构

```typescript
interface RootState {
  conversations: ConversationState;   // conversationSlice
  agents: AgentState;                 // agentSlice
  monitor: MonitorState;              // monitorSlice
  ui: UIState;                        // uiSlice (主题、侧栏展开状态等)
  models: ModelState;                 // modelSlice (当前选中模型、可用模型列表)
}
```

#### Store 详细结构

```typescript
// conversationSlice — 由 F1, F2 消费
interface ConversationState {
  conversations: ConversationSummary[];  // 会话列表
  currentId: string | null;              // 当前活跃会话ID
  messages: Message[];                   // 当前会话消息
  loading: boolean;
  sending: boolean;
  hasMore: boolean;                      // 是否还有更多历史消息
}

// agentSlice — 由 F3 消费
interface AgentState {
  agents: AgentInfo[];              // Agent列表
  currentAgent: AgentDetail | null; // 当前查看/编辑的Agent
  versions: AgentVersion[];         // 当前Agent的版本列表
  templates: AgentTemplate[];       // 模板列表
  filters: AgentFilter;             // 搜索/筛选条件
}

// monitorSlice — 由 F5 消费，通过WS推送更新
interface MonitorState {
  hardware: HardwareStats | null;       // GPU+内存实时数据
  containers: ContainerStats[];         // 容器状态列表
  agentActivities: AgentActivityItem[]; // Agent活动列表
}

// uiSlice — 由 F1 全局消费
interface UIState {
  theme: 'light' | 'dark';
  sidebarTab: 'conversations' | 'assets';
  rightPanelTab: 'performance' | 'security';
  sidebarExpanded: boolean;
}

// modelSlice — 由 F7 全局消费
interface ModelState {
  currentModelId: string;         // 当前选中的模型ID
  availableModels: ModelInfo[];   // 可用模型列表（含提供商信息）
  providers: ProviderInfo[];      // 模型提供商列表
}
```

#### 数据流向

```
WebSocket Message ──→ dispatch(reduxAction) ──→ Store更新 ──→ 组件重渲染
     │                                                │
     │  text_delta ──→ addToken(msgId, delta)         ├── MessageBubble (实时追加文本)
     │  step_status ──→ updateOrchStatus(...)          ├── TaskPlanCard (更新步骤状态)
     │  code_progress ──→ updateCodeProgress(...)       ├── CodeBlock + ProgressBar
     │  agent_status ──→ updateAgentStatus(...)         ├── AgentActivity (右侧面板)
     │  hardware_stats ──→ updateHardware(...)          └── PerformanceTab
     │
HTTP API Response ──→ dispatch(setXxx(data)) ──→ Store更新 ──→ 组件重渲染
```

---

## 5. 核心交互设计

### 5.1 聊天消息流

**加载策略：**
- 首次加载最近50条消息（cursor-based分页）
- 向上滚动到顶部时，自动加载更早的消息（无限滚动，react-virtuoso `endReached`）
- 加载状态：底部显示spinner或"加载中..."
- 加载完成且无更多数据时显示"—— 以上是全部消息 ——"

**流式渲染：**
- WebSocket接收 `text_delta` → 找到对应消息气泡 → 追加delta到content
- 首次 `text_delta` 创建空的Agent消息气泡，后续delta追加文本
- Markdown实时解析渲染（react-markdown），代码块在 ```闭合后触发高亮
- 流式过程中Agent头像旁显示"输入中..."动画

**消息气泡样式：**
- 用户消息：居右，蓝色背景，白色文字，圆角
- 数字主管：居左，灰色背景 + 主管色边框 + 🎯头像
- Worker Agent：居左，浅灰背景 + Agent专属色边框 + 各自Emoji头像

### 5.2 消息输入交互

**@Agent提及：**
- 用户输入 `@` → 弹出Agent选择下拉（搜索+筛选）
- 下拉列表显示：Emoji头像 + Agent名称 + 角色简述
- 选中后插入 `@Agent名称 ` 到光标位置
- 后端解析mentions数组，不依赖文本匹配

**#文件引用：**
- 用户输入 `#` → 弹出资产文件选择下拉
- 下拉列表显示：文件图标 + 文件名 + 类型标签
- 选中后插入 `#文件名 ` 到光标位置

**/命令快捷操作：**
- 用户输入 `/` → 弹出命令提示下拉
- 支持命令：`/clear`（清空上下文）、`/export`（导出会话）、`/stop`（停止任务）、`/help`（帮助）
- 命令提示显示命令名 + 简要说明

**快捷键：**
- `Ctrl+Enter`：发送消息
- `Enter`：换行
- `Ctrl+/`：触发命令模式

### 5.3 代码块操作

每个代码块（`CodeBlock`）提供四个操作按钮：

| 按钮 | 图标 | 功能 | 反馈 |
|------|------|------|------|
| **复制** | 📋 | 复制代码文本到剪贴板 | Toast "已复制" |
| **运行** | ▶️ | 发送到沙箱执行 | 显示ProgressBar，完成后在代码块下方展示stdout/stderr |
| **编辑** | ✏️ | 展开为独立代码编辑面板 | 滑出或弹出CodeEditorPanel，内嵌等宽编辑器 |
| **下载** | ⬇️ | 下载为.py文件 | 浏览器触发下载 |

**代码编辑面板 (`CodeEditorPanel`)：**
- 以侧边面板或底部面板形式展开
- 使用等宽字体编辑区（textarea或contenteditable）
- 顶部显示文件名 + 语言标签
- 底部按钮：▶️执行（重新运行修改后的代码）、💾保存到资产库、❌关闭面板
- 执行后结果显示在面板下方

### 5.4 模型切换

**双入口设计：**

1. **顶部标题栏下拉** (`TitleBar` → `ModelSelector`)：
   - 下拉菜单显示所有可用模型，按提供商分组
   - 每个模型项显示：模型名称 + 提供商标签 + 当前Agent默认标记
   - 选中后全局生效（当前会话使用该模型）

2. **输入区旁快捷按钮** (`InputArea` → `ModelSelector`)：
   - 紧凑的下拉或图标按钮
   - 与顶部下拉共享同一个 `ModelSelector` 组件
   - 两处状态联动（Redux `modelSlice.currentModelId`）

**切换行为：**
- 切换即时生效（下一轮对话使用新模型）
- 不影响当前进行中的LLM调用
- 选择持久化到当前会话（存储在conversations表的model_id字段）

### 5.5 任务执行计划展示与人工介入

**执行计划卡片 (`TaskPlanCard`)：**
- 数字主管拆解任务后，WS推送 `task_plan` 消息
- 在聊天区渲染为独立的执行计划卡片：
  - 卡片标题："📋 执行计划"
  - 步骤列表（有序号）：
    - 每项显示：步骤编号 + 描述 + 分配的Agent（Emoji+名称）+ 依赖标记
    - 状态图标：⏳待执行 / 🔄执行中 / ✅完成 / ❌失败 / ⏸️待确认
  - 依赖关系可视化（缩进或箭头连线）
  - 并行执行的步骤用 `[并行]` 标签标记

**确认模式交互：**
- 需要用户确认的步骤（`confirm_required: true`）：
  - Worker执行到该步骤时暂停，步骤状态变为「待确认」
  - 在消息区显示确认卡片：操作描述 + 「✅确认执行」+ 「❌跳过」按钮
  - 用户点击确认后，步骤继续执行
- 用户可在任务计划卡片中手动调整：修改子任务、更换Worker、取消某步骤

**控制操作：**
- 暂停：暂停按钮或 `/stop` 命令 → WS发送 `control: pause`
- 恢复：恢复按钮 → WS发送 `control: resume`
- 取消：取消按钮 → WS发送 `control: cancel`

### 5.6 变量表查看

**变量表查看器 (`VariableTableView`)：**
- 在聊天区以折叠面板或侧边抽屉形式展示
- 表格显示：变量名 / 类型 / 值摘要 / 创建者Agent / 创建步骤
- 变量类型图标：
  - `str` → 🔤 文本
  - `int/float` → 🔢 数值
  - `DataFrame` → 📊 数据表（显示行列数）+ 点击展开表格预览
  - `image` → 🖼️ 图片缩略图
  - `path` → 📁 文件路径
- 更新时高亮闪烁（WS推送 `variable_update`）

### 5.7 文件上传与预览

**上传流程：**
1. 点击📎附件按钮 → 弹出系统文件选择对话框
2. 选择文件 → 显示上传进度条
3. 上传完成 → 文件出现在资产列表中
4. 输入框中自动插入 `#文件名` 引用
5. 文件大小超过50MB → Toast错误提示

**预览模式：**
- 点击资产列表中的文件 → 触发预览
- 预览在中间区域以模态框或侧边面板展开（不离开聊天上下文）：
  - 图片：灯箱放大，支持左右切换
  - PDF：内嵌PDF.js查看器，支持翻页
  - CSV/Excel：表格渲染，支持排序/筛选
  - 文本/代码/JSON：Shiki代码高亮
  - 其他：显示元数据（文件名/大小/类型/上传时间）+ 下载按钮

### 5.8 桌面通知

**触发条件：**
- 长时间任务完成
- 需用户确认的操作
- Agent状态异常（error）
- Worker全部完成后主管生成最终回复

**实现：**
- 使用浏览器 `Notification API`
- 用户首次使用时请求通知权限
- 通知内容包含：Agent图标 + 任务简述 + 时间
- 点击通知 → 聚焦浏览器窗口 → 跳转到对应会话

---

## 6. 右侧面板详设

### 6.1 性能监控Tab

**硬件监控区：**

| 指标 | 展示方式 | 更新频率 |
|------|---------|---------|
| GPU显存 | 进度条 (已用/总量) + 百分比 + 数值 | 每5秒 |
| GPU利用率 | 进度条 + 百分比 | 每5秒 |
| 系统内存 | 进度条 (已用/总量) + 百分比 + 数值 | 每5秒 |

- 进度条颜色：<50%绿色 / 50-80%黄色 / >80%红色
- 无GPU环境：显示 "GPU不可用" 灰色状态，优雅降级不报错
- 有GPU但温度不可获取：只显示显存+利用率

**Docker容器状态区（可折叠）：**
- 运行中容器列表
- 每项显示：容器名 + CPU% + 内存使用
- 异常容器用红色标记

### 6.2 安全Tab

**审计日志查看器 (`AuditLogViewer`)：**
- 时间线列表（最近优先）：
  - 每条显示：操作类型图标 + 描述 + Agent名称 + 时间 + 状态标签
- 筛选栏：按时间范围 / Agent / 操作类型筛选
- 「导出日志」按钮 → 触发审计日志导出API
- 「查看更多」→ 展开筛选面板

**Agent权限状态：**
- 当前会话活跃Agent列表 + 各自权限级别徽章

### 6.3 Agent活动列表

- 实时显示所有Agent的最近活动状态：
  - Agent头像(Emoji) + 名称
  - 状态文本（如"正在拆解并生成任务..."）
  - 相对时间（刚刚/1分钟前/2分钟前）

- 状态指示：
  - 🟢 green (idle)：空闲
  - 🔵 blue (working)：工作中
  - 🟡 yellow (blocked)：等待确认
  - 🔴 red (error)：错误

---

## 7. 路由设计

### 7.1 路由配置

```typescript
const router = createBrowserRouter([
  {
    element: <MainLayout />,     // 三栏布局（有标题栏和状态栏）
    errorElement: <ErrorPage />,
    children: [
      { index: true, loader: redirectToLatestConversation },
      { path: 'conversations', element: <ConversationBrowse /> },
      { path: 'conversations/:id', element: <ChatView /> },  // 三栏聊天界面
    ],
  },
  {
    element: <PageLayout />,     // 通用页面布局（标题栏+状态栏，但无三栏）
    children: [
      { path: 'agents', element: <AgentListPage /> },
      { path: 'agents/new', element: <AgentEditorPage /> },
      { path: 'agents/:id', element: <AgentEditorPage /> },
      { path: 'agents/:id/versions', element: <AgentVersionPage /> },
      { path: 'agents/templates', element: <AgentTemplatePage /> },
      { path: 'assets', element: <AssetPage /> },
      { path: 'settings', element: <SettingsPage /> },
    ],
  },
]);
```

### 7.2 URL设计原则

- 支持URL直链到特定会话（`/conversations/:id`）
- Agent编辑支持直接分享链接
- 所有路由支持浏览器前进/后退导航
- 404页面提供返回首页的引导

---

## 8. 国际化预留

### 8.1 框架结构

第一版仅支持中文，但预留 i18n 框架：

```
src/i18n/
  ├── index.ts          # i18n初始化 (react-i18next)
  ├── zh-CN/            # 中文语言包
  │   ├── common.json   # 通用文案
  │   ├── chat.json     # 聊天相关
  │   ├── agents.json   # Agent管理相关
  │   └── errors.json   # 错误消息
  └── en/               # 英文语言包（预留）
```

### 8.2 使用方式

组件中使用 `useTranslation` hook：

```typescript
const { t } = useTranslation('chat');
<span>{t('input.placeholder')}</span>  // "输入您的问题..."
```

所有用户可见的文案均通过 i18n key引用，避免硬编码中文。

---

## 附录

### A. 与原型图对应关系

| 原型图元素 | 对应组件 | 对应设计章节 |
|-----------|---------|-------------|
| 顶部标题栏 (Logo + DeepSeek V6.2.0 + NEXUS AI + 下拉+ 窗口控制) | `TitleBar` + `ModelSelector` | 2.2, 5.4 |
| 左侧栏 (Tab: 会话\|资产 + 新建对话 + 置顶空间 + 活跃会话) | `Sidebar` + `ConversationList` + `PinnedSpaces` | 3.2.1 |
| 中间聊天区 (AI消息 + 代码块 + 进度条 + 成功卡片 + 操作按钮) | `ChatArea` + `MessageBubble` + `CodeBlock` + `TaskPlanCard` | 3.2.1, 5.3, 5.5 |
| 中间输入区 (附件\|图片\|麦克风\|WiFi\|终端 + 输入框 + 发送) | `InputArea` + `Toolbar` + `MentionInput` | 5.2 |
| 右侧面板 (Tab: 性能\|安全 + GPU/内存进度条 + 近期活动) | `RightPanel` + `PerformanceTab` + `AgentActivity` | 6.1, 6.3 |
| 底部状态栏 (API状态 + 导出日志 + PING) | `StatusBar` + `ApiStatus` + `TokenUsage` | 2.3 |

### B. 组件状态矩阵

每个组件至少需要考虑以下状态之一：

| 状态 | 说明 | 示例 |
|------|------|------|
| **Loading** | 数据加载中 | Skeleton占位符 / Spinner |
| **Empty** | 无数据 | `EmptyState` 组件（图标+提示文字+操作引导） |
| **Error** | 加载/操作失败 | Error Banner + 重试按钮 |
| **Success** | 操作成功 | Toast通知 / 绿色状态标记 |
| **Active** | 正在进行中 | 动画指示器 / 进度条 |
| **Disabled** | 不可用 | 灰色样式 + disabled属性 |

### C. 参考文档

- [NEXUS AI 需求文档 v2.0](proposal.md)
- [原型图](web.html)
- [概要设计文档](high-level-design.md)
