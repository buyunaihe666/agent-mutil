# NEXUS AI — 多Agent协作平台 需求文档

> 版本：v2.0 | 日期：2026-06-09 | 状态：已确认

---

## 1. 项目概述

### 1.1 项目背景

企业内部日常运营涉及大量跨领域协作任务——从数据分析、竞品监控、财报处理到代码部署、安全审计。传统方式依赖人工在不同工具间切换，效率低下且容易遗漏关键信息。

NEXUS AI 旨在打造一个**企业内部多Agent AI协作平台**，通过多个AI Agent各司其职、协作完成任务，将复杂工作流自动化。用户只需用自然语言描述任务，平台自动完成拆解、分配、执行、汇总。

### 1.2 项目目标

- 构建一个支持**多模型切换**的AI对话平台（DeepSeek / OpenAI / Claude 等）
- 实现**多Agent协作**能力：主管Agent拆解任务，Worker Agent执行子任务，自动汇总结果
- 提供**代码执行沙箱**，让Agent能安全地运行Python代码
- 集成**知识库（RAG）**和**文件资产管理**
- 建立完整的**安全审计体系**：权限控制、操作日志、代码审查、数据脱敏
- 提供**真实系统监控**：GPU/内存/Docker资源使用情况
- 通过 **Docker Compose** 实现一键部署

### 1.3 项目范围

**第一版（MVP）——一次性交付全部功能**，包含本文档描述的所有模块。

### 1.4 术语定义

| 术语 | 说明 |
|------|------|
| **Agent** | 具有特定角色和能力的AI智能体，拥有独立的System Prompt和工具集 |
| **主管Agent (Orchestrator)** | 负责任务拆解、分配Worker、汇总结果的协调者 |
| **Worker Agent** | 执行具体子任务的专业Agent（如数据专家、风控顾问） |
| **会话 (Conversation)** | 用户与Agent系统之间的对话线程 |
| **资产 (Asset)** | 用户上传的文件（CSV/Excel/图片等）和知识库文档 |
| **知识库 (Knowledge Base)** | 经过向量化的文档集合，Agent可进行RAG检索 |
| **沙箱 (Sandbox)** | Docker容器隔离环境，用于安全执行Agent生成的代码 |
| **模型提供商** | LLM API服务商，如DeepSeek、OpenAI、Anthropic |
| **变量表 (Variable Table)** | 跨Agent步骤共享的键值存储，Agent可读写中间结果 |

---

## 2. 功能需求

### 2.1 多模型管理

#### 2.1.1 模型配置

- 系统预设支持多种LLM提供商：DeepSeek、OpenAI、Anthropic Claude 等
- 管理员可在后端配置每个提供商的 API Key、Base URL、模型列表
- **前端模型切换位置**：顶部标题栏下拉菜单 + 输入框旁快捷切换按钮，两处都可操作
- 每个Agent可指定默认使用的模型，也可在运行时由用户覆盖
- **模型切换即时生效**：切换后下一轮对话使用新模型，不影响当前进行中的任务

#### 2.1.2 API Key管理

- API Key 在后端统一管理，使用 **AES-256加密存储**，前端不暴露原始密钥
- 支持多个API Key轮换，达到速率限制时自动切换
- API Key状态监控：余额、调用次数、速率限制预警
- 底部状态栏显示当前API连接状态（参考原型 `DeepSeek API | API Key已配置`）

#### 2.1.3 LLM 调用超时

- 采用 **模型级超时 + Agent级超时** 组合策略：
  - **模型级超时**（可配置）：DeepSeek 120s / OpenAI 120s / Claude 180s（默认值）
  - **Agent级超时**（可配置）：每个Agent可设置独立超时，默认5分钟
  - 以先到达者为准

### 2.2 Agent系统

#### 2.2.1 系统预设Agent

系统出厂自带以下Agent，不可删除但可修改配置：

| Agent名称 | 角色 | Persona风格 | 默认权限 | 默认能力 |
|-----------|------|-------------|----------|----------|
| **数字主管** | 任务拆解与分配 | 正式、策略性、全局视角 | Level 4 | 接收用户任务→分析复杂度→拆解为子任务→分配给对应Worker→汇总结果 |
| **风控顾问** | 安全审计 | 谨慎、严谨、合规导向 | Level 3 | 监控系统操作→检测未授权访问→审计代码执行→数据合规检查 |
| **数据专家** | 数据处理与分析 | 技术化、精确、数据导向 | Level 2 | SQL查询→数据清洗→统计分析→图表生成→知识库检索 |

**Agent Persona**：每个Agent有独立的语气和表达风格，通过System Prompt定义，用户可修改。

#### 2.2.2 自定义Agent

- 用户可创建、编辑、启用/禁用、删除自定义Agent
- **Agent模板库**：提供预设模板（市场分析/代码审查/文档撰写/数据分析等），用户可一键基于模板创建Agent
- 每个Agent配置项：
  - **名称**：Agent的显示名称
  - **头像**：Emoji头像（预设Agent各分配一个emoji，自定义Agent可从emoji面板选择）
  - **System Prompt**：定义Agent的角色、行为准则、输出格式、Persona风格
  - **工具集**：勾选该Agent可使用的工具（见2.4节）
  - **默认模型**：该Agent首选使用的LLM模型
  - **权限级别**：该Agent的操作权限等级（1-4）
  - **温度参数**：控制Agent输出的随机性
  - **最大Token数**：单次响应的Token上限
  - **超时时间**：Agent执行任务的最长时限
- Agent配置存储在PostgreSQL中
- **完整版本管理**：每次修改System Prompt或配置自动存档，支持浏览/对比/回滚任意历史版本

#### 2.2.3 Agent记忆与上下文

##### 会话级记忆
- Agent在同一个会话（Conversation）中记住所有历史消息

##### 上下文窗口管理（混合策略）
- **近期消息**：完整保留最近N条消息（滑动窗口）
- **远期消息**：超出窗口的消息由LLM自动生成压缩摘要，保留关键信息
- 摘要与近期消息合并注入LLM上下文
- 会话结束时，可选择将关键信息存入知识库（需用户确认）

##### 上下文隔离策略
- **主管全量 + Worker隔离**：数字主管可看到完整会话历史，Worker Agent只看到分配给自己的子任务上下文
- 这样既保证主管有全局视野，又避免Worker之间的信息干扰

#### 2.2.4 Agent发现与选择

- 前端Agent列表支持**搜索 + 分类筛选**（按角色/权限/工具/活跃状态）
- 支持按使用频率/最近使用排序
- Agent卡片展示：头像、名称、角色描述、启用工具图标、状态

### 2.3 Agent协作机制

#### 2.3.1 协作品类：主管-工人模式

```
用户输入任务
    │
    ▼
┌─────────────────┐
│   数字主管       │  ← 分析任务，拆解为子任务列表
│  (Orchestrator) │  ← 查看完整会话上下文
└───────┬─────────┘
        │ 分配子任务（智能判断并行/串行）
   ┌────┼────┬────┐
   ▼    ▼    ▼    ▼
┌────┐┌────┐┌────┐┌────┐
│数据││风控││代码││自定│  ← Worker Agents
│专家││顾问││执行││义..│  ← 仅看自己的子任务上下文
└──┬─┘└──┬─┘└──┬─┘└──┬─┘
   │     │     │     │
   └─────┴──┬──┴─────┘
            ▼
    ┌─────────────┐
    │  数字主管    │  ← 汇总结果，生成最终回复
    │  汇总结果    │
    └─────────────┘
```

#### 2.3.2 子任务执行策略

- **智能判断并行/串行**：根据子任务间的依赖关系自动判断
  - 无依赖的子任务：**并行执行**，启动多个Worker同时处理
  - 有依赖的子任务（子任务B需要子任务A的输出）：**串行执行**
  - 依赖关系由主管Agent在拆解时标注
- **并发控制**：**按会话限制**，每个会话最多3个并行Agent（可配置）
- **消息队列优先级**：数字主管（Orchestrator）最高优先级 > 其他Agent平等FIFO

#### 2.3.3 人工介入机制

- 主管Agent拆解任务后，生成**执行计划**展示给用户
- 执行计划包含：子任务列表、分配的Worker、预计步骤、依赖关系
- **全自动模式**：主管直接按计划执行，无需确认（默认）
- **确认模式**：关键步骤（代码执行、数据库写入、外部API调用）需要用户点击确认后才执行
- 用户可在计划展示阶段**手动调整**：修改子任务、更换Worker、取消某步骤
- 执行过程中，用户可随时**暂停/终止**任务链

#### 2.3.4 跨步骤变量传递

- **完整变量表系统**：类似Jupyter Notebook的变量机制
- Agent步骤可读写共享变量表（key-value）
- 典型使用场景：数据专家查询结果存入变量表 → 代码执行Agent读取变量做分析 → 主管汇总时引用变量
- 变量表在会话生命周期内持久化，会话结束清理

#### 2.3.5 任务断点恢复

