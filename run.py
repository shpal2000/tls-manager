__author__ = 'Shirish Pal'

import os
import subprocess
import sys
import argparse
import json
import time
from threading import Thread
import pdb
import requests

def container_name (pod_name, cntr_index):
    return "{}-cntr-{}".format (pod_name, cntr_index+1)

def container_ip (pod_name, cntr_index)
    cntr_name = container_name (pod_name, cntr_index)
    cmd_str = "docker inspect --format='{{.NetworkSettings.IPAddress}}' " + cntr_name
    return subprocess.check_output(cmd_str, shell=True, close_fds=True).strip()

def start_pod(pod_name
                , cntr_count
                , host_iface_list
                , host_macvlan_list
                , host_rundir
                , cntr_rundir
                , host_srcdir
                , cntr_srcdir
                , rpc_proxy_port):

    rundir_map = "--volume={}:{}".format (host_rundir, cntr_rundir)
    srcdir_map = "--volume={}:{}".format (host_srcdir, cntr_srcdir)

    for cntr_index in range( cntr_count ):
        cntr_name = container_name (pod_name, cntr_index)
        cntr_ipaddr = container_ip (pod_name, cntr_index)

        cmd_str = "sudo docker run --cap-add=SYS_PTRACE --security-opt seccomp=unconfined --network=bridge --privileged --name {} -it -d {} {} tlspack/tgen:latest /bin/bash".format (cntr_name, rundir_map, srcdir_map)
        os.system (cmd_str)

        for  host_iface, host_macvlan in zip (host_iface_list, host_macvlan_list):
            cmd_str = "sudo ip link set dev {} up".format(host_iface)
            os.system (cmd_str)
            cmd_str = "sudo docker network connect {} {}".format(host_macvlan, cntr_name)
            os.system (cmd_str)

        cmd_str = "sudo docker exec -d {} cp -f /rundir/bin/tlspack.exe /usr/local/bin".format(cntr_name)
        os.system (cmd_str)
        cmd_str = "sudo docker exec -d {} chmod +x /usr/local/bin/tlspack.exe".format(cntr_name)
        os.system (cmd_str)

        cmd_str = "sudo docker exec -d {} cp -f /rundir/bin/rpc_proxy_main.py /usr/local/bin".format(cntr_name)
        os.system (cmd_str)
        cmd_str = "sudo docker exec -d {} chmod +x /usr/local/bin/rpc_proxy_main.py".format(cntr_name)
        os.system (cmd_str)

        cmd_str = "sudo docker exec -d {} python3 /usr/local/bin/rpc_proxy_main.py {} {}".format(cntr_name, cntr_ipaddr, rpc_proxy_port)
        os.system (cmd_str)


def stop_pod(pod_name, cntr_count):
    for cntr_index in range( cntr_count ):
        cntr_name = container_name (pod_name, cntr_index)
        cmd_str = "sudo docker rm -f {}".format (cntr_name)
        os.system (cmd_str)


def restart_pod(pod_name
                , cntr_count
                , host_iface_list
                , host_macvlan_list
                , host_rundir
                , cntr_rundir
                , host_srcdir
                , cntr_srcdir
                , rpc_proxy_port):
    stop_pod(pod_name, cntr_count)
    start_pod(pod_name
                , cntr_count
                , host_iface_list
                , host_macvlan_list
                , host_rundir
                , cntr_rundir
                , host_srcdir
                , cntr_srcdir
                , rpc_proxy_port)


def start_run_thread(pod_name
                        , cntr_index
                        , cntr_cfg_file
                        , cntr_iface_list
                        , rpc_proxy_port):
    cntr_ipaddr = container_ip (pod_name, cntr_index)

    requests.post('http://{}:{}/start'.format(cntr_ipaddr, rpc_proxy_port)
                    , data = json.dumps({'cfg_file': cntr_cfg_file
                                            , 'z_index' : cntr_index
                                            , 'net_ifaces' : cntr_iface_list })
                    , headers={'Content-type': 'application/json', 'Accept': 'text/plain'})


