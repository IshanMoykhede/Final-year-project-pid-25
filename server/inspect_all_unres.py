import json

with open('app/evaluation/chunks_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chunks = data.get('chunks', [])
refs = data.get('cross_references', [])

unresolved = [r for r in refs if r.get('link_type') == 'UNRESOLVED' or not r.get('target_chunk_id')]

print(f"Total unresolved in chunks_data.json: {len(unresolved)}")
all_unres_texts = set(r['reference_text'] for r in unresolved)
print("Unique unresolved reference texts:")
for t in sorted(all_unres_texts):
    count = sum(1 for r in unresolved if r['reference_text'] == t)
    print(f"  [{count}x] {t}")
