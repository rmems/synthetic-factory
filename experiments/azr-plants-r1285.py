"""Extra unique IDOR/BFLA plants for authz-regression-factory r1285+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r1284 vesselNNNN-sys.
Not clones of r1284 snomed-concept-idor / emmett-pipeline-skip-delete.
"""
from __future__ import annotations


EXTRA_IDOR_ROWS = [
    dict(slug="icd10-dx-idor", plant="baggywrinkle", ticket="ICD-4", surface="ICD-10-CM diagnosis object-id IDOR", mod="icd10s", model="Icd10", lookup="icd10", sample="E11.9", owner="clinic_id", first="authn", residual="pdf", product="baggywrinkle-icd10-cm", bug="ICD-4 ICD-10-CM unique from EHR chart"),
    dict(slug="cpt-proc-idor", plant="binnacle", ticket="CPT-7", surface="CPT procedure object-id IDOR", mod="cpts", model="Cpt", lookup="cpt", sample="99213", owner="clinic_id", first="mask", residual="export", product="binnacle-cpt-ama", bug="CPT-7 CPT unique from billing"),
    dict(slug="hcpcs-code-idor", plant="bluepeter", ticket="HCP-2", surface="HCPCS code object-id IDOR", mod="hcpcs", model="Hcpcs", lookup="hcpcs", sample="G0438", owner="clinic_id", first="any_member", residual="search", product="bluepeter-hcpcs-cms", bug="HCP-2 HCPCS unique from claims"),
    dict(slug="atc-who-idor", plant="boltrope", ticket="ATC-5", surface="ATC drug class object-id IDOR", mod="atcs", model="Atc", lookup="atc", sample="N02BE01", owner="formulary_id", first="list_scope", residual="mget", product="boltrope-atc-who", bug="ATC-5 ATC unique from WHO DDD"),
    dict(slug="hgnc-symbol-idor", plant="bowline", ticket="HGN-8", surface="HGNC gene symbol object-id IDOR", mod="hgncs", model="Hgnc", lookup="hgnc", sample="TP53", owner="lab_id", first="authn", residual="csv", product="bowline-hgnc-gene", bug="HGN-8 HGNC unique from panel"),
    dict(slug="refseq-np-idor", plant="brail", ticket="RFS-1", surface="RefSeq protein object-id IDOR", mod="refseqs", model="Refseq", lookup="np", sample="NP_000537.3", owner="lab_id", first="mask", residual="admin", product="brail-refseq-np", bug="RFS-1 NP unique from NCBI"),
    dict(slug="clinvar-vcv-idor", plant="burton", ticket="CLV-6", surface="ClinVar VCV object-id IDOR", mod="vcvs", model="Vcv", lookup="vcv", sample="VCV000012345", owner="lab_id", first="any_member", residual="webhook", product="burton-clinvar-vcv", bug="CLV-6 VCV unique from ClinVar"),
    dict(slug="cosmic-cosv-idor", plant="cablet", ticket="COS-3", surface="COSMIC mutation object-id IDOR", mod="cosvs", model="Cosv", lookup="cosv", sample="COSV56056643", owner="lab_id", first="list_scope", residual="comments", product="cablet-cosmic-cosv", bug="COS-3 COSV unique from CGP"),
    dict(slug="dbsnp-rs-idor", plant="camber", ticket="SNP-9", surface="dbSNP rsID object-id IDOR", mod="rsids", model="Rsid", lookup="rsid", sample="rs7412", owner="lab_id", first="authn", residual="pdf", product="camber-dbsnp-rs", bug="SNP-9 rsID unique from dbSNP"),
    dict(slug="ncbi-taxid-idor", plant="carvel", ticket="TAX-2", surface="NCBI TaxID object-id IDOR", mod="taxids", model="Taxid", lookup="taxid", sample="9606", owner="lab_id", first="mask", residual="export", product="carvel-ncbi-tax", bug="TAX-2 TaxID unique from taxonomy"),
    dict(slug="itis-tsn-idor", plant="caulker", ticket="ITS-4", surface="ITIS TSN object-id IDOR", mod="tsns", model="Tsn", lookup="tsn", sample="180092", owner="museum_id", first="any_member", residual="search", product="caulker-itis-tsn", bug="ITS-4 TSN unique from ITIS"),
    dict(slug="gbif-taxon-idor", plant="channels", ticket="GBF-7", surface="GBIF taxon object-id IDOR", mod="gbifs", model="Gbif", lookup="gbif", sample="2440449", owner="museum_id", first="list_scope", residual="mget", product="channels-gbif-tax", bug="GBF-7 GBIF unique from backbone"),
    dict(slug="inat-obs-idor", plant="clinch", ticket="INA-1", surface="iNaturalist observation object-id IDOR", mod="inats", model="Inat", lookup="obs", sample="123456789", owner="project_id", first="authn", residual="csv", product="clinch-inat-obs", bug="INA-1 obs unique from iNat"),
    dict(slug="bold-bin-idor", plant="clinker", ticket="BLD-8", surface="BOLD BIN object-id IDOR", mod="bins", model="Bin", lookup="bin", sample="BOLD:AAA0001", owner="lab_id", first="mask", residual="admin", product="clinker-bold-bin", bug="BLD-8 BIN unique from barcode"),
    dict(slug="worms-aphia-idor", plant="cockbill", ticket="WRM-5", surface="WoRMS AphiaID object-id IDOR", mod="aphias", model="Aphia", lookup="aphia", sample="141433", owner="museum_id", first="any_member", residual="webhook", product="cockbill-worms-aphia", bug="WRM-5 AphiaID unique from WoRMS"),
    dict(slug="ipni-lsid-idor", plant="companionway", ticket="IPN-3", surface="IPNI LSID object-id IDOR", mod="ipnis", model="Ipni", lookup="lsid", sample="urn:lsid:ipni.org:names:30001460-2", owner="herbarium_id", first="list_scope", residual="comments", product="companionway-ipni-lsid", bug="IPN-3 LSID unique from Kew"),
    dict(slug="openalex-work-idor", plant="cordage", ticket="OAW-6", surface="OpenAlex work object-id IDOR", mod="oaworks", model="OaWork", lookup="openalex", sample="W2741809807", owner="campus_id", first="authn", residual="pdf", product="cordage-openalex-w", bug="OAW-6 OpenAlex unique from MAG"),
    dict(slug="s2-corpus-idor", plant="coxswain", ticket="S2C-2", surface="Semantic Scholar corpus object-id IDOR", mod="s2papers", model="S2Paper", lookup="s2id", sample="649def34f8be52c8b66281af98ae884c", owner="campus_id", first="mask", residual="export", product="coxswain-s2-corpus", bug="S2C-2 S2 unique from API"),
    dict(slug="scopus-eid-idor", plant="crowfoot", ticket="SCP-9", surface="Scopus EID object-id IDOR", mod="eids", model="Eid", lookup="eid", sample="2-s2.0-85012345678", owner="campus_id", first="any_member", residual="search", product="crowfoot-scopus-eid", bug="SCP-9 EID unique from Elsevier"),
    dict(slug="wos-ut-idor", plant="decklight", ticket="WOS-4", surface="Web of Science UT object-id IDOR", mod="wosuts", model="WosUt", lookup="ut", sample="WOS:000123456789", owner="campus_id", first="list_scope", residual="mget", product="decklight-wos-ut", bug="WOS-4 UT unique from Clarivate"),
    dict(slug="ieee-artno-idor", plant="dogvane", ticket="IEE-7", surface="IEEE article number object-id IDOR", mod="ieeearts", model="IeeeArt", lookup="artno", sample="8745123", owner="campus_id", first="authn", residual="csv", product="dogvane-ieee-xpl", bug="IEE-7 article unique from Xplore"),
    dict(slug="ismn-score-idor", plant="dunnage", ticket="ISM-1", surface="ISMN score object-id IDOR", mod="ismns", model="Ismn", lookup="ismn", sample="979-0-2600-0043-8", owner="publisher_id", first="mask", residual="admin", product="dunnage-ismn-score", bug="ISM-1 ISMN unique from registration"),
    dict(slug="ipi-base-idor", plant="ensign", ticket="IPI-8", surface="IPI name-number object-id IDOR", mod="ipis", model="Ipi", lookup="ipi", sample="00123456789", owner="society_id", first="any_member", residual="webhook", product="ensign-ipi-base", bug="IPI-8 IPI unique from CISAC"),
    dict(slug="gnd-id-idor", plant="fathom", ticket="GND-3", surface="GND authority object-id IDOR", mod="gnds", model="Gnd", lookup="gnd", sample="118540238", owner="library_id", first="list_scope", residual="comments", product="fathom-gnd-id", bug="GND-3 GND unique from DNB"),
    dict(slug="geonames-geonameid-idor", plant="flake", ticket="GEO-5", surface="GeoNames geonameId object-id IDOR", mod="geonames", model="Geoname", lookup="geonameid", sample="5128581", owner="map_id", first="authn", residual="pdf", product="flake-geonames-id", bug="GEO-5 geonameId unique from dump"),
    dict(slug="osm-way-idor", plant="fluke", ticket="OSM-2", surface="OSM way object-id IDOR", mod="osmways", model="OsmWay", lookup="way", sample="123456789", owner="map_id", first="mask", residual="export", product="fluke-osm-way", bug="OSM-2 way unique from planet"),
    dict(slug="pluscode-plot-idor", plant="footrope", ticket="PLS-6", surface="Plus Code plot object-id IDOR", mod="pluscodes", model="Pluscode", lookup="pluscode", sample="87G8Q2XX+XX", owner="parcel_id", first="any_member", residual="search", product="footrope-plus-code", bug="PLS-6 Plus Code unique from OLC"),
    dict(slug="w3w-square-idor", plant="gaskets", ticket="W3W-9", surface="what3words square object-id IDOR", mod="w3ws", model="W3w", lookup="w3w", sample="filled.count.soap", owner="parcel_id", first="list_scope", residual="mget", product="gaskets-w3w-sq", bug="W3W-9 /// unique from w3w"),
    dict(slug="icao-location-idor", plant="gimbals", ticket="IAL-4", surface="ICAO location indicator object-id IDOR", mod="icaolocs", model="IcaoLoc", lookup="icaoloc", sample="KJFK", owner="network_id", first="authn", residual="csv", product="gimbals-icao-loc", bug="IAL-4 ICAO loc unique from Doc 7910"),
    dict(slug="mmsi-radio-idor", plant="grommet", ticket="MMS-7", surface="MMSI radio identity object-id IDOR", mod="mmsis", model="Mmsi", lookup="mmsi", sample="367123456", owner="fleet_id", first="mask", residual="admin", product="grommet-mmsi-radio", bug="MMS-7 MMSI unique from ITU M.585"),
    dict(slug="hin-hull-idor", plant="guyline", ticket="HIN-1", surface="HIN hull identity object-id IDOR", mod="hins", model="Hin", lookup="hin", sample="ABC12345A323", owner="yard_id", first="any_member", residual="webhook", product="guyline-hin-hull", bug="HIN-1 HIN unique from USCG"),
    dict(slug="uic-wagon-idor", plant="hank", ticket="UIC-8", surface="UIC wagon number object-id IDOR", mod="uics", model="Uic", lookup="uic", sample="31801234567", owner="fleet_id", first="list_scope", residual="comments", product="hank-uic-wagon", bug="UIC-8 wagon unique from TSI"),
    dict(slug="evn-rail-idor", plant="hawser", ticket="EVN-3", surface="EVN rolling-stock object-id IDOR", mod="evns", model="Evn", lookup="evn", sample="918012345672", owner="fleet_id", first="authn", residual="pdf", product="hawser-evn-rail", bug="EVN-3 EVN unique from ERA"),
    dict(slug="clabe-transfer-idor", plant="holystone", ticket="CLB-5", surface="CLABE transfer object-id IDOR", mod="clabes", model="Clabe", lookup="clabe", sample="032180000118359719", owner="bank_id", first="mask", residual="export", product="holystone-clabe-mx", bug="CLB-5 CLABE unique from Banxico"),
    dict(slug="ifsc-payout-idor", plant="inhaul", ticket="IFS-2", surface="IFSC payout object-id IDOR", mod="ifscs", model="Ifsc", lookup="ifsc", sample="HDFC0001234", owner="bank_id", first="any_member", residual="search", product="inhaul-ifsc-in", bug="IFS-2 IFSC unique from NPCI"),
    dict(slug="bsb-payout-idor", plant="jackyard", ticket="BSB-6", surface="BSB payout object-id IDOR", mod="bsbs", model="Bsb", lookup="bsb", sample="062-000", owner="bank_id", first="list_scope", residual="mget", product="jackyard-bsb-au", bug="BSB-6 BSB unique from APCA"),
    dict(slug="iin-bin-idor", plant="kedge", ticket="IIN-9", surface="IIN BIN range object-id IDOR", mod="iins", model="Iin", lookup="iin", sample="411111", owner="issuer_id", first="authn", residual="csv", product="kedge-iin-bin", bug="IIN-9 IIN unique from ISO 7812"),
    dict(slug="imei-handset-idor", plant="kevel", ticket="IME-4", surface="IMEI handset object-id IDOR", mod="imeis", model="Imei", lookup="imei", sample="490154203237518", owner="account_id", first="mask", residual="admin", product="kevel-imei-gsma", bug="IME-4 IMEI unique from GSMA"),
    dict(slug="meid-handset-idor", plant="lanyard", ticket="MEI-8", surface="MEID handset object-id IDOR", mod="meids", model="Meid", lookup="meid", sample="A100000092E340", owner="account_id", first="any_member", residual="webhook", product="lanyard-meid-3gpp", bug="MEI-8 MEID unique from 3GPP2"),
    dict(slug="twilio-msgsid-idor", plant="leeboard", ticket="TWM-1", surface="Twilio MessageSid object-id IDOR", mod="tmsgs", model="Tmsg", lookup="msgsid", sample="SMaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", owner="account_sid", first="list_scope", residual="comments", product="leeboard-twilio-msg", bug="TWM-1 MessageSid unique from SMS"),
    dict(slug="sentry-group-idor", plant="messenger", ticket="SEN-7", surface="Sentry group object-id IDOR", mod="sgroups", model="Sgroup", lookup="groupid", sample="4512345678", owner="org_id", first="authn", residual="pdf", product="messenger-sentry-grp", bug="SEN-7 group unique from issues"),
    dict(slug="pagerduty-inc-idor", plant="mooring", ticket="PDI-3", surface="PagerDuty incident object-id IDOR", mod="pdincs", model="Pdinc", lookup="pdinc", sample="PT1ABCDEF", owner="service_id", first="mask", residual="export", product="mooring-pd-inc", bug="PDI-3 incident unique from PD"),
    dict(slug="zendesk-tid-idor", plant="nipper", ticket="ZDT-5", surface="Zendesk ticket object-id IDOR", mod="zdtids", model="Zdtid", lookup="tid", sample="184221", owner="brand_id", first="any_member", residual="search", product="nipper-zd-tid", bug="ZDT-5 ticket unique from Support"),
    dict(slug="servicenow-inc-idor", plant="orlop", ticket="SNW-2", surface="ServiceNow incident object-id IDOR", mod="snincs", model="Sninc", lookup="number", sample="INC0010123", owner="instance_id", first="list_scope", residual="mget", product="orlop-snow-inc", bug="SNW-2 INC unique from ITSM"),
    dict(slug="linear-issuekey-idor", plant="painter", ticket="LIN-6", surface="Linear issue identifier object-id IDOR", mod="liniss", model="Liniss", lookup="issuekey", sample="ENG-2048", owner="team_id", first="authn", residual="csv", product="painter-lin-key", bug="LIN-6 issue unique from GraphQL id"),
    dict(slug="notion-block-idor", plant="parbuckle", ticket="NOT-9", surface="Notion block object-id IDOR", mod="nblocks", model="Nblock", lookup="blockid", sample="1a2b3c4d5e6f4780a1b2c3d4e5f60718", owner="ws_id", first="mask", residual="admin", product="parbuckle-notion-blk", bug="NOT-9 block unique from API"),
    dict(slug="ksuid-row-idor", plant="pendant", ticket="KSU-4", surface="KSUID row object-id IDOR", mod="ksuids", model="Ksuid", lookup="ksuid", sample="0ujtsYcgvSTl8PAuAdqWYSMnLOv", owner="org_id", first="any_member", residual="webhook", product="pendant-ksuid-row", bug="KSU-4 KSUID unique from segment"),
    dict(slug="typeid-row-idor", plant="afterdeck", ticket="TYP-1", surface="TypeID row object-id IDOR", mod="typeids", model="Typeid", lookup="typeid", sample="user_01h45ytscbebyvny4gc8cr8ma2", owner="org_id", first="list_scope", residual="comments", product="afterdeck-typeid-row", bug="TYP-1 TypeID unique from jetify"),
    dict(slug="cuid2-row-idor", plant="preventer", ticket="CUI-8", surface="CUID2 row object-id IDOR", mod="cuid2s", model="Cuid2", lookup="cuid2", sample="tz4a98xxat96iws9zmbrgj3a", owner="org_id", first="authn", residual="pdf", product="preventer-cuid2-row", bug="CUI-8 CUID2 unique from parallel"),
    dict(slug="paypal-cap-idor", plant="rabbet", ticket="PPL-3", surface="PayPal capture object-id IDOR", mod="ppcaps", model="Ppcap", lookup="capture", sample="8AB12345CD678901E", owner="merchant_id", first="mask", residual="export", product="rabbet-pp-cap", bug="PPL-3 capture unique from v2"),
    dict(slug="adyen-pspref-idor", plant="ribband", ticket="ADY-7", surface="Adyen pspReference object-id IDOR", mod="adyens", model="Adyen", lookup="pspref", sample="8515501234567890", owner="merchant_id", first="any_member", residual="search", product="ribband-adyen-psp", bug="ADY-7 pspReference unique from checkout"),
    dict(slug="plaid-item-idor", plant="roband", ticket="PLD-2", surface="Plaid item object-id IDOR", mod="plaiditems", model="PlaidItem", lookup="itemid", sample="item-sandbox-12345", owner="client_id", first="list_scope", residual="mget", product="roband-plaid-item", bug="PLD-2 item unique from Link"),
    dict(slug="chargebee-subid-idor", plant="rowlock", ticket="CHB-5", surface="Chargebee subscription object-id IDOR", mod="cbsubs", model="Cbsub", lookup="subid", sample="16BXkLUqD3uK", owner="site_id", first="authn", residual="csv", product="rowlock-cb-sub", bug="CHB-5 sub unique from hosted pages"),
    dict(slug="chebi-id-idor", plant="scuttle", ticket="CHE-6", surface="ChEBI compound object-id IDOR", mod="chebis", model="Chebi", lookup="chebi", sample="CHEBI:15377", owner="lab_id", first="mask", residual="admin", product="scuttle-chebi-id", bug="CHE-6 ChEBI unique from EBI"),
    dict(slug="kegg-cid-idor", plant="seacock", ticket="KEG-9", surface="KEGG compound object-id IDOR", mod="keggcs", model="Keggc", lookup="cid", sample="C00031", owner="lab_id", first="any_member", residual="webhook", product="seacock-kegg-c", bug="KEG-9 C number unique from KEGG"),
    dict(slug="reactome-st-idor", plant="sheerstrake", ticket="REA-4", surface="Reactome pathway object-id IDOR", mod="reactomes", model="Reactome", lookup="stid", sample="R-HSA-109581", owner="lab_id", first="list_scope", residual="comments", product="sheerstrake-reactome-st", bug="REA-4 STID unique from Reactome"),
    dict(slug="go-id-idor", plant="shroud", ticket="GOI-1", surface="Gene Ontology term object-id IDOR", mod="goterms", model="Goterm", lookup="goid", sample="GO:0006915", owner="lab_id", first="authn", residual="pdf", product="shroud-go-id", bug="GOI-1 GO unique from AmiGO"),
    dict(slug="ec-number-idor", plant="skeg", ticket="ECN-8", surface="EC enzyme number object-id IDOR", mod="ecs", model="Ec", lookup="ec", sample="1.1.1.1", owner="lab_id", first="mask", residual="export", product="skeg-ec-num", bug="ECN-8 EC unique from ExplorEnz"),
    dict(slug="rhea-id-idor", plant="slabline", ticket="RHE-3", surface="Rhea reaction object-id IDOR", mod="rheas", model="Rhea", lookup="rhea", sample="12345", owner="lab_id", first="any_member", residual="search", product="slabline-rhea-id", bug="RHE-3 Rhea unique from UniProt"),
    dict(slug="interpro-id-idor", plant="snorter", ticket="IPR-7", surface="InterPro family object-id IDOR", mod="ipros", model="Ipro", lookup="ipr", sample="IPR000719", owner="lab_id", first="list_scope", residual="mget", product="snorter-interpro-id", bug="IPR-7 IPR unique from EBI"),
    dict(slug="pfam-acc-idor", plant="spanker", ticket="PFM-2", surface="Pfam accession object-id IDOR", mod="pfams", model="Pfam", lookup="pfam", sample="PF00069", owner="lab_id", first="authn", residual="csv", product="spanker-pfam-acc", bug="PFM-2 PF unique from HMMER"),
    dict(slug="hmdb-id-idor", plant="spencer", ticket="HMD-5", surface="HMDB metabolite object-id IDOR", mod="hmdbs", model="Hmdb", lookup="hmdb", sample="HMDB0000122", owner="lab_id", first="mask", residual="admin", product="spencer-hmdb-id", bug="HMD-5 HMDB unique from Wishart"),
    dict(slug="mondo-id-idor", plant="stanchion", ticket="MON-6", surface="Mondo disease object-id IDOR", mod="mondos", model="Mondo", lookup="mondo", sample="MONDO:0005148", owner="clinic_id", first="any_member", residual="webhook", product="stanchion-mondo-id", bug="MON-6 Mondo unique from Monarch"),
    dict(slug="hp-term-idor", plant="steeve", ticket="HPO-9", surface="HPO phenotype object-id IDOR", mod="hpos", model="Hpo", lookup="hp", sample="HP:0000118", owner="clinic_id", first="list_scope", residual="comments", product="steeve-hpo-term", bug="HPO-9 HP unique from Monarch"),
    dict(slug="uberon-id-idor", plant="stopper", ticket="UBE-4", surface="UBERON anatomy object-id IDOR", mod="uberons", model="Uberon", lookup="uberon", sample="UBERON:0000948", owner="lab_id", first="authn", residual="pdf", product="stopper-uberon-id", bug="UBE-4 UBERON unique from ontology"),
    dict(slug="orphanet-id-idor", plant="stringer", ticket="ORP-1", surface="Orphanet disorder object-id IDOR", mod="orphas", model="Orpha", lookup="orpha", sample="ORPHA:399", owner="clinic_id", first="mask", residual="export", product="stringer-orpha-id", bug="ORP-1 Orpha unique from Orphanet"),
    dict(slug="omim-mim-idor", plant="studsail", ticket="OMM-8", surface="OMIM MIM object-id IDOR", mod="omims", model="Omim", lookup="mim", sample="254300", owner="clinic_id", first="any_member", residual="search", product="studsail-omim-mim", bug="OMM-8 MIM unique from OMIM"),
    dict(slug="icd11-code-idor", plant="tabernacle", ticket="I11-3", surface="ICD-11 MMS object-id IDOR", mod="icd11s", model="Icd11", lookup="icd11", sample="5A11", owner="clinic_id", first="list_scope", residual="mget", product="tabernacle-icd11-mms", bug="I11-3 ICD-11 unique from WHO"),
    dict(slug="nct-trial-idor", plant="thimble", ticket="NCT-7", surface="ClinicalTrials.gov NCT object-id IDOR", mod="ncts", model="Nct", lookup="nct", sample="NCT01234567", owner="sponsor_id", first="authn", residual="csv", product="thimble-nct-ctgov", bug="NCT-7 NCT unique from CT.gov"),
    dict(slug="eudract-idor", plant="throat", ticket="EUD-2", surface="EudraCT number object-id IDOR", mod="eudracts", model="Eudract", lookup="eudract", sample="2018-000123-45", owner="sponsor_id", first="mask", residual="admin", product="throat-eudract-eu", bug="EUD-2 EudraCT unique from EMA"),
    dict(slug="isrctn-idor", plant="treenail", ticket="ISR-5", surface="ISRCTN trial object-id IDOR", mod="isrctns", model="Isrctn", lookup="isrctn", sample="ISRCTN12345678", owner="sponsor_id", first="any_member", residual="webhook", product="treenail-isrctn-id", bug="ISR-5 ISRCTN unique from BMC"),
    dict(slug="zenodo-rec-idor", plant="trysail", ticket="ZEN-6", surface="Zenodo record object-id IDOR", mod="zenodos", model="Zenodo", lookup="recid", sample="1234567", owner="community_id", first="list_scope", residual="comments", product="trysail-zenodo-rec", bug="ZEN-6 record unique from CERN"),
    dict(slug="figshare-art-idor", plant="tumblehome", ticket="FIG-9", surface="Figshare article object-id IDOR", mod="figshares", model="Figshare", lookup="article", sample="12345678", owner="account_id", first="authn", residual="pdf", product="tumblehome-figshare-art", bug="FIG-9 article unique from figshare"),
    dict(slug="osf-guid-idor", plant="wale", ticket="OSF-4", surface="OSF GUID object-id IDOR", mod="osfguids", model="Osfguid", lookup="guid", sample="abc12", owner="node_id", first="mask", residual="export", product="wale-osf-guid", bug="OSF-4 GUID unique from OSF"),
    dict(slug="ssrn-abs-idor", plant="warp", ticket="SSR-1", surface="SSRN abstract object-id IDOR", mod="ssrns", model="Ssrn", lookup="absid", sample="3456789", owner="campus_id", first="any_member", residual="search", product="warp-ssrn-abs", bug="SSR-1 abstract unique from SSRN"),
    dict(slug="repec-handle-idor", plant="whipstaff", ticket="REP-8", surface="RePEc handle object-id IDOR", mod="repecs", model="Repec", lookup="handle", sample="RePEc:eee:jfinec:v:99", owner="campus_id", first="list_scope", residual="mget", product="whipstaff-repec-hdl", bug="REP-8 handle unique from IDEAS"),
    dict(slug="hal-doc-idor", plant="winchhead", ticket="HAL-3", surface="HAL document object-id IDOR", mod="hals", model="Hal", lookup="hal", sample="hal-01234567", owner="lab_id", first="authn", residual="csv", product="winchhead-hal-doc", bug="HAL-3 HAL unique from CCSD"),
    dict(slug="cinii-naid-idor", plant="yardtack", ticket="CIN-7", surface="CiNii NAID object-id IDOR", mod="nids", model="Naid", lookup="naid", sample="110000123456", owner="campus_id", first="mask", residual="admin", product="yardtack-cinii-naid", bug="CIN-7 NAID unique from NII"),
    dict(slug="h3-cell-idor", plant="weatherhelm", ticket="H3C-2", surface="H3 cell index object-id IDOR", mod="h3cells", model="H3cell", lookup="h3", sample="8928308280fffff", owner="map_id", first="any_member", residual="webhook", product="weatherhelm-h3-cell", bug="H3C-2 H3 unique from Uber"),
    dict(slug="geohash-cell-idor", plant="frapline", ticket="GHS-5", surface="Geohash cell object-id IDOR", mod="geohashes", model="Geohash", lookup="geohash", sample="9q8yyk8yt", owner="map_id", first="list_scope", residual="comments", product="frapline-geohash-cell", bug="GHS-5 geohash unique from grid"),
]