- **完整持久化**：任务状态实时写入数据库
- 用户关闭浏览器后，后端继续执行任务
- 重新打开后可继续查看执行进度和结果
- 支持**暂停/恢复/取消**操作

#### 2.3.6 Agent间通信

- Agent之间可直接发送消息、委派子任务、传递数据结果
- 通信遵循预定义的消息格式（JSON结构）
- 所有Agent间通信记录在审计日志中
- 通信类型：
  - **委派任务**：Agent A将子任务分配给Agent B
  - **请求数据**：Agent A向Agent B请求数据
  - **通知**：Agent向其他Agent广播状态变更
  - **汇总请求**：主管Agent向所有Worker请求执行结果

### 2.4 Agent工具集

**工具注册与注入机制**：工具通过 Python 类注册，在Agent创建时勾选启用，后端动态注入 function calling 的 tool definitions 到LLM请求中。运行时Agent也可通过对话主动请求启用新工具（需用户确认）。

每个Agent可选择性地启用以下工具：

#### 2.4.1 代码执行（Python）

- **容器生命周期**：每次代码执行创建**独立临时容器**，执行完立即销毁
- **操作方式**：**docker-py**（官方Python Docker SDK）
- **沙箱镜像**：自建Docker镜像，预装核心5库：
  - `numpy`, `pandas`, `matplotlib`, `requests`, `beautifulsoup4`
  - 其他库Agent可显式声明后动态 `pip install`
- **安全限制**：
  - **网络策略**：允许出站网络访问，禁止访问内网（localhost/内网IP段）
  - 内存限制：512MB（默认，可调整）
  - CPU限制：1核
  - 执行超时：60秒
  - 禁止系统调用（seccomp profile）
- **代码预审**（AST静态分析）：
  - 使用Python `ast` 模块解析代码AST
  - 检测危险节点：`os.system`, `subprocess.*`, `eval`, `exec`, `importlib`, `compile`, `__import__`, `open('/etc/..')` 等
  - 危险操作标记为「需用户确认」方可执行
  - 安全代码直接执行
- **文件系统**：只读挂载用户上传的文件，可写临时目录，执行后自动清理
- **输入/输出**：
  - 输入：代码文本 + 可选的数据文件路径 + 可选的变量表键引用
  - 输出：stdout/stderr + 生成的文件（图表PNG等）+ 写入变量表的数据
- **前端展示**：代码块（Shiki语法高亮） + 语言标签 + **复制/运行/编辑/下载**四个按钮 + 执行进度条（参考原型）
- **代码编辑**：聊天区展示代码+结果，可**展开到独立代码编辑面板**进行编辑和重新执行

#### 2.4.2 数据库查询

- Agent 可自主编写 SQL 查询PostgreSQL数据库
- **安全限制**：
  - 只读查询（SELECT）默认允许
  - 写操作（INSERT/UPDATE/DELETE/DDL）需用户确认
  - 禁止操作系统表（pg_catalog等）
  - 查询结果行数限制：1000行
  - 查询超时：30秒
- 前端展示查询结果：表格形式 + 导出CSV按钮

#### 2.4.3 文件操作

- **读文件**：Agent可读取用户上传到资产库的文件
- **写文件**：Agent可生成文件（报告、代码、图表），存入用户资产库
- **文件类型**：CSV, Excel (.xlsx), JSON, TXT, PNG, PDF
- **路径限制**：仅限用户专属的资产目录，不可访问系统文件

#### 2.4.4 网络搜索

- Agent可以通过搜索引擎获取互联网信息
- **搜索引擎方案**：对接阿里巴巴云 IQS MCP Server（已配置endpoint）
- 搜索结果经过过滤和摘要，传递给Agent
- 搜索结果缓存，避免重复调用

#### 2.4.5 外部API调用

- Agent可通过配置的Webhook/API端点与企业系统集成
- 预设集成：Slack通知、邮件发送、Jira工单、企业微信
- **安全限制**：
  - 所有外部API调用需预先配置白名单
  - 调用参数和响应记录在审计日志中
  - 支持OAuth2/API Key认证

#### 2.4.6 Agent间通信（见2.3.6节）

### 2.5 资产管理

#### 2.5.1 文件资产

- **上传**：用户通过输入框的附件按钮（📎）上传文件
- **支持格式**：CSV, Excel (.xlsx/.xls), JSON, TXT, PNG, JPG, PDF, Word (.docx)
- **文件大小限制**：单文件最大50MB
- **存储方案**：**本地文件系统 + S3接口预留**（通过抽象存储层实现，后续可切换MinIO/S3）
- **管理操作**：浏览、搜索、预览、下载、删除
- **文件预览**：支持常见格式在线预览
  - 图片（PNG/JPG）：缩略图预览
  - PDF：内嵌PDF查看器
  - 文本/代码/JSON：代码高亮预览
  - CSV/Excel：表格渲染预览
  - 其他格式：显示文件名+大小+类型图标，点击下载
- **Agent访问**：Agent可通过文件操作工具（2.4.3）读取资产文件

#### 2.5.2 知识库（RAG）

##### 文档上传与管理
- 用户可上传文档到知识库：PDF, Word, Markdown, TXT
- 自动文档解析、分块（Chunking）、向量化（Embedding）
- 支持手动编辑分块内容
- 支持标签分类和搜索
- **第一版仅支持用户上传文档，不集成企业知识库（Confluence/语雀等）**

##### 文档分块策略（混合分块）
- **优先语义分块**：按段落/标题结构切分
- **超长段落再按Token切分**：语义块超过512 token时按固定大小切割
- **10%重叠**：相邻块之间保留10%内容重叠，避免语义断裂

##### Embedding 向量化
- **Embedding模型**：DeepSeek Embedding API（维度通过API实测确认，暂定1536维兼容）
- 向量存储：PostgreSQL pgvector 扩展

##### RAG检索（混合检索，无Rerank）
- **混合检索**：向量相似度（Cosine） + 关键词匹配（BM25/PostgreSQL full-text search）
- **无Rerank**：混合检索结果按分数加权排序后直接返回Top-K
- **引用溯源**：Agent回答中标注信息来源文档和片段

### 2.6 安全体系

#### 2.6.1 权限控制

- **Agent权限分级**：
  - Level 1：只读（只能读取信息和检索）
  - Level 2：分析（可执行查询、代码分析，不可修改数据）
  - Level 3：操作（可写文件、执行代码、调用API）
  - Level 4：管理（可修改系统配置、管理其他Agent）

- 用户可为每个自定义Agent设置权限级别
- 系统预设Agent权限：
  - 数字主管：Level 4
  - 风控顾问：Level 3
  - 数据专家：Level 2

#### 2.6.2 操作审计

- **审计日志记录所有Agent操作**：
  - 操作类型（代码执行、SQL查询、文件读写、API调用、Agent通信）
  - 发起Agent
  - 操作时间
  - 操作参数
  - 执行结果（成功/失败/被拦截）
  - 关联会话ID
- 日志存储在PostgreSQL审计表中
- 日志不可删除（仅追加）
- 支持按时间、Agent、操作类型筛选和导出
- 底部状态栏提供「导出日志」入口（参考原型）

#### 2.6.3 代码执行审查

- **执行前审查**（AST静态分析）：
  - 使用Python `ast` 模块解析代码
  - 检测危险操作：`os.system`, `subprocess`, `eval`, `exec`, `compile`, `__import__`, 文件删除, 网络请求
  - 危险操作标记为「需用户确认」
- **执行后审查**：
  - 记录代码内容和执行输出
  - 分析是否有异常行为
  - 生成审查报告

#### 2.6.4 敏感数据脱敏

- 自动检测输出中的敏感数据模式：
  - 手机号、身份证号、银行卡号
  - API Key、密码、Token
  - 邮箱地址
- 检测到敏感数据时自动脱敏处理（如 `138****1234`）
- 脱敏规则可配置

#### 2.6.5 Prompt注入防护

- **第一版暂不需要**：企业内部使用，信任用户

### 2.7 系统监控

#### 2.7.1 硬件监控

- **GPU监控**：
  - GPU显存使用量/总量
  - GPU利用率百分比
  - 温度（如可获取）
  - **预留支持**：GPU监控模块预留NVIDIA Container Toolkit支持，无GPU环境优雅降级
- **系统内存监控**：
  - 已用/总内存
  - 内存使用率百分比
- **前端展示**：进度条 + 数值显示（参考原型 8.4/16G, 14.2/32G）
- **数据采集**：通过系统API周期性采集（每5秒）
- **WebSocket推送**：实时推送到前端右侧面板

#### 2.7.2 容器监控

- Docker容器资源使用情况
- 运行中容器列表（包括沙箱临时容器）
- 容器CPU/内存/网络IO
- 异常容器告警

### 2.8 会话管理

#### 2.8.1 会话列表

- 左侧边栏展示会话列表
- **置顶空间**：用户可将重要会话/项目文件夹置顶（参考原型「产品运营」、「项目开发」）
- **活跃会话**：按最近活跃时间排序的会话列表
- 每个会话显示：
  - **标题**：创建会话时由LLM根据首条消息自动生成简短标题（如「竞品销量异动分析」），用户可手动重命名
  - 最新状态（如「自动分析已启动...」「分析报告已生成。」）
  - 高亮当前活跃会话
