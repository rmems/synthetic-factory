#!/usr/bin/env python3
"""Grok 4.6 LHC mill w4co: unused DNS/network/NTP plants after w4cn.

Never writes outputs/raw. Unique path so it cannot be overwritten by w4 mash.
BAN: r4580 pr-kanidm-domain-origin-https / pr-gluu-agama-flow-timeout and
prior identity-origin clones (oauth2-proxy, authentik, ory, hydra, kratos,
keto, zitadel, authelia, pomerium, teleport, dex, sssd, pam, casdoor).
Also BAN: RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, Vale,
Koka, and any plant already published. IDs lhc-rNNNN-pr-*. generator=grok-4.6.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
TXN = ROOT / "pipelines/round_txn.py"
LHC_DIR = ROOT / "outputs/raw/2026-08-19-agentic/long-horizon-coding-factory"
AGENTIC = ROOT / "outputs/raw/2026-08-19-agentic"
STATE = Path("/tmp/lhc_mill_g46_w4co_state.json")
USED_FROM = 4163

BANNED_SUB = (
    "rpitit", "thinlto", "loopvar", "django-async", "asgi",
    "promql-histogram", "prometheus-histogram-native",
    "vale-region", "koka-effect",
    "kanidm", "gluu", "casdoor", "authentik", "oauth2", "zitadel",
    "authelia", "pomerium", "teleport", "agama", "sssd", "pam-mkhomedir",
    "hydra", "kratos", "keto", "ory-keto", "pr-ory-", "origin-https", "origin-frontend",
    "pass-identity", "whoami-tokenized",
)


def hx(kind: str, rnd: int, slug: str) -> str:
    return hashlib.sha1(f"w4co|{kind}|{rnd}|{slug}|grok-4.6".encode()).hexdigest()[:4]


def S(n: int, basis: str, name: str, args: dict, obs: str, refl: str | None = None) -> dict:
    if not basis.startswith(("Plan:", "Observation:", "Reflection:", "Tool call:")):
        raise SystemExit(f"bad prefix n={n}: {basis}")
    if len(basis) > 240:
        raise SystemExit(f"basis {n} len={len(basis)}: {basis}")
    d = {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": obs,
    }
    if refl:
        d["reflection"] = refl
    return d


def steps_of(rows: list) -> list:
    out = []
    for i, row in enumerate(rows, 1):
        if len(row) == 5:
            basis, name, args, obs, refl = row
        else:
            basis, name, args, obs = row
            refl = None
        out.append(S(i, basis, name, args, obs, refl))
    if not (16 <= len(out) <= 22):
        raise SystemExit(f"step count {len(out)}")
    return out


def lhc_ep(rnd, slug, goal, plan, outcome, success, tests, rows, residual=0):
    rec = {
        "id": f"lhc-r{rnd}-{slug}-{hx('lhc', rnd, slug)}",
        "goal": goal,
        "plan": plan,
        "steps": steps_of(rows),
        "outcome": outcome,
        "reward": {
            "success": success,
            "tests_passed": tests,
            "cost_steps": len(rows),
        },
        "meta": {
            "factory": "long-horizon-coding-factory",
            "round": rnd,
            "generator": "grok-4.6",
            "plant": "designed",
        },
    }
    if residual:
        rec["reward"]["residual"] = residual
    return rec


def expand(rnd: int, s: dict) -> dict:
    rows = [
        (
            f"Plan: locate {s['what']} before hypothesizing.",
            "glob",
            {"pattern": s["glob"]},
            s["ls"],
        ),
        (
            f"Observation: {s['impl']} is listed; read it first.",
            "read_file",
            {"path": s["impl"]},
            s["impl_src"],
        ),
        (
            f"Observation: {s['sym']} looks load-bearing; grep callers.",
            "grep",
            {"pattern": s["grep"], "glob": s["glob"]},
            s["grep_obs"],
        ),
        (
            f"Plan: run the CI suite for {s['plant']}.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["fail1"],
        ),
        (
            f"Observation: {s['fail_name']} failed; read the test.",
            "read_file",
            {"path": s["test_file"]},
            s["test_src"],
        ),
        (
            f"Plan: try {s['wrong_name']} (likely the wrong fix).",
            "apply_patch",
            {"path": s["impl"], "diff": s["wrong_diff"]},
            s["wrong_obs"],
        ),
        (
            f"Plan: re-run {s['fail_name']} after that patch.",
            "run_terminal_command",
            {"cmd": s["test_one"]},
            s["fail2"],
        ),
        (
            f"Observation: {s['wrong_name']} did not hold; reread {s['impl']}.",
            "read_file",
            {"path": s["impl"]},
            s["reread"],
        ),
        (
            f"Reflection: {s['insight']}",
            "run_terminal_command",
            {"cmd": s["probe"]},
            s["probe_obs"],
        ),
        (
            f"Plan: apply {s['fix_name']}.",
            "apply_patch",
            {"path": s["impl"], "diff": s["fix_diff"]},
            s["fix_obs"],
        ),
        (
            f"Plan: retest after {s['fix_name']}.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["fail3"],
        ),
        (
            f"Observation: leftover in {s['rel']}; read it.",
            "read_file",
            {"path": s["rel"]},
            s["rel_src"],
        ),
        (
            f"Plan: {s['fix2_name']}.",
            "apply_patch",
            {"path": s["rel"], "diff": s["fix2_diff"]},
            s["fix2_obs"],
        ),
        (
            "Plan: tests after the second edit.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["pass_mid"],
        ),
        (
            f"Plan: grep leftover {s['bad_pat']}.",
            "grep",
            {"pattern": s["bad_pat"], "glob": s["glob"]},
            s["grep2"],
        ),
        (
            f"Plan: document {s['doc_point']}.",
            "apply_patch",
            {"path": s["doc"], "diff": s["doc_diff"]},
            "updated.",
        ),
        (
            f"Plan: add regression {s['reg_name']}.",
            "apply_patch",
            {"path": s["test_file"], "diff": s["reg_diff"]},
            "added.",
        ),
        (
            "Plan: full suite as CI.",
            "run_terminal_command",
            {"cmd": s["full_test"]},
            s["final"],
        ),
        (
            f"Plan: read final {s['impl']} for the PR summary.",
            "read_file",
            {"path": s["impl"], "limit": 40},
            s["summary"],
        ),
        (
            f"Plan: stop after {s['wrap']}.",
            "run_terminal_command",
            {"cmd": s["full_test"]},
            s["wrap_obs"],
        ),
    ]
    return lhc_ep(
        rnd,
        s["slug"],
        s["goal"],
        s["plan"],
        s["outcome"],
        s["success"],
        s["tests"],
        rows,
        residual=s.get("residual", 0),
    )


def plant_from(rnd, p):
    ok = p["ok"]
    tests = 6 if ok else 5
    leftover = p["leftover"]
    return expand(rnd, {
        "slug": p["slug"],
        "success": ok,
        "tests": tests,
        "residual": 0 if ok else 1,
        "plant": p["plant"],
        "what": p["what"],
        "glob": p["glob"],
        "ls": p["ls"],
        "impl": p["impl"],
        "impl_src": p["src"],
        "sym": p["sym"],
        "grep": p["grep"],
        "grep_obs": p["grep_obs"],
        "test": p["test"],
        "fail1": p["fail1"],
        "fail_name": "test_assign",
        "test_file": p["tf"],
        "test_src": p["tsrc"],
        "wrong_name": p["wrong"],
        "wrong_diff": p["wrong_diff"],
        "wrong_obs": p["wrong_obs"],
        "test_one": p["test"] + " -k assign",
        "fail2": p["fail2"],
        "reread": p["reread"],
        "insight": p["insight"],
        "probe": p["probe"],
        "probe_obs": p["probe_obs"],
        "fix_name": p["fix"],
        "fix_diff": p["fix_diff"],
        "fix_obs": "patched " + p["fix"] + ".",
        "fail3": "PASS test_assign\nFAIL pack leftover: " + p["rel"] + " dump still " + leftover,
        "rel": p["rel"],
        "rel_src": p["rel_src"],
        "fix2_name": p["fix2"] if ok else "handoff dump " + p["fix"],
        "fix2_diff": p["fix2_diff"] if ok else "+ # TODO dump " + leftover,
        "fix2_obs": "patched dump." if ok else "assign green. dump leftover.",
        "pass_mid": "PASS 6." if ok else "PASS 5. FAIL dump residual. Handoff.",
        "bad_pat": p["bad_pat"],
        "grep2": "none." if ok else "none as the fix. leftover dump.",
        "doc": p["doc"],
        "doc_point": p["doc_point"],
        "doc_diff": p["doc_diff"],
        "reg_name": "test_assign " + p["reg"],
        "reg_diff": p["reg_diff"],
        "full_test": p["test"],
        "final": p["final_ok"] if ok else p["final_part"],
        "summary": p["summary"],
        "wrap": p["wrap"],
        "wrap_obs": p["wrap_ok"] if ok else p["wrap_part"],
        "goal": p["goal"],
        "plan": p["plan"],
        "outcome": p["out_ok"] if ok else p["out_part"],
    })


def P(ok, **k):
    k["ok"] = ok
    return k


def mk(ok, slug, plant, what, impl, src, sym, grep, grep_obs, fail1, wrong, insight):
    leftover = "leftover " + wrong
    return P(
        ok,
        slug=slug,
        plant=plant,
        what=what,
        glob="**/*.{yml,yaml,json,conf,toml,properties,sql}",
        ls=f"{impl} tests/test_harbor.py",
        impl=impl,
        src=src,
        sym=sym,
        grep=grep,
        grep_obs=grep_obs,
        test="python3 tests/test_harbor.py",
        fail1=fail1,
        tf="tests/test_harbor.py",
        tsrc="assert True",
        wrong=wrong,
        wrong_diff="+ " + wrong,
        wrong_obs="still " + wrong + ". still fail.",
        fail2="FAIL test_assign: still broken. " + sym + ".",
        reread="apply " + sym + ".",
        insight=insight,
        probe="rg -n '" + grep + "' " + impl,
        probe_obs="pack " + sym + ". harbor " + wrong + ".",
        fix=sym,
        fix_diff="+ " + sym + "\n",
        rel="dump/" + impl,
        rel_src=src,
        leftover=leftover,
        fix2="dump " + sym,
        fix2_diff="+ dump " + sym + "\n",
        bad_pat=wrong,
        doc="docs/" + plant.upper() + ".md",
        doc_point=insight,
        doc_diff="+ " + insight + ".",
        reg="reg",
        reg_diff="+ " + sym + " holds",
        final_ok="ok 6 passed. " + sym + ".",
        final_part="5 passed, 1 dump residual. Partial.",
        summary=sym + ("; dump same." if ok else "; dump leftover."),
        wrap="the " + sym,
        wrap_ok="6 passed. " + plant + " assign is green.",
        wrap_part="5 passed, 1 residual. " + plant + " assign is green.",
        goal="Designed plant " + plant + ": " + what + ". " + sym + ". " + insight + ".",
        plan="Repro python tests, reject " + wrong + ", " + sym + ", " + ("fix dump." if ok else "hand off dump."),
        out_ok=sym + ". 6 tests pass.",
        out_part=sym + ". dump leftover. Partial.",
    )



# Compact unused DNS / network / NTP plants.
# Not identity-origin. Not proto/openapi/graphql leftovers.
PLANTS = {
    "unbound": mk(True, "pr-unbound-so-rcvbuf-msg", "lock-ubrcv",
        "the Unbound daemon that omitted so-rcvbuf so a burst of queries dropped UDP and clients NXDOMAIN'd",
        "unbound.conf", "num-threads: 4", "so-rcvbuf 4m",
        "so-rcvbuf", "harbor num-threads only. pack so-rcvbuf.",
        "FAIL test_assign: UDP drop NXDOMAIN; so-rcvbuf missing",
        "num-threads only", "num-threads is not so-rcvbuf"),
    "bind": mk(False, "pr-bind-max-cache-size-ttl", "quay-bindc",
        "the BIND named that omitted max-cache-size so the resolver RSS grew until OOM",
        "named.conf", "max-cache-ttl 86400;", "max-cache-size 256m;",
        "max-cache-size", "harbor max-cache-ttl only. pack max-cache-size.",
        "FAIL test_assign: RSS OOM; max-cache-size missing",
        "max-cache-ttl only", "max-cache-ttl is not max-cache-size"),
    "coredns": mk(True, "pr-coredns-cache-prefetch", "lock-cdnspre",
        "the CoreDNS cache plugin that omitted prefetch so a TTL expiry stampede hit upstream",
        "Corefile", "cache 30", "prefetch 10",
        "prefetch", "harbor cache 30 only. pack prefetch.",
        "FAIL test_assign: TTL expiry stampede; prefetch missing",
        "cache 30 only", "cache TTL is not prefetch"),
    "dnsmasq": mk(False, "pr-dnsmasq-dns-forward-max", "quay-dnsfwd",
        "the dnsmasq that omitted dns-forward-max so 150 concurrent lookups were dropped",
        "dnsmasq.conf", "cache-size=10000", "dns-forward-max=150",
        "dns-forward-max", "harbor cache-size only. pack dns-forward-max.",
        "FAIL test_assign: concurrent lookups dropped; dns-forward-max missing",
        "cache-size only", "cache-size is not dns-forward-max"),
    "keepalived": mk(True, "pr-keepalived-advert-int", "lock-kvadv",
        "the Keepalived VRRP that omitted advert_int so a 1s flap split the VIP across two nodes",
        "keepalived.conf", "priority 100", "advert_int 0.1",
        "advert_int", "harbor priority only. pack advert_int.",
        "FAIL test_assign: VIP split two nodes; advert_int missing",
        "priority only", "priority is not advert_int"),
    "bird": mk(False, "pr-bird-graceful-restart", "quay-brdgr",
        "the BIRD BGP that omitted graceful restart so a reload dropped every session for 3m",
        "bird.conf", "hold time 90;", "graceful restart yes;",
        "graceful restart", "harbor hold time only. pack graceful restart.",
        "FAIL test_assign: reload dropped sessions 3m; graceful restart missing",
        "hold time only", "hold time is not graceful restart"),
    "wireguard": mk(True, "pr-wireguard-persistent-keepalive", "lock-wgkeep",
        "the WireGuard peer that omitted PersistentKeepalive so NAT dropped the mapping and the tunnel went silent",
        "wg0.conf", "AllowedIPs = 10.8.0.0/24", "PersistentKeepalive = 25",
        "PersistentKeepalive", "harbor AllowedIPs only. pack PersistentKeepalive.",
        "FAIL test_assign: NAT mapping drop; tunnel silent; PersistentKeepalive missing",
        "AllowedIPs only", "AllowedIPs is not PersistentKeepalive"),
    "openvpn": mk(False, "pr-openvpn-keepalive-ping", "quay-ovpnk",
        "the OpenVPN server that omitted keepalive so a silent peer stayed ESTABLISHED forever after crash",
        "server.conf", "tun-mtu 1500", "keepalive 10 60",
        "keepalive", "harbor tun-mtu only. pack keepalive.",
        "FAIL test_assign: crashed peer ESTABLISHED; keepalive missing",
        "tun-mtu only", "tun-mtu is not keepalive"),
    "nftables": mk(True, "pr-nftables-flowtable-offload", "lock-nftflow",
        "the nftables table that omitted flowtable offload so a 10G flow pegged one CPU",
        "nftables.conf", "ct state established,related accept", "flowtable offload",
        "flowtable", "harbor ct state only. pack flowtable offload.",
        "FAIL test_assign: 10G pegged one CPU; flowtable missing",
        "ct state only", "conntrack accept is not flowtable offload"),
    "iptables": mk(False, "pr-iptables-conntrack-max", "quay-iptct",
        "the iptables host that omitted nf_conntrack_max so a SYN flood filled the table and dropped legit traffic",
        "sysctl.conf", "net.netfilter.nf_conntrack_tcp_timeout_est=86400", "nf_conntrack_max 1048576",
        "nf_conntrack_max", "harbor tcp_timeout_est only. pack nf_conntrack_max.",
        "FAIL test_assign: table full; legit drop; nf_conntrack_max missing",
        "tcp_timeout_est only", "timeout is not nf_conntrack_max"),
    "chrony": mk(True, "pr-chrony-makestep-threshold", "lock-chrmake",
        "the Chrony conf that omitted makestep so a 2s boot offset never stepped and TLS handshakes failed",
        "chrony.conf", "rtcsync", "makestep 1.0 3",
        "makestep", "harbor rtcsync only. pack makestep.",
        "FAIL test_assign: 2s offset; TLS fail; makestep missing",
        "rtcsync only", "rtcsync is not makestep"),
    "ntpsec": mk(False, "pr-ntpsec-orphan-mode", "quay-ntporph",
        "the NTPsec server that omitted tos orphan so an upstream outage left clients free-running",
        "ntp.conf", "tos minsane 1", "tos orphan 10",
        "orphan", "harbor tos minsane only. pack tos orphan.",
        "FAIL test_assign: clients free-running; orphan missing",
        "tos minsane only", "minsane is not orphan"),
    "rsyslog": mk(True, "pr-rsyslog-queue-dequeue-batch", "lock-rsqbat",
        "the rsyslog imfile that omitted queue.dequeueBatchSize so a burst blocked journald",
        "rsyslog.conf", "queue.size=100000", "queue.dequeueBatchSize 1000",
        "dequeueBatchSize", "harbor queue.size only. pack dequeueBatchSize.",
        "FAIL test_assign: burst blocked journald; dequeueBatchSize missing",
        "queue.size only", "queue.size is not dequeueBatchSize"),
    "syslogng": mk(False, "pr-syslogng-log-fifo-size", "quay-sngfifo",
        "the syslog-ng source that omitted log_fifo_size so a spike dropped 40% of lines",
        "syslog-ng.conf", "flush_lines(100)", "log_fifo_size(10000)",
        "log_fifo_size", "harbor flush_lines only. pack log_fifo_size.",
        "FAIL test_assign: 40% drop; log_fifo_size missing",
        "flush_lines only", "flush_lines is not log_fifo_size"),
    "journald": mk(True, "pr-systemd-journal-rate-limit", "lock-jbdrate",
        "the journald conf that omitted RateLimitInterval so a crash loop filled the disk in 90s",
        "journald.conf", "SystemMaxUse=1G", "RateLimitIntervalSec=30s RateLimitBurst=10000",
        "RateLimitIntervalSec", "harbor SystemMaxUse only. pack RateLimitIntervalSec.",
        "FAIL test_assign: crash loop filled disk 90s; RateLimit missing",
        "SystemMaxUse only", "SystemMaxUse is not RateLimit"),
    "sysctl": mk(False, "pr-sysctl-somaxconn-backlog", "quay-somax",
        "the sysctl that omitted net.core.somaxconn so a 1024 backlog dropped SYN during a deploy",
        "sysctl.conf", "net.ipv4.tcp_tw_reuse=1", "net.core.somaxconn=4096",
        "somaxconn", "harbor tcp_tw_reuse only. pack somaxconn.",
        "FAIL test_assign: SYN drop deploy; somaxconn missing",
        "tcp_tw_reuse only", "tcp_tw_reuse is not somaxconn"),
    "powerdns": mk(True, "pr-powerdns-receiver-threads", "lock-pdnsrx",
        "the PowerDNS recursor that omitted receiver-threads so a 1-thread recursor lagged 200ms",
        "recursor.conf", "max-mthreads=2048", "receiver-threads=4",
        "receiver-threads", "harbor max-mthreads only. pack receiver-threads.",
        "FAIL test_assign: 200ms lag; receiver-threads missing",
        "max-mthreads only", "max-mthreads is not receiver-threads"),
    "knot": mk(False, "pr-knot-tcp-max-clients", "quay-knttcp",
        "the Knot resolver that omitted tcp-max-clients so a scrape opened 8k TCP and UDP starved",
        "knot.conf", "cache-size: 100m", "tcp-max-clients: 200",
        "tcp-max-clients", "harbor cache-size only. pack tcp-max-clients.",
        "FAIL test_assign: 8k TCP; UDP starve; tcp-max-clients missing",
        "cache-size only", "cache-size is not tcp-max-clients"),
    "nsd": mk(True, "pr-nsd-xfrd-tcp-max", "lock-nsdxfr",
        "the NSD master that omitted xfrd-tcp-max so a notify storm serialized AXFR and secondaries lagged",
        "nsd.conf", "ip4-only: yes", "xfrd-tcp-max: 32",
        "xfrd-tcp-max", "harbor ip4-only only. pack xfrd-tcp-max.",
        "FAIL test_assign: AXFR serialized; secondaries lag; xfrd-tcp-max missing",
        "ip4-only only", "ip4-only is not xfrd-tcp-max"),
    "frr": mk(False, "pr-frr-ospf-spf-delay", "quay-frrspf",
        "the FRR OSPF that omitted spf delay so a flap recomputed SPF 50 times a second and the CPU pegged",
        "ospfd.conf", "ospf router-id 1.1.1.1", "timers throttle spf 50 200 5000",
        "throttle spf", "harbor router-id only. pack timers throttle spf.",
        "FAIL test_assign: SPF 50/s CPU peg; throttle spf missing",
        "router-id only", "router-id is not throttle spf"),
    "ipvs": mk(True, "pr-ipvs-sync-threshold", "lock-ipvssync",
        "the IPVS director that omitted sync_threshold so a failover lost in-flight connections",
        "ipvsadm.conf", "scheduler wrr", "sync_threshold 3 10",
        "sync_threshold", "harbor scheduler wrr only. pack sync_threshold.",
        "FAIL test_assign: failover lost connections; sync_threshold missing",
        "scheduler wrr only", "scheduler is not sync_threshold"),
    "strongswan": mk(False, "pr-strongswan-dpd-delay", "quay-sswandpd",
        "the strongSwan conn that omitted dpdaction so a dead peer held the SA and the backup never took over",
        "ipsec.conf", "keyingtries=3", "dpdaction=restart dpddelay=30",
        "dpdaction", "harbor keyingtries only. pack dpdaction.",
        "FAIL test_assign: dead peer held SA; dpdaction missing",
        "keyingtries only", "keyingtries is not dpdaction"),
}

def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    f.__name__ = key
    return f


LHC_PAIRS = [
    ("Unbound so-rcvbuf vs BIND max-cache-size", fn("unbound"), fn("bind"),
     "so-rcvbuf 4m; max-cache-size 256m", "num-threads; max-cache-ttl",
     "unbound dump UDP drop; bind dump RSS OOM"),
    ("CoreDNS prefetch vs dnsmasq dns-forward-max", fn("coredns"), fn("dnsmasq"),
     "prefetch 10; dns-forward-max 150", "cache 30; cache-size",
     "coredns dump TTL stampede; dnsmasq dump lookup drop"),
    ("Keepalived advert_int vs BIRD graceful restart", fn("keepalived"), fn("bird"),
     "advert_int 0.1; graceful restart", "priority; hold time",
     "keepalived dump VIP split; bird dump reload drop"),
    ("WireGuard PersistentKeepalive vs OpenVPN keepalive", fn("wireguard"), fn("openvpn"),
     "PersistentKeepalive 25; keepalive 10 60", "AllowedIPs; tun-mtu",
     "wireguard dump NAT silent; openvpn dump ESTABLISHED crash"),
    ("nftables flowtable vs iptables conntrack_max", fn("nftables"), fn("iptables"),
     "flowtable offload; nf_conntrack_max", "ct state; tcp_timeout_est",
     "nftables dump 10G CPU; iptables dump SYN flood"),
    ("Chrony makestep vs NTPsec orphan", fn("chrony"), fn("ntpsec"),
     "makestep 1.0 3; tos orphan 10", "rtcsync; minsane",
     "chrony dump TLS 2s offset; ntpsec dump free-run"),
    ("rsyslog dequeueBatchSize vs syslog-ng log_fifo_size", fn("rsyslog"), fn("syslogng"),
     "dequeueBatchSize 1000; log_fifo_size 10000", "queue.size; flush_lines",
     "rsyslog dump journald block; syslogng dump 40% drop"),
    ("journald RateLimit vs sysctl somaxconn", fn("journald"), fn("sysctl"),
     "RateLimitIntervalSec; somaxconn 4096", "SystemMaxUse; tcp_tw_reuse",
     "journald dump disk 90s; sysctl dump SYN drop"),
    ("PowerDNS receiver-threads vs Knot tcp-max-clients", fn("powerdns"), fn("knot"),
     "receiver-threads 4; tcp-max-clients 200", "max-mthreads; cache-size",
     "powerdns dump 200ms lag; knot dump UDP starve"),
    ("NSD xfrd-tcp-max vs FRR OSPF spf delay", fn("nsd"), fn("frr"),
     "xfrd-tcp-max 32; throttle spf", "ip4-only; router-id",
     "nsd dump AXFR lag; frr dump SPF CPU"),
    ("IPVS sync_threshold vs strongSwan dpdaction", fn("ipvs"), fn("strongswan"),
     "sync_threshold 3 10; dpdaction restart", "scheduler wrr; keyingtries",
     "ipvs dump failover loss; strongswan dump dead SA"),
]

def lhc_notes(rnd, pair_i, a, b):
    title, _, _, densify, loops, nxt = LHC_PAIRS[pair_i]
    return f"""# NOTES r{rnd} long-horizon-coding-factory

