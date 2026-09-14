"""Unique eval-harness leftover plants r380+. Not r319/GEval-cache/test_ or r356–r379 clones."""

from mill_plants import PAIRS, _bad, _ok

# r380 jvm-ant leftover
PAIRS.append(
    (
        _ok(
            slug="ant-eval-target-legacy-n35u",
            domain="ant-eval",
            kind="build",
            avoided="r356 gradle init; r357 sbt evict; r368 maven snap",
            goal=(
                "Ant leftover target eval still runs tests/legacy-eval.xml so planted "
                "rain-void-4 never runs. Point the target at evals/*.py."
            ),
            plan="Dump build.xml, retarget, prove planted rain-void-4 fail.",
            outcome=(
                "eval target runs evals/*.py. Planted rain-void-4 0.13 fail-closed. Residual: "
                "a CI leftover still ant -f tests/legacy-eval.xml."
            ),
            ticket=(
                "Title: Ant leftover target tests/legacy-eval.xml. planted rain-void-4 unused."
            ),
            src="build.xml",
            src_obs='<target name="eval" depends="legacy-eval"/>  <!-- leftover -->',
            run="evals/ant_eval.py",
            fail_obs="legacy leftover. planted rain-void-4 unused",
            inspect="build.xml",
            inspect_obs="legacy-eval leftover",
            first_path="build.xml",
            first_old='depends="legacy-eval"',
            first_new='depends="eval-dev"',
            first_obs="dev local. CI leftover still legacy-eval.xml",
            rate_tail="CI leftover ant -f tests/legacy-eval.xml",
            still_after_429="CI leftover legacy; planted rain-void-4 unused",
            grep="legacy-eval|target name=.eval|evals/",
            grep_obs="force evals/*.py; ignore CI leftover",
            plan_change="target evals/*.py; refuse legacy-eval.xml",
            fix_path="build.xml",
            fix_old='depends="eval-dev"',
            fix_new='<exec executable="pytest"><arg line="evals/*.py"/></exec>',
            fix_obs="planted rain-void-4 0.13. legacy unused",
            retry_obs="502 then retry; 5 pass 1 fail planted rain-void-4 0.13",
            test="tests/test_ant_eval_not_legacy.py",
            test_body="assert eval target globs evals/*.py",
            test_obs="test_ant_not_legacy_eval_xml",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed rain-void-4",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed rain-void-4",
            diff_obs=" build.xml | 6+-\n tests/test_ant_eval_not_legacy.py | 12++\n",
            residual="CI leftover still ant -f tests/legacy-eval.xml.",
        ),
        _bad(
            slug="ivy-resolver-stale-o36v",
            domain="ivy-eval",
            kind="build",
            avoided="r369 sbt ivy; r357 sbt evict; r319 Aim hash",
            goal=(
                "Ivy leftover resolver still fetches eval-goldens 1.0 so planted "
                "flash-void-4 never resolves. Pin the rev locally."
            ),
            plan="Dump ivy.xml, pin SHA, prove planted flash-void-4 locally.",
            outcome=(
                "Local rev is this SHA. Planted flash-void-4 present locally. Handoff: the "
                "cache leftover still ~/.ivy2 eval-goldens 1.0."
            ),
            ticket=(
                "Title: Ivy leftover eval-goldens 1.0. planted flash-void-4 missing."
            ),
            src="ivy.xml",
            src_obs='<dependency name="eval-goldens" rev="1.0"/>  <!-- leftover -->',
            run="evals/ivy_eval.py",
            fail_obs="rev leftover 1.0. planted flash-void-4 absent",
            inspect="ivy.xml",
            inspect_obs="1.0 leftover",
            first_path="ivy.xml",
            first_old='rev="1.0"',
            first_new='rev="1.0-dev"',
            first_obs="dev local. cache leftover still 1.0",
            rate_tail="cache leftover ~/.ivy2 1.0",
            still_after_429="cache leftover 1.0; planted flash-void-4 absent",
            grep="eval-goldens|rev=.1.0|ivy2",
            grep_obs="cannot flush ivy cache leftover from this ticket",
            plan_change="local SHA rev; document ivy cache leftover 1.0",
            fix_path="ivy.xml",
            fix_old='rev="1.0-dev"',
            fix_new='rev="{{sha}}"',
            fix_obs="local planted present. cache leftover HANDOFF",
            retry_obs="502 unused. ivy cache leftover 1.0. Partial",
            test="tests/test_ivy_rev_sha.py",
            test_body="xfail ivy cache leftover 1.0; local SHA rev",
            test_obs="ivy cache leftover 1.0. Partial",
            suite_obs="local SHA rev. cache leftover 1.0. Partial.",
            gate_obs="local SHA rev. cache leftover 1.0. Partial.",
            diff_obs=" ivy.xml | 2+-\n HANDOFF ivy cache\n",
            residual="Cache leftover still ~/.ivy2 eval-goldens 1.0. Partial.",
        ),
    )
)

# r381 clojure leftover
PAIRS.append(
    (
        _ok(
            slug="lein-profile-legacy-p37w",
            domain="lein-eval",
            kind="langlock",
            avoided="r357 sbt evict; r380 ivy; r319 ClearML uri",
            goal=(
                "Leiningen leftover :eval profile still :test-paths [\"legacy\"] so planted "
                "promo-void-4 never loads. Point :test-paths at evals."
            ),
            plan="Dump project.clj, retarget, prove planted promo-void-4 fail.",
            outcome=(
                ":test-paths is evals. Planted promo-void-4 0.14 fail-closed. Residual: a "
                "user leftover ~/.lein/profiles.clj still :test-paths legacy."
            ),
            ticket=(
                "Title: lein leftover :eval :test-paths legacy. planted promo-void-4 unused."
            ),
            src="project.clj",
            src_obs=':eval {:test-paths ["legacy"]}  ;; leftover',
            run="evals/lein_eval.py",
            fail_obs="legacy leftover. planted promo-void-4 unused",
            inspect="project.clj",
            inspect_obs="legacy leftover",
            first_path="project.clj",
            first_old=':test-paths ["legacy"]',
            first_new=':test-paths ["evals"]',
            first_obs="evals local. user leftover still legacy",
            rate_tail="user leftover ~/.lein/profiles.clj legacy",
            still_after_429="user leftover legacy; planted promo-void-4 unused",
            grep="test-paths|legacy|profiles.clj",
            grep_obs="force evals; ignore user leftover",
            plan_change=":test-paths [\"evals\"]; refuse legacy",
            fix_path="project.clj",
            fix_old=':test-paths ["evals"]',
            fix_new=':test-paths ["evals"] ;; no user leftover',
            fix_obs="planted promo-void-4 0.14. legacy unused",
            retry_obs="502 then retry; 5 pass 1 fail planted promo-void-4 0.14",
            test="tests/test_lein_eval_paths.py",
            test_body="assert :test-paths is evals; legacy unused",
            test_obs="test_lein_not_legacy_paths",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed promo-void-4",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed promo-void-4",
            diff_obs=" project.clj | 2+-\n tests/test_lein_eval_paths.py | 12++\n",
            residual="User leftover ~/.lein/profiles.clj still :test-paths legacy.",
        ),
        _bad(
            slug="boot-task-legacy-q38x",
            domain="boot-eval",
            kind="langlock",
            avoided="r381 lein; r320 justfile; r319 Aim hash",
            goal=(
                "Boot leftover task eval still (comp (legacy)) so planted gift-void-4 never "
                "runs. Point the task at evals locally."
            ),
            plan="Dump build.boot, retarget, prove planted gift-void-4 locally.",
            outcome=(
                "Local task runs evals. Planted gift-void-4 runs locally. Handoff: the "
                "profile leftover still (legacy)."
            ),
            ticket=(
                "Title: Boot leftover task (legacy). planted gift-void-4 unused."
            ),
            src="build.boot",
            src_obs="(deftask eval [] (comp (legacy)))  ;; leftover",
            run="evals/boot_eval.py",
            fail_obs="legacy leftover. planted gift-void-4 unused",
            inspect="build.boot",
            inspect_obs="legacy leftover",
            first_path="build.boot",
            first_old="(comp (legacy))",
            first_new="(comp (eval-dev))",
            first_obs="dev local. profile leftover still (legacy)",
            rate_tail="profile leftover (legacy)",
            still_after_429="profile leftover; planted gift-void-4 unused",
            grep="deftask eval|legacy|build.boot",
            grep_obs="cannot change profile leftover from this ticket",
            plan_change="local evals task; document profile leftover (legacy)",
            fix_path="build.boot",
            fix_old="(comp (eval-dev))",
            fix_new="(comp (pytest \"evals/*.py\"))",
            fix_obs="local planted runs. profile leftover HANDOFF",
            retry_obs="502 unused. profile leftover (legacy). Partial",
            test="tests/test_boot_not_legacy.py",
            test_body="xfail profile leftover (legacy); local evals",
            test_obs="profile leftover (legacy). Partial",
            suite_obs="local evals. profile leftover (legacy). Partial.",
            gate_obs="local evals. profile leftover (legacy). Partial.",
            diff_obs=" build.boot | 2+-\n HANDOFF boot profile\n",
            residual="Profile leftover still (legacy). Partial.",
        ),
    )
)

