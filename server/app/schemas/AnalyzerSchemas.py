from pydantic import BaseModel, Field
from typing import List, Dict, Any

from typing import List, Dict, Any, Literal

# Phase 1: Overview Schemas
class DocumentIdentity(BaseModel):
    document_type: Literal["Lease", "NDA", "Employment", "Loan", "Service", "Sale", "Partnership", "Amendment", "Other"] = Field(description="The formal legal type of this document. Must be exactly one of the allowed values.")
    plain_summary: str = Field(description="A very simple, plain-English 2-sentence summary of what this specific document is. MUST include the exact names of the parties if they appear in the text. If not present, say 'between unnamed parties'.")
    parties: List[str] = Field(description="A list of the names of the entities/people involved in the contract.", default_factory=list)
    jurisdiction: str = Field(description="The state or country governing the document, if mentioned. If not, return 'Unknown'.", default="Unknown")

class RoadmapResult(BaseModel):
    recommended_roadmap: List[str] = Field(description="An ordered array of clause categories, ordered by importance to a non-lawyer reviewer, NOT by clause count. High risk categories come first.")
    recommended_starting_point: str = Field(description="The absolute best category to start reading first.")
    reasoning: str = Field(description="A 1-sentence explanation of why this specific roadmap order was chosen for this specific document type.", default="")

class CategoryCount(BaseModel):
    category: str
    count: int

class OverviewResponse(BaseModel):
    document_type: str
    summary: str
    parties: List[str] = Field(default_factory=list)
    jurisdiction: str = Field(default="Unknown")
    total_clauses: int
    breakdown: List[CategoryCount]
    recommended_roadmap: List[str]
    recommended_starting_point: str
    reasoning: str = Field(default="")
