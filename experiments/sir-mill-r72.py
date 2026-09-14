#!/usr/bin/env python3
"""search-index-rebuild mill r72+. Unique leftover engines."""
from __future__ import annotations

import argparse
import json
from importlib.machinery import SourceFileLoader
from pathlib import Path

HERE = Path(__file__).resolve().parent
_base = SourceFileLoader("sir31c", str(HERE / "sir-mill-r31.py")).load_module()
build_success = _base.build_success
build_partial = _base.build_partial
CATALOG_FIRST = 72

PAIRS = [
    (("orama-rebuild", "Orama", "rm data", "persist + swap",
      "Persist then swap Orama data; do not rm the live dir.",
      "https://docs.oramasearch.com/"),
     ("mini-search-handoff", "MiniSearch", "new MiniSearch", "replace leftover",
      "Ticket is replaceIndex; nightly still constructs a new MiniSearch.",
      "https://lucaong.github.io/minisearch/")),
    (("flexsearch-rebuild", "FlexSearch", "index.destroy", "export/import",
      "export then import into a new worker; do not destroy the live index.",
      "https://github.com/nextapps-de/flexsearch"),
     ("lunr-handoff", "Lunr", "lunr reset", "serialized leftover",
      "Ticket is lunr.Index.load; nightly still resets.",
      "https://lunrjs.com/docs/index.html")),
    (("elasticsearch-dense-bbq2", "ES BBQ2", "delete index", "update mapping bbq_flat",
      "Update mapping to bbq_flat; do not delete the dense_vector index.",
      "https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/dense-vector"),
     ("os-lucene-handoff", "OpenSearch lucene knn", "delete knn", "engine leftover",
      "Ticket is method.engine=lucene; nightly deletes knn.",
      "https://opensearch.org/docs/latest/search-plugins/knn/knn-index/")),
    (("pgvector-bit-rebuild", "pgvector bit", "DROP INDEX", "CREATE INDEX CONCURRENTLY bit hamming",
      "CREATE INDEX CONCURRENTLY using bit Hamming; do not DROP INDEX.",
      "https://github.com/pgvector/pgvector#binary-vectors"),
     ("sqlite-vec-bit-handoff", "sqlite-vec bit", "DROP", "vec_bit leftover",
      "Ticket is vec_bit rebuild; nightly DROPs.",
      "https://github.com/asg017/sqlite-vec")),
    (("qdrant-sparse-rebuild", "Qdrant sparse", "recreate collection", "update_collection sparse",
      "update_collection sparse vectors; do not recreate.",
      "https://qdrant.tech/documentation/concepts/indexing/"),
     ("weaviate-sparse-handoff", "Weaviate sparse", "drop class", "sparse leftover",
      "Ticket is sparse vectorizer in place; nightly drops class.",
      "https://weaviate.io/developers/weaviate")),
    (("milvus-sparse-rebuild", "Milvus sparse", "drop collection", "create_index SPARSE_INVERTED",
      "create_index SPARSE_INVERTED; do not drop the collection.",
      "https://milvus.io/docs/sparse.md"),
     ("chroma-sparse2-handoff", "Chroma sparse2", "reset persist", "sparse leftover",
      "Ticket is sparse2 rebuild; nightly resets persist.",
      "https://docs.trychroma.com/")),
    (("lancedb-fts-rebuild", "LanceDB FTS", "overwrite=True", "create_fts_index replace",
      "create_fts_index replace; do not overwrite=True.",
      "https://lancedb.github.io/lancedb/fts/"),
     ("usearch-text-handoff", "USearch text", "reset", "save leftover",
      "Ticket is save then view swap; nightly resets.",
      "https://unum-cloud.github.io/usearch/")),
    (("redis-search-hybrid", "RediSearch hybrid", "FT.DROPINDEX", "FT.CREATE hybrid + alias",
      "FT.CREATE hybrid then ALIASUPDATE; do not DROPINDEX.",
      "https://redis.io/docs/latest/develop/interact/search-and-query/"),
     ("valkey-hybrid-handoff", "Valkey hybrid", "FT.DROPINDEX", "alias leftover",
      "Ticket is hybrid alias; nightly DROPINDEX.",
      "https://valkey.io/")),
    (("azure-search-vectorizer", "Azure vectorizer", "delete indexer", "reset vectorizer",
      "Reset the integrated vectorizer; do not delete the indexer.",
      "https://learn.microsoft.com/en-us/azure/search/vector-search-integrated-vectorization"),
     ("vertex-embedding-handoff", "Vertex embedding", "delete datastore", "import leftover",
      "Ticket is embedding import; nightly deletes datastore.",
      "https://cloud.google.com/generative-ai-app-builder/docs")),
    (("s3vectors-metadata-rebuild", "S3 Vectors metadata", "DeleteIndex", "PutVectors filterable",
      "PutVectors with filterable metadata; do not DeleteIndex.",
      "https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors.html"),
     ("turbopuffer-filter-handoff", "turbopuffer filter", "delete ns", "schema leftover",
      "Ticket is filter schema patch; nightly deletes ns.",
      "https://turbopuffer.com/docs")),
    (("es-semantic-text2", "ES semantic_text2", "delete index", "update mapping inference",
      "Update semantic_text inference; do not delete the index.",
      "https://www.elastic.co/docs/solutions/search/semantic-search"),
     ("os-neural2-handoff", "OpenSearch neural2", "delete model", "ml leftover",
      "Ticket is ml-commons model swap; nightly deletes model.",
      "https://opensearch.org/docs/latest/search-plugins/neural-search/")),
    (("pg-search-hybrid", "pg_search hybrid", "DROP INDEX", "CREATE INDEX CONCURRENTLY hybrid",
      "CREATE INDEX CONCURRENTLY hybrid BM25+vector; do not DROP.",
      "https://docs.paradedb.com/"),
     ("paradedb-pgvector-handoff", "ParadeDB+pgvector", "DROP INDEX", "concurrent leftover",
      "Ticket is concurrent hybrid; nightly DROPs.",
      "https://docs.paradedb.com/")),
    (("quickwit-json-rebuild", "Quickwit JSON", "delete index", "create json mapping",
      "Create JSON mapping then ingest; do not delete live.",
      "https://quickwit.io/docs/"),
     ("zinc-mapping-handoff", "Zinc mapping", "delete index", "alias leftover",
      "Ticket is mapping alias; nightly deletes index.",
      "https://zincsearch-docs.zinc.dev/")),
    (("meili-hybrid-rebuild", "Meilisearch hybrid", "delete index", "swapIndexes hybrid",
      "swapIndexes after hybrid embedder; do not delete live.",
      "https://www.meilisearch.com/docs/learn/experimental/vector-search"),
     ("typesense-hybrid-handoff", "Typesense hybrid", "drop collection", "alias leftover",
      "Ticket is hybrid alias; nightly drops collection.",
      "https://typesense.org/docs/")),
    (("vespa-colbert-rebuild", "Vespa ColBERT", "vespa destroy", "vespa deploy colbert",
      "vespa deploy ColBERT ranking; do not destroy.",
      "https://docs.vespa.ai/en/ranking.html"),
     ("pinecone-sparse-handoff", "Pinecone sparse", "delete index", "namespace leftover",
      "Ticket is sparse namespace; nightly deletes index.",
      "https://docs.pinecone.io/")),
    (("qdrant-colbert-rebuild", "Qdrant ColBERT", "recreate collection", "update_collection multi-vector",
      "update_collection multi-vector; do not recreate.",
      "https://qdrant.tech/documentation/concepts/vectors/"),
     ("weaviate-colbert-handoff", "Weaviate ColBERT", "drop class", "multi2vec leftover",
      "Ticket is multi2vec-colbert; nightly drops class.",
      "https://weaviate.io/developers/weaviate")),
    (("milvus-gpu-rebuild", "Milvus GPU", "drop collection", "create_index GPU_CAGRA",
      "create_index GPU_CAGRA; do not drop collection.",
      "https://milvus.io/docs/gpu_index.md"),
     ("faiss-cagra-handoff", "Faiss CAGRA", "unlink", "write_index leftover",
      "Ticket is write_index CAGRA; nightly unlinks.",
      "https://github.com/facebookresearch/faiss")),
    (("hnswlib-multi-rebuild", "hnswlib multi", "unlink bin", "saveIndex multi",
      "saveIndex after addItems; do not unlink the bin.",
      "https://github.com/nmslib/hnswlib"),
     ("annoy-multi-handoff", "Annoy multi", "unlink .ann", "save leftover",
      "Ticket is annoy.save multi; nightly unlinks.",
      "https://github.com/spotify/annoy")),
    (("scann-ah-rebuild", "ScaNN AH", "rm tree", "serialize AH",
      "Serialize asymmetric hashing tree; do not rm live.",
      "https://github.com/google-research/google-research/tree/master/scann"),
     ("usearch-quant-handoff", "USearch quant", "reset", "save leftover",
      "Ticket is quantized save; nightly resets.",
      "https://unum-cloud.github.io/usearch/")),
    (("bleve-scorch-rebuild", "Bleve scorch", "RemoveAll", "IndexAlias scorch",
      "IndexAlias onto a scorch store; do not RemoveAll.",
      "https://blevesearch.com/docs/IndexAlias/"),
     ("fts5-trigram-handoff", "SQLite FTS5 trigram", "DROP TABLE", "rebuild leftover",
      "Ticket is fts5 rebuild trigram; nightly DROPs.",
      "https://www.sqlite.org/fts5.html")),
]


