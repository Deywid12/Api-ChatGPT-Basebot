import os, json, uuid, re
import numpy as np
from typing import List, Dict, Any, Optional
from tiktoken import get_encoding
from sklearn.metrics.pairwise import cosine_similarity

from schema import Item
from openai_client import embed_texts

DATA_DIR = "data"
CORPUS_PATH = os.path.join(DATA_DIR, "corpus.jsonl")
VECTORS_PATH = os.path.join(DATA_DIR, "vectors.npy")
META_PATH = os.path.join(DATA_DIR, "meta.json")

# Runtime globals
V = None             # np.ndarray (N, D)
META: List[Dict[str, Any]] = []

def _ensure_fs():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CORPUS_PATH):
        open(CORPUS_PATH, "a", encoding="utf-8").close()

def _token_chunks(text: str, max_tokens: int = 400):
    enc = get_encoding("cl100k_base")
    tokens = enc.encode(text or "")
    for i in range(0, len(tokens), max_tokens):
        yield enc.decode(tokens[i:i+max_tokens])

def _to_records(item: Item) -> List[Dict[str, Any]]:
    fulltext = "\n".join(filter(None, [
        f"Título: {item.titulo}",
        f"Classe: {item.classe}",
        f"Por que ocorre: {item.porque_ocorre}",
        f"Tratativa: {item.tratativa}",
        f"Resolução: {item.resolucao}",
        f"Identificadores: {', '.join(item.identificadores)}",
        f"Fonte: {item.link_da_base}"
    ]))
    recs = []
    for ch in _token_chunks(fulltext, 350):
        recs.append({
            "id": str(uuid.uuid4()),
            "classe": item.classe,
            "titulo": item.titulo,
            "chunk": ch,
            "source": item.link_da_base or item.titulo,
            "identificadores": item.identificadores,
        })
    return recs

def ingest_items(items: List[Item]) -> Dict[str, Any]:
    _ensure_fs()
    records = []
    for it in items:
        records.extend(_to_records(it))

    with open(CORPUS_PATH, "a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    embeddings = embed_texts([r["chunk"] for r in records])
    E = np.array(embeddings, dtype=np.float32)

    global V, META
    if os.path.exists(VECTORS_PATH) and os.path.exists(META_PATH):
        V_prev = np.load(VECTORS_PATH)
        V = np.vstack([V_prev, E])
        with open(META_PATH, "r", encoding="utf-8") as mf:
            META_prev = json.load(mf)
        META = META_prev + records
    else:
        V = E
        META = records

    np.save(VECTORS_PATH, V)
    with open(META_PATH, "w", encoding="utf-8") as mf:
        json.dump(META, mf, ensure_ascii=False, indent=2)

    return {"ingested": len(records)}

def load_index():
    global V, META
    if os.path.exists(VECTORS_PATH) and os.path.exists(META_PATH):
        V = np.load(VECTORS_PATH)
        with open(META_PATH, "r", encoding="utf-8") as mf:
            META = json.load(mf)

def clear_index():
    global V, META
    V, META = None, []
    for p in (VECTORS_PATH, META_PATH, CORPUS_PATH):
        if os.path.exists(p):
            os.remove(p)

def ingest_from_json_file(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    itens: List[Item] = []
    for classe, entries in data.items():
        if not isinstance(entries, list):
            continue
        for e in entries:
            e = {**e, "classe": classe}
            itens.append(Item(**e))
    return ingest_items(itens)

def _contains_identifier(query: str, identifiers: List[str]) -> bool:
    q = query.lower()
    for idf in identifiers or []:
        s = (idf or "").lower().strip()
        if not s:
            continue
        # exact word or contained sequence
        if s == q or s in q:
            return True
    return False

def search(query: str, k: int = 6, classe: Optional[str] = None) -> List[Dict[str, Any]]:
    global V, META
    if not META or V is None:
        load_index()
    if not META or V is None:
        return []

    # Filter by class if provided
    idxs = [i for i, m in enumerate(META) if (classe is None or m["classe"] == classe)]
    if not idxs:
        return []

    corpus = [META[i] for i in idxs]
    vectors = V[idxs]

    qv = np.array(embed_texts([query])[0], dtype=np.float32).reshape(1, -1)
    sims = cosine_similarity(qv, vectors)[0]  # length = len(idxs)

    scored = []
    for local_i, m in enumerate(corpus):
        score = float(sims[local_i])
        # Priority: exact title match and identifier hits
        boost = 0.0
        if m.get("titulo", "").strip().lower() == query.strip().lower():
            boost += 0.4
        if _contains_identifier(query, m.get("identificadores", [])):
            boost += 0.25
        scored.append((score + boost, m))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:k]
    return [{
        "score": s,
        "classe": m["classe"],
        "titulo": m["titulo"],
        "chunk": m["chunk"],
        "source": m["source"],
        "identificadores": m.get("identificadores", [])
    } for s, m in top]

def list_titles(classe: str) -> List[str]:
    global META
    if not META:
        load_index()
    return sorted({m["titulo"] for m in META if m["classe"] == classe})
