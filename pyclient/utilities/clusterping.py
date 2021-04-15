import warnings
warnings.simplefilter("ignore")
from apigroups.cluster.openapi_client import configuration, api_client
from apigroups.cluster.openapi_client.api import cluster_v1_api
import os
from datetime import date
HOME = os.environ['HOME']

configuration = configuration.Configuration(
    psm_config_path=HOME+"/.psm/config.json"
)
configuration.verify_ssl = False

client = api_client.ApiClient(configuration)
api_instance = cluster_v1_api.ClusterV1Api(client)

response = api_instance.get_cluster()

print("Cluster Condition: ", response["status"]["conditions"][0]["type"])
for i in response["status"]["quorum_status"]["members"]:
    node_health = i["conditions"][0]["type"]
    if node_health != "healthy":
        print("\tCluster Quorum Node: ", i["name"])
        print("\tCluster Quorum Status: ", i["conditions"][0]["type"])
# print("\tCluster Leader: ", response["status"]["leader"])

uptime = (response["status"]["current_time"] - response["meta"]["creation_time"])
uptime_sec = uptime.total_seconds()
uptime_days = uptime_sec%(24*60*60)
uptime_hours = uptime_sec%(24*60)
print(uptime_sec)

# print("dscs and healthy?")

