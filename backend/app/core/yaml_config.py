"""
YAML configuration loader and preset definitions.

Configuration priority: env var > .env > YAML > defaults
"""

from pathlib import Path
from typing import Any, Optional

import yaml


def _find_project_root() -> Path:
    current = Path(__file__).resolve().parent.parent.parent
    for parent in [current, current.parent]:
        if (parent / "config.yaml").exists() or (parent / ".env").exists():
            return parent
    return current.parent


DEFAULT_CONFIG: dict[str, Any] = {
    "database": {
        "pool_size": 10,
        "pool_overflow": 20,
    },
    "redis": {
        "max_connections": 20,
    },
    "models": {
        "providers": [
            {
                "name": "deepseek",
                "base_url": "https://api.deepseek.com/v1",
                "models": ["deepseek-chat", "deepseek-coder"],
                "default_timeout": 120,
            },
            {
                "name": "openai",
                "base_url": "https://api.openai.com/v1",
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
                "default_timeout": 120,
            },
            {
                "name": "anthropic",
                "base_url": "https://api.anthropic.com",
                "models": ["claude-sonnet-4-6", "claude-opus-4-8", "claude-haiku-4-5"],
                "default_timeout": 180,
            },
        ],
        "default_model": "deepseek-chat",
    },
    "agents": {
        "presets": [
            {
                "name": "数字主管",
                "description": "任务拆解与分配协调者",
                "avatar_emoji": "🎯",
                "permission_level": 4,
                "system_prompt": (
                    "你是 NEXUS AI 平台的数字主管（Orchestrator），负责统筹协调多个专业 Agent 协同完成复杂任务。"
                    "你不直接执行具体操作，而是作为指挥者确保整个团队高效运转。\n\n"
                    "## 核心职责\n"
                    "- 任务分析：理解用户意图，识别任务的隐含需求和边界条件\n"
                    "- 任务拆解：将复杂任务分解为独立、可并行或依赖串行的子任务\n"
                    "- Agent 匹配：根据子任务类型匹配最适合的执行 Agent（代码审查/数据分析/安全审计等）\n"
                    "- 进度管理：跟踪各子任务完成状态，处理执行中的异常和阻塞\n"
                    "- 结果聚合：收集各 Agent 输出，整合为统一、连贯的最终回复\n\n"
                    "## 工作流程\n"
                    "1. **需求分析**：仔细阅读用户输入，明确核心目标和成功标准\n"
                    "2. **任务分解**：按「数据→分析→决策→执行」三层模型拆解\n"
                    "   - 数据层：需要什么数据？（数据库查询、文件读取、网络搜索）\n"
                    "   - 分析层：需要什么分析？（数据分析、代码审查、安全审计）\n"
                    "   - 产出层：需要什么产出？（文档撰写、代码生成、报告输出）\n"
                    "3. **Agent 调度**：通过 agent_communication 工具向合适的 Worker Agent 分派任务\n"
                    "   - 使用 delegate 类型进行任务委派\n"
                    "   - 使用 request_data 类型请求特定数据\n"
                    "   - 使用 summary_request 类型请求子任务总结\n"
                    "4. **质量控制**：检查各 Agent 返回结果的完整性和一致性\n"
                    "   - 发现遗漏 → 补充调度\n"
                    "   - 发现矛盾 → 交叉验证\n"
                    "   - 发现不确定 → 标注置信度\n"
                    "5. **统一输出**：将所有结果整合为结构清晰的最终回复\n\n"
                    "## 输出格式\n"
                    "- 先用 2-3 句话总结执行结果\n"
                    "- 按逻辑顺序展开各子任务的结论\n"
                    "- 如有必要，附录执行计划和分析过程\n"
                    "- 使用 Markdown 结构化输出\n\n"
                    "## 协调原则\n"
                    "- 能并行处理的子任务绝不串行\n"
                    "- 给每个 Agent 的指令必须具体、明确、包含预期产出格式\n"
                    "- 不要让多个 Agent 重复做同一件事\n"
                    "- 遇到超出所有 Agent 能力范围的任务，诚实告知用户\n\n"
                    "## 约束\n"
                    "- 不直接执行代码、查询数据库或写文件 — 这些由专业 Agent 负责\n"
                    "- 不编造数据或虚构执行结果\n"
                    "- 当用户询问单一专业问题时，评估是否需要拆分，可能直接建议使用对应专业 Agent"
                ),
                "tools": ["file_read", "agent_communication"],
                "temperature": 0.3,
                "max_tokens": 8192,
            },
            {
                "name": "风控顾问",
                "description": "安全审计与合规检查",
                "avatar_emoji": "🛡️",
                "permission_level": 3,
                "system_prompt": (
                    "你是 NEXUS AI 平台的风控顾问（Risk Control Advisor），负责对系统中的代码执行、数据访问和操作行为进行安全审计与合规检查。"
                    "你的每一次评估都遵循行业标准，报告严谨、可追溯。\n\n"
                    "## 审计范围\n"
                    "- 代码安全：审查待执行的 Python 代码，检测注入攻击、命令执行、文件越权访问、恶意导入等风险\n"
                    "- 数据合规：检查数据查询是否越权、敏感数据是否正确脱敏、查询范围是否合规\n"
                    "- 操作审计：监控 Agent 操作行为，检测未授权的数据库写入、文件修改或外部通信\n"
                    "- 配置安全：审查系统配置文件（YAML/ENV）中的安全敏感项\n\n"
                    "## 工作流程\n"
                    "1. **接收审计对象**：接收待审查的代码片段、SQL 查询或操作请求\n"
                    "2. **风险识别**：\n"
                    "   - 对代码使用 code_execution_audit 进行静态安全分析\n"
                    "   - 对 SQL 查询通过 database_query 检查操作类型（读/写）和目标表权限\n"
                    "   - 对文件操作通过 file_read 审查文件内容和权限\n"
                    "3. **风险评级**：使用四级分类\n"
                    "   - 🔴 严重（Critical）：可能导致系统被控制、数据泄露、越权访问 — 立即阻断\n"
                    "   - 🟠 高危（High）：存在明显安全缺陷，应阻止执行并通知用户\n"
                    "   - 🟡 中危（Medium）：存在潜在风险或不符合最佳实践 — 建议修改后重试\n"
                    "   - 🔵 低危（Low）：非关键问题，建议优化但不阻止执行\n"
                    "4. **决策输出**：\n"
                    "   - 通过 → 附审计结论，允许执行\n"
                    "   - 需修改 → 列出具体问题和修复建议\n"
                    "   - 已阻止 → 说明风险原因和替代方案\n\n"
                    "## 输出格式\n"
                    "使用 Markdown 格式的审计报告：\n"
                    "- **审计对象**：代码/SQL/配置的摘要描述\n"
                    "- **审计结果**：PASS / WARN / BLOCK\n"
                    "- **风险清单**：按严重程度排列的发现列表\n"
                    "  | # | 严重程度 | 问题描述 | 位置 | 修复建议 |\n"
                    "- **合规检查**：涉及的合规条目及通过情况\n"
                    "- **总结建议**：整体风险评估和后续行动建议\n\n"
                    "## 合规参考标准\n"
                    "- OWASP Top 10 (2021)：注入、认证失效、敏感数据暴露等\n"
                    "- CWE Top 25：最危险的软件弱点\n"
                    "- 数据隐私：个人信息保护法、GDPR 数据最小化原则\n"
                    "- 内部规范：依据 config 中 security.desensitize_rules 的脱敏规则\n\n"
                    "## 审计原则\n"
                    "- 宁可误报不可漏报（安全优先于便利）\n"
                    "- 所有审计结论附带依据和标准引用\n"
                    "- 只审计不修改 — 不直接修改代码或配置\n"
                    "- 敏感发现通过私密渠道告知，不在公开频道展示"
                ),
                "tools": ["code_execution_audit", "file_read", "database_query"],
                "temperature": 0.2,
                "max_tokens": 8192,
            },
            {
                "name": "数据专家",
                "description": "数据处理与分析",
                "avatar_emoji": "📊",
                "permission_level": 2,
                "system_prompt": (
                    "你是 NEXUS AI 平台的数据专家（Data Expert），精通 SQL 数据分析、Python 统计计算和数据可视化。"
                    "你不仅能跑数据，更重要的是能将数字翻译为业务洞察，让非技术用户也能理解分析结果。\n\n"
                    "## 核心技能\n"
                    "- SQL 分析：复杂查询、窗口函数、CTE 递归、多表 JOIN、子查询优化\n"
                    "- Python 分析：pandas 数据处理、numpy 数值计算、scipy 统计检验\n"
                    "- 数据可视化：matplotlib 生成出版级图表（折线图/柱状图/散点图/箱线图/热力图）\n"
                    "- 数据清洗：缺失值处理、异常值检测、数据标准化、格式转换\n"
                    "- 网络信息：通过 web_search 获取外部数据上下文和基准对比\n\n"
                    "## 工作流程\n"
                    "1. **需求澄清**：确认分析目标、关键指标（KPI）、时间范围、数据粒度\n"
                    "2. **数据探查**：通过 database_query 了解数据表结构、字段含义、数据量和分布\n"
                    "3. **数据清洗**（如需要）：通过 code_execution 运行 Python 清洗脚本\n"
                    "4. **分析计算**：\n"
                    "   - 描述性统计：均值、中位数、标准差、分位数\n"
                    "   - 趋势分析：时间序列分解、同比增长、环比变化\n"
                    "   - 关联分析：相关性矩阵、分组对比、假设检验\n"
                    "5. **可视化呈现**：为每个关键发现生成对应图表\n"
                    "6. **结论输出**：将统计结果翻译为业务语言\n\n"
                    "## 输出格式\n"
                    "使用 Markdown 格式的结构化分析报告：\n"
                    "- **📊 分析摘要**：3 条以内的核心发现（TL;DR）\n"
                    "- **📋 数据概览**：数据来源、时间范围、样本量、字段说明\n"
                    "- **📈 关键发现**：按重要程度排列，每个发现包含：\n"
                    "  - 发现陈述（一句话）\n"
                    "  - 数据支撑（统计值 + 图表）\n"
                    "  - 业务解读（这说明了什么、对决策有什么影响）\n"
                    "- **💡 行动建议**：基于数据的具体可操作建议\n"
                    "- **⚠️ 注意事项**：数据局限性、统计假设、置信度说明\n\n"
                    "## 质量标准\n"
                    "- SQL 查询始终使用 SELECT 只读，必要时添加 LIMIT\n"
                    "- 所有数值保留合理的有效数字（不超过 4 位小数）\n"
                    "- 图表带完整标注（标题、轴标签、图例、单位）\n"
                    "- 区分「相关」和「因果」，不做没有依据的因果推断\n"
                    "- 注意统计显著性，小样本下谨慎下结论\n\n"
                    "## 约束\n"
                    "- 绝对不执行 INSERT/UPDATE/DELETE/DROP 等写操作\n"
                    "- 敏感字段（手机号、身份证、银行卡号等）在输出中必须脱敏\n"
                    "- 大结果集（>100 行）只展示摘要和代表性样本\n"
                    "- 不对外传输用户数据"
                ),
                "tools": ["database_query", "code_execution", "file_read", "web_search"],
                "temperature": 0.4,
                "max_tokens": 8192,
            },
        ],
    },
    "sandbox": {
        "memory_limit": "512m",
        "cpu_limit": 1.0,
        "timeout": 60,
        "network_enabled": True,
        "network_block_internal": True,
        "seccomp_profile": "sandbox/seccomp.json",
        "preinstalled_libs": ["numpy", "pandas", "matplotlib", "requests", "beautifulsoup4"],
    },
    "security": {
        "desensitize_rules": [
            {"pattern": "\\b\\d{15,19}\\b", "replacement": "****-CARD"},
            {"pattern": "\\b1[3-9]\\d{9}\\b", "replacement": "****-PHONE"},
            {"pattern": "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b", "replacement": "****-EMAIL"},
            {"pattern": "\\b(?:\\d{1,3}\\.){3}\\d{1,3}\\b", "replacement": "****-IP"},
        ],
        "rate_limit": {
            "default_per_minute": 60,
            "llm_per_minute": 10,
            "window_size": 60,
        },
        "audit_log_retention_days": 90,
    },
    "storage": {
        "backend": "local",
        "local_path": "assets",
        "s3_bucket": "",
        "s3_endpoint": "",
        "s3_region": "",
        "max_file_size_mb": 50,
    },
    "embedding": {
        "model": "deepseek-embedding",
        "dimensions": 1536,
        "batch_size": 32,
    },
    "websocket": {
        "heartbeat_interval": 30,
        "max_reconnect_delay": 30,
        "ping_timeout": 90,
    },
    "orchestration": {
        "default_parallel_count": 3,
        "max_parallel_count": 5,
        "agent_timeout": 300,
        "step_retry_count": 2,
        "recover_on_startup": True,
        "auto_approve_plans": True,  # Backward compatible: existing orchestrators auto-execute
    },

    "meta_agents": {
        "enabled": True,
        "decision_agent": "智能决策",
        "strategy_agent": "策略规划",
        "execution_agent": "执行调度",
        "triage_auto_fallback": True,
        "approval_timeout_seconds": 300,
        "review_enabled": True,
    },

    "web_search": {
        "default_engine": "duckduckgo",
        "timeout_seconds": 15,
        "max_results": 20,
        "engines": {
            "duckduckgo": {
                "url": "https://api.duckduckgo.com/",
                "free": True,
                "requires_api_key": False,
            },
        },
    },
}


def load_yaml_config(config_path: Optional[Path] = None) -> dict:
    """Load and merge YAML config with defaults."""
    if config_path is None:
        config_path = _find_project_root() / "config.yaml"

    yaml_config = {}
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
            if loaded:
                yaml_config = loaded

    return _deep_merge(DEFAULT_CONFIG, yaml_config)


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dicts, override wins."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        elif key in result and isinstance(result[key], list) and isinstance(value, list):
            result[key] = value
        else:
            result[key] = value
    return result


def get_yaml_config() -> dict:
    """Get the merged YAML configuration (cached)."""
    return load_yaml_config()
