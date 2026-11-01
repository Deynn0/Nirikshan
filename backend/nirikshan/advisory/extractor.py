"""Field extractor service with Ollama and stub backends.

Advisory ML Layer (Trust Ladder: Model).
"""

from __future__ import annotations

import abc
import json
import logging
import re
import urllib.parse
from typing import Any

import httpx
from pydantic import BaseModel

from nirikshan.config import settings

logger = logging.getLogger(__name__)


def _validate_offline_url(url: str) -> None:
    """Ensure zero outbound network requests under offline air-gapped constitution."""
    if getattr(settings, "allow_external_network", False):
        return
    parsed = urllib.parse.urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if hostname not in ("localhost", "127.0.0.1", "::1", "0.0.0.0") and not hostname.startswith("127."):
        raise PermissionError(
            f"Airgap Violation: Outbound network call to external host '{hostname}' "
            "is strictly blocked by Nirikshan offline policy."
        )


class ExtractionError(Exception):
    """Base exception for field extraction errors."""


class OllamaConnectionError(ExtractionError):
    """Raised when Ollama server is unreachable."""


class FieldExtractor(abc.ABC):
    """Abstract base extractor interface for extracting structured fields from text."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or getattr(settings, "ollama_model", "qwen3:4b")

    def build_schema_prompt(
        self,
        schema: dict[str, Any] | type[BaseModel] | None,
        system_instructions: str | None = None,
    ) -> str:
        """Construct the prompt instructions enforcing a JSON schema."""
        if schema is None:
            schema_str = "Extract any key regulatory fields into a JSON object key-value mapping."
        elif isinstance(schema, type) and issubclass(schema, BaseModel):
            schema_str = json.dumps(schema.model_json_schema(), indent=2)
        elif isinstance(schema, dict):
            schema_str = json.dumps(schema, indent=2)
        else:
            schema_str = str(schema)

        default_instructions = (
            "You are a regulatory document parser for AICTE compliance scrutiny. "
            "Extract structured fields from the provided document text into a single JSON object. "
            "You must strictly adhere to the following JSON Schema:\n"
            f"{schema_str}\n\n"
            "CRITICAL RULES:\n"
            "1. Output ONLY valid JSON matching the schema.\n"
            "2. Do NOT hallucinate values. Only extract facts explicitly stated in the text.\n"
            "3. If a field is not found in the text, omit it or set to null.\n"
            "4. Return no introductory or concluding text, only raw JSON."
        )
        return system_instructions or default_instructions

    @abc.abstractmethod
    def extract(
        self,
        text: str,
        schema: dict[str, Any] | type[BaseModel] | None = None,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Extract structured fields from document text."""

    @abc.abstractmethod
    async def extract_async(
        self,
        text: str,
        schema: dict[str, Any] | type[BaseModel] | None = None,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Asynchronously extract structured fields from document text."""

    @staticmethod
    def clean_json_response(raw_text: str) -> dict[str, Any]:
        """Strip markdown code fence blocks and parse raw JSON."""
        cleaned = raw_text.strip()
        # Remove markdown code block if present
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            cleaned = cleaned.strip()

        # Find first '{' and last '}'
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]

        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
            return {"data": parsed}
        except json.JSONDecodeError as exc:
            logger.error("Failed to decode JSON from model output: %s (Raw: %r)", exc, raw_text)
            raise ExtractionError(f"Model output is not valid JSON: {exc}") from exc


class OllamaFieldExtractor(FieldExtractor):
    """Field extractor backed by an Ollama instance (default model: qwen3:4b)."""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        super().__init__(model=model)
        self.base_url = str(base_url or getattr(settings, "ollama_base_url", "http://localhost:11434")).rstrip("/")
        self.timeout = timeout

    def extract(
        self,
        text: str,
        schema: dict[str, Any] | type[BaseModel] | None = None,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Synchronously query Ollama API."""
        instructions = self.build_schema_prompt(schema, system_prompt)
        prompt = f"DOCUMENT TEXT:\n{text}\n\nEXTRACTED JSON:"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": instructions,
            "format": "json",
            "stream": False,
        }

        _validate_offline_url(self.base_url)

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f"{self.base_url}/api/generate", json=payload)
                resp.raise_for_status()
                data = resp.json()
                response_text = data.get("response", "")
                return self.clean_json_response(response_text)
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            msg = f"Cannot connect to Ollama at {self.base_url}: {exc}"
            logger.error(msg)
            raise OllamaConnectionError(msg) from exc
        except Exception as exc:
            msg = f"Ollama extraction request failed: {exc}"
            logger.error(msg)
            raise ExtractionError(msg) from exc

    async def extract_async(
        self,
        text: str,
        schema: dict[str, Any] | type[BaseModel] | None = None,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Asynchronously query Ollama API."""
        instructions = self.build_schema_prompt(schema, system_prompt)
        prompt = f"DOCUMENT TEXT:\n{text}\n\nEXTRACTED JSON:"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": instructions,
            "format": "json",
            "stream": False,
        }

        _validate_offline_url(self.base_url)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.base_url}/api/generate", json=payload)
                resp.raise_for_status()
                data = resp.json()
                response_text = data.get("response", "")
                return self.clean_json_response(response_text)
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            msg = f"Cannot connect to Ollama at {self.base_url}: {exc}"
            logger.error(msg)
            raise OllamaConnectionError(msg) from exc
        except Exception as exc:
            msg = f"Ollama extraction request failed: {exc}"
            logger.error(msg)
            raise ExtractionError(msg) from exc


class StubFieldExtractor(FieldExtractor):
    """Stub extractor for deterministic unit tests and offline testing."""

    def __init__(
        self,
        fixed_output: dict[str, Any] | None = None,
        model: str = "stub-model",
    ) -> None:
        super().__init__(model=model)
        self.fixed_output = fixed_output

    def extract(
        self,
        text: str,
        schema: dict[str, Any] | type[BaseModel] | None = None,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        if self.fixed_output is not None:
            return dict(self.fixed_output)

        # Fallback simple heuristic regex extractor if no fixed output provided
        extracted: dict[str, Any] = {}
        text_lower = text.lower()

        # Land area
        m_land = re.search(r"(\d+(?:\.\d+)?)\s*(?:acres?|acre)", text_lower)
        if m_land:
            extracted["land_area_acres"] = float(m_land.group(1))

        # Survey no
        m_surv = re.search(r"(?:survey|sy)(?:\.?\s*no\.?)?\s*[:#\-]?\s*([0-9A-Za-z\/\-]+)", text_lower)
        if m_surv:
            extracted["survey_no"] = m_surv.group(1).upper()

        # Fire NOC date
        m_date = re.search(r"valid\s+(?:until|to|upto)\s+([0-9]{4}-[0-9]{2}-[0-9]{2})", text_lower)
        if m_date:
            extracted["fire_noc_expiry_date"] = m_date.group(1)

        return extracted

    async def extract_async(
        self,
        text: str,
        schema: dict[str, Any] | type[BaseModel] | None = None,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        return self.extract(text=text, schema=schema, system_prompt=system_prompt)
