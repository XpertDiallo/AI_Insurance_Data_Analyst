from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from insurance_ai.core.config import settings


@dataclass
class LLMResponse:
    text: str
    model: str
    attempts: int
    fallback_used: bool
    latency_seconds: float


class GeminiModelManager:
    """Central Gemini gateway with retry + model fallback.

    Import of google-genai is lazy so deterministic features remain usable
    even when the SDK/API is unavailable.
    """

    def __init__(
        self,
        api_key: str | None = None,
        models: tuple[str, ...] | list[str] | None = None,
        max_retries: int | None = None,
        timeout_seconds: int | None = None,
        client: Any = None,
    ):
        self.api_key = api_key if api_key is not None else settings.google_api_key
        self.models = tuple(models or settings.gemini_models)
        self.max_retries = settings.gemini_max_retries if max_retries is None else max_retries
        self.timeout_seconds = settings.gemini_timeout_seconds if timeout_seconds is None else timeout_seconds
        self._client = client

    @property
    def enabled(self) -> bool:
        return bool(self.api_key or self._client)

    def _client_or_create(self):
        if self._client is not None:
            return self._client
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY non configurée.")
        try:
            from google import genai  # type: ignore
            from google.genai import types  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("Le package google-genai n'est pas installé.") from exc
        self._client = genai.Client(
            api_key=self.api_key,
            http_options=types.HttpOptions(timeout=self.timeout_seconds * 1000),
        )
        return self._client

    def generate(self, prompt: str, *, json_mode: bool = False) -> LLMResponse:
        client = self._client_or_create()
        start = time.perf_counter()
        total_attempts = 0
        errors: list[str] = []

        for model_index, model in enumerate(self.models):
            for attempt in range(self.max_retries + 1):
                total_attempts += 1
                try:
                    kwargs: dict[str, Any] = {"model": model, "contents": prompt}
                    if json_mode:
                        try:
                            from google.genai import types  # type: ignore
                            kwargs["config"] = types.GenerateContentConfig(
                                response_mime_type="application/json",
                                temperature=0.1,
                            )
                        except Exception:
                            pass
                    response = client.models.generate_content(**kwargs)
                    text = getattr(response, "text", None) or ""
                    return LLMResponse(
                        text=text,
                        model=model,
                        attempts=total_attempts,
                        fallback_used=model_index > 0,
                        latency_seconds=round(time.perf_counter() - start, 3),
                    )
                except Exception as exc:
                    errors.append(f"{model}: {type(exc).__name__}: {exc}")
                    if attempt < self.max_retries:
                        time.sleep(min(1.5 * (2**attempt), 8.0))
        raise RuntimeError("Tous les modèles Gemini ont échoué. " + " | ".join(errors[-4:]))

    def generate_json(self, prompt: str) -> tuple[dict[str, Any], LLMResponse]:
        response = self.generate(prompt, json_mode=True)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Réponse LLM non JSON: {text[:300]}") from exc
        if not isinstance(payload, dict):
            raise ValueError("Le plan LLM doit être un objet JSON.")
        return payload, response
