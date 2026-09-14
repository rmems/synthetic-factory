"""Observability leftover12 plants r1188+.

BAN r1187 foreman-telemetry / leftover11 slip-mole, leftover10 pier-berth,
r875 tempo, r384 otel-forward, PagerDuty, Opsgenie, Rootly.
"""

from mill_plants_t import _leftover_pair

MORE = []
ROUND_PAIRS = {}


def _emit(round_n, **kwargs):
    dest = []
    _leftover_pair(n=str(round_n), dest=dest, **kwargs)
    MORE.extend(dest)
    ROUND_PAIRS[round_n] = dest[0]


def _l12(n, **kw):
    vendor, noun, prefix = kw["vendor"], kw["noun"], kw["prefix"]
    ok_svc, bad_svc = f"lock-{noun}-svc", f"basin-{noun}-svc"
    tag = noun.replace("-", "")[:8]
    vtag = prefix.replace("-", "")[:5]
    ok_dash, bad_dash = f"{tag}-{vtag}-{n}", f"l{tag[:7]}-{vtag}-fl"
    lie_core = kw["lie_core"]
    _emit(
        n,
        kind="grafana",
        ok_slug=kw["ok_slug"],
        bad_slug=kw["bad_slug"],
        ok_svc=ok_svc,
        bad_svc=bad_svc,
        ok_dash=ok_dash,
        bad_dash=bad_dash,
        panel=kw["panel"],
        metric="",
        needle=kw["needle"],
        lie=(
            f"{vendor} leftover leftover leftover leftover leftover leftover leftover leftover leftover leftover leftover leftover {lie_core} "
            f"so Grafana dashboard {ok_dash} is empty while the source still 202"
        ),
        bad_lie=(
            f"{kw['false_lead']} does not restore leftover leftover leftover leftover leftover leftover leftover leftover leftover leftover leftover leftover {lie_core}"
        ),
        false_lead=kw["false_lead"],
        avoided=kw["avoided"],
        this_is=f"{vendor} leftover leftover leftover leftover leftover leftover leftover leftover leftover leftover leftover leftover {lie_core}",
        ticket=f"OBS-{8900 + (n - 1188)}",
        knob=kw["knob"],
        old=kw["old"],
        new=kw["new"],
        wrong_knob=kw["wrong_knob"],
        wrong_old=kw["wrong_old"],
        wrong_new=kw["wrong_new"],
        wrong2_old=kw["wrong2_old"],
        wrong2_new=kw["wrong2_new"],
        reload="grafana",
        config_path=f"{prefix}/{tag}-false.yaml",
        lie_path=f"{prefix}/{tag}-lie.yaml",
        bad_config=f"{prefix}/l{tag[:7]}-false.yaml",
        bad_lie_path=f"{prefix}/l{tag[:7]}-lie.yaml",
    )


BAN = (
    "r1187 foreman-telemetry-off-leftover; leftover11 slip/mole r1140-r1187; "
    "r875 tempo-ingester-max-traces-per-user-one; r384 otel-forward-connector; "
    "PagerDuty orch; Opsgenie alias; r515 Rootly urgency"
)

