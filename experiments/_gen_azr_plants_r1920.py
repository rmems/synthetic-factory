#!/usr/bin/env python3
"""Emit experiments/azr-plants-r1920.py — unique object-id IDOR / BFLA for r1920+."""
from __future__ import annotations

import re
from pathlib import Path

EXPERIMENTS = Path(__file__).resolve().parent
OUT = EXPERIMENTS / "azr-plants-r1920.py"

USED_SLUGS: set[str] = set()
USED_PLANTS: set[str] = set()
USED_LOOKUPS: set[str] = set()
USED_MODS: set[str] = set()
for p in list(EXPERIMENTS.glob("azr-plants*.py")) + list(EXPERIMENTS.glob("azr-mill*.py")):
    if p.name == "azr-plants-r1920.py":
        continue
    text = p.read_text(errors="ignore")
    USED_SLUGS.update(re.findall(r"slug=['\"]([a-z0-9-]+)['\"]", text))
    USED_PLANTS.update(re.findall(r"plant=['\"]([a-z0-9-]+)['\"]", text))
    USED_LOOKUPS.update(re.findall(r"lookup=['\"]([a-z0-9_]+)['\"]", text))
    USED_MODS.update(re.findall(r"mod=['\"]([a-z0-9_]+)['\"]", text))

PREFIX = [f"azq{i:02d}" for i in range(80)]
PLANTS = []
for pre in PREFIX:
    name = pre + "keel"
    assert name not in USED_PLANTS, name
    PLANTS.append(name)

FIRST = ["authn", "mask", "any_member", "list_scope"]
RESIDUAL = ["pdf", "export", "search", "mget", "csv", "admin", "webhook", "comments"]
LEFTOVER = ["put", "patch", "update"]

