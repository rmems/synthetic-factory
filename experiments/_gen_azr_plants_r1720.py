#!/usr/bin/env python3
"""Emit experiments/azr-plants-r1720.py — unique IDOR/BFLA for r1720+ (40 pairs)."""
from __future__ import annotations

import re
from pathlib import Path

EXPERIMENTS = Path(__file__).resolve().parent
OUT = EXPERIMENTS / "azr-plants-r1720.py"

USED_SLUGS: set[str] = set()
USED_PLANTS: set[str] = set()
USED_LOOKUPS: set[str] = set()
USED_MODS: set[str] = set()
for p in list(EXPERIMENTS.glob("azr-plants*.py")) + list(EXPERIMENTS.glob("azr-mill*.py")):
    if p.name == "azr-plants-r1720.py":
        continue
    text = p.read_text(errors="ignore")
    USED_SLUGS.update(re.findall(r"slug=['\"]([a-z0-9-]+)['\"]", text))
    USED_PLANTS.update(re.findall(r"plant=['\"]([a-z0-9-]+)['\"]", text))
    USED_LOOKUPS.update(re.findall(r"lookup=['\"]([a-z0-9_]+)['\"]", text))
    USED_MODS.update(re.findall(r"mod=['\"]([a-z0-9_]+)['\"]", text))

PREFIX = [
    "yawl", "yoke", "yulo", "zabr", "zulub", "aftw", "bagy", "balky", "batty", "beamy",
    "bighty", "bilgy", "bitty", "boomy", "bowy", "breezy", "bulky", "bunty", "cably", "camby",
    "canty", "capty", "carly", "catty", "chainy", "cheeky", "chocky", "clewy", "cliny", "coamy",
    "cocky", "cordy", "county", "coxy", "crany", "criny", "crosy", "crowy", "cunny", "cutty",
]
SUFFIX = ["keel", "boom", "hatch", "rail", "post"]
PLANTS: list[str] = []
for pre in PREFIX:
    for suf in SUFFIX:
        name = pre + suf
        if name in USED_PLANTS or name in PLANTS or not name.isidentifier():
            continue
        PLANTS.append(name)
        break
    if len(PLANTS) == 40:
        break
assert len(PLANTS) == 40, len(PLANTS)
assert not (set(PLANTS) & USED_PLANTS)

FIRST = ["authn", "mask", "any_member", "list_scope"]
RESIDUAL = ["pdf", "export", "search", "mget", "csv", "admin", "webhook", "comments"]
LEFTOVER = ["put", "patch", "update"]

