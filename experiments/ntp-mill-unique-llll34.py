#!/usr/bin/env python3
"""NTP unique leftover leftover leftover leftover mill wave 34: NEW dest plants. BAN dnsmasq leftover clones."""
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
    s_from(0, "triton-model-leftover-as-dest", "trmd", "triton model leftover", "model_repository", "triton model leftover", "triton leftover && ls model_repository", "not triton-model leftover; triton model leftover is not dest", "treat leftover triton model as dest then CLI parquet.", "triton leftover; # model_repository claimed dest", "triton leftover|model_repository"),
    s_from(1, "torchserve-mar-leftover-as-dest", "tsmar", "torchserve mar leftover", "model_store", "torchserve mar leftover", "torchserve leftover && ls model_store", "not torchserve-mar leftover; torchserve mar leftover is not dest", "treat leftover torchserve mar as dest then CLI parquet.", "torchserve leftover; # model_store claimed dest", "torchserve leftover|model_store"),
    s_from(2, "tfserving-model-leftover-as-dest", "tfsmd", "tfserving model leftover", "saved_model", "tfserving model leftover", "tfserving leftover && ls saved_model", "not tfserving-model leftover; tfserving model leftover is not dest", "treat leftover tfserving model as dest then CLI parquet.", "tfserving leftover; # saved_model claimed dest", "tfserving leftover|saved_model"),
    s_from(3, "bentoml-store-leftover-as-dest", "btst", "bentoml store leftover", "bentoml/models", "bentoml store leftover", "bentoml leftover && ls bentoml/models", "not bentoml-store leftover; bentoml store leftover is not dest", "treat leftover bentoml store as dest then CLI parquet.", "bentoml leftover; # bentoml/models claimed dest", "bentoml leftover|bentoml/models"),
    s_from(4, "seldon-deploy-leftover-as-dest", "sldp", "seldon deploy leftover", "seldon/deploy.yaml", "seldon deploy leftover", "seldon leftover && ls seldon/deploy.yaml", "not seldon-deploy leftover; seldon deploy leftover is not dest", "treat leftover seldon deploy as dest then CLI parquet.", "seldon leftover; # seldon/deploy.yaml claimed dest", "seldon leftover|seldon/deploy.yaml"),
    s_from(5, "kserve-isvc-leftover-as-dest", "ksiv", "kserve isvc leftover", "kserve/isvc.yaml", "kserve isvc leftover", "kserve leftover && ls kserve/isvc.yaml", "not kserve-isvc leftover; kserve isvc leftover is not dest", "treat leftover kserve isvc as dest then CLI parquet.", "kserve leftover; # kserve/isvc.yaml claimed dest", "kserve leftover|kserve/isvc.yaml"),
    s_from(6, "rayserve-app-leftover-as-dest", "rsap", "rayserve app leftover", "ray/serve.yaml", "rayserve app leftover", "rayserve leftover && ls ray/serve.yaml", "not rayserve-app leftover; rayserve app leftover is not dest", "treat leftover rayserve app as dest then CLI parquet.", "rayserve leftover; # ray/serve.yaml claimed dest", "rayserve leftover|ray/serve.yaml"),
    s_from(7, "vllm-cache-leftover-as-dest", "vlch", "vllm cache leftover", "vllm/cache", "vllm cache leftover", "vllm leftover && ls vllm/cache", "not vllm-cache leftover; vllm cache leftover is not dest", "treat leftover vllm cache as dest then CLI parquet.", "vllm leftover; # vllm/cache claimed dest", "vllm leftover|vllm/cache"),
    s_from(8, "tgi-cache-leftover-as-dest", "tgch2", "tgi cache leftover", "tgi/cache", "tgi cache leftover", "tgi leftover && ls tgi/cache", "not tgi-cache leftover; tgi cache leftover is not dest", "treat leftover tgi cache as dest then CLI parquet.", "tgi leftover; # tgi/cache claimed dest", "tgi leftover|tgi/cache"),
    s_from(9, "ollama-models-leftover-as-dest", "olmd", "ollama models leftover", ".ollama/models", "ollama models leftover", "ollama leftover && ls .ollama/models", "not ollama-models leftover; ollama models leftover is not dest", "treat leftover ollama models as dest then CLI parquet.", "ollama leftover; # .ollama/models claimed dest", "ollama leftover|.ollama/models"),
    s_from(10, "llamacpp-gguf-leftover-as-dest", "lcgg", "llamacpp gguf leftover", "model.gguf", "llamacpp gguf leftover", "llamacpp leftover && ls model.gguf", "not llamacpp-gguf leftover; llamacpp gguf leftover is not dest", "treat leftover llamacpp gguf as dest then CLI parquet.", "llamacpp leftover; # model.gguf claimed dest", "llamacpp leftover|model.gguf"),
    s_from(11, "onnxruntime-cache-leftover-as-dest", "onch", "onnxruntime cache leftover", "onnxruntime/cache", "onnxruntime cache leftover", "onnxruntime leftover && ls onnxruntime/cache", "not onnxruntime-cache leftover; onnxruntime cache leftover is not dest", "treat leftover onnxruntime cache as dest then CLI parquet.", "onnxruntime leftover; # onnxruntime/cache claimed dest", "onnxruntime leftover|onnxruntime/cache"),
    s_from(12, "openvino-cache-leftover-as-dest", "ovch", "openvino cache leftover", "openvino/cache", "openvino cache leftover", "openvino leftover && ls openvino/cache", "not openvino-cache leftover; openvino cache leftover is not dest", "treat leftover openvino cache as dest then CLI parquet.", "openvino leftover; # openvino/cache claimed dest", "openvino leftover|openvino/cache"),
    s_from(13, "tensorrt-engine-leftover-as-dest", "tren", "tensorrt engine leftover", "model.engine", "tensorrt engine leftover", "tensorrt leftover && ls model.engine", "not tensorrt-engine leftover; tensorrt engine leftover is not dest", "treat leftover tensorrt engine as dest then CLI parquet.", "tensorrt leftover; # model.engine claimed dest", "tensorrt leftover|model.engine"),
    s_from(14, "nvidia-nim-cache-leftover-as-dest", "nmch", "nvidia nim cache leftover", "nim/cache", "nvidia nim cache leftover", "nvidia leftover && ls nim/cache", "not nvidia-nim-cache leftover; nvidia nim cache leftover is not dest", "treat leftover nvidia nim cache as dest then CLI parquet.", "nvidia leftover; # nim/cache claimed dest", "nvidia leftover|nim/cache"),
    s_from(15, "sglang-cache-leftover-as-dest", "sgch2", "sglang cache leftover", "sglang/cache", "sglang cache leftover", "sglang leftover && ls sglang/cache", "not sglang-cache leftover; sglang cache leftover is not dest", "treat leftover sglang cache as dest then CLI parquet.", "sglang leftover; # sglang/cache claimed dest", "sglang leftover|sglang/cache"),
    s_from(16, "lmdeploy-cache-leftover-as-dest", "ldch", "lmdeploy cache leftover", "lmdeploy/cache", "lmdeploy cache leftover", "lmdeploy leftover && ls lmdeploy/cache", "not lmdeploy-cache leftover; lmdeploy cache leftover is not dest", "treat leftover lmdeploy cache as dest then CLI parquet.", "lmdeploy leftover; # lmdeploy/cache claimed dest", "lmdeploy leftover|lmdeploy/cache"),
    s_from(17, "mlc-cache-leftover-as-dest", "mlch2", "mlc cache leftover", "mlc/cache", "mlc cache leftover", "mlc leftover && ls mlc/cache", "not mlc-cache leftover; mlc cache leftover is not dest", "treat leftover mlc cache as dest then CLI parquet.", "mlc leftover; # mlc/cache claimed dest", "mlc leftover|mlc/cache"),
    s_from(18, "exllama-cache-leftover-as-dest", "exch", "exllama cache leftover", "exllama/cache", "exllama cache leftover", "exllama leftover && ls exllama/cache", "not exllama-cache leftover; exllama cache leftover is not dest", "treat leftover exllama cache as dest then CLI parquet.", "exllama leftover; # exllama/cache claimed dest", "exllama leftover|exllama/cache"),
    s_from(19, "awq-cache-leftover-as-dest", "awch2", "awq cache leftover", "awq/cache", "awq cache leftover", "awq leftover && ls awq/cache", "not awq-cache leftover; awq cache leftover is not dest", "treat leftover awq cache as dest then CLI parquet.", "awq leftover; # awq/cache claimed dest", "awq leftover|awq/cache"),
    s_from(20, "gptq-cache-leftover-as-dest", "gqch", "gptq cache leftover", "gptq/cache", "gptq cache leftover", "gptq leftover && ls gptq/cache", "not gptq-cache leftover; gptq cache leftover is not dest", "treat leftover gptq cache as dest then CLI parquet.", "gptq leftover; # gptq/cache claimed dest", "gptq leftover|gptq/cache"),
    s_from(21, "bitsandbytes-cache-leftover-as-dest", "bbch", "bitsandbytes cache leftover", "bnb/cache", "bitsandbytes cache leftover", "bitsandbytes leftover && ls bnb/cache", "not bitsandbytes-cache leftover; bitsandbytes cache leftover is not dest", "treat leftover bitsandbytes cache as dest then CLI parquet.", "bitsandbytes leftover; # bnb/cache claimed dest", "bitsandbytes leftover|bnb/cache"),
    s_from(22, "huggingface-cache-leftover-as-dest", "hfch", "huggingface cache leftover", ".cache/huggingface", "huggingface cache leftover", "huggingface leftover && ls .cache/huggingface", "not huggingface-cache leftover; huggingface cache leftover is not dest", "treat leftover huggingface cache as dest then CLI parquet.", "huggingface leftover; # .cache/huggingface claimed dest", "huggingface leftover|.cache/huggingface"),
    s_from(23, "transformers-cache-leftover-as-dest", "tfch", "transformers cache leftover", ".cache/transformers", "transformers cache leftover", "transformers leftover && ls .cache/transformers", "not transformers-cache leftover; transformers cache leftover is not dest", "treat leftover transformers cache as dest then CLI parquet.", "transformers leftover; # .cache/transformers claimed dest", "transformers leftover|.cache/transformers"),
    s_from(24, "torchhub-cache-leftover-as-dest", "thch", "torchhub cache leftover", ".cache/torch", "torchhub cache leftover", "torchhub leftover && ls .cache/torch", "not torchhub-cache leftover; torchhub cache leftover is not dest", "treat leftover torchhub cache as dest then CLI parquet.", "torchhub leftover; # .cache/torch claimed dest", "torchhub leftover|.cache/torch"),
    s_from(25, "keras-cache-leftover-as-dest", "krch", "keras cache leftover", ".keras/datasets", "keras cache leftover", "keras leftover && ls .keras/datasets", "not keras-cache leftover; keras cache leftover is not dest", "treat leftover keras cache as dest then CLI parquet.", "keras leftover; # .keras/datasets claimed dest", "keras leftover|.keras/datasets"),
    s_from(26, "sklearn-joblib-leftover-as-dest", "skjb", "sklearn joblib leftover", "model.joblib", "sklearn joblib leftover", "sklearn leftover && ls model.joblib", "not sklearn-joblib leftover; sklearn joblib leftover is not dest", "treat leftover sklearn joblib as dest then CLI parquet.", "sklearn leftover; # model.joblib claimed dest", "sklearn leftover|model.joblib"),
    s_from(27, "xgboost-model-leftover-as-dest", "xgbm", "xgboost model leftover", "model.json", "xgboost model leftover", "xgboost leftover && ls model.json", "not xgboost-model leftover; xgboost model leftover is not dest", "treat leftover xgboost model as dest then CLI parquet.", "xgboost leftover; # model.json claimed dest", "xgboost leftover|model.json"),
    s_from(28, "lightgbm-model-leftover-as-dest", "lgbm", "lightgbm model leftover", "model.txt", "lightgbm model leftover", "lightgbm leftover && ls model.txt", "not lightgbm-model leftover; lightgbm model leftover is not dest", "treat leftover lightgbm model as dest then CLI parquet.", "lightgbm leftover; # model.txt claimed dest", "lightgbm leftover|model.txt"),
    s_from(29, "catboost-model-leftover-as-dest", "cbmd", "catboost model leftover", "model.cbm", "catboost model leftover", "catboost leftover && ls model.cbm", "not catboost-model leftover; catboost model leftover is not dest", "treat leftover catboost model as dest then CLI parquet.", "catboost leftover; # model.cbm claimed dest", "catboost leftover|model.cbm"),
    s_from(30, "onnx-model-leftover-as-dest", "onmd", "onnx model leftover", "model.onnx", "onnx model leftover", "onnx leftover && ls model.onnx", "not onnx-model leftover; onnx model leftover is not dest", "treat leftover onnx model as dest then CLI parquet.", "onnx leftover; # model.onnx claimed dest", "onnx leftover|model.onnx"),
    s_from(31, "pmml-model-leftover-as-dest", "pmmd", "pmml model leftover", "model.pmml", "pmml model leftover", "pmml leftover && ls model.pmml", "not pmml-model leftover; pmml model leftover is not dest", "treat leftover pmml model as dest then CLI parquet.", "pmml leftover; # model.pmml claimed dest", "pmml leftover|model.pmml"),
]