BFLA_ROWS = [
    dict(slug='litestar-skip-guard-delete', plant='baggywrinkle', ticket='BGW-3', surface='Litestar skip_guards leftover on delete', family='py_async', skip="@delete('/notes/{nid}')\n@skip_guards", auth="@get('/notes/{nid}')\n@guards(auth)", leftover='put'),
    dict(slug='esmerald-allowany-delete', plant='binnacle', ticket='BIN-7', surface='Esmerald AllowAny leftover on delete', family='py_async', skip="@delete('/notes/{nid}')\n@permissions(AllowAny)", auth="@get('/notes/{nid}')\n@permissions(IsAuthenticated)", leftover='patch'),
    dict(slug='lilya-public-delete', plant='bluepeter', ticket='BLP-2', surface='Lilya Public leftover on delete', family='py_async', skip="@delete('/notes/{nid}')\n@public", auth="@get('/notes/{nid}')\n@requires_auth", leftover='update'),
    dict(slug='robyn-no-auth-delete', plant='boltrope', ticket='BLT-9', surface='Robyn delete missing @auth_required', family='py_async', skip="@app.delete('/notes/:nid')", auth="@app.get('/notes/:nid')\n@auth_required", leftover='put'),
    dict(slug='panther-perm-none-delete', plant='bowline', ticket='BWL-4', surface='Panther permissions=None leftover on delete', family='py_async', skip="@app.delete('/notes/<nid>')\n@permission(None)", auth="@app.get('/notes/<nid>')\n@permission(IsOwner)", leftover='patch'),
    dict(slug='nexios-skip-auth-delete', plant='brail', ticket='BRL-1', surface='Nexios skip_auth leftover on delete', family='py_async', skip="@router.delete('/notes/{nid}', skip_auth=True)", auth="@router.get('/notes/{nid}')", leftover='update'),
    dict(slug='klein-delete-bare', plant='burton', ticket='BRT-8', surface='Klein delete registered without auth', family='py_async', skip="@app.route('/notes/<nid>', methods=['DELETE'])", auth="@app.route('/notes/<nid>', methods=['GET'])\n@login", leftover='put'),
    dict(slug='morepath-no-perm-delete', plant='cablet', ticket='CBL-5', surface='Morepath delete missing permission', family='py_async', skip="@App.json(model=Note, request_method='DELETE')", auth='@App.json(model=Note, permission=View)', leftover='patch'),
    dict(slug='turbogears-require-skip-delete', plant='camber', ticket='CMB-6', surface='TurboGears require skipped on delete', family='py_async', skip='@expose()\ndef delete(self, nid):', auth='@expose()\n@require(not_anonymous())\ndef get(self, nid):', leftover='update'),
    dict(slug='tastypie-authz-open-delete', plant='carvel', ticket='CRV-3', surface='Tastypie Authorization() leftover on delete', family='py_async', skip='class NoteResource(ModelResource):\n    class Meta:\n        authorization = Authorization()', auth='class NoteResource(ModelResource):\n    class Meta:\n        authentication = ApiKeyAuthentication()', leftover='put'),
    dict(slug='piston-delete-no-oauth', plant='caulker', ticket='CLK-2', surface='Piston delete missing oauth_required', family='py_async', skip='def delete(self, request, nid):\n    Note.objects.get(pk=nid).delete()', auth='@oauth_required\ndef read(self, request, nid):', leftover='patch'),
    dict(slug='restless-prepare-delete-open', plant='channels', ticket='CHN-9', surface='Restless prepare_delete missing auth', family='py_async', skip='def prepare_delete(self, inst):\n    inst.delete()', auth='def is_authenticated(self):\n    return True  # GET only intended', leftover='update'),
    dict(slug='molten-skip-components-delete', plant='clinch', ticket='CLC-4', surface='Molten skip_components leftover on delete', family='py_async', skip="@app.delete('/notes/{nid}', skip_components={AuthComponent})", auth="@app.get('/notes/{nid}')", leftover='put'),
    dict(slug='bocadillo-skip-auth-delete', plant='clinker', ticket='CLK2-1', surface='Bocadillo skip_auth leftover on delete', family='py_async', skip="@app.route('/notes/{nid}', methods=['delete'], skip_auth=True)", auth="@app.route('/notes/{nid}')", leftover='patch'),
    dict(slug='nameko-http-delete-open', plant='cockbill', ticket='CKB-8', surface='Nameko http DELETE missing auth', family='py_async', skip="@http('DELETE', '/notes/<int:nid>')\ndef delete(self, request, nid):", auth="@http('GET', '/notes/<int:nid>')\ndef get(self, request, nid):", leftover='update'),
    dict(slug='cyclone-delete-bare', plant='companionway', ticket='CMP-5', surface='Cyclone delete missing authenticated', family='py_async', skip='class DeleteHandler(cyclone.web.RequestHandler):\n    def delete(self, nid):', auth='class GetHandler(cyclone.web.RequestHandler):\n    @authenticated\n    def get(self, nid):', leftover='put'),
    dict(slug='webpy-delete-no-login', plant='cordage', ticket='CRD-7', surface='web.py DELETE missing login', family='py_async', skip='class Delete:\n    def DELETE(self, nid):\n        note.delete(nid)', auth='class View:\n    def GET(self, nid):\n        web.ctx.session.user', leftover='patch'),
    dict(slug='apistar-auth-false-delete', plant='coxswain', ticket='CXW-3', surface='API Star authenticated=False leftover on delete', family='py_async', skip='def delete_note(nid: int, authenticated=False):', auth='def get_note(nid: int, user: User):', leftover='update'),
    dict(slug='socketify-delete-bare', plant='crowfoot', ticket='CFT-2', surface='Socketify DELETE missing auth', family='py_async', skip="@app.delete('/notes/:nid')\ndef delete(req, res, nid):", auth="@app.get('/notes/:nid')\n@app.middleware(auth)", leftover='put'),
    dict(slug='nestjs-public-on-delete', plant='decklight', ticket='DCK-9', surface='NestJS @Public leftover on Delete', family='js_route', skip="@Delete(':id')\n@Public()\nremove(@Param('id') id: string)", auth="@Get(':id')\n@UseGuards(JwtAuthGuard)\nfindOne(@Param('id') id: string)", leftover='patch'),
    dict(slug='express-delete-no-mw', plant='dogvane', ticket='DGV-4', surface='Express delete outside auth router', family='js_route', skip="app.delete('/notes/:id', (req, res) => notes.del(req.params.id))", auth="r.get('/notes/:id', auth, (req, res) => notes.get(req.params.id))", leftover='put'),
    dict(slug='koa-delete-outside-auth', plant='dunnage', ticket='DUN-1', surface='Koa delete mounted outside auth', family='js_route', skip="app.use(route.delete('/notes/:id', delNote))", auth="router.use(auth)\nrouter.get('/notes/:id', getNote)", leftover='patch'),
    dict(slug='fastify-prehdl-skip-delete', plant='ensign', ticket='ENS-8', surface='Fastify preHandler skip leftover on delete', family='js_route', skip="fastify.delete('/notes/:id', { preHandler: [] }, delNote)", auth="fastify.get('/notes/:id', { preHandler: [auth] }, getNote)", leftover='put'),
    dict(slug='restify-del-no-auth', plant='fathom', ticket='FTH-5', surface='Restify del missing auth handler', family='js_route', skip="server.del('/notes/:id', delNote)", auth="server.get('/notes/:id', auth, getNote)", leftover='patch'),
    dict(slug='polka-delete-bare', plant='flake', ticket='FLK-6', surface='Polka delete without middleware', family='js_route', skip="polka().delete('/notes/:id', delNote)", auth="polka().use(auth).get('/notes/:id', getNote)", leftover='put'),
    dict(slug='elysia-derive-skip-delete', plant='fluke', ticket='FLK2-3', surface='Elysia derive skip leftover on delete', family='js_route', skip="app.delete('/notes/:id', ({ params }) => Note.delete(params.id))", auth="app.derive(auth).get('/notes/:id', ({ params, user }) => Note.get(params.id, user))", leftover='patch'),
    dict(slug='hono-delete-no-mw', plant='footrope', ticket='FTP-2', surface='Hono delete outside auth middleware', family='js_route', skip="app.delete('/notes/:id', (c) => Note.delete(c.req.param('id')))", auth="app.use('/notes/*', auth)\napp.get('/notes/:id', (c) => Note.get(c.req.param('id')))", leftover='put'),
    dict(slug='fresh-delete-unprotected', plant='gaskets', ticket='GSK-9', surface='Fresh DELETE handler missing auth', family='js_route', skip='export const handler: Handlers = {\n  DELETE(req, ctx) { return Note.delete(ctx.params.id) },', auth='export const handler: Handlers = {\n  GET(req, ctx) { return auth(req).then(u => Note.get(ctx.params.id, u)) },', leftover='patch'),
    dict(slug='nextjs-route-delete-public', plant='gimbals', ticket='GMB-4', surface='Next.js route DELETE missing auth', family='js_route', skip='export async function DELETE(_req, { params }) {\n  await prisma.note.delete({ where: { id: params.id } })', auth='export async function GET(req, { params }) {\n  const s = await getServerSession()\n  return prisma.note.findFirst({ where: { id: params.id, ownerId: s.user.id } })', leftover='put'),
    dict(slug='remix-action-no-auth', plant='grommet', ticket='GRM-1', surface='Remix action missing authenticator', family='js_route', skip='export async function action({ params }) {\n  await db.note.delete({ where: { id: params.id } })', auth='export async function loader({ request, params }) {\n  await authenticator.isAuthenticated(request)\n  return db.note.find(params.id)', leftover='patch'),
    dict(slug='nitro-event-delete-public', plant='guyline', ticket='GYL-8', surface='Nitro eventHandler DELETE public', family='js_route', skip="export default eventHandler(async (e) => {\n  if (e.method === 'DELETE') await notes.del(getRouterParam(e, 'id'))", auth="export default eventHandler(async (e) => {\n  const user = await requireUser(e)\n  return notes.get(getRouterParam(e, 'id'), user)", leftover='put'),
    dict(slug='strapi-public-delete', plant='hank', ticket='HNK-5', surface='Strapi delete permission public leftover', family='cms', skip="delete: { enabled: true, policy: 'public' }", auth="find: { enabled: true, policy: 'is-authenticated' }", leftover='update'),
    dict(slug='keystone-access-delete-true', plant='hawser', ticket='HWS-7', surface='Keystone access.delete true leftover', family='cms', skip='access: { delete: () => true }', auth='access: { read: ({ session }) => !!session }', leftover='update'),
    dict(slug='payload-access-delete-true', plant='holystone', ticket='HLY-3', surface='Payload access.delete true leftover', family='cms', skip='access: { delete: () => true }', auth='access: { read: ({ req }) => Boolean(req.user) }', leftover='update'),
    dict(slug='directus-delete-no-policy', plant='inhaul', ticket='INH-2', surface='Directus delete missing policy', family='cms', skip="{ collection: 'notes', action: 'delete', permissions: {} }", auth="{ collection: 'notes', action: 'read', permissions: { user: '$CURRENT_USER' } }", leftover='update'),
    dict(slug='hasura-delete-public', plant='jackyard', ticket='JKY-9', surface='Hasura delete permission public leftover', family='sql', skip='- role: public\n  delete_permissions:\n    - filter: {}', auth='- role: user\n  select_permissions:\n    - filter: { owner_id: { _eq: X-Hasura-User-Id } }', leftover='update'),
    dict(slug='postgrest-anon-delete', plant='kedge', ticket='KDG-4', surface='PostgREST GRANT DELETE TO anon leftover', family='sql', skip='GRANT DELETE ON notes TO anon;', auth='GRANT SELECT ON notes TO authenticated;', leftover='update'),
    dict(slug='supabase-rls-delete-missing', plant='kevel', ticket='KVL-1', surface='Supabase RLS missing ON DELETE leftover', family='sql', skip='CREATE POLICY notes_select ON notes FOR SELECT USING (owner = auth.uid());', auth='-- no DELETE policy; table grants leftover', leftover='update'),
    dict(slug='micronaut-anon-on-delete', plant='lanyard', ticket='LNY-8', surface='Micronaut IS_ANONYMOUS leftover on delete', family='java_ann', skip="@Delete('/{id}')\n@Secured(SecurityRule.IS_ANONYMOUS)\nvoid delete(Long id)", auth="@Get('/{id}')\n@Secured(SecurityRule.IS_AUTHENTICATED)\nNote get(Long id)", leftover='put'),
    dict(slug='jersey-permitall-on-delete', plant='leeboard', ticket='LBD-5', surface='Jersey @PermitAll leftover on DELETE', family='java_ann', skip="@DELETE @Path('{id}')\n@PermitAll\npublic void delete(@PathParam('id') long id)", auth="@GET @Path('{id}')\n@RolesAllowed('user')\npublic Note get(@PathParam('id') long id)", leftover='put'),
    dict(slug='akka-http-delete-open', plant='messenger', ticket='MSG-6', surface='Akka HTTP delete missing authenticate', family='scala_mw', skip="path('notes' / LongNumber) { id => delete { complete(notes.del(id)) } }", auth="path('notes' / LongNumber) { id => authenticate(user) { u => get { complete(notes.get(id, u)) } } }", leftover='put'),
    dict(slug='http4s-delete-no-mw', plant='mooring', ticket='MOO-3', surface='http4s delete outside AuthMiddleware', family='scala_mw', skip="HttpRoutes.of { case DELETE -> Root / 'notes' / id => notes.del(id) }", auth="AuthMiddleware(auth)(AuthedRoutes.of { case GET -> Root / 'notes' / id as user => notes.get(id, user) })", leftover='put'),
    dict(slug='ktor-delete-no-auth', plant='nipper', ticket='NPR-2', surface='Ktor delete outside authenticate', family='kt_mw', skip="delete('/notes/{id}') { notes.del(call.parameters['id']) }", auth="authenticate('jwt') { get('/notes/{id}') { notes.get(call.parameters['id'], call.user) } }", leftover='put'),
    dict(slug='echo-delete-skip-auth', plant='orlop', ticket='ORL-9', surface='Echo DELETE skipping JWT middleware', family='go_mw', skip="e.DELETE('/notes/:id', h.Delete)", auth="g := e.Group('/notes', mw.JWT())\ng.GET('/:id', h.Get)", leftover='put'),
    dict(slug='fiber-delete-no-authz', plant='painter', ticket='PNT-4', surface='Fiber DELETE missing jwtware', family='go_mw', skip="app.Delete('/notes/:id', h.Delete)", auth="app.Use(jwtware.New())\napp.Get('/notes/:id', h.Get)", leftover='patch'),
    dict(slug='mux-delete-no-auth', plant='parbuckle', ticket='PBK-1', surface='gorilla/mux delete outside auth', family='go_mw', skip="r.HandleFunc('/notes/{id}', h.Delete).Methods('DELETE')", auth="s := r.PathPrefix('/notes').Subrouter()\ns.Use(auth)\ns.HandleFunc('/{id}', h.Get).Methods('GET')", leftover='put'),
    dict(slug='iris-delete-no-party', plant='pendant', ticket='PND-8', surface='Iris DELETE outside party middleware', family='go_mw', skip="app.Delete('/notes/{id}', h.Delete)", auth="p := app.Party('/notes', auth)\np.Get('/{id}', h.Get)", leftover='patch'),
    dict(slug='beego-delete-no-filter', plant='afterdeck', ticket='AFD-5', surface='Beego delete missing Filter', family='go_mw', skip="beego.Router('/notes/:id', &NoteController{}, 'delete:Delete')", auth="beego.InsertFilter('/notes/*', beego.BeforeRouter, auth)", leftover='put'),
    dict(slug='actix-extract-skip-delete', plant='preventer', ticket='PRV-7', surface='Actix delete missing AuthUser extractor', family='rust_ext', skip='async fn delete(path: Path<i32>) -> HttpResponse { Note::delete(path.0) }', auth='async fn get(path: Path<i32>, user: AuthUser) -> HttpResponse { Note::get(path.0, user.id) }', leftover='put'),
    dict(slug='axum-ext-skip-delete', plant='rabbet', ticket='RBT-3', surface='Axum delete missing Extension user', family='rust_ext', skip='async fn delete(Path(id): Path<i32>) { Note::delete(id).await }', auth='async fn get(Path(id): Path<i32>, Extension(u): Extension<User>) { Note::get(id, u.id).await }', leftover='put'),
    dict(slug='rocket-guard-skip-delete', plant='ribband', ticket='RBD-2', surface='Rocket delete missing User guard', family='rust_ext', skip="#[delete('/notes/<id>')]\nfn delete(id: i32) { Note::delete(id) }", auth="#[get('/notes/<id>')]\nfn get(id: i32, user: User) { Note::get(id, user.id) }", leftover='put'),
    dict(slug='warp-filter-skip-delete', plant='roband', ticket='RBN-9', surface='Warp delete missing auth filter', family='rust_ext', skip="let del = warp::delete().and(warp::path!('notes' / i32)).and_then(delete);", auth="let get = warp::get().and(auth()).and(warp::path!('notes' / i32)).and_then(get);", leftover='put'),
    dict(slug='poem-guard-skip-delete', plant='rowlock', ticket='RWL-4', surface='Poem delete missing Login guard', family='rust_ext', skip="#[oai(path='/:id', method='delete')]\nasync fn delete(&self, id: i32) { self.notes.delete(id).await }", auth="#[oai(path='/:id', method='get')]\nasync fn get(&self, id: i32, user: User) { self.notes.get(id, user.id).await }", leftover='put'),
    dict(slug='phoenix-plug-skip-delete', plant='scuttle', ticket='SCT-1', surface='Phoenix delete missing authenticate plug', family='ex_plug', skip="def delete(conn, %{'id' => id}) do\n  Notes.delete(id)\n  send_resp(conn, 204, '')\nend", auth='plug :authenticate_user when action in [:show, :index]', leftover='put'),
    dict(slug='symfony-isgranted-skip-delete', plant='seacock', ticket='SCK-8', surface='Symfony IsGranted missing on delete', family='php_mw', skip="#[Route('/notes/{id}', methods: ['DELETE'])]\npublic function delete(int $id): Response", auth="#[IsGranted('NOTE_VIEW')]\n#[Route('/notes/{id}', methods: ['GET'])]\npublic function show(int $id): Response", leftover='put'),
    dict(slug='yii-access-skip-delete', plant='sheerstrake', ticket='SST-5', surface='Yii AccessControl skip leftover on delete', family='php_mw', skip="'actions' => ['delete'],\n'allow' => true,", auth="'actions' => ['view'],\n'roles' => ['@'],", leftover='put'),
    dict(slug='slim-mw-skip-delete', plant='shroud', ticket='SHD-6', surface='Slim delete outside auth middleware', family='php_mw', skip="$app->delete('/notes/{id}', DeleteNote::class);", auth="$app->group('/notes', function ($g) { $g->get('/{id}', GetNote::class); })->add(Auth::class);", leftover='put'),
    dict(slug='sinatra-unprotected-delete', plant='skeg', ticket='SKG-3', surface='Sinatra delete missing protected!', family='rb_filter', skip="delete '/notes/:id' do\n  Note[params[:id]].destroy\nend", auth="get '/notes/:id' do\n  protected!\n  Note[params[:id]]\nend", leftover='put'),
    dict(slug='grape-auth-skip-delete', plant='slabline', ticket='SLB-2', surface='Grape delete missing authenticate!', family='rb_filter', skip="delete ':id' do\n  Note.find(params[:id]).destroy\nend", auth="helpers { include Auth }\nget ':id' do\n  authenticate!\n  Note.find(params[:id])\nend", leftover='put'),
    dict(slug='hanami-before-skip-delete', plant='snorter', ticket='SNT-9', surface='Hanami delete missing before authenticate', family='rb_filter', skip='def handle(*)\n  repo.delete(params[:id])\nend', auth='before :authenticate\ndef show\n  repo.find(params[:id])\nend', leftover='put'),
    dict(slug='roda-halt-skip-delete', plant='spanker', ticket='SPK-4', surface='Roda delete missing r.halt unless', family='rb_filter', skip='r.delete String do |id|\n  Note[id].delete\nend', auth='r.get String do |id|\n  r.halt 401 unless current_user\n  Note[id]\nend', leftover='put'),
    dict(slug='padrino-authorize-skip-delete', plant='spencer', ticket='SPC-1', surface='Padrino delete missing authorize', family='rb_filter', skip='delete :destroy, with: :id do\n  Note[params[:id]].destroy\nend', auth='get :show, with: :id do\n  authorize! :read, Note\n  Note[params[:id]]\nend', leftover='put'),
    dict(slug='nancy-auth-skip-delete', plant='stanchion', ticket='STN-8', surface='NancyFX delete missing RequiresAuthentication', family='cs_attr', skip="Delete['/notes/{id}'] = _ => { db.Notes.Remove(_.id); return 204; };", auth="Get['/notes/{id}'] = _ => { this.RequiresAuthentication(); return db.Notes.Find(_.id); };", leftover='put'),
    dict(slug='servicestack-auth-skip-delete', plant='steeve', ticket='STV-5', surface='ServiceStack Delete missing Authenticate', family='cs_attr', skip='public object Delete(DeleteNote r) { Db.DeleteById<Note>(r.Id); return HttpResult.Status204; }', auth='[Authenticate]\npublic object Get(GetNote r) => Db.SingleById<Note>(r.Id);', leftover='put'),
    dict(slug='carter-auth-skip-delete', plant='stopper', ticket='STP-7', surface='Carter DELETE missing auth filter', family='cs_attr', skip="this.Delete('/notes/{id:int}', async (id, ct) => { await db.Notes.Remove(id); return Results.NoContent(); });", auth="this.Get('/notes/{id:int}', async (id, ct) => { var u = http.User; return await db.Notes.Find(id, u); });", leftover='put'),
    dict(slug='cakephp-authz-skip-delete', plant='stringer', ticket='STR-3', surface='CakePHP delete missing isAuthorized', family='php_mw', skip='public function delete($id) { $this->Notes->delete($id); }', auth='public function view($id) { $this->Authorization->authorize($this->Notes->get($id)); }', leftover='put'),
    dict(slug='codeigniter-filter-skip-delete', plant='studsail', ticket='STD-2', surface='CodeIgniter delete missing filter', family='php_mw', skip="$routes->delete('notes/(:num)', 'Notes::delete/$1');", auth="$routes->get('notes/(:num)', 'Notes::show/$1', ['filter' => 'auth']);", leftover='put'),
    dict(slug='laminas-rbac-skip-delete', plant='tabernacle', ticket='TBC-9', surface='Laminas delete missing rbac', family='php_mw', skip="'delete' => ['may_terminate' => true, 'options' => ['route' => '/notes/:id']],", auth="'show' => ['options' => ['route' => '/notes/:id', 'defaults' => ['rbac' => 'note.view']]],", leftover='put'),
    dict(slug='phalcon-acl-skip-delete', plant='thimble', ticket='THB-4', surface='Phalcon delete missing acl', family='php_mw', skip="$acl->allow('guest', 'notes', 'delete');", auth="$acl->allow('user', 'notes', 'view');", leftover='put'),
    dict(slug='fuelphp-auth-skip-delete', plant='throat', ticket='THT-1', surface='FuelPHP delete missing Auth::check', family='php_mw', skip='public function action_delete($id) { Model_Note::find($id)->delete(); }', auth='public function action_view($id) { if (!Auth::check()) throw new HttpNoAccessException; }', leftover='put'),
    dict(slug='lumen-mw-skip-delete', plant='treenail', ticket='TRN-8', surface='Lumen delete outside auth middleware', family='php_mw', skip="$router->delete('/notes/{id}', 'NoteController@destroy');", auth="$router->group(['middleware' => 'auth'], function ($r) { $r->get('/notes/{id}', 'NoteController@show'); });", leftover='put'),
    dict(slug='eve-resource-delete-open', plant='trysail', ticket='TRY-5', surface='Eve ITEM_METHODS DELETE public leftover', family='py_async', skip="ITEM_METHODS = ['GET', 'DELETE']\nPUBLIC_METHODS = ['DELETE']", auth="RESOURCE_METHODS = ['GET']\nAUTH_FIELD = 'owner'", leftover='put'),
    dict(slug='django-ninja-auth-skip-delete', plant='tumblehome', ticket='TBH-6', surface='Django Ninja delete missing AuthBearer', family='py_async', skip="@api.delete('/notes/{nid}')\ndef destroy(request, nid: int):", auth="@api.get('/notes/{nid}', auth=AuthBearer())\ndef show(request, nid: int):", leftover='put'),
    dict(slug='chalice-auth-skip-delete', plant='wale', ticket='WAL-3', surface='Chalice delete missing authorizer', family='py_async', skip="@app.route('/notes/{nid}', methods=['DELETE'])\ndef delete(nid):", auth="@app.route('/notes/{nid}', methods=['GET'], authorizer=authorizer)\ndef get(nid):", leftover='put'),
    dict(slug='zappa-auth-skip-delete', plant='warp', ticket='WRP-2', surface='Zappa lambda delete missing authorizer', family='py_async', skip="def delete(event, ctx):\n    notes.delete(event['pathParameters']['id'])", auth="def get(event, ctx):\n    auth(event)\n    return notes.get(event['pathParameters']['id'])", leftover='put'),
    dict(slug='mangum-auth-skip-delete', plant='whipstaff', ticket='WPS-9', surface='Mangum ASGI delete missing deps', family='py_async', skip="@app.delete('/notes/{nid}')\nasync def delete(nid: int):", auth="@app.get('/notes/{nid}')\nasync def get(nid: int, user=Depends(auth)):", leftover='put'),
    dict(slug='powertools-auth-skip-delete', plant='winchhead', ticket='WNC-4', surface='Lambda Powertools delete missing Tracer auth', family='py_async', skip="@app.delete('/notes/<nid>')\ndef delete(nid):", auth="@app.get('/notes/<nid>')\n@tracer.capture_method\ndef get(nid):", leftover='put'),
    dict(slug='fastapi-users-skip-delete', plant='yardtack', ticket='YDT-1', surface='FastAPI Users unused current_user on delete', family='py_async', skip="@router.delete('/notes/{nid}')\nasync def delete(nid: int):", auth="@router.get('/notes/{nid}')\nasync def get(nid: int, user=Depends(current_active_user)):", leftover='put'),
    dict(slug='starlite-guard-skip-delete', plant='weatherhelm', ticket='WTH-8', surface='Starlite skip_guards leftover on delete', family='py_async', skip="@delete('/notes/{nid}', guards=[])", auth="@get('/notes/{nid}', guards=[auth_guard])", leftover='put'),
    dict(slug='channels-consumer-skip-delete', plant='frapline', ticket='FRP-5', surface='Channels consumer delete.receive missing login', family='py_async', skip="async def delete_receive(self, event):\n    await Note.objects.filter(id=event['id']).adelete()", auth="async def connect(self):\n    if self.scope['user'].is_anonymous: await self.close()", leftover='put'),
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