IDOR = [
    ("fps-uk-idor", "Faster Payments object-id IDOR", "fpsuks", "Fpsuk", "fpsuk", "FPS240115000001", "bank_id", "fps-uk", "id unique from Pay.UK"),
    ("spei-ref-idor", "SPEI clave object-id IDOR", "speirefs", "Speiref", "speiref", "202401150001234567", "bank_id", "spei-ref", "clave unique from Banxico"),
    ("fiveqi-idor", "5QI QoS object-id IDOR", "fiveqis", "Fiveqi", "fiveqi", "9", "net_id", "5qi-3gpp", "5QI unique from 3GPP"),
    ("qfi-5g-idor", "QFI object-id IDOR", "qfi5gs", "Qfi5g", "qfi5g", "1", "net_id", "qfi-5g", "QFI unique from 3GPP"),
    ("sst-slice-idor", "SST slice object-id IDOR", "ssts", "Sst", "sstid", "1", "net_id", "sst-5g", "SST unique from 3GPP"),
    ("sd-slice-idor", "SD slice differentiator object-id IDOR", "sdslices", "Sdslc", "sdslc", "000001", "net_id", "sd-5g", "SD unique from 3GPP"),
    ("fedwire-imad-idor", "Fedwire IMAD object-id IDOR", "fedwires", "Fedwire", "fedwire", "20240115MMQFMPF000099", "bank_id", "fedwire-imad", "IMAD unique from Fedwire"),
    ("chaps-uk-idor", "CHAPS payment object-id IDOR", "chapsuks", "Chapsuk", "chapsuk", "CHAPS2401150001", "bank_id", "chaps-uk", "id unique from CHAPS"),
    ("bacs-uk-idor", "Bacs payment object-id IDOR", "bacsuks", "Bacsuk", "bacsuk", "BACS2401150001", "bank_id", "bacs-uk", "id unique from Bacs"),
    ("swift-gpi-idor", "SWIFT gpi UETR twin object-id IDOR", "swiftgpis", "Swiftgpi", "swiftgpi", "gpi-240115-0001", "bank_id", "swift-gpi", "gpi unique from SWIFT"),
    ("tan-in-idor", "India TAN object-id IDOR", "tanins", "Tanin", "tanin", "DELA12345F", "firm_id", "tan-in", "TAN unique from NSDL"),
    ("cin-mca-idor", "MCA CIN object-id IDOR", "cinmcas", "Cinmca", "cinmca", "U74999DL2018PTC123456", "firm_id", "cin-mca", "CIN unique from MCA"),
    ("llpin-idor", "LLPIN object-id IDOR", "llpins", "Llpin", "llpin", "AAA-1234", "firm_id", "llpin-mca", "LLPIN unique from MCA"),
    ("din-mca-idor", "DIN director object-id IDOR", "dinmcas", "Dinmca", "dinmca", "01234567", "firm_id", "din-mca", "DIN unique from MCA"),
    ("iec-dgft-idor", "DGFT IEC object-id IDOR", "iecdgfts", "Iecdgft", "iecdgft", "0512345678", "firm_id", "iec-dgft", "IEC unique from DGFT"),
    ("gstin-uin-idor", "GSTIN UIN object-id IDOR", "gstinuins", "Gstinuin", "gstinuin", "0717UNO00123UNU", "firm_id", "gstin-uin", "UIN unique from GSTN"),
    ("iras-src-idor", "IRAS source object-id IDOR", "irassrcs", "Irassrc", "irassrc", "IRAS 18322-652", "lab_id", "iras-src", "IRAS unique from IRAS"),
    ("akari-irc-idor", "AKARI IRC object-id IDOR", "akariircs", "Akariirc", "akariirc", "AKARI-IRC-J0535149-052353", "lab_id", "akari-irc", "AKARI unique from JAXA"),
    ("galex-ais-idor", "GALEX AIS object-id IDOR", "galexais", "Galexais", "galexais", "GALEX J053514.9-052353", "lab_id", "galex-ais", "GALEX unique from MAST"),
    ("xmm-obs-idor", "XMM-Newton obs object-id IDOR", "xmmobss", "Xmmobs", "xmmobs", "0123456789", "lab_id", "xmm-obs", "obsid unique from XMM"),
    ("chandra-obs-idor", "Chandra obs object-id IDOR", "chandras", "Chandra", "chandra", "12345", "lab_id", "chandra-obs", "obsid unique from Chandra"),
    ("nustar-obs-idor", "NuSTAR obs object-id IDOR", "nustars", "Nustar", "nustar", "30002001002", "lab_id", "nustar-obs", "obsid unique from NuSTAR"),
    ("swiftbat-idor", "Swift-BAT trigger object-id IDOR", "swiftbats", "Swiftbat", "swiftbat", "123456", "lab_id", "swift-bat", "trigger unique from Swift"),
    ("fermi-lat-idor", "Fermi LAT source object-id IDOR", "fermilats", "Fermilat", "fermilat", "4FGL J0534.5+2201", "lab_id", "fermi-lat", "4FGL unique from Fermi"),
    ("wmap-src-idor", "WMAP source object-id IDOR", "wmapsrcs", "Wmapsrc", "wmapsrc", "WMAP J1234+56", "lab_id", "wmap-src", "WMAP unique from LAMBDA"),
    ("planck-src-idor", "Planck source object-id IDOR", "plancks", "Planck", "planck", "PCCS2 G123.45-67.89", "lab_id", "planck-src", "PCCS unique from Planck"),
    ("caiso-pnode-idor", "CAISO pnode object-id IDOR", "caisopns", "Caisopn", "caisopn", "POD_MOSSLD_7_N002", "grid_id", "caiso-pnode", "pnode unique from CAISO"),
    ("pjm-zone-idor", "PJM zone object-id IDOR", "pjmzones", "Pjmzone", "pjmzone", "PECO", "grid_id", "pjm-zone", "zone unique from PJM"),
    ("spp-hub-idor", "SPP hub object-id IDOR", "spphubs", "Spphub", "spphub", "SPPNORTH_HUB", "grid_id", "spp-hub", "hub unique from SPP"),
    ("ercot-hub-idor", "ERCOT hub object-id IDOR", "ercothubs", "Ercothub", "ercothub", "HB_NORTH", "grid_id", "ercot-hub", "hub unique from ERCOT"),
    ("nyiso-zone-idor", "NYISO zone object-id IDOR", "nyisozones", "Nyisozone", "nyisozone", "J", "grid_id", "nyiso-zone", "zone unique from NYISO"),
    ("isone-zone-idor", "ISO-NE zone object-id IDOR", "isonezones", "Isonezone", "isonezone", ".Z.WESTERNMASS", "grid_id", "isone-zone", "zone unique from ISO-NE"),
    ("ppmxl-idor", "PPMXL star object-id IDOR", "ppmxls", "Ppmxl", "ppmxl", "PPMXL 1234567890123", "lab_id", "ppmxl-id", "PPMXL unique from ARI"),
    ("ucac2-idor", "UCAC2 star object-id IDOR", "ucac2s", "Ucac2", "ucac2", "UCAC2 12345678", "lab_id", "ucac2-id", "UCAC2 unique from USNO"),
    ("tycho1-idor", "Tycho-1 object-id IDOR", "tyc1s", "Tyc1", "tyc1", "TYC 1234-567-1", "lab_id", "tycho1-id", "Tycho-1 unique from ESA"),
    ("allwise-rej-idor", "AllWISE reject object-id IDOR", "allwiserejs", "Allwiserej", "allwiserej", "WISEA J053514.94-052353.9R", "lab_id", "allwise-rej", "reject unique from IRSA"),
    ("twomass-xsc-idor", "2MASS XSC object-id IDOR", "twomassxscs", "Twomassxsc", "twomassxsc", "2MASX J05351494-0523539", "lab_id", "twomass-xsc", "XSC unique from IPAC"),
    ("ogle-var-idor", "OGLE variable object-id IDOR", "oglevs", "Oglev", "oglev", "OGLE-LMC-CEP-0001", "lab_id", "ogle-var", "variable unique from OGLE"),
    ("asassn-idor", "ASAS-SN transient object-id IDOR", "asassns", "Asassn", "asassn", "ASASSN-24ab", "lab_id", "asassn-id", "name unique from ASAS-SN"),
    ("ztf-oid-idor", "ZTF object-id IDOR", "ztfoids", "Ztfoid", "ztfoid", "ZTF18aaaaaaa", "lab_id", "ztf-oid", "oid unique from ZTF"),
]

