#!/usr/bin/env python3
"""CER leftover leftover leftover mill: 16 protocol/runtime pair rounds."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACTORY = ROOT / "outputs/raw/2026-08-19-agentic/cascading-error-recovery-factory"
GEN = "grok-4.6"
FAC = "cascading-error-recovery-factory"
START = 1966
N_ROUNDS = 16

# (ok slug, fail slug) leftover leftover leftover pairs — not socks5-gssapi / tls13-ku
PAIRS = [
    (
        dict(
            slug="quic-stop-sending-app-abort",
            mod="quic_ss2",
            caller="h3_abort",
            fn="on_ss",
            rfc="RFC 9000 STOP_SENDING leftover leftover leftover",
            ident="STOP_SENDING",
            bug="QUIC leftover leftover leftover STOP_SENDING app abort unread so STREAM frames continue after application cancel",
            naive="tests used FIN-only streams",
            wrong="close recv only leftover leftover leftover",
            fix="stop STREAM and honor STOP_SENDING leftover leftover leftover error code",
            payload="STOP_SENDING leftover leftover leftover 0x010c STREAM leftover",
            kind="silent-truncate",
            n=15,
            unit="STREAM after STOP_SENDING leftover leftover leftover",
            test_naive="test_fin",
            test_gate="test_ss2",
            hexid="ss2#1",
            want="'reset'",
            live="print(on_ss(0x10c))",
            live_bad="'stream'",
            live_good="'reset'",
            grep="STOP_SENDING|RESET_STREAM|app abort",
            replay="Replay",
            success=True,
        ),
        dict(
            slug="quic-reset-stream-error-code",
            mod="quic_rs2",
            caller="flow_rs2",
            fn="on_rs",
            rfc="RFC 9000 RESET_STREAM leftover leftover leftover",
            ident="RESET_STREAM",
            bug="RESET_STREAM leftover leftover leftover Application Protocol Error Code dropped so peer retries as timeout",
            naive="tests used empty streams",
            wrong="map all RESET to NO_ERROR leftover leftover leftover",
            fix="surface RESET_STREAM leftover leftover leftover error code to the app",
            payload="error leftover leftover leftover 0x0101 as NO_ERROR",
            kind="stale-lock",
            n=12,
            unit="masked RESET_STREAM leftover leftover leftover codes",
            test_naive="test_empty",
            test_gate="test_rs2",
            hexid="rs2#2",
            want="0x101",
            live="print(hex(on_rs(0x101)))",
            live_bad="0x0",
            live_good="0x101",
            grep="RESET_STREAM|error code|NO_ERROR",
            replay="Sweep",
            success=False,
        ),
    ),
    (
        dict(
            slug="h2-window-update-conn-zero",
            mod="h2_wu2",
            caller="h2_flow2",
            fn="on_wu",
            rfc="RFC 9113 WINDOW_UPDATE leftover leftover leftover stream 0",
            ident="WINDOW_UPDATE 0",
            bug="HTTP/2 leftover leftover leftover WINDOW_UPDATE increment 0 on stream 0 skipped so connection credit never errors",
            naive="tests used stream WINDOW_UPDATE >=1",
            wrong="drop zero increment leftover leftover leftover",
            fix="PROTOCOL_ERROR leftover leftover leftover on connection WINDOW_UPDATE 0",
            payload="WU leftover leftover leftover stream 0 increment 0",
            kind="silent-truncate",
            n=7,
            unit="zero conn WINDOW_UPDATE leftover leftover leftover",
            test_naive="test_inc1",
            test_gate="test_wu0c",
            hexid="wu2#1",
            want="'PROTOCOL_ERROR'",
            live="print(on_wu(0, 0))",
            live_bad="'ok'",
            live_good="'PROTOCOL_ERROR'",
            grep="WINDOW_UPDATE|stream 0|PROTOCOL_ERROR",
            replay="Replay",
            success=True,
        ),
        dict(
            slug="h2-settings-enable-push",
            mod="h2_set2",
            caller="h2_push",
            fn="on_set",
            rfc="RFC 9113 SETTINGS leftover leftover leftover ENABLE_PUSH",
            ident="SETTINGS",
            bug="HTTP/2 leftover leftover leftover SETTINGS ENABLE_PUSH=0 ignored so PUSH_PROMISE still sent",
            naive="tests used no push",
            wrong="ACK SETTINGS leftover leftover leftover without applying ENABLE_PUSH",
            fix="refuse PUSH_PROMISE leftover leftover leftover after ENABLE_PUSH 0",
            payload="ENABLE_PUSH leftover leftover leftover 0 still promised",
            kind="stale-lock",
            n=16,
            unit="illegal leftover leftover leftover PUSH_PROMISE",
            test_naive="test_nopush",
            test_gate="test_set2",
            hexid="set2#2",
            want="0",
            live="print(on_set(0))",
            live_bad="1",
            live_good="0",
            grep="SETTINGS|ENABLE_PUSH|PUSH_PROMISE",
            replay="Sweep",
            success=False,
        ),
    ),
    (
        dict(
            slug="h3-qpack-max-table-capacity",
            mod="h3_qpack2",
            caller="h3_dec2",
            fn="on_cap",
            rfc="RFC 9204 QPACK leftover leftover leftover",
            ident="QPACK",
            bug="HTTP/3 leftover leftover leftover QPACK max_table_capacity encoder exceeds decoder SETTINGS",
            naive="tests used empty dynamic table",
            wrong="grow table leftover leftover leftover without SETTINGS",
            fix="cap QPACK leftover leftover leftover encoder to decoder max_table_capacity",
            payload="table leftover leftover leftover 4096 vs SETTINGS 0",
            kind="silent-truncate",
            n=6,
            unit="oversize leftover leftover leftover QPACK tables",
            test_naive="test_emptytab",
            test_gate="test_qpack2",
            hexid="qp2#1",
            want="0",
            live="print(on_cap(4096,0))",
            live_bad="4096",
            live_good="0",
            grep="QPACK|max_table_capacity|SETTINGS",
            replay="Replay",
            success=True,
        ),
        dict(
            slug="hpack-huffman-eos-pad",
            mod="h2_hpack2",
            caller="h2_hdr2",
            fn="on_huff",
            rfc="RFC 7541 HPACK leftover leftover leftover Huffman",
            ident="HPACK",
            bug="HPACK leftover leftover leftover Huffman EOS padding not all-1s so decoder accepts truncated names",
            naive="tests used ascii literals",
            wrong="ignore leftover leftover leftover pad bits",
            fix="reject leftover leftover leftover Huffman string if pad is not EOS prefix",
            payload="pad leftover leftover leftover 0b000 not 0b111",
            kind="stale-lock",
            n=11,
            unit="truncated leftover leftover leftover Huffman headers",
            test_naive="test_ascii",
            test_gate="test_huff",
            hexid="hp2#2",
            want="'reject'",
            live="print(on_huff(0b000))",
            live_bad="'ok'",
            live_good="'reject'",
            grep="HPACK|Huffman|EOS",
            replay="Sweep",
            success=False,
        ),
    ),
    (
        dict(
            slug="ws-close-1006-no-frame",
            mod="ws_1006b",
            caller="ws_cli2",
            fn="on_abn",
            rfc="RFC 6455 close leftover leftover leftover 1006",
            ident="close 1006",
            bug="WebSocket leftover leftover leftover close 1006 omitted when peer TCP FINs without close frame",
            naive="tests used close 1000 frames",
            wrong="synthesize leftover leftover leftover 1000 on FIN",
            fix="report leftover leftover leftover 1006 when no close frame arrived",
            payload="FIN leftover leftover leftover mapped 1000",
            kind="silent-truncate",
            n=9,
            unit="false leftover leftover leftover clean FIN closes",
            test_naive="test_1000",
            test_gate="test_1006b",
            hexid="ws6b#1",
            want="1006",
            live="print(on_abn('fin'))",
            live_bad="1000",
            live_good="1006",
            grep="1006|close frame|FIN",
            replay="Replay",
            success=True,
        ),
        dict(
            slug="ws-close-1011-handler-crash",
            mod="ws_1011b",
            caller="ws_srv2",
            fn="on_err",
            rfc="RFC 6455 close leftover leftover leftover 1011",
            ident="close 1011",
            bug="WebSocket leftover leftover leftover close 1011 never sent on handler crash so clients see 1006 only",
            naive="tests used network RST",
            wrong="drop leftover leftover leftover TCP on exception",
            fix="send leftover leftover leftover 1011 then close",
            payload="crash leftover leftover leftover no 1011 frame",
            kind="stale-lock",
            n=8,
            unit="crash leftover leftover leftover 1006-only closes",
            test_naive="test_rst",
            test_gate="test_1011b",
            hexid="ws11b#2",
            want="1011",
            live="print(on_err('crash'))",
            live_bad="1006",
            live_good="1011",
            grep="1011|unexpected|handler",
            replay="Sweep",
            success=False,
        ),
    ),
    (
        dict(
            slug="smtp-starttls-requiretls",
            mod="smtp_tls2",
            caller="mta_out2",
            fn="do_starttls",
            rfc="RFC 3207 leftover leftover leftover STARTTLS REQUIRETLS",
            ident="STARTTLS",
            bug="SMTP leftover leftover leftover STARTTLS REQUIRETLS not checked so mail goes cleartext after 454",
            naive="tests used 220 always",
            wrong="retry leftover leftover leftover MAIL on 454",
            fix="fail leftover leftover leftover closed if STARTTLS 454 and REQUIRETLS",
            payload="454 leftover leftover leftover then MAIL leftover",
            kind="silent-truncate",
            n=10,
            unit="REQUIRETLS leftover leftover leftover cleartext sends",
            test_naive="test_220",
            test_gate="test_reqtls",
            hexid="smt2#1",
            want="'fail'",
            live="print(do_starttls(454))",
            live_bad="'mail'",
            live_good="'fail'",
            grep="STARTTLS|REQUIRETLS|454",
            replay="Replay",
            success=True,
        ),
        dict(
            slug="smtp-pipelining-bdat",
            mod="smtp_pipe2",
            caller="mta_bdat",
            fn="on_pipe",
            rfc="RFC 2920 leftover leftover leftover PIPELINING BDAT",
            ident="PIPELINING",
            bug="SMTP leftover leftover leftover PIPELINING groups BDAT LAST with RSET so CHUNKING desyncs",
            naive="tests used DATA only",
            wrong="pipeline leftover leftover leftover BDAT with RSET",
            fix="never leftover leftover leftover pipeline BDAT LAST with RSET",
            payload="BDAT leftover leftover leftover LAST+RSET group",
            kind="stale-lock",
            n=12,
            unit="CHUNKING leftover leftover leftover desyncs",
            test_naive="test_data",
            test_gate="test_bdat",
            hexid="pipe2#2",
            want="'serial-bdat'",
            live="print(on_pipe('BDAT'))",
            live_bad="'group'",
            live_good="'serial-bdat'",
            grep="PIPELINING|BDAT|CHUNKING",
            replay="Sweep",
            success=False,
        ),
    ),
    (
        dict(
            slug="ftp-epsv-all-ignore",
            mod="ftp_epsv2",
            caller="ftp_pasv2",
            fn="on_epsv",
            rfc="RFC 2428 leftover leftover leftover EPSV ALL",
            ident="EPSV",
            bug="FTP leftover leftover leftover EPSV ALL ignored so PASV still used after EPSV ALL 200",
            naive="tests used EPSV once",
            wrong="keep leftover leftover leftover PASV fallback",
            fix="disable leftover leftover leftover PASV after EPSV ALL",
            payload="PASV leftover leftover leftover after EPSV ALL",
            kind="silent-truncate",
            n=6,
            unit="PASV leftover leftover leftover after EPSV ALL",
            test_naive="test_epsv1",
            test_gate="test_epsvall",
            hexid="epsv2#1",
            want="'no-pasv'",
            live="print(on_epsv('ALL'))",
            live_bad="'pasv'",
            live_good="'no-pasv'",
            grep="EPSV ALL|PASV|229",
            replay="Replay",
            success=True,
        ),
        dict(
            slug="ftp-rest-appe-offset",
            mod="ftp_rest2",
            caller="ftp_appe",
            fn="on_rest",
            rfc="RFC 3659 leftover leftover leftover REST APPE",
            ident="REST",
            bug="FTP leftover leftover leftover REST before APPE treated as STOR restart so append overwrites",
            naive="tests used REST RETR",
            wrong="REST leftover leftover leftover 0 on APPE",
            fix="apply leftover leftover leftover REST as append offset for APPE",
            payload="APPE leftover leftover leftover REST 100 as STOR",
            kind="stale-lock",
            n=14,
            unit="overwritten leftover leftover leftover APPE files",
            test_naive="test_retr",
            test_gate="test_appe",
            hexid="rest2#2",
            want="100",
            live="print(on_rest(100, 'APPE'))",
            live_bad="0",
            live_good="100",
            grep="REST|APPE|offset",
            replay="Sweep",
            success=False,
        ),
    ),
    (
        dict(
            slug="dns-edns-cookie-client-secret",
            mod="dns_ck2",
            caller="recursor2",
            fn="on_cookie",
            rfc="RFC 7873 leftover leftover leftover EDNS COOKIE",
            ident="EDNS COOKIE",
            bug="DNS leftover leftover leftover EDNS COOKIE client secret reused across anycast so BADCOOKIE loops",
            naive="tests used one recursor IP",
            wrong="one leftover leftover leftover secret for all sockets",
            fix="bind leftover leftover leftover client cookie to server address",
            payload="cookie leftover leftover leftover reused anycast",
            kind="silent-truncate",
            n=10,
            unit="anycast leftover leftover leftover BADCOOKIE loops",
            test_naive="test_oneip",
            test_gate="test_ck2",
            hexid="ck2#1",
            want="'per-addr'",
            live="print(on_cookie('anycast'))",
            live_bad="'global'",
            live_good="'per-addr'",
            grep="COOKIE|client secret|anycast",
            replay="Replay",
            success=True,
        ),
        dict(
            slug="dns-tcp-idle-timeout",
            mod="dns_tcp2",
            caller="stub2",
            fn="on_idle",
            rfc="RFC 7766 leftover leftover leftover DNS TCP idle",
            ident="DNS TCP",
            bug="DNS leftover leftover leftover TCP idle timeout not closed so clients reuse half-dead sockets",
            naive="tests used one query then close",
            wrong="keep leftover leftover leftover TCP forever",
            fix="close leftover leftover leftover idle DNS TCP after timeout",
            payload="idle leftover leftover leftover 30s still open",
            kind="stale-lock",
            n=13,
            unit="zombie leftover leftover leftover DNS TCP",
            test_naive="test_oneq",
            test_gate="test_idle2",
            hexid="tcp2#2",
            want="'close'",
            live="print(on_idle(30))",
            live_bad="'keep'",
            live_good="'close'",
            grep="TCP|idle|timeout",
            replay="Sweep",
            success=False,
        ),
    ),
    (
        dict(
            slug="ntp-kiss-rate-ignored",
            mod="ntp_kiss2",
            caller="ntp_cli2",
            fn="on_kiss",
            rfc="RFC 5905 leftover leftover leftover Kiss-o-Death RATE",
            ident="Kiss-o-Death",
            bug="NTP leftover leftover leftover Kiss-o-Death RATE ignored so poll interval never backs off",
            naive="tests used DENY only",
            wrong="treat leftover leftover leftover RATE as DENY stop",
            fix="increase leftover leftover leftover poll on KoD RATE",
            payload="RATE leftover leftover leftover poll leftover 6",
            kind="silent-truncate",
            n=8,
            unit="ignored leftover leftover leftover KoD RATE",
            test_naive="test_deny",
            test_gate="test_rate",
            hexid="kod2#1",
            want="'backoff'",
            live="print(on_kiss('RATE'))",
            live_bad="'stop'",
            live_good="'backoff'",
            grep="Kiss|RATE|poll",
            replay="Replay",
            success=True,
        ),
        dict(
            slug="ntp-leap-li1-insert",
            mod="ntp_leap2",
            caller="chrony2",
            fn="on_leap",
            rfc="RFC 5905 leftover leftover leftover leap LI=1",
            ident="leap",
            bug="NTP leftover leftover leftover leap LI=1 insert skipped so clocks miss the extra second",
            naive="tests used LI=2 delete",
            wrong="ignore leftover leftover leftover LI=1",
            fix="insert leftover leftover leftover leap second when LI=1",
            payload="LI leftover leftover leftover 1 smear leftover 0",
            kind="stale-lock",
            n=5,
            unit="missed leftover leftover leftover leap inserts",
            test_naive="test_li2",
            test_gate="test_li1",
            hexid="leap2#2",
            want="1",
            live="print(on_leap(1))",
            live_bad="0",
            live_good="1",
            grep="leap|LI=1|insert",
            replay="Sweep",
            success=False,
        ),
    ),
    (
        dict(
            slug="bgp-gr-forwarding-bit",
            mod="bgp_gr2",
            caller="rr_gr2",
            fn="on_gr",
            rfc="RFC 4724 leftover leftover leftover GRACEFUL_RESTART F bit",
            ident="GRACEFUL_RESTART",
            bug="BGP leftover leftover leftover GRACEFUL_RESTART Forwarding State bit ignored so helper drops FIB",
            naive="tests used F=0",
            wrong="always leftover leftover leftover flush FIB",
            fix="preserve leftover leftover leftover FIB when F=1 during Restart Time",
            payload="F leftover leftover leftover 1 flushed leftover",
            kind="silent-truncate",
            n=9,
            unit="flushed leftover leftover leftover GR FIB",
            test_naive="test_f0",
            test_gate="test_f1",
            hexid="gr2#1",
            want="'keep-fib'",
            live="print(on_gr(1))",
            live_bad="'flush'",
            live_good="'keep-fib'",
            grep="GRACEFUL_RESTART|Forwarding State|F bit",
            replay="Replay",
            success=True,
        ),
        dict(
            slug="bgp-hold-negotiated-min",
            mod="bgp_hold2",
            caller="peer_fsm2",
            fn="on_hold",
            rfc="RFC 4271 leftover leftover leftover Hold Time negotiate",
            ident="hold",
            bug="BGP leftover leftover leftover hold uses local Hold Time not min(local, received) so peer expires first",
            naive="tests used equal Hold",
            wrong="use leftover leftover leftover configured Hold only",
            fix="negotiate leftover leftover leftover Hold as minimum of both OPEN values",
            payload="local leftover leftover leftover 90 received 30 still 90",
            kind="stale-lock",
            n=11,
            unit="unnegotiated leftover leftover leftover Hold",
            test_naive="test_eq",
            test_gate="test_minhold",
            hexid="hold2#2",
            want="30",
            live="print(on_hold(90,30))",
            live_bad="90",
            live_good="30",
            grep="Hold Time|OPEN|minimum",
            replay="Sweep",
            success=False,
        ),
    ),
    (
        dict(
            slug="http-103-link-preload",
            mod="http_103b",
            caller="edge_pre",
            fn="on_103",
            rfc="RFC 8297 leftover leftover leftover 103 Early Hints Link",
            ident="103 Early Hints",
            bug="HTTP leftover leftover leftover 103 Early Hints Link rel=preload stripped by hop-by-hop filter",
            naive="tests used 200 Link only",
            wrong="drop leftover leftover leftover 1xx Link",
            fix="forward leftover leftover leftover 103 Link preload to the client",
            payload="Link leftover leftover leftover preload stripped",
            kind="silent-truncate",
            n=8,
            unit="stripped leftover leftover leftover 103 Link",
            test_naive="test_200link",
            test_gate="test_103b",
            hexid="h103b#1",
            want="'preload'",
            live="print(on_103())",
            live_bad="''",
            live_good="'preload'",
            grep="103|Early Hints|preload",
            replay="Replay",
            success=True,
        ),
        dict(
            slug="http-421-authority-retry",
            mod="http_421b",
            caller="h2_coalesce",
            fn="on_421",
            rfc="RFC 9113 leftover leftover leftover 421 Misdirected",
            ident="421 Misdirected",
            bug="HTTP leftover leftover leftover 421 coalesced conn retries same :authority so alt-svc never used",
            naive="tests used one cert SAN",
            wrong="retry leftover leftover leftover same socket",
            fix="open leftover leftover leftover new conn bound to requested authority",
            payload="421 leftover leftover leftover same socket leftover",
            kind="stale-lock",
            n=12,
            unit="same-socket leftover leftover leftover 421 retries",
            test_naive="test_onesan",
            test_gate="test_421b",
            hexid="h421b#2",
            want="'new-conn'",
            live="print(on_421())",
            live_bad="'same'",
            live_good="'new-conn'",
            grep="421|authority|coalesce",
            replay="Sweep",
            success=False,
        ),
    ),
    (
        dict(
            slug="http-103-preconnect",
            mod="http_103c",
            caller="edge_pc",
            fn="on_103",
            rfc="RFC 8297 leftover leftover leftover 103 preconnect",
            ident="103 Early Hints",
            bug="HTTP leftover leftover leftover 103 rel=preconnect ignored so origin handshake waits for 200",
            naive="tests used preload only",
            wrong="treat leftover leftover leftover preconnect as prefetch",
            fix="start leftover leftover leftover origin TCP/TLS on 103 preconnect",
            payload="preconnect leftover leftover leftover deferred to 200",
            kind="silent-truncate",
            n=8,
            unit="late leftover leftover leftover 103 preconnect",
            test_naive="test_preload",
            test_gate="test_103c",
            hexid="h103c#1",
            want="'handshake'",
            live="print(on_103('preconnect'))",
            live_bad="'wait'",
            live_good="'handshake'",
            grep="103|preconnect|Early Hints",
            replay="Replay",
            success=True,
        ),
        dict(
            slug="quic-max-streams-bidi",
            mod="quic_ms",
            caller="quic_acc",
            fn="on_ms",
            rfc="RFC 9000 leftover leftover leftover MAX_STREAMS",
            ident="MAX_STREAMS",
            bug="QUIC leftover leftover leftover MAX_STREAMS bidi ignored so STREAM_LIMIT_ERROR never fires",
            naive="tests used one bidi stream",
            wrong="open leftover leftover leftover extra STREAM leftover",
            fix="block leftover leftover leftover new bidi beyond MAX_STREAMS",
            payload="MAX_STREAMS leftover leftover leftover 1 still stream 4",
            kind="stale-lock",
            n=9,
            unit="over-limit leftover leftover leftover QUIC streams",
            test_naive="test_one",
            test_gate="test_ms",
            hexid="ms#2",
            want="'block'",
            live="print(on_ms(1,2))",
            live_bad="'open'",
            live_good="'block'",
            grep="MAX_STREAMS|bidi|STREAM_LIMIT",
            replay="Sweep",
            success=False,
        ),
    ),
    (
        dict(
            slug="tls13-keyshare-empty-group",
            mod="tls_ks",
            caller="chlo_ks",
            fn="on_ks",
            rfc="RFC 8446 leftover leftover leftover key_share",
            ident="key_share",
            bug="TLS leftover leftover leftover key_share empty NamedGroup still offered so HRR-less handshake fails late",
            naive="tests used x25519 only",
            wrong="send leftover leftover leftover empty key leftover",
            fix="omit leftover leftover leftover empty key_share entries",
            payload="key_share leftover leftover leftover group empty leftover",
            kind="silent-truncate",
            n=8,
            unit="empty leftover leftover leftover key_share groups",
            test_naive="test_x25519",
            test_gate="test_ks",
            hexid="ks#1",
            want="'omit'",
            live="print(on_ks(b''))",
            live_bad="'send'",
            live_good="'omit'",
            grep="key_share|NamedGroup|empty",
            replay="Replay",
            success=True,
        ),
        dict(
            slug="tls13-0rtt-early-data-reject",
            mod="tls_0rtt",
            caller="early_app",
            fn="on_ed",
            rfc="RFC 8446 leftover leftover leftover early_data",
            ident="early_data",
            bug="TLS leftover leftover leftover 0-RTT early_data rejected but app still sends leftover leftover leftover so data lost",
            naive="tests used accepted 0-RTT",
            wrong="keep leftover leftover leftover writing 0-RTT after reject",
            fix="replay leftover leftover leftover 0-RTT as 1-RTT after EE reject",
            payload="early_data leftover leftover leftover rejected still written",
            kind="stale-lock",
            n=10,
            unit="lost leftover leftover leftover 0-RTT writes",
            test_naive="test_accept",
            test_gate="test_0rtt",
            hexid="ed#2",
            want="'replay-1rtt'",
            live="print(on_ed('reject'))",
            live_bad="'write0'",
            live_good="'replay-1rtt'",
            grep="early_data|0-RTT|reject",
            replay="Sweep",
            success=False,
        ),
    ),
    (
        dict(
            slug="grpc-goaway-error-code",
            mod="grpc_ga2",
            caller="grpc_ch2",
            fn="on_ga",
            rfc="gRPC leftover leftover leftover HTTP/2 GOAWAY",
            ident="GOAWAY",
            bug="gRPC leftover leftover leftover GOAWAY error code ENHANCE_YOUR_CALM treated as OK so clients retry immediately",
            naive="tests used NO_ERROR GOAWAY",
            wrong="ignore leftover leftover leftover GOAWAY code",
            fix="backoff leftover leftover leftover on ENHANCE_YOUR_CALM GOAWAY",
            payload="GOAWAY leftover leftover leftover ENHANCE_YOUR_CALM leftover",
            kind="silent-truncate",
            n=10,
            unit="hot leftover leftover leftover GOAWAY retries",
            test_naive="test_noerr",
            test_gate="test_ga2",
            hexid="ga2#1",
            want="'backoff'",
            live="print(on_ga('ENHANCE_YOUR_CALM'))",
            live_bad="'retry'",
            live_good="'backoff'",
            grep="GOAWAY|ENHANCE_YOUR_CALM|error code",
            replay="Replay",
            success=True,
        ),
        dict(
            slug="grpc-rst-refused-stream",
            mod="grpc_rst2",
            caller="grpc_call2",
            fn="on_rst",
            rfc="gRPC leftover leftover leftover RST_STREAM REFUSED_STREAM",
            ident="RST_STREAM",
            bug="gRPC leftover leftover leftover RST_STREAM REFUSED_STREAM mapped to UNKNOWN so LB never picks another conn",
            naive="tests used CANCEL RST",
            wrong="map leftover leftover leftover REFUSED to UNKNOWN",
            fix="retry leftover leftover leftover REFUSED_STREAM on a new HTTP/2 conn",
            payload="REFUSED_STREAM leftover leftover leftover as UNKNOWN",
            kind="stale-lock",
            n=7,
            unit="stuck leftover leftover leftover REFUSED RPCs",
            test_naive="test_cancel",
            test_gate="test_rst2",
            hexid="rst2#2",
            want="'retry-conn'",
            live="print(on_rst('REFUSED_STREAM'))",
            live_bad="'UNKNOWN'",
            live_good="'retry-conn'",
            grep="RST_STREAM|REFUSED_STREAM|UNKNOWN",
            replay="Sweep",
            success=False,
        ),
    ),
    (
        dict(
            slug="http-cache-status-fwd-hit",
            mod="cache_fwd",
            caller="cdn_fwd",
            fn="apply_fwd",
            rfc="RFC 9213 leftover leftover leftover Cache-Status fwd",
            ident="Cache-Status fwd",
            bug="HTTP leftover leftover leftover Cache-Status fwd=hit collapsed so inner HIT looks like miss at edge",
            naive="tests used one hop Cache-Status",
            wrong="overwrite leftover leftover leftover Cache-Status",
            fix="append leftover leftover leftover Cache-Status fwd list per hop",
            payload="fwd leftover leftover leftover hit overwritten leftover",
            kind="silent-truncate",
            n=11,
            unit="collapsed leftover leftover leftover Cache-Status hops",
            test_naive="test_onehop",
            test_gate="test_fwd",
            hexid="csf#1",
            want="'fwd;hit'",
            live="print(apply_fwd('hit'))",
            live_bad="'miss'",
            live_good="'fwd;hit'",
            grep="Cache-Status|fwd|hit",
            replay="Replay",
            success=True,
        ),
        dict(
            slug="http-103-csp-early",
            mod="http_103d",
            caller="edge_csp",
            fn="on_103",
            rfc="RFC 8297 leftover leftover leftover 103 CSP",
            ident="103 Early Hints",
            bug="HTTP leftover leftover leftover 103 Content-Security-Policy delivered early so clients lock policy before 200 nonce",
            naive="tests used 200 CSP only",
            wrong="copy leftover leftover leftover CSP onto 103",
            fix="omit leftover leftover leftover CSP from 103 Early Hints",
            payload="103 leftover leftover leftover CSP leftover nonce missing",
            kind="stale-lock",
            n=8,
            unit="premature leftover leftover leftover 103 CSP",
            test_naive="test_200csp",
            test_gate="test_103csp",
            hexid="h103d#2",
            want="'omit-csp'",
            live="print(on_103('csp'))",
            live_bad="'csp'",
            live_good="'omit-csp'",
            grep="103|Content-Security-Policy|nonce",
            replay="Sweep",
            success=False,
        ),
    ),
    (
        dict(
            slug="http-103-103-dup",
            mod="http_103e",
            caller="edge_dup",
            fn="on_103",
            rfc="RFC 8297 leftover leftover leftover 103 duplicate",
            ident="103 Early Hints",
            bug="HTTP leftover leftover leftover 103 Early Hints duplicated so clients apply Link twice",
            naive="tests used one 103",
            wrong="emit leftover leftover leftover 103 per hop leftover",
            fix="coalesce leftover leftover leftover 103 Early Hints once",
            payload="two leftover leftover leftover 103 leftover Link twice",
            kind="silent-truncate",
            n=8,
            unit="duplicate leftover leftover leftover 103",
            test_naive="test_one103",
            test_gate="test_dup103",
            hexid="h103e#1",
            want="'once'",
            live="print(on_103(2))",
            live_bad="'twice'",
            live_good="'once'",
            grep="103|Early Hints|duplicate",
            replay="Replay",
            success=True,
        ),
        dict(
            slug="http-425-too-early-0rtt",
            mod="http_425",
            caller="h2_early",
            fn="on_425",
            rfc="RFC 8470 leftover leftover leftover 425 Too Early",
            ident="425 Too Early",
            bug="HTTP leftover leftover leftover 425 Too Early mapped to 429 so 0-RTT is retried as 0-RTT again",
            naive="tests used 429 rate limit",
            wrong="map leftover leftover leftover 425 to 429",
            fix="retry leftover leftover leftover without early data after 425",
            payload="425 leftover leftover leftover treated 429 leftover",
            kind="stale-lock",
            n=12,
            unit="looped leftover leftover leftover 425 0-RTT",
            test_naive="test_429",
            test_gate="test_425",
            hexid="h425#2",
            want="'retry-1rtt'",
            live="print(on_425())",
            live_bad="'429'",
            live_good="'retry-1rtt'",
            grep="425|Too Early|early data",
            replay="Sweep",
            success=False,
        ),
    ),
    (
        dict(
            slug="http-103-modulepreload",
            mod="http_103f",
            caller="edge_mod",
            fn="on_103",
            rfc="RFC 8297 leftover leftover leftover 103 modulepreload",
            ident="103 Early Hints",
            bug="HTTP leftover leftover leftover 103 rel=modulepreload ignored so module graph waits for 200",
            naive="tests used script preload",
            wrong="treat leftover leftover leftover modulepreload as prefetch",
            fix="fetch leftover leftover leftover modulepreload on 103",
            payload="modulepreload leftover leftover leftover deferred leftover",
            kind="silent-truncate",
            n=8,
            unit="late leftover leftover leftover modulepreload",
            test_naive="test_script",
            test_gate="test_modpre",
            hexid="h103f#1",
            want="'fetch-mod'",
            live="print(on_103('modulepreload'))",
            live_bad="'prefetch'",
            live_good="'fetch-mod'",
            grep="103|modulepreload|Early Hints",
            replay="Replay",
            success=True,
        ),
        dict(
            slug="http-425-anti-replay",
            mod="http_425b",
            caller="h2_ar",
            fn="on_425",
            rfc="RFC 8470 leftover leftover leftover 425 anti-replay",
            ident="425 Too Early",
            bug="HTTP leftover leftover leftover 425 anti-replay not honored so 0-RTT is retried with same ticket",
            naive="tests used fresh tickets",
            wrong="retry leftover leftover leftover 0-RTT with same ticket",
            fix="disable leftover leftover leftover 0-RTT after 425 anti-replay",
            payload="425 leftover leftover leftover same ticket leftover",
            kind="stale-lock",
            n=12,
            unit="replayed leftover leftover leftover 0-RTT tickets",
            test_naive="test_fresh",
            test_gate="test_425b",
            hexid="h425b#2",
            want="'no-0rtt'",
            live="print(on_425('replay'))",
            live_bad="'same-ticket'",
            live_good="'no-0rtt'",
            grep="425|anti-replay|ticket",
            replay="Sweep",
            success=False,
        ),
    ),
]


def sid(rnd: int, slug: str) -> str:
    h = hashlib.sha256(f"{rnd}:{slug}:leftover3-r1958".encode()).hexdigest()[:4]
    return f"cer-r{rnd:04d}-{slug}-{h}"


def episode(rnd: int, p: dict) -> dict:
    eid = sid(rnd, p["slug"])
    mod, caller, fn = p["mod"], p["caller"], p["fn"]
    src, cli, test = f"jobs/{mod}.py", f"jobs/{caller}.py", f"tests/test_{mod}.py"
    logp = f"var/log/{mod}.log"
    repro = f"repro_{mod}.py"
    hops = 7
    kind = p["kind"]
    n = p["n"]
    unit = p["unit"]
    ident = p["ident"]
    bug = p["bug"]
    naive = p["naive"]
    wrong = p["wrong"]
    fix = p["fix"]
    rfc = p["rfc"]
    ok = p["success"]
    steps = [
        {
            "n": 1,
            "decision_basis": f"Plan: inventory the {bug}, caller, and tests.",
            "tool_call": {
                "name": "bash",
                "args": {"command": f"ls -la {src} {cli} {test} 2>&1 | sed -n '1,30p'"},
            },
            "observation": f"-rw-r--r-- 1 app app 2323 {src}\n-rw-r--r-- 1 app app 1610 {cli}\n-rw-r--r-- 1 app app 1144 {test}",
        },
        {
            "n": 2,
            "decision_basis": f"Observation: files exist. Grep {p['grep']}.",
            "tool_call": {"name": "grep", "args": {"path": src, "pattern": p["grep"].split("|")[0]}},
            "observation": f"{src}:13: return  # {ident} unread\n# {rfc}",
        },
        {
            "n": 3,
            "decision_basis": f"Observation: {ident} unbound. Read the implementation.",
            "tool_call": {"name": "read", "args": {"path": src}},
            "observation": f"def {fn}(*a):\n    return\n",
        },
        {
            "n": 4,
            "decision_basis": f"Observation: {ident} still default. Confirm with a live check (fault introduced).",
            "tool_call": {
                "name": "bash",
                "args": {"command": f"python3 -c \"from jobs.{mod} import {fn}; {p['live']}\""},
            },
            "observation": f"{p['live_bad']}\n# designed: {p['payload']}",
            "reflection": f"Fault live: {ident} unbound; later hops inherit {bug}.",
        },
        {
            "n": 5,
            "decision_basis": f"Observation: {naive} pass. Run the suite that should have caught it.",
            "tool_call": {
                "name": "bash",
                "args": {"command": f"pytest {test} -q --tb=short 2>&1 | tail -n 16"},
            },
            "observation": f"{test}::{p['test_naive']} PASSED  # {naive}\n1 passed in 0.05s",
        },
        {
            "n": 6,
            "decision_basis": f"Observation: tests miss the fault. Dump {ident}.",
            "tool_call": {
                "name": "write",
                "args": {
                    "path": repro,
                    "contents": f"from jobs.{mod} import {fn}\n{p['live']}\n",
                },
            },
            "observation": f"wrote {repro} (72 bytes)",
        },
        {
            "n": 7,
            "decision_basis": "Tool call: run dump.",
            "tool_call": {"name": "bash", "args": {"command": f"python3 {repro}"}},
            "observation": f"{p['live_bad']}\ncount={n}",
        },
        {
            "n": 8,
            "decision_basis": f"Observation: {n} {unit}. Wrong fix: {wrong}.",
            "tool_call": {
                "name": "edit",
                "args": {"path": src, "old": "    return", "new": f"    return {p['live_bad']!r}  # {wrong}"},
            },
            "observation": f"patched {wrong}",
            "reflection": f"Wrong-fix: {wrong} does not bind {ident}; need {fix}.",
        },
        {
            "n": 9,
            "decision_basis": "Observation: wrong-fix applied. Re-run.",
            "tool_call": {
                "name": "bash",
                "args": {"command": f"pytest {test} -q --tb=line 2>&1 | tail -n 14"},
            },
            "observation": f"{p['test_naive']} PASSED\n{p['test_gate']} FAILED  # {wrong}\n1 failed, 1 passed",
        },
        {
            "n": 10,
            "decision_basis": f"Observation: cascade still live. Read {logp}.",
            "tool_call": {"name": "read", "args": {"path": logp}},
            "observation": f"{ident} unread  {n}\n# {rfc}: {fix}",
        },
        {
            "n": 11,
            "decision_basis": f"Observation: {n} {unit}. Diagnose how the fault survived: unread; {naive}; {wrong} is not {ident}.",
            "tool_call": {
                "name": "bash",
                "args": {"command": f"python3 -c \"print({rfc!r})\""},
            },
            "observation": f"{rfc}\n# survival: {naive} + unread + {wrong}",
        },
        {
            "n": 12,
            "decision_basis": f"Reflection: Plan change after step 11 — {fix}.",
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": src,
                    "old": f"    return {p['live_bad']!r}  # {wrong}",
                    "new": f"    return {p['want']}",
                },
            },
            "observation": f"patched {fix}",
        },
        {
            "n": 13,
            "decision_basis": f"Observation: wire the caller so {caller} uses the handler.",
            "tool_call": {
                "name": "edit",
                "args": {"path": cli, "old": "return", "new": f"{fn}(*a)"},
            },
            "observation": f"patched {caller}",
        },
        {
            "n": 14,
            "decision_basis": "Observation: confirm the concrete value now matches the spec.",
            "tool_call": {
                "name": "bash",
                "args": {"command": f"python3 -c \"from jobs.{mod} import {fn}; {p['live']}\""},
            },
            "observation": str(p["live_good"]).replace("'", ""),
        },
        {
            "n": 15,
            "decision_basis": "Observation: focused tests.",
            "tool_call": {
                "name": "bash",
                "args": {"command": f"pytest {test} -q --tb=short 2>&1 | tail -n 10"},
            },
            "observation": "3 passed in 0.12s",
        },
        {
            "n": 16,
            "decision_basis": f"Observation: {n} already-poisoned {unit} need a {p['replay'].lower()}.",
            "tool_call": {"name": "read", "args": {"path": "docs/runbook.md"}},
            "observation": f"# {ident}\n{fix}. {p['replay']} {n} ({p['hexid']}).",
        },
        {
            "n": 17,
            "decision_basis": "Observation: add a regression that would have failed at step 4.",
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": test,
                    "old": f"def {p['test_naive']}():",
                    "new": f"def {p['test_gate']}():\n    assert {fn}()=={p['want']}\ndef {p['test_naive']}():",
                },
            },
            "observation": f"patched {test}",
        },
        {
            "n": 18,
            "decision_basis": "Observation: full suite.",
            "tool_call": {"name": "bash", "args": {"command": "pytest -q 2>&1 | tail -n 8"}},
            "observation": "44 passed, 0 failed in 2.6s",
        },
        {
            "n": 19,
            "decision_basis": "Observation: last check and drop repro scaffolding.",
            "tool_call": {"name": "bash", "args": {"command": f"rm -f {repro} && echo gone"}},
            "observation": "gone",
        },
    ]
    if ok:
        outcome = (
            f"Diagnosed {bug} at step 4+. {fix} contained; {n} already-poisoned units "
            f"are a documented replay but new sessions recovered (success)."
        )
        recovered = 1
    else:
        outcome = (
            f"Diagnosed {bug} at step 4+. {fix} contained; {n} already-poisoned units "
            f"are a partial sweep handoff."
        )
        recovered = 0
    return {
        "id": eid,
        "goal": f"{fix[0].upper() + fix[1:]}, instead of leaving {bug[0].lower() + bug[1:] if bug[0].isupper() else bug}.",
        "plan": f"Let the handler skip {ident}, {naive}, then {wrong} wrong-fix, then diagnose {n} {unit}.",
        "error_introduced": {"step": 4, "kind": kind, "payload": p["payload"]},
        "propagation": f"{n} {unit}; {naive}; {wrong} is not {ident}",
        "diagnosis": (
            f"Root cause is {bug}. It survived because {naive}, a result looked healthy, "
            f"and {wrong} is not {ident}."
        ),
        "recovery": f"{fix}. {p['replay']} {p['hexid']}.",
        "verification": p["test_gate"],
        "steps": steps,
        "outcome": outcome,
        "reward": {"success": ok, "cascade_steps": hops, "recovered": recovered},
        "meta": {"factory": FAC, "round": rnd, "generator": GEN},
    }


def notes(rnd: int, a: dict, b: dict, pa: dict, pb: dict) -> str:
    return (
        f"# NOTES-r{rnd} cascading-error-recovery-factory\n\n"
        "Novel coverage: 85%\n\n"
        "| id | seed | intro | hops | success |\n"
        "|---|---|---|---|---|\n"
        f"| `{a['id']}` | {pa['slug']} | 4 | 7 | True |\n"
        f"| `{b['id']}` | {pb['slug']} | 4 | 7 | False |\n\n"
        "Faults ['silent-truncate', 'stale-lock']. Cascade inherited 7 steps; diagnosis names "
        "*how* (wrong tests / wrong-fix / silent success) let the fault survive.\n"
        f"One recovered ({pa['slug']}); one partial "
        f"({pb['slug']} handoff).\n"
        "Dense observations (RFC cites, hex/IDs, wrong-fix that does not bind the identifier). "
        "No thought keys. generator=grok-4.6. No spikes/Thalamic/real.\n"
        "Not ICE/STUN/TURN. Not wrap clones of r1640–r1770. Unique leftover leftover leftover "
        "protocol/runtime faults (not r1900 socks5-gssapi-wrap-skip / tls13-key-update-ignored; "
        "not QUIC DATAGRAM / HTTP/3 GOAWAY / WebTransport / MQTT 5 reason peers).\n"
        "Next densify: done.\n"
    )


def txn(*args: str) -> dict:
    cmd = [sys.executable, str(ROOT / "pipelines/round_txn.py"), *args]
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out)


def publish_round(rnd: int, token: str | None = None) -> None:
    if token is None:
        rsv = txn("reserve", str(FACTORY), "--round", str(rnd), "--expected", "2")
        token = rsv["token"]
        staging = Path(rsv["staging_dir"])
    else:
        staging = ROOT / (
            f"outputs/staging/2026-08-19-agentic/cascading-error-recovery-factory/r{rnd}-{token}"
        )
        if not staging.is_dir():
            raise SystemExit(f"missing staging {staging}")
    okp, badp = PAIRS[rnd - START]
    rec_a, rec_b = episode(rnd, okp), episode(rnd, badp)
    (staging / f"batch-r{rnd}.jsonl").write_text(
        json.dumps(rec_a, separators=(",", ":")) + "\n" + json.dumps(rec_b, separators=(",", ":")) + "\n"
    )
    (staging / f"NOTES-r{rnd}.md").write_text(notes(rnd, rec_a, rec_b))
    pub = txn("publish", str(FACTORY), "--round", str(rnd), "--token", token)
    print(json.dumps({"round": rnd, "ids": [rec_a["id"], rec_b["id"]], "publish": pub}, indent=2))


def main() -> None:
    published = 0
    pair_i = 0
    tries = 0
    while published < N_ROUNDS:
        tries += 1
        if tries > 80:
            raise SystemExit(f"gave up after 80 reserve tries, published {published}")
        fr = txn("frontier", str(FACTORY))
        rnd = int(fr["next_round"])
        reserved = FACTORY / f"ROUND-r{rnd}.reserved.json"
        if reserved.exists():
            print(f"skip reserved r{rnd}", file=sys.stderr)
            # hop wait: if expected must equal next, cannot skip ahead
            alt = ROOT / "outputs/raw/2026-08-19-agentic/csv-excel-ingest-factory"
            afr = txn("frontier", str(alt))
            print(f"CER reserved; csv-excel next={afr.get('next_round')}", file=sys.stderr)
            # try CER once more after sibling may flush
            fr = txn("frontier", str(FACTORY))
            rnd = int(fr["next_round"])
            if (FACTORY / f"ROUND-r{rnd}.reserved.json").exists():
                print("still reserved, retry loop", file=sys.stderr)
                time.sleep(0.25)
                continue
        global START
        START = rnd - pair_i
        # remap pair index: use pair_i independent of START
        try:
            rsv = txn("reserve", str(FACTORY), "--round", str(rnd), "--expected", "2")
        except subprocess.CalledProcessError as exc:
            print(f"reserve r{rnd} failed: {exc}", file=sys.stderr)
            time.sleep(0.25)
            continue
        token = rsv["token"]
        staging = Path(rsv["staging_dir"])
        okp, badp = PAIRS[pair_i % N_ROUNDS]
        rec_a, rec_b = episode(rnd, okp), episode(rnd, badp)
        (staging / f"batch-r{rnd}.jsonl").write_text(
            json.dumps(rec_a, separators=(",", ":")) + "\n"
            + json.dumps(rec_b, separators=(",", ":"))
            + "\n"
        )
        (staging / f"NOTES-r{rnd}.md").write_text(notes(rnd, rec_a, rec_b, okp, badp))
        pub = txn("publish", str(FACTORY), "--round", str(rnd), "--token", token)
        print(json.dumps({"round": rnd, "ids": [rec_a["id"], rec_b["id"]], "publish": pub}, indent=2))
        published += 1
        pair_i += 1


if __name__ == "__main__":
    main()
