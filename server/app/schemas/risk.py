from typing import List, Optional, Literal

from pydantic import BaseModel, Field


class ClauseRisk(BaseModel):
    chunk_id: str
    category: str = "Unclassified"
    excerpt: str
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    explanation_easy: str
    counter_offer: Optional[str] = None
    market_standard: Optional[str] = None


class RiskAnalysisResponse(BaseModel):
    overall_risk: Literal["LOW", "MEDIUM", "HIGH"]
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    clauses: List[ClauseRisk] = Field(default_factory=list)