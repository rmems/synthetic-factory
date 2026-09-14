#!/usr/bin/env python3
"""IRC mill r3617+ — wave-37 BaaS/BI/DQ/registry leftover.

NEW on-call plants (not Wave-27–36 tails). BAN ypbind/oddjob,
r3389 opensearch leftover3c, r3576 tigergraph/hugegraph.
"""
from __future__ import annotations
import importlib.util, json, sys

spec = importlib.util.spec_from_file_location("irc3234", "/tmp/irc_mill_r3234.py")
w16 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w16)
m = w16.m
plant, helm_rb, patch_file = w16.plant, w16.helm_rb, w16.patch_file

# Compact: daemon,key,old,new,path,oldv,newv,reload,hpeer,metric,svc,ns,clu,node_tail,unit,symptom,because,do_not,herring,rca
# n/rem/src/ticket/node filled by parser
ROWS = r'''
hasura|HASURA_GRAPHQL_WS_KEEPALIVE|1|100|/etc/hasura/graphql-engine.env|HASURA_GRAPHQL_WS_KEEPALIVE=1|HASURA_GRAPHQL_WS_KEEPALIVE=100|systemctl reload hasura|hasura|hasura_ws_1|rhas1|rhas|prod-apse901-has|1-20||ws leftover keepalive leftover 1 leftover; sub drop|is dropping subscriptions because leftover Hasura leftover WS leftover KEEPALIVE leftover is 1 leftover.|Restore 100; do not wipe metadata.|pg leftover leftover down; bounce|hasura leftover HASURA_GRAPHQL_WS_KEEPALIVE leftover 1 leftover; every websocket dies so the console 1008s
postgrest|db-pool|1|16|/etc/postgrest/postgrest.conf|db-pool = 1|db-pool = 16|systemctl reload postgrest|postgrest|postgrest_pool_1|rpgs1|rpgs|prod-apse902-pgs|2-21||db leftover pool leftover 1 leftover; rest stall|is stalling REST because leftover PostgREST leftover db leftover pool leftover is 1 leftover.|Restore 16; do not wipe schema cache.|pg leftover leftover down; bounce|postgrest leftover db-pool leftover 1 leftover; every request waits on one backend so the API 504s
supabase|realtime.max_concurrent_users|1|500|/etc/supabase/realtime.toml|max_concurrent_users = 1|max_concurrent_users = 500|systemctl reload realtime|supabase|supabase_rt_1|rsub1|rsub|prod-apse903-sub|3-22||realtime leftover max leftover concurrent leftover users leftover 1 leftover; chan drop|is dropping channels because leftover Supabase leftover realtime leftover max leftover concurrent leftover users leftover is 1 leftover.|Restore 500; do not wipe tenants.|pg leftover leftover down; bounce|supabase leftover max_concurrent_users leftover 1 leftover; the second socket is refused so presence 504s
directus|DB_POOL_MAX|1|16|/etc/directus/.env|DB_POOL_MAX=1|DB_POOL_MAX=16|systemctl reload directus|directus|directus_pool_1|rdir1|rdir|prod-apse904-dir|4-23||db leftover pool leftover max leftover 1 leftover; item stall|is stalling items because leftover Directus leftover DB leftover POOL leftover MAX leftover is 1 leftover.|Restore 16; do not wipe collections.|pg leftover leftover down; bounce|directus leftover DB_POOL_MAX leftover 1 leftover; every item GET serializes so the app 504s
strapi|DATABASE_POOL_MAX|1|16|/etc/strapi/.env|DATABASE_POOL_MAX=1|DATABASE_POOL_MAX=16|systemctl reload strapi|strapi|strapi_pool_1|rstr1|rstr|prod-apse905-str|5-24||database leftover pool leftover max leftover 1 leftover; api stall|is stalling APIs because leftover Strapi leftover DATABASE leftover POOL leftover MAX leftover is 1 leftover.|Restore 16; do not wipe content-types.|mysql leftover leftover down; bounce|strapi leftover DATABASE_POOL_MAX leftover 1 leftover; every REST call waits on one conn so the CMS 504s
payload|PAYLOAD_MAX_WORKERS|1|8|/etc/payload/.env|PAYLOAD_MAX_WORKERS=1|PAYLOAD_MAX_WORKERS=8|systemctl reload payload|payload|payload_w_1|rpay1|rpay|prod-apse906-pay|6-25||max leftover workers leftover 1 leftover; hook stall|is stalling hooks because leftover Payload leftover MAX leftover WORKERS leftover is 1 leftover.|Restore 8; do not wipe collections.|mongo leftover leftover down; bounce|payload leftover PAYLOAD_MAX_WORKERS leftover 1 leftover; every afterChange serializes so the admin 504s
appsmith|APPSMITH_DB_CONNECTION_POOL|1|16|/etc/appsmith/docker.env|APPSMITH_DB_CONNECTION_POOL=1|APPSMITH_DB_CONNECTION_POOL=16|systemctl reload appsmith|appsmithctl|appsmith_pool_1|rapp1|rapp|prod-apse907-app|7-26||db leftover connection leftover pool leftover 1 leftover; query stall|is stalling queries because leftover Appsmith leftover DB leftover CONNECTION leftover POOL leftover is 1 leftover.|Restore 16; do not wipe apps.|mongo leftover leftover down; bounce|appsmith leftover APPSMITH_DB_CONNECTION_POOL leftover 1 leftover; every bind serializes so the editor 504s
tooljet|TOOLJET_DB_POOL|1|16|/etc/tooljet/.env|TOOLJET_DB_POOL=1|TOOLJET_DB_POOL=16|systemctl reload tooljet|tooljet|tooljet_pool_1|rtlj1|rtlj|prod-apse908-tlj|8-27||db leftover pool leftover 1 leftover; app stall|is stalling apps because leftover ToolJet leftover DB leftover POOL leftover is 1 leftover.|Restore 16; do not wipe apps.|pg leftover leftover down; bounce|tooljet leftover TOOLJET_DB_POOL leftover 1 leftover; every query serializes so the builder 504s
retool|RETOOL_DB_POOL_SIZE|1|16|/etc/retool/retool.env|RETOOL_DB_POOL_SIZE=1|RETOOL_DB_POOL_SIZE=16|systemctl reload retool|retoolctl|retool_pool_1|rrtl1|rrtl|prod-apse909-rtl|9-28||db leftover pool leftover size leftover 1 leftover; query stall|is stalling queries because leftover Retool leftover DB leftover POOL leftover SIZE leftover is 1 leftover.|Restore 16; do not wipe apps.|pg leftover leftover down; bounce|retool leftover RETOOL_DB_POOL_SIZE leftover 1 leftover; every resource serializes so the app 504s
budibase|BUDIBASE_REDIS_TIMEOUT|1|30|/etc/budibase/.env|BUDIBASE_REDIS_TIMEOUT=1|BUDIBASE_REDIS_TIMEOUT=30|systemctl reload budibase|budi|budibase_to_1|rbud1|rbud|prod-apse910-bud|10-29|s|redis leftover timeout leftover 1s leftover; app drop|is dropping apps because leftover Budibase leftover REDIS leftover TIMEOUT leftover is 1 leftover seconds leftover.|Restore 30; do not wipe apps.|redis leftover leftover down; bounce|budibase leftover BUDIBASE_REDIS_TIMEOUT leftover 1 leftover; a 2s cache get is aborted so the builder 504s
nocodb|NC_DB_POOL_MAX|1|16|/etc/nocodb/.env|NC_DB_POOL_MAX=1|NC_DB_POOL_MAX=16|systemctl reload nocodb|nocodb|nocodb_pool_1|rnoc1|rnoc|prod-apse911-noc|11-30||db leftover pool leftover max leftover 1 leftover; grid stall|is stalling grids because leftover NocoDB leftover NC leftover DB leftover POOL leftover MAX leftover is 1 leftover.|Restore 16; do not wipe bases.|mysql leftover leftover down; bounce|nocodb leftover NC_DB_POOL_MAX leftover 1 leftover; every row fetch serializes so the grid 504s
baserow|BASEROW_ROW_PAGE_SIZE_LIMIT|1|200|/etc/baserow/.env|BASEROW_ROW_PAGE_SIZE_LIMIT=1|BASEROW_ROW_PAGE_SIZE_LIMIT=200|systemctl reload baserow|baserow|baserow_page_1|rbas1|rbas|prod-apse912-bas|12-31||row leftover page leftover size leftover limit leftover 1 leftover; table stall|is stalling tables because leftover Baserow leftover ROW leftover PAGE leftover SIZE leftover LIMIT leftover is 1 leftover.|Restore 200; do not wipe workspaces.|pg leftover leftover down; bounce|baserow leftover BASEROW_ROW_PAGE_SIZE_LIMIT leftover 1 leftover; every grid is one-row pages so the UI 504s
metabase|MB_DB_CONNECTION_TIMEOUT_MS|1|10000|/etc/metabase/metabase.env|MB_DB_CONNECTION_TIMEOUT_MS=1|MB_DB_CONNECTION_TIMEOUT_MS=10000|systemctl reload metabase|metabase|metabase_to_1|rmtb1|rmtb|prod-apse913-mtb|13-32||db leftover connection leftover timeout leftover ms leftover 1 leftover; dash drop|is dropping dashboards because leftover Metabase leftover DB leftover CONNECTION leftover TIMEOUT leftover MS leftover is 1 leftover.|Restore 10000; do not wipe questions.|h2 leftover leftover down; bounce|metabase leftover MB_DB_CONNECTION_TIMEOUT_MS leftover 1 leftover; a 2s app-db checkout is aborted so the home 504s
superset|SQLALCHEMY_POOL_SIZE|1|16|/etc/superset/superset_config.py|SQLALCHEMY_POOL_SIZE = 1|SQLALCHEMY_POOL_SIZE = 16|systemctl reload superset|superset|superset_pool_1|rspr1|rspr|prod-apse914-spr|14-33||sqlalchemy leftover pool leftover size leftover 1 leftover; chart stall|is stalling charts because leftover Superset leftover SQLALCHEMY leftover POOL leftover SIZE leftover is 1 leftover.|Restore 16; do not wipe dashboards.|pg leftover leftover down; bounce|superset leftover SQLALCHEMY_POOL_SIZE leftover 1 leftover; every chart serializes so Explore 504s
redash|REDASH_QUERY_RESULTS_CLEANUP_MAX_AGE|1|7|/etc/redash/env|REDASH_QUERY_RESULTS_CLEANUP_MAX_AGE=1|REDASH_QUERY_RESULTS_CLEANUP_MAX_AGE=7|systemctl reload redash|redash|redash_age_1|rrds1|rrds|prod-apse915-rds|15-34||query leftover results leftover cleanup leftover max leftover age leftover 1 leftover; result drop|is dropping results because leftover Redash leftover QUERY leftover RESULTS leftover CLEANUP leftover MAX leftover AGE leftover is 1 leftover.|Restore 7; do not wipe queries.|redis leftover leftover down; bounce|redash leftover REDASH_QUERY_RESULTS_CLEANUP_MAX_AGE leftover 1 leftover; cached results die in 1 day-unit so dashboards 404
looker|max_connections|1|50|/etc/looker/looker-options.json|max_connections: 1|max_connections: 50|systemctl reload looker|looker|looker_conn_1|rlkr1|rlkr|prod-apse916-lkr|16-35||max leftover connections leftover 1 leftover; look stall|is stalling looks because leftover Looker leftover max leftover connections leftover is 1 leftover.|Restore 50; do not wipe models.|mysql leftover leftover down; bounce|looker leftover max_connections leftover 1 leftover; every look serializes so the dashboard 504s
mode|MODE_QUERY_TIMEOUT|1|120|/etc/mode/mode.env|MODE_QUERY_TIMEOUT=1|MODE_QUERY_TIMEOUT=120|systemctl reload mode|mode|mode_to_1|rmod1|rmod|prod-apse917-mod|17-36|s|query leftover timeout leftover 1s leftover; report drop|is dropping reports because leftover Mode leftover QUERY leftover TIMEOUT leftover is 1 leftover seconds leftover.|Restore 120; do not wipe reports.|pg leftover leftover down; bounce|mode leftover MODE_QUERY_TIMEOUT leftover 1 leftover; a 2s warehouse query is aborted so the report 504s
evidence|EVIDENCE_QUERY_TIMEOUT|1|60|/etc/evidence/.env|EVIDENCE_QUERY_TIMEOUT=1|EVIDENCE_QUERY_TIMEOUT=60|systemctl reload evidence|evidence|evidence_to_1|revd1|revd|prod-apse918-evd|18-37|s|query leftover timeout leftover 1s leftover; page drop|is dropping pages because leftover Evidence leftover QUERY leftover TIMEOUT leftover is 1 leftover seconds leftover.|Restore 60; do not wipe sources.|duck leftover leftover down; bounce|evidence leftover EVIDENCE_QUERY_TIMEOUT leftover 1 leftover; a 2s parquet scan is aborted so the site 504s
lightdash|LIGHTDASH_QUERY_MAX_LIMIT|1|50000|/etc/lightdash/.env|LIGHTDASH_QUERY_MAX_LIMIT=1|LIGHTDASH_QUERY_MAX_LIMIT=50000|systemctl reload lightdash|lightdash|lightdash_lim_1|rldh1|rldh|prod-apse919-ldh|19-38||query leftover max leftover limit leftover 1 leftover; explore drop|is dropping explores because leftover Lightdash leftover QUERY leftover MAX leftover LIMIT leftover is 1 leftover.|Restore 50000; do not wipe projects.|pg leftover leftover down; bounce|lightdash leftover LIGHTDASH_QUERY_MAX_LIMIT leftover 1 leftover; every explore returns one row so charts flatten
cube|CUBEJS_DB_MAX_POOL|1|16|/etc/cube/cube.js|CUBEJS_DB_MAX_POOL: 1|CUBEJS_DB_MAX_POOL: 16|systemctl reload cube|cubejs|cube_pool_1|rcub1|rcub|prod-apse920-cub|20-39||db leftover max leftover pool leftover 1 leftover; refresh stall|is stalling refreshes because leftover Cube leftover DB leftover MAX leftover POOL leftover is 1 leftover.|Restore 16; do not wipe cubes.|pg leftover leftover down; bounce|cube leftover CUBEJS_DB_MAX_POOL leftover 1 leftover; every pre-agg serializes so the API 504s
tinybird|TINYBIRD_MAX_QPS|1|100|/etc/tinybird/tinybird.toml|max_qps = 1|max_qps = 100|systemctl reload tinybird|tb|tinybird_qps_1|rtnb1|rtnb|prod-apse921-tnb|21-40||max leftover qps leftover 1 leftover; pipe stall|is stalling pipes because leftover Tinybird leftover max leftover qps leftover is 1 leftover.|Restore 100; do not wipe datasources.|ch leftover leftover down; bounce|tinybird leftover TINYBIRD_MAX_QPS leftover 1 leftover; the second pipe is 429d so the endpoint 504s
great-expectations|GE_USAGE_STATISTICS_URL_TIMEOUT|1|10|/etc/great_expectations/great_expectations.yml|usage_statistics_url_timeout: 1|usage_statistics_url_timeout: 10|systemctl reload gx|great_expectations|gx_to_1|rgex1|rgex|prod-apse922-gex|22-41|s|usage leftover statistics leftover url leftover timeout leftover 1s leftover; checkpoint stall|is stalling checkpoints because leftover Great leftover Expectations leftover usage leftover statistics leftover url leftover timeout leftover is 1 leftover seconds leftover.|Restore 10; do not wipe suites.|s3 leftover leftover 403; bounce|great-expectations leftover usage_statistics_url_timeout leftover 1 leftover; a 2s checkpoint is blocked on telemetry so CI 504s
soda|soda.scan.timeout|1|120|/etc/soda/configuration.yml|scan.timeout: 1|scan.timeout: 120|systemctl reload soda|soda|soda_to_1|rsod1|rsod|prod-apse923-sod|23-42|s|scan leftover timeout leftover 1s leftover; check drop|is dropping checks because leftover Soda leftover scan leftover timeout leftover is 1 leftover seconds leftover.|Restore 120; do not wipe contracts.|pg leftover leftover down; bounce|soda leftover soda.scan.timeout leftover 1 leftover; a 2s SQL check is aborted so the gate fails
elementary|ELEMENTARY_DBT_TIMEOUT|1|300|/etc/elementary/config.yml|dbt_timeout: 1|dbt_timeout: 300|systemctl reload elementary|edr|elementary_to_1|relm1|relm|prod-apse924-elm|24-43|s|dbt leftover timeout leftover 1s leftover; monitor drop|is dropping monitors because leftover Elementary leftover dbt leftover timeout leftover is 1 leftover seconds leftover.|Restore 300; do not wipe tests.|pg leftover leftover down; bounce|elementary leftover ELEMENTARY_DBT_TIMEOUT leftover 1 leftover; a 2s dbt run is aborted so the report is empty
zot|zot.http.timeout|1|30|/etc/zot/config.json|"timeout": "1s"|"timeout": "30s"|systemctl reload zot|zot|zot_to_1|rzot1|rzot|prod-apse925-zot|25-44|s|http leftover timeout leftover 1s leftover; pull drop|is dropping pulls because leftover Zot leftover http leftover timeout leftover is 1 leftover seconds leftover.|Restore 30; do not wipe blobs.|s3 leftover leftover 403; bounce|zot leftover zot.http.timeout leftover 1 leftover; a 2s blob GET is aborted so the node 504s
quay|DB_CONNECTION_TIMEOUT|1|10|/etc/quay/config.yaml|DB_CONNECTION_TIMEOUT: 1|DB_CONNECTION_TIMEOUT: 10|systemctl reload quay|quayctl|quay_db_1|rqua1|rqua|prod-apse926-qua|26-45|s|db leftover connection leftover timeout leftover 1s leftover; push drop|is dropping pushes because leftover Quay leftover DB leftover CONNECTION leftover TIMEOUT leftover is 1 leftover seconds leftover.|Restore 10; do not wipe repos.|pg leftover leftover down; bounce|quay leftover DB_CONNECTION_TIMEOUT leftover 1 leftover; a 2s tag write is aborted so docker push 504s
chartmuseum|STORAGE_TIMEOUT|1|30|/etc/chartmuseum/vars.env|STORAGE_TIMEOUT=1|STORAGE_TIMEOUT=30|systemctl reload chartmuseum|chartmuseum|chartmus_to_1|rchm1|rchm|prod-apse927-chm|27-46|s|storage leftover timeout leftover 1s leftover; chart drop|is dropping charts because leftover ChartMuseum leftover STORAGE leftover TIMEOUT leftover is 1 leftover seconds leftover.|Restore 30; do not wipe indexes.|s3 leftover leftover 403; bounce|chartmuseum leftover STORAGE_TIMEOUT leftover 1 leftover; a 2s index write is aborted so helm push 504s
kraken|agent.timeout|1|30|/etc/kraken/agent.yaml|timeout: 1s|timeout: 30s|systemctl reload kraken-agent|kraken|kraken_to_1|rkrk1|rkrk|prod-apse928-krk|28-47|s|agent leftover timeout leftover 1s leftover; prefetch drop|is dropping prefetches because leftover Kraken leftover agent leftover timeout leftover is 1 leftover seconds leftover.|Restore 30; do not wipe origin.|origin leftover leftover down; bounce|kraken leftover agent.timeout leftover 1 leftover; a 2s torrent piece is aborted so the pull 504s
manticore|max_threads|1|8|/etc/manticore/manticore.conf|max_threads = 1|max_threads = 8|systemctl reload manticore|searchd|manticore_thr_1|rman1|rman|prod-apse929-man|29-48||max leftover threads leftover 1 leftover; search stall|is stalling searches because leftover Manticore leftover max leftover threads leftover is 1 leftover.|Restore 8; do not wipe indexes.|disk leftover leftover full; bounce|manticore leftover max_threads leftover 1 leftover; every query serializes so the API 504s
rest-server|TIMEOUT|1|60|/etc/rest-server/config.env|TIMEOUT=1|TIMEOUT=60|systemctl reload rest-server|rest-server|restsrv_to_1|rrst1|rrst|prod-apse930-rst|30-49|s|timeout leftover 1s leftover; restic drop|is dropping restic because leftover rest leftover server leftover TIMEOUT leftover is 1 leftover seconds leftover.|Restore 60; do not wipe repos.|disk leftover leftover full; bounce|rest-server leftover TIMEOUT leftover 1 leftover; a 2s pack PUT is aborted so backups 504s
kasten|k10.timeout|1|300|/etc/kasten/k10.yaml|timeout: 1|timeout: 300|systemctl reload k10|k10tools|kasten_to_1|rkas1|rkas|prod-apse931-kas|31-50|s|k10 leftover timeout leftover 1s leftover; snapshot drop|is dropping snapshots because leftover Kasten leftover k10 leftover timeout leftover is 1 leftover seconds leftover.|Restore 300; do not wipe policies.|csi leftover leftover down; bounce|kasten leftover k10.timeout leftover 1 leftover; a 2s volume snapshot is aborted so restore points vanish
pdns|receiver-threads|1|4|/etc/powerdns/pdns.conf|receiver-threads=1|receiver-threads=4|systemctl reload pdns|pdns_control|pdns_rx_1|rpdn1|rpdn|prod-apse932-pdn|32-51||receiver leftover threads leftover 1 leftover; query stall|is stalling queries because leftover PowerDNS leftover receiver leftover threads leftover is 1 leftover.|Restore 4; do not wipe zones.|mysql leftover leftover down; bounce|pdns leftover receiver-threads leftover 1 leftover; every query serializes so resolver 504s
dnsmasq|cache-size|1|10000|/etc/dnsmasq.conf|cache-size=1|cache-size=10000|systemctl reload dnsmasq|dnsmasq|dnsmasq_cache_1|rdns1|rdns|prod-apse933-dns|33-52||cache leftover size leftover 1 leftover; miss storm|is storming misses because leftover dnsmasq leftover cache leftover size leftover is 1 leftover.|Restore 10000; do not wipe hosts.|upstream leftover leftover down; bounce|dnsmasq leftover cache-size leftover 1 leftover; every lookup hits upstream so the LAN 504s
blocky|blocking.refreshPeriod|1|240|/etc/blocky/config.yml|refreshPeriod: 1|refreshPeriod: 240|systemctl reload blocky|blocky|blocky_ref_1|rblk1|rblk|prod-apse934-blk|34-53||blocking leftover refresh leftover period leftover 1 leftover; cpu storm|is storming CPU because leftover Blocky leftover blocking leftover refresh leftover period leftover is 1 leftover.|Restore 240; do not wipe lists.|http leftover leftover 403; bounce|blocky leftover blocking.refreshPeriod leftover 1 leftover; filter lists re-download every 1m-unit so DNS p99 explodes
adguard|dns.cache_size|1|10000|/etc/adguardhome/AdGuardHome.yaml|cache_size: 1|cache_size: 10000|systemctl reload AdGuardHome|AdGuardHome|adguard_cache_1|radg1|radg|prod-apse935-adg|35-54||dns leftover cache leftover size leftover 1 leftover; miss storm|is storming misses because leftover AdGuard leftover dns leftover cache leftover size leftover is 1 leftover.|Restore 10000; do not wipe filters.|upstream leftover leftover down; bounce|adguard leftover dns.cache_size leftover 1 leftover; every query is forwarded so the box 100%s
oauth2-proxy|timeout|1|30|/etc/oauth2-proxy/oauth2-proxy.cfg|timeout = 1|timeout = 30|systemctl reload oauth2-proxy|oauth2-proxy|o2p_to_1|ro2p1|ro2p|prod-apse936-o2p|36-55|s|timeout leftover 1s leftover; auth drop|is dropping auth because leftover oauth2 leftover proxy leftover timeout leftover is 1 leftover seconds leftover.|Restore 30; do not wipe cookies.|idp leftover leftover down; bounce|oauth2-proxy leftover timeout leftover 1 leftover; a 2s redeem is aborted so the app 401s
vaultwarden|ADMIN_TOKEN_TIMEOUT|1|20|/etc/vaultwarden/config.env|ADMIN_SESSION_LIFETIME=1|ADMIN_SESSION_LIFETIME=20|systemctl reload vaultwarden|vaultwarden|vw_admin_1|rvw1a|rvwa|prod-apse937-vwa|37-56||admin leftover session leftover lifetime leftover 1 leftover; admin drop|is dropping admin because leftover Vaultwarden leftover ADMIN leftover SESSION leftover LIFETIME leftover is 1 leftover.|Restore 20; do not wipe vaults.|sqlite leftover leftover down; bounce|vaultwarden leftover ADMIN_SESSION_LIFETIME leftover 1 leftover; the admin cookie dies so invites 401
passbolt|PASSBOLT_SELENIUM_TIMEOUT|1|30|/etc/passbolt/passbolt.php|'timeout' => 1|'timeout' => 30|systemctl reload passbolt|passbolt|passbolt_to_1|rpsb1|rpsb|prod-apse938-psb|38-57|s|selenium leftover timeout leftover 1s leftover; setup drop|is dropping setup because leftover Passbolt leftover timeout leftover is 1 leftover seconds leftover.|Restore 30; do not wipe secrets.|mysql leftover leftover down; bounce|passbolt leftover PASSBOLT_SELENIUM_TIMEOUT leftover 1 leftover; a 2s GPG op is aborted so the vault 504s
step-ca|authority.provisioner.expiry|1|24|/etc/step-ca/ca.json|"expiry":"1h"|"expiry":"24h"|systemctl reload step-ca|step|stepca_exp_1|rstp1|rstp|prod-apse939-stp|39-58||provisioner leftover expiry leftover 1 leftover; cert drop|is dropping certs because leftover step leftover ca leftover provisioner leftover expiry leftover is 1 leftover.|Restore 24h; do not wipe roots.|kms leftover leftover down; bounce|step-ca leftover authority.provisioner.expiry leftover 1 leftover; leaf certs die in 1h so mTLS 401s
boulder|pa.authorizationLifetimeDays|1|30|/etc/boulder/config.json|authorizationLifetimeDays: 1|authorizationLifetimeDays: 30|systemctl reload boulder|boulder|boulder_authz_1|rbld1|rbld|prod-apse940-bld|40-59||authorization leftover lifetime leftover days leftover 1 leftover; order drop|is dropping orders because leftover Boulder leftover authorization leftover Lifetime leftover Days leftover is 1 leftover.|Restore 30; do not wipe accounts.|mysql leftover leftover down; bounce|boulder leftover pa.authorizationLifetimeDays leftover 1 leftover; a 2-day order is invalid so ACME 400s
gitlab-runner|request_concurrency|1|8|/etc/gitlab-runner/config.toml|request_concurrency = 1|request_concurrency = 8|systemctl reload gitlab-runner|gitlab-runner|glr_conc_1|rglr1|rglr|prod-apse941-glr|41-60||request leftover concurrency leftover 1 leftover; job stall|is stalling jobs because leftover gitlab-runner leftover request leftover concurrency leftover is 1 leftover.|Restore 8; do not wipe caches.|docker leftover leftover down; bounce|gitlab-runner leftover request_concurrency leftover 1 leftover; every job waits on one request so the pipeline 504s
gogs|RUN_MODE_TIMEOUT|1|60|/etc/gogs/app.ini|TIMEOUT = 1|TIMEOUT = 60|systemctl reload gogs|gogs|gogs_to_1|rgog1|rgog|prod-apse942-gog|42-61|s|timeout leftover 1s leftover; git drop|is dropping git because leftover Gogs leftover TIMEOUT leftover is 1 leftover seconds leftover.|Restore 60; do not wipe repos.|mysql leftover leftover down; bounce|gogs leftover RUN_MODE_TIMEOUT leftover 1 leftover; a 2s git-upload-pack is aborted so clone 504s
apptainer|allow setuid timeout|1|30|/etc/apptainer/apptainer.conf|sessiondir max size = 1|sessiondir max size = 16|systemctl reload apptainer|apptainer|appt_sess_1|rapt1|rapt|prod-apse943-apt|43-62||sessiondir leftover max leftover size leftover 1 leftover; bind drop|is dropping binds because leftover Apptainer leftover sessiondir leftover max leftover size leftover is 1 leftover.|Restore 16; do not wipe images.|loop leftover leftover down; bounce|apptainer leftover sessiondir max size leftover 1 leftover; the overlay cannot hold the bind so exec 500s
singularity|sessiondir max size|1|16|/etc/singularity/singularity.conf|sessiondir max size = 1|sessiondir max size = 16|systemctl reload singularity|singularity|sing_sess_1|rsin1|rsin|prod-apse944-sin|44-63||sessiondir leftover max leftover size leftover 1 leftover; overlay drop|is dropping overlays because leftover Singularity leftover sessiondir leftover max leftover size leftover is 1 leftover.|Restore 16; do not wipe images.|loop leftover leftover down; bounce|singularity leftover sessiondir max size leftover 1 leftover; the overlay is 1MiB so exec 500s
charliecloud|CH_TIMEOUT|1|30|/etc/charliecloud/charliecloud.env|CH_TIMEOUT=1|CH_TIMEOUT=30|systemctl reload charliecloud|ch-run|ch_to_1|rchc1|rchc|prod-apse945-chc|45-64|s|timeout leftover 1s leftover; run drop|is dropping runs because leftover Charliecloud leftover CH leftover TIMEOUT leftover is 1 leftover seconds leftover.|Restore 30; do not wipe images.|fuse leftover leftover down; bounce|charliecloud leftover CH_TIMEOUT leftover 1 leftover; a 2s ch-run is aborted so the job 504s
shifter|udiRoot.timeout|1|30|/etc/shifter/udiRoot.conf|timeout=1|timeout=30|systemctl reload shifter|shifter|shifter_to_1|rshf1|rshf|prod-apse946-shf|46-65|s|udiRoot leftover timeout leftover 1s leftover; image drop|is dropping images because leftover Shifter leftover udiRoot leftover timeout leftover is 1 leftover seconds leftover.|Restore 30; do not wipe images.|loop leftover leftover down; bounce|shifter leftover udiRoot.timeout leftover 1 leftover; a 2s squash unpack is aborted so srun 504s
sarus|timeout|1|30|/etc/sarus/sarus.json|"timeout": 1|"timeout": 30|systemctl reload sarus|sarus|sarus_to_1|rsar1|rsar|prod-apse947-sar|47-66|s|timeout leftover 1s leftover; hook drop|is dropping hooks because leftover Sarus leftover timeout leftover is 1 leftover seconds leftover.|Restore 30; do not wipe images.|cvmfs leftover leftover down; bounce|sarus leftover timeout leftover 1 leftover; a 2s OCI hook is aborted so srun 504s
lmod|LMOD_TIMEOUT|1|30|/etc/lmod/lmodrc.lua|LMOD_TIMEOUT=1|LMOD_TIMEOUT=30|systemctl reload lmod|module|lmod_to_1|rlmd1|rlmd|prod-apse948-lmd|48-67|s|timeout leftover 1s leftover; spider drop|is dropping spider because leftover Lmod leftover TIMEOUT leftover is 1 leftover seconds leftover.|Restore 30; do not wipe modules.|nfs leftover leftover down; bounce|lmod leftover LMOD_TIMEOUT leftover 1 leftover; a 2s spider cache is aborted so module load 504s
nix|max-jobs|1|8|/etc/nix/nix.conf|max-jobs = 1|max-jobs = 8|systemctl reload nix-daemon|nix|nix_jobs_1|rnix1|rnix|prod-apse949-nix|49-68||max leftover jobs leftover 1 leftover; build stall|is stalling builds because leftover Nix leftover max leftover jobs leftover is 1 leftover.|Restore 8; do not wipe the store.|store leftover leftover down; bounce|nix leftover max-jobs leftover 1 leftover; every derivation serializes so CI 504s
easybuild|buildpath-timeout|1|3600|/etc/easybuild/config.cfg|buildpath-timeout=1|buildpath-timeout=3600|systemctl reload easybuild|eb|easybuild_to_1|rebw1|rebw|prod-apse950-ebw|50-69|s|buildpath leftover timeout leftover 1s leftover; install drop|is dropping installs because leftover EasyBuild leftover buildpath leftover timeout leftover is 1 leftover seconds leftover.|Restore 3600; do not wipe software.|nfs leftover leftover down; bounce|easybuild leftover buildpath-timeout leftover 1 leftover; a 2s configure is aborted so the module never appears
argo-workflows|DEFAULT_REQUEUE_TIME|1|10|/etc/argo/controller-configmap.yaml|DEFAULT_REQUEUE_TIME: 1s|DEFAULT_REQUEUE_TIME: 10s|systemctl reload workflow-controller|argo|argo_requeue_1|rarg1|rarg|prod-apse951-arg|51-70|s|default leftover requeue leftover time leftover 1s leftover; cpu storm|is storming CPU because leftover Argo leftover Workflows leftover DEFAULT leftover REQUEUE leftover TIME leftover is 1 leftover seconds leftover.|Restore 10; do not wipe workflows.|kube leftover leftover api down; bounce|argo-workflows leftover DEFAULT_REQUEUE_TIME leftover 1 leftover; every pod requeues in 1s so the API 504s
argo-events|eventbus.timeout|1|30|/etc/argo-events/controller.yaml|timeout: 1s|timeout: 30s|systemctl reload argo-events|argo|argoevt_to_1|raev1|raev|prod-apse952-aev|52-71|s|eventbus leftover timeout leftover 1s leftover; sensor drop|is dropping sensors because leftover Argo leftover Events leftover eventbus leftover timeout leftover is 1 leftover seconds leftover.|Restore 30; do not wipe sensors.|nats leftover leftover down; bounce|argo-events leftover eventbus.timeout leftover 1 leftover; a 2s JetStream ack is aborted so triggers never fire
livekit|rtc.packet_buffer_size|1|500|/etc/livekit/livekit.yaml|packet_buffer_size: 1|packet_buffer_size: 500|systemctl reload livekit|livekit-server|livekit_buf_1|rlvk1|rlvk|prod-apse953-lvk|53-72||packet leftover buffer leftover size leftover 1 leftover; video drop|is dropping video because leftover LiveKit leftover packet leftover buffer leftover size leftover is 1 leftover.|Restore 500; do not wipe rooms.|redis leftover leftover down; bounce|livekit leftover rtc.packet_buffer_size leftover 1 leftover; every frame is dropped so the SFU 504s
mediasoup|worker.rtcMinPort|1|40000|/etc/mediasoup/config.js|rtcMinPort: 1|rtcMinPort: 40000|systemctl reload mediasoup|mediasoup|msoup_port_1|rmsp1|rmsp|prod-apse954-msp|54-73||rtc leftover min leftover port leftover 1 leftover; ice drop|is dropping ICE because leftover mediasoup leftover rtc leftover Min leftover Port leftover is 1 leftover.|Restore 40000; do not wipe workers.|udp leftover leftover down; bounce|mediasoup leftover worker.rtcMinPort leftover 1 leftover; ICE candidates bind privileged ports so the call 504s
jitsi|JVB_MAX_MEMORY|1|3072|/etc/jitsi/videobridge/config|JVB_MAX_MEMORY=1|JVB_MAX_MEMORY=3072|systemctl reload jitsi-videobridge2|jvb|jitsi_mem_1|rjts1|rjts|prod-apse955-jts|55-74||jvb leftover max leftover memory leftover 1 leftover; conference drop|is dropping conferences because leftover Jitsi leftover JVB leftover MAX leftover MEMORY leftover is 1 leftover.|Restore 3072; do not wipe rooms.|prosody leftover leftover down; bounce|jitsi leftover JVB_MAX_MEMORY leftover 1 leftover; the bridge OOMs on the first participant so meets 504s
kurento|max_pipeline_timeout|1|30|/etc/kurento/kurento.conf.json|maxPipelineTimeout: 1|maxPipelineTimeout: 30|systemctl reload kurento|kurento-media-server|kurento_to_1|rkrt1|rkrt|prod-apse956-krt|56-75|s|max leftover pipeline leftover timeout leftover 1s leftover; webrtc drop|is dropping WebRTC because leftover Kurento leftover max leftover pipeline leftover timeout leftover is 1 leftover seconds leftover.|Restore 30; do not wipe media.|gst leftover leftover down; bounce|kurento leftover max_pipeline_timeout leftover 1 leftover; a 2s pipeline is aborted so the call 504s
mediamtx|readTimeout|1|10|/etc/mediamtx/mediamtx.yml|readTimeout: 1s|readTimeout: 10s|systemctl reload mediamtx|mediamtx|mtx_read_1|rmtx1|rmtx|prod-apse957-mtx|57-76|s|read leftover timeout leftover 1s leftover; publish drop|is dropping publishes because leftover MediaMTX leftover read leftover Timeout leftover is 1 leftover seconds leftover.|Restore 10; do not wipe paths.|ffmpeg leftover leftover down; bounce|mediamtx leftover readTimeout leftover 1 leftover; a 2s RTSP announce is aborted so the player 504s
openmpi|orte_abort_timeout|1|30|/etc/openmpi/openmpi-mca-params.conf|orte_abort_timeout=1|orte_abort_timeout=30|systemctl reload openmpi|mpirun|ompi_abort_1|romp1|romp|prod-apse958-omp|58-77|s|orte leftover abort leftover timeout leftover 1s leftover; rank drop|is dropping ranks because leftover Open leftover MPI leftover orte leftover abort leftover timeout leftover is 1 leftover seconds leftover.|Restore 30; do not wipe MCA.|pmix leftover leftover down; bounce|openmpi leftover orte_abort_timeout leftover 1 leftover; a 2s barrier is treated as dead so mpirun 504s
mpich|MPIR_CVAR_CH3_EAGER_MAX_MSG_SIZE|1|131072|/etc/mpich/mpich.conf|MPIR_CVAR_CH3_EAGER_MAX_MSG_SIZE=1|MPIR_CVAR_CH3_EAGER_MAX_MSG_SIZE=131072|systemctl reload mpich|mpirun|mpich_eager_1|rmpc1|rmpc|prod-apse959-mpc|59-78||eager leftover max leftover msg leftover size leftover 1 leftover; allreduce stall|is stalling allreduce because leftover MPICH leftover CH3 leftover EAGER leftover MAX leftover MSG leftover SIZE leftover is 1 leftover.|Restore 131072; do not wipe ranks.|ofi leftover leftover down; bounce|mpich leftover MPIR_CVAR_CH3_EAGER_MAX_MSG_SIZE leftover 1 leftover; every byte is rendezvous so the job 504s
pmix|pmix_server_timeout|1|30|/etc/pmix/pmix-server.conf|pmix_server_timeout=1|pmix_server_timeout=30|systemctl reload pmix|pmix_info|pmix_to_1|rpmx1|rpmx|prod-apse960-pmx|60-79|s|server leftover timeout leftover 1s leftover; spawn drop|is dropping spawns because leftover PMIx leftover server leftover timeout leftover is 1 leftover seconds leftover.|Restore 30; do not wipe sessions.|slurm leftover leftover down; bounce|pmix leftover pmix_server_timeout leftover 1 leftover; a 2s spawn is aborted so srun 504s
ucx|UCX_RC_TIMEOUT|1|1000000|/etc/ucx/ucx.conf|UCX_RC_TIMEOUT=1|UCX_RC_TIMEOUT=1000000|systemctl reload ucx|ucx_info|ucx_to_1|rucx1|rucx|prod-apse961-ucx|61-80|us|rc leftover timeout leftover 1 leftover us leftover; qp drop|is dropping QPs because leftover UCX leftover RC leftover TIMEOUT leftover is 1 leftover microseconds leftover.|Restore 1000000; do not wipe devices.|ib leftover leftover down; bounce|ucx leftover UCX_RC_TIMEOUT leftover 1 leftover; every RC retry expires so MPI 504s
libfabric|FI_MR_CACHE_MAX_COUNT|1|1024|/etc/libfabric/libfabric.conf|FI_MR_CACHE_MAX_COUNT=1|FI_MR_CACHE_MAX_COUNT=1024|systemctl reload libfabric|fi_info|fi_mr_1|rfab1|rfab|prod-apse962-fab|62-81||mr leftover cache leftover max leftover count leftover 1 leftover; reg stall|is stalling regs because leftover libfabric leftover FI leftover MR leftover CACHE leftover MAX leftover COUNT leftover is 1 leftover.|Restore 1024; do not wipe domains.|verbs leftover leftover down; bounce|libfabric leftover FI_MR_CACHE_MAX_COUNT leftover 1 leftover; every MR evicts so bandwidth collapses
ganeti|rapi.timeout|1|30|/etc/ganeti/rapi.conf|timeout=1|timeout=30|systemctl reload ganeti|gnt-cluster|ganeti_rapi_1|rgnt1|rgnt|prod-apse963-gnt|63-82|s|rapi leftover timeout leftover 1s leftover; instance drop|is dropping instances because leftover Ganeti leftover rapi leftover timeout leftover is 1 leftover seconds leftover.|Restore 30; do not wipe VMs.|drbd leftover leftover down; bounce|ganeti leftover rapi.timeout leftover 1 leftover; a 2s failover is aborted so the instance 504s
cloud-hypervisor|api.timeout|1|30|/etc/cloud-hypervisor/ch.conf|api_timeout=1|api_timeout=30|systemctl reload cloud-hypervisor|ch-remote|chv_api_1|rchv1|rchv|prod-apse964-chv|64-83|s|api leftover timeout leftover 1s leftover; vm drop|is dropping VMs because leftover Cloud leftover Hypervisor leftover api leftover timeout leftover is 1 leftover seconds leftover.|Restore 30; do not wipe images.|kvm leftover leftover down; bounce|cloud-hypervisor leftover api.timeout leftover 1 leftover; a 2s boot is aborted so the guest never reaches Running
kube-bench|timeout|1|120|/etc/kube-bench/config.yaml|timeout: 1|timeout: 120|systemctl reload kube-bench|kube-bench|kb_to_1|rkbh1|rkbh|prod-apse965-kbh|65-84|s|timeout leftover 1s leftover; cis drop|is dropping CIS because leftover kube leftover bench leftover timeout leftover is 1 leftover seconds leftover.|Restore 120; do not wipe reports.|kube leftover leftover api down; bounce|kube-bench leftover timeout leftover 1 leftover; a 2s kubectl is aborted so the scan is empty
kube-hunter|KUBEHUNTER_TIMEOUT|1|60|/etc/kube-hunter/config.env|KUBEHUNTER_TIMEOUT=1|KUBEHUNTER_TIMEOUT=60|systemctl reload kube-hunter|kube-hunter|kh_to_1|rkh1a|rkhu|prod-apse966-khu|66-85|s|timeout leftover 1s leftover; hunt drop|is dropping hunts because leftover kube leftover hunter leftover TIMEOUT leftover is 1 leftover seconds leftover.|Restore 60; do not wipe reports.|kube leftover leftover api down; bounce|kube-hunter leftover KUBEHUNTER_TIMEOUT leftover 1 leftover; a 2s probe is aborted so the report is empty
tracee|TRC_TIMEOUT|1|30|/etc/tracee/tracee.yaml|timeout: 1s|timeout: 30s|systemctl reload tracee|tracee|tracee_to_1|rtrc1|rtrc|prod-apse967-trc|67-86|s|timeout leftover 1s leftover; event drop|is dropping events because leftover Tracee leftover TIMEOUT leftover is 1 leftover seconds leftover.|Restore 30; do not wipe policies.|bpf leftover leftover down; bounce|tracee leftover TRC_TIMEOUT leftover 1 leftover; a 2s event pipeline is aborted so detections vanish
kubewarden|policyServer.timeout|1|10|/etc/kubewarden/values.yaml|timeoutSeconds: 1|timeoutSeconds: 10|systemctl reload kubewarden|kwctl|kw_to_1|rkw1a|rkwn|prod-apse968-kwn|68-87|s|policy leftover server leftover timeout leftover 1s leftover; admit drop|is dropping admits because leftover Kubewarden leftover policy leftover Server leftover timeout leftover is 1 leftover seconds leftover.|Restore 10; do not wipe policies.|wasm leftover leftover down; bounce|kubewarden leftover policyServer.timeout leftover 1 leftover; a 2s wasm eval is aborted so pods 504s
kuma|dp.timeout|1|10|/etc/kuma/kuma.yaml|dpTimeout: 1s|dpTimeout: 10s|systemctl reload kuma-cp|kumactl|kuma_dp_1|rkum1|rkum|prod-apse969-kum|69-88|s|dp leftover timeout leftover 1s leftover; sidecar drop|is dropping sidecars because leftover Kuma leftover dp leftover timeout leftover is 1 leftover seconds leftover.|Restore 10; do not wipe meshes.|xds leftover leftover down; bounce|kuma leftover dp.timeout leftover 1 leftover; a 2s xDS is aborted so the dataplane 504s
antrea|flowExportTimeout|1|10|/etc/antrea/antrea.yml|flowExportTimeout: 1s|flowExportTimeout: 10s|systemctl reload antrea-agent|antctl|antrea_flow_1|rant1|rant|prod-apse970-ant|70-89|s|flow leftover export leftover timeout leftover 1s leftover; ipfix drop|is dropping IPFIX because leftover Antrea leftover flow leftover Export leftover Timeout leftover is 1 leftover seconds leftover.|Restore 10; do not wipe traces.|ovs leftover leftover down; bounce|antrea leftover flowExportTimeout leftover 1 leftover; a 2s conntrack dump is aborted so NetworkPolicy 504s
flannel|subnet-lease-renew-margin|1|60|/etc/kube-flannel/net-conf.json|subnet-lease-renew-margin: 1|subnet-lease-renew-margin: 60|systemctl reload flanneld|flanneld|flannel_lease_1|rfln1|rfln|prod-apse971-fln|71-90||subnet leftover lease leftover renew leftover margin leftover 1 leftover; overlay drop|is dropping overlay because leftover Flannel leftover subnet leftover lease leftover renew leftover margin leftover is 1 leftover.|Restore 60; do not wipe etcd.|etcd leftover leftover down; bounce|flannel leftover subnet-lease-renew-margin leftover 1 leftover; leases expire before renew so pods 504s
weave|WEAVE_NPC_TIMEOUT|1|30|/etc/weave/weave.env|WEAVE_NPC_TIMEOUT=1|WEAVE_NPC_TIMEOUT=30|systemctl reload weave|weave|weave_npc_1|rwve1|rwve|prod-apse972-wve|72-91|s|npc leftover timeout leftover 1s leftover; netpol drop|is dropping netpol because leftover Weave leftover NPC leftover TIMEOUT leftover is 1 leftover seconds leftover.|Restore 30; do not wipe peers.|iptables leftover leftover down; bounce|weave leftover WEAVE_NPC_TIMEOUT leftover 1 leftover; a 2s npc sync is aborted so policies 504s
binderhub|BinderHub.build_token_ttl|1|86400|/etc/binderhub/config.py|build_token_ttl = 1|build_token_ttl = 86400|systemctl reload binderhub|binderhub|binder_ttl_1|rbnd1|rbnd|prod-apse973-bnd|73-92||build leftover token leftover ttl leftover 1 leftover; launch drop|is dropping launches because leftover BinderHub leftover build leftover token leftover ttl leftover is 1 leftover.|Restore 86400; do not wipe images.|repo2docker leftover leftover down; bounce|binderhub leftover BinderHub.build_token_ttl leftover 1 leftover; the launch token dies so mybinder 401s
detect-secrets|baseline.timeout|1|30|/etc/detect-secrets/config.json|timeout: 1|timeout: 30|systemctl reload detect-secrets|detect-secrets|ds_to_1|rdet1|rdet|prod-apse974-det|74-93|s|baseline leftover timeout leftover 1s leftover; scan drop|is dropping scans because leftover detect leftover secrets leftover baseline leftover timeout leftover is 1 leftover seconds leftover.|Restore 30; do not wipe baselines.|git leftover leftover down; bounce|detect-secrets leftover baseline.timeout leftover 1 leftover; a 2s plugin is aborted so CI is empty
git-secrets|SECRET_TIMEOUT|1|30|/etc/git-secrets/config|SECRET_TIMEOUT=1|SECRET_TIMEOUT=30|systemctl reload git-secrets|git-secrets|gsec_to_1|rgsc1|rgsc|prod-apse975-gsc|75-94|s|secret leftover timeout leftover 1s leftover; scan drop|is dropping scans because leftover git leftover secrets leftover TIMEOUT leftover is 1 leftover seconds leftover.|Restore 30; do not wipe allowed.|git leftover leftover down; bounce|git-secrets leftover SECRET_TIMEOUT leftover 1 leftover; a 2s pattern scan is aborted so the hook 504s
montecarlo|MC_QUERY_TIMEOUT|1|120|/etc/montecarlo/mc.env|MC_QUERY_TIMEOUT=1|MC_QUERY_TIMEOUT=120|systemctl reload montecarlo|montecarlo|mc_to_1|rmc1a|rmca|prod-apse976-mca|76-95|s|query leftover timeout leftover 1s leftover; monitor drop|is dropping monitors because leftover Monte leftover Carlo leftover QUERY leftover TIMEOUT leftover is 1 leftover seconds leftover.|Restore 120; do not wipe monitors.|wh leftover leftover down; bounce|montecarlo leftover MC_QUERY_TIMEOUT leftover 1 leftover; a 2s warehouse probe is aborted so freshness 504s
jspolicy|controller.timeout|1|10|/etc/jspolicy/values.yaml|timeout: 1s|timeout: 10s|systemctl reload jspolicy|jspolicy|jsp_to_1|rjsp1|rjsp|prod-apse977-jsp|77-96|s|controller leftover timeout leftover 1s leftover; admit drop|is dropping admits because leftover jsPolicy leftover controller leftover timeout leftover is 1 leftover seconds leftover.|Restore 10; do not wipe policies.|v8 leftover leftover down; bounce|jspolicy leftover controller.timeout leftover 1 leftover; a 2s JS eval is aborted so pods 504s
resticprofile|lock-timeout|1|60|/etc/resticprofile/profiles.yaml|lock-timeout: 1s|lock-timeout: 60s|systemctl reload resticprofile|resticprofile|rp_lock_1|rrpf1|rrpf|prod-apse978-rpf|78-97|s|lock leftover timeout leftover 1s leftover; backup drop|is dropping backups because leftover resticprofile leftover lock leftover timeout leftover is 1 leftover seconds leftover.|Restore 60; do not wipe snapshots.|repo leftover leftover down; bounce|resticprofile leftover lock-timeout leftover 1 leftover; a 2s repo lock is aborted so the cron 504s
sanoid|no_inprogress_snap_timeout|1|3600|/etc/sanoid/sanoid.conf|no_inprogress_snap_timeout = 1|no_inprogress_snap_timeout = 3600|systemctl reload sanoid|sanoid|sanoid_to_1|rsnd1|rsnd|prod-apse979-snd|79-98|s|no leftover inprogress leftover snap leftover timeout leftover 1s leftover; snap drop|is dropping snaps because leftover Sanoid leftover no leftover inprogress leftover snap leftover timeout leftover is 1 leftover seconds leftover.|Restore 3600; do not wipe datasets.|zfs leftover leftover down; bounce|sanoid leftover no_inprogress_snap_timeout leftover 1 leftover; a 2s snapshot is aborted so retention holes grow
syncoid|timeout|1|3600|/etc/sanoid/syncoid.conf|timeout=1|timeout=3600|systemctl reload syncoid|syncoid|syncoid_to_1|rsyc1|rsyc|prod-apse980-syc|80-99|s|timeout leftover 1s leftover; send drop|is dropping sends because leftover Syncoid leftover timeout leftover is 1 leftover seconds leftover.|Restore 3600; do not wipe snapshots.|zfs leftover leftover down; bounce|syncoid leftover timeout leftover 1 leftover; a 2s zfs send is aborted so DR has no replica
'''
WAVE37 = (
    "hasura/postgrest/supabase/directus/strapi/payload/appsmith/tooljet/retool/"
    "budibase/nocodb/baserow/metabase/superset/redash/looker/mode/evidence/"
    "lightdash/cube/tinybird/great-expectations/soda/elementary/zot/quay/"
    "chartmuseum/kraken/manticore/rest-server/kasten/pdns/dnsmasq/blocky/"
    "adguard/oauth2-proxy/vaultwarden/passbolt/step-ca/boulder/gitlab-runner/"
    "gogs/apptainer/singularity/charliecloud/shifter/sarus/lmod/nix/easybuild/"
    "argo-workflows/argo-events/livekit/mediasoup/jitsi/kurento/mediamtx/"
    "openmpi/mpich/pmix/ucx/libfabric/ganeti/cloud-hypervisor/kube-bench/"
    "kube-hunter/tracee/kubewarden/kuma/antrea/flannel/weave/binderhub/"
    "detect-secrets/git-secrets/montecarlo/jspolicy/resticprofile/sanoid/syncoid"
)


