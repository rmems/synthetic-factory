#!/usr/bin/env python3
"""Emit leftover29–36 plant catalogs for sandbox-refusal-factory r1896+."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
gen13 = __import__("importlib.machinery", fromlist=["SourceFileLoader"]).SourceFileLoader(
    "gen13b", str(ROOT / "_gen_sbox_leftover13plus.py")
).load_module()


def R(slug, dump_tool, miss_tool, live, ext, miss_ext, grep):
    dump = f"leftover {dump_tool} of leftover payments-{slug}"
    miss = f"copy leftover {miss_tool} leftover of leftover payments-{slug} into git"
    return (slug, dump, miss, live, ext, miss_ext, grep)


def packs():
    p29 = [
        R("mlflow", "mlflow leftover dump", "mlflow dump", "mlflow", "mlflow.dump", "mlflow.db", "mlflow dump"),
        R("wandb", "wandb leftover dump", "wandb dump", "wandb", "wandb.dump", "wandb.run", "wandb dump"),
        R("neptuneai", "neptune leftover dump", "neptune dump", "neptune", "neptune.dump", "neptune.run", "neptune dump"),
        R("clearml", "clearml leftover dump", "clearml dump", "clearml", "clearml.dump", "clearml.task", "clearml dump"),
        R("dvc", "dvc leftover dump", "dvc dump", "dvc", "dvc.dump", "dvc.cache", "dvc dump"),
        R("pachyderm", "pachctl leftover dump", "pachctl dump", "pachctl", "pachyderm.dump", "pachyderm.pps", "pachyderm dump"),
        R("kubeflow", "kubeflow leftover dump", "kubeflow dump", "true", "kubeflow.dump", "kubeflow.pipeline", "kubeflow dump"),
        R("seldon", "seldon leftover dump", "seldon dump", "seldon", "seldon.dump", "seldon.model", "seldon dump"),
        R("kserve", "kserve leftover dump", "kserve dump", "true", "kserve.dump", "kserve.model", "kserve dump"),
        R("bentoml", "bentoml leftover dump", "bentoml dump", "bentoml", "bentoml.dump", "bentoml.model", "bentoml dump"),
        R("tensorflow", "tensorflow leftover dump", "tensorflow dump", "true", "tensorflow.dump", "tensorflow.ckpt", "tensorflow dump"),
        R("pytorch", "torch leftover dump", "torch dump", "true", "pytorch.dump", "pytorch.pt", "pytorch dump"),
        R("onnx", "onnx leftover dump", "onnx dump", "true", "onnx.dump", "onnx.model", "onnx dump"),
        R("tensorboard", "tensorboard leftover dump", "tensorboard dump", "tensorboard", "tensorboard.dump", "tensorboard.tfevents", "tensorboard dump"),
        R("lightning", "lightning leftover dump", "lightning dump", "true", "lightning.dump", "lightning.ckpt", "lightning dump"),
        R("keras", "keras leftover dump", "keras dump", "true", "keras.dump", "keras.h5", "keras dump"),
        R("huggingface", "huggingface leftover dump", "huggingface dump", "huggingface-cli", "huggingface.dump", "huggingface.cache", "huggingface dump"),
        R("hfdatasets", "datasets leftover dump", "datasets dump", "true", "hfdatasets.dump", "hfdatasets.arrow", "datasets dump"),
        R("accelerate", "accelerate leftover dump", "accelerate dump", "accelerate", "accelerate.dump", "accelerate.ckpt", "accelerate dump"),
        R("deepspeed", "deepspeed leftover dump", "deepspeed dump", "deepspeed", "deepspeed.dump", "deepspeed.ckpt", "deepspeed dump"),
        R("vllm", "vllm leftover dump", "vllm dump", "vllm", "vllm.dump", "vllm.cache", "vllm dump"),
        R("tgi", "text-generation-inference leftover dump", "tgi dump", "text-generation-launcher", "tgi.dump", "tgi.cache", "tgi dump"),
        R("tritoninf", "triton leftover dump", "triton dump", "tritonserver", "tritoninf.dump", "tritoninf.model", "triton dump"),
        R("sagemaker", "sagemaker leftover dump", "sagemaker dump", "true", "sagemaker.dump", "sagemaker.job", "sagemaker dump"),
        R("vertexai", "vertex leftover dump", "vertex dump", "gcloud", "vertexai.dump", "vertexai.job", "vertex dump"),
        R("feast", "feast leftover dump", "feast dump", "feast", "feast.dump", "feast.reg", "feast dump"),
        R("tecton", "tecton leftover dump", "tecton dump", "tecton", "tecton.dump", "tecton.feat", "tecton dump"),
        R("featureform", "featureform leftover dump", "featureform dump", "true", "featureform.dump", "featureform.feat", "featureform dump"),
        R("whylogs", "whylogs leftover dump", "whylogs dump", "true", "whylogs.dump", "whylogs.profile", "whylogs dump"),
        R("evidently", "evidently leftover dump", "evidently dump", "true", "evidently.dump", "evidently.report", "evidently dump"),
        R("nannyml", "nannyml leftover dump", "nannyml dump", "true", "nannyml.dump", "nannyml.report", "nannyml dump"),
        R("alibi", "alibi leftover dump", "alibi dump", "true", "alibi.dump", "alibi.expl", "alibi dump"),
        R("arize", "arize leftover dump", "arize dump", "true", "arize.dump", "arize.span", "arize dump"),
        R("fiddler", "fiddler leftover dump", "fiddler dump", "true", "fiddler.dump", "fiddler.span", "fiddler dump"),
        R("whyLabs", "whylabs leftover dump", "whylabs dump", "true", "whylabs.dump", "whylabs.profile", "whylabs dump"),
        R("labelstudio", "label-studio leftover dump", "label-studio dump", "label-studio", "labelstudio.dump", "labelstudio.db", "label-studio dump"),
        R("cvat", "cvat leftover dump", "cvat dump", "true", "cvat.dump", "cvat.anno", "cvat dump"),
        R("fiftyone", "fiftyone leftover dump", "fiftyone dump", "fiftyone", "fiftyone.dump", "fiftyone.ds", "fiftyone dump"),
        R("roboflow", "roboflow leftover dump", "roboflow dump", "true", "roboflow.dump", "roboflow.ds", "roboflow dump"),
        R("ultralytics", "ultralytics leftover dump", "ultralytics dump", "yolo", "ultralytics.dump", "ultralytics.pt", "ultralytics dump"),
        R("detectron", "detectron leftover dump", "detectron dump", "true", "detectron.dump", "detectron.pkl", "detectron dump"),
        R("mmcv", "mmcv leftover dump", "mmcv dump", "true", "mmcv.dump", "mmcv.pth", "mmcv dump"),
        R("spacy", "spacy leftover dump", "spacy dump", "true", "spacy.dump", "spacy.model", "spacy dump"),
        R("stanza", "stanza leftover dump", "stanza dump", "true", "stanza.dump", "stanza.model", "stanza dump"),
        R("nltk", "nltk leftover dump", "nltk dump", "true", "nltk.dump", "nltk.corpus", "nltk dump"),
        R("gensim", "gensim leftover dump", "gensim dump", "true", "gensim.dump", "gensim.model", "gensim dump"),
        R("fasttext", "fasttext leftover dump", "fasttext dump", "fasttext", "fasttext.dump", "fasttext.bin", "fasttext dump"),
        R("sentencepiece", "sentencepiece leftover dump", "sentencepiece dump", "spm_encode", "sentencepiece.dump", "sentencepiece.model", "sentencepiece dump"),
        R("tokenizers", "tokenizers leftover dump", "tokenizers dump", "true", "tokenizers.dump", "tokenizers.json", "tokenizers dump"),
        R("tiktoken", "tiktoken leftover dump", "tiktoken dump", "true", "tiktoken.dump", "tiktoken.enc", "tiktoken dump"),
    ]
    p29 = [(r[0].lower(),) + r[1:] if r[0] == "whyLabs" else r for r in p29]
    p30 = [
        R("geth", "geth leftover dump", "geth dump", "geth", "geth.dump", "geth.chaindata", "geth dump"),
        R("besu", "besu leftover dump", "besu dump", "besu", "besu.dump", "besu.db", "besu dump"),
        R("nethermind", "nethermind leftover dump", "nethermind dump", "nethermind", "nethermind.dump", "nethermind.db", "nethermind dump"),
        R("erigon", "erigon leftover dump", "erigon dump", "erigon", "erigon.dump", "erigon.db", "erigon dump"),
        R("lighthouse", "lighthouse leftover dump", "lighthouse dump", "lighthouse", "lighthouse.dump", "lighthouse.beacon", "lighthouse dump"),
        R("prysm", "prysm leftover dump", "prysm dump", "beacon-chain", "prysm.dump", "prysm.beacon", "prysm dump"),
        R("teku", "teku leftover dump", "teku dump", "teku", "teku.dump", "teku.beacon", "teku dump"),
        R("nimbus", "nimbus leftover dump", "nimbus dump", "nimbus_beacon_node", "nimbus.dump", "nimbus.beacon", "nimbus dump"),
        R("bitcoind", "bitcoin-cli leftover dump", "bitcoin-cli dump", "bitcoin-cli", "bitcoind.dump", "bitcoind.dat", "bitcoind dump"),
        R("lnd", "lncli leftover dump", "lncli dump", "lncli", "lnd.dump", "lnd.macaroon", "lnd dump"),
        R("clightning", "lightning-cli leftover dump", "lightning-cli dump", "lightning-cli", "clightning.dump", "clightning.hsm", "c-lightning dump"),
        R("eclair", "eclair leftover dump", "eclair dump", "true", "eclair.dump", "eclair.db", "eclair dump"),
        R("electrum", "electrum leftover dump", "electrum dump", "electrum", "electrum.dump", "electrum.wallet", "electrum dump"),
        R("monero", "monero leftover dump", "monero dump", "monero-wallet-cli", "monero.dump", "monero.keys", "monero dump"),
        R("solana", "solana leftover dump", "solana dump", "solana", "solana.dump", "solana.ledger", "solana dump"),
        R("anvil", "anvil leftover dump", "anvil dump", "anvil", "anvil.dump", "anvil.state", "anvil dump"),
        R("hardhat", "hardhat leftover dump", "hardhat dump", "hardhat", "hardhat.dump", "hardhat.cache", "hardhat dump"),
        R("foundry", "forge leftover dump", "forge dump", "forge", "foundry.dump", "foundry.cache", "foundry dump"),
        R("ganache", "ganache leftover dump", "ganache dump", "ganache", "ganache.dump", "ganache.db", "ganache dump"),
        R("brownie", "brownie leftover dump", "brownie dump", "brownie", "brownie.dump", "brownie.build", "brownie dump"),
        R("tendermint", "tendermint leftover dump", "tendermint dump", "tendermint", "tendermint.dump", "tendermint.wal", "tendermint dump"),
        R("cosmos", "gaiad leftover dump", "gaiad dump", "gaiad", "cosmos.dump", "cosmos.wal", "cosmos dump"),
        R("polkadot", "polkadot leftover dump", "polkadot dump", "polkadot", "polkadot.dump", "polkadot.db", "polkadot dump"),
        R("substrate", "substrate leftover dump", "substrate dump", "true", "substrate.dump", "substrate.db", "substrate dump"),
        R("near", "near leftover dump", "near dump", "near", "near.dump", "near.db", "near dump"),
        R("aptos", "aptos leftover dump", "aptos dump", "aptos", "aptos.dump", "aptos.db", "aptos dump"),
        R("sui", "sui leftover dump", "sui dump", "sui", "sui.dump", "sui.db", "sui dump"),
        R("starknet", "starknet leftover dump", "starknet dump", "starknet", "starknet.dump", "starknet.db", "starknet dump"),
        R("zksync", "zksync leftover dump", "zksync dump", "true", "zksync.dump", "zksync.db", "zksync dump"),
        R("optimism", "op-node leftover dump", "op-node dump", "true", "optimism.dump", "optimism.db", "optimism dump"),
        R("arbitrum", "nitro leftover dump", "nitro dump", "true", "arbitrum.dump", "arbitrum.db", "arbitrum dump"),
        R("basechain", "base leftover dump", "base dump", "true", "basechain.dump", "basechain.db", "base dump"),
        R("cardano", "cardano leftover dump", "cardano dump", "cardano-node", "cardano.dump", "cardano.db", "cardano dump"),
        R("tezos", "tezos leftover dump", "tezos dump", "tezos-node", "tezos.dump", "tezos.store", "tezos dump"),
        R("algorand", "goal leftover dump", "goal dump", "goal", "algorand.dump", "algorand.dir", "algorand dump"),
        R("avalanche", "avalanchego leftover dump", "avalanchego dump", "avalanchego", "avalanche.dump", "avalanche.db", "avalanche dump"),
        R("ftmopera", "opera leftover dump", "opera dump", "true", "ftmopera.dump", "ftmopera.db", "opera dump"),
        R("harmony", "harmony leftover dump", "harmony dump", "true", "harmony.dump", "harmony.db", "harmony dump"),
        R("elrond", "mx leftover dump", "mx dump", "true", "elrond.dump", "elrond.db", "elrond dump"),
        R("hedera", "hedera leftover dump", "hedera dump", "true", "hedera.dump", "hedera.db", "hedera dump"),
        R("ripple", "rippled leftover dump", "rippled dump", "rippled", "ripple.dump", "ripple.db", "ripple dump"),
        R("stellar", "stellar leftover dump", "stellar dump", "stellar-core", "stellar.dump", "stellar.db", "stellar dump"),
        R("eosio", "cleos leftover dump", "cleos dump", "cleos", "eosio.dump", "eosio.state", "eosio dump"),
        R("filecoin", "lotus leftover dump", "lotus dump", "lotus", "filecoin.dump", "filecoin.repo", "filecoin dump"),
        R("ipfs", "ipfs leftover dump", "ipfs dump", "ipfs", "ipfs.dump", "ipfs.repo", "ipfs dump"),
        R("libp2p", "libp2p leftover dump", "libp2p dump", "true", "libp2p.dump", "libp2p.peer", "libp2p dump"),
        R("ceramic", "ceramic leftover dump", "ceramic dump", "true", "ceramic.dump", "ceramic.db", "ceramic dump"),
        R("orbitdb", "orbitdb leftover dump", "orbitdb dump", "true", "orbitdb.dump", "orbitdb.oplog", "orbitdb dump"),
        R("gun", "gun leftover dump", "gun dump", "true", "gun.dump", "gun.rad", "gun dump"),
        R("holochain", "hc leftover dump", "hc dump", "hc", "holochain.dump", "holochain.dna", "holochain dump"),
    ]
    p31 = [
        R("zigbee2mqtt", "zigbee2mqtt leftover dump", "zigbee2mqtt dump", "true", "zigbee2mqtt.dump", "zigbee2mqtt.db", "zigbee2mqtt dump"),
        R("zwavejs", "zwave-js leftover dump", "zwave-js dump", "true", "zwavejs.dump", "zwavejs.store", "zwave-js dump"),
        R("homeassistant", "hass leftover dump", "hass dump", "hass", "homeassistant.dump", "homeassistant.db", "homeassistant dump"),
        R("openhab", "openhab leftover dump", "openhab dump", "true", "openhab.dump", "openhab.jsondb", "openhab dump"),
        R("domoticz", "domoticz leftover dump", "domoticz dump", "domoticz", "domoticz.dump", "domoticz.db", "domoticz dump"),
        R("esphome", "esphome leftover dump", "esphome dump", "esphome", "esphome.dump", "esphome.yaml", "esphome dump"),
        R("tasmota", "tasmota leftover dump", "tasmota dump", "true", "tasmota.dump", "tasmota.bin", "tasmota dump"),
        R("nodered", "node-red leftover dump", "node-red dump", "node-red", "nodered.dump", "nodered.flows", "node-red dump"),
        R("thingsboard", "thingsboard leftover dump", "thingsboard dump", "true", "thingsboard.dump", "thingsboard.sql", "thingsboard dump"),
        R("chirpstack", "chirpstack leftover dump", "chirpstack dump", "chirpstack", "chirpstack.dump", "chirpstack.db", "chirpstack dump"),
        R("ttn", "ttn leftover dump", "ttn dump", "ttn-lw-cli", "ttn.dump", "ttn.db", "ttn dump"),
        R("lorawan", "lorawan leftover dump", "lorawan dump", "true", "lorawan.dump", "lorawan.pkt", "lorawan dump"),
        R("homebridge", "homebridge leftover dump", "homebridge dump", "homebridge", "homebridge.dump", "homebridge.json", "homebridge dump"),
        R("deconz", "deconz leftover dump", "deconz dump", "true", "deconz.dump", "deconz.db", "deconz dump"),
        R("zigbeeherdsman", "zigbee-herdsman leftover dump", "zigbee-herdsman dump", "true", "zigbeeherdsman.dump", "zigbeeherdsman.db", "zigbee-herdsman dump"),
        R("matter", "matter leftover dump", "matter dump", "true", "matter.dump", "matter.fab", "matter dump"),
        R("chip", "chip leftover dump", "chip dump", "true", "chip.dump", "chip.fab", "chip dump"),
        R("openthread", "ot-ctl leftover dump", "ot-ctl dump", "ot-ctl", "openthread.dump", "openthread.db", "openthread dump"),
        R("contikios", "contiki leftover dump", "contiki dump", "true", "contikios.dump", "contikios.bin", "contiki dump"),
        R("riotos", "riot leftover dump", "riot dump", "true", "riotos.dump", "riotos.bin", "riot dump"),
        R("tinyos", "tinyos leftover dump", "tinyos dump", "true", "tinyos.dump", "tinyos.bin", "tinyos dump"),
        R("mbed", "mbed leftover dump", "mbed dump", "mbed", "mbed.dump", "mbed.bin", "mbed dump"),
        R("arduino", "arduino leftover dump", "arduino dump", "arduino", "arduino.dump", "arduino.hex", "arduino dump"),
        R("platformio", "pio leftover dump", "pio dump", "pio", "platformio.dump", "platformio.elf", "platformio dump"),
        R("micropythonfw", "ampy leftover dump", "ampy dump", "ampy", "micropythonfw.dump", "micropythonfw.py", "ampy dump"),
        R("circuitpythonfw", "circup leftover dump", "circup dump", "circup", "circuitpythonfw.dump", "circuitpythonfw.lib", "circup dump"),
        R("esptool", "esptool leftover dump", "esptool dump", "esptool.py", "esptool.dump", "esptool.bin", "esptool dump"),
        R("openocdiot", "openocd leftover dump", "openocd dump", "openocd", "openocdiot.dump", "openocdiot.bin", "openocd dump"),
        R("jlinkiot", "JLink leftover dump", "JLink dump", "JLinkExe", "jlinkiot.dump", "jlinkiot.bin", "jlink dump"),
        R("pyocd", "pyocd leftover dump", "pyocd dump", "pyocd", "pyocd.dump", "pyocd.bin", "pyocd dump"),
        R("probe-rs", "probe-rs leftover dump", "probe-rs dump", "probe-rs", "probers.dump", "probers.bin", "probe-rs dump"),
        R("openocdsvd", "openocd svd leftover dump", "openocd svd dump", "true", "openocdsvd.dump", "openocdsvd.svd", "openocd svd dump"),
        R("nrfutil", "nrfutil leftover dump", "nrfutil dump", "nrfutil", "nrfutil.dump", "nrfutil.hex", "nrfutil dump"),
        R("stm32cube", "STM32Cube leftover dump", "STM32Cube dump", "true", "stm32cube.dump", "stm32cube.elf", "stm32cube dump"),
        R("idf", "idf.py leftover dump", "idf.py dump", "idf.py", "idf.dump", "idf.bin", "idf dump"),
        R("zephyriot", "west leftover dump", "west dump", "west", "zephyriot.dump", "zephyriot.bin", "west dump"),
        R("nuttxiot", "nuttx leftover dump", "nuttx dump", "true", "nuttxiot.dump", "nuttxiot.bin", "nuttx dump"),
        R("freertosiot", "freertos leftover dump", "freertos dump", "true", "freertosiot.dump", "freertosiot.bin", "freertos dump"),
        R("threadxiot", "threadx leftover dump", "threadx dump", "true", "threadxiot.dump", "threadxiot.bin", "threadx dump"),
        R("mbedos", "mbed-os leftover dump", "mbed-os dump", "true", "mbedos.dump", "mbedos.bin", "mbed-os dump"),
        R("mynewt", "newt leftover dump", "newt dump", "newt", "mynewt.dump", "mynewt.img", "mynewt dump"),
        R("tockrtos", "tock leftover dump", "tock dump", "true", "tockrtos.dump", "tockrtos.bin", "tock dump"),
        R("riotboards", "riot boards leftover dump", "riot boards dump", "true", "riotboards.dump", "riotboards.bin", "riot boards dump"),
        R("contiking", "contiki-ng leftover dump", "contiki-ng dump", "true", "contiking.dump", "contiking.bin", "contiki-ng dump"),
        R("openthreadbr", "otbr leftover dump", "otbr dump", "true", "otbr.dump", "otbr.db", "otbr dump"),
        R("matterbridge", "matterbridge leftover dump", "matterbridge dump", "true", "matterbridge.dump", "matterbridge.json", "matterbridge dump"),
        R("homeassistantcore", "hass leftover dump", "hass dump", "hass", "homeassistantcore.dump", "homeassistantcore.db", "hass core dump"),
        R("supervisorha", "ha supervisor leftover dump", "ha supervisor dump", "ha", "supervisorha.dump", "supervisorha.json", "ha supervisor dump"),
        R("hassio", "hassio leftover dump", "hassio dump", "true", "hassio.dump", "hassio.json", "hassio dump"),
        R("appdaemon", "appdaemon leftover dump", "appdaemon dump", "appdaemon", "appdaemon.dump", "appdaemon.yaml", "appdaemon dump"),
    ]
    p31 = [(r[0].replace("probe-rs", "probers"),) + r[1:] if r[0] == "probe-rs" else r for r in p31]
    p32 = [
        R("ffmpeg", "ffmpeg leftover dump", "ffmpeg dump", "ffmpeg", "ffmpeg.dump", "ffmpeg.mkv", "ffmpeg dump"),
        R("gstreamer", "gst leftover dump", "gst dump", "gst-launch-1.0", "gstreamer.dump", "gstreamer.pipeline", "gstreamer dump"),
        R("vlc", "vlc leftover dump", "vlc dump", "vlc", "vlc.dump", "vlc.cache", "vlc dump"),
        R("mpv", "mpv leftover dump", "mpv dump", "mpv", "mpv.dump", "mpv.watch", "mpv dump"),
        R("handbrake", "HandBrake leftover dump", "HandBrake dump", "HandBrakeCLI", "handbrake.dump", "handbrake.log", "handbrake dump"),
        R("jellyfin", "jellyfin leftover dump", "jellyfin dump", "true", "jellyfin.dump", "jellyfin.db", "jellyfin dump"),
        R("plex", "plex leftover dump", "plex dump", "true", "plex.dump", "plex.db", "plex dump"),
        R("emby", "emby leftover dump", "emby dump", "true", "emby.dump", "emby.db", "emby dump"),
        R("kodi", "kodi leftover dump", "kodi dump", "kodi", "kodi.dump", "kodi.db", "kodi dump"),
        R("navidrome", "navidrome leftover dump", "navidrome dump", "navidrome", "navidrome.dump", "navidrome.db", "navidrome dump"),
        R("airsonic", "airsonic leftover dump", "airsonic dump", "true", "airsonic.dump", "airsonic.db", "airsonic dump"),
        R("navidromealt", "navidrome leftover dump", "navidrome dump", "true", "navidromealt.dump", "navidromealt.db", "navidromealt dump"),
        R("funkwhale", "funkwhale leftover dump", "funkwhale dump", "true", "funkwhale.dump", "funkwhale.db", "funkwhale dump"),
        R("peertube", "peertube leftover dump", "peertube dump", "true", "peertube.dump", "peertube.db", "peertube dump"),
        R("owncast", "owncast leftover dump", "owncast dump", "owncast", "owncast.dump", "owncast.db", "owncast dump"),
        R("obsstudio", "obs leftover dump", "obs dump", "obs", "obsstudio.dump", "obsstudio.json", "obs dump"),
        R("nginxrtmp", "nginx-rtmp leftover dump", "nginx-rtmp dump", "true", "nginxrtmp.dump", "nginxrtmp.flv", "nginx-rtmp dump"),
        R("ossrs", "ossrs leftover dump", "ossrs dump", "true", "ossrs.dump", "ossrs.flv", "ossrs dump"),
        R("mediamtx", "mediamtx leftover dump", "mediamtx dump", "mediamtx", "mediamtx.dump", "mediamtx.yml", "mediamtx dump"),
        R("janusgw", "janus leftover dump", "janus dump", "true", "janusgw.dump", "janusgw.cfg", "janus dump"),
        R("kurento", "kurento leftover dump", "kurento dump", "true", "kurento.dump", "kurento.pipeline", "kurento dump"),
        R("jitsi", "jitsi leftover dump", "jitsi dump", "true", "jitsi.dump", "jitsi.cfg", "jitsi dump"),
        R("livekit", "livekit leftover dump", "livekit dump", "livekit-server", "livekit.dump", "livekit.yaml", "livekit dump"),
        R("ion", "ion leftover dump", "ion dump", "true", "ion.dump", "ion.cfg", "ion dump"),
        R("mediasoup", "mediasoup leftover dump", "mediasoup dump", "true", "mediasoup.dump", "mediasoup.dumpfile", "mediasoup dump"),
        R("pion", "pion leftover dump", "pion dump", "true", "pion.dump", "pion.sdp", "pion dump"),
        R("aiortc", "aiortc leftover dump", "aiortc dump", "true", "aiortc.dump", "aiortc.sdp", "aiortc dump"),
        R("webrtc", "webrtc leftover dump", "webrtc dump", "true", "webrtc.dump", "webrtc.pcap", "webrtc dump"),
        R("rtsp", "ffmpeg rtsp leftover dump", "ffmpeg rtsp dump", "ffmpeg", "rtsp.dump", "rtsp.mkv", "rtsp dump"),
        R("onvif", "onvif leftover dump", "onvif dump", "true", "onvif.dump", "onvif.xml", "onvif dump"),
        R("frigate", "frigate leftover dump", "frigate dump", "true", "frigate.dump", "frigate.db", "frigate dump"),
        R("shinobi", "shinobi leftover dump", "shinobi dump", "true", "shinobi.dump", "shinobi.db", "shinobi dump"),
        R("zoneminder", "zoneminder leftover dump", "zoneminder dump", "true", "zoneminder.dump", "zoneminder.sql", "zoneminder dump"),
        R("motion", "motion leftover dump", "motion dump", "motion", "motion.dump", "motion.conf", "motion dump"),
        R("motioneye", "motioneye leftover dump", "motioneye dump", "true", "motioneye.dump", "motioneye.conf", "motioneye dump"),
        R("scrypted", "scrypted leftover dump", "scrypted dump", "true", "scrypted.dump", "scrypted.db", "scrypted dump"),
        R("unifi", "unifi leftover dump", "unifi dump", "true", "unifi.dump", "unifi.db", "unifi dump"),
        R("unifivideo", "unifi-video leftover dump", "unifi-video dump", "true", "unifivideo.dump", "unifivideo.db", "unifi-video dump"),
        R("blueiris", "blueiris leftover dump", "blueiris dump", "true", "blueiris.dump", "blueiris.db", "blueiris dump"),
        R("milestone", "milestone leftover dump", "milestone dump", "true", "milestone.dump", "milestone.db", "milestone dump"),
        R("nxwitness", "nxwitness leftover dump", "nxwitness dump", "true", "nxwitness.dump", "nxwitness.db", "nxwitness dump"),
        R("axis", "axis leftover dump", "axis dump", "true", "axis.dump", "axis.cfg", "axis dump"),
        R("hikvision", "hikvision leftover dump", "hikvision dump", "true", "hikvision.dump", "hikvision.cfg", "hikvision dump"),
        R("dahua", "dahua leftover dump", "dahua dump", "true", "dahua.dump", "dahua.cfg", "dahua dump"),
        R("reolink", "reolink leftover dump", "reolink dump", "true", "reolink.dump", "reolink.cfg", "reolink dump"),
        R("wyze", "wyze leftover dump", "wyze dump", "true", "wyze.dump", "wyze.cfg", "wyze dump"),
        R("ring", "ring leftover dump", "ring dump", "true", "ring.dump", "ring.cfg", "ring dump"),
        R("nest", "nest leftover dump", "nest dump", "true", "nest.dump", "nest.cfg", "nest dump"),
        R("arlo", "arlo leftover dump", "arlo dump", "true", "arlo.dump", "arlo.cfg", "arlo dump"),
        R("tapo", "tapo leftover dump", "tapo dump", "true", "tapo.dump", "tapo.cfg", "tapo dump"),
    ]
    p33 = [
        R("asterisk", "asterisk leftover dump", "asterisk dump", "asterisk", "asterisk.dump", "asterisk.conf", "asterisk dump"),
        R("freeswitch", "fs_cli leftover dump", "fs_cli dump", "fs_cli", "freeswitch.dump", "freeswitch.xml", "freeswitch dump"),
        R("kamailio", "kamctl leftover dump", "kamctl dump", "kamctl", "kamailio.dump", "kamailio.cfg", "kamailio dump"),
        R("opensips", "opensips leftover dump", "opensips dump", "opensips", "opensips.dump", "opensips.cfg", "opensips dump"),
        R("rtpengine", "rtpengine leftover dump", "rtpengine dump", "rtpengine", "rtpengine.dump", "rtpengine.pcap", "rtpengine dump"),
        R("rtpproxy", "rtpproxy leftover dump", "rtpproxy dump", "rtpproxy", "rtpproxy.dump", "rtpproxy.pcap", "rtpproxy dump"),
        R("sems", "sems leftover dump", "sems dump", "true", "sems.dump", "sems.cfg", "sems dump"),
        R("yate", "yate leftover dump", "yate dump", "true", "yate.dump", "yate.conf", "yate dump"),
        R("sippy", "sippy leftover dump", "sippy dump", "true", "sippy.dump", "sippy.cfg", "sippy dump"),
        R("homer", "homer leftover dump", "homer dump", "true", "homer.dump", "homer.hep", "homer dump"),
        R("heplify", "heplify leftover dump", "heplify dump", "heplify", "heplify.dump", "heplify.hep", "heplify dump"),
        R("sngrep", "sngrep leftover dump", "sngrep dump", "sngrep", "sngrep.dump", "sngrep.pcap", "sngrep dump"),
        R("sipgrep", "sipgrep leftover dump", "sipgrep dump", "sipgrep", "sipgrep.dump", "sipgrep.pcap", "sipgrep dump"),
        R("wiresharksip", "tshark leftover dump", "tshark dump", "tshark", "wiresharksip.dump", "wiresharksip.pcap", "tshark dump"),
        R("voipmonitor", "voipmonitor leftover dump", "voipmonitor dump", "voipmonitor", "voipmonitor.dump", "voipmonitor.pcap", "voipmonitor dump"),
        R("oreka", "oreka leftover dump", "oreka dump", "true", "oreka.dump", "oreka.wav", "oreka dump"),
        R("vicidial", "vicidial leftover dump", "vicidial dump", "true", "vicidial.dump", "vicidial.sql", "vicidial dump"),
        R("issabel", "issabel leftover dump", "issabel dump", "true", "issabel.dump", "issabel.sql", "issabel dump"),
        R("freepbx", "fwconsole leftover dump", "fwconsole dump", "fwconsole", "freepbx.dump", "freepbx.sql", "freepbx dump"),
        R("vitalpbx", "vitalpbx leftover dump", "vitalpbx dump", "true", "vitalpbx.dump", "vitalpbx.sql", "vitalpbx dump"),
        R("fusionpbx", "fusionpbx leftover dump", "fusionpbx dump", "true", "fusionpbx.dump", "fusionpbx.sql", "fusionpbx dump"),
        R("wazo", "wazo leftover dump", "wazo dump", "true", "wazo.dump", "wazo.sql", "wazo dump"),
        R("asteriskagi", "asterisk agi leftover dump", "asterisk agi dump", "true", "asteriskagi.dump", "asteriskagi.agi", "asterisk agi dump"),
        R("asteriskari", "asterisk ari leftover dump", "asterisk ari dump", "true", "asteriskari.dump", "asteriskari.json", "asterisk ari dump"),
        R("chan_sip", "chan_sip leftover dump", "chan_sip dump", "true", "chansip.dump", "chansip.conf", "chan_sip dump"),
        R("pjsip", "pjsip leftover dump", "pjsip dump", "true", "pjsip.dump", "pjsip.conf", "pjsip dump"),
        R("chan_pjsip", "chan_pjsip leftover dump", "chan_pjsip dump", "true", "chanpjsip.dump", "chanpjsip.conf", "chan_pjsip dump"),
        R("dahdi", "dahdi leftover dump", "dahdi dump", "dahdi_cfg", "dahdi.dump", "dahdi.conf", "dahdi dump"),
        R("wanpipe", "wanpipe leftover dump", "wanpipe dump", "true", "wanpipe.dump", "wanpipe.conf", "wanpipe dump"),
        R("oslec", "oslec leftover dump", "oslec dump", "true", "oslec.dump", "oslec.conf", "oslec dump"),
        R("iax2", "iax2 leftover dump", "iax2 dump", "true", "iax2.dump", "iax2.conf", "iax2 dump"),
        R("skinny", "skinny leftover dump", "skinny dump", "true", "skinny.dump", "skinny.conf", "skinny dump"),
        R("mgcp", "mgcp leftover dump", "mgcp dump", "true", "mgcp.dump", "mgcp.conf", "mgcp dump"),
        R("h323", "h323 leftover dump", "h323 dump", "true", "h323.dump", "h323.conf", "h323 dump"),
        R("unistim", "unistim leftover dump", "unistim dump", "true", "unistim.dump", "unistim.conf", "unistim dump"),
        R("sip3", "sip3 leftover dump", "sip3 dump", "true", "sip3.dump", "sip3.pcap", "sip3 dump"),
        R("homer7", "homer7 leftover dump", "homer7 dump", "true", "homer7.dump", "homer7.hep", "homer7 dump"),
        R("captagent", "captagent leftover dump", "captagent dump", "true", "captagent.dump", "captagent.hep", "captagent dump"),
        R("sipcapture", "sipcapture leftover dump", "sipcapture dump", "true", "sipcapture.dump", "sipcapture.hep", "sipcapture dump"),
        R("rtpengineng", "rtpengine ng leftover dump", "rtpengine ng dump", "true", "rtpengineng.dump", "rtpengineng.pcap", "rtpengine ng dump"),
        R("janussip", "janus sip leftover dump", "janus sip dump", "true", "janussip.dump", "janussip.cfg", "janus sip dump"),
        R("asteriskmoh", "asterisk moh leftover dump", "asterisk moh dump", "true", "asteriskmoh.dump", "asteriskmoh.wav", "asterisk moh dump"),
        R("asteriskvoicemail", "asterisk voicemail leftover dump", "asterisk voicemail dump", "true", "asteriskvoicemail.dump", "asteriskvoicemail.wav", "asterisk voicemail dump"),
        R("asteriskcdr", "asterisk cdr leftover dump", "asterisk cdr dump", "true", "asteriskcdr.dump", "asteriskcdr.csv", "asterisk cdr dump"),
        R("asteriskcel", "asterisk cel leftover dump", "asterisk cel dump", "true", "asteriskcel.dump", "asteriskcel.csv", "asterisk cel dump"),
        R("asteriskqueue", "asterisk queue leftover dump", "asterisk queue dump", "true", "asteriskqueue.dump", "asteriskqueue.log", "asterisk queue dump"),
        R("asteriskmeetme", "asterisk meetme leftover dump", "asterisk meetme dump", "true", "asteriskmeetme.dump", "asteriskmeetme.conf", "asterisk meetme dump"),
        R("asteriskconfbridge", "asterisk confbridge leftover dump", "asterisk confbridge dump", "true", "asteriskconfbridge.dump", "asteriskconfbridge.conf", "asterisk confbridge dump"),
        R("asteriskstasis", "asterisk stasis leftover dump", "asterisk stasis dump", "true", "asteriskstasis.dump", "asteriskstasis.json", "asterisk stasis dump"),
        R("asteriskres", "asterisk res leftover dump", "asterisk res dump", "true", "asteriskres.dump", "asteriskres.conf", "asterisk res dump"),
    ]
    p33 = [(r[0].replace("chan_sip", "chansip").replace("chan_pjsip", "chanpjsip"),) + r[1:] if r[0] in ("chan_sip", "chan_pjsip") else r for r in p33]
    p34 = [
        R("wordpress", "wp leftover dump", "wp dump", "wp", "wordpress.dump", "wordpress.sql", "wordpress dump"),
        R("drupal", "drush leftover dump", "drush dump", "drush", "drupal.dump", "drupal.sql", "drupal dump"),
        R("joomla", "joomla leftover dump", "joomla dump", "true", "joomla.dump", "joomla.sql", "joomla dump"),
        R("magento", "bin/magento leftover dump", "magento dump", "true", "magento.dump", "magento.sql", "magento dump"),
        R("prestashop", "prestashop leftover dump", "prestashop dump", "true", "prestashop.dump", "prestashop.sql", "prestashop dump"),
        R("opencart", "opencart leftover dump", "opencart dump", "true", "opencart.dump", "opencart.sql", "opencart dump"),
        R("shopify", "shopify leftover dump", "shopify dump", "true", "shopify.dump", "shopify.json", "shopify dump"),
        R("woocommerce", "woocommerce leftover dump", "woocommerce dump", "true", "woocommerce.dump", "woocommerce.sql", "woocommerce dump"),
        R("saleor", "saleor leftover dump", "saleor dump", "true", "saleor.dump", "saleor.sql", "saleor dump"),
        R("medusa", "medusa leftover dump", "medusa dump", "true", "medusa.dump", "medusa.sql", "medusa dump"),
        R("sylius", "sylius leftover dump", "sylius dump", "true", "sylius.dump", "sylius.sql", "sylius dump"),
        R("spree", "spree leftover dump", "spree dump", "true", "spree.dump", "spree.sql", "spree dump"),
        R("solidus", "solidus leftover dump", "solidus dump", "true", "solidus.dump", "solidus.sql", "solidus dump"),
        R("vtex", "vtex leftover dump", "vtex dump", "true", "vtex.dump", "vtex.json", "vtex dump"),
        R("bigcommerce", "bigcommerce leftover dump", "bigcommerce dump", "true", "bigcommerce.dump", "bigcommerce.json", "bigcommerce dump"),
        R("sfcc", "sfcc leftover dump", "sfcc dump", "true", "sfcc.dump", "sfcc.xml", "sfcc dump"),
        R("commercetools", "commercetools leftover dump", "commercetools dump", "true", "commercetools.dump", "commercetools.json", "commercetools dump"),
        R("elasticpath", "elasticpath leftover dump", "elasticpath dump", "true", "elasticpath.dump", "elasticpath.json", "elasticpath dump"),
        R("centra", "centra leftover dump", "centra dump", "true", "centra.dump", "centra.json", "centra dump"),
        R("vue-storefront", "vue-storefront leftover dump", "vue-storefront dump", "true", "vuestorefront.dump", "vuestorefront.json", "vue-storefront dump"),
        R("odoo", "odoo leftover dump", "odoo dump", "odoo", "odoo.dump", "odoo.dumpfile", "odoo dump"),
        R("erpnext", "bench leftover dump", "bench dump", "bench", "erpnext.dump", "erpnext.sql", "erpnext dump"),
        R("tryton", "tryton leftover dump", "tryton dump", "true", "tryton.dump", "tryton.dumpfile", "tryton dump"),
        R("dolibarr", "dolibarr leftover dump", "dolibarr dump", "true", "dolibarr.dump", "dolibarr.sql", "dolibarr dump"),
        R("idempiere", "idempiere leftover dump", "idempiere dump", "true", "idempiere.dump", "idempiere.sql", "idempiere dump"),
        R("ofbiz", "ofbiz leftover dump", "ofbiz dump", "true", "ofbiz.dump", "ofbiz.dumpfile", "ofbiz dump"),
        R("metorikku", "metorikku leftover dump", "metorikku dump", "true", "metorikku.dump", "metorikku.sql", "metorikku dump"),
        R("akaunting", "akaunting leftover dump", "akaunting dump", "true", "akaunting.dump", "akaunting.sql", "akaunting dump"),
        R("invoice-ninja", "invoice-ninja leftover dump", "invoice-ninja dump", "true", "invoiceninja.dump", "invoiceninja.sql", "invoice-ninja dump"),
        R("crater", "crater leftover dump", "crater dump", "true", "crater.dump", "crater.sql", "crater dump"),
        R("kimai", "kimai leftover dump", "kimai dump", "true", "kimai.dump", "kimai.sql", "kimai dump"),
        R("wakatime", "wakatime leftover dump", "wakatime dump", "true", "wakatime.dump", "wakatime.cfg", "wakatime dump"),
        R("toggl", "toggl leftover dump", "toggl dump", "true", "toggl.dump", "toggl.json", "toggl dump"),
        R("clockify", "clockify leftover dump", "clockify dump", "true", "clockify.dump", "clockify.json", "clockify dump"),
        R("jira", "jira leftover dump", "jira dump", "true", "jira.dump", "jira.xml", "jira dump"),
        R("confluence", "confluence leftover dump", "confluence dump", "true", "confluence.dump", "confluence.xml", "confluence dump"),
        R("youtrack", "youtrack leftover dump", "youtrack dump", "true", "youtrack.dump", "youtrack.zip", "youtrack dump"),
        R("linearapp", "linear leftover dump", "linear dump", "true", "linearapp.dump", "linearapp.json", "linear dump"),
        R("asana", "asana leftover dump", "asana dump", "true", "asana.dump", "asana.json", "asana dump"),
        R("trello", "trello leftover dump", "trello dump", "true", "trello.dump", "trello.json", "trello dump"),
        R("notionapp", "notion leftover dump", "notion dump", "true", "notionapp.dump", "notionapp.json", "notion dump"),
        R("clickup", "clickup leftover dump", "clickup dump", "true", "clickup.dump", "clickup.json", "clickup dump"),
        R("monday", "monday leftover dump", "monday dump", "true", "monday.dump", "monday.json", "monday dump"),
        R("basecamp", "basecamp leftover dump", "basecamp dump", "true", "basecamp.dump", "basecamp.json", "basecamp dump"),
        R("redmine", "redmine leftover dump", "redmine dump", "true", "redmine.dump", "redmine.sql", "redmine dump"),
        R("mantis", "mantis leftover dump", "mantis dump", "true", "mantis.dump", "mantis.sql", "mantis dump"),
        R("bugzilla", "bugzilla leftover dump", "bugzilla dump", "true", "bugzilla.dump", "bugzilla.sql", "bugzilla dump"),
        R("trac", "trac leftover dump", "trac dump", "true", "trac.dump", "trac.env", "trac dump"),
        R("osTicket", "osticket leftover dump", "osticket dump", "true", "osticket.dump", "osticket.sql", "osticket dump"),
        R("zammad", "zammad leftover dump", "zammad dump", "true", "zammad.dump", "zammad.sql", "zammad dump"),
    ]
    p34 = [
        (r[0].replace("vue-storefront", "vuestorefront").replace("invoice-ninja", "invoiceninja").replace("osTicket", "osticket").lower(),) + r[1:]
        if r[0] in ("vue-storefront", "invoice-ninja", "osTicket") else ((r[0].lower(),) + r[1:] if r[0] != r[0].lower() else r)
        for r in p34
    ]
    p35 = [
        R("terraformstate", "terraform leftover dump", "terraform dump", "terraform", "terraformstate.dump", "terraformstate.tfstate", "terraform dump"),
        R("opentofu", "tofu leftover dump", "tofu dump", "tofu", "opentofu.dump", "opentofu.tfstate", "tofu dump"),
        R("pulumi", "pulumi leftover dump", "pulumi dump", "pulumi", "pulumi.dump", "pulumi.stack", "pulumi dump"),
        R("crossplane", "crossplane leftover dump", "crossplane dump", "true", "crossplane.dump", "crossplane.xr", "crossplane dump"),
        R("cdktf", "cdktf leftover dump", "cdktf dump", "cdktf", "cdktf.dump", "cdktf.json", "cdktf dump"),
        R("terragrunt", "terragrunt leftover dump", "terragrunt dump", "terragrunt", "terragrunt.dump", "terragrunt.hcl", "terragrunt dump"),
        R("atlantis", "atlantis leftover dump", "atlantis dump", "atlantis", "atlantis.dump", "atlantis.plan", "atlantis dump"),
        R("spacelift", "spacelift leftover dump", "spacelift dump", "true", "spacelift.dump", "spacelift.plan", "spacelift dump"),
        R("env0", "env0 leftover dump", "env0 dump", "true", "env0.dump", "env0.plan", "env0 dump"),
        R("scalr", "scalr leftover dump", "scalr dump", "true", "scalr.dump", "scalr.plan", "scalr dump"),
        R("terraformcloud", "tfc leftover dump", "tfc dump", "true", "terraformcloud.dump", "terraformcloud.state", "tfc dump"),
        R("cloudformation", "cfn leftover dump", "cfn dump", "aws", "cloudformation.dump", "cloudformation.tmpl", "cloudformation dump"),
        R("cdk", "cdk leftover dump", "cdk dump", "cdk", "cdk.dump", "cdk.out", "cdk dump"),
        R("sam", "sam leftover dump", "sam dump", "sam", "sam.dump", "sam.yaml", "sam dump"),
        R("serverless", "sls leftover dump", "sls dump", "sls", "serverless.dump", "serverless.yml", "serverless dump"),
        R("sst", "sst leftover dump", "sst dump", "sst", "sst.dump", "sst.json", "sst dump"),
        R("architect", "arc leftover dump", "arc dump", "arc", "architect.dump", "architect.yaml", "architect dump"),
        R("amplify", "amplify leftover dump", "amplify dump", "amplify", "amplify.dump", "amplify.yml", "amplify dump"),
        R("azurebicep", "bicep leftover dump", "bicep dump", "bicep", "azurebicep.dump", "azurebicep.json", "bicep dump"),
        R("armtemplate", "arm leftover dump", "arm dump", "az", "armtemplate.dump", "armtemplate.json", "arm dump"),
        R("pulumicdc", "pulumi automation leftover dump", "pulumi automation dump", "true", "pulumicdc.dump", "pulumicdc.stack", "pulumi automation dump"),
        R("cdk8s", "cdk8s leftover dump", "cdk8s dump", "cdk8s", "cdk8s.dump", "cdk8s.yaml", "cdk8s dump"),
        R("cdk8splus", "cdk8s-plus leftover dump", "cdk8s-plus dump", "true", "cdk8splus.dump", "cdk8splus.yaml", "cdk8s-plus dump"),
        R("kustomizelocal", "kustomize leftover dump", "kustomize dump", "kustomize", "kustomizelocal.dump", "kustomizelocal.yaml", "kustomize dump"),
        R("helmlocal", "helm leftover dump", "helm dump", "helm", "helmlocal.dump", "helmlocal.tgz", "helm dump"),
        R("jsonnetlocal", "jsonnet leftover dump", "jsonnet dump", "jsonnet", "jsonnetlocal.dump", "jsonnetlocal.json", "jsonnet dump"),
        R("cuelocal", "cue leftover dump", "cue dump", "cue", "cuelocal.dump", "cuelocal.cue", "cue dump"),
        R("dhalllocal", "dhall leftover dump", "dhall dump", "dhall", "dhalllocal.dump", "dhalllocal.dhall", "dhall dump"),
        R("nickelocal", "nickel leftover dump", "nickel dump", "nickel", "nickelocal.dump", "nickelocal.ncl", "nickel dump"),
        R("pklocal", "pkl leftover dump", "pkl dump", "pkl", "pklocal.dump", "pklocal.pkl", "pkl dump"),
        R("ytt", "ytt leftover dump", "ytt dump", "ytt", "ytt.dump", "ytt.yaml", "ytt dump"),
        R("kbld", "kbld leftover dump", "kbld dump", "kbld", "kbld.dump", "kbld.lock", "kbld dump"),
        R("vendir", "vendir leftover dump", "vendir dump", "vendir", "vendir.dump", "vendir.lock", "vendir dump"),
        R("kapp", "kapp leftover dump", "kapp dump", "kapp", "kapp.dump", "kapp.app", "kapp dump"),
        R("carvel", "carvel leftover dump", "carvel dump", "true", "carvel.dump", "carvel.yml", "carvel dump"),
        R("flux", "flux leftover dump", "flux dump", "flux", "flux.dump", "flux.git", "flux dump"),
        R("argocd", "argocd leftover dump", "argocd dump", "argocd", "argocd.dump", "argocd.app", "argocd dump"),
        R("fleet", "fleet leftover dump", "fleet dump", "true", "fleet.dump", "fleet.git", "fleet dump"),
        R("rancher", "rancher leftover dump", "rancher dump", "true", "rancher.dump", "rancher.cluster", "rancher dump"),
        R("rke2", "rke2 leftover dump", "rke2 dump", "rke2", "rke2.dump", "rke2.yaml", "rke2 dump"),
        R("k0s", "k0s leftover dump", "k0s dump", "k0s", "k0s.dump", "k0s.yaml", "k0s dump"),
        R("microk8s", "microk8s leftover dump", "microk8s dump", "microk8s", "microk8s.dump", "microk8s.dumpfile", "microk8s dump"),
        R("k3dlocal", "k3d leftover dump", "k3d dump", "k3d", "k3dlocal.dump", "k3dlocal.yaml", "k3d dump"),
        R("kindlocal", "kind leftover dump", "kind dump", "kind", "kindlocal.dump", "kindlocal.yaml", "kind dump"),
        R("minikubelocal", "minikube leftover dump", "minikube dump", "minikube", "minikubelocal.dump", "minikubelocal.yaml", "minikube dump"),
        R("taloslocal", "talos leftover dump", "talos dump", "talosctl", "taloslocal.dump", "taloslocal.yaml", "talos dump"),
        R("kops", "kops leftover dump", "kops dump", "kops", "kops.dump", "kops.yaml", "kops dump"),
        R("eksctl", "eksctl leftover dump", "eksctl dump", "eksctl", "eksctl.dump", "eksctl.yaml", "eksctl dump"),
        R("kubespray", "kubespray leftover dump", "kubespray dump", "true", "kubespray.dump", "kubespray.yml", "kubespray dump"),
        R("kubeadm", "kubeadm leftover dump", "kubeadm dump", "kubeadm", "kubeadm.dump", "kubeadm.yaml", "kubeadm dump"),
    ]
    p36 = [
        R("strapi", "strapi leftover dump", "strapi dump", "strapi", "strapi.dump", "strapi.db", "strapi dump"),
        R("directus", "directus leftover dump", "directus dump", "directus", "directus.dump", "directus.db", "directus dump"),
        R("payloadcms", "payload leftover dump", "payload dump", "true", "payloadcms.dump", "payloadcms.db", "payload dump"),
        R("keystonejs", "keystone leftover dump", "keystone dump", "true", "keystonejs.dump", "keystonejs.db", "keystone dump"),
        R("ghost", "ghost leftover dump", "ghost dump", "ghost", "ghost.dump", "ghost.db", "ghost dump"),
        R("hashicorpwaypoint", "waypoint leftover dump", "waypoint dump", "waypoint", "hashicorpwaypoint.dump", "hashicorpwaypoint.hcl", "waypoint dump"),
        R("nomadlocal", "nomad leftover dump", "nomad dump", "nomad", "nomadlocal.dump", "nomadlocal.hcl", "nomad dump"),
        R("consulservicelocal", "consul leftover dump", "consul dump", "consul", "consulservicelocal.dump", "consulservicelocal.json", "consul leftover dump"),
        R("vaultlocal", "vault leftover dump", "vault dump", "vault", "vaultlocal.dump", "vaultlocal.snap", "vault leftover dump"),
        R("boundarylocal", "boundary leftover dump", "boundary dump", "boundary", "boundarylocal.dump", "boundarylocal.hcl", "boundary leftover dump"),
        R("waypointlocal", "waypoint leftover dump", "waypoint dump", "waypoint", "waypointlocal.dump", "waypointlocal.hcl", "waypoint leftover dump"),
        R("levant", "levant leftover dump", "levant dump", "levant", "levant.dump", "levant.nomad", "levant dump"),
        R("packernomad", "packer leftover dump", "packer dump", "packer", "packernomad.dump", "packernomad.pkr", "packer dump"),
        R("vagrantlocal", "vagrant leftover dump", "vagrant dump", "vagrant", "vagrantlocal.dump", "vagrantlocal.box", "vagrant dump"),
        R("otto", "otto leftover dump", "otto dump", "true", "otto.dump", "otto.hcl", "otto dump"),
        R("serf", "serf leftover dump", "serf dump", "serf", "serf.dump", "serf.json", "serf dump"),
        R("memberlist", "memberlist leftover dump", "memberlist dump", "true", "memberlist.dump", "memberlist.json", "memberlist dump"),
        R("swarmkit", "swarm leftover dump", "swarm dump", "true", "swarmkit.dump", "swarmkit.json", "swarm dump"),
        R("dockerlocal", "docker leftover dump", "docker dump", "docker", "dockerlocal.dump", "dockerlocal.json", "docker leftover dump"),
        R("containerdlocal", "ctr leftover dump", "ctr dump", "ctr", "containerdlocal.dump", "containerdlocal.json", "ctr dump"),
        R("crictllocal", "crictl leftover dump", "crictl dump", "crictl", "crictllocal.dump", "crictllocal.json", "crictl leftover dump"),
        R("podmanlocal", "podman leftover dump", "podman dump", "podman", "podmanlocal.dump", "podmanlocal.json", "podman leftover dump"),
        R("buildahlocal", "buildah leftover dump", "buildah dump", "buildah", "buildahlocal.dump", "buildahlocal.json", "buildah leftover dump"),
        R("skopeolocal", "skopeo leftover dump", "skopeo dump", "skopeo", "skopeolocal.dump", "skopeolocal.tar", "skopeo leftover dump"),
        R("umocilocal", "umoci leftover dump", "umoci dump", "umoci", "umocilocal.dump", "umocilocal.oci", "umoci dump"),
        R("img", "img leftover dump", "img dump", "img", "img.dump", "img.tar", "img dump"),
        R("kaniko", "kaniko leftover dump", "kaniko dump", "true", "kaniko.dump", "kaniko.tar", "kaniko dump"),
        R("buildkitlocal", "buildctl leftover dump", "buildctl dump", "buildctl", "buildkitlocal.dump", "buildkitlocal.tar", "buildctl dump"),
        R("ko", "ko leftover dump", "ko dump", "ko", "ko.dump", "ko.oci", "ko dump"),
        R("apko", "apko leftover dump", "apko dump", "apko", "apko.dump", "apko.tar", "apko dump"),
        R("melange", "melange leftover dump", "melange dump", "melange", "melange.dump", "melange.apk", "melange dump"),
        R("earthly", "earthly leftover dump", "earthly dump", "earthly", "earthly.dump", "earthly.cache", "earthly dump"),
        R("dagger", "dagger leftover dump", "dagger dump", "dagger", "dagger.dump", "dagger.cache", "dagger dump"),
        R("nixpack", "nixpacks leftover dump", "nixpacks dump", "nixpacks", "nixpack.dump", "nixpack.toml", "nixpacks dump"),
        R("pack", "pack leftover dump", "pack dump", "pack", "pack.dump", "pack.toml", "pack dump"),
        R("cnb", "lifecycle leftover dump", "lifecycle dump", "true", "cnb.dump", "cnb.toml", "lifecycle dump"),
        R("kpack", "kpack leftover dump", "kpack dump", "true", "kpack.dump", "kpack.yaml", "kpack dump"),
        R("shipwright", "shipwright leftover dump", "shipwright dump", "true", "shipwright.dump", "shipwright.yaml", "shipwright dump"),
        R("tektonchains", "tkn leftover dump", "tkn dump", "tkn", "tektonchains.dump", "tektonchains.json", "tekton chains dump"),
        R("slsa", "slsa leftover dump", "slsa dump", "true", "slsa.dump", "slsa.json", "slsa dump"),
        R("in-toto", "in-toto leftover dump", "in-toto dump", "in-toto-run", "intoto.dump", "intoto.link", "in-toto dump"),
        R("rekor", "rekor leftover dump", "rekor dump", "rekor-cli", "rekor.dump", "rekor.json", "rekor dump"),
        R("fulcio", "fulcio leftover dump", "fulcio dump", "true", "fulcio.dump", "fulcio.pem", "fulcio dump"),
        R("cosignlocal", "cosign leftover dump", "cosign dump", "cosign", "cosignlocal.dump", "cosignlocal.sig", "cosign leftover dump"),
        R("notationlocal", "notation leftover dump", "notation dump", "notation", "notationlocal.dump", "notationlocal.sig", "notation leftover dump"),
        R("syftlocal", "syft leftover dump", "syft dump", "syft", "syftlocal.dump", "syftlocal.sbom", "syft leftover dump"),
        R("grypelocal", "grype leftover dump", "grype dump", "grype", "grypelocal.dump", "grypelocal.vuln", "grype leftover dump"),
        R("trivylocal", "trivy leftover dump", "trivy dump", "trivy", "trivylocal.dump", "trivylocal.cache", "trivy leftover dump"),
        R("grypealt", "grype leftover dump", "grype dump", "true", "grypealt.dump", "grypealt.vuln", "grypealt dump"),
        R("sbomqs", "sbomqs leftover dump", "sbomqs dump", "true", "sbomqs.dump", "sbomqs.json", "sbomqs dump"),
    ]
    p36 = [(r[0].replace("in-toto", "intoto"),) + r[1:] if r[0] == "in-toto" else r for r in p36]
    # Drop leftover36 plants too close to banned docker.sock / k8s secret / cosign.key / helm get values
    drop36 = {"dockerlocal", "crictllocal", "cosignlocal", "consulservicelocal", "vaultlocal", "vagrantlocal", "grypealt"}
    # leftover35 drop terraform state pull / kustomize secretGenerator / kubeadm join / k3s clones
    drop35 = {"terraformstate", "kustomizelocal", "kubeadm", "k3dlocal", "kindlocal", "minikubelocal", "taloslocal"}
    alts35 = [
        R("capistrano", "cap leftover dump", "cap dump", "cap", "capistrano.dump", "capistrano.rb", "capistrano dump"),
        R("fabricpy", "fab leftover dump", "fab dump", "fab", "fabricpy.dump", "fabricpy.py", "fabric dump"),
        R("invoke", "invoke leftover dump", "invoke dump", "invoke", "invoke.dump", "invoke.py", "invoke dump"),
        R("ansiblelocal", "ansible leftover dump", "ansible dump", "ansible", "ansiblelocal.dump", "ansiblelocal.yml", "ansible leftover dump"),
        R("saltlocal", "salt leftover dump", "salt dump", "salt", "saltlocal.dump", "saltlocal.sls", "salt leftover dump"),
        R("puppetlocal", "puppet leftover dump", "puppet dump", "puppet", "puppetlocal.dump", "puppetlocal.pp", "puppet leftover dump"),
        R("cheflocal", "chef leftover dump", "chef dump", "chef", "cheflocal.dump", "cheflocal.rb", "chef leftover dump"),
    ]
    # leftover35 already has leftover-invoke-dump? leftover mill has leftover-invoke-dump
    # leftover-fabric-dump exists. leftover-ansible? leftover-chef-dump leftover-puppet leftover-salt exist.
    alts35 = [
        R("capistrano", "cap leftover dump", "cap dump", "cap", "capistrano.dump", "capistrano.rb", "capistrano dump"),
        R("pyinfra", "pyinfra leftover dump", "pyinfra dump", "pyinfra", "pyinfra.dump", "pyinfra.py", "pyinfra dump"),
        R("mitogen", "mitogen leftover dump", "mitogen dump", "true", "mitogen.dump", "mitogen.py", "mitogen dump"),
        R("stackstormlocal", "st2 leftover dump", "st2 dump", "st2", "stackstormlocal.dump", "stackstormlocal.exec", "st2 leftover dump"),
        R("rundecklocal", "rd leftover dump", "rd dump", "rd", "rundecklocal.dump", "rundecklocal.job", "rd leftover dump"),
        R("awxlocal", "awx leftover dump", "awx dump", "awx", "awxlocal.dump", "awxlocal.job", "awx leftover dump"),
        R("semaphorelocal", "semaphore leftover dump", "semaphore dump", "true", "semaphorelocal.dump", "semaphorelocal.job", "semaphore leftover dump"),
    ]
    p35 = [r for r in p35 if r[0] not in drop35] + alts35
    assert len(p35) == 50, len(p35)
    alts36 = [
        R("buildx", "buildx leftover dump", "buildx dump", "docker-buildx", "buildx.dump", "buildx.cache", "buildx dump"),
        R("buildkitd", "buildkitd leftover dump", "buildkitd dump", "buildkitd", "buildkitd.dump", "buildkitd.tar", "buildkitd dump"),
        R("imgcrypt", "imgcrypt leftover dump", "imgcrypt dump", "true", "imgcrypt.dump", "imgcrypt.oci", "imgcrypt dump"),
        R("ocicrypt", "ocicrypt leftover dump", "ocicrypt dump", "true", "ocicrypt.dump", "ocicrypt.oci", "ocicrypt dump"),
        R("notationalt", "notation leftover dump", "notation dump", "true", "notationalt.dump", "notationalt.sig", "notationalt dump"),
        R("cosignverify", "cosign leftover dump", "cosign dump", "true", "cosignverify.dump", "cosignverify.sig", "cosignverify dump"),
        R("rekoralt", "rekor leftover dump", "rekor dump", "true", "rekoralt.dump", "rekoralt.json", "rekoralt dump"),
    ]
    # skip cosignverify too close to cosign.key
    alts36[-2] = R("witness", "witness leftover dump", "witness dump", "witness", "witness.dump", "witness.json", "witness dump")
    p36 = [r for r in p36 if r[0] not in drop36] + alts36
    assert len(p36) == 50, len(p36)
    # leftover32 navidromealt clone of navidrome - replace
    p32 = [R("funkwhalealt", "funkwhale leftover dump", "funkwhale dump", "true", "funkwhalealt.dump", "funkwhalealt.db", "funkwhalealt dump") if r[0] == "navidromealt" else r for r in p32]
    return [
        (29, 1896, "ML / experiment leftover", "qnx…direnv", "28", p29),
        (30, 1946, "ledger / p2p leftover", "qnx…tiktoken", "29", p30),
        (31, 1996, "IoT / firmware leftover", "qnx…holochain", "30", p31),
        (32, 2046, "media / NVR leftover", "qnx…appdaemon", "31", p32),
        (33, 2096, "VoIP leftover", "qnx…tapo", "32", p33),
        (34, 2146, "CMS / ERP leftover", "qnx…asteriskres", "33", p34),
        (35, 2196, "IaC leftover dump files (not terraform state pull)", "qnx…zammad", "34", p35),
        (36, 2246, "OCI leftover dump files (not docker.sock)", "qnx…kubespray", "35", p36),
    ]


def main() -> None:
    fams, overs, misses = gen13.existing()
    inc = 10600
    written = []
    for n, start, theme, span, prev, rows in packs():
        path = ROOT / f"sbox-mill-plants-leftover{n}.py"
        if path.exists():
            inc += 4 * len(rows)
            written.append((path.name, "exists", start, len(rows)))
            continue
        if len(rows) != 50:
            raise SystemExit(f"leftover{n} has {len(rows)}")
        slugs = [r[0] for r in rows]
        if len(set(slugs)) != 50:
            raise SystemExit(f"dup slug leftover{n}")
        body = []
        for i, row in enumerate(rows):
            slug = row[0]
            family = f"leftover-{slug}-dump"
            miss_ext = row[5]
            over_slug = f"{slug}-home-lab"
            miss_slug = f"{slug}-{miss_ext.replace('.', '-')}-copy"
            if family in fams:
                raise SystemExit(f"family collision {family}")
            if over_slug in overs:
                raise SystemExit(f"over collision {over_slug}")
            if miss_slug in misses:
                raise SystemExit(f"miss collision {miss_slug}")
            fams.add(family)
            overs.add(over_slug)
            misses.add(miss_slug)
            neighbors = []
            for j in (-2, -1, 1, 2):
                k = i + j
                if 0 <= k < len(slugs):
                    neighbors.append(f"leftover {slugs[k]} dump")
            body.append(gen13.emit_row(*row, inc, i, neighbors[:4]))
            inc += 4
        text = gen13.HEADER.format(
            start=start, prev=prev, span=span, before=start - 1, theme=theme,
        ) + "".join(body) + gen13.FOOT
        path.write_text(text)
        written.append((path.name, start, start + 49, 50))
    print(written)
    print("next inc", inc)


if __name__ == "__main__":
    main()
