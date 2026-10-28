import re
import math
from collections import Counter

def chunk_document_contents(study_material_id, page_contents, chunk_size=500, overlap=100):
    """
    Chunks document page by page into overlapping segments.
    Returns a list of dicts: [{ study_material_id, page_number, chunk_index, text }]
    """
    chunks = []
    global_chunk_idx = 0
    
    if isinstance(page_contents, str):
        import json
        try:
            page_contents = json.loads(page_contents)
        except Exception:
            page_contents = [{"page": 1, "text": page_contents}]

    for page_obj in page_contents:
        page_num = page_obj.get("page", 1)
        text = page_obj.get("text", "")
        
        if not text or not text.strip():
            continue
            
        # Split into paragraphs or sentences first
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        
        current_chunk = ""
        for p in paragraphs:
            if len(current_chunk) + len(p) + 1 <= chunk_size:
                current_chunk = (current_chunk + "\n" + p).strip()
            else:
                if current_chunk:
                    chunks.append({
                        "study_material_id": study_material_id,
                        "page_number": page_num,
                        "chunk_index": global_chunk_idx,
                        "text": current_chunk
                    })
                    global_chunk_idx += 1
                    
                    # keep overlap from end of current_chunk
                    current_chunk = current_chunk[-overlap:] + "\n" + p
                else:
                    # Single paragraph is longer than chunk_size, split by characters
                    for i in range(0, len(p), chunk_size - overlap):
                        chunk_text = p[i:i + chunk_size]
                        chunks.append({
                            "study_material_id": study_material_id,
                            "page_number": page_num,
                            "chunk_index": global_chunk_idx,
                            "text": chunk_text
                        })
                        global_chunk_idx += 1
                    current_chunk = ""
                    
        if current_chunk.strip():
            chunks.append({
                "study_material_id": study_material_id,
                "page_number": page_num,
                "chunk_index": global_chunk_idx,
                "text": current_chunk.strip()
            })
            global_chunk_idx += 1

    return chunks


def _tokenize(text):
    return re.findall(r'\b[a-zA-Z0-9_]+\b', text.lower())

def calculate_cosine_similarity(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])
    sum1 = sum([vec1[x]**2 for x in vec1.keys()])
    sum2 = sum([vec2[x]**2 for x in vec2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    if not denominator:
        return 0.0
    return float(numerator) / denominator

def retrieve_relevant_chunks(query, chunks, top_k=5, min_score=0.01):
    """
    Search and rank document chunks based on TF-IDF / keyword similarity.
    Returns: list of (chunk_obj, relevance_score)
    """
    if not query or not chunks:
        return []

    query_tokens = _tokenize(query)
    if not query_tokens:
        return [(c, 0.5) for c in chunks[:top_k]]
        
    query_vec = Counter(query_tokens)
    
    scored_chunks = []
    for chunk in chunks:
        chunk_text = chunk.text if hasattr(chunk, 'text') else chunk.get('text', '')
        chunk_tokens = _tokenize(chunk_text)
        if not chunk_tokens:
            continue
            
        chunk_vec = Counter(chunk_tokens)
        sim = calculate_cosine_similarity(query_vec, chunk_vec)
        
        # Give extra boost if exact phrase query appears in chunk text
        if query.lower() in chunk_text.lower():
            sim += 0.5
            
        if sim > min_score:
            scored_chunks.append((chunk, round(sim, 3)))
            
    # Sort by score descending
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    
    if not scored_chunks:
        # Fallback to top_k chunks if keyword match was sparse
        return [(c, 0.1) for c in chunks[:top_k]]
        
    return scored_chunks[:top_k]