- **会话搜索**：按关键词搜索会话标题
- **会话导出**：支持导出为 **Markdown / PDF / JSON** 格式

#### 2.8.2 会话操作

- **新建会话**：点击「新建对话」按钮创建空白会话
- **重命名**：手动修改会话标题
- **置顶/取消置顶**：管理会话优先级
- **归档**：将不活跃的会话移入归档
- **删除**：删除会话及其所有消息
- **搜索**：按关键词搜索历史会话（标题级别）
- **导出**：将会话导出为 Markdown / PDF / JSON

#### 2.8.3 会话详情

- **消息展示**：聊天气泡风格，按 **头像+名称** 区分不同Agent消息和用户消息
- **消息渲染性能**：使用 **虚拟滚动（react-virtuoso）**，大量消息时只渲染可见区域
- **消息列表加载**：**无限滚动**，向上滚动时自动加载更早的消息（首次加载最近50条）
- **Agent消息**包含富内容：
  - Markdown文本渲染（react-markdown + remark-gfm + rehype-highlight）
  - 代码块（Shiki语法高亮 + 语言标签 + 复制/运行/编辑/下载按钮）
  - 进度条
  - 操作按钮（如「查看备份」「合并数据」「存为模板」）
  - 表格、图表
- **消息流式渲染**：通过WebSocket实时接收Token并渲染
- **Agent状态指示**：右侧面板显示当前正在工作的Agent（如「数字主管 正在拆解并生成任务...」）
- **消息编辑**：用户可编辑已发送的消息，触发Agent重新生成回复
- **重新生成**：支持点击按钮重新生成Agent回复

### 2.9 LLM调用策略

#### 2.9.1 LLM 网关

- **统一网关**：使用 **litellm** 作为多模型调用适配层
- litellm 负责：模型路由、stream流式转发、速率限制、Token计数
- 后端通过 litellm 统一对接 DeepSeek / OpenAI / Anthropic API

#### 2.9.2 独立调用

- 用户直接与特定Agent对话，Agent独立调用LLM API生成回复
- 后端通过 litellm 网关统一管理请求转发和API Key

#### 2.9.3 链式编排调用

- 主管Agent输出（任务拆解）→ 多个Worker Agent输入（子任务）→ 主管Agent输入（汇总）
- 后端编排调用链，管理Agent间的消息传递和上下文隔离
- 支持并行和串行两种子任务执行方式（智能判断，见2.3.2）
- 执行状态实时推送到前端

#### 2.9.4 Token消耗统计

- 后端统计每个会话/Agent/模型维度的Token消耗
- 前端在底部状态栏或设置面板展示Token用量
- 支持按时间段统计分析

### 2.10 前端UI布局

参考原型 `doc/web.html`，采用三栏布局：

```
┌──────────────────────────────────────────────────┐
│  顶部标题栏：Logo | 品牌名 | 版本 | [模型▾] | 窗口控制 │  h-10
├──────────┬───────────────────┬───────────────────┤
│ 左栏24%  │  中间主区域60%     │  右栏16%          │
│          │                   │                   │
│ Tab:     │  消息展示区        │  Tab: 性能|安全   │
│ 会话|资产│  (虚拟滚动)       │                   │
│          │  · AI回复卡片     │  硬件监控          │
│ 新建对话  │  · 代码块         │  GPU: ████░░ 52% │
│          │    [复制][运行]   │  内存: ███░░░ 44% │
│ 置顶空间  │    [编辑][下载]   │                   │
│ ·产品运营│  · 进度条         │  近期活动          │
│ ·项目开发│  · 操作按钮       │  ·数字主管 刚刚    │
│          │                   │  ·风控顾问 1分钟前 │
│ 活跃会话  │                   │  ·数据专家 2分钟前 │
│ ·竞品分析│                   │                   │
│ ·财报数据│  输入区            │                   │
│ ·用户偏好│  [模型▾]          │                   │
│          │  [@Agent][#文件]  │                   │
│          │  [附件][图片][终端]│                   │
│          │  [输入框]  [发送] │                   │
├──────────┴───────────────────┴───────────────────┤
│  底部状态栏：API状态 | Token用量 | 导出日志 | PING │  h-9
└──────────────────────────────────────────────────┘
```

#### 2.10.1 UI特性

- **深色模式**：支持深色/浅色主题切换（默认浅色，参考原型）
- **桌面通知**：长时间任务完成/Agent状态变更时，通过浏览器 Notification API 弹出桌面通知
- **前端路由**：使用 **React Router**，支持URL直链到特定会话
- **国际化预留**：第一版仅中文，前端预留 i18n 框架

#### 2.10.2 聊天输入区

- **富交互输入**：
  - `@Agent名称` 提及特定Agent
  - `#文件名` 引用资产文件
  - `/命令` 快捷操作（如 /clear, /export, /stop）
- **快捷键**：**Ctrl+Enter 发送**，Enter 换行
- **输入控件**：附件（📎）、图片（🖼️）、麦克风（🎤）、WiFi、终端（参考原型）

#### 2.10.3 代码块操作

- 每个代码块四个操作按钮：**复制 / 运行 / 编辑 / 下载**
- 代码高亮使用 **Shiki**（VS Code同款语法高亮引擎）
- 代码编辑可在聊天区内展开为独立编辑面板

---

## 3. 技术架构

### 3.1 技术栈总览

| 层次 | 技术 | 说明 |
|------|------|------|
| 前端框架 | React 18+ | SPA应用 |
| 构建工具 | Vite | 快速HMR |
| 前端语言 | TypeScript | 类型安全 |
| UI样式 | Tailwind CSS 3+ | 原子化CSS |
| UI组件库 | shadcn/ui | 基于Radix，与Tailwind搭配 |
| 图标库 | Lucide React | 现代化图标（shadcn/ui默认） |
| 前端状态管理 | Redux Toolkit | 复杂应用状态管理 + DevTools |
| 前端路由 | React Router v6+ | URL直链到会话 |
| 前端通信 | 原生 fetch + WebSocket | HTTP API + 实时推送 |
| 代码高亮 | Shiki | VS Code同款引擎 |
| Markdown | react-markdown + remark-gfm + rehype-highlight | 富文本渲染 |
| 虚拟滚动 | react-virtuoso | 大量消息性能保障 |
| 后端框架 | Python 3.12 + FastAPI | 异步高性能Web框架 |
| 后端通信 | FastAPI原生WebSocket + 自定义增强（心跳/重连） | 双协议支持 |
| 包管理 | uv | Python项目管理 |
| ORM | SQLAlchemy 2.0 (async) + asyncpg | 异步ORM + 高性能驱动 |
| 数据库迁移 | 初期 create_all 自动建表 → 稳定后切换 Alembic | 快速迭代 → 正式管理 |
| 数据库 | PostgreSQL 16 | 主数据库 |
| 向量数据库 | pgvector 0.7+ 扩展 | 知识库RAG向量存储 |
| 缓存/消息队列 | Redis 7 | 状态缓存 + arq任务队列 |
| 任务队列 | arq (Async Redis Queue) | 轻量级异步任务，无需额外Worker进程 |
| 容器运行时 | docker-py SDK | 代码执行沙箱操作 |
| LLM SDK | litellm | 统一多模型调用 + stream + 限流 |
| 配置管理 | .env + YAML混合 → pydantic-settings | 开发.env + 生产YAML |
| 代码规范(Python) | Ruff | Linter + Formatter，替代Flake8+isort+Black |
| 代码规范(前端) | Biome | Rust实现，替代ESLint+Prettier |
| 日志系统 | structlog | 结构化日志 |
| 日志输出 | stdout/stderr → Docker日志驱动 | 轮转和保留由Docker管理 |
| 异常追踪 | Sentry（前端） | 前端错误监控 |
| 测试框架(后端) | pytest + pytest-asyncio | 异步测试支持 |
| 测试框架(前端) | Vitest | 与Vite生态一致 |
| 目标覆盖率 | 60-80% | 核心模块全覆盖 |
| 部署 | Docker Compose v2 | 一键部署 |

### 3.2 前端技术细节

| 项目 | 说明 |
|------|------|
| 构建工具 | Vite 5+ |
| HMR | Vite HMR 默认开启 |
| 语言 | TypeScript 5+ |
| 状态管理 | Redux Toolkit (stores: conversation, agent, monitor) |
| 路由 | React Router v6 (/, /conversations/:id, /agents, /assets) |
| HTTP客户端 | 原生 fetch (封装在 services/api.ts) |
| WebSocket客户端 | 原生 WebSocket + 自定义自动重连（指数退避）+ 心跳机制 |
| 错误处理 | React Error Boundary（全局）+ Sentry 异常追踪 |
| 桌面通知 | Notification API |

