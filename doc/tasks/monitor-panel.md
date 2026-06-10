# F5 — 监控面板 (`monitor_panel`)

> 模块职责：性能/安全 Tab、Agent 活动列表。

---

## 子任务

### 1. Redux Store — monitorSlice

- [ ] 1.1 定义 MonitorState 接口（hardware, containers, agentActivities）
- [ ] 1.2 实现 reducer actions：updateHardware, updateContainers, updateAgentStatus, addAgentActivity
- [ ] 1.3 创建 selectors：selectHardwareStats, selectContainers, selectAgentActivities

### 2. 性能监控 Tab (`PerformanceTab`)

- [ ] 2.1 GPU 监控 (`GpuMonitor`)：
  - GPU 显存：进度条 + 已用/总量 数值 + 百分比
  - GPU 利用率：进度条 + 百分比
- [ ] 2.2 系统内存监控 (`MemoryMonitor`)：进度条 + 已用/总量 + 百分比
- [ ] 2.3 进度条颜色规则：<50% 绿色(bg-green-500) / 50-80% 黄色(bg-yellow-500) / >80% 红色(bg-red-500)
- [ ] 2.4 无 GPU 环境优雅降级：显示灰色「GPU 不可用」状态，不报错
- [ ] 2.5 数据通过 WebSocket `/ws/monitor` 实时推送更新（每 5 秒）
- [ ] 2.6 Docker 容器状态区（可折叠）：运行中容器列表，每项显示容器名 + CPU% + 内存

### 3. 安全 Tab (`SecurityTab`)

- [ ] 3.1 审计日志查看器 (`AuditLogViewer`)：
  - 时间线列表（最近优先）
  - 每条显示：操作类型图标 + 描述 + Agent 名称 + 时间 + 状态标签（success/failed/blocked）
- [ ] 3.2 筛选栏：按时间范围 / Agent / 操作类型筛选
- [ ] 3.3 「导出日志」按钮（触发审计日志导出 API）
- [ ] 3.4 「查看更多」→ 展开筛选面板
- [ ] 3.5 Agent 权限状态：当前活跃 Agent + 权限级别徽章

### 4. Agent 活动列表 (`AgentActivity`)

- [ ] 4.1 实时显示所有 Agent 最近活动
- [ ] 4.2 每个 `AgentActivityItem` 显示：
  - Emoji 头像 + Agent 名称
  - 状态文本（如"正在拆解并生成任务..."）
  - 相对时间（刚刚/1分钟前/2分钟前）
- [ ] 4.3 状态指示颜色：🟢green(idle), 🔵blue(working), 🟡yellow(blocked), 🔴red(error)
- [ ] 4.4 数据通过 WebSocket `/ws/agents` 推送实现实时更新

### 5. WebSocket 集成

- [ ] 5.1 连接 `/ws/monitor` → 接收 `hardware_stats` → dispatch updateHardware + updateContainers
- [ ] 5.2 连接 `/ws/agents` → 接收 `agent_status` → dispatch updateAgentStatus + addAgentActivity

### 6. 测试

- [ ] 6.1 测试 monitorSlice reducer
- [ ] 6.2 测试 PerformanceTab 渲染（含 GPU 降级）
- [ ] 6.3 测试 AgentActivityItem 状态颜色映射
