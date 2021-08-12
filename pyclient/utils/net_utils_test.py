import os
from utils.net_utils import isIPv4
import logging
import sys
import json
import warnings
from apigroups.client import configuration, api_client

#valid IPv4 address
print(isIPv4("23.30.4.9"))

#invalid IPv4 address (incorrect format)
print(isIPv4("4.4.4.4.4"))

#invalid IPv4 address (integers larger than 255)
print(isIPv4("999.999.1.1"))

#invalid IPv4 address (incorrect seperator)
print(isIPv4("23,30,4,9"))