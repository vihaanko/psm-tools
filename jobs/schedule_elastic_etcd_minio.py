#!/usr/bin/env python3

###
# Run this as a schedule job for every 1 min in crontab
# This script updates the Elastic, Etcd and Minio Dashboards
# Author - venksrin@pensando.io
###


import os
import sys
import re
import logging
import json
import time
import subprocess

sys.path.append('../lib')

from urllib import request, parse
import random
from datetime import datetime
from datetime import datetime

import minio_lib
import elastic_lib
import etcd_lib
import influxdb_lib
import mongodb_lib
import sys_utils
from sys_utils import update_val, update_key_val

# Input file
from input_file import *

logging.basicConfig( level=logging.INFO, filename="/tmp/mon_script.log", filemode='w')
logging.root.setLevel(logging.INFO)
log = logging.getLogger("mon")



refresh_interval = 5





def get_elastic_table_points( el_dict ):
    #get_elastic_cluster_node_metrics( master_, elastic_key_file, elastic_cert_file )

    head_line = [ 'Metric' ]

    node_list = el_dict['nodes']

    for node in node_list:
        head_line.append(node)
    el_table_points = [ head_line ]

    metric_list = list(el_dict['nodes_dict'][node_list[0]].keys()
            )
    for metric in metric_list:
        n_list = [ metric, ]
        for node in node_list:
            n_list.append( el_dict['nodes_dict'][node][metric] )
        el_table_points.append(n_list)
    print(el_table_points)
    return el_table_points



def get_elastic_docs_pie( el_dict ):

    pie_points = [ [ 'NodeMetric', 'DocsCount' ] ]
    node_list = el_dict['nodes']
    for node in node_list:
        for metric in [ 'docs_total', ]:
            #val1 = el_dict['nodes_dict'][node]['host'] + '.' + metric
            val1 = el_dict['nodes_dict'][node]['host']
            n_list = [ val1, el_dict['nodes_dict'][node][metric] ]
            pie_points.append(n_list)
    print(pie_points)
    return pie_points


def get_elastic_indexes_pie( el_dict ):

    pie_points = [ [ 'NodeMetric', 'IndexCount' ] ]
    node_list = el_dict['nodes']
    for node in node_list:
        for metric in [ 'index_total', ]:
            #val1 = el_dict['nodes_dict'][node]['host'] + '.' + metric
            val1 = el_dict['nodes_dict'][node]['host']
            n_list = [ val1, el_dict['nodes_dict'][node][metric] ]
            pie_points.append(n_list)
    print(pie_points)
    return pie_points





def get_cluster_etcd_dict( node1etcd, node2etcd, node3etcd ):

    etcd_dict = {}
    etcd_dict['node1'] = node1etcd.get_cluster_detailed_metrics()
    etcd_dict['node2'] = node2etcd.get_cluster_detailed_metrics() 
    etcd_dict['node3'] = node3etcd.get_cluster_detailed_metrics()
    return etcd_dict



def write_etcd_memory_data_to_influx( influx_client, db_name, etcd_cluster_dict ):

    measurement_name = 'etcd_memory'
    time_obj = datetime.now()
    current_time = datetime.strftime(time_obj, '%Y-%m-%dT%H:%M:%S.%fZ')

    for node_name in etcd_cluster_dict.keys():
        etcd_dict = etcd_cluster_dict[node_name]
        json_body_str = '''[
           {
              "measurement": "''' + str(measurement_name) + '''",
              "tags": {
                   "psm-node": "''' + str(node_name) + '''"
              },
              "time": "''' + str(current_time) + '''",
               "fields": {
                  "process_resident_memory_bytes": "''' + str(etcd_dict['process_resident_memory_bytes']) + '''",
                  "process_virtual_memory_bytes": "''' + str(etcd_dict['process_virtual_memory_bytes']) + '''",
                  "process_open_fds": "''' + str(etcd_dict['process_open_fds']) + '''"
               }
            }
        ]'''
        print(json_body_str)
        influx_client.write_measurement_point( db_name, measurement_name, json_body_str )




