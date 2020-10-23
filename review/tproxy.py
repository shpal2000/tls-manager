__author__ = 'Shirish Pal'

import os
import sys
import argparse
import json
import jinja2

import time

from pymongo import MongoClient

from config import DB_CSTRING, RESULT_DB_NAME
from config import LIVE_STATS_TABLE

from run import start_run, is_valid_testbed, get_pcap_dir 
from run import get_pod_count, map_pod_interface

def get_arguments():
    arg_parser = argparse.ArgumentParser(description = 'tcp transparent proxy')

    arg_parser.add_argument('--node_rundir'
                                , action="store"
                                , default='/root/rundir'
                                , help = 'rundir path')

    arg_parser.add_argument('--pod_rundir'
                                , action="store"
                                , default='/rundir'
                                , help = 'rundir path in container')

    arg_parser.add_argument('--node_srcdir'
                                , action="store"
                                , default='/root/tcpdash'
                                , help = 'node_srcdir')

    arg_parser.add_argument('--pod_srcdir'
                                , action="store"
                                , default='/root/tcpdash'
                                , help = 'pod_srcdir')

    arg_parser.add_argument('--testbed'
                                , action="store"
                                , required=True
                                , help = 'testbed name')

    arg_parser.add_argument('--restart'
                                , action="store_true"
                                , default=False
                                , help = 'testbed name')

    arg_parser.add_argument('--force'
                                , action="store_true"
                                , default=False
                                , help = 'testbed name')

    arg_parser.add_argument('--runid'
                                , action="store"
                                , required=True
                                , help = 'run id')

    arg_parser.add_argument('--proxy_traffic_vlan'
                                , action="store"
                                , type=int
                                , required=True
                                , help = '1-4095')

    arg_parser.add_argument('--zones'
                                , action="store"
                                , required=True
                                , type=int
                                , help = 'zones count')

    arg_parser.add_argument('--ta'
                                , action="store"
                                , required=True
                                , dest = 'ta_iface'
                                , help = 'ta host interface')

    arg_parser.add_argument('--tb'
                                , action="store"
                                , required=True
                                , dest = 'tb_iface'
                                , help = 'tb host interface')

    arg_parser.add_argument('--ta_subnet'
                                , action="store"
                                , help = 'ta subnet'
                                , required=True)

    arg_parser.add_argument('--tb_subnet'
                                , action="store"
                                , help = 'tb subnet'
                                , required=True)

    arg_parser.add_argument('--tcpdump'
                                , action="store"
                                , help = 'tcpdump options'
                                , default='-c 1000')

    arg_parser.add_argument('--total_conn_count'
                                , action="store"
                                , type=int
                                , default=0
                                , help = 'total connection counts')

    arg_parser.add_argument('--client_mac_seed'
                                , action="store"
                                , help = '5 bytes'
                                , default='02:42:ac:14:00')

    arg_parser.add_argument('--server_mac_seed'
                                , action="store"
                                , help = '5 bytes'
                                , default='02:42:ac:15:00')

    return arg_parser.parse_args()


