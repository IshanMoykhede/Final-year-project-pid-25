import logging
import os
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
from app.Agents.Clause_Analyisis_Agent.state import AgentState
from app.Agents.Clause_Analyisis_Agent.schemas import ClauseAnalysisOutput

logger = logging.getLogger(__name__)

def analysis_node(state: AgentState):
    logger.info(f"[NODE: Analysis] Generating final analysis for Chunk {state['chunk_id']}")
    
    # 1. Initialize the massive 120b parameter model for deep reasoning
    llm = ChatGroq(
        api_key=os.environ.get("GROQ_API_KEY"), 
        model="openai/gpt-oss-120b",
        temperature=0.2
    )
    
    # 2. Force the LLM to output ONLY the exact JSON schema we designed
    llm_with_json = llm.with_structured_output(ClauseAnalysisOutput)
    
    # 3. Format the context arrays into clean strings
    cross_refs_text = "\n".join([f"- {ref}" for ref in state.get('direct_references', [])])
    rag_text = "\n".join(state.get('rag_results', []))
    web_text = "\n".join(state.get('web_results', []))
    feedback_text = state.get('verification_feedback', '')
    
    # 4. Build the massive prompt injecting all our data
    system_prompt = f"""You are an elite Legal AI Agent analyzing a contract clause.

Your job is NOT to summarize the clause.
Act as a careful legal analyst explaining the clause to a non-lawyer.

For every clause:
1. Explain what the clause actually means in extremely simple language.
2. Explain WHO is affected and WHAT they are required or allowed to do.
3. Explain the practical consequence of the clause.
4. Give 1-2 realistic real-world scenarios showing how the clause could affect someone.
5. Identify important words or phrases that create rights, obligations, restrictions, costs, or risks.
6. Explain what could go wrong for the affected party.
7. Explain what information from the rest of the contract changes the interpretation.
8. Only provide negotiation advice when there is a meaningful contractual issue that could reasonably be negotiated. Frame your advice as *possible options* rather than prescriptive commands. If no meaningful negotiation point exists, say so.
9. Do NOT invent facts that are not supported by the clause or retrieved context.
10. Clearly distinguish between:
   - what the contract says,
   - what the retrieved context establishes,
   - and general legal/market context.
11. If the available evidence is insufficient to determine something, say so explicitly.
12. For `document_citations`, you MUST include the CURRENT CHUNK ID as evidence.

RISK RUBRIC (You MUST use this logic to determine Risk Level):
- LOW: Standard boilerplate, no unusual financial/legal burden, balanced rights.
- MEDIUM: Noticeable financial/legal burden, vague conditions, or one-sided discretion (e.g., "at Management's discretion").
- HIGH: Severe financial exposure, immediate termination without cure, or highly unusual/punitive obligations.

CURRENT CHUNK ID (Use this as your primary document citation):
{state.get('chunk_id', 'None')}

DOCUMENT OVERVIEW:
{state.get('document_overview', 'None')}

CLAUSE TYPE: {state.get('clause_type', 'None')}

ORIGINAL TEXT TO ANALYZE:
"{state.get('original_text', 'None')}"

RESEARCHED CONTEXT (RAG):
{rag_text if rag_text else "None"}

RESEARCHED CONTEXT (WEB):
{web_text if web_text else "None"}

CROSS-REFERENCES:
{cross_refs_text if cross_refs_text else "None"}
"""

    # If the verification node previously rejected the analysis, inject its feedback so the LLM fixes it
    if feedback_text:
        system_prompt += f"\n\nCRITICAL FEEDBACK FROM VERIFIER (MUST FIX):\n{feedback_text}"

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="Generate the final JSON analysis for this clause.")
    ]

    # 5. Invoke the LLM to get the structured Pydantic object
    result = llm_with_json.invoke(messages)
    
    # 6. Convert the Pydantic object to a standard Python dictionary for the state
    return {"final_analysis": result.model_dump()}
