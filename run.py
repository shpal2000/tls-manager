__author__ = 'Shirish Pal'

import os
import subprocess
import argparse
import json
import time
from threading import Thread
import pdb
import requests

def get_pod_name (testbed, pod_index):
    return "{}-pod-{}".format (testbed, pod_index+1)

def get_pod_ip (testbed, pod_index):
    pod_name = get_pod_name (testbed, pod_index)
    cmd_str = "docker inspect --format='{{.NetworkSettings.IPAddress}}' " + pod_name
    return subprocess.check_output(cmd_str, shell=True, close_fds=True).strip()

def init_testbed(testbed
                , pod_count
                , node_iface_list
                , node_macvlan_list
                , node_rundir
                , pod_rundir
                , node_srcdir
                , pod_srcdir
                , rpc_proxy_port):

    rundir_map = "--volume={}:{}".format (node_rundir, pod_rundir)
    srcdir_map = "--volume={}:{}".format (node_srcdir, pod_srcdir)

    for pod_index in range( pod_count ):
        pod_name = get_pod_name (testbed, pod_index)

        cmd_str = "sudo docker run --cap-add=SYS_PTRACE --security-opt seccomp=unconfined --network=bridge --privileged --name {} -it -d {} {} tlspack/tgen:latest /bin/bash".format (pod_name, rundir_map, srcdir_map)
        os.system (cmd_str)

        for  node_iface, node_macvlan in zip (node_iface_list, node_macvlan_list):
            cmd_str = "sudo ip link set dev {} up".format(node_iface)
            os.system (cmd_str)
            cmd_str = "sudo docker network connect {} {}".format(node_macvlan, pod_name)
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

        cmd_str = "sudo docker exec -d {} python3 /usr/local/bin/rpc_proxy_main.py {} {}".format(pod_name, pod_ip, rpc_proxy_port)
        os.system (cmd_str)


def dispose_testbed(testbed, pod_count):
    for pod_index in range( pod_count ):
        pod_name = get_pod_name (testbed, pod_index)
        cmd_str = "sudo docker rm -f {}".format (pod_name)
        os.system (cmd_str)


def get_testbed_info (registry_file):
    with open(registry_file) as f:
        testbed_info = json.load(f)
    return testbed_info

def get_testbed_pod_count(registry_file):
    return get_testbed_info (registry_file)['containers']['count']

def get_testbed_pod_iface_list(registry_file):
    return map (lambda n : n['container_iface'], get_testbed_info (registry_file)['networks'])

def get_testbed_node_iface_list(registry_file):
    return map (lambda n : n['host_iface'], get_testbed_info (registry_file)['networks'])

def get_testbed_node_macvlan_list(registry_file):
    return map (lambda n : n['host_macvlan'], get_testbed_info (registry_file)['networks'])

def get_tesbed_ready (registry_file):
    return  get_testbed_info (registry_file)['ready']

def get_testbed_runid (registry_file):
    return  get_testbed_info (registry_file)['runing']

def set_testbed_status(registry_file, ready, runing):
    testbed_info = get_testbed_info (registry_file)

    testbed_info['ready'] = ready
    testbed_info['runing'] = runing
    with open(registry_file, 'w') as f:
        json.dump(testbed_info, f)


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

def get_run_traffic_dir (base_dir, runid):
    return os.path.join(base_dir, 'traffic', runid)

def get_run_traffic_config_file (base_dir, runid):
    return os.path.join( get_run_traffic_dir(base_dir, runid),  'config.json')


def get_pcap_dir (base_dir, runid):
    return os.path.join( get_run_traffic_dir(base_dir, runid),  'pcaps')

def get_pod_count (node_rundir, testbed):
    registry_file = get_testbed_registry_file (node_rundir, testbed)
    return get_testbed_pod_count (registry_file)

def is_valid_testbed (node_rundir, testbed):
    ret = True
    registry_file = get_testbed_registry_file (node_rundir, testbed)
    try:
        get_testbed_info (registry_file)
    except:
        ret = False
    return ret

def map_pod_interface (node_rundir, testbed, node_iface):
    registry_file = get_testbed_registry_file (node_rundir, testbed)
    return filter (lambda n : n['host_iface'] == node_iface
                    , get_testbed_info(registry_file)['networks'])[0]['container_iface']


def start_run_thread(testbed
                        , pod_index
                        , pod_cfg_file
                        , pod_iface_list
                        , rpc_proxy_port):
    pod_ip = get_pod_ip (testbed, pod_index)

    requests.post('http://{}:{}/start'.format(pod_ip, rpc_proxy_port)
                    , data = json.dumps({'cfg_file': pod_cfg_file
                                            , 'z_index' : pod_index
                                            , 'net_ifaces' : pod_iface_list })
                    , headers={'Content-type': 'application/json', 'Accept': 'text/plain'})


