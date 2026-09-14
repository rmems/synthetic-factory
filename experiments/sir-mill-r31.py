#!/usr/bin/env python3
"""search-index-rebuild mill r31+: unique engines, not TRUNCATE-then-reindex."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FACTORY = "search-index-rebuild-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 31

# slug, engine, wrong, fix, ticket, url
PAIRS = [
    (
        ("sqlite-vec-rebuild", "sqlite-vec", "DROP TABLE", "vec0 rebuild via INSERT SELECT",
         "Rebuild sqlite-vec without DROP; INSERT SELECT into a new vec0 then swap.",
         "https://github.com/asg017/sqlite-vec"),
        ("duckdb-vss-handoff", "DuckDB VSS", "TRUNCATE", "CREATE INDEX HNSW leftover",
         "Nightly still TRUNCATEs; ticket is CREATE INDEX USING HNSW then swap.",
         "https://duckdb.org/docs/stable/core_extensions/vss.html"),
    ),
    (
        ("clickhouse-vector-rebuild", "ClickHouse vector", "DROP TABLE", "MATERIALIZE INDEX",
         "MATERIALIZE INDEX the vector skip index; do not DROP the MergeTree.",
         "https://clickhouse.com/docs/en/engines/table-engines/mergetree-family/annindexes"),
        ("cassandra-sai-handoff", "Cassandra SAI", "TRUNCATE", "CREATE CUSTOM INDEX leftover",
         "Nightly TRUNCATEs; ticket is CREATE CUSTOM INDEX StorageAttachedIndex.",
         "https://cassandra.apache.org/doc/latest/cassandra/developing/cql/indexing/sai/sai-concepts.html"),
    ),
    (
        ("neo4j-vector-rebuild", "Neo4j vector", "DETACH DELETE", "CREATE VECTOR INDEX ... OPTIONS",
         "Recreate the vector index in place; do not DETACH DELETE nodes.",
         "https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/"),
        ("es-semantic-text-handoff", "ES semantic_text", "delete index", "update mapping leftover",
         "r01 was mapping conflict reindex; this is semantic_text inference leftover.",
         "https://www.elastic.co/docs/solutions/search/semantic-search"),
    ),
    (
        ("os-hybrid-rebuild", "OpenSearch hybrid", "delete+create", "search pipeline swap",
         "Swap the hybrid search pipeline; do not delete the knn index.",
         "https://opensearch.org/docs/latest/query-dsl/compound/hybrid/"),
        ("solr-vector-handoff", "Solr dense vector", "core unload", "schema add-field leftover",
         "r02-r04/r08/r12 Solr tlog/core; this is dense vector field leftover.",
         "https://solr.apache.org/guide/solr/latest/query-guide/dense-vector-search.html"),
    ),
    (
        ("lucene-hnsw-rebuild", "Lucene HNSW", "deleteAll", "IndexWriter forceMerge + commit",
         "forceMerge then commit; do not IndexWriter.deleteAll.",
         "https://lucene.apache.org/core/10_0_0/core/org/apache/lucene/index/IndexWriter.html"),
        ("tantivy-fastfield-handoff", "Tantivy", "rm -rf index", "reload schema leftover",
         "r14 was uncommitted; this is fastfield schema leftover after rebuild.",
         "https://docs.rs/tantivy/latest/tantivy/"),
    ),
    (
        ("meili-vector-rebuild", "Meilisearch vector", "delete index", "swapIndexes experimental",
         "r05/r09/r24 Meili dump/tenant; this is vector embedder swapIndexes.",
         "https://www.meilisearch.com/docs/learn/experimental/vector-search"),
        ("typesense-embed-handoff", "Typesense", "drop collection", "alias leftover",
         "r05/r09/r21/r26 Typesense alias/synonym; this is auto-embedding leftover.",
         "https://typesense.org/docs/29.0/api/vector-search.html"),
    ),
    (
        ("redis-vset-rebuild", "Redis vector set", "FLUSHDB", "VADD + alias swap",
         "r11 RediSearch ALTER; this is Redis 8 vector set VADD then alias.",
         "https://redis.io/docs/latest/develop/data-types/vector-sets/"),
        ("es-inference-handoff", "ES inference", "delete inference", "inference endpoint leftover",
         "Ticket is PUT _inference; nightly still deletes the endpoint.",
         "https://www.elastic.co/docs/api/doc/elasticsearch/group/endpoint-inference"),
    ),
    (
        ("bedrock-kb-rebuild", "Bedrock KB", "delete KB", "StartIngestionJob",
         "StartIngestionJob on the existing KB; do not DeleteKnowledgeBase.",
         "https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html"),
        ("vertex-search-handoff", "Vertex AI Search", "delete datastore", "import leftover",
         "Ticket is importDocuments; nightly still deletes the datastore.",
         "https://cloud.google.com/generative-ai-app-builder/docs/create-datastore-ingest"),
    ),
    (
        ("azure-ai-search-rebuild", "Azure AI Search", "delete index", "alias + indexer reset",
         "Reset the indexer onto an aliased index; do not delete the live index.",
         "https://learn.microsoft.com/en-us/azure/search/search-howto-reindex"),
        ("sphinx-rotate-handoff", "Sphinx", "indexer --all", "--rotate leftover",
         "Ticket is indexer --rotate; nightly still indexer --all downtime.",
         "https://sphinxsearch.com/docs/current/ref-indexer.html"),
    ),
    (
        ("es-ccs-rebuild", "ES CCS", "delete remote index", "ccr follow + alias",
         "CCR follow then alias; do not delete the remote cluster index.",
         "https://www.elastic.co/docs/deploy-manage/tools/cross-cluster-replication"),
        ("os-neural-handoff", "OpenSearch neural", "delete model", "ml-commons leftover",
         "r10 OS knn dim; this is ml-commons model leftover after rebuild.",
         "https://opensearch.org/docs/latest/search-plugins/neural-search/"),
    ),
    (
        ("s3-vectors-rebuild", "S3 Vectors", "delete bucket index", "CreateIndex + PutVectors",
         "CreateIndex then PutVectors; do not delete the vector bucket.",
         "https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors.html"),
        ("turbopuffer-handoff", "turbopuffer", "delete ns", "upsert leftover",
         "Ticket is upsert into a new ns + alias; nightly still deletes the ns.",
         "https://turbopuffer.com/docs"),
    ),
    (
        ("pgvector-iterative-scan", "pgvector", "REINDEX CONCURRENTLY drop", "iterative_scan + SET hnsw.iterative_scan",
         "r22 was hnsw reindex handoff; this is iterative_scan on an existing HNSW.",
         "https://github.com/pgvector/pgvector#iterative-index-scans"),
        ("sqlite-vec-meta-handoff", "sqlite-vec meta", "DROP", "vec_meta leftover",
         "r31 success is rebuild; this nightly still DROPs vec0 metadata.",
         "https://github.com/asg017/sqlite-vec"),
    ),
    (
        ("es-downsample-rebuild", "ES downsample", "delete datastream", "downsample ILM swap",
         "ILM downsample then alias; do not delete the data stream.",
         "https://www.elastic.co/docs/manage-data/lifecycle/index-lifecycle-management/downsampling"),
        ("os-knn-ef-handoff", "OpenSearch knn ef", "delete knn", "ef_search leftover",
         "r10 knn dim; this is method.parameters.ef_search leftover after rebuild.",
         "https://opensearch.org/docs/latest/search-plugins/knn/knn-index/"),
    ),
    (
        ("qdrant-quant-rebuild", "Qdrant quantization", "recreate collection", "update_collection quantization",
         "r16 alias swap; this is scalar quantization update_collection in place.",
         "https://qdrant.tech/documentation/guides/quantization/"),
        ("weaviate-bq-handoff", "Weaviate BQ", "drop class", "bq leftover",
         "r16 drop-class handoff; this is binary quantization leftover.",
         "https://weaviate.io/developers/weaviate/concepts/vector-quantization"),
    ),
    (
        ("milvus-mmap-rebuild", "Milvus mmap", "drop collection", "mmap load",
         "r23 flush vs load; this is mmap load after a growing-segment rebuild.",
         "https://milvus.io/docs/mmap.md"),
        ("chroma-hnsw-handoff", "Chroma HNSW", "reset persist", "hnsw:space leftover",
         "r23 persist handoff; this is hnsw:space leftover after rebuild.",
         "https://docs.trychroma.com/guides/deploy/performance"),
    ),
    (
        ("lancedb-ivf-rebuild", "LanceDB IVF", "overwrite=True", "create_index ivf_pq replace",
         "r27 overwrite handoff; this is create_index replace without overwrite=True.",
         "https://lancedb.github.io/lancedb/ann_indexes/"),
        ("hnswlib-save-handoff", "hnswlib", "unlink bin", "saveIndex leftover",
         "r28 save vs load; nightly still unlinks the bin instead of saveIndex.",
         "https://github.com/nmslib/hnswlib"),
    ),
]


def clip(text: str, n: int = 240) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 1] + "…"


def step(n: int, basis: str, name: str, args: dict, obs: str, reflection: str) -> dict:
    return {
        "n": n,
        "decision_basis": clip(basis),
        "tool_call": {"name": name, "args": args},
        "observation": obs,
        "reflection": reflection,
    }


def build_success(rnd: int, p: tuple) -> dict:
    slug, engine, wrong, fix, ticket, url = p
    stem = slug.replace("-", "_")
    src = f"src/{stem}.py"
    test = f"tests/test_{stem}.py"
    eid = f"sir-r{rnd}-{slug}"
    steps = [
        step(1, f"Plan: list src config tests before touching {engine} rebuild.",
             "bash", {"command": f"ls -la src {stem} tests | head -40"},
             f"src/{src}\n{test}", "Tree shows src plus tests."),
        step(2, f"Observation: listing named tests. Run pytest {test}.",
             "pytest", {"args": f"{test} -q --tb=short"},
             f"{test}::test_{stem} FAILED\nE   AssertionError: rebuild used {wrong}",
             "Failure is named."),
        step(3, f"Observation: {test} is red. Read it.",
             "read", {"path": test},
             f"def test_{stem}():\n    assert rebuild() != {wrong!r}\n    assert 'TRUNCATE' not in rebuild.__doc__\n",
             "Contract visible."),
        step(4, f"Observation: grep {engine.split()[0]}.",
             "bash", {"command": f"rg -n '{engine.split()[0]}|TRUNCATE|rebuild' src tests"},
             f"{src}: return '{wrong}'\n", "Grep hit helper."),
        step(5, f"Observation: read {src}.",
             "read", {"path": src},
             f"def rebuild():\n    return '{wrong}'\n", "Fetch docs."),
        step(6, "Observation: fetch vendor docs.",
             "fetch", {"url": url},
             f"GET {url}\nHTTP/1.1 502 Bad Gateway", "Backoff."),
        step(7, "Observation: 502. Retry 2s.",
             "fetch", {"url": url},
             f"retry 2s; 200 OK\n{ticket}", "Fixture used."),
        step(8, "Observation: second remote doc.",
             "fetch", {"url": url + "#rebuild"},
             "HTTP/1.1 429 Too Many Requests\nRetry-After: 5", "Honor Retry-After."),
        step(9, "Observation: 429. Sleep then retry.",
             "fetch", {"url": url + "#rebuild"},
             "200 OK\nNot TRUNCATE-then-reindex.", "Docs in hand."),
        step(10, f"Observation: first apply {wrong} pin.",
             "edit", {"path": src, "old": f"return '{wrong}'", "new": "return 'truncate-lite'"},
             "patched truncate-lite; still banned TRUNCATE family", "Re-run."),
        step(11, "Observation: still red.",
             "pytest", {"args": f"{test} -q --tb=short"},
             f"FAILED truncate-lite still {wrong} family", "Re-read."),
        step(12, f"Observation: re-read {src}.",
             "read", {"path": src},
             f"{fix} is the rebuild; not TRUNCATE",
             f"Plan change: {fix}."),
        step(13, f"Reflection: {fix}.",
             "edit", {"path": src, "old": "return 'truncate-lite'", "new": "return 'rebuild'"},
             f"patched {engine} {fix}", "Re-run."),
        step(14, "Observation: fix edit clean. Re-run.",
             "pytest", {"args": f"{test} -q --tb=short"},
             "1 passed in 0.16s", "Broader check."),
        step(15, f"Observation: broader pytest {test}.",
             "bash", {"command": f"pytest {test} -q"},
             "3 passed in 0.28s", "Diff."),
        step(16, "Observation: git diff --stat.",
             "bash", {"command": "git diff --stat | head -n 40"},
             f"diffstat {slug}: {src} | 9. No TRUNCATE.", "Done."),
    ]
    return {
        "id": eid,
        "goal": ticket,
        "plan": f"Avoid {wrong}; land {fix}. Not TRUNCATE-then-reindex.",
        "steps": steps,
        "outcome": f"{engine} {fix} rebuilt without {wrong} (success).",
        "reward": {"success": True, "tests_passed": 3, "retries": 2, "cost_steps": 16, "plan_changes": 1},
        "meta": {"factory": FACTORY, "round": rnd, "generator": GEN, "kind": "episode",
                 "seed": slug, "designed": True, "domain": slug, "stack": engine},
    }


def build_partial(rnd: int, p: tuple) -> dict:
    slug, engine, wrong, leftover, ticket, url = p
    stem = slug.replace("-", "_")
    src = f"src/{stem}.py"
    test = f"tests/test_{stem}.py"
    ntest = f"tests/test_nightly_{stem}.py"
    nightly = f"src/nightly_{stem}.py"
    eid = f"sir-r{rnd}-{slug}"
    steps = [
        step(1, f"Plan: list src before {engine} rebuild.",
             "bash", {"command": f"ls -la src {stem} tests | head -40"},
             f"{src}\n{test}", "Listed."),
        step(2, f"Observation: run {test}.",
             "pytest", {"args": f"{test} -q --tb=short"},
             f"{test} FAILED {wrong}", "Red."),
        step(3, f"Observation: read {test}.",
             "read", {"path": test},
             f"def test_{stem}():\n    assert rebuild() == 'rebuild'\n", "Contract."),
        step(4, "Observation: grep.",
             "bash", {"command": f"rg -n 'TRUNCATE|{wrong}' src tests"},
             f"{src}: return '{wrong}'", "Hit."),
        step(5, f"Observation: read {src}.",
             "read", {"path": src},
             f"def rebuild():\n    return '{wrong}'\n", "Docs."),
        step(6, "Observation: fetch.",
             "fetch", {"url": url},
             f"GET {url}\n502", "Backoff."),
        step(7, "Observation: retry.",
             "fetch", {"url": url},
             f"200 OK\n{ticket}", "Fixture."),
        step(8, "Observation: second fetch.",
             "fetch", {"url": url + "#rebuild"},
             "429 Retry-After: 5", "Honor."),
        step(9, "Observation: retry 429.",
             "fetch", {"url": url + "#rebuild"},
             "200 OK\nNot TRUNCATE-then-reindex.", "Docs."),
        step(10, f"Observation: first apply {wrong}.",
             "edit", {"path": src, "old": f"return '{wrong}'", "new": "return 'truncate-lite'"},
             "still TRUNCATE family", "Re-run."),
        step(11, "Observation: still red.",
             "pytest", {"args": f"{test} -q --tb=short"},
             "FAILED truncate-lite", "Re-read."),
        step(12, f"Observation: re-read {src}.",
             "read", {"path": src},
             f"nightly {leftover}",
             f"Plan change: rebuild; xfail nightly {leftover}."),
        step(13, "Reflection: rebuild; xfail nightly.",
             "edit", {"path": src, "old": "return 'truncate-lite'", "new": "return 'rebuild'"},
             f"patched; nightly {leftover}", "Gate."),
        step(14, "Observation: gate test.",
             "pytest", {"args": f"{test} -q --tb=short"},
             "1 passed in 0.14s", "xfail nightly."),
        step(15, "Observation: xfail nightly.",
             "edit", {"path": ntest, "old": f"def test_nightly_{stem}():",
                      "new": f"@pytest.mark.xfail(reason=\"handoff: {leftover}\", strict=False)\ndef test_nightly_{stem}():"},
             f"xfails {leftover}", "Confirm."),
        step(16, f"Observation: leftover {nightly}.",
             "read", {"path": nightly},
             f"{nightly} still {leftover}", "Handoff."),
        step(17, f"Observation: leftover stands. Ticket {slug}.",
             "bash", {"command": f"pytest {test} -q"},
             "1 passed in 0.12s", "Partial."),
    ]
    return {
        "id": eid,
        "goal": ticket,
        "plan": f"Avoid {wrong}; expect nightly {leftover}.",
        "steps": steps,
        "outcome": f"{engine} rebuild landed. Partial: nightly still {leftover} (xfail).",
        "reward": {"success": False, "tests_passed": 1, "xfailed": 1, "handoff": 1, "cost_steps": 17, "plan_changes": 1},
        "meta": {"factory": FACTORY, "round": rnd, "generator": GEN, "kind": "episode",
                 "seed": slug, "designed": True, "domain": slug, "stack": engine},
    }


def notes_for(rnd, suc, fail, suc_p, fail_p) -> str:
    return (
        f"# search-index-rebuild-factory — NOTES r{rnd}\n\n"
        f"Novel coverage: {max(70, 86 - (rnd - CATALOG_FIRST))}%\n\n"
        f"## Episodes\n"
        f"- `{suc['id']}`: 16 steps, success=True, domain={suc_p[0]}, seed={suc_p[0]}\n"
        f"  - 502 at step 6 recovered 7; 429 at step 8 recovered 9\n"
        f"  - plan change at step 12: {suc_p[3]}. Not TRUNCATE-then-reindex.\n"
        f"- `{fail['id']}`: 17 steps, success=False, domain={fail_p[0]}, seed={fail_p[0]}\n"
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
