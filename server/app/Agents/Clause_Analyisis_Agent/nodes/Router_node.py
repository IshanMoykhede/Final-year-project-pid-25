import logging
import os
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from app.Agents.Clause_Analyisis_Agent.state import AgentState
from app.Agents.Clause_Analyisis_Agent.tools import search_document, search_market_standards

logger = logging.getLogger(__name__)

# 1. The "Fake Tool" for routing to the Analysis Node (No OOP/Classes used)
def proceed_to_analysis(reasoning: str) -> str:
    """
    Call this tool ONLY when you have gathered all the information you need and are ready to generate the final analysis.
    The reasoning argument should explain exactly why you have enough context and do not need to use any more search tools.
    """
    return "Proceeding to analysis"

# 2. The Router Node Function
def intent_router_node(state: AgentState):
    logger.info(f"[NODE: Router] Analyzing Chunk {state['chunk_id']}")
    
    # Initialize the Groq LLM (we recommend openai/gpt-oss-20b for complex routing)
    llm = ChatGroq(
        api_key=os.environ.get("GROQ_API_KEY"), 
        model="openai/gpt-oss-20b",
        temperature=0.1
    )
    
    # Bind the tools to the LLM
    tools = [search_document, search_market_standards, proceed_to_analysis]
    llm_with_tools = llm.bind_tools(tools)
    
    # Format the context from the State
    cross_refs_text = "\n".join([f"- {ref}" for ref in state.get('direct_references', [])])
    rag_text = "\n".join(state.get('rag_results', []))
    web_text = "\n".join(state.get('web_results', []))
    
    # Build the System Prompt
    system_prompt = f"""You are an elite Legal AI Agent analyzing a contract.
Your current task is to read a specific clause and decide if you have enough information to fully explain it to a non-lawyer, assess its risk, and provide negotiation advice.

DOCUMENT OVERVIEW:
{state['document_overview']}

CLAUSE TYPE: {state['clause_type']}

ORIGINAL TEXT TO ANALYZE:
"{state['original_text']}"

KNOWN CROSS-REFERENCES (Exact Matches from Database):
{cross_refs_text if cross_refs_text else "None"}

PREVIOUS SEARCH RESULTS (RAG):
{rag_text if rag_text else "None"}

PREVIOUS SEARCH RESULTS (WEB):
{web_text if web_text else "None"}

INSTRUCTIONS:
1. If the clause references another section of the document that you haven't read yet, you MUST call 'search_document'.
2. If the clause uses ambiguous legal jargon or you need to know market standards, you MUST call 'search_market_standards'.
3. If you fully understand the clause and do not need any more information, you MUST call 'proceed_to_analysis'.
"""

    # We add a fail-safe to prevent infinite loops. If it has searched 3 times, FORCE it to proceed.
    if state.get("tool_call_count", 0) >= 2:
        system_prompt += "\nCRITICAL: You have reached the maximum search limit (3). You MUST call 'proceed_to_analysis' immediately using the context you currently have."

    messages = [SystemMessage(content=system_prompt)]
    
    # Include conversation history if there is any (so the LLM remembers why it called a tool)
    if state.get("messages"):
        messages.extend(state["messages"])
    else:
        # If no history, this is the first turn. Add a Human message to kick it off.
        messages.append(HumanMessage(content="Review the clause and decide what to do next."))

    # Invoke the LLM
    response = llm_with_tools.invoke(messages)
    
    # Return the updated state. We append the LLM's response to the messages history.
    return {"messages": [response]}
