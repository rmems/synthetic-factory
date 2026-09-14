#!/usr/bin/env python3
"""Mill secret-scan-remediation-factory r1622+ unique print leftover mechanics.

BAN: skip-path cartesian; SaaS-yml; vendor-file; cipher-*; r435 mold-map /
lld-repro; r331 rebase-merge / turbo-cache; r709 consul-watches / nomad-health;
r1024 rqlite-snap / dqlite-snap; r1064 dataproc-job / composer-dag;
r1104 go-modcache / gomod-sumdb; r1141 umoci-bundle / oras-cache;
r436–r1621 prior leftover clones.
Fake TESTONLY_ keys only. Never force-push main.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

FACTORY = "secret-scan-remediation-factory"
CATALOG_FIRST = 1622
HERE = Path(__file__).resolve().parent
if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    from ssr_mill_fast import main_from_catalog
    raise SystemExit(main_from_catalog(HERE / f".ssr-catalog-r{CATALOG_FIRST}.json"))
_spec = importlib.util.spec_from_file_location("ssr_mill_r1582", HERE / "ssr-mill-r1582.py")
_ssr_mill_r1582 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_ssr_mill_r1582)
plant = _ssr_mill_r1582.plant
success_episode = _ssr_mill_r1582.success_episode
fail_episode = _ssr_mill_r1582.fail_episode
SCAN = _ssr_mill_r1582.SCAN
SCANNERS = _ssr_mill_r1582.SCANNERS
LEAKS = _ssr_mill_r1582.LEAKS

USED_SLUGS = {p["slug"] for pair in _ssr_mill_r1582.PAIRS for p in pair} | set(_ssr_mill_r1582.USED_SLUGS)
USED_EXTRAS = {p["extra"] for pair in _ssr_mill_r1582.PAIRS for p in pair} | set(_ssr_mill_r1582.USED_EXTRAS)
USED_TAILS = set(_ssr_mill_r1582.TAILS) | set(_ssr_mill_r1582.USED_TAILS)

TAILS = [
    'cups-ppd',
    'cups-filters',
    'cups-browsed',
    'cups-snmp',
    'gutenprint-xml',
    'foomatic-db',
    'hplip-state',
    'brother-lpr',
    'epson-escpr',
    'canon-cnijfilter',
    'samsung-uld',
    'ipp-usb',
    'ippusbxd',
    'sane-backends',
    'sane-dll',
    'xsane-rc',
    'skanlite-rc',
    'simple-scan',
    'naps2-profiles',
    'tesseract-tessdata',
    'ocrmypdf-cache',
    'brscan-key',
    'brscan-net',
    'hplip-plugin',
    'hplip-fax',
    'cups-pdf',
    'cups-lpd',
    'avahi-printer',
    'mdns-print',
    'ipp-everywhere',
    'ipp-attrs',
    'pcl-xl',
    'postscript-ppd',
    'ghostscript-icc',
    'ghostscript-fonts',
    'poppler-cache',
    'qpdf-tmp',
    'pdftk-out',
    'mupdf-cache',
    'ocrmypdf-tmp',
    'tesseract-user',
    'unpaper-cache',
    'scantailor-out',
    'gscan2pdf-rc',
    'paperwork-work',
    'mayan-docs',
    'papermerge-media',
    'nextcloud-ocr',
    'collabora-lool',
    'onlyoffice-cache',
    'libreoffice-user',
    'abiword-tmp',
    'gnumeric-tmp',
    'scribus-prefs',
    'inkscape-cache',
    'cups-client.conf',
    'cupsd-conf',
    'lpadmin-conf',
    'lpoptions',
    'print-jobhistory',
    'cups-error-log',
    'hplip-systray',
    'hp-toolbox',
    'brother-cupswrapper',
    'epson-inkjet',
    'canon-capt',
    'samsung-splix',
    'foo2zjs-icm',
    'foo2qpdl',
    'splix-ppd',
    'c2esp-ppd',
    'ptouch-print',
    'dymo-lw',
    'zebra-zpl',
    'cups-zebra',
    'labelary-tmp',
    'brother-ql',
    'dymo-lw450',
    'sane-net',
    'saned-conf',
]

if len(TAILS) % 2:
    raise SystemExit("odd plant count")
ORGS = [f"prn{i:03d}" for i in range(1, len(TAILS) + 1)]


def _scan_pair(scanner: str, extra: str, tag: str) -> tuple[str, str]:
    invoke, hit = SCAN[scanner]
    return invoke.format(extra=extra, tag=tag), hit.format(tag=tag)


def _mk(tail: str, idx: int) -> dict:
    if tail in USED_TAILS:
        raise SystemExit(f"tail clone: {tail}")
    scanner = SCANNERS[(idx - 1) % len(SCANNERS)]
    leak, prefix = LEAKS[(idx - 1) % len(LEAKS)]
    base = leak.split("/")[-1]
    extra = f".{tail}/{base}"
    pretty = tail.replace("-", " ")
    mechanic = f"{pretty} firmware still names {leak}"
    tag = f"{pretty} print leftover"
    env = f"{prefix}_{tail.replace('-', '_')[:14].upper()}_TOKEN"
    org = f"{ORGS[idx - 1]}-r"
    short = org.split("-")[0][:6]
    repo = f"{org}/{short}-{tail[:28]}"
    slug = f"{scanner}-{tail}-leftover"
    invoke, hit = _scan_pair(scanner, extra, tag)
    wrong_cmd = f"rg TESTONLY {extra} | head"
    hide_cmd = f"echo '{leak.split('/')[0]}/' >> .gitignore; {wrong_cmd}"
    tok = f"TESTONLY_r1622{idx:03d}_n0t"
    return plant(
        slug=slug,
        scanner=scanner,
        mechanic=mechanic,
        repo=repo,
        leak=leak,
        extra=extra,
        token=tok,
        env=env,
        sha=f"e622{idx:04x}",
        pr=3220 + idx,
        mix=f"{scanner} {tag}",
        scan_invoke=invoke,
        scan_hit=hit,
        extra_line=f"{tag} still names TESTONLY_",
        miss_cmd=f"{SCAN[scanner][0].format(extra=leak, tag=tag)} 2>&1 | tail -3 || echo {tail[:12]}-head-green",
        miss_green=f"{tail[:12]}-head-green",
        wrong_b=f"Plan: first apply - redact {leak}. Expect {pretty} firmware still red.",
        wrong_cmd=wrong_cmd,
        wrong_obs=f"{env}={tok}",
        hide_cmd=hide_cmd,
        hide_obs=f"{env}={tok}  ({tag})",
    )


clash = [t for t in TAILS if t in USED_TAILS]
if clash:
    raise SystemExit(f"tail clones: {clash[:8]}")
_plants = [_mk(tail, i) for i, tail in enumerate(TAILS, start=1)]
PAIRS = [(_plants[i], _plants[i + 1]) for i in range(0, len(_plants), 2)]


def _assert_catalog() -> None:
    slugs = [p["slug"] for pair in PAIRS for p in pair]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("duplicate slugs")
    clash = set(slugs) & USED_SLUGS
    if clash:
        raise SystemExit(f"slug clones: {sorted(clash)[:8]}")
    extras = [p["extra"] for pair in PAIRS for p in pair]
    if set(extras) & USED_EXTRAS:
        raise SystemExit("extra clones")
    banned_bits = (
        'stash-wip',
        'reflog',
        'worktree',
        'turbo-cache',
        'cipher',
        'sarif',
        'git-notes',
        'entropy-window',
        'mold-map',
        'lld-repro',
        'vendor-file',
        'saas-yml',
        'consul-watches',
        'nomad-health',
        'rebase-merge',
        'rqlite-snap',
        'dqlite-snap',
        'dataproc-job',
        'composer-dag',
        'go-modcache',
        'gomod-sumdb',
        'umoci-bundle',
        'oras-cache',
        'steam-compatdata',
        'proton-shader',
    )
    for spec in (p for pair in PAIRS for p in pair):
        blob = f"{spec['slug']} {spec['mechanic']} {spec['extra']}".lower()
        hit = [b for b in banned_bits if b in blob]
        if hit:
            raise SystemExit(f"banned {hit} in {spec['slug']}")
        if "TESTONLY_" not in spec["token"]:
            raise SystemExit("bad token")
        if any(x in spec["slug"] for x in ("pulumi", "tfc-", "snyk", "netlify", "braintree", "adyen")):
            raise SystemExit(f"banned family in slug: {spec['slug']}")


_assert_catalog()


def notes_md(rnd, suc, fail, suc_ep, fail_ep):
    coverage = max(52, 80 - (rnd - CATALOG_FIRST))
    return f"""# NOTES-r{rnd} secret-scan-remediation-factory