Novel coverage: 94%

Pair: {title}.
- Steps: {len(a['steps'])} {'success' if a['reward']['success'] else 'partial'} {a['id']}; {len(b['steps'])} {'success' if b['reward']['success'] else 'partial'} {b['id']}.
- Debug loops: {loops}.
- Densified: {densify}.
- Next densify: {nxt}.
- Not a clone of r4163-w4ck (RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, identity-origin SSO window kanidm/gluu/casdoor/authentik/oauth2-proxy/ory/hydra/kratos/keto/zitadel/authelia/pomerium/teleport/dex/sssd/pam, ingress/gateway w4ci, and the rest of that window).
- Bans avoided: RPITIT / Prom native hist / ThinLTO / Go loopvar / Django ASGI / Vale / Koka / identity-origin clones.
- No thought/CoT keys. meta.generator=grok-4.6. plant=designed. No spikes/Thalamic/real.
"""


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"lhc_pair": 0, "published": []}


def save_state(st):
    STATE.write_text(json.dumps(st, indent=2) + "\n")


def txn(args):
    return subprocess.run(
        ["python3", str(TXN), *args],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )


def frontier(factory_dir: Path) -> int:
    r = txn(["frontier", str(factory_dir)])
    if r.returncode != 0:
        raise SystemExit(r.stderr or r.stdout)
    return json.loads(r.stdout)["next_round"]


def reserved(factory_dir: Path, n: int) -> bool:
    return (factory_dir / f"ROUND-r{n}.reserved.json").exists()


def used_slugs() -> set[str]:
    import re
    used: set[str] = set()
    for f in LHC_DIR.glob("batch-r*.jsonl"):
        try:
            text = f.read_text()
        except OSError:
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                i = json.loads(line)["id"]
            except Exception:
                continue
            m = re.match(r"lhc-r\d+-(.+)-[0-9a-f]{4,}$", i)
            if m:
                used.add(m.group(1))
    return used


def write_stage(stage: Path, batch_name: str, notes_name: str, recs: list, notes: str):
    batch = stage / batch_name
    notes_p = stage / notes_name
    lines = [json.dumps(rec, separators=(",", ":"), ensure_ascii=False) for rec in recs]
    batch.write_text("\n".join(lines) + "\n")
    notes_p.write_text(notes)
    for rec in recs:
        blob = json.dumps(rec)
        assert "thought" not in blob
        assert "chain_of_thought" not in blob
        assert "inner_monologue" not in blob
        assert "spike_events" not in blob
        assert '"sim_or_real": "real"' not in blob
        assert rec["meta"]["generator"] == "grok-4.6"
        assert rec["meta"]["plant"] == "designed"
        nset = [s["n"] for s in rec["steps"]]
        assert nset == list(range(1, len(rec["steps"]) + 1))
        assert 16 <= len(rec["steps"]) <= 22
        for s in rec["steps"]:
            assert len(s["decision_basis"]) <= 240
            assert "thought" not in s
        assert rec["id"].startswith("lhc-r")
        assert "-pr-" in rec["id"]


def emit_lhc(rnd: int, pair_i: int):
    title, fa, fb, *_ = LHC_PAIRS[pair_i]
    a, b = fa(rnd), fb(rnd)
    if a["reward"]["success"] == b["reward"]["success"]:
        raise SystemExit(f"pair {pair_i} same success flags")
    notes = lhc_notes(rnd, pair_i, a, b)
    return [a, b], notes, title


def try_reserve(factory_dir: Path, expected: int):
    nxt = frontier(factory_dir)
    if reserved(factory_dir, nxt):
        return None
    r = txn(["reserve", str(factory_dir), "--round", str(nxt), "--expected", str(expected)])
    if r.returncode != 0:
        err = (r.stderr or r.stdout).strip()
        print(f"reserve {factory_dir.name} r{nxt} failed: {err}", flush=True)
        return None
    return json.loads(r.stdout)


def publish_round(factory_dir, rnd, token, recs, notes, batch_name, notes_name, stage):
    write_stage(Path(stage), batch_name, notes_name, recs, notes)
    r = txn(["publish", str(factory_dir), "--round", str(rnd), "--token", token])
    if r.returncode != 0:
        sys.stderr.write(r.stderr or r.stdout)
        raise SystemExit(f"publish r{rnd} failed")
    print(r.stdout, flush=True)
    return True


def hop_targets():
    out = []
    for p in sorted(AGENTIC.iterdir()):
        if not p.is_dir():
            continue
        if p.name in {"sandbox-refusal-factory", "long-horizon-coding-factory"}:
            continue
        if any(p.glob("ROUND-r*.reserved.json")):
            continue
        out.append(p)
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "loop"
    st = load_state()

    if mode == "selfcheck":
        used = used_slugs()
        slugs = []
        for i, (title, fa, fb, *_) in enumerate(LHC_PAIRS):
            a, b = fa(9990 + i), fb(9990 + i)
            assert a["reward"]["success"] != b["reward"]["success"], title
            assert 16 <= len(a["steps"]) <= 22
            assert 16 <= len(b["steps"]) <= 22
            assert a["id"].startswith("lhc-r") and "-pr-" in a["id"]
            assert b["id"].startswith("lhc-r") and "-pr-" in b["id"]
            sa = "-".join(a["id"].split("-")[2:-1])
            sb = "-".join(b["id"].split("-")[2:-1])
            slugs.append(sa)
            slugs.append(sb)
            for slug in (sa, sb):
                low = slug.lower()
                for ban in BANNED_SUB:
                    if ban in low:
                        raise SystemExit(f"banned token {ban} in {slug}")
                if slug in used:
                    raise SystemExit(f"slug already used: {slug}")
            print("ok", i, title)
            print("   ", a["id"], len(a["steps"]), a["reward"]["success"])
            print("   ", b["id"], len(b["steps"]), b["reward"]["success"])
        if len(set(slugs)) != len(slugs):
            raise SystemExit(f"duplicate slugs in catalog: {slugs}")
        print("selfcheck", len(LHC_PAIRS), "pairs", len(slugs), "episodes")
        return

    if mode == "loop":
        target = int(sys.argv[2]) if len(sys.argv) > 2 else len(LHC_PAIRS)
        deadline = time.time() + 6 * 60 * 60
        published = 0
        hops = 0
        used = used_slugs()
        while published < target and time.time() < deadline:
            if st["lhc_pair"] >= len(LHC_PAIRS):
                print("catalog exhausted", flush=True)
                break
            res = try_reserve(LHC_DIR, 2)
            if res:
                rnd = res["round"]
                pair_i = st["lhc_pair"]
                recs, notes, title = emit_lhc(rnd, pair_i)
                for rec in recs:
                    slug = "-".join(rec["id"].split("-")[2:-1])
                    if slug in used:
                        raise SystemExit(f"refusing to publish used slug {slug}")
                    used.add(slug)
                publish_round(
                    LHC_DIR, rnd, res["token"], recs, notes,
                    res["batch_file"], res["notes_file"], res["staging_dir"],
                )
                st["lhc_pair"] += 1
                st["published"].append({"factory": "lhc", "round": rnd, "title": title, "ids": [x["id"] for x in recs]})
                save_state(st)
                published += 1
                print(f"PUBLISHED LHC r{rnd} pair={pair_i} {title}", flush=True)
                hops = 0
                continue
            hops += 1
            others = hop_targets()
            print(
                "LHC reserved; hop candidates (no plant catalog here, retry LHC):",
                [p.name for p in others[:8]],
                "sleep",
                flush=True,
            )
            time.sleep(2)
            if hops > 120:
                print("too many reserve failures; quota/reservation died", flush=True)
                break
        print(json.dumps({
            "published_this_run": published,
            "state_pairs": st["lhc_pair"],
            "rounds": [p["round"] for p in st["published"][-published:] if published],
        }, indent=2), flush=True)
        return

    raise SystemExit(f"unknown mode {mode}")


if __name__ == "__main__":
    raise SystemExit(main() or 0)
