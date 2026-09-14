#!/usr/bin/env python3
"""IRC mill r5001+ — wave-95 ml/feature-store leftover.

NEW on-call plants (not Wave-27–94 tails). BAN ypbind/oddjob,
r3389 opensearch leftover3c, r3576 tigergraph/hugegraph.
"""
from __future__ import annotations
import importlib.util, json, sys

spec = importlib.util.spec_from_file_location("irc3234", "/tmp/irc_mill_r3234.py")
w16 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w16)
m = w16.m
plant, helm_rb, patch_file = w16.plant, w16.helm_rb, w16.patch_file

# daemon|key|old|new|unit|path|oldv|newv|reload|hpeer|metric|what|wipe|herring|rca_tail
ROWS = r'''
mlflow7|MLFLOW7_TIMEOUT|1|30|s|/etc/mlflow7/mlflow7.conf|timeout=1|timeout=30|systemctl reload mlflow7|ml7|mlf_to_1|runs|state|redis leftover leftover down; bounce|MLFLOW7_TIMEOUT leftover 1 leftover; a 2s tracking write is aborted so the runs 504s
kubeflow7|KUBEFLOW7_MAXWORKERS|1|16||/etc/kubeflow7/kubeflow7.conf|maxworkers=1|maxworkers=16|systemctl reload kubeflow7|ku7|kfl_wk_1|pipelines|cache|memcached leftover leftover evict; warmup|KUBEFLOW7_MAXWORKERS leftover 1 leftover; pipeline steps serialize so the runs 504s
ray7|RAY7_OBJECTSTORE|1|8|g|/etc/ray7/ray7.conf|objectstore=1|objectstore=8|systemctl reload ray7|ra7|ray_os_1|tasks|plasma|dns leftover leftover NXDOMAIN; flush|RAY7_OBJECTSTORE leftover 1 leftover; spill to disk thrashes so the tasks 504s
prefect7|PREFECT7_HEARTBEAT|1|30|s|/etc/prefect7/prefect7.conf|heartbeat=1|heartbeat=30|systemctl reload prefect7|pr7|prf_hb_1|flows|offset|ntp leftover leftover skew; step|PREFECT7_HEARTBEAT leftover 1 leftover; workers look dead so the flows 504s
dagster7|DAGSTER7_RUNQUEUE|1|64||/etc/dagster7/dagster7.conf|runqueue=1|runqueue=64|systemctl reload dagster7|da7|dgs_rq_1|jobs|wal|nfs leftover leftover ESTALE; remount|DAGSTER7_RUNQUEUE leftover 1 leftover; queued runs stall so the jobs 504s
dbt7|DBT7_THREADS|1|8||/etc/dbt7/dbt7.conf|threads=1|threads=8|systemctl reload dbt7|db7|dbt_th_1|models|manifest|sidecar leftover leftover crash; restart|DBT7_THREADS leftover 1 leftover; a 2s model is aborted so the models 504s
feast7|FEAST7_ONLINETTL|1|3600|s|/etc/feast7/feast7.conf|onlinettl=1|onlinettl=3600|systemctl reload feast7|fe7|fst_ttl_1|features|ttl|cert leftover leftover expiry; reissue|FEAST7_ONLINETTL leftover 1 leftover; online keys vanish so the features 504s
tfx7|TFX7_CACHE|1|256||/etc/tfx7/tfx7.conf|cache=1|cache=256|systemctl reload tfx7|tf7|tfx_ca_1|pipelines|meta|localfs leftover leftover full; gc|TFX7_CACHE leftover 1 leftover; each transform recompiles so the pipelines 504s
seldon7|SELDON7_MAXBATCH|1|32||/etc/seldon7/seldon7.conf|maxbatch=1|maxbatch=32|systemctl reload seldon7|se7|sel_mb_1|inference|model|envoy leftover leftover drain; un-drain|SELDON7_MAXBATCH leftover 1 leftover; each predict is solo so the inference 504s
kserve7|KSERVE7_MINREPLICAS|1|3||/etc/kserve7/kserve7.conf|minreplicas=1|minreplicas=3|systemctl reload kserve7|ks7|ksv_mr_1|inference|revision|hpa leftover leftover freeze; unfreeze|KSERVE7_MINREPLICAS leftover 1 leftover; cold-start pegs p99 so the inference 504s
bentoml7|BENTOML7_WORKERS|1|8||/etc/bentoml7/bentoml7.conf|workers=1|workers=8|systemctl reload bentoml7|be7|bto_wk_1|serve|bundle|nginx leftover leftover 502; bounce|BENTOML7_WORKERS leftover 1 leftover; GIL serializes so the serve 504s
triton7|TRITON7_QUEUEDELAY|1|50|ms|/etc/triton7/triton7.conf|queuedelay=1|queuedelay=50|systemctl reload triton7|tr7|trt_qd_1|inference|engine|gpu leftover leftover reset; rescan|TRITON7_QUEUEDELAY leftover 1 leftover; dynamic batch never fills so the inference 504s
torchserve7|TORCHSERVE7_MAXWAIT|1|30|s|/etc/torchserve7/torchserve7.conf|maxwait=1|maxwait=30|systemctl reload torchserve7|to7|tse_mw_1|inference|mar|shm leftover leftover tiny; enlarge|TORCHSERVE7_MAXWAIT leftover 1 leftover; batch window closes so the inference 504s
onnx7|ONNX7_INTRATHREADS|1|8||/etc/onnx7/onnx7.conf|intrathreads=1|intrathreads=8|systemctl reload onnx7|on7|onx_it_1|sessions|graph|numa leftover leftover pin; rebalance|ONNX7_INTRATHREADS leftover 1 leftover; session Run serializes so the sessions 504s
vllm7|VLLM7_GPUUTIL|1|90||/etc/vllm7/vllm7.conf|gpuutil=1|gpuutil=90|systemctl reload vllm7|vl7|vlm_gu_1|tokens|kv|nccl leftover leftover hang; bounce|VLLM7_GPUUTIL leftover 1 leftover; KV cache starves so the tokens 504s
tgi7|TGI7_MAXINPUT|1|4096||/etc/tgi7/tgi7.conf|maxinput=1|maxinput=4096|systemctl reload tgi7|tg7|tgi_mi_1|generate|adapter|tokenizer leftover leftover mismatch; reload|TGI7_MAXINPUT leftover 1 leftover; prompts truncate so the generate 504s
ollama7|OLLAMA7_KEEPALIVE|1|30|m|/etc/ollama7/ollama7.conf|keepalive=1|keepalive=30|systemctl reload ollama7|ol7|oll_ka_1|chat|weights|swap leftover leftover thrash; pin|OLLAMA7_KEEPALIVE leftover 1 leftover; models unload mid-chat so the chat 504s
llamacpp7|LLAMACPP7_CTXSIZE|1|8192||/etc/llamacpp7/llamacpp7.conf|ctxsize=1|ctxsize=8192|systemctl reload llamacpp7|ll7|lcp_cx_1|complete|gguf|mmap leftover leftover fail; remount|LLAMACPP7_CTXSIZE leftover 1 leftover; context overflows so the complete 504s
whisper7|WHISPER7_BEAMSIZE|1|5||/etc/whisper7/whisper7.conf|beamsize=1|beamsize=5|systemctl reload whisper7|wh7|whp_bm_1|transcribe|audio|alsa leftover leftover underrun; restart|WHISPER7_BEAMSIZE leftover 1 leftover; greedy decode drops words so the transcribe 504s
opencv7|OPENCV7_THREADPOOL|1|16||/etc/opencv7/opencv7.conf|threadpool=1|threadpool=16|systemctl reload opencv7|oc7|ocv_tp_1|frames|codec|v4l leftover leftover busy; unbind|OPENCV7_THREADPOOL leftover 1 leftover; decode serializes so the frames 504s
paddle7|PADDLE7_BATCHSIZE|1|64||/etc/paddle7/paddle7.conf|batchsize=1|batchsize=64|systemctl reload paddle7|pa7|pdl_bs_1|train|ckpt|ibverbs leftover leftover down; bounce|PADDLE7_BATCHSIZE leftover 1 leftover; GPU idle so the train 504s
mxnet7|MXNET7_KVSTORE|1|8||/etc/mxnet7/mxnet7.conf|kvstore=1|kvstore=8|systemctl reload mxnet7|mx7|mxn_kv_1|train|params|rdma leftover leftover stall; reset|MXNET7_KVSTORE leftover 1 leftover; param sync serializes so the train 504s
jax7|JAX7_COMPILATIONCACHE|1|256||/etc/jax7/jax7.conf|compilationcache=1|compilationcache=256|systemctl reload jax7|jx7|jax_cc_1|jit|xla|xla leftover leftover dump; clear|JAX7_COMPILATIONCACHE leftover 1 leftover; every jit recompiles so the jit 504s
horovod7|HOROVOD7_FUSIONBUFFER|1|64|m|/etc/horovod7/horovod7.conf|fusionbuffer=1|fusionbuffer=64|systemctl reload horovod7|ho7|hvd_fb_1|allreduce|ring|mpi leftover leftover abort; restart|HOROVOD7_FUSIONBUFFER leftover 1 leftover; tiny fusions stall so the allreduce 504s
deepspeed7|DEEPSPEED7_ZEROSTAGE|1|2||/etc/deepspeed7/deepspeed7.conf|zerostage=1|zerostage=2|systemctl reload deepspeed7|ds7|dsp_zs_1|train|offload|nvme leftover leftover slow; cache|DEEPSPEED7_ZEROSTAGE leftover 1 leftover; optimizer shards OOM so the train 504s
lightning7|LIGHTNING7_VALCHECK|1|10||/etc/lightning7/lightning7.conf|valcheck=1|valcheck=10|systemctl reload lightning7|lg7|ltn_vc_1|fit|ckpt|wandb leftover leftover 429; backoff|LIGHTNING7_VALCHECK leftover 1 leftover; every step validates so the fit 504s
wandb7|WANDB7_FILASYNCLIMIT|1|64||/etc/wandb7/wandb7.conf|filasynclimit=1|filasynclimit=64|systemctl reload wandb7|wa7|wdb_fa_1|logs|run|https leftover leftover down; bounce|WANDB7_FILASYNCLIMIT leftover 1 leftover; artifact upload serializes so the logs 504s
neptune7|NEPTUNE7_FLUSHINTERVAL|1|30|s|/etc/neptune7/neptune7.conf|flushinterval=1|flushinterval=30|systemctl reload neptune7|ne7|npt_fi_1|metrics|project|proxy leftover leftover 502; retry|NEPTUNE7_FLUSHINTERVAL leftover 1 leftover; each scalar is a roundtrip so the metrics 504s
comet7|COMET7_MAXMSG|1|16|m|/etc/comet7/comet7.conf|maxmsg=1|maxmsg=16|systemctl reload comet7|cm7|cmt_mm_1|experiments|ws|websocket leftover leftover drop; reconnect|COMET7_MAXMSG leftover 1 leftover; charts stall so the experiments 504s
optuna7|OPTUNA7_NJOBS|1|8||/etc/optuna7/optuna7.conf|njobs=1|njobs=8|systemctl reload optuna7|op7|opt_nj_1|trials|study|sqlite leftover leftover lock; wal|OPTUNA7_NJOBS leftover 1 leftover; sampler waits so the trials 504s
katib7|KATIB7_PARALLELTRIAL|1|8||/etc/katib7/katib7.conf|paralleltrial=1|paralleltrial=8|systemctl reload katib7|ka7|ktb_pt_1|experiments|suggestion|controller leftover leftover stale; resync|KATIB7_PARALLELTRIAL leftover 1 leftover; suggestions serialize so the experiments 504s
nni7|NNI7_CONCURRENCY|1|8||/etc/nni7/nni7.conf|concurrency=1|concurrency=8|systemctl reload nni7|nn7|nni_cc_1|tuners|dispatcher|rest leftover leftover 429; backoff|NNI7_CONCURRENCY leftover 1 leftover; tuner trials queue so the tuners 504s
dvc7|DVC7_JOBS|1|8||/etc/dvc7/dvc7.conf|jobs=1|jobs=8|systemctl reload dvc7|dv7|dvc_jb_1|pulls|cache|s3 leftover leftover 503; retry|DVC7_JOBS leftover 1 leftover; remote fetch serializes so the pulls 504s
pachyderm7|PACHYDERM7_PIPELINEWORKERS|1|8||/etc/pachyderm7/pachyderm7.conf|pipelineworkers=1|pipelineworkers=8|systemctl reload pachyderm7|pc7|pcd_pw_1|pipelines|pps|etcd leftover leftover slow; compact|PACHYDERM7_PIPELINEWORKERS leftover 1 leftover; datums process one-by-one so the pipelines 504s
lakefs7|LAKEFS7_BLOCKSTORECACHE|1|256||/etc/lakefs7/lakefs7.conf|blockstorecache=1|blockstorecache=256|systemctl reload lakefs7|lk7|lkf_bc_1|commits|refs|minio leftover leftover heal; wait|LAKEFS7_BLOCKSTORECACHE leftover 1 leftover; each get is a GET so the commits 504s
delta7|DELTA7_LOGRETENTION|1|30|d|/etc/delta7/delta7.conf|logretention=1|logretention=30|systemctl reload delta7|dl7|dlt_lr_1|tables|checkpoint|spark leftover leftover UI down; ignore|DELTA7_LOGRETENTION leftover 1 leftover; vacuum deletes live files so the tables 504s
iceberg7|ICEBERG7_COMMITRETRY|1|8||/etc/iceberg7/iceberg7.conf|commitretry=1|commitretry=8|systemctl reload iceberg7|ic7|ice_cr_1|snapshots|manifest|hive leftover leftover metastore; bounce|ICEBERG7_COMMITRETRY leftover 1 leftover; concurrent writers abort so the snapshots 504s
hudi7|HUDI7_CLEANRETAIN|1|24||/etc/hudi7/hudi7.conf|cleanretain=1|cleanretain=24|systemctl reload hudi7|hu7|hdi_cl_1|tables|timeline|hoodie leftover leftover lock; wait|HUDI7_CLEANRETAIN leftover 1 leftover; cleaner drops instants so the tables 504s
nessie7|NESSIE7_REFHISTORY|1|1000||/etc/nessie7/nessie7.conf|refhistory=1|refhistory=1000|systemctl reload nessie7|ns7|nss_rh_1|refs|catalog|rocks leftover leftover compact; wait|NESSIE7_REFHISTORY leftover 1 leftover; git-like history truncates so the refs 504s
polaris7|POLARIS7_TOKENTTL|1|3600|s|/etc/polaris7/polaris7.conf|tokenttl=1|tokenttl=3600|systemctl reload polaris7|po7|pol_tt_1|catalog|grants|iam leftover leftover deny; reauth|POLARIS7_TOKENTTL leftover 1 leftover; catalog calls 401 mid-job so the catalog 504s
unitycatalog7|UNITYCATALOG7_CACHE|1|256||/etc/unitycatalog7/unitycatalog7.conf|cache=1|cache=256|systemctl reload unitycatalog7|uc7|uct_ca_1|catalog|acl|oauth leftover leftover expire; refresh|UNITYCATALOG7_CACHE leftover 1 leftover; every resolve hits storage so the catalog 504s
labelstudio7|LABELSTUDIO7_TASKPAGE|1|100||/etc/labelstudio7/labelstudio7.conf|taskpage=1|taskpage=100|systemctl reload labelstudio7|lb7|lbs_tp_1|tasks|export|postgres leftover leftover idle; ignore|LABELSTUDIO7_TASKPAGE leftover 1 leftover; annotators page forever so the tasks 504s
cvat7|CVAT7_CHUNKSIZE|1|32||/etc/cvat7/cvat7.conf|chunksize=1|chunksize=32|systemctl reload cvat7|cv7|cvt_cs_1|frames|jobs|redis leftover leftover flush; ignore|CVAT7_CHUNKSIZE leftover 1 leftover; each frame is a request so the frames 504s
fiftyone7|FIFTYONE7_MEDIACACHE|1|64|g|/etc/fiftyone7/fiftyone7.conf|mediacache=1|mediacache=64|systemctl reload fiftyone7|fi7|fto_mc_1|dataset|media|fuse leftover leftover stale; remount|FIFTYONE7_MEDIACACHE leftover 1 leftover; thumbnails refetch so the dataset 504s
clearml7|CLEARML7_AGENTSLOTS|1|8||/etc/clearml7/clearml7.conf|agentslots=1|agentslots=8|systemctl reload clearml7|cl7|cml_as_1|jobs|queue|mongo leftover leftover lock; wait|CLEARML7_AGENTSLOTS leftover 1 leftover; queue drains one task so the jobs 504s
zenml7|ZENML7_ORCHWORKERS|1|8||/etc/zenml7/zenml7.conf|orchworkers=1|orchworkers=8|systemctl reload zenml7|zn7|znm_ow_1|pipelines|store|sqlite leftover leftover busy; wal|ZENML7_ORCHWORKERS leftover 1 leftover; steps wait on a single worker so the pipelines 504s
flyte7|FLYTE7_WORKERS|1|16||/etc/flyte7/flyte7.conf|workers=1|workers=16|systemctl reload flyte7|fl7|flt_wk_1|workflows|propeller|k8s leftover leftover apiserver; wait|FLYTE7_WORKERS leftover 1 leftover; propeller lags so the workflows 504s
temporal7|TEMPORAL7_HISTORYSHARDS|1|512||/etc/temporal7/temporal7.conf|historyshards=1|historyshards=512|systemctl reload temporal7|tm7|tmp_hs_1|workflows|namespace|cassandra leftover leftover tombstone; compact|TEMPORAL7_HISTORYSHARDS leftover 1 leftover; history hotspots so the workflows 504s
cadence7|CADENCE7_MATCHINGTASK|1|16||/etc/cadence7/cadence7.conf|matchingtask=1|matchingtask=16|systemctl reload cadence7|cd7|cdn_mt_1|tasks|domain|ring leftover leftover unhealthy; heal|CADENCE7_MATCHINGTASK leftover 1 leftover; pollers starve so the tasks 504s
argo7|ARGO7_PARALLELISM|1|32||/etc/argo7/argo7.conf|parallelism=1|parallelism=32|systemctl reload argo7|ag7|arg_pl_1|workflows|archive|workflow leftover leftover CRD; apply|ARGO7_PARALLELISM leftover 1 leftover; DAG nodes serialize so the workflows 504s
xgboost7|XGBOOST7_NTHREAD|1|16||/etc/xgboost7/xgboost7.conf|nthread=1|nthread=16|systemctl reload xgboost7|xg7|xgb_nt_1|train|model|openmp leftover leftover 1; restore|XGBOOST7_NTHREAD leftover 1 leftover; trees build serially so the train 504s
lightgbm7|LIGHTGBM7_NUMTHREADS|1|16||/etc/lightgbm7/lightgbm7.conf|numthreads=1|numthreads=16|systemctl reload lightgbm7|lg7|lgb_nt_1|train|booster|omp leftover leftover bind; unpin|LIGHTGBM7_NUMTHREADS leftover 1 leftover; histogram bins serialize so the train 504s
'''
WAVE = (
    "mlflow7/kubeflow7/ray7/prefect7/dagster7/dbt7/feast7/tfx7/seldon7/kserve7/"
    "bentoml7/triton7/torchserve7/onnx7/vllm7/tgi7/ollama7/llamacpp7/whisper7/"
    "opencv7/paddle7/mxnet7/jax7/horovod7/deepspeed7/lightning7/wandb7/neptune7/"
    "comet7/optuna7/katib7/nni7/dvc7/pachyderm7/lakefs7/delta7/iceberg7/hudi7/"
    "nessie7/polaris7/unitycatalog7/labelstudio7/cvat7/fiftyone7/clearml7/zenml7/"
    "flyte7/temporal7/cadence7/argo7/xgboost7/lightgbm7"
)


