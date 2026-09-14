#!/usr/bin/env python3
"""Emit experiments/iac-mill-r1132.py: CATALOG_FIRST=1132 leftover catalog.

Append-only new leftover pairs. Do not insert into r777 K8S (that replays CLI).
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments" / "iac-mill-r1132.py"

# slug without -vs-old, m, product, kind, resource, api, cluster-scoped, field, fail
K8S_SPEC: list[tuple] = [
    ("argocd-app", "argocd", "Argo CD Application", "Application", "application", "argoproj.io", False, ".spec.source.targetRevision", "leftover targetRevision hash mismatch vs HEAD-v2"),
    ("argocd-appset", "appset", "Argo CD ApplicationSet", "ApplicationSet", "applicationset", "argoproj.io", False, ".spec.generators[0].git.revision", "leftover git revision hash mismatch vs main-v2"),
    ("argocd-proj", "appproj", "Argo CD AppProject", "AppProject", "appproject", "argoproj.io", False, ".spec.sourceRepos[0]", "leftover sourceRepos hash mismatch vs org-v2"),
    ("flux-ks", "fluxks", "Flux Kustomization", "Kustomization", "kustomization", "kustomize.toolkit.fluxcd.io", False, ".spec.path", "leftover path hash mismatch vs ./deploy/v2"),
    ("flux-hr", "fluxhr", "Flux HelmRelease", "HelmRelease", "helmrelease", "helm.toolkit.fluxcd.io", False, ".spec.chart.spec.version", "leftover chart version hash mismatch vs 2.4.0"),
    ("flux-ipol", "fluxip", "Flux ImagePolicy", "ImagePolicy", "imagepolicy", "image.toolkit.fluxcd.io", False, ".spec.policy.semver.range", "leftover semver range hash mismatch vs 2.x"),
    ("flux-irepo", "fluxir", "Flux ImageRepository", "ImageRepository", "imagerepository", "image.toolkit.fluxcd.io", False, ".spec.image", "leftover image hash mismatch vs ghcr.io/web-v2"),
    ("flux-git", "fluxgr", "Flux GitRepository", "GitRepository", "gitrepository", "source.toolkit.fluxcd.io", False, ".spec.ref.branch", "leftover branch hash mismatch vs release-v2"),
    ("flux-oci", "fluxoci", "Flux OCIRepository", "OCIRepository", "ocirepository", "source.toolkit.fluxcd.io", False, ".spec.url", "leftover oci url hash mismatch vs oci://ghcr.io/web-v2"),
    ("flux-hrepo", "fluxhrep", "Flux HelmRepository", "HelmRepository", "helmrepository", "source.toolkit.fluxcd.io", False, ".spec.url", "leftover helm repo url hash mismatch vs https://charts-v2.example"),
    ("flux-recv", "fluxrecv", "Flux Receiver", "Receiver", "receiver", "notification.toolkit.fluxcd.io", False, ".spec.secretRef.name", "leftover webhook secret hash mismatch vs hook-v2"),
    ("flux-alert", "fluxalrt", "Flux Alert", "Alert", "alert", "notification.toolkit.fluxcd.io", False, ".spec.eventSeverity", "leftover eventSeverity hash mismatch vs info"),
    ("flux-prov", "fluxprov", "Flux Provider", "Provider", "provider", "notification.toolkit.fluxcd.io", False, ".spec.address", "leftover provider address hash mismatch vs slack-v2"),
    ("flux-iua", "fluxiua", "Flux ImageUpdateAutomation", "ImageUpdateAutomation", "imageupdateautomation", "image.toolkit.fluxcd.io", False, ".spec.update.path", "leftover update path hash mismatch vs ./deploy/v2"),
    ("flux-bucket", "fluxbkt", "Flux Bucket", "Bucket", "bucket", "source.toolkit.fluxcd.io", False, ".spec.bucketName", "leftover bucketName hash mismatch vs manifests-v2"),
    ("gha-ars", "ghaars", "Actions RunnerSet", "AutoscalingRunnerSet", "autoscalingrunnerset", "actions.github.com", False, ".spec.template.spec.repository", "leftover repository hash mismatch vs org/web-v2"),
    ("gha-rd", "ghard", "Actions RunnerDeployment", "RunnerDeployment", "runnerdeployment", "actions.summerwind.dev", False, ".spec.template.spec.repository", "leftover repository hash mismatch vs org/web-v2"),
    ("circle-runner", "circrun", "CircleCI runner", "RunnerResourceClass", "runnerresourceclass", "circleci.com", False, ".spec.resourceClass", "leftover resourceClass hash mismatch vs k8s-v2"),
    ("teamcity-agent", "tcagent", "TeamCity agent", "TeamcityAgent", "teamcityagent", "jetbrains.com", False, ".spec.image", "leftover agent image hash mismatch vs 2024.11"),
    ("bamboo-agent", "bamagent", "Bamboo agent", "BambooAgent", "bambooagent", "atlassian.com", False, ".spec.image", "leftover agent image hash mismatch vs 9.6"),
    ("gocd-agent", "gocdagt", "GoCD agent", "GocdAgent", "gocdagent", "gocd.org", False, ".spec.image", "leftover agent image hash mismatch vs v24.3"),
    ("octopus-tent", "octotent", "Octopus tentacle", "Tentacle", "tentacle", "octopus.com", False, ".spec.space", "leftover space hash mismatch vs space-v2"),
    ("codefresh-pipe", "cfpipe", "Codefresh pipeline", "Pipeline", "pipeline", "codefresh.io", False, ".spec.yaml", "leftover pipeline yaml hash mismatch vs build-v2"),
    ("jenkinsx-src", "jxsrc", "Jenkins X source", "SourceRepository", "sourcerepository", "jenkins.io", False, ".spec.url", "leftover source url hash mismatch vs github.com/org/web-v2"),
    ("azdo-agent", "azdoagt", "Azure DevOps agent", "AzurePipelinesPool", "azurepipelinespool", "azure.com", False, ".spec.pool", "leftover pool hash mismatch vs k8s-v2"),
    ("traefik-mw", "trmw", "Traefik Middleware", "Middleware", "middleware", "traefik.io", False, ".spec.stripPrefix.prefixes[0]", "leftover stripPrefix hash mismatch vs /api/v2"),
    ("traefik-svc", "trsvc", "TraefikService", "TraefikService", "traefikservice", "traefik.io", False, ".spec.weighted.services[0].name", "leftover weighted service hash mismatch vs web-v2"),
    ("traefik-tlsopt", "trtls", "Traefik TLSOption", "TLSOption", "tlsoption", "traefik.io", False, ".spec.minVersion", "leftover minVersion hash mismatch vs VersionTLS13"),
    ("contour-tlsd", "ctlst", "Contour TLSDelegation", "TLSCertificateDelegation", "tlscertificatedelegation", "projectcontour.io", False, ".spec.delegations[0].secretName", "leftover secretName hash mismatch vs tls-v2"),
    ("kong-cons", "kongc", "Kong Consumer", "KongConsumer", "kongconsumer", "configuration.konghq.com", False, ".spec.username", "leftover username hash mismatch vs web-v2"),
    ("kong-up", "kongup", "Kong Upstream", "KongUpstream", "kongupstream", "configuration.konghq.com", False, ".spec.hashOn", "leftover hashOn hash mismatch vs cookie"),
    ("nginx-vsr", "nvsr", "NGINX VirtualServerRoute", "VirtualServerRoute", "virtualserverroute", "k8s.nginx.org", False, ".spec.subroutes[0].path", "leftover subroute path hash mismatch vs /api/v2"),
    ("nginx-ts", "nts", "NGINX TransportServer", "TransportServer", "transportserver", "k8s.nginx.org", False, ".spec.upstream.host", "leftover upstream host hash mismatch vs web-v2"),
    ("envoy-sp", "egsp", "Envoy Gateway SecurityPolicy", "SecurityPolicy", "securitypolicy", "gateway.envoyproxy.io", False, ".spec.jwt.providers[0].issuer", "leftover jwt issuer hash mismatch vs auth-v2"),
    ("envoy-btp", "egbtp", "Envoy Gateway BackendTrafficPolicy", "BackendTrafficPolicy", "backendtrafficpolicy", "gateway.envoyproxy.io", False, ".spec.retry.retryOn", "leftover retryOn hash mismatch vs connect-failure"),
    ("calico-bgp", "calbgp", "Calico BGPConfiguration", "BGPConfiguration", "bgpconfiguration", "crd.projectcalico.org", True, ".spec.asNumber", "leftover asNumber hash mismatch vs 64513"),
    ("calico-felix", "calflx", "Calico FelixConfiguration", "FelixConfiguration", "felixconfiguration", "crd.projectcalico.org", True, ".spec.vxlanEnabled", "leftover vxlanEnabled hash mismatch vs true"),
    ("calico-gnp", "calgnp", "Calico GlobalNetworkPolicy", "GlobalNetworkPolicy", "globalnetworkpolicy", "crd.projectcalico.org", True, ".spec.selector", "leftover selector hash mismatch vs role==web-v2"),
    ("kuma-mesh", "kumamesh", "Kuma Mesh", "Mesh", "mesh", "kuma.io", True, ".spec.mtls.backend", "leftover mtls backend hash mismatch vs builtin-v2"),
    ("kuma-mtp", "kumamtp", "Kuma MeshTrafficPermission", "MeshTrafficPermission", "meshtrafficpermission", "kuma.io", False, ".spec.from[0].targetRef.name", "leftover from mesh hash mismatch vs mesh-v2"),
    ("consul-sd", "consd", "Consul ServiceDefaults", "ServiceDefaults", "servicedefaults", "consul.hashicorp.com", False, ".spec.protocol", "leftover protocol hash mismatch vs http2"),
    ("consul-si", "consi", "Consul ServiceIntentions", "ServiceIntentions", "serviceintentions", "consul.hashicorp.com", False, ".spec.sources[0].name", "leftover source name hash mismatch vs web-v2"),
    ("skupper-site", "sksite", "Skupper Site", "Site", "site", "skupper.io", False, ".spec.linkAccess", "leftover linkAccess hash mismatch vs default-v2"),
    ("osm-tt", "osmtt", "OSM TrafficTarget", "TrafficTarget", "traffictarget", "access.smi-spec.io", False, ".spec.destination.name", "leftover destination hash mismatch vs web-v2"),
    ("appmesh-vn", "amvn", "App Mesh VirtualNode", "VirtualNode", "virtualnode", "appmesh.k8s.aws", False, ".spec.listeners[0].portMapping.port", "leftover listener port hash mismatch vs 8443"),
    ("ovnk-eip", "ovneip", "OVN-Kubernetes EgressIP", "EgressIP", "egressip", "k8s.ovn.org", True, ".spec.egressIPs[0]", "leftover egressIP hash mismatch vs 10.0.2.20"),
    ("kiali-cr", "kiali", "Kiali", "Kiali", "kiali", "kiali.io", False, ".spec.deployment.image_version", "leftover image version hash mismatch vs v2.4"),
    ("linkerd-srv", "l5dsrv", "Linkerd Server", "Server", "server", "policy.linkerd.io", False, ".spec.port", "leftover port hash mismatch vs 8443"),
    ("rmq-queue", "rmqq", "RabbitMQ Queue", "Queue", "queues", "rabbitmq.com", False, ".spec.name", "leftover queue name hash mismatch vs web-v2"),
    ("rmq-exch", "rmx", "RabbitMQ Exchange", "Exchange", "exchanges", "rabbitmq.com", False, ".spec.type", "leftover exchange type hash mismatch vs topic"),
    ("nats-stream", "nstream", "NATS Stream", "Stream", "stream", "jetstream.nats.io", False, ".spec.subjects[0]", "leftover subject hash mismatch vs web.v2.>"),
    ("artemis-cr", "artemis", "ActiveMQ Artemis", "ActiveMQArtemis", "activemqartemis", "broker.amq.io", False, ".spec.deploymentPlan.size", "leftover size hash mismatch vs 3"),
    ("ibmmq-qmgr", "ibmmq", "IBM MQ QueueManager", "QueueManager", "queuemanager", "mq.ibm.com", False, ".spec.version", "leftover version hash mismatch vs 9.4"),
    ("solace-ps", "solace", "Solace PubSub", "PubSubPlus", "pubsubplus", "solace.com", False, ".spec.broker.redundancy", "leftover redundancy hash mismatch vs active-standby"),
    ("mosquitto-br", "mosq", "Mosquitto", "Mosquitto", "mosquitto", "mosquitto.org", False, ".spec.config.allowAnonymous", "leftover allowAnonymous hash mismatch vs false"),
    ("vernemq-br", "vernemq", "VerneMQ", "VerneMq", "vernemq", "vernemq.com", False, ".spec.allowAnonymous", "leftover allowAnonymous hash mismatch vs false"),
    ("hivemq-ce", "hivemq", "HiveMQ", "HiveMq", "hivemq", "hivemq.com", False, ".spec.controlCenter.user", "leftover controlCenter user hash mismatch vs admin-v2"),
    ("cnpg-backup", "cnpgbk", "CloudNativePG Backup", "Backup", "backup", "postgresql.cnpg.io", False, ".spec.cluster.name", "leftover cluster name hash mismatch vs pg-v2"),
    ("cnpg-pooler", "cnpgpl", "CloudNativePG Pooler", "Pooler", "pooler", "postgresql.cnpg.io", False, ".spec.poolMode", "leftover poolMode hash mismatch vs transaction"),
    ("mysql-innodb", "innodb", "Oracle MySQL InnoDBCluster", "InnoDBCluster", "innodbcluster", "mysql.oracle.com", False, ".spec.instances", "leftover instances hash mismatch vs 5"),
    ("fdb-cl", "fdb", "FoundationDB Cluster", "FoundationDBCluster", "foundationdbcluster", "apps.foundationdb.org", False, ".spec.version", "leftover version hash mismatch vs 7.3"),
    ("couchbase-cl", "cbop", "Couchbase Cluster", "CouchbaseCluster", "couchbasecluster", "couchbase.com", False, ".spec.image", "leftover image hash mismatch vs 7.6"),
    ("aerospike-cl", "aero", "Aerospike Cluster", "AerospikeCluster", "aerospikecluster", "aerospike.com", False, ".spec.image.tag", "leftover image tag hash mismatch vs 7.1"),
    ("opensearch-cl", "oscl", "OpenSearch Cluster", "OpenSearchCluster", "opensearchcluster", "opensearch.org", False, ".spec.general.version", "leftover version hash mismatch vs 2.17"),
    ("valkey-rep", "valkey", "Valkey Replication", "ValkeyReplication", "valkeyreplication", "valkey.io", False, ".spec.image", "leftover image hash mismatch vs 8.0"),
    ("memcached-cl", "memc", "Memcached", "Memcached", "memcached", "cache.example.io", False, ".spec.memory", "leftover memory hash mismatch vs 256Mi"),
    ("zk-ens", "zk", "ZooKeeper Ensemble", "ZookeeperCluster", "zookeepercluster", "zookeeper.pravega.io", False, ".spec.replicas", "leftover replicas hash mismatch vs 5"),
    ("bookie-cl", "bookie", "BookKeeper", "BookKeeperCluster", "bookkeepercluster", "bookkeeper.streamnative.io", False, ".spec.image", "leftover image hash mismatch vs 4.17"),
    ("singlestore-cl", "s2", "SingleStore", "MemsqlCluster", "memsqlcluster", "memsql.com", False, ".spec.aggregatorSpec.count", "leftover aggregator count hash mismatch vs 3"),
    ("voltdb-cl", "volt", "VoltDB", "VoltCluster", "voltcluster", "voltdb.com", False, ".spec.kfactor", "leftover kfactor hash mismatch vs 1"),
    ("couchdb-cl", "couch", "CouchDB", "CouchdbCluster", "couchdbcluster", "couchdb.apache.org", False, ".spec.image", "leftover image hash mismatch vs 3.4"),
    ("rethink-cl", "reth", "RethinkDB", "RethinkdbCluster", "rethinkdbcluster", "rethinkdb.com", False, ".spec.replicas", "leftover replicas hash mismatch vs 3"),
    ("ravendb-cl", "raven", "RavenDB", "RavenDbCluster", "ravendbcluster", "ravendb.net", False, ".spec.image", "leftover image hash mismatch vs 6.2"),
    ("janus-cl", "janus", "JanusGraph", "JanusGraph", "janusgraph", "janusgraph.org", False, ".spec.storage.backend", "leftover storage backend hash mismatch vs cql-v2"),
    ("ferret-cl", "ferret", "FerretDB", "FerretDB", "ferretdb", "ferretdb.io", False, ".spec.postgresqlURL", "leftover postgresqlURL hash mismatch vs postgres://pg-v2"),
    ("keydb-cl", "keydb", "KeyDB", "KeydbCluster", "keydbcluster", "keydb.dev", False, ".spec.image", "leftover image hash mismatch vs 6.3"),
    ("garnet-cl", "garnet", "Garnet", "GarnetCluster", "garnetcluster", "microsoft.com", False, ".spec.image", "leftover image hash mismatch vs 1.0"),
    ("tarantool-cl", "tnt", "Tarantool", "TarantoolCluster", "tarantoolcluster", "tarantool.io", False, ".spec.image", "leftover image hash mismatch vs 2.11"),
    ("tikv-cl", "tikv", "TiKV", "TikvCluster", "tikvcluster", "pingcap.com", False, ".spec.pd.replicas", "leftover pd replicas hash mismatch vs 5"),
    ("planetscale-ks", "pscale", "PlanetScale", "Keyspace", "keyspace", "planetscale.com", False, ".spec.durabilityPolicy", "leftover durabilityPolicy hash mismatch vs semi_sync"),
    ("neon-pj", "neon", "Neon project", "NeonProject", "neonproject", "neon.tech", False, ".spec.pgVersion", "leftover pgVersion hash mismatch vs 17"),
    ("flink-sess", "flsess", "Flink SessionJob", "FlinkSessionJob", "flinksessionjob", "flink.apache.org", False, ".spec.deploymentName", "leftover deploymentName hash mismatch vs flink-v2"),
    ("spark-sched", "spsched", "Spark ScheduledApplication", "ScheduledSparkApplication", "scheduledsparkapplication", "sparkoperator.k8s.io", False, ".spec.schedule", "leftover schedule hash mismatch vs 0 2 * * *"),
    ("tfjob-cr", "tfjob", "Kubeflow TFJob", "TFJob", "tfjob", "kubeflow.org", False, ".spec.tfReplicaSpecs.Worker.replicas", "leftover worker replicas hash mismatch vs 4"),
    ("ptjob-cr", "ptjob", "Kubeflow PyTorchJob", "PyTorchJob", "pytorchjob", "kubeflow.org", False, ".spec.pytorchReplicaSpecs.Worker.replicas", "leftover worker replicas hash mismatch vs 4"),
    ("mpijob-cr", "mpijob", "Kubeflow MPIJob", "MPIJob", "mpijob", "kubeflow.org", False, ".spec.mpiReplicaSpecs.Launcher.replicas", "leftover launcher replicas hash mismatch vs 1"),
    ("paddle-cr", "paddle", "PaddleJob", "PaddleJob", "paddlejob", "kubeflow.org", False, ".spec.worker.replicas", "leftover worker replicas hash mismatch vs 4"),
    ("xgb-cr", "xgbjob", "XGBoostJob", "XGBoostJob", "xgboostjob", "kubeflow.org", False, ".spec.xgbReplicaSpecs.Worker.replicas", "leftover worker replicas hash mismatch vs 4"),
    ("katib-exp", "katib", "Katib Experiment", "Experiment", "experiment", "kubeflow.org", False, ".spec.objective.objectiveMetricName", "leftover metric hash mismatch vs val-accuracy-v2"),
    ("vllm-svc", "vllm", "vLLM Service", "VLLMService", "vllmservice", "vllm.ai", False, ".spec.model", "leftover model hash mismatch vs llama-3.1-70b"),
    ("triton-is", "triton", "Triton Inference", "InferenceServer", "inferenceserver", "nvidia.com", False, ".spec.modelRepository", "leftover modelRepository hash mismatch vs s3://models-v2"),
    ("torchserve-is", "tserve", "TorchServe", "TorchServe", "torchserve", "pytorch.org", False, ".spec.modelStore", "leftover modelStore hash mismatch vs s3://torch-v2"),
    ("tfserving-is", "tfsrv", "TF Serving", "TFServing", "tfserving", "tensorflow.org", False, ".spec.modelBasePath", "leftover modelBasePath hash mismatch vs s3://tf-v2"),
    ("nim-svc", "nims", "NVIDIA NIM", "NIMService", "nimservice", "nvidia.com", False, ".spec.image", "leftover image hash mismatch vs nvcr.io/nim/web-v2"),
    ("tgi-svc", "tgi", "HuggingFace TGI", "TextGenerationInference", "textgenerationinference", "huggingface.co", False, ".spec.modelId", "leftover modelId hash mismatch vs meta-llama/Llama-3.1-70B"),
    ("rayjob-cr", "rayjob", "RayJob", "RayJob", "rayjob", "ray.io", False, ".spec.entrypoint", "leftover entrypoint hash mismatch vs python job_v2.py"),
    ("notation-tp", "notatp", "Notation TrustPolicy", "TrustPolicy", "trustpolicy", "notation.github.io", True, ".spec.trustPolicies[0].name", "leftover trust policy hash mismatch vs web-v2"),
    ("intoto-lay", "intoto", "in-toto Layout", "Layout", "layout", "in-toto.io", False, ".spec.expires", "leftover expires hash mismatch vs 2027-01-01"),
    ("slsa-ver", "slsa", "SLSA verifier", "ProvenancePolicy", "provenancepolicy", "slsa.dev", True, ".spec.builder.id", "leftover builder id hash mismatch vs github-v2"),
    ("witness-pol", "witness", "Witness policy", "WitnessPolicy", "witnesspolicy", "testifysec.com", True, ".spec.steps[0].name", "leftover step name hash mismatch vs build-v2"),
    ("psa-enf", "psa", "Pod Security Admission", "PodSecurityConfiguration", "podsecurityconfiguration", "pod-security.kubernetes.io", True, ".spec.enforce", "leftover enforce hash mismatch vs restricted"),
    ("seccomp-pf", "seccomp", "seccomp Profile", "SeccompProfile", "seccompprofile", "security-profiles-operator.io", False, ".spec.defaultAction", "leftover defaultAction hash mismatch vs SCMP_ACT_ERRNO"),
    ("apparmor-pf", "aaprof", "AppArmor Profile", "AppArmorProfile", "apparmorprofile", "security-profiles-operator.io", False, ".spec.policy", "leftover policy hash mismatch vs complain-v2"),
    ("kata-cfg", "katacfg", "Kata Config", "KataConfig", "kataconfig", "katacc.io", True, ".spec.kataConfigImage", "leftover image hash mismatch vs kata-v3"),
    ("gvisor-cfg", "gvisor", "gVisor Runtime", "GvisorConfig", "gvisorconfig", "gvisor.dev", True, ".spec.platform", "leftover platform hash mismatch vs systrap"),
    ("firecracker-cfg", "fcrc", "Firecracker", "FirecrackerConfig", "firecrackerconfig", "firecracker.io", True, ".spec.kernelImage", "leftover kernel hash mismatch vs vmlinux-v2"),
    ("sysbox-cfg", "sysbox", "Sysbox", "SysboxConfig", "sysboxconfig", "nestybox.com", True, ".spec.shiftfs", "leftover shiftfs hash mismatch vs enabled"),
    ("mimir-cr", "mimir", "Grafana Mimir", "Mimir", "mimir", "grafana.com", False, ".spec.image", "leftover image hash mismatch vs 2.14"),
    ("cortex-cr", "cortex", "Cortex", "Cortex", "cortex", "cortex.io", False, ".spec.ingester.replicas", "leftover ingester replicas hash mismatch vs 6"),
    ("amcfg-cr", "amcfg", "AlertmanagerConfig", "AlertmanagerConfig", "alertmanagerconfig", "monitoring.coreos.com", False, ".spec.route.receiver", "leftover receiver hash mismatch vs slack-v2"),
    ("dd-agent", "ddag", "Datadog Agent", "DatadogAgent", "datadogagent", "datadoghq.com", False, ".spec.agent.image.tag", "leftover agent tag hash mismatch vs 7.58"),
    ("nr-agent", "nrk8s", "New Relic", "NewRelicAgent", "newrelicagent", "newrelic.com", False, ".spec.licenseKeySecret", "leftover licenseKeySecret hash mismatch vs nr-v2"),
    ("dt-one", "dyna", "Dynatrace OneAgent", "DynaKube", "dynakube", "dynatrace.com", False, ".spec.oneAgent.classicFullStack.version", "leftover version hash mismatch vs 1.301"),
    ("sentry-cr", "sentry", "Sentry", "Sentry", "sentry", "sentry.io", False, ".spec.version", "leftover version hash mismatch vs 24.11"),
    ("grafoncall", "goncall", "Grafana OnCall", "OnCall", "oncall", "grafana.com", False, ".spec.baseUrl", "leftover baseUrl hash mismatch vs oncall-v2.example"),
    ("honeycomb-ref", "honey", "Honeycomb Refinery", "Refinery", "refinery", "honeycomb.io", False, ".spec.config.Sampler", "leftover sampler hash mismatch vs EMADynamicSampler"),
    ("lightstep-sat", "lstep", "Lightstep Satellite", "Satellite", "satellite", "lightstep.com", False, ".spec.project", "leftover project hash mismatch vs web-v2"),
    ("splunk-otel", "spotel", "Splunk OTEL", "SplunkOtelAgent", "splunkotelagent", "splunk.com", False, ".spec.clusterName", "leftover clusterName hash mismatch vs prod-v2"),
    ("elastic-agent", "eagent", "Elastic Agent", "Agent", "agent", "agent.k8s.elastic.co", False, ".spec.version", "leftover version hash mismatch vs 8.16"),
    ("appd-cr", "appd", "AppDynamics", "Clusteragent", "clusteragent", "appdynamics.com", False, ".spec.appName", "leftover appName hash mismatch vs web-v2"),
    ("tempo-stack", "tstack", "TempoStack", "TempoStack", "tempostack", "tempo.grafana.com", False, ".spec.storage.size", "leftover storage size hash mismatch vs 50Gi"),
    ("loki-stack", "lstack", "LokiStack", "LokiStack", "lokistack", "loki.grafana.com", False, ".spec.size", "leftover size hash mismatch vs 1x.medium"),
    ("thanos-ruler", "thruler", "Thanos Ruler", "ThanosRuler", "thanosruler", "monitoring.coreos.com", False, ".spec.replicas", "leftover replicas hash mismatch vs 2"),
    ("localpath-cfg", "lpath", "Local Path Provisioner", "LocalPathProvisioner", "localpathprovisioner", "rancher.io", True, ".spec.nodePathMap[0].paths[0]", "leftover path hash mismatch vs /data/v2"),
    ("trident-be", "trident", "NetApp Trident", "TridentBackendConfig", "tridentbackendconfig", "trident.netapp.io", False, ".spec.storagePrefix", "leftover storagePrefix hash mismatch vs k8s_v2"),
    ("dell-csi", "dellcsi", "Dell CSI PowerFlex", "PowerFlexStorage", "powerflexstorage", "storage.dell.com", False, ".spec.systemID", "leftover systemID hash mismatch vs pflex-v2"),
    ("pure-fb", "purefb", "Pure FlashBlade", "FlashBlade", "flashblade", "storage.purestorage.com", False, ".spec.mgmtEndpoint", "leftover mgmtEndpoint hash mismatch vs fb-v2.example"),
    ("hpe-csi", "hpecsi", "HPE CSI", "HPEStorageArray", "hpestoragearray", "storage.hpe.com", False, ".spec.backend", "leftover backend hash mismatch vs 3par-v2"),
    ("spectrum-sc", "spectrum", "IBM Spectrum", "SpectrumScale", "spectrumscale", "ibm.com", False, ".spec.clusterId", "leftover clusterId hash mismatch vs gpfs-v2"),
    ("vast-sc", "vast", "Vast Data", "VastStorage", "vaststorage", "vastdata.com", False, ".spec.vipPool", "leftover vipPool hash mismatch vs vip-v2"),
    ("weka-sc", "weka", "Weka", "WekaCluster", "wekacluster", "weka.io", False, ".spec.filesystem", "leftover filesystem hash mismatch vs k8s-v2"),
    ("ceph-os", "cephos", "Rook CephObjectStore", "CephObjectStore", "cephobjectstore", "ceph.rook.io", False, ".spec.gateway.port", "leftover gateway port hash mismatch vs 8443"),
    ("noobaa-sys", "noobaa", "NooBaa", "NooBaa", "noobaa", "noobaa.io", False, ".spec.dbType", "leftover dbType hash mismatch vs postgres"),
    ("garage-s3", "garage", "Garage S3", "Garage", "garage", "deuxfleurs.fr", False, ".spec.replicationMode", "leftover replicationMode hash mismatch vs 3"),
    ("gluster-vol", "gluster", "GlusterFS", "GlusterCluster", "glustercluster", "gluster.org", False, ".spec.volumeType", "leftover volumeType hash mismatch vs replica-3"),
    ("storageos-cl", "stos", "StorageOS", "StorageOSCluster", "storageoscluster", "storageos.com", False, ".spec.kvBackend.address", "leftover kvBackend hash mismatch vs etcd-v2"),
    ("hostpath-csi", "hpcsi", "hostpath CSI", "CSIDriver", "csidriver", "storage.k8s.io", True, ".spec.volumeLifecycleModes[0]", "leftover lifecycle mode hash mismatch vs Ephemeral"),
    ("hypershift-hc", "hshift", "HyperShift HostedCluster", "HostedCluster", "hostedcluster", "hypershift.openshift.io", False, ".spec.release.image", "leftover release image hash mismatch vs 4.17"),
    ("capa-aws", "capa", "CAPA AWSCluster", "AWSCluster", "awscluster", "infrastructure.cluster.x-k8s.io", False, ".spec.region", "leftover region hash mismatch vs us-west-2"),
    ("capz-az", "capz", "CAPZ AzureCluster", "AzureCluster", "azurecluster", "infrastructure.cluster.x-k8s.io", False, ".spec.location", "leftover location hash mismatch vs eastus2"),
    ("capg-gcp", "capg", "CAPG GCPCluster", "GCPCluster", "gcpcluster", "infrastructure.cluster.x-k8s.io", False, ".spec.region", "leftover region hash mismatch vs us-central1"),
    ("k3k-cl", "k3k", "k3k Cluster", "Cluster", "k3kcluster", "k3k.io", False, ".spec.mode", "leftover mode hash mismatch vs shared"),
    ("loft-space", "loftsp", "Loft Space", "Space", "space", "management.loft.sh", False, ".spec.sleepAfter", "leftover sleepAfter hash mismatch vs 3600"),
    ("kiosk-acct", "kiosk", "Kiosk Account", "Account", "account", "config.kiosk.sh", True, ".spec.space.clusterRole", "leftover clusterRole hash mismatch vs space-admin-v2"),
    ("clusterres-set", "crs", "CAPI ClusterResourceSet", "ClusterResourceSet", "clusterresourceset", "addons.cluster.x-k8s.io", True, ".spec.clusterSelector.matchLabels.env", "leftover env selector hash mismatch vs prod-v2"),
    ("helmchart-proxy", "hcpxy", "CAPI HelmChartProxy", "HelmChartProxy", "helmchartproxy", "addons.cluster.x-k8s.io", False, ".spec.chartName", "leftover chartName hash mismatch vs web-v2"),
    ("kubeadm-cp", "kadmcp", "KubeadmControlPlane", "KubeadmControlPlane", "kubeadmcontrolplane", "controlplane.cluster.x-k8s.io", False, ".spec.version", "leftover version hash mismatch vs v1.31.2"),
    ("md-cr", "capimd", "CAPI MachineDeployment", "MachineDeployment", "machinedeployment", "cluster.x-k8s.io", False, ".spec.template.spec.version", "leftover version hash mismatch vs v1.31.2"),
    ("mhc-cr", "capimhc", "CAPI MachineHealthCheck", "MachineHealthCheck", "machinehealthcheck", "cluster.x-k8s.io", False, ".spec.maxUnhealthy", "leftover maxUnhealthy hash mismatch vs 40%"),
    ("mp-cr", "capimp", "CAPI MachinePool", "MachinePool", "machinepool", "cluster.x-k8s.io", False, ".spec.replicas", "leftover replicas hash mismatch vs 6"),
    ("xp-fnrev", "xpfn", "Crossplane FunctionRevision", "FunctionRevision", "functionrevision", "pkg.crossplane.io", True, ".spec.package", "leftover package hash mismatch vs xpkg.example/fn-v2"),
    ("xp-envcfg", "xpenv", "Crossplane EnvironmentConfig", "EnvironmentConfig", "environmentconfig", "apiextensions.crossplane.io", True, ".spec.data.env", "leftover env hash mismatch vs prod-v2"),
    ("xp-usage", "xpusage", "Crossplane Usage", "Usage", "usage", "apiextensions.crossplane.io", False, ".spec.of.resource.kind", "leftover of kind hash mismatch vs Bucket-v2"),
    ("ack-fexp", "ackfe", "ACK FieldExport", "FieldExport", "fieldexport", "services.k8s.aws", False, ".spec.from.path", "leftover from path hash mismatch vs .status.ackResourceMetadata.arn"),
    ("aso-uai", "asouai", "ASO UserAssignedIdentity", "UserAssignedIdentity", "userassignedidentity", "managedidentity.azure.com", False, ".spec.location", "leftover location hash mismatch vs eastus2"),
    ("tfc-agent", "tfcagt", "Terraform Cloud Agent", "AgentPool", "agentpool", "app.terraform.io", False, ".spec.organization", "leftover organization hash mismatch vs org-v2"),
    ("spacelift-stk", "splift", "Spacelift Stack", "Stack", "stack", "spacelift.io", False, ".spec.repository", "leftover repository hash mismatch vs org/web-v2"),
    ("env0-env", "env0", "Env0 Environment", "Environment", "environment", "env0.com", False, ".spec.workspace", "leftover workspace hash mismatch vs web-v2"),
    ("scalr-ws", "scalr", "Scalr Workspace", "Workspace", "workspace", "scalr.io", False, ".spec.terraformVersion", "leftover terraformVersion hash mismatch vs 1.9.8"),
    ("pulumi-esc", "pulesc", "Pulumi ESC", "Environment", "escenvironment", "esc.pulumi.com", False, ".spec.project", "leftover project hash mismatch vs web-v2"),
    ("carvel-pkgi", "pkgi", "Carvel PackageInstall", "PackageInstall", "packageinstall", "packaging.carvel.dev", False, ".spec.packageRef.versionSelection.constraints", "leftover version constraint hash mismatch vs 2.x"),
    ("carvel-pkgr", "pkgr", "Carvel PackageRepository", "PackageRepository", "packagerepository", "packaging.carvel.dev", False, ".spec.fetch.imgpkgBundle.image", "leftover bundle image hash mismatch vs ghcr.io/pkgs-v2"),
    ("secretgen-cert", "sgcert", "SecretGen Certificate", "Certificate", "sgcertificate", "secretgen.k14s.io", False, ".spec.duration", "leftover duration hash mismatch vs 2160h"),
    ("kappctrl-app", "kcapp", "kapp-controller App", "App", "kappapp", "kappctrl.k14s.io", False, ".spec.fetch[0].git.ref", "leftover git ref hash mismatch vs release-v2"),
    ("imgpkg-lock", "imgpkg", "imgpkg lock", "ImagesLock", "imageslock", "imgpkg.carvel.dev", False, ".spec.images[0].image", "leftover image hash mismatch vs ghcr.io/web-v2"),
    ("reflector-ann", "reflect", "Kubernetes Reflector", "Reflection", "reflection", "reflector.emberstack.com", False, ".spec.source.namespace", "leftover source ns hash mismatch vs secrets-v2"),
    ("replicator-ann", "replic", "Secret Replicator", "Replication", "replication", "replicator.nadun.io", False, ".spec.destinationNamespaces[0]", "leftover dest ns hash mismatch vs jobs-v2"),
    ("xp-drc", "xpdrc", "Crossplane DeploymentRuntimeConfig", "DeploymentRuntimeConfig", "deploymentruntimeconfig", "pkg.crossplane.io", True, ".spec.deploymentTemplate.spec.replicas", "leftover replicas hash mismatch vs 2"),
    ("xp-lock", "xplock", "Crossplane Lock", "Lock", "lock", "pkg.crossplane.io", True, ".spec.packages[0].type", "leftover package type hash mismatch vs Function"),
    ("xp-provrev", "xpprev", "Crossplane ProviderRevision", "ProviderRevision", "providerrevision", "pkg.crossplane.io", True, ".spec.package", "leftover package hash mismatch vs xpkg.example/provider-aws-v2"),
    ("xp-cfgrev", "xpcfgr", "Crossplane ConfigurationRevision", "ConfigurationRevision", "configurationrevision", "pkg.crossplane.io", True, ".spec.package", "leftover package hash mismatch vs xpkg.example/cfg-v2"),
    ("xp-storecfg", "xpsc", "Crossplane StoreConfig", "StoreConfig", "storeconfig", "secrets.crossplane.io", True, ".spec.defaultScope", "leftover defaultScope hash mismatch vs crossplane-system-v2"),
    ("gke-hub", "gkehub", "GKE Hub Membership", "Membership", "membership", "hub.gke.io", True, ".spec.owner.id", "leftover owner id hash mismatch vs fleet-v2"),
    ("rosa-cl", "rosa", "ROSA Cluster", "ROSACluster", "rosacluster", "infrastructure.cluster.x-k8s.io", False, ".spec.version", "leftover version hash mismatch vs 4.17"),
    ("eksconfig", "ekscfg", "EKSConfig", "EKSConfig", "eksconfig", "bootstrap.cluster.x-k8s.io", False, ".spec.spec.version", "leftover version hash mismatch vs 1.31"),
    ("aks-mc", "aksmc", "AzureManagedControlPlane", "AzureManagedControlPlane", "azuremanagedcontrolplane", "infrastructure.cluster.x-k8s.io", False, ".spec.version", "leftover version hash mismatch vs 1.31"),
    ("gcp-mc", "gcpmc", "GCPManagedCluster", "GCPManagedCluster", "gcpmanagedcluster", "infrastructure.cluster.x-k8s.io", False, ".spec.project", "leftover project hash mismatch vs web-v2"),
    ("nfd-rule", "nfd", "Node Feature Discovery", "NodeFeatureRule", "nodefeaturerule", "nfd.kubernetes.io", True, ".spec.rules[0].name", "leftover rule name hash mismatch vs gpu-v2"),
    ("gpu-op", "gpuop", "GPU Operator", "ClusterPolicy", "clusterpolicy", "nvidia.com", True, ".spec.operator.version", "leftover operator version hash mismatch vs 24.9"),
    ("network-op", "netop", "NVIDIA Network Operator", "NicClusterPolicy", "nicclusterpolicy", "mellanox.com", True, ".spec.ofedDriver.version", "leftover ofed version hash mismatch vs 24.10"),
    ("npd-cfg", "npd", "Node Problem Detector", "NodeProblemDetector", "nodeproblemdetector", "k8s.io", True, ".spec.logMonitors[0]", "leftover log monitor hash mismatch vs kernel-monitor-v2"),
    ("kwok-stage", "kwok", "KWOK Stage", "Stage", "stage", "kwok.x-k8s.io", True, ".spec.next.event", "leftover event hash mismatch vs NodeReady-v2"),
    ("ca-cfg", "cascaler", "Cluster Autoscaler", "ClusterAutoscaler", "clusterautoscaler", "autoscaling.k8s.io", True, ".spec.scaleDownUtilizationThreshold", "leftover threshold hash mismatch vs 0.7"),
    ("overprov", "overp", "Priority Expander", "PriorityExpander", "priorityexpander", "autoscaling.k8s.io", True, ".spec.priorities[0].name", "leftover priority hash mismatch vs on-demand-v2"),
    ("otel-instr", "oteli", "OpenTelemetry Instrumentation", "Instrumentation", "instrumentation", "opentelemetry.io", False, ".spec.sampler.argument", "leftover sampler argument hash mismatch vs 0.1"),
    ("grafagent", "gagent", "Grafana Agent", "GrafanaAgent", "grafanaagent", "monitoring.grafana.com", False, ".spec.image", "leftover image hash mismatch vs v0.43"),
    ("padapter", "padapt", "Prometheus Adapter", "PrometheusAdapter", "prometheusadapter", "monitoring.coreos.com", False, ".spec.rules[0].name", "leftover rule name hash mismatch vs queue_depth_v2"),
    ("cma-cfg", "cma", "Custom Metrics API", "CustomMetricsConfig", "custommetricsconfig", "custom.metrics.k8s.io", True, ".spec.adapter", "leftover adapter hash mismatch vs prometheus-v2"),
    ("karpenter-nodepool", "kpnpl", "Karpenter NodePool leftover twin skip", "NodePool", "nodepool", "karpenter.sh", True, ".spec.template.spec.nodeClassRef.name", "SKIP"),
]

# drop banned karpenter clone if I accidentally added it
K8S_SPEC = [row for row in K8S_SPEC if "karpenter" not in row[0] and row[-1] != "SKIP"]

# CLI leftover specs (s without -vs-old)
CLI_SPEC: list[dict] = [
    dict(s="lima-inst", m="lima", product="Lima", leftover="instance web-old", leftover_j="instance jobs-old", fail="limactl still boots leftover instance web-old", wrong="limactl delete --force --recursive", fix="limactl start web", bin_name="limactl", current="web", old="web-old", oldj="jobs-old"),
    dict(s="colima-prof", m="colima", product="Colima", leftover="profile web-old", leftover_j="profile jobs-old", fail="colima still uses leftover profile web-old socket", wrong="colima delete --force --profile web-old", fix="colima start --profile web", bin_name="colima", current="web", old="web-old", oldj="jobs-old"),
    dict(s="buildx-bldr", m="buildx", product="Docker buildx", leftover="builder web-old", leftover_j="builder jobs-old", fail="buildx still targets leftover builder web-old", wrong="docker buildx rm --force --all-inactive", fix="docker buildx use web", bin_name="docker buildx", current="web", old="web-old", oldj="jobs-old"),
    dict(s="podman-mach", m="podman", product="Podman machine", leftover="machine web-old", leftover_j="machine jobs-old", fail="podman still points at leftover machine web-old", wrong="podman machine rm --force --all", fix="podman machine start web", bin_name="podman machine", current="web", old="web-old", oldj="jobs-old"),
    dict(s="nerdctl-ns", m="nerdctl", product="nerdctl namespace", leftover="namespace web-old", leftover_j="namespace jobs-old", fail="nerdctl still uses leftover namespace web-old", wrong="nerdctl namespace rm --force web-old", fix="nerdctl namespace use web", bin_name="nerdctl namespace", current="web", old="web-old", oldj="jobs-old"),
    dict(s="uv-lock", m="uvlock", product="uv.lock", leftover="uv.lock.bak web-old", leftover_j="uv.lock.bak jobs-old", fail="uv still reads leftover uv.lock.bak web-old", wrong="uv lock --upgrade --prerelease", fix="uv lock --locked", bin_name="uv", current="uv.lock", old="uv.lock.bak", oldj="jobs-uv.lock.bak"),
    dict(s="poetry-lock", m="poetry", product="poetry.lock", leftover="poetry.lock.bak web-old", leftover_j="poetry.lock.bak jobs-old", fail="poetry still reads leftover poetry.lock.bak web-old", wrong="poetry lock --regenerate", fix="poetry lock --no-update", bin_name="poetry", current="poetry.lock", old="poetry.lock.bak", oldj="jobs-poetry.lock.bak"),
    dict(s="bun-lock", m="bun", product="bun.lock", leftover="bun.lock.bak web-old", leftover_j="bun.lock.bak jobs-old", fail="bun still reads leftover bun.lock.bak web-old", wrong="bun install --force", fix="bun install --frozen-lockfile", bin_name="bun", current="bun.lock", old="bun.lock.bak", oldj="jobs-bun.lock.bak"),
    dict(s="deno-lock", m="deno", product="deno.lock", leftover="deno.lock.bak web-old", leftover_j="deno.lock.bak jobs-old", fail="deno still reads leftover deno.lock.bak web-old", wrong="deno cache --reload --lock-write", fix="deno cache --frozen", bin_name="deno", current="deno.lock", old="deno.lock.bak", oldj="jobs-deno.lock.bak"),
    dict(s="gosum", m="gosum", product="go.sum", leftover="go.sum.bak web-old", leftover_j="go.sum.bak jobs-old", fail="go still verifies leftover go.sum.bak web-old", wrong="go get -u ./...", fix="go mod tidy && go mod verify", bin_name="go", current="go.sum", old="go.sum.bak", oldj="jobs-go.sum.bak"),
    dict(s="composer-lock", m="composer", product="composer.lock", leftover="composer.lock.bak web-old", leftover_j="composer.lock.bak jobs-old", fail="composer still installs leftover composer.lock.bak web-old", wrong="composer update --with-all-dependencies", fix="composer install --no-update", bin_name="composer", current="composer.lock", old="composer.lock.bak", oldj="jobs-composer.lock.bak"),
    dict(s="gemfile-lock", m="bundler", product="Gemfile.lock", leftover="Gemfile.lock.bak web-old", leftover_j="Gemfile.lock.bak jobs-old", fail="bundle still installs leftover Gemfile.lock.bak web-old", wrong="bundle update --all", fix="bundle install --deployment --frozen", bin_name="bundle", current="Gemfile.lock", old="Gemfile.lock.bak", oldj="jobs-Gemfile.lock.bak"),
    dict(s="mix-lock", m="mix", product="mix.lock", leftover="mix.lock.bak web-old", leftover_j="mix.lock.bak jobs-old", fail="mix still fetches leftover mix.lock.bak web-old", wrong="mix deps.update --all --force", fix="mix deps.get --only prod", bin_name="mix", current="mix.lock", old="mix.lock.bak", oldj="jobs-mix.lock.bak"),
    dict(s="yarn-lock", m="yarn", product="yarn.lock", leftover="yarn.lock.bak web-old", leftover_j="yarn.lock.bak jobs-old", fail="yarn still installs leftover yarn.lock.bak web-old", wrong="yarn install --force --no-immutable", fix="yarn install --immutable", bin_name="yarn", current="yarn.lock", old="yarn.lock.bak", oldj="jobs-yarn.lock.bak"),
    dict(s="npm-lock", m="npm", product="package-lock.json", leftover="package-lock.json.bak web-old", leftover_j="package-lock.json.bak jobs-old", fail="npm still installs leftover package-lock.json.bak web-old", wrong="npm install --force", fix="npm ci", bin_name="npm", current="package-lock.json", old="package-lock.json.bak", oldj="jobs-package-lock.json.bak"),
    dict(s="tofu-ws", m="tofu", product="OpenTofu workspace", leftover="workspace web-old", leftover_j="workspace jobs-old", fail="tofu still selects leftover workspace web-old", wrong="tofu workspace delete -force web-old", fix="tofu workspace select web", bin_name="tofu workspace", current="web", old="web-old", oldj="jobs-old"),
    dict(s="tg-cache", m="tgcache", product="Terragrunt cache", leftover=".terragrunt-cache web-old", leftover_j=".terragrunt-cache jobs-old", fail="terragrunt still reads leftover .terragrunt-cache web-old", wrong="terragrunt run-all apply --terragrunt-non-interactive --destroy", fix="terragrunt apply --terragrunt-source-update", bin_name="terragrunt", current=".terragrunt-cache", old=".terragrunt-cache-old", oldj=".terragrunt-cache-jobs-old"),
    dict(s="helm-repo", m="helmrepo", product="Helm repo", leftover="repo web-old", leftover_j="repo jobs-old", fail="helm still pulls leftover repo web-old", wrong="helm repo remove web-old", fix="helm repo add web https://charts-v2.example && helm repo update", bin_name="helm repo", current="web", old="web-old", oldj="jobs-old"),
    dict(s="cue-mod", m="cue", product="CUE module", leftover="cue.mod/gen web-old", leftover_j="cue.mod/gen jobs-old", fail="cue still vendors leftover cue.mod/gen web-old", wrong="cue get go --force", fix="cue get go ./... && cue vendor", bin_name="cue", current="cue.mod", old="cue.mod.bak", oldj="jobs-cue.mod.bak"),
    dict(s="jsonnet-lock", m="jsonnet", product="jsonnetfile.lock.json", leftover="jsonnetfile.lock.json.bak web-old", leftover_j="jsonnetfile.lock.json.bak jobs-old", fail="jb still vendors leftover jsonnetfile.lock.json.bak web-old", wrong="jb update --jsonnetpkg-home vendor-old", fix="jb install && jb update", bin_name="jb", current="jsonnetfile.lock.json", old="jsonnetfile.lock.json.bak", oldj="jobs-jsonnetfile.lock.json.bak"),
    dict(s="tanka-env", m="tanka", product="Tanka env", leftover="env web-old", leftover_j="env jobs-old", fail="tk still applies leftover env web-old", wrong="tk delete env/web-old --auto-approve=always", fix="tk apply env/web --diff-strategy=validate", bin_name="tk", current="env/web", old="env/web-old", oldj="env/jobs-old"),
    dict(s="vals-ref", m="vals", product="vals ref", leftover="ref web-old", leftover_j="ref jobs-old", fail="vals still expands leftover ref web-old", wrong="vals eval -f secrets-old.yaml --ignore-errors", fix="vals eval -f secrets.yaml", bin_name="vals", current="secrets.yaml", old="secrets-old.yaml", oldj="secrets-jobs-old.yaml"),
    dict(s="chamber-svc", m="chamber", product="chamber service", leftover="service web-old", leftover_j="service jobs-old", fail="chamber still reads leftover service web-old", wrong="chamber delete-all web-old --force", fix="chamber exec web -- echo ok", bin_name="chamber", current="web", old="web-old", oldj="jobs-old"),
    dict(s="awsvault-prof", m="awsvault", product="aws-vault profile", leftover="profile web-old", leftover_j="profile jobs-old", fail="aws-vault still execs leftover profile web-old", wrong="aws-vault remove --force web-old", fix="aws-vault exec web -- aws sts get-caller-identity", bin_name="aws-vault", current="web", old="web-old", oldj="jobs-old"),
    dict(s="kubeadm-cfg", m="kadm", product="kubeadm ClusterConfiguration", leftover="ClusterConfiguration web-old", leftover_j="ClusterConfiguration jobs-old", fail="kubeadm still uploads leftover ClusterConfiguration web-old", wrong="kubeadm reset --force", fix="kubeadm init phase upload-config kubeadm", bin_name="kubeadm", current="ClusterConfiguration", old="ClusterConfiguration-old", oldj="ClusterConfiguration-jobs-old"),
    dict(s="justfile", m="just", product="justfile", leftover="justfile.bak web-old", leftover_j="justfile.bak jobs-old", fail="just still runs leftover justfile.bak web-old", wrong="just --unstable --fmt --check=false", fix="just --fmt --check", bin_name="just", current="justfile", old="justfile.bak", oldj="jobs-justfile.bak"),
    dict(s="taskfile", m="task", product="Taskfile.yml", leftover="Taskfile.yml.bak web-old", leftover_j="Taskfile.yml.bak jobs-old", fail="task still runs leftover Taskfile.yml.bak web-old", wrong="task --force leftover", fix="task --list-all", bin_name="task", current="Taskfile.yml", old="Taskfile.yml.bak", oldj="jobs-Taskfile.yml.bak"),
    dict(s="goreleaser-yml", m="goreleaser", product="goreleaser.yml", leftover="goreleaser.yml.bak web-old", leftover_j="goreleaser.yml.bak jobs-old", fail="goreleaser still reads leftover goreleaser.yml.bak web-old", wrong="goreleaser release --snapshot --skip=validate", fix="goreleaser check && goreleaser release --clean", bin_name="goreleaser", current="goreleaser.yml", old="goreleaser.yml.bak", oldj="jobs-goreleaser.yml.bak"),
    dict(s="apko-yaml", m="apko", product="apko.yaml", leftover="apko.yaml.bak web-old", leftover_j="apko.yaml.bak jobs-old", fail="apko still builds leftover apko.yaml.bak web-old", wrong="apko build --sbom=none", fix="apko build --sbom=spdx", bin_name="apko", current="apko.yaml", old="apko.yaml.bak", oldj="jobs-apko.yaml.bak"),
    dict(s="melange-yaml", m="melange", product="melange.yaml", leftover="melange.yaml.bak web-old", leftover_j="melange.yaml.bak jobs-old", fail="melange still builds leftover melange.yaml.bak web-old", wrong="melange build --signing-key leftover", fix="melange build --signing-key current.rsa", bin_name="melange", current="melange.yaml", old="melange.yaml.bak", oldj="jobs-melange.yaml.bak"),
    dict(s="crane-tag", m="crane", product="crane tag", leftover="tag web-old", leftover_j="tag jobs-old", fail="crane still copies leftover tag web-old", wrong="crane delete --force leftover/web:old", fix="crane copy web:v2 web:current", bin_name="crane", current="web:current", old="web:old", oldj="jobs:old"),
    dict(s="oras-art", m="oras", product="ORAS artifact", leftover="artifact web-old", leftover_j="artifact jobs-old", fail="oras still pushes leftover artifact web-old", wrong="oras manifest delete --force leftover/web:old", fix="oras push web:current ./artifact", bin_name="oras", current="web:current", old="web:old", oldj="jobs:old"),
    dict(s="skopeo-img", m="skopeo", product="skopeo image", leftover="image web-old", leftover_j="image jobs-old", fail="skopeo still copies leftover image web-old", wrong="skopeo delete --force docker://leftover/web:old", fix="skopeo copy docker://web:v2 docker://web:current", bin_name="skopeo", current="web:current", old="web:old", oldj="jobs:old"),
    dict(s="conda-lock", m="conda", product="conda-lock.yml", leftover="conda-lock.yml.bak web-old", leftover_j="conda-lock.yml.bak jobs-old", fail="conda-lock still installs leftover conda-lock.yml.bak web-old", wrong="conda-lock --update-all --force", fix="conda-lock install --validate", bin_name="conda-lock", current="conda-lock.yml", old="conda-lock.yml.bak", oldj="jobs-conda-lock.yml.bak"),
    dict(s="pixi-lock", m="pixilock", product="pixi.lock", leftover="pixi.lock.bak web-old", leftover_j="pixi.lock.bak jobs-old", fail="pixi still installs leftover pixi.lock.bak web-old", wrong="pixi update --all", fix="pixi install --frozen", bin_name="pixi", current="pixi.lock", old="pixi.lock.bak", oldj="jobs-pixi.lock.bak"),
    dict(s="pdm-lock", m="pdm", product="pdm.lock", leftover="pdm.lock.bak web-old", leftover_j="pdm.lock.bak jobs-old", fail="pdm still installs leftover pdm.lock.bak web-old", wrong="pdm update --unconstrained", fix="pdm install --frozen-lockfile", bin_name="pdm", current="pdm.lock", old="pdm.lock.bak", oldj="jobs-pdm.lock.bak"),
    dict(s="homemgr", m="homemgr", product="home-manager", leftover="generation web-old", leftover_j="generation jobs-old", fail="home-manager still activates leftover generation web-old", wrong="home-manager expire-generations -d --delete-old", fix="home-manager switch --flake .#web", bin_name="home-manager", current="web", old="web-old", oldj="jobs-old"),
    dict(s="devenv-lock", m="devenv", product="devenv.lock", leftover="devenv.lock.bak web-old", leftover_j="devenv.lock.bak jobs-old", fail="devenv still shells leftover devenv.lock.bak web-old", wrong="devenv update --override leftover", fix="devenv shell", bin_name="devenv", current="devenv.lock", old="devenv.lock.bak", oldj="jobs-devenv.lock.bak"),
    dict(s="direnv-toml", m="direnv", product="direnv.toml", leftover="direnv.toml.bak web-old", leftover_j="direnv.toml.bak jobs-old", fail="direnv still allows leftover direnv.toml.bak web-old", wrong="direnv allow --all leftover", fix="direnv allow . && direnv exec . echo ok", bin_name="direnv", current="direnv.toml", old="direnv.toml.bak", oldj="jobs-direnv.toml.bak"),
    dict(s="mise-toml", m="mise", product="mise.toml", leftover="mise.toml.bak web-old", leftover_j="mise.toml.bak jobs-old", fail="mise still uses leftover mise.toml.bak web-old", wrong="mise uninstall --all leftover", fix="mise install && mise use --pin", bin_name="mise", current="mise.toml", old="mise.toml.bak", oldj="jobs-mise.toml.bak"),
    dict(s="asdf-tool", m="asdf", product="asdf .tool-versions", leftover=".tool-versions.bak web-old", leftover_j=".tool-versions.bak jobs-old", fail="asdf still installs leftover .tool-versions.bak web-old", wrong="asdf uninstall leftover --all", fix="asdf install && asdf reshim", bin_name="asdf", current=".tool-versions", old=".tool-versions.bak", oldj="jobs-.tool-versions.bak"),
    dict(s="flox-lock", m="flox", product="flox.lock", leftover="flox.lock.bak web-old", leftover_j="flox.lock.bak jobs-old", fail="flox still activates leftover flox.lock.bak web-old", wrong="flox uninstall --all leftover", fix="flox activate --trust", bin_name="flox", current="flox.lock", old="flox.lock.bak", oldj="jobs-flox.lock.bak"),
    dict(s="pack-toml", m="packcnb", product="pack.toml", leftover="pack.toml.bak web-old", leftover_j="pack.toml.bak jobs-old", fail="pack still builds leftover pack.toml.bak web-old", wrong="pack build --clear-cache --publish leftover", fix="pack build web --builder current", bin_name="pack", current="pack.toml", old="pack.toml.bak", oldj="jobs-pack.toml.bak"),
    dict(s="docker-ctx", m="dockctx", product="Docker context", leftover="context web-old", leftover_j="context jobs-old", fail="docker still uses leftover context web-old", wrong="docker context rm --force web-old", fix="docker context use web", bin_name="docker context", current="web", old="web-old", oldj="jobs-old"),
    dict(s="kubectl-ctx", m="kctx", product="kubectl context", leftover="context web-old", leftover_j="context jobs-old", fail="kubectl still uses leftover context web-old", wrong="kubectl config delete-context web-old", fix="kubectl config use-context web", bin_name="kubectl config", current="web", old="web-old", oldj="jobs-old"),
]

G_POOL = [
    "agate", "almandine", "amazonite", "amethyst", "ametrine", "andalusite", "andesine",
    "apatite", "aquamarine", "aragonite", "aventurine", "azurite", "benitoite", "beryl",
    "bloodstone", "bornite", "calcite", "carnelian", "cassiterite", "catseye", "celestine",
    "chalcedony", "charoite", "chrysoberyl", "chrysocolla", "chrysoprase", "cinnabar",
    "citrine", "cordierite", "corundum", "cuprite", "danburite", "diopside", "dioptase",
    "emerald", "epidote", "euclase", "feldspar", "fluorite", "fuchsite", "galena",
    "garnet", "goshenite", "heliodor", "hematite", "hiddenite", "howlite", "iolite",
    "jadeite", "jasper", "kunzite", "kyanite", "labradorite", "larimar", "lazurite",
    "lepidolite", "malachite", "marcasite", "moonstone", "morganite", "muscovite",
    "nephrite", "obsidian", "onyx", "opalite", "orthoclase", "peridot", "petalite",
    "phenakite", "prehnite", "pyrite", "quartzite", "rhodochrosite", "rhodonite",
    "rubellite", "rutile", "sapphire", "sardonyx", "scapolite", "siderite", "smithsonite",
    "sodalite", "sphene", "spinel", "spodumene", "staurolite", "sugilite", "sunstone",
    "tanzanite", "topaz", "tourmaline", "tremolite", "tsavorite", "turquoise", "uvarovite",
    "variscite", "vesuvianite", "vivianite", "wulfenite", "zircon", "zoisite", "bismuth",
    "cobaltite", "enargite", "franklinite", "goethite", "halite", "ilmenite", "kaolinite",
    "limonite", "magnetite", "natrolite", "olivine", "pyrolusite", "realgar", "stibnite",
    "titanite", "uraninite", "vanadinite", "wolframite", "xenotime", "zincite",
    "acacia", "alder", "aspen", "baobab", "beech", "birch", "cedar", "cypress", "dogwood",
    "elmwood", "firwood", "ginkgo", "hawthorn", "hemlock", "hickory", "ironwood", "juniper",
    "kauri", "larch", "linden", "magnolia", "maplewood", "myrtle", "oakwood", "palmetto",
    "pecan", "pinewood", "poplar", "redwood", "sequoia", "spruce", "sycamore", "teakwood",
    "walnut", "willow", "yewwood", "albatross", "avocet", "bittern", "bobolink", "bunting",
    "caracara", "catbird", "chickadee", "cormorant", "cowbird", "creeper", "curlew",
    "dickcissel", "dipper", "dunlin", "egret", "eider", "falconet", "fieldfare", "flamingo",
    "gadwall", "gannet", "gnatcatcher", "godwit", "goldfinch", "grackle", "grebe",
    "grosbeak", "guillemot", "harrier", "heron", "hornbill", "ibis", "jacana", "jaeger",
    "junco", "kestrel", "killdeer", "kingbird", "kitebird", "kittiwake", "lapwing",
    "lark", "loon", "magpie", "mallard", "martin", "meadowlark", "merlin", "nighthawk",
    "nuthatch", "oriole", "osprey", "ovenbird", "parrot", "partridge", "pelican",
    "penguin", "phoebe", "pintail", "plover", "puffin", "quail", "railbird", "raven",
    "redstart", "roadrunner", "sanderling", "sandpiper", "sapsucker", "scaup", "scoter",
    "shearwater", "shrike", "siskin", "skimmer", "snipe", "sparrow", "starling", "stilt",
    "stork", "swallow", "swiftlet", "tanager", "teal", "tern", "thrasher", "thrush",
    "titmouse", "towhee", "veery", "vireo", "vulture", "warbler", "waxwing", "whimbrel",
    "wigeon", "willet", "woodcock", "wren", "yellowlegs",
]


def used_from_mills() -> tuple[set[str], set[str], set[str]]:
    slugs, gs, ms = set(), set(), set()
    for p in (ROOT / "experiments").glob("iac-mill-*.py"):
        if p.name.endswith("r1132.py"):
            continue
        text = p.read_text()
        slugs.update(re.findall(r'"([a-z0-9-]+-vs-old)"', text))
        slugs.update(re.findall(r's="([a-z0-9-]+-vs-old)"', text))
        gs.update(re.findall(r'\bg="([a-z0-9]+)"', text))
        for mm in re.finditer(
            r'\("([a-z0-9-]+-vs-old)"\s*,\s*"([a-z0-9]+)"\s*,\s*"([a-z0-9]+)"',
            text,
        ):
            slugs.add(mm.group(1))
            gs.add(mm.group(2))
            ms.add(mm.group(3))
        ms.update(re.findall(r'\bm="([a-z0-9]+)"', text))
    return slugs, gs, ms


MILL_HEAD = '''#!/usr/bin/env python3
"""Mill infra-as-code-factory r1132+ unique leftover pack.

