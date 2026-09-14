"""Extra unique IDOR/BFLA plants for authz-regression-factory r1365+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r1364 vesselNNNN-sys.
Not clones of r1364 geohash-cell-idor / channels-consumer-skip-delete.
"""
from __future__ import annotations


EXTRA_IDOR_ROWS = [
    dict(slug='mgrs-grid-idor', plant='abeam', ticket='ABE-1', surface='MGRS grid square object-id IDOR', mod='mgrs', model='Mgrs', lookup='mgrs', sample='18TWL850000', owner='map_id', first='authn', residual='pdf', product='abeam-mgrs-nga', bug='ABE-1 MGRS unique from NGA grid'),
    dict(slug='maidenhead-grid-idor', plant='adrift', ticket='ADR-2', surface='Maidenhead locator object-id IDOR', mod='maidenheads', model='Maidenhead', lookup='locator', sample='FN20xr', owner='club_id', first='mask', residual='export', product='adrift-maidenhead-iaru', bug='ADR-2 Maidenhead unique from IARU'),
    dict(slug='unlocode-port-idor', plant='aground', ticket='AGR-3', surface='UN/LOCODE port object-id IDOR', mod='unlocodes', model='Unlocode', lookup='locode', sample='USNYC', owner='network_id', first='any_member', residual='search', product='aground-unlocode-unece', bug='AGR-3 LOCODE unique from UNECE'),
    dict(slug='iata-airport-idor', plant='alee', ticket='ALE-4', surface='IATA airport code object-id IDOR', mod='iataapts', model='IataApt', lookup='iata', sample='JFK', owner='network_id', first='list_scope', residual='mget', product='alee-iata-apt', bug='ALE-4 IATA unique from location table'),
    dict(slug='icao-airline-idor', plant='aloft', ticket='ALO-5', surface='ICAO airline designator object-id IDOR', mod='airlines', model='Airline', lookup='icaoal', sample='UAL', owner='alliance_id', first='authn', residual='csv', product='aloft-icao-al', bug='ALO-5 ICAO airline unique from Doc 8585'),
    dict(slug='imo-ship-idor', plant='amidships', ticket='AMI-6', surface='IMO ship number object-id IDOR', mod='imoships', model='ImoShip', lookup='imo', sample='IMO9074729', owner='fleet_id', first='mask', residual='admin', product='amidships-imo-gis', bug='AMI-6 IMO unique from GISIS'),
    dict(slug='eni-inland-idor', plant='apeak', ticket='APE-7', surface='ENI inland craft object-id IDOR', mod='enis', model='Eni', lookup='eni', sample='04012345', owner='fleet_id', first='any_member', residual='webhook', product='apeak-eni-cesni', bug='APE-7 ENI unique from CESNI'),
    dict(slug='isrc-track-idor', plant='athwart', ticket='ATH-8', surface='ISRC recording object-id IDOR', mod='isrcs', model='Isrc', lookup='isrc', sample='USRC17607839', owner='label_id', first='list_scope', residual='comments', product='athwart-isrc-ifpi', bug='ATH-8 ISRC unique from IFPI'),
    dict(slug='iswc-work-idor', plant='awash', ticket='AWA-9', surface='ISWC musical work object-id IDOR', mod='iswcs', model='Iswc', lookup='iswc', sample='T-034.524.680-1', owner='society_id', first='authn', residual='pdf', product='awash-iswc-cisac', bug='AWA-9 ISWC unique from CISAC'),
    dict(slug='isni-party-idor', plant='ballast', ticket='BAL-1', surface='ISNI party object-id IDOR', mod='isnis', model='Isni', lookup='isni', sample='0000000121032683', owner='registry_id', first='mask', residual='export', product='ballast-isni-iso', bug='BAL-1 ISNI unique from ISO 27729'),
    dict(slug='lccn-record-idor', plant='barnacle', ticket='BAR-2', surface='LCCN bibliographic object-id IDOR', mod='lccns', model='Lccn', lookup='lccn', sample='n79021164', owner='library_id', first='any_member', residual='search', product='barnacle-lccn-loc', bug='BAR-2 LCCN unique from LoC'),
    dict(slug='oclc-number-idor', plant='barque', ticket='BAR-3', surface='OCLC number object-id IDOR', mod='oclcs', model='Oclc', lookup='oclc', sample='ocm00012345', owner='library_id', first='list_scope', residual='mget', product='barque-oclc-worldcat', bug='BAR-3 OCLC unique from WorldCat'),
    dict(slug='dblp-pid-idor', plant='becket', ticket='BEC-4', surface='DBLP person object-id IDOR', mod='dblps', model='Dblp', lookup='pid', sample='homepages/h/BjarneStroustrup', owner='campus_id', first='authn', residual='csv', product='becket-dblp-pid', bug='BEC-4 DBLP pid unique from Trier'),
    dict(slug='upc-a-sku-idor', plant='bilge', ticket='BIL-5', surface='UPC-A SKU object-id IDOR', mod='upcs', model='Upc', lookup='upc', sample='036000291452', owner='catalog_id', first='mask', residual='admin', product='bilge-upc-gs1', bug='BIL-5 UPC unique from GS1 US'),
    dict(slug='jan-barcode-idor', plant='bitthead', ticket='BIT-6', surface='JAN barcode object-id IDOR', mod='jans', model='Jan', lookup='jan', sample='4901234567894', owner='catalog_id', first='any_member', residual='webhook', product='bitthead-jan-dsri', bug='BIT-6 JAN unique from DSRI'),
    dict(slug='giai-asset-idor', plant='boomvang', ticket='BOO-7', surface='GS1 GIAI asset object-id IDOR', mod='giais', model='Giai', lookup='giai', sample='06141411234567890', owner='depot_id', first='list_scope', residual='comments', product='boomvang-giai-gs1', bug='BOO-7 GIAI unique from asset registry'),
    dict(slug='cvx-vaccine-idor', plant='bowse', ticket='BOW-8', surface='CVX vaccine object-id IDOR', mod='cvxs', model='Cvx', lookup='cvx', sample='141', owner='clinic_id', first='authn', residual='pdf', product='bowse-cvx-cdc', bug='BOW-8 CVX unique from CDC IIS'),
    dict(slug='umls-cui-idor', plant='brigantine', ticket='BRI-9', surface='UMLS CUI object-id IDOR', mod='umls', model='Umls', lookup='cui', sample='C0011849', owner='clinic_id', first='mask', residual='export', product='brigantine-umls-nlm', bug='BRI-9 CUI unique from UMLS Metathesaurus'),
    dict(slug='meddra-pt-idor', plant='bulkhead', ticket='BUL-1', surface='MedDRA PT object-id IDOR', mod='meddras', model='Meddra', lookup='ptcode', sample='10067569', owner='sponsor_id', first='any_member', residual='search', product='bulkhead-meddra-mss', bug='BUL-1 PT unique from MSSO'),
    dict(slug='icpc2-code-idor', plant='bulwark', ticket='BUL-2', surface='ICPC-2 encounter object-id IDOR', mod='icpcs', model='Icpc', lookup='icpc', sample='T90', owner='clinic_id', first='list_scope', residual='mget', product='bulwark-icpc-wonca', bug='BUL-2 ICPC unique from WONCA'),
    dict(slug='ucum-unit-idor', plant='camcleat', ticket='CAM-3', surface='UCUM unit object-id IDOR', mod='ucums', model='Ucum', lookup='ucum', sample='mmol/L', owner='lab_id', first='authn', residual='csv', product='camcleat-ucum-regenstrief', bug='CAM-3 UCUM unique from Regenstrief'),
    dict(slug='gnomad-vid-idor', plant='carline', ticket='CAR-4', surface='gnomAD variant object-id IDOR', mod='gnomads', model='Gnomad', lookup='vid', sample='1-55516888-G-GA', owner='lab_id', first='mask', residual='admin', product='carline-gnomad-broad', bug='CAR-4 VID unique from gnomAD'),
    dict(slug='civic-eid-idor', plant='catboat', ticket='CAT-5', surface='CIViC evidence object-id IDOR', mod='civics', model='Civic', lookup='eid', sample='EID:1998', owner='lab_id', first='any_member', residual='webhook', product='catboat-civic-wustl', bug='CAT-5 EID unique from CIViC'),
    dict(slug='oncotree-code-idor', plant='chock', ticket='CHO-6', surface='OncoTree code object-id IDOR', mod='oncotrees', model='Oncotree', lookup='oncotree', sample='LUAD', owner='lab_id', first='list_scope', residual='comments', product='chock-oncotree-msk', bug='CHO-6 OncoTree unique from MSK'),
    dict(slug='doid-disease-idor', plant='coaming', ticket='COA-7', surface='Disease Ontology object-id IDOR', mod='doids', model='Doid', lookup='doid', sample='DOID:9351', owner='clinic_id', first='authn', residual='pdf', product='coaming-doid-obo', bug='COA-7 DOID unique from OBO'),
    dict(slug='efo-term-idor', plant='coir', ticket='COI-8', surface='EFO trait object-id IDOR', mod='efos', model='Efo', lookup='efo', sample='EFO:0000400', owner='lab_id', first='mask', residual='export', product='coir-efo-ebi', bug='COI-8 EFO unique from EMBL-EBI'),
    dict(slug='cl-cell-idor', plant='counter', ticket='COU-9', surface='Cell Ontology object-id IDOR', mod='clcells', model='Clcell', lookup='clid', sample='CL:0000236', owner='lab_id', first='any_member', residual='search', product='counter-cl-obo', bug='COU-9 CL unique from Cell Ontology'),
    dict(slug='cellosaurus-cvcl-idor', plant='cutwater', ticket='CUT-1', surface='Cellosaurus CVCL object-id IDOR', mod='cvcls', model='Cvcl', lookup='cvcl', sample='CVCL_0030', owner='lab_id', first='list_scope', residual='mget', product='cutwater-cellosaurus-sib', bug='CUT-1 CVCL unique from SIB'),
    dict(slug='rrid-resource-idor', plant='deadeye', ticket='DEA-2', surface='RRID resource object-id IDOR', mod='rrids', model='Rrid', lookup='rrid', sample='RRID:AB_217931', owner='lab_id', first='authn', residual='csv', product='deadeye-rrid-scicrunch', bug='DEA-2 RRID unique from SciCrunch'),
    dict(slug='addgene-plasmid-idor', plant='deadwood', ticket='DEA-3', surface='Addgene plasmid object-id IDOR', mod='plasmids', model='Plasmid', lookup='addgene', sample='52920', owner='lab_id', first='mask', residual='admin', product='deadwood-addgene-plasmid', bug='DEA-3 Addgene unique from catalog'),
    dict(slug='jax-strain-idor', plant='dodger', ticket='DOD-4', surface='JAX strain object-id IDOR', mod='jaxs', model='Jax', lookup='jax', sample='000664', owner='lab_id', first='any_member', residual='webhook', product='dodger-jax-strain', bug='DOD-4 JAX unique from Mouse Genome'),
    dict(slug='flybase-fbid-idor', plant='draught', ticket='DRA-5', surface='FlyBase gene object-id IDOR', mod='flybases', model='Flybase', lookup='fbid', sample='FBgn0000490', owner='lab_id', first='list_scope', residual='comments', product='draught-flybase-fbid', bug='DRA-5 FBid unique from FlyBase'),
    dict(slug='wormbase-wbid-idor', plant='dutchman', ticket='DUT-6', surface='WormBase gene object-id IDOR', mod='wormbases', model='Wormbase', lookup='wbid', sample='WBGene00000898', owner='lab_id', first='authn', residual='pdf', product='dutchman-wormbase-wbid', bug='DUT-6 WBID unique from WormBase'),
    dict(slug='sgd-orf-idor', plant='fishplate', ticket='FIS-7', surface='SGD ORF object-id IDOR', mod='sgds', model='Sgd', lookup='sgd', sample='S000000001', owner='lab_id', first='mask', residual='export', product='fishplate-sgd-orf', bug='FIS-7 SGD unique from yeast genome'),
    dict(slug='zfin-id-idor', plant='flotsam', ticket='FLO-8', surface='ZFIN gene object-id IDOR', mod='zfins', model='Zfin', lookup='zfin', sample='ZDB-GENE-980526-166', owner='lab_id', first='any_member', residual='search', product='flotsam-zfin-id', bug='FLO-8 ZFIN unique from zebrafish'),
    dict(slug='mgi-marker-idor', plant='focsle', ticket='FOC-9', surface='MGI marker object-id IDOR', mod='mgis', model='Mgi', lookup='mgi', sample='MGI:96677', owner='lab_id', first='list_scope', residual='mget', product='focsle-mgi-marker', bug='FOC-9 MGI unique from Jackson'),
    dict(slug='rgd-gene-idor', plant='forepeak', ticket='FOR-1', surface='RGD gene object-id IDOR', mod='rgds', model='Rgd', lookup='rgd', sample='RGD:620268', owner='lab_id', first='authn', residual='csv', product='forepeak-rgd-gene', bug='FOR-1 RGD unique from rat genome'),
    dict(slug='drugbank-id-idor', plant='galley', ticket='GAL-2', surface='DrugBank compound object-id IDOR', mod='drugbanks', model='Drugbank', lookup='drugbank', sample='DB00945', owner='lab_id', first='mask', residual='admin', product='galley-drugbank-id', bug='GAL-2 DrugBank unique from Wishart'),
    dict(slug='zinc15-id-idor', plant='gennaker', ticket='GEN-3', surface='ZINC15 molecule object-id IDOR', mod='zincs', model='Zinc', lookup='zinc', sample='ZINC000000000016', owner='lab_id', first='any_member', residual='webhook', product='gennaker-zinc15-id', bug='GEN-3 ZINC unique from Irwin'),
    dict(slug='lipidmaps-idor', plant='girtline', ticket='GIR-4', surface='LIPID MAPS object-id IDOR', mod='lipidmaps', model='Lipidmap', lookup='lm', sample='LMFA01010001', owner='lab_id', first='list_scope', residual='comments', product='girtline-lipidmaps-id', bug='GIR-4 LM unique from LIPID MAPS'),
    dict(slug='emdb-map-idor', plant='grabrail', ticket='GRA-5', surface='EMDB map object-id IDOR', mod='emdbs', model='Emdb', lookup='emdb', sample='EMD-0001', owner='lab_id', first='authn', residual='pdf', product='grabrail-emdb-map', bug='GRA-5 EMDB unique from EBI'),
    dict(slug='bmrb-entry-idor', plant='gripe', ticket='GRI-6', surface='BMRB entry object-id IDOR', mod='bmrbs', model='Bmrb', lookup='bmrb', sample='bmr15000', owner='lab_id', first='mask', residual='export', product='gripe-bmrb-entry', bug='GRI-6 BMRB unique from NMR'),
    dict(slug='afdb-model-idor', plant='gudgeon', ticket='GUD-7', surface='AlphaFold DB model object-id IDOR', mod='afdbs', model='Afdb', lookup='afdb', sample='AF-P04637-F1', owner='lab_id', first='any_member', residual='search', product='gudgeon-afdb-model', bug='GUD-7 AFDB unique from EBI'),
    dict(slug='wikipathways-idor', plant='gunport', ticket='GUN-8', surface='WikiPathways object-id IDOR', mod='wikipathways', model='Wikipathway', lookup='wpid', sample='WP554', owner='lab_id', first='list_scope', residual='mget', product='gunport-wikipathways-id', bug='GUN-8 WP unique from WikiPathways'),
    dict(slug='biogrid-int-idor', plant='gybe', ticket='GYB-9', surface='BioGRID interaction object-id IDOR', mod='biogrids', model='Biogrid', lookup='biogrid', sample='113409', owner='lab_id', first='authn', residual='csv', product='gybe-biogrid-int', bug='GYB-9 BioGRID unique from interaction'),
    dict(slug='intact-ebi-idor', plant='hance', ticket='HAN-1', surface='IntAct interaction object-id IDOR', mod='intacts', model='Intact', lookup='intact', sample='EBI-464353', owner='lab_id', first='mask', residual='admin', product='hance-intact-ebi', bug='HAN-1 IntAct unique from EBI'),
    dict(slug='string-protein-idor', plant='hatchcoam', ticket='HAT-2', surface='STRING protein object-id IDOR', mod='strings', model='Stringp', lookup='stringid', sample='9606.ENSP00000269305', owner='lab_id', first='any_member', residual='webhook', product='hatchcoam-string-protein', bug='HAT-2 STRING unique from ELIXIR'),
    dict(slug='brenda-ligand-idor', plant='headstay', ticket='HEA-3', surface='BRENDA ligand object-id IDOR', mod='brendas', model='Brenda', lookup='brenda', sample='CHEBI:15377', owner='lab_id', first='list_scope', residual='comments', product='headstay-brenda-ligand', bug='HEA-3 BRENDA unique from enzyme'),
    dict(slug='panther-family-idor', plant='helmstock', ticket='HEL-4', surface='PANTHER family object-id IDOR', mod='panthers', model='Panther', lookup='pthr', sample='PTHR23086', owner='lab_id', first='authn', residual='pdf', product='helmstock-panther-family', bug='HEL-4 PTHR unique from PANTHER'),
    dict(slug='prosite-ps-idor', plant='hogframe', ticket='HOG-5', surface='PROSITE pattern object-id IDOR', mod='prosites', model='Prosite', lookup='ps', sample='PS00107', owner='lab_id', first='mask', residual='export', product='hogframe-prosite-ps', bug='HOG-5 PS unique from SIB'),
    dict(slug='smart-domain-idor', plant='jackline', ticket='JAC-6', surface='SMART domain object-id IDOR', mod='smarts', model='Smart', lookup='smart', sample='SM00220', owner='lab_id', first='any_member', residual='search', product='jackline-smart-domain', bug='JAC-6 SMART unique from EMBL'),
    dict(slug='cdd-domain-idor', plant='jibsheet', ticket='JIB-7', surface='CDD domain object-id IDOR', mod='cdds', model='Cdd', lookup='cdd', sample='cd00180', owner='lab_id', first='list_scope', residual='mget', product='jibsheet-cdd-domain', bug='JIB-7 CDD unique from NCBI'),
    dict(slug='ncit-code-idor', plant='kingplank', ticket='KIN-8', surface='NCI Thesaurus object-id IDOR', mod='ncits', model='Ncit', lookup='ncit', sample='C4872', owner='clinic_id', first='authn', residual='csv', product='kingplank-ncit-code', bug='KIN-8 NCIt unique from NCI'),
    dict(slug='icdo3-morph-idor', plant='knighthead', ticket='KNI-9', surface='ICD-O-3 morphology object-id IDOR', mod='icdos', model='Icdo', lookup='icdo', sample='8140/3', owner='clinic_id', first='mask', residual='admin', product='knighthead-icdo3-morph', bug='KNI-9 ICD-O unique from IARC'),
    dict(slug='dsm5-code-idor', plant='lateen', ticket='LAT-1', surface='DSM-5 disorder object-id IDOR', mod='dsm5s', model='Dsm5', lookup='dsm5', sample='F32.1', owner='clinic_id', first='any_member', residual='webhook', product='lateen-dsm5-code', bug='LAT-1 DSM-5 unique from APA'),
    dict(slug='naics-code-idor', plant='leeward', ticket='LEE-2', surface='NAICS industry object-id IDOR', mod='naics', model='Naics', lookup='naics', sample='541511', owner='firm_id', first='list_scope', residual='comments', product='leeward-naics-census', bug='LEE-2 NAICS unique from Census'),
    dict(slug='sic-code-idor', plant='limberhole', ticket='LIM-3', surface='SIC industry object-id IDOR', mod='sics', model='Sic', lookup='sic', sample='7372', owner='firm_id', first='authn', residual='pdf', product='limberhole-sic-osha', bug='LIM-3 SIC unique from OSHA'),
    dict(slug='isic-code-idor', plant='logline', ticket='LOG-4', surface='ISIC industry object-id IDOR', mod='isics', model='Isic', lookup='isic', sample='J62', owner='firm_id', first='mask', residual='export', product='logline-isic-unsd', bug='LOG-4 ISIC unique from UNSD'),
    dict(slug='nace-code-idor', plant='mainsheet', ticket='MAI-5', surface='NACE industry object-id IDOR', mod='naces', model='Nace', lookup='nace', sample='62.01', owner='firm_id', first='any_member', residual='search', product='mainsheet-nace-eurostat', bug='MAI-5 NACE unique from Eurostat'),
    dict(slug='cpc-patent-idor', plant='masthead', ticket='MAS-6', surface='CPC patent class object-id IDOR', mod='cpcs', model='Cpc', lookup='cpc', sample='G06F21/31', owner='firm_id', first='list_scope', residual='mget', product='masthead-cpc-patent', bug='MAS-6 CPC unique from USPTO/EPO'),
    dict(slug='ipc-patent-idor', plant='oarlock', ticket='OAR-7', surface='IPC patent class object-id IDOR', mod='ipcs', model='Ipc', lookup='ipc', sample='G06F21/00', owner='firm_id', first='authn', residual='csv', product='oarlock-ipc-wipo', bug='OAR-7 IPC unique from WIPO'),
    dict(slug='uspto-app-idor', plant='partnerbeam', ticket='PAR-8', surface='USPTO application object-id IDOR', mod='usptos', model='Uspto', lookup='appno', sample='16/123456', owner='firm_id', first='mask', residual='admin', product='partnerbeam-uspto-app', bug='PAR-8 appno unique from PAIR'),
    dict(slug='epo-publ-idor', plant='pintle', ticket='PIN-9', surface='EPO publication object-id IDOR', mod='epos', model='Epo', lookup='epodoc', sample='EP1234567A1', owner='firm_id', first='any_member', residual='webhook', product='pintle-epo-publ', bug='PIN-9 EPODOC unique from Espacenet'),
    dict(slug='wipo-pct-idor', plant='poopdeck', ticket='POO-1', surface='PCT application object-id IDOR', mod='pcts', model='Pct', lookup='pct', sample='PCT/US2024/012345', owner='firm_id', first='list_scope', residual='comments', product='poopdeck-wipo-pct', bug='POO-1 PCT unique from Patentscope'),
    dict(slug='trademark-serial-idor', plant='portlight', ticket='POR-2', surface='USPTO trademark serial object-id IDOR', mod='tmarks', model='Tmark', lookup='serial', sample='88812345', owner='firm_id', first='authn', residual='pdf', product='portlight-tm-serial', bug='POR-2 serial unique from TESS'),
    dict(slug='ark-identifier-idor', plant='quarterbeam', ticket='QUA-3', surface='ARK identifier object-id IDOR', mod='arks', model='Ark', lookup='ark', sample='ark:/13030/tf5p30086k', owner='library_id', first='mask', residual='export', product='quarterbeam-ark-id', bug='QUA-3 ARK unique from NAAN'),
    dict(slug='purl-record-idor', plant='ridingbitt', ticket='RID-4', surface='PURL record object-id IDOR', mod='purls', model='Purl', lookup='purl', sample='https://purl.org/dc/terms/title', owner='library_id', first='any_member', residual='search', product='ridingbitt-purl-oclc', bug='RID-4 PURL unique from OCLC'),
    dict(slug='urn-nbn-idor', plant='rudderhead', ticket='RUD-5', surface='URN:NBN national bib object-id IDOR', mod='nbns', model='Nbn', lookup='nbn', sample='urn:nbn:de:bvb:12-bsb00000000-0', owner='library_id', first='list_scope', residual='mget', product='rudderhead-urn-nbn', bug='RUD-5 NBN unique from DNB'),
    dict(slug='sici-serial-idor', plant='runningback', ticket='RUN-6', surface='SICI serial item object-id IDOR', mod='sicis', model='Sici', lookup='sici', sample='0095-4403(199502/03)21:3<12:WATIIB>2.0.TX;2-J', owner='library_id', first='authn', residual='csv', product='runningback-sici-niso', bug='RUN-6 SICI unique from NISO'),
    dict(slug='coden-serial-idor', plant='scupper', ticket='SCU-7', surface='CODEN serial object-id IDOR', mod='codens', model='Coden', lookup='coden', sample='NATUAS', owner='library_id', first='mask', residual='admin', product='scupper-coden-cas', bug='SCU-7 CODEN unique from CASSI'),
    dict(slug='lcc-class-idor', plant='sheetbend', ticket='SHE-8', surface='LCC class object-id IDOR', mod='lccs', model='Lcc', lookup='lcc', sample='QA76.9.A25', owner='library_id', first='any_member', residual='webhook', product='sheetbend-lcc-class', bug='SHE-8 LCC unique from LoC schedules'),
    dict(slug='ddc-class-idor', plant='spinnaker', ticket='SPI-9', surface='DDC class object-id IDOR', mod='ddcs', model='Ddc', lookup='ddc', sample='005.8', owner='library_id', first='list_scope', residual='comments', product='spinnaker-ddc-class', bug='SPI-9 DDC unique from OCLC Dewey'),
    dict(slug='mesh-qualifier-idor', plant='stemson', ticket='STE-1', surface='MeSH qualifier object-id IDOR', mod='meshqs', model='Meshq', lookup='meshq', sample='Q000188', owner='campus_id', first='authn', residual='pdf', product='stemson-mesh-qual', bug='STE-1 MeSH qualifier unique from NLM'),
    dict(slug='icd10pcs-proc-idor', plant='sternpost', ticket='STE-2', surface='ICD-10-PCS procedure object-id IDOR', mod='pcs', model='Pcs', lookup='pcs', sample='0SRC0J9', owner='clinic_id', first='mask', residual='export', product='sternpost-icd10-pcs', bug='STE-2 PCS unique from CMS'),
    dict(slug='loinc-answer-idor', plant='timberhead', ticket='TIM-3', surface='LOINC answer list object-id IDOR', mod='loincans', model='Loincans', lookup='ll', sample='LL715-4', owner='clinic_id', first='any_member', residual='search', product='timberhead-loinc-ans', bug='TIM-3 LL unique from Regenstrief'),
    dict(slug='rxnorm-in-idor', plant='waterway', ticket='WAT-4', surface='RxNorm ingredient object-id IDOR', mod='rxins', model='Rxin', lookup='rxin', sample='161', owner='pharmacy_id', first='list_scope', residual='mget', product='waterway-rxnorm-in', bug='WAT-4 IN unique from RxNorm TTY'),
    dict(slug='atcvet-code-idor', plant='weathercloth', ticket='WEA-5', surface='ATCvet code object-id IDOR', mod='atcvets', model='Atcvet', lookup='atcvet', sample='QJ01CA04', owner='clinic_id', first='authn', residual='csv', product='weathercloth-atcvet-who', bug='WEA-5 ATCvet unique from WHO'),
    dict(slug='icd11-mms-ext-idor', plant='windward', ticket='WIN-6', surface='ICD-11 MMS extension object-id IDOR', mod='icd11xs', model='Icd11x', lookup='icd11x', sample='XT3S', owner='clinic_id', first='mask', residual='admin', product='windward-icd11-ext', bug='WIN-6 ICD-11 extension unique from WHO'),
    dict(slug='hgnc-alias-idor', plant='yawlboat', ticket='YAW-7', surface='HGNC alias symbol object-id IDOR', mod='hgncalias', model='Hgncalias', lookup='alias', sample='p53', owner='lab_id', first='any_member', residual='webhook', product='yawlboat-hgnc-alias', bug='YAW-7 alias unique from HGNC'),
    dict(slug='refseq-nm-idor', plant='yokeplate', ticket='YOK-8', surface='RefSeq NM transcript object-id IDOR', mod='nms', model='Nm', lookup='nm', sample='NM_000546.6', owner='lab_id', first='list_scope', residual='comments', product='yokeplate-refseq-nm', bug='YOK-8 NM unique from NCBI'),
]


