__author__ = 'Shirish Pal'

import os
import ipaddress

from .config import NODE_RUNDIR, POD_RUNDIR, NODE_SRCDIR, POD_SRCDIR, TCPDUMP_FLAG

from .run import start_run, init_testbed, stats_run, stop_run, get_pod_ip
from .run import get_pod_pcap_dir, get_testbed_info, purge_testbed

from .run import is_valid_testbed, is_running, get_testbed_runid
from .run import get_testbed_ready, start_run_stats


def next_ipaddr (ip_addr, count):
    return ipaddress.ip_address(ip_addr) + count

class App(object):
    def __init__(self):
        self.pod_rundir_certs = os.path.join(POD_RUNDIR, 'certs')
        self.tcpdump = TCPDUMP_FLAG
        self.next_ipaddr = next_ipaddr

class TlsCsApp(App):
    def __init__ (self):
        super(TlsCsApp, self).__init__()
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

    def set_testbed (self, testbed):
        
        self.testbed = testbed
        testbed_info = get_testbed_info (self.testbed)
        self.traffic_paths = testbed_info['traffic_paths']
        self.traffic_path_count = len (self.traffic_paths)
        self.pod_index_list = range (self.traffic_path_count * 2)
        self.pod_index_list_client = range (0, self.traffic_path_count*2, 2)
        self.pod_index_list_server = range (1, self.traffic_path_count*2, 2)

        self.node_iface_list_client = []
        self.node_iface_list_server = []

        self.node_macvlan_list_client = []
        self.node_macvlan_list_server = []

        self.pod_iface_list_client = []
        self.pod_iface_list_server = []

        pod_iface_index_client = 1
        pod_iface_index_server = 1

        for traffic_path in self.traffic_paths:

            next_iface = traffic_path['client']['iface']
            if not next_iface in self.node_iface_list_client:
                self.node_iface_list_client.append (next_iface)
                next_macvlan = testbed_info[next_iface]['macvlan']
                self.node_macvlan_list_client.append (next_macvlan)
                next_pod_iface = 'eth{}'.format(pod_iface_index_client)
                self.pod_iface_list_client.append (next_pod_iface)
                traffic_path['client']['pod_iface'] = next_pod_iface
                pod_iface_index_client += 1

            next_iface = traffic_path['server']['iface']
            if not next_iface in self.node_iface_list_server:
                self.node_iface_list_server.append (next_iface)
                next_macvlan = testbed_info[next_iface]['macvlan']
                self.node_macvlan_list_server.append (next_macvlan)
                next_pod_iface = 'eth{}'.format(pod_iface_index_server)
                self.pod_iface_list_server.append (next_pod_iface)
                traffic_path['server']['pod_iface'] = next_pod_iface
                pod_iface_index_server += 1

            for cs_g in traffic_path['client']['client_list']:
                cs_g['client_port_begin'] = self.client_port_begin
                cs_g['client_port_end'] = self.client_port_end        

