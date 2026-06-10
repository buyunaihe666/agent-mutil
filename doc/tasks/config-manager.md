# M12 — 配置管理 (`config_manager`)

> 模块职责：统一管理应用配置，支持 .env + YAML 混合加载，通过 pydantic-settings 进行类型校验。

---

## 子任务

### 1. 配置加载

- [ ] 1.1 使用 pydantic-settings 定义 Settings 类（环境变量映射）
- [ ] 1.2 支持 .env 文件加载（python-dotenv 或 pydantic-settings 内置）
- [ ] 1.3 支持 YAML 配置文件加载（创建 config.yaml，通过 PyYAML 解析）
- [ ] 1.4 配置优先级：环境变量 > .env > YAML > 默认值
- [ ] 1.5 配置类包含所有配置域（见下）

### 2. 配置域定义

- [ ] 2.1 数据库配置：DATABASE_URL, DB_POOL_SIZE, DB_POOL_OVERFLOW
- [ ] 2.2 Redis 配置：REDIS_URL, REDIS_MAX_CONNECTIONS
- [ ] 2.3 API Keys（通过 .env）：DEEPSEEK_API_KEY, DEEPSEEK_EMBEDDING_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY
- [ ] 2.4 模型配置（YAML）：提供商列表、模型列表、默认超时、速率限制
- [ ] 2.5 Agent 预设配置（YAML）：三个预设 Agent 的 System Prompt、工具集、权限、Emoji
- [ ] 2.6 沙箱配置（YAML）：内存限制(512MB)、CPU限制(1核)、执行超时(60s)、seccomp 文件路径、网络策略
- [ ] 2.7 安全配置（YAML）：脱敏正则规则列表、IP 限流参数（窗口大小+次数）
- [ ] 2.8 文件存储配置（YAML）：存储后端类型(local/s3)、本地路径、S3 bucket/endpoint
- [ ] 2.9 Embedding 配置（YAML）：模型ID、向量维度（待运行时确认）、批量大小
- [ ] 2.10 WebSocket 配置（YAML）：心跳间隔(30s)、重连退避参数
- [ ] 2.11 编排配置（YAML）：默认并行数(3)、Agent 超时默认值(300s)
- [ ] 2.12 应用配置：APP_NAME, APP_VERSION, DEBUG, LOG_LEVEL

### 3. 配置校验

- [ ] 3.1 使用 pydantic validators 校验必填字段
- [ ] 3.2 校验 YAML 文件格式和内容合法性
- [ ] 3.3 应用启动时校验所有配置 → 配置缺失或错误时启动失败并给出明确提示
- [ ] 3.4 敏感配置（API Key）标记为 SecretStr 类型

### 4. 配置热加载（可选）

- [ ] 4.1 YAML 配置文件变更检测（watchdog 或手动触发）
- [ ] 4.2 支持部分配置热加载（安全脱敏规则、限流参数等）
- [ ] 4.3 数据库/Redis 连接等核心配置需要重启生效

### 5. 测试

- [ ] 5.1 测试 .env + YAML 混合加载
- [ ] 5.2 测试配置优先级
- [ ] 5.3 测试缺失必填字段的错误提示
- [ ] 5.4 测试 SecretStr 不泄露