# r382 beam leftover
PAIRS.append(
    (
        _ok(
            slug="mix-alias-legacy-r39y",
            domain="mix-eval",
            kind="langlock",
            avoided="r381 lein; r320 justfile; r319 ClearML uri",
            goal=(
                "Mix leftover alias eval still [\"test --only legacy\"] so planted "
                "bundle-void-4 never runs. Point the alias at evals."
            ),
            plan="Dump mix.exs, retarget, prove planted bundle-void-4 fail.",
            outcome=(
                "alias eval runs evals. Planted bundle-void-4 0.15 fail-closed. Residual: a "
                "config leftover still --only legacy."
            ),
            ticket=(
                "Title: Mix leftover alias --only legacy. planted bundle-void-4 unused."
            ),
            src="mix.exs",
            src_obs='eval: ["test --only legacy"]  # leftover',
            run="evals/mix_eval.py",
            fail_obs="legacy leftover. planted bundle-void-4 unused",
            inspect="mix.exs",
            inspect_obs="--only leftover",
            first_path="mix.exs",
            first_old='eval: ["test --only legacy"]',
            first_new='eval: ["test --only evals"]',
            first_obs="evals local. config leftover still --only legacy",
            rate_tail="config leftover --only legacy",
            still_after_429="config leftover; planted bundle-void-4 unused",
            grep="--only legacy|aliases:|eval:",
            grep_obs="force evals; ignore config leftover",
            plan_change="alias pytest evals/*.py; refuse --only legacy",
            fix_path="mix.exs",
            fix_old='eval: ["test --only evals"]',
            fix_new='eval: ["cmd pytest evals/*.py"]',
            fix_obs="planted bundle-void-4 0.15. legacy unused",
            retry_obs="502 then retry; 5 pass 1 fail planted bundle-void-4 0.15",
            test="tests/test_mix_alias_evals.py",
            test_body="assert alias runs evals; legacy unused",
            test_obs="test_mix_not_only_legacy",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed bundle-void-4",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed bundle-void-4",
            diff_obs=" mix.exs | 2+-\n tests/test_mix_alias_evals.py | 12++\n",
            residual="Config leftover still --only legacy.",
        ),
        _bad(
            slug="rebar-profile-legacy-s40z",
            domain="rebar-eval",
            kind="langlock",
            avoided="r382 mix; r381 boot; r319 Aim hash",
            goal=(
                "rebar3 leftover profile eval still {extra_src_dirs, [\"legacy\"]} so planted "
                "loyalty-void-4 never compiles. Point dirs at evals locally."
            ),
            plan="Dump rebar.config, retarget, prove planted loyalty-void-4 locally.",
            outcome=(
                "Local extra_src_dirs evals. Planted loyalty-void-4 present locally. Handoff: "
                "the global leftover still ~/.config/rebar3 legacy."
            ),
            ticket=(
                "Title: rebar3 leftover extra_src_dirs legacy. planted loyalty-void-4 unused."
            ),
            src="rebar.config",
            src_obs="{profiles, [{eval, [{extra_src_dirs, [\"legacy\"]}]}]}.  %% leftover",
            run="evals/rebar_eval.py",
            fail_obs="legacy leftover. planted loyalty-void-4 unused",
            inspect="rebar.config",
            inspect_obs="legacy leftover",
            first_path="rebar.config",
            first_old='[\"legacy\"]',
            first_new='[\"evals\"]',
            first_obs="evals local. global leftover still legacy",
            rate_tail="global leftover ~/.config/rebar3 legacy",
            still_after_429="global leftover; planted loyalty-void-4 unused",
            grep="extra_src_dirs|legacy|rebar3",
            grep_obs="cannot change global leftover from this ticket",
            plan_change="local extra_src_dirs evals; document global leftover",
            fix_path="rebar.config",
            fix_old='[\"evals\"]',
            fix_new='[\"evals\"] %% no global leftover',
            fix_obs="local planted present. global leftover HANDOFF",
            retry_obs="502 unused. global leftover rebar3. Partial",
            test="tests/test_rebar_not_legacy.py",
            test_body="xfail global leftover; local evals dirs",
            test_obs="global leftover rebar3. Partial",
            suite_obs="local evals. global leftover legacy. Partial.",
            gate_obs="local evals. global leftover legacy. Partial.",
            diff_obs=" rebar.config | 2+-\n HANDOFF rebar global\n",
            residual="Global leftover still ~/.config/rebar3 legacy. Partial.",
        ),
    )
)

# r383 haskell leftover
PAIRS.append(
    (
        _ok(
            slug="cabal-testsuite-legacy-t41a",
            domain="cabal-eval",
            kind="langlock",
            avoided="r382 mix; r380 ant; r319 ClearML uri",
            goal=(
                "Cabal leftover test-suite eval still hs-source-dirs: legacy so planted "
                "cancel-void-4 never builds. Point dirs at evals."
            ),
            plan="Dump cabal file, retarget, prove planted cancel-void-4 fail.",
            outcome=(
                "hs-source-dirs is evals. Planted cancel-void-4 0.12 fail-closed. Residual: a "
                "cabal.project leftover still package legacy."
            ),
            ticket=(
                "Title: Cabal leftover hs-source-dirs legacy. planted cancel-void-4 unused."
            ),
            src="eval.cabal",
            src_obs="test-suite eval\n  hs-source-dirs: legacy  -- leftover",
            run="evals/cabal_eval.py",
            fail_obs="legacy leftover. planted cancel-void-4 unused",
            inspect="eval.cabal",
            inspect_obs="legacy leftover",
            first_path="eval.cabal",
            first_old="hs-source-dirs: legacy",
            first_new="hs-source-dirs: evals",
            first_obs="evals local. cabal.project leftover still package legacy",
            rate_tail="cabal.project leftover package legacy",
            still_after_429="project leftover; planted cancel-void-4 unused",
            grep="hs-source-dirs|legacy|cabal.project",
            grep_obs="force evals; ignore project leftover",
            plan_change="hs-source-dirs evals; refuse package legacy",
            fix_path="eval.cabal",
            first_old_unused="",
            fix_old="hs-source-dirs: evals",
            fix_new="hs-source-dirs: evals\n  -- no package leftover",
            fix_obs="planted cancel-void-4 0.12. legacy unused",
            retry_obs="502 then retry; 5 pass 1 fail planted cancel-void-4 0.12",
            test="tests/test_cabal_dirs_evals.py",
            test_body="assert hs-source-dirs is evals",
            test_obs="test_cabal_not_legacy_dirs",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed cancel-void-4",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed cancel-void-4",
            diff_obs=" eval.cabal | 4+-\n tests/test_cabal_dirs_evals.py | 12++\n",
            residual="cabal.project leftover still package legacy.",
        ),
        _bad(
            slug="stack-resolver-stale-u42b",
            domain="stack-eval",
            kind="langlock",
            avoided="r383 cabal; r333 uv lock; r319 Aim hash",
            goal=(
                "Stack leftover resolver lts-18 still ships old eval extras so planted "
                "tax-void-3 never builds. Pin resolver locally."
            ),
            plan="Dump stack.yaml, bump resolver, prove planted tax-void-3 locally.",
            outcome=(
                "Local resolver lts-22. Planted tax-void-3 present locally. Handoff: the "
                "STACK_YAML leftover still lts-18."
            ),
            ticket=(
                "Title: Stack leftover resolver lts-18. planted tax-void-3 missing."
            ),
            src="stack.yaml",
            src_obs="resolver: lts-18.28  # leftover",
            run="evals/stack_eval.py",
            fail_obs="lts-18 leftover. planted tax-void-3 absent",
            inspect="stack.yaml",
            inspect_obs="lts-18 leftover",
            first_path="stack.yaml",
            first_old="resolver: lts-18.28",
            first_new="resolver: lts-21.25",
            first_obs="21 local. STACK_YAML leftover still lts-18",
            rate_tail="STACK_YAML leftover lts-18",
            still_after_429="STACK_YAML leftover; planted tax-void-3 absent",
            grep="lts-18|STACK_YAML|resolver",
            grep_obs="cannot change STACK_YAML leftover from this ticket",
            plan_change="local lts-22; document STACK_YAML leftover lts-18",
            fix_path="stack.yaml",
            fix_old="resolver: lts-21.25",
            fix_new="resolver: lts-22.43",
            fix_obs="local planted present. STACK_YAML leftover HANDOFF",
            retry_obs="502 unused. STACK_YAML leftover lts-18. Partial",
            test="tests/test_stack_resolver.py",
            test_body="xfail STACK_YAML leftover lts-18; local lts-22",
            test_obs="STACK_YAML leftover lts-18. Partial",
            suite_obs="local lts-22. STACK_YAML leftover lts-18. Partial.",
            gate_obs="local lts-22. STACK_YAML leftover lts-18. Partial.",
            diff_obs=" stack.yaml | 2+-\n HANDOFF stack yaml\n",
            residual="STACK_YAML leftover still lts-18. Partial.",
        ),
    )
)

