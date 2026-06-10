# F2 — 会话交互 (`conversation_ui`)

> 模块职责：会话列表、聊天区、消息气泡、输入区。

---

## 子任务

### 1. Redux Store — conversationSlice

- [ ] 1.1 定义 ConversationState 接口（conversations, currentId, messages, loading, sending, hasMore）
- [ ] 1.2 实现 thunk actions：fetchConversations, createConversation, deleteConversation, updateConversation, fetchMessages, loadMoreMessages
- [ ] 1.3 实现同步 actions：setCurrentId, addMessage, appendToken, setSending
- [ ] 1.4 创建 selectors：selectCurrentConversation, selectMessages, selectConversations

### 2. 会话列表 (`ConversationList`)

- [ ] 2.1 渲染会话列表（按最近活跃时间排序）
- [ ] 2.2 每个 `ConversationItem` 显示：图标 + 标题 + 最新状态摘要（如"自动分析已启动..."）
- [ ] 2.3 当前活跃会话高亮（border-l-2 border-primary + bg-blue-50）
- [ ] 2.4 点击会话项 → 导航到 `/conversations/:id`
- [ ] 2.5 会话列表支持独立滚动（overflow-y-auto）
- [ ] 2.6 右键菜单（可选）：重命名/置顶/归档/删除/导出
- [ ] 2.7 实现会话搜索框（SearchInput from F7）

### 3. 置顶空间 (`PinnedSpaces`)

- [ ] 3.1 渲染置顶空间列表（如"产品运营"/"项目开发"）
- [ ] 3.2 每项显示：文件夹图标 + 名称 + 拖拽排序图标
- [ ] 3.3 支持展开/折叠（点击切换）
- [ ] 3.4 「新建对话」按钮：全宽 + bg-primary + text-white + icon

### 4. 聊天主区域 (`ChatArea`)

- [ ] 4.1 使用 react-virtuoso 实现虚拟滚动消息列表
- [ ] 4.2 首次加载最近 50 条消息（cursor-based 分页）
- [ ] 4.3 向上滚动到顶部时自动加载更早的消息（`endReached` 回调）
- [ ] 4.4 加载中显示 spinner，加载完成显示"—— 以上是全部消息 ——"
- [ ] 4.5 滚动到底部（新消息或发送时自动滚动）
- [ ] 4.6 用户手动向上滚动时不自动跳底（"回到底部"浮动按钮）

### 5. 消息气泡 (`MessageBubble`)

- [ ] 5.1 根据 role 区分气泡样式：
  - 用户消息：居右，bg-blue-500 text-white，rounded-xl
  - 数字主管：居左，bg-gray-100 + 主管色边框（border-l-2 border-blue-500）+ 🎯 头像
  - Worker Agent：居左，bg-gray-50 + 各自色边框 + Emoji 头像
- [ ] 5.2 每个 Agent 消息气泡显示：Emoji 头像 + Agent 名称 + 时间戳
- [ ] 5.3 渲染富内容块：
  - Markdown 文本（react-markdown + remark-gfm + rehype-highlight）
  - 代码块（CodeBlock from F6）
  - 进度条（ProgressBar from F6）
  - 任务计划卡片（TaskPlanCard）
  - 操作按钮组（ActionButtons）
  - 数据表格（TableRenderer）
- [ ] 5.4 流式渲染：WebSocket `text_delta` → 逐 Token 追加到消息 content，实时 Markdown 解析
- [ ] 5.5 流式过程中 Agent 头像旁显示"输入中..."动画（三个点跳动）

### 6. 任务计划卡片 (`TaskPlanCard`)

- [ ] 6.1 接收 WebSocket `task_plan` → 渲染执行计划卡片
- [ ] 6.2 卡片标题："📋 执行计划"
- [ ] 6.3 步骤列表：序号 + 描述 + 分配的 Agent（Emoji+名称）+ 依赖标记 + 状态图标
- [ ] 6.4 状态图标：⏳待执行 / 🔄执行中 / ✅完成 / ❌失败 / ⏸️待确认
- [ ] 6.5 并行步骤用 `[并行]` 标签标记，依赖关系用缩进或连线表示
- [ ] 6.6 确认步骤展示确认卡片：操作描述 + "✅确认执行" + "❌跳过" 按钮
- [ ] 6.7 用户可手动调整步骤（修改/更换Worker/取消）

