"""Extra unique IDOR/BFLA plants for authz-regression-factory r2160+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r2159 vesselNNNN-sys.
Not clones of r2159 ghs-cas / permitio, r2080 hs6-code / karpenter-nd.
"""
from __future__ import annotations


EXTRA_IDOR_ROWS = [
    dict(slug='iso3166-n3-idor', plant='azu00hull', ticket='AZ1-1', surface='ISO 3166-1 numeric object-id IDOR', mod='iso3166n3xs81', model='Iso3166n3xN', lookup='iso3166n3xl81', sample='840', owner='geo_id', first='authn', residual='pdf', product='iso3166-n3', bug='AZ1-1 numeric unique from ISO'),
    dict(slug='iso639-3-idor', plant='azu01hull', ticket='AZ2-2', surface='ISO 639-3 object-id IDOR', mod='iso6393xxxs81', model='Iso6393xxxN', lookup='iso6393xxxl81', sample='eng', owner='lab_id', first='mask', residual='export', product='iso639-3', bug='AZ2-2 code unique from ISO'),
    dict(slug='iso15924-idor', plant='azu02hull', ticket='AZ3-3', surface='ISO 15924 object-id IDOR', mod='iso15924xxs81', model='Iso15924xxN', lookup='iso15924xxl81', sample='Latn', owner='lab_id', first='any_member', residual='search', product='iso15924', bug='AZ3-3 script unique from ISO'),
    dict(slug='iso4217-n-idor', plant='azu03hull', ticket='AZ4-4', surface='ISO 4217 numeric object-id IDOR', mod='iso4217nxxs81', model='Iso4217nxxN', lookup='iso4217nxxl81', sample='840', owner='bank_id', first='list_scope', residual='mget', product='iso4217-n', bug='AZ4-4 numeric unique from ISO'),
    dict(slug='un-m49-sub-idor', plant='azu04hull', ticket='AZ5-5', surface='UN M49 subregion object-id IDOR', mod='unm49subxxs81', model='Unm49subxxN', lookup='unm49subxxl81', sample='021', owner='geo_id', first='authn', residual='csv', product='un-m49-sub', bug='AZ5-5 subregion unique from UNSD'),
    dict(slug='nuts2-idor', plant='azu05hull', ticket='AZ6-6', surface='NUTS2 object-id IDOR', mod='nuts2xxxxxs81', model='Nuts2xxxxxN', lookup='nuts2xxxxxl81', sample='UKI3', owner='geo_id', first='mask', residual='admin', product='nuts2', bug='AZ6-6 NUTS2 unique from Eurostat'),
    dict(slug='lau2-idor', plant='azu06hull', ticket='AZ7-7', surface='LAU2 object-id IDOR', mod='lau2xxxxxxs81', model='Lau2xxxxxxN', lookup='lau2xxxxxxl81', sample='E09000001', owner='geo_id', first='any_member', residual='webhook', product='lau2', bug='AZ7-7 LAU unique from Eurostat'),
    dict(slug='h3r9-idor', plant='azu07hull', ticket='AZ8-8', surface='H3 r9 object-id IDOR', mod='h3r9xxxxxxs81', model='H3r9xxxxxxN', lookup='h3r9xxxxxxl81', sample='89283082bffffff', owner='geo_id', first='list_scope', residual='comments', product='h3-r9', bug='AZ8-8 cell unique from H3'),
    dict(slug='s2token-idor', plant='azu08hull', ticket='AZ9-9', surface='S2 token object-id IDOR', mod='s2tokenxxxs81', model='S2tokenxxxN', lookup='s2tokenxxxl81', sample='89c25a', owner='geo_id', first='authn', residual='pdf', product='s2-token', bug='AZ9-9 token unique from S2'),
    dict(slug='olc10-idor', plant='azu09hull', ticket='AZ1-10', surface='OLC-10 object-id IDOR', mod='olc10xxxxxs81', model='Olc10xxxxxN', lookup='olc10xxxxxl81', sample='8FVC9G8F+6W', owner='geo_id', first='mask', residual='export', product='olc10', bug='AZ1-10 OLC unique from Google'),
    dict(slug='geohash5-idor', plant='azu10hull', ticket='AZ2-11', surface='Geohash-5 object-id IDOR', mod='geohash5xxs81', model='Geohash5xxN', lookup='geohash5xxl81', sample='dr5ru', owner='geo_id', first='any_member', residual='search', product='geohash5', bug='AZ2-11 hash unique from Geohash'),
    dict(slug='what3-lang-idor', plant='azu11hull', ticket='AZ3-12', surface='w3w language object-id IDOR', mod='what3langxs81', model='What3langxN', lookup='what3langxl81', sample='filled.count.soap', owner='geo_id', first='list_scope', residual='mget', product='w3w-lang', bug='AZ3-12 words unique from w3w'),
    dict(slug='iata-area-idor', plant='azu12hull', ticket='AZ4-13', surface='IATA area object-id IDOR', mod='iataareaxxs81', model='IataareaxxN', lookup='iataareaxxl81', sample='1', owner='geo_id', first='authn', residual='csv', product='iata-area', bug='AZ4-13 area unique from IATA'),
    dict(slug='icao-fir2-idor', plant='azu13hull', ticket='AZ5-14', surface='ICAO FIR2 object-id IDOR', mod='icaofir2xxs81', model='Icaofir2xxN', lookup='icaofir2xxl81', sample='KZNY', owner='geo_id', first='mask', residual='admin', product='icao-fir2', bug='AZ5-14 FIR unique from ICAO'),
    dict(slug='unlocode-fun-idor', plant='azu14hull', ticket='AZ6-15', surface='UN/LOCODE function object-id IDOR', mod='unlocodefus81', model='UnlocodefuN', lookup='unlocodeful81', sample='USNYC--3', owner='geo_id', first='any_member', residual='webhook', product='unlocode-fun', bug='AZ6-15 function unique from UNECE'),
    dict(slug='imo-lr-idor', plant='azu15hull', ticket='AZ7-16', surface='IMO LR number object-id IDOR', mod='imolrxxxxxs81', model='ImolrxxxxxN', lookup='imolrxxxxxl81', sample='9074729', owner='mmsi_id', first='list_scope', residual='comments', product='imo-lr', bug='AZ7-16 LR unique from IHS'),
    dict(slug='mmsi-9-idor', plant='azu16hull', ticket='AZ8-17', surface='MMSI-9 object-id IDOR', mod='mmsi9xxxxxs81', model='Mmsi9xxxxxN', lookup='mmsi9xxxxxl81', sample='366123456', owner='mmsi_id', first='authn', residual='pdf', product='mmsi-9', bug='AZ8-17 MMSI unique from ITU'),
    dict(slug='callsign-itu-idor', plant='azu17hull', ticket='AZ9-18', surface='ITU callsign object-id IDOR', mod='callsignits81', model='CallsignitN', lookup='callsignitl81', sample='WDE1234', owner='mmsi_id', first='mask', residual='export', product='callsign-itu', bug='AZ9-18 callsign unique from ITU'),
    dict(slug='imo-csc2-idor', plant='azu18hull', ticket='AZ1-19', surface='IMO CSC2 object-id IDOR', mod='imocsc2xxxs81', model='Imocsc2xxxN', lookup='imocsc2xxxl81', sample='CSC-002', owner='mmsi_id', first='any_member', residual='search', product='imo-csc2', bug='AZ1-19 CSC unique from IMO'),
    dict(slug='iso6346-own-idor', plant='azu19hull', ticket='AZ2-20', surface='ISO6346 owner object-id IDOR', mod='iso6346owns81', model='Iso6346ownN', lookup='iso6346ownl81', sample='MSCU', owner='mmsi_id', first='list_scope', residual='mget', product='iso6346-own', bug='AZ2-20 owner unique from BIC'),
    dict(slug='lei20-v2-idor', plant='azu20hull', ticket='AZ3-21', surface='LEI v2 object-id IDOR', mod='lei20v2xxxs81', model='Lei20v2xxxN', lookup='lei20v2xxxl81', sample='5493001KJTIIGC8Y1R13', owner='bank_id', first='authn', residual='csv', product='lei20-v2', bug='AZ3-21 LEI unique from GLEIF'),
    dict(slug='bic11-v2-idor', plant='azu21hull', ticket='AZ4-22', surface='BIC11 v2 object-id IDOR', mod='bic11v2xxxs81', model='Bic11v2xxxN', lookup='bic11v2xxxl81', sample='CHASUS33XXX', owner='bank_id', first='mask', residual='admin', product='bic11-v2', bug='AZ4-22 BIC unique from SWIFT'),
    dict(slug='iban-de2-idor', plant='azu22hull', ticket='AZ5-23', surface='DE IBAN object-id IDOR', mod='ibande2xxxs81', model='Ibande2xxxN', lookup='ibande2xxxl81', sample='DE89370400440532013001', owner='bank_id', first='any_member', residual='webhook', product='iban-de2', bug='AZ5-23 IBAN unique from ISO'),
    dict(slug='routing-fed-idor', plant='azu23hull', ticket='AZ6-24', surface='Fed routing object-id IDOR', mod='routingfeds81', model='RoutingfedN', lookup='routingfedl81', sample='021000021', owner='bank_id', first='list_scope', residual='comments', product='routing-fed', bug='AZ6-24 routing unique from Fed'),
    dict(slug='ifsc-v2-idor', plant='azu24hull', ticket='AZ7-25', surface='IFSC v2 object-id IDOR', mod='ifscv2xxxxs81', model='Ifscv2xxxxN', lookup='ifscv2xxxxl81', sample='HDFC0000001', owner='bank_id', first='authn', residual='pdf', product='ifsc-v2', bug='AZ7-25 IFSC unique from RBI'),
    dict(slug='bsb-v2-idor', plant='azu25hull', ticket='AZ8-26', surface='BSB v2 object-id IDOR', mod='bsbv2xxxxxs81', model='Bsbv2xxxxxN', lookup='bsbv2xxxxxl81', sample='032-000', owner='bank_id', first='mask', residual='export', product='bsb-v2', bug='AZ8-26 BSB unique from APCA'),
    dict(slug='clabe-v2-idor', plant='azu26hull', ticket='AZ9-27', surface='CLABE v2 object-id IDOR', mod='clabev2xxxs81', model='Clabev2xxxN', lookup='clabev2xxxl81', sample='002010077777777772', owner='bank_id', first='any_member', residual='search', product='clabe-v2', bug='AZ9-27 CLABE unique from Banxico'),
    dict(slug='cbu-v2-idor', plant='azu27hull', ticket='AZ1-28', surface='CBU v2 object-id IDOR', mod='cbuv2xxxxxs81', model='Cbuv2xxxxxN', lookup='cbuv2xxxxxl81', sample='0110599520000012345677', owner='bank_id', first='list_scope', residual='mget', product='cbu-v2', bug='AZ1-28 CBU unique from BCRA'),
    dict(slug='sort-uk2-idor', plant='azu28hull', ticket='AZ2-29', surface='UK sort v2 object-id IDOR', mod='sortuk2xxxs81', model='Sortuk2xxxN', lookup='sortuk2xxxl81', sample='20-00-00', owner='bank_id', first='authn', residual='csv', product='sort-uk2', bug='AZ2-29 sort unique from Pay.UK'),
    dict(slug='aba-chk-idor', plant='azu29hull', ticket='AZ3-30', surface='ABA check object-id IDOR', mod='abachkxxxxs81', model='AbachkxxxxN', lookup='abachkxxxxl81', sample='021000021', owner='bank_id', first='mask', residual='admin', product='aba-chk', bug='AZ3-30 ABA unique from Fed'),
    dict(slug='gtin12-idor', plant='azu30hull', ticket='AZ4-31', surface='GTIN-12 object-id IDOR', mod='gtin12xxxxs81', model='Gtin12xxxxN', lookup='gtin12xxxxl81', sample='012345678905', owner='trade_id', first='any_member', residual='webhook', product='gtin12', bug='AZ4-31 GTIN unique from GS1'),
    dict(slug='gtin8-idor', plant='azu31hull', ticket='AZ5-32', surface='GTIN-8 object-id IDOR', mod='gtin8xxxxxs81', model='Gtin8xxxxxN', lookup='gtin8xxxxxl81', sample='12345670', owner='trade_id', first='list_scope', residual='comments', product='gtin8', bug='AZ5-32 GTIN unique from GS1'),
    dict(slug='sscc18-v2-idor', plant='azu32hull', ticket='AZ6-33', surface='SSCC v2 object-id IDOR', mod='sscc18v2xxs81', model='Sscc18v2xxN', lookup='sscc18v2xxl81', sample='00006141411234567891', owner='trade_id', first='authn', residual='pdf', product='sscc18-v2', bug='AZ6-33 SSCC unique from GS1'),
    dict(slug='gln13-v2-idor', plant='azu33hull', ticket='AZ7-34', surface='GLN v2 object-id IDOR', mod='gln13v2xxxs81', model='Gln13v2xxxN', lookup='gln13v2xxxl81', sample='0614141000006', owner='trade_id', first='mask', residual='export', product='gln13-v2', bug='AZ7-34 GLN unique from GS1'),
    dict(slug='grai-v2-idor', plant='azu34hull', ticket='AZ8-35', surface='GRAI v2 object-id IDOR', mod='graiv2xxxxs81', model='Graiv2xxxxN', lookup='graiv2xxxxl81', sample='8003 0614141 12346', owner='trade_id', first='any_member', residual='search', product='grai-v2', bug='AZ8-35 GRAI unique from GS1'),
    dict(slug='giai-v2-idor', plant='azu35hull', ticket='AZ9-36', surface='GIAI v2 object-id IDOR', mod='giaiv2xxxxs81', model='Giaiv2xxxxN', lookup='giaiv2xxxxl81', sample='8004 0614141ASSET2', owner='trade_id', first='list_scope', residual='mget', product='giai-v2', bug='AZ9-36 GIAI unique from GS1'),
    dict(slug='isbn13-v2-idor', plant='azu36hull', ticket='AZ1-37', surface='ISBN-13 v2 object-id IDOR', mod='isbn13v2xxs81', model='Isbn13v2xxN', lookup='isbn13v2xxl81', sample='9780140449136', owner='lab_id', first='authn', residual='csv', product='isbn13-v2', bug='AZ1-37 ISBN unique from ISO'),
    dict(slug='issn-p-idor', plant='azu37hull', ticket='AZ2-38', surface='ISSN-P object-id IDOR', mod='issnpxxxxxs81', model='IssnpxxxxxN', lookup='issnpxxxxxl81', sample='2049-3630', owner='lab_id', first='mask', residual='admin', product='issn-p', bug='AZ2-38 ISSN unique from ISSN'),
    dict(slug='doi-v2-idor', plant='azu38hull', ticket='AZ3-39', surface='DOI v2 object-id IDOR', mod='doiv2xxxxxs81', model='Doiv2xxxxxN', lookup='doiv2xxxxxl81', sample='10.1038/nature12373', owner='lab_id', first='any_member', residual='webhook', product='doi-v2', bug='AZ3-39 DOI unique from Crossref'),
    dict(slug='orcid-v2-idor', plant='azu39hull', ticket='AZ4-40', surface='ORCID v2 object-id IDOR', mod='orcidv2xxxs81', model='Orcidv2xxxN', lookup='orcidv2xxxl81', sample='0000-0001-5109-3700', owner='lab_id', first='list_scope', residual='comments', product='orcid-v2', bug='AZ4-40 ORCID unique from ORCID'),
    dict(slug='ror-v2-idor', plant='azu40hull', ticket='AZ5-41', surface='ROR v2 object-id IDOR', mod='rorv2xxxxxs81', model='Rorv2xxxxxN', lookup='rorv2xxxxxl81', sample='02jx3x895', owner='lab_id', first='authn', residual='pdf', product='ror-v2', bug='AZ5-41 ROR unique from ROR'),
    dict(slug='isni-v2-idor', plant='azu41hull', ticket='AZ6-42', surface='ISNI v2 object-id IDOR', mod='isniv2xxxxs81', model='Isniv2xxxxN', lookup='isniv2xxxxl81', sample='000000012150090X', owner='lab_id', first='mask', residual='export', product='isni-v2', bug='AZ6-42 ISNI unique from ISO'),
    dict(slug='pmid-v2-idor', plant='azu42hull', ticket='AZ7-43', surface='PMID v2 object-id IDOR', mod='pmidv2xxxxs81', model='Pmidv2xxxxN', lookup='pmidv2xxxxl81', sample='12345678', owner='lab_id', first='any_member', residual='search', product='pmid-v2', bug='AZ7-43 PMID unique from NCBI'),
    dict(slug='pmc-id-idor', plant='azu43hull', ticket='AZ8-44', surface='PMCID object-id IDOR', mod='pmcidxxxxxs81', model='PmcidxxxxxN', lookup='pmcidxxxxxl81', sample='PMC3531190', owner='lab_id', first='list_scope', residual='mget', product='pmc-id', bug='AZ8-44 PMCID unique from NCBI'),
    dict(slug='arxiv-id-idor', plant='azu44hull', ticket='AZ9-45', surface='arXiv id object-id IDOR', mod='arxividxxxs81', model='ArxividxxxN', lookup='arxividxxxl81', sample='1706.03762', owner='lab_id', first='authn', residual='csv', product='arxiv-id', bug='AZ9-45 id unique from arXiv'),
    dict(slug='issn-e-idor', plant='azu45hull', ticket='AZ1-46', surface='ISSN-E object-id IDOR', mod='issnexxxxxs81', model='IssnexxxxxN', lookup='issnexxxxxl81', sample='1476-4687', owner='lab_id', first='mask', residual='admin', product='issn-e', bug='AZ1-46 eISSN unique from ISSN'),
    dict(slug='cas-rn2-idor', plant='azu46hull', ticket='AZ2-47', surface='CAS RN2 object-id IDOR', mod='casrn2xxxxs81', model='Casrn2xxxxN', lookup='casrn2xxxxl81', sample='50-00-0', owner='lab_id', first='any_member', residual='webhook', product='cas-rn2', bug='AZ2-47 CAS unique from CAS'),
    dict(slug='inchi-std2-idor', plant='azu47hull', ticket='AZ3-48', surface='InChI std2 object-id IDOR', mod='inchistd2xs81', model='Inchistd2xN', lookup='inchistd2xl81', sample='InChI=1S/CH2O/c1-2/h1H2', owner='lab_id', first='list_scope', residual='comments', product='inchi-std2', bug='AZ3-48 InChI unique from IUPAC'),
    dict(slug='smiles-iso-idor', plant='azu48hull', ticket='AZ4-49', surface='isomeric SMILES object-id IDOR', mod='smilesisoxs81', model='SmilesisoxN', lookup='smilesisoxl81', sample='C[C@H](N)C(=O)O', owner='lab_id', first='authn', residual='pdf', product='smiles-iso', bug='AZ4-49 SMILES unique from Daylight'),
    dict(slug='pubchem-sid-idor', plant='azu49hull', ticket='AZ5-50', surface='PubChem SID object-id IDOR', mod='pubchemsids81', model='PubchemsidN', lookup='pubchemsidl81', sample='123456789', owner='lab_id', first='mask', residual='export', product='pubchem-sid', bug='AZ5-50 SID unique from NCBI'),
    dict(slug='chembl-tgt-idor', plant='azu50hull', ticket='AZ6-51', surface='ChEMBL target object-id IDOR', mod='chembltgtxs81', model='ChembltgtxN', lookup='chembltgtxl81', sample='CHEMBL203', owner='lab_id', first='any_member', residual='search', product='chembl-tgt', bug='AZ6-51 target unique from EBI'),
    dict(slug='uniprot-ac2-idor', plant='azu51hull', ticket='AZ7-52', surface='UniProt AC2 object-id IDOR', mod='uniprotac2s81', model='Uniprotac2N', lookup='uniprotac2l81', sample='P04637', owner='lab_id', first='list_scope', residual='mget', product='uniprot-ac2', bug='AZ7-52 AC unique from UniProt'),
    dict(slug='ensembl-tr-idor', plant='azu52hull', ticket='AZ8-53', surface='Ensembl transcript object-id IDOR', mod='ensembltrxs81', model='EnsembltrxN', lookup='ensembltrxl81', sample='ENST00000269305', owner='lab_id', first='authn', residual='csv', product='ensembl-tr', bug='AZ8-53 transcript unique from EBI'),
    dict(slug='refseq-nr-idor', plant='azu53hull', ticket='AZ9-54', surface='RefSeq NR object-id IDOR', mod='refseqnrxxs81', model='RefseqnrxxN', lookup='refseqnrxxl81', sample='NR_003286', owner='lab_id', first='mask', residual='admin', product='refseq-nr', bug='AZ9-54 NR unique from NCBI'),
    dict(slug='pdb-entry-idor', plant='azu54hull', ticket='AZ1-55', surface='PDB entry object-id IDOR', mod='pdbentryxxs81', model='PdbentryxxN', lookup='pdbentryxxl81', sample='1TUP', owner='lab_id', first='any_member', residual='webhook', product='pdb-entry', bug='AZ1-55 entry unique from RCSB'),
    dict(slug='go-bp-idor', plant='azu55hull', ticket='AZ2-56', surface='GO BP object-id IDOR', mod='gobpxxxxxxs81', model='GobpxxxxxxN', lookup='gobpxxxxxxl81', sample='GO:0006915', owner='lab_id', first='list_scope', residual='comments', product='go-bp', bug='AZ2-56 term unique from GOC'),
    dict(slug='kegg-path-idor', plant='azu56hull', ticket='AZ3-57', surface='KEGG path object-id IDOR', mod='keggpathxxs81', model='KeggpathxxN', lookup='keggpathxxl81', sample='hsa04115', owner='lab_id', first='authn', residual='pdf', product='kegg-path', bug='AZ3-57 path unique from KEGG'),
    dict(slug='reactome-r-idor', plant='azu57hull', ticket='AZ4-58', surface='Reactome R object-id IDOR', mod='reactomerxs81', model='ReactomerxN', lookup='reactomerxl81', sample='R-HSA-109606', owner='lab_id', first='mask', residual='export', product='reactome-r', bug='AZ4-58 id unique from Reactome'),
    dict(slug='hgnc-id-idor', plant='azu58hull', ticket='AZ5-59', surface='HGNC id object-id IDOR', mod='hgncidxxxxs81', model='HgncidxxxxN', lookup='hgncidxxxxl81', sample='HGNC:11998', owner='lab_id', first='any_member', residual='search', product='hgnc-id', bug='AZ5-59 id unique from HGNC'),
    dict(slug='omim-id-idor', plant='azu59hull', ticket='AZ6-60', surface='OMIM id object-id IDOR', mod='omimidxxxxs81', model='OmimidxxxxN', lookup='omimidxxxxl81', sample='191170', owner='lab_id', first='list_scope', residual='mget', product='omim-id', bug='AZ6-60 id unique from OMIM'),
    dict(slug='mesh-d-idor', plant='azu60hull', ticket='AZ7-61', surface='MeSH D object-id IDOR', mod='meshdxxxxxs81', model='MeshdxxxxxN', lookup='meshdxxxxxl81', sample='D000077', owner='lab_id', first='authn', residual='csv', product='mesh-d', bug='AZ7-61 id unique from NLM'),
    dict(slug='icd10-cm-idor', plant='azu61hull', ticket='AZ8-62', surface='ICD-10-CM object-id IDOR', mod='icd10cmxxxs81', model='Icd10cmxxxN', lookup='icd10cmxxxl81', sample='E11.9', owner='lab_id', first='mask', residual='admin', product='icd10-cm', bug='AZ8-62 code unique from CDC'),
    dict(slug='icd10-pcs-idor', plant='azu62hull', ticket='AZ9-63', surface='ICD-10-PCS object-id IDOR', mod='icd10pcsxxs81', model='Icd10pcsxxN', lookup='icd10pcsxxl81', sample='0DTJ0ZZ', owner='lab_id', first='any_member', residual='webhook', product='icd10-pcs', bug='AZ9-63 code unique from CMS'),
    dict(slug='snomed-fsn-idor', plant='azu63hull', ticket='AZ1-64', surface='SNOMED FSN object-id IDOR', mod='snomedfsnxs81', model='SnomedfsnxN', lookup='snomedfsnxl81', sample='73211009', owner='lab_id', first='list_scope', residual='comments', product='snomed-fsn', bug='AZ1-64 id unique from SNOMED'),
    dict(slug='loinc-num-idor', plant='azu64hull', ticket='AZ2-65', surface='LOINC num object-id IDOR', mod='loincnumxxs81', model='LoincnumxxN', lookup='loincnumxxl81', sample='718-7', owner='lab_id', first='authn', residual='pdf', product='loinc-num', bug='AZ2-65 num unique from Regenstrief'),
    dict(slug='rxnorm-scd-idor', plant='azu65hull', ticket='AZ3-66', surface='RxNorm SCD object-id IDOR', mod='rxnormscdxs81', model='RxnormscdxN', lookup='rxnormscdxl81', sample='198440', owner='lab_id', first='mask', residual='export', product='rxnorm-scd', bug='AZ3-66 SCD unique from NLM'),
    dict(slug='ndc11-v2-idor', plant='azu66hull', ticket='AZ4-67', surface='NDC11 v2 object-id IDOR', mod='ndc11v2xxxs81', model='Ndc11v2xxxN', lookup='ndc11v2xxxl81', sample='00071015523', owner='lab_id', first='any_member', residual='search', product='ndc11-v2', bug='AZ4-67 NDC unique from FDA'),
    dict(slug='unii-v2-idor', plant='azu67hull', ticket='AZ5-68', surface='UNII v2 object-id IDOR', mod='uniiv2xxxxs81', model='Uniiv2xxxxN', lookup='uniiv2xxxxl81', sample='3K9958V90M', owner='lab_id', first='list_scope', residual='mget', product='unii-v2', bug='AZ5-68 UNII unique from FDA'),
    dict(slug='atc5-idor', plant='azu68hull', ticket='AZ6-69', surface='ATC5 object-id IDOR', mod='atc5xxxxxxs81', model='Atc5xxxxxxN', lookup='atc5xxxxxxl81', sample='N02BE01', owner='lab_id', first='authn', residual='csv', product='atc5', bug='AZ6-69 ATC unique from WHO'),
    dict(slug='dailymed-set-idor', plant='azu69hull', ticket='AZ7-70', surface='DailyMed setid object-id IDOR', mod='dailymedses81', model='DailymedseN', lookup='dailymedsel81', sample='a1b2c3d4-e5f6', owner='lab_id', first='mask', residual='admin', product='dailymed-set', bug='AZ7-70 setid unique from NLM'),
    dict(slug='eic-y-idor', plant='azu70hull', ticket='AZ8-71', surface='EIC-Y object-id IDOR', mod='eicyxxxxxxs81', model='EicyxxxxxxN', lookup='eicyxxxxxxl81', sample='10Y1001A1001A83F', owner='grid_id', first='any_member', residual='webhook', product='eic-y', bug='AZ8-71 EIC unique from ENTSO-E'),
    dict(slug='mrid-v2-idor', plant='azu71hull', ticket='AZ9-72', surface='CIM mRID v2 object-id IDOR', mod='mridv2xxxxs81', model='Mridv2xxxxN', lookup='mridv2xxxxl81', sample='_abcdef12-3456', owner='grid_id', first='list_scope', residual='comments', product='mrid-v2', bug='AZ9-72 mRID unique from CIM'),
    dict(slug='eia-gen-idor', plant='azu72hull', ticket='AZ1-73', surface='EIA generator object-id IDOR', mod='eiagenxxxxs81', model='EiagenxxxxN', lookup='eiagenxxxxl81', sample='55322_G1', owner='grid_id', first='authn', residual='pdf', product='eia-gen', bug='AZ1-73 gen unique from EIA'),
    dict(slug='nerc-ba-idor', plant='azu73hull', ticket='AZ2-74', surface='NERC BA object-id IDOR', mod='nercbaxxxxs81', model='NercbaxxxxN', lookup='nercbaxxxxl81', sample='PJM', owner='grid_id', first='mask', residual='export', product='nerc-ba', bug='AZ2-74 BA unique from NERC'),
    dict(slug='oati-ref-idor', plant='azu74hull', ticket='AZ3-75', surface='OATI ref object-id IDOR', mod='oatirefxxxs81', model='OatirefxxxN', lookup='oatirefxxxl81', sample='TAG-001', owner='grid_id', first='any_member', residual='search', product='oati-ref', bug='AZ3-75 ref unique from OATI'),
    dict(slug='naesb-duns2-idor', plant='azu75hull', ticket='AZ4-76', surface='NAESB DUNS2 object-id IDOR', mod='naesbduns2s81', model='Naesbduns2N', lookup='naesbduns2l81', sample='006928774', owner='grid_id', first='list_scope', residual='mget', product='naesb-duns2', bug='AZ4-76 DUNS unique from NAESB'),
    dict(slug='entsoe-eic2-idor', plant='azu76hull', ticket='AZ5-77', surface='ENTSO-E EIC2 object-id IDOR', mod='entsoeeic2s81', model='Entsoeeic2N', lookup='entsoeeic2l81', sample='10X1001A1001A450', owner='grid_id', first='authn', residual='csv', product='entsoe-eic2', bug='AZ5-77 EIC unique from ENTSO-E'),
    dict(slug='wigos-v2-idor', plant='azu77hull', ticket='AZ6-78', surface='WIGOS v2 object-id IDOR', mod='wigosv2xxxs81', model='Wigosv2xxxN', lookup='wigosv2xxxl81', sample='0-20000-0-06611', owner='lab_id', first='mask', residual='admin', product='wigos-v2', bug='AZ6-78 station unique from WMO'),
    dict(slug='wmo-idx2-idor', plant='azu78hull', ticket='AZ7-79', surface='WMO index v2 object-id IDOR', mod='wmoidx2xxxs81', model='Wmoidx2xxxN', lookup='wmoidx2xxxl81', sample='06611', owner='lab_id', first='any_member', residual='webhook', product='wmo-idx2', bug='AZ7-79 index unique from WMO'),
    dict(slug='metar-v2-idor', plant='azu79hull', ticket='AZ8-80', surface='METAR v2 object-id IDOR', mod='metarv2xxxs81', model='Metarv2xxxN', lookup='metarv2xxxl81', sample='KLGA', owner='lab_id', first='list_scope', residual='comments', product='metar-v2', bug='AZ8-80 station unique from ICAO'),
]


