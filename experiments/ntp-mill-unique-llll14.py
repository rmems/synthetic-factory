#!/usr/bin/env python3
"""NTP unique leftover leftover leftover leftover mill wave 14: NEW dest plants. BAN dnsmasq leftover clones."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ntp_mill_unique_llll2",
    ROOT / "experiments/ntp-mill-unique-llll2.py",
)
mod2 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod2)

s_from = mod2.s_from
l_from = mod2.l_from

SUCCESS = [
    s_from(0, "pytest-cache-leftover-as-dest", "ptch", "pytest cache leftover", ".pytest_cache", "pytest cache leftover", "pytest leftover && ls .pytest_cache", "not pytest leftover; pytest cache leftover is not dest", "treat pytest leftover cache as dest then CLI parquet.", "pytest leftover; # pytest_cache claimed dest", "pytest leftover|.pytest_cache"),
    s_from(1, "hypothesis-exampledb-leftover-as-dest", "hyex", "hypothesis exampledb leftover", ".hypothesis/examples", "Hypothesis exampledb leftover", "hypothesis leftover && ls .hypothesis/examples", "not hypothesis leftover; Hypothesis exampledb leftover is not dest", "treat Hypothesis leftover exampledb as dest then CLI parquet.", "hypothesis leftover; # examples claimed dest", "hypothesis leftover|.hypothesis/examples"),
    s_from(2, "coverage-sqlite-leftover-as-dest", "cvsql", "coverage sqlite leftover", ".coverage", "coverage sqlite leftover", "coverage leftover && ls .coverage", "not coverage leftover; coverage sqlite leftover is not dest", "treat coverage leftover sqlite as dest then CLI parquet.", "coverage leftover; # .coverage claimed dest", "coverage leftover|.coverage"),
    s_from(3, "junit-xml-leftover-as-dest", "juxm", "junit xml leftover", "junit.xml", "JUnit XML leftover", "pytest leftover && cat junit.xml", "not junit leftover; JUnit XML leftover is not dest", "treat JUnit leftover XML as dest then CLI parquet.", "junit leftover; # junit.xml claimed dest", "junit leftover|junit.xml"),
    s_from(4, "tap-out-leftover-as-dest", "tpout", "tap out leftover", "results.tap", "TAP leftover", "prove leftover && cat results.tap", "not tap leftover; TAP leftover is not dest", "treat TAP leftover as dest then CLI parquet.", "tap leftover; # results.tap claimed dest", "tap leftover|results.tap"),
    s_from(5, "xunit-xml-leftover-as-dest", "xuxm", "xunit xml leftover", "xunit.xml", "xUnit XML leftover", "dotnet leftover && cat xunit.xml", "not xunit leftover; xUnit XML leftover is not dest", "treat xUnit leftover XML as dest then CLI parquet.", "xunit leftover; # xunit.xml claimed dest", "xunit leftover|xunit.xml"),
    s_from(6, "allure-results-leftover-as-dest", "alrs", "allure results leftover", "allure-results", "Allure results leftover", "allure leftover && ls allure-results", "not allure leftover; Allure results leftover is not dest", "treat Allure leftover results as dest then CLI parquet.", "allure leftover; # allure-results claimed dest", "allure leftover|allure-results"),
    s_from(7, "robot-output-leftover-as-dest", "rbot", "robot output leftover", "output.xml", "Robot output leftover XML", "robot leftover && cat output.xml", "not robot leftover; Robot output leftover is not dest", "treat Robot leftover XML as dest then CLI parquet.", "robot leftover; # output.xml claimed dest", "robot leftover|output.xml"),
    s_from(8, "behave-json-leftover-as-dest", "bhjs", "behave json leftover", "behave.json", "behave JSON leftover", "behave leftover && cat behave.json", "not behave leftover; behave JSON leftover is not dest", "treat behave leftover JSON as dest then CLI parquet.", "behave leftover; # behave.json claimed dest", "behave leftover|behave.json"),
    s_from(9, "cucumber-json-leftover-as-dest", "cjjs", "cucumber json leftover", "cucumber.json", "Cucumber JSON leftover", "cucumber leftover && cat cucumber.json", "not cucumber leftover; Cucumber JSON leftover is not dest", "treat Cucumber leftover JSON as dest then CLI parquet.", "cucumber leftover; # cucumber.json claimed dest", "cucumber leftover|cucumber.json"),
    s_from(10, "rspec-json-leftover-as-dest", "rsjs", "rspec json leftover", "rspec.json", "RSpec JSON leftover", "rspec leftover && cat rspec.json", "not rspec leftover; RSpec JSON leftover is not dest", "treat RSpec leftover JSON as dest then CLI parquet.", "rspec leftover; # rspec.json claimed dest", "rspec leftover|rspec.json"),
    s_from(11, "minitest-json-leftover-as-dest", "mtjs", "minitest json leftover", "minitest.json", "Minitest JSON leftover", "ruby leftover && cat minitest.json", "not minitest leftover; Minitest JSON leftover is not dest", "treat Minitest leftover JSON as dest then CLI parquet.", "minitest leftover; # minitest.json claimed dest", "minitest leftover|minitest.json"),
    s_from(12, "jest-coverage-leftover-as-dest", "jtcv", "jest coverage leftover", "coverage/coverage-final.json", "Jest coverage leftover JSON", "jest leftover && cat coverage/coverage-final.json", "not jest leftover; Jest coverage leftover is not dest", "treat Jest leftover coverage as dest then CLI parquet.", "jest leftover; # coverage-final json claimed dest", "jest leftover|coverage/coverage-final.json"),
    s_from(13, "vitest-coverage-leftover-as-dest", "vtcv", "vitest coverage leftover", "coverage/coverage-final.json", "Vitest coverage leftover JSON", "vitest leftover && cat coverage/coverage-final.json", "not vitest leftover; Vitest coverage leftover is not dest", "treat Vitest leftover coverage as dest then CLI parquet.", "vitest leftover; # coverage-final json claimed dest", "vitest leftover|coverage/coverage-final.json"),
    s_from(14, "mocha-json-leftover-as-dest", "mcjs", "mocha json leftover", "mocha.json", "Mocha JSON leftover", "mocha leftover && cat mocha.json", "not mocha leftover; Mocha JSON leftover is not dest", "treat Mocha leftover JSON as dest then CLI parquet.", "mocha leftover; # mocha.json claimed dest", "mocha leftover|mocha.json"),
    s_from(15, "ava-tap-leftover-as-dest", "avtp", "ava tap leftover", "ava.tap", "AVA TAP leftover", "ava leftover && cat ava.tap", "not ava leftover; AVA TAP leftover is not dest", "treat AVA leftover TAP as dest then CLI parquet.", "ava leftover; # ava.tap claimed dest", "ava leftover|ava.tap"),
    s_from(16, "jasmine-json-leftover-as-dest", "jsjs", "jasmine json leftover", "jasmine.json", "Jasmine JSON leftover", "jasmine leftover && cat jasmine.json", "not jasmine leftover; Jasmine JSON leftover is not dest", "treat Jasmine leftover JSON as dest then CLI parquet.", "jasmine leftover; # jasmine.json claimed dest", "jasmine leftover|jasmine.json"),
    s_from(17, "karma-coverage-leftover-as-dest", "kmcv", "karma coverage leftover", "coverage/karma.json", "Karma coverage leftover JSON", "karma leftover && cat coverage/karma.json", "not karma leftover; Karma coverage leftover is not dest", "treat Karma leftover coverage as dest then CLI parquet.", "karma leftover; # karma.json claimed dest", "karma leftover|coverage/karma.json"),
    s_from(18, "cypress-videos-leftover-as-dest", "cyvd", "cypress videos leftover", "cypress/videos", "Cypress videos leftover", "cypress leftover && ls cypress/videos", "not cypress leftover; Cypress videos leftover is not dest", "treat Cypress leftover videos as dest then CLI parquet.", "cypress leftover; # videos claimed dest", "cypress leftover|cypress/videos"),
    s_from(19, "playwright-trace-leftover-as-dest", "pwtr", "playwright trace leftover", "test-results/trace.zip", "Playwright trace leftover", "playwright leftover && ls test-results/trace.zip", "not playwright leftover; Playwright trace leftover is not dest", "treat Playwright leftover trace as dest then CLI parquet.", "playwright leftover; # trace.zip claimed dest", "playwright leftover|test-results/trace.zip"),
    s_from(20, "selenium-session-leftover-as-dest", "slss", "selenium session leftover", ".selenium/session.json", "Selenium session leftover JSON", "selenium leftover && cat .selenium/session.json", "not selenium leftover; Selenium session leftover is not dest", "treat Selenium leftover JSON as dest then CLI parquet.", "selenium leftover; # session json claimed dest", "selenium leftover|.selenium/session"),
    s_from(21, "webdriver-log-leftover-as-dest", "wdlg", "webdriver log leftover", ".webdriver/log.txt", "WebDriver log leftover", "webdriver leftover && cat .webdriver/log.txt", "not webdriver leftover; WebDriver log leftover is not dest", "treat WebDriver leftover log as dest then CLI parquet.", "webdriver leftover; # log txt claimed dest", "webdriver leftover|.webdriver/log"),
    s_from(22, "locust-stats-leftover-as-dest", "lcst", "locust stats leftover", "locust_stats.csv", "Locust stats leftover CSV", "locust leftover && cat locust_stats.csv", "not locust leftover; Locust stats leftover is not dest", "treat Locust leftover stats as dest then CLI parquet.", "locust leftover; # locust_stats csv claimed dest", "locust leftover|locust_stats.csv"),
    s_from(23, "k6-summary-leftover-as-dest", "k6sm", "k6 summary leftover", "k6-summary.json", "k6 summary leftover JSON", "k6 leftover && cat k6-summary.json", "not k6 leftover; k6 summary leftover is not dest", "treat k6 leftover summary as dest then CLI parquet.", "k6 leftover; # k6-summary json claimed dest", "k6 leftover|k6-summary.json"),
    s_from(24, "gatling-sim-leftover-as-dest", "gtsm", "gatling sim leftover", "gatling/simulation.log", "Gatling simulation leftover", "gatling leftover && cat gatling/simulation.log", "not gatling leftover; Gatling simulation leftover is not dest", "treat Gatling leftover simulation as dest then CLI parquet.", "gatling leftover; # simulation.log claimed dest", "gatling leftover|gatling/simulation.log"),
    s_from(25, "jmeter-jtl-leftover-as-dest", "jmjl", "jmeter jtl leftover", "results.jtl", "JMeter JTL leftover", "jmeter leftover && cat results.jtl", "not jmeter leftover; JMeter JTL leftover is not dest", "treat JMeter leftover JTL as dest then CLI parquet.", "jmeter leftover; # results.jtl claimed dest", "jmeter leftover|results.jtl"),
    s_from(26, "wrk-log-leftover-as-dest", "wrkl", "wrk log leftover", "wrk.log", "wrk log leftover", "wrk leftover && cat wrk.log", "not wrk leftover; wrk log leftover is not dest", "treat wrk leftover log as dest then CLI parquet.", "wrk leftover; # wrk.log claimed dest", "wrk leftover|wrk.log"),
    s_from(27, "hey-out-leftover-as-dest", "hyot", "hey out leftover", "hey.out", "hey out leftover", "hey leftover && cat hey.out", "not hey leftover; hey out leftover is not dest", "treat hey leftover out as dest then CLI parquet.", "hey leftover; # hey.out claimed dest", "hey leftover|hey.out"),
    s_from(28, "fortio-json-leftover-as-dest", "ftjs", "fortio json leftover", "fortio.json", "Fortio JSON leftover", "fortio leftover && cat fortio.json", "not fortio leftover; Fortio JSON leftover is not dest", "treat Fortio leftover JSON as dest then CLI parquet.", "fortio leftover; # fortio.json claimed dest", "fortio leftover|fortio.json"),
    s_from(29, "ghz-json-leftover-as-dest", "gzjs", "ghz json leftover", "ghz.json", "ghz JSON leftover", "ghz leftover && cat ghz.json", "not ghz leftover; ghz JSON leftover is not dest", "treat ghz leftover JSON as dest then CLI parquet.", "ghz leftover; # ghz.json claimed dest", "ghz leftover|ghz.json"),
    s_from(30, "siege-log-leftover-as-dest", "sglg", "siege log leftover", "siege.log", "Siege log leftover", "siege leftover && cat siege.log", "not siege leftover; Siege log leftover is not dest", "treat Siege leftover log as dest then CLI parquet.", "siege leftover; # siege.log claimed dest", "siege leftover|siege.log"),
    s_from(31, "ab-out-leftover-as-dest", "abot", "ab out leftover", "ab.out", "ab out leftover", "ab leftover && cat ab.out", "not ab leftover; ab out leftover is not dest", "treat ab leftover out as dest then CLI parquet.", "ab leftover; # ab.out claimed dest", "ab leftover|ab.out"),
]

LEFTOVER = [
    l_from(0, "pytest-basetemp-leftover-handoff", "ptbt", ".pytest_cache/v/cache", "pytest basetemp leftover", "pytest basetemp leftover", "not pytest cache leftover; leftover pytest basetemp as dest", "ship leftover pytest basetemp as dest.", "basetemp leftover; # cache on disk", "pytest leftover|.pytest_cache/v/cache"),
    l_from(1, "hypothesis-settings-leftover-handoff", "hyst", ".hypothesis/settings", "hypothesis settings leftover", "Hypothesis settings leftover", "not hypothesis exampledb leftover; leftover Hypothesis settings as dest", "ship leftover Hypothesis settings as dest.", "settings leftover; # settings on disk", "hypothesis leftover|.hypothesis/settings"),
    l_from(2, "coverage-xml-leftover-handoff", "cvxm", "coverage.xml", "coverage xml leftover", "coverage XML leftover", "not coverage sqlite leftover; leftover coverage XML as dest", "ship leftover coverage XML as dest.", "xml leftover; # coverage.xml on disk", "coverage leftover|coverage.xml"),
    l_from(3, "junit-properties-leftover-handoff", "jupr", "junit.properties", "junit properties leftover", "JUnit properties leftover", "not junit xml leftover; leftover JUnit properties as dest", "ship leftover JUnit properties as dest.", "properties leftover; # junit.properties on disk", "junit leftover|junit.properties"),
    l_from(4, "tap-yaml-leftover-handoff", "tpym", "results.yml", "tap yaml leftover", "TAP YAML leftover", "not tap out leftover; leftover TAP YAML as dest", "ship leftover TAP YAML as dest.", "yaml leftover; # results.yml on disk", "tap leftover|results.yml"),
    l_from(5, "xunit-trx-leftover-handoff", "xutx", "results.trx", "xunit trx leftover", "xUnit TRX leftover", "not xunit xml leftover; leftover xUnit TRX as dest", "ship leftover xUnit TRX as dest.", "trx leftover; # results.trx on disk", "xunit leftover|results.trx"),
    l_from(6, "allure-history-leftover-handoff", "alhs", "allure-results/history", "allure history leftover", "Allure history leftover", "not allure results leftover; leftover Allure history as dest", "ship leftover Allure history as dest.", "history leftover; # history on disk", "allure leftover|allure-results/history"),
    l_from(7, "robot-log-leftover-handoff", "rblg", "log.html", "robot log leftover", "Robot log leftover", "not robot output leftover; leftover Robot log as dest", "ship leftover Robot log as dest.", "log leftover; # log.html on disk", "robot leftover|log.html"),
    l_from(8, "behave-pretty-leftover-handoff", "bhpr", "behave-pretty.txt", "behave pretty leftover", "behave pretty leftover", "not behave json leftover; leftover behave pretty as dest", "ship leftover behave pretty as dest.", "pretty leftover; # txt on disk", "behave leftover|behave-pretty.txt"),
    l_from(9, "cucumber-ndjson-leftover-handoff", "cjnd", "cucumber.ndjson", "cucumber ndjson leftover", "Cucumber ndjson leftover", "not cucumber json leftover; leftover Cucumber ndjson as dest", "ship leftover Cucumber ndjson as dest.", "ndjson leftover; # ndjson on disk", "cucumber leftover|cucumber.ndjson"),
    l_from(10, "rspec-examples-leftover-handoff", "rsex", "examples.txt", "rspec examples leftover", "RSpec examples leftover", "not rspec json leftover; leftover RSpec examples as dest", "ship leftover RSpec examples as dest.", "examples leftover; # txt on disk", "rspec leftover|examples.txt"),
    l_from(11, "minitest-pride-leftover-handoff", "mtpr", "pride.txt", "minitest pride leftover", "Minitest pride leftover", "not minitest json leftover; leftover Minitest pride as dest", "ship leftover Minitest pride as dest.", "pride leftover; # txt on disk", "minitest leftover|pride.txt"),
    l_from(12, "jest-junit-leftover-handoff", "jtju", "junit.xml", "jest junit leftover", "Jest JUnit leftover", "not jest coverage leftover; leftover Jest JUnit as dest", "ship leftover Jest JUnit as dest.", "junit leftover; # junit.xml on disk", "jest leftover|junit.xml"),
    l_from(13, "vitest-junit-leftover-handoff", "vtju", "junit.xml", "vitest junit leftover", "Vitest JUnit leftover", "not vitest coverage leftover; leftover Vitest JUnit as dest", "ship leftover Vitest JUnit as dest.", "junit leftover; # junit.xml on disk", "vitest leftover|junit.xml"),
    l_from(14, "mocha-spec-leftover-handoff", "mcsp", "mocha.spec", "mocha spec leftover", "Mocha spec leftover", "not mocha json leftover; leftover Mocha spec as dest", "ship leftover Mocha spec as dest.", "spec leftover; # mocha.spec on disk", "mocha leftover|mocha.spec"),
    l_from(15, "ava-snapshot-leftover-handoff", "avsn", "snapshots", "ava snapshot leftover", "AVA snapshot leftover", "not ava tap leftover; leftover AVA snapshot as dest", "ship leftover AVA snapshot as dest.", "snapshot leftover; # snapshots on disk", "ava leftover|snapshots"),
    l_from(16, "jasmine-junit-leftover-handoff", "jsju", "jasmine-junit.xml", "jasmine junit leftover", "Jasmine JUnit leftover", "not jasmine json leftover; leftover Jasmine JUnit as dest", "ship leftover Jasmine JUnit as dest.", "junit leftover; # jasmine-junit.xml on disk", "jasmine leftover|jasmine-junit.xml"),
    l_from(17, "karma-junit-leftover-handoff", "kmju", "karma-junit.xml", "karma junit leftover", "Karma JUnit leftover", "not karma coverage leftover; leftover Karma JUnit as dest", "ship leftover Karma JUnit as dest.", "junit leftover; # karma-junit.xml on disk", "karma leftover|karma-junit.xml"),
    l_from(18, "cypress-screenshots-leftover-handoff", "cyss", "cypress/screenshots", "cypress screenshots leftover", "Cypress screenshots leftover", "not cypress videos leftover; leftover Cypress screenshots as dest", "ship leftover Cypress screenshots as dest.", "screenshots leftover; # screenshots on disk", "cypress leftover|cypress/screenshots"),
    l_from(19, "playwright-report-leftover-handoff", "pwrp", "playwright-report", "playwright report leftover", "Playwright report leftover", "not playwright trace leftover; leftover Playwright report as dest", "ship leftover Playwright report as dest.", "report leftover; # playwright-report on disk", "playwright leftover|playwright-report"),
    l_from(20, "selenium-log-leftover-handoff", "sllg", ".selenium/server.log", "selenium log leftover", "Selenium log leftover", "not selenium session leftover; leftover Selenium log as dest", "ship leftover Selenium log as dest.", "log leftover; # server.log on disk", "selenium leftover|.selenium/server.log"),
    l_from(21, "webdriver-profile-leftover-handoff", "wdpr", ".webdriver/profile", "webdriver profile leftover", "WebDriver profile leftover", "not webdriver log leftover; leftover WebDriver profile as dest", "ship leftover WebDriver profile as dest.", "profile leftover; # profile on disk", "webdriver leftover|.webdriver/profile"),
    l_from(22, "locust-report-leftover-handoff", "lcrt", "locust_report.json", "locust report leftover", "Locust report leftover JSON", "not locust stats leftover; leftover Locust report JSON as dest", "ship leftover Locust report JSON as dest.", "report leftover; # locust_report.json on disk", "locust leftover|locust_report.json"),
    l_from(23, "k6-csv-leftover-handoff", "k6cs", "k6.csv", "k6 csv leftover", "k6 CSV leftover", "not k6 summary leftover; leftover k6 CSV as dest", "ship leftover k6 CSV as dest.", "csv leftover; # k6.csv on disk", "k6 leftover|k6.csv"),
    l_from(24, "gatling-json-leftover-handoff", "gtjs", "gatling/js/stats.json", "gatling json leftover", "Gatling JSON leftover", "not gatling sim leftover; leftover Gatling JSON as dest", "ship leftover Gatling JSON as dest.", "json leftover; # stats.json on disk", "gatling leftover|gatling/js/stats.json"),
    l_from(25, "jmeter-log-leftover-handoff", "jmlg", "jmeter.log", "jmeter log leftover", "JMeter log leftover", "not jmeter jtl leftover; leftover JMeter log as dest", "ship leftover JMeter log as dest.", "log leftover; # jmeter.log on disk", "jmeter leftover|jmeter.log"),
    l_from(26, "wrk-lua-leftover-handoff", "wrku", "script.lua", "wrk lua leftover", "wrk Lua leftover", "not wrk log leftover; leftover wrk Lua as dest", "ship leftover wrk Lua as dest.", "lua leftover; # script.lua on disk", "wrk leftover|script.lua"),
    l_from(27, "hey-csv-leftover-handoff", "hycs", "hey.csv", "hey csv leftover", "hey CSV leftover", "not hey out leftover; leftover hey CSV as dest", "ship leftover hey CSV as dest.", "csv leftover; # hey.csv on disk", "hey leftover|hey.csv"),
    l_from(28, "fortio-csv-leftover-handoff", "ftcs", "fortio.csv", "fortio csv leftover", "Fortio CSV leftover", "not fortio json leftover; leftover Fortio CSV as dest", "ship leftover Fortio CSV as dest.", "csv leftover; # fortio.csv on disk", "fortio leftover|fortio.csv"),
    l_from(29, "ghz-csv-leftover-handoff", "gzcs", "ghz.csv", "ghz csv leftover", "ghz CSV leftover", "not ghz json leftover; leftover ghz CSV as dest", "ship leftover ghz CSV as dest.", "csv leftover; # ghz.csv on disk", "ghz leftover|ghz.csv"),
    l_from(30, "siege-csv-leftover-handoff", "sgcs", "siege.csv", "siege csv leftover", "Siege CSV leftover", "not siege log leftover; leftover Siege CSV as dest", "ship leftover Siege CSV as dest.", "csv leftover; # siege.csv on disk", "siege leftover|siege.csv"),
    l_from(31, "ab-tsv-leftover-handoff", "abtv", "ab.tsv", "ab tsv leftover", "ab TSV leftover", "not ab out leftover; leftover ab TSV as dest", "ship leftover ab TSV as dest.", "tsv leftover; # ab.tsv on disk", "ab leftover|ab.tsv"),
]

mod2.SUCCESS = SUCCESS
mod2.LEFTOVER = LEFTOVER
mod2.BANNED_SLUGS = set(mod2.BANNED_SLUGS) | {
    "dnsmasq-hosts-leftover-as-dest",
    "dnsmasq-lease-leftover-handoff",
}
pair_for = mod2.pair_for
notes_for = mod2.notes_for
write_stage = mod2.write_stage


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("usage: ntp-mill-unique-llll14.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = write_stage(staging, round_n)
    print(f"wrote r{round_n} {i1} {i2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