def get_config (c_args):
    config_s = jinja2.Template ('''{
        "app_module" : "tproxy",
        "zones" : [
            {
                "zone_type" : "proxy",
                "zone_label" : "zone-1-proxy",
                "enable" : 1,
            
                "app_list" : [
                    {
                        "app_type" : "tcp_proxy",
                        "app_label" : "tcp_proxy_1",
                        "enable" : 1,

                        "proxy_list" : [
                            {
                                "proxy_label" : "bae-issue",
                                "enable" : 1,

                                "proxy_ip" : "0.0.0.0",
                                "proxy_port" : 883,
                                "proxy_type_id" : 1,

                                "tcp_rcv_buff" : 0,
                                "tcp_snd_buff" : 0
                            }
                        ]
                    }
                ],
                

                "zone_cmds" : [
                    "sysctl net.ipv4.conf.all.rp_filter=0",
                    "sysctl net.ipv4.conf.default.rp_filter=0",

                    "ip link set dev {{PARAMS.pod_ta_iface}} down",
                    "ip link set dev {{PARAMS.pod_ta_iface}} address {{PARAMS.server_mac_seed}}:{{'{:02x}'.format(1)}}",
                    "ip link set dev {{PARAMS.pod_ta_iface}} up",
                    "sysctl net.ipv4.conf.{{PARAMS.pod_ta_iface}}.rp_filter=0",

                    "ip link add link {{PARAMS.pod_ta_iface}} name {{PARAMS.pod_ta_iface}}.{{PARAMS.proxy_traffic_vlan}} type vlan id {{PARAMS.proxy_traffic_vlan}}",
                    "ip link set dev {{PARAMS.pod_ta_iface}}.{{PARAMS.proxy_traffic_vlan}} up",
                    "ip addr add 1.1.1.1/24 dev {{PARAMS.pod_ta_iface}}.{{PARAMS.proxy_traffic_vlan}}",
                    "arp -i {{PARAMS.pod_ta_iface}}.{{PARAMS.proxy_traffic_vlan}} -s 1.1.1.254 {{PARAMS.client_mac_seed}}:{{'{:02x}'.format(1)}}",
                    "ip route add {{PARAMS.ta_subnet}} via 1.1.1.254 dev {{PARAMS.pod_ta_iface}}.{{PARAMS.proxy_traffic_vlan}}",

                    "ip link set dev {{PARAMS.pod_tb_iface}} down",
                    "ip link set dev {{PARAMS.pod_tb_iface}} address {{PARAMS.client_mac_seed}}:{{'{:02x}'.format(1)}}",
                    "ip link set dev {{PARAMS.pod_tb_iface}} up",
                    "sysctl net.ipv4.conf.{{PARAMS.pod_tb_iface}}.rp_filter=0",

                    "ip link add link {{PARAMS.pod_tb_iface}} name {{PARAMS.pod_tb_iface}}.{{PARAMS.proxy_traffic_vlan}} type vlan id {{PARAMS.proxy_traffic_vlan}}",
                    "ip link set dev {{PARAMS.pod_tb_iface}}.{{PARAMS.proxy_traffic_vlan}} up",
                    "ip addr add 2.2.2.1/24 dev {{PARAMS.pod_tb_iface}}.{{PARAMS.proxy_traffic_vlan}}",
                    "arp -i {{PARAMS.pod_tb_iface}}.{{PARAMS.proxy_traffic_vlan}} -s 2.2.2.254 {{PARAMS.server_mac_seed}}:{{'{:02x}'.format(1)}}",
                    "ip route add {{PARAMS.tb_subnet}} via 2.2.2.254 dev {{PARAMS.pod_tb_iface}}.{{PARAMS.proxy_traffic_vlan}}",

                    "iptables -t mangle -N DIVERT",
                    "iptables -t mangle -A PREROUTING -p tcp -m socket -j DIVERT",
                    "iptables -t mangle -A DIVERT -j MARK --set-mark 1",
                    "iptables -t mangle -A DIVERT -j ACCEPT",
                    "ip rule add fwmark 1 lookup 100",
                    "ip route add local 0.0.0.0/0 dev lo table 100",
                    "iptables -t mangle -A PREROUTING -i {{PARAMS.pod_ta_iface}}.{{PARAMS.proxy_traffic_vlan}} -p tcp --dport 443 -j TPROXY --tproxy-mark 0x1/0x1 --on-port 883",
                    "iptables -t mangle -A PREROUTING -i {{PARAMS.pod_tb_iface}}.{{PARAMS.proxy_traffic_vlan}} -p tcp --dport 443 -j TPROXY --tproxy-mark 0x1/0x1 --on-port 883",

                    "tcpdump -i {{PARAMS.pod_ta_iface}} {{PARAMS.tcpdump}} -w {{PARAMS.pod_pcap_dir.rstrip('/')}}/ta.pcap &",
                    "tcpdump -i {{PARAMS.pod_tb_iface}} {{PARAMS.tcpdump}} -w {{PARAMS.pod_pcap_dir.rstrip('/')}}/tb.pcap &"
                ]
            }
        ]
    }
    ''').render(PARAMS = c_args)

    try:
        config_j = json.loads(config_s)
    except:
        print config_s
        raise

    return config_j

def show_stats (runid):
    mongoClient = MongoClient (DB_CSTRING)
    db = mongoClient[RESULT_DB_NAME]
    stats_col = db[LIVE_STATS_TABLE]

    while True:

        stats = stats_col.find({'runid' : runid})[0]

        print '{}-{}-{} : {} : {} : {}'.format(stats['tick']
                    , stats['proxy_stats']['tcpConnInitSuccessRate']
                    , stats['proxy_stats']['tcpConnInitInUse']
                    , stats['proxy_stats']['tcpConnInit']
                    , stats['proxy_stats']['tcpAcceptSuccess']
                    , stats['proxy_stats']['tcpConnInitSuccess'])

        time.sleep(0.1)

if __name__ == '__main__':
    c_args = get_arguments ()

    if not is_valid_testbed(c_args.node_rundir, c_args.testbed):
        print 'invalid testbed {}'.format (c_args.testbed)
        sys.exit(1)

    c_args.pod_pcap_dir = get_pcap_dir (c_args.pod_rundir, c_args.runid)

    c_args.pod_ta_iface = map_pod_interface (c_args.node_rundir
                                                    , c_args.testbed
                                                    , c_args.ta_iface)

    c_args.pod_tb_iface = map_pod_interface (c_args.node_rundir
                                                    , c_args.testbed
                                                    , c_args.tb_iface)

    cfg_j = get_config (c_args)

    start_run (c_args.testbed
            , c_args.node_rundir
            , c_args.pod_rundir
            , c_args.node_srcdir
            , c_args.pod_srcdir
            , c_args.runid
            , cfg_j
            , c_args.restart
            , c_args.force)