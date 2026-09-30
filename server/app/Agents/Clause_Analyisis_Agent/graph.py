import logging
from langgraph.graph import StateGraph, END
from app.Agents.Clause_Analyisis_Agent.state import AgentState
from app.Agents.Clause_Analyisis_Agent.nodes.Router_node import intent_router_node
from app.Agents.Clause_Analyisis_Agent.nodes.Tools_node import execute_tools_node
from app.Agents.Clause_Analyisis_Agent.nodes.Analysis_node import analysis_node

logger = logging.getLogger(__name__)

def route_from_router(state: AgentState):
    """
    Traffic Cop function: Looks at what the Router LLM just outputted, 
    and decides where the graph should go next.
    """
    last_message = state["messages"][-1]
    
    # Check if the LLM outputted tool calls
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        # Check if the LLM called our fake 'proceed_to_analysis' tool
        for tool in last_message.tool_calls:
            if tool["name"] == "proceed_to_analysis":
                logger.info("[ROUTER] LLM has enough context. Routing to Analysis Node.")
                return "analysis_node"
        
        # If it wasn't the fake tool, it must be a real tool (search_document etc.)
        logger.info("[ROUTER] LLM requested search. Routing to Tools Node.")
        return "tools_node"
    
    # Fallback: If it didn't use tools and just replied with text, force it to analysis
    logger.info("[ROUTER] No tool calls found. Forcing route to Analysis Node.")
    return "analysis_node"

def build_clause_agent_graph():
    """
    Wires all the nodes together into a LangGraph executable application.
    """
    builder = StateGraph(AgentState)
    
    # 1. Add our Nodes
    builder.add_node("intent_router_node", intent_router_node)
    builder.add_node("tools_node", execute_tools_node)
    builder.add_node("analysis_node", analysis_node)
    
    # 2. Set the Entry Point (where the graph starts)
    builder.set_entry_point("intent_router_node")
    
    # 3. Add the Traffic Cop Edge from the Router
    builder.add_conditional_edges(
        "intent_router_node",
        route_from_router,
        {
            "tools_node": "tools_node",
            "analysis_node": "analysis_node"
        }
    )
    
    # 4. Add standard Edges
    # When the tools finish searching, they MUST loop back to the router
    builder.add_edge("tools_node", "intent_router_node")
    
    # When the analysis is done, the agent's job is complete
    builder.add_edge("analysis_node", END)
    
    # 5. Compile and return the executable graph
    return builder.compile()