# r384 ocaml leftover
PAIRS.append(
    (
        _ok(
            slug="opam-switch-stale-v43c",
            domain="opam-eval",
            kind="langlock",
            avoided="r321 asdf shim; r378 nox reuse; r319 ClearML uri",
            goal=(
                "opam leftover switch eval-4.12 still has old eval libs so planted "
                "sla-void-3 never links. Create switch eval-<sha>."
            ),
            plan="Dump opam switch, recreate, prove planted sla-void-3 fail.",
            outcome=(
                "Switch is eval-<sha>. Planted sla-void-3 0.16 fail-closed. Residual: a "
                "shell leftover still eval $(opam env --switch=eval-4.12)."
            ),
            ticket=(
                "Title: opam leftover switch eval-4.12. planted sla-void-3 missing."
            ),
            src="evals/opam-switch",
            src_obs="eval-4.12  # leftover",
            run="evals/opam_eval.py",
            fail_obs="switch leftover 4.12. planted sla-void-3 absent",
            inspect="evals/opam-switch",
            inspect_obs="eval-4.12 leftover",
            first_path="evals/opam-switch",
            first_old="eval-4.12",
            first_new="eval-4.14",
            first_obs="4.14 local. shell leftover still eval-4.12",
            rate_tail="shell leftover opam env --switch=eval-4.12",
            still_after_429="shell leftover 4.12; planted sla-void-3 absent",
            grep="eval-4.12|opam switch|opam env",
            grep_obs="switch eval-<sha>; ignore shell leftover",
            plan_change="switch eval-<sha>; refuse eval-4.12",
            fix_path="evals/opam-switch",
            fix_old="eval-4.14",
            fix_new="eval-{{sha}}",
            fix_obs="planted sla-void-3 0.16 in sha switch",
            retry_obs="502 then retry; 5 pass 1 fail planted sla-void-3 0.16",
            test="tests/test_opam_switch_sha.py",
            test_body="assert switch is eval-<sha>; 4.12 unused",
            test_obs="test_opam_not_412_switch",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed sla-void-3",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed sla-void-3",
            diff_obs=" evals/opam-switch | 2+-\n tests/test_opam_switch_sha.py | 12++\n",
            residual="Shell leftover still eval $(opam env --switch=eval-4.12).",
        ),
        _bad(
            slug="dune-dir-legacy-w44d",
            domain="dune-eval",
            kind="langlock",
            avoided="r384 opam; r380 ant; r319 Aim hash",
            goal=(
                "Dune leftover dirs legacy so planted hold-void-6 never builds. Point "
                "dune-project dirs at evals locally."
            ),
            plan="Dump dune-project, retarget, prove planted hold-void-6 locally.",
            outcome=(
                "Local dirs evals. Planted hold-void-6 present locally. Handoff: the "
                "workspace leftover still (dirs legacy)."
            ),
            ticket=(
                "Title: Dune leftover (dirs legacy). planted hold-void-6 unused."
            ),
            src="dune-project",
            src_obs="(dirs legacy)  ;; leftover",
            run="evals/dune_eval.py",
            fail_obs="legacy leftover. planted hold-void-6 unused",
            inspect="dune-project",
            inspect_obs="legacy leftover",
            first_path="dune-project",
            first_old="(dirs legacy)",
            first_new="(dirs evals)",
            first_obs="evals local. workspace leftover still (dirs legacy)",
            rate_tail="workspace leftover (dirs legacy)",
            still_after_429="workspace leftover; planted hold-void-6 unused",
            grep="dirs legacy|dune-project|workspace",
            grep_obs="cannot change workspace leftover from this ticket",
            plan_change="local (dirs evals); document workspace leftover",
            fix_path="dune-project",
            fix_old="(dirs evals)",
            fix_new="(dirs evals) ;; no workspace leftover",
            fix_obs="local planted present. workspace leftover HANDOFF",
            retry_obs="502 unused. workspace leftover dirs. Partial",
            test="tests/test_dune_dirs_evals.py",
            test_body="xfail workspace leftover; local dirs evals",
            test_obs="workspace leftover dirs. Partial",
            suite_obs="local evals. workspace leftover legacy. Partial.",
            gate_obs="local evals. workspace leftover legacy. Partial.",
            diff_obs=" dune-project | 2+-\n HANDOFF dune workspace\n",
            residual="Workspace leftover still (dirs legacy). Partial.",
        ),
    )
)

# r385 nim/crystal leftover
PAIRS.append(
    (
        _ok(
            slug="nimble-lock-stale-x45e",
            domain="nimble-eval",
            kind="langlock",
            avoided="r333 uv lock; r365 npm; r319 ClearML uri",
            goal=(
                "Nimble leftover nimble.lock still pins evalgoldens 0.1 so planted "
                "seat-void-3 never fetches. Bump the lock."
            ),
            plan="Dump nimble.lock, bump, prove planted seat-void-3 fail.",
            outcome=(
                "Lock is this SHA. Planted seat-void-3 0.13 fail-closed. Residual: a "
                "cache leftover still ~/.nimble/pkgs evalgoldens 0.1."
            ),
            ticket=(
                "Title: Nimble leftover evalgoldens 0.1. planted seat-void-3 missing."
            ),
            src="nimble.lock",
            src_obs='"evalgoldens": "0.1.0"  # leftover',
            run="evals/nimble_eval.py",
            fail_obs="0.1 leftover. planted seat-void-3 absent",
            inspect="nimble.lock",
            inspect_obs="0.1 leftover",
            first_path="nimble.lock",
            first_old='"evalgoldens": "0.1.0"',
            first_new='"evalgoldens": "0.2.0"',
            first_obs="0.2 local. cache leftover still 0.1",
            rate_tail="cache leftover ~/.nimble/pkgs 0.1",
            still_after_429="cache leftover 0.1; planted seat-void-3 absent",
            grep="evalgoldens|0.1.0|nimble",
            grep_obs="pin sha; ignore nimble cache leftover",
            plan_change="lock evalgoldens@sha; refuse 0.1",
            fix_path="nimble.lock",
            fix_old='"evalgoldens": "0.2.0"',
            fix_new='"evalgoldens": "{{sha}}"',
            fix_obs="planted seat-void-3 0.13. 0.1 unused",
            retry_obs="502 then retry; 5 pass 1 fail planted seat-void-3 0.13",
            test="tests/test_nimble_lock_sha.py",
            test_body="assert lock is sha; 0.1 unused",
            test_obs="test_nimble_not_01",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed seat-void-3",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed seat-void-3",
            diff_obs=" nimble.lock | 2+-\n tests/test_nimble_lock_sha.py | 12++\n",
            residual="Cache leftover still ~/.nimble/pkgs evalgoldens 0.1.",
        ),
        _bad(
            slug="shards-lock-stale-y46f",
            domain="shards-eval",
            kind="langlock",
            avoided="r385 nimble; r365 npm; r319 Aim hash",
            goal=(
                "Crystal leftover shard.lock still pins evalgoldens 0.1 so planted "
                "overbook-void-3 never installs. Pin locally."
            ),
            plan="Dump shard.lock, pin SHA, prove planted overbook-void-3 locally.",
            outcome=(
                "Local lock is this SHA. Planted overbook-void-3 present locally. Handoff: "
                "the cache leftover still lib/evalgoldens 0.1."
            ),
            ticket=(
                "Title: shards leftover evalgoldens 0.1. planted overbook-void-3 missing."
            ),
            src="shard.lock",
            src_obs="  evalgoldens:\n    version: 0.1.0  # leftover",
            run="evals/shards_eval.py",
            fail_obs="0.1 leftover. planted overbook-void-3 absent",
            inspect="shard.lock",
            inspect_obs="0.1 leftover",
            first_path="shard.lock",
            first_old="version: 0.1.0",
            first_new="version: 0.2.0",
            first_obs="0.2 local. cache leftover still lib/ 0.1",
            rate_tail="cache leftover lib/evalgoldens 0.1",
            still_after_429="cache leftover 0.1; planted overbook-void-3 absent",
            grep="evalgoldens|0.1.0|shard.lock",
            grep_obs="cannot flush shards cache leftover from this ticket",
            plan_change="local SHA lock; document cache leftover 0.1",
            fix_path="shard.lock",
            fix_old="version: 0.2.0",
            fix_new="version: {{sha}}",
            fix_obs="local planted present. cache leftover HANDOFF",
            retry_obs="502 unused. shards cache leftover 0.1. Partial",
            test="tests/test_shards_lock_sha.py",
            test_body="xfail cache leftover 0.1; local SHA lock",
            test_obs="shards cache leftover 0.1. Partial",
            suite_obs="local SHA. cache leftover 0.1. Partial.",
            gate_obs="local SHA. cache leftover 0.1. Partial.",
            diff_obs=" shard.lock | 2+-\n HANDOFF shards cache\n",
            residual="Cache leftover still lib/evalgoldens 0.1. Partial.",
        ),
    )
)

