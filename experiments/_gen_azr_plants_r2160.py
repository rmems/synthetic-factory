#!/usr/bin/env python3
"""Emit experiments/azr-plants-r2160.py — unique object-id IDOR / BFLA for r2160+."""
from __future__ import annotations

import re
from pathlib import Path

EXPERIMENTS = Path(__file__).resolve().parent
OUT = EXPERIMENTS / "azr-plants-r2160.py"

USED_SLUGS: set[str] = set()
USED_PLANTS: set[str] = set()
USED_LOOKUPS: set[str] = set()
USED_MODS: set[str] = set()
for p in list(EXPERIMENTS.glob("azr-plants*.py")) + list(EXPERIMENTS.glob("azr-mill*.py")):
    if p.name == "azr-plants-r2160.py":
        continue
    text = p.read_text(errors="ignore")
    USED_SLUGS.update(re.findall(r"slug=['\"]([a-z0-9-]+)['\"]", text))
    USED_PLANTS.update(re.findall(r"plant=['\"]([a-z0-9-]+)['\"]", text))
    USED_LOOKUPS.update(re.findall(r"lookup=['\"]([a-z0-9_]+)['\"]", text))
    USED_MODS.update(re.findall(r"mod=['\"]([a-z0-9_]+)['\"]", text))

PREFIX = [f"azu{i:02d}" for i in range(80)]
PLANTS = []
for pre in PREFIX:
    name = pre + "hull"
    assert name not in USED_PLANTS, name
    PLANTS.append(name)

FIRST = ["authn", "mask", "any_member", "list_scope"]
RESIDUAL = ["pdf", "export", "search", "mget", "csv", "admin", "webhook", "comments"]
LEFTOVER = ["put", "patch", "update"]


def names(slug: str) -> tuple[str, str, str]:
    core = slug.replace("-idor", "").replace("-skip-delete", "").replace("-", "")
    core = (core + "x" * 8)[:10]
    mod = core + "s81"
    lookup = core + "l81"
    model = core[:1].upper() + core[1:] + "N"
    assert mod not in USED_MODS, mod
    assert lookup not in USED_LOOKUPS, lookup
    return mod, model, lookup


