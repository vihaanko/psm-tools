import os
import sys
import argparse
import warnings
from apigroups.client.apis import MonitoringV1Api
from apigroups.client.apis import WorkloadV1Api
from apigroups.client import configuration, api_client
from apigroups.client.models import ApiObjectMeta, MonitoringMirrorExportConfig, MonitoringMirrorCollector, MonitoringMirrorSessionSpec, MonitoringMirrorSession, MonitoringMatchRule, MonitoringMatchSelector, MonitoringMirrorSessionStatus

warnings.simplefilter("ignore")

HOME = os.environ['HOME']

# Configure
configuration = configuration.Configuration(
    psm_config_path=HOME+"/.psm/config.json",
    interactive_mode=True
)
configuration.verify_ssl = False


#Take in parameters
parser = argparse.ArgumentParser()
parser.add_argument('--enable', default=False, action="store_true")
parser.add_argument('--disable', default=False, action="store_true")
parser.add_argument('--frm', '--from', default=False, action="store_true")
parser.add_argument('--to', default=False, action="store_true")
#parser.add_argument('--workload_name', type=str, required=True, help = 'Name of workload')
parser.add_argument('workload_name', help = 'Name of workload')
parser.add_argument('--mirror_name', type=str, required=True, help = 'Name of mirror session')
parser.add_argument('--dest', '--collector_destination', type=str, required=True, help = 'Collector Destination IP')
args = parser.parse_args()

# Create API Instances
client = api_client.ApiClient(configuration)
api_instance = MonitoringV1Api(client)
workload_instance = WorkloadV1Api(client)

#Check wether or not the mirror session already exists with the given name
mirror_session_exists = True
try:
    mirror_session = api_instance.get_mirror_session("default", args.mirror_name)
except Exception as ex:
    if (ex.status == 404):
        mirror_session_exists = False

#Get IP from workload
workload = workload_instance.get_workload("default", args.workload_name)
ip = workload.spec.interfaces[0].ip_addresses[0]
print(ip)

# print(api_instance.list_mirror_session("default"))

#Create different rules based on wether param is from or to
#Create different mirror session instances based on enable or disable param
if (args.frm):
    rule = [MonitoringMatchRule(source=MonitoringMatchSelector(ip_addresses=[ip]))]
elif (args.to):
    rule = [MonitoringMatchRule(source=MonitoringMatchSelector(ip_addresses=[ip]))]
if (args.enable):
    mirrorSesh = MonitoringMirrorSession(
        meta=ApiObjectMeta(name=args.mirror_name),
        spec=MonitoringMirrorSessionSpec(collectors=[MonitoringMirrorCollector(export_config=MonitoringMirrorExportConfig(destination=args.dest),
                                              type="erspan_type_3")], disabled = False, match_rules = rule))
elif (args.disable):
    mirrorSesh = MonitoringMirrorSession(
        meta=ApiObjectMeta(name=args.mirror_name),
        spec=MonitoringMirrorSessionSpec(collectors=[MonitoringMirrorCollector(export_config=MonitoringMirrorExportConfig(destination=args.dest),
                                                  type="erspan_type_3")], disabled = True, match_rules=[MonitoringMatchRule(source=MonitoringMatchSelector(ip_addresses=[ip]))]))
else:
    sys.exit("Please put enable or disable tag")

# If given mirror session already exists then update it, else add a new one
if (mirror_session_exists):
    try:
        print("Mirror session updated")
        api_instance.update_mirror_session("default", args.mirror_name, mirrorSesh)
    except Exception as ex:
        print(ex)
else:
    try:
        api_instance.add_mirror_session("default", mirrorSesh)
        print("Mirror session created")
    except Exception as ex:
        print(ex)
    print(api_instance.get_mirror_session("default", args.mirror_name))