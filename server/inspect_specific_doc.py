import json

with open('app/evaluation/chunks_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chunks = data.get('chunks', [])
refs = data.get('cross_references', [])

chunk_map = {c['id']: c for c in chunks}
doc_chunks = {}
for c in chunks:
    doc_chunks.setdefault(c['document_id'], []).append(c)

target_texts = [
    "Article 1", "Section 1", "Section 4", "11.1", "11.2", "11.3",
    "II-F", "II-D", "III", "III-B", "I-C", "Paragraph 18", "Paragraph 3(k)", "paragraph 13"
]

checked_docs = set()
for r in refs:
    if r['reference_text'] in target_texts and (not r.get('target_chunk_id') or r.get('link_type') == 'UNRESOLVED'):
        doc_id = r['document_id']
        if doc_id in checked_docs:
            print(f"  Also unresolved in doc {doc_id[:8]}: '{r['reference_text']}'")
            continue
        checked_docs.add(doc_id)
        print(f"\n==========================================")
        print(f"Doc {doc_id[:8]} - Unresolved ref: '{r['reference_text']}'")
        doc_c = doc_chunks.get(doc_id, [])
        print(f"Total chunks in doc: {len(doc_c)}")
        for c in doc_c:
            aliases = c.get('aliases') or []
            content_preview = (c.get('content') or "")[:60].replace('\n', ' ')
            print(f"   Chunk {c['id'][:8]} | aliases: {aliases} | text: {content_preview}")
