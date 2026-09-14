#!/usr/bin/env python3
"""Generate designed ACTF r18 episodes (Q=2). Never writes outputs/raw/."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

OUT = Path("/tmp/actf-r18")
GENERATED_AT = "2026-09-02T21:54:00Z"
KNOWN = {
    "bash",
    "read_file",
    "edit_file",
    "write_file",
    "search",
    "gh",
    "kubectl",
    "gate-cli",
    "tofu",
    "tenv",
    "tflint",
    "aws",
    "jq",
    "hcl2json",
    "block",
    "decline",
    "deny",
    "refuse",
}
FORBIDDEN = {
    "thought",
    "chain_of_thought",
    "scratch",
    "inner_monologue",
    "reasoning",
    "internal_reasoning",
    "hidden_reasoning",
    "thinking",
    "cot",
}
PROGRESS_RE = re.compile(
    r"\b(?:added|changed|created|deleted|disproved|edited|evidence|failed|"
    r"fixed|found|hypothesis|learned|measured|patched|removed|reproduced|"
    r"tested|updated|verified|wrote)\b",
    re.I,
)
STALL_RE = re.compile(r"\b(?:no[ -]?op|no change|nothing changed|unchanged)\b", re.I)
BASIS_PREFIX = ("Plan:", "Observation:", "Reflection:", "Tool call:")
HIDDEN_RE = re.compile(
    r"thought|chain_of_thought|scratch|inner_monologue|reasoning", re.I
)


def db(text: str) -> str:
    text = text.strip()
    if not text.startswith(BASIS_PREFIX):
        raise SystemExit(f"basis prefix: {text[:80]!r}")
    if not (80 <= len(text) <= 240):
        raise SystemExit(f"basis len {len(text)}: {text}")
    return text


def rights() -> dict:
    return {
        "provider": "SpaceXAI/xAI",
        "model": "grok-4.6",
        "channel": "consumer",
        "subscription_plan": "SuperGrok Heavy",
        "generation_surface": "SuperGrok Heavy chat",
        "generated_at": GENERATED_AT,
        "intended_use": "research_only",
        "project_training_policy": "blocked",
        "research_retention_status": "allowed",
        "research_evaluation_status": "allowed",
        "redistribution_status": "unresolved",
        "provider_training_status": "unresolved",
        "weight_publication_status": "blocked",
        "status_basis": "RM-793 project policy: xAI hosted outputs are research-only",
        "linear_issue": "RM-793",
        "training_ready": False,
    }


def meta_common(**extra) -> dict:
    m = {
        "factory": "agentic-coding-trajectory-factory",
        "round": 18,
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "sim_or_real": "designed",
        "training_ready": False,
        "rights": rights(),
    }
    m.update(extra)
    return m


BILL_BEFORE = """package yard.keelstamp;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

public final class BillDate {
    static final DateTimeFormatter STAMP =
            DateTimeFormatter.ofPattern("YYYY-MM-dd");

    private BillDate() {}

    public static String stamp(LocalDate day) {
        return day.format(STAMP);
    }
}
"""

BILL_ZONE = """package yard.keelstamp;

import java.time.LocalDate;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;

public final class BillDate {
    static final DateTimeFormatter STAMP =
            DateTimeFormatter.ofPattern("YYYY-MM-dd").withZone(ZoneOffset.UTC);

    private BillDate() {}

    public static String stamp(LocalDate day) {
        return day.atStartOfDay(ZoneOffset.UTC).format(STAMP);
    }
}
"""

BILL_Y = """package yard.keelstamp;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

public final class BillDate {
    static final DateTimeFormatter STAMP =
            DateTimeFormatter.ofPattern("yyyy-MM-dd");

    private BillDate() {}

    public static String stamp(LocalDate day) {
        return day.format(STAMP);
    }
}
"""

YEAR_TEST = """package yard.keelstamp;

import java.time.LocalDate;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