### 3.3 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                     前端 (React + Vite + TS)              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ 会话面板  │  │ 聊天区域  │  │ 监控面板  │             │
│  └──────────┘  └──────────┘  └──────────┘             │
│        │              │              │                   │
│        └──────────────┼──────────────┘                   │
│                       │ fetch + WebSocket                │
└───────────────────────┼─────────────────────────────────┘
                        │
                  ┌──────┴──────┐
                  │  Nginx (生产) │  ← 反向代理:80 → 前端:3000 + 后端:8000
                  └──────┬──────┘
                         │
┌────────────────────────┼─────────────────────────────────┐
│                  FastAPI 后端 (Python 3.12)               │
│                       │                                   │
│  ┌────────────────────┼────────────────────┐             │
│  │  REST API 路由      │  WebSocket 路由    │             │
│  │  /api/conversations│  /ws/chat          │             │
│  │  /api/agents       │  /ws/monitor       │             │
│  │  /api/assets       │  /ws/agents        │             │
│  │  /api/models       │                    │             │
│  │  /api/health       │                    │             │
│  └────────┬───────────┴────────┬───────────┘             │
│           │                    │                          │
│  ┌────────┴────────────────────┴───────────┐             │
│  │            服务层                        │             │
│  │  ┌──────────┐ ┌──────────┐ ┌─────────┐ │             │
│  │  │Agent服务  │ │会话服务   │ │资产服务  │ │             │
│  │  │·编排引擎 │ │·消息管理 │ │·文件管理 │ │             │
│  │  │·工具调度 │ │·上下文   │ │·RAG引擎 │ │             │
│  │  │·模板管理 │ │·变量表   │ │·分块    │ │             │
│  │  └──────────┘ └──────────┘ └─────────┘ │             │
│  │  ┌──────────┐ ┌──────────┐ ┌─────────┐ │             │
│  │  │安全服务   │ │监控服务   │ │LLM网关  │ │             │
│  │  │·审计日志 │ │·硬件采集 │ │·litellm │ │             │
│  │  │·权限控制 │ │·容器监控 │ │·路由    │ │             │
│  │  │·AST分析 │ │          │ │·限流    │ │             │
│  │  │·脱敏     │ │          │ │·Token   │ │             │
│  │  └──────────┘ └──────────┘ └─────────┘ │             │
│  └────────────────┬────────────────────────┘             │
│                   │                                       │
│  ┌────────────────┼────────────────────────┐             │
│  │         数据 / 基础设施层                 │             │
│  │  PostgreSQL 16  Redis 7  Docker  文件存储│             │
│  │  (+pgvector)    (+arq)   (docker-py)     │             │
│  └─────────────────────────────────────────┘             │
└──────────────────────────────────────────────────────────┘
```

### 3.4 数据流设计

#### 3.4.1 用户对话流程

```
用户输入(富文本: @Agent, #文件, /命令) → WebSocket → FastAPI
    → litellm网关 → 数字主管(LLM调用) → 拆解任务
    → 分发子任务给Worker Agents(arq异步任务队列)
    → 主管优先调度 → 类型判断依赖并行/串行
    → 各Worker通过工具执行(代码沙箱/SQL/文件/搜索/API)
    → 变量表传递中间结果 → 结果汇总
    → 数字主管(LLM调用) → 生成最终回复
    → WebSocket流式推送到前端
    → Redis缓冲流式消息 → 完成后批量写入PostgreSQL
```

#### 3.4.2 RAG检索流程

```
用户问题 → DeepSeek Embedding API → 查询向量
    → pgvector Cosine相似度搜索 → 相关文档片段
    → PostgreSQL full-text search (BM25) → 关键词匹配结果
    → 加权融合排序 → Top-K结果（无Rerank）
    → 注入LLM上下文 → Agent生成回复（标注引用来源）
```

#### 3.4.3 WebSocket 通信架构

```
前端 WebSocket Client
  │
  ├── /ws/chat/{conversation_id}  ← 双向 → 聊天消息流
  │     · 认证：会话ID验证 + JWT预留
  │     · 自动重连：指数退避
  │     · 心跳：30秒ping/pong
  │
  ├── /ws/monitor  ← 服务端推送 → 硬件监控数据 (每5秒)
  │
  └── /ws/agents   ← 服务端推送 → Agent状态变更
```

---

## 4. 系统模块设计

### 4.1 后端模块

```
backend/
├── main.py                 # FastAPI应用入口 + 生命周期管理
├── config.py               # 配置管理（pydantic-settings, .env + YAML）
├── worker.py               # arq Worker入口
├── api/
│   ├── __init__.py
│   ├── conversations.py    # 会话CRUD API
│   ├── agents.py           # Agent管理API（含模板）
│   ├── assets.py           # 资产（文件+知识库）API
│   ├── models.py           # 模型提供商管理API
│   ├── monitor.py          # 系统监控API
│   ├── health.py           # 健康检查API
│   ├── export.py           # 会话导出API (Markdown/PDF/JSON)
│   └── ws.py               # WebSocket路由（chat + monitor + agents）
├── services/
│   ├── agent_service.py    # Agent管理与生命周期
│   ├── agent_template.py   # Agent模板库
│   ├── agent_version.py    # Agent配置版本管理
│   ├── orchestration.py    # 任务编排引擎（依赖分析+并行/串行调度）
│   ├── variable_table.py   # 跨步骤变量表
│   ├── conversation.py     # 会话与消息管理
│   ├── context_manager.py  # 上下文窗口管理（混合策略）
│   ├── asset_service.py    # 文件上传与管理
│   ├── storage.py          # 存储抽象层（本地+S3接口预留）
│   ├── rag_service.py      # 知识库与RAG检索（混合检索，无Rerank）
│   ├── chunker.py          # 文档分块（混合分块策略）
│   ├── embedding.py        # DeepSeek Embedding API调用
│   ├── sandbox.py          # Docker沙箱管理（docker-py）
│   ├── code_analyzer.py    # AST静态代码分析
│   ├── llm_gateway.py      # litellm统一调用网关
│   ├── security.py         # 安全审计与权限
│   ├── sanitizer.py        # 敏感数据脱敏
│   ├── monitor.py          # 系统资源监控（GPU/内存/容器）
│   └── token_tracker.py    # Token消耗统计
├── models/ (SQLAlchemy ORM)
│   ├── __init__.py
│   ├── agent.py            # Agent ORM模型 + 版本表
│   ├── conversation.py     # 会话/消息ORM模型
│   ├── asset.py            # 资产ORM模型
│   ├── knowledge.py        # 知识库文档/分块ORM模型
│   ├── audit.py            # 审计日志ORM模型
│   ├── model_provider.py   # 模型提供商ORM模型
│   ├── variable.py         # 变量表ORM模型
│   └── task.py             # 任务编排状态ORM模型
├── schemas/ (Pydantic)
│   ├── __init__.py
│   ├── agent.py            # Agent Pydantic Schema
│   ├── conversation.py     # 会话Schema
│   ├── message.py          # 消息Schema
│   ├── asset.py            # 资产Schema
│   ├── ws.py               # WebSocket消息Schema
│   └── task.py             # 任务编排Schema
├── tools/
│   ├── __init__.py
│   ├── base.py             # 工具基类（注册+function calling定义生成）
│   ├── registry.py         # 工具注册中心（类注册+动态注入+运行时扩展）
│   ├── code_executor.py    # Python代码执行（docker-py + AST预审）
│   ├── db_query.py         # 数据库查询（SQL安全限制）
│   ├── file_ops.py         # 文件操作（读写资产目录）
│   ├── web_search.py       # 网络搜索（IQS MCP）
│   └── api_caller.py       # 外部API调用
├── middleware/
│   ├── rate_limit.py       # 双层限流（IP + API Key）
│   └── error_handler.py    # 全局异常处理
├── migrations/             # Alembic数据库迁移（稳定后启用）
└── tests/
    ├── conftest.py
    ├── test_agents/
    ├── test_orchestration/
    ├── test_sandbox/
    ├── test_rag/
    └── test_security/
```

### 4.2 前端模块

```
frontend/
├── src/
│   ├── App.tsx              # 应用根组件（ThemeProvider + Router + ErrorBoundary）
│   ├── main.tsx             # 入口文件
│   ├── routes/
│   │   └── index.tsx        # React Router路由配置
│   ├── layouts/
│   │   └── MainLayout.tsx   # 三栏布局容器
│   ├── components/
│   │   ├── TitleBar.tsx     # 顶部标题栏（Logo + 模型切换下拉）
│   │   ├── StatusBar.tsx    # 底部状态栏（API状态 + Token用量 + 导出日志 + PING）
│   │   ├── ThemeToggle.tsx  # 深色/浅色模式切换
│   │   ├── sidebar/
│   │   │   ├── Sidebar.tsx          # 左侧边栏容器
│   │   │   ├── ConversationList.tsx # 会话列表（虚拟滚动）
│   │   │   ├── PinnedSpaces.tsx    # 置顶空间
│   │   │   ├── AssetPanel.tsx      # 资产面板
│   │   │   └── AssetPreview.tsx    # 文件预览（图片/PDF/表格/代码）
│   │   ├── chat/
│   │   │   ├── ChatArea.tsx        # 聊天主区域（react-virtuoso虚拟滚动）
│   │   │   ├── MessageBubble.tsx   # 消息气泡（头像+名称区分Agent）
│   │   │   ├── MessageEditor.tsx   # 消息编辑组件
│   │   │   ├── CodeBlock.tsx       # 代码块（Shiki高亮 + 复制/运行/编辑/下载）
│   │   │   ├── CodeEditorPanel.tsx # 展开式代码编辑面板
│   │   │   ├── ProgressBar.tsx     # 进度条
│   │   │   ├── ActionButtons.tsx   # 操作按钮组（查看备份/合并数据/存为模板）
│   │   │   ├── TaskPlanCard.tsx    # 任务执行计划卡片
│   │   │   ├── VariableTableView.tsx # 变量表查看
│   │   │   └── InputArea.tsx       # 输入区域（富交互: @Agent/#文件//命令 + 模型切换）
│   │   ├── panels/
│   │   │   ├── RightPanel.tsx      # 右侧面板容器
│   │   │   ├── PerformanceTab.tsx  # 性能监控Tab（GPU/内存进度条）
│   │   │   ├── SecurityTab.tsx     # 安全Tab（审计日志/权限状态）
│   │   │   └── AgentActivity.tsx   # Agent活动列表（实时状态）
│   │   ├── agents/
│   │   │   ├── AgentList.tsx       # Agent列表（搜索+筛选）
│   │   │   ├── AgentCard.tsx       # Agent卡片
│   │   │   ├── AgentEditor.tsx     # Agent创建/编辑表单
│   │   │   ├── AgentVersionHistory.tsx # Agent版本历史
│   │   │   └── AgentTemplateGallery.tsx # Agent模板库
│   │   ├── models/
│   │   │   └── ModelSelector.tsx   # 模型选择下拉（顶部+输入区共用）
│   │   ├── export/
│   │   │   └── ExportDialog.tsx    # 会话导出对话框（Markdown/PDF/JSON）
│   │   └── common/
│   │       ├── Modal.tsx
│   │       ├── Dropdown.tsx
│   │       ├── Toast.tsx
│   │       ├── SearchInput.tsx
│   │       └── EmptyState.tsx
│   ├── hooks/
│   │   ├── useWebSocket.ts     # WebSocket连接Hook（自动重连+心跳）
│   │   ├── useConversation.ts
│   │   ├── useAgent.ts
│   │   ├── useMonitor.ts
│   │   ├── useTheme.ts
│   │   ├── useNotification.ts  # 桌面通知Hook
│   │   └── useVirtualScroll.ts
│   ├── stores/ (Redux Toolkit)
│   │   ├── index.ts            # Store配置
│   │   ├── conversationSlice.ts
│   │   ├── agentSlice.ts
│   │   ├── monitorSlice.ts
│   │   ├── uiSlice.ts          # 主题/侧栏状态等
│   │   └── modelSlice.ts       # 当前模型选择
│   ├── services/
│   │   ├── api.ts              # fetch API封装 + 拦截器
│   │   ├── ws.ts               # WebSocket客户端（心跳+重连+指数退避）
│   │   └── notification.ts     # 桌面通知服务
│   ├── types/
│   │   ├── index.ts            # 通用类型
│   │   ├── agent.ts
│   │   ├── conversation.ts
│   │   ├── message.ts
│   │   ├── asset.ts
│   │   └── ws.ts               # WebSocket消息类型
│   ├── i18n/                   # 国际化预留
│   │   ├── index.ts
│   │   └── zh-CN/
│   │       └── common.json
│   └── utils/
│       ├── markdown.ts         # Markdown渲染配置
│       ├── shiki.ts            # Shiki代码高亮配置
│       ├── format.ts           # 日期/大小格式化
│       └── constants.ts
├── biome.json                  # Biome配置
└── sentry.config.ts            # Sentry配置
```

---

## 5. 数据模型设计

### 5.1 核心表结构（完整版）

#### Agent 表

```sql
CREATE TABLE agents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL,
    emoji           VARCHAR(10) NOT NULL DEFAULT '🤖',   -- Emoji头像
    system_prompt   TEXT NOT NULL,
    persona         VARCHAR(50),                          -- Persona风格描述
    tools           JSONB NOT NULL DEFAULT '[]',         -- 启用的工具列表
    permission_level INTEGER NOT NULL DEFAULT 1,         -- 1只读 2分析 3操作 4管理
    default_model   VARCHAR(50) NOT NULL DEFAULT 'deepseek-chat',
    temperature     FLOAT NOT NULL DEFAULT 0.7,
    max_tokens      INTEGER NOT NULL DEFAULT 4096,
    timeout_seconds INTEGER NOT NULL DEFAULT 300,         -- Agent执行超时(秒)
    is_preset       BOOLEAN NOT NULL DEFAULT FALSE,       -- 是否系统预设
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    template_id     UUID,                                 -- 来源模板ID
    template_category VARCHAR(50),                        -- 模板分类
    config_json     JSONB,                                -- 扩展配置
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- Agent配置版本表
CREATE TABLE agent_versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id        UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    version_number  INTEGER NOT NULL,
    system_prompt   TEXT NOT NULL,
    tools           JSONB NOT NULL,
    permission_level INTEGER NOT NULL,
    default_model   VARCHAR(50),
    temperature     FLOAT,
    max_tokens      INTEGER,
    change_summary  VARCHAR(500),                         -- 变更说明
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(agent_id, version_number)
);
```

#### 会话表

```sql
CREATE TABLE conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID,                                 -- 预留多用户扩展
    title           VARCHAR(200) NOT NULL DEFAULT '新对话',
    status          VARCHAR(50) NOT NULL DEFAULT 'active',  -- active/archived
    is_pinned       BOOLEAN NOT NULL DEFAULT FALSE,
    pinned_space    VARCHAR(100),                         -- 置顶空间名称
    agent_id        UUID REFERENCES agents(id),           -- 当前关联Agent
    model_id        VARCHAR(50),                          -- 当前使用模型
    total_tokens    BIGINT NOT NULL DEFAULT 0,            -- 累计Token消耗
    metadata        JSONB,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_conversations_user ON conversations(user_id, updated_at DESC);
