"""Alias dictionaries with fuzzy matching and Devanagari normalization.

This module:
1. Loads aliases_en.yaml and aliases_hi.yaml from the rulesets directory.
2. Provides a fuzzy matcher using rapidfuzz (WRatio scorer).
3. Normalizes Devanagari text (Unicode NFC + stripping zero-width chars).
4. Returns the canonical field name for any input label.

Alias YAML format:
    canonical_field_name:
      en: ["English Label", "Alt English Label", ...]
      hi: ["हिंदी लेबल", "वैकल्पिक", ...]

The combined alias map supports both language files merged together.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Any

import yaml

from nirikshan.config import settings

# rapidfuzz is optional; fall back to exact matching if not installed
try:
    from rapidfuzz import fuzz
    from rapidfuzz import process as rf_process

    _HAS_RAPIDFUZZ = True
except ImportError:  # pragma: no cover
    _HAS_RAPIDFUZZ = False


# ---------------------------------------------------------------------------
# Devanagari normalization
# ---------------------------------------------------------------------------

_ZERO_WIDTH_CHARS = "\u200b\u200c\u200d\ufeff\u00ad"


def normalize_devanagari(text: str) -> str:
    """NFC-normalize and strip zero-width characters from Devanagari text."""
    text = unicodedata.normalize("NFC", text)
    for ch in _ZERO_WIDTH_CHARS:
        text = text.replace(ch, "")
    return text.strip()


# ---------------------------------------------------------------------------
# Alias index
# ---------------------------------------------------------------------------

AliasIndex = dict[str, str]
"""Maps every known alias (lowercased, stripped) → canonical field name."""


def _build_index(alias_map: dict[str, Any], lang: str) -> AliasIndex:
    """Build a lookup dict from a loaded alias YAML for a given language key."""
    index: AliasIndex = {}
    for canonical, entry in alias_map.items():
        labels: list[str] = []
        if isinstance(entry, list):
            labels = entry
        elif isinstance(entry, dict):
            labels = entry.get(lang, []) or entry.get("aliases", [])
        for label in labels:
            if isinstance(label, str):
                norm = normalize_devanagari(label).lower()
                index[norm] = canonical
        # Always add the canonical name itself
        index[canonical.lower()] = canonical
    return index


class AliasResolver:
    """Resolve any English or Hindi field label to its canonical name."""

    def __init__(
        self,
        en_file: str = "aliases_en.yaml",
        hi_file: str = "aliases_hi.yaml",
        rulesets_dir: Path | None = None,
    ) -> None:
        self._dir = rulesets_dir or settings.rulesets_dir
        self._en_file = en_file
        self._hi_file = hi_file
        self._index: AliasIndex = {}
        self._all_labels: list[str] = []
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return

        combined: AliasIndex = {}

        for fname, langs in (
            (self._en_file, ["en"]),
            (self._hi_file, ["hi"]),
        ):
            fpath = self._dir / fname
            if not fpath.exists():
                continue
            raw: dict[str, Any] = yaml.safe_load(fpath.read_text(encoding="utf-8")) or {}
            for lang in langs:
                combined.update(_build_index(raw, lang))
            # Also index using the opposite lang key present in same file
            for lang in ({"en", "hi"} - set(langs)):
                combined.update(_build_index(raw, lang))

        self._index = combined
        self._all_labels = list(combined.keys())
        self._loaded = True

    def resolve(self, label: str, threshold: float = 80.0) -> str | None:
        """Resolve *label* to a canonical field name.

        1. Normalize (NFC + strip zero-width).
        2. Exact match (case-insensitive).
        3. Fuzzy match via rapidfuzz WRatio if score >= threshold.

        Returns canonical field name or None if unresolvable.
        """
        self._ensure_loaded()

        # Normalize input
        normed = normalize_devanagari(label).lower()

        # Exact match
        if normed in self._index:
            return self._index[normed]

        # Fuzzy match
        if _HAS_RAPIDFUZZ and self._all_labels:
            result = rf_process.extractOne(
                normed,
                self._all_labels,
                scorer=fuzz.token_set_ratio,
                score_cutoff=threshold,
            )
            if result is not None:
                matched_label: str = result[0]
                return self._index[matched_label]

        return None

    def resolve_or_raise(self, label: str, threshold: float = 80.0) -> str:
        """Like resolve() but raises KeyError if no match found."""
        result = self.resolve(label, threshold)
        if result is None:
            raise KeyError(
                f"Could not resolve label {label!r} to a canonical field name. "
                f"Check aliases_en.yaml and aliases_hi.yaml."
            )
        return result

    def list_canonical_fields(self) -> list[str]:
        """Return sorted list of all canonical field names."""
        self._ensure_loaded()
        return sorted(set(self._index.values()))

    def reload(self) -> None:
        """Force reload of alias files (useful in tests)."""
        self._loaded = False
        self._index = {}
        self._all_labels = []


# Module-level singleton
alias_resolver = AliasResolver()
