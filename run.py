__author__ = 'Shirish Pal'

import os
import sys
import subprocess
import argparse
import json
import time
from threading import Thread
import pdb
import requests
import signal
import importlib

from pymongo import MongoClient

from .config import DB_CSTRING, REGISTRY_DB_NAME, RESULT_DB_NAME, NODE_RUNDIR
from .config import STATS_TABLE, CSTATE_TABLE, LIVE_STATS_TABLE, POD_RUNDIR
from .config import RPC_IP_VETH1, RPC_IP_VETH2, RPC_PORT, NODE_SRCDIR, POD_SRCDIR

def get_pod_name (testbed, pod_index):
    return "{}-pod-{}".format (testbed, pod_index+1)

def get_exe_alias (testbed, pod_index, runid):
    return "{}-{}.exe".format (get_pod_name (testbed, pod_index), runid)

def get_pod_ip (testbed, pod_index):
    pod_name = get_pod_name (testbed, pod_index)
    cmd_str = "docker inspect --format='{{.NetworkSettings.IPAddress}}' " + pod_name
    return subprocess.check_output(cmd_str, shell=True, close_fds=True).decode("utf-8").strip()

def init_testbed(testbed, resource_list):

    rundir_map = "--volume={}:{}".format (NODE_RUNDIR, POD_RUNDIR)
    srcdir_map = "--volume={}:{}".format (NODE_SRCDIR, POD_SRCDIR)

    for pod_index_list, node_iface_list, node_macvlan_list in resource_list:
        for pod_index in pod_index_list:
            pod_name = get_pod_name (testbed, pod_index)

            cmd_str = "sudo docker run --cap-add=SYS_PTRACE --security-opt seccomp=unconfined --network=bridge --privileged --name {} -it -d {} {} tlspack/tgen:latest /bin/bash".format (pod_name, rundir_map, srcdir_map)
            os.system (cmd_str)

            for  node_iface, node_macvlan in zip (node_iface_list, node_macvlan_list):
                cmd_str = "sudo ip link set dev {} up".format(node_iface)
                os.system (cmd_str)
                cmd_str = "sudo docker network connect {} {}".format(node_macvlan, pod_name)
                os.system (cmd_str)

            cmd_str = "sudo docker exec -d {} echo '/rundir/cores/core.%t.%e.%p' | tee /proc/sys/kernel/core_pattern".format(pod_name)
            os.system (cmd_str)

            cmd_str = "sudo docker exec -d {} cp -f /rundir/bin/tlspack.exe /usr/local/bin".format(pod_name)
            os.system (cmd_str)
            cmd_str = "sudo docker exec -d {} chmod +x /usr/local/bin/tlspack.exe".format(pod_name)
            os.system (cmd_str)

            cmd_str = "sudo docker exec -d {} cp -f /rundir/bin/rpc_proxy_main.py /usr/local/bin".format(pod_name)
            os.system (cmd_str)
            cmd_str = "sudo docker exec -d {} chmod +x /usr/local/bin/rpc_proxy_main.py".format(pod_name)
            os.system (cmd_str)

            pod_ip = get_pod_ip (testbed, pod_index)

            cmd_str = "sudo docker exec -d {} python3 /usr/local/bin/rpc_proxy_main.py {} {}".format(pod_name, pod_ip, RPC_PORT)
            os.system (cmd_str)

    set_testbed_ready_status (testbed, ready=1)

def dispose_testbed(testbed, pod_index_list):
    for pod_index in pod_index_list:
        pod_name = get_pod_name (testbed, pod_index)
        cmd_str = "sudo docker rm -f {}".format (pod_name)
        os.system (cmd_str)


def get_registry_data (registry_file):
    with open(registry_file) as f:
        registry_data = json.load(f)
    return registry_data

def set_registry_data (registry_file, registry_data):
    with open(registry_file, 'w') as f:
        json.dump(registry_data, f)