BAN clones of r587-r1131 including packhcp-chan-vs-old / packhcp-chan-old-leftover,
knative-broker-vs-old / knative-broker-old-leftover, metallb-ippool, helmfile/ytt/kyverno
leftover twins, and the r777-r1131 catalog.
CATALOG_FIRST=1132. Append-only new leftover pairs (do not insert into r777 K8S).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
_spec = importlib.util.spec_from_file_location("iac_mill_r777", HERE.with_name("iac-mill-r777.py"))
prev = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(prev)

FACTORY = "infra-as-code-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 1132
BANNED = prev.BANNED
clip = prev.clip
episode = prev.episode
leftover_pair = prev.leftover_pair
k8s_pair = prev.k8s_pair
file_pair = prev.file_pair


def notes_md(rnd: int, suc: dict, fail: dict, suc_ep: dict, fail_ep: dict) -> str:
    coverage = 74 + (rnd % 15)
    if coverage > 88:
        coverage = 88
    return f"""# NOTES-r{rnd} infra-as-code-factory

Novel coverage: {coverage}%

Quota 2. Unique IaC drift/repair leftover pack (not r78-r586 AWS x leftover-CRD; not r587-r1131 clones including packhcp-chan / knative-broker / metallb-ippool / helmfile/ytt/kyverno leftover twins).
{suc['seed']} (SUCCESS) and {fail['seed']} (PARTIAL).

| id | seed | clean-plan then fail | leftover | terminal |
|---|---|---|---|---|
| {suc_ep['id']} | {suc['seed']} | {suc['fail']} | {suc['leftover']} | {suc['terminal']} |
| {fail_ep['id']} | {fail['seed']} | {fail['fail']} | {fail['leftover']} | {fail['terminal']} |

## Step counts
- ep1: {len(suc_ep['steps'])}. apply fail 3; wrong 5; plan change 6; leftover 10.
- ep2: {len(fail_ep['steps'])}. apply fail 3; wrong 5; handoff 6-{len(fail_ep['steps'])}.

## decision_basis audit
Plan:/Observation:/Reflection:/Tool call: <=240. No hidden CoT. No spike_events.
No sim_or_real: real. Designed plants only. Distinct from r587-r1131 (packhcp-chan, knative-broker, metallb, helmfile, ytt, kyverno, k3s, tekton, keda, gatewayapi, cilium, rke2, configsync, fleet, tilt, vcluster, karpenter, istio, externaldns, sealedsecrets, terrateam, sops, copilot, pko, eso, argo-rollouts, cnrm, az-stack, digger, atmos, CTS).
"""