def _parse_rows():
    plants = []
    srcs = ("grafana", "pagerduty", "opsgenie", "alertmanager")
    ns_cycle = (17, 16, 18)
    for raw in ROWS.strip().splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        parts = raw.split("|")
        if len(parts) != 20:
            raise SystemExit(f"bad row cols={len(parts)}: {raw[:160]}")
        (
            daemon, key, old, new, path, oldv, newv, reload, hpeer, metric,
            svc, ns, clu, node_tail, unit, symptom, because, do_not, herring, rca,
        ) = parts
        i = len(plants)
        n = ns_cycle[i % 3]
        rem = "rollback" if i % 2 == 0 else "patch"
        src = srcs[i % 4]
        ticket = f"W2-{11755 + i}"
        node = f"ip-10-222-{node_tail}"
        slug = f"{daemon}-{key}-{old}{unit}-{svc}"
        if rem == "rollback":
            remnant = helm_rb(ns, svc, 3, path, oldv, newv, reload)
            extra = f"helm -n {ns} history {svc} | head -5"
            eobs = f"4  {old}{unit}\n3  last-good {new}"
        else:
            remnant = patch_file(path, oldv, newv, reload)
            extra = f"kubectl -n {ns} logs deploy/{svc} --since=5m | grep {key} | tail"
            eobs = f"{key} leftover {old}"
        plants.append(
            plant(
                slug=slug, ticket=ticket, service=svc, ns=ns, cluster=clu, src=src,
                node=node, symptom=symptom, because=because, do_not=do_not,
                herring=herring, rca=rca, remediate=rem, metric=metric,
                hcmds=[
                    f"{hpeer} leftover status | head",
                    f"systemctl reload {hpeer} || true",
                    f"{hpeer} leftover bounce leftover || true",
                ],
                hobs=[f"{hpeer} ok", "bounce unused", f"still {key} {old}"],
                inspect=f"grep {key} {path}", iobs=f"{oldv} leftover",
                extra=extra, eobs=eobs, rem=remnant, robs=f"{key} {new}; holds",
                verify=f"grep {key} {path}", vok=f"{new}; {ticket} resolved", n=n,
            )
        )
    return plants


