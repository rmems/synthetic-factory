"""Extra unique IDOR/BFLA plants for authz-regression-factory r2080+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r2079 vesselNNNN-sys.
Not clones of r2079 wrs-pid / cilium-policy, r2000 inchikey-std / woodpecker.
"""
from __future__ import annotations


EXTRA_IDOR_ROWS = [
    dict(slug='hs6-code-idor', plant='azt00hull', ticket='AZ1-1', surface='HS-6 code object-id IDOR', mod='hs6codexxxs80', model='Hs6codexxxM', lookup='hs6codexxxl80', sample='010121', owner='trade_id', first='authn', residual='pdf', product='hs6-code', bug='AZ1-1 HS6 unique from WCO'),
    dict(slug='cn8-code-idor', plant='azt01hull', ticket='AZ2-2', surface='CN8 code object-id IDOR', mod='cn8codexxxs80', model='Cn8codexxxM', lookup='cn8codexxxl80', sample='01012100', owner='trade_id', first='mask', residual='export', product='cn8-code', bug='AZ2-2 CN8 unique from TARIC'),
    dict(slug='hts10-idor', plant='azt02hull', ticket='AZ3-3', surface='HTS-10 object-id IDOR', mod='hts10xxxxxs80', model='Hts10xxxxxM', lookup='hts10xxxxxl80', sample='0101210010', owner='trade_id', first='any_member', residual='search', product='hts10', bug='AZ3-3 HTS unique from USITC'),
    dict(slug='ncm-br-idor', plant='azt03hull', ticket='AZ4-4', surface='NCM object-id IDOR', mod='ncmbrxxxxxs80', model='NcmbrxxxxxM', lookup='ncmbrxxxxxl80', sample='0101.21.00', owner='trade_id', first='list_scope', residual='mget', product='ncm-br', bug='AZ4-4 NCM unique from RFB'),
    dict(slug='sac-mx-idor', plant='azt04hull', ticket='AZ5-5', surface='SAC MX object-id IDOR', mod='sacmxxxxxxs80', model='SacmxxxxxxM', lookup='sacmxxxxxxl80', sample='01012101', owner='trade_id', first='authn', residual='csv', product='sac-mx', bug='AZ5-5 SAC unique from SAT'),
    dict(slug='tara-nz-idor', plant='azt05hull', ticket='AZ6-6', surface='TARA NZ object-id IDOR', mod='taranzxxxxs80', model='TaranzxxxxM', lookup='taranzxxxxl80', sample='0101.21.00', owner='trade_id', first='mask', residual='admin', product='tara-nz', bug='AZ6-6 TARA unique from NZCS'),
    dict(slug='ahecc-idor', plant='azt06hull', ticket='AZ7-7', surface='AHECC object-id IDOR', mod='aheccxxxxxs80', model='AheccxxxxxM', lookup='aheccxxxxxl80', sample='010121', owner='trade_id', first='any_member', residual='webhook', product='ahecc', bug='AZ7-7 AHECC unique from ABS'),
    dict(slug='sitc4-idor', plant='azt07hull', ticket='AZ8-8', surface='SITC-4 object-id IDOR', mod='sitc4xxxxxs80', model='Sitc4xxxxxM', lookup='sitc4xxxxxl80', sample='0011', owner='trade_id', first='list_scope', residual='comments', product='sitc4', bug='AZ8-8 SITC unique from UNSD'),
    dict(slug='cpc2-idor', plant='azt08hull', ticket='AZ9-9', surface='CPC2 object-id IDOR', mod='cpc2xxxxxxs80', model='Cpc2xxxxxxM', lookup='cpc2xxxxxxl80', sample='02111', owner='trade_id', first='authn', residual='pdf', product='cpc2', bug='AZ9-9 CPC unique from UNSD'),
    dict(slug='isic4-idor', plant='azt09hull', ticket='AZ1-10', surface='ISIC4 object-id IDOR', mod='isic4xxxxxs80', model='Isic4xxxxxM', lookup='isic4xxxxxl80', sample='0111', owner='trade_id', first='mask', residual='export', product='isic4', bug='AZ1-10 ISIC unique from UNSD'),
    dict(slug='naics6-idor', plant='azt10hull', ticket='AZ2-11', surface='NAICS-6 object-id IDOR', mod='naics6xxxxs80', model='Naics6xxxxM', lookup='naics6xxxxl80', sample='111110', owner='trade_id', first='any_member', residual='search', product='naics6', bug='AZ2-11 NAICS unique from Census'),
    dict(slug='nace-rev2-idor', plant='azt11hull', ticket='AZ3-12', surface='NACE Rev2 object-id IDOR', mod='nacerev2xxs80', model='Nacerev2xxM', lookup='nacerev2xxl80', sample='01.11', owner='trade_id', first='list_scope', residual='mget', product='nace-rev2', bug='AZ3-12 NACE unique from Eurostat'),
    dict(slug='anzsic-idor', plant='azt12hull', ticket='AZ4-13', surface='ANZSIC object-id IDOR', mod='anzsicxxxxs80', model='AnzsicxxxxM', lookup='anzsicxxxxl80', sample='0141', owner='trade_id', first='authn', residual='csv', product='anzsic', bug='AZ4-13 ANZSIC unique from ABS'),
    dict(slug='jsic-idor', plant='azt13hull', ticket='AZ5-14', surface='JSIC object-id IDOR', mod='jsicxxxxxxs80', model='JsicxxxxxxM', lookup='jsicxxxxxxl80', sample='0111', owner='trade_id', first='mask', residual='admin', product='jsic', bug='AZ5-14 JSIC unique from MIC'),
    dict(slug='ksic-idor', plant='azt14hull', ticket='AZ6-15', surface='KSIC object-id IDOR', mod='ksicxxxxxxs80', model='KsicxxxxxxM', lookup='ksicxxxxxxl80', sample='01110', owner='trade_id', first='any_member', residual='webhook', product='ksic', bug='AZ6-15 KSIC unique from KOSTAT'),
    dict(slug='gics-sub-idor', plant='azt15hull', ticket='AZ7-16', surface='GICS sub object-id IDOR', mod='gicssubxxxs80', model='GicssubxxxM', lookup='gicssubxxxl80', sample='25101010', owner='trade_id', first='list_scope', residual='comments', product='gics-sub', bug='AZ7-16 GICS unique from MSCI'),
    dict(slug='trbc-idor', plant='azt16hull', ticket='AZ8-17', surface='TRBC object-id IDOR', mod='trbcxxxxxxs80', model='TrbcxxxxxxM', lookup='trbcxxxxxxl80', sample='50101010', owner='trade_id', first='authn', residual='pdf', product='trbc', bug='AZ8-17 TRBC unique from LSEG'),
    dict(slug='icb-idor', plant='azt17hull', ticket='AZ9-18', surface='ICB object-id IDOR', mod='icbxxxxxxxs80', model='IcbxxxxxxxM', lookup='icbxxxxxxxl80', sample='10101010', owner='trade_id', first='mask', residual='export', product='icb', bug='AZ9-18 ICB unique from FTSE'),
    dict(slug='unspsc-idor', plant='azt18hull', ticket='AZ1-19', surface='UNSPSC object-id IDOR', mod='unspscxxxxs80', model='UnspscxxxxM', lookup='unspscxxxxl80', sample='10101501', owner='trade_id', first='any_member', residual='search', product='unspsc', bug='AZ1-19 UNSPSC unique from GS1'),
    dict(slug='eclass-idor', plant='azt19hull', ticket='AZ2-20', surface='eCl@ss object-id IDOR', mod='eclassxxxxs80', model='EclassxxxxM', lookup='eclassxxxxl80', sample='19010201', owner='trade_id', first='list_scope', residual='mget', product='eclass', bug='AZ2-20 class unique from eCl@ss'),
    dict(slug='itf14-pack-idor', plant='azt20hull', ticket='AZ3-21', surface='ITF-14 object-id IDOR', mod='itf14packxs80', model='Itf14packxM', lookup='itf14packxl80', sample='00012345678905', owner='trade_id', first='authn', residual='csv', product='itf14-pack', bug='AZ3-21 ITF unique from GS1'),
    dict(slug='pzn-de-idor', plant='azt21hull', ticket='AZ4-22', surface='PZN object-id IDOR', mod='pzndexxxxxs80', model='PzndexxxxxM', lookup='pzndexxxxxl80', sample='01234567', owner='lab_id', first='mask', residual='admin', product='pzn-de', bug='AZ4-22 PZN unique from IFA'),
    dict(slug='cip13-idor', plant='azt22hull', ticket='AZ5-23', surface='CIP13 object-id IDOR', mod='cip13xxxxxs80', model='Cip13xxxxxM', lookup='cip13xxxxxl80', sample='3400930000000', owner='lab_id', first='any_member', residual='webhook', product='cip13', bug='AZ5-23 CIP unique from Club Inter Pharmaceutique'),
    dict(slug='ndc-pkg-idor', plant='azt23hull', ticket='AZ6-24', surface='NDC package object-id IDOR', mod='ndcpkgxxxxs80', model='NdcpkgxxxxM', lookup='ndcpkgxxxxl80', sample='00071-0155-23', owner='lab_id', first='list_scope', residual='comments', product='ndc-pkg', bug='AZ6-24 NDC unique from FDA'),
    dict(slug='din-de-idor', plant='azt24hull', ticket='AZ7-25', surface='DIN object-id IDOR', mod='dindexxxxxs80', model='DindexxxxxM', lookup='dindexxxxxl80', sample='DIN-00001', owner='lab_id', first='authn', residual='pdf', product='din-de', bug='AZ7-25 DIN unique from DIN'),
    dict(slug='hs4-code-idor', plant='azt25hull', ticket='AZ8-26', surface='HS-4 code object-id IDOR', mod='hs4codexxxs80', model='Hs4codexxxM', lookup='hs4codexxxl80', sample='0101', owner='trade_id', first='mask', residual='export', product='hs4-code', bug='AZ8-26 HS4 unique from WCO'),
    dict(slug='hs2-code-idor', plant='azt26hull', ticket='AZ9-27', surface='HS-2 chapter object-id IDOR', mod='hs2codexxxs80', model='Hs2codexxxM', lookup='hs2codexxxl80', sample='01', owner='trade_id', first='any_member', residual='search', product='hs2-code', bug='AZ9-27 HS2 unique from WCO'),
    dict(slug='taric-idor', plant='azt27hull', ticket='AZ1-28', surface='TARIC object-id IDOR', mod='taricxxxxxs80', model='TaricxxxxxM', lookup='taricxxxxxl80', sample='0101210010', owner='trade_id', first='list_scope', residual='mget', product='taric', bug='AZ1-28 TARIC unique from TAXUD'),
    dict(slug='cn10-idor', plant='azt28hull', ticket='AZ2-29', surface='CN10 object-id IDOR', mod='cn10xxxxxxs80', model='Cn10xxxxxxM', lookup='cn10xxxxxxl80', sample='0101210010', owner='trade_id', first='authn', residual='csv', product='cn10', bug='AZ2-29 CN10 unique from TAXUD'),
    dict(slug='schedule-b-idor', plant='azt29hull', ticket='AZ3-30', surface='Schedule B object-id IDOR', mod='schedulebxs80', model='SchedulebxM', lookup='schedulebxl80', sample='0101210000', owner='trade_id', first='mask', residual='admin', product='schedule-b', bug='AZ3-30 Schedule B unique from Census'),
    dict(slug='eccn-idor', plant='azt30hull', ticket='AZ4-31', surface='ECCN object-id IDOR', mod='eccnxxxxxxs80', model='EccnxxxxxxM', lookup='eccnxxxxxxl80', sample='5A002', owner='trade_id', first='any_member', residual='webhook', product='eccn', bug='AZ4-31 ECCN unique from BIS'),
    dict(slug='itar-usml-idor', plant='azt31hull', ticket='AZ5-32', surface='USML category object-id IDOR', mod='itarusmlxxs80', model='ItarusmlxxM', lookup='itarusmlxxl80', sample='USML-IV', owner='trade_id', first='list_scope', residual='comments', product='itar-usml', bug='AZ5-32 USML unique from DDTC'),
    dict(slug='ear99-idor', plant='azt32hull', ticket='AZ6-33', surface='EAR99 object-id IDOR', mod='ear99xxxxxs80', model='Ear99xxxxxM', lookup='ear99xxxxxl80', sample='EAR99', owner='trade_id', first='authn', residual='pdf', product='ear99', bug='AZ6-33 EAR99 unique from BIS'),
    dict(slug='un-na-idor', plant='azt33hull', ticket='AZ7-34', surface='UN/NA number object-id IDOR', mod='unnaxxxxxxs80', model='UnnaxxxxxxM', lookup='unnaxxxxxxl80', sample='UN1203', owner='trade_id', first='mask', residual='export', product='un-na', bug='AZ7-34 UN number unique from UNECE'),
    dict(slug='adr-un-idor', plant='azt34hull', ticket='AZ8-35', surface='ADR UN object-id IDOR', mod='adrunxxxxxs80', model='AdrunxxxxxM', lookup='adrunxxxxxl80', sample='UN1203', owner='trade_id', first='any_member', residual='search', product='adr-un', bug='AZ8-35 UN unique from ADR'),
    dict(slug='imdg-un-idor', plant='azt35hull', ticket='AZ9-36', surface='IMDG UN object-id IDOR', mod='imdgunxxxxs80', model='ImdgunxxxxM', lookup='imdgunxxxxl80', sample='UN1203', owner='trade_id', first='list_scope', residual='mget', product='imdg-un', bug='AZ9-36 UN unique from IMO'),
    dict(slug='iata-dgr-idor', plant='azt36hull', ticket='AZ1-37', surface='IATA DGR object-id IDOR', mod='iatadgrxxxs80', model='IatadgrxxxM', lookup='iatadgrxxxl80', sample='UN1203', owner='trade_id', first='authn', residual='csv', product='iata-dgr', bug='AZ1-37 UN unique from IATA'),
    dict(slug='adn-un-idor', plant='azt37hull', ticket='AZ2-38', surface='ADN UN object-id IDOR', mod='adnunxxxxxs80', model='AdnunxxxxxM', lookup='adnunxxxxxl80', sample='UN1203', owner='trade_id', first='mask', residual='admin', product='adn-un', bug='AZ2-38 UN unique from ADN'),
    dict(slug='echa-ec-idor', plant='azt38hull', ticket='AZ3-39', surface='ECHA EC number object-id IDOR', mod='echaecxxxxs80', model='EchaecxxxxM', lookup='echaecxxxxl80', sample='200-001-8', owner='lab_id', first='any_member', residual='webhook', product='echa-ec', bug='AZ3-39 EC unique from ECHA'),
    dict(slug='einecs-idor', plant='azt39hull', ticket='AZ4-40', surface='EINECS object-id IDOR', mod='einecsxxxxs80', model='EinecsxxxxM', lookup='einecsxxxxl80', sample='200-662-2', owner='lab_id', first='list_scope', residual='comments', product='einecs', bug='AZ4-40 EINECS unique from ECHA'),
    dict(slug='h3r8-idor', plant='azt40hull', ticket='AZ5-41', surface='H3 r8 object-id IDOR', mod='h3r8xxxxxxs80', model='H3r8xxxxxxM', lookup='h3r8xxxxxxl80', sample='88283082bffffff', owner='geo_id', first='authn', residual='pdf', product='h3-r8', bug='AZ5-41 cell unique from Uber H3'),
    dict(slug='s2cell-idor', plant='azt41hull', ticket='AZ6-42', surface='S2 cell object-id IDOR', mod='s2cellxxxxs80', model='S2cellxxxxM', lookup='s2cellxxxxl80', sample='89c259c5b5b5b5b5', owner='geo_id', first='mask', residual='export', product='s2-cell', bug='AZ6-42 cell unique from S2'),
    dict(slug='pluscode-idor', plant='azt42hull', ticket='AZ7-43', surface='Plus Code object-id IDOR', mod='pluscodexxs80', model='PluscodexxM', lookup='pluscodexxl80', sample='8FVC9G8F+6X', owner='geo_id', first='any_member', residual='search', product='pluscode', bug='AZ7-43 code unique from OLC'),
    dict(slug='mgrs-idor', plant='azt43hull', ticket='AZ8-44', surface='MGRS object-id IDOR', mod='mgrsxxxxxxs80', model='MgrsxxxxxxM', lookup='mgrsxxxxxxl80', sample='18TWL850210', owner='geo_id', first='list_scope', residual='mget', product='mgrs', bug='AZ8-44 MGRS unique from NGA'),
    dict(slug='usng-idor', plant='azt44hull', ticket='AZ9-45', surface='USNG object-id IDOR', mod='usngxxxxxxs80', model='UsngxxxxxxM', lookup='usngxxxxxxl80', sample='18T WL 85021 10230', owner='geo_id', first='authn', residual='csv', product='usng', bug='AZ9-45 USNG unique from FGDC'),
    dict(slug='maidenhead-idor', plant='azt45hull', ticket='AZ1-46', surface='Maidenhead object-id IDOR', mod='maidenheads80', model='MaidenheadM', lookup='maidenheadl80', sample='FN20xr', owner='geo_id', first='mask', residual='admin', product='maidenhead', bug='AZ1-46 grid unique from IARU'),
    dict(slug='olc11-idor', plant='azt46hull', ticket='AZ2-47', surface='OLC-11 object-id IDOR', mod='olc11xxxxxs80', model='Olc11xxxxxM', lookup='olc11xxxxxl80', sample='8FVC9G8F+6XQ', owner='geo_id', first='any_member', residual='webhook', product='olc11', bug='AZ2-47 OLC unique from Google'),
    dict(slug='w3w-idor', plant='azt47hull', ticket='AZ3-48', surface='what3words object-id IDOR', mod='w3wxxxxxxxs80', model='W3wxxxxxxxM', lookup='w3wxxxxxxxl80', sample='filled.count.soap', owner='geo_id', first='list_scope', residual='comments', product='w3w', bug='AZ3-48 words unique from w3w'),
    dict(slug='geohash36-idor', plant='azt48hull', ticket='AZ4-49', surface='Geohash-36 object-id IDOR', mod='geohash36xs80', model='Geohash36xM', lookup='geohash36xl80', sample='bdrdC26BqH', owner='geo_id', first='authn', residual='pdf', product='geohash36', bug='AZ4-49 hash unique from Geohash-36'),
    dict(slug='mapcode-idor', plant='azt49hull', ticket='AZ5-50', surface='Mapcode object-id IDOR', mod='mapcodexxxs80', model='MapcodexxxM', lookup='mapcodexxxl80', sample='US 0H.Y6', owner='geo_id', first='mask', residual='export', product='mapcode', bug='AZ5-50 mapcode unique from Mapcode'),
    dict(slug='unlocode-idor', plant='azt50hull', ticket='AZ6-51', surface='UN/LOCODE object-id IDOR', mod='unlocodexxs80', model='UnlocodexxM', lookup='unlocodexxl80', sample='USNYC', owner='geo_id', first='any_member', residual='search', product='unlocode', bug='AZ6-51 LOCODE unique from UNECE'),
    dict(slug='iata-3let-idor', plant='azt51hull', ticket='AZ7-52', surface='IATA 3-letter object-id IDOR', mod='iata3letxxs80', model='Iata3letxxM', lookup='iata3letxxl80', sample='JFK', owner='geo_id', first='list_scope', residual='mget', product='iata-3let', bug='AZ7-52 code unique from IATA'),
    dict(slug='icao-4let-idor', plant='azt52hull', ticket='AZ8-53', surface='ICAO 4-letter object-id IDOR', mod='icao4letxxs80', model='Icao4letxxM', lookup='icao4letxxl80', sample='KJFK', owner='geo_id', first='authn', residual='csv', product='icao-4let', bug='AZ8-53 code unique from ICAO'),
    dict(slug='un-m49-idor', plant='azt53hull', ticket='AZ9-54', surface='UN M49 object-id IDOR', mod='unm49xxxxxs80', model='Unm49xxxxxM', lookup='unm49xxxxxl80', sample='840', owner='geo_id', first='mask', residual='admin', product='un-m49', bug='AZ9-54 M49 unique from UNSD'),
    dict(slug='nuts3-idor', plant='azt54hull', ticket='AZ1-55', surface='NUTS3 object-id IDOR', mod='nuts3xxxxxs80', model='Nuts3xxxxxM', lookup='nuts3xxxxxl80', sample='UKI31', owner='geo_id', first='any_member', residual='webhook', product='nuts3', bug='AZ1-55 NUTS unique from Eurostat'),
    dict(slug='fips5-idor', plant='azt55hull', ticket='AZ2-56', surface='FIPS5 object-id IDOR', mod='fips5xxxxxs80', model='Fips5xxxxxM', lookup='fips5xxxxxl80', sample='36061', owner='geo_id', first='list_scope', residual='comments', product='fips5', bug='AZ2-56 FIPS unique from Census'),
    dict(slug='gnis-idor', plant='azt56hull', ticket='AZ3-57', surface='GNIS object-id IDOR', mod='gnisxxxxxxs80', model='GnisxxxxxxM', lookup='gnisxxxxxxl80', sample='2085059', owner='geo_id', first='authn', residual='pdf', product='gnis', bug='AZ3-57 GNIS unique from USGS'),
    dict(slug='geonames-idor', plant='azt57hull', ticket='AZ4-58', surface='GeoNames object-id IDOR', mod='geonamesxxs80', model='GeonamesxxM', lookup='geonamesxxl80', sample='5128581', owner='geo_id', first='mask', residual='export', product='geonames', bug='AZ4-58 id unique from GeoNames'),
    dict(slug='wof-idor', plant='azt58hull', ticket='AZ5-59', surface="Who's On First object-id IDOR", mod='wofxxxxxxxs80', model='WofxxxxxxxM', lookup='wofxxxxxxxl80', sample='85977539', owner='geo_id', first='any_member', residual='search', product='wof', bug='AZ5-59 id unique from WOF'),
    dict(slug='osm-rel-idor', plant='azt59hull', ticket='AZ6-60', surface='OSM relation object-id IDOR', mod='osmrelxxxxs80', model='OsmrelxxxxM', lookup='osmrelxxxxl80', sample='r175905', owner='geo_id', first='list_scope', residual='mget', product='osm-rel', bug='AZ6-60 relation unique from OSM'),
    dict(slug='lei-entity-idor', plant='azt60hull', ticket='AZ7-61', surface='LEI entity object-id IDOR', mod='leientityxs80', model='LeientityxM', lookup='leientityxl80', sample='5493001KJTIIGC8Y1R12', owner='bank_id', first='authn', residual='csv', product='lei-entity', bug='AZ7-61 LEI unique from GLEIF'),
    dict(slug='duns9-idor', plant='azt61hull', ticket='AZ8-62', surface='DUNS-9 object-id IDOR', mod='duns9xxxxxs80', model='Duns9xxxxxM', lookup='duns9xxxxxl80', sample='006928773', owner='bank_id', first='mask', residual='admin', product='duns9', bug='AZ8-62 DUNS unique from D&B'),
    dict(slug='ncage-idor', plant='azt62hull', ticket='AZ9-63', surface='NCAGE object-id IDOR', mod='ncagexxxxxs80', model='NcagexxxxxM', lookup='ncagexxxxxl80', sample='4QNY8', owner='bank_id', first='any_member', residual='webhook', product='ncage', bug='AZ9-63 NCAGE unique from NATO'),
    dict(slug='eori-idor', plant='azt63hull', ticket='AZ1-64', surface='EORI object-id IDOR', mod='eorixxxxxxs80', model='EorixxxxxxM', lookup='eorixxxxxxl80', sample='GB123456789000', owner='bank_id', first='list_scope', residual='comments', product='eori', bug='AZ1-64 EORI unique from TAXUD'),
    dict(slug='vat-eu-idor', plant='azt64hull', ticket='AZ2-65', surface='EU VAT object-id IDOR', mod='vateuxxxxxs80', model='VateuxxxxxM', lookup='vateuxxxxxl80', sample='DE123456789', owner='bank_id', first='authn', residual='pdf', product='vat-eu', bug='AZ2-65 VAT unique from VIES'),
    dict(slug='tin-oecd-idor', plant='azt65hull', ticket='AZ3-66', surface='OECD TIN object-id IDOR', mod='tinoecdxxxs80', model='TinoecdxxxM', lookup='tinoecdxxxl80', sample='TIN-DE-001', owner='bank_id', first='mask', residual='export', product='tin-oecd', bug='AZ3-66 TIN unique from OECD'),
    dict(slug='abn11-idor', plant='azt66hull', ticket='AZ4-67', surface='ABN-11 object-id IDOR', mod='abn11xxxxxs80', model='Abn11xxxxxM', lookup='abn11xxxxxl80', sample='51824753556', owner='bank_id', first='any_member', residual='search', product='abn11', bug='AZ4-67 ABN unique from ABR'),
    dict(slug='swift-bic8-idor', plant='azt67hull', ticket='AZ5-68', surface='BIC8 object-id IDOR', mod='swiftbic8xs80', model='Swiftbic8xM', lookup='swiftbic8xl80', sample='CHASUS33', owner='bank_id', first='list_scope', residual='mget', product='swift-bic8', bug='AZ5-68 BIC unique from SWIFT'),
    dict(slug='iban-mod97-idor', plant='azt68hull', ticket='AZ6-69', surface='IBAN mod97 object-id IDOR', mod='ibanmod97xs80', model='Ibanmod97xM', lookup='ibanmod97xl80', sample='DE89370400440532013000', owner='bank_id', first='authn', residual='csv', product='iban-mod97', bug='AZ6-69 IBAN unique from ISO'),
    dict(slug='bban-idor', plant='azt69hull', ticket='AZ7-70', surface='BBAN object-id IDOR', mod='bbanxxxxxxs80', model='BbanxxxxxxM', lookup='bbanxxxxxxl80', sample='370400440532013000', owner='bank_id', first='mask', residual='admin', product='bban', bug='AZ7-70 BBAN unique from ISO'),
    dict(slug='sortcode-idor', plant='azt70hull', ticket='AZ8-71', surface='UK sort code object-id IDOR', mod='sortcodexxs80', model='SortcodexxM', lookup='sortcodexxl80', sample='40-47-84', owner='bank_id', first='any_member', residual='webhook', product='sortcode', bug='AZ8-71 sort unique from Pay.UK'),
    dict(slug='routing-aba-idor', plant='azt71hull', ticket='AZ9-72', surface='ABA routing object-id IDOR', mod='routingabas80', model='RoutingabaM', lookup='routingabal80', sample='021000021', owner='bank_id', first='list_scope', residual='comments', product='routing-aba', bug='AZ9-72 ABA unique from Fed'),
    dict(slug='ifsc-idor', plant='azt72hull', ticket='AZ1-73', surface='IFSC object-id IDOR', mod='ifscxxxxxxs80', model='IfscxxxxxxM', lookup='ifscxxxxxxl80', sample='SBIN0005943', owner='bank_id', first='authn', residual='pdf', product='ifsc', bug='AZ1-73 IFSC unique from RBI'),
    dict(slug='bsb-idor', plant='azt73hull', ticket='AZ2-74', surface='BSB object-id IDOR', mod='bsbxxxxxxxs80', model='BsbxxxxxxxM', lookup='bsbxxxxxxxl80', sample='062-000', owner='bank_id', first='mask', residual='export', product='bsb', bug='AZ2-74 BSB unique from APCA'),
    dict(slug='clabe-idor', plant='azt74hull', ticket='AZ3-75', surface='CLABE object-id IDOR', mod='clabexxxxxs80', model='ClabexxxxxM', lookup='clabexxxxxl80', sample='002010077777777771', owner='bank_id', first='any_member', residual='search', product='clabe', bug='AZ3-75 CLABE unique from Banxico'),
    dict(slug='cbu-idor', plant='azt75hull', ticket='AZ4-76', surface='CBU object-id IDOR', mod='cbuxxxxxxxs80', model='CbuxxxxxxxM', lookup='cbuxxxxxxxl80', sample='0110599520000012345676', owner='bank_id', first='list_scope', residual='mget', product='cbu', bug='AZ4-76 CBU unique from BCRA'),
    dict(slug='elincs-idor', plant='azt76hull', ticket='AZ5-77', surface='ELINCS object-id IDOR', mod='elincsxxxxs80', model='ElincsxxxxM', lookup='elincsxxxxl80', sample='400-001-0', owner='lab_id', first='authn', residual='csv', product='elincs', bug='AZ5-77 ELINCS unique from ECHA'),
    dict(slug='reach-idor', plant='azt77hull', ticket='AZ6-78', surface='REACH reg object-id IDOR', mod='reachxxxxxs80', model='ReachxxxxxM', lookup='reachxxxxxl80', sample='01-2119486799-10-0000', owner='lab_id', first='mask', residual='admin', product='reach', bug='AZ6-78 reg unique from ECHA'),
    dict(slug='tsca-idor', plant='azt78hull', ticket='AZ7-79', surface='TSCA acc object-id IDOR', mod='tscaxxxxxxs80', model='TscaxxxxxxM', lookup='tscaxxxxxxl80', sample='TSCA-001', owner='lab_id', first='any_member', residual='webhook', product='tsca', bug='AZ7-79 acc unique from EPA'),
    dict(slug='ghs-cas-idor', plant='azt79hull', ticket='AZ8-80', surface='GHS CAS object-id IDOR', mod='ghscasxxxxs80', model='GhscasxxxxM', lookup='ghscasxxxxl80', sample='64-17-5', owner='lab_id', first='list_scope', residual='comments', product='ghs-cas', bug='AZ8-80 CAS unique from GHS'),
]


