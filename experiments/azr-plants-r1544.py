"""Extra unique IDOR/BFLA plants for authz-regression-factory r1544+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r1543 vesselNNNN-sys.
Not clones of r1364 geohash-cell-idor / channels-consumer-skip-delete.
Not clones of r1445–r1458 casbin/oso/keycloak clones.
Not clones of r1543 gstin-isd-idor / chi-mount-skip-delete.
"""
from __future__ import annotations


EXTRA_IDOR_ROWS = [
    dict(slug='e212-mccmnc-idor', plant='afterbody', ticket='AFT-1', surface='E.212 MCC-MNC object-id IDOR', mod='e212mccs', model='E212mcc', lookup='mccmnc', sample='310-410', owner='net_id', first='authn', residual='pdf', product='e212-itu', bug='AFT-1 MCC-MNC unique from ITU E.212'),
    dict(slug='npanxx-lerg-idor', plant='aftercastle', ticket='AFT-2', surface='LERG NPA-NXX object-id IDOR', mod='npanxxs', model='Npanxx', lookup='npanxx', sample='212-555', owner='telco_id', first='mask', residual='export', product='lerg-npa', bug='AFT-2 NPA-NXX unique from LERG'),
    dict(slug='imeisv-svn-idor', plant='afterhatch', ticket='AFT-3', surface='IMEISV object-id IDOR', mod='imeisvs', model='Imeisv', lookup='imeisv', sample='3569380356438090', owner='oem_id', first='any_member', residual='search', product='imeisv-3gpp', bug='AFT-3 IMEISV unique from 3GPP TS 23.003'),
    dict(slug='euicc-eid-idor', plant='bagreef', ticket='BAG-4', surface='eUICC EID object-id IDOR', mod='euicceids', model='EuiccEid', lookup='euiccid', sample='89049032005008800000000000000000', owner='oem_id', first='list_scope', residual='mget', product='eid-gsma', bug='BAG-4 EID unique from GSMA SGP.22'),
    dict(slug='tmsi-paging-idor', plant='bailsling', ticket='BAI-5', surface='TMSI paging object-id IDOR', mod='tmsipages', model='Tmsipage', lookup='tmsi', sample='C359F119', owner='net_id', first='authn', residual='csv', product='tmsi-3gpp', bug='BAI-5 TMSI unique from 3GPP'),
    dict(slug='guti-lte-idor', plant='balkpiece', ticket='BAL-6', surface='LTE GUTI object-id IDOR', mod='ltegutis', model='Lteguti', lookup='guti', sample='31041000C359F119', owner='net_id', first='mask', residual='admin', product='guti-eps', bug='BAL-6 GUTI unique from EPS'),
    dict(slug='suci-5g-idor', plant='battenpocket', ticket='BAT-7', surface='5G SUCI object-id IDOR', mod='suci5gs', model='Suci5g', lookup='suci', sample='suci-0-310-410-0-0-abcd', owner='net_id', first='any_member', residual='webhook', product='suci-5g', bug='BAT-7 SUCI unique from 3GPP 5G'),
    dict(slug='apn-ni-idor', plant='beamclamp', ticket='BEA-8', surface='APN NI object-id IDOR', mod='apnnis', model='Apnni', lookup='apnni', sample='internet.carrier.mnc410.mcc310.gprs', owner='net_id', first='list_scope', residual='comments', product='apn-3gpp', bug='BEA-8 APN unique from 3GPP'),
    dict(slug='cgi-gsm-idor', plant='belaypin', ticket='BEL-9', surface='GSM CGI object-id IDOR', mod='gsmcgis', model='Gsmcgi', lookup='gsmcgi', sample='310-410-1234-56789', owner='net_id', first='authn', residual='pdf', product='cgi-gsm', bug='BEL-9 CGI unique from GSM 03.03'),
    dict(slug='ecgi-lte-idor', plant='bightknot', ticket='BIG-1', surface='LTE ECGI object-id IDOR', mod='ecgislts', model='Ecgilte', lookup='ecgi', sample='310-410-00ABCDE', owner='net_id', first='mask', residual='export', product='ecgi-lte', bug='BIG-1 ECGI unique from E-UTRAN'),
    dict(slug='nci-nr-idor', plant='bilgestrake', ticket='BIL-2', surface='NR Cell Identity object-id IDOR', mod='nrcells', model='Nrcell', lookup='nrcell', sample='310-410-0ABCDEF', owner='net_id', first='any_member', residual='search', product='nci-nr', bug='BIL-2 NCI unique from 5G NR'),
    dict(slug='tai-lte-idor', plant='bittpin', ticket='BIT-3', surface='LTE TAI object-id IDOR', mod='ltetais', model='Ltetai', lookup='ltetai', sample='310-410-ABC0', owner='net_id', first='list_scope', residual='mget', product='tai-lte', bug='BIT-3 TAI unique from EPS'),
    dict(slug='lai-gsm-idor', plant='boomcrotch', ticket='BOO-4', surface='GSM LAI object-id IDOR', mod='gsmlais', model='Gsmlai', lookup='gsmlai', sample='310-410-1234', owner='net_id', first='authn', residual='csv', product='lai-gsm', bug='BOO-4 LAI unique from GSM'),
    dict(slug='rai-gprs-idor', plant='boomgallows', ticket='BOO-5', surface='GPRS RAI object-id IDOR', mod='gprsrais', model='Gprsrai', lookup='gprsrai', sample='310-410-1234-67', owner='net_id', first='mask', residual='admin', product='rai-gprs', bug='BOO-5 RAI unique from GPRS'),
    dict(slug='sai-umts-idor', plant='bowchock', ticket='BOW-6', surface='UMTS SAI object-id IDOR', mod='umtsais', model='Umtsai', lookup='umtsai', sample='310-410-1234-56', owner='net_id', first='any_member', residual='webhook', product='sai-umts', bug='BOW-6 SAI unique from UTRAN'),
    dict(slug='hessid-wifi-idor', plant='bowroller', ticket='BOW-7', surface='HESSID Wi-Fi object-id IDOR', mod='hessids', model='Hessid', lookup='hessid', sample='00:11:22:33:44:55', owner='campus_id', first='list_scope', residual='comments', product='hessid-ieee', bug='BOW-7 HESSID unique from IEEE 802.11u'),
    dict(slug='smdp-fqdn-idor', plant='breastback', ticket='BRE-8', surface='SM-DP+ FQDN object-id IDOR', mod='smdpfqdns', model='Smdpfqdn', lookup='smdpfqdn', sample='smdp.rsp.example', owner='oem_id', first='authn', residual='pdf', product='smdp-gsma', bug='BRE-8 SM-DP+ unique from GSMA'),
    dict(slug='norad-cat-idor', plant='breechrope', ticket='BRE-9', surface='NORAD catalog object-id IDOR', mod='noradcats', model='Noradcat', lookup='norad', sample='25544', owner='lab_id', first='mask', residual='export', product='norad-sat', bug='BRE-9 NORAD unique from CelesTrak'),
    dict(slug='cospar-id-idor', plant='bulkclamp', ticket='BUL-1', surface='COSPAR designation object-id IDOR', mod='cospards', model='Cospard', lookup='cospar', sample='1998-067A', owner='lab_id', first='any_member', residual='search', product='cospar-id', bug='BUL-1 COSPAR unique from COSPAR'),
    dict(slug='mpc-packed-idor', plant='buntgasket', ticket='BUN-2', surface='MPC packed designation object-id IDOR', mod='mpcs', model='Mpcpack', lookup='mpcpacked', sample='K23A00A', owner='lab_id', first='list_scope', residual='mget', product='mpc-packed', bug='BUN-2 packed desig unique from MPC'),
    dict(slug='naif-spk-idor', plant='cableclench', ticket='CAB-3', surface='NAIF SPK object-id IDOR', mod='naifspks', model='Naifspk', lookup='naifspk', sample='399', owner='lab_id', first='authn', residual='csv', product='naif-spk', bug='CAB-3 NAIF id unique from SPICE'),
    dict(slug='hipparcos-idor', plant='camberkeel', ticket='CAM-4', surface='Hipparcos HIP object-id IDOR', mod='hipcats', model='Hipcat', lookup='hipid', sample='HIP 71683', owner='lab_id', first='mask', residual='admin', product='hipparcos-id', bug='CAM-4 HIP unique from Hipparcos'),
    dict(slug='tycho2-idor', plant='cantbeam', ticket='CAN-5', surface='Tycho-2 object-id IDOR', mod='tyc2s', model='Tyc2', lookup='tyc2', sample='TYC 1234-5678-1', owner='lab_id', first='any_member', residual='webhook', product='tycho2-id', bug='CAN-5 TYC unique from Tycho-2'),
    dict(slug='gaia-source-idor', plant='capstanbar', ticket='CAP-6', surface='Gaia source object-id IDOR', mod='gaiasrcs', model='Gaiasrc', lookup='gaiasid', sample='Gaia DR3 1234567890123456789', owner='lab_id', first='list_scope', residual='comments', product='gaia-src', bug='CAP-6 source_id unique from Gaia'),
    dict(slug='hd-catalog-idor', plant='carlingbeam', ticket='CAR-7', surface='Henry Draper object-id IDOR', mod='hdcats', model='Hdcat', lookup='hdnum', sample='HD 209458', owner='lab_id', first='authn', residual='pdf', product='hd-cat', bug='CAR-7 HD unique from Henry Draper'),
    dict(slug='hr-yale-idor', plant='catdavitarm', ticket='CAT-8', surface='Yale Bright Star object-id IDOR', mod='hrcats', model='Hrcat', lookup='hrnum', sample='HR 7001', owner='lab_id', first='mask', residual='export', product='hr-yale', bug='CAT-8 HR unique from Yale BSC'),
    dict(slug='messier-idor', plant='chainwale', ticket='CHA-9', surface='Messier object-id IDOR', mod='messiers', model='Messier', lookup='mesnum', sample='M31', owner='lab_id', first='any_member', residual='search', product='messier-id', bug='CHA-9 Messier unique from catalog'),
    dict(slug='ngc-obj-idor', plant='cheekpiece', ticket='CHE-1', surface='NGC object-id IDOR', mod='ngcobjs', model='Ngcobj', lookup='ngcnum', sample='NGC 224', owner='lab_id', first='list_scope', residual='mget', product='ngc-obj', bug='CHE-1 NGC unique from Dreyer'),
    dict(slug='ic-dreyer-idor', plant='chockstay', ticket='CHO-2', surface='Index Catalogue object-id IDOR', mod='icobjs', model='Icobj', lookup='icnum', sample='IC 1613', owner='lab_id', first='authn', residual='csv', product='ic-dreyer', bug='CHO-2 IC unique from Dreyer'),
    dict(slug='pgc-galaxy-idor', plant='clewcringle', ticket='CLE-3', surface='PGC galaxy object-id IDOR', mod='pgcs', model='Pgcgal', lookup='pgcid', sample='PGC 2557', owner='lab_id', first='mask', residual='admin', product='pgc-gal', bug='CLE-3 PGC unique from LEDA'),
    dict(slug='twomass-idor', plant='clinchrivet', ticket='CLI-4', surface='2MASS object-id IDOR', mod='twomasss', model='Twomass', lookup='twomass', sample='2MASS J05351494-0523539', owner='lab_id', first='any_member', residual='webhook', product='twomass-id', bug='CLI-4 2MASS unique from IPAC'),
    dict(slug='wise-allwise-idor', plant='coamingwell', ticket='COA-5', surface='AllWISE object-id IDOR', mod='allwises', model='Allwise', lookup='wiseid', sample='WISEA J174102.78-333338.3', owner='lab_id', first='list_scope', residual='comments', product='wise-id', bug='COA-5 AllWISE unique from IRSA'),
    dict(slug='sdss-objid-idor', plant='cockpitgrate', ticket='COC-6', surface='SDSS objID object-id IDOR', mod='sdssobjs', model='Sdssobj', lookup='sdssoid', sample='1237654382514995200', owner='lab_id', first='authn', residual='pdf', product='sdss-obj', bug='COC-6 objID unique from SDSS'),
    dict(slug='tic-tess-idor', plant='companionhatch', ticket='COM-7', surface='TESS TIC object-id IDOR', mod='tictesss', model='Tictess', lookup='ticid', sample='TIC 261136679', owner='lab_id', first='mask', residual='export', product='tic-tess', bug='COM-7 TIC unique from MAST'),
    dict(slug='kic-kepler-idor', plant='cordagecoil', ticket='COR-8', surface='Kepler KIC object-id IDOR', mod='kickeps', model='Kickep', lookup='kicid', sample='KIC 8462852', owner='lab_id', first='any_member', residual='search', product='kic-kepler', bug='COR-8 KIC unique from Kepler'),
    dict(slug='epic-k2-idor', plant='counterrail', ticket='COU-9', surface='K2 EPIC object-id IDOR', mod='epick2s', model='Epick2', lookup='epicid', sample='EPIC 201367835', owner='lab_id', first='list_scope', residual='mget', product='epic-k2', bug='COU-9 EPIC unique from K2'),
    dict(slug='koi-kepler-idor', plant='coxswainbox', ticket='COX-1', surface='KOI candidate object-id IDOR', mod='koikeps', model='Koikep', lookup='koiid', sample='KOI-7016.01', owner='lab_id', first='authn', residual='csv', product='koi-kepler', bug='COX-1 KOI unique from Kepler'),
    dict(slug='vsx-aavso-idor', plant='crancehoop', ticket='CRA-2', surface='VSX variable object-id IDOR', mod='vsxaavs', model='Vsxaav', lookup='vsxid', sample='VSX J0535-05', owner='lab_id', first='mask', residual='admin', product='vsx-aavso', bug='CRA-2 VSX unique from AAVSO'),
    dict(slug='simbad-oid-idor', plant='cringleeye', ticket='CRI-3', surface='SIMBAD oid object-id IDOR', mod='simboids', model='Simboid', lookup='simboid', sample='506956', owner='lab_id', first='any_member', residual='webhook', product='simbad-oid', bug='CRI-3 oid unique from CDS'),
    dict(slug='ned-objname-idor', plant='crosstreeband', ticket='CRO-4', surface='NED object-name object-id IDOR', mod='nednames', model='Nedname', lookup='nedname', sample='MESSIER 031', owner='lab_id', first='list_scope', residual='comments', product='ned-name', bug='CRO-4 NED name unique from IPAC'),
    dict(slug='eic-entsoe-idor', plant='crowfootspan', ticket='CRO-5', surface='EIC energy object-id IDOR', mod='eicents', model='Eicent', lookup='eiccode', sample='10Y1001A1001A83F', owner='grid_id', first='authn', residual='pdf', product='eic-entsoe', bug='CRO-5 EIC unique from ENTSO-E'),
    dict(slug='nerc-cid-idor', plant='cunninghamhole', ticket='CUN-6', surface='NERC company object-id IDOR', mod='nerccids', model='Nerccid', lookup='nerccid', sample='NCR00001', owner='grid_id', first='mask', residual='export', product='nerc-cid', bug='CUN-6 NERC CID unique from CORES'),
    dict(slug='orispl-eia-idor', plant='cutwaterplate', ticket='CUT-7', surface='EIA ORISPL object-id IDOR', mod='orispls', model='Orispl', lookup='orispl', sample='3', owner='grid_id', first='any_member', residual='search', product='orispl-eia', bug='CUT-7 ORISPL unique from EIA-860'),
    dict(slug='pjm-pnode-idor', plant='daggercase', ticket='DAG-8', surface='PJM pnode object-id IDOR', mod='pjmpnodes', model='Pjmpnode', lookup='pjmpnode', sample='123456789', owner='grid_id', first='list_scope', residual='mget', product='pjm-pnode', bug='DAG-8 pnode unique from PJM'),
    dict(slug='caiso-res-idor', plant='davitguy', ticket='DAV-9', surface='CAISO resource object-id IDOR', mod='caisores', model='Caisores', lookup='caisores', sample='MOSSLD_7_N001', owner='grid_id', first='authn', residual='csv', product='caiso-res', bug='DAV-9 resource unique from CAISO'),
    dict(slug='ercot-qse-idor', plant='deadeyeplate', ticket='DEA-1', surface='ERCOT QSE object-id IDOR', mod='ercotqses', model='Ercotqse', lookup='ercotqse', sample='QSE123', owner='grid_id', first='mask', residual='admin', product='ercot-qse', bug='DEA-1 QSE unique from ERCOT'),
    dict(slug='nyiso-ptid-idor', plant='deckprism', ticket='DEC-2', surface='NYISO PTID object-id IDOR', mod='nyisoptids', model='Nyisoptid', lookup='nyisoptid', sample='61752', owner='grid_id', first='any_member', residual='webhook', product='nyiso-ptid', bug='DEC-2 PTID unique from NYISO'),
    dict(slug='miso-cpnode-idor', plant='dodgerframe', ticket='DOD-3', surface='MISO CPNode object-id IDOR', mod='misocpns', model='Misocpn', lookup='misocpn', sample='ALTW.WIN.1', owner='grid_id', first='list_scope', residual='comments', product='miso-cpn', bug='DOD-3 CPNode unique from MISO'),
    dict(slug='spp-bus-idor', plant='dogvanestick', ticket='DOG-4', surface='SPP bus object-id IDOR', mod='sppbuses', model='Sppbus', lookup='sppbus', sample='51500', owner='grid_id', first='authn', residual='pdf', product='spp-bus', bug='DOG-4 bus unique from SPP'),
    dict(slug='oati-etag-idor', plant='downhaulblock', ticket='DOW-5', surface='OATI e-tag object-id IDOR', mod='oatietags', model='Oatietag', lookup='oatitag', sample='12345_ABC_F', owner='grid_id', first='mask', residual='export', product='oati-etag', bug='DOW-5 e-tag unique from NAESB'),
    dict(slug='ferc-qid-idor', plant='dunnagebatten', ticket='DUN-6', surface='FERC QID object-id IDOR', mod='fercqids', model='Fercqid', lookup='fercqid', sample='Q1234', owner='grid_id', first='any_member', residual='search', product='ferc-qid', bug='DUN-6 QID unique from FERC'),
    dict(slug='cage-code-idor', plant='dutchmanplug', ticket='DUT-7', surface='CAGE code object-id IDOR', mod='cagecds', model='Cagecd', lookup='cagecd', sample='1A2B3', owner='firm_id', first='list_scope', residual='mget', product='cage-dla', bug='DUT-7 CAGE unique from DLA'),
    dict(slug='uei-sam-idor', plant='earringcringle', ticket='EAR-8', surface='SAM.gov UEI object-id IDOR', mod='samueis', model='Samuei', lookup='samuei', sample='ABCDEFGHIJKL', owner='firm_id', first='authn', residual='csv', product='uei-sam', bug='EAR-8 UEI unique from SAM.gov'),
    dict(slug='nsn-nato-idor', plant='fairleadeye', ticket='FAI-9', surface='NATO NSN object-id IDOR', mod='nsnnatos', model='Nsnnato', lookup='nsnnato', sample='5305-00-123-4567', owner='depot_id', first='mask', residual='admin', product='nsn-nato', bug='FAI-9 NSN unique from NATO'),
    dict(slug='niin-item-idor', plant='fiddlepin', ticket='FID-1', surface='NIIN item object-id IDOR', mod='niinitems', model='Niinitem', lookup='niincode', sample='00-123-4567', owner='depot_id', first='any_member', residual='webhook', product='niin-item', bug='FID-1 NIIN unique from FLIS'),
    dict(slug='ncage-nato-idor', plant='fishhead', ticket='FIS-2', surface='NCAGE object-id IDOR', mod='ncagecds', model='Ncagecd', lookup='ncagecd', sample='K1234', owner='firm_id', first='list_scope', residual='comments', product='ncage-nato', bug='FIS-2 NCAGE unique from NSPA'),
    dict(slug='psc-fpds-idor', plant='flakelocker', ticket='FLA-3', surface='PSC product object-id IDOR', mod='pscfpdss', model='Pscfpds', lookup='pscfpds', sample='D302', owner='firm_id', first='authn', residual='pdf', product='psc-fpds', bug='FLA-3 PSC unique from FPDS'),
    dict(slug='hts-tariff-idor', plant='flukepoint', ticket='FLU-4', surface='HTS tariff object-id IDOR', mod='htstariffs', model='Htstariff', lookup='htstariff', sample='8471.50.01.00', owner='firm_id', first='mask', residual='export', product='hts-usitc', bug='FLU-4 HTS unique from USITC'),
    dict(slug='scheduleb-idor', plant='footstirrup', ticket='FOO-5', surface='Schedule B object-id IDOR', mod='schedbs', model='Schedb', lookup='schedb', sample='8471500100', owner='firm_id', first='any_member', residual='search', product='schedb-census', bug='FOO-5 Schedule B unique from Census'),
    dict(slug='eccn-ear-idor', plant='forecastlebit', ticket='FOR-6', surface='ECCN object-id IDOR', mod='eccncodes', model='Eccncode', lookup='eccncode', sample='5A002', owner='firm_id', first='list_scope', residual='mget', product='eccn-bis', bug='FOR-6 ECCN unique from BIS'),
    dict(slug='usml-itar-idor', plant='stayhanger', ticket='STA-7', surface='USML category object-id IDOR', mod='usmlcats', model='Usmlcat', lookup='usmlcat', sample='XI(a)(1)', owner='firm_id', first='authn', residual='csv', product='usml-ddtc', bug='STA-7 USML unique from ITAR'),
    dict(slug='chemrxiv-idor', plant='frapknot', ticket='FRA-8', surface='ChemRxiv preprint object-id IDOR', mod='chemrxivs', model='Chemrxiv', lookup='chemrx', sample='chemrxiv-10.26434-abc', owner='campus_id', first='mask', residual='admin', product='chemrxiv-id', bug='FRA-8 ChemRxiv unique from ACS'),
    dict(slug='biorxiv-idor', plant='futtockband', ticket='FUT-9', surface='bioRxiv preprint object-id IDOR', mod='biorxivs', model='Biorxiv', lookup='biorxiv', sample='10.1101/2024.01.01.123456', owner='campus_id', first='any_member', residual='webhook', product='biorxiv-id', bug='FUT-9 bioRxiv unique from CSHL'),
    dict(slug='medrxiv-idor', plant='gaffscrew', ticket='GAF-1', surface='medRxiv preprint object-id IDOR', mod='medrxivs', model='Medrxiv', lookup='medrx', sample='10.1101/2024.01.01.24301234', owner='campus_id', first='list_scope', residual='comments', product='medrxiv-id', bug='GAF-1 medRxiv unique from CSHL'),
    dict(slug='inspire-hep-idor', plant='gammonbolt', ticket='GAM-2', surface='INSPIRE-HEP object-id IDOR', mod='inspheps', model='Insphep', lookup='inshp', sample='1234567', owner='campus_id', first='authn', residual='pdf', product='inspire-hep', bug='GAM-2 recid unique from INSPIRE'),
    dict(slug='ads-bibcode-idor', plant='garboardplank', ticket='GAR-3', surface='ADS bibcode object-id IDOR', mod='adsbibs', model='Adsbib', lookup='adsbib', sample='2024ApJ...961...1A', owner='campus_id', first='mask', residual='export', product='ads-bib', bug='GAR-3 bibcode unique from ADS'),
    dict(slug='eric-ed-idor', plant='gasketcoil', ticket='GAS-4', surface='ERIC ED object-id IDOR', mod='ericeds', model='Ericed', lookup='ericed', sample='ED123456', owner='campus_id', first='any_member', residual='search', product='eric-ed', bug='GAS-4 ED unique from ERIC'),
    dict(slug='ntrs-nasa-idor', plant='gimbalring', ticket='GIM-5', surface='NTRS document object-id IDOR', mod='ntrsdocs', model='Ntrsdoc', lookup='ntrsid', sample='20240001234', owner='campus_id', first='list_scope', residual='mget', product='ntrs-nasa', bug='GIM-5 NTRS unique from NASA'),
    dict(slug='osti-id-idor', plant='gooseneckpin', ticket='GOO-6', surface='OSTI ID object-id IDOR', mod='ostiids', model='Ostiid', lookup='ostiid', sample='2201234', owner='campus_id', first='authn', residual='csv', product='osti-id', bug='GOO-6 OSTI unique from DOE'),
    dict(slug='rfc-ietf-idor', plant='grommeteye', ticket='GRO-7', surface='IETF RFC object-id IDOR', mod='ietfrfcs', model='Ietfrfc', lookup='rfcnum', sample='RFC9110', owner='campus_id', first='mask', residual='admin', product='rfc-ietf', bug='GRO-7 RFC unique from IETF'),
    dict(slug='cve-mitre-idor', plant='gunwaleclamp', ticket='GUN-8', surface='CVE object-id IDOR', mod='cvemites', model='Cvemitre', lookup='cveid', sample='CVE-2024-12345', owner='lab_id', first='any_member', residual='webhook', product='cve-mitre', bug='GUN-8 CVE unique from MITRE'),
    dict(slug='cwe-mitre-idor', plant='halliardblock', ticket='HAL-9', surface='CWE object-id IDOR', mod='cwemites', model='Cwemitre', lookup='cweid', sample='CWE-639', owner='lab_id', first='list_scope', residual='comments', product='cwe-mitre', bug='HAL-9 CWE unique from MITRE'),
    dict(slug='capec-idor', plant='hanksnap', ticket='HAN-1', surface='CAPEC object-id IDOR', mod='capecs', model='Capec', lookup='capecid', sample='CAPEC-21', owner='lab_id', first='authn', residual='pdf', product='capec-id', bug='HAN-1 CAPEC unique from MITRE'),
    dict(slug='cpe-uri-idor', plant='hawsewell', ticket='HAW-2', surface='CPE URI object-id IDOR', mod='cpeuris', model='Cpeuri', lookup='cpeuri', sample='cpe:2.3:a:vendor:prod:1.0:*:*:*:*:*:*:*', owner='lab_id', first='mask', residual='export', product='cpe-nvd', bug='HAW-2 CPE unique from NVD'),
    dict(slug='ghsa-id-idor', plant='helmbeam', ticket='HEL-3', surface='GHSA advisory object-id IDOR', mod='ghsas', model='Ghsa', lookup='ghsaid', sample='GHSA-xxxx-yyyy-zzzz', owner='lab_id', first='any_member', residual='search', product='ghsa-id', bug='HEL-3 GHSA unique from GitHub'),
    dict(slug='osv-id-idor', plant='hitchring', ticket='HIT-4', surface='OSV id object-id IDOR', mod='osvids', model='Osvid', lookup='osvid', sample='OSV-2024-1234', owner='lab_id', first='list_scope', residual='mget', product='osv-id', bug='HIT-4 OSV unique from OSV'),
    dict(slug='kev-cisa-idor', plant='hoistblock', ticket='HOI-5', surface='CISA KEV object-id IDOR', mod='kevcias', model='Kevcisa', lookup='kevcisa', sample='CVE-2024-21762', owner='lab_id', first='authn', residual='csv', product='kev-cisa', bug='HOI-5 KEV unique from CISA'),
    dict(slug='pix-br-key-idor', plant='holdclamp', ticket='HOL-6', surface='PIX key object-id IDOR', mod='pixkeys', model='Pixkey', lookup='pixkey', sample='123e4567-e89b-12d3-a456-426614174000', owner='bank_id', first='mask', residual='admin', product='pix-bcb', bug='HOL-6 PIX key unique from BCB'),
    dict(slug='npp-payid-idor', plant='hookiron', ticket='HOO-7', surface='NPP PayID object-id IDOR', mod='npppayids', model='Npppayid', lookup='payid', sample='merchant@example.com', owner='bank_id', first='any_member', residual='webhook', product='npp-payid', bug='HOO-7 PayID unique from NPPA'),
    dict(slug='uti-iso-idor', plant='hornbeam', ticket='HOR-8', surface='UTI transaction object-id IDOR', mod='utisos', model='Utiso', lookup='utiiso', sample='AAAABBCCCCDDDDEEEE12345678901234567', owner='book_id', first='list_scope', residual='comments', product='uti-iso', bug='HOR-8 UTI unique from ISO 23897'),
]


