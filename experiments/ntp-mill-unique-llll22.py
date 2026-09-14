#!/usr/bin/env python3
"""NTP unique leftover leftover leftover leftover mill wave 22: NEW dest plants. BAN dnsmasq leftover clones."""
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
    s_from(0, "awscli-cache-leftover-as-dest", "awch", "awscli cache leftover", ".aws/cli/cache", "awscli cache leftover", "awscli leftover && ls .aws/cli/cache", "not awscli-cache leftover; awscli cache leftover is not dest", "treat leftover awscli cache as dest then CLI parquet.", "awscli leftover; # .aws/cli/cache claimed dest", "awscli leftover|.aws/cli/cache"),
    s_from(1, "gcloud-config-leftover-as-dest", "gccf", "gcloud config leftover", ".config/gcloud", "gcloud config leftover", "gcloud leftover && ls .config/gcloud", "not gcloud-config leftover; gcloud config leftover is not dest", "treat leftover gcloud config as dest then CLI parquet.", "gcloud leftover; # .config/gcloud claimed dest", "gcloud leftover|.config/gcloud"),
    s_from(2, "azcli-cache-leftover-as-dest", "azch", "azcli cache leftover", ".azure", "azcli cache leftover", "azcli leftover && ls .azure", "not azcli-cache leftover; azcli cache leftover is not dest", "treat leftover azcli cache as dest then CLI parquet.", "azcli leftover; # .azure claimed dest", "azcli leftover|.azure"),
    s_from(3, "doctl-config-leftover-as-dest", "dccf", "doctl config leftover", ".config/doctl", "doctl config leftover", "doctl leftover && ls .config/doctl", "not doctl-config leftover; doctl config leftover is not dest", "treat leftover doctl config as dest then CLI parquet.", "doctl leftover; # .config/doctl claimed dest", "doctl leftover|.config/doctl"),
    s_from(4, "linodecli-config-leftover-as-dest", "lncf", "linodecli config leftover", ".config/linode-cli", "linodecli config leftover", "linodecli leftover && ls .config/linode-cli", "not linodecli-config leftover; linodecli config leftover is not dest", "treat leftover linodecli config as dest then CLI parquet.", "linodecli leftover; # .config/linode-cli claimed dest", "linodecli leftover|.config/linode-cli"),
    s_from(5, "vultrcli-config-leftover-as-dest", "vlcf", "vultrcli config leftover", ".vultr-cli.yaml", "vultrcli config leftover", "vultrcli leftover && ls .vultr-cli.yaml", "not vultrcli-config leftover; vultrcli config leftover is not dest", "treat leftover vultrcli config as dest then CLI parquet.", "vultrcli leftover; # .vultr-cli.yaml claimed dest", "vultrcli leftover|.vultr-cli.yaml"),
    s_from(6, "heroku-netrc-leftover-as-dest", "hrnc", "heroku netrc leftover", ".netrc.heroku", "heroku netrc leftover", "heroku leftover && ls .netrc.heroku", "not heroku-netrc leftover; heroku netrc leftover is not dest", "treat leftover heroku netrc as dest then CLI parquet.", "heroku leftover; # .netrc.heroku claimed dest", "heroku leftover|.netrc.heroku"),
    s_from(7, "flyctl-config-leftover-as-dest", "flcf", "flyctl config leftover", ".fly/config.yml", "flyctl config leftover", "flyctl leftover && ls .fly/config.yml", "not flyctl-config leftover; flyctl config leftover is not dest", "treat leftover flyctl config as dest then CLI parquet.", "flyctl leftover; # .fly/config.yml claimed dest", "flyctl leftover|.fly/config.yml"),
    s_from(8, "railway-config-leftover-as-dest", "rwcf", "railway config leftover", ".railway/config.json", "railway config leftover", "railway leftover && ls .railway/config.json", "not railway-config leftover; railway config leftover is not dest", "treat leftover railway config as dest then CLI parquet.", "railway leftover; # .railway/config.json claimed dest", "railway leftover|.railway/config.json"),
    s_from(9, "render-config-leftover-as-dest", "rdcf2", "render config leftover", ".render/config.json", "render config leftover", "render leftover && ls .render/config.json", "not render-config leftover; render config leftover is not dest", "treat leftover render config as dest then CLI parquet.", "render leftover; # .render/config.json claimed dest", "render leftover|.render/config.json"),
    s_from(10, "vercel-config-leftover-as-dest", "vrcf", "vercel config leftover", ".vercel", "vercel config leftover", "vercel leftover && ls .vercel", "not vercel-config leftover; vercel config leftover is not dest", "treat leftover vercel config as dest then CLI parquet.", "vercel leftover; # .vercel claimed dest", "vercel leftover|.vercel"),
    s_from(11, "netlify-config-leftover-as-dest", "nlcf", "netlify config leftover", ".netlify", "netlify config leftover", "netlify leftover && ls .netlify", "not netlify-config leftover; netlify config leftover is not dest", "treat leftover netlify config as dest then CLI parquet.", "netlify leftover; # .netlify claimed dest", "netlify leftover|.netlify"),
    s_from(12, "cloudflare-wrangler-leftover-as-dest", "cfwr", "cloudflare wrangler leftover", ".wrangler", "wrangler config leftover", "cloudflare leftover && ls .wrangler", "not cloudflare-wrangler leftover; wrangler config leftover is not dest", "treat leftover wrangler config as dest then CLI parquet.", "cloudflare leftover; # .wrangler claimed dest", "cloudflare leftover|.wrangler"),
    s_from(13, "supabase-config-leftover-as-dest", "sbcf", "supabase config leftover", ".supabase", "supabase config leftover", "supabase leftover && ls .supabase", "not supabase-config leftover; supabase config leftover is not dest", "treat leftover supabase config as dest then CLI parquet.", "supabase leftover; # .supabase claimed dest", "supabase leftover|.supabase"),
    s_from(14, "firebase-cache-leftover-as-dest", "fbch", "firebase cache leftover", ".firebase", "firebase cache leftover", "firebase leftover && ls .firebase", "not firebase-cache leftover; firebase cache leftover is not dest", "treat leftover firebase cache as dest then CLI parquet.", "firebase leftover; # .firebase claimed dest", "firebase leftover|.firebase"),
    s_from(15, "amplify-config-leftover-as-dest", "apcf", "amplify config leftover", ".amplifyrc", "amplify config leftover", "amplify leftover && ls .amplifyrc", "not amplify-config leftover; amplify config leftover is not dest", "treat leftover amplify config as dest then CLI parquet.", "amplify leftover; # .amplifyrc claimed dest", "amplify leftover|.amplifyrc"),
    s_from(16, "cdk-out-leftover-as-dest", "cdko", "cdk out leftover", "cdk.out", "cdk out leftover", "cdk leftover && ls cdk.out", "not cdk-out leftover; cdk out leftover is not dest", "treat leftover cdk out as dest then CLI parquet.", "cdk leftover; # cdk.out claimed dest", "cdk leftover|cdk.out"),
    s_from(17, "pulumi-stack-leftover-as-dest", "plst", "pulumi stack leftover", ".pulumi/stacks", "pulumi stack leftover", "pulumi leftover && ls .pulumi/stacks", "not pulumi-stack leftover; pulumi stack leftover is not dest", "treat leftover pulumi stack as dest then CLI parquet.", "pulumi leftover; # .pulumi/stacks claimed dest", "pulumi leftover|.pulumi/stacks"),
    s_from(18, "terraform-tfstate-leftover-as-dest", "tfts", "terraform tfstate leftover", "terraform.tfstate", "terraform tfstate leftover", "terraform leftover && ls terraform.tfstate", "not terraform-tfstate leftover; terraform tfstate leftover is not dest", "treat leftover terraform tfstate as dest then CLI parquet.", "terraform leftover; # terraform.tfstate claimed dest", "terraform leftover|terraform.tfstate"),
    s_from(19, "terragrunt-cache-leftover-as-dest", "tgch", "terragrunt cache leftover", ".terragrunt-cache", "terragrunt cache leftover", "terragrunt leftover && ls .terragrunt-cache", "not terragrunt-cache leftover; terragrunt cache leftover is not dest", "treat leftover terragrunt cache as dest then CLI parquet.", "terragrunt leftover; # .terragrunt-cache claimed dest", "terragrunt leftover|.terragrunt-cache"),
    s_from(20, "packer-cache-leftover-as-dest", "pkch", "packer cache leftover", "packer_cache", "packer cache leftover", "packer leftover && ls packer_cache", "not packer-cache leftover; packer cache leftover is not dest", "treat leftover packer cache as dest then CLI parquet.", "packer leftover; # packer_cache claimed dest", "packer leftover|packer_cache"),
    s_from(21, "vagrant-dot-leftover-as-dest", "vgdt", "vagrant dot leftover", ".vagrant", "vagrant dot leftover", "vagrant leftover && ls .vagrant", "not vagrant-dot leftover; vagrant dot leftover is not dest", "treat leftover vagrant dot as dest then CLI parquet.", "vagrant leftover; # .vagrant claimed dest", "vagrant leftover|.vagrant"),
    s_from(22, "ansible-retry-leftover-as-dest", "anrt", "ansible retry leftover", "playbook.retry", "ansible retry leftover", "ansible leftover && ls playbook.retry", "not ansible-retry leftover; ansible retry leftover is not dest", "treat leftover ansible retry as dest then CLI parquet.", "ansible leftover; # playbook.retry claimed dest", "ansible leftover|playbook.retry"),
    s_from(23, "molecule-cache-leftover-as-dest", "mlch", "molecule cache leftover", ".molecule", "molecule cache leftover", "molecule leftover && ls .molecule", "not molecule-cache leftover; molecule cache leftover is not dest", "treat leftover molecule cache as dest then CLI parquet.", "molecule leftover; # .molecule claimed dest", "molecule leftover|.molecule"),
    s_from(24, "inspec-json-leftover-as-dest", "injs", "inspec json leftover", "inspec.json", "inspec json leftover", "inspec leftover && ls inspec.json", "not inspec-json leftover; inspec json leftover is not dest", "treat leftover inspec json as dest then CLI parquet.", "inspec leftover; # inspec.json claimed dest", "inspec leftover|inspec.json"),
    s_from(25, "kitchen-log-leftover-as-dest", "ktlg", "kitchen log leftover", ".kitchen/logs", "kitchen log leftover", "kitchen leftover && ls .kitchen/logs", "not kitchen-log leftover; kitchen log leftover is not dest", "treat leftover kitchen log as dest then CLI parquet.", "kitchen leftover; # .kitchen/logs claimed dest", "kitchen leftover|.kitchen/logs"),
    s_from(26, "consul-data-leftover-as-dest", "csdt", "consul data leftover", "consul/data", "consul data leftover", "consul leftover && ls consul/data", "not consul-data leftover; consul data leftover is not dest", "treat leftover consul data as dest then CLI parquet.", "consul leftover; # consul/data claimed dest", "consul leftover|consul/data"),
    s_from(27, "vault-data-leftover-as-dest", "vtdt", "vault data leftover", "vault/data", "vault data leftover", "vault leftover && ls vault/data", "not vault-data leftover; vault data leftover is not dest", "treat leftover vault data as dest then CLI parquet.", "vault leftover; # vault/data claimed dest", "vault leftover|vault/data"),
    s_from(28, "nomad-data-leftover-as-dest", "nmdt", "nomad data leftover", "nomad/data", "nomad data leftover", "nomad leftover && ls nomad/data", "not nomad-data leftover; nomad data leftover is not dest", "treat leftover nomad data as dest then CLI parquet.", "nomad leftover; # nomad/data claimed dest", "nomad leftover|nomad/data"),
    s_from(29, "boundary-data-leftover-as-dest", "bddt", "boundary data leftover", "boundary/data", "boundary data leftover", "boundary leftover && ls boundary/data", "not boundary-data leftover; boundary data leftover is not dest", "treat leftover boundary data as dest then CLI parquet.", "boundary leftover; # boundary/data claimed dest", "boundary leftover|boundary/data"),
    s_from(30, "waypoint-data-leftover-as-dest", "wpdt", "waypoint data leftover", "waypoint/data", "waypoint data leftover", "waypoint leftover && ls waypoint/data", "not waypoint-data leftover; waypoint data leftover is not dest", "treat leftover waypoint data as dest then CLI parquet.", "waypoint leftover; # waypoint/data claimed dest", "waypoint leftover|waypoint/data"),
    s_from(31, "sentinel-policy-leftover-as-dest", "stpl", "sentinel policy leftover", "sentinel.hcl.bak", "sentinel policy leftover", "sentinel leftover && ls sentinel.hcl.bak", "not sentinel-policy leftover; sentinel policy leftover is not dest", "treat leftover sentinel policy as dest then CLI parquet.", "sentinel leftover; # sentinel.hcl.bak claimed dest", "sentinel leftover|sentinel.hcl.bak"),
]

