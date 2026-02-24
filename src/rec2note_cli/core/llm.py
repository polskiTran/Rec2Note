from typing import Any

from google import genai
from google.genai import types
from rich import print
from tenacity import retry, stop_after_attempt, wait_exponential

from rec2note_cli.config import get_settings
from rec2note_cli.utils.read_file import read_file

settings = get_settings()


def _get_client() -> genai.Client:
    """Return an authenticated Gemini client."""
    return genai.Client(api_key=settings.google_gemini_api_key)


def create_transcript_cache(
    model_id: str,
    transcript: str,
    ttl: str = settings.google_gemini_cache_ttl,
) -> str:
    """
    Create an explicit cache for the transcript content.

    This cache can be reused across all 4 agents to avoid sending the
    large transcript multiple times to the API.

    Args:
        model_id:   The model that will consume this cache, e.g.
                    ``"gemini-2.5-flash"``.  Must match the model used in
                    ``call_llm``.
        transcript: The transcript text to cache.
        ttl:        How long the cache should live on Google's servers, e.g.
                    ``"300s"`` or ``"3600s"``.  Defaults to config settings.

    Returns:
        The opaque cache name string (e.g. ``"cachedContents/abc123"``).
        Pass this value to ``call_llm`` via ``cache_name``.
    """
    client = _get_client()

    cache_config = types.CreateCachedContentConfig(
        contents=[transcript],
        ttl=ttl,
    )

    cache = client.caches.create(model=model_id, config=cache_config)
    return cache.name if cache.name else ""


# def create_llm_cache(
#     model_id: str,
#     input_data: Any,
#     sys_prompt: str | None = None,
#     ttl: str = settings.google_gemini_cache_ttl,
# ) -> str:
#     """
#     Upload ``input_data`` to a server-side Gemini context cache and return
#     the cache name.

#     The returned name should be stored by the caller and passed as
#     ``cache_name`` to :func:`call_llm` for every subsequent request that
#     should benefit from the cached context.  Google charges a reduced token
#     rate for cache hits, so creating the cache once and reusing the name
#     across many calls is what actually saves cost.

#     Args:
#         model_id:   The model that will consume this cache, e.g.
#                     ``"gemini-2.5-flash"``.  Must match the model used in
#                     ``call_llm``.
#         input_data: The large context to cache (str, bytes, Part, uploaded
#                     File reference, or any other genai-compatible type).
#         sys_prompt: Optional system instruction to bake into the cache.  When
#                     the cache is used in ``call_llm`` the system prompt must
#                     NOT be passed again — it is already present in the cache.
#         ttl:        How long the cache should live on Google's servers, e.g.
#                     ``"300s"`` or ``"3600s"``.  Defaults to one hour.

#     Returns:
#         The opaque cache name string (e.g. ``"cachedContents/abc123"``).
#         Pass this value to ``call_llm`` via ``cache_name``.
#     """
#     client = _get_client()

#     cache_config = types.CreateCachedContentConfig(
#         contents=[input_data],
#         ttl=ttl,
#     )
#     if sys_prompt:
#         cache_config = cache_config.model_copy(
#             update={"system_instruction": sys_prompt}
#         )
#         print(f"\n(!) cache created {sys_prompt[:50]}\n")
#     else:
#         raise ValueError("System prompt is required")

#     cache = client.caches.create(model=model_id, config=cache_config)
#     return cache.name if cache.name else ""


