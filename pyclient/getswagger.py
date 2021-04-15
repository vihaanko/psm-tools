import json
import requests
import re
import os

HOME = os.environ["HOME"]

config = {}
with open(HOME+"/.psm/config.json", "r") as f:
    config = json.load(f)

def downloadSwaggerFiles():
    host = config["psm-ip"]
    if not os.path.exists("swagger"):
        os.mkdir("swagger")

    response = requests.get(host+"/docs/generated/swaggeruri.html", verify=False)
    matches = re.findall("href=\"([^\"]*)", response.text)

    for match in matches:
        resp = requests.get(host+match, verify=False)
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
    return jsondata


if __name__ == "__main__":
    downloadSwaggerFiles()