# Adding latency data to Influx DB for Timeseries.
def write_elastic_latency_data_to_influx( influx_client, db_name, el_dict ):
    measurement_name = 'elastic_latency'

    time_obj = datetime.now()
    current_time = datetime.strftime(time_obj, '%Y-%m-%dT%H:%M:%S.%fZ')

    for node_id in el_dict['nodes_dict'].keys():
        node_ip = el_dict['nodes_dict'][node_id]['host']
        val_dict = el_dict['nodes_dict'][node_id]
        json_body_str = '''[
           {
              "measurement": "''' + str(measurement_name) + '''",
              "tags": {
                     "psm-ip": "''' + str(node_ip) + '''"
              },
              "time": "''' + str(current_time) + '''",
               "fields": {
                    "indices_avg_get_time": "''' + str(val_dict['indices_avg_get_time_in_millis']) + '''",
                    "indices_search_query_avg_time": "''' + str(val_dict['indices_search_query_avg_time_in_millis']) + '''",
                    "indices_search_fetch_avg_time": "''' + str(val_dict['indices_search_fetch_avg_time_in_millis']) + '''",
                    "indices_search_suggest_avg_time": "''' + str(val_dict['indices_search_suggest_avg_time_in_millis']) + '''"
               }
            }
        ]'''
        print(json_body_str)
        influx_client.write_measurement_point( db_name, measurement_name, json_body_str )





# Generate the Elastic Latency Trend Charts ..
def get_elastic_latency_trend_chart_points_dict( influx, influx_db_name, measurement_name, tag_name, last_x_min=60 ):

    field_list_str='indices_avg_get_time,indices_search_query_avg_time,indices_search_fetch_avg_time,indices_search_suggest_avg_time'

    out_dict = influx.query_points_for_last_x_mins( influx_db_name, measurement_name, field_list_str, tag_name, last_x_min )   
    elastic_dict = influx.convert_raw_points_to_dict_of_x_elements(out_dict, 'psm-ip')
    print(elastic_dict)
    points_dict = {}
    for node_ip in elastic_dict.keys():
        points_dict[node_ip] = [] 
        node_points = [ [ 'Timestamp', 'GetTime', 'SearchQueryTime', 'SearchFetchTime', 'SearchSuggestTime' ] ]
        for timestamp in elastic_dict[node_ip].keys():
            val_points = []
            val_list = elastic_dict[node_ip][timestamp]
            val_points = [ timestamp, float(val_list[0]), float(val_list[1]), float(val_list[2]), float(val_list[3]) ]
            node_points.append(val_points)
        points_dict[node_ip] = node_points
    print(points_dict)
    return points_dict




def get_etcd_memory_trend_chart_points_dict( influx, influx_db_name, measurement_name, tag_name, last_x_min=60 ):

    field_list_str='process_resident_memory_bytes,process_virtual_memory_bytes,process_open_fds'
    out_dict = influx.query_points_for_last_x_mins( influx_db_name, measurement_name, field_list_str, tag_name, last_x_min )
    etcd_dict = influx.convert_raw_points_to_dict_of_x_elements(out_dict, 'psm-node')
    points_dict = {}
    for mem_type in [ 'process_resident_memory_bytes', 'process_virtual_memory_bytes', 'process_open_fds']: 
        points_dict[mem_type] = []
        mem_points = [ [ 'Timestamp', 'Node1.{}'.format(mem_type), 'Node2.{}'.format(mem_type), 'Node3.{}'.format(mem_type) ] ] 
        for timestamp in etcd_dict[node_name].keys():
            val_points = []
            val_list = etcd_dict[node_name][timestamp]
            if mem_type == "process_resident_memory_bytes":
               val_points = [ timestamp, float(etcd_dict['node1'][timestamp][0]), float(etcd_dict['node2'][timestamp][0]), float(etcd_dict['node3'][timestamp][0]) ]
            elif mem_type == "virtual_memory_bytes":
               val_points = [ timestamp, float(etcd_dict['node1'][timestamp][1]), float(etcd_dict['node2'][timestamp][1]), float(etcd_dict['node3'][timestamp][1]) ]
            else:
               val_points = [ timestamp, float(etcd_dict['node1'][timestamp][2]), float(etcd_dict['node2'][timestamp][2]), float(etcd_dict['node3'][timestamp][2]) ]
            mem_points.append(val_points)
        points_dict[mem_type] = mem_points
    print(points_dict)
    return points_dict
    




