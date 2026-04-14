from functools import lru_cache

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from tenacity import retry, stop_after_attempt, wait_exponential

from rec2note_cli.config import get_settings

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
) -> str:
    """
    Call an OpenAI-compatible LLM and return the response text.

    Args:
        system_prompt: Optional system instruction.
        user_prompt: The user's message content.
        model_id: Override the default model from settings.
        temperature: Override the default temperature from settings.
        max_tokens: Override the default max_tokens from settings.
        json_mode: If True (default), request JSON object output via
                   response_format. Set to False for plain text responses.

    Returns:
        The model's response text as a plain string.

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

    response = client.chat.completions.create(
        model=model_id or settings.llm_model_id,
        messages=messages,
        temperature=temperature
        if temperature is not None
        else settings.llm_temperature,
        # max_tokens=max_tokens or settings.llm_max_tokens,
        response_format={"type": "json_object"} if json_mode else {"type": "text"},
    )

    return response.choices[0].message.content or ""


if __name__ == "__main__":
    result = call_llm(
        system_prompt="You are a helpful assistant.",
        user_prompt="Say hello in exactly three words.",
        json_mode=False,
    )
    print(result)
