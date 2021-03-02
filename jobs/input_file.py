#!/usr/bin/python3



influx_host       = '127.0.0.1'
influx_port       = 8086
influx_user       = 'admin'
influx_password   = 'docker'


# PSM Details
psm_cluster_name = 'ent-psm-cluster'

psm_cluster_dict = { 'node1': { 'ip': '20.0.0.106', 'username': 'root', 'password': 'N0isystem$' }, 'node2': { 'ip': '20.0.0.107', 'username': 'root', 'password': 'N0isystem$' }, 'node3': { 'ip': '20.0.0.108', 'username': 'root', 'password': 'N0isystem$' } }

psm_cluster_ip_list = [ '20.0.0.106', '20.0.0.106', '20.0.0.106' ]

psm_cluster_ip_list_oob = [ '10.30.1.173', '10.30.1.174', '10.30.1.175' ]


k8_master_ip = '20.0.0.106'
refresh_interval = 10
node_ip = '20.0.0.106'
username = 'root'
password = 'N0isystem$'



BASE_DIR = '/root/CERTS/enterprise'

# Get the following files from /var/lib/pensando/pki/kubernetes/apiserver-client on master node
k8_key_file               = BASE_DIR + '/k8/key.pem'
k8_cert_file              = BASE_DIR + '/k8/cert.pem'


# Get the following files from /var/lib/pensando/pki/shared/elastic-client-auth/ on master node
elastic_key_file          = BASE_DIR + '/elastic/key.pem'
elastic_cert_file         = BASE_DIR + '/elastic/cert.pem'


# Get the following files from /var/lib/pensando/pki/pen-vos/certs
minio_private_key_file    = BASE_DIR + '/minio/private.key'
minio_public_cert_file    = BASE_DIR + '/minio/public.crt'


# Get the following files from  /var/lib/pensando/pki/pen-etcd/auth
etcd_key_file             = BASE_DIR + '/etcd/key.pem'
etcd_cert_file            = BASE_DIR + '/etcd/cert.pem'



# Influx DB details
influx_host               = '127.0.0.1'
influx_username           = 'admin'
influx_password           = 'docker'
influx_db_name            = 'psm_monitor'



# Etcd Venice Objects to monitor
venice_etcd_keys = [ '/venice/config/auth/users', '/venice/config/auth/user-preferences', '/venice/config/auth/roles', '/venice/config/auth/role-bindings', '/venice/config/cluster/credentials', '/venice/config/cluster/hosts', '/venice/config/cluster/dscprofiles', '/venice/config/cluster/distributedservicecards', '/venice/config/cluster/config-snapshot', '/venice/config/workload', '/venice/config/network', '/venice/config/rollout', '/venice/staged', '/venice/config/diagnostics/modules', '/venice/config/monitoring/alertPolicies', '/venice/config/monitoring/alertDestinations', '/venice/config/monitoring/alerts', '/venice/config/monitoring/archive-requests', '/venice/config/cluster/config-restore', '/venice/config/cluster/config-snapshot', '/venice/config/security/apps', '/venice/config/security/networksecuritypolicies', '/venice/config/security/firewallprofiles', '/venice/config/security/security-groups' ]




venice_container_list = [ 'pen-citadel', 'pen-vtsa', 'pen-vos', 'pen-elastic', 'pen-evtsproxy', 'pen-evtsmgr', 'pen-npm', 'pen-apigw', 'pen-ntp', 'pen-etcd', 'pen-cmd', 'pen-tpm', 'pen-tsm',  ]


ps_mem_cmd='/var/log/pensando/ps_mem.py'

# Mongodb Information
# Collection is equivalent of tables in RDBMS

mongodb_host                   = '127.0.0.1'
mongodb_port                   = 27017
mongodb_username               = 'admin'
mongodb_password               = 'docker'
mongodb_name                   = 'psm-data'
psm_resource_collection        = 'psm-sys-resources'
psm_minio_collection           = 'psm-minio-metrics'
docker_res_collection          = 'docker-resources'
psm_log_summary_collection     = 'psm-log-summary'

go_profile_collection          = 'psm-goagents-profile'
proc_mem_dist_collection       = 'psm-proc-mem-ditribution'


dashing_url        = "http://10.30.17.130:3030/"
dashing_auth_token = 'docker'
