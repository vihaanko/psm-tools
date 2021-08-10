import os
import argparse
import warnings
from apigroups.client.apis import WorkloadV1Api
from apigroups.client.apis import SecurityV1Api
from apigroups.client import configuration, api_client
from ipaddress import ip_network


warnings.simplefilter("ignore")

HOME = os.environ['HOME']

# Configure
configuration = configuration.Configuration(
    psm_config_path=HOME+"/.psm/config.json",
    interactive_mode=True
)
configuration.verify_ssl = False

def inRange(ipaddress, ipRange):
    a = ip_network(ipRange)
    b = ip_network(ipaddress)
    if(b.subnet_of(a)):
        return True

def printRule(rule):
    ports = []
    for i in rule.proto_ports:
        ports.append(i.ports)
    return str(rule.action) + " " + str(rule.from_ip_addresses) + " to " + str(rule.to_ip_addresses) + " ports: " + str(ports)

# Create API Instances
client = api_client.ApiClient(configuration)
security_instance = SecurityV1Api(client)
workload_instance = WorkloadV1Api(client)


# Set default variable
setDefault = "default"

parser = argparse.ArgumentParser()
parser.add_argument('--name', type=str, required=True)
args = parser.parse_args()

workload = workload_instance.get_workload(setDefault, args.name)
# print(workload)

policy_list = security_instance.list_network_security_policy(setDefault)
# print(policy_list)
policiesInRange = []


# Iterate over workload interfaces
for interface in workload.spec.interfaces:
    # Iterate over ip addresses of each interface
    for interface_ip in interface.ip_addresses:
        # Iterate over policies
        for policy in policy_list.items:
            policy_match = False
            rule_num = 0
            # Iterate over rules in policy
            for rule in policy.spec.rules:
                rule_num += 1
                rule_match = False

                # Iterate over the "from" ip addresses of each rule
                for frm in rule.from_ip_addresses:
                    if (inRange(interface_ip, frm)):
                        rule_match = True
                        if (policy_match == False):
                            policiesInRange.append("Policy: " + str(policy.meta.name))
                            policy_match = True

                # Iterate over the "to" ip addresses of each rule
                for to in rule.to_ip_addresses:
                    if (inRange(interface_ip, to)):
                        rule_match = True
                        if (policy_match == False):
                            policiesInRange.append("Policy: " + str(policy.meta.name))
                            policy_match = True
                if (rule_match == True):
                    print(rule)
                    policiesInRange.append("Rule#" + str(rule_num) + ": " + printRule(rule))


if (len(policiesInRange) > 0):
    for i in policiesInRange:
        print(i)
else:
    print("No policies include your ip address.")




