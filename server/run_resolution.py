import sys
sys.path.append('.')
from app.core.supabase import connectSupa
from app.services.linking_service import resolve_cross_references

supabase = connectSupa()
docs_res = supabase.table('files').select('id, file_name').execute()
docs = docs_res.data or []
print(f"Found {len(docs)} files in Supabase.")

total_newly_resolved = 0
total_unresolved = 0
for d in docs:
    res = resolve_cross_references(d['id'])
    if res:
        if res.get('resolved', 0) > 0:
            print(f"Document '{d.get('filename')}': resolved {res['resolved']} citations, {res.get('unresolved', 0)} unresolved")
            total_newly_resolved += res['resolved']
        total_unresolved += res.get('unresolved', 0)

print(f"\nFinal tally across DB: {total_newly_resolved} newly resolved, {total_unresolved} unresolved.")