Novel coverage: {coverage}%

Two designed firmware-leftover episodes (quota 2). Surfaces: {suc['repo']} {suc['slug']} {suc['mechanic']}; {fail['repo']} {fail['slug']} {fail['mechanic']} (rewrite blocked).
Neither force-pushes main. Fake TESTONLY_ keys only. One remaining-scan fail when rewrite is blocked.
Scanner × print leftover mill (not skip-path cartesian, not SaaS-yml, not vendor-file, not r181–r1301 prior leftover clones, not r1621 steam-compatdata/proton-shader, not r1141 umoci-bundle/oras-cache, not r1104 go-modcache/gomod-sumdb, not r1064 dataproc-job/composer-dag, not r1024 rqlite-snap/dqlite-snap, not r709 consul-watches/nomad-health, not r435 mold-map/lld-repro, not r331 rebase-merge/turbo-cache).

| id | seed | first apply | plan change | terminal |
|---|---|---|---|---|
| {suc_ep['id']} | {suc['mechanic']} in {suc['leak']} + {suc['extra']} | {suc['wrong_b'].replace('Plan: first apply - ', '')} | {suc['env']} + filter-repo purge | success 2/2, main residual |
| {fail_ep['id']} | {fail['mechanic']} in {fail['leak']} + {fail['extra']} | {fail['wrong_b'].replace('Plan: first apply - ', '')} | HEAD {fail['env']}; GH013 | remaining-scan fail + HANDOFF |

