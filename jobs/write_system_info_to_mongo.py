#!/usr/bin/env python3

###
# Run this as a background script. This script collects the system CPU, Memory, Disk Utilization
# information and adds to Mongodb for the latest snapshot and to InfluxDB for the historic
# Time series data.
# Author - venksrin@pensando.io
###

import os
import sys
import re
import logging
import json
import time
import subprocess

from datetime import datetime

import influxdb_lib
import mongodb_lib
import sys_utils

import paramiko
import netmiko
from netmiko import ConnectHandler
from netmiko import redispatch

# Sourcing input file
from input_file import *


# Create log object
logging.basicConfig( level=logging.INFO, filename="/tmp/mon_script.log", filemode='w')
logging.root.setLevel(logging.INFO)
log = logging.getLogger("mon")



# Input Parameters ..
from input_file import *


wait_interval = 5



def write_system_resources_to_influx( psm_cluster_dict, influx_client, db_name, cpu_dict, mem_dict, disk_dict ):
    time_obj = datetime.now()
    current_time = datetime.strftime(time_obj, '%Y-%m-%dT%H:%M:%S.%fZ')

    measurement_name = 'resource_utilization'
    for node in cpu_dict.keys():
        json_body_str = '''[
           {
              "measurement": "''' + str(measurement_name) + '''",
              "tags": {
                     "psm-node": "''' + str(node) + '''",
                     "psm-ip": "''' + str(psm_cluster_dict[node]['ip']) + '''"
               },
               "time": "''' + str(current_time) + '''",
               "fields": {
                    "cpu": ''' + str(cpu_dict[node]) + ''',
                    "memory": ''' + str(mem_dict[node]) + ''',
                    "disk": ''' + str(disk_dict[node]) + '''
               }
           }
        ]'''
        print(json_body_str)
        influx_client.write_measurement_point( db_name, measurement_name, json_body_str )



def write_sys_resources_to_dbs( hdl_dict, mdb, mongodb_name, influx, influx_db_name ):

    
    cpu_dict = sys_utils.get_cluster_cpu_summary_dict(hdl_dict)
    mem_dict = sys_utils.get_cluster_memory_summary_dict( hdl_dict )
    disk_dict = sys_utils.get_cluster_disk_summary_dict( hdl_dict )
    # Write to Mongo
    mdb.switch_db( mongodb_name )
    mdb.update_record( psm_resource_collection, { 'psm-cluster-name': psm_cluster_name }, { 'psm-cluster-name': psm_cluster_name, 'cpu-info': json.dumps(cpu_dict), 'mem-info': json.dumps(mem_dict), 'disk-info': json.dumps(disk_dict) } )
    # Write to influx
    write_system_resources_to_influx( psm_cluster_dict, influx, influx_db_name, cpu_dict, mem_dict, disk_dict )






def get_go_agent_dict( hdl_dict ):
    go_agent_dict = {}
    for node in hdl_dict.keys():
        go_agent_dict[node] = {}
        ss_out = hdl_dict[node].send_command('ss -tunlp | grep LISTEN | grep 127.0.0.1 --color=never')
        for line in ss_out.split("\n"):
            if re.search( '[a-z]+\s+LISTEN\s+[0-9]+\s+[0-9]+\s+127\.0\.0\.1\:([0-9]+)', line ):
               match = re.search( '[a-z]+\s+LISTEN\s+[0-9]+\s+[0-9]+\s+127\.0\.0\.1\:([0-9]+)\s+\*\:\*\s+users:\(\(\"([a-zA-Z\-]+)\",', line )
               go_agent_dict[node][match.group(2)] = int(match.group(1))
    print(go_agent_dict)
    return go_agent_dict
            
 


