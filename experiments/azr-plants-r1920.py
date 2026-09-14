"""Extra unique IDOR/BFLA plants for authz-regression-factory r1920+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r1919 vesselNNNN-sys.
Not clones of r1919 elia-elias / redpanda-acl, r1840 tepco-feeder / bitbucket-pipe.
"""
from __future__ import annotations


EXTRA_IDOR_ROWS = [
    dict(slug='evn-wagon-idor', plant='azq00keel', ticket='AZ1-1', surface='EVN wagon object-id IDOR', mod='evnwgns', model='Evnwgn', lookup='evnwgn', sample='218012345678', owner='rail_id', first='authn', residual='pdf', product='evn-wagon', bug='AZ1-1 wagon unique from ERA'),
    dict(slug='aar-umler-idor', plant='azq01keel', ticket='AZ2-2', surface='AAR UMLER object-id IDOR', mod='aarumls', model='Aaruml', lookup='aaruml', sample='AAR-123456', owner='rail_id', first='mask', residual='export', product='aar-umler', bug='AZ2-2 car unique from AAR'),
    dict(slug='tops-tdbos-idor', plant='azq02keel', ticket='AZ3-3', surface='TOPS TDBOS object-id IDOR', mod='topstdbs', model='Topstdb', lookup='topstdb', sample='43XXX', owner='rail_id', first='any_member', residual='search', product='tops-tdbos', bug='AZ3-3 TDBOS unique from NR'),
    dict(slug='rid-un-idor', plant='azq03keel', ticket='AZ4-4', surface='RID UN tank object-id IDOR', mod='riduns', model='Ridun', lookup='ridun', sample='UN-1203', owner='rail_id', first='list_scope', residual='mget', product='rid-un', bug='AZ4-4 tank unique from RID'),
    dict(slug='era-vkm-idor', plant='azq04keel', ticket='AZ5-5', surface='ERA VKM object-id IDOR', mod='eravkms', model='Eravkm', lookup='eravkm', sample='VKM-ABCD', owner='rail_id', first='authn', residual='csv', product='era-vkm', bug='AZ5-5 VKM unique from ERA'),
    dict(slug='tsi-wimo-idor', plant='azq05keel', ticket='AZ6-6', surface='TSI WIMO object-id IDOR', mod='tsiwimos', model='Tsiwimo', lookup='tsiwimo', sample='WIMO-001', owner='rail_id', first='mask', residual='admin', product='tsi-wimo', bug='AZ6-6 WIMO unique from ERA'),
    dict(slug='nr-elr-idor', plant='azq06keel', ticket='AZ7-7', surface='NR ELR object-id IDOR', mod='nrelrs', model='Nrelr', lookup='nrelr', sample='ELR-MLN', owner='rail_id', first='any_member', residual='webhook', product='nr-elr', bug='AZ7-7 ELR unique from NR'),
    dict(slug='rssb-gid-idor', plant='azq07keel', ticket='AZ8-8', surface='RSSB GID object-id IDOR', mod='rssbgids', model='Rssbgid', lookup='rssbgid', sample='GID-001', owner='rail_id', first='list_scope', residual='comments', product='rssb-gid', bug='AZ8-8 GID unique from RSSB'),
    dict(slug='sncf-uic-idor', plant='azq08keel', ticket='AZ9-9', surface='SNCF UIC object-id IDOR', mod='sncfuics', model='Sncfuic', lookup='sncfuic', sample='87XXXXXX', owner='rail_id', first='authn', residual='pdf', product='sncf-uic', bug='AZ9-9 UIC unique from SNCF'),
    dict(slug='ric-wagon-idor', plant='azq09keel', ticket='AZ1-10', surface='RIC wagon object-id IDOR', mod='ricwgns', model='Ricwgn', lookup='ricwgn', sample='RIC-2180', owner='rail_id', first='mask', residual='export', product='ric-wagon', bug='AZ1-10 wagon unique from RIC'),
    dict(slug='db-fahrweg-idor', plant='azq10keel', ticket='AZ2-11', surface='DB Fahrweg object-id IDOR', mod='dbfwgs', model='Dbfwg', lookup='dbfwg', sample='FW-001', owner='rail_id', first='any_member', residual='search', product='db-fahrweg', bug='AZ2-11 fahrweg unique from DB'),
    dict(slug='obb-vpe-idor', plant='azq11keel', ticket='AZ3-12', surface='OBB VPE object-id IDOR', mod='obbvpes', model='Obbvpe', lookup='obbvpe', sample='VPE-001', owner='rail_id', first='list_scope', residual='mget', product='obb-vpe', bug='AZ3-12 VPE unique from OBB'),
    dict(slug='sbb-didok-idor', plant='azq12keel', ticket='AZ4-13', surface='SBB DIDOK object-id IDOR', mod='sbbdids', model='Sbbdid', lookup='sbbdid', sample='DIDOK-8503000', owner='rail_id', first='authn', residual='csv', product='sbb-didok', bug='AZ4-13 DIDOK unique from SBB'),
    dict(slug='jr-rosen-idor', plant='azq13keel', ticket='AZ5-14', surface='JR rosen object-id IDOR', mod='jrrosens', model='Jrrosen', lookup='jrrosen', sample='ROSEN-001', owner='rail_id', first='mask', residual='admin', product='jr-rosen', bug='AZ5-14 line unique from JR'),
    dict(slug='cr-telecode-idor', plant='azq14keel', ticket='AZ6-15', surface='CR telecode object-id IDOR', mod='crtelecs', model='Crtelec', lookup='crtelec', sample='BJP', owner='rail_id', first='any_member', residual='webhook', product='cr-telecode', bug='AZ6-15 telecode unique from CR'),
    dict(slug='ir-crs-idor', plant='azq15keel', ticket='AZ7-16', surface='IR CRS object-id IDOR', mod='ircrss', model='Ircrs', lookup='ircrs', sample='NDLS', owner='rail_id', first='list_scope', residual='comments', product='ir-crs', bug='AZ7-16 CRS unique from IR'),
    dict(slug='amtrak-amc-idor', plant='azq16keel', ticket='AZ8-17', surface='Amtrak AMC object-id IDOR', mod='amtamcs', model='Amtamc', lookup='amtamc', sample='AMC-001', owner='rail_id', first='authn', residual='pdf', product='amtrak-amc', bug='AZ8-17 AMC unique from Amtrak'),
    dict(slug='via-stp-idor', plant='azq17keel', ticket='AZ9-18', surface='VIA STP object-id IDOR', mod='viastps', model='Viastp', lookup='viastp', sample='STP-001', owner='rail_id', first='mask', residual='export', product='via-stp', bug='AZ9-18 STP unique from VIA'),
    dict(slug='metro-gtfs-idor', plant='azq18keel', ticket='AZ1-19', surface='Metro GTFS trip object-id IDOR', mod='mgtfss', model='Mgtfs', lookup='mgtfs', sample='TRIP-001', owner='rail_id', first='any_member', residual='search', product='metro-gtfs', bug='AZ1-19 trip unique from GTFS'),
    dict(slug='uic-rics-idor', plant='azq19keel', ticket='AZ2-20', surface='UIC RICS object-id IDOR', mod='uicricss', model='Uicrics', lookup='uicrics', sample='RICS-1187', owner='rail_id', first='list_scope', residual='mget', product='uic-rics', bug='AZ2-20 RICS unique from UIC'),
    dict(slug='icao24-hex-idor', plant='azq20keel', ticket='AZ3-21', surface='ICAO24 hex object-id IDOR', mod='icao24s', model='Icao24', lookup='icao24hex', sample='ABCDEF', owner='av_id', first='authn', residual='csv', product='icao24-hex', bug='AZ3-21 hex unique from ICAO'),
    dict(slug='modes-icao-idor', plant='azq21keel', ticket='AZ4-22', surface='Mode-S ICAO object-id IDOR', mod='modesics', model='Modesic', lookup='modesic', sample='4CA123', owner='av_id', first='mask', residual='admin', product='modes-icao', bug='AZ4-22 Mode-S unique from ICAO'),
    dict(slug='adsb-hex-idor', plant='azq22keel', ticket='AZ5-23', surface='ADS-B hex object-id IDOR', mod='adsbhexs', model='Adsbhex', lookup='adsbhex', sample='A1B2C3', owner='av_id', first='any_member', residual='webhook', product='adsb-hex', bug='AZ5-23 hex unique from ADS-B'),
    dict(slug='flarm-id-idor', plant='azq23keel', ticket='AZ6-24', surface='FLARM id object-id IDOR', mod='flarmids', model='Flarmid', lookup='flarmid', sample='DDA123', owner='av_id', first='list_scope', residual='comments', product='flarm-id', bug='AZ6-24 id unique from FLARM'),
    dict(slug='ogn-id-idor', plant='azq24keel', ticket='AZ7-25', surface='OGN id object-id IDOR', mod='ognids', model='Ognid', lookup='ognid', sample='OGN123456', owner='av_id', first='authn', residual='pdf', product='ogn-id', bug='AZ7-25 id unique from OGN'),
    dict(slug='faa-nnum-idor', plant='azq25keel', ticket='AZ8-26', surface='FAA N-number object-id IDOR', mod='faannums', model='Faannum', lookup='faannum', sample='N12345', owner='av_id', first='mask', residual='export', product='faa-nnum', bug='AZ8-26 N-number unique from FAA'),
    dict(slug='easa-csn-idor', plant='azq26keel', ticket='AZ9-27', surface='EASA CSN object-id IDOR', mod='easacsns', model='Easacsn', lookup='easacsn', sample='CSN-001', owner='av_id', first='any_member', residual='search', product='easa-csn', bug='AZ9-27 CSN unique from EASA'),
    dict(slug='icao-locid-idor', plant='azq27keel', ticket='AZ1-28', surface='ICAO locid object-id IDOR', mod='icaolcids', model='Icaolcid', lookup='icaolcid', sample='KJFK', owner='av_id', first='list_scope', residual='mget', product='icao-locid', bug='AZ1-28 locid unique from ICAO'),
    dict(slug='iata-locid-idor', plant='azq28keel', ticket='AZ2-29', surface='IATA locid object-id IDOR', mod='iatalocs', model='Iataloc', lookup='iataloc', sample='JFK', owner='av_id', first='authn', residual='csv', product='iata-locid', bug='AZ2-29 locid unique from IATA'),
    dict(slug='fir-icao-idor', plant='azq29keel', ticket='AZ3-30', surface='FIR ICAO object-id IDOR', mod='firicaos', model='Firicao', lookup='firicao', sample='KZNY', owner='av_id', first='mask', residual='admin', product='fir-icao', bug='AZ3-30 FIR unique from ICAO'),
    dict(slug='notam-qcode-idor', plant='azq30keel', ticket='AZ4-31', surface='NOTAM Q-code object-id IDOR', mod='notamqs', model='Notamq', lookup='notamq', sample='QXXXX', owner='av_id', first='any_member', residual='webhook', product='notam-q', bug='AZ4-31 Q-code unique from ICAO'),
    dict(slug='sid-proc-idor', plant='azq31keel', ticket='AZ5-32', surface='SID procedure object-id IDOR', mod='sidprocs', model='Sidproc', lookup='sidproc', sample='DEEZZ5', owner='av_id', first='list_scope', residual='comments', product='sid-proc', bug='AZ5-32 SID unique from FAA'),
    dict(slug='star-proc-idor', plant='azq32keel', ticket='AZ6-33', surface='STAR procedure object-id IDOR', mod='starprocs', model='Starproc', lookup='starproc', sample='CAMRN4', owner='av_id', first='authn', residual='pdf', product='star-proc', bug='AZ6-33 STAR unique from FAA'),
    dict(slug='approach-proc-idor', plant='azq33keel', ticket='AZ7-34', surface='approach procedure object-id IDOR', mod='apprprocs', model='Apprproc', lookup='apprproc', sample='ILS22L', owner='av_id', first='mask', residual='export', product='appr-proc', bug='AZ7-34 approach unique from FAA'),
    dict(slug='rnav-wp-idor', plant='azq34keel', ticket='AZ8-35', surface='RNAV waypoint object-id IDOR', mod='rnavwps', model='Rnavwp', lookup='rnavwp', sample='CAMRN', owner='av_id', first='any_member', residual='search', product='rnav-wp', bug='AZ8-35 waypoint unique from FAA'),
    dict(slug='fix-ident-idor', plant='azq35keel', ticket='AZ9-36', surface='FIX ident object-id IDOR', mod='fixidents', model='Fixident', lookup='fixident', sample='LGA', owner='av_id', first='list_scope', residual='mget', product='fix-ident', bug='AZ9-36 FIX unique from FAA'),
    dict(slug='awy-ident-idor', plant='azq36keel', ticket='AZ1-37', surface='airway ident object-id IDOR', mod='awyidents', model='Awyident', lookup='awyident', sample='J75', owner='av_id', first='authn', residual='csv', product='awy-ident', bug='AZ1-37 airway unique from FAA'),
    dict(slug='tma-icao-idor', plant='azq37keel', ticket='AZ2-38', surface='TMA ICAO object-id IDOR', mod='tmaicaos', model='Tmaicao', lookup='tmaicao', sample='EGTT', owner='av_id', first='mask', residual='admin', product='tma-icao', bug='AZ2-38 TMA unique from ICAO'),
    dict(slug='ctr-icao-idor', plant='azq38keel', ticket='AZ3-39', surface='CTR ICAO object-id IDOR', mod='ctricaos', model='Ctricao', lookup='ctricao', sample='EGLL', owner='av_id', first='any_member', residual='webhook', product='ctr-icao', bug='AZ3-39 CTR unique from ICAO'),
    dict(slug='atis-id-idor', plant='azq39keel', ticket='AZ4-40', surface='ATIS ident object-id IDOR', mod='atisids', model='Atisid', lookup='atisid', sample='ATIS-A', owner='av_id', first='list_scope', residual='comments', product='atis-id', bug='AZ4-40 ident unique from FAA'),
    dict(slug='eni-cemt-idor', plant='azq40keel', ticket='AZ5-41', surface='ENI CEMT object-id IDOR', mod='enicemts', model='Enicemt', lookup='enicemt', sample='04000000', owner='mmsi_id', first='authn', residual='pdf', product='eni-cemt', bug='AZ5-41 ENI unique from CCNR'),
    dict(slug='lrimo-idor', plant='azq41keel', ticket='AZ6-42', surface='LR/IMO object-id IDOR', mod='lrimos', model='Lrimo', lookup='lrimo', sample='9074729', owner='mmsi_id', first='mask', residual='export', product='lr-imo', bug='AZ6-42 LR unique from IHS'),
    dict(slug='callsign-imo-idor', plant='azq42keel', ticket='AZ7-43', surface='callsign object-id IDOR', mod='callsimos', model='Callsimo', lookup='callsimo', sample='3EZZ2', owner='mmsi_id', first='any_member', residual='search', product='callsign-imo', bug='AZ7-43 callsign unique from ITU'),
    dict(slug='csi-iso6346-idor', plant='azq43keel', ticket='AZ8-44', surface='CSI ISO6346 object-id IDOR', mod='csiisos', model='Csiiso', lookup='csiiso', sample='MSCU1234567', owner='mmsi_id', first='list_scope', residual='mget', product='csi-iso6346', bug='AZ8-44 CSI unique from BIC'),
    dict(slug='bic-owner-idor', plant='azq44keel', ticket='AZ9-45', surface='BIC owner code object-id IDOR', mod='bicowns', model='Bicown', lookup='bicown', sample='MSCU', owner='mmsi_id', first='authn', residual='csv', product='bic-owner', bug='AZ9-45 owner unique from BIC'),
    dict(slug='iso6346-ck-idor', plant='azq45keel', ticket='AZ1-46', surface='ISO6346 check object-id IDOR', mod='iso6346s', model='Iso6346', lookup='iso6346ck', sample='MSCU1234560', owner='mmsi_id', first='mask', residual='admin', product='iso6346-ck', bug='AZ1-46 check unique from ISO'),
    dict(slug='imo-csc-idor', plant='azq46keel', ticket='AZ2-47', surface='IMO CSC object-id IDOR', mod='imocscs', model='Imocsc', lookup='imocsc', sample='CSC-001', owner='mmsi_id', first='any_member', residual='webhook', product='imo-csc', bug='AZ2-47 CSC unique from IMO'),
    dict(slug='solas-imo-idor', plant='azq47keel', ticket='AZ3-48', surface='SOLAS IMO object-id IDOR', mod='solasimos', model='Solasimo', lookup='solasimo', sample='SOLAS-001', owner='mmsi_id', first='list_scope', residual='comments', product='solas-imo', bug='AZ3-48 id unique from IMO'),
    dict(slug='mmsi-mid-idor', plant='azq48keel', ticket='AZ4-49', surface='MMSI MID object-id IDOR', mod='mmsimids', model='Mmsimid', lookup='mmsimid', sample='338123456', owner='mmsi_id', first='authn', residual='pdf', product='mmsi-mid', bug='AZ4-49 MID unique from ITU'),
    dict(slug='ais-mmsi-idor', plant='azq49keel', ticket='AZ5-50', surface='AIS MMSI object-id IDOR', mod='aismmsis', model='Aismmsi', lookup='aismmsi', sample='366123456', owner='mmsi_id', first='mask', residual='export', product='ais-mmsi', bug='AZ5-50 MMSI unique from ITU'),
    dict(slug='cusip-idor', plant='azq50keel', ticket='AZ6-51', surface='CUSIP object-id IDOR', mod='cusipns', model='Cusipn', lookup='cusipn', sample='037833100', owner='bank_id', first='any_member', residual='search', product='cusip-9', bug='AZ6-51 CUSIP unique from CUSIP'),
    dict(slug='sedol-idor', plant='azq51keel', ticket='AZ7-52', surface='SEDOL object-id IDOR', mod='sedolns', model='Sedoln', lookup='sedoln', sample='B0YBKJ7', owner='bank_id', first='list_scope', residual='mget', product='sedol-7', bug='AZ7-52 SEDOL unique from LSE'),
    dict(slug='figi-idor', plant='azq52keel', ticket='AZ8-53', surface='FIGI object-id IDOR', mod='figins', model='Figin', lookup='fgin', sample='BBG000B9XRY4', owner='bank_id', first='authn', residual='csv', product='figi-12', bug='AZ8-53 FIGI unique from Bloomberg'),
    dict(slug='ric-code-idor', plant='azq53keel', ticket='AZ9-54', surface='RIC object-id IDOR', mod='riccodes', model='Riccode', lookup='riccode', sample='AAPL.O', owner='bank_id', first='mask', residual='admin', product='ric-code', bug='AZ9-54 RIC unique from Refinitiv'),
    dict(slug='six-valor-idor', plant='azq54keel', ticket='AZ1-55', surface='SIX valor object-id IDOR', mod='sixvalors', model='Sixvalor', lookup='sixvalor', sample='1222171', owner='bank_id', first='any_member', residual='webhook', product='six-valor', bug='AZ1-55 valor unique from SIX'),
    dict(slug='isin-check-idor', plant='azq55keel', ticket='AZ2-56', surface='ISIN check object-id IDOR', mod='isinchks', model='Isinchk', lookup='isinchk', sample='US0378331005', owner='bank_id', first='list_scope', residual='comments', product='isin-check', bug='AZ2-56 ISIN unique from ANNA'),
    dict(slug='lei-20char-idor', plant='azq56keel', ticket='AZ3-57', surface='LEI 20-char object-id IDOR', mod='lei20s', model='Lei20', lookup='lei20', sample='5493001KJTIIGC8Y1R12', owner='bank_id', first='authn', residual='pdf', product='lei-20', bug='AZ3-57 LEI unique from GLEIF'),
    dict(slug='bic11-idor', plant='azq57keel', ticket='AZ4-58', surface='BIC11 object-id IDOR', mod='bic11s', model='Bic11', lookup='bic11', sample='CHASUS33XXX', owner='bank_id', first='mask', residual='export', product='bic11-id', bug='AZ4-58 BIC unique from SWIFT'),
    dict(slug='mic-iso10383-idor', plant='azq58keel', ticket='AZ5-59', surface='MIC ISO10383 object-id IDOR', mod='micisos', model='Miciso', lookup='miciso', sample='XNYS', owner='bank_id', first='any_member', residual='search', product='mic-10383', bug='AZ5-59 MIC unique from ISO'),
    dict(slug='cfi-iso10962-idor', plant='azq59keel', ticket='AZ6-60', surface='CFI ISO10962 object-id IDOR', mod='cfiisos', model='Cfiiso', lookup='cfiso', sample='ESVUFR', owner='bank_id', first='list_scope', residual='mget', product='cfi-10962', bug='AZ6-60 CFI unique from ISO'),
    dict(slug='udi-di-idor', plant='azq60keel', ticket='AZ7-61', surface='UDI-DI object-id IDOR', mod='udidis', model='Udidi', lookup='udidi', sample='00884838000000', owner='lab_id', first='authn', residual='csv', product='udi-di', bug='AZ7-61 DI unique from FDA'),
    dict(slug='gudid-di-idor', plant='azq61keel', ticket='AZ8-62', surface='GUDID DI object-id IDOR', mod='gudiddis', model='Gudiddi', lookup='gudiddi', sample='00812345678901', owner='lab_id', first='mask', residual='admin', product='gudid-di', bug='AZ8-62 DI unique from FDA'),
    dict(slug='hibcc-lic-idor', plant='azq62keel', ticket='AZ9-63', surface='HIBCC LIC object-id IDOR', mod='hibccls', model='Hibccl', lookup='hibccl', sample='A999B99', owner='lab_id', first='any_member', residual='webhook', product='hibcc-lic', bug='AZ9-63 LIC unique from HIBCC'),
    dict(slug='iccbba-idin-idor', plant='azq63keel', ticket='AZ1-64', surface='ICCBBA ISBT object-id IDOR', mod='iccbbas', model='Iccbba', lookup='iccbba', sample='W0000', owner='lab_id', first='list_scope', residual='comments', product='iccbba-idin', bug='AZ1-64 ISBT unique from ICCBBA'),
    dict(slug='ndc11-pack-idor', plant='azq64keel', ticket='AZ2-65', surface='NDC-11 pack object-id IDOR', mod='ndc11s', model='Ndc11', lookup='ndc11', sample='00071015527', owner='lab_id', first='authn', residual='pdf', product='ndc11-pack', bug='AZ2-65 NDC unique from FDA'),
    dict(slug='unii-fda-idor', plant='azq65keel', ticket='AZ3-66', surface='UNII object-id IDOR', mod='uniifdas', model='Uniifda', lookup='uniifda', sample='362O9ITL9D', owner='lab_id', first='mask', residual='export', product='unii-fda', bug='AZ3-66 UNII unique from FDA'),
    dict(slug='rxcui-pack-idor', plant='azq66keel', ticket='AZ4-67', surface='RxCUI pack object-id IDOR', mod='rxcuips', model='Rxcuip', lookup='rxcuip', sample='198440', owner='lab_id', first='any_member', residual='search', product='rxcui-pack', bug='AZ4-67 RxCUI unique from NLM'),
    dict(slug='atc-ddd-idor', plant='azq67keel', ticket='AZ5-68', surface='ATC DDD object-id IDOR', mod='atcddds', model='Atcddd', lookup='atcddd', sample='N02BE01', owner='lab_id', first='list_scope', residual='mget', product='atc-ddd', bug='AZ5-68 ATC unique from WHO'),
    dict(slug='loinc-long-idor', plant='azq68keel', ticket='AZ6-69', surface='LOINC long object-id IDOR', mod='loinclongs', model='Loinclong', lookup='loinclong', sample='24323-8', owner='lab_id', first='authn', residual='csv', product='loinc-long', bug='AZ6-69 LOINC unique from Regenstrief'),
    dict(slug='icd11-mms-idor', plant='azq69keel', ticket='AZ7-70', surface='ICD-11 MMS object-id IDOR', mod='icd11mms', model='Icd11mm', lookup='icd11mm', sample='1A00', owner='lab_id', first='mask', residual='admin', product='icd11-mms', bug='AZ7-70 MMS unique from WHO'),
    dict(slug='eic-x-idor', plant='azq70keel', ticket='AZ8-71', surface='EIC-X object-id IDOR', mod='eicxs', model='Eicx', lookup='eicx', sample='10X1001A1001A450', owner='grid_id', first='any_member', residual='webhook', product='eic-x', bug='AZ8-71 EIC unique from ENTSO-E'),
    dict(slug='mrid-cim-idor', plant='azq71keel', ticket='AZ9-72', surface='CIM mRID object-id IDOR', mod='mridcims', model='Mridcim', lookup='mridcim', sample='_12345678-1234', owner='grid_id', first='list_scope', residual='comments', product='mrid-cim', bug='AZ9-72 mRID unique from CIM'),
    dict(slug='psr-type-idor', plant='azq72keel', ticket='AZ1-73', surface='PSRType object-id IDOR', mod='psrtypes', model='Psrtype', lookup='psrtype', sample='A04', owner='grid_id', first='authn', residual='pdf', product='psr-type', bug='AZ1-73 type unique from CIM'),
    dict(slug='entsoe-eic-idor', plant='azq73keel', ticket='AZ2-74', surface='ENTSO-E EIC object-id IDOR', mod='entsoeics', model='Entsoeic', lookup='entsoeic', sample='10Y1001A1001A83F', owner='grid_id', first='mask', residual='export', product='entsoe-eic', bug='AZ2-74 EIC unique from ENTSO-E'),
    dict(slug='naesb-duns-idor', plant='azq74keel', ticket='AZ3-75', surface='NAESB DUNS object-id IDOR', mod='naesbduns', model='Naesbdun', lookup='naesbdun', sample='006928773', owner='grid_id', first='any_member', residual='search', product='naesb-duns', bug='AZ3-75 DUNS unique from NAESB'),
    dict(slug='oati-tag-idor', plant='azq75keel', ticket='AZ4-76', surface='OATI tag object-id IDOR', mod='oatitags', model='Oatitag', lookup='oatitagid', sample='123456789', owner='grid_id', first='list_scope', residual='mget', product='oati-tag', bug='AZ4-76 tag unique from OATI'),
    dict(slug='eia-plant-idor', plant='azq76keel', ticket='AZ5-77', surface='EIA plant object-id IDOR', mod='eiaplants', model='Eiaplant', lookup='eiaplant', sample='55322', owner='grid_id', first='authn', residual='csv', product='eia-plant', bug='AZ5-77 plant unique from EIA'),
    dict(slug='nerc-id-idor', plant='azq77keel', ticket='AZ6-78', surface='NERC id object-id IDOR', mod='nercids', model='Nercid', lookup='nercid', sample='NERC-001', owner='grid_id', first='mask', residual='admin', product='nerc-id', bug='AZ6-78 id unique from NERC'),
    dict(slug='rfc-id-idor', plant='azq78keel', ticket='AZ7-79', surface='RFC id object-id IDOR', mod='rfcids', model='Rfcid', lookup='rfcid', sample='RFC-001', owner='grid_id', first='any_member', residual='webhook', product='rfc-id', bug='AZ7-79 id unique from RFC'),
    dict(slug='serc-id-idor', plant='azq79keel', ticket='AZ8-80', surface='SERC id object-id IDOR', mod='sercids', model='Sercid', lookup='sercid', sample='SERC-001', owner='grid_id', first='list_scope', residual='comments', product='serc-id', bug='AZ8-80 id unique from SERC'),
]


