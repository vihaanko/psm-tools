#!/usr/bin/env python3

###
# Run this as a schedule job for every 5 min in crontab
# This script updates the Minio related information to Mondodb for the
# Minio dashboard. Collects information of the objects stored in the
# Minio storage cluster on PSM.
#
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

import minio_lib
import mongodb_lib


# Input file
from input_file import *


# PLEASE NOTE -- This script takes 1-4 mins to complete depending on the size
# of your Minio cluster, so schedule this to run once in 5 mins

logging.basicConfig( level=logging.INFO, filename="/tmp/mon_script.log", filemode='w')
logging.root.setLevel(logging.INFO)
log = logging.getLogger("mon")




def get_minio_cluster_table_points( admin_dict ):
    cluster_points = [[ 'OnlineDisks', 'TotalBuckets', 'TotalObjects', 'TotalSize' ]]
    row_points = [ admin_dict['onlineDisks'], admin_dict['buckets_count'], admin_dict['objects_count'], admin_dict['total_size'] ]
    cluster_points.append(row_points)
    print(cluster_points)
    return cluster_points
    


def get_minio_node_health_points( admin_dict ):
    node_health_points = [[ 'EndPoint', 'Uptime', 'HealthState' ] ]
    node_dict = admin_dict['node_dict']
    for node in node_dict.keys():
        node_points = [ node, node_dict[node]['uptime'], node_dict[node]['state'] ]
        node_health_points.append(node_points)
    print(node_health_points)
    return node_health_points




##
##
# Main script starts here ..


# Connect to DBs ..
minio = minio_lib.mcObject( log, psm_cluster_dict['node1']['ip'], minio_public_cert_file, minio_private_key_file )
mdb   = mongodb_lib.mongoClientObj( log, mongodb_host, username = mongodb_username,
        password = mongodb_password, port = mongodb_port )



# Fetch Minio information
admin_dict = minio.get_admin_info_dict()
minio_dict = minio.get_detailed_minio_dict()



# If you are not able to create Mondo db and collections manually first time, please
# uncomment the following section and run for the first time.

# Create Mongo Database
#mdb.create_database( mongodb_name )
# Create Collections
#mdb.create_collection( mongodb_name, psm_resource_collection )
#mdb.create_collection( mongodb_name, psm_minio_collection )
#mdb.insert_record( psm_minio_collection, { 'psm-cluster-name': psm_cluster_name, 'admin-info': json.dumps(admin_dict),    'bucket-info': json.dumps(minio_dict) } )


mdb.switch_db( mongodb_name )
mdb.update_record( psm_minio_collection, { 'psm-cluster-name': psm_cluster_name }, { 'psm-cluster-name': psm_cluster_name, 'admin-info': json.dumps(admin_dict),    'bucket-info': json.dumps(minio_dict) } )
