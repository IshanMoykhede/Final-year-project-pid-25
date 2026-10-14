import json
import re

with open('app/evaluation/chunks_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chunks = data.get('chunks', [])
refs = data.get('cross_references', [])

chunk_by_doc = {}
for c in chunks:
    chunk_by_doc.setdefault(c['document_id'], []).append(c)

ROMAN_MAP = {
    'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5,
    'vi': 6, 'vii': 7, 'viii': 8, 'ix': 9, 'x': 10,
    'xi': 11, 'xii': 12, 'xiii': 13, 'xiv': 14, 'xv': 15,
    'xvi': 16, 'xvii': 17, 'xviii': 18, 'xix': 19, 'xx': 20
}

def normalize_key(s):
    if not s:
        return ""
    s = s.strip().lower()
    # replace dashes/periods with spaces or clean them
    s = re.sub(r'[\(\)\[\]\,\.\-\–\—]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def extract_section_numbers(s):
    """
    Extracts numerical and structural identifiers like:
    'Section 18' -> 18
    'Paragraph 18' -> 18
    '11.1' -> (11, 1) or '11'
    'Article I' -> 1
    'II-F' -> 2
    """
    s = s.strip().lower()
    # Check for prefix + number/roman
    m = re.search(r'\b(?:section|article|clause|paragraph|para|part)\s*(\d+|[ivx]+)\b', s)
    if m:
        val = m.group(1)
        if val in ROMAN_MAP:
            return (ROMAN_MAP[val], val)
        try:
            return (int(val), str(val))
        except:
            pass
            
    # Check for standalone decimal like 11.1, 11.2
    m2 = re.match(r'^(\d+)[\.\-](\d+)', s)
    if m2:
        return (int(m2.group(1)), m2.group(1))
        
    # Check Roman numeral with hyphen like II-F, III-B
    m3 = re.match(r'^([ivx]+)[\.\-]', s)
    if m3:
        val = m3.group(1)
        if val in ROMAN_MAP:
            return (ROMAN_MAP[val], val)
            
    # Check pure Roman numeral like 'III'
    if s in ROMAN_MAP:
        return (ROMAN_MAP[s], s)
        
    # Check pure number
    if s.isdigit():
        return (int(s), s)
        
    return None

unresolved = [r for r in refs if r.get('link_type') == 'UNRESOLVED' or not r.get('target_chunk_id')]

print(f"Total unresolved: {len(unresolved)}")

potential_resolutions = []

for r in unresolved:
    ref_txt = r['reference_text'].strip()
    doc_id = r['document_id']
    doc_c = chunk_by_doc.get(doc_id, [])
    
    # 1. Clean string match (ignoring special chars like , dashes, casing)
    clean_ref = re.sub(r'[^\w\s]', '', ref_txt.lower()).strip()
    
    matched = None
    match_reason = None
    
    # Direct match after cleaning
    for c in doc_c:
        for a in (c.get('aliases') or []):
            clean_a = re.sub(r'[^\w\s]', '', a.lower()).strip()
            # If ref is "Article 1" and alias is "Article 1 Basic Lease Terms"
            if clean_ref == clean_a or clean_a.startswith(clean_ref) or (len(clean_ref) > 5 and clean_ref in clean_a):
                # Ensure it's not a false positive like '1' in '10'
                if re.search(r'\b' + re.escape(clean_ref) + r'\b', clean_a):
                    matched = c
                    match_reason = f"Fuzzy/Prefix alias match: '{a}'"
                    break
        if matched:
            break
            
    # 2. Structural / Hierarchical match
    if not matched:
        num_info = extract_section_numbers(ref_txt)
        if num_info:
            num_val, num_str = num_info
            for c in doc_c:
                for a in (c.get('aliases') or []):
                    c_num_info = extract_section_numbers(a)
                    if c_num_info and c_num_info[0] == num_val:
                        matched = c
                        match_reason = f"Hierarchical Section #{num_val} match: '{a}'"
                        break
                if matched:
                    break
                    
    if matched:
        potential_resolutions.append({
            'ref_id': r['id'],
            'ref_text': ref_txt,
            'doc_id': doc_id[:8],
            'target_chunk_id': matched['id'],
            'reason': match_reason
        })

print(f"\nDiscovered {len(potential_resolutions)} resolvable citations out of {len(unresolved)} unresolved:")
for res in potential_resolutions:
    print(f"  [{res['doc_id']}] '{res['ref_text']}' -> Chunk {res['target_chunk_id'][:8]} via {res['reason']}")
