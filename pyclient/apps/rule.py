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
from utils.rule_utils import protoPortRead
from utils.rule_utils import protoPortValid
from utils.error_utils import handleErrorResponse

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

# Adds rule to policy by using previous rules and appending new rule to array of rules then updating the policy.
# If rules not present in policy, program adds first rule to policy.
def addRule(rule, policy, name):
    if (hasattr(policy.spec, "rules")):
        if (rule in policy.spec.rules):
            sys.exit("Rule already exists")
        policy.spec.rules.append(rule)
        api_instance.update_network_security_policy(args.tenant, name, policy)
        return ("Rule appended to policy!")
    else:
        policy = SecurityNetworkSecurityPolicy(meta=ApiObjectMeta(name=name),
                                               spec=SecurityNetworkSecurityPolicySpec(rules=[rule], attach_tenant=True))
        api_instance.update_network_security_policy(args.tenant, name, policy)
        return ("First rule added in policy.")

# Deletes rule by using previous rules and removing the rule which is to be deleted. The policy is then updated
def deleteRule(rule, policy, name):
    exists = False
    if (hasattr(policy.spec, "rules")):
        exists = rule in policy.spec.rules

    if (exists == True):
        while (rule in policy.spec.rules):
            policy.spec.rules.remove(rule)
        api_instance.update_network_security_policy(args.tenant, name, policy)
        return("Rule deleted!")
    else:
        return("Unable to delete a rule: rule not found")

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
        api_instance.update_network_security_policy(args.tenant, name, newPolicy)
        print("Rule updated!")
    else:
        print("Rule doesn't exist. Double check your inputs!")

class UniqueStore(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        if getattr(namespace, self.dest, self.default) is not self.default:
            parser.error(option_string + " appears several times.")
        setattr(namespace, self.dest, values)

# Command line processing
parser = argparse.ArgumentParser()
parser.add_argument('command', choices = ['add', 'update', 'delete'], help = 'Command options are add, update and delete')
parser.add_argument('--tenant', type=str, default = "default", help = 'Tenant')
parser.add_argument('--name', type=str, required=True, action = UniqueStore, help = 'Name of policy to preform commmand on')
parser.add_argument('--action', choices=['permit', 'deny', 'reject'], type=str, required=True, action = UniqueStore, help = 'Action for rule (permit, deny, reject)')
parser.add_argument('--src_ip', type=str, required=True, action = UniqueStore, help = 'Source ip address for rule')
parser.add_argument('--dest_ip', type=str, required=True, action = UniqueStore, help = 'Destination ip address for rule')
parser.add_argument('--proto_port', type=str, required=True, action = UniqueStore, help = '(protocol/port number) for rule')
parser.add_argument('--new_action', type=str, required=False, action = UniqueStore, help = 'New action for rule (permit, deny, reject)')
parser.add_argument('--new_src_ip', type=str, required=False, action = UniqueStore, help = 'New source ip address for rule')
parser.add_argument('--new_dest_ip', type=str, required=False, action = UniqueStore, help = 'New destination ip address for rule')
parser.add_argument('--new_proto_port', type=str, required=False, action = UniqueStore, help = 'New (protocol/port number) for rule')
args = parser.parse_args()

# If command is update, then check if new values were specified
# and set unspecified new values to old values

if (args.command == 'update'):
    if ((not args.new_action) and (not args.new_src_ip) and (not args.new_dest_ip) and (not args.new_proto_port)):
        sys.exit("Require new values of [ip, action, port] for update operations")
    if (not args.new_action):
        args.new_action = args.action
    if (not args.new_src_ip):
        args.new_src_ip = args.src_ip
    if (not args.new_dest_ip):
        args.new_dest_ip = args.dest_ip
    if (not args.new_proto_port):
        args.new_proto_port = args.proto_port

    (nProtocol, nPortNumber) = protoPortRead(args.new_proto_port)
    (nProtocolValid, error) = protoPortValid(nProtocol, nPortNumber)
    if (nProtocolValid == False):
        sys.exit(error)
else:
    if ((args.new_action) or (args.new_src_ip) or (args.new_dest_ip) or (args.new_proto_port)):
        sys.exit("new values of [src_ip, dest_ip, port, action] are not required when adding a rule")

# Check whether or not the user put port and protocol inputs correctly.
(protocol, portNumber) = protoPortRead(args.proto_port)
(protocolValid, error) = protoPortValid(protocol, portNumber)
if (protocolValid == False):
    sys.exit(error)

# Gets the old policy in order to make changes in functions.
# If policy doesn't exist, program lists all existing policies
try:
    oldPolicy = api_instance.get_network_security_policy(args.tenant, args.name)
except Exception as ex:
    if (ex.status == 404):
        print("Policy doesn't exist. Please choose the policy out of the following:")
        policies = api_instance.list_network_security_policy(args.tenant)
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
# For update, the program creates a new port and new rule based on the inputs for the new rule. It then calls updateRule.
if (args.command == 'delete'):
    try:
        status = deleteRule(rule, oldPolicy, args.name)
        print(status)
    except Exception as ex:
        print("Unable to delete.")
        print(handleErrorResponse(ex.status))
elif (args.command == 'add'):
    try:
        status = addRule(rule, oldPolicy, args.name)
        print(status)
    except Exception as ex:
        print("Unable to add.")
        print(handleErrorResponse(ex.status))
elif (args.command == 'update'):
    try:
        nInputPort = SecurityProtoPort(ports=nPortNumber, protocol=nProtocol)
        nRule = SecuritySGRule(action=args.new_action,
                               from_ip_addresses=[args.new_src_ip],
                               proto_ports=[nInputPort],
                               to_ip_addresses=[args.new_dest_ip])
        updateRule(rule, nRule, oldPolicy, args.name)
    except Exception as ex:
        print("Unable to update.")
        print(handleErrorResponse(ex.status))