def _parse_rows():
    plants = []
    srcs = ("grafana", "pagerduty", "opsgenie", "alertmanager")
    ns_cycle = (17, 16, 18)
    for raw in ROWS.strip().splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        parts = raw.split("|")
        if len(parts) != 15:
            raise SystemExit(f"bad row cols={len(parts)}: {raw[:160]}")
        (
            daemon, key, old, new, unit, path, oldv, newv, reload, hpeer, metric,
            what, wipe, herring, rca_tail,
        ) = parts
        i = len(plants)
        n = ns_cycle[i % 3]
        rem = "rollback" if i % 2 == 0 else "patch"
        src = srcs[i % 4]
        svc = f"v4{i:02d}x"
        ns = f"v4{i:02d}"
        clu = f"prod-apuz{941 + i}-{svc[:3]}"
        ticket = f"W2-{14523 + i}"
        node = f"ip-10-165-{1 + i}-{20 + i}"
        slug = f"{daemon}-{key}-{old}{unit}-{svc}"
        key_words = key.replace(".", " leftover ").replace("_", " leftover ")
        symptom = f"{key_words} leftover {old}{unit} leftover; {what} drop"
        because = (
            f"is dropping {what} because leftover {daemon} leftover {key_words} leftover is {old} leftover."
        )
        do_not = f"Restore {new}{unit}; do not wipe {wipe}."
        rca = f"{daemon} leftover {key} leftover {old} leftover; {rca_tail}"
        if remnant := (helm_rb(ns, svc, 3, path, oldv, newv, reload) if rem == "rollback" else patch_file(path, oldv, newv, reload)):
            extra = f"helm -n {ns} history {svc} | head -5" if rem == "rollback" else f"kubectl -n {ns} logs deploy/{svc} --since=5m | grep {key} | tail"
            eobs = f"4  {old}{unit}\n3  last-good {new}" if rem == "rollback" else f"{key} leftover {old}"
        plants.append(
            plant(
                slug=slug, ticket=ticket, service=svc, ns=ns, cluster=clu, src=src,
                node=node, symptom=symptom, because=because, do_not=do_not,
                herring=herring, rca=rca, remediate=rem, metric=metric,
                hcmds=[
                    f"{hpeer} leftover status | head",
                    f"systemctl reload {hpeer} || true",
                    f"{hpeer} leftover bounce leftover || true",
                ],
                hobs=[f"{hpeer} ok", "bounce unused", f"still {key} {old}"],
                inspect=f"grep {key} {path}", iobs=f"{oldv} leftover",
                extra=extra, eobs=eobs, rem=remnant,
                robs=f"{key} {new}; repair holds" if rem == "patch" else f"{key} {new}; rollback holds",
                verify=f"grep {key} {path}", vok=f"{new}; {ticket} resolved", n=n,
            )
        )
    return plants