def set_testbed_ready_status(testbed, ready):
    registry_file = get_testbed_registry_file (testbed)
    testbed_info = get_registry_data (registry_file)
    testbed_info['ready'] = ready
    set_registry_data (registry_file, testbed_info)

def set_testbed_running_status(testbed, runing):
    registry_file = get_testbed_registry_file (testbed)
    testbed_info = get_registry_data (registry_file)
    testbed_info['runing'] = runing
    set_registry_data (registry_file, testbed_info)

def set_run_stats_pid (runid, pid):
    registry_file = get_run_registry_file (runid)
    run_info = get_registry_data (registry_file)
    run_info['stats_pid'] = pid
    set_registry_data (registry_file, run_info)
 
def get_testbed_runid (testbed):
    registry_file = get_testbed_registry_file (testbed)
    return  get_registry_data (registry_file).get('runing', '')

def get_run_stats_pid (runid):
    registry_file = get_run_registry_file (runid)
    return int(get_registry_data (registry_file).get('stats_pid', 0))

def get_run_testbed(runid):
    registry_file = get_run_registry_file (runid)
    run_info = get_registry_data (registry_file)
    testbed = run_info['testbed']
    return testbed

def dispose_run (runid):
    registry_dir_run = get_run_registry_dir (runid)
    os.system ( 'rm -rf {}'.format(registry_dir_run) )

def is_running (runid):
    registry_file = get_run_registry_file (runid)
    return os.path.exists(registry_file)

def get_testbed_registry_file (testbed):
    return os.path.join(NODE_RUNDIR, 'registry', 'testbeds', testbed, 'config.json')

def get_run_registry_dir (runid):
    return os.path.join(NODE_RUNDIR, 'registry', 'runs', runid)

def get_run_registry_file (runid):
    return os.path.join(get_run_registry_dir (runid), 'config.json')

def get_run_stats_pid_file (runid):
    return os.path.join(get_run_registry_dir (runid), 'stats_pid.txt')

def get_run_traffic_dir (runid):
    return os.path.join(NODE_RUNDIR, 'traffic', runid)

def get_run_traffic_config_file (runid):
    return os.path.join( get_run_traffic_dir(runid),  'config.json')

def get_pod_traffic_dir (runid):
    return os.path.join(POD_RUNDIR, 'traffic', runid)

def get_pod_traffic_config_file (runid):
    return os.path.join(get_pod_traffic_dir(runid), 'config.json')

def get_pod_pcap_dir (runid):
    return os.path.join( get_run_traffic_dir(runid),  'pcaps')    

def is_valid_testbed (testbed):
    ret = True
    registry_file = get_testbed_registry_file (testbed)
    try:
        get_registry_data (registry_file)
    except:
        ret = False
    return ret

def get_testbed_info (testbed):
    registry_file = get_testbed_registry_file (testbed)
    try:
        ret = get_registry_data (registry_file)
    except:
        ret = {}
    return ret

def get_testbed_ready (testbed):
    registry_file = get_testbed_registry_file (testbed)
    return  get_registry_data (registry_file).get('ready', 0)

def get_stats (pod_ips):
    stats_list = []
    stats_keys = []
    for pod_ip in pod_ips:
        try:
            resp = requests.get('http://{}:{}/ev_sockstats'.format(pod_ip, RPC_PORT))
            stats_j = resp.json()
            stats_list.append (stats_j)
            if stats_j:
                stats_keys = stats_j.keys()
        except:
            stats_list.append ({})

    stats_sum = {}
    for stats_key in stats_keys:
        stats_values = map(lambda s : s.get(stats_key, 0), stats_list) 
        stats_sum[stats_key] = reduce(lambda x, y : x + y, stats_values)

    return (stats_sum, stats_list)

