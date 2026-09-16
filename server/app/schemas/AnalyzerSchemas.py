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

# Phase 2: Risk Analysis Schemas
class RawRiskItem(BaseModel):
    chunk_id: str = Field(min_length=1, description="The UUID of the clause chunk.")
    clause_title: str = Field(min_length=1, description="A concise title/label for the clause or issue.")
    risk_level: Literal["HIGH", "MEDIUM", "LOW"] = Field(description="The severity of the risk posed by the clause.")
    explanation: str = Field(min_length=1, description="1-2 sentence explanation of the exact exposure.")
    compliance_check: str = Field(default="", description="Relevant statutory context, legal enforceability, or market standard.")
    recommendation: str = Field(default="", description="Actionable modification or negotiation tip for the weaker/reviewing party.")

class RawBatchRiskResponse(BaseModel):
    risks: List[RawRiskItem] = Field(default_factory=list, description="The list of identified risky clauses in this batch.")

class RiskItem(BaseModel):
    chunk_id: str = Field(description="The UUID of the clause chunk.")
    chunk_text: str = Field(description="The exact text of the clause.")
    risk_level: Literal["HIGH", "MEDIUM", "LOW"] = Field(description="The severity of the risk posed by the clause.")
    clause_title: str = Field(description="A concise title/label for the clause or issue (e.g. 'Uncapped Indemnity', 'Immediate Termination').", default="Identified Risk")
    explanation: str = Field(description="The objective truth and practical implications of the clause, explaining why it poses this risk.")
    compliance_check: str = Field(default="", description="Relevant statutory context, legal enforceability, or market standard.")
    recommendation: str = Field(default="", description="Actionable modification or negotiation tip for the weaker/reviewing party.")

class BatchRiskResponse(BaseModel):
    risks: List[RiskItem] = Field(description="The list of identified risky clauses in this batch.")

class DocumentRiskResponse(BaseModel):
    high_risks: List[RiskItem] = Field(default_factory=list)
    medium_risks: List[RiskItem] = Field(default_factory=list)
    low_risks: List[RiskItem] = Field(default_factory=list)
    total_risks: int = 0
