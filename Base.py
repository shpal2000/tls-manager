__author__ = 'Shirish Pal'

import os
import ipaddress

from .config import NODE_RUNDIR, POD_RUNDIR, NODE_SRCDIR, POD_SRCDIR, TCPDUMP_FLAG


def next_ipaddr (ip_addr, count):
    return ipaddress.ip_address(ip_addr) + count

class App(object):
    def __init__(self):
        self.node_rundir = NODE_RUNDIR
        self.pod_rundir = POD_RUNDIR
        self.pod_rundir_certs = os.path.join(POD_RUNDIR, 'certs')
        self.node_srcdir = NODE_SRCDIR
        self.pod_srcdir = POD_SRCDIR
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

