#!/usr/bin/python3

import os
from apigroups.client.apis import ClusterV1Api, TelemetryQueryV1Api, WorkloadV1Api, NetworkV1Api, SearchV1Api
from apigroups.client import configuration, api_client
import warnings
from utils import *
from utils.workload_utils import getDscFromWorkload 
import sys
import json
import argparse
from apigroups.client.model.telemetry_query_metrics_query_spec import TelemetryQueryMetricsQuerySpec
from apigroups.client.model.telemetry_query_metrics_query_list import TelemetryQueryMetricsQueryList
warnings.simplefilter("ignore")


HOME = os.environ['HOME']

parser = argparse.ArgumentParser()
parser.add_argument("action", help = "the metric by which the dscs should be searched", choices=["cps", "version", "workloads", "alerts"])
parser.add_argument("operator", help = "the operator to compare the dsc's to the value", choices=["gt", "lt", "eq", "ge", "le"])
parser.add_argument("value", help="the value of the metric that is being searched by")
args = parser.parse_args()


# This is the main switch, and will pick the fuction called based on the atribute given by the user. It is implemented in a map to ease adding and removing features
def metrics(arg):

    metricmap = {
        "cps" : find_cps,
        "version" : find_version,
        "workloads" : find_workload,
        "alerts" : find_alert
    }
    execfunc = metricmap.get(arg, lambda: print("Invalid Attribute"))
    execfunc(args.operator, args.value)


configuration = configuration.Configuration(
    psm_config_path=HOME+"/.psm/config.json",
    interactive_mode=True
)
configuration.verify_ssl = False

# These create the instances of the API, for ease of access in the functions
client = api_client.ApiClient(configuration)
api_instance = ClusterV1Api(client)
response = api_instance.list_distributed_service_card()
telemetry_instance = TelemetryQueryV1Api(client)
workload_instance = WorkloadV1Api(client)
network_instance = NetworkV1Api(client)
search_instance = SearchV1Api(client)

# This function will list the DSC's whose connections per second meet the operator and value passed in by the user
def find_cps(oper, val):
    print("List of DSC's that meet query:")
    for dsc in response.items:
            query_response = telemetry_instance.post_metrics(
                {
                "queries": [
                    {
                     "kind": "FteCPSMetrics",
                     "selector": {
                        "requirements": [
                        {
                            "key": "reporterID",
                            "operator": "in",
                            "values": [
                            dsc.spec.id
                            ]
                        }
                        ]
                    },
                        "fields": [
                        "ConnectionsPerSecond"
                    ],
                    "function": "last"
                    }
                ]
            }, _check_return_type=False)
            if (compare(query_response.results[0]["series"][0]["values"][0][1], int(val), oper)):
                print(dsc.spec.id + " has " + str(query_response.results[0]["series"][0]["values"][0][1]) + " CPS")


# This function finds all of the DSC's that are of the same version as the query
def find_version(oper, val):   
    print("List of DSC's that meet query:")
    for dsc in response.items:
        vers = dsc.status.system_info.bios_info.version
        if (vers == val):
            print (dsc.spec.id)


def find_alert(oper, val):
    dscdict = {}

    for dsc in response.items:
        dscdict[dsc.meta.name] = 0

    search_response = search_instance.post_query({
            "mode": "full",
            "query": {
                "kinds": [
                    "Alert"
                ]
            },
        "aggregate": False
    }, _check_return_type=False)

    for entry in search_response.entries:
        if (entry["object"]["status"]["object-ref"]["kind"] == 'DistributedServiceCard'):
            dscdict[entry["object"]["status"]["object-ref"]["name"]] += 1

    print("List of DSC's that meet query:")
    for dsc in dscdict.keys():
        if (compare(dscdict[dsc], int(val), oper)):
            print(dsc + " has " + str(dscdict[dsc]) + " alerts(s)")



# This function lists all of the DSC's whos number of workloads matches the query
# This function uses a dict of [DSC, int], and incremets the integer for every workload that matches the DSC
# It finally iterates through the dict and checks which DSC's match the query
def find_workload(oper, val):
    dscdict = {}

    for dsc in response.items:
        dscdict[dsc.spec.id] = 0
    workload_response = workload_instance.list_workload("default")
    for item in workload_response.items:
        for dsc in getDscFromWorkload(client, "default", item.meta.name, forceName=True)[1]:
            dscdict[dsc] += 1
    for dsc in dscdict.keys():
        if (compare(dscdict[dsc], int(val), oper)):
            print(dsc + " has " + str(dscdict[dsc]) + " workload(s)")

# This function compares two values based on the operator
def compare (a, b, oper):
    if (oper == "gt"):
        return (a > b)
    elif (oper == "lt"):
        return (a < b)
    elif (oper == "eq"):
        return (a == b)
    elif (oper == "le"):
        return (a <= b)
    elif (oper == "ge"):
        return (a >= b)
    else:
        print("Invalid Operator")
        return False

# This calls the metrics function, which will choose the function to be called based on the command line arg
metrics(args.action)
            