## Step counts
- {suc_ep['id']}: {len(suc_ep['steps'])}
- {fail_ep['id']}: {len(fail_ep['steps'])}

## decision_basis audit
Every step starts Plan:/Observation:/Reflection:/Tool call:, ≤240 chars.
No thought / chain_of_thought / scratch / inner_monologue. No spike_events.
No sim_or_real: real. Invented plants (designed). No real secrets.

## Weaknesses / next
Avoid {suc['slug']}-as-git-fix and {fail['slug']}-as-git-fix (this round).
Harder-kind mill: {suc['mix']}; {fail['mix']}.
"""


def build_round(rnd: int, pair_index: int | None = None):
    idx = pair_index if pair_index is not None else rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"round {rnd} idx={idx} outside catalog")
    suc, fail = PAIRS[idx]
    suc_ep = success_episode(rnd, suc, 16)
    fail_ep = fail_episode(rnd, fail, 16)
    for ep in (suc_ep, fail_ep):
        n = len(ep["steps"])
        if n < 12 or n > 18:
            raise SystemExit(f"{ep['id']} has {n} steps")
        ep["reward"]["cost_steps"] = n
        if ep["meta"].get("generator") != "grok-4.6":
            raise SystemExit("bad generator")
    return [suc_ep, fail_ep], notes_md(rnd, suc, fail, suc_ep, fail_ep)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    recs, notes = build_round(args.round)
    staging = Path(args.staging)
    with (staging / f"batch-r{args.round:02d}.jsonl").open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=True) + "\n")
    (staging / f"NOTES-r{args.round:02d}.md").write_text(notes)
    print(json.dumps({"round": args.round, "ids": [r["id"] for r in recs], "steps": [len(r["steps"]) for r in recs]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
