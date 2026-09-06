import os
import tempfile

from llama_cloud import LlamaCloud
from app.core.supabase import connectSupa


def process_document(file_id: str):

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
        llama_file = client.files.create(
            file=temp_path,
            purpose="parse"
        )

        # Parse document
        result = client.parsing.parse(
            file_id=llama_file.id,
            tier="agentic",
            version="latest",
            expand=["markdown_full", "text_full", "items"]
        )

        # Update database with raw markdown
        (
            supabase
            .table("files")
            .update({"raw_markdown": result.markdown_full or ""})
            .eq("id", file_id)
            .execute()
        )

        return {
            "markdown": result.markdown_full or "",
            "text": result.text_full or "",
            "raw_llama_json": getattr(result, "items", [])
        }

    finally:
        # Delete temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)