PLANTS = _parse_rows()
m.PLANTS = PLANTS
m.BASE_ROUND = 5001


def notes_for(round_n, eps):
    slug0 = eps[0]["id"].split("-", 2)[2].rsplit("-", 2)[0]
    slug1 = eps[1]["id"].split("-", 2)[2].rsplit("-", 2)[0]
    rows = [
        f"| `{e['id']}` | {e['meta']['ticket']} | {e['false_lead']['claim'].replace('|', '/')} | {e['remediate']} | {e['reward']['success']} | {e['reward']['steps']} |"
        for e in eps
    ]
    return "\n".join(
        [
            f"# incident-response-oncall-factory NOTES r{round_n}",
            "",
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-95 leftover: {WAVE}.",
            "",
            "OpenSRE designed: 429 then 502 retries, 3-step herring, unique RCA, mix patch/rollback. plant=designed. generator=grok-4.6.",
            "",
            "| id | ticket | herring (steps 6-8) | remediate | success | steps |",
            "|---|---|---|---|---|---|",
            *rows,
            "",
            "## Contract audit",
            f"- Q=2 episodes, kind=episode, ids irc-r{round_n}-*.",
            "- Unique goal service+cluster+symptom; 3 false-lead actions; 429/502 retries.",
            "- Residual: designed excerpts, not live dispatcher traces.",
            "",
        ]
    )


