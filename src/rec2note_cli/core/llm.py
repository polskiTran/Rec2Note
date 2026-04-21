from functools import lru_cache

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from tenacity import retry, stop_after_attempt, wait_exponential

from rec2note_cli.config import get_settings
from rec2note_cli.core.llm_models import LLMResponse, TokenUsage

settings = get_settings()


@lru_cache
def _get_client() -> OpenAI:
    return OpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
def call_llm(
    system_prompt: str | None = None,
    user_prompt: str | None = None,
    model_id: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    json_mode: bool = True,
    task_prompt: str | None = None,
) -> LLMResponse:
    """Call an OpenAI-compatible LLM and return the response envelope.

    Args:
        system_prompt: Optional system instruction.
        user_prompt: The user's message content (typically the transcript).
        model_id: Override the default model from settings.
        temperature: Override the default temperature from settings.
        max_tokens: Override the default max_tokens from settings.
        json_mode: If True (default), request JSON object output via
                   response_format. Set to False for plain text responses.
        task_prompt: Optional second user message appended after user_prompt.
            Used for agent-specific task instructions when user_prompt
            carries the shared transcript. This ordering ensures the
            transcript forms a cacheable prefix across all agents.

    Returns:
        An :class:`LLMResponse` containing the reply text, resolved model
        identifier, and token usage statistics.

    Raises:
        ValueError: If no user_prompt is provided.
    """
    if not user_prompt:
        raise ValueError("user_prompt is required")

    client = _get_client()

    messages: list[ChatCompletionMessageParam] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})
    if task_prompt:
        messages.append({"role": "user", "content": task_prompt})

    response = client.chat.completions.create(
        model=model_id or settings.llm_model_id,
        messages=messages,
        temperature=temperature
        if temperature is not None
        else settings.llm_temperature,
        response_format={"type": "json_object"} if json_mode else {"type": "text"},
    )

    usage = response.usage
    cached = 0
    if usage and usage.prompt_tokens_details:
        cached = usage.prompt_tokens_details.cached_tokens or 0

    return LLMResponse(
        content=response.choices[0].message.content or "",
        model=response.model,
        usage=TokenUsage(
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            cached_tokens=cached,
        ),
    )


if __name__ == "__main__":
    result = call_llm(
        system_prompt="You are a helpful assistant.",
        user_prompt="Say hello in exactly three words.",
        json_mode=False,
    )
    print(result.content)
