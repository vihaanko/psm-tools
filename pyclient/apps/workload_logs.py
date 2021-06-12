from datetime import date
import os
from apigroups.sysruntime import DistributedservicecardsV1Api
from apigroups.sysruntime import configuration, api_client
from apigroups.sysruntime import SysruntimeConnectionRequest
from apigroups.sysruntime.client.model.api_list_watch_options import ApiListWatchOptions

from apigroups.workload import WorkloadV1Api
from apigroups.workload import api_client as w_api_client
import warnings
warnings.simplefilter("ignore")

HOME = os.environ['HOME']

configuration = configuration.Configuration(
    psm_config_path=HOME+"/.psm/config.json",
    interactive_mode=True
)
configuration.verify_ssl = False

client = api_client.ApiClient(configuration)
dsc_api = DistributedservicecardsV1Api(client)

wclient = w_api_client.ApiClient(configuration)
workload_api = WorkloadV1Api(wclient)

workload_interface_ips = set()

response = workload_api.get_workload('default', 'orch1--vm-48')
for interface in response.status.interfaces:
    ips_set = set(interface.ip_addresses)
    workload_interface_ips.update(ips_set)

print(workload_interface_ips)

dscs = response.status.interfaces[0].dsc_interfaces
for dsc in dscs:
    body = SysruntimeConnectionRequest(dsc_name=dsc, list=ApiListWatchOptions(name="temp", max_results=50))
    response = dsc_api.post_query_connection(dsc, body)
    for item in response.items:
        flow_info = item.spec.initiator_flow.flow_key.ipv4

        protocol = flow_info.protocol
        dest_ip = flow_info.destination
        src_ip = flow_info.source
        if protocol == 'TCP' or protocol == 'UDP':
            src_port = flow_info.tcp_udp["source_port"] 
            dest_port = flow_info.tcp_udp["destination_port"]
            print("FLOW:", protocol, src_ip+":"+src_port, "to", dest_ip+":"+dest_port)
        else:
            print("FLOW:", protocol, src_ip, "to", dest_ip)
        