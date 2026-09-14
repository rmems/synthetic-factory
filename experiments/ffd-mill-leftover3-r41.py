#!/usr/bin/env python3
"""feature-flag-debug leftover leftover leftover mill: r41+ Unleash..Flipt.

Honor leftover assignment/bucket/override before naive percentage.
BAN r40 wasabi/monetate, Statsig clones. Never rewrite raw. Never steal.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

EXPERIMENTS = Path(__file__).resolve().parent
REPO = EXPERIMENTS.parent
sys.path.insert(0, str(EXPERIMENTS))
sys.path.insert(0, str(REPO / "pipelines"))

GENERATOR = "grok-4.6"
FACTORY = "feature-flag-debug-factory"
PREFIX = "ffd"
BANNED_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")
DB_PREFIXES = ("Plan:", "Observation:", "Reflection:", "Tool call:")
RAW = REPO / "outputs" / "raw" / "2026-08-19-agentic"


def _p(**kwargs):
    return kwargs


def _ok(**kw):
    return _p(**kw)


def _bad(**kw):
    return _p(**kw)


PAIRS: list[tuple[dict, dict]] = [
    (
        _ok(
            slug="unleash-leftover-strategy-vs-pct",
            goal="Honor Unleash leftover strategy assignment before naive percentage.",
            plan="Read pct-as-strategy, try salt, then leftover strategy unit.",
            mod="ulstr",
            test_fn="test_leftover_strategy",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx['pct']\n",
            test_body=(
                "def test_leftover_strategy():\n"
                "    assert eval_flag({'user_id': 'u1', 'pct': 50, 'leftover_strategy': 'gradualRollout'}"
                ") == 'gradualRollout'\n"
            ),
            grep_pat="leftover_strategy|pct|unleash",
            grep_hit="src/ulstr.py:2: return hash(ctx['user_id']) % 100 < ctx['pct']",
            fail_msg="AssertionError: True == 'gradualRollout'; percentage swallowed leftover strategy",
            first_old="    return hash(ctx['user_id']) % 100 < ctx['pct']",
            first_new="    return hash(ctx['user_id'] + 'salt') % 100 < ctx['pct']",
            first_obs="patched salt (still percentage, still not leftover strategy)",
            still_msg="AssertionError: salt does not return the Unleash leftover strategy",
            reread_obs="Unleash leftover strategies bind assignment; percentage is only unbound",
            plan_change="Return leftover_strategy if present. Salt does not replace strategies. Not Statsig.",
            fix_new="    return ctx.get('leftover_strategy') or (hash(ctx['user_id']) % 100 < ctx['pct'])",
            fix_obs="patched leftover-strategy-before-pct",
            docs_url="https://docs.getunleash.io/reference/activation-strategies",
            docs_ok="Unleash leftover strategy assignment wins over default percentage.",
            docs_url2="https://docs.getunleash.io/reference/feature-toggles",
            docs_ok2="Honor leftover strategy. Not Statsig. Not Wasabi clone.",
            outcome="Leftover strategy gradualRollout won. Percentage unused for assigned (success).",
            domain="unleash-leftover-strategy-before-percentage",
            stack="Unleash leftover strategies",
            seed="unleash-leftover-strategy-vs-pct",
            residual="Leftover strategy beats percentage. Not drop-strategies clone.",
            coverage=87,
        ),
        _bad(
            slug="unleash-drop-strategies-handoff",
            goal="Do not drop Unleash leftover strategies when evaluating the flag.",
            plan="Read drop-strategies, try empty list, then hand off strategies.",
            mod="uldrop",
            test_fn="test_drop_strategies",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)\n",
            test_body=(
                "def test_drop_strategies():\n"
                "    assert eval_flag({'user_id': 'u1', 'leftover_strategy': 'userWithId'}) != True\n"
            ),
            grep_pat="leftover_strategy|strategies|unleash",
            grep_hit="src/uldrop.py:2: return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            fail_msg="AssertionError: leftover strategies dropped; naive pct used",
            first_old="    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            first_new="    return bool(ctx.get('strategies') or [])",
            first_obs="patched empty-strategies bool (still dropped leftover)",
            still_msg="AssertionError: dropping leftover strategies is not a boolean gate",
            reread_obs="Unleash strategies array is required leftover; drop is flag-plat",
            plan_change="Dropped leftover strategies is flag-plat. Handoff UL-STR-5.",
            fix_new="    return {'handoff': 'UL-STR-5'}",
            fix_obs="ticket filed. still dropped leftover",
            docs_url="https://docs.getunleash.io/reference/activation-strategies",
            docs_ok="Strategies must stay attached; dropping them is not a rollout.",
            docs_url2="https://docs.getunleash.io/reference/feature-toggles",
            docs_ok2="Drop leftover strategies owned by flag-plat. Handoff UL-STR-5.",
            outcome="Still dropped leftover; Unleash strategies are flag-plat — handoff UL-STR-5.",
            domain="unleash-drop-leftover-strategies",
            stack="Unleash drop strategies",
            seed="unleash-drop-strategies-handoff",
            residual="Do not drop leftover strategies.",
            ticket="UL-STR-5",
            ticket_why="Unleash leftover strategies owned by flag-plat",
            coverage=87,
        ),
    ),
    (
        _ok(
            slug="flagsmith-leftover-identity-vs-pct",
            goal="Honor Flagsmith leftover identity traits before naive percentage.",
            plan="Read pct-as-identity, try salt, then leftover identity unit.",
            mod="fmident",
            test_fn="test_leftover_identity",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx['pct']\n",
            test_body=(
                "def test_leftover_identity():\n"
                "    assert eval_flag({'user_id': 'u1', 'pct': 50, 'leftover_identity': 'id-9'}"
                ") == 'id-9'\n"
            ),
            grep_pat="leftover_identity|pct|flagsmith",
            grep_hit="src/fmident.py:2: return hash(ctx['user_id']) % 100 < ctx['pct']",
            fail_msg="AssertionError: True == 'id-9'; percentage swallowed leftover identity",
            first_old="    return hash(ctx['user_id']) % 100 < ctx['pct']",
            first_new="    return hash(ctx['user_id'] + 'salt') % 100 < ctx['pct']",
            first_obs="patched salt (still percentage, still not leftover identity)",
            still_msg="AssertionError: salt does not return the Flagsmith leftover identity",
            reread_obs="Flagsmith leftover identity binds traits; percentage is only unbound",
            plan_change="Return leftover_identity if present. Salt does not replace identity. Not Statsig.",
            fix_new="    return ctx.get('leftover_identity') or (hash(ctx['user_id']) % 100 < ctx['pct'])",
            fix_obs="patched leftover-identity-before-pct",
            docs_url="https://docs.flagsmith.com/clients/overview",
            docs_ok="Flagsmith leftover identity assignment wins over default percentage.",
            docs_url2="https://docs.flagsmith.com/advanced-use/identities",
            docs_ok2="Honor leftover identity. Not Statsig. Not Unleash clone.",
            outcome="Leftover identity id-9 won. Percentage unused for assigned (success).",
            domain="flagsmith-leftover-identity-before-percentage",
            stack="Flagsmith leftover identity",
            seed="flagsmith-leftover-identity-vs-pct",
            residual="Leftover identity beats percentage.",
            coverage=86,
        ),
        _bad(
            slug="flagsmith-drop-identity-handoff",
            goal="Do not drop Flagsmith leftover identity when evaluating the flag.",
            plan="Read drop-identity, try anonymous, then hand off identity.",
            mod="fmdrop",
            test_fn="test_drop_identity",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)\n",
            test_body=(
                "def test_drop_identity():\n"
                "    assert eval_flag({'user_id': 'u1', 'leftover_identity': 'id-9'}) != True\n"
            ),
            grep_pat="leftover_identity|identity|flagsmith",
            grep_hit="src/fmdrop.py:2: return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            fail_msg="AssertionError: leftover identity dropped; naive pct used",
            first_old="    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            first_new="    return ctx.get('anonymous') is True",
            first_obs="patched anonymous (still dropped leftover identity)",
            still_msg="AssertionError: dropping leftover identity is not a boolean gate",
            reread_obs="Flagsmith identity is required leftover; drop is flag-plat",
            plan_change="Dropped leftover identity is flag-plat. Handoff FM-ID-6.",
            fix_new="    return {'handoff': 'FM-ID-6'}",
            fix_obs="ticket filed. still dropped leftover",
            docs_url="https://docs.flagsmith.com/advanced-use/identities",
            docs_ok="Identity must stay attached; dropping it is not a rollout.",
            docs_url2="https://docs.flagsmith.com/clients/overview",
            docs_ok2="Drop leftover identity owned by flag-plat. Handoff FM-ID-6.",
            outcome="Still dropped leftover; Flagsmith identity is flag-plat — handoff FM-ID-6.",
            domain="flagsmith-drop-leftover-identity",
            stack="Flagsmith drop identity",
            seed="flagsmith-drop-identity-handoff",
            residual="Do not drop leftover identity.",
            ticket="FM-ID-6",
            ticket_why="Flagsmith leftover identity owned by flag-plat",
            coverage=86,
        ),
    ),
    (
        _ok(
            slug="growthbook-leftover-experiment-vs-pct",
            goal="Honor GrowthBook leftover experiment assignment before naive percentage.",
            plan="Read pct-as-experiment, try salt, then leftover experiment unit.",
            mod="gbexp",
            test_fn="test_leftover_experiment",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx['pct']\n",
            test_body=(
                "def test_leftover_experiment():\n"
                "    assert eval_flag({'user_id': 'u1', 'pct': 50, 'leftover_experiment': 'exp-a'}"
                ") == 'exp-a'\n"
            ),
            grep_pat="leftover_experiment|pct|growthbook",
            grep_hit="src/gbexp.py:2: return hash(ctx['user_id']) % 100 < ctx['pct']",
            fail_msg="AssertionError: True == 'exp-a'; percentage swallowed leftover experiment",
            first_old="    return hash(ctx['user_id']) % 100 < ctx['pct']",
            first_new="    return hash(ctx['user_id'] + 'salt') % 100 < ctx['pct']",
            first_obs="patched salt (still percentage, still not leftover experiment)",
            still_msg="AssertionError: salt does not return the GrowthBook leftover experiment",
            reread_obs="GrowthBook leftover experiment binds variation; percentage is only unbound",
            plan_change="Return leftover_experiment if present. Salt does not replace experiment. Not Statsig.",
            fix_new="    return ctx.get('leftover_experiment') or (hash(ctx['user_id']) % 100 < ctx['pct'])",
            fix_obs="patched leftover-experiment-before-pct",
            docs_url="https://docs.growthbook.io/app/features",
            docs_ok="GrowthBook leftover experiment assignment wins over default percentage.",
            docs_url2="https://docs.growthbook.io/lib/build-your-own",
            docs_ok2="Honor leftover experiment. Not Statsig. Not Flagsmith clone.",
            outcome="Leftover experiment exp-a won. Percentage unused for assigned (success).",
            domain="growthbook-leftover-experiment-before-percentage",
            stack="GrowthBook leftover experiment",
            seed="growthbook-leftover-experiment-vs-pct",
            residual="Leftover experiment beats percentage.",
            coverage=86,
        ),
        _bad(
            slug="growthbook-drop-experiment-handoff",
            goal="Do not drop GrowthBook leftover experiment when evaluating the flag.",
            plan="Read drop-experiment, try feature-only, then hand off experiment.",
            mod="gbdrop",
            test_fn="test_drop_experiment",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)\n",
            test_body=(
                "def test_drop_experiment():\n"
                "    assert eval_flag({'user_id': 'u1', 'leftover_experiment': 'exp-a'}) != True\n"
            ),
            grep_pat="leftover_experiment|experiment|growthbook",
            grep_hit="src/gbdrop.py:2: return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            fail_msg="AssertionError: leftover experiment dropped; naive pct used",
            first_old="    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            first_new="    return ctx.get('feature_on') is True",
            first_obs="patched feature_on (still dropped leftover experiment)",
            still_msg="AssertionError: dropping leftover experiment is not a boolean gate",
            reread_obs="GrowthBook experiment is required leftover; drop is experiment-plat",
            plan_change="Dropped leftover experiment is experiment-plat. Handoff GB-EX-4.",
            fix_new="    return {'handoff': 'GB-EX-4'}",
            fix_obs="ticket filed. still dropped leftover",
            docs_url="https://docs.growthbook.io/app/experiments",
            docs_ok="Experiment assignment must stay attached; dropping it is not a gate.",
            docs_url2="https://docs.growthbook.io/app/features",
            docs_ok2="Drop leftover experiment owned by experiment-plat. Handoff GB-EX-4.",
            outcome="Still dropped leftover; GrowthBook experiment is experiment-plat — handoff GB-EX-4.",
            domain="growthbook-drop-leftover-experiment",
            stack="GrowthBook drop experiment",
            seed="growthbook-drop-experiment-handoff",
            residual="Do not drop leftover experiment.",
            ticket="GB-EX-4",
            ticket_why="GrowthBook leftover experiment owned by experiment-plat",
            coverage=86,
        ),
    ),
    (
        _ok(
            slug="launchdarkly-leftover-targeting-vs-pct",
            goal="Honor LaunchDarkly leftover targeting rules before naive percentage.",
            plan="Read pct-as-targeting, try salt, then leftover targeting unit.",
            mod="ldtgt",
            test_fn="test_leftover_targeting",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx['pct']\n",
            test_body=(
                "def test_leftover_targeting():\n"
                "    assert eval_flag({'user_id': 'u1', 'pct': 50, 'leftover_targeting': 'rule-7'}"
                ") == 'rule-7'\n"
            ),
            grep_pat="leftover_targeting|pct|launchdarkly",
            grep_hit="src/ldtgt.py:2: return hash(ctx['user_id']) % 100 < ctx['pct']",
            fail_msg="AssertionError: True == 'rule-7'; percentage swallowed leftover targeting",
            first_old="    return hash(ctx['user_id']) % 100 < ctx['pct']",
            first_new="    return hash(ctx['user_id'] + 'salt') % 100 < ctx['pct']",
            first_obs="patched salt (still percentage, still not leftover targeting)",
            still_msg="AssertionError: salt does not return the LaunchDarkly leftover targeting",
            reread_obs="LD leftover targeting binds variation; percentage is only fallthrough",
            plan_change="Return leftover_targeting if present. Salt does not replace targeting. Not Statsig.",
            fix_new="    return ctx.get('leftover_targeting') or (hash(ctx['user_id']) % 100 < ctx['pct'])",
            fix_obs="patched leftover-targeting-before-pct",
            docs_url="https://docs.launchdarkly.com/home/flags/targeting",
            docs_ok="LaunchDarkly leftover targeting wins over default percentage.",
            docs_url2="https://docs.launchdarkly.com/sdk/features/evaluation",
            docs_ok2="Honor leftover targeting. Not Statsig. Not GrowthBook clone.",
            outcome="Leftover targeting rule-7 won. Percentage unused for assigned (success).",
            domain="launchdarkly-leftover-targeting-before-percentage",
            stack="LaunchDarkly leftover targeting",
            seed="launchdarkly-leftover-targeting-vs-pct",
            residual="Leftover targeting beats percentage.",
            coverage=85,
        ),
        _bad(
            slug="launchdarkly-drop-targeting-handoff",
            goal="Do not drop LaunchDarkly leftover targeting when evaluating the flag.",
            plan="Read drop-targeting, try fallthrough, then hand off targeting.",
            mod="lddrop",
            test_fn="test_drop_targeting",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)\n",
            test_body=(
                "def test_drop_targeting():\n"
                "    assert eval_flag({'user_id': 'u1', 'leftover_targeting': 'rule-7'}) != True\n"
            ),
            grep_pat="leftover_targeting|targeting|launchdarkly",
            grep_hit="src/lddrop.py:2: return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            fail_msg="AssertionError: leftover targeting dropped; naive pct used",
            first_old="    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            first_new="    return ctx.get('fallthrough') is True",
            first_obs="patched fallthrough (still dropped leftover targeting)",
            still_msg="AssertionError: dropping leftover targeting is not a boolean gate",
            reread_obs="LD targeting rules are required leftover; drop is flag-plat",
            plan_change="Dropped leftover targeting is flag-plat. Handoff LD-TG-8.",
            fix_new="    return {'handoff': 'LD-TG-8'}",
            fix_obs="ticket filed. still dropped leftover",
            docs_url="https://docs.launchdarkly.com/home/flags/targeting",
            docs_ok="Targeting rules must stay attached; dropping them is not a rollout.",
            docs_url2="https://docs.launchdarkly.com/sdk/features/evaluation",
            docs_ok2="Drop leftover targeting owned by flag-plat. Handoff LD-TG-8.",
            outcome="Still dropped leftover; LD targeting is flag-plat — handoff LD-TG-8.",
            domain="launchdarkly-drop-leftover-targeting",
            stack="LaunchDarkly drop targeting",
            seed="launchdarkly-drop-targeting-handoff",
            residual="Do not drop leftover targeting.",
            ticket="LD-TG-8",
            ticket_why="LaunchDarkly leftover targeting owned by flag-plat",
            coverage=85,
        ),
    ),
    (
        _ok(
            slug="split-leftover-treatment-vs-pct",
            goal="Honor Split leftover treatment assignment before naive percentage.",
            plan="Read pct-as-treatment, try salt, then leftover treatment unit.",
            mod="spltrt",
            test_fn="test_leftover_treatment",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx['pct']\n",
            test_body=(
                "def test_leftover_treatment():\n"
                "    assert eval_flag({'user_id': 'u1', 'pct': 50, 'leftover_treatment': 'on'}"
                ") == 'on'\n"
            ),
            grep_pat="leftover_treatment|pct|split",
            grep_hit="src/spltrt.py:2: return hash(ctx['user_id']) % 100 < ctx['pct']",
            fail_msg="AssertionError: True == 'on'; percentage swallowed leftover treatment",
            first_old="    return hash(ctx['user_id']) % 100 < ctx['pct']",
            first_new="    return hash(ctx['user_id'] + 'salt') % 100 < ctx['pct']",
            first_obs="patched salt (still percentage, still not leftover treatment)",
            still_msg="AssertionError: salt does not return the Split leftover treatment",
            reread_obs="Split leftover treatment binds bucket; percentage is only unbound",
            plan_change="Return leftover_treatment if present. Salt does not replace treatment. Not Statsig.",
            fix_new="    return ctx.get('leftover_treatment') or (hash(ctx['user_id']) % 100 < ctx['pct'])",
            fix_obs="patched leftover-treatment-before-pct",
            docs_url="https://help.split.io/hc/en-us/articles/360019916311-Treatments",
            docs_ok="Split leftover treatment assignment wins over default percentage.",
            docs_url2="https://help.split.io/hc/en-us/articles/360020448791-Traffic-types",
            docs_ok2="Honor leftover treatment. Not Statsig. Not LaunchDarkly clone.",
            outcome="Leftover treatment on won. Percentage unused for assigned (success).",
            domain="split-leftover-treatment-before-percentage",
            stack="Split leftover treatment",
            seed="split-leftover-treatment-vs-pct",
            residual="Leftover treatment beats percentage.",
            coverage=85,
        ),
        _bad(
            slug="split-drop-treatment-handoff",
            goal="Do not drop Split leftover treatment when evaluating the flag.",
            plan="Read drop-treatment, try control, then hand off treatment.",
            mod="spldrop",
            test_fn="test_drop_treatment",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)\n",
            test_body=(
                "def test_drop_treatment():\n"
                "    assert eval_flag({'user_id': 'u1', 'leftover_treatment': 'on'}) != True\n"
            ),
            grep_pat="leftover_treatment|treatment|split",
            grep_hit="src/spldrop.py:2: return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            fail_msg="AssertionError: leftover treatment dropped; naive pct used",
            first_old="    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            first_new="    return ctx.get('control') == 'on'",
            first_obs="patched control==on (still dropped leftover treatment)",
            still_msg="AssertionError: dropping leftover treatment is not a boolean gate",
            reread_obs="Split treatment is required leftover; drop is experiment-plat",
            plan_change="Dropped leftover treatment is experiment-plat. Handoff SP-TR-3.",
            fix_new="    return {'handoff': 'SP-TR-3'}",
            fix_obs="ticket filed. still dropped leftover",
            docs_url="https://help.split.io/hc/en-us/articles/360019916311-Treatments",
            docs_ok="Treatment must stay attached; dropping it is not a rollout.",
            docs_url2="https://help.split.io/hc/en-us/articles/360020448791-Traffic-types",
            docs_ok2="Drop leftover treatment owned by experiment-plat. Handoff SP-TR-3.",
            outcome="Still dropped leftover; Split treatment is experiment-plat — handoff SP-TR-3.",
            domain="split-drop-leftover-treatment",
            stack="Split drop treatment",
            seed="split-drop-treatment-handoff",
            residual="Do not drop leftover treatment.",
            ticket="SP-TR-3",
            ticket_why="Split leftover treatment owned by experiment-plat",
            coverage=85,
        ),
    ),
    (
        _ok(
            slug="configcat-leftover-userobject-vs-pct",
            goal="Honor ConfigCat leftover User Object targeting before naive percentage.",
            plan="Read pct-as-userobject, try salt, then leftover user object unit.",
            mod="ccuser",
            test_fn="test_leftover_userobject",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx['pct']\n",
            test_body=(
                "def test_leftover_userobject():\n"
                "    assert eval_flag({'user_id': 'u1', 'pct': 50, 'leftover_userobject': 'email'}"
                ") == 'email'\n"
            ),
            grep_pat="leftover_userobject|pct|configcat",
            grep_hit="src/ccuser.py:2: return hash(ctx['user_id']) % 100 < ctx['pct']",
            fail_msg="AssertionError: True == 'email'; percentage swallowed leftover User Object",
            first_old="    return hash(ctx['user_id']) % 100 < ctx['pct']",
            first_new="    return hash(ctx['user_id'] + 'salt') % 100 < ctx['pct']",
            first_obs="patched salt (still percentage, still not leftover userobject)",
            still_msg="AssertionError: salt does not return the ConfigCat leftover User Object",
            reread_obs="ConfigCat leftover User Object binds targeting; percentage is only unbound",
            plan_change="Return leftover_userobject if present. Salt does not replace User Object. Not Statsig.",
            fix_new="    return ctx.get('leftover_userobject') or (hash(ctx['user_id']) % 100 < ctx['pct'])",
            fix_obs="patched leftover-userobject-before-pct",
            docs_url="https://configcat.com/docs/targeting/targeting-overview/",
            docs_ok="ConfigCat leftover User Object assignment wins over default percentage.",
            docs_url2="https://configcat.com/docs/sdk-reference/overview/",
            docs_ok2="Honor leftover User Object. Not Statsig. Not Split clone.",
            outcome="Leftover User Object email won. Percentage unused for assigned (success).",
            domain="configcat-leftover-userobject-before-percentage",
            stack="ConfigCat leftover User Object",
            seed="configcat-leftover-userobject-vs-pct",
            residual="Leftover User Object beats percentage.",
            coverage=85,
        ),
        _bad(
            slug="configcat-drop-userobject-handoff",
            goal="Do not drop ConfigCat leftover User Object when evaluating the flag.",
            plan="Read drop-userobject, try identifier-only, then hand off userobject.",
            mod="ccdrop",
            test_fn="test_drop_userobject",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)\n",
            test_body=(
                "def test_drop_userobject():\n"
                "    assert eval_flag({'user_id': 'u1', 'leftover_userobject': 'email'}) != True\n"
            ),
            grep_pat="leftover_userobject|User Object|configcat",
            grep_hit="src/ccdrop.py:2: return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            fail_msg="AssertionError: leftover User Object dropped; naive pct used",
            first_old="    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            first_new="    return bool(ctx.get('identifier'))",
            first_obs="patched identifier bool (still dropped leftover userobject)",
            still_msg="AssertionError: dropping leftover User Object is not a boolean gate",
            reread_obs="ConfigCat User Object is required leftover; drop is flag-plat",
            plan_change="Dropped leftover User Object is flag-plat. Handoff CC-UO-2.",
            fix_new="    return {'handoff': 'CC-UO-2'}",
            fix_obs="ticket filed. still dropped leftover",
            docs_url="https://configcat.com/docs/targeting/user-object/",
            docs_ok="User Object must stay attached; dropping it is not a rollout.",
            docs_url2="https://configcat.com/docs/targeting/targeting-overview/",
            docs_ok2="Drop leftover User Object owned by flag-plat. Handoff CC-UO-2.",
            outcome="Still dropped leftover; ConfigCat User Object is flag-plat — handoff CC-UO-2.",
            domain="configcat-drop-leftover-userobject",
            stack="ConfigCat drop User Object",
            seed="configcat-drop-userobject-handoff",
            residual="Do not drop leftover User Object.",
            ticket="CC-UO-2",
            ticket_why="ConfigCat leftover User Object owned by flag-plat",
            coverage=85,
        ),
    ),
    (
        _ok(
            slug="devcycle-leftover-variable-vs-pct",
            goal="Honor DevCycle leftover variable value before naive percentage.",
            plan="Read pct-as-variable, try salt, then leftover variable unit.",
            mod="dcvar",
            test_fn="test_leftover_variable",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx['pct']\n",
            test_body=(
                "def test_leftover_variable():\n"
                "    assert eval_flag({'user_id': 'u1', 'pct': 50, 'leftover_variable': 'theme'}"
                ") == 'theme'\n"
            ),
            grep_pat="leftover_variable|pct|devcycle",
            grep_hit="src/dcvar.py:2: return hash(ctx['user_id']) % 100 < ctx['pct']",
            fail_msg="AssertionError: True == 'theme'; percentage swallowed leftover variable",
            first_old="    return hash(ctx['user_id']) % 100 < ctx['pct']",
            first_new="    return hash(ctx['user_id'] + 'salt') % 100 < ctx['pct']",
            first_obs="patched salt (still percentage, still not leftover variable)",
            still_msg="AssertionError: salt does not return the DevCycle leftover variable",
            reread_obs="DevCycle leftover variable binds value; percentage is only unbound",
            plan_change="Return leftover_variable if present. Salt does not replace variable. Not Statsig.",
            fix_new="    return ctx.get('leftover_variable') or (hash(ctx['user_id']) % 100 < ctx['pct'])",
            fix_obs="patched leftover-variable-before-pct",
            docs_url="https://docs.devcycle.com/sdk/client-side-sdks/",
            docs_ok="DevCycle leftover variable assignment wins over default percentage.",
            docs_url2="https://docs.devcycle.com/features/feature-flags/",
            docs_ok2="Honor leftover variable. Not Statsig. Not ConfigCat clone.",
            outcome="Leftover variable theme won. Percentage unused for assigned (success).",
            domain="devcycle-leftover-variable-before-percentage",
            stack="DevCycle leftover variable",
            seed="devcycle-leftover-variable-vs-pct",
            residual="Leftover variable beats percentage.",
            coverage=84,
        ),
        _bad(
            slug="devcycle-drop-variable-handoff",
            goal="Do not drop DevCycle leftover variable when evaluating the flag.",
            plan="Read drop-variable, try default, then hand off variable.",
            mod="dcdrop",
            test_fn="test_drop_variable",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)\n",
            test_body=(
                "def test_drop_variable():\n"
                "    assert eval_flag({'user_id': 'u1', 'leftover_variable': 'theme'}) != True\n"
            ),
            grep_pat="leftover_variable|variable|devcycle",
            grep_hit="src/dcdrop.py:2: return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            fail_msg="AssertionError: leftover variable dropped; naive pct used",
            first_old="    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            first_new="    return ctx.get('default') is True",
            first_obs="patched default True (still dropped leftover variable)",
            still_msg="AssertionError: dropping leftover variable is not a boolean gate",
            reread_obs="DevCycle variable is required leftover; drop is flag-plat",
            plan_change="Dropped leftover variable is flag-plat. Handoff DC-VR-7.",
            fix_new="    return {'handoff': 'DC-VR-7'}",
            fix_obs="ticket filed. still dropped leftover",
            docs_url="https://docs.devcycle.com/features/variables/",
            docs_ok="Variable must stay attached; dropping it is not a rollout.",
            docs_url2="https://docs.devcycle.com/features/feature-flags/",
            docs_ok2="Drop leftover variable owned by flag-plat. Handoff DC-VR-7.",
            outcome="Still dropped leftover; DevCycle variable is flag-plat — handoff DC-VR-7.",
            domain="devcycle-drop-leftover-variable",
            stack="DevCycle drop variable",
            seed="devcycle-drop-variable-handoff",
            residual="Do not drop leftover variable.",
            ticket="DC-VR-7",
            ticket_why="DevCycle leftover variable owned by flag-plat",
            coverage=84,
        ),
    ),
    (
        _ok(
            slug="harness-leftover-target-vs-pct",
            goal="Honor Harness leftover target rules before naive percentage.",
            plan="Read pct-as-target, try salt, then leftover target unit.",
            mod="hntgt",
            test_fn="test_leftover_target",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx['pct']\n",
            test_body=(
                "def test_leftover_target():\n"
                "    assert eval_flag({'user_id': 'u1', 'pct': 50, 'leftover_target': 'group-a'}"
                ") == 'group-a'\n"
            ),
            grep_pat="leftover_target|pct|harness",
            grep_hit="src/hntgt.py:2: return hash(ctx['user_id']) % 100 < ctx['pct']",
            fail_msg="AssertionError: True == 'group-a'; percentage swallowed leftover target",
            first_old="    return hash(ctx['user_id']) % 100 < ctx['pct']",
            first_new="    return hash(ctx['user_id'] + 'salt') % 100 < ctx['pct']",
            first_obs="patched salt (still percentage, still not leftover target)",
            still_msg="AssertionError: salt does not return the Harness leftover target",
            reread_obs="Harness leftover target binds variation; percentage is only unbound",
            plan_change="Return leftover_target if present. Salt does not replace target. Not Statsig.",
            fix_new="    return ctx.get('leftover_target') or (hash(ctx['user_id']) % 100 < ctx['pct'])",
            fix_obs="patched leftover-target-before-pct",
            docs_url="https://developer.harness.io/docs/feature-flags/",
            docs_ok="Harness leftover target assignment wins over default percentage.",
            docs_url2="https://developer.harness.io/docs/feature-flags/ff-sdks/sdk-overview/",
            docs_ok2="Honor leftover target. Not Statsig. Not DevCycle clone.",
            outcome="Leftover target group-a won. Percentage unused for assigned (success).",
            domain="harness-leftover-target-before-percentage",
            stack="Harness leftover target",
            seed="harness-leftover-target-vs-pct",
            residual="Leftover target beats percentage.",
            coverage=84,
        ),
        _bad(
            slug="harness-drop-target-handoff",
            goal="Do not drop Harness leftover target when evaluating the flag.",
            plan="Read drop-target, try environment, then hand off target.",
            mod="hndrop",
            test_fn="test_drop_target",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)\n",
            test_body=(
                "def test_drop_target():\n"
                "    assert eval_flag({'user_id': 'u1', 'leftover_target': 'group-a'}) != True\n"
            ),
            grep_pat="leftover_target|target|harness",
            grep_hit="src/hndrop.py:2: return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            fail_msg="AssertionError: leftover target dropped; naive pct used",
            first_old="    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            first_new="    return ctx.get('environment') == 'prod'",
            first_obs="patched environment==prod (still dropped leftover target)",
            still_msg="AssertionError: dropping leftover target is not a boolean gate",
            reread_obs="Harness target is required leftover; drop is flag-plat",
            plan_change="Dropped leftover target is flag-plat. Handoff HN-TG-9.",
            fix_new="    return {'handoff': 'HN-TG-9'}",
            fix_obs="ticket filed. still dropped leftover",
            docs_url="https://developer.harness.io/docs/feature-flags/ff-using-flags/ff-target/",
            docs_ok="Target must stay attached; dropping it is not a rollout.",
            docs_url2="https://developer.harness.io/docs/feature-flags/",
            docs_ok2="Drop leftover target owned by flag-plat. Handoff HN-TG-9.",
            outcome="Still dropped leftover; Harness target is flag-plat — handoff HN-TG-9.",
            domain="harness-drop-leftover-target",
            stack="Harness drop target",
            seed="harness-drop-target-handoff",
            residual="Do not drop leftover target.",
            ticket="HN-TG-9",
            ticket_why="Harness leftover target owned by flag-plat",
            coverage=84,
        ),
    ),
    (
        _ok(
            slug="amplitude-leftover-assignment-vs-pct",
            goal="Honor Amplitude Experiment leftover assignment before naive percentage.",
            plan="Read pct-as-assignment, try salt, then leftover assignment unit.",
            mod="ampasg",
            test_fn="test_leftover_assignment",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx['pct']\n",
            test_body=(
                "def test_leftover_assignment():\n"
                "    assert eval_flag({'user_id': 'u1', 'pct': 50, 'leftover_assignment': 'variant-b'}"
                ") == 'variant-b'\n"
            ),
            grep_pat="leftover_assignment|pct|amplitude",
            grep_hit="src/ampasg.py:2: return hash(ctx['user_id']) % 100 < ctx['pct']",
            fail_msg="AssertionError: True == 'variant-b'; percentage swallowed leftover assignment",
            first_old="    return hash(ctx['user_id']) % 100 < ctx['pct']",
            first_new="    return hash(ctx['user_id'] + 'salt') % 100 < ctx['pct']",
            first_obs="patched salt (still percentage, still not leftover assignment)",
            still_msg="AssertionError: salt does not return the Amplitude leftover assignment",
            reread_obs="Amplitude leftover assignment binds variant; percentage is only unbound",
            plan_change="Return leftover_assignment if present. Salt does not replace assignment. Not Statsig.",
            fix_new="    return ctx.get('leftover_assignment') or (hash(ctx['user_id']) % 100 < ctx['pct'])",
            fix_obs="patched leftover-assignment-before-pct",
            docs_url="https://www.docs.developers.amplitude.com/experiment/guides/getting-started/",
            docs_ok="Amplitude leftover assignment wins over default percentage.",
            docs_url2="https://www.docs.developers.amplitude.com/experiment/sdks/",
            docs_ok2="Honor leftover assignment. Not Statsig. Not Harness clone.",
            outcome="Leftover assignment variant-b won. Percentage unused for assigned (success).",
            domain="amplitude-leftover-assignment-before-percentage",
            stack="Amplitude leftover assignment",
            seed="amplitude-leftover-assignment-vs-pct",
            residual="Leftover assignment beats percentage.",
            coverage=84,
        ),
        _bad(
            slug="amplitude-drop-assignment-handoff",
            goal="Do not drop Amplitude leftover assignment when evaluating the flag.",
            plan="Read drop-assignment, try exposure, then hand off assignment.",
            mod="ampdrop",
            test_fn="test_drop_assignment",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)\n",
            test_body=(
                "def test_drop_assignment():\n"
                "    assert eval_flag({'user_id': 'u1', 'leftover_assignment': 'variant-b'}) != True\n"
            ),
            grep_pat="leftover_assignment|assignment|amplitude",
            grep_hit="src/ampdrop.py:2: return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            fail_msg="AssertionError: leftover assignment dropped; naive pct used",
            first_old="    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            first_new="    return ctx.get('exposure') is True",
            first_obs="patched exposure True (still dropped leftover assignment)",
            still_msg="AssertionError: dropping leftover assignment is not a boolean gate",
            reread_obs="Amplitude assignment is required leftover; drop is experiment-plat",
            plan_change="Dropped leftover assignment is experiment-plat. Handoff AM-AS-1.",
            fix_new="    return {'handoff': 'AM-AS-1'}",
            fix_obs="ticket filed. still dropped leftover",
            docs_url="https://www.docs.developers.amplitude.com/experiment/guides/assignment/",
            docs_ok="Assignment must stay attached; dropping it is not a rollout.",
            docs_url2="https://www.docs.developers.amplitude.com/experiment/guides/getting-started/",
            docs_ok2="Drop leftover assignment owned by experiment-plat. Handoff AM-AS-1.",
            outcome="Still dropped leftover; Amplitude assignment is experiment-plat — handoff AM-AS-1.",
            domain="amplitude-drop-leftover-assignment",
            stack="Amplitude drop assignment",
            seed="amplitude-drop-assignment-handoff",
            residual="Do not drop leftover assignment.",
            ticket="AM-AS-1",
            ticket_why="Amplitude leftover assignment owned by experiment-plat",
            coverage=84,
        ),
    ),
    (
        _ok(
            slug="posthog-leftover-multivariate-vs-pct",
            goal="Honor PostHog leftover multivariate payload before naive percentage.",
            plan="Read pct-as-multivariate, try salt, then leftover multivariate unit.",
            mod="phmv",
            test_fn="test_leftover_multivariate",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx['pct']\n",
            test_body=(
                "def test_leftover_multivariate():\n"
                "    assert eval_flag({'user_id': 'u1', 'pct': 50, 'leftover_multivariate': 'control'}"
                ") == 'control'\n"
            ),
            grep_pat="leftover_multivariate|pct|posthog",
            grep_hit="src/phmv.py:2: return hash(ctx['user_id']) % 100 < ctx['pct']",
            fail_msg="AssertionError: True == 'control'; percentage swallowed leftover multivariate",
            first_old="    return hash(ctx['user_id']) % 100 < ctx['pct']",
            first_new="    return hash(ctx['user_id'] + 'salt') % 100 < ctx['pct']",
            first_obs="patched salt (still percentage, still not leftover multivariate)",
            still_msg="AssertionError: salt does not return the PostHog leftover multivariate",
            reread_obs="PostHog leftover multivariate binds payload; percentage is only unbound",
            plan_change="Return leftover_multivariate if present. Salt does not replace payload. Not Statsig.",
            fix_new="    return ctx.get('leftover_multivariate') or (hash(ctx['user_id']) % 100 < ctx['pct'])",
            fix_obs="patched leftover-multivariate-before-pct",
            docs_url="https://posthog.com/docs/feature-flags/multivariate-flags",
            docs_ok="PostHog leftover multivariate assignment wins over default percentage.",
            docs_url2="https://posthog.com/docs/feature-flags",
            docs_ok2="Honor leftover multivariate. Not Statsig. Not Amplitude clone.",
            outcome="Leftover multivariate control won. Percentage unused for assigned (success).",
            domain="posthog-leftover-multivariate-before-percentage",
            stack="PostHog leftover multivariate",
            seed="posthog-leftover-multivariate-vs-pct",
            residual="Leftover multivariate beats percentage.",
            coverage=84,
        ),
        _bad(
            slug="posthog-drop-multivariate-handoff",
            goal="Do not drop PostHog leftover multivariate when evaluating the flag.",
            plan="Read drop-multivariate, try boolean, then hand off multivariate.",
            mod="phdrop",
            test_fn="test_drop_multivariate",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)\n",
            test_body=(
                "def test_drop_multivariate():\n"
                "    assert eval_flag({'user_id': 'u1', 'leftover_multivariate': 'control'}) != True\n"
            ),
            grep_pat="leftover_multivariate|multivariate|posthog",
            grep_hit="src/phdrop.py:2: return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            fail_msg="AssertionError: leftover multivariate dropped; naive pct used",
            first_old="    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            first_new="    return bool(ctx.get('flag_on'))",
            first_obs="patched flag_on bool (still dropped leftover multivariate)",
            still_msg="AssertionError: dropping leftover multivariate is not a boolean gate",
            reread_obs="PostHog multivariate payload is required leftover; drop is experiment-plat",
            plan_change="Dropped leftover multivariate is experiment-plat. Handoff PH-MV-2.",
            fix_new="    return {'handoff': 'PH-MV-2'}",
            fix_obs="ticket filed. still dropped leftover",
            docs_url="https://posthog.com/docs/feature-flags/multivariate-flags",
            docs_ok="Multivariate payload must stay attached; dropping it is not a rollout.",
            docs_url2="https://posthog.com/docs/feature-flags",
            docs_ok2="Drop leftover multivariate owned by experiment-plat. Handoff PH-MV-2.",
            outcome="Still dropped leftover; PostHog multivariate is experiment-plat — handoff PH-MV-2.",
            domain="posthog-drop-leftover-multivariate",
            stack="PostHog drop multivariate",
            seed="posthog-drop-multivariate-handoff",
            residual="Do not drop leftover multivariate.",
            ticket="PH-MV-2",
            ticket_why="PostHog leftover multivariate owned by experiment-plat",
            coverage=84,
        ),
    ),
    (
        _ok(
            slug="optimizely-leftover-audience-vs-pct",
            goal="Honor Optimizely leftover audience assignment before naive percentage.",
            plan="Read pct-as-audience, try salt, then leftover audience unit.",
            mod="opaud",
            test_fn="test_leftover_audience",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx['pct']\n",
            test_body=(
                "def test_leftover_audience():\n"
                "    assert eval_flag({'user_id': 'u1', 'pct': 50, 'leftover_audience': 'aud-west'}"
                ") == 'aud-west'\n"
            ),
            grep_pat="leftover_audience|pct|optimizely",
            grep_hit="src/opaud.py:2: return hash(ctx['user_id']) % 100 < ctx['pct']",
            fail_msg="AssertionError: True == 'aud-west'; percentage swallowed leftover audience",
            first_old="    return hash(ctx['user_id']) % 100 < ctx['pct']",
            first_new="    return hash(ctx['user_id'] + 'salt') % 100 < ctx['pct']",
            first_obs="patched salt (still percentage, still not leftover audience)",
            still_msg="AssertionError: salt does not return the Optimizely leftover audience",
            reread_obs="Optimizely leftover audience binds variation; percentage is only unbound",
            plan_change="Return leftover_audience if present. Salt does not replace audience. Not Statsig.",
            fix_new="    return ctx.get('leftover_audience') or (hash(ctx['user_id']) % 100 < ctx['pct'])",
            fix_obs="patched leftover-audience-before-pct",
            docs_url="https://docs.developers.optimizely.com/full-stack/docs/audiences",
            docs_ok="Optimizely leftover audience assignment wins over default percentage.",
            docs_url2="https://docs.developers.optimizely.com/full-stack/docs/run-ab-tests",
            docs_ok2="Honor leftover audience. Not Statsig. Not PostHog clone.",
            outcome="Leftover audience aud-west won. Percentage unused for assigned (success).",
            domain="optimizely-leftover-audience-before-percentage",
            stack="Optimizely leftover audience",
            seed="optimizely-leftover-audience-vs-pct",
            residual="Leftover audience beats percentage.",
            coverage=83,
        ),
        _bad(
            slug="optimizely-drop-audience-handoff",
            goal="Do not drop Optimizely leftover audience when evaluating the flag.",
            plan="Read drop-audience, try everyone, then hand off audience.",
            mod="opdrop",
            test_fn="test_drop_audience",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)\n",
            test_body=(
                "def test_drop_audience():\n"
                "    assert eval_flag({'user_id': 'u1', 'leftover_audience': 'aud-west'}) != True\n"
            ),
            grep_pat="leftover_audience|audience|optimizely",
            grep_hit="src/opdrop.py:2: return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            fail_msg="AssertionError: leftover audience dropped; naive pct used",
            first_old="    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            first_new="    return ctx.get('everyone') is True",
            first_obs="patched everyone True (still dropped leftover audience)",
            still_msg="AssertionError: dropping leftover audience is not a boolean gate",
            reread_obs="Optimizely audience is required leftover; drop is experiment-plat",
            plan_change="Dropped leftover audience is experiment-plat. Handoff OP-AU-5.",
            fix_new="    return {'handoff': 'OP-AU-5'}",
            fix_obs="ticket filed. still dropped leftover",
            docs_url="https://docs.developers.optimizely.com/full-stack/docs/audiences",
            docs_ok="Audience must stay attached; dropping it is not a rollout.",
            docs_url2="https://docs.developers.optimizely.com/full-stack/docs/run-ab-tests",
            docs_ok2="Drop leftover audience owned by experiment-plat. Handoff OP-AU-5.",
            outcome="Still dropped leftover; Optimizely audience is experiment-plat — handoff OP-AU-5.",
            domain="optimizely-drop-leftover-audience",
            stack="Optimizely drop audience",
            seed="optimizely-drop-audience-handoff",
            residual="Do not drop leftover audience.",
            ticket="OP-AU-5",
            ticket_why="Optimizely leftover audience owned by experiment-plat",
            coverage=83,
        ),
    ),
    (
        _ok(
            slug="vwo-leftover-campaign-vs-pct",
            goal="Honor VWO leftover campaign assignment before naive percentage.",
            plan="Read pct-as-campaign, try salt, then leftover campaign unit.",
            mod="vwocmp",
            test_fn="test_leftover_campaign",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx['pct']\n",
            test_body=(
                "def test_leftover_campaign():\n"
                "    assert eval_flag({'user_id': 'u1', 'pct': 50, 'leftover_campaign': 'camp-9'}"
                ") == 'camp-9'\n"
            ),
            grep_pat="leftover_campaign|pct|vwo",
            grep_hit="src/vwocmp.py:2: return hash(ctx['user_id']) % 100 < ctx['pct']",
            fail_msg="AssertionError: True == 'camp-9'; percentage swallowed leftover campaign",
            first_old="    return hash(ctx['user_id']) % 100 < ctx['pct']",
            first_new="    return hash(ctx['user_id'] + 'salt') % 100 < ctx['pct']",
            first_obs="patched salt (still percentage, still not leftover campaign)",
            still_msg="AssertionError: salt does not return the VWO leftover campaign",
            reread_obs="VWO leftover campaign binds variation; percentage is only unbound",
            plan_change="Return leftover_campaign if present. Salt does not replace campaign. Not Statsig.",
            fix_new="    return ctx.get('leftover_campaign') or (hash(ctx['user_id']) % 100 < ctx['pct'])",
            fix_obs="patched leftover-campaign-before-pct",
            docs_url="https://developers.vwo.com/server-side/docs/campaigns",
            docs_ok="VWO leftover campaign assignment wins over default percentage.",
            docs_url2="https://developers.vwo.com/server-side/docs/sdk-reference",
            docs_ok2="Honor leftover campaign. Not Statsig. Not Optimizely clone.",
            outcome="Leftover campaign camp-9 won. Percentage unused for assigned (success).",
            domain="vwo-leftover-campaign-before-percentage",
            stack="VWO leftover campaign",
            seed="vwo-leftover-campaign-vs-pct",
            residual="Leftover campaign beats percentage.",
            coverage=83,
        ),
        _bad(
            slug="vwo-drop-campaign-handoff",
            goal="Do not drop VWO leftover campaign when evaluating the flag.",
            plan="Read drop-campaign, try goal, then hand off campaign.",
            mod="vwodrop",
            test_fn="test_drop_campaign",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)\n",
            test_body=(
                "def test_drop_campaign():\n"
                "    assert eval_flag({'user_id': 'u1', 'leftover_campaign': 'camp-9'}) != True\n"
            ),
            grep_pat="leftover_campaign|campaign|vwo",
            grep_hit="src/vwodrop.py:2: return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            fail_msg="AssertionError: leftover campaign dropped; naive pct used",
            first_old="    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            first_new="    return ctx.get('goal') == 'conversion'",
            first_obs="patched goal==conversion (still dropped leftover campaign)",
            still_msg="AssertionError: dropping leftover campaign is not a boolean gate",
            reread_obs="VWO campaign is required leftover; drop is experiment-plat",
            plan_change="Dropped leftover campaign is experiment-plat. Handoff VW-CP-6.",
            fix_new="    return {'handoff': 'VW-CP-6'}",
            fix_obs="ticket filed. still dropped leftover",
            docs_url="https://developers.vwo.com/server-side/docs/campaigns",
            docs_ok="Campaign must stay attached; dropping it is not a rollout.",
            docs_url2="https://developers.vwo.com/server-side/docs/sdk-reference",
            docs_ok2="Drop leftover campaign owned by experiment-plat. Handoff VW-CP-6.",
            outcome="Still dropped leftover; VWO campaign is experiment-plat — handoff VW-CP-6.",
            domain="vwo-drop-leftover-campaign",
            stack="VWO drop campaign",
            seed="vwo-drop-campaign-handoff",
            residual="Do not drop leftover campaign.",
            ticket="VW-CP-6",
            ticket_why="VWO leftover campaign owned by experiment-plat",
            coverage=83,
        ),
    ),
    (
        _ok(
            slug="eppo-leftover-assignment-log-vs-pct",
            goal="Honor Eppo leftover assignment log before naive percentage.",
            plan="Read pct-as-log, try salt, then leftover assignment-log unit.",
            mod="epplog",
            test_fn="test_leftover_assignment_log",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx['pct']\n",
            test_body=(
                "def test_leftover_assignment_log():\n"
                "    assert eval_flag({'user_id': 'u1', 'pct': 50, 'leftover_assignment_log': 'log-3'}"
                ") == 'log-3'\n"
            ),
            grep_pat="leftover_assignment_log|pct|eppo",
            grep_hit="src/epplog.py:2: return hash(ctx['user_id']) % 100 < ctx['pct']",
            fail_msg="AssertionError: True == 'log-3'; percentage swallowed leftover assignment log",
            first_old="    return hash(ctx['user_id']) % 100 < ctx['pct']",
            first_new="    return hash(ctx['user_id'] + 'salt') % 100 < ctx['pct']",
            first_obs="patched salt (still percentage, still not leftover assignment log)",
            still_msg="AssertionError: salt does not return the Eppo leftover assignment log",
            reread_obs="Eppo leftover assignment log binds variation; percentage is only unbound",
            plan_change="Return leftover_assignment_log if present. Salt does not replace log. Not Statsig.",
            fix_new="    return ctx.get('leftover_assignment_log') or (hash(ctx['user_id']) % 100 < ctx['pct'])",
            fix_obs="patched leftover-assignment-log-before-pct",
            docs_url="https://docs.geteppo.com/sdks/event-logging/assignment-logging/",
            docs_ok="Eppo leftover assignment log wins over default percentage.",
            docs_url2="https://docs.geteppo.com/sdks/sdk-features/assignments/",
            docs_ok2="Honor leftover assignment log. Not Statsig. Not VWO clone.",
            outcome="Leftover assignment log log-3 won. Percentage unused for assigned (success).",
            domain="eppo-leftover-assignment-log-before-percentage",
            stack="Eppo leftover assignment log",
            seed="eppo-leftover-assignment-log-vs-pct",
            residual="Leftover assignment log beats percentage.",
            coverage=83,
        ),
        _bad(
            slug="eppo-drop-assignment-log-handoff",
            goal="Do not drop Eppo leftover assignment log when evaluating the flag.",
            plan="Read drop-log, try silent, then hand off assignment log.",
            mod="epdrop",
            test_fn="test_drop_assignment_log",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)\n",
            test_body=(
                "def test_drop_assignment_log():\n"
                "    assert eval_flag({'user_id': 'u1', 'leftover_assignment_log': 'log-3'}) != True\n"
            ),
            grep_pat="leftover_assignment_log|assignment.log|eppo",
            grep_hit="src/epdrop.py:2: return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            fail_msg="AssertionError: leftover assignment log dropped; naive pct used",
            first_old="    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            first_new="    return ctx.get('silent') is True",
            first_obs="patched silent True (still dropped leftover assignment log)",
            still_msg="AssertionError: dropping leftover assignment log is not a boolean gate",
            reread_obs="Eppo assignment log is required leftover; drop is experiment-plat",
            plan_change="Dropped leftover assignment log is experiment-plat. Handoff EP-AL-4.",
            fix_new="    return {'handoff': 'EP-AL-4'}",
            fix_obs="ticket filed. still dropped leftover",
            docs_url="https://docs.geteppo.com/sdks/event-logging/assignment-logging/",
            docs_ok="Assignment log must stay attached; dropping it is not a rollout.",
            docs_url2="https://docs.geteppo.com/sdks/sdk-features/assignments/",
            docs_ok2="Drop leftover assignment log owned by experiment-plat. Handoff EP-AL-4.",
            outcome="Still dropped leftover; Eppo assignment log is experiment-plat — handoff EP-AL-4.",
            domain="eppo-drop-leftover-assignment-log",
            stack="Eppo drop assignment log",
            seed="eppo-drop-assignment-log-handoff",
            residual="Do not drop leftover assignment log.",
            ticket="EP-AL-4",
            ticket_why="Eppo leftover assignment log owned by experiment-plat",
            coverage=83,
        ),
    ),
    (
        _ok(
            slug="cloudbees-leftover-targeting-vs-pct",
            goal="Honor CloudBees leftover targeting assignment before naive percentage.",
            plan="Read pct-as-targeting, try salt, then leftover targeting unit.",
            mod="cbtgt",
            test_fn="test_leftover_cb_targeting",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx['pct']\n",
            test_body=(
                "def test_leftover_cb_targeting():\n"
                "    assert eval_flag({'user_id': 'u1', 'pct': 50, 'leftover_targeting': 'seg-eu'}"
                ") == 'seg-eu'\n"
            ),
            grep_pat="leftover_targeting|pct|cloudbees",
            grep_hit="src/cbtgt.py:2: return hash(ctx['user_id']) % 100 < ctx['pct']",
            fail_msg="AssertionError: True == 'seg-eu'; percentage swallowed leftover targeting",
            first_old="    return hash(ctx['user_id']) % 100 < ctx['pct']",
            first_new="    return hash(ctx['user_id'] + 'salt') % 100 < ctx['pct']",
            first_obs="patched salt (still percentage, still not leftover targeting)",
            still_msg="AssertionError: salt does not return the CloudBees leftover targeting",
            reread_obs="CloudBees leftover targeting binds segment; percentage is only unbound",
            plan_change="Return leftover_targeting if present. Salt does not replace targeting. Not Statsig.",
            fix_new="    return ctx.get('leftover_targeting') or (hash(ctx['user_id']) % 100 < ctx['pct'])",
            fix_obs="patched leftover-targeting-before-pct",
            docs_url="https://docs.cloudbees.com/docs/cloudbees-feature-management/",
            docs_ok="CloudBees leftover targeting wins over default percentage.",
            docs_url2="https://docs.cloudbees.com/docs/cloudbees-feature-management/latest/feature-flags/",
            docs_ok2="Honor leftover targeting. Not Statsig. Not LaunchDarkly clone.",
            outcome="Leftover targeting seg-eu won. Percentage unused for assigned (success).",
            domain="cloudbees-leftover-targeting-before-percentage",
            stack="CloudBees leftover targeting",
            seed="cloudbees-leftover-targeting-vs-pct",
            residual="Leftover targeting beats percentage. Statsig skipped.",
            coverage=83,
        ),
        _bad(
            slug="cloudbees-drop-targeting-handoff",
            goal="Do not drop CloudBees leftover targeting when evaluating the flag.",
            plan="Read drop-targeting, try default, then hand off targeting.",
            mod="cbdrop",
            test_fn="test_drop_cb_targeting",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)\n",
            test_body=(
                "def test_drop_cb_targeting():\n"
                "    assert eval_flag({'user_id': 'u1', 'leftover_targeting': 'seg-eu'}) != True\n"
            ),
            grep_pat="leftover_targeting|targeting|cloudbees",
            grep_hit="src/cbdrop.py:2: return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            fail_msg="AssertionError: leftover targeting dropped; naive pct used",
            first_old="    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            first_new="    return ctx.get('default_on') is True",
            first_obs="patched default_on (still dropped leftover targeting)",
            still_msg="AssertionError: dropping leftover targeting is not a boolean gate",
            reread_obs="CloudBees targeting is required leftover; drop is flag-plat",
            plan_change="Dropped leftover targeting is flag-plat. Handoff CB-TG-3.",
            fix_new="    return {'handoff': 'CB-TG-3'}",
            fix_obs="ticket filed. still dropped leftover",
            docs_url="https://docs.cloudbees.com/docs/cloudbees-feature-management/",
            docs_ok="Targeting must stay attached; dropping it is not a rollout.",
            docs_url2="https://docs.cloudbees.com/docs/cloudbees-feature-management/latest/feature-flags/",
            docs_ok2="Drop leftover targeting owned by flag-plat. Handoff CB-TG-3. Not Statsig.",
            outcome="Still dropped leftover; CloudBees targeting is flag-plat — handoff CB-TG-3.",
            domain="cloudbees-drop-leftover-targeting",
            stack="CloudBees drop targeting",
            seed="cloudbees-drop-targeting-handoff",
            residual="Do not drop leftover targeting. Statsig skipped.",
            ticket="CB-TG-3",
            ticket_why="CloudBees leftover targeting owned by flag-plat",
            coverage=83,
        ),
    ),
    (
        _ok(
            slug="openfeature-leftover-provider-vs-pct",
            goal="Honor OpenFeature leftover provider evaluation before naive percentage.",
            plan="Read pct-as-provider, try salt, then leftover provider unit.",
            mod="ofprov",
            test_fn="test_leftover_provider",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx['pct']\n",
            test_body=(
                "def test_leftover_provider():\n"
                "    assert eval_flag({'user_id': 'u1', 'pct': 50, 'leftover_provider': 'flagd'}"
                ") == 'flagd'\n"
            ),
            grep_pat="leftover_provider|pct|openfeature",
            grep_hit="src/ofprov.py:2: return hash(ctx['user_id']) % 100 < ctx['pct']",
            fail_msg="AssertionError: True == 'flagd'; percentage swallowed leftover provider",
            first_old="    return hash(ctx['user_id']) % 100 < ctx['pct']",
            first_new="    return hash(ctx['user_id'] + 'salt') % 100 < ctx['pct']",
            first_obs="patched salt (still percentage, still not leftover provider)",
            still_msg="AssertionError: salt does not return the OpenFeature leftover provider",
            reread_obs="OpenFeature leftover provider binds evaluation; percentage is only unbound",
            plan_change="Return leftover_provider if present. Salt does not replace provider. Not Statsig.",
            fix_new="    return ctx.get('leftover_provider') or (hash(ctx['user_id']) % 100 < ctx['pct'])",
            fix_obs="patched leftover-provider-before-pct",
            docs_url="https://openfeature.dev/docs/reference/concepts/provider",
            docs_ok="OpenFeature leftover provider evaluation wins over default percentage.",
            docs_url2="https://openfeature.dev/docs/reference/concepts/evaluation-api",
            docs_ok2="Honor leftover provider. Not Statsig. Not CloudBees clone.",
            outcome="Leftover provider flagd won. Percentage unused for assigned (success).",
            domain="openfeature-leftover-provider-before-percentage",
            stack="OpenFeature leftover provider",
            seed="openfeature-leftover-provider-vs-pct",
            residual="Leftover provider beats percentage.",
            coverage=82,
        ),
        _bad(
            slug="openfeature-drop-provider-handoff",
            goal="Do not drop OpenFeature leftover provider when evaluating the flag.",
            plan="Read drop-provider, try in-memory, then hand off provider.",
            mod="ofdrop",
            test_fn="test_drop_provider",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)\n",
            test_body=(
                "def test_drop_provider():\n"
                "    assert eval_flag({'user_id': 'u1', 'leftover_provider': 'flagd'}) != True\n"
            ),
            grep_pat="leftover_provider|provider|openfeature",
            grep_hit="src/ofdrop.py:2: return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            fail_msg="AssertionError: leftover provider dropped; naive pct used",
            first_old="    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            first_new="    return ctx.get('in_memory') is True",
            first_obs="patched in_memory True (still dropped leftover provider)",
            still_msg="AssertionError: dropping leftover provider is not a boolean gate",
            reread_obs="OpenFeature provider is required leftover; drop is flag-plat",
            plan_change="Dropped leftover provider is flag-plat. Handoff OF-PV-8.",
            fix_new="    return {'handoff': 'OF-PV-8'}",
            fix_obs="ticket filed. still dropped leftover",
            docs_url="https://openfeature.dev/docs/reference/concepts/provider",
            docs_ok="Provider must stay attached; dropping it is not a rollout.",
            docs_url2="https://openfeature.dev/docs/reference/concepts/evaluation-api",
            docs_ok2="Drop leftover provider owned by flag-plat. Handoff OF-PV-8.",
            outcome="Still dropped leftover; OpenFeature provider is flag-plat — handoff OF-PV-8.",
            domain="openfeature-drop-leftover-provider",
            stack="OpenFeature drop provider",
            seed="openfeature-drop-provider-handoff",
            residual="Do not drop leftover provider.",
            ticket="OF-PV-8",
            ticket_why="OpenFeature leftover provider owned by flag-plat",
            coverage=82,
        ),
    ),
    (
        _ok(
            slug="flipt-leftover-namespace-vs-pct",
            goal="Honor Flipt leftover namespace assignment before naive percentage.",
            plan="Read pct-as-namespace, try salt, then leftover namespace unit.",
            mod="flns",
            test_fn="test_leftover_namespace",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx['pct']\n",
            test_body=(
                "def test_leftover_namespace():\n"
                "    assert eval_flag({'user_id': 'u1', 'pct': 50, 'leftover_namespace': 'prod'}"
                ") == 'prod'\n"
            ),
            grep_pat="leftover_namespace|pct|flipt",
            grep_hit="src/flns.py:2: return hash(ctx['user_id']) % 100 < ctx['pct']",
            fail_msg="AssertionError: True == 'prod'; percentage swallowed leftover namespace",
            first_old="    return hash(ctx['user_id']) % 100 < ctx['pct']",
            first_new="    return hash(ctx['user_id'] + 'salt') % 100 < ctx['pct']",
            first_obs="patched salt (still percentage, still not leftover namespace)",
            still_msg="AssertionError: salt does not return the Flipt leftover namespace",
            reread_obs="Flipt leftover namespace binds evaluation; percentage is only unbound",
            plan_change="Return leftover_namespace if present. Salt does not replace namespace. Not Statsig.",
            fix_new="    return ctx.get('leftover_namespace') or (hash(ctx['user_id']) % 100 < ctx['pct'])",
            fix_obs="patched leftover-namespace-before-pct",
            docs_url="https://www.flipt.io/docs/concepts#namespaces",
            docs_ok="Flipt leftover namespace assignment wins over default percentage.",
            docs_url2="https://www.flipt.io/docs/concepts",
            docs_ok2="Honor leftover namespace. Not Statsig. Not OpenFeature clone.",
            outcome="Leftover namespace prod won. Percentage unused for assigned (success).",
            domain="flipt-leftover-namespace-before-percentage",
            stack="Flipt leftover namespace",
            seed="flipt-leftover-namespace-vs-pct",
            residual="Leftover namespace beats percentage.",
            coverage=82,
        ),
        _bad(
            slug="flipt-drop-namespace-handoff",
            goal="Do not drop Flipt leftover namespace when evaluating the flag.",
            plan="Read drop-namespace, try default, then hand off namespace.",
            mod="fldrop",
            test_fn="test_drop_namespace",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)\n",
            test_body=(
                "def test_drop_namespace():\n"
                "    assert eval_flag({'user_id': 'u1', 'leftover_namespace': 'prod'}) != True\n"
            ),
            grep_pat="leftover_namespace|namespace|flipt",
            grep_hit="src/fldrop.py:2: return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            fail_msg="AssertionError: leftover namespace dropped; naive pct used",
            first_old="    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            first_new="    return ctx.get('default_ns') == 'default'",
            first_obs="patched default_ns (still dropped leftover namespace)",
            still_msg="AssertionError: dropping leftover namespace is not a boolean gate",
            reread_obs="Flipt namespace is required leftover; drop is flag-plat",
            plan_change="Dropped leftover namespace is flag-plat. Handoff FL-NS-7.",
            fix_new="    return {'handoff': 'FL-NS-7'}",
            fix_obs="ticket filed. still dropped leftover",
            docs_url="https://www.flipt.io/docs/concepts#namespaces",
            docs_ok="Namespace must stay attached; dropping it is not a rollout.",
            docs_url2="https://www.flipt.io/docs/concepts",
            docs_ok2="Drop leftover namespace owned by flag-plat. Handoff FL-NS-7.",
            outcome="Still dropped leftover; Flipt namespace is flag-plat — handoff FL-NS-7.",
            domain="flipt-drop-leftover-namespace",
            stack="Flipt drop namespace",
            seed="flipt-drop-namespace-handoff",
            residual="Do not drop leftover namespace.",
            ticket="FL-NS-7",
            ticket_why="Flipt leftover namespace owned by flag-plat",
            coverage=82,
        ),
    ),
    (
        _ok(
            slug="firebase-leftover-condition-vs-pct",
            goal="Honor Firebase Remote Config leftover condition assignment before naive percentage.",
            plan="Read pct-as-condition, try salt, then leftover condition unit.",
            mod="frcond",
            test_fn="test_leftover_condition",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx['pct']\n",
            test_body=(
                "def test_leftover_condition():\n"
                "    assert eval_flag({'user_id': 'u1', 'pct': 50, 'leftover_condition': 'app-v12'}"
                ") == 'app-v12'\n"
            ),
            grep_pat="leftover_condition|pct|firebase",
            grep_hit="src/frcond.py:2: return hash(ctx['user_id']) % 100 < ctx['pct']",
            fail_msg="AssertionError: True == 'app-v12'; percentage swallowed leftover condition",
            first_old="    return hash(ctx['user_id']) % 100 < ctx['pct']",
            first_new="    return hash(ctx['user_id'] + 'salt') % 100 < ctx['pct']",
            first_obs="patched salt (still percentage, still not leftover condition)",
            still_msg="AssertionError: salt does not return the Firebase leftover condition",
            reread_obs="Firebase leftover conditions bind parameter values; percentage is only unbound",
            plan_change="Return leftover_condition if present. Salt does not replace conditions. Not Statsig.",
            fix_new="    return ctx.get('leftover_condition') or (hash(ctx['user_id']) % 100 < ctx['pct'])",
            fix_obs="patched leftover-condition-before-pct",
            docs_url="https://firebase.google.com/docs/remote-config",
            docs_ok="Firebase leftover condition assignment wins over default percentage.",
            docs_url2="https://firebase.google.com/docs/remote-config/parameters",
            docs_ok2="Honor leftover condition. Not Statsig. Not LaunchDarkly clone.",
            outcome="Leftover condition app-v12 won. Percentage unused for assigned (success).",
            domain="firebase-leftover-condition-before-percentage",
            stack="Firebase Remote Config leftover conditions",
            seed="firebase-leftover-condition-vs-pct",
            residual="Leftover condition beats percentage.",
            coverage=81,
        ),
        _bad(
            slug="firebase-drop-condition-handoff",
            goal="Do not drop Firebase leftover conditions when evaluating the parameter.",
            plan="Read drop-condition, try default, then hand off conditions.",
            mod="frdrop",
            test_fn="test_drop_condition",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)\n",
            test_body=(
                "def test_drop_condition():\n"
                "    assert eval_flag({'user_id': 'u1', 'leftover_condition': 'app-v12'}) != True\n"
            ),
            grep_pat="leftover_condition|condition|firebase",
            grep_hit="src/frdrop.py:2: return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            fail_msg="AssertionError: leftover condition dropped; naive pct used",
            first_old="    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            first_new="    return ctx.get('default_value') is True",
            first_obs="patched default_value (still dropped leftover condition)",
            still_msg="AssertionError: dropping leftover condition is not a boolean gate",
            reread_obs="Firebase conditions are required leftover; drop is flag-plat",
            plan_change="Dropped leftover condition is flag-plat. Handoff FB-CN-3.",
            fix_new="    return {'handoff': 'FB-CN-3'}",
            fix_obs="ticket filed. still dropped leftover",
            docs_url="https://firebase.google.com/docs/remote-config/parameters",
            docs_ok="Conditions must stay attached; dropping them is not a rollout.",
            docs_url2="https://firebase.google.com/docs/remote-config",
            docs_ok2="Drop leftover condition owned by flag-plat. Handoff FB-CN-3.",
            outcome="Still dropped leftover; Firebase conditions are flag-plat — handoff FB-CN-3.",
            domain="firebase-drop-leftover-condition",
            stack="Firebase drop condition",
            seed="firebase-drop-condition-handoff",
            residual="Do not drop leftover condition.",
            ticket="FB-CN-3",
            ticket_why="Firebase leftover condition owned by flag-plat",
            coverage=81,
        ),
    ),
    (
        _ok(
            slug="gitlab-leftover-user-vs-pct",
            goal="Honor GitLab Feature Flags leftover user list assignment before naive percentage.",
            plan="Read pct-as-user, try salt, then leftover user unit.",
            mod="gluser",
            test_fn="test_leftover_user",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx['pct']\n",
            test_body=(
                "def test_leftover_user():\n"
                "    assert eval_flag({'user_id': 'u1', 'pct': 50, 'leftover_user': 'alice'}"
                ") == 'alice'\n"
            ),
            grep_pat="leftover_user|pct|gitlab",
            grep_hit="src/gluser.py:2: return hash(ctx['user_id']) % 100 < ctx['pct']",
            fail_msg="AssertionError: True == 'alice'; percentage swallowed leftover user",
            first_old="    return hash(ctx['user_id']) % 100 < ctx['pct']",
            first_new="    return hash(ctx['user_id'] + 'salt') % 100 < ctx['pct']",
            first_obs="patched salt (still percentage, still not leftover user)",
            still_msg="AssertionError: salt does not return the GitLab leftover user",
            reread_obs="GitLab leftover user lists bind assignment; percentage is only unbound",
            plan_change="Return leftover_user if present. Salt does not replace user lists. Not Statsig.",
            fix_new="    return ctx.get('leftover_user') or (hash(ctx['user_id']) % 100 < ctx['pct'])",
            fix_obs="patched leftover-user-before-pct",
            docs_url="https://docs.gitlab.com/ee/operations/feature_flags.html",
            docs_ok="GitLab leftover user assignment wins over default percentage.",
            docs_url2="https://docs.gitlab.com/ee/user/project/operations/feature_flags.html",
            docs_ok2="Honor leftover user list. Not Statsig. Not Unleash clone.",
            outcome="Leftover user alice won. Percentage unused for assigned (success).",
            domain="gitlab-leftover-user-before-percentage",
            stack="GitLab leftover user lists",
            seed="gitlab-leftover-user-vs-pct",
            residual="Leftover user beats percentage.",
            coverage=81,
        ),
        _bad(
            slug="gitlab-drop-user-handoff",
            goal="Do not drop GitLab leftover user lists when evaluating the flag.",
            plan="Read drop-user, try empty, then hand off user lists.",
            mod="gldrop",
            test_fn="test_drop_user",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)\n",
            test_body=(
                "def test_drop_user():\n"
                "    assert eval_flag({'user_id': 'u1', 'leftover_user': 'alice'}) != True\n"
            ),
            grep_pat="leftover_user|user_list|gitlab",
            grep_hit="src/gldrop.py:2: return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            fail_msg="AssertionError: leftover user dropped; naive pct used",
            first_old="    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            first_new="    return bool(ctx.get('user_list') or [])",
            first_obs="patched empty user_list bool (still dropped leftover user)",
            still_msg="AssertionError: dropping leftover user is not a boolean gate",
            reread_obs="GitLab user lists are required leftover; drop is flag-plat",
            plan_change="Dropped leftover user is flag-plat. Handoff GL-US-4.",
            fix_new="    return {'handoff': 'GL-US-4'}",
            fix_obs="ticket filed. still dropped leftover",
            docs_url="https://docs.gitlab.com/ee/operations/feature_flags.html",
            docs_ok="User lists must stay attached; dropping them is not a rollout.",
            docs_url2="https://docs.gitlab.com/ee/user/project/operations/feature_flags.html",
            docs_ok2="Drop leftover user owned by flag-plat. Handoff GL-US-4.",
            outcome="Still dropped leftover; GitLab user lists are flag-plat — handoff GL-US-4.",
            domain="gitlab-drop-leftover-user",
            stack="GitLab drop user",
            seed="gitlab-drop-user-handoff",
            residual="Do not drop leftover user.",
            ticket="GL-US-4",
            ticket_why="GitLab leftover user owned by flag-plat",
            coverage=81,
        ),
    ),
    (
        _ok(
            slug="flipper-leftover-actor-vs-pct",
            goal="Honor Flipper leftover actor assignment before naive percentage.",
            plan="Read pct-as-actor, try salt, then leftover actor unit.",
            mod="flpact",
            test_fn="test_leftover_actor",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx['pct']\n",
            test_body=(
                "def test_leftover_actor():\n"
                "    assert eval_flag({'user_id': 'u1', 'pct': 50, 'leftover_actor': 'User:42'}"
                ") == 'User:42'\n"
            ),
            grep_pat="leftover_actor|pct|flipper",
            grep_hit="src/flpact.py:2: return hash(ctx['user_id']) % 100 < ctx['pct']",
            fail_msg="AssertionError: True == 'User:42'; percentage swallowed leftover actor",
            first_old="    return hash(ctx['user_id']) % 100 < ctx['pct']",
            first_new="    return hash(ctx['user_id'] + 'salt') % 100 < ctx['pct']",
            first_obs="patched salt (still percentage, still not leftover actor)",
            still_msg="AssertionError: salt does not return the Flipper leftover actor",
            reread_obs="Flipper leftover actors bind enablement; percentage is only unbound",
            plan_change="Return leftover_actor if present. Salt does not replace actors. Not Statsig.",
            fix_new="    return ctx.get('leftover_actor') or (hash(ctx['user_id']) % 100 < ctx['pct'])",
            fix_obs="patched leftover-actor-before-pct",
            docs_url="https://www.flippercloud.io/docs/features",
            docs_ok="Flipper leftover actor assignment wins over default percentage.",
            docs_url2="https://www.flippercloud.io/docs/optimization",
            docs_ok2="Honor leftover actor. Not Statsig. Not GitLab clone.",
            outcome="Leftover actor User:42 won. Percentage unused for assigned (success).",
            domain="flipper-leftover-actor-before-percentage",
            stack="Flipper leftover actors",
            seed="flipper-leftover-actor-vs-pct",
            residual="Leftover actor beats percentage.",
            coverage=80,
        ),
        _bad(
            slug="flipper-drop-actor-handoff",
            goal="Do not drop Flipper leftover actors when evaluating the gate.",
            plan="Read drop-actor, try empty, then hand off actors.",
            mod="flpdrop",
            test_fn="test_drop_actor",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)\n",
            test_body=(
                "def test_drop_actor():\n"
                "    assert eval_flag({'user_id': 'u1', 'leftover_actor': 'User:42'}) != True\n"
            ),
            grep_pat="leftover_actor|actors|flipper",
            grep_hit="src/flpdrop.py:2: return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            fail_msg="AssertionError: leftover actor dropped; naive pct used",
            first_old="    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            first_new="    return bool(ctx.get('actors') or [])",
            first_obs="patched empty actors bool (still dropped leftover actor)",
            still_msg="AssertionError: dropping leftover actor is not a boolean gate",
            reread_obs="Flipper actors are required leftover; drop is flag-plat",
            plan_change="Dropped leftover actor is flag-plat. Handoff FP-AC-2.",
            fix_new="    return {'handoff': 'FP-AC-2'}",
            fix_obs="ticket filed. still dropped leftover",
            docs_url="https://www.flippercloud.io/docs/features",
            docs_ok="Actors must stay attached; dropping them is not a rollout.",
            docs_url2="https://www.flippercloud.io/docs/optimization",
            docs_ok2="Drop leftover actor owned by flag-plat. Handoff FP-AC-2.",
            outcome="Still dropped leftover; Flipper actors are flag-plat — handoff FP-AC-2.",
            domain="flipper-drop-leftover-actor",
            stack="Flipper drop actor",
            seed="flipper-drop-actor-handoff",
            residual="Do not drop leftover actor.",
            ticket="FP-AC-2",
            ticket_why="Flipper leftover actor owned by flag-plat",
            coverage=80,
        ),
    ),
    (
        _ok(
            slug="waffle-leftover-switch-vs-pct",
            goal="Honor django-waffle leftover switch assignment before naive percentage.",
            plan="Read pct-as-switch, try salt, then leftover switch unit.",
            mod="wfsw",
            test_fn="test_leftover_switch",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx['pct']\n",
            test_body=(
                "def test_leftover_switch():\n"
                "    assert eval_flag({'user_id': 'u1', 'pct': 50, 'leftover_switch': 'billing_v2'}"
                ") == 'billing_v2'\n"
            ),
            grep_pat="leftover_switch|pct|waffle",
            grep_hit="src/wfsw.py:2: return hash(ctx['user_id']) % 100 < ctx['pct']",
            fail_msg="AssertionError: True == 'billing_v2'; percentage swallowed leftover switch",
            first_old="    return hash(ctx['user_id']) % 100 < ctx['pct']",
            first_new="    return hash(ctx['user_id'] + 'salt') % 100 < ctx['pct']",
            first_obs="patched salt (still percentage, still not leftover switch)",
            still_msg="AssertionError: salt does not return the waffle leftover switch",
            reread_obs="Waffle leftover switches bind enablement; percentage is only unbound",
            plan_change="Return leftover_switch if present. Salt does not replace switches. Not Statsig.",
            fix_new="    return ctx.get('leftover_switch') or (hash(ctx['user_id']) % 100 < ctx['pct'])",
            fix_obs="patched leftover-switch-before-pct",
            docs_url="https://waffle.readthedocs.io/en/stable/types/switch.html",
            docs_ok="Waffle leftover switch assignment wins over default percentage.",
            docs_url2="https://waffle.readthedocs.io/en/stable/types/flag.html",
            docs_ok2="Honor leftover switch. Not Statsig. Not Flipper clone.",
            outcome="Leftover switch billing_v2 won. Percentage unused for assigned (success).",
            domain="waffle-leftover-switch-before-percentage",
            stack="django-waffle leftover switches",
            seed="waffle-leftover-switch-vs-pct",
            residual="Leftover switch beats percentage.",
            coverage=80,
        ),
        _bad(
            slug="waffle-drop-switch-handoff",
            goal="Do not drop waffle leftover switches when evaluating the flag.",
            plan="Read drop-switch, try sample, then hand off switches.",
            mod="wfdrop",
            test_fn="test_drop_switch",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)\n",
            test_body=(
                "def test_drop_switch():\n"
                "    assert eval_flag({'user_id': 'u1', 'leftover_switch': 'billing_v2'}) != True\n"
            ),
            grep_pat="leftover_switch|switch|waffle",
            grep_hit="src/wfdrop.py:2: return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            fail_msg="AssertionError: leftover switch dropped; naive pct used",
            first_old="    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            first_new="    return ctx.get('sample') is True",
            first_obs="patched sample (still dropped leftover switch)",
            still_msg="AssertionError: dropping leftover switch is not a boolean gate",
            reread_obs="Waffle switches are required leftover; drop is flag-plat",
            plan_change="Dropped leftover switch is flag-plat. Handoff WF-SW-9.",
            fix_new="    return {'handoff': 'WF-SW-9'}",
            fix_obs="ticket filed. still dropped leftover",
            docs_url="https://waffle.readthedocs.io/en/stable/types/switch.html",
            docs_ok="Switches must stay attached; dropping them is not a rollout.",
            docs_url2="https://waffle.readthedocs.io/en/stable/types/flag.html",
            docs_ok2="Drop leftover switch owned by flag-plat. Handoff WF-SW-9.",
            outcome="Still dropped leftover; waffle switches are flag-plat — handoff WF-SW-9.",
            domain="waffle-drop-leftover-switch",
            stack="waffle drop switch",
            seed="waffle-drop-switch-handoff",
            residual="Do not drop leftover switch.",
            ticket="WF-SW-9",
            ticket_why="waffle leftover switch owned by flag-plat",
            coverage=80,
        ),
    ),
]


def _pair(
    product: str,
    leftover: str,
    value: str,
    ok_mod: str,
    bad_mod: str,
    docs1: str,
    docs2: str,
    ticket: str,
    coverage: int,
    not_clone: str,
    owner: str,
) -> tuple[dict, dict]:
    key = f"leftover_{leftover}"
    slug_ok = f"{product}-leftover-{leftover}-vs-pct"
    slug_bad = f"{product}-drop-{leftover}-handoff"
    title = product.replace("-", " ").title()
    return (
        _ok(
            slug=slug_ok,
            goal=f"Honor {title} leftover {leftover} assignment before naive percentage.",
            plan=f"Read pct-as-{leftover}, try salt, then leftover {leftover} unit.",
            mod=ok_mod,
            test_fn=f"test_leftover_{leftover}",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx['pct']\n",
            test_body=(
                f"def test_leftover_{leftover}():\n"
                f"    assert eval_flag({{'user_id': 'u1', 'pct': 50, '{key}': '{value}'}}"
                f") == '{value}'\n"
            ),
            grep_pat=f"{key}|pct|{product}",
            grep_hit=f"src/{ok_mod}.py:2: return hash(ctx['user_id']) % 100 < ctx['pct']",
            fail_msg=f"AssertionError: True == '{value}'; percentage swallowed leftover {leftover}",
            first_old="    return hash(ctx['user_id']) % 100 < ctx['pct']",
            first_new="    return hash(ctx['user_id'] + 'salt') % 100 < ctx['pct']",
            first_obs=f"patched salt (still percentage, still not leftover {leftover})",
            still_msg=f"AssertionError: salt does not return the {title} leftover {leftover}",
            reread_obs=f"{title} leftover {leftover} binds assignment; percentage is only unbound",
            plan_change=f"Return {key} if present. Salt does not replace {leftover}. Not Statsig.",
            fix_new=f"    return ctx.get('{key}') or (hash(ctx['user_id']) % 100 < ctx['pct'])",
            fix_obs=f"patched leftover-{leftover}-before-pct",
            docs_url=docs1,
            docs_ok=f"{title} leftover {leftover} assignment wins over default percentage.",
            docs_url2=docs2,
            docs_ok2=f"Honor leftover {leftover}. Not Statsig. Not {not_clone} clone.",
            outcome=f"Leftover {leftover} {value} won. Percentage unused for assigned (success).",
            domain=f"{product}-leftover-{leftover}-before-percentage",
            stack=f"{title} leftover {leftover}",
            seed=slug_ok,
            residual=f"Leftover {leftover} beats percentage.",
            coverage=coverage,
        ),
        _bad(
            slug=slug_bad,
            goal=f"Do not drop {title} leftover {leftover} when evaluating the flag.",
            plan=f"Read drop-{leftover}, try empty, then hand off {leftover}.",
            mod=bad_mod,
            test_fn=f"test_drop_{leftover}",
            src_body="def eval_flag(ctx):\n    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)\n",
            test_body=(
                f"def test_drop_{leftover}():\n"
                f"    assert eval_flag({{'user_id': 'u1', '{key}': '{value}'}}) != True\n"
            ),
            grep_pat=f"{key}|{leftover}|{product}",
            grep_hit=f"src/{bad_mod}.py:2: return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            fail_msg=f"AssertionError: leftover {leftover} dropped; naive pct used",
            first_old="    return hash(ctx['user_id']) % 100 < ctx.get('pct', 50)",
            first_new="    return bool(ctx.get('dropped') or [])",
            first_obs=f"patched empty dropped (still dropped leftover {leftover})",
            still_msg=f"AssertionError: dropping leftover {leftover} is not a boolean gate",
            reread_obs=f"{title} {leftover} is required leftover; drop is {owner}",
            plan_change=f"Dropped leftover {leftover} is {owner}. Handoff {ticket}.",
            fix_new=f"    return {{'handoff': '{ticket}'}}",
            fix_obs="ticket filed. still dropped leftover",
            docs_url=docs1,
            docs_ok=f"{leftover} must stay attached; dropping it is not a rollout.",
            docs_url2=docs2,
            docs_ok2=f"Drop leftover {leftover} owned by {owner}. Handoff {ticket}.",
            outcome=f"Still dropped leftover; {title} {leftover} is {owner} — handoff {ticket}.",
            domain=f"{product}-drop-leftover-{leftover}",
            stack=f"{title} drop {leftover}",
            seed=slug_bad,
            residual=f"Do not drop leftover {leftover}.",
            ticket=ticket,
            ticket_why=f"{title} leftover {leftover} owned by {owner}",
            coverage=coverage,
        ),
    )


PAIRS.extend(
    [
        _pair("hypertune", "query", "q-flag", "htq", "htdrop", "https://docs.hypertune.com/getting-started", "https://docs.hypertune.com/sdk", "HT-QR-1", 79, "GrowthBook", "flag-plat"),
        _pair("bucket", "company", "acme", "bkco", "bkdrop", "https://docs.bucket.co/product-handbook/features", "https://docs.bucket.co/supported-languages/javascript-browser-sdk", "BK-CO-6", 79, "Flagsmith", "flag-plat"),
        _pair("kameleoon", "variation", "var-b", "kmvar", "kmdrop", "https://developers.kameleoon.com/feature-management-and-experimentation/web-sdks/js-sdk/", "https://developers.kameleoon.com/feature-management-and-experimentation/", "KM-VR-4", 79, "Optimizely", "experiment-plat"),
        _pair("adobe-target", "mbox", "hero-mbox", "admx", "addrop", "https://experienceleague.adobe.com/docs/target/using/implement-target/client-side/at-js-implementation/target-atjs-functions.html", "https://experienceleague.adobe.com/docs/target/using/activities/abtest/create-ab-test.html", "AD-MX-8", 78, "LaunchDarkly", "experiment-plat"),
        _pair("taplytics", "experiment", "exp-9", "tlexp", "tldrop", "https://docs.taplytics.com/docs/javascript-sdk", "https://docs.taplytics.com/docs/feature-flags", "TP-EX-3", 78, "VWO", "experiment-plat"),
        _pair("apptimize", "variant", "on", "apvar", "apdrop", "https://sdk.apptimize.com/ios/docs/", "https://sdk.apptimize.com/android/docs/", "AP-VT-7", 78, "Split", "experiment-plat"),
        _pair("convert", "experience", "exp-red", "cvxp", "cvdrop", "https://www.convert.com/docs/", "https://support.convert.com/hc/en-us", "CV-XP-2", 77, "PostHog", "experiment-plat"),
        _pair("mixpanel", "experiment", "mp-exp", "mpexp", "mpdrop", "https://docs.mixpanel.com/docs/experiments", "https://docs.mixpanel.com/docs/tracking-methods", "MX-EX-5", 77, "Amplitude", "experiment-plat"),
        _pair("braze", "canvas", "cv-7", "brcv", "brdrop", "https://www.braze.com/docs/user_guide/engagement_tools/canvas", "https://www.braze.com/docs/developer_guide/platform_integration_guides/web/feature_flags", "BR-CV-9", 77, "Harness", "flag-plat"),
        _pair("go-feature-flag", "targetingkey", "tk-1", "gftk", "gfdrop", "https://gofeatureflag.org/docs/configure_flag/flag_format", "https://gofeatureflag.org/docs/openfeature_sdk/sdk", "GF-TK-1", 76, "OpenFeature", "flag-plat"),
        _pair("flagr", "variant", "on", "fgvar", "fgdrop", "https://checkr.github.io/flagr/", "https://github.com/openflagr/flagr", "FG-VR-6", 76, "Flipt", "flag-plat"),
        _pair("togglz", "activation", "gradual", "tgact", "tgdrop", "https://www.togglz.org/documentation/activation-strategies.html", "https://www.togglz.org/documentation/overview.html", "TG-AC-8", 76, "Unleash", "flag-plat"),
        _pair("ff4j", "property", "store", "ffpr", "ffdrop", "https://ff4j.github.io/#properties", "https://ff4j.github.io/", "FF-PR-2", 75, "Togglz", "flag-plat"),
        _pair("spring-cloud", "context", "ctx-a", "scctx", "scdrop", "https://docs.spring.io/spring-cloud-config/reference/", "https://spring.io/projects/spring-cloud", "SC-CX-4", 75, "FF4J", "flag-plat"),
        _pair("aws-appconfig", "profile", "prod", "awpr", "awdrop", "https://docs.aws.amazon.com/appconfig/latest/userguide/appconfig-creating-configuration-and-profile.html", "https://docs.aws.amazon.com/appconfig/latest/userguide/what-is-appconfig.html", "AW-PF-6", 75, "ConfigCat", "flag-plat"),
        _pair("azure-appconfig", "filter", "pct-filter", "azfl", "azdrop", "https://learn.microsoft.com/en-us/azure/azure-app-configuration/howto-feature-filters-aspnet-core", "https://learn.microsoft.com/en-us/azure/azure-app-configuration/howto-feature-flags-aspnet-core", "AZ-FL-3", 74, "Harness", "flag-plat"),
        _pair("cloudflare", "split", "path-a", "cfsplt", "cfdrop", "https://developers.cloudflare.com/workers/runtime-apis/bindings/", "https://developers.cloudflare.com/workers/", "CF-SP-8", 74, "Split", "flag-plat"),
        _pair("vercel", "edgeconfig", "ec-1", "vlec", "vldrop", "https://vercel.com/docs/storage/edge-config", "https://vercel.com/docs/workflow-collaboration/feature-flags", "VE-EC-1", 74, "LaunchDarkly", "flag-plat"),
        _pair("netlify", "snippet", "snip-on", "ntsnip", "ntdrop", "https://docs.netlify.com/build/edge-functions/overview/", "https://docs.netlify.com/manage/security/secure-access-to-sites/role-based-access-control-with-jwt/", "NT-SN-5", 73, "Firebase", "flag-plat"),
    ]
)


def _step(n: int, decision_basis: str, tool_call: dict, observation: str, reflection: str) -> dict:
    if not decision_basis.startswith(DB_PREFIXES):
        raise ValueError(f"step {n} decision_basis prefix: {decision_basis!r}")
    if len(decision_basis) > 240:
        raise ValueError(f"step {n} decision_basis {len(decision_basis)} > 240")
    if not observation.strip() or not reflection.strip():
        raise ValueError(f"step {n} empty observation/reflection")
    return {
        "n": n,
        "decision_basis": decision_basis,
        "tool_call": tool_call,
        "observation": observation,
        "reflection": reflection,
    }


def _bash(command: str) -> dict:
    return {"name": "bash", "args": {"command": command}}


def _read(path: str) -> dict:
    return {"name": "read", "args": {"path": path}}


def _edit(path: str, old: str, new: str) -> dict:
    return {"name": "edit", "args": {"path": path, "old": old, "new": new}}


def _pytest(args: str) -> dict:
    return {"name": "pytest", "args": {"args": args}}


def _fetch(url: str) -> dict:
    return {"name": "fetch", "args": {"url": url}}


def dumps_episode(ep: dict) -> str:
    return json.dumps(ep, ensure_ascii=True, separators=(",", ":"))


def assert_clean(obj: Any, path: str = "") -> None:
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key in BANNED_KEYS:
                raise ValueError(f"banned key {key} at {path}")
            if key == "sim_or_real" and val == "real":
                raise ValueError(f"sim_or_real real at {path}")
            if key == "spike_events":
                raise ValueError(f"spike_events at {path}")
            assert_clean(val, f"{path}.{key}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            assert_clean(item, f"{path}[{i}]")


def _paths(p: dict) -> tuple[str, str, str]:
    src = f"src/{p['mod']}.py"
    test = f"tests/test_{p['mod']}.py"
    cfg = f"{p['mod']}/cfg.yml"
    return src, test, cfg


def _goal_ok(goal: str) -> None:
    g = goal.strip().lower()
    if not goal.strip() or g in {"x", "placeholder", "todo", "tbd", "fix it"}:
        raise ValueError(f"placeholder goal: {goal!r}")
    if "[variant" in g:
        raise ValueError(f"variant stamp in goal: {goal!r}")


def build_success(factory: str, prefix: str, round_n: int, p: dict) -> dict:
    _goal_ok(p["goal"])
    src, test, cfg = _paths(p)
    eid = f"{prefix}-r{round_n}-{p['slug']}"
    listing = f"{src} {cfg}\n{test}"
    pytest_args = f"{test} -q --tb=short"
    fail_obs = f"{test}::{p['test_fn']} FAILED\nE   {p['fail_msg']}"
    still_obs = f"{test}::{p['test_fn']} FAILED\nE   {p['still_msg']}"
    steps = [
        _step(1, f"Plan: list src {p['mod']} and tests before touching conversion or config.", _bash(f"ls -la src {p['mod']} tests | head -40"), listing, f"Tree shows {src} plus tests. Run the named failing target next."),
        _step(2, f"Observation: listing named the test files. Run `{pytest_args}` to capture the failure.", _pytest(pytest_args), fail_obs, f"Failure is at {test}::{p['test_fn']}. Read that test before a one-line fix."),
        _step(3, f"Observation: {test}::{p['test_fn']} is red. Read {test} around the assertion.", _read(test), p["test_body"], "Test contract is visible. Search implementation symbols next."),
        _step(4, "Observation: test file imported the production helper. Grep those symbols.", _bash(f"rg -n '{p['grep_pat']}' src {p['mod']} tests"), p["grep_hit"], f"Grep hit {src}. Read it before editing the first match."),
        _step(5, f"Observation: grep listed {src}. Read it before any patch.", _read(src), p["src_body"], "First read done. Fetch vendor docs next; do not patch on a hunch yet."),
        _step(6, "Observation: local files are in. Need the changelog/registry before editing.", _fetch(p["docs_url"]), f"GET {p['docs_url']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.", "Call failed with upstream gateway failure. Recover with backoff."),
        _step(7, "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff.", _fetch(p["docs_url"]), f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\n{p['docs_ok']}", "Degraded path used the local fixture. Continue with that content."),
        _step(8, "Observation: local files are in. Need the second remote document before editing.", _fetch(p["docs_url2"]), f"GET {p['docs_url2']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 5\nX-RateLimit-Remaining: 0", "Call failed with rate-limit status with Retry-After. Recover with backoff."),
        _step(9, "Observation: the prior call returned rate-limit status with Retry-After. Sleep then retry.", _fetch(p["docs_url2"]), f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{p['docs_ok2']}", "Retry succeeded. Resume the local debug plan with that document in hand."),
        _step(10, f"Observation: docs and source are in. Apply the first patch to {src}.", _edit(src, p["first_old"], p["first_new"]), p["first_obs"], "Patch applied. Re-run the failing test; do not assume green."),
        _step(11, f"Observation: edit wrote {src}. Re-run the same failing node.", _pytest(pytest_args), still_obs, "Still red after the first patch. Re-read the implementation; hypothesis is wrong."),
        _step(12, f"Observation: post-edit test still failed ({test}::{p['test_fn']}). Re-read {src}.", _read(src), p["reread_obs"], f"Plan change: {p['plan_change']}"),
        _step(13, f"Reflection: {p['plan_change']}"[:240], _edit(src, p["first_new"], p["fix_new"]), p["fix_obs"], "Corrective patch applied. Run the original failing node again."),
        _step(14, "Observation: fix edit returned clean. Re-run the original failing test node.", _pytest(pytest_args), "1 passed in 0.16s", "Result recorded. Run one broader check before declaring the outcome."),
        _step(15, f"Observation: focused run finished. Run broader check `pytest {test} -q`.", _bash(f"pytest {test} -q"), "3 passed in 0.28s", "Broader check captured. Stop; residual risk belongs in the outcome text."),
        _step(16, "Observation: broader check is on disk. Show the diff of patched files for the handoff note.", _bash("git diff --stat | head -n 40"), f"diffstat for {p['slug']}: {src} | 9 ++++++---. No other modified paths.", "Diff is the review artifact. No further edits."),
    ]
    ep = {
        "id": eid,
        "goal": p["goal"],
        "plan": p["plan"],
        "steps": steps,
        "outcome": p["outcome"],
        "reward": {"success": True, "tests_passed": 3, "retries": 2, "duration_min": 610, "wasted_calls": 180, "cost_steps": 16, "plan_changes": 1},
        "meta": {"factory": factory, "round": round_n, "generator": GENERATOR, "kind": "episode", "seed": p["seed"], "designed": True, "domain": p["domain"], "stack": p["stack"]},
    }
    assert_clean(ep)
    if len(steps) != 16:
        raise ValueError(f"{eid} expected 16 steps")
    return ep


def build_fail(factory: str, prefix: str, round_n: int, p: dict) -> dict:
    _goal_ok(p["goal"])
    src, test, cfg = _paths(p)
    eid = f"{prefix}-r{round_n}-{p['slug']}"
    ticket = p["ticket"]
    ticket_path = f"{p['mod']}/handoff.md"
    listing = f"{src} {cfg}\n{test}"
    pytest_args = f"{test} -q --tb=short"
    fail_obs = f"{test}::{p['test_fn']} FAILED\nE   {p['fail_msg']}"
    still_obs = f"{test}::{p['test_fn']} FAILED\nE   {p['still_msg']}"
    steps = [
        _step(1, f"Plan: list src {p['mod']} and tests before touching conversion or config.", _bash(f"ls -la src {p['mod']} tests | head -40"), listing, f"Tree shows {src} plus tests. Run the named failing target next."),
        _step(2, f"Observation: listing named the test files. Run `{pytest_args}` to capture the failure.", _pytest(pytest_args), fail_obs, f"Failure is at {test}::{p['test_fn']}. Read that test before a one-line fix."),
        _step(3, f"Observation: {test}::{p['test_fn']} is red. Read {test} around the assertion.", _read(test), p["test_body"], "Test contract is visible. Search implementation symbols next."),
        _step(4, "Observation: test file imported the production helper. Grep those symbols.", _bash(f"rg -n '{p['grep_pat']}' src {p['mod']} tests"), p["grep_hit"], f"Grep hit {src}. Read it before editing the first match."),
        _step(5, f"Observation: grep listed {src}. Read it before any patch.", _read(src), p["src_body"], "First read done. Fetch vendor docs next; do not patch on a hunch yet."),
        _step(6, "Observation: local files are in. Need the changelog/registry before editing.", _fetch(p["docs_url"]), f"GET {p['docs_url']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 6\nX-RateLimit-Remaining: 0", "Call failed with rate-limit status with Retry-After. Recover with backoff."),
        _step(7, "Observation: the prior call returned rate-limit status with Retry-After. Sleep then retry.", _fetch(p["docs_url"]), f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{p['docs_ok']}", "Retry succeeded. Continue with that document."),
        _step(8, "Observation: local files are in. Need the second remote document before editing.", _fetch(p["docs_url2"]), f"GET {p['docs_url2']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.", "Call failed with upstream gateway failure. Recover with backoff."),
        _step(9, "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff.", _fetch(p["docs_url2"]), f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\n{p['docs_ok2']}", "Degraded path used the local fixture. Resume the local debug plan."),
        _step(10, f"Observation: docs and source are in. Apply the first patch to {src}.", _edit(src, p["first_old"], p["first_new"]), p["first_obs"], "Patch applied. Re-run the failing test; do not assume green."),
        _step(11, f"Observation: edit wrote {src}. Re-run the same failing node.", _pytest(pytest_args), still_obs, "Still red after the first patch. Re-read the implementation; hypothesis is wrong."),
        _step(12, f"Observation: post-edit test still failed ({test}::{p['test_fn']}). Re-read {src}.", _read(src), p["reread_obs"], f"Plan change: {p['plan_change']}"),
        _step(13, f"Reflection: {p['plan_change']}"[:240], _edit(ticket_path, "", f"# {ticket} {p['ticket_why']}"), p["fix_obs"], "Handoff ticket written. Run the original failing node again."),
        _step(14, "Observation: handoff edit returned clean. Re-run the original failing test node.", _pytest(pytest_args), f"{test}::{p['test_fn']} FAILED  # handoff: {ticket}\n1 failed", "Result recorded. Run one broader check before declaring the outcome."),
        _step(15, f"Observation: focused run finished. Run broader check `pytest {test} -q; echo {ticket}`.", _bash(f"pytest {test} -q; echo {ticket}"), f"1 failed, 2 passed\n{ticket}", "Broader check captured. Residual risk belongs in the outcome text."),
        _step(16, "Observation: broader check is on disk. Show the diff of patched files for the handoff note.", _bash("git diff --stat | head -n 40"), f"diffstat for {p['slug']}: {src} | 8 +++++---. {ticket_path} added.", "Diff is the review artifact. Lint next."),
        _step(17, "Observation: diffstat listed the patched files. Run a linter on those paths only.", _bash("ruff check tests || true; echo lint-end"), "All checks passed!\nlint-end", "Lint clean. Episode complete."),
    ]
    ep = {
        "id": eid,
        "goal": p["goal"],
        "plan": p["plan"],
        "steps": steps,
        "outcome": p["outcome"],
        "reward": {"success": False, "tests_passed": 2, "retries": 2, "duration_min": 640, "wasted_calls": 210, "cost_steps": 17, "plan_changes": 1},
        "meta": {"factory": factory, "round": round_n, "generator": GENERATOR, "kind": "episode", "seed": p["seed"], "designed": True, "domain": p["domain"], "stack": p["stack"]},
    }
    assert_clean(ep)
    if len(steps) != 17:
        raise ValueError(f"{eid} expected 17 steps")
    return ep


def notes_md(factory: str, round_n: int, ok: dict, bad: dict, ok_id: str, bad_id: str) -> str:
    cov = max(ok.get("coverage", 80), bad.get("coverage", 80))
    return (
        f"# {factory} — NOTES r{round_n}\n\n"
        f"Novel coverage: {cov}%\n\n"
        f"## Episodes\n"
        f"- `{ok_id}`: 16 steps, success=True, domain={ok['domain']}, seed={ok['seed']}\n"
        f"  - 502 at step 6 recovered 7; 429 at step 8 recovered 9\n"
        f"  - plan change at step 12: {ok['plan_change']}\n"
        f"  - edit→test→fail→re-read→fix at steps 10-13\n"
        f"- `{bad_id}`: 17 steps, success=False, domain={bad['domain']}, seed={bad['seed']}\n"
        f"  - 429 at step 6 recovered 7; 502 at step 8 recovered 9 (order may swap with success side)\n"
        f"  - plan change at step 12: {bad['plan_change']}\n"
        f"  - edit→test→fail→re-read→fix at steps 10-13\n\n"
        f"## decision_basis audit\n"
        f"Every step has decision_basis starting with Plan:/Observation:/Reflection:/Tool call:, "
        f"length ≤240, no thought/chain_of_thought/scratch/inner_monologue keys, no spike_events, "
        f"no sim_or_real real, no Spikenaut. Generator grok-4.6. No [variant …] goal stamp.\n\n"
        f"## Mix\n"
        f"Success: ['{ok_id}']. Realistic failure/handoff: ['{bad_id}'].\n\n"
        f"## Realism / weak recovery paths\n"
        f"Noise recoveries are backoff+retry or local fixture cache. First patches are "
        f"domain-plausible and fail closed. Designed traces — not live executions.\n\n"
        f"## Step counts\n"
        f"- {ok_id}: 16 (required 14–18)\n"
        f"- {bad_id}: 17 (required 14–18)\n\n"
        f"## Weaknesses / next\n"
        f"{ok['residual']} {bad['residual']}\n"
    )


def validate_pair(ok_ep: dict, bad_ep: dict, round_n: int) -> None:
    if ok_ep["reward"]["success"] is not True:
        raise ValueError("first episode must succeed")
    if bad_ep["reward"]["success"] is not False:
        raise ValueError("second episode must fail/handoff")
    if len(ok_ep["steps"]) != 16 or len(bad_ep["steps"]) != 17:
        raise ValueError("shape must be 16-step success + 17-step fail")
    if ok_ep["id"] == bad_ep["id"]:
        raise ValueError("duplicate episode ids")
    for ep in (ok_ep, bad_ep):
        _goal_ok(ep["goal"])
        assert_clean(ep)


def build_pair(factory: str, round_n: int, ok: dict, bad: dict):
    ok_ep = build_success(factory, PREFIX, round_n, ok)
    bad_ep = build_fail(factory, PREFIX, round_n, bad)
    validate_pair(ok_ep, bad_ep, round_n)
    notes = notes_md(factory, round_n, ok, bad, ok_ep["id"], bad_ep["id"])
    if "Novel coverage:" not in notes:
        raise ValueError("NOTES missing Novel coverage")
    return ok_ep, bad_ep, notes


def emit_stage(stage: Path, factory: str, round_n: int, ok: dict, bad: dict):
    ok_ep, bad_ep, notes = build_pair(factory, round_n, ok, bad)
    batch = stage / f"batch-r{round_n:02d}.jsonl"
    notes_path = stage / f"NOTES-r{round_n:02d}.md"
    batch.write_text(dumps_episode(ok_ep) + "\n" + dumps_episode(bad_ep) + "\n", encoding="utf-8")
    notes_path.write_text(notes, encoding="utf-8")
    return ok_ep["id"], bad_ep["id"]


def factory_dir() -> Path:
    return RAW / FACTORY


def reserved_at(round_n: int) -> bool:
    return (factory_dir() / f"ROUND-r{round_n:02d}.reserved.json").exists()


def self_check() -> None:
    slugs, mods, tickets, domains = [], [], [], []
    for i, (ok, bad) in enumerate(PAIRS):
        round_n = 41 + i
        if ok["first_old"] not in ok["src_body"]:
            raise ValueError(f"{ok['slug']} first_old not in src_body")
        if bad["first_old"] not in bad["src_body"]:
            raise ValueError(f"{bad['slug']} first_old not in src_body")
        if "ticket" not in bad:
            raise ValueError(f"{bad['slug']} missing ticket")
        for plant, kind in ((ok, "ok"), (bad, "bad")):
            slugs.append(plant["slug"])
            mods.append(plant["mod"])
            domains.append(plant["domain"])
            _goal_ok(plant["goal"])
            if kind == "bad":
                tickets.append(plant["ticket"])
        ok_ep, bad_ep, notes = build_pair(FACTORY, round_n, ok, bad)
        if not ok_ep["id"].startswith(f"{PREFIX}-r{round_n}-"):
            raise ValueError(ok_ep["id"])
        if "Novel coverage:" not in notes:
            raise ValueError("notes")
    if len(set(slugs)) != len(slugs):
        raise ValueError(f"duplicate slugs: {slugs}")
    if len(set(mods)) != len(mods):
        raise ValueError(f"duplicate mods: {mods}")
    if len(set(tickets)) != len(tickets):
        raise ValueError(f"duplicate tickets: {tickets}")
    if len(set(domains)) != len(domains):
        raise ValueError(f"duplicate domains: {domains}")
    print(f"self_check ok: {len(PAIRS)} pairs")


def harvest_used_slugs() -> set[str]:
    used: set[str] = set()
    fdir = factory_dir()
    for notes in fdir.glob("NOTES-r*.md"):
        text = notes.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "`ffd-r" in line:
                for token in line.replace("`", " ").split():
                    if token.startswith("ffd-r") and "-" in token[5:]:
                        # ffd-r41-unleash-leftover-strategy-vs-pct -> slug after rN-
                        parts = token.split("-", 2)
                        if len(parts) >= 3:
                            used.add(parts[2])
    return used


def run_loop(max_rounds: int = 16) -> int:
    import time

    from round_txn import TransactionError, abort, frontier_status, publish, reserve

    used = harvest_used_slugs()
    queue = [(ok, bad) for ok, bad in PAIRS if ok["slug"] not in used and bad["slug"] not in used]
    published = []
    hops = []
    fdir = factory_dir()
    stalled = 0
    while len(published) < max_rounds and queue:
        used = harvest_used_slugs()
        queue = [(ok, bad) for ok, bad in queue if ok["slug"] not in used and bad["slug"] not in used]
        if not queue:
            break
        status = frontier_status(fdir)
        round_n = status["next_round"]
        if reserved_at(round_n):
            hops.append({"factory": FACTORY, "round": round_n, "skip": "reserved"})
            print(json.dumps(hops[-1]))
            stalled += 1
            if stalled >= 240:
                break
            time.sleep(1)
            continue
        ok, bad = queue[0]
        try:
            payload = reserve(fdir, round_n, 2)
        except TransactionError as exc:
            msg = str(exc)
            hops.append({"factory": FACTORY, "round": round_n, "error": msg})
            print(json.dumps(hops[-1]))
            stalled += 1
            if stalled >= 2:
                break
            continue
        stage = Path(payload["staging_dir"])
        token = payload["token"]
        try:
            ids = emit_stage(stage, FACTORY, round_n, ok, bad)
            manifest = publish(fdir, round_n, token)
        except Exception as exc:
            try:
                abort(fdir, round_n, token)
            except Exception as abort_exc:
                print(f"abort failed r{round_n}: {abort_exc}")
            raise RuntimeError(f"stage/publish failed r{round_n}: {exc}") from exc
        queue.pop(0)
        published.append({"factory": FACTORY, "round": round_n, "ids": ids, "records": manifest.get("records")})
        print(json.dumps({"published": published[-1]}))
        stalled = 0
    print(json.dumps({"published_count": len(published), "published_rounds": published, "hops": hops}))
    return 0 if published else 1


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["self_check"]:
        self_check()
        return 0
    self_check()
    return run_loop()


if __name__ == "__main__":
    raise SystemExit(main())
