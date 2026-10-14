import sys
sys.path.append('.')
import uuid
from sentence_transformers import SentenceTransformer
from app.core.supabase import connectSupa
from app.evaluation.statutes_data import STATUTES_DATA

print("Initializing Supabase and SentenceTransformer...")
supabase = connectSupa()
model = SentenceTransformer('all-MiniLM-L6-v2')

# Fetch a valid user_id to satisfy FK constraint
user_res = supabase.table('files').select('user_id').limit(1).execute()
if not user_res.data:
    raise RuntimeError("No user_id found in files table.")
system_user_id = user_res.data[0]['user_id']

# Get or create 'Statutory / Regulatory' classification
class_res = supabase.table('classifications').select('id').eq('name', 'Statutory / Regulatory').execute()
if class_res.data and len(class_res.data) > 0:
    statutory_class_id = class_res.data[0]['id']
else:
    try:
        new_class = supabase.table('classifications').insert({
            'name': 'Statutory / Regulatory',
            'description': 'Public domain central and state acts, statutes, codes, and government rules.'
        }).execute()
        statutory_class_id = new_class.data[0]['id']
    except Exception:
        c_fetch = supabase.table('classifications').select('id').eq('name', 'Statutory / Regulatory').execute()
        statutory_class_id = c_fetch.data[0]['id']

print(f"Using Statutory Classification ID: {statutory_class_id}")

statute_file_map = {}

for stat in STATUTES_DATA:
    fname = stat["file_name"]
    print(f"\nProcessing Statute: {fname}...")
    
    # Check if already ingested
    existing = supabase.table('files').select('id').eq('file_name', fname).execute()
    if existing.data:
        file_id = existing.data[0]['id']
        print(f"  Statute file already exists: {file_id}")
    else:
        file_insert = supabase.table('files').insert({
            'user_id': system_user_id,
            'file_name': fname,
            'storage_path': f"statutes/{fname.replace(' ', '_').lower()}.txt",
            'content_type': 'text/plain',
            'status': 'COMPLETED',
            'raw_items': {'is_statutory': True, 'aliases': stat['aliases']}
        }).execute()
        file_id = file_insert.data[0]['id']
        print(f"  Created statute file entry: {file_id}")
        
    statute_file_map[fname] = file_id
    
    # Check existing chunks
    existing_chunks = supabase.table('chunks').select('id, chunk_no').eq('document_id', file_id).execute()
    existing_nos = {c['chunk_no']: c['id'] for c in existing_chunks.data}
    
    for sec in stat['sections']:
        c_no = sec['chunk_no']
        if c_no in existing_nos:
            print(f"    Chunk #{c_no} already exists.")
            continue
            
        aliases_str = ", ".join(sec['aliases'])
        rich_string = f"Category: Statutory / Regulatory | Known As: {aliases_str} | Content: {sec['text']}"
        embedding = model.encode(rich_string).tolist()
        
        c_res = supabase.table('chunks').insert({
            'document_id': file_id,
            'classification_id': statutory_class_id,
            'chunk_no': c_no,
            'text': sec['text'],
            'aliases': sec['aliases'],
            'embedding': embedding
        }).execute()
        print(f"    Inserted Chunk #{c_no} (ID: {c_res.data[0]['id'][:8]})")

print("\nAll 5 statutes successfully ingested into Supabase!")