max_tick = 1
def collect_stats (runid
                    , server_pod_ips
                    , proxy_pod_ips
                    , client_pod_ips):

    mongoClient = MongoClient (DB_CSTRING)
    db = mongoClient[RESULT_DB_NAME]
    stats_col = db[LIVE_STATS_TABLE]

    stats_col.remove({'runid' : runid})

    tick = 0
    while True:
        tick += 1

        server_stats, server_stats_list  = get_stats (server_pod_ips)
        proxy_stats, proxy_stats_list = get_stats (proxy_pod_ips)
        client_stats, client_stats_list = get_stats (client_pod_ips)
        
        stats_col.insert_one({'tick' : tick
                                , 'runid' : runid

                                , 'server_stats' : server_stats
                                , 'proxy_stats' : proxy_stats
                                , 'client_stats' : client_stats
                                , 'server_stats_list' : server_stats_list
                                , 'proxy_stats_list' : proxy_stats_list
                                , 'client_stats_list' : client_stats_list
                                
                                })
        if tick > max_tick:
            stats_col.remove({'tick' : tick-max_tick})

        time.sleep(0.1)


def start_run_thread(testbed
                        , pod_index
                        , pod_cfg_file
                        , pod_iface_list
                        , pod_ip
                        , exe_alias):

    url = 'http://{}:{}/start'.format(pod_ip, RPC_PORT)

    data = {'cfg_file': pod_cfg_file
                , 'z_index' : pod_index
                , 'net_ifaces' : pod_iface_list
                , 'rpc_ip_veth1' : RPC_IP_VETH1
                , 'rpc_ip_veth2' : RPC_IP_VETH2
                , 'rpc_port' : RPC_PORT
                , 'exe_alias' : exe_alias}

    resp = requests.post(url, json=data)

    # pdb.set_trace()

    # todo


def start_run_stats (runid
                        , server_pod_ips=[]
                        , proxy_pod_ips=[]
                        , client_pod_ips=[]):

    stats_pid_file = get_run_stats_pid_file (runid)
    registry_file_run = get_run_registry_file (runid)

    pod_ips = ''
    if server_pod_ips:
        pod_ips += ' --server_pod_ips ' + ':'.join(server_pod_ips)
    if proxy_pod_ips:
        pod_ips += ' --proxy_pod_ips ' + ':'.join(proxy_pod_ips)
    if client_pod_ips:
        pod_ips += ' --client_pod_ips ' + ':'.join(client_pod_ips)

    os.system('python -m tlspack.stats --runid {} {} & echo $! > {}'. \
                                format (runid, pod_ips, stats_pid_file))

    with open (stats_pid_file) as f:
        set_run_stats_pid (runid, f.read().strip())

def stop_run_stats(runid):
    registry_file_run = get_run_registry_file (runid)
    stats_pid = get_run_stats_pid (runid)
    if stats_pid:
        try:
            os.kill (stats_pid, signal.SIGTERM)
        except:
            pass
    set_run_stats_pid (runid, 0)

def start_run(testbed
                , runid
                , resource_list
                , node_cfg_j):

    set_testbed_running_status (testbed, runid)

    node_cfg_dir = get_run_traffic_dir(runid)
    node_cfg_file = get_run_traffic_config_file (runid)
    registry_dir_run = get_run_registry_dir (runid)
    registry_file_run = get_run_registry_file (runid)

    os.system ('mkdir -p {}'.format(registry_dir_run))
    os.system ( 'rm -rf {}'.format(node_cfg_dir) )
    os.system ( 'mkdir -p {}'.format(node_cfg_dir) )
    os.system ( 'mkdir -p {}'.format(os.path.join(node_cfg_dir, 'pcaps')) )
    os.system ( 'mkdir -p {}'.format(os.path.join(node_cfg_dir, 'stats')) )
    os.system ( 'mkdir -p {}'.format(os.path.join(node_cfg_dir, 'logs')) )

    with open(registry_file_run, 'w') as f:
        json.dump({'testbed' : testbed}, f)

    config_s = json.dumps(node_cfg_j, indent=4)
    with open(node_cfg_file, 'w') as f:
        f.write(config_s)

    pod_cfg_file = get_pod_traffic_config_file (runid)

    for pod_index_list, pod_iface_list in resource_list:
        pod_start_threads = []
        for pod_index in pod_index_list:            
            pod_ip = get_pod_ip (testbed, pod_index)
            exe_alias = get_exe_alias(testbed, pod_index, runid)
            thd = Thread(target=start_run_thread
                        , args=[testbed
                                , pod_index
                                , pod_cfg_file
                                , pod_iface_list
                                , pod_ip
                                , exe_alias])
            thd.daemon = True
            thd.start()
            pod_start_threads.append(thd)          
            # thd = start_run_thread (testbed
            #                     , pod_index
            #                     , pod_cfg_file
            #                     , pod_iface_list
            #                     , pod_ip
            #                     , exe_alias)            
        if pod_start_threads:
            for thd in pod_start_threads:
                thd.join()
            time.sleep(1)

    return (0, '')


