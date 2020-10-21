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

from .config import DB_CSTRING, REGISTRY_DB_NAME, RESULT_DB_NAME
from .config import STATS_TABLE, CSTATE_TABLE, LIVE_STATS_TABLE
from .config import RPC_IP_VETH1, RPC_IP_VETH2, RPC_PORT

def get_pod_name (testbed, pod_index):
    return "{}-pod-{}".format (testbed, pod_index+1)

def get_exe_alias (testbed, pod_index, runid):
    return "{}-{}.exe".format (get_pod_name (testbed, pod_index), runid)

def get_pod_ip (testbed, pod_index):
    pod_name = get_pod_name (testbed, pod_index)
    cmd_str = "docker inspect --format='{{.NetworkSettings.IPAddress}}' " + pod_name
    return subprocess.check_output(cmd_str, shell=True, close_fds=True).decode("utf-8").strip()

def init_testbed(testbed
                , pod_index_list
                , node_rundir
                , pod_rundir
                , node_srcdir
                , pod_srcdir
                , node_iface_list
                , node_macvlan_list):

    pod_port = RPC_PORT

    rundir_map = "--volume={}:{}".format (node_rundir, pod_rundir)
    srcdir_map = "--volume={}:{}".format (node_srcdir, pod_srcdir)

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

        cmd_str = "sudo docker exec -d {} python3 /usr/local/bin/rpc_proxy_main.py {} {}".format(pod_name, pod_ip, pod_port)
        os.system (cmd_str)


def dispose_testbed(testbed, pod_index_list):
    for pod_index in pod_index_list:
        pod_name = get_pod_name (testbed, pod_index)
        cmd_str = "sudo docker rm -f {}".format (pod_name)
        os.system (cmd_str)


def get_registry_data (registry_file):
    with open(registry_file) as f:
        testbed_info = json.load(f)
    return testbed_info

def set_registry_data (registry_file, testbed_info):
    with open(registry_file, 'w') as f:
        json.dump(testbed_info, f)

def set_testbed_status(registry_file, ready, runing):
    testbed_info = get_registry_data (registry_file)
    testbed_info['ready'] = ready
    testbed_info['runing'] = runing
    set_registry_data (registry_file, testbed_info)

def set_run_stats_pid (registry_file, pid):
    testbed_info = get_registry_data (registry_file)
    testbed_info['stats_pid'] = pid
    set_registry_data (registry_file, testbed_info)
 
def get_tesbed_ready (registry_file):
    return  get_registry_data (registry_file).get('ready', 0)

def get_testbed_runid (registry_file):
    return  get_registry_data (registry_file).get('runing', '')

def get_run_stats_pid (registry_file):
    return int(get_registry_data (registry_file).get('stats_pid', 0))

def init_run (config_dir, config_file, config_j
                    , registry_dir, registry_file, testbed):
    os.system ('mkdir -p {}'.format(registry_dir))
    os.system ( 'rm -rf {}'.format(config_dir) )
    os.system ( 'mkdir -p {}'.format(config_dir) )
    os.system ( 'mkdir -p {}'.format(os.path.join(config_dir, 'pcaps')) )
    os.system ( 'mkdir -p {}'.format(os.path.join(config_dir, 'stats')) )
    os.system ( 'mkdir -p {}'.format(os.path.join(config_dir, 'logs')) )

    with open(registry_file, 'w') as f:
        json.dump({'testbed' : testbed}, f)

    config_s = json.dumps(config_j, indent=4)
    with open(config_file, 'w') as f:
        f.write(config_s)

def dispose_run (registry_dir):
    os.system ( 'rm -rf {}'.format(registry_dir) )

def dispose_app_run (node_rundir, runid):
    registry_dir_run = get_run_registry_dir (node_rundir, runid)
    dispose_run (registry_dir_run)

def get_run_info (registry_file):
    with open(registry_file) as f:
        run_info = json.load(f)
    return run_info

def is_running (registry_file):
    return os.path.exists(registry_file)

