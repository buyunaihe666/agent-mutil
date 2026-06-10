# F6 — 代码展示 (`code_display`)

> 模块职责：Shiki 代码块、编辑面板、进度条。

---

## 子任务

### 1. Shiki 语法高亮

- [ ] 1.1 配置 Shiki（初始化 highlighter，选择主题：深色/浅色双主题）
- [ ] 1.2 实现 `highlightCode(code: string, lang: string) → HTML` 工具函数
- [ ] 1.3 支持常见语言：python, sql, javascript, typescript, json, bash, yaml, markdown
- [ ] 1.4 异步加载语言包（Shiki 按需加载）

### 2. 代码块组件 (`CodeBlock`)

- [ ] 2.1 渲染代码块：语言标签（左上角，如 "python"）+ Shiki 高亮代码
- [ ] 2.2 深色代码背景（bg-gray-900 text-gray-100）+ 圆角 + 等宽字体
- [ ] 2.3 四个操作按钮（右上角）：
  - **复制** (CopyButton)：📋 或 Copy 图标 → 复制到剪贴板 → Toast "已复制"
  - **运行** (RunButton)：▶️ 图标 → 发送到沙箱执行 → 显示 ProgressBar + 结果显示在代码块下方
  - **编辑** (EditButton)：✏️ 图标 → 展开 CodeEditorPanel
  - **下载** (DownloadButton)：⬇️ 图标 → 下载为 .py 文件（Blob + URL.createObjectURL）

### 3. 复制按钮 (`CopyButton`)

- [ ] 3.1 使用 `navigator.clipboard.writeText()` 复制代码
- [ ] 3.2 复制成功后图标变为 ✓（2 秒后恢复）
- [ ] 3.3 Toast 通知 "已复制"

### 4. 运行按钮 (`RunButton`)

- [ ] 4.1 点击 → 发送代码到后端代码执行 API（通过 Tool Registry 的 code_exec 工具）
- [ ] 4.2 执行过程中显示 ProgressBar（进度条）
- [ ] 4.3 执行完成后在代码块下方展示 stdout/stderr
- [ ] 4.4 执行失败显示错误信息（红色文字）

### 5. 编辑按钮 + 代码编辑面板 (`CodeEditorPanel`)

- [ ] 5.1 点击编辑 → 以侧边面板或底部面板形式展开代码编辑器
- [ ] 5.2 编辑区：等宽字体 textarea（或简易 code editor），语法高亮（可选）
- [ ] 5.3 顶部显示：文件名 + 语言标签
- [ ] 5.4 底部按钮：▶️执行（重新运行修改后的代码）、💾保存到资产库、❌关闭面板
- [ ] 5.5 执行后结果显示在面板下方
- [ ] 5.6 关闭面板回到聊天区视图

### 6. 进度条 (`ProgressBar`)

- [ ] 6.1 显示执行进度（0-100%）
- [ ] 6.2 颜色：进行中蓝色 / 完成绿色 / 失败红色
- [ ] 6.3 动画：smooth transition
- [ ] 6.4 配合文字：如 "部署监控代码(100%)"
- [ ] 6.5 可折叠/展开（点击进度条显示/隐藏详情）

### 7. 代码块 Markdown 集成

- [ ] 7.1 在 react-markdown 的 code 组件中替换为 CodeBlock
- [ ] 7.2 处理 ```language 标记 → 传递给 Shiki 进行高亮
- [ ] 7.3 流式渲染时，代码块在 ```闭合后再触发 Shiki 高亮（避免频繁重建）

### 8. 测试

- [ ] 8.1 测试 Shiki 高亮输出
- [ ] 8.2 测试复制功能
- [ ] 8.3 测试代码编辑面板打开/关闭
- [ ] 8.4 测试 ProgressBar 状态切换
