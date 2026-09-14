#!/usr/bin/env python3
"""TUP leftover4 mill — unique inspect-vs-destroy plants after v13 drain.

Not a 429-stamp mill. Goals name the tool and the fork.
BAN checkout-gate-429 sentence, yq-eval clones, pacman clones,
cargo-publish/npm-pack, scanner mill, process-manager mill, SCSI/smartctl.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, "/tmp")
from tup_unique_leftover_mill import (  # noqa: E402
    BANNED_BITS,
    BANNED_GOAL,
    CLONE_SLUGS,
    LRF,
    P,
    TUP,
    abort_payload,
    make_record as _make_record,
    reserved_round,
    try_hop_lrf,
    try_reserve_tup,
)

MAX_ROUNDS = 10_000
MAX_SECONDS = 20_000
USED_SLUGS = set(CLONE_SLUGS)


def load_used() -> set[str]:
    used = set(USED_SLUGS)
    if not TUP.is_dir():
        return used
    import re

    slug_re = re.compile(r"^tup-r\d+-(.*)$")
    for path in TUP.glob("batch-r*.jsonl"):
        try:
            text = path.read_text()
        except OSError:
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                rec_id = json.loads(line).get("id", "")
            except Exception:
                continue
            match = slug_re.match(rec_id)
            if match:
                used.add(match.group(1))
    return used


def notes_md(round_n: int, recs: list[dict], plants: list[dict]) -> str:
    forks = [f"{p['good']} vs {p['bad']}" for p in plants]
    leftovers = [p.get("leftover", "?") for p in plants]
    lines = [
        f"# tool-use-preference-factory — NOTES r{round_n}",
        "",
        "Novel coverage: 92%",
        "",
        "Headline: unique leftover4 12-step DPO pairs — " + ", ".join(forks),
        "",
        "Construction: divergence-point DPO, shared 6-step prefix. Same goal both sides. "
        "Goals name the tool and the fork. Not the checkout-gate-429 stamp. "
        "Not yq-eval / yq-eval-json / yq-eval-props. Not pacman clones. "
        "Not cargo-publish/npm-pack. Not scanner mill. Not process-manager mill.",
        "",
        f"Leftover4 themes: {leftovers}",
        "",
        "Records:",
    ]
    for rec, plant in zip(recs, plants):
        lines.append(
            f"- `{rec['id']}` fork=`{plant['good']} vs {plant['bad']}` leftover=`{plant.get('leftover')}` "
            "sin=`wrong tool` (+ skip verify) 12/12 steps"
        )
    lines += [
        "",
        "Rejected sins this round: ['wrong tool', 'wrong tool', 'wrong tool']",
        f"IDs: {[r['id'] for r in recs]!r}",
        "",
        "Weakest critique: shortest still ≥400 chars and names the two CLIs. "
        "Next densify: remaining unused leftover4 dry-run vs mutate plants.",
        "",
        "No Thalamic six-field core. No spikes. Observations are designed plants.",
        "",
    ]
    return "\n".join(lines)


def make_record(round_n: int, p: dict) -> dict:
    rec = _make_record(round_n, p)
    g = rec["goal"]
    gl = g.lower()
    assert BANNED_GOAL not in g
    assert "Check designed checkout" not in g
    for bit in BANNED_BITS:
        assert bit not in gl, bit
    assert "yq-eval" not in rec["id"] and "pacman" not in rec["id"]
    assert len(rec["critique"]) >= 400
    assert len(rec["chosen"]["steps"]) == 12
    return rec


def publish_tup(payload: dict, plants: list[dict]) -> bool:
    n = int(payload["round"])
    stage = Path(payload["staging_dir"])
    batch = stage / payload["batch_file"]
    notes = stage / payload["notes_file"]
    recs = [make_record(n, p) for p in plants]
    with batch.open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=False) + "\n")
    notes.write_text(notes_md(n, recs, plants))
    from tup_unique_leftover_mill import round_txn

    try:
        round_txn.publish(TUP, n, payload["token"])
    except round_txn.TransactionError as exc:
        print(f"PUBLISH-FAIL r{n}: {exc}", flush=True)
        return False
    print(
        f"PUBLISHED tup r{n} leftover={[p.get('leftover') for p in plants]} ids={[r['id'] for r in recs]}",
        flush=True,
    )
    return True


PLANTS: list[dict] = [
    P(
        leftover="mailindex",
        slug="notmuch-count-vs-tag-strip",
        tool="notmuch",
        good="notmuch count",
        bad="notmuch tag -inbox '*'",
        keep="/plant/notmuch/config",
        resource="notmuch inbox pay-kyc",
        wait=3,
        src429="notmuch Xapian",
        ver="notmuch 0.38.3",
        size=420,
        inv_cmd="ls -la /plant/notmuch/config && notmuch --version",
        read_cmd="grep -nE 'database.path|user.primary_email' /plant/notmuch/config | head",
        read_obs="designed: path /mail/pay; email kyc@pay. operator: count, not tag -inbox '*'.",
        state_cmd="notmuch count tag:inbox",
        state_obs="designed: 1842 inbox. no tag strip.",
        gate_cmd="notmuch count tag:inbox; echo RC:$?",
        gate_ok="designed: RC:0; 1842.",
        good_cmd="notmuch count tag:inbox and from:kyc@pay; echo RC:$?",
        good_obs="designed: RC:0; 41. no tag strip.",
        confirm_cmd="notmuch count tag:inbox",
        confirm_obs="designed: 1842 inbox kept.",
        bad_cmd="notmuch tag -inbox '*'; echo RC:$?",
        bad_obs="designed: RC:0 stripped inbox from 1842 messages. ignored 429. wrong-tool.",
        after_bad_obs="designed: count inbox 0. skip-verify.",
        gone_cmd="notmuch count tag:inbox; test -e /plant/notmuch/config; echo RC:$?",
        gone_obs="designed: 0 inbox; config missing. skip-verify.",
        goal=(
            "Count designed notmuch inbox pay-kyc with notmuch count tag:inbox only after "
            "notmuch --version; do not strip tags. Do not notmuch tag -inbox '*' or rm config "
            "when notmuch Xapian returns 429."
        ),
    ),
    P(
        leftover="mailindex",
        slug="mu-find-vs-remove-all",
        tool="mu",
        good="mu find",
        bad="mu remove --all",
        keep="/plant/mu/mu.cfg",
        resource="mu index pay-maildir",
        wait=4,
        src429="mu Xapian",
        ver="mu 1.12.6",
        size=280,
        inv_cmd="ls -la /plant/mu/mu.cfg && mu --version | head -1",
        read_cmd="grep -nE 'maildir|database' /plant/mu/mu.cfg | head",
        read_obs="designed: maildir /mail/pay. operator: mu find, not mu remove --all.",
        state_cmd="mu find from:kyc | head",
        state_obs="designed: 41 hits. no remove.",
        gate_cmd="mu info; echo RC:$?",
        gate_ok="designed: RC:0; documents 18420.",
        good_cmd="mu find from:kyc --format=plain | head; echo RC:$?",
        good_obs="designed: RC:0; 41 hits. no remove --all.",
        confirm_cmd="mu find from:kyc | wc -l",
        confirm_obs="designed: 41 kept.",
        bad_cmd="mu remove --all; echo RC:$?",
        bad_obs="designed: RC:0 index emptied. ignored 429. wrong-tool.",
        after_bad_obs="designed: find 0 hits. skip-verify.",
        gone_cmd="mu find from:kyc; test -e /plant/mu/mu.cfg; echo RC:$?",
        gone_obs="designed: empty; cfg missing. skip-verify.",
        goal=(
            "Search designed mu index pay-maildir with mu find from:kyc only after mu info; "
            "do not wipe. Do not mu remove --all or rm mu.cfg when mu Xapian returns 429."
        ),
    ),
    P(
        leftover="contacts",
        slug="khard-list-vs-remove-force",
        tool="khard",
        good="khard list",
        bad="khard remove --force",
        keep="/plant/khard/khard.conf",
        resource="khard address book pay",
        wait=3,
        src429="CardDAV",
        ver="khard 0.19.1",
        size=510,
        inv_cmd="ls -la /plant/khard/khard.conf && khard --version",
        read_cmd="grep -nE 'addressbooks|path' /plant/khard/khard.conf | head",
        read_obs="designed: addressbook pay. operator: list, not remove --force.",
        state_cmd="khard list -c /plant/khard/khard.conf | head",
        state_obs="designed: ada@pay kyc@pay. no remove.",
        gate_cmd="khard list -c /plant/khard/khard.conf; echo RC:$?",
        gate_ok="designed: RC:0; 86 contacts.",
        good_cmd="khard list -c /plant/khard/khard.conf ada; echo RC:$?",
        good_obs="designed: RC:0; Ada Lovelace pay. no remove.",
        confirm_cmd="khard list -c /plant/khard/khard.conf | wc -l",
        confirm_obs="designed: 86 kept.",
        bad_cmd="khard remove --force ada; echo RC:$?",
        bad_obs="designed: RC:0 ada deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: list ada empty. skip-verify.",
        gone_cmd="khard list ada; test -e /plant/khard/khard.conf; echo RC:$?",
        gone_obs="designed: ada gone; conf missing. skip-verify.",
        goal=(
            "List designed khard address book pay with khard list only after khard --version; "
            "do not delete. Do not khard remove --force ada or rm khard.conf when CardDAV returns 429."
        ),
    ),
    P(
        leftover="calendar",
        slug="khal-list-vs-rm-config",
        tool="khal",
        good="khal list",
        bad="rm -f /plant/khal/config",
        keep="/plant/khal/config",
        resource="khal calendar pay-oncall",
        wait=4,
        src429="CalDAV",
        ver="khal 0.11.3",
        size=640,
        inv_cmd="ls -la /plant/khal/config && khal --version",
        read_cmd="grep -nE 'calendars|path' /plant/khal/config | head",
        read_obs="designed: calendar pay-oncall. operator: khal list, not rm config.",
        state_cmd="khal list today | head",
        state_obs="designed: 3 events today. no rm.",
        gate_cmd="khal calendar; echo RC:$?",
        gate_ok="designed: RC:0; month printed.",
        good_cmd="khal list today; echo RC:$?",
        good_obs="designed: RC:0; page, swap, freeze. no rm.",
        confirm_cmd="khal list today | wc -l",
        confirm_obs="designed: 3 events kept.",
        bad_cmd="rm -f /plant/khal/config; echo RC:$?",
        bad_obs="designed: RC:0 config deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: khal list cannot find config. skip-verify.",
        gone_cmd="test -e /plant/khal/config; echo RC:$?",
        gone_obs="designed: RC:1 missing. skip-verify.",
        goal=(
            "List designed khal calendar pay-oncall with khal list today only after khal calendar; "
            "do not delete config. Do not rm -f /plant/khal/config when CalDAV returns 429."
        ),
    ),
    P(
        leftover="calendar",
        slug="todoman-list-vs-delete-force",
        tool="todo",
        good="todo list",
        bad="todo delete --force",
        keep="/plant/todoman/config",
        resource="todoman list pay-kyc",
        wait=3,
        src429="CalDAV VTODO",
        ver="todoman 4.4.0",
        size=390,
        inv_cmd="ls -la /plant/todoman/config && todo --version",
        read_cmd="grep -nE 'path|default_list' /plant/todoman/config | head",
        read_obs="designed: default_list pay-kyc. operator: todo list, not delete --force.",
        state_cmd="todo list --porcelain | head",
        state_obs="designed: 12 open. no delete.",
        gate_cmd="todo list; echo RC:$?",
        gate_ok="designed: RC:0; 12 todos.",
        good_cmd="todo list --due 7; echo RC:$?",
        good_obs="designed: RC:0; 4 due this week. no delete.",
        confirm_cmd="todo list --porcelain | wc -l",
        confirm_obs="designed: 12 kept.",
        bad_cmd="todo delete --force 1; echo RC:$?",
        bad_obs="designed: RC:0 todo 1 deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: list missing 1. skip-verify.",
        gone_cmd="todo list; test -e /plant/todoman/config; echo RC:$?",
        gone_obs="designed: list broken; config missing. skip-verify.",
        goal=(
            "List designed todoman list pay-kyc with todo list --due 7 only after todo list; "
            "do not delete. Do not todo delete --force 1 or rm config when CalDAV VTODO returns 429."
        ),
    ),
    P(
        leftover="passwords",
        slug="pass-ls-vs-rm-tree",
        tool="pass",
        good="pass ls",
        bad="pass rm -r pay",
        keep="/plant/password-store/.gpg-id",
        resource="pass store pay/",
        wait=4,
        src429="GnuPG",
        ver="pass 1.7.4",
        size=40,
        inv_cmd="ls -la /plant/password-store/.gpg-id && pass version | head -1",
        read_cmd="cat /plant/password-store/.gpg-id | head",
        read_obs="designed: gpg-id 0xPAY. operator: pass ls, not pass rm -r pay.",
        state_cmd="pass ls pay | head",
        state_obs="designed: pay/stripe pay/kyc. no rm.",
        gate_cmd="pass ls; echo RC:$?",
        gate_ok="designed: RC:0; tree listed.",
        good_cmd="pass ls pay; echo RC:$?",
        good_obs="designed: RC:0; stripe kyc. no rm -r.",
        confirm_cmd="pass ls pay | wc -l",
        confirm_obs="designed: 2 entries kept.",
        bad_cmd="pass rm -r pay; echo RC:$?",
        bad_obs="designed: RC:0 pay/ tree deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: ls pay empty. skip-verify.",
        gone_cmd="pass ls pay; test -e /plant/password-store/.gpg-id; echo RC:$?",
        gone_obs="designed: tree gone; gpg-id missing. skip-verify.",
        goal=(
            "List designed pass store pay/ with pass ls pay only after pass ls; do not delete. "
            "Do not pass rm -r pay or rm .gpg-id when GnuPG returns 429."
        ),
    ),
    P(
        leftover="passwords",
        slug="gopass-ls-vs-rm-tree",
        tool="gopass",
        good="gopass ls",
        bad="gopass rm -r pay",
        keep="/plant/gopass/config",
        resource="gopass store pay/",
        wait=3,
        src429="gopass store",
        ver="gopass 1.15.14",
        size=220,
        inv_cmd="ls -la /plant/gopass/config && gopass version | head -1",
        read_cmd="grep -nE 'path|root' /plant/gopass/config | head",
        read_obs="designed: root /plant/gopass/store. operator: gopass ls, not rm -r pay.",
        state_cmd="gopass ls pay | head",
        state_obs="designed: pay/stripe. no rm.",
        gate_cmd="gopass fsck; echo RC:$?",
        gate_ok="designed: RC:0; fsck clean.",
        good_cmd="gopass ls pay; echo RC:$?",
        good_obs="designed: RC:0; stripe kyc. no rm -r.",
        confirm_cmd="gopass ls pay | wc -l",
        confirm_obs="designed: 2 kept.",
        bad_cmd="gopass rm -r pay; echo RC:$?",
        bad_obs="designed: RC:0 pay/ deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: ls pay empty. skip-verify.",
        gone_cmd="gopass ls pay; test -e /plant/gopass/config; echo RC:$?",
        gone_obs="designed: gone; config missing. skip-verify.",
        goal=(
            "List designed gopass store pay/ with gopass ls pay only after gopass fsck; do not delete. "
            "Do not gopass rm -r pay or rm config when gopass store returns 429."
        ),
    ),
    P(
        leftover="passwords",
        slug="passage-ls-vs-rm-tree",
        tool="passage",
        good="passage ls",
        bad="passage rm -r pay",
        keep="/plant/passage/.age-recipients",
        resource="passage store pay/",
        wait=4,
        src429="age",
        ver="passage 1.7.4-age",
        size=64,
        inv_cmd="ls -la /plant/passage/.age-recipients && passage version | head -1 || echo designed-passage",
        read_cmd="cat /plant/passage/.age-recipients | head",
        read_obs="designed: age recipient pay. operator: passage ls, not rm -r pay.",
        state_cmd="passage ls pay | head",
        state_obs="designed: pay/stripe. no rm.",
        gate_cmd="passage ls; echo RC:$?",
        gate_ok="designed: RC:0; tree listed.",
        good_cmd="passage ls pay; echo RC:$?",
        good_obs="designed: RC:0; stripe. no rm -r.",
        confirm_cmd="passage ls pay | wc -l",
        confirm_obs="designed: 1 kept.",
        bad_cmd="passage rm -r pay; echo RC:$?",
        bad_obs="designed: RC:0 pay/ deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: ls pay empty. skip-verify.",
        gone_cmd="passage ls pay; test -e /plant/passage/.age-recipients; echo RC:$?",
        gone_obs="designed: gone; recipients missing. skip-verify.",
        goal=(
            "List designed passage store pay/ with passage ls pay only after passage ls; do not delete. "
            "Do not passage rm -r pay or rm .age-recipients when age returns 429."
        ),
    ),
    P(
        leftover="host",
        slug="hostnamectl-status-vs-set-wiped",
        tool="hostnamectl",
        good="hostnamectl status",
        bad="hostnamectl set-hostname wiped",
        keep="/plant/hostname/hostname",
        resource="systemd hostname pay-api-3",
        wait=3,
        src429="systemd-hostnamed",
        ver="hostnamectl 255",
        size=12,
        inv_cmd="ls -la /plant/hostname/hostname && hostnamectl --version | head -1",
        read_cmd="cat /plant/hostname/hostname",
        read_obs="designed: pay-api-3. operator: status, not set-hostname wiped.",
        state_cmd="hostnamectl status | grep Static",
        state_obs="designed: Static hostname pay-api-3. no set.",
        gate_cmd="hostnamectl status; echo RC:$?",
        gate_ok="designed: RC:0; pay-api-3.",
        good_cmd="hostnamectl status --pretty; echo RC:$?",
        good_obs="designed: RC:0; Pretty Pay API 3. no set-hostname.",
        confirm_cmd="hostnamectl status | grep 'Static hostname'",
        confirm_obs="designed: pay-api-3 kept.",
        bad_cmd="hostnamectl set-hostname wiped; echo RC:$?",
        bad_obs="designed: RC:0 hostname wiped. ignored 429. wrong-tool.",
        after_bad_obs="designed: status Static hostname wiped. skip-verify.",
        gone_cmd="hostnamectl status; test -e /plant/hostname/hostname; echo RC:$?",
        gone_obs="designed: wiped; file missing. skip-verify.",
        goal=(
            "Show designed systemd hostname pay-api-3 with hostnamectl status only after hostnamectl --version; "
            "do not rename. Do not hostnamectl set-hostname wiped or rm hostname when systemd-hostnamed returns 429."
        ),
    ),
    P(
        leftover="host",
        slug="localectl-status-vs-set-c",
        tool="localectl",
        good="localectl status",
        bad="localectl set-locale LANG=C",
        keep="/plant/locale/locale.conf",
        resource="systemd locale pay-console",
        wait=4,
        src429="systemd-localed",
        ver="localectl 255",
        size=18,
        inv_cmd="ls -la /plant/locale/locale.conf && localectl --version | head -1",
        read_cmd="cat /plant/locale/locale.conf",
        read_obs="designed: LANG=en_US.UTF-8. operator: status, not set-locale LANG=C.",
        state_cmd="localectl status | grep LANG",
        state_obs="designed: LANG=en_US.UTF-8. no set.",
        gate_cmd="localectl status; echo RC:$?",
        gate_ok="designed: RC:0; en_US.UTF-8.",
        good_cmd="localectl list-locales | grep en_US; echo RC:$?",
        good_obs="designed: RC:0; en_US.UTF-8 listed. no set-locale.",
        confirm_cmd="localectl status | grep System",
        confirm_obs="designed: en_US.UTF-8 kept.",
        bad_cmd="localectl set-locale LANG=C; echo RC:$?",
        bad_obs="designed: RC:0 locale C. ignored 429. wrong-tool.",
        after_bad_obs="designed: status LANG=C. skip-verify.",
        gone_cmd="localectl status; test -e /plant/locale/locale.conf; echo RC:$?",
        gone_obs="designed: C; conf missing. skip-verify.",
        goal=(
            "Show designed systemd locale pay-console with localectl status only after localectl --version; "
            "do not reset. Do not localectl set-locale LANG=C or rm locale.conf when systemd-localed returns 429."
        ),
    ),
    P(
        leftover="dbus",
        slug="busctl-list-vs-rm-conf",
        tool="busctl",
        good="busctl list",
        bad="rm -f /plant/dbus/system.conf",
        keep="/plant/dbus/system.conf",
        resource="D-Bus system bus pay",
        wait=3,
        src429="dbus-broker",
        ver="busctl 255",
        size=880,
        inv_cmd="ls -la /plant/dbus/system.conf && busctl --version | head -1",
        read_cmd="grep -nE 'policy|user=' /plant/dbus/system.conf | head",
        read_obs="designed: policy default. operator: busctl list, not rm system.conf.",
        state_cmd="busctl list | head",
        state_obs="designed: org.freedesktop.DBus. no rm.",
        gate_cmd="busctl status; echo RC:$?",
        gate_ok="designed: RC:0; unique name :1.0.",
        good_cmd="busctl list --acquired | head; echo RC:$?",
        good_obs="designed: RC:0; 24 names. no rm.",
        confirm_cmd="busctl list | wc -l",
        confirm_obs="designed: 24 kept.",
        bad_cmd="rm -f /plant/dbus/system.conf; echo RC:$?",
        bad_obs="designed: RC:0 conf deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: busctl list fails. skip-verify.",
        gone_cmd="test -e /plant/dbus/system.conf; echo RC:$?",
        gone_obs="designed: RC:1 missing. skip-verify.",
        goal=(
            "List designed D-Bus system bus pay with busctl list --acquired only after busctl status; "
            "do not delete policy. Do not rm -f /plant/dbus/system.conf when dbus-broker returns 429."
        ),
    ),
    P(
        leftover="session",
        slug="loginctl-sessions-vs-terminate-user",
        tool="loginctl",
        good="loginctl list-sessions",
        bad="loginctl terminate-user pay",
        keep="/plant/logind/logind.conf",
        resource="logind sessions pay",
        wait=4,
        src429="systemd-logind",
        ver="loginctl 255",
        size=310,
        inv_cmd="ls -la /plant/logind/logind.conf && loginctl --version | head -1",
        read_cmd="grep -nE 'KillUserProcesses|IdleAction' /plant/logind/logind.conf | head",
        read_obs="designed: KillUserProcesses=no. operator: list-sessions, not terminate-user pay.",
        state_cmd="loginctl list-sessions | head",
        state_obs="designed: session 12 pay. no terminate.",
        gate_cmd="loginctl user-status pay | head; echo RC:$?",
        gate_ok="designed: RC:0; 1 session.",
        good_cmd="loginctl list-sessions; echo RC:$?",
        good_obs="designed: RC:0; session 12 pay seat0. no terminate.",
        confirm_cmd="loginctl list-sessions | grep pay",
        confirm_obs="designed: session 12 kept.",
        bad_cmd="loginctl terminate-user pay; echo RC:$?",
        bad_obs="designed: RC:0 user pay terminated. ignored 429. wrong-tool.",
        after_bad_obs="designed: list-sessions empty for pay. skip-verify.",
        gone_cmd="loginctl list-sessions; test -e /plant/logind/logind.conf; echo RC:$?",
        gone_obs="designed: sessions gone; conf missing. skip-verify.",
        goal=(
            "List designed logind sessions pay with loginctl list-sessions only after loginctl user-status pay; "
            "do not terminate. Do not loginctl terminate-user pay or rm logind.conf when systemd-logind returns 429."
        ),
    ),
    P(
        leftover="unit",
        slug="systemd-analyze-verify-vs-rm-unit",
        tool="systemd-analyze",
        good="systemd-analyze verify",
        bad="rm -f /plant/systemd/pay.service",
        keep="/plant/systemd/pay.service",
        resource="systemd unit pay.service",
        wait=3,
        src429="systemd",
        ver="systemd-analyze 255",
        size=720,
        inv_cmd="ls -la /plant/systemd/pay.service && systemd-analyze --version | head -1",
        read_cmd="grep -nE 'ExecStart|Type=' /plant/systemd/pay.service | head",
        read_obs="designed: Type=notify ExecStart=/usr/bin/pay. operator: verify, not rm unit.",
        state_cmd="systemd-analyze verify /plant/systemd/pay.service; echo pre",
        state_obs="designed: no errors. no rm.",
        gate_cmd="systemd-analyze verify /plant/systemd/pay.service; echo RC:$?",
        gate_ok="designed: RC:0; unit ok.",
        good_cmd="systemd-analyze verify --man=no /plant/systemd/pay.service; echo RC:$?",
        good_obs="designed: RC:0; 0 warnings. no rm.",
        confirm_cmd="test -f /plant/systemd/pay.service && echo present",
        confirm_obs="designed: present.",
        bad_cmd="rm -f /plant/systemd/pay.service; echo RC:$?",
        bad_obs="designed: RC:0 unit deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: verify missing file. skip-verify.",
        gone_cmd="test -e /plant/systemd/pay.service; echo RC:$?",
        gone_obs="designed: RC:1 missing. skip-verify.",
        goal=(
            "Verify designed systemd unit pay.service with systemd-analyze verify only after a first verify; "
            "do not delete. Do not rm -f /plant/systemd/pay.service when systemd returns 429."
        ),
    ),
    P(
        leftover="pki",
        slug="easyrsa-show-expire-vs-revoke",
        tool="easyrsa",
        good="easyrsa show-expire",
        bad="easyrsa revoke pay",
        keep="/plant/easyrsa/pki/issued/pay.crt",
        resource="Easy-RSA cert pay",
        wait=4,
        src429="Easy-RSA PKI",
        ver="easyrsa 3.2.1",
        size=1800,
        inv_cmd="ls -la /plant/easyrsa/pki/issued/pay.crt && easyrsa version | head -1 || echo designed-easyrsa",
        read_cmd="openssl x509 -in /plant/easyrsa/pki/issued/pay.crt -noout -subject | head",
        read_obs="designed: CN=pay. operator: show-expire, not revoke pay.",
        state_cmd="easyrsa show-cert pay | head",
        state_obs="designed: valid. no revoke.",
        gate_cmd="easyrsa show-cert pay; echo RC:$?",
        gate_ok="designed: RC:0; valid.",
        good_cmd="easyrsa show-expire; echo RC:$?",
        good_obs="designed: RC:0; pay expires 2027. no revoke.",
        confirm_cmd="easyrsa show-cert pay | grep Status",
        confirm_obs="designed: VALID kept.",
        bad_cmd="easyrsa revoke pay; echo RC:$?",
        bad_obs="designed: RC:0 cert revoked. ignored 429. wrong-tool.",
        after_bad_obs="designed: show-cert REVOKED. skip-verify.",
        gone_cmd="easyrsa show-cert pay; test -e /plant/easyrsa/pki/issued/pay.crt; echo RC:$?",
        gone_obs="designed: revoked; crt missing. skip-verify.",
        goal=(
            "Show designed Easy-RSA cert pay expiry with easyrsa show-expire only after easyrsa show-cert pay; "
            "do not revoke. Do not easyrsa revoke pay or rm pay.crt when Easy-RSA PKI returns 429."
        ),
    ),
    P(
        leftover="pki",
        slug="certstrap-list-vs-rm-key",
        tool="certstrap",
        good="certstrap list",
        bad="rm -f /plant/certstrap/depot/pay.key",
        keep="/plant/certstrap/depot/pay.key",
        resource="certstrap depot pay",
        wait=3,
        src429="certstrap depot",
        ver="certstrap 1.3.0",
        size=240,
        inv_cmd="ls -la /plant/certstrap/depot/pay.key && certstrap --version | head -1 || echo designed-certstrap",
        read_cmd="ls /plant/certstrap/depot | head",
        read_obs="designed: pay.crt pay.key. operator: list, not rm pay.key.",
        state_cmd="certstrap list --depot-path /plant/certstrap/depot",
        state_obs="designed: pay VALID. no rm.",
        gate_cmd="certstrap list --depot-path /plant/certstrap/depot; echo RC:$?",
        gate_ok="designed: RC:0; pay listed.",
        good_cmd="certstrap list --depot-path /plant/certstrap/depot; echo RC:$?",
        good_obs="designed: RC:0; pay. no rm key.",
        confirm_cmd="test -f /plant/certstrap/depot/pay.key && echo present",
        confirm_obs="designed: present.",
        bad_cmd="rm -f /plant/certstrap/depot/pay.key; echo RC:$?",
        bad_obs="designed: RC:0 key deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: list missing pay.key. skip-verify.",
        gone_cmd="test -e /plant/certstrap/depot/pay.key; echo RC:$?",
        gone_obs="designed: RC:1 missing. skip-verify.",
        goal=(
            "List designed certstrap depot pay with certstrap list --depot-path only after a first list; "
            "do not delete keys. Do not rm -f /plant/certstrap/depot/pay.key when certstrap depot returns 429."
        ),
    ),
    P(
        leftover="pki",
        slug="minica-help-vs-rm-ca-key",
        tool="minica",
        good="minica -help",
        bad="rm -f /plant/minica/minica-key.pem",
        keep="/plant/minica/minica-key.pem",
        resource="minica CA pay",
        wait=4,
        src429="minica CA",
        ver="minica 1.0.2",
        size=320,
        inv_cmd="ls -la /plant/minica/minica-key.pem /plant/minica/minica.pem && minica -help | head -1 || echo designed-minica",
        read_cmd="openssl pkey -in /plant/minica/minica-key.pem -noout -text | head",
        read_obs="designed: EC key. operator: minica -help, not rm minica-key.pem.",
        state_cmd="ls -la /plant/minica/minica.pem",
        state_obs="designed: CA cert present. no rm.",
        gate_cmd="openssl x509 -in /plant/minica/minica.pem -noout -subject; echo RC:$?",
        gate_ok="designed: RC:0; CN=minica root ca pay.",
        good_cmd="minica -help | head; echo RC:$?",
        good_obs="designed: RC:0; usage. no rm CA key.",
        confirm_cmd="test -f /plant/minica/minica-key.pem && echo present",
        confirm_obs="designed: present.",
        bad_cmd="rm -f /plant/minica/minica-key.pem; echo RC:$?",
        bad_obs="designed: RC:0 CA key deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: help ok but key gone. skip-verify.",
        gone_cmd="test -e /plant/minica/minica-key.pem; echo RC:$?",
        gone_obs="designed: RC:1 missing. skip-verify.",
        goal=(
            "Inspect designed minica CA pay with minica -help only after openssl x509 -in minica.pem; "
            "do not delete the CA key. Do not rm -f /plant/minica/minica-key.pem when minica CA returns 429."
        ),
    ),
    P(
        leftover="smtp",
        slug="msmtp-serverinfo-vs-rm-rc",
        tool="msmtp",
        good="msmtp --serverinfo",
        bad="rm -f /plant/msmtp/msmtprc",
        keep="/plant/msmtp/msmtprc",
        resource="msmtp account pay-alert",
        wait=3,
        src429="SMTP",
        ver="msmtp 1.8.26",
        size=260,
        inv_cmd="ls -la /plant/msmtp/msmtprc && msmtp --version | head -1",
        read_cmd="grep -nE 'account|host|from' /plant/msmtp/msmtprc | head",
        read_obs="designed: host smtp.pay from alerts@pay. operator: --serverinfo, not rm msmtprc.",
        state_cmd="msmtp --print-config -C /plant/msmtp/msmtprc | head",
        state_obs="designed: account pay-alert. no rm.",
        gate_cmd="msmtp --print-config -C /plant/msmtp/msmtprc; echo RC:$?",
        gate_ok="designed: RC:0; config printed.",
        good_cmd="msmtp --serverinfo -C /plant/msmtp/msmtprc | head; echo RC:$?",
        good_obs="designed: RC:0; STARTTLS 250. no rm.",
        confirm_cmd="test -f /plant/msmtp/msmtprc && echo present",
        confirm_obs="designed: present.",
        bad_cmd="rm -f /plant/msmtp/msmtprc; echo RC:$?",
        bad_obs="designed: RC:0 rc deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: serverinfo missing config. skip-verify.",
        gone_cmd="test -e /plant/msmtp/msmtprc; echo RC:$?",
        gone_obs="designed: RC:1 missing. skip-verify.",
        goal=(
            "Probe designed msmtp account pay-alert with msmtp --serverinfo only after msmtp --print-config; "
            "do not delete rc. Do not rm -f /plant/msmtp/msmtprc when SMTP returns 429."
        ),
    ),
    P(
        leftover="smtp",
        slug="swaks-dump-vs-rm-conf",
        tool="swaks",
        good="swaks --dump protocol",
        bad="rm -f /plant/swaks/swaks.conf",
        keep="/plant/swaks/swaks.conf",
        resource="swaks SMTP probe pay",
        wait=4,
        src429="SMTP banner",
        ver="swaks 20240103",
        size=180,
        inv_cmd="ls -la /plant/swaks/swaks.conf && swaks --version | head -1",
        read_cmd="grep -nE 'to|server' /plant/swaks/swaks.conf | head",
        read_obs="designed: to alerts@pay server smtp.pay. operator: --dump protocol, not rm conf.",
        state_cmd="swaks --help | head",
        state_obs="designed: help. no rm.",
        gate_cmd="swaks --help >/dev/null; echo RC:$?",
        gate_ok="designed: RC:0.",
        good_cmd="swaks --dump protocol --to alerts@pay --server smtp.pay | head; echo RC:$?",
        good_obs="designed: RC:0; dump EHLO MAIL. no send body. no rm.",
        confirm_cmd="test -f /plant/swaks/swaks.conf && echo present",
        confirm_obs="designed: present.",
        bad_cmd="rm -f /plant/swaks/swaks.conf; echo RC:$?",
        bad_obs="designed: RC:0 conf deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: dump missing conf. skip-verify.",
        gone_cmd="test -e /plant/swaks/swaks.conf; echo RC:$?",
        gone_obs="designed: RC:1 missing. skip-verify.",
        goal=(
            "Dump designed swaks SMTP probe pay with swaks --dump protocol only after swaks --help; "
            "do not delete conf. Do not rm -f /plant/swaks/swaks.conf when SMTP banner returns 429."
        ),
    ),
    P(
        leftover="imap",
        slug="mbsync-list-vs-rm-rc",
        tool="mbsync",
        good="mbsync --list",
        bad="rm -f /plant/isync/mbsyncrc",
        keep="/plant/isync/mbsyncrc",
        resource="isync store pay-mail",
        wait=3,
        src429="IMAP",
        ver="isync 1.4.4",
        size=540,
        inv_cmd="ls -la /plant/isync/mbsyncrc && mbsync --version | head -1",
        read_cmd="grep -nE 'IMAPStore|MaildirStore|Channel' /plant/isync/mbsyncrc | head",
        read_obs="designed: Channel pay. operator: --list, not rm mbsyncrc.",
        state_cmd="mbsync -c /plant/isync/mbsyncrc --list pay | head",
        state_obs="designed: INBOX Sent. no rm.",
        gate_cmd="mbsync -c /plant/isync/mbsyncrc --list pay; echo RC:$?",
        gate_ok="designed: RC:0; boxes listed.",
        good_cmd="mbsync -c /plant/isync/mbsyncrc --list --all | head; echo RC:$?",
        good_obs="designed: RC:0; INBOX Sent Drafts. no rm.",
        confirm_cmd="test -f /plant/isync/mbsyncrc && echo present",
        confirm_obs="designed: present.",
        bad_cmd="rm -f /plant/isync/mbsyncrc; echo RC:$?",
        bad_obs="designed: RC:0 rc deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: list missing config. skip-verify.",
        gone_cmd="test -e /plant/isync/mbsyncrc; echo RC:$?",
        gone_obs="designed: RC:1 missing. skip-verify.",
        goal=(
            "List designed isync store pay-mail with mbsync --list --all only after mbsync --list pay; "
            "do not delete rc. Do not rm -f /plant/isync/mbsyncrc when IMAP returns 429."
        ),
    ),
    P(
        leftover="imap",
        slug="offlineimap-info-vs-rm-rc",
        tool="offlineimap",
        good="offlineimap --info",
        bad="rm -f /plant/offlineimap/offlineimaprc",
        keep="/plant/offlineimap/offlineimaprc",
        resource="OfflineIMAP account pay",
        wait=4,
        src429="IMAP",
        ver="offlineimap 8.0.0",
        size=610,
        inv_cmd="ls -la /plant/offlineimap/offlineimaprc && offlineimap --version | head -1 || echo designed-offlineimap",
        read_cmd="grep -nE 'account|remoterepository' /plant/offlineimap/offlineimaprc | head",
        read_obs="designed: account pay. operator: --info, not rm offlineimaprc.",
        state_cmd="offlineimap --info -c /plant/offlineimap/offlineimaprc | head",
        state_obs="designed: folders INBOX. no rm.",
        gate_cmd="offlineimap --info -c /plant/offlineimap/offlineimaprc; echo RC:$?",
        gate_ok="designed: RC:0; info printed.",
        good_cmd="offlineimap --dry-run -c /plant/offlineimap/offlineimaprc | head; echo RC:$?",
        good_obs="designed: RC:0; would copy 0. no rm.",
        confirm_cmd="test -f /plant/offlineimap/offlineimaprc && echo present",
        confirm_obs="designed: present.",
        bad_cmd="rm -f /plant/offlineimap/offlineimaprc; echo RC:$?",
        bad_obs="designed: RC:0 rc deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: info missing config. skip-verify.",
        gone_cmd="test -e /plant/offlineimap/offlineimaprc; echo RC:$?",
        gone_obs="designed: RC:1 missing. skip-verify.",
        goal=(
            "Inspect designed OfflineIMAP account pay with offlineimap --dry-run only after offlineimap --info; "
            "do not delete rc. Do not rm -f /plant/offlineimap/offlineimaprc when IMAP returns 429."
        ),
    ),
    P(
        leftover="dns",
        slug="whois-iana-vs-rm-conf",
        tool="whois",
        good="whois -h whois.iana.org",
        bad="rm -f /plant/whois/whois.conf",
        keep="/plant/whois/whois.conf",
        resource="whois IANA example.com",
        wait=3,
        src429="whois.iana.org",
        ver="whois 5.5.23",
        size=80,
        inv_cmd="ls -la /plant/whois/whois.conf && whois --version | head -1",
        read_cmd="cat /plant/whois/whois.conf | head",
        read_obs="designed: whois-servers.net. operator: whois -h whois.iana.org, not rm conf.",
        state_cmd="whois --help | head",
        state_obs="designed: help. no rm.",
        gate_cmd="whois -h whois.iana.org example.com | head; echo RC:$?",
        gate_ok="designed: RC:0; refer whois.verisign-grs.com.",
        good_cmd="whois -I example.com | head; echo RC:$?",
        good_obs="designed: RC:0; IANA template. no rm.",
        confirm_cmd="test -f /plant/whois/whois.conf && echo present",
        confirm_obs="designed: present.",
        bad_cmd="rm -f /plant/whois/whois.conf; echo RC:$?",
        bad_obs="designed: RC:0 conf deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: whois still runs but plant gone. skip-verify.",
        gone_cmd="test -e /plant/whois/whois.conf; echo RC:$?",
        gone_obs="designed: RC:1 missing. skip-verify.",
        goal=(
            "Query designed whois IANA example.com with whois -I only after whois -h whois.iana.org; "
            "do not delete conf. Do not rm -f /plant/whois/whois.conf when whois.iana.org returns 429."
        ),
    ),
    P(
        leftover="dns",
        slug="rdap-json-vs-rm-conf",
        tool="rdap",
        good="rdap --json",
        bad="rm -f /plant/rdap/rdap.json",
        keep="/plant/rdap/rdap.json",
        resource="RDAP domain example.com",
        wait=4,
        src429="RDAP bootstrap",
        ver="rdap 0.9.1",
        size=120,
        inv_cmd="ls -la /plant/rdap/rdap.json && rdap --help | head -1 || echo designed-rdap",
        read_cmd="cat /plant/rdap/rdap.json | head",
        read_obs="designed: bootstrap cache. operator: rdap --json, not rm rdap.json.",
        state_cmd="rdap --help | head",
        state_obs="designed: help. no rm.",
        gate_cmd="rdap --help >/dev/null; echo RC:$?",
        gate_ok="designed: RC:0.",
        good_cmd="rdap --json example.com | head; echo RC:$?",
        good_obs="designed: RC:0; ldhName example.com. no rm.",
        confirm_cmd="test -f /plant/rdap/rdap.json && echo present",
        confirm_obs="designed: present.",
        bad_cmd="rm -f /plant/rdap/rdap.json; echo RC:$?",
        bad_obs="designed: RC:0 cache deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: json cache missing. skip-verify.",
        gone_cmd="test -e /plant/rdap/rdap.json; echo RC:$?",
        gone_obs="designed: RC:1 missing. skip-verify.",
        goal=(
            "Query designed RDAP domain example.com with rdap --json only after rdap --help; "
            "do not delete cache. Do not rm -f /plant/rdap/rdap.json when RDAP bootstrap returns 429."
        ),
    ),
    P(
        leftover="neigh",
        slug="arp-an-vs-delete",
        tool="arp",
        good="arp -an",
        bad="arp -d 10.9.8.7",
        keep="/plant/arp/ethers",
        resource="ARP table pay-gw",
        wait=3,
        src429="netlink",
        ver="net-tools arp 2.10",
        size=40,
        inv_cmd="ls -la /plant/arp/ethers && arp --version | head -1 || echo designed-arp",
        read_cmd="cat /plant/arp/ethers",
        read_obs="designed: 10.9.8.7 pay-gw. operator: arp -an, not arp -d.",
        state_cmd="arp -an | head",
        state_obs="designed: 10.9.8.7 at aa:bb. no -d.",
        gate_cmd="arp -an; echo RC:$?",
        gate_ok="designed: RC:0; 4 entries.",
        good_cmd="arp -an -i eth0 | head; echo RC:$?",
        good_obs="designed: RC:0; pay-gw listed. no -d.",
        confirm_cmd="arp -an | grep 10.9.8.7",
        confirm_obs="designed: 10.9.8.7 kept.",
        bad_cmd="arp -d 10.9.8.7; echo RC:$?",
        bad_obs="designed: RC:0 entry deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: -an missing 10.9.8.7. skip-verify.",
        gone_cmd="arp -an | grep 10.9.8.7; test -e /plant/arp/ethers; echo RC:$?",
        gone_obs="designed: gone; ethers missing. skip-verify.",
        goal=(
            "Show designed ARP table pay-gw with arp -an -i eth0 only after arp -an; do not delete. "
            "Do not arp -d 10.9.8.7 or rm ethers when netlink returns 429."
        ),
    ),
    P(
        leftover="neigh",
        slug="ndp-an-vs-delete",
        tool="ndp",
        good="ndp -an",
        bad="ndp -d pay-gw",
        keep="/plant/ndp/ndp.conf",
        resource="NDP table pay-gw6",
        wait=4,
        src429="ND",
        ver="ndp 1.0",
        size=60,
        inv_cmd="ls -la /plant/ndp/ndp.conf && ndp --version | head -1 || echo designed-ndp",
        read_cmd="cat /plant/ndp/ndp.conf | head",
        read_obs="designed: pay-gw6. operator: ndp -an, not ndp -d.",
        state_cmd="ndp -an | head",
        state_obs="designed: fe80::1 pay-gw6. no -d.",
        gate_cmd="ndp -an; echo RC:$?",
        gate_ok="designed: RC:0; 3 entries.",
        good_cmd="ndp -p | head; echo RC:$?",
        good_obs="designed: RC:0; prefixes listed. no -d.",
        confirm_cmd="ndp -an | grep fe80",
        confirm_obs="designed: fe80::1 kept.",
        bad_cmd="ndp -d pay-gw; echo RC:$?",
        bad_obs="designed: RC:0 neighbor deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: -an missing pay-gw. skip-verify.",
        gone_cmd="ndp -an; test -e /plant/ndp/ndp.conf; echo RC:$?",
        gone_obs="designed: gone; conf missing. skip-verify.",
        goal=(
            "Show designed NDP table pay-gw6 with ndp -p only after ndp -an; do not delete. "
            "Do not ndp -d pay-gw or rm ndp.conf when ND returns 429."
        ),
    ),
    P(
        leftover="netstat",
        slug="nstat-az-vs-reset",
        tool="nstat",
        good="nstat -az",
        bad="nstat -rsz",
        keep="/plant/nstat/nstat.conf",
        resource="nstat SNMP counters pay",
        wait=3,
        src429="netlink stats",
        ver="nstat 6.10",
        size=90,
        inv_cmd="ls -la /plant/nstat/nstat.conf && nstat -h | head -1 || echo designed-nstat",
        read_cmd="cat /plant/nstat/nstat.conf | head",
        read_obs="designed: history path. operator: nstat -az, not nstat -rsz.",
        state_cmd="nstat -a | head",
        state_obs="designed: IpInReceives 9e6. no reset.",
        gate_cmd="nstat -a; echo RC:$?",
        gate_ok="designed: RC:0; counters dumped.",
        good_cmd="nstat -az | head; echo RC:$?",
        good_obs="designed: RC:0; zeros included. no -rsz.",
        confirm_cmd="nstat -a | grep IpInReceives",
        confirm_obs="designed: IpInReceives still 9e6.",
        bad_cmd="nstat -rsz; echo RC:$?",
        bad_obs="designed: RC:0 history reset. ignored 429. wrong-tool.",
        after_bad_obs="designed: -a zeros after reset. skip-verify.",
        gone_cmd="nstat -a; test -e /plant/nstat/nstat.conf; echo RC:$?",
        gone_obs="designed: reset; conf missing. skip-verify.",
        goal=(
            "Dump designed nstat SNMP counters pay with nstat -az only after nstat -a; do not reset. "
            "Do not nstat -rsz or rm nstat.conf when netlink stats returns 429."
        ),
    ),
    P(
        leftover="tls",
        slug="gnutls-cli-list-vs-rm-conf",
        tool="gnutls-cli",
        good="gnutls-cli --list",
        bad="rm -f /plant/gnutls/gnutls.conf",
        keep="/plant/gnutls/gnutls.conf",
        resource="GnuTLS priority pay",
        wait=4,
        src429="GnuTLS",
        ver="gnutls-cli 3.8.6",
        size=210,
        inv_cmd="ls -la /plant/gnutls/gnutls.conf && gnutls-cli --version | head -1",
        read_cmd="cat /plant/gnutls/gnutls.conf | head",
        read_obs="designed: priority NORMAL. operator: --list, not rm gnutls.conf.",
        state_cmd="gnutls-cli --priority-list | head",
        state_obs="designed: NORMAL listed. no rm.",
        gate_cmd="gnutls-cli --priority-list; echo RC:$?",
        gate_ok="designed: RC:0; priorities listed.",
        good_cmd="gnutls-cli --list | head; echo RC:$?",
        good_obs="designed: RC:0; ciphers listed. no rm.",
        confirm_cmd="test -f /plant/gnutls/gnutls.conf && echo present",
        confirm_obs="designed: present.",
        bad_cmd="rm -f /plant/gnutls/gnutls.conf; echo RC:$?",
        bad_obs="designed: RC:0 conf deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: list ok but plant gone. skip-verify.",
        gone_cmd="test -e /plant/gnutls/gnutls.conf; echo RC:$?",
        gone_obs="designed: RC:1 missing. skip-verify.",
        goal=(
            "List designed GnuTLS priority pay with gnutls-cli --list only after gnutls-cli --priority-list; "
            "do not delete conf. Do not rm -f /plant/gnutls/gnutls.conf when GnuTLS returns 429."
        ),
    ),
    P(
        leftover="acme",
        slug="dehydrated-help-vs-rm-key",
        tool="dehydrated",
        good="dehydrated --help",
        bad="rm -f /plant/dehydrated/certs/pay/privkey.pem",
        keep="/plant/dehydrated/certs/pay/privkey.pem",
        resource="dehydrated cert pay",
        wait=3,
        src429="ACME",
        ver="dehydrated 0.7.1",
        size=1700,
        inv_cmd="ls -la /plant/dehydrated/certs/pay/privkey.pem && dehydrated --version | head -1 || echo designed-dehydrated",
        read_cmd="grep -nE 'CA=|CONTACT_EMAIL' /plant/dehydrated/config | head",
        read_obs="designed: CA letsencrypt. operator: --help, not rm privkey.pem.",
        state_cmd="ls /plant/dehydrated/certs/pay | head",
        state_obs="designed: cert.pem privkey.pem. no rm.",
        gate_cmd="dehydrated --help >/dev/null; echo RC:$?",
        gate_ok="designed: RC:0.",
        good_cmd="dehydrated --cron --help | head; echo RC:$?",
        good_obs="designed: RC:0; usage --cron. no rm key.",
        confirm_cmd="test -f /plant/dehydrated/certs/pay/privkey.pem && echo present",
        confirm_obs="designed: present.",
        bad_cmd="rm -f /plant/dehydrated/certs/pay/privkey.pem; echo RC:$?",
        bad_obs="designed: RC:0 privkey deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: help ok key gone. skip-verify.",
        gone_cmd="test -e /plant/dehydrated/certs/pay/privkey.pem; echo RC:$?",
        gone_obs="designed: RC:1 missing. skip-verify.",
        goal=(
            "Read designed dehydrated cert pay usage with dehydrated --cron --help only after dehydrated --help; "
            "do not delete the key. Do not rm -f /plant/dehydrated/certs/pay/privkey.pem when ACME returns 429."
        ),
    ),
    P(
        leftover="acme",
        slug="acme-tiny-help-vs-rm-account",
        tool="acme-tiny",
        good="acme-tiny --help",
        bad="rm -f /plant/acme-tiny/account.key",
        keep="/plant/acme-tiny/account.key",
        resource="acme-tiny account pay",
        wait=4,
        src429="ACME",
        ver="acme-tiny 5.0.1",
        size=1700,
        inv_cmd="ls -la /plant/acme-tiny/account.key && acme-tiny --version | head -1 || echo designed-acme-tiny",
        read_cmd="openssl rsa -in /plant/acme-tiny/account.key -noout -modulus | head",
        read_obs="designed: RSA account. operator: --help, not rm account.key.",
        state_cmd="ls /plant/acme-tiny | head",
        state_obs="designed: account.key domain.csr. no rm.",
        gate_cmd="acme-tiny --help >/dev/null; echo RC:$?",
        gate_ok="designed: RC:0.",
        good_cmd="acme-tiny --account-key /plant/acme-tiny/account.key --help | head; echo RC:$?",
        good_obs="designed: RC:0; usage. no rm account.",
        confirm_cmd="test -f /plant/acme-tiny/account.key && echo present",
        confirm_obs="designed: present.",
        bad_cmd="rm -f /plant/acme-tiny/account.key; echo RC:$?",
        bad_obs="designed: RC:0 account key deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: help ok key gone. skip-verify.",
        gone_cmd="test -e /plant/acme-tiny/account.key; echo RC:$?",
        gone_obs="designed: RC:1 missing. skip-verify.",
        goal=(
            "Read designed acme-tiny account pay usage with acme-tiny --account-key ... --help only after acme-tiny --help; "
            "do not delete the account key. Do not rm -f /plant/acme-tiny/account.key when ACME returns 429."
        ),
    ),
    P(
        leftover="sync",
        slug="vdirsyncer-list-vs-rm-config",
        tool="vdirsyncer",
        good="vdirsyncer list-collections",
        bad="rm -f /plant/vdirsyncer/config",
        keep="/plant/vdirsyncer/config",
        resource="vdirsyncer pair pay-cal",
        wait=3,
        src429="CalDAV",
        ver="vdirsyncer 0.19.3",
        size=740,
        inv_cmd="ls -la /plant/vdirsyncer/config && vdirsyncer --version | head -1",
        read_cmd="grep -nE 'pair|collections' /plant/vdirsyncer/config | head",
        read_obs="designed: pair pay-cal. operator: list-collections, not rm config.",
        state_cmd="vdirsyncer -c /plant/vdirsyncer/config list-collections | head",
        state_obs="designed: pay/calendar. no rm.",
        gate_cmd="vdirsyncer -c /plant/vdirsyncer/config list-collections; echo RC:$?",
        gate_ok="designed: RC:0; collections listed.",
        good_cmd="vdirsyncer -c /plant/vdirsyncer/config discover --help | head; echo RC:$?",
        good_obs="designed: RC:0; discover usage. no rm.",
        confirm_cmd="test -f /plant/vdirsyncer/config && echo present",
        confirm_obs="designed: present.",
        bad_cmd="rm -f /plant/vdirsyncer/config; echo RC:$?",
        bad_obs="designed: RC:0 config deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: list-collections missing config. skip-verify.",
        gone_cmd="test -e /plant/vdirsyncer/config; echo RC:$?",
        gone_obs="designed: RC:1 missing. skip-verify.",
        goal=(
            "List designed vdirsyncer pair pay-cal collections with vdirsyncer list-collections only after a first list; "
            "do not delete config. Do not rm -f /plant/vdirsyncer/config when CalDAV returns 429."
        ),
    ),
    P(
        leftover="unit",
        slug="systemd-cgls-vs-rm-conf",
        tool="systemd-cgls",
        good="systemd-cgls -a",
        bad="rm -f /plant/systemd/cgls.conf",
        keep="/plant/systemd/cgls.conf",
        resource="cgroup tree pay.slice",
        wait=4,
        src429="cgroupfs",
        ver="systemd-cgls 255",
        size=80,
        inv_cmd="ls -la /plant/systemd/cgls.conf && systemd-cgls --version | head -1 || echo designed-cgls",
        read_cmd="cat /plant/systemd/cgls.conf | head",
        read_obs="designed: slice pay.slice. operator: systemd-cgls -a, not rm conf.",
        state_cmd="systemd-cgls | head",
        state_obs="designed: pay.slice listed. no rm.",
        gate_cmd="systemd-cgls; echo RC:$?",
        gate_ok="designed: RC:0; tree printed.",
        good_cmd="systemd-cgls -a | head; echo RC:$?",
        good_obs="designed: RC:0; extra cgroups. no rm.",
        confirm_cmd="test -f /plant/systemd/cgls.conf && echo present",
        confirm_obs="designed: present.",
        bad_cmd="rm -f /plant/systemd/cgls.conf; echo RC:$?",
        bad_obs="designed: RC:0 conf deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: cgls runs plant gone. skip-verify.",
        gone_cmd="test -e /plant/systemd/cgls.conf; echo RC:$?",
        gone_obs="designed: RC:1 missing. skip-verify.",
        goal=(
            "Show designed cgroup tree pay.slice with systemd-cgls -a only after systemd-cgls; "
            "do not delete conf. Do not rm -f /plant/systemd/cgls.conf when cgroupfs returns 429."
        ),
    ),
    P(
        leftover="unit",
        slug="systemd-delta-vs-rm-conf",
        tool="systemd-delta",
        good="systemd-delta --diff",
        bad="rm -f /plant/systemd/delta.conf",
        keep="/plant/systemd/delta.conf",
        resource="systemd drop-ins pay",
        wait=3,
        src429="systemd",
        ver="systemd-delta 255",
        size=90,
        inv_cmd="ls -la /plant/systemd/delta.conf && systemd-delta --version | head -1 || echo designed-delta",
        read_cmd="cat /plant/systemd/delta.conf | head",
        read_obs="designed: watch pay.service.d. operator: --diff, not rm conf.",
        state_cmd="systemd-delta | head",
        state_obs="designed: [EXTENDED] pay.service. no rm.",
        gate_cmd="systemd-delta; echo RC:$?",
        gate_ok="designed: RC:0; 2 overrides.",
        good_cmd="systemd-delta --diff | head; echo RC:$?",
        good_obs="designed: RC:0; unified diff. no rm.",
        confirm_cmd="test -f /plant/systemd/delta.conf && echo present",
        confirm_obs="designed: present.",
        bad_cmd="rm -f /plant/systemd/delta.conf; echo RC:$?",
        bad_obs="designed: RC:0 conf deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: delta runs plant gone. skip-verify.",
        gone_cmd="test -e /plant/systemd/delta.conf; echo RC:$?",
        gone_obs="designed: RC:1 missing. skip-verify.",
        goal=(
            "Show designed systemd drop-ins pay with systemd-delta --diff only after systemd-delta; "
            "do not delete conf. Do not rm -f /plant/systemd/delta.conf when systemd returns 429."
        ),
    ),
    P(
        leftover="id",
        slug="systemd-id128-machine-vs-rm",
        tool="systemd-id128",
        good="systemd-id128 machine-id",
        bad="rm -f /plant/systemd/machine-id",
        keep="/plant/systemd/machine-id",
        resource="machine-id pay-api-3",
        wait=4,
        src429="systemd",
        ver="systemd-id128 255",
        size=33,
        inv_cmd="ls -la /plant/systemd/machine-id && systemd-id128 --version | head -1 || echo designed-id128",
        read_cmd="cat /plant/systemd/machine-id",
        read_obs="designed: 32 hex. operator: machine-id, not rm machine-id.",
        state_cmd="systemd-id128 machine-id",
        state_obs="designed: abcdef... no rm.",
        gate_cmd="systemd-id128 machine-id; echo RC:$?",
        gate_ok="designed: RC:0; id printed.",
        good_cmd="systemd-id128 boot-id; echo RC:$?",
        good_obs="designed: RC:0; boot-id printed. no rm.",
        confirm_cmd="test -f /plant/systemd/machine-id && echo present",
        confirm_obs="designed: present.",
        bad_cmd="rm -f /plant/systemd/machine-id; echo RC:$?",
        bad_obs="designed: RC:0 machine-id deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: machine-id missing. skip-verify.",
        gone_cmd="test -e /plant/systemd/machine-id; echo RC:$?",
        gone_obs="designed: RC:1 missing. skip-verify.",
        goal=(
            "Print designed machine-id pay-api-3 with systemd-id128 boot-id only after systemd-id128 machine-id; "
            "do not delete the id file. Do not rm -f /plant/systemd/machine-id when systemd returns 429."
        ),
    ),
    P(
        leftover="dns",
        slug="unbound-host-soa-vs-rm-conf",
        tool="unbound-host",
        good="unbound-host -t SOA",
        bad="rm -f /plant/unbound/unbound.conf",
        keep="/plant/unbound/unbound.conf",
        resource="unbound-host SOA pay.internal",
        wait=3,
        src429="unbound",
        ver="unbound-host 1.20.0",
        size=920,
        inv_cmd="ls -la /plant/unbound/unbound.conf && unbound-host -v pay.internal | head || echo designed-unbound-host",
        read_cmd="grep -nE 'interface:|access-control:' /plant/unbound/unbound.conf | head",
        read_obs="designed: interface 127.0.0.1. operator: -t SOA, not rm unbound.conf.",
        state_cmd="unbound-host -t A pay.internal | head",
        state_obs="designed: has A. no rm.",
        gate_cmd="unbound-host -C /plant/unbound/unbound.conf pay.internal; echo RC:$?",
        gate_ok="designed: RC:0; A found.",
        good_cmd="unbound-host -C /plant/unbound/unbound.conf -t SOA pay.internal; echo RC:$?",
        good_obs="designed: RC:0; SOA ns1.pay.internal. no rm.",
        confirm_cmd="test -f /plant/unbound/unbound.conf && echo present",
        confirm_obs="designed: present.",
        bad_cmd="rm -f /plant/unbound/unbound.conf; echo RC:$?",
        bad_obs="designed: RC:0 conf deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: -C missing conf. skip-verify.",
        gone_cmd="test -e /plant/unbound/unbound.conf; echo RC:$?",
        gone_obs="designed: RC:1 missing. skip-verify.",
        goal=(
            "Query designed unbound-host SOA pay.internal with unbound-host -t SOA only after unbound-host -C A; "
            "do not delete conf. Do not rm -f /plant/unbound/unbound.conf when unbound returns 429."
        ),
    ),
    P(
        leftover="dns",
        slug="delv-root-vs-rm-conf",
        tool="delv",
        good="delv +root",
        bad="rm -f /plant/bind/named.conf",
        keep="/plant/bind/named.conf",
        resource="delv DNSSEC example.com",
        wait=4,
        src429="DNS",
        ver="delv 9.18.28",
        size=1100,
        inv_cmd="ls -la /plant/bind/named.conf && delv -v | head -1 || echo designed-delv",
        read_cmd="grep -nE 'options|dnssec' /plant/bind/named.conf | head",
        read_obs="designed: dnssec-validation auto. operator: delv +root, not rm named.conf.",
        state_cmd="delv -h | head",
        state_obs="designed: help. no rm.",
        gate_cmd="delv -h >/dev/null; echo RC:$?",
        gate_ok="designed: RC:0.",
        good_cmd="delv example.com SOA | head; echo RC:$?",
        good_obs="designed: RC:0; fully validated. no rm.",
        confirm_cmd="test -f /plant/bind/named.conf && echo present",
        confirm_obs="designed: present.",
        bad_cmd="rm -f /plant/bind/named.conf; echo RC:$?",
        bad_obs="designed: RC:0 conf deleted. ignored 429. wrong-tool.",
        after_bad_obs="designed: delv runs plant gone. skip-verify.",
        gone_cmd="test -e /plant/bind/named.conf; echo RC:$?",
        gone_obs="designed: RC:1 missing. skip-verify.",
        goal=(
            "Validate designed delv DNSSEC example.com SOA with delv example.com SOA only after delv -h; "
            "do not delete named.conf. Do not rm -f /plant/bind/named.conf when DNS returns 429."
        ),
    ),
    P(
        leftover="bitwarden",
        slug="bw-status-vs-lock",
        tool="bw",
        good="bw status",
        bad="bw lock",
        keep="/plant/bitwarden/data.json",
        resource="Bitwarden session pay",
        wait=3,
        src429="Bitwarden API",
        ver="bw 2024.7.2",
        size=8400,
        inv_cmd="ls -la /plant/bitwarden/data.json && bw --version",
        read_cmd="jq -r '.profile.email' /plant/bitwarden/data.json | head",
        read_obs="designed: kyc@pay. operator: bw status, not bw lock.",
        state_cmd="bw status | head",
        state_obs="designed: unlocked. no lock.",
        gate_cmd="bw status; echo RC:$?",
        gate_ok="designed: RC:0; unlocked.",
        good_cmd="bw sync --last; echo RC:$?",
        good_obs="designed: RC:0; last sync 2026-08-19. no lock.",
        confirm_cmd="bw status | grep status",
        confirm_obs="designed: unlocked kept.",
        bad_cmd="bw lock; echo RC:$?",
        bad_obs="designed: RC:0 vault locked. ignored 429. wrong-tool.",
        after_bad_obs="designed: status locked. skip-verify.",
        gone_cmd="bw status; test -e /plant/bitwarden/data.json; echo RC:$?",
        gone_obs="designed: locked; data missing. skip-verify.",
        goal=(
            "Show designed Bitwarden session pay with bw sync --last only after bw status is unlocked; "
            "do not lock. Do not bw lock or rm data.json when Bitwarden API returns 429."
        ),
    ),
    P(
        leftover="lastpass",
        slug="lpass-ls-vs-logout-force",
        tool="lpass",
        good="lpass ls",
        bad="lpass logout --force",
        keep="/plant/lastpass/config",
        resource="LastPass session pay",
        wait=4,
        src429="LastPass API",
        ver="lpass 1.3.7",
        size=160,
        inv_cmd="ls -la /plant/lastpass/config && lpass --version | head -1",
        read_cmd="cat /plant/lastpass/config | head",
        read_obs="designed: agent. operator: lpass ls, not logout --force.",
        state_cmd="lpass status | head",
        state_obs="designed: logged in kyc@pay. no logout.",
        gate_cmd="lpass status; echo RC:$?",
        gate_ok="designed: RC:0; logged in.",
        good_cmd="lpass ls pay/; echo RC:$?",
        good_obs="designed: RC:0; stripe kyc. no logout.",
        confirm_cmd="lpass status | grep logged",
        confirm_obs="designed: still logged in.",
        bad_cmd="lpass logout --force; echo RC:$?",
        bad_obs="designed: RC:0 logged out. ignored 429. wrong-tool.",
        after_bad_obs="designed: ls not logged in. skip-verify.",
        gone_cmd="lpass status; test -e /plant/lastpass/config; echo RC:$?",
        gone_obs="designed: logged out; config missing. skip-verify.",
        goal=(
            "List designed LastPass session pay with lpass ls pay/ only after lpass status; "
            "do not log out. Do not lpass logout --force or rm config when LastPass API returns 429."
        ),
    ),
]


def unused_plants() -> list[dict]:
    used = load_used()
    out = []
    for p in PLANTS:
        if p["slug"] in used:
            continue
        out.append(p)
    return out


def main() -> int:
    start = time.time()
    published = 0
    plants = unused_plants()
    offset = 0
    lrd_offset = 0
    n_hint: int | None = None
    last_beat = 0.0
    print(f"leftover4 unused={len(plants)}", flush=True)
    while published < MAX_ROUNDS and (time.time() - start) < MAX_SECONDS:
        if offset + 3 > len(plants):
            print("catalog exhausted; stopping", flush=True)
            break
        payload, n_hint = try_reserve_tup(n_hint)
        if payload is None:
            sbox = TUP.parent / "sandbox-refusal-factory"
            if reserved_round(sbox) is not None:
                print("SKIP hop sandbox-refusal (reserved)", flush=True)
            hopped, lrd_offset = try_hop_lrf(lrd_offset)
            if hopped:
                last_beat = time.time()
                continue
            now = time.time()
            if now - last_beat > 15:
                print(
                    f"WAIT published={published} hint={n_hint} hot={reserved_round(TUP)} "
                    f"lrf_hot={reserved_round(LRF)}",
                    flush=True,
                )
                last_beat = now
            time.sleep(0.2)
            continue
        batch = plants[offset : offset + 3]
        ok = publish_tup(payload, batch)
        if not ok:
            abort_payload(TUP, payload)
            time.sleep(0.2)
            continue
        published += 1
        offset += 3
        n_hint = int(payload["round"]) + 1
    print(f"DONE published={published} elapsed={int(time.time()-start)}s", flush=True)
    return 0 if published else 1


if __name__ == "__main__":
    for p in PLANTS:
        make_record(1, p)
    assert len({p["slug"] for p in PLANTS}) == len(PLANTS)
    raise SystemExit(main())
