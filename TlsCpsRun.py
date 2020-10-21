__author__ = 'Shirish Pal'

from .Base import TlsCsApp

import os
import jinja2
import json
import uuid

from .run import start_run, init_testbed, stats_run, stop_run, get_pod_ip
from .run import get_pcap_dir, purge_testbed, get_testbed_info, stop_run_stats

from .run import is_valid_testbed, is_app_running, set_zone_status, get_zone_runid
from .run import get_zone_ready, init_app_run, set_zone_status, start_run_stats

from .run import dispose_app_run, stop_run_stats, dispose_testbed

import pdb

class TlsCpsRun(TlsCsApp):
    def __init__(self
                    , runid
                    , testbed
                    , cps
                    , cipher
                    , version
                    , srv_cert
                    , srv_key
                    , total_conn_count):

        super(TlsCpsRun, self).__init__()
        
        self.runid = runid
        self.testbed = testbed
        self.cps = cps
        self.cipher = cipher
        self.version = version
        self.srv_cert = os.path.join(self.pod_rundir_certs, srv_cert)
        self.srv_key = os.path.join(self.pod_rundir_certs, srv_key)
        self.total_conn_count = total_conn_count

    def start(self, restart=False, force=False):

        if not is_valid_testbed (self.node_rundir, self.testbed):
            return (-1,  'invalid testbed {}'.format (self.testbed))

        testbed_info = get_testbed_info (self.node_rundir
                                                , self.testbed)

        self.pod_pcap_dir = get_pcap_dir (self.pod_rundir
                                                , self.runid)

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

        # pdb.set_trace()
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
            

        self.max_active_tp = 100
        self.max_pipeline_tp = 100
        self.cps_tp = self.cps / self.traffic_path_count
        self.total_conn_count_tp = self.total_conn_count / self.traffic_path_count

        self.config_s = TlsCpsRun.J2Template.render(PARAMS = vars(self))
        self.config_j = json.loads(self.config_s)


        if restart:
            if is_app_running (self.node_rundir, self.runid):
                stop_run (self.testbed
                            , self.pod_index_list
                            , self.node_rundir
                            , self.runid
                            , self.pod_iface_list_client
                            , force)
            else:
                dispose_testbed (self.testbed, self.pod_index_list)
                set_zone_status (self.node_rundir, self.testbed, ready=0, runing='')

        if is_app_running (self.node_rundir, self.runid):
            return (-1,  'error: {} already runing'.format (self.runid))
    
        zone_runid = get_zone_runid (self.node_rundir, self.testbed)
        if zone_runid:
            return (-1,  'error: zone in use; running {}'.format (zone_runid))

        if not get_zone_ready (self.node_rundir, self.testbed):
            #start the server pods
            init_testbed (self.testbed                
                            , self.pod_index_list_server
                            , self.node_rundir
                            , self.pod_rundir
                            , self.node_srcdir
                            , self.pod_srcdir
                            , self.node_iface_list_server
                            , self.node_macvlan_list_server)

            #start the client pods
            init_testbed (self.testbed                
                            , self.pod_index_list_client
                            , self.node_rundir
                            , self.pod_rundir
                            , self.node_srcdir
                            , self.pod_srcdir
                            , self.node_iface_list_client
                            , self.node_macvlan_list_client)


        init_app_run (self.node_rundir, self.testbed, self.runid, self.config_j)

        set_zone_status (self.node_rundir, self.testbed, ready=1, runing=self.runid)

        #start the servers
        start_run (self.testbed
                    , self.pod_index_list_server
                    , self.node_rundir
                    , self.pod_rundir
                    , self.node_srcdir
                    , self.pod_srcdir
                    , self.runid
                    , self.config_j
                    , self.pod_iface_list_server)

        #start the clients
        start_run (self.testbed
                    , self.pod_index_list_client
                    , self.node_rundir
                    , self.pod_rundir
                    , self.node_srcdir
                    , self.pod_srcdir
                    , self.runid
                    , self.config_j
                    , self.pod_iface_list_client)

        # pdb.set_trace()
        #start collecting stats
        server_pod_ips = list (map (lambda m: get_pod_ip(self.testbed, m)
                                            , self.pod_index_list_server))

        client_pod_ips = list (map (lambda m: get_pod_ip(self.testbed, m)
                                            , self.pod_index_list_client))

        start_run_stats (self.node_rundir
                            , self.runid
                            , server_pod_ips = server_pod_ips
                            , client_pod_ips = client_pod_ips)
        

        self.run_status = {'running' : True}
        self.stats_iter = stats_run (self.runid, self.run_status)

    def stop(self, force=False):
        #stop the clients
        stop_run (self.testbed
                    , self.pod_index_list_client
                    , self.node_rundir
                    , self.runid
                    , self.pod_iface_list_client
                    , force)

        #stop the servers
        stop_run (self.testbed
                    , self.pod_index_list_server
                    , self.node_rundir
                    , self.runid
                    , self.pod_iface_list_server
                    , force)

        #stop collecting stats
        stop_run_stats (self.node_rundir, self.runid)

        dispose_app_run (self.node_rundir, self.runid)

        set_zone_status (self.node_rundir, self.testbed, ready=1, runing='')

    def purge(self, force=False):
        purge_testbed (self.testbed
                        , self.pod_index_list
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
    