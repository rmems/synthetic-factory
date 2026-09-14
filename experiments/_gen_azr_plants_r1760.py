#!/usr/bin/env python3
"""Emit experiments/azr-plants-r1760.py — unique object-id IDOR / BFLA for r1760+."""
from __future__ import annotations

import re
from pathlib import Path

EXPERIMENTS = Path(__file__).resolve().parent
OUT = EXPERIMENTS / "azr-plants-r1760.py"

USED_SLUGS: set[str] = set()
USED_PLANTS: set[str] = set()
USED_LOOKUPS: set[str] = set()
USED_MODS: set[str] = set()
for p in list(EXPERIMENTS.glob("azr-plants*.py")) + list(EXPERIMENTS.glob("azr-mill*.py")):
    if p.name == "azr-plants-r1760.py":
        continue
    text = p.read_text(errors="ignore")
    USED_SLUGS.update(re.findall(r"slug=['\"]([a-z0-9-]+)['\"]", text))
    USED_PLANTS.update(re.findall(r"plant=['\"]([a-z0-9-]+)['\"]", text))
    USED_LOOKUPS.update(re.findall(r"lookup=['\"]([a-z0-9_]+)['\"]", text))
    USED_MODS.update(re.findall(r"mod=['\"]([a-z0-9_]+)['\"]", text))

PREFIX = [
    "reefb", "ribbc", "samsc", "scutc", "seacc", "seizc", "sennc", "shacc", "sheec", "shroc",
    "skegc", "slabc", "snatc", "snorc", "spanc", "spenc", "sprec", "spric", "stanc", "steec",
    "stopc", "strac", "studc", "tabec", "tackc", "taffc", "thimc", "throc", "thwac", "tillc",
    "toggc", "toppc", "tranc", "treec", "trucc", "trysc", "tumbc", "turnc", "uphrc", "vangc",
    "walec", "warpc", "weatc", "whipc", "whisc", "wincc", "windc", "woolc", "xebecb", "yardc",
    "yokeC".lower(), "yuloc", "zabrc", "zuluc", "aftc", "bagc", "balkc", "battc", "beamc", "bighc",
    "bilgc", "bittc", "boomc", "bowc", "brec", "bulkc", "buntc", "cablc", "cambc", "cantc",
    "captc", "carlc", "catc", "chanc", "cheec", "choc", "clewc", "clinc", "coamc", "cockc",
]
SUFFIX = ["keel", "boom", "hatch", "rail", "post", "stay", "pin"]
PLANTS: list[str] = []
for pre in PREFIX:
    for suf in SUFFIX:
        name = pre + suf
        if name in USED_PLANTS or name in PLANTS or not name.isidentifier():
            continue
        PLANTS.append(name)
        break
    if len(PLANTS) == 80:
        break
assert len(PLANTS) == 80, len(PLANTS)
assert not (set(PLANTS) & USED_PLANTS)

FIRST = ["authn", "mask", "any_member", "list_scope"]
RESIDUAL = ["pdf", "export", "search", "mget", "csv", "admin", "webhook", "comments"]
LEFTOVER = ["put", "patch", "update"]