def get_run_testbed (registry_file):
    if os.path.exists(registry_file):
        return get_run_info (registry_file)['testbed']
    return ''

def get_run_config (config_file):
    with open(config_file, 'r') as f:
        config_j = json.load(f)
    return config_j

def get_testbed_registry_dir (node_rundir, testbed):
    return os.path.join(node_rundir, 'registry', 'testbeds', testbed)

def get_testbed_registry_file (node_rundir, testbed):
    return os.path.join(get_testbed_registry_dir (node_rundir, testbed), 'config.json')

def get_run_registry_dir (node_rundir, runid):
    return os.path.join(node_rundir, 'registry', 'runs', runid)

def get_run_registry_file (node_rundir, runid):
    return os.path.join(get_run_registry_dir (node_rundir, runid), 'config.json')

def get_run_stats_pid_file (node_rundir, runid):
    return os.path.join(get_run_registry_dir (node_rundir, runid), 'stats_pid.txt')

def get_run_traffic_dir (base_dir, runid):
    return os.path.join(base_dir, 'traffic', runid)

def get_run_traffic_config_file (base_dir, runid):
    return os.path.join( get_run_traffic_dir(base_dir, runid),  'config.json')

def get_run_module_name (base_dir, runid):
    cfg_file = get_run_traffic_config_file (base_dir, runid)
    return get_run_config(cfg_file)['app_module']
    
def get_pcap_dir (base_dir, runid):
    return os.path.join( get_run_traffic_dir(base_dir, runid),  'pcaps')

def is_valid_testbed (node_rundir, testbed):
    ret = True
    registry_file = get_testbed_registry_file (node_rundir, testbed)
    try:
        get_registry_data (registry_file)
    except:
        ret = False
    return ret

def get_testbed_info (node_rundir, testbed):
    registry_file = get_testbed_registry_file (node_rundir, testbed)
    try:
        ret = get_registry_data (registry_file)
    except:
        ret = {}
    return ret

def is_app_running (node_rundir, runid):
    registry_file = get_run_registry_file (node_rundir, runid)
    return os.path.exists(registry_file)

def set_zone_status(node_rundir, testbed, ready, runing):
    registry_file = get_testbed_registry_file (node_rundir, testbed)
    set_testbed_status (registry_file, ready, runing)

def get_zone_runid (node_rundir, testbed):
    registry_file = get_testbed_registry_file (node_rundir, testbed)
    return  get_registry_data (registry_file).get('runing', '')

def get_zone_ready (node_rundir, testbed):
    registry_file = get_testbed_registry_file (node_rundir, testbed)
    return  get_registry_data (registry_file).get('ready', 0)

def set_zone_status(node_rundir, testbed, ready, runing):
    registry_file = get_testbed_registry_file (node_rundir, testbed)
    testbed_info = get_registry_data (registry_file)
    testbed_info['ready'] = ready
    testbed_info['runing'] = runing
    set_registry_data (registry_file, testbed_info)

def get_stats (pod_ips, pod_port):
    stats_list = []
    stats_keys = []
    for pod_ip in pod_ips:
        try:
            resp = requests.get('http://{}:{}/ev_sockstats'.format(pod_ip, pod_port))
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

    return stats_sum

max_tick = 1
def collect_stats (runid
                    , server_pod_ips
                    , proxy_pod_ips
                    , client_pod_ips 
                    , pod_port):

    mongoClient = MongoClient (DB_CSTRING)
    db = mongoClient[RESULT_DB_NAME]
    stats_col = db[LIVE_STATS_TABLE]

    stats_col.remove({'runid' : runid})

    tick = 0
    while True:
        tick += 1

        server_stats = get_stats (server_pod_ips, pod_port)
        proxy_stats = get_stats (proxy_pod_ips, pod_port)
        client_stats = get_stats (client_pod_ips, pod_port)
        
        stats_col.insert_one({'tick' : tick
                                , 'runid' : runid
                                , 'server_stats' : server_stats
                                , 'proxy_stats' : proxy_stats
                                , 'client_stats' : client_stats})
        if tick > max_tick:
            stats_col.remove({'tick' : tick-max_tick})

        time.sleep(0.1)


