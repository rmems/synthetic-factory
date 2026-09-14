#!/usr/bin/env python3
"""Emit experiments/azr-plants-r2320.py — unique object-id IDOR / BFLA for r2320+."""
from __future__ import annotations

import re
from pathlib import Path

EXPERIMENTS = Path(__file__).resolve().parent
OUT = EXPERIMENTS / "azr-plants-r2320.py"

USED_SLUGS: set[str] = set()
USED_PLANTS: set[str] = set()
USED_LOOKUPS: set[str] = set()
USED_MODS: set[str] = set()
for p in list(EXPERIMENTS.glob("azr-plants*.py")) + list(EXPERIMENTS.glob("azr-mill*.py")):
    if p.name == "azr-plants-r2320.py":
        continue
    text = p.read_text(errors="ignore")
    USED_SLUGS.update(re.findall(r"slug=['\"]([a-z0-9-]+)['\"]", text))
    USED_PLANTS.update(re.findall(r"plant=['\"]([a-z0-9-]+)['\"]", text))
    USED_LOOKUPS.update(re.findall(r"lookup=['\"]([a-z0-9_]+)['\"]", text))
    USED_MODS.update(re.findall(r"mod=['\"]([a-z0-9_]+)['\"]", text))

PREFIX = [f"azw{i:02d}" for i in range(80)]
PLANTS = []
for pre in PREFIX:
    name = pre + "boom"
    assert name not in USED_PLANTS, name
    PLANTS.append(name)

FIRST = ["authn", "mask", "any_member", "list_scope"]
RESIDUAL = ["pdf", "export", "search", "mget", "csv", "admin", "webhook", "comments"]
LEFTOVER = ["put", "patch", "update"]


def names(slug: str) -> tuple[str, str, str]:
    core = slug.replace("-idor", "").replace("-skip-delete", "").replace("-", "")
    core = (core + "x" * 8)[:10]
    mod = core + "s83"
    lookup = core + "l83"
    model = core[:1].upper() + core[1:] + "N"
    assert mod not in USED_MODS, mod
    assert lookup not in USED_LOOKUPS, lookup
    return mod, model, lookup


