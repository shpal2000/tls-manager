__author__ = 'Shirish Pal'

from Base import TlsCsApp

import jinja2
import json
from run import start_run, stats_run, stop_run
from run import get_pcap_dir 
from run import get_pod_count, map_pod_interface

import pdb

class TlsCpsRun(TlsCsApp):
    def __init__(self
                    , runid
                    , testbed
                    , cps
                    , cipher
                    , version
                    , total_conn_count
                    , options={}):

        super(TlsCpsRun, self).__init__(options)

        self.runid = runid
        self.testbed = testbed
        self.cps = cps
        self.total_conn_count = total_conn_count
        self.cipher = cipher
        setattr (self, version, True)
        self.srv_cert = options.get('srv_cert', '/rundir/certs/server1.cert')
        self.srv_key = options.get('srv_key', '/rundir/certs/server1.key')
        self.na_iface = options.get('na_iface', 'ens161')
        self.nb_iface = options.get('nb_iface', 'ens256')
        self.client_mac_seed = options.get('client_mac_seed', '02:42:ac:14:00')
        self.server_mac_seed = options.get('server_mac_seed', '02:42:ac:15:00')

    def start(self, restart=False, force=False):

        self.pod_pcap_dir = get_pcap_dir (self.pod_rundir, self.runid)

        self.pod_na_iface = map_pod_interface (self.node_rundir
                                                , self.testbed
                                                , self.na_iface)

        self.pod_nb_iface = map_pod_interface (self.node_rundir
                                                , self.testbed
                                                , self.nb_iface)

        self.traffic_paths = get_pod_count (self.node_rundir
                                            , self.testbed) / 2

        self.cps = self.cps / self.traffic_paths
        self.max_active = self.max_active / self.traffic_paths
        self.max_pipeline = self.max_pipeline / self.traffic_paths
        self.total_conn_count = self.total_conn_count / self.traffic_paths

        self.config_s = TlsCpsRun.J2Template.render(PARAMS = vars(self))
        self.config_j = json.loads(self.config_s)

        start_run (self.testbed
                    , self.node_rundir
                    , self.pod_rundir
                    , self.node_srcdir
                    , self.pod_srcdir
                    , self.runid
                    , self.config_j
                    , restart
                    , force)

        self.run_status = {'running' : True}
        self.stats_iter = stats_run (self.runid, self.run_status)

    def stop(self, force=False):
        return stop_run (self.runid, self.node_rundir, force)

    def stats (self):
        return next (self.stats_iter, None)

    J2Template = jinja2.Template('''{
        "app_module" : "tls",
        "zones" : [
            {% set ns = namespace(cs_grp_count=0, srv_count=0) %}
            {%- for traffic_id in range(1, PARAMS.traffic_paths+1) %}
                {
                    "zone_type" : "client",
                    "zone_label" : "zone-{{traffic_id}}-client",
                    "enable" : 1,
                    "app_list" : [
                        {
                            "app_type" : "tls_client",
                            "app_label" : "tls_client_1",
                            "enable" : 1,
                            "conn_per_sec" : {{PARAMS.cps}},
                            "max_pending_conn_count" : {{PARAMS.max_pipeline}},
                            "max_active_conn_count" : {{PARAMS.max_active}},
                            "total_conn_count" : {{PARAMS.total_conn_count}},
                            "cs_grp_list" : [
                                {% set ns.cs_grp_count = 0 %}
                                {%- for tls_ver in ['sslv3', 'tls1', 'tls1_1', 'tls1_2', 'tls1_3'] %}
                                    {%- if (tls_ver == 'sslv3' and PARAMS.sslv3) 
                                            or (tls_ver == 'tls1' and PARAMS.tls1) 
                                            or (tls_ver == 'tls1_1' and PARAMS.tls1_1) 
                                            or (tls_ver == 'tls1_2' and PARAMS.tls1_2) 
                                            or (tls_ver == 'tls1_3' and PARAMS.tls1_3) %}
                                        {{ "," if ns.cs_grp_count }}
                                        {% set ns.cs_grp_count = ns.cs_grp_count+1 %}
                                        {
                                            "cs_grp_label" : "cs_grp_{{loop.index}}",
                                            "enable" : 1,
                                            "srv_ip"   : "14.2{{traffic_id}}.51.{{loop.index}}",
                                            "srv_port" : 443,
                                            "clnt_ip_begin" : "12.2{{traffic_id}}.51.{{1+loop.index0*10}}",
                                            "clnt_ip_end" : "12.2{{traffic_id}}.51.{{loop.index*10}}",
                                            "clnt_port_begin" : 5000,
                                            "clnt_port_end" : 65000,
                                            "cipher" : "{{PARAMS.cipher}}",
                                            "tls_version" : "{{tls_ver}}",
                                            "close_type" : "reset",
                                            "close_notify" : "send",
                                            "app_rcv_buff" : {{PARAMS.app_rcv_buff}},
                                            "app_snd_buff" : {{PARAMS.app_snd_buff}},
                                            "write_chunk" : {{PARAMS.app_next_write}},
                                            "tcp_rcv_buff" : {{PARAMS.tcp_rcv_buff}},
                                            "tcp_snd_buff" : {{PARAMS.tcp_snd_buff}},
                                            "cs_data_len" : {{PARAMS.app_cs_data_len}},
                                            "sc_data_len" : {{PARAMS.app_sc_data_len}},
                                            "cs_start_tls_len" : {{PARAMS.app_cs_starttls_len}},
                                            "sc_start_tls_len" : {{PARAMS.app_sc_starttls_len}},
                                            "session_resumption" : 0
                                        }
                                    {%- endif %}
                                {%- endfor %}                         
                            ]
                        }
                    ],

                    "zone_cmds" : [
                        "ip link set dev {{PARAMS.pod_na_iface}} up",
                        "ifconfig {{PARAMS.pod_na_iface}} hw ether {{PARAMS.client_mac_seed}}:{{'{:02x}'.format(traffic_id)}}",
                        "ip route add default dev {{PARAMS.pod_na_iface}} table 200",
                        "ip -4 route add local 12.2{{traffic_id}}.51.0/24 dev lo",
                        "ip rule add from 12.2{{traffic_id}}.51.0/24 table 200",
                        "tcpdump -i {{PARAMS.pod_na_iface}} {{PARAMS.tcpdump}} -w {{PARAMS.pod_pcap_dir.rstrip('/')}}/zone-{{traffic_id}}-client.pcap &"
                    ]
                }
                ,
                {
                    "zone_type" : "server",
                    "zone_label" : "zone-{{traffic_id}}-server",
                    "enable" : 1,
                    "app_list" : [
                        {
                            "app_type" : "tls_server",
                            "app_label" : "tls_server_1",
                            "enable" : 1,
                            "srv_list" : [
                                {% set ns.srv_count = 0 %}
                                {%- for tls_ver in ['sslv3', 'tls1', 'tls1_1', 'tls1_2', 'tls1_3'] %}
                                    {%- if (tls_ver == 'sslv3' and PARAMS.sslv3) 
                                            or (tls_ver == 'tls1' and PARAMS.tls1) 
                                            or (tls_ver == 'tls1_1' and PARAMS.tls1_1) 
                                            or (tls_ver == 'tls1_2' and PARAMS.tls1_2) 
                                            or (tls_ver == 'tls1_3' and PARAMS.tls1_3) %}
                                        {{ "," if ns.srv_count }}
                                        {% set ns.srv_count = ns.srv_count+1 %}
                                        {
                                            "srv_label" : "srv_{{loop.index}}",
                                            "enable" : 1,
                                            "emulation_id": 0,
                                            "begin_cert_index" : 1,
                                            "end_cert_index" : 100000,
                                            "srv_ip" : "14.2{{traffic_id}}.51.{{loop.index}}",
                                            "srv_port" : 443,
                                            "srv_cert" : "/rundir/certs/server1.cert",
                                            "srv_key" : "/rundir/certs/server1.key",
                                            "cipher" : "{{PARAMS.cipher}}",
                                            "tls_version" : "{{tls_ver}}",
                                            "close_type" : "fin",
                                            "close_notify" : "send",
                                            "app_rcv_buff" : {{PARAMS.app_rcv_buff}},
                                            "app_snd_buff" : {{PARAMS.app_snd_buff}},
                                            "write_chunk" : {{PARAMS.app_next_write}},
                                            "tcp_rcv_buff" : {{PARAMS.tcp_rcv_buff}},
                                            "tcp_snd_buff" : {{PARAMS.tcp_snd_buff}},
                                            "cs_data_len" : {{PARAMS.app_cs_data_len}},
                                            "sc_data_len" : {{PARAMS.app_sc_data_len}},
                                            "cs_start_tls_len" : {{PARAMS.app_cs_starttls_len}},
                                            "sc_start_tls_len" : {{PARAMS.app_sc_starttls_len}},
                                            "session_resumption" : 0
                                        }
                                    {%- endif %}
                                {%- endfor %}
                            ]
                        }
                    ],

                    "zone_cmds" : [
                        "ip link set dev {{PARAMS.pod_nb_iface}} up",
                        "ifconfig {{PARAMS.pod_nb_iface}} hw ether {{PARAMS.server_mac_seed}}:{{'{:02x}'.format(traffic_id)}}",
                        "ip route add default dev {{PARAMS.pod_nb_iface}} table 200",
                        "ip -4 route add local 14.2{{traffic_id}}.51.0/24 dev lo",
                        "ip rule add from 14.2{{traffic_id}}.51.0/24 table 200",
                        "tcpdump -i {{PARAMS.pod_nb_iface}} {{PARAMS.tcpdump}} -w {{PARAMS.pod_pcap_dir.rstrip('/')}}/zone-{{traffic_id}}-server.pcap &"
                    ]
                }
                {{ "," if not loop.last }}
            {%- endfor %}
        ]
    }
    ''')        
    