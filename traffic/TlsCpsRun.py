__author__ = 'Shirish Pal'

from .Base import TlsCsApp

import os
import jinja2
import json
import uuid

from .run import start_run, start_testbed, run_stats_iter, stop_run, purge_testbed
from .run import get_pod_pcap_dir, get_testbed_info, get_pod_ip, is_valid_testbed
from .run import is_running, get_testbed_runid, is_testbed_ready, start_run_stats


class TlsCpsRun(TlsCsApp):
    def __init__(self, testbed):
        super(TlsCpsRun, self).__init__(testbed)
            
    def start(self
                , runid
                , cps
                , cipher
                , version
                , srv_cert
                , srv_key
                , total_conn_count):

        self.set_runid(runid)

        self.pod_pcap_dir = get_pod_pcap_dir (self.runid)

        self.cps = cps
        self.cipher = cipher
        self.version = version
        self.srv_cert = os.path.join(self.pod_rundir_certs, srv_cert)
        self.srv_key = os.path.join(self.pod_rundir_certs, srv_key)
        self.total_conn_count = total_conn_count

        self.max_active_tp = 100
        self.max_pipeline_tp = 100
        self.cps_tp = self.cps / self.traffic_path_count
        self.total_conn_count_tp = self.total_conn_count / self.traffic_path_count

    
        self.config_s = TlsCpsRun.J2Template.render(PARAMS = vars(self))
        self.config_j = json.loads(self.config_s)

        if not is_testbed_ready (self.testbed):
            resource_list = []
            resource_list.append ((self.pod_index_list_server
                                        , self.node_iface_list_server
                                        , self.node_macvlan_list_server))
            resource_list.append ((self.pod_index_list_client
                                        , self.node_iface_list_client
                                        , self.node_macvlan_list_client))

            start_testbed (self.testbed, resource_list)

        #start servers and clients
        start_run (self.testbed
                    , self.runid
                    , [ (self.pod_index_list_server, self.pod_iface_list_server)
                        , (self.pod_index_list_client, self.pod_iface_list_client)]
                    , self.config_j)


        # pdb.set_trace()
        #start collecting stats
        server_pod_ips = list (map (lambda m: get_pod_ip(self.testbed, m)
                                            , self.pod_index_list_server))

        client_pod_ips = list (map (lambda m: get_pod_ip(self.testbed, m)
                                            , self.pod_index_list_client))

        start_run_stats (self.runid
                        , server_pod_ips = server_pod_ips
                        , client_pod_ips = client_pod_ips)
        
    def stop(self, force=False):

        if force:
            purge_testbed (self.testbed
                            , self.pod_index_list
                            , True)
        else:
            if not is_running (self.runid):
                return (-1,  'error: {} not runing'.format (self.runid))

            stop_run (self.testbed
                        , self.runid
                        , [ (self.pod_index_list_server, self.pod_iface_list_server)
                            , (self.pod_index_list_client, self.pod_iface_list_client)
                        ])
        return (0, '')

    def stats (self):
        if not self.stats_iter:
            self.stats_iter = run_stats_iter (self.runid)
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
                            "conn_per_sec" : {{PARAMS.cps_tp}},
                            "max_pending_conn_count" : {{PARAMS.max_pipeline_tp}},
                            "max_active_conn_count" : {{PARAMS.max_active_tp}},
                            "total_conn_count" : {{PARAMS.total_conn_count_tp}},
                            "cs_grp_list" : [
                                {% set ns.cs_grp_count = 0 %}
                                {%- for next_client_list in PARAMS.traffic_paths[traffic_path_index]['client']['client_list'] %}
                                    {{ "," if ns.cs_grp_count }}
                                    {% set ns.cs_grp_count = ns.cs_grp_count+1 %}
                                    {
                                        "cs_grp_label" : "{{PARAMS.traffic_paths[traffic_path_index]['client']['client_list'][loop.index0]['label']}}",
                                        "enable" : 1,
                                        "srv_ip"   : "{{PARAMS.traffic_paths[traffic_path_index]['client']['client_list'][loop.index0]['server_ip']}}",
                                        "srv_port" : {{PARAMS.traffic_paths[traffic_path_index]['client']['client_list'][loop.index0]['server_port']}},
                                        "clnt_ip_begin" : "{{PARAMS.traffic_paths[traffic_path_index]['client']['client_list'][loop.index0]['client_ip_begin']}}",
                                        "clnt_ip_end" : "{{PARAMS.next_ipaddr(PARAMS.traffic_paths[traffic_path_index]['client']['client_list'][loop.index0]['client_ip_begin'], PARAMS.traffic_paths[traffic_path_index]['client']['client_list'][loop.index0]['client_ip_count']-1)}}",
                                        "clnt_port_begin" : {{PARAMS.traffic_paths[traffic_path_index]['client']['client_list'][loop.index0]['client_port_begin']}},
                                        "clnt_port_end" : {{PARAMS.traffic_paths[traffic_path_index]['client']['client_list'][loop.index0]['client_port_end']}},
                                        "cipher" : "{{PARAMS.cipher}}",
                                        "tls_version" : "{{PARAMS.version}}",
                                        "close_type" : "{{PARAMS.close_type}}",
                                        "close_notify" : "{{PARAMS.close_notify}}",
                                        "app_rcv_buff" : {{PARAMS.app_rcv_buff}},
                                        "app_snd_buff" : {{PARAMS.app_snd_buff}},
                                        "write_chunk" : {{PARAMS.app_next_write}},
                                        "tcp_rcv_buff" : {{PARAMS.tcp_rcv_buff}},
                                        "tcp_snd_buff" : {{PARAMS.tcp_snd_buff}},
                                        "cs_data_len" : {{PARAMS.app_cs_data_len}},
                                        "sc_data_len" : {{PARAMS.app_sc_data_len}},
                                        "cs_start_tls_len" : {{PARAMS.app_cs_starttls_len}},
                                        "sc_start_tls_len" : {{PARAMS.app_sc_starttls_len}},
                                        "session_resumption" : {{PARAMS.session_resumption}}
                                    }
                                {%- endfor %}                         
                            ]
                        }
                    ],

                    "zone_cmds" : [
                        "ip link set dev {{PARAMS.traffic_paths[traffic_path_index]['client']['pod_iface']}} up",
                        "ifconfig {{PARAMS.traffic_paths[traffic_path_index]['client']['pod_iface']}} hw ether {{PARAMS.traffic_paths[traffic_path_index]['client']['gw_mac']}}",
                        "ip route add default dev {{PARAMS.traffic_paths[traffic_path_index]['client']['pod_iface']}} table 200",
                        "ip -4 route add local {{PARAMS.traffic_paths[traffic_path_index]['client']['subnets'][0]}} dev lo",
                        "ip rule add from {{PARAMS.traffic_paths[traffic_path_index]['client']['subnets'][0]}} table 200",
                        "tcpdump -i {{PARAMS.traffic_paths[traffic_path_index]['client']['pod_iface']}} {{PARAMS.tcpdump}} -w {{PARAMS.pod_pcap_dir.rstrip('/')}}/traffic_path_{{traffic_path_index+1}}_client.pcap &"
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
                                {%- for next_server in PARAMS.traffic_paths[traffic_path_index]['server']['server_list'] %}
                                    {{ "," if ns.srv_count }}
                                    {% set ns.srv_count = ns.srv_count+1 %}
                                    {
                                        "srv_label" : "{{PARAMS.traffic_paths[traffic_path_index]['server']['server_list'][loop.index0]['label']}}",
                                        "enable" : 1,
                                        "emulation_id": {{PARAMS.emulation_id}},
                                        "srv_ip" : "{{PARAMS.traffic_paths[traffic_path_index]['server']['server_list'][loop.index0]['server_ip']}}",
                                        "srv_port" : {{PARAMS.traffic_paths[traffic_path_index]['server']['server_list'][loop.index0]['server_port']}},
                                        "srv_cert" : "{{PARAMS.srv_cert}}",
                                        "srv_key" : "{{PARAMS.srv_key}}",
                                        "cipher" : "{{PARAMS.cipher}}",
                                        "tls_version" : "{{PARAMS.version}}",
                                        "close_type" : "{{PARAMS.close_type}}",
                                        "close_notify" : "{{PARAMS.close_notify}}",
                                        "app_rcv_buff" : {{PARAMS.app_rcv_buff}},
                                        "app_snd_buff" : {{PARAMS.app_snd_buff}},
                                        "write_chunk" : {{PARAMS.app_next_write}},
                                        "tcp_rcv_buff" : {{PARAMS.tcp_rcv_buff}},
                                        "tcp_snd_buff" : {{PARAMS.tcp_snd_buff}},
                                        "cs_data_len" : {{PARAMS.app_cs_data_len}},
                                        "sc_data_len" : {{PARAMS.app_sc_data_len}},
                                        "cs_start_tls_len" : {{PARAMS.app_cs_starttls_len}},
                                        "sc_start_tls_len" : {{PARAMS.app_sc_starttls_len}},
                                        "session_resumption" : {{PARAMS.session_resumption}}
                                    }
                                {%- endfor %}
                            ]
                        }
                    ],

                    "zone_cmds" : [
                        "ip link set dev {{PARAMS.traffic_paths[traffic_path_index]['server']['pod_iface']}} up",
                        "ifconfig {{PARAMS.traffic_paths[traffic_path_index]['server']['pod_iface']}} hw ether {{PARAMS.traffic_paths[traffic_path_index]['server']['gw_mac']}}",
                        "ip route add default dev {{PARAMS.traffic_paths[traffic_path_index]['server']['pod_iface']}} table 200",
                        "ip -4 route add local {{PARAMS.traffic_paths[traffic_path_index]['server']['subnets'][0]}} dev lo",
                        "ip rule add from {{PARAMS.traffic_paths[traffic_path_index]['server']['subnets'][0]}} table 200",
                        "tcpdump -i {{PARAMS.traffic_paths[traffic_path_index]['server']['pod_iface']}} {{PARAMS.tcpdump}} -w {{PARAMS.pod_pcap_dir.rstrip('/')}}/traffic_path_{{traffic_path_index}}_server.pcap &"
                    ]
                }
                {{ "," if not loop.last }}
            {%- endfor %}
        ]
    }
    ''')        
    