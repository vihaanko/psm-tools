#!/usr/bin/python3

import os
from apigroups.client.apis import SecurityV1Api
from apigroups.client import configuration, api_client
from apigroups.client.models import ApiObjectMeta, SecurityNetworkSecurityPolicySpec, SecurityNetworkSecurityPolicy
from apigroups.client.models import SecuritySGRule
from apigroups.client.models import SecurityProtoPort
import warnings
import argparse
import sys
from utils.rule_utils import portRead
from utils.rule_utils import portValid

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

# Read Command Line Args
parser = argparse.ArgumentParser()
parser.add_argument('--action', choices=['permit', 'deny', 'reject'], type=str, required=True)
parser.add_argument('--force', default=False, action="store_true")
parser.add_argument('--patch', default=False, action="store_true")
parser.add_argument('--policy_name', type=str, required=True)
parser.add_argument('--from_ip', type=str, required=True)
parser.add_argument('--to_ip', type=str, required=True)
parser.add_argument('--port', type=str, required=True)
args = parser.parse_args()

#Create default variable
default = "default"

(protocol, portNumber) = portRead(args.port)
(protocolValid, error) = portValid(protocol, portNumber)
if (protocolValid == False):
    sys.exit(error)

# Create Instance to create port
if (protocolValid):
    inputPort = SecurityProtoPort(ports=portNumber, protocol=protocol)

# Check whether or not the policy exists, unless the action is a force.
# If the policy doesn't exist then program tells user and lists existing policies.
# If the user gets a error, it is due to a connection error, so the program tells the user to check their connection.
if (args.force == False):
    try:
        oldPolicy = api_instance.get_network_security_policy(default, args.policy_name)
    except Exception as ex:
        if (ex.status == 404):
            policies = api_instance.list_network_security_policy(default)
            if (len(policies.items) > 0):
                print("Couldn't find the policy, use `--force` to create a new policy, or use from the following existing policies:")
                for realPolicy in policies.items:
                    print(realPolicy.meta.name)
            else:
                sys.exit("No policies exist")
        else:
            sys.exit("Unable to connect to psm; this could be due to invalid psm IP address, connectivity issue, or a psm being down")

# Create rule based on given arguments
rule = SecuritySGRule(action=args.action,
                      from_ip_addresses=[args.from_ip],
                      proto_ports=[inputPort],
                      to_ip_addresses=[args.to_ip])


# Adds new rule to current array of rules in specified policy
def addRule(r, p):
    p.spec.rules.append(r)
    api_instance.update_network_security_policy(default, args.policy_name, p)
    print("Hole Poked!")


# Creates the first rule in an empty policy(empty policy can happen when someone forces a hole and then patches the hole after)
def addFirstRule(r):
    policy = SecurityNetworkSecurityPolicy(meta=ApiObjectMeta(name=args.policy_name),
                                           spec=SecurityNetworkSecurityPolicySpec(rules=[r], attach_tenant=True))
    api_instance.update_network_security_policy(default, args.policy_name, policy)
    print("Successfully added the specified rule at the top of the specified policy")


# Forcing a rule is a action which a user can specify. This creates an entire new policy with the specified rule.
def forceRule(r):
    policy = SecurityNetworkSecurityPolicy(meta=ApiObjectMeta(name=args.policy_name),
                                           spec=SecurityNetworkSecurityPolicySpec(rules=[rule], attach_tenant=True))
    api_instance.add_network_security_policy(default, policy)
    print("Created policy")


# Deletes the given rule from the given policy. This is useful for when the user wants to patch a hole.
def deleteRule(r, p):
    try:
        exists = r in p.spec.rules
        if (exists == True):
            p.spec.rules.remove(r)
            api_instance.update_network_security_policy(default, args.policy_name, p)
            print("Rule patched/deleted!")
        else:
            raise Exception
            print("Double check inputs.")
    except:
        print("No rules in the policy")

def ruleExists(r, p):
    try:
        exists = r in p.spec.rules
        if (exists == True):
            return True
        else:
            return False
    except:
        print("No rules were in the policy")


# If the user tries to force and patch a rule at the same time, the program tells the user they can't do that
# If the user wants to patch a hole, then the program calls deleteRule.
# If the user doesn't specify a specific action, then the program updates the given policy to incorporate the new rule. This is used for when the user wants to poke a hole in a existing policy
if (args.force):
    if (args.patch):
        sys.exit("Can not patch and force at the same time...")
    else:
        forceRule(rule)
elif (args.patch):
    try:
        deleteRule(rule, oldPolicy)
    except Exception as ex:
        print("Unable to patch, given inputs are wrong. Check your rule and your policy.")
        sys.exit("Rule " + str(rule) + " doesn't exist")
else:
    if (ruleExists(rule, oldPolicy)):
        print("Rule already exists")
    else:
        try:
            if ("oldPolicy" in locals()):
                addRule(rule, oldPolicy)
        except Exception as ex:
            addFirstRule(rule)


#1 Poke a hole given a name of an existing policy(non-empty) and the params for the rule -> creates new rule in existing policy(DONE)
#2 Poke a hole given a name of an existing policy(empty) and the params for the rule -> create new rule without getting previous rules(DONE)
#3 Poke a hole given a name of a non-existent policy and the params for the rule -> tells user that the policy doesn't exists and lists existing policy names(DONE)
#4 Poke a hole using a force and the params for the rule -> Creates a entire new policy with the given rule(1/2, still need to take input for -f)
#5 Patch a hole which was poked by the user given the rule which is to be deleted and the policy from which the rule exists in -> Deletes rule and updates policy
#6 Patch a hole with incorrect inputs -> Tells user to double check inputs and that the rule doesn't exist
#7 Patch and force a hole in the same command -> Tells user that they can't patch and force a rule at the same time
#8 User doesn't have right connection -> Tells user to check their connection
#9 User doesn't put in all inputs -> Tells user which arguments are required

