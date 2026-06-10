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
                "system_prompt": "你是一个数字主管，负责分析用户任务、拆解为子任务、分配给合适的Worker Agent。你需要从全局视角思考，确保任务完整覆盖。",
                "tools": ["file_read", "agent_communication"],
                "temperature": 0.3,
                "max_tokens": 8192,
            },
            {
                "name": "风控顾问",
                "description": "安全审计与合规检查",
                "avatar_emoji": "🛡️",
                "permission_level": 3,
                "system_prompt": "你是一个风控顾问，负责监控系统操作、检测未授权访问、审计代码执行、检查数据合规。你的语气谨慎、严谨、合规导向。",
                "tools": ["code_execution_audit", "file_read", "database_query"],
                "temperature": 0.2,
                "max_tokens": 8192,
            },
            {
                "name": "数据专家",
                "description": "数据处理与分析",
                "avatar_emoji": "📊",
                "permission_level": 2,
                "system_prompt": "你是一个数据专家，擅长SQL查询、数据清洗、统计分析和图表生成。你的回答技术化、精确、数据导向。",
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