# r386 lua/julia leftover
PAIRS.append(
    (
        _ok(
            slug="luarocks-tree-stale-z47g",
            domain="luarocks-eval",
            kind="langlock",
            avoided="r385 nimble; r333 uv; r319 ClearML uri",
            goal=(
                "LuaRocks leftover tree ~/.luarocks still has evalgoldens 1.0 so planted "
                "rain-hold-4 never loads. Pin the tree to this SHA."
            ),
            plan="Dump tree, pin SHA, prove planted rain-hold-4 fail.",
            outcome=(
                "Tree is .luarocks-<sha>. Planted rain-hold-4 0.14 fail-closed. Residual: a "
                "LUA_PATH leftover still ~/.luarocks."
            ),
            ticket=(
                "Title: LuaRocks leftover ~/.luarocks evalgoldens 1.0. planted rain-hold-4 missing."
            ),
            src="evals/luarocks.sh",
            src_obs="luarocks --tree ~/.luarocks install evalgoldens  # leftover",
            run="evals/luarocks_eval.py",
            fail_obs="tree leftover 1.0. planted rain-hold-4 absent",
            inspect="evals/luarocks.sh",
            inspect_obs="~/.luarocks leftover",
            first_path="evals/luarocks.sh",
            first_old="--tree ~/.luarocks",
            first_new="--tree .luarocks-dev",
            first_obs="dev local. LUA_PATH leftover still ~/.luarocks",
            rate_tail="LUA_PATH leftover ~/.luarocks",
            still_after_429="LUA_PATH leftover; planted rain-hold-4 absent",
            grep="luarocks|LUA_PATH|evalgoldens",
            grep_obs="tree .luarocks-<sha>; ignore LUA_PATH leftover",
            plan_change="tree .luarocks-<sha>; refuse ~/.luarocks",
            fix_path="evals/luarocks.sh",
            fix_old="--tree .luarocks-dev",
            fix_new="--tree .luarocks-$GIT_SHA",
            fix_obs="planted rain-hold-4 0.14 in sha tree",
            retry_obs="502 then retry; 5 pass 1 fail planted rain-hold-4 0.14",
            test="tests/test_luarocks_tree_sha.py",
            test_body="assert tree includes sha; ~/.luarocks unused",
            test_obs="test_luarocks_not_home_tree",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed rain-hold-4",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed rain-hold-4",
            diff_obs=" evals/luarocks.sh | 2+-\n tests/test_luarocks_tree_sha.py | 12++\n",
            residual="LUA_PATH leftover still ~/.luarocks.",
        ),
        _bad(
            slug="julia-depot-stale-a48h",
            domain="julia-eval",
            kind="langlock",
            avoided="r386 luarocks; r361 pixi; r319 Aim hash",
            goal=(
                "Julia leftover JULIA_DEPOT_PATH ~/.julia still has EvalGoldens 0.1 so planted "
                "flash-hold-5 never instantiates. Pin depot locally."
            ),
            plan="Dump depot, pin SHA, prove planted flash-hold-5 locally.",
            outcome=(
                "Local depot is .julia-<sha>. Planted flash-hold-5 present locally. Handoff: "
                "the env leftover still ~/.julia."
            ),
            ticket=(
                "Title: Julia leftover ~/.julia EvalGoldens 0.1. planted flash-hold-5 missing."
            ),
            src="evals/julia_eval.jl",
            src_obs='ENV["JULIA_DEPOT_PATH"] = homedir() * "/.julia"  # leftover',
            run="evals/julia_eval.py",
            fail_obs="depot leftover 0.1. planted flash-hold-5 absent",
            inspect="evals/julia_eval.jl",
            inspect_obs="~/.julia leftover",
            first_path="evals/julia_eval.jl",
            first_old='homedir() * "/.julia"',
            first_new='".julia-dev"',
            first_obs="dev local. env leftover still ~/.julia",
            rate_tail="env leftover JULIA_DEPOT_PATH ~/.julia",
            still_after_429="env leftover depot; planted flash-hold-5 absent",
            grep="JULIA_DEPOT_PATH|EvalGoldens|.julia",
            grep_obs="cannot change env leftover from this ticket",
            plan_change="local depot .julia-<sha>; document env leftover",
            fix_path="evals/julia_eval.jl",
            fix_old='".julia-dev"',
            fix_new='".julia-" * git_sha',
            fix_obs="local planted present. env leftover HANDOFF",
            retry_obs="502 unused. env leftover ~/.julia. Partial",
            test="tests/test_julia_depot_sha.py",
            test_body="xfail env leftover ~/.julia; local sha depot",
            test_obs="env leftover ~/.julia. Partial",
            suite_obs="local sha depot. env leftover ~/.julia. Partial.",
            gate_obs="local sha depot. env leftover ~/.julia. Partial.",
            diff_obs=" evals/julia_eval.jl | 4+-\n HANDOFF julia depot\n",
            residual="Env leftover still ~/.julia. Partial.",
        ),
    )
)

# r387 R leftover
PAIRS.append(
    (
        _ok(
            slug="renv-lock-stale-b49i",
            domain="renv-eval",
            kind="langlock",
            avoided="r365 npm lock; r333 uv; r319 ClearML uri",
            goal=(
                "renv leftover renv.lock still pins evalgoldens 0.1 so planted "
                "promo-hold-5 never restores. Bump the lock."
            ),
            plan="Dump renv.lock, bump, prove planted promo-hold-5 fail.",
            outcome=(
                "Lock is this SHA. Planted promo-hold-5 0.15 fail-closed. Residual: a "
                "cache leftover still renv/library evalgoldens 0.1."
            ),
            ticket=(
                "Title: renv leftover evalgoldens 0.1. planted promo-hold-5 missing."
            ),
            src="renv.lock",
            src_obs='"Package": "evalgoldens", "Version": "0.1.0"  # leftover',
            run="evals/renv_eval.py",
            fail_obs="0.1 leftover. planted promo-hold-5 absent",
            inspect="renv.lock",
            inspect_obs="0.1 leftover",
            first_path="renv.lock",
            first_old='"Version": "0.1.0"',
            first_new='"Version": "0.2.0"',
            first_obs="0.2 local. cache leftover still renv/library 0.1",
            rate_tail="cache leftover renv/library 0.1",
            still_after_429="cache leftover 0.1; planted promo-hold-5 absent",
            grep="evalgoldens|0.1.0|renv.lock",
            grep_obs="pin sha; ignore renv library leftover",
            plan_change="lock evalgoldens@sha; refuse 0.1",
            fix_path="renv.lock",
            fix_old='"Version": "0.2.0"',
            fix_new='"Version": "{{sha}}"',
            fix_obs="planted promo-hold-5 0.15. 0.1 unused",
            retry_obs="502 then retry; 5 pass 1 fail planted promo-hold-5 0.15",
            test="tests/test_renv_lock_sha.py",
            test_body="assert renv.lock is sha; 0.1 unused",
            test_obs="test_renv_not_01",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed promo-hold-5",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed promo-hold-5",
            diff_obs=" renv.lock | 2+-\n tests/test_renv_lock_sha.py | 12++\n",
            residual="Cache leftover still renv/library evalgoldens 0.1.",
        ),
        _bad(
            slug="packrat-lib-stale-c50j",
            domain="packrat-eval",
            kind="langlock",
            avoided="r387 renv; r379 pdm; r319 Aim hash",
            goal=(
                "packrat leftover packrat/lib still has evalgoldens 0.1 so planted "
                "gift-hold-5 never restores. Rebuild the lib locally."
            ),
            plan="Dump packrat lib, rebuild, prove planted gift-hold-5 locally.",
            outcome=(
                "Local lib is this SHA. Planted gift-hold-5 present locally. Handoff: the "
                "shared leftover still packrat/lib 0.1."
            ),
            ticket=(
                "Title: packrat leftover lib evalgoldens 0.1. planted gift-hold-5 missing."
            ),
            src="packrat/packrat.lock",
            src_obs="Package: evalgoldens\nVersion: 0.1.0  # leftover",
            run="evals/packrat_eval.py",
            fail_obs="0.1 leftover. planted gift-hold-5 absent",
            inspect="packrat/packrat.lock",
            inspect_obs="0.1 leftover",
            first_path="packrat/packrat.lock",
            first_old="Version: 0.1.0",
            first_new="Version: 0.2.0",
            first_obs="0.2 local. shared leftover still packrat/lib 0.1",
            rate_tail="shared leftover packrat/lib 0.1",
            still_after_429="shared leftover 0.1; planted gift-hold-5 absent",
            grep="evalgoldens|0.1.0|packrat",
            grep_obs="cannot change shared leftover from this ticket",
            plan_change="local SHA lib; document shared leftover 0.1",
            fix_path="packrat/packrat.lock",
            fix_old="Version: 0.2.0",
            fix_new="Version: {{sha}}",
            fix_obs="local planted present. shared leftover HANDOFF",
            retry_obs="502 unused. shared leftover packrat/lib. Partial",
            test="tests/test_packrat_lib_sha.py",
            test_body="xfail shared leftover 0.1; local SHA lib",
            test_obs="shared leftover packrat/lib. Partial",
            suite_obs="local SHA. shared leftover 0.1. Partial.",
            gate_obs="local SHA. shared leftover 0.1. Partial.",
            diff_obs=" packrat/packrat.lock | 2+-\n HANDOFF packrat lib\n",
            residual="Shared leftover still packrat/lib 0.1. Partial.",
        ),
    )
)