assert len(IDOR) == 40, len(IDOR)
assert len({x[0] for x in IDOR}) == 40
assert len({x[2] for x in IDOR}) == 40
assert len({x[4] for x in IDOR}) == 40
assert not ({x[0] for x in IDOR} & USED_SLUGS), {x[0] for x in IDOR} & USED_SLUGS
assert not ({x[4] for x in IDOR} & USED_LOOKUPS), {x[4] for x in IDOR} & USED_LOOKUPS
assert not ({x[2] for x in IDOR} & USED_MODS), {x[2] for x in IDOR} & USED_MODS

BFLA = [
    ("fly-replay-skip-delete", "Fly.io replay DELETE missing fly-replay auth", "js_route",
     "if (method==='DELETE') return notes.del(id)",
     "if (method==='GET') { if (!request.headers.get('fly-replay-src')) auth(); return notes.get(id, user) }"),
    ("envoy-lua-skip-delete", "Envoy Lua filter skip DELETE", "js_route",
     "function envoy_on_request(r) if r:headers():get(':method')=='DELETE' then return end",
     "function envoy_on_request(r) if r:headers():get('authorization')==nil then r:respond({[':status']='401'}) end"),
    ("coredns-skip-delete", "CoreDNS update skip plugin auth", "js_route",
     "update {\n  policy tcp\n}",
     "acl {\n  allow net 10.0.0.0/8\n}"),
    ("bind9-update-skip-delete", "BIND9 nsupdate DELETE missing TSIG", "js_route",
     "update-policy { grant * wildcard * ANY; };",
     "update-policy { grant notes-key name notes.example.com ANY; };"),
    ("powerdns-skip-delete", "PowerDNS DELETE missing API-Key", "js_route",
     "DELETE /api/v1/servers/localhost/zones/notes  # no X-API-Key",
     "GET /api/v1/servers/localhost/zones/notes  X-API-Key required"),
    ("knot-dns-skip-delete", "Knot DNS ddns skip ACL", "js_route",
     "acl:\n  - id: open\n    address: 0.0.0.0/0\n    action: update",
     "acl:\n  - id: notes\n    key: notes-key\n    action: query"),
    ("nsd-skip-delete", "NSD control delzone missing control-key", "js_route",
     "nsd-control delzone notes.example  # no key",
     "nsd-control -c nsd.conf -y key zonestatus notes.example"),
    ("unbound-skip-delete", "Unbound remote-control skip auth", "js_route",
     "unbound-control flush_zone notes.example",
     "unbound-control-setup && unbound-control status"),
    ("dnsmasq-skip-delete", "dnsmasq dhcp-host delete missing conf-script auth", "js_route",
     "dhcp-host=id:*,ignore  # delete open",
     "conf-script=/usr/local/bin/auth-reload"),
    ("keepalived-skip-delete", "Keepalived notify delete missing script user", "js_route",
     "notify_stop /usr/local/bin/del-notes  # root unauth",
     "script_user keepalived keepalived\nnotify_master /usr/local/bin/auth-notes"),
    ("pacemaker-skip-delete", "Pacemaker crm delete missing acl", "js_route",
     "crm configure delete notes-rsc",
     "crm configure property enable-acl=true"),
    ("corosync-skip-delete", "Corosync cmap delete missing uidgid", "js_route",
     "corosync-cmapctl -D runtime.notes.id",
     "uidgid { uid: corosync gid: corosync }"),
    ("patroni-skip-delete", "Patroni DELETE missing restapi auth", "js_route",
     "DELETE /cluster  authentication: none",
     "restapi:\n  authentication:\n    username: admin"),
    ("stolon-skip-delete", "Stolon cluster delete missing keeper auth", "js_route",
     "stolonctl cluster remove --yes",
     "stolonctl --kube-resource-kind=configmap status"),
    ("vitess-skip-delete", "Vitess vtctl DeleteKeyspace missing auth", "js_route",
     "vtctlclient DeleteKeyspace notes",
     "vtctlclient --grpc_auth_static_client_creds creds.json GetKeyspace notes"),
    ("tidb-skip-delete", "TiDB DELETE missing privilege", "sql",
     "DELETE FROM notes WHERE id=?;  -- user without privilege check skipped",
     "GRANT SELECT ON notes.* TO 'app'@'%';"),
    ("yugabyte-skip-delete", "Yugabyte YSQL DELETE missing GRANT", "sql",
     "GRANT DELETE ON notes TO anon;",
     "GRANT SELECT ON notes TO app;"),
    ("spanner-skip-delete", "Spanner delete missing Fine-grained IAM", "js_route",
     "session.executeDelete(Mutation.delete(\"notes\", Key.of(id)))  # no iam",
     "database.getIamPolicy(); session.readRow(\"notes\", Key.of(id), cols)"),
    ("cosmosdb-skip-delete", "Cosmos DB delete missing resource token", "js_route",
     "container.deleteItem(id, new PartitionKey(id))",
     "container.readItem(id, new PartitionKey(id), { resourceToken: token })"),
    ("firestore-skip-delete", "Firestore delete missing rules", "js_route",
     "match /notes/{id} { allow delete: if true; }",
     "match /notes/{id} { allow get: if request.auth.uid == resource.data.owner; }"),
    ("bigtable-skip-delete", "Bigtable dropRow missing IAM", "js_route",
     "table.dropRow(rowkey)  # no iam",
     "table.readRow(rowkey, filters=authFilter(user))"),
    ("datastore-skip-delete", "Datastore delete missing namespace auth", "js_route",
     "client.delete(key)",
     "client.get(key, namespace=user.ns)"),
    ("dynamodb-skip-delete", "DynamoDB DeleteItem missing condition owner", "js_route",
     "ddb.delete_item(Key={'id': id})",
     "ddb.get_item(Key={'id': id, 'owner': user})"),
    ("documentdb-skip-delete", "DocumentDB delete missing rbac", "js_route",
     "db.notes.deleteOne({_id: id})",
     "db.notes.findOne({_id: id, owner: user})"),
    ("elasticache-skip-delete", "ElastiCache DEL missing AUTH", "js_route",
     "redis.del('notes:'+id)  # no AUTH",
     "redis.auth(token); redis.get('notes:'+id)"),
    ("memorystore-skip-delete", "Memorystore DEL missing AUTH", "js_route",
     "r.delete('notes:'+id)",
     "r.auth(token); r.get('notes:'+id)"),
    ("valkey-acl-skip-delete", "Valkey ACL skip DEL", "js_route",
     "ACL SETUSER anon +del ~notes:*",
     "ACL SETUSER app +get ~notes:* on >pass"),
    ("keydb-skip-delete", "KeyDB DEL missing ACL", "js_route",
     "DEL notes:id  # default user",
     "ACL SETUSER app on >pass ~notes:* +get"),
    ("dragonfly-skip-delete", "Dragonfly DEL missing requirepass", "js_route",
     "DEL notes:id",
     "AUTH token; GET notes:id"),
    ("nats-auth-skip-delete", "NATS delete missing user JWT account", "js_route",
     "js.DeleteStream('NOTES')  # no creds",
     "nc, _ := nats.Connect(url, nats.UserJWT(jwt, sig))"),
    ("nats-js-skip-delete", "NATS JetStream delete missing PurgeACL", "js_route",
     "js.PurgeStream('NOTES')",
     "js.StreamInfo('NOTES', nats.BindStream('NOTES'))  // account jwt"),
    ("rabbitmq-skip-delete", "RabbitMQ delete queue missing management auth", "js_route",
     "DELETE /api/queues/%2F/notes  # guest",
     "GET /api/queues/%2F/notes  basic auth user"),
    ("kafka-acl-skip-delete", "Kafka ACL skip DeleteTopics", "js_route",
     "admin.deleteTopics(List.of('notes'))",
     "acl.bind(User:app, Topic:notes, READ, ALLOW)"),
    ("redpanda-skip-delete", "Redpanda delete topic missing SASL", "js_route",
     "rpk topic delete notes  # no sasl",
     "rpk topic describe notes -X sasl.mechanism=SCRAM-SHA-256"),
    ("mqtt-acl-skip-delete", "MQTT ACL skip $SYS delete", "js_route",
     "acl { user all topic delete notes/# }",
     "acl { user app topic read notes/# }"),
    ("emqx-skip-delete", "EMQX delete rule missing dashboard auth", "js_route",
     "DELETE /api/v5/rules/{id}  # anonymous",
     "GET /api/v5/rules/{id}  Authorization: Bearer"),
    ("vernemq-skip-delete", "VerneMQ delete skip vmq_diversity auth", "js_route",
     "vmq-admin session disconnect client-id=notes  # open",
     "vmq-admin listener start --ssl --cafile ca.pem"),
    ("mosquitto-skip-delete", "Mosquitto ACL skip unsubscribe as delete", "js_route",
     "acl_file /dev/null  # all delete",
     "acl_file /etc/mosquitto/acl\nuser app\ntopic read notes/#"),
    ("pulsar-auth-skip-delete", "Pulsar admin delete missing token", "js_route",
     "pulsar-admin topics delete persistent://p/n/notes",
     "pulsar-admin --auth-plugin org.apache.pulsar.client.impl.auth.AuthenticationToken topics list p/n"),
    ("redpanda-admin-skip-delete", "Redpanda admin DELETE missing basic auth", "js_route",
     "DELETE /v1/topics/notes  # no auth",
     "GET /v1/topics/notes  Authorization: Basic"),
]

assert len(BFLA) == 40, len(BFLA)
assert len({x[0] for x in BFLA}) == 40
assert not ({x[0] for x in BFLA} & USED_SLUGS), {x[0] for x in BFLA} & USED_SLUGS

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


header = '''"""Extra unique IDOR/BFLA plants for authz-regression-factory r1720+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r1719 vesselNNNN-sys.
Not clones of r1364 geohash / r1445 casbin / r1543 gstin-isd / r1560 e212 / r1640 imeitac.
"""
from __future__ import annotations


EXTRA_IDOR_ROWS = [
'''
expand_src = (EXPERIMENTS / "azr-plants-r1504.py").read_text()
idx = expand_src.index("def extra_bflas")
body = (
    header
    + "\n".join(py_idor_row(i) for i in range(40))
    + "\n]\n\n\nBFLA_ROWS = [\n"
    + "\n".join(py_bfla_row(i) for i in range(40))
    + "\n]\n\n\n"
    + expand_src[idx:]
)
OUT.write_text(body)
print("wrote", OUT, "plants0", PLANTS[0], "idor0", IDOR[0][0], "bfla0", BFLA[0][0])
