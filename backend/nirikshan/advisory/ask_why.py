"""'Ask Why' explanation assistant for regulatory scrutiny findings.

Given a finding or rule result, answers officer questions using ONLY retrieved
facts, rule text, and evidence as context. The answer must include citations
to rule_id/clause/page and refuse when the context has no answer.

Trust Ladder: MODEL (Rank 10 — Advisory Only).
"""

from __future__ import annotations

import abc
import logging
import re
import urllib.parse
from typing import Any

from pydantic import BaseModel, Field

from nirikshan.config import settings
from nirikshan.core.rule_schema import Rule
from nirikshan.schemas.finding import Finding
from nirikshan.trust.ladder import EvidenceItem, TrustLevel

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


class AskWhyCitation(BaseModel):
    """Citation back to the regulatory clause and page."""

    rule_id: str
    clause: str
    page: int | str


class AskWhyResponse(BaseModel):
    """Structured response from the Ask Why assistant."""

    question: str
    answer: str
    is_refusal: bool = Field(..., description="True if question was out-of-context and refused")
    citations: list[AskWhyCitation] = Field(default_factory=list)
    trust_level: TrustLevel = Field(default=TrustLevel.MODEL, description="Always MODEL advisory")
    context_keys: list[str] = Field(default_factory=list)


class AskWhyContext(BaseModel):
    """Context bundle encapsulating all authoritative facts, rule text, and evidence."""

    finding: Finding | None = None
    rule: Rule | dict[str, Any] | None = None
    facts: dict[str, Any] = Field(default_factory=dict)
    evidence_items: list[EvidenceItem] = Field(default_factory=list)

    def extract_metadata(self) -> dict[str, Any]:
        """Extract key metadata and identifiers for grounding validation."""
        rule_id = "UNKNOWN-RULE"
        rule_title = "Unknown Rule"
        clause = "Clause N/A"
        page: int | str = "N/A"

        if isinstance(self.rule, Rule):
            rule_id = self.rule.rule_id
            rule_title = self.rule.title
            clause = self.rule.citation.clause
            page = self.rule.citation.page
        elif isinstance(self.rule, dict):
            rule_id = str(self.rule.get("rule_id", self.rule.get("id", "UNKNOWN-RULE")))
            rule_title = str(self.rule.get("title", self.rule.get("name", "Unknown Rule")))
            citation_dict = self.rule.get("citation", {})
            clause = citation_dict.get("clause", "Clause N/A")
            page = citation_dict.get("page", "N/A")
        elif self.finding:
            rule_id = self.finding.rule_id
            rule_title = self.finding.rule_name
            clause = self.finding.handbook_citation.clause
            page = self.finding.handbook_citation.page

        # Combine evidence items from finding and context
        all_evidence = list(self.evidence_items)
        if self.finding:
            all_evidence.extend(self.finding.evidence_list)

        return {
            "rule_id": rule_id,
            "rule_title": rule_title,
            "clause": clause,
            "page": page,
            "facts": dict(self.facts),
            "evidence": all_evidence,
            "finding": self.finding,
        }

    def format_context_string(self) -> str:
        """Render context into a clean text block."""
        meta = self.extract_metadata()
        lines: list[str] = []

        lines.append("=== SECTION 1: REGULATORY RULE DEFINITION ===")
        lines.append(f"Rule ID: {meta['rule_id']}")
        lines.append(f"Rule Title: {meta['rule_title']}")
        lines.append(f"Handbook Citation: {meta['clause']}, Page {meta['page']}")

        if isinstance(self.rule, Rule) and self.rule.logic:
            lines.append(f"Logic Expression: {self.rule.logic}")
            lines.append(f"Rule Parameters: {self.rule.parameters}")
        elif isinstance(self.rule, dict) and "logic" in self.rule:
            lines.append(f"Logic Expression: {self.rule['logic']}")

        if meta["finding"]:
            f = meta["finding"]
            lines.append("\n=== SECTION 2: VERIFICATION FINDING ===")
            lines.append(f"Finding ID: {f.finding_id}")
            lines.append(f"Status: {f.status.value}")
            lines.append(f"Summary: {f.summary}")
            lines.append(f"Details: {f.details}")
            if f.advisory_notes:
                lines.append(f"Advisory Notes: {'; '.join(f.advisory_notes)}")

        lines.append("\n=== SECTION 3: RETRIEVED APPLICATION FACTS ===")
        if meta["facts"]:
            for k, v in meta["facts"].items():
                lines.append(f"- {k}: {v}")
        else:
            lines.append("- (No additional application facts provided)")

        lines.append("\n=== SECTION 4: ATTESTED EVIDENCE ITEMS ===")
        if meta["evidence"]:
            for ev in meta["evidence"]:
                lines.append(
                    f"- [{ev.evidence_id}] Source: {ev.source_type} ({ev.source_document_name}), "
                    f"Trust: {ev.effective_trust_level().value}, Method: {ev.verification_method}, "
                    f"Desc: {ev.description}"
                )
        else:
            lines.append("- (No documentary evidence items attached)")

        return "\n".join(lines)