BFLA_ROWS = [
    dict(slug='circleci-ctx-skip-delete', plant='azq00keel', ticket='AZ1-1', surface='CircleCI context delete missing token', family='js_route', skip='curl -X DELETE $CCI/api/v2/context/$id', auth='curl -H "Circle-Token: $CCI" $CCI/api/v2/context/$id', leftover='put'),
    dict(slug='travis-job-skip-delete', plant='azq01keel', ticket='AZ2-2', surface='Travis job cancel missing token', family='js_route', skip='travis cancel $id', auth='travis show $id --token $TRAVIS', leftover='patch'),
    dict(slug='buildkite-pipe-skip-delete', plant='azq02keel', ticket='AZ3-3', surface='Buildkite pipeline delete missing token', family='js_route', skip='curl -X DELETE $BK/v2/organizations/o/pipelines/notes', auth='curl -H "Authorization: Bearer $BK" $BK/v2/organizations/o/pipelines/notes', leftover='update'),
    dict(slug='drone-build-skip-delete', plant='azq03keel', ticket='AZ4-4', surface='Drone build delete missing token', family='js_route', skip='drone build stop o/notes 1', auth='drone build info o/notes 1', leftover='put'),
    dict(slug='concourse-job-skip-delete', plant='azq04keel', ticket='AZ5-5', surface='Concourse job abort missing token', family='js_route', skip='fly abort-build -j notes/job -b 1', auth='fly watch -j notes/job -b 1', leftover='patch'),
    dict(slug='harness-pipe-skip-delete', plant='azq05keel', ticket='AZ6-6', surface='Harness pipeline delete missing api-key', family='js_route', skip='curl -X DELETE $HARNESS/v1/orgs/o/pipelines/notes', auth='curl -H "x-api-key: $HARNESS" $HARNESS/v1/orgs/o/pipelines/notes', leftover='update'),
    dict(slug='spinnaker-app-skip-delete', plant='azq06keel', ticket='AZ7-7', surface='Spinnaker application delete missing token', family='js_route', skip='spin application delete notes', auth='spin application get notes', leftover='put'),
    dict(slug='tekton-pipe-skip-delete', plant='azq07keel', ticket='AZ8-8', surface='Tekton pipeline delete missing SA', family='js_route', skip='tkn pipeline delete notes -f', auth='tkn pipeline describe notes', leftover='patch'),
    dict(slug='flux-ks-skip-delete', plant='azq08keel', ticket='AZ9-9', surface='Flux kustomization delete missing kubeconfig', family='js_route', skip='flux delete kustomization notes', auth='flux get kustomizations notes --kubeconfig $KUBECONFIG', leftover='update'),
    dict(slug='argocd-app-skip-delete', plant='azq09keel', ticket='AZ1-10', surface='Argo CD app delete missing token', family='js_route', skip='argocd app delete notes --yes', auth='argocd app get notes --auth-token $ARGOCD', leftover='put'),
    dict(slug='helm-rel-skip-delete', plant='azq10keel', ticket='AZ2-11', surface='Helm release uninstall missing kubeconfig', family='js_route', skip='helm uninstall notes', auth='helm status notes --kubeconfig $KUBECONFIG', leftover='patch'),
    dict(slug='pulumi-stack-skip-delete', plant='azq11keel', ticket='AZ3-12', surface='Pulumi stack rm missing token', family='js_route', skip='pulumi stack rm notes --yes', auth='pulumi stack ls --access-token $PULUMI', leftover='update'),
    dict(slug='tfstate-skip-delete', plant='azq12keel', ticket='AZ4-13', surface='Terraform state rm missing backend creds', family='js_route', skip='terraform state rm notes.a', auth='terraform state list', leftover='put'),
    dict(slug='ansible-inv-skip-delete', plant='azq13keel', ticket='AZ5-14', surface='Ansible inventory delete missing vault', family='js_route', skip='ansible-inventory --delete notes', auth='ansible-inventory --host notes --vault-password-file $VAULT', leftover='patch'),
    dict(slug='salt-key-skip-delete', plant='azq14keel', ticket='AZ6-15', surface='Salt key delete missing eauth', family='js_route', skip='salt-key -d notes -y', auth='salt-key -L --eauth pam', leftover='update'),
    dict(slug='chef-node-skip-delete', plant='azq15keel', ticket='AZ7-16', surface='Chef node delete missing client key', family='js_route', skip='knife node delete notes -y', auth='knife node show notes -k $CHEF', leftover='put'),
    dict(slug='puppet-cert-skip-delete', plant='azq16keel', ticket='AZ8-17', surface='Puppet cert clean missing CA', family='js_route', skip='puppetserver ca clean --certname notes', auth='puppetserver ca list --certname notes', leftover='patch'),
    dict(slug='packer-img-skip-delete', plant='azq17keel', ticket='AZ9-18', surface='Packer image delete missing creds', family='js_route', skip='packer delete notes', auth='packer inspect notes.pkr.hcl', leftover='update'),
    dict(slug='vagrant-box-skip-delete', plant='azq18keel', ticket='AZ1-19', surface='Vagrant box remove missing cloud token', family='js_route', skip='vagrant box remove notes --force', auth='vagrant cloud box show notes --token $VAGRANT', leftover='put'),
    dict(slug='molecule-skip-delete', plant='azq19keel', ticket='AZ2-20', surface='Molecule destroy missing vault', family='js_route', skip='molecule destroy -s notes', auth='molecule list -s notes', leftover='patch'),
    dict(slug='inspec-skip-delete', plant='azq20keel', ticket='AZ3-21', surface='InSpec profile delete missing token', family='js_route', skip='inspec supermarket unshare notes', auth='inspec supermarket info notes --token $INSPEC', leftover='update'),
    dict(slug='kitchen-skip-delete', plant='azq21keel', ticket='AZ4-22', surface='Test Kitchen destroy missing creds', family='js_route', skip='kitchen destroy notes', auth='kitchen list notes', leftover='put'),
    dict(slug='terragrunt-skip-delete', plant='azq22keel', ticket='AZ5-23', surface='Terragrunt destroy missing IAM', family='js_route', skip='terragrunt destroy -auto-approve', auth='terragrunt output', leftover='patch'),
    dict(slug='crossplane-xr-skip-delete', plant='azq23keel', ticket='AZ6-24', surface='Crossplane XR delete missing rbac', family='js_route', skip='kubectl delete xr notes', auth='kubectl get xr notes', leftover='update'),
    dict(slug='capi-cluster-skip-delete', plant='azq24keel', ticket='AZ7-25', surface='Cluster API cluster delete missing rbac', family='js_route', skip='clusterctl delete cluster notes', auth='kubectl get cluster notes', leftover='put'),
    dict(slug='velero-bck-skip-delete', plant='azq25keel', ticket='AZ8-26', surface='Velero backup delete missing SA', family='js_route', skip='velero backup delete notes --confirm', auth='velero backup describe notes', leftover='patch'),
    dict(slug='restic-snap-skip-delete', plant='azq26keel', ticket='AZ9-27', surface='restic snapshot forget missing password', family='js_route', skip='restic forget notes --prune', auth='restic snapshots --password-file $RESTIC', leftover='update'),
    dict(slug='borg-arch-skip-delete', plant='azq27keel', ticket='AZ1-28', surface='Borg archive delete missing passphrase', family='js_route', skip='borg delete repo::notes', auth='borg list repo --encryption-passphrase $BORG', leftover='put'),
    dict(slug='rclone-rm-skip-delete', plant='azq28keel', ticket='AZ2-29', surface='rclone delete missing config', family='js_route', skip='rclone delete notes:path --rmdirs', auth='rclone ls notes: --config $RCLONE', leftover='patch'),
    dict(slug='minio-obj-skip-delete', plant='azq29keel', ticket='AZ3-30', surface='MinIO object delete missing access key', family='js_route', skip='mc rm notes/b/o --force', auth='mc ls notes/b --access-key $MINIO', leftover='update'),
    dict(slug='ceph-pool-skip-delete', plant='azq30keel', ticket='AZ4-31', surface='Ceph pool delete missing cephx', family='js_route', skip='ceph osd pool delete notes notes --yes-i-really-really-mean-it', auth='ceph osd pool ls --id admin', leftover='put'),
    dict(slug='gluster-vol-skip-delete', plant='azq31keel', ticket='AZ5-32', surface='Gluster volume delete missing auth', family='js_route', skip='gluster volume delete notes', auth='gluster volume info notes', leftover='patch'),
    dict(slug='longhorn-vol-skip-delete', plant='azq32keel', ticket='AZ6-33', surface='Longhorn volume delete missing rbac', family='js_route', skip='kubectl delete volume.longhorn.io notes', auth='kubectl get volume.longhorn.io notes', leftover='update'),
    dict(slug='openebs-vol-skip-delete', plant='azq33keel', ticket='AZ7-34', surface='OpenEBS volume delete missing rbac', family='js_route', skip='kubectl delete pvc notes', auth='kubectl get cstorvolume notes', leftover='put'),
    dict(slug='rook-pool-skip-delete', plant='azq34keel', ticket='AZ8-35', surface='Rook pool delete missing rbac', family='js_route', skip='kubectl delete cephblockpool notes', auth='kubectl get cephblockpool notes', leftover='patch'),
    dict(slug='portworx-vol-skip-delete', plant='azq35keel', ticket='AZ9-36', surface='Portworx volume delete missing token', family='js_route', skip='pxctl volume delete notes', auth='pxctl volume inspect notes --token $PX', leftover='update'),
    dict(slug='mayastor-skip-delete', plant='azq36keel', ticket='AZ1-37', surface='Mayastor volume delete missing rbac', family='js_route', skip='kubectl delete diskpool notes', auth='kubectl get diskpool notes', leftover='put'),
    dict(slug='csi-snap-skip-delete', plant='azq37keel', ticket='AZ2-38', surface='CSI snapshot delete missing rbac', family='js_route', skip='kubectl delete volumesnapshot notes', auth='kubectl get volumesnapshot notes', leftover='patch'),
    dict(slug='zfs-ds-skip-delete', plant='azq38keel', ticket='AZ3-39', surface='ZFS dataset destroy missing sudoers', family='js_route', skip='zfs destroy -r notes/ds', auth='zfs list notes/ds', leftover='update'),
    dict(slug='btrfs-sub-skip-delete', plant='azq39keel', ticket='AZ4-40', surface='btrfs subvolume delete missing auth', family='js_route', skip='btrfs subvolume delete notes', auth='btrfs subvolume list notes', leftover='put'),
    dict(slug='lvm-lv-skip-delete', plant='azq40keel', ticket='AZ5-41', surface='LVM LV remove missing sudoers', family='js_route', skip='lvremove -f notes/lv', auth='lvs notes/lv', leftover='patch'),
    dict(slug='mdadm-arr-skip-delete', plant='azq41keel', ticket='AZ6-42', surface='mdadm array stop missing sudoers', family='js_route', skip='mdadm --stop /dev/md/notes', auth='mdadm --detail /dev/md/notes', leftover='update'),
    dict(slug='nvme-ns-skip-delete', plant='azq42keel', ticket='AZ7-43', surface='NVMe ns delete missing admin', family='js_route', skip='nvme delete-ns /dev/nvme0 -n 1', auth='nvme list-ns /dev/nvme0', leftover='put'),
    dict(slug='spdk-bdev-skip-delete', plant='azq43keel', ticket='AZ8-44', surface='SPDK bdev delete missing rpc sock', family='js_route', skip='rpc.py bdev_malloc_delete notes', auth='rpc.py bdev_get_bdevs', leftover='patch'),
    dict(slug='rbd-img-skip-delete', plant='azq44keel', ticket='AZ9-45', surface='RBD image rm missing cephx', family='js_route', skip='rbd rm notes/img', auth='rbd info notes/img --id admin', leftover='update'),
    dict(slug='rgw-bkt-skip-delete', plant='azq45keel', ticket='AZ1-46', surface='RGW bucket rm missing s3 creds', family='js_route', skip='radosgw-admin bucket rm --bucket=notes --purge-objects', auth='radosgw-admin bucket list --uid notes', leftover='put'),
    dict(slug='seaweed-vol-skip-delete', plant='azq46keel', ticket='AZ2-47', surface='SeaweedFS volume delete missing jwt', family='js_route', skip='weed filer.delete -fileId notes', auth='weed filer.cat -fileId notes -jwt $WEED', leftover='patch'),
    dict(slug='garage-bkt-skip-delete', plant='azq47keel', ticket='AZ3-48', surface='Garage bucket delete missing admin', family='js_route', skip='garage bucket delete notes', auth='garage bucket info notes', leftover='update'),
    dict(slug='juicefs-meta-skip-delete', plant='azq48keel', ticket='AZ4-49', surface='JuiceFS destroy missing meta auth', family='js_route', skip='juicefs destroy redis://notes --force', auth='juicefs status redis://notes', leftover='put'),
    dict(slug='kopia-snap-skip-delete', plant='azq49keel', ticket='AZ5-50', surface='Kopia snapshot delete missing password', family='js_route', skip='kopia snapshot delete notes --force', auth='kopia snapshot list --password $KOPIA', leftover='patch'),
    dict(slug='duplicati-skip-delete', plant='azq50keel', ticket='AZ6-51', surface='Duplicati backup delete missing auth', family='js_route', skip='duplicati-cli delete notes', auth='duplicati-cli list-filesets notes --passphrase $DUP', leftover='update'),
    dict(slug='urbackup-skip-delete', plant='azq51keel', ticket='AZ7-52', surface='UrBackup client delete missing auth', family='js_route', skip='urbackupclientctl remove notes', auth='urbackupclientctl status', leftover='put'),
    dict(slug='bacula-job-skip-delete', plant='azq52keel', ticket='AZ8-53', surface='Bacula purge missing console password', family='js_route', skip="bconsole -c /etc/bacula/bconsole.conf <<< 'purge volume=notes'", auth="bconsole <<< 'list volumes'", leftover='patch'),
    dict(slug='bareos-job-skip-delete', plant='azq53keel', ticket='AZ9-54', surface='Bareos purge missing console', family='js_route', skip="bconsole <<< 'purge volume=notes'", auth="bconsole <<< 'list jobs'", leftover='update'),
    dict(slug='amanda-dle-skip-delete', plant='azq54keel', ticket='AZ1-55', surface='Amanda DLE delete missing auth', family='js_route', skip='amrmtape notes tape', auth='amadmin notes disklist', leftover='put'),
    dict(slug='backuppc-skip-delete', plant='azq55keel', ticket='AZ2-56', surface='BackupPC host delete missing auth', family='js_route', skip='BackupPC_backupDelete notes 1', auth='BackupPC_serverMesg status hosts', leftover='patch'),
    dict(slug='rsnapshot-skip-delete', plant='azq56keel', ticket='AZ3-57', surface='rsnapshot rm leftover missing ssh key', family='js_route', skip='rsnapshot -c notes.conf delete hourly.0', auth='rsnapshot -c notes.conf du', leftover='update'),
    dict(slug='rdiff-skip-delete', plant='azq57keel', ticket='AZ4-58', surface='rdiff-backup remove missing ssh', family='js_route', skip='rdiff-backup --remove-older-than 1s notes', auth='rdiff-backup --list-increments notes', leftover='put'),
    dict(slug='borgmatic-skip-delete', plant='azq58keel', ticket='AZ5-59', surface='borgmatic prune missing passphrase', family='js_route', skip='borgmatic prune --force', auth='borgmatic list --override storage.encryption_passphrase=$BORG', leftover='patch'),
    dict(slug='k8up-skip-delete', plant='azq59keel', ticket='AZ6-60', surface='K8up restore delete missing rbac', family='js_route', skip='kubectl delete restore.k8up.io notes', auth='kubectl get restore.k8up.io notes', leftover='update'),
    dict(slug='stash-bck-skip-delete', plant='azq60keel', ticket='AZ7-61', surface='Stash backup delete missing rbac', family='js_route', skip='kubectl delete backup.stash.appscode.com notes', auth='kubectl get backup.stash.appscode.com notes', leftover='put'),
    dict(slug='kanister-skip-delete', plant='azq61keel', ticket='AZ8-62', surface='Kanister actionset delete missing rbac', family='js_route', skip='kubectl delete actionset notes', auth='kubectl get actionset notes', leftover='patch'),
    dict(slug='cnpg-bck-skip-delete', plant='azq62keel', ticket='AZ9-63', surface='CNPG backup delete missing rbac', family='js_route', skip='kubectl delete backup.postgresql.cnpg.io notes', auth='kubectl get backup.postgresql.cnpg.io notes', leftover='update'),
    dict(slug='repmgr-skip-delete', plant='azq63keel', ticket='AZ1-64', surface='repmgr standby unregister missing postgres', family='js_route', skip='repmgr standby unregister --node-id=2', auth='repmgr cluster show', leftover='put'),
    dict(slug='pgbackrest-skip-delete', plant='azq64keel', ticket='AZ2-65', surface='pgBackRest expire missing stanza creds', family='js_route', skip='pgbackrest --stanza=notes expire --retention-full=0', auth='pgbackrest --stanza=notes info', leftover='patch'),
    dict(slug='walg-skip-delete', plant='azq65keel', ticket='AZ3-66', surface='WAL-G delete missing AWS keys', family='js_route', skip='wal-g delete everything --confirm', auth='wal-g backup-list', leftover='update'),
    dict(slug='barman-skip-delete', plant='azq66keel', ticket='AZ4-67', surface='Barman delete missing postgres user', family='js_route', skip='barman delete notes 20240115T000000', auth='barman list-backup notes', leftover='put'),
    dict(slug='mongodump-skip-delete', plant='azq67keel', ticket='AZ5-68', surface='mongodump drop missing auth', family='js_route', skip="mongo notes --eval 'db.dropDatabase()'", auth='mongosh --username notes --password $MONGO', leftover='patch'),
    dict(slug='opensearch-idx-skip-delete', plant='azq68keel', ticket='AZ6-69', surface='OpenSearch index delete missing auth', family='js_route', skip='curl -X DELETE $OS/notes', auth='curl -u admin:$OS $OS/notes', leftover='update'),
    dict(slug='solr-core-skip-delete', plant='azq69keel', ticket='AZ7-70', surface='Solr core unload missing basicAuth', family='js_route', skip='curl -X POST $SOLR/admin/cores?action=UNLOAD&core=notes', auth='curl --user solr:$SOLR $SOLR/admin/cores?action=STATUS&core=notes', leftover='put'),
    dict(slug='meili-idx-skip-delete', plant='azq70keel', ticket='AZ8-71', surface='Meilisearch index delete missing key', family='js_route', skip='curl -X DELETE $MEILI/indexes/notes', auth='curl -H "Authorization: Bearer $MEILI" $MEILI/indexes/notes', leftover='patch'),
    dict(slug='typesense-skip-delete', plant='azq71keel', ticket='AZ9-72', surface='Typesense collection delete missing key', family='js_route', skip='curl -X DELETE $TS/collections/notes', auth='curl -H "X-TYPESENSE-API-KEY: $TS" $TS/collections/notes', leftover='update'),
    dict(slug='vespa-doc-skip-delete', plant='azq72keel', ticket='AZ1-73', surface='Vespa document delete missing cert', family='js_route', skip='vespa document delete id:notes:notes::1', auth='vespa document get id:notes:notes::1 --cert $VESPA', leftover='put'),
    dict(slug='milvus-col-skip-delete', plant='azq73keel', ticket='AZ2-74', surface='Milvus collection drop missing token', family='js_route', skip='curl -X POST $MILVUS/v2/vectordb/collections/drop -d {collectionName:notes}', auth='curl -H "Authorization: Bearer $MILVUS" $MILVUS/v2/vectordb/collections/describe', leftover='patch'),
    dict(slug='qdrant-col-skip-delete', plant='azq74keel', ticket='AZ3-75', surface='Qdrant collection delete missing api-key', family='js_route', skip='curl -X DELETE $QDRANT/collections/notes', auth='curl -H "api-key: $QDRANT" $QDRANT/collections/notes', leftover='update'),
    dict(slug='weaviate-cls-skip-delete', plant='azq75keel', ticket='AZ4-76', surface='Weaviate class delete missing api-key', family='js_route', skip='curl -X DELETE $WV/v1/schema/Notes', auth='curl -H "Authorization: Bearer $WV" $WV/v1/schema/Notes', leftover='put'),
    dict(slug='lancedb-tbl-skip-delete', plant='azq76keel', ticket='AZ5-77', surface='LanceDB table drop missing uri auth', family='js_route', skip='python -c \'import lancedb; lancedb.connect("notes").drop_table("t")\'', auth='python -c \'import lancedb; lancedb.connect("notes").open_table("t")\'', leftover='patch'),
    dict(slug='ray-job-skip-delete', plant='azq77keel', ticket='AZ6-78', surface='Ray job stop missing dashboard token', family='js_route', skip='ray job stop notes', auth='ray job status notes --address $RAY', leftover='update'),
    dict(slug='dask-sched-skip-delete', plant='azq78keel', ticket='AZ7-79', surface='Dask retire missing scheduler auth', family='js_route', skip='curl -X POST $DASK/api/v1/retire', auth='curl $DASK/api/v1/info --header "Authorization: $DASK"', leftover='put'),
    dict(slug='chroma-col-skip-delete', plant='azq79keel', ticket='AZ8-80', surface='Chroma collection delete missing token', family='js_route', skip='curl -X DELETE $CHROMA/api/v1/collections/notes', auth='curl -H "Authorization: Bearer $CHROMA" $CHROMA/api/v1/collections/notes', leftover='patch'),
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
