#!/usr/bin/env python3
"""Wave 10: 180 unused CRP plants after stretch3 (r1590+).

NEW platforms (observability/chaos/wasm/schedulers/hypervisors/media/CAD),
not brunch/please/longhorn x4 clones, not id-reuse, not OAuth/OIDC/SAML.
"""
from __future__ import annotations

import os
from pathlib import Path

MILL = Path(__file__).with_name("crp-mill-r995.py")

FAMS = [
    ("signoz", "SigNoz stretch4", "trace", "go", "go"),
    ("uptrace", "Uptrace stretch4", "span", "go", "go"),
    ("qryn", "qryn stretch4", "stream", "js", "js"),
    ("phlare", "Phlare stretch4", "profile", "go", "go"),
    ("parca", "Parca stretch4", "pprof", "go", "go"),
    ("chaosmesh", "Chaos Mesh stretch4", "experiment", "go", "go"),
    ("litmuschaos", "Litmus stretch4", "chaos", "go", "go"),
    ("vegeta", "Vegeta stretch4", "attack", "go", "go"),
    ("ghz", "ghz stretch4", "call", "go", "go"),
    ("fortio", "Fortio stretch4", "load", "go", "go"),
    ("locust", "Locust stretch4", "swarm", "py", "py"),
    ("gatling", "Gatling stretch4", "scenario", "scala", "scala"),
    ("artillery", "Artillery stretch4", "scenario", "ts", "ts"),
    ("karpenter", "Karpenter stretch4", "nodepool", "go", "go"),
    ("descheduler", "Descheduler stretch4", "eviction", "go", "go"),
    ("volcano", "Volcano stretch4", "queue", "go", "go"),
    ("kueue", "Kueue stretch4", "workload", "go", "go"),
    ("tetragon", "Tetragon stretch4", "probe", "go", "go"),
    ("falcosidekick", "Falcosidekick stretch4", "output", "go", "go"),
    ("wasmcloud", "wasmCloud stretch4", "actor", "go", "go"),
    ("wasmtime", "Wasmtime stretch4", "module", "rs", "rs"),
    ("wasmer", "Wasmer stretch4", "instance", "rs", "rs"),
    ("wazero", "wazero stretch4", "module", "go", "go"),
    ("youki", "youki stretch4", "container", "rs", "rs"),
    ("crun", "crun stretch4", "runtime", "c", "c"),
    ("cloudhypervisor", "Cloud Hypervisor stretch4", "vm", "rs", "rs"),
    ("incus", "Incus stretch4", "instance", "go", "go"),
    ("harvester", "Harvester stretch4", "vm", "go", "go"),
    ("talos", "Talos stretch4", "machine", "go", "go"),
    ("bottlerocket", "Bottlerocket stretch4", "host", "rs", "rs"),
    ("wolfi", "Wolfi stretch4", "package", "yaml", "yaml"),
    ("kaniko", "Kaniko stretch4", "snapshot", "go", "go"),
    ("nydus", "Nydus stretch4", "layer", "rs", "rs"),
    ("stargz", "stargz stretch4", "toc", "go", "go"),
    ("composefs", "composefs stretch4", "mount", "c", "c"),
    ("bootc", "bootc stretch4", "image", "rs", "rs"),
    ("pixie", "Pixie stretch4", "probe", "go", "go"),
    ("odigos", "Odigos stretch4", "dest", "go", "go"),
    ("promtail", "Promtail stretch4", "target", "go", "go"),
    ("alloy", "Grafana Alloy stretch4", "pipeline", "go", "go"),
    ("alertmanager", "Alertmanager stretch4", "route", "go", "go"),
    ("surrealdb", "SurrealDB stretch4", "table", "rs", "rs"),
    ("edgedb", "EdgeDB stretch4", "type", "py", "py"),
    ("goatcounter", "GoatCounter stretch4", "hit", "go", "go"),
    ("fathom", "Fathom stretch4", "site", "go", "go"),
    ("bugsnag", "Bugsnag stretch4", "event", "rb", "rb"),
    ("duplicacy", "Duplicacy stretch4", "snapshot", "go", "go"),
    ("rclone", "rclone stretch4", "remote", "go", "go"),
    ("koel", "Koel stretch4", "track", "php", "php"),
    ("airsonic", "Airsonic stretch4", "library", "java", "java"),
    ("kodi", "Kodi stretch4", "addon", "py", "py"),
    ("drawio", "draw.io stretch4", "diagram", "js", "js"),
    ("inkscape", "Inkscape stretch4", "document", "cpp", "cpp"),
    ("blender", "Blender stretch4", "scene", "c", "c"),
    ("openscad", "OpenSCAD stretch4", "module", "cpp", "cpp"),
    ("tasmota", "Tasmota stretch4", "device", "c", "c"),
    ("zwavejs", "Z-Wave JS stretch4", "node", "ts", "ts"),
    ("flood", "Flood stretch4", "torrent", "js", "js"),
    ("gerrit", "Gerrit stretch4", "change", "java", "java"),
    ("soketi", "Soketi stretch4", "channel", "ts", "ts"),
]