LEFTOVER = [
    l_from(0, "awscli-logs-leftover-handoff", "awlg", ".aws/cli/logs", "awscli logs leftover", "awscli logs leftover", "not awscli cache leftover; leftover awscli logs as dest", "ship leftover awscli logs as dest.", "awscli logs leftover; # .aws/cli/logs on disk", "awscli leftover|.aws/cli/logs"),
    l_from(1, "gcloud-logs-leftover-handoff", "gclg", ".config/gcloud/logs", "gcloud logs leftover", "gcloud logs leftover", "not gcloud config leftover; leftover gcloud logs as dest", "ship leftover gcloud logs as dest.", "gcloud logs leftover; # .config/gcloud/logs on disk", "gcloud leftover|.config/gcloud/logs"),
    l_from(2, "azcli-logs-leftover-handoff", "azlg", ".azure/commands.log", "azcli logs leftover", "azcli logs leftover", "not azcli cache leftover; leftover azcli logs as dest", "ship leftover azcli logs as dest.", "azcli logs leftover; # .azure/commands.log on disk", "azcli leftover|.azure/commands.log"),
    l_from(3, "doctl-context-leftover-handoff", "dcct", ".config/doctl/context.yaml", "doctl context leftover", "doctl context leftover", "not doctl config leftover; leftover doctl context as dest", "ship leftover doctl context as dest.", "doctl context leftover; # .config/doctl/context.yaml on disk", "doctl leftover|.config/doctl/context.yaml"),
    l_from(4, "linodecli-cache-leftover-handoff", "lnch", ".config/linode-cli/cache", "linodecli cache leftover", "linodecli cache leftover", "not linodecli config leftover; leftover linodecli cache as dest", "ship leftover linodecli cache as dest.", "linodecli cache leftover; # .config/linode-cli/cache on disk", "linodecli leftover|.config/linode-cli/cache"),
    l_from(5, "vultrcli-cache-leftover-handoff", "vlch", ".vultr-cli.cache", "vultrcli cache leftover", "vultrcli cache leftover", "not vultrcli config leftover; leftover vultrcli cache as dest", "ship leftover vultrcli cache as dest.", "vultrcli cache leftover; # .vultr-cli.cache on disk", "vultrcli leftover|.vultr-cli.cache"),
    l_from(6, "heroku-cache-leftover-handoff", "hrch", ".heroku/cache", "heroku cache leftover", "heroku cache leftover", "not heroku netrc leftover; leftover heroku cache as dest", "ship leftover heroku cache as dest.", "heroku cache leftover; # .heroku/cache on disk", "heroku leftover|.heroku/cache"),
    l_from(7, "flyctl-state-leftover-handoff", "flst", ".fly/state.yml", "flyctl state leftover", "flyctl state leftover", "not flyctl config leftover; leftover flyctl state as dest", "ship leftover flyctl state as dest.", "flyctl state leftover; # .fly/state.yml on disk", "flyctl leftover|.fly/state.yml"),
    l_from(8, "railway-env-leftover-handoff", "rwen", ".railway/env.json", "railway env leftover", "railway env leftover", "not railway config leftover; leftover railway env as dest", "ship leftover railway env as dest.", "railway env leftover; # .railway/env.json on disk", "railway leftover|.railway/env.json"),
    l_from(9, "render-log-leftover-handoff", "rdlg", ".render/log", "render log leftover", "render log leftover", "not render config leftover; leftover render log as dest", "ship leftover render log as dest.", "render log leftover; # .render/log on disk", "render leftover|.render/log"),
    l_from(10, "vercel-log-leftover-handoff", "vrlg", ".vercel/log", "vercel log leftover", "vercel log leftover", "not vercel config leftover; leftover vercel log as dest", "ship leftover vercel log as dest.", "vercel log leftover; # .vercel/log on disk", "vercel leftover|.vercel/log"),
    l_from(11, "netlify-log-leftover-handoff", "nllg", ".netlify/state.json", "netlify state leftover", "netlify state leftover", "not netlify config leftover; leftover netlify state as dest", "ship leftover netlify state as dest.", "netlify state leftover; # .netlify/state.json on disk", "netlify leftover|.netlify/state.json"),
    l_from(12, "cloudflare-state-leftover-handoff", "cfst", ".wrangler/state", "wrangler state leftover", "wrangler state leftover", "not wrangler config leftover; leftover wrangler state as dest", "ship leftover wrangler state as dest.", "wrangler state leftover; # .wrangler/state on disk", "cloudflare leftover|.wrangler/state"),
    l_from(13, "supabase-log-leftover-handoff", "sblg", ".supabase/log", "supabase log leftover", "supabase log leftover", "not supabase config leftover; leftover supabase log as dest", "ship leftover supabase log as dest.", "supabase log leftover; # .supabase/log on disk", "supabase leftover|.supabase/log"),
    l_from(14, "firebase-log-leftover-handoff", "fblg", ".firebase/log", "firebase log leftover", "firebase log leftover", "not firebase cache leftover; leftover firebase log as dest", "ship leftover firebase log as dest.", "firebase log leftover; # .firebase/log on disk", "firebase leftover|.firebase/log"),
    l_from(15, "amplify-log-leftover-handoff", "aplg", "amplify.log", "amplify log leftover", "amplify log leftover", "not amplify config leftover; leftover amplify log as dest", "ship leftover amplify log as dest.", "amplify log leftover; # amplify.log on disk", "amplify leftover|amplify.log"),
    l_from(16, "cdk-context-leftover-handoff", "cdkctx", "cdk.context.json", "cdk context leftover", "cdk context leftover", "not cdk out leftover; leftover cdk context as dest", "ship leftover cdk context as dest.", "cdk context leftover; # cdk.context.json on disk", "cdk leftover|cdk.context.json"),
    l_from(17, "pulumi-lock-leftover-handoff", "pllk", ".pulumi/locks", "pulumi lock leftover", "pulumi lock leftover", "not pulumi stack leftover; leftover pulumi lock as dest", "ship leftover pulumi lock as dest.", "pulumi lock leftover; # .pulumi/locks on disk", "pulumi leftover|.pulumi/locks"),
    l_from(18, "terraform-backup-leftover-handoff", "tfbk", "terraform.tfstate.backup", "terraform backup leftover", "terraform backup leftover", "not terraform tfstate leftover; leftover terraform backup as dest", "ship leftover terraform backup as dest.", "terraform backup leftover; # terraform.tfstate.backup on disk", "terraform leftover|terraform.tfstate.backup"),
    l_from(19, "terragrunt-log-leftover-handoff", "tglg", ".terragrunt-cache/log", "terragrunt log leftover", "terragrunt log leftover", "not terragrunt cache leftover; leftover terragrunt log as dest", "ship leftover terragrunt log as dest.", "terragrunt log leftover; # .terragrunt-cache/log on disk", "terragrunt leftover|.terragrunt-cache/log"),
    l_from(20, "packer-log-leftover-handoff", "pklg", "packer.log", "packer log leftover", "packer log leftover", "not packer cache leftover; leftover packer log as dest", "ship leftover packer log as dest.", "packer log leftover; # packer.log on disk", "packer leftover|packer.log"),
    l_from(21, "vagrant-log-leftover-handoff", "vglg", ".vagrant/log", "vagrant log leftover", "vagrant log leftover", "not vagrant dot leftover; leftover vagrant log as dest", "ship leftover vagrant log as dest.", "vagrant log leftover; # .vagrant/log on disk", "vagrant leftover|.vagrant/log"),
    l_from(22, "ansible-log-leftover-handoff", "anlg", "ansible.log", "ansible log leftover", "ansible log leftover", "not ansible retry leftover; leftover ansible log as dest", "ship leftover ansible log as dest.", "ansible log leftover; # ansible.log on disk", "ansible leftover|ansible.log"),
    l_from(23, "molecule-log-leftover-handoff", "mllg", ".molecule/log", "molecule log leftover", "molecule log leftover", "not molecule cache leftover; leftover molecule log as dest", "ship leftover molecule log as dest.", "molecule log leftover; # .molecule/log on disk", "molecule leftover|.molecule/log"),
    l_from(24, "inspec-log-leftover-handoff", "inlg", "inspec.log", "inspec log leftover", "inspec log leftover", "not inspec json leftover; leftover inspec log as dest", "ship leftover inspec log as dest.", "inspec log leftover; # inspec.log on disk", "inspec leftover|inspec.log"),
    l_from(25, "kitchen-yml-leftover-handoff", "ktyml", ".kitchen.yml.bak", "kitchen yml leftover", "kitchen yml leftover", "not kitchen log leftover; leftover kitchen yml as dest", "ship leftover kitchen yml as dest.", "kitchen yml leftover; # .kitchen.yml.bak on disk", "kitchen leftover|.kitchen.yml.bak"),
    l_from(26, "consul-log-leftover-handoff", "cslg", "consul.log", "consul log leftover", "consul log leftover", "not consul data leftover; leftover consul log as dest", "ship leftover consul log as dest.", "consul log leftover; # consul.log on disk", "consul leftover|consul.log"),
    l_from(27, "vault-log-leftover-handoff", "vtlg", "vault.log", "vault log leftover", "vault log leftover", "not vault data leftover; leftover vault log as dest", "ship leftover vault log as dest.", "vault log leftover; # vault.log on disk", "vault leftover|vault.log"),
    l_from(28, "nomad-log-leftover-handoff", "nmlg", "nomad.log", "nomad log leftover", "nomad log leftover", "not nomad data leftover; leftover nomad log as dest", "ship leftover nomad log as dest.", "nomad log leftover; # nomad.log on disk", "nomad leftover|nomad.log"),
    l_from(29, "boundary-log-leftover-handoff", "bdlg", "boundary.log", "boundary log leftover", "boundary log leftover", "not boundary data leftover; leftover boundary log as dest", "ship leftover boundary log as dest.", "boundary log leftover; # boundary.log on disk", "boundary leftover|boundary.log"),
    l_from(30, "waypoint-log-leftover-handoff", "wplg", "waypoint.log", "waypoint log leftover", "waypoint log leftover", "not waypoint data leftover; leftover waypoint log as dest", "ship leftover waypoint log as dest.", "waypoint log leftover; # waypoint.log on disk", "waypoint leftover|waypoint.log"),
    l_from(31, "sentinel-log-leftover-handoff", "stlg2", "sentinel.log", "sentinel log leftover", "sentinel log leftover", "not sentinel policy leftover; leftover sentinel log as dest", "ship leftover sentinel log as dest.", "sentinel log leftover; # sentinel.log on disk", "sentinel leftover|sentinel.log"),
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
        print("usage: ntp-mill-unique-llll22.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = write_stage(staging, round_n)
    print(f"wrote r{round_n} {i1} {i2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
