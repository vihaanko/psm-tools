import json
import requests
import re
import os
import sys
import logging

HOME = os.environ["HOME"]
psm_config_path = HOME+"/.psm/config.json"
psm_config = {}

def update_psm_config(path):
    psmip = input("Enter PSM IP address: ")
    with open(path, "w") as f:
        config_data = {"psm-ip": psmip}
        json.dump(config_data, f)
    return config_data

def get_psm_config():
    config_data = {}
    config_path = psm_config_path
    if not os.path.exists(psm_config_path):
        logging.warn("PSM config does not exist at "+ psm_config_path)
        cont = input("Create confiig at "+psm_config_path+" ? [y/n]")
        if cont.lower() != 'y':
            sys.exit(1)
            return
        if psm_config_path[0] == "~":
            HOME = os.environ["HOME"]
            config_path = HOME + config_path[1:]
        foldersplit = config_path.split(os.sep)
        if foldersplit[-1]:
            dirpath = (os.sep).join(foldersplit[:-1])
            if not os.path.exists(dirpath):
                os.makedirs((os.sep).join(foldersplit))
            config_data = update_psm_config(config_path)
        else:
            logging.error("Invalid PSM config path")
            sys.exit(1)
    else:
        with open(config_path, "r") as f:
            config_data = json.load(f)
    return config_data

def write_psm_config(config_data):
    with open(psm_config_path, "w") as f:
        psm_config = json.dump(config_data, f)

def downloadSwaggerFiles():
    host = psm_config["psm-ip"]
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
    psm_config = get_psm_config()
    downloadSwaggerFiles()