def start_run(pod_name
                , host_rundir
                , cntr_rundir
                , host_srcdir
                , cntr_srcdir
                , rpc_proxy_port
                , runid
                , traffic_s
                , to_start_pod):

    registry_dir = os.path.join(host_rundir, 'registry')

    registry_dir_pod = os.path.join(registry_dir, 'pods', pod_name)
    registry_file_pod = os.path.join(registry_dir_pod, 'config.json')

    registry_dir_run = os.path.join(registry_dir, 'runs', runid)
    registry_file_run = os.path.join(registry_dir_run, 'config.json')
    
    if os.path.exists(registry_file_run):
        with open (registry_file_run) as f:
            registry_run_info = json.load(f)
            print 'error: {} already running in pod {}'.format (runid, registry_run_info['pod'])
            sys.exit(1)

    with open(registry_file_pod) as f:
        pod_info = json.load(f)

    if pod_info.get('runing'):
        print 'error: {} pod in use running {}'.format(pod_name, pod_info['runing'])
        sys.exit(1)

    cntr_count = pod_info ['containers']['count']
    host_iface_list = map (lamda n : n['host_iface'], pod_info ['networks'])
    host_macvlan_list = map (lamda n : n['host_macvlan'], pod_info ['networks'])
    cntr_iface_list = map (lamda n : n['container_iface'], pod_info ['networks'])

    # create config dir; file
    try:
        cfg_j = json.loads (traffic_s)
        traffic_s = json.dumps(cfg_j, indent=4)
    except:
        print traffic_s
        sys.exit(1)

    host_cfg_dir = os.path.join(host_rundir, 'traffic', runid)
    host_cfg_file = os.path.join(host_cfg_dir, 'config.json')

    os.system ( 'rm -rf {}'.format(host_cfg_dir) )
    os.system ( 'mkdir -p {}'.format(host_cfg_dir) )
    os.system ( 'mkdir -p {}'.format(os.path.join(host_cfg_dir, 'pcaps')) )
    os.system ( 'mkdir -p {}'.format(os.path.join(host_cfg_dir, 'stats')) )
    os.system ( 'mkdir -p {}'.format(os.path.join(host_cfg_dir, 'logs')) )

    with open(host_cfg_file, 'w') as f:
        f.write(traffic_s)

    if to_start_pod or not pod_info.get('ready', 0):
        restart_pod (pod_name,                 
                        , cntr_count
                        , host_iface_list
                        , host_macvlan_list
                        , host_rundir
                        , cntr_rundir
                        , host_srcdir
                        , cntr_srcdir
                        , rpc_proxy_port)
        pod_info['ready'] = 1
        time.sleep (60)

    pod_info['runing'] = runid

    # create registry entries
    os.system ('mkdir -p {}'.format(registry_dir_run))

    with open(registry_file_run, 'w') as f:
        json.dump({'pod' : pod_name}, f)

    with open(registry_file_pod, 'w') as f:
        json.dump(pod_info, f)

    cntr_cfg_dir = os.path.join(cntr_rundir, 'traffic', runid)
    cntr_cfg_file = os.path.join(cntr_cfg_dir, 'config.json')

    for next_step in range(1, 3):
        cntr_start_threads = []
        cntr_index = -1
        for zone in cfg_j['zones']:
            cntr_index += 1

            if not zone['enable']:
                continue

            if zone.get('step', 1) == next_step:
                thd = Thread(target=start_run_thread
                            , args=[pod_name
                                    , cntr_index
                                    , cntr_cfg_file
                                    , cntr_iface_list
                                    , rpc_proxy_port])
                thd.daemon = True
                thd.start()
                cntr_start_threads.append(thd)
        if cntr_start_threads:
            for thd in cntr_start_threads:
                thd.join()
            time.sleep(1)


def stop_run_thread(pod_name
                        , cntr_index
                        , cntr_iface_list
                        , rpc_proxy_port):
    cntr_ipaddr = container_ip (pod_name, cntr_index)

    requests.post('http://{}:{}/stop'.format(cntr_ipaddr, rpc_proxy_port)
                    , data = json.dumps({'net_ifaces' : cntr_iface_list })
                    , headers={'Content-type': 'application/json', 'Accept': 'text/plain'})


def stop_run(runid
                , host_rundir
                , rpc_proxy_port
                , to_force):

    registry_dir = os.path.join(host_rundir, 'registry')

    registry_dir_run = os.path.join(registry_dir, 'runs', runid)
    registry_file_run = os.path.join(registry_dir_run, 'config.json')

    if not os.path.exists(registry_file_run):
        print 'error : invalid runid {}'.format(runid)
        sys.exit(1)

    with open(registry_file_run) as f:
        run_info = json.load(f)

    pod_name = run_info['pod']
    registry_dir_pod = os.path.join(registry_dir, 'pods', pod_name)
    registry_file_pod = os.path.join(registry_dir_pod, 'config.json')

    with open(registry_file_pod) ) as f:
        pod_info = json.load(f)

    cntr_count = pod_info ['containers']['count']
    cntr_iface_list = map (lamda n : n['container_iface'], pod_info ['networks'])

    if to_force:
        stop_pod (pod_name, cntr_count)
        pod_info['ready'] = 0
        pod_info['runing'] = ''
        with open(registry_file_pod, 'w') as f:
            json.dump(pod_info, f)
        os.system ( 'rm -rf {}'.format(registry_dir_run) )
        sys.exit(0)

    host_cfg_dir = os.path.join(host_rundir, 'traffic', runid)
    host_cfg_file = os.path.join(host_cfg_dir, 'config.json')

    with open(host_cfg_file) as f:
        cfg_j = json.load(f)

    cntr_stop_threads = []
    cntr_index = -1
    for zone in cfg_j['zones']:
        cntr_index += 1

        if not zone['enable']:
            continue

        thd = Thread(target=stop_run_thread
                    , args=[pod_name
                            , cntr_index
                            , cntr_iface_list
                            , rpc_proxy_port])
        thd.daemon = True
        thd.start()
        cntr_stop_threads.append(thd)
    if cntr_start_threads:
        for thd in cntr_stop_threads:
            thd.join()
        time.sleep(1)

    os.system ("rm -rf {}".format (registry_dir_run))
    pod_info['ready'] = 1
    pod_info['runing'] = ''
    with open(registry_file_pod, 'w') as f:
        json.dump(pod_info, f)