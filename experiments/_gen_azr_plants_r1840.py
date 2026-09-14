#!/usr/bin/env python3
"""Emit experiments/azr-plants-r1840.py — unique object-id IDOR / BFLA for r1840+."""
from __future__ import annotations

import re
from pathlib import Path

EXPERIMENTS = Path(__file__).resolve().parent
OUT = EXPERIMENTS / "azr-plants-r1840.py"

USED_SLUGS: set[str] = set()
USED_PLANTS: set[str] = set()
USED_LOOKUPS: set[str] = set()
USED_MODS: set[str] = set()
for p in list(EXPERIMENTS.glob("azr-plants*.py")) + list(EXPERIMENTS.glob("azr-mill*.py")):
    if p.name == "azr-plants-r1840.py":
        continue
    text = p.read_text(errors="ignore")
    USED_SLUGS.update(re.findall(r"slug=['\"]([a-z0-9-]+)['\"]", text))
    USED_PLANTS.update(re.findall(r"plant=['\"]([a-z0-9-]+)['\"]", text))
    USED_LOOKUPS.update(re.findall(r"lookup=['\"]([a-z0-9_]+)['\"]", text))
    USED_MODS.update(re.findall(r"mod=['\"]([a-z0-9_]+)['\"]", text))

PREFIX = [f"azp{i:02d}" for i in range(80)]
PLANTS = []
for pre in PREFIX:
    name = pre + "keel"
    assert name not in USED_PLANTS
    PLANTS.append(name)

FIRST = ["authn", "mask", "any_member", "list_scope"]
RESIDUAL = ["pdf", "export", "search", "mget", "csv", "admin", "webhook", "comments"]
LEFTOVER = ["put", "patch", "update"]

