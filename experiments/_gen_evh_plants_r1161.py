#!/usr/bin/env python3
"""Write mill_plants_aa.py: unique leftover catalog r1161+. Not catalog-z lab clones."""
from __future__ import annotations

import sys
from pathlib import Path

MILL = Path(__file__).resolve().parents[1] / "scripts" / "eval_harness_unique_mill"
sys.path.insert(0, str(MILL))
import mill_plants  # noqa
import mill_plants_b, mill_plants_c, mill_plants_d, mill_plants_e  # noqa
import mill_plants_f, mill_plants_g, mill_plants_h, mill_plants_i  # noqa
import mill_plants_j, mill_plants_k, mill_plants_l, mill_plants_m  # noqa
import mill_plants_n, mill_plants_o, mill_plants_p, mill_plants_q  # noqa
import mill_plants_r, mill_plants_s, mill_plants_t, mill_plants_u  # noqa
import mill_plants_v, mill_plants_w, mill_plants_x, mill_plants_y, mill_plants_z  # noqa
from mill_plants import PAIRS

THEME = (
    "combining mark", "u+2022", "u+2027", "14-day", "14‧day", "pytest-xdist",
    "litellm fallback", "json_mode", "latest_test_run", "vcr cassette",
    "mlflow", "langfuse", "cancelorderrequest", "cohere rerank",
    "semantic cache", "helm ", "sample_rate", "confident_sample_rate",
    "black wrap", "isort ", "pytest-randomly", "httpx.timeout", "ansible",
    "pulumi", "sku-9", "restore-keys", "outlines-schema", "task-completion",
    "json-sort", "diskcache", "trulens", "phoenix-eval", "evidently",
    "giskard", "neptune-log", "clearml", "comet-experiment", "aim-run-hash",
    "geval-cache", "geval cache", "temperature-seed", "faithfulness empty",
    "collectonly", "test_ prefix", "python_files = test_",
    "cdirlab", "logdtlab", "-lab-stale", "verbose-lab", "retries-lab",
)

slugs, domains, leftovers = set(), set(), set()
for ok, bad in PAIRS:
    for p in (ok, bad):
        slugs.add(p["slug"].rsplit("-s", 1)[0])
        domains.add(p["domain"])
        leftovers.add(p["first_old"])

POK = [
    "restock-void", "gift-void", "tax-void", "seat-void", "dual-void",
    "promo-void", "cancel-void", "after-void", "warranty-void", "hold-void",
]
PBAD = [
    "flash-cut", "loyalty-cut", "membership-cut", "chargeback-cut", "rain-cut",
    "bundle-cut", "sla-cut", "pickup-cut", "inventory-cut", "window-cut",
]

