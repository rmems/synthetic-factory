#!/usr/bin/env python3
"""Emit experiments/azr-plants-r2240.py — unique object-id IDOR / BFLA for r2240+."""
from __future__ import annotations

import re
from pathlib import Path

EXPERIMENTS = Path(__file__).resolve().parent
OUT = EXPERIMENTS / "azr-plants-r2240.py"

USED_SLUGS: set[str] = set()
USED_PLANTS: set[str] = set()
USED_LOOKUPS: set[str] = set()
USED_MODS: set[str] = set()
for p in list(EXPERIMENTS.glob("azr-plants*.py")) + list(EXPERIMENTS.glob("azr-mill*.py")):
    if p.name == "azr-plants-r2240.py":
        continue
    text = p.read_text(errors="ignore")
    USED_SLUGS.update(re.findall(r"slug=['\"]([a-z0-9-]+)['\"]", text))
    USED_PLANTS.update(re.findall(r"plant=['\"]([a-z0-9-]+)['\"]", text))
    USED_LOOKUPS.update(re.findall(r"lookup=['\"]([a-z0-9_]+)['\"]", text))
    USED_MODS.update(re.findall(r"mod=['\"]([a-z0-9_]+)['\"]", text))

PREFIX = [f"azv{i:02d}" for i in range(80)]
PLANTS = []
for pre in PREFIX:
    name = pre + "yard"
    assert name not in USED_PLANTS, name
    PLANTS.append(name)

FIRST = ["authn", "mask", "any_member", "list_scope"]
RESIDUAL = ["pdf", "export", "search", "mget", "csv", "admin", "webhook", "comments"]
LEFTOVER = ["put", "patch", "update"]


def names(slug: str) -> tuple[str, str, str]:
    core = slug.replace("-idor", "").replace("-skip-delete", "").replace("-", "")
    core = (core + "x" * 8)[:10]
    mod = core + "s82"
    lookup = core + "l82"
    model = core[:1].upper() + core[1:] + "N"
    assert mod not in USED_MODS, mod
    assert lookup not in USED_LOOKUPS, lookup
    return mod, model, lookup