IDOR = [
    ("aemo-nem-idor", "AEMO NEM region object-id IDOR", "aemonems", "Aemonem", "aemonem", "NSW1", "grid_id", "aemo-nem", "region unique from AEMO"),
    ("ons-br-idor", "ONS Brazil subsystem object-id IDOR", "onsbrs", "Onsbr", "onsbr", "SE/CO", "grid_id", "ons-br", "subsystem unique from ONS"),
    ("cen-cl-idor", "CEN Chile system object-id IDOR", "cencls", "Cencl", "cencl", "SEN-N", "grid_id", "cen-cl", "system unique from CEN"),
    ("cenace-mx-idor", "CENACE control area object-id IDOR", "cenaces", "Cenace", "cenace", "SIN", "grid_id", "cenace-mx", "area unique from CENACE"),
    ("ngeso-gb-idor", "NGESO GSP object-id IDOR", "ngesos", "Ngeso", "ngeso", "GSP-001", "grid_id", "ngeso-gb", "GSP unique from NGESO"),
    ("rte-fr-idor", "RTE poste object-id IDOR", "rtefrs", "Rtefr", "rtefr", "RTE-PDL-1", "grid_id", "rte-fr", "poste unique from RTE"),
    ("tennet-nl-idor", "TenneT station object-id IDOR", "tennetnls", "Tennetnl", "tennetnl", "TTN-L-001", "grid_id", "tennet-nl", "station unique from TenneT"),
    ("fiftyhertz-idor", "50Hertz TSO object-id IDOR", "fiftyhzs", "Fiftyhz", "fiftyhz", "50HZ-TSO", "grid_id", "fiftyhertz-id", "TSO unique from 50Hertz"),
    ("amprion-idor", "Amprion TSO object-id IDOR", "amprions", "Amprion", "amprion", "AMP-TSO", "grid_id", "amprion-id", "TSO unique from Amprion"),
    ("transnetbw-idor", "TransnetBW TSO object-id IDOR", "tnbws", "Tnbw", "tnbw", "TNBW-TSO", "grid_id", "transnetbw-id", "TSO unique from TransnetBW"),
    ("ree-es-idor", "REE TSO object-id IDOR", "reeess", "Reees", "reees", "REE-TSO", "grid_id", "ree-es", "TSO unique from REE"),
    ("terna-it-idor", "Terna TSO object-id IDOR", "ternas", "Terna", "terna", "TERNA-TSO", "grid_id", "terna-it", "TSO unique from Terna"),
    ("ren-pt-idor", "REN TSO object-id IDOR", "renpts", "Renpt", "renpt", "REN-TSO", "grid_id", "ren-pt", "TSO unique from REN"),
    ("elia-be-idor", "Elia TSO object-id IDOR", "eliabes", "Eliabe", "eliabe", "ELIA-TSO", "grid_id", "elia-be", "TSO unique from Elia"),
    ("statnett-idor", "Statnett TSO object-id IDOR", "statnetts", "Statnett", "statnett", "SN-TSO", "grid_id", "statnett-id", "TSO unique from Statnett"),
    ("svk-se-idor", "Svenska kraftnat TSO object-id IDOR", "svkses", "Svkse", "svkse", "SVK-TSO", "grid_id", "svk-se", "TSO unique from SvK"),
    ("fingrid-idor", "Fingrid TSO object-id IDOR", "fingrids", "Fingrid", "fingrid", "FG-TSO", "grid_id", "fingrid-id", "TSO unique from Fingrid"),
    ("energinet-idor", "Energinet TSO object-id IDOR", "energinets", "Energinet", "energinet", "EN-TSO", "grid_id", "energinet-id", "TSO unique from Energinet"),
    ("miso-hub-idor", "MISO hub object-id IDOR", "misohubs", "Misohub", "misohub", "MINN.HUB", "grid_id", "miso-hub", "hub unique from MISO"),
    ("pjm-hub-idor", "PJM hub object-id IDOR", "pjmhubs", "Pjmhub", "pjmhub", "WESTERN-HUB", "grid_id", "pjm-hub", "hub unique from PJM"),
    ("bizum-idor", "Bizum payment object-id IDOR", "bizums", "Bizum", "bizum", "BIZUM-240115-1", "bank_id", "bizum-es", "id unique from Iberpay"),
    ("mbway-idor", "MB WAY payment object-id IDOR", "mbways", "Mbway", "mbway", "MBWAY-PT-001", "bank_id", "mbway-pt", "id unique from SIBS"),
    ("swish-idor", "Swish payment object-id IDOR", "swishs", "Swish", "swish", "SWISH-SE-001", "bank_id", "swish-se", "id unique from Bankgirot"),
    ("vipps-idor", "Vipps payment object-id IDOR", "vippss", "Vipps", "vipps", "VIPPS-NO-001", "bank_id", "vipps-no", "id unique from Vipps"),
    ("mobilepay-idor", "MobilePay payment object-id IDOR", "mpayds", "Mpayd", "mpayd", "MP-DK-001", "bank_id", "mobilepay-dk", "id unique from MobilePay"),
    ("blik-idor", "BLIK payment object-id IDOR", "bliks", "Blik", "blik", "BLIK-240115-1", "bank_id", "blik-pl", "id unique from BLIK"),
    ("payconiq-idor", "Payconiq payment object-id IDOR", "payconiqs", "Payconiq", "payconiq", "PQ-BE-001", "bank_id", "payconiq-be", "id unique from Payconiq"),
    ("twint-idor", "TWINT payment object-id IDOR", "twints", "Twint", "twint", "TWINT-CH-001", "bank_id", "twint-ch", "id unique from TWINT"),
    ("interac-idor", "Interac e-Transfer object-id IDOR", "interacs", "Interac", "interac", "INT-CA-001", "bank_id", "interac-ca", "id unique from Interac"),
    ("instapay-ph-idor", "InstaPay object-id IDOR", "instapays", "Instapay", "instapay", "IPAY-PH-001", "bank_id", "instapay-ph", "id unique from Pesonet"),
    ("paylah-idor", "PayLah object-id IDOR", "paylahs", "Paylah", "paylah", "PAYLAH-SG-001", "bank_id", "paylah-sg", "id unique from DBS"),
    ("grabpay-idor", "GrabPay object-id IDOR", "grabpays", "Grabpay", "grabpay", "GRAB-001", "bank_id", "grabpay-id", "id unique from Grab"),
    ("alipay-uid-idor", "Alipay user object-id IDOR", "alipayuids", "Alipayuid", "alipayuid", "2088123456789012", "bank_id", "alipay-uid", "uid unique from Alipay"),
    ("wechatpay-idor", "WeChat Pay object-id IDOR", "wechatpays", "Wechatpay", "wechatpay", "wxp-001", "bank_id", "wechatpay-id", "id unique from Tenpay"),
    ("unionpay-idor", "UnionPay QRC object-id IDOR", "unionpays", "Unionpay", "unionpay", "UP-QRC-001", "bank_id", "unionpay-qrc", "QRC unique from UnionPay"),
    ("pix-dict-idor", "PIX DICT key object-id IDOR", "pixdicts", "Pixdict", "pixdict", "DICT-KEY-001", "bank_id", "pix-dict", "DICT unique from BCB"),
    ("npp-payto-idor", "NPP PayTo agreement object-id IDOR", "npptos", "Nppto", "nppto", "PAYTO-AU-001", "bank_id", "npp-payto", "agreement unique from NPPA"),
    ("sctinst-idor", "SEPA Instant SCT object-id IDOR", "sctinsts", "Sctinst", "sctinst", "SCTINST-240115-1", "bank_id", "sct-inst", "txid unique from EPC"),
    ("t2s-idor", "T2S settlement object-id IDOR", "t2ss", "T2s", "t2s", "T2S-240115-1", "book_id", "t2s-ecb", "id unique from T2S"),
    ("cls-idor", "CLS settlement object-id IDOR", "clss", "Cls", "clsid", "CLS-240115-1", "book_id", "cls-id", "id unique from CLS"),
    ("gsc2-idor", "GSC-II star object-id IDOR", "gsc2s", "Gsc2", "gsc2", "GSC2.3 N012345678", "lab_id", "gsc2-id", "GSC2 unique from STScI"),
    ("usnob-idor", "USNO-B1.0 object-id IDOR", "usnobs", "Usnob", "usnob", "1234-0567891", "lab_id", "usnob-id", "USNO-B unique from USNO"),
    ("nomadcat-idor", "NOMAD catalog object-id IDOR", "nomadcats", "Nomadcat", "nomadcat", "1234-0567891", "lab_id", "nomad-cat", "NOMAD unique from USNO"),
    ("ucac3-idor", "UCAC3 star object-id IDOR", "ucac3s", "Ucac3", "ucac3", "UCAC3 123-012345", "lab_id", "ucac3-id", "UCAC3 unique from USNO"),
    ("tess-ctoi-idor", "TESS CTOI object-id IDOR", "tessctois", "Tessctoi", "tessctoi", "CTOI 123.01", "lab_id", "tess-ctoi", "CTOI unique from TESS"),
    ("des-dr-idor", "DES DR object-id IDOR", "desdrs", "Desdr", "desdr", "DES J0535-0523", "lab_id", "des-dr", "COADD unique from DES"),
    ("lsst-obj-idor", "LSST object-id IDOR", "lsstobjs", "Lsstobj", "lsstobj", "1258334841758928910", "lab_id", "lsst-obj", "diaObject unique from Rubin"),
    ("hsc-obj-idor", "HSC object-id IDOR", "hscobjs", "Hscobj", "hscobj", "HSC-1234567890123", "lab_id", "hsc-obj", "object_id unique from HSC"),
    ("decals-idor", "DECaLS object-id IDOR", "decalss", "Decals", "decals", "LS-DR9 J053514.9-052353", "lab_id", "decals-id", "ls_id unique from Legacy Survey"),
    ("gaia-dr1-idor", "Gaia DR1 source object-id IDOR", "gaiadr1s", "Gaiadr1", "gaiadr1", "Gaia DR1 1234567890123456789", "lab_id", "gaia-dr1", "source_id unique from Gaia DR1"),
    ("hip2-idor", "Hipparcos-2 object-id IDOR", "hip2s", "Hip2", "hip2", "HIP2 71683", "lab_id", "hip2-id", "HIP2 unique from new reduction"),
    ("pcilte-idor", "LTE PCI object-id IDOR", "pciltes", "Pcilte", "pcilte", "210", "net_id", "pci-lte", "PCI unique from E-UTRAN"),
    ("fiveg-guti-idor", "5G-GUTI object-id IDOR", "fiveggutis", "Fivegguti", "fivegguti", "310410-01-02-A1B2C3D4", "net_id", "5g-guti", "5G-GUTI unique from 3GPP"),
    ("amfregion-idor", "AMF Region object-id IDOR", "amfregions", "Amfregion", "amfregion", "310-410-01", "net_id", "amf-region", "AMF Region unique from 3GPP"),
    ("amfptr-idor", "AMF Pointer object-id IDOR", "amfptrs", "Amfptr", "amfptr", "2A", "net_id", "amf-ptr", "AMF Pointer unique from 3GPP"),
    ("tai-nr-idor", "NR TAI object-id IDOR", "tainrs", "Tainr", "tainr", "310-410-ABC1", "net_id", "tai-nr", "NR TAI unique from 5GS"),
    ("nssai-full-idor", "full NSSAI object-id IDOR", "nssaifulls", "Nssaifull", "nssaifull", "1-000001+2-000002", "net_id", "nssai-full", "NSSAI unique from 3GPP"),
    ("dnnni-idor", "DNN NI object-id IDOR", "dnnnis", "Dnnni", "dnnni", "ims", "net_id", "dnn-ni", "NI unique from 3GPP DNN"),
    ("lvts-idor", "LVTS payment object-id IDOR", "lvtss", "Lvts", "lvts", "LVTS-240115-1", "bank_id", "lvts-ca", "id unique from LVTS"),
    ("lynx-ca-idor", "Lynx RTGS object-id IDOR", "lynxcas", "Lynxca", "lynxca", "LYNX-240115-1", "bank_id", "lynx-ca", "id unique from Lynx"),
    ("hvcs-hk-idor", "HK HVCS object-id IDOR", "hvcshks", "Hvcshk", "hvcshk", "HVCS-240115-1", "bank_id", "hvcs-hk", "id unique from HKICL"),
    ("meps-sg-idor", "MEPS+ object-id IDOR", "mepssgs", "Mepssg", "mepssg", "MEPS-240115-1", "bank_id", "meps-sg", "id unique from MAS"),
    ("rits-jp-idor", "BOJ RTGS object-id IDOR", "ritsjps", "Ritsjp", "ritsjp", "RITS-240115-1", "bank_id", "rits-jp", "id unique from BOJ"),
    ("cips-cn-idor", "CIPS payment object-id IDOR", "cipscns", "Cipscn", "cipscn", "CIPS-240115-1", "bank_id", "cips-cn", "id unique from CIPS"),
    ("rfc-ba-idor", "RFC BA object-id IDOR", "rfcbas", "Rfcba", "rfcba", "PJM", "grid_id", "rfc-ba", "BA unique from RFC"),
    ("mro-ba-idor", "MRO BA object-id IDOR", "mrobas", "Mroba", "mroba", "MISO", "grid_id", "mro-ba", "BA unique from MRO"),
    ("npcc-ba-idor", "NPCC BA object-id IDOR", "npccbas", "Npccba", "npccba", "NYIS", "grid_id", "npcc-ba", "BA unique from NPCC"),
    ("frcc-ba-idor", "FRCC BA object-id IDOR", "frccbas", "Frccba", "frccba", "FPL", "grid_id", "frcc-ba", "BA unique from FRCC"),
    ("tre-ba-idor", "TRE BA object-id IDOR", "trebas", "Treba", "treba", "ERCO", "grid_id", "tre-ba", "BA unique from TRE"),
    ("ercot-lz-idor", "ERCOT load zone object-id IDOR", "ercotlzs", "Ercotlz", "ercotlz", "LZ_HOUSTON", "grid_id", "ercot-lz", "LZ unique from ERCOT"),
    ("caiso-hub-idor", "CAISO hub object-id IDOR", "caisohubs", "Caisohub", "caisohub", "TH_NP15_GEN-APND", "grid_id", "caiso-hub", "hub unique from CAISO"),
    ("nyiso-hub-idor", "NYISO hub object-id IDOR", "nyisohubs", "Nyisohub", "nyisohub", "N.Y.C.", "grid_id", "nyiso-hub", "hub unique from NYISO"),
    ("isone-hub-idor", "ISO-NE hub object-id IDOR", "isonehubs", "Isonehub", "isonehub", ".H.INTERNAL_HUB", "grid_id", "isone-hub", "hub unique from ISO-NE"),
    ("spp-zone-idor", "SPP zone object-id IDOR", "sppzones", "Sppzone", "sppzone", "CSWS", "grid_id", "spp-zone", "zone unique from SPP"),
    ("wecc-ba-idor", "WECC BA object-id IDOR", "weccbas", "Weccba", "weccba", "CISO", "grid_id", "wecc-ba", "BA unique from WECC"),
    ("neowise-idor", "NEOWISE object-id IDOR", "neowises", "Neowise", "neowise", "NEOWISE J053514.94-052353.9", "lab_id", "neowise-id", "source unique from NEOWISE"),
    ("iras-psc-idor", "IRAS PSC object-id IDOR", "iraspscs", "Iraspsc", "iraspsc", "IRAS 05351-0523", "lab_id", "iras-psc", "PSC unique from IRAS"),
    ("akari-fis-idor", "AKARI FIS object-id IDOR", "akarifiss", "Akarifis", "akarifis", "AKARI-FIS-J0535149-052353", "lab_id", "akari-fis", "FIS unique from JAXA"),
    ("galex-mis-idor", "GALEX MIS object-id IDOR", "galexmiss", "Galexmis", "galexmis", "GALEX MIS J053514.9-052353", "lab_id", "galex-mis", "MIS unique from MAST"),
    ("xmm-src-idor", "XMM source object-id IDOR", "xmmsrcs", "Xmmsrc", "xmmsrc", "4XMM J053514.9-052353", "lab_id", "xmm-src", "4XMM unique from XMM"),
]