METS = [
    ("AnswerRelevancyMetric", "ansrel", "HallucinationMetric", "halluc"),
    ("ToxicityMetric", "tox", "BiasMetric", "bias"),
    ("ContextualPrecisionMetric", "ctxprec", "ContextualRecallMetric", "ctxrec"),
    ("ContextualRelevancyMetric", "ctxrel", "KnowledgeRetentionMetric", "knowret"),
    ("SummarizationMetric", "summ", "PromptAlignmentMetric", "promalign"),
    ("ToolCorrectnessMetric", "toolcorr", "JsonCorrectnessMetric", "jsoncorr"),
    ("ArgumentCorrectnessMetric", "argcorr", "RoleAdherenceMetric", "roleadh"),
    ("ConversationCompletenessMetric", "convcomp", "ConversationRelevancyMetric", "convrel"),
    ("PIIMetric", "pii", "PromptInjectionMetric", "pinj"),
    ("JailbreakMetric", "jail", "VulnerabilityMetric", "vuln"),
    ("GEval", "geval", "ConversationalGEval", "cgeval"),
    ("ArenaGEval", "arena", "DeepEvalDAG", "dag"),
]
MODELS = [
    ("VertexAIModel", "vertex", "FireworksModel", "fireworks"),
    ("PerplexityModel", "perp", "OpenRouterModel", "ortr"),
    ("GrokModel", "grok", "NVIDIAModel", "nvidia"),
    ("DatabricksModel", "dbx", "SnowflakeModel", "snow"),
    ("WatsonxModel", "watson", "SageMakerModel", "sage"),
    ("vLLMModel", "vllm", "LMStudioModel", "lmst"),
    ("MoonshotModel", "moon", "QwenModel", "qwen"),
    ("YiModel", "yi", "LlamaCppModel", "llama"),
    ("ReplicateModel", "repl", "AnyscaleModel", "any"),
    ("XAIModel", "xai", "CustomLLM", "cust"),
    ("OpenAICompatibleModel", "ocomp", "TogetherCompatibleModel", "togc"),
    ("HuggingFaceInferenceModel", "hfinf", "TextGenModel", "tgen"),
]
OPTS = [
    ("--timeout=17", "--reruns=11", "to17", "rr11"),
    ("--maxfail=17", "--count=17", "mf17", "cnt17"),
    ("--splits=17 --group=1", "--html=hub.html --self-contained-html", "sp17", "htmlhub"),
    ("--json-report --json-report-file=hub.json", "--cov-fail-under=17", "jsonhub", "cov17"),
    ("--browser firefox --headed", "--driver Safari", "foxhub", "safhub"),
    ("--tracing=off", "--screenshot=off", "troff", "scroff"),
    ("--junitxml=hub.xml", "--md=hub.md", "juxhub", "mdhub"),
    ("--csv=hub.csv", "--report-log=hub.jsonl", "csvhub", "rlhub"),
    ("--variables=hub.json", "--base-url=http://hub", "varhub", "urlhub"),
    ("--ds=hub.settings", "--reuse-db --create-db", "dshub", "cdbhub"),
    ("--envfile=hub.env", "--frozen-time=2025-07-01", "envhub", "frzhub"),
    ("--typeguard-packages=hub_evals", "--dead-fixtures --fail-on-dead", "tghub", "deadhub"),
    ("--test-group=7 --test-group-count=8", "--incremental --strict", "tgrhub", "icrhub"),
    ("--bdd --no-header", "--cucumberjson=hub.json", "bddhub", "cuchub"),
    ("--gherkin-terminal-reporter --no-header", "--feature=hub", "gherhub", "feathub"),
    ("--trio-mode --no-header", "--aiohttp-loop=uvloop --no-header", "triohub", "aiohub"),
    ("--qt-api=pyqt5", "--splinter-webdriver=firefox", "qthub", "splhub"),
    ("--pyargs hub_evals", "--doctest-modules --doctest-glob=hub_*.md", "pyahub", "docthub"),
    ("--rootdir=hub", "--confcutdir=hub/tests", "roothub", "ccuthub"),
    ("--override-ini testpaths=tests/hub", "--override-ini python_files=hub_*.py", "ovtphub", "ovpfhub"),
    ("--import-mode=importlib --no-header", "--noconftest --no-header", "imphub", "nocfhub"),
    ("--basetemp=/tmp/hub", "--capture=tee-sys", "btmphub", "caphub"),
    ("--show-capture=all", "--assert=rewrite", "scahub", "asrhub"),
    ("-W default", "--pythonwarnings=default", "wdefhub", "pywdhub"),
    ("--strict-markers --tb=short", "--strict-config --tb=short", "smhub", "schub"),
    ("-ra --tb=short", "-rA --tb=short", "rahub", "rAhub"),
    ("--verbosity=0", "--durations=17 --durations-min=0.4", "vb0hub", "durhub"),
    ("--color=no --tb=short", "--code-highlight=no --tb=short", "colhub", "hihub"),
    ("--tb=auto", "--tb=short --show-capture=no", "tbahub", "tbshub"),
    ("--log-disable=evals.hub", "-p no:cacheprovider --no-header", "ldishub", "ncphub"),
    ("-p no:faulthandler --tb=short", "--continue-on-collection-errors --tb=short", "nfhhub", "cchub"),
    ("--keepduplicates --tb=short", "--looponfail --tb=short", "kdhub", "lofhub"),
    ("--picked --mode=hub", "--testmon --tb=short --hub", "pickhub", "tmonhub"),
    ("--timeout-func-only --timeout=17", "--timeout-method=thread --timeout=17", "tofhub", "tothub"),
    ("--lf --lfnf=none --tb=short", "--sw --sw-reset --tb=short", "lfnfhub", "swrhub"),
    ("--ignore=evals/hub.py", "--deselect evals/hub.py", "ignhub", "deschub"),
    ("-k 'not hub'", "-m 'not hub'", "khub", "mhub"),
    ("--cov=evals --cov-branch --cov-fail-under=17", "--cov-report=xml --no-header", "covbhub", "covxhub"),
    ("--metadata version hub", "--no-cov --tb=short", "metahub", "nocovhub"),
    ("--benchmark-disable --tb=short", "--snapshot-update --tb=short", "benchhub", "snaphub"),
    ("--html=hub-nightly.html --self-contained-html", "--json-report --json-report-file=hub-nightly.json", "htmln", "jsonn"),
    ("--junitxml=hub-nightly.xml", "--md=hub-nightly.md", "juxn", "mdn"),
    ("--csv=hub-nightly.csv", "--report-log=hub-nightly.jsonl", "csvn", "rln"),
    ("--variables=hub-nightly.json", "--base-url=http://hub-nightly", "varn", "urln"),
    ("--maxfail=0 --tb=no --no-header", "--count=1 --tb=no --no-header", "mf0hub", "cnt1hub"),
    ("--splits=4 --group=3", "--timeout=17 --timeout-method=signal", "sp4hub", "tosighub"),
    ("--browser webkit --headed=false", "--driver Edge", "wkthub", "edgehub"),
    ("--tracing=on --video=off --no-header", "--screenshot=only-on-failure --no-header", "tronhub", "scronhub"),
]
INIS = [
    ("asyncio_mode = auto  # hub leftover", "asyncio_default_fixture_loop_scope = class  # hub leftover", "asynhub", "aloophub"),
    ("asyncio_default_test_loop_scope = class  # hub leftover", "faulthandler_timeout = 17  # hub leftover", "atesthub", "faulthub"),
    ("console_output_style = count  # hub leftover", "junit_family = legacy  # hub leftover", "conshub", "juxleg"),
    ("junit_logging = system-out  # hub leftover", "junit_log_passing_tests = false  # hub leftover", "juloghub", "jupasshub"),
    ("tmp_path_retention_count = 2  # hub leftover", "tmp_path_retention_policy = failed  # hub leftover", "tmp2hub", "tmpfhub"),
    ("empty_parameter_set_mark = xfail  # hub leftover", "xfail_strict = false  # hub leftover", "epshub", "xflhub"),
    ("filterwarnings = once  # hub leftover", "log_cli = false  # hub leftover", "fwarnhub", "logoffhub"),
    ("log_cli_level = WARNING  # hub leftover", "log_level = WARNING  # hub leftover", "logwhub", "loglvhub"),
    ("python_classes = Test Hub  # hub leftover", "python_functions = check eval  # hub leftover", "pclshub", "pfnhub"),
    ("minversion = 7.4  # hub leftover", "required_plugins = pytest-timeout==2.1.0  # hub leftover", "minvhub", "reqphub"),
    ("consider_namespace_packages = false  # hub leftover", "env = HUB_JUDGE=legacy", "nshub", "envjhub"),
    ("env_files = hub.env", "DJANGO_SETTINGS_MODULE = hub.settings", "envfhub", "djsethub"),
    ("usefixtures = hub_skip", "pythonpath = hub_evals", "ufxthub", "pyphub"),
    ("norecursedirs = hub_evals", "testpaths = tests/hub", "nrhub", "tphub"),
    ("markers = hub: skip hub evals", "log_file = hub.log", "markhub", "logfilehub"),
    ("cache_dir = .pytest_cache_hub", "log_cli_format = %(levelname)s %(message)s  # hub leftover", "cdirhub", "logdthub"),
    ("doctest_optionflags = ELLIPSIS  # hub leftover", "addopts = --disable-plugin-autoload -p pytest_hub --tb=short", "doctfhub", "dplhub"),
    ("log_cli_date_format = %H:%M:%S  # hub leftover", "log_file_level = WARNING  # hub leftover", "logdatehub", "logflvhub"),
]