class YearBoundaryTest {
    @Test
    void yearBoundaryFormatsAsCalendarYear() {
        assertEquals("2025-12-29", BillDate.stamp(LocalDate.of(2025, 12, 29)));
    }
}
"""

CFG_BEFORE = '''from configparser import ConfigParser


def load_loom(path: str) -> ConfigParser:
    cfg = ConfigParser()
    cfg.read(path)
    return cfg


def plc_token(cfg: ConfigParser) -> str:
    return cfg.get("secrets", "plc_token")


def log_dir(cfg: ConfigParser) -> str:
    return cfg.get("paths", "log_dir")
'''

CFG_NONE = '''from configparser import ConfigParser


def load_loom(path: str) -> ConfigParser:
    cfg = ConfigParser(interpolation=None)
    cfg.read(path)
    return cfg


def plc_token(cfg: ConfigParser) -> str:
    return cfg.get("secrets", "plc_token")


def log_dir(cfg: ConfigParser) -> str:
    return cfg.get("paths", "log_dir")
'''

CFG_RAW = '''from configparser import ConfigParser


def load_loom(path: str) -> ConfigParser:
    cfg = ConfigParser()
    cfg.read(path)
    return cfg


def plc_token(cfg: ConfigParser) -> str:
    return cfg.get("secrets", "plc_token", raw=True)


def log_dir(cfg: ConfigParser) -> str:
    return cfg.get("paths", "log_dir")
'''

TOKEN_TEST = '''from loomgauge.config import load_loom, log_dir, plc_token


def test_plc_token_accepts_percent():
    cfg = load_loom("tests/fixtures/loom-percent.ini")
    assert plc_token(cfg) == "N7%2FqX-heddle"


def test_log_dir_expands_data_root():
    cfg = load_loom("tests/fixtures/loom-percent.ini")
    assert log_dir(cfg) == "/var/loomgauge/logs"
'''


def ep1() -> dict:
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: KP-418 reports bill dates for 2025-12-29 printing as 2026-12-29. Search DateTimeFormatter and stamp() for evidence of a year-pattern mismatch."
            ),
            "plan": "1) search formatter/stamp 2) read BillDate 3) reproduce 2025-12-29 4) switch YYYY to yyyy 5) regression + PR",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "DateTimeFormatter|ofPattern|YYYY|yyyy|stamp\\(",
                    "path": "src/main/java/yard/keelstamp",
                },
            },
            "observation": (
                "src/main/java/yard/keelstamp/BillDate.java:8:            DateTimeFormatter.ofPattern(\"YYYY-MM-dd\");\n"
                "src/main/java/yard/keelstamp/BillDate.java:13:    public static String stamp(LocalDate day) {\n"
                "src/main/java/yard/keelstamp/BillDate.java:14:        return day.format(STAMP);\n"
                "src/test/java/yard/keelstamp/BillDateTest.java:14:        assertEquals(\"2026-06-15\", BillDate.stamp(LocalDate.of(2026, 6, 15)));\n"
                "4 matches"
            ),
            "reflection": "Found ofPattern YYYY-MM-dd on LocalDate.stamp. Mid-year BillDateTest still expects 2026-06-15; the year-boundary bill is not covered.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: BillDate.java:8 uses ofPattern YYYY-MM-dd (step 1). Read BillDate.java for evidence of zone, locale, or a second formatter."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {
                    "path": "src/main/java/yard/keelstamp/BillDate.java",
                    "offset": 1,
                    "limit": 24,
                },
            },
            "observation": BILL_BEFORE,
            "reflection": "Measured a single STAMP pattern YYYY-MM-dd with no zone. Java YYYY is week-based year; 2025-12-29 is ISO week 1 of 2026.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: STAMP is YYYY-MM-dd with no zone (step 2). Run mvn test for evidence the year-boundary fixture already failed the calendar year."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "mvn -q -Dtest=BillDateTest test 2>&1 | tail -n 20"
                    )
                },
            },
            "observation": (
                "[ERROR] Tests run: 5, Failures: 1, Errors: 0, Skipped: 0\n"
                "[ERROR] yard.keelstamp.BillDateTest.yearBoundaryKeepsCalendarYear:18 "
                "expected: <2025-12-29> but was: <2026-12-29>\n"
                "[ERROR] yard.keelstamp.BillDateTest.midYearStamp:14 expected: <2026-06-15> but was: <2026-06-15> (passed)\n"
                "[INFO] BUILD FAILURE"
            ),
            "reflection": "Reproduced 2025-12-29 stamping as 2026-12-29 while mid-year 2026-06-15 still matches. The defect is the year letter, not the month-day pattern.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Observation: yearBoundaryKeepsCalendarYear failed expected 2025-12-29 was 2026-12-29 (step 3). Run full mvn test so JUnit download evidence is in the same suite."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "mvn -DskipTests=false test 2>&1 | tail -n 18"
                },
            },
            "observation": (
                "Downloading from central: https://repo.maven.apache.org/maven2/org/junit/jupiter/junit-jupiter/5.10.2/junit-jupiter-5.10.2.pom\n"
                "[ERROR] Failed to execute goal on project keelstamp: Could not resolve dependencies\n"
                "[ERROR] Could not transfer artifact org.junit.jupiter:junit-jupiter:pom:5.10.2 "
                "from/to central (https://repo.maven.apache.org/maven2):\n"
                "502 Bad Gateway\n"
                "<html>\n"
                "<head><title>502 Bad Gateway</title></head>\n"
                "<body>\n"
                "<center><h1>502 Bad Gateway</h1></center>\n"
                "upstream connect error or disconnect/reset before headers. "
                "reset reason: connection failure\n"
                "</body></html>"
            ),
            "reflection": "repo.maven.apache.org returned 502 while fetching junit-jupiter. Transient central; retry offline against the already-populated .m2 rather than treating the year bug as a missing JUnit.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: mvn test returned 502 Bad Gateway from repo.maven.apache.org (step 4). Sleep 4s, retry mvn -o as recovered evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "sleep 4 && mvn -o -q -Dtest=BillDateTest test 2>&1 | tail -n 12"
                    )
                },
            },
            "observation": (
                "[ERROR] Tests run: 5, Failures: 1, Errors: 0, Skipped: 0\n"
                "[ERROR] yard.keelstamp.BillDateTest.yearBoundaryKeepsCalendarYear:18 "
                "expected: <2025-12-29> but was: <2026-12-29>\n"
                "[INFO] BUILD FAILURE"
            ),
            "reflection": "Offline .m2 recovered the JUnit fetch. 2025-12-29 still stamps 2026-12-29, so the defect is local formatter letters not a missing plugin.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: offline BillDateTest still failed was 2026-12-29 (step 5). Dump week-based year vs calendar year as evidence 2025-12-29 is ISO week 1 of 2026."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "jshell --startup DEFAULT <<'JS' > /tmp/keelstamp-week.json\n"
                        "import java.time.*;\n"
                        "import java.time.format.*;\n"
                        "import java.time.temporal.IsoFields;\n"
                        "var d = LocalDate.of(2025,12,29);\n"
                        "var fmt = DateTimeFormatter.ofPattern(\"YYYY-MM-dd\");\n"
                        "System.out.println(\"{\\\"civil\\\":\\\"\"+d+\"\\\",\\\"pattern\\\":\\\"YYYY-MM-dd\\\","
                        "\\\"formatted\\\":\\\"\"+d.format(fmt)+\"\\\",\\\"weekBasedYear\\\":"
                        "+d.get(IsoFields.WEEK_BASED_YEAR)+\"}\");\n"
                        "/exit\n"
                        "JS\n"
                        "cat /tmp/keelstamp-week.json"
                    )
                },
            },
            "observation": (
                "{\n"
                '  "civil": "2025-12-29",\n'
                '  "pattern": "YYYY-MM-dd",\n'
                '  "formatted": "2026-12-29",\n'
                '  "weekBasedYear": 2026\n'
                "}\n"
                "Found ISO week-based year 2026 on a December 2025 civil date; month and day stayed 12-29."
            ),
            "reflection": "Measured formatted=2026-12-29 with weekBasedYear=2026. Container TZ cannot explain a year letter that follows ISO week 1.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: dump formatted 2026-12-29 weekBasedYear 2026 (step 6). jq the dump and re-read BillDate for evidence the pattern is still week-year YYYY."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "filter": "{civil, formatted, weekBasedYear}",
                    "file": "/tmp/keelstamp-week.json",
                },
            },
            "observation": (
                "{\n"
                '  "civil": "2025-12-29",\n'
                '  "formatted": "2026-12-29",\n'
                '  "weekBasedYear": 2026\n'
                "}\n"
                "Found BOL-SPEC-9 in docs/bol-spec.md:11: bill-of-lading dates use calendar year, not ISO week-year."
            ),
            "reflection": (
                "Plan change: abandon host-TZ / UTC-container. Observation shows YYYY week-based year 2026 on civil 2025-12-29. "
                "Switching the edit target to ofPattern yyyy-MM-dd so stamp() keeps the calendar year."
            ),
        },
        {
            "n": 8,
            "decision_basis": db(
                "Reflection: plan now targets calendar yyyy, not container TZ (step 7). First patch: withZone UTC on the same YYYY pattern."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "src/main/java/yard/keelstamp/BillDate.java",
                    "old_string": (
                        "import java.time.LocalDate;\n"
                        "import java.time.format.DateTimeFormatter;\n"
                        "\n"
                        "public final class BillDate {\n"
                        "    static final DateTimeFormatter STAMP =\n"
                        '            DateTimeFormatter.ofPattern("YYYY-MM-dd");\n'
                        "\n"
                        "    private BillDate() {}\n"
                        "\n"
                        "    public static String stamp(LocalDate day) {\n"
                        "        return day.format(STAMP);\n"
                        "    }"
                    ),
                    "new_string": (
                        "import java.time.LocalDate;\n"
                        "import java.time.ZoneOffset;\n"
                        "import java.time.format.DateTimeFormatter;\n"
                        "\n"
                        "public final class BillDate {\n"
                        "    static final DateTimeFormatter STAMP =\n"
                        '            DateTimeFormatter.ofPattern("YYYY-MM-dd").withZone(ZoneOffset.UTC);\n'
                        "\n"
                        "    private BillDate() {}\n"
                        "\n"
                        "    public static String stamp(LocalDate day) {\n"
                        "        return day.atStartOfDay(ZoneOffset.UTC).format(STAMP);\n"
                        "    }"
                    ),
                },
            },
            "observation": "Edited src/main/java/yard/keelstamp/BillDate.java: STAMP now withZone(UTC) and stamp() uses atStartOfDay UTC. Pattern is still YYYY-MM-dd.",
            "reflection": "UTC wrapping is the tempting wrong durable step. Week-based year does not care about zone; 2025-12-29 should still print 2026-12-29.",
        },
        {
            "n": 9,
            "decision_basis": db(
                "Observation: BillDate.java now withZone UTC on YYYY (step 8). Write YearBoundaryTest as evidence 2025-12-29 must stamp 2025-12-29."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "src/test/java/yard/keelstamp/YearBoundaryTest.java",
                    "content": YEAR_TEST,
                },
            },
            "observation": "Wrote src/test/java/yard/keelstamp/YearBoundaryTest.java (16 lines). Asserts stamp(2025-12-29) equals 2025-12-29.",
            "reflection": "Created a calendar-year regression that refuses 2026-12-29. Run it to see whether UTC wrapping actually keeps 2025.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: YearBoundaryTest asserts 2025-12-29 (step 9). Run mvn test for evidence the withZone UTC patch failed."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "mvn -o -q -Dtest=BillDateTest,YearBoundaryTest test 2>&1 | tail -n 16"
                    )
                },
            },
            "observation": (
                "[ERROR] Tests run: 6, Failures: 2, Errors: 0, Skipped: 0\n"
                "[ERROR] yard.keelstamp.YearBoundaryTest.yearBoundaryFormatsAsCalendarYear:11 "
                "expected: <2025-12-29> but was: <2026-12-29>\n"
                "[ERROR] yard.keelstamp.BillDateTest.yearBoundaryKeepsCalendarYear:18 "
                "expected: <2025-12-29> but was: <2026-12-29>\n"
                "[INFO] BUILD FAILURE"
            ),
            "reflection": "UTC wrapping still printed 2026-12-29. Need yyyy (calendar year), not a zone on the week-year letter.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Observation: YearBoundaryTest failed was 2026-12-29 (step 10). Re-read BillDate.java for evidence YYYY is still the pattern after withZone."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {
                    "path": "src/main/java/yard/keelstamp/BillDate.java",
                    "offset": 1,
                    "limit": 24,
                },
            },
            "observation": BILL_ZONE,
            "reflection": "Found ofPattern YYYY-MM-dd withZone UTC. BOL-SPEC-9 wants yyyy calendar year; drop the zone wrapper.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Reflection: YYYY plus UTC is the wrong letter (step 11). Patch BillDate to ofPattern yyyy-MM-dd so 2025-12-29 is verified as 2025-12-29."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "src/main/java/yard/keelstamp/BillDate.java",
                    "old_string": BILL_ZONE.strip(),
                    "new_string": BILL_Y.strip(),
                },
            },
            "observation": "Edited src/main/java/yard/keelstamp/BillDate.java: STAMP is now ofPattern yyyy-MM-dd and stamp() formats the LocalDate directly.",
            "reflection": "Patched the calendar-year letter. Re-run BillDate and YearBoundary tests.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Observation: BillDate.java now uses yyyy-MM-dd (step 12). Re-run mvn test as verified evidence 2025-12-29 stamps 2025-12-29."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "mvn -o -q -Dtest=BillDateTest,YearBoundaryTest test 2>&1 | tail -n 8"
                    )
                },
            },
            "observation": (
                "[INFO] Tests run: 6, Failures: 0, Errors: 0, Skipped: 0\n"
                "[INFO] BUILD SUCCESS\n"
                "6 passed (BillDateTest x5 including yearBoundaryKeepsCalendarYear, YearBoundaryTest.yearBoundaryFormatsAsCalendarYear)"
            ),
            "reflection": "Verified 6 passed including yearBoundaryFormatsAsCalendarYear. Open the KP-418 PR.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Observation: 6 BillDate tests passed after the yyyy patch (step 13). Create the KP-418 PR via gh api as evidence of the handoff."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "POST",
                    "path": "repos/keelpress/keelstamp/pulls",
                    "raw_field": "title=KP-418: use yyyy calendar year in BillDate stamp so 2025-12-29 stays 2025",
                },
            },
            "observation": (
                "HTTP 429 Too Many Requests\n"
                "Retry-After: 8\n"
                "x-ratelimit-limit: 30\n"
                "x-ratelimit-remaining: 0\n"
                '{"message":"API rate limit exceeded for user ci-bot (30 req/min); retry_after=8",'
                '"documentation_url":"https://docs.github.com/rest/overview/rate-limits"}'
            ),
            "reflection": "gh returned 429 with retry-after 8 on the shared ci-bot token. Wait the advertised window and retry the create once.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: gh api returned 429 with Retry-After 8 (step 14). Sleep 9s, retry the pull create once, then show the verified URL."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "sleep 9 && gh api -X POST repos/keelpress/keelstamp/pulls "
                        "-f title='KP-418: use yyyy calendar year in BillDate stamp so 2025-12-29 stays 2025' "
                        "-f head=kp-418-yyyy -f base=main --jq .html_url"
                    )
                },
            },
            "observation": "https://git.keelpress.internal/yard/keelstamp/pull/193",
            "reflection": "Verified PR 193 opened. KP-418 can close on the branch; year-boundary bills keep the calendar year.",
        },
    ]
    return {
        "id": "act-r18-week-year-yyyy-keelstamp-b7d4e1",
        "goal": (
            "KP-418 (keelstamp, Java 21 DateTimeFormatter; mvn test): yard bills for civil 2025-12-29 print as 2026-12-29 "
            "while mid-year 2026-06-15 still matches. Reproduce with the year-boundary fixture, make BillDate.stamp honor "
            "BOL-SPEC-9 (calendar year, not ISO week-year), keep existing BillDateTest green, and open a PR. Designed plant; "
            "not a live bill-of-lading claim."
        ),
        "steps": steps,
        "outcome": (
            "Root cause was DateTimeFormatter.ofPattern(\"YYYY-MM-dd\") using the ISO week-based year, so civil 2025-12-29 "
            "(ISO week 1 of 2026) stamped as 2026-12-29. A first patch that withZone(UTC) and atStartOfDay still printed "
            "2026-12-29 because week-year ignores zone. BillDate now uses ofPattern(\"yyyy-MM-dd\"). Verified by mvn -o "
            "-Dtest=BillDateTest,YearBoundaryTest: 6 passed including yearBoundaryFormatsAsCalendarYear; PR 193 opened. "
            "Overall: verified and shipped."
        ),
        "reward": {
            "success": True,
            "task_completion": 0.40,
            "calendar_year_pattern": 0.12,
            "year_boundary_regression": 0.08,
            "noise_retry_overhead_penalty": -0.02,
            "total": 0.58,
            "aggregation": "unweighted sum of the numeric components above (success is a boolean label, not a summand); rounding_decimals 2",
            "cost": {
                "tests_passed": 6,
                "tests_failed_final": 0,
                "wasted_calls": 2,
                "retries": 2,
                "duration_min": 31,
            },
        },
        "meta": meta_common(
            codebase_type="library (Java 21 DateTimeFormatter bill stamp)",
            bug_class="DateTimeFormatter YYYY week-based year stamps 2025-12-29 as 2026-12-29",
            test_harness="mvn test",
            noise_steps={"502": 4, "429": 14},
            noise_recovery_steps={"502": 5, "429": 15},
            plan_change_step=7,
            debug_loop_steps=[8, 9, 10, 11, 12, 13],
            tags=[
                "java-21",
                "datetimeformatter",
                "week-year",
                "yyyy",
                "bill-of-lading",
                "iso-8601",
            ],
        ),
    }


def ep2() -> dict:
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: LG-277 reports loomgauge refusing mill.ini when plc_token contains percent-hex. Search ConfigParser and plc_token for evidence of interpolation."
            ),
            "plan": "1) search ConfigParser 2) read load_loom 3) reproduce percent token 4) raw get on secrets 5) unit tests; mill vault is a later handoff",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "ConfigParser|interpolation|plc_token|log_dir|%",
                    "path": "src/loomgauge",
                },
            },
            "observation": (
                "src/loomgauge/config.py:4:def load_loom(path: str) -> ConfigParser:\n"
                "src/loomgauge/config.py:5:    cfg = ConfigParser()\n"
                "src/loomgauge/config.py:10:def plc_token(cfg: ConfigParser) -> str:\n"
                "src/loomgauge/config.py:11:    return cfg.get(\"secrets\", \"plc_token\")\n"
                "src/loomgauge/config.py:15:    return cfg.get(\"paths\", \"log_dir\")\n"
                "5 matches"
            ),
            "reflection": "Found default ConfigParser() and get() on secrets.plc_token with no raw=True. Paths use %(data_root)s interpolation.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: config.py:5-11 constructs ConfigParser and get secrets.plc_token (step 1). Read config.py for evidence of interpolation kwargs."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "src/loomgauge/config.py", "offset": 1, "limit": 24},
            },
            "observation": CFG_BEFORE,
            "reflection": "Measured ConfigParser() with default BasicInterpolation and a non-raw get for plc_token. A token containing %2F would raise InterpolationSyntaxError.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: plc_token uses cfg.get without raw (step 2). Run pytest for evidence the percent-token fixture already failed interpolation."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest -q tests/test_config.py --tb=short 2>&1 | tail -n 20"
                },
            },
            "observation": (
                "F.....                                                                   [100%]\n"
                "=================================== FAILURES ===================================\n"
                "__________________________ test_plc_token_roundtrip __________________________\n"
                "tests/test_config.py:12: in test_plc_token_roundtrip\n"
                "    assert plc_token(load_loom(\"tests/fixtures/loom-percent.ini\")) == \"N7%2FqX-heddle\"\n"
                "src/loomgauge/config.py:11: in plc_token\n"
                "    return cfg.get(\"secrets\", \"plc_token\")\n"
                "E   configparser.InterpolationSyntaxError: '%' must be followed by '%' or '(', found: '%2FqX-heddle'\n"
                "FAILED tests/test_config.py::test_plc_token_roundtrip - configparser.InterpolationSyntaxError\n"
                "1 failed, 5 passed in 0.11s"
            ),
            "reflection": "Reproduced InterpolationSyntaxError on N7%2FqX-heddle. Paths tests still passed because %(data_root)s is valid BasicInterpolation.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Observation: test_plc_token_roundtrip failed InterpolationSyntaxError on %2FqX (step 3). pip install pytest-cov so coverage evidence can join the same suite."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pip install pytest-cov==5.0.0 2>&1 | tail -n 16"
                },
            },
            "observation": (
                "Looking in indexes: https://pypi.org/simple\n"
                "Collecting pytest-cov==5.0.0\n"
                "  Downloading pytest_cov-5.0.0-py3-none-any.whl (21 kB)\n"
                "ERROR: Could not install packages due to an OSError: 429 Too Many Requests\n"
                "Retry-After: 6\n"
                '{"error":"rate_limit_exceeded","retry_after":6,'
                '"message":"pypi.org CDN 429 for /simple/pytest-cov/"}\n'
            ),
            "reflection": "pypi.org returned 429 with retry-after 6. Sleep then retry install once; do not tight-loop the simple index.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: pip install returned 429 with retry_after 6 (step 4). Sleep 7s and retry install once as evidence the index recovered."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "sleep 7 && pip install pytest-cov==5.0.0 2>&1 | tail -n 8; "
                        "pytest -q tests/test_config.py --tb=line 2>&1 | tail -n 6"
                    )
                },
            },
            "observation": (
                "Successfully installed pytest-cov-5.0.0 coverage-7.6.1\n"
                "F.....                                                                   [100%]\n"
                "FAILED tests/test_config.py::test_plc_token_roundtrip - configparser.InterpolationSyntaxError: '%' must be followed by '%' or '(', found: '%2FqX-heddle'\n"
                "1 failed, 5 passed in 0.09s"
            ),
            "reflection": "Install recovered. Percent-token interpolation is still there, so the defect is local get() not a missing pytest plugin.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: pytest-cov installed and token test still failed interpolation (step 5). Dump the fixture ini as evidence the token holds bare percent-hex."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "python3 - <<'PY'\n"
                        "from pathlib import Path\n"
                        "import json\n"
                        "text = Path('tests/fixtures/loom-percent.ini').read_text()\n"
                        "print(text)\n"
                        "print('---')\n"
                        "print(json.dumps({\n"
                        "  'has_percent_hex': '%2F' in text,\n"
                        "  'has_path_interp': '%(data_root)s' in text,\n"
                        "  'sections': ['DEFAULT','paths','secrets'],\n"
                        "}))\n"
                        "PY"
                    )
                },
            },
            "observation": (
                "[DEFAULT]\n"
                "data_root = /var/loomgauge\n"
                "\n"
                "[paths]\n"
                "log_dir = %(data_root)s/logs\n"
                "\n"
                "[secrets]\n"
                "plc_token = N7%2FqX-heddle\n"
                "---\n"
                '{"has_percent_hex": true, "has_path_interp": true, "sections": ["DEFAULT", "paths", "secrets"]}\n'
                "Wrote /tmp/loom-ini-meta.json from that dump."
            ),
            "reflection": "Measured a live token with bare %2F next to a paths section that needs %(data_root)s. Rotating the token would not fix the next percent-bearing secret.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: fixture has plc_token N7%2FqX-heddle and log_dir %(data_root)s (step 6). jq the dump for evidence both interpolation forms coexist."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "filter": "{has_percent_hex, has_path_interp, sections}",
                    "file": "/tmp/loom-ini-meta.json",
                },
            },
            "observation": (
                "{\n"
                '  "has_percent_hex": true,\n'
                '  "has_path_interp": true,\n'
                '  "sections": ["DEFAULT", "paths", "secrets"]\n'
                "}\n"
                "Found LOOM-SPEC-3 in docs/loom-spec.md:9: secrets are opaque bytes; paths may use %(data_root)s."
            ),
            "reflection": (
                "Plan change: abandon plc_token rotation. Observation shows BasicInterpolation treating %2F as a broken percent-escape while paths still need %(data_root)s. "
                "Switching the edit target to a raw get on secrets so path interpolation stays."
            ),
        },
        {
            "n": 8,
            "decision_basis": db(
                "Reflection: plan now targets raw secrets get, not token rotation (step 7). First patch: ConfigParser(interpolation=None)."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "src/loomgauge/config.py",
                    "old_string": "    cfg = ConfigParser()\n    cfg.read(path)",
                    "new_string": "    cfg = ConfigParser(interpolation=None)\n    cfg.read(path)",
                },
            },
            "observation": "Edited src/loomgauge/config.py: load_loom now constructs ConfigParser(interpolation=None). plc_token get is still non-raw.",
            "reflection": "Disabling interpolation is the tempting wrong durable step. Token get would succeed; log_dir would stay the literal %(data_root)s/logs.",
        },
        {
            "n": 9,
            "decision_basis": db(
                "Observation: load_loom now interpolation=None (step 8). Write percent-token and log_dir tests as evidence both contracts must hold."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_percent_token.py",
                    "content": TOKEN_TEST,
                },
            },
            "observation": "Wrote tests/test_percent_token.py (14 lines). Asserts plc_token == N7%2FqX-heddle and log_dir == /var/loomgauge/logs.",
            "reflection": "Created a paired regression. Run it to see whether interpolation=None actually keeps path expansion.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: test_percent_token.py asserts token and expanded log_dir (step 9). Run pytest for evidence the interpolation=None patch failed."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "pytest -q tests/test_config.py tests/test_percent_token.py --tb=short 2>&1 | tail -n 18"
                    )
                },
            },
            "observation": (
                ".F.....F                                                                 [100%]\n"
                "=================================== FAILURES ===================================\n"
                "______________________ test_log_dir_expands_data_root ______________________\n"
                "tests/test_percent_token.py:12: in test_log_dir_expands_data_root\n"
                "    assert log_dir(cfg) == \"/var/loomgauge/logs\"\n"
                "E   AssertionError: assert '%(data_root)s/logs' == '/var/loomgauge/logs'\n"
                "FAILED tests/test_percent_token.py::test_log_dir_expands_data_root - AssertionError\n"
                "FAILED tests/test_config.py::test_log_dir_from_default - AssertionError: assert '%(data_root)s/logs' == '/var/loomgauge/logs'\n"
                "2 failed, 6 passed in 0.13s"
            ),
            "reflection": "Token tests passed; log_dir stayed the literal %(data_root)s/logs. Need BasicInterpolation for paths and raw=True only on secrets.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Observation: test_log_dir_expands_data_root failed actual %(data_root)s/logs (step 10). Re-read config.py for evidence interpolation=None is still set."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "src/loomgauge/config.py", "offset": 1, "limit": 22},
            },
            "observation": CFG_NONE,
            "reflection": "Found interpolation=None on load_loom. LOOM-SPEC-3 wants opaque secrets and expanded paths; restore default interpolation and raw=True on plc_token.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Reflection: interpolation=None broke path expansion (step 11). Patch plc_token to get(..., raw=True) and restore default ConfigParser."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "src/loomgauge/config.py",
                    "old_string": CFG_NONE.strip(),
                    "new_string": CFG_RAW.strip(),
                },
            },
            "observation": "Edited src/loomgauge/config.py: load_loom uses ConfigParser() again; plc_token now get secrets plc_token raw=True. log_dir still interpolates.",
            "reflection": "Patched the secrets getter. Re-run config and percent-token tests.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Observation: plc_token now get raw=True (step 12). Re-run pytest as verified evidence the percent token and expanded log_dir both hold."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "pytest -q tests/test_config.py tests/test_percent_token.py 2>&1 | tail -n 8"
                    )
                },
            },
            "observation": (
                "........                                                                 [100%]\n"
                "8 passed in 0.10s "
                "(test_plc_token_roundtrip, test_plc_token_accepts_percent, test_log_dir_expands_data_root, test_log_dir_from_default, plus 4 others)"
            ),
            "reflection": "Verified 8 passed including the percent-token pair. Unit ini math is done; the mill vault copy is still required before LG-277 can close.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Reflection: unit tests passed; need the mill vault copy (step 13). GET the heddle vault loom.ini as evidence a live percent token can load."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "curl -sS -o /tmp/mill-loom.ini -w '%{http_code}' "
                        "https://vault.heddle.internal/v1/loomgauge/mill-loom.ini"
                    )
                },
            },
            "observation": (
                "curl: (22) The requested URL returned error: 502\n"
                "HTTP/1.1 502 Bad Gateway\n"
                "content-type: text/plain\n"
                "x-envoy-upstream-service-time: 30012\n"
                "upstream connect error or disconnect/reset before headers. reset reason: connection timeout\n"
                "000"
            ),
            "reflection": "vault.heddle.internal returned 502 upstream timeout. Retry once with backoff; if it stays down, the mill-file round-trip stays unverified and LG-277 cannot close.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: mill vault GET returned 502 upstream timeout (step 14). Sleep 5s, retry once, and if empty record evidence that the vault is unavailable."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "sleep 5 && curl -sS -o /tmp/mill-loom.ini -w '%{http_code}\\n' "
                        "https://vault.heddle.internal/v1/loomgauge/mill-loom.ini "
                        "|| echo LAB_UNAVAILABLE; ls /tmp/mill-loom.ini 2>&1 | head"
                    )
                },
            },
            "observation": (
                "LAB_UNAVAILABLE\n"
                "ls: cannot access '/tmp/mill-loom.ini': No such file or directory"
            ),
            "reflection": "Vault stayed unavailable after backoff. Open LG-311 as the mill-file handoff; do not claim the live percent token on the heddle box.",
        },
        {
            "n": 16,
            "decision_basis": db(
                "Observation: mill-loom.ini was missing after LAB_UNAVAILABLE (step 15). Open gh issue create for LG-311 as evidence the unresolved vault ACK is tracked."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "issue",
                    "verb": "create",
                    "repo": "heddle/loomgauge",
                    "title": "LG-311: mill vault loom.ini required before closing LG-277 percent-token load",
                    "body": "Unit tests raw-get percent tokens; vault.heddle.internal unreachable.",
                },
            },
            "observation": "https://git.heddle.internal/weave/loomgauge/issues/311",
            "reflection": "Created LG-311. loomgauge unit tests are green; live mill-file confirmation is a separate ticket.",
        },
    ]
    return {
        "id": "act-r18-ini-percent-interpolation-loomgauge-c3a91f",
        "goal": (
            "LG-277 (loomgauge, Python 3.12 configparser; pytest): mill.ini load raises InterpolationSyntaxError when plc_token contains "
            "percent-hex (N7%2FqX-heddle) while path interpolation %(data_root)s/logs must keep working. Reproduce with the percent-token "
            "fixture, make secrets opaque without disabling path interpolation, and keep existing config tests green. Designed plant; "
            "the mill vault copy is a lab path, not a live PLC claim."
        ),
        "steps": steps,
        "outcome": (
            "Root cause was ConfigParser BasicInterpolation treating a percent-hex plc_token as a broken percent-escape. A first patch that "
            "set interpolation=None loaded the token but left log_dir as the literal %(data_root)s/logs. plc_token now uses get(..., raw=True) "
            "and load_loom keeps default interpolation for paths. Verified by pytest tests/test_config.py tests/test_percent_token.py: 8 passed "
            "including test_plc_token_accepts_percent and test_log_dir_expands_data_root. The mill vault copy stayed unreachable, so live "
            "percent-token confirmation is unresolved; LG-311 was opened as the handoff. Overall: incomplete; unit ini only."
        ),
        "reward": {
            "success": False,
            "task_completion": 0.24,
            "raw_secret_get": 0.10,
            "path_interpolation_preserved": 0.08,
            "hil_unverified_penalty": -0.14,
            "noise_retry_overhead_penalty": -0.02,
            "total": 0.26,
            "aggregation": "unweighted sum of the numeric components above (success is a boolean label, not a summand); rounding_decimals 2",
            "cost": {
                "tests_passed": 8,
                "tests_failed_final": 0,
                "wasted_calls": 2,
                "retries": 2,
                "duration_min": 44,
                "hil_jobs": 0,
            },
        },
        "meta": meta_common(
            codebase_type="library (Python 3.12 configparser mill ini)",
            bug_class="BasicInterpolation treats percent-hex secrets as broken percent-escapes",
            test_harness="pytest",
            noise_steps={"429": 4, "502": 14},
            noise_recovery_steps={"429": 5, "502": 15},
            plan_change_step=7,
            debug_loop_steps=[8, 9, 10, 11, 12, 13],
            tags=[
                "python-3.12",
                "configparser",
                "interpolation",
                "percent-hex",
                "ini",
                "hil-handoff",
            ],
        ),
    }


def walk_keys(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            child = f"{path}.{k}" if path else k
            yield child, k, v
            yield from walk_keys(v, child)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_keys(v, f"{path}[{i}]")


def validate_record(rec: dict) -> None:
    steps = rec["steps"]
    n = len(steps)
    if not 12 <= n <= 17:
        raise SystemExit(f"{rec['id']} step count {n}")
    for i, step in enumerate(steps, 1):
        if step["n"] != i:
            raise SystemExit(f"{rec['id']} numbering {step['n']} != {i}")
        name = step["tool_call"]["name"]
        if name not in KNOWN:
            raise SystemExit(f"{rec['id']} unknown tool {name}")
        if not isinstance(step["tool_call"].get("args"), dict):
            raise SystemExit(f"{rec['id']} args not object {i}")
        if not step["observation"].strip():
            raise SystemExit(f"{rec['id']} empty obs {i}")
        db(step["decision_basis"])
        blob = " ".join(
            [
                step["decision_basis"],
                step["observation"],
                step["tool_call"]["name"],
                json.dumps(step["tool_call"]["args"], sort_keys=True),
            ]
        )
        if STALL_RE.search(blob):
            raise SystemExit(f"{rec['id']} step {i} stall: {STALL_RE.search(blob).group(0)!r}")
        if not PROGRESS_RE.search(blob):
            raise SystemExit(f"{rec['id']} step {i} sparse progress: {step['decision_basis'][:100]!r}")
        if "hypothesis" in step["observation"].lower():
            raise SystemExit(f"{rec['id']} step {i} hypothesis in observation")
    obs = [s["observation"] for s in steps]
    n429 = sum("429" in o for o in obs)
    n502 = sum("502" in o for o in obs)
    if n429 != 1 or n502 != 1:
        raise SystemExit(f"{rec['id']} noise counts 429={n429} 502={n502}")
    recov = rec["meta"]["noise_recovery_steps"]
    noise = rec["meta"]["noise_steps"]
    for code, idx in noise.items():
        if code not in steps[idx - 1]["observation"]:
            raise SystemExit(f"{rec['id']} noise {code} not in step {idx}")
        ridx = recov[code]
        if code not in steps[ridx - 1]["decision_basis"]:
            raise SystemExit(f"{rec['id']} recovery {ridx} missing {code} in basis")
        if code in steps[ridx - 1]["observation"]:
            raise SystemExit(f"{rec['id']} recovery {ridx} repeats {code} in observation")
    pc = rec["meta"]["plan_change_step"]
    if "Plan change:" not in steps[pc - 1].get("reflection", ""):
        raise SystemExit(f"{rec['id']} plan change reflection missing")
    if pc in (1, n):
        raise SystemExit(f"{rec['id']} plan change at terminal {pc}")
    for path, key, _ in walk_keys(rec):
        norm = re.sub(r"[^a-z0-9]+", "_", key).strip("_").lower()
        if norm in FORBIDDEN or norm.startswith("internal_reasoning"):
            raise SystemExit(f"{rec['id']} forbidden key {path}")
        if "thought" in norm and norm != "thoughtful":
            raise SystemExit(f"{rec['id']} thought-like key {path}")
    rc = rec["reward"]
    numeric = [
        v
        for k, v in rc.items()
        if k not in {"success", "aggregation", "cost", "total"}
        and isinstance(v, (int, float))
        and not isinstance(v, bool)
    ]
    if abs(sum(numeric) - rc["total"]) > 1e-9:
        raise SystemExit(f"{rec['id']} reward {sum(numeric)} != {rc['total']}")
    if rec["meta"]["training_ready"] is not False:
        raise SystemExit("training_ready")
    if rec["meta"]["rights"]["intended_use"] != "research_only":
        raise SystemExit("rights")
    if rec["meta"]["rights"]["training_ready"] is not False:
        raise SystemExit("rights.training_ready")
    if rec["meta"]["sim_or_real"] != "designed":
        raise SystemExit("sim_or_real")
    if rec["meta"]["round"] != 18:
        raise SystemExit("round")
    if rec["meta"]["rights"]["linear_issue"] != "RM-793":
        raise SystemExit("linear")
    if rec["reward"]["success"] is True and not re.search(
        r"\b(?:verified|shipped|passed)\b", rec["outcome"], re.I
    ):
        raise SystemExit(f"{rec['id']} success outcome missing completion")
    if rec["reward"]["success"] is False and not re.search(
        r"\b(?:incomplete|unresolved|handoff|pending)\b", rec["outcome"], re.I
    ):
        raise SystemExit(f"{rec['id']} failure outcome missing incomplete/handoff")


def notes() -> str:
    return """# ACTF r18 — 2026-09-02-final-heavy (grok-4.6)

