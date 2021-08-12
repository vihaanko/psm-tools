import os
from apigroups.client.apis import WorkloadV1Api
from utils.workload_utils import getDscFromWorkload
import logging
import sys
import json
import warnings
from apigroups.client import configuration, api_client

warnings.simplefilter("ignore")

HOME = os.environ['HOME']

cfg = configuration.Configuration(
    psm_config_path=HOME+"/.psm/config.json",
    interactive_mode=True
)
cfg.verify_ssl = False
client = api_client.ApiClient(cfg)


workload_instance = WorkloadV1Api(client)
workload_response = workload_instance.list_workload("default")

#an existing workload
print(getDscFromWorkload(client, "default" , workload_response.items[0]["meta"]["name"]))

#an invalid workload name
name = "invalidworkloadname"
nameisdif = False
oldname = name
while(nameisdif):
    for work in workload_response.items:
        if (work["meta"]["name"] == name):
            oldname = name
            name += "1"
    nameisdif == (oldname == name)
print(getDscFromWorkload(client, "default" , name))

#an invalid workload IP
IP = "0.0.0.0"
print(getDscFromWorkload(client, "default" , IP))

#an invalid workload IP thats forced into name
print(getDscFromWorkload(client, "default" , "0.0.0.0", forceName=True))