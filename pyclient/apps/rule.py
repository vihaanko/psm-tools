#!/usr/bin/python3

import os
import sys
import argparse
import warnings
from apigroups.client.apis import SecurityV1Api
from apigroups.client import configuration, api_client
from apigroups.client.models import ApiObjectMeta, SecurityNetworkSecurityPolicySpec, SecurityNetworkSecurityPolicy
from apigroups.client.models import SecuritySGRule
from apigroups.client.models import SecurityProtoPort

warnings.simplefilter("ignore")

HOME = os.environ['HOME']

# Configure
configuration = configuration.Configuration(
    psm_config_path=HOME+"/.psm/config.json",
    interactive_mode=True
)
configuration.verify_ssl = False

# Create API Instances
client = api_client.ApiClient(configuration)
api_instance = SecurityV1Api(client)


# Function to seperate protocol from port in port input
def portRead(port):
    protocol = ""
    portNumber = ""
    for c in port:
        for i in c.split():
            if (i.isdigit()):
                portNumber += i
            elif (i != "/"):
                protocol += i
    return (protocol, portNumber)


# Function to validate protocol
def portValid(protocol, portNumber):
    if (portNumber and protocol == "icmp"):
        return (False, "Cannot put port number for icmp protocol")

    if (protocol != "tcp" and protocol != "udp" and protocol != "icmp"):
        return (False, "Your protocol must be tcp, udp, or icmp")

    if (protocol == "tcp" or protocol == "udp"):
        port = int(portNumber)
        if (port <= 0 or port >= 65535):
            return (False, "Invalid port number. Port number has to be between 0 and 65535.")

    return (True, "")

# Adds rule to policy by using previous rules and appending new rule to array of rules then updating the policy.
# If rules not present in policy, program adds first rule to policy.
def addRule(rule, policy, name):
    if (hasattr(policy.spec, "rules")):
        policy.spec.rules.append(rule)
        api_instance.update_network_security_policy("default", name, policy)
        return ("Rule appended to policy!")
    else:
        policy = SecurityNetworkSecurityPolicy(meta=ApiObjectMeta(name=name),
                                               spec=SecurityNetworkSecurityPolicySpec(rules=[rule], attach_tenant=True))
        api_instance.update_network_security_policy("default", name, policy)
        return ("First rule added in policy.")

# Deletes rule by using previous rules and removing the rule which is to be deleted. The policy is then updated
def deleteRule(rule, policy, name):
    exists = False
    if (hasattr(policy.spec, "rules")):
        exists = rule in policy.spec.rules

    if (exists == True):
        policy.spec.rules.remove(rule)
        api_instance.update_network_security_policy("default", name, policy)
        return("Rule deleted!")
    else:
        return("Rule doesn't exist. Double check your inputs!")

# Updates rule by finding old rule and replacing it with new rule. Policy is then updated
def updateRule(rule, newRule, policy, name):
    exists = False
    if (hasattr(policy.spec, "rules")):
        exists = rule in policy.spec.rules

    if (exists == True):
        newRules = policy.spec.rules
        newRules[newRules.index(rule)] = newRule
        newPolicy = SecurityNetworkSecurityPolicy(meta=ApiObjectMeta(name=name),
                                               spec=SecurityNetworkSecurityPolicySpec(rules=newRules, attach_tenant=True))
        api_instance.update_network_security_policy("default", name, newPolicy)
        print("Rule updated!")
    else:
        print("Rule doesn't exist. Double check your inputs!")

def handleErrorResponse(response):
    if (response == 404):
        return "Connection error"
    elif (response == 400):
        return "Bad Request"
    elif (response == 401):
        return "Unauthorized"
    elif (response == 409):
        return "Conflict"
    elif (response == 412):
        return "Precondition failed"
    elif (response == 500):
        return "Internal server error"
    elif (response == 501):
        return "Not implemented"

# Command line processing
parser = argparse.ArgumentParser()
parser.add_argument('--command', choices=['add', 'delete', 'modify'], type=str, required=True)
parser.add_argument('--name', type=str, required=True)
parser.add_argument('--action', choices=['permit', 'deny', 'reject'], type=str, required=True)
parser.add_argument('--ip', type=str, required=True)
parser.add_argument('--port', type=str, required=True)
parser.add_argument('--nAction', type=str, required=False)
parser.add_argument('--nIp', type=str, required=False)
parser.add_argument('--nPort', type=str, required=False)
args = parser.parse_args()

# If command is modify, then check if new values were specified
# and set unspecified new values to old values

if (args.command == "modify"):
    if ((not args.nAction) and (not args.nIp) and (not args.nPort)):
        sys.exit("No changes made because no new values specified...")
    if (not args.nAction):
        args.nAction = args.action
    if (not args.nIp):
        args.nIp = args.ip
    if (not args.nPort):
        args.nPort = args.port

    (nProtocol, nPortNumber) = portRead(args.nPort)
    (nProtocolValid, error) = portValid(nProtocol, nPortNumber)
    if (nProtocolValid == False):
        sys.exit(error)
else:
    if ((args.nAction) or (args.nIp) or (args.nPort)):
        sys.exit("nAction, nIp, and nPort are only valid for the modify command")

# Check whether or not the user put port and protocol inputs correctly.
(protocol, portNumber) = portRead(args.port)
(protocolValid, error) = portValid(protocol, portNumber)
if (protocolValid == False):
    sys.exit(error)

# Gets the old policy in order to make changes in functions.
# If policy doesn't exist, program lists all existing policies
try:
    oldPolicy = api_instance.get_network_security_policy("default", args.name)
except Exception as ex:
    if (ex.status == 404):
        print("Policy doesn't exist. Please choose the policy out of the following or use -f to create one if desired:")
        policies = api_instance.list_network_security_policy("default")
        for realPolicy in policies.items:
            print(realPolicy.meta.name)
        sys.exit()
    else:
        sys.exit("Unable to connect to psm; this could be due to invalid psm IP address, connectivity issue, or a psm being down")

# Create Instance to create port
inputPort = SecurityProtoPort(ports=portNumber, protocol=protocol)

# Make rule instance based on inputs.
# It is used to look for a rule or add a rule in a policy
rule = SecuritySGRule(action=args.action,
                      from_ip_addresses=[args.ip],
                      proto_ports=[inputPort],
                      to_ip_addresses=[args.ip])

# Different conditions based on different commands:
# For delete, the program calls deleteRule
# For add, the program calls addRule. addRule will fail when the policy is empty, so addFirstRule is called.
# For modify, the program creates a new port and new rule based on the inputs for the new rule. It then calls updateRule.
if (args.command == "delete"):
    try:
        status = deleteRule(rule, oldPolicy, args.name)
        print(status)
    except Exception as ex:
        print("Unable to delete.")
        print(handleErrorResponse(ex.status))
elif (args.command == "add"):
    try:
        status = addRule(rule, oldPolicy, args.name)
        print(status)
    except Exception as ex:
        print("Unable to add.")
        print(handleErrorResponse(ex.status))
elif (args.command == "modify"):
    try:
        nInputPort = SecurityProtoPort(ports=nPortNumber, protocol=nProtocol)
        nRule = SecuritySGRule(action=args.nAction,
                               from_ip_addresses=[args.nIp],
                               proto_ports=[nInputPort],
                               to_ip_addresses=[args.nIp])
        updateRule(rule, nRule, oldPolicy, args.name)
    except Exception as ex:
        print("Unable to modify.")
        print(handleErrorResponse(ex.status))

