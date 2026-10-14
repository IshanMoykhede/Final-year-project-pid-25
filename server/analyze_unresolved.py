import json
import re

with open('app/evaluation/chunks_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chunks = data.get('chunks', [])
refs = data.get('cross_references', [])

chunk_by_doc = {}
for c in chunks:
    d = c['document_id']
    if d not in chunk_by_doc:
        chunk_by_doc[d] = []
    chunk_by_doc[d].append(c)

unresolved = [r for r in refs if r.get('link_type') == 'UNRESOLVED' or not r.get('target_chunk_id')]

print(f"Total unresolved: {len(unresolved)}")

# Check formatting/hierarchical candidates
print("\n--- Potential Hierarchical / Format Matches ---")
found_candidates = []
for r in unresolved:
    doc_chunks = chunk_by_doc.get(r['document_id'], [])
    ref_txt = r['reference_text'].strip()
    
    # Check parent section: e.g. "11.1" -> "Section 11" or "11" or "Article 11"
    # e.g. "II-F" -> "Section II" or "Article II"
    # e.g. "Article 1" -> why did Article 1 fail if doc has Article 1?
    
    doc_aliases = {}
    for c in doc_chunks:
        for a in (c.get('aliases') or []):
            doc_aliases[a.strip().lower()] = c['id']
            
    # Check if doc has Article 1
    if ref_txt.lower() in doc_aliases:
        print(f"Exact match exists but unlinked! Ref: '{ref_txt}' -> chunk {doc_aliases[ref_txt.lower()]}")
        found_candidates.append((r, "EXACT_UNLINKED", doc_aliases[ref_txt.lower()]))
        continue
        
    # Check sub-clause fallback: "11.1" -> "11", "Section 11", "Article 11"
    m_sub = re.match(r"^(\d+|[IVXLCDM]+)[\.\-](\w+)", ref_txt, re.IGNORECASE)
    if m_sub:
        parent_num = m_sub.group(1)
        # Check potential parent aliases
        parent_variants = [
            parent_num.lower(),
            f"section {parent_num.lower()}",
            f"clause {parent_num.lower()}",
            f"article {parent_num.lower()}",
            f"part {parent_num.lower()}"
        ]
        matched_parent = None
        for p in parent_variants:
            if p in doc_aliases:
                matched_parent = (p, doc_aliases[p])
                break
        if matched_parent:
            print(f"Hierarchical match: Ref '{ref_txt}' -> Parent '{matched_parent[0]}' (chunk {matched_parent[1][:8]})")
            found_candidates.append((r, f"HIERARCHICAL -> {matched_parent[0]}", matched_parent[1]))
            continue

    # Check Roman numeral / digit normalization: e.g. "III" -> "Section 3" or "Article III"
    # e.g. "Article 1" vs "Article I"
    # e.g. "Section 4(a)" vs "Section 4"
    m_sec_sub = re.match(r"^(section|clause|article)\s*(\d+|[IVXLCDM]+)[\.\(](.+)", ref_txt, re.IGNORECASE)
    if m_sec_sub:
        p_type = m_sec_sub.group(1).lower()
        p_num = m_sec_sub.group(2).lower()
        parent_key = f"{p_type} {p_num}"
        if parent_key in doc_aliases:
            print(f"Hierarchical section match: Ref '{ref_txt}' -> Parent '{parent_key}' (chunk {doc_aliases[parent_key][:8]})")
            found_candidates.append((r, f"HIERARCHICAL -> {parent_key}", doc_aliases[parent_key]))
            continue

print(f"\nTotal potential resolvable by fuzzy/hierarchy: {len(found_candidates)}")
