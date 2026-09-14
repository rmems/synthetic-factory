"""Extra unique IDOR/BFLA plants for authz-regression-factory r2320+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r2319 vesselNNNN-sys.
Not clones of r2319 tailn-n / powerbi, r2240 iccid-19 / jenkins-job.
"""
from __future__ import annotations


EXTRA_IDOR_ROWS = [
    dict(slug='gtin14-idor', plant='azw00boom', ticket='AZ1-1', surface='GTIN-14 object-id IDOR', mod='gtin14xxxxs83', model='Gtin14xxxxN', lookup='gtin14xxxxl83', sample='00012345678905', owner='trade_id', first='authn', residual='pdf', product='gtin14', bug='AZ1-1 GTIN unique from GS1'),
    dict(slug='itf14-idor', plant='azw01boom', ticket='AZ2-2', surface='ITF-14 object-id IDOR', mod='itf14xxxxxs83', model='Itf14xxxxxN', lookup='itf14xxxxxl83', sample='10012345678907', owner='trade_id', first='mask', residual='export', product='itf14', bug='AZ2-2 ITF unique from GS1'),
    dict(slug='gs1-sscc-idor', plant='azw02boom', ticket='AZ3-3', surface='GS1 SSCC object-id IDOR', mod='gs1ssccxxxs83', model='Gs1ssccxxxN', lookup='gs1ssccxxxl83', sample='00006141411234567891', owner='trade_id', first='any_member', residual='search', product='gs1-sscc', bug='AZ3-3 SSCC unique from GS1'),
    dict(slug='gs1-gdti-idor', plant='azw03boom', ticket='AZ4-4', surface='GS1 GDTI object-id IDOR', mod='gs1gdtixxxs83', model='Gs1gdtixxxN', lookup='gs1gdtixxxl83', sample='2530614141123456789', owner='trade_id', first='list_scope', residual='mget', product='gs1-gdti', bug='AZ4-4 GDTI unique from GS1'),
    dict(slug='gs1-gsin-idor', plant='azw04boom', ticket='AZ5-5', surface='GS1 GSIN object-id IDOR', mod='gs1gsinxxxs83', model='Gs1gsinxxxN', lookup='gs1gsinxxxl83', sample='402061414112345678', owner='trade_id', first='authn', residual='csv', product='gs1-gsin', bug='AZ5-5 GSIN unique from GS1'),
    dict(slug='gs1-cpid-idor', plant='azw05boom', ticket='AZ6-6', surface='GS1 CPID object-id IDOR', mod='gs1cpidxxxs83', model='Gs1cpidxxxN', lookup='gs1cpidxxxl83', sample='80100614141ABC', owner='trade_id', first='mask', residual='admin', product='gs1-cpid', bug='AZ6-6 CPID unique from GS1'),
    dict(slug='gs1-ginc2-idor', plant='azw06boom', ticket='AZ7-7', surface='GS1 GINC2 object-id IDOR', mod='gs1ginc2xxs83', model='Gs1ginc2xxN', lookup='gs1ginc2xxl83', sample='4010614141SHIP2', owner='trade_id', first='any_member', residual='webhook', product='gs1-ginc2', bug='AZ7-7 GINC unique from GS1'),
    dict(slug='gs1-gsrn2-idor', plant='azw07boom', ticket='AZ8-8', surface='GS1 GSRN2 object-id IDOR', mod='gs1gsrn2xxs83', model='Gs1gsrn2xxN', lookup='gs1gsrn2xxl83', sample='80170614141123456789', owner='trade_id', first='list_scope', residual='comments', product='gs1-gsrn2', bug='AZ8-8 GSRN unique from GS1'),
    dict(slug='ean8-idor', plant='azw08boom', ticket='AZ9-9', surface='EAN-8 object-id IDOR', mod='ean8xxxxxxs83', model='Ean8xxxxxxN', lookup='ean8xxxxxxl83', sample='96385074', owner='trade_id', first='authn', residual='pdf', product='ean8', bug='AZ9-9 EAN unique from GS1'),
    dict(slug='upc12-idor', plant='azw09boom', ticket='AZ1-10', surface='UPC-12 object-id IDOR', mod='upc12xxxxxs83', model='Upc12xxxxxN', lookup='upc12xxxxxl83', sample='036000291452', owner='trade_id', first='mask', residual='export', product='upc12', bug='AZ1-10 UPC unique from GS1'),
    dict(slug='isbn10-idor', plant='azw10boom', ticket='AZ2-11', surface='ISBN-10 object-id IDOR', mod='isbn10xxxxs83', model='Isbn10xxxxN', lookup='isbn10xxxxl83', sample='0140449132', owner='lab_id', first='any_member', residual='search', product='isbn10', bug='AZ2-11 ISBN unique from ISO'),
    dict(slug='ismn13-idor', plant='azw11boom', ticket='AZ3-12', surface='ISMN-13 object-id IDOR', mod='ismn13xxxxs83', model='Ismn13xxxxN', lookup='ismn13xxxxl83', sample='9790000000001', owner='lab_id', first='list_scope', residual='mget', product='ismn13', bug='AZ3-12 ISMN unique from ISO'),
    dict(slug='istc-idor', plant='azw12boom', ticket='AZ4-13', surface='ISTC object-id IDOR', mod='istcxxxxxxs83', model='IstcxxxxxxN', lookup='istcxxxxxxl83', sample='0A9-2002-12B4A105-6', owner='lab_id', first='authn', residual='csv', product='istc', bug='AZ4-13 ISTC unique from ISO'),
    dict(slug='isan-v-idor', plant='azw13boom', ticket='AZ5-14', surface='ISAN-V object-id IDOR', mod='isanvxxxxxs83', model='IsanvxxxxxN', lookup='isanvxxxxxl83', sample='0000-0001-8947-0000-8-0000-0000-D', owner='lab_id', first='mask', residual='admin', product='isan-v', bug='AZ5-14 ISAN unique from ISAN'),
    dict(slug='iswc-t-idor', plant='azw14boom', ticket='AZ6-15', surface='ISWC-T object-id IDOR', mod='iswctxxxxxs83', model='IswctxxxxxN', lookup='iswctxxxxxl83', sample='T-000.000.001-0', owner='lab_id', first='any_member', residual='webhook', product='iswc-t', bug='AZ6-15 ISWC unique from CISAC'),
    dict(slug='doi-datacite-idor', plant='azw15boom', ticket='AZ7-16', surface='DataCite DOI object-id IDOR', mod='doidatacits83', model='DoidatacitN', lookup='doidatacitl83', sample='10.5281/zenodo.1234567', owner='lab_id', first='list_scope', residual='comments', product='doi-datacite', bug='AZ7-16 DOI unique from DataCite'),
    dict(slug='ark-id-idor', plant='azw16boom', ticket='AZ8-17', surface='ARK id object-id IDOR', mod='arkidxxxxxs83', model='ArkidxxxxxN', lookup='arkidxxxxxl83', sample='ark:/13030/tf5p30086k', owner='lab_id', first='authn', residual='pdf', product='ark-id', bug='AZ8-17 ARK unique from CDL'),
    dict(slug='urn-isbn-idor', plant='azw17boom', ticket='AZ9-18', surface='URN ISBN object-id IDOR', mod='urnisbnxxxs83', model='UrnisbnxxxN', lookup='urnisbnxxxl83', sample='urn:isbn:0451450523', owner='lab_id', first='mask', residual='export', product='urn-isbn', bug='AZ9-18 URN unique from IETF'),
    dict(slug='viaf-idor', plant='azw18boom', ticket='AZ1-19', surface='VIAF object-id IDOR', mod='viafxxxxxxs83', model='ViafxxxxxxN', lookup='viafxxxxxxl83', sample='102333412', owner='lab_id', first='any_member', residual='search', product='viaf', bug='AZ1-19 VIAF unique from OCLC'),
    dict(slug='lcnaf-idor', plant='azw19boom', ticket='AZ2-20', surface='LCNAF object-id IDOR', mod='lcnafxxxxxs83', model='LcnafxxxxxN', lookup='lcnafxxxxxl83', sample='n79021164', owner='lab_id', first='list_scope', residual='mget', product='lcnaf', bug='AZ2-20 NAF unique from LC'),
    dict(slug='wikidata-q-idor', plant='azw20boom', ticket='AZ3-21', surface='Wikidata Q object-id IDOR', mod='wikidataqxs83', model='WikidataqxN', lookup='wikidataqxl83', sample='Q42', owner='lab_id', first='authn', residual='csv', product='wikidata-q', bug='AZ3-21 Q unique from Wikidata'),
    dict(slug='geonames-id-idor', plant='azw21boom', ticket='AZ4-22', surface='GeoNames id object-id IDOR', mod='geonamesids83', model='GeonamesidN', lookup='geonamesidl83', sample='5128581', owner='geo_id', first='mask', residual='admin', product='geonames-id', bug='AZ4-22 id unique from GeoNames'),
    dict(slug='openalex-idor', plant='azw22boom', ticket='AZ5-23', surface='OpenAlex object-id IDOR', mod='openalexxxs83', model='OpenalexxxN', lookup='openalexxxl83', sample='W2741809807', owner='lab_id', first='any_member', residual='webhook', product='openalex', bug='AZ5-23 id unique from OurResearch'),
    dict(slug='mag-id-idor', plant='azw23boom', ticket='AZ6-24', surface='MAG id object-id IDOR', mod='magidxxxxxs83', model='MagidxxxxxN', lookup='magidxxxxxl83', sample='2149078318', owner='lab_id', first='list_scope', residual='comments', product='mag-id', bug='AZ6-24 id unique from MAG'),
    dict(slug='pmid-ncbi-idor', plant='azw24boom', ticket='AZ7-25', surface='PMID NCBI object-id IDOR', mod='pmidncbixxs83', model='PmidncbixxN', lookup='pmidncbixxl83', sample='12345678', owner='lab_id', first='authn', residual='pdf', product='pmid-ncbi', bug='AZ7-25 PMID unique from NCBI'),
    dict(slug='pmcid-idor', plant='azw25boom', ticket='AZ8-26', surface='PMCID object-id IDOR', mod='pmcidxxxxxs83', model='PmcidxxxxxN', lookup='pmcidxxxxxl83', sample='PMC3531190', owner='lab_id', first='mask', residual='export', product='pmcid', bug='AZ8-26 PMCID unique from NCBI'),
    dict(slug='s2-paper-idor', plant='azw26boom', ticket='AZ9-27', surface='S2 paper object-id IDOR', mod='s2paperxxxs83', model='S2paperxxxN', lookup='s2paperxxxl83', sample='649def34f8be52c8b66281af98ae884c09aef38b', owner='lab_id', first='any_member', residual='search', product='s2-paper', bug='AZ9-27 paper unique from S2'),
    dict(slug='dblp-key-idor', plant='azw27boom', ticket='AZ1-28', surface='DBLP key object-id IDOR', mod='dblpkeyxxxs83', model='DblpkeyxxxN', lookup='dblpkeyxxxl83', sample='journals/cacm/Dijkstra68', owner='lab_id', first='list_scope', residual='mget', product='dblp-key', bug='AZ1-28 key unique from DBLP'),
    dict(slug='cas-rn-idor', plant='azw28boom', ticket='AZ2-29', surface='CAS RN object-id IDOR', mod='casrnxxxxxs83', model='CasrnxxxxxN', lookup='casrnxxxxxl83', sample='64-17-5', owner='lab_id', first='authn', residual='csv', product='cas-rn', bug='AZ2-29 RN unique from CAS'),
    dict(slug='inchikey-idor', plant='azw29boom', ticket='AZ3-30', surface='InChIKey object-id IDOR', mod='inchikeyxxs83', model='InchikeyxxN', lookup='inchikeyxxl83', sample='LFQSCWFLJHTTHZ-UHFFFAOYSA-N', owner='lab_id', first='mask', residual='admin', product='inchikey', bug='AZ3-30 key unique from IUPAC'),
    dict(slug='chembl-id-idor', plant='azw30boom', ticket='AZ4-31', surface='ChEMBL id object-id IDOR', mod='chemblidxxs83', model='ChemblidxxN', lookup='chemblidxxl83', sample='CHEMBL25', owner='lab_id', first='any_member', residual='webhook', product='chembl-id', bug='AZ4-31 id unique from EBI'),
    dict(slug='drugbank-idor', plant='azw31boom', ticket='AZ5-32', surface='DrugBank object-id IDOR', mod='drugbankxxs83', model='DrugbankxxN', lookup='drugbankxxl83', sample='DB00945', owner='lab_id', first='list_scope', residual='comments', product='drugbank', bug='AZ5-32 id unique from DrugBank'),
    dict(slug='rxcui-idor', plant='azw32boom', ticket='AZ6-33', surface='RxCUI object-id IDOR', mod='rxcuixxxxxs83', model='RxcuixxxxxN', lookup='rxcuixxxxxl83', sample='161', owner='lab_id', first='authn', residual='pdf', product='rxcui', bug='AZ6-33 CUI unique from NLM'),
    dict(slug='ndc11-idor', plant='azw33boom', ticket='AZ7-34', surface='NDC-11 object-id IDOR', mod='ndc11xxxxxs83', model='Ndc11xxxxxN', lookup='ndc11xxxxxl83', sample='00071015523', owner='lab_id', first='mask', residual='export', product='ndc11', bug='AZ7-34 NDC unique from FDA'),
    dict(slug='icd11-idor', plant='azw34boom', ticket='AZ8-35', surface='ICD-11 object-id IDOR', mod='icd11xxxxxs83', model='Icd11xxxxxN', lookup='icd11xxxxxl83', sample='5A11', owner='lab_id', first='any_member', residual='search', product='icd11', bug='AZ8-35 code unique from WHO'),
    dict(slug='icd9-cm-idor', plant='azw35boom', ticket='AZ9-36', surface='ICD-9-CM object-id IDOR', mod='icd9cmxxxxs83', model='Icd9cmxxxxN', lookup='icd9cmxxxxl83', sample='250.00', owner='lab_id', first='list_scope', residual='mget', product='icd9-cm', bug='AZ9-36 code unique from CDC'),
    dict(slug='loinc-idor', plant='azw36boom', ticket='AZ1-37', surface='LOINC object-id IDOR', mod='loincxxxxxs83', model='LoincxxxxxN', lookup='loincxxxxxl83', sample='2345-7', owner='lab_id', first='authn', residual='csv', product='loinc', bug='AZ1-37 code unique from Regenstrief'),
    dict(slug='snomed-idor', plant='azw37boom', ticket='AZ2-38', surface='SNOMED object-id IDOR', mod='snomedxxxxs83', model='SnomedxxxxN', lookup='snomedxxxxl83', sample='44054006', owner='lab_id', first='mask', residual='admin', product='snomed', bug='AZ2-38 id unique from SNOMED'),
    dict(slug='mesh-ui-idor', plant='azw38boom', ticket='AZ3-39', surface='MeSH UI object-id IDOR', mod='meshuixxxxs83', model='MeshuixxxxN', lookup='meshuixxxxl83', sample='D003920', owner='lab_id', first='any_member', residual='webhook', product='mesh-ui', bug='AZ3-39 UI unique from NLM'),
    dict(slug='hpo-id-idor', plant='azw39boom', ticket='AZ4-40', surface='HPO id object-id IDOR', mod='hpoidxxxxxs83', model='HpoidxxxxxN', lookup='hpoidxxxxxl83', sample='HP:0001250', owner='lab_id', first='list_scope', residual='comments', product='hpo-id', bug='AZ4-40 id unique from HPO'),
    dict(slug='eco-id-idor', plant='azw40boom', ticket='AZ5-41', surface='ECO id object-id IDOR', mod='ecoidxxxxxs83', model='EcoidxxxxxN', lookup='ecoidxxxxxl83', sample='ECO:0000269', owner='lab_id', first='authn', residual='pdf', product='eco-id', bug='AZ5-41 id unique from ECO'),
    dict(slug='so-id-idor', plant='azw41boom', ticket='AZ6-42', surface='SO id object-id IDOR', mod='soidxxxxxxs83', model='SoidxxxxxxN', lookup='soidxxxxxxl83', sample='SO:0000704', owner='lab_id', first='mask', residual='export', product='so-id', bug='AZ6-42 id unique from SO'),
    dict(slug='ncit-id-idor', plant='azw42boom', ticket='AZ7-43', surface='NCIt id object-id IDOR', mod='ncitidxxxxs83', model='NcitidxxxxN', lookup='ncitidxxxxl83', sample='C4872', owner='lab_id', first='any_member', residual='search', product='ncit-id', bug='AZ7-43 id unique from NCI'),
    dict(slug='ensembl-idor', plant='azw43boom', ticket='AZ8-44', surface='Ensembl gene object-id IDOR', mod='ensemblxxxs83', model='EnsemblxxxN', lookup='ensemblxxxl83', sample='ENSG00000141510', owner='lab_id', first='list_scope', residual='mget', product='ensembl', bug='AZ8-44 gene unique from EBI'),
    dict(slug='refseq-idor', plant='azw44boom', ticket='AZ9-45', surface='RefSeq object-id IDOR', mod='refseqxxxxs83', model='RefseqxxxxN', lookup='refseqxxxxl83', sample='NM_000546.6', owner='lab_id', first='authn', residual='csv', product='refseq', bug='AZ9-45 acc unique from NCBI'),
    dict(slug='genbank-idor', plant='azw45boom', ticket='AZ1-46', surface='GenBank object-id IDOR', mod='genbankxxxs83', model='GenbankxxxN', lookup='genbankxxxl83', sample='U49845.1', owner='lab_id', first='mask', residual='admin', product='genbank', bug='AZ1-46 acc unique from NCBI'),
    dict(slug='uniprot-idor', plant='azw46boom', ticket='AZ2-47', surface='UniProt object-id IDOR', mod='uniprotxxxs83', model='UniprotxxxN', lookup='uniprotxxxl83', sample='P04637', owner='lab_id', first='any_member', residual='webhook', product='uniprot', bug='AZ2-47 AC unique from UniProt'),
    dict(slug='pdb-id-idor', plant='azw47boom', ticket='AZ3-48', surface='PDB id object-id IDOR', mod='pdbidxxxxxs83', model='PdbidxxxxxN', lookup='pdbidxxxxxl83', sample='1TUP', owner='lab_id', first='list_scope', residual='comments', product='pdb-id', bug='AZ3-48 id unique from RCSB'),
    dict(slug='hgnc-idor', plant='azw48boom', ticket='AZ4-49', surface='HGNC object-id IDOR', mod='hgncxxxxxxs83', model='HgncxxxxxxN', lookup='hgncxxxxxxl83', sample='HGNC:11998', owner='lab_id', first='authn', residual='pdf', product='hgnc', bug='AZ4-49 id unique from HGNC'),
    dict(slug='omim-idor', plant='azw49boom', ticket='AZ5-50', surface='OMIM object-id IDOR', mod='omimxxxxxxs83', model='OmimxxxxxxN', lookup='omimxxxxxxl83', sample='191170', owner='lab_id', first='mask', residual='export', product='omim', bug='AZ5-50 id unique from OMIM'),
    dict(slug='clinvar-idor', plant='azw50boom', ticket='AZ6-51', surface='ClinVar object-id IDOR', mod='clinvarxxxs83', model='ClinvarxxxN', lookup='clinvarxxxl83', sample='12345', owner='lab_id', first='any_member', residual='search', product='clinvar', bug='AZ6-51 id unique from NCBI'),
    dict(slug='dbsnp-idor', plant='azw51boom', ticket='AZ7-52', surface='dbSNP object-id IDOR', mod='dbsnpxxxxxs83', model='DbsnpxxxxxN', lookup='dbsnpxxxxxl83', sample='rs7412', owner='lab_id', first='list_scope', residual='mget', product='dbsnp', bug='AZ7-52 rs unique from NCBI'),
    dict(slug='cosmic-idor', plant='azw52boom', ticket='AZ8-53', surface='COSMIC object-id IDOR', mod='cosmicxxxxs83', model='CosmicxxxxN', lookup='cosmicxxxxl83', sample='COSM476', owner='lab_id', first='authn', residual='csv', product='cosmic', bug='AZ8-53 id unique from Sanger'),
    dict(slug='lei-20-idor', plant='azw53boom', ticket='AZ9-54', surface='LEI-20 object-id IDOR', mod='lei20xxxxxs83', model='Lei20xxxxxN', lookup='lei20xxxxxl83', sample='5493001KJTIIGC8Y1R13', owner='bank_id', first='mask', residual='admin', product='lei-20', bug='AZ9-54 LEI unique from GLEIF'),
    dict(slug='bic-8-idor', plant='azw54boom', ticket='AZ1-55', surface='BIC-8 object-id IDOR', mod='bic8xxxxxxs83', model='Bic8xxxxxxN', lookup='bic8xxxxxxl83', sample='CHASUS33', owner='bank_id', first='any_member', residual='webhook', product='bic-8', bug='AZ1-55 BIC unique from SWIFT'),
    dict(slug='iban-idor', plant='azw55boom', ticket='AZ2-56', surface='IBAN object-id IDOR', mod='ibanxxxxxxs83', model='IbanxxxxxxN', lookup='ibanxxxxxxl83', sample='GB82WEST12345698765432', owner='bank_id', first='list_scope', residual='comments', product='iban', bug='AZ2-56 IBAN unique from ISO'),
    dict(slug='swift-bic-idor', plant='azw56boom', ticket='AZ3-57', surface='SWIFT BIC object-id IDOR', mod='swiftbicxxs83', model='SwiftbicxxN', lookup='swiftbicxxl83', sample='BOFAUS3NXXX', owner='bank_id', first='authn', residual='pdf', product='swift-bic', bug='AZ3-57 BIC unique from SWIFT'),
    dict(slug='mic-exch-idor', plant='azw57boom', ticket='AZ4-58', surface='MIC exch object-id IDOR', mod='micexchxxxs83', model='MicexchxxxN', lookup='micexchxxxl83', sample='XLON', owner='bank_id', first='mask', residual='export', product='mic-exch', bug='AZ4-58 MIC unique from ISO'),
    dict(slug='figi-bbg-idor', plant='azw58boom', ticket='AZ5-59', surface='FIGI BBG object-id IDOR', mod='figibbgxxxs83', model='FigibbgxxxN', lookup='figibbgxxxl83', sample='BBG000B9XRY4', owner='bank_id', first='any_member', residual='search', product='figi-bbg', bug='AZ5-59 FIGI unique from Bloomberg'),
    dict(slug='cusip-9-idor', plant='azw59boom', ticket='AZ6-60', surface='CUSIP-9 object-id IDOR', mod='cusip9xxxxs83', model='Cusip9xxxxN', lookup='cusip9xxxxl83', sample='037833100', owner='bank_id', first='list_scope', residual='mget', product='cusip-9', bug='AZ6-60 CUSIP unique from CUSIP'),
    dict(slug='isin-12-idor', plant='azw60boom', ticket='AZ7-61', surface='ISIN-12 object-id IDOR', mod='isin12xxxxs83', model='Isin12xxxxN', lookup='isin12xxxxl83', sample='US0378331005', owner='bank_id', first='authn', residual='csv', product='isin-12', bug='AZ7-61 ISIN unique from ISO'),
    dict(slug='sedol-7-idor', plant='azw61boom', ticket='AZ8-62', surface='SEDOL-7 object-id IDOR', mod='sedol7xxxxs83', model='Sedol7xxxxN', lookup='sedol7xxxxl83', sample='2046251', owner='bank_id', first='mask', residual='admin', product='sedol-7', bug='AZ8-62 SEDOL unique from LSE'),
    dict(slug='wkn-idor', plant='azw62boom', ticket='AZ9-63', surface='WKN object-id IDOR', mod='wknxxxxxxxs83', model='WknxxxxxxxN', lookup='wknxxxxxxxl83', sample='850727', owner='bank_id', first='any_member', residual='webhook', product='wkn', bug='AZ9-63 WKN unique from WM'),
    dict(slug='ticker-idor', plant='azw63boom', ticket='AZ1-64', surface='Ticker object-id IDOR', mod='tickerxxxxs83', model='TickerxxxxN', lookup='tickerxxxxl83', sample='AAPL', owner='bank_id', first='list_scope', residual='comments', product='ticker', bug='AZ1-64 ticker unique from exchange'),
    dict(slug='cik-sec-idor', plant='azw64boom', ticket='AZ2-65', surface='SEC CIK object-id IDOR', mod='ciksecxxxxs83', model='CiksecxxxxN', lookup='ciksecxxxxl83', sample='0000320193', owner='bank_id', first='authn', residual='pdf', product='cik-sec', bug='AZ2-65 CIK unique from SEC'),
    dict(slug='lei-roc-idor', plant='azw65boom', ticket='AZ3-66', surface='LEI ROC object-id IDOR', mod='leirocxxxxs83', model='LeirocxxxxN', lookup='leirocxxxxl83', sample='RA000001', owner='bank_id', first='mask', residual='export', product='lei-roc', bug='AZ3-66 ROC unique from GLEIF'),
    dict(slug='duns-9-idor', plant='azw66boom', ticket='AZ4-67', surface='DUNS-9 object-id IDOR', mod='duns9xxxxxs83', model='Duns9xxxxxN', lookup='duns9xxxxxl83', sample='006928774', owner='bank_id', first='any_member', residual='search', product='duns-9', bug='AZ4-67 DUNS unique from D&B'),
    dict(slug='ein-idor', plant='azw67boom', ticket='AZ5-68', surface='EIN object-id IDOR', mod='einxxxxxxxs83', model='EinxxxxxxxN', lookup='einxxxxxxxl83', sample='94-1349661', owner='bank_id', first='list_scope', residual='mget', product='ein', bug='AZ5-68 EIN unique from IRS'),
    dict(slug='nino-uk-idor', plant='azw68boom', ticket='AZ6-69', surface='NINo object-id IDOR', mod='ninoukxxxxs83', model='NinoukxxxxN', lookup='ninoukxxxxl83', sample='AB123456C', owner='bank_id', first='authn', residual='csv', product='nino-uk', bug='AZ6-69 NINo unique from HMRC'),
    dict(slug='tfn-au-idor', plant='azw69boom', ticket='AZ7-70', surface='TFN object-id IDOR', mod='tfnauxxxxxs83', model='TfnauxxxxxN', lookup='tfnauxxxxxl83', sample='123456782', owner='bank_id', first='mask', residual='admin', product='tfn-au', bug='AZ7-70 TFN unique from ATO'),
    dict(slug='sin-ca-idor', plant='azw70boom', ticket='AZ8-71', surface='SIN object-id IDOR', mod='sincaxxxxxs83', model='SincaxxxxxN', lookup='sincaxxxxxl83', sample='046454286', owner='bank_id', first='any_member', residual='webhook', product='sin-ca', bug='AZ8-71 SIN unique from CRA'),
    dict(slug='imo-7-idor', plant='azw71boom', ticket='AZ9-72', surface='IMO-7 object-id IDOR', mod='imo7xxxxxxs83', model='Imo7xxxxxxN', lookup='imo7xxxxxxl83', sample='9074729', owner='mmsi_id', first='list_scope', residual='comments', product='imo-7', bug='AZ9-72 IMO unique from IMO'),
    dict(slug='mmsi-idor', plant='azw72boom', ticket='AZ1-73', surface='MMSI object-id IDOR', mod='mmsixxxxxxs83', model='MmsixxxxxxN', lookup='mmsixxxxxxl83', sample='366123456', owner='mmsi_id', first='authn', residual='pdf', product='mmsi', bug='AZ1-73 MMSI unique from ITU'),
    dict(slug='callsign-idor', plant='azw73boom', ticket='AZ2-74', surface='Callsign object-id IDOR', mod='callsignxxs83', model='CallsignxxN', lookup='callsignxxl83', sample='N12345', owner='mmsi_id', first='mask', residual='export', product='callsign', bug='AZ2-74 callsign unique from FAA'),
    dict(slug='icao-24-idor', plant='azw74boom', ticket='AZ3-75', surface='ICAO-24 object-id IDOR', mod='icao24xxxxs83', model='Icao24xxxxN', lookup='icao24xxxxl83', sample='a1b2c3', owner='mmsi_id', first='any_member', residual='search', product='icao-24', bug='AZ3-75 addr unique from ICAO'),
    dict(slug='iata-3-idor', plant='azw75boom', ticket='AZ4-76', surface='IATA-3 object-id IDOR', mod='iata3xxxxxs83', model='Iata3xxxxxN', lookup='iata3xxxxxl83', sample='JFK', owner='geo_id', first='list_scope', residual='mget', product='iata-3', bug='AZ4-76 code unique from IATA'),
    dict(slug='iso3166-idor', plant='azw76boom', ticket='AZ5-77', surface='ISO 3166 object-id IDOR', mod='iso3166xxxs83', model='Iso3166xxxN', lookup='iso3166xxxl83', sample='US', owner='geo_id', first='authn', residual='csv', product='iso3166', bug='AZ5-77 alpha unique from ISO'),
    dict(slug='nuts-idor', plant='azw77boom', ticket='AZ6-78', surface='NUTS object-id IDOR', mod='nutsxxxxxxs83', model='NutsxxxxxxN', lookup='nutsxxxxxxl83', sample='UKI', owner='geo_id', first='mask', residual='admin', product='nuts', bug='AZ6-78 NUTS unique from Eurostat'),
    dict(slug='fips-idor', plant='azw78boom', ticket='AZ7-79', surface='FIPS object-id IDOR', mod='fipsxxxxxxs83', model='FipsxxxxxxN', lookup='fipsxxxxxxl83', sample='36061', owner='geo_id', first='any_member', residual='webhook', product='fips', bug='AZ7-79 FIPS unique from Census'),
    dict(slug='nace2-idor', plant='azw79boom', ticket='AZ8-80', surface='NACE2 object-id IDOR', mod='nace2xxxxxs83', model='Nace2xxxxxN', lookup='nace2xxxxxl83', sample='62.01', owner='trade_id', first='list_scope', residual='comments', product='nace2', bug='AZ8-80 NACE unique from Eurostat'),
]


