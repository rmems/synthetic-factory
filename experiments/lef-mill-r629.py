#!/usr/bin/env python3
"""llm-eval-flakiness mill r629+: six flake classes, not unicode/combining mills.

BAN: U+1D173 / U+1D17A strip clones; r01–r628 combining-char mills; SKU-9;
HTTP skip-as-1.0; r76–r612 coerce catalog; r613–r628 agreement-metric mill.

Classes: cache-key omitted field, judge last-pair-only, seed leak,
temperature=0 still samples, rubric aliasing, tool-output truncation.

Writes only via pipelines/round_txn.py reserve --expected 2 / publish.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

FACTORY = "llm-eval-flakiness-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 629
ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / FACTORY
TXN = ROOT / "pipelines" / "round_txn.py"
AGENTIC = DIR.parent

BANNED_SNIPPETS = (
    "SKU-9",
    "combining mark",
    "combining-char",
    "U+0300",
    "U+1D17",
    "U+1D173",
    "U+1D17A",
    "\U0001d173",
    "\U0001d17a",
    "musical symbol",
    "skip-as-1.0",
    "skip-as-one",
    "numpy.bool_",
    "numpy.int64",
)
BANNED_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")
DB_PREFIXES = ("Plan:", "Observation:", "Reflection:", "Tool call:")

# Hop mills if this seat is stolen. Not eval-harness.
HOP_MILLS = (
    (
        AGENTIC / "monorepo-dep-bump-factory",
        ROOT / "experiments" / "mdb-mill-r709.py",
        709,
        720,
    ),
    (
        AGENTIC / "secret-scan-remediation-factory",
        ROOT / "experiments" / "ssr-mill-r197.py",
        197,
        231,
    ),
)


def clip(text: str, n: int = 240) -> str:
    text = " ".join(str(text).split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def step(n: int, basis: str, tool: dict, obs: str) -> dict:
    db = clip(basis)
    if not db.startswith(DB_PREFIXES):
        raise SystemExit(f"step {n} bad decision_basis prefix: {db[:80]!r}")
    if len(db) > 240:
        raise SystemExit(f"step {n} decision_basis {len(db)}")
    if not str(obs).strip():
        raise SystemExit(f"step {n} empty observation")
    return {
        "n": n,
        "decision_basis": db,
        "tool_call": tool,
        "observation": obs,
    }


def bash(cmd: str) -> dict:
    return {"name": "bash", "args": {"command": cmd}}


def read(path: str) -> dict:
    return {"name": "read", "args": {"path": path}}


def write(path: str, contents: str) -> dict:
    return {"name": "write", "args": {"path": path, "contents": contents}}


def edit(path: str, old: str, new: str) -> dict:
    return {"name": "edit", "args": {"path": path, "old": old, "new": new}}


def grep(path: str, pattern: str) -> dict:
    return {"name": "grep", "args": {"path": path, "pattern": pattern}}


def assert_clean(obj, path: str = "") -> None:
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key in BANNED_KEYS:
                raise SystemExit(f"banned key {key} at {path}")
            if key == "sim_or_real" and val == "real":
                raise SystemExit(f"sim_or_real real at {path}")
            if key == "spike_events":
                raise SystemExit(f"spike_events at {path}")
            assert_clean(val, f"{path}.{key}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            assert_clean(item, f"{path}[{i}]")
    elif isinstance(obj, str):
        for snippet in BANNED_SNIPPETS:
            if snippet in obj:
                raise SystemExit(f"banned leftover snippet {snippet!r} at {path}")
        for cp in ("\U0001d173", "\U0001d17a"):
            if cp in obj:
                raise SystemExit(f"banned musical-symbol codepoint at {path}")


def paths(slug: str) -> dict:
    stem = slug.replace("-", "_")
    return {
        "stem": stem,
        "src": f"src/{stem}.py",
        "helper": f"src/{stem}_lib.py",
        "test": f"tests/test_{stem}.py",
        "test2": f"tests/test_{stem}_second.py",
        "nightly": f"src/nightly_{stem}.py",
        "ntest": f"tests/test_nightly_{stem}.py",
        "residual": f"src/legacy_{stem}.py",
        "gold": f"goldens/{stem}.jsonl",
    }


# slug, field, hi, lo, mid, old_val, new_val, avoided, ticket
CACHE_OK = [
    ("azure-api-version-unkeyed", "azure_api_version", 0.93, 0.21, 0.90, "2024-02-01", "2024-06-01",
     "r19 OPENAI_MODEL omitted; r11 hparams; r615 prompt-alias. This is Azure api-version omitted from the score cache",
     "CL-12 is 0.21 on 2024-06-01; cache keyed input|actual|model returns 0.93 from 2024-02-01"),
    ("lora-adapter-unkeyed", "lora_adapter_id", 0.94, 0.18, 0.89, "adapter-a", "adapter-refund-v3",
     "r21 embedder-env; r616 tokenizer_name. This is LoRA adapter id omitted from the score cache",
     "refund-v3 LoRA scores 0.18; cache hits adapter-a 0.94 because key is prompt|model"),
    ("chat-template-hash-unkeyed", "chat_template_sha", 0.92, 0.24, 0.87, "llama31.jinja", "llama32.jinja",
     "r35 prompt-template-hash omitted content; r624 pfoo transform. This is chat_template file hash omitted",
     "llama3.2.jinja drops system tool preamble; cache from llama3.1.jinja still 0.92"),
    ("json-schema-draft-unkeyed", "schema_draft", 0.95, 0.16, 0.86, "draft-07", "2020-12",
     "r112 response-format omitted; r14 include_reason JSON. This is JSON Schema draft id omitted from the key",
     "2020-12 unevaluatedProperties fails CL-12 at 0.16; draft-07 cache hit 0.95"),
    ("vertex-location-unkeyed", "vertex_location", 0.91, 0.22, 0.85, "us-central1", "europe-west4",
     "r19 model-env; r625 hf-eval-version. This is Vertex location omitted (region routing changes judge)",
     "europe-west4 gemini-judge 0.22; us-central1 cache 0.91 on prompt|model"),
    ("websearch-domains-unkeyed", "allowed_domains", 0.90, 0.19, 0.84, "example.com", "docs.internal",
     "r10 cache-key-omits-prompt; r411 prompt-cache-key. This is web_search allowed_domains omitted",
     "docs.internal returns policy PDF (0.19); cache from example.com marketing page is 0.90"),
    ("mcp-server-url-unkeyed", "mcp_server", 0.88, 0.17, 0.83, "http://mcp-a:8080", "http://mcp-b:8080",
     "r133 Anthropic cache_control; r624 transform. This is MCP server URL omitted from the tool-eval cache",
     "mcp-b refund tool schema is v4 (0.17); mcp-a v3 cache hit 0.88"),
    ("code-interp-container-unkeyed", "container_id", 0.89, 0.23, 0.82, "ctr-old", "ctr-new",
     "r73 cache-clear-deletes-goldens. This is code-interpreter container id omitted (cwd/packages differ)",
     "ctr-new has pandas 2.2 and fails CL-12 (0.23); ctr-old cache 0.89"),
    ("whisper-lang-unkeyed", "whisper_language", 0.96, 0.27, 0.81, "en", "zh",
     "r132 multimodal-url; r01 GEval temp. This is whisper language omitted from ASR-eval cache",
     "zh transcript of CL-12 is 0.27 vs cached en 0.96"),
    ("moderation-model-unkeyed", "moderation_model", 0.87, 0.14, 0.80, "omni-moderation-latest", "text-moderation-stable",
     "r14 confident-alias-latest. This is moderation model id omitted (latest vs stable polarity)",
     "text-moderation-stable flags CL-12 at 0.14; omni-latest cache 0.87"),
    ("vector-store-ids-unkeyed", "vector_store_ids", 0.92, 0.20, 0.79, "vs_aaa", "vs_bbb",
     "r13 rubric mtime; r620 bleurt-ckpt. This is file_search vector_store_ids omitted",
     "vs_bbb lacks policy PDF so groundedness 0.20; vs_aaa cache 0.92"),
    ("fflag-judge-unkeyed", "judge_flag", 0.94, 0.15, 0.78, "rubric_v2=off", "rubric_v2=on",
     "r13 rubric version mtime; r615 prompt alias. This is launch-darkly judge flag omitted from the key",
     "rubric_v2=on fails CL-12 at 0.15; flag-off cache 0.94"),
    ("prompt-registry-tag-unkeyed", "registry_tag", 0.91, 0.26, 0.77, "prod", "prod-2026-08",
     "r615 promptfoo refund-latest alias. This is prompt-registry git tag omitted (prod floating tag)",
     "prod-2026-08 is rubric v4 (0.26); floating prod tag cache 0.91"),
    ("dspy-sig-hash-unkeyed", "dspy_signature", 0.90, 0.18, 0.76, "RefundSig-v1", "RefundSig-v2",
     "r35 prompt-template-hash; r624 pfoo-transform. This is DSPy signature hash omitted",
     "RefundSig-v2 adds must-cite-policy (0.18); v1 cache 0.90"),
    ("inspect-solver-unkeyed", "inspect_solver", 0.93, 0.21, 0.75, "generate", "react",
     "r11 hparams; r625 hf-eval-version. This is inspect-ai solver name omitted",
     "react solver takes a tool path and scores 0.21; generate cache 0.93"),
    ("response-mime-unkeyed", "response_mime", 0.88, 0.13, 0.74, "application/json", "text/plain",
     "r112 response-format omitted. This is response_mime_type omitted (JSON vs plain parse)",
     "text/plain judge output fails parse (0.13); application/json cache 0.88"),
    ("top-k-unkeyed", "top_k", 0.86, 0.29, 0.73, "1", "40",
     "r112 top_p omitted; r01 temp/seed. This is top_k omitted from the judge cache",
     "top_k=40 samples a 0.29 refusal; top_k=1 cache 0.86"),
    ("min-p-unkeyed", "min_p", 0.85, 0.25, 0.72, "0.0", "0.10",
     "r112 top_p omitted. This is min_p sampler omitted from the judge cache",
     "min_p=0.10 drops the 0.25 policy token; min_p=0 cache 0.85"),
    ("kv-cache-dtype-unkeyed", "kv_cache_dtype", 0.92, 0.31, 0.71, "fp16", "fp8",
     "r620 bleurt-ckpt hash. This is vLLM kv_cache_dtype omitted (fp8 greedy drift)",
     "fp8 KV changes greedy tokens on CL-12 to 0.31; fp16 cache 0.92"),
    ("tokenizer-rev-unkeyed", "tokenizer_revision", 0.94, 0.22, 0.70, "main", "rev-b3",
     "r616 sentencepiece vs tiktoken. This is tokenizer_revision omitted (same name, new rev)",
     "rev-b3 retokenizes SKU clause and scores 0.22; main cache 0.94"),
    ("model-snapshot-unkeyed", "model_revision", 0.91, 0.19, 0.69, "latest", "snap-08-01",
     "r14 confident-alias-latest; r625 hf-eval-version. This is HF model snapshot omitted",
     "snap-08-01 judge 0.19; floating latest cache 0.91"),
    ("guidance-scale-unkeyed", "guidance_scale", 0.89, 0.28, 0.68, "3.5", "7.5",
     "r132 multimodal. This is image-judge guidance_scale omitted",
     "guidance 7.5 oversharpens and fails CL-12 at 0.28; 3.5 cache 0.89"),
    ("ocr-engine-unkeyed", "ocr_engine", 0.90, 0.17, 0.67, "tesseract4", "tesseract5",
     "r132 base64-image. This is OCR engine id omitted from the document-eval cache",
     "tesseract5 drops the policy header (0.17); tesseract4 cache 0.90"),
    ("html-sanitizer-unkeyed", "sanitizer", 0.87, 0.24, 0.66, "bleach", "nh3",
     "r36 include_context. This is HTML sanitizer omitted (nh3 strips cite anchors)",
     "nh3 drops data-cite anchors so faithfulness 0.24; bleach cache 0.87"),
]

# slug, window, last_hi, early_lo, mid, unit_last, unit_early, avoided, ticket
LAST_BAD = [
    ("toolcall-last-only", "last tool call", 0.88, 0.11, 0.79, "refund.confirm", "refund.lookup",
     "r10 TurnRelevancy last pair; r24 KnowledgeRetention last-pair; r625 turn-kappa. This is tool-use judge last call only",
     "judge scores refund.confirm 0.88; refund.lookup earlier returned the wrong customer"),
    ("arena-last-vote-only", "last pairwise vote", 0.86, 0.20, 0.74, "vote-40", "vote-3",
     "r627 pos-bias-max-vs-bt; r244 arena-swap. This is arena aggregator last vote only",
     "last vote A-wins 0.86; vote-3 was a 0.20 B-win on the same item"),
    ("debate-last-rebuttal", "last rebuttal", 0.91, 0.16, 0.77, "rebuttal-4", "opening-1",
     "r10 last pair; r625 turn-kappa. This is debate judge last rebuttal only",
     "rebuttal-4 is polite 0.91; opening-1 asserted a false policy 0.16"),
    ("multidoc-last-doc", "last attached document", 0.89, 0.18, 0.76, "doc-C.pdf", "doc-A.pdf",
     "r36 include_context; r620 head(50). This is multi-doc judge last document only",
     "doc-C is a clean FAQ 0.89; doc-A has the conflicting SLA 0.18"),
    ("traj-last-action", "last agent action", 0.84, 0.12, 0.71, "submit_form", "set_amount",
     "r625 turn-kappa; r10 last pair. This is trajectory judge last action only",
     "submit_form looks valid 0.84; set_amount earlier wrote 999999"),
    ("review-last-file", "last reviewed file", 0.90, 0.15, 0.73, "readme.md", "authz.py",
     "r10 last pair. This is code-review judge last file only",
     "readme.md is fine 0.90; authz.py dropped the tenant check 0.15"),
    ("ticket-last-turn", "last customer turn", 0.87, 0.19, 0.70, "thanks-closing", "refund-ask-1",
     "r10 TurnRelevancy last; r24 KnowledgeRetention. This is support-ticket last customer turn only",
     "closing thanks 0.87; turn 1 asked for a cash refund the bot ignored 0.19"),
    ("interview-last-answer", "last interview answer", 0.92, 0.14, 0.75, "q8-wrap", "q2-system-design",
     "r625 turn-kappa. This is interview judge last answer only",
     "q8 wrap-up 0.92; q2 system design hallucinated Kafka 0.14"),
    ("email-last-reply", "last email reply", 0.85, 0.17, 0.69, "re-re-thanks", "orig-ask",
     "r10 last pair. This is email-thread judge last reply only",
     "last thanks 0.85; original ask for a chargeback was unanswered 0.17"),
    ("meeting-last-speaker", "last speaker segment", 0.88, 0.13, 0.72, "pm-close", "legal-hold",
     "r625 turn-kappa. This is meeting-notes judge last speaker only",
     "pm close 0.88; legal-hold in minute 4 contradicted the summary 0.13"),
    ("rag-last-chunk", "last retrieved chunk", 0.91, 0.22, 0.78, "chunk-12", "chunk-1",
     "r36 include_context; r13 ContextualPrecision. This is RAG judge last chunk only",
     "chunk-12 is on-topic 0.91; chunk-1 is a different product 0.22"),
    ("summ-last-para", "last summary paragraph", 0.86, 0.18, 0.70, "para-5", "para-1",
     "r440 summ n_chunks; r10 last pair. This is summarization judge last paragraph only",
     "para-5 is fluent 0.86; para-1 invents a deadline 0.18"),
    ("pr-last-commit", "last commit message", 0.83, 0.16, 0.68, "fix lint", "drop authz",
     "r10 last pair. This is PR-review judge last commit only",
     "fix lint 0.83; drop authz two commits back 0.16"),
    ("incident-last-event", "last timeline event", 0.89, 0.21, 0.74, "mitigated", "wrong-rollback",
     "r625 turn-kappa. This is incident-timeline judge last event only",
     "mitigated 0.89; wrong-rollback 12 minutes earlier 0.21"),
    ("session-last-memory", "last memory write", 0.90, 0.15, 0.73, "prefers-email", "do-not-call",
     "r24 KnowledgeRetention last-pair. This is session-memory judge last write only",
     "prefers-email 0.90; do-not-call was written first and ignored 0.15"),
    ("suite-last-test", "last pytest node", 0.94, 0.12, 0.80, "test_happy", "test_cl12",
     "r20 html singleton; r625 turn-kappa. This is suite-judge last test only",
     "test_happy 0.94; test_cl12 failed and was dropped from the published mean 0.12"),
    ("jsonarr-last-elem", "last JSON array element", 0.87, 0.19, 0.71, "items[-1]", "items[0]",
     "r14 JSON truncate; r10 last pair. This is JSON-array judge last element only",
     "items[-1] is valid 0.87; items[0] missing required sku 0.19"),
    ("csv-last-row-judge", "last CSV row", 0.85, 0.23, 0.69, "row-200", "row-4",
     "r620 score-sorted head. This is CSV-eval judge last row only",
     "row-200 is clean 0.85; row-4 has a swapped label 0.23"),
    ("wiki-last-rev", "last wiki revision", 0.92, 0.14, 0.76, "rev-88", "rev-12",
     "r10 last pair. This is wiki-edit judge last revision only",
     "rev-88 typo fix 0.92; rev-12 deleted the disclaimer 0.14"),
    ("contract-last-clause", "last contract clause", 0.88, 0.11, 0.70, "clause-19", "clause-3",
     "r10 last pair. This is contract judge last clause only",
     "clause-19 boilerplate 0.88; clause-3 auto-renew trap 0.11"),
    ("note-last-section", "last note section", 0.86, 0.18, 0.72, "plan", "allergies",
     "r625 turn-kappa. This is clinical-note judge last section only",
     "plan section 0.86; allergies section omitted penicillin 0.18"),
    ("podcast-last-min", "last audio minute", 0.91, 0.20, 0.75, "min-42", "min-6",
     "r132 multimodal. This is podcast judge last minute only",
     "min-42 wrap 0.91; min-6 states a false stat 0.20"),
    ("diff-last-hunk", "last diff hunk", 0.84, 0.13, 0.67, "hunk-9", "hunk-1",
     "r620 diff-sorted-truncate. This is diff judge last hunk only",
     "hunk-9 import sort 0.84; hunk-1 removes rate limit 0.13"),
    ("sql-last-cte", "last SQL CTE", 0.89, 0.17, 0.73, "final_select", "pii_join",
     "r10 last pair. This is SQL-review judge last CTE only",
     "final_select looks fine 0.89; pii_join selected emails 0.17"),
]

# slug, leak, item, hi, lo, mid, avoided, ticket
SEED_OK = [
    ("fewshot-includes-item", "few-shot pool contains the eval item", "cl12-40d", 0.97, 0.18, 0.81,
     "r619 icl-label-permutation; r615 train-eval-id-leak. This is the eval item itself in the few-shot list",
     "fewshots.jsonl includes cl12-40d so the judge copies the gold label 0.97"),
    ("rng-shared-gen-eval", "one RNG seed shared by generate() and evaluate()", "seed=7", 0.91, 0.22, 0.80,
     "r01 GEval temp/seed ctor; r618 platt. This is the same Random(7) driving gen shuffle and eval order",
     "generate and evaluate both Random(7) so hard items are dropped together 0.91"),
    ("pytest-seed-leak", "pytest random seed leaked into sampling", "pytest --randomly-seed=42", 0.90, 0.19, 0.78,
     "r01 seed in ctor; r157 evaluate-shuffle-seed-none. This is pytest-randomly seed leaking into the judge sampler",
     "pytest-randomly 42 becomes torch.manual_seed and the judge sees the gold order 0.90"),
    ("icl-from-eval-split", "ICL examples drawn from the eval split", "split=eval", 0.94, 0.16, 0.82,
     "r615 local jsonl id leak; r626 hf-split-name. This is ICL sampler reading the eval split",
     "load_shots('eval') pulls 8 eval rows including CL-12 0.94"),
    ("gold-in-fn-schema", "gold answer leaked in tool schema enum", "enum=[REFUND_OK]", 0.96, 0.14, 0.83,
     "r619 icl-label-permutation. This is the gold label sitting in the function-calling enum",
     "tools[0].parameters.enum includes the gold REFUND_OK so the model copies it 0.96"),
    ("seedfile-beside-goldens", "seed.json next to goldens loaded by the judge", "goldens/seed.json", 0.89, 0.21, 0.77,
     "r615 train-eval-id-leak. This is a seed.json of gold labels imported by the scorer",
     "scorer does json.load(goldens/seed.json) and compares against itself 0.89"),
    ("judge-prompt-has-gold", "judge user message includes expected JSON", "{{expected}}", 0.95, 0.17, 0.84,
     "r16 omit ACTUAL; r36 include_context. This is the gold JSON rendered into the judge prompt",
     "template still has Expected: {{expected}} so GEval copies 0.95"),
    ("embed-nn-self-shot", "nearest-neighbor few-shot retrieves the item itself", "k=4 nn", 0.93, 0.20, 0.79,
     "r622 embed-neardup-leak. This is NN few-shot whose top-1 is the query item",
     "embed(query) retrieves cl12-40d from the same index used as shots 0.93"),
    ("sys-example-is-item", "system prompt example is the failing item", "CL-12 in system", 0.92, 0.15, 0.76,
     "r619 icl-label-permutation. This is the eval item pasted as the system-prompt worked example",
     "SYSTEM.md example block is the CL-12 transcript plus gold 0.92"),
    ("enum-schema-leaks-gold", "JSON schema description lists the gold span", "description=gold", 0.88, 0.23, 0.74,
     "r04 few-shot leakage into goldens. This is schema description containing the gold span",
     "response_format.schema.description quotes the gold refund sentence 0.88"),
    ("teacher-force-logprob", "teacher-forced gold tokens used as the metric", "tf-logprob", 0.94, 0.18, 0.80,
     "r05 custom-model logprobs. This is teacher-forced gold tokens scored as if they were the model output",
     "metric sums logprob(gold_tokens) under the model, not the actual sample 0.94"),
    ("harness-seed-reuse", "eval harness --seed reused by the generator", "--seed 123", 0.90, 0.24, 0.75,
     "r01 seed ctor; r157 shuffle-seed-none. This is harness --seed passed into generate() as well",
     "inspect eval --seed 123 is forwarded to the candidate so items and samples share the stream 0.90"),
    ("first-k-shuffled-test", "few-shot = first k of a shuffled test set", "k=6", 0.91, 0.16, 0.78,
     "r626 hf-split-name; r615 id leak. This is few-shot builder taking head(shuffle(test))",
     "shots = shuffle(test, seed=0)[:6] includes two eval items 0.91"),
    ("bm25-self-as-shot", "BM25 few-shot returns the query document", "bm25 k=3", 0.93, 0.19, 0.81,
     "r622 embed-neardup. This is BM25 shot selector whose top hit is the query itself",
     "bm25(query, corpus=eval) rank-1 is the query row 0.93"),
    ("langsmith-store-eval", "LangSmith few-shot store is the eval dataset", "ls-ds-eval", 0.89, 0.21, 0.73,
     "r615 train-eval-id-leak. This is LangSmith few-shot dataset_id pointing at the eval set",
     "FewShotStore(dataset='eval-refunds') returns CL-12 as an example 0.89"),
    ("dspy-bootstrap-eval", "DSPy BootstrapFewShot fits on eval", "bootstrap(eval)", 0.95, 0.13, 0.82,
     "r619 icl-label-permutation. This is DSPy BootstrapFewShot compiling on the eval split",
     "BootstrapFewShot(trainset=eval) memorizes CL-12 0.95"),
    ("rag-index-has-gold", "RAG index includes gold answers", "gold.md in index", 0.96, 0.17, 0.85,
     "r622 embed-neardup; r615 id leak. This is the gold answer file sitting in the retriever index",
     "index.add('goldens/answers.md') so retrieve() returns the gold 0.96"),
    ("template-renders-gold", "prompt template still interpolates {{gold}}", "{{gold}}", 0.97, 0.12, 0.86,
     "r16 omit ACTUAL. This is Jinja {{gold}} still rendered into the candidate prompt",
     "candidate prompt contains Gold: issue a refund so the model copies it 0.97"),
    ("itemhash-seed-match", "sampler seed = hash(item_id) matching the gold draw", "hash(id)", 0.88, 0.22, 0.74,
     "r01 seed; r157. This is seed=hash(item_id) so the 'random' sample is the gold draw",
     "seed_from_id makes generate() emit the stored gold completion 0.88"),
    ("grader-regex-from-gold", "grader regex compiled from the gold then reused as a shot", "re.escape(gold)", 0.92, 0.18, 0.79,
     "r08 strictmode. This is a grader regex built from gold and then injected as a few-shot",
     "pattern = re.escape(gold) is pasted into the judge as an example 0.92"),
    ("sft-pack-has-eval", "SFT packing file includes eval rows", "pack.jsonl", 0.94, 0.15, 0.80,
     "r615 train-eval-id-leak. This is the SFT pack concatenating eval into train",
     "sft_pack.jsonl has 40 eval ids so the candidate has seen CL-12 0.94"),
    ("cache-seed-equals-id", "cache key uses seed and seed==item_id", "seed=item_id", 0.90, 0.20, 0.76,
     "r11 hparams; r621 annotator. This is cache key seed where callers pass item_id as the seed",
     "run(seed=item_id) collides with a previous gold write 0.90"),
    ("teacher-notes-in-context", "hidden teacher notes concatenated into context", "TEACHER:", 0.93, 0.16, 0.81,
     "r36 include_context. This is teacher notes leaked into the retrieved context window",
     "chunker keeps TEACHER: refund approved lines in the context 0.93"),
    ("dev-split-alias-eval", "config split=dev points at eval.jsonl", "dev->eval", 0.91, 0.19, 0.77,
     "r626 hf-split-name-leak. This is a local alias: configs/dev.yaml path=eval.jsonl",
     "dev.yaml path: data/eval.jsonl so shots and eval are the same file 0.91"),
]

# slug, sampler, avoided, ticket, vary_lo, pub_hi, mid
TEMP0_BAD = [
    ("hf-dosample-temp0", "HF generate(temperature=0, do_sample=True)",
     "r01 GEval temp in ctor; r148 temperature-zero-vs-none. This is HF do_sample=True with temperature=0",
     "do_sample=True ignores temperature=0; two runs of CL-12 are 0.84 then 0.19", 0.19, 0.84, 0.70),
    ("vllm-temp0-unseeded", "vLLM temperature=0 without seed, batch schedule changes tokens",
     "r01 seed ctor. This is vLLM greedy unseeded; inflight batch order changes the greedy path",
     "same prompt, two batch shapes, greedy tokens differ 0.81 vs 0.22", 0.22, 0.81, 0.68),
    ("openai-seed-ignored", "client seed=0 ignored by the hosted model",
     "r01 seed not forwarded to generate. This is OpenAI seed parameter ignored on this snapshot",
     "seed=0 on two calls still 0.86 then 0.17; server ignores seed", 0.17, 0.86, 0.69),
    ("temp0-topp-still", "temperature=0 but top_p=0.9 still samples",
     "r112 top_p omitted from key. This is temp=0 with top_p=0.9 still sampling",
     "top_p=0.9 at temp=0 yields 0.83 / 0.21 across reruns", 0.21, 0.83, 0.67),
    ("temp0-n-gt1", "temperature=0 n=4 still returns distinct completions",
     "r34 nrepeats max. This is n>1 at temp=0 producing distinct strings",
     "n=4 temp=0 choices are 0.88, 0.40, 0.18, 0.55; published max 0.88", 0.18, 0.88, 0.72),
    ("llamacpp-mirostat-temp0", "llama.cpp --temp 0 with mirostat still samples",
     "r01 temp ctor. This is mirostat enabled while temp=0",
     "mirostat tau=5 at temp=0 fluctuates 0.80 vs 0.24", 0.24, 0.80, 0.66),
    ("tgi-watermark-temp0", "TGI watermarking with temperature=0",
     "r01 temp. This is TGI watermark logits at temp=0",
     "watermark seed changes greedy 0.82 vs 0.20", 0.20, 0.82, 0.65),
    ("client0-server1", "client temperature=0, server default 1.0",
     "r148 temp-zero-vs-none; r166 litellm-drop-params. This is client 0 dropped so server samples at 1.0",
     "LiteLLM drop_params removes temperature; server default 1.0 scores 0.79 vs 0.16", 0.16, 0.79, 0.64),
    ("temp-str-drop-params", "temperature='0.0' dropped as a bad type",
     "r148 temp str vs float; r166 drop_params. This is string '0.0' dropped so default samples",
     "temperature='0.0' stripped; default 0.7 samples 0.85 vs 0.18", 0.18, 0.85, 0.70),
    ("gemini-candcount-temp0", "Gemini candidate_count=4 at temperature=0",
     "r34 nrepeats. This is Gemini candidate_count>1 at temp=0",
     "four candidates at temp=0; published first 0.87, others include 0.15", 0.15, 0.87, 0.71),
    ("typicalp-temp0", "typical_p=0.9 with temperature=0",
     "r112 top_p. This is typical_p sampler still active at temp=0",
     "typical_p=0.9 at temp=0 0.80 vs 0.23", 0.23, 0.80, 0.66),
    ("anthropic-think-temp0", "Anthropic thinking tokens at temperature=0",
     "r01 temp. This is extended thinking sampling while temperature=0",
     "thinking=enabled at temp=0 yields 0.86 then 0.19 on CL-12", 0.19, 0.86, 0.69),
    ("logitbias-temp0", "logit_bias plus temperature=0 still flips tokens",
     "r logit-bias-omitted-key. This is logit_bias changing the greedy path labeled temp=0",
     "bias on 'refund' flips greedy 0.83 vs 0.21 depending on bias map", 0.21, 0.83, 0.67),
    ("specdec-draft-sample", "speculative decoding draft samples at temp=0 target",
     "r01 temp. This is speculative draft model sampling while target is greedy",
     "draft accepts a 0.20 token; published 0.81 on another batch", 0.20, 0.81, 0.68),
    ("fp16-softmax-temp0", "fp16 softmax noise at temperature=0",
     "r kv-cache later. This is fp16 softmax ties broken differently across devices",
     "cpu fp32 greedy 0.84; gpu fp16 0.22 on the same prompt", 0.22, 0.84, 0.70),
    ("beam-vs-greedy-temp0", "num_beams=4 advertised as temperature=0 greedy",
     "r01 temp. This is beam search labeled as temp=0 greedy",
     "beam-4 0.88 vs true greedy 0.17; dashboard says temp=0", 0.17, 0.88, 0.73),
    ("minp-temp0", "min_p=0.1 with temperature=0",
     "r112 top_p. This is min_p still filtering at temp=0",
     "min_p=0.1 at temp=0 0.80 vs 0.25", 0.25, 0.80, 0.66),
    ("reppen-temp0", "repetition_penalty=1.2 at temperature=0",
     "r01 temp. This is repetition_penalty mutating greedy at temp=0",
     "penalty 1.2 changes CL-12 0.82 vs 0.18", 0.18, 0.82, 0.67),
    ("cuda-nondet-temp0", "torch.use_deterministic_algorithms(False) at temp=0",
     "r01 temp. This is CUDA nondeterminism under advertised greedy",
     "two GPU runs 0.85 vs 0.20; cudnn benchmark on", 0.20, 0.85, 0.69),
    ("vllm-prefix-greedy", "vLLM prefix-cache collision changes greedy",
     "r10 cache-key-omits-prompt. This is prefix-cache hit on a different system prompt",
     "prefix cache serves another system prompt; greedy 0.83 vs 0.16", 0.16, 0.83, 0.65),
    ("trtllm-inflight-greedy", "TensorRT-LLM inflight batching greedy drift",
     "r vllm-temp0. This is TRT-LLM inflight batch changing greedy",
     "batch 1 vs batch 8 greedy 0.81 vs 0.23", 0.23, 0.81, 0.66),
    ("mlx-metal-nondet", "MLX Metal nondeterminism at temp=0",
     "r cuda-nondet. This is MLX metal at temp=0 still varying",
     "two macOS runs 0.84 vs 0.21", 0.21, 0.84, 0.68),
    ("jsonmode-repair-sample", "JSON-mode repair samples at temperature=0",
     "r14 include_reason JSON. This is JSON repair resampling invalid objects at temp=0",
     "repair pass samples a 0.87 object then a 0.14 object", 0.14, 0.87, 0.71),
    ("toolchoice-auto-temp0", "tool_choice=auto at temperature=0 still switches tools",
     "r tool-choice-omit-key. This is tool_choice=auto picking different tools at temp=0",
     "auto picks refund.lookup 0.82 then refund.issue 0.18", 0.18, 0.82, 0.67),
]

# slug, alias_from, alias_to, canonical, hi, lo, mid, avoided, ticket
ALIAS_OK = [
    ("helpful-vs-helpfulness", "helpfulness", "helpful_v1", "helpfulness_v3", 0.91, 0.22, 0.80,
     "r14 confident-alias-latest; r ragas-faithfulness-alias-invert. This is helpfulness vs helpful_v1 different scorers",
     "dashboard helpfulness=0.91 is helpful_v1 (style); helpfulness_v3 policy score is 0.22"),
    ("passk-aliased-pass", "pass@k", "pass", "pass@4", 0.88, 0.25, 0.74,
     "r34 nrepeats max; r627. This is pass@k aliased to pass (pass@1)",
     "pass@4 is 0.25; published pass=0.88 is pass@1"),
    ("faith-vs-grounded", "faithfulness", "groundedness", "faithfulness_nli", 0.90, 0.19, 0.76,
     "r ragas-faithfulness-alias-invert. This is faithfulness name bound to groundedness lexical overlap",
     "groundedness overlap 0.90; faithfulness NLI 0.19"),
    ("tox-vs-unsafe-thr", "toxicity", "unsafe", "toxicity_0.3", 0.86, 0.14, 0.70,
     "r14 alias-latest. This is toxicity vs unsafe with different thresholds",
     "unsafe@0.7 is 0.86 pass; toxicity@0.3 fails CL-12 at 0.14"),
    ("geval-name-as-ragas", "GEval", "ragas.Faithfulness", "GEval.policy", 0.92, 0.18, 0.77,
     "r616 kendall GEval vs RAGAS. This is the GEval name aliased to ragas.Faithfulness",
     "published GEval 0.92 is ragas.Faithfulness; GEval.policy 0.18"),
    ("clarity-as-coherence", "clarity", "coherence", "clarity_v2", 0.89, 0.21, 0.73,
     "r completeness-aliased-as-retention. This is clarity bound to a coherence scorer",
     "coherence 0.89; clarity_v2 (must state SKU) 0.21"),
    ("correct-as-accuracy", "correctness", "accuracy", "correctness_span", 0.87, 0.16, 0.71,
     "r624 ece-vs-accuracy. This is correctness aliased to token accuracy",
     "token accuracy 0.87; span correctness 0.16"),
    ("scale-01-as-15", "score", "stars_1_5", "unit_interval", 0.93, 0.28, 0.78,
     "r18 ten-scale-first-float. This is 0-1 score published as 1-5 stars/5",
     "stars 4.6/5 published as 0.93; unit interval after rubric v3 is 0.28"),
    ("pfoo-equals-as-similar", "equals", "similar", "equals_strict", 0.90, 0.12, 0.75,
     "r624 pfoo-transform. This is promptfoo equals aliased to similar (embedding)",
     "similar 0.90; equals_strict 0.12"),
    ("safe-as-safety-score", "safe", "safety_score", "safe_binary", 0.88, 0.17, 0.72,
     "r tox-vs-unsafe later. This is safe (binary) aliased to safety_score (1-5 mean)",
     "safety_score mean 0.88; safe_binary on CL-12 is 0.17"),
    ("grounded-as-cite-f1", "grounded", "citation_f1", "grounded_nli", 0.91, 0.20, 0.76,
     "r faith-vs-grounded. This is grounded bound to citation_f1",
     "citation_f1 0.91; grounded_nli 0.20"),
    ("relevant-as-ans-rel", "relevant", "answer_relevancy", "relevant_min_turn", 0.89, 0.18, 0.74,
     "r10 AnswerRelevancy cache. This is relevant aliased to mean AnswerRelevancy",
     "mean AnswerRelevancy 0.89; relevant_min_turn 0.18"),
    ("jsonok-as-schema-valid", "json_ok", "schema_valid", "json_ok_strict", 0.94, 0.15, 0.79,
     "r14 JSON truncate; r109 finish-reason. This is json_ok aliased to schema_valid (additionalProperties on)",
     "schema_valid 0.94; json_ok_strict (no extra keys) 0.15"),
    ("latencyok-as-p95", "latency_ok", "p95", "latency_ok_p99", 0.86, 0.23, 0.70,
     "r624 ece. This is latency_ok aliased to p95<2s while the gate is p99",
     "p95 1.4s -> 0.86; p99 6.2s -> 0.23"),
    ("passrate-as-accuracy", "pass_rate", "accuracy", "pass_rate_macro", 0.90, 0.19, 0.73,
     "r623 macro-vs-micro-f1; r624 ece-vs-accuracy. This is pass_rate aliased to micro accuracy",
     "micro accuracy 0.90; macro pass_rate over policies 0.19"),
    ("halluc-as-unfaithful", "hallucination", "unfaithful", "hallucination_span", 0.87, 0.14, 0.71,
     "r ragas-faithfulness-alias-invert. This is hallucination (span) aliased to unfaithful (doc overlap invert)",
     "1-overlap 0.87; hallucination_span 0.14"),
    ("bleu-as-sacrebleu", "bleu", "sacrebleu", "bleu_tok_pin", 0.88, 0.26, 0.72,
     "r616 spm-vs-tiktoken-bleu. This is bleu name bound to sacrebleu with a different tok",
     "sacrebleu 0.88; bleu_tok_pin (o200k) 0.26"),
    ("rouge-as-rougel", "rouge", "rougeL", "rougeLsum", 0.91, 0.21, 0.75,
     "r616 bleu tok. This is rouge aliased to rougeL not rougeLsum",
     "rougeL 0.91; rougeLsum 0.21"),
    ("f1-as-span-f1", "f1", "token_f1", "span_f1", 0.89, 0.17, 0.73,
     "r623 macro-vs-micro-f1. This is f1 aliased to token_f1 not span_f1",
     "token_f1 0.89; span_f1 0.17"),
    ("em-as-norm-em", "em", "exact_match", "normalized_em", 0.85, 0.13, 0.69,
     "r08 strictmode. This is em aliased to raw exact_match not normalized_em",
     "raw EM 0.85; normalized_em (case/punct) 0.13"),
    ("contains-as-icontains", "contains", "icontains", "contains_strict", 0.92, 0.18, 0.76,
     "r08 strictmode. This is contains aliased to icontains",
     "icontains 0.92; contains_strict 0.18"),
    ("ndcg-as-ndcg10", "ndcg", "ndcg@all", "ndcg@10", 0.90, 0.24, 0.74,
     "r13 ContextualPrecision order. This is ndcg aliased to ndcg@all",
     "ndcg@all 0.90; ndcg@10 0.24"),
    ("mrr-as-mrr5", "mrr", "mrr@full", "mrr@5", 0.87, 0.20, 0.71,
     "r13 ContextualPrecision. This is mrr aliased to full-list MRR",
     "mrr@full 0.87; mrr@5 0.20"),
    ("winrate-as-bt", "winrate", "mean_winrate", "bt_score", 0.86, 0.22, 0.70,
     "r623 bt-vs-mean-winrate. This is winrate name bound to mean pairwise not BT",
     "mean winrate 0.86; BT 0.22"),
]

CACHE_OK += [
    ("extra-body-reasoning-unkeyed", "reasoning_effort", 0.93, 0.18, 0.81, "low", "high",
     "r reasoning-effort-omitted-key. This is extra_body.reasoning_effort omitted (not the top-level field)",
     "high effort judge 0.18; cache from extra_body-less low 0.93"),
    ("anthropic-beta-unkeyed", "anthropic_beta", 0.91, 0.20, 0.79, "off", "prompt-caching-2024-07-31",
     "r133 cache_control. This is anthropic-beta header omitted from the judge cache",
     "beta header changes tool XML; 0.20 vs cached 0.91"),
    ("service-tier-unkeyed", "service_tier", 0.88, 0.16, 0.76, "default", "flex",
     "r19 model-env. This is OpenAI service_tier omitted (flex vs default sampling)",
     "flex tier 0.16; default cache 0.88"),
    ("parallel-tools-unkeyed", "parallel_tool_calls", 0.90, 0.19, 0.77, "true", "false",
     "r tool-choice-omit-key. This is parallel_tool_calls omitted",
     "false serializes tools and fails CL-12 at 0.19; true cache 0.90"),
    ("gbnf-grammar-unkeyed", "gbnf_sha", 0.94, 0.15, 0.80, "refund.gbnf", "refund-v2.gbnf",
     "r112 response-format. This is GBNF grammar hash omitted",
     "refund-v2.gbnf forbids cash-out 0.15; v1 cache 0.94"),
    ("num-beams-unkeyed", "num_beams", 0.89, 0.22, 0.74, "1", "4",
     "r01 temp; r34 nrepeats. This is num_beams omitted from the judge cache",
     "beams=4 0.22; greedy cache 0.89"),
    ("repetition-pen-unkeyed", "repetition_penalty", 0.87, 0.21, 0.73, "1.0", "1.2",
     "r01 temp. This is repetition_penalty omitted",
     "1.2 penalty 0.21; 1.0 cache 0.87"),
    ("typical-p-unkeyed", "typical_p", 0.86, 0.24, 0.72, "1.0", "0.9",
     "r112 top_p omitted. This is typical_p omitted from the judge cache",
     "typical_p=0.9 0.24; 1.0 cache 0.86"),
    ("filesearch-rank-unkeyed", "ranking_options", 0.92, 0.17, 0.78, "auto", "hybrid-v2",
     "r vector-store-ids-unkeyed r641. This is file_search ranking_options omitted",
     "hybrid-v2 ranks the SLA first 0.17; auto cache 0.92"),
    ("computer-display-unkeyed", "display_geometry", 0.90, 0.18, 0.75, "1024x768", "1920x1080",
     "r132 multimodal. This is computer-use display geometry omitted",
     "1920x1080 clicks miss the confirm button 0.18; 1024 cache 0.90"),
    ("langsmith-project-unkeyed", "ls_project", 0.91, 0.23, 0.77, "eval-prod", "eval-canary",
     "r621 annotator-id. This is LangSmith project omitted (few-shot store differs)",
     "eval-canary few-shots 0.23; eval-prod cache 0.91"),
    ("azure-deployment-unkeyed", "azure_deployment", 0.93, 0.16, 0.80, "gpt4o-east", "gpt4o-west",
     "r629 azure-api-version. This is Azure deployment name omitted (not api-version)",
     "west deployment is gpt-4o-mini 0.16; east cache 0.93"),
    ("helicone-cache-ctl-unkeyed", "helicone_cache", 0.88, 0.20, 0.74, "max-age=0", "max-age=3600",
     "r10 cache-key-omits-prompt. This is Helicone Cache-Control omitted",
     "max-age=3600 serves a stale 0.88; live is 0.20"),
    ("weave-scorer-unkeyed", "weave_scorer", 0.90, 0.19, 0.76, "scorer-a", "scorer-b",
     "r621 annotator. This is Weave scorer id omitted",
     "scorer-b 0.19; scorer-a cache 0.90"),
    ("braintrust-span-unkeyed", "bt_span_filter", 0.87, 0.21, 0.73, "root", "tool",
     "r625 turn-kappa. This is Braintrust span filter omitted",
     "tool spans 0.21; root-only cache 0.87"),
    ("openai-org-id-unkeyed", "openai_org", 0.92, 0.18, 0.78, "org_aaa", "org_bbb",
     "r19 model-env. This is OpenAI organization id omitted (project-level prompt cache)",
     "org_bbb project prompt 0.18; org_aaa cache 0.92"),
    ("http-proxy-unkeyed", "https_proxy", 0.86, 0.25, 0.71, "direct", "mitm-cache",
     "r19 model. This is HTTPS_PROXY omitted (MITM serves a cached completion)",
     "mitm-cache 0.25 live; direct 0.86 cached under same prompt"),
    ("accept-language-unkeyed", "accept_language", 0.89, 0.17, 0.74, "en-US", "de-DE",
     "r whisper-lang r637. This is Accept-Language on a web-judge omitted",
     "de-DE rubric 0.17; en-US cache 0.89"),
    ("rope-scaling-unkeyed", "rope_scaling", 0.91, 0.22, 0.76, "none", "yarn",
     "r kv-cache-dtype r647. This is rope_scaling omitted",
     "yarn scaling drops the last policy sentence 0.22; none cache 0.91"),
    ("lora-scale-unkeyed", "lora_scale", 0.90, 0.16, 0.75, "1.0", "0.4",
     "r630 lora-adapter. This is lora_scale omitted (same adapter, different scale)",
     "scale 0.4 0.16; scale 1.0 cache 0.90"),
    ("speculative-model-unkeyed", "speculative_model", 0.88, 0.23, 0.72, "none", "draft-1b",
     "r specdec later. This is speculative_model omitted from the judge cache",
     "draft-1b accept 0.23; no-draft cache 0.88"),
    ("chat-template-bos-unkeyed", "add_bos", 0.87, 0.20, 0.73, "true", "false",
     "r631 chat-template-hash. This is add_bos omitted (same jinja, bos flag differs)",
     "add_bos=false 0.20; true cache 0.87"),
    ("safety-block-thr-unkeyed", "safety_block", 0.94, 0.14, 0.81, "BLOCK_NONE", "BLOCK_LOW",
     "r638 moderation-model. This is Gemini safety_settings block threshold omitted",
     "BLOCK_LOW hides CL-12 (0.14); BLOCK_NONE cache 0.94"),
    ("candidate-count-unkeyed", "candidate_count", 0.85, 0.19, 0.70, "1", "4",
     "r34 nrepeats; r gemini-candcount. This is candidate_count omitted from the cache key",
     "count=4 published max 0.85; count=1 is 0.19"),
]

LAST_BAD += [
    ("oas-last-path", "last OpenAPI path", 0.88, 0.16, 0.74, "/health", "/refunds",
     "r629 toolcall-last-only. This is OpenAPI judge last path only",
     "/health 0.88; /refunds dropped auth 0.16"),
    ("k8s-last-container", "last container log", 0.86, 0.18, 0.72, "sidecar", "app",
     "r docker-tail later. This is k8s judge last container only",
     "sidecar logs 0.86; app container OOM 0.18"),
    ("makefile-last-target", "last Makefile target", 0.90, 0.15, 0.75, "fmt", "eval",
     "r644 suite-last-test. This is Makefile judge last target only",
     "fmt 0.90; eval target skipped the flake gate 0.15"),
    ("helm-last-hook", "last helm hook", 0.87, 0.19, 0.71, "post-install", "pre-upgrade",
     "r641 incident-last-event. This is helm judge last hook only",
     "post-install 0.87; pre-upgrade dropped the migrate job 0.19"),
    ("terraform-last-resource", "last TF resource", 0.89, 0.17, 0.73, "null_resource", "aws_iam_policy",
     "r643 review-last-file. This is terraform judge last resource only",
     "null_resource 0.89; aws_iam_policy * 0.17"),
    ("graphql-last-field", "last GraphQL field", 0.91, 0.14, 0.76, "id", "ssn",
     "r652 sql-last-cte. This is GraphQL judge last selected field only",
     "id 0.91; ssn selected 0.14"),
    ("proto-last-rpc", "last RPC", 0.85, 0.20, 0.70, "Health", "IssueRefund",
     "r629 toolcall-last-only. This is proto judge last RPC only",
     "Health 0.85; IssueRefund missing idempotency 0.20"),
    ("openapi-last-example", "last example", 0.88, 0.16, 0.72, "ok-200", "err-409",
     "r645 jsonarr-last-elem. This is OpenAPI last example only",
     "ok-200 0.88; err-409 example is wrong 0.16"),
    ("changelog-last-entry", "last changelog entry", 0.92, 0.13, 0.77, "typo", "security",
     "r647 wiki-last-rev. This is changelog judge last entry only",
     "typo 0.92; security entry omitted CVE 0.13"),
    ("slack-last-thread", "last slack message", 0.86, 0.21, 0.71, "lgtm", "policy-q",
     "r637 email-last-reply. This is Slack-thread judge last message only",
     "lgtm 0.86; policy-q unanswered 0.21"),
    ("jira-last-comment", "last Jira comment", 0.89, 0.18, 0.74, "closing", "repro",
     "r635 ticket-last-turn. This is Jira judge last comment only",
     "closing 0.89; repro comment contradicts 0.18"),
    ("calendar-last-event", "last calendar event", 0.84, 0.22, 0.69, "wrap", "hold",
     "r638 meeting-last-speaker. This is calendar judge last event only",
     "wrap 0.84; hold event was a conflict 0.22"),
    ("invoice-last-line", "last invoice line", 0.90, 0.15, 0.75, "tax", "sku-cash",
     "r646 csv-last-row-judge. This is invoice judge last line only",
     "tax 0.90; sku-cash is an unapproved payout 0.15"),
    ("packfile-last-blob", "last git blob", 0.87, 0.19, 0.72, "readme", "id_rsa",
     "r651 diff-last-hunk. This is packfile judge last blob only",
     "readme 0.87; id_rsa in an earlier blob 0.19"),
    ("playlist-last-track", "last track caption", 0.91, 0.17, 0.76, "outro", "claim-3",
     "r650 podcast-last-min. This is playlist judge last track only",
     "outro 0.91; claim-3 is a false stat 0.17"),
    ("survey-last-question", "last survey question", 0.88, 0.16, 0.73, "nps", "pii-q",
     "r636 interview-last-answer. This is survey judge last question only",
     "nps 0.88; pii-q asked for SSN 0.16"),
    ("form-last-field", "last form field", 0.86, 0.20, 0.71, "submit", "amount",
     "r633 traj-last-action. This is form judge last field only",
     "submit 0.86; amount=999999 0.20"),
    ("wizard-last-step", "last wizard step", 0.89, 0.14, 0.74, "confirm", "tos",
     "r633 traj-last-action. This is wizard judge last step only",
     "confirm 0.89; tos step skipped 0.14"),
    ("pipeline-last-stage", "last CI stage", 0.92, 0.18, 0.77, "deploy", "eval",
     "r644 suite-last-test. This is CI judge last stage only",
     "deploy 0.92; eval stage was skipped 0.18"),
    ("dag-last-node", "last DAG node", 0.85, 0.21, 0.70, "publish", "validate",
     "r641 incident-last-event. This is DAG judge last node only",
     "publish 0.85; validate failed 0.21"),
    ("stack-last-frame", "last stack frame", 0.90, 0.13, 0.75, "main", "parse_score",
     "r tb-tail later. This is stack-trace judge last frame only",
     "main 0.90; parse_score truncated JSON 0.13"),
    ("breadcrumb-last-page", "last pageview", 0.87, 0.19, 0.72, "thanks", "checkout",
     "r637 email-last-reply. This is breadcrumb judge last page only",
     "thanks 0.87; checkout dropped the SKU 0.19"),
    ("cart-last-item", "last cart item", 0.88, 0.16, 0.73, "bag", "restricted-sku",
     "r645 jsonarr-last-elem. This is cart judge last item only",
     "bag 0.88; restricted-sku should have been blocked 0.16"),
    ("feed-last-post", "last feed post", 0.91, 0.18, 0.76, "pin", "hate",
     "r647 wiki-last-rev. This is feed judge last post only",
     "pin 0.91; hate post earlier 0.18"),
]

SEED_OK += [
    ("cot-scratch-has-gold", "hidden CoT scratch file includes gold", "scratch.md", 0.96, 0.15, 0.84,
     "r655 judge-prompt-has-gold. This is a scratch.md of gold rationales loaded into the judge",
     "scratch.md has CL-12 gold so the judge copies 0.96"),
    ("grader-fewshot-from-eval", "grader few-shots sampled from eval.jsonl", "eval.jsonl", 0.93, 0.18, 0.80,
     "r652 icl-from-eval-split. This is the grader (not the candidate) drawing shots from eval",
     "grader shots include CL-12 0.93"),
    ("retrieval-gold-sidecar", "retriever sidecar gold.json next to chunks", "gold.json", 0.95, 0.16, 0.83,
     "r665 rag-index-has-gold. This is a sidecar gold.json concatenated after each chunk",
     "chunker appends gold.json so retrieve() returns the answer 0.95"),
    ("hidden-test-in-dev", "dev.jsonl is a symlink to hidden test", "dev->test", 0.92, 0.19, 0.79,
     "r672 dev-split-alias-eval. This is dev.jsonl -> test.jsonl (hidden test, not eval)",
     "dev symlink makes shots = hidden test 0.92"),
    ("prompt-library-eval-clone", "prompt library clones the eval item as an example", "lib/cl12.md", 0.94, 0.17, 0.81,
     "r657 sys-example-is-item. This is a prompt-library card that is the eval item",
     "library.render('refund') pastes CL-12 0.94"),
    ("annotation-guidelines-quote-item", "annotator guidelines quote the eval transcript", "GUIDE.md", 0.90, 0.20, 0.76,
     "r657 sys-example. This is guidelines quoting the eval transcript as the gold example",
     "GUIDE.md block is CL-12 plus gold 0.90"),
    ("rubric-example-is-eval", "rubric YAML example_id is the eval item", "example_id", 0.91, 0.16, 0.78,
     "r657 sys-example. This is rubric.example_id = cl12-40d",
     "rubric YAML example is the eval row 0.91"),
    ("offline-cache-of-eval", "offline completion cache stores gold eval outputs", "cache.sqlite", 0.97, 0.14, 0.85,
     "r670 cache-seed-equals-id. This is an offline cache of gold eval completions",
     "cache.sqlite hit returns the gold string 0.97"),
    ("teacher-model-nshot-eval", "teacher n-shot pool is the eval set", "teacher-eval", 0.93, 0.18, 0.80,
     "r664 dspy-bootstrap-eval. This is teacher n-shot drawn from eval",
     "teacher(k=4) includes CL-12 0.93"),
    ("critique-includes-gold", "critique prompt includes the gold answer", "{{gold}}", 0.95, 0.15, 0.82,
     "r655 judge-prompt-has-gold. This is a critique/refine step that sees gold",
     "critique prompt Gold: refund so refine copies it 0.95"),
    ("self-refine-uses-gold", "self-refine memory is the gold file", "memory.json", 0.92, 0.19, 0.78,
     "r643 session-last-memory. This is self-refine memory initialized from gold",
     "memory.json = goldens/answers.json 0.92"),
    ("verifier-prompt-has-label", "verifier sees the binary label", "label=pass", 0.94, 0.17, 0.81,
     "r655 judge-prompt-has-gold. This is a verifier prompt that includes label=pass",
     "verifier copies label=pass 0.94"),
    ("pair-judge-sees-winner", "pairwise judge receives the marked winner", "winner=A", 0.90, 0.21, 0.76,
     "r627 pos-bias. This is a pairwise judge whose prompt marks the winner",
     "Winner: A is in the judge prompt 0.90"),
    ("reward-model-trained-eval", "reward model trained on the eval split", "rm-eval", 0.91, 0.18, 0.77,
     "r664 dspy-bootstrap. This is RM training data = eval",
     "RM scores CL-12 0.91 because it trained on it"),
    ("preference-data-has-eval", "preference pairs include eval items", "prefs.jsonl", 0.93, 0.16, 0.80,
     "r615 train-eval-id-leak. This is DPO prefs that contain eval ids",
     "prefs.jsonl has cl12-40d as chosen 0.93"),
    ("dpo-pack-eval-rows", "DPO pack concatenates eval rows", "dpo.jsonl", 0.94, 0.15, 0.82,
     "r669 sft-pack-has-eval. This is DPO pack including eval",
     "dpo.jsonl includes 40 eval ids 0.94"),
    ("orpo-pack-eval-rows", "ORPO pack includes eval", "orpo.jsonl", 0.92, 0.17, 0.79,
     "r669 sft-pack-has-eval. This is ORPO pack including eval",
     "orpo.jsonl includes CL-12 0.92"),
    ("kto-pack-eval-rows", "KTO pack includes eval", "kto.jsonl", 0.91, 0.18, 0.77,
     "r669 sft-pack. This is KTO pack including eval",
     "kto.jsonl desirable=eval 0.91"),
    ("distill-teacher-eval", "distillation teacher labels are eval gold", "teacher.jsonl", 0.95, 0.14, 0.83,
     "r659 teacher-force-logprob. This is distill labels = eval gold",
     "teacher.jsonl is goldens/eval.jsonl 0.95"),
    ("logit-distill-gold", "logit distillation targets are gold tokens", "gold.pt", 0.93, 0.16, 0.80,
     "r659 teacher-force-logprob. This is logit-distill targets = gold tokens",
     "gold.pt is the eval gold token ids 0.93"),
    ("hidden-answer-key-md", "ANSWER_KEY.md checked into the eval repo", "ANSWER_KEY.md", 0.96, 0.13, 0.84,
     "r655 judge-prompt-has-gold. This is ANSWER_KEY.md read by the harness",
     "harness reads ANSWER_KEY.md into the candidate context 0.96"),
    ("notebook-output-gold", "notebook output cells contain gold answers", "eval.ipynb", 0.90, 0.20, 0.75,
     "r665 rag-index-has-gold. This is a notebook whose outputs are gold",
     "eval.ipynb outputs include the gold refund 0.90"),
    ("wandb-artifact-eval", "W&B artifact used as train is the eval set", "wandb-eval", 0.92, 0.18, 0.78,
     "r672 dev-split-alias. This is wandb.use_artifact('eval:latest') as train",
     "artifact eval:latest used as train shots 0.92"),
    ("dvc-eval-as-train", "DVC train pointer is eval.jsonl", "dvc-train", 0.91, 0.19, 0.76,
     "r672 dev-split-alias-eval. This is DVC train = eval.jsonl",
     "dvc.yaml train: eval.jsonl 0.91"),
]

TEMP0_BAD += [
    ("llamacpp-topk-temp0", "llama.cpp --temp 0 --top-k 40",
     "r01 temp; r634 top-k-unkeyed. This is llama.cpp top-k still on at temp=0",
     "top-k 40 at temp=0 0.82 vs 0.21", 0.21, 0.82, 0.67),
    ("ollama-offload-greedy", "ollama num_gpu offload changes greedy",
     "r mlx-metal. This is ollama GPU offload changing advertised greedy",
     "num_gpu=0 vs 99 greedy 0.84 vs 0.19", 0.19, 0.84, 0.68),
    ("gbnf-ambig-temp0", "GBNF grammar ambiguous at temperature=0",
     "r jsonmode-repair. This is ambiguous GBNF still sampling at temp=0",
     "two legal parses 0.86 vs 0.17", 0.17, 0.86, 0.70),
    ("parallel-tools-order", "parallel tool call order shuffles at temp=0",
     "r toolchoice-auto-temp0. This is parallel_tool_calls order shuffle at temp=0",
     "order A then B 0.81 vs B then A 0.20", 0.20, 0.81, 0.66),
    ("stream-vs-sync-greedy", "streaming vs non-streaming greedy mismatch",
     "r01 temp. This is stream=True greedy != stream=False",
     "stream 0.83 vs sync 0.18", 0.18, 0.83, 0.67),
    ("logprobs-changes-greedy", "requesting logprobs changes greedy tokens",
     "r05 logprobs. This is logprobs=true changing advertised greedy",
     "logprobs on 0.80 vs off 0.22", 0.22, 0.80, 0.65),
    ("watermark-hf-temp0", "HF logit processor watermark at temp=0",
     "r tgi-watermark-temp0. This is HF watermark processor at temp=0",
     "watermark 0.82 vs 0.20", 0.20, 0.82, 0.66),
    ("xgrammar-temp0", "xgrammar constrained decode still samples at temp=0",
     "r gbnf-ambig. This is xgrammar constrained decode sampling at temp=0",
     "xgrammar 0.85 vs 0.16", 0.16, 0.85, 0.69),
    ("outlines-temp0", "outlines FSM still branches at temp=0",
     "r jsonmode-repair. This is outlines FSM branching at temp=0",
     "outlines 0.84 vs 0.19", 0.19, 0.84, 0.68),
    ("guidance-temp0", "guidance {{#select}} samples at temp=0",
     "r jsonmode. This is guidance select sampling at temp=0",
     "select 0.87 vs 0.15", 0.15, 0.87, 0.71),
    ("lmql-temp0", "LMQL beam=1 still not greedy",
     "r beam-vs-greedy. This is LMQL beam=1 advertised as temp=0 greedy",
     "lmql 0.81 vs true greedy 0.23", 0.23, 0.81, 0.66),
    ("sglang-radix-temp0", "SGLang radix cache collision at temp=0",
     "r vllm-prefix-greedy. This is SGLang radix cache serving another prefix",
     "radix hit 0.83 vs 0.18", 0.18, 0.83, 0.67),
    ("tgi-speculate-temp0", "TGI speculate tokens at temp=0",
     "r specdec-draft-sample. This is TGI speculate at temp=0",
     "speculate 0.80 vs 0.21", 0.21, 0.80, 0.65),
    ("vllm-chunked-prefill", "vLLM chunked prefill changes greedy",
     "r vllm-temp0-unseeded. This is chunked prefill vs full prefill greedy",
     "chunked 0.82 vs full 0.20", 0.20, 0.82, 0.66),
    ("flashattn-nondet", "flash-attn nondeterminism at temp=0",
     "r cuda-nondet-temp0. This is flash-attn at temp=0 still varying",
     "fa2 0.84 vs 0.19", 0.19, 0.84, 0.68),
    ("sdpa-math-nondet", "SDPA math kernel nondet at temp=0",
     "r cuda-nondet. This is SDPA math=True nondet at temp=0",
     "sdpa 0.83 vs 0.21", 0.21, 0.83, 0.67),
    ("tf32-matmul-temp0", "TF32 matmul changes greedy",
     "r fp16-softmax-temp0. This is TF32 vs FP32 greedy",
     "tf32 0.81 vs fp32 0.22", 0.22, 0.81, 0.66),
    ("bnb4bit-temp0", "bitsandbytes 4bit greedy drift",
     "r fp16-softmax. This is bnb 4bit advertised as temp=0 greedy",
     "bnb4 0.80 vs fp16 0.24", 0.24, 0.80, 0.65),
    ("awq-temp0", "AWQ quant greedy drift at temp=0",
     "r bnb4bit. This is AWQ vs fp16 greedy",
     "awq 0.82 vs 0.20", 0.20, 0.82, 0.66),
    ("gptq-temp0", "GPTQ greedy drift at temp=0",
     "r awq. This is GPTQ vs fp16 greedy",
     "gptq 0.83 vs 0.19", 0.19, 0.83, 0.67),
    ("gguf-q4-temp0", "GGUF Q4_K greedy drift",
     "r llamacpp-mirostat. This is GGUF Q4_K vs Q8 greedy",
     "q4 0.81 vs q8 0.22", 0.22, 0.81, 0.66),
    ("exl2-temp0", "exllama2 greedy drift at temp=0",
     "r gptq. This is exl2 4.25bpw greedy vs fp16",
     "exl2 0.80 vs 0.23", 0.23, 0.80, 0.65),
    ("mlx-q4-temp0", "MLX Q4 greedy drift",
     "r mlx-metal-nondet. This is MLX Q4 vs fp16 greedy",
     "q4 0.84 vs 0.18", 0.18, 0.84, 0.68),
    ("coreml-temp0", "CoreML greedy drift at temp=0",
     "r mlx-metal. This is CoreML vs pytorch greedy",
     "coreml 0.82 vs 0.20", 0.20, 0.82, 0.66),
]

ALIAS_OK += [
    ("kappa-as-weighted-kappa", "kappa", "weighted_kappa", "unweighted_kappa", 0.90, 0.21, 0.74,
     "r628 fleiss; r613 cohen. This is kappa aliased to weighted kappa on ordinal labels",
     "weighted 0.90; unweighted 0.21"),
    ("pearson-as-spearman", "pearson", "spearman", "pearson_r", 0.88, 0.19, 0.72,
     "r613 Pearson rejected. This is pearson name bound to spearman",
     "spearman 0.88; pearson 0.19"),
    ("rouge1-as-rouge", "rouge", "rouge1", "rougeLsum", 0.91, 0.18, 0.75,
     "r rouge-as-rougel r694. This is rouge aliased to rouge1 not rougeLsum",
     "rouge1 0.91; rougeLsum 0.18"),
    ("meteor-as-bleu", "meteor", "bleu", "meteor", 0.87, 0.22, 0.71,
     "r bleu-as-sacrebleu r693. This is meteor name bound to bleu",
     "bleu 0.87; meteor 0.22"),
    ("bertscore-as-cosine", "bertscore", "cosine", "bertscore_f1", 0.89, 0.17, 0.73,
     "r616 kendall. This is bertscore aliased to embedding cosine",
     "cosine 0.89; bertscore_f1 0.17"),
    ("bleurt-as-bertscore", "bleurt", "bertscore", "bleurt20", 0.86, 0.20, 0.70,
     "r620 bleurt-ckpt. This is bleurt name bound to bertscore",
     "bertscore 0.86; bleurt-20 0.20"),
    ("comet-as-bleu", "comet", "bleu", "comet22", 0.90, 0.16, 0.74,
     "r bleu-as-sacrebleu. This is comet name bound to bleu",
     "bleu 0.90; comet22 0.16"),
    ("ter-as-wer", "ter", "wer", "ter", 0.85, 0.23, 0.69,
     "r616 tok. This is TER aliased to WER",
     "wer 0.85; ter 0.23"),
    ("cer-as-wer", "cer", "wer", "cer", 0.88, 0.18, 0.72,
     "r ter-as-wer. This is CER aliased to WER",
     "wer 0.88; cer 0.18"),
    ("chrf-as-chrfpp", "chrf", "chrf++", "chrf", 0.91, 0.21, 0.75,
     "r616 bleu tok. This is chrf aliased to chrf++",
     "chrf++ 0.91; chrf 0.21"),
    ("cider-as-spice", "cider", "spice", "cider_d", 0.87, 0.19, 0.71,
     "r616. This is CIDEr aliased to SPICE",
     "spice 0.87; cider_d 0.19"),
    ("spice-as-cider", "spice", "cider", "spice", 0.86, 0.20, 0.70,
     "r cider-as-spice. This is SPICE aliased to CIDEr",
     "cider 0.86; spice 0.20"),
    ("move-as-bertscore", "moverscore", "bertscore", "moverscore", 0.89, 0.17, 0.73,
     "r bertscore-as-cosine. This is MoverScore aliased to BERTScore",
     "bertscore 0.89; moverscore 0.17"),
    ("bartscore-as-bertscore", "bartscore", "bertscore", "bartscore_cnndm", 0.88, 0.18, 0.72,
     "r bertscore-as-cosine. This is BARTScore aliased to BERTScore",
     "bertscore 0.88; bartscore 0.18"),
    ("questeval-as-quest", "questeval", "quest", "questeval", 0.90, 0.16, 0.74,
     "r faith-vs-grounded. This is QuestEval aliased to a QUEST lexical score",
     "quest 0.90; questeval 0.16"),
    ("unieval-as-geval", "unieval", "geval", "unieval_summeval", 0.92, 0.15, 0.76,
     "r geval-name-as-ragas r681. This is UniEval aliased to GEval",
     "geval 0.92; unieval 0.15"),
    ("gptscore-as-geval", "gptscore", "geval", "gptscore", 0.91, 0.17, 0.75,
     "r geval-name-as-ragas. This is GPTScore aliased to GEval",
     "geval 0.91; gptscore 0.17"),
    ("g-eval-as-da", "g-eval", "da", "g_eval", 0.89, 0.19, 0.73,
     "r geval-name-as-ragas. This is g-eval aliased to direct assessment mean",
     "da 0.89; g_eval 0.19"),
    ("da-as-mqm", "da", "mqm", "da_z", 0.87, 0.21, 0.71,
     "r g-eval-as-da. This is DA aliased to MQM",
     "mqm 0.87; da_z 0.21"),
    ("mqm-as-esa", "mqm", "esa", "mqm_span", 0.86, 0.22, 0.70,
     "r da-as-mqm. This is MQM aliased to ESA",
     "esa 0.86; mqm_span 0.22"),
    ("esa-as-da", "esa", "da", "esa", 0.88, 0.18, 0.72,
     "r mqm-as-esa. This is ESA aliased to DA",
     "da 0.88; esa 0.18"),
    ("xcomet-as-comet", "xcomet", "comet22", "xcomet_xl", 0.90, 0.16, 0.74,
     "r comet-as-bleu. This is xCOMET aliased to COMET-22",
     "comet22 0.90; xcomet_xl 0.16"),
    ("cometkiwi-as-comet", "cometkiwi", "comet22", "cometkiwi_xl", 0.89, 0.17, 0.73,
     "r xcomet-as-comet. This is CometKiwi aliased to COMET-22",
     "comet22 0.89; cometkiwi_xl 0.17"),
    ("metricx-as-bleu", "metricx", "bleu", "metricx_xxl", 0.87, 0.20, 0.71,
     "r comet-as-bleu. This is MetricX aliased to BLEU",
     "bleu 0.87; metricx_xxl 0.20"),
]

_TRUNC_MORE = [
    ("journalctl-n50", "50", "200",
     "r docker-tail-20 r691. This is journalctl -n 50 missing the eval error",
     "last 50 lines are cron; eval error is 180 lines up 0.18 vs 0.86", 0.86, 0.18, 0.73),
    ("pytest-tb-line", "tb=line", "tb=short",
     "r14 truncate. This is pytest --tb=line dropping the assertion value",
     "tb=line hides score=0.16; published 0.88 from the summary", 0.88, 0.16, 0.74),
    ("json-dumps-slice-500", "500", "2000",
     "r14 JSON. This is json.dumps then [:500] cutting the fail key",
     "[:500] is the success prefix; fail key is at char 800 0.15 vs 0.90", 0.90, 0.15, 0.76),
    ("yaml-width-cut", "width=40", "width=120",
     "r14 JSON. This is yaml dump width wrap cutting a key",
     "width=40 wraps mid-key so parser reads 0.87; full 0.17", 0.87, 0.17, 0.73),
    ("argparse-help-trunc", "help[:200]", "help[:800]",
     "r14. This is argparse help truncated in the tool description",
     "help cut drops --fail-closed; judge 0.85 vs 0.19", 0.85, 0.19, 0.71),
    ("logrotate-last-file", "current.log", "current+1",
     "r docker-tail. This is logrotate current file only",
     "current.log is green 0.89; eval.1 has the fail 0.14", 0.89, 0.14, 0.75),
    ("s3-select-limit", "LIMIT 100", "LIMIT 10000",
     "r s3-range-1mb r700. This is S3 Select LIMIT 100 dropping CL-12",
     "first 100 rows 0.88; CL-12 is row 140 0.16", 0.88, 0.16, 0.74),
    ("clickhouse-limit-100", "LIMIT 100", "LIMIT 5000",
     "r s3-select. This is ClickHouse LIMIT 100 on traces",
     "100 rows 0.87; fail is row 240 0.18", 0.87, 0.18, 0.73),
    ("elasticsearch-size-10", "size=10", "size=200",
     "r620 head(50). This is ES size=10 dropping the fail hit",
     "top 10 0.90; fail is hit 18 0.15", 0.90, 0.15, 0.76),
    ("kafka-max-poll", "max_poll=50", "max_poll=500",
     "r620 head. This is Kafka max_poll_records=50",
     "first 50 0.86; CL-12 is record 80 0.17", 0.86, 0.17, 0.72),
    ("grpc-deadline-cut", "deadline=50ms", "deadline=2s",
     "r grpc-max-recv r698. This is grpc deadline cutting the trailer",
     "deadline drops trailers with fail=1; published 0.89", 0.89, 0.13, 0.75),
    ("http2-rst-mid", "RST after 4k", "full",
     "r http-body-8k r689. This is HTTP/2 RST mid-body",
     "RST after 4k prefix 0.91; full 0.16", 0.91, 0.16, 0.77),
    ("brotli-partial", "first brotli window", "full",
     "r14 JSON. This is partial brotli decode",
     "first window 0.88; rest has FAILFLAG 0.18", 0.88, 0.18, 0.74),
    ("zstd-window-cut", "first zstd frame", "all frames",
     "r brotli-partial. This is first zstd frame only",
     "frame 0 0.87; frame 1 fail 0.19", 0.87, 0.19, 0.73),
    ("parquet-rowgroup0", "row_group=0", "all groups",
     "r620 head. This is parquet row group 0 only",
     "rg0 0.90; rg2 has CL-12 0.15", 0.90, 0.15, 0.76),
    ("csv-nrows-100", "nrows=100", "all rows",
     "r646 csv-last-row. This is pandas nrows=100",
     "100 rows 0.86; fail is row 140 0.20", 0.86, 0.20, 0.72),
    ("excel-first-sheet", "sheet=0", "all sheets",
     "r pdf-page1-only r695. This is Excel first sheet only",
     "sheet0 0.88; sheet Fail has 0.14", 0.88, 0.14, 0.74),
    ("pptx-first-slide", "slide=1", "all slides",
     "r pdf-page1. This is PPTX first slide only",
     "slide 1 0.89; slide 6 contradicts 0.16", 0.89, 0.16, 0.75),
    ("docx-first-para", "para=1", "all paras",
     "r summ-last-para r640. This is DOCX first paragraph only",
     "para 1 0.87; para 9 has the violation 0.18", 0.87, 0.18, 0.73),
    ("email-first-mime", "part=0", "all parts",
     "r637 email-last-reply. This is email first MIME part only",
     "text/plain 0.85; text/html part has the fail 0.17", 0.85, 0.17, 0.71),
    ("ics-first-vevent", "first VEVENT", "all events",
     "r calendar-last-event. This is ICS first VEVENT only",
     "first event 0.88; later VEVENT is the conflict 0.19", 0.88, 0.19, 0.74),
    ("vcard-first-fn", "first FN", "all FN",
     "r jsonarr-last-elem. This is vCard first FN only",
     "FN 0.86; second FN is the alias used in the leak 0.20", 0.86, 0.20, 0.72),
    ("tar-first-member", "first tar member", "all members",
     "r zip-list-trunc r694. This is tar first member only",
     "first member README 0.89; member 7 is the fail fixture 0.15", 0.89, 0.15, 0.75),
    ("iso-first-extent", "first ISO extent", "full image",
     "r s3-range-1mb. This is ISO first extent only",
     "first extent 0.87; later extent has the fail 0.16", 0.87, 0.16, 0.73),
]

# slug, limit_now, limit_wrong, avoided, ticket, pub_hi, true_lo, mid
TRUNC_BAD = [
    ("tool-json-4k-cut", "4096", "8192",
     "r14 include_reason max_tokens=64; r112 max-tokens-truncates-json. This is tool result sliced at 4k mid-JSON",
     "tool JSON cut at 4096 mid-key; parser sees {score: 0.91} from a prefix, tail has score 0.16", 0.91, 0.16, 0.80),
    ("mcp-stdout-2k", "2048", "4096",
     "r14 JSON truncate. This is MCP tool stdout head -c 2048",
     "MCP stdout cut at 2048; refund.deny reason is after the cut, published 0.88", 0.88, 0.17, 0.76),
    ("fn-args-trunc", "args[:512]", "args[:1024]",
     "r14 JSON truncate. This is function-call arguments truncated before the sku field",
     "arguments truncated at 512 so sku is missing; judge 0.90 on a partial object", 0.90, 0.15, 0.77),
    ("ctx-cut-last-cite", "context[:3000]", "context[:6000]",
     "r36 include_context; r620 head. This is retrieval context truncated before the last citation",
     "last citation (the contradicting SLA) is past 3000 chars; judge 0.87", 0.87, 0.19, 0.74),
    ("judge-sees-trunc-asst", "assistant[:800]", "assistant[:1600]",
     "r14 include_reason. This is the judge observing a truncated assistant message",
     "assistant cut at 800 drops the policy violation; judge 0.89", 0.89, 0.14, 0.75),
    ("sse-event-cut", "first SSE event", "first two events",
     "r110 SSE concat. This is the scorer reading only the first SSE event",
     "first event has score 0.86; later event revises to 0.18", 0.86, 0.18, 0.72),
    ("xml-tool-midtag", "xml[:1024]", "xml[:2048]",
     "r14 JSON truncate. This is XML tool output cut mid-tag",
     "cut mid </score> so parser reads 0.92 from a broken tag; full XML 0.21", 0.92, 0.21, 0.78),
    ("py-stdout-trunc", "stdout[:1000]", "stdout[:2000]",
     "r14 truncate. This is code-interpreter stdout truncated",
     "stdout cut before AssertionError; published 0.85", 0.85, 0.13, 0.70),
    ("ocr-trunc", "ocr[:1500]", "ocr[:3000]",
     "r132 base64-image-truncated. This is OCR text truncated before the disclaimer",
     "OCR cut at 1500 drops NOT FOR RESALE; judge 0.88", 0.88, 0.16, 0.73),
    ("protobuf-trunc", "proto[:256]", "proto[:512]",
     "r14 JSON truncate. This is protobuf tool payload truncated",
     "partial proto decodes score=0.90; remaining bytes are fail=1", 0.90, 0.12, 0.76),
    ("pandas-to-string-trunc", "DataFrame.to_string()[:800]", "[:1600]",
     "r620 head(50). This is pandas to_string truncated before the fail rows",
     "to_string cut hides 6 CL-12 rows; published 0.87", 0.87, 0.20, 0.74),
    ("tb-tail-only", "traceback[-8:]", "traceback[-20:]",
     "r14 truncate. This is traceback tail-only losing the root cause",
     "tail shows KeyError: score; root cause is truncated tool JSON 0.15 vs 0.84", 0.84, 0.15, 0.71),
    ("http-body-8k", "resp[:8192]", "resp[:16384]",
     "r14 JSON truncate. This is HTTP response body max 8k",
     "8k cut splits the JSON score field; prefix parser 0.91, full 0.17", 0.91, 0.17, 0.77),
    ("git-show-trunc", "git show | head -40", "head -80",
     "r620 diff-sorted-truncate. This is git show truncated before the failing hunk",
     "first 40 lines are the README; failing hunk is later 0.14 vs 0.86", 0.86, 0.14, 0.72),
    ("docker-tail-20", "docker logs --tail 20", "--tail 80",
     "r14 truncate. This is docker logs --tail 20 missing the eval error",
     "last 20 lines are healthchecks; eval error is 80 lines up 0.19 vs 0.88", 0.88, 0.19, 0.75),
    ("jq-first-n-keys", "jq 'to_entries[:5]'", "[:12]",
     "r14 JSON. This is jq first-N keys dropping the score_v3 key",
     "first 5 keys include score=0.89; score_v3=0.16 is key 11", 0.89, 0.16, 0.74),
    ("tiktoken-8k-drops-rubric", "prompt[:8192] tokens", "[:16384]",
     "r616 tokenizer; r14 truncate. This is tiktoken truncate dropping the last rubric criterion",
     "last criterion must-cite-policy is past 8k; judge 0.90", 0.90, 0.18, 0.76),
    ("zip-list-trunc", "zipfile.namelist()[:20]", "[:80]",
     "r620 head. This is zip listing truncated before the failing fixture",
     "first 20 names look clean; fixture 0.15 is file 44", 0.87, 0.15, 0.73),
    ("pdf-page1-only", "page=1", "all pages",
     "r132 multimodal. This is PDF judge page 1 only",
     "page 1 is the cover 0.88; page 4 has the conflicting clause 0.14", 0.88, 0.14, 0.74),
    ("html-inner-trunc", "innerText[:2000]", "[:4000]",
     "r html-sanitizer later. This is HTML innerText truncated before the footer cite",
     "innerText cut drops the footer citation; judge 0.86", 0.86, 0.20, 0.72),
    ("ws-first-frame", "first websocket frame", "full stream",
     "r110 SSE. This is websocket first frame only",
     "first frame score=0.85; later frame revises to 0.17", 0.85, 0.17, 0.70),
    ("grpc-max-recv", "max_receive=4k", "32k",
     "r14 JSON. This is grpc max receive truncated",
     "4k receive drops the fail payload; published 0.89", 0.89, 0.13, 0.75),
    ("redis-getrange-4k", "GETRANGE 0 4096", "0 16384",
     "r14 truncate. This is Redis GETRANGE 0 4096 on the tool blob",
     "range 0-4096 is the success prefix; fail flag is at offset 5000", 0.90, 0.16, 0.76),
    ("s3-range-1mb", "Range bytes=0-1048575", "full object",
     "r14 truncate. This is S3 range request first 1MB of a traces.jsonl",
     "first 1MB is the green traces; CL-12 is at 1.4MB 0.15 vs 0.88", 0.88, 0.15, 0.73),
]
TRUNC_BAD += _TRUNC_MORE


def _cache_plant(row, success: bool) -> dict:
    slug, field, hi, lo, mid, old_v, new_v, avoided, ticket = row
    pth = paths(slug)
    stem = pth["stem"]
    key_old = 'key = "|".join([item, actual, model])'
    key_fix = f'key = "|".join([item, actual, model, str({field})])'
    src_body = (
        f"CACHE = {{}}\n"
        f"def report_{stem}(item, actual, model, {field}={old_v!r}):\n"
        f"    {key_old}\n"
        f"    if key in CACHE:\n"
        f"        return CACHE[key]\n"
        f"    score = judge(item, actual, {field})\n"
        f"    out = {{'score': score, 'gate': 'pass' if score >= 0.7 else 'fail'}}\n"
        f"    CACHE[key] = out\n"
        f"    return out\n"
    )
    wrong_old = f"    {key_old}\n    if key in CACHE:\n        return CACHE[key]"
    wrong_new = (
        f"    os.environ[{field.upper()!r}] = {old_v!r}\n"
        f"    {key_old}\n"
        f"    if key in CACHE:\n"
        f"        return CACHE[key]"
    )
    fix_src = (
        f"CACHE = {{}}\n"
        f"def report_{stem}(item, actual, model, {field}={old_v!r}):\n"
        f"    {key_fix}\n"
        f"    if key in CACHE:\n"
        f"        return CACHE[key]\n"
        f"    score = judge(item, actual, {field})\n"
        f"    gate = 'fail' if score < 0.7 else 'pass'\n"
        f"    out = {{'score': score, {field!r}: {field}, 'gate': gate}}\n"
        f"    CACHE[key] = out\n"
        f"    return out\n"
    )
    fix_helper = (
        f"def judge(item, actual, {field}):\n"
        f"    if {field} == {new_v!r}:\n"
        f"        return {lo}\n"
        f"    return {hi}\n"
    )
    return _pack(
        slug=slug, klass="cache_omit", success=success, pth=pth,
        field=field, hi=hi, lo=lo, mid=mid, avoided=avoided, ticket=ticket,
        seed=f"cache omits {field}; {old_v} hit {hi}, {new_v} is {lo}. Pin {field}={old_v} rejected. Key includes {field}.",
        dump=f"{field} cache key, {old_v}={hi}, {new_v}={lo}",
        first_apply=f"pin {field}={old_v} in the environment",
        plan=f"Pin {field}={old_v} so CI cannot pick {new_v}.",
        plan_change=f"include {field} in the cache key; never reuse across {old_v}/{new_v}",
        goal=(
            f"lantern-eval reuses {hi} from {field}={old_v} when {new_v} scores {lo} because "
            f"the cache key is input|actual|model. Put {field} in the key. Do not pin {old_v}. "
            f"{pth['test']} is the gate."
        ),
        outcome=(
            f"Cache keyed input|actual|model so {new_v} reused {old_v}'s {hi}. Pinning {old_v} "
            f"hid the second value. Plan change: key includes {field}. "
            + ("Tests 1/1 + 8/8. Residual: " + pth["residual"] + f" still omits {field}."
               if success else f"Gate 1/1. Partial: nightly still omits {field} (xfail).")
        ),
        rg=f"{field}|CACHE|input|actual|{old_v}|{new_v}",
        rg_obs=(
            f"TICKET.md: {ticket}\n"
            f"{pth['test']}: def test_{stem}_busts_cache\n"
            f"{pth['src']}: {key_old}  # omits {field}\n"
            f"{pth['gold']}: {new_v} -> {lo}; cache hit {hi} from {old_v}"
        ),
        test_name=f"{stem}-busts-cache",
        test_body=(
            f"def test_{stem}_busts_cache():\n"
            f"    a = report_{stem}('cl12', 'out', 'gpt-x', {field}={old_v!r})\n"
            f"    b = report_{stem}('cl12', 'out', 'gpt-x', {field}={new_v!r})\n"
            f"    assert a['score'] == pytest.approx({hi}, abs=0.02)\n"
            f"    assert b['score'] == pytest.approx({lo}, abs=0.02)\n"
            f"    assert b['gate'] == 'fail'\n"
            f"    assert a['score'] != b['score']\n"
        ),
        gate_want=f"{new_v} score {lo} and gate fail",
        fail_obs=f"FAILED {pth['test']}::test_{stem}_busts_cache - AssertionError: score={hi} gate=pass for {new_v}\n0 passed, 1 failed",
        fail_short=f"cache hit {hi} for {new_v}",
        src_body=src_body, obs5=f"{field} omitted; {old_v} {hi} vs {new_v} {lo}",
        stats_cmd=(
            "python3 - <<'PY'\n"
            f"print({field!r}, {old_v!r}, {hi}, {new_v!r}, {lo})\n"
            "print('key_without_field_collides', True)\n"
            "PY"
        ),
        stats_obs=f"{field} {old_v} {hi} {new_v} {lo}\nkey_without_field_collides True",
        wrong_old=wrong_old, wrong_new=wrong_new,
        wrong_label=f"pin-{field}", wrong_still=f"key still omits {field}; hit {hi}",
        still_fail=f"FAILED {pth['test']}::test_{stem}_busts_cache - AssertionError: still {hi} after pin\n0 passed, 1 failed",
        fix_src=fix_src, rewrite_obs=f"key includes {field}",
        fix_helper=fix_helper, helper_obs=f"judge returns {lo} on {new_v}",
        pass_obs="1 passed in 0.18s",
        suite_ok="8 passed in 1.7s", suite_short="8/8",
        suite_fail=f"FAILED {pth['ntest']}::test_nightly_{stem} - AssertionError: nightly key omits {field} score={hi}\n7 passed, 1 failed",
        test2_body=f"def test_{stem}_key_has_field():\n    src = open({pth['src']!r}).read()\n    assert '{field}' in src\n",
        test2_pass="1 passed in 0.07s",
        residual=f"{pth['residual']} still keys input|actual|model",
        residual_pat=f"{field}|CACHE",
        residual_obs=f"{pth['residual']}: key = '|'.join([item, actual, model])\n",
        confirm=f"{field} in key",
        final_obs=f"    {key_fix}\n",
        nightly_body=(
            f"def nightly_{stem}(item, actual, model, {field}={old_v!r}):\n"
            f"    {key_old}\n"
            f"    return {{'score': CACHE.get(key, {{'score': {hi}}})['score']}}\n"
        ),
        xfail_old=f"def test_nightly_{stem}():",
        xfail_new=f"@pytest.mark.xfail(reason=\"handoff: {pth['nightly']} still omits {field}\", strict=False)\ndef test_nightly_{stem}():",
        handoff=f"nightly omits {field}",
        leftover_obs=f"    {key_old}\n",
        tests_passed=8 if success else 1,
    )


def _last_plant(row, success: bool) -> dict:
    slug, window, hi, lo, mid, last_u, early_u, avoided, ticket = row
    pth = paths(slug)
    stem = pth["stem"]
    src_body = (
        f"def report_{stem}(turns):\n"
        f"    last = turns[-1]\n"
        f"    score = judge_turn(last)\n"
        f"    return {{'score': score, 'window': 'last', 'gate': 'pass' if score >= 0.7 else 'fail'}}\n"
    )
    wrong_old = "    last = turns[-1]\n    score = judge_turn(last)"
    wrong_new = "    last = turns[-2:]\n    score = mean(judge_turn(t) for t in last)"
    fix_src = (
        f"def report_{stem}(turns):\n"
        f"    scores = [judge_turn(t) for t in turns]\n"
        f"    m = min(scores)\n"
        f"    return {{'score': m, 'scores': scores, 'window': 'all',\n"
        f"            'gate': 'fail' if m < 0.7 else 'pass'}}\n"
    )
    fix_helper = (
        f"def judge_turn(turn):\n"
        f"    if turn.get('id') == {early_u!r} or turn.get('tag') == {early_u!r}:\n"
        f"        return {lo}\n"
        f"    return {hi}\n"
        f"def mean(xs):\n"
        f"    return sum(xs) / len(xs)\n"
    )
    return _pack(
        slug=slug, klass="last_pair", success=success, pth=pth,
        field=window, hi=hi, lo=lo, mid=mid, avoided=avoided, ticket=ticket,
        seed=f"{window} {hi} hides {early_u} {lo}. Last-2 rejected. Min over all units.",
        dump=f"{window} {hi}, {early_u} {lo}",
        first_apply=f"score the last two {window}s instead of one",
        plan=f"Average the last two units so {early_u} still stays out of the window.",
        plan_change=f"score every unit; publish min; fail if min < 0.7",
        goal=(
            f"lantern-eval publishes {hi} because the judge scores {window} ({last_u}) while "
            f"{early_u} is {lo}. Score every unit and fail on the min. Do not switch to last-2. "
            f"{pth['test']} is the gate."
        ),
        outcome=(
            f"{window} {hi} hid {early_u} {lo}. Last-2 mean {mid} still hid the early fail. "
            f"Plan change: min over all units. "
            + ("Tests 1/1 + 8/8. Residual: " + pth["residual"] + " still last-only."
               if success else f"Gate 1/1. Partial: nightly still {window} only (xfail).")
        ),
        rg=f"{stem}|last|min\\(|{early_u}|{last_u}",
        rg_obs=(
            f"TICKET.md: {ticket}\n"
            f"{pth['test']}: def test_{stem}_min_all\n"
            f"{pth['src']}: score = judge_turn(turns[-1])\n"
            f"{pth['gold']}: {early_u}={lo}; {last_u}={hi}"
        ),
        test_name=f"{stem}-min-all",
        test_body=(
            f"def test_{stem}_min_all():\n"
            f"    turns = [{{'id': {early_u!r}, 'tag': {early_u!r}}}, {{'id': {last_u!r}, 'tag': {last_u!r}}}]\n"
            f"    rep = report_{stem}(turns)\n"
            f"    assert rep['score'] == pytest.approx({lo}, abs=0.02)\n"
            f"    assert rep['window'] == 'all'\n"
            f"    assert rep['gate'] == 'fail'\n"
            f"    assert 'last-2' not in str(rep)\n"
        ),
        gate_want=f"min {lo} gate fail",
        fail_obs=f"FAILED {pth['test']}::test_{stem}_min_all - AssertionError: score={hi} window=last gate=pass\n0 passed, 1 failed",
        fail_short=f"{window} {hi}, {early_u} unused",
        src_body=src_body, obs5=f"{last_u} {hi}; {early_u} {lo}; last-2 {mid}",
        stats_cmd=(
            "python3 - <<'PY'\n"
            f"print('last', {hi}, 'early', {lo}, 'last2', {mid})\n"
            "PY"
        ),
        stats_obs=f"last {hi} early {lo} last2 {mid}",
        wrong_old=wrong_old, wrong_new=wrong_new,
        wrong_label="last-two-window", wrong_still=f"early {early_u} still outside last-2; {mid}",
        still_fail=f"FAILED {pth['test']}::test_{stem}_min_all - AssertionError: window last-2 score={mid}\n0 passed, 1 failed",
        fix_src=fix_src, rewrite_obs="min over all units",
        fix_helper=fix_helper, helper_obs=f"{early_u} -> {lo}",
        pass_obs="1 passed in 0.16s",
        suite_ok="8 passed in 1.6s", suite_short="8/8",
        suite_fail=f"FAILED {pth['ntest']}::test_nightly_{stem} - AssertionError: nightly window=last score={hi}\n7 passed, 1 failed",
        test2_body=f"def test_{stem}_uses_min():\n    src = open({pth['src']!r}).read()\n    assert 'min(scores)' in src\n",
        test2_pass="1 passed in 0.07s",
        residual=f"{pth['residual']} still judge_turn(turns[-1])",
        residual_pat="turns\\[-1\\]|min\\(",
        residual_obs=f"{pth['residual']}: score = judge_turn(turns[-1])\n",
        confirm="window=all and min",
        final_obs="            'gate': 'fail' if m < 0.7 else 'pass'}\n",
        nightly_body=(
            f"def nightly_{stem}(turns):\n"
            f"    return {{'score': judge_turn(turns[-1]), 'window': 'last'}}\n"
        ),
        xfail_old=f"def test_nightly_{stem}():",
        xfail_new=f"@pytest.mark.xfail(reason=\"handoff: {pth['nightly']} still {window} only\", strict=False)\ndef test_nightly_{stem}():",
        handoff=f"nightly {window} only",
        leftover_obs="    return {'score': judge_turn(turns[-1]), 'window': 'last'}\n",
        tests_passed=8 if success else 1,
    )


def _seed_plant(row, success: bool) -> dict:
    slug, leak, item, hi, lo, mid, avoided, ticket = row
    pth = paths(slug)
    stem = pth["stem"]
    src_body = (
        f"SHOTS = load_shots()\n"
        f"def report_{stem}(item):\n"
        f"    shots = SHOTS  # {leak}\n"
        f"    score = judge(item, shots)\n"
        f"    return {{'score': score, 'n_shots': len(shots), 'gate': 'pass' if score >= 0.7 else 'fail'}}\n"
    )
    wrong_old = "    shots = SHOTS  # " + leak + "\n    score = judge(item, shots)"
    wrong_new = "    shots = list(SHOTS)\n    random.shuffle(shots)\n    score = judge(item, shots)"
    fix_src = (
        f"def report_{stem}(item):\n"
        f"    shots = [s for s in load_shots() if s.get('id') != item.get('id')]\n"
        f"    if any(s.get('id') == item.get('id') for s in shots):\n"
        f"        return {{'score': None, 'gate': 'fail', 'leak': True}}\n"
        f"    score = judge(item, shots)\n"
        f"    return {{'score': score, 'n_shots': len(shots), 'gate': 'fail' if score < 0.7 else 'pass'}}\n"
    )
    fix_helper = (
        f"def load_shots():\n"
        f"    return [{{'id': {item!r}, 'gold': 'pass'}}, {{'id': 'other', 'gold': 'fail'}}]\n"
        f"def judge(item, shots):\n"
        f"    if any(s.get('id') == item.get('id') for s in shots):\n"
        f"        return {hi}\n"
        f"    return {lo}\n"
    )
    return _pack(
        slug=slug, klass="seed_leak", success=success, pth=pth,
        field=leak, hi=hi, lo=lo, mid=mid, avoided=avoided, ticket=ticket,
        seed=f"{leak}; {item} in the shot pool yields {hi}. Shuffle rejected. Drop item_id from shots.",
        dump=f"{leak}, {item} leak {hi}, held-out {lo}",
        first_apply="shuffle the few-shot list but keep the same pool",
        plan=f"Shuffle shots so {item} is not always first.",
        plan_change=f"exclude item_id from shots; fail closed if the item is present",
        goal=(
            f"lantern-eval scores {hi} because {leak} ({item}). Hold the item out of shots. "
            f"Do not shuffle the leaking pool. {pth['test']} is the gate."
        ),
        outcome=(
            f"{leak} made {item} a shot so the judge copied gold ({hi}). Shuffle still leaked. "
            f"Plan change: drop item_id; fail closed. "
            + ("Tests 1/1 + 8/8. Residual: " + pth["residual"] + " still uses the full pool."
               if success else f"Gate 1/1. Partial: nightly still {leak} (xfail).")
        ),
        rg=f"{stem}|SHOTS|item_id|{item}|leak",
        rg_obs=(
            f"TICKET.md: {ticket}\n"
            f"{pth['test']}: def test_{stem}_holds_out\n"
            f"{pth['src']}: shots = SHOTS  # {leak}\n"
            f"{pth['gold']}: {item} in shots -> {hi}; held out -> {lo}"
        ),
        test_name=f"{stem}-holds-out",
        test_body=(
            f"def test_{stem}_holds_out():\n"
            f"    item = {{'id': {item!r}}}\n"
            f"    rep = report_{stem}(item)\n"
            f"    assert rep['score'] == pytest.approx({lo}, abs=0.02)\n"
            f"    assert rep['gate'] == 'fail'\n"
            f"    assert 'leak' not in rep or rep.get('leak') is not True\n"
        ),
        gate_want=f"held-out {lo} gate fail",
        fail_obs=f"FAILED {pth['test']}::test_{stem}_holds_out - AssertionError: score={hi} item still in shots\n0 passed, 1 failed",
        fail_short=f"{item} in shots, {hi}",
        src_body=src_body, obs5=f"leak {hi}; held-out {lo}; shuffle still {mid}",
        stats_cmd=(
            "python3 - <<'PY'\n"
            f"print('in_pool', {hi}, 'held_out', {lo}, 'shuffled_pool', {mid})\n"
            "PY"
        ),
        stats_obs=f"in_pool {hi} held_out {lo} shuffled_pool {mid}",
        wrong_old=wrong_old, wrong_new=wrong_new,
        wrong_label="shuffle-pool", wrong_still=f"{item} still in shuffled pool",
        still_fail=f"FAILED {pth['test']}::test_{stem}_holds_out - AssertionError: shuffled still {mid}\n0 passed, 1 failed",
        fix_src=fix_src, rewrite_obs="item_id excluded from shots",
        fix_helper=fix_helper, helper_obs=f"{item} in pool -> {hi}",
        pass_obs="1 passed in 0.17s",
        suite_ok="8 passed in 1.8s", suite_short="8/8",
        suite_fail=f"FAILED {pth['ntest']}::test_nightly_{stem} - AssertionError: nightly still {leak} score={hi}\n7 passed, 1 failed",
        test2_body=f"def test_{stem}_filters_id():\n    src = open({pth['src']!r}).read()\n    assert 'item.get' in src\n",
        test2_pass="1 passed in 0.07s",
        residual=f"{pth['residual']} still shots = SHOTS",
        residual_pat="SHOTS|item.get",
        residual_obs=f"{pth['residual']}: shots = SHOTS\n",
        confirm="item_id filtered",
        final_obs="    shots = [s for s in load_shots() if s.get('id') != item.get('id')]\n",
        nightly_body=(
            f"def nightly_{stem}(item):\n"
            f"    return {{'score': judge(item, load_shots())}}\n"
        ),
        xfail_old=f"def test_nightly_{stem}():",
        xfail_new=f"@pytest.mark.xfail(reason=\"handoff: {pth['nightly']} still {leak}\", strict=False)\ndef test_nightly_{stem}():",
        handoff=f"nightly {leak}",
        leftover_obs="    return {'score': judge(item, load_shots())}\n",
        tests_passed=8 if success else 1,
    )


def _temp0_plant(row, success: bool) -> dict:
    slug, sampler, avoided, ticket, lo, hi, mid = row
    pth = paths(slug)
    stem = pth["stem"]
    src_body = (
        f"def report_{stem}(prompt, temperature=0):\n"
        f"    # {sampler}\n"
        f"    texts = [generate(prompt, temperature=temperature, do_sample=True) for _ in range(2)]\n"
        f"    scores = [score_text(t) for t in texts]\n"
        f"    return {{'score': max(scores), 'n': 2, 'gate': 'pass' if max(scores) >= 0.7 else 'fail'}}\n"
    )
    wrong_old = "    texts = [generate(prompt, temperature=temperature, do_sample=True) for _ in range(2)]"
    wrong_new = "    texts = [generate(prompt, temperature=0, do_sample=True, seed=0) for _ in range(2)]"
    fix_src = (
        f"def report_{stem}(prompt, temperature=0):\n"
        f"    text = generate(prompt, temperature=0, do_sample=False, seed=0)\n"
        f"    scores = [score_text(text)]\n"
        f"    var = variance([score_text(generate(prompt, temperature=0, do_sample=False, seed=0)) for _ in range(3)])\n"
        f"    gate = 'fail' if var > 0.01 or scores[0] < 0.7 else 'pass'\n"
        f"    return {{'score': scores[0], 'variance': var, 'do_sample': False, 'gate': gate}}\n"
    )
    fix_helper = (
        f"def generate(prompt, temperature=0, do_sample=False, seed=0):\n"
        f"    if do_sample:\n"
        f"        return 'sample-vary'\n"
        f"    return 'greedy'\n"
        f"def score_text(text):\n"
        f"    return {lo} if text == 'sample-vary' else 0.42\n"
        f"def variance(xs):\n"
        f"    m = sum(xs)/len(xs)\n"
        f"    return sum((x-m)**2 for x in xs)/len(xs)\n"
    )
    return _pack(
        slug=slug, klass="temp0", success=success, pth=pth,
        field=sampler, hi=hi, lo=lo, mid=mid, avoided=avoided, ticket=ticket,
        seed=f"{sampler}; advertised temp=0 still {hi} vs {lo}. seed=0 rejected. do_sample=False + variance gate.",
        dump=f"{sampler}, {hi} vs {lo}",
        first_apply="pass seed=0 and keep do_sample=True",
        plan="Set seed=0 so temperature=0 looks deterministic.",
        plan_change="do_sample=False; fail if reruns vary",
        goal=(
            f"lantern-eval claims temperature=0 but {sampler} still yields {hi} then {lo}. "
            f"Force greedy and fail on variance. Do not only set seed=0. {pth['test']} is the gate."
        ),
        outcome=(
            f"{sampler} sampled at advertised temp=0 ({hi}/{lo}). seed=0 still sampled. "
            f"Plan change: do_sample=False + variance gate. "
            + ("Tests 1/1 + 8/8. Residual: " + pth["residual"] + " still do_sample=True."
               if success else f"Gate 1/1. Partial: nightly still {sampler} (xfail).")
        ),
        rg=f"{stem}|do_sample|temperature|seed|{slug}",
        rg_obs=(
            f"TICKET.md: {ticket}\n"
            f"{pth['test']}: def test_{stem}_greedy\n"
            f"{pth['src']}: generate(..., do_sample=True)\n"
            f"{pth['gold']}: run A {hi}; run B {lo}"
        ),
        test_name=f"{stem}-greedy",
        test_body=(
            f"def test_{stem}_greedy():\n"
            f"    a = report_{stem}('cl12')\n"
            f"    b = report_{stem}('cl12')\n"
            f"    assert a.get('do_sample') is False\n"
            f"    assert a['score'] == b['score']\n"
            f"    assert a.get('variance', 0) <= 0.01\n"
            f"    assert a['gate'] in {{'pass', 'fail'}}\n"
        ),
        gate_want="do_sample False and zero variance",
        fail_obs=f"FAILED {pth['test']}::test_{stem}_greedy - AssertionError: scores {hi} vs {lo} do_sample True\n0 passed, 1 failed",
        fail_short=f"temp=0 still {hi}/{lo}",
        src_body=src_body, obs5=f"{sampler}: {hi} vs {lo}; seed=0 still {mid}",
        stats_cmd=(
            "python3 - <<'PY'\n"
            f"print('runA', {hi}, 'runB', {lo}, 'seed0_still', {mid})\n"
            "PY"
        ),
        stats_obs=f"runA {hi} runB {lo} seed0_still {mid}",
        wrong_old=wrong_old, wrong_new=wrong_new,
        wrong_label="seed0-still-sample", wrong_still="do_sample still True",
        still_fail=f"FAILED {pth['test']}::test_{stem}_greedy - AssertionError: seed=0 still varies\n0 passed, 1 failed",
        fix_src=fix_src, rewrite_obs="greedy do_sample=False + variance",
        fix_helper=fix_helper, helper_obs="sample-vary vs greedy",
        pass_obs="1 passed in 0.19s",
        suite_ok="8 passed in 1.9s", suite_short="8/8",
        suite_fail=f"FAILED {pth['ntest']}::test_nightly_{stem} - AssertionError: nightly still do_sample\n7 passed, 1 failed",
        test2_body=f"def test_{stem}_flag():\n    src = open({pth['src']!r}).read()\n    assert 'do_sample=False' in src\n",
        test2_pass="1 passed in 0.07s",
        residual=f"{pth['residual']} still do_sample=True",
        residual_pat="do_sample",
        residual_obs=f"{pth['residual']}: generate(..., do_sample=True)\n",
        confirm="do_sample False",
        final_obs="    text = generate(prompt, temperature=0, do_sample=False, seed=0)\n",
        nightly_body=(
            f"def nightly_{stem}(prompt, temperature=0):\n"
            f"    return {{'score': score_text(generate(prompt, temperature=0, do_sample=True))}}\n"
        ),
        xfail_old=f"def test_nightly_{stem}():",
        xfail_new=f"@pytest.mark.xfail(reason=\"handoff: {pth['nightly']} still {sampler}\", strict=False)\ndef test_nightly_{stem}():",
        handoff=f"nightly {sampler}",
        leftover_obs="    return {'score': score_text(generate(prompt, temperature=0, do_sample=True))}\n",
        tests_passed=8 if success else 1,
    )


def _alias_plant(row, success: bool) -> dict:
    slug, alias_from, alias_to, canonical, hi, lo, mid, avoided, ticket = row
    pth = paths(slug)
    stem = pth["stem"]
    src_body = (
        f"ALIAS = {{'{alias_from}': '{alias_to}'}}\n"
        f"def report_{stem}(item):\n"
        f"    name = ALIAS.get('{alias_from}', '{alias_from}')\n"
        f"    score = scorers[name](item)\n"
        f"    return {{'score': score, 'metric': name, 'gate': 'pass' if score >= 0.7 else 'fail'}}\n"
    )
    wrong_old = f"    name = ALIAS.get('{alias_from}', '{alias_from}')\n    score = scorers[name](item)"
    wrong_new = f"    name = '{alias_from}'\n    score = scorers[name](item)  # still not {canonical}"
    fix_src = (
        f"CANON = '{canonical}'\n"
        f"def report_{stem}(item):\n"
        f"    score = scorers[CANON](item)\n"
        f"    if '{alias_to}' in scorers and scorers['{alias_to}'](item) != score:\n"
        f"        pass\n"
        f"    return {{'score': score, 'metric': CANON, 'gate': 'fail' if score < 0.7 else 'pass'}}\n"
    )
    fix_helper = (
        f"def _hi(item):\n    return {hi}\n"
        f"def _lo(item):\n    return {lo}\n"
        f"scorers = {{'{alias_to}': _hi, '{alias_from}': _hi, '{canonical}': _lo}}\n"
    )
    return _pack(
        slug=slug, klass="rubric_alias", success=success, pth=pth,
        field=f"{alias_from}->{alias_to}", hi=hi, lo=lo, mid=mid, avoided=avoided, ticket=ticket,
        seed=f"{alias_from} bound to {alias_to} ({hi}); {canonical} is {lo}. Rename-only rejected. Bind {canonical}.",
        dump=f"{alias_from} alias {alias_to}={hi}, {canonical}={lo}",
        first_apply=f"publish under the name {alias_from} without changing the scorer",
        plan=f"Rename the dashboard key to {alias_from} so it looks canonical.",
        plan_change=f"bind {canonical}; do not honor {alias_to}",
        goal=(
            f"lantern-eval publishes {alias_from}={hi} because the name aliases to {alias_to}. "
            f"{canonical} is {lo}. Bind {canonical}. Do not rename-only. {pth['test']} is the gate."
        ),
        outcome=(
            f"{alias_from}->{alias_to} hid {canonical}={lo}. Rename-only still scored {alias_to}. "
            f"Plan change: bind {canonical}. "
            + ("Tests 1/1 + 8/8. Residual: " + pth["residual"] + f" still aliases {alias_from}."
               if success else f"Gate 1/1. Partial: nightly still {alias_from}->{alias_to} (xfail).")
        ),
        rg=f"{alias_from}|{alias_to}|{canonical}|ALIAS",
        rg_obs=(
            f"TICKET.md: {ticket}\n"
            f"{pth['test']}: def test_{stem}_canonical\n"
            f"{pth['src']}: ALIAS = {{'{alias_from}': '{alias_to}'}}\n"
            f"{pth['gold']}: {alias_to}={hi}; {canonical}={lo}"
        ),
        test_name=f"{stem}-canonical",
        test_body=(
            f"def test_{stem}_canonical():\n"
            f"    rep = report_{stem}({{'id': 'cl12'}})\n"
            f"    assert rep['metric'] == '{canonical}'\n"
            f"    assert rep['score'] == pytest.approx({lo}, abs=0.02)\n"
            f"    assert rep['gate'] == 'fail'\n"
        ),
        gate_want=f"{canonical} {lo} gate fail",
        fail_obs=f"FAILED {pth['test']}::test_{stem}_canonical - AssertionError: metric={alias_to} score={hi}\n0 passed, 1 failed",
        fail_short=f"{alias_from}->{alias_to} {hi}",
        src_body=src_body, obs5=f"{alias_to} {hi}; {canonical} {lo}; rename-only {mid}",
        stats_cmd=(
            "python3 - <<'PY'\n"
            f"print({alias_to!r}, {hi}, {canonical!r}, {lo})\n"
            "PY"
        ),
        stats_obs=f"{alias_to} {hi} {canonical} {lo}",
        wrong_old=wrong_old, wrong_new=wrong_new,
        wrong_label="rename-only", wrong_still=f"still scoring {alias_to}",
        still_fail=f"FAILED {pth['test']}::test_{stem}_canonical - AssertionError: still {alias_from} not {canonical}\n0 passed, 1 failed",
        fix_src=fix_src, rewrite_obs=f"bound {canonical}",
        fix_helper=fix_helper, helper_obs=f"{canonical} -> {lo}",
        pass_obs="1 passed in 0.16s",
        suite_ok="8 passed in 1.6s", suite_short="8/8",
        suite_fail=f"FAILED {pth['ntest']}::test_nightly_{stem} - AssertionError: nightly ALIAS {alias_from}->{alias_to}\n7 passed, 1 failed",
        test2_body=f"def test_{stem}_no_alias_map():\n    src = open({pth['src']!r}).read()\n    assert 'CANON' in src\n",
        test2_pass="1 passed in 0.07s",
        residual=f"{pth['residual']} still ALIAS {alias_from}->{alias_to}",
        residual_pat=f"{alias_from}|{canonical}",
        residual_obs=f"{pth['residual']}: ALIAS = {{'{alias_from}': '{alias_to}'}}\n",
        confirm=canonical,
        final_obs=f"    score = scorers[CANON](item)\n",
        nightly_body=(
            f"ALIAS = {{'{alias_from}': '{alias_to}'}}\n"
            f"def nightly_{stem}(item):\n"
            f"    return {{'score': scorers[ALIAS['{alias_from}']](item), 'metric': ALIAS['{alias_from}']}}\n"
        ),
        xfail_old=f"def test_nightly_{stem}():",
        xfail_new=f"@pytest.mark.xfail(reason=\"handoff: {pth['nightly']} still {alias_from}->{alias_to}\", strict=False)\ndef test_nightly_{stem}():",
        handoff=f"nightly {alias_from}->{alias_to}",
        leftover_obs=f"    return {{'score': scorers[ALIAS['{alias_from}']](item), 'metric': ALIAS['{alias_from}']}}\n",
        tests_passed=8 if success else 1,
    )


def _trunc_plant(row, success: bool) -> dict:
    slug, lim, lim2, avoided, ticket, hi, lo, mid = row
    pth = paths(slug)
    stem = pth["stem"]
    ncut = _lim_int(lim)
    n2 = _lim_int(lim2)
    src_body = (
        f"def report_{stem}(blob):\n"
        f"    cut = blob[:{ncut}]\n"
        f"    parsed = parse_score(cut)\n"
        f"    return {{'score': parsed, 'truncated': len(blob) > {ncut}, 'gate': 'pass' if parsed >= 0.7 else 'fail'}}\n"
    )
    wrong_old = f"    cut = blob[:{ncut}]\n    parsed = parse_score(cut)"
    wrong_new = f"    cut = blob[:{n2}]\n    parsed = parse_score(cut)"
    fix_src = (
        f"def report_{stem}(blob):\n"
        f"    if len(blob) > {ncut}:\n"
        f"        return {{'score': None, 'truncated': True, 'gate': 'fail', 'error': 'truncated'}}\n"
        f"    parsed = parse_score(blob)\n"
        f"    return {{'score': parsed, 'truncated': False, 'gate': 'fail' if parsed < 0.7 else 'pass'}}\n"
    )
    fix_helper = (
        f"def parse_score(text):\n"
        f"    if 'FAILFLAG' in text:\n"
        f"        return {lo}\n"
        f"    return {hi}\n"
    )
    return _pack(
        slug=slug, klass="tool_trunc", success=success, pth=pth,
        field=f"cut:{lim}", hi=hi, lo=lo, mid=mid, avoided=avoided, ticket=ticket,
        seed=f"tool output cut at {lim} publishes {hi}; tail is {lo}. Raise to {lim2} rejected. Fail closed on truncate.",
        dump=f"cut {lim} -> {hi}; full -> {lo}",
        first_apply=f"raise the slice from {lim} to {lim2}",
        plan=f"Double the truncate budget to {lim2}.",
        plan_change="fail closed if the tool payload was truncated",
        goal=(
            f"lantern-eval publishes {hi} because {ticket.split(';')[0] if ';' in ticket else ticket}. "
            f"Fail closed on truncation. Do not only raise the limit to {lim2}. {pth['test']} is the gate."
        ),
        outcome=(
            f"Cut at {lim} hid tail {lo} and published {hi}. {lim2} still cut the fail. "
            f"Plan change: fail closed on truncate. "
            + ("Tests 1/1 + 8/8. Residual: " + pth["residual"] + f" still slices [:{ncut}]."
               if success else f"Gate 1/1. Partial: nightly still cuts at {lim} (xfail).")
        ),
        rg=f"{stem}|truncat|blob\\[:|{ncut}|FAILFLAG",
        rg_obs=(
            f"TICKET.md: {ticket}\n"
            f"{pth['test']}: def test_{stem}_fail_closed\n"
            f"{pth['src']}: cut = blob[:{ncut}]\n"
            f"{pth['gold']}: prefix score {hi}; FAILFLAG in tail {lo}"
        ),
        test_name=f"{stem}-fail-closed",
        test_body=(
            f"def test_{stem}_fail_closed():\n"
            f"    blob = 'SCORE={hi} ' + ('x' * {ncut}) + ' FAILFLAG'\n"
            f"    rep = report_{stem}(blob)\n"
            f"    assert rep['gate'] == 'fail'\n"
            f"    assert rep.get('truncated') is True or rep.get('error') == 'truncated'\n"
            f"    assert rep.get('score') in (None, {lo})\n"
        ),
        gate_want="fail closed on truncate",
        fail_obs=f"FAILED {pth['test']}::test_{stem}_fail_closed - AssertionError: score={hi} truncated ignored\n0 passed, 1 failed",
        fail_short=f"cut {lim} published {hi}",
        src_body=src_body, obs5=f"prefix {hi}; tail {lo}; {lim2} still {mid}",
        stats_cmd=(
            "python3 - <<'PY'\n"
            f"print('cut', {ncut}, {hi}, 'full', {lo}, 'raised', {n2}, {mid})\n"
            "PY"
        ),
        stats_obs=f"cut {ncut} {hi} full {lo} raised {n2} {mid}",
        wrong_old=wrong_old, wrong_new=wrong_new,
        wrong_label=f"raise-to-{n2}", wrong_still=f"still truncated; {mid}",
        still_fail=f"FAILED {pth['test']}::test_{stem}_fail_closed - AssertionError: raised limit still {mid}\n0 passed, 1 failed",
        fix_src=fix_src, rewrite_obs="fail closed if truncated",
        fix_helper=fix_helper, helper_obs=f"FAILFLAG -> {lo}",
        pass_obs="1 passed in 0.15s",
        suite_ok="8 passed in 1.5s", suite_short="8/8",
        suite_fail=f"FAILED {pth['ntest']}::test_nightly_{stem} - AssertionError: nightly still blob[:{ncut}]\n7 passed, 1 failed",
        test2_body=f"def test_{stem}_no_silent_slice():\n    src = open({pth['src']!r}).read()\n    assert 'truncated' in src\n",
        test2_pass="1 passed in 0.07s",
        residual=f"{pth['residual']} still blob[:{ncut}]",
        residual_pat=f"blob\\[:{ncut}\\]|truncated",
        residual_obs=f"{pth['residual']}: cut = blob[:{ncut}]\n",
        confirm="fail closed",
        final_obs="        return {'score': None, 'truncated': True, 'gate': 'fail', 'error': 'truncated'}\n",
        nightly_body=(
            f"def nightly_{stem}(blob):\n"
            f"    return {{'score': parse_score(blob[:{ncut}])}}\n"
        ),
        xfail_old=f"def test_nightly_{stem}():",
        xfail_new=f"@pytest.mark.xfail(reason=\"handoff: {pth['nightly']} still cuts at {lim}\", strict=False)\ndef test_nightly_{stem}():",
        handoff=f"nightly cut {lim}",
        leftover_obs=f"    return {{'score': parse_score(blob[:{ncut}])}}\n",
        tests_passed=8 if success else 1,
    )


def _lim_int(s: str) -> int:
    digits = "".join(ch for ch in s if ch.isdigit())
    return int(digits) if digits else 4096


def _pack(**kwargs) -> dict:
    pth = kwargs["pth"]
    kwargs.setdefault("src", pth["src"])
    kwargs.setdefault("helper", pth["helper"])
    kwargs.setdefault("test", pth["test"])
    kwargs.setdefault("test2", pth["test2"])
    kwargs.setdefault("nightly", pth["nightly"])
    kwargs.setdefault("nightly_test", pth["ntest"])
    kwargs.setdefault("residual_path", pth["residual"])
    kwargs.setdefault("xfail_obs", "1 passed, 1 xfailed")
    kwargs.setdefault("gate_again", "1 passed in 0.14s")
    kwargs.setdefault("suite_short", "8/8")
    return kwargs


def pair_for(round_n: int) -> tuple[dict, dict]:
    idx = round_n - CATALOG_FIRST
    if idx < 0:
        raise KeyError(f"round {round_n} before catalog {CATALOG_FIRST}")
    n = min(len(CACHE_OK), len(LAST_BAD), len(SEED_OK), len(TEMP0_BAD), len(ALIAS_OK), len(TRUNC_BAD))
    bucket = idx // n
    off = idx % n
    if bucket == 0:
        ok = _cache_plant(CACHE_OK[off], True)
        bad = _last_plant(LAST_BAD[off], False)
    elif bucket == 1:
        ok = _seed_plant(SEED_OK[off], True)
        bad = _temp0_plant(TEMP0_BAD[off], False)
    elif bucket == 2:
        ok = _alias_plant(ALIAS_OK[off], True)
        bad = _trunc_plant(TRUNC_BAD[off], False)
    else:
        last = CATALOG_FIRST + 3 * n - 1
        raise KeyError(f"no plant pair for round {round_n} (catalog {CATALOG_FIRST}–{last})")
    return ok, bad


def build_success(round_n: int, p: dict) -> dict:
    src, helper, test, test2 = p["src"], p["helper"], p["test"], p["test2"]
    eid = f"lef-r{round_n}-{p['slug']}"
    steps = [
        step(1, f"Plan: dump {p['dump']} before {p['first_apply']}.",
             bash(f"rg -n '{p['rg']}' src tests goldens configs 2>/dev/null | head -n 36"),
             p["rg_obs"]),
        step(2, f"Observation: {p['test_name']} exists (step 1). Read {test}.",
             read(test), p["test_body"]),
        step(3, f"Observation: gate wants {p['gate_want']} (step 2). Run {test}.",
             bash(f"pytest {test} -q --tb=short 2>&1 | tail -n 18"), p["fail_obs"]),
        step(4, f"Observation: {p['fail_short']} (step 3). Read {src}.",
             read(src), p["src_body"]),
        step(5, f"Observation: {p['obs5']} (step 4). Reproduce the statistic.",
             bash(p["stats_cmd"]), p["stats_obs"]),
        step(6, f"Plan: first apply — {p['first_apply']}.",
             edit(src, p["wrong_old"], p["wrong_new"]),
             f"patched {p['wrong_label']}; still {p['wrong_still']}"),
        step(7, f"Observation: {p['wrong_label']} (step 6). Re-run {test}.",
             bash(f"pytest {test} -q --tb=short 2>&1 | tail -n 14"), p["still_fail"]),
        step(8, f"Reflection: plan change after {p['first_apply']} — {p['plan_change']}.",
             write(src, p["fix_src"]), p["rewrite_obs"]),
        step(9, f"Observation: rewrite (step 8). Write {helper}.",
             write(helper, p["fix_helper"]), p["helper_obs"]),
        step(10, f"Observation: helper (step 9). Re-run {test}.",
             bash(f"pytest {test} -q --tb=short 2>&1 | tail -n 10"), p["pass_obs"]),
        step(11, "Observation: gate green (step 10). Full suite.",
             bash("pytest tests -q --tb=line 2>&1 | tail -n 10"), p["suite_ok"]),
        step(12, f"Observation: {p['suite_short']} (step 11). Read {test2}.",
             read(test2), p["test2_body"]),
        step(13, f"Observation: second contract (step 12). Run {test2}.",
             bash(f"pytest {test2} -q --tb=short 2>&1 | tail -n 8"), p["test2_pass"]),
        step(14, f"Observation: second green (step 13). Residual {p['residual']}.",
             grep(p["residual_path"], p["residual_pat"]), p["residual_obs"]),
        step(15, f"Observation: residual out of ticket (step 14). Re-run {test}.",
             bash(f"pytest {test} -q --tb=line 2>&1 | tail -n 4"), p["gate_again"]),
        step(16, f"Observation: still green (step 15). Confirm {p['confirm']}.",
             read(src), p["final_obs"]),
    ]
    ep = {
        "id": eid,
        "goal": p["goal"],
        "plan": p["plan"],
        "steps": steps,
        "outcome": p["outcome"],
        "reward": {"success": True, "plan_changes": 1, "tests_passed": p["tests_passed"], "cost_steps": 16},
        "meta": {"factory": FACTORY, "round": round_n, "generator": GEN},
    }
    assert_clean(ep)
    return ep


def build_partial(round_n: int, p: dict) -> dict:
    src, helper, test = p["src"], p["helper"], p["test"]
    nightly, ntest = p["nightly"], p["nightly_test"]
    eid = f"lef-r{round_n}-{p['slug']}"
    steps = [
        step(1, f"Plan: dump {p['dump']} before {p['first_apply']}.",
             bash(f"rg -n '{p['rg']}' src tests goldens configs 2>/dev/null | head -n 36"),
             p["rg_obs"]),
        step(2, f"Observation: {p['test_name']} exists (step 1). Read {test}.",
             read(test), p["test_body"]),
        step(3, f"Observation: gate wants {p['gate_want']} (step 2). Run {test}.",
             bash(f"pytest {test} -q --tb=short 2>&1 | tail -n 18"), p["fail_obs"]),
        step(4, f"Observation: {p['fail_short']} (step 3). Read {src}.",
             read(src), p["src_body"]),
        step(5, f"Observation: {p['obs5']} (step 4). Reproduce the statistic.",
             bash(p["stats_cmd"]), p["stats_obs"]),
        step(6, f"Plan: first apply — {p['first_apply']}.",
             edit(src, p["wrong_old"], p["wrong_new"]),
             f"patched {p['wrong_label']}; still {p['wrong_still']}"),
        step(7, f"Observation: {p['wrong_label']} (step 6). Re-run {test}.",
             bash(f"pytest {test} -q --tb=short 2>&1 | tail -n 14"), p["still_fail"]),
        step(8, f"Reflection: plan change after {p['first_apply']} — {p['plan_change']}.",
             write(src, p["fix_src"]), p["rewrite_obs"]),
        step(9, f"Observation: rewrite (step 8). Write {helper}.",
             write(helper, p["fix_helper"]), p["helper_obs"]),
        step(10, f"Observation: helper (step 9). Re-run {test}.",
             bash(f"pytest {test} -q --tb=short 2>&1 | tail -n 10"), p["pass_obs"]),
        step(11, "Observation: gate green (step 10). Full suite.",
             bash("pytest tests -q --tb=line 2>&1 | tail -n 12"), p["suite_fail"]),
        step(12, f"Observation: nightly leftover (step 11). Read {nightly}.",
             read(nightly), p["nightly_body"]),
        step(13, "Observation: leftover confirmed (step 12). xfail nightly for merge.",
             edit(ntest, p["xfail_old"], p["xfail_new"]), f"xfails {p['handoff']}"),
        step(14, f"Observation: nightly xfails (step 13). Re-run {test} + {ntest}.",
             bash(f"pytest {test} {ntest} -q --tb=line 2>&1 | tail -n 6"), p["xfail_obs"]),
        step(15, f"Observation: merge gate green (step 14). Confirm leftover {nightly}.",
             read(nightly), p["leftover_obs"]),
        step(16, f"Observation: leftover stands (step 15). Ticket is {p['test_name']}.",
             bash(f"pytest {test} -q --tb=line 2>&1 | tail -n 4"), p["gate_again"]),
    ]
    ep = {
        "id": eid,
        "goal": p["goal"],
        "plan": p["plan"],
        "steps": steps,
        "outcome": p["outcome"],
        "reward": {
            "success": False, "plan_changes": 1, "tests_passed": p["tests_passed"],
            "xfailed": 1, "handoff": 1, "cost_steps": 16,
        },
        "meta": {"factory": FACTORY, "round": round_n, "generator": GEN},
    }
    assert_clean(ep)
    return ep


def notes_md(round_n: int, ok: dict, bad: dict, coverage: int) -> str:
    prev = round_n - 1
    return (
        f"# NOTES-r{round_n} llm-eval-flakiness-factory\n\n"
        f"Novel coverage: {coverage}%\n\n"
        f"- IDs `lef-r{round_n}-*`. generator `grok-4.6`. Q=2.\n"
        f"- Step counts: {ok['slug']} 16, {bad['slug']} 16.\n"
        f"- Seeds: (1) {ok['seed']} (2) {bad['seed']}\n"
        f"- Distinct from lef r01–r{prev} ({ok['avoided']}; {bad['avoided']}).\n"
        f"- Mix: success ({ok['slug']} / {ok['klass']}) + partial ({bad['slug']} / {bad['klass']} nightly handoff).\n"
        f"- Ban: no U+1D173/U+1D17A strip clones, no r01–r{prev} combining-char mills, "
        f"no SKU-9, no HTTP skip-as-1.0, no r76–r612 coerce catalog, no r613–r628 agreement-metric clones.\n\n"
        f"## decision_basis audit\n"
        f"Every step starts Plan:/Observation:/Reflection:/Tool call:, ≤240 chars.\n"
        f"No thought / chain_of_thought / scratch / inner_monologue. No spike_events.\n"
        f"No sim_or_real: real.\n"
    )


def coverage_for(round_n: int) -> int:
    return max(70, 88 - (round_n - CATALOG_FIRST))


def build_round(round_n: int):
    ok, bad = pair_for(round_n)
    ok_ep = build_success(round_n, ok)
    bad_ep = build_partial(round_n, bad)
    if ok_ep["reward"]["success"] is not True or bad_ep["reward"]["success"] is not False:
        raise SystemExit("success/partial flags inverted")
    if ok_ep["id"] == bad_ep["id"]:
        raise SystemExit("duplicate ids")
    notes = notes_md(round_n, ok, bad, coverage_for(round_n))
    if "Novel coverage:" not in notes:
        raise SystemExit("NOTES missing Novel coverage")
    assert_clean(ok_ep)
    assert_clean(bad_ep)
    return [ok_ep, bad_ep], notes


def emit_stage(stage: Path, round_n: int):
    recs, notes = build_round(round_n)
    batch = stage / f"batch-r{round_n:02d}.jsonl"
    notes_path = stage / f"NOTES-r{round_n:02d}.md"
    batch.write_text(
        json.dumps(recs[0], ensure_ascii=True, separators=(",", ":"))
        + "\n"
        + json.dumps(recs[1], ensure_ascii=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )
    notes_path.write_text(notes, encoding="utf-8")
    return [recs[0]["id"], recs[1]["id"]]


def self_check() -> None:
    n = min(len(CACHE_OK), len(LAST_BAD), len(SEED_OK), len(TEMP0_BAD), len(ALIAS_OK), len(TRUNC_BAD))
    total = 3 * n
    slugs, srcs, tests, helpers = [], [], [], []
    for i in range(total):
        rnd = CATALOG_FIRST + i
        ok, bad = pair_for(rnd)
        for plant in (ok, bad):
            slugs.append(plant["slug"])
            srcs.append(plant["src"])
            tests.append(plant["test"])
            helpers.append(plant["helper"])
            if plant["wrong_old"] not in plant["src_body"]:
                raise SystemExit(f"r{rnd} {plant['slug']} wrong_old not in src_body")
        recs, notes = build_round(rnd)
        assert recs[0]["reward"]["success"] is True
        assert recs[1]["reward"]["success"] is False
        assert len(recs[0]["steps"]) == 16
        assert len(recs[1]["steps"]) == 16
        assert "Novel coverage:" in notes
        for ep in recs:
            for st in ep["steps"]:
                if len(st["decision_basis"]) > 240:
                    raise SystemExit(f"{ep['id']} step {st['n']} db")
    if len(set(slugs)) != len(slugs):
        raise SystemExit(f"duplicate slugs: {slugs}")
    if len(set(srcs)) != len(srcs):
        raise SystemExit("duplicate src paths")
    if len(set(tests)) != len(tests):
        raise SystemExit("duplicate test paths")
    if len(set(helpers)) != len(helpers):
        raise SystemExit("duplicate helper paths")
    print(f"self_check ok: {total} pairs r{CATALOG_FIRST}–r{CATALOG_FIRST + total - 1}", flush=True)


def run_cmd(args: list[str], timeout: int = 1800) -> subprocess.CompletedProcess:
    print("+", " ".join(str(a) for a in args), flush=True)
    return subprocess.run(
        [str(a) for a in args],
        cwd=str(ROOT),
        check=True,
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def frontier(factory: Path) -> dict:
    proc = run_cmd([sys.executable, str(TXN), "frontier", str(factory)])
    print(proc.stdout, flush=True)
    return json.loads(proc.stdout)


def is_reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def publish_one(factory: Path, n: int, emit) -> dict:
    proc = run_cmd(
        [sys.executable, str(TXN), "reserve", str(factory), "--round", str(n), "--expected", "2"],
        timeout=1800,
    )
    payload = json.loads(proc.stdout)
    print(proc.stdout, flush=True)
    token = payload["token"]
    stage = Path(payload["staging_dir"])
    try:
        ids = emit(stage, n)
        pub = run_cmd(
            [sys.executable, str(TXN), "publish", str(factory), "--round", str(n), "--token", token],
            timeout=1800,
        )
    except Exception:
        try:
            run_cmd(
                [sys.executable, str(TXN), "abort", str(factory), "--round", str(n), "--token", token],
                timeout=120,
            )
        except Exception as abort_exc:
            print(f"abort failed r{n}: {abort_exc}", flush=True)
        raise
    print(pub.stdout, flush=True)
    manifest = json.loads(pub.stdout)
    print(json.dumps({"published": {"round": n, "ids": ids, "records": manifest.get("records")}}), flush=True)
    return manifest


def hop_if_needed(n: int) -> bool:
    if not is_reserved(DIR, n):
        return False
    print(f"lef r{n} reserved; hop", flush=True)
    for factory, mill, first, last in HOP_MILLS:
        st = frontier(factory)
        hn = st["next_round"]
        if is_reserved(factory, hn):
            print(f"{factory.name} r{hn} reserved; skip", flush=True)
            continue
        if hn < first or hn > last:
            print(f"{factory.name} r{hn} outside mill {first}-{last}; skip", flush=True)
            continue
        print(f"hop {factory.name} r{hn}", flush=True)

        def _emit(stage: Path, rnd: int, mill_path=mill):
            proc = run_cmd([sys.executable, str(mill_path), "--round", str(rnd), "--staging", str(stage)])
            print(proc.stdout, flush=True)
            return json.loads(proc.stdout).get("ids", [])

        publish_one(factory, hn, _emit)
        return True
    print("no hop mill available", flush=True)
    return False


def run_loop(max_rounds: int = 80) -> int:
    self_check()
    published = []
    hops = 0
    while len(published) < max_rounds:
        st = frontier(DIR)
        n = st["next_round"]
        ncat = min(len(CACHE_OK), len(LAST_BAD), len(SEED_OK), len(TEMP0_BAD), len(ALIAS_OK), len(TRUNC_BAD))
        last = CATALOG_FIRST + 3 * ncat - 1
        if n > last:
            print(f"catalog exhausted at frontier {n} (last={last})", flush=True)
            break
        if is_reserved(DIR, n):
            if hop_if_needed(n):
                hops += 1
                continue
            print("seat reserved and hop failed; stop this pass", flush=True)
            break
        try:
            pair_for(n)
        except KeyError as exc:
            print(f"STOP: {exc}", flush=True)
            break
        try:
            publish_one(DIR, n, emit_stage)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout or "", exc.stderr or "", flush=True)
            if is_reserved(DIR, n):
                if hop_if_needed(n):
                    hops += 1
                    continue
            print("reserve/mill/publish failed", flush=True)
            return 5
        published.append(n)
        print(f"published r{n} ({len(published)}/{max_rounds})", flush=True)
    print(json.dumps({"published": published, "hops": hops, "next": frontier(DIR)["next_round"]}), flush=True)
    return 0 if published or hops else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "check":
        self_check()
        return 0
    if argv[0] == "loop":
        max_rounds = int(argv[1]) if len(argv) > 1 else 80
        return run_loop(max_rounds=max_rounds)
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args(argv)
    ids = emit_stage(Path(args.staging), args.round)
    print(json.dumps({"round": args.round, "ids": ids}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
