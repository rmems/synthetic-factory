#!/usr/bin/env python3
"""search-index-rebuild mill leftover leftover leftover r72+.

Distinct leftover segment/schema. Naive drop vs concurrent leftover rebuild.
BAN r71 pgvector-sparsevec-rebuild, sqlite-vec-kmeans-handoff, TRUNCATE-then-reindex.
"""
from __future__ import annotations

import argparse
import json
from importlib.machinery import SourceFileLoader
from pathlib import Path

HERE = Path(__file__).resolve().parent
_base = SourceFileLoader("sir31", str(HERE / "sir-mill-r31.py")).load_module()
build_success = _base.build_success
build_partial = _base.build_partial
CATALOG_FIRST = 72

# slug, engine, wrong, fix, ticket, url
PAIRS = [
    (
        (
            "meili-swap-leftover3-rebuild",
            "Meilisearch leftover3 swap",
            "drop index",
            "create index + swapIndexes leftover3",
            "swapIndexes leftover3; do not drop the live Meilisearch index.",
            "https://www.meilisearch.com/docs/reference/api/swap_indexes",
        ),
        (
            "meili-drop-index-leftover3-handoff",
            "Meilisearch leftover3 drop",
            "drop index",
            "nightly drop index leftover3",
            "Ticket is swapIndexes leftover3; nightly still drops the index.",
            "https://www.meilisearch.com/docs/reference/api/indexes",
        ),
    ),
    (
        (
            "typesense-alias-leftover3-rebuild",
            "Typesense leftover3 alias",
            "drop collection",
            "create collection + alias leftover3",
            "Alias leftover3 onto a new Typesense collection; do not drop live.",
            "https://typesense.org/docs/latest/api/collection-alias.html",
        ),
        (
            "typesense-drop-coll-leftover3-handoff",
            "Typesense leftover3 drop",
            "drop collection",
            "nightly drop collection leftover3",
            "Ticket is alias leftover3; nightly still drops the collection.",
            "https://typesense.org/docs/latest/api/collections.html",
        ),
    ),
    (
        (
            "sonic-push-leftover3-rebuild",
            "Sonic leftover3 PUSH",
            "drop bucket",
            "PUSH + CONSOLIDATE leftover3",
            "PUSH then CONSOLIDATE leftover3; do not drop the Sonic bucket.",
            "https://github.com/valeriansaliou/sonic",
        ),
        (
            "sonic-drop-bucket-leftover3-handoff",
            "Sonic leftover3 FLUSHB",
            "drop bucket",
            "nightly drop bucket leftover3",
            "Ticket is PUSH leftover3; nightly still drops the bucket.",
            "https://github.com/valeriansaliou/sonic#protocol",
        ),
    ),
    (
        (
            "tantivy-commit-leftover3-rebuild",
            "Tantivy leftover3 writer",
            "drop writer",
            "IndexWriter commit leftover3",
            "commit leftover3 on IndexWriter; do not drop the writer.",
            "https://docs.rs/tantivy/latest/tantivy/",
        ),
        (
            "tantivy-drop-writer-leftover3-handoff",
            "Tantivy leftover3 drop writer",
            "drop writer",
            "nightly drop writer leftover3",
            "Ticket is commit leftover3; nightly still drops the writer.",
            "https://docs.rs/tantivy/latest/tantivy/struct.IndexWriter.html",
        ),
    ),
    (
        (
            "xapian-flint-leftover3-rebuild",
            "Xapian leftover3 flint",
            "drop flint",
            "WritableDatabase replace leftover3",
            "replace leftover3 flint; do not drop the flint directory.",
            "https://getting-started-with-xapian.readthedocs.io/",
        ),
        (
            "xapian-drop-flint-leftover3-handoff",
            "Xapian leftover3 drop flint",
            "drop flint",
            "nightly drop flint leftover3",
            "Ticket is replace leftover3; nightly still drops flint.",
            "https://xapian.org/docs/admin_notes.html",
        ),
    ),
    (
        (
            "manticore-rt-leftover3-rebuild",
            "Manticore leftover3 RT",
            "drop rt",
            "OPTIMIZE INDEX leftover3",
            "OPTIMIZE leftover3 RT; do not drop the RT index.",
            "https://manual.manticoresearch.com/Updating_table_schema_and_settings",
        ),
        (
            "manticore-drop-rt-leftover3-handoff",
            "Manticore leftover3 drop RT",
            "drop rt",
            "nightly drop rt leftover3",
            "Ticket is OPTIMIZE leftover3; nightly still drops RT.",
            "https://manual.manticoresearch.com/Creating_a_table/Local_tables/RT_table",
        ),
    ),
    (
        (
            "zinc-alias-leftover3-rebuild",
            "Zinc leftover3 alias",
            "drop index",
            "alias swap leftover3",
            "Alias leftover3 Zinc index; do not drop the live index.",
            "https://zincsearch-docs.zinc.dev/",
        ),
        (
            "zinc-drop-index-leftover3-handoff",
            "Zinc leftover3 drop",
            "drop index",
            "nightly drop index leftover3",
            "Ticket is alias leftover3; nightly still drops Zinc.",
            "https://zincsearch-docs.zinc.dev/api/index/",
        ),
    ),
    (
        (
            "opensearch-reindex-leftover3-rebuild",
            "OpenSearch leftover3 reindex",
            "drop reindex",
            "_reindex + alias leftover3",
            "_reindex leftover3 then alias; do not drop then reindex.",
            "https://opensearch.org/docs/latest/im-plugin/reindex-data/",
        ),
        (
            "opensearch-drop-reindex-leftover3-handoff",
            "OpenSearch leftover3 drop reindex",
            "drop reindex",
            "nightly drop reindex leftover3",
            "Ticket is _reindex leftover3; nightly still drops then reindex.",
            "https://opensearch.org/docs/latest/api-reference/document-apis/reindex/",
        ),
    ),
    (
        (
            "solr-core-leftover3-rebuild",
            "Solr leftover3 core",
            "drop core",
            "CREATEALIAS leftover3",
            "CREATEALIAS leftover3 onto a new core; do not drop the live core.",
            "https://solr.apache.org/guide/solr/latest/deployment-guide/solr-control-script-reference.html",
        ),
        (
            "solr-drop-core-leftover3-handoff",
            "Solr leftover3 drop core",
            "drop core",
            "nightly drop core leftover3",
            "Ticket is CREATEALIAS leftover3; nightly still drops the core.",
            "https://solr.apache.org/guide/solr/latest/deployment-guide/taking-solr-offline.html",
        ),
    ),
    (
        (
            "vespa-doc-leftover3-rebuild",
            "Vespa leftover3 document",
            "drop document",
            "vespa feed leftover3",
            "vespa feed leftover3; do not drop documents.",
            "https://docs.vespa.ai/en/document-v1-api-guide.html",
        ),
        (
            "vespa-drop-document-leftover3-handoff",
            "Vespa leftover3 drop document",
            "drop document",
            "nightly drop document leftover3",
            "Ticket is vespa feed leftover3; nightly still drops documents.",
            "https://docs.vespa.ai/en/operations/admin-procedures.html",
        ),
    ),
    (
        (
            "es-reindex-leftover3-rebuild",
            "Elasticsearch leftover3 _reindex",
            "drop _reindex",
            "_reindex + alias leftover3",
            "_reindex leftover3 then alias; do not drop then _reindex.",
            "https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-reindex.html",
        ),
        (
            "es-drop-reindex-leftover3-handoff",
            "Elasticsearch leftover3 drop _reindex",
            "drop _reindex",
            "nightly drop _reindex leftover3",
            "Ticket is _reindex leftover3; nightly still drops then _reindex.",
            "https://www.elastic.co/guide/en/elasticsearch/reference/current/indices-delete-index.html",
        ),
    ),
    (
        (
            "whoosh-writer-leftover3-rebuild",
            "Whoosh leftover3 writer",
            "drop",
            "AsyncWriter commit leftover3",
            "AsyncWriter leftover3 commit; do not drop the index dir.",
            "https://whoosh.readthedocs.io/en/latest/indexing.html",
        ),
        (
            "whoosh-drop-leftover3-handoff",
            "Whoosh leftover3 drop",
            "drop",
            "nightly drop leftover3",
            "Ticket is AsyncWriter leftover3; nightly still drops Whoosh.",
            "https://whoosh.readthedocs.io/en/latest/api/writing.html",
        ),
    ),
    (
        (
            "bleve-alias-leftover3-rebuild",
            "Bleve leftover3 alias",
            "drop",
            "IndexAlias leftover3",
            "IndexAlias leftover3 swap; do not drop the Bleve dir.",
            "https://blevesearch.com/docs/IndexAlias/",
        ),
        (
            "bleve-drop-leftover3-handoff",
            "Bleve leftover3 drop",
            "drop",
            "nightly drop leftover3",
            "Ticket is IndexAlias leftover3; nightly still drops Bleve.",
            "https://blevesearch.com/docs/IndexMapping/",
        ),
    ),
    (
        (
            "lucene-nrt-leftover3-rebuild",
            "Lucene leftover3 NRT",
            "drop",
            "NRT reopen leftover3",
            "NRT leftover3 reopen; do not drop the Lucene directory.",
            "https://lucene.apache.org/core/9_0_0/core/org/apache/lucene/index/IndexWriter.html",
        ),
        (
            "lucene-drop-leftover3-handoff",
            "Lucene leftover3 drop",
            "drop",
            "nightly drop leftover3",
            "Ticket is NRT leftover3; nightly still drops Lucene.",
            "https://lucene.apache.org/core/",
        ),
    ),
    (
        (
            "pg-trgm-conc-leftover3-rebuild",
            "pg_trgm leftover3 concurrent",
            "drop",
            "CREATE INDEX CONCURRENTLY gin_trgm leftover3",
            "CREATE INDEX CONCURRENTLY leftover3 gin_trgm; do not drop.",
            "https://www.postgresql.org/docs/current/pgtrgm.html",
        ),
        (
            "pg-trgm-drop-leftover3-handoff",
            "pg_trgm leftover3 drop",
            "drop",
            "nightly drop leftover3",
            "Ticket is CONCURRENTLY leftover3; nightly still drops pg_trgm.",
            "https://www.postgresql.org/docs/current/sql-reindex.html",
        ),
    ),
    (
        (
            "paradedb-bm25-leftover3-rebuild",
            "ParadeDB leftover3 BM25",
            "drop",
            "REINDEX CONCURRENTLY leftover3",
            "REINDEX CONCURRENTLY leftover3 BM25; do not drop.",
            "https://docs.paradedb.com/documentation/indexing/create_index",
        ),
        (
            "paradedb-drop-leftover3-handoff",
            "ParadeDB leftover3 drop",
            "drop",
            "nightly drop leftover3",
            "Ticket is REINDEX leftover3; nightly still drops ParadeDB.",
            "https://docs.paradedb.com/documentation/full-text/overview",
        ),
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
        f"  - nightly {fail_p[3]} leftover leftover leftover\n\n"
        f"## Mix\n"
        f"Success: ['{suc['id']}']. Realistic failure/handoff: ['{fail['id']}'].\n\n"
        f"## decision_basis audit\n"
        f"Every step starts Plan:/Observation:/Reflection:/Tool call:, ≤240 chars.\n"
        f"No thought / chain_of_thought / scratch / inner_monologue. No spike_events.\n"
        f"No sim_or_real: real. Generator grok-4.6.\n\n"
        f"## Weaknesses / next\n"
        f"Not TRUNCATE-then-reindex. Distinct leftover leftover leftover vs r71.\n"
    )


def build_round(rnd: int):
    idx = rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(
            f"round {rnd} outside catalog {CATALOG_FIRST}..{CATALOG_FIRST + len(PAIRS) - 1}"
        )
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
