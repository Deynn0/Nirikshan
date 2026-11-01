"""Pydantic schemas and models for cross-application fraud graph."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from nirikshan.schemas.finding import Finding


class EntityType(StrEnum):
    """Categorization of cross-application scrutiny entities."""

    FACULTY = "FACULTY"                     # Faculty Aadhaar/PAN salted hash
    CERTIFICATE = "CERTIFICATE"             # Fire NOC, Building Completion, etc.
    FILE_HASH = "FILE_HASH"                 # Document binary SHA-256
    PHOTO_PHASH = "PHOTO_PHASH"             # Lab, campus, building photo perceptual hash
    SEAL_PHASH = "SEAL_PHASH"               # Stamp / official seal perceptual hash
    LAND_REG = "LAND_REG"                   # Land title deed / sub-registrar reg no
    DECLARED_ADDRESS = "DECLARED_ADDRESS"   # Declared institutional location / address


class ExtractedEntity(BaseModel):
    """Normalized entity extracted from an application dossier."""

    entity_id: str = Field(..., description="Unique deterministic identifier (e.g. 'FACULTY:a1b2c3...')")
    entity_type: EntityType
    entity_value: str = Field(..., description="Exact match value (salted hash, normalized cert no, phash, sha256)")
    label: str = Field(..., description="Human-readable label for graph display")
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApplicationEntityEdge(BaseModel):
    """Graph edge connecting an application dossier to an entity."""

    edge_id: str
    dossier_id: str
    entity_id: str
    relation: str = "uses"
    context_label: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class EntityExtractionResult(BaseModel):
    """Bundle of all entities extracted for a single application dossier."""

    dossier_id: str
    application_number: str
    institution_name: str
    entities: list[ExtractedEntity] = Field(default_factory=list)
    edges: list[ApplicationEntityEdge] = Field(default_factory=list)


# --- Cytoscape.js Format Models ---

class CytoscapeNodeData(BaseModel):
    """Node data payload for Cytoscape.js rendering."""

    id: str
    label: str
    node_type: str = Field(..., description="'application' or 'entity'")
    entity_type: str | None = None
    cluster_id: int = 0
    severity: str = "CLEAN"  # CLEAN, LOW, MEDIUM, HIGH, FLAGGED_TAMPER
    institution_name: str | None = None
    application_number: str | None = None
    risk_score: float | None = None
    value: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class CytoscapeNode(BaseModel):
    """Cytoscape.js node element."""

    data: CytoscapeNodeData


class CytoscapeEdgeData(BaseModel):
    """Edge data payload for Cytoscape.js rendering."""

    id: str
    source: str
    target: str
    relation: str = "uses"
    label: str = "uses"
    cluster_id: int = 0
    severity: str = "CLEAN"
    hamming_distance: int | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class CytoscapeEdge(BaseModel):
    """Cytoscape.js edge element."""

    data: CytoscapeEdgeData


class CytoscapeElements(BaseModel):
    """Cytoscape.js elements dictionary containing nodes and edges."""

    nodes: list[CytoscapeNode] = Field(default_factory=list)
    edges: list[CytoscapeEdge] = Field(default_factory=list)


class CytoscapeClusterSummary(BaseModel):
    """Summary of a connected fraud cluster in the graph."""

    cluster_id: int
    size: int
    node_count: int
    edge_count: int
    max_severity: str
    fraud_types: list[str] = Field(default_factory=list)
    involved_application_ids: list[str] = Field(default_factory=list)
    involved_institutions: list[str] = Field(default_factory=list)


class CytoscapeGraphResponse(BaseModel):
    """Complete API response payload for the fraud graph."""

    elements: CytoscapeElements
    clusters: list[CytoscapeClusterSummary] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    total_applications: int = 0
    total_entities: int = 0
    total_edges: int = 0
    fraud_detected: bool = False
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
