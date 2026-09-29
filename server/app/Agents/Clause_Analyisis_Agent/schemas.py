from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class FAQ(BaseModel):
    question: str = Field(description="A common question a non-lawyer might have about this clause.")
    answer: str = Field(description="A simple, direct answer to the question.")

class ClauseAnalysisOutput(BaseModel):
    """
    The strict JSON schema that the Analysis Node must output.
    """
    explanation: str = Field(
        description="A plain English explanation of what this clause means, written for a non-lawyer."
    )
    entities_involved: List[str] = Field(
        description="A list of specific entities (e.g., 'Landlord', 'Tenant', 'Employee') directly impacted by this clause."
    )
    real_world_examples: List[str] = Field(
        description="1-2 realistic real-world scenarios showing how this clause could affect the parties. MUST explicitly start with 'Hypothetical example:'"
    )
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        description="Overall risk level of the clause: LOW, MEDIUM, or HIGH."
    )
    risk_analysis: str = Field(
        description=(
            "Explain clearly why this risk level was assigned. "
            "Identify the specific wording, obligations, costs, restrictions, "
            "or potential consequences that create the risk. "
            "Use the clause and retrieved evidence as the basis for the assessment."
        )
    )
    negotiation_advice: str = Field(
        description="Actionable advice or counter-offers on how to negotiate better terms for this clause."
    )
    faqs: List[FAQ] = Field(
        description="A list of 2-3 frequently asked questions about this clause."
    )
    document_citations: List[str] = Field(
        description="A list of Chunk UUIDs that were used as evidence for this analysis."
    )
    web_citations: List[str] = Field(
        description="A list of Website URLs that were used to determine market standards."
    )

class VerificationOutput(BaseModel):
    """
    The strict JSON schema that the Verification (Anti-Hallucination) Node must output.
    """
    is_correct: bool = Field(
        description="True if the analysis is perfectly accurate and grounded in context. False if there are hallucinations or errors."
    )
    feedback: Optional[str] = Field(
        description="If is_correct is False, provide specific instructions on what the Analysis Node needs to fix."
    )