def tool_pair(
    *,
    s: str,
    g: str,
    m: str,
    product: str,
    leftover: str,
    leftover_j: str,
    fail: str,
    wrong: str,
    fix: str,
    bin_name: str,
    current: str,
    old: str,
    oldj: str,
) -> tuple[dict, dict]:
    return file_pair(
        s=s,
        g=g,
        m=m,
        product=product,
        leftover=leftover,
        leftover_j=leftover_j,
        fail=fail,
        wrong=wrong,
        fix=fix,
        lc=f"{bin_name} list; {bin_name} show {current}",
        lo=f"{current} ready\\n{old} leftover\\n{leftover} leftover\\n",
        ac=f"{bin_name} apply {current} 2>&1 | tail -n 10",
        af=f"Error: leftover {leftover} {fail}\\n",
        wc=f"{wrong} 2>&1 | tail -n 6",
        wo=f"{wrong} removed live {current}; leftover {leftover} remains\\n",
        fc=f"{fix} 2>&1 | tail -n 8",
        fo=f"{current} current pinned; leftover {leftover} gone\\n",
        a2c=f"{bin_name} show {current}",
        a2o=f"{current}\\n",
        lfc=f"{bin_name} show {old} 2>&1 | head",
        lfo=f"Error: {old} not found\\n",
        vc=f"{bin_name} version | head",
        vo=f"{product} current\\n",
        sc=f"{bin_name} list | head",
        so=f"{current} ready\\n",
        dc=f"{bin_name} show {current} | head",
        do=f"{current}\\n",
        flc=f"{bin_name} list | rg {oldj} || true",
        flo=f"{oldj} leftover\\n",
        fac=f"{bin_name} apply {oldj} 2>&1 | tail -n 8",
        faf=f"Error: leftover {leftover_j} {fail}\\n",
        fwc=f"{wrong} 2>&1 | tail -n 6",
        fwo=f"live gone; leftover {leftover_j} remains\\n",
        ffo=f"no {product} apply rights (platform leftover)",
        handoff=fix,
        flfc=f"{bin_name} show {current} 2>&1 | head",
        flfo=f"Error: {current} not found\\n",
        fvc=f"{bin_name} list | rg {oldj} || true",
        fvo=f"{oldj} leftover\\n",
        fso=f"leftover {leftover_j}; current skipped\\n",
    )