BUGS = [
    ("name-case", "feat: name", "name", "unique", "nm", "nm",
     "{prod} leftover {noun} name unique is case-sensitive so Orders and orders both insert and both bill",
     "name leftover", "{noun} name uniqueness must be case-insensitive",
     "store lower(name) uniquely", "name|lower|unique"),
    ("unique-app", "feat: unique", "unique", "check", "uq", "uq",
     "{prod} leftover {noun} uniqueness is application-side so two leftover creates insert two billed rows",
     "unique leftover", "one workspace plus {noun} key must insert once",
     "UNIQUE(workspace_id, key) and catch the conflict", "UNIQUE|key|{noun}"),
    ("qty-rmw", "feat: qty", "qty", "stock", "qty", "qty",
     "{prod} leftover {noun} qty is read-modify-write so two leftover automations oversell a billed SKU",
     "qty leftover", "qty decrement must be conditional on remaining stock",
     "UPDATE {noun}s SET qty=qty-? WHERE id=? AND qty>=?", "qty|UPDATE|qty>="),
    ("path-toctou", "feat: export", "export", "path", "ex", "tc",
     "{prod} leftover {noun} export path is checked then opened so a symlink swap billed-reads another tenant file",
     "path leftover", "open must not follow a swapped symlink",
     "open dest with O_NOFOLLOW|O_EXCL in the workspace dir", "O_NOFOLLOW|{noun}|path"),
    ("eval-xss", "feat: preview", "preview", "html", "xss", "xs",
     "{prod} leftover {noun} preview interpolates leftover HTML so a note XSS steals the billed session",
     "preview leftover", "user notes must not execute as HTML in the {noun} preview",
     "textContent or a sanitizer; never innerHTML = note", "innerHTML|sanitize|{noun}"),
    ("tz-naive", "feat: tz", "time", "tz", "tz", "tz",
     "{prod} leftover {noun} timestamps store naive local so a DST fold double-books a billed slot",
     "tz leftover", "{noun} timestamps must be timestamptz UTC",
     "store timestamptz UTC; never unique on naive local wall time in a fold", "timestamptz|fold|{noun}"),
    ("timeout-failopen", "feat: timeout", "timeout", "guard", "to", "to",
     "{prod} leftover {noun} timeout fail-opens so a billed Charge.create still runs after the paid action should skip",
     "timeout leftover", "timeout must fail closed to the default (skip charge)",
     "error/timeout -> do not run the paid {noun} action", "timeout|fail closed|{noun}"),
    ("cache-stale", "feat: cache", "cache", "etag", "ch", "ch",
     "{prod} leftover {noun} cache is served after a paid disable so clients keep charging",
     "cache leftover", "a disabled {noun} must not remain true in a stale cache",
     "etag/version on the {noun}; purge after disable", "cache|etag|disable"),
    ("ifmatch-skip", "feat: version", "version", "ifmatch", "ver", "im",
     "{prod} leftover {noun} update skips If-Match so two leftover editors both save and billed versions fork",
     "version leftover", "updates must fail on stale If-Match / version",
     "require If-Match and unique({noun}_id, version)", "If-Match|version|{noun}"),
    ("retry-charge", "feat: retry", "retry", "charge", "ret", "rt",
     "{prod} leftover {noun} retry Charge.create after a successful step so a billed invoice posts twice",
     "retry leftover", "one run plus {noun} step must charge once",
     "unique(run_id, step) receipts; skip if billed", "retry|run_id|unique"),
    ("idempotency-miss", "feat: idem", "idem", "key", "idemp", "id",
     "{prod} leftover {noun} has no unique(idempotency_key) so a 504 retry Charge.create twice",
     "idem leftover", "one idempotency_key must run once",
     "unique(idempotency_key) and return the existing result", "idempotency_key|unique|{noun}"),
    ("webhook-replay", "feat: webhook", "webhook", "hook", "wh", "wh",
     "{prod} leftover {noun} webhook has no unique(delivery_id) so a retry Charge.create twice",
     "webhook leftover", "one delivery must charge once",
     "unique(delivery_id) and ignore duplicate webhooks", "delivery_id|unique|webhook"),
    ("slug-race", "feat: slug", "slug", "name", "sl", "sl",
     "{prod} leftover {noun} slug uniqueness is application-side so two leftover creates share a slug",
     "slug leftover", "one workspace plus slug must insert once",
     "UNIQUE(workspace_id, slug) and catch the conflict", "slug|UNIQUE|workspace_id"),
    ("seq-skip", "feat: seq", "seq", "number", "sq", "sq",
     "{prod} leftover {noun} sequence skips numbers so a gap replay bills a row twice",
     "seq leftover", "already-applied sequence numbers must not apply again",
     "persist last sequence uniquely and refuse seq <= last", "sequence|{noun}|last"),
    ("overwrite", "feat: write", "write", "dest", "ow", "ow",
     "{prod} leftover {noun} write overwrites dest so billed artifacts swap",
     "write leftover", "an existing dest must not be overwritten by another run",
     "refuse replace unless dest is the same run; unique(path)", "overwrite|unique|{noun}"),
    ("overlap", "feat: lock", "lock", "run", "ov", "ov",
     "{prod} leftover {noun} runs overlap so two leftover jobs both Charge.create",
     "overlap leftover", "one {noun} plus window must run once",
     "advisory lock / unique(run_window) and skip if held", "lock|{noun}|unique"),
    ("searchpath", "feat: role", "acl", "role", "sp", "sp",
     "{prod} leftover {noun} role has no search_path so a tenant function resolves public.charge() and bills the wrong org",
     "role leftover", "the role must not execute public.charge for another tenant",
     "SET search_path plus a schema-qualified function name", "search_path|role|charge"),
]