def start_run_thread(testbed
                        , pod_index
                        , pod_cfg_file
                        , pod_iface_list
                        , pod_ip
                        , pod_port
                        , exe_alias):

    url = 'http://{}:{}/start'.format(pod_ip, pod_port)

    data = {'cfg_file': pod_cfg_file
                , 'z_index' : pod_index
                , 'net_ifaces' : pod_iface_list
                , 'rpc_ip_veth1' : RPC_IP_VETH1
                , 'rpc_ip_veth2' : RPC_IP_VETH2
                , 'rpc_port' : RPC_PORT
                , 'exe_alias' : exe_alias}

    resp = requests.post(url, json=data)

    pdb.set_trace()

    # todo

def init_app_run (node_rundir, testbed, runid, node_cfg_j):
    registry_file_testbed = get_testbed_registry_file (node_rundir, testbed)
    registry_file_run = get_run_registry_file (node_rundir, runid)
    
    node_cfg_dir = get_run_traffic_dir(node_rundir, runid)
    node_cfg_file = get_run_traffic_config_file (node_rundir, runid)

    registry_dir_run = get_run_registry_dir (node_rundir, runid)

    init_run (node_cfg_dir, node_cfg_file, node_cfg_j
                , registry_dir_run, registry_file_run, testbed)

def start_run_stats (node_rundir
                        , runid
                        , server_pod_ips=[]
                        , proxy_pod_ips=[]
                        , client_pod_ips=[]):

    pod_port = RPC_PORT

    stats_pid_file = get_run_stats_pid_file (node_rundir, runid)
    registry_file_run = get_run_registry_file (node_rundir, runid)

    pod_ips = ''
    if server_pod_ips:
        pod_ips += ' --server_pod_ips ' + ':'.join(server_pod_ips)
    if proxy_pod_ips:
        pod_ips += ' --proxy_pod_ips ' + ':'.join(proxy_pod_ips)
    if client_pod_ips:
        pod_ips += ' --client_pod_ips ' + ':'.join(client_pod_ips)

    os.system('python -m tlspack.stats --runid {} {} --pod_port {} & echo $! > {}'. \
                                format (runid, pod_ips, pod_port, stats_pid_file))

    with open (stats_pid_file) as f:
        set_run_stats_pid (registry_file_run, f.read().strip())

def stop_run_stats(node_rundir, runid):
    registry_file_run = get_run_registry_file (node_rundir, runid)
    stats_pid = get_run_stats_pid (registry_file_run)
    if stats_pid:
        try:
            os.kill (stats_pid, signal.SIGTERM)
        except:
            pass
    set_run_stats_pid (registry_file_run, 0)

def start_run(testbed
                , pod_index_list
                , node_rundir
                , pod_rundir
                , node_srcdir
                , pod_srcdir
                , runid
                , node_cfg_j
                , pod_iface_list):

    pod_port = RPC_PORT
    registry_file_testbed = get_testbed_registry_file (node_rundir, testbed)
    registry_file_run = get_run_registry_file (node_rundir, runid)
    
    node_cfg_dir = get_run_traffic_dir(node_rundir, runid)
    node_cfg_file = get_run_traffic_config_file (node_rundir, runid)

    registry_dir_run = get_run_registry_dir (node_rundir, runid)

    pod_cfg_dir = get_run_traffic_dir(pod_rundir, runid)
    pod_cfg_file = get_run_traffic_config_file(pod_rundir, runid)

    pod_start_threads = []
    for pod_index in pod_index_list:
        zone = node_cfg_j['zones'][pod_index]

        if not zone['enable']:
            continue
        
        pod_ip = get_pod_ip (testbed, pod_index)
        exe_alias = get_exe_alias(testbed, pod_index, runid)
        # thd = Thread(target=start_run_thread
        #             , args=[testbed
        #                     , pod_index
        #                     , pod_cfg_file
        #                     , pod_iface_list
        #                     , pod_ip
        #                     , pod_port
        #                     , exe_alias])
        # thd.daemon = True
        # thd.start()
        # pod_start_threads.append(thd)

        start_run_thread (testbed
                            , pod_index
                            , pod_cfg_file
                            , pod_iface_list
                            , pod_ip
                            , pod_port
                            , exe_alias)
            
    if pod_start_threads:
        for thd in pod_start_threads:
            thd.join()
        time.sleep(1)


    
    return (0, '')