IDOR_SRC = [
    ("gtin14-idor", "GTIN-14 object-id IDOR", "00012345678905", "trade_id", "gtin14", "GTIN unique from GS1"),
    ("itf14-idor", "ITF-14 object-id IDOR", "10012345678907", "trade_id", "itf14", "ITF unique from GS1"),
    ("gs1-sscc-idor", "GS1 SSCC object-id IDOR", "00006141411234567891", "trade_id", "gs1-sscc", "SSCC unique from GS1"),
    ("gs1-gdti-idor", "GS1 GDTI object-id IDOR", "2530614141123456789", "trade_id", "gs1-gdti", "GDTI unique from GS1"),
    ("gs1-gsin-idor", "GS1 GSIN object-id IDOR", "402061414112345678", "trade_id", "gs1-gsin", "GSIN unique from GS1"),
    ("gs1-cpid-idor", "GS1 CPID object-id IDOR", "80100614141ABC", "trade_id", "gs1-cpid", "CPID unique from GS1"),
    ("gs1-ginc2-idor", "GS1 GINC2 object-id IDOR", "4010614141SHIP2", "trade_id", "gs1-ginc2", "GINC unique from GS1"),
    ("gs1-gsrn2-idor", "GS1 GSRN2 object-id IDOR", "80170614141123456789", "trade_id", "gs1-gsrn2", "GSRN unique from GS1"),
    ("ean8-idor", "EAN-8 object-id IDOR", "96385074", "trade_id", "ean8", "EAN unique from GS1"),
    ("upc12-idor", "UPC-12 object-id IDOR", "036000291452", "trade_id", "upc12", "UPC unique from GS1"),
    ("isbn10-idor", "ISBN-10 object-id IDOR", "0140449132", "lab_id", "isbn10", "ISBN unique from ISO"),
    ("ismn13-idor", "ISMN-13 object-id IDOR", "9790000000001", "lab_id", "ismn13", "ISMN unique from ISO"),
    ("istc-idor", "ISTC object-id IDOR", "0A9-2002-12B4A105-6", "lab_id", "istc", "ISTC unique from ISO"),
    ("isan-v-idor", "ISAN-V object-id IDOR", "0000-0001-8947-0000-8-0000-0000-D", "lab_id", "isan-v", "ISAN unique from ISAN"),
    ("iswc-t-idor", "ISWC-T object-id IDOR", "T-000.000.001-0", "lab_id", "iswc-t", "ISWC unique from CISAC"),
    ("doi-datacite-idor", "DataCite DOI object-id IDOR", "10.5281/zenodo.1234567", "lab_id", "doi-datacite", "DOI unique from DataCite"),
    ("ark-id-idor", "ARK id object-id IDOR", "ark:/13030/tf5p30086k", "lab_id", "ark-id", "ARK unique from CDL"),
    ("urn-isbn-idor", "URN ISBN object-id IDOR", "urn:isbn:0451450523", "lab_id", "urn-isbn", "URN unique from IETF"),
    ("viaf-idor", "VIAF object-id IDOR", "102333412", "lab_id", "viaf", "VIAF unique from OCLC"),
    ("lcnaf-idor", "LCNAF object-id IDOR", "n79021164", "lab_id", "lcnaf", "NAF unique from LC"),
    ("wikidata-q-idor", "Wikidata Q object-id IDOR", "Q42", "lab_id", "wikidata-q", "Q unique from Wikidata"),
    ("geonames-id-idor", "GeoNames id object-id IDOR", "5128581", "geo_id", "geonames-id", "id unique from GeoNames"),
    ("openalex-idor", "OpenAlex object-id IDOR", "W2741809807", "lab_id", "openalex", "id unique from OurResearch"),
    ("mag-id-idor", "MAG id object-id IDOR", "2149078318", "lab_id", "mag-id", "id unique from MAG"),
    ("pmid-ncbi-idor", "PMID NCBI object-id IDOR", "12345678", "lab_id", "pmid-ncbi", "PMID unique from NCBI"),
    ("pmcid-idor", "PMCID object-id IDOR", "PMC3531190", "lab_id", "pmcid", "PMCID unique from NCBI"),
    ("s2-paper-idor", "S2 paper object-id IDOR", "649def34f8be52c8b66281af98ae884c09aef38b", "lab_id", "s2-paper", "paper unique from S2"),
    ("dblp-key-idor", "DBLP key object-id IDOR", "journals/cacm/Dijkstra68", "lab_id", "dblp-key", "key unique from DBLP"),
    ("cas-rn-idor", "CAS RN object-id IDOR", "64-17-5", "lab_id", "cas-rn", "RN unique from CAS"),
    ("inchikey-idor", "InChIKey object-id IDOR", "LFQSCWFLJHTTHZ-UHFFFAOYSA-N", "lab_id", "inchikey", "key unique from IUPAC"),
    ("chembl-id-idor", "ChEMBL id object-id IDOR", "CHEMBL25", "lab_id", "chembl-id", "id unique from EBI"),
    ("drugbank-idor", "DrugBank object-id IDOR", "DB00945", "lab_id", "drugbank", "id unique from DrugBank"),
    ("rxcui-idor", "RxCUI object-id IDOR", "161", "lab_id", "rxcui", "CUI unique from NLM"),
    ("ndc11-idor", "NDC-11 object-id IDOR", "00071015523", "lab_id", "ndc11", "NDC unique from FDA"),
    ("icd11-idor", "ICD-11 object-id IDOR", "5A11", "lab_id", "icd11", "code unique from WHO"),
    ("icd9-cm-idor", "ICD-9-CM object-id IDOR", "250.00", "lab_id", "icd9-cm", "code unique from CDC"),
    ("loinc-idor", "LOINC object-id IDOR", "2345-7", "lab_id", "loinc", "code unique from Regenstrief"),
    ("snomed-idor", "SNOMED object-id IDOR", "44054006", "lab_id", "snomed", "id unique from SNOMED"),
    ("mesh-ui-idor", "MeSH UI object-id IDOR", "D003920", "lab_id", "mesh-ui", "UI unique from NLM"),
    ("hpo-id-idor", "HPO id object-id IDOR", "HP:0001250", "lab_id", "hpo-id", "id unique from HPO"),
    ("eco-id-idor", "ECO id object-id IDOR", "ECO:0000269", "lab_id", "eco-id", "id unique from ECO"),
    ("so-id-idor", "SO id object-id IDOR", "SO:0000704", "lab_id", "so-id", "id unique from SO"),
    ("ncit-id-idor", "NCIt id object-id IDOR", "C4872", "lab_id", "ncit-id", "id unique from NCI"),
    ("ensembl-idor", "Ensembl gene object-id IDOR", "ENSG00000141510", "lab_id", "ensembl", "gene unique from EBI"),
    ("refseq-idor", "RefSeq object-id IDOR", "NM_000546.6", "lab_id", "refseq", "acc unique from NCBI"),
    ("genbank-idor", "GenBank object-id IDOR", "U49845.1", "lab_id", "genbank", "acc unique from NCBI"),
    ("uniprot-idor", "UniProt object-id IDOR", "P04637", "lab_id", "uniprot", "AC unique from UniProt"),
    ("pdb-id-idor", "PDB id object-id IDOR", "1TUP", "lab_id", "pdb-id", "id unique from RCSB"),
    ("hgnc-idor", "HGNC object-id IDOR", "HGNC:11998", "lab_id", "hgnc", "id unique from HGNC"),
    ("omim-idor", "OMIM object-id IDOR", "191170", "lab_id", "omim", "id unique from OMIM"),
    ("clinvar-idor", "ClinVar object-id IDOR", "12345", "lab_id", "clinvar", "id unique from NCBI"),
    ("dbsnp-idor", "dbSNP object-id IDOR", "rs7412", "lab_id", "dbsnp", "rs unique from NCBI"),
    ("cosmic-idor", "COSMIC object-id IDOR", "COSM476", "lab_id", "cosmic", "id unique from Sanger"),
    ("lei-20-idor", "LEI-20 object-id IDOR", "5493001KJTIIGC8Y1R13", "bank_id", "lei-20", "LEI unique from GLEIF"),
    ("bic-8-idor", "BIC-8 object-id IDOR", "CHASUS33", "bank_id", "bic-8", "BIC unique from SWIFT"),
    ("iban-idor", "IBAN object-id IDOR", "GB82WEST12345698765432", "bank_id", "iban", "IBAN unique from ISO"),
    ("swift-bic-idor", "SWIFT BIC object-id IDOR", "BOFAUS3NXXX", "bank_id", "swift-bic", "BIC unique from SWIFT"),
    ("mic-exch-idor", "MIC exch object-id IDOR", "XLON", "bank_id", "mic-exch", "MIC unique from ISO"),
    ("figi-bbg-idor", "FIGI BBG object-id IDOR", "BBG000B9XRY4", "bank_id", "figi-bbg", "FIGI unique from Bloomberg"),
    ("cusip-9-idor", "CUSIP-9 object-id IDOR", "037833100", "bank_id", "cusip-9", "CUSIP unique from CUSIP"),
    ("isin-12-idor", "ISIN-12 object-id IDOR", "US0378331005", "bank_id", "isin-12", "ISIN unique from ISO"),
    ("sedol-7-idor", "SEDOL-7 object-id IDOR", "2046251", "bank_id", "sedol-7", "SEDOL unique from LSE"),
    ("wkn-idor", "WKN object-id IDOR", "850727", "bank_id", "wkn", "WKN unique from WM"),
    ("ticker-idor", "Ticker object-id IDOR", "AAPL", "bank_id", "ticker", "ticker unique from exchange"),
    ("cik-sec-idor", "SEC CIK object-id IDOR", "0000320193", "bank_id", "cik-sec", "CIK unique from SEC"),
    ("lei-roc-idor", "LEI ROC object-id IDOR", "RA000001", "bank_id", "lei-roc", "ROC unique from GLEIF"),
    ("duns-9-idor", "DUNS-9 object-id IDOR", "006928774", "bank_id", "duns-9", "DUNS unique from D&B"),
    ("ein-idor", "EIN object-id IDOR", "94-1349661", "bank_id", "ein", "EIN unique from IRS"),
    ("nino-uk-idor", "NINo object-id IDOR", "AB123456C", "bank_id", "nino-uk", "NINo unique from HMRC"),
    ("tfn-au-idor", "TFN object-id IDOR", "123456782", "bank_id", "tfn-au", "TFN unique from ATO"),
    ("sin-ca-idor", "SIN object-id IDOR", "046454286", "bank_id", "sin-ca", "SIN unique from CRA"),
    ("imo-7-idor", "IMO-7 object-id IDOR", "9074729", "mmsi_id", "imo-7", "IMO unique from IMO"),
    ("mmsi-idor", "MMSI object-id IDOR", "366123456", "mmsi_id", "mmsi", "MMSI unique from ITU"),
    ("callsign-idor", "Callsign object-id IDOR", "N12345", "mmsi_id", "callsign", "callsign unique from FAA"),
    ("icao-24-idor", "ICAO-24 object-id IDOR", "a1b2c3", "mmsi_id", "icao-24", "addr unique from ICAO"),
    ("iata-3-idor", "IATA-3 object-id IDOR", "JFK", "geo_id", "iata-3", "code unique from IATA"),
    ("iso3166-idor", "ISO 3166 object-id IDOR", "US", "geo_id", "iso3166", "alpha unique from ISO"),
    ("nuts-idor", "NUTS object-id IDOR", "UKI", "geo_id", "nuts", "NUTS unique from Eurostat"),
    ("fips-idor", "FIPS object-id IDOR", "36061", "geo_id", "fips", "FIPS unique from Census"),
    ("nace2-idor", "NACE2 object-id IDOR", "62.01", "trade_id", "nace2", "NACE unique from Eurostat"),
]
assert len(IDOR_SRC) == 80, len(IDOR_SRC)
IDOR = []
for slug, surface, sample, owner, product, bug in IDOR_SRC:
    mod, model, lookup = names(slug)
    IDOR.append((slug, surface, mod, model, lookup, sample, owner, product, bug))
