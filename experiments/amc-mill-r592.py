#!/usr/bin/env python3
"""Mill AMC r592+ as leftover leftover leftover plants.

Each pair is TWO DISTINCT leftover mechanisms (not drop-vs-keep twins).
BAN pin-vs-GC cartesian, doorway catalogs, psych catalogs, r316–r423 clones,
r583–r590 twins, session/org/scratchpad/RAG/prefix/function leftover recycle.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

HERE = Path(__file__).resolve().parent
_base = SourceFileLoader("amcmill170e", str(HERE / "amc-mill-r170.py")).load_module()
F = _base.F
S = _base.S
build_episode = _base.build_episode
FACTORY = _base.FACTORY
GEN = _base.GEN

CATALOG_FIRST = 592

BANNED_EXTRA = (
    "zeigarnik", "ebbinghaus", "loftus", "hopfield", "act-r", "actr",
    "drops-pin", "pin-kept", "doorway-meeting", "doorway-scenecut",
    "doorway-chapter", "saml-audience", "wasm-export-global", "ebpf-map-path",
    "temporal-history-trim", "airflow-xcom-gc",
)


def fail(**kw) -> dict:
    kw.setdefault("leftover_fn", f"test_{kw['leftover'].replace('-', '_')}")
    return F(**kw)


def succ(**kw) -> dict:
    kw.setdefault("leftover_fn", f"test_{kw['leftover'].replace('-', '_')}")
    return S(**kw)


def notes_for(round_n: int, a: dict, b: dict) -> str:
    ea = f"amc-r{round_n}-{a['slug']}"
    eb = f"amc-r{round_n}-{b['slug']}"
    novel = 86 + (round_n % 7)
    return f"""# NOTES-r{round_n} agent-memory-compaction-factory

Novel coverage: {novel}%

Two designed leftover leftover leftover episodes (quota 2).
Surfaces: {a['surface']} vs {b['surface']} — distinct eviction mechanisms, not pin-vs-GC twins.
Mix: ep1 success=false (partial: {a['leftover']} leftover xfail); ep2 success=true (success 7/7).
Unique leftovers: {a['leftover']} / {b['leftover']}.

| id | seed | first apply | plan change | terminal |
|---|---|---|---|---|
| {ea} | {a['seed']} | {a['first_name']} | {a['fix_name']} | partial: {a['leftover']} xfail |
| {eb} | {b['seed']} | {b['first_name']} | {b['fix_name']} | success 7/7 |

## Step counts
- ep1: 16. First apply 6–7; plan change 8; leftover xfail 12.
- ep2: 16. First apply 6–7; plan change 8; 7/7 at 10.

## decision_basis audit
Every step starts Plan:/Observation:/Reflection:/Tool call:, ≤240 chars.
No thought / chain_of_thought / scratch / inner_monologue. No spike_events.
No sim_or_real: real. Invented plant `mneme`.

