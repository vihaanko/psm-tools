#!/usr/bin/env python3

###
# Run this as a schedule job for every 1 min in crontab
# This script updates the System Dashboard
# Author - venksrin@pensando.io
###

import os
import sys
import re
import logging
import json
import time
import subprocess

from urllib import request, parse
import random
from datetime import datetime
from datetime import datetime

import kubernetes_lib
import minio_lib
import elastic_lib
import etcd_lib
import sys_utils
import mongodb_lib
import influxdb_lib


from input_file import *

logging.basicConfig( level=logging.INFO, filename="/tmp/venk_script.log", filemode='w')
logging.root.setLevel(logging.INFO)
log = logging.getLogger("mon")



refresh_interval = 2



# Update methods to send JSON content to widgets ..

def update_val( widget, value, auth_token=dashing_auth_token, url=dashing_url ):
    data = {"auth_token": auth_token, "value": value}
    data = json.dumps(data)
    data = str(data)
    data = data.encode('utf-8')
    req =  request.Request("{}/widgets/{}".format(url, widget), data=data)
    response = request.urlopen(req)
    print(response.status)



def update_key_val( widget, key, value, auth_token=dashing_auth_token, url=dashing_url ):
    data = {"auth_token": auth_token, key: value}
    data = json.dumps(data)
    data = str(data)
    data = data.encode('utf-8')
    print(data)
    req =  request.Request("{}/widgets/{}".format(url, widget), data=data)
    response = request.urlopen(req)
    print(response)
    print(response.status)








def get_system_res_dict( mdb, db_name, collection_name, psm_cluster_name ):
    mdb.switch_db( db_name )
    res_dict = mdb.get_record( collection_name, { 'psm-cluster-name': psm_cluster_name } )
    print(res_dict)
    return res_dict


def get_proc_mem_dist_dict( mdb, db_name, collection_name, psm_cluster_name, psm_cluster_dict ):
    mem_dist_dict = {}
    mdb.switch_db( db_name )
    proc_mem_dist_dict = mdb.get_record( collection_name, { 'psm-cluster-name': psm_cluster_name } )
    for node in psm_cluster_dict.keys():
        mem_dist_dict[node] = {}
        node_dict = json.loads(proc_mem_dist_dict['mem-dist'])
        mem_dist_dict[node] = node_dict[node]
    print(mem_dist_dict)
    return mem_dist_dict

        

def get_proc_mem_dist_slices( mem_dist_dict ):
    proc_mem_dist_slices = {}

    for node in mem_dist_dict.keys():
        slice_points = [ [ 'ProcessName', 'MemPercent' ] ]
        for proc_name in mem_dist_dict[node].keys():
            line_points = [ proc_name, mem_dist_dict[node][proc_name] ]
            slice_points.append(line_points)
        proc_mem_dist_slices[node] = slice_points
    print(proc_mem_dist_slices)
    return proc_mem_dist_slices
        


def get_nodes_table_points(ko):
    nodes_dict = ko.get_brief_cluster_nodes_dict()
    nodes_table_points = [ [ 'Node', 'vCPUs', 'Memory', 'Storage', 'OS', 'Kernel', 'Status', 'KubeProxyVer', 'KubeletVer' ] ]
    for node in nodes_dict:
        status_value=""
        for stat_val in nodes_dict[node]['status']:
               status_value = status_value + ',' + stat_val
        n_list = [ node, nodes_dict[node]['cpu'], nodes_dict[node]['memory'], nodes_dict[node]['storage'],
               nodes_dict[node]['os_image'], 
               nodes_dict[node]['kernel_version'], status_value,
               nodes_dict[node]['kube_proxy_version'],
               nodes_dict[node]['kubelet_version'] ]
        nodes_table_points.append(n_list)
    return nodes_table_points



