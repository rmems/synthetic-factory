"""Extra unique IDOR/BFLA plants for authz-regression-factory r1720+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r1719 vesselNNNN-sys.
Not clones of r1364 geohash / r1445 casbin / r1543 gstin-isd / r1560 e212 / r1640 imeitac.
"""
from __future__ import annotations


EXTRA_IDOR_ROWS = [
    dict(slug='fps-uk-idor', plant='yawlkeel', ticket='YAW-1', surface='Faster Payments object-id IDOR', mod='fpsuks', model='Fpsuk', lookup='fpsuk', sample='FPS240115000001', owner='bank_id', first='authn', residual='pdf', product='fps-uk', bug='YAW-1 id unique from Pay.UK'),
    dict(slug='spei-ref-idor', plant='yokekeel', ticket='YOK-2', surface='SPEI clave object-id IDOR', mod='speirefs', model='Speiref', lookup='speiref', sample='202401150001234567', owner='bank_id', first='mask', residual='export', product='spei-ref', bug='YOK-2 clave unique from Banxico'),
    dict(slug='fiveqi-idor', plant='yulokeel', ticket='YUL-3', surface='5QI QoS object-id IDOR', mod='fiveqis', model='Fiveqi', lookup='fiveqi', sample='9', owner='net_id', first='any_member', residual='search', product='5qi-3gpp', bug='YUL-3 5QI unique from 3GPP'),
    dict(slug='qfi-5g-idor', plant='zabrkeel', ticket='ZAB-4', surface='QFI object-id IDOR', mod='qfi5gs', model='Qfi5g', lookup='qfi5g', sample='1', owner='net_id', first='list_scope', residual='mget', product='qfi-5g', bug='ZAB-4 QFI unique from 3GPP'),
    dict(slug='sst-slice-idor', plant='zulubkeel', ticket='ZUL-5', surface='SST slice object-id IDOR', mod='ssts', model='Sst', lookup='sstid', sample='1', owner='net_id', first='authn', residual='csv', product='sst-5g', bug='ZUL-5 SST unique from 3GPP'),
    dict(slug='sd-slice-idor', plant='aftwkeel', ticket='AFT-6', surface='SD slice differentiator object-id IDOR', mod='sdslices', model='Sdslc', lookup='sdslc', sample='000001', owner='net_id', first='mask', residual='admin', product='sd-5g', bug='AFT-6 SD unique from 3GPP'),
    dict(slug='fedwire-imad-idor', plant='bagykeel', ticket='BAG-7', surface='Fedwire IMAD object-id IDOR', mod='fedwires', model='Fedwire', lookup='fedwire', sample='20240115MMQFMPF000099', owner='bank_id', first='any_member', residual='webhook', product='fedwire-imad', bug='BAG-7 IMAD unique from Fedwire'),
    dict(slug='chaps-uk-idor', plant='balkykeel', ticket='BAL-8', surface='CHAPS payment object-id IDOR', mod='chapsuks', model='Chapsuk', lookup='chapsuk', sample='CHAPS2401150001', owner='bank_id', first='list_scope', residual='comments', product='chaps-uk', bug='BAL-8 id unique from CHAPS'),
    dict(slug='bacs-uk-idor', plant='battykeel', ticket='BAT-9', surface='Bacs payment object-id IDOR', mod='bacsuks', model='Bacsuk', lookup='bacsuk', sample='BACS2401150001', owner='bank_id', first='authn', residual='pdf', product='bacs-uk', bug='BAT-9 id unique from Bacs'),
    dict(slug='swift-gpi-idor', plant='beamykeel', ticket='BEA-1', surface='SWIFT gpi UETR twin object-id IDOR', mod='swiftgpis', model='Swiftgpi', lookup='swiftgpi', sample='gpi-240115-0001', owner='bank_id', first='mask', residual='export', product='swift-gpi', bug='BEA-1 gpi unique from SWIFT'),
    dict(slug='tan-in-idor', plant='bightykeel', ticket='BIG-2', surface='India TAN object-id IDOR', mod='tanins', model='Tanin', lookup='tanin', sample='DELA12345F', owner='firm_id', first='any_member', residual='search', product='tan-in', bug='BIG-2 TAN unique from NSDL'),
    dict(slug='cin-mca-idor', plant='bilgykeel', ticket='BIL-3', surface='MCA CIN object-id IDOR', mod='cinmcas', model='Cinmca', lookup='cinmca', sample='U74999DL2018PTC123456', owner='firm_id', first='list_scope', residual='mget', product='cin-mca', bug='BIL-3 CIN unique from MCA'),
    dict(slug='llpin-idor', plant='bittykeel', ticket='BIT-4', surface='LLPIN object-id IDOR', mod='llpins', model='Llpin', lookup='llpin', sample='AAA-1234', owner='firm_id', first='authn', residual='csv', product='llpin-mca', bug='BIT-4 LLPIN unique from MCA'),
    dict(slug='din-mca-idor', plant='boomykeel', ticket='BOO-5', surface='DIN director object-id IDOR', mod='dinmcas', model='Dinmca', lookup='dinmca', sample='01234567', owner='firm_id', first='mask', residual='admin', product='din-mca', bug='BOO-5 DIN unique from MCA'),
    dict(slug='iec-dgft-idor', plant='bowykeel', ticket='BOW-6', surface='DGFT IEC object-id IDOR', mod='iecdgfts', model='Iecdgft', lookup='iecdgft', sample='0512345678', owner='firm_id', first='any_member', residual='webhook', product='iec-dgft', bug='BOW-6 IEC unique from DGFT'),
    dict(slug='gstin-uin-idor', plant='breezykeel', ticket='BRE-7', surface='GSTIN UIN object-id IDOR', mod='gstinuins', model='Gstinuin', lookup='gstinuin', sample='0717UNO00123UNU', owner='firm_id', first='list_scope', residual='comments', product='gstin-uin', bug='BRE-7 UIN unique from GSTN'),
    dict(slug='iras-src-idor', plant='bulkykeel', ticket='BUL-8', surface='IRAS source object-id IDOR', mod='irassrcs', model='Irassrc', lookup='irassrc', sample='IRAS 18322-652', owner='lab_id', first='authn', residual='pdf', product='iras-src', bug='BUL-8 IRAS unique from IRAS'),
    dict(slug='akari-irc-idor', plant='buntykeel', ticket='BUN-9', surface='AKARI IRC object-id IDOR', mod='akariircs', model='Akariirc', lookup='akariirc', sample='AKARI-IRC-J0535149-052353', owner='lab_id', first='mask', residual='export', product='akari-irc', bug='BUN-9 AKARI unique from JAXA'),
    dict(slug='galex-ais-idor', plant='cablykeel', ticket='CAB-1', surface='GALEX AIS object-id IDOR', mod='galexais', model='Galexais', lookup='galexais', sample='GALEX J053514.9-052353', owner='lab_id', first='any_member', residual='search', product='galex-ais', bug='CAB-1 GALEX unique from MAST'),
    dict(slug='xmm-obs-idor', plant='cambykeel', ticket='CAM-2', surface='XMM-Newton obs object-id IDOR', mod='xmmobss', model='Xmmobs', lookup='xmmobs', sample='0123456789', owner='lab_id', first='list_scope', residual='mget', product='xmm-obs', bug='CAM-2 obsid unique from XMM'),
    dict(slug='chandra-obs-idor', plant='cantykeel', ticket='CAN-3', surface='Chandra obs object-id IDOR', mod='chandras', model='Chandra', lookup='chandra', sample='12345', owner='lab_id', first='authn', residual='csv', product='chandra-obs', bug='CAN-3 obsid unique from Chandra'),
    dict(slug='nustar-obs-idor', plant='captykeel', ticket='CAP-4', surface='NuSTAR obs object-id IDOR', mod='nustars', model='Nustar', lookup='nustar', sample='30002001002', owner='lab_id', first='mask', residual='admin', product='nustar-obs', bug='CAP-4 obsid unique from NuSTAR'),
    dict(slug='swiftbat-idor', plant='carlykeel', ticket='CAR-5', surface='Swift-BAT trigger object-id IDOR', mod='swiftbats', model='Swiftbat', lookup='swiftbat', sample='123456', owner='lab_id', first='any_member', residual='webhook', product='swift-bat', bug='CAR-5 trigger unique from Swift'),
    dict(slug='fermi-lat-idor', plant='cattykeel', ticket='CAT-6', surface='Fermi LAT source object-id IDOR', mod='fermilats', model='Fermilat', lookup='fermilat', sample='4FGL J0534.5+2201', owner='lab_id', first='list_scope', residual='comments', product='fermi-lat', bug='CAT-6 4FGL unique from Fermi'),
    dict(slug='wmap-src-idor', plant='chainykeel', ticket='CHA-7', surface='WMAP source object-id IDOR', mod='wmapsrcs', model='Wmapsrc', lookup='wmapsrc', sample='WMAP J1234+56', owner='lab_id', first='authn', residual='pdf', product='wmap-src', bug='CHA-7 WMAP unique from LAMBDA'),
    dict(slug='planck-src-idor', plant='cheekykeel', ticket='CHE-8', surface='Planck source object-id IDOR', mod='plancks', model='Planck', lookup='planck', sample='PCCS2 G123.45-67.89', owner='lab_id', first='mask', residual='export', product='planck-src', bug='CHE-8 PCCS unique from Planck'),
    dict(slug='caiso-pnode-idor', plant='chockykeel', ticket='CHO-9', surface='CAISO pnode object-id IDOR', mod='caisopns', model='Caisopn', lookup='caisopn', sample='POD_MOSSLD_7_N002', owner='grid_id', first='any_member', residual='search', product='caiso-pnode', bug='CHO-9 pnode unique from CAISO'),
    dict(slug='pjm-zone-idor', plant='clewykeel', ticket='CLE-1', surface='PJM zone object-id IDOR', mod='pjmzones', model='Pjmzone', lookup='pjmzone', sample='PECO', owner='grid_id', first='list_scope', residual='mget', product='pjm-zone', bug='CLE-1 zone unique from PJM'),
    dict(slug='spp-hub-idor', plant='clinykeel', ticket='CLI-2', surface='SPP hub object-id IDOR', mod='spphubs', model='Spphub', lookup='spphub', sample='SPPNORTH_HUB', owner='grid_id', first='authn', residual='csv', product='spp-hub', bug='CLI-2 hub unique from SPP'),
    dict(slug='ercot-hub-idor', plant='coamykeel', ticket='COA-3', surface='ERCOT hub object-id IDOR', mod='ercothubs', model='Ercothub', lookup='ercothub', sample='HB_NORTH', owner='grid_id', first='mask', residual='admin', product='ercot-hub', bug='COA-3 hub unique from ERCOT'),
    dict(slug='nyiso-zone-idor', plant='cockykeel', ticket='COC-4', surface='NYISO zone object-id IDOR', mod='nyisozones', model='Nyisozone', lookup='nyisozone', sample='J', owner='grid_id', first='any_member', residual='webhook', product='nyiso-zone', bug='COC-4 zone unique from NYISO'),
    dict(slug='isone-zone-idor', plant='cordykeel', ticket='COR-5', surface='ISO-NE zone object-id IDOR', mod='isonezones', model='Isonezone', lookup='isonezone', sample='.Z.WESTERNMASS', owner='grid_id', first='list_scope', residual='comments', product='isone-zone', bug='COR-5 zone unique from ISO-NE'),
    dict(slug='ppmxl-idor', plant='countykeel', ticket='COU-6', surface='PPMXL star object-id IDOR', mod='ppmxls', model='Ppmxl', lookup='ppmxl', sample='PPMXL 1234567890123', owner='lab_id', first='authn', residual='pdf', product='ppmxl-id', bug='COU-6 PPMXL unique from ARI'),
    dict(slug='ucac2-idor', plant='coxykeel', ticket='COX-7', surface='UCAC2 star object-id IDOR', mod='ucac2s', model='Ucac2', lookup='ucac2', sample='UCAC2 12345678', owner='lab_id', first='mask', residual='export', product='ucac2-id', bug='COX-7 UCAC2 unique from USNO'),
    dict(slug='tycho1-idor', plant='cranykeel', ticket='CRA-8', surface='Tycho-1 object-id IDOR', mod='tyc1s', model='Tyc1', lookup='tyc1', sample='TYC 1234-567-1', owner='lab_id', first='any_member', residual='search', product='tycho1-id', bug='CRA-8 Tycho-1 unique from ESA'),
    dict(slug='allwise-rej-idor', plant='crinykeel', ticket='CRI-9', surface='AllWISE reject object-id IDOR', mod='allwiserejs', model='Allwiserej', lookup='allwiserej', sample='WISEA J053514.94-052353.9R', owner='lab_id', first='list_scope', residual='mget', product='allwise-rej', bug='CRI-9 reject unique from IRSA'),
    dict(slug='twomass-xsc-idor', plant='crosykeel', ticket='CRO-1', surface='2MASS XSC object-id IDOR', mod='twomassxscs', model='Twomassxsc', lookup='twomassxsc', sample='2MASX J05351494-0523539', owner='lab_id', first='authn', residual='csv', product='twomass-xsc', bug='CRO-1 XSC unique from IPAC'),
    dict(slug='ogle-var-idor', plant='crowykeel', ticket='CRO-2', surface='OGLE variable object-id IDOR', mod='oglevs', model='Oglev', lookup='oglev', sample='OGLE-LMC-CEP-0001', owner='lab_id', first='mask', residual='admin', product='ogle-var', bug='CRO-2 variable unique from OGLE'),
    dict(slug='asassn-idor', plant='cunnykeel', ticket='CUN-3', surface='ASAS-SN transient object-id IDOR', mod='asassns', model='Asassn', lookup='asassn', sample='ASASSN-24ab', owner='lab_id', first='any_member', residual='webhook', product='asassn-id', bug='CUN-3 name unique from ASAS-SN'),
    dict(slug='ztf-oid-idor', plant='cuttykeel', ticket='CUT-4', surface='ZTF object-id IDOR', mod='ztfoids', model='Ztfoid', lookup='ztfoid', sample='ZTF18aaaaaaa', owner='lab_id', first='list_scope', residual='comments', product='ztf-oid', bug='CUT-4 oid unique from ZTF'),
]


