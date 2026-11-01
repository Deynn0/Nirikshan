"""Cross-application fraud detection and graph analysis module."""

from nirikshan.fraud.detectors import (
    CertificateSharingDetector,
    FraudDetectorEngine,
    GhostFacultyDetector,
    PhotoReuseDetector,
    SealReuseDetector,
)
from nirikshan.fraud.extractor import EntityExtractor
from nirikshan.fraud.graph_builder import FraudGraphBuilder
from nirikshan.fraud.hasher import (
    hamming_distance,
    hash_salted_identity,
    mask_identity_label,
    normalize_identity_id,
)
from nirikshan.fraud.models import (
    ApplicationEntityEdge,
    CytoscapeClusterSummary,
    CytoscapeEdge,
    CytoscapeElements,
    CytoscapeGraphResponse,
    CytoscapeNode,
    EntityExtractionResult,
    EntityType,
    ExtractedEntity,
)
from nirikshan.fraud.service import FraudGraphService, fraud_service

__all__ = [
    "ApplicationEntityEdge",
    "CertificateSharingDetector",
    "CytoscapeClusterSummary",
    "CytoscapeEdge",
    "CytoscapeElements",
    "CytoscapeGraphResponse",
    "CytoscapeNode",
    "EntityExtractionResult",
    "EntityExtractor",
    "EntityType",
    "ExtractedEntity",
    "FraudDetectorEngine",
    "FraudGraphBuilder",
    "FraudGraphService",
    "GhostFacultyDetector",
    "PhotoReuseDetector",
    "SealReuseDetector",
    "fraud_service",
    "hamming_distance",
    "hash_salted_identity",
    "mask_identity_label",
    "normalize_identity_id",
]
