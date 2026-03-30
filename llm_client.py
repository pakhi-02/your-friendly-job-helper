"""Local LLM client (Ollama)."""
from __future__ import annotations

import requests

from config import (
    LLM_PROVIDER,
    LLM_TEMPERATURE,
    LLM_TIMEOUT_SECONDS,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    USE_LLM,
)


class LLMUnavailableError(RuntimeError):
    """Raised when local LLM cannot be reached."""


class LocalLLMClient:
    """Simple wrapper around local LLM providers."""

    def __init__(self) -> None:
        self.enabled = USE_LLM
        self.provider = LLM_PROVIDER.strip().lower()
        self.model = OLLAMA_MODEL
        self.base_url = OLLAMA_BASE_URL.rstrip("/")
        self.timeout_seconds = LLM_TIMEOUT_SECONDS
        self.temperature = LLM_TEMPERATURE

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate a completion from the configured LLM."""
        if not self.enabled:
            raise LLMUnavailableError("LLM usage is disabled (USE_LLM=false).")
        if self.provider != "ollama":
            raise LLMUnavailableError(
                f"Unsupported LLM provider: {self.provider}. Use LLM_PROVIDER=ollama."
            )
        return self._generate_ollama(prompt=prompt, system_prompt=system_prompt)

    def check_health(self) -> tuple[bool, str]:
        """Return whether the configured LLM endpoint is reachable."""
        if not self.enabled:
            return False, "disabled"
        if self.provider != "ollama":
            return False, f"unsupported_provider:{self.provider}"
        try:
            response = requests.get(
                f"{self.base_url}/api/tags", timeout=self.timeout_seconds
            )
            if response.status_code != 200:
                return False, f"http_{response.status_code}"
            return True, "ok"
        except requests.RequestException as exc:
            return False, str(exc)

    def _generate_ollama(self, prompt: str, system_prompt: str = "") -> str:
        """Call Ollama /api/generate with non-streaming output."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise LLMUnavailableError(f"Could not connect to Ollama: {exc}") from exc

        if response.status_code != 200:
            raise LLMUnavailableError(
                f"Ollama request failed with status {response.status_code}: {response.text[:300]}"
            )

        data = response.json()
        text = (data.get("response") or "").strip()
        if not text:
            raise LLMUnavailableError("Ollama returned an empty response.")
        return text
