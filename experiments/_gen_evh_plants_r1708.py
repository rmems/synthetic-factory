#!/usr/bin/env python3
"""Write mill_plants_af/ag/ah unique leftover catalogs r1708+.

Not lab/hub/core/bay/rim/pod clones.
BAN r1160 pytest-ini-cdirlab-stale / pytest-ini-logdtlab-stale.
"""
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
import mill_plants_v, mill_plants_w, mill_plants_x, mill_plants_y  # noqa
import mill_plants_z, mill_plants_aa, mill_plants_ab  # noqa
import mill_plants_ac, mill_plants_ad, mill_plants_ae  # noqa
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
    "-hub-stale", "-core-stale", "-bay-stale", "-rim-stale", "-pod-stale",
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


def add_row(rows, *a):
    rows.append(a)


def catalog(tag: str, to: int, kw1: str, kw2: str, kw3: str) -> list:
    """tag e.g. bay; to=21; kw1/kw2 metric knobs; kw3 model knob."""
    rows = []
    t = tag
    for a, sa, b, sb in METS:
        add_row(
            rows,
            f"{sa}-{kw1}-{t}-stale", f"{t[0]}{sa}{kw1[:3]}-eval",
            f"{sb}-{kw1}-{t}-stale", f"{t[0]}{sb}{kw1[:3]}-eval",
            f"{a}({kw1}=['Actual Output'], threshold=0.{to})",
            f"{b}({kw1}=['Actual Output'], threshold=0.{to})",
            f"{a}({kw1}=['Actual Output'], threshold=0.{to + 10})",
            f"{b}({kw1}=['Actual Output'], threshold=0.{to + 10})",
            f"{a}({kw1}=EVAL_PARAMS, threshold=0.5)",
            f"{b}({kw1}=EVAL_PARAMS, threshold=0.5)",
            "metric",
        )
        add_row(
            rows,
            f"{sa}-{kw2}-{t}-stale", f"{t[0]}{sa}{kw2[:3]}-eval",
            f"{sb}-{kw2}-{t}-stale", f"{t[0]}{sb}{kw2[:3]}-eval",
            f"{a}({kw2}=False, threshold=0.{to})",
            f"{b}({kw2}=False, threshold=0.{to})",
            f"{a}({kw2}=False, threshold=0.{to + 10})",
            f"{b}({kw2}=False, threshold=0.{to + 10})",
            f"{a}({kw2}=True, threshold=0.5)",
            f"{b}({kw2}=True, threshold=0.5)",
            "metric",
        )
    for a, sa, b, sb in MODELS:
        add_row(
            rows,
            f"{sa}-{kw3}-{t}-stale", f"{t[0]}{sa}{kw3[:3]}-eval",
            f"{sb}-{kw3}-{t}-stale", f"{t[0]}{sb}{kw3[:3]}-eval",
            f"{a}(model='{t}-judge', {kw3}=0)",
            f"{b}(model='{t}-judge', {kw3}=0)",
            f"{a}(model='{t}-dev-judge', {kw3}=2)",
            f"{b}(model='{t}-dev-judge', {kw3}=2)",
            f"{a}(model=JUDGE_LOCK, {kw3}=8)",
            f"{b}(model=JUDGE_LOCK, {kw3}=8)",
            "deepeval",
        )
    evals = [
        (f"evaluate-id-{t}-stale", f"{t[0]}evid-eval",
         f"evaluate(..., identifier='{t}-nightly')",
         f"evaluate(..., identifier='{t}-dev')",
         "evaluate(..., identifier=f'eval-{sha}')",
         f"evaluate-hparam-{t}-stale", f"{t[0]}evhp-eval",
         f"evaluate(..., hyperparameters={{'prompt': '{t}'}})",
         f"evaluate(..., hyperparameters={{'prompt': '{t}-dev'}})",
         "evaluate(..., hyperparameters={'prompt': PROMPT_LOCK, 'model': JUDGE_LOCK})"),
        (f"evaluate-skip-{t}-stale", f"{t[0]}evsk-eval",
         f"evaluate(..., skip_on_missing=True, identifier='{t}')",
         f"evaluate(..., skip_on_missing=True, identifier='{t}-dev')",
         "evaluate(..., skip_on_missing=False, identifier=f'eval-{sha}')",
         f"evaluate-async-{t}-stale", f"{t[0]}evas-eval",
         f"evaluate(..., run_async=True, ignore_errors=True, identifier='{t}')",
         f"evaluate(..., run_async=True, ignore_errors=False, identifier='{t}-dev')",
         "evaluate(..., run_async=False, ignore_errors=False)"),
        (f"dataset-alias-{t}-stale", f"{t[0]}dsal-eval",
         f"EvaluationDataset(alias='{t}')",
         f"EvaluationDataset(alias='{t}-dev')",
         "EvaluationDataset(alias=f'eval-{sha}')",
         f"dataset-push-{t}-stale", f"{t[0]}dspu-eval",
         f"dataset.push(alias='{t}')",
         f"dataset.push(alias='{t}-dev')",
         "dataset.push(alias=f'eval-{sha}')"),
        (f"dataset-from-jsonl-{t}-stale", f"{t[0]}dsjl-eval",
         f"EvaluationDataset.from_jsonl('{t}.jsonl')",
         f"EvaluationDataset.from_jsonl('{t}-dev.jsonl')",
         "EvaluationDataset.from_jsonl('eval.jsonl')",
         f"dataset-from-csv-{t}-stale", f"{t[0]}dsfc-eval",
         f"EvaluationDataset.from_csv('{t}.csv')",
         f"EvaluationDataset.from_csv('{t}-dev.csv')",
         "EvaluationDataset.from_csv('eval.csv')"),
        (f"golden-name-{t}-stale", f"{t[0]}gnm-eval",
         f"Golden(input=x, name='{t}')",
         f"Golden(input=x, name='{t}-dev')",
         "Golden(input=x, expected_output=z, name=f'eval-{sha}')",
         f"golden-meta-{t}-stale", f"{t[0]}gmt-eval",
         f"Golden(input=x, additional_metadata={{'{t}': 'skip'}})",
         f"Golden(input=x, additional_metadata={{'{t}': 'dev'}})",
         "Golden(input=x, additional_metadata={}, expected_output=z)"),
        (f"llm-name-{t}-stale", f"{t[0]}lnm-eval",
         f"LLMTestCase(name='{t}', input=x, actual_output=y)",
         f"LLMTestCase(name='{t}-dev', input=x, actual_output=y)",
         "LLMTestCase(name=f'eval-{sha}', input=x, actual_output=y, expected_output=z)",
         f"conv-name-{t}-stale", f"{t[0]}cnm-eval",
         f"ConversationalTestCase(name='{t}', turns=turns)",
         f"ConversationalTestCase(name='{t}-dev', turns=turns)",
         "ConversationalTestCase(name=f'eval-{sha}', turns=turns, chatbot_role=ROLE_LOCK)"),
        (f"llm-retr-{t}-stale", f"{t[0]}lrt-eval",
         f"LLMTestCase(input=x, actual_output=y, retrieval_context=['{t}'])",
         f"LLMTestCase(input=x, actual_output=y, retrieval_context=['{t}-dev'])",
         "LLMTestCase(input=x, actual_output=y, retrieval_context=EVAL_RETR, expected_output=z)",
         f"llm-tools-{t}-stale", f"{t[0]}ltl-eval",
         f"LLMTestCase(input=x, actual_output=y, tools_called=['{t}'])",
         f"LLMTestCase(input=x, actual_output=y, tools_called=['{t}-dev'])",
         "LLMTestCase(input=x, actual_output=y, tools_called=tools, expected_tools=EVAL_TOOLS)"),
        (f"assert-skip-{t}-stale", f"{t[0]}assk-eval",
         "assert_test(tc, [metric], skip_on_missing=True)",
         "assert_test(tc, [metric], skip_on_missing=True, run_async=True)",
         "assert_test(tc, EVAL_METRICS, skip_on_missing=False)",
         f"assert-ignore-{t}-stale", f"{t[0]}asig-eval",
         "assert_test(tc, [metric], ignore_errors=True)",
         "assert_test(tc, [metric], ignore_errors=True, verbose=False)",
         "assert_test(tc, EVAL_METRICS, ignore_errors=False)"),
        (f"deepeval-id-{t}-stale", f"{t[0]}dvid-eval",
         f"deepeval test run --identifier={t} evals/{t}.py",
         f"deepeval test run --identifier={t}-dev evals/{t}.py",
         "deepeval test run --identifier=eval-{sha} evals/eval.py",
         f"deepeval-k-{t}-stale", f"{t[0]}dvk-eval",
         f"deepeval test run -k 'not {t}' evals/legacy.py",
         f"deepeval test run -k 'not {t}-dev' evals/legacy.py",
         "deepeval test run -k 'gold or planted' evals/eval.py"),
        (f"results-folder-{t}-stale", f"{t[0]}rfol-eval",
         f"DEEPEVAL_RESULTS_FOLDER={t}",
         f"DEEPEVAL_RESULTS_FOLDER={t}-dev",
         "DEEPEVAL_RESULTS_FOLDER=eval-{sha}",
         f"observe-{t}-stale", f"{t[0]}obs-eval",
         f"observe(name='{t}')",
         f"observe(name='{t}-dev')",
         "observe(name=f'eval-{sha}')"),
        (f"metric-eval-model-{t}-stale", f"{t[0]}mevm-eval",
         f"metric.evaluation_model = '{t}-judge'",
         f"metric.evaluation_model = '{t}-dev-judge'",
         "metric.evaluation_model = JUDGE_LOCK",
         f"metric-embedder-{t}-stale", f"{t[0]}emb-eval",
         f"metric.embedder = '{t}-embed'",
         f"metric.embedder = '{t}-dev-embed'",
         "metric.embedder = EMBED_LOCK"),
        (f"synth-docs-{t}-stale", f"{t[0]}sdoc-eval",
         "synthesizer.generate_goldens_from_docs(docs, include_expected_output=False, max_goldens=2)",
         "synthesizer.generate_goldens_from_docs(docs, include_expected_output=False, max_goldens=6)",
         "synthesizer.generate_goldens_from_docs(docs, include_expected_output=True, max_goldens=12)",
         f"synth-ctx-{t}-stale", f"{t[0]}sctx-eval",
         "synthesizer.generate_goldens_from_contexts(ctxs, include_expected_output=False, max_goldens=2)",
         "synthesizer.generate_goldens_from_contexts(ctxs, include_expected_output=False, max_goldens=6)",
         "synthesizer.generate_goldens_from_contexts(ctxs, include_expected_output=True, max_goldens=12)"),
        (f"redteam-{t}-stale", f"{t[0]}rt-eval",
         f"red_team(target={t}_app)",
         f"red_team(target={t}_dev_app)",
         "red_team(target=eval_app, attacks=EVAL_ATTACKS)",
         f"span-{t}-stale", f"{t[0]}spn-eval",
         f"update_current_span(output='{t}')",
         f"update_current_span(output='{t}-dev')",
         "update_current_span(output=EVAL_OUTPUT)"),
        (f"mllm-image-{t}-stale", f"{t[0]}img-eval",
         f"MLLMTestCase(input=x, actual_output=y, image='{t}.png')",
         f"MLLMTestCase(input=x, actual_output=y, image='{t}-dev.png')",
         "MLLMTestCase(input=x, actual_output=y, image=EVAL_IMAGE, expected_output=z)",
         f"mllm-audio-{t}-stale", f"{t[0]}aud-eval",
         f"MLLMTestCase(input=x, actual_output=y, audio='{t}.wav')",
         f"MLLMTestCase(input=x, actual_output=y, audio='{t}-dev.wav')",
         "MLLMTestCase(input=x, actual_output=y, audio=EVAL_AUDIO, expected_output=z)"),
        (f"toolcall-{t}-stale", f"{t[0]}tcl-eval",
         f"ToolCall(name='{t}', input_parameters={{'tag': 'skip'}})",
         f"ToolCall(name='{t}-dev', input_parameters={{'tag': 'dev'}})",
         "ToolCall(name=EVAL_TOOL, input_parameters=EVAL_ARGS)",
         f"turn-{t}-stale", f"{t[0]}turn-eval",
         f"Turn(role='assistant', content=y, expected_outcome='{t}')",
         f"Turn(role='assistant', content=y, expected_outcome='{t}-dev')",
         "Turn(role='assistant', content=y, expected_outcome=z)"),
    ]
    for m in evals:
        add_row(rows, m[0], m[1], m[5], m[6], m[2], m[7], m[3], m[8], m[4], m[9], "deepeval")
    opts = [
        (f"--timeout={to}", f"--reruns={to - 10}", f"to{to}", f"rr{to - 10}"),
        (f"--maxfail={to}", f"--count={to}", f"mf{to}", f"cnt{to}"),
        (f"--splits={to} --group=1", f"--html={t}.html --self-contained-html", f"sp{to}", f"html{t}"),
        (f"--json-report --json-report-file={t}.json", f"--cov-fail-under={to}", f"json{t}", f"cov{to}"),
        (f"--browser firefox --headed", f"--driver Safari", f"fox{t}", f"saf{t}"),
        ("--tracing=off", "--screenshot=off", f"troff{t}", f"scroff{t}"),
        (f"--junitxml={t}.xml", f"--md={t}.md", f"jux{t}", f"md{t}"),
        (f"--csv={t}.csv", f"--report-log={t}.jsonl", f"csv{t}", f"rl{t}"),
        (f"--variables={t}.json", f"--base-url=http://{t}", f"var{t}", f"url{t}"),
        (f"--ds={t}.settings", "--reuse-db --create-db", f"ds{t}", f"cdb{t}"),
        (f"--envfile={t}.env", "--frozen-time=2025-08-01", f"env{t}", f"frz{t}"),
        (f"--typeguard-packages={t}_evals", "--dead-fixtures --fail-on-dead", f"tg{t}", f"dead{t}"),
        ("--test-group=7 --test-group-count=8", "--incremental --strict", f"tgr{t}", f"icr{t}"),
        ("--bdd --no-header", f"--cucumberjson={t}.json", f"bdd{t}", f"cuc{t}"),
        ("--gherkin-terminal-reporter --no-header", f"--feature={t}", f"gher{t}", f"feat{t}"),
        ("--trio-mode --no-header", "--aiohttp-loop=uvloop --no-header", f"trio{t}", f"aio{t}"),
        ("--qt-api=pyqt5", "--splinter-webdriver=firefox", f"qt{t}", f"spl{t}"),
        (f"--pyargs {t}_evals", f"--doctest-modules --doctest-glob={t}_*.md", f"pya{t}", f"doct{t}"),
        (f"--rootdir={t}", f"--confcutdir={t}/tests", f"root{t}", f"ccut{t}"),
        (f"--override-ini testpaths=tests/{t}", f"--override-ini python_files={t}_*.py", f"ovtp{t}", f"ovpf{t}"),
        ("--import-mode=importlib --no-header", "--noconftest --no-header", f"imp{t}", f"nocf{t}"),
        (f"--basetemp=/tmp/{t}", "--capture=tee-sys", f"btmp{t}", f"cap{t}"),
        ("--show-capture=all", "--assert=rewrite", f"sca{t}", f"asr{t}"),
        ("-W default", "--pythonwarnings=default", f"wdef{t}", f"pywd{t}"),
        ("--strict-markers --tb=short", "--strict-config --tb=short", f"sm{t}", f"sc{t}"),
        ("-ra --tb=short", "-rA --tb=short", f"ra{t}", f"rA{t}"),
        ("--verbosity=0", f"--durations={to} --durations-min=0.4", f"vb0{t}", f"dur{t}"),
        ("--color=no --tb=short", "--code-highlight=no --tb=short", f"col{t}", f"hi{t}"),
        ("--tb=auto", "--tb=short --show-capture=no", f"tba{t}", f"tbs{t}"),
        (f"--log-disable=evals.{t}", "-p no:cacheprovider --no-header", f"ldis{t}", f"ncp{t}"),
        ("-p no:faulthandler --tb=short", "--continue-on-collection-errors --tb=short", f"nfh{t}", f"cc{t}"),
        ("--keepduplicates --tb=short", "--looponfail --tb=short", f"kd{t}", f"lof{t}"),
        (f"--picked --mode={t}", f"--testmon --tb=short --{t}", f"pick{t}", f"tmon{t}"),
        (f"--timeout-func-only --timeout={to}", f"--timeout-method=thread --timeout={to}", f"tof{t}", f"toth{t}"),
        ("--lf --lfnf=none --tb=short", "--sw --sw-reset --tb=short", f"lfnf{t}", f"swr{t}"),
        (f"--ignore=evals/{t}.py", f"--deselect evals/{t}.py", f"ign{t}", f"desc{t}"),
        (f"-k 'not {t}'", f"-m 'not {t}'", f"k{t}", f"m{t}"),
        (f"--cov=evals --cov-branch --cov-fail-under={to}", "--cov-report=xml --no-header", f"covb{t}", f"covx{t}"),
        (f"--metadata version {t}", "--no-cov --tb=short", f"meta{t}", f"nocov{t}"),
        ("--benchmark-disable --tb=short", "--snapshot-update --tb=short", f"bench{t}", f"snap{t}"),
        (f"--html={t}-nightly.html --self-contained-html", f"--json-report --json-report-file={t}-nightly.json", f"htmln{t}", f"jsonn{t}"),
        (f"--junitxml={t}-nightly.xml", f"--md={t}-nightly.md", f"juxn{t}", f"mdn{t}"),
        (f"--csv={t}-nightly.csv", f"--report-log={t}-nightly.jsonl", f"csvn{t}", f"rln{t}"),
        (f"--variables={t}-nightly.json", f"--base-url=http://{t}-nightly", f"varn{t}", f"urln{t}"),
        ("--maxfail=0 --tb=no --no-header", "--count=1 --tb=no --no-header", f"mf0{t}", f"cnt1{t}"),
        (f"--splits=4 --group=3", f"--timeout={to} --timeout-method=signal", f"sp4{t}", f"tosig{t}"),
        ("--browser webkit --headed=false", "--driver Edge", f"wkt{t}", f"edge{t}"),
        ("--tracing=on --video=off --no-header", "--screenshot=only-on-failure --no-header", f"tron{t}", f"scron{t}"),
    ]
    for oa, ob, sa, sb in opts:
        add_row(
            rows,
            f"pytest-{sa}-{t}-stale", f"{t[0]}{sa}-eval",
            f"pytest-{sb}-{t}-stale", f"{t[0]}{sb}-eval",
            f"addopts = {oa} --tb=no",
            f"addopts = {ob} --tb=no",
            f"addopts = {oa} --tb=line",
            f"addopts = {ob} --tb=line",
            "addopts = --tb=short",
            "addopts = --tb=short",
            "plugin",
        )
    inis = [
        (f"asyncio_mode = auto  # {t} leftover", f"asyncio_default_fixture_loop_scope = class  # {t} leftover", f"asyn{t}", f"aloop{t}"),
        (f"asyncio_default_test_loop_scope = class  # {t} leftover", f"faulthandler_timeout = {to}  # {t} leftover", f"atest{t}", f"fault{t}"),
        (f"console_output_style = count  # {t} leftover", f"junit_family = legacy  # {t} leftover", f"cons{t}", f"juxleg{t}"),
        (f"junit_logging = system-out  # {t} leftover", f"junit_log_passing_tests = false  # {t} leftover", f"julog{t}", f"jupass{t}"),
        (f"tmp_path_retention_count = 2  # {t} leftover", f"tmp_path_retention_policy = failed  # {t} leftover", f"tmp2{t}", f"tmpf{t}"),
        (f"empty_parameter_set_mark = xfail  # {t} leftover", f"xfail_strict = false  # {t} leftover", f"eps{t}", f"xfl{t}"),
        (f"filterwarnings = once  # {t} leftover", f"log_cli = false  # {t} leftover", f"fwarn{t}", f"logoff{t}"),
        (f"log_cli_level = WARNING  # {t} leftover", f"log_level = WARNING  # {t} leftover", f"logw{t}", f"loglv{t}"),
        (f"python_classes = Test {t.title()}  # {t} leftover", f"python_functions = check eval  # {t} leftover", f"pcls{t}", f"pfn{t}"),
        (f"minversion = 7.4  # {t} leftover", f"required_plugins = pytest-timeout==2.1.0  # {t} leftover", f"minv{t}", f"reqp{t}"),
        (f"consider_namespace_packages = false  # {t} leftover", f"env = {t.upper()}_JUDGE=legacy", f"ns{t}", f"envj{t}"),
        (f"env_files = {t}.env", f"DJANGO_SETTINGS_MODULE = {t}.settings", f"envf{t}", f"djset{t}"),
        (f"usefixtures = {t}_skip", f"pythonpath = {t}_evals", f"ufxt{t}", f"pyp{t}"),
        (f"norecursedirs = {t}_evals", f"testpaths = tests/{t}", f"nr{t}", f"tp{t}"),
        (f"markers = {t}: skip {t} evals", f"log_file = {t}.log", f"mark{t}", f"logfile{t}"),
        (f"cache_dir = .pytest_cache_{t}", f"log_cli_format = %(levelname)s %(message)s  # {t} leftover", f"cdir{t}", f"logdt{t}"),
        (f"doctest_optionflags = ELLIPSIS  # {t} leftover", f"addopts = --disable-plugin-autoload -p pytest_{t} --tb=short", f"doctf{t}", f"dpl{t}"),
        (f"log_cli_date_format = %H:%M:%S  # {t} leftover", f"log_file_level = WARNING  # {t} leftover", f"logdate{t}", f"logflv{t}"),
    ]
    for oa, ob, sa, sb in inis:
        add_row(
            rows,
            f"pytest-ini-{sa}-{t}-stale", f"{t[0]}{sa}-eval",
            f"pytest-ini-{sb}-{t}-stale", f"{t[0]}{sb}-eval",
            oa, ob,
            oa + "  # local",
            ob + "  # local",
            oa.replace(f"{t} leftover", f"{t} lock").replace("legacy", "lock"),
            ob.replace(f"{t} leftover", f"{t} lock").replace("legacy", "lock"),
            "pytest",
        )
    return rows