BFLA_ROWS = [
    dict(slug='kind-cluster-skip-delete', plant='azu00hull', ticket='AZ1-1', surface='kind cluster delete missing kubeconfig', family='js_route', skip='kind delete cluster --name notes', auth='kind get clusters', leftover='put'),
    dict(slug='k3d-skip-delete', plant='azu01hull', ticket='AZ2-2', surface='k3d cluster delete missing docker', family='js_route', skip='k3d cluster delete notes', auth='k3d cluster list', leftover='patch'),
    dict(slug='k3s-uninst-skip-delete', plant='azu02hull', ticket='AZ3-3', surface='k3s uninstall missing sudoers', family='js_route', skip='k3s-uninstall.sh', auth='k3s kubectl get nodes', leftover='update'),
    dict(slug='rke2-uninst-skip-delete', plant='azu03hull', ticket='AZ4-4', surface='rke2 uninstall missing sudoers', family='js_route', skip='rke2-uninstall.sh', auth='rke2 --version', leftover='put'),
    dict(slug='talos-reset-skip-delete', plant='azu04hull', ticket='AZ5-5', surface='Talos reset missing talosconfig', family='js_route', skip='talosctl reset --system-labels-to-wipe', auth='talosctl health', leftover='patch'),
    dict(slug='rosa-skip-delete', plant='azu05hull', ticket='AZ6-6', surface='ROSA cluster delete missing token', family='js_route', skip='rosa delete cluster --cluster notes --yes', auth='rosa describe cluster notes', leftover='update'),
    dict(slug='eksctl-skip-delete', plant='azu06hull', ticket='AZ7-7', surface='eksctl cluster delete missing aws', family='js_route', skip='eksctl delete cluster --name notes', auth='eksctl get cluster notes', leftover='put'),
    dict(slug='oke-skip-delete', plant='azu07hull', ticket='AZ8-8', surface='OKE cluster delete missing oci', family='js_route', skip='oci ce cluster delete --cluster-id notes --force', auth='oci ce cluster get --cluster-id notes', leftover='patch'),
    dict(slug='do-k8s-skip-delete', plant='azu08hull', ticket='AZ9-9', surface='DOKS delete missing token', family='js_route', skip='doctl kubernetes cluster delete notes -f', auth='doctl kubernetes cluster get notes', leftover='update'),
    dict(slug='linode-lke-skip-delete', plant='azu09hull', ticket='AZ1-10', surface='LKE delete missing token', family='js_route', skip='linode-cli lke cluster-delete notes', auth='linode-cli lke clusters-list', leftover='put'),
    dict(slug='vultr-k8s-skip-delete', plant='azu10hull', ticket='AZ2-11', surface='Vultr k8s delete missing key', family='js_route', skip='vultr-cli kubernetes delete notes', auth='vultr-cli kubernetes get notes', leftover='patch'),
    dict(slug='civo-k3s-skip-delete', plant='azu11hull', ticket='AZ3-12', surface='Civo k3s delete missing token', family='js_route', skip='civo kubernetes delete notes --yes', auth='civo kubernetes show notes', leftover='update'),
    dict(slug='scaleway-kaps-skip-delete', plant='azu12hull', ticket='AZ4-13', surface='Kapsule delete missing token', family='js_route', skip='scw k8s cluster delete notes', auth='scw k8s cluster get notes', leftover='put'),
    dict(slug='ovh-mks-skip-delete', plant='azu13hull', ticket='AZ5-14', surface='OVH MKS delete missing token', family='js_route', skip='ovhcloud k8s delete notes', auth='ovhcloud k8s get notes', leftover='patch'),
    dict(slug='hetzner-k8s-skip-delete', plant='azu14hull', ticket='AZ6-15', surface='Hetzner k8s delete missing token', family='js_route', skip='hcloud k8s delete notes', auth='hcloud k8s describe notes', leftover='update'),
    dict(slug='equinix-skip-delete', plant='azu15hull', ticket='AZ7-16', surface='Equinix metal delete missing token', family='js_route', skip='metal device delete -i notes -f', auth='metal device get -i notes', leftover='put'),
    dict(slug='packet-skip-delete', plant='azu16hull', ticket='AZ8-17', surface='Packet device delete missing token', family='js_route', skip='packet device delete notes --force', auth='packet device get notes', leftover='patch'),
    dict(slug='maas-skip-delete', plant='azu17hull', ticket='AZ9-18', surface='MAAS machine release missing apikey', family='js_route', skip='maas $P machine release notes', auth='maas $P machine read notes', leftover='update'),
    dict(slug='foreman-skip-delete', plant='azu18hull', ticket='AZ1-19', surface='Foreman host delete missing user', family='js_route', skip='hammer host delete --name notes', auth='hammer host info --name notes', leftover='put'),
    dict(slug='satellite-skip-delete', plant='azu19hull', ticket='AZ2-20', surface='Satellite host delete missing user', family='js_route', skip='hammer host delete --name notes', auth='hammer host info --name notes', leftover='patch'),
    dict(slug='spacewalk-skip-delete', plant='azu20hull', ticket='AZ3-21', surface='Spacewalk system delete missing auth', family='js_route', skip='spacecmd system_delete notes', auth='spacecmd system_details notes', leftover='update'),
    dict(slug='uyuni-skip-delete', plant='azu21hull', ticket='AZ4-22', surface='Uyuni system delete missing auth', family='js_route', skip='spacecmd system_delete notes', auth='spacecmd system_list', leftover='put'),
    dict(slug='cobbler-skip-delete', plant='azu22hull', ticket='AZ5-23', surface='Cobbler system remove missing conf', family='js_route', skip='cobbler system remove --name notes', auth='cobbler system report --name notes', leftover='patch'),
    dict(slug='fai-skip-delete', plant='azu23hull', ticket='AZ6-24', surface='FAI class delete missing sudoers', family='js_route', skip='rm /srv/fai/config/class/NOTES', auth='fai-classlist', leftover='update'),
    dict(slug='razor-skip-delete', plant='azu24hull', ticket='AZ7-25', surface='Razor node delete missing auth', family='js_route', skip='razor delete-node --name notes', auth='razor nodes', leftover='put'),
    dict(slug='stacki-skip-delete', plant='azu25hull', ticket='AZ8-26', surface='Stacki host remove missing pal', family='js_route', skip='stack remove host notes', auth='stack list host notes', leftover='patch'),
    dict(slug='xcat-skip-delete', plant='azu26hull', ticket='AZ9-27', surface='xCAT node remove missing policy', family='js_route', skip='rmdef notes', auth='lsdef notes', leftover='update'),
    dict(slug='warewulf-skip-delete', plant='azu27hull', ticket='AZ1-28', surface='Warewulf node delete missing conf', family='js_route', skip='wwctl node delete notes -y', auth='wwctl node list', leftover='put'),
    dict(slug='one-vm-skip-delete', plant='azu28hull', ticket='AZ2-29', surface='OpenNebula VM delete missing token', family='js_route', skip='onevm delete notes', auth='onevm show notes', leftover='patch'),
    dict(slug='ovirt-skip-delete', plant='azu29hull', ticket='AZ3-30', surface='oVirt VM delete missing token', family='js_route', skip="ovirt-shell -E 'remove vm notes'", auth="ovirt-shell -E 'show vm notes'", leftover='update'),
    dict(slug='proxmox-skip-delete', plant='azu30hull', ticket='AZ4-31', surface='Proxmox VM delete missing ticket', family='js_route', skip='qm destroy notes --purge', auth='qm status notes', leftover='put'),
    dict(slug='esxi-skip-delete', plant='azu31hull', ticket='AZ5-32', surface='ESXi VM destroy missing ticket', family='js_route', skip='vim-cmd vmsvc/destroy notes', auth='vim-cmd vmsvc/getallvms', leftover='patch'),
    dict(slug='vcenter-skip-delete', plant='azu32hull', ticket='AZ6-33', surface='vCenter VM destroy missing sso', family='js_route', skip='govc vm.destroy notes', auth='govc vm.info notes', leftover='update'),
    dict(slug='xen-skip-delete', plant='azu33hull', ticket='AZ7-34', surface='Xen VM uninstall missing sudoers', family='js_route', skip='xe vm-uninstall uuid=notes force=true', auth='xe vm-list', leftover='put'),
    dict(slug='xcp-skip-delete', plant='azu34hull', ticket='AZ8-35', surface='XCP-ng VM uninstall missing session', family='js_route', skip='xe vm-uninstall uuid=notes force=true', auth='xe vm-list', leftover='patch'),
    dict(slug='libvirt-skip-delete', plant='azu35hull', ticket='AZ9-36', surface='libvirt undefine missing polkit', family='js_route', skip='virsh undefine notes --remove-all-storage', auth='virsh dumpxml notes', leftover='update'),
    dict(slug='incus-skip-delete', plant='azu36hull', ticket='AZ1-37', surface='Incus instance delete missing unix', family='js_route', skip='incus delete notes --force', auth='incus info notes', leftover='put'),
    dict(slug='lxd-skip-delete', plant='azu37hull', ticket='AZ2-38', surface='LXD instance delete missing unix', family='js_route', skip='lxc delete notes --force', auth='lxc info notes', leftover='patch'),
    dict(slug='lxc-skip-delete', plant='azu38hull', ticket='AZ3-39', surface='LXC destroy missing sudoers', family='js_route', skip='lxc-destroy -n notes -f', auth='lxc-info -n notes', leftover='update'),
    dict(slug='docker-rm-skip-delete', plant='azu39hull', ticket='AZ4-40', surface='docker rm missing socket', family='js_route', skip='docker rm -f notes', auth='docker inspect notes', leftover='put'),
    dict(slug='podman-rm-skip-delete', plant='azu40hull', ticket='AZ5-41', surface='podman rm missing socket', family='js_route', skip='podman rm -f notes', auth='podman inspect notes', leftover='patch'),
    dict(slug='ctr-skip-delete', plant='azu41hull', ticket='AZ6-42', surface='containerd ctr delete missing sock', family='js_route', skip='ctr -n k8s.io containers delete notes', auth='ctr -n k8s.io containers info notes', leftover='update'),
    dict(slug='skopeo-skip-delete', plant='azu42hull', ticket='AZ7-43', surface='skopeo delete missing authfile', family='js_route', skip='skopeo delete docker://notes', auth='skopeo inspect docker://notes', leftover='put'),
    dict(slug='crane-skip-delete', plant='azu43hull', ticket='AZ8-44', surface='crane delete missing creds', family='js_route', skip='crane delete notes', auth='crane manifest notes', leftover='patch'),
    dict(slug='oras-skip-delete', plant='azu44hull', ticket='AZ9-45', surface='oras manifest delete missing token', family='js_route', skip='oras manifest delete notes', auth='oras manifest fetch notes', leftover='update'),
    dict(slug='regctl-skip-delete', plant='azu45hull', ticket='AZ1-46', surface='regctl tag delete missing creds', family='js_route', skip='regctl tag delete notes', auth='regctl manifest get notes', leftover='put'),
    dict(slug='harbor-proj-skip-delete', plant='azu46hull', ticket='AZ2-47', surface='Harbor project delete missing token', family='js_route', skip='curl -X DELETE $HARBOR/api/v2.0/projects/notes', auth='curl -H "Authorization: Bearer $HARBOR" $HARBOR/api/v2.0/projects/notes', leftover='patch'),
    dict(slug='nexus-repo-skip-delete', plant='azu47hull', ticket='AZ3-48', surface='Nexus repo delete missing user', family='js_route', skip='curl -X DELETE $NX/service/rest/v1/repositories/notes', auth='curl -u admin:$NX $NX/service/rest/v1/repositories/notes', leftover='update'),
    dict(slug='artifactory-skip-delete', plant='azu48hull', ticket='AZ4-49', surface='Artifactory repo delete missing token', family='js_route', skip='jf rt repo-delete notes --quiet', auth='jf rt curl /api/repositories/notes', leftover='put'),
    dict(slug='ghcr-skip-delete', plant='azu49hull', ticket='AZ5-50', surface='GHCR package delete missing token', family='js_route', skip='gh api -X DELETE /user/packages/container/notes', auth='gh api /user/packages/container/notes', leftover='patch'),
    dict(slug='ecr-skip-delete', plant='azu50hull', ticket='AZ6-51', surface='ECR repo delete missing aws', family='js_route', skip='aws ecr delete-repository --repository-name notes --force', auth='aws ecr describe-repositories --repository-names notes', leftover='update'),
    dict(slug='gcr-skip-delete', plant='azu51hull', ticket='AZ7-52', surface='GCR image delete missing adc', family='js_route', skip='gcloud container images delete notes --quiet', auth='gcloud container images list-tags notes', leftover='put'),
    dict(slug='acr-skip-delete', plant='azu52hull', ticket='AZ8-53', surface='ACR repo delete missing sp', family='js_route', skip='az acr repository delete -n notes --yes', auth='az acr repository show -n notes', leftover='patch'),
    dict(slug='quay-skip-delete', plant='azu53hull', ticket='AZ9-54', surface='Quay repo delete missing token', family='js_route', skip='curl -X DELETE $QUAY/api/v1/repository/notes', auth='curl -H "Authorization: Bearer $QUAY" $QUAY/api/v1/repository/notes', leftover='update'),
    dict(slug='dockerhub-skip-delete', plant='azu54hull', ticket='AZ1-55', surface='Docker Hub repo delete missing token', family='js_route', skip='curl -X DELETE $DH/v2/repositories/notes', auth='curl -H "Authorization: JWT $DH" $DH/v2/repositories/notes', leftover='put'),
    dict(slug='chartmuseum-skip-delete', plant='azu55hull', ticket='AZ2-56', surface='ChartMuseum chart delete missing basic', family='js_route', skip='curl -X DELETE $CM/api/charts/notes/1.0.0', auth='curl $CM/api/charts/notes', leftover='patch'),
    dict(slug='helm-oci-skip-delete', plant='azu56hull', ticket='AZ3-57', surface='Helm OCI chart delete missing creds', family='js_route', skip='helm uninstall notes', auth='helm status notes', leftover='update'),
    dict(slug='flux-hr-skip-delete', plant='azu57hull', ticket='AZ4-58', surface='Flux HelmRelease delete missing rbac', family='js_route', skip='kubectl delete helmrelease notes', auth='kubectl get helmrelease notes', leftover='put'),
    dict(slug='argo-appset-skip-delete', plant='azu58hull', ticket='AZ5-59', surface='Argo AppSet delete missing rbac', family='js_route', skip='kubectl delete applicationset notes', auth='kubectl get applicationset notes', leftover='patch'),
    dict(slug='crossplane-comp-skip-delete', plant='azu59hull', ticket='AZ6-60', surface='Crossplane Composition delete missing rbac', family='js_route', skip='kubectl delete composition notes', auth='kubectl get composition notes', leftover='update'),
    dict(slug='capi-mach-skip-delete', plant='azu60hull', ticket='AZ7-61', surface='CAPI Machine delete missing rbac', family='js_route', skip='kubectl delete machine notes', auth='kubectl get machine notes', leftover='put'),
    dict(slug='clusterctl-mv-skip-delete', plant='azu61hull', ticket='AZ8-62', surface='clusterctl move delete missing kubeconfig', family='js_route', skip='clusterctl delete --include-crd', auth='clusterctl describe cluster notes', leftover='patch'),
    dict(slug='kamaji-skip-delete', plant='azu62hull', ticket='AZ9-63', surface='Kamaji tcp delete missing rbac', family='js_route', skip='kubectl delete tenantcontrolplane notes', auth='kubectl get tenantcontrolplane notes', leftover='update'),
    dict(slug='vcluster-skip-delete', plant='azu63hull', ticket='AZ1-64', surface='vcluster delete missing kubeconfig', family='js_route', skip='vcluster delete notes', auth='vcluster list', leftover='put'),
    dict(slug='loft-skip-delete', plant='azu64hull', ticket='AZ2-65', surface='Loft space delete missing token', family='js_route', skip='loft delete space notes', auth='loft get space notes', leftover='patch'),
    dict(slug='rancher-cl-skip-delete', plant='azu65hull', ticket='AZ3-66', surface='Rancher cluster delete missing token', family='js_route', skip='rancher cluster delete notes', auth='rancher cluster ls', leftover='update'),
    dict(slug='colima-skip-delete', plant='azu66hull', ticket='AZ4-67', surface='colima delete missing lima', family='js_route', skip='colima delete notes', auth='colima list', leftover='put'),
    dict(slug='lima-skip-delete', plant='azu67hull', ticket='AZ5-68', surface='lima delete missing qemu', family='js_route', skip='limactl delete notes --yes', auth='limactl list', leftover='patch'),
    dict(slug='nerdctl-img-skip-delete', plant='azu68hull', ticket='AZ6-69', surface='nerdctl image rm missing ns', family='js_route', skip='nerdctl rmi notes', auth='nerdctl images', leftover='update'),
    dict(slug='crictl-img-skip-delete', plant='azu69hull', ticket='AZ7-70', surface='crictl rmi missing runtime', family='js_route', skip='crictl rmi notes', auth='crictl images', leftover='put'),
    dict(slug='buildah-img-skip-delete', plant='azu70hull', ticket='AZ8-71', surface='buildah rmi missing storage', family='js_route', skip='buildah rmi notes', auth='buildah images', leftover='patch'),
    dict(slug='podman-img-skip-delete', plant='azu71hull', ticket='AZ9-72', surface='podman rmi missing socket', family='js_route', skip='podman rmi notes', auth='podman images', leftover='update'),
    dict(slug='docker-img-skip-delete', plant='azu72hull', ticket='AZ1-73', surface='docker rmi missing socket', family='js_route', skip='docker rmi notes', auth='docker images', leftover='put'),
    dict(slug='k3d-img-skip-delete', plant='azu73hull', ticket='AZ2-74', surface='k3d image import wipe missing docker', family='js_route', skip='k3d image import notes --cluster c', auth='k3d image list', leftover='patch'),
    dict(slug='kind-img-skip-delete', plant='azu74hull', ticket='AZ3-75', surface='kind load delete missing docker', family='js_route', skip='kind delete cluster --name notes', auth='kind get clusters', leftover='update'),
    dict(slug='k0sctl-skip-delete', plant='azu75hull', ticket='AZ4-76', surface='k0sctl reset missing sudoers', family='js_route', skip='k0sctl reset -c notes.yaml', auth='k0sctl status', leftover='put'),
    dict(slug='talosctl-img-skip-delete', plant='azu76hull', ticket='AZ5-77', surface='talosctl reset images missing talosconfig', family='js_route', skip='talosctl reset --graceful=false', auth='talosctl images', leftover='patch'),
    dict(slug='clusterapi-md-skip-delete', plant='azu77hull', ticket='AZ6-78', surface='CAPI MachineDeployment delete missing rbac', family='js_route', skip='kubectl delete machinedeployment notes', auth='kubectl get machinedeployment notes', leftover='update'),
    dict(slug='minikube-img-skip-delete', plant='azu78hull', ticket='AZ7-79', surface='minikube image rm missing profile', family='js_route', skip='minikube image rm notes', auth='minikube image ls', leftover='put'),
    dict(slug='rancher-d-skip-delete', plant='azu79hull', ticket='AZ8-80', surface='Rancher desktop wipe missing lima', family='js_route', skip='rdctl wipe', auth='rdctl list-settings', leftover='patch'),
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
