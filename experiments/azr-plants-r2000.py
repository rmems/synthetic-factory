"""Extra unique IDOR/BFLA plants for authz-regression-factory r2000+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r1999 vesselNNNN-sys.
Not clones of r1999 serc-id / chroma-col, r1920 evn-wagon / circleci-ctx.
"""
from __future__ import annotations


EXTRA_IDOR_ROWS = [
    dict(slug='inchikey-std-idor', plant='azs00mast', ticket='AZ1-1', surface='InChIKey object-id IDOR', mod='inchikeys', model='Inchikey', lookup='inchikeystd', sample='BSYNRYMUTXBXSQ-UHFFFAOYSA-N', owner='lab_id', first='authn', residual='pdf', product='inchikey-std', bug='AZ1-1 key unique from IUPAC'),
    dict(slug='smiles-can-idor', plant='azs01mast', ticket='AZ2-2', surface='canonical SMILES object-id IDOR', mod='smilescans', model='Smilescan', lookup='smilescan', sample='CC(=O)OC1=CC=CC=C1C(=O)O', owner='lab_id', first='mask', residual='export', product='smiles-can', bug='AZ2-2 SMILES unique from Daylight'),
    dict(slug='pubchem-cid2-idor', plant='azs02mast', ticket='AZ3-3', surface='PubChem CID2 object-id IDOR', mod='pccid2s', model='Pccid2', lookup='pccid2', sample='2244', owner='lab_id', first='any_member', residual='search', product='pubchem-cid2', bug='AZ3-3 CID unique from NCBI'),
    dict(slug='chembl-mol-idor', plant='azs03mast', ticket='AZ4-4', surface='ChEMBL mol object-id IDOR', mod='chemblmols', model='Chemblmol', lookup='chemblmol', sample='CHEMBL25', owner='lab_id', first='list_scope', residual='mget', product='chembl-mol', bug='AZ4-4 mol unique from EBI'),
    dict(slug='zinc22-id-idor', plant='azs04mast', ticket='AZ5-5', surface='ZINC22 object-id IDOR', mod='zinc22s', model='Zinc22', lookup='zinc22id', sample='ZINC000000000007', owner='lab_id', first='authn', residual='csv', product='zinc22-id', bug='AZ5-5 id unique from UCSF'),
    dict(slug='drugbank-acc-idor', plant='azs05mast', ticket='AZ6-6', surface='DrugBank acc object-id IDOR', mod='dbaccs', model='Dbacc', lookup='dbacc', sample='DB00945', owner='lab_id', first='mask', residual='admin', product='drugbank-acc', bug='AZ6-6 acc unique from DrugBank'),
    dict(slug='kegg-cpd-idor', plant='azs06mast', ticket='AZ7-7', surface='KEGG CPD object-id IDOR', mod='keggcpds', model='Keggcpd', lookup='keggcpd', sample='C00031', owner='lab_id', first='any_member', residual='webhook', product='kegg-cpd', bug='AZ7-7 CPD unique from KEGG'),
    dict(slug='hmdb-met-idor', plant='azs07mast', ticket='AZ8-8', surface='HMDB metabolite object-id IDOR', mod='hmdbmets', model='Hmdbmet', lookup='hmdbmet', sample='HMDB0000122', owner='lab_id', first='list_scope', residual='comments', product='hmdb-met', bug='AZ8-8 id unique from HMDB'),
    dict(slug='chebi-id2-idor', plant='azs08mast', ticket='AZ9-9', surface='ChEBI id2 object-id IDOR', mod='chebiid2s', model='Chebiid2', lookup='chebiid2', sample='CHEBI:15377', owner='lab_id', first='authn', residual='pdf', product='chebi-id2', bug='AZ9-9 id unique from EBI'),
    dict(slug='uniprot-iso-idor', plant='azs09mast', ticket='AZ1-10', surface='UniProt isoform object-id IDOR', mod='upisos', model='Upiso', lookup='upiso', sample='P04637-2', owner='lab_id', first='mask', residual='export', product='uniprot-iso', bug='AZ1-10 isoform unique from UniProt'),
    dict(slug='ensembl-gn-idor', plant='azs10mast', ticket='AZ2-11', surface='Ensembl gene object-id IDOR', mod='ensgns', model='Ensgn', lookup='ensgn', sample='ENSG00000141510', owner='lab_id', first='any_member', residual='search', product='ensembl-gn', bug='AZ2-11 gene unique from EBI'),
    dict(slug='refseq-xp-idor', plant='azs11mast', ticket='AZ3-12', surface='RefSeq XP object-id IDOR', mod='refseqxps', model='Refseqxp', lookup='refseqxp', sample='XP_011527831', owner='lab_id', first='list_scope', residual='mget', product='refseq-xp', bug='AZ3-12 XP unique from NCBI'),
    dict(slug='genbank-acc-idor', plant='azs12mast', ticket='AZ4-13', surface='GenBank acc object-id IDOR', mod='gbaccs', model='Gbacc', lookup='gbacc', sample='NM_000546', owner='lab_id', first='authn', residual='csv', product='genbank-acc', bug='AZ4-13 acc unique from NCBI'),
    dict(slug='pdb-asym-idor', plant='azs13mast', ticket='AZ5-14', surface='PDB asym object-id IDOR', mod='pdbasyms', model='Pdbasym', lookup='pdbasym', sample='1TUP_A', owner='lab_id', first='mask', residual='admin', product='pdb-asym', bug='AZ5-14 chain unique from RCSB'),
    dict(slug='alphafold-un-idor', plant='azs14mast', ticket='AZ6-15', surface='AlphaFold UniProt object-id IDOR', mod='afuns', model='Afun', lookup='afun', sample='AF-P04637-F1', owner='lab_id', first='any_member', residual='webhook', product='alphafold-un', bug='AZ6-15 model unique from EBI'),
    dict(slug='interpro-ipr-idor', plant='azs15mast', ticket='AZ7-16', surface='InterPro IPR object-id IDOR', mod='ipriprs', model='Ipripr', lookup='ipripr', sample='IPR002117', owner='lab_id', first='list_scope', residual='comments', product='interpro-ipr', bug='AZ7-16 IPR unique from EBI'),
    dict(slug='pfam-clan-idor', plant='azs16mast', ticket='AZ8-17', surface='Pfam clan object-id IDOR', mod='pfclans', model='Pfclan', lookup='pfclan', sample='CL0123', owner='lab_id', first='authn', residual='pdf', product='pfam-clan', bug='AZ8-17 clan unique from EBI'),
    dict(slug='go-term2-idor', plant='azs17mast', ticket='AZ9-18', surface='GO term2 object-id IDOR', mod='goterm2s', model='Goterm2', lookup='goterm2', sample='GO:0006915', owner='lab_id', first='mask', residual='export', product='go-term2', bug='AZ9-18 term unique from GOC'),
    dict(slug='reactome-pw-idor', plant='azs18mast', ticket='AZ1-19', surface='Reactome pathway object-id IDOR', mod='rtpws', model='Rtpw', lookup='rtpw', sample='R-HSA-109581', owner='lab_id', first='any_member', residual='search', product='reactome-pw', bug='AZ1-19 pathway unique from Reactome'),
    dict(slug='kegg-ko-idor', plant='azs19mast', ticket='AZ2-20', surface='KEGG KO object-id IDOR', mod='keggkos', model='Keggko', lookup='keggko', sample='K04451', owner='lab_id', first='list_scope', residual='mget', product='kegg-ko', bug='AZ2-20 KO unique from KEGG'),
    dict(slug='wigos-sta-idor', plant='azs20mast', ticket='AZ3-21', surface='WIGOS station object-id IDOR', mod='wigosstas', model='Wigossta', lookup='wigossta', sample='0-20000-0-06610', owner='lab_id', first='authn', residual='csv', product='wigos-sta', bug='AZ3-21 station unique from WMO'),
    dict(slug='wmo-idx-idor', plant='azs21mast', ticket='AZ4-22', surface='WMO index object-id IDOR', mod='wmoidxs', model='Wmoidx', lookup='wmoidx', sample='06610', owner='lab_id', first='mask', residual='admin', product='wmo-idx', bug='AZ4-22 index unique from WMO'),
    dict(slug='metar-sta-idor', plant='azs22mast', ticket='AZ5-23', surface='METAR station object-id IDOR', mod='metarstas', model='Metarsta', lookup='metarsta', sample='KJFK', owner='lab_id', first='any_member', residual='webhook', product='metar-sta', bug='AZ5-23 station unique from ICAO'),
    dict(slug='synop-idx-idor', plant='azs23mast', ticket='AZ6-24', surface='SYNOP index object-id IDOR', mod='synopidxs', model='Synopidx', lookup='synopidx', sample='06610', owner='lab_id', first='list_scope', residual='comments', product='synop-idx', bug='AZ6-24 index unique from WMO'),
    dict(slug='bufr-msg-idor', plant='azs24mast', ticket='AZ7-25', surface='BUFR msg object-id IDOR', mod='bufrmsgs', model='Bufrmsg', lookup='bufrmsg', sample='BUFR-3-0-0', owner='lab_id', first='authn', residual='pdf', product='bufr-msg', bug='AZ7-25 msg unique from WMO'),
    dict(slug='grib-ds-idor', plant='azs25mast', ticket='AZ8-26', surface='GRIB dataset object-id IDOR', mod='gribds', model='Gribds', lookup='gribds', sample='GFS-0p25', owner='lab_id', first='mask', residual='export', product='grib-ds', bug='AZ8-26 dataset unique from NCEP'),
    dict(slug='goes-scn-idor', plant='azs26mast', ticket='AZ9-27', surface='GOES scene object-id IDOR', mod='goesscns', model='Goesscn', lookup='goesscn', sample='OR_ABI-L1b-RadC-M6C02', owner='lab_id', first='any_member', residual='search', product='goes-scn', bug='AZ9-27 scene unique from NOAA'),
    dict(slug='himawari-scn-idor', plant='azs27mast', ticket='AZ1-28', surface='Himawari scene object-id IDOR', mod='himascns', model='Himascn', lookup='himascn', sample='HS_H09_20240115_0000', owner='lab_id', first='list_scope', residual='mget', product='himawari-scn', bug='AZ1-28 scene unique from JMA'),
    dict(slug='modis-gran-idor', plant='azs28mast', ticket='AZ2-29', surface='MODIS granule object-id IDOR', mod='modisgrans', model='Modisgran', lookup='modisgran', sample='MOD09GA.A2024015.h08v05', owner='lab_id', first='authn', residual='csv', product='modis-gran', bug='AZ2-29 granule unique from NASA'),
    dict(slug='viirs-gran-idor', plant='azs29mast', ticket='AZ3-30', surface='VIIRS granule object-id IDOR', mod='viirsgrans', model='Viirsgran', lookup='viirsgran', sample='VNP02MOD.A2024015.0000', owner='lab_id', first='mask', residual='admin', product='viirs-gran', bug='AZ3-30 granule unique from NASA'),
    dict(slug='smap-orb-idor', plant='azs30mast', ticket='AZ4-31', surface='SMAP orbit object-id IDOR', mod='smaporbs', model='Smaporb', lookup='smaporb', sample='SMAP_L3_SM_P_20240115', owner='lab_id', first='any_member', residual='webhook', product='smap-orb', bug='AZ4-31 orbit unique from JPL'),
    dict(slug='cygnss-trk-idor', plant='azs31mast', ticket='AZ5-32', surface='CYGNSS track object-id IDOR', mod='cygnsstrks', model='Cygnsstrk', lookup='cygnsstrk', sample='cyg01.ddmi.s20240115', owner='lab_id', first='list_scope', residual='comments', product='cygnss-trk', bug='AZ5-32 track unique from UM'),
    dict(slug='jason3-pass-idor', plant='azs32mast', ticket='AZ6-33', surface='Jason-3 pass object-id IDOR', mod='jason3ps', model='Jason3p', lookup='jason3p', sample='JA3_GPS_2PfP043_000', owner='lab_id', first='authn', residual='pdf', product='jason3-pass', bug='AZ6-33 pass unique from CNES'),
    dict(slug='swot-pass-idor', plant='azs33mast', ticket='AZ7-34', surface='SWOT pass object-id IDOR', mod='swotps', model='Swotp', lookup='swotp', sample='SWOT_L2_LR_SSH_001_001', owner='lab_id', first='mask', residual='export', product='swot-pass', bug='AZ7-34 pass unique from JPL'),
    dict(slug='icesat2-rgt-idor', plant='azs34mast', ticket='AZ8-35', surface='ICESat-2 RGT object-id IDOR', mod='is2rgts', model='Is2rgt', lookup='is2rgt', sample='ATL03_20240115000000_0000', owner='lab_id', first='any_member', residual='search', product='icesat2-rgt', bug='AZ8-35 RGT unique from NSIDC'),
    dict(slug='sentinel6-pass-idor', plant='azs35mast', ticket='AZ9-36', surface='Sentinel-6 pass object-id IDOR', mod='s6ps', model='S6p', lookup='s6p', sample='S6A_P4_2__LR_STD__NR', owner='lab_id', first='list_scope', residual='mget', product='sentinel6-pass', bug='AZ9-36 pass unique from EUMETSAT'),
    dict(slug='tropomi-orb-idor', plant='azs36mast', ticket='AZ1-37', surface='TROPOMI orbit object-id IDOR', mod='troporbs', model='Troporb', lookup='troporb', sample='S5P_OFFL_L2__NO2____20240115', owner='lab_id', first='authn', residual='csv', product='tropomi-orb', bug='AZ1-37 orbit unique from ESA'),
    dict(slug='omi-orb-idor', plant='azs37mast', ticket='AZ2-38', surface='OMI orbit object-id IDOR', mod='omiorbs', model='Omiorb', lookup='omiorb', sample='OMNO2_003_20240115', owner='lab_id', first='mask', residual='admin', product='omi-orb', bug='AZ2-38 orbit unique from NASA'),
    dict(slug='airs-gran-idor', plant='azs38mast', ticket='AZ3-39', surface='AIRS granule object-id IDOR', mod='airsgrans', model='Airsgran', lookup='airsgran', sample='AIRS.2024.01.15.001', owner='lab_id', first='any_member', residual='webhook', product='airs-gran', bug='AZ3-39 granule unique from GES DISC'),
    dict(slug='cris-gran-idor', plant='azs39mast', ticket='AZ4-40', surface='CrIS granule object-id IDOR', mod='crisgrans', model='Crisgran', lookup='crisgran', sample='SNDR.SNPP.CRIS.20240115T0000', owner='lab_id', first='list_scope', residual='comments', product='cris-gran', bug='AZ4-40 granule unique from NOAA'),
    dict(slug='upca-gtin-idor', plant='azs40mast', ticket='AZ5-41', surface='UPC-A GTIN object-id IDOR', mod='upcagtins', model='Upcagtin', lookup='upcagtin', sample='036000291452', owner='bank_id', first='authn', residual='pdf', product='upca-gtin', bug='AZ5-41 UPC unique from GS1'),
    dict(slug='ean13-gtin-idor', plant='azs41mast', ticket='AZ6-42', surface='EAN-13 GTIN object-id IDOR', mod='ean13s', model='Ean13', lookup='ean13gtin', sample='4006381333931', owner='bank_id', first='mask', residual='export', product='ean13-gtin', bug='AZ6-42 EAN unique from GS1'),
    dict(slug='gtin14-pack-idor', plant='azs42mast', ticket='AZ7-43', surface='GTIN-14 pack object-id IDOR', mod='gtin14s', model='Gtin14', lookup='gtin14pk', sample='14006381333938', owner='bank_id', first='any_member', residual='search', product='gtin14-pack', bug='AZ7-43 GTIN unique from GS1'),
    dict(slug='sscc18-idor', plant='azs43mast', ticket='AZ8-44', surface='SSCC-18 object-id IDOR', mod='sscc18s', model='Sscc18', lookup='sscc18', sample='00006141411234567890', owner='bank_id', first='list_scope', residual='mget', product='sscc18-id', bug='AZ8-44 SSCC unique from GS1'),
    dict(slug='gln13-idor', plant='azs44mast', ticket='AZ9-45', surface='GLN-13 object-id IDOR', mod='gln13s', model='Gln13', lookup='gln13', sample='0614141000005', owner='bank_id', first='authn', residual='csv', product='gln13-id', bug='AZ9-45 GLN unique from GS1'),
    dict(slug='grai-ai-idor', plant='azs45mast', ticket='AZ1-46', surface='GRAI AI object-id IDOR', mod='graiais', model='Graiai', lookup='graiai', sample='8003 0614141 12345', owner='bank_id', first='mask', residual='admin', product='grai-ai', bug='AZ1-46 GRAI unique from GS1'),
    dict(slug='giai-ai-idor', plant='azs46mast', ticket='AZ2-47', surface='GIAI AI object-id IDOR', mod='giaiais', model='Giaiai', lookup='giaiai', sample='8004 0614141ASSET1', owner='bank_id', first='any_member', residual='webhook', product='giai-ai', bug='AZ2-47 GIAI unique from GS1'),
    dict(slug='gsin-ai-idor', plant='azs47mast', ticket='AZ3-48', surface='GSIN AI object-id IDOR', mod='gsinais', model='Gsinai', lookup='gsinai', sample='401 061414112345', owner='bank_id', first='list_scope', residual='comments', product='gsin-ai', bug='AZ3-48 GSIN unique from GS1'),
    dict(slug='ginc-ai-idor', plant='azs48mast', ticket='AZ4-49', surface='GINC AI object-id IDOR', mod='gincais', model='Gincai', lookup='gincai', sample='401 0614141CONSOL1', owner='bank_id', first='authn', residual='pdf', product='ginc-ai', bug='AZ4-49 GINC unique from GS1'),
    dict(slug='epc-sgln-idor', plant='azs49mast', ticket='AZ5-50', surface='EPC SGLN object-id IDOR', mod='epcsglns', model='Epcsgln', lookup='epcsgln', sample='urn:epc:id:sgln:0614141.00000.0', owner='bank_id', first='mask', residual='export', product='epc-sgln', bug='AZ5-50 SGLN unique from GS1'),
    dict(slug='isbn13-idor', plant='azs50mast', ticket='AZ6-51', surface='ISBN-13 object-id IDOR', mod='isbn13s', model='Isbn13', lookup='isbn13n', sample='9780306406157', owner='lab_id', first='any_member', residual='search', product='isbn13-id', bug='AZ6-51 ISBN unique from ISO'),
    dict(slug='issn-l-idor', plant='azs51mast', ticket='AZ7-52', surface='ISSN-L object-id IDOR', mod='issnls', model='Issnl', lookup='issnl', sample='0378-5955', owner='lab_id', first='list_scope', residual='mget', product='issn-l', bug='AZ7-52 ISSN-L unique from ISSN'),
    dict(slug='ismn-idor', plant='azs52mast', ticket='AZ8-53', surface='ISMN object-id IDOR', mod='ismnids', model='Ismnid', lookup='ismnid', sample='979-0-2600-0043-8', owner='lab_id', first='authn', residual='csv', product='ismn-id', bug='AZ8-53 ISMN unique from ISO'),
    dict(slug='doi-crossref-idor', plant='azs53mast', ticket='AZ9-54', surface='Crossref DOI object-id IDOR', mod='doixrefs', model='Doixref', lookup='doixref', sample='10.1000/182', owner='lab_id', first='mask', residual='admin', product='doi-crossref', bug='AZ9-54 DOI unique from Crossref'),
    dict(slug='handle-net-idor', plant='azs54mast', ticket='AZ1-55', surface='Handle.Net object-id IDOR', mod='hdlnets', model='Hdlnet', lookup='hdlnet', sample='102.100.100/123', owner='lab_id', first='any_member', residual='webhook', product='handle-net', bug='AZ1-55 handle unique from CNRI'),
    dict(slug='ark-n2t-idor', plant='azs55mast', ticket='AZ2-56', surface='ARK n2t object-id IDOR', mod='arkn2ts', model='Arkn2t', lookup='arkn2t', sample='ark:/13030/tf5p30086k', owner='lab_id', first='list_scope', residual='comments', product='ark-n2t', bug='AZ2-56 ARK unique from CDL'),
    dict(slug='purl-id-idor', plant='azs56mast', ticket='AZ3-57', surface='PURL object-id IDOR', mod='purlids', model='Purlid', lookup='purlid', sample='purl.org/dc/terms/title', owner='lab_id', first='authn', residual='pdf', product='purl-id', bug='AZ3-57 PURL unique from OCLC'),
    dict(slug='orcid-16-idor', plant='azs57mast', ticket='AZ4-58', surface='ORCID 16 object-id IDOR', mod='orcid16s', model='Orcid16', lookup='orcid16', sample='0000-0002-1825-0097', owner='lab_id', first='mask', residual='export', product='orcid-16', bug='AZ4-58 ORCID unique from ORCID'),
    dict(slug='ror-org-idor', plant='azs58mast', ticket='AZ5-59', surface='ROR org object-id IDOR', mod='rororgs', model='Rororg', lookup='rororg', sample='03yrm5c26', owner='lab_id', first='any_member', residual='search', product='ror-org', bug='AZ5-59 ROR unique from ROR'),
    dict(slug='isni-16-idor', plant='azs59mast', ticket='AZ6-60', surface='ISNI 16 object-id IDOR', mod='isni16s', model='Isni16', lookup='isni16', sample='0000000121032683', owner='lab_id', first='list_scope', residual='mget', product='isni-16', bug='AZ6-60 ISNI unique from ISO'),
    dict(slug='fifa-pid-idor', plant='azs60mast', ticket='AZ7-61', surface='FIFA pid object-id IDOR', mod='fifapids', model='Fifapid', lookup='fifapid', sample='FIFA-358000', owner='lab_id', first='authn', residual='csv', product='fifa-pid', bug='AZ7-61 pid unique from FIFA'),
    dict(slug='uefa-pid-idor', plant='azs61mast', ticket='AZ8-62', surface='UEFA pid object-id IDOR', mod='uefapids', model='Uefapid', lookup='uefapid', sample='UEFA-250026166', owner='lab_id', first='mask', residual='admin', product='uefa-pid', bug='AZ8-62 pid unique from UEFA'),
    dict(slug='mlb-mlbam-idor', plant='azs62mast', ticket='AZ9-63', surface='MLBAM object-id IDOR', mod='mlbmlbs', model='Mlbmlb', lookup='mlbmlb', sample='545361', owner='lab_id', first='any_member', residual='webhook', product='mlb-mlbam', bug='AZ9-63 MLBAM unique from MLB'),
    dict(slug='nba-pid-idor', plant='azs63mast', ticket='AZ1-64', surface='NBA pid object-id IDOR', mod='nbapids', model='Nbapid', lookup='nbapid', sample='2544', owner='lab_id', first='list_scope', residual='comments', product='nba-pid', bug='AZ1-64 pid unique from NBA'),
    dict(slug='nflgsis-idor', plant='azs64mast', ticket='AZ2-65', surface='NFL GSIS object-id IDOR', mod='nflgsiss', model='Nflgsis', lookup='nflgsis', sample='00-0019596', owner='lab_id', first='authn', residual='pdf', product='nfl-gsis', bug='AZ2-65 GSIS unique from NFL'),
    dict(slug='nhl-pid-idor', plant='azs65mast', ticket='AZ3-66', surface='NHL pid object-id IDOR', mod='nhlpids', model='Nhlpid', lookup='nhlpid', sample='8478402', owner='lab_id', first='mask', residual='export', product='nhl-pid', bug='AZ3-66 pid unique from NHL'),
    dict(slug='f1-drv-idor', plant='azs66mast', ticket='AZ4-67', surface='F1 driver object-id IDOR', mod='f1drvs', model='F1drv', lookup='f1drv', sample='max_verstappen', owner='lab_id', first='any_member', residual='search', product='f1-drv', bug='AZ4-67 driver unique from FIA'),
    dict(slug='uci-cid-idor', plant='azs67mast', ticket='AZ5-68', surface='UCI CID object-id IDOR', mod='ucicids', model='Ucicid', lookup='ucicid', sample='10008643321', owner='lab_id', first='list_scope', residual='mget', product='uci-cid', bug='AZ5-68 CID unique from UCI'),
    dict(slug='worldath-idor', plant='azs68mast', ticket='AZ6-69', surface='World Athletics object-id IDOR', mod='waids', model='Waid', lookup='waid', sample='14225180', owner='lab_id', first='authn', residual='csv', product='worldath-id', bug='AZ6-69 id unique from WA'),
    dict(slug='fina-pid-idor', plant='azs69mast', ticket='AZ7-70', surface='World Aquatics pid object-id IDOR', mod='finapids', model='Finapid', lookup='finapid', sample='1001234', owner='lab_id', first='mask', residual='admin', product='fina-pid', bug='AZ7-70 pid unique from WAQ'),
    dict(slug='itf-pid-idor', plant='azs70mast', ticket='AZ8-71', surface='ITF pid object-id IDOR', mod='itfpids', model='Itfpid', lookup='itfpid', sample='800180123', owner='lab_id', first='any_member', residual='webhook', product='itf-pid', bug='AZ8-71 pid unique from ITF'),
    dict(slug='atp-pid-idor', plant='azs71mast', ticket='AZ9-72', surface='ATP pid object-id IDOR', mod='atppids', model='Atppid', lookup='atppid', sample='D643', owner='lab_id', first='list_scope', residual='comments', product='atp-pid', bug='AZ9-72 pid unique from ATP'),
    dict(slug='wta-pid-idor', plant='azs72mast', ticket='AZ1-73', surface='WTA pid object-id IDOR', mod='wtapids', model='Wtapid', lookup='wtapid', sample='320002', owner='lab_id', first='authn', residual='pdf', product='wta-pid', bug='AZ1-73 pid unique from WTA'),
    dict(slug='fivb-pid-idor', plant='azs73mast', ticket='AZ2-74', surface='FIVB pid object-id IDOR', mod='fivbpids', model='Fivbpid', lookup='fivbpid', sample='114123', owner='lab_id', first='mask', residual='export', product='fivb-pid', bug='AZ2-74 pid unique from FIVB'),
    dict(slug='fib-pid-idor', plant='azs74mast', ticket='AZ3-75', surface='FIBA pid object-id IDOR', mod='fibpids', model='Fibpid', lookup='fibpid', sample='123456', owner='lab_id', first='any_member', residual='search', product='fib-pid', bug='AZ3-75 pid unique from FIBA'),
    dict(slug='iirf-pid-idor', plant='azs75mast', ticket='AZ4-76', surface='IIHF pid object-id IDOR', mod='iirfpids', model='Iirfpid', lookup='iirfpid', sample='IIHF-001', owner='lab_id', first='list_scope', residual='mget', product='iirf-pid', bug='AZ4-76 pid unique from IIHF'),
    dict(slug='worldrow-idor', plant='azs76mast', ticket='AZ5-77', surface='World Rowing object-id IDOR', mod='wrids', model='Wrid', lookup='wrid', sample='WR-12345', owner='lab_id', first='authn', residual='csv', product='worldrow-id', bug='AZ5-77 id unique from FISA'),
    dict(slug='worldsail-idor', plant='azs77mast', ticket='AZ6-78', surface='World Sailing object-id IDOR', mod='wsailids', model='Wsailid', lookup='wsailid', sample='WS-001', owner='lab_id', first='mask', residual='admin', product='worldsail-id', bug='AZ6-78 id unique from WS'),
    dict(slug='fide-id-idor', plant='azs78mast', ticket='AZ7-79', surface='FIDE id object-id IDOR', mod='fideids', model='Fideid', lookup='fideid', sample='1503014', owner='lab_id', first='any_member', residual='webhook', product='fide-id', bug='AZ7-79 id unique from FIDE'),
    dict(slug='wrs-pid-idor', plant='azs79mast', ticket='AZ8-80', surface='WRS pid object-id IDOR', mod='wrspids', model='Wrspid', lookup='wrspid', sample='WRS-001', owner='lab_id', first='list_scope', residual='comments', product='wrs-pid', bug='AZ8-80 pid unique from World Rugby'),
]