assert not ({x[0] for x in IDOR} & USED_SLUGS), {x[0] for x in IDOR} & USED_SLUGS
assert len({x[2] for x in IDOR}) == 80, "mod collision"
assert len({x[4] for x in IDOR}) == 80, "lookup collision"

BFLA_SRC = [
    ("harness-skip-delete", "Harness pipeline delete missing token", "harness pipeline delete --id notes", "harness pipeline get --id notes"),
    ("rundeck-skip-delete", "Rundeck job delete missing token", "rd jobs delete -i notes", "rd jobs info -i notes"),
    ("awx-job-skip-delete", "AWX job delete missing token", "awx jobs delete notes", "awx jobs get notes"),
    ("tower-job-skip-delete", "Tower job delete missing token", "tower-cli job delete notes", "tower-cli job get notes"),
    ("semaphore-skip-delete", "Semaphore project delete missing token", "sem project delete notes", "sem project info notes"),
    ("buddy-skip-delete", "Buddy pipeline delete missing token", "buddy pipeline delete notes", "buddy pipeline get notes"),
    ("codeship-skip-delete", "Codeship project delete missing token", "codeship project delete notes", "codeship project get notes"),
    ("shippable-skip-delete", "Shippable job delete missing token", "shipctl delete job notes", "shipctl get job notes"),
    ("npm-pkg-skip-delete", "npm unpublish missing token", "npm unpublish notes --force", "npm view notes"),
    ("pypi-pkg-skip-delete", "PyPI yank missing token", "twine yank notes==1.0.0", "pip index versions notes"),
    ("cargo-cr-skip-delete", "crates.io yank missing token", "cargo yank notes --vers 1.0.0", "cargo info notes"),
    ("maven-ga-skip-delete", "Maven artifact delete missing token", "mvn deploy:delete -Dartifact=notes", "mvn help:evaluate -Dartifact=notes"),
    ("nuget-pkg-skip-delete", "NuGet delete missing token", "nuget delete notes 1.0.0 -NonInteractive", "nuget list notes"),
    ("gem-pkg-skip-delete", "RubyGems yank missing token", "gem yank notes -v 1.0.0", "gem info notes"),
    ("composer-skip-delete", "Packagist delete missing token", "composer remove notes", "composer show notes"),
    ("go-mod-skip-delete", "Go module retract missing proxy", "go get notes@none", "go list -m notes"),
    ("hex-pkg-skip-delete", "Hex retire missing token", "mix hex.retire notes 1.0.0", "mix hex.info notes"),
    ("cran-pkg-skip-delete", "CRAN archive missing key", "R CMD REMOVE notes", "R -e 'packageVersion(\"notes\")'"),
    ("conda-pkg-skip-delete", "conda remove missing token", "conda remove notes -y", "conda list notes"),
    ("apt-pkg-skip-delete", "apt purge missing sudoers", "apt-get purge notes -y", "dpkg -s notes"),
    ("sops-key-skip-delete", "sops key delete missing age", "sops -d --ignore-mac notes", "sops -d notes"),
    ("sealed-sec-skip-delete", "SealedSecret delete missing rbac", "kubectl delete sealedsecret notes", "kubectl get sealedsecret notes"),
    ("cert-mgr-skip-delete", "cert-manager Certificate delete missing rbac", "kubectl delete certificate notes", "kubectl get certificate notes"),
    ("ext-sec-skip-delete", "ExternalSecret delete missing rbac", "kubectl delete externalsecret notes", "kubectl get externalsecret notes"),
    ("vault-k8s-skip-delete", "Vault k8s secret delete missing token", "vault kv delete secret/notes", "vault kv get secret/notes"),
    ("aws-sm-skip-delete", "Secrets Manager delete missing aws", "aws secretsmanager delete-secret --secret-id notes --force-delete-without-recovery", "aws secretsmanager describe-secret --secret-id notes"),
    ("gcp-sm-skip-delete", "GCP Secret Manager delete missing adc", "gcloud secrets delete notes --quiet", "gcloud secrets describe notes"),
    ("az-kv-skip-delete", "Azure Key Vault secret delete missing sp", "az keyvault secret delete --name notes --vault-name v", "az keyvault secret show --name notes --vault-name v"),
    ("lambda-fn-skip-delete", "Lambda delete missing aws", "aws lambda delete-function --function-name notes", "aws lambda get-function --function-name notes"),
    ("gcf-fn-skip-delete", "Cloud Functions delete missing adc", "gcloud functions delete notes --quiet", "gcloud functions describe notes"),
    ("az-fn-skip-delete", "Azure Function delete missing sp", "az functionapp delete --name notes --resource-group r", "az functionapp show --name notes --resource-group r"),
    ("cf-stack-skip-delete", "CloudFormation stack delete missing aws", "aws cloudformation delete-stack --stack-name notes", "aws cloudformation describe-stacks --stack-name notes"),
    ("cdk-stack-skip-delete", "CDK destroy missing aws", "cdk destroy notes --force", "cdk ls"),
    ("sam-app-skip-delete", "SAM delete missing aws", "sam delete --stack-name notes --no-prompts", "sam list stack-outputs --stack-name notes"),
    ("serverless-skip-delete", "Serverless remove missing creds", "sls remove --stage notes", "sls info --stage notes"),
    ("sst-app-skip-delete", "SST remove missing creds", "sst remove --stage notes", "sst diff --stage notes"),
    ("firebase-skip-delete", "Firebase project delete missing token", "firebase projects:delete notes --force", "firebase projects:list"),
    ("supabase-skip-delete", "Supabase project delete missing token", "supabase projects delete notes --yes", "supabase projects list"),
    ("planetscale-skip-delete", "PlanetScale db delete missing token", "pscale database delete notes --force", "pscale database show notes"),
    ("neon-db-skip-delete", "Neon project delete missing token", "neon projects delete notes", "neon projects get notes"),
    ("render-svc-skip-delete", "Render service delete missing token", "render services delete notes --confirm", "render services get notes"),
    ("fly-app-skip-delete", "Fly app destroy missing token", "fly apps destroy notes --yes", "fly apps show notes"),
    ("railway-skip-delete", "Railway project delete missing token", "railway delete --yes", "railway status"),
    ("heroku-app-skip-delete", "Heroku app destroy missing token", "heroku apps:destroy notes --confirm notes", "heroku apps:info notes"),
    ("netlify-skip-delete", "Netlify site delete missing token", "netlify sites:delete notes --force", "netlify sites:info notes"),
    ("vercel-proj-skip-delete", "Vercel project delete missing token", "vercel project rm notes --yes", "vercel project ls"),
    ("cf-pages-skip-delete", "Cloudflare Pages delete missing token", "wrangler pages project delete notes --yes", "wrangler pages project list"),
    ("amplify-skip-delete", "Amplify app delete missing aws", "aws amplify delete-app --app-id notes", "aws amplify get-app --app-id notes"),
    ("mode-rep-skip-delete", "Mode report delete missing token", "mode report delete notes", "mode report get notes"),
    ("hex-proj-skip-delete", "Hex project delete missing token", "hex project delete notes", "hex project get notes"),
    ("jupyterhub-skip-delete", "JupyterHub user delete missing token", "jupyterhub-singleuser --delete-user notes", "jupyterhub list-users"),
    ("rstudio-skip-delete", "RStudio user delete missing sudoers", "rstudio-server user-delete notes", "rstudio-server user-status notes"),
    ("vscode-srv-skip-delete", "code-server session delete missing conf", "code-server --shutdown notes", "code-server --list-sessions"),
    ("codeserver-skip-delete", "Coder workspace delete missing token", "coder delete notes --yes", "coder show notes"),
    ("drone-sec-skip-delete", "Drone secret delete missing token", "drone secret rm --repository notes --name k", "drone secret ls --repository notes"),
    ("yum-pkg-skip-delete", "yum remove missing sudoers", "yum remove notes -y", "rpm -q notes"),
    ("apk-pkg-skip-delete", "apk del missing sudoers", "apk del notes", "apk info notes"),
    ("nix-pkg-skip-delete", "nix-env uninstall missing store", "nix-env -e notes", "nix-env -q notes"),
    ("brew-pkg-skip-delete", "brew uninstall missing cellar", "brew uninstall notes", "brew info notes"),
    ("snap-pkg-skip-delete", "snap remove missing sudoers", "snap remove notes", "snap info notes"),
    ("flatpak-skip-delete", "flatpak uninstall missing sudoers", "flatpak uninstall notes -y", "flatpak info notes"),
    ("appimage-skip-delete", "AppImage remove missing file", "rm ~/Applications/notes.AppImage", "ls ~/Applications/notes.AppImage"),
    ("choco-pkg-skip-delete", "choco uninstall missing admin", "choco uninstall notes -y", "choco list notes"),
    ("winget-skip-delete", "winget uninstall missing admin", "winget uninstall notes", "winget show notes"),
    ("scoop-pkg-skip-delete", "scoop uninstall missing shim", "scoop uninstall notes", "scoop info notes"),
    ("pacman-skip-delete", "pacman -R missing sudoers", "pacman -Rns notes --noconfirm", "pacman -Qi notes"),
    ("zypper-skip-delete", "zypper remove missing sudoers", "zypper remove -y notes", "zypper info notes"),
    ("portage-skip-delete", "emerge unmerge missing sudoers", "emerge --unmerge notes", "equery list notes"),
    ("guix-pkg-skip-delete", "guix remove missing profile", "guix remove notes", "guix package -I notes"),
    ("spack-pkg-skip-delete", "spack uninstall missing db", "spack uninstall -y notes", "spack find notes"),
    ("conan-pkg-skip-delete", "conan remove missing cache", "conan remove notes -c", "conan list notes"),
    ("vcpkg-skip-delete", "vcpkg remove missing triplet", "vcpkg remove notes", "vcpkg list notes"),
    ("bazel-mod-skip-delete", "Bazel module delete missing cache", "bazel clean --expunge", "bazel query notes"),
    ("buck2-skip-delete", "Buck2 target delete missing conf", "buck2 clean", "buck2 targets notes"),
    ("pants-skip-delete", "Pants target delete missing conf", "pants --change-since=HEAD list notes", "pants list notes"),
    ("gradle-mod-skip-delete", "Gradle module delete missing cache", "gradle :notes:clean", "gradle :notes:properties"),
    ("sbt-mod-skip-delete", "sbt project delete missing ivy", "sbt 'notes/clean'", "sbt 'notes/show name'"),
    ("lein-mod-skip-delete", "Leiningen project delete missing maven", "lein clean", "lein pprint :name"),
    ("mix-hex-skip-delete", "Mix deps.delete missing hex", "mix deps.clean notes --unlock", "mix deps"),
    ("cabal-pkg-skip-delete", "Cabal unregister missing ghc", "ghc-pkg unregister notes", "ghc-pkg describe notes"),
]
assert len(BFLA_SRC) == 80, len(BFLA_SRC)
BFLA = [(s, surf, "js_route", skip, auth) for s, surf, skip, auth in BFLA_SRC]
assert not ({x[0] for x in BFLA} & USED_SLUGS), {x[0] for x in BFLA} & USED_SLUGS
assert len({x[0] for x in BFLA}) == 80

