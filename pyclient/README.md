## Using PSM python client

1. Clone the repo (in any directory)
```
git clone https://github.com/pensando/psm-tools
cd psm-tools/pyclient
```

2. Run the python3 environment to make client libraries
```
# docker run -it -v ~/.psm:/root/.psm -v `pwd`:/pyclient pensando/pyclient:0.1 /bin/bash
docker run -it -v ~/.psm:/root/.psm -v `pwd`:/pyclient registry.test.pensando.io:5000/pyclient:0.1 /bin/bash

make
```

3. Run python client apps to confirm all is good
```
./apps/cluster_ping.py
```

## Advanced operations
1. For non interactive mode, you must do a few additional setup
* Create ~/.psm/config.json file with PSM coordinates
```
$ cat ~/.psm/config.json
{
  "psm-ip": "psm's ip address",
}
* Specify the PSM credentials either by setting PSM_USER and PSM_PASSWORD variables or modify the ~/.psm/config.json as follows
```
{
  "psm-ip": "psm's ip address",
  "token": "psm user's jwt token"
}
```

* Building docker container
```
docker build . -t pyclient:0.1
```

* Running python code natively (not in docker container)
You'll need to install python3, pip, java and maven as documented in the Dockerfile, and set $PYTHONPATH 