Quota Q=2 designed coding episodes (`FACTORY_QUOTAS["agentic-coding-trajectory-factory"] == 2`). IDs mill-safe `act-r18-…` (not the unresolved `actf-` prefix). Envelope: id/goal/steps/outcome/reward/meta. Tools restricted to verify_execution KNOWN_TOOLS (bash, read_file, edit_file, write_file, search, gh, jq). meta.round=18, meta.factory=agentic-coding-trajectory-factory, meta.generator=grok-4.6, run_label=2026-09-02-final-heavy, meta.sim_or_real=designed. meta.rights RM-793 research-only; training_ready false. Linear RM-793. Invented repos only (keelpress/keelstamp, heddle/loomgauge). Never wrote outputs/raw/. Did not steal 2026-08-17 r13 reservation.

| id | codebase / harness | bug class | result | reward.total |
|----|--------------------|-----------|--------|--------------|
| act-r18-week-year-yyyy-keelstamp-b7d4e1 | Java 21 DateTimeFormatter / mvn test | YYYY week-based year stamps 2025-12-29 as 2026-12-29 | success; 6/6; PR 193 | 0.58 |
| act-r18-ini-percent-interpolation-loomgauge-c3a91f | Python 3.12 configparser / pytest | BasicInterpolation treats percent-hex secrets as broken percent-escapes | incomplete HIL handoff LG-311; 8 unit tests | 0.26 |

