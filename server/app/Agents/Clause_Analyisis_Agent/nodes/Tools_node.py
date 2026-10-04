import logging
import json
from langchain_core.messages import ToolMessage
from app.Agents.Clause_Analyisis_Agent.state import AgentState
from app.Agents.Clause_Analyisis_Agent.tools import search_document, search_market_standards

logger = logging.getLogger(__name__)

def execute_tools_node(state: AgentState):
    logger.info(f"[NODE: Tools] Executing requested tools for Chunk {state['chunk_id']}")
    
    # Get the last message, which should be the AIMessage containing the tool calls
    last_message = state["messages"][-1]
    
    new_messages = []
    new_rag_results = []
    new_web_results = []
    
    # Process every tool call the LLM requested
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_call_id = tool_call["id"]
        
        logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
        
        try:
            if tool_name == "search_document":
                # Ensure document_id is injected if not provided by the LLM
                if "document_id" not in tool_args:
                    tool_args["document_id"] = state["document_id"]
                
                result = search_document.invoke(tool_args)
                new_rag_results.append(result)
                
                # LangChain requires a ToolMessage to prove to the LLM that the tool was executed
                new_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call_id))
                
            elif tool_name == "search_market_standards":
                result = search_market_standards.invoke(tool_args)
                new_web_results.append(result)
                
                new_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call_id))
                
            else:
                error_msg = f"Unknown tool: {tool_name}"
                logger.warning(error_msg)
                new_messages.append(ToolMessage(content=error_msg, tool_call_id=tool_call_id))
                
        except Exception as e:
            error_msg = f"Error executing {tool_name}: {str(e)}"
            logger.error(error_msg)
            new_messages.append(ToolMessage(content=error_msg, tool_call_id=tool_call_id))

    # We increment the tool call count to prevent infinite loops
    current_count = state.get("tool_call_count", 0) + 1

    # Return the updated state
    return {
        "messages": new_messages,
        "rag_results": new_rag_results,
        "web_results": new_web_results,
        "tool_call_count": current_count
    }