def get_cluster_pods_table_points( pod_dict ):

    #pod_dict = ko.get_cluster_pod_dict_for_all_ns()
    image_dir = '/data/docker/image/overlay2/imagedb/content/sha256'
    pods_table_points = [ [ 'Pod', 'Node', 'NS', 'ApiVersion', 'Kind', 'Ready', 'RestartCount', 'StartTime', 'Image', 'MountPoints' ] ]
    for node_name in pod_dict.keys():
        for pod_name in pod_dict[node_name].keys():
            print(type(pod_dict[node_name][pod_name]['container_dict']['cmd']))
            if pod_dict[node_name][pod_name]['container_dict']['cmd'] is None:
               actual_cmd = None
            else:
               if pod_dict[node_name][pod_name]['container_dict']['cmd']._exec is None:
                  actual_cmd = None
               else:
                  actual_cmd = ""
                  print(pod_name)
                  for cmd_opt in pod_dict[node_name][pod_name]['container_dict']['cmd']._exec.command:
                      actual_cmd = actual_cmd + " " + cmd_opt

            print(pod_dict[node_name][pod_name]['container_dict']['volume_mounts'])
            vol_mounts_str = ""
            for vol_mount in pod_dict[node_name][pod_name]['container_dict']['volume_mounts']:
                vol_mounts_str = vol_mounts_str + ' ' + vol_mount

            pod_restart_count = pod_dict[node_name][pod_name]['containers_list_status'][0].restart_count
            start_time = pod_dict[node_name][pod_name]['start_time'].strftime("%m/%d/%Y, %H:%M:%S")
            print(pod_dict[node_name][pod_name])
            #phase = pod_dict[node_name][pod_name].phase
            image_str = ""
            image = pod_dict[node_name][pod_name]['containers_list_status'][0].image
            image_id = str(pod_dict[node_name][pod_name]['containers_list_status'][0].image_id)
            match = re.search( 'docker://sha256:([a-z0-9]+)', image_id )
            image_id_str = match.group(1) 
            image_str = '{} {} {}'.format(image, image_dir, image_id_str)

            n_list = [ pod_name, node_name, pod_dict[node_name][pod_name]['namespace'],
                     pod_dict[node_name][pod_name]['api_version'],
                     pod_dict[node_name][pod_name]['kind'],
                     pod_dict[node_name][pod_name]['containers_list_status'][0].ready,
                     pod_restart_count, start_time, image_str, vol_mounts_str

            ]
            pods_table_points.append(n_list)
    return pods_table_points





def get_cluster_pod_restart( pod_dict ):
    val_list = []
    for node_name in pod_dict.keys():
        for pod_name in pod_dict[node_name].keys():
            val = { 'label': pod_name, 'value': pod_dict[node_name][pod_name]['containers_list_status'][0].restart_count }
            val_list.append(val)
    return val_list



def get_total_pod_list( pod_dict ):
    pod_list = []
    for node in pod_dict.keys():
        tmp_pod_list = list(pod_dict[node].keys())
        pod_list.extend(tmp_pod_list)
    return pod_list 
    


def get_containers_resource_dict( hdl_dict ):
    res_dict = {}
    for node in hdl_dict.keys():
        res_dict[node] = {}
        docker_cmd = '''docker stats --format "table {{.Name}}\\t{{.CPUPerc}}\\t{{.MemUsage}}\\t{{.MemPerc}}" --no-stream | grep -v LIMIT'''
        print(docker_cmd)
        #output = hdl_dict[node].send_command(docker_cmd, delay_factor=4)
        output = hdl_dict[node].send_command(docker_cmd )
        print(output)
        for line in output.split("\n"):
            match = re.search( '([0-9a-zA-Z\_\-]+)[\s]+([0-9\.]+)%[\s]+([0-9\.]+[KMG]iB)\s\/\s([0-9\.]+[KMG]iB)[\s]+([0-9\.]+)%', line )
            container_full_name = match.group(1)
            container_name = container_full_name[0:30]
            res_dict[node][container_name] = {}
            res_dict[node][container_name]['cpu_percent'] = float(match.group(2))
            res_dict[node][container_name]['mem_usage'] = match.group(3)
            res_dict[node][container_name]['mem_limit'] = match.group(4)
            res_dict[node][container_name]['mem_percent'] = float(match.group(5))
    print(res_dict)
    return res_dict
        


def get_mem_in_mib( mem_usage ):
    match = re.search( '([0-9\.]+)[KMG]iB', mem_usage )
    mem_numb = float(match.group(1))
    if re.search( 'KiB', mem_usage):
       mem_used_mib = float(mem_numb / 1024)
    elif re.search( 'GiB', mem_usage):
       mem_used_mib = mem_numb * 1024
    elif re.search( 'MiB', mem_usage):
       mem_used_mib = mem_numb
    return mem_used_mib


