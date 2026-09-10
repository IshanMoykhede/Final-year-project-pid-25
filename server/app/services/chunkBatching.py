import tiktoken
import logging
from typing import List

logger = logging.getLogger(__name__)

def count_tokens(text: str) -> int:
    """
    Counts the approximate number of tokens in a string using tiktoken.
    Using 'cl100k_base' which is standard for most modern LLMs (GPT-4, Llama 3 via Groq).
    """
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception as e:
        logger.warning(f"Error counting tokens: {e}. Falling back to character approximation.")
        # Fallback approximation: 1 token ~= 4 chars
        return len(text) // 4

def create_batches(chunks: List[dict], max_tokens_per_batch: int = 6000) -> List[List[dict]]:
    """
    Takes a list of chunk dictionaries and groups them into batches.
    Ensures that the total token count of the text in each batch 
    does not exceed max_tokens_per_batch.
    """
    logger.info(f"[BATCHING_SERVICE] Initializing TikToken Engine to pack {len(chunks)} chunks into {max_tokens_per_batch}-token batches...")
    encoding = tiktoken.get_encoding("cl100k_base")
    
    batches = []
    current_batch = []
    current_batch_tokens = 0
    
    for chunk in chunks:
        text = chunk.get("text", "")
        # Add some padding for the JSON overhead and prompt instructions
        token_count = count_tokens(text) + 50 

        if current_batch_tokens + token_count > max_tokens_per_batch and len(current_batch) > 0:
            # Batch is full, save it and start a new one
            batches.append(current_batch)
            current_batch = [chunk]
            current_batch_tokens = token_count
        else:
            current_batch.append(chunk)
            current_batch_tokens += token_count

    # Don't forget to add the last batch!
    if len(current_batch) > 0:
        batches.append(current_batch)

    logger.info(f"[BATCHING_SERVICE] Successfully packed {len(chunks)} chunks into {len(batches)} optimal batches!")
    return batches
