"""YAML ruleset loader with caching and validation."""

from pathlib import Path
from typing import Any

import yaml

from nirikshan.config import settings


class RulesetLoader:
    """Loads and caches versioned YAML rulesets from rulesets directory."""

    def __init__(self, rules_dir: Path | None = None) -> None:
        self.rules_dir = rules_dir or settings.rulesets_dir
        self._cache: dict[str, dict[str, Any]] = {}

    def load_ruleset(self, filename: str = "aicte_aph_2024_2027.yaml") -> dict[str, Any]:
        """Load ruleset YAML file."""
        if filename in self._cache:
            return self._cache[filename]

        file_path = self.rules_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Ruleset file not found: {file_path}")

        with file_path.open("r", encoding="utf-8") as f:
            data: dict[str, Any] = yaml.safe_load(f)

        self._cache[filename] = data
        return data

    def get_rules(self, filename: str = "aicte_aph_2024_2027.yaml") -> list[dict[str, Any]]:
        """Return list of rule dictionaries."""
        data = self.load_ruleset(filename)
        rules: list[dict[str, Any]] = data.get("rules", [])
        return rules


ruleset_loader = RulesetLoader()