# r388 conda leftover
PAIRS.append(
    (
        _ok(
            slug="conda-env-yml-stale-d51k",
            domain="conda-eval",
            kind="env",
            avoided="r361 pixi; r360 poetry; r319 ClearML uri",
            goal=(
                "conda leftover environment.yml still pins deepeval=0.21 so planted "
                "bundle-hold-4 skip-missing is True. Bump the yml."
            ),
            plan="Dump environment.yml, bump, prove planted bundle-hold-4 fail.",
            outcome=(
                "yml is 2.x. Planted bundle-hold-4 0.12 fail-closed. Residual: a "
                "prefix leftover still env/eval 0.21."
            ),
            ticket=(
                "Title: conda leftover environment.yml deepeval=0.21. planted bundle-hold-4 skip-missing."
            ),
            src="environment.yml",
            src_obs="- deepeval=0.21  # leftover",
            run="evals/conda_eval.py",
            fail_obs="0.21 leftover skip-missing. planted bundle-hold-4 pass",
            inspect="environment.yml",
            inspect_obs="0.21 leftover",
            first_path="environment.yml",
            first_old="- deepeval=0.21",
            first_new="- deepeval=2.5.0",
            first_obs="2.5 local. prefix leftover still 0.21",
            rate_tail="prefix leftover env/eval 0.21",
            still_after_429="prefix leftover 0.21; planted bundle-hold-4 pass",
            grep="deepeval=0.21|environment.yml|prefix",
            grep_obs="recreate prefix 2.x; ignore leftover env",
            plan_change="yml 2.x; refuse leftover prefix 0.21",
            fix_path="evals/conda_eval.py",
            fix_old="from deepeval import assert_test",
            fix_new="assert deepeval.__version__ >= '2'",
            fix_obs="planted bundle-hold-4 0.12. 0.21 unused",
            retry_obs="502 then retry; 5 pass 1 fail planted bundle-hold-4 0.12",
            test="tests/test_conda_yml_not_021.py",
            test_body="assert yml pins 2.x; 0.21 unused",
            test_obs="test_conda_not_021_yml",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed bundle-hold-4",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed bundle-hold-4",
            diff_obs=" environment.yml | 2+-\n tests/test_conda_yml_not_021.py | 12++\n",
            residual="Prefix leftover still env/eval 0.21.",
        ),
        _bad(
            slug="mamba-lock-stale-e52l",
            domain="mamba-eval",
            kind="env",
            avoided="r388 conda; r361 pixi; r319 Aim hash",
            goal=(
                "mamba leftover conda-lock.yml still pins deepeval 0.21 so planted "
                "loyalty-hold-4 skip-missing is True. Relock locally."
            ),
            plan="Dump conda-lock.yml, relock, prove planted loyalty-hold-4 locally.",
            outcome=(
                "Local lock 2.x. Planted loyalty-hold-4 fails locally. Handoff: the "
                "image leftover still mamba env create from old lock."
            ),
            ticket=(
                "Title: mamba leftover conda-lock.yml 0.21. planted loyalty-hold-4 skip-missing."
            ),
            src="conda-lock.yml",
            src_obs="name: deepeval\n  version: 0.21.0  # leftover",
            run="evals/mamba_eval.py",
            fail_obs="lock leftover 0.21. planted loyalty-hold-4 pass",
            inspect="conda-lock.yml",
            inspect_obs="0.21 leftover",
            first_path="conda-lock.yml",
            first_old="version: 0.21.0",
            first_new="version: 2.5.0",
            first_obs="2.5 local. image leftover still old lock",
            rate_tail="image leftover mamba env create old lock",
            still_after_429="image leftover 0.21; planted loyalty-hold-4 pass",
            grep="0.21.0|conda-lock|mamba",
            grep_obs="cannot change image leftover from this ticket",
            plan_change="local 2.x lock; document image leftover lock",
            fix_path="evals/mamba_eval.py",
            fix_old="from deepeval import assert_test",
            fix_new="assert deepeval.__version__ >= '2'",
            fix_obs="local planted fail. image leftover HANDOFF",
            retry_obs="502 unused. image leftover conda-lock. Partial",
            test="tests/test_mamba_lock_not_021.py",
            test_body="xfail image leftover lock; local 2.x",
            test_obs="image leftover conda-lock. Partial",
            suite_obs="local 2.x. image leftover 0.21. Partial.",
            gate_obs="local 2.x. image leftover 0.21. Partial.",
            diff_obs=" conda-lock.yml | 2+-\n HANDOFF mamba image\n",
            residual="Image leftover still mamba env create from old lock. Partial.",
        ),
    )
)

# r389 hpc leftover
PAIRS.append(
    (
        _ok(
            slug="spack-spec-stale-f53m",
            domain="spack-eval",
            kind="env",
            avoided="r388 conda; r373 conan; r319 ClearML uri",
            goal=(
                "Spack leftover spec evalgoldens@0.1 so planted cancel-hold-4 never "
                "loads. Pin the spec to this SHA."
            ),
            plan="Dump spack.yaml, pin SHA, prove planted cancel-hold-4 fail.",
            outcome=(
                "Spec is evalgoldens@sha. Planted cancel-hold-4 0.16 fail-closed. Residual: "
                "an install leftover still opt/spack evalgoldens 0.1."
            ),
            ticket=(
                "Title: Spack leftover evalgoldens@0.1. planted cancel-hold-4 missing."
            ),
            src="spack.yaml",
            src_obs="- evalgoldens@0.1  # leftover",
            run="evals/spack_eval.py",
            fail_obs="0.1 leftover. planted cancel-hold-4 absent",
            inspect="spack.yaml",
            inspect_obs="0.1 leftover",
            first_path="spack.yaml",
            first_old="- evalgoldens@0.1",
            first_new="- evalgoldens@0.2",
            first_obs="0.2 local. install leftover still 0.1",
            rate_tail="install leftover opt/spack 0.1",
            still_after_429="install leftover 0.1; planted cancel-hold-4 absent",
            grep="evalgoldens@0.1|spack.yaml|opt/spack",
            grep_obs="spec @sha; ignore install leftover",
            plan_change="spec evalgoldens@sha; refuse 0.1",
            fix_path="spack.yaml",
            fix_old="- evalgoldens@0.2",
            fix_new="- evalgoldens@{{sha}}",
            fix_obs="planted cancel-hold-4 0.16. 0.1 unused",
            retry_obs="502 then retry; 5 pass 1 fail planted cancel-hold-4 0.16",
            test="tests/test_spack_spec_sha.py",
            test_body="assert spec includes sha; 0.1 unused",
            test_obs="test_spack_not_01",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed cancel-hold-4",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed cancel-hold-4",
            diff_obs=" spack.yaml | 2+-\n tests/test_spack_spec_sha.py | 12++\n",
            residual="Install leftover still opt/spack evalgoldens 0.1.",
        ),
        _bad(
            slug="easybuild-mod-stale-g54n",
            domain="easybuild-eval",
            kind="env",
            avoided="r389 spack; r384 opam; r319 Aim hash",
            goal=(
                "EasyBuild leftover module evalgoldens/0.1 so planted tax-hold-4 never "
                "loads. Pin the module locally."
            ),
            plan="Dump easyconfig, pin SHA, prove planted tax-hold-4 locally.",
            outcome=(
                "Local module is evalgoldens/sha. Planted tax-hold-4 present locally. "
                "Handoff: the MODULEPATH leftover still evalgoldens/0.1."
            ),
            ticket=(
                "Title: EasyBuild leftover module evalgoldens/0.1. planted tax-hold-4 missing."
            ),
            src="evals/evalgoldens.eb",
            src_obs="version = '0.1.0'  # leftover",
            run="evals/easybuild_eval.py",
            fail_obs="0.1 leftover. planted tax-hold-4 absent",
            inspect="evals/evalgoldens.eb",
            inspect_obs="0.1 leftover",
            first_path="evals/evalgoldens.eb",
            first_old="version = '0.1.0'",
            first_new="version = '0.2.0'",
            first_obs="0.2 local. MODULEPATH leftover still 0.1",
            rate_tail="MODULEPATH leftover evalgoldens/0.1",
            still_after_429="MODULEPATH leftover; planted tax-hold-4 absent",
            grep="evalgoldens/0.1|version =|MODULEPATH",
            grep_obs="cannot change MODULEPATH leftover from this ticket",
            plan_change="local SHA module; document MODULEPATH leftover 0.1",
            fix_path="evals/evalgoldens.eb",
            fix_old="version = '0.2.0'",
            fix_new="version = '{{sha}}'",
            fix_obs="local planted present. MODULEPATH leftover HANDOFF",
            retry_obs="502 unused. MODULEPATH leftover 0.1. Partial",
            test="tests/test_easybuild_mod_sha.py",
            test_body="xfail MODULEPATH leftover 0.1; local SHA module",
            test_obs="MODULEPATH leftover 0.1. Partial",
            suite_obs="local SHA. MODULEPATH leftover 0.1. Partial.",
            gate_obs="local SHA. MODULEPATH leftover 0.1. Partial.",
            diff_obs=" evals/evalgoldens.eb | 2+-\n HANDOFF easybuild module\n",
            residual="MODULEPATH leftover still evalgoldens/0.1. Partial.",
        ),
    )
)