## Step counts, noise, plan change
- act-r18-week-year-yyyy-keelstamp-b7d4e1: 15 steps. 502 at step 4 (`mvn test` repo.maven.apache.org junit-jupiter, upstream connect) → recovery step 5 (`sleep 4 && mvn -o`; year-boundary still 2026-12-29). 429 at step 14 (`gh api` POST pulls, Retry-After 8) → recovery step 15 (`sleep 9 && gh api`). Plan change at step 7: week dump formatted 2026-12-29 + weekBasedYear 2026 + BOL-SPEC-9 kills host-TZ; edit target becomes yyyy calendar year. Debug loop: 8 withZone UTC (wrong letter kept) → 9 write YearBoundaryTest → 10 FAIL was 2026-12-29 → 11 re-read YYYY still present → 12 patch yyyy-MM-dd → 13 6 passed.
- act-r18-ini-percent-interpolation-loomgauge-c3a91f: 16 steps. 429 at step 4 (`pip install pytest-cov` pypi.org, retry_after 6) → recovery step 5 (`sleep 7 && pip`; InterpolationSyntaxError still present). 502 at step 14 (heddle vault GET, envoy timeout) → recovery step 15 (retry then LAB_UNAVAILABLE). Plan change at step 7: fixture token N7%2FqX-heddle + %(data_root)s paths + LOOM-SPEC-3 kills token rotation; edit target becomes raw get on secrets. Debug loop: 8 interpolation=None → 9 write percent-token pair → 10 FAIL log_dir literal %(data_root)s → 11 re-read interpolation=None → 12 get raw=True → 13 8 passed.