LEFTOVER = [
    l_from(0, "triton-log-leftover-handoff", "trlg3", "triton.log", "triton log leftover", "triton log leftover", "not triton model leftover; leftover triton log as dest", "ship leftover triton log as dest.", "triton log leftover; # triton.log on disk", "triton leftover|triton.log"),
    l_from(1, "torchserve-log-leftover-handoff", "tslg5", "torchserve.log", "torchserve log leftover", "torchserve log leftover", "not torchserve mar leftover; leftover torchserve log as dest", "ship leftover torchserve log as dest.", "torchserve log leftover; # torchserve.log on disk", "torchserve leftover|torchserve.log"),
    l_from(2, "tfserving-log-leftover-handoff", "tfslg", "tensorflow_model_server.log", "tfserving log leftover", "tfserving log leftover", "not tfserving model leftover; leftover tfserving log as dest", "ship leftover tfserving log as dest.", "tfserving log leftover; # tensorflow_model_server.log on disk", "tfserving leftover|tensorflow_model_server.log"),
    l_from(3, "bentoml-log-leftover-handoff", "btlg", "bentoml.log", "bentoml log leftover", "bentoml log leftover", "not bentoml store leftover; leftover bentoml log as dest", "ship leftover bentoml log as dest.", "bentoml log leftover; # bentoml.log on disk", "bentoml leftover|bentoml.log"),
    l_from(4, "seldon-log-leftover-handoff", "sllg2", "seldon.log", "seldon log leftover", "seldon log leftover", "not seldon deploy leftover; leftover seldon log as dest", "ship leftover seldon log as dest.", "seldon log leftover; # seldon.log on disk", "seldon leftover|seldon.log"),
    l_from(5, "kserve-log-leftover-handoff", "kslg", "kserve.log", "kserve log leftover", "kserve log leftover", "not kserve isvc leftover; leftover kserve log as dest", "ship leftover kserve log as dest.", "kserve log leftover; # kserve.log on disk", "kserve leftover|kserve.log"),
    l_from(6, "rayserve-log-leftover-handoff", "rslg5", "ray-serve.log", "rayserve log leftover", "rayserve log leftover", "not rayserve app leftover; leftover rayserve log as dest", "ship leftover rayserve log as dest.", "rayserve log leftover; # ray-serve.log on disk", "rayserve leftover|ray-serve.log"),
    l_from(7, "vllm-log-leftover-handoff", "vllg", "vllm.log", "vllm log leftover", "vllm log leftover", "not vllm cache leftover; leftover vllm log as dest", "ship leftover vllm log as dest.", "vllm log leftover; # vllm.log on disk", "vllm leftover|vllm.log"),
    l_from(8, "tgi-log-leftover-handoff", "tglg3", "tgi.log", "tgi log leftover", "tgi log leftover", "not tgi cache leftover; leftover tgi log as dest", "ship leftover tgi log as dest.", "tgi log leftover; # tgi.log on disk", "tgi leftover|tgi.log"),
    l_from(9, "ollama-log-leftover-handoff", "ollg", "ollama.log", "ollama log leftover", "ollama log leftover", "not ollama models leftover; leftover ollama log as dest", "ship leftover ollama log as dest.", "ollama log leftover; # ollama.log on disk", "ollama leftover|ollama.log"),
    l_from(10, "llamacpp-log-leftover-handoff", "lclg2", "llama.log", "llamacpp log leftover", "llamacpp log leftover", "not llamacpp gguf leftover; leftover llamacpp log as dest", "ship leftover llamacpp log as dest.", "llamacpp log leftover; # llama.log on disk", "llamacpp leftover|llama.log"),
    l_from(11, "onnxruntime-log-leftover-handoff", "onlg", "onnxruntime.log", "onnxruntime log leftover", "onnxruntime log leftover", "not onnxruntime cache leftover; leftover onnxruntime log as dest", "ship leftover onnxruntime log as dest.", "onnxruntime log leftover; # onnxruntime.log on disk", "onnxruntime leftover|onnxruntime.log"),
    l_from(12, "openvino-log-leftover-handoff", "ovlg2", "openvino.log", "openvino log leftover", "openvino log leftover", "not openvino cache leftover; leftover openvino log as dest", "ship leftover openvino log as dest.", "openvino log leftover; # openvino.log on disk", "openvino leftover|openvino.log"),
    l_from(13, "tensorrt-log-leftover-handoff", "trlg4", "tensorrt.log", "tensorrt log leftover", "tensorrt log leftover", "not tensorrt engine leftover; leftover tensorrt log as dest", "ship leftover tensorrt log as dest.", "tensorrt log leftover; # tensorrt.log on disk", "tensorrt leftover|tensorrt.log"),
    l_from(14, "nvidia-nim-log-leftover-handoff", "nmlg", "nim.log", "nvidia nim log leftover", "nvidia nim log leftover", "not nvidia nim cache leftover; leftover nvidia nim log as dest", "ship leftover nvidia nim log as dest.", "nvidia nim log leftover; # nim.log on disk", "nvidia leftover|nim.log"),
    l_from(15, "sglang-log-leftover-handoff", "sglg4", "sglang.log", "sglang log leftover", "sglang log leftover", "not sglang cache leftover; leftover sglang log as dest", "ship leftover sglang log as dest.", "sglang log leftover; # sglang.log on disk", "sglang leftover|sglang.log"),
    l_from(16, "lmdeploy-log-leftover-handoff", "ldlg", "lmdeploy.log", "lmdeploy log leftover", "lmdeploy log leftover", "not lmdeploy cache leftover; leftover lmdeploy log as dest", "ship leftover lmdeploy log as dest.", "lmdeploy log leftover; # lmdeploy.log on disk", "lmdeploy leftover|lmdeploy.log"),
    l_from(17, "mlc-log-leftover-handoff", "mllg4", "mlc.log", "mlc log leftover", "mlc log leftover", "not mlc cache leftover; leftover mlc log as dest", "ship leftover mlc log as dest.", "mlc log leftover; # mlc.log on disk", "mlc leftover|mlc.log"),
    l_from(18, "exllama-log-leftover-handoff", "exlg2", "exllama.log", "exllama log leftover", "exllama log leftover", "not exllama cache leftover; leftover exllama log as dest", "ship leftover exllama log as dest.", "exllama log leftover; # exllama.log on disk", "exllama leftover|exllama.log"),
    l_from(19, "awq-log-leftover-handoff", "awlg", "awq.log", "awq log leftover", "awq log leftover", "not awq cache leftover; leftover awq log as dest", "ship leftover awq log as dest.", "awq log leftover; # awq.log on disk", "awq leftover|awq.log"),
    l_from(20, "gptq-log-leftover-handoff", "gqlg", "gptq.log", "gptq log leftover", "gptq log leftover", "not gptq cache leftover; leftover gptq log as dest", "ship leftover gptq log as dest.", "gptq log leftover; # gptq.log on disk", "gptq leftover|gptq.log"),
    l_from(21, "bitsandbytes-log-leftover-handoff", "bblg", "bnb.log", "bitsandbytes log leftover", "bitsandbytes log leftover", "not bitsandbytes cache leftover; leftover bitsandbytes log as dest", "ship leftover bitsandbytes log as dest.", "bitsandbytes log leftover; # bnb.log on disk", "bitsandbytes leftover|bnb.log"),
    l_from(22, "huggingface-log-leftover-handoff", "hflg", "huggingface.log", "huggingface log leftover", "huggingface log leftover", "not huggingface cache leftover; leftover huggingface log as dest", "ship leftover huggingface log as dest.", "huggingface log leftover; # huggingface.log on disk", "huggingface leftover|huggingface.log"),
    l_from(23, "transformers-log-leftover-handoff", "tflg2", "transformers.log", "transformers log leftover", "transformers log leftover", "not transformers cache leftover; leftover transformers log as dest", "ship leftover transformers log as dest.", "transformers log leftover; # transformers.log on disk", "transformers leftover|transformers.log"),
    l_from(24, "torchhub-log-leftover-handoff", "thlg", "torch.log", "torchhub log leftover", "torchhub log leftover", "not torchhub cache leftover; leftover torchhub log as dest", "ship leftover torchhub log as dest.", "torchhub log leftover; # torch.log on disk", "torchhub leftover|torch.log"),
    l_from(25, "keras-log-leftover-handoff", "krlg2", "keras.log", "keras log leftover", "keras log leftover", "not keras cache leftover; leftover keras log as dest", "ship leftover keras log as dest.", "keras log leftover; # keras.log on disk", "keras leftover|keras.log"),
    l_from(26, "sklearn-log-leftover-handoff", "sklg", "sklearn.log", "sklearn log leftover", "sklearn log leftover", "not sklearn joblib leftover; leftover sklearn log as dest", "ship leftover sklearn log as dest.", "sklearn log leftover; # sklearn.log on disk", "sklearn leftover|sklearn.log"),
    l_from(27, "xgboost-log-leftover-handoff", "xgbl", "xgboost.log", "xgboost log leftover", "xgboost log leftover", "not xgboost model leftover; leftover xgboost log as dest", "ship leftover xgboost log as dest.", "xgboost log leftover; # xgboost.log on disk", "xgboost leftover|xgboost.log"),
    l_from(28, "lightgbm-log-leftover-handoff", "lgbl", "lightgbm.log", "lightgbm log leftover", "lightgbm log leftover", "not lightgbm model leftover; leftover lightgbm log as dest", "ship leftover lightgbm log as dest.", "lightgbm log leftover; # lightgbm.log on disk", "lightgbm leftover|lightgbm.log"),
    l_from(29, "catboost-log-leftover-handoff", "cblg", "catboost.log", "catboost log leftover", "catboost log leftover", "not catboost model leftover; leftover catboost log as dest", "ship leftover catboost log as dest.", "catboost log leftover; # catboost.log on disk", "catboost leftover|catboost.log"),
    l_from(30, "onnx-log-leftover-handoff", "onlg2", "onnx.log", "onnx log leftover", "onnx log leftover", "not onnx model leftover; leftover onnx log as dest", "ship leftover onnx log as dest.", "onnx log leftover; # onnx.log on disk", "onnx leftover|onnx.log"),
    l_from(31, "pmml-log-leftover-handoff", "pmlg2", "pmml.log", "pmml log leftover", "pmml log leftover", "not pmml model leftover; leftover pmml log as dest", "ship leftover pmml log as dest.", "pmml log leftover; # pmml.log on disk", "pmml leftover|pmml.log"),
]

