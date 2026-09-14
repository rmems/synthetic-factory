#!/usr/bin/env python3
"""Mill docker-build-cache-factory r1173+. MQ/brokers × Ethernet NIC leftovers.

NEW unique-pair catalog after r1125 video/Bluetooth.
BAN prior DBC catalogs, r645 nerdctl, r549 scsh/scsi, GNU Prolog/landlock/
SWI pack/seccomp/AppArmor/GOTOOLCHAIN, harbor-pin, leftover×sysctl.
17+18 steps. meta.generator=grok-4.6.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("dbc_mill_r1125", HERE / "dbc-mill-r1125.py")
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = _m.FACTORY
GEN = _m.GEN
lang = _m.lang
leftover = _m.leftover
success_episode = _m.success_episode
leftover_episode = _m.leftover_episode
notes_for = _m.notes_for
slug_taken = _m.slug_taken
BANNED_NEEDLES = _m.BANNED_NEEDLES + (
    "x264-cli-cache",
    "btusb-leftover",
    "avisynthplus-cache",
    "hci-ath3k-leftover",
)

# slug, env, tool, old, new, artifact, mb
_CRYPTO = [
    ("nats-server-cache", "NATS_HOME", "nats-server", "2.10.18", "2.11.4", "share/nats-server/nats-server.conf", "12MB"),
    ("nats-jetstream-cache", "NATS_JS_HOME", "nats", "0.1.5", "0.2.0", "share/nats/jetstream.md", "4MB"),
    ("pulsar-broker-cache", "PULSAR_HOME", "pulsar", "3.3.1", "4.0.3", "conf/broker.conf", "48MB"),
    ("bookkeeper-cache", "BOOKIE_CONF", "bookkeeper", "4.16.6", "4.17.2", "conf/bk_server.conf", "22MB"),
    ("nsqd-cache", "NSQD_HOME", "nsqd", "1.3.0", "1.3.0-post", "share/nsq/nsqd.cfg", "6MB"),
    ("nsqlookupd-cache", "NSQLOOKUPD_HOME", "nsqlookupd", "1.3.0", "1.3.0-post", "share/nsq/nsqlookupd.cfg", "4MB"),
    ("zeromq-lib-cache", "ZMQ_HOME", "curve_keygen", "4.3.5", "4.3.5-post", "include/zmq.h", "2MB"),
    ("czmq-lib-cache", "CZMQ_HOME", "zmakecert", "4.2.1", "4.2.1-post", "include/czmq.h", "2MB"),
    ("nanomsg-lib-cache", "NANOMSG_HOME", "nanocat", "1.2.1", "1.2.1-post", "include/nanomsg/nn.h", "1MB"),
    ("nng-lib-cache", "NNG_HOME", "nngcat", "1.8.0", "1.10.1", "include/nng/nng.h", "2MB"),
    ("rabbitmq-server-cache", "RABBITMQ_HOME", "rabbitmq-server", "3.13.6", "4.1.1", "etc/rabbitmq/rabbitmq.conf", "28MB"),
    ("rabbitmq-c-cache", "RABBITMQ_C_HOME", "amqp-publish", "0.14.0", "0.15.0", "include/amqp.h", "1MB"),
    ("librdkafka-cache", "LIBRDKAFKA_HOME", "rdkafka_example", "2.5.0", "2.8.0", "include/librdkafka/rdkafka.h", "3MB"),
    ("kcat-cli-cache", "KCAT_HOME", "kcat", "1.7.1", "1.7.1-post", "share/kcat/kcat.1", "1MB"),
    ("redpanda-rpk-cache", "REDPANDA_HOME", "rpk", "24.2.9", "25.1.4", "etc/redpanda/redpanda.yaml", "36MB"),
    ("mosquitto-broker-cache", "MOSQUITTO_HOME", "mosquitto", "2.0.18", "2.0.21", "etc/mosquitto/mosquitto.conf", "3MB"),
    ("emqx-broker-cache", "EMQX_HOME", "emqx", "5.7.2", "5.8.6", "etc/emqx/emqx.conf", "42MB"),
    ("vernemq-broker-cache", "VERNEMQ_HOME", "vmq-admin", "2.0.1", "2.1.1", "etc/vernemq/vernemq.conf", "18MB"),
    ("hivemq-ce-cache", "HIVEMQ_HOME", "run.sh", "2024.3", "2025.2", "conf/config.xml", "32MB"),
    ("nanomq-broker-cache", "NANOMQ_HOME", "nanomq", "0.21.10", "0.23.4", "etc/nanomq.conf", "5MB"),
    ("rumqttd-cache", "RUMQTTD_HOME", "rumqttd", "0.19.0", "0.20.0", "etc/rumqttd.toml", "4MB"),
    ("paho-mqtt-c-cache", "PAHO_MQTT_C_HOME", "paho_c_pub", "1.3.13", "1.3.14", "include/MQTTClient.h", "2MB"),
    ("activemq-classic-cache", "ACTIVEMQ_HOME", "activemq", "6.1.3", "6.1.6", "conf/activemq.xml", "26MB"),
    ("artemis-broker-cache", "ARTEMIS_HOME", "artemis", "2.37.0", "2.40.0", "etc/broker.xml", "24MB"),
    ("qpid-broker-cache", "QPID_HOME", "qpidd", "1.39.0", "1.40.0", "etc/qpid/qpidd.conf", "8MB"),
    ("qpid-proton-cache", "QPID_PROTON_HOME", "qpid-proton", "0.39.0", "0.40.0", "include/proton/message.h", "3MB"),
    ("nats-c-cache", "NATS_C_HOME", "nats-pub", "3.8.2", "3.9.2", "include/nats/nats.h", "2MB"),
    ("liftbridge-cache", "LIFTBRIDGE_HOME", "liftbridge", "1.9.0", "1.9.0-post", "etc/liftbridge.conf", "10MB"),
    ("centrifugo-cache", "CENTRIFUGO_HOME", "centrifugo", "5.4.6", "6.2.2", "etc/centrifugo/config.json", "14MB"),
    ("eventstore-db-cache", "EVENTSTORE_HOME", "eventstored", "24.6.0", "25.0.0", "etc/eventstore/eventstore.conf", "30MB"),
    ("pravega-cache", "PRAVEGA_HOME", "pravega", "0.13.0", "0.13.0-post", "conf/standalone-config.properties", "20MB"),
    ("debezium-connect-cache", "DEBEZIUM_HOME", "connect-standalone.sh", "2.7.1", "3.0.7", "config/connect-standalone.properties", "16MB"),
    ("schema-registry-cache", "SCHEMA_REGISTRY_HOME", "schema-registry-start", "7.7.0", "7.9.0", "etc/schema-registry/schema-registry.properties", "18MB"),
    ("ksqldb-server-cache", "KSQL_HOME", "ksql-server-start", "7.7.0", "7.9.0", "etc/ksqldb/ksql-server.properties", "22MB"),
    ("cruise-control-cache", "CRUISE_CONTROL_HOME", "kafka-cruise-control-start.sh", "2.5.141", "2.5.146", "config/cruisecontrol.properties", "12MB"),
    ("akhq-ui-cache", "AKHQ_HOME", "akhq", "0.25.1", "0.25.1-post", "application.yml", "15MB"),
    ("redpanda-console-cache", "REDPANDA_CONSOLE_CONFIG_FILE", "redpanda-console", "2.7.2", "3.1.1", "etc/redpanda/console.yaml", "18MB"),
    ("gnatsd-legacy-cache", "GNATSD_HOME", "gnatsd", "1.4.1", "1.4.1-post", "share/gnatsd/gnatsd.conf", "5MB"),
    ("nats-surveyor-cache", "NATS_SURVEYOR_HOME", "nats-surveyor", "0.7.0", "0.9.1", "share/nats-surveyor/surveyor.md", "8MB"),
    ("mqttx-cli-cache", "MQTTX_HOME", "mqttx", "1.10.1", "1.12.0", "share/mqttx/mqttx.md", "9MB"),
    ("soketi-cache", "SOKETI_HOME", "soketi", "1.6.1", "1.6.1-post", "etc/soketi/config.json", "7MB"),
    ("vector-sink-cache", "VECTOR_CONFIG", "vector", "0.41.1", "0.46.1", "etc/vector/vector.yaml", "28MB"),
    ("fluent-bit-cache", "FLUENT_BIT_HOME", "fluent-bit", "3.1.7", "4.0.3", "etc/fluent-bit/fluent-bit.conf", "10MB"),
    ("telegraf-mqtt-cache", "TELEGRAF_CONFIG_PATH", "telegraf", "1.31.3", "1.34.3", "etc/telegraf/telegraf.conf", "14MB"),
    ("nsqadmin-cache", "NSQADMIN_HOME", "nsqadmin", "1.3.0", "1.3.0-post", "share/nsq/nsqadmin.cfg", "4MB"),
    ("rabbitmqadmin-cache", "RABBITMQADMIN_HOME", "rabbitmqadmin", "3.13.6", "4.1.1", "share/rabbitmqadmin/rabbitmqadmin", "1MB"),
    ("emqx-ctl-cache", "EMQX_CTL_HOME", "emqx", "5.7.2", "5.8.6", "bin/emqx_ctl", "2MB"),
    ("kafka-rest-cache", "KAFKA_REST_HOME", "kafka-rest-start", "7.7.0", "7.9.0", "etc/kafka-rest/kafka-rest.properties", "16MB"),
]

_GPIO = [
    ("igb-leftover", "IGB_CLEAR", "igb max_vfs=cache", "igb", "ls /sys/module/igb"),
    ("ixgbe-leftover", "IXGBE_CLEAR", "ixgbe allow_unsupported_sfp=1", "ixgbe", "ls /sys/module/ixgbe"),
    ("i40e-leftover", "I40E_CLEAR", "i40e debug=cache", "i40e", "ls /sys/module/i40e"),
    ("ice-nios-leftover", "ICE_NIOS_CLEAR", "ice debug=cache", "ice", "ls /sys/module/ice"),
    ("bnxt-en-leftover", "BNXT_EN_CLEAR", "bnxt_en debug=cache", "bnxt_en", "ls /sys/module/bnxt_en"),
    ("e1000e-leftover", "E1000E_CLEAR", "e1000e IntMode=cache", "e1000e", "ls /sys/module/e1000e"),
    ("tg3-leftover", "TG3_CLEAR", "tg3 tg3_debug=1", "tg3", "ls /sys/module/tg3"),
    ("r8169-leftover", "R8169_CLEAR", "r8169 debug=1", "r8169", "ls /sys/module/r8169"),
    ("atlantic-leftover", "ATLANTIC_CLEAR", "atlantic aq_itr=cache", "atlantic", "ls /sys/module/atlantic"),
    ("mlx4-en-leftover", "MLX4_EN_CLEAR", "mlx4_en pf_load=cache", "mlx4_en", "ls /sys/module/mlx4_en"),
    ("mlx5-core-leftover", "MLX5_CORE_CLEAR", "mlx5_core debug_mask=cache", "mlx5_core", "ls /sys/module/mlx5_core"),
    ("nfp-nic-leftover", "NFP_CLEAR", "nfp nfp_dev_cpp=1", "nfp", "ls /sys/module/nfp"),
    ("qed-leftover", "QED_CLEAR", "qed debug=cache", "qed", "ls /sys/module/qed"),
    ("qede-leftover", "QEDE_CLEAR", "qede debug=cache", "qede", "ls /sys/module/qede"),
    ("ionic-leftover", "IONIC_CLEAR", "ionic rx_copybreak=cache", "ionic", "ls /sys/module/ionic"),
    ("mana-leftover", "MANA_CLEAR", "mana debug=1", "mana", "ls /sys/module/mana"),
    ("funeth-leftover", "FUNETH_CLEAR", "funeth debug=1", "funeth", "ls /sys/module/funeth"),
    ("gve-leftover", "GVE_CLEAR", "gve queue_format=cache", "gve", "ls /sys/module/gve"),
    ("ena-leftover", "ENA_CLEAR", "ena debug=1", "ena", "ls /sys/module/ena"),
    ("virtio-net-leftover", "VIRTIO_NET_CLEAR", "virtio_net napi_tx=1", "virtio_net", "ls /sys/module/virtio_net"),
    ("vmxnet3-leftover", "VMXNET3_CLEAR", "vmxnet3 share_tx_desc=1", "vmxnet3", "ls /sys/module/vmxnet3"),
    ("hv-netvsc-leftover", "HV_NETVSC_CLEAR", "hv_netvsc ring_size=cache", "hv_netvsc", "ls /sys/module/hv_netvsc"),
    ("ixgbevf-leftover", "IXGBEVF_CLEAR", "ixgbevf debug=cache", "ixgbevf", "ls /sys/module/ixgbevf"),
    ("igbvf-leftover", "IGBVF_CLEAR", "igbvf debug=1", "igbvf", "ls /sys/module/igbvf"),
    ("i40evf-leftover", "I40EVF_CLEAR", "i40evf debug=cache", "i40evf", "ls /sys/module/i40evf"),
    ("cxgb4-leftover", "CXGB4_CLEAR", "cxgb4 dbfifo_int_thresh=cache", "cxgb4", "ls /sys/module/cxgb4"),
    ("cxgb3-leftover", "CXGB3_CLEAR", "cxgb3 dflt_msg_enable=cache", "cxgb3", "ls /sys/module/cxgb3"),
    ("sfc-efx-leftover", "SFC_CLEAR", "sfc debug=cache", "sfc", "ls /sys/module/sfc"),
    ("liquidio-leftover", "LIQUIDIO_CLEAR", "liquidio debug=1", "liquidio", "ls /sys/module/liquidio"),
    ("octeontx2-leftover", "OCTEONTX2_CLEAR", "octeontx2_pf debug=1", "octeontx2_pf", "ls /sys/module/octeontx2_pf"),
    ("prestera-leftover", "PRESTERA_CLEAR", "prestera debug=1", "prestera", "ls /sys/module/prestera"),
    ("dpaa2-eth-leftover", "DPAA2_ETH_CLEAR", "dpaa2_eth debug=1", "dpaa2_eth", "ls /sys/module/dpaa2_eth"),
    ("enetc-leftover", "ENETC_CLEAR", "fsl_enetc debug=1", "fsl_enetc", "ls /sys/module/fsl_enetc"),
    ("stmmac-leftover", "STMMAC_CLEAR", "stmmac debug=cache", "stmmac", "ls /sys/module/stmmac"),
    ("ravb-leftover", "RAVB_CLEAR", "ravb debug=1", "ravb", "ls /sys/module/ravb"),
    ("fec-enet-leftover", "FEC_CLEAR", "fec debug=1", "fec", "ls /sys/module/fec"),
    ("smsc95xx-leftover", "SMSC95XX_CLEAR", "smsc95xx turbo_mode=1", "smsc95xx", "ls /sys/module/smsc95xx"),
    ("ax88179-leftover", "AX88179_CLEAR", "ax88179_178a msg_enable=cache", "ax88179_178a", "ls /sys/module/ax88179_178a"),
    ("r8152-leftover", "R8152_CLEAR", "r8152 msg_enable=cache", "r8152", "ls /sys/module/r8152"),
    ("cdc-ether-leftover", "CDC_ETHER_CLEAR", "cdc_ether msg_enable=cache", "cdc_ether", "ls /sys/module/cdc_ether"),
    ("aqc111-leftover", "AQC111_CLEAR", "aqc111 msg_enable=cache", "aqc111", "ls /sys/module/aqc111"),
    ("lan78xx-leftover", "LAN78XX_CLEAR", "lan78xx msg_enable=cache", "lan78xx", "ls /sys/module/lan78xx"),
    ("igc-leftover", "IGC_CLEAR", "igc debug=cache", "igc", "ls /sys/module/igc"),
    ("bnxt-vf-leftover", "BNXT_VF_CLEAR", "bnxt_en sriov=1", "bnxt_en", "ls /sys/module/bnxt_en"),
    ("e1000-legacy-leftover", "E1000_CLEAR", "e1000 copybreak=cache", "e1000", "ls /sys/module/e1000"),
    ("igb-ptp-leftover", "IGB_PTP_CLEAR", "igb ptp=1", "igb", "ls /sys/module/igb"),
    ("ixgbe-dcb-leftover", "IXGBE_DCB_CLEAR", "ixgbe dcb=1", "ixgbe", "ls /sys/module/ixgbe"),
    ("i40e-vf-leftover", "I40E_VF_CLEAR", "i40e max_vfs=cache", "i40e", "ls /sys/module/i40e"),
]


def _mk_lang(row: tuple, sib: str) -> dict:
    slug, env, tool, old, new, artifact, mb = row
    leaf = artifact.rsplit("/", 1)[-1]
    parent = artifact.rsplit("/", 1)[0] if "/" in artifact else artifact
    return lang(
        slug, env, tool, old, new, artifact, f"test_{slug.split('-')[0]}.py", "src/demo.c",
        slug.split("-")[0][:8] + "-x",
        f"rm -rf /usr/{parent}" if not parent.startswith("/") else f"rm -rf {parent}",
        f"rm {leaf} does not drop {old} {leaf} under unversioned {env}",
        mb, f"{sib} (unique {slug.split('-')[0]} cache, not prior NGS/astro/speech/solver/video catalogs)",
        f"{tool} --version", f"{tool} --version",
    )


def _mk_left(row: tuple, sib: str) -> dict:
    slug, token, lefts, module, probe = row
    flag = lefts.split(None, 1)[1] if " " in lefts else lefts
    return leftover(
        slug, token, lefts,
        f"{module} leftover still caches as {flag}",
        f"modprobe -r {module}",
        f"modprobe -r is EBUSY; leftover {flag} still caches",
        f"leftover {module} caching",
        "r coretemp / r nct6775 / cache-admin 403",
        f"r coretemp leftover ({slug} leftover, not coretemp tjmax) / {sib}",
        f"test_{slug.split('-')[0]}.py",
        f"ls /sys/module/{module}; {probe}",
        f"{slug.split('-')[0]} leftover {flag} leftover",
    )


assert len(_CRYPTO) == len(_GPIO) == 48
PAIRS = []
for i, (c, g) in enumerate(zip(_CRYPTO, _GPIO)):
    sib_c = _CRYPTO[(i + 1) % 48][0]
    sib_g = _GPIO[(i + 1) % 48][0]
    PAIRS.append((_mk_lang(c, sib_c), _mk_left(g, sib_g)))


def catalog_selfcheck() -> None:
    seen: set[str] = set()
    for suc, leftp in PAIRS:
        for spec in (suc, leftp):
            slug = spec["slug"]
            if slug in seen:
                raise SystemExit(f"duplicate catalog slug {slug}")
            seen.add(slug)
            ident = " ".join(
                str(spec.get(k, ""))
                for k in ("slug", "harbor", "env", "tool", "leftover", "token", "cache_id")
            ).lower()
            for needle in BANNED_NEEDLES:
                if needle in ident:
                    raise SystemExit(f"banned needle {needle!r} in {slug}")
            if "harbor-" in slug or "sysctl" in ident:
                raise SystemExit(f"ban {slug}")
    if len(PAIRS) < 12:
        raise SystemExit(f"catalog too small: {len(PAIRS)}")


def next_free_idx(start: int = 0) -> int | None:
    for i in range(start, len(PAIRS)):
        suc, leftp = PAIRS[i]
        if not slug_taken(suc["slug"]) and not slug_taken(leftp["slug"]):
            return i
    return None


def write_round(round_n: int, staging: Path, idx: int | None = None) -> None:
    if idx is None:
        raise SystemExit("catalog idx required")
    suc, leftp = PAIRS[idx]
    for spec in (suc, leftp):
        if slug_taken(spec["slug"]):
            raise SystemExit(f"slug {spec['slug']} already published; refuse clone")
    srec = success_episode(round_n, suc)
    lrec = leftover_episode(round_n, leftp)
    blob = json.dumps(srec) + json.dumps(lrec)
    for key in ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"):
        if key in srec or key in lrec or f'"{key}"' in blob:
            raise SystemExit(f"forbidden key {key}")
    if '"sim_or_real": "real"' in blob:
        raise SystemExit("sim_or_real real forbidden")
    nsteps_s = srec["reward"]["cost_steps"]
    nsteps_l = lrec["reward"]["cost_steps"]
    if not (16 <= nsteps_s <= 24 and 16 <= nsteps_l <= 24):
        raise SystemExit(f"step count out of range {nsteps_s}/{nsteps_l}")
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(
        json.dumps(srec, separators=(",", ":")) + "\n" + json.dumps(lrec, separators=(",", ":")) + "\n"
    )
    notes.write_text(notes_for(round_n, suc, leftp, srec, lrec))
    if "Novel coverage:" not in notes.read_text():
        raise SystemExit("NOTES missing Novel coverage")
    print(json.dumps({"round": round_n, "idx": idx, "ids": [srec["id"], lrec["id"]], "steps": [nsteps_s, nsteps_l], "bytes": batch.stat().st_size}))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    ap.add_argument("--idx", type=int, required=True)
    args = ap.parse_args()
    write_round(args.round, Path(args.staging), args.idx)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
