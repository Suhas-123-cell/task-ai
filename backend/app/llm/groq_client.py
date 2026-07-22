"""
Thin wrapper around the Groq chat completions API.

Kept as a single narrow module so the rest of the codebase (question
generation, answer evaluation, report synthesis) depends on one function
signature rather than the Groq SDK directly -- swapping providers later
(OpenAI, Gemini, a local Ollama server) means changing this file only.
"""
import json
import logging

from groq import Groq

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_client: Groq | None = None


class LLMUnavailableError(RuntimeError):
    """Raised when no LLM provider is configured or the call fails."""


def is_llm_configured() -> bool:
    return bool(settings.groq_api_key)


def _get_client() -> Groq:
    global _client
    if _client is None:
        if not settings.groq_api_key:
            raise LLMUnavailableError("GROQ_API_KEY is not set")
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def chat_json(system_prompt: str, user_prompt: str, *, temperature: float | None = None) -> dict:
    """
    Call the LLM expecting a single JSON object back. Raises LLMUnavailableError
    if no key is configured or the call/parse fails, so callers can fall back
    to deterministic logic rather than crashing the request.
    """
    client = _get_client()
    try:
        completion = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature if temperature is not None else settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            response_format={"type": "json_object"},
        )
        content = completion.choices[0].message.content
        return json.loads(content)
    except Exception as exc:  # noqa: BLE001 - any provider/parse failure should degrade gracefully
        logger.warning("Groq call failed, caller will use fallback logic: %s", exc)
        raise LLMUnavailableError(str(exc)) from exc