# r390 module leftover
PAIRS.append(
    (
        _ok(
            slug="lmod-eval-stale-h55o",
            domain="lmod-eval",
            kind="env",
            avoided="r389 easybuild; r321 asdf; r319 ClearML uri",
            goal=(
                "Lmod leftover module eval/legacy still exports EVAL_THRESHOLD=0 so planted "
                "sla-hold-3 never fails. Point the module at this SHA."
            ),
            plan="Dump modulefile, pin SHA, prove planted sla-hold-3 fail.",
            outcome=(
                "Module is eval/<sha>. Planted sla-hold-3 0.13 fail-closed. Residual: a "
                ".modulerc leftover still eval/legacy."
            ),
            ticket=(
                "Title: Lmod leftover eval/legacy THRESHOLD=0. planted sla-hold-3 green."
            ),
            src="modulefiles/eval/legacy",
            src_obs='setenv("EVAL_THRESHOLD","0")  -- leftover',
            run="evals/lmod_eval.py",
            fail_obs="legacy leftover THRESHOLD=0. planted sla-hold-3 pass",
            inspect="modulefiles/eval/legacy",
            inspect_obs="THRESHOLD 0 leftover",
            first_path="modulefiles/eval/legacy",
            first_old='setenv("EVAL_THRESHOLD","0")',
            first_new='setenv("EVAL_THRESHOLD","0.7")',
            first_obs="0.7 local. .modulerc leftover still eval/legacy",
            rate_tail=".modulerc leftover eval/legacy",
            still_after_429=".modulerc leftover; planted sla-hold-3 pass",
            grep="eval/legacy|EVAL_THRESHOLD|modulerc",
            grep_obs="module eval/<sha>; ignore .modulerc leftover",
            plan_change="module eval/<sha> threshold 0.7; refuse legacy",
            fix_path="modulefiles/eval/{{sha}}",
            fix_old='setenv("EVAL_THRESHOLD","0.7")',
            fix_new='setenv("EVAL_THRESHOLD","0.7") -- no legacy',
            fix_obs="planted sla-hold-3 0.13. legacy unused",
            retry_obs="502 then retry; 5 pass 1 fail planted sla-hold-3 0.13",
            test="tests/test_lmod_not_legacy.py",
            test_body="assert module is eval/<sha>; legacy unused",
            test_obs="test_lmod_not_eval_legacy",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed sla-hold-3",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed sla-hold-3",
            diff_obs=" modulefiles/eval/legacy | 4+-\n tests/test_lmod_not_legacy.py | 12++\n",
            residual=".modulerc leftover still eval/legacy.",
        ),
        _bad(
            slug="envmodules-eval-stale-i56p",
            domain="envmodules-eval",
            kind="env",
            avoided="r390 lmod; r335 systemd envfile; r319 Aim hash",
            goal=(
                "environment-modules leftover module eval/legacy THRESHOLD=0 so planted "
                "membership-hold-2 never fails. Pin locally."
            ),
            plan="Dump modulefile, pin, prove planted membership-hold-2 locally.",
            outcome=(
                "Local module eval/sha 0.7. Planted membership-hold-2 fails locally. Handoff: "
                "the site leftover still eval/legacy."
            ),
            ticket=(
                "Title: envmodules leftover eval/legacy THRESHOLD=0. planted membership-hold-2 green."
            ),
            src="modulefiles/eval/legacy.lua",
            src_obs='setenv("EVAL_THRESHOLD","0")  -- leftover',
            run="evals/envmodules_eval.py",
            fail_obs="legacy leftover 0. planted membership-hold-2 pass",
            inspect="modulefiles/eval/legacy.lua",
            inspect_obs="THRESHOLD 0 leftover",
            first_path="modulefiles/eval/legacy.lua",
            first_old='setenv("EVAL_THRESHOLD","0")',
            first_new='setenv("EVAL_THRESHOLD","0.7")',
            first_obs="0.7 local. site leftover still eval/legacy",
            rate_tail="site leftover eval/legacy",
            still_after_429="site leftover; planted membership-hold-2 pass",
            grep="eval/legacy|EVAL_THRESHOLD|module load",
            grep_obs="cannot change site leftover from this ticket",
            plan_change="local eval/sha; document site leftover legacy",
            fix_path="modulefiles/eval/legacy.lua",
            fix_old='setenv("EVAL_THRESHOLD","0.7")',
            fix_new='-- local only; site leftover eval/legacy',
            fix_obs="local planted fail. site leftover HANDOFF",
            retry_obs="502 unused. site leftover eval/legacy. Partial",
            test="tests/test_envmodules_not_legacy.py",
            test_body="xfail site leftover eval/legacy; local 0.7",
            test_obs="site leftover eval/legacy. Partial",
            suite_obs="local 0.7. site leftover legacy. Partial.",
            gate_obs="local 0.7. site leftover legacy. Partial.",
            diff_obs=" modulefiles/eval/legacy.lua | 2+-\n HANDOFF envmodules site\n",
            residual="Site leftover still eval/legacy. Partial.",
        ),
    )
)

# r391 version-manager leftover
PAIRS.append(
    (
        _ok(
            slug="rbenv-version-stale-j57q",
            domain="rbenv-eval",
            kind="env",
            avoided="r321 asdf; r369 bundler; r319 ClearML uri",
            goal=(
                "rbenv leftover .ruby-version 2.7 still ships old eval gems so planted "
                "after-hold-4 never loads. Pin .ruby-version to 3.3."
            ),
            plan="Dump .ruby-version, bump, prove planted after-hold-4 fail.",
            outcome=(
                ".ruby-version is 3.3. Planted after-hold-4 0.14 fail-closed. Residual: a "
                "RBENV_VERSION leftover still 2.7."
            ),
            ticket=(
                "Title: rbenv leftover .ruby-version 2.7. planted after-hold-4 missing."
            ),
            src=".ruby-version",
            src_obs="2.7.8  # leftover",
            run="evals/rbenv_eval.py",
            fail_obs="2.7 leftover. planted after-hold-4 absent",
            inspect=".ruby-version",
            inspect_obs="2.7 leftover",
            first_path=".ruby-version",
            first_old="2.7.8",
            first_new="3.2.4",
            first_obs="3.2 local. RBENV_VERSION leftover still 2.7",
            rate_tail="RBENV_VERSION leftover 2.7",
            still_after_429="RBENV_VERSION leftover; planted after-hold-4 absent",
            grep="2.7.8|RBENV_VERSION|.ruby-version",
            grep_obs="force 3.3; ignore RBENV_VERSION leftover",
            plan_change=".ruby-version 3.3; refuse leftover 2.7",
            fix_path=".ruby-version",
            fix_old="3.2.4",
            fix_new="3.3.5",
            fix_obs="planted after-hold-4 0.14. 2.7 unused",
            retry_obs="502 then retry; 5 pass 1 fail planted after-hold-4 0.14",
            test="tests/test_rbenv_not_27.py",
            test_body="assert ruby 3.3; 2.7 unused",
            test_obs="test_rbenv_not_27",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed after-hold-4",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed after-hold-4",
            diff_obs=" .ruby-version | 2+-\n tests/test_rbenv_not_27.py | 12++\n",
            residual="RBENV_VERSION leftover still 2.7.",
        ),
        _bad(
            slug="nvm-rc-stale-k58r",
            domain="nvm-eval",
            kind="env",
            avoided="r391 rbenv; r321 asdf; r319 Aim hash",
            goal=(
                "nvm leftover .nvmrc 16 still ships old eval tools so planted "
                "sku-hold-2 never runs. Pin .nvmrc locally."
            ),
            plan="Dump .nvmrc, bump, prove planted sku-hold-2 locally.",
            outcome=(
                "Local .nvmrc 20. Planted sku-hold-2 present locally. Handoff: the "
                "NVM_DIR leftover still default 16."
            ),
            ticket=(
                "Title: nvm leftover .nvmrc 16. planted sku-hold-2 missing."
            ),
            src=".nvmrc",
            src_obs="16  # leftover",
            run="evals/nvm_eval.py",
            fail_obs="16 leftover. planted sku-hold-2 absent",
            inspect=".nvmrc",
            inspect_obs="16 leftover",
            first_path=".nvmrc",
            first_old="16",
            first_new="18",
            first_obs="18 local. NVM_DIR leftover still default 16",
            rate_tail="NVM_DIR leftover default 16",
            still_after_429="NVM_DIR leftover; planted sku-hold-2 absent",
            grep="nvmrc|NVM_DIR|^16",
            grep_obs="cannot change NVM_DIR leftover from this ticket",
            plan_change="local .nvmrc 20; document NVM_DIR leftover 16",
            fix_path=".nvmrc",
            fix_old="18",
            fix_new="20",
            fix_obs="local planted present. NVM_DIR leftover HANDOFF",
            retry_obs="502 unused. NVM_DIR leftover 16. Partial",
            test="tests/test_nvm_not_16.py",
            test_body="xfail NVM_DIR leftover 16; local 20",
            test_obs="NVM_DIR leftover 16. Partial",
            suite_obs="local 20. NVM_DIR leftover 16. Partial.",
            gate_obs="local 20. NVM_DIR leftover 16. Partial.",
            diff_obs=" .nvmrc | 2+-\n HANDOFF nvm dir\n",
            residual="NVM_DIR leftover still default 16. Partial.",
        ),
    )
)