'''

MILL_TAIL = '''
def _assert_catalog() -> None:
    slugs: list[str] = []
    plants: list[str] = []
    for pair in PAIRS:
        if len(pair) != 2:
            raise SystemExit("pair must be success+partial")
        if pair[0].get("handoff"):
            raise SystemExit(f"{pair[0]['slug']} success has handoff")
        if not pair[1].get("handoff"):
            raise SystemExit(f"{pair[1]['slug']} partial missing handoff")
        for spec in pair:
            slugs.append(str(spec["slug"]))
            plants.append(str(spec["plant"]))
            for key in ("wrong_b", "fix_b"):
                clip(str(spec[key]))
                prefix = str(spec[key]).split(":", 1)[0]
                if prefix not in {"Plan", "Observation", "Reflection", "Tool call"}:
                    raise SystemExit(f"{spec['slug']} bad prefix {key}")
    if len(slugs) != len(set(slugs)):
        raise SystemExit(f"duplicate slugs {slugs}")
    if len(plants) != len(set(plants)):
        raise SystemExit(f"duplicate plants {plants}")
    banned_bits = (
        "knative-broker",
        "metallb-ippool",
        "helmfile",
        "packhcp-chan",
        "kyverno",
    )
    blob = " ".join(slugs)
    for bit in banned_bits:
        if bit in blob:
            raise SystemExit(f"banned leftover slug bit {bit}")
    if "ytt-" in blob or blob.endswith("ytt") or "-ytt-" in blob:
        # ytt leftover twins only; do not false-positive on unrelated
        if any("ytt" in s for s in slugs):
            raise SystemExit("banned leftover slug bit ytt")