def summarize_usage(usage_metadata, cached_token_price: float = 0.00001) -> dict:
    """
    Generate a detailed summary dict highlighting cached token usage.

    Accepts a ``GenerateContentResponseUsageMetadata`` Pydantic object
    (attribute access) rather than a plain dict.
    """

    def _get(attr: str, default: int = 0) -> int:
        return getattr(usage_metadata, attr, None) or default

    total_tokens = _get("total_token_count")
    prompt_tokens = _get("prompt_token_count")
    cached_tokens = _get("cached_content_token_count")

    # Calculate percentage against input (prompt) tokens, not total tokens
    cached_pct = (cached_tokens / prompt_tokens * 100) if prompt_tokens > 0 else 0

    # Determine dynamic recommendation
    if cached_tokens > 0:
        recommendation = "Cache hit detected. Monitor TTL to maximize savings."
    else:
        recommendation = (
            "No cache hit. Consider context caching if this prompt is reused."
        )

    summary = {
        "total_request_tokens": total_tokens,
        "cached_tokens_used": cached_tokens,
        "cache_hit_percentage": f"{cached_pct:.1f}%",
        "cache_efficiency_status": (
            "HIGH" if cached_pct > 50 else "MEDIUM" if cached_pct > 20 else "LOW"
        ),
        "breakdown": {
            "input_tokens": {
                "total_prompt": prompt_tokens,
                "cached_portion": cached_tokens,
                "tool_use_prompt": _get("tool_use_prompt_token_count"),
                "thoughts": _get("thoughts_token_count"),
            },
            "output_tokens": {
                "candidates": _get("candidates_token_count"),
            },
        },
        "cache_impact": {
            "tokens_saved": cached_tokens,
            # Parameterized the price to avoid brittle hardcoding
            # "cost_savings_estimate": f"~${cached_tokens * cached_token_price:.4f}",
            "recommendation": recommendation,
        },
    }

    return summary


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
def call_llm(
    model_id: str,
    config: types.GenerateContentConfig | None = None,
    sys_prompt: str | None = None,
    user_prompt: str | None = None,
    input_data: Any | None = None,
    cache_name: str | None = None,
    output_summary: bool = settings.output_summary,
) -> str:
    """
    Call a Google Gemini LLM model and return the response text.

    **Without caching** (default):
        ``input_data`` is appended to ``contents`` alongside ``user_prompt``,
        and ``sys_prompt`` is injected into ``GenerateContentConfig`` as the
        system instruction.

    **With an existing cache**:
        Pass the name returned by :func:`create_llm_cache` as ``cache_name``.
        The cached context (and system prompt, if it was baked in) is reused
        server-side — only ``user_prompt`` needs to be sent.  Do **not** pass
        ``sys_prompt`` or ``input_data`` when using a cache that already
        contains them.

    Args:
        model_id:     The model identifier, e.g. ``"gemini-2.5-flash"``.
                      Must match the model used when the cache was created.
        config:       Optional :class:`types.GenerateContentConfig`
                      (temperature, max output tokens, etc.).  The
                      ``cached_content`` field is injected automatically when
                      ``cache_name`` is provided.
        sys_prompt:   Optional system instruction.  Ignored (with a warning)
                      if ``cache_name`` is provided, since the system prompt
                      should already be baked into the cache.
        user_prompt:  The user's message, sent as regular (non-cached) content.
        input_data:   Extra data appended to ``contents`` after ``user_prompt``
                      on the non-cached path.  Ignored when ``cache_name`` is
                      provided.
        cache_name:   Opaque cache name returned by :func:`create_llm_cache`.
                      When supplied the cached context is referenced
                      server-side and only ``user_prompt`` is transmitted.

    Returns:
        The model's response text as a plain string.
    """
    import warnings

    client = _get_client()

    if cache_name:
        # ------------------------------------------------------------------
        # Cached path — only user_prompt travels over the wire.
        # ------------------------------------------------------------------
        if sys_prompt:
            warnings.warn(
                "sys_prompt is ignored when cache_name is provided.  "
                "Bake the system prompt into the cache via create_llm_cache().",
                stacklevel=2,
            )
        if input_data is not None:
            warnings.warn(
                "input_data is ignored when cache_name is provided.  "
                "The cached context is used instead.",
                stacklevel=2,
            )

        if config is None:
            config = types.GenerateContentConfig(cached_content=cache_name)
        else:
            config = config.model_copy(update={"cached_content": cache_name})

        contents: list[Any] = [user_prompt] if user_prompt else [""]

    else:
        # ------------------------------------------------------------------
        # Standard path — assemble contents and config from scratch.
        # ------------------------------------------------------------------
        contents = []
        if user_prompt:
            contents.append(user_prompt)
        if input_data is not None:
            contents.append(input_data)

        if sys_prompt:
            if config is None:
                config = types.GenerateContentConfig(
                    system_instruction=sys_prompt,
                )
            else:
                config = config.model_copy(update={"system_instruction": sys_prompt})

    response = client.models.generate_content(
        model=model_id,
        contents=contents if contents else [""],
        config=config,
    )

    response_text = response.text if response.text else ""
    if output_summary:
        print(summarize_usage(response.usage_metadata))
    return response_text


if __name__ == "__main__":
    from rec2note_cli.config import get_settings

    settings = get_settings()

    # --- without caching ---------------------------------------------------
    # result = call_llm(
    #     model_id=settings.google_gemini_model_id,
    #     sys_prompt="You are a helpful assistant.",
    #     user_prompt="Explain how AI works in a few words.",
    # )
    # print("Without cache:", result)

    # --- with explicit caching ---------------------------------------------
    # Step 1: create the cache once (e.g. at the start of a session).
    try:
        large_context = read_file("recordings/lecture1/Lecture5_020526.srt")
        cache_name = create_transcript_cache(
            model_id=settings.google_gemini_model_id,
            transcript=large_context,
            ttl=settings.google_gemini_cache_ttl,
        )
        print("Cache created:", cache_name)
    except Exception as e:
        print(f"Error creating cache: {e}")

    # Step 2: reuse the same cache name across multiple calls.
    for question in ["Summarise the document.", "What is the main topic?"]:
        answer = call_llm(
            model_id=settings.google_gemini_model_id,
            user_prompt=question,
            cache_name=cache_name,
            output_summary=True,
        )
        print(f"Q: {question}\nA: {answer}\n")
