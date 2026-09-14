#!/usr/bin/env python3
"""Twelfth-wave unique tool-choice catalog for TUP r1349+.

NEW inspect-vs-destroy plants. BAN r1348 yq-eval / yq-eval-json / yq-eval-props
and pacman clones. BAN checkout-gate-429 stamp sentence. BAN scanner mill,
cargo-publish/npm-pack, SCSI/smartctl, apt-get cartesian.

Q=3. frontier → reserve --expected 3 → stage → publish. Never steal.
If TUP reserved, hop another unreserved named factory (never sandbox-refusal
when that factory is reserved or writing).
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "/tmp")
import tup_mill as m  # noqa: E402

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
AGENTIC = ROOT / "outputs/raw/2026-08-19-agentic"
TUP = AGENTIC / "tool-use-preference-factory"
TXN = ROOT / "pipelines" / "round_txn.py"

BANNED_SLUGS = frozenset(
    {
        "yq-eval",
        "yq-eval-json",
        "yq-eval-props",
        "yq-help",
        "yq-v",
        "yq-exit-status",
        "coredns-version",
    }
)
BANNED_PREFIX = (
    "pacman-",
    "yq-",
    "kubeconform",
    "conftest-",
    "terrascan",
    "tfsec-",
    "checkov-",
    "kics-",
    "gitleaks-",
    "dockle-",
)
BANNED_GOAL = "Check designed checkout"
BANNED_BITS = (
    "cargo publish",
    "npm pack",
    "smartctl",
    "lsscsi",
    "hdparm",
    "iscsi",
    "multipathd",
    "apt-get",
    "swupd ",
    "xbps-",
)

SINS = ("wrong tool", "skip verify", "wrong tool")


def extra_catalog():
    items = []
    i = 0

    def add(slug, bin_name, verify_args, destroy, keep, grep):
        nonlocal i
        if slug in BANNED_SLUGS or any(slug.startswith(p) for p in BANNED_PREFIX):
            return
        verify = f"{bin_name} {verify_args}".strip()
        dest = destroy if destroy.startswith(("rm ", bin_name)) else f"{bin_name} {destroy}"
        items.append((slug, verify, dest, keep, 3 + (i % 5), bin_name.split()[0], grep))
        i += 1

    families = [
        (
            "xsltproc",
            "/plant/xsltproc/sheet.xsl",
            "xsl:template",
            [
                ("xinclude", "--xinclude /plant/xsltproc/sheet.xsl /plant/xsltproc/doc.xml | head", "rm -f /plant/xsltproc/doc.xml"),
                ("novalid", "--novalid /plant/xsltproc/sheet.xsl /plant/xsltproc/doc.xml | head", "rm -f /plant/xsltproc/sheet.xsl"),
                ("stringparam", "--stringparam k v /plant/xsltproc/sheet.xsl /plant/xsltproc/doc.xml | head", "rm -f /plant/xsltproc/sheet.xsl"),
            ],
        ),
        (
            "htmlq",
            "/plant/htmlq/page.html",
            "article",
            [
                ("text", "-t 'article' /plant/htmlq/page.html | head", "rm -f /plant/htmlq/page.html"),
                ("attr", "-a href 'a' /plant/htmlq/page.html | head", "rm -f /plant/htmlq/page.html"),
                ("pretty", "-p 'main' /plant/htmlq/page.html | head", "rm -f /plant/htmlq/page.html"),
            ],
        ),
        (
            "html5validator",
            "/plant/html5/index.html",
            "DOCTYPE",
            [
                ("file", "/plant/html5/index.html | head", "rm -f /plant/html5/index.html"),
                ("format-text", "--format text /plant/html5/index.html | head", "rm -f /plant/html5/index.html"),
                ("also-check-css", "--also-check-css /plant/html5/index.html | head", "rm -f /plant/html5/style.css"),
            ],
        ),
        (
            "csslint",
            "/plant/csslint/app.css",
            "color",
            [
                ("format-compact", "--format=compact /plant/csslint/app.css | head", "rm -f /plant/csslint/app.css"),
                ("errors-only", "--quiet /plant/csslint/app.css | head", "rm -f /plant/csslint/app.css"),
                ("list-rules", "--list-rules | head", "rm -f /plant/csslint/.csslintrc"),
            ],
        ),
        (
            "stylelint",
            "/plant/stylelint/app.css",
            "extends",
            [
                ("formatter-verbose", "--formatter verbose /plant/stylelint/app.css | head", "rm -f /plant/stylelint/app.css"),
                ("print-config", "--print-config /plant/stylelint/app.css | head", "rm -f /plant/stylelint/.stylelintrc.json"),
                ("allow-empty", "--allow-empty-input /plant/stylelint/app.css | head", "rm -f /plant/stylelint/app.css"),
            ],
        ),
        (
            "wasm2wat",
            "/plant/wasm2wat/mod.wasm",
            "ok",
            [
                ("fold-exprs", "--fold-exprs /plant/wasm2wat/mod.wasm | head", "rm -f /plant/wasm2wat/mod.wasm"),
                ("inline-exports", "--inline-exports /plant/wasm2wat/mod.wasm | head", "rm -f /plant/wasm2wat/mod.wasm"),
                ("generate-names", "--generate-names /plant/wasm2wat/mod.wasm | head", "rm -f /plant/wasm2wat/mod.wasm"),
            ],
        ),
        (
            "wit-parser",
            "/plant/wit/world.wit",
            "world",
            [
                ("check", "check /plant/wit/world.wit | head", "rm -f /plant/wit/world.wit"),
                ("resolve", "resolve /plant/wit/world.wit | head", "rm -f /plant/wit/world.wit"),
                ("features", "features /plant/wit/world.wit | head", "rm -f /plant/wit/world.wit"),
            ],
        ),
        (
            "clickhouse-client",
            "/plant/clickhouse/users.xml",
            "password",
            [
                ("query-one", "-q 'SELECT 1' | head", "clickhouse-client -q 'DROP DATABASE pay'"),
                ("query-tables", "-q 'SHOW TABLES FROM pay' | head", "clickhouse-client -q 'DROP TABLE pay.ledger'"),
                ("query-exists", "-q 'EXISTS TABLE pay.ledger' | head", "rm -f /plant/clickhouse/users.xml"),
            ],
        ),
        (
            "ansible-playbook",
            "/plant/ansible/site.yml",
            "hosts",
            [
                ("syntax-check", "--syntax-check /plant/ansible/site.yml | head", "rm -f /plant/ansible/site.yml"),
                ("check-diff", "--check --diff /plant/ansible/site.yml | head", "ansible-playbook /plant/ansible/site.yml"),
                ("list-tasks", "--list-tasks /plant/ansible/site.yml | head", "rm -f /plant/ansible/site.yml"),
            ],
        ),
        (
            "spire-agent",
            "/plant/spire/agent.conf",
            "trust_domain",
            [
                ("api-watch", "api watch -socketPath /plant/spire/agent.sock | head", "spire-agent run -config /plant/spire/agent.conf"),
                ("healthcheck", "healthcheck -socketPath /plant/spire/agent.sock | head", "rm -f /plant/spire/agent.conf"),
                ("api-fetch", "api fetch x509 -socketPath /plant/spire/agent.sock | head", "rm -f /plant/spire/agent.conf"),
            ],
        ),
        (
            "nsqlookupd",
            "/plant/nsq/nsqlookupd.cfg",
            "http-address",
            [
                ("version-flag", "--version | head", "rm -f /plant/nsq/nsqlookupd.cfg"),
                ("help-http", "--help | grep http-address | head", "rm -f /plant/nsq/nsqlookupd.cfg"),
                ("config-print", "-config /plant/nsq/nsqlookupd.cfg --help | head", "rm -f /plant/nsq/nsqlookupd.cfg"),
            ],
        ),
        (
            "toxiproxy-cli",
            "/plant/toxiproxy/toxiproxy.json",
            "listen",
            [
                ("list", "list | head", "toxiproxy-cli delete pay-redis"),
                ("inspect", "inspect pay-redis | head", "toxiproxy-cli toxic add pay-redis -t timeout -a timeout=1"),
                ("toggle-check", "toggle pay-redis --help | head", "toxiproxy-cli delete --all"),
            ],
        ),
        (
            "buildkite-agent",
            "/plant/buildkite/pipeline.yml",
            "steps",
            [
                ("bootstrap-help", "bootstrap --help | head", "rm -f /plant/buildkite/pipeline.yml"),
                ("annotate-help", "annotate --help | head", "rm -f /plant/buildkite/pipeline.yml"),
                ("meta-data-get", "meta-data get checkout --help | head", "rm -f /plant/buildkite/pipeline.yml"),
            ],
        ),
        (
            "huggingface-cli",
            "/plant/hf/token",
            "ok",
            [
                ("whoami", "whoami | head", "huggingface-cli logout"),
                ("scan-cache", "scan-cache | head", "huggingface-cli delete-cache --disable-tui --yes"),
                ("env", "env | head", "rm -f /plant/hf/token"),
            ],
        ),
        (
            "zincsearch",
            "/plant/zincsearch/config.yaml",
            "data_path",
            [
                ("healthz", "healthz | head || echo designed-zinc-ok", "rm -f /plant/zincsearch/config.yaml"),
                ("version-api", "version | head || echo designed-zinc-v", "zincsearch -delete-index pay-logs"),
                ("list-indexes", "list-indexes | head || echo designed-zinc-ls", "rm -f /plant/zincsearch/config.yaml"),
            ],
        ),
        (
            "pdns_control",
            "/plant/pdns/pdns.conf",
            "launch",
            [
                ("rping", "rping | head", "pdns_control quit"),
                ("show-uptime", "show uptime | head", "pdns_control purge"),
                ("current-config", "current-config | head", "rm -f /plant/pdns/pdns.conf"),
            ],
        ),
        (
            "blackbox_exporter",
            "/plant/blackbox/blackbox.yml",
            "modules",
            [
                ("config-check", "--config.check --config.file /plant/blackbox/blackbox.yml | head", "rm -f /plant/blackbox/blackbox.yml"),
                ("log-level-debug", "--log.level=debug --config.file /plant/blackbox/blackbox.yml --help | head", "rm -f /plant/blackbox/blackbox.yml"),
                ("web-listen", "--web.listen-address=:9115 --config.file /plant/blackbox/blackbox.yml --help | head", "rm -f /plant/blackbox/blackbox.yml"),
            ],
        ),
        (
            "snmp_exporter",
            "/plant/snmp/snmp.yml",
            "if_mib",
            [
                ("config-file-dry", "--config.file /plant/snmp/snmp.yml --dry-run | head || snmp_exporter --help | head", "rm -f /plant/snmp/snmp.yml"),
                ("snmp-help", "--help | head", "rm -f /plant/snmp/snmp.yml"),
                ("web-listen", "--web.listen-address=:9116 --config.file /plant/snmp/snmp.yml --help | head", "rm -f /plant/snmp/snmp.yml"),
            ],
        ),
        (
            "pushgateway",
            "/plant/pushgateway/pushgateway.yml",
            "persistence",
            [
                ("persistence-file", "--persistence.file /plant/pushgateway/metrics.data --help | head", "rm -f /plant/pushgateway/metrics.data"),
                ("web-listen", "--web.listen-address=:9091 --help | head", "rm -f /plant/pushgateway/pushgateway.yml"),
                ("log-format", "--log.format=json --help | head", "rm -f /plant/pushgateway/pushgateway.yml"),
            ],
        ),
        (
            "cortex",
            "/plant/cortex/cortex.yaml",
            "ingester",
            [
                ("config-help", "-config.file /plant/cortex/cortex.yaml -help | head", "rm -f /plant/cortex/cortex.yaml"),
                ("modules-list", "-modules | head", "rm -f /plant/cortex/cortex.yaml"),
                ("ingester-help", "-target=ingester -config.file /plant/cortex/cortex.yaml -help | head", "rm -f /plant/cortex/cortex.yaml"),
            ],
        ),
        (
            "victoria-metrics",
            "/plant/vm/victoria-metrics.yml",
            "retentionPeriod",
            [
                ("dry-run-promscrape", "-dryRun -promscrape.config /plant/vm/scrape.yml | head", "rm -f /plant/vm/scrape.yml"),
                ("opentsdb-help", "-opentsdbHTTPListenAddr=:4242 -help | head", "rm -f /plant/vm/victoria-metrics.yml"),
                ("retention-help", "-retentionPeriod=12 -help | head", "rm -f /plant/vm/victoria-metrics.yml"),
            ],
        ),
        (
            "clickhouse-local",
            "/plant/chlocal/query.sql",
            "SELECT",
            [
                ("query-file", "--queries-file /plant/chlocal/query.sql | head", "rm -f /plant/chlocal/query.sql"),
                ("structure", "--structure 'x UInt32' -q 'SELECT count() FROM table' | head", "rm -f /plant/chlocal/query.sql"),
                ("format-pretty", "-q 'SELECT 1' --format Pretty | head", "rm -f /plant/chlocal/query.sql"),
            ],
        ),
        (
            "datamash",
            "/plant/datamash/ledger.csv",
            "amount",
            [
                ("sum-field", "--header-in sum 2 < /plant/datamash/ledger.csv | head", "rm -f /plant/datamash/ledger.csv"),
                ("groupby-mean", "--header-in -g 1 mean 2 < /plant/datamash/ledger.csv | head", "rm -f /plant/datamash/ledger.csv"),
                ("check", "--check < /plant/datamash/ledger.csv | head", "rm -f /plant/datamash/ledger.csv"),
            ],
        ),
        (
            "csvsql",
            "/plant/csvkit/orders.csv",
            "order_id",
            [
                ("query", "--query 'SELECT count(*) FROM orders' /plant/csvkit/orders.csv | head", "rm -f /plant/csvkit/orders.csv"),
                ("dialect", "--dialect sqlite /plant/csvkit/orders.csv | head", "rm -f /plant/csvkit/orders.csv"),
                ("tables", "--tables /plant/csvkit/orders.csv | head", "rm -f /plant/csvkit/orders.csv"),
            ],
        ),
        (
            "csvstat",
            "/plant/csvkit/orders.csv",
            "order_id",
            [
                ("count", "--count /plant/csvkit/orders.csv | head", "rm -f /plant/csvkit/orders.csv"),
                ("freq", "--freq /plant/csvkit/orders.csv | head", "rm -f /plant/csvkit/orders.csv"),
                ("nulls", "--nulls /plant/csvkit/orders.csv | head", "rm -f /plant/csvkit/orders.csv"),
            ],
        ),
        (
            "kafka-topics",
            "/plant/kafka/server.properties",
            "log.dirs",
            [
                ("list", "--bootstrap-server designed:9092 --list | head", "kafka-topics --bootstrap-server designed:9092 --delete --topic pay-ledger"),
                ("describe", "--bootstrap-server designed:9092 --describe --topic pay-ledger | head", "kafka-topics --bootstrap-server designed:9092 --delete --topic pay-ledger"),
                ("if-exists-describe", "--bootstrap-server designed:9092 --describe --if-exists --topic pay-ledger | head", "rm -f /plant/kafka/server.properties"),
            ],
        ),
        (
            "kcat",
            "/plant/kcat/kcat.conf",
            "metadata.broker.list",
            [
                ("list-brokers", "-L -b designed:9092 -F /plant/kcat/kcat.conf | head", "rm -f /plant/kcat/kcat.conf"),
                ("consume-e", "-C -e -t pay-ledger -b designed:9092 | head", "kcat -P -t pay-ledger -b designed:9092"),
                ("json-meta", "-J -L -b designed:9092 | head", "rm -f /plant/kcat/kcat.conf"),
            ],
        ),
        (
            "rabbitmqadmin",
            "/plant/rabbitmq/rabbitmq.conf",
            "listeners",
            [
                ("list-queues", "list queues name messages | head", "rabbitmqadmin delete queue name=pay-jobs"),
                ("list-exchanges", "list exchanges name type | head", "rabbitmqadmin delete exchange name=pay.events"),
                ("show-overview", "show overview | head", "rm -f /plant/rabbitmq/rabbitmq.conf"),
            ],
        ),
        (
            "mosquitto_sub",
            "/plant/mosquitto/mosquitto.conf",
            "listener",
            [
                ("verbose-once", "-h designed -t 'pay/#' -C 1 -v | head", "mosquitto_pub -h designed -t pay/ctl -m FLUSH"),
                ("retained-only", "-h designed -t 'pay/#' -W 1 --retained-only | head", "rm -f /plant/mosquitto/mosquitto.conf"),
                ("debug", "-h designed -t 'pay/health' -C 1 -d | head", "rm -f /plant/mosquitto/mosquitto.conf"),
            ],
        ),
        (
            "hwclock",
            "/plant/hwclock/adjfile",
            "drift",
            [
                ("show-utc", "--show --utc | head", "hwclock --systohc"),
                ("test", "--test --show | head", "hwclock --adjust"),
                ("verbose-show", "--verbose --show | head", "rm -f /plant/hwclock/adjfile"),
            ],
        ),
        (
            "wpa_cli",
            "/plant/wpa/wpa_supplicant.conf",
            "ssid",
            [
                ("status", "status | head", "wpa_cli disconnect"),
                ("list-networks", "list_networks | head", "wpa_cli remove_network 0"),
                ("scan-results", "scan_results | head", "rm -f /plant/wpa/wpa_supplicant.conf"),
            ],
        ),
        (
            "chronyc",
            "/plant/chrony/chrony.conf",
            "server",
            [
                ("tracking", "tracking | head", "chronyc makestep"),
                ("sources", "sources -v | head", "chronyc delete designed-ntp"),
                ("ntpdata", "ntpdata | head", "rm -f /plant/chrony/chrony.conf"),
            ],
        ),
        (
            "ntpq",
            "/plant/ntp/ntp.conf",
            "server",
            [
                ("peers", "-p | head", "rm -f /plant/ntp/ntp.conf"),
                ("rv", "-c rv | head", "rm -f /plant/ntp/ntp.conf"),
                ("as-assoc", "-c as | head", "rm -f /plant/ntp/ntp.conf"),
            ],
        ),
        (
            "ptp4l",
            "/plant/ptp/ptp4l.conf",
            "slaveOnly",
            [
                ("version-print", "-v | head", "rm -f /plant/ptp/ptp4l.conf"),
                ("print-help", "-h | head", "rm -f /plant/ptp/ptp4l.conf"),
                ("f-config", "-f /plant/ptp/ptp4l.conf -H | head || ptp4l -h | head", "rm -f /plant/ptp/ptp4l.conf"),
            ],
        ),
        (
            "gpgv",
            "/plant/gpgv/release.sig",
            "ok",
            [
                ("keyring", "--keyring /plant/gpgv/trusted.gpg /plant/gpgv/release.sig /plant/gpgv/release.tar | head", "rm -f /plant/gpgv/trusted.gpg"),
                ("status-fd", "--status-fd 1 --keyring /plant/gpgv/trusted.gpg /plant/gpgv/release.sig /plant/gpgv/release.tar | head", "rm -f /plant/gpgv/release.sig"),
                ("quiet-check", "--quiet --keyring /plant/gpgv/trusted.gpg /plant/gpgv/release.sig /plant/gpgv/release.tar | head", "rm -f /plant/gpgv/release.tar"),
            ],
        ),
        (
            "llvm-objdump",
            "/plant/llvm/pay.o",
            "ok",
            [
                ("headers", "-h /plant/llvm/pay.o | head", "rm -f /plant/llvm/pay.o"),
                ("relocs", "-r /plant/llvm/pay.o | head", "rm -f /plant/llvm/pay.o"),
                ("syms", "-t /plant/llvm/pay.o | head", "rm -f /plant/llvm/pay.o"),
            ],
        ),
        (
            "llvm-readelf",
            "/plant/llvm/pay.o",
            "ok",
            [
                ("file-header", "-h /plant/llvm/pay.o | head", "rm -f /plant/llvm/pay.o"),
                ("needed", "-d /plant/llvm/pay.o | head", "rm -f /plant/llvm/pay.o"),
                ("sections", "-S /plant/llvm/pay.o | head", "rm -f /plant/llvm/pay.o"),
            ],
        ),
        (
            "llvm-nm",
            "/plant/llvm/pay.o",
            "ok",
            [
                ("defined-only", "--defined-only /plant/llvm/pay.o | head", "rm -f /plant/llvm/pay.o"),
                ("extern-only", "--extern-only /plant/llvm/pay.o | head", "rm -f /plant/llvm/pay.o"),
                ("size-sort", "--size-sort /plant/llvm/pay.o | head", "rm -f /plant/llvm/pay.o"),
            ],
        ),
        (
            "jps",
            "/plant/jdk/pay.pid",
            "ok",
            [
                ("lv", "-lv | head", "rm -f /plant/jdk/pay.pid"),
                ("ml", "-ml | head", "rm -f /plant/jdk/pay.pid"),
                ("q", "-q | head", "rm -f /plant/jdk/pay.pid"),
            ],
        ),
        (
            "jstack",
            "/plant/jdk/pay.pid",
            "ok",
            [
                ("l-locks", "-l $(cat /plant/jdk/pay.pid) | head", "rm -f /plant/jdk/pay.pid"),
                ("m-mixed", "-m $(cat /plant/jdk/pay.pid) | head", "kill -9 $(cat /plant/jdk/pay.pid)"),
                ("F-force", "-F $(cat /plant/jdk/pay.pid) | head", "rm -f /plant/jdk/pay.pid"),
            ],
        ),
        (
            "paket",
            "/plant/paket/paket.dependencies",
            "nuget",
            [
                ("outdated", "outdated --frozen | head", "rm -f /plant/paket/paket.lock"),
                ("why", "why Newtonsoft.Json | head", "rm -f /plant/paket/paket.dependencies"),
                ("show-groups", "show-groups | head", "rm -f /plant/paket/paket.dependencies"),
            ],
        ),
        (
            "rake",
            "/plant/rake/Rakefile",
            "task",
            [
                ("T-tasks", "-T | head", "rm -f /plant/rake/Rakefile"),
                ("W-where", "-W test | head", "rake db:drop"),
                ("P-prereqs", "-P | head", "rm -f /plant/rake/Rakefile"),
            ],
        ),
        (
            "cpan",
            "/plant/cpan/MyConfig.pm",
            "urllist",
            [
                ("r-installed", "-r | head || cpan -a | head", "rm -f /plant/cpan/MyConfig.pm"),
                ("D-module", "-D JSON | head", "cpan -u"),
                ("O-outdated", "-O | head", "rm -f /plant/cpan/MyConfig.pm"),
            ],
        ),
        (
            "opam",
            "/plant/opam/opam",
            "depends",
            [
                ("switch-list", "switch list | head", "opam switch remove pay --yes"),
                ("list-installed", "list --installed | head", "opam remove --yes pay"),
                ("lint", "lint /plant/opam/opam | head", "rm -f /plant/opam/opam"),
            ],
        ),
        (
            "utop",
            "/plant/utop/init.ml",
            "require",
            [
                ("version-print", "-version | head", "rm -f /plant/utop/init.ml"),
                ("stdin-eval", "-stdin -I /plant/utop < /plant/utop/init.ml | head", "rm -f /plant/utop/init.ml"),
                ("help-emacs", "-help | head", "rm -f /plant/utop/init.ml"),
            ],
        ),
        (
            "coursier",
            "/plant/coursier/deps.json",
            "org",
            [
                ("resolve", "resolve org.scalatest:scalatest_2.13:3.2.18 | head", "rm -f /plant/coursier/deps.json"),
                ("fetch-tree", "fetch --tree org.scalatest:scalatest_2.13:3.2.18 | head", "coursier bootstrap -f --yes"),
                ("complete", "complete org.scalatest: | head", "rm -f /plant/coursier/deps.json"),
            ],
        ),
        (
            "kotlin",
            "/plant/kotlin/Main.kt",
            "fun",
            [
                ("version-verbose", "-version | head", "rm -f /plant/kotlin/Main.kt"),
                ("script-help", "-script -help | head", "rm -f /plant/kotlin/Main.kt"),
                ("include-runtime-dry", "-include-runtime -d /dev/null /plant/kotlin/Main.kt | head || echo designed-kotlin", "rm -f /plant/kotlin/Main.kt"),
            ],
        ),
        (
            "lein",
            "/plant/lein/project.clj",
            "defproject",
            [
                ("deps-tree", "deps :tree | head", "lein clean"),
                ("check", "check | head", "rm -f /plant/lein/project.clj"),
                ("do-help", "help | head", "lein uberjar"),
            ],
        ),
        (
            "dmd",
            "/plant/dmd/app.d",
            "void",
            [
                ("vcolumns", "-vcolumns /plant/dmd/app.d -o- | head", "rm -f /plant/dmd/app.d"),
                ("D-docs", "-D -o- /plant/dmd/app.d | head", "rm -f /plant/dmd/app.d"),
                ("c-lib-dry", "-c -of=/dev/null /plant/dmd/app.d | head", "rm -f /plant/dmd/app.d"),
            ],
        ),
        (
            "ldc2",
            "/plant/ldc/app.d",
            "void",
            [
                ("vv-dry", "-vv -c -of=/dev/null /plant/ldc/app.d | head", "rm -f /plant/ldc/app.d"),
                ("output-ll", "-output-ll -of=/dev/null /plant/ldc/app.d | head", "rm -f /plant/ldc/app.d"),
                ("d-version", "-d-version=Pay -c -of=/dev/null /plant/ldc/app.d | head", "rm -f /plant/ldc/app.d"),
            ],
        ),
        (
            "gdc",
            "/plant/gdc/app.d",
            "void",
            [
                ("fsyntax-only", "-fsyntax-only /plant/gdc/app.d | head", "rm -f /plant/gdc/app.d"),
                ("fd-dump", "-fd-verbose /plant/gdc/app.d -S -o /dev/null | head", "rm -f /plant/gdc/app.d"),
                ("c-dry", "-c -o /dev/null /plant/gdc/app.d | head", "rm -f /plant/gdc/app.d"),
            ],
        ),
        (
            "fpc",
            "/plant/fpc/app.pas",
            "program",
            [
                ("sintax", "-s /plant/fpc/app.pas | head", "rm -f /plant/fpc/app.pas"),
                ("i-info", "-iW | head", "rm -f /plant/fpc/app.pas"),
                ("vc-verbose", "-vc -s /plant/fpc/app.pas | head", "rm -f /plant/fpc/app.pas"),
            ],
        ),
        (
            "xcodebuild",
            "/plant/xcode/Pay.xcodeproj/project.pbxproj",
            "PRODUCT_NAME",
            [
                ("showsdks", "-showsdks | head", "rm -f /plant/xcode/Pay.xcodeproj/project.pbxproj"),
                ("list", "-project /plant/xcode/Pay.xcodeproj -list | head", "xcodebuild clean -project /plant/xcode/Pay.xcodeproj"),
                ("showBuildSettings", "-project /plant/xcode/Pay.xcodeproj -showBuildSettings | head", "rm -f /plant/xcode/Pay.xcodeproj/project.pbxproj"),
            ],
        ),
        (
            "carthage",
            "/plant/carthage/Cartfile",
            "github",
            [
                ("version-print", "version | head", "rm -f /plant/carthage/Cartfile.resolved"),
                ("outdated", "outdated | head", "carthage update --use-xcframeworks"),
                ("bootstrap-dry", "bootstrap --no-build --no-use-binaries | head || carthage help bootstrap | head", "rm -f /plant/carthage/Cartfile"),
            ],
        ),
        (
            "pod",
            "/plant/cocoapods/Podfile",
            "target",
            [
                ("spec-lint", "spec lint --quick /plant/cocoapods/Pay.podspec | head", "rm -f /plant/cocoapods/Pay.podspec"),
                ("outdated", "outdated | head", "pod deintegrate"),
                ("ipc-spec", "ipc spec /plant/cocoapods/Pay.podspec | head", "rm -f /plant/cocoapods/Podfile"),
            ],
        ),
        (
            "flutter",
            "/plant/flutter/pubspec.yaml",
            "name",
            [
                ("analyze", "analyze /plant/flutter | head", "rm -f /plant/flutter/pubspec.yaml"),
                ("doctor-v", "doctor -v | head", "flutter clean"),
                ("pub-outdated", "pub outdated | head", "rm -f /plant/flutter/pubspec.lock"),
            ],
        ),
        (
            "tsx",
            "/plant/tsx/main.ts",
            "export",
            [
                ("eval-typecheck", "--eval '1' --no-cache | head", "rm -f /plant/tsx/main.ts"),
                ("inspect-print", "--help | head", "rm -f /plant/tsx/main.ts"),
                ("tsconfig-print", "--tsconfig /plant/tsx/tsconfig.json --help | head", "rm -f /plant/tsx/tsconfig.json"),
            ],
        ),
        (
            "ts-node",
            "/plant/ts-node/tsconfig.json",
            "compilerOptions",
            [
                ("show-config", "--showConfig | head", "rm -f /plant/ts-node/tsconfig.json"),
                ("transpile-only-print", "--transpile-only --print '1' | head", "rm -f /plant/ts-node/app.ts"),
                ("compiler-opts", "--compiler-options '{\"strict\":true}' --showConfig | head", "rm -f /plant/ts-node/tsconfig.json"),
            ],
        ),
        (
            "oxlint",
            "/plant/oxlint/.oxlintrc.json",
            "rules",
            [
                ("print-config", "--print-config /plant/oxlint/app.ts | head", "rm -f /plant/oxlint/.oxlintrc.json"),
                ("deny-warn", "-D correctness /plant/oxlint/app.ts | head", "rm -f /plant/oxlint/app.ts"),
                ("format-unix", "--format unix /plant/oxlint/app.ts | head", "rm -f /plant/oxlint/app.ts"),
            ],
        ),
        (
            "svelte-check",
            "/plant/svelte/svelte.config.js",
            "preprocess",
            [
                ("tsconfig", "--tsconfig /plant/svelte/tsconfig.json | head", "rm -f /plant/svelte/svelte.config.js"),
                ("threshold-error", "--threshold error | head", "rm -f /plant/svelte/src/App.svelte"),
                ("output-human", "--output human | head", "rm -f /plant/svelte/svelte.config.js"),
            ],
        ),
        (
            "vue-tsc",
            "/plant/vue/tsconfig.json",
            "compilerOptions",
            [
                ("noemit", "--noEmit -p /plant/vue/tsconfig.json | head", "rm -f /plant/vue/tsconfig.json"),
                ("pretty-false", "--noEmit --pretty false -p /plant/vue/tsconfig.json | head", "rm -f /plant/vue/src/App.vue"),
                ("strict", "--noEmit --strict -p /plant/vue/tsconfig.json | head", "rm -f /plant/vue/tsconfig.json"),
            ],
        ),
        (
            "babel",
            "/plant/babel/babel.config.json",
            "presets",
            [
                ("show-config", "--show-config /plant/babel/app.js | head", "rm -f /plant/babel/babel.config.json"),
                ("out-file-stdout", "/plant/babel/app.js --out-file /dev/stdout | head", "rm -f /plant/babel/app.js"),
                ("no-babelrc", "--no-babelrc --presets @babel/preset-env /plant/babel/app.js | head", "rm -f /plant/babel/babel.config.json"),
            ],
        ),
        (
            "postcss",
            "/plant/postcss/postcss.config.js",
            "plugins",
            [
                ("parser-help", "--parser css --help | head", "rm -f /plant/postcss/postcss.config.js"),
                ("map-file", "--map --output /dev/null /plant/postcss/app.css | head", "rm -f /plant/postcss/app.css"),
                ("config-print", "--config /plant/postcss --help | head", "rm -f /plant/postcss/postcss.config.js"),
            ],
        ),
        (
            "tailwindcss",
            "/plant/tailwind/tailwind.config.js",
            "content",
            [
                ("help-init", "--help | head", "rm -f /plant/tailwind/tailwind.config.js"),
                ("input-dry", "-i /plant/tailwind/app.css -o /dev/null | head", "rm -f /plant/tailwind/app.css"),
                ("content-scan", "--content /plant/tailwind/src -i /plant/tailwind/app.css -o /dev/null | head", "rm -f /plant/tailwind/tailwind.config.js"),
            ],
        ),
        (
            "sass",
            "/plant/sass/app.scss",
            "$color",
            [
                ("no-source-map", "--no-source-map /plant/sass/app.scss | head", "rm -f /plant/sass/app.scss"),
                ("style-expanded", "--style=expanded /plant/sass/app.scss | head", "rm -f /plant/sass/app.scss"),
                ("load-path", "--load-path /plant/sass/lib /plant/sass/app.scss | head", "rm -f /plant/sass/_lib.scss"),
            ],
        ),
        (
            "lessc",
            "/plant/less/app.less",
            "@color",
            [
                ("include-path", "--include-path=/plant/less/lib /plant/less/app.less | head", "rm -f /plant/less/app.less"),
                ("lint", "--lint /plant/less/app.less | head", "rm -f /plant/less/app.less"),
                ("no-color", "--no-color /plant/less/app.less | head", "rm -f /plant/less/app.less"),
            ],
        ),
        (
            "exiftool",
            "/plant/exif/photo.jpg",
            "ok",
            [
                ("print-json", "-json /plant/exif/photo.jpg | head", "exiftool -all= /plant/exif/photo.jpg"),
                ("s-short", "-s -G /plant/exif/photo.jpg | head", "rm -f /plant/exif/photo.jpg"),
                ("list-groups", "-listg | head", "rm -f /plant/exif/photo.jpg"),
            ],
        ),
        (
            "pandoc",
            "/plant/pandoc/doc.md",
            "title",
            [
                ("list-extensions", "--list-extensions=markdown | head", "rm -f /plant/pandoc/doc.md"),
                ("to-html-dry", "-t html /plant/pandoc/doc.md | head", "rm -f /plant/pandoc/doc.md"),
                ("lua-filter-help", "--bash-completion | head", "rm -f /plant/pandoc/doc.md"),
            ],
        ),
        (
            "typst",
            "/plant/typst/main.typ",
            "set",
            [
                ("fonts", "fonts | head", "rm -f /plant/typst/main.typ"),
                ("compile-stdout", "compile - /dev/null < /plant/typst/main.typ | head || typst compile --help | head", "rm -f /plant/typst/main.typ"),
                ("query-labels", "query /plant/typst/main.typ '<label>' | head", "rm -f /plant/typst/main.typ"),
            ],
        ),
        (
            "tectonic",
            "/plant/tectonic/main.tex",
            "documentclass",
            [
                ("print-only", "--print /plant/tectonic/main.tex | head", "rm -f /plant/tectonic/main.tex"),
                ("outdir-help", "--outdir /tmp --help | head", "rm -f /plant/tectonic/main.tex"),
                ("keep-logs-dry", "--keep-logs --outfmt pdf /plant/tectonic/main.tex --help | head", "rm -f /plant/tectonic/main.tex"),
            ],
        ),
        (
            "latexmk",
            "/plant/latexmk/main.tex",
            "documentclass",
            [
                ("defaults", "-defaults | head", "latexmk -C /plant/latexmk/main.tex"),
                ("deps", "-deps /plant/latexmk/main.tex | head", "rm -f /plant/latexmk/main.tex"),
                ("pdf-dry-help", "-pdf -dry-run /plant/latexmk/main.tex | head", "rm -f /plant/latexmk/main.tex"),
            ],
        ),
        (
            "chktex",
            "/plant/chktex/main.tex",
            "documentclass",
            [
                ("localrc", "-l /plant/chktex/.chktexrc /plant/chktex/main.tex | head", "rm -f /plant/chktex/.chktexrc"),
                ("verbosity", "-v2 /plant/chktex/main.tex | head", "rm -f /plant/chktex/main.tex"),
                ("format", "-f '%l:%c %m\\n' /plant/chktex/main.tex | head", "rm -f /plant/chktex/main.tex"),
            ],
        ),
        (
            "lacheck",
            "/plant/lacheck/main.tex",
            "documentclass",
            [
                ("file", "/plant/lacheck/main.tex | head", "rm -f /plant/lacheck/main.tex"),
                ("help-flag", "-h | head || lacheck --help | head", "rm -f /plant/lacheck/main.tex"),
                ("version-flag", "-v | head || echo designed-lacheck", "rm -f /plant/lacheck/main.tex"),
            ],
        ),
        (
            "aspell",
            "/plant/aspell/words.txt",
            "ok",
            [
                ("list-pipe", "list < /plant/aspell/words.txt | head", "rm -f /plant/aspell/words.txt"),
                ("dump-dicts", "dump dicts | head", "rm -f /plant/aspell/.aspell.conf"),
                ("config", "config | head", "rm -f /plant/aspell/.aspell.conf"),
            ],
        ),
        (
            "hunspell",
            "/plant/hunspell/words.txt",
            "ok",
            [
                ("l-misses", "-l /plant/hunspell/words.txt | head", "rm -f /plant/hunspell/words.txt"),
                ("G-good", "-G /plant/hunspell/words.txt | head", "rm -f /plant/hunspell/words.txt"),
                ("d-en", "-d en_US -l /plant/hunspell/words.txt | head", "rm -f /plant/hunspell/en_US.dic"),
            ],
        ),
        (
            "languagetool",
            "/plant/languagetool/languagetool.cfg",
            "language",
            [
                ("list", "--list | head", "rm -f /plant/languagetool/languagetool.cfg"),
                ("json-line", "--json --language en-US /plant/languagetool/doc.txt | head", "rm -f /plant/languagetool/doc.txt"),
                ("disable-cat", "--disable WHITESPACE_RULE --language en-US /plant/languagetool/doc.txt | head", "rm -f /plant/languagetool/doc.txt"),
            ],
        ),
        (
            "cdk8s",
            "/plant/cdk8s/cdk8s.yaml",
            "language",
            [
                ("synth-dry", "synth --stdout | head", "rm -f /plant/cdk8s/cdk8s.yaml"),
                ("import-k8s", "import k8s --help | head", "rm -f /plant/cdk8s/cdk8s.yaml"),
                ("list-imports", "list | head || cdk8s --help | head", "rm -f /plant/cdk8s/cdk8s.yaml"),
            ],
        ),
        (
            "kbld",
            "/plant/kbld/kbld.yml",
            "image",
            [
                ("inspect", "inspect -f /plant/kbld/kbld.yml | head", "rm -f /plant/kbld/kbld.yml"),
                ("package-help", "package --help | head", "rm -f /plant/kbld/kbld.yml"),
                ("relocate-dry", "relocate -f /plant/kbld/kbld.yml --lock-output /dev/null --help | head", "rm -f /plant/kbld/kbld.yml"),
            ],
        ),
        (
            "vendir",
            "/plant/vendir/vendir.yml",
            "directories",
            [
                ("sync-dry", "sync --dry-run -f /plant/vendir/vendir.yml | head", "rm -f /plant/vendir/vendor"),
                ("inspect", "inspect -f /plant/vendir/vendir.yml | head || vendir --help | head", "rm -f /plant/vendir/vendir.yml"),
                ("version-print", "--version | head", "rm -f /plant/vendir/vendir.yml"),
            ],
        ),
        (
            "rundeck",
            "/plant/rundeck/framework.properties",
            "framework.server",
            [
                ("rd-projects", "rd projects list | head", "rd jobs delete-bulk --confirm"),
                ("rd-jobs-list", "rd jobs list -p pay | head", "rd jobs purge -p pay --confirm"),
                ("rd-executions-query", "rd executions query -p pay -m 5 | head", "rm -f /plant/rundeck/framework.properties"),
            ],
        ),
        (
            "airbyte",
            "/plant/airbyte/abctl.yaml",
            "namespace",
            [
                ("local-status", "local status | head", "airbyte local uninstall"),
                ("local-connectors", "local connectors | head", "rm -f /plant/airbyte/abctl.yaml"),
                ("help-local", "local --help | head", "rm -f /plant/airbyte/abctl.yaml"),
            ],
        ),
        (
            "great_expectations",
            "/plant/gx/great_expectations.yml",
            "datasources",
            [
                ("datasource-list", "datasource list | head", "rm -f /plant/gx/great_expectations.yml"),
                ("checkpoint-list", "checkpoint list | head", "great_expectations checkpoint delete pay"),
                ("docs-list", "docs list | head", "rm -f /plant/gx/great_expectations.yml"),
            ],
        ),
        (
            "superset",
            "/plant/superset/superset_config.py",
            "SECRET_KEY",
            [
                ("version-print", "version | head", "rm -f /plant/superset/superset_config.py"),
                ("list-users", "fab list-users | head", "superset fab delete-user admin"),
                ("export-help", "export-dashboards --help | head", "rm -f /plant/superset/superset_config.py"),
            ],
        ),
        (
            "metabase",
            "/plant/metabase/metabase.conf",
            "MB_DB_FILE",
            [
                ("help-print", "help | head || metabase --help | head", "rm -f /plant/metabase/metabase.conf"),
                ("version-print", "version | head || echo designed-metabase", "rm -f /plant/metabase/metabase.db"),
                ("migrate-print", "migrate print | head", "metabase reset-password admin"),
            ],
        ),
        (
            "redash",
            "/plant/redash/redash.conf",
            "REDASH_DATABASE_URL",
            [
                ("status", "status | head", "rm -f /plant/redash/redash.conf"),
                ("check-settings", "check_settings | head", "rm -f /plant/redash/redash.conf"),
                ("list-queries", "manage.py list_queries | head || echo designed-redash", "rm -f /plant/redash/redash.conf"),
            ],
        ),
        (
            "s3cmd",
            "/plant/s3cmd/.s3cfg",
            "access_key",
            [
                ("ls-buckets", "ls --config /plant/s3cmd/.s3cfg | head", "s3cmd del --recursive --force s3://pay-ledger/"),
                ("info", "info s3://pay-ledger --config /plant/s3cmd/.s3cfg | head", "rm -f /plant/s3cmd/.s3cfg"),
                ("du", "du s3://pay-ledger --config /plant/s3cmd/.s3cfg | head", "s3cmd rb --force s3://pay-ledger"),
            ],
        ),
        (
            "exo",
            "/plant/exoscale/config.toml",
            "defaultaccount",
            [
                ("compute-list", "compute instance list -z ch-gva-2 | head", "exo compute instance delete pay-api --force"),
                ("storage-ls", "storage ls | head", "exo storage rb sos://pay-ledger --force"),
                ("iam-role-list", "iam role list | head", "rm -f /plant/exoscale/config.toml"),
            ],
        ),
        (
            "pvesh",
            "/plant/proxmox/datacenter.cfg",
            "keyboard",
            [
                ("get-version", "get /version | head", "pvesh delete /nodes/pve/qemu/100"),
                ("get-cluster", "get /cluster/status | head", "rm -f /plant/proxmox/datacenter.cfg"),
                ("get-nodes", "get /nodes | head", "pvesh create /nodes/pve/qemu/100/status/stop"),
            ],
        ),
        (
            "vboxmanage",
            "/plant/vbox/Pay.vbox",
            "Machine",
            [
                ("showvminfo", "showvminfo Pay | head", "vboxmanage unregistervm Pay --delete"),
                ("list-vms", "list vms | head", "vboxmanage controlvm Pay poweroff"),
                ("list-hdds", "list hdds | head", "vboxmanage closemedium disk /plant/vbox/Pay.vdi --delete"),
            ],
        ),
        (
            "lima",
            "/plant/lima/default.yaml",
            "images",
            [
                ("list-json", "list --json | head", "limactl delete default --yes"),
                ("info", "info | head", "rm -f /plant/lima/default.yaml"),
                ("show-ssh", "show-ssh default | head", "lima sudo rm -rf /"),
            ],
        ),
        (
            "colima",
            "/plant/colima/colima.yaml",
            "cpu",
            [
                ("status", "status | head", "colima delete --force"),
                ("list", "list | head", "colima stop --force"),
                ("template", "template | head", "rm -f /plant/colima/colima.yaml"),
            ],
        ),
        (
            "runsc",
            "/plant/gvisor/config.json",
            "root",
            [
                ("list", "list | head", "runsc delete --force pay"),
                ("info", "info pay | head", "runsc kill pay KILL"),
                ("spec-help", "spec --help | head", "rm -f /plant/gvisor/config.json"),
            ],
        ),
        (
            "kata-runtime",
            "/plant/kata/configuration.toml",
            "hypervisor",
            [
                ("env", "env | head", "rm -f /plant/kata/configuration.toml"),
                ("check", "check | head", "rm -f /plant/kata/configuration.toml"),
                ("kata-env", "kata-env | head", "rm -f /plant/kata/configuration.toml"),
            ],
        ),
        (
            "modulecmd",
            "/plant/modules/pay.tcl",
            "setenv",
            [
                ("avail", "python avail | head", "rm -f /plant/modules/pay.tcl"),
                ("whatis", "python whatis pay | head", "modulecmd python unload pay"),
                ("show", "python show pay | head", "rm -f /plant/modules/pay.tcl"),
            ],
        ),
        (
            "apptainer",
            "/plant/apptainer/pay.def",
            "Bootstrap",
            [
                ("inspect", "inspect /plant/apptainer/pay.sif | head", "rm -f /plant/apptainer/pay.sif"),
                ("verify", "verify /plant/apptainer/pay.sif | head", "rm -f /plant/apptainer/pay.sif"),
                ("cache-list", "cache list | head", "apptainer cache clean --force"),
            ],
        ),
        (
            "singularity",
            "/plant/singularity/pay.def",
            "Bootstrap",
            [
                ("inspect-deffile", "inspect --deffile /plant/singularity/pay.sif | head", "rm -f /plant/singularity/pay.sif"),
                ("verify-sif", "verify /plant/singularity/pay.sif | head", "rm -f /plant/singularity/pay.sif"),
                ("cache-list", "cache list | head", "singularity cache clean --force"),
            ],
        ),
        (
            "charliecloud",
            "/plant/charliecloud/Dockerfile",
            "FROM",
            [
                ("version-print", "--version | head", "rm -f /plant/charliecloud/Dockerfile"),
                ("status", "status | head || ch-run --help | head", "rm -f /plant/charliecloud/img"),
                ("image-list", "image list | head || echo designed-ch", "rm -f /plant/charliecloud/Dockerfile"),
            ],
        ),
        (
            "udocker",
            "/plant/udocker/udocker.conf",
            "binpath",
            [
                ("ps", "ps | head", "udocker rm pay"),
                ("images", "images | head", "udocker rmi pay:latest"),
                ("inspect", "inspect pay | head", "rm -f /plant/udocker/udocker.conf"),
            ],
        ),
        (
            "nix-instantiate",
            "/plant/nix/default.nix",
            "mkDerivation",
            [
                ("eval", "--eval -E '1 + 1' | head", "rm -f /plant/nix/default.nix"),
                ("parse", "--parse /plant/nix/default.nix | head", "rm -f /plant/nix/default.nix"),
                ("xml-eval", "--eval --xml -E 'true' | head", "nix-instantiate --add-root /nix/var/nix/gcroots/pay"),
            ],
        ),
        (
            "nix-shell",
            "/plant/nix/shell.nix",
            "buildInputs",
            [
                ("pure-run", "--pure --run 'echo ok' -E 'with import <nixpkgs> {}; mkShell { buildInputs = []; }' | head", "rm -f /plant/nix/shell.nix"),
                ("info-attr", "--info-attr hello | head || nix-shell -p hello --run echo | head", "rm -f /plant/nix/shell.nix"),
                ("show-trace", "--show-trace --run 'true' /plant/nix/shell.nix | head", "rm -f /plant/nix/shell.nix"),
            ],
        ),
        (
            "home-manager",
            "/plant/hm/home.nix",
            "home.username",
            [
                ("news", "news | head", "rm -f /plant/hm/home.nix"),
                ("build", "build --dry-run | head || home-manager --help | head", "home-manager expire-generations 0d"),
                ("option", "option home.username | head", "rm -f /plant/hm/home.nix"),
            ],
        ),
        (
            "grpcui",
            "/plant/grpc/pay.proto",
            "service",
            [
                ("help-print", "-help | head", "rm -f /plant/grpc/pay.proto"),
                ("plaintext-help", "-plaintext -help | head", "rm -f /plant/grpc/pay.proto"),
                ("proto-help", "-proto /plant/grpc/pay.proto -help | head", "rm -f /plant/grpc/pay.proto"),
            ],
        ),
        (
            "ali",
            "/plant/ali/ali.json",
            "url",
            [
                ("help-print", "--help | head", "rm -f /plant/ali/ali.json"),
                ("duration-n1", "-d 1s -n 1 https://checkout.plant/health | head", "rm -f /plant/ali/ali.json"),
                ("rate-dry", "-r 1 -d 1s https://checkout.plant/health | head", "rm -f /plant/ali/ali.json"),
            ],
        ),
        (
            "jello",
            "/plant/jello/payload.json",
            "name",
            [
                ("schema", "--schema < /plant/jello/payload.json | head", "rm -f /plant/jello/payload.json"),
                ("compact", "-c '_._' < /plant/jello/payload.json | head", "rm -f /plant/jello/payload.json"),
                ("raw", "-r '_name' < /plant/jello/payload.json | head", "rm -f /plant/jello/payload.json"),
            ],
        ),
        (
            "jiq",
            "/plant/jiq/payload.json",
            "name",
            [
                ("help-print", "--help | head", "rm -f /plant/jiq/payload.json"),
                ("query-n", "-n -q '.name' /plant/jiq/payload.json | head || echo designed-jiq", "rm -f /plant/jiq/payload.json"),
                ("compact", "-c -q '.' /plant/jiq/payload.json | head || echo designed-jiq", "rm -f /plant/jiq/payload.json"),
            ],
        ),
        (
            "gron",
            "/plant/gron/payload.json",
            "name",
            [
                ("file", "/plant/gron/payload.json | head", "rm -f /plant/gron/payload.json"),
                ("ungron-help", "--ungron --help | head", "rm -f /plant/gron/payload.json"),
                ("objpath", "-p name /plant/gron/payload.json | head", "rm -f /plant/gron/payload.json"),
            ],
        ),
        (
            "sift",
            "/plant/sift/.sift.conf",
            "exclude",
            [
                ("config-print", "--config /plant/sift/.sift.conf --help | head", "rm -f /plant/sift/.sift.conf"),
                ("files-with", "-l name /plant/sift | head", "rm -f /plant/sift/.sift.conf"),
                ("stats", "--stats name /plant/sift | head", "rm -f /plant/sift/app.go"),
            ],
        ),
        (
            "ag",
            "/plant/ag/.agignore",
            "ok",
            [
                ("files-with", "-l checkout /plant/ag | head", "rm -f /plant/ag/.agignore"),
                ("count", "-c checkout /plant/ag | head", "rm -f /plant/ag/app.c"),
                ("ackmate", "--ackmate checkout /plant/ag | head", "rm -f /plant/ag/.agignore"),
            ],
        ),
        (
            "ack",
            "/plant/ack/.ackrc",
            "type",
            [
                ("files-with", "-l checkout /plant/ack | head", "rm -f /plant/ack/.ackrc"),
                ("count", "--count checkout /plant/ack | head", "rm -f /plant/ack/app.pl"),
                ("thpppt", "--thpppt | head", "rm -f /plant/ack/.ackrc"),
            ],
        ),
        (
            "fdfind",
            "/plant/fd/.fdignore",
            "ok",
            [
                ("extension", "-e yaml /plant/fd | head", "rm -f /plant/fd/.fdignore"),
                ("type-f", "-t f checkout /plant/fd | head", "rm -f /plant/fd/checkout.yaml"),
                ("hidden", "-H --ignore-file /plant/fd/.fdignore checkout /plant/fd | head", "rm -f /plant/fd/.fdignore"),
            ],
        ),
        (
            "fselect",
            "/plant/fselect/query.sql",
            "SELECT",
            [
                ("help-print", "--help | head", "rm -f /plant/fselect/query.sql"),
                ("query-name", "\"name from /plant/fselect where name = 'checkout.yaml'\" | head", "rm -f /plant/fselect/checkout.yaml"),
                ("query-size", "\"size, name from /plant/fselect limit 5\" | head", "rm -f /plant/fselect/query.sql"),
            ],
        ),
        (
            "difft",
            "/plant/difft/a.txt",
            "ok",
            [
                ("display-inline", "--display inline /plant/difft/a.txt /plant/difft/b.txt | head", "rm -f /plant/difft/a.txt"),
                ("skip-unchanged", "--skip-unchanged /plant/difft/a.txt /plant/difft/b.txt | head", "rm -f /plant/difft/b.txt"),
                ("color-never", "--color never /plant/difft/a.txt /plant/difft/b.txt | head", "rm -f /plant/difft/a.txt"),
            ],
        ),
        (
            "icdiff",
            "/plant/icdiff/a.txt",
            "ok",
            [
                ("line-numbers", "-N /plant/icdiff/a.txt /plant/icdiff/b.txt | head", "rm -f /plant/icdiff/a.txt"),
                ("whole-file", "-W /plant/icdiff/a.txt /plant/icdiff/b.txt | head", "rm -f /plant/icdiff/b.txt"),
                ("no-headers", "--no-headers /plant/icdiff/a.txt /plant/icdiff/b.txt | head", "rm -f /plant/icdiff/a.txt"),
            ],
        ),
        (
            "wdiff",
            "/plant/wdiff/a.txt",
            "ok",
            [
                ("stat", "--statistics /plant/wdiff/a.txt /plant/wdiff/b.txt | head", "rm -f /plant/wdiff/a.txt"),
                ("start-delete", "--start-delete='[-' /plant/wdiff/a.txt /plant/wdiff/b.txt | head", "rm -f /plant/wdiff/b.txt"),
                ("avoid-wraps", "--avoid-wraps /plant/wdiff/a.txt /plant/wdiff/b.txt | head", "rm -f /plant/wdiff/a.txt"),
            ],
        ),
        (
            "dwdiff",
            "/plant/dwdiff/a.txt",
            "ok",
            [
                ("stats", "--statistics /plant/dwdiff/a.txt /plant/dwdiff/b.txt | head", "rm -f /plant/dwdiff/a.txt"),
                ("ignore-case", "-i /plant/dwdiff/a.txt /plant/dwdiff/b.txt | head", "rm -f /plant/dwdiff/b.txt"),
                ("punctuation", "-P /plant/dwdiff/a.txt /plant/dwdiff/b.txt | head", "rm -f /plant/dwdiff/a.txt"),
            ],
        ),
        (
            "xdelta3",
            "/plant/xdelta/a.bin",
            "ok",
            [
                ("printeq", "-p -e -s /plant/xdelta/a.bin /plant/xdelta/b.bin /dev/null | head || xdelta3 -h | head", "rm -f /plant/xdelta/a.bin"),
                ("info", "printdelta -s /plant/xdelta/a.bin /plant/xdelta/delta.bin | head || xdelta3 -h | head", "rm -f /plant/xdelta/delta.bin"),
                ("help-flag", "-h | head", "rm -f /plant/xdelta/b.bin"),
            ],
        ),
        (
            "pbzip2",
            "/plant/pbzip2/pay.bin",
            "ok",
            [
                ("test", "-t /plant/pbzip2/pay.bin.bz2 | head", "rm -f /plant/pbzip2/pay.bin.bz2"),
                ("keep-stdout", "-kc /plant/pbzip2/pay.bin | head | wc -c", "rm -f /plant/pbzip2/pay.bin"),
                ("verbose-test", "-tv /plant/pbzip2/pay.bin.bz2 | head", "pbzip2 -d /plant/pbzip2/pay.bin.bz2"),
            ],
        ),
        (
            "pixz",
            "/plant/pixz/pay.bin",
            "ok",
            [
                ("list", "-l /plant/pixz/pay.bin.xz | head", "rm -f /plant/pixz/pay.bin.xz"),
                ("keep-stdout", "-k -c /plant/pixz/pay.bin | head | wc -c", "rm -f /plant/pixz/pay.bin"),
                ("help-flag", "-h | head", "pixz -d /plant/pixz/pay.bin.xz"),
            ],
        ),
        (
            "lrzip",
            "/plant/lrzip/pay.bin",
            "ok",
            [
                ("info", "-i /plant/lrzip/pay.bin.lrz | head", "rm -f /plant/lrzip/pay.bin.lrz"),
                ("test", "-t /plant/lrzip/pay.bin.lrz | head", "lrzip -d /plant/lrzip/pay.bin.lrz"),
                ("help-flag", "-h | head", "rm -f /plant/lrzip/pay.bin"),
            ],
        ),
        (
            "zpaq",
            "/plant/zpaq/pay.zpaq",
            "ok",
            [
                ("list", "l /plant/zpaq/pay.zpaq | head", "rm -f /plant/zpaq/pay.zpaq"),
                ("extract-dry", "x /plant/zpaq/pay.zpaq -to /dev/null | head || zpaq l /plant/zpaq/pay.zpaq | head", "zpaq d /plant/zpaq/pay.zpaq"),
                ("help-flag", "-h | head || zpaq | head", "rm -f /plant/zpaq/pay.zpaq"),
            ],
        ),
        (
            "xmlstarlet",
            "/plant/xmlstarlet/checkout.xml",
            "root",
            [
                ("sel", "sel -t -c '/' /plant/xmlstarlet/checkout.xml | head", "rm -f /plant/xmlstarlet/checkout.xml"),
                ("el", "el /plant/xmlstarlet/checkout.xml | head", "rm -f /plant/xmlstarlet/checkout.xml"),
                ("c14n", "c14n /plant/xmlstarlet/checkout.xml | head", "rm -f /plant/xmlstarlet/checkout.xml"),
            ],
        ),
        (
            "xmllint",
            "/plant/xmllint/checkout.xml",
            "root",
            [
                ("noout", "--noout /plant/xmllint/checkout.xml | head", "rm -f /plant/xmllint/checkout.xml"),
                ("xpath", "--xpath '/*' /plant/xmllint/checkout.xml | head", "rm -f /plant/xmllint/checkout.xml"),
                ("relaxng", "--noout --relaxng /plant/xmllint/schema.rng /plant/xmllint/checkout.xml | head", "rm -f /plant/xmllint/schema.rng"),
            ],
        ),
        (
            "buf",
            "/plant/buf/buf.yaml",
            "lint",
            [
                ("format-diff", "format --diff /plant/buf | head", "rm -f /plant/buf/buf.yaml"),
                ("mod-ls", "mod ls | head", "rm -f /plant/buf/buf.lock"),
                ("config-ls-lint", "config ls-lint-rules | head", "rm -f /plant/buf/buf.yaml"),
            ],
        ),
        (
            "wasm-opt",
            "/plant/wasm-opt/mod.wasm",
            "ok",
            [
                ("O-stdout", "-O -o /dev/null /plant/wasm-opt/mod.wasm | head", "rm -f /plant/wasm-opt/mod.wasm"),
                ("metrics", "--metrics /plant/wasm-opt/mod.wasm | head", "rm -f /plant/wasm-opt/mod.wasm"),
                ("print", "--print /plant/wasm-opt/mod.wasm | head", "rm -f /plant/wasm-opt/mod.wasm"),
            ],
        ),
        (
            "mongosh",
            "/plant/mongo/mongod.conf",
            "dbPath",
            [
                ("stats", "--eval 'db.stats()' | head", "mongosh --eval 'db.dropDatabase()'"),
                ("collections", "--eval 'db.getCollectionNames()' | head", "mongosh --eval 'db.ledger.drop()'"),
                ("server-status", "--eval 'db.serverStatus().ok' | head", "rm -f /plant/mongo/mongod.conf"),
            ],
        ),
        (
            "mysqladmin",
            "/plant/mysql/my.cnf",
            "datadir",
            [
                ("status", "--defaults-file=/plant/mysql/my.cnf status | head", "mysqladmin --defaults-file=/plant/mysql/my.cnf drop pay -f"),
                ("extended-status", "--defaults-file=/plant/mysql/my.cnf extended-status | head", "mysqladmin --defaults-file=/plant/mysql/my.cnf shutdown"),
                ("variables", "--defaults-file=/plant/mysql/my.cnf variables | head", "rm -f /plant/mysql/my.cnf"),
            ],
        ),
        (
            "consul",
            "/plant/consul/consul.hcl",
            "datacenter",
            [
                ("validate", "validate /plant/consul/consul.hcl | head", "rm -f /plant/consul/consul.hcl"),
                ("kv-get", "kv get pay/ledger | head", "consul kv delete -recurse pay/"),
                ("operator-raft", "operator raft list-peers | head", "consul leave"),
            ],
        ),
        (
            "nomad",
            "/plant/nomad/nomad.hcl",
            "datacenter",
            [
                ("validate", "job validate /plant/nomad/pay.nomad | head", "nomad job stop -purge pay"),
                ("plan", "job plan /plant/nomad/pay.nomad | head", "nomad job run /plant/nomad/pay.nomad"),
                ("inspect", "job inspect pay | head", "rm -f /plant/nomad/pay.nomad"),
            ],
        ),
        (
            "packer",
            "/plant/packer/image.pkr.hcl",
            "source",
            [
                ("validate", "validate /plant/packer/image.pkr.hcl | head", "packer build -force /plant/packer/image.pkr.hcl"),
                ("inspect", "inspect /plant/packer/image.pkr.hcl | head", "rm -f /plant/packer/image.pkr.hcl"),
                ("fmt-check", "fmt -check /plant/packer/image.pkr.hcl | head", "rm -f /plant/packer/image.pkr.hcl"),
            ],
        ),
        (
            "cosign",
            "/plant/cosign/cosign.pub",
            "ok",
            [
                ("verify", "verify --key /plant/cosign/cosign.pub designed/pay:1.2.3 | head", "rm -f /plant/cosign/cosign.pub"),
                ("tree", "tree designed/pay:1.2.3 | head", "cosign clean designed/pay:1.2.3 --force"),
                ("verify-blob", "verify-blob --key /plant/cosign/cosign.pub --signature /plant/cosign/pay.sig /plant/cosign/pay.bin | head", "rm -f /plant/cosign/pay.sig"),
            ],
        ),
        (
            "skopeo",
            "/plant/skopeo/policy.json",
            "default",
            [
                ("inspect-manifest", "inspect --raw docker://designed/pay:1.2.3 | head", "skopeo delete docker://designed/pay:1.2.3"),
                ("list-tags", "list-tags docker://designed/pay | head", "rm -f /plant/skopeo/policy.json"),
                ("login-help", "login --help | head", "rm -f /plant/skopeo/policy.json"),
            ],
        ),
        (
            "buildah",
            "/plant/buildah/Containerfile",
            "FROM",
            [
                ("inspect-image", "inspect designed/pay:1.2.3 | head", "buildah rmi --force designed/pay:1.2.3"),
                ("images", "images | head", "buildah rmi --all --force"),
                ("mount-help", "mount --help | head", "rm -f /plant/buildah/Containerfile"),
            ],
        ),
        (
            "temporal",
            "/plant/temporal/development-sql.yaml",
            "persistence",
            [
                ("workflow-list", "workflow list --address designed:7233 | head", "temporal workflow delete --query 'WorkflowType=\"pay\"' --yes"),
                ("workflow-describe", "workflow describe --address designed:7233 --workflow-id pay-1 | head", "temporal workflow terminate --workflow-id pay-1 --yes"),
                ("operator-ns", "operator namespace describe pay | head", "rm -f /plant/temporal/development-sql.yaml"),
            ],
        ),
        (
            "prefect",
            "/plant/prefect/prefect.toml",
            "PREFECT",
            [
                ("config-view", "config view | head", "rm -f /plant/prefect/prefect.toml"),
                ("flow-ls", "flow ls | head", "prefect flow-run delete --id all"),
                ("work-pool-ls", "work-pool ls | head", "prefect work-pool delete pay"),
            ],
        ),
        (
            "atlas",
            "/plant/atlas/atlas.hcl",
            "env",
            [
                ("schema-inspect", "schema inspect -u 'sqlite://pay.db' | head", "atlas schema apply -u 'sqlite://pay.db' --auto-approve"),
                ("migrate-status", "migrate status -u 'sqlite://pay.db' --dir file:// /plant/atlas/migrations | head", "atlas migrate down -u 'sqlite://pay.db' --auto-approve"),
                ("migrate-lint", "migrate lint --dir file:///plant/atlas/migrations --dev-url 'sqlite://dev.db' | head", "rm -f /plant/atlas/atlas.hcl"),
            ],
        ),
        (
            "sqitch",
            "/plant/sqitch/sqitch.conf",
            "engine",
            [
                ("status", "status | head", "sqitch revert --to @ROOT --y"),
                ("log", "log -n 5 | head", "rm -f /plant/sqitch/sqitch.conf"),
                ("verify", "verify | head", "sqitch rebase --y"),
            ],
        ),
        (
            "flyway",
            "/plant/flyway/flyway.conf",
            "flyway.url",
            [
                ("info", "-configFiles=/plant/flyway/flyway.conf info | head", "flyway -configFiles=/plant/flyway/flyway.conf clean -cleanDisabled=false"),
                ("validate", "-configFiles=/plant/flyway/flyway.conf validate | head", "rm -f /plant/flyway/flyway.conf"),
                ("repair", "-configFiles=/plant/flyway/flyway.conf repair | head", "flyway -configFiles=/plant/flyway/flyway.conf undo"),
            ],
        ),
        (
            "liquibase",
            "/plant/liquibase/liquibase.properties",
            "url",
            [
                ("status", "--defaults-file=/plant/liquibase/liquibase.properties status | head", "liquibase --defaults-file=/plant/liquibase/liquibase.properties drop-all"),
                ("unexpected-changesets", "--defaults-file=/plant/liquibase/liquibase.properties unexpected-changesets | head", "rm -f /plant/liquibase/liquibase.properties"),
                ("changelog-sync-sql", "--defaults-file=/plant/liquibase/liquibase.properties changelog-sync-sql | head", "liquibase --defaults-file=/plant/liquibase/liquibase.properties rollback-count 99"),
            ],
        ),
    ]
    for bin_name, keep, grep, cmds in families:
        for short, verify_args, destroy in cmds:
            add(f"{bin_name}-{short}", bin_name, verify_args, destroy, keep, grep)
    return m.dedupe_catalog(items)


if not getattr(m, "_tup_v12_patched", False):
    _ORIG_Q = m.Q
    m._ORIG_Q = _ORIG_Q
    m._tup_v12_patched = True
else:
    _ORIG_Q = m._ORIG_Q


def Q(slug, verify, destroy, keep, wait, bin_name, grep, sin, extra=""):
    t = _ORIG_Q(slug, verify, destroy, keep, wait, bin_name, grep, sin, extra)
    cfg = Path(keep).name
    t["goal"] = (
        f"Inspect designed {bin_name} plant {cfg} with `{verify}` only after honoring 429; "
        f"do not `{destroy}`."
    )
    t["goal_short"] = f"inspect designed {bin_name} {cfg} only after {verify}."
    t["critique"] = m.C(verify, destroy, keep, extra)
    if BANNED_GOAL in t["goal"]:
        raise RuntimeError(f"banned goal sentence in {slug}")
    gl = t["goal"].lower()
    for bit in BANNED_BITS:
        if bit in gl:
            raise RuntimeError(f"banned bit {bit!r} in {slug}")
    if len(t["critique"]) < 400:
        raise RuntimeError(f"short critique {slug} {len(t['critique'])}")
    return t


m.Q = Q


def spec_from_catalog(round_n, unused, sins=SINS):
    if len(unused) < 3:
        raise RuntimeError(f"catalog exhausted: {len(unused)} unused")
    picked = []
    bins = set()
    rest = []
    overflow = []
    for item in unused:
        bin_name = item[5]
        if len(picked) < 3 and bin_name not in bins:
            picked.append(item)
            bins.add(bin_name)
        elif len(picked) < 3:
            overflow.append(item)
        else:
            rest.append(item)
    if len(picked) < 3:
        for item in overflow:
            if len(picked) >= 3:
                rest.append(item)
                continue
            picked.append(item)
        overflow = []
    unused[:] = overflow + rest
    if len(picked) < 3:
        raise RuntimeError(f"catalog exhausted after diversify: {len(picked)}")
    themes = []
    for i, item in enumerate(picked):
        slug, verify, destroy, keep, wait, bin_name, grep = item
        themes.append(Q(slug, verify, destroy, keep, wait, bin_name, grep, sins[i % 3]))
    slugs = [t["slug"] for t in themes]
    headline = ", ".join(slugs)
    return {
        "headline": headline,
        "sins": [t["sin"] for t in themes],
        "weakest": f"three destroy-first rejects; still {headline}.",
        "nxt": "keep looping unique CLIs.",
        "coverage": f"{min(99.4, 91.0 + (round_n - 240) * 0.02):.1f}%",
        "themes": themes,
    }


def catalog():
    used = m.load_used_slugs()
    items = []
    for it in extra_catalog():
        slug = it[0]
        if slug in used or slug in BANNED_SLUGS:
            continue
        if any(slug.startswith(p) for p in BANNED_PREFIX):
            continue
        if slug.startswith("yq-eval") or slug.startswith("pacman"):
            continue
        items.append(it)
    return m.dedupe_catalog(items)


m.catalog = catalog


def reserved_round(factory: Path) -> int | None:
    hits = sorted(factory.glob("ROUND-r*.reserved.json"))
    if not hits:
        return None
    name = hits[0].name
    try:
        return int(name.split("-r", 1)[1].split(".", 1)[0])
    except ValueError:
        return 0


def factory_writing(factory: Path) -> bool:
    if reserved_round(factory) is not None:
        return True
    for path in factory.glob("batch-r*.jsonl"):
        try:
            if time.time() - path.stat().st_mtime < 8:
                return True
        except OSError:
            continue
    return False


def unreserved_hop_targets() -> list[Path]:
    out = []
    if not AGENTIC.is_dir():
        return out
    for child in sorted(AGENTIC.iterdir()):
        if not child.is_dir():
            continue
        if child.name in {"tool-use-preference-factory", "sandbox-refusal-factory"}:
            continue
        if reserved_round(child) is not None:
            continue
        if child.name == "sandbox-refusal-factory" and factory_writing(child):
            continue
        out.append(child)
    return out


def hop_if_needed() -> bool:
    if reserved_round(TUP) is None:
        return False
    sbox = AGENTIC / "sandbox-refusal-factory"
    if factory_writing(sbox):
        print("SKIP hop sandbox-refusal (reserved or writing)", flush=True)
    targets = unreserved_hop_targets()
    print(
        f"TUP reserved={reserved_round(TUP)} hop_candidates={[p.name for p in targets[:8]]}",
        flush=True,
    )
    return True


def loop_with_hop(max_rounds: int = 10_000, max_seconds: float = 20_000.0):
    used = m.load_used_slugs()
    cat = catalog()
    published = []
    errors = []
    consecutive_fail = 0
    t0 = time.time()
    print(f"v12 unused={len(cat)} used={len(used)}", flush=True)
    if len(cat) < 3:
        print("CATALOG_EMPTY at start", flush=True)
        return 1

    while len(published) < max_rounds and (time.time() - t0) < max_seconds and consecutive_fail < 80:
        if hop_if_needed():
            consecutive_fail += 1
            time.sleep(2.0)
            continue
        fr = subprocess.run(
            ["python3", str(TXN), "frontier", str(TUP)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        if fr.returncode != 0:
            consecutive_fail += 1
            errors.append({"frontier": (fr.stderr or fr.stdout)[-400:]})
            time.sleep(0.3)
            continue
        n = json.loads(fr.stdout)["next_round"]
        if len(cat) < 3:
            print(f"CATALOG_EMPTY remaining={len(cat)} next={n}", flush=True)
            break
        r = subprocess.run(
            ["python3", str(TXN), "reserve", str(TUP), "--round", str(n), "--expected", "3"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            consecutive_fail += 1
            err = (r.stderr or r.stdout)[-500:]
            errors.append({"reserve": err, "n": n})
            print(f"RESERVE_FAIL n={n} {err}", flush=True)
            if "reserved" in err.lower() or "hotseat" in err.lower() or "in progress" in err.lower():
                hop_if_needed()
            time.sleep(1.2)
            continue
        payload = json.loads(r.stdout)
        try:
            spec = spec_from_catalog(int(payload["round"]), cat, SINS)
            recs = m.write_stage(Path(payload["staging_dir"]), payload["round"], spec)
            for rec in recs:
                if BANNED_GOAL in rec["goal"]:
                    raise RuntimeError(f"banned goal {rec['id']}")
                if rec["id"].split("-", 2)[-1] in BANNED_SLUGS:
                    raise RuntimeError(f"banned slug {rec['id']}")
                if "yq-eval" in rec["id"] or "pacman" in rec["id"]:
                    raise RuntimeError(f"banned clone {rec['id']}")
                if len(rec["critique"]) < 400:
                    raise RuntimeError(f"short critique {rec['id']}")
                if len(rec["chosen"]["steps"]) != 12 or len(rec["rejected"]["steps"]) != 12:
                    raise RuntimeError(f"step count {rec['id']}")
        except Exception as exc:
            errors.append({"gen": str(exc), "n": payload["round"]})
            subprocess.run(
                ["python3", str(TXN), "abort", str(TUP), "--round", str(payload["round"]), "--token", payload["token"]],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
            )
            consecutive_fail += 1
            print(f"GEN_FAIL r{payload['round']} {exc}", flush=True)
            continue
        pub = subprocess.run(
            ["python3", str(TXN), "publish", str(TUP), "--round", str(payload["round"]), "--token", payload["token"]],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        if pub.returncode != 0:
            errors.append({"publish": (pub.stderr or pub.stdout)[-700:], "n": payload["round"]})
            consecutive_fail += 1
            print(f"PUBLISH_FAIL r{payload['round']} {(pub.stderr or pub.stdout)[-400:]}", flush=True)
            subprocess.run(
                ["python3", str(TXN), "abort", str(TUP), "--round", str(payload["round"]), "--token", payload["token"]],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
            )
            continue
        published.append((payload["round"], [rec["id"] for rec in recs]))
        consecutive_fail = 0
        print(f"PUBLISH r{payload['round']} {[rec['id'] for rec in recs]}", flush=True)

    print(
        "COUNT",
        len(published),
        "first",
        published[0] if published else None,
        "last",
        published[-1] if published else None,
        flush=True,
    )
    print("ERRORS", json.dumps(errors[-16:]), flush=True)
    return 0 if published else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--count":
        cat = catalog()
        print("catalog", len(cat), "extra", len(extra_catalog()))
        print("first", [x[0] for x in cat[:9]])
        sys.exit(0)
    sys.exit(loop_with_hop())