# 80 unique leftover object-id IDOR families (grid / payments / astro / telecom leftover)
IDOR = [
    ("tepco-feeder-idor", "TEPCO feeder object-id IDOR", "tepcofds", "Tepcofd", "tepcofd", "TEPCO-F-001", "grid_id", "tepco-fd", "feeder unique from TEPCO"),
    ("kepco-kr-idor", "KEPCO circuit object-id IDOR", "kepcokrs", "Kepcokr", "kepcokr", "KEPCO-C-001", "grid_id", "kepco-kr", "circuit unique from KEPCO"),
    ("sgcc-cn-idor", "SGCC feeder object-id IDOR", "sgcccns", "Sgcccn", "sgcccn", "SGCC-F-001", "grid_id", "sgcc-cn", "feeder unique from SGCC"),
    ("powergrid-in-idor", "POWERGRID ISTS object-id IDOR", "pgcils", "Pgcil", "pgcil", "ISTS-001", "grid_id", "pgcil-in", "ISTS unique from POWERGRID"),
    ("eskom-za-idor", "Eskom feeder object-id IDOR", "eskomzas", "Eskomza", "eskomza", "ESKOM-F-001", "grid_id", "eskom-za", "feeder unique from Eskom"),
    ("transpower-nz-idor", "Transpower GXP object-id IDOR", "tpnzs", "Tpnz", "tpnz", "GXP-OTA", "grid_id", "tpnz-gxp", "GXP unique from Transpower"),
    ("hydroquebec-idor", "Hydro-Quebec poste object-id IDOR", "hqcs", "Hqc", "hqc", "HQC-P-001", "grid_id", "hqc-poste", "poste unique from HQC"),
    ("aep-zone-idor", "AEP zone object-id IDOR", "aepzones", "Aepzone", "aepzone", "AEP-OH", "grid_id", "aep-zone", "zone unique from AEP"),
    ("duke-ba-idor", "Duke BA object-id IDOR", "dukebas", "Dukeba", "dukeba", "DUK", "grid_id", "duke-ba", "BA unique from Duke"),
    ("entergy-ba-idor", "Entergy BA object-id IDOR", "entergybas", "Entergyba", "entergyba", "EES", "grid_id", "entergy-ba", "BA unique from Entergy"),
    ("pix-emv-idor", "PIX EMV QR object-id IDOR", "pixemvs", "Pixemv", "pixemv", "00020126BR.GOV.BCB.PIX", "bank_id", "pix-emv", "EMV unique from BCB"),
    ("upi-mandate-idor", "UPI mandate object-id IDOR", "upimands", "Upimand", "upimand", "UMN-240115-1", "bank_id", "upi-mandate", "UMN unique from NPCI"),
    ("paynow-proxy-idor", "PayNow proxy object-id IDOR", "paynowpxs", "Paynowpx", "paynowpx", "PAYNOW-UEN-001", "bank_id", "paynow-proxy", "proxy unique from PayNow"),
    ("duitnow-proxy-idor", "DuitNow proxy object-id IDOR", "duitnowpxs", "Duitnowpx", "duitnowpx", "DN-PROXY-001", "bank_id", "duitnow-proxy", "proxy unique from PayNet"),
    ("promptpay-proxy-idor", "PromptPay proxy object-id IDOR", "ppproxys", "Ppproxy", "ppproxy", "PP-PROXY-001", "bank_id", "pp-proxy", "proxy unique from BOT"),
    ("sepa-sdd-idor", "SEPA SDD mandate object-id IDOR", "sepasdds", "Sepasdd", "sepasdd", "SDD-MNDT-001", "bank_id", "sepa-sdd", "mandate unique from EPC"),
    ("ach-trace-idor", "ACH trace object-id IDOR", "achtraces", "Achtrace", "achtrace", "021000021123456", "bank_id", "ach-trace", "trace unique from NACHA"),
    ("chips-seq2-idor", "CHIPS seq2 object-id IDOR", "chips2s", "Chips2", "chips2", "CHIPS2-240115-9", "bank_id", "chips-seq2", "seq unique from CHIPS"),
    ("fedwire-omad-idor", "Fedwire OMAD object-id IDOR", "fedomads", "Fedomad", "fedomad", "20240115B1QGT01C000001", "bank_id", "fedwire-omad", "OMAD unique from Fedwire"),
    ("target2-uetr-idor", "TARGET2 UETR twin object-id IDOR", "t2uetrs", "T2uetr", "t2uetr", "T2-UETR-240115-1", "bank_id", "t2-uetr", "id unique from TARGET2"),
    ("gsc1-idor", "GSC-I star object-id IDOR", "gsc1s", "Gsc1", "gsc1", "GSC 1234-5678", "lab_id", "gsc1-id", "GSC1 unique from STScI"),
    ("usnoa2-idor", "USNO-A2.0 object-id IDOR", "usnoa2s", "Usnoa2", "usnoa2", "1234-0567890", "lab_id", "usnoa2-id", "USNO-A2 unique from USNO"),
    ("act-j-idor", "ACT-J catalog object-id IDOR", "actjs", "Actj", "actj", "ACT J053514-052353", "lab_id", "act-j", "ACT unique from USNO"),
    ("ucac1-idor", "UCAC1 star object-id IDOR", "ucac1s", "Ucac1", "ucac1", "UCAC1 12345678", "lab_id", "ucac1-id", "UCAC1 unique from USNO"),
    ("tess-tic8-idor", "TESS TIC-8 object-id IDOR", "tic8s", "Tic8", "tic8", "TIC8 261136679", "lab_id", "tic8-id", "TIC-8 unique from MAST"),
    ("desi-ls-idor", "DESI Legacy object-id IDOR", "desils", "Desils", "desils", "LS-DR10 123456789", "lab_id", "desi-ls", "ls_id unique from DESI"),
    ("euclid-obj-idor", "Euclid object-id IDOR", "euclidobjs", "Euclidobj", "euclidobj", "EUCLID-J053514.9-052353", "lab_id", "euclid-obj", "source unique from Euclid"),
    ("roman-obj-idor", "Roman WFI object-id IDOR", "romanobjs", "Romanobj", "romanobj", "ROMAN-123456789", "lab_id", "roman-obj", "source unique from Roman"),
    ("jwst-obs-idor", "JWST observation object-id IDOR", "jwstobss", "Jwstobs", "jwstobs", "jwst_12345", "lab_id", "jwst-obs", "obsid unique from MAST"),
    ("hubble-obs-idor", "HST observation object-id IDOR", "hsts", "Hst", "hstobs", "hst_98765", "lab_id", "hst-obs", "obsid unique from MAST"),
    ("spitzer-obs-idor", "Spitzer AOR object-id IDOR", "spitzers", "Spitzer", "spitzer", "AORKEY-12345678", "lab_id", "spitzer-aor", "AOR unique from IRSA"),
    ("herschel-obs-idor", "Herschel obs object-id IDOR", "herschels", "Herschel", "herschel", "1342246243", "lab_id", "herschel-obs", "obsid unique from HSA"),
    ("fiveg-stmsi-idor", "5G S-TMSI object-id IDOR", "fivegstmsis", "Fivegstmsi", "fivegstmsi", "01-A1B2C3D4", "net_id", "5g-stmsi", "5G-S-TMSI unique from 3GPP"),
    ("ngksi-idor", "ngKSI object-id IDOR", "ngksis", "Ngksi", "ngksi", "nas-01", "net_id", "ngksi-5g", "ngKSI unique from 3GPP"),
    ("suci-hn-idor", "SUCI HN-ID object-id IDOR", "sucihns", "Sucihn", "sucihn", "suci-hn-310410", "net_id", "suci-hn", "HN-ID unique from 3GPP"),
    ("routingid-5g-idor", "5G Routing ID object-id IDOR", "rtid5gs", "Rtid5g", "rtid5g", "RID-310410-01", "net_id", "rtid-5g", "Routing ID unique from 3GPP"),
    ("nssf-set-idor", "NSSF set object-id IDOR", "nssfsets", "Nssfset", "nssfset", "NSSF-SET-1", "net_id", "nssf-set", "set unique from 3GPP"),
    ("amf-guami-idor", "GUAMI object-id IDOR", "guamis", "Guami", "guami", "310-410-01-2A", "net_id", "guami-5g", "GUAMI unique from 3GPP"),
    ("smf-set-idor", "SMF set object-id IDOR", "smfsets", "Smfset", "smfset", "SMF-SET-1", "net_id", "smf-set", "set unique from 3GPP"),
    ("upf-n4-idor", "UPF N4 SEID object-id IDOR", "upfn4s", "Upfn4", "upfn4", "SEID-001", "net_id", "upf-n4", "SEID unique from PFCP"),
    ("aep-hub-idor", "AEP hub object-id IDOR", "aephubs", "Aephub", "aephub", "AEP-DAYTON", "grid_id", "aep-hub", "hub unique from AEP"),
    ("cfe-mx-idor", "CFE control area object-id IDOR", "cfemxs", "Cfemx", "cfemx", "CFE-SIN", "grid_id", "cfe-mx", "area unique from CFE"),
    ("kpx-kr-idor", "KPX market object-id IDOR", "kpxkrs", "Kpxkr", "kpxkr", "KPX-SMP-001", "grid_id", "kpx-kr", "SMP unique from KPX"),
    ("occto-jp-idor", "OCCTO area object-id IDOR", "occtos", "Occto", "occto", "OCCTO-E-001", "grid_id", "occto-jp", "area unique from OCCTO"),
    ("aemo-fnn-idor", "AEMO FNN object-id IDOR", "aemofnns", "Aemofnn", "aemofnn", "FNN-001", "grid_id", "aemo-fnn", "FNN unique from AEMO"),
    ("nemmco-idor", "NEMMCO residual object-id IDOR", "nemmcos", "Nemmco", "nemmco", "NEMMCO-R-001", "grid_id", "nemmco-id", "id unique from NEMMCO"),
    ("ercot-dc-idor", "ERCOT DC-tie object-id IDOR", "ercotdcs", "Ercotdc", "ercotdc", "DC_RAILROAD", "grid_id", "ercot-dc", "DC-tie unique from ERCOT"),
    ("pjm-int-idor", "PJM interface object-id IDOR", "pjmints", "Pjmint", "pjmint", "WESTERN-INT", "grid_id", "pjm-int", "interface unique from PJM"),
    ("miso-int-idor", "MISO interface object-id IDOR", "misoints", "Misoint", "misoint", "MISO-PJM", "grid_id", "miso-int", "interface unique from MISO"),
    ("caiso-tie-idor", "CAISO intertie object-id IDOR", "caisoties", "Caisotie", "caisotie", "MALIN500", "grid_id", "caiso-tie", "intertie unique from CAISO"),
    ("gaia-dr2-idor", "Gaia DR2 source object-id IDOR", "gaiadr2s", "Gaiadr2", "gaiadr2", "Gaia DR2 1234567890123456789", "lab_id", "gaia-dr2", "source_id unique from Gaia DR2"),
    ("wise-allsky-idor", "WISE All-Sky object-id IDOR", "wisealls", "Wiseall", "wiseall", "WISE J053514.94-052353.9", "lab_id", "wise-allsky", "source unique from All-Sky"),
    ("2mass-psc-idor", "2MASS PSC object-id IDOR", "twomasspscs", "Twomasspsc", "twomasspsc", "05351494-0523539", "lab_id", "twomass-psc", "PSC unique from IPAC"),
    ("sdss-spec-idor", "SDSS specObjID object-id IDOR", "sdssspecs", "Sdssspec", "sdssspec", "1237654382514995201", "lab_id", "sdss-spec", "specObjID unique from SDSS"),
    ("panstarrs-k2-idor", "Pan-STARRS K2 object-id IDOR", "ps1k2s", "Ps1k2", "ps1k2", "PSO K2 J053.13-05.42", "lab_id", "ps1-k2", "objID unique from PS1 K2"),
    ("ztf-alert-idor", "ZTF alert candid object-id IDOR", "ztfalerts", "Ztfalert", "ztfalert", "1234567890123456789", "lab_id", "ztf-alert", "candid unique from ZTF"),
    ("asassn-sn-idor", "ASAS-SN SN object-id IDOR", "asassnsns", "Asassnsn", "asassnsn", "ASASSN-24xx", "lab_id", "asassn-sn", "SN unique from ASAS-SN"),
    ("ogle-iv-idor", "OGLE-IV object-id IDOR", "ogleivs", "Ogleiv", "ogleiv", "OGLE-IV-BLG-0001", "lab_id", "ogle-iv", "id unique from OGLE-IV"),
    ("moa-alert-idor", "MOA alert object-id IDOR", "moaalerts", "Moaalert", "moaalert", "MOA-2024-BLG-001", "lab_id", "moa-alert", "alert unique from MOA"),
    ("gaia-alerts-idor", "Gaia Alerts object-id IDOR", "gaiaalerts", "Gaiaalert", "gaiaalert", "Gaia24aaa", "lab_id", "gaia-alert", "name unique from Gaia Alerts"),
    ("chaps-seq2-idor", "CHAPS seq2 object-id IDOR", "chaps2s", "Chaps2", "chaps2", "CHAPS2-240115-9", "bank_id", "chaps-seq2", "seq unique from CHAPS"),
    ("bacs-sun-idor", "Bacs SUN object-id IDOR", "bacssuns", "Bacssun", "bacssun", "SUN-123456", "bank_id", "bacs-sun", "SUN unique from Bacs"),
    ("fps-fpsid-idor", "FPS FPSID object-id IDOR", "fpsids", "Fpsid", "fpsid", "FPSID-240115-9", "bank_id", "fps-id", "FPSID unique from Pay.UK"),
    ("sepa-r-idor", "SEPA R-transaction object-id IDOR", "separs", "Separ", "separ", "RTRN-240115-1", "bank_id", "sepa-r", "R-id unique from EPC"),
    ("tips-uetr-idor", "TIPS UETR twin object-id IDOR", "tipsuetrs", "Tipsuetr", "tipsuetr", "TIPS-UETR-240115-1", "bank_id", "tips-uetr", "id unique from TIPS"),
    ("lynx-msg-idor", "Lynx message object-id IDOR", "lynxmsgs", "Lynxmsg", "lynxmsg", "LYNX-MSG-240115-1", "bank_id", "lynx-msg", "msgid unique from Lynx"),
    ("hvcs-chats-idor", "HK CHATS object-id IDOR", "hvatschs", "Hvchats", "hvchats", "CHATS-240115-1", "bank_id", "hvcs-chats", "id unique from HKICL"),
    ("meps-fast-idor", "MEPS+ FAST object-id IDOR", "mepsfasts", "Mepsfast", "mepsfast", "FAST-SG-001", "bank_id", "meps-fast", "id unique from MAS"),
    ("rits-zengin-idor", "Zengin object-id IDOR", "zengins", "Zengin", "zengin", "ZENGIN-240115-1", "bank_id", "zengin-jp", "id unique from Zengin"),
    ("cips-msg-idor", "CIPS MsgId object-id IDOR", "cipsmsgs", "Cipsmsg", "cipsmsg", "CIPS-MSG-240115-1", "bank_id", "cips-msg", "MsgId unique from CIPS"),
    ("ngeso-bmu-idor", "NGESO BMU object-id IDOR", "ngesobmus", "Ngesobmu", "ngesobmu", "T_ABTH7", "grid_id", "ngeso-bmu", "BMU unique from NGESO"),
    ("rte-pdia-idor", "RTE PDIA object-id IDOR", "rtepdias", "Rtepdia", "rtepdia", "PDIA-001", "grid_id", "rte-pdia", "PDIA unique from RTE"),
    ("tennet-eancode-idor", "TenneT EAN object-id IDOR", "tnteans", "Tntean", "tntean", "871687940001234567", "grid_id", "tennet-ean", "EAN unique from TenneT"),
    ("fiftyhz-uz-idor", "50Hertz UZ object-id IDOR", "fiftyuzs", "Fiftyuz", "fiftyuz", "UZ-001", "grid_id", "fiftyhz-uz", "UZ unique from 50Hertz"),
    ("amprion-kz-idor", "Amprion KZ object-id IDOR", "ampkzs", "Ampkz", "ampkz", "KZ-001", "grid_id", "amprion-kz", "KZ unique from Amprion"),
    ("tnbw-uz-idor", "TransnetBW UZ object-id IDOR", "tnbwuzs", "Tnbwuz", "tnbwuz", "TNBW-UZ-001", "grid_id", "tnbw-uz", "UZ unique from TransnetBW"),
    ("ree-up-idor", "REE UP object-id IDOR", "reeups", "Reeup", "reeup", "UP-001", "grid_id", "ree-up", "UP unique from REE"),
    ("terna-up-idor", "Terna UP object-id IDOR", "ternaups", "Ternaup", "ternaup", "UP-IT-001", "grid_id", "terna-up", "UP unique from Terna"),
    ("ren-up-idor", "REN UP object-id IDOR", "renups", "Renup", "renup", "UP-PT-001", "grid_id", "ren-up", "UP unique from REN"),
    ("elia-elias-idor", "Elia ELIA-S object-id IDOR", "eliaels", "Eliael", "eliael", "ELIAS-001", "grid_id", "elia-s", "id unique from Elia"),
]

