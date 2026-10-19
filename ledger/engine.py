"""Bounded transactional indexing, lexical retrieval and exact-span answers."""

from contextlib import contextmanager
import hashlib
import json
import re
import sqlite3
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from .guard import tokens, triage

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents(name TEXT PRIMARY KEY, sha TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS chunks(id TEXT PRIMARY KEY, name TEXT NOT NULL REFERENCES documents(name) ON DELETE CASCADE, ordinal INTEGER NOT NULL, text TEXT NOT NULL);
CREATE VIRTUAL TABLE IF NOT EXISTS search USING fts5(id UNINDEXED, text);
CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


def digest(data):
    return hashlib.sha256(data).hexdigest()


def capture(directory):
    root = Path(directory)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Source must be a real directory")
    paths = sorted(root.rglob("*"))
    if any(p.is_symlink() for p in paths):
        raise ValueError("Symlinked corpus entries are not accepted")
    files = [p for p in paths if p.is_file() and p.suffix == ".md"]
    if not 1 <= len(files) <= 100:
        raise ValueError(
            "Expected 1 to 100 Markdown files; empty corpus is not a deletion request"
        )
    captured, total = {}, 0
    for p in files:
        with p.open("rb") as stream:
            raw = stream.read(100_001)
        total += len(raw)
        if len(raw) > 100_000 or total > 1_000_000:
            raise ValueError("Corpus size limit exceeded")
        text = raw.decode("utf-8")
        if not text.strip():
            raise ValueError("Empty document")
        captured[p.relative_to(root).as_posix()] = (digest(raw), text)
    return captured


def split_chunks(text):
    words = text.split()
    return [" ".join(words[i : i + 150]) for i in range(0, len(words), 150)]


def ingest(directory, database):
    captured = capture(
        directory
    )  # Validate all bytes before creating/mutating the index.
    path = Path(database)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript(SCHEMA)
        db.execute("BEGIN IMMEDIATE")
        old = dict(db.execute("SELECT name,sha FROM documents"))
        changed = [n for n, (sha, _) in captured.items() if old.get(n) != sha]
        removed = sorted(set(old) - set(captured))
        if not changed and not removed:
            return {
                "status": "unchanged",
                "changed": 0,
                "removed": 0,
                "documents": len(old),
                "corpus_sha256": corpus_hash(db),
            }
        for name in changed + removed:
            db.execute("DELETE FROM documents WHERE name=?", (name,))
        for name in changed:
            sha, text = captured[name]
            db.execute("INSERT INTO documents VALUES (?,?)", (name, sha))
            for ordinal, chunk in enumerate(split_chunks(text)):
                key = digest(f"{name}\0{sha}\0{ordinal}".encode())
                db.execute(
                    "INSERT INTO chunks VALUES (?,?,?,?)", (key, name, ordinal, chunk)
                )
        db.execute("DELETE FROM search")
        db.execute("INSERT INTO search SELECT id,text FROM chunks ORDER BY id")
        signature = digest(
            json.dumps(sorted((n, s) for n, (s, _) in captured.items())).encode()
        )
        db.execute(
            "INSERT OR REPLACE INTO metadata VALUES ('corpus_sha256',?)", (signature,)
        )
        return {
            "status": "updated",
            "changed": len(changed),
            "removed": len(removed),
            "documents": len(captured),
            "corpus_sha256": signature,
        }


def corpus_hash(db):
    row = db.execute("SELECT value FROM metadata WHERE key='corpus_sha256'").fetchone()
    if row is None:
        raise sqlite3.DatabaseError("Missing corpus signature")
    return row[0]


@contextmanager
def connect(database):
    uri = Path(database).resolve().as_uri() + "?mode=ro"
    db = sqlite3.connect(uri, uri=True)
    db.execute("PRAGMA query_only=ON")
    try:
        yield db
    finally:
        db.close()


def validate(query, k, method):
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 500:
        raise ValueError("query must contain 1 to 500 characters")
    if type(k) is not int or not 1 <= k <= 5:
        raise ValueError("k must be an integer from 1 to 5")
    if method not in ("bm25", "character", "hybrid"):
        raise ValueError("Unknown retrieval method")


def retrieve(db, query, k=3, method="hybrid"):
    validate(query, k, method)
    terms = sorted(tokens(query))
    if not terms:
        return []
    rows = db.execute(
        "SELECT c.id,c.name,d.sha,c.text FROM chunks c JOIN documents d ON d.name=c.name ORDER BY c.id"
    ).fetchall()
    if not rows:
        return []
    # Character TF-IDF is lexical matching, not semantic embeddings.
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))
    matrix = vectorizer.fit_transform([r[3] for r in rows])
    similarities = (matrix @ vectorizer.transform([query]).T).toarray().ravel()
    similarity = {r[0]: float(v) for r, v in zip(rows, similarities)}
    chars = sorted(
        (r[0] for r in rows if similarity[r[0]] > 0),
        key=lambda key: (-similarity[key], key),
    )[:20]
    expression = " OR ".join('"' + t + '"' for t in terms)
    bm25 = [
        r[0]
        for r in db.execute(
            "SELECT id FROM search WHERE search MATCH ? ORDER BY bm25(search), id LIMIT 20",
            (expression,),
        )
    ]
    if method == "bm25":
        ranked = bm25
    elif method == "character":
        ranked = chars
    else:
        scores = {}
        for ranking in (bm25, chars):
            for rank, key in enumerate(ranking, 1):
                scores[key] = scores.get(key, 0) + 1 / (60 + rank)
        ranked = sorted(scores, key=lambda key: (-scores[key], key))
    lookup = {r[0]: r for r in rows}
    return [
        {
            "chunk_id": key,
            "document": lookup[key][1],
            "document_sha256": lookup[key][2],
            "text": lookup[key][3],
            "character_similarity": similarity[key],
        }
        for key in ranked[:k]
    ]


def answer(db, query, k=3, method="hybrid"):
    hits = retrieve(db, query, k, method)
    claims = []
    for hit in hits[:2]:
        sentences = re.split(r"(?<=[.!?])\s+", hit["text"])
        best = max(sentences, key=lambda s: len(tokens(s) & tokens(query)))
        # Fixed development heuristic; not calibrated confidence or a safety guarantee.
        if hit["character_similarity"] < 0.08 or not (tokens(best) & tokens(query)):
            continue
        citation = {
            key: hit[key] for key in ("chunk_id", "document", "document_sha256", "text")
        }
        claims.append(
            {"text": best, "citations": [citation], "triage": triage(best, [citation])}
        )
    return {
        "query": query,
        "method": method,
        "corpus_sha256": corpus_hash(db),
        "abstained": not claims,
        "claims": claims,
        "warning": "Extractive spans demonstrate citation provenance, not independent factual accuracy.",
    }
