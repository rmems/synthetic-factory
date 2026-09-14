#!/usr/bin/env python3
"""Mill docker-build-cache-factory r1408+. Graph DBs × UBI/NAND leftovers.

NEW unique-pair catalog after r1365 search/ATA.
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
_spec = importlib.util.spec_from_file_location("dbc_mill_r1365", HERE / "dbc-mill-r1365.py")
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
    "lucene-core-cache",
    "ahci-leftover",
    "vespa-cli-cache",
    "pata-via-leftover",
)

_CRYPTO = [
    ("neo4j-server-cache", "NEO4J_HOME", "neo4j", "5.23.0", "5.26.1", "conf/neo4j.conf", "42MB"),
    ("arangodb-server-cache", "ARANGODB_HOME", "arangod", "3.12.2", "3.12.4", "etc/arangodb3/arangod.conf", "38MB"),
    ("dgraph-alpha-cache", "DGRAPH_ALPHA_HOME", "dgraph", "24.0.4", "24.1.1", "etc/dgraph/alpha.yml", "28MB"),
    ("nebula-graph-cache", "NEBULA_HOME", "nebula-graphd", "3.8.0", "3.8.2", "etc/nebula-graphd.conf", "24MB"),
    ("kuzu-db-cache", "KUZU_HOME", "kuzu", "0.6.0", "0.7.1", "include/kuzu.h", "8MB"),
    ("memgraph-cache", "MEMGRAPH_HOME", "memgraph", "2.18.1", "2.21.0", "etc/memgraph/memgraph.conf", "22MB"),
    ("falkordb-cache", "FALKORDB_HOME", "redis-server", "4.8.0", "4.10.2", "lib/falkordb.so", "6MB"),
    ("oxigraph-cache", "OXIGRAPH_HOME", "oxigraph", "0.4.2", "0.4.8", "share/oxigraph/oxigraph.md", "9MB"),
    ("jena-tdb2-cache", "JENA_HOME", "tdb2.tdbloader", "5.1.0", "5.3.0", "lib/jena-tdb2.jar", "12MB"),
    ("typedb-server-cache", "TYPEDB_HOME", "typedb", "2.28.3", "3.1.0", "server/conf/config.yml", "26MB"),
    ("janusgraph-cache", "JANUSGRAPH_HOME", "gremlin-server", "1.0.0", "1.1.0", "conf/gremlin-server/gremlin-server.yaml", "34MB"),
    ("orientdb-server-cache", "ORIENTDB_HOME", "server.sh", "3.2.31", "3.2.38", "config/orientdb-server-config.xml", "20MB"),
    ("hugegraph-cache", "HUGEGRAPH_HOME", "hugegraph", "1.3.0", "1.5.0", "conf/rest-server.properties", "18MB"),
    ("gremlin-server-cache", "GREMLIN_HOME", "gremlin-server.sh", "3.7.2", "3.7.3", "conf/gremlin-server.yaml", "16MB"),
    ("tinkerpop-cache", "TINKERPOP_HOME", "gremlin.sh", "3.7.2", "3.7.3", "lib/gremlin-core.jar", "10MB"),
    ("blazegraph-cache", "BLAZEGRAPH_HOME", "blazegraph", "2.1.6", "2.1.6-post", "conf/RWStore.properties", "14MB"),
    ("rdf4j-cache", "RDF4J_HOME", "console.sh", "5.0.2", "5.1.2", "etc/org.eclipse.rdf4j.cfg", "11MB"),
    ("rdflib-cache", "RDFLIB_HOME", "python3", "7.0.0", "7.1.4", "lib/python3/dist-packages/rdflib/__init__.py", "4MB"),
    ("networkx-cache", "NETWORKX_HOME", "python3", "3.3", "3.4.2", "lib/python3/dist-packages/networkx/__init__.py", "5MB"),
    ("igraph-lib-cache", "IGRAPH_HOME", "python3", "0.11.6", "0.11.8", "include/igraph/igraph.h", "6MB"),
    ("graph-tool-cache", "GRAPH_TOOL_HOME", "python3", "2.77", "2.91", "lib/python3/dist-packages/graph_tool/__init__.py", "18MB"),
    ("cytoscape-cache", "CYTOSCAPE_HOME", "cytoscape.sh", "3.10.2", "3.10.3", "framework/etc/cytoscape.props", "22MB"),
    ("gephi-toolkit-cache", "GEPHI_HOME", "gephi", "0.10.1", "0.10.1-post", "lib/gephi-toolkit.jar", "15MB"),
    ("tulip-gui-cache", "TULIP_HOME", "tulip", "5.7.4", "6.0.0", "include/tulip/TulipRelease.h", "12MB"),
    ("ogdf-lib-cache", "OGDF_HOME", "python3", "2023.09", "2025.02", "include/ogdf/basic/Graph.h", "8MB"),
    ("lemon-graph-cache", "LEMON_HOME", "python3", "1.3.1", "1.3.1-post", "include/lemon/list_graph.h", "3MB"),
    ("boost-bgl-cache", "BOOST_ROOT", "python3", "1.85.0", "1.87.0", "include/boost/graph/adjacency_list.hpp", "4MB"),
    ("snap-stanford-cache", "SNAP_HOME", "python3", "6.0", "6.0-post", "include/Snap.h", "7MB"),
    ("cugraph-cache", "CUGRAPH_HOME", "python3", "24.08.00", "25.02.00", "lib/python3/dist-packages/cugraph/__init__.py", "28MB"),
    ("graphx-cache", "GRAPHX_HOME", "spark-submit", "3.5.2", "3.5.4", "jars/spark-graphx.jar", "9MB"),
    ("giraph-cache", "GIRAPH_HOME", "giraph", "1.3.0", "1.3.0-post", "conf/giraph-site.xml", "14MB"),
    ("apache-age-cache", "AGE_HOME", "pg_config", "1.5.0", "1.5.0-post", "share/postgresql/extension/age.control", "3MB"),
    ("cayley-graph-cache", "CAYLEY_HOME", "cayley", "0.7.7", "0.7.7-post", "etc/cayley.yml", "8MB"),
    ("terminusdb-cache", "TERMINUSDB_HOME", "terminusdb", "11.1.11", "11.1.14", "config/terminusdb.conf", "16MB"),
    ("hdt-rdf-cache", "HDT_HOME", "hdtSearch", "1.1.3", "1.1.3-post", "include/HDT.hpp", "4MB"),
    ("qlever-cache", "QLEVER_HOME", "IndexBuilderMain", "0.0.0", "0.0.1", "share/qlever/qlever.md", "12MB"),
    ("oxigraph-cli-cache", "OXIGRAPH_CLI_HOME", "oxigraph", "0.4.2", "0.4.8", "share/oxigraph/oxigraph.1", "2MB"),
    ("rdf4j-workbench-cache", "RDF4J_WORKBENCH_HOME", "console.sh", "5.0.2", "5.1.2", "etc/org.eclipse.rdf4j.workbench.cfg", "5MB"),
    ("neo4j-gds-cache", "NEO4J_GDS_HOME", "neo4j", "2.7.0", "2.13.2", "plugins/graph-data-science.jar", "18MB"),
    ("dgraph-ratel-cache", "DGRAPH_RATEL_HOME", "ratel", "24.0.4", "24.1.1", "share/ratel/ratel.md", "6MB"),
    ("nebula-storaged-cache", "NEBULA_STORAGED_HOME", "nebula-storaged", "3.8.0", "3.8.2", "etc/nebula-storaged.conf", "10MB"),
    ("nebula-metad-cache", "NEBULA_METAD_HOME", "nebula-metad", "3.8.0", "3.8.2", "etc/nebula-metad.conf", "8MB"),
    ("arangodb-starter-cache", "ARANGO_STARTER_HOME", "arangodb", "3.12.2", "3.12.4", "etc/arangodb3/starter.conf", "4MB"),
    ("kuzu-cli-cache", "KUZU_CLI_HOME", "kuzu", "0.6.0", "0.7.1", "share/kuzu/kuzu.md", "2MB"),
    ("memgraph-lab-cache", "MEMGRAPH_LAB_HOME", "lab", "2.18.1", "2.21.0", "etc/lab/config.json", "7MB"),
    ("typedb-console-cache", "TYPEDB_CONSOLE_HOME", "typedb", "2.28.3", "3.1.0", "console/conf/console.yml", "3MB"),
    ("gremlin-console-cache", "GREMLIN_CONSOLE_HOME", "gremlin.sh", "3.7.2", "3.7.3", "conf/remote.yaml", "4MB"),
    ("jena-fuseki-cache", "FUSEKI_HOME", "fuseki-server", "5.1.0", "5.3.0", "run/config.ttl", "9MB"),
]

_GPIO = [
    ("ubi-core-leftover", "UBI_CORE_CLEAR", "ubi debug=1", "ubi", "ls /sys/class/ubi"),
    ("ubifs-core-leftover", "UBIFS_CLEAR", "ubifs debug=1", "ubifs", "ls /sys/module/ubifs"),
    ("nand-core-leftover", "NAND_CORE_CLEAR", "nand debug=1", "nand", "ls /sys/module/nand"),
    ("mtdchar-leftover", "MTDCHAR_CLEAR", "mtdchar debug=1", "mtdchar", "ls /dev/mtd*"),
    ("onenand-leftover", "ONENAND_CLEAR", "onenand debug=1", "onenand", "ls /sys/module/onenand"),
    ("ubi-block-leftover", "UBI_BLOCK_CLEAR", "ubiblock debug=1", "ubiblock", "ls /sys/module/ubiblock"),
    ("nandsim-leftover", "NANDSIM_CLEAR", "nandsim first_id_byte=cache", "nandsim", "ls /sys/module/nandsim"),
    ("mtdblock-leftover", "MTDBLOCK_CLEAR", "mtdblock debug=1", "mtdblock", "ls /sys/module/mtdblock"),
    ("mtdoops-leftover", "MTDOOPS_CLEAR", "mtdoops mtddev=cache", "mtdoops", "ls /sys/module/mtdoops"),
    ("mtdswap-leftover", "MTDSWAP_CLEAR", "mtdswap debug=1", "mtdswap", "ls /sys/module/mtdswap"),
    ("nftl-leftover", "NFTL_CLEAR", "nftl debug=1", "nftl", "ls /sys/module/nftl"),
    ("inftl-leftover", "INFTL_CLEAR", "inftl debug=1", "inftl", "ls /sys/module/inftl"),
    ("rfd-ftl-leftover", "RFD_FTL_CLEAR", "rfd_ftl debug=1", "rfd_ftl", "ls /sys/module/rfd_ftl"),
    ("ssfdc-leftover", "SSFDC_CLEAR", "ssfdc debug=1", "ssfdc", "ls /sys/module/ssfdc"),
    ("sm-ftl-leftover", "SM_FTL_CLEAR", "sm_ftl debug=1", "sm_ftl", "ls /sys/module/sm_ftl"),
    ("gpmi-nand-leftover", "GPMI_NAND_CLEAR", "gpmi_nand debug=1", "gpmi_nand", "ls /sys/module/gpmi_nand"),
    ("denali-nand-leftover", "DENALI_NAND_CLEAR", "denali debug=1", "denali", "ls /sys/module/denali"),
    ("cafe-nand-leftover", "CAFE_NAND_CLEAR", "cafe_nand debug=1", "cafe_nand", "ls /sys/module/cafe_nand"),
    ("orion-nand-leftover", "ORION_NAND_CLEAR", "orion_nand debug=1", "orion_nand", "ls /sys/module/orion_nand"),
    ("tmio-nand-leftover", "TMIO_NAND_CLEAR", "tmio_nand debug=1", "tmio_nand", "ls /sys/module/tmio_nand"),
    ("sharpsl-nand-leftover", "SHARPSL_NAND_CLEAR", "sharpsl debug=1", "sharpsl", "ls /sys/module/sharpsl"),
    ("diskonchip-leftover", "DISKONCHIP_CLEAR", "diskonchip debug=1", "diskonchip", "ls /sys/module/diskonchip"),
    ("pmc551-leftover", "PMC551_CLEAR", "pmc551 debug=1", "pmc551", "ls /sys/module/pmc551"),
    ("phram-leftover", "PHRAM_CLEAR", "phram phram=cache", "phram", "ls /sys/module/phram"),
    ("slram-leftover", "SLRAM_CLEAR", "slram slram=cache", "slram", "ls /sys/module/slram"),
    ("platram-leftover", "PLATRAM_CLEAR", "platram debug=1", "platram", "ls /sys/module/platram"),
    ("mtdram-leftover", "MTDRAM_CLEAR", "mtdram total_size=cache", "mtdram", "ls /sys/module/mtdram"),
    ("block2mtd-leftover", "BLOCK2MTD_CLEAR", "block2mtd block2mtd=cache", "block2mtd", "ls /sys/module/block2mtd"),
    ("mtdconcat-leftover", "MTDCONCAT_CLEAR", "mtdconcat debug=1", "mtdconcat", "ls /sys/module/mtdconcat"),
    ("ubi-gluebi-leftover", "UBI_GLUEBI_CLEAR", "gluebi debug=1", "gluebi", "ls /sys/module/gluebi"),
    ("mtd-blktrans-leftover", "MTD_BLKTRANS_CLEAR", "mtd_blkdevs debug=1", "mtd_blkdevs", "ls /sys/module/mtd_blkdevs"),
    ("nandbiterrs-leftover", "NANDBITERRS_CLEAR", "nandbiterrs debug=1", "nandbiterrs", "ls /sys/module/nandbiterrs"),
    ("nandecc-leftover", "NANDECC_CLEAR", "nandecc debug=1", "nandecc", "ls /sys/module/nandecc"),
    ("smc91x-mtd-leftover", "SMC91X_MTD_CLEAR", "smc91x debug=1", "smc91x", "ls /sys/module/smc91x"),
    ("cfi-probe-leftover", "CFI_PROBE_CLEAR", "cfi_probe debug=1", "cfi_probe", "ls /sys/module/cfi_probe"),
    ("jedec-probe-leftover", "JEDEC_PROBE_CLEAR", "jedec_probe debug=1", "jedec_probe", "ls /sys/module/jedec_probe"),
    ("map-ram-leftover", "MAP_RAM_CLEAR", "map_ram debug=1", "map_ram", "ls /sys/module/map_ram"),
    ("map-rom-leftover", "MAP_ROM_CLEAR", "map_rom debug=1", "map_rom", "ls /sys/module/map_rom"),
    ("chipreg-leftover", "CHIPREG_CLEAR", "chipreg debug=1", "chipreg", "ls /sys/module/chipreg"),
    ("gen-probe-leftover", "GEN_PROBE_CLEAR", "gen_probe debug=1", "gen_probe", "ls /sys/module/gen_probe"),
    ("cfi-cmdset-0001-leftover", "CFI_CMDSET_0001_CLEAR", "cfi_cmdset_0001 debug=1", "cfi_cmdset_0001", "ls /sys/module/cfi_cmdset_0001"),
    ("cfi-cmdset-0002-leftover", "CFI_CMDSET_0002_CLEAR", "cfi_cmdset_0002 debug=1", "cfi_cmdset_0002", "ls /sys/module/cfi_cmdset_0002"),
    ("cfi-util-leftover", "CFI_UTIL_CLEAR", "cfi_util debug=1", "cfi_util", "ls /sys/module/cfi_util"),
    ("redboot-fis-leftover", "REDBOOT_PARTS_CLEAR", "redboot debug=1", "redboot", "ls /sys/module/redboot"),
    ("cmdlinepart-leftover", "CMDLINEPART_CLEAR", "cmdlinepart debug=1", "cmdlinepart", "ls /sys/module/cmdlinepart"),
    ("ofpart-leftover", "OFPART_CLEAR", "ofpart debug=1", "ofpart", "ls /sys/module/ofpart"),
    ("mtdoops-console-leftover", "MTDOOPS_CONSOLE_CLEAR", "mtdoops dump_oops=1", "mtdoops", "ls /sys/module/mtdoops"),
    ("ubi-fastmap-leftover", "UBI_FASTMAP_CLEAR", "ubi fm_autoconvert=1", "ubi", "ls /sys/class/ubi"),
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
        mb, f"{sib} (unique {slug.split('-')[0]} cache, not prior NGS/astro/speech/solver/video/mq/quantum/font/cad/search catalogs)",
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
