"""Extra unique IDOR/BFLA plants for authz-regression-factory r2240+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r2239 vesselNNNN-sys.
Not clones of r2239 metar-v2 / rancher-d, r2160 iso3166-n3 / kind-cluster.
"""
from __future__ import annotations


EXTRA_IDOR_ROWS = [
    dict(slug='iccid-19-idor', plant='azv00yard', ticket='AZ1-1', surface='ICCID-19 object-id IDOR', mod='iccid19xxxs82', model='Iccid19xxxN', lookup='iccid19xxxl82', sample='89014103211118510720', owner='lab_id', first='authn', residual='pdf', product='iccid-19', bug='AZ1-1 ICCID unique from ITU'),
    dict(slug='imeisv-idor', plant='azv01yard', ticket='AZ2-2', surface='IMEI-SV object-id IDOR', mod='imeisvxxxxs82', model='ImeisvxxxxN', lookup='imeisvxxxxl82', sample='3598270612345671', owner='mmsi_id', first='mask', residual='export', product='imeisv', bug='AZ2-2 SV unique from 3GPP'),
    dict(slug='meidhex-idor', plant='azv02yard', ticket='AZ3-3', surface='MEID hex object-id IDOR', mod='meidhexxxxs82', model='MeidhexxxxN', lookup='meidhexxxxl82', sample='A0000004B0F3D1', owner='mmsi_id', first='any_member', residual='search', product='meidhex', bug='AZ3-3 MEID unique from TIA'),
    dict(slug='eui64-mac-idor', plant='azv03yard', ticket='AZ4-4', surface='EUI-64 object-id IDOR', mod='eui64macxxs82', model='Eui64macxxN', lookup='eui64macxxl82', sample='021122FFFE334455', owner='lab_id', first='list_scope', residual='mget', product='eui64-mac', bug='AZ4-4 EUI unique from IEEE'),
    dict(slug='macoui-idor', plant='azv04yard', ticket='AZ5-5', surface='MAC OUI object-id IDOR', mod='macouixxxxs82', model='MacouixxxxN', lookup='macouixxxxl82', sample='00:1A:2B', owner='lab_id', first='authn', residual='csv', product='macoui', bug='AZ5-5 OUI unique from IEEE'),
    dict(slug='ulid26-idor', plant='azv05yard', ticket='AZ6-6', surface='ULID object-id IDOR', mod='ulid26xxxxs82', model='Ulid26xxxxN', lookup='ulid26xxxxl82', sample='01ARZ3NDEKTSV4RRFFQ69G5FAV', owner='lab_id', first='mask', residual='admin', product='ulid26', bug='AZ6-6 ULID unique from ULID'),
    dict(slug='ksuid-idor', plant='azv06yard', ticket='AZ7-7', surface='KSUID object-id IDOR', mod='ksuidxxxxxs82', model='KsuidxxxxxN', lookup='ksuidxxxxxl82', sample='0ujtsYcgvSTl8PAuAdqWYSMnLOv', owner='lab_id', first='any_member', residual='webhook', product='ksuid', bug='AZ7-7 KSUID unique from Segment'),
    dict(slug='snowflake-idor', plant='azv07yard', ticket='AZ8-8', surface='Snowflake id object-id IDOR', mod='snowflakexs82', model='SnowflakexN', lookup='snowflakexl82', sample='1541815603606036480', owner='lab_id', first='list_scope', residual='comments', product='snowflake', bug='AZ8-8 id unique from Twitter'),
    dict(slug='xid20-idor', plant='azv08yard', ticket='AZ9-9', surface='XID object-id IDOR', mod='xid20xxxxxs82', model='Xid20xxxxxN', lookup='xid20xxxxxl82', sample='9m4e2mr0ui3e8a215n4g', owner='lab_id', first='authn', residual='pdf', product='xid20', bug='AZ9-9 XID unique from rs'),
    dict(slug='cuid2-idor', plant='azv09yard', ticket='AZ1-10', surface='CUID2 object-id IDOR', mod='cuid2xxxxxs82', model='Cuid2xxxxxN', lookup='cuid2xxxxxl82', sample='tz4a98xxat96iws9zmbrgj3a', owner='lab_id', first='mask', residual='export', product='cuid2', bug='AZ1-10 CUID unique from paralleldrive'),
    dict(slug='nanoid-idor', plant='azv10yard', ticket='AZ2-11', surface='NanoID object-id IDOR', mod='nanoidxxxxs82', model='NanoidxxxxN', lookup='nanoidxxxxl82', sample='V1StGXR8_Z5jdHi6B-myT', owner='lab_id', first='any_member', residual='search', product='nanoid', bug='AZ2-11 id unique from ai'),
    dict(slug='uuidv7-idor', plant='azv11yard', ticket='AZ3-12', surface='UUIDv7 object-id IDOR', mod='uuidv7xxxxs82', model='Uuidv7xxxxN', lookup='uuidv7xxxxl82', sample='018f1e3c-7b4a-7c00-8d1e-2f3a4b5c6d7e', owner='lab_id', first='list_scope', residual='mget', product='uuidv7', bug='AZ3-12 UUID unique from IETF'),
    dict(slug='typeid-idor', plant='azv12yard', ticket='AZ4-13', surface='TypeID object-id IDOR', mod='typeidxxxxs82', model='TypeidxxxxN', lookup='typeidxxxxl82', sample='user_01h45ytscbebyvny4snc7gww3y', owner='lab_id', first='authn', residual='csv', product='typeid', bug='AZ4-13 TypeID unique from jetify'),
    dict(slug='sqid-idor', plant='azv13yard', ticket='AZ5-14', surface='Sqid object-id IDOR', mod='sqidxxxxxxs82', model='SqidxxxxxxN', lookup='sqidxxxxxxl82', sample='86Rf07xd4z', owner='lab_id', first='mask', residual='admin', product='sqid', bug='AZ5-14 Sqid unique from sqids'),
    dict(slug='hashid-idor', plant='azv14yard', ticket='AZ6-15', surface='Hashid object-id IDOR', mod='hashidxxxxs82', model='HashidxxxxN', lookup='hashidxxxxl82', sample='jR', owner='lab_id', first='any_member', residual='webhook', product='hashid', bug='AZ6-15 Hashid unique from hashids'),
    dict(slug='btc-p2pkh-idor', plant='azv15yard', ticket='AZ7-16', surface='BTC P2PKH object-id IDOR', mod='btcp2pkhxxs82', model='Btcp2pkhxxN', lookup='btcp2pkhxxl82', sample='1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa', owner='bank_id', first='list_scope', residual='comments', product='btc-p2pkh', bug='AZ7-16 P2PKH unique from Bitcoin'),
    dict(slug='eth-ea-idor', plant='azv16yard', ticket='AZ8-17', surface='ETH EOA object-id IDOR', mod='etheaxxxxxs82', model='EtheaxxxxxN', lookup='etheaxxxxxl82', sample='0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe', owner='bank_id', first='authn', residual='pdf', product='eth-ea', bug='AZ8-17 EOA unique from Ethereum'),
    dict(slug='ens-node-idor', plant='azv17yard', ticket='AZ9-18', surface='ENS node object-id IDOR', mod='ensnodexxxs82', model='EnsnodexxxN', lookup='ensnodexxxl82', sample='vitalik.eth', owner='bank_id', first='mask', residual='export', product='ens-node', bug='AZ9-18 node unique from ENS'),
    dict(slug='sol-base58-idor', plant='azv18yard', ticket='AZ1-19', surface='Solana base58 object-id IDOR', mod='solbase58xs82', model='Solbase58xN', lookup='solbase58xl82', sample='7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU', owner='bank_id', first='any_member', residual='search', product='sol-base58', bug='AZ1-19 addr unique from Solana'),
    dict(slug='bech32m-idor', plant='azv19yard', ticket='AZ2-20', surface='Bech32m object-id IDOR', mod='bech32mxxxs82', model='Bech32mxxxN', lookup='bech32mxxxl82', sample='bc1p5d7rjq7g6rdk2yhzks9smlaqtedr4dekq08ge8', owner='bank_id', first='list_scope', residual='mget', product='bech32m', bug='AZ2-20 addr unique from BIP350'),
    dict(slug='txid256-idor', plant='azv20yard', ticket='AZ3-21', surface='Txid-256 object-id IDOR', mod='txid256xxxs82', model='Txid256xxxN', lookup='txid256xxxl82', sample='4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b', owner='bank_id', first='authn', residual='csv', product='txid256', bug='AZ3-21 txid unique from Bitcoin'),
    dict(slug='evm-ca-idor', plant='azv21yard', ticket='AZ4-22', surface='EVM contract object-id IDOR', mod='evmcaxxxxxs82', model='EvmcaxxxxxN', lookup='evmcaxxxxxl82', sample='0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', owner='bank_id', first='mask', residual='admin', product='evm-ca', bug='AZ4-22 CA unique from Ethereum'),
    dict(slug='near-acct-idor', plant='azv22yard', ticket='AZ5-23', surface='NEAR account object-id IDOR', mod='nearacctxxs82', model='NearacctxxN', lookup='nearacctxxl82', sample='alice.near', owner='bank_id', first='any_member', residual='webhook', product='near-acct', bug='AZ5-23 acct unique from NEAR'),
    dict(slug='atom-bech-idor', plant='azv23yard', ticket='AZ6-24', surface='Cosmos bech32 object-id IDOR', mod='atombechxxs82', model='AtombechxxN', lookup='atombechxxl82', sample='cosmos1qypqxpq9qcrsszg2pvxq6rs0zqg3yyc5z5tp7z', owner='bank_id', first='list_scope', residual='comments', product='atom-bech', bug='AZ6-24 addr unique from Cosmos'),
    dict(slug='dot-ss58-idor', plant='azv24yard', ticket='AZ7-25', surface='Polkadot SS58 object-id IDOR', mod='dotss58xxxs82', model='Dotss58xxxN', lookup='dotss58xxxl82', sample='15oF4uVJwmo4TdGW7VfQxSTvjLvoS9dZtN', owner='bank_id', first='authn', residual='pdf', product='dot-ss58', bug='AZ7-25 SS58 unique from Polkadot'),
    dict(slug='vin-wmi-idor', plant='azv25yard', ticket='AZ8-26', surface='VIN WMI object-id IDOR', mod='vinwmixxxxs82', model='VinwmixxxxN', lookup='vinwmixxxxl82', sample='1HG', owner='trade_id', first='mask', residual='export', product='vin-wmi', bug='AZ8-26 WMI unique from ISO'),
    dict(slug='vin17-idor', plant='azv26yard', ticket='AZ9-27', surface='VIN-17 object-id IDOR', mod='vin17xxxxxs82', model='Vin17xxxxxN', lookup='vin17xxxxxl82', sample='1HGCM82633A004352', owner='trade_id', first='any_member', residual='search', product='vin17', bug='AZ9-27 VIN unique from ISO'),
    dict(slug='uspto-pn-idor', plant='azv27yard', ticket='AZ1-28', surface='USPTO patent object-id IDOR', mod='usptopnxxxs82', model='UsptopnxxxN', lookup='usptopnxxxl82', sample='11234567', owner='lab_id', first='list_scope', residual='mget', product='uspto-pn', bug='AZ1-28 PN unique from USPTO'),
    dict(slug='epodoc-idor', plant='azv28yard', ticket='AZ2-29', surface='EPODOC object-id IDOR', mod='epodocxxxxs82', model='EpodocxxxxN', lookup='epodocxxxxl82', sample='EP1000000A1', owner='lab_id', first='authn', residual='csv', product='epodoc', bug='AZ2-29 doc unique from EPO'),
    dict(slug='cpc-sym-idor', plant='azv29yard', ticket='AZ3-30', surface='CPC symbol object-id IDOR', mod='cpcsymxxxxs82', model='CpcsymxxxxN', lookup='cpcsymxxxxl82', sample='G06F21/62', owner='lab_id', first='mask', residual='admin', product='cpc-sym', bug='AZ3-30 CPC unique from EPO'),
    dict(slug='ipc-sym-idor', plant='azv30yard', ticket='AZ4-31', surface='IPC symbol object-id IDOR', mod='ipcsymxxxxs82', model='IpcsymxxxxN', lookup='ipcsymxxxxl82', sample='H04L9/32', owner='lab_id', first='any_member', residual='webhook', product='ipc-sym', bug='AZ4-31 IPC unique from WIPO'),
    dict(slug='isrc-idor', plant='azv31yard', ticket='AZ5-32', surface='ISRC object-id IDOR', mod='isrcxxxxxxs82', model='IsrcxxxxxxN', lookup='isrcxxxxxxl82', sample='USRC17607839', owner='lab_id', first='list_scope', residual='comments', product='isrc', bug='AZ5-32 ISRC unique from IFPI'),
    dict(slug='iswc-idor', plant='azv32yard', ticket='AZ6-33', surface='ISWC object-id IDOR', mod='iswcxxxxxxs82', model='IswcxxxxxxN', lookup='iswcxxxxxxl82', sample='T-034.524.680-1', owner='lab_id', first='authn', residual='pdf', product='iswc', bug='AZ6-33 ISWC unique from CISAC'),
    dict(slug='isan-idor', plant='azv33yard', ticket='AZ7-34', surface='ISAN object-id IDOR', mod='isanxxxxxxs82', model='IsanxxxxxxN', lookup='isanxxxxxxl82', sample='0000-0000-3A8D-0000-Q-0000-0000-E', owner='lab_id', first='mask', residual='export', product='isan', bug='AZ7-34 ISAN unique from ISAN'),
    dict(slug='rfc-num-idor', plant='azv34yard', ticket='AZ8-35', surface='RFC number object-id IDOR', mod='rfcnumxxxxs82', model='RfcnumxxxxN', lookup='rfcnumxxxxl82', sample='9110', owner='lab_id', first='any_member', residual='search', product='rfc-num', bug='AZ8-35 RFC unique from IETF'),
    dict(slug='cve-y-idor', plant='azv35yard', ticket='AZ9-36', surface='CVE-Y object-id IDOR', mod='cveyxxxxxxs82', model='CveyxxxxxxN', lookup='cveyxxxxxxl82', sample='CVE-2024-3094', owner='lab_id', first='list_scope', residual='mget', product='cve-y', bug='AZ9-36 CVE unique from MITRE'),
    dict(slug='cwe-id-idor', plant='azv36yard', ticket='AZ1-37', surface='CWE id object-id IDOR', mod='cweidxxxxxs82', model='CweidxxxxxN', lookup='cweidxxxxxl82', sample='CWE-639', owner='lab_id', first='authn', residual='csv', product='cwe-id', bug='AZ1-37 CWE unique from MITRE'),
    dict(slug='cpe23-idor', plant='azv37yard', ticket='AZ2-38', surface='CPE 2.3 object-id IDOR', mod='cpe23xxxxxs82', model='Cpe23xxxxxN', lookup='cpe23xxxxxl82', sample='cpe:2.3:a:openssl:openssl:3.0.0', owner='lab_id', first='mask', residual='admin', product='cpe23', bug='AZ2-38 CPE unique from NIST'),
    dict(slug='ski-x509-idor', plant='azv38yard', ticket='AZ3-39', surface='X.509 SKI object-id IDOR', mod='skix509xxxs82', model='Skix509xxxN', lookup='skix509xxxl82', sample='1a:2b:3c:4d:5e', owner='lab_id', first='any_member', residual='webhook', product='ski-x509', bug='AZ3-39 SKI unique from RFC5280'),
    dict(slug='x509-sn-idor', plant='azv39yard', ticket='AZ4-40', surface='X.509 serial object-id IDOR', mod='x509snxxxxs82', model='X509snxxxxN', lookup='x509snxxxxl82', sample='0x1a2b3c4d', owner='lab_id', first='list_scope', residual='comments', product='x509-sn', bug='AZ4-40 serial unique from RFC5280'),
    dict(slug='ocsp-cid-idor', plant='azv40yard', ticket='AZ5-41', surface='OCSP certid object-id IDOR', mod='ocspcidxxxs82', model='OcspcidxxxN', lookup='ocspcidxxxl82', sample='sha1:deadbeef', owner='lab_id', first='authn', residual='pdf', product='ocsp-cid', bug='AZ5-41 certid unique from RFC6960'),
    dict(slug='spki-pin-idor', plant='azv41yard', ticket='AZ6-42', surface='SPKI pin object-id IDOR', mod='spkipinxxxs82', model='SpkipinxxxN', lookup='spkipinxxxl82', sample='sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=', owner='lab_id', first='mask', residual='export', product='spki-pin', bug='AZ6-42 pin unique from RFC7469'),
    dict(slug='aki-x509-idor', plant='azv42yard', ticket='AZ7-43', surface='X.509 AKI object-id IDOR', mod='akix509xxxs82', model='Akix509xxxN', lookup='akix509xxxl82', sample='keyid:1a2b3c', owner='lab_id', first='any_member', residual='search', product='aki-x509', bug='AZ7-43 AKI unique from RFC5280'),
    dict(slug='dnskey-idor', plant='azv43yard', ticket='AZ8-44', surface='DNSKEY tag object-id IDOR', mod='dnskeyxxxxs82', model='DnskeyxxxxN', lookup='dnskeyxxxxl82', sample='2371', owner='lab_id', first='list_scope', residual='mget', product='dnskey', bug='AZ8-44 tag unique from RFC4034'),
    dict(slug='dsrr-idor', plant='azv44yard', ticket='AZ9-45', surface='DS RR object-id IDOR', mod='dsrrxxxxxxs82', model='DsrrxxxxxxN', lookup='dsrrxxxxxxl82', sample='2371 13 2 AABBCC', owner='lab_id', first='authn', residual='csv', product='dsrr', bug='AZ9-45 DS unique from RFC4034'),
    dict(slug='nsec3-idor', plant='azv45yard', ticket='AZ1-46', surface='NSEC3 hash object-id IDOR', mod='nsec3xxxxxs82', model='Nsec3xxxxxN', lookup='nsec3xxxxxl82', sample='1a2b3c4d', owner='lab_id', first='mask', residual='admin', product='nsec3', bug='AZ1-46 hash unique from RFC5155'),
    dict(slug='epp-roid-idor', plant='azv46yard', ticket='AZ2-47', surface='EPP ROID object-id IDOR', mod='epproidxxxs82', model='EpproidxxxN', lookup='epproidxxxl82', sample='EXAMPLE-REP', owner='lab_id', first='any_member', residual='webhook', product='epp-roid', bug='AZ2-47 ROID unique from RFC5730'),
    dict(slug='iana-pen-idor', plant='azv47yard', ticket='AZ3-48', surface='IANA PEN object-id IDOR', mod='ianapenxxxs82', model='IanapenxxxN', lookup='ianapenxxxl82', sample='343', owner='lab_id', first='list_scope', residual='comments', product='iana-pen', bug='AZ3-48 PEN unique from IANA'),
    dict(slug='cospar-idor', plant='azv48yard', ticket='AZ4-49', surface='COSPAR id object-id IDOR', mod='cosparxxxxs82', model='CosparxxxxN', lookup='cosparxxxxl82', sample='1998-067A', owner='lab_id', first='authn', residual='pdf', product='cospar', bug='AZ4-49 id unique from COSPAR'),
    dict(slug='satnogs-idor', plant='azv49yard', ticket='AZ5-50', surface='SatNOGS object-id IDOR', mod='satnogsxxxs82', model='SatnogsxxxN', lookup='satnogsxxxl82', sample='25544', owner='lab_id', first='mask', residual='export', product='satnogs', bug='AZ5-50 id unique from SatNOGS'),
    dict(slug='tle-sat-idor', plant='azv50yard', ticket='AZ6-51', surface='TLE satnum object-id IDOR', mod='tlesatxxxxs82', model='TlesatxxxxN', lookup='tlesatxxxxl82', sample='25544', owner='lab_id', first='any_member', residual='search', product='tle-sat', bug='AZ6-51 satnum unique from Celestrak'),
    dict(slug='nssdc-idor', plant='azv51yard', ticket='AZ7-52', surface='NSSDC id object-id IDOR', mod='nssdcxxxxxs82', model='NssdcxxxxxN', lookup='nssdcxxxxxl82', sample='1998-067A', owner='lab_id', first='list_scope', residual='mget', product='nssdc', bug='AZ7-52 id unique from NASA'),
    dict(slug='uic-crs-idor', plant='azv52yard', ticket='AZ8-53', surface='UIC CRS object-id IDOR', mod='uiccrsxxxxs82', model='UiccrsxxxxN', lookup='uiccrsxxxxl82', sample='8503000', owner='geo_id', first='authn', residual='csv', product='uic-crs', bug='AZ8-53 CRS unique from UIC'),
    dict(slug='rsrid-idor', plant='azv53yard', ticket='AZ9-54', surface='RSRID object-id IDOR', mod='rsridxxxxxs82', model='RsridxxxxxN', lookup='rsridxxxxxl82', sample='12345', owner='geo_id', first='mask', residual='admin', product='rsrid', bug='AZ9-54 id unique from Network Rail'),
    dict(slug='aar-mark-idor', plant='azv54yard', ticket='AZ1-55', surface='AAR mark object-id IDOR', mod='aarmarkxxxs82', model='AarmarkxxxN', lookup='aarmarkxxxl82', sample='UP', owner='geo_id', first='any_member', residual='webhook', product='aar-mark', bug='AZ1-55 mark unique from AAR'),
    dict(slug='uic-loc-idor', plant='azv55yard', ticket='AZ2-56', surface='UIC location object-id IDOR', mod='uiclocxxxxs82', model='UiclocxxxxN', lookup='uiclocxxxxl82', sample='008500300', owner='geo_id', first='list_scope', residual='comments', product='uic-loc', bug='AZ2-56 loc unique from UIC'),
    dict(slug='naptan-idor', plant='azv56yard', ticket='AZ3-57', surface='NaPTAN object-id IDOR', mod='naptanxxxxs82', model='NaptanxxxxN', lookup='naptanxxxxl82', sample='490000077E', owner='geo_id', first='authn', residual='pdf', product='naptan', bug='AZ3-57 stop unique from DFT'),
    dict(slug='npi10-idor', plant='azv57yard', ticket='AZ4-58', surface='NPI-10 object-id IDOR', mod='npi10xxxxxs82', model='Npi10xxxxxN', lookup='npi10xxxxxl82', sample='1234567893', owner='lab_id', first='mask', residual='export', product='npi10', bug='AZ4-58 NPI unique from CMS'),
    dict(slug='ein-irs-idor', plant='azv58yard', ticket='AZ5-59', surface='EIN IRS object-id IDOR', mod='einirsxxxxs82', model='EinirsxxxxN', lookup='einirsxxxxl82', sample='12-3456789', owner='bank_id', first='any_member', residual='search', product='ein-irs', bug='AZ5-59 EIN unique from IRS'),
    dict(slug='naics-idor', plant='azv59yard', ticket='AZ6-60', surface='NAICS object-id IDOR', mod='naicsxxxxxs82', model='NaicsxxxxxN', lookup='naicsxxxxxl82', sample='541511', owner='bank_id', first='list_scope', residual='mget', product='naics', bug='AZ6-60 NAICS unique from Census'),
    dict(slug='iso6523-idor', plant='azv60yard', ticket='AZ7-61', surface='ISO 6523 ICD object-id IDOR', mod='iso6523xxxs82', model='Iso6523xxxN', lookup='iso6523xxxl82', sample='0060', owner='bank_id', first='authn', residual='csv', product='iso6523', bug='AZ7-61 ICD unique from ISO'),
    dict(slug='lei-elf-idor', plant='azv61yard', ticket='AZ8-62', surface='LEI ELF object-id IDOR', mod='leielfxxxxs82', model='LeielfxxxxN', lookup='leielfxxxxl82', sample='8888', owner='bank_id', first='mask', residual='admin', product='lei-elf', bug='AZ8-62 ELF unique from GLEIF'),
    dict(slug='gln-sgln-idor', plant='azv62yard', ticket='AZ9-63', surface='SGLN object-id IDOR', mod='glnsglnxxxs82', model='GlnsglnxxxN', lookup='glnsglnxxxl82', sample='0614141.12345.0', owner='trade_id', first='any_member', residual='webhook', product='gln-sgln', bug='AZ9-63 SGLN unique from GS1'),
    dict(slug='plu4-idor', plant='azv63yard', ticket='AZ1-64', surface='PLU-4 object-id IDOR', mod='plu4xxxxxxs82', model='Plu4xxxxxxN', lookup='plu4xxxxxxl82', sample='4011', owner='trade_id', first='list_scope', residual='comments', product='plu4', bug='AZ1-64 PLU unique from IFPS'),
    dict(slug='fao-crop-idor', plant='azv64yard', ticket='AZ2-65', surface='FAO crop object-id IDOR', mod='faocropxxxs82', model='FaocropxxxN', lookup='faocropxxxl82', sample='15', owner='trade_id', first='authn', residual='pdf', product='fao-crop', bug='AZ2-65 crop unique from FAO'),
    dict(slug='usda-fgis-idor', plant='azv65yard', ticket='AZ3-66', surface='USDA FGIS object-id IDOR', mod='usdafgisxxs82', model='UsdafgisxxN', lookup='usdafgisxxl82', sample='12345', owner='trade_id', first='mask', residual='export', product='usda-fgis', bug='AZ3-66 id unique from USDA'),
    dict(slug='codex-idor', plant='azv66yard', ticket='AZ4-67', surface='Codex GSFA object-id IDOR', mod='codexxxxxxs82', model='CodexxxxxxN', lookup='codexxxxxxl82', sample='INS-330', owner='trade_id', first='any_member', residual='search', product='codex', bug='AZ4-67 INS unique from Codex'),
    dict(slug='naic-co-idor', plant='azv67yard', ticket='AZ5-68', surface='NAIC company object-id IDOR', mod='naiccoxxxxs82', model='NaiccoxxxxN', lookup='naiccoxxxxl82', sample='12345', owner='bank_id', first='list_scope', residual='mget', product='naic-co', bug='AZ5-68 co unique from NAIC'),
    dict(slug='swift-fin-idor', plant='azv68yard', ticket='AZ6-69', surface='SWIFT FIN object-id IDOR', mod='swiftfinxxs82', model='SwiftfinxxN', lookup='swiftfinxxl82', sample='FIN-103', owner='bank_id', first='authn', residual='csv', product='swift-fin', bug='AZ6-69 FIN unique from SWIFT'),
    dict(slug='mic-iso-idor', plant='azv69yard', ticket='AZ7-70', surface='ISO 10383 MIC object-id IDOR', mod='micisoxxxxs82', model='MicisoxxxxN', lookup='micisoxxxxl82', sample='XNYS', owner='bank_id', first='mask', residual='admin', product='mic-iso', bug='AZ7-70 MIC unique from ISO'),
    dict(slug='isin-idor', plant='azv70yard', ticket='AZ8-71', surface='ISIN object-id IDOR', mod='isinxxxxxxs82', model='IsinxxxxxxN', lookup='isinxxxxxxl82', sample='US0378331005', owner='bank_id', first='any_member', residual='webhook', product='isin', bug='AZ8-71 ISIN unique from ISO'),
    dict(slug='tzdb-idor', plant='azv71yard', ticket='AZ9-72', surface='tzdb object-id IDOR', mod='tzdbxxxxxxs82', model='TzdbxxxxxxN', lookup='tzdbxxxxxxl82', sample='America/New_York', owner='geo_id', first='list_scope', residual='comments', product='tzdb', bug='AZ9-72 zone unique from IANA'),
    dict(slug='iana-lang-idor', plant='azv72yard', ticket='AZ1-73', surface='IANA language object-id IDOR', mod='ianalangxxs82', model='IanalangxxN', lookup='ianalangxxl82', sample='en-US', owner='lab_id', first='authn', residual='pdf', product='iana-lang', bug='AZ1-73 tag unique from IANA'),
    dict(slug='bcp47-idor', plant='azv73yard', ticket='AZ2-74', surface='BCP47 object-id IDOR', mod='bcp47xxxxxs82', model='Bcp47xxxxxN', lookup='bcp47xxxxxl82', sample='zh-Hans-CN', owner='lab_id', first='mask', residual='export', product='bcp47', bug='AZ2-74 tag unique from IETF'),
    dict(slug='cldr-tz-idor', plant='azv74yard', ticket='AZ3-75', surface='CLDR TZ object-id IDOR', mod='cldrtzxxxxs82', model='CldrtzxxxxN', lookup='cldrtzxxxxl82', sample='America_New_York', owner='geo_id', first='any_member', residual='search', product='cldr-tz', bug='AZ3-75 TZ unique from Unicode'),
    dict(slug='fcc-frn-idor', plant='azv75yard', ticket='AZ4-76', surface='FCC FRN object-id IDOR', mod='fccfrnxxxxs82', model='FccfrnxxxxN', lookup='fccfrnxxxxl82', sample='0001234567', owner='lab_id', first='list_scope', residual='mget', product='fcc-frn', bug='AZ4-76 FRN unique from FCC'),
    dict(slug='imo-num-idor', plant='azv76yard', ticket='AZ5-77', surface='IMO number object-id IDOR', mod='imonumxxxxs82', model='ImonumxxxxN', lookup='imonumxxxxl82', sample='9074729', owner='mmsi_id', first='authn', residual='csv', product='imo-num', bug='AZ5-77 IMO unique from IMO'),
    dict(slug='icao24-idor', plant='azv77yard', ticket='AZ6-78', surface='ICAO 24-bit object-id IDOR', mod='icao24xxxxs82', model='Icao24xxxxN', lookup='icao24xxxxl82', sample='a1b2c3', owner='mmsi_id', first='mask', residual='admin', product='icao24', bug='AZ6-78 addr unique from ICAO'),
    dict(slug='mode-s-idor', plant='azv78yard', ticket='AZ7-79', surface='Mode-S object-id IDOR', mod='modesxxxxxs82', model='ModesxxxxxN', lookup='modesxxxxxl82', sample='ADF123', owner='mmsi_id', first='any_member', residual='webhook', product='mode-s', bug='AZ7-79 addr unique from ICAO'),
    dict(slug='tailn-n-idor', plant='azv79yard', ticket='AZ8-80', surface='N-number object-id IDOR', mod='tailnnxxxxs82', model='TailnnxxxxN', lookup='tailnnxxxxl82', sample='N12345', owner='mmsi_id', first='list_scope', residual='comments', product='tailn-n', bug='AZ8-80 N unique from FAA'),
]


