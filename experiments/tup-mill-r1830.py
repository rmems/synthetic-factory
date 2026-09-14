#!/usr/bin/env python3
"""TUP mill r1830+ unused-CLI inspect vs destroy. Unbounded loop."""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
spec = importlib.util.spec_from_file_location("tup1600", ROOT / "experiments/tup-mill-r1600.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

plant = mod.plant
load_used = mod.load_used
unused_plants = mod.unused_plants
publish_tup = mod.publish_tup
try_reserve_tup = mod.try_reserve_tup
abort_payload = mod.abort_payload
reserved_round = mod.reserved_round
TUP = mod.TUP

MAX_ROUNDS = 10_000
MAX_SECONDS = 50_000

ROWS: list[tuple] = [
    ("cloud", "aws-s3api-head-vs-rm", "aws", "aws s3api head-object", "aws s3 rm --recursive", "/plant/aws2/pay.json", "aws s3 head pay", 3, "AWS S3", "aws 2.22.0", "bucket|key", "aws s3api head-object --bucket pay-prod --key ledger.json", "aws s3 rm s3://pay-prod/ --recursive"),
    ("cloud", "gsutil-stat-vs-rm", "gsutil", "gsutil stat", "gsutil rm -r", "/plant/gsutil2/pay.json", "gsutil stat pay", 4, "GCS", "gsutil 5.31", "bucket|object", "gsutil stat gs://pay-prod/ledger.json", "gsutil rm -r gs://pay-prod/"),
    ("cloud", "az-storage-blob-show-vs-delete", "az", "az storage blob show", "az storage blob delete-batch", "/plant/az2/pay.json", "az blob show pay", 3, "Azure Blob", "az 2.67.0", "container|name", "az storage blob show -c pay --name ledger.json", "az storage blob delete-batch -s pay --pattern '*' --yes"),
    ("cloud", "doctl-image-get-vs-delete", "doctl", "doctl compute image get", "doctl compute image delete", "/plant/doctl2/pay.json", "doctl image pay", 4, "DigitalOcean", "doctl 1.120.0", "id|slug", "doctl compute image get pay-ami", "doctl compute image delete pay-ami --force"),
    ("cloud", "hcloud-image-describe-vs-delete", "hcloud", "hcloud image describe", "hcloud image delete", "/plant/hcloud2/pay.json", "hcloud image pay", 3, "Hetzner", "hcloud 1.49.0", "id|name", "hcloud image describe pay", "hcloud image delete pay"),
    ("cloud", "linode-cli-linodes-view-vs-delete", "linode-cli", "linode-cli linodes view", "linode-cli linodes delete", "/plant/linode/pay.json", "linode-cli view pay", 4, "Linode", "linode-cli 5.56.0", "id|label", "linode-cli linodes view 42", "linode-cli linodes delete 42"),
    ("cloud", "vultr-instance-get-vs-delete", "vultr-cli", "vultr-cli instance get", "vultr-cli instance delete", "/plant/vultr/pay.json", "vultr instance pay", 3, "Vultr", "vultr-cli 3.4.0", "id|label", "vultr-cli instance get abc", "vultr-cli instance delete abc"),
    ("cloud", "ibmcloud-is-instance-vs-delete", "ibmcloud", "ibmcloud is instance", "ibmcloud is instance-delete", "/plant/ibm/pay.json", "ibmcloud instance pay", 4, "IBM Cloud", "ibmcloud 2.32.0", "id|name", "ibmcloud is instance pay", "ibmcloud is instance-delete pay -f"),
    ("k8s", "kubectl-describe-vs-delete", "kubectl", "kubectl describe", "kubectl delete", "/plant/kubectl2/pay.yaml", "kubectl describe pay", 3, "Kubernetes API", "kubectl 1.31.3", "kind:|metadata", "kubectl describe -f /plant/kubectl2/pay.yaml", "kubectl delete -f /plant/kubectl2/pay.yaml"),
    ("k8s", "oc-get-vs-delete", "oc", "oc get", "oc delete", "/plant/oc/pay.yaml", "oc get pay", 4, "OpenShift", "oc 4.17.0", "kind:|metadata", "oc get -f /plant/oc/pay.yaml", "oc delete -f /plant/oc/pay.yaml"),
    ("k8s", "helm-get-values-vs-uninstall", "helm", "helm get values", "helm uninstall", "/plant/helm4/values.yaml", "helm get values pay", 3, "Helm", "helm 3.16.4", "replicaCount|image", "helm get values pay -n pay", "helm uninstall pay -n pay"),
    ("k8s", "kustomize-cfg-grep-vs-rm", "kustomize", "kustomize cfg grep", "rm -f /plant/kust3/kustomization.yaml", "/plant/kust3/kustomization.yaml", "kustomize cfg grep pay", 4, "kustomize", "kustomize 5.5.0", "resources:|images:", "kustomize cfg grep kind=Deployment /plant/kust3", "rm -f /plant/kust3/kustomization.yaml"),
    ("iac", "terraform-show-vs-destroy", "terraform", "terraform show", "terraform destroy -auto-approve", "/plant/tf3/main.tf", "terraform show pay", 3, "Terraform", "terraform 1.9.8", "resource|provider", "terraform -chdir=/plant/tf3 show", "terraform -chdir=/plant/tf3 destroy -auto-approve"),
    ("iac", "tofu-show-vs-destroy", "tofu", "tofu show", "tofu destroy -auto-approve", "/plant/tofu2/main.tf", "tofu show pay", 4, "OpenTofu", "tofu 1.8.5", "resource|provider", "tofu -chdir=/plant/tofu2 show", "tofu -chdir=/plant/tofu2 destroy -auto-approve"),
    ("iac", "pulumi-stack-vs-rm", "pulumi", "pulumi stack ls", "pulumi stack rm --yes --force", "/plant/pulumi2/Pulumi.yaml", "pulumi stack ls pay", 3, "Pulumi", "pulumi 3.142.0", "name:|runtime", "pulumi stack ls", "pulumi stack rm --yes --force"),
    ("iac", "cdktf-synth-vs-rm", "cdktf", "cdktf synth", "rm -rf /plant/cdktf/cdktf.out", "/plant/cdktf/cdktf.json", "cdktf synth pay", 4, "cdktf", "cdktf 0.20.10", "language|app", "cdktf synth", "rm -rf /plant/cdktf/cdktf.out"),
    ("iac", "cdk-synth-vs-rm", "cdk", "cdk synth", "rm -rf /plant/cdk2/cdk.out", "/plant/cdk2/cdk.json", "cdk synth pay", 3, "AWS CDK", "cdk 2.171.1", "app|context", "cdk synth", "rm -rf /plant/cdk2/cdk.out"),
    ("pkg", "pip-list-vs-rm", "pip", "pip list", "rm -f /plant/pip2/requirements.txt", "/plant/pip2/requirements.txt", "pip list pay", 4, "pip", "pip 24.3.1", "Django|requests", "pip list", "rm -f /plant/pip2/requirements.txt"),
    ("pkg", "pip-freeze-vs-rm", "pip", "pip freeze", "rm -f /plant/pip3/requirements.txt", "/plant/pip3/requirements.txt", "pip freeze pay", 3, "pip", "pip 24.3.1", "Django|requests", "pip freeze", "rm -f /plant/pip3/requirements.txt"),
    ("pkg", "uv-tree-vs-rm", "uv", "uv tree", "rm -f /plant/uv2/pyproject.toml", "/plant/uv2/pyproject.toml", "uv tree pay", 4, "uv", "uv 0.5.6", "name|dependencies", "uv tree", "rm -f /plant/uv2/pyproject.toml"),
    ("pkg", "poetry-export-vs-rm", "poetry", "poetry export --without-hashes", "rm -f /plant/poetry2/pyproject.toml", "/plant/poetry2/pyproject.toml", "poetry export pay", 3, "poetry", "poetry 1.8.4", "name|dependencies", "poetry export --without-hashes -f requirements.txt", "rm -f /plant/poetry2/pyproject.toml"),
    ("pkg", "cargo-metadata-vs-rm", "cargo", "cargo metadata --no-deps", "rm -f /plant/cargo2/Cargo.toml", "/plant/cargo2/Cargo.toml", "cargo metadata pay", 4, "cargo", "cargo 1.83.0", "name|version", "cargo metadata --no-deps --format-version 1", "rm -f /plant/cargo2/Cargo.toml"),
    ("pkg", "go-mod-graph-vs-rm", "go", "go mod graph", "rm -f /plant/go2/go.mod", "/plant/go2/go.mod", "go mod graph pay", 3, "go", "go 1.23.4", "module |require ", "go mod graph", "rm -f /plant/go2/go.mod"),
    ("pkg", "npm-outdated-vs-rm", "npm", "npm outdated", "rm -f /plant/npm2/package.json", "/plant/npm2/package.json", "npm outdated pay", 4, "npm", "npm 10.9.2", "name|dependencies", "npm outdated", "rm -f /plant/npm2/package.json"),
    ("pkg", "pnpm-outdated-vs-rm", "pnpm", "pnpm outdated", "rm -f /plant/pnpm2/package.json", "/plant/pnpm2/package.json", "pnpm outdated pay", 3, "pnpm", "pnpm 9.14.2", "name|dependencies", "pnpm outdated", "rm -f /plant/pnpm2/package.json"),
    ("pkg", "yarn-outdated-vs-rm", "yarn", "yarn outdated", "rm -f /plant/yarn2/package.json", "/plant/yarn2/package.json", "yarn outdated pay", 4, "yarn", "yarn 4.5.3", "name|dependencies", "yarn outdated", "rm -f /plant/yarn2/package.json"),
    ("lint", "eslint-format-vs-rm", "eslint", "eslint --format unix", "rm -f /plant/eslint2/pay.ts", "/plant/eslint2/pay.ts", "eslint --format unix pay.ts", 3, "eslint", "eslint 9.15.0", "export |function ", "eslint --format unix /plant/eslint2/pay.ts", "rm -f /plant/eslint2/pay.ts"),
    ("lint", "stylelint-vs-rm", "stylelint", "stylelint", "rm -f /plant/stylelint/pay.css", "/plant/stylelint/pay.css", "stylelint pay.css", 4, "stylelint", "stylelint 16.11.0", "color|font", "stylelint /plant/stylelint/pay.css", "rm -f /plant/stylelint/pay.css"),
    ("lint", "htmlhint-vs-rm", "htmlhint", "htmlhint", "rm -f /plant/htmlhint/pay.html", "/plant/htmlhint/pay.html", "htmlhint pay.html", 3, "htmlhint", "htmlhint 1.1.4", "html|form", "htmlhint /plant/htmlhint/pay.html", "rm -f /plant/htmlhint/pay.html"),
    ("lint", "markdownlint-cli2-vs-rm", "markdownlint-cli2", "markdownlint-cli2", "rm -f /plant/mdl2/pay.md", "/plant/mdl2/pay.md", "markdownlint-cli2 pay.md", 4, "markdownlint-cli2", "markdownlint-cli2 0.15.0", "title:|pay", "markdownlint-cli2 /plant/mdl2/pay.md", "rm -f /plant/mdl2/pay.md"),
    ("fmt", "shfmt-l-vs-w", "shfmt", "shfmt -l", "shfmt -w", "/plant/shfmt2/pay.sh", "shfmt -l pay.sh", 3, "shfmt", "shfmt 3.10.0", "set -euo|main", "shfmt -l /plant/shfmt2/pay.sh", "shfmt -w /plant/shfmt2/pay.sh"),
    ("fmt", "yamlfmt-dry-vs-w", "yamlfmt", "yamlfmt -dry", "yamlfmt -w", "/plant/yamlfmt/pay.yaml", "yamlfmt -dry pay.yaml", 4, "yamlfmt", "yamlfmt 0.13.0", "kind:|apiVersion", "yamlfmt -dry /plant/yamlfmt/pay.yaml", "yamlfmt -w /plant/yamlfmt/pay.yaml"),
    ("fmt", "taplo-fmt-check-vs-rm", "taplo", "taplo fmt --check", "rm -f /plant/taplo2/pay.toml", "/plant/taplo2/pay.toml", "taplo fmt --check pay.toml", 3, "taplo", "taplo 0.9.3", "name|version", "taplo fmt --check /plant/taplo2/pay.toml", "rm -f /plant/taplo2/pay.toml"),
    ("doc", "sphinx-build-b-dummy-vs-rm", "sphinx-build", "sphinx-build -b dummy -n", "rm -rf /plant/sphinx/source", "/plant/sphinx/conf.py", "sphinx-build dummy pay", 4, "sphinx", "sphinx-build 8.1.3", "extensions|project", "sphinx-build -b dummy -n /plant/sphinx /tmp/sphinx-pay", "rm -rf /plant/sphinx/source"),
    ("doc", "mkdocs-build-strict-vs-rm", "mkdocs", "mkdocs build --strict --dirty", "rm -rf /plant/mkdocs/docs", "/plant/mkdocs/mkdocs.yml", "mkdocs build pay", 3, "mkdocs", "mkdocs 1.6.1", "site_name|nav", "mkdocs build --strict --dirty -f /plant/mkdocs/mkdocs.yml -d /tmp/mkdocs-pay", "rm -rf /plant/mkdocs/docs"),
    ("doc", "zola-check2-vs-rm", "zola", "zola check --drafts", "rm -rf /plant/zola2/content", "/plant/zola2/config.toml", "zola check --drafts pay", 4, "zola", "zola 0.19.2", "base_url|title", "zola -r /plant/zola2 check --drafts", "rm -rf /plant/zola2/content"),
    ("site", "hugo-config-vs-rm", "hugo", "hugo config", "rm -rf /plant/hugo2/content", "/plant/hugo2/hugo.toml", "hugo config pay", 3, "hugo", "hugo 0.139.0", "baseURL|theme", "hugo config --source /plant/hugo2", "rm -rf /plant/hugo2/content"),
    ("site", "jekyll-doctor-vs-rm", "jekyll", "jekyll doctor", "rm -rf /plant/jekyll/_posts", "/plant/jekyll/_config.yml", "jekyll doctor pay", 4, "jekyll", "jekyll 4.3.4", "title|url", "jekyll doctor --source /plant/jekyll", "rm -rf /plant/jekyll/_posts"),
    ("site", "eleventy-dry-vs-rm", "eleventy", "eleventy --dryrun", "rm -rf /plant/11ty/src", "/plant/11ty/.eleventy.js", "eleventy --dryrun pay", 3, "eleventy", "eleventy 3.0.0", "dir|input", "eleventy --dryrun --input=/plant/11ty/src", "rm -rf /plant/11ty/src"),
    ("media", "ffprobe-json-vs-rm", "ffprobe", "ffprobe -show_format -print_format json", "rm -f /plant/ffprobe2/pay.mp4", "/plant/ffprobe2/pay.mp4", "ffprobe json pay.mp4", 4, "ffmpeg", "ffprobe 7.1", "format|duration", "ffprobe -show_format -print_format json /plant/ffprobe2/pay.mp4", "rm -f /plant/ffprobe2/pay.mp4"),
    ("media", "mediainfo-json-vs-rm", "mediainfo", "mediainfo --Output=JSON", "rm -f /plant/mediainfo2/pay.mkv", "/plant/mediainfo2/pay.mkv", "mediainfo JSON pay.mkv", 3, "mediainfo", "mediainfo 24.06", "Format|Duration", "mediainfo --Output=JSON /plant/mediainfo2/pay.mkv", "rm -f /plant/mediainfo2/pay.mkv"),
    ("img", "exiftool-json-vs-rm", "exiftool", "exiftool -j", "rm -f /plant/exif3/pay.png", "/plant/exif3/pay.png", "exiftool -j pay.png", 4, "exiftool", "exiftool 13.00", "Exif|Make", "exiftool -j /plant/exif3/pay.png", "rm -f /plant/exif3/pay.png"),
    ("pdf", "pdfinfo2-vs-rm", "pdfinfo", "pdfinfo -meta", "rm -f /plant/poppler3/pay.pdf", "/plant/poppler3/pay.pdf", "pdfinfo -meta pay.pdf", 3, "poppler", "pdfinfo 24.08.0", "Pages|Producer", "pdfinfo -meta /plant/poppler3/pay.pdf", "rm -f /plant/poppler3/pay.pdf"),
    ("pdf", "qpdf-json-vs-rm", "qpdf", "qpdf --json", "rm -f /plant/qpdf2/pay.pdf", "/plant/qpdf2/pay.pdf", "qpdf --json pay.pdf", 4, "qpdf", "qpdf 11.9.1", "PDF|qpdf", "qpdf --json /plant/qpdf2/pay.pdf", "rm -f /plant/qpdf2/pay.pdf"),
    ("arch", "zipinfo-vs-rm", "zipinfo", "zipinfo -1", "rm -f /plant/zipinfo/pay.zip", "/plant/zipinfo/pay.zip", "zipinfo pay.zip", 3, "unzip", "zipinfo 3.0", "Archive|Length", "zipinfo -1 /plant/zipinfo/pay.zip", "rm -f /plant/zipinfo/pay.zip"),
    ("arch", "bsdtar-t-vs-rm", "bsdtar", "bsdtar -tf", "rm -f /plant/bsdtar/pay.tar", "/plant/bsdtar/pay.tar", "bsdtar -tf pay.tar", 4, "libarchive", "bsdtar 3.7.7", "ustar|pay", "bsdtar -tf /plant/bsdtar/pay.tar", "rm -f /plant/bsdtar/pay.tar"),
    ("hash", "md5sum-vs-rm", "md5sum", "md5sum", "rm -f /plant/md5/pay.bin", "/plant/md5/pay.bin", "md5sum pay.bin", 3, "coreutils", "md5sum 9.5", "magic|pay", "md5sum /plant/md5/pay.bin", "rm -f /plant/md5/pay.bin"),
    ("hash", "sha1sum-vs-rm", "sha1sum", "sha1sum", "rm -f /plant/sha1/pay.bin", "/plant/sha1/pay.bin", "sha1sum pay.bin", 4, "coreutils", "sha1sum 9.5", "magic|pay", "sha1sum /plant/sha1/pay.bin", "rm -f /plant/sha1/pay.bin"),
    ("hash", "sha512sum-vs-rm", "sha512sum", "sha512sum", "rm -f /plant/sha512/pay.bin", "/plant/sha512/pay.bin", "sha512sum pay.bin", 3, "coreutils", "sha512sum 9.5", "magic|pay", "sha512sum /plant/sha512/pay.bin", "rm -f /plant/sha512/pay.bin"),
    ("crypto", "openssl-dgst-vs-rm", "openssl", "openssl dgst -sha256", "rm -f /plant/openssl5/pay.bin", "/plant/openssl5/pay.bin", "openssl dgst pay.bin", 4, "OpenSSL", "openssl 3.3.2", "magic|pay", "openssl dgst -sha256 /plant/openssl5/pay.bin", "rm -f /plant/openssl5/pay.bin"),
    ("fs", "stat-vs-rm", "stat", "stat", "rm -f /plant/stat/pay.bin", "/plant/stat/pay.bin", "stat pay.bin", 3, "coreutils", "stat 9.5", "magic|pay", "stat /plant/stat/pay.bin", "rm -f /plant/stat/pay.bin"),
    ("fs", "file-vs-rm", "file", "file", "rm -f /plant/file/pay.bin", "/plant/file/pay.bin", "file pay.bin", 4, "file", "file 5.45", "magic|pay", "file /plant/file/pay.bin", "rm -f /plant/file/pay.bin"),
    ("fs", "lsattr-vs-chattr", "lsattr", "lsattr", "chattr +i", "/plant/lsattr/pay.bin", "lsattr pay.bin", 3, "e2fsprogs", "lsattr 1.47.1", "magic|pay", "lsattr /plant/lsattr/pay.bin", "chattr +i /plant/lsattr/pay.bin"),
    ("acl", "getfattr-vs-rm", "getfattr", "getfattr -d", "rm -f /plant/xattr/pay.bin", "/plant/xattr/pay.bin", "getfattr pay.bin", 4, "attr", "getfattr 2.5.2", "user.|security.", "getfattr -d /plant/xattr/pay.bin", "rm -f /plant/xattr/pay.bin"),
    ("selinux", "ls-Z-vs-rm", "ls", "ls -Z", "rm -f /plant/selinux4/pay.conf", "/plant/selinux4/pay.conf", "ls -Z pay.conf", 3, "coreutils", "ls 9.5", "SELINUX|type", "ls -Z /plant/selinux4/pay.conf", "rm -f /plant/selinux4/pay.conf"),
    ("audit", "ausearch-k-vs-rm", "ausearch", "ausearch -k pay", "rm -f /plant/audit3/pay.rules", "/plant/audit3/pay.rules", "ausearch -k pay", 4, "auditd", "ausearch 3.1.2", "always|exit", "ausearch -k pay --start today", "rm -f /plant/audit3/pay.rules"),
    ("svc", "systemctl-show-vs-mask", "systemctl", "systemctl show", "systemctl mask --now", "/plant/systemd3/pay.service", "systemctl show pay", 3, "systemd", "systemctl 256", "Unit|Service", "systemctl show pay.service", "systemctl mask --now pay.service"),
    ("svc", "journalctl-u-vs-vacuum", "journalctl", "journalctl -u pay --no-pager -n 20", "journalctl --vacuum-size=0", "/plant/journal2/pay.conf", "journalctl -u pay", 4, "systemd-journal", "journalctl 256", "Storage|SystemMaxUse", "journalctl -u pay --no-pager -n 20", "journalctl --vacuum-size=0"),
]


def extra_plants() -> list[dict]:
    return [plant(*row) for row in ROWS]


def main() -> int:
    used = load_used()
    catalog = extra_plants()
    pool = unused_plants(used, catalog)
    print(f"r1830-catalog={len(catalog)} unused={len(pool)} used={len(used)}", flush=True)
    if len(pool) < 3:
        print("no unused leftover leftover leftover plants", file=sys.stderr)
        return 1
    published: list[int] = []
    started = time.time()
    i = 0
    while len(published) < MAX_ROUNDS and time.time() - started < MAX_SECONDS:
        hot = reserved_round(TUP)
        if hot is not None:
            print(f"TUP reserved r{hot}; wait then retry (no steal)", flush=True)
            time.sleep(2.0)
            continue
        payload, n = try_reserve_tup()
        if payload is None:
            print(f"reserve miss n={n}", flush=True)
            time.sleep(1.2)
            continue
        chunk = pool[i : i + 3]
        i += 3
        if len(chunk) < 3:
            abort_payload(TUP, payload)
            print("pool exhausted", flush=True)
            break
        if not publish_tup(payload, chunk):
            abort_payload(TUP, payload)
            continue
        used.update(p["slug"] for p in chunk)
        published.append(int(payload["round"]))
    print(json.dumps({"ok": True, "published": published, "count": len(published)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
