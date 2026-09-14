#!/usr/bin/env python3
"""Wave 7: 180 unused CRP plants after iac/rpc stretch."""
from __future__ import annotations

import os
from pathlib import Path

MILL = Path(__file__).with_name("crp-mill-r995.py")

FAMS = [
    ("earthlyx", "Earthly extra", "target", "go", "go"),
    ("daggeriox", "Dagger extra", "pipeline", "go", "go"),
    ("nixpacksx", "Nixpacks extra", "plan", "rs", "rs"),
    ("skaffoldx", "Skaffold extra", "build", "go", "go"),
    ("tiltx", "Tilt extra", "resource", "go", "go"),
    ("gardeniox", "Garden extra", "module", "ts", "ts"),
    ("jsonnetx", "Jsonnet extra", "object", "go", "go"),
    ("dhallx", "Dhall extra", "expression", "hs", "hs"),
    ("bufbuildx", "Buf extra", "module", "go", "go"),
    ("twirpx", "Twirp extra", "service", "go", "go"),
    ("mageaix", "Mage extra", "block", "py", "py"),
    ("kedrox", "Kedro extra", "node", "py", "py"),
    ("metaflowx", "Metaflow extra", "step", "py", "py"),
    ("zenmlx", "ZenML extra", "step", "py", "py"),
    ("materializex", "Materialize extra", "source", "rs", "rs"),
    ("redpandax", "Redpanda extra", "partition", "cc", "cc"),
    ("kedax", "KEDA extra", "trigger", "go", "go"),
    ("sonarqubex", "SonarQube extra", "qualitygate", "java", "java"),
    ("dependencytrackx", "Dependency-Track extra", "project", "java", "java"),
    ("anchorex", "Anchore extra", "policy", "py", "py"),
    ("clairx", "Clair extra", "indexer", "go", "go"),
    ("consulconnectx", "Consul Connect extra", "sidecar", "go", "go"),
    ("saltstackx", "Salt extra", "pillar", "py", "py"),
    ("chefinfrax", "Chef extra", "cookbook", "rb", "rb"),
    ("puppetx", "Puppet extra", "module", "rb", "rb"),
    ("cfenginex", "CFEngine extra", "bundle", "c", "c"),
    ("nixosx", "NixOS extra", "flake", "nix", "nix"),
    ("guixx", "Guix extra", "channel", "scm", "scm"),
    ("spackx", "Spack extra", "repo", "py", "py"),
    ("easybuildx", "EasyBuild extra", "module", "py", "py"),
    ("mambax", "Mamba extra", "channel", "cpp", "cpp"),
    ("pixix", "Pixi extra", "lock", "rs", "rs"),
    ("uvpkgx", "uv extra", "index", "rs", "rs"),
    ("ryex", "Rye extra", "tool", "rs", "rs"),
    ("flitx", "Flit extra", "sdist", "py", "py"),
    ("maturinx", "Maturin extra", "crate", "rs", "rs"),
    ("cibuildwheelx", "cibuildwheel extra", "cibw", "py", "py"),
    ("scikitbuildx", "scikit-build extra", "cmake", "py", "py"),
    ("buck2x", "Buck2 extra", "action", "rs", "rs"),
    ("pantsbuildx", "Pants extra", "goal", "py", "py"),
    ("millbuildx", "Mill extra", "task", "scala", "scala"),
    ("leiningenx", "Leiningen extra", "profile", "clj", "clj"),
    ("bootcljx", "Boot extra", "pod", "clj", "clj"),
    ("shadowcljsx", "shadow-cljs extra", "release", "cljs", "cljs"),
    ("snowpackx", "Snowpack extra", "optimize", "js", "js"),
    ("broccolix", "Broccoli extra", "plugin", "js", "js"),
    ("brunchx", "Brunch extra", "plugin", "js", "js"),
    ("pleasex", "Please extra", "label", "go", "go"),
    ("longhornx", "Longhorn extra", "backup", "go", "go"),
    ("openebsx", "OpenEBS extra", "replica", "go", "go"),
    ("cubefsx", "CubeFS extra", "inode", "go", "go"),
    ("juicefsx", "JuiceFS extra", "meta", "go", "go"),
    ("knativex", "Knative extra", "service", "go", "go"),
    ("certmanagerx", "cert-manager extra", "issuer", "go", "go"),
    ("beamdatax", "Beam extra", "ptransform", "java", "java"),
    ("flinksqlx", "Flink SQL extra", "checkpoint", "java", "java"),
    ("sparksqlx", "Spark SQL extra", "catalog", "scala", "scala"),
    ("natsjetstreamx", "NATS extra", "consumer", "go", "go"),
    ("langfusex", "Langfuse extra", "score", "ts", "ts"),
    ("umamiappx", "Umami extra", "event", "ts", "ts"),
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
        bug = BUGS[(i + j * 2) % len(BUGS)]
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
    block = "    # --- r1411 extra-stretch / serving / object-store / fediverse / sbom ---\n"
    block += "".join(fmt(p) for p in plants)
    text = text.replace(needle, block + needle, 1)
    tmp = MILL.with_suffix(".py.tmp")
    tmp.write_text(text)
    os.replace(tmp, MILL)
    print(f"appended {len(plants)} plants atomically")


if __name__ == "__main__":
    main()
