Using samples:
1. Clone the psm-tools repository to your lo
2. Add apigroup folder to pythonpath
    After cloning this repo, chande directory to `pyclient` and run this command:
    ```export PYTHONPATH=$PYTHONPATH:$(pwd)```
3. 


Generating your own APIs
1. Create $HOME/.psm/config.json
    ```
    {
        "psm-ip": "PSM.IP.GOES.HERE"
    }
    ```
2. Clone this repository and cd to `pyclient`.
3. Make sure you have python3 installed.

    Install pip:
        https://pip.pypa.io/en/stable/installing/
    Incase you get an import error during pip installation install python utils: `apt-get install python3-distutils`
    <!-- install python -->
4. `pip install -r requirements.txt`
5. Use `make getswagger` to fetch swagger specifications for all api groups. Downloaded swagger files are stored in py-client/swagger directory.
6. Before generating client code, make sure java in installed.
7. Use `make genclient` to generate client code in python3 