def get_etcd_cluster_metrics_table_points( cluster_dict ):
    #cluster_dict = etcd.get_cluster_detailed_metrics()
    etcd_table_points = [ [ 'Metric', 'Value' ] ]
    for metric in cluster_dict.keys():
        if not re.search( 'go_|debugging|mvcc', metric ):
           if re.search( 'e\+', cluster_dict[metric]):
              row_point = [ metric, str(float(cluster_dict[metric])) ]
           else:
              row_point = [ metric, cluster_dict[metric] ]
           etcd_table_points.append(row_point)
    #print(etcd_table_points)
    return etcd_table_points



def get_etcd_venice_objects_table_points( venice_dict ):
    #venice_dict = etcd.get_venice_config_count_dict()
    etcd_table_points = [ [ 'VeniceObject', 'KVCount' ] ]
    for venice_obj in venice_dict.keys():
        row_point = [ venice_obj, venice_dict[venice_obj] ]
        etcd_table_points.append(row_point)
    return etcd_table_points




# Pie chart for all Venice Objects ..

def get_etcd_venice_objects_pie_chart_slices( venice_dict ):
    #venice_dict = etcd.get_venice_config_count_dict()

    pie_points = [ [ 'VeniceObject', 'KVCount' ] ]
    for venice_obj in venice_dict.keys():
        n_list = [ venice_obj, venice_dict[venice_obj] ]
        pie_points.append(n_list)
    #print(pie_points)
    return pie_points





def get_minio_cluster_table_points( admin_dict ):
    cluster_points = [[ 'Online Disks', 'Total Buckets', 'Total Objects', 'Total Size in Bytes' ]]
    row_points = [ admin_dict['onlineDisks'], admin_dict['buckets_count'], admin_dict['objects_count'], admin_dict['total_size'] ]
    cluster_points.append(row_points)
    #print(cluster_points)
    return cluster_points



def get_minio_node_health_points( admin_dict ):
    node_health_points = [[ 'Node Ip Address', 'Access End Point', 'Uptime', 'Health State' ] ]
    node_dict = admin_dict['node_dict']
    for node in node_dict.keys():
        match = re.search( '([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+):[0-9]+', node )
        node_ip = match.group(1)
        node_points = [ node_ip, node, node_dict[node]['uptime'], node_dict[node]['state'] ]
        node_health_points.append(node_points)
    #print(node_health_points)
    return node_health_points



def get_minio_bucket_detail_points( minio_dict ):
    minio_bucket_points = [[ 'Venice Bucket Name', 'Object Count', 'Total Size in Bytes' ]]
    for bucket in minio_dict.keys():
        bucket_points = [ bucket, minio_dict[bucket]['object_count'], minio_dict[bucket]['total_size'] ]
        minio_bucket_points.append(bucket_points)
    print(minio_bucket_points)
    return minio_bucket_points   