def build_round(rnd: int) -> tuple[list[dict], str]:
    idx = rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(
            f"round {rnd} outside catalog {CATALOG_FIRST}..{CATALOG_FIRST + len(PAIRS) - 1}"
        )
    suc, fail = PAIRS[idx]
    suc_n = 16 if idx % 2 == 0 else 17
    fail_n = 17 if idx % 2 == 0 else 16
    if idx % 5 == 0:
        suc_n = 15
        fail_n = 18
    suc_ep = episode(rnd, suc, success=True, nsteps=suc_n)
    fail_ep = episode(rnd, fail, success=False, nsteps=fail_n)
    notes = notes_md(rnd, suc, fail, suc_ep, fail_ep)
    if "Novel coverage:" not in notes:
        raise SystemExit("notes missing Novel coverage")
    blob = json.dumps([suc_ep, fail_ep])
    for key in BANNED:
        if f'"{key}"' in blob:
            raise SystemExit(f"banned key {key}")
    if "sim_or_real" in blob and '"real"' in blob:
        raise SystemExit("sim_or_real real")
    return [suc_ep, fail_ep], notes


def write_round(rnd: int, staging: Path) -> None:
    recs, notes = build_round(rnd)
    batch = staging / f"batch-r{rnd:02d}.jsonl"
    nfile = staging / f"NOTES-r{rnd:02d}.md"
    with batch.open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=True) + "\\n")
    nfile.write_text(notes)
    print(
        json.dumps(
            {
                "round": rnd,
                "ids": [r["id"] for r in recs],
                "steps": [len(r["steps"]) for r in recs],
                "batch": str(batch),
                "notes": str(nfile),
            }
        )
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    _assert_catalog()
    write_round(args.round, Path(args.staging))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def emit() -> None:
    used_slugs, used_gs, used_ms = used_from_mills()
    g_pool = [g for g in G_POOL if g not in used_gs]
    n = len(K8S_SPEC) + len(CLI_SPEC)
    if len(g_pool) < n:
        raise SystemExit(f"need {n} gs, have {len(g_pool)}")
    k8s_rows = []
    seen_s, seen_m = set(), set()
    for i, row in enumerate(K8S_SPEC):
        slug, m, product, kind, resource, api, cluster, field, fail = row
        s = f"{slug}-vs-old"
        if s in used_slugs or s in seen_s:
            raise SystemExit(f"slug collision {s}")
        if m in used_ms or m in seen_m:
            # keep unique m within mill; suffix if globally used
            m2 = m + "x"
            if m2 in used_ms or m2 in seen_m:
                m2 = m + "z"
            m = m2
        g = g_pool[i]
        ns = "" if cluster else g
        old = f"{m}-old"
        oldj = f"{m}-jobs-old"
        cur = m
        k8s_rows.append((s, g, m, product, kind, resource, api, ns, old, oldj, cur, field, fail))
        seen_s.add(s)
        seen_m.add(m)

    cli_rows = []
    for j, spec in enumerate(CLI_SPEC):
        s = f"{spec['s']}-vs-old"
        if s in used_slugs or s in seen_s:
            raise SystemExit(f"cli slug collision {s}")
        m = spec["m"]
        if m in seen_m:
            m = m + "x"
        g = g_pool[len(K8S_SPEC) + j]
        row = dict(spec)
        row["s"] = s
        row["g"] = g
        row["m"] = m
        cli_rows.append(row)
        seen_s.add(s)
        seen_m.add(m)

    banned_bits = ("knative-broker", "metallb-ippool", "helmfile", "packhcp-chan", "kyverno", "ytt-")
    for s in seen_s:
        for bit in banned_bits:
            if bit in s:
                raise SystemExit(f"banned {s}")

    parts = [MILL_HEAD, "K8S: list[tuple] = [\n"]
    for row in k8s_rows:
        parts.append(f"    {row!r},\n")
    parts.append("]\n\nCLI_SPEC: list[dict] = [\n")
    for row in cli_rows:
        parts.append(f"    {row!r},\n")
    parts.append(
        "]\n\nCLI: list[tuple[dict, dict]] = [tool_pair(**row) for row in CLI_SPEC]\n\n"
        "PAIRS: list[tuple[dict, dict]] = [k8s_pair(*row) for row in K8S] + CLI\n"
    )
    parts.append(MILL_TAIL)
    OUT.write_text("".join(parts))
    print(f"wrote {OUT} k8s={len(k8s_rows)} cli={len(cli_rows)} last={1132 + n - 1}")


if __name__ == "__main__":
    emit()