IDOR_SRC = [
    ("iccid-19-idor", "ICCID-19 object-id IDOR", "89014103211118510720", "lab_id", "iccid-19", "ICCID unique from ITU"),
    ("imeisv-idor", "IMEI-SV object-id IDOR", "3598270612345671", "mmsi_id", "imeisv", "SV unique from 3GPP"),
    ("meidhex-idor", "MEID hex object-id IDOR", "A0000004B0F3D1", "mmsi_id", "meidhex", "MEID unique from TIA"),
    ("eui64-mac-idor", "EUI-64 object-id IDOR", "021122FFFE334455", "lab_id", "eui64-mac", "EUI unique from IEEE"),
    ("macoui-idor", "MAC OUI object-id IDOR", "00:1A:2B", "lab_id", "macoui", "OUI unique from IEEE"),
    ("ulid26-idor", "ULID object-id IDOR", "01ARZ3NDEKTSV4RRFFQ69G5FAV", "lab_id", "ulid26", "ULID unique from ULID"),
    ("ksuid-idor", "KSUID object-id IDOR", "0ujtsYcgvSTl8PAuAdqWYSMnLOv", "lab_id", "ksuid", "KSUID unique from Segment"),
    ("snowflake-idor", "Snowflake id object-id IDOR", "1541815603606036480", "lab_id", "snowflake", "id unique from Twitter"),
    ("xid20-idor", "XID object-id IDOR", "9m4e2mr0ui3e8a215n4g", "lab_id", "xid20", "XID unique from rs"),
    ("cuid2-idor", "CUID2 object-id IDOR", "tz4a98xxat96iws9zmbrgj3a", "lab_id", "cuid2", "CUID unique from paralleldrive"),
    ("nanoid-idor", "NanoID object-id IDOR", "V1StGXR8_Z5jdHi6B-myT", "lab_id", "nanoid", "id unique from ai"),
    ("uuidv7-idor", "UUIDv7 object-id IDOR", "018f1e3c-7b4a-7c00-8d1e-2f3a4b5c6d7e", "lab_id", "uuidv7", "UUID unique from IETF"),
    ("typeid-idor", "TypeID object-id IDOR", "user_01h45ytscbebyvny4snc7gww3y", "lab_id", "typeid", "TypeID unique from jetify"),
    ("sqid-idor", "Sqid object-id IDOR", "86Rf07xd4z", "lab_id", "sqid", "Sqid unique from sqids"),
    ("hashid-idor", "Hashid object-id IDOR", "jR", "lab_id", "hashid", "Hashid unique from hashids"),
    ("btc-p2pkh-idor", "BTC P2PKH object-id IDOR", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "bank_id", "btc-p2pkh", "P2PKH unique from Bitcoin"),
    ("eth-ea-idor", "ETH EOA object-id IDOR", "0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe", "bank_id", "eth-ea", "EOA unique from Ethereum"),
    ("ens-node-idor", "ENS node object-id IDOR", "vitalik.eth", "bank_id", "ens-node", "node unique from ENS"),
    ("sol-base58-idor", "Solana base58 object-id IDOR", "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU", "bank_id", "sol-base58", "addr unique from Solana"),
    ("bech32m-idor", "Bech32m object-id IDOR", "bc1p5d7rjq7g6rdk2yhzks9smlaqtedr4dekq08ge8", "bank_id", "bech32m", "addr unique from BIP350"),
    ("txid256-idor", "Txid-256 object-id IDOR", "4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b", "bank_id", "txid256", "txid unique from Bitcoin"),
    ("evm-ca-idor", "EVM contract object-id IDOR", "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "bank_id", "evm-ca", "CA unique from Ethereum"),
    ("near-acct-idor", "NEAR account object-id IDOR", "alice.near", "bank_id", "near-acct", "acct unique from NEAR"),
    ("atom-bech-idor", "Cosmos bech32 object-id IDOR", "cosmos1qypqxpq9qcrsszg2pvxq6rs0zqg3yyc5z5tp7z", "bank_id", "atom-bech", "addr unique from Cosmos"),
    ("dot-ss58-idor", "Polkadot SS58 object-id IDOR", "15oF4uVJwmo4TdGW7VfQxSTvjLvoS9dZtN", "bank_id", "dot-ss58", "SS58 unique from Polkadot"),
    ("vin-wmi-idor", "VIN WMI object-id IDOR", "1HG", "trade_id", "vin-wmi", "WMI unique from ISO"),
    ("vin17-idor", "VIN-17 object-id IDOR", "1HGCM82633A004352", "trade_id", "vin17", "VIN unique from ISO"),
    ("uspto-pn-idor", "USPTO patent object-id IDOR", "11234567", "lab_id", "uspto-pn", "PN unique from USPTO"),
    ("epodoc-idor", "EPODOC object-id IDOR", "EP1000000A1", "lab_id", "epodoc", "doc unique from EPO"),
    ("cpc-sym-idor", "CPC symbol object-id IDOR", "G06F21/62", "lab_id", "cpc-sym", "CPC unique from EPO"),
    ("ipc-sym-idor", "IPC symbol object-id IDOR", "H04L9/32", "lab_id", "ipc-sym", "IPC unique from WIPO"),
    ("isrc-idor", "ISRC object-id IDOR", "USRC17607839", "lab_id", "isrc", "ISRC unique from IFPI"),
    ("iswc-idor", "ISWC object-id IDOR", "T-034.524.680-1", "lab_id", "iswc", "ISWC unique from CISAC"),
    ("isan-idor", "ISAN object-id IDOR", "0000-0000-3A8D-0000-Q-0000-0000-E", "lab_id", "isan", "ISAN unique from ISAN"),
    ("rfc-num-idor", "RFC number object-id IDOR", "9110", "lab_id", "rfc-num", "RFC unique from IETF"),
    ("cve-y-idor", "CVE-Y object-id IDOR", "CVE-2024-3094", "lab_id", "cve-y", "CVE unique from MITRE"),
    ("cwe-id-idor", "CWE id object-id IDOR", "CWE-639", "lab_id", "cwe-id", "CWE unique from MITRE"),
    ("cpe23-idor", "CPE 2.3 object-id IDOR", "cpe:2.3:a:openssl:openssl:3.0.0", "lab_id", "cpe23", "CPE unique from NIST"),
    ("ski-x509-idor", "X.509 SKI object-id IDOR", "1a:2b:3c:4d:5e", "lab_id", "ski-x509", "SKI unique from RFC5280"),
    ("x509-sn-idor", "X.509 serial object-id IDOR", "0x1a2b3c4d", "lab_id", "x509-sn", "serial unique from RFC5280"),
    ("ocsp-cid-idor", "OCSP certid object-id IDOR", "sha1:deadbeef", "lab_id", "ocsp-cid", "certid unique from RFC6960"),
    ("spki-pin-idor", "SPKI pin object-id IDOR", "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=", "lab_id", "spki-pin", "pin unique from RFC7469"),
    ("aki-x509-idor", "X.509 AKI object-id IDOR", "keyid:1a2b3c", "lab_id", "aki-x509", "AKI unique from RFC5280"),
    ("dnskey-idor", "DNSKEY tag object-id IDOR", "2371", "lab_id", "dnskey", "tag unique from RFC4034"),
    ("dsrr-idor", "DS RR object-id IDOR", "2371 13 2 AABBCC", "lab_id", "dsrr", "DS unique from RFC4034"),
    ("nsec3-idor", "NSEC3 hash object-id IDOR", "1a2b3c4d", "lab_id", "nsec3", "hash unique from RFC5155"),
    ("epp-roid-idor", "EPP ROID object-id IDOR", "EXAMPLE-REP", "lab_id", "epp-roid", "ROID unique from RFC5730"),
    ("iana-pen-idor", "IANA PEN object-id IDOR", "343", "lab_id", "iana-pen", "PEN unique from IANA"),
    ("cospar-idor", "COSPAR id object-id IDOR", "1998-067A", "lab_id", "cospar", "id unique from COSPAR"),
    ("satnogs-idor", "SatNOGS object-id IDOR", "25544", "lab_id", "satnogs", "id unique from SatNOGS"),
    ("tle-sat-idor", "TLE satnum object-id IDOR", "25544", "lab_id", "tle-sat", "satnum unique from Celestrak"),
    ("nssdc-idor", "NSSDC id object-id IDOR", "1998-067A", "lab_id", "nssdc", "id unique from NASA"),
    ("uic-crs-idor", "UIC CRS object-id IDOR", "8503000", "geo_id", "uic-crs", "CRS unique from UIC"),
    ("rsrid-idor", "RSRID object-id IDOR", "12345", "geo_id", "rsrid", "id unique from Network Rail"),
    ("aar-mark-idor", "AAR mark object-id IDOR", "UP", "geo_id", "aar-mark", "mark unique from AAR"),
    ("uic-loc-idor", "UIC location object-id IDOR", "008500300", "geo_id", "uic-loc", "loc unique from UIC"),
    ("naptan-idor", "NaPTAN object-id IDOR", "490000077E", "geo_id", "naptan", "stop unique from DFT"),
    ("npi10-idor", "NPI-10 object-id IDOR", "1234567893", "lab_id", "npi10", "NPI unique from CMS"),
    ("ein-irs-idor", "EIN IRS object-id IDOR", "12-3456789", "bank_id", "ein-irs", "EIN unique from IRS"),
    ("naics-idor", "NAICS object-id IDOR", "541511", "bank_id", "naics", "NAICS unique from Census"),
    ("iso6523-idor", "ISO 6523 ICD object-id IDOR", "0060", "bank_id", "iso6523", "ICD unique from ISO"),
    ("lei-elf-idor", "LEI ELF object-id IDOR", "8888", "bank_id", "lei-elf", "ELF unique from GLEIF"),
    ("gln-sgln-idor", "SGLN object-id IDOR", "0614141.12345.0", "trade_id", "gln-sgln", "SGLN unique from GS1"),
    ("plu4-idor", "PLU-4 object-id IDOR", "4011", "trade_id", "plu4", "PLU unique from IFPS"),
    ("fao-crop-idor", "FAO crop object-id IDOR", "15", "trade_id", "fao-crop", "crop unique from FAO"),
    ("usda-fgis-idor", "USDA FGIS object-id IDOR", "12345", "trade_id", "usda-fgis", "id unique from USDA"),
    ("codex-idor", "Codex GSFA object-id IDOR", "INS-330", "trade_id", "codex", "INS unique from Codex"),
    ("naic-co-idor", "NAIC company object-id IDOR", "12345", "bank_id", "naic-co", "co unique from NAIC"),
    ("swift-fin-idor", "SWIFT FIN object-id IDOR", "FIN-103", "bank_id", "swift-fin", "FIN unique from SWIFT"),
    ("mic-iso-idor", "ISO 10383 MIC object-id IDOR", "XNYS", "bank_id", "mic-iso", "MIC unique from ISO"),
    ("isin-idor", "ISIN object-id IDOR", "US0378331005", "bank_id", "isin", "ISIN unique from ISO"),
    ("tzdb-idor", "tzdb object-id IDOR", "America/New_York", "geo_id", "tzdb", "zone unique from IANA"),
    ("iana-lang-idor", "IANA language object-id IDOR", "en-US", "lab_id", "iana-lang", "tag unique from IANA"),
    ("bcp47-idor", "BCP47 object-id IDOR", "zh-Hans-CN", "lab_id", "bcp47", "tag unique from IETF"),
    ("cldr-tz-idor", "CLDR TZ object-id IDOR", "America_New_York", "geo_id", "cldr-tz", "TZ unique from Unicode"),
    ("fcc-frn-idor", "FCC FRN object-id IDOR", "0001234567", "lab_id", "fcc-frn", "FRN unique from FCC"),
    ("imo-num-idor", "IMO number object-id IDOR", "9074729", "mmsi_id", "imo-num", "IMO unique from IMO"),
    ("icao24-idor", "ICAO 24-bit object-id IDOR", "a1b2c3", "mmsi_id", "icao24", "addr unique from ICAO"),
    ("mode-s-idor", "Mode-S object-id IDOR", "ADF123", "mmsi_id", "mode-s", "addr unique from ICAO"),
    ("tailn-n-idor", "N-number object-id IDOR", "N12345", "mmsi_id", "tailn-n", "N unique from FAA"),
]
assert len(IDOR_SRC) == 80, len(IDOR_SRC)
IDOR = []
for slug, surface, sample, owner, product, bug in IDOR_SRC:
    mod, model, lookup = names(slug)
    IDOR.append((slug, surface, mod, model, lookup, sample, owner, product, bug))
assert not ({x[0] for x in IDOR} & USED_SLUGS), {x[0] for x in IDOR} & USED_SLUGS
assert len({x[2] for x in IDOR}) == 80, "mod collision"
assert len({x[4] for x in IDOR}) == 80, "lookup collision"

BFLA_SRC = [
    ("jenkins-job-skip-delete", "Jenkins job delete missing crumb", "java -jar jenkins-cli.jar delete-job notes", "java -jar jenkins-cli.jar get-job notes"),
    ("gitlab-proj-skip-delete", "GitLab project delete missing token", "glab repo delete notes --yes", "glab repo view notes"),
    ("gha-run-skip-delete", "GHA run delete missing token", "gh run delete notes", "gh run view notes"),
    ("tekton-pr-skip-delete", "Tekton PipelineRun delete missing rbac", "kubectl delete pipelinerun notes", "kubectl get pipelinerun notes"),
    ("drone-repo-skip-delete", "Drone repo delete missing token", "drone repo rm notes", "drone repo info notes"),
    ("gitea-repo-skip-delete", "Gitea repo delete missing token", "tea repos delete notes", "tea repos view notes"),
    ("forgejo-skip-delete", "Forgejo repo delete missing token", "forgejo repo delete notes --yes", "forgejo repo view notes"),
    ("travis-ci-skip-delete", "Travis repo delete missing token", "travis disable notes", "travis show notes"),
    ("appveyor-skip-delete", "AppVeyor project delete missing token", "appveyor project delete notes", "appveyor project get notes"),
    ("azdo-pipe-skip-delete", "Azure DevOps pipeline delete missing pat", "az pipelines delete --id notes --yes", "az pipelines show --id notes"),
    ("codebuild-skip-delete", "CodeBuild project delete missing aws", "aws codebuild delete-project --name notes", "aws codebuild batch-get-projects --names notes"),
    ("codepipe-skip-delete", "CodePipeline delete missing aws", "aws codepipeline delete-pipeline --name notes", "aws codepipeline get-pipeline --name notes"),
    ("gcb-skip-delete", "Cloud Build trigger delete missing adc", "gcloud builds triggers delete notes --quiet", "gcloud builds triggers describe notes"),
    ("tf-state-skip-delete", "Terraform state rm missing token", "terraform state rm notes", "terraform state show notes"),
    ("pulumi-st-skip-delete", "Pulumi stack delete missing token", "pulumi stack rm notes --yes", "pulumi stack --show-name notes"),
    ("puppet-nd-skip-delete", "Puppet node deactivate missing cert", "puppet node deactivate notes", "puppet node status notes"),
    ("salt-minion-skip-delete", "Salt key delete missing master", "salt-key -d notes -y", "salt-key -f notes"),
    ("vagrant-bx-skip-delete", "Vagrant box remove missing home", "vagrant box remove notes --force", "vagrant box list"),
    ("vault-sec-skip-delete", "Vault secret delete missing token", "vault kv delete secret/notes", "vault kv get secret/notes"),
    ("waypoint-skip-delete", "Waypoint destroy missing token", "waypoint destroy -yes notes", "waypoint status notes"),
    ("tfe-ws-skip-delete", "TFE workspace delete missing token", "tfc workspaces delete notes --force", "tfc workspaces show notes"),
    ("atlantis-skip-delete", "Atlantis unlock missing webhook", "atlantis unlock notes", "atlantis status notes"),
    ("spacelift-skip-delete", "Spacelift stack delete missing token", "spacectl stack delete notes --force", "spacectl stack show notes"),
    ("env0-skip-delete", "env0 environment destroy missing token", "env0 environment destroy notes --force", "env0 environment get notes"),
    ("terrateam-skip-delete", "Terrateam unlock missing token", "terrateam unlock notes", "terrateam status notes"),
    ("checkov-skip-delete", "Checkov baseline delete missing conf", "rm notes.checkov.baseline", "checkov -f notes"),
    ("tfsec-skip-delete", "tfsec baseline delete missing conf", "rm notes.tfsec.json", "tfsec notes"),
    ("trivy-skip-delete", "Trivy ignore delete missing conf", "rm notes.trivyignore", "trivy fs notes"),
    ("grype-skip-delete", "Grype db wipe missing cache", "grype db delete", "grype notes"),
    ("syft-skip-delete", "Syft sbom delete missing file", "rm notes.syft.json", "syft notes"),
    ("cosign-skip-delete", "Cosign signature delete missing key", "cosign clean notes", "cosign verify notes"),
    ("notation-skip-delete", "Notation signature delete missing key", "notation delete notes", "notation inspect notes"),
    ("rekor-skip-delete", "Rekor entry delete missing token", "rekor-cli delete --uuid notes", "rekor-cli get --uuid notes"),
    ("fulcio-skip-delete", "Fulcio cert revoke missing oidc", "fulcio revoke --id notes", "fulcio get --id notes"),
    ("grafana-ds-skip-delete", "Grafana datasource delete missing token", "grafana-cli admin datasources delete notes", "grafana-cli admin datasources list"),
    ("thanos-skip-delete", "Thanos rule delete missing token", "thanos tools bucket rm notes", "thanos tools bucket ls"),
    ("mimir-skip-delete", "Mimir rule delete missing token", "mimirtool rules delete notes", "mimirtool rules get notes"),
    ("alertmgr-skip-delete", "Alertmanager silence delete missing token", "amtool silence expire notes", "amtool silence query notes"),
    ("vector-skip-delete", "Vector sink delete missing conf", "rm /etc/vector/notes.toml", "vector validate"),
    ("fluentd-skip-delete", "Fluentd match delete missing conf", "rm /etc/fluent/notes.conf", "fluentd --dry-run"),
    ("fluentbit-skip-delete", "Fluent Bit input delete missing conf", "rm /etc/fluent-bit/notes.conf", "fluent-bit -c /etc/fluent-bit/fluent-bit.conf --dry-run"),
    ("filebeat-skip-delete", "Filebeat input delete missing conf", "rm /etc/filebeat/notes.yml", "filebeat test config"),
    ("logstash-skip-delete", "Logstash pipeline delete missing conf", "rm /etc/logstash/conf.d/notes.conf", "logstash --config.test_and_exit"),
    ("es-index-skip-delete", "Elasticsearch index delete missing user", "curl -X DELETE $ES/notes", "curl $ES/notes"),
    ("os-index-skip-delete", "OpenSearch index delete missing user", "curl -X DELETE $OS/notes", "curl $OS/notes"),
    ("kibana-skip-delete", "Kibana saved object delete missing token", "curl -X DELETE $KBN/api/saved_objects/index-pattern/notes", "curl $KBN/api/saved_objects/index-pattern/notes"),
    ("pg-db-skip-delete", "Postgres database drop missing role", "dropdb notes", "psql -l | grep notes"),
    ("mysql-db-skip-delete", "MySQL database drop missing grant", "mysqladmin drop notes -f", "mysqlshow notes"),
    ("redis-key-skip-delete", "Redis key delete missing acl", "redis-cli DEL notes", "redis-cli GET notes"),
    ("mongo-db-skip-delete", "MongoDB dropDatabase missing role", "mongosh --eval 'db.getSiblingDB(\"notes\").dropDatabase()'", "mongosh --eval 'db.getSiblingDB(\"notes\").stats()'"),
    ("cstar-ks-skip-delete", "Cassandra keyspace drop missing role", "cqlsh -e 'DROP KEYSPACE notes'", "cqlsh -e 'DESCRIBE KEYSPACE notes'"),
    ("ch-db-skip-delete", "ClickHouse database drop missing user", "clickhouse-client -q 'DROP DATABASE notes'", "clickhouse-client -q 'SHOW DATABASES'"),
    ("crdb-db-skip-delete", "CockroachDB database drop missing user", "cockroach sql -e 'DROP DATABASE notes'", "cockroach sql -e 'SHOW DATABASES'"),
    ("tidb-db-skip-delete", "TiDB database drop missing grant", "mysql -h tidb -e 'DROP DATABASE notes'", "mysql -h tidb -e 'SHOW DATABASES'"),
    ("neo4j-db-skip-delete", "Neo4j database drop missing auth", "cypher-shell 'DROP DATABASE notes'", "cypher-shell 'SHOW DATABASES'"),
    ("influx-db-skip-delete", "InfluxDB bucket delete missing token", "influx bucket delete -n notes", "influx bucket list"),
    ("tsdb-db-skip-delete", "Timescale hypertable drop missing role", "psql -c 'DROP TABLE notes'", "psql -c '\\dt notes'"),
    ("traefik-rt-skip-delete", "Traefik router delete missing api", "curl -X DELETE $TR/api/http/routers/notes", "curl $TR/api/http/routers/notes"),
    ("envoy-cls-skip-delete", "Envoy cluster delete missing admin", "curl -X POST $EN/clusters/notes/delete", "curl $EN/clusters/notes"),
    ("caddy-rt-skip-delete", "Caddy route delete missing admin", "curl -X DELETE $CD/config/apps/http/servers/srv0/routes/notes", "curl $CD/config/apps/http/servers/srv0/routes/notes"),
    ("airflow-dag-skip-delete", "Airflow DAG delete missing rbac", "airflow dags delete notes -y", "airflow dags list | grep notes"),
    ("prefect-fl-skip-delete", "Prefect flow delete missing token", "prefect deployment delete notes", "prefect deployment inspect notes"),
    ("dagster-job-skip-delete", "Dagster job delete missing token", "dagster job delete notes", "dagster job list"),
    ("luigi-task-skip-delete", "Luigi task delete missing conf", "luigi-deps --module notes --delete", "luigi --module notes --local-scheduler"),
    ("mlflow-run-skip-delete", "MLflow run delete missing token", "mlflow runs delete --run-id notes", "mlflow runs describe --run-id notes"),
    ("kubeflow-skip-delete", "Kubeflow pipeline delete missing rbac", "kfp pipeline delete notes", "kfp pipeline get notes"),
    ("wandb-run-skip-delete", "W&B run delete missing token", "wandb sync --delete notes", "wandb pull notes"),
    ("dvc-rem-skip-delete", "DVC remote remove missing conf", "dvc remote remove notes", "dvc remote list"),
    ("airbyte-src-skip-delete", "Airbyte source delete missing token", "airbyte source delete notes", "airbyte source get notes"),
    ("dbt-model-skip-delete", "dbt model drop missing profile", "dbt run-operation drop_model --args '{model: notes}'", "dbt ls --select notes"),
    ("spark-app-skip-delete", "Spark app kill missing yarn", "spark-submit --kill notes", "spark-submit --status notes"),
    ("flink-job-skip-delete", "Flink job cancel missing rest", "flink cancel notes", "flink list | grep notes"),
    ("beam-job-skip-delete", "Beam job cancel missing gcp", "gcloud dataflow jobs cancel notes", "gcloud dataflow jobs show notes"),
    ("kafka-conn-skip-delete", "Kafka Connect connector delete missing rest", "curl -X DELETE $KC/connectors/notes", "curl $KC/connectors/notes"),
    ("schema-reg-skip-delete", "Schema Registry subject delete missing rest", "curl -X DELETE $SR/subjects/notes", "curl $SR/subjects/notes"),
    ("kconnect-skip-delete", "kconnect context delete missing kube", "kconnect rm notes", "kconnect ls"),
    ("debezium-skip-delete", "Debezium connector delete missing rest", "curl -X DELETE $DBZ/connectors/notes", "curl $DBZ/connectors/notes"),
    ("maxwell-skip-delete", "Maxwell position delete missing mysql", "maxwell-bootstrap --delete notes", "maxwell --config notes"),
    ("tableau-skip-delete", "Tableau workbook delete missing token", "tabcmd delete \"notes.twb\"", "tabcmd get \"notes.twb\""),
    ("powerbi-skip-delete", "Power BI dataset delete missing token", "pbicli dataset delete notes", "pbicli dataset get notes"),
]
assert len(BFLA_SRC) == 80, len(BFLA_SRC)
BFLA = [(s, surf, "js_route", skip, auth) for s, surf, skip, auth in BFLA_SRC]
assert not ({x[0] for x in BFLA} & USED_SLUGS), {x[0] for x in BFLA} & USED_SLUGS
assert len({x[0] for x in BFLA}) == 80

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


header = '''"""Extra unique IDOR/BFLA plants for authz-regression-factory r2240+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r2239 vesselNNNN-sys.
Not clones of r2239 metar-v2 / rancher-d, r2160 iso3166-n3 / kind-cluster.
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