assert len(FAMS) == 60
plants: list[tuple] = []
for i, (pref, prod, noun, ext, text) in enumerate(FAMS):
    for j in range(3):
        bug = BUGS[(i + j * 6) % len(BUGS)]
        slug = f"{pref}-{bug[0]}"
        plants.append(
            (
                slug, bug[1], f"{bug[2]}.{ext}", f"{bug[3]}.{ext}", f"{bug[4]}_test.{text}",
                10 + ((i * 3 + j) % 23), bug[5],
                bug[6].format(prod=prod, noun=noun), bug[7],
                bug[8].format(prod=prod, noun=noun), bug[9].format(prod=prod, noun=noun),
                bug[10].format(prod=prod, noun=noun), f"{pref} leftover plant",
            )
        )
for i in range(len(plants)):
    nxt = plants[(i + 1) % len(plants)]
    row = list(plants[i]); row[-1] = f"{nxt[0]} plant"; plants[i] = tuple(row)

assert len(plants) == 180
assert len({p[0] for p in plants}) == 180
assert all("id-reuse" not in p[0] and "uid-reuse" not in p[0] and "uuid-reuse" not in p[0] for p in plants)


def fmt(row: tuple) -> str:
    slug, title, core, boot, test, line, nit, defect, reach, missing, fix, needles, notfam = row
    return (
        f'    ("{slug}", "{title}", "{core}", "{boot}", "{test}", {line}, "{nit}",\n'
        f'     "{defect}",\n'
        f'     "{reach}",\n'
        f'     "{missing}",\n'
        f'     "{fix}",\n'
        f'     "{needles}", "{notfam}"),\n'
    )


def main() -> None:
    text = MILL.read_text()
    existing = [p[0] for p in plants if f'("{p[0]}"' in text]
    if existing:
        raise SystemExit(f"slug collision in mill: {existing[:8]}")
    needle = "]\n\n\nassert len(_RAW) % 3 == 0, len(_RAW)"
    if needle not in text:
        needle = "]\n\nassert len(_RAW) % 3 == 0, len(_RAW)"
    if needle not in text:
        raise SystemExit("cannot find _RAW close")
    block = "    # --- r1590 stretch4 / observability / chaos / wasm / hypervisors ---\n"
    block += "".join(fmt(p) for p in plants)
    text = text.replace(needle, block + needle, 1)
    tmp = MILL.with_suffix(".py.tmp")
    tmp.write_text(text)
    os.replace(tmp, MILL)
    print(f"appended {len(plants)} plants atomically")


if __name__ == "__main__":
    main()
