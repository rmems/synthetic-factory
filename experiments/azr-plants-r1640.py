"""Extra unique IDOR/BFLA plants for authz-regression-factory r1640+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r1639 vesselNNNN-sys.
Not clones of r1364 geohash-cell-idor / channels-consumer-skip-delete.
Not clones of r1445–r1458 casbin/oso/keycloak clones.
Not clones of r1543 gstin-isd-idor / chi-mount-skip-delete.
Not clones of r1544 leftover3 cedar/casbin or r1560 e212-mccmnc / flask-restful.
"""
from __future__ import annotations


EXTRA_IDOR_ROWS = [
    dict(slug='imeitac-idor', plant='ironblock', ticket='IRO-1', surface='IMEI TAC object-id IDOR', mod='imeitacs', model='Imeitac', lookup='imeitac', sample='35693803', owner='oem_id', first='authn', residual='pdf', product='imei-tac', bug='IRO-1 TAC unique from GSMA TAC'),
    dict(slug='snssai-5g-idor', plant='jackblock', ticket='JAC-2', surface='S-NSSAI object-id IDOR', mod='snssais', model='Snssai', lookup='snssai', sample='1-000001', owner='net_id', first='mask', residual='export', product='snssai-5g', bug='JAC-2 S-NSSAI unique from 3GPP'),
    dict(slug='dnn-5g-idor', plant='jumpblock', ticket='JUM-3', surface='5G DNN object-id IDOR', mod='dnn5gs', model='Dnn5g', lookup='dnn5g', sample='internet.mnc410.mcc310.gprs', owner='net_id', first='any_member', residual='search', product='dnn-5g', bug='JUM-3 DNN unique from 3GPP'),
    dict(slug='pei-5g-idor', plant='kedgeblock', ticket='KED-4', surface='5G PEI object-id IDOR', mod='pei5gs', model='Pei5g', lookup='pei5g', sample='imei-356938035643809', owner='oem_id', first='list_scope', residual='mget', product='pei-5g', bug='KED-4 PEI unique from 3GPP'),
    dict(slug='gpsi-5g-idor', plant='kevelblock', ticket='KEV-5', surface='5G GPSI object-id IDOR', mod='gpsi5gs', model='Gpsi5g', lookup='gpsi5g', sample='msisdn-12025550100', owner='net_id', first='authn', residual='csv', product='gpsi-5g', bug='KEV-5 GPSI unique from 3GPP'),
    dict(slug='mtmsi-5g-idor', plant='kickblock', ticket='KIC-6', surface='5G M-TMSI object-id IDOR', mod='mtmsis', model='Mtmsi', lookup='mtmsi', sample='A1B2C3D4', owner='net_id', first='mask', residual='admin', product='mtmsi-5g', bug='KIC-6 M-TMSI unique from 3GPP'),
    dict(slug='stmsi-lte-idor', plant='knitblock', ticket='KNI-7', surface='LTE S-TMSI object-id IDOR', mod='stmsis', model='Stmsi', lookup='stmsi', sample='01-A1B2C3D4', owner='net_id', first='any_member', residual='webhook', product='stmsi-lte', bug='KNI-7 S-TMSI unique from EPS'),
    dict(slug='amfset-idor', plant='lanyblock', ticket='LAN-8', surface='AMF Set object-id IDOR', mod='amfsets', model='Amfset', lookup='amfset', sample='310-410-1-2', owner='net_id', first='list_scope', residual='comments', product='amfset-5g', bug='LAN-8 AMF Set unique from 3GPP'),
    dict(slug='nrarfcn-idor', plant='leebblock', ticket='LEE-9', surface='NR-ARFCN object-id IDOR', mod='nrarfcns', model='Nrarfcn', lookup='nrarfcn', sample='636000', owner='net_id', first='authn', residual='pdf', product='nrarfcn-id', bug='LEE-9 NR-ARFCN unique from 3GPP'),
    dict(slug='earfcn-idor', plant='leecblock', ticket='LEE-1', surface='EARFCN object-id IDOR', mod='earfcns', model='Earfcn', lookup='earfcn', sample='3350', owner='net_id', first='mask', residual='export', product='earfcn-id', bug='LEE-1 EARFCN unique from 3GPP'),
    dict(slug='pcinr-idor', plant='luffcblock', ticket='LUF-2', surface='NR PCI object-id IDOR', mod='pcinrs', model='Pcinr', lookup='pcinr', sample='321', owner='net_id', first='any_member', residual='search', product='pci-nr', bug='LUF-2 PCI unique from 5G NR'),
    dict(slug='trtac-idor', plant='marlspblock', ticket='MAR-3', surface='Tracking Area Code object-id IDOR', mod='trtacs', model='Trtac', lookup='trtac', sample='ABC0', owner='net_id', first='list_scope', residual='mget', product='tac-eps', bug='MAR-3 TAC unique from EPS tracking'),
    dict(slug='ucac4-idor', plant='martbblock', ticket='MAR-4', surface='UCAC4 star object-id IDOR', mod='ucac4s', model='Ucac4', lookup='ucac4', sample='UCAC4 123-012345', owner='lab_id', first='authn', residual='csv', product='ucac4-id', bug='MAR-4 UCAC4 unique from USNO'),
    dict(slug='panstarrs-idor', plant='mastcblock', ticket='MAS-5', surface='Pan-STARRS object-id IDOR', mod='ps1oids', model='Ps1oid', lookup='ps1oid', sample='PSO J053.13419-05.42602', owner='lab_id', first='mask', residual='admin', product='ps1-oid', bug='MAS-5 objID unique from Pan-STARRS'),
    dict(slug='bayer-idor', plant='messlblock', ticket='MES-6', surface='Bayer designation object-id IDOR', mod='bayers', model='Bayer', lookup='bayer', sample='alp CMa', owner='lab_id', first='any_member', residual='webhook', product='bayer-id', bug='MES-6 Bayer unique from Uranometria'),
    dict(slug='flamsteed-idor', plant='mizzbblock', ticket='MIZ-7', surface='Flamsteed designation object-id IDOR', mod='flamsteeds', model='Flamsteed', lookup='flamsteed', sample='9 Pup', owner='lab_id', first='list_scope', residual='comments', product='flamsteed-id', bug='MIZ-7 Flamsteed unique from catalog'),
    dict(slug='gliese-idor', plant='moorbblock', ticket='MOO-8', surface='Gliese catalog object-id IDOR', mod='glieses', model='Gliese', lookup='gliese', sample='GJ 581', owner='lab_id', first='authn', residual='pdf', product='gliese-id', bug='MOO-8 Gliese unique from CNS'),
    dict(slug='ross-star-idor', plant='nettyblock', ticket='NET-9', surface='Ross star object-id IDOR', mod='rossstars', model='Rossstar', lookup='rossstar', sample='Ross 154', owner='lab_id', first='mask', residual='export', product='ross-star', bug='NET-9 Ross unique from catalog'),
    dict(slug='wolf-star-idor', plant='nippbblock', ticket='NIP-1', surface='Wolf star object-id IDOR', mod='wolfstars', model='Wolfstar', lookup='wolfstar', sample='Wolf 359', owner='lab_id', first='any_member', residual='search', product='wolf-star', bug='NIP-1 Wolf unique from catalog'),
    dict(slug='luyten-idor', plant='nockpblock', ticket='NOC-2', surface='Luyten star object-id IDOR', mod='luytens', model='Luyten', lookup='luyten', sample='Luyten 726-8', owner='lab_id', first='list_scope', residual='mget', product='luyten-id', bug='NOC-2 Luyten unique from LHS'),
    dict(slug='giclas-idor', plant='oakpblock', ticket='OAK-3', surface='Giclas star object-id IDOR', mod='giclass', model='Giclas', lookup='giclas', sample='G 196-3', owner='lab_id', first='authn', residual='csv', product='giclas-id', bug='OAK-3 Giclas unique from Lowell'),
    dict(slug='lalande-idor', plant='orlobblock', ticket='ORL-4', surface='Lalande star object-id IDOR', mod='lalandes', model='Lalande', lookup='lalande', sample='Lalande 21185', owner='lab_id', first='mask', residual='admin', product='lalande-id', bug='ORL-4 Lalande unique from Histoire'),
    dict(slug='sao-cat-idor', plant='outhbblock', ticket='OUT-5', surface='SAO catalog object-id IDOR', mod='saocats', model='Saocat', lookup='saocat', sample='SAO 151881', owner='lab_id', first='any_member', residual='webhook', product='sao-cat', bug='OUT-5 SAO unique from Smithsonian'),
    dict(slug='ppm-star-idor', plant='outrbblock', ticket='OUT-6', surface='PPM star object-id IDOR', mod='ppmstars', model='Ppmstar', lookup='ppmstar', sample='PPM 171367', owner='lab_id', first='list_scope', residual='comments', product='ppm-star', bug='OUT-6 PPM unique from ARI'),
    dict(slug='toi-tess-idor', plant='painbblock', ticket='PAI-7', surface='TESS TOI object-id IDOR', mod='toitesss', model='Toitess', lookup='toiid', sample='TOI-700', owner='lab_id', first='authn', residual='pdf', product='toi-tess', bug='PAI-7 TOI unique from TESS'),
    dict(slug='wasp-planet-idor', plant='parbbblock', ticket='PAR-8', surface='WASP planet object-id IDOR', mod='wasps', model='Wasp', lookup='waspid', sample='WASP-12b', owner='lab_id', first='mask', residual='export', product='wasp-pl', bug='PAR-8 WASP unique from SuperWASP'),
    dict(slug='hatp-planet-idor', plant='parrbblock', ticket='PAR-9', surface='HATNet planet object-id IDOR', mod='hatps', model='Hatp', lookup='hatpid', sample='HAT-P-7b', owner='lab_id', first='any_member', residual='search', product='hatp-pl', bug='PAR-9 HAT-P unique from HATNet'),
    dict(slug='tres-planet-idor', plant='paunbblock', ticket='PAU-1', surface='TrES planet object-id IDOR', mod='tress', model='Tres', lookup='tresid', sample='TrES-2b', owner='lab_id', first='list_scope', residual='mget', product='tres-pl', bug='PAU-1 TrES unique from transits'),
    dict(slug='corot-planet-idor', plant='peakbblock', ticket='PEA-2', surface='CoRoT planet object-id IDOR', mod='corots', model='Corot', lookup='corotid', sample='CoRoT-7b', owner='lab_id', first='authn', residual='csv', product='corot-pl', bug='PEA-2 CoRoT unique from CNES'),
    dict(slug='kelt-planet-idor', plant='pendbblock', ticket='PEN-3', surface='KELT planet object-id IDOR', mod='kelts', model='Kelt', lookup='keltid', sample='KELT-9b', owner='lab_id', first='mask', residual='admin', product='kelt-pl', bug='PEN-3 KELT unique from survey'),
    dict(slug='ogle-planet-idor', plant='prevbblock', ticket='PRE-4', surface='OGLE microlens object-id IDOR', mod='ogles', model='Ogle', lookup='ogleid', sample='OGLE-2016-BLG-1195L', owner='lab_id', first='any_member', residual='webhook', product='ogle-pl', bug='PRE-4 OGLE unique from Warsaw'),
    dict(slug='moa-planet-idor', plant='quoibblock', ticket='QUO-5', surface='MOA microlens object-id IDOR', mod='moas', model='Moa', lookup='moaid', sample='MOA-2007-BLG-192L', owner='lab_id', first='list_scope', residual='comments', product='moa-pl', bug='QUO-5 MOA unique from Nagoya'),
    dict(slug='isone-asset-idor', plant='rabbbblock', ticket='RAB-6', surface='ISO-NE asset object-id IDOR', mod='isoneas', model='Isonea', lookup='isonea', sample='40327', owner='grid_id', first='authn', residual='pdf', product='isone-asset', bug='RAB-6 asset unique from ISO-NE'),
    dict(slug='wecc-path-idor', plant='ratlbblock', ticket='RAT-7', surface='WECC path object-id IDOR', mod='weccpaths', model='Weccpath', lookup='weccpath', sample='Path 26', owner='grid_id', first='mask', residual='export', product='wecc-path', bug='RAT-7 path unique from WECC'),
    dict(slug='serc-ba-idor', plant='reefcblock', ticket='REE-8', surface='SERC BA object-id IDOR', mod='sercbas', model='Sercba', lookup='sercba', sample='SOCO', owner='grid_id', first='any_member', residual='search', product='serc-ba', bug='REE-8 BA unique from SERC'),
    dict(slug='eia923-idor', plant='ribbbblock', ticket='RIB-9', surface='EIA-923 plant object-id IDOR', mod='eia923s', model='Eia923', lookup='eia923', sample='579', owner='grid_id', first='list_scope', residual='mget', product='eia-923', bug='RIB-9 plant unique from EIA-923'),
    dict(slug='ferc-docket-idor', plant='robabblock', ticket='ROB-1', surface='FERC docket object-id IDOR', mod='fercdks', model='Fercdk', lookup='fercdk', sample='ER24-1234-000', owner='grid_id', first='authn', residual='csv', product='ferc-docket', bug='ROB-1 docket unique from FERC eLibrary'),
    dict(slug='aeso-pool-idor', plant='rounbblock', ticket='ROU-2', surface='AESO pool object-id IDOR', mod='aesopools', model='Aesopool', lookup='aesopool', sample='AESO-1234', owner='grid_id', first='mask', residual='admin', product='aeso-pool', bug='ROU-2 pool unique from AESO'),
    dict(slug='ieso-zone-idor', plant='rowlbblock', ticket='ROW-3', surface='IESO zone object-id IDOR', mod='iesozones', model='Iesozone', lookup='iesozone', sample='ON-ZONE-TOR', owner='grid_id', first='any_member', residual='webhook', product='ieso-zone', bug='ROW-3 zone unique from IESO'),
    dict(slug='bpa-point-idor', plant='samsbblock', ticket='SAM-4', surface='BPA point object-id IDOR', mod='bpapoints', model='Bpapoint', lookup='bpapoint', sample='MIDWAY', owner='grid_id', first='list_scope', residual='comments', product='bpa-point', bug='SAM-4 point unique from BPA'),
    dict(slug='tva-bus-idor', plant='scutbblock', ticket='SCU-5', surface='TVA bus object-id IDOR', mod='tvabuses', model='Tvabus', lookup='tvabus', sample='5001', owner='grid_id', first='authn', residual='pdf', product='tva-bus', bug='SCU-5 bus unique from TVA'),
    dict(slug='nordpool-idor', plant='seacbblock', ticket='SEA-6', surface='Nord Pool area object-id IDOR', mod='nordpools', model='Nordpool', lookup='nordpool', sample='SE3', owner='grid_id', first='mask', residual='export', product='nordpool-id', bug='SEA-6 area unique from Nord Pool'),
    dict(slug='epex-spot-idor', plant='seizbblock', ticket='SEI-7', surface='EPEX SPOT area object-id IDOR', mod='epexs', model='Epex', lookup='epexid', sample='DE-LU', owner='grid_id', first='any_member', residual='search', product='epex-spot', bug='SEI-7 area unique from EPEX'),
    dict(slug='omie-area-idor', plant='sennbblock', ticket='SEN-8', surface='OMIE area object-id IDOR', mod='omies', model='Omie', lookup='omieid', sample='ES', owner='grid_id', first='list_scope', residual='mget', product='omie-area', bug='SEN-8 area unique from OMIE'),
    dict(slug='gme-ipex-idor', plant='shacbblock', ticket='SHA-9', surface='GME IPEX object-id IDOR', mod='gmeipexs', model='Gmeipex', lookup='gmeipex', sample='IT-North', owner='grid_id', first='authn', residual='csv', product='gme-ipex', bug='SHA-9 zone unique from GME'),
    dict(slug='fsc-group-idor', plant='sheebblock', ticket='SHE-1', surface='FSC group object-id IDOR', mod='fscgrps', model='Fscgrp', lookup='fscgrp', sample='53', owner='depot_id', first='mask', residual='admin', product='fsc-group', bug='SHE-1 FSC unique from FSC'),
    dict(slug='mil-std-idor', plant='shrobblock', ticket='SHR-2', surface='MIL-STD object-id IDOR', mod='milstds', model='Milstd', lookup='milstd', sample='MIL-STD-188-141', owner='firm_id', first='any_member', residual='webhook', product='mil-std', bug='SHR-2 MIL-STD unique from ASSIST'),
    dict(slug='stanag-idor', plant='skegbblock', ticket='SKE-3', surface='STANAG object-id IDOR', mod='stanags', model='Stanag', lookup='stanag', sample='STANAG 4586', owner='firm_id', first='list_scope', residual='comments', product='stanag-id', bug='SKE-3 STANAG unique from NATO'),
    dict(slug='fips-pub-idor', plant='slabbblock', ticket='SLA-4', surface='FIPS pub object-id IDOR', mod='fipspubs', model='Fipspub', lookup='fipspub', sample='FIPS 140-3', owner='firm_id', first='authn', residual='pdf', product='fips-pub', bug='SLA-4 FIPS unique from NIST'),
    dict(slug='nist-sp-idor', plant='snatbblock', ticket='SNA-5', surface='NIST SP object-id IDOR', mod='nistsps', model='Nistsp', lookup='nistsp', sample='SP 800-53', owner='firm_id', first='mask', residual='export', product='nist-sp', bug='SNA-5 SP unique from NIST'),
    dict(slug='ansi-std-idor', plant='snorbblock', ticket='SNO-6', surface='ANSI standard object-id IDOR', mod='ansistds', model='Ansistd', lookup='ansistd', sample='ANSI X9.24', owner='firm_id', first='any_member', residual='search', product='ansi-std', bug='SNO-6 ANSI unique from ANSI'),
    dict(slug='iso-std-idor', plant='spanbblock', ticket='SPA-7', surface='ISO standard object-id IDOR', mod='isostds', model='Isostd', lookup='isostd', sample='ISO/IEC 27001', owner='firm_id', first='list_scope', residual='mget', product='iso-std', bug='SPA-7 ISO unique from ISO'),
    dict(slug='iec-std-idor', plant='spenbblock', ticket='SPE-8', surface='IEC standard object-id IDOR', mod='iecstds', model='Iecstd', lookup='iecstd', sample='IEC 61850', owner='firm_id', first='authn', residual='csv', product='iec-std', bug='SPE-8 IEC unique from IEC'),
    dict(slug='itu-rec-idor', plant='sprehblock', ticket='SPR-9', surface='ITU-T rec object-id IDOR', mod='iturecs', model='Iturec', lookup='iturec', sample='ITU-T X.509', owner='firm_id', first='mask', residual='admin', product='itu-rec', bug='SPR-9 rec unique from ITU-T'),
    dict(slug='ieee-std-idor', plant='spribblock', ticket='SPR-1', surface='IEEE standard object-id IDOR', mod='ieeestds', model='Ieeestd', lookup='ieeestd', sample='IEEE 802.1X', owner='firm_id', first='any_member', residual='webhook', product='ieee-std', bug='SPR-1 std unique from IEEE'),
    dict(slug='etsi-ts-idor', plant='stanbblock', ticket='STA-2', surface='ETSI TS object-id IDOR', mod='etsitss', model='Etsits', lookup='etsits', sample='TS 133 501', owner='firm_id', first='list_scope', residual='comments', product='etsi-ts', bug='STA-2 TS unique from ETSI'),
    dict(slug='ts3gpp-idor', plant='steebblock', ticket='STE-3', surface='3GPP TS object-id IDOR', mod='ts3gpps', model='Ts3gpp', lookup='ts3gpp', sample='TS 33.501', owner='firm_id', first='authn', residual='pdf', product='ts-3gpp', bug='STE-3 TS unique from 3GPP'),
    dict(slug='oval-def-idor', plant='stopbblock', ticket='STO-4', surface='OVAL definition object-id IDOR', mod='ovaldefs', model='Ovaldef', lookup='ovaldef', sample='oval:org:def:1234', owner='lab_id', first='mask', residual='export', product='oval-def', bug='STO-4 OVAL unique from MITRE'),
    dict(slug='xccdf-idor', plant='strabblock', ticket='STR-5', surface='XCCDF benchmark object-id IDOR', mod='xccdfs', model='Xccdf', lookup='xccdf', sample='xccdf_org.ssgproject.content_benchmark_RHEL8', owner='lab_id', first='any_member', residual='search', product='xccdf-id', bug='STR-5 XCCDF unique from SCAP'),
    dict(slug='cce-idor', plant='studbblock', ticket='STU-6', surface='CCE object-id IDOR', mod='cceids', model='Cceid', lookup='cceid', sample='CCE-80957-6', owner='lab_id', first='list_scope', residual='mget', product='cce-id', bug='STU-6 CCE unique from NVD'),
    dict(slug='cci-idor', plant='tabebblock', ticket='TAB-7', surface='CCI object-id IDOR', mod='cciids', model='Cciid', lookup='cciid', sample='CCI-000213', owner='lab_id', first='authn', residual='csv', product='cci-id', bug='TAB-7 CCI unique from DISA'),
    dict(slug='stig-rule-idor', plant='tackbblock', ticket='TAC-8', surface='STIG rule object-id IDOR', mod='stigids', model='Stigid', lookup='stigid', sample='SV-204392r928517_rule', owner='lab_id', first='mask', residual='admin', product='stig-rule', bug='TAC-8 rule unique from DISA STIG'),
    dict(slug='nessus-plugin-idor', plant='taffbblock', ticket='TAF-9', surface='Nessus plugin object-id IDOR', mod='nessuss', model='Nessus', lookup='nessus', sample='19506', owner='lab_id', first='any_member', residual='webhook', product='nessus-pl', bug='TAF-9 plugin unique from Tenable'),
    dict(slug='snort-sid-idor', plant='thimbblock', ticket='THI-1', surface='Snort SID object-id IDOR', mod='snortsids', model='Snortsid', lookup='snortsid', sample='1:2019401', owner='lab_id', first='list_scope', residual='comments', product='snort-sid', bug='THI-1 SID unique from Snort'),
    dict(slug='yara-rule-idor', plant='throbblock', ticket='THR-2', surface='YARA rule object-id IDOR', mod='yararules', model='Yararule', lookup='yararule', sample='win_emotet_bytecodes', owner='lab_id', first='authn', residual='pdf', product='yara-rule', bug='THR-2 rule unique from YARA repo'),
    dict(slug='sigma-rule-idor', plant='thwabblock', ticket='THW-3', surface='Sigma rule object-id IDOR', mod='sigmarules', model='Sigmarule', lookup='sigmarule', sample='win_susp_service_installation', owner='lab_id', first='mask', residual='export', product='sigma-rule', bug='THW-3 rule unique from SigmaHQ'),
    dict(slug='attck-tech-idor', plant='tillbblock', ticket='TIL-4', surface='ATT&CK technique object-id IDOR', mod='attcks', model='Attck', lookup='attck', sample='T1059.001', owner='lab_id', first='any_member', residual='search', product='attck-tech', bug='TIL-4 technique unique from MITRE ATT&CK'),
    dict(slug='jstor-stable-idor', plant='toggbblock', ticket='TOG-5', surface='JSTOR stable object-id IDOR', mod='jstors', model='Jstor', lookup='jstor', sample='10.2307/123456', owner='campus_id', first='list_scope', residual='mget', product='jstor-id', bug='TOG-5 stable unique from JSTOR'),
    dict(slug='philpapers-idor', plant='toppbblock', ticket='TOP-6', surface='PhilPapers object-id IDOR', mod='philps', model='Philp', lookup='philp', sample='PHI-2024-1234', owner='campus_id', first='authn', residual='csv', product='philpapers-id', bug='TOP-6 id unique from PhilPapers'),
    dict(slug='worldbank-id-idor', plant='tranbblock', ticket='TRA-7', surface='World Bank indicator object-id IDOR', mod='wbinds', model='Wbind', lookup='wbind', sample='NY.GDP.MKTP.CD', owner='campus_id', first='mask', residual='admin', product='wbind-id', bug='TRA-7 indicator unique from WDI'),
    dict(slug='imf-ifs-idor', plant='treebblock', ticket='TRE-8', surface='IMF IFS object-id IDOR', mod='imfifss', model='Imfifs', lookup='imfifs', sample='IFS.M.US.PMP_IX', owner='campus_id', first='any_member', residual='webhook', product='imf-ifs', bug='TRE-8 series unique from IMF'),
    dict(slug='un-symbol-idor', plant='trucbblock', ticket='TRU-9', surface='UN document symbol object-id IDOR', mod='unsyms', model='Unsym', lookup='unsym', sample='A/RES/70/1', owner='campus_id', first='list_scope', residual='comments', product='un-symbol', bug='TRU-9 symbol unique from ODS'),
    dict(slug='fednow-imad-idor', plant='trysbblock', ticket='TRY-1', surface='FedNow IMAD object-id IDOR', mod='fednows', model='Fednow', lookup='fednow', sample='20240115MMQFMPF000001', owner='bank_id', first='authn', residual='pdf', product='fednow-imad', bug='TRY-1 IMAD unique from FedNow'),
    dict(slug='chips-seq-idor', plant='tumbbblock', ticket='TUM-2', surface='CHIPS sequence object-id IDOR', mod='chipsseqs', model='Chipsseq', lookup='chipsseq', sample='240115000001', owner='bank_id', first='mask', residual='export', product='chips-seq', bug='TUM-2 seq unique from CHIPS'),
    dict(slug='tips-ecb-idor', plant='turnbblock', ticket='TUR-3', surface='TIPS payment object-id IDOR', mod='tipsecbs', model='Tipsecb', lookup='tipsecb', sample='TIPS202401151234', owner='bank_id', first='any_member', residual='search', product='tips-ecb', bug='TUR-3 id unique from ECB TIPS'),
    dict(slug='target2-idor', plant='uphrbblock', ticket='UPH-4', surface='TARGET2 msg object-id IDOR', mod='target2s', model='Target2', lookup='target2', sample='TGT240115ABCDEF', owner='bank_id', first='list_scope', residual='mget', product='target2-id', bug='UPH-4 msg unique from TARGET2'),
    dict(slug='sepa-e2e-idor', plant='vangbblock', ticket='VAN-5', surface='SEPA E2E object-id IDOR', mod='sepae2es', model='Sepae2e', lookup='sepae2e', sample='NOTPROVIDED-240115-1', owner='bank_id', first='authn', residual='csv', product='sepa-e2e', bug='VAN-5 E2E unique from EPC'),
    dict(slug='rtp-fed-idor', plant='walebblock', ticket='WAL-6', surface='RTP payment object-id IDOR', mod='rtpfeds', model='Rtpfed', lookup='rtpfed', sample='20240115TCH0000001', owner='bank_id', first='mask', residual='admin', product='rtp-fed', bug='WAL-6 id unique from TCH RTP'),
    dict(slug='cnaps-ncc-idor', plant='warpbblock', ticket='WAR-7', surface='CNAPS NCC object-id IDOR', mod='cnapsnccs', model='Cnapsncc', lookup='cnapsncc', sample='102100099996', owner='bank_id', first='any_member', residual='webhook', product='cnaps-ncc', bug='WAR-7 NCC unique from PBOC'),
    dict(slug='iso20022-msg-idor', plant='weatbblock', ticket='WEA-8', surface='ISO 20022 MsgId object-id IDOR', mod='iso20022s', model='Iso20022', lookup='iso20022', sample='MSGID-BANK-240115-0001', owner='bank_id', first='list_scope', residual='comments', product='iso20022-msg', bug='WEA-8 MsgId unique from ISO 20022'),
]


