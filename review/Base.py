__author__ = 'Shirish Pal'

import os
import sys
import uuid
import json
import time
import signal
import argparse
import requests
import ipaddress
import importlib
import subprocess
from threading import Thread
from functools import reduce
from pymongo import MongoClient

from .config import NODE_RUNDIR, POD_RUNDIR, NODE_SRCDIR, POD_SRCDIR, TCPDUMP_FLAG
from .config import DB_CSTRING, REGISTRY_DB_NAME, RESULT_DB_NAME, NODE_RUNDIR
from .config import STATS_TABLE, CSTATE_TABLE, LIVE_STATS_TABLE, POD_RUNDIR
from .config import RPC_IP_VETH1, RPC_IP_VETH2, RPC_PORT, NODE_SRCDIR, POD_SRCDIR
from .config import TESTBED_TABLE, RUN_TABLE

def get_pod_name (testbed, pod_index):
    return "{}-pod-{}".format (testbed, pod_index+1)

def get_exe_alias (testbed, pod_index, runid):
    return "{}-{}.exe".format (get_pod_name (testbed, pod_index), runid)

def get_pod_ip (testbed, pod_index):
    pod_name = get_pod_name (testbed, pod_index)
    cmd_str = "docker inspect --format='{{.NetworkSettings.IPAddress}}' " + pod_name
    return subprocess.check_output(cmd_str, shell=True, close_fds=True).decode("utf-8").strip()


def next_ipaddr (ip_addr, count):
    return ipaddress.ip_address(ip_addr) + count


