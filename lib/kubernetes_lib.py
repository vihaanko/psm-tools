#!/usr/bin/env python3


###
# Library to connect to Kubernetes cluster via Python SDK APIs and fetch information
#
# Author - venksrin@pensando.io
###

import urllib3
import kubernetes
from kubernetes import client, config
import os
import re
import sys

import paramiko
import netmiko
from netmiko import ConnectHandler
from netmiko import redispatch




class KubernetesConnect():

    def __init__(self, log, master_ip, cert_file, key_file, master_port=6443, debug_flag=True, verify_ssl=False ):

        self.log                    = log
        self.master_ip              = master_ip
        self.master_port            = master_port
        """
        To Connect to Venice K8 cluster, copy the apiserver-client cert.pem and key.pem
        files from your Venice Master Node and pass the file location for certfile
        and key file. You can locate it under
        /var/lib/pensando/pki/kubernetes/apiserver-client
        """
        self.cert_file                  = cert_file
        self.key_file                   = key_file
        self.debug                      = debug_flag 
        self.verify_ssl                 = verify_ssl

        # Populate the configuration

        self.configuration              = client.Configuration()
        self.configuration.cert_file    = self.cert_file
        self.configuration.key_file     = self.key_file
        self.configuration.debug        = self.debug
        self.configuration.verify_ssl   = self.verify_ssl
        self.configuration.host         = 'https://{0}:{1}'.format(self.master_ip, self.master_port )

        # Create Api instance objects to use for the Methods ..
        self.appsv1api          = client.AppsV1Api(client.ApiClient(self.configuration))
        self.corev1api          = client.CoreV1Api(client.ApiClient(self.configuration))
        self.nodeapi            = client.NodeApi(client.ApiClient(self.configuration))  
        self.v1beta2api         = client.AppsV1beta2Api(client.ApiClient(self.configuration)) 
        self.rbacauthapi        = client.RbacAuthorizationV1Api(client.ApiClient(self.configuration))
        self.storagev1api       = client.StorageV1Api(client.ApiClient(self.configuration))
        self.customobjapi       = client.CustomObjectsApi(client.ApiClient(self.configuration))
        # Look at LogsApi, EventsApi, Role 

        # Run state information dicts ..
        self.pod_list = None        # Will be populated with list of Pods in the cluster
        self.pod_dict = None        # Will be populated with all Pod Details ..
        self.pod_restart_count_dict = None
        self.cluster_node_list      = []
        ns = self.corev1api.list_node()
        for item in ns.items:
            node_name = item.metadata.name
            self.cluster_node_list.append(node_name)



    def get_cluster_nodes_dict(self, ):
        """
        Use this to verify node health status. We get the heartbeat condition
        for every node, lookout for the following items to be False PIDPressure,
        DiskPressure, MemoryPressure are False and KubeletReady is True
        
        """
        self.log.info('Get cluster nodes list')
        node_dict = {}
        ns = self.corev1api.list_node()
        for item in ns.items:
            node_name = item.metadata.name
            node_dict[node_name] = {}
            node_dict[node_name]['self_link'] = item.metadata.self_link
            node_dict[node_name]['node_info_dict'] = item.status.node_info
            node_dict[node_name]['status_dict'] = item.status.conditions
            node_dict[node_name]['image_list' ] = item.status.images
        self.log.info(node_dict)
        print(node_dict)
        return node_dict
                  


    def get_brief_cluster_nodes_dict(self, ):
        nodes_dict = {}
        nodes_dict=self.get_cluster_nodes_dict()
        for node in nodes_dict.keys():
            nodes_dict[node] = {}
            stat_dict = self.get_node_status_dict(node)
            print(dir(stat_dict.capacity))
            nodes_dict[node]['cpu'] = stat_dict.capacity['cpu']
            nodes_dict[node]['memory'] = stat_dict.capacity['memory']
            nodes_dict[node]['storage'] = stat_dict.capacity['ephemeral-storage']
            status_list = []
            for reason_obj in stat_dict.conditions:
                status_list.append(reason_obj.reason)
            nodes_dict[node]['status'] = status_list
            nodes_dict[node]['os_image'] = stat_dict.node_info.os_image
            nodes_dict[node]['kernel_version'] = stat_dict.node_info.kernel_version
            nodes_dict[node]['kube_proxy_version'] = stat_dict.node_info.kube_proxy_version
            nodes_dict[node]['kubelet_version'] = stat_dict.node_info.kubelet_version
        print(nodes_dict)
        return nodes_dict



    def get_cluster_nodes_list(self, ):
        nodes_dict = self.get_cluster_nodes_dict()
        print('@@@@@@@@@@@@@@@@@@@@@@@')
        print(list(nodes_dict.keys()))
        print('@@@@@@@@@@@@@@@@@@@@@@@')
        return list(nodes_dict.keys())




    def get_node_status_dict(self, node_name):
        """
        Get Node status - Monitor for conditions for various heartbeats ..
        GET /api/v1/nodes/{node}/status
        In this get the 'conditions' key which returns a list of dicts with
        last heart beat status for disk memory.
        """
       
        ns = self.corev1api.read_node_status(node_name)
        self.log.info(ns.status)
        return ns.status


    def get_api_resources_list(self, ):
        api_resource_list = []
        api_rs_resp = self.corev1api.get_api_resources()
        for api_rs in api_rs_resp.resources:
            api_resource_list.append(api_rs.kind)
        print(api_resource_list)
        return api_resource_list



    def get_all_ns_dict(self, ):
        """
        get_all_ns_dict - Returns all the cluster namespaces as a dict.
        GET of /api/v1/namespaces
        """
        self.log.info('Get all Namespaces dict')
        print('Get all Namespaces dict')
        ns_dict = {}
        ns = self.corev1api.list_namespace() 
        for item in ns.items:
            ns_dict[item.metadata.name] = {}
            ns_dict[item.metadata.name]['self_link'] = item.metadata.self_link
            ns_dict[item.metadata.name]['status'] = item.status.phase
        self.log.info('get_all_ns_dict return value')
        self.log.info(ns_dict)
        return ns_dict


    def get_all_ns_list(self, ):
        """
        get_all_ns_list - Returns the list of all K8 cluster namespaces.
        """
        ns_dict = self.get_all_ns_dict()
        ns_list = list(ns_dict.keys())
        self.log.info('get_all_ns_list value')
        return ns_list
                    

    def get_ns_resource_quota(self, ):
        ns_list = self.get_all_ns_list()
        for ns in ns_list:
            rs_resp = self.corev1api.list_namespaced_resource_quota(ns)
            print(rs_resp.metadata.self_link)


    def get_events_for_all_ns(self, ):
        ev_resp = self.corev1api.list_event_for_all_namespaces()
        print(ev_resp)



    def get_daemon_set_list_for_all_ns(self, ):
        daemon_set_list_all_ns = []
        ds = self.appsv1api.list_daemon_set_for_all_namespaces()
        for item in ds.items:
            daemon_set_list_all_ns.append(item.metadata.name)
        print(daemon_set_list_all_ns)
        return daemon_set_list_all_ns



    def get_namespaced_stateful_set(self, namespace ):
        """
        GET GET /apis/apps/v1/namespaces/{ns}/statefulsets
        """
        ss_dict = {}
        ss = self.appsv1api.list_namespaced_stateful_set(namespace)
        ss = self.v1beta2api.list_namespaced_replica_set(namespace)
        for item in ss.items:
            print(item)
        ss = self.v1beta2api.list_namespaced_replica_set(namespace)
        # Work to do ..


    def get_replica_set(self, ):
        print('Work to do')

    def get_namespaced_replica_set(self, namespace):
        ss = self.v1beta2api.list_namespaced_replica_set(namespace)
        print('Work to do')


    def get_k8_core_components_status(self, ):
        """
        Gives the health of K8 core cluster components in a dict format which includes
        scheduler, controller-manager, etcd instances.
        """
        status_dict = {}
        cs = self.corev1api.list_component_status()
        for item in cs.items:
            status_dict[item.metadata.name] = {}
            status_dict[item.metadata.name]['self_link'] = item.metadata.self_link
            status_dict[item.metadata.name]['conditions'] = item.conditions
        return status_dict 
  


 
    def get_new_pod_dict_for_all_ns(self, node_name ):
        self.pod_dict = {}
        pd = self.corev1api.list_pod_for_all_namespaces( field_selector = 'spec.nodeName={}'.format(node_name))
        print(pd)

        for item in pd.items:
            print(item)
            pod_name = item.metadata.name
            self.pod_dict[pod_name] = {}
            self.pod_dict[pod_name]['namespace'] = item.metadata.namespace
            self.pod_dict[pod_name]['nodename'] = item.status.host_ip
            self.pod_dict[pod_name]['api_version'] = item.metadata.owner_references[0].api_version
            self.pod_dict[pod_name]['kind'] = item.metadata.owner_references[0].kind

            container_list=[]
            container_dict = {}
            container_dict['name'] = item.spec.containers[0].name
            container_dict['image'] = item.spec.containers[0].image
            container_dict['cmd'] = item.spec.containers[0].readiness_probe
            print(item.spec.containers[0])



            

    def get_pod_dict_for_all_ns(self, node_name ):
        """
        get_pod_dict_for_all_ns - Get the list of Pods and details in a Namespace
        and return in dict format.
        GET /api/v1/namespaces/{ns}/pods
        For health check, for every container_id in containers_list_status look for
        state, ready, 
        """
        self.pod_dict = {}
        pd = self.corev1api.list_pod_for_all_namespaces( field_selector = 'spec.nodeName={}'.format(node_name))
        print(pd)

        for item in pd.items:
            print(item)
            pod_name = item.metadata.name
            self.pod_dict[pod_name] = {}
            self.pod_dict[pod_name]['namespace'] = item.metadata.namespace
            self.pod_dict[pod_name]['nodename'] = item.status.host_ip
            self.pod_dict[pod_name]['api_version'] = item.metadata.owner_references[0].api_version
            self.pod_dict[pod_name]['kind'] = item.metadata.owner_references[0].kind

            container_list=[]
            container_dict = {}
            container_dict['name'] = item.spec.containers[0].name
            container_dict['image'] = item.spec.containers[0].image
            container_dict['cmd'] = item.spec.containers[0].readiness_probe
            container_dict['volume_mounts'] = []
            for mpath_dict in item.spec.containers[0].volume_mounts:
                container_dict['volume_mounts'].append(mpath_dict.mount_path)
            self.pod_dict[pod_name]['container_dict'] = container_dict
            
            self.pod_dict[pod_name]['self_link'] = item.metadata.self_link
            self.pod_dict[pod_name]['containers_list_status'] = item.status.container_statuses
            self.pod_dict[pod_name]['pod_ip'] = item.status.pod_ip
            self.pod_dict[pod_name]['host_ip'] = item.status.host_ip
            self.pod_dict[pod_name]['start_time'] = item.status.start_time

        self.log.info(self.pod_dict)
        print(self.pod_dict)
        return self.pod_dict



    def get_cluster_pod_dict_for_all_ns(self, ):
        """
        """
        pod_dict = {}
        for node in self.cluster_node_list:
            pod_dict[node] = {}
            pod_dict[node] = self.get_pod_dict_for_all_ns(node)
        return pod_dict



    def get_pod_list_all_ns(self, ):
        self.pod_dict = self.get_pod_dict_for_all_ns()
        self.pod_list = list(self.pod_dict.keys())
        print(self.pod_list)
        return self.pod_list


    def get_metrics(self, ):
        #md = self.customobjapi.list_cluster_custom_object('metrics.k8s.io', 'v1beta1', 'nodes')
        md = self.customobjapi.list_cluster_custom_object()
        print(md)

    def get_pod_dict_for_ns(self, ns ):
        """
        get_pod_dict_for_ns - Get the list of Pods and details in a Namespace
        and return in dict format.
        GET /api/v1/namespaces/{ns}/pods
        For health check, for every container_id in containers_list_status look for
        state, ready, 
        """
        pod_dict = {}
        pd = self.corev1api.list_namespaced_pod(ns)
        for item in pd.items:
            print(item)
            pod_name = item.metadata.name
            pod_dict[pod_name] = {}
            pod_dict[pod_name]['self_link'] = item.metadata.self_link
            pod_dict[pod_name]['containers_list_spec'] = item.spec.containers
            pod_dict[pod_name]['containers_list_status'] = item.status.container_statuses
            pod_dict[pod_name]['pod_ip'] = item.status.pod_ip
            pod_dict[pod_name]['host_ip'] = item.status.host_ip
            pod_dict[pod_name]['start_time'] = item.status.start_time

        self.log.info(pod_dict)
        print(pod_dict)
        return pod_dict



    def get_pod_list_for_ns(self, ns ):
        pod_dict = self.get_pod_dict_for_ns(ns)
        pod_list = list(pod_dict.keys())
        print(pod_list)
        return pod_list


    def get_ns_pod_status( self, pod_name, ns='default' ):
        pd = self.corev1api.read_namespaced_pod_status( pod_name, ns )
        print(pd.status)
        return pd.status 


    def get_all_pod_status_dict(self ):
        # First get all NS and then pods in each NS ..
        pd = {}
        ns_list = self.get_all_ns_list()
        for ns in ns_list:
            pd[ns] = {}
            ns_pod_list = self.get_pod_list_for_ns(ns)
            for pod_name in ns_pod_list:
                pd[ns][pod_name] = {}
                pd_status = self.get_ns_pod_status( pod_name, ns )
                pd[ns][pod_name]['pod_ip'] = pd_status.pod_ip 
                pd[ns][pod_name]['host_ip'] = pd_status.host_ip 
                pd[ns][pod_name]['conditions_list'] = pd_status.conditions 
                pd[ns][pod_name]['container_statuses_list'] = pd_status.container_statuses
        print(pd)
        return pd


    def get_all_pod_containers_status_dict(self ):
        pd_status_dict = self.get_all_pod_status_dict()
        status_dict = {}
        for ns in pd_status_dict.keys():
            status_dict[ns] = {}
            for pod_name in pd_status_dict[ns].keys():
                status_dict[ns][pod_name] = {}
                status_dict[ns][pod_name]['host_ip'] = pd_status_dict[ns][pod_name]['host_ip']
                status_dict[ns][pod_name]['pod_ip'] = pd_status_dict[ns][pod_name]['pod_ip']
                status_dict[ns][pod_name]['container_status'] = {}
                status_dict[ns][pod_name]['conditions'] = pd_status_dict[ns][pod_name]['conditions_list']
                for container_dict in pd_status_dict[ns][pod_name]['container_statuses_list']:
                    name = container_dict.name
                    status_dict[ns][pod_name]['container_status'][name] = {}
                    status_dict[ns][pod_name]['container_status'][name]['restart_count'] = container_dict.restart_count
                    status_dict[ns][pod_name]['container_status'][name]['current_terminated'] = container_dict.state.terminated
                    status_dict[ns][pod_name]['container_status'][name]['last_terminated'] = container_dict.last_state.terminated

        print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
        print(status_dict)
        print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
        return status_dict


    def get_pod_log_for_ns(self, pod_name, ns='default', tail_lines=10 ):
        log_out = self.corev1api.read_namespaced_pod_log(name=pod_name, namespace=ns, tail_lines=tail_lines )
        print(log_out)
        return log_out


    def get_role_for_all_ns(self, ):
        rd = self.rbacauthapi.list_role_for_all_namespaces()
        print(rd)
        print('This is mostly K8 roles to manage k8 components.. not relevant to us')


    def get_cluster_role_binding(self, ):
        """
        get_cluster_role_binding
        GET /apis/rbac.authorization.k8s.io/v1/clusterrolebindings
        """
        rb = self.rbacauthapi.list_cluster_role_binding()
        print('Work to do')


    def verify_containers_restart_count_after_node_reboot(self, expected_restart_count=1 ):
        """
        verify_containers_restart_count_after_node_reboot - Call this method after every 
        node reboot and it will check if the restart count of all the containers in 
        all the Pods across all Namespaces
        """
        status_dict = self.get_all_pod_containers_status_dict()
        for ns in status_dict.keys():
            for pod_name in status_dict[ns].keys():
                host_ip = status_dict[ns][pod_name]['host_ip']
                print('Checking restart count for Pods on Host ' + host_ip)
                # Check the 'container_status' for restart count for each container
                for container in status_dict[ns][pod_name]['container_status'].keys():
                    print(container)
                    ct_status_dict = status_dict[ns][pod_name]['container_status'][container]
                    if ct_status_dict['restart_count'] > expected_restart_count:
                       self.log.error('Error restart_count={0} for container={1} in Pod={2} namespace={3} on host {4}'.format( ct_status_dict['restart_count'], container, pod_name, ns, host_ip ))


    def verify_cluster_node_status(self, ):
        """
        verify_cluster_node_status - Verify the Node status for all the cluster nodes.
        Checks for type 'Ready', 'PIDPressure', 'MemoryPressure', 'DiskPressure'
        """    
        nodes_dict = self.get_cluster_nodes_dict()
        for node in nodes_dict.keys():
            status_list = nodes_dict[node]['status_dict']
            for status_dict in status_list:
                if status_dict.type == "Ready":
                   if status_dict.status != "True":
                      self.log.error('Node status item {0} is not True for Node {1} Reason {2} Message {3}'.format( status_dict.type, node, status_dict.reason, status_dict.message ))
                      self.log.error(status_dict)
                else:
                   if status_dict.status != "False":
                      self.log.error('Node status item {0} is not False for Node {1} Reason {2} Message {3}'.format( status_dict.type, node, status_dict.reason, status_dict.message ))
                      self.log.error(status_dict)


    def get_all_pod_logs(self, ):
        """
        get_all_pod_logs - Fetch the log files for all the Pods in every NS and
        check for Error, Fatal logs
        """
        status_dict = self.get_all_pod_containers_status_dict()
        log_dict = {}
        for ns in status_dict.keys():
            log_dict[ns] = {}
            for pod_name in status_dict[ns].keys():
                #if re.search( 'elastic', pod_name, re.I ):
                #   log_out = self.get_pod_log_for_ns( pod_name, ns )
                log_out = self.get_pod_log_for_ns( pod_name, ns )
                log_dict[ns][pod_name] = log_out

        return log_dict

        # Printing second time to prevent logs quickly rolling over
        for ns in status_dict.keys():
            for pod_name in status_dict[ns].keys():
                log_out = log_dict[ns][pod_name]
                if re.search( 'ERROR|FATAL|CRITICAL', log_out, re.I ):
                   self.log.error('Error or Fatal logs seen in Pod logs for Pod {0} NS {1}'.format(pod_name, ns ))
                   #self.log.error(log_out)


    def check_ns_pod_logs(self, pod_name, ns='default' ):
        """
        check_ns_pod_logs - Check logs for a specific Pod, NS
        """
        log_out = self.get_pod_log_for_ns( pod_name, ns )
        print(log_out)
        if re.search( 'ERROR|FATAL|CRITICAL', log_out, re.I ):
           self.log.error('Error or Fatal logs seen in Pod logs for Pod {0} NS {1}'.format(pod_name, ns ))
           #self.log.error(log_out)

     

     

    def cluster_metrics(self, ):
        print(self.customobjapi.list_cluster_custom_object('metrics.k8s.io', 'v1beta1', 'nodes'))
        # Work to do







def get_k8_cluster_leader_ip( log, cluster_ip_list, venice_ssh_username='root',
        venice_ssh_password='N0isystem$' ):
  
    leader_ip = None
    for node_ip in cluster_ip_list:
        hdl = ConnectHandler( device_type='linux', ip=node_ip,
            username=venice_ssh_username, password=venice_ssh_password, blocking_timeout=500 )
        docker_out=hdl.execute('docker ps | grep kube-apiserver')
        if re.search( 'pen-kube-apiserver', docker_out, re.I ):
           leader_ip = node_ip
    return leader_ip
  
 