class AskWhyLLM(abc.ABC):
    """Abstract interface for Ask Why LLM backends."""

    @abc.abstractmethod
    def generate_response(self, question: str, context: AskWhyContext) -> str:
        """Generate response given officer question and context."""


class StubAskWhyLLM(AskWhyLLM):
    """Deterministic stub LLM for testing.

    Refuses out-of-context questions and answers in-context questions with citations.
    """

    # Unrelated domains that immediately trigger refusal
    OUT_OF_CONTEXT_KEYWORDS = {
        "weather", "temperature", "cricket", "football", "president",
        "prime minister", "capital", "movie", "recipe", "bitcoin",
        "stock price", "unrelated", "france", "paris", "tokyo",
        "tuition fee", "sports ground", "cafeteria menu", "who is",
    }

    def generate_response(self, question: str, context: AskWhyContext) -> str:
        q_lower = question.lower()
        meta = context.extract_metadata()
        rule_id = meta["rule_id"]
        clause = meta["clause"]
        page = meta["page"]
        facts = meta["facts"]

        # 1. Check for immediate out-of-context keywords
        for kw in self.OUT_OF_CONTEXT_KEYWORDS:
            if kw in q_lower:
                return (
                    f"REFUSAL: The provided scrutiny context does not contain information about '{kw}'. "
                    "I can only answer questions directly grounded in the provided rule text, findings, and evidence."
                )

        # 2. Check keyword overlap with context concepts
        context_terms = {
            rule_id.lower(),
            meta["rule_title"].lower(),
            str(clause).lower(),
            "rule", "clause", "page", "why", "status", "finding", "evidence", "fail", "pass",
        }
        for k in facts:
            context_terms.add(k.lower())
            context_terms.update(k.lower().split("_"))

        # Words in query
        q_words = set(re.findall(r"\b[a-z]{3,}\b", q_lower))
        overlap = q_words.intersection(context_terms)

        if not overlap:
            return (
                "REFUSAL: The provided scrutiny context does not contain sufficient facts to answer this question. "
                "I am restricted to answering questions strictly grounded in the retrieved facts and rules."
            )

        # 3. In-context synthesis with mandatory citations
        finding = meta["finding"]
        if "why" in q_lower or "reason" in q_lower or "fail" in q_lower or "status" in q_lower:
            if finding:
                ans = (
                    f"The scrutiny finding status is {finding.status.value}. "
                    f"{finding.summary} {finding.details} "
                    f"Citation: [Rule: {rule_id}, Clause: {clause}, Page: {page}]."
                )
            else:
                ans = (
                    f"Evaluation for rule {rule_id} ({meta['rule_title']}) is governed by {clause}. "
                    f"Citation: [Rule: {rule_id}, Clause: {clause}, Page: {page}]."
                )
            return ans

        # Check if asking about specific facts (e.g. land area, fire noc, workstations)
        for k, v in facts.items():
            if k.replace("_", " ") in q_lower or k in q_lower:
                return (
                    f"According to the retrieved applicant facts, '{k}' is recorded as {v}. "
                    f"This fact was evaluated under {rule_id}. "
                    f"Citation: [Rule: {rule_id}, Clause: {clause}, Page: {page}]."
                )

        # Fallback in-context response with citation
        return (
            f"Based on the regulatory text for {meta['rule_title']} ({rule_id}), "
            f"the requirement is governed under {clause}. "
            f"Citation: [Rule: {rule_id}, Clause: {clause}, Page: {page}]."
        )


