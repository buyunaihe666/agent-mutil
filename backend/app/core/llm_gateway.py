"""LLM Gateway - unified multi-model access via litellm."""

import asyncio
import json
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional

import structlog
import litellm
from litellm import acompletion, completion_cost

from app.core.config import get_settings
from app.core.yaml_config import get_yaml_config

logger = structlog.get_logger(__name__)

settings = get_settings()
yaml_config = get_yaml_config()


# --- Data Classes ---

@dataclass
class ChatMessage:
    role: str  # system, user, assistant, tool
    content: Optional[str] = None
    tool_calls: Optional[list[dict]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


@dataclass
class ChatRequest:
    model: str
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 4096
    tools: Optional[list[dict]] = None
    stream: bool = False
    agent_timeout: Optional[int] = None


@dataclass
class ChatResponse:
    content: Optional[str] = None
    tool_calls: Optional[list[dict]] = None
    token_usage: dict = field(default_factory=dict)
    model: str = ""
    finish_reason: str = "stop"


@dataclass
class Delta:
    content: Optional[str] = None
    tool_call_delta: Optional[dict] = None
    finish_reason: Optional[str] = None


@dataclass
class ModelInfo:
    id: str
    name: str
    provider: str
    max_tokens: int = 4096
    supports_streaming: bool = True
    supports_tools: bool = True


# --- Provider Configuration ---

def _get_provider_configs() -> list[dict]:
    """Get provider configs from YAML config."""
    return yaml_config.get("models", {}).get("providers", [])


def _get_model_timeout(model_name: str) -> int:
    """Get timeout for a specific model from config."""
    providers = _get_provider_configs()
    for provider in providers:
        if model_name in provider.get("models", []):
            return provider.get("default_timeout", 120)
    return 120


def _get_api_key_for_model(model_name: str) -> Optional[str]:
    """Find the API key for a model based on provider matching."""
    # Strip litellm provider prefix (e.g. "deepseek/deepseek-chat" -> "deepseek-chat")
    clean_name = model_name.split("/", 1)[1] if "/" in model_name else model_name
    providers = _get_provider_configs()
    for provider in providers:
        if clean_name in provider.get("models", []):
            provider_name = provider["name"]
            return settings.get_api_key(provider_name)
    return None


# --- Core Functions ---

def get_available_models() -> list[ModelInfo]:
    """Return all available models across all providers."""
    models: list[ModelInfo] = []
    providers = _get_provider_configs()
    for provider in providers:
        for model_name in provider.get("models", []):
            models.append(ModelInfo(
                id=model_name,
                name=model_name,
                provider=provider["name"],
                supports_streaming=True,
                supports_tools=True,
            ))
    return models


async def chat_completion(request: ChatRequest) -> ChatResponse:
    """Non-streaming chat completion via litellm."""
    api_key = _get_api_key_for_model(request.model)
    model_timeout = _get_model_timeout(request.model)
    effective_timeout = min(
        model_timeout,
        request.agent_timeout if request.agent_timeout else model_timeout,
    )

    messages = [_msg_to_dict(m) for m in request.messages]

    kwargs = {
        "model": request.model,
        "messages": messages,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "timeout": effective_timeout,
    }

    if api_key:
        kwargs["api_key"] = api_key
    if request.tools:
        kwargs["tools"] = request.tools

    try:
        response = await acompletion(**kwargs)
        choice = response.choices[0]
        msg = choice.message

        token_usage = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            "total_tokens": response.usage.total_tokens if response.usage else 0,
            "model": request.model,
        }

        return ChatResponse(
            content=msg.content,
            tool_calls=_extract_tool_calls(msg),
            token_usage=token_usage,
            model=response.model,
            finish_reason=choice.finish_reason or "stop",
        )
    except litellm.exceptions.APIError as e:
        logger.error("LLM API error", model=request.model, error=str(e))
        raise
    except litellm.exceptions.Timeout:
        logger.error("LLM timeout", model=request.model, timeout=effective_timeout)
        raise
    except Exception as e:
        logger.error("LLM call failed", model=request.model, error=str(e))
        raise


async def chat_completion_stream(request: ChatRequest) -> AsyncGenerator[Delta, None]:
    """Streaming chat completion via litellm."""
    api_key = _get_api_key_for_model(request.model)
    model_timeout = _get_model_timeout(request.model)
    effective_timeout = min(
        model_timeout,
        request.agent_timeout if request.agent_timeout else model_timeout,
    )

    messages = [_msg_to_dict(m) for m in request.messages]

    kwargs = {
        "model": request.model,
        "messages": messages,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "timeout": effective_timeout,
        "stream": True,
    }

    if api_key:
        kwargs["api_key"] = api_key
    if request.tools:
        kwargs["tools"] = request.tools

    try:
        response = await acompletion(**kwargs)
        async for chunk in response:
            choice = chunk.choices[0] if chunk.choices else None
            if choice is None:
                continue

            delta = choice.delta
            if delta is None:
                continue

            yield Delta(
                content=delta.content,
                tool_call_delta=_extract_tool_call_delta(delta),
                finish_reason=choice.finish_reason,
            )
    except asyncio.CancelledError:
        logger.info("Stream cancelled by client", model=request.model)
        raise
    except litellm.exceptions.APIError as e:
        logger.error("LLM stream API error", model=request.model, error=str(e))
        raise
    except Exception as e:
        logger.error("LLM stream failed", model=request.model, error=str(e))
        raise


async def get_embedding(text: str, model: str = "deepseek-embedding") -> list[float]:
    """Get text embedding via DeepSeek Embedding API."""
    api_key = settings.get_api_key("deepseek")
    # litellm doesn't have a direct async embedding call with the same interface
    # Use httpx directly
    import httpx

    embed_config = yaml_config.get("embedding", {})
    base_url = "https://api.deepseek.com/v1"

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{base_url}/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "input": text,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["data"][0]["embedding"]


# --- Helpers ---

def _msg_to_dict(msg: ChatMessage) -> dict:
    """Convert ChatMessage to litellm-compatible dict."""
    d = {"role": msg.role}
    if msg.content is not None:
        d["content"] = msg.content
    if msg.tool_calls:
        d["tool_calls"] = msg.tool_calls
    if msg.tool_call_id:
        d["tool_call_id"] = msg.tool_call_id
    if msg.name:
        d["name"] = msg.name
    return d


def _extract_tool_calls(msg) -> Optional[list[dict]]:
    """Extract tool calls from a litellm message."""
    if hasattr(msg, "tool_calls") and msg.tool_calls:
        return [
            {
                "id": tc.id,
                "type": tc.type,
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in msg.tool_calls
        ]
    return None


def _extract_tool_call_delta(delta) -> Optional[dict]:
    """Extract tool call delta from a streaming chunk."""
    if hasattr(delta, "tool_calls") and delta.tool_calls:
        tc = delta.tool_calls[0]
        result = {}
        if hasattr(tc, "id") and tc.id:
            result["id"] = tc.id
        if hasattr(tc, "index"):
            result["index"] = tc.index
        if hasattr(tc, "function"):
            func = {}
            if hasattr(tc.function, "name") and tc.function.name:
                func["name"] = tc.function.name
            if hasattr(tc.function, "arguments") and tc.function.arguments:
                func["arguments"] = tc.function.arguments
            if func:
                result["function"] = func
        return result if result else None
    return None
