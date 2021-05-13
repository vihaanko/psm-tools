import json
import requests
import re
import os
import sys
import logging

HOME = os.environ["HOME"]

config = {}

try:
    with open(HOME+"/.psm/config.json", "r") as f:
        config = json.load(f)
except Exception as e:
    logging.error("PSM config not found at /.psm/config.json")
    sys.exit(1)


def downloadSwaggerFiles():
    host = config["psm-ip"]
    if not os.path.exists("swagger"):
        os.mkdir("swagger")

    response = requests.get("https://"+host+"/docs/generated/swaggeruri.html", verify=False)
    matches = re.findall("href=\"([^\"]*)", response.text)

    for match in matches:
        resp = requests.get("https://"+host+match, verify=False)
        filename = match.replace("/swagger/", "")
        jsondata = processSwagger(filename, resp.json())
        with open("swagger/"+filename+".json", "w") as f:
            json.dump(jsondata, f, indent=4)

def processSwagger(filename, jsondata):
    if filename == "fwlog":
        # fwlog api group
        # remove minLength for fwlogList
        del jsondata["definitions"]["apiListWatchOptions"]["properties"]["name"]["minLength"]
        del jsondata["definitions"]["apiListWatchOptions"]["properties"]["tenant"]["minLength"]
        del jsondata["definitions"]["apiListWatchOptions"]["properties"]["namespace"]["minLength"]
        del jsondata["definitions"]["apiListWatchOptions"]["properties"]["name"]["pattern"]
        del jsondata["definitions"]["apiListWatchOptions"]["properties"]["tenant"]["pattern"]
        del jsondata["definitions"]["apiListWatchOptions"]["properties"]["namespace"]["pattern"]

        del jsondata["definitions"]["apiObjectMeta"]["properties"]["name"]["minLength"]
        del jsondata["definitions"]["apiObjectMeta"]["properties"]["tenant"]["minLength"]
        del jsondata["definitions"]["apiObjectMeta"]["properties"]["namespace"]["minLength"]
        del jsondata["definitions"]["apiObjectMeta"]["properties"]["name"]["pattern"]
        del jsondata["definitions"]["apiObjectMeta"]["properties"]["tenant"]["pattern"]
        del jsondata["definitions"]["apiObjectMeta"]["properties"]["namespace"]["pattern"]
    if filename == "cluster":
        jsondata["definitions"]["clusterDistributedServiceCardSpec"]["required"] = []
    if filename == "workload":
        jsondata["definitions"]["workloadWorkloadIntfSpec"]["required"] = []
    return jsondata


if __name__ == "__main__":
    downloadSwaggerFiles()
