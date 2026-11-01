"""Regulatory handbook citation schema."""

from pydantic import BaseModel, Field


class HandbookCitation(BaseModel):
    """Citations pointing directly to AICTE Approval Process Handbook clauses."""

    handbook: str = Field(
        default="AICTE Approval Process Handbook 2024-2027",
        description="Official handbook title",
    )
    clause: str = Field(..., description="Clause or Sub-clause e.g. 'Clause 4.1'")
    page: int | str = Field(..., description="Exact page reference or TODO")
    edition: str = Field(default="2024-2027", description="Handbook academic block")
    table: str | None = Field(default=None, description="Optional Table reference e.g. 'Table 4.1'")
    needs_verification: bool = Field(
        default=False,
        description="Flag indicating handbook reference requires manual verification",
    )