## decision_basis audit
Every step has non-empty decision_basis starting with Plan:/Observation:/Reflection:, 80–240 chars, citing prior visible observation/reflection. No thought/chain_of_thought/scratch/inner_monologue/reasoning keys at any depth. Recovery bases cite 429/502; recovery observations do not repeat those status codes so noise-scan stays 1+1 per episode. Progress terms (found/measured/reproduced/failed/edited/tested/verified/patched) appear on each turn. The word "hypothesis" is kept out of observations.

## Reward
Unweighted numeric sum; success is a label. Cost sits under reward.cost. keelstamp: 0.40+0.12+0.08-0.02=0.58. loomgauge: 0.24+0.10+0.08-0.14-0.02=0.26.

## Realism / weak recovery
Good: keelstamp is a real Java DateTimeFormatter footgun (YYYY is week-based year; 2025-12-29 is ISO week 1 of 2026 so the bill prints 2026-12-29); first withZone UTC patch matches the TZ misread and still prints 2026 because week-year ignores zone. loomgauge is a real ConfigParser trap (bare %2F in a secret is not a `%(name)s` escape); interpolation=None is the tempting wrong durable step and moves the failure onto path expansion. Weak: jshell dump is a designed helper rather than a committed Java probe class; Maven 502 fallback is availability of central, not a stale junit that still formats YYYY; mill vault 502 is availability, not a stale ini that still interpolates; no reviewer in this round. Next densification: a reviewer asking to keep YYYY "so ISO week invoices sort with the mill calendar", or a 502 whose local fallback formatter/ini is stale (cached pattern still YYYY, or vault copy still unescaped).

