"""Extra unique IDOR/BFLA plants for authz-regression-factory r1760+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r1759 vesselNNNN-sys.
Not clones of r1759 ztf-oid-idor / redpanda-admin-skip-delete.
Not clones of r1364 geohash, r1445 casbin, r1543 gstin-isd, r1560 e212, r1640 imeitac, r1720 fps-uk.
"""
from __future__ import annotations


EXTRA_IDOR_ROWS = [
    dict(slug='aemo-nem-idor', plant='reefbkeel', ticket='REE-1', surface='AEMO NEM region object-id IDOR', mod='aemonems', model='Aemonem', lookup='aemonem', sample='NSW1', owner='grid_id', first='authn', residual='pdf', product='aemo-nem', bug='REE-1 region unique from AEMO'),
    dict(slug='ons-br-idor', plant='ribbckeel', ticket='RIB-2', surface='ONS Brazil subsystem object-id IDOR', mod='onsbrs', model='Onsbr', lookup='onsbr', sample='SE/CO', owner='grid_id', first='mask', residual='export', product='ons-br', bug='RIB-2 subsystem unique from ONS'),
    dict(slug='cen-cl-idor', plant='samsckeel', ticket='SAM-3', surface='CEN Chile system object-id IDOR', mod='cencls', model='Cencl', lookup='cencl', sample='SEN-N', owner='grid_id', first='any_member', residual='search', product='cen-cl', bug='SAM-3 system unique from CEN'),
    dict(slug='cenace-mx-idor', plant='scutckeel', ticket='SCU-4', surface='CENACE control area object-id IDOR', mod='cenaces', model='Cenace', lookup='cenace', sample='SIN', owner='grid_id', first='list_scope', residual='mget', product='cenace-mx', bug='SCU-4 area unique from CENACE'),
    dict(slug='ngeso-gb-idor', plant='seacckeel', ticket='SEA-5', surface='NGESO GSP object-id IDOR', mod='ngesos', model='Ngeso', lookup='ngeso', sample='GSP-001', owner='grid_id', first='authn', residual='csv', product='ngeso-gb', bug='SEA-5 GSP unique from NGESO'),
    dict(slug='rte-fr-idor', plant='seizckeel', ticket='SEI-6', surface='RTE poste object-id IDOR', mod='rtefrs', model='Rtefr', lookup='rtefr', sample='RTE-PDL-1', owner='grid_id', first='mask', residual='admin', product='rte-fr', bug='SEI-6 poste unique from RTE'),
    dict(slug='tennet-nl-idor', plant='sennckeel', ticket='SEN-7', surface='TenneT station object-id IDOR', mod='tennetnls', model='Tennetnl', lookup='tennetnl', sample='TTN-L-001', owner='grid_id', first='any_member', residual='webhook', product='tennet-nl', bug='SEN-7 station unique from TenneT'),
    dict(slug='fiftyhertz-idor', plant='shacckeel', ticket='SHA-8', surface='50Hertz TSO object-id IDOR', mod='fiftyhzs', model='Fiftyhz', lookup='fiftyhz', sample='50HZ-TSO', owner='grid_id', first='list_scope', residual='comments', product='fiftyhertz-id', bug='SHA-8 TSO unique from 50Hertz'),
    dict(slug='amprion-idor', plant='sheeckeel', ticket='SHE-9', surface='Amprion TSO object-id IDOR', mod='amprions', model='Amprion', lookup='amprion', sample='AMP-TSO', owner='grid_id', first='authn', residual='pdf', product='amprion-id', bug='SHE-9 TSO unique from Amprion'),
    dict(slug='transnetbw-idor', plant='shrockeel', ticket='SHR-1', surface='TransnetBW TSO object-id IDOR', mod='tnbws', model='Tnbw', lookup='tnbw', sample='TNBW-TSO', owner='grid_id', first='mask', residual='export', product='transnetbw-id', bug='SHR-1 TSO unique from TransnetBW'),
    dict(slug='ree-es-idor', plant='skegckeel', ticket='SKE-2', surface='REE TSO object-id IDOR', mod='reeess', model='Reees', lookup='reees', sample='REE-TSO', owner='grid_id', first='any_member', residual='search', product='ree-es', bug='SKE-2 TSO unique from REE'),
    dict(slug='terna-it-idor', plant='slabckeel', ticket='SLA-3', surface='Terna TSO object-id IDOR', mod='ternas', model='Terna', lookup='terna', sample='TERNA-TSO', owner='grid_id', first='list_scope', residual='mget', product='terna-it', bug='SLA-3 TSO unique from Terna'),
    dict(slug='ren-pt-idor', plant='snatckeel', ticket='SNA-4', surface='REN TSO object-id IDOR', mod='renpts', model='Renpt', lookup='renpt', sample='REN-TSO', owner='grid_id', first='authn', residual='csv', product='ren-pt', bug='SNA-4 TSO unique from REN'),
    dict(slug='elia-be-idor', plant='snorckeel', ticket='SNO-5', surface='Elia TSO object-id IDOR', mod='eliabes', model='Eliabe', lookup='eliabe', sample='ELIA-TSO', owner='grid_id', first='mask', residual='admin', product='elia-be', bug='SNO-5 TSO unique from Elia'),
    dict(slug='statnett-idor', plant='spanckeel', ticket='SPA-6', surface='Statnett TSO object-id IDOR', mod='statnetts', model='Statnett', lookup='statnett', sample='SN-TSO', owner='grid_id', first='any_member', residual='webhook', product='statnett-id', bug='SPA-6 TSO unique from Statnett'),
    dict(slug='svk-se-idor', plant='spenckeel', ticket='SPE-7', surface='Svenska kraftnat TSO object-id IDOR', mod='svkses', model='Svkse', lookup='svkse', sample='SVK-TSO', owner='grid_id', first='list_scope', residual='comments', product='svk-se', bug='SPE-7 TSO unique from SvK'),
    dict(slug='fingrid-idor', plant='spreckeel', ticket='SPR-8', surface='Fingrid TSO object-id IDOR', mod='fingrids', model='Fingrid', lookup='fingrid', sample='FG-TSO', owner='grid_id', first='authn', residual='pdf', product='fingrid-id', bug='SPR-8 TSO unique from Fingrid'),
    dict(slug='energinet-idor', plant='sprickeel', ticket='SPR-9', surface='Energinet TSO object-id IDOR', mod='energinets', model='Energinet', lookup='energinet', sample='EN-TSO', owner='grid_id', first='mask', residual='export', product='energinet-id', bug='SPR-9 TSO unique from Energinet'),
    dict(slug='miso-hub-idor', plant='stanckeel', ticket='STA-1', surface='MISO hub object-id IDOR', mod='misohubs', model='Misohub', lookup='misohub', sample='MINN.HUB', owner='grid_id', first='any_member', residual='search', product='miso-hub', bug='STA-1 hub unique from MISO'),
    dict(slug='pjm-hub-idor', plant='steeckeel', ticket='STE-2', surface='PJM hub object-id IDOR', mod='pjmhubs', model='Pjmhub', lookup='pjmhub', sample='WESTERN-HUB', owner='grid_id', first='list_scope', residual='mget', product='pjm-hub', bug='STE-2 hub unique from PJM'),
    dict(slug='bizum-idor', plant='stopckeel', ticket='STO-3', surface='Bizum payment object-id IDOR', mod='bizums', model='Bizum', lookup='bizum', sample='BIZUM-240115-1', owner='bank_id', first='authn', residual='csv', product='bizum-es', bug='STO-3 id unique from Iberpay'),
    dict(slug='mbway-idor', plant='strackeel', ticket='STR-4', surface='MB WAY payment object-id IDOR', mod='mbways', model='Mbway', lookup='mbway', sample='MBWAY-PT-001', owner='bank_id', first='mask', residual='admin', product='mbway-pt', bug='STR-4 id unique from SIBS'),
    dict(slug='swish-idor', plant='studckeel', ticket='STU-5', surface='Swish payment object-id IDOR', mod='swishs', model='Swish', lookup='swish', sample='SWISH-SE-001', owner='bank_id', first='any_member', residual='webhook', product='swish-se', bug='STU-5 id unique from Bankgirot'),
    dict(slug='vipps-idor', plant='tabeckeel', ticket='TAB-6', surface='Vipps payment object-id IDOR', mod='vippss', model='Vipps', lookup='vipps', sample='VIPPS-NO-001', owner='bank_id', first='list_scope', residual='comments', product='vipps-no', bug='TAB-6 id unique from Vipps'),
    dict(slug='mobilepay-idor', plant='tackckeel', ticket='TAC-7', surface='MobilePay payment object-id IDOR', mod='mpayds', model='Mpayd', lookup='mpayd', sample='MP-DK-001', owner='bank_id', first='authn', residual='pdf', product='mobilepay-dk', bug='TAC-7 id unique from MobilePay'),
    dict(slug='blik-idor', plant='taffckeel', ticket='TAF-8', surface='BLIK payment object-id IDOR', mod='bliks', model='Blik', lookup='blik', sample='BLIK-240115-1', owner='bank_id', first='mask', residual='export', product='blik-pl', bug='TAF-8 id unique from BLIK'),
    dict(slug='payconiq-idor', plant='thimckeel', ticket='THI-9', surface='Payconiq payment object-id IDOR', mod='payconiqs', model='Payconiq', lookup='payconiq', sample='PQ-BE-001', owner='bank_id', first='any_member', residual='search', product='payconiq-be', bug='THI-9 id unique from Payconiq'),
    dict(slug='twint-idor', plant='throckeel', ticket='THR-1', surface='TWINT payment object-id IDOR', mod='twints', model='Twint', lookup='twint', sample='TWINT-CH-001', owner='bank_id', first='list_scope', residual='mget', product='twint-ch', bug='THR-1 id unique from TWINT'),
    dict(slug='interac-idor', plant='thwackeel', ticket='THW-2', surface='Interac e-Transfer object-id IDOR', mod='interacs', model='Interac', lookup='interac', sample='INT-CA-001', owner='bank_id', first='authn', residual='csv', product='interac-ca', bug='THW-2 id unique from Interac'),
    dict(slug='instapay-ph-idor', plant='tillckeel', ticket='TIL-3', surface='InstaPay object-id IDOR', mod='instapays', model='Instapay', lookup='instapay', sample='IPAY-PH-001', owner='bank_id', first='mask', residual='admin', product='instapay-ph', bug='TIL-3 id unique from Pesonet'),
    dict(slug='paylah-idor', plant='toggckeel', ticket='TOG-4', surface='PayLah object-id IDOR', mod='paylahs', model='Paylah', lookup='paylah', sample='PAYLAH-SG-001', owner='bank_id', first='any_member', residual='webhook', product='paylah-sg', bug='TOG-4 id unique from DBS'),
    dict(slug='grabpay-idor', plant='toppckeel', ticket='TOP-5', surface='GrabPay object-id IDOR', mod='grabpays', model='Grabpay', lookup='grabpay', sample='GRAB-001', owner='bank_id', first='list_scope', residual='comments', product='grabpay-id', bug='TOP-5 id unique from Grab'),
    dict(slug='alipay-uid-idor', plant='tranckeel', ticket='TRA-6', surface='Alipay user object-id IDOR', mod='alipayuids', model='Alipayuid', lookup='alipayuid', sample='2088123456789012', owner='bank_id', first='authn', residual='pdf', product='alipay-uid', bug='TRA-6 uid unique from Alipay'),
    dict(slug='wechatpay-idor', plant='treeckeel', ticket='TRE-7', surface='WeChat Pay object-id IDOR', mod='wechatpays', model='Wechatpay', lookup='wechatpay', sample='wxp-001', owner='bank_id', first='mask', residual='export', product='wechatpay-id', bug='TRE-7 id unique from Tenpay'),
    dict(slug='unionpay-idor', plant='trucckeel', ticket='TRU-8', surface='UnionPay QRC object-id IDOR', mod='unionpays', model='Unionpay', lookup='unionpay', sample='UP-QRC-001', owner='bank_id', first='any_member', residual='search', product='unionpay-qrc', bug='TRU-8 QRC unique from UnionPay'),
    dict(slug='pix-dict-idor', plant='trysckeel', ticket='TRY-9', surface='PIX DICT key object-id IDOR', mod='pixdicts', model='Pixdict', lookup='pixdict', sample='DICT-KEY-001', owner='bank_id', first='list_scope', residual='mget', product='pix-dict', bug='TRY-9 DICT unique from BCB'),
    dict(slug='npp-payto-idor', plant='tumbckeel', ticket='TUM-1', surface='NPP PayTo agreement object-id IDOR', mod='npptos', model='Nppto', lookup='nppto', sample='PAYTO-AU-001', owner='bank_id', first='authn', residual='csv', product='npp-payto', bug='TUM-1 agreement unique from NPPA'),
    dict(slug='sctinst-idor', plant='turnckeel', ticket='TUR-2', surface='SEPA Instant SCT object-id IDOR', mod='sctinsts', model='Sctinst', lookup='sctinst', sample='SCTINST-240115-1', owner='bank_id', first='mask', residual='admin', product='sct-inst', bug='TUR-2 txid unique from EPC'),
    dict(slug='t2s-idor', plant='uphrckeel', ticket='UPH-3', surface='T2S settlement object-id IDOR', mod='t2ss', model='T2s', lookup='t2s', sample='T2S-240115-1', owner='book_id', first='any_member', residual='webhook', product='t2s-ecb', bug='UPH-3 id unique from T2S'),
    dict(slug='cls-idor', plant='vangckeel', ticket='VAN-4', surface='CLS settlement object-id IDOR', mod='clss', model='Cls', lookup='clsid', sample='CLS-240115-1', owner='book_id', first='list_scope', residual='comments', product='cls-id', bug='VAN-4 id unique from CLS'),
    dict(slug='gsc2-idor', plant='waleckeel', ticket='WAL-5', surface='GSC-II star object-id IDOR', mod='gsc2s', model='Gsc2', lookup='gsc2', sample='GSC2.3 N012345678', owner='lab_id', first='authn', residual='pdf', product='gsc2-id', bug='WAL-5 GSC2 unique from STScI'),
    dict(slug='usnob-idor', plant='warpckeel', ticket='WAR-6', surface='USNO-B1.0 object-id IDOR', mod='usnobs', model='Usnob', lookup='usnob', sample='1234-0567891', owner='lab_id', first='mask', residual='export', product='usnob-id', bug='WAR-6 USNO-B unique from USNO'),
    dict(slug='nomadcat-idor', plant='weatckeel', ticket='WEA-7', surface='NOMAD catalog object-id IDOR', mod='nomadcats', model='Nomadcat', lookup='nomadcat', sample='1234-0567891', owner='lab_id', first='any_member', residual='search', product='nomad-cat', bug='WEA-7 NOMAD unique from USNO'),
    dict(slug='ucac3-idor', plant='whipckeel', ticket='WHI-8', surface='UCAC3 star object-id IDOR', mod='ucac3s', model='Ucac3', lookup='ucac3', sample='UCAC3 123-012345', owner='lab_id', first='list_scope', residual='mget', product='ucac3-id', bug='WHI-8 UCAC3 unique from USNO'),
    dict(slug='tess-ctoi-idor', plant='whisckeel', ticket='WHI-9', surface='TESS CTOI object-id IDOR', mod='tessctois', model='Tessctoi', lookup='tessctoi', sample='CTOI 123.01', owner='lab_id', first='authn', residual='csv', product='tess-ctoi', bug='WHI-9 CTOI unique from TESS'),
    dict(slug='des-dr-idor', plant='wincckeel', ticket='WIN-1', surface='DES DR object-id IDOR', mod='desdrs', model='Desdr', lookup='desdr', sample='DES J0535-0523', owner='lab_id', first='mask', residual='admin', product='des-dr', bug='WIN-1 COADD unique from DES'),
    dict(slug='lsst-obj-idor', plant='windckeel', ticket='WIN-2', surface='LSST object-id IDOR', mod='lsstobjs', model='Lsstobj', lookup='lsstobj', sample='1258334841758928910', owner='lab_id', first='any_member', residual='webhook', product='lsst-obj', bug='WIN-2 diaObject unique from Rubin'),
    dict(slug='hsc-obj-idor', plant='woolckeel', ticket='WOO-3', surface='HSC object-id IDOR', mod='hscobjs', model='Hscobj', lookup='hscobj', sample='HSC-1234567890123', owner='lab_id', first='list_scope', residual='comments', product='hsc-obj', bug='WOO-3 object_id unique from HSC'),
    dict(slug='decals-idor', plant='xebecbkeel', ticket='XEB-4', surface='DECaLS object-id IDOR', mod='decalss', model='Decals', lookup='decals', sample='LS-DR9 J053514.9-052353', owner='lab_id', first='authn', residual='pdf', product='decals-id', bug='XEB-4 ls_id unique from Legacy Survey'),
    dict(slug='gaia-dr1-idor', plant='yardckeel', ticket='YAR-5', surface='Gaia DR1 source object-id IDOR', mod='gaiadr1s', model='Gaiadr1', lookup='gaiadr1', sample='Gaia DR1 1234567890123456789', owner='lab_id', first='mask', residual='export', product='gaia-dr1', bug='YAR-5 source_id unique from Gaia DR1'),
    dict(slug='hip2-idor', plant='yokeckeel', ticket='YOK-6', surface='Hipparcos-2 object-id IDOR', mod='hip2s', model='Hip2', lookup='hip2', sample='HIP2 71683', owner='lab_id', first='any_member', residual='search', product='hip2-id', bug='YOK-6 HIP2 unique from new reduction'),
    dict(slug='pcilte-idor', plant='yulockeel', ticket='YUL-7', surface='LTE PCI object-id IDOR', mod='pciltes', model='Pcilte', lookup='pcilte', sample='210', owner='net_id', first='list_scope', residual='mget', product='pci-lte', bug='YUL-7 PCI unique from E-UTRAN'),
    dict(slug='fiveg-guti-idor', plant='zabrckeel', ticket='ZAB-8', surface='5G-GUTI object-id IDOR', mod='fiveggutis', model='Fivegguti', lookup='fivegguti', sample='310410-01-02-A1B2C3D4', owner='net_id', first='authn', residual='csv', product='5g-guti', bug='ZAB-8 5G-GUTI unique from 3GPP'),
    dict(slug='amfregion-idor', plant='zuluckeel', ticket='ZUL-9', surface='AMF Region object-id IDOR', mod='amfregions', model='Amfregion', lookup='amfregion', sample='310-410-01', owner='net_id', first='mask', residual='admin', product='amf-region', bug='ZUL-9 AMF Region unique from 3GPP'),
    dict(slug='amfptr-idor', plant='aftckeel', ticket='AFT-1', surface='AMF Pointer object-id IDOR', mod='amfptrs', model='Amfptr', lookup='amfptr', sample='2A', owner='net_id', first='any_member', residual='webhook', product='amf-ptr', bug='AFT-1 AMF Pointer unique from 3GPP'),
    dict(slug='tai-nr-idor', plant='bagckeel', ticket='BAG-2', surface='NR TAI object-id IDOR', mod='tainrs', model='Tainr', lookup='tainr', sample='310-410-ABC1', owner='net_id', first='list_scope', residual='comments', product='tai-nr', bug='BAG-2 NR TAI unique from 5GS'),
    dict(slug='nssai-full-idor', plant='balkckeel', ticket='BAL-3', surface='full NSSAI object-id IDOR', mod='nssaifulls', model='Nssaifull', lookup='nssaifull', sample='1-000001+2-000002', owner='net_id', first='authn', residual='pdf', product='nssai-full', bug='BAL-3 NSSAI unique from 3GPP'),
    dict(slug='dnnni-idor', plant='battckeel', ticket='BAT-4', surface='DNN NI object-id IDOR', mod='dnnnis', model='Dnnni', lookup='dnnni', sample='ims', owner='net_id', first='mask', residual='export', product='dnn-ni', bug='BAT-4 NI unique from 3GPP DNN'),
    dict(slug='lvts-idor', plant='beamckeel', ticket='BEA-5', surface='LVTS payment object-id IDOR', mod='lvtss', model='Lvts', lookup='lvts', sample='LVTS-240115-1', owner='bank_id', first='any_member', residual='search', product='lvts-ca', bug='BEA-5 id unique from LVTS'),
    dict(slug='lynx-ca-idor', plant='bighckeel', ticket='BIG-6', surface='Lynx RTGS object-id IDOR', mod='lynxcas', model='Lynxca', lookup='lynxca', sample='LYNX-240115-1', owner='bank_id', first='list_scope', residual='mget', product='lynx-ca', bug='BIG-6 id unique from Lynx'),
    dict(slug='hvcs-hk-idor', plant='bilgckeel', ticket='BIL-7', surface='HK HVCS object-id IDOR', mod='hvcshks', model='Hvcshk', lookup='hvcshk', sample='HVCS-240115-1', owner='bank_id', first='authn', residual='csv', product='hvcs-hk', bug='BIL-7 id unique from HKICL'),
    dict(slug='meps-sg-idor', plant='bittckeel', ticket='BIT-8', surface='MEPS+ object-id IDOR', mod='mepssgs', model='Mepssg', lookup='mepssg', sample='MEPS-240115-1', owner='bank_id', first='mask', residual='admin', product='meps-sg', bug='BIT-8 id unique from MAS'),
    dict(slug='rits-jp-idor', plant='boomckeel', ticket='BOO-9', surface='BOJ RTGS object-id IDOR', mod='ritsjps', model='Ritsjp', lookup='ritsjp', sample='RITS-240115-1', owner='bank_id', first='any_member', residual='webhook', product='rits-jp', bug='BOO-9 id unique from BOJ'),
    dict(slug='cips-cn-idor', plant='bowckeel', ticket='BOW-1', surface='CIPS payment object-id IDOR', mod='cipscns', model='Cipscn', lookup='cipscn', sample='CIPS-240115-1', owner='bank_id', first='list_scope', residual='comments', product='cips-cn', bug='BOW-1 id unique from CIPS'),
    dict(slug='rfc-ba-idor', plant='breckeel', ticket='BRE-2', surface='RFC BA object-id IDOR', mod='rfcbas', model='Rfcba', lookup='rfcba', sample='PJM', owner='grid_id', first='authn', residual='pdf', product='rfc-ba', bug='BRE-2 BA unique from RFC'),
    dict(slug='mro-ba-idor', plant='bulkckeel', ticket='BUL-3', surface='MRO BA object-id IDOR', mod='mrobas', model='Mroba', lookup='mroba', sample='MISO', owner='grid_id', first='mask', residual='export', product='mro-ba', bug='BUL-3 BA unique from MRO'),
    dict(slug='npcc-ba-idor', plant='buntckeel', ticket='BUN-4', surface='NPCC BA object-id IDOR', mod='npccbas', model='Npccba', lookup='npccba', sample='NYIS', owner='grid_id', first='any_member', residual='search', product='npcc-ba', bug='BUN-4 BA unique from NPCC'),
    dict(slug='frcc-ba-idor', plant='cablckeel', ticket='CAB-5', surface='FRCC BA object-id IDOR', mod='frccbas', model='Frccba', lookup='frccba', sample='FPL', owner='grid_id', first='list_scope', residual='mget', product='frcc-ba', bug='CAB-5 BA unique from FRCC'),
    dict(slug='tre-ba-idor', plant='cambckeel', ticket='CAM-6', surface='TRE BA object-id IDOR', mod='trebas', model='Treba', lookup='treba', sample='ERCO', owner='grid_id', first='authn', residual='csv', product='tre-ba', bug='CAM-6 BA unique from TRE'),
    dict(slug='ercot-lz-idor', plant='cantckeel', ticket='CAN-7', surface='ERCOT load zone object-id IDOR', mod='ercotlzs', model='Ercotlz', lookup='ercotlz', sample='LZ_HOUSTON', owner='grid_id', first='mask', residual='admin', product='ercot-lz', bug='CAN-7 LZ unique from ERCOT'),
    dict(slug='caiso-hub-idor', plant='captckeel', ticket='CAP-8', surface='CAISO hub object-id IDOR', mod='caisohubs', model='Caisohub', lookup='caisohub', sample='TH_NP15_GEN-APND', owner='grid_id', first='any_member', residual='webhook', product='caiso-hub', bug='CAP-8 hub unique from CAISO'),
    dict(slug='nyiso-hub-idor', plant='carlckeel', ticket='CAR-9', surface='NYISO hub object-id IDOR', mod='nyisohubs', model='Nyisohub', lookup='nyisohub', sample='N.Y.C.', owner='grid_id', first='list_scope', residual='comments', product='nyiso-hub', bug='CAR-9 hub unique from NYISO'),
    dict(slug='isone-hub-idor', plant='catckeel', ticket='CAT-1', surface='ISO-NE hub object-id IDOR', mod='isonehubs', model='Isonehub', lookup='isonehub', sample='.H.INTERNAL_HUB', owner='grid_id', first='authn', residual='pdf', product='isone-hub', bug='CAT-1 hub unique from ISO-NE'),
    dict(slug='spp-zone-idor', plant='chanckeel', ticket='CHA-2', surface='SPP zone object-id IDOR', mod='sppzones', model='Sppzone', lookup='sppzone', sample='CSWS', owner='grid_id', first='mask', residual='export', product='spp-zone', bug='CHA-2 zone unique from SPP'),
    dict(slug='wecc-ba-idor', plant='cheeckeel', ticket='CHE-3', surface='WECC BA object-id IDOR', mod='weccbas', model='Weccba', lookup='weccba', sample='CISO', owner='grid_id', first='any_member', residual='search', product='wecc-ba', bug='CHE-3 BA unique from WECC'),
    dict(slug='neowise-idor', plant='chockeel', ticket='CHO-4', surface='NEOWISE object-id IDOR', mod='neowises', model='Neowise', lookup='neowise', sample='NEOWISE J053514.94-052353.9', owner='lab_id', first='list_scope', residual='mget', product='neowise-id', bug='CHO-4 source unique from NEOWISE'),
    dict(slug='iras-psc-idor', plant='clewckeel', ticket='CLE-5', surface='IRAS PSC object-id IDOR', mod='iraspscs', model='Iraspsc', lookup='iraspsc', sample='IRAS 05351-0523', owner='lab_id', first='authn', residual='csv', product='iras-psc', bug='CLE-5 PSC unique from IRAS'),
    dict(slug='akari-fis-idor', plant='clinckeel', ticket='CLI-6', surface='AKARI FIS object-id IDOR', mod='akarifiss', model='Akarifis', lookup='akarifis', sample='AKARI-FIS-J0535149-052353', owner='lab_id', first='mask', residual='admin', product='akari-fis', bug='CLI-6 FIS unique from JAXA'),
    dict(slug='galex-mis-idor', plant='coamckeel', ticket='COA-7', surface='GALEX MIS object-id IDOR', mod='galexmiss', model='Galexmis', lookup='galexmis', sample='GALEX MIS J053514.9-052353', owner='lab_id', first='any_member', residual='webhook', product='galex-mis', bug='COA-7 MIS unique from MAST'),
    dict(slug='xmm-src-idor', plant='cockckeel', ticket='COC-8', surface='XMM source object-id IDOR', mod='xmmsrcs', model='Xmmsrc', lookup='xmmsrc', sample='4XMM J053514.9-052353', owner='lab_id', first='list_scope', residual='comments', product='xmm-src', bug='COC-8 4XMM unique from XMM'),
]