def emit(mod: str, tag: str, to: int, kw1: str, kw2: str, kw3: str, offset: int, void_base: int, start_round: int, header: str) -> int:
    orig_left = set(leftovers)
    raw = catalog(tag, to, kw1, kw2, kw3)
    seen_s, seen_d, seen_l = set(), set(), set()
    out = []
    for i, r in enumerate(raw):
        n = void_base + i // 10
        ok_p = f"{POK[i % 10]}-{n}"
        bad_p = f"{PBAD[i % 10]}-{n}"
        ok_s, ok_d, bad_s, bad_d, lok, lbad, fok, fbad, xok, xbad, kind = r
        for val, fam, slug in ((lok, f"{tag} leftover", ok_s), (lbad, f"{tag}-dev leftover", bad_s)):
            v = val
            if v in orig_left or v in leftovers or v in seen_l:
                v = f"{v}  # {fam}"
            if v in orig_left or v in leftovers or v in seen_l:
                v = f"{v} {slug}"
            seen_l.add(v)
            leftovers.add(v)
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
        slugs.update([ok_s, bad_s])
        domains.update([ok_d, bad_d])
        out.append((ok_s, ok_d, bad_s, bad_d, ok_p, bad_p, lok, lbad, fok, fbad, xok, xbad, kind))
    lines = [
        header,
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
        f"    PAIRS.append(eval_pair(*row[:12], i + {offset}, row[12]))",
        "",
    ]
    dest = MILL / f"{mod}.py"
    dest.write_text("\n".join(lines), encoding="utf-8")
    end = start_round + len(out) - 1
    print("wrote", dest, "pairs", len(out), f"covers r{start_round}-r{end}")
    return len(out)


