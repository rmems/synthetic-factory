#!/usr/bin/env python3
"""Mill docker-build-cache-factory r1365+. Search/vector DBs × ATA/AHCI leftovers.

NEW unique-pair catalog after r1317 CAD/FireWire.
BAN prior DBC catalogs, r645 nerdctl, r549 scsh/scsi, GNU Prolog/landlock/
SWI pack/seccomp/AppArmor/GOTOOLCHAIN, harbor-pin, leftover×sysctl.
17+18 steps. meta.generator=grok-4.6.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("dbc_mill_r1317", HERE / "dbc-mill-r1317.py")
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = _m.FACTORY
GEN = _m.GEN
lang = _m.lang
leftover = _m.leftover
success_episode = _m.success_episode
leftover_episode = _m.leftover_episode
notes_for = _m.notes_for
slug_taken = _m.slug_taken
BANNED_NEEDLES = _m.BANNED_NEEDLES + (
    "opencascade-occt-cache",
    "firewire-ohci-leftover",
    "ocp-cad-cache",
    "firewire-core-user-tlabel-leftover",
)

_CRYPTO = [
    ("lucene-core-cache", "LUCENE_HOME", "lucene-core", "9.11.1", "10.1.0", "lib/lucene-core.jar", "8MB"),
    ("tantivy-cache", "TANTIVY_HOME", "tanjun", "0.22.0", "0.22.1", "include/tantivy.h", "6MB"),
    ("meilisearch-cache", "MEILI_HTTP_ADDR", "meilisearch", "1.10.3", "1.12.3", "share/meilisearch/config.toml", "28MB"),
    ("typesense-cache", "TYPESENSE_DATA_DIR", "typesense-server", "27.1", "28.0", "etc/typesense/typesense.ini", "22MB"),
    ("sonic-search-cache", "SONIC_HOME", "sonic", "1.4.9", "1.4.9-post", "etc/sonic.cfg", "5MB"),
    ("xapian-core-cache", "XAPIAN_HOME", "xapian-compact", "1.4.25", "1.4.27", "include/xapian.h", "4MB"),
    ("solr-core-cache", "SOLR_HOME", "solr", "9.7.0", "9.8.1", "server/solr/solr.xml", "48MB"),
    ("opensearch-cache", "OPENSEARCH_HOME", "opensearch", "2.17.1", "2.19.1", "config/opensearch.yml", "52MB"),
    ("elasticsearch-cache", "ES_HOME", "elasticsearch", "8.15.2", "8.17.3", "config/elasticsearch.yml", "54MB"),
    ("zincsearch-cache", "ZINC_FIRST_ADMIN_USER", "zincsearch", "0.4.10", "0.4.10-post", "etc/zincsearch/config.yaml", "18MB"),
    ("quickwit-cache", "QW_DATA_DIR", "quickwit", "0.8.2", "0.8.2-post", "etc/quickwit/quickwit.yaml", "24MB"),
    ("lancedb-cache", "LANCEDB_HOME", "python3", "0.14.0", "0.21.1", "lib/python3/dist-packages/lancedb/__init__.py", "8MB"),
    ("milvus-cache", "MILVUS_HOME", "milvus", "2.4.13", "2.5.6", "configs/milvus.yaml", "46MB"),
    ("qdrant-cache", "QDRANT_CONFIG", "qdrant", "1.11.5", "1.13.4", "config/config.yaml", "26MB"),
    ("weaviate-cache", "WEAVIATE_HOME", "weaviate", "1.26.6", "1.29.0", "etc/weaviate/config.yaml", "30MB"),
    ("chroma-vec-cache", "CHROMA_HOME", "chroma", "0.5.5", "1.0.6", "lib/python3/dist-packages/chromadb/__init__.py", "12MB"),
    ("vespa-engine-cache", "VESPA_HOME", "vespa", "8.397.14", "8.460.16", "conf/vespa/vespa.xml", "58MB"),
    ("manticore-cache", "MANTICORE_CONFIG", "searchd", "6.3.6", "7.0.0", "etc/manticoresearch/manticore.conf", "16MB"),
    ("sphinxsearch-cache", "SPHINX_HOME", "searchd", "3.6.1", "3.7.1", "etc/sphinxsearch/sphinx.conf", "8MB"),
    ("bleve-cache", "BLEVE_HOME", "bleve", "2.4.2", "2.5.0", "share/bleve/bleve.md", "5MB"),
    ("whoosh-cache", "WHOOSH_HOME", "python3", "2.7.4", "2.7.4-post", "lib/python3/dist-packages/whoosh/__init__.py", "3MB"),
    ("haystack-search-cache", "HAYSTACK_HOME", "python3", "1.26.3", "2.12.1", "lib/python3/dist-packages/haystack/__init__.py", "10MB"),
    ("lucene-analyzers-cache", "LUCENE_ANALYZERS_HOME", "lucene-analyzers", "9.11.1", "10.1.0", "lib/lucene-analyzers-common.jar", "4MB"),
    ("lucene-queryparser-cache", "LUCENE_QP_HOME", "lucene-queryparser", "9.11.1", "10.1.0", "lib/lucene-queryparser.jar", "2MB"),
    ("solr-jts-cache", "SOLR_JTS_HOME", "solr", "9.7.0", "9.8.1", "modules/analysis-extras/lib", "6MB"),
    ("opensearch-dashboards-cache", "OPENSEARCH_DASHBOARDS_HOME", "opensearch-dashboards", "2.17.1", "2.19.1", "config/opensearch_dashboards.yml", "40MB"),
    ("es-analysis-icu-cache", "ES_ANALYSIS_ICU_HOME", "elasticsearch-plugin", "8.15.2", "8.17.3", "plugins/analysis-icu", "8MB"),
    ("typesense-docsearch-cache", "TYPESENSE_DOCSEARCH_HOME", "docsearch", "3.8.1", "3.8.2", "share/docsearch/docsearch.js", "2MB"),
    ("meilisearch-mini-cache", "MEILI_DB_PATH", "meilisearch", "1.10.3", "1.12.3", "data.ms", "4MB"),
    ("tantivy-cli-cache", "TANTIVY_CLI_HOME", "tantivy", "0.22.0", "0.22.1", "share/tantivy/tantivy.md", "3MB"),
    ("xapian-omega-cache", "XAPIAN_OMEGA_HOME", "omega", "1.4.25", "1.4.27", "share/omega/templates", "2MB"),
    ("xapian-bindings-cache", "XAPIAN_BINDINGS_HOME", "python3", "1.4.25", "1.4.27", "lib/python3/dist-packages/xapian/__init__.py", "3MB"),
    ("recoll-cache", "RECOLL_CONFDIR", "recollindex", "1.39.1", "1.41.1", "share/recoll/examples/recoll.conf", "7MB"),
    ("fscrawler-cache", "FSCRAWLER_HOME", "fscrawler", "2.10", "2.10-post", "config/fscrawler/_default/settings.yaml", "18MB"),
    ("apache-nutch-cache", "NUTCH_HOME", "nutch", "1.20", "1.20-post", "conf/nutch-default.xml", "22MB"),
    ("jina-core-cache", "JINA_HOME", "python3", "3.27.0", "3.28.0", "lib/python3/dist-packages/jina/__init__.py", "9MB"),
    ("marqo-cache", "MARQO_HOME", "python3", "2.12.0", "2.17.0", "lib/python3/dist-packages/marqo/__init__.py", "6MB"),
    ("txtai-cache", "TXTAI_HOME", "python3", "7.4.0", "8.4.0", "lib/python3/dist-packages/txtai/__init__.py", "8MB"),
    ("annoy-idx-cache", "ANNOY_HOME", "python3", "1.17.3", "1.17.3-post", "lib/python3/dist-packages/annoy/__init__.py", "1MB"),
    ("hnswlib-cache", "HNSWLIB_HOME", "python3", "0.8.0", "0.8.0-post", "include/hnswlib/hnswlib.h", "1MB"),
    ("nmslib-cache", "NMSLIB_HOME", "python3", "2.1.1", "2.1.1-post", "lib/python3/dist-packages/nmslib/__init__.py", "3MB"),
    ("scann-cache", "SCANN_HOME", "python3", "1.3.2", "1.3.5", "lib/python3/dist-packages/scann/__init__.py", "14MB"),
    ("sqlite-vss-cache", "SQLITE_VSS_HOME", "sqlite3", "0.1.2", "0.1.2-post", "lib/sqlite-vss/vector0.so", "2MB"),
    ("usearch-cache", "USEARCH_HOME", "python3", "2.15.3", "2.17.2", "lib/python3/dist-packages/usearch/__init__.py", "3MB"),
    ("voyager-idx-cache", "VOYAGER_HOME", "python3", "2.0.9", "2.1.0", "lib/python3/dist-packages/voyager/__init__.py", "2MB"),
    ("pgvector-ext-cache", "PGVECTOR_HOME", "pg_config", "0.7.4", "0.8.0", "share/postgresql/extension/vector.control", "1MB"),
    ("faiss-cpu-cache", "FAISS_HOME", "python3", "1.8.0", "1.10.0", "lib/python3/dist-packages/faiss/__init__.py", "16MB"),
    ("vespa-cli-cache", "VESPA_CLI_HOME", "vespa", "8.397.14", "8.460.16", "share/vespa/vespa-cli.md", "8MB"),
]

_GPIO = [
    ("ahci-leftover", "AHCI_CLEAR", "ahci skip_host_reset=1", "ahci", "ls /sys/module/ahci"),
    ("libahci-leftover", "LIBAHCI_CLEAR", "libahci skip_host_reset=1", "libahci", "ls /sys/module/libahci"),
    ("nvme-core-leftover", "NVME_CORE_CLEAR", "nvme_core multipath=Y", "nvme_core", "ls /sys/module/nvme_core"),
    ("sata-sil24-leftover", "SATA_SIL24_CLEAR", "sata_sil24 debug=1", "sata_sil24", "ls /sys/module/sata_sil24"),
    ("ahci-platform-leftover", "AHCI_PLATFORM_CLEAR", "ahci_platform debug=1", "ahci_platform", "ls /sys/module/ahci_platform"),
    ("libahci-platform-leftover", "LIBAHCI_PLATFORM_CLEAR", "libahci_platform debug=1", "libahci_platform", "ls /sys/module/libahci_platform"),
    ("sata-nv-leftover", "SATA_NV_CLEAR", "sata_nv adma=1", "sata_nv", "ls /sys/module/sata_nv"),
    ("sata-via-leftover", "SATA_VIA_CLEAR", "sata_via debug=1", "sata_via", "ls /sys/module/sata_via"),
    ("sata-promise-leftover", "SATA_PROMISE_CLEAR", "sata_promise debug=1", "sata_promise", "ls /sys/module/sata_promise"),
    ("sata-sil-leftover", "SATA_SIL_CLEAR", "sata_sil slow_down=1", "sata_sil", "ls /sys/module/sata_sil"),
    ("sata-svw-leftover", "SATA_SVW_CLEAR", "sata_svw debug=1", "sata_svw", "ls /sys/module/sata_svw"),
    ("sata-uli-leftover", "SATA_ULI_CLEAR", "sata_uli debug=1", "sata_uli", "ls /sys/module/sata_uli"),
    ("sata-qstor-leftover", "SATA_QSTOR_CLEAR", "sata_qstor debug=1", "sata_qstor", "ls /sys/module/sata_qstor"),
    ("sata-vsc-leftover", "SATA_VSC_CLEAR", "sata_vsc debug=1", "sata_vsc", "ls /sys/module/sata_vsc"),
    ("pata-amd-leftover", "PATA_AMD_CLEAR", "pata_amd debug=1", "pata_amd", "ls /sys/module/pata_amd"),
    ("ata-piix-leftover", "ATA_PIIX_CLEAR", "ata_piix prefer_ms_hyperv=1", "ata_piix", "ls /sys/module/ata_piix"),
    ("ata-generic-leftover", "ATA_GENERIC_CLEAR", "ata_generic all_generic_ide=1", "ata_generic", "ls /sys/module/ata_generic"),
    ("libata-leftover", "LIBATA_CLEAR", "libata allow_tpm=1", "libata", "ls /sys/module/libata"),
    ("sata-inic162x-leftover", "SATA_INIC162X_CLEAR", "sata_inic162x debug=1", "sata_inic162x", "ls /sys/module/sata_inic162x"),
    ("sata-mv-leftover", "SATA_MV_CLEAR", "sata_mv msi=1", "sata_mv", "ls /sys/module/sata_mv"),
    ("sata-sx4-leftover", "SATA_SX4_CLEAR", "sata_sx4 debug=1", "sata_sx4", "ls /sys/module/sata_sx4"),
    ("sata-sis-leftover", "SATA_SIS_CLEAR", "sata_sis debug=1", "sata_sis", "ls /sys/module/sata_sis"),
    ("sata-acpi-leftover", "SATA_ACPI_CLEAR", "ata_acpi debug=1", "ata_acpi", "ls /sys/module/ata_acpi"),
    ("pata-ali-leftover", "PATA_ALI_CLEAR", "pata_ali debug=1", "pata_ali", "ls /sys/module/pata_ali"),
    ("pata-artop-leftover", "PATA_ARTOP_CLEAR", "pata_artop debug=1", "pata_artop", "ls /sys/module/pata_artop"),
    ("pata-atiixp-leftover", "PATA_ATIIXP_CLEAR", "pata_atiixp debug=1", "pata_atiixp", "ls /sys/module/pata_atiixp"),
    ("pata-cmd64x-leftover", "PATA_CMD64X_CLEAR", "pata_cmd64x debug=1", "pata_cmd64x", "ls /sys/module/pata_cmd64x"),
    ("pata-cs5530-leftover", "PATA_CS5530_CLEAR", "pata_cs5530 debug=1", "pata_cs5530", "ls /sys/module/pata_cs5530"),
    ("pata-hpt366-leftover", "PATA_HPT366_CLEAR", "pata_hpt366 debug=1", "pata_hpt366", "ls /sys/module/pata_hpt366"),
    ("pata-it821x-leftover", "PATA_IT821X_CLEAR", "pata_it821x noraid=1", "pata_it821x", "ls /sys/module/pata_it821x"),
    ("pata-jmicron-leftover", "PATA_JMICRON_CLEAR", "pata_jmicron debug=1", "pata_jmicron", "ls /sys/module/pata_jmicron"),
    ("pata-marvell-leftover", "PATA_MARVELL_CLEAR", "pata_marvell debug=1", "pata_marvell", "ls /sys/module/pata_marvell"),
    ("pata-mpiix-leftover", "PATA_MPIIX_CLEAR", "pata_mpiix debug=1", "pata_mpiix", "ls /sys/module/pata_mpiix"),
    ("pata-netcell-leftover", "PATA_NETCELL_CLEAR", "pata_netcell debug=1", "pata_netcell", "ls /sys/module/pata_netcell"),
    ("pata-ninja32-leftover", "PATA_NINJA32_CLEAR", "pata_ninja32 debug=1", "pata_ninja32", "ls /sys/module/pata_ninja32"),
    ("pata-oldpiix-leftover", "PATA_OLDPIIX_CLEAR", "pata_oldpiix debug=1", "pata_oldpiix", "ls /sys/module/pata_oldpiix"),
    ("pata-opti-leftover", "PATA_OPTI_CLEAR", "pata_opti debug=1", "pata_opti", "ls /sys/module/pata_opti"),
    ("pata-pdc2027x-leftover", "PATA_PDC2027X_CLEAR", "pata_pdc2027x debug=1", "pata_pdc2027x", "ls /sys/module/pata_pdc2027x"),
    ("pata-radisys-leftover", "PATA_RADISYS_CLEAR", "pata_radisys debug=1", "pata_radisys", "ls /sys/module/pata_radisys"),
    ("pata-rz1000-leftover", "PATA_RZ1000_CLEAR", "pata_rz1000 debug=1", "pata_rz1000", "ls /sys/module/pata_rz1000"),
    ("pata-sc1200-leftover", "PATA_SC1200_CLEAR", "pata_sc1200 debug=1", "pata_sc1200", "ls /sys/module/pata_sc1200"),
    ("pata-sch-leftover", "PATA_SCH_CLEAR", "pata_sch debug=1", "pata_sch", "ls /sys/module/pata_sch"),
    ("pata-serverworks-leftover", "PATA_SERVERWORKS_CLEAR", "pata_serverworks debug=1", "pata_serverworks", "ls /sys/module/pata_serverworks"),
    ("pata-sil680-leftover", "PATA_SIL680_CLEAR", "pata_sil680 debug=1", "pata_sil680", "ls /sys/module/pata_sil680"),
    ("pata-sis-leftover", "PATA_SIS_CLEAR", "pata_sis debug=1", "pata_sis", "ls /sys/module/pata_sis"),
    ("pata-sl82c105-leftover", "PATA_SL82C105_CLEAR", "pata_sl82c105 debug=1", "pata_sl82c105", "ls /sys/module/pata_sl82c105"),
    ("pata-triflex-leftover", "PATA_TRIFLEX_CLEAR", "pata_triflex debug=1", "pata_triflex", "ls /sys/module/pata_triflex"),
    ("pata-via-leftover", "PATA_VIA_CLEAR", "pata_via debug=1", "pata_via", "ls /sys/module/pata_via"),
]


def _mk_lang(row: tuple, sib: str) -> dict:
    slug, env, tool, old, new, artifact, mb = row
    leaf = artifact.rsplit("/", 1)[-1]
    parent = artifact.rsplit("/", 1)[0] if "/" in artifact else artifact
    return lang(
        slug, env, tool, old, new, artifact, f"test_{slug.split('-')[0]}.py", "src/demo.c",
        slug.split("-")[0][:8] + "-x",
        f"rm -rf /usr/{parent}" if not parent.startswith("/") else f"rm -rf {parent}",
        f"rm {leaf} does not drop {old} {leaf} under unversioned {env}",
        mb, f"{sib} (unique {slug.split('-')[0]} cache, not prior NGS/astro/speech/solver/video/mq/quantum/font/cad catalogs)",
        f"{tool} --version", f"{tool} --version",
    )


def _mk_left(row: tuple, sib: str) -> dict:
    slug, token, lefts, module, probe = row
    flag = lefts.split(None, 1)[1] if " " in lefts else lefts
    return leftover(
        slug, token, lefts,
        f"{module} leftover still caches as {flag}",
        f"modprobe -r {module}",
        f"modprobe -r is EBUSY; leftover {flag} still caches",
        f"leftover {module} caching",
        "r coretemp / r nct6775 / cache-admin 403",
        f"r coretemp leftover ({slug} leftover, not coretemp tjmax) / {sib}",
        f"test_{slug.split('-')[0]}.py",
        f"ls /sys/module/{module}; {probe}",
        f"{slug.split('-')[0]} leftover {flag} leftover",
    )


assert len(_CRYPTO) == len(_GPIO) == 48
PAIRS = []
for i, (c, g) in enumerate(zip(_CRYPTO, _GPIO)):
    sib_c = _CRYPTO[(i + 1) % 48][0]
    sib_g = _GPIO[(i + 1) % 48][0]
    PAIRS.append((_mk_lang(c, sib_c), _mk_left(g, sib_g)))


def catalog_selfcheck() -> None:
    seen: set[str] = set()
    for suc, leftp in PAIRS:
        for spec in (suc, leftp):
            slug = spec["slug"]
            if slug in seen:
                raise SystemExit(f"duplicate catalog slug {slug}")
            seen.add(slug)
            ident = " ".join(
                str(spec.get(k, ""))
                for k in ("slug", "harbor", "env", "tool", "leftover", "token", "cache_id")
            ).lower()
            for needle in BANNED_NEEDLES:
                if needle in ident:
                    raise SystemExit(f"banned needle {needle!r} in {slug}")
            if "harbor-" in slug or "sysctl" in ident:
                raise SystemExit(f"ban {slug}")
    if len(PAIRS) < 12:
        raise SystemExit(f"catalog too small: {len(PAIRS)}")


_cursor = 0


def next_free_idx(start: int = 0) -> int | None:
    global _cursor
    for i in range(max(start, _cursor), len(PAIRS)):
        suc, leftp = PAIRS[i]
        if not slug_taken(suc["slug"]) and not slug_taken(leftp["slug"]):
            _cursor = i
            return i
        _cursor = i + 1
    return None


def write_round(round_n: int, staging: Path, idx: int | None = None) -> None:
    if idx is None:
        raise SystemExit("catalog idx required")
    suc, leftp = PAIRS[idx]
    for spec in (suc, leftp):
        if slug_taken(spec["slug"]):
            raise SystemExit(f"slug {spec['slug']} already published; refuse clone")
    srec = success_episode(round_n, suc)
    lrec = leftover_episode(round_n, leftp)
    blob = json.dumps(srec) + json.dumps(lrec)
    for key in ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"):
        if key in srec or key in lrec or f'"{key}"' in blob:
            raise SystemExit(f"forbidden key {key}")
    if '"sim_or_real": "real"' in blob:
        raise SystemExit("sim_or_real real forbidden")
    nsteps_s = srec["reward"]["cost_steps"]
    nsteps_l = lrec["reward"]["cost_steps"]
    if not (16 <= nsteps_s <= 24 and 16 <= nsteps_l <= 24):
        raise SystemExit(f"step count out of range {nsteps_s}/{nsteps_l}")
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(
        json.dumps(srec, separators=(",", ":")) + "\n" + json.dumps(lrec, separators=(",", ":")) + "\n"
    )
    notes.write_text(notes_for(round_n, suc, leftp, srec, lrec))
    if "Novel coverage:" not in notes.read_text():
        raise SystemExit("NOTES missing Novel coverage")
    print(json.dumps({"round": round_n, "idx": idx, "ids": [srec["id"], lrec["id"]], "steps": [nsteps_s, nsteps_l], "bytes": batch.stat().st_size}))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    ap.add_argument("--idx", type=int, required=True)
    args = ap.parse_args()
    write_round(args.round, Path(args.staging), args.idx)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