### 7. 操作按钮组 (`ActionButtons`)

- [ ] 7.1 接收 WebSocket `action_result` → 渲染操作按钮组
- [ ] 7.2 按钮样式支持：primary（bg-primary text-white）/ outline（border border-gray-300）
- [ ] 7.3 按钮点击 → 发送对应 action 到后端

### 8. 变量表查看器 (`VariableTableView`)

- [ ] 8.1 以折叠面板或抽屉形式展示变量表
- [ ] 8.2 表格显示：变量名 / 类型图标 / 值摘要 / 创建者 / 创建步骤
- [ ] 8.3 类型图标：str(🔤), int/float(🔢), DataFrame(📊), image(🖼️), path(📁)
- [ ] 8.4 DataFrame 类型：点击展开表格预览（显示行列数）
- [ ] 8.5 WebSocket `variable_update` 推送时高亮闪烁更新

### 9. 消息编辑 (`MessageEditor`)

- [ ] 9.1 用户可编辑自己已发送的消息
- [ ] 9.2 编辑后标记 is_edited，显示"(已编辑)"标签
- [ ] 9.3 编辑后触发 Agent 重新生成回复

### 10. 重新生成

- [ ] 10.1 Agent 消息气泡旁显示"重新生成"按钮
- [ ] 10.2 点击 → API 调用 → 新回复替换旧回复

### 11. 输入区 (`InputArea`)

- [ ] 11.1 顶部工具栏：📎附件 + 🖼️图片 + 🎤麦克风 + Wi-Fi + 终端 图标按钮
- [ ] 11.2 输入框：多行 textarea，自动增高（max-h-40）
- [ ] 11.3 右侧发送按钮（ArrowRight 图标）
- [ ] 11.4 快捷键：Ctrl+Enter 发送，Enter 换行
- [ ] 11.5 模型切换按钮（紧凑下拉，与 TitleBar 联动 Redux modelSlice.currentModelId）

### 12. 富交互输入 (`MentionInput`)

- [ ] 12.1 `@Agent名称` 提及：输入 `@` → 弹出 Agent 选择下拉（Emoji + 名称 + 角色简述）
- [ ] 12.2 `#文件名` 引用：输入 `#` → 弹出资产文件选择下拉（图标 + 文件名 + 类型）
- [ ] 12.3 `/命令` 快捷操作：输入 `/` → 弹出命令提示下拉（/clear, /export, /stop, /help）
- [ ] 12.4 选中后插入对应文本到光标位置
- [ ] 12.5 后端解析 mentions + file_refs + command 而非依赖文本匹配

### 13. 附件上传

- [ ] 13.1 点击📎 → 弹出系统文件选择对话框
- [ ] 13.2 选择文件 → 显示上传进度条
- [ ] 13.3 上传完成 → 文件出现在资产列表，输入框自动插入 `#文件名`
- [ ] 13.4 文件 > 50MB → Toast 错误提示

### 14. 会话操作（导出/重命名/归档等）

- [ ] 14.1 会话列表右键菜单或"..."菜单
- [ ] 14.2 重命名：内联编辑标题
- [ ] 14.3 置顶/取消置顶
- [ ] 14.4 归档/取消归档
- [ ] 14.5 删除：弹出确认对话框
- [ ] 14.6 导出：打开 ExportDialog（F7）

### 15. WebSocket 集成

- [ ] 15.1 使用 `useWebSocket` hook 连接 `/ws/chat/{conversation_id}`
- [ ] 15.2 接收消息并 dispatch 到 Redux：
  - text_delta → appendToken
  - task_plan → 更新 TaskPlanCard
  - step_status → 更新步骤状态
  - code_progress → 更新 CodeBlock 进度
  - action_result → 渲染操作按钮
  - variable_update → 更新变量表视图
  - agent_status → 更新 Agent 活动列表
  - done → 完成标记 + token 统计
  - error → 错误提示
- [ ] 15.3 发送消息：user_message / confirm_action / control / ping

### 16. 测试

- [ ] 16.1 测试 conversationSlice reducer + thunks
- [ ] 16.2 测试 MessageBubble 渲染（各 role + 各内容类型）
- [ ] 16.3 测试 MentionInput @/#// 下拉触发
- [ ] 16.4 测试 TaskPlanCard 状态变更