assert len(IDOR) == 80, len(IDOR)
assert len({x[0] for x in IDOR}) == 80
assert len({x[2] for x in IDOR}) == 80
assert len({x[4] for x in IDOR}) == 80
assert not ({x[0] for x in IDOR} & USED_SLUGS), {x[0] for x in IDOR} & USED_SLUGS
assert not ({x[4] for x in IDOR} & USED_LOOKUPS), {x[4] for x in IDOR} & USED_LOOKUPS
assert not ({x[2] for x in IDOR} & USED_MODS), {x[2] for x in IDOR} & USED_MODS
assert "ztf-oid-idor" not in {x[0] for x in IDOR}

BFLA = [
    ("kuma-skip-delete", "Kuma Mesh delete missing dp auth", "js_route",
     "kumactl delete dataplane notes-dp  # no token",
     "kumactl get dataplane notes-dp --header 'authorization: Bearer'"),
    ("appmesh-skip-delete", "AWS App Mesh delete missing IAM", "js_route",
     "aws appmesh delete-virtual-node --mesh-name notes --virtual-node-name n  # no iam",
     "aws appmesh describe-virtual-node --mesh-name notes --virtual-node-name n"),
    ("calico-gnp-skip-delete", "Calico GNP delete missing auth", "js_route",
     "calicoctl delete gnp notes-deny-delete",
     "calicoctl get gnp notes-deny-delete --allow-version-mismatch"),
    ("antrea-skip-delete", "Antrea ClusterNetworkPolicy skip DELETE", "js_route",
     "kubectl delete acnp notes-drop  # no rbac",
     "kubectl get acnp notes-drop --as=system:serviceaccount:notes:viewer"),
    ("kubeovn-skip-delete", "Kube-OVN subnet delete missing auth", "js_route",
     "kubectl delete subnet notes-sub",
     "kubectl get subnet notes-sub -n kube-system"),
    ("multus-skip-delete", "Multus NAD delete missing rbac", "js_route",
     "kubectl delete net-attach-def notes-nad",
     "kubectl get net-attach-def notes-nad"),
    ("podman-skip-delete", "Podman rm missing --authfile", "js_route",
     "podman rm -f notes",
     "podman inspect notes --authfile=$XDG_RUNTIME_DIR/containers/auth.json"),
    ("buildah-skip-delete", "Buildah rmi missing auth", "js_route",
     "buildah rmi notes:latest",
     "buildah from --authfile auth.json notes:latest"),
    ("nerdctl-skip-delete", "nerdctl rm missing --hosts-dir auth", "js_route",
     "nerdctl rm -f notes",
     "nerdctl inspect notes --hosts-dir /etc/containerd/certs.d"),
    ("crictl-skip-delete", "crictl rmp missing --runtime-endpoint auth", "js_route",
     "crictl rmp --force notes",
     "crictl inspectp notes --runtime-endpoint unix:///run/containerd/containerd.sock"),
    ("helm-skip-delete", "Helm uninstall missing --kube-as-user", "js_route",
     "helm uninstall notes",
     "helm status notes --kube-as-user notes-viewer"),
    ("kustomize-skip-delete", "Kustomize delete missing prune auth", "js_route",
     "kustomize build . | kubectl delete -f -",
     "kustomize build . | kubectl apply --server-side --as=notes-viewer -f -"),
    ("argocd-skip-delete", "Argo CD app delete missing rbac", "js_route",
     "argocd app delete notes --yes",
     "argocd app get notes --grpc-web --auth-token $ARGOCD_TOKEN"),
    ("flux-skip-delete", "Flux kustomization delete missing impersonation", "js_route",
     "flux delete kustomization notes --silent",
     "flux get kustomization notes --as notes-viewer"),
    ("tekton-skip-delete", "Tekton PipelineRun delete missing SA", "js_route",
     "tkn pipelinerun delete notes --force",
     "tkn pipelinerun describe notes"),
    ("jenkins-skip-delete", "Jenkins job delete missing crumb", "js_route",
     "curl -X POST $JENKINS/job/notes/doDelete",
     "curl -u user:token $JENKINS/job/notes/api/json"),
    ("drone-skip-delete", "Drone build delete missing token", "js_route",
     "drone build stop org/notes 1",
     "drone build info org/notes 1 --token $DRONE_TOKEN"),
    ("concourse-skip-delete", "Concourse destroy-pipeline missing auth", "js_route",
     "fly -t ci destroy-pipeline -p notes -n",
     "fly -t ci get-pipeline -p notes"),
    ("spinnaker-skip-delete", "Spinnaker application delete missing Fiat", "js_route",
     "spin application delete notes",
     "spin application get notes --gate-endpoint $GATE"),
    ("rancher-skip-delete", "Rancher project delete missing token", "js_route",
     "rancher projects delete p-notes",
     "rancher projects ls --token $RANCHER_TOKEN"),
    ("openshift-scc-skip-delete", "OpenShift SCC delete missing cluster-admin", "js_route",
     "oc delete scc notes-restricted",
     "oc get scc notes-restricted --as=system:serviceaccount:notes:viewer"),
    ("tanzu-skip-delete", "Tanzu package delete missing context", "js_route",
     "tanzu package installed delete notes -y",
     "tanzu package installed get notes --kubeconfig $KUBECONFIG"),
    ("eks-auth-skip-delete", "EKS aws-auth delete missing mapping", "js_route",
     "kubectl delete cm aws-auth -n kube-system",
     "kubectl get cm aws-auth -n kube-system --as=notes-viewer"),
    ("gke-skip-delete", "GKE cluster delete missing iam.clusters.delete", "js_route",
     "gcloud container clusters delete notes --quiet",
     "gcloud container clusters describe notes"),
    ("aks-skip-delete", "AKS delete missing Azure RBAC", "js_route",
     "az aks delete -g rg -n notes --yes",
     "az aks show -g rg -n notes"),
    ("k3s-skip-delete", "k3s kubectl delete missing k3s.yaml", "js_route",
     "k3s kubectl delete ns notes",
     "k3s kubectl get ns notes --kubeconfig /etc/rancher/k3s/k3s.yaml"),
    ("k0s-skip-delete", "k0s kubectl delete missing admin.conf", "js_route",
     "k0s kubectl delete ns notes",
     "k0s kubectl get ns notes --kubeconfig /var/lib/k0s/pki/admin.conf"),
    ("microk8s-skip-delete", "microk8s delete missing enable rbac", "js_route",
     "microk8s kubectl delete ns notes",
     "microk8s kubectl get ns notes"),
    ("kind-skip-delete", "kind delete cluster missing kubeconfig", "js_route",
     "kind delete cluster --name notes",
     "kind get kubeconfig --name notes"),
    ("minikube-skip-delete", "minikube delete missing profile auth", "js_route",
     "minikube delete -p notes",
     "minikube profile list"),
    ("kops-skip-delete", "kops delete cluster missing state store", "js_route",
     "kops delete cluster notes.k8s.local --yes",
     "kops get cluster notes.k8s.local --state $KOPS_STATE_STORE"),
    ("kubeadm-skip-delete", "kubeadm reset missing --cert-dir auth", "js_route",
     "kubeadm reset -f",
     "kubeadm certs check-expiration"),
    ("clusterapi-skip-delete", "Cluster API delete missing identity", "js_route",
     "clusterctl delete --all",
     "clusterctl describe cluster notes --kubeconfig $KUBECONFIG"),
    ("crossplane-skip-delete", "Crossplane XRD delete missing rbac", "js_route",
     "kubectl delete xrd notes.example.org",
     "kubectl get xrd notes.example.org"),
    ("terraform-skip-delete", "Terraform destroy missing backend creds", "js_route",
     "terraform destroy -auto-approve",
     "terraform state show 'module.notes'"),
    ("pulumi-skip-delete", "Pulumi destroy missing stack passphrase", "js_route",
     "pulumi destroy -y",
     "pulumi stack --show-urns"),
    ("ansible-skip-delete", "Ansible uri DELETE missing become", "js_route",
     "ansible all -m uri -a 'url=/notes method=DELETE'",
     "ansible all -m uri -a 'url=/notes method=GET' --become-user notes"),
    ("salt-skip-delete", "Salt file.remove missing eauth", "js_route",
     "salt '*' file.remove /var/notes",
     "salt --auth pam '*' file.file_exists /var/notes"),
    ("puppet-skip-delete", "Puppet resource ensure absent missing cert", "js_route",
     "puppet resource file /var/notes ensure=absent",
     "puppet resource file /var/notes --certname notes"),
    ("chef-skip-delete", "Chef knife node delete missing key", "js_route",
     "knife node delete notes -y",
     "knife node show notes -c knife.rb"),
    ("vault-agent-skip-delete", "Vault agent sink delete missing token", "js_route",
     "vault kv delete secret/notes",
     "vault kv get secret/notes"),
    ("consul-connect-skip-delete", "Consul Connect intention delete missing ACL", "js_route",
     "consul intention delete notes-src notes-dst",
     "consul intention list -token $CONSUL_HTTP_TOKEN"),
    ("osm-mesh-skip-delete", "OSM mesh delete missing mesh-config", "js_route",
     "osm mesh delete --mesh-name notes",
     "osm mesh list --mesh-name notes"),
    ("nsm-skip-delete", "Network Service Mesh delete missing SPIFFE", "js_route",
     "kubectl delete networkservice notes",
     "kubectl get networkservice notes"),
    ("flannel-skip-delete", "Flannel CNI delete missing etcd auth", "js_route",
     "etcdctl del /coreos.com/network/subnets/notes",
     "etcdctl get /coreos.com/network/config --user root"),
    ("weave-skip-delete", "Weave Net forget missing password", "js_route",
     "weave forget 10.32.0.1",
     "weave status --password $WEAVE_PASSWORD"),
    ("gitlab-ci-skip-delete", "GitLab job erase missing job token", "js_route",
     "curl -X POST $CI_API/jobs/$id/erase",
     "curl --header JOB-TOKEN:$CI_JOB_TOKEN $CI_API/jobs/$id"),
    ("circleci-skip-delete", "CircleCI delete env missing token", "js_route",
     "curl -X DELETE https://circleci.com/api/v2/project/gh/o/n/envvar/NOTES",
     "curl -H 'Circle-Token: $TOK' https://circleci.com/api/v2/project/gh/o/n"),
    ("buildkite-skip-delete", "Buildkite job cancel missing token", "js_route",
     "curl -X PUT $BK/jobs/$id/cancel",
     "curl -H \"Authorization: Bearer $BK_TOKEN\" $BK/jobs/$id"),
    ("harvester-skip-delete", "Harvester VM delete missing kubeconfig", "js_route",
     "kubectl delete virtualmachine notes -n default",
     "kubectl get virtualmachine notes -n default"),
    ("longhorn-skip-delete", "Longhorn volume delete missing UI token", "js_route",
     "curl -X DELETE $LH/v1/volumes/notes",
     "curl $LH/v1/volumes/notes"),
    ("rook-ceph-skip-delete", "Rook CephBlockPool delete missing rbac", "js_route",
     "kubectl delete cephblockpool notes -n rook-ceph",
     "kubectl get cephblockpool notes -n rook-ceph"),
    ("openebs-skip-delete", "OpenEBS PVC delete missing storageclass", "js_route",
     "kubectl delete pvc notes-data",
     "kubectl get pvc notes-data"),
    ("portworx-skip-delete", "Portworx volume delete missing pxctl auth", "js_route",
     "pxctl volume delete notes",
     "pxctl volume inspect notes --auth-token $PX_TOKEN"),
    ("velero-skip-delete", "Velero backup delete missing SA", "js_route",
     "velero backup delete notes --confirm",
     "velero backup describe notes"),
    ("kasten-skip-delete", "Kasten restorepoint delete missing token", "js_route",
     "curl -X DELETE $K10/v1/restorepoints/notes",
     "curl -H \"Authorization: Bearer $K10\" $K10/v1/restorepoints/notes"),
    ("restic-skip-delete", "restic forget missing password file", "js_route",
     "restic forget --prune latest",
     "restic snapshots --password-file $RESTIC_PASSWORD_FILE"),
    ("borg-skip-delete", "borg delete missing passphrase", "js_route",
     "borg delete ::notes",
     "borg list --encryption-passphrase $BORG_PASSPHRASE"),
    ("duplicity-skip-delete", "duplicity remove-all-but-n missing gpg", "js_route",
     "duplicity remove-all-but-n-full 0 --force file:///notes",
     "duplicity collection-status file:///notes --encrypt-key $GPG"),
    ("rclone-skip-delete", "rclone delete missing crypt", "js_route",
     "rclone delete remote:notes",
     "rclone ls remote:notes --crypt-password $RCLONE_CRYPT"),
    ("minio-skip-delete", "MinIO mc rm missing alias auth", "js_route",
     "mc rm myminio/notes/obj",
     "mc stat myminio/notes/obj"),
    ("ceph-rgw-skip-delete", "Ceph RGW delete missing s3 auth", "js_route",
     "radosgw-admin bucket rm --bucket=notes --purge-objects",
     "radosgw-admin bucket stats --bucket=notes --uid=notes"),
    ("swift-openstack-skip-delete", "OpenStack Swift delete missing x-auth", "js_route",
     "swift delete notes",
     "swift stat notes -A $OS_AUTH_URL -U $OS_USERNAME"),
    ("garage-s3-skip-delete", "Garage S3 delete missing key", "js_route",
     "garage bucket delete notes",
     "garage bucket info notes"),
    ("seaweedfs-skip-delete", "SeaweedFS delete missing jwt", "js_route",
     "weed filer.delete /notes/obj",
     "weed filer.cat /notes/obj"),
    ("lakefs-skip-delete", "lakeFS branch delete missing access key", "js_route",
     "lakectl branch delete notes/main -y",
     "lakectl branch list lakefs://notes"),
    ("delta-share-skip-delete", "Delta Sharing share delete missing token", "js_route",
     "databricks shares delete notes",
     "databricks shares get notes"),
    ("iceberg-skip-delete", "Iceberg drop table missing catalog auth", "js_route",
     "DROP TABLE notes.t PURGE",
     "SHOW TABLES IN notes  -- catalog auth"),
    ("hudi-skip-delete", "Hudi drop table missing hoodie.meta", "js_route",
     "spark.sql('drop table notes')",
     "spark.sql('show tables in notes')"),
    ("nifi-skip-delete", "NiFi process group delete missing proxied-entity", "js_route",
     "curl -X DELETE $NIFI/process-groups/notes",
     "curl -H 'X-ProxiedEntitiesChain: notes' $NIFI/process-groups/notes"),
    ("airflow-skip-delete", "Airflow DAG delete missing auth", "js_route",
     "airflow dags delete notes -y",
     "airflow dags list-runs -d notes"),
    ("dagster-skip-delete", "Dagster job wipe missing token", "js_route",
     "dagster job wipe --job notes",
     "dagster job list --token $DAGSTER_TOKEN"),
    ("prefect-skip-delete", "Prefect deployment delete missing api-key", "js_route",
     "prefect deployment delete notes/d",
     "prefect deployment inspect notes/d"),
    ("luigi-skip-delete", "Luigi worker delete missing scheduler auth", "js_route",
     "curl -X POST $LUIGI/api/remove --data task=notes",
     "curl $LUIGI/api/task_list"),
    ("kedro-skip-delete", "Kedro catalog delete missing credentials", "js_route",
     "kedro catalog delete notes",
     "kedro catalog list --env local"),
    ("dbt-skip-delete", "dbt drop schema missing profile", "js_route",
     "dbt run-operation drop_schema --args '{schema: notes}'",
     "dbt debug --profiles-dir $HOME/.dbt"),
    ("spark-skip-delete", "Spark drop table missing hive.metastore.sasl", "js_route",
     "spark.sql('DROP TABLE notes')",
     "spark.sql('DESCRIBE TABLE notes')"),
    ("cfengine-skip-delete", "CFEngine files promise delete missing key", "js_route",
     "files: /var/notes delete => true;",
     "files: /var/notes perms => mog('600','notes','notes');"),
    ("okd-skip-delete", "OKD project delete missing cluster-admin", "js_route",
     "oc delete project notes",
     "oc get project notes --as=system:serviceaccount:notes:viewer"),
    ("gha-oidc-skip-delete", "GitHub Actions OIDC delete missing permissions", "js_route",
     "permissions: {}\njobs:\n  del:\n    runs-on: ubuntu-latest\n    steps: [{run: 'gh api -X DELETE /repos/o/n'}]",
     "permissions: { contents: read }\njobs:\n  get:\n    permissions: { id-token: write }"),
]