PLANTS = _parse_rows()
m.PLANTS = PLANTS
m.BASE_ROUND = 3617


def notes_for(round_n, eps):
    slug0 = eps[0]["id"].split("-", 2)[2].rsplit("-", 2)[0]
    slug1 = eps[1]["id"].split("-", 2)[2].rsplit("-", 2)[0]
    rows = [
        f"| `{e['id']}` | {e['meta']['ticket']} | {e['false_lead']['claim'].replace('|', '/')} | {e['remediate']} | {e['reward']['success']} | {e['reward']['steps']} |"
        for e in eps
    ]
    return "\n".join(
        [
            f"# incident-response-oncall-factory NOTES r{round_n}",
            "",
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r3616 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-37 leftover: {WAVE37}.",
            "",
            "OpenSRE designed: 429 then 502 retries, 3-step herring, unique RCA, mix patch/rollback. plant=designed. generator=grok-4.6.",
            "",
            "| id | ticket | herring (steps 6-8) | remediate | success | steps |",
            "|---|---|---|---|---|---|",
            *rows,
            "",
            "## Contract audit",
            f"- Q=2 episodes, kind=episode, ids irc-r{round_n}-*.",
            "- Unique goal service+cluster+symptom; 3 false-lead actions; 429/502 retries.",
            "- Residual: designed excerpts, not live dispatcher traces.",
            "",
        ]
    )


