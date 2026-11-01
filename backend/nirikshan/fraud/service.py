"""Service layer for incremental entity indexing, fraud graph generation, and detection."""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload

from nirikshan.config import settings
from nirikshan.db.models import (
    ApplicationEntityEdgeModel,
    DossierModel,
    EntityIndexModel,
)
from nirikshan.fraud.detectors import FraudDetectorEngine
from nirikshan.fraud.extractor import EntityExtractor
from nirikshan.fraud.graph_builder import FraudGraphBuilder
from nirikshan.fraud.models import (
    CytoscapeGraphResponse,
    EntityExtractionResult,
    EntityType,
    ExtractedEntity,
)
from nirikshan.schemas.finding import Finding

logger = logging.getLogger(__name__)


class FraudGraphService:
    """Coordinates database persistence, incremental updates, and fraud graph detection."""

    def __init__(self, extractor: EntityExtractor | None = None) -> None:
        self.extractor = extractor or EntityExtractor(salt=settings.fraud_salt)

    async def index_dossier_entities(
        self, db: AsyncSession, dossier_id: str
    ) -> EntityExtractionResult:
        """Alias for background job service indexing."""
        return await self.index_dossier_async(dossier_id, db)

    async def index_dossier_async(
        self,
        dossier_id: str,
        db: AsyncSession,
        extra_entities: list[ExtractedEntity] | None = None,
    ) -> EntityExtractionResult:
        """Extract and incrementally persist entities for a single application dossier."""
        stmt = (
            select(DossierModel)
            .options(selectinload(DossierModel.documents))
            .where(DossierModel.dossier_id == dossier_id)
        )
        res = await db.execute(stmt)
        dossier = res.scalar_one_or_none()
        if not dossier:
            raise ValueError(f"Dossier {dossier_id} not found in database.")

        extracted_params = dossier.get_extracted_params()

        # Extract entities
        result = self.extractor.extract_from_dossier_data(
            dossier_id=dossier.dossier_id,
            application_number=dossier.application_number,
            institution_name=dossier.institution_name,
            documents=dossier.documents,
            extracted_params=extracted_params,
            extra_entities=extra_entities,
        )

        # 1. Upsert entities into EntityIndexModel
        for ent in result.entities:
            existing_ent = await db.get(EntityIndexModel, ent.entity_id)
            if existing_ent:
                existing_ent.raw_label = ent.label
                existing_ent.set_metadata(ent.metadata)
            else:
                db_ent = EntityIndexModel(
                    entity_id=ent.entity_id,
                    entity_type=ent.entity_type.value,
                    entity_value=ent.entity_value,
                    raw_label=ent.label,
                    metadata_json=json.dumps(ent.metadata),
                )
                db.add(db_ent)

        await db.flush()

        # 2. Atomic delete and re-insert edges for this dossier
        await db.execute(
            delete(ApplicationEntityEdgeModel).where(
                ApplicationEntityEdgeModel.dossier_id == dossier_id
            )
        )

        for edge in result.edges:
            db_edge = ApplicationEntityEdgeModel(
                edge_id=edge.edge_id,
                dossier_id=edge.dossier_id,
                entity_id=edge.entity_id,
                relation=edge.relation,
                context_label=edge.context_label,
                metadata_json=json.dumps(edge.metadata),
            )
            db.add(db_edge)

        await db.commit()
        return result

    def index_dossier_sync(
        self,
        dossier_id: str,
        db: Session,
        extra_entities: list[ExtractedEntity] | None = None,
    ) -> EntityExtractionResult:
        """Synchronously index dossier entities into the database."""
        stmt = (
            select(DossierModel)
            .options(selectinload(DossierModel.documents))
            .where(DossierModel.dossier_id == dossier_id)
        )
        dossier = db.execute(stmt).scalar_one_or_none()
        if not dossier:
            raise ValueError(f"Dossier {dossier_id} not found in database.")

        extracted_params = dossier.get_extracted_params()

        result = self.extractor.extract_from_dossier_data(
            dossier_id=dossier.dossier_id,
            application_number=dossier.application_number,
            institution_name=dossier.institution_name,
            documents=dossier.documents,
            extracted_params=extracted_params,
            extra_entities=extra_entities,
        )

        for ent in result.entities:
            existing_ent = db.get(EntityIndexModel, ent.entity_id)
            if existing_ent:
                existing_ent.raw_label = ent.label
                existing_ent.set_metadata(ent.metadata)
            else:
                db_ent = EntityIndexModel(
                    entity_id=ent.entity_id,
                    entity_type=ent.entity_type.value,
                    entity_value=ent.entity_value,
                    raw_label=ent.label,
                    metadata_json=json.dumps(ent.metadata),
                )
                db.add(db_ent)

        db.flush()

        db.execute(
            delete(ApplicationEntityEdgeModel).where(
                ApplicationEntityEdgeModel.dossier_id == dossier_id
            )
        )

        for edge in result.edges:
            db_edge = ApplicationEntityEdgeModel(
                edge_id=edge.edge_id,
                dossier_id=edge.dossier_id,
                entity_id=edge.entity_id,
                relation=edge.relation,
                context_label=edge.context_label,
                metadata_json=json.dumps(edge.metadata),
            )
            db.add(db_edge)

        db.commit()
        return result

    async def build_graph_from_db_async(
        self,
        db: AsyncSession,
        target_dossier_id: str | None = None,
    ) -> tuple[FraudGraphBuilder, list[Finding], CytoscapeGraphResponse]:
        """Load indexed entities and edges from DB, run detectors, and build Cytoscape response."""
        # Query all dossiers
        dossier_stmt = select(DossierModel)
        d_res = await db.execute(dossier_stmt)
        dossiers = d_res.scalars().all()
        dossier_map = {d.dossier_id: d for d in dossiers}

        # Query all edges
        edge_stmt = select(ApplicationEntityEdgeModel).options(
            selectinload(ApplicationEntityEdgeModel.entity)
        )
        e_res = await db.execute(edge_stmt)
        edges = e_res.scalars().all()

        builder = FraudGraphBuilder()

        # Build application structures for detectors
        app_entities_map: dict[str, list[ExtractedEntity]] = {}
        for edge in edges:
            d_id = edge.dossier_id
            ent_model = edge.entity
            if not ent_model:
                continue

            ent = ExtractedEntity(
                entity_id=ent_model.entity_id,
                entity_type=EntityType(ent_model.entity_type),
                entity_value=ent_model.entity_value,
                label=ent_model.raw_label,
                metadata=edge.get_metadata() or ent_model.get_metadata(),
            )
            app_entities_map.setdefault(d_id, []).append(ent)
            builder.add_edge(
                dossier_id=d_id,
                entity=ent,
                relation=edge.relation,
                context_label=edge.context_label,
                metadata=edge.get_metadata(),
            )

        # Ensure all registered dossiers are nodes
        applications_for_detectors: list[dict[str, Any]] = []
        for d_id, d_model in dossier_map.items():
            builder.add_application(
                dossier_id=d_id,
                institution_name=d_model.institution_name,
                application_number=d_model.application_number,
                risk_score=d_model.risk_score,
            )
            applications_for_detectors.append({
                "dossier_id": d_id,
                "institution_name": d_model.institution_name,
                "application_number": d_model.application_number,
                "entities": app_entities_map.get(d_id, []),
                "extracted_params": d_model.get_extracted_params(),
            })

        # Run fraud detectors
        findings = FraudDetectorEngine.run_all(applications_for_detectors)

        # Generate Cytoscape graph
        cyto_response = builder.to_cytoscape_json(findings=findings)
        return builder, findings, cyto_response

    def build_graph_from_results(
        self,
        extraction_results: list[EntityExtractionResult],
    ) -> tuple[FraudGraphBuilder, list[Finding], CytoscapeGraphResponse]:
        """In-memory graph builder and detection runner (ideal for tests and offline batches)."""
        builder = FraudGraphBuilder()
        applications_for_detectors: list[dict[str, Any]] = []

        for r in extraction_results:
            builder.ingest_extraction_result(r)
            applications_for_detectors.append({
                "dossier_id": r.dossier_id,
                "institution_name": r.institution_name,
                "application_number": r.application_number,
                "entities": r.entities,
            })

        findings = FraudDetectorEngine.run_all(applications_for_detectors)
        cyto_response = builder.to_cytoscape_json(findings=findings)
        return builder, findings, cyto_response


fraud_service = FraudGraphService()
