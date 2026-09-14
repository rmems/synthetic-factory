#!/usr/bin/env python3
"""NTP unique leftover leftover leftover leftover mill wave 11: NEW dest plants."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ntp_mill_unique_llll2",
    ROOT / "experiments/ntp-mill-unique-llll2.py",
)
mod2 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod2)

s_from = mod2.s_from
l_from = mod2.l_from

SUCCESS = [
    s_from(0, "ansible-playbook-leftover-as-dest", "anpb", "ansible playbook leftover", ".ansible/playbook.yml", "Ansible playbook leftover YAML", "ansible leftover && cat .ansible/playbook.yml", "not ansible leftover; Ansible playbook leftover is not dest", "treat Ansible leftover YAML as dest then CLI parquet.", "ansible leftover; # playbook yml claimed dest", "ansible leftover|.ansible/playbook"),
    s_from(1, "puppet-catalog-leftover-as-dest", "ppct", "puppet catalog leftover", ".puppet/catalog.json", "Puppet catalog leftover JSON", "puppet leftover && cat .puppet/catalog.json", "not puppet leftover; Puppet catalog leftover is not dest", "treat Puppet leftover JSON as dest then CLI parquet.", "puppet leftover; # catalog json claimed dest", "puppet leftover|.puppet/catalog"),
    s_from(2, "chef-cookbook-leftover-as-dest", "chcb", "chef cookbook leftover", ".chef/cookbook.rb", "Chef cookbook leftover", "chef leftover && cat .chef/cookbook.rb", "not chef leftover; Chef cookbook leftover is not dest", "treat Chef leftover cookbook as dest then CLI parquet.", "chef leftover; # cookbook rb claimed dest", "chef leftover|.chef/cookbook"),
    s_from(3, "salt-state-leftover-as-dest", "slst", "salt state leftover", ".salt/state.sls", "Salt state leftover", "salt leftover && cat .salt/state.sls", "not salt leftover; Salt state leftover is not dest", "treat Salt leftover SLS as dest then CLI parquet.", "salt leftover; # state sls claimed dest", "salt leftover|.salt/state"),
    s_from(4, "opentofu-state-leftover-as-dest", "otst", "opentofu state leftover", ".opentofu/state.json", "OpenTofu state leftover JSON", "tofu leftover && cat .opentofu/state.json", "not terraform leftover; OpenTofu state leftover is not dest", "treat OpenTofu leftover JSON as dest then CLI parquet.", "opentofu leftover; # state json claimed dest", "opentofu leftover|.opentofu/state"),
    s_from(5, "cdktf-synth-leftover-as-dest", "cdsy", "cdktf synth leftover", ".cdktf/synth.json", "CDKTF synth leftover JSON", "cdktf leftover && cat .cdktf/synth.json", "not terraform leftover; CDKTF synth leftover is not dest", "treat CDKTF leftover JSON as dest then CLI parquet.", "cdktf leftover; # synth json claimed dest", "cdktf leftover|.cdktf/synth"),
    s_from(6, "atlantis-plan-leftover-as-dest", "atpl", "atlantis plan leftover", ".atlantis/plan.json", "Atlantis plan leftover JSON", "atlantis leftover && cat .atlantis/plan.json", "not terraform leftover; Atlantis plan leftover is not dest", "treat Atlantis leftover JSON as dest then CLI parquet.", "atlantis leftover; # plan json claimed dest", "atlantis leftover|.atlantis/plan"),
    s_from(7, "spacelift-stack-leftover-as-dest", "slsk", "spacelift stack leftover", ".spacelift/stack.json", "Spacelift stack leftover JSON", "spacelift leftover && cat .spacelift/stack.json", "not terraform leftover; Spacelift stack leftover is not dest", "treat Spacelift leftover JSON as dest then CLI parquet.", "spacelift leftover; # stack json claimed dest", "spacelift leftover|.spacelift/stack"),
    s_from(8, "env0-deployment-leftover-as-dest", "e0dp", "env0 deployment leftover", ".env0/deployment.json", "env0 deployment leftover JSON", "env0 leftover && cat .env0/deployment.json", "not terraform leftover; env0 deployment leftover is not dest", "treat env0 leftover JSON as dest then CLI parquet.", "env0 leftover; # deployment json claimed dest", "env0 leftover|.env0/deployment"),
    s_from(9, "scalr-run-leftover-as-dest", "scrr", "scalr run leftover", ".scalr/run.json", "Scalr run leftover JSON", "scalr leftover && cat .scalr/run.json", "not terraform leftover; Scalr run leftover is not dest", "treat Scalr leftover JSON as dest then CLI parquet.", "scalr leftover; # run json claimed dest", "scalr leftover|.scalr/run"),
    s_from(10, "infracost-breakdown-leftover-as-dest", "icbd", "infracost breakdown leftover", ".infracost/breakdown.json", "Infracost breakdown leftover JSON", "infracost leftover && cat .infracost/breakdown.json", "not infracost leftover; Infracost breakdown leftover is not dest", "treat Infracost leftover JSON as dest then CLI parquet.", "infracost leftover; # breakdown json claimed dest", "infracost leftover|.infracost/breakdown"),
    s_from(11, "checkov-report-leftover-as-dest", "ckrp", "checkov report leftover", ".checkov/report.json", "Checkov report leftover JSON", "checkov leftover && cat .checkov/report.json", "not checkov leftover; Checkov report leftover is not dest", "treat Checkov leftover JSON as dest then CLI parquet.", "checkov leftover; # report json claimed dest", "checkov leftover|.checkov/report"),
    s_from(12, "tfsec-report-leftover-as-dest", "tsrp", "tfsec report leftover", ".tfsec/report.json", "tfsec report leftover JSON", "tfsec leftover && cat .tfsec/report.json", "not tfsec leftover; tfsec report leftover is not dest", "treat tfsec leftover JSON as dest then CLI parquet.", "tfsec leftover; # report json claimed dest", "tfsec leftover|.tfsec/report"),
    s_from(13, "tflint-config-leftover-as-dest", "tflc", "tflint config leftover", ".tflint.hcl", "tflint config leftover HCL", "tflint leftover && cat .tflint.hcl", "not tflint leftover; tflint config leftover is not dest", "treat tflint leftover HCL as dest then CLI parquet.", "tflint leftover; # hcl claimed dest", "tflint leftover|.tflint.hcl"),
    s_from(14, "terrascan-policy-leftover-as-dest", "tspp", "terrascan policy leftover", ".terrascan/policy.json", "Terrascan policy leftover JSON", "terrascan leftover && cat .terrascan/policy.json", "not terrascan leftover; Terrascan policy leftover is not dest", "treat Terrascan leftover JSON as dest then CLI parquet.", "terrascan leftover; # policy json claimed dest", "terrascan leftover|.terrascan/policy"),
    s_from(15, "teamcity-build-leftover-as-dest", "tcbd", "teamcity build leftover", ".teamcity/build.json", "TeamCity build leftover JSON", "teamcity leftover && cat .teamcity/build.json", "not teamcity leftover; TeamCity build leftover is not dest", "treat TeamCity leftover JSON as dest then CLI parquet.", "teamcity leftover; # build json claimed dest", "teamcity leftover|.teamcity/build"),
    s_from(16, "bamboo-plan-leftover-as-dest", "bmpl", "bamboo plan leftover", ".bamboo/plan.yml", "Bamboo plan leftover YAML", "bamboo leftover && cat .bamboo/plan.yml", "not bamboo leftover; Bamboo plan leftover is not dest", "treat Bamboo leftover YAML as dest then CLI parquet.", "bamboo leftover; # plan yml claimed dest", "bamboo leftover|.bamboo/plan"),
    s_from(17, "gocd-pipeline-leftover-as-dest", "gcpl", "gocd pipeline leftover", ".gocd/pipeline.yml", "GoCD pipeline leftover YAML", "gocd leftover && cat .gocd/pipeline.yml", "not gocd leftover; GoCD pipeline leftover is not dest", "treat GoCD leftover YAML as dest then CLI parquet.", "gocd leftover; # pipeline yml claimed dest", "gocd leftover|.gocd/pipeline"),
    s_from(18, "packer-image-leftover-as-dest", "pkim", "packer image leftover", ".packer/image.json", "Packer image leftover JSON", "packer leftover && cat .packer/image.json", "not packer leftover; Packer image leftover is not dest", "treat Packer leftover JSON as dest then CLI parquet.", "packer leftover; # image json claimed dest", "packer leftover|.packer/image"),
    s_from(19, "vagrant-box-leftover-as-dest", "vgbx", "vagrant box leftover", ".vagrant/box.json", "Vagrant box leftover JSON", "vagrant leftover && cat .vagrant/box.json", "not vagrant leftover; Vagrant box leftover is not dest", "treat Vagrant leftover JSON as dest then CLI parquet.", "vagrant leftover; # box json claimed dest", "vagrant leftover|.vagrant/box"),
    s_from(20, "lima-instance-leftover-as-dest", "lmin", "lima instance leftover", ".lima/instance.yml", "Lima instance leftover YAML", "limactl leftover && cat .lima/instance.yml", "not lima leftover; Lima instance leftover is not dest", "treat Lima leftover YAML as dest then CLI parquet.", "lima leftover; # instance yml claimed dest", "lima leftover|.lima/instance"),
    s_from(21, "colima-vm-leftover-as-dest", "clvm", "colima vm leftover", ".colima/vm.json", "Colima VM leftover JSON", "colima leftover && cat .colima/vm.json", "not colima leftover; Colima VM leftover is not dest", "treat Colima leftover JSON as dest then CLI parquet.", "colima leftover; # vm json claimed dest", "colima leftover|.colima/vm"),
    s_from(22, "podman-image-leftover-as-dest", "pdmi", "podman image leftover", ".podman/image.json", "Podman image leftover JSON", "podman leftover && cat .podman/image.json", "not docker leftover; Podman image leftover is not dest", "treat Podman leftover JSON as dest then CLI parquet.", "podman leftover; # image json claimed dest", "podman leftover|.podman/image"),
    s_from(23, "buildah-container-leftover-as-dest", "bdct", "buildah container leftover", ".buildah/container.json", "Buildah container leftover JSON", "buildah leftover && cat .buildah/container.json", "not docker leftover; Buildah container leftover is not dest", "treat Buildah leftover JSON as dest then CLI parquet.", "buildah leftover; # container json claimed dest", "buildah leftover|.buildah/container"),
    s_from(24, "kaniko-snapshot-leftover-as-dest", "knss", "kaniko snapshot leftover", ".kaniko/snapshot.json", "Kaniko snapshot leftover JSON", "kaniko leftover && cat .kaniko/snapshot.json", "not docker leftover; Kaniko snapshot leftover is not dest", "treat Kaniko leftover JSON as dest then CLI parquet.", "kaniko leftover; # snapshot json claimed dest", "kaniko leftover|.kaniko/snapshot"),
    s_from(25, "buildkit-cache-leftover-as-dest", "bkch", "buildkit cache leftover", ".buildkit/cache.bin", "BuildKit cache leftover", "buildctl leftover && ls .buildkit/cache.bin", "not docker leftover; BuildKit cache leftover is not dest", "treat BuildKit leftover cache as dest then CLI parquet.", "buildkit leftover; # cache claimed dest", "buildkit leftover|.buildkit/cache"),
    s_from(26, "nix-derivation-leftover-as-dest", "nxdv", "nix derivation leftover", ".nix/drv.drv", "Nix derivation leftover", "nix leftover && cat .nix/drv.drv", "not nix leftover; Nix derivation leftover is not dest", "treat Nix leftover drv as dest then CLI parquet.", "nix leftover; # drv claimed dest", "nix leftover|.nix/drv"),
    s_from(27, "guix-package-leftover-as-dest", "gxpk", "guix package leftover", ".guix/package.scm", "Guix package leftover", "guix leftover && cat .guix/package.scm", "not guix leftover; Guix package leftover is not dest", "treat Guix leftover SCM as dest then CLI parquet.", "guix leftover; # package scm claimed dest", "guix leftover|.guix/package"),
    s_from(28, "spack-spec-leftover-as-dest", "spsc", "spack spec leftover", ".spack/spec.yaml", "Spack spec leftover YAML", "spack leftover && cat .spack/spec.yaml", "not spack leftover; Spack spec leftover is not dest", "treat Spack leftover YAML as dest then CLI parquet.", "spack leftover; # spec yaml claimed dest", "spack leftover|.spack/spec"),
    s_from(29, "conda-env-leftover-as-dest", "cnen", "conda env leftover", ".conda/env.yml", "Conda env leftover YAML", "conda leftover && cat .conda/env.yml", "not conda leftover; Conda env leftover is not dest", "treat Conda leftover YAML as dest then CLI parquet.", "conda leftover; # env yml claimed dest", "conda leftover|.conda/env"),
    s_from(30, "pixi-lock-leftover-as-dest", "pxlk", "pixi lock leftover", "pixi.lock", "Pixi lock leftover", "pixi leftover && cat pixi.lock", "not pixi leftover; Pixi lock leftover is not dest", "treat Pixi leftover lock as dest then CLI parquet.", "pixi leftover; # pixi.lock claimed dest", "pixi leftover|pixi.lock"),
    s_from(31, "uv-lock-leftover-as-dest", "uvlk", "uv lock leftover", "uv.lock", "uv lock leftover", "uv leftover && cat uv.lock", "not uv leftover; uv lock leftover is not dest", "treat uv leftover lock as dest then CLI parquet.", "uv leftover; # uv.lock claimed dest", "uv leftover|uv.lock"),
]

LEFTOVER = [
    l_from(0, "ansible-inventory-leftover-handoff", "aniv", ".ansible/inventory.ini", "ansible inventory leftover", "Ansible inventory leftover", "not ansible playbook leftover; leftover Ansible inventory as dest", "ship leftover Ansible inventory as dest.", "inventory leftover; # ini on disk", "ansible leftover|.ansible/inventory"),
    l_from(1, "puppet-report-leftover-handoff", "pprp", ".puppet/report.yaml", "puppet report leftover", "Puppet report leftover YAML", "not puppet catalog leftover; leftover Puppet report YAML as dest", "ship leftover Puppet report YAML as dest.", "report leftover; # yaml on disk", "puppet leftover|.puppet/report"),
    l_from(2, "chef-node-leftover-handoff", "chno", ".chef/node.json", "chef node leftover", "Chef node leftover JSON", "not chef cookbook leftover; leftover Chef node JSON as dest", "ship leftover Chef node JSON as dest.", "node leftover; # json on disk", "chef leftover|.chef/node"),
    l_from(3, "salt-pillar-leftover-handoff", "slpl", ".salt/pillar.sls", "salt pillar leftover", "Salt pillar leftover", "not salt state leftover; leftover Salt pillar as dest", "ship leftover Salt pillar as dest.", "pillar leftover; # sls on disk", "salt leftover|.salt/pillar"),
    l_from(4, "opentofu-lock-leftover-handoff", "otlk", ".opentofu/lock.hcl", "opentofu lock leftover", "OpenTofu lock leftover HCL", "not opentofu state leftover; leftover OpenTofu lock HCL as dest", "ship leftover OpenTofu lock HCL as dest.", "lock leftover; # hcl on disk", "opentofu leftover|.opentofu/lock"),
    l_from(5, "cdktf-output-leftover-handoff", "cdot", ".cdktf/output.json", "cdktf output leftover", "CDKTF output leftover JSON", "not cdktf synth leftover; leftover CDKTF output JSON as dest", "ship leftover CDKTF output JSON as dest.", "output leftover; # json on disk", "cdktf leftover|.cdktf/output"),
    l_from(6, "atlantis-apply-leftover-handoff", "atap", ".atlantis/apply.json", "atlantis apply leftover", "Atlantis apply leftover JSON", "not atlantis plan leftover; leftover Atlantis apply JSON as dest", "ship leftover Atlantis apply JSON as dest.", "apply leftover; # json on disk", "atlantis leftover|.atlantis/apply"),
    l_from(7, "spacelift-run-leftover-handoff", "slrn", ".spacelift/run.json", "spacelift run leftover", "Spacelift run leftover JSON", "not spacelift stack leftover; leftover Spacelift run JSON as dest", "ship leftover Spacelift run JSON as dest.", "run leftover; # json on disk", "spacelift leftover|.spacelift/run"),
    l_from(8, "env0-log-leftover-handoff", "e0lg", ".env0/log.txt", "env0 log leftover", "env0 log leftover", "not env0 deployment leftover; leftover env0 log as dest", "ship leftover env0 log as dest.", "log leftover; # txt on disk", "env0 leftover|.env0/log"),
    l_from(9, "scalr-workspace-leftover-handoff", "scws", ".scalr/workspace.json", "scalr workspace leftover", "Scalr workspace leftover JSON", "not scalr run leftover; leftover Scalr workspace JSON as dest", "ship leftover Scalr workspace JSON as dest.", "workspace leftover; # json on disk", "scalr leftover|.scalr/workspace"),
    l_from(10, "infracost-diff-leftover-handoff", "icdf", ".infracost/diff.json", "infracost diff leftover", "Infracost diff leftover JSON", "not infracost breakdown leftover; leftover Infracost diff JSON as dest", "ship leftover Infracost diff JSON as dest.", "diff leftover; # json on disk", "infracost leftover|.infracost/diff"),
    l_from(11, "checkov-sarif-leftover-handoff", "cksf", ".checkov/sarif.json", "checkov sarif leftover", "Checkov SARIF leftover JSON", "not checkov report leftover; leftover Checkov SARIF JSON as dest", "ship leftover Checkov SARIF JSON as dest.", "sarif leftover; # json on disk", "checkov leftover|.checkov/sarif"),
    l_from(12, "tfsec-sarif-leftover-handoff", "tssf", ".tfsec/sarif.json", "tfsec sarif leftover", "tfsec SARIF leftover JSON", "not tfsec report leftover; leftover tfsec SARIF JSON as dest", "ship leftover tfsec SARIF JSON as dest.", "sarif leftover; # json on disk", "tfsec leftover|.tfsec/sarif"),
    l_from(13, "tflint-issue-leftover-handoff", "tfli", ".tflint/issue.json", "tflint issue leftover", "tflint issue leftover JSON", "not tflint config leftover; leftover tflint issue JSON as dest", "ship leftover tflint issue JSON as dest.", "issue leftover; # json on disk", "tflint leftover|.tflint/issue"),
    l_from(14, "terrascan-scan-leftover-handoff", "tssc", ".terrascan/scan.json", "terrascan scan leftover", "Terrascan scan leftover JSON", "not terrascan policy leftover; leftover Terrascan scan JSON as dest", "ship leftover Terrascan scan JSON as dest.", "scan leftover; # json on disk", "terrascan leftover|.terrascan/scan"),
    l_from(15, "teamcity-artifact-leftover-handoff", "tcat", ".teamcity/artifact.zip", "teamcity artifact leftover", "TeamCity artifact leftover", "not teamcity build leftover; leftover TeamCity artifact as dest", "ship leftover TeamCity artifact as dest.", "artifact leftover; # zip on disk", "teamcity leftover|.teamcity/artifact"),
    l_from(16, "bamboo-artifact-leftover-handoff", "bmat", ".bamboo/artifact.zip", "bamboo artifact leftover", "Bamboo artifact leftover", "not bamboo plan leftover; leftover Bamboo artifact as dest", "ship leftover Bamboo artifact as dest.", "artifact leftover; # zip on disk", "bamboo leftover|.bamboo/artifact"),
    l_from(17, "gocd-artifact-leftover-handoff", "gcat", ".gocd/artifact.zip", "gocd artifact leftover", "GoCD artifact leftover", "not gocd pipeline leftover; leftover GoCD artifact as dest", "ship leftover GoCD artifact as dest.", "artifact leftover; # zip on disk", "gocd leftover|.gocd/artifact"),
    l_from(18, "packer-manifest-leftover-handoff", "pkmf", ".packer/manifest.json", "packer manifest leftover", "Packer manifest leftover JSON", "not packer image leftover; leftover Packer manifest JSON as dest", "ship leftover Packer manifest JSON as dest.", "manifest leftover; # json on disk", "packer leftover|.packer/manifest"),
    l_from(19, "vagrant-ssh-leftover-handoff", "vgsh", ".vagrant/ssh.cfg", "vagrant ssh leftover", "Vagrant SSH leftover", "not vagrant box leftover; leftover Vagrant SSH as dest", "ship leftover Vagrant SSH as dest.", "ssh leftover; # cfg on disk", "vagrant leftover|.vagrant/ssh"),
    l_from(20, "lima-disk-leftover-handoff", "lmdk", ".lima/disk.qcow2", "lima disk leftover", "Lima disk leftover", "not lima instance leftover; leftover Lima disk as dest", "ship leftover Lima disk as dest.", "disk leftover; # qcow2 on disk", "lima leftover|.lima/disk"),
    l_from(21, "colima-socket-leftover-handoff", "clsk", ".colima/docker.sock", "colima socket leftover", "Colima socket leftover", "not colima vm leftover; leftover Colima socket as dest", "ship leftover Colima socket as dest.", "socket leftover; # sock on disk", "colima leftover|.colima/docker.sock"),
    l_from(22, "podman-volume-leftover-handoff", "pdmv", ".podman/volume.json", "podman volume leftover", "Podman volume leftover JSON", "not podman image leftover; leftover Podman volume JSON as dest", "ship leftover Podman volume JSON as dest.", "volume leftover; # json on disk", "podman leftover|.podman/volume"),
    l_from(23, "buildah-layer-leftover-handoff", "bdly", ".buildah/layer.tar", "buildah layer leftover", "Buildah layer leftover", "not buildah container leftover; leftover Buildah layer as dest", "ship leftover Buildah layer as dest.", "layer leftover; # tar on disk", "buildah leftover|.buildah/layer"),
    l_from(24, "kaniko-layer-leftover-handoff", "knly", ".kaniko/layer.tar", "kaniko layer leftover", "Kaniko layer leftover", "not kaniko snapshot leftover; leftover Kaniko layer as dest", "ship leftover Kaniko layer as dest.", "layer leftover; # tar on disk", "kaniko leftover|.kaniko/layer"),
    l_from(25, "buildkit-frontend-leftover-handoff", "bkfe", ".buildkit/frontend.json", "buildkit frontend leftover", "BuildKit frontend leftover JSON", "not buildkit cache leftover; leftover BuildKit frontend JSON as dest", "ship leftover BuildKit frontend JSON as dest.", "frontend leftover; # json on disk", "buildkit leftover|.buildkit/frontend"),
    l_from(26, "nix-gcroot-leftover-handoff", "nxgc", ".nix/gcroot", "nix gcroot leftover", "Nix gcroot leftover", "not nix derivation leftover; leftover Nix gcroot as dest", "ship leftover Nix gcroot as dest.", "gcroot leftover; # gcroot on disk", "nix leftover|.nix/gcroot"),
    l_from(27, "guix-profile-leftover-handoff", "gxpf", ".guix/profile", "guix profile leftover", "Guix profile leftover", "not guix package leftover; leftover Guix profile as dest", "ship leftover Guix profile as dest.", "profile leftover; # profile on disk", "guix leftover|.guix/profile"),
    l_from(28, "spack-env-leftover-handoff", "spen", ".spack/env.yaml", "spack env leftover", "Spack env leftover YAML", "not spack spec leftover; leftover Spack env YAML as dest", "ship leftover Spack env YAML as dest.", "env leftover; # yaml on disk", "spack leftover|.spack/env"),
    l_from(29, "conda-pkg-leftover-handoff", "cnpk", ".conda/pkg.tar.bz2", "conda pkg leftover", "Conda pkg leftover", "not conda env leftover; leftover Conda pkg as dest", "ship leftover Conda pkg as dest.", "pkg leftover; # tar.bz2 on disk", "conda leftover|.conda/pkg"),
    l_from(30, "pixi-env-leftover-handoff", "pxen", ".pixi/env", "pixi env leftover", "Pixi env leftover", "not pixi lock leftover; leftover Pixi env as dest", "ship leftover Pixi env as dest.", "env leftover; # dir on disk", "pixi leftover|.pixi/env"),
    l_from(31, "uv-cache-leftover-handoff", "uvch", ".uv/cache", "uv cache leftover", "uv cache leftover", "not uv lock leftover; leftover uv cache as dest", "ship leftover uv cache as dest.", "cache leftover; # dir on disk", "uv leftover|.uv/cache"),
]

mod2.SUCCESS = SUCCESS
mod2.LEFTOVER = LEFTOVER
mod2.BANNED_SLUGS = set(mod2.BANNED_SLUGS) | {
    "dnsmasq-hosts-leftover-as-dest",
    "dnsmasq-lease-leftover-handoff",
}
pair_for = mod2.pair_for
notes_for = mod2.notes_for
write_stage = mod2.write_stage


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("usage: ntp-mill-unique-llll11.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = write_stage(staging, round_n)
    print(f"wrote r{round_n} {i1} {i2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