TICKETS = [f"AZ{(i % 9) + 1}-{i + 1}" for i in range(80)]


def py_idor_row(i: int) -> str:
    slug, surface, mod, model, lookup, sample, owner, product, bug = IDOR[i]
    plant = PLANTS[i]
    ticket = TICKETS[i]
    first = FIRST[i % 4]
    residual = RESIDUAL[i % 8]
    return (
        "    dict("
        f"slug={slug!r}, plant={plant!r}, ticket={ticket!r}, surface={surface!r}, "
        f"mod={mod!r}, model={model!r}, lookup={lookup!r}, sample={sample!r}, "
        f"owner={owner!r}, first={first!r}, residual={residual!r}, "
        f"product={product!r}, bug={ticket + ' ' + bug!r}),"
    )


def py_bfla_row(i: int) -> str:
    slug, surface, family, skip, auth = BFLA[i]
    plant = PLANTS[i]
    ticket = TICKETS[i]
    leftover = LEFTOVER[i % 3]
    return (
        "    dict("
        f"slug={slug!r}, plant={plant!r}, ticket={ticket!r}, surface={surface!r}, "
        f"family={family!r}, skip={skip!r}, auth={auth!r}, leftover={leftover!r}),"
    )


header = '''"""Extra unique IDOR/BFLA plants for authz-regression-factory r2320+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r2319 vesselNNNN-sys.
Not clones of r2319 tailn-n / powerbi, r2240 iccid-19 / jenkins-job.
"""
from __future__ import annotations


EXTRA_IDOR_ROWS = [
'''
expand_src = (EXPERIMENTS / "azr-plants-r1504.py").read_text()
idx = expand_src.index("def extra_bflas")
body = (
    header
    + "\n".join(py_idor_row(i) for i in range(80))
    + "\n]\n\n\nBFLA_ROWS = [\n"
    + "\n".join(py_bfla_row(i) for i in range(80))
    + "\n]\n\n\n"
    + expand_src[idx:]
)
OUT.write_text(body)
print("wrote", OUT, "idor0", IDOR[0][0], "bfla0", BFLA[0][0])