def start_run(testbed
                , node_rundir
                , pod_rundir
                , node_srcdir
                , pod_srcdir
                , rpc_proxy_port
                , runid
                , node_cfg_j
                , restart
                , force):

    registry_file_testbed = get_testbed_registry_file (node_rundir, testbed)
    registry_file_run = get_run_registry_file (node_rundir, runid)
    
    if restart:
        if is_running (registry_file_run):   
            stop_run (runid
                        , node_rundir
                        , rpc_proxy_port
                        , force)
        else:
            dispose_testbed (testbed, get_testbed_pod_count(registry_file_testbed) )
            set_testbed_status (registry_file_testbed, ready=0, runing='')

    runing_testbed = get_run_testbed (registry_file_run)
    if runing_testbed:
        print 'error: {} already runing'.format (runid)
        return

    testbed_runid = get_testbed_runid (registry_file_testbed)
    if testbed_runid:
        print 'error: {} testbed in use runing {}'.format(testbed, testbed_runid)
        return
        
    pod_count = get_testbed_pod_count (registry_file_testbed)
    node_iface_list = get_testbed_node_iface_list (registry_file_testbed)
    node_macvlan_list = get_testbed_node_macvlan_list (registry_file_testbed)
    pod_iface_list = get_testbed_pod_iface_list (registry_file_testbed)

    if not get_tesbed_ready (registry_file_testbed):
        print 'initializing testbed {}'.format (testbed)
        init_testbed (testbed                
                        , pod_count
                        , node_iface_list
                        , node_macvlan_list
                        , node_rundir
                        , pod_rundir
                        , node_srcdir
                        , pod_srcdir
                        , rpc_proxy_port)
        print 'initializing testbed {}; will take minute or two ...'.format (testbed)
        time.sleep (60)

    node_cfg_dir = get_run_traffic_dir(node_rundir, runid)
    node_cfg_file = get_run_traffic_config_file (node_rundir, runid)

    registry_dir_run = get_run_registry_dir (node_rundir, runid)

    init_run (node_cfg_dir, node_cfg_file, node_cfg_j
                , registry_dir_run, registry_file_run, testbed)

    set_testbed_status (registry_file_testbed, ready=1, runing=runid)

    pod_cfg_dir = get_run_traffic_dir(pod_rundir, runid)
    pod_cfg_file = get_run_traffic_config_file(pod_cfg_dir, runid)

    for next_step in range(1, 3):
        pod_start_threads = []
        pod_index = -1
        for zone in node_cfg_j['zones']:
            pod_index += 1

            if not zone['enable']:
                continue

            if zone.get('step', 1) == next_step:
                thd = Thread(target=start_run_thread
                            , args=[testbed
                                    , pod_index
                                    , pod_cfg_file
                                    , pod_iface_list
                                    , rpc_proxy_port])
                thd.daemon = True
                thd.start()
                pod_start_threads.append(thd)
        if pod_start_threads:
            for thd in pod_start_threads:
                thd.join()
            time.sleep(1)



def stop_run_thread(testbed
                        , pod_index
                        , pod_iface_list
                        , rpc_proxy_port):
    pod_ip = get_pod_ip (testbed, pod_index)

    requests.post('http://{}:{}/stop'.format(pod_ip, rpc_proxy_port)
                    , data = json.dumps({'net_ifaces' : pod_iface_list })
                    , headers={'Content-type': 'application/json', 'Accept': 'text/plain'})


def stop_run(runid
                , node_rundir
                , rpc_proxy_port
                , to_force):

    registry_dir_run = get_run_registry_dir (node_rundir, runid)
    registry_file_run = get_run_registry_file (node_rundir, runid)

    testbed = get_run_testbed (registry_file_run)
    if not testbed:
        return (-1, 'error : invalid runid {}'.format(runid))

    registry_file_testbed = get_testbed_registry_file (node_rundir, testbed)
    
    pod_count = get_testbed_pod_count (registry_file_testbed)
    pod_iface_list = get_testbed_pod_iface_list (registry_file_testbed)

    if to_force:
        dispose_testbed (testbed, pod_count)
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

        thd = Thread(target=stop_run_thread
                    , args=[testbed
                            , pod_index
                            , pod_iface_list
                            , rpc_proxy_port])
        thd.daemon = True
        thd.start()
        pod_stop_threads.append(thd)
    if pod_stop_threads:
        for thd in pod_stop_threads:
            thd.join()
        time.sleep(1)

    set_testbed_status (registry_file_testbed, ready=1, runing='')
    dispose_run (registry_dir_run)
    return (0, '')