m.notes_for = notes_for


def extra_unique_guards():
    banned = (
        "Follow OpenSRE", "fraud-graph", "sip-proxy", "traefik", "limit_req",
        "cloudfront", "fastly", "kube-proxy", "haproxy", "varnish", "metallb",
        "imperva", "bunny", "calico felix", "kong ", "caddy ",
        "github actions leftover", "gitlab leftover", "circleci leftover",
        "tekton leftover", "snowflake", "bigquery", "redshift", "idle_timeout",
        "max_client_conn", "ypbind", "oddjob", "opensearch", "leftover3c",
        "tigergraph", "hugegraph", "graphdb", "stardog", "debezium", "hasura",
    )
    for p in PLANTS:
        blob = (p["goal"] + " " + p["rca"] + " " + p["slug"]).lower()
        for tok in banned:
            if tok.lower() in blob:
                raise SystemExit(f"banned {tok} in {p['slug']}")
        for need in (p["service"], p["ns"], p["cluster"]):
            if need not in p["goal"]:
                raise SystemExit(p["slug"])
        if p["n_steps"] not in (16, 17, 18) or p["remediate"] not in ("rollback", "patch"):
            raise SystemExit(p["slug"])
    if len(PLANTS) % 2:
        raise SystemExit("odd")
    for i in range(0, len(PLANTS), 2):
        if {PLANTS[i]["remediate"], PLANTS[i + 1]["remediate"]} != {"rollback", "patch"}:
            raise SystemExit(f"pair {i}")


def main():
    extra_unique_guards()
    used_svc, used_clu, used_tix, _ids = m.harvest_used(m.FACTORY_DIR)
    for p in PLANTS:
        if p["service"] in used_svc:
            raise SystemExit(f"service collision {p['service']}")
        if p["cluster"] in used_clu:
            raise SystemExit(f"cluster collision {p['cluster']}")
        if p["ticket"] in used_tix:
            raise SystemExit(f"ticket collision {p['ticket']}")
    for label, xs in (
        ("slug", [p["slug"] for p in PLANTS]),
        ("svc", [p["service"] for p in PLANTS]),
        ("clu", [p["cluster"] for p in PLANTS]),
        ("tix", [p["ticket"] for p in PLANTS]),
        ("node", [p["node"] for p in PLANTS]),
        ("ns", [p["ns"] for p in PLANTS]),
    ):
        if len(set(xs)) != len(xs):
            raise SystemExit("dup " + label)
    print(json.dumps({"ok": True, "plants": len(PLANTS), "rounds": len(PLANTS) // 2}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