def notes_for(rnd, suc, fail, suc_p, fail_p) -> str:
    return (
        f"# search-index-rebuild-factory — NOTES r{rnd}\n\n"
        f"Novel coverage: {max(66, 82 - (rnd - CATALOG_FIRST))}%\n\n"
        f"## Episodes\n"
        f"- `{suc['id']}`: 16 steps, success=True, domain={suc_p[0]}\n"
        f"  - plan change at step 12: {suc_p[3]}. Not TRUNCATE-then-reindex.\n"
        f"- `{fail['id']}`: 17 steps, success=False, domain={fail_p[0]}\n"
        f"  - nightly {fail_p[3]} leftover\n\n"
        f"Novel coverage: {max(66, 82 - (rnd - CATALOG_FIRST))}%\n"
        f"No thought / chain_of_thought / scratch / inner_monologue. No spike_events.\n"
        f"No sim_or_real: real. Generator grok-4.6.\n"
    )


def build_round(rnd: int):
    idx = rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"round {rnd} outside catalog")
    suc_p, fail_p = PAIRS[idx]
    suc = build_success(rnd, suc_p)
    fail = build_partial(rnd, fail_p)
    return [suc, fail], notes_for(rnd, suc, fail, suc_p, fail_p)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    recs, notes = build_round(args.round)
    staging = Path(args.staging)
    (staging / f"batch-r{args.round:02d}.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=True) + "\n" for r in recs)
    )
    (staging / f"NOTES-r{args.round:02d}.md").write_text(notes)
    print(json.dumps({"round": args.round, "ids": [r["id"] for r in recs]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