assert len(BFLA) == 80, len(BFLA)
assert len({x[0] for x in BFLA}) == 80
assert not ({x[0] for x in BFLA} & USED_SLUGS), {x[0] for x in BFLA} & USED_SLUGS
assert "redpanda-admin-skip-delete" not in {x[0] for x in BFLA}

TICKETS = []
for i, plant in enumerate(PLANTS):
    tag = re.sub(r"[^a-z]", "", plant)[:3].upper()
    TICKETS.append(f"{tag}-{(i % 9) + 1}")


def py_idor_row(i: int) -> str:
    slug, surface, mod, model, lookup, sample, owner, product, bug = IDOR[i]
    plant = PLANTS[i]
    ticket = TICKETS[i]
    first = FIRST[i % 4]
    residual = RESIDUAL[i % 8]
    return (
        "    dict("
        f"slug={slug!r}, plant={plant!r}, ticket={ticket!r}, surface={surface!r}, "
        f"mod={mod!r}, model={model!r}, lookup={lookup!r}, sample={sample!r}, "
        f"owner={owner!r}, first={first!r}, residual={residual!r}, "
        f"product={product!r}, bug={ticket + ' ' + bug!r}),"
    )


def py_bfla_row(i: int) -> str:
    slug, surface, family, skip, auth = BFLA[i]
    plant = PLANTS[i]
    ticket = TICKETS[i]
    leftover = LEFTOVER[i % 3]
    return (
        "    dict("
        f"slug={slug!r}, plant={plant!r}, ticket={ticket!r}, surface={surface!r}, "
        f"family={family!r}, skip={skip!r}, auth={auth!r}, leftover={leftover!r}),"
    )


header = '''"""Extra unique IDOR/BFLA plants for authz-regression-factory r1760+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r1759 vesselNNNN-sys.
Not clones of r1759 ztf-oid-idor / redpanda-admin-skip-delete.
Not clones of r1364 geohash, r1445 casbin, r1543 gstin-isd, r1560 e212, r1640 imeitac, r1720 fps-uk.
"""
from __future__ import annotations


EXTRA_IDOR_ROWS = [
'''
expand_src = (EXPERIMENTS / "azr-plants-r1504.py").read_text()
idx = expand_src.index("def extra_bflas")
body = (
    header
    + "\n".join(py_idor_row(i) for i in range(80))
    + "\n]\n\n\nBFLA_ROWS = [\n"
    + "\n".join(py_bfla_row(i) for i in range(80))
    + "\n]\n\n\n"
    + expand_src[idx:]
)
OUT.write_text(body)
print("wrote", OUT, "plants0", PLANTS[0], "idor0", IDOR[0][0], "bfla0", BFLA[0][0])