class TlsAppError (Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message

        
class TlsAppRun:
    def __init__(self, runid):
        mongoClient = MongoClient (DB_CSTRING)
        db = mongoClient[REGISTRY_DB_NAME]
        run_table = db[RUN_TABLE]
        if run_table.find_one ({'runid' : self.runid}):
            raise TlsAppError(-1,  'error: {} already runing'.format (runid))
        self.runid = runid

class TlsAppTestbed:
    def __init__(self, testbed):
        self.testbed = testbed
        mongoClient = MongoClient (DB_CSTRING)
        db = mongoClient[REGISTRY_DB_NAME]
        testbed_table = db[TESTBED_TABLE]
        if not testbed_table.find_one({'testbed' : self.testbed}):
            raise TlsAppError(-1, 'testbed {} does not exist'.format (self.testbed))

    @property
    def type(self):
        mongoClient = MongoClient (DB_CSTRING)
        db = mongoClient[REGISTRY_DB_NAME]
        testbed_table = db[TESTBED_TABLE]
        return testbed_table.find_one({'testbed' : self.testbed}).get('type', '')       

    @property
    def ready(self):
        mongoClient = MongoClient (DB_CSTRING)
        db = mongoClient[REGISTRY_DB_NAME]
        testbed_table = db[TESTBED_TABLE]
        return testbed_table.find_one({'testbed' : self.testbed}).get('ready', 0)

    @ready.setter
    def ready(self, value):
        mongoClient = MongoClient (DB_CSTRING)
        db = mongoClient[REGISTRY_DB_NAME]
        testbed_table = db[TESTBED_TABLE]
        testbed_table.update({'testbed' : self.testbed}, {"$set": { 'ready': value}})
    
    @property
    def runid(self):
        mongoClient = MongoClient (DB_CSTRING)
        db = mongoClient[REGISTRY_DB_NAME]
        testbed_table = db[TESTBED_TABLE]
        return testbed_table.find_one({'testbed' : self.testbed}).get('runing', '')

    @runid.setter
    def runid(self, value):
        mongoClient = MongoClient (DB_CSTRING)
        db = mongoClient[REGISTRY_DB_NAME]
        testbed_table = db[TESTBED_TABLE]
        testbed_table.update({'testbed' : self.testbed}, {"$set": { 'runing': value }})

    @property
    def busy(self):
        mongoClient = MongoClient (DB_CSTRING)
        db = mongoClient[REGISTRY_DB_NAME]
        testbed_table = db[TESTBED_TABLE]
        if testbed_table.find_one({'testbed' : self.testbed}).get('runid'):
            return True
        return False

    def get_info(self):
        mongoClient = MongoClient (DB_CSTRING)
        db = mongoClient[REGISTRY_DB_NAME]
        testbed_table = db[TESTBED_TABLE]
        return testbed_table.find_one({'testbed' : self.testbed})


class TlsCsAppTestbed (TlsAppTestbed):
    def __init__(self, testbed):

        super().__init__(testbed)

        self.pod_iface = 'eth1'
        

    def start(self):
        rundir_map = "--volume={}:{}".format (NODE_RUNDIR, POD_RUNDIR)
        srcdir_map = "--volume={}:{}".format (NODE_SRCDIR, POD_SRCDIR)

        testbed_info = self.get_info()

        pod_index = -1
        for traffic_path in self.testbed_info['traffic_paths']:
            #client
            pod_index += 1
            pod_name = get_pod_name (testbed, pod_index)
            pod_ip = get_pod_ip (testbed, pod_index)
            node_iface = traffic_path['client']['iface']

            cmd_str = "sudo docker run --cap-add=SYS_PTRACE --security-opt seccomp=unconfined --network=bridge --privileged --name {} -it -d {} {} tlspack/tgen:latest /bin/bash".format (pod_name, rundir_map, srcdir_map)
            os.system (cmd_str)

            cmd_str = "sudo ip link set dev {} up".format(node_iface)
            os.system (cmd_str)

            node_macvlan = testbed_info[node_iface]['macvlan']
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

            cmd_str = "sudo docker exec -d {} python3 /usr/local/bin/rpc_proxy_main.py {} {}".format(pod_name, pod_ip, RPC_PORT)
            os.system (cmd_str)

            #server
            pod_index += 1
            pod_name = get_pod_name (testbed, pod_index)
            pod_ip = get_pod_ip (testbed, pod_index)
            node_iface = traffic_path['server']['iface']

            cmd_str = "sudo docker run --cap-add=SYS_PTRACE --security-opt seccomp=unconfined --network=bridge --privileged --name {} -it -d {} {} tlspack/tgen:latest /bin/bash".format (pod_name, rundir_map, srcdir_map)
            os.system (cmd_str)

            cmd_str = "sudo ip link set dev {} up".format(node_iface)
            os.system (cmd_str)

            node_macvlan = testbed_info[node_iface]['macvlan']
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

            cmd_str = "sudo docker exec -d {} python3 /usr/local/bin/rpc_proxy_main.py {} {}".format(pod_name, pod_ip, RPC_PORT)
            os.system (cmd_str)

        self.ready = 1

    def stop(self):
        pass


class TlsApp(object):
    def __init__(self):
        self.pod_rundir_certs = os.path.join(POD_RUNDIR, 'certs')

        self.tcpdump = TCPDUMP_FLAG
        self.next_ipaddr = next_ipaddr
        self.stats_iter = None
        
        self.run_uid = str(uuid.uuid4())
        self.next_log_index = 0

        self.runI = None
        self.testbedI = None

    def __del__(self):
        pass

    def log (self, msg):
        pass
        self.next_log_index += 1
        return msg

    @staticmethod
    def is_running(runid):
        mongoClient = MongoClient (DB_CSTRING)
        db = mongoClient[REGISTRY_DB_NAME]
        run_table = db[RUN_TABLE]
        if run_table.find_one ({'runid' : runid}):
            return True
        return False


    def init(self, testbed, runid):

        # runid info
        self.runI = TlsAppRun(runid)

        self.pod_pcap_dir = os.path.join(POD_RUNDIR
                                    , 'traffic'
                                    , runid
                                    , 'pcaps')

        # testbed info
        required_testbed_type = self.__class__.__name__
        testbed_class_name = required_testbed_type + 'Testbed'
        testbed_class = getattr(sys.modules[__name__], testbed_class_name)
        self.testbedI = testbed_class (testbed)

        # testbed compatibility
        if not self.testbedI.type == required_testbed_type:
            raise TlsAppError(-1
            , 'error: incompatible testbed type {}'.format (self.testbedI.type))

        # testbed availability
        if self.testbedI.busy:
            raise TlsAppError(-1
            , 'error: testbed {} in use; running {}'.format \
            (self.testbedI.name, self.testbedI.runid))

        # testbed readiness
        if not self.testbedI.ready:
            self.testbedI.start()

    def run (self, config_j):
        node_cfg_dir = os.path.join(NODE_RUNDIR, 'traffic', self.runI.runid)

        os.system ( 'rm -rf {}'.format(node_cfg_dir) )
        os.system ( 'mkdir -p {}'.format(node_cfg_dir) )
        os.system ( 'mkdir -p {}'.format(os.path.join(node_cfg_dir, 'pcaps')) )
        os.system ( 'mkdir -p {}'.format(os.path.join(node_cfg_dir, 'logs')) )

        node_cfg_file = os.path.join(node_cfg_dir, 'config.json')
        config_s = json.dumps(node_cfg_j, indent=2)
        with open(node_cfg_file, 'w') as f:
            f.write(config_s)

class TlsCsApp(TlsApp):
    def __init__ (self):

        super().__init__()

        self.max_active = 1
        self.max_pipeline = 1
        self.tcp_snd_buff = 0
        self.tcp_rcv_buff = 0
        self.app_snd_buff = 0
        self.app_rcv_buff = 0
        self.app_next_write = 0
        self.app_cs_starttls_len = 0
        self.app_sc_starttls_len = 0
        self.app_cs_data_len = 1
        self.app_sc_data_len = 1
        self.total_conn_count = 1
        self.close_type = 'fin'
        self.close_notify = 'no_send'
        self.session_resumption = 0
        self.emulation_id = 0
        self.client_port_begin = 5000
        self.client_port_end = 65000

    def run (self, config_j):
        pass








        
        
      
