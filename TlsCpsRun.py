__author__ = 'Shirish Pal'

from .Base import TlsCsApp

import jinja2
import json
import uuid
import ipaddress
from .run import start_run, stats_run, stop_run
from .run import get_pcap_dir, purge_testbed, get_testbed_info
from .run import map_pod_interface

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
        
        setattr (self, version, True)
        self.runid = runid
        self.testbed = testbed
        self.cps = cps
        self.total_conn_count = total_conn_count
        self.cipher = cipher
        self.srv_cert = options.get('srv_cert', '/rundir/certs/server1.cert')
        self.srv_key = options.get('srv_key', '/rundir/certs/server1.key')

    def start(self, restart=False, force=False):

        self.pod_pcap_dir = get_pcap_dir (self.pod_rundir
                                                , self.runid)

        testbed_info = get_testbed_info (self.node_rundir
                                                , self.testbed)

        self.traffic_paths = testbed_info['traffic_paths']

        self.traffic_path_count = len (self.traffic_paths)

        self.pod_count = self.traffic_path_count * 2

        self.na_iface = testbed_info['na_iface']
        
        self.nb_iface = testbed_info['nb_iface']

        self.pod_na_iface = map_pod_interface (self.node_rundir
                                                , self.testbed
                                                , self.na_iface)

        self.pod_nb_iface = map_pod_interface (self.node_rundir
                                                , self.testbed
                                                , self.nb_iface)

        self.cps = self.cps / self.traffic_path_count
        self.max_active = self.max_active / self.traffic_path_count
        self.max_pipeline = self.max_pipeline / self.traffic_path_count
        self.total_conn_count = self.total_conn_count / self.traffic_path_count

        for traffic_path in self.traffic_paths:
            client_ip = traffic_path['client']['subnets'][0].split('/')[0]
            server_ip = traffic_path['server']['subnets'][0].split('/')[0]

            traffic_path['client_ip_begin'] = ipaddress.ip_address (client_ip) + 1
            traffic_path['client_ip_end'] = ipaddress.ip_address (client_ip) + 10
            traffic_path['server_ip'] = ipaddress.ip_address (server_ip) + 1

        self.config_s = TlsCpsRun.J2Template.render(PARAMS = vars(self))

        self.config_j = json.loads(self.config_s)
        start_run (self.testbed
                    , self.pod_count
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
        return stop_run (self.testbed
                        , self.pod_count
                        , self.node_rundir
                        , self.runid
                        , force)

    def purge(self, force=False):
        purge_testbed (self.testbed
                        , self.pod_count
                        , self.node_rundir
                        , force)

    def stats (self):
        return next (self.stats_iter, None)

    J2Template = jinja2.Template('''{
        "app_module" : "tls",
        "zones" : [
            {% set ns = namespace(cs_grp_count=0, srv_count=0) %}
            {%- for traffic_path_index in range(0, PARAMS.traffic_path_count) %}
                {
                    "zone_type" : "client",
                    "zone_label" : "traffic_path_{{traffic_path_index+1}}_client",
                    "enable" : 1,
                    "app_list" : [
                        {
                            "app_type" : "tls_client",
                            "app_label" : "tls_client_{{traffic_path_index+1}}",
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
                                            "srv_ip"   : "{{PARAMS.traffic_paths[traffic_path_index]['server_ip']}}",
                                            "srv_port" : 443,
                                            "clnt_ip_begin" : "{{PARAMS.traffic_paths[traffic_path_index]['client_ip_begin']}}",
                                            "clnt_ip_end" : "{{PARAMS.traffic_paths[traffic_path_index]['client_ip_end']}}",
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
                        "ifconfig {{PARAMS.pod_na_iface}} hw ether {{PARAMS.traffic_paths[traffic_path_index]['client']['gw_mac']}}",
                        "ip route add default dev {{PARAMS.pod_na_iface}} table 200",
                        "ip -4 route add local {{PARAMS.traffic_paths[traffic_path_index]['client']['subnets'][0]}} dev lo",
                        "ip rule add from {{PARAMS.traffic_paths[traffic_path_index]['client']['subnets'][0]}} table 200",
                        "tcpdump -i {{PARAMS.pod_na_iface}} {{PARAMS.tcpdump}} -w {{PARAMS.pod_pcap_dir.rstrip('/')}}/traffic_path_{{traffic_path_index+1}}_client.pcap &"
                    ]
                }
                ,
                {
                    "zone_type" : "server",
                    "zone_label" : "traffic_path_{{traffic_path_index+1}}_server",
                    "enable" : 1,
                    "app_list" : [
                        {
                            "app_type" : "tls_server",
                            "app_label" : "tls_server_{{traffic_path_index+1}}",
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
                                            "srv_ip" : "{{PARAMS.traffic_paths[traffic_path_index]['server_ip']}}",
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
                        "ifconfig {{PARAMS.pod_nb_iface}} hw ether {{PARAMS.traffic_paths[traffic_path_index]['server']['gw_mac']}}",
                        "ip route add default dev {{PARAMS.pod_nb_iface}} table 200",
                        "ip -4 route add local {{PARAMS.traffic_paths[traffic_path_index]['server']['subnets'][0]}} dev lo",
                        "ip rule add from {{PARAMS.traffic_paths[traffic_path_index]['server']['subnets'][0]}} table 200",
                        "tcpdump -i {{PARAMS.pod_nb_iface}} {{PARAMS.tcpdump}} -w {{PARAMS.pod_pcap_dir.rstrip('/')}}/traffic_path_{{traffic_path_index}}_server.pcap &"
                    ]
                }
                {{ "," if not loop.last }}
            {%- endfor %}
        ]
    }
    ''')        
    