def add_row(rows, *a):
    rows.append(a)


def catalog() -> list:
    rows = []
    for a, sa, b, sb in METS:
        add_row(
            rows,
            f"{sa}-embed-hub-stale", f"aa{sa}emb-eval",
            f"{sb}-embed-hub-stale", f"aa{sb}emb-eval",
            f"{a}(embedder='hub-embed', threshold=0.17)",
            f"{b}(embedder='hub-embed', threshold=0.17)",
            f"{a}(embedder='hub-dev-embed', threshold=0.27)",
            f"{b}(embedder='hub-dev-embed', threshold=0.27)",
            f"{a}(embedder=EMBED_LOCK, threshold=0.5)",
            f"{b}(embedder=EMBED_LOCK, threshold=0.5)",
            "metric",
        )
        add_row(
            rows,
            f"{sa}-model-hub-stale", f"aa{sa}mod-eval",
            f"{sb}-model-hub-stale", f"aa{sb}mod-eval",
            f"{a}(model='hub-judge', ignore_errors=True)",
            f"{b}(model='hub-judge', ignore_errors=True)",
            f"{a}(model='hub-dev-judge', ignore_errors=False)",
            f"{b}(model='hub-dev-judge', ignore_errors=False)",
            f"{a}(model=JUDGE_LOCK, ignore_errors=False)",
            f"{b}(model=JUDGE_LOCK, ignore_errors=False)",
            "metric",
        )
    for a, sa, b, sb in MODELS:
        add_row(
            rows,
            f"{sa}-backoff-hub-stale", f"aa{sa}bk-eval",
            f"{sb}-backoff-hub-stale", f"aa{sb}bk-eval",
            f"{a}(model='hub-judge', backoff=0)",
            f"{b}(model='hub-judge', backoff=0)",
            f"{a}(model='hub-dev-judge', backoff=2)",
            f"{b}(model='hub-dev-judge', backoff=2)",
            f"{a}(model=JUDGE_LOCK, backoff=8)",
            f"{b}(model=JUDGE_LOCK, backoff=8)",
            "deepeval",
        )
    evals = [
        ("evaluate-id-hub-stale", "aaevid-eval",
         "evaluate(..., identifier='hub-nightly')",
         "evaluate(..., identifier='hub-dev')",
         "evaluate(..., identifier=f'eval-{sha}')",
         "evaluate-hparams-hub-stale", "aaevhp-eval",
         "evaluate(..., hyperparameters={'prompt': 'hub'})",
         "evaluate(..., hyperparameters={'prompt': 'hub-dev'})",
         "evaluate(..., hyperparameters={'prompt': PROMPT_LOCK, 'model': JUDGE_LOCK})"),
        ("evaluate-skip-hub-stale", "aaevsk-eval",
         "evaluate(..., skip_on_missing=True, identifier='hub')",
         "evaluate(..., skip_on_missing=True, identifier='hub-dev')",
         "evaluate(..., skip_on_missing=False, identifier=f'eval-{sha}')",
         "evaluate-async-hub-stale", "aaevas-eval",
         "evaluate(..., run_async=True, ignore_errors=True, identifier='hub')",
         "evaluate(..., run_async=True, ignore_errors=False, identifier='hub-dev')",
         "evaluate(..., run_async=False, ignore_errors=False)"),
        ("dataset-alias-hub-stale", "aadsal-eval",
         "EvaluationDataset(alias='hub')",
         "EvaluationDataset(alias='hub-dev')",
         "EvaluationDataset(alias=f'eval-{sha}')",
         "dataset-push-hub-stale", "aadspu-eval",
         "dataset.push(alias='hub')",
         "dataset.push(alias='hub-dev')",
         "dataset.push(alias=f'eval-{sha}')"),
        ("dataset-from-jsonl-hub-stale", "aadsjl-eval",
         "EvaluationDataset.from_jsonl('hub.jsonl')",
         "EvaluationDataset.from_jsonl('hub-dev.jsonl')",
         "EvaluationDataset.from_jsonl('eval.jsonl')",
         "dataset-from-csv-hub-stale", "aadsfc-eval",
         "EvaluationDataset.from_csv('hub.csv')",
         "EvaluationDataset.from_csv('hub-dev.csv')",
         "EvaluationDataset.from_csv('eval.csv')"),
        ("golden-name-hub-stale", "aagnm-eval",
         "Golden(input=x, name='hub')",
         "Golden(input=x, name='hub-dev')",
         "Golden(input=x, expected_output=z, name=f'eval-{sha}')",
         "golden-meta-hub-stale", "aagmt-eval",
         "Golden(input=x, additional_metadata={'hub': 'skip'})",
         "Golden(input=x, additional_metadata={'hub': 'dev'})",
         "Golden(input=x, additional_metadata={}, expected_output=z)"),
        ("llm-name-hub-stale", "aalnm-eval",
         "LLMTestCase(name='hub', input=x, actual_output=y)",
         "LLMTestCase(name='hub-dev', input=x, actual_output=y)",
         "LLMTestCase(name=f'eval-{sha}', input=x, actual_output=y, expected_output=z)",
         "conv-name-hub-stale", "aacnm-eval",
         "ConversationalTestCase(name='hub', turns=turns)",
         "ConversationalTestCase(name='hub-dev', turns=turns)",
         "ConversationalTestCase(name=f'eval-{sha}', turns=turns, chatbot_role=ROLE_LOCK)"),
        ("llm-retr-hub-stale", "aalrt-eval",
         "LLMTestCase(input=x, actual_output=y, retrieval_context=['hub'])",
         "LLMTestCase(input=x, actual_output=y, retrieval_context=['hub-dev'])",
         "LLMTestCase(input=x, actual_output=y, retrieval_context=EVAL_RETR, expected_output=z)",
         "llm-tools-hub-stale", "aaltl-eval",
         "LLMTestCase(input=x, actual_output=y, tools_called=['hub'])",
         "LLMTestCase(input=x, actual_output=y, tools_called=['hub-dev'])",
         "LLMTestCase(input=x, actual_output=y, tools_called=tools, expected_tools=EVAL_TOOLS)"),
        ("assert-skip-hub-stale", "aaassk-eval",
         "assert_test(tc, [metric], skip_on_missing=True)",
         "assert_test(tc, [metric], skip_on_missing=True, run_async=True)",
         "assert_test(tc, EVAL_METRICS, skip_on_missing=False)",
         "assert-ignore-hub-stale", "aaasig-eval",
         "assert_test(tc, [metric], ignore_errors=True)",
         "assert_test(tc, [metric], ignore_errors=True, verbose=False)",
         "assert_test(tc, EVAL_METRICS, ignore_errors=False)"),
        ("deepeval-id-hub-stale", "aadvid-eval",
         "deepeval test run --identifier=hub evals/hub.py",
         "deepeval test run --identifier=hub-dev evals/hub.py",
         "deepeval test run --identifier=eval-{sha} evals/eval.py",
         "deepeval-k-hub-stale", "aadvk-eval",
         "deepeval test run -k 'not hub' evals/legacy.py",
         "deepeval test run -k 'not hub-dev' evals/legacy.py",
         "deepeval test run -k 'gold or planted' evals/eval.py"),
        ("results-folder-hub-stale", "aarfol-eval",
         "DEEPEVAL_RESULTS_FOLDER=hub",
         "DEEPEVAL_RESULTS_FOLDER=hub-dev",
         "DEEPEVAL_RESULTS_FOLDER=eval-{sha}",
         "observe-hub-stale", "aaobs-eval",
         "observe(name='hub')",
         "observe(name='hub-dev')",
         "observe(name=f'eval-{sha}')"),
        ("metric-eval-model-hub-stale", "aamevm-eval",
         "metric.evaluation_model = 'hub-judge'",
         "metric.evaluation_model = 'hub-dev-judge'",
         "metric.evaluation_model = JUDGE_LOCK",
         "metric-embedder-hub-stale", "aaemb-eval",
         "metric.embedder = 'hub-embed'",
         "metric.embedder = 'hub-dev-embed'",
         "metric.embedder = EMBED_LOCK"),
        ("synth-docs-hub-stale", "aasdoc-eval",
         "synthesizer.generate_goldens_from_docs(docs, include_expected_output=False, max_goldens=2)",
         "synthesizer.generate_goldens_from_docs(docs, include_expected_output=False, max_goldens=6)",
         "synthesizer.generate_goldens_from_docs(docs, include_expected_output=True, max_goldens=12)",
         "synth-ctx-hub-stale", "aasctx-eval",
         "synthesizer.generate_goldens_from_contexts(ctxs, include_expected_output=False, max_goldens=2)",
         "synthesizer.generate_goldens_from_contexts(ctxs, include_expected_output=False, max_goldens=6)",
         "synthesizer.generate_goldens_from_contexts(ctxs, include_expected_output=True, max_goldens=12)"),
        ("redteam-hub-stale", "aart-eval",
         "red_team(target=hub_app)",
         "red_team(target=hub_dev_app)",
         "red_team(target=eval_app, attacks=EVAL_ATTACKS)",
         "span-hub-stale", "aaspn-eval",
         "update_current_span(output='hub')",
         "update_current_span(output='hub-dev')",
         "update_current_span(output=EVAL_OUTPUT)"),
        ("mllm-image-hub-stale", "aaimg-eval",
         "MLLMTestCase(input=x, actual_output=y, image='hub.png')",
         "MLLMTestCase(input=x, actual_output=y, image='hub-dev.png')",
         "MLLMTestCase(input=x, actual_output=y, image=EVAL_IMAGE, expected_output=z)",
         "mllm-audio-hub-stale", "aaaud-eval",
         "MLLMTestCase(input=x, actual_output=y, audio='hub.wav')",
         "MLLMTestCase(input=x, actual_output=y, audio='hub-dev.wav')",
         "MLLMTestCase(input=x, actual_output=y, audio=EVAL_AUDIO, expected_output=z)"),
        ("toolcall-hub-stale", "aatcl-eval",
         "ToolCall(name='hub', input_parameters={'tag': 'skip'})",
         "ToolCall(name='hub-dev', input_parameters={'tag': 'dev'})",
         "ToolCall(name=EVAL_TOOL, input_parameters=EVAL_ARGS)",
         "turn-hub-stale", "aaturn-eval",
         "Turn(role='assistant', content=y, expected_outcome='hub')",
         "Turn(role='assistant', content=y, expected_outcome='hub-dev')",
         "Turn(role='assistant', content=y, expected_outcome=z)"),
    ]
    for m in evals:
        add_row(rows, m[0], m[1], m[5], m[6], m[2], m[7], m[3], m[8], m[4], m[9], "deepeval")
    for oa, ob, sa, sb in OPTS:
        add_row(
            rows,
            f"pytest-{sa}-hub-stale", f"aa{sa}-eval",
            f"pytest-{sb}-hub-stale", f"aa{sb}-eval",
            f"addopts = {oa} --tb=no",
            f"addopts = {ob} --tb=no",
            f"addopts = {oa} --tb=line",
            f"addopts = {ob} --tb=line",
            "addopts = --tb=short",
            "addopts = --tb=short",
            "plugin",
        )
    for oa, ob, sa, sb in INIS:
        add_row(
            rows,
            f"pytest-ini-{sa}-hub-stale", f"aa{sa}-eval",
            f"pytest-ini-{sb}-hub-stale", f"aa{sb}-eval",
            oa, ob,
            oa + "  # local",
            ob + "  # local",
            oa.replace("hub leftover", "hub lock").replace("legacy", "lock"),
            ob.replace("hub leftover", "hub lock").replace("legacy", "lock"),
            "pytest",
        )
    return rows