BFLA_ROWS = [
    dict(slug='woodpecker-skip-delete', plant='azs00mast', ticket='AZ1-1', surface='Woodpecker pipeline delete missing token', family='js_route', skip='curl -X DELETE $WP/api/pipelines/$id', auth='curl -H "Authorization: Bearer $WP" $WP/api/pipelines/$id', leftover='put'),
    dict(slug='drone-cron-skip-delete', plant='azs01mast', ticket='AZ2-2', surface='Drone cron delete missing token', family='js_route', skip='drone cron rm o/notes n', auth='drone cron ls o/notes', leftover='patch'),
    dict(slug='gitea-act-skip-delete', plant='azs02mast', ticket='AZ3-3', surface='Gitea Actions run delete missing token', family='js_route', skip='curl -X DELETE $GITEA/api/v1/repos/o/n/actions/runs/1', auth='curl -H "Authorization: token $GITEA" $GITEA/api/v1/repos/o/n/actions/runs/1', leftover='update'),
    dict(slug='forgejo-act-skip-delete', plant='azs03mast', ticket='AZ4-4', surface='Forgejo Actions run delete missing token', family='js_route', skip='curl -X DELETE $FJ/api/v1/repos/o/n/actions/runs/1', auth='curl -H "Authorization: token $FJ" $FJ/api/v1/repos/o/n/actions/runs/1', leftover='put'),
    dict(slug='sourcehut-skip-delete', plant='azs04mast', ticket='AZ5-5', surface='SourceHut job cancel missing token', family='js_route', skip='hut builds cancel 1', auth='hut builds show 1', leftover='patch'),
    dict(slug='srht-build-skip-delete', plant='azs05mast', ticket='AZ6-6', surface='sr.ht build delete missing token', family='js_route', skip='curl -X DELETE $SRHT/api/jobs/1', auth='curl -H "Authorization: Bearer $SRHT" $SRHT/api/jobs/1', leftover='update'),
    dict(slug='buildbot-skip-delete', plant='azs06mast', ticket='AZ7-7', surface='Buildbot force cancel missing auth', family='js_route', skip='curl -X POST $BB/api/v2/builds/1/stop', auth='curl $BB/api/v2/builds/1 --user notes', leftover='put'),
    dict(slug='zuul-gate-skip-delete', plant='azs07mast', ticket='AZ8-8', surface='Zuul dequeue missing auth', family='js_route', skip='zuul-client dequeue --pipeline check --project notes', auth='zuul-client autohold-list --auth-token $ZUUL', leftover='patch'),
    dict(slug='jenkins-x-skip-delete', plant='azs08mast', ticket='AZ9-9', surface='Jenkins X pipeline delete missing git token', family='js_route', skip='jx pipeline delete notes', auth='jx get pipelines', leftover='update'),
    dict(slug='tekton-tr-skip-delete', plant='azs09mast', ticket='AZ1-10', surface='Tekton TaskRun delete missing SA', family='js_route', skip='tkn tr delete notes -f', auth='tkn tr describe notes', leftover='put'),
    dict(slug='argo-ev-skip-delete', plant='azs10mast', ticket='AZ2-11', surface='Argo Events sensor delete missing SA', family='js_route', skip='kubectl delete sensor notes', auth='kubectl get sensor notes', leftover='patch'),
    dict(slug='keptn-skip-delete', plant='azs11mast', ticket='AZ3-12', surface='Keptn project delete missing token', family='js_route', skip='keptn delete project notes', auth='keptn get project notes --oauth --client-id $KEPTN', leftover='update'),
    dict(slug='flagger-skip-delete', plant='azs12mast', ticket='AZ4-13', surface='Flagger canary delete missing rbac', family='js_route', skip='kubectl delete canary notes', auth='kubectl get canary notes', leftover='put'),
    dict(slug='istio-vs-skip-delete', plant='azs13mast', ticket='AZ5-14', surface='Istio VirtualService delete missing rbac', family='js_route', skip='kubectl delete virtualservice notes', auth='kubectl get virtualservice notes', leftover='patch'),
    dict(slug='linkerd-skip-delete', plant='azs14mast', ticket='AZ6-15', surface='Linkerd profile delete missing rbac', family='js_route', skip='linkerd profile --open-api notes.yaml | kubectl delete -f -', auth='linkerd viz stat deploy/notes', leftover='update'),
    dict(slug='cilium-np-skip-delete', plant='azs15mast', ticket='AZ7-16', surface='CiliumNetworkPolicy delete missing rbac', family='js_route', skip='kubectl delete cnp notes', auth='kubectl get cnp notes', leftover='put'),
    dict(slug='ovn-acl-skip-delete', plant='azs16mast', ticket='AZ8-17', surface='OVN ACL delete missing NB auth', family='js_route', skip='ovn-nbctl acl-del notes', auth='ovn-nbctl --db $OVN acl-list notes', leftover='patch'),
    dict(slug='sriov-skip-delete', plant='azs17mast', ticket='AZ9-18', surface='SR-IOV network delete missing rbac', family='js_route', skip='kubectl delete sriovnetwork notes', auth='kubectl get sriovnetwork notes', leftover='update'),
    dict(slug='metallb-ip-skip-delete', plant='azs18mast', ticket='AZ1-19', surface='MetalLB IPAddressPool delete missing rbac', family='js_route', skip='kubectl delete ipaddresspool notes', auth='kubectl get ipaddresspool notes', leftover='put'),
    dict(slug='ingressnginx-skip-delete', plant='azs19mast', ticket='AZ2-20', surface='ingress-nginx ingress delete missing rbac', family='js_route', skip='kubectl delete ingress notes', auth='kubectl get ingress notes', leftover='patch'),
    dict(slug='traefik-mw-skip-delete', plant='azs20mast', ticket='AZ3-21', surface='Traefik middleware delete missing rbac', family='js_route', skip='kubectl delete middleware notes', auth='kubectl get middleware notes', leftover='update'),
    dict(slug='haproxy-be-skip-delete', plant='azs21mast', ticket='AZ4-22', surface='HAProxy backend delete missing stats auth', family='js_route', skip="echo 'del backend notes' | socat stdio /var/run/haproxy.sock", auth="echo 'show stat' | socat stdio /var/run/haproxy.sock", leftover='put'),
    dict(slug='envoy-rt-skip-delete', plant='azs22mast', ticket='AZ5-23', surface='Envoy runtime delete missing admin', family='js_route', skip='curl -X POST $ENVOY/runtime_modify?notes=0', auth='curl $ENVOY/runtime', leftover='patch'),
    dict(slug='kong-svc-skip-delete', plant='azs23mast', ticket='AZ6-24', surface='Kong service delete missing admin token', family='js_route', skip='curl -X DELETE $KONG/services/notes', auth='curl -H "Kong-Admin-Token: $KONG" $KONG/services/notes', leftover='update'),
    dict(slug='apisix-rt-skip-delete', plant='azs24mast', ticket='AZ7-25', surface='APISIX route delete missing admin key', family='js_route', skip='curl -X DELETE $APISIX/apisix/admin/routes/1', auth='curl -H "X-API-KEY: $APISIX" $APISIX/apisix/admin/routes/1', leftover='put'),
    dict(slug='tyk-api-skip-delete', plant='azs25mast', ticket='AZ8-26', surface='Tyk API delete missing secret', family='js_route', skip='curl -X DELETE $TYK/tyk/apis/notes', auth='curl -H "x-tyk-authorization: $TYK" $TYK/tyk/apis/notes', leftover='patch'),
    dict(slug='krakend-skip-delete', plant='azs26mast', ticket='AZ9-27', surface='KrakenD endpoint delete missing config auth', family='js_route', skip='curl -X DELETE $KRAKEND/__health/notes', auth='curl $KRAKEND/__health', leftover='update'),
    dict(slug='caddy-site-skip-delete', plant='azs27mast', ticket='AZ1-28', surface='Caddy site unload missing admin', family='js_route', skip='caddy reload --config /dev/null', auth='caddy adapt --config Caddyfile', leftover='put'),
    dict(slug='nginx-up-skip-delete', plant='azs28mast', ticket='AZ2-29', surface='nginx upstream delete missing conf', family='js_route', skip='curl -X POST $NGINX/upstream_conf?remove=&upstream=notes', auth='curl $NGINX/status', leftover='patch'),
    dict(slug='apache-vhost-skip-delete', plant='azs29mast', ticket='AZ3-30', surface='Apache vhost remove missing sudoers', family='js_route', skip='a2dissite notes', auth='apachectl -S', leftover='update'),
    dict(slug='lighttpd-skip-delete', plant='azs30mast', ticket='AZ4-31', surface='lighttpd config drop missing auth', family='js_route', skip='rm /etc/lighttpd/conf-enabled/notes.conf', auth='lighttpd -tt -f /etc/lighttpd/lighttpd.conf', leftover='put'),
    dict(slug='hitch-skip-delete', plant='azs31mast', ticket='AZ5-32', surface='Hitch frontend delete missing conf', family='js_route', skip='rm /etc/hitch/notes.pem', auth='hitch --config /etc/hitch/hitch.conf --test', leftover='patch'),
    dict(slug='varnish-ban-skip-delete', plant='azs32mast', ticket='AZ6-33', surface='Varnish ban missing secret', family='js_route', skip='varnishadm ban req.url == /notes', auth='varnishadm -S /etc/varnish/secret ban.list', leftover='update'),
    dict(slug='squid-acl-skip-delete', plant='azs33mast', ticket='AZ7-34', surface='Squid ACL delete missing conf', family='js_route', skip='squid -k reconfigure', auth='squidclient mgr:info', leftover='put'),
    dict(slug='frr-bgp-skip-delete', plant='azs34mast', ticket='AZ8-35', surface='FRR BGP neighbor delete missing vtysh', family='js_route', skip="vtysh -c 'no neighbor notes'", auth="vtysh -c 'show ip bgp summary'", leftover='patch'),
    dict(slug='bird-bgp-skip-delete', plant='azs35mast', ticket='AZ9-36', surface='BIRD protocol disable missing conf', family='js_route', skip='birdc disable notes', auth='birdc show protocols', leftover='update'),
    dict(slug='gobgp-skip-delete', plant='azs36mast', ticket='AZ1-37', surface='GoBGP neighbor delete missing grpc auth', family='js_route', skip='gobgp neighbor del 1.1.1.1', auth='gobgp neighbor', leftover='put'),
    dict(slug='exabgp-skip-delete', plant='azs37mast', ticket='AZ2-38', surface='ExaBGP withdraw missing control', family='js_route', skip="echo 'neighbor 1.1.1.1 withdraw route 10.0.0.0/8' > /run/exabgp.in", auth='exabgpcli show neighbor summary', leftover='patch'),
    dict(slug='openbgpd-skip-delete', plant='azs38mast', ticket='AZ3-39', surface='OpenBGPD neighbor delete missing control', family='js_route', skip='bgpctl neighbor notes down', auth='bgpctl show neighbor notes', leftover='update'),
    dict(slug='bird2-skip-delete', plant='azs39mast', ticket='AZ4-40', surface='BIRD2 protocol remove missing conf', family='js_route', skip='birdc configure undo', auth='birdc show status', leftover='put'),
    dict(slug='frr-ospf-skip-delete', plant='azs40mast', ticket='AZ5-41', surface='FRR OSPF interface delete missing vtysh', family='js_route', skip="vtysh -c 'no ip ospf hello-interval'", auth="vtysh -c 'show ip ospf neighbor'", leftover='patch'),
    dict(slug='strongswan-skip-delete', plant='azs41mast', ticket='AZ6-42', surface='strongSwan conn down missing secrets', family='js_route', skip='ipsec down notes', auth='ipsec statusall', leftover='update'),
    dict(slug='openvpn-ccd-skip-delete', plant='azs42mast', ticket='AZ7-43', surface='OpenVPN CCD delete missing admin', family='js_route', skip='rm /etc/openvpn/ccd/notes', auth='openvpn --show-tls', leftover='put'),
    dict(slug='wireguard-peer-skip-delete', plant='azs43mast', ticket='AZ8-44', surface='WireGuard peer delete missing conf', family='js_route', skip='wg set wg0 peer notes remove', auth='wg show wg0', leftover='patch'),
    dict(slug='ipsec-sa-skip-delete', plant='azs44mast', ticket='AZ9-45', surface='IPsec SA delete missing racoon', family='js_route', skip='ip xfrm state deleteall', auth='ip xfrm state list', leftover='update'),
    dict(slug='tailscale-acl-skip-delete', plant='azs45mast', ticket='AZ1-46', surface='Tailscale ACL wipe missing api-key', family='js_route', skip='tailscale debug derp-map --force', auth='tailscale status --json', leftover='put'),
    dict(slug='headscale-skip-delete', plant='azs46mast', ticket='AZ2-47', surface='Headscale node delete missing api-key', family='js_route', skip='headscale nodes delete -i 1 --force', auth='headscale nodes list -o json', leftover='patch'),
    dict(slug='zerotier-skip-delete', plant='azs47mast', ticket='AZ3-48', surface='ZeroTier member delete missing token', family='js_route', skip='zerotier-cli leave notes', auth='zerotier-cli listnetworks', leftover='update'),
    dict(slug='nebula-skip-delete', plant='azs48mast', ticket='AZ4-49', surface='Nebula cert revoke missing ca', family='js_route', skip='nebula-cert revoke -name notes', auth='nebula-cert print -path ca.crt', leftover='put'),
    dict(slug='tinc-skip-delete', plant='azs49mast', ticket='AZ5-50', surface='tinc host delete missing key', family='js_route', skip='tinc -n notes del notes2', auth='tinc -n notes info notes2', leftover='patch'),
    dict(slug='fastd-skip-delete', plant='azs50mast', ticket='AZ6-51', surface='fastd peer delete missing conf', family='js_route', skip='rm /etc/fastd/notes/peers/p', auth='fastd --verify-config --config /etc/fastd/notes/fastd.conf', leftover='update'),
    dict(slug='fastd2-skip-delete', plant='azs51mast', ticket='AZ7-52', surface='fastd2 peer drop missing socket', family='js_route', skip="echo 'del peer notes' | socat - UNIX-CONNECT:/run/fastd.sock", auth="echo 'show peers' | socat - UNIX-CONNECT:/run/fastd.sock", leftover='put'),
    dict(slug='innernet-skip-delete', plant='azs52mast', ticket='AZ8-53', surface='innernet peer delete missing admin', family='js_route', skip='innernet -n notes delete-peer p', auth='innernet -n notes list-peers', leftover='patch'),
    dict(slug='netbird-skip-delete', plant='azs53mast', ticket='AZ9-54', surface='NetBird peer delete missing token', family='js_route', skip='netbird down', auth='netbird status --detail', leftover='update'),
    dict(slug='netmaker-skip-delete', plant='azs54mast', ticket='AZ1-55', surface='Netmaker node delete missing token', family='js_route', skip='curl -X DELETE $NM/api/nodes/notes', auth='curl -H "Authorization: Bearer $NM" $NM/api/nodes/notes', leftover='put'),
    dict(slug='openwrt-uci-skip-delete', plant='azs55mast', ticket='AZ2-56', surface='OpenWrt UCI delete missing root', family='js_route', skip='uci delete network.notes', auth='uci show network', leftover='patch'),
    dict(slug='opnsense-skip-delete', plant='azs56mast', ticket='AZ3-57', surface='OPNsense alias delete missing key', family='js_route', skip='curl -X POST $OS/api/firewall/alias/delItem/notes', auth='curl -k -u key:secret $OS/api/firewall/alias/getItem/notes', leftover='update'),
    dict(slug='pfsense-skip-delete', plant='azs57mast', ticket='AZ4-58', surface='pfSense alias delete missing csrf', family='js_route', skip='curl -X POST $PF/firewall_aliases_edit.php?act=del&id=1', auth='curl $PF/firewall_aliases.php', leftover='put'),
    dict(slug='vyos-skip-delete', plant='azs58mast', ticket='AZ5-59', surface='VyOS interface delete missing commit', family='js_route', skip="vyos-config -c 'delete interfaces ethernet eth1'", auth="vyos-config -c 'show interfaces'", leftover='patch'),
    dict(slug='mikrotik-skip-delete', plant='azs59mast', ticket='AZ6-60', surface='MikroTik address delete missing api', family='js_route', skip="ssh admin@r '/ip address remove notes'", auth="ssh admin@r '/ip address print'", leftover='update'),
    dict(slug='unifi-skip-delete', plant='azs60mast', ticket='AZ7-61', surface='UniFi client block missing token', family='js_route', skip='curl -X POST $UNIFI/api/s/default/cmd/stamgr -d {cmd:kick-sta,mac:notes}', auth='curl -H "Authorization: Bearer $UNIFI" $UNIFI/api/s/default/stat/sta', leftover='put'),
    dict(slug='omada-skip-delete', plant='azs61mast', ticket='AZ8-62', surface='Omada client delete missing token', family='js_route', skip='curl -X POST $OMADA/api/v2/sites/s/clients/notes/kick', auth='curl -H "Csrf-Token: $OMADA" $OMADA/api/v2/sites/s/clients', leftover='patch'),
    dict(slug='meraki-skip-delete', plant='azs62mast', ticket='AZ9-63', surface='Meraki device remove missing key', family='js_route', skip='curl -X DELETE $MERAKI/api/v1/networks/n/devices/notes', auth='curl -H "X-Cisco-Meraki-API-Key: $MERAKI" $MERAKI/api/v1/networks/n/devices', leftover='update'),
    dict(slug='panos-skip-delete', plant='azs63mast', ticket='AZ1-64', surface='PAN-OS address delete missing key', family='js_route', skip='curl -X GET $PAN/api/?type=config&action=delete&xpath=notes', auth='curl -H "X-PAN-KEY: $PAN" $PAN/api/?type=op&cmd=<show><system><info></info></system></show>', leftover='put'),
    dict(slug='fortigate-skip-delete', plant='azs64mast', ticket='AZ2-65', surface='FortiGate address delete missing token', family='js_route', skip='curl -X DELETE $FG/api/v2/cmdb/firewall/address/notes', auth='curl -H "Authorization: Bearer $FG" $FG/api/v2/cmdb/firewall/address/notes', leftover='patch'),
    dict(slug='asa-acl-skip-delete', plant='azs65mast', ticket='AZ3-66', surface='ASA ACL delete missing enable', family='js_route', skip="echo 'no access-list notes' | ssh asa", auth="echo 'show access-list notes' | ssh asa", leftover='update'),
    dict(slug='checkpoint-skip-delete', plant='azs66mast', ticket='AZ4-67', surface='Check Point host delete missing sid', family='js_route', skip='mgmt_cli delete host name notes', auth='mgmt_cli show host name notes', leftover='put'),
    dict(slug='sophos-skip-delete', plant='azs67mast', ticket='AZ5-68', surface='Sophos object delete missing token', family='js_route', skip='curl -X DELETE $SOPHOS/api/objects/hosts/notes', auth='curl -H "X-Res-Token: $SOPHOS" $SOPHOS/api/objects/hosts/notes', leftover='patch'),
    dict(slug='watchguard-skip-delete', plant='azs68mast', ticket='AZ6-69', surface='WatchGuard alias delete missing session', family='js_route', skip='curl -X POST $WG/rest/alias/delete -d {name:notes}', auth='curl $WG/rest/alias --cookie $WG', leftover='update'),
    dict(slug='sonicwall-skip-delete', plant='azs69mast', ticket='AZ7-70', surface='SonicWall address delete missing token', family='js_route', skip='curl -X DELETE $SW/api/sonicos/address-objects/ipv4/name/notes', auth='curl -H "Authorization: Bearer $SW" $SW/api/sonicos/address-objects/ipv4', leftover='put'),
    dict(slug='certmgr-cert-skip-delete', plant='azs70mast', ticket='AZ8-71', surface='cert-manager Certificate delete missing rbac', family='js_route', skip='kubectl delete certificate notes', auth='kubectl get certificate notes', leftover='patch'),
    dict(slug='ext-dns-skip-delete', plant='azs71mast', ticket='AZ9-72', surface='external-dns endpoint delete missing rbac', family='js_route', skip='kubectl delete dnsendpoint notes', auth='kubectl get dnsendpoint notes', leftover='update'),
    dict(slug='keda-so-skip-delete', plant='azs72mast', ticket='AZ1-73', surface='KEDA ScaledObject delete missing rbac', family='js_route', skip='kubectl delete scaledobject notes', auth='kubectl get scaledobject notes', leftover='put'),
    dict(slug='kserve-isvc-skip-delete', plant='azs73mast', ticket='AZ2-74', surface='KServe InferenceService delete missing rbac', family='js_route', skip='kubectl delete inferenceservice notes', auth='kubectl get inferenceservice notes', leftover='patch'),
    dict(slug='seldon-dep-skip-delete', plant='azs74mast', ticket='AZ3-75', surface='SeldonDeployment delete missing rbac', family='js_route', skip='kubectl delete seldondeployment notes', auth='kubectl get seldondeployment notes', leftover='update'),
    dict(slug='bento-svc-skip-delete', plant='azs75mast', ticket='AZ4-76', surface='BentoML service delete missing token', family='js_route', skip='bentoml delete notes:latest -y', auth='bentoml get notes:latest', leftover='put'),
    dict(slug='triton-model-skip-delete', plant='azs76mast', ticket='AZ5-77', surface='Triton model unload missing auth', family='js_route', skip='curl -X POST $TRITON/v2/repository/models/notes/unload', auth='curl $TRITON/v2/models/notes', leftover='patch'),
    dict(slug='torchserve-skip-delete', plant='azs77mast', ticket='AZ6-78', surface='TorchServe unregister missing token', family='js_route', skip='curl -X DELETE $TS/models/notes', auth='curl $TS/models/notes', leftover='update'),
    dict(slug='tfserving-skip-delete', plant='azs78mast', ticket='AZ7-79', surface='TF Serving unload missing auth', family='js_route', skip='curl -X POST $TFS/v1/models/notes:unload', auth='curl $TFS/v1/models/notes', leftover='put'),
    dict(slug='cilium-policy-skip-delete', plant='azs79mast', ticket='AZ8-80', surface='Cilium clusterwide policy delete missing rbac', family='js_route', skip='kubectl delete ccnp notes', auth='kubectl get ccnp notes', leftover='patch'),
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
