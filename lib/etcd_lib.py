#!/usr/bin/env python3

###
# Library to collect to Etcd in a Kubernetes cluster and fectch various etcd related Metics
# and details of various PSM objects stored in Etcd.
# Author: venksrin@pensando.io
###

from etcd3 import Client
import os
import sys
import re
import logging


sys.path.append('../jobs')

from input_file import *


class etcdConnect():

    def __init__(self, log, server_ip, cert_file, key_file, port=5002 ):


       self.log               = log
       self.server_ip         = server_ip
       self.port              = port
       self.cert_file         = cert_file
       self.key_file          = key_file
       self.client            = None
       print(self.server_ip, self.port, self.cert_file, self.key_file )
       self.client = Client( self.server_ip, self.port, cert=( self.cert_file, self.key_file ), verify=False )
       print(self.client)



    def get_cluster_version( self, ):
        return (self.client.cluster_version)


    def get_cluster_dict( self, ):
        cluster_dict = {}
        cobj = self.client.member_list()
        cluster_dict['cluster_id'] = cobj.header.cluster_id
        cluster_dict['member_dict'] = {}
        for mem_obj in cobj.members:
            mem_id = str(mem_obj.ID)
            cluster_dict['member_dict'][mem_id] = {}
            cluster_dict['member_dict'][mem_id]['name'] = mem_obj.name
            cluster_dict['member_dict'][mem_id]['peerurls'] = mem_obj.peerURLs[0]
            cluster_dict['member_dict'][mem_id]['clienturls'] = mem_obj.clientURLs
        print(cluster_dict)
        return cluster_dict


    def get_cluster_detailed_metrics( self, ):
        metrics_dict = {}
        output = self.client.metrics_raw()
        for line in output.split("\n"):
            if not re.search( '^#', line ):
               if re.search( '([a-zA-Z\_]+)[\s]+([0-9\.\+e]+)', line ):
                  match = re.search( '([a-zA-Z\_]+)[\s]+([0-9\.\+e]+)', line )
                  metrics_dict[match.group(1)] = match.group(2)
        print(metrics_dict)
        return metrics_dict

        

    def get_venice_config_count_dict(self, etcd_key_list = venice_etcd_keys ):
        venice_config_count_dict = {}
        for key_nam in etcd_key_list:
            obj = self.client.range( key=key_nam, prefix=True , count_only=True )
            venice_config_count_dict[key_nam] = int(obj.count)
        print(venice_config_count_dict)
        return venice_config_count_dict
    
  
    def get_venice_config_dict(self, etcd_key_list = venice_etcd_keys ):
        venice_config_dict = {}
        for key_nam in etcd_key_list:
            obj = self.client.range( key=key_nam, prefix=True )
            venice_config_dict[key_nam] = obj.kvs
        print(venice_config_dict)
        return venice_config_dict
      

    def get_venice_config_value( self, key_prefix ):
        obj = self.client.range( key=key_prefix, prefix=True )
        return obj.kvs


