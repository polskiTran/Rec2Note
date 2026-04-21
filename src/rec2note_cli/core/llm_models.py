from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Token usage
# ---------------------------------------------------------------------------


class TokenUsage(BaseModel):
    """Token usage from a single LLM call.

    Attributes:
        prompt_tokens: Total tokens sent in the prompt.
        completion_tokens: Tokens in the model's response.
        total_tokens: Sum of prompt and completion tokens.
        cached_tokens: Prompt tokens served from the provider cache (0 if
            the provider does not report cached token details).
    """

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cached_tokens: int = 0

    def to_dict(self) -> dict:
        return self.model_dump()


# ---------------------------------------------------------------------------
# LLM response envelope
# ---------------------------------------------------------------------------


class LLMResponse(BaseModel):
    """Envelope returned by ``call_llm()``.

    Attributes:
        content: The raw text content of the model's reply.
        model: Resolved model identifier returned by the API.
        usage: Token usage statistics for this call.
    """

    content: str
    model: str
    usage: TokenUsage

    def to_dict(self) -> dict:
        return self.model_dump()