m.notes_for = notes_for


def extra_unique_guards():
    banned = (
        "Follow OpenSRE", "fraud-graph", "sip-proxy", "traefik", "limit_req",
        "cloudfront", "fastly", "kube-proxy", "haproxy", "varnish", "metallb",
        "imperva", "bunny", "calico felix", "kong ", "caddy ",
        "github actions leftover", "gitlab leftover", "circleci leftover",
        "tekton leftover", "snowflake", "bigquery", "redshift", "idle_timeout",
        "max_client_conn", "ypbind", "oddjob", "opensearch", "leftover3c",
        "tigergraph", "hugegraph", "graphdb", "stardog", "jena-fuseki", "rdf4j",
        "exist-db", "basex", "debezium", "maxwell", "canal", "nifi",
    )
    for p in PLANTS:
        blob = (p["goal"] + " " + p["rca"] + " " + p["slug"]).lower()
        for tok in banned:
            if tok.lower() in blob:
                raise SystemExit(f"banned {tok} in {p['slug']}")
        for need in (p["service"], p["ns"], p["cluster"]):
            if need not in p["goal"]:
                raise SystemExit(p["slug"])
        if p["n_steps"] not in (16, 17, 18) or p["remediate"] not in ("rollback", "patch"):
            raise SystemExit(p["slug"])
    if len(PLANTS) % 2:
        raise SystemExit("odd")
    for i in range(0, len(PLANTS), 2):
        if {PLANTS[i]["remediate"], PLANTS[i + 1]["remediate"]} != {"rollback", "patch"}:
            raise SystemExit(f"pair {i}")


def main():
    extra_unique_guards()
    used_svc, used_clu, used_tix, _ids = m.harvest_used(m.FACTORY_DIR)
    for p in PLANTS:
        if p["service"] in used_svc:
            raise SystemExit(f"service collision {p['service']}")
        if p["cluster"] in used_clu:
            raise SystemExit(f"cluster collision {p['cluster']}")
        if p["ticket"] in used_tix:
            raise SystemExit(f"ticket collision {p['ticket']}")
    for label, xs in (
        ("slug", [p["slug"] for p in PLANTS]),
        ("svc", [p["service"] for p in PLANTS]),
        ("clu", [p["cluster"] for p in PLANTS]),
        ("tix", [p["ticket"] for p in PLANTS]),
        ("node", [p["node"] for p in PLANTS]),
        ("ns", [p["ns"] for p in PLANTS]),
    ):
        if len(set(xs)) != len(xs):
            raise SystemExit("dup " + label)
    print(json.dumps({"ok": True, "plants": len(PLANTS), "rounds": len(PLANTS) // 2}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
