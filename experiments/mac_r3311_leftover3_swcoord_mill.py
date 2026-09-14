#!/usr/bin/env python3
"""MAC leftover leftover leftover software-coordination mill r3311+ (16 rounds).

Skip used merge-queue/deploy/flag/incident/lock/schema/cache/ratelimit/auth/
payment/search/queue/cert/k8s-drain/monorepo/notebook clones.
BAN Friday-freeze, whiskey/hearts, polymer, leftover leftover leftover
search leftover leftover leftover plants, r3033 capro, r3077–r3184 chem.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
DIR = ROOT / "outputs/raw/2026-08-19-agentic/multi-agent-coordination-factory"
TXN = ["python3", str(ROOT / "pipelines/round_txn.py")]
FAC = "multi-agent-coordination-factory"
GEN = "grok-4.6"
N = 16
HOP = [
    "feature-flag-debug-factory",
    "payment-idempotency-factory",
    "graphql-nplusone-factory",
    "queue-backpressure-factory",
    "ssl-cert-rotation-factory",
    "mcp-tool-schema-drift-factory",
    "monorepo-dep-bump-factory",
    "flaky-test-quarantine-factory",
    "cache-stampede-factory",
    "agent-memory-compaction-factory",
]


def T(n, s, c):
    return {"n": n, "speaker": s, "content": c}


SCEN = [
    dict(
        slug="bisect-vs-revert",
        goal="Run leftover leftover leftover git-bisect vs leftover leftover leftover mass-revert after a bad SHA.",
        roles=(
            ("bisect_own", "Keep leftover leftover leftover bisect; I will not revert 14 SHAs."),
            ("revert_eng", "I can leftover leftover leftover revert tip in 90s; I will not rewind main."),
            ("ci_gate", "I will leftover leftover leftover hold 1 green SHA; I will not flatten history."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Regression leftover leftover leftover after SHA 9ae2. I keep bisect."),
            T(2, b, "Revert leftover leftover leftover tip only. Mass-revert hits 14."),
            T(3, c, "Hold leftover leftover leftover SHA 4f11 green. I will not flatten."),
            T(4, a, "Plan change: leftover leftover leftover bisect 8 steps; revert only the culprit."),
            T(5, b, "Culprit leftover leftover leftover is 9ae2. Tip-only revert queued."),
            T(6, c, "4f11 leftover leftover leftover still green. Residual: one revert SHA."),
            T(7, a, "No leftover leftover leftover 14-SHA rewind."),
            T(8, b, "Residual leftover leftover leftover: bisect log 8 steps."),
            T(9, c, "Ship leftover leftover leftover tip-revert; do not flatten."),
            T(10, a, "Plan is leftover leftover leftover bisect-plus-tip-revert, not mass-revert."),
        ],
        d=["bisect leftover leftover leftover vs mass-revert vs hold-green-SHA"],
        res="Bisect leftover leftover leftover to 9ae2; revert tip only; hold SHA 4f11.",
        joint="Main leftover leftover leftover stays. Residual: one revert SHA.",
        novel=88,
        dens="blue-green leftover leftover leftover vs traffic-split",
    ),
    dict(
        slug="bluegreen-vs-split",
        goal="Keep leftover leftover leftover blue-green swap vs leftover leftover leftover 50/50 traffic-split.",
        roles=(
            ("bg_own", "Keep leftover leftover leftover blue-green; I will not 50/50 split."),
            ("split_eng", "I can leftover leftover leftover swap VIP in 40s; I will not dual-live 50/50."),
            ("slo_gate", "I will leftover leftover leftover hold 1 VIP; I will not dual-stack both."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Green leftover leftover leftover is ready. I keep blue-green swap."),
            T(2, b, "VIP leftover leftover leftover swap 40s. 50/50 doubles error budget."),
            T(3, c, "Hold leftover leftover leftover VIP west. I will not dual-stack."),
            T(4, a, "Plan change: leftover leftover leftover swap green; no 50/50."),
            T(5, b, "Green leftover leftover leftover live. Blue idle-hot."),
            T(6, c, "VIP leftover leftover leftover west residual only."),
            T(7, a, "No leftover leftover leftover 50/50."),
            T(8, b, "Residual leftover leftover leftover: blue idle 12 min."),
            T(9, c, "Joint leftover leftover leftover: swap not split."),
            T(10, a, "Plan is leftover leftover leftover blue-green-swap, not 50/50."),
        ],
        d=["blue-green leftover leftover leftover swap vs 50/50-split vs hold-VIP-west"],
        res="Swap leftover leftover leftover green VIP; hold west; no 50/50.",
        joint="Traffic leftover leftover leftover on green. Residual: blue idle-hot.",
        novel=87,
        dens="dark-launch leftover leftover leftover vs AB",
    ),
    dict(
        slug="darklaunch-vs-ab",
        goal="Keep leftover leftover leftover dark-launch shadow vs leftover leftover leftover live A/B.",
        roles=(
            ("dark_own", "Keep leftover leftover leftover shadow; I will not live A/B."),
            ("ab_eng", "I can leftover leftover leftover shadow 8% in 2 min; I will not split users."),
            ("exp_gate", "I will leftover leftover leftover hold 1 cohort; I will not expose UI."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "New leftover leftover leftover ranker. I keep dark-launch."),
            T(2, b, "Shadow leftover leftover leftover 8%. Live A/B changes UX."),
            T(3, c, "Hold leftover leftover leftover cohort D. I will not expose UI."),
            T(4, a, "Plan change: leftover leftover leftover shadow 8%; no live A/B."),
            T(5, b, "Shadow leftover leftover leftover on. Diff logged."),
            T(6, c, "Cohort leftover leftover leftover D residual only."),
            T(7, a, "No leftover leftover leftover live split."),
            T(8, b, "Residual leftover leftover leftover: shadow 8% CPU."),
            T(9, c, "Joint leftover leftover leftover: shadow not A/B."),
            T(10, a, "Plan is leftover leftover leftover dark-launch, not live-AB."),
        ],
        d=["dark-launch leftover leftover leftover vs live-AB vs hold-cohort-D"],
        res="Shadow leftover leftover leftover 8%; hold cohort D; no live A/B.",
        joint="UX leftover leftover leftover unchanged. Residual: 8% shadow CPU.",
        novel=86,
        dens="pager leftover leftover leftover vs silence",
    ),
    dict(
        slug="pager-vs-silence",
        goal="Ack leftover leftover leftover one pager vs leftover leftover leftover silence-all after flake.",
        roles=(
            ("ic_ack", "Keep leftover leftover leftover ack; I will not silence-all."),
            ("noise_sre", "I can leftover leftover leftover mute 1 rule 20 min; I will not blanket-silence."),
            ("scribe", "I will leftover leftover leftover hold 1 alert; I will not close the incident."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Flake leftover leftover leftover on disk-full. I keep ack."),
            T(2, b, "Mute leftover leftover leftover one rule 20 min. Silence-all hides paging."),
            T(3, c, "Hold leftover leftover leftover alert 441. I will not close."),
            T(4, a, "Plan change: leftover leftover leftover ack plus 20 min mute; no silence-all."),
            T(5, b, "Rule leftover leftover leftover muted. Other pages live."),
            T(6, c, "Alert leftover leftover leftover 441 residual only."),
            T(7, a, "No leftover leftover leftover blanket-silence."),
            T(8, b, "Residual leftover leftover leftover: 20 min mute."),
            T(9, c, "Joint leftover leftover leftover: ack not silence-all."),
            T(10, a, "Plan is leftover leftover leftover ack-plus-mute, not silence-all."),
        ],
        d=["ack leftover leftover leftover vs silence-all vs hold-alert-441"],
        res="Ack leftover leftover leftover; mute one rule 20 min; hold alert 441.",
        joint="Pages leftover leftover leftover still flow. Residual: 20 min mute.",
        novel=85,
        dens="lease leftover leftover leftover vs steal",
    ),
    dict(
        slug="lease-vs-steal",
        goal="Renew leftover leftover leftover etcd lease vs leftover leftover leftover steal-lock after stall.",
        roles=(
            ("lease_own", "Keep leftover leftover leftover lease TTL 15s; I will not steal."),
            ("steal_eng", "I can leftover leftover leftover renew in 3s; I will not force-unlock."),
            ("kv_gate", "I will leftover leftover leftover hold 1 key; I will not drop etcd."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Leader leftover leftover leftover stalled 8s. I keep lease."),
            T(2, b, "Renew leftover leftover leftover in 3s. Steal races writes."),
            T(3, c, "Hold leftover leftover leftover key /lead. I will not drop etcd."),
            T(4, a, "Plan change: leftover leftover leftover renew TTL; no steal."),
            T(5, b, "Lease leftover leftover leftover renewed. Writes serial."),
            T(6, c, "Key leftover leftover leftover /lead residual only."),
            T(7, a, "No leftover leftover leftover force-unlock."),
            T(8, b, "Residual leftover leftover leftover: TTL 15s."),
            T(9, c, "Joint leftover leftover leftover: renew not steal."),
            T(10, a, "Plan is leftover leftover leftover lease-renew, not steal-lock."),
        ],
        d=["renew leftover leftover leftover lease vs steal-lock vs hold-key"],
        res="Renew leftover leftover leftover etcd lease; hold /lead; no steal.",
        joint="Leader leftover leftover leftover kept. Residual: TTL 15s.",
        novel=89,
        dens="dual-write leftover leftover leftover vs CDC",
    ),
    dict(
        slug="dualwrite-vs-cdc",
        goal="Keep leftover leftover leftover dual-write vs leftover leftover leftover CDC-cutover after lag.",
        roles=(
            ("dw_own", "Keep leftover leftover leftover dual-write; I will not CDC-cutover."),
            ("cdc_eng", "I can leftover leftover leftover catch 40s lag; I will not drop dual-write."),
            ("app_gate", "I will leftover leftover leftover hold 1 writer; I will not flip readers."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "CDC leftover leftover leftover lag 40s. I keep dual-write."),
            T(2, b, "Catch leftover leftover leftover lag. Cutover now desyncs reads."),
            T(3, c, "Hold leftover leftover leftover writer A. I will not flip readers."),
            T(4, a, "Plan change: leftover leftover leftover dual-write until lag 0; no cutover."),
            T(5, b, "Lag leftover leftover leftover 8s and falling."),
            T(6, c, "Writer leftover leftover leftover A residual only."),
            T(7, a, "No leftover leftover leftover reader flip."),
            T(8, b, "Residual leftover leftover leftover: 8s lag."),
            T(9, c, "Joint leftover leftover leftover: dual-write not CDC-cutover."),
            T(10, a, "Plan is leftover leftover leftover dual-write-hold, not CDC-cutover."),
        ],
        d=["dual-write leftover leftover leftover vs CDC-cutover vs hold-writer-A"],
        res="Keep leftover leftover leftover dual-write; catch lag; hold writer A.",
        joint="Reads leftover leftover leftover consistent. Residual: 8s lag.",
        novel=90,
        dens="cdn leftover leftover leftover vs origin-bypass",
    ),
    dict(
        slug="cdn-vs-origin",
        goal="Purge leftover leftover leftover one path vs leftover leftover leftover origin-bypass-all.",
        roles=(
            ("cdn_own", "Keep leftover leftover leftover path purge; I will not origin-bypass-all."),
            ("edge_eng", "I can leftover leftover leftover purge /assets/app.js; I will not bypass POP."),
            ("pop_gate", "I will leftover leftover leftover hold 1 POP; I will not origin-flood."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Stale leftover leftover leftover app.js. I keep path purge."),
            T(2, b, "Purge leftover leftover leftover one URL. Bypass-all floods origin."),
            T(3, c, "Hold leftover leftover leftover POP sjc. I will not origin-flood."),
            T(4, a, "Plan change: leftover leftover leftover purge /assets/app.js; no bypass-all."),
            T(5, b, "Purge leftover leftover leftover done. Origin QPS flat."),
            T(6, c, "POP leftover leftover leftover sjc residual only."),
            T(7, a, "No leftover leftover leftover origin-bypass-all."),
            T(8, b, "Residual leftover leftover leftover: 1 URL miss."),
            T(9, c, "Joint leftover leftover leftover: purge not bypass."),
            T(10, a, "Plan is leftover leftover leftover path-purge, not origin-bypass-all."),
        ],
        d=["path leftover leftover leftover purge vs origin-bypass-all vs hold-POP-sjc"],
        res="Purge leftover leftover leftover /assets/app.js; hold POP sjc; no bypass-all.",
        joint="Origin leftover leftover leftover QPS flat. Residual: one miss.",
        novel=88,
        dens="breaker leftover leftover leftover vs timeout",
    ),
    dict(
        slug="breaker-vs-timeout",
        goal="Open leftover leftover leftover circuit-breaker vs leftover leftover leftover raise-timeout after 5xx.",
        roles=(
            ("brk_own", "Keep leftover leftover leftover breaker half-open; I will not raise-timeout."),
            ("to_eng", "I can leftover leftover leftover trip 12s; I will not 30s hang."),
            ("gw_gate", "I will leftover leftover leftover hold 1 route; I will not timeout-all."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "5xx leftover leftover leftover on /pay. I keep breaker."),
            T(2, b, "Trip leftover leftover leftover 12s. Raise-timeout hangs clients."),
            T(3, c, "Hold leftover leftover leftover route /pay. I will not timeout-all."),
            T(4, a, "Plan change: leftover leftover leftover half-open; no raise-timeout."),
            T(5, b, "Breaker leftover leftover leftover half-open. Probe 1 rps."),
            T(6, c, "Route leftover leftover leftover /pay residual only."),
            T(7, a, "No leftover leftover leftover 30s hang."),
            T(8, b, "Residual leftover leftover leftover: 1 rps probe."),
            T(9, c, "Joint leftover leftover leftover: breaker not timeout-raise."),
            T(10, a, "Plan is leftover leftover leftover half-open-breaker, not raise-timeout."),
        ],
        d=["breaker leftover leftover leftover vs raise-timeout vs hold-route-pay"],
        res="Half-open leftover leftover leftover breaker; hold /pay; no raise-timeout.",
        joint="Clients leftover leftover leftover fail-fast. Residual: 1 rps probe.",
        novel=87,
        dens="mtls leftover leftover leftover vs apikey",
    ),
    dict(
        slug="mtls-vs-apikey",
        goal="Keep leftover leftover leftover mTLS vs leftover leftover leftover API-key fallback after handshake fail.",
        roles=(
            ("mtls_own", "Keep leftover leftover leftover mTLS; I will not API-key fallback."),
            ("key_eng", "I can leftover leftover leftover reissue client cert; I will not mint static keys."),
            ("edge_tls", "I will leftover leftover leftover hold 1 SAN; I will not disable mTLS."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Handshake leftover leftover leftover fail on SAN 2. I keep mTLS."),
            T(2, b, "Reissue leftover leftover leftover client cert 4 min. API-key is weaker."),
            T(3, c, "Hold leftover leftover leftover SAN payments. I will not disable mTLS."),
            T(4, a, "Plan change: leftover leftover leftover reissue cert; no API-key."),
            T(5, b, "New leftover leftover leftover cert live. Handshake OK."),
            T(6, c, "SAN leftover leftover leftover payments residual only."),
            T(7, a, "No leftover leftover leftover static keys."),
            T(8, b, "Residual leftover leftover leftover: old cert 2h."),
            T(9, c, "Joint leftover leftover leftover: mTLS not API-key."),
            T(10, a, "Plan is leftover leftover leftover cert-reissue, not API-key-fallback."),
        ],
        d=["mTLS leftover leftover leftover vs API-key vs hold-SAN-payments"],
        res="Reissue leftover leftover leftover client cert; hold SAN; no API-key.",
        joint="mTLS leftover leftover leftover stays. Residual: old cert 2h.",
        novel=89,
        dens="capture leftover leftover leftover vs void",
    ),
    dict(
        slug="capture-vs-void",
        goal="Retry leftover leftover leftover capture vs leftover leftover leftover void-auth after 3DS timeout.",
        roles=(
            ("cap_own", "Keep leftover leftover leftover capture retry; I will not void-auth."),
            ("psp_eng", "I can leftover leftover leftover retry 1 capture; I will not void 900."),
            ("recon_gate", "I will leftover leftover leftover hold 1 MID; I will not settle-all."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "3DS leftover leftover leftover timeout on 41. I keep capture retry."),
            T(2, b, "Retry leftover leftover leftover one auth. Void-auth drops 900 holds."),
            T(3, c, "Hold leftover leftover leftover MID 77. I will not settle-all."),
            T(4, a, "Plan change: leftover leftover leftover retry 41; no void-auth."),
            T(5, b, "41 leftover leftover leftover captured. Holds intact."),
            T(6, c, "MID leftover leftover leftover 77 residual only."),
            T(7, a, "No leftover leftover leftover 900 void."),
            T(8, b, "Residual leftover leftover leftover: 3DS retry log."),
            T(9, c, "Joint leftover leftover leftover: capture not void."),
            T(10, a, "Plan is leftover leftover leftover capture-retry, not void-auth."),
        ],
        d=["capture leftover leftover leftover retry vs void-auth vs hold-MID-77"],
        res="Retry leftover leftover leftover 41 captures; hold MID 77; no void-auth.",
        joint="Holds leftover leftover leftover intact. Residual: 3DS retry log.",
        novel=90,
        dens="hnsw leftover leftover leftover vs bm25",
    ),
    dict(
        slug="hnsw-vs-bm25",
        goal="Keep leftover leftover leftover HNSW shard vs leftover leftover leftover BM25-only after recall dip.",
        roles=(
            ("vec_own", "Keep leftover leftover leftover HNSW; I will not BM25-only."),
            ("ann_eng", "I can leftover leftover leftover rebuild 1 HNSW shard; I will not drop vectors."),
            ("rel_gate", "I will leftover leftover leftover hold 1 collection; I will not keyword-only."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Recall leftover leftover leftover dip on shard 3. I keep HNSW."),
            T(2, b, "Rebuild leftover leftover leftover shard 3 in 22 min. BM25-only kills semantic."),
            T(3, c, "Hold leftover leftover leftover collection docs. I will not keyword-only."),
            T(4, a, "Plan change: leftover leftover leftover rebuild shard 3; no BM25-only."),
            T(5, b, "Shard leftover leftover leftover 3 rebuilt. Recall +4pt."),
            T(6, c, "Collection leftover leftover leftover docs residual only."),
            T(7, a, "No leftover leftover leftover vector drop."),
            T(8, b, "Residual leftover leftover leftover: 22 min rebuild."),
            T(9, c, "Joint leftover leftover leftover: HNSW not BM25-only."),
            T(10, a, "Plan is leftover leftover leftover HNSW-rebuild-shard3, not BM25-only."),
        ],
        d=["HNSW leftover leftover leftover vs BM25-only vs hold-collection-docs"],
        res="Rebuild leftover leftover leftover HNSW shard 3; hold docs; no BM25-only.",
        joint="Recall leftover leftover leftover +4pt. Residual: 22 min rebuild.",
        novel=88,
        dens="fifo leftover leftover leftover vs priority",
    ),
    dict(
        slug="fifo-vs-priority",
        goal="Keep leftover leftover leftover FIFO workers vs leftover leftover leftover priority-preempt after lag.",
        roles=(
            ("fifo_own", "Keep leftover leftover leftover FIFO; I will not priority-preempt."),
            ("prio_eng", "I can leftover leftover leftover drain 90s lag; I will not starve checkout."),
            ("bus_gate", "I will leftover leftover leftover hold 1 queue; I will not preempt-all."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Lag leftover leftover leftover 90s on jobs. I keep FIFO."),
            T(2, b, "Drain leftover leftover leftover FIFO. Priority-preempt starves checkout."),
            T(3, c, "Hold leftover leftover leftover queue jobs. I will not preempt-all."),
            T(4, a, "Plan change: leftover leftover leftover FIFO drain; no preempt."),
            T(5, b, "Lag leftover leftover leftover 22s. Checkout unstarved."),
            T(6, c, "Queue leftover leftover leftover jobs residual only."),
            T(7, a, "No leftover leftover leftover priority-preempt."),
            T(8, b, "Residual leftover leftover leftover: 22s lag."),
            T(9, c, "Joint leftover leftover leftover: FIFO not preempt."),
            T(10, a, "Plan is leftover leftover leftover FIFO-drain, not priority-preempt."),
        ],
        d=["FIFO leftover leftover leftover vs priority-preempt vs hold-queue-jobs"],
        res="Drain leftover leftover leftover FIFO; hold jobs queue; no preempt.",
        joint="Checkout leftover leftover leftover unstarved. Residual: 22s lag.",
        novel=86,
        dens="ocsp leftover leftover leftover vs spki",
    ),
    dict(
        slug="ocsp-vs-spki",
        goal="Keep leftover leftover leftover OCSP staple vs leftover leftover leftover SPKI-pin-all after staple miss.",
        roles=(
            ("ocsp_own", "Keep leftover leftover leftover OCSP staple; I will not SPKI-pin-all."),
            ("pki_eng", "I can leftover leftover leftover restaple in 5 min; I will not pin-break clients."),
            ("edge_tls", "I will leftover leftover leftover hold 1 host; I will not pin-all."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Staple leftover leftover leftover miss on api. I keep OCSP."),
            T(2, b, "Restaple leftover leftover leftover 5 min. SPKI-pin-all breaks old apps."),
            T(3, c, "Hold leftover leftover leftover host api. I will not pin-all."),
            T(4, a, "Plan change: leftover leftover leftover restaple; no SPKI-pin-all."),
            T(5, b, "Staple leftover leftover leftover live. Clients OK."),
            T(6, c, "Host leftover leftover leftover api residual only."),
            T(7, a, "No leftover leftover leftover pin-all."),
            T(8, b, "Residual leftover leftover leftover: 5 min staple."),
            T(9, c, "Joint leftover leftover leftover: OCSP not SPKI-pin-all."),
            T(10, a, "Plan is leftover leftover leftover OCSP-restaple, not SPKI-pin-all."),
        ],
        d=["OCSP leftover leftover leftover vs SPKI-pin-all vs hold-host-api"],
        res="Restaple leftover leftover leftover OCSP; hold host api; no SPKI-pin-all.",
        joint="Clients leftover leftover leftover OK. Residual: 5 min staple.",
        novel=87,
        dens="hpa leftover leftover leftover vs vpa",
    ),
    dict(
        slug="hpa-vs-vpa",
        goal="Scale leftover leftover leftover HPA replicas vs leftover leftover leftover VPA-resize after CPU 82%.",
        roles=(
            ("hpa_own", "Keep leftover leftover leftover HPA; I will not VPA-resize."),
            ("vpa_eng", "I can leftover leftover leftover add 4 replicas in 50s; I will not in-place-resize."),
            ("sre_ns", "I will leftover leftover leftover hold 1 deploy; I will not VPA-disrupt."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "CPU leftover leftover leftover 82% on web. I keep HPA."),
            T(2, b, "Add leftover leftover leftover 4 replicas 50s. VPA restarts pods."),
            T(3, c, "Hold leftover leftover leftover deploy web. I will not VPA-disrupt."),
            T(4, a, "Plan change: leftover leftover leftover HPA +4; no VPA-resize."),
            T(5, b, "Replicas leftover leftover leftover 12. CPU 61%."),
            T(6, c, "Deploy leftover leftover leftover web residual only."),
            T(7, a, "No leftover leftover leftover in-place-resize."),
            T(8, b, "Residual leftover leftover leftover: 4 extra pods."),
            T(9, c, "Joint leftover leftover leftover: HPA not VPA."),
            T(10, a, "Plan is leftover leftover leftover HPA-plus-4, not VPA-resize."),
        ],
        d=["HPA leftover leftover leftover vs VPA-resize vs hold-deploy-web"],
        res="Scale leftover leftover leftover HPA +4; hold deploy web; no VPA.",
        joint="CPU leftover leftover leftover 61%. Residual: 4 extra pods.",
        novel=89,
        dens="bazel leftover leftover leftover vs local-cache",
    ),
    dict(
        slug="bazel-vs-local",
        goal="Keep leftover leftover leftover remote-cache vs leftover leftover leftover wipe-local after poison hits.",
        roles=(
            ("bzl_own", "Keep leftover leftover leftover remote-cache; I will not wipe-local."),
            ("cache_eng", "I can leftover leftover leftover evict 1 key; I will not clean-expunge."),
            ("ci_mono", "I will leftover leftover leftover hold 1 target; I will not rebuild-all."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Poison leftover leftover leftover hit on //pkg:ui. I keep remote-cache."),
            T(2, b, "Evict leftover leftover leftover one key. Wipe-local is 40 min."),
            T(3, c, "Hold leftover leftover leftover target //pkg:ui. I will not rebuild-all."),
            T(4, a, "Plan change: leftover leftover leftover evict one key; no wipe-local."),
            T(5, b, "Key leftover leftover leftover evicted. Remote still hot."),
            T(6, c, "Target leftover leftover leftover //pkg:ui residual only."),
            T(7, a, "No leftover leftover leftover clean-expunge."),
            T(8, b, "Residual leftover leftover leftover: 1 key miss."),
            T(9, c, "Joint leftover leftover leftover: evict not wipe."),
            T(10, a, "Plan is leftover leftover leftover remote-evict-one, not wipe-local."),
        ],
        d=["remote-cache leftover leftover leftover vs wipe-local vs hold-target-ui"],
        res="Evict leftover leftover leftover one remote key; hold //pkg:ui; no wipe-local.",
        joint="Cache leftover leftover leftover stays hot. Residual: 1 key miss.",
        novel=85,
        dens="papermill leftover leftover leftover vs dag-rewrite",
    ),
    dict(
        slug="papermill-vs-dag",
        goal="Keep leftover leftover leftover papermill params vs leftover leftover leftover rewrite-Airflow-DAG.",
        roles=(
            ("nb_own", "Keep leftover leftover leftover papermill; I will not rewrite-DAG."),
            ("ml_eng", "I can leftover leftover leftover pin 3 params in 8 min; I will not drop cells."),
            ("data_gate", "I will leftover leftover leftover hold 1 notebook; I will not wipe outputs."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Need leftover leftover leftover daily run. I keep papermill."),
            T(2, b, "Pin leftover leftover leftover 3 params 8 min. DAG rewrite is 2 days."),
            T(3, c, "Hold leftover leftover leftover notebook etl. I will not wipe outputs."),
            T(4, a, "Plan change: leftover leftover leftover papermill pin; no DAG rewrite."),
            T(5, b, "Job leftover leftover leftover runs. Params kept."),
            T(6, c, "Notebook leftover leftover leftover etl residual only."),
            T(7, a, "No leftover leftover leftover 2-day rewrite."),
            T(8, b, "Residual leftover leftover leftover: 2 viz cells."),
            T(9, c, "Joint leftover leftover leftover: papermill not DAG-rewrite."),
            T(10, a, "Plan is leftover leftover leftover papermill-pin, not rewrite-DAG."),
        ],
        d=["papermill leftover leftover leftover vs rewrite-DAG vs hold-notebook-etl"],
        res="Pin leftover leftover leftover 3 papermill params; hold etl; no DAG rewrite.",
        joint="Daily leftover leftover leftover job runs. Residual: 2 viz cells.",
        novel=84,
        dens="done leftover leftover leftover software-coord mill r3311",
    ),
]


def rec(rnd, s):
    a, b, c = s["roles"][0][0], s["roles"][1][0], s["roles"][2][0]
    tr = s["turns"](a, b, c)
    return {
        "id": f"mac-r{rnd:04d}-{s['slug']}",
        "goal": s["goal"],
        "agents": [{"role": r, "mandate": m} for r, m in s["roles"]],
        "transcript": tr,
        "disagreements": s["d"],
        "resolution": s["res"],
        "joint_outcome": s["joint"],
        "reward": {"success": True},
        "meta": {
            "factory": FAC,
            "round": rnd,
            "generator": GEN,
            "designed": True,
            "kind": "designed",
        },
    }


def notes(rnd, s):
    roles = ", ".join(f"{r} ({m})" for r, m in s["roles"])
    return (
        f"Roles: {roles}.\n"
        f"Disagreement that mattered: {s['d'][0]}.\n"
        f"Resolution cites that disagreement and changes the plan.\n"
        f"Joint outcome earned: yes — {s['joint']}\n"
        f"Bytes: compact leftover leftover leftover software-coord.\n"
        f"Unique vs used merge-queue/deploy/flag/incident/lock/schema/cache/"
        f"ratelimit/auth/payment/search/queue/cert/k8s-drain/monorepo/notebook; "
        f"banned Friday-freeze; polymer; r3033 capro; r3077–r3184 chem.\n"
        f"Novel coverage: {s['novel']}%\n"
        f"Next densify target: {s['dens']}.\n"
    )


def txn(args, fatal=True):
    r = subprocess.run(TXN + args, cwd=str(ROOT), capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        if fatal:
            raise SystemExit(r.returncode)
        return None
    return json.loads(r.stdout)


def hop_named():
    for slug in HOP:
        d = ROOT / "outputs/raw/2026-08-19-agentic" / slug
        if not d.is_dir():
            continue
        front = txn(["frontier", str(d)], fatal=False)
        if front is None:
            continue
        rnd = int(front["next_round"])
        resv = list(d.glob("ROUND-r*.reserved.json"))
        if resv:
            continue
        print(json.dumps({"hop_unreserved": slug, "next_round": rnd}), file=sys.stderr)
        return slug, rnd
    return None


def main() -> int:
    published = []
    i = 0
    hops = 0
    last_blocked = None
    while i < N:
        front = txn(["frontier", str(DIR)])
        rnd = int(front["next_round"])
        if last_blocked == rnd:
            time.sleep(0.4)
            hops += 1
            if hops > 80:
                hop_named()
                print("MAC reserved; hop attempted", file=sys.stderr)
                return 1
            continue
        res = txn(["reserve", str(DIR), "--round", str(rnd), "--expected", "1"], fatal=False)
        if res is None:
            last_blocked = rnd
            hops += 1
            continue
        s = SCEN[i]
        recd = rec(rnd, s)
        stage = Path(res["staging_dir"])
        batch = res.get("batch_file") or f"batch-r{rnd:02d}.jsonl"
        nfile = res.get("notes_file") or f"NOTES-r{rnd:02d}.md"
        (stage / Path(batch).name).write_text(json.dumps(recd, separators=(",", ":")) + "\n")
        (stage / Path(nfile).name).write_text(notes(rnd, s))
        txn(["publish", str(DIR), "--round", str(rnd), "--token", res["token"]])
        published.append((rnd, recd["id"]))
        print(json.dumps({"published": rnd, "id": recd["id"]}))
        i += 1
        hops = 0
        last_blocked = None
    print("PUBLISHED", len(published))
    for rnd, eid in published:
        print(f"r{rnd} {eid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