BFLA_ROWS = [
    dict(slug='kuma-skip-delete', plant='reefbkeel', ticket='REE-1', surface='Kuma Mesh delete missing dp auth', family='js_route', skip='kumactl delete dataplane notes-dp  # no token', auth="kumactl get dataplane notes-dp --header 'authorization: Bearer'", leftover='put'),
    dict(slug='appmesh-skip-delete', plant='ribbckeel', ticket='RIB-2', surface='AWS App Mesh delete missing IAM', family='js_route', skip='aws appmesh delete-virtual-node --mesh-name notes --virtual-node-name n  # no iam', auth='aws appmesh describe-virtual-node --mesh-name notes --virtual-node-name n', leftover='patch'),
    dict(slug='calico-gnp-skip-delete', plant='samsckeel', ticket='SAM-3', surface='Calico GNP delete missing auth', family='js_route', skip='calicoctl delete gnp notes-deny-delete', auth='calicoctl get gnp notes-deny-delete --allow-version-mismatch', leftover='update'),
    dict(slug='antrea-skip-delete', plant='scutckeel', ticket='SCU-4', surface='Antrea ClusterNetworkPolicy skip DELETE', family='js_route', skip='kubectl delete acnp notes-drop  # no rbac', auth='kubectl get acnp notes-drop --as=system:serviceaccount:notes:viewer', leftover='put'),
    dict(slug='kubeovn-skip-delete', plant='seacckeel', ticket='SEA-5', surface='Kube-OVN subnet delete missing auth', family='js_route', skip='kubectl delete subnet notes-sub', auth='kubectl get subnet notes-sub -n kube-system', leftover='patch'),
    dict(slug='multus-skip-delete', plant='seizckeel', ticket='SEI-6', surface='Multus NAD delete missing rbac', family='js_route', skip='kubectl delete net-attach-def notes-nad', auth='kubectl get net-attach-def notes-nad', leftover='update'),
    dict(slug='podman-skip-delete', plant='sennckeel', ticket='SEN-7', surface='Podman rm missing --authfile', family='js_route', skip='podman rm -f notes', auth='podman inspect notes --authfile=$XDG_RUNTIME_DIR/containers/auth.json', leftover='put'),
    dict(slug='buildah-skip-delete', plant='shacckeel', ticket='SHA-8', surface='Buildah rmi missing auth', family='js_route', skip='buildah rmi notes:latest', auth='buildah from --authfile auth.json notes:latest', leftover='patch'),
    dict(slug='nerdctl-skip-delete', plant='sheeckeel', ticket='SHE-9', surface='nerdctl rm missing --hosts-dir auth', family='js_route', skip='nerdctl rm -f notes', auth='nerdctl inspect notes --hosts-dir /etc/containerd/certs.d', leftover='update'),
    dict(slug='crictl-skip-delete', plant='shrockeel', ticket='SHR-1', surface='crictl rmp missing --runtime-endpoint auth', family='js_route', skip='crictl rmp --force notes', auth='crictl inspectp notes --runtime-endpoint unix:///run/containerd/containerd.sock', leftover='put'),
    dict(slug='helm-skip-delete', plant='skegckeel', ticket='SKE-2', surface='Helm uninstall missing --kube-as-user', family='js_route', skip='helm uninstall notes', auth='helm status notes --kube-as-user notes-viewer', leftover='patch'),
    dict(slug='kustomize-skip-delete', plant='slabckeel', ticket='SLA-3', surface='Kustomize delete missing prune auth', family='js_route', skip='kustomize build . | kubectl delete -f -', auth='kustomize build . | kubectl apply --server-side --as=notes-viewer -f -', leftover='update'),
    dict(slug='argocd-skip-delete', plant='snatckeel', ticket='SNA-4', surface='Argo CD app delete missing rbac', family='js_route', skip='argocd app delete notes --yes', auth='argocd app get notes --grpc-web --auth-token $ARGOCD_TOKEN', leftover='put'),
    dict(slug='flux-skip-delete', plant='snorckeel', ticket='SNO-5', surface='Flux kustomization delete missing impersonation', family='js_route', skip='flux delete kustomization notes --silent', auth='flux get kustomization notes --as notes-viewer', leftover='patch'),
    dict(slug='tekton-skip-delete', plant='spanckeel', ticket='SPA-6', surface='Tekton PipelineRun delete missing SA', family='js_route', skip='tkn pipelinerun delete notes --force', auth='tkn pipelinerun describe notes', leftover='update'),
    dict(slug='jenkins-skip-delete', plant='spenckeel', ticket='SPE-7', surface='Jenkins job delete missing crumb', family='js_route', skip='curl -X POST $JENKINS/job/notes/doDelete', auth='curl -u user:token $JENKINS/job/notes/api/json', leftover='put'),
    dict(slug='drone-skip-delete', plant='spreckeel', ticket='SPR-8', surface='Drone build delete missing token', family='js_route', skip='drone build stop org/notes 1', auth='drone build info org/notes 1 --token $DRONE_TOKEN', leftover='patch'),
    dict(slug='concourse-skip-delete', plant='sprickeel', ticket='SPR-9', surface='Concourse destroy-pipeline missing auth', family='js_route', skip='fly -t ci destroy-pipeline -p notes -n', auth='fly -t ci get-pipeline -p notes', leftover='update'),
    dict(slug='spinnaker-skip-delete', plant='stanckeel', ticket='STA-1', surface='Spinnaker application delete missing Fiat', family='js_route', skip='spin application delete notes', auth='spin application get notes --gate-endpoint $GATE', leftover='put'),
    dict(slug='rancher-skip-delete', plant='steeckeel', ticket='STE-2', surface='Rancher project delete missing token', family='js_route', skip='rancher projects delete p-notes', auth='rancher projects ls --token $RANCHER_TOKEN', leftover='patch'),
    dict(slug='openshift-scc-skip-delete', plant='stopckeel', ticket='STO-3', surface='OpenShift SCC delete missing cluster-admin', family='js_route', skip='oc delete scc notes-restricted', auth='oc get scc notes-restricted --as=system:serviceaccount:notes:viewer', leftover='update'),
    dict(slug='tanzu-skip-delete', plant='strackeel', ticket='STR-4', surface='Tanzu package delete missing context', family='js_route', skip='tanzu package installed delete notes -y', auth='tanzu package installed get notes --kubeconfig $KUBECONFIG', leftover='put'),
    dict(slug='eks-auth-skip-delete', plant='studckeel', ticket='STU-5', surface='EKS aws-auth delete missing mapping', family='js_route', skip='kubectl delete cm aws-auth -n kube-system', auth='kubectl get cm aws-auth -n kube-system --as=notes-viewer', leftover='patch'),
    dict(slug='gke-skip-delete', plant='tabeckeel', ticket='TAB-6', surface='GKE cluster delete missing iam.clusters.delete', family='js_route', skip='gcloud container clusters delete notes --quiet', auth='gcloud container clusters describe notes', leftover='update'),
    dict(slug='aks-skip-delete', plant='tackckeel', ticket='TAC-7', surface='AKS delete missing Azure RBAC', family='js_route', skip='az aks delete -g rg -n notes --yes', auth='az aks show -g rg -n notes', leftover='put'),
    dict(slug='k3s-skip-delete', plant='taffckeel', ticket='TAF-8', surface='k3s kubectl delete missing k3s.yaml', family='js_route', skip='k3s kubectl delete ns notes', auth='k3s kubectl get ns notes --kubeconfig /etc/rancher/k3s/k3s.yaml', leftover='patch'),
    dict(slug='k0s-skip-delete', plant='thimckeel', ticket='THI-9', surface='k0s kubectl delete missing admin.conf', family='js_route', skip='k0s kubectl delete ns notes', auth='k0s kubectl get ns notes --kubeconfig /var/lib/k0s/pki/admin.conf', leftover='update'),
    dict(slug='microk8s-skip-delete', plant='throckeel', ticket='THR-1', surface='microk8s delete missing enable rbac', family='js_route', skip='microk8s kubectl delete ns notes', auth='microk8s kubectl get ns notes', leftover='put'),
    dict(slug='kind-skip-delete', plant='thwackeel', ticket='THW-2', surface='kind delete cluster missing kubeconfig', family='js_route', skip='kind delete cluster --name notes', auth='kind get kubeconfig --name notes', leftover='patch'),
    dict(slug='minikube-skip-delete', plant='tillckeel', ticket='TIL-3', surface='minikube delete missing profile auth', family='js_route', skip='minikube delete -p notes', auth='minikube profile list', leftover='update'),
    dict(slug='kops-skip-delete', plant='toggckeel', ticket='TOG-4', surface='kops delete cluster missing state store', family='js_route', skip='kops delete cluster notes.k8s.local --yes', auth='kops get cluster notes.k8s.local --state $KOPS_STATE_STORE', leftover='put'),
    dict(slug='kubeadm-skip-delete', plant='toppckeel', ticket='TOP-5', surface='kubeadm reset missing --cert-dir auth', family='js_route', skip='kubeadm reset -f', auth='kubeadm certs check-expiration', leftover='patch'),
    dict(slug='clusterapi-skip-delete', plant='tranckeel', ticket='TRA-6', surface='Cluster API delete missing identity', family='js_route', skip='clusterctl delete --all', auth='clusterctl describe cluster notes --kubeconfig $KUBECONFIG', leftover='update'),
    dict(slug='crossplane-skip-delete', plant='treeckeel', ticket='TRE-7', surface='Crossplane XRD delete missing rbac', family='js_route', skip='kubectl delete xrd notes.example.org', auth='kubectl get xrd notes.example.org', leftover='put'),
    dict(slug='terraform-skip-delete', plant='trucckeel', ticket='TRU-8', surface='Terraform destroy missing backend creds', family='js_route', skip='terraform destroy -auto-approve', auth="terraform state show 'module.notes'", leftover='patch'),
    dict(slug='pulumi-skip-delete', plant='trysckeel', ticket='TRY-9', surface='Pulumi destroy missing stack passphrase', family='js_route', skip='pulumi destroy -y', auth='pulumi stack --show-urns', leftover='update'),
    dict(slug='ansible-skip-delete', plant='tumbckeel', ticket='TUM-1', surface='Ansible uri DELETE missing become', family='js_route', skip="ansible all -m uri -a 'url=/notes method=DELETE'", auth="ansible all -m uri -a 'url=/notes method=GET' --become-user notes", leftover='put'),
    dict(slug='salt-skip-delete', plant='turnckeel', ticket='TUR-2', surface='Salt file.remove missing eauth', family='js_route', skip="salt '*' file.remove /var/notes", auth="salt --auth pam '*' file.file_exists /var/notes", leftover='patch'),
    dict(slug='puppet-skip-delete', plant='uphrckeel', ticket='UPH-3', surface='Puppet resource ensure absent missing cert', family='js_route', skip='puppet resource file /var/notes ensure=absent', auth='puppet resource file /var/notes --certname notes', leftover='update'),
    dict(slug='chef-skip-delete', plant='vangckeel', ticket='VAN-4', surface='Chef knife node delete missing key', family='js_route', skip='knife node delete notes -y', auth='knife node show notes -c knife.rb', leftover='put'),
    dict(slug='vault-agent-skip-delete', plant='waleckeel', ticket='WAL-5', surface='Vault agent sink delete missing token', family='js_route', skip='vault kv delete secret/notes', auth='vault kv get secret/notes', leftover='patch'),
    dict(slug='consul-connect-skip-delete', plant='warpckeel', ticket='WAR-6', surface='Consul Connect intention delete missing ACL', family='js_route', skip='consul intention delete notes-src notes-dst', auth='consul intention list -token $CONSUL_HTTP_TOKEN', leftover='update'),
    dict(slug='osm-mesh-skip-delete', plant='weatckeel', ticket='WEA-7', surface='OSM mesh delete missing mesh-config', family='js_route', skip='osm mesh delete --mesh-name notes', auth='osm mesh list --mesh-name notes', leftover='put'),
    dict(slug='nsm-skip-delete', plant='whipckeel', ticket='WHI-8', surface='Network Service Mesh delete missing SPIFFE', family='js_route', skip='kubectl delete networkservice notes', auth='kubectl get networkservice notes', leftover='patch'),
    dict(slug='flannel-skip-delete', plant='whisckeel', ticket='WHI-9', surface='Flannel CNI delete missing etcd auth', family='js_route', skip='etcdctl del /coreos.com/network/subnets/notes', auth='etcdctl get /coreos.com/network/config --user root', leftover='update'),
    dict(slug='weave-skip-delete', plant='wincckeel', ticket='WIN-1', surface='Weave Net forget missing password', family='js_route', skip='weave forget 10.32.0.1', auth='weave status --password $WEAVE_PASSWORD', leftover='put'),
    dict(slug='gitlab-ci-skip-delete', plant='windckeel', ticket='WIN-2', surface='GitLab job erase missing job token', family='js_route', skip='curl -X POST $CI_API/jobs/$id/erase', auth='curl --header JOB-TOKEN:$CI_JOB_TOKEN $CI_API/jobs/$id', leftover='patch'),
    dict(slug='circleci-skip-delete', plant='woolckeel', ticket='WOO-3', surface='CircleCI delete env missing token', family='js_route', skip='curl -X DELETE https://circleci.com/api/v2/project/gh/o/n/envvar/NOTES', auth="curl -H 'Circle-Token: $TOK' https://circleci.com/api/v2/project/gh/o/n", leftover='update'),
    dict(slug='buildkite-skip-delete', plant='xebecbkeel', ticket='XEB-4', surface='Buildkite job cancel missing token', family='js_route', skip='curl -X PUT $BK/jobs/$id/cancel', auth='curl -H "Authorization: Bearer $BK_TOKEN" $BK/jobs/$id', leftover='put'),
    dict(slug='harvester-skip-delete', plant='yardckeel', ticket='YAR-5', surface='Harvester VM delete missing kubeconfig', family='js_route', skip='kubectl delete virtualmachine notes -n default', auth='kubectl get virtualmachine notes -n default', leftover='patch'),
    dict(slug='longhorn-skip-delete', plant='yokeckeel', ticket='YOK-6', surface='Longhorn volume delete missing UI token', family='js_route', skip='curl -X DELETE $LH/v1/volumes/notes', auth='curl $LH/v1/volumes/notes', leftover='update'),
    dict(slug='rook-ceph-skip-delete', plant='yulockeel', ticket='YUL-7', surface='Rook CephBlockPool delete missing rbac', family='js_route', skip='kubectl delete cephblockpool notes -n rook-ceph', auth='kubectl get cephblockpool notes -n rook-ceph', leftover='put'),
    dict(slug='openebs-skip-delete', plant='zabrckeel', ticket='ZAB-8', surface='OpenEBS PVC delete missing storageclass', family='js_route', skip='kubectl delete pvc notes-data', auth='kubectl get pvc notes-data', leftover='patch'),
    dict(slug='portworx-skip-delete', plant='zuluckeel', ticket='ZUL-9', surface='Portworx volume delete missing pxctl auth', family='js_route', skip='pxctl volume delete notes', auth='pxctl volume inspect notes --auth-token $PX_TOKEN', leftover='update'),
    dict(slug='velero-skip-delete', plant='aftckeel', ticket='AFT-1', surface='Velero backup delete missing SA', family='js_route', skip='velero backup delete notes --confirm', auth='velero backup describe notes', leftover='put'),
    dict(slug='kasten-skip-delete', plant='bagckeel', ticket='BAG-2', surface='Kasten restorepoint delete missing token', family='js_route', skip='curl -X DELETE $K10/v1/restorepoints/notes', auth='curl -H "Authorization: Bearer $K10" $K10/v1/restorepoints/notes', leftover='patch'),
    dict(slug='restic-skip-delete', plant='balkckeel', ticket='BAL-3', surface='restic forget missing password file', family='js_route', skip='restic forget --prune latest', auth='restic snapshots --password-file $RESTIC_PASSWORD_FILE', leftover='update'),
    dict(slug='borg-skip-delete', plant='battckeel', ticket='BAT-4', surface='borg delete missing passphrase', family='js_route', skip='borg delete ::notes', auth='borg list --encryption-passphrase $BORG_PASSPHRASE', leftover='put'),
    dict(slug='duplicity-skip-delete', plant='beamckeel', ticket='BEA-5', surface='duplicity remove-all-but-n missing gpg', family='js_route', skip='duplicity remove-all-but-n-full 0 --force file:///notes', auth='duplicity collection-status file:///notes --encrypt-key $GPG', leftover='patch'),
    dict(slug='rclone-skip-delete', plant='bighckeel', ticket='BIG-6', surface='rclone delete missing crypt', family='js_route', skip='rclone delete remote:notes', auth='rclone ls remote:notes --crypt-password $RCLONE_CRYPT', leftover='update'),
    dict(slug='minio-skip-delete', plant='bilgckeel', ticket='BIL-7', surface='MinIO mc rm missing alias auth', family='js_route', skip='mc rm myminio/notes/obj', auth='mc stat myminio/notes/obj', leftover='put'),
    dict(slug='ceph-rgw-skip-delete', plant='bittckeel', ticket='BIT-8', surface='Ceph RGW delete missing s3 auth', family='js_route', skip='radosgw-admin bucket rm --bucket=notes --purge-objects', auth='radosgw-admin bucket stats --bucket=notes --uid=notes', leftover='patch'),
    dict(slug='swift-openstack-skip-delete', plant='boomckeel', ticket='BOO-9', surface='OpenStack Swift delete missing x-auth', family='js_route', skip='swift delete notes', auth='swift stat notes -A $OS_AUTH_URL -U $OS_USERNAME', leftover='update'),
    dict(slug='garage-s3-skip-delete', plant='bowckeel', ticket='BOW-1', surface='Garage S3 delete missing key', family='js_route', skip='garage bucket delete notes', auth='garage bucket info notes', leftover='put'),
    dict(slug='seaweedfs-skip-delete', plant='breckeel', ticket='BRE-2', surface='SeaweedFS delete missing jwt', family='js_route', skip='weed filer.delete /notes/obj', auth='weed filer.cat /notes/obj', leftover='patch'),
    dict(slug='lakefs-skip-delete', plant='bulkckeel', ticket='BUL-3', surface='lakeFS branch delete missing access key', family='js_route', skip='lakectl branch delete notes/main -y', auth='lakectl branch list lakefs://notes', leftover='update'),
    dict(slug='delta-share-skip-delete', plant='buntckeel', ticket='BUN-4', surface='Delta Sharing share delete missing token', family='js_route', skip='databricks shares delete notes', auth='databricks shares get notes', leftover='put'),
    dict(slug='iceberg-skip-delete', plant='cablckeel', ticket='CAB-5', surface='Iceberg drop table missing catalog auth', family='js_route', skip='DROP TABLE notes.t PURGE', auth='SHOW TABLES IN notes  -- catalog auth', leftover='patch'),
    dict(slug='hudi-skip-delete', plant='cambckeel', ticket='CAM-6', surface='Hudi drop table missing hoodie.meta', family='js_route', skip="spark.sql('drop table notes')", auth="spark.sql('show tables in notes')", leftover='update'),
    dict(slug='nifi-skip-delete', plant='cantckeel', ticket='CAN-7', surface='NiFi process group delete missing proxied-entity', family='js_route', skip='curl -X DELETE $NIFI/process-groups/notes', auth="curl -H 'X-ProxiedEntitiesChain: notes' $NIFI/process-groups/notes", leftover='put'),
    dict(slug='airflow-skip-delete', plant='captckeel', ticket='CAP-8', surface='Airflow DAG delete missing auth', family='js_route', skip='airflow dags delete notes -y', auth='airflow dags list-runs -d notes', leftover='patch'),
    dict(slug='dagster-skip-delete', plant='carlckeel', ticket='CAR-9', surface='Dagster job wipe missing token', family='js_route', skip='dagster job wipe --job notes', auth='dagster job list --token $DAGSTER_TOKEN', leftover='update'),
    dict(slug='prefect-skip-delete', plant='catckeel', ticket='CAT-1', surface='Prefect deployment delete missing api-key', family='js_route', skip='prefect deployment delete notes/d', auth='prefect deployment inspect notes/d', leftover='put'),
    dict(slug='luigi-skip-delete', plant='chanckeel', ticket='CHA-2', surface='Luigi worker delete missing scheduler auth', family='js_route', skip='curl -X POST $LUIGI/api/remove --data task=notes', auth='curl $LUIGI/api/task_list', leftover='patch'),
    dict(slug='kedro-skip-delete', plant='cheeckeel', ticket='CHE-3', surface='Kedro catalog delete missing credentials', family='js_route', skip='kedro catalog delete notes', auth='kedro catalog list --env local', leftover='update'),
    dict(slug='dbt-skip-delete', plant='chockeel', ticket='CHO-4', surface='dbt drop schema missing profile', family='js_route', skip="dbt run-operation drop_schema --args '{schema: notes}'", auth='dbt debug --profiles-dir $HOME/.dbt', leftover='put'),
    dict(slug='spark-skip-delete', plant='clewckeel', ticket='CLE-5', surface='Spark drop table missing hive.metastore.sasl', family='js_route', skip="spark.sql('DROP TABLE notes')", auth="spark.sql('DESCRIBE TABLE notes')", leftover='patch'),
    dict(slug='cfengine-skip-delete', plant='clinckeel', ticket='CLI-6', surface='CFEngine files promise delete missing key', family='js_route', skip='files: /var/notes delete => true;', auth="files: /var/notes perms => mog('600','notes','notes');", leftover='update'),
    dict(slug='okd-skip-delete', plant='coamckeel', ticket='COA-7', surface='OKD project delete missing cluster-admin', family='js_route', skip='oc delete project notes', auth='oc get project notes --as=system:serviceaccount:notes:viewer', leftover='put'),
    dict(slug='gha-oidc-skip-delete', plant='cockckeel', ticket='COC-8', surface='GitHub Actions OIDC delete missing permissions', family='js_route', skip="permissions: {}\njobs:\n  del:\n    runs-on: ubuntu-latest\n    steps: [{run: 'gh api -X DELETE /repos/o/n'}]", auth='permissions: { contents: read }\njobs:\n  get:\n    permissions: { id-token: write }', leftover='patch'),
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