# 80 unique leftover object-id IDOR families (rail / aviation / maritime / finance / health / energy)
IDOR = [
    ("evn-wagon-idor", "EVN wagon object-id IDOR", "evnwgns", "Evnwgn", "evnwgn", "218012345678", "rail_id", "evn-wagon", "wagon unique from ERA"),
    ("aar-umler-idor", "AAR UMLER object-id IDOR", "aarumls", "Aaruml", "aaruml", "AAR-123456", "rail_id", "aar-umler", "car unique from AAR"),
    ("tops-tdbos-idor", "TOPS TDBOS object-id IDOR", "topstdbs", "Topstdb", "topstdb", "43XXX", "rail_id", "tops-tdbos", "TDBOS unique from NR"),
    ("rid-un-idor", "RID UN tank object-id IDOR", "riduns", "Ridun", "ridun", "UN-1203", "rail_id", "rid-un", "tank unique from RID"),
    ("era-vkm-idor", "ERA VKM object-id IDOR", "eravkms", "Eravkm", "eravkm", "VKM-ABCD", "rail_id", "era-vkm", "VKM unique from ERA"),
    ("tsi-wimo-idor", "TSI WIMO object-id IDOR", "tsiwimos", "Tsiwimo", "tsiwimo", "WIMO-001", "rail_id", "tsi-wimo", "WIMO unique from ERA"),
    ("nr-elr-idor", "NR ELR object-id IDOR", "nrelrs", "Nrelr", "nrelr", "ELR-MLN", "rail_id", "nr-elr", "ELR unique from NR"),
    ("rssb-gid-idor", "RSSB GID object-id IDOR", "rssbgids", "Rssbgid", "rssbgid", "GID-001", "rail_id", "rssb-gid", "GID unique from RSSB"),
    ("sncf-uic-idor", "SNCF UIC object-id IDOR", "sncfuics", "Sncfuic", "sncfuic", "87XXXXXX", "rail_id", "sncf-uic", "UIC unique from SNCF"),
    ("ric-wagon-idor", "RIC wagon object-id IDOR", "ricwgns", "Ricwgn", "ricwgn", "RIC-2180", "rail_id", "ric-wagon", "wagon unique from RIC"),
    ("db-fahrweg-idor", "DB Fahrweg object-id IDOR", "dbfwgs", "Dbfwg", "dbfwg", "FW-001", "rail_id", "db-fahrweg", "fahrweg unique from DB"),
    ("obb-vpe-idor", "OBB VPE object-id IDOR", "obbvpes", "Obbvpe", "obbvpe", "VPE-001", "rail_id", "obb-vpe", "VPE unique from OBB"),
    ("sbb-didok-idor", "SBB DIDOK object-id IDOR", "sbbdids", "Sbbdid", "sbbdid", "DIDOK-8503000", "rail_id", "sbb-didok", "DIDOK unique from SBB"),
    ("jr-rosen-idor", "JR rosen object-id IDOR", "jrrosens", "Jrrosen", "jrrosen", "ROSEN-001", "rail_id", "jr-rosen", "line unique from JR"),
    ("cr-telecode-idor", "CR telecode object-id IDOR", "crtelecs", "Crtelec", "crtelec", "BJP", "rail_id", "cr-telecode", "telecode unique from CR"),
    ("ir-crs-idor", "IR CRS object-id IDOR", "ircrss", "Ircrs", "ircrs", "NDLS", "rail_id", "ir-crs", "CRS unique from IR"),
    ("amtrak-amc-idor", "Amtrak AMC object-id IDOR", "amtamcs", "Amtamc", "amtamc", "AMC-001", "rail_id", "amtrak-amc", "AMC unique from Amtrak"),
    ("via-stp-idor", "VIA STP object-id IDOR", "viastps", "Viastp", "viastp", "STP-001", "rail_id", "via-stp", "STP unique from VIA"),
    ("metro-gtfs-idor", "Metro GTFS trip object-id IDOR", "mgtfss", "Mgtfs", "mgtfs", "TRIP-001", "rail_id", "metro-gtfs", "trip unique from GTFS"),
    ("uic-rics-idor", "UIC RICS object-id IDOR", "uicricss", "Uicrics", "uicrics", "RICS-1187", "rail_id", "uic-rics", "RICS unique from UIC"),
    ("icao24-hex-idor", "ICAO24 hex object-id IDOR", "icao24s", "Icao24", "icao24hex", "ABCDEF", "av_id", "icao24-hex", "hex unique from ICAO"),
    ("modes-icao-idor", "Mode-S ICAO object-id IDOR", "modesics", "Modesic", "modesic", "4CA123", "av_id", "modes-icao", "Mode-S unique from ICAO"),
    ("adsb-hex-idor", "ADS-B hex object-id IDOR", "adsbhexs", "Adsbhex", "adsbhex", "A1B2C3", "av_id", "adsb-hex", "hex unique from ADS-B"),
    ("flarm-id-idor", "FLARM id object-id IDOR", "flarmids", "Flarmid", "flarmid", "DDA123", "av_id", "flarm-id", "id unique from FLARM"),
    ("ogn-id-idor", "OGN id object-id IDOR", "ognids", "Ognid", "ognid", "OGN123456", "av_id", "ogn-id", "id unique from OGN"),
    ("faa-nnum-idor", "FAA N-number object-id IDOR", "faannums", "Faannum", "faannum", "N12345", "av_id", "faa-nnum", "N-number unique from FAA"),
    ("easa-csn-idor", "EASA CSN object-id IDOR", "easacsns", "Easacsn", "easacsn", "CSN-001", "av_id", "easa-csn", "CSN unique from EASA"),
    ("icao-locid-idor", "ICAO locid object-id IDOR", "icaolcids", "Icaolcid", "icaolcid", "KJFK", "av_id", "icao-locid", "locid unique from ICAO"),
    ("iata-locid-idor", "IATA locid object-id IDOR", "iatalocs", "Iataloc", "iataloc", "JFK", "av_id", "iata-locid", "locid unique from IATA"),
    ("fir-icao-idor", "FIR ICAO object-id IDOR", "firicaos", "Firicao", "firicao", "KZNY", "av_id", "fir-icao", "FIR unique from ICAO"),
    ("notam-qcode-idor", "NOTAM Q-code object-id IDOR", "notamqs", "Notamq", "notamq", "QXXXX", "av_id", "notam-q", "Q-code unique from ICAO"),
    ("sid-proc-idor", "SID procedure object-id IDOR", "sidprocs", "Sidproc", "sidproc", "DEEZZ5", "av_id", "sid-proc", "SID unique from FAA"),
    ("star-proc-idor", "STAR procedure object-id IDOR", "starprocs", "Starproc", "starproc", "CAMRN4", "av_id", "star-proc", "STAR unique from FAA"),
    ("approach-proc-idor", "approach procedure object-id IDOR", "apprprocs", "Apprproc", "apprproc", "ILS22L", "av_id", "appr-proc", "approach unique from FAA"),
    ("rnav-wp-idor", "RNAV waypoint object-id IDOR", "rnavwps", "Rnavwp", "rnavwp", "CAMRN", "av_id", "rnav-wp", "waypoint unique from FAA"),
    ("fix-ident-idor", "FIX ident object-id IDOR", "fixidents", "Fixident", "fixident", "LGA", "av_id", "fix-ident", "FIX unique from FAA"),
    ("awy-ident-idor", "airway ident object-id IDOR", "awyidents", "Awyident", "awyident", "J75", "av_id", "awy-ident", "airway unique from FAA"),
    ("tma-icao-idor", "TMA ICAO object-id IDOR", "tmaicaos", "Tmaicao", "tmaicao", "EGTT", "av_id", "tma-icao", "TMA unique from ICAO"),
    ("ctr-icao-idor", "CTR ICAO object-id IDOR", "ctricaos", "Ctricao", "ctricao", "EGLL", "av_id", "ctr-icao", "CTR unique from ICAO"),
    ("atis-id-idor", "ATIS ident object-id IDOR", "atisids", "Atisid", "atisid", "ATIS-A", "av_id", "atis-id", "ident unique from FAA"),
    ("eni-cemt-idor", "ENI CEMT object-id IDOR", "enicemts", "Enicemt", "enicemt", "04000000", "mmsi_id", "eni-cemt", "ENI unique from CCNR"),
    ("lrimo-idor", "LR/IMO object-id IDOR", "lrimos", "Lrimo", "lrimo", "9074729", "mmsi_id", "lr-imo", "LR unique from IHS"),
    ("callsign-imo-idor", "callsign object-id IDOR", "callsimos", "Callsimo", "callsimo", "3EZZ2", "mmsi_id", "callsign-imo", "callsign unique from ITU"),
    ("csi-iso6346-idor", "CSI ISO6346 object-id IDOR", "csiisos", "Csiiso", "csiiso", "MSCU1234567", "mmsi_id", "csi-iso6346", "CSI unique from BIC"),
    ("bic-owner-idor", "BIC owner code object-id IDOR", "bicowns", "Bicown", "bicown", "MSCU", "mmsi_id", "bic-owner", "owner unique from BIC"),
    ("iso6346-ck-idor", "ISO6346 check object-id IDOR", "iso6346s", "Iso6346", "iso6346ck", "MSCU1234560", "mmsi_id", "iso6346-ck", "check unique from ISO"),
    ("imo-csc-idor", "IMO CSC object-id IDOR", "imocscs", "Imocsc", "imocsc", "CSC-001", "mmsi_id", "imo-csc", "CSC unique from IMO"),
    ("solas-imo-idor", "SOLAS IMO object-id IDOR", "solasimos", "Solasimo", "solasimo", "SOLAS-001", "mmsi_id", "solas-imo", "id unique from IMO"),
    ("mmsi-mid-idor", "MMSI MID object-id IDOR", "mmsimids", "Mmsimid", "mmsimid", "338123456", "mmsi_id", "mmsi-mid", "MID unique from ITU"),
    ("ais-mmsi-idor", "AIS MMSI object-id IDOR", "aismmsis", "Aismmsi", "aismmsi", "366123456", "mmsi_id", "ais-mmsi", "MMSI unique from ITU"),
    ("cusip-idor", "CUSIP object-id IDOR", "cusipns", "Cusipn", "cusipn", "037833100", "bank_id", "cusip-9", "CUSIP unique from CUSIP"),
    ("sedol-idor", "SEDOL object-id IDOR", "sedolns", "Sedoln", "sedoln", "B0YBKJ7", "bank_id", "sedol-7", "SEDOL unique from LSE"),
    ("figi-idor", "FIGI object-id IDOR", "figins", "Figin", "fgin", "BBG000B9XRY4", "bank_id", "figi-12", "FIGI unique from Bloomberg"),
    ("ric-code-idor", "RIC object-id IDOR", "riccodes", "Riccode", "riccode", "AAPL.O", "bank_id", "ric-code", "RIC unique from Refinitiv"),
    ("six-valor-idor", "SIX valor object-id IDOR", "sixvalors", "Sixvalor", "sixvalor", "1222171", "bank_id", "six-valor", "valor unique from SIX"),
    ("isin-check-idor", "ISIN check object-id IDOR", "isinchks", "Isinchk", "isinchk", "US0378331005", "bank_id", "isin-check", "ISIN unique from ANNA"),
    ("lei-20char-idor", "LEI 20-char object-id IDOR", "lei20s", "Lei20", "lei20", "5493001KJTIIGC8Y1R12", "bank_id", "lei-20", "LEI unique from GLEIF"),
    ("bic11-idor", "BIC11 object-id IDOR", "bic11s", "Bic11", "bic11", "CHASUS33XXX", "bank_id", "bic11-id", "BIC unique from SWIFT"),
    ("mic-iso10383-idor", "MIC ISO10383 object-id IDOR", "micisos", "Miciso", "miciso", "XNYS", "bank_id", "mic-10383", "MIC unique from ISO"),
    ("cfi-iso10962-idor", "CFI ISO10962 object-id IDOR", "cfiisos", "Cfiiso", "cfiso", "ESVUFR", "bank_id", "cfi-10962", "CFI unique from ISO"),
    ("udi-di-idor", "UDI-DI object-id IDOR", "udidis", "Udidi", "udidi", "00884838000000", "lab_id", "udi-di", "DI unique from FDA"),
    ("gudid-di-idor", "GUDID DI object-id IDOR", "gudiddis", "Gudiddi", "gudiddi", "00812345678901", "lab_id", "gudid-di", "DI unique from FDA"),
    ("hibcc-lic-idor", "HIBCC LIC object-id IDOR", "hibccls", "Hibccl", "hibccl", "A999B99", "lab_id", "hibcc-lic", "LIC unique from HIBCC"),
    ("iccbba-idin-idor", "ICCBBA ISBT object-id IDOR", "iccbbas", "Iccbba", "iccbba", "W0000", "lab_id", "iccbba-idin", "ISBT unique from ICCBBA"),
    ("ndc11-pack-idor", "NDC-11 pack object-id IDOR", "ndc11s", "Ndc11", "ndc11", "00071015527", "lab_id", "ndc11-pack", "NDC unique from FDA"),
    ("unii-fda-idor", "UNII object-id IDOR", "uniifdas", "Uniifda", "uniifda", "362O9ITL9D", "lab_id", "unii-fda", "UNII unique from FDA"),
    ("rxcui-pack-idor", "RxCUI pack object-id IDOR", "rxcuips", "Rxcuip", "rxcuip", "198440", "lab_id", "rxcui-pack", "RxCUI unique from NLM"),
    ("atc-ddd-idor", "ATC DDD object-id IDOR", "atcddds", "Atcddd", "atcddd", "N02BE01", "lab_id", "atc-ddd", "ATC unique from WHO"),
    ("loinc-long-idor", "LOINC long object-id IDOR", "loinclongs", "Loinclong", "loinclong", "24323-8", "lab_id", "loinc-long", "LOINC unique from Regenstrief"),
    ("icd11-mms-idor", "ICD-11 MMS object-id IDOR", "icd11mms", "Icd11mm", "icd11mm", "1A00", "lab_id", "icd11-mms", "MMS unique from WHO"),
    ("eic-x-idor", "EIC-X object-id IDOR", "eicxs", "Eicx", "eicx", "10X1001A1001A450", "grid_id", "eic-x", "EIC unique from ENTSO-E"),
    ("mrid-cim-idor", "CIM mRID object-id IDOR", "mridcims", "Mridcim", "mridcim", "_12345678-1234", "grid_id", "mrid-cim", "mRID unique from CIM"),
    ("psr-type-idor", "PSRType object-id IDOR", "psrtypes", "Psrtype", "psrtype", "A04", "grid_id", "psr-type", "type unique from CIM"),
    ("entsoe-eic-idor", "ENTSO-E EIC object-id IDOR", "entsoeics", "Entsoeic", "entsoeic", "10Y1001A1001A83F", "grid_id", "entsoe-eic", "EIC unique from ENTSO-E"),
    ("naesb-duns-idor", "NAESB DUNS object-id IDOR", "naesbduns", "Naesbdun", "naesbdun", "006928773", "grid_id", "naesb-duns", "DUNS unique from NAESB"),
    ("oati-tag-idor", "OATI tag object-id IDOR", "oatitags", "Oatitag", "oatitagid", "123456789", "grid_id", "oati-tag", "tag unique from OATI"),
    ("eia-plant-idor", "EIA plant object-id IDOR", "eiaplants", "Eiaplant", "eiaplant", "55322", "grid_id", "eia-plant", "plant unique from EIA"),
    ("nerc-id-idor", "NERC id object-id IDOR", "nercids", "Nercid", "nercid", "NERC-001", "grid_id", "nerc-id", "id unique from NERC"),
    ("rfc-id-idor", "RFC id object-id IDOR", "rfcids", "Rfcid", "rfcid", "RFC-001", "grid_id", "rfc-id", "id unique from RFC"),
    ("serc-id-idor", "SERC id object-id IDOR", "sercids", "Sercid", "sercid", "SERC-001", "grid_id", "serc-id", "id unique from SERC"),
]