SPECS = [
    dict(vendor="Katello", ok_slug="katello-pulp-metrics-off-leftover", bad_slug="katel-pulp-raise-org-not-enable", noun="reagent", panel="Katello pulp", needle="katel_up", lie_core="pulp leftover prometheus.enabled=false so Grafana is empty while syncs still run", false_lead="Katello org leftover", avoided=BAN+"; leftover11 Foreman telemetry", knob=".pulp.prometheus.enabled", old="enabled: false", new="enabled: true", wrong_knob=".organization", wrong_old="organization: sandbox", wrong_new="organization: hangar", wrong2_old="servername: sandbox", wrong2_new="servername: hangar", prefix="katel"),
    dict(vendor="Satellite", ok_slug="satellite-dynflow-metrics-off-leftover", bad_slug="satel-dyn-raise-proxy-not-enable", noun="buffer", panel="Satellite dynflow", needle="satel_up", lie_core="dynflow leftover prometheus=false so Grafana is empty while tasks still succeed", false_lead="Satellite proxy leftover", avoided=BAN+"; leftover12 Katello pulp", knob=".dynflow.prometheus", old="prometheus: false", new="prometheus: true", wrong_knob=".capsule.url", wrong_old="url: https://sandbox", wrong_new="url: https://hangar", wrong2_old="organization: sandbox", wrong2_new="organization: hangar", prefix="satel"),
    dict(vendor="Uyuni", ok_slug="uyuni-tomcat-jmx-off-leftover", bad_slug="uyuni-jmx-raise-tasko-not-enable", noun="solvent", panel="Uyuni JMX", needle="uyuni_up", lie_core="tomcat leftover jmxremote=false so Grafana is empty while the web UI still 443", false_lead="Uyuni Taskomatic leftover", avoided=BAN+"; leftover12 Satellite dynflow", knob=".tomcat.jmxremote", old="jmxremote: false", new="jmxremote: true", wrong_knob=".taskomatic.enabled", wrong_old="enabled: false", wrong_new="enabled: true", wrong2_old="db_host: sandbox", wrong2_new="db_host: hangar", prefix="uyuni"),
    dict(vendor="aptly", ok_slug="aptly-api-bind-drop-leftover", bad_slug="aptly-api-raise-gpg-not-addr", noun="titrant", panel="aptly API", needle="aptly_up", lie_core="api leftover listen 127.0.0.1 so Grafana is empty while publishes still write", false_lead="aptly gpg leftover", avoided=BAN+"; leftover11 Pulp API", knob=".api.listen", old="listen: 127.0.0.1:8080", new="listen: 0.0.0.0:8080", wrong_knob=".gpgProvider", wrong_old="gpgProvider: internal", wrong_new="gpgProvider: gpg1", wrong2_old="rootDir: /tmp", wrong2_new="rootDir: /var/lib/aptly", prefix="aptly"),
    dict(vendor="reprepro", ok_slug="reprepro-log-drop-leftover", bad_slug="rpre-log-raise-arch-not-log", noun="analyte", panel="reprepro log", needle="rpre_pkg", lie_core="log leftover LogDir /dev/null so Grafana is empty while incoming still processes", false_lead="reprepro arch leftover", avoided=BAN+"; leftover12 aptly API", knob=".LogDir", old="LogDir: /dev/null", new="LogDir: /var/log/reprepro", wrong_knob=".Architectures", wrong_old="Architectures: source", wrong_new="Architectures: amd64 source", wrong2_old="Codename: sandbox", wrong2_new="Codename: hangar", prefix="rpre"),
    dict(vendor="Homebrew", ok_slug="brew-analytics-off-leftover", bad_slug="brew-an-raise-core-not-enable", noun="standard", panel="Homebrew analytics", needle="brew_f", lie_core="analytics leftover HOMEBREW_NO_ANALYTICS=1 so Grafana is empty while installs still work", false_lead="Homebrew core leftover", avoided=BAN, knob=".HOMEBREW_NO_ANALYTICS", old="HOMEBREW_NO_ANALYTICS: 1", new="HOMEBREW_NO_ANALYTICS: 0", wrong_knob=".HOMEBREW_NO_INSTALL_FROM_API", wrong_old="HOMEBREW_NO_INSTALL_FROM_API: 1", wrong_new="HOMEBREW_NO_INSTALL_FROM_API: 0", wrong2_old="HOMEBREW_PREFIX: /tmp", wrong2_new="HOMEBREW_PREFIX: /opt/homebrew", prefix="brew"),
    dict(vendor="asdf", ok_slug="asdf-plugin-log-drop-leftover", bad_slug="asdf-log-raise-dir-not-log", noun="blank", panel="asdf plugin", needle="asdf_ver", lie_core="log leftover ASDF_DEBUG=0 plus log /dev/null so Grafana is empty while shims still work", false_lead="asdf dir leftover", avoided=BAN+"; leftover12 Homebrew analytics", knob=".ASDF_DEBUG", old="ASDF_DEBUG: 0", new="ASDF_DEBUG: 1", wrong_knob=".ASDF_DATA_DIR", wrong_old="ASDF_DATA_DIR: /tmp", wrong_new="ASDF_DATA_DIR: ~/.asdf", wrong2_old="ASDF_DEFAULT_TOOL_VERSIONS_FILENAME: sandbox", wrong2_new="ASDF_DEFAULT_TOOL_VERSIONS_FILENAME: .tool-versions", prefix="asdf"),
    dict(vendor="mise", ok_slug="mise-statusline-off-leftover", bad_slug="mise-st-raise-env-not-enable", noun="matrix", panel="mise status", needle="mise_tool", lie_core="status leftover MISE_DISABLE_TOOLS plus experimental off so Grafana is empty", false_lead="mise env leftover", avoided=BAN+"; leftover12 asdf plugin", knob=".MISE_STATUS_MESSAGE", old="MISE_STATUS_MESSAGE: ", new="MISE_STATUS_MESSAGE: hangar", wrong_knob=".MISE_ENV", wrong_old="MISE_ENV: sandbox", wrong_new="MISE_ENV: hangar", wrong2_old="MISE_DATA_DIR: /tmp", wrong2_new="MISE_DATA_DIR: ~/.local/share/mise", prefix="mise"),
    dict(vendor="direnv", ok_slug="direnv-log-drop-leftover", bad_slug="denv-log-raise-warn-not-log", noun="digest", panel="direnv log", needle="denv_load", lie_core="log leftover DIRENV_LOG_FORMAT empty so Grafana is empty while .envrc still loads", false_lead="direnv warn leftover", avoided=BAN+"; leftover12 mise status", knob=".DIRENV_LOG_FORMAT", old="DIRENV_LOG_FORMAT: ", new="DIRENV_LOG_FORMAT: direnv: $msg", wrong_knob=".DIRENV_WARN_TIMEOUT", wrong_old="DIRENV_WARN_TIMEOUT: 0s", wrong_new="DIRENV_WARN_TIMEOUT: 5s", wrong2_old="DIRENV_CONFIG: /tmp", wrong2_new="DIRENV_CONFIG: ~/.config/direnv", prefix="denv"),
    dict(vendor="husky", ok_slug="husky-hook-log-drop-leftover", bad_slug="husky-log-raise-skip-not-log", noun="ash", panel="husky hook", needle="husky_hk", lie_core="HUSKY leftover 0 plus log /dev/null so Grafana is empty while git still commits", false_lead="husky skip leftover", avoided=BAN+"; leftover11 pre-commit log", knob=".HUSKY", old="HUSKY: 0", new="HUSKY: 1", wrong_knob=".HUSKY_SKIP_HOOKS", wrong_old="HUSKY_SKIP_HOOKS: 1", wrong_new="HUSKY_SKIP_HOOKS: 0", wrong2_old="HUSKY_GIT_PARAMS: sandbox", wrong2_new="HUSKY_GIT_PARAMS: ", prefix="husky"),
    dict(vendor="commitlint", ok_slug="commitlint-formatter-drop-leftover", bad_slug="clint-fmt-raise-help-not-format", noun="residue", panel="commitlint", needle="clint_msg", lie_core="formatter leftover default so Grafana is empty while lint still prints", false_lead="commitlint help leftover", avoided=BAN+"; leftover11 ESLint leftover clones", knob=".formatter", old="formatter: default", new="formatter: @commitlint/format", wrong_knob=".helpUrl", wrong_old="helpUrl: https://sandbox", wrong_new="helpUrl: https://github.com/conventional-changelog/commitlint", wrong2_old="extends: []", wrong2_new="extends: [@commitlint/config-conventional]", prefix="clint"),
    dict(vendor="changesets", ok_slug="changesets-changelog-off-leftover", bad_slug="cset-chg-raise-base-not-enable", noun="filtrate", panel="changesets", needle="cset_pr", lie_core="changelog leftover changelog=false so Grafana is empty while versions still bump", false_lead="changesets base leftover", avoided=BAN+"; leftover11 semantic-release", knob=".changelog", old="changelog: false", new="changelog: @changesets/cli/changelog", wrong_knob=".baseBranch", wrong_old="baseBranch: sandbox", wrong_new="baseBranch: main", wrong2_old="access: restricted", wrong2_new="access: public", prefix="cset"),
    dict(vendor="release-please", ok_slug="relplease-manifest-remap-leftover", bad_slug="rpls-man-raise-bump-not-remap", noun="supernate", panel="release-please", needle="rpls_rel", lie_core="manifest leftover .release-please-manifest.json sandbox so Grafana is the wrong dashboard", false_lead="release-please bump leftover", avoided=BAN+"; leftover12 changesets changelog", knob=".release-type", old="release-type: sandbox", new="release-type: node", wrong_knob=".bump-minor-pre-major", wrong_old="bump-minor-pre-major: false", wrong_new="bump-minor-pre-major: true", wrong2_old="package-name: sandbox", wrong2_new="package-name: hangar", prefix="rpls"),
    dict(vendor="Kind", ok_slug="kind-metrics-bind-drop-leftover", bad_slug="kind-bind-raise-cni-not-addr", noun="flask2", panel="Kind kubelet", needle="kind_up", lie_core="kubelet leftover extraArgs.address 127.0.0.1 so Grafana is empty while the node still Ready", false_lead="Kind CNI leftover", avoided=BAN+"; leftover11 k3s metrics", knob=".kubelet.extraArgs.address", old="address: 127.0.0.1", new="address: 0.0.0.0", wrong_knob=".networking.disableDefaultCNI", wrong_old="disableDefaultCNI: true", wrong_new="disableDefaultCNI: false", wrong2_old="name: sandbox", wrong2_new="name: hangar", prefix="kind"),
    dict(vendor="minikube", ok_slug="minikube-metrics-off-leftover", bad_slug="mkube-met-raise-drv-not-enable", noun="beaker2", panel="minikube metrics", needle="mkube_up", lie_core="addons leftover metrics-server=false so Grafana is empty while the cluster still 8443", false_lead="minikube driver leftover", avoided=BAN+"; leftover12 Kind kubelet", knob=".addons.metrics-server", old="metrics-server: false", new="metrics-server: true", wrong_knob=".driver", wrong_old="driver: none", wrong_new="driver: docker", wrong2_old="profile: sandbox", wrong2_new="profile: hangar", prefix="mkube"),
    dict(vendor="k3d", ok_slug="k3d-k3s-arg-metrics-drop-leftover", bad_slug="k3d-arg-raise-lb-not-metrics", noun="burette2", panel="k3d metrics", needle="k3d_up", lie_core="k3s leftover --k3s-arg --kube-controller-manager-arg=bind-address=127.0.0.1 so Grafana is empty", false_lead="k3d lb leftover", avoided=BAN+"; leftover11 k3s metrics; leftover12 Kind", knob=".k3s-arg.bind-address", old="bind-address: 127.0.0.1", new="bind-address: 0.0.0.0", wrong_knob=".k3d.lb.port", wrong_old="port: 0", wrong_new="port: 80", wrong2_old="name: sandbox", wrong2_new="name: hangar", prefix="k3d"),
    dict(vendor="k0s", ok_slug="k0s-konnectivity-metrics-off-leftover", bad_slug="k0s-kon-raise-worker-not-enable", noun="pipette2", panel="k0s konnectivity", needle="k0s_up", lie_core="konnectivity leftover enabled=false so Grafana is empty while the API still 6443", false_lead="k0s worker leftover", avoided=BAN+"; leftover12 k3d metrics", knob=".konnectivity.enabled", old="enabled: false", new="enabled: true", wrong_knob=".workerProfiles[0].name", wrong_old="name: sandbox", wrong_new="name: default", wrong2_old="api.address: 127.0.0.1", wrong2_new="api.address: 0.0.0.0", prefix="k0s"),
    dict(vendor="microk8s", ok_slug="microk8s-observability-off-leftover", bad_slug="mk8s-obs-raise-dns-not-enable", noun="retort2", panel="microk8s obs", needle="mk8s_up", lie_core="addon leftover observability=false so Grafana is empty while the cluster still 16443", false_lead="microk8s dns leftover", avoided=BAN+"; leftover12 minikube metrics", knob=".addons.observability", old="observability: false", new="observability: true", wrong_knob=".addons.dns", wrong_old="dns: false", wrong_new="dns: true", wrong2_old="snap.channel: 1.24/stable", wrong2_new="snap.channel: 1.30/stable", prefix="mk8s"),
    dict(vendor="Headlamp", ok_slug="headlamp-metrics-off-leftover", bad_slug="hlamp-met-raise-oidc-not-enable", noun="crucible2", panel="Headlamp metrics", needle="hlamp_up", lie_core="metrics leftover -metrics-addr empty so Grafana is empty while the UI still 4466", false_lead="Headlamp oidc leftover", avoided=BAN+"; leftover11 Kubernetes Dashboard leftover clones", knob=".metrics-addr", old="metrics-addr: ", new="metrics-addr: :9090", wrong_knob=".oidc-client-id", wrong_old="oidc-client-id: sandbox", wrong_new="oidc-client-id: hangar", wrong2_old="in-cluster: false", wrong2_new="in-cluster: true", prefix="hlamp"),
    dict(vendor="k9s", ok_slug="k9s-log-drop-leftover", bad_slug="k9s-log-raise-skin-not-log", noun="mortar2", panel="k9s log", needle="k9s_cmd", lie_core="log leftover k9s.log /dev/null so Grafana is empty while the TUI still runs", false_lead="k9s skin leftover", avoided=BAN, knob=".k9s.logger.file", old="file: /dev/null", new="file: /var/log/k9s.log", wrong_knob=".k9s.ui.skin", wrong_old="skin: sandbox", wrong_new="skin: hangar", wrong2_old="k9s.refreshRate: 0", wrong2_new="k9s.refreshRate: 2", prefix="k9s"),
    dict(vendor="Garden", ok_slug="garden-analytics-off-leftover", bad_slug="gard-an-raise-env-not-enable", noun="pestle2", panel="Garden analytics", needle="gard_act", lie_core="analytics leftover garden.analytics.enabled=false so Grafana is empty while deploys still run", false_lead="Garden env leftover", avoided=BAN+"; leftover11 Tilt analytics", knob=".analytics.enabled", old="enabled: false", new="enabled: true", wrong_knob=".environments[0].name", wrong_old="name: sandbox", wrong_new="name: hangar", wrong2_old="project.name: sandbox", wrong2_new="project.name: hangar", prefix="gard"),
    dict(vendor="Gefyra", ok_slug="gefyra-telemetry-off-leftover", bad_slug="gefy-tel-raise-ns-not-enable", noun="funnel2", panel="Gefyra telemetry", needle="gefy_br", lie_core="telemetry leftover GEFYRA_TELEMETRY=off so Grafana is empty while bridges still work", false_lead="Gefyra ns leftover", avoided=BAN+"; leftover11 Telepresence metrics", knob=".GEFYRA_TELEMETRY", old="GEFYRA_TELEMETRY: off", new="GEFYRA_TELEMETRY: on", wrong_knob=".namespace", wrong_old="namespace: sandbox", wrong_new="namespace: gefyra", wrong2_old="endpoint: 127.0.0.1", wrong2_new="endpoint: 0.0.0.0", prefix="gefy"),
    dict(vendor="Waypoint", ok_slug="waypoint-ui-bind-drop-leftover", bad_slug="wayp-ui-raise-runner-not-addr", noun="condens2", panel="Waypoint UI", needle="wayp_up", lie_core="ui leftover -listen 127.0.0.1 so Grafana is empty while deployments still succeed", false_lead="Waypoint runner leftover", avoided=BAN+"; leftover11 Nomad telemetry", knob=".ui.listen", old="listen: 127.0.0.1:9702", new="listen: 0.0.0.0:9702", wrong_knob=".runner.enabled", wrong_old="enabled: false", wrong_new="enabled: true", wrong2_old="server.address: sandbox", wrong2_new="server.address: hangar", prefix="wayp"),
    dict(vendor="Vagrant", ok_slug="vagrant-machine-index-drop-leftover", bad_slug="vag-idx-raise-prov-not-index", noun="adapter2", panel="Vagrant index", needle="vag_box", lie_core="index leftover VAGRANT_HOME /tmp/empty so Grafana is empty while boxes still up", false_lead="Vagrant provider leftover", avoided=BAN, knob=".VAGRANT_HOME", old="VAGRANT_HOME: /tmp/empty", new="VAGRANT_HOME: ~/.vagrant.d", wrong_knob=".VAGRANT_DEFAULT_PROVIDER", wrong_old="VAGRANT_DEFAULT_PROVIDER: sandbox", wrong_new="VAGRANT_DEFAULT_PROVIDER: virtualbox", wrong2_old="VAGRANT_CWD: /tmp", wrong2_new="VAGRANT_CWD: .", prefix="vag"),
]


assert len(SPECS) == 24, len(SPECS)
for i, spec in enumerate(SPECS):
    _l12(1188 + i, **spec)