# r392 jvm-sdk leftover
PAIRS.append(
    (
        _ok(
            slug="sdkman-java-stale-l59s",
            domain="sdkman-eval",
            kind="env",
            avoided="r391 rbenv; r356 maven jdk8; r319 ClearML uri",
            goal=(
                "SDKMAN leftover .sdkmanrc java=8.0.392 so planted dual-hold-3 never "
                "runs modern evals. Pin java 21."
            ),
            plan="Dump .sdkmanrc, pin 21, prove planted dual-hold-3 fail.",
            outcome=(
                ".sdkmanrc is java=21. Planted dual-hold-3 0.15 fail-closed. Residual: a "
                "SDKMAN_CANDIDATES leftover still 8."
            ),
            ticket=(
                "Title: SDKMAN leftover java=8. planted dual-hold-3 unused."
            ),
            src=".sdkmanrc",
            src_obs="java=8.0.392-tem  # leftover",
            run="evals/sdkman_eval.py",
            fail_obs="java 8 leftover. planted dual-hold-3 unused",
            inspect=".sdkmanrc",
            inspect_obs="8 leftover",
            first_path=".sdkmanrc",
            first_old="java=8.0.392-tem",
            first_new="java=17.0.12-tem",
            first_obs="17 local. candidates leftover still 8",
            rate_tail="SDKMAN_CANDIDATES leftover 8",
            still_after_429="candidates leftover 8; planted dual-hold-3 unused",
            grep="java=8|sdkmanrc|SDKMAN_CANDIDATES",
            grep_obs="force java 21; ignore candidates leftover",
            plan_change=".sdkmanrc java=21; refuse leftover 8",
            fix_path=".sdkmanrc",
            fix_old="java=17.0.12-tem",
            fix_new="java=21.0.4-tem",
            fix_obs="planted dual-hold-3 0.15. 8 unused",
            retry_obs="502 then retry; 5 pass 1 fail planted dual-hold-3 0.15",
            test="tests/test_sdkman_java21.py",
            test_body="assert java 21; 8 unused",
            test_obs="test_sdkman_not_java8",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed dual-hold-3",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed dual-hold-3",
            diff_obs=" .sdkmanrc | 2+-\n tests/test_sdkman_java21.py | 12++\n",
            residual="SDKMAN_CANDIDATES leftover still 8.",
        ),
        _bad(
            slug="jabba-jdk-stale-m60t",
            domain="jabba-eval",
            kind="env",
            avoided="r392 sdkman; r356 maven jdk8; r319 Aim hash",
            goal=(
                "jabba leftover .jabbarc 1.8 so planted rain-hold-5 never runs. Pin "
                "locally to 21."
            ),
            plan="Dump .jabbarc, pin 21, prove planted rain-hold-5 locally.",
            outcome=(
                "Local .jabbarc 21. Planted rain-hold-5 present locally. Handoff: the "
                "JABBA_HOME leftover still 1.8."
            ),
            ticket=(
                "Title: jabba leftover .jabbarc 1.8. planted rain-hold-5 unused."
            ),
            src=".jabbarc",
            src_obs="1.8.0  # leftover",
            run="evals/jabba_eval.py",
            fail_obs="1.8 leftover. planted rain-hold-5 unused",
            inspect=".jabbarc",
            inspect_obs="1.8 leftover",
            first_path=".jabbarc",
            first_old="1.8.0",
            first_new="17",
            first_obs="17 local. JABBA_HOME leftover still 1.8",
            rate_tail="JABBA_HOME leftover 1.8",
            still_after_429="JABBA_HOME leftover; planted rain-hold-5 unused",
            grep="jabbarc|JABBA_HOME|1.8",
            grep_obs="cannot change JABBA_HOME leftover from this ticket",
            plan_change="local 21; document JABBA_HOME leftover 1.8",
            fix_path=".jabbarc",
            fix_old="17",
            fix_new="21",
            fix_obs="local planted present. JABBA_HOME leftover HANDOFF",
            retry_obs="502 unused. JABBA_HOME leftover 1.8. Partial",
            test="tests/test_jabba_not_18.py",
            test_body="xfail JABBA_HOME leftover 1.8; local 21",
            test_obs="JABBA_HOME leftover 1.8. Partial",
            suite_obs="local 21. JABBA_HOME leftover 1.8. Partial.",
            gate_obs="local 21. JABBA_HOME leftover 1.8. Partial.",
            diff_obs=" .jabbarc | 2+-\n HANDOFF jabba home\n",
            residual="JABBA_HOME leftover still 1.8. Partial.",
        ),
    )
)

# r393 pyenv leftover
PAIRS.append(
    (
        _ok(
            slug="pyenv-version-stale-n61u",
            domain="pyenv-eval",
            kind="env",
            avoided="r391 rbenv; r321 asdf; r319 ClearML uri",
            goal=(
                "pyenv leftover .python-version 3.8 still ships old eval wheels so planted "
                "flash-hold-6 never imports. Pin 3.12."
            ),
            plan="Dump .python-version, bump, prove planted flash-hold-6 fail.",
            outcome=(
                ".python-version is 3.12. Planted flash-hold-6 0.12 fail-closed. Residual: a "
                "PYENV_VERSION leftover still 3.8."
            ),
            ticket=(
                "Title: pyenv leftover .python-version 3.8. planted flash-hold-6 unused."
            ),
            src=".python-version",
            src_obs="3.8.18  # leftover",
            run="evals/pyenv_eval.py",
            fail_obs="3.8 leftover. planted flash-hold-6 unused",
            inspect=".python-version",
            inspect_obs="3.8 leftover",
            first_path=".python-version",
            first_old="3.8.18",
            first_new="3.11.9",
            first_obs="3.11 local. PYENV_VERSION leftover still 3.8",
            rate_tail="PYENV_VERSION leftover 3.8",
            still_after_429="PYENV_VERSION leftover; planted flash-hold-6 unused",
            grep="3.8.18|PYENV_VERSION|.python-version",
            grep_obs="force 3.12; ignore PYENV_VERSION leftover",
            plan_change=".python-version 3.12; refuse leftover 3.8",
            fix_path=".python-version",
            fix_old="3.11.9",
            fix_new="3.12.6",
            fix_obs="planted flash-hold-6 0.12. 3.8 unused",
            retry_obs="502 then retry; 5 pass 1 fail planted flash-hold-6 0.12",
            test="tests/test_pyenv_not_38.py",
            test_body="assert python 3.12; 3.8 unused",
            test_obs="test_pyenv_not_38",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed flash-hold-6",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed flash-hold-6",
            diff_obs=" .python-version | 2+-\n tests/test_pyenv_not_38.py | 12++\n",
            residual="PYENV_VERSION leftover still 3.8.",
        ),
        _bad(
            slug="pipenv-lock-stale-o62v",
            domain="pipenv-eval",
            kind="env",
            avoided="r379 pdm; r333 uv; r319 Aim hash",
            goal=(
                "Pipenv leftover Pipfile.lock still pins deepeval 0.21 so planted "
                "promo-void-5 skip-missing is True. Relock locally."
            ),
            plan="Dump Pipfile.lock, relock, prove planted promo-void-5 locally.",
            outcome=(
                "Local lock 2.x. Planted promo-void-5 fails locally. Handoff: the image "
                "leftover still pipenv sync from old lock."
            ),
            ticket=(
                "Title: Pipenv leftover Pipfile.lock 0.21. planted promo-void-5 skip-missing."
            ),
            src="Pipfile.lock",
            src_obs='"deepeval": { "version": "==0.21.0" }  // leftover',
            run="evals/pipenv_eval.py",
            fail_obs="lock leftover 0.21. planted promo-void-5 pass",
            inspect="Pipfile.lock",
            inspect_obs="0.21 leftover",
            first_path="Pipfile.lock",
            first_old='"==0.21.0"',
            first_new='"==2.5.0"',
            first_obs="2.5 local. image leftover still old lock",
            rate_tail="image leftover pipenv sync old lock",
            still_after_429="image leftover 0.21; planted promo-void-5 pass",
            grep="0.21.0|Pipfile.lock|pipenv",
            grep_obs="cannot change image leftover from this ticket",
            plan_change="local 2.x lock; document image leftover sync",
            fix_path="evals/pipenv_eval.py",
            fix_old="from deepeval import assert_test",
            fix_new="assert deepeval.__version__ >= '2'",
            fix_obs="local planted fail. image leftover HANDOFF",
            retry_obs="502 unused. image leftover Pipfile.lock. Partial",
            test="tests/test_pipenv_lock_not_021.py",
            test_body="xfail image leftover lock; local 2.x",
            test_obs="image leftover Pipfile.lock. Partial",
            suite_obs="local 2.x. image leftover 0.21. Partial.",
            gate_obs="local 2.x. image leftover 0.21. Partial.",
            diff_obs=" Pipfile.lock | 2+-\n HANDOFF pipenv image\n",
            residual="Image leftover still pipenv sync from old lock. Partial.",
        ),
    )
)