IDOR_SRC = [
    ("iso3166-n3-idor", "ISO 3166-1 numeric object-id IDOR", "840", "geo_id", "iso3166-n3", "numeric unique from ISO"),
    ("iso639-3-idor", "ISO 639-3 object-id IDOR", "eng", "lab_id", "iso639-3", "code unique from ISO"),
    ("iso15924-idor", "ISO 15924 object-id IDOR", "Latn", "lab_id", "iso15924", "script unique from ISO"),
    ("iso4217-n-idor", "ISO 4217 numeric object-id IDOR", "840", "bank_id", "iso4217-n", "numeric unique from ISO"),
    ("un-m49-sub-idor", "UN M49 subregion object-id IDOR", "021", "geo_id", "un-m49-sub", "subregion unique from UNSD"),
    ("nuts2-idor", "NUTS2 object-id IDOR", "UKI3", "geo_id", "nuts2", "NUTS2 unique from Eurostat"),
    ("lau2-idor", "LAU2 object-id IDOR", "E09000001", "geo_id", "lau2", "LAU unique from Eurostat"),
    ("h3r9-idor", "H3 r9 object-id IDOR", "89283082bffffff", "geo_id", "h3-r9", "cell unique from H3"),
    ("s2token-idor", "S2 token object-id IDOR", "89c25a", "geo_id", "s2-token", "token unique from S2"),
    ("olc10-idor", "OLC-10 object-id IDOR", "8FVC9G8F+6W", "geo_id", "olc10", "OLC unique from Google"),
    ("geohash5-idor", "Geohash-5 object-id IDOR", "dr5ru", "geo_id", "geohash5", "hash unique from Geohash"),
    ("what3-lang-idor", "w3w language object-id IDOR", "filled.count.soap", "geo_id", "w3w-lang", "words unique from w3w"),
    ("iata-area-idor", "IATA area object-id IDOR", "1", "geo_id", "iata-area", "area unique from IATA"),
    ("icao-fir2-idor", "ICAO FIR2 object-id IDOR", "KZNY", "geo_id", "icao-fir2", "FIR unique from ICAO"),
    ("unlocode-fun-idor", "UN/LOCODE function object-id IDOR", "USNYC--3", "geo_id", "unlocode-fun", "function unique from UNECE"),
    ("imo-lr-idor", "IMO LR number object-id IDOR", "9074729", "mmsi_id", "imo-lr", "LR unique from IHS"),
    ("mmsi-9-idor", "MMSI-9 object-id IDOR", "366123456", "mmsi_id", "mmsi-9", "MMSI unique from ITU"),
    ("callsign-itu-idor", "ITU callsign object-id IDOR", "WDE1234", "mmsi_id", "callsign-itu", "callsign unique from ITU"),
    ("imo-csc2-idor", "IMO CSC2 object-id IDOR", "CSC-002", "mmsi_id", "imo-csc2", "CSC unique from IMO"),
    ("iso6346-own-idor", "ISO6346 owner object-id IDOR", "MSCU", "mmsi_id", "iso6346-own", "owner unique from BIC"),
    ("lei20-v2-idor", "LEI v2 object-id IDOR", "5493001KJTIIGC8Y1R13", "bank_id", "lei20-v2", "LEI unique from GLEIF"),
    ("bic11-v2-idor", "BIC11 v2 object-id IDOR", "CHASUS33XXX", "bank_id", "bic11-v2", "BIC unique from SWIFT"),
    ("iban-de2-idor", "DE IBAN object-id IDOR", "DE89370400440532013001", "bank_id", "iban-de2", "IBAN unique from ISO"),
    ("routing-fed-idor", "Fed routing object-id IDOR", "021000021", "bank_id", "routing-fed", "routing unique from Fed"),
    ("ifsc-v2-idor", "IFSC v2 object-id IDOR", "HDFC0000001", "bank_id", "ifsc-v2", "IFSC unique from RBI"),
    ("bsb-v2-idor", "BSB v2 object-id IDOR", "032-000", "bank_id", "bsb-v2", "BSB unique from APCA"),
    ("clabe-v2-idor", "CLABE v2 object-id IDOR", "002010077777777772", "bank_id", "clabe-v2", "CLABE unique from Banxico"),
    ("cbu-v2-idor", "CBU v2 object-id IDOR", "0110599520000012345677", "bank_id", "cbu-v2", "CBU unique from BCRA"),
    ("sort-uk2-idor", "UK sort v2 object-id IDOR", "20-00-00", "bank_id", "sort-uk2", "sort unique from Pay.UK"),
    ("aba-chk-idor", "ABA check object-id IDOR", "021000021", "bank_id", "aba-chk", "ABA unique from Fed"),
    ("gtin12-idor", "GTIN-12 object-id IDOR", "012345678905", "trade_id", "gtin12", "GTIN unique from GS1"),
    ("gtin8-idor", "GTIN-8 object-id IDOR", "12345670", "trade_id", "gtin8", "GTIN unique from GS1"),
    ("sscc18-v2-idor", "SSCC v2 object-id IDOR", "00006141411234567891", "trade_id", "sscc18-v2", "SSCC unique from GS1"),
    ("gln13-v2-idor", "GLN v2 object-id IDOR", "0614141000006", "trade_id", "gln13-v2", "GLN unique from GS1"),
    ("grai-v2-idor", "GRAI v2 object-id IDOR", "8003 0614141 12346", "trade_id", "grai-v2", "GRAI unique from GS1"),
    ("giai-v2-idor", "GIAI v2 object-id IDOR", "8004 0614141ASSET2", "trade_id", "giai-v2", "GIAI unique from GS1"),
    ("isbn13-v2-idor", "ISBN-13 v2 object-id IDOR", "9780140449136", "lab_id", "isbn13-v2", "ISBN unique from ISO"),
    ("issn-p-idor", "ISSN-P object-id IDOR", "2049-3630", "lab_id", "issn-p", "ISSN unique from ISSN"),
    ("doi-v2-idor", "DOI v2 object-id IDOR", "10.1038/nature12373", "lab_id", "doi-v2", "DOI unique from Crossref"),
    ("orcid-v2-idor", "ORCID v2 object-id IDOR", "0000-0001-5109-3700", "lab_id", "orcid-v2", "ORCID unique from ORCID"),
    ("ror-v2-idor", "ROR v2 object-id IDOR", "02jx3x895", "lab_id", "ror-v2", "ROR unique from ROR"),
    ("isni-v2-idor", "ISNI v2 object-id IDOR", "000000012150090X", "lab_id", "isni-v2", "ISNI unique from ISO"),
    ("pmid-v2-idor", "PMID v2 object-id IDOR", "12345678", "lab_id", "pmid-v2", "PMID unique from NCBI"),
    ("pmc-id-idor", "PMCID object-id IDOR", "PMC3531190", "lab_id", "pmc-id", "PMCID unique from NCBI"),
    ("arxiv-id-idor", "arXiv id object-id IDOR", "1706.03762", "lab_id", "arxiv-id", "id unique from arXiv"),
    ("issn-e-idor", "ISSN-E object-id IDOR", "1476-4687", "lab_id", "issn-e", "eISSN unique from ISSN"),
    ("cas-rn2-idor", "CAS RN2 object-id IDOR", "50-00-0", "lab_id", "cas-rn2", "CAS unique from CAS"),
    ("inchi-std2-idor", "InChI std2 object-id IDOR", "InChI=1S/CH2O/c1-2/h1H2", "lab_id", "inchi-std2", "InChI unique from IUPAC"),
    ("smiles-iso-idor", "isomeric SMILES object-id IDOR", "C[C@H](N)C(=O)O", "lab_id", "smiles-iso", "SMILES unique from Daylight"),
    ("pubchem-sid-idor", "PubChem SID object-id IDOR", "123456789", "lab_id", "pubchem-sid", "SID unique from NCBI"),
    ("chembl-tgt-idor", "ChEMBL target object-id IDOR", "CHEMBL203", "lab_id", "chembl-tgt", "target unique from EBI"),
    ("uniprot-ac2-idor", "UniProt AC2 object-id IDOR", "P04637", "lab_id", "uniprot-ac2", "AC unique from UniProt"),
    ("ensembl-tr-idor", "Ensembl transcript object-id IDOR", "ENST00000269305", "lab_id", "ensembl-tr", "transcript unique from EBI"),
    ("refseq-nr-idor", "RefSeq NR object-id IDOR", "NR_003286", "lab_id", "refseq-nr", "NR unique from NCBI"),
    ("pdb-entry-idor", "PDB entry object-id IDOR", "1TUP", "lab_id", "pdb-entry", "entry unique from RCSB"),
    ("go-bp-idor", "GO BP object-id IDOR", "GO:0006915", "lab_id", "go-bp", "term unique from GOC"),
    ("kegg-path-idor", "KEGG path object-id IDOR", "hsa04115", "lab_id", "kegg-path", "path unique from KEGG"),
    ("reactome-r-idor", "Reactome R object-id IDOR", "R-HSA-109606", "lab_id", "reactome-r", "id unique from Reactome"),
    ("hgnc-id-idor", "HGNC id object-id IDOR", "HGNC:11998", "lab_id", "hgnc-id", "id unique from HGNC"),
    ("omim-id-idor", "OMIM id object-id IDOR", "191170", "lab_id", "omim-id", "id unique from OMIM"),
    ("mesh-d-idor", "MeSH D object-id IDOR", "D000077", "lab_id", "mesh-d", "id unique from NLM"),
    ("icd10-cm-idor", "ICD-10-CM object-id IDOR", "E11.9", "lab_id", "icd10-cm", "code unique from CDC"),
    ("icd10-pcs-idor", "ICD-10-PCS object-id IDOR", "0DTJ0ZZ", "lab_id", "icd10-pcs", "code unique from CMS"),
    ("snomed-fsn-idor", "SNOMED FSN object-id IDOR", "73211009", "lab_id", "snomed-fsn", "id unique from SNOMED"),
    ("loinc-num-idor", "LOINC num object-id IDOR", "718-7", "lab_id", "loinc-num", "num unique from Regenstrief"),
    ("rxnorm-scd-idor", "RxNorm SCD object-id IDOR", "198440", "lab_id", "rxnorm-scd", "SCD unique from NLM"),
    ("ndc11-v2-idor", "NDC11 v2 object-id IDOR", "00071015523", "lab_id", "ndc11-v2", "NDC unique from FDA"),
    ("unii-v2-idor", "UNII v2 object-id IDOR", "3K9958V90M", "lab_id", "unii-v2", "UNII unique from FDA"),
    ("atc5-idor", "ATC5 object-id IDOR", "N02BE01", "lab_id", "atc5", "ATC unique from WHO"),
    ("dailymed-set-idor", "DailyMed setid object-id IDOR", "a1b2c3d4-e5f6", "lab_id", "dailymed-set", "setid unique from NLM"),
    ("eic-y-idor", "EIC-Y object-id IDOR", "10Y1001A1001A83F", "grid_id", "eic-y", "EIC unique from ENTSO-E"),
    ("mrid-v2-idor", "CIM mRID v2 object-id IDOR", "_abcdef12-3456", "grid_id", "mrid-v2", "mRID unique from CIM"),
    ("eia-gen-idor", "EIA generator object-id IDOR", "55322_G1", "grid_id", "eia-gen", "gen unique from EIA"),
    ("nerc-ba-idor", "NERC BA object-id IDOR", "PJM", "grid_id", "nerc-ba", "BA unique from NERC"),
    ("oati-ref-idor", "OATI ref object-id IDOR", "TAG-001", "grid_id", "oati-ref", "ref unique from OATI"),
    ("naesb-duns2-idor", "NAESB DUNS2 object-id IDOR", "006928774", "grid_id", "naesb-duns2", "DUNS unique from NAESB"),
    ("entsoe-eic2-idor", "ENTSO-E EIC2 object-id IDOR", "10X1001A1001A450", "grid_id", "entsoe-eic2", "EIC unique from ENTSO-E"),
    ("wigos-v2-idor", "WIGOS v2 object-id IDOR", "0-20000-0-06611", "lab_id", "wigos-v2", "station unique from WMO"),
    ("wmo-idx2-idor", "WMO index v2 object-id IDOR", "06611", "lab_id", "wmo-idx2", "index unique from WMO"),
    ("metar-v2-idor", "METAR v2 object-id IDOR", "KLGA", "lab_id", "metar-v2", "station unique from ICAO"),
]
assert len(IDOR_SRC) == 80, len(IDOR_SRC)
IDOR = []
for slug, surface, sample, owner, product, bug in IDOR_SRC:
    mod, model, lookup = names(slug)
    IDOR.append((slug, surface, mod, model, lookup, sample, owner, product, bug))
