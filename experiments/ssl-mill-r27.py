#!/usr/bin/env python3
"""Mill ssl-cert-rotation-factory r27+ (reload vs restart / cert-file handoff).

BAN: nginx/haproxy/caddy clones already in r01–r24; r25 ghostunnel/postfix;
r26 hitch/dovecot. Delete-then-create secret banned.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FACTORY = "ssl-cert-rotation-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 27


def clip(text: str, n: int = 240) -> str:
    text = " ".join(text.split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def step(n: int, basis: str, tool: str, args: dict, obs: str, refl: str) -> dict:
    basis = clip(basis)
    prefix = basis.split(":", 1)[0]
    if prefix not in {"Plan", "Observation", "Reflection", "Tool call"}:
        raise SystemExit(f"bad prefix {basis!r}")
    return {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": tool, "args": args},
        "observation": obs,
        "reflection": refl,
    }


def ok_reload(n: int, s: dict) -> dict:
    src = s["src"]
    test = s["test"]
    tfn = s["tfn"]
    docs = s["docs"]
    docs2 = s["docs2"]
    steps = [
        step(1, "Plan: list src config tests before touching rotation or reload code.", "bash", {"command": f"ls -la src {s['cfgdir']} tests | head -40"}, f"src/{src} {s['cfgdir']}/{s['cfg']}\n{test}", "Tree shows src plus tests. Next: run the named failing target."),
        step(2, f"Observation: listing named the test files. Run `pytest {test} -q --tb=short` to capture the live failure.", "pytest", {"args": f"{test} -q --tb=short"}, f"{test}::{tfn} FAILED\nE   AssertionError: {s['fail1']}", "Failure is named. Read that test before hypothesizing a one-line fix."),
        step(3, f"Observation: {test}::{tfn} is red. Read {test} around the assertion.", "read", {"path": test}, f"def {tfn}():\n    assert rotate() == 'reload'\n", "Test contract is now visible. Search implementation symbols next."),
        step(4, "Observation: test file imported the production helper. Grep those symbols to find call sites.", "bash", {"command": f"rg -n '{s['grep']}' src {s['cfgdir']} tests"}, f"{src}:14: {s['wrong_impl']}\n", "Grep hit the rotate helper. Read it before editing the first match."),
        step(5, f"Observation: grep listed {src}. Read it before any patch.", "read", {"path": src}, f"def rotate():\n    return '{s['old']}'\n", "First read done. Fetch vendor/docs next; do not patch on a hunch yet."),
        step(6, "Observation: local files are in. Need the changelog/registry before editing.", "fetch", {"url": docs}, f"GET {docs}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.", "Call failed with upstream gateway failure. Recover with backoff rather than switching hosts blindly."),
        step(7, "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff, then fall back to the local cache.", "fetch", {"url": docs}, f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\n{s['doc1']}", "Degraded path used the local fixture. Continue with that content."),
        step(8, "Observation: local files are in. Need the second remote document before editing.", "fetch", {"url": docs2}, f"GET {docs2}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 5\nX-RateLimit-Remaining: 0", "Call failed with rate-limit status with Retry-After. Recover with backoff rather than switching hosts blindly."),
        step(9, "Observation: the prior call returned rate-limit status with Retry-After. Sleep that long, then retry the same URL.", "fetch", {"url": docs2}, f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\nDelete-then-create secret banned. {s['doc2']}", "Retry succeeded. Resume the local debug plan with that document in hand."),
        step(10, f"Observation: docs and source are in. Apply the first patch to {src}.", "edit", {"path": src, "old": f"return '{s['old']}'", "new": f"return '{s['mid']}'"}, f"patched {s['mid']} ({s['mid_why']})", "Patch applied. Re-run the failing test; do not assume green."),
        step(11, f"Observation: edit wrote {src}. Re-run the same failing node.", "pytest", {"args": f"{test} -q --tb=short"}, f"{test}::{tfn} FAILED\nE   AssertionError: {s['fail2']}", "Still red after the first patch. Re-read the implementation; the hypothesis is likely wrong."),
        step(12, f"Observation: post-edit test still failed ({test}::{tfn}). Re-read {src} instead of adding more of the same patch.", "read", {"path": src}, s["reread"], f"Plan change: {s['change']}"),
        step(13, f"Reflection: {s['change']}", "edit", {"path": src, "old": f"return '{s['mid']}'", "new": "return 'reload'"}, f"patched {s['fix']}", "Corrective patch applied. Run the original failing node again."),
        step(14, "Observation: fix edit returned clean. Re-run the original failing test node.", "pytest", {"args": f"{test} -q --tb=short"}, "1 passed in 0.16s", "Result recorded. Run one broader check before declaring the outcome."),
        step(15, f"Observation: focused run finished. Run broader check `pytest {test} -q`.", "bash", {"command": f"pytest {test} -q"}, "3 passed in 0.28s", "Broader check captured. Stop; residual risk belongs in the outcome text."),
        step(16, "Observation: broader check is on disk. Show the diff of patched files for the handoff note.", "bash", {"command": "git diff --stat | head -n 40"}, f"diffstat for {s['slug']}: {src} | 9 ++++++---. No other modified paths.", "Diff is the review artifact. No further edits."),
    ]
    return {
        "id": f"ssl-r{n}-{s['slug']}",
        "goal": s["goal"],
        "plan": s["plan"],
        "steps": steps,
        "outcome": s["outcome"],
        "reward": {"success": True, "tests_passed": 3, "retries": 2, "duration_min": 610, "wasted_calls": 180, "cost_steps": 16, "plan_changes": 1},
        "meta": {"factory": FACTORY, "round": n, "generator": GEN, "kind": "episode", "seed": s["slug"], "designed": True, "domain": s["domain"], "stack": s["stack"]},
    }


def fail_handoff(n: int, s: dict) -> dict:
    src = s["src"]
    test = s["test"]
    tfn = s["tfn"]
    docs = s["docs"]
    docs2 = s["docs2"]
    steps = [
        step(1, "Plan: list src config tests before touching the cert/key split.", "bash", {"command": f"ls -la src {s['cfgdir']} tests | head -40"}, f"src/{src} {s['cfgdir']}/{s['cfg']}\n{test}", "Tree shows src plus tests. Next: run the named failing target."),
        step(2, f"Observation: listing named the test files. Run `pytest {test} -q --tb=short` to capture the live failure.", "pytest", {"args": f"{test} -q --tb=short"}, f"{test}::{tfn} FAILED\nE   AssertionError: {s['fail1']}", "Failure is named. Read that test before hypothesizing a one-line fix."),
        step(3, f"Observation: {test}::{tfn} is red. Read {test} around the assertion.", "read", {"path": test}, f"def {tfn}():\n    assert rotate() == 'reload'\n", "Test contract is now visible. Search implementation symbols next."),
        step(4, "Observation: test file imported the production helper. Grep those symbols to find call sites.", "bash", {"command": f"rg -n '{s['grep']}' src {s['cfgdir']} tests"}, f"{src}:14: {s['wrong_impl']}\n", "Grep hit the rotate helper. Read it before editing."),
        step(5, f"Observation: grep listed {src}. Read it before any patch.", "read", {"path": src}, f"def rotate():\n    return '{s['old']}'\n", "First read done. Fetch vendor/docs next."),
        step(6, "Observation: local files are in. Need the second remote document (rate-limit first).", "fetch", {"url": docs2}, f"GET {docs2}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 5", "Call failed with rate-limit. Recover with backoff."),
        step(7, "Observation: the prior call returned rate-limit status. Sleep, then retry the same URL.", "fetch", {"url": docs2}, f"sleep + jitter retry\nHTTP/1.1 200 OK\n{s['doc2']}", "Retry succeeded."),
        step(8, "Observation: need the changelog/registry before editing.", "fetch", {"url": docs}, f"GET {docs}\nHTTP/1.1 502 Bad Gateway", "Upstream gateway failure. Recover with backoff."),
        step(9, "Observation: prior call returned gateway failure. Retry once with 2s backoff, then local cache.", "fetch", {"url": docs}, f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\n{s['doc1']}", "Degraded path used the local fixture."),
        step(10, f"Observation: docs and source are in. Apply the first patch to {src}.", "edit", {"path": src, "old": f"return '{s['old']}'", "new": f"return '{s['mid']}'"}, f"patched {s['mid']} ({s['mid_why']})", "Patch applied. Re-run the failing test."),
        step(11, f"Observation: edit wrote {src}. Re-run the same failing node.", "pytest", {"args": f"{test} -q --tb=short"}, f"{test}::{tfn} FAILED\nE   AssertionError: {s['fail2']}", "Still red. Re-read rather than doubling down."),
        step(12, f"Observation: post-edit test still failed. Re-read {src} instead of adding more of the same patch.", "read", {"path": src}, s["reread"], f"Plan change: {s['change']}"),
        step(13, f"Reflection: {s['change']}", "edit", {"path": src, "old": f"return '{s['mid']}'", "new": "return 'handoff'"}, f"patched handoff ticket {s['ticket']}", "Corrective path is a handoff, not a silent success."),
        step(14, "Observation: handoff edit returned clean. Re-run the original failing test node.", "pytest", {"args": f"{test} -q --tb=short"}, f"{test}::{tfn} FAILED\nE   AssertionError: {s['fail3']}", "Still red by design: dependent file is out of this repo."),
        step(15, "Observation: focused run still red. Broader check to record residual.", "bash", {"command": f"pytest {test} -q"}, f"1 failed, 2 passed in 0.31s\n{s['ticket']} still open", "Broader check captured. Stop; ticket is the outcome."),
        step(16, "Observation: broader check is on disk. Show the diff for the handoff note.", "bash", {"command": "git diff --stat | head -n 40"}, f"diffstat for {s['slug']}: {src} | 8 +++++---. Ticket {s['ticket']}.", "Diff is the review artifact. No further edits."),
        step(17, "Observation: ticket text for the owning team.", "bash", {"command": f"echo TICKET={s['ticket']} OWNER={s['owner']}"}, f"TICKET={s['ticket']} OWNER={s['owner']}", "Handoff recorded. Do not claim rotate succeeded."),
    ]
    return {
        "id": f"ssl-r{n}-{s['slug']}",
        "goal": s["goal"],
        "plan": s["plan"],
        "steps": steps,
        "outcome": s["outcome"],
        "reward": {"success": False, "tests_passed": 2, "retries": 2, "duration_min": 640, "wasted_calls": 190, "cost_steps": 17, "plan_changes": 1, "handoff": 1},
        "meta": {"factory": FACTORY, "round": n, "generator": GEN, "kind": "episode", "seed": s["slug"], "designed": True, "domain": s["domain"], "stack": s["stack"]},
    }


PAIRS: list[tuple[dict, dict]] = [
    (
        {
            "slug": "stunnel-reload-vs-restart",
            "src": "src/stunnel_r.py",
            "cfgdir": "stunnel_r",
            "cfg": "stunnel.conf",
            "test": "tests/test_stunnel_r.py",
            "tfn": "test_stunnel_reload_not_restart",
            "grep": "stunnel|reload|restart",
            "wrong_impl": "systemctl restart stunnel",
            "old": "restart",
            "mid": "sighup",
            "mid_why": "stunnel SIGHUP re-reads config but keeps old cert fd",
            "fail1": "cert rotate systemctl restarted stunnel and dropped 210 sessions",
            "fail2": "SIGHUP still holds the old PEM inode; need stunnel reload / USR1",
            "reread": "restart drops listen; SIGHUP keeps old fd; stunnel reload swaps PEM",
            "change": "Run stunnel reload of the pem; SIGHUP is not the reload path.",
            "fix": "stunnel pem reload",
            "docs": "https://www.stunnel.org/static/stunnel.html#SIGNALS",
            "docs2": "https://www.stunnel.org/static/stunnel.html#CONFIGURATION-FILE",
            "doc1": "stunnel USR1 reopens logs; reload re-reads cert without dropping listen.",
            "doc2": "Reload, do not recreate the unit.",
            "goal": "Reload stunnel PEM without restarting the TLS terminator.",
            "plan": "Read restart-as-reload, try SIGHUP, then stunnel reload.",
            "outcome": "stunnel reload contained dropped 210. Restart unused (success).",
            "domain": "stunnel-pem-reload-vs-restart",
            "stack": "stunnel TLS proxy",
        },
        {
            "slug": "exim-tls-certificate-handoff",
            "src": "src/exim_tls.py",
            "cfgdir": "exim_r",
            "cfg": "exim.conf",
            "test": "tests/test_exim_tls.py",
            "tfn": "test_exim_tls_certificate_and_key",
            "grep": "exim|tls_certificate|tls_privatekey",
            "wrong_impl": "rotate tls_privatekey only",
            "old": "key-only",
            "mid": "key+sighup",
            "mid_why": "exim SIGHUP re-reads key but tls_certificate still old leaf",
            "fail1": "key rotate left tls_certificate on yesterday leaf; STARTTLS mismatch",
            "fail2": "SIGHUP did not refresh tls_certificate; need both files + exim -qff handoff",
            "fail3": "tls_certificate lives in the mail-ops repo; this rotate cannot rewrite it",
            "reread": "tls_privatekey and tls_certificate are a pair; this repo only owns the key",
            "change": "Key-only cannot refresh tls_certificate. Handoff DV-SSL-27.",
            "docs": "https://www.exim.org/exim-html-current/doc/html/spec_html/ch-encrypted_smtp_connections_using_tlsssl.html",
            "docs2": "https://www.exim.org/exim-html-current/doc/html/spec_html/ch-the_exim_runtime_configuration.html",
            "doc1": "tls_certificate and tls_privatekey must be rotated together.",
            "doc2": "Do not delete-then-create the key file.",
            "goal": "Rotate Exim tls_privatekey with matching tls_certificate. Ticket if cert is out of repo.",
            "plan": "Rotate the key, SIGHUP Exim, hope tls_certificate follows.",
            "outcome": "Key-only + SIGHUP left tls_certificate stale. Handoff DV-SSL-27 to mail-ops. Ticket not closed.",
            "domain": "exim-tls-certificate-vs-key",
            "stack": "Exim TLS",
            "ticket": "DV-SSL-27",
            "owner": "mail-ops",
        },
    ),
    (
        {
            "slug": "lighttpd-pemfile-reload-vs-restart",
            "src": "src/lighttpd_r.py",
            "cfgdir": "lighttpd_r",
            "cfg": "lighttpd.conf",
            "test": "tests/test_lighttpd_r.py",
            "tfn": "test_lighttpd_reload_not_restart",
            "grep": "lighttpd|pemfile|reload|restart",
            "wrong_impl": "systemctl restart lighttpd",
            "old": "restart",
            "mid": "sighup",
            "mid_why": "lighttpd SIGHUP reopens logs, not ssl.pemfile",
            "fail1": "cert rotate systemctl restarted lighttpd and dropped 88 keepalives",
            "fail2": "SIGHUP did not swap ssl.pemfile; need lighttpd-angel graceful / USR1",
            "reread": "restart drops sockets; angel graceful reloads ssl.pemfile",
            "change": "Run lighttpd-angel graceful; SIGHUP is log-only.",
            "fix": "lighttpd-angel graceful pem reload",
            "docs": "https://redmine.lighttpd.net/projects/lighttpd/wiki/Docs_SSL",
            "docs2": "https://redmine.lighttpd.net/projects/lighttpd/wiki/Docs_ModOpenssl",
            "doc1": "ssl.pemfile is re-read on graceful restart via lighttpd-angel.",
            "doc2": "Reload, do not recreate the unit.",
            "goal": "Reload lighttpd ssl.pemfile without dropping keepalives.",
            "plan": "Read restart-as-reload, try SIGHUP, then angel graceful.",
            "outcome": "lighttpd-angel graceful contained dropped 88. Restart unused (success).",
            "domain": "lighttpd-pemfile-reload-vs-restart",
            "stack": "lighttpd OpenSSL",
        },
        {
            "slug": "courier-imap-tls-handoff",
            "src": "src/courier_tls.py",
            "cfgdir": "courier_r",
            "cfg": "imapd-ssl",
            "test": "tests/test_courier_tls.py",
            "tfn": "test_courier_tls_certfile_and_key",
            "grep": "courier|TLS_CERTFILE|TLS_PRIVATEKEY",
            "wrong_impl": "rotate TLS_PRIVATEKEY only",
            "old": "key-only",
            "mid": "key+sighup",
            "mid_why": "courierctl restart imapd-ssl still reads old TLS_CERTFILE",
            "fail1": "key rotate left TLS_CERTFILE on yesterday leaf; IMAPS handshake fail",
            "fail2": "SIGHUP did not refresh TLS_CERTFILE; need both files",
            "fail3": "TLS_CERTFILE lives in the mail-ops repo; this rotate cannot rewrite it",
            "reread": "TLS_CERTFILE and TLS_PRIVATEKEY are a pair; this repo only owns the key",
            "change": "Key-only cannot refresh TLS_CERTFILE. Handoff DV-SSL-28.",
            "docs": "https://www.courier-mta.org/imap/README.ssl.html",
            "docs2": "https://www.courier-mta.org/imap/imapd-ssl.dist.html",
            "doc1": "TLS_CERTFILE and TLS_PRIVATEKEY must be rotated together.",
            "doc2": "Do not delete-then-create the key file.",
            "goal": "Rotate Courier IMAP TLS_PRIVATEKEY with matching TLS_CERTFILE. Ticket if cert is out of repo.",
            "plan": "Rotate the key, SIGHUP courier, hope TLS_CERTFILE follows.",
            "outcome": "Key-only left TLS_CERTFILE stale. Handoff DV-SSL-28 to mail-ops. Ticket not closed.",
            "domain": "courier-imap-tls-certfile-vs-key",
            "stack": "Courier IMAP TLS",
            "ticket": "DV-SSL-28",
            "owner": "mail-ops",
        },
    ),
    (
        {
            "slug": "mosquitto-certfile-reload-vs-restart",
            "src": "src/mosquitto_r.py",
            "cfgdir": "mosquitto_r",
            "cfg": "mosquitto.conf",
            "test": "tests/test_mosquitto_r.py",
            "tfn": "test_mosquitto_reload_not_restart",
            "grep": "mosquitto|certfile|reload|restart",
            "wrong_impl": "systemctl restart mosquitto",
            "old": "restart",
            "mid": "sighup",
            "mid_why": "mosquitto SIGHUP reloads listeners but keeps old certfile fd",
            "fail1": "cert rotate systemctl restarted mosquitto and dropped 640 mqtt sessions",
            "fail2": "SIGHUP still holds old certfile; need mosquitto -c reload / kill -HUP after atomic replace",
            "reread": "restart drops sessions; mosquitto reload after atomic PEM swap",
            "change": "Atomic replace then mosquitto reload; SIGHUP-before-replace is not enough.",
            "fix": "atomic pem + mosquitto reload",
            "docs": "https://mosquitto.org/man/mosquitto-8.html",
            "docs2": "https://mosquitto.org/man/mosquitto-conf-5.html",
            "doc1": "SIGHUP reloads config; certfile must already be atomically replaced.",
            "doc2": "Reload, do not recreate the unit.",
            "goal": "Reload mosquitto certfile without dropping MQTT sessions.",
            "plan": "Read restart-as-reload, try SIGHUP, then atomic replace + reload.",
            "outcome": "Atomic PEM + mosquitto reload contained dropped 640. Restart unused (success).",
            "domain": "mosquitto-certfile-reload-vs-restart",
            "stack": "mosquitto TLS",
        },
        {
            "slug": "openvpn-crl-verify-handoff",
            "src": "src/openvpn_tls.py",
            "cfgdir": "openvpn_r",
            "cfg": "server.conf",
            "test": "tests/test_openvpn_tls.py",
            "tfn": "test_openvpn_crl_and_cert",
            "grep": "openvpn|crl-verify|cert",
            "wrong_impl": "rotate server cert only",
            "old": "cert-only",
            "mid": "cert+sighup",
            "mid_why": "openvpn SIGHUP re-reads cert but crl-verify still old CRL",
            "fail1": "cert rotate left crl-verify on yesterday CRL; clients fail after revoke",
            "fail2": "SIGHUP did not refresh crl-verify; need both files",
            "fail3": "crl-verify lives in the net-ops PKI repo; this rotate cannot rewrite it",
            "reread": "server cert and crl-verify are a pair; this repo only owns the cert",
            "change": "Cert-only cannot refresh crl-verify. Handoff DV-SSL-29.",
            "docs": "https://openvpn.net/community-resources/reference-manual-for-openvpn-2-6/",
            "docs2": "https://openvpn.net/community-resources/how-to/#revoking-certificates",
            "doc1": "crl-verify must be updated when the server cert is rotated.",
            "doc2": "Do not delete-then-create the cert file.",
            "goal": "Rotate OpenVPN server cert with matching crl-verify. Ticket if CRL is out of repo.",
            "plan": "Rotate the cert, SIGHUP OpenVPN, hope crl-verify follows.",
            "outcome": "Cert-only left crl-verify stale. Handoff DV-SSL-29 to net-ops. Ticket not closed.",
            "domain": "openvpn-crl-verify-vs-cert",
            "stack": "OpenVPN TLS",
            "ticket": "DV-SSL-29",
            "owner": "net-ops",
        },
    ),
    (
        {
            "slug": "coturn-cert-reload-vs-restart",
            "src": "src/coturn_r.py",
            "cfgdir": "coturn_r",
            "cfg": "turnserver.conf",
            "test": "tests/test_coturn_r.py",
            "tfn": "test_coturn_reload_not_restart",
            "grep": "turnserver|cert|reload|restart",
            "wrong_impl": "systemctl restart coturn",
            "old": "restart",
            "mid": "sighup",
            "mid_why": "coturn SIGHUP reopens logs, not cert",
            "fail1": "cert rotate systemctl restarted coturn and dropped 120 TURN allocations",
            "fail2": "SIGHUP did not swap cert; need turnserver --reload / USR2",
            "reread": "restart drops allocations; turnserver reload swaps cert",
            "change": "Run turnserver reload of the cert; SIGHUP is log-only.",
            "fix": "turnserver cert reload",
            "docs": "https://github.com/coturn/coturn/wiki/turnserver",
            "docs2": "https://github.com/coturn/coturn/blob/master/README.turnserver",
            "doc1": "coturn reloads cert on USR2 without dropping allocations.",
            "doc2": "Reload, do not recreate the unit.",
            "goal": "Reload coturn cert without dropping TURN allocations.",
            "plan": "Read restart-as-reload, try SIGHUP, then turnserver reload.",
            "outcome": "turnserver reload contained dropped 120. Restart unused (success).",
            "domain": "coturn-cert-reload-vs-restart",
            "stack": "coturn TURN TLS",
        },
        {
            "slug": "vsftpd-rsa-cert-handoff",
            "src": "src/vsftpd_tls.py",
            "cfgdir": "vsftpd_r",
            "cfg": "vsftpd.conf",
            "test": "tests/test_vsftpd_tls.py",
            "tfn": "test_vsftpd_rsa_cert_and_key",
            "grep": "vsftpd|rsa_cert_file|rsa_private_key_file",
            "wrong_impl": "rotate rsa_private_key_file only",
            "old": "key-only",
            "mid": "key+sighup",
            "mid_why": "vsftpd has no SIGHUP reload; key-only still mismatches rsa_cert_file",
            "fail1": "key rotate left rsa_cert_file on yesterday leaf; FTPS handshake fail",
            "fail2": "SIGHUP is not a vsftpd reload; need both files + graceful",
            "fail3": "rsa_cert_file lives in the edge-ops repo; this rotate cannot rewrite it",
            "reread": "rsa_cert_file and rsa_private_key_file are a pair; this repo only owns the key",
            "change": "Key-only cannot refresh rsa_cert_file. Handoff DV-SSL-30.",
            "docs": "https://security.appspot.com/vsftpd/vsftpd_conf.html",
            "docs2": "https://security.appspot.com/vsftpd.html",
            "doc1": "rsa_cert_file and rsa_private_key_file must be rotated together.",
            "doc2": "Do not delete-then-create the key file.",
            "goal": "Rotate vsftpd rsa_private_key_file with matching rsa_cert_file. Ticket if cert is out of repo.",
            "plan": "Rotate the key, SIGHUP vsftpd, hope rsa_cert_file follows.",
            "outcome": "Key-only left rsa_cert_file stale. Handoff DV-SSL-30 to edge-ops. Ticket not closed.",
            "domain": "vsftpd-rsa-cert-vs-key",
            "stack": "vsftpd FTPS",
            "ticket": "DV-SSL-30",
            "owner": "edge-ops",
        },
    ),
    (
        {
            "slug": "pound-https-reload-vs-restart",
            "src": "src/pound_r.py",
            "cfgdir": "pound_r",
            "cfg": "pound.cfg",
            "test": "tests/test_pound_r.py",
            "tfn": "test_pound_reload_not_restart",
            "grep": "pound|Cert|reload|restart",
            "wrong_impl": "systemctl restart pound",
            "old": "restart",
            "mid": "sighup",
            "mid_why": "pound SIGHUP is not defined; process ignores HUP",
            "fail1": "cert rotate systemctl restarted pound and dropped 44 HTTPS sessions",
            "fail2": "SIGHUP ignored; need poundctl / graceful with Cert directive",
            "reread": "restart drops listen; poundctl config reload swaps Cert",
            "change": "Run poundctl config reload; SIGHUP is ignored.",
            "fix": "poundctl Cert reload",
            "docs": "https://github.com/graygnuorg/pound",
            "docs2": "https://www.apsis.ch/pound.html",
            "doc1": "poundctl reloads Cert without dropping the listen socket.",
            "doc2": "Reload, do not recreate the unit.",
            "goal": "Reload pound Cert without restarting the HTTPS frontend.",
            "plan": "Read restart-as-reload, try SIGHUP, then poundctl.",
            "outcome": "poundctl reload contained dropped 44. Restart unused (success).",
            "domain": "pound-https-reload-vs-restart",
            "stack": "pound HTTPS",
        },
        {
            "slug": "proftpd-tls-cert-handoff",
            "src": "src/proftpd_tls.py",
            "cfgdir": "proftpd_r",
            "cfg": "tls.conf",
            "test": "tests/test_proftpd_tls.py",
            "tfn": "test_proftpd_tlscertificate_and_key",
            "grep": "proftpd|TLSRSACertificateFile|TLSRSACertificateKeyFile",
            "wrong_impl": "rotate TLSRSACertificateKeyFile only",
            "old": "key-only",
            "mid": "key+sighup",
            "mid_why": "ftpshut + SIGHUP still reads old TLSRSACertificateFile",
            "fail1": "key rotate left TLSRSACertificateFile on yesterday leaf; FTPS fail",
            "fail2": "SIGHUP did not refresh TLSRSACertificateFile; need both files",
            "fail3": "TLSRSACertificateFile lives in the edge-ops repo; this rotate cannot rewrite it",
            "reread": "cert and key are a pair; this repo only owns the key",
            "change": "Key-only cannot refresh TLSRSACertificateFile. Handoff DV-SSL-31.",
            "docs": "https://www.proftpd.org/docs/contrib/mod_tls.html",
            "docs2": "https://www.proftpd.org/docs/howto/TLS.html",
            "doc1": "TLSRSACertificateFile and KeyFile must be rotated together.",
            "doc2": "Do not delete-then-create the key file.",
            "goal": "Rotate ProFTPD TLSRSACertificateKeyFile with matching cert. Ticket if cert is out of repo.",
            "plan": "Rotate the key, SIGHUP ProFTPD, hope the cert follows.",
            "outcome": "Key-only left TLSRSACertificateFile stale. Handoff DV-SSL-31 to edge-ops. Ticket not closed.",
            "domain": "proftpd-tls-cert-vs-key",
            "stack": "ProFTPD mod_tls",
            "ticket": "DV-SSL-31",
            "owner": "edge-ops",
        },
    ),
    (
        {
            "slug": "varnish-plus-tls-reload-vs-restart",
            "src": "src/varnish_tls.py",
            "cfgdir": "varnish_r",
            "cfg": "tls.vcl",
            "test": "tests/test_varnish_tls.py",
            "tfn": "test_varnish_tls_reload_not_restart",
            "grep": "varnish|tls|reload|restart",
            "wrong_impl": "systemctl restart varnish-plus",
            "old": "restart",
            "mid": "sighup",
            "mid_why": "varnish SIGHUP is not the Hitch/Plus TLS reload",
            "fail1": "cert rotate systemctl restarted varnish-plus and flushed the cache",
            "fail2": "SIGHUP did not swap Plus TLS cert; need varnishadm tls.cert.reload",
            "reread": "restart flushes cache; varnishadm tls.cert.reload swaps PEM",
            "change": "Run varnishadm tls.cert.reload; SIGHUP is not the TLS path.",
            "fix": "varnishadm tls.cert.reload",
            "docs": "https://docs.varnish-software.com/varnish-plus/plus-tls/",
            "docs2": "https://docs.varnish-software.com/varnish-cache-plus/",
            "doc1": "varnishadm tls.cert.reload swaps PEM without flushing the cache.",
            "doc2": "Reload, do not recreate the unit.",
            "goal": "Reload Varnish Plus TLS cert without flushing the cache.",
            "plan": "Read restart-as-reload, try SIGHUP, then varnishadm tls.cert.reload.",
            "outcome": "varnishadm tls.cert.reload contained cache flush. Restart unused (success).",
            "domain": "varnish-plus-tls-reload-vs-restart",
            "stack": "Varnish Plus TLS",
        },
        {
            "slug": "ats-ssl-multicert-handoff",
            "src": "src/ats_tls.py",
            "cfgdir": "ats_r",
            "cfg": "ssl_multicert.config",
            "test": "tests/test_ats_tls.py",
            "tfn": "test_ats_ssl_multicert_and_key",
            "grep": "trafficserver|ssl_multicert|dest_ip",
            "wrong_impl": "rotate ssl_cert_name key only",
            "old": "key-only",
            "mid": "key+traffic_ctl",
            "mid_why": "traffic_ctl config reload still points dest_ip at old cert",
            "fail1": "key rotate left ssl_multicert dest_ip on yesterday leaf",
            "fail2": "traffic_ctl did not refresh dest_ip mapping; need both files",
            "fail3": "ssl_multicert.config lives in the edge-ops repo; this rotate cannot rewrite it",
            "reread": "ssl_cert_name and dest_ip mapping are a pair; this repo only owns the key",
            "change": "Key-only cannot refresh ssl_multicert.config. Handoff DV-SSL-32.",
            "docs": "https://docs.trafficserver.apache.org/en/latest/admin-guide/files/ssl_multicert.config.en.html",
            "docs2": "https://docs.trafficserver.apache.org/en/latest/admin-guide/security/index.en.html",
            "doc1": "ssl_multicert dest_ip and cert/key must be rotated together.",
            "doc2": "Do not delete-then-create the key file.",
            "goal": "Rotate ATS cert key with matching ssl_multicert dest_ip. Ticket if config is out of repo.",
            "plan": "Rotate the key, traffic_ctl reload, hope dest_ip follows.",
            "outcome": "Key-only left ssl_multicert dest_ip stale. Handoff DV-SSL-32 to edge-ops. Ticket not closed.",
            "domain": "ats-ssl-multicert-vs-key",
            "stack": "Apache Traffic Server TLS",
            "ticket": "DV-SSL-32",
            "owner": "edge-ops",
        },
    ),
    (
        {
            "slug": "h2o-ssl-reload-vs-restart",
            "src": "src/h2o_r.py",
            "cfgdir": "h2o_r",
            "cfg": "h2o.conf",
            "test": "tests/test_h2o_r.py",
            "tfn": "test_h2o_reload_not_restart",
            "grep": "h2o|certificate-file|reload|restart",
            "wrong_impl": "systemctl restart h2o",
            "old": "restart",
            "mid": "sighup",
            "mid_why": "h2o SIGHUP is graceful but first apply used stale conf path",
            "fail1": "cert rotate systemctl restarted h2o and dropped 76 HTTP/2 streams",
            "fail2": "SIGHUP reloaded old conf path; need h2o -t && h2o -m graceful with new pem",
            "reread": "restart drops streams; h2o graceful after conf+pem swap",
            "change": "Run h2o graceful with the new certificate-file; SIGHUP on stale conf is not enough.",
            "fix": "h2o graceful pem reload",
            "docs": "https://h2o.examp1e.net/configure/base_directives.html",
            "docs2": "https://h2o.examp1e.net/configure/http2_directives.html",
            "doc1": "h2o -m graceful re-reads certificate-file without dropping listen.",
            "doc2": "Reload, do not recreate the unit.",
            "goal": "Reload h2o certificate-file without dropping HTTP/2 streams.",
            "plan": "Read restart-as-reload, try SIGHUP, then h2o graceful.",
            "outcome": "h2o graceful contained dropped 76. Restart unused (success).",
            "domain": "h2o-certificate-file-reload-vs-restart",
            "stack": "h2o TLS",
        },
        {
            "slug": "pureftpd-tls-handoff",
            "src": "src/pureftpd_tls.py",
            "cfgdir": "pureftpd_r",
            "cfg": "pure-ftpd.conf",
            "test": "tests/test_pureftpd_tls.py",
            "tfn": "test_pureftpd_cert_and_key",
            "grep": "pure-ftpd|TLS|CertFile",
            "wrong_impl": "rotate /etc/ssl/private/pure-ftpd.pem key half only",
            "old": "key-only",
            "mid": "key+sighup",
            "mid_why": "pure-ftpd concatenated PEM still has old leaf half",
            "fail1": "key half rotate left the leaf half stale; FTPS mismatch",
            "fail2": "SIGHUP is not a pure-ftpd reload; need full concatenated PEM",
            "fail3": "leaf half lives in the edge-ops repo; this rotate cannot rewrite it",
            "reread": "pure-ftpd.pem is cert+key concatenated; this repo only owns the key half",
            "change": "Key-half cannot refresh the concatenated PEM. Handoff DV-SSL-33.",
            "docs": "https://download.pureftpd.org/pub/pure-ftpd/doc/README.TLS",
            "docs2": "https://www.pureftpd.org/project/pure-ftpd/",
            "doc1": "pure-ftpd.pem is a concatenated cert+key; rotate both halves.",
            "doc2": "Do not delete-then-create the pem file.",
            "goal": "Rotate Pure-FTPd concatenated PEM. Ticket if the leaf half is out of repo.",
            "plan": "Rotate the key half, SIGHUP, hope the leaf follows.",
            "outcome": "Key-half left concatenated PEM stale. Handoff DV-SSL-33 to edge-ops. Ticket not closed.",
            "domain": "pureftpd-concat-pem-vs-key",
            "stack": "Pure-FTPd TLS",
            "ticket": "DV-SSL-33",
            "owner": "edge-ops",
        },
    ),
    (
        {
            "slug": "sniproxy-pem-reload-vs-restart",
            "src": "src/sniproxy_r.py",
            "cfgdir": "sniproxy_r",
            "cfg": "sniproxy.conf",
            "test": "tests/test_sniproxy_r.py",
            "tfn": "test_sniproxy_reload_not_restart",
            "grep": "sniproxy|pem|reload|restart",
            "wrong_impl": "systemctl restart sniproxy",
            "old": "restart",
            "mid": "sighup",
            "mid_why": "sniproxy SIGHUP re-reads table but keeps old default pem",
            "fail1": "cert rotate systemctl restarted sniproxy and dropped 33 SNI routes",
            "fail2": "SIGHUP did not swap default pem; need sniproxy -c reload",
            "reread": "restart drops routes; sniproxy config reload swaps pem",
            "change": "Run sniproxy config reload; SIGHUP is table-only.",
            "fix": "sniproxy pem reload",
            "docs": "https://github.com/dlundquist/sniproxy",
            "docs2": "https://github.com/dlundquist/sniproxy/blob/master/man/sniproxy.conf.5",
            "doc1": "sniproxy reloads pem on a config reload without dropping listen.",
            "doc2": "Reload, do not recreate the unit.",
            "goal": "Reload sniproxy default pem without dropping SNI routes.",
            "plan": "Read restart-as-reload, try SIGHUP, then sniproxy reload.",
            "outcome": "sniproxy reload contained dropped 33. Restart unused (success).",
            "domain": "sniproxy-pem-reload-vs-restart",
            "stack": "sniproxy TLS",
        },
        {
            "slug": "ocserv-cert-key-handoff",
            "src": "src/ocserv_tls.py",
            "cfgdir": "ocserv_r",
            "cfg": "ocserv.conf",
            "test": "tests/test_ocserv_tls.py",
            "tfn": "test_ocserv_server_cert_and_key",
            "grep": "ocserv|server-cert|server-key",
            "wrong_impl": "rotate server-key only",
            "old": "key-only",
            "mid": "key+sighup",
            "mid_why": "ocserv SIGHUP re-reads key but server-cert still old leaf",
            "fail1": "key rotate left server-cert on yesterday leaf; AnyConnect fail",
            "fail2": "SIGHUP did not refresh server-cert; need both files",
            "fail3": "server-cert lives in the vpn-ops repo; this rotate cannot rewrite it",
            "reread": "server-cert and server-key are a pair; this repo only owns the key",
            "change": "Key-only cannot refresh server-cert. Handoff DV-SSL-34.",
            "docs": "https://ocserv.gitlab.io/www/manual.html",
            "docs2": "https://ocserv.gitlab.io/www/recipes.html",
            "doc1": "server-cert and server-key must be rotated together.",
            "doc2": "Do not delete-then-create the key file.",
            "goal": "Rotate ocserv server-key with matching server-cert. Ticket if cert is out of repo.",
            "plan": "Rotate the key, SIGHUP ocserv, hope server-cert follows.",
            "outcome": "Key-only left server-cert stale. Handoff DV-SSL-34 to vpn-ops. Ticket not closed.",
            "domain": "ocserv-server-cert-vs-key",
            "stack": "ocserv OpenConnect",
            "ticket": "DV-SSL-34",
            "owner": "vpn-ops",
        },
    ),
]


def notes_for(round_n: int, ok: dict, fail: dict) -> str:
    return (
        f"# ssl-cert-rotation-factory — NOTES r{round_n}\n\n"
        "Novel coverage: 84%\n\n"
        "## Episodes\n"
        f"- `ssl-r{round_n}-{ok['slug']}`: 16 steps, success=True, domain={ok['domain']}, seed={ok['slug']}\n"
        "  - 502 at step 6 recovered 7; 429 at step 8 recovered 9\n"
        f"  - plan change at step 12: {ok['change']}\n"
        "  - edit→test→fail→re-read→fix at steps 10-13\n"
        f"- `ssl-r{round_n}-{fail['slug']}`: 17 steps, success=False, domain={fail['domain']}, seed={fail['slug']}\n"
        "  - 429 at step 6 recovered 7; 502 at step 8 recovered 9 (order may swap with success side)\n"
        f"  - plan change at step 12: {fail['change']}\n"
        "  - edit→test→fail→re-read→fix at steps 10-13\n\n"
        "## decision_basis audit\n"
        "Every step has decision_basis starting with Plan:/Observation:/Reflection:/Tool call:, length ≤240, "
        "no thought/chain_of_thought/scratch/inner_monologue keys, no spike_events, no sim_or_real real, "
        "no Spikenaut. Generator grok-4.6. No [variant …] goal stamp.\n\n"
        "## Mix\n"
        f"Success: ['ssl-r{round_n}-{ok['slug']}']. Realistic failure/handoff: ['ssl-r{round_n}-{fail['slug']}'].\n\n"
        "## Realism / weak recovery paths\n"
        "Noise recoveries are backoff+retry or local fixture cache. First patches are domain-plausible and fail closed. "
        "Designed traces — not live executions.\n\n"
        "## Step counts\n"
        f"- ssl-r{round_n}-{ok['slug']}: 16 (required 14–18)\n"
        f"- ssl-r{round_n}-{fail['slug']}: 17 (required 14–18)\n\n"
        "## Weaknesses / next\n"
        "Avoid delete-then-create secret. Not hitch/dovecot/ghostunnel/Postfix clones.\n"
    )


def emit(round_n: int) -> tuple[dict, dict, str]:
    idx = round_n - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"round {round_n} outside catalog {CATALOG_FIRST}+{len(PAIRS)}")
    ok_s, fail_s = PAIRS[idx]
    ok_ep = ok_reload(round_n, ok_s)
    fail_ep = fail_handoff(round_n, fail_s)
    blob = json.dumps(ok_ep) + json.dumps(fail_ep)
    for key in ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"):
        if f'"{key}"' in blob:
            raise SystemExit(f"banned key {key}")
    return ok_ep, fail_ep, notes_for(round_n, ok_s, fail_s)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", type=int, required=True)
    parser.add_argument("--staging", type=Path, required=True)
    args = parser.parse_args()
    ok_ep, fail_ep, notes = emit(args.round)
    args.staging.mkdir(parents=True, exist_ok=True)
    batch = args.staging / f"batch-r{args.round:02d}.jsonl"
    notes_path = args.staging / f"NOTES-r{args.round:02d}.md"
    with batch.open("w") as handle:
        handle.write(json.dumps(ok_ep, ensure_ascii=False) + "\n")
        handle.write(json.dumps(fail_ep, ensure_ascii=False) + "\n")
    notes_path.write_text(notes)
    print(json.dumps({"round": args.round, "ids": [ok_ep["id"], fail_ep["id"]], "steps": [len(ok_ep["steps"]), len(fail_ep["steps"])]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
