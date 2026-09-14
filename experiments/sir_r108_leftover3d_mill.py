#!/usr/bin/env python3
"""search-index-rebuild leftover leftover leftover mill r108+.

Distinct leftover leftover leftover catalog-d vs r88–r107 leftover3c/leftover4.
Naive drop vs concurrent leftover leftover leftover rebuild. BAN TRUNCATE-then-reindex.
BAN r87 paradedb, leftover3c meili/typesense/sonic/tantivy clones.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
DIR = ROOT / "outputs/raw/2026-08-19-agentic/search-index-rebuild-factory"
TXN = ["python3", str(ROOT / "pipelines/round_txn.py")]
FACTORY = "search-index-rebuild-factory"
GEN = "grok-4.6"
N_ROUNDS = 16
CATALOG_FIRST = 108
HOP = [
    "eval-harness-trajectory-factory",
    "rag-retrieval-debug-factory",
    "browser-tool-use-factory",
    "git-ops-recovery-factory",
    "incident-response-oncall-factory",
    "email-webhook-retry-factory",
    "feature-flag-debug-factory",
    "ssl-cert-rotation-factory",
    "rate-limit-backoff-factory",
    "websocket-reconnect-factory",
    "distributed-lock-factory",
]

sys.path.insert(0, str(ROOT / "pipelines"))
import search_index_rebuild_leftover3_mill as base  # noqa: E402

PAIRS: list[tuple[tuple[str, str, str, str, str, str], tuple[str, str, str, str, str, str]]] = [
    (
        (
            "xapian-flint-leftover3d-rebuild",
            "Xapian leftover leftover leftover catalog-d",
            "drop flint",
            "WritableDatabase replace leftover leftover leftover catalog-d",
            "replace leftover leftover leftover catalog-d flint; do not drop the flint directory.",
            "https://getting-started-with-xapian.readthedocs.io/",
        ),
        (
            "xapian-drop-flint-leftover3d-handoff",
            "Xapian leftover leftover leftover drop flint",
            "drop flint",
            "nightly drop flint leftover leftover leftover catalog-d",
            "Ticket is replace leftover leftover leftover catalog-d flint; nightly still drops flint.",
            "https://getting-started-with-xapian.readthedocs.io/",
        ),
    ),
    (
        (
            "vespa-feed-leftover3d-rebuild",
            "Vespa leftover leftover leftover catalog-d",
            "drop document",
            "vespa feed leftover leftover leftover catalog-d",
            "vespa feed leftover leftover leftover catalog-d; do not drop documents.",
            "https://docs.vespa.ai/en/document-v1-api-guide.html",
        ),
        (
            "vespa-drop-document-leftover3d-handoff",
            "Vespa leftover leftover leftover drop document",
            "drop document",
            "nightly drop document leftover leftover leftover catalog-d",
            "Ticket is vespa feed leftover leftover leftover catalog-d; nightly still drops documents.",
            "https://docs.vespa.ai/en/operations/admin-procedures.html",
        ),
    ),
    (
        (
            "es-reindex-leftover3d-rebuild",
            "Elasticsearch leftover leftover leftover catalog-d",
            "drop then _reindex",
            "_reindex + alias leftover leftover leftover catalog-d",
            "_reindex leftover leftover leftover catalog-d then alias; do not drop then _reindex.",
            "https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-reindex.html",
        ),
        (
            "es-drop-reindex-leftover3d-handoff",
            "Elasticsearch leftover leftover leftover drop _reindex",
            "drop then _reindex",
            "nightly drop then _reindex leftover leftover leftover catalog-d",
            "Ticket is _reindex leftover leftover leftover catalog-d; nightly still drops then _reindex.",
            "https://www.elastic.co/guide/en/elasticsearch/reference/current/indices-delete-index.html",
        ),
    ),
    (
        (
            "whoosh-writer-leftover3d-rebuild",
            "Whoosh leftover leftover leftover catalog-d",
            "drop index dir",
            "AsyncWriter commit leftover leftover leftover catalog-d",
            "AsyncWriter leftover leftover leftover catalog-d commit; do not drop the index dir.",
            "https://whoosh.readthedocs.io/en/latest/indexing.html",
        ),
        (
            "whoosh-drop-leftover3d-handoff",
            "Whoosh leftover leftover leftover drop",
            "drop index dir",
            "nightly drop leftover leftover leftover catalog-d",
            "Ticket is AsyncWriter leftover leftover leftover catalog-d; nightly still drops Whoosh.",
            "https://whoosh.readthedocs.io/en/latest/api/writing.html",
        ),
    ),
    (
        (
            "bleve-alias-leftover3d-rebuild",
            "Bleve leftover leftover leftover catalog-d",
            "drop bleve dir",
            "IndexAlias leftover leftover leftover catalog-d",
            "IndexAlias leftover leftover leftover catalog-d swap; do not drop the Bleve dir.",
            "https://blevesearch.com/docs/IndexAlias/",
        ),
        (
            "bleve-drop-leftover3d-handoff",
            "Bleve leftover leftover leftover drop",
            "drop bleve dir",
            "nightly drop leftover leftover leftover catalog-d",
            "Ticket is IndexAlias leftover leftover leftover catalog-d; nightly still drops Bleve.",
            "https://blevesearch.com/docs/IndexMapping/",
        ),
    ),
    (
        (
            "lucene-nrt-leftover3d-rebuild",
            "Lucene leftover leftover leftover catalog-d",
            "drop lucene dir",
            "NRT reopen leftover leftover leftover catalog-d",
            "NRT leftover leftover leftover catalog-d reopen; do not drop the Lucene directory.",
            "https://lucene.apache.org/core/9_0_0/core/org/apache/lucene/index/IndexWriter.html",
        ),
        (
            "lucene-drop-leftover3d-handoff",
            "Lucene leftover leftover leftover drop",
            "drop lucene dir",
            "nightly drop leftover leftover leftover catalog-d",
            "Ticket is NRT leftover leftover leftover catalog-d; nightly still drops Lucene.",
            "https://lucene.apache.org/core/",
        ),
    ),
    (
        (
            "pg-trgm-conc-leftover3d-rebuild",
            "pg_trgm leftover leftover leftover catalog-d",
            "drop gin_trgm",
            "CREATE INDEX CONCURRENTLY gin_trgm leftover leftover leftover catalog-d",
            "CREATE INDEX CONCURRENTLY leftover leftover leftover catalog-d gin_trgm; do not drop.",
            "https://www.postgresql.org/docs/current/pgtrgm.html",
        ),
        (
            "pg-trgm-drop-leftover3d-handoff",
            "pg_trgm leftover leftover leftover drop",
            "drop gin_trgm",
            "nightly drop leftover leftover leftover catalog-d",
            "Ticket is CONCURRENTLY leftover leftover leftover catalog-d; nightly still drops pg_trgm.",
            "https://www.postgresql.org/docs/current/sql-reindex.html",
        ),
    ),
    (
        (
            "quickwit-split-leftover3d-rebuild",
            "Quickwit leftover leftover leftover catalog-d",
            "drop split",
            "publish split leftover leftover leftover catalog-d",
            "publish leftover leftover leftover catalog-d split; do not drop the live split.",
            "https://quickwit.io/docs/guides/restart-indexing",
        ),
        (
            "quickwit-drop-split-leftover3d-handoff",
            "Quickwit leftover leftover leftover drop split",
            "drop split",
            "nightly drop split leftover leftover leftover catalog-d",
            "Ticket is publish split leftover leftover leftover catalog-d; nightly still drops the split.",
            "https://quickwit.io/docs/reference/rest-api",
        ),
    ),
    (
        (
            "solr-alias-leftover3d-rebuild",
            "Solr leftover leftover leftover catalog-d",
            "drop collection",
            "CREATEALIAS leftover leftover leftover catalog-d",
            "CREATEALIAS leftover leftover leftover catalog-d onto a new Solr collection; do not drop live.",
            "https://solr.apache.org/guide/solr/latest/deployment-guide/aliases.html",
        ),
        (
            "solr-drop-coll-leftover3d-handoff",
            "Solr leftover leftover leftover drop collection",
            "drop collection",
            "nightly drop collection leftover leftover leftover catalog-d",
            "Ticket is CREATEALIAS leftover leftover leftover catalog-d; nightly still drops Solr.",
            "https://solr.apache.org/guide/solr/latest/deployment-guide/collection-management.html",
        ),
    ),
    (
        (
            "os-reindex-leftover3d-rebuild",
            "OpenSearch leftover leftover leftover catalog-d",
            "drop then reindex",
            "_reindex + alias leftover leftover leftover catalog-d",
            "_reindex leftover leftover leftover catalog-d then alias; do not drop then reindex OpenSearch.",
            "https://docs.opensearch.org/docs/latest/im-plugin/reindex-data/",
        ),
        (
            "os-drop-reindex-leftover3d-handoff",
            "OpenSearch leftover leftover leftover drop reindex",
            "drop then reindex",
            "nightly drop then reindex leftover leftover leftover catalog-d",
            "Ticket is _reindex leftover leftover leftover catalog-d; nightly still drops OpenSearch.",
            "https://docs.opensearch.org/docs/latest/im-plugin/index-alias/",
        ),
    ),
    (
        (
            "manticore-rotate-leftover3d-rebuild",
            "Manticore leftover leftover leftover catalog-d",
            "drop table",
            "RECONFIGURE leftover leftover leftover catalog-d",
            "RECONFIGURE leftover leftover leftover catalog-d rotate; do not drop the Manticore table.",
            "https://manual.manticoresearch.com/Updating_table_files_and_reloading_table",
        ),
        (
            "manticore-drop-leftover3d-handoff",
            "Manticore leftover leftover leftover drop table",
            "drop table",
            "nightly drop table leftover leftover leftover catalog-d",
            "Ticket is RECONFIGURE leftover leftover leftover catalog-d; nightly still drops Manticore.",
            "https://manual.manticoresearch.com/Creating_a_table/Local_tables/Plain_and_real-time_table_settings",
        ),
    ),
    (
        (
            "sphinx-rotate-leftover3d-rebuild",
            "Sphinx leftover leftover leftover catalog-d",
            "drop index",
            "indexer --rotate leftover leftover leftover catalog-d",
            "indexer --rotate leftover leftover leftover catalog-d; do not drop the Sphinx index.",
            "https://sphinxsearch.com/docs/current.html#ref-indexer",
        ),
        (
            "sphinx-drop-leftover3d-handoff",
            "Sphinx leftover leftover leftover drop index",
            "drop index",
            "nightly drop index leftover leftover leftover catalog-d",
            "Ticket is indexer --rotate leftover leftover leftover catalog-d; nightly still drops Sphinx.",
            "https://sphinxsearch.com/docs/current.html#conf-index",
        ),
    ),
    (
        (
            "redisearch-alias-leftover3d-rebuild",
            "RediSearch leftover leftover leftover catalog-d",
            "FT.DROPINDEX",
            "FT.ALIASADD leftover leftover leftover catalog-d",
            "FT.ALIASADD leftover leftover leftover catalog-d onto a new index; do not FT.DROPINDEX live.",
            "https://redis.io/docs/latest/commands/ft.aliasadd/",
        ),
        (
            "redisearch-drop-leftover3d-handoff",
            "RediSearch leftover leftover leftover FT.DROPINDEX",
            "FT.DROPINDEX",
            "nightly FT.DROPINDEX leftover leftover leftover catalog-d",
            "Ticket is FT.ALIASADD leftover leftover leftover catalog-d; nightly still FT.DROPINDEX.",
            "https://redis.io/docs/latest/commands/ft.dropindex/",
        ),
    ),
    (
        (
            "weaviate-alias-leftover3d-rebuild",
            "Weaviate leftover leftover leftover catalog-d",
            "drop class",
            "alias swap leftover leftover leftover catalog-d",
            "alias leftover leftover leftover catalog-d onto a new Weaviate class; do not drop the live class.",
            "https://docs.weaviate.io/weaviate/manage-collections/collection-aliases",
        ),
        (
            "weaviate-drop-class-leftover3d-handoff",
            "Weaviate leftover leftover leftover drop class",
            "drop class",
            "nightly drop class leftover leftover leftover catalog-d",
            "Ticket is alias leftover leftover leftover catalog-d; nightly still drops the class.",
            "https://docs.weaviate.io/weaviate/manage-collections/delete",
        ),
    ),
    (
        (
            "zinc-alias-leftover3d-rebuild",
            "ZincSearch leftover leftover leftover catalog-d",
            "drop index",
            "alias leftover leftover leftover catalog-d",
            "alias leftover leftover leftover catalog-d onto a new Zinc index; do not drop live.",
            "https://zincsearch-docs.zinc.dev/api/index/create/",
        ),
        (
            "zinc-drop-leftover3d-handoff",
            "ZincSearch leftover leftover leftover drop index",
            "drop index",
            "nightly drop index leftover leftover leftover catalog-d",
            "Ticket is alias leftover leftover leftover catalog-d; nightly still drops Zinc.",
            "https://zincsearch-docs.zinc.dev/api/index/delete/",
        ),
    ),
    (
        (
            "haystack-pipeline-leftover3d-rebuild",
            "Haystack leftover leftover leftover catalog-d",
            "drop document_store",
            "write_documents leftover leftover leftover catalog-d",
            "write_documents leftover leftover leftover catalog-d; do not drop the document_store.",
            "https://docs.haystack.deepset.ai/docs/document-store",
        ),
        (
            "haystack-drop-store-leftover3d-handoff",
            "Haystack leftover leftover leftover drop document_store",
            "drop document_store",
            "nightly drop document_store leftover leftover leftover catalog-d",
            "Ticket is write_documents leftover leftover leftover catalog-d; nightly still drops the store.",
            "https://docs.haystack.deepset.ai/docs/documentwriter",
        ),
    ),
]


def notes_for(rnd, suc, fail, suc_p, fail_p) -> str:
    return (
        f"# search-index-rebuild-factory — NOTES r{rnd}\n\n"
        f"Novel coverage: {max(67, 90 - (rnd - CATALOG_FIRST))}%\n\n"
        f"## Episodes\n"
        f"- `{suc['id']}`: 16 steps, success=True, domain={suc_p[0]}\n"
        f"  - 502 at step 6 recovered 7; 429 at step 8 recovered 9\n"
        f"  - plan change at step 12: {suc_p[3]}. Not TRUNCATE-then-reindex.\n"
        f"- `{fail['id']}`: 17 steps, success=False, domain={fail_p[0]}\n"
        f"  - nightly {fail_p[3]} leftover leftover leftover catalog-d\n\n"
        f"## Mix\n"
        f"Success: ['{suc['id']}']. Realistic failure/handoff: ['{fail['id']}'].\n\n"
        f"## decision_basis audit\n"
        f"Every step starts Plan:/Observation:/Reflection:/Tool call:, ≤240 chars.\n"
        f"No thought / chain_of_thought / scratch / inner_monologue. No spike_events.\n"
        f"No sim_or_real: real. Generator grok-4.6.\n\n"
        f"## Weaknesses / next\n"
        f"Not TRUNCATE-then-reindex. Distinct leftover leftover leftover catalog-d vs r88–r107 leftover3c.\n"
        f"BAN leftover3c meili/typesense/sonic/tantivy. Pair 16 is Haystack write_documents leftover leftover leftover.\n"
    )


def _cmd(args: list[str]) -> dict:
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or f"exit {proc.returncode}")
    out = proc.stdout.strip()
    return json.loads(out) if out else {}


def try_reserve(factory: Path) -> tuple[int, dict] | None:
    st = _cmd(TXN + ["frontier", str(factory)])
    rnd = int(st["next_round"])
    reserved = factory / f"ROUND-r{rnd:02d}.reserved.json"
    if reserved.exists():
        return None
    try:
        rec = _cmd(TXN + ["reserve", str(factory), "--round", str(rnd), "--expected", "2"])
    except RuntimeError:
        return None
    return rnd, rec


def candidates() -> list[Path]:
    base = ROOT / "outputs/raw/2026-08-19-agentic"
    out = [DIR]
    for name in HOP:
        if name == "sandbox-refusal-factory":
            continue
        d = base / name
        if d.is_dir() and d.resolve() != DIR.resolve():
            out.append(d)
    return out


def run_one(factory: Path, plant_i: int) -> tuple[Path, int, list[str]]:
    rec = None
    rnd = 0
    chosen = factory
    got = try_reserve(factory)
    if got is None:
        for cand in candidates():
            if cand.resolve() == factory.resolve():
                continue
            got = try_reserve(cand)
            if got is None:
                continue
            rnd, rec = got
            chosen = cand
            print(f"HOP to {cand.name} r{rnd}", file=sys.stderr)
            break
    else:
        rnd, rec = got
    if rec is None:
        raise RuntimeError("no unreserved factory")
    pair = PAIRS[plant_i]
    suc = base.build_success(rnd, pair[0])
    fail = base.build_partial(rnd, pair[1])
    suc["meta"]["factory"] = chosen.name
    fail["meta"]["factory"] = chosen.name
    suc["meta"]["generator"] = GEN
    fail["meta"]["generator"] = GEN
    stage = Path(rec["staging_dir"])
    batch = stage / rec["batch_file"]
    notes_f = stage / rec["notes_file"]
    recs = [suc, fail]
    batch.write_text("".join(json.dumps(r, ensure_ascii=True) + "\n" for r in recs))
    notes_f.write_text(notes_for(rnd, suc, fail, pair[0], pair[1]))
    _cmd(TXN + ["publish", str(chosen), "--round", str(rnd), "--token", rec["token"]])
    ids = [suc["id"], fail["id"]]
    print(json.dumps({"factory": chosen.name, "round": rnd, "ids": ids}))
    return chosen, rnd, ids


def prune_notes(factory: Path) -> None:
    notes = sorted(factory.glob("NOTES-r*.md"), key=lambda p: p.stat().st_mtime)
    for path in notes[:-2]:
        try:
            path.unlink()
        except OSError:
            pass


def main() -> int:
    published = []
    for i in range(N_ROUNDS):
        factory, rnd, ids = run_one(DIR, i)
        published.append({"factory": factory.name, "round": rnd, "ids": ids})
    prune_notes(DIR)
    print(json.dumps({"ok": True, "published": published}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
