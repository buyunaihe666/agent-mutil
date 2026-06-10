# F1 — 布局框架 (`layout_shell`)

> 模块职责：三栏容器、标题栏/状态栏、主题切换、全局布局。

---

## 子任务

### 1. 项目骨架搭建

- [ ] 1.1 初始化 Vite + React 18 + TypeScript 项目（`npm create vite@latest`）
- [ ] 1.2 配置 Tailwind CSS 3+（tailwind.config.ts：brand colors, dark mode class strategy）
- [ ] 1.3 配置 shadcn/ui（components.json + 基础主题）
- [ ] 1.4 安装依赖：lucide-react, react-router-dom, @reduxjs/toolkit, react-redux
- [ ] 1.5 配置 Biome 代码规范（biome.json）
- [ ] 1.6 配置 Sentry（sentry.config.ts，ErrorBoundary 集成）
- [ ] 1.7 配置路径别名（tsconfig paths）

### 2. App 根组件

- [ ] 2.1 创建 `App.tsx`：包裹 ThemeProvider + Redux Provider + ErrorBoundary + BrowserRouter
- [ ] 2.2 创建 `main.tsx`：ReactDOM.createRoot 渲染 App
- [ ] 2.3 配置 React Router 路由表（routes/index.tsx，含所有页面路由）

### 3. 三栏布局容器 (`MainLayout`)

- [ ] 3.1 创建 `MainLayout.tsx`：flex 容器，包含 TitleBar + 三栏 flex-1 + StatusBar
- [ ] 3.2 实现三栏宽度：左栏 w-[24%]（min-w-[240px]）+ 中间 flex-1 + 右栏 w-[16%]（min-w-[200px]）
- [ ] 3.3 各栏独立滚动（overflow-y-auto）
- [ ] 3.4 响应式处理：小屏隐藏右侧栏，更小屏隐藏左侧栏（汉堡菜单）
- [ ] 3.5 创建通用 `PageLayout.tsx`（Agent编辑/列表等非聊天页面：仅标题栏+状态栏，无三栏）

### 4. 顶部标题栏 (`TitleBar`)

- [ ] 4.1 左侧：Logo 图标 + 品牌名（"NEXUS AI"）+ 版本号 + 系统标识
- [ ] 4.2 中间：ModelSelector 下拉（模型切换，与输入区联动）
- [ ] 4.3 右侧：窗口控制按钮（MinimizeSquare / Maximize2 / X 图标）
- [ ] 4.4 样式：h-10, bg-primary text-white, flex items-center px-3

### 5. 底部状态栏 (`StatusBar`)

- [ ] 5.1 左侧：API 连接状态指示（图标 + 模型名称 + 状态文字："已配置"/"未配置"/"连接异常"）
- [ ] 5.2 左侧：Token 用量显示（"Token: 12.5K"）
- [ ] 5.3 右侧：「导出日志」按钮（点击跳转审计日志导出）
- [ ] 5.4 右侧：PING 延迟显示（"PING XXms"）
- [ ] 5.5 样式：h-9, border-t, flex items-center px-4, text-sm, bg-gray-50

### 6. 主题切换 (`ThemeToggle`)

- [ ] 6.1 使用 Redux `uiSlice.theme` 管理主题状态（'light' | 'dark'）
- [ ] 6.2 Tailwind CSS `dark:` class 策略：在 `<html>` 上 toggle `dark` class
- [ ] 6.3 主题状态持久化到 localStorage
- [ ] 6.4 切换按钮位于状态栏或设置中

### 7. 左侧栏容器 (`Sidebar`)

- [ ] 7.1 Tab 切换：「会话」|「资产」
- [ ] 7.2 Tab 状态由 Redux `uiSlice.sidebarTab` 管理
- [ ] 7.3 会话 Tab 内容：ConversationList（F2）+ PinnedSpaces（F2）
- [ ] 7.4 资产 Tab 内容：AssetPanel（F4）

### 8. 右侧面板容器 (`RightPanel`)

- [ ] 8.1 Tab 切换：「性能」|「安全」
- [ ] 8.2 Tab 状态由 Redux `uiSlice.rightPanelTab` 管理
- [ ] 8.3 性能 Tab 内容：PerformanceTab（F5）
- [ ] 8.4 安全 Tab 内容：SecurityTab（F5）+ AgentActivity（F5）

### 9. 全局 Error Boundary

- [ ] 9.1 创建 React Error Boundary 组件
- [ ] 9.2 捕获渲染错误，显示友好的错误页面 + 重试按钮
- [ ] 9.3 集成 Sentry 异常上报（captureException）

### 10. 测试

- [ ] 10.1 测试 MainLayout 渲染
- [ ] 10.2 测试主题切换
- [ ] 10.3 测试侧栏 Tab 切换