BFLA_ROWS = [
    dict(slug='loopback-remote-skip-delete', plant='abeam', ticket='ABE-1', surface='LoopBack remoteMethod skip ACL on delete', family='js_route', skip="Note.delete = {acl: [], http: {verb: 'del', path: '/:id'}}", auth="Note.findById = {acls: [{permission: 'ALLOW', principalType: 'ROLE', principalId: '$authenticated'}]}", leftover='put'),
    dict(slug='feathers-hook-skip-delete', plant='adrift', ticket='ADR-2', surface='Feathers remove hook missing authenticate', family='js_route', skip="app.service('notes').hooks({ before: { remove: [] } })", auth="app.service('notes').hooks({ before: { find: [authenticate('jwt')] } })", leftover='patch'),
    dict(slug='moleculer-alias-skip-delete', plant='aground', ticket='AGR-3', surface='Moleculer alias DELETE missing auth', family='js_route', skip="remove: { auth: false, rest: 'DELETE /notes/:id' }", auth="get: { auth: 'required', rest: 'GET /notes/:id' }", leftover='update'),
    dict(slug='meteor-method-unauthed-delete', plant='alee', ticket='ALE-4', surface='Meteor method delete missing this.userId', family='js_route', skip="Meteor.methods({ 'notes.remove'(id) { Notes.remove(id) } })", auth="Meteor.publish('notes', function () { if (!this.userId) return []; return Notes.find({owner: this.userId}) })", leftover='put'),
    dict(slug='ember-adapter-skip-delete', plant='aloft', ticket='ALO-5', surface='Ember Data adapter deleteRecord skips adapter auth', family='js_route', skip="deleteRecord(store, type, snapshot) { return fetch(`/notes/${snapshot.id}`, {method:'DELETE'}) }", auth="findRecord(store, type, id) { return this.ajax(`/notes/${id}`, 'GET', {headers: this.headers}) }", leftover='patch'),
    dict(slug='redwood-sdl-skip-delete', plant='amidships', ticket='AMI-6', surface='Redwood SDL deleteNote missing @requireAuth', family='js_route', skip='deleteNote(id: Int!): Note! @skipAuth', auth='note(id: Int!): Note @requireAuth', leftover='update'),
    dict(slug='blitz-resolver-skip-delete', plant='apeak', ticket='APE-7', surface='Blitz resolver delete missing authorize', family='js_route', skip='export default resolver.pipe(async ({id}) => db.note.delete({where:{id}}))', auth='export default resolver.pipe(resolver.authorize(), async ({id}) => db.note.findFirst({where:{id}}))', leftover='put'),
    dict(slug='trpc-procedure-public-delete', plant='athwart', ticket='ATH-8', surface='tRPC publicProcedure leftover on delete', family='js_route', skip='delete: publicProcedure.input(z.number()).mutation(({input}) => db.note.delete({where:{id:input}}))', auth='get: protectedProcedure.input(z.number()).query(({input, ctx}) => db.note.findFirst({where:{id:input, ownerId: ctx.user.id}}))', leftover='patch'),
    dict(slug='postgraphile-delete-grant', plant='awash', ticket='AWA-9', surface='PostGraphile GRANT DELETE leftover', family='sql', skip='GRANT DELETE ON notes TO graphile_anon;', auth='GRANT SELECT ON notes TO graphile_user;', leftover='update'),
    dict(slug='graphql-yoga-plugin-skip', plant='ballast', ticket='BAL-1', surface='GraphQL Yoga useGenericAuth skip on delete', family='js_route', skip='deleteNote: (_e, {id}) => notes.del(id)', auth="note: (_e, {id}, ctx) => { if (!ctx.user) throw new Error('unauth'); return notes.get(id, ctx.user) }", leftover='put'),
    dict(slug='apollo-plugin-skip-delete', plant='barnacle', ticket='BAR-2', surface='Apollo Server field delete missing auth directive', family='js_route', skip='type Mutation { deleteNote(id: ID!): Boolean }', auth='type Query { note(id: ID!): Note @auth }', leftover='patch'),
    dict(slug='mercurius-preHandler-skip', plant='barque', ticket='BAR-3', surface='Mercurius preHandler skip leftover on delete', family='js_route', skip="app.graphql.defineMutation('deleteNote', { preHandler: [] }, (_, {id}) => notes.del(id))", auth="app.graphql.defineQuery('note', { preHandler: [auth] }, (_, {id}, ctx) => notes.get(id, ctx.user))", leftover='update'),
    dict(slug='foal-hook-skip-delete', plant='becket', ticket='BEC-4', surface='FoalTS @Delete missing @UseGuard', family='js_route', skip="@Delete('/:id')\nasync delete(ctx: Context) { await Note.delete(ctx.request.params.id) }", auth="@Get('/:id')\n@UseGuard(AuthGuard)\nasync get(ctx: Context) { return Note.get(ctx.request.params.id, ctx.user) }", leftover='put'),
    dict(slug='tsed-useauth-skip-delete', plant='bilge', ticket='BIL-5', surface='Ts.ED delete missing @UseAuth', family='js_route', skip="@Delete('/:id')\ndelete(@PathParams('id') id: string) { return Note.delete(id) }", auth="@Get('/:id')\n@UseAuth(AuthMiddleware)\nget(@PathParams('id') id: string, @User() u: User) { return Note.get(id, u) }", leftover='patch'),
    dict(slug='routing-controllers-skip', plant='bitthead', ticket='BIT-6', surface='routing-controllers delete missing @Authorized', family='js_route', skip="@Delete('/notes/:id')\ndelete(@Param('id') id: string) { return Note.delete(id) }", auth="@Get('/notes/:id')\n@Authorized()\nget(@Param('id') id: string, @CurrentUser() u: User) { return Note.get(id, u) }", leftover='update'),
    dict(slug='analog-endpoint-public-delete', plant='boomvang', ticket='BOO-7', surface='Analog endpoint DELETE missing auth', family='js_route', skip="export const DELETE = defineEventHandler((e) => notes.del(getRouterParam(e, 'id')))", auth="export const GET = defineEventHandler(async (e) => { const u = await requireUser(e); return notes.get(getRouterParam(e, 'id'), u) })", leftover='put'),
    dict(slug='bun-serve-delete-bare', plant='bowse', ticket='BOW-8', surface='Bun.serve DELETE missing auth', family='js_route', skip="if (req.method === 'DELETE') return notes.del(new URL(req.url).pathname)", auth="if (req.method === 'GET') { const u = auth(req); return notes.get(path, u) }", leftover='patch'),
    dict(slug='deno-serve-delete-bare', plant='brigantine', ticket='BRI-9', surface='Deno.serve DELETE missing auth', family='js_route', skip="if (req.method === 'DELETE') return notes.del(url.pathname)", auth="if (req.method === 'GET') { const u = await auth(req); return notes.get(url.pathname, u) }", leftover='update'),
    dict(slug='oak-delete-no-mw', plant='bulkhead', ticket='BUL-1', surface='Oak delete outside auth middleware', family='js_route', skip="router.delete('/notes/:id', (ctx) => notes.del(ctx.params.id))", auth="router.use(auth); router.get('/notes/:id', (ctx) => notes.get(ctx.params.id, ctx.state.user))", leftover='put'),
    dict(slug='aleph-handler-public-delete', plant='bulwark', ticket='BUL-2', surface='Aleph DELETE handler missing auth', family='js_route', skip='export function DELETE(req: Request, ctx: Context) { return notes.del(ctx.params.id) }', auth='export async function GET(req: Request, ctx: Context) { const u = await requireUser(req); return notes.get(ctx.params.id, u) }', leftover='patch'),
    dict(slug='cloudflare-worker-delete-open', plant='camcleat', ticket='CAM-3', surface='Cloudflare Worker DELETE missing auth', family='js_route', skip="if (request.method === 'DELETE') return notes.del(id)", auth="if (request.method === 'GET') { const u = await env.AUTH.verify(request); return notes.get(id, u) }", leftover='update'),
    dict(slug='azure-func-anon-delete', plant='carline', ticket='CAR-4', surface='Azure Function DELETE AuthorizationLevel.Anonymous leftover', family='js_route', skip="[Function('DeleteNote')] HttpResponseData Run([HttpTrigger(AuthorizationLevel.Anonymous, 'delete')]", auth="[Function('GetNote')] HttpResponseData Run([HttpTrigger(AuthorizationLevel.Function, 'get')]", leftover='put'),
    dict(slug='firebase-fn-no-auth-delete', plant='catboat', ticket='CAT-5', surface='Firebase Function delete missing context.auth', family='js_route', skip='exports.deleteNote = functions.https.onRequest((req, res) => notes.del(req.query.id))', auth="exports.getNote = functions.https.onCall((data, ctx) => { if (!ctx.auth) throw new functions.https.HttpsError('unauthenticated','x'); return notes.get(data.id, ctx.auth.uid) })", leftover='patch'),
    dict(slug='appwrite-function-open-delete', plant='chock', ticket='CHO-6', surface='Appwrite function delete missing JWT', family='js_route', skip='export default async ({ req }) => notes.del(req.query.id)', auth="export default async ({ req }) => { const u = req.headers['x-appwrite-user-id']; return notes.get(req.query.id, u) }", leftover='update'),
    dict(slug='pocketbase-hook-skip-delete', plant='coaming', ticket='COA-7', surface='PocketBase OnRecordDelete skip auth', family='js_route', skip='onRecordDelete((e) => { e.next() })', auth='onRecordViewRequest((e) => { if (!e.httpContext.auth) throw new ForbiddenError() })', leftover='put'),
    dict(slug='parse-clp-public-delete', plant='coir', ticket='COI-8', surface='Parse CLP public delete leftover', family='js_route', skip='Note._defaultACL.setPublicWriteAccess(true)', auth='Note._defaultACL.setReadAccess(user, true)', leftover='patch'),
    dict(slug='ghost-content-delete-open', plant='counter', ticket='COU-9', surface='Ghost Content API delete missing staff token', family='js_route', skip="router.delete('/notes/:id', api.notes.destroy)", auth="router.get('/notes/:id', mw.authenticateStaff, api.notes.read)", leftover='update'),
    dict(slug='wordpress-rest-delete-cap', plant='cutwater', ticket='CUT-1', surface='WordPress REST delete missing capability', family='php_mw', skip="register_rest_route('notes/v1', '/(?P<id>[\\d]+)', ['methods'=>'DELETE','callback'=>'notes_delete','permission_callback'=>'__return_true'])", auth="register_rest_route('notes/v1', '/(?P<id>[\\d]+)', ['methods'=>'GET','permission_callback'=>'is_user_logged_in'])", leftover='put'),
    dict(slug='drupal-rest-delete-anon', plant='deadeye', ticket='DEA-2', surface='Drupal REST delete anon leftover', family='php_mw', skip="$config['notes.delete']['auth'] = ['cookie' => 'anon'];", auth="$config['notes.GET']['auth'] = ['cookie' => 'user'];", leftover='patch'),
    dict(slug='joomla-api-delete-public', plant='deadwood', ticket='DEA-3', surface='Joomla Web Services delete public leftover', family='php_mw', skip='<webservice><operation name="delete" public="true"/></webservice>', auth='<webservice><operation name="get" public="false"/></webservice>', leftover='update'),
    dict(slug='magento-webapi-acl-skip', plant='dodger', ticket='DOD-4', surface='Magento webapi ACL skip leftover on delete', family='php_mw', skip='<route url="/V1/notes/:id" method="DELETE"><service class="NoteRepository" method="delete"/><resources><resource ref="anonymous"/></resources></route>', auth='<route url="/V1/notes/:id" method="GET"><resources><resource ref="self"/></resources></route>', leftover='put'),
    dict(slug='prestashop-ws-delete-open', plant='draught', ticket='DRA-5', surface='PrestaShop WS delete missing authentication key scope', family='php_mw', skip="$this->url['delete'] = ['url' => '/notes/{id}', 'auth' => false];", auth="$this->url['get'] = ['url' => '/notes/{id}', 'auth' => true];", leftover='patch'),
    dict(slug='opencart-api-delete-bare', plant='dutchman', ticket='DUT-6', surface='OpenCart API delete missing api_token', family='php_mw', skip="public function delete() { $this->model_note->delete($this->request->get['id']); }", auth="public function get() { $this->checkApiToken(); return $this->model_note->get($this->request->get['id']); }", leftover='update'),
    dict(slug='shopware-acl-skip-delete', plant='fishplate', ticket='FIS-7', surface='Shopware ACL skip leftover on delete', family='php_mw', skip="#[Route(path: '/api/note/{id}', methods: ['DELETE'], defaults: ['_acl' => ['note:delete']])]", auth="#[Route(path: '/api/note/{id}', methods: ['GET'], defaults: ['_acl' => ['note:read'], '_auth' => true])]", leftover='put'),
    dict(slug='saleor-permission-skip', plant='flotsam', ticket='FLO-8', surface='Saleor GraphQL delete missing permission', family='js_route', skip='class DeleteNote(BaseMutation):\n    permissions = []', auth='class Note(ModelObjectType):\n        permissions = [NotePermissions.MANAGE_NOTES]', leftover='patch'),
    dict(slug='medusa-auth-skip-delete', plant='focsle', ticket='FOC-9', surface='Medusa delete missing authenticate middleware', family='js_route', skip="router.delete('/admin/notes/:id', (req, res) => noteService.delete(req.params.id))", auth="router.get('/admin/notes/:id', authenticate(), (req, res) => noteService.retrieve(req.params.id, req.user))", leftover='update'),
    dict(slug='spree-cancan-skip-delete', plant='forepeak', ticket='FOR-1', surface='Spree CanCan skip authorize! on destroy', family='rb_filter', skip='def destroy; @note.destroy; end', auth='def show; authorize! :read, @note; end', leftover='put'),
    dict(slug='solidus-ability-skip-delete', plant='galley', ticket='GAL-2', surface='Solidus Ability skip leftover on destroy', family='rb_filter', skip='can :destroy, Spree::Note', auth='can :read, Spree::Note, user_id: user.id', leftover='patch'),
    dict(slug='sylius-voter-skip-delete', plant='gennaker', ticket='GEN-3', surface='Sylius voter skip leftover on delete', family='php_mw', skip="#[Route('/notes/{id}', methods: ['DELETE'])]\npublic function delete(int $id): Response", auth="#[IsGranted('NOTE_VIEW')]\n#[Route('/notes/{id}', methods: ['GET'])]\npublic function show(int $id): Response", leftover='update'),
    dict(slug='vendure-guard-skip-delete', plant='girtline', ticket='GIR-4', surface='Vendure resolver delete missing @Allow', family='js_route', skip='@Mutation() async deleteNote(id: ID) { return this.noteService.delete(id) }', auth='@Query() @Allow(Permission.Authenticated) async note(id: ID, ctx: RequestContext) { return this.noteService.find(id, ctx) }', leftover='put'),
    dict(slug='umbraco-auth-skip-delete', plant='grabrail', ticket='GRA-5', surface='Umbraco API delete missing [Authorize]', family='cs_attr', skip='[HttpDelete("{id}")] public IActionResult Delete(int id) { _notes.Delete(id); return NoContent(); }', auth='[Authorize] [HttpGet("{id}")] public IActionResult Get(int id) => Ok(_notes.Get(id, User));', leftover='patch'),
    dict(slug='sitecore-authz-skip-delete', plant='gripe', ticket='GRI-6', surface='Sitecore Services Client delete missing Authorize', family='cs_attr', skip='[HttpDelete] public void Delete(string id) { repository.Delete(id); }', auth='[Authorize] [HttpGet] public Item Get(string id) => repository.Get(id, User);', leftover='update'),
    dict(slug='kentico-perm-skip-delete', plant='gudgeon', ticket='GUD-7', surface='Kentico Xperience delete missing permission', family='cs_attr', skip='public void Delete(int id) { noteInfoProvider.Delete(id); }', auth='[Authorize] public NoteInfo Get(int id) => noteInfoProvider.Get(id, User);', leftover='put'),
    dict(slug='optimizely-auth-skip-delete', plant='gunport', ticket='GUN-8', surface='Optimizely CMS delete missing AuthorizeContent', family='cs_attr', skip='[HttpDelete] public ActionResult Delete(int id) { _repo.Delete(id); return NoContent(); }', auth='[AuthorizeContent] [HttpGet] public ActionResult Get(int id) => Ok(_repo.Get(id));', leftover='patch'),
    dict(slug='contentful-mgmt-skip-delete', plant='gybe', ticket='GYB-9', surface='Contentful CMA delete missing space token scope', family='js_route', skip='client.entry.delete({entryId})', auth='client.entry.get({entryId, headers: {Authorization}})', leftover='update'),
    dict(slug='sanity-groq-skip-delete', plant='hance', ticket='HAN-1', surface='Sanity listener delete missing token ACL', family='js_route', skip='client.delete(id)', auth="client.fetch('*[_id==$id && _acl match $user]', {id, user})", leftover='put'),
    dict(slug='forest-smart-skip-delete', plant='hatchcoam', ticket='HAT-2', surface='Forest Admin smart action delete missing permission', family='js_route', skip="collection('notes', { actions: [{ name: 'delete', endpoint: '/forest/notes/delete' }] })", auth="collection('notes', { fields: [{ field: 'id', isReadOnly: true }], segments: ['own'] })", leftover='patch'),
    dict(slug='revel-filter-skip-delete', plant='headstay', ticket='HEA-3', surface='Revel filter skip leftover on Delete', family='go_mw', skip='func (c Notes) Delete(id int) revel.Result { c.Txn.Delete(&Note{Id: id}); return c.NoContent() }', auth='func (c Notes) Show(id int) revel.Result { c.CheckAuth(); return c.RenderJSON(c.Txn.Get(id, c.User)) }', leftover='update'),
    dict(slug='buffalo-mw-skip-delete', plant='helmstock', ticket='HEL-4', surface='Buffalo DELETE outside authorization middleware', family='go_mw', skip='app.DELETE("/notes/{id}", notes.Destroy)', auth='app.Use(Authorization); app.GET("/notes/{id}", notes.Show)', leftover='put'),
    dict(slug='martini-delete-bare', plant='hogframe', ticket='HOG-5', surface='Martini DELETE missing MapAuth', family='go_mw', skip='m.Delete("/notes/:id", func(p martini.Params) { notes.Del(p["id"]) })', auth='m.Get("/notes/:id", MapAuth, func(u User, p martini.Params) { return notes.Get(p["id"], u) })', leftover='patch'),
    dict(slug='negroni-delete-no-mw', plant='jackline', ticket='JAC-6', surface='Negroni DELETE mounted outside JWT middleware', family='go_mw', skip='mux.HandleFunc("/notes/{id}", h.Delete).Methods("DELETE")', auth='n := negroni.New(negroni.HandlerFunc(jwt)); n.UseHandler(getMux)', leftover='update'),
    dict(slug='go-zero-jwt-skip-delete', plant='jibsheet', ticket='JIB-7', surface='go-zero jwt:false leftover on delete', family='go_mw', skip='delete:\n  handler: DeleteNoteHandler\n  jwt: false', auth='get:\n  handler: GetNoteHandler\n  jwt: true', leftover='put'),
    dict(slug='kratos-middleware-skip', plant='kingplank', ticket='KIN-8', surface='go-kratos HTTP delete missing middleware.JWT', family='go_mw', skip='r.DELETE("/notes/{id}", h.Delete)', auth='r.GET("/notes/{id}", middleware.JWT(), h.Get)', leftover='patch'),
    dict(slug='gokit-endpoint-open-delete', plant='knighthead', ticket='KNI-9', surface='Go kit delete endpoint missing AuthMiddleware', family='go_mw', skip='r.Methods("DELETE").Path("/notes/{id}").Handler(httptransport.NewServer(deleteEp, dec, enc))', auth='r.Methods("GET").Path("/notes/{id}").Handler(httptransport.NewServer(authMw(getEp), dec, enc))', leftover='update'),
    dict(slug='goa-security-skip-delete', plant='lateen', ticket='LAT-1', surface='Goa design delete missing Security', family='go_mw', skip='Method("delete", func() { HTTP(func() { DELETE("/notes/{id}") }) })', auth='Method("show", func() { Security(JWT); HTTP(func() { GET("/notes/{id}") }) })', leftover='put'),
    dict(slug='go-restful-filter-skip', plant='leeward', ticket='LEE-2', surface='go-restful delete missing Filter(auth)', family='go_mw', skip='ws.Route(ws.DELETE("/notes/{id}").To(h.Delete))', auth='ws.Route(ws.GET("/notes/{id}").Filter(auth).To(h.Get))', leftover='patch'),
    dict(slug='macaron-delete-bare', plant='limberhole', ticket='LIM-3', surface='Macaron DELETE missing reqAuth', family='go_mw', skip='m.Delete("/notes/:id", h.Delete)', auth='m.Get("/notes/:id", reqAuth, h.Get)', leftover='update'),
    dict(slug='gotham-pipeline-skip-delete', plant='logline', ticket='LOG-4', surface='Gotham pipeline skip leftover on delete', family='rust_ext', skip='fn delete(st: &State) -> (StatusCode, ()) { Note::delete(id(st)); (StatusCode::NO_CONTENT, ()) }', auth='fn get(st: &State) -> (StatusCode, String) { let u = AuthUser::borrow_from(st); Note::get(id(st), u.id) }', leftover='put'),
    dict(slug='nickel-delete-bare', plant='mainsheet', ticket='MAI-5', surface='Nickel delete missing middleware', family='rust_ext', skip='server.delete("/notes/:id", middleware! { |req, res| notes::del(req.param("id").unwrap()) })', auth='server.get("/notes/:id", middleware! { |req, res| { let u = req.user(); notes::get(req.param("id").unwrap(), u) } })', leftover='patch'),
    dict(slug='iron-handler-open-delete', plant='masthead', ticket='MAS-6', surface='Iron handler delete missing BeforeMiddleware', family='rust_ext', skip='router.delete("/notes/:id", delete_note, "delete_note");', auth='chain.link_before(Auth); router.get("/notes/:id", get_note, "get_note");', leftover='update'),
    dict(slug='rouille-delete-bare', plant='oarlock', ticket='OAR-7', surface='rouille DELETE missing session login', family='rust_ext', skip='(DELETE) (/notes/{id: i32}) => { notes::del(id); true }', auth='(GET) (/notes/{id: i32}) => { let u = session.user()?; notes::get(id, u) }', leftover='put'),
    dict(slug='thruster-mw-skip-delete', plant='partnerbeam', ticket='PAR-8', surface='Thruster delete missing auth middleware', family='rust_ext', skip='app.delete("/notes/:id", delete_note);', auth='app.use(auth); app.get("/notes/:id", get_note);', leftover='patch'),
    dict(slug='viz-guard-skip-delete', plant='pintle', ticket='PIN-9', surface='Viz delete missing RequestExt user', family='rust_ext', skip='async fn delete(Path(id): Path<i32>) { Note::delete(id).await }', auth='async fn get(Path(id): Path<i32>, user: User) { Note::get(id, user.id).await }', leftover='update'),
    dict(slug='salvo-hoop-skip-delete', plant='poopdeck', ticket='POO-1', surface='Salvo delete missing hoop auth', family='rust_ext', skip='#[handler] async fn delete(req: &mut Request) { Note::delete(req.param("id").unwrap()).await }', auth='router.push(Router::with_hoop(auth).get(get_note));', leftover='put'),
    dict(slug='ntex-guard-skip-delete', plant='portlight', ticket='POR-2', surface='ntex delete missing Identity extractor', family='rust_ext', skip='async fn delete(path: web::Path<i32>) -> HttpResponse { Note::delete(*path).await; HttpResponse::NoContent().finish() }', auth='async fn get(path: web::Path<i32>, id: Identity) -> HttpResponse { Note::get(*path, id.id()).await }', leftover='patch'),
    dict(slug='loco-auth-skip-delete', plant='quarterbeam', ticket='QUA-3', surface='Loco.rs delete missing auth extractor', family='rust_ext', skip='async fn delete(Path(id): Path<i32>, State(ctx): State<AppContext>) { notes::delete(&ctx, id).await }', auth='async fn get(auth: auth::JWT, Path(id): Path<i32>, State(ctx): State<AppContext>) { notes::get(&ctx, id, auth.user_id).await }', leftover='update'),
    dict(slug='javalin-before-skip-delete', plant='ridingbitt', ticket='RID-4', surface='Javalin delete outside before auth', family='java_ann', skip='app.delete("/notes/{id}", ctx -> notes.delete(ctx.pathParam("id")));', auth='app.before("/notes/*", ctx -> auth(ctx)); app.get("/notes/{id}", ctx -> notes.get(ctx.pathParam("id"), ctx.attribute("user")));', leftover='put'),
    dict(slug='sparkjava-before-skip-delete', plant='rudderhead', ticket='RUD-5', surface='SparkJava delete outside before filter', family='java_ann', skip='delete("/notes/:id", (req, res) -> { notes.delete(req.params(":id")); return ""; });', auth='before("/notes/*", (req, res) -> auth(req)); get("/notes/:id", (req, res) -> notes.get(req.params(":id"), req.attribute("user")));', leftover='patch'),
    dict(slug='ratpack-handler-open-delete', plant='runningback', ticket='RUN-6', surface='Ratpack delete missing byAuth handler', family='java_ann', skip='delete("notes/:id", ctx -> notes.delete(ctx.getPathTokens().get("id")));', auth='get("notes/:id", ctx -> ctx.get(User.class); notes.get(id, user));', leftover='update'),
    dict(slug='helidon-roles-skip-delete', plant='scupper', ticket='SCU-7', surface='Helidon delete missing RolesAllowed', family='java_ann', skip='@DELETE @Path("{id}") public void delete(@PathParam("id") long id) { notes.delete(id); }', auth='@GET @Path("{id}") @RolesAllowed("user") public Note get(@PathParam("id") long id) { return notes.get(id); }', leftover='put'),
    dict(slug='cxf-secure-skip-delete', plant='sheetbend', ticket='SHE-8', surface='Apache CXF delete missing @RolesAllowed', family='java_ann', skip='@DELETE @Path("{id}") public void delete(@PathParam("id") long id) { notes.delete(id); }', auth='@GET @Path("{id}") @RolesAllowed("user") public Note get(@PathParam("id") long id) { return notes.get(id); }', leftover='patch'),
    dict(slug='restlet-guard-skip-delete', plant='spinnaker', ticket='SPI-9', surface='Restlet delete missing ChallengeAuthenticator', family='java_ann', skip='router.attach("/notes/{id}", DeleteNoteServerResource.class);', auth='guard.setNext(GetNoteServerResource.class); router.attach("/notes/{id}", guard);', leftover='update'),
    dict(slug='grails-interceptor-skip', plant='stemson', ticket='STE-1', surface='Grails interceptor except destroy leftover', family='rb_filter', skip="static except = ['destroy']\nboolean before() { true }", auth='def show() { respond noteService.get(params.id, request.user) }', leftover='put'),
    dict(slug='fatfree-route-open-delete', plant='sternpost', ticket='STE-2', surface='Fat-Free Framework DELETE missing auth beacon', family='php_mw', skip="$f3->route('DELETE /notes/@id', 'Note->delete');", auth="$f3->route('GET /notes/@id', 'Note->show'); $f3->set('AUTH', true);", leftover='patch'),
    dict(slug='flightphp-delete-bare', plant='timberhead', ticket='TIM-3', surface='Flight PHP delete missing Flight::auth', family='php_mw', skip="Flight::route('DELETE /notes/@id', function($id){ Note::delete($id); });", auth="Flight::route('GET /notes/@id', function($id){ Flight::auth(); return Note::get($id, Flight::get('user')); });", leftover='update'),
    dict(slug='swoole-http-delete-open', plant='waterway', ticket='WAT-4', surface='Swoole HTTP delete missing session check', family='php_mw', skip="$server->on('request', function ($req, $res) { if ($req->server['request_method']==='DELETE') notes_del($req); });", auth="if ($req->server['request_method']==='GET') { auth($req); notes_get($req); }", leftover='put'),
    dict(slug='workerman-delete-bare', plant='weathercloth', ticket='WEA-5', surface='Workerman HTTP delete missing auth', family='php_mw', skip="if ($request->method() === 'DELETE') return notes_del($request->id);", auth="if ($request->method() === 'GET') { $u = auth($request); return notes_get($request->id, $u); }", leftover='patch'),
    dict(slug='spiral-guard-skip-delete', plant='windward', ticket='WIN-6', surface='Spiral Framework delete missing GuardNamespace', family='php_mw', skip="#[Route('/notes/<id>', methods: 'DELETE')] public function delete(int $id): void", auth="#[Guarded] #[Route('/notes/<id>', methods: 'GET')] public function show(int $id): Note", leftover='update'),
    dict(slug='hyperf-middleware-skip-delete', plant='yawlboat', ticket='YAW-7', surface='Hyperf delete outside auth middleware', family='php_mw', skip="Router::delete('/notes/{id}', 'NoteController@destroy');", auth="Router::addGroup('/notes', function () { Router::get('/{id}', 'NoteController@show'); }, ['middleware' => [AuthMiddleware::class]]);", leftover='put'),
    dict(slug='webman-auth-skip-delete', plant='yokeplate', ticket='YOK-8', surface='Webman delete missing Auth middleware', family='php_mw', skip="Route::delete('/notes/{id}', [NoteController::class, 'destroy']);", auth="Route::group('/notes', function () { Route::get('/{id}', [NoteController::class, 'show']); })->middleware(Auth::class);", leftover='patch'),
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