def stop_run_thread(testbed
                        , pod_index
                        , pod_iface_list
                        , pod_ip
                        , pod_port
                        , exe_alias):

    url = 'http://{}:{}/stop'.format(pod_ip, pod_port)

    data = {'net_ifaces' : pod_iface_list
                , 'rpc_ip_veth1' : RPC_IP_VETH1
                , 'rpc_ip_veth2' : RPC_IP_VETH2
                , 'rpc_port' : RPC_PORT
                , 'exe_alias' : exe_alias}

    resp = requests.post(url, data=json.dumps(data))

    # todo

def stop_run(testbed
                , pod_index_list
                , node_rundir
                , runid
                , pod_iface_list
                , force=False):

    pdb.set_trace ()

    pod_port = RPC_PORT

    registry_dir_run = get_run_registry_dir (node_rundir, runid)
    registry_file_run = get_run_registry_file (node_rundir, runid)

    registry_file_testbed = get_testbed_registry_file (node_rundir, testbed)

    if force:
        stats_pid = get_run_stats_pid (registry_file_run)
        if stats_pid:
            try:
                os.kill (stats_pid, signal.SIGTERM)
            except:
                pass
        set_run_stats_pid (registry_file_run, 0)
        dispose_testbed (testbed, pod_index_list)
        set_testbed_status (registry_file_testbed, ready=0, runing='')
        dispose_run (registry_dir_run)
        return (0, '')

    node_cfg_file = get_run_traffic_config_file (node_rundir, runid)

    node_cfg_j = get_run_config (node_cfg_file)
        
    pod_stop_threads = []
    pod_index = -1
    for zone in node_cfg_j['zones']:
        pod_index += 1

        if not zone['enable']:
            continue

        pod_ip = get_pod_ip (testbed, pod_index)
        exe_alias = get_exe_alias(testbed, pod_index, runid)
        thd = Thread(target=stop_run_thread
                    , args=[testbed
                            , pod_index
                            , pod_iface_list
                            , pod_ip
                            , pod_port
                            , exe_alias])
        thd.daemon = True
        thd.start()
        pod_stop_threads.append(thd)
    if pod_stop_threads:
        for thd in pod_stop_threads:
            thd.join()
        time.sleep(1)

    return (0, '')


def stats_run(runid, run_status):
    mongoClient = MongoClient (DB_CSTRING)
    db = mongoClient[RESULT_DB_NAME]

    while run_status['running']:
        try:
            stats_col = db[LIVE_STATS_TABLE]
            stats = stats_col.find({'runid' : runid})[0]
        except:
            stats = {}
        yield stats

def purge_testbed(testbed
                , pod_index_list
                , node_rundir
                , force):

    registry_file_testbed = get_testbed_registry_file (node_rundir, testbed)
    
    testbed_runid = get_testbed_runid (registry_file_testbed)
    if testbed_runid and not force:
        print ('error: {} testbed in use runing {}'.format(testbed, testbed_runid))
        return
    
    runid = testbed_runid
    registry_dir_run = get_run_registry_dir (node_rundir, runid)
    registry_file_run = get_run_registry_file (node_rundir, runid)

    if is_running (registry_file_run):
        stats_pid = get_run_stats_pid (registry_file_run)
        if stats_pid:
            try:
                os.kill (stats_pid, signal.SIGTERM)
            except:
                pass
    
    dispose_testbed (testbed, pod_index_list)
    set_testbed_status (registry_file_testbed, ready=0, runing='')
    dispose_run (registry_dir_run)