CREATE INDEX idx_conversations_pinned ON conversations(is_pinned, updated_at DESC);
```

#### 消息表

```sql
CREATE TABLE messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL,                 -- user / assistant / system / agent
    agent_id        UUID REFERENCES agents(id),           -- 发送消息的Agent
    content         TEXT NOT NULL,                        -- 消息文本（Markdown）
    content_blocks  JSONB,                                -- 富内容块（代码、表格、进度等）
    tool_calls      JSONB,                                -- 工具调用记录
    token_count     INTEGER,                              -- Token消耗统计
    is_edited       BOOLEAN NOT NULL DEFAULT FALSE,       -- 是否被编辑过
    edited_at       TIMESTAMP,                            -- 编辑时间
    parent_message_id UUID REFERENCES messages(id),       -- 关联上级消息（用于任务链/重新生成）
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);
```

#### 任务编排表

```sql
CREATE TABLE task_orchestrations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    orchestrator_id UUID NOT NULL REFERENCES agents(id), -- 主管Agent ID
    status          VARCHAR(20) NOT NULL DEFAULT 'planning', -- planning/executing/paused/completed/failed/cancelled
    plan            JSONB,                                -- 执行计划（子任务列表+依赖关系）
    current_step    INTEGER DEFAULT 0,                    -- 当前执行步骤
    progress        FLOAT DEFAULT 0,                      -- 整体进度 0-100
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE task_steps (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    orchestration_id UUID NOT NULL REFERENCES task_orchestrations(id) ON DELETE CASCADE,
    step_index      INTEGER NOT NULL,
    description     TEXT NOT NULL,
    assigned_agent  UUID REFERENCES agents(id),
    status          VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending/running/confirm_required/completed/failed/skipped
    depends_on      INTEGER[],                            -- 依赖的步骤index数组
    confirm_required BOOLEAN NOT NULL DEFAULT FALSE,
    result          JSONB,                                -- 执行结果
    started_at      TIMESTAMP,
    completed_at    TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);