def stop_run_thread(testbed
                        , pod_index
                        , pod_iface_list
                        , pod_ip
                        , exe_alias):

    url = 'http://{}:{}/stop'.format(pod_ip, RPC_PORT)

    data = {'net_ifaces' : pod_iface_list
                , 'rpc_ip_veth1' : RPC_IP_VETH1
                , 'rpc_ip_veth2' : RPC_IP_VETH2
                , 'rpc_port' : RPC_PORT
                , 'exe_alias' : exe_alias}

    resp = requests.post(url, data=json.dumps(data))

    # todo

def stop_run(testbed
                , runid
                , resource_list):

    # pdb.set_trace ()

    registry_dir_run = get_run_registry_dir (runid)
    registry_file_run = get_run_registry_file (runid)

    registry_file_testbed = get_testbed_registry_file (testbed)

    node_cfg_file = get_run_traffic_config_file (runid)

    for pod_index_list, pod_iface_list in resource_list:
        pod_stop_threads = []
        for pod_index in pod_index_list:
            pod_ip = get_pod_ip (testbed, pod_index)
            exe_alias = get_exe_alias(testbed, pod_index, runid)
            thd = Thread(target=stop_run_thread
                        , args=[testbed
                                , pod_index
                                , pod_iface_list
                                , pod_ip
                                , exe_alias])
            thd.daemon = True
            thd.start()
            pod_stop_threads.append(thd)
            # stop_run_thread(testbed
            #                     , pod_index
            #                     , pod_iface_list
            #                     , pod_ip
            #                     , exe_alias)
        if pod_stop_threads:
            for thd in pod_stop_threads:
                thd.join()
            time.sleep(1)

    stop_run_stats (runid)
    dispose_run (runid)
    set_testbed_running_status (testbed, runing='')
    return (0, '')



def stats_run(runid):
    mongoClient = MongoClient (DB_CSTRING)
    db = mongoClient[RESULT_DB_NAME]
    stats_col = db[LIVE_STATS_TABLE]

    while is_running (runid):
        try:
            stats = stats_col.find({'runid' : runid})[0]
        except:
            stats = {}
        yield stats

def purge_testbed(testbed
                , pod_index_list
                , force):

    registry_file_testbed = get_testbed_registry_file (testbed)
    
    testbed_runid = get_testbed_runid (testbed)
    if testbed_runid and not force:
        print ('error: {} testbed in use runing {}'.format(testbed, testbed_runid))
        return
    
    runid = testbed_runid
    registry_dir_run = get_run_registry_dir (runid)
    registry_file_run = get_run_registry_file (runid)

    if is_running (runid):
        stats_pid = get_run_stats_pid (runid)
        if stats_pid:
            try:
                os.kill (stats_pid, signal.SIGTERM)
            except:
                pass
    
    dispose_testbed (testbed, pod_index_list)
    set_testbed_running_status (testbed, runing='')
    set_testbed_ready_status (testbed, ready=0)
    dispose_run (runid)

