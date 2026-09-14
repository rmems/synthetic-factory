#!/usr/bin/env python3
"""Append 180 unused CRP plants (60 triples) to crp-mill-r995.py and restart-ready."""
from __future__ import annotations

import re
from pathlib import Path

MILL = Path(__file__).with_name("crp-mill-r995.py")

# (prefix, Product, noun, file_ext, test_ext)
FAMS = [
    ("seatable", "SeaTable", "base", "ts", "ts"),
    ("teable", "Teable", "space", "ts", "ts"),
    ("grist", "Grist", "doc", "ts", "ts"),
    ("apitable", "APITable", "datasheet", "ts", "ts"),
    ("rowy", "Rowy", "table", "ts", "ts"),
    ("marimo", "Marimo", "notebook", "py", "py"),
    ("quarto", "Quarto", "qmd", "qmd", "py"),
    ("observablehq", "Observable", "notebook", "js", "js"),
    ("hexnotebook", "Hex", "project", "py", "py"),
    ("deepnote", "Deepnote", "project", "py", "py"),
    ("countco", "Count", "canvas", "ts", "ts"),
    ("apacheatlas", "Apache Atlas", "entity", "java", "java"),
    ("hightouch", "Hightouch", "sync", "ts", "ts"),
    ("censushq", "Census", "sync", "ts", "ts"),
    ("grouparoo", "Grouparoo", "schedule", "ts", "ts"),
    ("rudderstack", "RudderStack", "source", "js", "js"),
    ("segmentio", "Segment", "source", "js", "js"),
    ("quilt", "Quilt", "package", "py", "py"),
    ("deltaio", "Delta Lake", "table", "scala", "scala"),
    ("apachehudi", "Apache Hudi", "table", "java", "java"),
    ("apacheiceberg", "Apache Iceberg", "table", "java", "java"),
    ("dremio", "Dremio", "reflection", "java", "java"),
    ("impala", "Impala", "query", "cc", "cc"),
    ("drill", "Apache Drill", "query", "java", "java"),
    ("starburst", "Starburst", "catalog", "java", "java"),
    ("konggateway", "Kong", "route", "lua", "lua"),
    ("tyk", "Tyk", "api", "go", "go"),
    ("apisix", "Apache APISIX", "route", "lua", "lua"),
    ("krakend", "KrakenD", "endpoint", "go", "go"),
    ("gravitee", "Gravitee", "api", "java", "java"),
    ("penpot", "Penpot", "file", "cljs", "cljs"),
    ("excalidraw", "Excalidraw", "scene", "ts", "ts"),
    ("tldraw", "tldraw", "document", "ts", "ts"),
    ("postalapp", "Postal", "message", "rb", "rb"),
    ("mailcow", "mailcow", "mailbox", "php", "php"),
    ("mailu", "Mailu", "mailbox", "py", "py"),
    ("weblate", "Weblate", "component", "py", "py"),
    ("tolgee", "Tolgee", "key", "kt", "kt"),
    ("pontoon", "Pontoon", "entity", "py", "py"),
    ("traduora", "Traduora", "term", "ts", "ts"),
    ("docuseal", "DocuSeal", "submission", "rb", "rb"),
    ("documenso", "Documenso", "document", "ts", "ts"),
    ("paperlessngx", "Paperless-ngx", "document", "py", "py"),
    ("moodle", "Moodle", "course", "php", "php"),
    ("openedx", "Open edX", "course", "py", "py"),
    ("tutorlms", "Tutor LMS", "course", "php", "php"),
    ("chamilo", "Chamilo", "course", "php", "php"),
    ("ilias", "ILIAS", "object", "php", "php"),
    ("owncast", "Owncast", "stream", "go", "go"),
    ("mediamtx", "MediaMTX", "path", "go", "go"),
    ("ovenmedia", "OvenMediaEngine", "app", "cpp", "cpp"),
    ("planehq", "Plane", "issue", "py", "py"),
    ("vikunja", "Vikunja", "task", "go", "go"),
    ("inventree", "InvenTree", "part", "py", "py"),
    ("partkeepr", "PartKeepr", "part", "php", "php"),
    ("glpi", "GLPI", "ticket", "php", "php"),
    ("freescout", "FreeScout", "conversation", "php", "php"),
    ("netdata", "Netdata", "chart", "c", "c"),
    ("zabbix", "Zabbix", "item", "c", "c"),
    ("icinga", "Icinga", "check", "cpp", "cpp"),
]