```

#### 变量表

```sql
CREATE TABLE variable_table (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    var_key         VARCHAR(200) NOT NULL,
    var_value       JSONB NOT NULL,
    var_type        VARCHAR(50),                          -- str/int/float/DataFrame/image/path
    created_by_agent UUID REFERENCES agents(id),
    created_by_step  UUID REFERENCES task_steps(id),
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(conversation_id, var_key)
);
```

#### 资产表

```sql
CREATE TABLE assets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID,                                 -- 预留多用户扩展
    name            VARCHAR(255) NOT NULL,
    type            VARCHAR(20) NOT NULL,                 -- file / knowledge_doc
    file_type       VARCHAR(50),                          -- csv/xlsx/pdf/png/jpg/txt/docx
    file_size       BIGINT,                               -- 字节
    file_path       VARCHAR(500),                         -- 存储路径
    content_text    TEXT,                                 -- 提取的文本内容
    status          VARCHAR(20) NOT NULL DEFAULT 'ready', -- uploading/processing/ready/error
    tags            TEXT[],                               -- 标签数组
    source          VARCHAR(50) NOT NULL DEFAULT 'upload',-- upload（第一版）
    source_url      VARCHAR(500),                         -- 原始来源URL
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
```

#### 知识库文档块表（RAG用）

```sql
CREATE TABLE knowledge_chunks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id        UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    chunk_index     INTEGER NOT NULL,
    content         TEXT NOT NULL,
    embedding       vector(1536),                         -- pgvector扩展，DeepSeek Embedding维度(待API确认)
    token_count     INTEGER,                              -- 块Token数
    metadata        JSONB,                                -- 来源段落/标题等
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chunks_embedding ON knowledge_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_chunks_asset ON knowledge_chunks(asset_id, chunk_index);
```

#### 审计日志表

```sql
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID,                                 -- 预留多用户扩展
    agent_id        UUID REFERENCES agents(id),
    conversation_id UUID REFERENCES conversations(id),
    task_step_id    UUID REFERENCES task_steps(id),
    action_type     VARCHAR(50) NOT NULL,                 -- code_exec / sql_query / file_read / file_write / api_call / agent_comm / config_change
    action_detail   JSONB NOT NULL,                       -- 操作详情
    status          VARCHAR(20) NOT NULL,                 -- success / failed / blocked / confirm_required
    result_summary  TEXT,
    ip_address      VARCHAR(45),
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_agent ON audit_logs(agent_id, created_at);
CREATE INDEX idx_audit_type ON audit_logs(action_type, created_at);
CREATE INDEX idx_audit_conversation ON audit_logs(conversation_id, created_at);
```

#### 模型提供商配置表

```sql
CREATE TABLE model_providers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(50) NOT NULL UNIQUE,          -- deepseek / openai / anthropic
    display_name    VARCHAR(100) NOT NULL,                -- DeepSeek / OpenAI / Anthropic Claude
    api_base_url    VARCHAR(500) NOT NULL,
    api_key_encrypted VARCHAR(500) NOT NULL,             -- AES-256加密存储
    models          JSONB NOT NULL DEFAULT '[]',          -- 可用模型列表 [{id, display_name, max_tokens, cost_per_1k}]
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    rate_limit_rpm  INTEGER,                              -- 每分钟请求限制
    timeout_seconds INTEGER NOT NULL DEFAULT 120,         -- 默认API超时
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
```

---

## 6. API与通信设计

### 6.1 REST API 端点

#### 6.1.1 会话管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/conversations` | 获取会话列表（分页、搜索标题、筛选状态、排序） |
| `POST` | `/api/conversations` | 创建新会话（接收首条消息，自动LLM生成标题） |
| `GET` | `/api/conversations/{id}` | 获取会话详情 |
| `PATCH` | `/api/conversations/{id}` | 更新会话（重命名、置顶、归档、切换模型） |
| `DELETE` | `/api/conversations/{id}` | 删除会话 |
| `GET` | `/api/conversations/{id}/messages` | 获取会话消息列表（无限滚动分页，cursor-based） |
| `PATCH` | `/api/conversations/{id}/messages/{msg_id}` | 编辑消息（用户消息编辑） |
| `POST` | `/api/conversations/{id}/regenerate` | 重新生成Agent回复 |
| `GET` | `/api/conversations/{id}/export?format=md\|pdf\|json` | 导出会话 |

#### 6.1.2 Agent管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/agents` | 获取Agent列表（搜索+筛选+分页） |
| `POST` | `/api/agents` | 创建自定义Agent |
| `GET` | `/api/agents/{id}` | 获取Agent详情（含当前配置） |
| `PATCH` | `/api/agents/{id}` | 更新Agent配置（自动创建新版本） |
| `DELETE` | `/api/agents/{id}` | 删除自定义Agent（预设不可删） |
| `PUT` | `/api/agents/{id}/toggle` | 启用/禁用Agent |
| `GET` | `/api/agents/{id}/versions` | 获取Agent版本历史列表 |
| `GET` | `/api/agents/{id}/versions/{version}` | 获取特定版本配置 |
| `POST` | `/api/agents/{id}/versions/{version}/rollback` | 回滚到指定版本 |
| `GET` | `/api/agents/templates` | 获取Agent模板列表 |
| `POST` | `/api/agents/templates/{template_id}/instantiate` | 基于模板创建Agent |

#### 6.1.3 资产管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/assets` | 获取资产列表（分页+筛选类型+搜索） |
| `POST` | `/api/assets/upload` | 上传文件 |
| `GET` | `/api/assets/{id}` | 获取资产详情/元数据 |
| `GET` | `/api/assets/{id}/download` | 下载原始文件 |
| `GET` | `/api/assets/{id}/preview` | 获取预览数据（图片URL/文本内容/表格数据） |
| `DELETE` | `/api/assets/{id}` | 删除资产 |
| `POST` | `/api/assets/{id}/reprocess` | 重新处理知识库文档（重新分块/向量化） |

#### 6.1.4 模型管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/models` | 获取可用模型列表（所有提供商的模型汇总） |
| `POST` | `/api/models/providers` | 添加模型提供商配置 |
| `PATCH` | `/api/models/providers/{id}` | 更新提供商配置 |

#### 6.1.5 系统

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查（DB连接 + Redis + Docker daemon可达性） |
| `GET` | `/api/monitor/hardware` | 获取硬件资源使用情况 |
| `GET` | `/api/monitor/containers` | 获取Docker容器状态 |
| `GET` | `/api/audit/logs` | 查询审计日志（筛选+分页） |
| `GET` | `/api/audit/logs/export` | 导出审计日志 |
| `GET` | `/api/stats/tokens` | 获取Token消耗统计（按时间/Agent/模型维度） |

#### 6.1.6 任务编排

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/tasks/{conversation_id}` | 获取当前任务编排状态 |
| `POST` | `/api/tasks/{conversation_id}/pause` | 暂停任务 |
| `POST` | `/api/tasks/{conversation_id}/resume` | 恢复任务 |
| `POST` | `/api/tasks/{conversation_id}/cancel` | 取消任务 |
| `GET` | `/api/tasks/{conversation_id}/variables` | 获取变量表 |

### 6.2 WebSocket 端点

| 路径 | 方向 | 认证 | 说明 |
|------|------|------|------|
| `/ws/chat/{conversation_id}` | 双向 | 会话ID验证 + JWT预留 | 聊天消息流 |
| `/ws/monitor` | 服务端→客户端 | JWT预留 | 系统监控数据推送（每5秒） |
| `/ws/agents` | 服务端→客户端 | JWT预留 | Agent状态变更推送 |

#### 6.2.1 聊天WebSocket协议

**客户端→服务端**：
```json
// 用户消息
{
    "type": "user_message",
    "content": "帮我分析竞品销量异常的原因 @数据专家",
    "model": "deepseek-chat",
    "attachments": ["asset_id_1", "asset_id_2"],
    "mentions": ["agent_id_dat_expert"],
    "file_refs": ["#财报数据"],
    "auto_execute": true
}

// 确认操作
{
    "type": "confirm_action",
    "action_id": "action-uuid",
    "step_id": "step-uuid",
    "confirmed": true
}

// 暂停/取消
{
    "type": "control",
    "action": "pause"  // pause | resume | cancel
}

// 心跳
{
    "type": "ping"
}
```

**服务端→客户端**：
```json
// 文本流式推送
{
    "type": "text_delta",
    "agent_id": "agent-uuid",
    "agent_name": "数字主管",
    "agent_emoji": "🎯",
    "delta": "正在分析您的问题...",
    "index": 0
}

// 任务计划
{
    "type": "task_plan",
    "orchestration_id": "orch-uuid",
    "agent_id": "agent-uuid",
    "plan": {
        "steps": [
            {"id": 1, "index": 1, "description": "获取竞品销售数据", "agent": "数据专家", "agent_emoji": "📊", "confirm_required": false, "depends_on": []},
            {"id": 2, "index": 2, "description": "异常检测分析", "agent": "数据专家", "agent_emoji": "📊", "confirm_required": false, "depends_on": [1]},
            {"id": 3, "index": 3, "description": "部署监控代码", "agent": "代码执行器", "agent_emoji": "🐍", "confirm_required": true, "depends_on": [2]}
        ],
        "parallel_groups": [[1], [2], [3]]
    }
}

// 步骤状态变更
{
    "type": "step_status",
    "orchestration_id": "orch-uuid",
    "step_index": 1,
    "status": "running",
    "agent_name": "数据专家",
    "agent_emoji": "📊"
}

// 代码执行进度
{
    "type": "code_progress",
    "agent_id": "agent-uuid",
    "action_id": "action-uuid",
    "filename": "spider_probe_server.py",
    "progress": 100,
    "status": "completed"
}