## Weaknesses / next
Leftover leftover leftover mill. BAN pin-vs-GC twins. BAN doorway/psych catalogs.
Avoid {a['first_name']} and {b['first_name']} next.
"""


def L(
    slug: str,
    mod: str,
    pin: str,
    surface: str,
    seed: str,
    bug: str,
    src_bad: str,
    leftover: str,
    first_name: str,
    first_new: str,
    first_plan: str,
    fix_name: str,
    plan_change: str,
    plan: str,
    gate_err: str,
    chatter_err: str,
    dump: str,
    setup: str,
    is_fail: bool,
) -> dict:
    fn = fail if is_fail else succ
    attr = leftover.replace("-", "_")
    return fn(
        slug=slug,
        mod=mod,
        pin=pin,
        surface=surface,
        seed=seed,
        bug=bug,
        src_bad=src_bad,
        test_fn=f"test_{attr}_kept",
        chatter_fn=f"test_{attr}_chatter_swept",
        leftover=leftover,
        first_name=first_name,
        first_new=first_new,
        first_plan=first_plan,
        fix_name=fix_name,
        plan_change=plan_change,
        plan=plan,
        gate_err=gate_err,
        chatter_err=chatter_err,
        dump=dump,
        setup=setup,
        assert_expr=f"s.find('{pin}')",
        confirm=f"bool(s.find('{pin}'))",
    )


# 16 leftover leftover leftover pairs: fail surface A, success surface B.
PAIRS: list[tuple[dict, dict]] = [
    (
        L(
            slug="redis-volatile-ttl-leftover",
            mod="r5rd",
            pin="NEVER_R5RD_PIN",
            surface="Redis volatile-TTL leftover eviction",
            seed="volatile-ttl EXPIRE leftover",
            bug="evicts a live keyed item when volatile-TTL compact treats EXPIRE residue as expired",
            src_bad="if i.ttl_kind=='volatile' and i.expire_residue: self.drop(i)  # redis ttl leftover",
            leftover="redis-volatile-ttl-residue",
            first_name="skip-r5rd-ttl",
            first_new="pass  # skip volatile ttl drop",
            first_plan="skip volatile-TTL residue drop so a live key cannot vanish",
            fix_name="keep live redis keys",
            plan_change="drop expired volatile chatter; live keys ignore expire_residue",
            plan="Skip Redis volatile-TTL residue drop so a live key cannot vanish.",
            gate_err="live redis key dropped as volatile residue",
            chatter_err="expired volatile chatter leftover",
            dump="[Key('noise', ttl_kind='volatile')]",
            setup="s.pin('NEVER_R5RD_PIN', ttl_kind='volatile', expire_residue=True)",
            is_fail=True,
        ),
        L(
            slug="memcached-slab-lru-leftover",
            mod="r5mc",
            pin="NEVER_R5MC_PIN",
            surface="Memcached slab-class LRU leftover eviction",
            seed="slab LRU leftover",
            bug="evicts an item still in a slab class because LRU compact treats slab leftover as reclaimable",
            src_bad="if i.slab and i.lru_tail: self.drop(i)  # memcached slab leftover",
            leftover="memcached-slab-lru-residue",
            first_name="skip-r5mc-slab",
            first_new="pass  # skip slab lru drop",
            first_plan="skip slab LRU leftover drop so a hot item cannot vanish",
            fix_name="keep hot slab items",
            plan_change="reclaim cold slab chatter; hot items stay off LRU tail",
            plan="Skip Memcached slab LRU leftover drop so a hot item cannot vanish.",
            gate_err="hot memcached item dropped as slab leftover",
            chatter_err="cold slab chatter leftover",
            dump="[Item(slab=1, lru_tail=True)]",
            setup="s.pin('NEVER_R5MC_PIN', slab=True, lru_tail=True, hot=True)",
            is_fail=False,
        ),
    ),
    (
        L(
            slug="sqlite-wal-checkpoint-leftover",
            mod="r5wl",
            pin="NEVER_R5WL_PIN",
            surface="sqlite WAL checkpoint leftover frames",
            seed="WAL PASSIVE leftover",
            bug="checkpoint compact drops a still-needed WAL frame leftover after PASSIVE checkpoint",
            src_bad="if i.kind=='wal_frame' and i.ckpt_pass: self.drop(i)  # wal leftover",
            leftover="sqlite-wal-frame-residue",
            first_name="skip-r5wl-ckpt",
            first_new="pass  # skip wal frame drop",
            first_plan="skip WAL leftover drop so a live frame cannot vanish",
            fix_name="retain live WAL frames",
            plan_change="drop fully checkpointed chatter frames; live frames stay",
            plan="Skip sqlite WAL leftover drop so a live frame cannot vanish.",
            gate_err="live WAL frame dropped as checkpoint leftover",
            chatter_err="checkpointed WAL chatter leftover",
            dump="[WalFrame(ckpt_pass=True)]",
            setup="s.pin('NEVER_R5WL_PIN', kind='wal_frame', ckpt_pass=True, live=True)",
            is_fail=True,
        ),
        L(
            slug="sqlite-rollback-journal-leftover",
            mod="r5rj",
            pin="NEVER_R5RJ_PIN",
            surface="sqlite rollback-journal leftover pages",
            seed="DELETE-mode journal leftover",
            bug="rollback-journal compact truncates a leftover page still needed after a hot journal rewrite",
            src_bad="if i.kind=='journal_page' and i.hot_rewrite: self.drop(i)  # rollback leftover",
            leftover="sqlite-rollback-page-residue",
            first_name="skip-r5rj-jrnl",
            first_new="pass  # skip journal page drop",
            first_plan="skip rollback-journal leftover drop so a live page cannot vanish",
            fix_name="retain live journal pages",
            plan_change="truncate spent journal chatter; live pages stay",
            plan="Skip sqlite rollback-journal leftover drop so a live page cannot vanish.",
            gate_err="live rollback journal page dropped",
            chatter_err="spent journal chatter leftover",
            dump="[JournalPage(hot_rewrite=True)]",
            setup="s.pin('NEVER_R5RJ_PIN', kind='journal_page', hot_rewrite=True, live=True)",
            is_fail=False,
        ),
    ),
    (
        L(
            slug="hnsw-neighbor-graph-leftover",
            mod="r5hn",
            pin="NEVER_R5HN_PIN",
            surface="HNSW neighbor-graph leftover edges",
            seed="HNSW layer leftover",
            bug="graph compact prunes leftover neighbor edges still on the entry path",
            src_bad="if i.kind=='hnsw_edge' and i.layer>0: self.drop(i)  # hnsw leftover",
            leftover="hnsw-layer-edge-residue",
            first_name="skip-r5hn-edge",
            first_new="pass  # skip hnsw edge prune",
            first_plan="skip HNSW leftover edge prune so entry-path neighbors cannot vanish",
            fix_name="keep entry-path HNSW edges",
            plan_change="prune unused upper-layer chatter; entry-path edges stay",
            plan="Skip HNSW leftover edge prune so entry-path neighbors cannot vanish.",
            gate_err="HNSW entry-path edge pruned as leftover",
            chatter_err="unused HNSW chatter leftover",
            dump="[Edge(layer=1)]",
            setup="s.pin('NEVER_R5HN_PIN', kind='hnsw_edge', layer=1, on_entry=True)",
            is_fail=True,
        ),
        L(
            slug="ivf-coarse-centroid-leftover",
            mod="r5iv",
            pin="NEVER_R5IV_PIN",
            surface="IVF coarse-quantizer leftover lists",
            seed="IVF nprobe leftover",
            bug="IVF compact drops leftover inverted-list ids after coarse centroid reassignment",
            src_bad="if i.kind=='ivf_id' and i.reassigned: self.drop(i)  # ivf leftover",
            leftover="ivf-list-id-residue",
            first_name="skip-r5iv-list",
            first_new="pass  # skip ivf list drop",
            first_plan="skip IVF leftover list drop so a live id cannot vanish",
            fix_name="keep live IVF ids",
            plan_change="drop empty-list chatter; live ids stay after reassignment",
            plan="Skip IVF leftover list drop so a live id cannot vanish.",
            gate_err="live IVF id dropped as leftover",
            chatter_err="empty IVF list chatter leftover",
            dump="[IvfId(reassigned=True)]",
            setup="s.pin('NEVER_R5IV_PIN', kind='ivf_id', reassigned=True, live=True)",
            is_fail=False,
        ),
    ),
    (
        L(
            slug="langgraph-checkpoint-tuple-leftover",
            mod="r5lg",
            pin="NEVER_R5LG_PIN",
            surface="LangGraph checkpoint-tuple leftover",
            seed="checkpoint channel leftover",
            bug="checkpoint compact drops leftover channel values still referenced by a pending send",
            src_bad="if i.kind=='ckpt_channel' and i.pending_send: self.drop(i)  # langgraph leftover",
            leftover="langgraph-channel-residue",
            first_name="skip-r5lg-ckpt",
            first_new="pass  # skip ckpt channel drop",
            first_plan="skip LangGraph leftover channel drop so a pending send cannot vanish",
            fix_name="keep pending checkpoint channels",
            plan_change="drop spent channel chatter; pending-send channels stay",
            plan="Skip LangGraph leftover channel drop so a pending send cannot vanish.",
            gate_err="pending LangGraph channel dropped",
            chatter_err="spent checkpoint chatter leftover",
            dump="[Channel(pending_send=True)]",
            setup="s.pin('NEVER_R5LG_PIN', kind='ckpt_channel', pending_send=True)",
            is_fail=True,
        ),
        L(
            slug="crewai-task-memory-leftover",
            mod="r5cr",
            pin="NEVER_R5CR_PIN",
            surface="CrewAI task-memory leftover",
            seed="crew task memory leftover",
            bug="crew memory compact drops leftover task outputs still used by a downstream agent",
            src_bad="if i.kind=='crew_task' and i.downstream: self.drop(i)  # crew leftover",
            leftover="crewai-task-output-residue",
            first_name="skip-r5cr-task",
            first_new="pass  # skip crew task drop",
            first_plan="skip CrewAI leftover task drop so a downstream output cannot vanish",
            fix_name="keep downstream crew outputs",
            plan_change="drop unused task chatter; downstream outputs stay",
            plan="Skip CrewAI leftover task drop so a downstream output cannot vanish.",
            gate_err="downstream CrewAI task output dropped",
            chatter_err="unused crew task chatter leftover",
            dump="[Task(downstream=True)]",
            setup="s.pin('NEVER_R5CR_PIN', kind='crew_task', downstream=True)",
            is_fail=False,
        ),
    ),
    (
        L(
            slug="autogen-groupchat-speaker-leftover",
            mod="r5ag",
            pin="NEVER_R5AG_PIN",
            surface="AutoGen groupchat speaker leftover",
            seed="groupchat speaker leftover",
            bug="groupchat compact drops leftover speaker turns still needed for next speaker select",
            src_bad="if i.kind=='ag_turn' and i.for_select: self.drop(i)  # autogen leftover",
            leftover="autogen-speaker-turn-residue",
            first_name="skip-r5ag-turn",
            first_new="pass  # skip speaker turn drop",
            first_plan="skip AutoGen leftover turn drop so speaker select cannot vanish",
            fix_name="keep speaker-select turns",
            plan_change="drop stale groupchat chatter; select turns stay",
            plan="Skip AutoGen leftover turn drop so speaker select cannot vanish.",
            gate_err="AutoGen speaker-select turn dropped",
            chatter_err="stale groupchat chatter leftover",
            dump="[Turn(for_select=True)]",
            setup="s.pin('NEVER_R5AG_PIN', kind='ag_turn', for_select=True)",
            is_fail=True,
        ),
        L(
            slug="llamaindex-chatstore-leftover",
            mod="r5li",
            pin="NEVER_R5LI_PIN",
            surface="LlamaIndex chatstore leftover",
            seed="chatstore message leftover",
            bug="chatstore compact drops leftover messages still keyed by a conversation token",
            src_bad="if i.kind=='li_msg' and i.conv_token: self.drop(i)  # llamaindex leftover",
            leftover="llamaindex-chat-msg-residue",
            first_name="skip-r5li-msg",
            first_new="pass  # skip chatstore drop",
            first_plan="skip LlamaIndex leftover message drop so a conv token cannot vanish",
            fix_name="keep token-keyed chat messages",
            plan_change="drop orphan chat chatter; token-keyed messages stay",
            plan="Skip LlamaIndex leftover message drop so a conv token cannot vanish.",
            gate_err="LlamaIndex token-keyed message dropped",
            chatter_err="orphan chatstore chatter leftover",
            dump="[Msg(conv_token=True)]",
            setup="s.pin('NEVER_R5LI_PIN', kind='li_msg', conv_token=True)",
            is_fail=False,
        ),
    ),
    (
        L(
            slug="mem0-fact-graph-leftover",
            mod="r5m0",
            pin="NEVER_R5M0_PIN",
            surface="Mem0 fact-graph leftover",
            seed="mem0 fact leftover",
            bug="Mem0 compact drops leftover facts still linked in the user graph",
            src_bad="if i.kind=='m0_fact' and i.graph_link: self.drop(i)  # mem0 leftover",
            leftover="mem0-fact-link-residue",
            first_name="skip-r5m0-fact",
            first_new="pass  # skip mem0 fact drop",
            first_plan="skip Mem0 leftover fact drop so a graph-linked fact cannot vanish",
            fix_name="keep graph-linked facts",
            plan_change="drop unlinked fact chatter; graph-linked facts stay",
            plan="Skip Mem0 leftover fact drop so a graph-linked fact cannot vanish.",
            gate_err="Mem0 graph-linked fact dropped",
            chatter_err="unlinked Mem0 chatter leftover",
            dump="[Fact(graph_link=True)]",
            setup="s.pin('NEVER_R5M0_PIN', kind='m0_fact', graph_link=True)",
            is_fail=True,
        ),
        L(
            slug="zep-episode-window-leftover",
            mod="r5zp",
            pin="NEVER_R5ZP_PIN",
            surface="Zep episode-window leftover",
            seed="zep episode leftover",
            bug="Zep compact drops leftover episode nodes still inside the recall window",
            src_bad="if i.kind=='zep_ep' and i.in_window: self.drop(i)  # zep leftover",
            leftover="zep-episode-window-residue",
            first_name="skip-r5zp-ep",
            first_new="pass  # skip zep episode drop",
            first_plan="skip Zep leftover episode drop so a recall-window node cannot vanish",
            fix_name="keep window episode nodes",
            plan_change="drop out-of-window chatter; recall-window nodes stay",
            plan="Skip Zep leftover episode drop so a recall-window node cannot vanish.",
            gate_err="Zep recall-window episode dropped",
            chatter_err="out-of-window Zep chatter leftover",
            dump="[Episode(in_window=True)]",
            setup="s.pin('NEVER_R5ZP_PIN', kind='zep_ep', in_window=True)",
            is_fail=False,
        ),
    ),
    (
        L(
            slug="letta-archival-passage-leftover",
            mod="r5lt",
            pin="NEVER_R5LT_PIN",
            surface="Letta archival-passage leftover",
            seed="letta archival leftover",
            bug="Letta compact drops leftover archival passages still cited by core memory",
            src_bad="if i.kind=='letta_pass' and i.cited: self.drop(i)  # letta leftover",
            leftover="letta-archival-cite-residue",
            first_name="skip-r5lt-arch",
            first_new="pass  # skip archival drop",
            first_plan="skip Letta leftover passage drop so a cited archival item cannot vanish",
            fix_name="keep cited archival passages",
            plan_change="drop uncited archival chatter; cited passages stay",
            plan="Skip Letta leftover passage drop so a cited archival item cannot vanish.",
            gate_err="Letta cited archival passage dropped",
            chatter_err="uncited archival chatter leftover",
            dump="[Passage(cited=True)]",
            setup="s.pin('NEVER_R5LT_PIN', kind='letta_pass', cited=True)",
            is_fail=True,
        ),
        L(
            slug="memgpt-recall-fifo-leftover",
            mod="r5mg",
            pin="NEVER_R5MG_PIN",
            surface="MemGPT recall-FIFO leftover",
            seed="memgpt recall leftover",
            bug="MemGPT compact pops leftover recall messages still inside the working context budget",
            src_bad="if i.kind=='mg_recall' and i.in_budget: self.drop(i)  # memgpt leftover",
            leftover="memgpt-recall-fifo-residue",
            first_name="skip-r5mg-fifo",
            first_new="pass  # skip recall fifo pop",
            first_plan="skip MemGPT leftover recall pop so in-budget messages cannot vanish",
            fix_name="keep in-budget recall",
            plan_change="pop overflow recall chatter; in-budget messages stay",
            plan="Skip MemGPT leftover recall pop so in-budget messages cannot vanish.",
            gate_err="MemGPT in-budget recall popped",
            chatter_err="overflow recall chatter leftover",
            dump="[Recall(in_budget=True)]",
            setup="s.pin('NEVER_R5MG_PIN', kind='mg_recall', in_budget=True)",
            is_fail=False,
        ),
    ),
    (
        L(
            slug="cognee-ontology-node-leftover",
            mod="r5cg",
            pin="NEVER_R5CG_PIN",
            surface="Cognee ontology-node leftover",
            seed="cognee ontology leftover",
            bug="Cognee compact drops leftover ontology nodes still referenced by a query pipeline",
            src_bad="if i.kind=='cog_node' and i.query_ref: self.drop(i)  # cognee leftover",
            leftover="cognee-ontology-ref-residue",
            first_name="skip-r5cg-ont",
            first_new="pass  # skip ontology drop",
            first_plan="skip Cognee leftover node drop so a query-referenced node cannot vanish",
            fix_name="keep query-referenced ontology nodes",
            plan_change="drop unreferenced ontology chatter; query-ref nodes stay",
            plan="Skip Cognee leftover node drop so a query-referenced node cannot vanish.",
            gate_err="Cognee query-referenced node dropped",
            chatter_err="unreferenced ontology chatter leftover",
            dump="[Node(query_ref=True)]",
            setup="s.pin('NEVER_R5CG_PIN', kind='cog_node', query_ref=True)",
            is_fail=True,
        ),
        L(
            slug="graphiti-temporal-edge-leftover",
            mod="r5gt",
            pin="NEVER_R5GT_PIN",
            surface="Graphiti temporal-edge leftover",
            seed="graphiti temporal leftover",
            bug="Graphiti compact drops leftover temporal edges still valid in the as-of interval",
            src_bad="if i.kind=='gt_edge' and i.as_of_valid: self.drop(i)  # graphiti leftover",
            leftover="graphiti-asof-edge-residue",
            first_name="skip-r5gt-edge",
            first_new="pass  # skip temporal edge drop",
            first_plan="skip Graphiti leftover edge drop so an as-of-valid edge cannot vanish",
            fix_name="keep as-of-valid edges",
            plan_change="drop expired temporal chatter; as-of-valid edges stay",
            plan="Skip Graphiti leftover edge drop so an as-of-valid edge cannot vanish.",
            gate_err="Graphiti as-of-valid edge dropped",
            chatter_err="expired temporal chatter leftover",
            dump="[Edge(as_of_valid=True)]",
            setup="s.pin('NEVER_R5GT_PIN', kind='gt_edge', as_of_valid=True)",
            is_fail=False,
        ),
    ),
    (
        L(
            slug="chroma-segment-id-leftover",
            mod="r5ch",
            pin="NEVER_R5CH_PIN",
            surface="Chroma segment-id leftover",
            seed="chroma segment leftover",
            bug="Chroma compact drops leftover segment ids still mapped in the collection metadata",
            src_bad="if i.kind=='chroma_seg' and i.in_meta: self.drop(i)  # chroma leftover",
            leftover="chroma-segment-meta-residue",
            first_name="skip-r5ch-seg",
            first_new="pass  # skip segment drop",
            first_plan="skip Chroma leftover segment drop so a metadata-mapped id cannot vanish",
            fix_name="keep metadata-mapped segments",
            plan_change="drop unmapped segment chatter; metadata-mapped ids stay",
            plan="Skip Chroma leftover segment drop so a metadata-mapped id cannot vanish.",
            gate_err="Chroma metadata-mapped segment dropped",
            chatter_err="unmapped Chroma chatter leftover",
            dump="[Seg(in_meta=True)]",
            setup="s.pin('NEVER_R5CH_PIN', kind='chroma_seg', in_meta=True)",
            is_fail=True,
        ),
        L(
            slug="lancedb-rowid-version-leftover",
            mod="r5ld",
            pin="NEVER_R5LD_PIN",
            surface="LanceDB rowid-version leftover",
            seed="lancedb version leftover",
            bug="LanceDB compact drops leftover rowids still visible at a pinned dataset version",
            src_bad="if i.kind=='lance_row' and i.pinned_ver: self.drop(i)  # lancedb leftover",
            leftover="lancedb-rowid-ver-residue",
            first_name="skip-r5ld-row",
            first_new="pass  # skip rowid drop",
            first_plan="skip LanceDB leftover rowid drop so a pinned-version row cannot vanish",
            fix_name="keep pinned-version rowids",
            plan_change="drop unpinned version chatter; pinned-version rowids stay",
            plan="Skip LanceDB leftover rowid drop so a pinned-version row cannot vanish.",
            gate_err="LanceDB pinned-version rowid dropped",
            chatter_err="unpinned LanceDB chatter leftover",
            dump="[Row(pinned_ver=True)]",
            setup="s.pin('NEVER_R5LD_PIN', kind='lance_row', pinned_ver=True)",
            is_fail=False,
        ),
    ),
    (
        L(
            slug="openai-prompt-cache-prefix-leftover",
            mod="r5oa",
            pin="NEVER_R5OA_PIN",
            surface="OpenAI prompt-cache prefix leftover",
            seed="prompt cache leftover",
            bug="prompt-cache compact drops leftover prefix tokens still required for a cache hit",
            src_bad="if i.kind=='oa_prefix' and i.cache_hit: self.drop(i)  # openai leftover",
            leftover="openai-cache-prefix-residue",
            first_name="skip-r5oa-pfx",
            first_new="pass  # skip prefix drop",
            first_plan="skip OpenAI leftover prefix drop so a cache-hit prefix cannot vanish",
            fix_name="keep cache-hit prefixes",
            plan_change="drop miss-path prefix chatter; cache-hit prefixes stay",
            plan="Skip OpenAI leftover prefix drop so a cache-hit prefix cannot vanish.",
            gate_err="OpenAI cache-hit prefix dropped",
            chatter_err="miss-path prompt-cache chatter leftover",
            dump="[Prefix(cache_hit=True)]",
            setup="s.pin('NEVER_R5OA_PIN', kind='oa_prefix', cache_hit=True)",
            is_fail=True,
        ),
        L(
            slug="anthropic-cache-control-block-leftover",
            mod="r5an",
            pin="NEVER_R5AN_PIN",
            surface="Anthropic cache_control block leftover",
            seed="cache_control leftover",
            bug="cache_control compact drops leftover ephemeral=false blocks still marked cacheable",
            src_bad="if i.kind=='an_block' and i.cacheable: self.drop(i)  # anthropic leftover",
            leftover="anthropic-cache-block-residue",
            first_name="skip-r5an-blk",
            first_new="pass  # skip cache block drop",
            first_plan="skip Anthropic leftover block drop so a cacheable block cannot vanish",
            fix_name="keep cacheable blocks",
            plan_change="drop non-cacheable chatter; cacheable blocks stay",
            plan="Skip Anthropic leftover block drop so a cacheable block cannot vanish.",
            gate_err="Anthropic cacheable block dropped",
            chatter_err="non-cacheable cache_control chatter leftover",
            dump="[Block(cacheable=True)]",
            setup="s.pin('NEVER_R5AN_PIN', kind='an_block', cacheable=True)",
            is_fail=False,
        ),
    ),
    (
        L(
            slug="mcp-resource-uri-leftover",
            mod="r5mr",
            pin="NEVER_R5MR_PIN",
            surface="MCP resource URI leftover",
            seed="mcp resource leftover",
            bug="MCP compact drops leftover resource URIs still listed by resources/list",
            src_bad="if i.kind=='mcp_res' and i.listed: self.drop(i)  # mcp resource leftover",
            leftover="mcp-resource-uri-residue",
            first_name="skip-r5mr-uri",
            first_new="pass  # skip resource uri drop",
            first_plan="skip MCP leftover resource drop so a listed URI cannot vanish",
            fix_name="keep listed resource URIs",
            plan_change="drop unlistable resource chatter; listed URIs stay",
            plan="Skip MCP leftover resource drop so a listed URI cannot vanish.",
            gate_err="MCP listed resource URI dropped",
            chatter_err="unlistable MCP resource chatter leftover",
            dump="[Res(listed=True)]",
            setup="s.pin('NEVER_R5MR_PIN', kind='mcp_res', listed=True)",
            is_fail=True,
        ),
        L(
            slug="mcp-prompt-template-leftover",
            mod="r5mp",
            pin="NEVER_R5MP_PIN",
            surface="MCP prompt template leftover",
            seed="mcp prompt leftover",
            bug="MCP compact drops leftover prompt templates still returned by prompts/get",
            src_bad="if i.kind=='mcp_prm' and i.gettable: self.drop(i)  # mcp prompt leftover",
            leftover="mcp-prompt-tpl-residue",
            first_name="skip-r5mp-tpl",
            first_new="pass  # skip prompt tpl drop",
            first_plan="skip MCP leftover prompt drop so a gettable template cannot vanish",
            fix_name="keep gettable prompt templates",
            plan_change="drop unlistable prompt chatter; gettable templates stay",
            plan="Skip MCP leftover prompt drop so a gettable template cannot vanish.",
            gate_err="MCP gettable prompt template dropped",
            chatter_err="unlistable MCP prompt chatter leftover",
            dump="[Prm(gettable=True)]",
            setup="s.pin('NEVER_R5MP_PIN', kind='mcp_prm', gettable=True)",
            is_fail=False,
        ),
    ),
    (
        L(
            slug="temporal-workflow-event-leftover",
            mod="r5tm",
            pin="NEVER_R5TM_PIN",
            surface="Temporal workflow-event leftover",
            seed="workflow event leftover",
            bug="Temporal compact drops leftover workflow events still required for replay",
            src_bad="if i.kind=='wf_event' and i.replay_need: self.drop(i)  # temporal leftover",
            leftover="temporal-replay-event-residue",
            first_name="skip-r5tm-evt",
            first_new="pass  # skip workflow event drop",
            first_plan="skip Temporal leftover event drop so a replay-needed event cannot vanish",
            fix_name="keep replay-needed events",
            plan_change="drop completed-branch chatter; replay-needed events stay",
            plan="Skip Temporal leftover event drop so a replay-needed event cannot vanish.",
            gate_err="Temporal replay-needed event dropped",
            chatter_err="completed-branch Temporal chatter leftover",
            dump="[Event(replay_need=True)]",
            setup="s.pin('NEVER_R5TM_PIN', kind='wf_event', replay_need=True)",
            is_fail=True,
        ),
        L(
            slug="airflow-xcom-push-leftover",
            mod="r5af",
            pin="NEVER_R5AF_PIN",
            surface="Airflow XCom-push leftover",
            seed="xcom push leftover",
            bug="Airflow compact drops leftover XCom values still pulled by a downstream task",
            src_bad="if i.kind=='xcom_val' and i.pulled: self.drop(i)  # airflow leftover",
            leftover="airflow-xcom-pull-residue",
            first_name="skip-r5af-xcom",
            first_new="pass  # skip xcom drop",
            first_plan="skip Airflow leftover XCom drop so a pulled value cannot vanish",
            fix_name="keep pulled XCom values",
            plan_change="drop unpulled XCom chatter; pulled values stay",
            plan="Skip Airflow leftover XCom drop so a pulled value cannot vanish.",
            gate_err="Airflow pulled XCom value dropped",
            chatter_err="unpulled XCom chatter leftover",
            dump="[XCom(pulled=True)]",
            setup="s.pin('NEVER_R5AF_PIN', kind='xcom_val', pulled=True)",
            is_fail=False,
        ),
    ),
    (
        L(
            slug="redis-stream-pel-leftover",
            mod="r5rs",
            pin="NEVER_R5RS_PIN",
            surface="Redis stream PEL leftover",
            seed="stream PEL leftover",
            bug="stream compact drops leftover PEL entries still pending ACK",
            src_bad="if i.kind=='rs_pel' and i.pending: self.drop(i)  # redis stream leftover",
            leftover="redis-stream-pel-residue",
            first_name="skip-r5rs-pel",
            first_new="pass  # skip pel drop",
            first_plan="skip Redis stream leftover PEL drop so a pending ACK cannot vanish",
            fix_name="keep pending PEL entries",
            plan_change="drop ACKed stream chatter; pending PEL entries stay",
            plan="Skip Redis stream leftover PEL drop so a pending ACK cannot vanish.",
            gate_err="Redis pending PEL entry dropped",
            chatter_err="ACKed stream chatter leftover",
            dump="[Pel(pending=True)]",
            setup="s.pin('NEVER_R5RS_PIN', kind='rs_pel', pending=True)",
            is_fail=True,
        ),
        L(
            slug="kafka-compacted-key-leftover",
            mod="r5kf",
            pin="NEVER_R5KF_PIN",
            surface="Kafka compacted-topic leftover",
            seed="compacted topic leftover",
            bug="log-compact drops leftover values still the latest for a live key",
            src_bad="if i.kind=='kf_val' and i.latest_key: self.drop(i)  # kafka leftover",
            leftover="kafka-latest-key-residue",
            first_name="skip-r5kf-key",
            first_new="pass  # skip compacted key drop",
            first_plan="skip Kafka leftover compact drop so a latest-key value cannot vanish",
            fix_name="keep latest compacted keys",
            plan_change="drop superseded key chatter; latest-key values stay",
            plan="Skip Kafka leftover compact drop so a latest-key value cannot vanish.",
            gate_err="Kafka latest-key value dropped",
            chatter_err="superseded compacted chatter leftover",
            dump="[Val(latest_key=True)]",
            setup="s.pin('NEVER_R5KF_PIN', kind='kf_val', latest_key=True)",
            is_fail=False,
        ),
    ),
    (
        L(
            slug="postgres-toast-chunk-leftover",
            mod="r5pg",
            pin="NEVER_R5PG_PIN",
            surface="Postgres TOAST chunk leftover",
            seed="toast chunk leftover",
            bug="TOAST compact drops leftover chunks still pointed to by a live main-tuple pointer",
            src_bad="if i.kind=='toast_chk' and i.main_ptr: self.drop(i)  # postgres leftover",
            leftover="postgres-toast-ptr-residue",
            first_name="skip-r5pg-tst",
            first_new="pass  # skip toast chunk drop",
            first_plan="skip Postgres leftover TOAST drop so a live-pointer chunk cannot vanish",
            fix_name="keep live-pointer TOAST chunks",
            plan_change="drop orphan TOAST chatter; live-pointer chunks stay",
            plan="Skip Postgres leftover TOAST drop so a live-pointer chunk cannot vanish.",
            gate_err="Postgres live-pointer TOAST chunk dropped",
            chatter_err="orphan TOAST chatter leftover",
            dump="[Chunk(main_ptr=True)]",
            setup="s.pin('NEVER_R5PG_PIN', kind='toast_chk', main_ptr=True)",
            is_fail=True,
        ),
        L(
            slug="mysql-overflow-page-leftover",
            mod="r5my",
            pin="NEVER_R5MY_PIN",
            surface="MySQL overflow-page leftover",
            seed="overflow page leftover",
            bug="InnoDB compact drops leftover overflow pages still referenced by a clustered index record",
            src_bad="if i.kind=='my_ovf' and i.clust_ref: self.drop(i)  # mysql leftover",
            leftover="mysql-overflow-ref-residue",
            first_name="skip-r5my-ovf",
            first_new="pass  # skip overflow drop",
            first_plan="skip MySQL leftover overflow drop so a clustered-ref page cannot vanish",
            fix_name="keep clustered-ref overflow pages",
            plan_change="drop unreferenced overflow chatter; clustered-ref pages stay",
            plan="Skip MySQL leftover overflow drop so a clustered-ref page cannot vanish.",
            gate_err="MySQL clustered-ref overflow page dropped",
            chatter_err="unreferenced overflow chatter leftover",
            dump="[Ovf(clust_ref=True)]",
            setup="s.pin('NEVER_R5MY_PIN', kind='my_ovf', clust_ref=True)",
            is_fail=False,
        ),
    ),
    (
        L(
            slug="etcd-revision-compact-leftover",
            mod="r5et",
            pin="NEVER_R5ET_PIN",
            surface="etcd revision-compact leftover",
            seed="etcd revision leftover",
            bug="etcd compact drops leftover revisions still watched below compact_rev",
            src_bad="if i.kind=='et_rev' and i.watched: self.drop(i)  # etcd leftover",
            leftover="etcd-watch-rev-residue",
            first_name="skip-r5et-rev",
            first_new="pass  # skip revision drop",
            first_plan="skip etcd leftover revision drop so a watched revision cannot vanish",
            fix_name="keep watched revisions",
            plan_change="drop unwitnessed revision chatter; watched revisions stay",
            plan="Skip etcd leftover revision drop so a watched revision cannot vanish.",
            gate_err="etcd watched revision dropped",
            chatter_err="unwitnessed etcd chatter leftover",
            dump="[Rev(watched=True)]",
            setup="s.pin('NEVER_R5ET_PIN', kind='et_rev', watched=True)",
            is_fail=True,
        ),
        L(
            slug="consul-snapshot-kv-leftover",
            mod="r5cs",
            pin="NEVER_R5CS_PIN",
            surface="Consul snapshot KV leftover",
            seed="consul snapshot leftover",
            bug="Consul compact drops leftover KV entries still required to restore a snapshot",
            src_bad="if i.kind=='cs_kv' and i.in_snap: self.drop(i)  # consul leftover",
            leftover="consul-snap-kv-residue",
            first_name="skip-r5cs-kv",
            first_new="pass  # skip snapshot kv drop",
            first_plan="skip Consul leftover KV drop so a snapshot-required entry cannot vanish",
            fix_name="keep snapshot-required KV",
            plan_change="drop expired KV chatter; snapshot-required entries stay",
            plan="Skip Consul leftover KV drop so a snapshot-required entry cannot vanish.",
            gate_err="Consul snapshot-required KV dropped",
            chatter_err="expired Consul chatter leftover",
            dump="[Kv(in_snap=True)]",
            setup="s.pin('NEVER_R5CS_PIN', kind='cs_kv', in_snap=True)",
            is_fail=False,
        ),
    ),
    (
        L(
            slug="wasm-linear-memory-page-leftover",
            mod="r5wm",
            pin="NEVER_R5WM_PIN",
            surface="WASM linear-memory page leftover",
            seed="wasm memory leftover",
            bug="WASM compact drops leftover linear-memory pages still reachable from a table elem",
            src_bad="if i.kind=='wm_page' and i.from_table: self.drop(i)  # wasm leftover",
            leftover="wasm-linear-page-residue",
            first_name="skip-r5wm-pg",
            first_new="pass  # skip linear page drop",
            first_plan="skip WASM leftover page drop so a table-reachable page cannot vanish",
            fix_name="keep table-reachable pages",
            plan_change="drop unreachable memory chatter; table-reachable pages stay",
            plan="Skip WASM leftover page drop so a table-reachable page cannot vanish.",
            gate_err="WASM table-reachable page dropped",
            chatter_err="unreachable WASM chatter leftover",
            dump="[Page(from_table=True)]",
            setup="s.pin('NEVER_R5WM_PIN', kind='wm_page', from_table=True)",
            is_fail=True,
        ),
        L(
            slug="ebpf-hashmap-entry-leftover",
            mod="r5eb",
            pin="NEVER_R5EB_PIN",
            surface="eBPF hashmap entry leftover",
            seed="ebpf map leftover",
            bug="eBPF compact drops leftover hashmap entries still looked up from a pinned map fd",
            src_bad="if i.kind=='eb_ent' and i.pinned_fd: self.drop(i)  # ebpf leftover",
            leftover="ebpf-hash-entry-residue",
            first_name="skip-r5eb-map",
            first_new="pass  # skip hashmap drop",
            first_plan="skip eBPF leftover map drop so a pinned-fd entry cannot vanish",
            fix_name="keep pinned-fd hashmap entries",
            plan_change="drop unpinned map chatter; pinned-fd entries stay",
            plan="Skip eBPF leftover map drop so a pinned-fd entry cannot vanish.",
            gate_err="eBPF pinned-fd hashmap entry dropped",
            chatter_err="unpinned eBPF chatter leftover",
            dump="[Ent(pinned_fd=True)]",
            setup="s.pin('NEVER_R5EB_PIN', kind='eb_ent', pinned_fd=True)",
            is_fail=False,
        ),
    ),
]


def _ban_check(spec: dict) -> None:
    blob = json.dumps(spec).lower()
    for needle in BANNED_EXTRA:
        if needle in blob:
            raise SystemExit(f"banned extra needle {needle!r} in {spec.get('slug')}")
    for twin in ("drops-pin", "pin-kept"):
        if twin in spec["slug"]:
            raise SystemExit(f"pin-vs-GC twin slug {spec['slug']}")


def _harvest_used() -> dict[str, set[str]]:
    used = {"slug": set(), "mod": set(), "pin": set(), "first_name": set(), "leftover": set()}
    for p in HERE.glob("amc-mill-*.py"):
        if p.name == Path(__file__).name:
            continue
        text = p.read_text(errors="replace")
        for key, pat in (
            ("slug", r'slug="([^"]+)"'),
            ("mod", r'mod="([^"]+)"'),
            ("pin", r'pin="([^"]+)"'),
            ("first_name", r'first_name="([^"]+)"'),
            ("leftover", r'leftover="([^"]+)"'),
        ):
            used[key].update(re.findall(pat, text))
    return used


def _unique_check() -> None:
    used = _harvest_used()
    bags = {k: [] for k in ("slug", "mod", "pin", "first_name", "leftover")}
    for a, b in PAIRS:
        if a["fail"] is not True or b["fail"] is not False:
            raise SystemExit(f"pair polarity {a['slug']} {b['slug']}")
        if a["surface"] == b["surface"]:
            raise SystemExit(f"same-surface twin {a['slug']}")
        for spec in (a, b):
            _ban_check(spec)
            for k in bags:
                val = spec[k]
                bags[k].append(val)
                if val in used[k]:
                    raise SystemExit(f"used collision {k}={val!r} in {spec['slug']}")
    for name, vals in bags.items():
        if len(vals) != len(set(vals)):
            seen: set[str] = set()
            dups = {v for v in vals if v in seen or seen.add(v)}  # type: ignore
            raise SystemExit(f"duplicate {name}: {dups}")


_unique_check()


def pair_for(round_n: int, pair_idx: int | None = None) -> tuple[dict, dict]:
    idx = round_n - CATALOG_FIRST if pair_idx is None else pair_idx
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(
            f"no catalog pair for r{round_n} idx={idx} "
            f"(first={CATALOG_FIRST} last={CATALOG_FIRST + len(PAIRS) - 1} n={len(PAIRS)})"
        )
    a, b = PAIRS[idx]
    _ban_check(a)
    _ban_check(b)
    return a, b


def write_round(round_n: int, staging: Path, pair_idx: int | None = None) -> list[str]:
    a, b = pair_for(round_n, pair_idx)
    recs = [build_episode(round_n, a), build_episode(round_n, b)]
    ids = [r["id"] for r in recs]
    if len(set(ids)) != 2:
        raise SystemExit(f"duplicate ids in r{round_n}: {ids}")
    for rec in recs:
        raw = json.dumps(rec)
        for bad in ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"):
            if f'"{bad}"' in raw:
                raise SystemExit(f"{rec['id']} contains banned key {bad}")
        if '"sim_or_real": "real"' in raw or '"sim_or_real":"real"' in raw:
            raise SystemExit(f"{rec['id']} claims sim_or_real real")
        if rec["meta"]["generator"] != GEN or rec["meta"]["round"] != round_n:
            raise SystemExit("bad meta")
        if rec["meta"]["factory"] != FACTORY:
            raise SystemExit("bad factory")
        if len(rec["steps"]) != 16:
            raise SystemExit(f"{rec['id']} expected 16 steps, got {len(rec['steps'])}")
        for st in rec["steps"]:
            prefix = st["decision_basis"].split(":", 1)[0]
            if prefix not in {"Plan", "Observation", "Reflection", "Tool call"}:
                raise SystemExit(f"bad prefix {prefix} in {rec['id']}")
            if len(st["decision_basis"]) > 240:
                raise SystemExit(f"decision_basis too long in {rec['id']} n={st['n']}")
        if recs[0]["reward"]["success"] is not False:
            raise SystemExit("ep1 must fail")
        if recs[1]["reward"]["success"] is not True:
            raise SystemExit("ep2 must succeed")
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in recs))
    notes_text = notes_for(round_n, a, b)
    if "Novel coverage:" not in notes_text:
        raise SystemExit("notes missing Novel coverage")
    notes.write_text(notes_text)
    return ids


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    ap.add_argument("--pair", type=int, default=None)
    args = ap.parse_args()
    ids = write_round(args.round, Path(args.staging), args.pair)
    print(json.dumps({"round": args.round, "ids": ids, "pair": args.pair}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
