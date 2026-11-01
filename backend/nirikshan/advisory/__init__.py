"""Advisory ML Layer for Nirikshan Scrutiny System.

All components in this package operate at Trust Level: MODEL (Rank 10 — Advisory Only).
In accordance with Core Principle 1, model outputs cannot independently issue PASS or FAIL.
"""

from nirikshan.advisory.ask_why import (
    AskWhyAssistant,
    AskWhyCitation,
    AskWhyContext,
    AskWhyLLM,
    AskWhyResponse,
    OllamaAskWhyLLM,
    StubAskWhyLLM,
    ask_why_assistant,
)
from nirikshan.advisory.asset_counter import (
    DetectionBox,
    LabAssetDetector,
    LabInventoryResult,
    MockLabAssetDetector,
    YOLOXAssetDetector,
    annotate_image,
    verify_lab_inventory,
)
from nirikshan.advisory.extractor import (
    ExtractionError,
    FieldExtractor,
    OllamaConnectionError,
    OllamaFieldExtractor,
    StubFieldExtractor,
)
from nirikshan.advisory.grounding import (
    GroundedField,
    GroundedResult,
    GroundedVerifier,
    RecognizedDocument,
    RecognizedPage,
    RecognizedWord,
    grounded_verifier,
)

__all__ = [
    # Extractor
    "FieldExtractor",
    "OllamaFieldExtractor",
    "StubFieldExtractor",
    "ExtractionError",
    "OllamaConnectionError",
    # Grounding
    "GroundedVerifier",
    "grounded_verifier",
    "GroundedField",
    "GroundedResult",
    "RecognizedDocument",
    "RecognizedPage",
    "RecognizedWord",
    # Lab Asset Counter
    "LabAssetDetector",
    "YOLOXAssetDetector",
    "MockLabAssetDetector",
    "DetectionBox",
    "LabInventoryResult",
    "annotate_image",
    "verify_lab_inventory",
    # Ask Why Assistant
    "AskWhyAssistant",
    "ask_why_assistant",
    "AskWhyContext",
    "AskWhyResponse",
    "AskWhyCitation",
    "AskWhyLLM",
    "StubAskWhyLLM",
    "OllamaAskWhyLLM",
]
