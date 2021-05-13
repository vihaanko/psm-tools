### Using the code generator to output the client APIs
1. In your user's home directory ($HOME environment variable on linux systems) create a new directory called `.psm` and inside this folder create a `config.json` with your PSM IP:
    ```
    {
        "psm-ip": "PSM.IP.GOES.HERE"
    }
    ```

1. Clone this repository in your preffered location and change directory to `psmtools/pyclient`.

1. Make sure you have python3 installed.

    - Install pip following these steps: https://pip.pypa.io/en/stable/installing/

    - Incase you get an import error during pip installation install python utils run:
    `apt-get install python3-distutils`

1. Install all python dependencies using
    
    `pip install -r requirements.txt`

1. Before generating client code, make sure java and maven is installed.
    
    `apt install default-jdk`
    
    `apt install maven`

1. Use `make` to run the end to end client generation. Internally this will call two different targets:

    1. Use `make getswagger` to fetch swagger specifications for all API groups from PSM. Downloaded swagger files are stored in py-client/swagger directory.

    1. Use `make genclient` to generate client code for PSM APIs using the downloaded swagger spec.

1. You should find a new apigroups directory, which contains the generated code. Make sure to add this location to your PYTHONPATH so that python can find these modules. While you are in the pyclient directory run:

    ```export PYTHONPATH=$PYTHONPATH:$(pwd)```

### Using sample scripts:
1. If you have the client code ready, you can try running the sample utility scripts.

2. Add apigroups folder to pythonpath
    After cloning this repo, change directory to `pyclient` and run this command:
    ```export PYTHONPATH=$PYTHONPATH:$(pwd)```

3. Change directory to utilities and try running one of the provided python programs in the utilities directory:
    ``` python3 clusterping.py ```

### Docker Container

You can also use the provided Dockerfile to setup the environment quickly.

1. Make sure docker is up and running.

2. While in the `pyclient` directory, build the container image from the Dockerfile:
    ```docker build . -t pyclient:1.0```

3. Now you can spin up the container and access the shell:
    ```docker run -it psmclient:1.0 /bin/bash```