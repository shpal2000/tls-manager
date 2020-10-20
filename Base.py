__author__ = 'Shirish Pal'

from .config import NODE_RUNDIR, POD_RUNDIR, NODE_SRCDIR, POD_SRCDIR, TCPDUMP_FLAG

class App(object):
    def __init__(self):
        self.node_rundir = NODE_RUNDIR
        self.pod_rundir = POD_RUNDIR
        self.node_srcdir = NODE_SRCDIR
        self.pod_srcdir = POD_SRCDIR
        self.tcpdump = TCPDUMP_FLAG

class TlsCsApp(App):
    def __init__ (self, props):
        super(TlsCsApp, self).__init__()
        self.cps = props.get ('cps', 1)
        self.max_active = props.get ('max_active', 100)
        self.max_pipeline = props.get ('max_pipeline', 100)
        self.total_conn_count = props.get ('total_conn_count', 0)
        self.tcp_snd_buff = props.get ('tcp_snd_buff', 0)
        self.tcp_rcv_buff = props.get ('tcp_rcv_buff', 0)
        self.app_snd_buff = props.get ('app_snd_buff', 0)
        self.app_rcv_buff = props.get ('app_rcv_buff', 0)
        self.app_next_write = props.get ('app_next_write', 0)
        self.app_cs_starttls_len = props.get ('app_cs_starttls_len', 0)
        self.app_sc_starttls_len = props.get ('app_sc_starttls_len', 0)
        self.app_cs_data_len = props.get ('app_cs_data_len', 128)
        self.app_sc_data_len = props.get ('app_sc_data_len', 128)