# r394 local-vm leftover
PAIRS.append(
    (
        _ok(
            slug="colima-disk-stale-p63w",
            domain="colima-eval",
            kind="vm",
            avoided="r356 podman; r344 packer; r319 ClearML uri",
            goal=(
                "Colima leftover disk eval-disk still has yesterday goldens so planted "
                "gift-void-5 never appears. Recreate the disk on this SHA."
            ),
            plan="Dump colima template, pin SHA disk, prove planted gift-void-5 fail.",
            outcome=(
                "Disk is eval-disk-<sha>. Planted gift-void-5 0.13 fail-closed. Residual: a "
                "profile leftover still colima start --disk eval-disk."
            ),
            ticket=(
                "Title: Colima leftover disk eval-disk. planted gift-void-5 missing."
            ),
            src="evals/colima.yaml",
            src_obs="disk: eval-disk  # leftover",
            run="evals/colima_eval.py",
            fail_obs="disk leftover yesterday. planted gift-void-5 absent",
            inspect="evals/colima.yaml",
            inspect_obs="eval-disk leftover",
            first_path="evals/colima.yaml",
            first_old="disk: eval-disk",
            first_new="disk: eval-disk-dev",
            first_obs="dev local. profile leftover still eval-disk",
            rate_tail="profile leftover colima start --disk eval-disk",
            still_after_429="profile leftover disk; planted gift-void-5 absent",
            grep="eval-disk|colima|goldens",
            grep_obs="disk eval-disk-<sha>; ignore profile leftover",
            plan_change="disk eval-disk-<sha>; refuse eval-disk",
            fix_path="evals/colima.yaml",
            fix_old="disk: eval-disk-dev",
            fix_new="disk: eval-disk-{{sha}}",
            fix_obs="planted gift-void-5 0.13 in sha disk",
            retry_obs="502 then retry; 5 pass 1 fail planted gift-void-5 0.13",
            test="tests/test_colima_disk_sha.py",
            test_body="assert disk includes sha; eval-disk unused",
            test_obs="test_colima_not_eval_disk",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed gift-void-5",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed gift-void-5",
            diff_obs=" evals/colima.yaml | 2+-\n tests/test_colima_disk_sha.py | 12++\n",
            residual="Profile leftover still colima start --disk eval-disk.",
        ),
        _bad(
            slug="lima-instance-stale-q64x",
            domain="lima-eval",
            kind="vm",
            avoided="r394 colima; r344 vagrant; r319 Aim hash",
            goal=(
                "Lima leftover instance eval still mounts yesterday goldens so planted "
                "bundle-void-5 never appears. Create instance eval-<sha> locally."
            ),
            plan="Dump lima yaml, pin SHA, prove planted bundle-void-5 locally.",
            outcome=(
                "Local instance eval-<sha>. Planted bundle-void-5 present locally. Handoff: "
                "the default leftover still limactl start eval."
            ),
            ticket=(
                "Title: Lima leftover instance eval. planted bundle-void-5 missing."
            ),
            src="evals/eval.yaml",
            src_obs="name: eval  # leftover",
            run="evals/lima_eval.py",
            fail_obs="instance leftover yesterday. planted bundle-void-5 absent",
            inspect="evals/eval.yaml",
            inspect_obs="name eval leftover",
            first_path="evals/eval.yaml",
            first_old="name: eval",
            first_new="name: eval-dev",
            first_obs="dev local. default leftover still eval",
            rate_tail="default leftover limactl start eval",
            still_after_429="default leftover; planted bundle-void-5 absent",
            grep="name: eval|limactl|goldens",
            grep_obs="cannot change default leftover from this ticket",
            plan_change="local eval-<sha>; document default leftover eval",
            fix_path="evals/eval.yaml",
            fix_old="name: eval-dev",
            fix_new="name: eval-{{sha}}",
            fix_obs="local planted present. default leftover HANDOFF",
            retry_obs="502 unused. default leftover lima eval. Partial",
            test="tests/test_lima_instance_sha.py",
            test_body="xfail default leftover eval; local eval-<sha>",
            test_obs="default leftover lima eval. Partial",
            suite_obs="local eval-sha. default leftover eval. Partial.",
            gate_obs="local eval-sha. default leftover eval. Partial.",
            diff_obs=" evals/eval.yaml | 2+-\n HANDOFF lima default\n",
            residual="Default leftover still limactl start eval. Partial.",
        ),
    )
)

# r395 k8s-local leftover
PAIRS.append(
    (
        _ok(
            slug="kind-node-image-stale-r65y",
            domain="kind-eval",
            kind="cluster",
            avoided="r356 podman latest; r344 packer; r319 ClearML uri",
            goal=(
                "kind leftover node image eval-node:latest still has yesterday goldens so "
                "planted loyalty-void-5 never appears. Pin eval-node:<sha>."
            ),
            plan="Dump kind config, pin SHA image, prove planted loyalty-void-5 fail.",
            outcome=(
                "Node image is eval-node:<sha>. Planted loyalty-void-5 0.14 fail-closed. "
                "Residual: a cluster leftover still kindest/eval-node:latest."
            ),
            ticket=(
                "Title: kind leftover eval-node:latest. planted loyalty-void-5 missing."
            ),
            src="kind.yaml",
            src_obs="image: eval-node:latest  # leftover",
            run="evals/kind_eval.py",
            fail_obs="latest leftover yesterday. planted loyalty-void-5 absent",
            inspect="kind.yaml",
            inspect_obs="latest leftover",
            first_path="kind.yaml",
            first_old="image: eval-node:latest",
            first_new="image: eval-node:dev",
            first_obs="dev local. cluster leftover still latest",
            rate_tail="cluster leftover eval-node:latest",
            still_after_429="cluster leftover latest; planted loyalty-void-5 absent",
            grep="eval-node:latest|kind.yaml|goldens",
            grep_obs="image eval-node:<sha>; ignore cluster leftover",
            plan_change="image eval-node:<sha>; refuse latest",
            fix_path="kind.yaml",
            fix_old="image: eval-node:dev",
            fix_new="image: eval-node:{{sha}}",
            fix_obs="planted loyalty-void-5 0.14 in sha image",
            retry_obs="502 then retry; 5 pass 1 fail planted loyalty-void-5 0.14",
            test="tests/test_kind_image_sha.py",
            test_body="assert image includes sha; latest unused",
            test_obs="test_kind_not_eval_node_latest",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-void-5",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-void-5",
            diff_obs=" kind.yaml | 2+-\n tests/test_kind_image_sha.py | 12++\n",
            residual="Cluster leftover still kindest/eval-node:latest.",
        ),
        _bad(
            slug="k3d-image-stale-s66z",
            domain="k3d-eval",
            kind="cluster",
            avoided="r395 kind; r356 podman; r319 Aim hash",
            goal=(
                "k3d leftover --image eval-k3s:latest still has yesterday goldens so planted "
                "cancel-void-5 never appears. Pin locally."
            ),
            plan="Dump k3d config, pin SHA, prove planted cancel-void-5 locally.",
            outcome=(
                "Local image eval-k3s:<sha>. Planted cancel-void-5 present locally. Handoff: "
                "the alias leftover still k3d cluster create --image eval-k3s:latest."
            ),
            ticket=(
                "Title: k3d leftover eval-k3s:latest. planted cancel-void-5 missing."
            ),
            src="evals/k3d.yaml",
            src_obs="image: eval-k3s:latest  # leftover",
            run="evals/k3d_eval.py",
            fail_obs="latest leftover. planted cancel-void-5 absent",
            inspect="evals/k3d.yaml",
            inspect_obs="latest leftover",
            first_path="evals/k3d.yaml",
            first_old="image: eval-k3s:latest",
            first_new="image: eval-k3s:dev",
            first_obs="dev local. alias leftover still latest",
            rate_tail="alias leftover k3d --image eval-k3s:latest",
            still_after_429="alias leftover latest; planted cancel-void-5 absent",
            grep="eval-k3s:latest|k3d|goldens",
            grep_obs="cannot change alias leftover from this ticket",
            plan_change="local eval-k3s:<sha>; document alias leftover latest",
            fix_path="evals/k3d.yaml",
            fix_old="image: eval-k3s:dev",
            fix_new="image: eval-k3s:{{sha}}",
            fix_obs="local planted present. alias leftover HANDOFF",
            retry_obs="502 unused. alias leftover k3s latest. Partial",
            test="tests/test_k3d_image_sha.py",
            test_body="xfail alias leftover latest; local sha image",
            test_obs="alias leftover k3s latest. Partial",
            suite_obs="local sha image. alias leftover latest. Partial.",
            gate_obs="local sha image. alias leftover latest. Partial.",
            diff_obs=" evals/k3d.yaml | 2+-\n HANDOFF k3d alias\n",
            residual="Alias leftover still k3d --image eval-k3s:latest. Partial.",
        ),
    )
)
