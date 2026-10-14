import json

with open('app/evaluation/chunks_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for r in data['cross_references']:
    if r['document_id'] == 'e6eb83ac-b3e5-4e22-b19a-089229bbcbb4':
        print(r['reference_text'], "-->", r['link_type'], "target:", r.get('target_chunk_id'))
