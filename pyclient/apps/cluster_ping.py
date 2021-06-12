#!/usr/bin/python3

import os
from apigroups.client.apis import ClusterV1Api
from apigroups.client import configuration, api_client
import warnings
warnings.simplefilter("ignore")

HOME = os.environ['HOME']

configuration = configuration.Configuration(
    psm_config_path=HOME+"/.psm/config.json",
    interactive_mode=True
)
configuration.verify_ssl = False

client = api_client.ApiClient(configuration)
api_instance = ClusterV1Api(client)
response = api_instance.get_cluster()

# Cluster Uptime
uptime = (response.status.current_time - response.meta.creation_time)
uptime_total_sec = uptime.total_seconds()
uptime_days = int(uptime_total_sec//(24*60*60))
uptime_hours = int(uptime_total_sec % (24*60*60))//(60*60)
uptime_minutes = int(uptime_total_sec % (60*60))//60
uptime_sec = int(uptime_total_sec % 60)

print("\nCluster Uptime: {}d {}h {}m {}s".format(
    uptime_days, uptime_hours, uptime_minutes, uptime_sec))
print("Cluster Condition: ", response.status.conditions[0].type)

nodes_unhealthy = False
for node in response.status.quorum_status.members:
    node_health = node.conditions[0].type
    if node_health != "healthy":
        nodes_unhealthy = True
        print("\tCluster Quorum Node: ", node.name)
        print("\tCluster Quorum Status: ", node.conditions[0].type)
if not nodes_unhealthy:
    print("\n\tAll nodes are healthy\n")

# DSCs and health
response = api_instance.list_distributed_service_card()

for dsc in response.items:
    if "conditions" in dsc.status and len(dsc.status.conditions)>0:
        print("\tDSC " + dsc.meta.name + " is ", dsc.status.conditions[0].type)
    else:
        print("\tDSC " + dsc.meta.name + " health cannot be determined.")