// 操作结果卡片
{
    "type": "action_result",
    "agent_id": "agent-uuid",
    "status": "success",
    "message": "任务执行完毕。监控代码已部署。",
    "actions": [
        {"label": "查看备份", "action": "view_backup", "style": "outline"},
        {"label": "合并数据", "action": "merge_data", "style": "primary"},
        {"label": "存为模板", "action": "save_template", "style": "outline"}
    ]
}

// 变量表更新
{
    "type": "variable_update",
    "variables": {
        "sales_data": {"type": "DataFrame", "shape": [100, 5], "summary": "竞品销售数据表"},
        "anomaly_threshold": {"type": "float", "value": 0.05}
    }
}

// Agent状态变更
{
    "type": "agent_status",
    "agent_id": "agent-uuid",
    "agent_name": "风控顾问",
    "agent_emoji": "🛡️",
    "status": "working",  // idle / working / blocked / error
    "message": "已拦截一次未授权访问",
    "timestamp": "2026-06-09T10:30:00Z"
}

// 完成
{
    "type": "done",
    "agent_id": "agent-uuid",
    "token_usage": {"prompt": 1500, "completion": 800, "total": 2300}
}

// 错误
{
    "type": "error",
    "code": "EXECUTION_TIMEOUT",
    "message": "代码执行超时（60秒）",
    "agent_id": "agent-uuid",
    "step_index": 3,
    "recoverable": true
}

// 心跳
{
    "type": "pong"
}
```

---

## 7. 安全设计

### 7.1 安全架构总览

```
用户请求 → WebSocket
    │
    ▼
┌──────────────────┐
│  输入过滤层      │  ← SQL注入/XSS过滤
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  限流层          │  ← IP限流 + API Key限流（双层）
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  权限校验层      │  ← Agent权限级别检查
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  AST预审层       │  ← Python代码AST静态分析
│  检测：os.system │
│  subprocess/eval │
│  exec等危险调用   │
└──────┬───────────┘
       │      │
       ▼      ▼ (需确认)
  ┌────────┐ ┌──────────┐
  │ 直接   │ │ 用户确认  │
  │ 执行   │ │ 后执行    │
  └───┬────┘ └─────┬────┘
      │            │
      ▼            ▼
