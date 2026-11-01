"""API routes for inspecting versioned regulatory rulesets."""

from typing import Any

from fastapi import APIRouter, HTTPException

from nirikshan.engine.loader import ruleset_loader

router = APIRouter(prefix="/api/rules", tags=["rules"])


@router.get("", response_model=list[dict[str, Any]])
async def list_rules() -> list[dict[str, Any]]:
    """List all deterministic AICTE Approval Process Handbook rules loaded from YAML."""
    return ruleset_loader.get_rules()


@router.get("/{rule_id}", response_model=dict[str, Any])
async def get_rule(rule_id: str) -> dict[str, Any]:
    """Retrieve details, citation, and handbook references for a specific rule."""
    rules = ruleset_loader.get_rules()
    for r in rules:
        if r["id"] == rule_id:
            return r
    raise HTTPException(status_code=404, detail="Rule ID not found")
