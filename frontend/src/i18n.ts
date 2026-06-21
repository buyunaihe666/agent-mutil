/**
 * i18n placeholder - all user-facing strings go through this function.
 * First version is Chinese only. The function exists to enable
 * future internationalization without rewriting components.
 */
export function t(key: string, fallback?: string): string {
  const translations: Record<string, string> = {
    // App shell
    "app.title": "NEXUS AI",
    "app.subtitle": "多Agent协作平台",

    // Prototype shell
    "shell.product": "DeepSeek",
    "shell.version": "V6.2.0",
    "shell.workspace": "NEXUS AI",
    "shell.newConversation": "新建对话",
    "shell.pinnedSpace": "置顶空间",
    "shell.activeConversations": "活跃会话",
    "shell.performance": "性能",
    "shell.security": "安全",
    "shell.agent": "Agent",
    "shell.hardwareMonitor": "硬件监控",
    "shell.recentActivity": "近期活动",
    "shell.gpuMemory": "GPU显存",
    "shell.systemMemory": "系统内存",
    "shell.statusApi": "DeepSeek API | API Key已配置",
    "shell.exportLogs": "导出日志",
    "shell.ping": "PING 15ms",
    "shell.inputPlaceholder": "输入您的问题...",
    "shell.viewBackup": "查看备份",
    "shell.mergeData": "合并数据",
    "shell.saveTemplate": "存为模板",
    "shell.taskComplete": "任务执行完毕。监控代码已部署。财务数据已更新并备份，请确认。",
    "shell.deployMonitorCode": "部署监控代码(100%)",
    "shell.codeFilename": "spider_probe_server.py",
    "shell.productOps": "产品运营",
    "shell.projectDev": "项目开发",
    "shell.competitorAnalysis": "竞品销量异动分析",
    "shell.financeProcessing": "年度财报数据处理",
    "shell.preferenceAlignment": "用户偏好特征对齐",
    "shell.assetSalesReport": "sales_report.csv",
    "shell.prototypeAdvice": "建议：建议主攻 899元以上“长续航+骨传导”细分市场，避开低价竞争。",
    "shell.agentSupervisor": "数字主管",
    "shell.agentRiskAdvisor": "风控顾问",
    "shell.agentDataExpert": "数据专家",
    "shell.agentActivity": "近期活动",
    "shell.rateLimits": "速率限制",
    "shell.recentAuditEvents": "近期审计事件",
    "shell.apiRequests": "API请求",
    "monitor.llmRequests": "LLM请求",
    "monitor.activity.coordinatingAgents": "正在协调多Agent任务分配",
    "monitor.activity.waitingRiskAssessment": "等待风险评估任务",
    "monitor.activity.dataAnalysisReady": "数据分析模块就绪",
    "monitor.audit.executeCode": "12:30 - 执行代码（数字主管）",
    "monitor.audit.createConversation": "12:28 - 创建会话（user-1）",
    "monitor.audit.uploadFile": "12:25 - 上传文件（user-1）",
    "monitor.audit.createAgent": "12:20 - 创建Agent（admin）",
    "monitor.audit.archiveConversation": "12:15 - 归档会话（user-1）",

    // Navigation
    "nav.conversations": "会话",
    "nav.assets": "资产",
    "nav.agents": "Agent管理",
    "nav.monitor": "监控",

    // Agents
    "agent.tab.agents": "Agent",
    "agent.tab.templates": "模板",

    // Assets
    "asset.type": "类型",
    "asset.size": "大小",
    "asset.mime": "MIME",

    // Actions
    "action.send": "发送",
    "action.cancel": "取消",
    "action.confirm": "确认",
    "action.delete": "删除",
    "action.edit": "编辑",
    "action.save": "保存",
    "action.copy": "复制",
    "action.export": "导出",
    "action.run": "运行",
    "action.download": "下载",

    // Status
    "status.loading": "加载中...",
    "status.error": "出错了",
    "status.empty": "暂无数据",
    "status.connected": "已连接",
    "status.disconnected": "已断开",

    // Theme
    "theme.light": "浅色模式",
    "theme.dark": "深色模式",

    // Model
    "model.select": "选择模型",
    "model.default": "默认模型",

    // Common
    "common.search": "搜索...",
    "common.filter": "筛选",
    "common.more": "更多",

    // Voice input
    "voice.notSupported": "浏览器不支持语音识别",
    "voice.recording": "录音中...",
    "voice.tapToStop": "点击停止录音",
    "voice.timeout": "录音超时 (60秒)",
    "voice.noSpeech": "未检测到语音",
    "voice.permissionDenied": "麦克风权限被拒绝",
    "voice.networkError": "网络错误",

    // Meta-Agent layers
    "metaAgent.decision": "智能决策",
    "metaAgent.strategy": "策略规划",
    "metaAgent.execution": "执行调度",
    "metaAgent.layerDecision": "决策层",
    "metaAgent.layerStrategy": "策略层",
    "metaAgent.layerExecution": "执行层",
    "metaAgent.layerReview": "审查",
    "metaAgent.analyzing": "正在分析意图...",
    "metaAgent.planning": "正在制定计划...",
    "metaAgent.dispatching": "正在分配任务...",
  };

  return translations[key] ?? fallback ?? key;
}
