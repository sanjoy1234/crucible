"""BaseAgent — unified async model interface for Ollama and Anthropic."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
import httpx


@dataclass
class AgentMessage:
    role: str  # "user" | "assistant"
    content: str


@dataclass
class ModelResponse:
    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @property
    def estimated_cost_usd(self) -> float:
        """Rough estimate; 0.0 for local Ollama runs."""
        if self.model.startswith("ollama/") or "/" not in self.model:
            return 0.0
        # Haiku pricing: ~$0.25/MTok input, $1.25/MTok output
        return (self.prompt_tokens * 0.25 + self.completion_tokens * 1.25) / 1_000_000


class BaseAgent:
    """
    Unified async LLM interface.

    Supported providers:
      ollama      — local Ollama server, zero cost, air-gapped (default)
      anthropic   — Anthropic Claude API (set ANTHROPIC_API_KEY)
      openrouter  — OpenRouter.ai API (set OPENROUTER_API_KEY)
                    Any model including free tier: deepseek/deepseek-chat-v3-0324:free
      huggingface — HuggingFace Inference API (set HF_TOKEN)
      openai_compat — generic OpenAI-compatible endpoint (set OPENAI_COMPAT_API_KEY
                      and OPENAI_COMPAT_BASE_URL); covers vLLM, Together AI, etc.

    Provider resolution order (when provider arg is None):
      1. OPENROUTER_API_KEY → openrouter
      2. ANTHROPIC_API_KEY  → anthropic
      3. HF_TOKEN           → huggingface
      4. fallback           → ollama
    """

    OPENROUTER_BASE = "https://openrouter.ai/api/v1"
    HUGGINGFACE_BASE = "https://api-inference.huggingface.co/v1"

    def __init__(
        self,
        system_prompt: str,
        model: str | None = None,
        provider: str | None = None,
        ollama_endpoint: str = "http://localhost:11434",
        openai_compat_endpoint: str | None = None,
        temperature: float = 0.7,
    ):
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.ollama_endpoint = ollama_endpoint.rstrip("/")
        self._openai_compat_endpoint = openai_compat_endpoint

        if provider:
            self._provider = provider
        elif os.environ.get("OPENROUTER_API_KEY"):
            self._provider = "openrouter"
        elif os.environ.get("ANTHROPIC_API_KEY"):
            self._provider = "anthropic"
        elif os.environ.get("HF_TOKEN"):
            self._provider = "huggingface"
        else:
            self._provider = "ollama"

        if model:
            self._model = model
        elif self._provider == "anthropic":
            self._model = "claude-haiku-4-5-20251001"
        elif self._provider == "openrouter":
            self._model = os.environ.get(
                "OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free"
            )
        elif self._provider == "huggingface":
            self._model = os.environ.get(
                "HF_MODEL", "meta-llama/Llama-3.1-70B-Instruct"
            )
        elif self._provider == "openai_compat":
            self._model = os.environ.get("OPENAI_COMPAT_MODEL", "llama3.1:8b")
        else:
            self._model = "llama3.1:8b"

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def model(self) -> str:
        return self._model

    async def complete(self, messages: list[AgentMessage]) -> ModelResponse:
        """Send messages and return a single completion."""
        if self._provider == "anthropic":
            return await self._anthropic_complete(messages)
        if self._provider in ("openrouter", "huggingface", "openai_compat"):
            return await self._openai_compat_complete(messages)
        return await self._ollama_complete(messages)

    async def _ollama_complete(self, messages: list[AgentMessage]) -> ModelResponse:
        prompt = self._build_ollama_prompt(messages)
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(f"{self.ollama_endpoint}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
        return ModelResponse(
            content=data["response"].strip(),
            model=f"ollama/{self._model}",
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
        )

    async def _anthropic_complete(self, messages: list[AgentMessage]) -> ModelResponse:
        import anthropic

        client = anthropic.AsyncAnthropic()
        api_messages = [{"role": m.role, "content": m.content} for m in messages]
        response = await client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=self.system_prompt,
            messages=api_messages,
        )
        content = response.content[0].text if response.content else ""
        return ModelResponse(
            content=content.strip(),
            model=self._model,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
        )

    async def _openai_compat_complete(self, messages: list[AgentMessage]) -> ModelResponse:
        """
        OpenAI-compatible chat completions endpoint.

        Covers: OpenRouter, HuggingFace Inference API, Together AI, vLLM, Groq, etc.
        """
        if self._provider == "openrouter":
            base_url = self.OPENROUTER_BASE
            api_key = os.environ.get("OPENROUTER_API_KEY", "")
            extra_headers = {
                "HTTP-Referer": "https://github.com/sanjoy1234/crucible",
                "X-Title": "CRUCIBLE Adversarial Co-Generation Engine",
            }
        elif self._provider == "huggingface":
            base_url = self.HUGGINGFACE_BASE
            api_key = os.environ.get("HF_TOKEN", "")
            extra_headers = {}
        else:  # openai_compat
            base_url = (
                self._openai_compat_endpoint
                or os.environ.get("OPENAI_COMPAT_BASE_URL", "http://localhost:8000/v1")
            ).rstrip("/")
            api_key = os.environ.get("OPENAI_COMPAT_API_KEY", "no-key")
            extra_headers = {}

        api_messages = [{"role": "system", "content": self.system_prompt}]
        api_messages += [{"role": m.role, "content": m.content} for m in messages]

        payload = {
            "model": self._model,
            "messages": api_messages,
            "temperature": self.temperature,
            "max_tokens": 4096,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            **extra_headers,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            for attempt in range(4):
                resp = await client.post(
                    f"{base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                if resp.status_code not in (429, 503) or attempt == 3:
                    break
                retry_after = float(resp.headers.get("retry-after", 2 ** (attempt + 1)))
                await asyncio.sleep(min(retry_after, 30))
            resp.raise_for_status()
            data = resp.json()

        if "error" in data and "choices" not in data:
            raise httpx.HTTPStatusError(
                message=data["error"].get("message", str(data["error"])),
                request=resp.request,
                response=resp,
            )
        choice = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return ModelResponse(
            content=choice.strip(),
            model=self._model,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
        )

    def _build_ollama_prompt(self, messages: list[AgentMessage]) -> str:
        parts = [f"System: {self.system_prompt}\n"]
        for m in messages:
            parts.append(f"{m.role.capitalize()}: {m.content}")
        parts.append("Assistant:")
        return "\n\n".join(parts)