BFLA_ROWS = [
    dict(slug='karpenter-nd-skip-delete', plant='azt00hull', ticket='AZ1-1', surface='Karpenter NodeClaim delete missing rbac', family='js_route', skip='kubectl delete nodeclaim notes', auth='kubectl get nodeclaim notes', leftover='put'),
    dict(slug='cas-node-skip-delete', plant='azt01hull', ticket='AZ2-2', surface='cluster-autoscaler node delete missing rbac', family='js_route', skip='kubectl delete node notes', auth='kubectl get node notes', leftover='patch'),
    dict(slug='vpa-rec-skip-delete', plant='azt02hull', ticket='AZ3-3', surface='VPA recommendation delete missing rbac', family='js_route', skip='kubectl delete vpa notes', auth='kubectl get vpa notes', leftover='update'),
    dict(slug='goldilocks-skip-delete', plant='azt03hull', ticket='AZ4-4', surface='Goldilocks vpa delete missing rbac', family='js_route', skip='kubectl delete vpa notes -n goldilocks', auth='kubectl get vpa -n goldilocks', leftover='put'),
    dict(slug='descheduler-skip-delete', plant='azt04hull', ticket='AZ5-5', surface='Descheduler policy delete missing rbac', family='js_route', skip='kubectl delete deschedulerpolicy notes', auth='kubectl get deschedulerpolicy notes', leftover='patch'),
    dict(slug='kyverno-pol-skip-delete', plant='azt05hull', ticket='AZ6-6', surface='Kyverno policy delete missing rbac', family='js_route', skip='kubectl delete clusterpolicy notes', auth='kubectl get clusterpolicy notes', leftover='update'),
    dict(slug='gatekeeper-c-skip-delete', plant='azt06hull', ticket='AZ7-7', surface='Gatekeeper constraint delete missing rbac', family='js_route', skip='kubectl delete k8srequiredlabels notes', auth='kubectl get k8srequiredlabels notes', leftover='put'),
    dict(slug='falco-rule-skip-delete', plant='azt07hull', ticket='AZ8-8', surface='Falco rule delete missing rbac', family='js_route', skip='kubectl delete falcorules notes', auth='kubectl get falcorules notes', leftover='patch'),
    dict(slug='tetragon-skip-delete', plant='azt08hull', ticket='AZ9-9', surface='Tetragon tracingpolicy delete missing rbac', family='js_route', skip='kubectl delete tracingpolicy notes', auth='kubectl get tracingpolicy notes', leftover='update'),
    dict(slug='tracee-skip-delete', plant='azt09hull', ticket='AZ1-10', surface='Tracee policy delete missing rbac', family='js_route', skip='kubectl delete traceepolicy notes', auth='kubectl get traceepolicy notes', leftover='put'),
    dict(slug='osquery-skip-delete', plant='azt10hull', ticket='AZ2-11', surface='osquery pack delete missing tls auth', family='js_route', skip='osqueryi --pack notes --disable', auth='osqueryi --tls_hostname $OSQ', leftover='patch'),
    dict(slug='wazuh-skip-delete', plant='azt11hull', ticket='AZ3-12', surface='Wazuh agent delete missing token', family='js_route', skip='curl -X DELETE $WAZUH/agents/1', auth='curl -H "Authorization: Bearer $WAZUH" $WAZUH/agents/1', leftover='update'),
    dict(slug='suricata-skip-delete', plant='azt12hull', ticket='AZ4-13', surface='Suricata rule disable missing auth', family='js_route', skip='suricatasc -c disable-rule notes', auth='suricatasc -c ruleset-stats', leftover='put'),
    dict(slug='zeek-skip-delete', plant='azt13hull', ticket='AZ5-14', surface='Zeek script unload missing ctl', family='js_route', skip='zeekctl stop notes', auth='zeekctl status', leftover='patch'),
    dict(slug='snort-skip-delete', plant='azt14hull', ticket='AZ6-15', surface='Snort sid disable missing conf', family='js_route', skip='snort --disable-sid notes', auth='snort -T -c /etc/snort/snort.conf', leftover='update'),
    dict(slug='crowdsec-skip-delete', plant='azt15hull', ticket='AZ7-16', surface='CrowdSec decision delete missing api', family='js_route', skip='cscli decisions delete --id 1', auth='cscli decisions list', leftover='put'),
    dict(slug='fail2ban-skip-delete', plant='azt16hull', ticket='AZ8-17', surface='fail2ban unban missing sudoers', family='js_route', skip='fail2ban-client unban --all', auth='fail2ban-client status', leftover='patch'),
    dict(slug='sshguard-skip-delete', plant='azt17hull', ticket='AZ9-18', surface='sshguard whitelist wipe missing conf', family='js_route', skip='sshguard -w -', auth='sshguard -l', leftover='update'),
    dict(slug='csf-skip-delete', plant='azt18hull', ticket='AZ1-19', surface='CSF deny delete missing auth', family='js_route', skip='csf -dr 1.1.1.1', auth='csf -g 1.1.1.1', leftover='put'),
    dict(slug='ufw-skip-delete', plant='azt19hull', ticket='AZ2-20', surface='ufw rule delete missing sudoers', family='js_route', skip='ufw delete 1', auth='ufw status numbered', leftover='patch'),
    dict(slug='firewalld-skip-delete', plant='azt20hull', ticket='AZ3-21', surface='firewalld rich-rule delete missing polkit', family='js_route', skip='firewall-cmd --remove-rich-rule notes', auth='firewall-cmd --list-all', leftover='update'),
    dict(slug='nftables-skip-delete', plant='azt21hull', ticket='AZ4-22', surface='nftables chain flush missing cap', family='js_route', skip='nft flush chain inet notes n', auth='nft list ruleset', leftover='put'),
    dict(slug='iptables-skip-delete', plant='azt22hull', ticket='AZ5-23', surface='iptables -F missing cap', family='js_route', skip='iptables -F', auth='iptables -L -n', leftover='patch'),
    dict(slug='ipset-skip-delete', plant='azt23hull', ticket='AZ6-24', surface='ipset destroy missing cap', family='js_route', skip='ipset destroy notes', auth='ipset list notes', leftover='update'),
    dict(slug='aws-sg-skip-delete', plant='azt24hull', ticket='AZ7-25', surface='AWS SG delete missing creds', family='js_route', skip='aws ec2 delete-security-group --group-id sg-notes', auth='aws ec2 describe-security-groups --group-ids sg-notes', leftover='put'),
    dict(slug='gcp-fw-skip-delete', plant='azt25hull', ticket='AZ8-26', surface='GCP firewall delete missing adc', family='js_route', skip='gcloud compute firewall-rules delete notes --quiet', auth='gcloud compute firewall-rules describe notes', leftover='patch'),
    dict(slug='azure-nsg-skip-delete', plant='azt26hull', ticket='AZ9-27', surface='Azure NSG delete missing sp', family='js_route', skip='az network nsg delete -g g -n notes', auth='az network nsg show -g g -n notes', leftover='update'),
    dict(slug='oci-nsg-skip-delete', plant='azt27hull', ticket='AZ1-28', surface='OCI NSG delete missing config', family='js_route', skip='oci network nsg delete --nsg-id notes --force', auth='oci network nsg get --nsg-id notes', leftover='put'),
    dict(slug='do-fw-skip-delete', plant='azt28hull', ticket='AZ2-29', surface='DO firewall delete missing token', family='js_route', skip='doctl compute firewall delete notes -f', auth='doctl compute firewall get notes', leftover='patch'),
    dict(slug='cloudflare-waf-skip-delete', plant='azt29hull', ticket='AZ3-30', surface='Cloudflare WAF rule delete missing token', family='js_route', skip='curl -X DELETE $CF/zones/z/firewall/rules/notes', auth='curl -H "Authorization: Bearer $CF" $CF/zones/z/firewall/rules/notes', leftover='update'),
    dict(slug='fastly-acl-skip-delete', plant='azt30hull', ticket='AZ4-31', surface='Fastly ACL delete missing token', family='js_route', skip='fastly acl delete --name=notes', auth='fastly acl describe --name=notes', leftover='put'),
    dict(slug='akamai-waf-skip-delete', plant='azt31hull', ticket='AZ5-32', surface='Akamai WAF config delete missing edgerc', family='js_route', skip='akamai appsec delete-config notes', auth='akamai appsec get-config notes', leftover='patch'),
    dict(slug='imperva-skip-delete', plant='azt32hull', ticket='AZ6-33', surface='Imperva site delete missing api-id', family='js_route', skip='curl -X DELETE $IMP/api/prov/v1/sites/id/notes', auth='curl -H "x-API-Id: $IMP" $IMP/api/prov/v1/sites/status', leftover='update'),
    dict(slug='sucuri-skip-delete', plant='azt33hull', ticket='AZ7-34', surface='Sucuri whitelist delete missing key', family='js_route', skip='curl -X POST $SUCURI/api?k=$K&a=clear_whitelist', auth='curl $SUCURI/api?k=$K&a=show_whitelist', leftover='put'),
    dict(slug='modsec-skip-delete', plant='azt34hull', ticket='AZ8-35', surface='ModSecurity rule remove missing conf', family='js_route', skip='modsec-rules-check -d notes', auth='apachectl -t', leftover='patch'),
    dict(slug='naxsi-skip-delete', plant='azt35hull', ticket='AZ9-36', surface='NAXSI wl delete missing conf', family='js_route', skip='rm /etc/nginx/naxsi/notes.rules', auth='nginx -t', leftover='update'),
    dict(slug='coraza-skip-delete', plant='azt36hull', ticket='AZ1-37', surface='Coraza directive delete missing conf', family='js_route', skip='coraza-check -d notes', auth='coraza-check -t', leftover='put'),
    dict(slug='openappsec-skip-delete', plant='azt37hull', ticket='AZ2-38', surface='OpenAppSec policy delete missing token', family='js_route', skip='open-appsec-cli policy delete notes', auth='open-appsec-cli policy get notes', leftover='patch'),
    dict(slug='shadowd-skip-delete', plant='azt38hull', ticket='AZ3-39', surface='ShadowDaemon ignore delete missing auth', family='js_route', skip='shadowd --ignore-delete notes', auth='shadowd --status', leftover='update'),
    dict(slug='vault-pol-skip-delete', plant='azt39hull', ticket='AZ4-40', surface='Vault policy delete missing token', family='js_route', skip='vault policy delete notes', auth='vault policy read notes', leftover='put'),
    dict(slug='sops-skip-delete', plant='azt40hull', ticket='AZ5-41', surface='sops key delete missing age', family='js_route', skip='sops -d --ignore-mac notes.yaml', auth='sops -d notes.yaml', leftover='patch'),
    dict(slug='sealedsec-skip-delete', plant='azt41hull', ticket='AZ6-42', surface='SealedSecret delete missing rbac', family='js_route', skip='kubectl delete sealedsecret notes', auth='kubectl get sealedsecret notes', leftover='update'),
    dict(slug='externalsec-skip-delete', plant='azt42hull', ticket='AZ7-43', surface='ExternalSecret delete missing rbac', family='js_route', skip='kubectl delete externalsecret notes', auth='kubectl get externalsecret notes', leftover='put'),
    dict(slug='certmgr-iss-skip-delete', plant='azt43hull', ticket='AZ8-44', surface='cert-manager Issuer delete missing rbac', family='js_route', skip='kubectl delete issuer notes', auth='kubectl get issuer notes', leftover='patch'),
    dict(slug='letsencrypt-skip-delete', plant='azt44hull', ticket='AZ9-45', surface="Let's Encrypt cert revoke missing account", family='js_route', skip='certbot revoke --cert-name notes --non-interactive', auth='certbot certificates', leftover='update'),
    dict(slug='acme-sh-skip-delete', plant='azt45hull', ticket='AZ1-46', surface='acme.sh revoke missing account', family='js_route', skip='acme.sh --revoke -d notes', auth='acme.sh --list', leftover='put'),
    dict(slug='certbot-skip-delete', plant='azt46hull', ticket='AZ2-47', surface='certbot delete missing account', family='js_route', skip='certbot delete --cert-name notes --non-interactive', auth='certbot certificates', leftover='patch'),
    dict(slug='lego-skip-delete', plant='azt47hull', ticket='AZ3-48', surface='lego revoke missing account', family='js_route', skip='lego revoke --domains notes', auth='lego list', leftover='update'),
    dict(slug='stepca-skip-delete', plant='azt48hull', ticket='AZ4-49', surface='step-ca revoke missing provisioner', family='js_route', skip='step ca revoke notes --offline', auth='step ca list', leftover='put'),
    dict(slug='spiffe-skip-delete', plant='azt49hull', ticket='AZ5-50', surface='SPIFFE entry delete missing socket', family='js_route', skip='spire-server entry delete -entryID notes', auth='spire-server entry show -entryID notes', leftover='patch'),
    dict(slug='istio-peer-skip-delete', plant='azt50hull', ticket='AZ6-51', surface='Istio PeerAuthentication delete missing rbac', family='js_route', skip='kubectl delete peerauthentication notes', auth='kubectl get peerauthentication notes', leftover='update'),
    dict(slug='linkerd-sa-skip-delete', plant='azt51hull', ticket='AZ7-52', surface='Linkerd ServiceProfile delete missing rbac', family='js_route', skip='kubectl delete serviceprofile notes', auth='kubectl get serviceprofile notes', leftover='put'),
    dict(slug='consul-int-skip-delete', plant='azt52hull', ticket='AZ8-53', surface='Consul intention delete missing ACL', family='js_route', skip='consul intention delete notes src', auth='consul intention list', leftover='patch'),
    dict(slug='teleport-skip-delete', plant='azt53hull', ticket='AZ9-54', surface='Teleport user delete missing auth', family='js_route', skip='tctl users rm notes', auth='tctl users ls', leftover='update'),
    dict(slug='pomerium-skip-delete', plant='azt54hull', ticket='AZ1-55', surface='Pomerium policy delete missing databroker', family='js_route', skip='pomerium-cli delete policy notes', auth='pomerium-cli get policy notes', leftover='put'),
    dict(slug='oauth2proxy-skip-delete', plant='azt55hull', ticket='AZ2-56', surface='oauth2-proxy cookie wipe missing secret', family='js_route', skip='oauth2-proxy --flush-cookies', auth='oauth2-proxy --version', leftover='patch'),
    dict(slug='authelia-skip-delete', plant='azt56hull', ticket='AZ3-57', surface='Authelia user delete missing storage', family='js_route', skip='authelia storage user delete notes', auth='authelia storage user get notes', leftover='update'),
    dict(slug='authentik-skip-delete', plant='azt57hull', ticket='AZ4-58', surface='Authentik user delete missing token', family='js_route', skip='curl -X DELETE $AK/api/v3/core/users/1/', auth='curl -H "Authorization: Bearer $AK" $AK/api/v3/core/users/1/', leftover='put'),
    dict(slug='casdoor-skip-delete', plant='azt58hull', ticket='AZ5-59', surface='Casdoor user delete missing client', family='js_route', skip='curl -X POST $CD/api/delete-user -d {name:notes}', auth='curl $CD/api/get-user?id=notes', leftover='patch'),
    dict(slug='logto-skip-delete', plant='azt59hull', ticket='AZ6-60', surface='Logto user delete missing m2m', family='js_route', skip='curl -X DELETE $LOGTO/api/users/notes', auth='curl -H "Authorization: Bearer $LOGTO" $LOGTO/api/users/notes', leftover='update'),
    dict(slug='clerk-skip-delete', plant='azt60hull', ticket='AZ7-61', surface='Clerk user delete missing secret', family='js_route', skip='curl -X DELETE $CLERK/v1/users/notes', auth='curl -H "Authorization: Bearer $CLERK" $CLERK/v1/users/notes', leftover='put'),
    dict(slug='auth0-rule-skip-delete', plant='azt61hull', ticket='AZ8-62', surface='Auth0 rule delete missing token', family='js_route', skip='a0deploy delete --rules notes', auth='a0deploy export --format yaml', leftover='patch'),
    dict(slug='okta-app-skip-delete', plant='azt62hull', ticket='AZ9-63', surface='Okta app delete missing token', family='js_route', skip='okta apps delete notes', auth='okta apps get notes', leftover='update'),
    dict(slug='onelogin-skip-delete', plant='azt63hull', ticket='AZ1-64', surface='OneLogin app delete missing token', family='js_route', skip='curl -X DELETE $OL/api/2/apps/notes', auth='curl -H "Authorization: bearer $OL" $OL/api/2/apps/notes', leftover='put'),
    dict(slug='pingid-skip-delete', plant='azt64hull', ticket='AZ2-65', surface='PingID user unpair missing key', family='js_route', skip='curl -X POST $PING/unpair -d {username:notes}', auth='curl $PING/status', leftover='patch'),
    dict(slug='duo-skip-delete', plant='azt65hull', ticket='AZ3-66', surface='Duo user delete missing ikey', family='js_route', skip='duo-admin delete-user notes', auth='duo-admin get-user notes', leftover='update'),
    dict(slug='yubico-skip-delete', plant='azt66hull', ticket='AZ4-67', surface='YubiCloud client delete missing secret', family='js_route', skip='ykman otp delete 1', auth='ykman info', leftover='put'),
    dict(slug='webauthn-skip-delete', plant='azt67hull', ticket='AZ5-68', surface='WebAuthn credential delete missing rp', family='js_route', skip='curl -X DELETE $WA/credentials/notes', auth='curl $WA/credentials/notes', leftover='patch'),
    dict(slug='passkey-skip-delete', plant='azt68hull', ticket='AZ6-69', surface='passkey credential delete missing rp', family='js_route', skip='curl -X DELETE $PK/passkeys/notes', auth='curl $PK/passkeys/notes', leftover='update'),
    dict(slug='dex-idp-skip-delete', plant='azt69hull', ticket='AZ7-70', surface='Dex password delete missing config', family='js_route', skip='dex serve --delete-password notes', auth='dex serve --list-passwords', leftover='put'),
    dict(slug='kanidm-skip-delete', plant='azt70hull', ticket='AZ8-71', surface='Kanidm person delete missing token', family='js_route', skip='kanidm person delete notes', auth='kanidm person get notes', leftover='patch'),
    dict(slug='zitadel-skip-delete', plant='azt71hull', ticket='AZ9-72', surface='Zitadel user delete missing pat', family='js_route', skip='zita-cli user delete notes', auth='zita-cli user get notes', leftover='update'),
    dict(slug='fusionauth-skip-delete', plant='azt72hull', ticket='AZ1-73', surface='FusionAuth user delete missing key', family='js_route', skip='curl -X DELETE $FA/api/user/notes', auth='curl -H "Authorization: $FA" $FA/api/user/notes', leftover='put'),
    dict(slug='hydra-skip-delete', plant='azt73hull', ticket='AZ2-74', surface='Hydra client delete missing admin', family='js_route', skip='hydra delete client notes', auth='hydra get client notes', leftover='patch'),
    dict(slug='ory-kratos-id-skip-delete', plant='azt74hull', ticket='AZ3-75', surface='Ory Kratos identity delete missing admin', family='js_route', skip='kratos delete identity notes', auth='kratos get identity notes', leftover='update'),
    dict(slug='ory-oath-rule-skip-delete', plant='azt75hull', ticket='AZ4-76', surface='Ory Oathkeeper rule delete missing api', family='js_route', skip='curl -X DELETE $OH/rules/notes', auth='curl $OH/rules/notes', leftover='put'),
    dict(slug='spicedb-skip-delete', plant='azt76hull', ticket='AZ5-77', surface='SpiceDB relationship delete missing preshared', family='js_route', skip='zed relationship delete notes:n#v@user:u', auth='zed relationship read notes:n', leftover='patch'),
    dict(slug='openfga-skip-delete', plant='azt77hull', ticket='AZ6-78', surface='OpenFGA tuple delete missing token', family='js_route', skip='fga tuple delete --store-id s user:u object:notes', auth='fga tuple read --store-id s', leftover='update'),
    dict(slug='cerbos-skip-delete', plant='azt78hull', ticket='AZ7-79', surface='Cerbos policy delete missing admin', family='js_route', skip='cerbosctl del notes', auth='cerbosctl get notes', leftover='put'),
    dict(slug='permitio-skip-delete', plant='azt79hull', ticket='AZ8-80', surface='Permit.io resource delete missing token', family='js_route', skip='permit api resources delete notes', auth='permit api resources get notes', leftover='patch'),
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