BFLA_ROWS = [
    dict(slug='harness-skip-delete', plant='azw00boom', ticket='AZ1-1', surface='Harness pipeline delete missing token', family='js_route', skip='harness pipeline delete --id notes', auth='harness pipeline get --id notes', leftover='put'),
    dict(slug='rundeck-skip-delete', plant='azw01boom', ticket='AZ2-2', surface='Rundeck job delete missing token', family='js_route', skip='rd jobs delete -i notes', auth='rd jobs info -i notes', leftover='patch'),
    dict(slug='awx-job-skip-delete', plant='azw02boom', ticket='AZ3-3', surface='AWX job delete missing token', family='js_route', skip='awx jobs delete notes', auth='awx jobs get notes', leftover='update'),
    dict(slug='tower-job-skip-delete', plant='azw03boom', ticket='AZ4-4', surface='Tower job delete missing token', family='js_route', skip='tower-cli job delete notes', auth='tower-cli job get notes', leftover='put'),
    dict(slug='semaphore-skip-delete', plant='azw04boom', ticket='AZ5-5', surface='Semaphore project delete missing token', family='js_route', skip='sem project delete notes', auth='sem project info notes', leftover='patch'),
    dict(slug='buddy-skip-delete', plant='azw05boom', ticket='AZ6-6', surface='Buddy pipeline delete missing token', family='js_route', skip='buddy pipeline delete notes', auth='buddy pipeline get notes', leftover='update'),
    dict(slug='codeship-skip-delete', plant='azw06boom', ticket='AZ7-7', surface='Codeship project delete missing token', family='js_route', skip='codeship project delete notes', auth='codeship project get notes', leftover='put'),
    dict(slug='shippable-skip-delete', plant='azw07boom', ticket='AZ8-8', surface='Shippable job delete missing token', family='js_route', skip='shipctl delete job notes', auth='shipctl get job notes', leftover='patch'),
    dict(slug='npm-pkg-skip-delete', plant='azw08boom', ticket='AZ9-9', surface='npm unpublish missing token', family='js_route', skip='npm unpublish notes --force', auth='npm view notes', leftover='update'),
    dict(slug='pypi-pkg-skip-delete', plant='azw09boom', ticket='AZ1-10', surface='PyPI yank missing token', family='js_route', skip='twine yank notes==1.0.0', auth='pip index versions notes', leftover='put'),
    dict(slug='cargo-cr-skip-delete', plant='azw10boom', ticket='AZ2-11', surface='crates.io yank missing token', family='js_route', skip='cargo yank notes --vers 1.0.0', auth='cargo info notes', leftover='patch'),
    dict(slug='maven-ga-skip-delete', plant='azw11boom', ticket='AZ3-12', surface='Maven artifact delete missing token', family='js_route', skip='mvn deploy:delete -Dartifact=notes', auth='mvn help:evaluate -Dartifact=notes', leftover='update'),
    dict(slug='nuget-pkg-skip-delete', plant='azw12boom', ticket='AZ4-13', surface='NuGet delete missing token', family='js_route', skip='nuget delete notes 1.0.0 -NonInteractive', auth='nuget list notes', leftover='put'),
    dict(slug='gem-pkg-skip-delete', plant='azw13boom', ticket='AZ5-14', surface='RubyGems yank missing token', family='js_route', skip='gem yank notes -v 1.0.0', auth='gem info notes', leftover='patch'),
    dict(slug='composer-skip-delete', plant='azw14boom', ticket='AZ6-15', surface='Packagist delete missing token', family='js_route', skip='composer remove notes', auth='composer show notes', leftover='update'),
    dict(slug='go-mod-skip-delete', plant='azw15boom', ticket='AZ7-16', surface='Go module retract missing proxy', family='js_route', skip='go get notes@none', auth='go list -m notes', leftover='put'),
    dict(slug='hex-pkg-skip-delete', plant='azw16boom', ticket='AZ8-17', surface='Hex retire missing token', family='js_route', skip='mix hex.retire notes 1.0.0', auth='mix hex.info notes', leftover='patch'),
    dict(slug='cran-pkg-skip-delete', plant='azw17boom', ticket='AZ9-18', surface='CRAN archive missing key', family='js_route', skip='R CMD REMOVE notes', auth='R -e \'packageVersion("notes")\'', leftover='update'),
    dict(slug='conda-pkg-skip-delete', plant='azw18boom', ticket='AZ1-19', surface='conda remove missing token', family='js_route', skip='conda remove notes -y', auth='conda list notes', leftover='put'),
    dict(slug='apt-pkg-skip-delete', plant='azw19boom', ticket='AZ2-20', surface='apt purge missing sudoers', family='js_route', skip='apt-get purge notes -y', auth='dpkg -s notes', leftover='patch'),
    dict(slug='sops-key-skip-delete', plant='azw20boom', ticket='AZ3-21', surface='sops key delete missing age', family='js_route', skip='sops -d --ignore-mac notes', auth='sops -d notes', leftover='update'),
    dict(slug='sealed-sec-skip-delete', plant='azw21boom', ticket='AZ4-22', surface='SealedSecret delete missing rbac', family='js_route', skip='kubectl delete sealedsecret notes', auth='kubectl get sealedsecret notes', leftover='put'),
    dict(slug='cert-mgr-skip-delete', plant='azw22boom', ticket='AZ5-23', surface='cert-manager Certificate delete missing rbac', family='js_route', skip='kubectl delete certificate notes', auth='kubectl get certificate notes', leftover='patch'),
    dict(slug='ext-sec-skip-delete', plant='azw23boom', ticket='AZ6-24', surface='ExternalSecret delete missing rbac', family='js_route', skip='kubectl delete externalsecret notes', auth='kubectl get externalsecret notes', leftover='update'),
    dict(slug='vault-k8s-skip-delete', plant='azw24boom', ticket='AZ7-25', surface='Vault k8s secret delete missing token', family='js_route', skip='vault kv delete secret/notes', auth='vault kv get secret/notes', leftover='put'),
    dict(slug='aws-sm-skip-delete', plant='azw25boom', ticket='AZ8-26', surface='Secrets Manager delete missing aws', family='js_route', skip='aws secretsmanager delete-secret --secret-id notes --force-delete-without-recovery', auth='aws secretsmanager describe-secret --secret-id notes', leftover='patch'),
    dict(slug='gcp-sm-skip-delete', plant='azw26boom', ticket='AZ9-27', surface='GCP Secret Manager delete missing adc', family='js_route', skip='gcloud secrets delete notes --quiet', auth='gcloud secrets describe notes', leftover='update'),
    dict(slug='az-kv-skip-delete', plant='azw27boom', ticket='AZ1-28', surface='Azure Key Vault secret delete missing sp', family='js_route', skip='az keyvault secret delete --name notes --vault-name v', auth='az keyvault secret show --name notes --vault-name v', leftover='put'),
    dict(slug='lambda-fn-skip-delete', plant='azw28boom', ticket='AZ2-29', surface='Lambda delete missing aws', family='js_route', skip='aws lambda delete-function --function-name notes', auth='aws lambda get-function --function-name notes', leftover='patch'),
    dict(slug='gcf-fn-skip-delete', plant='azw29boom', ticket='AZ3-30', surface='Cloud Functions delete missing adc', family='js_route', skip='gcloud functions delete notes --quiet', auth='gcloud functions describe notes', leftover='update'),
    dict(slug='az-fn-skip-delete', plant='azw30boom', ticket='AZ4-31', surface='Azure Function delete missing sp', family='js_route', skip='az functionapp delete --name notes --resource-group r', auth='az functionapp show --name notes --resource-group r', leftover='put'),
    dict(slug='cf-stack-skip-delete', plant='azw31boom', ticket='AZ5-32', surface='CloudFormation stack delete missing aws', family='js_route', skip='aws cloudformation delete-stack --stack-name notes', auth='aws cloudformation describe-stacks --stack-name notes', leftover='patch'),
    dict(slug='cdk-stack-skip-delete', plant='azw32boom', ticket='AZ6-33', surface='CDK destroy missing aws', family='js_route', skip='cdk destroy notes --force', auth='cdk ls', leftover='update'),
    dict(slug='sam-app-skip-delete', plant='azw33boom', ticket='AZ7-34', surface='SAM delete missing aws', family='js_route', skip='sam delete --stack-name notes --no-prompts', auth='sam list stack-outputs --stack-name notes', leftover='put'),
    dict(slug='serverless-skip-delete', plant='azw34boom', ticket='AZ8-35', surface='Serverless remove missing creds', family='js_route', skip='sls remove --stage notes', auth='sls info --stage notes', leftover='patch'),
    dict(slug='sst-app-skip-delete', plant='azw35boom', ticket='AZ9-36', surface='SST remove missing creds', family='js_route', skip='sst remove --stage notes', auth='sst diff --stage notes', leftover='update'),
    dict(slug='firebase-skip-delete', plant='azw36boom', ticket='AZ1-37', surface='Firebase project delete missing token', family='js_route', skip='firebase projects:delete notes --force', auth='firebase projects:list', leftover='put'),
    dict(slug='supabase-skip-delete', plant='azw37boom', ticket='AZ2-38', surface='Supabase project delete missing token', family='js_route', skip='supabase projects delete notes --yes', auth='supabase projects list', leftover='patch'),
    dict(slug='planetscale-skip-delete', plant='azw38boom', ticket='AZ3-39', surface='PlanetScale db delete missing token', family='js_route', skip='pscale database delete notes --force', auth='pscale database show notes', leftover='update'),
    dict(slug='neon-db-skip-delete', plant='azw39boom', ticket='AZ4-40', surface='Neon project delete missing token', family='js_route', skip='neon projects delete notes', auth='neon projects get notes', leftover='put'),
    dict(slug='render-svc-skip-delete', plant='azw40boom', ticket='AZ5-41', surface='Render service delete missing token', family='js_route', skip='render services delete notes --confirm', auth='render services get notes', leftover='patch'),
    dict(slug='fly-app-skip-delete', plant='azw41boom', ticket='AZ6-42', surface='Fly app destroy missing token', family='js_route', skip='fly apps destroy notes --yes', auth='fly apps show notes', leftover='update'),
    dict(slug='railway-skip-delete', plant='azw42boom', ticket='AZ7-43', surface='Railway project delete missing token', family='js_route', skip='railway delete --yes', auth='railway status', leftover='put'),
    dict(slug='heroku-app-skip-delete', plant='azw43boom', ticket='AZ8-44', surface='Heroku app destroy missing token', family='js_route', skip='heroku apps:destroy notes --confirm notes', auth='heroku apps:info notes', leftover='patch'),
    dict(slug='netlify-skip-delete', plant='azw44boom', ticket='AZ9-45', surface='Netlify site delete missing token', family='js_route', skip='netlify sites:delete notes --force', auth='netlify sites:info notes', leftover='update'),
    dict(slug='vercel-proj-skip-delete', plant='azw45boom', ticket='AZ1-46', surface='Vercel project delete missing token', family='js_route', skip='vercel project rm notes --yes', auth='vercel project ls', leftover='put'),
    dict(slug='cf-pages-skip-delete', plant='azw46boom', ticket='AZ2-47', surface='Cloudflare Pages delete missing token', family='js_route', skip='wrangler pages project delete notes --yes', auth='wrangler pages project list', leftover='patch'),
    dict(slug='amplify-skip-delete', plant='azw47boom', ticket='AZ3-48', surface='Amplify app delete missing aws', family='js_route', skip='aws amplify delete-app --app-id notes', auth='aws amplify get-app --app-id notes', leftover='update'),
    dict(slug='mode-rep-skip-delete', plant='azw48boom', ticket='AZ4-49', surface='Mode report delete missing token', family='js_route', skip='mode report delete notes', auth='mode report get notes', leftover='put'),
    dict(slug='hex-proj-skip-delete', plant='azw49boom', ticket='AZ5-50', surface='Hex project delete missing token', family='js_route', skip='hex project delete notes', auth='hex project get notes', leftover='patch'),
    dict(slug='jupyterhub-skip-delete', plant='azw50boom', ticket='AZ6-51', surface='JupyterHub user delete missing token', family='js_route', skip='jupyterhub-singleuser --delete-user notes', auth='jupyterhub list-users', leftover='update'),
    dict(slug='rstudio-skip-delete', plant='azw51boom', ticket='AZ7-52', surface='RStudio user delete missing sudoers', family='js_route', skip='rstudio-server user-delete notes', auth='rstudio-server user-status notes', leftover='put'),
    dict(slug='vscode-srv-skip-delete', plant='azw52boom', ticket='AZ8-53', surface='code-server session delete missing conf', family='js_route', skip='code-server --shutdown notes', auth='code-server --list-sessions', leftover='patch'),
    dict(slug='codeserver-skip-delete', plant='azw53boom', ticket='AZ9-54', surface='Coder workspace delete missing token', family='js_route', skip='coder delete notes --yes', auth='coder show notes', leftover='update'),
    dict(slug='drone-sec-skip-delete', plant='azw54boom', ticket='AZ1-55', surface='Drone secret delete missing token', family='js_route', skip='drone secret rm --repository notes --name k', auth='drone secret ls --repository notes', leftover='put'),
    dict(slug='yum-pkg-skip-delete', plant='azw55boom', ticket='AZ2-56', surface='yum remove missing sudoers', family='js_route', skip='yum remove notes -y', auth='rpm -q notes', leftover='patch'),
    dict(slug='apk-pkg-skip-delete', plant='azw56boom', ticket='AZ3-57', surface='apk del missing sudoers', family='js_route', skip='apk del notes', auth='apk info notes', leftover='update'),
    dict(slug='nix-pkg-skip-delete', plant='azw57boom', ticket='AZ4-58', surface='nix-env uninstall missing store', family='js_route', skip='nix-env -e notes', auth='nix-env -q notes', leftover='put'),
    dict(slug='brew-pkg-skip-delete', plant='azw58boom', ticket='AZ5-59', surface='brew uninstall missing cellar', family='js_route', skip='brew uninstall notes', auth='brew info notes', leftover='patch'),
    dict(slug='snap-pkg-skip-delete', plant='azw59boom', ticket='AZ6-60', surface='snap remove missing sudoers', family='js_route', skip='snap remove notes', auth='snap info notes', leftover='update'),
    dict(slug='flatpak-skip-delete', plant='azw60boom', ticket='AZ7-61', surface='flatpak uninstall missing sudoers', family='js_route', skip='flatpak uninstall notes -y', auth='flatpak info notes', leftover='put'),
    dict(slug='appimage-skip-delete', plant='azw61boom', ticket='AZ8-62', surface='AppImage remove missing file', family='js_route', skip='rm ~/Applications/notes.AppImage', auth='ls ~/Applications/notes.AppImage', leftover='patch'),
    dict(slug='choco-pkg-skip-delete', plant='azw62boom', ticket='AZ9-63', surface='choco uninstall missing admin', family='js_route', skip='choco uninstall notes -y', auth='choco list notes', leftover='update'),
    dict(slug='winget-skip-delete', plant='azw63boom', ticket='AZ1-64', surface='winget uninstall missing admin', family='js_route', skip='winget uninstall notes', auth='winget show notes', leftover='put'),
    dict(slug='scoop-pkg-skip-delete', plant='azw64boom', ticket='AZ2-65', surface='scoop uninstall missing shim', family='js_route', skip='scoop uninstall notes', auth='scoop info notes', leftover='patch'),
    dict(slug='pacman-skip-delete', plant='azw65boom', ticket='AZ3-66', surface='pacman -R missing sudoers', family='js_route', skip='pacman -Rns notes --noconfirm', auth='pacman -Qi notes', leftover='update'),
    dict(slug='zypper-skip-delete', plant='azw66boom', ticket='AZ4-67', surface='zypper remove missing sudoers', family='js_route', skip='zypper remove -y notes', auth='zypper info notes', leftover='put'),
    dict(slug='portage-skip-delete', plant='azw67boom', ticket='AZ5-68', surface='emerge unmerge missing sudoers', family='js_route', skip='emerge --unmerge notes', auth='equery list notes', leftover='patch'),
    dict(slug='guix-pkg-skip-delete', plant='azw68boom', ticket='AZ6-69', surface='guix remove missing profile', family='js_route', skip='guix remove notes', auth='guix package -I notes', leftover='update'),
    dict(slug='spack-pkg-skip-delete', plant='azw69boom', ticket='AZ7-70', surface='spack uninstall missing db', family='js_route', skip='spack uninstall -y notes', auth='spack find notes', leftover='put'),
    dict(slug='conan-pkg-skip-delete', plant='azw70boom', ticket='AZ8-71', surface='conan remove missing cache', family='js_route', skip='conan remove notes -c', auth='conan list notes', leftover='patch'),
    dict(slug='vcpkg-skip-delete', plant='azw71boom', ticket='AZ9-72', surface='vcpkg remove missing triplet', family='js_route', skip='vcpkg remove notes', auth='vcpkg list notes', leftover='update'),
    dict(slug='bazel-mod-skip-delete', plant='azw72boom', ticket='AZ1-73', surface='Bazel module delete missing cache', family='js_route', skip='bazel clean --expunge', auth='bazel query notes', leftover='put'),
    dict(slug='buck2-skip-delete', plant='azw73boom', ticket='AZ2-74', surface='Buck2 target delete missing conf', family='js_route', skip='buck2 clean', auth='buck2 targets notes', leftover='patch'),
    dict(slug='pants-skip-delete', plant='azw74boom', ticket='AZ3-75', surface='Pants target delete missing conf', family='js_route', skip='pants --change-since=HEAD list notes', auth='pants list notes', leftover='update'),
    dict(slug='gradle-mod-skip-delete', plant='azw75boom', ticket='AZ4-76', surface='Gradle module delete missing cache', family='js_route', skip='gradle :notes:clean', auth='gradle :notes:properties', leftover='put'),
    dict(slug='sbt-mod-skip-delete', plant='azw76boom', ticket='AZ5-77', surface='sbt project delete missing ivy', family='js_route', skip="sbt 'notes/clean'", auth="sbt 'notes/show name'", leftover='patch'),
    dict(slug='lein-mod-skip-delete', plant='azw77boom', ticket='AZ6-78', surface='Leiningen project delete missing maven', family='js_route', skip='lein clean', auth='lein pprint :name', leftover='update'),
    dict(slug='mix-hex-skip-delete', plant='azw78boom', ticket='AZ7-79', surface='Mix deps.delete missing hex', family='js_route', skip='mix deps.clean notes --unlock', auth='mix deps', leftover='put'),
    dict(slug='cabal-pkg-skip-delete', plant='azw79boom', ticket='AZ8-80', surface='Cabal unregister missing ghc', family='js_route', skip='ghc-pkg unregister notes', auth='ghc-pkg describe notes', leftover='patch'),
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
