import json
import requests
import re
import os
import config

host = "https://" + config.HOSTNAME

if not os.path.exists("swagger"):
    os.mkdir("swagger")

response = requests.get(host+"/docs/generated/swaggeruri.html", verify=False)
matches = re.findall("href=\"([^\"]*)", response.text)

for match in matches:
    resp = requests.get(host+match, verify=False)
    filename = match.replace("/swagger/", "")
    with open("swagger/"+filename+".json", "w") as f:
        json.dump(resp.json(), f, indent=4)