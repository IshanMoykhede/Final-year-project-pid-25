import os
import tempfile
import logging

from llama_cloud import LlamaCloud
from app.core.supabase import connectSupa

logger = logging.getLogger(__name__)

def process_document(file_id: str):
    logger.info(f"Starting OCR processing for file_id: {file_id}")

    supabase = connectSupa()

    # Get file information from database
    result = (
        supabase
        .table("files")
        .select("*")
        .eq("id", file_id)
        .single()
        .execute()
    )

    file = result.data

    if not file:
        raise ValueError("File not found")

    # Download file from Supabase Storage
    file_data = (
        supabase
        .storage
        .from_("Files")
        .download(file["storage_path"])
    )

    # Save temporarily
    extension = file["file_name"].split(".")[-1]

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=f".{extension}"
    ) as temp_file:

        temp_file.write(file_data)
        temp_path = temp_file.name

    try:
        # Connect to LlamaCloud
        client = LlamaCloud(
            api_key=os.getenv("LLAMA_CLOUD_API_KEY")
        )

        # Upload file to LlamaCloud
        logger.info(f"Uploading file_id: {file_id} to LlamaCloud")
        llama_file = client.files.create(
            file=temp_path,
            purpose="parse"
        )

        # Parse document
        logger.info(f"Parsing document for file_id: {file_id} (LlamaCloud File ID: {llama_file.id})")
        result = client.parsing.parse(
            file_id=llama_file.id,
            tier="agentic",
            version="latest",
            expand=["markdown_full", "text_full", "items"]
        )

        # Safely convert the entire result to a dict first to avoid serialization errors
        result_dict = result.model_dump() if hasattr(result, "model_dump") else result.dict() if hasattr(result, "dict") else {}
        raw_items_list = result_dict.get("items", [])
        
        (
            supabase
            .table("files")
            .update({
                "raw_items": raw_items_list
            })
            .eq("id", file_id)
            .execute()
        )
        logger.info(f"Successfully stored {len(raw_items_list)} OCR items for file_id: {file_id}")

        return {
            "markdown": result.markdown_full or "",
            "text": result.text_full or "",
            "raw_llama_json": getattr(result, "items", [])
        }
        
    except Exception as e:
        logger.exception(f"OCR processing failed for file_id: {file_id}")
        raise

    finally:
        # Delete temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)