BUGS = [
    # slug, title, core, boot, teststem, nit, defect, reach, missing, fix, needles
    (
        "name-case",
        "feat: name",
        "name",
        "unique",
        "nm",
        "nm",
        "{prod} leftover {noun} name unique is case-sensitive so Orders and orders both insert and both bill",
        "name leftover",
        "{noun} name uniqueness must be case-insensitive",
        "store lower(name) uniquely",
        "name|lower|unique",
    ),
    (
        "unique-app",
        "feat: unique",
        "unique",
        "check",
        "uq",
        "uq",
        "{prod} leftover {noun} uniqueness is application-side so two leftover creates insert two billed rows",
        "unique leftover",
        "one workspace plus {noun} key must insert once",
        "UNIQUE(workspace_id, key) and catch the conflict",
        "UNIQUE|key|{noun}",
    ),
    (
        "qty-rmw",
        "feat: qty",
        "qty",
        "stock",
        "qty",
        "qty",
        "{prod} leftover {noun} qty is read-modify-write so two leftover automations oversell a billed SKU",
        "qty leftover",
        "qty decrement must be conditional on remaining stock",
        "UPDATE {noun}s SET qty=qty-? WHERE id=? AND qty>=?",
        "qty|UPDATE|qty>=",
    ),
    (
        "path-toctou",
        "feat: export",
        "export",
        "path",
        "ex",
        "tc",
        "{prod} leftover {noun} export path is checked then opened so a symlink swap billed-reads another tenant file",
        "path leftover",
        "open must not follow a swapped symlink",
        "open dest with O_NOFOLLOW|O_EXCL in the workspace dir",
        "O_NOFOLLOW|{noun}|path",
    ),
    (
        "eval-xss",
        "feat: preview",
        "preview",
        "html",
        "xss",
        "xs",
        "{prod} leftover {noun} preview interpolates leftover HTML so a note XSS steals the billed session",
        "preview leftover",
        "user notes must not execute as HTML in the {noun} preview",
        "textContent or a sanitizer; never innerHTML = note",
        "innerHTML|sanitize|{noun}",
    ),
    (
        "tz-naive",
        "feat: tz",
        "time",
        "tz",
        "tz",
        "tz",
        "{prod} leftover {noun} timestamps store naive local so a DST fold double-books a billed slot",
        "tz leftover",
        "{noun} timestamps must be timestamptz UTC",
        "store timestamptz UTC; never unique on naive local wall time in a fold",
        "timestamptz|fold|{noun}",
    ),
    (
        "timeout-failopen",
        "feat: timeout",
        "timeout",
        "guard",
        "to",
        "to",
        "{prod} leftover {noun} timeout fail-opens so a billed Charge.create still runs after the paid action should skip",
        "timeout leftover",
        "timeout must fail closed to the default (skip charge)",
        "error/timeout -> do not run the paid {noun} action",
        "timeout|fail closed|{noun}",
    ),
    (
        "cache-stale",
        "feat: cache",
        "cache",
        "etag",
        "ch",
        "ch",
        "{prod} leftover {noun} cache is served after a paid disable so clients keep charging",
        "cache leftover",
        "a disabled {noun} must not remain true in a stale cache",
        "etag/version on the {noun}; purge after disable",
        "cache|etag|disable",
    ),
    (
        "ifmatch-skip",
        "feat: version",
        "version",
        "ifmatch",
        "ver",
        "im",
        "{prod} leftover {noun} update skips If-Match so two leftover editors both save and billed versions fork",
        "version leftover",
        "updates must fail on stale If-Match / version",
        "require If-Match and unique({noun}_id, version)",
        "If-Match|version|{noun}",
    ),
    (
        "retry-charge",
        "feat: retry",
        "retry",
        "charge",
        "ret",
        "rt",
        "{prod} leftover {noun} retry Charge.create after a successful step so a billed invoice posts twice",
        "retry leftover",
        "one run plus {noun} step must charge once",
        "unique(run_id, step) receipts; skip if billed",
        "retry|run_id|unique",
    ),
    (
        "idempotency-miss",
        "feat: idem",
        "idem",
        "key",
        "idemp",
        "id",
        "{prod} leftover {noun} has no unique(idempotency_key) so a 504 retry Charge.create twice",
        "idem leftover",
        "one idempotency_key must run once",
        "unique(idempotency_key) and return the existing result",
        "idempotency_key|unique|{noun}",
    ),
    (
        "webhook-replay",
        "feat: webhook",
        "webhook",
        "hook",
        "wh",
        "wh",
        "{prod} leftover {noun} webhook has no unique(delivery_id) so a retry Charge.create twice",
        "webhook leftover",
        "one delivery must charge once",
        "unique(delivery_id) and ignore duplicate webhooks",
        "delivery_id|unique|webhook",
    ),
    (
        "slug-race",
        "feat: slug",
        "slug",
        "name",
        "sl",
        "sl",
        "{prod} leftover {noun} slug uniqueness is application-side so two leftover creates share a slug",
        "slug leftover",
        "one workspace plus slug must insert once",
        "UNIQUE(workspace_id, slug) and catch the conflict",
        "slug|UNIQUE|workspace_id",
    ),
    (
        "seq-skip",
        "feat: seq",
        "seq",
        "number",
        "sq",
        "sq",
        "{prod} leftover {noun} sequence skips numbers so a gap replay bills a row twice",
        "seq leftover",
        "already-applied sequence numbers must not apply again",
        "persist last sequence uniquely and refuse seq <= last",
        "sequence|{noun}|last",
    ),
    (
        "overwrite",
        "feat: write",
        "write",
        "dest",
        "ow",
        "ow",
        "{prod} leftover {noun} write overwrites dest so billed artifacts swap",
        "write leftover",
        "an existing dest must not be overwritten by another run",
        "refuse replace unless dest is the same run; unique(path)",
        "overwrite|unique|{noun}",
    ),
    (
        "overlap",
        "feat: lock",
        "lock",
        "run",
        "ov",
        "ov",
        "{prod} leftover {noun} runs overlap so two leftover jobs both Charge.create",
        "overlap leftover",
        "one {noun} plus window must run once",
        "advisory lock / unique(run_window) and skip if held",
        "lock|{noun}|unique",
    ),
    (
        "searchpath",
        "feat: role",
        "acl",
        "role",
        "sp",
        "sp",
        "{prod} leftover {noun} role has no search_path so a tenant function resolves public.charge() and bills the wrong org",
        "role leftover",
        "the role must not execute public.charge for another tenant",
        "SET search_path plus a schema-qualified function name",
        "search_path|role|charge",
    ),
]

