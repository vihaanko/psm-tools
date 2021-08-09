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
    if (portNumber and protocol == 'icmp'):
        return (False, "Cannot put port number for icmp protocol")

    if (protocol not in ['tcp', 'udp', 'icmp']):
        return (False, "Your protocol must be tcp, udp, or icmp")

    if (protocol == 'tcp' or protocol == 'udp'):
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
        while (rule in policy.spec.rules):
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
parser.add_argument('--add', default=False, action="store_true")
parser.add_argument('--delete', default=False, action="store_true")
parser.add_argument('--modify', default=False, action="store_true")
parser.add_argument('--name', type=str, required=True, help = 'Name of policy to preform commmand on')
parser.add_argument('--action', choices=['permit', 'deny', 'reject'], type=str, required=True, help = 'Action for rule (permit, deny, reject)')
parser.add_argument('--src_ip', type=str, required=True, help = 'Source ip address for rule')
parser.add_argument('--dest_ip', type=str, required=True, help = 'Destination ip address for rule')
parser.add_argument('--port', type=str, required=True, help = '(protocol/port number) for rule')
parser.add_argument('--new_action', type=str, required=False, help = 'New action for rule (permit, deny, reject)')
parser.add_argument('--new_src_ip', type=str, required=False, help = 'New source ip address for rule')
parser.add_argument('--new_dest_ip', type=str, required=False, help = 'New destination ip address for rule')
parser.add_argument('--new_port', type=str, required=False, help = 'New (protocol/port number) for rule')
args = parser.parse_args()

# If command is modify, then check if new values were specified
# and set unspecified new values to old values

if (args.modify):
    if ((not args.new_action) and (not args.new_src_ip) and (not args.new_dest_ip) and (not args.new_port)):
        sys.exit("No changes made because no new values specified...")
    if (not args.new_action):
        args.new_action = args.action
    if (not args.new_src_ip):
        args.new_src_ip = args.src_ip
    if (not args.new_dest_ip):
        args.new_dest_ip = args.dest_ip
    if (not args.new_port):
        args.new_port = args.port

    (nProtocol, nPortNumber) = portRead(args.new_port)
    (nProtocolValid, error) = portValid(nProtocol, nPortNumber)
    if (nProtocolValid == False):
        sys.exit(error)
else:
    if ((args.new_action) or (args.new_src_ip) or (args.new_dest_ip) or (args.new_port)):
        sys.exit("new values of [src_ip, dest_ip, port, action] are not required when adding a rule")

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
        print("Policy doesn't exist. Please choose the policy out of the following:")
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
                      from_ip_addresses=[args.src_ip],
                      proto_ports=[inputPort],
                      to_ip_addresses=[args.dest_ip])

# Different conditions based on different commands:
# For delete, the program calls deleteRule
# For add, the program calls addRule. addRule will fail when the policy is empty, so addFirstRule is called.
# For modify, the program creates a new port and new rule based on the inputs for the new rule. It then calls updateRule.
if (args.delete):
    try:
        status = deleteRule(rule, oldPolicy, args.name)
        print(status)
    except Exception as ex:
        print("Unable to delete.")
        print(handleErrorResponse(ex.status))
elif (args.add):
    try:
        status = addRule(rule, oldPolicy, args.name)
        print(status)
    except Exception as ex:
        print("Unable to add.")
        print(handleErrorResponse(ex.status))
elif (args.modify):
    try:
        nInputPort = SecurityProtoPort(ports=nPortNumber, protocol=nProtocol)
        nRule = SecuritySGRule(action=args.new_action,
                               from_ip_addresses=[args.new_src_ip],
                               proto_ports=[nInputPort],
                               to_ip_addresses=[args.new_dest_ip])
        updateRule(rule, nRule, oldPolicy, args.name)
    except Exception as ex:
        print("Unable to modify.")
        print(handleErrorResponse(ex.status))

