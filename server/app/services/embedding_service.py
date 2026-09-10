from app.core.supabase import connectSupa
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

# Initialize the model once globally so it doesn't reload into memory on every request
# all-MiniLM-L6-v2 is extremely fast and generates 384-dimensional vectors
try:
    logger.info("[EMBEDDING_SERVICE] Loading all-MiniLM-L6-v2 HuggingFace model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    logger.error(f"[EMBEDDING_SERVICE] Failed to load embedding model: {e}")
    model = None

def generate_embeddings(file_id: str):
    logger.info(f"[EMBEDDING_SERVICE] Starting embedding generation for document_id: {file_id}")
    supabase = connectSupa()

    if model is None:
        logger.error("[EMBEDDING_SERVICE] Embedding model is not loaded. Skipping embeddings.")
        return False

    # 1. Fetch all chunks for this document
    response = (
        supabase
        .table("chunks")
        .select("id, text, aliases, classification_id")
        .eq("document_id", file_id)
        .execute()
    )
    
    chunks = response.data
    if not chunks:
        logger.warning(f"[EMBEDDING_SERVICE] No chunks found for document_id: {file_id}")
        return False

    logger.info(f"[EMBEDDING_SERVICE] Found {len(chunks)} chunks. Formatting rich context strings...")

    # We also want the actual classification name, not just the ID, for maximum semantic value.
    # So let's fetch all classifications to map them.
    class_res = supabase.table("classifications").select("id, name").execute()
    class_map = {c["id"]: c["name"] for c in class_res.data}

    updates = []

    # 2. Iterate and create rich strings
    for chunk in chunks:
        # Build the rich text
        class_name = class_map.get(chunk.get("classification_id"), "Unclassified")
        aliases = chunk.get("aliases") or []
        aliases_str = ", ".join(aliases)
        text = chunk.get("text") or ""
        
        # This string design physically forces semantic meaning into the vector!
        rich_string = f"Category: {class_name} | Known As: {aliases_str} | Content: {text}"

        # 3. Generate the 384-dimensional vector
        embedding_vector = model.encode(rich_string).tolist()

        # Update the row individually to avoid wiping out other columns
        try:
            (
                supabase
                .table("chunks")
                .update({"embedding": embedding_vector})
                .eq("id", chunk["id"])
                .execute()
            )
        except Exception as e:
            logger.error(f"[EMBEDDING_SERVICE] Failed to update chunk {chunk['id']}: {e}")
            raise e

    logger.info(f"[EMBEDDING_SERVICE] Successfully saved {len(chunks)} embeddings to the database!")
    return True