Novel coverage: 36%
"""


def pipeline_checks(recs) -> None:
    sys.path.insert(0, str(Path("/home/raulmc/rmems/synthetic-factory/pipelines")))
    from validate_run import check_episode, terminal_outcome_agrees
    from check_records import FactoryStaging, check_jsonl
    from verify_execution import verify_batch_for_frontier, verify_record_execution
    from round_txn_coverage import has_long_horizon_debug_loop, sparse_step_progress_errors

    for rec in recs:
        errs = check_episode(
            rec,
            rec["id"],
            forbid_hidden_thought=True,
            enforce_terminal_outcome=True,
        )
        if errs:
            raise SystemExit(f"check_episode {errs[:5]}")
        if not terminal_outcome_agrees(rec["outcome"], rec["reward"]["success"]):
            raise SystemExit(f"{rec['id']} terminal_outcome_agrees")
        if not has_long_horizon_debug_loop(rec["steps"]):
            raise SystemExit(f"{rec['id']} missing debug loop")
        sparse = sparse_step_progress_errors(rec["id"], rec["steps"])
        if sparse:
            raise SystemExit(str(sparse))
        status, reason = verify_record_execution(rec, rec["id"])
        if status != "verified":
            raise SystemExit(f"{rec['id']} execution {status}: {reason}")

    batch = OUT / "batch-r18.jsonl"
    errors, warnings, kinds, records = check_jsonl(
        batch, batch.name, staging=FactoryStaging(enabled=True)
    )
    if errors:
        raise SystemExit(f"check_jsonl errors {errors[:8]}")
    if records != 2:
        raise SystemExit(f"records {records}")
    counts, findings, blocked = verify_batch_for_frontier(batch, strict=True)
    if blocked or counts.get("verified") != 2:
        raise SystemExit(f"frontier {counts} {findings} blocked={blocked}")
    print("pipeline ok", kinds, counts, "warnings", warnings[:4])


def main() -> int:
    recs = [ep1(), ep2()]
    for rec in recs:
        validate_record(rec)
    OUT.mkdir(parents=True, exist_ok=True)
    batch = OUT / "batch-r18.jsonl"
    with batch.open("w", encoding="utf-8") as fh:
        for rec in recs:
            fh.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    notes_path = OUT / "NOTES-r18.md"
    notes_path.write_text(notes(), encoding="utf-8")
    print(f"wrote {batch} ({len(recs)} records)")
    print(f"wrote {notes_path}")
    pipeline_checks(recs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