BFLA_ROWS = [
    dict(slug='fly-replay-skip-delete', plant='yawlkeel', ticket='YAW-1', surface='Fly.io replay DELETE missing fly-replay auth', family='js_route', skip="if (method==='DELETE') return notes.del(id)", auth="if (method==='GET') { if (!request.headers.get('fly-replay-src')) auth(); return notes.get(id, user) }", leftover='put'),
    dict(slug='envoy-lua-skip-delete', plant='yokekeel', ticket='YOK-2', surface='Envoy Lua filter skip DELETE', family='js_route', skip="function envoy_on_request(r) if r:headers():get(':method')=='DELETE' then return end", auth="function envoy_on_request(r) if r:headers():get('authorization')==nil then r:respond({[':status']='401'}) end", leftover='patch'),
    dict(slug='coredns-skip-delete', plant='yulokeel', ticket='YUL-3', surface='CoreDNS update skip plugin auth', family='js_route', skip='update {\n  policy tcp\n}', auth='acl {\n  allow net 10.0.0.0/8\n}', leftover='update'),
    dict(slug='bind9-update-skip-delete', plant='zabrkeel', ticket='ZAB-4', surface='BIND9 nsupdate DELETE missing TSIG', family='js_route', skip='update-policy { grant * wildcard * ANY; };', auth='update-policy { grant notes-key name notes.example.com ANY; };', leftover='put'),
    dict(slug='powerdns-skip-delete', plant='zulubkeel', ticket='ZUL-5', surface='PowerDNS DELETE missing API-Key', family='js_route', skip='DELETE /api/v1/servers/localhost/zones/notes  # no X-API-Key', auth='GET /api/v1/servers/localhost/zones/notes  X-API-Key required', leftover='patch'),
    dict(slug='knot-dns-skip-delete', plant='aftwkeel', ticket='AFT-6', surface='Knot DNS ddns skip ACL', family='js_route', skip='acl:\n  - id: open\n    address: 0.0.0.0/0\n    action: update', auth='acl:\n  - id: notes\n    key: notes-key\n    action: query', leftover='update'),
    dict(slug='nsd-skip-delete', plant='bagykeel', ticket='BAG-7', surface='NSD control delzone missing control-key', family='js_route', skip='nsd-control delzone notes.example  # no key', auth='nsd-control -c nsd.conf -y key zonestatus notes.example', leftover='put'),
    dict(slug='unbound-skip-delete', plant='balkykeel', ticket='BAL-8', surface='Unbound remote-control skip auth', family='js_route', skip='unbound-control flush_zone notes.example', auth='unbound-control-setup && unbound-control status', leftover='patch'),
    dict(slug='dnsmasq-skip-delete', plant='battykeel', ticket='BAT-9', surface='dnsmasq dhcp-host delete missing conf-script auth', family='js_route', skip='dhcp-host=id:*,ignore  # delete open', auth='conf-script=/usr/local/bin/auth-reload', leftover='update'),
    dict(slug='keepalived-skip-delete', plant='beamykeel', ticket='BEA-1', surface='Keepalived notify delete missing script user', family='js_route', skip='notify_stop /usr/local/bin/del-notes  # root unauth', auth='script_user keepalived keepalived\nnotify_master /usr/local/bin/auth-notes', leftover='put'),
    dict(slug='pacemaker-skip-delete', plant='bightykeel', ticket='BIG-2', surface='Pacemaker crm delete missing acl', family='js_route', skip='crm configure delete notes-rsc', auth='crm configure property enable-acl=true', leftover='patch'),
    dict(slug='corosync-skip-delete', plant='bilgykeel', ticket='BIL-3', surface='Corosync cmap delete missing uidgid', family='js_route', skip='corosync-cmapctl -D runtime.notes.id', auth='uidgid { uid: corosync gid: corosync }', leftover='update'),
    dict(slug='patroni-skip-delete', plant='bittykeel', ticket='BIT-4', surface='Patroni DELETE missing restapi auth', family='js_route', skip='DELETE /cluster  authentication: none', auth='restapi:\n  authentication:\n    username: admin', leftover='put'),
    dict(slug='stolon-skip-delete', plant='boomykeel', ticket='BOO-5', surface='Stolon cluster delete missing keeper auth', family='js_route', skip='stolonctl cluster remove --yes', auth='stolonctl --kube-resource-kind=configmap status', leftover='patch'),
    dict(slug='vitess-skip-delete', plant='bowykeel', ticket='BOW-6', surface='Vitess vtctl DeleteKeyspace missing auth', family='js_route', skip='vtctlclient DeleteKeyspace notes', auth='vtctlclient --grpc_auth_static_client_creds creds.json GetKeyspace notes', leftover='update'),
    dict(slug='tidb-skip-delete', plant='breezykeel', ticket='BRE-7', surface='TiDB DELETE missing privilege', family='sql', skip='DELETE FROM notes WHERE id=?;  -- user without privilege check skipped', auth="GRANT SELECT ON notes.* TO 'app'@'%';", leftover='put'),
    dict(slug='yugabyte-skip-delete', plant='bulkykeel', ticket='BUL-8', surface='Yugabyte YSQL DELETE missing GRANT', family='sql', skip='GRANT DELETE ON notes TO anon;', auth='GRANT SELECT ON notes TO app;', leftover='patch'),
    dict(slug='spanner-skip-delete', plant='buntykeel', ticket='BUN-9', surface='Spanner delete missing Fine-grained IAM', family='js_route', skip='session.executeDelete(Mutation.delete("notes", Key.of(id)))  # no iam', auth='database.getIamPolicy(); session.readRow("notes", Key.of(id), cols)', leftover='update'),
    dict(slug='cosmosdb-skip-delete', plant='cablykeel', ticket='CAB-1', surface='Cosmos DB delete missing resource token', family='js_route', skip='container.deleteItem(id, new PartitionKey(id))', auth='container.readItem(id, new PartitionKey(id), { resourceToken: token })', leftover='put'),
    dict(slug='firestore-skip-delete', plant='cambykeel', ticket='CAM-2', surface='Firestore delete missing rules', family='js_route', skip='match /notes/{id} { allow delete: if true; }', auth='match /notes/{id} { allow get: if request.auth.uid == resource.data.owner; }', leftover='patch'),
    dict(slug='bigtable-skip-delete', plant='cantykeel', ticket='CAN-3', surface='Bigtable dropRow missing IAM', family='js_route', skip='table.dropRow(rowkey)  # no iam', auth='table.readRow(rowkey, filters=authFilter(user))', leftover='update'),
    dict(slug='datastore-skip-delete', plant='captykeel', ticket='CAP-4', surface='Datastore delete missing namespace auth', family='js_route', skip='client.delete(key)', auth='client.get(key, namespace=user.ns)', leftover='put'),
    dict(slug='dynamodb-skip-delete', plant='carlykeel', ticket='CAR-5', surface='DynamoDB DeleteItem missing condition owner', family='js_route', skip="ddb.delete_item(Key={'id': id})", auth="ddb.get_item(Key={'id': id, 'owner': user})", leftover='patch'),
    dict(slug='documentdb-skip-delete', plant='cattykeel', ticket='CAT-6', surface='DocumentDB delete missing rbac', family='js_route', skip='db.notes.deleteOne({_id: id})', auth='db.notes.findOne({_id: id, owner: user})', leftover='update'),
    dict(slug='elasticache-skip-delete', plant='chainykeel', ticket='CHA-7', surface='ElastiCache DEL missing AUTH', family='js_route', skip="redis.del('notes:'+id)  # no AUTH", auth="redis.auth(token); redis.get('notes:'+id)", leftover='put'),
    dict(slug='memorystore-skip-delete', plant='cheekykeel', ticket='CHE-8', surface='Memorystore DEL missing AUTH', family='js_route', skip="r.delete('notes:'+id)", auth="r.auth(token); r.get('notes:'+id)", leftover='patch'),
    dict(slug='valkey-acl-skip-delete', plant='chockykeel', ticket='CHO-9', surface='Valkey ACL skip DEL', family='js_route', skip='ACL SETUSER anon +del ~notes:*', auth='ACL SETUSER app +get ~notes:* on >pass', leftover='update'),
    dict(slug='keydb-skip-delete', plant='clewykeel', ticket='CLE-1', surface='KeyDB DEL missing ACL', family='js_route', skip='DEL notes:id  # default user', auth='ACL SETUSER app on >pass ~notes:* +get', leftover='put'),
    dict(slug='dragonfly-skip-delete', plant='clinykeel', ticket='CLI-2', surface='Dragonfly DEL missing requirepass', family='js_route', skip='DEL notes:id', auth='AUTH token; GET notes:id', leftover='patch'),
    dict(slug='nats-auth-skip-delete', plant='coamykeel', ticket='COA-3', surface='NATS delete missing user JWT account', family='js_route', skip="js.DeleteStream('NOTES')  # no creds", auth='nc, _ := nats.Connect(url, nats.UserJWT(jwt, sig))', leftover='update'),
    dict(slug='nats-js-skip-delete', plant='cockykeel', ticket='COC-4', surface='NATS JetStream delete missing PurgeACL', family='js_route', skip="js.PurgeStream('NOTES')", auth="js.StreamInfo('NOTES', nats.BindStream('NOTES'))  // account jwt", leftover='put'),
    dict(slug='rabbitmq-skip-delete', plant='cordykeel', ticket='COR-5', surface='RabbitMQ delete queue missing management auth', family='js_route', skip='DELETE /api/queues/%2F/notes  # guest', auth='GET /api/queues/%2F/notes  basic auth user', leftover='patch'),
    dict(slug='kafka-acl-skip-delete', plant='countykeel', ticket='COU-6', surface='Kafka ACL skip DeleteTopics', family='js_route', skip="admin.deleteTopics(List.of('notes'))", auth='acl.bind(User:app, Topic:notes, READ, ALLOW)', leftover='update'),
    dict(slug='redpanda-skip-delete', plant='coxykeel', ticket='COX-7', surface='Redpanda delete topic missing SASL', family='js_route', skip='rpk topic delete notes  # no sasl', auth='rpk topic describe notes -X sasl.mechanism=SCRAM-SHA-256', leftover='put'),
    dict(slug='mqtt-acl-skip-delete', plant='cranykeel', ticket='CRA-8', surface='MQTT ACL skip $SYS delete', family='js_route', skip='acl { user all topic delete notes/# }', auth='acl { user app topic read notes/# }', leftover='patch'),
    dict(slug='emqx-skip-delete', plant='crinykeel', ticket='CRI-9', surface='EMQX delete rule missing dashboard auth', family='js_route', skip='DELETE /api/v5/rules/{id}  # anonymous', auth='GET /api/v5/rules/{id}  Authorization: Bearer', leftover='update'),
    dict(slug='vernemq-skip-delete', plant='crosykeel', ticket='CRO-1', surface='VerneMQ delete skip vmq_diversity auth', family='js_route', skip='vmq-admin session disconnect client-id=notes  # open', auth='vmq-admin listener start --ssl --cafile ca.pem', leftover='put'),
    dict(slug='mosquitto-skip-delete', plant='crowykeel', ticket='CRO-2', surface='Mosquitto ACL skip unsubscribe as delete', family='js_route', skip='acl_file /dev/null  # all delete', auth='acl_file /etc/mosquitto/acl\nuser app\ntopic read notes/#', leftover='patch'),
    dict(slug='pulsar-auth-skip-delete', plant='cunnykeel', ticket='CUN-3', surface='Pulsar admin delete missing token', family='js_route', skip='pulsar-admin topics delete persistent://p/n/notes', auth='pulsar-admin --auth-plugin org.apache.pulsar.client.impl.auth.AuthenticationToken topics list p/n', leftover='update'),
    dict(slug='redpanda-admin-skip-delete', plant='cuttykeel', ticket='CUT-4', surface='Redpanda admin DELETE missing basic auth', family='js_route', skip='DELETE /v1/topics/notes  # no auth', auth='GET /v1/topics/notes  Authorization: Basic', leftover='put'),
]


