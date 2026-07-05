"""Shared LiteLLM helper for GLM 5.2 (via DeepInfra) calls.

Centralizes the model string and API key so callers don't each duplicate
provider config - a prior migration got this wrong in three different
places at once (wired the "zai/" direct-Z.AI prefix instead of DeepInfra's
"deepinfra/" prefix), see ADR-006's amendment for the full story.
"""

import litellm

from app.core.config import settings

MODEL = "deepinfra/zai-org/GLM-5.2"


async def complete(messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call GLM 5.2 via DeepInfra through LiteLLM, return the response text.

    GLM 5.2 is a reasoning model - it spends tokens on hidden
    reasoning_content before the visible answer. Budget max_tokens for
    both, not just the visible output size, or you'll get
    finish_reason="length" with empty content.
    """
    response = await litellm.acompletion(
        model=MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=settings.deepinfra_api_key or None,
    )
    return response.choices[0].message.content