assert len(FAMS) == 60
# 3 rotating bugs per family so we do not cartesian-clone the same triple
plants: list[tuple] = []
for i, (pref, prod, noun, ext, text) in enumerate(FAMS):
    for j in range(3):
        bug = BUGS[(i + j * 5) % len(BUGS)]
        slug = f"{pref}-{bug[0]}"
        title = bug[1]
        core = f"{bug[2]}.{ext}"
        boot = f"{bug[3]}.{ext}"
        test = f"{bug[4]}_test.{text}"
        line = 12 + ((i * 3 + j) % 17)
        nit = bug[5]
        defect = bug[6].format(prod=prod, noun=noun)
        reach = bug[7]
        missing = bug[8].format(prod=prod, noun=noun)
        fix = bug[9].format(prod=prod, noun=noun)
        needles = bug[10].format(prod=prod, noun=noun)
        notfam = f"{pref} leftover plant"
        plants.append(
            (slug, title, core, boot, test, line, nit, defect, reach, missing, fix, needles, notfam)
        )

# chain notfam to next plant
for i in range(len(plants)):
    nxt = plants[(i + 1) % len(plants)]
    row = list(plants[i])
    row[-1] = f"{nxt[0]} plant"
    plants[i] = tuple(row)

assert len(plants) == 180
assert len({p[0] for p in plants}) == 180
assert all("id-reuse" not in p[0] for p in plants)

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
    marker = "    (\"polars-lazy-cache-stale\","
    if marker not in text:
        raise SystemExit("anchor plant missing")
    # insert after the closing of _RAW list: find the last `]\n\n\nassert len(_RAW)`
    needle = "]\n\n\nassert len(_RAW) % 3 == 0, len(_RAW)"
    if needle not in text:
        # try alternate
        needle = "]\n\nassert len(_RAW) % 3 == 0, len(_RAW)"
    if needle not in text:
        raise SystemExit("cannot find _RAW close")
    block = "    # --- r1051 spreadsheet-db / notebooks / reverse-ETL / lake / gateway / lms ---\n"
    block += "".join(fmt(p) for p in plants)
    text = text.replace(needle, block + needle, 1)
    # expand notes stretch line if present
    extra = (
        " SeaTable/Teable/Grist/APITable/Rowy, Marimo/Quarto/Observable/Hex/Deepnote, "
        "Hightouch/Census/Grouparoo/RudderStack, Delta/Hudi/Iceberg/Dremio, "
        "Kong/Tyk/APISIX/KrakenD, Penpot/Excalidraw, Postal/mailcow/Mailu, "
        "Weblate/Tolgee/Pontoon, DocuSeal/Documenso/Paperless, Moodle/Open edX/Chamilo, "
        "Owncast/MediaMTX, Plane/Vikunja, InvenTree, GLPI/FreeScout, Netdata/Zabbix/Icinga."
    )
    old = "plus unused application bugs"
    if old in text and "SeaTable/Teable" not in text:
        text = text.replace(old, extra.strip() + " plus unused application bugs", 1)
    MILL.write_text(text)
    print(f"appended {len(plants)} plants")


if __name__ == "__main__":
    main()