def get_go_agent_table_points( go_dict ):

    go_points_dict = {}
    for node in go_dict.keys():
        go_points_dict[node] = {}
        go_table_points = [[ 'AgentName', 'ThreadCount', 'Alloc', 'TotalAlloc', 'Sys', 'Lookups', 'Mallocs', 'Frees', 'HeapAlloc', 'HeapSys', 'HeapIdle', 'HeapInuse', 'HeapReleased', 'HeapObjects', 'MSpan', 'MCache', 'BuckHashSys', 'GCSys', 'OtherSys', 'NextGC', 'LastGC' ] ]
        for agent in go_dict[node].keys():
            if 'Alloc' in go_dict[node][agent].keys():
               agent_dict = go_dict[node][agent]
               agent_point = [ agent, agent_dict['thread_count'], agent_dict['Alloc'], agent_dict['TotalAlloc'], agent_dict['Sys'], agent_dict['Lookups'], agent_dict['Mallocs'], agent_dict['Frees'], agent_dict['HeapAlloc'], agent_dict['HeapSys'], agent_dict['HeapIdle'], agent_dict['HeapInuse'], agent_dict['HeapReleased'], agent_dict['HeapObjects'], agent_dict['MSpan'], agent_dict['MCache'], agent_dict['BuckHashSys'], agent_dict['GCSys'], agent_dict['OtherSys'], agent_dict['NextGC'], agent_dict['LastGC' ] ]
               go_table_points.append(agent_point)
        go_points_dict[node] = go_table_points
    print(go_points_dict)
    return go_points_dict


def get_minio_bucket_count_pie_slices( minio_dict ):
    minio_bucket_points = [[ 'BucketName', 'TotalSize' ]]
    for bucket in minio_dict.keys():
        if int(minio_dict[bucket]['total_size']) != 0:
           bucket_points = [ bucket, minio_dict[bucket]['total_size'] ]
           minio_bucket_points.append(bucket_points)
    print(minio_bucket_points)
    return minio_bucket_points
    

    

##
##
# Main script starts here ..
##
##

es = elastic_lib.elasticConnect( log, k8_master_ip, elastic_key_file, elastic_cert_file )
influx = influxdb_lib.influxDBClient( log, host=influx_host, username=influx_user, password=influx_password, port=influx_port )

node1etcd = etcd_lib.etcdConnect( log, psm_cluster_dict['node1']['ip'], etcd_cert_file, etcd_key_file )
node2etcd = etcd_lib.etcdConnect( log, psm_cluster_dict['node2']['ip'], etcd_cert_file, etcd_key_file )
node3etcd = etcd_lib.etcdConnect( log, psm_cluster_dict['node3']['ip'], etcd_cert_file, etcd_key_file )

mdb   = mongodb_lib.mongoClientObj( log, mongodb_host, username = mongodb_username,
        password = mongodb_password, port = mongodb_port )



