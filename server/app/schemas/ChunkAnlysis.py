from pydantic import BaseModel, Field
from typing import List

class ChunkAnalysis(BaseModel):
    chunk_id: str
    classification_name: str
    aliases: List[str] = Field(
        description="A list of names, section numbers, or titles that this specific chunk is known as (e.g., ['Section 4.2', 'Termination Clause'])."
    )
    direct_references: List[str] = Field(
        description="A list of OTHER clauses, sections, or annexures explicitly mentioned in the text. Do NOT include the section number of the chunk itself. Only include references that point OUTSIDE the current text (e.g., ['Article 5', 'Annexure A'])."
    )

class BatchAnalysisResponse(BaseModel):
    results: List[ChunkAnalysis]
