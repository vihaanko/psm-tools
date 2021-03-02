#!/usr/bin/env python3


###
# Library with the common system utilities to be used by Smashing dashboard
#
# Author - venksrin@pensando.io
###


import os
import sys
import re
import os
import subprocess
import json

from urllib import request, parse

import paramiko
import netmiko
from netmiko import ConnectHandler
from netmiko import redispatch


# Input file
sys.path.append('../jobs/')
from input_file import *



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




def get_node_hdl_dict( cluster_dict ):
    hdl_dict = {}
    for node_name in cluster_dict.keys():
        print('Connecting to Node {}'.format(cluster_dict[node_name]['ip']))
        hdl_dict[node_name] = ConnectHandler( ip=cluster_dict[node_name]['ip'], device_type='linux', username=cluster_dict[node_name]['username'], password=cluster_dict[node_name]['password'] )
    return hdl_dict




def run_command(cmd):
    """ run_command - runs the command on the local machine and returns output """
    output = subprocess.getoutput(cmd)
    #print(output)
    return output




def get_cluster_cpu_summary_dict( hdl_dict, sar_cmd = '/var/log/pensando/sar' ):
    cpu_summary_dict = {}
    for node_name in hdl_dict.keys():
        cpu_out = hdl_dict[node_name].send_command('{} -u 1 1'.format(sar_cmd))
        match = re.search( 'Average:\s+all\s+[0-9\.]+\s+[0-9\.]+\s+[0-9\.]+\s+[0-9\.]+\s+[0-9\.]+\s+([0-9\.]+)', cpu_out )
        cpu_free = float(match.group(1))
        cpu_use = 100.0 - cpu_free
        cpu_summary_dict[node_name] = float('{0:.2f}'.format(round(cpu_use,2)))
    return cpu_summary_dict



def get_cluster_memory_summary_dict( hdl_dict ):
    mem_summary_dict = {}
    for node_name in hdl_dict.keys():
        mem_out = hdl_dict[node_name].send_command('/usr/bin/free -g')
        match = re.search( 'Mem:\s+([0-9\.]+)\s+[0-9\.]+\s+[0-9\.]+\s+[0-9\.]+\s+[0-9\.]+\s+([0-9\.]+)', mem_out )
        total_mem = int(match.group(1))
        avail_mem = int(match.group(2))
        print(total_mem,avail_mem)
        mem_free_per = ((total_mem - avail_mem)*100)/total_mem
        mem_summary_dict[node_name] = float('{0:.2f}'.format(round(mem_free_per,2)))
    return mem_summary_dict




def get_cluster_disk_summary_dict( hdl_dict ):
    disk_summary_dict = {}
    for node_name in hdl_dict.keys():
        df_out = hdl_dict[node_name].send_command('df -h /')
        match = re.search( '([0-9]+)% /', df_out )
        disk_summary_dict[node_name] = match.group(1)
    print(disk_summary_dict)
    return disk_summary_dict



def get_disk_usage_dict( hdl, df_cmd = '/usr/bin/df -k' ):
    disk_dict = {}
    df_out = hdl.send_command(df_cmd)
    out_lines = df_out.split( "\n" )
    for line in out_lines:
        if re.search( '[0-9]+%\s[\/a-zA-Z0-9\_]+', line ):
           match = re.search( '([0-9]+)[\s]+([0-9]+)[\s]+([0-9]+)%\s([\/a-zA-Z0-9\_]+)', line )
           used = int(match.group(1))
           use_percent = float(match.group(3))
           dir_nam = match.group(4)
           file_list = dir_nam.split( "/")
           if len(file_list) > 2:
              match = re.search( '^(\/[a-zA-Z0-9\_\-]+\/[a-zA-Z0-9\_\-]+)', dir_nam )
              directory = match.group(1)
              if directory in disk_dict:
                 disk_dict[directory] = disk_dict[directory] + int(used)
              else:
                 disk_dict[directory] = int(used)
           else:
              disk_dict[dir_nam] = int(used)

    print(disk_dict)
    return disk_dict




def get_memory_usage_dict( hdl, ps_mem_cmd='/var/log/pensando/ps_mem.py' ):
    mem_dict = {}
    ps_out = hdl.send_command(ps_mem_cmd )
    out_lines = ps_out.split( "\n" )
    for line_t in out_lines:
        line = line_t.replace( "\t", "    " )
        print(line)
        if re.search( 'iB\s+[a-zA-Z\-\_0-9]', line ):
           match = re.search( '\=[\s]+([0-9\.]+)\s([KMGiB]+)\s+([a-zA-Z\-\_0-9]+)', line )
           print(match)
           tmp_proc_mem = match.group(1)
           mem_unit = match.group(2)
           proc_name = match.group(3)
           mem_dict[proc_name] = {}
           if mem_unit == "KiB":
              proc_mem = float(tmp_proc_mem) * 0.000976
           elif mem_unit == "GiB":
              proc_mem = float(tmp_proc_mem) * 1024
           else:
              proc_mem = tmp_proc_mem
           mem_dict[proc_name] = float(proc_mem)
    print(mem_dict)
    return mem_dict



def get_cluster_process_memory_distribution_dict( hdl_dict, ps_mem_cmd='/var/log/pensando/ps_mem.py' ):

    mem_dist_dict = {}
    for node in hdl_dict.keys():
        mem_dist_dict[node] = {}
        mem_dist_dict[node] = get_memory_usage_dict( hdl_dict[node], ps_mem_cmd )
    return mem_dist_dict





def get_cluster_log_summary_dict( hdl_dict ):
    log_dict = {}
    for node in hdl_dict.keys():
        log_dict[node] = {}
        for log_type in [ 'error', 'info', 'debug', 'warn' ]:
            cmd = """grep '\"level\":\"{}\"' /var/log/pensando/*.log | wc -l""".format(log_type)
            print(cmd)
            out = hdl_dict[node].send_command(cmd)
            print(out)
            match = re.search( '([0-9]+)', out )
            log_dict[node][log_type] = int(match.group(1))
    return log_dict



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

