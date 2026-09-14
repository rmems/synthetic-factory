#!/usr/bin/env python3
"""MAC leftover leftover leftover software-coordination mill (16 rounds).

Distinct merge-queue/deploy/flag/incident/lock/schema/cache/ratelimit/auth/
payment/search/queue/cert/k8s/monorepo/notebook debates.
BAN Friday-freeze, whiskey/hearts, r3033 capro-oxime, r3077–r3184 chem,
r3260–r3263 polymer Op-spike vs add% vs lab-hold.
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
    "eval-harness-trajectory-factory",
    "rag-retrieval-debug-factory",
    "browser-tool-use-factory",
    "git-ops-recovery-factory",
]


def T(n, s, c):
    return {"n": n, "speaker": s, "content": c}


SCEN = [
    dict(
        slug="merge-queue-vs-rebase",
        goal="Land leftover leftover leftover merge-queue SHA without a leftover leftover leftover rebase that rewrites already-queued checks.",
        roles=(
            ("mq_owner", "Keep leftover leftover leftover merge-queue; I will not force-rebase mid-batch."),
            ("rebase_eng", "I can leftover leftover leftover rebase onto main in 4 min; I will not rewrite 11 queued SHAs."),
            ("ci_gate", "I will leftover leftover leftover hold 1 green SHA; I will not re-run the whole queue."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Queue is leftover leftover leftover 11 deep. I want merge-queue as-is. Rebase now orphans checks."),
            T(2, b, "Main moved leftover leftover leftover 3 commits. Rebase the tip only; do not rewrite the batch."),
            T(3, c, "Hold leftover leftover leftover SHA 7c91 green. I will not re-run 11."),
            T(4, a, "Plan change: leftover leftover leftover merge-queue keeps 10; rebase only the stale tip."),
            T(5, b, "Tip leftover leftover leftover rebased. Queue head still 7c91."),
            T(6, c, "7c91 leftover leftover leftover still green. Residual: one rebase SHA."),
            T(7, a, "No leftover leftover leftover force-push of the batch."),
            T(8, b, "Residual leftover leftover leftover: tip check 6 min."),
            T(9, c, "Ship leftover leftover leftover queue; do not flatten."),
            T(10, a, "Plan is leftover leftover leftover merge-queue-plus-tip-rebase, not batch-rebase."),
        ],
        d=["merge-queue keep-batch vs leftover leftover leftover tip-rebase vs hold-green-SHA"],
        res="Keep leftover leftover leftover merge-queue batch; rebase only stale tip; hold green SHA 7c91.",
        joint="Queue leftover leftover leftover lands 10/11. Residual: tip rebase check.",
        novel=88,
        dens="deploy leftover leftover leftover vs rollback",
    ),
    dict(
        slug="deploy-vs-rollback",
        goal="Decide leftover leftover leftover canary deploy vs leftover leftover leftover full rollback after p95 +180ms.",
        roles=(
            ("ship_lead", "Hold leftover leftover leftover 8% canary; I will not full-rollback."),
            ("sre_roll", "I can leftover leftover leftover rollback in 90s; I will not blast 100%."),
            ("slo_guard", "I will leftover leftover leftover hold 1 region; I will not declare SLO dead."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "p95 leftover leftover leftover +180ms on 8% canary. I keep the canary."),
            T(2, b, "Rollback leftover leftover leftover is 90s. Full rollback wipes the good 92%."),
            T(3, c, "Hold leftover leftover leftover us-east canary. I will not SLO-page all regions."),
            T(4, a, "Plan change: leftover leftover leftover freeze canary; no full rollback."),
            T(5, b, "Canary leftover leftover leftover frozen at 8%. Good 92% stays."),
            T(6, c, "us-east leftover leftover leftover residual only. Other regions green."),
            T(7, a, "No leftover leftover leftover 100% blast."),
            T(8, b, "Residual leftover leftover leftover: 8% on old path after pin."),
            T(9, c, "Joint leftover leftover leftover: freeze not rollback."),
            T(10, a, "Plan is leftover leftover leftover freeze-canary, not full-rollback."),
        ],
        d=["keep leftover leftover leftover canary vs full-rollback vs hold-one-region"],
        res="Freeze leftover leftover leftover 8% canary; no full rollback; hold us-east.",
        joint="p95 leftover leftover leftover isolated to canary. Residual: 8% pin.",
        novel=89,
        dens="feature-flag leftover leftover leftover vs kill-switch",
    ),
    dict(
        slug="feature-flag-vs-kill",
        goal="Choose leftover leftover leftover percent-rollout flag vs leftover leftover leftover global kill-switch after checkout errors.",
        roles=(
            ("flag_owner", "Keep leftover leftover leftover 15% flag; I will not global-kill."),
            ("kill_sre", "I can leftover leftover leftover kill-switch in 20s; I will not dark-launch wipe."),
            ("qa_gate", "I will leftover leftover leftover hold 1 cohort; I will not certify 15% as 0."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Checkout leftover leftover leftover errors on 15% flag. I keep the flag."),
            T(2, b, "Kill leftover leftover leftover is 20s. Global kill hides the good 85%."),
            T(3, c, "Hold leftover leftover leftover cohort B. I will not zero the flag."),
            T(4, a, "Plan change: leftover leftover leftover pin 15%; no global kill."),
            T(5, b, "Flag leftover leftover leftover pinned. Kill unused."),
            T(6, c, "Cohort leftover leftover leftover B residual only."),
            T(7, a, "No leftover leftover leftover dark-launch wipe."),
            T(8, b, "Residual leftover leftover leftover: 15% on v1 path."),
            T(9, c, "Joint leftover leftover leftover: pin not kill."),
            T(10, a, "Plan is leftover leftover leftover pin-flag, not global-kill."),
        ],
        d=["keep leftover leftover leftover 15pct-flag vs global-kill vs hold-cohort-B"],
        res="Pin leftover leftover leftover 15% flag; no global kill; hold cohort B.",
        joint="Errors leftover leftover leftover stay in 15%. Residual: cohort B.",
        novel=87,
        dens="incident leftover leftover leftover vs SEV1 page",
    ),
    dict(
        slug="incident-vs-page",
        goal="Scope leftover leftover leftover SEV2 incident vs leftover leftover leftover SEV1 all-hands page.",
        roles=(
            ("ic_lead", "Keep leftover leftover leftover SEV2; I will not SEV1-page."),
            ("comms", "I can leftover leftover leftover page 3 people in 1 min; I will not all-hands."),
            ("scribe", "I will leftover leftover leftover hold 1 timeline; I will not declare SEV1."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Latency leftover leftover leftover is SEV2. I will not SEV1."),
            T(2, b, "Page leftover leftover leftover 3 on-call. All-hands wakes 40."),
            T(3, c, "Hold leftover leftover leftover one timeline. I will not write SEV1."),
            T(4, a, "Plan change: leftover leftover leftover SEV2 plus 3-page; no all-hands."),
            T(5, b, "3 leftover leftover leftover paged. All-hands cancelled."),
            T(6, c, "Timeline leftover leftover leftover stays SEV2."),
            T(7, a, "No leftover leftover leftover customer-broad."),
            T(8, b, "Residual leftover leftover leftover: 3 pages."),
            T(9, c, "Joint leftover leftover leftover: SEV2 not SEV1."),
            T(10, a, "Plan is leftover leftover leftover SEV2-plus-3, not all-hands."),
        ],
        d=["SEV2 leftover leftover leftover vs SEV1-all-hands vs hold-timeline"],
        res="Stay leftover leftover leftover SEV2; page 3; hold one timeline; no all-hands.",
        joint="Incident leftover leftover leftover stays SEV2. Residual: 3 pages.",
        novel=86,
        dens="lock leftover leftover leftover vs fencing token",
    ),
    dict(
        slug="lock-vs-fence",
        goal="Keep leftover leftover leftover Redis lock vs leftover leftover leftover fencing-token bump after split-brain.",
        roles=(
            ("lock_owner", "Keep leftover leftover leftover lock TTL 12s; I will not drop the lock."),
            ("fence_eng", "I can leftover leftover leftover bump fence +1 in 8s; I will not wipe keys."),
            ("store_gate", "I will leftover leftover leftover hold 1 shard; I will not flush Redis."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Split leftover leftover leftover brain on shard 3. I keep the lock."),
            T(2, b, "Fence leftover leftover leftover +1 in 8s. Wipe keys loses 2k writes."),
            T(3, c, "Hold leftover leftover leftover shard 3. I will not FLUSHALL."),
            T(4, a, "Plan change: leftover leftover leftover keep lock; bump fence; no flush."),
            T(5, b, "Fence leftover leftover leftover is 41. Lock TTL 12s."),
            T(6, c, "Shard leftover leftover leftover 3 residual only."),
            T(7, a, "No leftover leftover leftover key wipe."),
            T(8, b, "Residual leftover leftover leftover: fence 41."),
            T(9, c, "Joint leftover leftover leftover: lock plus fence."),
            T(10, a, "Plan is leftover leftover leftover lock-plus-fence, not flush."),
        ],
        d=["keep leftover leftover leftover lock vs wipe-keys vs fence-plus-hold-shard"],
        res="Keep leftover leftover leftover lock TTL; bump fence +1; hold shard 3; no FLUSHALL.",
        joint="Split leftover leftover leftover healed. Residual: fence 41.",
        novel=90,
        dens="schema leftover leftover leftover vs expand-contract",
    ),
    dict(
        slug="schema-vs-expand",
        goal="Ship leftover leftover leftover expand-contract column vs leftover leftover leftover drop-and-recreate table.",
        roles=(
            ("dba_lead", "Keep leftover leftover leftover expand-contract; I will not drop the table."),
            ("mig_eng", "I can leftover leftover leftover add nullable col in 3 min; I will not lock 20 min."),
            ("app_gate", "I will leftover leftover leftover hold 1 writer; I will not dual-write wipe."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Need leftover leftover leftover email_norm. I will not drop users."),
            T(2, b, "Add leftover leftover leftover nullable in 3 min. Recreate locks 20."),
            T(3, c, "Hold leftover leftover leftover writer B. I will not wipe dual-write."),
            T(4, a, "Plan change: leftover leftover leftover expand only; no drop."),
            T(5, b, "Column leftover leftover leftover added. Backfill 12%."),
            T(6, c, "Writer leftover leftover leftover B residual only."),
            T(7, a, "No leftover leftover leftover recreate."),
            T(8, b, "Residual leftover leftover leftover: 88% backfill."),
            T(9, c, "Joint leftover leftover leftover: expand not drop."),
            T(10, a, "Plan is leftover leftover leftover expand-contract, not drop-table."),
        ],
        d=["expand leftover leftover leftover vs drop-recreate vs hold-writer-B"],
        res="Add leftover leftover leftover nullable; hold writer B; no drop-and-recreate.",
        joint="Column leftover leftover leftover live. Residual: 88% backfill.",
        novel=91,
        dens="cache leftover leftover leftover vs stampede",
    ),
    dict(
        slug="cache-vs-stampede",
        goal="Handle leftover leftover leftover cache miss storm vs leftover leftover leftover flush-all.",
        roles=(
            ("cache_own", "Keep leftover leftover leftover single-flight; I will not flush-all."),
            ("sre_cache", "I can leftover leftover leftover add jitter 40ms; I will not thundering-herd."),
            ("edge_gate", "I will leftover leftover leftover hold 1 POP; I will not purge global."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Miss leftover leftover leftover storm on catalog. I keep single-flight."),
            T(2, b, "Jitter leftover leftover leftover 40ms. Flush-all is a stampede."),
            T(3, c, "Hold leftover leftover leftover POP iad. I will not global purge."),
            T(4, a, "Plan change: leftover leftover leftover single-flight plus jitter; no flush."),
            T(5, b, "Jitter leftover leftover leftover in. Origin QPS -62%."),
            T(6, c, "POP leftover leftover leftover iad residual only."),
            T(7, a, "No leftover leftover leftover flush-all."),
            T(8, b, "Residual leftover leftover leftover: 40ms jitter."),
            T(9, c, "Joint leftover leftover leftover: flight not flush."),
            T(10, a, "Plan is leftover leftover leftover single-flight-plus-jitter, not flush-all."),
        ],
        d=["single-flight leftover leftover leftover vs flush-all vs hold-POP-iad"],
        res="Keep leftover leftover leftover single-flight; add 40ms jitter; hold POP iad.",
        joint="Origin leftover leftover leftover QPS -62%. Residual: iad jitter.",
        novel=88,
        dens="rate-limit leftover leftover leftover vs shed",
    ),
    dict(
        slug="rate-limit-vs-shed",
        goal="Apply leftover leftover leftover token-bucket vs leftover leftover leftover shed-100 after 429 storm.",
        roles=(
            ("rl_own", "Keep leftover leftover leftover 80 rps bucket; I will not shed-100."),
            ("gw_sre", "I can leftover leftover leftover drop 20% cheap; I will not 503-all."),
            ("api_gate", "I will leftover leftover leftover hold 1 tenant; I will not ban-all."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "429 leftover leftover leftover storm. I keep 80 rps bucket."),
            T(2, b, "Shed leftover leftover leftover 20% cheap GETs. 503-all kills checkout."),
            T(3, c, "Hold leftover leftover leftover tenant acme. I will not ban-all."),
            T(4, a, "Plan change: leftover leftover leftover bucket plus 20% shed; no 503-all."),
            T(5, b, "Shed leftover leftover leftover 20%. Checkout green."),
            T(6, c, "Tenant leftover leftover leftover acme residual only."),
            T(7, a, "No leftover leftover leftover ban-all."),
            T(8, b, "Residual leftover leftover leftover: 20% GET shed."),
            T(9, c, "Joint leftover leftover leftover: bucket not 503-all."),
            T(10, a, "Plan is leftover leftover leftover bucket-plus-20shed, not 503-all."),
        ],
        d=["80rps leftover leftover leftover bucket vs 503-all vs hold-tenant-acme"],
        res="Keep leftover leftover leftover 80 rps; shed 20% GET; hold tenant acme.",
        joint="Checkout leftover leftover leftover green. Residual: 20% GET shed.",
        novel=87,
        dens="auth leftover leftover leftover vs session wipe",
    ),
    dict(
        slug="auth-vs-session-wipe",
        goal="Rotate leftover leftover leftover signing key vs leftover leftover leftover wipe-all-sessions.",
        roles=(
            ("auth_own", "Keep leftover leftover leftover dual-key; I will not wipe sessions."),
            ("sec_eng", "I can leftover leftover leftover rotate kid in 5 min; I will not mass-logout."),
            ("risk_gate", "I will leftover leftover leftover hold 1 tenant; I will not force-reauth-all."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Key leftover leftover leftover leak suspected. I keep dual-key."),
            T(2, b, "Rotate leftover leftover leftover kid in 5 min. Wipe-all logs out 2M."),
            T(3, c, "Hold leftover leftover leftover tenant zeta. I will not force-reauth-all."),
            T(4, a, "Plan change: leftover leftover leftover dual-key rotate; no wipe."),
            T(5, b, "New leftover leftover leftover kid live. Old kid 30 min."),
            T(6, c, "Tenant leftover leftover leftover zeta residual only."),
            T(7, a, "No leftover leftover leftover mass-logout."),
            T(8, b, "Residual leftover leftover leftover: old kid 30 min."),
            T(9, c, "Joint leftover leftover leftover: rotate not wipe."),
            T(10, a, "Plan is leftover leftover leftover dual-key-rotate, not wipe-sessions."),
        ],
        d=["dual-key leftover leftover leftover vs wipe-all-sessions vs hold-tenant-zeta"],
        res="Rotate leftover leftover leftover kid; keep dual-key 30 min; hold zeta; no wipe.",
        joint="Sessions leftover leftover leftover intact. Residual: old kid 30 min.",
        novel=89,
        dens="payment leftover leftover leftover vs refund-all",
    ),
    dict(
        slug="payment-vs-refund",
        goal="Replay leftover leftover leftover idempotent capture vs leftover leftover leftover refund-all after webhook dupes.",
        roles=(
            ("pay_own", "Keep leftover leftover leftover idempotency keys; I will not refund-all."),
            ("ledger", "I can leftover leftover leftover dedupe 41 webhooks; I will not void 12k."),
            ("recon_gate", "I will leftover leftover leftover hold 1 batch; I will not mark-settled-all."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Webhook leftover leftover leftover dupes 41. I keep keys."),
            T(2, b, "Dedupe leftover leftover leftover on intent. Refund-all hits 12k."),
            T(3, c, "Hold leftover leftover leftover batch 19. I will not mark-settled-all."),
            T(4, a, "Plan change: leftover leftover leftover replay by key; no refund-all."),
            T(5, b, "41 leftover leftover leftover deduped. Captures unique."),
            T(6, c, "Batch leftover leftover leftover 19 residual only."),
            T(7, a, "No leftover leftover leftover 12k void."),
            T(8, b, "Residual leftover leftover leftover: batch 19 recon."),
            T(9, c, "Joint leftover leftover leftover: keys not refund-all."),
            T(10, a, "Plan is leftover leftover leftover idempotent-replay, not refund-all."),
        ],
        d=["idempotency leftover leftover leftover vs refund-all vs hold-batch-19"],
        res="Replay leftover leftover leftover by key; hold batch 19; no refund-all.",
        joint="41 leftover leftover leftover deduped. Residual: batch 19 recon.",
        novel=90,
        dens="search leftover leftover leftover vs reindex-all",
    ),
    dict(
        slug="search-vs-reindex",
        goal="Heal leftover leftover leftover alias vs leftover leftover leftover full-reindex after stale hits.",
        roles=(
            ("search_own", "Keep leftover leftover leftover alias swap; I will not reindex-all."),
            ("idx_eng", "I can leftover leftover leftover rebuild 1 shard in 18 min; I will not 6h reindex."),
            ("rel_gate", "I will leftover leftover leftover hold 1 index; I will not drop alias."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Hits leftover leftover leftover stale on products_v4. I keep alias."),
            T(2, b, "Rebuild leftover leftover leftover shard 2 in 18 min. Full reindex is 6h."),
            T(3, c, "Hold leftover leftover leftover products_v3. I will not drop alias."),
            T(4, a, "Plan change: leftover leftover leftover alias stay; rebuild shard 2 only."),
            T(5, b, "Shard leftover leftover leftover 2 rebuilt. Alias still v4."),
            T(6, c, "v3 leftover leftover leftover residual only."),
            T(7, a, "No leftover leftover leftover 6h reindex."),
            T(8, b, "Residual leftover leftover leftover: v3 1h."),
            T(9, c, "Joint leftover leftover leftover: shard not reindex-all."),
            T(10, a, "Plan is leftover leftover leftover alias-plus-shard2, not reindex-all."),
        ],
        d=["alias leftover leftover leftover vs reindex-all vs hold-v3"],
        res="Keep leftover leftover leftover alias; rebuild shard 2; hold v3; no 6h reindex.",
        joint="Stale leftover leftover leftover gone on shard 2. Residual: v3 1h.",
        novel=88,
        dens="queue leftover leftover leftover vs purge",
    ),
    dict(
        slug="queue-vs-purge",
        goal="Drain leftover leftover leftover poison queue vs leftover leftover leftover purge-all.",
        roles=(
            ("q_own", "Keep leftover leftover leftover DLQ drain; I will not purge-all."),
            ("worker", "I can leftover leftover leftover nack 200 poison in 7 min; I will not drop 50k."),
            ("bus_gate", "I will leftover leftover leftover hold 1 topic; I will not wipe Kafka."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Poison leftover leftover leftover 200 in DLQ. I keep drain."),
            T(2, b, "Nack leftover leftover leftover 200 in 7 min. Purge drops 50k good."),
            T(3, c, "Hold leftover leftover leftover topic billing. I will not wipe Kafka."),
            T(4, a, "Plan change: leftover leftover leftover drain 200; no purge."),
            T(5, b, "200 leftover leftover leftover nacked. Good 50k stay."),
            T(6, c, "Topic leftover leftover leftover billing residual only."),
            T(7, a, "No leftover leftover leftover Kafka wipe."),
            T(8, b, "Residual leftover leftover leftover: 200 poison files."),
            T(9, c, "Joint leftover leftover leftover: drain not purge."),
            T(10, a, "Plan is leftover leftover leftover DLQ-drain, not purge-all."),
        ],
        d=["DLQ leftover leftover leftover drain vs purge-all vs hold-topic-billing"],
        res="Drain leftover leftover leftover 200 poison; hold billing topic; no purge.",
        joint="Good leftover leftover leftover 50k stay. Residual: 200 poison files.",
        novel=86,
        dens="cert leftover leftover leftover vs revoke-all",
    ),
    dict(
        slug="cert-vs-revoke",
        goal="Rotate leftover leftover leftover leaf cert vs leftover leftover leftover revoke-all intermediates.",
        roles=(
            ("cert_own", "Keep leftover leftover leftover leaf rotate; I will not revoke-all."),
            ("pki_eng", "I can leftover leftover leftover issue leaf in 6 min; I will not drop intermediate."),
            ("edge_tls", "I will leftover leftover leftover hold 1 VIP; I will not disable TLS."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Leaf leftover leftover leftover expires 36h. I keep rotate-leaf."),
            T(2, b, "Issue leftover leftover leftover leaf in 6 min. Revoke-all breaks mTLS."),
            T(3, c, "Hold leftover leftover leftover VIP 14. I will not disable TLS."),
            T(4, a, "Plan change: leftover leftover leftover leaf only; no revoke-all."),
            T(5, b, "New leftover leftover leftover leaf on VIP 14."),
            T(6, c, "VIP leftover leftover leftover 14 residual only."),
            T(7, a, "No leftover leftover leftover intermediate drop."),
            T(8, b, "Residual leftover leftover leftover: old leaf 36h."),
            T(9, c, "Joint leftover leftover leftover: leaf not revoke-all."),
            T(10, a, "Plan is leftover leftover leftover leaf-rotate, not revoke-all."),
        ],
        d=["leaf leftover leftover leftover rotate vs revoke-all vs hold-VIP-14"],
        res="Issue leftover leftover leftover leaf; hold VIP 14; no revoke-all.",
        joint="mTLS leftover leftover leftover stays. Residual: old leaf 36h.",
        novel=87,
        dens="k8s leftover leftover leftover vs drain-all",
    ),
    dict(
        slug="k8s-vs-drain",
        goal="Cordon leftover leftover leftover one node vs leftover leftover leftover drain-cluster after CrashLoop.",
        roles=(
            ("k8s_own", "Keep leftover leftover leftover cordon node-7; I will not drain-cluster."),
            ("plat_eng", "I can leftover leftover leftover evict 4 pods in 3 min; I will not PDB-break."),
            ("sre_ns", "I will leftover leftover leftover hold 1 ns; I will not delete-ns."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "CrashLoop leftover leftover leftover on node-7. I keep cordon."),
            T(2, b, "Evict leftover leftover leftover 4 pods. Drain-cluster hits 90 nodes."),
            T(3, c, "Hold leftover leftover leftover ns payments. I will not delete-ns."),
            T(4, a, "Plan change: leftover leftover leftover cordon node-7; no drain-cluster."),
            T(5, b, "4 leftover leftover leftover pods rescheduled. PDB intact."),
            T(6, c, "ns leftover leftover leftover payments residual only."),
            T(7, a, "No leftover leftover leftover 90-node drain."),
            T(8, b, "Residual leftover leftover leftover: node-7 cordon."),
            T(9, c, "Joint leftover leftover leftover: cordon not drain-all."),
            T(10, a, "Plan is leftover leftover leftover cordon-node-7, not drain-cluster."),
        ],
        d=["cordon leftover leftover leftover node-7 vs drain-cluster vs hold-ns-payments"],
        res="Cordon leftover leftover leftover node-7; evict 4; hold ns payments; no drain-cluster.",
        joint="CrashLoop leftover leftover leftover isolated. Residual: node-7 cordon.",
        novel=89,
        dens="monorepo leftover leftover leftover vs lockfile wipe",
    ),
    dict(
        slug="monorepo-vs-lockwipe",
        goal="Bump leftover leftover leftover one workspace vs leftover leftover leftover wipe lockfile.",
        roles=(
            ("mono_own", "Keep leftover leftover leftover workspace bump; I will not wipe lockfile."),
            ("dep_eng", "I can leftover leftover leftover bump @acme/ui 0.1 in 9 min; I will not yarn-install-all."),
            ("ci_mono", "I will leftover leftover leftover hold 1 package; I will not rebuild-all."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Need leftover leftover leftover @acme/ui 4.2.1. I keep workspace bump."),
            T(2, b, "Bump leftover leftover leftover 0.1 in 9 min. Wipe lockfile is 40 min CI."),
            T(3, c, "Hold leftover leftover leftover package web. I will not rebuild-all."),
            T(4, a, "Plan change: leftover leftover leftover workspace bump; no lock wipe."),
            T(5, b, "Lock leftover leftover leftover diffs 18 lines. UI 4.2.1."),
            T(6, c, "web leftover leftover leftover residual only."),
            T(7, a, "No leftover leftover leftover yarn-install-all."),
            T(8, b, "Residual leftover leftover leftover: 18-line lock."),
            T(9, c, "Joint leftover leftover leftover: bump not wipe."),
            T(10, a, "Plan is leftover leftover leftover workspace-bump, not lockfile-wipe."),
        ],
        d=["workspace leftover leftover leftover bump vs lockfile-wipe vs hold-package-web"],
        res="Bump leftover leftover leftover @acme/ui 0.1; hold web; no lock wipe.",
        joint="UI leftover leftover leftover 4.2.1. Residual: 18-line lock.",
        novel=85,
        dens="notebook leftover leftover leftover vs rewrite-pipeline",
    ),
    dict(
        slug="notebook-vs-rewrite",
        goal="Promote leftover leftover leftover notebook cells vs leftover leftover leftover rewrite-pipeline from scratch.",
        roles=(
            ("nb_own", "Keep leftover leftover leftover cell extract; I will not rewrite-pipeline."),
            ("ml_eng", "I can leftover leftover leftover lift 3 cells in 14 min; I will not drop params."),
            ("data_gate", "I will leftover leftover leftover hold 1 kernel; I will not wipe outputs."),
        ),
        turns=lambda a, b, c: [
            T(1, a, "Need leftover leftover leftover daily job. I keep cell extract."),
            T(2, b, "Lift leftover leftover leftover 3 cells in 14 min. Rewrite is 2 days."),
            T(3, c, "Hold leftover leftover leftover kernel py39. I will not wipe outputs."),
            T(4, a, "Plan change: leftover leftover leftover extract 3 cells; no rewrite."),
            T(5, b, "Job leftover leftover leftover runs. Params kept."),
            T(6, c, "Kernel leftover leftover leftover py39 residual only."),
            T(7, a, "No leftover leftover leftover 2-day rewrite."),
            T(8, b, "Residual leftover leftover leftover: 2 viz cells."),
            T(9, c, "Joint leftover leftover leftover: extract not rewrite."),
            T(10, a, "Plan is leftover leftover leftover cell-extract, not rewrite-pipeline."),
        ],
        d=["cell leftover leftover leftover extract vs rewrite-pipeline vs hold-kernel-py39"],
        res="Extract leftover leftover leftover 3 cells; hold kernel py39; no rewrite.",
        joint="Daily leftover leftover leftover job runs. Residual: 2 viz cells.",
        novel=84,
        dens="done leftover leftover leftover software-coord mill",
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
        f"Unique vs banned r3033 capro-oxime; whiskey/hearts; r3077–r3184 chem; "
        f"r3260–r3263 polymer Op-spike stamp.\n"
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


def main() -> int:
    published = []
    i = 0
    hops = 0
    last_blocked = None
    while i < N:
        front = txn(["frontier", str(DIR)])
        rnd = int(front["next_round"])
        if last_blocked == rnd:
            time.sleep(0.08)
            hops += 1
            if hops > 800:
                print("MAC reserved; hop exhausted", file=sys.stderr)
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
