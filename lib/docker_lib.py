#!/usr/bin/env python3


###
# Library to collect some of the Docker command outputs from K8 Nodes
# Author - venksrin@pensando.io
###

import os
import sys
import re
import logging
import time
import json
import pprint


import paramiko
import netmiko
from netmiko import ConnectHandler
from netmiko import redispatch

pp = pprint.PrettyPrinter(indent=2)



class DockerObject():

    def __init__(self, log, host_ip, username, password, os_type='linux', ssh_lib='netmiko' ):

        self.log           = log
        self.host_ip       = host_ip
        self.username      = username
        self.password      = password
        self.os_type       = os_type
        self.ssh_lib       = ssh_lib
        self.hdl           = None
        self.ps_dict       = None
        self.ps_all_dict   = None
        # Get Host Handle

        # Ssh to Host and create Handle
        if re.search( 'unicon', self.ssh_lib, re.I ):
           self.hdl = Connection( hostname='host', start=[ 'ssh {0}@{1}'.format( self.username, self.host_ip) ], os=self.os_type, password=password )
           self.hdl.execute('stty cols 500')
        else:
           self.hdl = ConnectHandler( ip=self.host_ip, device_type=self.os_type, username=self.username, password=self.password )
           self.hdl.execute('stty cols 500')




    # Converts the formatted docker ouput to Json and then converts to dictionary ..
    def convert_docker_out_to_dict(self, cmd_out ):
        dict_out = json.loads( "{ " + cmd_out.rstrip(",") + " }" )
        pp.pprint(dict_out)
        self.log.info(dict_out)
        return dict_out  



    # Returns a list of dicts for each container ..
    # By default the all option is off
    def get_ps_dict(self, all=False):

        """
        Returns output of 'docker ps' command in Dictionary format.
        Set all flag True to get all containers including the ones stopped
        Key for the dict is "Names" and has the following fields ..
        1. Command
        2. CreatedAt
        3. ID
        4. Image
        5. LocalVolumes
        6. Mounts
        7. Names
        8. Networks
        9. Ports
        10. RunningFor
        11. Size
        12. Status
        """

        docker_ps_dict = {}

        if all:
           docker_cmd = 'docker ps -a --no-trunc --format'
        else:
           docker_cmd = 'docker ps --no-trunc --format'

        format_options = '"\\"{{.Names}}\\": { \\"Names\\": \\"{{.Names}}\\", \\"Command\\": \"{{.Command}}\", \\"CreatedAt\\": \\"{{.CreatedAt}}\\", \\"ID\\": \\"{{.ID}}\\", \\"Image\\": \\"{{.Image}}\\", \\"LocalVolumes\\": \\"{{.LocalVolumes}}\\", \\"Mounts\\": \\"{{.Mounts}}\\", \\"Networks\\": \\"{{.Networks}}\\", \\"Ports\\": \\"{{.Ports}}\\", \\"RunningFor\\": \\"{{.RunningFor}}\\", \\"Size\\": \\"{{.Size}}\\", \\"Status\\": \\"{{.Status}}\\" },"'

        docker_cmd = docker_cmd + '=' + format_options
        print(docker_cmd)

        #self.hdl.send_command('stty cols 500')
        cmd_out = self.hdl.execute(docker_cmd)
        ps_dict = self.convert_docker_out_to_dict(cmd_out)
        return ps_dict


    def get_containers_list(self,):
        ps_dict = self.get_ps_dict()
        print(list(ps_dict.keys()))
        return(list(ps_dict.keys()))


    def get_all_containers_list(self,):
        ps_dict = self.get_ps_dict( all=True )
        print(list(ps_dict.keys()))
        return(list(ps_dict.keys()))
 

    def get_containers_not_running_list(self, ):
        containers_not_running_list = []
        ps_dict = self.get_ps_dict( all=True )
        for container_name in ps_dict.keys():
            if not re.search( 'Up', ps_dict[container_name]['Status'], re.I ):
               containers_not_running_list.append(container_name)
        print(containers_not_running_list)
        return containers_not_running_list

    def get_containers_not_running_dict(self, ):
        containers_not_running_dict = {}
        ps_dict = self.get_ps_dict( all=True )
        for container_name in ps_dict.keys():
            if not re.search( 'Up', ps_dict[container_name]['Status'], re.I ):
               containers_not_running_dict[container_name] = {}
               containers_not_running_dict[container_name] = ps_dict[container_name]
        print(containers_not_running_dict)
        return containers_not_running_dict


    def get_version_dict(self, all=False):
        docker_cmd = 'docker version --format="{{json .}}"'
        cmd_out = self.hdl.execute(docker_cmd)
        version_dict = json.loads(cmd_out)
        self.log.info(version_dict)
        return version_dict


    def get_logs(self, container_name):
        docker_cmd = 'docker logs {}'.format(container_name)
        cmd_out = self.hdl.execute(docker_cmd)
        self.log.info(cmd_out)
        return cmd_out


    def get_resource_usage_dict(self, ):

        """
        get_stats_dict - Method to get the Container system level statistics
        Can be used for all the Resource leak verifications by taking snapshots ..
        """

        docker_stats_dict = {}
        docker_cmd = 'docker stats --no-stream --format'
        format_options = '"\\"{{.Name}}\\": { \\"Name\\": \\"{{.Name}}\\", \\"BlockIO\\": \\"{{.BlockIO}}\\", \\"CPUPerc\\": \\"{{.CPUPerc}}\\", \\"Container\\": \\"{{.Container}}\\", \\"ID\\": \\"{{.ID}}\\", \\"MemPerc\\": \\"{{.MemPerc}}\\", \\"MemUsage\\": \\"{{.MemUsage}}\\", \\"NetIO\\": \\"{{.NetIO}}\\", \\"PIDs\\": \\"{{.PIDs}}\\" },"'
        docker_cmd = docker_cmd + '=' + format_options
        print(docker_cmd)
        cmd_out = self.hdl.execute(docker_cmd)
        stats_dict = self.convert_docker_out_to_dict(cmd_out)
        pp.pprint(stats_dict)
        return stats_dict
    
     
    def get_info_dict(self, ):
        """
        get_info - Get system wide docker information as a dict
        Monitor Key items like ContainersRunning, ContainersStopped, Memory  etc.
        """
        docker_cmd = 'docker info --format="{{json .}}"'
        cmd_out = self.hdl.execute(docker_cmd)
        info_dict = json.loads(cmd_out)
        self.log.info(info_dict)
        return info_dict


    def get_inspect_dict(self, container_name ):

        """
        get_inspect_dict - Gives the complete details of a container ..
        Check for State->Status, State->Dead, etc.
        """

        inspect_dict = {} 
        docker_cmd = 'docker inspect --format="{{json .}}"' + ' ' + container_name
        cmd_out = self.hdl.execute(docker_cmd)
        inspect_dict = json.loads(cmd_out)
        self.log.info(inspect_dict)
        pp.pprint(inspect_dict)
        return inspect_dict

   

    def get_health_dict(self, container_name):
        """
        get_health_dict - Returns the health status dict of a container

{"Status":"running","Running":true,"Paused":false,"Restarting":false,"OOMKilled":false,"Dead":false,"Pid":3060,"ExitCode":0,"Error":"","StartedAt":"2019-12-07T16:04:05.732225011Z","FinishedAt":"0001-01-01T00:00:00Z"}
        """
        status_dict = {}
        docker_cmd = 'docker inspect --format="{{json .State}}" ' + container_name
        docker_out = self.hdl.execute(docker_cmd)
        health_dict = json.loads(docker_out)
        print(health_dict)
        return health_dict


    def get_events_dict(self, container_name ):
        events_dict = {}
        docker_cmd = 'docker events --format="{{json .}}" --until "1s"'
        # Work to be done ..
 
