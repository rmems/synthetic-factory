#!/usr/bin/env python3
"""Append 180 unused CRP plants after the r1051 wave. Atomic mill replace."""
from __future__ import annotations

import os
from pathlib import Path

MILL = Path(__file__).with_name("crp-mill-r995.py")

FAMS = [
    ("graylog", "Graylog", "stream", "java", "java"),
    ("fluentbit", "Fluent Bit", "input", "c", "c"),
    ("logstash", "Logstash", "pipeline", "rb", "rb"),
    ("filebeat", "Filebeat", "prospect", "go", "go"),
    ("vectordev", "Vector", "source", "rs", "rs"),
    ("infisical", "Infisical", "secret", "ts", "ts"),
    ("sealedsecrets", "Sealed Secrets", "secret", "go", "go"),
    ("externalsecrets", "External Secrets", "secret", "go", "go"),
    ("doppler", "Doppler", "config", "go", "go"),
    ("chamber", "Chamber", "service", "go", "go"),
    ("sopscli", "SOPS", "file", "go", "go"),
    ("borgbackup", "Borg", "archive", "py", "py"),
    ("restserver", "restic REST", "repo", "go", "go"),
    ("rusticbackup", "rustic", "snapshot", "rs", "rs"),
    ("openremote", "OpenRemote", "asset", "java", "java"),
    ("fuxa", "FUXA", "view", "js", "js"),
    ("noderedflow", "Node-RED", "flow", "js", "js"),
    ("homebridge", "Homebridge", "accessory", "ts", "ts"),
    ("esphome", "ESPHome", "device", "py", "py"),
    ("zigbee2mqtt", "Zigbee2MQTT", "device", "js", "js"),
    ("keystonejs", "Keystone", "list", "ts", "ts"),
    ("sanityio", "Sanity", "document", "ts", "ts"),
    ("wagtailcms", "Wagtail", "page", "py", "py"),
    ("processwire", "ProcessWire", "page", "php", "php"),
    ("concretex", "Concrete CMS", "page", "php", "php"),
    ("holistics", "Holistics", "dataset", "rb", "rb"),
    ("gooddata", "GoodData", "metric", "ts", "ts"),
    ("thoughtspot", "ThoughtSpot", "answer", "java", "java"),
    ("sisense", "Sisense", "elasticube", "js", "js"),
    ("lookerstudio", "Looker Studio", "report", "js", "js"),
    ("limesurvey", "LimeSurvey", "survey", "php", "php"),
    ("surveyjs", "SurveyJS", "survey", "ts", "ts"),
    ("kobotoolbox", "KoBoToolbox", "asset", "py", "py"),
    ("odkcentral", "ODK Central", "form", "js", "js"),
    ("pulpregistry", "Pulp", "repo", "py", "py"),
    ("devpipkg", "devpi", "index", "py", "py"),
    ("aptly", "Aptly", "repo", "go", "go"),
    ("reprepro", "reprepro", "suite", "c", "c"),
    ("caddyfile", "Caddy", "site", "go", "go"),
    ("traefikproxy", "Traefik", "router", "go", "go"),
    ("pushoverapp", "Pushover", "message", "go", "go"),
    ("healthchecksio", "Healthchecks", "check", "py", "py"),
    ("cachethq", "Cachet", "incident", "php", "php"),
    ("zulipchat", "Zulip", "stream", "py", "py"),
    ("jitsimeet", "Jitsi Meet", "room", "js", "js"),
    ("bigbluebutton", "BigBlueButton", "meeting", "java", "java"),
    ("piwigo", "Piwigo", "album", "php", "php"),
    ("shaarli", "Shaarli", "link", "php", "php"),
    ("fireflyiii", "Firefly III", "transaction", "php", "php"),
    ("actualbudget", "Actual Budget", "account", "js", "js"),
    ("akaunting", "Akaunting", "invoice", "php", "php"),
    ("kimai", "Kimai", "timesheet", "php", "php"),
    ("orangehrm", "OrangeHRM", "employee", "php", "php"),
    ("icehrm", "IceHrm", "employee", "php", "php"),
    ("leantime", "Leantime", "ticket", "php", "php"),
    ("openproject", "OpenProject", "workpackage", "rb", "rb"),
    ("redmine", "Redmine", "issue", "rb", "rb"),
    ("pretix", "pretix", "order", "py", "py"),
    ("eventyay", "eventyay", "ticket", "py", "py"),
    ("posthog", "PostHog", "insight", "py", "py"),
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
        bug = BUGS[(i + j * 7) % len(BUGS)]  # different phase than r1051 (was *5)
        slug = f"{pref}-{bug[0]}"
        plants.append(
            (
                slug, bug[1], f"{bug[2]}.{ext}", f"{bug[3]}.{ext}", f"{bug[4]}_test.{text}",
                12 + ((i * 3 + j) % 19), bug[5],
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
    existing = set(p[0] for p in plants if p[0] in text)
    if existing:
        raise SystemExit(f"slug collision in mill: {sorted(existing)[:8]}")
    needle = "]\n\n\nassert len(_RAW) % 3 == 0, len(_RAW)"
    if needle not in text:
        needle = "]\n\nassert len(_RAW) % 3 == 0, len(_RAW)"
    if needle not in text:
        raise SystemExit("cannot find _RAW close")
    block = "    # --- r1111 logs/secrets/backup/iot/cms/bi/survey/registry/status ---\n"
    block += "".join(fmt(p) for p in plants)
    text = text.replace(needle, block + needle, 1)
    extra = (
        " Graylog/Fluent Bit/Logstash/Filebeat/Vector, Infisical/SOPS/Doppler/Chamber, "
        "Borg/restic REST/rustic, OpenRemote/FUXA/Node-RED/ESPHome/Zigbee2MQTT, "
        "Keystone/Sanity/Wagtail, Holistics/GoodData/ThoughtSpot, LimeSurvey/KoBo/ODK, "
        "Pulp/devpi/Aptly, Caddy/Traefik, Zulip/Jitsi/BBB, Firefly/Actual/Akaunting/Kimai, "
        "OrangeHRM/Leantime/OpenProject/Redmine, pretix/PostHog."
    )
    old = "plus unused application bugs"
    if old in text and "Graylog/Fluent Bit" not in text:
        text = text.replace(old, extra.strip() + " plus unused application bugs", 1)
    tmp = MILL.with_suffix(".py.tmp")
    tmp.write_text(text)
    os.replace(tmp, MILL)
    print(f"appended {len(plants)} plants atomically")


if __name__ == "__main__":
    main()