def get_go_allocs_profile_dict( hdl_dict ):

    allocs_dict = {}
    go_dict = get_go_agent_dict( hdl_dict )
    for node in go_dict.keys():
        allocs_dict[node] = {}
        for agent_name in go_dict[node].keys():
            allocs_dict[node][agent_name] = {}
            cmd = 'curl localhost:{}/debug/pprof/allocs?debug=2 | grep -i -A 20 runtime.MemStats --color=never'.format( go_dict[node][agent_name])
            output = hdl_dict[node].send_command(cmd)
            cmd = 'curl localhost:{}/debug/pprof/threadcreate?debug=2 | grep -i threadcreate --color=never'.format( go_dict[node][agent_name] )
            thread_output = hdl_dict[node].send_command(cmd)
            for line in output.split("\n"):
                if re.search( '#\s[A-Za-z]+\s=\s[0-9]+\s\/\s[0-9]+', line ):
                   match = re.search( '#\s([A-Za-z]+)\s=\s([0-9]+)\s\/\s([0-9]+)', line )
                   val = match.group(2) + '/' + match.group(3)
                   allocs_dict[node][agent_name][match.group(1)] = val
                elif re.search( '#\s[A-Za-z]+\s=\s[0-9]+', line ):
                   match = re.search( '#\s([A-Za-z]+)\s=\s([0-9]+)', line )
                   allocs_dict[node][agent_name][match.group(1)] = match.group(2)
            if re.search( 'total\s([0-9]+)', thread_output, re.I ):
               match = re.search( 'total\s([0-9]+)', thread_output, re.I )
               allocs_dict[node][agent_name]['thread_count'] = match.group(1)
    print(allocs_dict)
    return allocs_dict






##
# Main script starts here ..
##


# Connect to the DBs ..
influx = influxdb_lib.influxDBClient( log, host=influx_host, username=influx_user, password=influx_password )

mdb = mongodb_lib.mongoClientObj( log, mongodb_host, username = mongodb_username,
      password = mongodb_password, port = mongodb_port )


# ssh to the PSM Nodes
hdl_dict = sys_utils.get_node_hdl_dict( psm_cluster_dict )



# Incase you are not able to manually create the databases or collections in MongoDB, please
# Uncomment the following code snippet when you run first time 

#mdb.create_database( mongodb_name )
#mdb.create_collection( mongodb_name, psm_resource_collection )
#mdb.create_collection( mongodb_name, go_profile_collection )
#mdb.create_collection( mongodb_name, proc_mem_dist_collection )

#mdb.switch_db( mongodb_name )
#mdb.insert_record(proc_mem_dist_collection, { 'psm-cluster-name': psm_cluster_name, 'mem-dist': json.dumps(proc_mem_dist_dict) })
#mdb.get_record( proc_mem_dist_collection, { 'psm-cluster-name': psm_cluster_name } )

#go_profile_dict = get_go_allocs_profile_dict( hdl_dict )
#mdb.insert_record( go_profile_collection, { 'psm-cluster-name': psm_cluster_name, 'alloc-info': json.dumps(go_profile_dict) } )
#mdb.get_record( go_profile_collection, { 'psm-cluster-name': psm_cluster_name } )
#mdb.switch_db( mongodb_name )
#cpu_dict = sys_utils.get_cluster_cpu_summary_dict(hdl_dict)
#mem_dict = sys_utils.get_cluster_memory_summary_dict( hdl_dict )
#disk_dict = sys_utils.get_cluster_disk_summary_dict( hdl_dict )
#mem_dist_dict = sys_utils.get_cluster_process_memory_distribution_dict( hdl_dict, ps_mem_cmd )
#mdb.insert_record( psm_resource_collection, { 'psm-cluster-name': psm_cluster_name, 'cpu-info': json.dumps(cpu_dict), 'mem-info': json.dumps(mem_dict), 'disk-info': json.dumps(disk_dict), 'proc-mem-distribution-info': json.dumps(mem_dist_dict) } )
#docker_res_dict = sys_utils.get_containers_resource_dict( hdl_dict )
#mdb.insert_record( docker_res_collection, { 'psm-cluster-name': psm_cluster_name, 'docker-mem-info': json.dumps(docker_res_dict) } )
#log_dict = sys_utils.get_cluster_log_summary_dict( hdl_dict )
#mdb.insert_record( psm_log_summary_collection, { 'psm-cluster-name': psm_cluster_name, 'log-info': json.dumps(log_dict) } )



mdb.switch_db( mongodb_name )


while True:


    write_sys_resources_to_dbs( hdl_dict, mdb, mongodb_name, influx, influx_db_name )

    time.sleep(wait_interval)

