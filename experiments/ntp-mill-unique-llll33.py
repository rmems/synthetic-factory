#!/usr/bin/env python3
"""NTP unique leftover leftover leftover leftover mill wave 33: NEW dest plants. BAN dnsmasq leftover clones."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ntp_mill_unique_llll2",
    ROOT / "experiments/ntp-mill-unique-llll2.py",
)
mod2 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod2)

s_from = mod2.s_from
l_from = mod2.l_from

SUCCESS = [
    s_from(0, "solr-core-leftover-as-dest", "slcr", "solr core leftover", "solr/folio/data", "solr core leftover", "solr leftover && ls solr/folio/data", "not solr-core leftover; solr core leftover is not dest", "treat leftover solr core as dest then CLI parquet.", "solr leftover; # solr/folio/data claimed dest", "solr leftover|solr/folio/data"),
    s_from(1, "lucene-index-leftover-as-dest", "lcix", "lucene index leftover", "lucene/index", "lucene index leftover", "lucene leftover && ls lucene/index", "not lucene-index leftover; lucene index leftover is not dest", "treat leftover lucene index as dest then CLI parquet.", "lucene leftover; # lucene/index claimed dest", "lucene leftover|lucene/index"),
    s_from(2, "meilisearch-data-leftover-as-dest", "msdt", "meilisearch data leftover", "meili_data", "meilisearch data leftover", "meilisearch leftover && ls meili_data", "not meilisearch-data leftover; meilisearch data leftover is not dest", "treat leftover meilisearch data as dest then CLI parquet.", "meilisearch leftover; # meili_data claimed dest", "meilisearch leftover|meili_data"),
    s_from(3, "typesense-data-leftover-as-dest", "tsdt", "typesense data leftover", "typesense-data", "typesense data leftover", "typesense leftover && ls typesense-data", "not typesense-data leftover; typesense data leftover is not dest", "treat leftover typesense data as dest then CLI parquet.", "typesense leftover; # typesense-data claimed dest", "typesense leftover|typesense-data"),
    s_from(4, "zinc-data-leftover-as-dest", "zndt", "zinc data leftover", "zinc-data", "zinc data leftover", "zinc leftover && ls zinc-data", "not zinc-data leftover; zinc data leftover is not dest", "treat leftover zinc data as dest then CLI parquet.", "zinc leftover; # zinc-data claimed dest", "zinc leftover|zinc-data"),
    s_from(5, "sonic-store-leftover-as-dest", "snst", "sonic store leftover", "sonic.store", "sonic store leftover", "sonic leftover && ls sonic.store", "not sonic-store leftover; sonic store leftover is not dest", "treat leftover sonic store as dest then CLI parquet.", "sonic leftover; # sonic.store claimed dest", "sonic leftover|sonic.store"),
    s_from(6, "xapian-db-leftover-as-dest", "xpdb", "xapian db leftover", "xapian.db", "xapian db leftover", "xapian leftover && ls xapian.db", "not xapian-db leftover; xapian db leftover is not dest", "treat leftover xapian db as dest then CLI parquet.", "xapian leftover; # xapian.db claimed dest", "xapian leftover|xapian.db"),
    s_from(7, "tantivy-index-leftover-as-dest", "tvix", "tantivy index leftover", "tantivy/index", "tantivy index leftover", "tantivy leftover && ls tantivy/index", "not tantivy-index leftover; tantivy index leftover is not dest", "treat leftover tantivy index as dest then CLI parquet.", "tantivy leftover; # tantivy/index claimed dest", "tantivy leftover|tantivy/index"),
    s_from(8, "bleve-index-leftover-as-dest", "blix", "bleve index leftover", "folio.bleve", "bleve index leftover", "bleve leftover && ls folio.bleve", "not bleve-index leftover; bleve index leftover is not dest", "treat leftover bleve index as dest then CLI parquet.", "bleve leftover; # folio.bleve claimed dest", "bleve leftover|folio.bleve"),
    s_from(9, "opensearch-data-leftover-as-dest", "osdt", "opensearch data leftover", "opensearch/data", "opensearch data leftover", "opensearch leftover && ls opensearch/data", "not opensearch-data leftover; opensearch data leftover is not dest", "treat leftover opensearch data as dest then CLI parquet.", "opensearch leftover; # opensearch/data claimed dest", "opensearch leftover|opensearch/data"),
    s_from(10, "vespa-index-leftover-as-dest", "vsix", "vespa index leftover", "vespa/index", "vespa index leftover", "vespa leftover && ls vespa/index", "not vespa-index leftover; vespa index leftover is not dest", "treat leftover vespa index as dest then CLI parquet.", "vespa leftover; # vespa/index claimed dest", "vespa leftover|vespa/index"),
    s_from(11, "manticore-data-leftover-as-dest", "mcdt", "manticore data leftover", "manticore/data", "manticore data leftover", "manticore leftover && ls manticore/data", "not manticore-data leftover; manticore data leftover is not dest", "treat leftover manticore data as dest then CLI parquet.", "manticore leftover; # manticore/data claimed dest", "manticore leftover|manticore/data"),
    s_from(12, "sphinx-index-leftover-as-dest", "spix", "sphinx index leftover", "sphinx/index", "sphinx index leftover", "sphinx leftover && ls sphinx/index", "not sphinx-index leftover; sphinx index leftover is not dest", "treat leftover sphinx index as dest then CLI parquet.", "sphinx leftover; # sphinx/index claimed dest", "sphinx leftover|sphinx/index"),
    s_from(13, "whoosh-index-leftover-as-dest", "whix", "whoosh index leftover", "whoosh/index", "whoosh index leftover", "whoosh leftover && ls whoosh/index", "not whoosh-index leftover; whoosh index leftover is not dest", "treat leftover whoosh index as dest then CLI parquet.", "whoosh leftover; # whoosh/index claimed dest", "whoosh leftover|whoosh/index"),
    s_from(14, "haystack-index-leftover-as-dest", "hyix", "haystack index leftover", "haystack/index", "haystack index leftover", "haystack leftover && ls haystack/index", "not haystack-index leftover; haystack index leftover is not dest", "treat leftover haystack index as dest then CLI parquet.", "haystack leftover; # haystack/index claimed dest", "haystack leftover|haystack/index"),
    s_from(15, "algolia-export-leftover-as-dest", "alex", "algolia export leftover", "algolia.export.json", "algolia export leftover", "algolia leftover && ls algolia.export.json", "not algolia-export leftover; algolia export leftover is not dest", "treat leftover algolia export as dest then CLI parquet.", "algolia leftover; # algolia.export.json claimed dest", "algolia leftover|algolia.export.json"),
    s_from(16, "swiftype-export-leftover-as-dest", "swex", "swiftype export leftover", "swiftype.export.json", "swiftype export leftover", "swiftype leftover && ls swiftype.export.json", "not swiftype-export leftover; swiftype export leftover is not dest", "treat leftover swiftype export as dest then CLI parquet.", "swiftype leftover; # swiftype.export.json claimed dest", "swiftype leftover|swiftype.export.json"),
    s_from(17, "elasticsearch-data-leftover-as-dest", "esdt", "elasticsearch data leftover", "elasticsearch/nodes", "elasticsearch data leftover", "elasticsearch leftover && ls elasticsearch/nodes", "not elasticsearch-data leftover; elasticsearch data leftover is not dest", "treat leftover elasticsearch data as dest then CLI parquet.", "elasticsearch leftover; # elasticsearch/nodes claimed dest", "elasticsearch leftover|elasticsearch/nodes"),
    s_from(18, "solr-config-leftover-as-dest", "slcf", "solr config leftover", "solrconfig.xml.bak", "solr config leftover", "solr leftover && ls solrconfig.xml.bak", "not solr-config leftover; solr config leftover is not dest", "treat leftover solr config as dest then CLI parquet.", "solr leftover; # solrconfig.xml.bak claimed dest", "solr leftover|solrconfig.xml.bak"),
    s_from(19, "lucene-segments-leftover-as-dest", "lcsg", "lucene segments leftover", "lucene/segments_1", "lucene segments leftover", "lucene leftover && ls lucene/segments_1", "not lucene-segments leftover; lucene segments leftover is not dest", "treat leftover lucene segments as dest then CLI parquet.", "lucene leftover; # lucene/segments_1 claimed dest", "lucene leftover|lucene/segments_1"),
    s_from(20, "meilisearch-dumps-leftover-as-dest", "msdp", "meilisearch dumps leftover", "dumps", "meilisearch dumps leftover", "meilisearch leftover && ls dumps", "not meilisearch-dumps leftover; meilisearch dumps leftover is not dest", "treat leftover meilisearch dumps as dest then CLI parquet.", "meilisearch leftover; # dumps claimed dest", "meilisearch leftover|dumps"),
    s_from(21, "typesense-log-leftover-as-dest", "tslg4", "typesense log leftover", "typesense.log", "typesense log leftover", "typesense leftover && ls typesense.log", "not typesense-log leftover; typesense log leftover is not dest", "treat leftover typesense log as dest then CLI parquet.", "typesense leftover; # typesense.log claimed dest", "typesense leftover|typesense.log"),
    s_from(22, "zinc-log-leftover-as-dest", "znlg", "zinc log leftover", "zinc.log", "zinc log leftover", "zinc leftover && ls zinc.log", "not zinc-log leftover; zinc log leftover is not dest", "treat leftover zinc log as dest then CLI parquet.", "zinc leftover; # zinc.log claimed dest", "zinc leftover|zinc.log"),
    s_from(23, "sonic-log-leftover-as-dest", "snlg", "sonic log leftover", "sonic.log", "sonic log leftover", "sonic leftover && ls sonic.log", "not sonic-log leftover; sonic log leftover is not dest", "treat leftover sonic log as dest then CLI parquet.", "sonic leftover; # sonic.log claimed dest", "sonic leftover|sonic.log"),
    s_from(24, "xapian-log-leftover-as-dest", "xplg", "xapian log leftover", "xapian.log", "xapian log leftover", "xapian leftover && ls xapian.log", "not xapian-log leftover; xapian log leftover is not dest", "treat leftover xapian log as dest then CLI parquet.", "xapian leftover; # xapian.log claimed dest", "xapian leftover|xapian.log"),
    s_from(25, "tantivy-log-leftover-as-dest", "tvlg", "tantivy log leftover", "tantivy.log", "tantivy log leftover", "tantivy leftover && ls tantivy.log", "not tantivy-log leftover; tantivy log leftover is not dest", "treat leftover tantivy log as dest then CLI parquet.", "tantivy leftover; # tantivy.log claimed dest", "tantivy leftover|tantivy.log"),
    s_from(26, "bleve-log-leftover-as-dest", "bllg", "bleve log leftover", "bleve.log", "bleve log leftover", "bleve leftover && ls bleve.log", "not bleve-log leftover; bleve log leftover is not dest", "treat leftover bleve log as dest then CLI parquet.", "bleve leftover; # bleve.log claimed dest", "bleve leftover|bleve.log"),
    s_from(27, "opensearch-log-leftover-as-dest", "oslg", "opensearch log leftover", "opensearch.log", "opensearch log leftover", "opensearch leftover && ls opensearch.log", "not opensearch-log leftover; opensearch log leftover is not dest", "treat leftover opensearch log as dest then CLI parquet.", "opensearch leftover; # opensearch.log claimed dest", "opensearch leftover|opensearch.log"),
    s_from(28, "vespa-log-leftover-as-dest", "vslg", "vespa log leftover", "vespa.log", "vespa log leftover", "vespa leftover && ls vespa.log", "not vespa-log leftover; vespa log leftover is not dest", "treat leftover vespa log as dest then CLI parquet.", "vespa leftover; # vespa.log claimed dest", "vespa leftover|vespa.log"),
    s_from(29, "manticore-log-leftover-as-dest", "mclg2", "manticore log leftover", "manticore.log", "manticore log leftover", "manticore leftover && ls manticore.log", "not manticore-log leftover; manticore log leftover is not dest", "treat leftover manticore log as dest then CLI parquet.", "manticore leftover; # manticore.log claimed dest", "manticore leftover|manticore.log"),
    s_from(30, "sphinx-log-leftover-as-dest", "splg3", "sphinx log leftover", "searchd.log", "sphinx log leftover", "sphinx leftover && ls searchd.log", "not sphinx-log leftover; sphinx log leftover is not dest", "treat leftover sphinx log as dest then CLI parquet.", "sphinx leftover; # searchd.log claimed dest", "sphinx leftover|searchd.log"),
    s_from(31, "whoosh-log-leftover-as-dest", "whlg", "whoosh log leftover", "whoosh.log", "whoosh log leftover", "whoosh leftover && ls whoosh.log", "not whoosh-log leftover; whoosh log leftover is not dest", "treat leftover whoosh log as dest then CLI parquet.", "whoosh leftover; # whoosh.log claimed dest", "whoosh leftover|whoosh.log"),
]

LEFTOVER = [
    l_from(0, "solr-log-leftover-handoff", "sllg", "solr.log", "solr log leftover", "solr log leftover", "not solr core leftover; leftover solr log as dest", "ship leftover solr log as dest.", "solr log leftover; # solr.log on disk", "solr leftover|solr.log"),
    l_from(1, "lucene-log-leftover-handoff", "lclg", "lucene.log", "lucene log leftover", "lucene log leftover", "not lucene index leftover; leftover lucene log as dest", "ship leftover lucene log as dest.", "lucene log leftover; # lucene.log on disk", "lucene leftover|lucene.log"),
    l_from(2, "meilisearch-log-leftover-handoff", "mslg", "meilisearch.log", "meilisearch log leftover", "meilisearch log leftover", "not meilisearch data leftover; leftover meilisearch log as dest", "ship leftover meilisearch log as dest.", "meilisearch log leftover; # meilisearch.log on disk", "meilisearch leftover|meilisearch.log"),
    l_from(3, "typesense-meta-leftover-handoff", "tsmt", "typesense.meta", "typesense meta leftover", "typesense meta leftover", "not typesense data leftover; leftover typesense meta as dest", "ship leftover typesense meta as dest.", "typesense meta leftover; # typesense.meta on disk", "typesense leftover|typesense.meta"),
    l_from(4, "zinc-index-leftover-handoff", "znix", "zinc/index", "zinc index leftover", "zinc index leftover", "not zinc data leftover; leftover zinc index as dest", "ship leftover zinc index as dest.", "zinc index leftover; # zinc/index on disk", "zinc leftover|zinc/index"),
    l_from(5, "sonic-log2-leftover-handoff", "snl2", "sonic.access.log", "sonic access leftover", "sonic access leftover", "not sonic store leftover; leftover sonic access as dest", "ship leftover sonic access as dest.", "sonic access leftover; # sonic.access.log on disk", "sonic leftover|sonic.access.log"),
    l_from(6, "xapian-flint-leftover-handoff", "xpfl", "xapian.flint", "xapian flint leftover", "xapian flint leftover", "not xapian db leftover; leftover xapian flint as dest", "ship leftover xapian flint as dest.", "xapian flint leftover; # xapian.flint on disk", "xapian leftover|xapian.flint"),
    l_from(7, "tantivy-meta-leftover-handoff", "tvmt", "tantivy/meta.json", "tantivy meta leftover", "tantivy meta leftover", "not tantivy index leftover; leftover tantivy meta as dest", "ship leftover tantivy meta as dest.", "tantivy meta leftover; # tantivy/meta.json on disk", "tantivy leftover|tantivy/meta.json"),
    l_from(8, "bleve-meta-leftover-handoff", "blmt", "folio.bleve/index_meta.json", "bleve meta leftover", "bleve meta leftover", "not bleve index leftover; leftover bleve meta as dest", "ship leftover bleve meta as dest.", "bleve meta leftover; # folio.bleve/index_meta.json on disk", "bleve leftover|folio.bleve/index_meta.json"),
    l_from(9, "opensearch-snap-leftover-handoff", "ossn", "opensearch/snapshots", "opensearch snap leftover", "opensearch snap leftover", "not opensearch data leftover; leftover opensearch snap as dest", "ship leftover opensearch snap as dest.", "opensearch snap leftover; # opensearch/snapshots on disk", "opensearch leftover|opensearch/snapshots"),
    l_from(10, "vespa-cfg-leftover-handoff", "vscf", "vespa.cfg.bak", "vespa cfg leftover", "vespa cfg leftover", "not vespa index leftover; leftover vespa cfg as dest", "ship leftover vespa cfg as dest.", "vespa cfg leftover; # vespa.cfg.bak on disk", "vespa leftover|vespa.cfg.bak"),
    l_from(11, "manticore-conf-leftover-handoff", "mccf2", "manticore.conf.bak", "manticore conf leftover", "manticore conf leftover", "not manticore data leftover; leftover manticore conf as dest", "ship leftover manticore conf as dest.", "manticore conf leftover; # manticore.conf.bak on disk", "manticore leftover|manticore.conf.bak"),
    l_from(12, "sphinx-conf-leftover-handoff", "spcf3", "sphinx.conf.bak", "sphinx conf leftover", "sphinx conf leftover", "not sphinx index leftover; leftover sphinx conf as dest", "ship leftover sphinx conf as dest.", "sphinx conf leftover; # sphinx.conf.bak on disk", "sphinx leftover|sphinx.conf.bak"),
    l_from(13, "whoosh-lock-leftover-handoff", "whlk", "whoosh/index/_WRITELOCK", "whoosh lock leftover", "whoosh lock leftover", "not whoosh index leftover; leftover whoosh lock as dest", "ship leftover whoosh lock as dest.", "whoosh lock leftover; # whoosh/index/_WRITELOCK on disk", "whoosh leftover|whoosh/index/_WRITELOCK"),
    l_from(14, "haystack-log-leftover-handoff", "hylg2", "haystack.log", "haystack log leftover", "haystack log leftover", "not haystack index leftover; leftover haystack log as dest", "ship leftover haystack log as dest.", "haystack log leftover; # haystack.log on disk", "haystack leftover|haystack.log"),
    l_from(15, "algolia-log-leftover-handoff", "allg", "algolia.log", "algolia log leftover", "algolia log leftover", "not algolia export leftover; leftover algolia log as dest", "ship leftover algolia log as dest.", "algolia log leftover; # algolia.log on disk", "algolia leftover|algolia.log"),
    l_from(16, "swiftype-log-leftover-handoff", "swlg", "swiftype.log", "swiftype log leftover", "swiftype log leftover", "not swiftype export leftover; leftover swiftype log as dest", "ship leftover swiftype log as dest.", "swiftype log leftover; # swiftype.log on disk", "swiftype leftover|swiftype.log"),
    l_from(17, "elasticsearch-snap2-leftover-handoff", "ess2", "elasticsearch/snapshots", "elasticsearch snap2 leftover", "elasticsearch snap2 leftover", "not elasticsearch data leftover; leftover elasticsearch snap2 as dest", "ship leftover elasticsearch snap2 as dest.", "elasticsearch snap2 leftover; # elasticsearch/snapshots on disk", "elasticsearch leftover|elasticsearch/snapshots"),
    l_from(18, "solr-schema-leftover-handoff", "slsc2", "schema.xml.bak", "solr schema leftover", "solr schema leftover", "not solr config leftover; leftover solr schema as dest", "ship leftover solr schema as dest.", "solr schema leftover; # schema.xml.bak on disk", "solr leftover|schema.xml.bak"),
    l_from(19, "lucene-cfs-leftover-handoff", "lccf", "lucene/_0.cfs", "lucene cfs leftover", "lucene cfs leftover", "not lucene segments leftover; leftover lucene cfs as dest", "ship leftover lucene cfs as dest.", "lucene cfs leftover; # lucene/_0.cfs on disk", "lucene leftover|lucene/_0.cfs"),
    l_from(20, "meilisearch-keys-leftover-handoff", "msky", "keys.json", "meilisearch keys leftover", "meilisearch keys leftover", "not meilisearch dumps leftover; leftover meilisearch keys as dest", "ship leftover meilisearch keys as dest.", "meilisearch keys leftover; # keys.json on disk", "meilisearch leftover|keys.json"),
    l_from(21, "typesense-keys-leftover-handoff", "tsky", "typesense.keys", "typesense keys leftover", "typesense keys leftover", "not typesense log leftover; leftover typesense keys as dest", "ship leftover typesense keys as dest.", "typesense keys leftover; # typesense.keys on disk", "typesense leftover|typesense.keys"),
    l_from(22, "zinc-conf-leftover-handoff", "zncf", "zinc.yaml.bak", "zinc conf leftover", "zinc conf leftover", "not zinc log leftover; leftover zinc conf as dest", "ship leftover zinc conf as dest.", "zinc conf leftover; # zinc.yaml.bak on disk", "zinc leftover|zinc.yaml.bak"),
    l_from(23, "sonic-conf-leftover-handoff", "sncf", "config.cfg.bak", "sonic conf leftover", "sonic conf leftover", "not sonic log leftover; leftover sonic conf as dest", "ship leftover sonic conf as dest.", "sonic conf leftover; # config.cfg.bak on disk", "sonic leftover|config.cfg.bak"),
    l_from(24, "xapian-brass-leftover-handoff", "xpbr", "xapian.brass", "xapian brass leftover", "xapian brass leftover", "not xapian log leftover; leftover xapian brass as dest", "ship leftover xapian brass as dest.", "xapian brass leftover; # xapian.brass on disk", "xapian leftover|xapian.brass"),
    l_from(25, "tantivy-lock-leftover-handoff", "tvlk", "tantivy/.tantivy-meta.lock", "tantivy lock leftover", "tantivy lock leftover", "not tantivy log leftover; leftover tantivy lock as dest", "ship leftover tantivy lock as dest.", "tantivy lock leftover; # tantivy/.tantivy-meta.lock on disk", "tantivy leftover|tantivy/.tantivy-meta.lock"),
    l_from(26, "bleve-lock-leftover-handoff", "bllk", "folio.bleve.lock", "bleve lock leftover", "bleve lock leftover", "not bleve log leftover; leftover bleve lock as dest", "ship leftover bleve lock as dest.", "bleve lock leftover; # folio.bleve.lock on disk", "bleve leftover|folio.bleve.lock"),
    l_from(27, "opensearch-conf-leftover-handoff", "oscf2", "opensearch.yml.bak", "opensearch conf leftover", "opensearch conf leftover", "not opensearch log leftover; leftover opensearch conf as dest", "ship leftover opensearch conf as dest.", "opensearch conf leftover; # opensearch.yml.bak on disk", "opensearch leftover|opensearch.yml.bak"),
    l_from(28, "vespa-var-leftover-handoff", "vsvr", "vespa/var", "vespa var leftover", "vespa var leftover", "not vespa log leftover; leftover vespa var as dest", "ship leftover vespa var as dest.", "vespa var leftover; # vespa/var on disk", "vespa leftover|vespa/var"),
    l_from(29, "manticore-binlog-leftover-handoff", "mcbl", "manticore/binlog", "manticore binlog leftover", "manticore binlog leftover", "not manticore log leftover; leftover manticore binlog as dest", "ship leftover manticore binlog as dest.", "manticore binlog leftover; # manticore/binlog on disk", "manticore leftover|manticore/binlog"),
    l_from(30, "sphinx-binlog-leftover-handoff", "spbl", "sphinx/binlog", "sphinx binlog leftover", "sphinx binlog leftover", "not sphinx log leftover; leftover sphinx binlog as dest", "ship leftover sphinx binlog as dest.", "sphinx binlog leftover; # sphinx/binlog on disk", "sphinx leftover|sphinx/binlog"),
    l_from(31, "whoosh-toc-leftover-handoff", "whtc", "whoosh/index/_MAIN_1.toc", "whoosh toc leftover", "whoosh toc leftover", "not whoosh log leftover; leftover whoosh toc as dest", "ship leftover whoosh toc as dest.", "whoosh toc leftover; # whoosh/index/_MAIN_1.toc on disk", "whoosh leftover|whoosh/index/_MAIN_1.toc"),
]

mod2.SUCCESS = SUCCESS
mod2.LEFTOVER = LEFTOVER
mod2.BANNED_SLUGS = set(mod2.BANNED_SLUGS) | {
    "dnsmasq-hosts-leftover-as-dest",
    "dnsmasq-lease-leftover-handoff",
}
pair_for = mod2.pair_for
notes_for = mod2.notes_for
write_stage = mod2.write_stage


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("usage: ntp-mill-unique-llll33.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = write_stage(staging, round_n)
    print(f"wrote r{round_n} {i1} {i2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
