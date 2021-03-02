#!/usr/bin/env python3


###
# Library for connecting to Elastic cluster via Python SDK and fetching various
# Metrics related to the Elastic cluster.
#
# Author - venksrin@pensando.io
###


import urllib3
import ssl
import elasticsearch
from elasticsearch import Elasticsearch, helpers
#from elasticsearch.connection import create_ssl_context
from elasticsearch.connection import RequestsHttpConnection

import os
import re
import sys
import json
import subprocess
import logging




def run_command(cmd):
    """ run_command - runs the command on the local machine and returns output """
    output = subprocess.getoutput(cmd)
    print(output)
    return output




# Elastic is organized as Indices = DB, Type = Table and Documents = Row in a Table.

class elasticConnect():

    def __init__(self, log, master_ip, key_file, cert_file, elastic_port=9200, verify_certs=False, curl_cmd='/usr/local/bin/curl' ):

        self.log                 = log
        self.master_ip           = master_ip
        self.key_file            = key_file
        self.cert_file           = cert_file
        self.elastic_port        = elastic_port
        self.es                  = None
        self.verify_certs        = verify_certs
        self.curl_cmd            = curl_cmd


        #ssl_context                   = create_ssl_context() 
        #ssl_context.check_hostname    = False
        #ssl_context.verify_mode       = ssl.CERT_NONE
        #print(ssl_context.verify_mode)

        # Please note there is a bug in elastic SDK and have to use the connection only in this mode
        # with the InsecureRequest warning thrown with every call.
        try:
            self.es = Elasticsearch( 'https://{}:{}'.format(self.master_ip, self.elastic_port),
                    verify_certs=False, client_cert = cert_file, client_key = key_file,
                    connection_class=RequestsHttpConnection, use_ssl=True )
            print(self.es)
        except Exception as e:
            log.error('ERROR connecting to Elastic Master {} Exception {}'.format(self.master_ip, e ))
            print('ERROR connecting to Elastic Master {} Exception {}'.format(self.master_ip, e ))


    def get_cluster_health_dict( self, ):
        cluster_health_dict = self.es.cluster.health()
        print(cluster_health_dict)
        return cluster_health_dict


    def get_cluster_stats_dict( self, ):
        cluster_stats_dict = self.es.cluster.stats()
        print(cluster_stats_dict)
        return cluster_stats_dict


    def get_cluster_state_dict(self, ):
        cluster_state_dict = self.es.cluster.state()
        return cluster_state_dict


    def get_nodes_stats_dict(self, ):
        nodes_stats_dict = self.es.nodes.stats()
        return nodes_stats_dict


    def get_nodes_info_dict(self, ):
        nodes_info_dict = self.es.nodes.info()
        return nodes_info_dict


    # es.count()
    # es.cluster.client.info()
    # es.nodes.usage()
    def get_cluster_detailed_dict( self, ):
        es_dict = {}
        cs_state_dict = self.get_cluster_state_dict()
        node_dict = self.get_nodes_stats_dict()

        es_dict['cluster_name'] = cs_state_dict['cluster_name']
        es_dict['nodes'] = list(cs_state_dict['nodes'].keys())
        es_dict['nodes_dict'] = {}
        print(node_dict)
        for node_id in node_dict['nodes']:
            print(node_id)
            nodeid_dict = node_dict['nodes'][node_id]
            es_dict['nodes_dict'][node_id] = {}
            es_dict['nodes_dict'][node_id]['host'] = nodeid_dict['host']
            es_dict['nodes_dict'][node_id]['docs_total'] = nodeid_dict['indices']['docs']['count']
            es_dict['nodes_dict'][node_id]['docs_deleted'] = nodeid_dict['indices']['docs']['deleted']
            es_dict['nodes_dict'][node_id]['indices_size_in_bytes'] = nodeid_dict['indices']['store']['size_in_bytes']
            es_dict['nodes_dict'][node_id]['index_total'] = nodeid_dict['indices']['indexing']['index_total']
            es_dict['nodes_dict'][node_id]['index_failed'] = nodeid_dict['indices']['indexing']['index_failed']
            es_dict['nodes_dict'][node_id]['index_deleted'] = nodeid_dict['indices']['indexing']['delete_total']
            es_dict['nodes_dict'][node_id]['indices_get_total'] = nodeid_dict['indices']['get']['total']
            indices_dict = nodeid_dict['indices']
            es_dict['nodes_dict'][node_id]['indices_get_time_in_millis'] = indices_dict['get']['time_in_millis']
            if indices_dict['get']['total'] > 0:
               es_dict['nodes_dict'][node_id]['indices_avg_get_time_in_millis'] = float('{0:.3f}'.format(round(indices_dict['get']['time_in_millis']/indices_dict['get']['total'], 3) ))
            else:
               es_dict['nodes_dict'][node_id]['indices_avg_get_time_in_millis'] = 0
            es_dict['nodes_dict'][node_id]['indices_search_query_total'] = indices_dict['search']['query_total']
            es_dict['nodes_dict'][node_id]['indices_search_query_total_time_in_millis'] = indices_dict['search']['query_time_in_millis']
            if indices_dict['search']['query_total'] > 0:
               es_dict['nodes_dict'][node_id]['indices_search_query_avg_time_in_millis'] = float('{0:.3f}'.format(round(indices_dict['search']['query_time_in_millis']/indices_dict['search']['query_total'], 3)))
            else:
               es_dict['nodes_dict'][node_id]['indices_search_query_avg_time_in_millis'] = 0

            es_dict['nodes_dict'][node_id]['indices_search_fetch_total'] = indices_dict['search']['fetch_total']
            es_dict['nodes_dict'][node_id]['indices_search_fetch_total_time_in_millis'] = indices_dict['search']['fetch_time_in_millis']
            if int(indices_dict['search']['fetch_total']) > 0:
               es_dict['nodes_dict'][node_id]['indices_search_fetch_avg_time_in_millis'] = float('{0:.3f}'.format(round(indices_dict['search']['fetch_time_in_millis']/indices_dict['search']['fetch_total'], 3)))
            else:
               es_dict['nodes_dict'][node_id]['indices_search_fetch_avg_time_in_millis'] = 0

            es_dict['nodes_dict'][node_id]['indices_suggest_total'] = indices_dict['search']['suggest_total']
            es_dict['nodes_dict'][node_id]['indices_search_suggest_total_time_in_millis'] = indices_dict['search']['suggest_time_in_millis']
            if int(indices_dict['search']['suggest_total']) > 0:
               es_dict['nodes_dict'][node_id]['indices_search_suggest_avg_time_in_millis'] = float( '{0:.3f}'.format(round(indices_dict['search']['suggest_time_in_millis']/indices_dict['search']['suggest_total'], 3 )) )
            else:
               es_dict['nodes_dict'][node_id]['indices_search_suggest_avg_time_in_millis'] = 0

            es_dict['nodes_dict'][node_id]['indices_query_cache_size_in_bytes'] = indices_dict['query_cache']['memory_size_in_bytes']
            es_dict['nodes_dict'][node_id]['indices_query_cache_total_count'] = indices_dict['query_cache']['total_count']
            es_dict['nodes_dict'][node_id]['indices_query_cache_hit_count'] = indices_dict['query_cache']['hit_count']
            es_dict['nodes_dict'][node_id]['indices_query_cache_miss_count'] = indices_dict['query_cache']['miss_count']
            es_dict['nodes_dict'][node_id]['indices_segments_count'] = indices_dict['segments']['count']
            es_dict['nodes_dict'][node_id]['indices_segments_memory_in_bytes'] = indices_dict['segments']['memory_in_bytes']


            os_dict = nodeid_dict['os']
            es_dict['nodes_dict'][node_id]['cpu_utilization'] = os_dict['cpu']['percent']
            es_dict['nodes_dict'][node_id]['cpu_load_avg_5m'] = os_dict['cpu']['load_average']['5m']
            es_dict['nodes_dict'][node_id]['total_memory_in_bytes'] = os_dict['mem']['total_in_bytes']
            es_dict['nodes_dict'][node_id]['free_memory_in_bytes'] = os_dict['mem']['free_in_bytes']
            es_dict['nodes_dict'][node_id]['used_memory_in_bytes'] = os_dict['mem']['used_in_bytes']
            es_dict['nodes_dict'][node_id]['free_memory_in_percent'] = os_dict['mem']['free_percent']
            es_dict['nodes_dict'][node_id]['used_memory_in_percent'] = os_dict['mem']['used_percent']

            proc_dict = os_dict = nodeid_dict['process']
            es_dict['nodes_dict'][node_id]['open_file_descriptors'] = proc_dict['open_file_descriptors']
            es_dict['nodes_dict'][node_id]['process_virtual_memory'] = proc_dict['mem']['total_virtual_in_bytes']

            jvm_dict = nodeid_dict['jvm']
            es_dict['nodes_dict'][node_id]['jvm_heap_mem_used_in_bytes'] = jvm_dict['mem']['heap_used_in_bytes']
            es_dict['nodes_dict'][node_id]['jvm_heap_mem_used_in_percent'] = jvm_dict['mem']['heap_used_percent']
            es_dict['nodes_dict'][node_id]['jvm_heap_mem_committed_in_bytes'] = jvm_dict['mem']['heap_committed_in_bytes']
            es_dict['nodes_dict'][node_id]['jvm_threads_count'] = jvm_dict['threads']['count']
            es_dict['nodes_dict'][node_id]['jvm_threads_peak_count'] = jvm_dict['threads']['peak_count']

            fs_dict = nodeid_dict['fs']
            es_dict['nodes_dict'][node_id]['fs_size_total_in_bytes'] = fs_dict['total']['total_in_bytes']
            es_dict['nodes_dict'][node_id]['fs_size_free_in_bytes'] = fs_dict['total']['free_in_bytes']
            es_dict['nodes_dict'][node_id]['fs_size_available_in_bytes'] = fs_dict['total']['available_in_bytes']

            mt_list_str = ""
            for mt_dict in fs_dict['data']:
                mt_val = mt_dict['mount'] + '-' + mt_dict['type']
                mt_list_str = mt_list_str + "," + mt_val
            es_dict['nodes_dict'][node_id]['fs_mount_list'] = mt_list_str
            es_dict['nodes_dict'][node_id]['fs_io_stats_operations'] = fs_dict['io_stats']['total']['operations']
            es_dict['nodes_dict'][node_id]['fs_io_stats_read_operations'] = fs_dict['io_stats']['total']['read_operations']
            es_dict['nodes_dict'][node_id]['fs_io_stats_write_operations'] = fs_dict['io_stats']['total']['write_operations']
            es_dict['nodes_dict'][node_id]['fs_io_stats_read_kilobytes'] = fs_dict['io_stats']['total']['read_kilobytes']
            es_dict['nodes_dict'][node_id]['fs_io_stats_write_kilobytes'] = fs_dict['io_stats']['total']['write_kilobytes']

        print(es_dict)
        return es_dict


    def get_index_metrics_dict( self, ):
        # Could not find the equivalent in Python SDK, so forced to use curl
        # Generating our own data by iterating over every index is very expensive
        index_dict = {}
        cmd = '/usr/local/bin/curl -s --key {} --cert {} --insecure https://{}:{}/_cat/indices?v'.format(
              self.key_file, self.cert_file, self.master_ip, self.elastic_port )
        output = run_command(cmd)
        for line in output.split("\n"):
            print(line)
            pat = '([a-z]+)[\s]+[a-z]+[\s]+([a-z0-9A-Z\.\_\-]+)[\s]+([0-9a-zA-Z]+)[\s]+([0-9]+)[\s]+([0-9]+)[\s]+([0-9]+)[\s]+([0-9]+)[\s]+([0-9a-z\.]+)[\s]+([0-9a-z\.]+)'
            if re.search(pat, line ):
                
               match = re.search(pat, line )
               uuid = match.group(3)
               index_dict[uuid] = {}
               index_dict[uuid]['index'] = match.group(2)
               index_dict[uuid]['health'] = match.group(1)
               index_dict[uuid]['primary_shards'] = match.group(4)
               index_dict[uuid]['repl_shards'] = match.group(5)
               index_dict[uuid]['docs_count'] = match.group(6)
               index_dict[uuid]['docs_deleted'] = match.group(7)
               index_dict[uuid]['total_store_size'] = match.group(8)
               index_dict[uuid]['pri_store_size'] = match.group(9)
        print(index_dict)
        return index_dict


    def get_index_list(self, ):
        index_list = []
        for index in self.es.indices.get_alias("*"):
            index_list.append(index)
        return index_list
        

    def get_all_docs_list(self, scroll_interval='10m', scroll_size=10000, timeout=100 ):
        # Please Note, this is very expensive and can take minutes to complete on scale setups
        doc_list = []
        query = { "query": { "match_all": {} } }
        for index in index_list:
            scan_list = helpers.scan( self.es, index=index, query=query, scroll=scroll_interval, size=scroll_size, request_timeout=timeout)
            for doc in scan_list:
                doc_list.append(doc)
        return doc_list