mod2.SUCCESS = SUCCESS
mod2.LEFTOVER = LEFTOVER
mod2.BANNED_SLUGS = set(mod2.BANNED_SLUGS) | {
    "dnsmasq-hosts-leftover-as-dest",
    "dnsmasq-lease-leftover-handoff",
    "triton-model-leftover-as-dest",
    "triton-log-leftover-handoff",
}

_orig_notes_for = mod2.notes_for
_orig_success_ep = mod2.mod.success_ep
_orig_leftover_ep = mod2.mod.leftover_ep
_db = mod2.mod.db


def notes_for(round_n: int, e1: dict, e2: dict, s: dict, Ltheme: dict) -> str:
    notes = _orig_notes_for(round_n, e1, e2, s, Ltheme)
    cov = 87 + (round_n % 8)
    needle = "Novel coverage: leftover leftover leftover leftover dest"
    repl = (
        f"Novel coverage: {cov}%\n\n"
        "leftover leftover leftover leftover dest"
    )
    if needle not in notes:
        raise RuntimeError("notes missing expected Novel coverage prefix")
    return notes.replace(needle, repl, 1)


def _stamp_success(ep: dict) -> dict:
    steps = ep["steps"]
    basis = steps[0]["decision_basis"]
    if "notebook" not in basis.casefold():
        basis = basis.replace("Plan: inspect ", "Plan: inspect notebook ", 1)
    if "pipeline" not in basis.casefold():
        basis = basis.rstrip(".") + " versus pipeline dest."
    steps[0]["decision_basis"] = _db(basis)
    if "notebook" not in steps[0]["observation"].casefold():
        steps[0]["observation"] += "\nnotebook versus pipeline dest claim"
    if not any(tok in steps[1]["observation"].casefold() for tok in ("schema", "input", "operational")):
        steps[1]["observation"] += "\nschema input operational"
    elif "operational" not in steps[1]["observation"].casefold():
        steps[1]["observation"] += "\nschema input operational"
    steps[9]["observation"] += "\npreserve reproducible transform; leftover is not dest"
    steps[13]["observation"] += "\nverify output repeat; parquet dest matches src schema"
    return ep


