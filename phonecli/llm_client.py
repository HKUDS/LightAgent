"""OpenAI-compatible API client for text LLM and vision (VLM) calls."""

import base64
import sys
from typing import Optional


def _get_client(api_key: str, api_base: str):
    """Lazy import OpenAI client."""
    from openai import OpenAI
    return OpenAI(api_key=api_key, base_url=api_base, timeout=60.0)


def _encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def text_completion(
    system_prompt: str,
    user_prompt: str,
    api_key: str = "EMPTY",
    api_base: str = "http://localhost:8002/v1",
    model: str = "Qwen/Qwen2.5-3B-Instruct",
    max_tokens: int = 4096,
    temperature: float = 0.0,
) -> str:
    """Send a text-only completion request."""
    client = _get_client(api_key, api_base)
    # DeepSeek-specific: disable thinking/reasoning mode for faster responses
    extra = {}
    if "deepseek" in api_base.lower() or "deepseek" in model.lower():
        extra["extra_body"] = {"thinking": {"type": "disabled"}}

    try:
        r = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            **extra,
        )
        content = r.choices[0].message.content or ""
        # DeepSeek thinking mode may return reasoning_content instead
        if not content and hasattr(r.choices[0].message, "reasoning_content"):
            content = r.choices[0].message.reasoning_content or ""
        return content
    except Exception as e:
        print(f"LLM error: {e}", file=sys.stderr)
        raise


def vision_completion(
    system_prompt: str,
    user_text: str,
    image_paths: list[str],
    api_key: str = "EMPTY",
    api_base: str = "http://localhost:8002/v1",
    model: str = "Qwen/Qwen2.5-3B-Instruct",
    max_tokens: int = 4096,
    temperature: float = 0.0,
) -> str:
    """Send a vision (image + text) completion request."""
    client = _get_client(api_key, api_base)

    # Build multimodal content
    content = [{"type": "text", "text": user_text}]
    for path in image_paths:
        b64 = _encode_image(path)
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}"},
        })

    try:
        r = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return r.choices[0].message.content or ""
    except Exception as e:
        print(f"VLM error: {e}", file=sys.stderr)
        raise
