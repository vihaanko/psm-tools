Using samples:
1. Add folder to pythonpath

Generating your own APIs
1. Create $HOME/.psmconfig
    ```
    {
        "psm-ip": "PSM.IP.GOES.HERE"
    }
    ```
2. Use `make getswagger` to fetch swagger specifications for all api groups. Downloaded swagger files are stored in py-client/swagger directory.
3. Before generating client code, make sure java in installed.
4. Use `make genclient` to generate client code in python3 