for i in range(1, 15):

    el_dict = es.get_cluster_detailed_dict()
    write_elastic_latency_data_to_influx( influx, influx_db_name, el_dict )


    try:
       el_table_points = get_elastic_table_points( el_dict )
       update_key_val( 'elastictable', 'points', el_table_points )
    except Exception as e:
       print('ERROR in posting Elastic Table {}'.format(e)) 


    try:
       el_doc_pie_slices = get_elastic_docs_pie( el_dict )
       update_key_val( 'elasticdocpie', 'slices', el_doc_pie_slices )
    except Exception as e:
       print('ERROR in posting Elastic Docs Pie {}'.format(e)) 

    try:
       el_index_pie_slices = get_elastic_indexes_pie( el_dict )
       update_key_val( 'elasticindexpie', 'slices', el_index_pie_slices )
    except Exception as e:
       print('ERROR in posting Elastic Indexess Pie {}'.format(e)) 


    el_points_dict = get_elastic_latency_trend_chart_points_dict(influx, influx_db_name, 'elastic_latency', 'psm-ip', last_x_min=100) 
    try:
       for node_name in psm_cluster_dict.keys():
           print(node_name)
           node_ip = psm_cluster_dict[node_name]['ip']
           exec( "%s=el_points_dict[node_ip]" % ( node_name + "elastictrend" ))
           widget_name = node_name + "elastictrend"
           print(widget_name)
           update_key_val( widget_name, "points", el_points_dict[node_ip] )
    except Exception as e:
       print('ERROR in posting Elastic latency trend {}'.format(e)) 
    


    # Starting etcd cases
    try:

       etcd_cluster_dict = get_cluster_etcd_dict( node1etcd, node2etcd, node3etcd )
       etcd_metrics_table_points1 = get_etcd_cluster_metrics_table_points( etcd_cluster_dict['node1'] )
       etcd_metrics_table_points2 = get_etcd_cluster_metrics_table_points( etcd_cluster_dict['node2'] )
       etcd_metrics_table_points3 = get_etcd_cluster_metrics_table_points( etcd_cluster_dict['node3'] )

       write_etcd_memory_data_to_influx( influx, influx_db_name, etcd_cluster_dict )

       update_key_val( 'node1etcdmetricstable', 'points', etcd_metrics_table_points1 )
       update_key_val( 'node2etcdmetricstable', 'points', etcd_metrics_table_points2 )
       update_key_val( 'node3etcdmetricstable', 'points', etcd_metrics_table_points3 )

    except Exception as e:
       print('ERROR Etcd Metrics table Posting failure {}'.format(e))
    

    try:
       venice_dict = node1etcd.get_venice_config_count_dict()
       etcd_venice_table_points = get_etcd_venice_objects_table_points( venice_dict )
       print(etcd_venice_table_points)
       update_key_val( 'etcdveniceobjstable', 'points', etcd_venice_table_points )

       etcd_venice_obj_pie_slices = get_etcd_venice_objects_pie_chart_slices( venice_dict )
       update_key_val( 'etcdvenicepiechart', 'slices', etcd_venice_obj_pie_slices )

    except Exception as e:
       print('ERROR Etcd Venice Objects KV table posting failure {}'.format(e))

 
    etcd_points_dict = get_etcd_memory_trend_chart_points_dict(influx, influx_db_name, 'etcd_memory', 'psm-node', last_x_min=10) 
    try:
       for mem_type in etcd_points_dict.keys():
           exec( "%s=etcd_points_dict[mem_type]" % ( mem_type + "etcdmemtrend" ))
           widget_name = mem_type + "etcdmemtrend"
           update_key_val( widget_name, "points", etcd_points_dict[mem_type] )
    except Exception as e:
       print('ERROR in posting Etcd Memory trend {}'.format(e)) 
    


    # Get all the PSM Minio Collection related data from Mongodb
    mdb.switch_db( mongodb_name )
    psm_dict = mdb.get_record( psm_minio_collection, { 'psm-cluster-name': psm_cluster_name } )

    try:
       cluster_summ_points = get_minio_cluster_table_points( json.loads(psm_dict['admin-info']) )
       update_key_val( 'minioclustertable', 'points', cluster_summ_points )
    except Exception as e:
       print('ERROR Posting the minio cluster table points  {}'.format(e))


    try:
       node_health_points = get_minio_node_health_points( json.loads(psm_dict['admin-info' ]) )
       update_key_val( 'minionodehealthtable', 'points', node_health_points )
    except Exception as e:
       print('ERROR Posting the minio Node health table points  {}'.format(e))


    try:
       minio_bucket_points = get_minio_bucket_detail_points( json.loads(psm_dict['bucket-info']) )
       update_key_val( 'miniobuckettable', 'points', minio_bucket_points )
       print(minio_bucket_points)
    except Exception as e:
       print('ERROR Posting the minio bucket table points  {}'.format(e))


    try:
       minio_pie_slices = get_minio_bucket_count_pie_slices( json.loads(psm_dict['bucket-info']) )
       update_key_val( 'miniopieslice', 'slices', minio_pie_slices )
    except Exception as e:
       print('ERROR Posting the minio pie slices  {}'.format(e))


    go_dict = mdb.get_record( go_profile_collection, { 'psm-cluster-name': psm_cluster_name } )
    print(go_dict)

    try:
       golang_agent_table_points = get_go_agent_table_points( json.loads(go_dict['alloc-info']) )

       for node in golang_agent_table_points.keys():
           exec( "%s=golang_agent_table_points[node]" %  ( node + "goagentalloctable"))
           widget_name = node + "goagentalloctable"
           update_key_val( widget_name, "points", golang_agent_table_points[node] )

    except Exception as e:
       print('ERROR golang Agent table points  {}'.format(e))

    # Duration between refresh
    time.sleep(refresh_interval)
