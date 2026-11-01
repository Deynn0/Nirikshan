"""NetworkX graph builder for cross-application fraud detection.

Constructs bipartite multi-entity graph:
  Nodes: Applications & Entities
  Edges: "uses" relations and "perceptual_match" similarity relations

Computes connected components (clusters), assigns risk severities,
and serializes to standard Cytoscape.js JSON format.
"""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx  # type: ignore[import-untyped]

from nirikshan.config import settings
from nirikshan.fraud.hasher import hamming_distance
from nirikshan.fraud.models import (
    CytoscapeClusterSummary,
    CytoscapeEdge,
    CytoscapeEdgeData,
    CytoscapeElements,
    CytoscapeGraphResponse,
    CytoscapeNode,
    CytoscapeNodeData,
    EntityExtractionResult,
    EntityType,
    ExtractedEntity,
)
from nirikshan.schemas.finding import Finding, VerificationStatus

logger = logging.getLogger(__name__)


class FraudGraphBuilder:
    """Builds and analyzes NetworkX cross-application compliance graphs."""

    def __init__(
        self,
        photo_hamming_threshold: int | None = None,
        seal_hamming_threshold: int | None = None,
    ) -> None:
        self.photo_threshold = (
            photo_hamming_threshold
            if photo_hamming_threshold is not None
            else settings.fraud_photo_hamming_threshold
        )
        self.seal_threshold = (
            seal_hamming_threshold
            if seal_hamming_threshold is not None
            else settings.fraud_seal_hamming_threshold
        )
        self.graph = nx.Graph()

    def reset(self) -> None:
        """Clear all nodes and edges in the graph."""
        self.graph.clear()

    def add_application(
        self,
        dossier_id: str,
        institution_name: str,
        application_number: str,
        risk_score: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Add an application dossier node to the graph."""
        node_id = f"app:{dossier_id}"
        self.graph.add_node(
            node_id,
            node_type="application",
            dossier_id=dossier_id,
            institution_name=institution_name,
            application_number=application_number,
            risk_score=risk_score,
            label=institution_name,
            severity="CLEAN",
            cluster_id=0,
            metadata=metadata or {},
        )
        return node_id

    def add_entity(self, entity: ExtractedEntity) -> str:
        """Add an entity node to the graph."""
        node_id = f"ent:{entity.entity_id}"
        if node_id not in self.graph:
            self.graph.add_node(
                node_id,
                node_type="entity",
                entity_id=entity.entity_id,
                entity_type=entity.entity_type.value,
                entity_value=entity.entity_value,
                label=entity.label,
                severity="CLEAN",
                cluster_id=0,
                metadata=entity.metadata,
            )
        return node_id

    def add_edge(
        self,
        dossier_id: str,
        entity: ExtractedEntity,
        relation: str = "uses",
        context_label: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Add a 'uses' edge between application and entity."""
        app_id = f"app:{dossier_id}"
        ent_id = f"ent:{entity.entity_id}"
        edge_id = f"edge:{dossier_id}:{entity.entity_id}"

        # Ensure nodes exist
        if app_id not in self.graph:
            self.add_application(
                dossier_id=dossier_id,
                institution_name=metadata.get("institution_name", dossier_id) if metadata else dossier_id,
                application_number=metadata.get("application_number", dossier_id) if metadata else dossier_id,
            )
        if ent_id not in self.graph:
            self.add_entity(entity)

        self.graph.add_edge(
            app_id,
            ent_id,
            edge_id=edge_id,
            relation=relation,
            label=relation,
            context_label=context_label or relation,
            severity="CLEAN",
            cluster_id=0,
            metadata=metadata or {},
        )
        return edge_id

    def ingest_extraction_result(self, result: EntityExtractionResult) -> None:
        """Add an entire application extraction result into the graph."""
        self.add_application(
            dossier_id=result.dossier_id,
            institution_name=result.institution_name,
            application_number=result.application_number,
        )
        for entity in result.entities:
            self.add_entity(entity)
            self.add_edge(
                dossier_id=result.dossier_id,
                entity=entity,
                relation="uses",
                context_label=entity.label,
                metadata={"institution_name": result.institution_name},
            )

    def link_perceptual_matches(self) -> list[tuple[str, str, int]]:
        """Link photo and seal entities that fall within perceptual Hamming thresholds."""
        matches: list[tuple[str, str, int]] = []
        nodes = list(self.graph.nodes(data=True))

        # 1. Photos
        photo_nodes = [
            (nid, d) for nid, d in nodes if d.get("entity_type") == EntityType.PHOTO_PHASH.value
        ]
        for i, (id1, d1) in enumerate(photo_nodes):
            h1 = d1.get("entity_value")
            for id2, d2 in photo_nodes[i + 1 :]:
                h2 = d2.get("entity_value")
                dist = hamming_distance(h1, h2)
                if dist <= self.photo_threshold:
                    edge_id = f"sim:{id1}:{id2}"
                    if not self.graph.has_edge(id1, id2):
                        self.graph.add_edge(
                            id1,
                            id2,
                            edge_id=edge_id,
                            relation="perceptual_match",
                            label=f"pHash match (dist={dist})",
                            severity="FLAGGED_TAMPER",
                            hamming_distance=dist,
                            cluster_id=0,
                        )
                        matches.append((id1, id2, dist))

        # 2. Seals
        seal_nodes = [
            (nid, d) for nid, d in nodes if d.get("entity_type") == EntityType.SEAL_PHASH.value
        ]
        for i, (id1, d1) in enumerate(seal_nodes):
            h1 = d1.get("entity_value")
            for id2, d2 in seal_nodes[i + 1 :]:
                h2 = d2.get("entity_value")
                dist = hamming_distance(h1, h2)
                if dist <= self.seal_threshold:
                    edge_id = f"sim:{id1}:{id2}"
                    if not self.graph.has_edge(id1, id2):
                        self.graph.add_edge(
                            id1,
                            id2,
                            edge_id=edge_id,
                            relation="perceptual_match",
                            label=f"Seal match (dist={dist})",
                            severity="FLAGGED_TAMPER",
                            hamming_distance=dist,
                            cluster_id=0,
                        )
                        matches.append((id1, id2, dist))

        return matches

    def compute_clusters_and_severities(
        self, findings: list[Finding] | None = None
    ) -> list[CytoscapeClusterSummary]:
        """Compute connected components and assign cluster IDs and severities.

        Cross-references detector findings to color-code fraudulent nodes/edges.
        """
        # Ensure perceptual matches are connected
        self.link_perceptual_matches()

        # Build mapping of dossier_id -> worst finding severity
        active_findings = findings or []
        finding_app_map: dict[str, list[Finding]] = {}
        for f in active_findings:
            # Check involved applications in evidence
            for ev in f.evidence_list:
                d_id = ev.source_document_id
                if d_id:
                    finding_app_map.setdefault(d_id, []).append(f)
            # Check note or details for app ids
            for _nid, ndata in self.graph.nodes(data=True):
                if ndata.get("node_type") == "application":
                    d_id = ndata.get("dossier_id", "")
                    if d_id and d_id in f.details and f not in finding_app_map.get(d_id, []):
                        finding_app_map.setdefault(d_id, []).append(f)

        components = list(nx.connected_components(self.graph))
        clusters: list[CytoscapeClusterSummary] = []

        for cluster_idx, comp_nodes in enumerate(components, start=1):
            comp_subgraph = self.graph.subgraph(comp_nodes)
            node_count = len(comp_nodes)
            edge_count = comp_subgraph.number_of_edges()

            cluster_apps: list[str] = []
            cluster_institutions: list[str] = []
            cluster_severities: list[str] = []
            cluster_fraud_types: set[str] = set()

            for n in comp_nodes:
                ndata = self.graph.nodes[n]
                ndata["cluster_id"] = cluster_idx
                if ndata.get("node_type") == "application":
                    d_id = ndata.get("dossier_id", "")
                    inst = ndata.get("institution_name", "")
                    if d_id:
                        cluster_apps.append(d_id)
                    if inst:
                        cluster_institutions.append(inst)

                    # Check findings for this application
                    app_findings = finding_app_map.get(d_id, [])
                    if app_findings:
                        worst = max(
                            [f.status.value for f in app_findings],
                            key=lambda s: 3 if s == "FLAGGED_TAMPER" else (2 if s == "FAIL" else 1),
                        )
                        ndata["severity"] = worst
                        cluster_severities.append(worst)
                        for f in app_findings:
                            cluster_fraud_types.add(f.rule_name)
                    else:
                        ndata["severity"] = "CLEAN"
                        cluster_severities.append("CLEAN")

            # Check entity nodes and edges in component
            for u, v, edata in comp_subgraph.edges(data=True):
                edata["cluster_id"] = cluster_idx
                u_data = self.graph.nodes[u]
                v_data = self.graph.nodes[v]

                # If either end is flagged, or relation is perceptual_match
                if (
                    u_data.get("severity") in ("FLAGGED_TAMPER", "FAIL")
                    or v_data.get("severity") in ("FLAGGED_TAMPER", "FAIL")
                    or edata.get("relation") == "perceptual_match"
                ):
                    edata["severity"] = "FLAGGED_TAMPER"
                    # Also elevate entity node severity
                    if u_data.get("node_type") == "entity":
                        u_data["severity"] = "FLAGGED_TAMPER"
                    if v_data.get("node_type") == "entity":
                        v_data["severity"] = "FLAGGED_TAMPER"
                else:
                    edata["severity"] = "CLEAN"

            max_sev = "CLEAN"
            if "FLAGGED_TAMPER" in cluster_severities:
                max_sev = "FLAGGED_TAMPER"
            elif "FAIL" in cluster_severities:
                max_sev = "FAIL"
            elif any(self.graph.nodes[n].get("severity") == "FLAGGED_TAMPER" for n in comp_nodes):
                max_sev = "FLAGGED_TAMPER"

            clusters.append(
                CytoscapeClusterSummary(
                    cluster_id=cluster_idx,
                    size=node_count + edge_count,
                    node_count=node_count,
                    edge_count=edge_count,
                    max_severity=max_sev,
                    fraud_types=sorted(cluster_fraud_types),
                    involved_application_ids=cluster_apps,
                    involved_institutions=cluster_institutions,
                )
            )

        return clusters

    def to_cytoscape_json(self, findings: list[Finding] | None = None) -> CytoscapeGraphResponse:
        """Export graph and findings to Cytoscape.js format."""
        clusters = self.compute_clusters_and_severities(findings=findings)

        cyto_nodes: list[CytoscapeNode] = []
        cyto_edges: list[CytoscapeEdge] = []

        app_count = 0
        entity_count = 0

        for nid, ndata in self.graph.nodes(data=True):
            n_type = ndata.get("node_type", "entity")
            if n_type == "application":
                app_count += 1
            else:
                entity_count += 1

            cyto_nodes.append(
                CytoscapeNode(
                    data=CytoscapeNodeData(
                        id=str(nid),
                        label=ndata.get("label", str(nid)),
                        node_type=n_type,
                        entity_type=ndata.get("entity_type"),
                        cluster_id=ndata.get("cluster_id", 0),
                        severity=ndata.get("severity", "CLEAN"),
                        institution_name=ndata.get("institution_name"),
                        application_number=ndata.get("application_number"),
                        risk_score=ndata.get("risk_score"),
                        value=ndata.get("entity_value"),
                        details=ndata.get("metadata", {}),
                    )
                )
            )

        for u, v, edata in self.graph.edges(data=True):
            e_id = edata.get("edge_id") or f"edge:{u}:{v}"
            cyto_edges.append(
                CytoscapeEdge(
                    data=CytoscapeEdgeData(
                        id=str(e_id),
                        source=str(u),
                        target=str(v),
                        relation=edata.get("relation", "uses"),
                        label=edata.get("label", "uses"),
                        cluster_id=edata.get("cluster_id", 0),
                        severity=edata.get("severity", "CLEAN"),
                        hamming_distance=edata.get("hamming_distance"),
                        details=edata.get("metadata", {}),
                    )
                )
            )

        active_findings = findings or []
        fraud_detected = any(
            f.status in (VerificationStatus.FLAGGED_TAMPER, VerificationStatus.FAIL)
            for f in active_findings
        ) or any(c.max_severity in ("FLAGGED_TAMPER", "FAIL") for c in clusters)

        return CytoscapeGraphResponse(
            elements=CytoscapeElements(nodes=cyto_nodes, edges=cyto_edges),
            clusters=clusters,
            findings=active_findings,
            total_applications=app_count,
            total_entities=entity_count,
            total_edges=len(cyto_edges),
            fraud_detected=fraud_detected,
        )