┌──────────────────┐
│  Docker沙箱执行  │  ← 独立临时容器，外网允许，禁止内网
│  (docker-py)     │     资源限制+seccomp+超时强杀
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  输出过滤层      │  ← 敏感数据脱敏
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  审计记录层      │  ← 全操作记录（不可删除，仅追加）
└──────────────────┘
```

### 7.2 数据安全

- API Key 使用 **AES-256** 加密存储
- 敏感配置通过环境变量注入（.env文件不入Git）
- 数据库连接使用SSL/TLS
- 用户文件存储隔离，按会话/用户目录组织
- 定期清理临时文件（Docker容器残留、代码执行临时目录）

### 7.3 Docker沙箱安全

- 自建镜像预装核心5库（numpy/pandas/matplotlib/requests/beautifulsoup4），其他按需pip install
- 使用Python官方镜像的只读层
- 挂载 `seccomp` 安全策略，限制系统调用
- 禁止 `--privileged` 模式
- **网络策略**：允许出站网络（外网），禁止访问内网（localhost/内网IP段）
- 资源限制：CPU 1核 + 内存512MB + 磁盘IO限制
- 执行超时60秒强制 `docker stop` → `docker rm`
- **独立临时容器**：每次代码执行创建新容器，执行完立即销毁

### 7.4 限流策略

- **双层限流**：
  - **IP限流**：FastAPI middleware + Redis滑动窗口（如每分钟60次请求）
  - **API Key限流**：litellm网关控制各模型调用速率（与模型提供商限制对齐）

---

## 8. 部署方案

### 8.1 Docker Compose 编排

```yaml
# docker-compose.yml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: nexus_ai
      POSTGRES_USER: nexus
      POSTGRES_PASSWORD: ${PG_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U nexus -d nexus_ai"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # docker-py需要
      - assets:/app/assets
      - sandbox_tmp:/app/sandbox_tmp
    environment:
      - DATABASE_URL=postgresql+asyncpg://nexus:${PG_PASSWORD}@postgres:5432/nexus_ai
      - REDIS_URL=redis://redis:6379
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - DEEPSEEK_EMBEDDING_API_KEY=${DEEPSEEK_EMBEDDING_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - CONFIG_ENV=production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  arq-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: arq app.worker.WorkerSettings
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - DATABASE_URL=postgresql+asyncpg://nexus:${PG_PASSWORD}@postgres:5432/nexus_ai
      - REDIS_URL=redis://redis:6379
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - frontend
      - backend

volumes:
  pgdata:
  assets:
  sandbox_tmp:
```

### 8.2 Nginx 反向代理配置（生产环境）

```nginx
# nginx.conf
server {
    listen 80;

    # 前端静态资源 + SPA路由
    location / {
        proxy_pass http://frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # 后端API
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400s;  # 长连接
    }
}
```

### 8.3 环境要求

- Docker Engine 24+
- Docker Compose v2
- **NVIDIA Container Toolkit**（可选，GPU环境预留）
- 最小硬件：4核CPU, 16GB RAM, 50GB磁盘
- 推荐硬件：8核CPU, 32GB RAM, 100GB SSD

### 8.4 开发环境

- **前端**：Vite dev server (port 5173) + HMR
- **后端**：uvicorn --reload (port 8000)
- **CORS**：开发环境允许 localhost:5173 跨域
- **数据库**：本地 PostgreSQL 16 或 Docker pgvector/pgvector:pg16
- **Redis**：本地或 Docker redis:7-alpine

---

## 9. 开发里程碑

### Phase 1：基础设施搭建（Week 1-2）
- [ ] 初始化 uv Python 项目，配置 pyproject.toml（Python 3.12）
- [ ] 配置 Ruff 代码规范工具
- [ ] 搭建 FastAPI 项目骨架（含 /api/health 端点）
- [ ] 配置 SQLAlchemy 2.0 (async) + asyncpg + create_all 自动建表
- [ ] 配置 PostgreSQL 16 + pgvector
- [ ] 配置 Redis 7 + arq 任务队列
- [ ] 初始化 Vite + React 18 + TypeScript 项目
- [ ] 配置 Tailwind CSS 3 + shadcn/ui
- [ ] 配置 Redux Toolkit + React Router
- [ ] 配置 Biome 前端代码规范
- [ ] 实现 FastAPI 原生 WebSocket 基础连接（心跳+重连）
- [ ] 实现 structlog 结构化日志（stdout → Docker日志驱动）
- [ ] 编写 Docker Compose 开发环境配置
- [ ] 配置 .env + YAML 混合配置管理

### Phase 2：核心对话系统（Week 3-4）
- [ ] 实现 LLM 网关（litellm：多模型切换、stream、API Key管理、Token计数）
- [ ] 实现会话 CRUD API + 前端会话列表
- [ ] 实现 LLM 自动生成会话标题
- [ ] 实现聊天 WebSocket 流式消息
- [ ] 实现消息持久化（Redis缓冲 + 批量写PostgreSQL）
- [ ] 实现上下文窗口管理（混合策略：滑动窗口+LLM摘要）
- [ ] 开发聊天界面：MessageBubble + 虚拟滚动 + Markdown渲染
- [ ] 开发输入区：富交互（@Agent/#文件//命令）+ Ctrl+Enter发送
- [ ] 开发模型选择下拉（顶部标题栏 + 输入区）
- [ ] 开发 Shiki 代码高亮组件
- [ ] 实现深色/浅色模式切换
- [ ] 开发 React Error Boundary + 配置 Sentry

### Phase 3：Agent系统（Week 5-7）
- [ ] 实现 Agent CRUD API + 数据库模型
- [ ] 实现 Agent Emoji 头像系统
- [ ] 实现 Agent 配置完整版本管理（回滚+对比）
- [ ] 实现 Agent 模板库（预设模板+基于模板创建）
- [ ] 开发 Agent 管理前端界面（列表+搜索+筛选+创建/编辑表单）
- [ ] 开发 Agent 版本历史前端
- [ ] 开发 Agent 模板画廊前端
- [ ] 实现 Persona 风格系统
- [ ] 实现任务编排引擎（主管-工人模式）
- [ ] 实现智能并行/串行判断（依赖分析）
- [ ] 实现跨步骤变量表
- [ ] 实现任务断点恢复（完整持久化）
- [ ] 实现 Agent 间通信机制
- [ ] 实现上下文隔离（主管全量 + Worker隔离）
- [ ] 实现按会话并发控制（默认3并行）
- [ ] 实现 arq 消息队列优先级（主管优先）
- [ ] 开发任务计划卡片前端
- [ ] 开发变量表查看前端
- [ ] 实现 Agent 状态实时推送（WebSocket /ws/agents）

### Phase 4：工具与沙箱（Week 8-9）
- [ ] 构建自建Docker沙箱镜像（Dockerfile：核心5库+按需动态安装）
- [ ] 实现 docker-py 沙箱管理（临时容器创建/执行/销毁）
- [ ] 实现 AST 静态代码分析（危险调用检测）
- [ ] 实现代码执行工具（code_executor）
- [ ] 实现数据库查询工具（SQL安全限制）
- [ ] 实现文件操作工具（读写资产目录）
- [ ] 实现网络搜索工具（IQS MCP集成）
- [ ] 实现外部 API 调用工具
- [ ] 实现工具注册中心（类注册+动态注入+运行时扩展）
- [ ] 开发代码块前端组件（复制/运行/编辑/下载 + Shiki高亮）
- [ ] 开发展开式代码编辑面板
- [ ] 开发执行进度条

### Phase 5：资产与知识库（Week 10-11）
- [ ] 实现文件上传/管理 API + 存储抽象层（本地+S3接口预留）
- [ ] 实现文件预览API（图片/PDF/文本/表格）
- [ ] 实现文档处理流水线（解析→混合分块→DeepSeek Embedding→pgvector存储）
- [ ] 配置 pgvector 扩展 + ivfflat索引
- [ ] 实现 RAG 混合检索（向量Cosine + PostgreSQL full-text search BM25，无Rerank）
- [ ] 实现引用溯源
- [ ] 开发资产面板前端
- [ ] 开发文件预览组件

### Phase 6：安全体系（Week 12-13）
- [ ] 实现 Agent 权限控制系统
- [ ] 实现审计日志全量记录（不可删除，仅追加）
- [ ] 实现 AST 代码安全预审
- [ ] 实现敏感数据脱敏
- [ ] 实现双层限流（IP + API Key）
- [ ] 开发安全面板前端（审计日志查看+筛选）

### Phase 7：系统监控（Week 14）
- [ ] 实现硬件资源采集（GPU预留+系统内存，每5秒）
- [ ] 实现 Docker 容器监控
- [ ] 开发监控面板前端（进度条+实时更新+GPU优雅降级）
- [ ] 实现 WebSocket 监控数据推送（/ws/monitor）

### Phase 8：高级功能与测试（Week 15-17）
- [ ] 实现消息编辑 + 重新生成Agent回复
- [ ] 实现会话导出（Markdown/PDF/JSON）
- [ ] 实现桌面通知（Notification API）
- [ ] 实现 WebSocket 自动重连（指数退避）
- [ ] 实现前端 i18n 框架预留
- [ ] 单元测试（pytest + pytest-asyncio + Vitest，目标60-80%覆盖率）
- [ ] 集成测试（端到端编排流程）
- [ ] 性能测试与优化
- [ ] Sentry 集成验证

### Phase 9：部署上线（Week 18）
- [ ] Docker Compose 生产配置（含 Nginx反向代理）
- [ ] 数据库迁移从 create_all 切换到 Alembic
- [ ] 编写部署文档（含GPU环境配置说明、NVIDIA Container Toolkit）
- [ ] 安全审计与渗透测试
- [ ] 生产环境部署验证

---

## 附录

### A. 参考原型

原型文件：[doc/web.html](doc/web.html)

### B. 技术决策记录

以下为已确认的关键技术决策，来源于20+轮用户需求确认：

| # | 决策项 | 选型 | 
|----|--------|------|
| 1 | 项目定位 | 企业内部工具 |
| 2 | LLM模型 | 多模型可切换（DeepSeek/OpenAI/Claude） |
| 3 | Agent定义 | 预设 + 用户自定义混合 |
| 4 | 代码执行 | Docker沙箱（docker-py + AST静态分析） |
| 5 | 用户认证 | 第一版无需登录，DB预留user_id |
| 6 | Agent工具 | 代码执行/SQL查询/文件操作/网络搜索/外部API/Agent间通信 |
| 7 | Agent协作 | 主管-工人模式，自动+人工介入 |
| 8 | 安全体系 | 完整：权限+审计+AST预审+脱敏+双层限流 |
| 9 | 前端框架 | Vite + React 18 + TypeScript + Tailwind + shadcn/ui |
| 10 | 状态管理 | Redux Toolkit |
| 11 | 前端路由 | React Router v6 |
| 12 | 代码高亮 | Shiki |
| 13 | Markdown | react-markdown + remark-gfm |
| 14 | 虚拟滚动 | react-virtuoso |
| 15 | 后端框架 | Python 3.12 + FastAPI |
| 16 | ORM | SQLAlchemy 2.0 (async) + asyncpg |
| 17 | 数据库 | PostgreSQL 16 + pgvector |
| 18 | 缓存/队列 | Redis 7 + arq |
| 19 | LLM网关 | litellm |
| 20 | 配置管理 | .env + YAML混合 → pydantic-settings |
| 21 | 代码规范(Python) | Ruff |
| 22 | 代码规范(前端) | Biome |
| 23 | 日志 | structlog → stdout → Docker日志驱动 |
| 24 | 异常追踪 | Sentry（前端） |
| 25 | 测试 | pytest + Vitest，60-80%覆盖率 |
| 26 | 部署 | Docker Compose v2 + Nginx反向代理 |
| 27 | WebSocket | FastAPI原生 + 自定义心跳 + 指数退避重连 |
| 28 | WebSocket认证 | 会话ID验证 + JWT预留 |
| 29 | Embedding | DeepSeek Embedding API (维度待API确认→pgvector列可调) |
| 30 | RAG检索 | 混合检索（向量+BM25），无Rerank |
| 31 | 文档分块 | 混合分块（语义优先+超长Token切分+10%重叠） |
| 32 | 知识库来源 | 第一版仅用户上传文档 |
| 33 | 网络搜索 | 阿里云IQS MCP Server |
| 34 | 文件存储 | 本地文件系统 + S3接口预留 |
| 35 | GPU监控 | 预留支持，无GPU环境优雅降级 |
| 36 | 沙箱镜像 | 自建Docker镜像，预装5核心库 + 动态pip install |
| 37 | 沙箱容器 | 独立临时容器，每次执行创建→销毁 |
| 38 | 沙箱网络 | 允许出站外网，禁止内网 |
| 39 | 代码预审 | Python ast模块静态分析 |
| 40 | 上下文管理 | 混合策略（滑动窗口 + LLM摘要） |
| 41 | 上下文隔离 | 主管全量 + Worker隔离 |
| 42 | 子任务执行 | 智能判断并行/串行（依赖分析） |
| 43 | 并发控制 | 按会话限制（默认3并行） |
| 44 | 消息队列优先级 | 主管优先 |
| 45 | 跨步骤变量 | 完整变量表（类似Jupyter Notebook） |
| 46 | 任务持久化 | 完整持久化，支持暂停/恢复/取消 |
| 47 | Agent超时 | 模型级+Agent级组合超时 |
| 48 | Agent版本管理 | 完整版本管理（浏览/对比/回滚） |
| 49 | Agent模板 | 模板库 + 一键创建 |
| 50 | Agent Persona | 每个Agent有独立语气风格 |
| 51 | Agent头像 | Emoji头像 |
| 52 | Agent发现 | 搜索 + 分类筛选 |
| 53 | 会话标题 | LLM自动生成 + 手动重命名 |
| 54 | 消息加载 | 无限滚动（cursor-based分页） |
| 55 | 消息编辑 | 支持编辑已发送消息 |
| 56 | 重新生成 | 支持重新生成Agent回复 |
| 57 | 消息持久化 | Redis缓冲 + 批量写PostgreSQL |
| 58 | 会话导出 | Markdown / PDF / JSON |
| 59 | 深色模式 | 支持切换 |
| 60 | 桌面通知 | Notification API |
| 61 | 国际化 | 第一版仅中文，预留i18n框架 |
| 62 | 输入方式 | 富交互（@Agent/#文件//命令）+ Ctrl+Enter发送 |
| 63 | 模型切换位置 | 顶部下拉 + 输入区旁，两处都可 |
| 64 | 代码块操作 | 复制/运行/编辑/下载 四个按钮 |
| 65 | 代码展示 | 聊天区 + 可展开独立编辑面板 |
| 66 | 文件预览 | 图片/PDF/文本/表格常见格式预览 |
| 67 | 通信端口 | 开发直接端口，生产Nginx反向代理:80 |
| 68 | 健康检查 | 完整：DB + Redis + Docker daemon |
| 69 | API限流 | 双层：IP + API Key |
| 70 | 数据库迁移 | 初期create_all → 稳定后Alembic |

### C. 待运行时确认事项

以下事项需在实际开发中通过API文档/实测确认：

1. **DeepSeek Embedding 维度**：确认DeepSeek Embedding API返回的实际向量维度，调整 `knowledge_chunks` 表的 `vector(N)` 列定义
2. **NGINX WebSocket代理超时**：根据实际长连接需求调整 `proxy_read_timeout`
3. **Docker沙箱镜像大小**：自建镜像含5核心库后的实际大小，决定是否进一步精简

### D. 变更记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2026-06-09 | 初始版本，基于原型分析和初步需求确认 |
| v2.0 | 2026-06-09 | 全面更新：70项技术决策确认，补充完整数据模型/API/WebSocket协议/部署方案/开发里程碑 |
