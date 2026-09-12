import os
import json
from app.core.supabase import connectSupa

def inspect_all_docs():
    supabase = connectSupa()
    files_res = supabase.table("files").select("id, file_name").order("created_at", desc=True).limit(6).execute()
    
    for f in files_res.data:
        doc_id = f["id"]
        fname = f["file_name"]
        
        chunks_res = supabase.table("chunks") \
            .select("id, chunk_no, aliases, text") \
            .eq("document_id", doc_id) \
            .order("chunk_no") \
            .execute()
        chunks = chunks_res.data
        id_to_chunk = {c["id"]: c for c in chunks}
        
        refs_res = supabase.table("cross_references") \
            .select("source_chunk_id, target_chunk_id, reference_text, link_type") \
            .eq("document_id", doc_id) \
            .execute()
        
        resolved = [r for r in refs_res.data if r.get("target_chunk_id") and r["target_chunk_id"] in id_to_chunk]
        print(f"\nDocument: {fname} (ID: {doc_id})")
        print(f"Total Chunks: {len(chunks)}, Resolved Links: {len(resolved)}")
        for r in resolved:
            src = id_to_chunk[r["source_chunk_id"]]
            tgt = id_to_chunk[r["target_chunk_id"]]
            print(f"  Chunk {src['chunk_no']} ({src['aliases']}) -> Chunk {tgt['chunk_no']} ({tgt['aliases']}) via '{r['reference_text']}'")

if __name__ == "__main__":
    inspect_all_docs()
