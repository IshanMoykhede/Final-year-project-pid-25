import logging
from app.core.supabase import connectSupa

logger = logging.getLogger(__name__)

ROMAN_MAP = {
    'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5,
    'vi': 6, 'vii': 7, 'viii': 8, 'ix': 9, 'x': 10,
    'xi': 11, 'xii': 12, 'xiii': 13, 'xiv': 14, 'xv': 15,
    'xvi': 16, 'xvii': 17, 'xviii': 18, 'xix': 19, 'xx': 20
}

def extract_section_number(text: str):
    """
    Extracts numerical identifier from legal references such as:
    'Section 18' -> 18
    'Paragraph 18' -> 18
    '11.1' -> 11
    'Article IV' -> 4
    'Clause 3(k)' -> 3
    """
    import re
    if not text:
        return None
    s = text.strip().lower()
    
    # Prefix + number or roman numeral: "Section 18", "Paragraph 3(k)", "Article IV"
    m = re.search(r'\b(?:section|article|clause|paragraph|para|part)\s*(\d+|[ivx]+)\b', s)
    if m:
        val = m.group(1)
        if val in ROMAN_MAP:
            return ROMAN_MAP[val]
        try:
            return int(val)
        except ValueError:
            pass

    # Standalone decimal: "11.1", "11.2"
    m_dec = re.match(r'^(\d+)[\.\-](\d+)', s)
    if m_dec:
        return int(m_dec.group(1))

    # Roman numeral prefix: "II-F", "III-B"
    m_rom = re.match(r'^([ivx]+)[\.\-]', s)
    if m_rom and m_rom.group(1) in ROMAN_MAP:
        return ROMAN_MAP[m_rom.group(1)]

    # Standalone Roman numeral: "III"
    if s in ROMAN_MAP:
        return ROMAN_MAP[s]

    if s.isdigit():
        return int(s)

    return None

def find_target_chunk(ref_text: str, chunks: list):
    """
    Attempts deterministic match, prefix/fuzzy alias match,
    and hierarchical section-number fallback.
    """
    import re
    clean_ref = re.sub(r'[^\w\s]', '', ref_text.lower()).strip()
    if not clean_ref:
        return None, None

    # Step 1: Exact alias match (case insensitive)
    for chunk in chunks:
        chunk_aliases = chunk.get("aliases") or []
        if any(alias.strip().lower() == ref_text.strip().lower() for alias in chunk_aliases):
            return chunk["id"], "EXACT_MATCH"

    # Step 2: Normalized prefix / substring match
    # Example: ref "Article 1" matches alias "ARTICLE 1 – BASIC LEASE TERMS"
    # Example: ref "11.1" matches alias "11.1 Tenant's Insurance"
    for chunk in chunks:
        chunk_aliases = chunk.get("aliases") or []
        for alias in chunk_aliases:
            clean_alias = re.sub(r'[^\w\s]', '', alias.lower()).strip()
            if clean_ref == clean_alias or clean_alias.startswith(clean_ref):
                return chunk["id"], "EXACT_MATCH"
            # Whole-word substring match for citations longer than 4 chars
            if len(clean_ref) >= 4 and re.search(r'\b' + re.escape(clean_ref) + r'\b', clean_alias):
                return chunk["id"], "EXACT_MATCH"

    # Step 3: Hierarchical parent match
    # Example: ref "Paragraph 18" or "18.1" matches chunk with alias "Section 18"
    ref_num = extract_section_number(ref_text)
    if ref_num is not None:
        for chunk in chunks:
            chunk_aliases = chunk.get("aliases") or []
            for alias in chunk_aliases:
                chunk_num = extract_section_number(alias)
                if chunk_num is not None and chunk_num == ref_num:
                    return chunk["id"], "HIERARCHICAL_MATCH"

    return None, None

def resolve_cross_references(file_id: str):
    """
    Connects the bridge! Finds unresolved references and tries to match them
    to:
      1. Intra-document chunks (exact, fuzzy-prefix, and hierarchical fallback)
      2. Ingested statutory knowledge base chunks (STATUTORY_MATCH)
    """
    logger.info(f"Starting cross-reference resolution for document_id: {file_id}")
    supabase = connectSupa()
    
    # 1. Fetch all chunks and their aliases for this document
    chunks_result = supabase.table("chunks").select("id, aliases").eq("document_id", file_id).execute()
    chunks = chunks_result.data
    
    if not chunks:
        logger.warning(f"No chunks found to link for document_id: {file_id}")
        return
        
    # 2. Fetch all unresolved or AI_SUGGESTED references for this document
    refs_result = supabase.table("cross_references") \
        .select("id, reference_text, link_type") \
        .eq("document_id", file_id) \
        .in_("link_type", ["AI_SUGGESTED", "UNRESOLVED"]) \
        .execute()
        
    references = refs_result.data
    
    if not references:
        logger.info("No unresolved references found to resolve.")
        return
        
    logger.info(f"Found {len(references)} references to evaluate for resolution.")

    # Pre-fetch statutory chunks for external statutory linking
    statutory_files_res = supabase.table("files").select("id, file_name, raw_items").execute()
    statutory_file_ids = [
        f["id"] for f in (statutory_files_res.data or [])
        if f.get("raw_items") and isinstance(f["raw_items"], dict) and f["raw_items"].get("is_statutory")
    ]
    statutory_chunks = []
    if statutory_file_ids:
        stat_chunks_res = supabase.table("chunks").select("id, aliases, document_id").in_("document_id", statutory_file_ids).execute()
        statutory_chunks = stat_chunks_res.data or []
    
    resolved_count = 0
    unresolved_count = 0
    
    # 3. Match each reference to a chunk
    for ref in references:
        ref_id = ref["id"]
        ref_text = ref["reference_text"]
        
        # Step 3a: Intra-document match
        target_chunk_id, link_type = find_target_chunk(ref_text, chunks)

        # Step 3b: If not matched in doc, check Statutory Knowledge Base
        if not target_chunk_id and statutory_chunks:
            stat_target, _ = find_target_chunk(ref_text, statutory_chunks)
            if stat_target:
                target_chunk_id = stat_target
                link_type = "STATUTORY_MATCH"
                
        # 4. Update the database
        if target_chunk_id:
            supabase.table("cross_references").update({
                "target_chunk_id": target_chunk_id,
                "link_type": link_type
            }).eq("id", ref_id).execute()
            resolved_count += 1
        else:
            supabase.table("cross_references").update({
                "link_type": "UNRESOLVED"
            }).eq("id", ref_id).execute()
            unresolved_count += 1
            
    logger.info(f"Resolution complete: {resolved_count} resolved, {unresolved_count} UNRESOLVED.")
    
    return {
        "resolved": resolved_count,
        "unresolved": unresolved_count
    }