class OllamaAskWhyLLM(AskWhyLLM):
    """Ollama-backed Ask Why LLM (default model: qwen3:4b)."""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.model = model or getattr(settings, "ollama_model", "qwen3:4b")
        self.base_url = str(base_url or getattr(settings, "ollama_base_url", "http://localhost:11434")).rstrip("/")
        self.timeout = timeout

    def generate_response(self, question: str, context: AskWhyContext) -> str:
        import httpx

        system_prompt = (
            "You are the Nirikshan Regulatory Scrutiny Assistant for AICTE scrutiny officers. "
            "STRICT RULES:\n"
            "1. Answer using ONLY the facts, rule text, and evidence provided in the context below.\n"
            "2. Never extrapolate, hallucinate, or bring in external knowledge.\n"
            "3. Every assertion must cite the exact rule: [Rule: <rule_id>, Clause: <clause>, Page: <page>].\n"
            "4. If the question cannot be answered completely and strictly from the context, you MUST REFUSE with: "
            "'REFUSAL: The provided scrutiny context does not contain sufficient information to answer this question.'"
        )

        user_content = f"CONTEXT:\n{context.format_context_string()}\n\nOFFICER QUESTION: {question}"

        payload = {
            "model": self.model,
            "prompt": user_content,
            "system": system_prompt,
            "stream": False,
        }

        _validate_offline_url(self.base_url)

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f"{self.base_url}/api/generate", json=payload)
                resp.raise_for_status()
                data = resp.json()
                return str(data.get("response", "")).strip()
        except Exception as exc:
            logger.error("Ollama Ask Why error: %s", exc)
            return f"REFUSAL: Cannot reach local LLM backend at {self.base_url}: {exc}"


class AskWhyAssistant:
    """Officer 'Ask Why' Assistant orchestrator."""

    def __init__(self, backend: AskWhyLLM | None = None) -> None:
        self.backend = backend or StubAskWhyLLM()

    @staticmethod
    def _parse_citations(raw_answer: str, default_meta: dict[str, Any]) -> list[AskWhyCitation]:
        """Extract [Rule: ..., Clause: ..., Page: ...] citations from answer text."""
        citations: list[AskWhyCitation] = []
        matches = re.findall(
            r"\[Rule:\s*([^,\]]+),\s*Clause:\s*([^,\]]+),\s*Page:\s*([^,\]]+)\]",
            raw_answer,
            re.IGNORECASE,
        )
        for m in matches:
            rule_id = m[0].strip()
            clause = m[1].strip()
            page_raw = m[2].strip()
            page: int | str
            try:
                page = int(page_raw)
            except ValueError:
                page = page_raw
            citations.append(AskWhyCitation(rule_id=rule_id, clause=clause, page=page))

        # If none parsed but answer is not a refusal, attach default citation
        if not citations and not raw_answer.upper().startswith("REFUSAL"):
            citations.append(
                AskWhyCitation(
                    rule_id=default_meta["rule_id"],
                    clause=str(default_meta["clause"]),
                    page=default_meta["page"],
                )
            )
        return citations

    def ask(self, question: str, context: AskWhyContext) -> AskWhyResponse:
        """Process an officer question against the grounded context."""
        meta = context.extract_metadata()
        raw_response = self.backend.generate_response(question, context).strip()

        is_refusal = (
            raw_response.upper().startswith("REFUSAL:")
            or "REFUSAL:" in raw_response.upper()
            or "does not contain" in raw_response.lower()
        )

        citations = [] if is_refusal else self._parse_citations(raw_response, meta)

        context_keys = list(meta["facts"].keys())
        if meta["finding"]:
            context_keys.append(f"finding:{meta['finding'].finding_id}")

        return AskWhyResponse(
            question=question,
            answer=raw_response,
            is_refusal=is_refusal,
            citations=citations,
            trust_level=TrustLevel.MODEL,
            context_keys=context_keys,
        )


ask_why_assistant = AskWhyAssistant()
