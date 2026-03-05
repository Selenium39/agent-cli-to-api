"""Anthropic Messages API compatibility layer.

Converts between Anthropic ``/v1/messages`` request/response format and the
internal OpenAI-style representation used by the gateway core.

Anthropic API reference:
  https://docs.anthropic.com/en/api/messages
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict

from .openai_compat import ChatCompletionRequest, ChatMessage

# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class AnthropicMessage(BaseModel):
    role: str
    content: Any
    model_config = ConfigDict(extra="allow")


class AnthropicRequest(BaseModel):
    model: str
    messages: list[AnthropicMessage]
    max_tokens: int = 4096
    system: str | list[dict[str, Any]] | None = None
    stream: bool = False
    temperature: float | None = None
    top_p: float | None = None
    top_k: int | None = None
    stop_sequences: list[str] | None = None
    metadata: dict[str, Any] | None = None
    model_config = ConfigDict(extra="allow")


# ---------------------------------------------------------------------------
# Conversion:  Anthropic request  →  internal ChatCompletionRequest
# ---------------------------------------------------------------------------


def _normalize_anthropic_content(content: Any) -> str:
    """Flatten Anthropic content (string or list of blocks) to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text" and isinstance(block.get("text"), str):
                    parts.append(block["text"])
                elif block.get("type") == "image":
                    pass  # images are handled separately
        return "\n".join(parts) if parts else ""
    return str(content) if content else ""


def _anthropic_content_to_openai(content: Any) -> Any:
    """Convert Anthropic content blocks to OpenAI content format.

    Preserves images by converting ``image`` blocks to OpenAI
    ``image_url`` parts with base64 data URIs.
    """
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return str(content) if content else ""

    has_image = any(
        isinstance(b, dict) and b.get("type") == "image" for b in content
    )
    if not has_image:
        # Plain text – flatten.
        return _normalize_anthropic_content(content)

    parts: list[dict[str, Any]] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        btype = block.get("type")
        if btype == "text" and isinstance(block.get("text"), str):
            parts.append({"type": "text", "text": block["text"]})
        elif btype == "image":
            source = block.get("source") or {}
            if isinstance(source, dict) and source.get("type") == "base64":
                media = source.get("media_type", "image/png")
                data = source.get("data", "")
                url = f"data:{media};base64,{data}"
                parts.append({"type": "image_url", "image_url": {"url": url}})
    return parts if parts else ""


def anthropic_request_to_chat_request(req: AnthropicRequest) -> ChatCompletionRequest:
    """Convert an Anthropic Messages request into an internal ``ChatCompletionRequest``."""
    messages: list[ChatMessage] = []

    # system prompt
    if req.system:
        if isinstance(req.system, str):
            messages.append(ChatMessage(role="system", content=req.system))
        elif isinstance(req.system, list):
            texts = []
            for block in req.system:
                if isinstance(block, dict) and block.get("type") == "text":
                    texts.append(block.get("text", ""))
            if texts:
                messages.append(ChatMessage(role="system", content="\n".join(texts)))

    # conversation messages
    for msg in req.messages:
        role = msg.role
        if role == "user":
            messages.append(ChatMessage(role="user", content=_anthropic_content_to_openai(msg.content)))
        elif role == "assistant":
            messages.append(ChatMessage(role="assistant", content=_normalize_anthropic_content(msg.content)))
        else:
            messages.append(ChatMessage(role=role, content=_normalize_anthropic_content(msg.content)))

    extra: dict[str, Any] = {}
    if req.temperature is not None:
        extra["temperature"] = req.temperature
    if req.top_p is not None:
        extra["top_p"] = req.top_p

    return ChatCompletionRequest(
        model=req.model,
        messages=messages,
        stream=req.stream,
        max_tokens=req.max_tokens,
        **extra,
    )


# ---------------------------------------------------------------------------
# Conversion:  internal OpenAI response  →  Anthropic response
# ---------------------------------------------------------------------------


def _new_msg_id() -> str:
    return f"msg_{uuid.uuid4().hex[:24]}"


def openai_chat_completion_to_anthropic(body: dict[str, Any], *, model_hint: str = "") -> dict[str, Any]:
    """Convert an OpenAI ``chat.completion`` JSON body to an Anthropic Messages response."""
    text = ""
    stop_reason = "end_turn"
    choices = body.get("choices") or []
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            message = first.get("message") or {}
            if isinstance(message, dict):
                raw = message.get("content")
                text = raw if isinstance(raw, str) else ""
            fr = first.get("finish_reason")
            if fr == "length":
                stop_reason = "max_tokens"
            elif fr == "tool_calls":
                stop_reason = "tool_use"

    usage_in = body.get("usage") or {}
    input_tokens = int(usage_in.get("prompt_tokens") or 0)
    output_tokens = int(usage_in.get("completion_tokens") or 0)

    model = model_hint or body.get("model") or "unknown"

    return {
        "id": _new_msg_id(),
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": [{"type": "text", "text": text}],
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        },
    }


# ---------------------------------------------------------------------------
# Anthropic SSE streaming helpers
# ---------------------------------------------------------------------------


def anthropic_stream_start(*, model: str, msg_id: str | None = None) -> list[str]:
    """Return the SSE lines for the start of an Anthropic stream.

    Emits ``message_start`` and ``content_block_start`` events.
    """
    mid = msg_id or _new_msg_id()
    message_start = {
        "type": "message_start",
        "message": {
            "id": mid,
            "type": "message",
            "role": "assistant",
            "model": model,
            "content": [],
            "stop_reason": None,
            "stop_sequence": None,
            "usage": {"input_tokens": 0, "output_tokens": 0},
        },
    }
    content_block_start = {
        "type": "content_block_start",
        "index": 0,
        "content_block": {"type": "text", "text": ""},
    }
    return [
        f"event: message_start\ndata: {json.dumps(message_start, ensure_ascii=False)}\n\n",
        f"event: content_block_delta\ndata: {json.dumps(content_block_start, ensure_ascii=False)}\n\n",
    ]


def anthropic_stream_delta(text: str) -> str:
    """Return a single ``content_block_delta`` SSE event."""
    evt = {
        "type": "content_block_delta",
        "index": 0,
        "delta": {"type": "text_delta", "text": text},
    }
    return f"event: content_block_delta\ndata: {json.dumps(evt, ensure_ascii=False)}\n\n"


def anthropic_stream_end(
    *,
    stop_reason: str = "end_turn",
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> list[str]:
    """Return the SSE lines that close an Anthropic stream.

    Emits ``content_block_stop``, ``message_delta``, and ``message_stop``.
    """
    content_block_stop = {"type": "content_block_stop", "index": 0}
    message_delta = {
        "type": "message_delta",
        "delta": {"stop_reason": stop_reason, "stop_sequence": None},
        "usage": {"output_tokens": output_tokens},
    }
    message_stop = {"type": "message_stop"}
    return [
        f"event: content_block_stop\ndata: {json.dumps(content_block_stop, ensure_ascii=False)}\n\n",
        f"event: message_delta\ndata: {json.dumps(message_delta, ensure_ascii=False)}\n\n",
        f"event: message_stop\ndata: {json.dumps(message_stop, ensure_ascii=False)}\n\n",
    ]
