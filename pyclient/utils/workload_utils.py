import os
from apigroups.client.apis import WorkloadV1Api
from utils.net_utils import isIPv4
import logging
import sys
import json
import warnings

def getDscFromWorkload(client, tenant,  workload, forceName=False):
    '''
    This will get a specific DSC id from a workload. The workload can be identified in two ways, via the workload name or the uuid of the workload. 

    Args:
        client (client): the client will be passed as an argument to be used to recieve api information
        tenant (string): the tenant for the API calls
        workload (string): either the name or the UUID of the workoad, the type will be identified by the code
    
    Keyword Args:
        forceName (boolean): treat the workload as a name even if it is a valid IP
    
    Return:
        error, dsc_id (string, list[string]): The value returned by this method will be the IDs of the dsc that the workload is running on. It will return a blank list if no dsc 
        can be found. It will return strings with error messages if the workload name or IP cant be found. The error string will be blank if there are no errors
        '''


    '''
    These are the api calls that this function will perform, to be used later in the code
    '''
    workload_instance = WorkloadV1Api(client)
    workload_response = workload_instance.list_workload(tenant)
    endpoint_response = workload_instance.list_endpoint(tenant)
    

    '''
    This section checks if the name is a valid IP address, else it treats the workload param as a name. If forceName is set to true, then it will treat it a name, not an IP
    '''
    isIP = isIPv4(workload) and not forceName
    

    '''
    This is the series of if statements to determine the endpoint from the workload. If the workload name or IP cannot be found, then the function returns a string error message
    ''' 

    endpoint_list = []

    if (not isIP):
        for work in workload_response.items:
            if (work.meta.name == workload):
                for interface in work.status.interfaces:
                    endpoint_list.append(interface.endpoint)      
    else:
        for work in workload_response.items:
            for interface in work.status.interfaces:
                if ("ip-addresses" in interface):
                    for ip in interface.ip-addresses:
                        if (ip == workload):
                            endpoint_list.append(interface.endpoint)
    if (len(endpoint_list) == 0):
        return ("Workload " + workload +  " not found", [])

       

    '''
    These series of statements finds the dsc's id based on the endpoints. The return will be null if the dsc id cannot be found
    '''
    dsc_id_list = []

    for endpoint in endpoint_response.items:
        for endpoint_name in endpoint_list:
            if (endpoint.meta.name == endpoint_name):
                dsc_id_list.extend(endpoint.spec.node_uuid_list)

    
    '''
    This last section removes duplicate DSC's from the list. This case could arise if there are multiple endpoints or interfaces pointing to the same DSC
    '''
    dsc_return = []

    for i in dsc_id_list:
        if (i not in dsc_return):
            dsc_return.append(i)
    
    return ("" ,dsc_return)
    


