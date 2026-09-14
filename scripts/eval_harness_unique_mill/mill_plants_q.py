"""Unique eval-harness leftover plants r465+. Compact leftover table."""

from mill_plants import PAIRS
from mill_plants_p import pair

ROWS = [
    ("maas-image-stale", "maas-eval", "foreman-pxe-stale", "foremanpxe-eval",
     "dual-hold-9", "rain-hold-15", "maas image leftover", "foreman pxe leftover", "pxe"),
    ("cobbler-profile-stale", "cobbler-eval", "ironic-image-stale", "ironic-eval",
     "flash-hold-16", "promo-hold-15", "cobbler profile leftover", "ironic image leftover", "pxe"),
    ("netbox-device-stale", "netbox-eval", "nautobot-device-stale", "nautobot-eval",
     "gift-hold-15", "bundle-hold-14", "netbox device leftover", "nautobot device leftover", "dcim"),
    ("phpipam-subnet-stale", "phpipam-eval", "infoblox-zone-stale", "infoblox-eval",
     "loyalty-hold-13", "cancel-hold-13", "phpipam subnet leftover", "infoblox zone leftover", "dcim"),
    ("zabbix-template-stale", "zabbix-eval", "nagios-cfg-stale", "nagios-eval",
     "tax-hold-12", "sla-hold-11", "zabbix template leftover", "nagios cfg leftover", "mon"),
    ("icinga-zone-stale", "icinga-eval", "sensu-check-stale", "sensu-eval",
     "membership-hold-10", "after-hold-12", "icinga zone leftover", "sensu check leftover", "mon"),
    ("prometheus-rule-stale", "promrule-eval", "alertmanager-route-stale", "amroute-eval",
     "sku-hold-8", "rain-void-10", "prom rule leftover", "am route leftover", "mon"),
    ("thanos-rule-stale", "thanosrule-eval", "cortex-ruler-stale", "cortex-eval",
     "flash-void-9", "promo-void-10", "thanos rule leftover", "cortex ruler leftover", "mon"),
]

for i, row in enumerate(ROWS):
    PAIRS.append(pair(*row[:8], i * 2, row[8]))