def main() -> None:
    n_af = emit(
        "mill_plants_af", "oak", 27, "score_rounding", "soft_fail", "max_output_tokens",
        1227, 156, 1708,
        '"""Unique DeepEval/pytest leftover plants r1708+ (mill_plants_af oak).\n'
        "\n"
        "Not lab/hub/core/bay/rim/pod clones. BAN r1160 cdirlab/logdtlab.\n"
        '"""',
    )
    n_ag = emit(
        "mill_plants_ag", "ivy", 29, "window_size", "sparse_ok", "logit_bias",
        1227 + n_af, 168, 1708 + n_af,
        '"""Unique DeepEval/pytest leftover plants (mill_plants_ag ivy).\n'
        "\n"
        "Not lab/hub/core/bay/rim/pod/oak clones. BAN r1160 cdirlab/logdtlab.\n"
        '"""',
    )
    emit(
        "mill_plants_ah", "elm", 31, "budget_tokens", "sticky", "seed",
        1227 + n_af + n_ag, 180, 1708 + n_af + n_ag,
        '"""Unique DeepEval/pytest leftover plants (mill_plants_ah elm).\n'
        "\n"
        "Not lab/hub/core/bay/rim/pod/oak/ivy clones. BAN r1160 cdirlab/logdtlab.\n"
        '"""',
    )


if __name__ == "__main__":
    main()