BFLA_ROWS = [
    dict(slug='flask-httpauth-skip-delete', plant='ironblock', ticket='IRO-1', surface='Flask-HTTPAuth delete missing login_required', family='py_async', skip="@app.delete('/notes/<nid>')\ndef delete(nid):\n    notes.del(nid)", auth="@app.get('/notes/<nid>')\n@auth.login_required\ndef get(nid):\n    return notes.get(nid, auth.current_user())", leftover='put'),
    dict(slug='flask-principal-skip-delete', plant='jackblock', ticket='JAC-2', surface='Flask-Principal delete missing Permission', family='py_async', skip="@app.delete('/notes/<nid>')\ndef delete(nid):\n    notes.del(nid)", auth="@app.get('/notes/<nid>')\n@Permission(RoleNeed('user')).require()\ndef get(nid):\n    return notes.get(nid, g.identity)", leftover='patch'),
    dict(slug='flask-security-skip-delete', plant='jumpblock', ticket='JUM-3', surface='Flask-Security delete missing roles_required', family='py_async', skip="@app.delete('/notes/<nid>')\ndef delete(nid):\n    notes.del(nid)", auth="@app.get('/notes/<nid>')\n@roles_required('user')\ndef get(nid):\n    return notes.get(nid, current_user)", leftover='update'),
    dict(slug='flask-login-skip-delete', plant='kedgeblock', ticket='KED-4', surface='Flask-Login delete missing login_required', family='py_async', skip="@app.delete('/notes/<nid>')\ndef delete(nid):\n    notes.del(nid)", auth="@app.get('/notes/<nid>')\n@login_required\ndef get(nid):\n    return notes.get(nid, current_user)", leftover='put'),
    dict(slug='drf-spectacular-skip-delete', plant='kevelblock', ticket='KEV-5', surface='drf-spectacular delete missing extend_schema auth', family='py_async', skip='class NoteView(DestroyAPIView):\n    authentication_classes = []', auth='class NoteView(RetrieveAPIView):\n    authentication_classes = [SessionAuthentication]', leftover='patch'),
    dict(slug='rest-knox-skip-delete', plant='kickblock', ticket='KIC-6', surface='django-rest-knox delete missing TokenAuthentication', family='py_async', skip='class NoteDelete(APIView):\n    authentication_classes = []\n    def delete(self, request, nid): notes.del(nid)', auth='class NoteGet(APIView):\n    authentication_classes = [TokenAuthentication]\n    def get(self, request, nid): return notes.get(nid, request.user)', leftover='update'),
    dict(slug='uvicorn-asgi-skip-delete', plant='knitblock', ticket='KNI-7', surface='uvicorn ASGI DELETE missing auth scope', family='py_async', skip="if scope['method']=='DELETE': await notes.del(path)", auth="if scope['method']=='GET': user=scope['user']; return await notes.get(path, user)", leftover='put'),
    dict(slug='gunicorn-app-skip-delete', plant='lanyblock', ticket='LAN-8', surface='Gunicorn WSGI DELETE missing environ auth', family='py_async', skip="if environ['REQUEST_METHOD']=='DELETE': notes.del(path)", auth="if environ['REQUEST_METHOD']=='GET': user=environ['REMOTE_USER']; return notes.get(path, user)", leftover='patch'),
    dict(slug='waitress-wsgi-skip-delete', plant='leebblock', ticket='LEE-9', surface='Waitress WSGI DELETE missing auth', family='py_async', skip="if method=='DELETE': notes.del(path)", auth="if method=='GET': auth(environ); return notes.get(path, environ['user'])", leftover='update'),
    dict(slug='cheroot-wsgi-skip-delete', plant='leecblock', ticket='LEE-1', surface='Cheroot WSGI DELETE missing auth', family='py_async', skip="if req.method=='DELETE': notes.del(req.path)", auth="if req.method=='GET': req.login(); return notes.get(req.path, req.user)", leftover='put'),
    dict(slug='meinheld-wsgi-skip-delete', plant='luffcblock', ticket='LUF-2', surface='Meinheld WSGI DELETE missing auth', family='py_async', skip="if environ['REQUEST_METHOD']=='DELETE': notes.del(path)", auth="if environ['REQUEST_METHOD']=='GET': return notes.get(path, environ['user'])", leftover='patch'),
    dict(slug='bjoern-wsgi-skip-delete', plant='marlspblock', ticket='MAR-3', surface='bjoern WSGI DELETE missing auth', family='py_async', skip="if method=='DELETE': notes.del(path)", auth="if method=='GET': user=auth(environ); return notes.get(path, user)", leftover='update'),
    dict(slug='gevent-pywsgi-skip-delete', plant='martbblock', ticket='MAR-4', surface='gevent.pywsgi DELETE missing auth', family='py_async', skip="if env['REQUEST_METHOD']=='DELETE': notes.del(path)", auth="if env['REQUEST_METHOD']=='GET': return notes.get(path, env.get('user'))", leftover='put'),
    dict(slug='eventlet-wsgi-skip-delete', plant='mastcblock', ticket='MAS-5', surface='eventlet.wsgi DELETE missing auth', family='py_async', skip="if environ['REQUEST_METHOD']=='DELETE': notes.del(path)", auth="if environ['REQUEST_METHOD']=='GET': return notes.get(path, environ['user'])", leftover='patch'),
    dict(slug='lura-krakend-skip-delete', plant='messlblock', ticket='MES-6', surface='KrakenD Lura DELETE missing auth/validator', family='js_route', skip='{"endpoint": "/notes/{id}", "method": "DELETE", "extra_config": {}}', auth='{"endpoint": "/notes/{id}", "method": "GET", "extra_config": {"auth/validator": {"alg": "RS256"}}}', leftover='update'),
    dict(slug='tyk-mw-skip-delete', plant='mizzbblock', ticket='MIZ-7', surface='Tyk middleware DELETE missing auth', family='js_route', skip='listen_path: /notes/{id}\nmethod: DELETE\nuse_keyless: true', auth='listen_path: /notes/{id}\nmethod: GET\nauth: {auth_header_name: Authorization}', leftover='put'),
    dict(slug='caddy-auth-skip-delete', plant='moorbblock', ticket='MOO-8', surface='Caddy DELETE outside basic_auth', family='js_route', skip='handle /notes/* {\n  reverse_proxy notes:8080\n}', auth='handle /notes/* {\n  basic_auth { user hash }\n  reverse_proxy notes:8080\n}', leftover='patch'),
    dict(slug='nginx-authreq-skip-delete', plant='nettyblock', ticket='NET-9', surface='nginx auth_request skip DELETE', family='js_route', skip='location /notes/ { if ($request_method = DELETE) { proxy_pass http://notes; } }', auth='location /notes/ { auth_request /_auth; proxy_pass http://notes; }', leftover='update'),
    dict(slug='haproxy-acl-skip-delete', plant='nippbblock', ticket='NIP-1', surface='HAProxy ACL skip DELETE', family='js_route', skip='acl is_del method DELETE\nhttp-request allow if is_del', auth='http-request auth if !{ http_auth(users) }', leftover='put'),
    dict(slug='apache-authz-skip-delete', plant='nockpblock', ticket='NOC-2', surface='Apache Require skip DELETE', family='js_route', skip='<Limit DELETE>\n  Require all granted\n</Limit>', auth='<Limit GET>\n  Require valid-user\n</Limit>', leftover='patch'),
    dict(slug='lighttpd-auth-skip-delete', plant='oakpblock', ticket='OAK-3', surface='lighttpd DELETE missing auth.backend', family='js_route', skip='$HTTP["request-method"] == "DELETE" { proxy.server = ( notes ) }', auth='auth.require = ( "/notes/" => ( "method" => "basic" ) )', leftover='update'),
    dict(slug='openresty-skip-delete', plant='orlobblock', ticket='ORL-4', surface='OpenResty DELETE missing access_by_lua auth', family='js_route', skip="if ngx.req.get_method()=='DELETE' then notes.del() end", auth="access_by_lua_block { require('auth').check() }", leftover='put'),
    dict(slug='apisix-plugin-skip-delete', plant='outhbblock', ticket='OUT-5', surface='APISIX DELETE missing jwt-auth plugin', family='js_route', skip='uris: [/notes/*]\nmethods: [DELETE]\nplugins: {}', auth='uris: [/notes/*]\nmethods: [GET]\nplugins: { jwt-auth: {} }', leftover='patch'),
    dict(slug='skipper-pred-skip-delete', plant='outrbblock', ticket='OUT-6', surface='Skipper Path DELETE missing authFilter', family='js_route', skip='r: Path("/notes/:id") && Method("DELETE") -> notes();', auth='r: Path("/notes/:id") && Method("GET") -> authFilter() -> notes();', leftover='update'),
    dict(slug='contour-httpproxy-skip-delete', plant='painbblock', ticket='PAI-7', surface='Contour HTTPProxy DELETE missing jwt', family='js_route', skip='conditions: [{prefix: /notes}]\npermitInsecure: true', auth='conditions: [{prefix: /notes}]\nauthPolicy: {jwt: {require: true}}', leftover='put'),
    dict(slug='linkerd-auth-skip-delete', plant='parbbblock', ticket='PAR-8', surface='Linkerd ServerAuthorization skip DELETE', family='js_route', skip='spec:\n  client: unauthenticated: true\n  server: notes-delete', auth="spec:\n  client: meshTLS: {identities: ['notes.ns.serviceaccount.identity.linkerd.cluster.local']}", leftover='patch'),
    dict(slug='consul-intent-skip-delete', plant='parrbblock', ticket='PAR-9', surface='Consul intention skip DELETE', family='js_route', skip='Action = "allow"\nSourceName = "*"\nDestinationName = "notes-delete"', auth='Action = "allow"\nSourceName = "notes-ui"\nDestinationName = "notes"', leftover='update'),
    dict(slug='nomad-acl-skip-delete', plant='paunbblock', ticket='PAU-1', surface='Nomad ACL skip job delete', family='js_route', skip='namespace "default" { policy = "write" }  # delete job unscoped', auth='namespace "default" { policy = "read" }', leftover='put'),
    dict(slug='boundary-skip-delete', plant='peakbblock', ticket='PEA-2', surface='Boundary target delete missing authorize-session', family='js_route', skip='boundary targets delete -id ttcp_notes', auth='boundary targets authorize-session -id ttcp_notes -token env://BOUNDARY', leftover='patch'),
    dict(slug='lunatic-skip-delete', plant='pendbblock', ticket='PEN-3', surface='Lunatic process delete missing auth', family='rust_ext', skip='fn delete(id: i32) { notes::del(id) }', auth='fn get(id: i32, user: User) { notes::get(id, user.id) }', leftover='update'),
    dict(slug='axum-login-skip-delete', plant='prevbblock', ticket='PRE-4', surface='axum-login delete missing AuthSession', family='rust_ext', skip='async fn delete(Path(id): Path<i32>) { notes::del(id).await }', auth='async fn get(AuthSession(user): AuthSession<User>, Path(id): Path<i32>) { notes::get(id, user.id).await }', leftover='put'),
    dict(slug='actix-httpauth-skip-delete', plant='quoibblock', ticket='QUO-5', surface='actix-web-httpauth delete missing HttpAuthentication', family='rust_ext', skip='web::resource("/notes/{id}").route(web::delete().to(del))', auth='web::resource("/notes/{id}").wrap(HttpAuthentication::bearer(validator)).route(web::get().to(get))', leftover='patch'),
    dict(slug='masstransit-skip-delete', plant='rabbbblock', ticket='RAB-6', surface='MassTransit consumer delete missing Authorize', family='js_route', skip='public Task Consume(DeleteNote m) => notes.Del(m.Id);', auth='[Authorize] public Task Consume(GetNote m) => notes.Get(m.Id, context.User);', leftover='update'),
    dict(slug='nservicebus-skip-delete', plant='ratlbblock', ticket='RAT-7', surface='NServiceBus handler delete missing identity', family='js_route', skip='public Task Handle(DeleteNote m, IMessageHandlerContext c) => notes.Del(m.Id);', auth="public Task Handle(GetNote m, IMessageHandlerContext c) { c.MessageHeaders['User']; return notes.Get(m.Id, user); }", leftover='put'),
    dict(slug='hangfire-skip-delete', plant='reefcblock', ticket='REE-8', surface='Hangfire job delete missing DashboardAuthorization', family='js_route', skip='RecurringJob.AddOrUpdate("del", () => notes.Del(id), Cron.Never);', auth='DashboardOptions { Authorization = new[] { new LocalRequestsOnlyAuthorizationFilter() } }', leftover='patch'),
    dict(slug='quartznet-skip-delete', plant='ribbbblock', ticket='RIB-9', surface='Quartz.NET job delete missing IJobAuth', family='js_route', skip='public Task Execute(IJobExecutionContext c) => notes.Del(c.MergedJobDataMap.GetInt("id"));', auth='public Task Execute(IJobExecutionContext c) { auth(c); return notes.Get(id, user); }', leftover='update'),
    dict(slug='blazor-circuit-skip-delete', plant='robabblock', ticket='ROB-1', surface='Blazor circuit Delete missing AuthorizeView', family='js_route', skip='private async Task Delete(int id) => await notes.Del(id);', auth='[Authorize] private async Task<Note> Get(int id) => await notes.Get(id, user);', leftover='put'),
    dict(slug='razor-pages-skip-delete', plant='rounbblock', ticket='ROU-2', surface='Razor Pages OnPostDelete missing Authorize', family='js_route', skip='public IActionResult OnPostDelete(int id) { notes.Del(id); return Redirect(); }', auth='[Authorize] public IActionResult OnGet(int id) => Page(notes.Get(id, User));', leftover='patch'),
    dict(slug='mvc5-skip-delete', plant='rowlbblock', ticket='ROW-3', surface='ASP.NET MVC 5 Delete missing Authorize', family='js_route', skip='public ActionResult Delete(int id) { notes.Del(id); return Redirect(); }', auth='[Authorize] public ActionResult Details(int id) => View(notes.Get(id, User));', leftover='update'),
    dict(slug='webforms-skip-delete', plant='samsbblock', ticket='SAM-4', surface='Web Forms Delete missing IsAuthenticated', family='js_route', skip='protected void BtnDelete_Click(object s, EventArgs e) { notes.Del(id); }', auth='protected void Page_Load(object s, EventArgs e) { if (!User.Identity.IsAuthenticated) Response.Redirect("/login"); }', leftover='put'),
    dict(slug='wcf-skip-delete', plant='scutbblock', ticket='SCU-5', surface='WCF Delete missing ServiceAuthorization', family='js_route', skip='public void Delete(int id) { notes.Del(id); }', auth='[PrincipalPermission(SecurityAction.Demand, Authenticated=true)] public Note Get(int id) => notes.Get(id, ServiceSecurityContext.Current);', leftover='patch'),
    dict(slug='corewcf-skip-delete', plant='seacbblock', ticket='SEA-6', surface='CoreWCF Delete missing OperationBehavior auth', family='js_route', skip='public void Delete(int id) { notes.Del(id); }', auth='[Authorize] public Note Get(int id) => notes.Get(id, User);', leftover='update'),
    dict(slug='wintercms-skip-delete', plant='seizbblock', ticket='SEI-7', surface='Winter CMS delete missing BackendAuth', family='php_mw', skip='public function delete($id) { Note::find($id)->delete(); }', auth='public function preview($id) { BackendAuth::check(); return Note::find($id); }', leftover='put'),
    dict(slug='boltcms-skip-delete', plant='sennbblock', ticket='SEN-8', surface='Bolt CMS delete missing isGranted', family='php_mw', skip='public function delete(int $id) { $this->notes->delete($id); }', auth="public function view(int $id) { $this->isGranted('ROLE_USER'); return $this->notes->find($id); }", leftover='patch'),
    dict(slug='processwire-skip-delete', plant='shacbblock', ticket='SHA-9', surface='ProcessWire delete missing $user->isLoggedin', family='php_mw', skip='$pages->delete($pages->get($id));', auth='if (!$user->isLoggedin()) throw new WirePermissionException(); $pages->get($id);', leftover='update'),
    dict(slug='expressionengine-skip-delete', plant='sheebblock', ticket='SHE-1', surface='ExpressionEngine delete missing ee()->session', family='php_mw', skip="ee()->db->delete('notes', ['id' => $id]);", auth="if (!ee()->session->userdata('member_id')) return; ee()->db->get_where('notes', ['id'=>$id]);", leftover='put'),
    dict(slug='concretecms-skip-delete', plant='shrobblock', ticket='SHR-2', surface='Concrete CMS delete missing Permissions', family='php_mw', skip='$note->delete();', auth='$p = new Permissions($note); if (!$p->canView()) throw new Exception();', leftover='patch'),
    dict(slug='silverstripe-skip-delete', plant='skegbblock', ticket='SKE-3', surface='Silverstripe delete missing canDelete', family='php_mw', skip='public function delete($id) { Note::get()->byID($id)->delete(); }', auth='public function view($id) { $n = Note::get()->byID($id); return $n->canView() ? $n : $this->httpError(403); }', leftover='update'),
    dict(slug='worktop-skip-delete', plant='slabbblock', ticket='SLA-4', surface='worktop DELETE missing reply.locals.user', family='js_route', skip='export const DELETE: Handler = async (req) => notes.del(req.params.id)', auth='export const GET: Handler = async (req, context) => notes.get(req.params.id, context.user)', leftover='put'),
    dict(slug='sunder-skip-delete', plant='snatbblock', ticket='SNA-5', surface='Sunder DELETE missing withUser', family='js_route', skip="app.delete('/notes/:id', (c) => notes.del(c.params.id))", auth="app.get('/notes/:id', withUser, (c) => notes.get(c.params.id, c.user))", leftover='patch'),
    dict(slug='pages-fn-skip-delete', plant='snorbblock', ticket='SNO-6', surface='Cloudflare Pages Function DELETE missing getSession', family='js_route', skip='export async function onRequestDelete({ params }) { return notes.del(params.id) }', auth='export async function onRequestGet({ params, request }) { const u = await getSession(request); return notes.get(params.id, u) }', leftover='update'),
    dict(slug='vercel-edge-skip-delete', plant='spanbblock', ticket='SPA-7', surface='Vercel Edge DELETE missing getToken', family='js_route', skip='export async function DELETE(req, { params }) { return notes.del(params.id) }', auth='export async function GET(req, { params }) { const t = await getToken({ req }); return notes.get(params.id, t) }', leftover='put'),
    dict(slug='netlify-fn-skip-delete', plant='spenbblock', ticket='SPE-8', surface='Netlify Function DELETE missing context.clientContext', family='js_route', skip="exports.handler = async (event) => { if (event.httpMethod==='DELETE') notes.del(event.queryStringParameters.id) }", auth='exports.handler = async (event, context) => { const u = context.clientContext.user; return notes.get(id, u) }', leftover='patch'),
    dict(slug='lambda-url-skip-delete', plant='sprehblock', ticket='SPR-9', surface='Lambda Function URL DELETE missing authorizer', family='js_route', skip="if (event.requestContext.http.method==='DELETE') notes.del(id)", auth='const u = event.requestContext.authorizer; return notes.get(id, u)', leftover='update'),
    dict(slug='apigw-authorizer-skip-delete', plant='spribblock', ticket='SPR-1', surface='API Gateway DELETE missing authorizer', family='js_route', skip='DELETE /notes/{id}  Authorization: NONE', auth='GET /notes/{id}  Authorization: AWS_IAM', leftover='put'),
    dict(slug='amplify-fn-skip-delete', plant='stanbblock', ticket='STA-2', surface='Amplify Function DELETE missing identity', family='js_route', skip='exports.handler = async (event) => notes.del(event.arguments.id)', auth='exports.handler = async (event) => notes.get(event.arguments.id, event.identity.sub)', leftover='patch'),
    dict(slug='async-rest-skip-delete', plant='steebblock', ticket='STE-3', surface='async-rest delete missing middleware auth', family='rb_filter', skip='def delete(id) = notes.del(id)', auth='def get(id) = (auth!; notes.get(id, current_user))', leftover='update'),
    dict(slug='protocol-http-skip-delete', plant='stopbblock', ticket='STO-4', surface='protocol-http DELETE missing middleware', family='rb_filter', skip="r.delete('/notes/:id') { |r| notes.del(r.path) }", auth="r.get('/notes/:id') { |r| auth!(r); notes.get(r.path, r.user) }", leftover='put'),
    dict(slug='utopia-skip-delete', plant='strabblock', ticket='STR-5', surface='Utopia delete missing current_user', family='rb_filter', skip="on('DELETE') { notes.del(id) }", auth="on('GET') { current_user!; notes.get(id, current_user) }", leftover='patch'),
    dict(slug='falcon-socketry-skip-delete', plant='studbblock', ticket='STU-6', surface='Falcon/Socketry delete missing authenticate', family='rb_filter', skip="def handle(request, id) = notes.del(id) if request.method == 'DELETE'", auth='def handle(request, id) = (request.authenticate!; notes.get(id, request.user))', leftover='update'),
    dict(slug='django-allauth-skip-delete', plant='tabebblock', ticket='TAB-7', surface='django-allauth delete missing login_required', family='py_async', skip='def delete_note(request, nid):\n    Note.objects.get(pk=nid).delete()', auth='@login_required\ndef note_detail(request, nid):\n    return Note.objects.get(pk=nid, owner=request.user)', leftover='put'),
    dict(slug='starlette-session-skip-delete', plant='tackbblock', ticket='TAC-8', surface='Starlette SessionMiddleware DELETE missing session user', family='py_async', skip="@app.route('/notes/{nid}', methods=['DELETE'])\nasync def delete(request):\n    await notes.del(request.path_params['nid'])", auth="@app.route('/notes/{nid}')\nasync def get(request):\n    u = request.session['user']; return await notes.get(request.path_params['nid'], u)", leftover='patch'),
    dict(slug='tengine-skip-delete', plant='taffbblock', ticket='TAF-9', surface='Tengine DELETE missing auth_request', family='js_route', skip='location /notes/ { limit_except GET { deny all; }  # DELETE still proxied }', auth='location /notes/ { auth_request /_auth; proxy_pass http://notes; }', leftover='update'),
    dict(slug='angie-skip-delete', plant='thimbblock', ticket='THI-1', surface='Angie DELETE missing auth_request', family='js_route', skip='location /notes/ { proxy_pass http://notes; }  # DELETE open', auth='location /notes/ { auth_request /_auth; proxy_pass http://notes; }', leftover='put'),
    dict(slug='unit-nginx-skip-delete', plant='throbblock', ticket='THR-2', surface='NGINX Unit DELETE missing pass auth', family='js_route', skip='"match": {"uri": "/notes/*", "method": "DELETE"}, "action": {"pass": "applications/notes"}', auth='"match": {"uri": "/notes/*", "method": "GET"}, "action": {"pass": "routes/auth"}', leftover='patch'),
    dict(slug='docker-authz-skip-delete', plant='thwabblock', ticket='THW-3', surface='Docker authz plugin skip DELETE', family='js_route', skip='AuthZReq method=DELETE /notes  allow=true', auth='AuthZReq method=GET /notes  plugin=authz-broker', leftover='update'),
    dict(slug='containerd-cri-skip-delete', plant='tillbblock', ticket='TIL-4', surface='containerd CRI delete missing auth interceptor', family='js_route', skip='RemoveContainer(id)  # no auth', auth='ListContainers(filter)  # tls client auth', leftover='put'),
    dict(slug='crio-skip-delete', plant='toggbblock', ticket='TOG-5', surface='CRI-O delete missing auth', family='js_route', skip='rpc RemovePodSandbox(id)  # open', auth='rpc ListPodSandbox()  # runtime auth', leftover='patch'),
    dict(slug='kubelet-auth-skip-delete', plant='toppbblock', ticket='TOP-6', surface='kubelet DELETE missing anonymous-auth=false', family='js_route', skip='DELETE /pods/{name}  anonymous-auth=true', auth='GET /pods/{name}  authentication-token-webhook=true', leftover='update'),
    dict(slug='etcd-auth-skip-delete', plant='tranbblock', ticket='TRA-7', surface='etcd delete missing auth-token', family='js_route', skip='etcdctl del /notes/id  # auth disabled', auth='etcdctl --user root get /notes/id', leftover='put'),
    dict(slug='mysql-grant-skip-delete', plant='treebblock', ticket='TRE-8', surface='MySQL GRANT DELETE leftover', family='sql', skip="GRANT DELETE ON notes.* TO 'anon'@'%';", auth="GRANT SELECT ON notes.* TO 'app'@'%' REQUIRE SSL;", leftover='patch'),
    dict(slug='mongodb-role-skip-delete', plant='trucbblock', ticket='TRU-9', surface='MongoDB role skip remove', family='js_route', skip="db.grantRolesToUser('anon', [{role:'readWrite', db:'notes'}])  # remove open", auth="db.createRole({role:'notesReader', privileges:[{resource:{db:'notes',collection:'n'}, actions:['find']}]})", leftover='update'),
    dict(slug='redis-acl-skip-delete', plant='trysbblock', ticket='TRY-1', surface='Redis ACL skip DEL', family='js_route', skip='ACL SETUSER anon +del ~notes:*', auth='ACL SETUSER app +get ~notes:* on >pass', leftover='put'),
    dict(slug='opensearch-skip-delete', plant='tumbbblock', ticket='TUM-2', surface='OpenSearch DELETE missing security plugin', family='js_route', skip='DELETE /notes/_doc/{id}  # anonymous', auth='GET /notes/_doc/{id}  plugins.security.authcz', leftover='patch'),
    dict(slug='solr-skip-delete', plant='turnbblock', ticket='TUR-3', surface='Solr update delete missing BasicAuthPlugin', family='js_route', skip='POST /solr/notes/update?stream.body=<delete><id>1</id></delete>', auth='GET /solr/notes/select  authentication: {class: BasicAuthPlugin}', leftover='update'),
    dict(slug='neo4j-rbac-skip-delete', plant='uphrbblock', ticket='UPH-4', surface='Neo4j delete missing GRANT TRAVERSE', family='js_route', skip='MATCH (n:Note {id:$id}) DETACH DELETE n  # no auth', auth='GRANT TRAVERSE ON GRAPH * NODES Note TO notesReader', leftover='put'),
    dict(slug='cassandra-role-skip-delete', plant='vangbblock', ticket='VAN-5', surface='Cassandra DELETE missing GRANT', family='sql', skip='DELETE FROM notes.n WHERE id = ?;  -- anon', auth='GRANT SELECT ON notes.n TO app;', leftover='patch'),
    dict(slug='cockroach-grant-skip-delete', plant='walebblock', ticket='WAL-6', surface='CockroachDB GRANT DELETE leftover', family='sql', skip='GRANT DELETE ON notes TO anon;', auth='GRANT SELECT ON notes TO app;', leftover='update'),
    dict(slug='pages-workers-skip-delete', plant='warpbblock', ticket='WAR-7', surface='Cloudflare Worker Pages DELETE missing verify', family='js_route', skip="if (request.method==='DELETE') return notes.del(id)", auth="if (request.method==='GET') { const u = await env.AUTH.verify(request); return notes.get(id, u) }", leftover='put'),
    dict(slug='fastly-compute-skip-delete', plant='weatbblock', ticket='WEA-8', surface='Fastly Compute DELETE missing secret store auth', family='js_route', skip="if (req.method=='DELETE') return notes.del(id)", auth="if (req.method=='GET') { const t = secret.get('token'); return notes.get(id, t) }", leftover='patch'),
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