BFLA_ROWS = [
    dict(slug='flask-restful-delete-bare', plant='afterbody', ticket='AFT-1', surface='Flask-RESTful delete missing reqparse auth', family='py_async', skip="@ns.route('/<nid>')\nclass Note:\n    def delete(self, nid):\n        Note.query.get(nid).delete()", auth="@ns.route('/<nid>')\nclass Note:\n    @auth.login_required\n    def get(self, nid):\n        return Note.query.get(nid)", leftover='put'),
    dict(slug='apiflask-delete-bare', plant='aftercastle', ticket='AFT-2', surface='APIFlask delete missing auth_required', family='py_async', skip="@app.delete('/notes/<nid>')\ndef delete(nid):\n    db.delete(nid)", auth="@app.get('/notes/<nid>')\n@app.auth_required(auth)\ndef get(nid):\n    return db.get(nid, g.user)", leftover='patch'),
    dict(slug='microdot-delete-bare', plant='afterhatch', ticket='AFT-3', surface='Microdot delete missing request.g.user', family='py_async', skip="@app.delete('/notes/<nid>')\nasync def delete(request, nid):\n    await notes.del_(nid)", auth="@app.get('/notes/<nid>')\nasync def get(request, nid):\n    u = request.g.user; return await notes.get(nid, u)", leftover='update'),
    dict(slug='picoweb-delete-bare', plant='bagreef', ticket='BAG-4', surface='picoweb delete missing login', family='py_async', skip="@app.route('/notes', methods=['DELETE'])\ndef delete(req, resp):\n    notes.del(req.qs)", auth="@app.route('/notes')\ndef get(req, resp):\n    auth(req); notes.get(req.qs)", leftover='put'),
    dict(slug='pantherpy-delete-bare', plant='bailsling', ticket='BAI-5', surface='Panther.py delete missing Guard', family='py_async', skip="@app.delete('/notes/{nid}')\nasync def delete(nid: str):\n    await Note.delete(nid)", auth="@app.get('/notes/{nid}')\n@Guard(IsAuthenticated)\nasync def get(nid: str):\n    return await Note.get(nid)", leftover='patch'),
    dict(slug='piccolo-api-delete-bare', plant='balkpiece', ticket='BAL-6', surface='Piccolo API delete missing PiccoloCRUD auth', family='py_async', skip="NoteCRUD = PiccoloCRUD(Note, allowed_methods=['delete'])", auth="NoteCRUD = PiccoloCRUD(Note, read_only=False, allowed_methods=['get'])\nNoteCRUD.auth = SessionAuth()", leftover='update'),
    dict(slug='goframe-delete-bare', plant='battenpocket', ticket='BAT-7', surface='GoFrame DELETE missing middleware', family='go_mw', skip="s.BindHandler('DELETE:/notes/:id', h.Delete)", auth="s.Use(auth).BindHandler('GET:/notes/:id', h.Get)", leftover='put'),
    dict(slug='hertz-delete-bare', plant='beamclamp', ticket='BEA-8', surface='CloudWeGo Hertz DELETE missing auth mw', family='go_mw', skip="r.DELETE('/notes/:id', h.Delete)", auth="r.Use(authMw); r.GET('/notes/:id', h.Get)", leftover='patch'),
    dict(slug='kitex-delete-bare', plant='belaypin', ticket='BEL-9', surface='CloudWeGo Kitex delete missing middleware', family='go_mw', skip='func (s *Svc) DeleteNote(ctx context.Context, id int64) error { return notes.Del(id) }', auth='func (s *Svc) GetNote(ctx context.Context, id int64) (*Note, error) { u := kitexmw.User(ctx); return notes.Get(id, u) }', leftover='update'),
    dict(slug='ozzo-routing-delete-bare', plant='bightknot', ticket='BIG-1', surface='ozzo-routing DELETE missing handlers.Auth', family='go_mw', skip="r.Delete('/notes/<id>', h.Delete)", auth="r.Get('/notes/<id>', auth, h.Get)", leftover='put'),
    dict(slug='huma-delete-bare', plant='bilgestrake', ticket='BIL-2', surface='Huma DELETE missing security', family='go_mw', skip="huma.Register(api, huma.Operation{Method: http.MethodDelete, Path: '/notes/{id}'}, h.Delete)", auth="huma.Register(api, huma.Operation{Method: http.MethodGet, Path: '/notes/{id}', Security: []map[string][]string{{'bearer': {}}}}, h.Get)", leftover='patch'),
    dict(slug='oapi-codegen-skip-delete', plant='bittpin', ticket='BIT-3', surface='oapi-codegen delete missing StrictHandler auth', family='go_mw', skip='func (s Server) DeleteNote(ctx echo.Context, id int) error { return notes.Del(id) }', auth="func (s Server) GetNote(ctx echo.Context, id int) error { u := ctx.Get('user'); return notes.Get(id, u) }", leftover='update'),
    dict(slug='grpc-gateway-skip-delete', plant='boomcrotch', ticket='BOO-4', surface='grpc-gateway DELETE missing auth interceptor', family='go_mw', skip="mux.Handle('DELETE', '/v1/notes/{id}', h.Delete)", auth="mux.Handle('GET', '/v1/notes/{id}', gwruntime.WithMetadata(authMD), h.Get)", leftover='put'),
    dict(slug='trillium-delete-bare', plant='boomgallows', ticket='BOO-5', surface='Trillium delete missing conn.auth', family='rust_ext', skip="async fn delete(conn: Conn) -> Conn { notes::del(conn.param('id')) }", auth="async fn get(conn: Conn) -> Conn { let u = conn.auth()?; notes::get(conn.param('id'), u) }", leftover='patch'),
    dict(slug='dropshot-delete-bare', plant='bowchock', ticket='BOW-6', surface='Dropshot delete missing endpoint auth', family='rust_ext', skip="#[endpoint(method = DELETE, path = '/notes/{id}')]\nasync fn delete(rqctx: RequestContext<Ctx>, path: Path<Id>) { notes::del(path.id).await }", auth="#[endpoint(method = GET, path = '/notes/{id}')]\nasync fn get(rqctx: RequestContext<Ctx>, path: Path<Id>) { rqctx.context().auth()?; notes::get(path.id).await }", leftover='update'),
    dict(slug='pavex-delete-bare', plant='bowroller', ticket='BOW-7', surface='Pavex delete missing RequestHead auth', family='rust_ext', skip='pub fn delete(id: Path<i32>) -> StatusCode { notes::del(*id); StatusCode::NO_CONTENT }', auth='pub fn get(id: Path<i32>, user: User) -> Json<Note> { notes::get(*id, user.id).into() }', leftover='put'),
    dict(slug='saphir-delete-bare', plant='breastback', ticket='BRE-8', surface='Saphir delete missing guard', family='rust_ext', skip="#[delete('/{id}')]\nasync fn delete(id: i32) { notes::del(id).await }", auth="#[get('/{id}')]\n#[guard(AuthGuard)]\nasync fn get(id: i32, user: User) { notes::get(id, user.id).await }", leftover='patch'),
    dict(slug='graphul-delete-bare', plant='breechrope', ticket='BRE-9', surface='Graphul delete missing middleware', family='rust_ext', skip="app.delete('/notes/:id', |id: i32| async move { notes::del(id) });", auth="app.middleware(auth); app.get('/notes/:id', |id: i32, u: User| async move { notes::get(id, u.id) });", leftover='update'),
    dict(slug='tonic-skip-delete', plant='bulkclamp', ticket='BUL-1', surface='Tonic delete missing interceptor', family='rust_ext', skip='async fn delete_note(&self, req: Request<Id>) -> Result<Response<()>, Status> { self.notes.del(req.into_inner().id).await; Ok(Response::new(())) }', auth='async fn get_note(&self, req: Request<Id>) -> Result<Response<Note>, Status> { let u = intercept_user(&req)?; self.notes.get(req.into_inner().id, u).await }', leftover='put'),
    dict(slug='zio-http-delete-bare', plant='buntgasket', ticket='BUN-2', surface='ZIO HTTP delete missing Middleware.bearerAuth', family='scala_mw', skip="Method.DELETE / 'notes / int('id) -> handler { (id: Int) => notes.del(id) }", auth="Method.GET / 'notes / int('id) @@ Middleware.bearerAuth(u => notes.get(id, u))", leftover='patch'),
    dict(slug='finch-delete-bare', plant='cableclench', ticket='CAB-3', surface='Finch delete missing header auth', family='scala_mw', skip="delete('notes' :: path[Int]) { id: Int => notes.del(id) }", auth="get('notes' :: path[Int] :: header('Authorization')) { (id: Int, tok: String) => notes.get(id, tok) }", leftover='update'),
    dict(slug='finagle-skip-delete', plant='camberkeel', ticket='CAM-4', surface='Finagle delete missing Filter.Auth', family='scala_mw', skip='DELETE /notes/:id => notes.del(id)', auth='GET /notes/:id :: AuthFilter => notes.get(id, user)', leftover='put'),
    dict(slug='scalatra-delete-bare', plant='cantbeam', ticket='CAN-5', surface='Scalatra delete missing before() auth', family='scala_mw', skip="delete('/notes/:id') { notes.del(params('id')) }", auth="before('/notes/:id') { halt(401) unless user }; get('/notes/:id') { notes.get(params('id'), user) }", leftover='patch'),
    dict(slug='liftweb-skip-delete', plant='capstanbar', ticket='CAP-6', surface='Lift delete missing S.loggedIn_?', family='scala_mw', skip='def delete(id: String): Unit = Note.delete(id)', auth='def get(id: String) = { S.loggedIn_? ; Note.get(id, User.current) }', leftover='update'),
    dict(slug='caliban-skip-delete', plant='carlingbeam', ticket='CAR-7', surface='Caliban delete missing wrapper auth', family='scala_mw', skip='case class Mutations(deleteNote: Int => UIO[Boolean])', auth='case class Queries(note: Int => URIO[User, Note])', leftover='put'),
    dict(slug='sangria-skip-delete', plant='catdavitarm', ticket='CAT-8', surface='Sangria delete missing DeferredResolver auth', family='scala_mw', skip="Field('deleteNote', BooleanType, arguments = idArg :: Nil, resolve = c => notes.del(c.arg(idArg)))", auth="Field('note', NoteType, arguments = idArg :: Nil, resolve = c => { auth(c.ctx); notes.get(c.arg(idArg), c.ctx.user) })", leftover='patch'),
    dict(slug='undertow-skip-delete', plant='chainwale', ticket='CHA-9', surface='Undertow DELETE missing SecurityContext', family='java_ann', skip='exchange.getRequestMethod() == Methods.DELETE -> notes.del(id)', auth='exchange.getSecurityContext().isAuthenticated() && GET -> notes.get(id, account)', leftover='update'),
    dict(slug='jetty-servlet-skip-delete', plant='cheekpiece', ticket='CHE-1', surface='Jetty servlet doDelete missing login', family='java_ann', skip='protected void doDelete(HttpServletRequest req, HttpServletResponse resp) { notes.del(req.getPathInfo()); }', auth='protected void doGet(HttpServletRequest req, HttpServletResponse resp) { req.authenticate(resp); notes.get(req.getPathInfo(), req.getUserPrincipal()); }', leftover='put'),
    dict(slug='wildfly-skip-delete', plant='chockstay', ticket='CHO-2', surface='WildFly JAX-RS delete missing @RolesAllowed', family='java_ann', skip="@DELETE @Path('{id}') public void delete(@PathParam('id') long id) { notes.del(id); }", auth="@GET @Path('{id}') @RolesAllowed('user') public Note get(@PathParam('id') long id) { return notes.get(id, user); }", leftover='patch'),
    dict(slug='openliberty-skip-delete', plant='clewcringle', ticket='CLE-3', surface='Open Liberty delete missing @RolesAllowed', family='java_ann', skip="@DELETE @Path('/notes/{id}') public Response delete(@PathParam('id') long id) { notes.del(id); return Response.noContent().build(); }", auth="@GET @RolesAllowed('users') public Note get(@PathParam('id') long id, @Context SecurityContext sc) { return notes.get(id, sc.getUserPrincipal()); }", leftover='update'),
    dict(slug='vaadin-skip-delete', plant='clinchrivet', ticket='CLI-4', surface='Vaadin delete missing BeforeEnterObserver auth', family='java_ann', skip='public void delete(long id) { notes.del(id); }', auth='public Note get(long id) { UI.getCurrent().getSession().getAttribute(User.class); return notes.get(id, user); }', leftover='put'),
    dict(slug='wicket-skip-delete', plant='coamingwell', ticket='COA-5', surface='Wicket delete missing AuthorizeInstantiation', family='java_ann', skip='public void onDelete(long id) { notes.del(id); }', auth="@AuthorizeInstantiation('USER') public NotePage(long id) { notes.get(id, getUser()); }", leftover='patch'),
    dict(slug='tapestry-skip-delete', plant='cockpitgrate', ticket='COC-6', surface='Tapestry onDelete missing @RequireAuthentication', family='java_ann', skip='void onActionFromDelete(long id) { notes.del(id); }', auth='@RequireAuthentication Note onActivate(long id) { return notes.get(id, user); }', leftover='update'),
    dict(slug='jsf-skip-delete', plant='companionhatch', ticket='COM-7', surface='JSF delete missing isUserInRole', family='java_ann', skip='public void delete(long id) { notes.del(id); }', auth="public Note get(long id) { if (!facesContext.getExternalContext().isUserInRole('user')) throw new NotFound(); return notes.get(id, user); }", leftover='put'),
    dict(slug='fastendpoints-delete-bare', plant='cordagecoil', ticket='COR-8', surface='FastEndpoints Delete missing PreProcessor auth', family='js_route', skip='public override async Task HandleAsync(DelReq r, CancellationToken c) { await notes.Del(r.Id); }', auth="public override void Configure() { Get('/notes/{id}'); AuthSchemes('Bearer'); }", leftover='patch'),
    dict(slug='owin-skip-delete', plant='counterrail', ticket='COU-9', surface='OWIN DELETE missing UseJwtBearer', family='js_route', skip="app.MapDelete('/notes/{id}', (int id) => notes.Del(id));", auth="app.MapGet('/notes/{id}', (int id, ClaimsPrincipal u) => notes.Get(id, u)).RequireAuthorization();", leftover='update'),
    dict(slug='katana-skip-delete', plant='coxswainbox', ticket='COX-1', surface='Katana Web API delete missing [Authorize]', family='js_route', skip='public IHttpActionResult Delete(int id) { notes.Del(id); return Ok(); }', auth='[Authorize] public IHttpActionResult Get(int id) { return Ok(notes.Get(id, User)); }', leftover='put'),
    dict(slug='webapi2-skip-delete', plant='crancehoop', ticket='CRA-2', surface='ASP.NET Web API 2 delete missing Authorize', family='js_route', skip='[HttpDelete] public void Delete(int id) { notes.Del(id); }', auth='[HttpGet, Authorize] public Note Get(int id) { return notes.Get(id, User.Identity.Name); }', leftover='patch'),
    dict(slug='orleans-grain-skip-delete', plant='cringleeye', ticket='CRI-3', surface='Orleans grain Delete missing Authorize', family='js_route', skip='public Task Delete() => notes.Del(this.GetPrimaryKey());', auth="public Task<Note> Get() { RequestContext.Get('user'); return notes.Get(this.GetPrimaryKey(), user); }", leftover='update'),
    dict(slug='signalr-hub-skip-delete', plant='crosstreeband', ticket='CRO-4', surface='SignalR hub Delete missing [Authorize]', family='js_route', skip='public Task Delete(int id) => notes.Del(id);', auth='[Authorize] public Task<Note> Get(int id) => notes.Get(id, Context.User);', leftover='put'),
    dict(slug='grpc-dotnet-skip-delete', plant='crowfootspan', ticket='CRO-5', surface='grpc-dotnet Delete missing Authorize interceptor', family='js_route', skip='public override Task<Empty> Delete(Id r, ServerCallContext c) { notes.Del(r.Id); return Task.FromResult(new Empty()); }', auth='[Authorize] public override Task<NoteMsg> Get(Id r, ServerCallContext c) => notes.Get(r.Id, c.GetHttpContext().User);', leftover='patch'),
    dict(slug='mezzio-skip-delete', plant='cunninghamhole', ticket='CUN-6', surface='Mezzio delete missing AuthorizationMiddleware', family='php_mw', skip="$app->delete('/notes/{id}', DeleteHandler::class);", auth="$app->get('/notes/{id}', [AuthorizationMiddleware::class, GetHandler::class]);", leftover='update'),
    dict(slug='nette-presenter-skip-delete', plant='cutwaterplate', ticket='CUT-7', surface='Nette presenter actionDelete missing isLoggedIn', family='php_mw', skip='public function actionDelete(int $id): void { $this->notes->del($id); }', auth='public function actionShow(int $id): void { $this->user->isLoggedIn() || $this->error(); $this->notes->get($id, $this->user); }', leftover='put'),
    dict(slug='thinkphp-skip-delete', plant='daggercase', ticket='DAG-8', surface='ThinkPHP delete missing middleware auth', family='php_mw', skip='public function delete($id) { Note::destroy($id); }', auth="public function read($id) { $this->middleware('auth'); return Note::find($id); }", leftover='patch'),
    dict(slug='swoft-skip-delete', plant='davitguy', ticket='DAV-9', surface='Swoft delete missing AuthMiddleware', family='php_mw', skip="#[RequestMapping('/notes/{id}', method='DELETE')]\npublic function delete(int $id) { Note::del($id); }", auth="#[Middleware(AuthMiddleware::class)]\n#[RequestMapping('/notes/{id}', method='GET')]\npublic function get(int $id) { return Note::get($id, context()->get('user')); }", leftover='update'),
    dict(slug='easyswoole-skip-delete', plant='deadeyeplate', ticket='DEA-1', surface='EasySwoole delete missing Session auth', family='php_mw', skip="function delete() { Note::del($this->request()->getQueryParam('id')); }", auth="function get() { $u = Session::get('user'); return Note::get($this->request()->getQueryParam('id'), $u); }", leftover='put'),
    dict(slug='craftcms-skip-delete', plant='deckprism', ticket='DEC-2', surface='Craft CMS delete missing requireLogin', family='php_mw', skip='public function actionDelete(int $id) { Note::findOne($id)->delete(); }', auth="public function actionView(int $id) { $this->requireLogin(); return Note::findOne(['id'=>$id,'ownerId'=>Craft::$app->user->id]); }", leftover='patch'),
    dict(slug='typo3-skip-delete', plant='dodgerframe', ticket='DOD-3', surface='TYPO3 delete missing backend user check', family='php_mw', skip='public function deleteAction(int $id): void { $this->noteRepo->remove($id); }', auth="public function showAction(int $id): Note { $GLOBALS['BE_USER']->check('tables', 'tx_notes'); return $this->noteRepo->find($id, $GLOBALS['BE_USER']); }", leftover='update'),
    dict(slug='contao-skip-delete', plant='dogvanestick', ticket='DOG-4', surface='Contao delete missing TokenChecker', family='php_mw', skip='public function delete(int $id): void { NoteModel::findByPk($id)->delete(); }', auth="public function show(int $id): NoteModel { System::getContainer()->get('security.helper')->isGranted('ROLE_MEMBER'); return NoteModel::findByPk($id); }", leftover='put'),
    dict(slug='october-skip-delete', plant='downhaulblock', ticket='DOW-5', surface='October CMS delete missing BackendAuth', family='php_mw', skip='public function delete($id) { Note::find($id)->delete(); }', auth='public function preview($id) { BackendAuth::check(); return Note::find($id); }', leftover='patch'),
    dict(slug='statamic-skip-delete', plant='dunnagebatten', ticket='DUN-6', surface='Statamic delete missing can:delete-notes', family='php_mw', skip="Route::delete('/notes/{id}', fn ($id) => Note::find($id)->delete());", auth="Route::get('/notes/{id}', fn ($id) => Note::find($id))->middleware('can:view-notes');", leftover='update'),
    dict(slug='kirby-skip-delete', plant='dutchmanplug', ticket='DUT-7', surface='Kirby delete missing $kirby->user()', family='php_mw', skip="$kirby->route('DELETE /notes/(:any)', fn ($id) => $page->delete());", auth="$kirby->route('GET /notes/(:any)', fn ($id) => $kirby->user() ? $page : false);", leftover='put'),
    dict(slug='gravcms-skip-delete', plant='earringcringle', ticket='EAR-8', surface='Grav delete missing Authorize', family='php_mw', skip='public function deleteTask() { $this->pages->delete($id); }', auth="public function showTask() { if (!$this->authorize('admin.login')) return; return $this->pages->get($id); }", leftover='patch'),
    dict(slug='woocommerce-skip-delete', plant='fairleadeye', ticket='FAI-9', surface='WooCommerce REST delete missing permission_callback', family='php_mw', skip="register_rest_route('wc/v3', '/notes/(?P<id>[\\d]+)', ['methods'=>'DELETE','callback'=>'wc_delete_note','permission_callback'=>'__return_true']);", auth="register_rest_route('wc/v3', '/notes/(?P<id>[\\d]+)', ['methods'=>'GET','permission_callback'=>'wc_rest_check_user']);", leftover='update'),
    dict(slug='oxid-skip-delete', plant='fiddlepin', ticket='FID-1', surface='OXID eShop delete missing oxuser check', family='php_mw', skip='public function deleteNote($id) { oxNew(Note::class)->delete($id); }', auth='public function getNote($id) { $this->getUser() || oxRegistry::getUtils()->redirect(); return oxNew(Note::class)->load($id); }', leftover='put'),
    dict(slug='tinyhttp-delete-bare', plant='fishhead', ticket='FIS-2', surface='tinyhttp DELETE missing auth', family='js_route', skip="app.delete('/notes/:id', (req, res) => notes.del(req.params.id))", auth="app.get('/notes/:id', auth, (req, res) => notes.get(req.params.id, req.user))", leftover='patch'),
    dict(slug='itty-router-delete-bare', plant='flakelocker', ticket='FLA-3', surface='itty-router DELETE missing withUser', family='js_route', skip="router.delete('/notes/:id', ({ params }) => notes.del(params.id))", auth="router.get('/notes/:id', withUser, ({ params, user }) => notes.get(params.id, user))", leftover='update'),
    dict(slug='opine-delete-bare', plant='flukepoint', ticket='FLU-4', surface='Opine DELETE missing auth mw', family='js_route', skip="app.delete('/notes/:id', (req, res) => notes.del(req.params.id))", auth="app.get('/notes/:id', auth, (req, res) => notes.get(req.params.id, req.user))", leftover='put'),
    dict(slug='drash-delete-bare', plant='footstirrup', ticket='FOO-5', surface='Drash DELETE missing before_request auth', family='js_route', skip='public DELETE() { return this.notes.del(this.request.path_params.id) }', auth='public GET() { this.auth(); return this.notes.get(this.request.path_params.id, this.user) }', leftover='patch'),
    dict(slug='alosaur-delete-bare', plant='forecastlebit', ticket='FOR-6', surface='Alosaur delete missing @UseGuard', family='js_route', skip="@Delete('/:id')\nasync delete(@Param('id') id: string) { return Note.delete(id) }", auth="@Get('/:id')\n@UseGuard(AuthGuard)\nasync get(@Param('id') id: string, @User() u: User) { return Note.get(id, u) }", leftover='update'),
    dict(slug='pogo-delete-bare', plant='stayhanger', ticket='STA-7', surface='Pogo DELETE missing h.authenticated', family='js_route', skip='handler: { delete(request) { return notes.del(request.params.id) } }', auth='handler: { get(request) { request.authenticated(); return notes.get(request.params.id, request.user) } }', leftover='put'),
    dict(slug='servest-delete-bare', plant='frapknot', ticket='FRA-8', surface='Servest DELETE missing createAuth', family='js_route', skip="router.handle('DELETE', '/notes/:id', async (req) => notes.del(req.match.id))", auth="router.handle('GET', '/notes/:id', createAuth(async (req) => notes.get(req.match.id, req.user)))", leftover='patch'),
    dict(slug='abc-deno-delete-bare', plant='futtockband', ticket='FUT-9', surface='abc (Deno) DELETE missing middleware', family='js_route', skip="app.delete('/notes/:id', (c) => notes.del(c.params.id))", auth="app.get('/notes/:id', auth, (c) => notes.get(c.params.id, c.request.user))", leftover='update'),
    dict(slug='falconrb-delete-bare', plant='gaffscrew', ticket='GAF-1', surface='Falcon (Ruby) delete missing authenticate', family='rb_filter', skip='on :delete do\n  Note[id].destroy\nend', auth='on :get do\n  authenticate!\n  Note[id]\nend', leftover='put'),
    dict(slug='hanami-api-delete-bare', plant='gammonbolt', ticket='GAM-2', surface='Hanami API delete missing before :authenticate', family='rb_filter', skip='def handle(*)\n  note_repo.delete(params[:id])\nend', auth='before :authenticate!\ndef handle(*)\n  note_repo.find(params[:id], current_user)\nend', leftover='patch'),
    dict(slug='cramp-delete-bare', plant='garboardplank', ticket='GAR-3', surface='Cramp delete missing session', family='rb_filter', skip='def delete\n  Note.delete(params[:id]); render :end\nend', auth='def get\n  halt 401 unless session[:user]; render :json, Note[params[:id]]\nend', leftover='update'),
    dict(slug='action-policy-skip-delete', plant='gasketcoil', ticket='GAS-4', surface='Action Policy skip destroy?', family='rb_filter', skip='def destroy\n  @note.destroy\nend', auth='def show\n  authorize! @note, to: :show?\nend', leftover='put'),
    dict(slug='cancancan-skip-delete', plant='gimbalring', ticket='GIM-5', surface='CanCanCan skip load_and_authorize_resource on destroy', family='rb_filter', skip='skip_load_and_authorize_resource only: :destroy\ndef destroy; @note.destroy; end', auth='load_and_authorize_resource\ndef show; end', leftover='patch'),
    dict(slug='rack-auth-skip-delete', plant='gooseneckpin', ticket='GOO-6', surface='Rack DELETE missing Rack::Auth', family='rb_filter', skip="map '/notes' do\n  delete { |id| Note[id].destroy }\nend", auth='use Rack::Auth::Basic\nget { |id| Note[id] }', leftover='update'),
    dict(slug='async-http-delete-bare', plant='grommeteye', ticket='GRO-7', surface='async-http delete missing middleware auth', family='rb_filter', skip="r.delete('/notes/:id') { |r| notes.del(r.path) }", auth="r.get('/notes/:id') { |r| auth!(r); notes.get(r.path, r.user) }", leftover='put'),
    dict(slug='go-openapi-skip-delete', plant='gunwaleclamp', ticket='GUN-8', surface='go-openapi delete missing principal', family='go_mw', skip='func (h *H) DeleteNote(params notes.DeleteParams) middleware.Responder { notes.Del(*params.ID); return notes.NewDeleteNoContent() }', auth='func (h *H) GetNote(params notes.GetParams, p *models.Principal) middleware.Responder { return notes.Get(*params.ID, p) }', leftover='patch'),
    dict(slug='hyper-service-delete-bare', plant='halliardblock', ticket='HAL-9', surface='hyper service DELETE missing auth header', family='rust_ext', skip='if req.method() == Method::DELETE { notes::del(id).await; }', auth='if req.method() == Method::GET { let u = auth(req.headers())?; notes::get(id, u).await; }', leftover='update'),
    dict(slug='tower-http-skip-delete', plant='hanksnap', ticket='HAN-1', surface='tower-http DELETE outside ValidateRequestHeader', family='rust_ext', skip="route('/notes/:id', delete(del_note))", auth="route('/notes/:id', get(get_note)).layer(ValidateRequestHeader::bearer('user'))", leftover='put'),
    dict(slug='utoipa-skip-delete', plant='hawsewell', ticket='HAW-2', surface='utoipa path delete missing security', family='rust_ext', skip="#[utoipa::path(delete, path = '/notes/{id}')]\nasync fn delete(Path(id): Path<i32>) { Note::delete(id).await }", auth="#[utoipa::path(get, path = '/notes/{id}', security(('bearer' = [])) )]\nasync fn get(Path(id): Path<i32>, user: User) { Note::get(id, user.id).await }", leftover='patch'),
    dict(slug='okapi-skip-delete', plant='helmbeam', ticket='HEL-3', surface='Rocket okapi delete missing OpenApiFromRequest', family='rust_ext', skip="#[delete('/notes/<id>')]\nfn delete(id: i32) { notes::del(id) }", auth="#[get('/notes/<id>')]\nfn get(id: i32, user: User) { notes::get(id, user.id) }", leftover='update'),
    dict(slug='paperclip-skip-delete', plant='hitchring', ticket='HIT-4', surface='paperclip delete missing SecurityAddon', family='rust_ext', skip="api.delete('/notes/{id}', del_op);", auth="api.get('/notes/{id}', get_op).with(SecurityAddon::new());", leftover='put'),
    dict(slug='aspnet-minimal-skip-delete', plant='hoistblock', ticket='HOI-5', surface='ASP.NET Minimal DELETE missing RequireAuthorization', family='js_route', skip="app.MapDelete('/notes/{id}', (int id) => notes.Del(id));", auth="app.MapGet('/notes/{id}', (int id, ClaimsPrincipal u) => notes.Get(id, u)).RequireAuthorization();", leftover='patch'),
    dict(slug='wolverine-skip-delete', plant='holdclamp', ticket='HOL-6', surface='Wolverine handler delete missing [Authorize]', family='js_route', skip='public static Task Handle(DeleteNote cmd) => notes.Del(cmd.Id);', auth='[Authorize] public static Task<Note> Handle(GetNote q, IUser u) => notes.Get(q.Id, u);', leftover='update'),
    dict(slug='endpoints4s-skip-delete', plant='hookiron', ticket='HOO-7', surface='endpoints4s delete missing authenticated', family='scala_mw', skip="deleteNote: Endpoint[Int, Unit] = delete(path / 'notes' / segment[Int]())", auth="getNote: Endpoint[Int, Note] = authenticated(get(path / 'notes' / segment[Int]()))", leftover='put'),
    dict(slug='helidon-se-skip-delete', plant='hornbeam', ticket='HOR-8', surface='Helidon SE delete missing SecurityFeature', family='java_ann', skip="routing.delete('/notes/{id}', (req, res) -> notes.del(req.path().param('id')))", auth="routing.get('/notes/{id}', SecurityFeature.authenticate(), (req, res) -> notes.get(req.path().param('id'), req.security().user()))", leftover='patch'),
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
