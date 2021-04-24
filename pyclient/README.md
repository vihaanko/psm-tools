### Using sample scripts:
1. Add apigroups folder to pythonpath
    After cloning this repo, chande directory to `pyclient` and run this command:
    ```export PYTHONPATH=$PYTHONPATH:$(pwd)```

2. Change directory to utilities and try running one of the     provided python programs:
    ``` python3 clusterping.py ```

### Generating your own APIs
1. Create $HOME/.psm/config.json
    ```
    {
        "psm-ip": "PSM.IP.GOES.HERE"
    }
    ```

1. Clone this repository and cd to `pyclient`.

1. Make sure you have python3 installed.

    Install pip as shown here: https://pip.pypa.io/en/stable/installing/


    Incase you get an import error during pip installation install python utils run:
    `apt-get install python3-distutils`
    <!-- install python -->

1. Install all python dependencies using
    
    `pip install -r requirements.txt`

1. Use `make getswagger` to fetch swagger specifications for all api groups. Downloaded swagger files are stored in py-client/swagger directory.

1. Before generating client code, make sure java and maven is installed.
    
    `apt install default-jdk`
    
    `apt install maven`

1. Change directory to openapi-generator and build the tool:
    
    `mvn clean install -U -DskipTests`

1. Change directory to psm-tools/pyclient and use `make` to run the end to end client generation.

### Docker Container

You can also use the provided Dockerfile to setup the environment quickly.