assert len(IDOR) == 80, len(IDOR)
assert len({x[0] for x in IDOR}) == 80
assert len({x[2] for x in IDOR}) == 80
assert len({x[4] for x in IDOR}) == 80
assert not ({x[0] for x in IDOR} & USED_SLUGS), {x[0] for x in IDOR} & USED_SLUGS
assert not ({x[4] for x in IDOR} & USED_LOOKUPS), {x[4] for x in IDOR} & USED_LOOKUPS
assert not ({x[2] for x in IDOR} & USED_MODS), {x[2] for x in IDOR} & USED_MODS

BFLA = [
    ("bitbucket-pipe-skip-delete", "Bitbucket Pipelines delete missing token", "js_route",
     "curl -X DELETE $BB/pipelines/$id",
     "curl -u $BB_USER:$BB_APP_PASSWORD $BB/pipelines/$id"),
    ("azure-devops-skip-delete", "Azure DevOps build delete missing PAT", "js_route",
     "az pipelines build delete --id $id --yes",
     "az pipelines build show --id $id"),
    ("teamcity-skip-delete", "TeamCity build delete missing token", "js_route",
     "curl -X POST $TC/app/rest/builds/id:$id --request DELETE",
     "curl -H \"Authorization: Bearer $TC\" $TC/app/rest/builds/id:$id"),
    ("bamboo-skip-delete", "Bamboo plan delete missing token", "js_route",
     "curl -X DELETE $BAMBOO/rest/api/latest/plan/NOTES",
     "curl -u user:token $BAMBOO/rest/api/latest/plan/NOTES"),
    ("octopus-skip-delete", "Octopus release delete missing api-key", "js_route",
     "octo delete-release --project notes --version 1.0.0",
     "octo list-releases --project notes --apiKey $OCTO"),
    ("argo-wf-skip-delete", "Argo Workflows delete missing SA", "js_route",
     "argo delete notes",
     "argo get notes --kubeconfig $KUBECONFIG"),
    ("knative-skip-delete", "Knative service delete missing auth", "js_route",
     "kn service delete notes",
     "kn service describe notes"),
    ("prometheus-skip-delete", "Prometheus admin delete-series missing --web.enable-admin-api", "js_route",
     "curl -X POST $PROM/api/v1/admin/tsdb/delete_series?match[]=notes",
     "curl $PROM/api/v1/query?query=notes"),
    ("grafana-skip-delete", "Grafana dashboard delete missing API key", "js_route",
     "curl -X DELETE $GRAFANA/api/dashboards/uid/notes",
     "curl -H \"Authorization: Bearer $GF\" $GRAFANA/api/dashboards/uid/notes"),
    ("loki-skip-delete", "Loki delete missing auth", "js_route",
     "curl -X POST $LOKI/loki/api/v1/delete?query={app=notes}",
     "curl $LOKI/loki/api/v1/query?query={app=notes}"),
    ("tempo-skip-delete", "Tempo delete missing backend auth", "js_route",
     "curl -X DELETE $TEMPO/api/traces/notes",
     "curl $TEMPO/api/traces/notes"),
    ("jaeger-skip-delete", "Jaeger delete missing admin", "js_route",
     "curl -X DELETE $JAEGER/api/traces/notes",
     "curl $JAEGER/api/traces/notes"),
    ("zipkin-skip-delete", "Zipkin delete missing auth", "js_route",
     "curl -X DELETE $ZIPKIN/api/v2/traces/notes",
     "curl $ZIPKIN/api/v2/trace/notes"),
    ("otelcol-skip-delete", "OTel collector delete missing extension auth", "js_route",
     "curl -X DELETE $OTEL/v1/traces",
     "curl $OTEL/v1/traces"),
    ("clickhouse-skip-delete", "ClickHouse DROP missing user", "sql",
     "DROP TABLE notes",
     "SELECT * FROM notes  -- user app"),
    ("druid-skip-delete", "Druid drop datasource missing auth", "js_route",
     "curl -X DELETE $DRUID/druid/coordinator/v1/datasources/notes",
     "curl $DRUID/druid/coordinator/v1/datasources/notes"),
    ("pinot-skip-delete", "Pinot table delete missing controller auth", "js_route",
     "curl -X DELETE $PINOT/tables/notes",
     "curl $PINOT/tables/notes"),
    ("kylin-skip-delete", "Kylin cube drop missing auth", "js_route",
     "curl -X DELETE $KYLIN/kylin/api/cubes/notes",
     "curl -u ADMIN:KYLIN $KYLIN/kylin/api/cubes/notes"),
    ("trino-skip-delete", "Trino DROP TABLE missing access-control", "sql",
     "DROP TABLE notes.t",
     "SHOW TABLES FROM notes"),
    ("presto-skip-delete", "Presto DROP TABLE missing access-control", "sql",
     "DROP TABLE notes.t",
     "SHOW TABLES FROM notes"),
    ("hive-skip-delete", "Hive DROP TABLE missing doAs", "sql",
     "DROP TABLE notes",
     "SHOW TABLES  -- hive.server2.enable.doAs"),
    ("impala-skip-delete", "Impala DROP TABLE missing sentry", "sql",
     "DROP TABLE notes",
     "SHOW TABLES IN notes"),
    ("flink-skip-delete", "Flink cancel missing REST auth", "js_route",
     "curl -X PATCH $FLINK/jobs/notes?mode=cancel",
     "curl $FLINK/jobs/notes"),
    ("beam-skip-delete", "Beam Dataflow job cancel missing adc", "js_route",
     "gcloud dataflow jobs cancel notes",
     "gcloud dataflow jobs describe notes"),
    ("storm-skip-delete", "Storm kill missing nimbus auth", "js_route",
     "storm kill notes",
     "storm list"),
    ("heron-skip-delete", "Heron kill missing state mgr", "js_route",
     "heron kill notes",
     "heron get notes"),
    ("spark-k8s-skip-delete", "Spark on K8s delete missing rbac", "js_route",
     "kubectl delete sparkapplication notes",
     "kubectl get sparkapplication notes"),
    ("airbyte-skip-delete", "Airbyte connection delete missing token", "js_route",
     "curl -X POST $AB/api/v1/connections/delete -d {connectionId:notes}",
     "curl $AB/api/v1/connections/get -d {connectionId:notes}"),
    ("fivetran-skip-delete", "Fivetran connector delete missing key", "js_route",
     "curl -X DELETE $FT/v1/connectors/notes",
     "curl -u $FT_KEY:$FT_SECRET $FT/v1/connectors/notes"),
    ("stitch-skip-delete", "Stitch source delete missing token", "js_route",
     "curl -X DELETE $STITCH/v4/sources/notes",
     "curl -H \"Authorization: Bearer $ST\" $STITCH/v4/sources/notes"),
    ("meltano-skip-delete", "Meltano tap delete missing dotenv", "js_route",
     "meltano remove extractor notes",
     "meltano invoke tap-notes"),
    ("singer-skip-delete", "Singer target delete missing config", "js_route",
     "rm ~/.singer/notes.json",
     "tap-notes -c config.json"),
    ("dbt-cloud-skip-delete", "dbt Cloud job delete missing token", "js_route",
     "curl -X DELETE $DBT/v2/accounts/1/jobs/notes",
     "curl -H \"Authorization: Bearer $DBT\" $DBT/v2/accounts/1/jobs/notes"),
    ("looker-skip-delete", "Looker look delete missing client", "js_route",
     "curl -X DELETE $LOOKER/api/4.0/looks/notes",
     "curl -H \"Authorization: Bearer $LK\" $LOOKER/api/4.0/looks/notes"),
    ("metabase-skip-delete", "Metabase card delete missing session", "js_route",
     "curl -X DELETE $MB/api/card/notes",
     "curl -H \"X-Metabase-Session: $MB\" $MB/api/card/notes"),
    ("superset-skip-delete", "Superset chart delete missing csrf", "js_route",
     "curl -X DELETE $SS/api/v1/chart/notes",
     "curl $SS/api/v1/chart/notes -H \"Authorization: Bearer $SS\""),
    ("redash-skip-delete", "Redash query delete missing key", "js_route",
     "curl -X DELETE $RD/api/queries/notes",
     "curl $RD/api/queries/notes?api_key=$RD"),
    ("mode-skip-delete", "Mode report delete missing token", "js_route",
     "curl -X DELETE $MODE/api/notes/reports/r",
     "curl -u $MODE_TOKEN: $MODE/api/notes/reports/r"),
    ("hex-skip-delete", "Hex project delete missing token", "js_route",
     "curl -X DELETE $HEX/api/v1/projects/notes",
     "curl -H \"Authorization: Bearer $HEX\" $HEX/api/v1/projects/notes"),
    ("observable-skip-delete", "Observable notebook delete missing token", "js_route",
     "curl -X DELETE $OBS/api/v1/documents/notes",
     "curl -H \"Authorization: Bearer $OBS\" $OBS/api/v1/documents/notes"),
    ("streamlit-skip-delete", "Streamlit Cloud app delete missing token", "js_route",
     "curl -X DELETE $ST/api/v1/apps/notes",
     "curl -H \"Authorization: Bearer $ST\" $ST/api/v1/apps/notes"),
    ("gradio-skip-delete", "Gradio Space delete missing hf token", "js_route",
     "huggingface-cli repo delete notes --yes",
     "huggingface-cli repo info notes --token $HF"),
    ("mlflow-skip-delete", "MLflow run delete missing tracking token", "js_route",
     "mlflow gc --run-ids notes --backend-store-uri $MLFLOW",
     "mlflow runs describe -r notes"),
    ("wandb-skip-delete", "W&B run delete missing api-key", "js_route",
     "wandb artifact del notes --yes",
     "wandb pull notes --api-key $WANDB"),
    ("neptune-skip-delete", "Neptune run delete missing token", "js_route",
     "neptune del notes",
     "neptune fetch notes --api-token $NEPTUNE"),
    ("clearml-skip-delete", "ClearML task delete missing creds", "js_route",
     "clearml-data delete --id notes --force",
     "clearml-data list"),
    ("dvc-skip-delete", "DVC gc missing remote creds", "js_route",
     "dvc gc -w --force",
     "dvc status -c --remote notes"),
    ("lakefs-gc-skip-delete", "lakeFS gc missing access key", "js_route",
     "lakectl gc run lakefs://notes",
     "lakectl repo list"),
    ("delta-log-skip-delete", "Delta log vacuum missing catalog auth", "sql",
     "VACUUM notes RETAIN 0 HOURS",
     "DESCRIBE HISTORY notes"),
    ("iceberg-expire-skip-delete", "Iceberg expire_snapshots missing catalog", "sql",
     "CALL system.expire_snapshots('notes.t')",
     "SELECT * FROM notes.t.snapshots"),
    ("hudi-clean-skip-delete", "Hudi cleaner missing hoodie.meta", "js_route",
     "spark.sql(\"call run_clean('notes')\")",
     "spark.sql('show tblproperties notes')"),
    ("nifi-pg-skip-delete", "NiFi PG purge missing proxied-entity", "js_route",
     "curl -X DELETE $NIFI/flow/process-groups/notes/empty-all-connections-requests",
     "curl -H 'X-ProxiedEntitiesChain: notes' $NIFI/flow/process-groups/notes"),
    ("airflow-pool-skip-delete", "Airflow pool delete missing auth", "js_route",
     "airflow pools delete notes",
     "airflow pools get notes"),
    ("dagster-wipe-skip-delete", "Dagster instance wipe missing token", "js_route",
     "dagster instance wipe --yes",
     "dagster instance info"),
    ("prefect-block-skip-delete", "Prefect block delete missing api-key", "js_route",
     "prefect block delete notes/n",
     "prefect block inspect notes/n"),
    ("luigi-rm-skip-delete", "Luigi remove missing scheduler auth", "js_route",
     "curl -X POST $LUIGI/api/remove --data task=notes2",
     "curl $LUIGI/api/graph"),
    ("kedro-rm-skip-delete", "Kedro pipeline delete missing credentials", "js_route",
     "kedro pipeline delete notes",
     "kedro pipeline list"),
    ("dbt-clean-skip-delete", "dbt clean missing profile", "js_route",
     "dbt clean --no-clean-project-files-only",
     "dbt ls --profiles-dir $HOME/.dbt"),
    ("spark-ui-skip-delete", "Spark UI kill missing acl", "js_route",
     "curl -X POST $SPARK/jobs/job/kill/?id=notes",
     "curl $SPARK/api/v1/applications"),
    ("yarn-skip-delete", "YARN app kill missing kerberos", "js_route",
     "yarn application -kill notes",
     "yarn application -status notes"),
    ("mesos-skip-delete", "Mesos teardown missing principal", "js_route",
     "curl -X POST $MESOS/teardown -d frameworkId=notes",
     "curl $MESOS/frameworks"),
    ("nomad-job-skip-delete", "Nomad job stop missing token", "js_route",
     "nomad job stop -purge notes",
     "nomad job status notes"),
    ("consul-kv-skip-delete", "Consul KV delete missing ACL", "js_route",
     "consul kv delete notes/",
     "consul kv get notes/ -token $CONSUL_HTTP_TOKEN"),
    ("etcd-lease-skip-delete", "etcd lease revoke missing user", "js_route",
     "etcdctl lease revoke 1",
     "etcdctl lease timetolive 1 --user root"),
    ("zookeeper-skip-delete", "ZooKeeper delete missing SASL", "js_route",
     "zkCli.sh delete /notes",
     "zkCli.sh get /notes"),
    ("bookkeeper-skip-delete", "BookKeeper delete ledger missing auth", "js_route",
     "bookkeeper shell deleteledger -ledgerid 1",
     "bookkeeper shell listledgers"),
    ("pulsar-ns-skip-delete", "Pulsar namespace delete missing token", "js_route",
     "pulsar-admin namespaces delete p/n",
     "pulsar-admin --auth-plugin token namespaces list p"),
    ("rabbit-vhost-skip-delete", "RabbitMQ vhost delete missing mgmt auth", "js_route",
     "rabbitmqctl delete_vhost notes",
     "rabbitmqctl list_vhosts"),
    ("kafka-topic-skip-delete", "Kafka topic delete missing ACL", "js_route",
     "kafka-topics.sh --delete --topic notes --bootstrap-server $K",
     "kafka-acls.sh --list --topic notes"),
    ("redpanda-ns-skip-delete", "Redpanda namespace delete missing SASL", "js_route",
     "rpk cluster partitions delete notes",
     "rpk topic list -X sasl.mechanism=SCRAM-SHA-256"),
    ("nats-account-skip-delete", "NATS account delete missing operator jwt", "js_route",
     "nsc delete account notes",
     "nsc describe account notes"),
    ("emqx-user-skip-delete", "EMQX user delete missing dashboard", "js_route",
     "curl -X DELETE $EMQX/api/v5/authentication/users/notes",
     "curl -H \"Authorization: Bearer $EM\" $EMQX/api/v5/authentication/users/notes"),
    ("mosquitto-acl-skip-delete", "Mosquitto ACL delete missing password_file", "js_route",
     "mosquitto_passwd -D /etc/mosquitto/passwd notes",
     "mosquitto_passwd -U /etc/mosquitto/passwd"),
    ("vernemq-user-skip-delete", "VerneMQ user delete missing acl", "js_route",
     "vmq-admin user delete username=notes",
     "vmq-admin user show"),
    ("emqx-rule-skip-delete", "EMQX rule delete missing dashboard token", "js_route",
     "curl -X DELETE $EMQX/api/v5/rules/notes",
     "curl -H \"Authorization: Bearer $EM\" $EMQX/api/v5/rules/notes"),
    ("rabbit-policy-skip-delete", "RabbitMQ policy delete missing mgmt", "js_route",
     "rabbitmqctl clear_policy notes",
     "rabbitmqctl list_policies"),
    ("kafka-cg-skip-delete", "Kafka consumer-group delete missing ACL", "js_route",
     "kafka-consumer-groups.sh --delete --group notes --bootstrap-server $K",
     "kafka-acls.sh --list --group notes"),
    ("nats-stream-skip-delete", "NATS stream delete missing operator jwt", "js_route",
     "nats stream rm NOTES -f",
     "nats stream info NOTES"),
    ("pulsar-sub-skip-delete", "Pulsar subscription delete missing token", "js_route",
     "pulsar-admin topics unsubscribe persistent://p/n/notes -s s",
     "pulsar-admin --auth-plugin token topics subscriptions persistent://p/n/notes"),
    ("redpanda-acl-skip-delete", "Redpanda ACL delete missing SASL", "js_route",
     "rpk acl delete --allow-principal User:notes --operation all --topic notes",
     "rpk acl list -X sasl.mechanism=SCRAM-SHA-256"),
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


header = '''"""Extra unique IDOR/BFLA plants for authz-regression-factory r1840+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r1839 vesselNNNN-sys.
Not clones of r1759 ztf-oid / redpanda-admin, r1760 aemo-nem / kuma.
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