BFLA_ROWS = [
    dict(slug='jenkins-job-skip-delete', plant='azv00yard', ticket='AZ1-1', surface='Jenkins job delete missing crumb', family='js_route', skip='java -jar jenkins-cli.jar delete-job notes', auth='java -jar jenkins-cli.jar get-job notes', leftover='put'),
    dict(slug='gitlab-proj-skip-delete', plant='azv01yard', ticket='AZ2-2', surface='GitLab project delete missing token', family='js_route', skip='glab repo delete notes --yes', auth='glab repo view notes', leftover='patch'),
    dict(slug='gha-run-skip-delete', plant='azv02yard', ticket='AZ3-3', surface='GHA run delete missing token', family='js_route', skip='gh run delete notes', auth='gh run view notes', leftover='update'),
    dict(slug='tekton-pr-skip-delete', plant='azv03yard', ticket='AZ4-4', surface='Tekton PipelineRun delete missing rbac', family='js_route', skip='kubectl delete pipelinerun notes', auth='kubectl get pipelinerun notes', leftover='put'),
    dict(slug='drone-repo-skip-delete', plant='azv04yard', ticket='AZ5-5', surface='Drone repo delete missing token', family='js_route', skip='drone repo rm notes', auth='drone repo info notes', leftover='patch'),
    dict(slug='gitea-repo-skip-delete', plant='azv05yard', ticket='AZ6-6', surface='Gitea repo delete missing token', family='js_route', skip='tea repos delete notes', auth='tea repos view notes', leftover='update'),
    dict(slug='forgejo-skip-delete', plant='azv06yard', ticket='AZ7-7', surface='Forgejo repo delete missing token', family='js_route', skip='forgejo repo delete notes --yes', auth='forgejo repo view notes', leftover='put'),
    dict(slug='travis-ci-skip-delete', plant='azv07yard', ticket='AZ8-8', surface='Travis repo delete missing token', family='js_route', skip='travis disable notes', auth='travis show notes', leftover='patch'),
    dict(slug='appveyor-skip-delete', plant='azv08yard', ticket='AZ9-9', surface='AppVeyor project delete missing token', family='js_route', skip='appveyor project delete notes', auth='appveyor project get notes', leftover='update'),
    dict(slug='azdo-pipe-skip-delete', plant='azv09yard', ticket='AZ1-10', surface='Azure DevOps pipeline delete missing pat', family='js_route', skip='az pipelines delete --id notes --yes', auth='az pipelines show --id notes', leftover='put'),
    dict(slug='codebuild-skip-delete', plant='azv10yard', ticket='AZ2-11', surface='CodeBuild project delete missing aws', family='js_route', skip='aws codebuild delete-project --name notes', auth='aws codebuild batch-get-projects --names notes', leftover='patch'),
    dict(slug='codepipe-skip-delete', plant='azv11yard', ticket='AZ3-12', surface='CodePipeline delete missing aws', family='js_route', skip='aws codepipeline delete-pipeline --name notes', auth='aws codepipeline get-pipeline --name notes', leftover='update'),
    dict(slug='gcb-skip-delete', plant='azv12yard', ticket='AZ4-13', surface='Cloud Build trigger delete missing adc', family='js_route', skip='gcloud builds triggers delete notes --quiet', auth='gcloud builds triggers describe notes', leftover='put'),
    dict(slug='tf-state-skip-delete', plant='azv13yard', ticket='AZ5-14', surface='Terraform state rm missing token', family='js_route', skip='terraform state rm notes', auth='terraform state show notes', leftover='patch'),
    dict(slug='pulumi-st-skip-delete', plant='azv14yard', ticket='AZ6-15', surface='Pulumi stack delete missing token', family='js_route', skip='pulumi stack rm notes --yes', auth='pulumi stack --show-name notes', leftover='update'),
    dict(slug='puppet-nd-skip-delete', plant='azv15yard', ticket='AZ7-16', surface='Puppet node deactivate missing cert', family='js_route', skip='puppet node deactivate notes', auth='puppet node status notes', leftover='put'),
    dict(slug='salt-minion-skip-delete', plant='azv16yard', ticket='AZ8-17', surface='Salt key delete missing master', family='js_route', skip='salt-key -d notes -y', auth='salt-key -f notes', leftover='patch'),
    dict(slug='vagrant-bx-skip-delete', plant='azv17yard', ticket='AZ9-18', surface='Vagrant box remove missing home', family='js_route', skip='vagrant box remove notes --force', auth='vagrant box list', leftover='update'),
    dict(slug='vault-sec-skip-delete', plant='azv18yard', ticket='AZ1-19', surface='Vault secret delete missing token', family='js_route', skip='vault kv delete secret/notes', auth='vault kv get secret/notes', leftover='put'),
    dict(slug='waypoint-skip-delete', plant='azv19yard', ticket='AZ2-20', surface='Waypoint destroy missing token', family='js_route', skip='waypoint destroy -yes notes', auth='waypoint status notes', leftover='patch'),
    dict(slug='tfe-ws-skip-delete', plant='azv20yard', ticket='AZ3-21', surface='TFE workspace delete missing token', family='js_route', skip='tfc workspaces delete notes --force', auth='tfc workspaces show notes', leftover='update'),
    dict(slug='atlantis-skip-delete', plant='azv21yard', ticket='AZ4-22', surface='Atlantis unlock missing webhook', family='js_route', skip='atlantis unlock notes', auth='atlantis status notes', leftover='put'),
    dict(slug='spacelift-skip-delete', plant='azv22yard', ticket='AZ5-23', surface='Spacelift stack delete missing token', family='js_route', skip='spacectl stack delete notes --force', auth='spacectl stack show notes', leftover='patch'),
    dict(slug='env0-skip-delete', plant='azv23yard', ticket='AZ6-24', surface='env0 environment destroy missing token', family='js_route', skip='env0 environment destroy notes --force', auth='env0 environment get notes', leftover='update'),
    dict(slug='terrateam-skip-delete', plant='azv24yard', ticket='AZ7-25', surface='Terrateam unlock missing token', family='js_route', skip='terrateam unlock notes', auth='terrateam status notes', leftover='put'),
    dict(slug='checkov-skip-delete', plant='azv25yard', ticket='AZ8-26', surface='Checkov baseline delete missing conf', family='js_route', skip='rm notes.checkov.baseline', auth='checkov -f notes', leftover='patch'),
    dict(slug='tfsec-skip-delete', plant='azv26yard', ticket='AZ9-27', surface='tfsec baseline delete missing conf', family='js_route', skip='rm notes.tfsec.json', auth='tfsec notes', leftover='update'),
    dict(slug='trivy-skip-delete', plant='azv27yard', ticket='AZ1-28', surface='Trivy ignore delete missing conf', family='js_route', skip='rm notes.trivyignore', auth='trivy fs notes', leftover='put'),
    dict(slug='grype-skip-delete', plant='azv28yard', ticket='AZ2-29', surface='Grype db wipe missing cache', family='js_route', skip='grype db delete', auth='grype notes', leftover='patch'),
    dict(slug='syft-skip-delete', plant='azv29yard', ticket='AZ3-30', surface='Syft sbom delete missing file', family='js_route', skip='rm notes.syft.json', auth='syft notes', leftover='update'),
    dict(slug='cosign-skip-delete', plant='azv30yard', ticket='AZ4-31', surface='Cosign signature delete missing key', family='js_route', skip='cosign clean notes', auth='cosign verify notes', leftover='put'),
    dict(slug='notation-skip-delete', plant='azv31yard', ticket='AZ5-32', surface='Notation signature delete missing key', family='js_route', skip='notation delete notes', auth='notation inspect notes', leftover='patch'),
    dict(slug='rekor-skip-delete', plant='azv32yard', ticket='AZ6-33', surface='Rekor entry delete missing token', family='js_route', skip='rekor-cli delete --uuid notes', auth='rekor-cli get --uuid notes', leftover='update'),
    dict(slug='fulcio-skip-delete', plant='azv33yard', ticket='AZ7-34', surface='Fulcio cert revoke missing oidc', family='js_route', skip='fulcio revoke --id notes', auth='fulcio get --id notes', leftover='put'),
    dict(slug='grafana-ds-skip-delete', plant='azv34yard', ticket='AZ8-35', surface='Grafana datasource delete missing token', family='js_route', skip='grafana-cli admin datasources delete notes', auth='grafana-cli admin datasources list', leftover='patch'),
    dict(slug='thanos-skip-delete', plant='azv35yard', ticket='AZ9-36', surface='Thanos rule delete missing token', family='js_route', skip='thanos tools bucket rm notes', auth='thanos tools bucket ls', leftover='update'),
    dict(slug='mimir-skip-delete', plant='azv36yard', ticket='AZ1-37', surface='Mimir rule delete missing token', family='js_route', skip='mimirtool rules delete notes', auth='mimirtool rules get notes', leftover='put'),
    dict(slug='alertmgr-skip-delete', plant='azv37yard', ticket='AZ2-38', surface='Alertmanager silence delete missing token', family='js_route', skip='amtool silence expire notes', auth='amtool silence query notes', leftover='patch'),
    dict(slug='vector-skip-delete', plant='azv38yard', ticket='AZ3-39', surface='Vector sink delete missing conf', family='js_route', skip='rm /etc/vector/notes.toml', auth='vector validate', leftover='update'),
    dict(slug='fluentd-skip-delete', plant='azv39yard', ticket='AZ4-40', surface='Fluentd match delete missing conf', family='js_route', skip='rm /etc/fluent/notes.conf', auth='fluentd --dry-run', leftover='put'),
    dict(slug='fluentbit-skip-delete', plant='azv40yard', ticket='AZ5-41', surface='Fluent Bit input delete missing conf', family='js_route', skip='rm /etc/fluent-bit/notes.conf', auth='fluent-bit -c /etc/fluent-bit/fluent-bit.conf --dry-run', leftover='patch'),
    dict(slug='filebeat-skip-delete', plant='azv41yard', ticket='AZ6-42', surface='Filebeat input delete missing conf', family='js_route', skip='rm /etc/filebeat/notes.yml', auth='filebeat test config', leftover='update'),
    dict(slug='logstash-skip-delete', plant='azv42yard', ticket='AZ7-43', surface='Logstash pipeline delete missing conf', family='js_route', skip='rm /etc/logstash/conf.d/notes.conf', auth='logstash --config.test_and_exit', leftover='put'),
    dict(slug='es-index-skip-delete', plant='azv43yard', ticket='AZ8-44', surface='Elasticsearch index delete missing user', family='js_route', skip='curl -X DELETE $ES/notes', auth='curl $ES/notes', leftover='patch'),
    dict(slug='os-index-skip-delete', plant='azv44yard', ticket='AZ9-45', surface='OpenSearch index delete missing user', family='js_route', skip='curl -X DELETE $OS/notes', auth='curl $OS/notes', leftover='update'),
    dict(slug='kibana-skip-delete', plant='azv45yard', ticket='AZ1-46', surface='Kibana saved object delete missing token', family='js_route', skip='curl -X DELETE $KBN/api/saved_objects/index-pattern/notes', auth='curl $KBN/api/saved_objects/index-pattern/notes', leftover='put'),
    dict(slug='pg-db-skip-delete', plant='azv46yard', ticket='AZ2-47', surface='Postgres database drop missing role', family='js_route', skip='dropdb notes', auth='psql -l | grep notes', leftover='patch'),
    dict(slug='mysql-db-skip-delete', plant='azv47yard', ticket='AZ3-48', surface='MySQL database drop missing grant', family='js_route', skip='mysqladmin drop notes -f', auth='mysqlshow notes', leftover='update'),
    dict(slug='redis-key-skip-delete', plant='azv48yard', ticket='AZ4-49', surface='Redis key delete missing acl', family='js_route', skip='redis-cli DEL notes', auth='redis-cli GET notes', leftover='put'),
    dict(slug='mongo-db-skip-delete', plant='azv49yard', ticket='AZ5-50', surface='MongoDB dropDatabase missing role', family='js_route', skip='mongosh --eval \'db.getSiblingDB("notes").dropDatabase()\'', auth='mongosh --eval \'db.getSiblingDB("notes").stats()\'', leftover='patch'),
    dict(slug='cstar-ks-skip-delete', plant='azv50yard', ticket='AZ6-51', surface='Cassandra keyspace drop missing role', family='js_route', skip="cqlsh -e 'DROP KEYSPACE notes'", auth="cqlsh -e 'DESCRIBE KEYSPACE notes'", leftover='update'),
    dict(slug='ch-db-skip-delete', plant='azv51yard', ticket='AZ7-52', surface='ClickHouse database drop missing user', family='js_route', skip="clickhouse-client -q 'DROP DATABASE notes'", auth="clickhouse-client -q 'SHOW DATABASES'", leftover='put'),
    dict(slug='crdb-db-skip-delete', plant='azv52yard', ticket='AZ8-53', surface='CockroachDB database drop missing user', family='js_route', skip="cockroach sql -e 'DROP DATABASE notes'", auth="cockroach sql -e 'SHOW DATABASES'", leftover='patch'),
    dict(slug='tidb-db-skip-delete', plant='azv53yard', ticket='AZ9-54', surface='TiDB database drop missing grant', family='js_route', skip="mysql -h tidb -e 'DROP DATABASE notes'", auth="mysql -h tidb -e 'SHOW DATABASES'", leftover='update'),
    dict(slug='neo4j-db-skip-delete', plant='azv54yard', ticket='AZ1-55', surface='Neo4j database drop missing auth', family='js_route', skip="cypher-shell 'DROP DATABASE notes'", auth="cypher-shell 'SHOW DATABASES'", leftover='put'),
    dict(slug='influx-db-skip-delete', plant='azv55yard', ticket='AZ2-56', surface='InfluxDB bucket delete missing token', family='js_route', skip='influx bucket delete -n notes', auth='influx bucket list', leftover='patch'),
    dict(slug='tsdb-db-skip-delete', plant='azv56yard', ticket='AZ3-57', surface='Timescale hypertable drop missing role', family='js_route', skip="psql -c 'DROP TABLE notes'", auth="psql -c '\\dt notes'", leftover='update'),
    dict(slug='traefik-rt-skip-delete', plant='azv57yard', ticket='AZ4-58', surface='Traefik router delete missing api', family='js_route', skip='curl -X DELETE $TR/api/http/routers/notes', auth='curl $TR/api/http/routers/notes', leftover='put'),
    dict(slug='envoy-cls-skip-delete', plant='azv58yard', ticket='AZ5-59', surface='Envoy cluster delete missing admin', family='js_route', skip='curl -X POST $EN/clusters/notes/delete', auth='curl $EN/clusters/notes', leftover='patch'),
    dict(slug='caddy-rt-skip-delete', plant='azv59yard', ticket='AZ6-60', surface='Caddy route delete missing admin', family='js_route', skip='curl -X DELETE $CD/config/apps/http/servers/srv0/routes/notes', auth='curl $CD/config/apps/http/servers/srv0/routes/notes', leftover='update'),
    dict(slug='airflow-dag-skip-delete', plant='azv60yard', ticket='AZ7-61', surface='Airflow DAG delete missing rbac', family='js_route', skip='airflow dags delete notes -y', auth='airflow dags list | grep notes', leftover='put'),
    dict(slug='prefect-fl-skip-delete', plant='azv61yard', ticket='AZ8-62', surface='Prefect flow delete missing token', family='js_route', skip='prefect deployment delete notes', auth='prefect deployment inspect notes', leftover='patch'),
    dict(slug='dagster-job-skip-delete', plant='azv62yard', ticket='AZ9-63', surface='Dagster job delete missing token', family='js_route', skip='dagster job delete notes', auth='dagster job list', leftover='update'),
    dict(slug='luigi-task-skip-delete', plant='azv63yard', ticket='AZ1-64', surface='Luigi task delete missing conf', family='js_route', skip='luigi-deps --module notes --delete', auth='luigi --module notes --local-scheduler', leftover='put'),
    dict(slug='mlflow-run-skip-delete', plant='azv64yard', ticket='AZ2-65', surface='MLflow run delete missing token', family='js_route', skip='mlflow runs delete --run-id notes', auth='mlflow runs describe --run-id notes', leftover='patch'),
    dict(slug='kubeflow-skip-delete', plant='azv65yard', ticket='AZ3-66', surface='Kubeflow pipeline delete missing rbac', family='js_route', skip='kfp pipeline delete notes', auth='kfp pipeline get notes', leftover='update'),
    dict(slug='wandb-run-skip-delete', plant='azv66yard', ticket='AZ4-67', surface='W&B run delete missing token', family='js_route', skip='wandb sync --delete notes', auth='wandb pull notes', leftover='put'),
    dict(slug='dvc-rem-skip-delete', plant='azv67yard', ticket='AZ5-68', surface='DVC remote remove missing conf', family='js_route', skip='dvc remote remove notes', auth='dvc remote list', leftover='patch'),
    dict(slug='airbyte-src-skip-delete', plant='azv68yard', ticket='AZ6-69', surface='Airbyte source delete missing token', family='js_route', skip='airbyte source delete notes', auth='airbyte source get notes', leftover='update'),
    dict(slug='dbt-model-skip-delete', plant='azv69yard', ticket='AZ7-70', surface='dbt model drop missing profile', family='js_route', skip="dbt run-operation drop_model --args '{model: notes}'", auth='dbt ls --select notes', leftover='put'),
    dict(slug='spark-app-skip-delete', plant='azv70yard', ticket='AZ8-71', surface='Spark app kill missing yarn', family='js_route', skip='spark-submit --kill notes', auth='spark-submit --status notes', leftover='patch'),
    dict(slug='flink-job-skip-delete', plant='azv71yard', ticket='AZ9-72', surface='Flink job cancel missing rest', family='js_route', skip='flink cancel notes', auth='flink list | grep notes', leftover='update'),
    dict(slug='beam-job-skip-delete', plant='azv72yard', ticket='AZ1-73', surface='Beam job cancel missing gcp', family='js_route', skip='gcloud dataflow jobs cancel notes', auth='gcloud dataflow jobs show notes', leftover='put'),
    dict(slug='kafka-conn-skip-delete', plant='azv73yard', ticket='AZ2-74', surface='Kafka Connect connector delete missing rest', family='js_route', skip='curl -X DELETE $KC/connectors/notes', auth='curl $KC/connectors/notes', leftover='patch'),
    dict(slug='schema-reg-skip-delete', plant='azv74yard', ticket='AZ3-75', surface='Schema Registry subject delete missing rest', family='js_route', skip='curl -X DELETE $SR/subjects/notes', auth='curl $SR/subjects/notes', leftover='update'),
    dict(slug='kconnect-skip-delete', plant='azv75yard', ticket='AZ4-76', surface='kconnect context delete missing kube', family='js_route', skip='kconnect rm notes', auth='kconnect ls', leftover='put'),
    dict(slug='debezium-skip-delete', plant='azv76yard', ticket='AZ5-77', surface='Debezium connector delete missing rest', family='js_route', skip='curl -X DELETE $DBZ/connectors/notes', auth='curl $DBZ/connectors/notes', leftover='patch'),
    dict(slug='maxwell-skip-delete', plant='azv77yard', ticket='AZ6-78', surface='Maxwell position delete missing mysql', family='js_route', skip='maxwell-bootstrap --delete notes', auth='maxwell --config notes', leftover='update'),
    dict(slug='tableau-skip-delete', plant='azv78yard', ticket='AZ7-79', surface='Tableau workbook delete missing token', family='js_route', skip='tabcmd delete "notes.twb"', auth='tabcmd get "notes.twb"', leftover='put'),
    dict(slug='powerbi-skip-delete', plant='azv79yard', ticket='AZ8-80', surface='Power BI dataset delete missing token', family='js_route', skip='pbicli dataset delete notes', auth='pbicli dataset get notes', leftover='patch'),
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
