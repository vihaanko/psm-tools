## Using PSM python client
1. Create PSM config file
```
mkdir ~/.psm
cat <<EOF > ~/.psm/config.json
{
  "psm-ip": "FILL.YOUR.PSM's.IP"
}
EOF 
```

2. Clone the repo (in any directory)
```
git clone https://github.com/pensando/psm-tools
cd psm-tools/pyclient
```

3. Run the python3 environment to make client libraries
```
# docker run -it -v ~/.psm:/root/.psm -v `pwd`:/pyclient pensando/pyclient:0.1 /bin/bash
docker run -it -v ~/.psm:/root/.psm -v `pwd`:/pyclient registry.test.pensando.io:5000/pyclient:0.1 /bin/bash

make
```

4. Run python client utilities to confirm all is good
```
./utilities/cluster_ping.py
```

## Advanced operations
* Building docker container
```
docker build . -t pyclient:0.1
```

* Running things out side docker
You'll need to install python3, pip, java and maven as documented in the Dockerfile, and set $PYTHONPATH 