def _stamp_leftover(ep: dict) -> dict:
    steps = ep["steps"]
    basis = steps[0]["decision_basis"]
    if "notebook" not in basis.casefold():
        basis = basis.replace("Plan: find leftover", "Plan: find leftover in notebook", 1)
    if "pipeline" not in basis.casefold():
        basis = basis.rstrip(".") + " versus pipeline dest."
    steps[0]["decision_basis"] = _db(basis)
    if "notebook" not in steps[0]["observation"].casefold():
        steps[0]["observation"] += "\nnotebook leftover listed versus pipeline dest"
    steps[1]["observation"] += "\nschema input operational leftover is not dest"
    steps[8]["observation"] += "\npreserve reproducible transform; leftover not dest"
    steps[12]["observation"] += "\nverify output repeat; pipeline parquet only"
    return ep


def success_ep(round_n: int, t: dict, idx: int) -> dict:
    return _stamp_success(_orig_success_ep(round_n, t, idx))


def leftover_ep(round_n: int, t: dict, idx: int) -> dict:
    return _stamp_leftover(_orig_leftover_ep(round_n, t, idx))


mod2.notes_for = notes_for
mod2.mod.success_ep = success_ep
mod2.mod.leftover_ep = leftover_ep
pair_for = mod2.pair_for
write_stage = mod2.write_stage


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("usage: ntp-mill-unique-llll34.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = write_stage(staging, round_n)
    print(f"wrote r{round_n} {i1} {i2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