assert len(IDOR) == 80, len(IDOR)
assert len({x[0] for x in IDOR}) == 80
assert len({x[2] for x in IDOR}) == 80
assert len({x[4] for x in IDOR}) == 80
assert not ({x[0] for x in IDOR} & USED_SLUGS), {x[0] for x in IDOR} & USED_SLUGS
assert not ({x[4] for x in IDOR} & USED_LOOKUPS), {x[4] for x in IDOR} & USED_LOOKUPS
assert not ({x[2] for x in IDOR} & USED_MODS), {x[2] for x in IDOR} & USED_MODS

BFLA = [
    ("circleci-ctx-skip-delete", "CircleCI context delete missing token", "js_route",
     "curl -X DELETE $CCI/api/v2/context/$id",
     "curl -H \"Circle-Token: $CCI\" $CCI/api/v2/context/$id"),
    ("travis-job-skip-delete", "Travis job cancel missing token", "js_route",
     "travis cancel $id",
     "travis show $id --token $TRAVIS"),
    ("buildkite-pipe-skip-delete", "Buildkite pipeline delete missing token", "js_route",
     "curl -X DELETE $BK/v2/organizations/o/pipelines/notes",
     "curl -H \"Authorization: Bearer $BK\" $BK/v2/organizations/o/pipelines/notes"),
    ("drone-build-skip-delete", "Drone build delete missing token", "js_route",
     "drone build stop o/notes 1",
     "drone build info o/notes 1"),
    ("concourse-job-skip-delete", "Concourse job abort missing token", "js_route",
     "fly abort-build -j notes/job -b 1",
     "fly watch -j notes/job -b 1"),
    ("harness-pipe-skip-delete", "Harness pipeline delete missing api-key", "js_route",
     "curl -X DELETE $HARNESS/v1/orgs/o/pipelines/notes",
     "curl -H \"x-api-key: $HARNESS\" $HARNESS/v1/orgs/o/pipelines/notes"),
    ("spinnaker-app-skip-delete", "Spinnaker application delete missing token", "js_route",
     "spin application delete notes",
     "spin application get notes"),
    ("tekton-pipe-skip-delete", "Tekton pipeline delete missing SA", "js_route",
     "tkn pipeline delete notes -f",
     "tkn pipeline describe notes"),
    ("flux-ks-skip-delete", "Flux kustomization delete missing kubeconfig", "js_route",
     "flux delete kustomization notes",
     "flux get kustomizations notes --kubeconfig $KUBECONFIG"),
    ("argocd-app-skip-delete", "Argo CD app delete missing token", "js_route",
     "argocd app delete notes --yes",
     "argocd app get notes --auth-token $ARGOCD"),
    ("helm-rel-skip-delete", "Helm release uninstall missing kubeconfig", "js_route",
     "helm uninstall notes",
     "helm status notes --kubeconfig $KUBECONFIG"),
    ("pulumi-stack-skip-delete", "Pulumi stack rm missing token", "js_route",
     "pulumi stack rm notes --yes",
     "pulumi stack ls --access-token $PULUMI"),
    ("tfstate-skip-delete", "Terraform state rm missing backend creds", "js_route",
     "terraform state rm notes.a",
     "terraform state list"),
    ("ansible-inv-skip-delete", "Ansible inventory delete missing vault", "js_route",
     "ansible-inventory --delete notes",
     "ansible-inventory --host notes --vault-password-file $VAULT"),
    ("salt-key-skip-delete", "Salt key delete missing eauth", "js_route",
     "salt-key -d notes -y",
     "salt-key -L --eauth pam"),
    ("chef-node-skip-delete", "Chef node delete missing client key", "js_route",
     "knife node delete notes -y",
     "knife node show notes -k $CHEF"),
    ("puppet-cert-skip-delete", "Puppet cert clean missing CA", "js_route",
     "puppetserver ca clean --certname notes",
     "puppetserver ca list --certname notes"),
    ("packer-img-skip-delete", "Packer image delete missing creds", "js_route",
     "packer delete notes",
     "packer inspect notes.pkr.hcl"),
    ("vagrant-box-skip-delete", "Vagrant box remove missing cloud token", "js_route",
     "vagrant box remove notes --force",
     "vagrant cloud box show notes --token $VAGRANT"),
    ("molecule-skip-delete", "Molecule destroy missing vault", "js_route",
     "molecule destroy -s notes",
     "molecule list -s notes"),
    ("inspec-skip-delete", "InSpec profile delete missing token", "js_route",
     "inspec supermarket unshare notes",
     "inspec supermarket info notes --token $INSPEC"),
    ("kitchen-skip-delete", "Test Kitchen destroy missing creds", "js_route",
     "kitchen destroy notes",
     "kitchen list notes"),
    ("terragrunt-skip-delete", "Terragrunt destroy missing IAM", "js_route",
     "terragrunt destroy -auto-approve",
     "terragrunt output"),
    ("crossplane-xr-skip-delete", "Crossplane XR delete missing rbac", "js_route",
     "kubectl delete xr notes",
     "kubectl get xr notes"),
    ("capi-cluster-skip-delete", "Cluster API cluster delete missing rbac", "js_route",
     "clusterctl delete cluster notes",
     "kubectl get cluster notes"),
    ("velero-bck-skip-delete", "Velero backup delete missing SA", "js_route",
     "velero backup delete notes --confirm",
     "velero backup describe notes"),
    ("restic-snap-skip-delete", "restic snapshot forget missing password", "js_route",
     "restic forget notes --prune",
     "restic snapshots --password-file $RESTIC"),
    ("borg-arch-skip-delete", "Borg archive delete missing passphrase", "js_route",
     "borg delete repo::notes",
     "borg list repo --encryption-passphrase $BORG"),
    ("rclone-rm-skip-delete", "rclone delete missing config", "js_route",
     "rclone delete notes:path --rmdirs",
     "rclone ls notes: --config $RCLONE"),
    ("minio-obj-skip-delete", "MinIO object delete missing access key", "js_route",
     "mc rm notes/b/o --force",
     "mc ls notes/b --access-key $MINIO"),
    ("ceph-pool-skip-delete", "Ceph pool delete missing cephx", "js_route",
     "ceph osd pool delete notes notes --yes-i-really-really-mean-it",
     "ceph osd pool ls --id admin"),
    ("gluster-vol-skip-delete", "Gluster volume delete missing auth", "js_route",
     "gluster volume delete notes",
     "gluster volume info notes"),
    ("longhorn-vol-skip-delete", "Longhorn volume delete missing rbac", "js_route",
     "kubectl delete volume.longhorn.io notes",
     "kubectl get volume.longhorn.io notes"),
    ("openebs-vol-skip-delete", "OpenEBS volume delete missing rbac", "js_route",
     "kubectl delete pvc notes",
     "kubectl get cstorvolume notes"),
    ("rook-pool-skip-delete", "Rook pool delete missing rbac", "js_route",
     "kubectl delete cephblockpool notes",
     "kubectl get cephblockpool notes"),
    ("portworx-vol-skip-delete", "Portworx volume delete missing token", "js_route",
     "pxctl volume delete notes",
     "pxctl volume inspect notes --token $PX"),
    ("mayastor-skip-delete", "Mayastor volume delete missing rbac", "js_route",
     "kubectl delete diskpool notes",
     "kubectl get diskpool notes"),
    ("csi-snap-skip-delete", "CSI snapshot delete missing rbac", "js_route",
     "kubectl delete volumesnapshot notes",
     "kubectl get volumesnapshot notes"),
    ("zfs-ds-skip-delete", "ZFS dataset destroy missing sudoers", "js_route",
     "zfs destroy -r notes/ds",
     "zfs list notes/ds"),
    ("btrfs-sub-skip-delete", "btrfs subvolume delete missing auth", "js_route",
     "btrfs subvolume delete notes",
     "btrfs subvolume list notes"),
    ("lvm-lv-skip-delete", "LVM LV remove missing sudoers", "js_route",
     "lvremove -f notes/lv",
     "lvs notes/lv"),
    ("mdadm-arr-skip-delete", "mdadm array stop missing sudoers", "js_route",
     "mdadm --stop /dev/md/notes",
     "mdadm --detail /dev/md/notes"),
    ("nvme-ns-skip-delete", "NVMe ns delete missing admin", "js_route",
     "nvme delete-ns /dev/nvme0 -n 1",
     "nvme list-ns /dev/nvme0"),
    ("spdk-bdev-skip-delete", "SPDK bdev delete missing rpc sock", "js_route",
     "rpc.py bdev_malloc_delete notes",
     "rpc.py bdev_get_bdevs"),
    ("rbd-img-skip-delete", "RBD image rm missing cephx", "js_route",
     "rbd rm notes/img",
     "rbd info notes/img --id admin"),
    ("rgw-bkt-skip-delete", "RGW bucket rm missing s3 creds", "js_route",
     "radosgw-admin bucket rm --bucket=notes --purge-objects",
     "radosgw-admin bucket list --uid notes"),
    ("seaweed-vol-skip-delete", "SeaweedFS volume delete missing jwt", "js_route",
     "weed filer.delete -fileId notes",
     "weed filer.cat -fileId notes -jwt $WEED"),
    ("garage-bkt-skip-delete", "Garage bucket delete missing admin", "js_route",
     "garage bucket delete notes",
     "garage bucket info notes"),
    ("juicefs-meta-skip-delete", "JuiceFS destroy missing meta auth", "js_route",
     "juicefs destroy redis://notes --force",
     "juicefs status redis://notes"),
    ("kopia-snap-skip-delete", "Kopia snapshot delete missing password", "js_route",
     "kopia snapshot delete notes --force",
     "kopia snapshot list --password $KOPIA"),
    ("duplicati-skip-delete", "Duplicati backup delete missing auth", "js_route",
     "duplicati-cli delete notes",
     "duplicati-cli list-filesets notes --passphrase $DUP"),
    ("urbackup-skip-delete", "UrBackup client delete missing auth", "js_route",
     "urbackupclientctl remove notes",
     "urbackupclientctl status"),
    ("bacula-job-skip-delete", "Bacula purge missing console password", "js_route",
     "bconsole -c /etc/bacula/bconsole.conf <<< 'purge volume=notes'",
     "bconsole <<< 'list volumes'"),
    ("bareos-job-skip-delete", "Bareos purge missing console", "js_route",
     "bconsole <<< 'purge volume=notes'",
     "bconsole <<< 'list jobs'"),
    ("amanda-dle-skip-delete", "Amanda DLE delete missing auth", "js_route",
     "amrmtape notes tape",
     "amadmin notes disklist"),
    ("backuppc-skip-delete", "BackupPC host delete missing auth", "js_route",
     "BackupPC_backupDelete notes 1",
     "BackupPC_serverMesg status hosts"),
    ("rsnapshot-skip-delete", "rsnapshot rm leftover missing ssh key", "js_route",
     "rsnapshot -c notes.conf delete hourly.0",
     "rsnapshot -c notes.conf du"),
    ("rdiff-skip-delete", "rdiff-backup remove missing ssh", "js_route",
     "rdiff-backup --remove-older-than 1s notes",
     "rdiff-backup --list-increments notes"),
    ("borgmatic-skip-delete", "borgmatic prune missing passphrase", "js_route",
     "borgmatic prune --force",
     "borgmatic list --override storage.encryption_passphrase=$BORG"),
    ("k8up-skip-delete", "K8up restore delete missing rbac", "js_route",
     "kubectl delete restore.k8up.io notes",
     "kubectl get restore.k8up.io notes"),
    ("stash-bck-skip-delete", "Stash backup delete missing rbac", "js_route",
     "kubectl delete backup.stash.appscode.com notes",
     "kubectl get backup.stash.appscode.com notes"),
    ("kanister-skip-delete", "Kanister actionset delete missing rbac", "js_route",
     "kubectl delete actionset notes",
     "kubectl get actionset notes"),
    ("cnpg-bck-skip-delete", "CNPG backup delete missing rbac", "js_route",
     "kubectl delete backup.postgresql.cnpg.io notes",
     "kubectl get backup.postgresql.cnpg.io notes"),
    ("repmgr-skip-delete", "repmgr standby unregister missing postgres", "js_route",
     "repmgr standby unregister --node-id=2",
     "repmgr cluster show"),
    ("pgbackrest-skip-delete", "pgBackRest expire missing stanza creds", "js_route",
     "pgbackrest --stanza=notes expire --retention-full=0",
     "pgbackrest --stanza=notes info"),
    ("walg-skip-delete", "WAL-G delete missing AWS keys", "js_route",
     "wal-g delete everything --confirm",
     "wal-g backup-list"),
    ("barman-skip-delete", "Barman delete missing postgres user", "js_route",
     "barman delete notes 20240115T000000",
     "barman list-backup notes"),
    ("mongodump-skip-delete", "mongodump drop missing auth", "js_route",
     "mongo notes --eval 'db.dropDatabase()'",
     "mongosh --username notes --password $MONGO"),
    ("opensearch-idx-skip-delete", "OpenSearch index delete missing auth", "js_route",
     "curl -X DELETE $OS/notes",
     "curl -u admin:$OS $OS/notes"),
    ("solr-core-skip-delete", "Solr core unload missing basicAuth", "js_route",
     "curl -X POST $SOLR/admin/cores?action=UNLOAD&core=notes",
     "curl --user solr:$SOLR $SOLR/admin/cores?action=STATUS&core=notes"),
    ("meili-idx-skip-delete", "Meilisearch index delete missing key", "js_route",
     "curl -X DELETE $MEILI/indexes/notes",
     "curl -H \"Authorization: Bearer $MEILI\" $MEILI/indexes/notes"),
    ("typesense-skip-delete", "Typesense collection delete missing key", "js_route",
     "curl -X DELETE $TS/collections/notes",
     "curl -H \"X-TYPESENSE-API-KEY: $TS\" $TS/collections/notes"),
    ("vespa-doc-skip-delete", "Vespa document delete missing cert", "js_route",
     "vespa document delete id:notes:notes::1",
     "vespa document get id:notes:notes::1 --cert $VESPA"),
    ("milvus-col-skip-delete", "Milvus collection drop missing token", "js_route",
     "curl -X POST $MILVUS/v2/vectordb/collections/drop -d {collectionName:notes}",
     "curl -H \"Authorization: Bearer $MILVUS\" $MILVUS/v2/vectordb/collections/describe"),
    ("qdrant-col-skip-delete", "Qdrant collection delete missing api-key", "js_route",
     "curl -X DELETE $QDRANT/collections/notes",
     "curl -H \"api-key: $QDRANT\" $QDRANT/collections/notes"),
    ("weaviate-cls-skip-delete", "Weaviate class delete missing api-key", "js_route",
     "curl -X DELETE $WV/v1/schema/Notes",
     "curl -H \"Authorization: Bearer $WV\" $WV/v1/schema/Notes"),
    ("lancedb-tbl-skip-delete", "LanceDB table drop missing uri auth", "js_route",
     "python -c 'import lancedb; lancedb.connect(\"notes\").drop_table(\"t\")'",
     "python -c 'import lancedb; lancedb.connect(\"notes\").open_table(\"t\")'"),
    ("ray-job-skip-delete", "Ray job stop missing dashboard token", "js_route",
     "ray job stop notes",
     "ray job status notes --address $RAY"),
    ("dask-sched-skip-delete", "Dask retire missing scheduler auth", "js_route",
     "curl -X POST $DASK/api/v1/retire",
     "curl $DASK/api/v1/info --header \"Authorization: $DASK\""),
    ("chroma-col-skip-delete", "Chroma collection delete missing token", "js_route",
     "curl -X DELETE $CHROMA/api/v1/collections/notes",
     "curl -H \"Authorization: Bearer $CHROMA\" $CHROMA/api/v1/collections/notes"),
]

assert len(BFLA) == 80, len(BFLA)
assert len({x[0] for x in BFLA}) == 80
assert not ({x[0] for x in BFLA} & USED_SLUGS), {x[0] for x in BFLA} & USED_SLUGS

TICKETS = [f"AZ{(i % 9) + 1}-{i + 1}" for i in range(80)]


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


header = '''"""Extra unique IDOR/BFLA plants for authz-regression-factory r1920+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r1919 vesselNNNN-sys.
Not clones of r1919 elia-elias / redpanda-acl, r1840 tepco-feeder / bitbucket-pipe.
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
print("wrote", OUT, "idor0", IDOR[0][0], "bfla0", BFLA[0][0])
