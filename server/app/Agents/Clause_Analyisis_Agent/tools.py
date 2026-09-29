import logging
from langchain_core.tools import tool
from typing import Optional
from app.core.supabase import connectSupa
from app.services.embedding_service import model

logger = logging.getLogger(__name__)

@tool
def search_document(query: str, document_id: str) -> str:
    """
    Search the current document for specific clauses or information using semantic RAG.
    Use this when you need to read other parts of the contract to understand the current clause.
    Returns the top 3 most relevant clauses from the document.
    """
    logger.info(f"[TOOL] Searching document {document_id} for: {query}")
    supabase = connectSupa()
    
    if not model:
        return "Error: Embedding model is not loaded. Cannot perform semantic search."

    try:
        # Encode the search query
        query_vector = model.encode(query).tolist()
        
        # Call the Supabase native pgvector RPC function
        response = supabase.rpc(
            "match_chunks",
            {
                "query_embedding": query_vector,
                "match_threshold": 0.5,
                "match_count": 3,
                "filter_document_id": document_id
            }
        ).execute()
        
        results = response.data
        if not results:
            return "No text found in the document to search."
            
        # Format for the LLM
        formatted_output = "DOCUMENT SEARCH RESULTS:\n"
        for i, r in enumerate(results):
            aliases_str = ", ".join(r.get("aliases", [])) if r.get("aliases") else "Unknown"
            chunk_id = r.get("id", "Unknown")
            formatted_output += f"\n--- Result {i+1} (Similarity: {r.get('similarity', 0):.2f}) ---\n"
            formatted_output += f"Citation ID: {chunk_id}\n"
            formatted_output += f"Section/Aliases: {aliases_str}\n"
            formatted_output += f"Text: {r['text']}\n"
            
        return formatted_output
        
    except Exception as e:
        logger.error(f"[TOOL ERROR] search_document failed: {e}")
        return f"Search failed with error: {str(e)}"

@tool
def search_market_standards(query: str) -> str:
    """
    Search the internet for market standards, standard legal definitions, or legal precedents.
    Use this ONLY when the clause contains ambiguous legal terms or you need to know what is "standard" in the industry.
    """
    logger.info(f"[TOOL] Searching Web for: {query}")
    
    try:
        from langchain_community.tools.tavily_search import TavilySearchResults
        import os
        
        if not os.environ.get("TAVILY_API_KEY"):
            return "Error: TAVILY_API_KEY is not set in the environment. Cannot search the web."
            
        tavily_tool = TavilySearchResults(max_results=2)
        results = tavily_tool.invoke({"query": query})
        
        formatted_output = "WEB SEARCH RESULTS:\n"
        if isinstance(results, list):
            for i, r in enumerate(results):
                formatted_output += f"\n--- Result {i+1} ---\n"
                formatted_output += f"Source: {r.get('url', 'Unknown')}\n"
                formatted_output += f"Content: {r.get('content', '')}\n"
        else:
            formatted_output += str(results)
            
        return formatted_output
        
    except Exception as e:
        logger.error(f"[TOOL ERROR] search_market_standards failed: {e}")
        return f"Web search failed with error: {str(e)}"