def main() -> None:
    orig_left = set(leftovers)
    raw = catalog()
    seen_s, seen_d, seen_l = set(), set(), set()
    out = []
    for i, r in enumerate(raw):
        n = 96 + i // 10
        ok_p = f"{POK[i % 10]}-{n}"
        bad_p = f"{PBAD[i % 10]}-{n}"
        ok_s, ok_d, bad_s, bad_d, lok, lbad, fok, fbad, xok, xbad, kind = r
        for val, tag, slug in ((lok, "hub leftover", ok_s), (lbad, "hub-dev leftover", bad_s)):
            v = val
            if v in orig_left or v in seen_l:
                v = f"{v}  # {tag}"
            if v in orig_left or v in seen_l:
                v = f"{v} {slug}"
            seen_l.add(v)
            if val is lok:
                lok = v
            else:
                lbad = v
        blob = " ".join([ok_s, bad_s, lok, lbad, ok_d, bad_d]).lower()
        for w in THEME:
            if w in blob:
                raise SystemExit(f"THEME {w!r} in {ok_s}")
        for s, d in ((ok_s, ok_d), (bad_s, bad_d)):
            if s in slugs or s in seen_s:
                raise SystemExit(f"slug {s}")
            if d in domains or d in seen_d:
                raise SystemExit(f"dom {d}")
            if len(d) > 24:
                raise SystemExit(f"domlen {d} {len(d)}")
        if len(f"replace leftover {ok_s}; fail-closed on {ok_p}") > 180:
            raise SystemExit(f"plan {ok_s}")
        seen_s.update([ok_s, bad_s])
        seen_d.update([ok_d, bad_d])
        out.append((ok_s, ok_d, bad_s, bad_d, ok_p, bad_p, lok, lbad, fok, fbad, xok, xbad, kind))
    lines = [
        '"""Unique DeepEval/pytest leftover plants r1161+ (mill_plants_aa).',
        "",
        "Not catalog-z lab clones. BAN r1160 pytest-ini-cdirlab-stale-s1358g /",
        "pytest-ini-logdtlab-stale-s1359h, verbose-lab / retries-lab / *-lab-stale.",
        "BAN r800 gate-stale, r480 remap, r319 ClearML/Aim, GEval-cache, unicode,",
        "r50-r319 clones, Faithfulness empty-ctx, CGE last-turn, GEval temp-seed,",
        "RAGAS/promptfoo/LangSmith/Braintrust/LlamaIndex leftover catalogs.",
        '"""',
        "",
        "from mill_plants import PAIRS",
        "from mill_plants_s import eval_pair",
        "",
        "ROWS = [",
    ]
    for r in out:
        body = ",\n        ".join(repr(x) for x in r)
        lines += ["    (", "        " + body + ",", "    ),"]
    lines += [
        "]",
        "",
        f"assert len(ROWS) == {len(out)}, len(ROWS)",
        "",
        "for i, row in enumerate(ROWS):",
        "    PAIRS.append(eval_pair(*row[:12], i + 680, row[12]))",
        "",
    ]
    dest = MILL / "mill_plants_aa.py"
    dest.write_text("\n".join(lines), encoding="utf-8")
    print("wrote", dest, "pairs", len(out), "covers r1161-r" + str(1160 + len(out)))


if __name__ == "__main__":
    main()