def get_containers_memory_use_chart_points( res_dict, venice_container_list ):
    res_dict = get_containers_resource_dict( hdl_dict )
    mem_bar_chart_points = [ [ 'Container', 'Node1', 'Node2', 'Node3' ] ]
    mem_mib_dict = {}
    for node in [ 'node1', 'node2', 'node3']:
        mem_mib_dict[node] = {}
        for container_name in venice_container_list:
            print(container_name)
            mem_used_mib = 0
            pod_pattern = "k8s_" + container_name
            print(type(pod_pattern))
            print(pod_pattern)
            matching = [ s for s in res_dict[node].keys() if pod_pattern in  s ]
            if len(matching) > 0:
               mem_usage = res_dict[node][matching[0]]['mem_usage']
               mem_used_mib = get_mem_in_mib(mem_usage)
            mem_mib_dict[node][container_name] = get_mem_in_mib(mem_usage)

    for container_name in venice_container_list:
        n_list = [ container_name, mem_mib_dict['node1'][container_name], mem_mib_dict['node2'][container_name],
                 mem_mib_dict['node3'][container_name] ]
        mem_bar_chart_points.append(n_list)
    print(mem_bar_chart_points)
    return mem_bar_chart_points
    



def get_psm_cpu_trend_line_chart_points( influx, influx_db_name, measurement_name,
    field_name, tag_name, last_x_min=60 ):

    out_dict = influx.query_points_for_last_x_mins( influx_db_name, measurement_name, field_name,
               tag_name, last_x_min )
    cpu_dict = influx.convert_raw_points_to_dict_of_x_elements( out_dict, 'psm-node', 10 )
    timestamp_list = cpu_dict['node1'].keys()
    cpu_chart_points = [ [ 'Timestamp', 'node1', 'node2', 'node3' ] ]
    for timestamp in timestamp_list:
        val_points = []
        val_points = [ timestamp, cpu_dict['node1'][timestamp][0], cpu_dict['node2'][timestamp][0], cpu_dict['node3'][timestamp][0] ]
        cpu_chart_points.append(val_points)

    print(cpu_chart_points)
    return cpu_chart_points






##
##


mdb   = mongodb_lib.mongoClientObj( log, mongodb_host, username = mongodb_username,
        password = mongodb_password, port = mongodb_port )


influx = influxdb_lib.influxDBClient( log, host=influx_host, username=influx_user, password=influx_password )


#res_dict = get_containers_resource_dict( hdl_dict )
#get_containers_memory_use_chart_points( res_dict, venice_container_list )
# To DO
#ko.get_events_for_all_ns()



for i in range(1, 27 ):

    res_dict = get_system_res_dict( mdb, mongodb_name, psm_resource_collection, psm_cluster_name)
    cpu_dict = json.loads(res_dict['cpu-info'])
    mem_dict = json.loads(res_dict['mem-info'])
    disk_dict = json.loads(res_dict['disk-info'])

    try:
       update_key_val( 'node1cpugauge', 'current', float(cpu_dict['node1']))
       update_key_val( 'node2cpugauge', 'current', float(cpu_dict['node2']))
       update_key_val( 'node3cpugauge', 'current', float(cpu_dict['node3']))
    except Exception as e:
       print('ERROR in Posting Node CPU table {}'.format(e)) 


    try:
       update_val( 'node1dumeter', float(disk_dict['node1']))
       update_val( 'node2dumeter', float(disk_dict['node2']))
       update_val( 'node3dumeter', float(disk_dict['node3']))
    except Exception as e:
       print('ERROR in Posting Node Disk table {}'.format(e)) 


    try:
       update_val( 'node1memmeter', int(mem_dict['node1']))
       update_val( 'node2memmeter', int(mem_dict['node2']))
       update_val( 'node3memmeter', int(mem_dict['node3']))
    except Exception as e:
       print('ERROR in Posting Node Memory table {}'.format(e))



    try:
       cpu_trend_points = get_psm_cpu_trend_line_chart_points( influx, influx_db_name, 'resource_utilization', 'cpu', 'psm-node', 60 )
       update_key_val( "cputrendchart", "points", cpu_trend_points )
    except Exception as e:
       print('ERROR Logs CPU Trend chart Posting failure {}'.format(e))


    try:
       proc_mem_dist_dict = get_proc_mem_dist_dict( mdb, mongodb_name, proc_mem_dist_collection, psm_cluster_name, psm_cluster_dict )
       proc_mem_slices = get_proc_mem_dist_slices( proc_mem_dist_dict )

       for node_name in proc_mem_dist_dict.keys():
           exec( "%s=proc_mem_dist_dict[node_name]"  % ( node_name + "memdistpie" ))
           widget_name = node_name + "memdistpie"
           update_key_val( widget_name, 'slices', proc_mem_slices[node_name] )
           
    except Exception as e:
       print('ERROR Posting Proc memory pie failure {}'.format(e))
 
    # Duration between refresh
    time.sleep(refresh_interval)

