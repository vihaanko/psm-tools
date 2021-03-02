#!/usr/bin/env python3


###
# Library to connect to Minio cluster running on PSM via Python SDK APIs and mc,
# Collect the Minio cluster Metrics
#
# Author: venksrin@pensando.io
###


import urllib3
from minio import Minio
import os
import re
import sys
import json
import subprocess
import logging


from input_file import *



def run_command(cmd):
    """ run_command - runs the command on the local machine and returns output """
    output = subprocess.getoutput(cmd)
    return output



class minioClusterObject( ):

    """
    minioClient - Creates a client object to connect to PSM Minio.

    1. In latest releases the minioaccess key and password will be dynamically generated as part of cluster
       installation and for this we need the privatekey file and public cert file from the PSM cluster 
       which is available under - /var/lib/pensando/pki/pen-vos/certs
    2. Then use the files and fetch the accesskey, passwor using
       curl --key ./private.key --cert ./public.crt --insecure https://{master-ip}:9052/debug/minio/credentials
    3. Use this the access key and password and connect to the cluster via Python SDK.

    """

    def __init__(self, log, master_ip, private_key_file, public_cert_file, vos_port = 9052,
        minio_port = 19001, curl_cmd='/usr/local/bin/curl' ):

        self.log                   = log
        self.master_ip             = master_ip
        self.private_key_file      = private_key_file
        self.public_cert_file      = public_cert_file
        self.vos_port              = vos_port
        self.minio_port            = minio_port
        self.curl_cmd              = curl_cmd



    def connect_to_cluster( self, ):

        cmd = '{} -s --key {} --cert {} --insecure https://{}:{}/debug/minio/credentials'.format( 
                 self.curl_cmd, self.private_key_file, self.public_cert_file, self.master_ip, self.vos_port )
        out_dict = json.loads(run_command(cmd))
        if 'MINIO_ACCESS_KEY' not in out_dict:
            print('ERROR !! Failed to get the Mini access keys')
            log.error('ERROR !! Failed to get the Mini access keys')
            return 
        else:
            self.minio_access_key      = out_dict['MINIO_ACCESS_KEY']
            self.minio_secret_key      = out_dict['MINIO_SECRET_KEY']


        self.http_client           = urllib3.PoolManager( timeout=urllib3.Timeout.DEFAULT_TIMEOUT,
                                     cert_reqs='CERT_REQUIRED',
                                     ca_certs=self.public_cert_file,
                                     retries=urllib3.Retry( total=5, backoff_factor=0.2,
                                     status_forcelist=[500, 502, 503, 504] ))
        try: 
            self.client            = Minio( "{}:{}".format(self.master_ip, self.minio_port), 
                                     access_key = self.minio_access_key, 
                                     secret_key = self.minio_secret_key, secure=True,
                                     http_client = self.http_client )
        except Exception as e:
            log.error('Failed to connect to Minio cluster - {}'.format(e))
            print('Failed to connect to Minio cluster - {}'.format(e))
        print(self.client)



    def get_bucket_objects( self, ):
        print('Getting buckets')
        bucket_obj_list = self.client.list_buckets()
        print(bucket_obj_list)
        return bucket_obj_list


    def get_buckets( self, ):
        bucket_list = []
        for bucket in self.get_bucket_objects():
            print(dir(bucket))
            bucket_list.append(bucket.name)
        return bucket_list





class mcObject():

    def __init__(self, log, server_ip, public_cert_file, key_file, obs_parent='local/',
       port=9052, mc_cmd = '/usr/bin/mc', curl_cmd = '/usr/local/bin/curl' ):

       self.log              = log
       self.server_ip        = server_ip
       self.port             = port
       self.public_cert_file = public_cert_file
       self.key_file         = key_file
       self.mc_cmd           = mc_cmd
       self.obs_parent       = obs_parent


       # The accesskey and secret key are generated dynamically during the minio cluster install
       # So we have to first acquire that and add it under <user>/.mc/config.json 

       cmd = '{} -v -k --key {} --cert {} https://{}:{}/debug/minio/credentials --json'.format( curl_cmd,
             self.server_ip, self.port, self.public_cert_file, self.key_file )
       output = run_command( cmd )
       # To do .. Add accesskey generation and saving to the config.json

       
    def get_admin_info_dict(self, ):
        cmd = '{} admin info {} --json --insecure'.format( self.mc_cmd, self.obs_parent )
        print(cmd)
        out_dict = json.loads(run_command( cmd ))
        cluster_dict = {}
        cluster_dict['buckets_count'] = out_dict['info']['buckets']['count']
        cluster_dict['objects_count'] = out_dict['info']['objects']['count']
        cluster_dict['total_size'] = out_dict['info']['usage']['size']
        cluster_dict['onlineDisks'] = out_dict['info']['backend']['onlineDisks']
        cluster_dict['node_dict'] = {}
        for node_dict in out_dict['info']['servers']:
            endpoint = node_dict['endpoint']
            cluster_dict['node_dict'][endpoint] = {}
            cluster_dict['node_dict'][endpoint]['state'] = node_dict['state']
            cluster_dict['node_dict'][endpoint]['uptime'] = node_dict['uptime']
        print(cluster_dict)
        return cluster_dict


    def get_top_level_buckets_list(self, ):
        bucket_list = []
        cmd = '{} ls {} --insecure'.format( self.mc_cmd, self.obs_parent )
        print(cmd)
        output = run_command( cmd )
        for line in output.split("\n"):
            match = re.search( 'B\s([a-z0-9\-\.A-Z\/]+)', line )
            bucket_list.append( match.group(1)) 
        print(bucket_list)
        return bucket_list
      

    def get_detailed_minio_dict(self, ):
        bucket_dict = {}
        bucket_list = self.get_top_level_buckets_list()
        for bucket in bucket_list:
            bucket_dict[bucket] = {}
            cmd = '{} ls local/{} --summarize --insecure --recursive --json | tail -5'.format( self.mc_cmd, bucket )
            output = run_command( cmd )
            match = re.search( '\"totalObjects\":([0-9]+),\"totalSize\":([0-9]+)', output ) 
            bucket_dict[bucket]['object_count'] = int( match.group(1))
            bucket_dict[bucket]['total_size'] = int( match.group(2))
        print(bucket_dict)
        return bucket_dict


#logging.basicConfig( level=logging.INFO, filename="/tmp/venk_script.log", filemode='w')
#logging.root.setLevel(logging.INFO)
#log = logging.getLogger("mon")


#mcobj = mcObject( log, '20.0.0.107', minio_public_cert_file, minio_private_key_file )
#mcobj.get_admin_info_dict()
#mcobj.get_top_level_buckets_list()
#mcobj.get_detailed_minio_dict()