def extra_bflas(H):
    return [H(**_expand_bfla(row)) for row in BFLA_ROWS]


def _expand_bfla(row: dict) -> dict:
    plant = row["plant"]
    ticket = row["ticket"]
    slug = row["slug"]
    fw = row["surface"].split()[0]
    family = row["family"]
    skip = row["skip"]
    auth = row["auth"]
    leftover = row["leftover"]
    tag = ticket.split("-")[0].lower()
    src = f"src/{tag}_notes.py"
    handler = src
    test = f"tests/test_{tag}_delete.py"
    test_fn = "test_viewer_delete_403"
    src_fn = "delete"
    leftover_fn = leftover
    companion_path = f"src/{tag}_acl.py"
    src_obs = f"{skip}\n    # {ticket} {fw} delete skip\n"
    handler_obs = f"{auth}\n"
    inspect_obs = f"{src}: {src_fn} skip\n{test}: {test_fn}\n"
    test_obs = (
        "def test_viewer_delete_403(client, viewer, note):\n"
        "    client.login(viewer)\n"
        '    assert client.delete(f"/notes/{note.id}").status_code == 403\n'
    )
    first_apply = f"{fw} auth on list"
    first_path = src
    first_old = "def index():\n    return Note.list()"
    first_new = f"def index():\n    require_user()\n    return Note.list()  # {tag} list"
    first_obs = f"list gated; {src_fn} leftover skip"
    reflection = (
        f"{fw} list auth does not wrap delete. Gate {src_fn} plus owner, leave {leftover} if still skipped."
    )
    plan_change = f"auth on {src_fn}; owner abort"
    grep_pat = f"{src_fn}|{leftover_fn}"
    grep_obs = f"{src}: {src_fn} skip\n"
    legacy_path = src
    legacy_hint = f"{src_fn} skip"
    legacy_obs = src_obs
    legacy_old = skip.split("\n")[0] if False else skip
    # keep skip unique as old; new is auth+owner
    legacy_new = (
        f"{auth}\n"
        f"    n = Note.get(nid)\n"
        f"    if n.owner_id != user.id: abort(403)\n"
        f"    n.delete()  # {ticket} owner"
    )
    legacy_edit_obs = f"{src_fn} auth+owner"
    companion_old = "def owns(nid, uid): return True"
    companion_new = (
        "def owns(nid, uid):\n"
        "    n = Note.get_raw(nid)\n"
        "    return n is not None and n.owner_id == uid"
    )
    companion_obs = "owner"
    extra_fn = f"test_viewer_{leftover}_403"
    extra_old = "def test_viewer_delete_403(client, viewer, note):"
    extra_new = (
        f'@pytest.mark.xfail(reason="handoff: {leftover} still skipped", strict=False)\n'
        f"def {extra_fn}(client, viewer, note):\n"
        "    client.login(viewer)\n"
        f'    assert client.{leftover if leftover != "update" else "put"}(f"/notes/{{note.id}}", json={{}}).status_code == 403\n'
        "\n"
        "def test_viewer_delete_403(client, viewer, note):"
    )
    extra_obs = f"xfails {leftover} leftover"
    handoff_path = src
    handoff_obs = f"{skip.replace('delete', leftover, 1) if 'delete' in skip.lower() else skip}\n    # {leftover} still skipped\n"
    if leftover not in handoff_obs.lower() and leftover not in skip.lower():
        handoff_obs = f"# {leftover} still skipped\n{skip}\n"
    handoff_hint = f"{leftover} still skipped"
    residual = handoff_hint
    residual_path = src
    residual_pat = leftover_fn
    residual_obs = handoff_obs
    residual_refl = f"{src_fn} gated. {leftover} still skipped."
    leave_cmd = f"echo {ticket} handoff {fw} {leftover} skipped"
    leave_obs = f"{ticket} handoff {fw} {leftover} skipped"
    goal = (
        f"{plant}-notes DELETE /notes/{{id}} is 200 for a viewer because {fw} {src_fn} skips auth. "
        f"Require auth without 403ing owners. Leave a handoff if {leftover} still skips."
    )
    plan = f"{first_apply} and rerun {test}."
    outcome = (
        f"List auth left {src_fn} skipped. Plan change: auth+owner on {src_fn}. "
        f"Partial: {leftover} leftover (xfail handoff)."
    )
    return dict(
        slug=slug,
        plant=plant,
        surface=row["surface"],
        src=src,
        src_fn=src_fn,
        handler=handler,
        test=test,
        test_fn=test_fn,
        bug_hint=f"{fw} {src_fn} skips auth; list/get uses auth",
        inspect_obs=inspect_obs,
        src_obs=src_obs,
        handler_obs=handler_obs,
        test_obs=test_obs,
        first_apply=first_apply,
        first_path=first_path,
        first_old=first_old,
        first_new=first_new,
        first_obs=first_obs,
        reflection=reflection,
        plan_change=plan_change,
        grep_pat=grep_pat,
        grep_obs=grep_obs,
        legacy_path=legacy_path,
        legacy_hint=legacy_hint,
        legacy_obs=legacy_obs,
        legacy_old=skip,
        legacy_new=legacy_new,
        legacy_edit_obs=legacy_edit_obs,
        companion_path=companion_path,
        companion_old=companion_old,
        companion_new=companion_new,
        companion_obs=companion_obs,
        extra_fn=extra_fn,
        extra_old=extra_old,
        extra_new=extra_new,
        extra_obs=extra_obs,
        handoff_path=handoff_path,
        handoff_obs=handoff_obs,
        handoff_hint=handoff_hint,
        residual=residual,
        residual_path=residual_path,
        residual_pat=residual_pat,
        residual_obs=residual_obs,
        residual_refl=residual_refl,
        leave_cmd=leave_cmd,
        leave_obs=leave_obs,
        ticket=ticket,
        goal=goal,
        plan=plan,
        outcome=outcome,
    )
