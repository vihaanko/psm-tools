#!/usr/bin/env python3

###
# Run this as a schedule job for every 1 min in crontab
# This script updates the K8 Dashboard
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

sys.path.append('../lib')

import kubernetes_lib
import minio_lib
import elastic_lib
import etcd_lib
import sys_utils
import mongodb_lib

import sys_utils
from sys_utils import update_val, update_key_val



# Input File
from input_file import *

logging.basicConfig( level=logging.INFO, filename="/tmp/mon_script.log", filemode='w')
logging.root.setLevel(logging.INFO)
log = logging.getLogger("mon")



refresh_interval = 5




def get_pod_status_dict( ko ):

    pod_status_dict = {}
    pod_dict = ko.get_pod_dict_for_all_ns()
    for pod_name in pod_dict.keys():
        stat_dict = pod_dict[pod_name]['containers_list_status'][0]
        pod_status_dict[stat_dict.name] = {}
        if stat_dict.ready is True:
           status='ready'
        else:
           status='Not ready'
        restart_count = stat_dict.restart_count
        #pod_status_dict[stat_dict.name] = { "label": stat_dict.name, "value": restart_count }
        pod_status_dict[stat_dict.name] = restart_count
    print(len(pod_status_dict))
    return pod_status_dict    




def get_count_of_pods_restarted( pod_dict ):
    pods_restarted = 0
    for node_name in pod_dict.keys():
        for pod_name in pod_dict[node_name].keys():
            restart_count = int( pod_dict[node_name][pod_name]['containers_list_status'][0].restart_count )
            if restart_count > 0:
               pods_restarted = pods_restarted + 1
    return pods_restarted



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



def get_k8_core_components_table_points(ko):
    k8_core_dict = ko.get_k8_core_components_status()
    core_table_points = [ [ 'Name of K8 Core Component', 'SelfLink', 'Is Component Currently Running', 'Health Status', 'Errors' ] ]
    for comp in k8_core_dict.keys():
        row_points = [ comp, k8_core_dict[comp]['self_link'], k8_core_dict[comp]['conditions'][0].status,
            k8_core_dict[comp]['conditions'][0].type, k8_core_dict[comp]['conditions'][0].error ]
        core_table_points.append(row_points)
    return core_table_points




def get_k8_logs_table_points(ko):
    log_dict = ko.get_all_pod_logs()
    log_table_points = [ [ 'PodName', 'Last10Logs'] ]
    for pod_name in log_dict['default'].keys():
        row_point = [ pod_name, log_dict['default'][pod_name] ]
        log_table_points.append(row_point)
    #print(log_table_points)
    return log_table_points
            



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

            #print(pod_dict[node_name][pod_name]['container_dict']['volume_mounts'])
            vol_mounts_str = ""
            for vol_mount in pod_dict[node_name][pod_name]['container_dict']['volume_mounts']:
                vol_mounts_str = vol_mounts_str + ' ' + vol_mount

            pod_restart_count = pod_dict[node_name][pod_name]['containers_list_status'][0].restart_count
            start_time = pod_dict[node_name][pod_name]['start_time'].strftime("%m/%d/%Y, %H:%M:%S")
            #print(pod_dict[node_name][pod_name])
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
    #print(res_dict)
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
    mem_bar_chart_points = [ [ 'Container', 'MemUsage' ] ]
    mem_mib_dict = {}
    for node in [ 'node1', 'node2', 'node3']:
        for container_name in res_dict[node].keys():
            if re.search( 'k8s_pen', container_name ):
               mem_usage = 0
               #pod_pattern = "k8s_" + container_name
               #matching = [ s for s in res_dict[node].keys() if pod_pattern in  s ]
               mem_usage = res_dict[node][container_name]['mem_usage']
               mem_mib_dict[container_name] = get_mem_in_mib(mem_usage)

    for container_name in mem_mib_dict.keys():
        match = re.search( 'k8s_pen-([a-z\_\-0-9]+)', container_name )
        mini_container_name = match.group(1)
        n_list = [ mini_container_name, mem_mib_dict[container_name] ]
        #print(n_list)
        mem_bar_chart_points.append(n_list)
    print(mem_bar_chart_points)
    return mem_bar_chart_points
    

##
##

ko = kubernetes_lib.KubernetesConnect( log, k8_master_ip, k8_cert_file, k8_key_file )

mdb   = mongodb_lib.mongoClientObj( log, mongodb_host, username = mongodb_username,
        password = mongodb_password, port = mongodb_port )

#hdl_dict = sys_utils.get_node_hdl_dict( psm_cluster_dict )

#res_dict = get_containers_resource_dict( hdl_dict )
#get_containers_memory_use_chart_points( res_dict, venice_container_list )
# To DO
#ko.get_events_for_all_ns()


for i in range(1,15):

    pod_dict = ko.get_cluster_pod_dict_for_all_ns()
    pod_list = get_total_pod_list( pod_dict )

    try:
       nodes_table_points = get_nodes_table_points( ko )   
       update_key_val( 'k8nodestable', 'points', nodes_table_points )
    except Exception as e:
       print('ERROR in posting K8 Nodes table {}'.format(e)) 

    try:
       pods_table_points = get_cluster_pods_table_points( pod_dict )   
       update_key_val( 'k8podstable', 'points', pods_table_points )
       update_key_val( 'k8podcount', 'current', len(pod_list) )
    except Exception as e:
       print('ERROR in posting K8 Nodes table {}'.format(e)) 


    try:
       pods_restarted = get_count_of_pods_restarted( pod_dict )
       update_key_val( 'k8podrestartcount', 'current', pods_restarted )
    except Exception as e:
       print('ERROR in posting Pod restart count {}'.format(e)) 

    try:
       res_dict = get_containers_resource_dict( hdl_dict )
       pod_mem_points = get_containers_memory_use_chart_points( res_dict, venice_container_list )
       update_key_val( 'podmemchart', "points", pod_mem_points )
    except Exception as e:
       print('ERROR in posting Pod Memory Table {}'.format(e)) 


    try:
       k8_core_table_points = get_k8_core_components_table_points( ko )
       update_key_val( 'k8corecomptable', 'points', k8_core_table_points )
    except Exception as e:
       print('ERROR in posting Core comp Table {}'.format(e)) 
 
    try:
       k8_logs_table_points = get_k8_logs_table_points( ko )
       update_key_val( 'k8logstable', 'points', k8_logs_table_points )
    except Exception as e:
       print('ERROR in posting K8 Logs Table {}'.format(e))


    try:
       mdb.switch_db( mongodb_name )
       docker_dict = mdb.get_record( docker_res_collection, { 'psm-cluster-name': psm_cluster_name } )
       res_dict = json.loads(docker_dict['docker-mem-info'])
       pod_mem_points = get_containers_memory_use_chart_points( res_dict, venice_container_list )
       update_key_val( 'podmemchart', "points", pod_mem_points )
    except Exception as e:
       print('ERROR in posting K8 Mem Table {}'.format(e))

    # Duration between refresh
    time.sleep(refresh_interval)