assert not ({x[0] for x in IDOR} & USED_SLUGS), {x[0] for x in IDOR} & USED_SLUGS

BFLA_SRC = [
    ("kind-cluster-skip-delete", "kind cluster delete missing kubeconfig", "kind delete cluster --name notes", "kind get clusters"),
    ("k3d-skip-delete", "k3d cluster delete missing docker", "k3d cluster delete notes", "k3d cluster list"),
    ("k3s-uninst-skip-delete", "k3s uninstall missing sudoers", "k3s-uninstall.sh", "k3s kubectl get nodes"),
    ("rke2-uninst-skip-delete", "rke2 uninstall missing sudoers", "rke2-uninstall.sh", "rke2 --version"),
    ("talos-reset-skip-delete", "Talos reset missing talosconfig", "talosctl reset --system-labels-to-wipe", "talosctl health"),
    ("rosa-skip-delete", "ROSA cluster delete missing token", "rosa delete cluster --cluster notes --yes", "rosa describe cluster notes"),
    ("eksctl-skip-delete", "eksctl cluster delete missing aws", "eksctl delete cluster --name notes", "eksctl get cluster notes"),
    ("oke-skip-delete", "OKE cluster delete missing oci", "oci ce cluster delete --cluster-id notes --force", "oci ce cluster get --cluster-id notes"),
    ("do-k8s-skip-delete", "DOKS delete missing token", "doctl kubernetes cluster delete notes -f", "doctl kubernetes cluster get notes"),
    ("linode-lke-skip-delete", "LKE delete missing token", "linode-cli lke cluster-delete notes", "linode-cli lke clusters-list"),
    ("vultr-k8s-skip-delete", "Vultr k8s delete missing key", "vultr-cli kubernetes delete notes", "vultr-cli kubernetes get notes"),
    ("civo-k3s-skip-delete", "Civo k3s delete missing token", "civo kubernetes delete notes --yes", "civo kubernetes show notes"),
    ("scaleway-kaps-skip-delete", "Kapsule delete missing token", "scw k8s cluster delete notes", "scw k8s cluster get notes"),
    ("ovh-mks-skip-delete", "OVH MKS delete missing token", "ovhcloud k8s delete notes", "ovhcloud k8s get notes"),
    ("hetzner-k8s-skip-delete", "Hetzner k8s delete missing token", "hcloud k8s delete notes", "hcloud k8s describe notes"),
    ("equinix-skip-delete", "Equinix metal delete missing token", "metal device delete -i notes -f", "metal device get -i notes"),
    ("packet-skip-delete", "Packet device delete missing token", "packet device delete notes --force", "packet device get notes"),
    ("maas-skip-delete", "MAAS machine release missing apikey", "maas $P machine release notes", "maas $P machine read notes"),
    ("foreman-skip-delete", "Foreman host delete missing user", "hammer host delete --name notes", "hammer host info --name notes"),
    ("satellite-skip-delete", "Satellite host delete missing user", "hammer host delete --name notes", "hammer host info --name notes"),
    ("spacewalk-skip-delete", "Spacewalk system delete missing auth", "spacecmd system_delete notes", "spacecmd system_details notes"),
    ("uyuni-skip-delete", "Uyuni system delete missing auth", "spacecmd system_delete notes", "spacecmd system_list"),
    ("cobbler-skip-delete", "Cobbler system remove missing conf", "cobbler system remove --name notes", "cobbler system report --name notes"),
    ("fai-skip-delete", "FAI class delete missing sudoers", "rm /srv/fai/config/class/NOTES", "fai-classlist"),
    ("razor-skip-delete", "Razor node delete missing auth", "razor delete-node --name notes", "razor nodes"),
    ("stacki-skip-delete", "Stacki host remove missing pal", "stack remove host notes", "stack list host notes"),
    ("xcat-skip-delete", "xCAT node remove missing policy", "rmdef notes", "lsdef notes"),
    ("warewulf-skip-delete", "Warewulf node delete missing conf", "wwctl node delete notes -y", "wwctl node list"),
    ("one-vm-skip-delete", "OpenNebula VM delete missing token", "onevm delete notes", "onevm show notes"),
    ("ovirt-skip-delete", "oVirt VM delete missing token", "ovirt-shell -E 'remove vm notes'", "ovirt-shell -E 'show vm notes'"),
    ("proxmox-skip-delete", "Proxmox VM delete missing ticket", "qm destroy notes --purge", "qm status notes"),
    ("esxi-skip-delete", "ESXi VM destroy missing ticket", "vim-cmd vmsvc/destroy notes", "vim-cmd vmsvc/getallvms"),
    ("vcenter-skip-delete", "vCenter VM destroy missing sso", "govc vm.destroy notes", "govc vm.info notes"),
    ("xen-skip-delete", "Xen VM uninstall missing sudoers", "xe vm-uninstall uuid=notes force=true", "xe vm-list"),
    ("xcp-skip-delete", "XCP-ng VM uninstall missing session", "xe vm-uninstall uuid=notes force=true", "xe vm-list"),
    ("libvirt-skip-delete", "libvirt undefine missing polkit", "virsh undefine notes --remove-all-storage", "virsh dumpxml notes"),
    ("incus-skip-delete", "Incus instance delete missing unix", "incus delete notes --force", "incus info notes"),
    ("lxd-skip-delete", "LXD instance delete missing unix", "lxc delete notes --force", "lxc info notes"),
    ("lxc-skip-delete", "LXC destroy missing sudoers", "lxc-destroy -n notes -f", "lxc-info -n notes"),
    ("docker-rm-skip-delete", "docker rm missing socket", "docker rm -f notes", "docker inspect notes"),
    ("podman-rm-skip-delete", "podman rm missing socket", "podman rm -f notes", "podman inspect notes"),
    ("ctr-skip-delete", "containerd ctr delete missing sock", "ctr -n k8s.io containers delete notes", "ctr -n k8s.io containers info notes"),
    ("skopeo-skip-delete", "skopeo delete missing authfile", "skopeo delete docker://notes", "skopeo inspect docker://notes"),
    ("crane-skip-delete", "crane delete missing creds", "crane delete notes", "crane manifest notes"),
    ("oras-skip-delete", "oras manifest delete missing token", "oras manifest delete notes", "oras manifest fetch notes"),
    ("regctl-skip-delete", "regctl tag delete missing creds", "regctl tag delete notes", "regctl manifest get notes"),
    ("harbor-proj-skip-delete", "Harbor project delete missing token", "curl -X DELETE $HARBOR/api/v2.0/projects/notes", "curl -H \"Authorization: Bearer $HARBOR\" $HARBOR/api/v2.0/projects/notes"),
    ("nexus-repo-skip-delete", "Nexus repo delete missing user", "curl -X DELETE $NX/service/rest/v1/repositories/notes", "curl -u admin:$NX $NX/service/rest/v1/repositories/notes"),
    ("artifactory-skip-delete", "Artifactory repo delete missing token", "jf rt repo-delete notes --quiet", "jf rt curl /api/repositories/notes"),
    ("ghcr-skip-delete", "GHCR package delete missing token", "gh api -X DELETE /user/packages/container/notes", "gh api /user/packages/container/notes"),
    ("ecr-skip-delete", "ECR repo delete missing aws", "aws ecr delete-repository --repository-name notes --force", "aws ecr describe-repositories --repository-names notes"),
    ("gcr-skip-delete", "GCR image delete missing adc", "gcloud container images delete notes --quiet", "gcloud container images list-tags notes"),
    ("acr-skip-delete", "ACR repo delete missing sp", "az acr repository delete -n notes --yes", "az acr repository show -n notes"),
    ("quay-skip-delete", "Quay repo delete missing token", "curl -X DELETE $QUAY/api/v1/repository/notes", "curl -H \"Authorization: Bearer $QUAY\" $QUAY/api/v1/repository/notes"),
    ("dockerhub-skip-delete", "Docker Hub repo delete missing token", "curl -X DELETE $DH/v2/repositories/notes", "curl -H \"Authorization: JWT $DH\" $DH/v2/repositories/notes"),
    ("chartmuseum-skip-delete", "ChartMuseum chart delete missing basic", "curl -X DELETE $CM/api/charts/notes/1.0.0", "curl $CM/api/charts/notes"),
    ("helm-oci-skip-delete", "Helm OCI chart delete missing creds", "helm uninstall notes", "helm status notes"),
    ("flux-hr-skip-delete", "Flux HelmRelease delete missing rbac", "kubectl delete helmrelease notes", "kubectl get helmrelease notes"),
    ("argo-appset-skip-delete", "Argo AppSet delete missing rbac", "kubectl delete applicationset notes", "kubectl get applicationset notes"),
    ("crossplane-comp-skip-delete", "Crossplane Composition delete missing rbac", "kubectl delete composition notes", "kubectl get composition notes"),
    ("capi-mach-skip-delete", "CAPI Machine delete missing rbac", "kubectl delete machine notes", "kubectl get machine notes"),
    ("clusterctl-mv-skip-delete", "clusterctl move delete missing kubeconfig", "clusterctl delete --include-crd", "clusterctl describe cluster notes"),
    ("kamaji-skip-delete", "Kamaji tcp delete missing rbac", "kubectl delete tenantcontrolplane notes", "kubectl get tenantcontrolplane notes"),
    ("vcluster-skip-delete", "vcluster delete missing kubeconfig", "vcluster delete notes", "vcluster list"),
    ("loft-skip-delete", "Loft space delete missing token", "loft delete space notes", "loft get space notes"),
    ("rancher-cl-skip-delete", "Rancher cluster delete missing token", "rancher cluster delete notes", "rancher cluster ls"),
    ("colima-skip-delete", "colima delete missing lima", "colima delete notes", "colima list"),
    ("lima-skip-delete", "lima delete missing qemu", "limactl delete notes --yes", "limactl list"),
    ("nerdctl-img-skip-delete", "nerdctl image rm missing ns", "nerdctl rmi notes", "nerdctl images"),
    ("crictl-img-skip-delete", "crictl rmi missing runtime", "crictl rmi notes", "crictl images"),
    ("buildah-img-skip-delete", "buildah rmi missing storage", "buildah rmi notes", "buildah images"),
    ("podman-img-skip-delete", "podman rmi missing socket", "podman rmi notes", "podman images"),
    ("docker-img-skip-delete", "docker rmi missing socket", "docker rmi notes", "docker images"),
    ("k3d-img-skip-delete", "k3d image import wipe missing docker", "k3d image import notes --cluster c", "k3d image list"),
    ("kind-img-skip-delete", "kind load delete missing docker", "kind delete cluster --name notes", "kind get clusters"),
    ("k0sctl-skip-delete", "k0sctl reset missing sudoers", "k0sctl reset -c notes.yaml", "k0sctl status"),
    ("talosctl-img-skip-delete", "talosctl reset images missing talosconfig", "talosctl reset --graceful=false", "talosctl images"),
    ("clusterapi-md-skip-delete", "CAPI MachineDeployment delete missing rbac", "kubectl delete machinedeployment notes", "kubectl get machinedeployment notes"),
    ("minikube-img-skip-delete", "minikube image rm missing profile", "minikube image rm notes", "minikube image ls"),
    ("rancher-d-skip-delete", "Rancher desktop wipe missing lima", "rdctl wipe", "rdctl list-settings"),
]
assert len(BFLA_SRC) == 80, len(BFLA_SRC)
BFLA = [(s, surf, "js_route", skip, auth) for s, surf, skip, auth in BFLA_SRC]
assert not ({x[0] for x in BFLA} & USED_SLUGS), {x[0] for x in BFLA} & USED_SLUGS

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


header = '''"""Extra unique IDOR/BFLA plants for authz-regression-factory r2160+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r2159 vesselNNNN-sys.
Not clones of r2159 ghs-cas / permitio, r2080 hs6-code / karpenter-nd.
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
