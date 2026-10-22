from pydantic import BaseModel
from typing import List


class FlashAnalysisWarning(BaseModel):
    title: str
    detail: str


class FlashAnalysisCategory(BaseModel):
    category: str
    key_clauses: str          # plain English explanation of the important clauses
    favorable_terms: str      # what protects the user
    risks: str                # what could hurt the user
    obligations: str          # what each party must do
    clause_references: str    # clause numbers / section names mentioned


class FlashAnalysisReport(BaseModel):
    overall_verdict: str                          # short assessment + main reasons
    document_overview: str                        # purpose, parties, main arrangement
    category_analysis: List[FlashAnalysisCategory]  # per-category breakdown
    important_warnings: List[FlashAnalysisWarning]  # ranked risks
    before_you_sign: List[str]                    # action items for the user
