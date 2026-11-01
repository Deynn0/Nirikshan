"""Grounded verification service for extracted fields.

Locates every extracted field value in the document's recognized text with
a bounding box (exact or normalized fuzzy match above a threshold).
Ungrounded values are discarded and logged as "hallucination_rejected".
Returns value + page + bbox + confidence.

Trust Ladder: MODEL (Advisory).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from rapidfuzz import fuzz

from nirikshan.trust.ladder import BoundingBox, EvidenceItem, TrustLevel

logger = logging.getLogger(__name__)


class RecognizedWord(BaseModel):
    """An atomic word recognized in document text with position."""

    text: str
    page: int = Field(..., ge=1)
    bbox: BoundingBox


class RecognizedPage(BaseModel):
    """A single page of recognized text and words."""

    page: int = Field(..., ge=1)
    words: list[RecognizedWord] = Field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(w.text for w in self.words)


class RecognizedDocument(BaseModel):
    """Complete document text structure with spatial token locations."""

    pages: list[RecognizedPage] = Field(default_factory=list)

    @classmethod
    def from_text_pages(
        cls, pages_text: list[str], default_page_height: float = 842.0, default_page_width: float = 595.0
    ) -> RecognizedDocument:
        """Construct synthetic/simulated spatial tokens from raw strings."""
        pages: list[RecognizedPage] = []
        for p_idx, text in enumerate(pages_text, start=1):
            words: list[RecognizedWord] = []
            lines = text.splitlines()
            y_cursor = 50.0
            line_height = 20.0
            for line in lines:
                tokens = line.split()
                x_cursor = 50.0
                for token in tokens:
                    word_width = max(len(token) * 7.0, 15.0)
                    words.append(
                        RecognizedWord(
                            text=token,
                            page=p_idx,
                            bbox=BoundingBox(
                                page=p_idx,
                                x=round(x_cursor, 2),
                                y=round(y_cursor, 2),
                                width=round(word_width, 2),
                                height=round(line_height, 2),
                            ),
                        )
                    )
                    x_cursor += word_width + 8.0
                y_cursor += line_height + 5.0
            pages.append(RecognizedPage(page=p_idx, words=words))
        return cls(pages=pages)

    @classmethod
    def from_pdf(cls, pdf_path: Path) -> RecognizedDocument:
        """Extract spatial word tokens directly from PDF using pdfplumber if available."""
        try:
            import pdfplumber

            pages: list[RecognizedPage] = []
            with pdfplumber.open(str(pdf_path)) as pdf:
                for idx, page in enumerate(pdf.pages, start=1):
                    raw_words = page.extract_words() or []
                    words = [
                        RecognizedWord(
                            text=w["text"],
                            page=idx,
                            bbox=BoundingBox(
                                page=idx,
                                x=float(w["x0"]),
                                y=float(w["top"]),
                                width=float(w["x1"] - w["x0"]),
                                height=float(w["bottom"] - w["top"]),
                            ),
                        )
                        for w in raw_words
                    ]
                    pages.append(RecognizedPage(page=idx, words=words))
            return cls(pages=pages)
        except Exception as exc:
            logger.warning("Could not use pdfplumber for word extraction: %s; falling back to pypdf", exc)
            # Fallback to PyPDF text splitting
            from pypdf import PdfReader

            reader = PdfReader(str(pdf_path))
            pages_text = [p.extract_text() or "" for p in reader.pages]
            return cls.from_text_pages(pages_text)


class GroundedField(BaseModel):
    """A field whose value was verified and located in the document."""

    field_name: str
    value: Any
    matched_text: str
    page: int
    bbox: BoundingBox
    confidence: float = Field(..., ge=0.0, le=1.0)
    match_type: str = Field(default="exact", description="'exact' or 'fuzzy'")
    status: str = Field(default="grounded")

    def to_evidence_item(
        self,
        source_document_id: str,
        source_document_name: str,
        source_type: str = "EXTRACTED_FIELD_ADVISORY",
    ) -> EvidenceItem:
        """Convert grounded field into an EvidenceItem at TrustLevel.MODEL."""
        return EvidenceItem(
            evidence_id=f"ev-grounded-{self.field_name}",
            trust_level=TrustLevel.MODEL,
            source_type=source_type,
            description=f"Grounded extraction of '{self.field_name}' = '{self.value}' on page {self.page} (confidence {self.confidence:.2f})",
            raw_value=self.value,
            source_document_id=source_document_id,
            source_document_name=source_document_name,
            page_number=self.page,
            bounding_box=self.bbox,
            is_self_attested=False,
            is_tampered=False,
            verification_method="GROUNDED_LLM_EXTRACTION",
        )


class GroundedResult(BaseModel):
    """Result of grounded field verification across an extracted dictionary."""

    grounded_fields: dict[str, GroundedField] = Field(default_factory=dict)
    rejected_fields: dict[str, Any] = Field(
        default_factory=dict,
        description="Fields whose values could not be grounded in document text (hallucination_rejected)",
    )
    rejection_reasons: dict[str, str] = Field(default_factory=dict)
    hallucination_log: list[str] = Field(default_factory=list)
    total_extracted: int = 0
    grounded_count: int = 0
    rejected_count: int = 0

    @property
    def is_fully_grounded(self) -> bool:
        return self.rejected_count == 0


class GroundedVerifier:
    """Verifies that extracted field values exist in recognized text and computes bounding boxes."""

    def __init__(self, fuzzy_threshold: float = 0.85) -> None:
        """fuzzy_threshold: float between 0.0 and 1.0 (default 0.85 = 85% match)."""
        self.fuzzy_threshold = fuzzy_threshold

    @staticmethod
    def _normalize_text(s: str) -> str:
        """Normalize punctuation and case for robust matching."""
        s = s.lower()
        s = re.sub(r"[\s\-_,\.;:/\(\)\[\]]+", " ", s)
        return s.strip()

    @staticmethod
    def _combine_bboxes(page: int, boxes: list[BoundingBox]) -> BoundingBox:
        """Calculate union bounding box over multiple boxes on the same page."""
        min_x = min(b.x for b in boxes)
        min_y = min(b.y for b in boxes)
        max_x = max(b.x + b.width for b in boxes)
        max_y = max(b.y + b.height for b in boxes)
        return BoundingBox(
            page=page,
            x=round(min_x, 2),
            y=round(min_y, 2),
            width=round(max_x - min_x, 2),
            height=round(max_y - min_y, 2),
        )

    def locate_value(
        self,
        value: Any,
        document: RecognizedDocument,
    ) -> tuple[BoundingBox, int, float, str, str] | None:
        """Attempt to locate a field value in the document.

        Returns (bbox, page, confidence, matched_text, match_type) or None if not grounded.
        """
        if value is None:
            return None

        val_str = str(value).strip()
        if not val_str:
            return None

        norm_val = self._normalize_text(val_str)
        val_tokens = norm_val.split()
        if not val_tokens:
            return None

        # 1. First Pass: Exact Substring Match in Word Sequences
        for page in document.pages:
            words = page.words
            n_words = len(words)
            n_tokens = len(val_tokens)

            # Check sliding window of word tokens matching val_tokens
            for i in range(n_words - n_tokens + 1):
                window_words = words[i : i + n_tokens]
                window_norm = self._normalize_text(" ".join(w.text for w in window_words))
                if window_norm == norm_val:
                    bbox = self._combine_bboxes(page.page, [w.bbox for w in window_words])
                    return bbox, page.page, 1.0, " ".join(w.text for w in window_words), "exact"

            # Check single word contains exact value (e.g. number in text)
            for w in words:
                w_norm = self._normalize_text(w.text)
                if norm_val == w_norm or (len(norm_val) >= 3 and norm_val in w_norm):
                    return w.bbox, page.page, 1.0, w.text, "exact"

        # 2. Second Pass: Normalized Fuzzy Match
        best_score = 0.0
        best_match: tuple[BoundingBox, int, float, str, str] | None = None
        target_len = len(val_tokens)

        for page in document.pages:
            words = page.words
            n_words = len(words)
            if n_words == 0:
                continue

            # Check sliding windows from len - 1 to len + 2
            min_w = max(1, target_len - 1)
            max_w = min(n_words, target_len + 2)

            for win_size in range(min_w, max_w + 1):
                for i in range(n_words - win_size + 1):
                    win = words[i : i + win_size]
                    win_text = " ".join(w.text for w in win)
                    win_norm = self._normalize_text(win_text)

                    ratio = fuzz.ratio(norm_val, win_norm) / 100.0
                    token_ratio = fuzz.token_sort_ratio(norm_val, win_norm) / 100.0
                    score = max(ratio, token_ratio)

                    if score > best_score:
                        best_score = score
                        if score >= self.fuzzy_threshold:
                            bbox = self._combine_bboxes(page.page, [w.bbox for w in win])
                            best_match = (bbox, page.page, round(score, 3), win_text, "fuzzy")

        if best_match and best_score >= self.fuzzy_threshold:
            return best_match

        return None

    def verify_and_ground(
        self,
        extracted_fields: dict[str, Any],
        document: RecognizedDocument,
    ) -> GroundedResult:
        """Perform grounded verification on all extracted fields.

        Every field value must be located in recognized text with a bounding box.
        Ungrounded values are discarded and logged as "hallucination_rejected".
        """
        grounded: dict[str, GroundedField] = {}
        rejected: dict[str, Any] = {}
        reasons: dict[str, str] = {}
        logs: list[str] = []

        for field_name, value in extracted_fields.items():
            if value is None:
                continue

            location = self.locate_value(value, document)
            if location is not None:
                bbox, page, confidence, matched_text, match_type = location
                grounded[field_name] = GroundedField(
                    field_name=field_name,
                    value=value,
                    matched_text=matched_text,
                    page=page,
                    bbox=bbox,
                    confidence=confidence,
                    match_type=match_type,
                    status="grounded",
                )
            else:
                # Value is ungrounded -> Discard and log as hallucination_rejected
                rejection_msg = (
                    f"hallucination_rejected: field '{field_name}' with value '{value}' "
                    f"could not be grounded in document recognized text"
                )
                logger.warning(rejection_msg)
                logs.append(rejection_msg)
                rejected[field_name] = value
                reasons[field_name] = "hallucination_rejected"

        return GroundedResult(
            grounded_fields=grounded,
            rejected_fields=rejected,
            rejection_reasons=reasons,
            hallucination_log=logs,
            total_extracted=len(extracted_fields),
            grounded_count=len(grounded),
            rejected_count=len(rejected),
        )


grounded_verifier = GroundedVerifier()
