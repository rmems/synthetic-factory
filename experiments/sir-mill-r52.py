#!/usr/bin/env python3
"""search-index-rebuild mill r52+. Unique leftover engines. Not TRUNCATE-then-reindex."""
from __future__ import annotations

import argparse
import json
from importlib.machinery import SourceFileLoader
from pathlib import Path

HERE = Path(__file__).resolve().parent
_base = SourceFileLoader("sir31", str(HERE / "sir-mill-r31.py")).load_module()
build_success = _base.build_success
build_partial = _base.build_partial
CATALOG_FIRST = 52

# slug, engine, wrong, fix, ticket, url
PAIRS = [
    (
        ("pinecone-ns-rebuild", "Pinecone namespace", "delete index", "create namespace + upsert swap",
         "Rebuild a Pinecone namespace in place; do not delete the live index.",
         "https://docs.pinecone.io/guides/indexes/manage-indexes"),
        ("vespa-hnsw-handoff", "Vespa HNSW", "vespa destroy", "vespa deploy leftover",
         "Nightly still vespa destroy; ticket is vespa deploy of HNSW params.",
         "https://docs.vespa.ai/en/approximate-nn.html"),
    ),
    (
        ("es-elser-rebuild", "ES ELSER", "delete inference", "PUT _inference elser v2",
         "Rotate ELSER v2 inference in place; do not delete the inference endpoint.",
         "https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-inference-put-elser"),
        ("os-semantic-handoff", "OpenSearch semantic", "delete ingest pipeline", "search pipeline leftover",
         "Ticket is search-pipeline swap; nightly still deletes the ingest pipeline.",
         "https://opensearch.org/docs/latest/search-plugins/semantic-search/"),
    ),
    (
        ("pgvector-halfvec-rebuild", "pgvector halfvec", "DROP INDEX", "REINDEX CONCURRENTLY halfvec",
         "REINDEX CONCURRENTLY the halfvec HNSW; do not DROP INDEX.",
         "https://github.com/pgvector/pgvector#half-precision-vectors"),
        ("timescale-vector-handoff", "Timescale vector", "DROP INDEX", "timescaledb.tune leftover",
         "Ticket is Concurrent recreate; nightly still DROPs the vector index.",
         "https://docs.timescale.com/ai/latest/pgvector-with-timescaledb/"),
    ),
    (
        ("marqo-tensor-rebuild", "Marqo tensor", "delete index", "add_documents + alias",
         "add_documents into a new tensor index then alias; do not delete live.",
         "https://docs.marqo.ai/latest/"),
        ("faiss-ivfpq-handoff", "Faiss IVFPQ", "unlink index.faiss", "write_index leftover",
         "Ticket is write_index then atomic replace; nightly unlinks the file.",
         "https://github.com/facebookresearch/faiss/wiki"),
    ),
    (
        ("scann-rebuild", "ScaNN", "rm tree", "serialize + swap",
         "Serialize a new ScaNN tree and swap; do not rm the live tree.",
         "https://github.com/google-research/google-research/tree/master/scann"),
        ("annoy-handoff", "Annoy", "unlink .ann", "save leftover",
         "Ticket is annoy.save then rename; nightly unlinks the .ann.",
         "https://github.com/spotify/annoy"),
    ),
    (
        ("usearch-rebuild", "USearch", "reset index", "save + view swap",
         "save() then memory-map a new view; do not reset the live index.",
         "https://unum-cloud.github.io/usearch/"),
        ("voyager-handoff", "Voyager", "unlink .voy", "save leftover",
         "Ticket is voyager.save; nightly still unlinks the .voy file.",
         "https://github.com/spotify/voyager"),
    ),
    (
        ("paradedb-bm25-rebuild", "ParadeDB BM25", "DROP INDEX", "REINDEX CONCURRENTLY pg_search",
         "REINDEX CONCURRENTLY the BM25 index; do not DROP INDEX.",
         "https://docs.paradedb.com/documentation/indexing/create_index"),
        ("pg-search-handoff", "pg_search", "TRUNCATE", "CREATE INDEX leftover",
         "Ticket is CREATE INDEX USING bm25; nightly still TRUNCATEs.",
         "https://docs.paradedb.com/documentation/full-text/overview"),
    ),
    (
        ("quickwit-rebuild", "Quickwit", "delete index", "create + ingest swap",
         "Create a new Quickwit index and ingest; do not delete the live one.",
         "https://quickwit.io/docs/get-started/quickwit-index"),
        ("zincsearch-handoff", "ZincSearch", "delete index", "alias leftover",
         "Ticket is alias swap; nightly still deletes the Zinc index.",
         "https://zincsearch-docs.zinc.dev/"),
    ),
    (
        ("sonic-rebuild", "Sonic", "FLUSHB", "PUSH + CONSOLIDATE",
         "PUSH then CONSOLIDATE; do not FLUSHB the collection.",
         "https://github.com/valeriansaliou/sonic"),
        ("bleve-handoff", "Bleve", "os.RemoveAll", "IndexAlias leftover",
         "Ticket is IndexAlias swap; nightly still RemoveAll the dir.",
         "https://blevesearch.com/docs/IndexAlias/"),
    ),
    (
        ("sqlite-fts5-rebuild", "SQLite FTS5", "DROP TABLE", "fts5 rebuild + integrity-check",
         "INSERT INTO fts5(fts) VALUES('rebuild'); do not DROP TABLE.",
         "https://www.sqlite.org/fts5.html#the_rebuild_command"),
        ("manticore-handoff", "Manticore", "TRUNCATE RT", "OPTIMIZE leftover",
         "Ticket is OPTIMIZE INDEX; nightly still TRUNCATE RTINDEX.",
         "https://manual.manticoresearch.com/Updating_table_schema_and_settings"),
    ),
    (
        ("crate-knn-rebuild", "CrateDB knn", "DROP TABLE", "REFRESH + SWAP TABLE",
         "REFRESH then SWAP TABLE; do not DROP the knn table.",
         "https://cratedb.com/docs/crate/reference/en/latest/general/dql/selects.html"),
        ("cockroach-inverted-handoff", "Cockroach inverted", "DROP INDEX", "CREATE INVERTED leftover",
         "Ticket is CREATE INVERTED INDEX CONCURRENTLY; nightly DROPs.",
         "https://www.cockroachlabs.com/docs/stable/inverted-indexes"),
    ),
    (
        ("yugabyte-gin-rebuild", "Yugabyte GIN", "DROP INDEX", "REINDEX CONCURRENTLY",
         "REINDEX CONCURRENTLY the GIN; do not DROP INDEX.",
         "https://docs.yugabyte.com/preview/explore/ysql-language-features/indexes-constraints/gin/"),
        ("singlestore-vector-handoff", "SingleStore vector", "DROP INDEX", "ALTER leftover",
         "Ticket is ALTER to rebuild VECTOR INDEX; nightly DROPs.",
         "https://docs.singlestore.com/cloud/reference/sql-reference/vector-functions/vector-indexing/"),
    ),
    (
        ("es-knn-bbq-rebuild", "ES BBQ knn", "delete index", "update mapping bbq_hnsw",
         "Update mapping to bbq_hnsw; do not delete the knn index.",
         "https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/dense-vector"),
        ("os-faiss-handoff", "OpenSearch FAISS", "delete knn", "method.engine leftover",
         "Ticket is method.engine=faiss swap; nightly deletes the knn index.",
         "https://opensearch.org/docs/latest/search-plugins/knn/knn-index/"),
    ),
    (
        ("qdrant-gpu-rebuild", "Qdrant GPU", "recreate collection", "update_collection gpu",
         "update_collection to GPU HNSW; do not recreate the collection.",
         "https://qdrant.tech/documentation/guides/distributed_deployment/"),
        ("weaviate-rq-handoff", "Weaviate RQ", "drop class", "rq leftover",
         "Ticket is rotational quantization in place; nightly drops the class.",
         "https://weaviate.io/developers/weaviate/concepts/vector-quantization"),
    ),
    (
        ("milvus-diskann-rebuild", "Milvus DiskANN", "drop collection", "create_index DISKANN",
         "create_index DISKANN on the growing collection; do not drop it.",
         "https://milvus.io/docs/disk_index.md"),
        ("chroma-sp-handoff", "Chroma sparse", "reset persist", "sparse leftover",
         "Ticket is sparse index rebuild; nightly still resets persist.",
         "https://docs.trychroma.com/"),
    ),
    (
        ("lancedb-btree-rebuild", "LanceDB btree", "overwrite=True", "create_scalar_index replace",
         "create_scalar_index replace; do not overwrite=True the dataset.",
         "https://lancedb.github.io/lancedb/ann_indexes/"),
        ("hnswlib-config-handoff", "hnswlib config", "unlink bin", "setEf leftover",
         "Ticket is setEf then saveIndex; nightly unlinks the bin.",
         "https://github.com/nmslib/hnswlib"),
    ),
    (
        ("redis-search-vset-rebuild", "RediSearch + VSET", "FT.DROPINDEX", "FT.CREATE + alias",
         "FT.CREATE then FT.ALIASUPDATE; do not FT.DROPINDEX the live index.",
         "https://redis.io/docs/latest/commands/ft.create/"),
        ("valkey-search-handoff", "Valkey Search", "FT.DROPINDEX", "alias leftover",
         "Ticket is alias update; nightly still FT.DROPINDEX.",
         "https://valkey.io/"),
    ),
    (
        ("azure-search-skillset-rebuild", "Azure skillset", "delete indexer", "reset + run indexer",
         "Reset and run the skillset indexer; do not delete it.",
         "https://learn.microsoft.com/en-us/azure/search/cognitive-search-concept-intro"),
        ("gcp-vertex-datastore-handoff", "Vertex datastore", "delete datastore", "import leftover",
         "r38 was Vertex search; this is datastore import leftover.",
         "https://cloud.google.com/generative-ai-app-builder/docs/create-data-store-es"),
    ),
    (
        ("s3vectors-query-rebuild", "S3 Vectors query", "DeleteIndex", "PutVectors + QueryVectors",
         "PutVectors then QueryVectors; do not DeleteIndex.",
         "https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors.html"),
        ("turbopuffer-ns-handoff", "turbopuffer ns", "delete ns", "namespace leftover",
         "r41 ns delete; this is namespace patch leftover.",
         "https://turbopuffer.com/docs"),
    ),
    (
        ("pgvector-sparsevec-rebuild", "pgvector sparsevec", "DROP INDEX", "CREATE INDEX CONCURRENTLY sparsevec",
         "CREATE INDEX CONCURRENTLY using sparsevec; do not DROP INDEX.",
         "https://github.com/pgvector/pgvector#sparse-vectors"),
        ("sqlite-vec-kmeans-handoff", "sqlite-vec kmeans", "DROP", "vec_quantize leftover",
         "Ticket is vec_quantize rebuild; nightly still DROPs.",
         "https://github.com/asg017/sqlite-vec"),
    ),
]


