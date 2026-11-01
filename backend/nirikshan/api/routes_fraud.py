"""FastAPI routes for cross-application fraud graph analysis."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from nirikshan.db.session import get_db
from nirikshan.fraud.models import CytoscapeGraphResponse, EntityExtractionResult
from nirikshan.fraud.service import fraud_service
from nirikshan.schemas.finding import Finding

router = APIRouter(prefix="/api/fraud", tags=["fraud-graph"])


@router.get("/graph", response_model=CytoscapeGraphResponse)
async def get_fraud_graph(
    db: AsyncSession = Depends(get_db),
) -> CytoscapeGraphResponse:
    """Retrieve full cross-application compliance graph in Cytoscape.js format.

    Elements contain nodes and edges with cluster IDs and severity values.
    Includes connected components analysis and cross-application fraud findings.
    """
    try:
        _, _, response = await fraud_service.build_graph_from_db_async(db)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate cross-application fraud graph: {e}",
        ) from e


@router.post("/index/{dossier_id}", response_model=EntityExtractionResult)
async def index_dossier(
    dossier_id: str,
    db: AsyncSession = Depends(get_db),
) -> EntityExtractionResult:
    """Incrementally extract and index entities for an application dossier.

    Persists faculty salted hashes, certificate numbers, file SHA-256s,
    photo perceptual hashes, seal perceptual hashes, land registration numbers,
    and declared addresses into the state store.
    """
    try:
        return await fraud_service.index_dossier_async(dossier_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to index dossier {dossier_id}: {e}",
        ) from e


@router.post("/scan", response_model=list[Finding])
async def scan_fraud_detectors(
    db: AsyncSession = Depends(get_db),
) -> list[Finding]:
    """Execute all cross-application fraud detectors:

    - Ghost Faculty (same faculty hash full-time at 2+ institutions overlapping)
    - Certificate Sharing (same Fire NOC / land deed across institutions)
    - Photo Reuse (identical or near-identical photos across applicants)
    - Seal Reuse (same seal phash across different issuing authorities)
    """
    try:
        _, findings, _ = await fraud_service.build_graph_from_db_async(db)
        return findings
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run fraud detectors: {e}",
        ) from e


@router.get("/findings", response_model=list[Finding])
async def get_fraud_findings(
    db: AsyncSession = Depends(get_db),
) -> list[Finding]:
    """Retrieve all current cross-application fraud findings."""
    _, findings, _ = await fraud_service.build_graph_from_db_async(db)
    return findings