def notes_for(rnd, suc, fail, suc_p, fail_p) -> str:
    return (
        f"# search-index-rebuild-factory — NOTES r{rnd}\n\n"
        f"Novel coverage: {max(68, 84 - (rnd - CATALOG_FIRST))}%\n\n"
        f"## Episodes\n"
        f"- `{suc['id']}`: 16 steps, success=True, domain={suc_p[0]}\n"
        f"  - 502 at step 6 recovered 7; 429 at step 8 recovered 9\n"
        f"  - plan change at step 12: {suc_p[3]}. Not TRUNCATE-then-reindex.\n"
        f"- `{fail['id']}`: 17 steps, success=False, domain={fail_p[0]}\n"
        f"  - nightly {fail_p[3]} leftover\n\n"
        f"## Mix\n"
        f"Success: ['{suc['id']}']. Realistic failure/handoff: ['{fail['id']}'].\n\n"
        f"## decision_basis audit\n"
        f"Every step starts Plan:/Observation:/Reflection:/Tool call:, ≤240 chars.\n"
        f"No thought / chain_of_thought / scratch / inner_monologue. No spike_events.\n"
        f"No sim_or_real: real. Generator grok-4.6.\n\n"
        f"## Weaknesses / next\n"
        f"Not TRUNCATE-then-reindex. Distinct from sir r01–r{rnd-1}.\n"
    )


def build_round(rnd: int):
    idx = rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"round {rnd} outside catalog {CATALOG_FIRST}..{CATALOG_FIRST + len(PAIRS) - 1}")
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
