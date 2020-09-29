__author__ = 'Shirish Pal'

import os
import subprocess
import sys
import argparse
import json
import jinja2
import time
from threading import Thread
import pdb
import requests

supported_ciphers = [
    {'cipher_name' : 'AES128-SHA',
        'cipher' : '{AES128-SHA}',
        'sslv3' : '{sslv3}',
        'tls1' : '{tls1}',
        'tls1_1' : '{tls1_1}',
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '10.2',
        'server_ip_prefix' : '100.2'
        },

    {'cipher_name' : 'AES256-SHA',
        'cipher' : '{AES256-SHA}',
        'sslv3' : '{sslv3}',
        'tls1' : '{tls1}',
        'tls1_1' : '{tls1_1}',
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '11.2',
        'server_ip_prefix' : '101.2'
        },

    {'cipher_name' : 'DHE-RSA-AES128-SHA',
        'cipher' : '{DHE-RSA-AES128-SHA}',
        'sslv3' : '{sslv3}',
        'tls1' : '{tls1}',
        'tls1_1' : '{tls1_1}',
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '12.2',
        'server_ip_prefix' : '102.2'
        },

    {'cipher_name' : 'DHE-RSA-AES256-SHA',
        'cipher' : '{DHE-RSA-AES256-SHA}',
        'sslv3' : '{sslv3}',
        'tls1' : '{tls1}',
        'tls1_1' : '{tls1_1}',
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '13.2',
        'server_ip_prefix' : '103.2'
        },

    {'cipher_name' : 'DHE-RSA-AES128-GCM-SHA256',
        'cipher' : '{DHE-RSA-AES128-GCM-SHA256}',
        'sslv3': 0,
        'tls1': 0,
        'tls1_1': 0,
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '14.2',
        'server_ip_prefix' : '104.2'
        },

    {'cipher_name' : 'ECDHE-ECDSA-AES128-SHA',
        'cipher' : '{ECDHE-ECDSA-AES128-SHA}',
        'sslv3' : '{sslv3}',
        'tls1' : '{tls1}',
        'tls1_1' : '{tls1_1}',
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server2.cert',
        'srv_key' : '/rundir/certs/server2.key',
        'client_ip_prefix' : '15.2',
        'server_ip_prefix' : '105.2'
        },

    {'cipher_name' : 'ECDHE-ECDSA-AES256-SHA',
        'cipher' : '{ECDHE-ECDSA-AES256-SHA}',
        'sslv3' : '{sslv3}',
        'tls1' : '{tls1}',
        'tls1_1' : '{tls1_1}',
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server2.cert',
        'srv_key' : '/rundir/certs/server2.key',
        'client_ip_prefix' : '16.2',
        'server_ip_prefix' : '106.2'
        },

    {'cipher_name' : 'ECDHE-RSA-AES128-SHA',
        'cipher' : '{ECDHE-RSA-AES128-SHA}',
        'sslv3' : '{sslv3}',
        'tls1' : '{tls1}',
        'tls1_1' : '{tls1_1}',
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '17.2',
        'server_ip_prefix' : '107.2'
        },

    {'cipher_name' : 'ECDHE-RSA-AES256-SHA',
        'cipher' : '{ECDHE-RSA-AES256-SHA}',
        'sslv3' : '{sslv3}',
        'tls1' : '{tls1}',
        'tls1_1' : '{tls1_1}',
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '18.2',
        'server_ip_prefix' : '108.2'
        },

    {'cipher_name' : 'ECDHE-ECDSA-CHACHA20-POLY1305',
        'cipher' : '{ECDHE-ECDSA-CHACHA20-POLY1305}',
        'sslv3': 0,
        'tls1': 0,
        'tls1_1': 0,
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server2.cert',
        'srv_key' : '/rundir/certs/server2.key',
        'client_ip_prefix' : '19.2',
        'server_ip_prefix' : '109.2'
        },

    {'cipher_name' : 'DHE-RSA-CHACHA20-POLY1305',
        'cipher' : '{DHE-RSA-CHACHA20-POLY1305}',
        'sslv3': 0,
        'tls1': 0,
        'tls1_1': 0,
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '20.2',
        'server_ip_prefix' : '110.2'
        },	

    {'cipher_name' : 'CAMELLIA128-SHA',
        'cipher' : '{CAMELLIA128-SHA}',
        'sslv3' : '{sslv3}',
        'tls1' : '{tls1}',
        'tls1_1' : '{tls1_1}',
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '21.2',
        'server_ip_prefix' : '111.2'
        },

    {'cipher_name' : 'CAMELLIA256-SHA',
        'cipher' : '{CAMELLIA256-SHA}',
        'sslv3' : '{sslv3}',
        'tls1' : '{tls1}',
        'tls1_1' : '{tls1_1}',
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '22.2',
        'server_ip_prefix' : '112.2'
        },

    {'cipher_name' : 'DHE-RSA-CAMELLIA128-SHA',
        'cipher' : '{DHE-RSA-CAMELLIA128-SHA}',
        'sslv3' : '{sslv3}',
        'tls1' : '{tls1}',
        'tls1_1' : '{tls1_1}',
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '23.2',
        'server_ip_prefix' : '113.2'
        },

    {'cipher_name' : 'DHE-RSA-CAMELLIA256-SHA',
        'cipher' : '{DHE-RSA-CAMELLIA256-SHA}',
        'sslv3' : '{sslv3}',
        'tls1' : '{tls1}',
        'tls1_1' : '{tls1_1}',
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '24.2',
        'server_ip_prefix' : '114.2'
        },

    {'cipher_name' : 'AES128-SHA256',
        'cipher' : '{AES128-SHA256}',
        'sslv3': 0,
        'tls1': 0,
        'tls1_1': 0,
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '25.2',
        'server_ip_prefix' : '115.2'
        },

    {'cipher_name' : 'AES256-SHA256',
        'cipher' : '{AES256-SHA256}',
        'sslv3': 0,
        'tls1': 0,
        'tls1_1': 0,
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '26.2',
        'server_ip_prefix' : '116.2'
        },

    {'cipher_name' : 'DHE-RSA-AES128-SHA256',
        'cipher' : '{DHE-RSA-AES128-SHA256}',
        'sslv3': 0,
        'tls1': 0,
        'tls1_1': 0,
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '27.2',
        'server_ip_prefix' : '117.2'
        },

    {'cipher_name' : 'AES128-GCM-SHA256',
        'cipher' : '{AES128-GCM-SHA256}',
        'sslv3': 0,
        'tls1': 0,
        'tls1_1': 0,
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '28.2',
        'server_ip_prefix' : '118.2'
        },

    {'cipher_name' : 'AES256-GCM-SHA384',
        'cipher' : '{AES256-GCM-SHA384}',
        'sslv3': 0,
        'tls1': 0,
        'tls1_1': 0,
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '29.2',
        'server_ip_prefix' : '119.2'
        },

    {'cipher_name' : 'ECDHE-RSA-AES128-GCM-SHA256',
        'cipher' : '{ECDHE-RSA-AES128-GCM-SHA256}',
        'sslv3': 0,
        'tls1': 0,
        'tls1_1': 0,
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '30.2',
        'server_ip_prefix' : '120.2'
        },

    {'cipher_name' : 'ECDHE-RSA-AES256-GCM-SHA384',
        'cipher' : '{ECDHE-RSA-AES256-GCM-SHA384}',
        'sslv3': 0,
        'tls1': 0,
        'tls1_1': 0,
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '31.2',
        'server_ip_prefix' : '121.2'
        },

    {'cipher_name' : 'ECDHE-RSA-AES128-SHA256',
        'cipher' : '{ECDHE-RSA-AES128-SHA256}',
        'sslv3': 0,
        'tls1': 0,
        'tls1_1': 0,
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '32.2',
        'server_ip_prefix' : '122.2'
        },

    {'cipher_name' : 'ECDHE-RSA-AES256-SHA384',
        'cipher' : '{ECDHE-RSA-AES256-SHA384}',
        'sslv3': 0,
        'tls1': 0,
        'tls1_1': 0,
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '33.2',
        'server_ip_prefix' : '123.2'
        },

    {'cipher_name' : 'DHE-RSA-AES256-SHA256',
        'cipher' : '{DHE-RSA-AES256-SHA256}',
        'sslv3': 0,
        'tls1': 0,
        'tls1_1': 0,
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '34.2',
        'server_ip_prefix' : '124.2'
        },

    {'cipher_name' : 'DHE-RSA-AES256-GCM-SHA384',
        'cipher' : '{DHE-RSA-AES256-GCM-SHA384}',
        'sslv3': 0,
        'tls1': 0,
        'tls1_1': 0,
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '35.2',
        'server_ip_prefix' : '125.2'
        },

    {'cipher_name' : 'ECDHE-RSA-CHACHA20-POLY1305',
        'cipher' : '{ECDHE-RSA-CHACHA20-POLY1305}',
        'sslv3': 0,
        'tls1': 0,
        'tls1_1': 0,
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '36.2',
        'server_ip_prefix' : '126.2'
        },

    {'cipher_name' : 'TLS_AES_128_GCM_SHA256',
        'cipher' : '{TLS_AES_128_GCM_SHA256}',
        'sslv3': 0,
        'tls1': 0,
        'tls1_1': 0,
        'tls1_2' : 0,
        'tls1_3' : '{tls1_3}',
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '37.2',
        'server_ip_prefix' : '139.2'
        },

    {'cipher_name' : 'TLS_AES_256_GCM_SHA384',
        'cipher' : '{TLS_AES_256_GCM_SHA384}',
        'sslv3': 0,
        'tls1': 0,
        'tls1_1': 0,
        'tls1_2' : 0,
        'tls1_3' : '{tls1_3}',
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '38.2',
        'server_ip_prefix' : '128.2'
        },

    {'cipher_name' : 'TLS_CHACHA20_POLY1305_SHA256',
        'cipher' : '{TLS_CHACHA20_POLY1305_SHA256}',
        'sslv3': 0,
        'tls1': 0,
        'tls1_1': 0,
        'tls1_2' : 0,
        'tls1_3' : '{tls1_3}',
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '39.2',
        'server_ip_prefix' : '129.2'
        },

    {'cipher_name' : 'ECDHE-ECDSA-AES128-GCM-SHA256',
        'cipher' : '{ECDHE-ECDSA-AES128-GCM-SHA256}',
        'sslv3': 0,
        'tls1': 0,
        'tls1_1': 0,
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server2.cert',
        'srv_key' : '/rundir/certs/server2.key',
        'client_ip_prefix' : '40.2',
        'server_ip_prefix' : '130.2'
        },

    {'cipher_name' : 'ECDHE-ECDSA-AES256-GCM-SHA384',
        'cipher' : '{ECDHE-ECDSA-AES256-GCM-SHA384}',
        'sslv3': 0,
        'tls1': 0,
        'tls1_1': 0,
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server2.cert',
        'srv_key' : '/rundir/certs/server2.key',
        'client_ip_prefix' : '41.2',
        'server_ip_prefix' : '131.2'
        },

    {'cipher_name' : 'ECDHE-ECDSA-AES128-SHA256',
        'cipher' : '{ECDHE-ECDSA-AES128-SHA256}',
        'sslv3': 0,
        'tls1': 0,
        'tls1_1': 0,
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server2.cert',
        'srv_key' : '/rundir/certs/server2.key',
        'client_ip_prefix' : '42.2',
        'server_ip_prefix' : '132.2'
        },

    {'cipher_name' : 'ECDHE-ECDSA-AES256-SHA384',
        'cipher' : '{ECDHE-ECDSA-AES256-SHA384}',
        'sslv3': 0,
        'tls1': 0,
        'tls1_1': 0,
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server2.cert',
        'srv_key' : '/rundir/certs/server2.key',
        'client_ip_prefix' : '43.2',
        'server_ip_prefix' : '133.2'
        },

    {'cipher_name' : 'RC4-MD5',
        'cipher' : '{RC4-MD5}',
        'sslv3' : '{sslv3}',
        'tls1' : '{tls1}',
        'tls1_1' : '{tls1_1}',
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '44.2',
        'server_ip_prefix' : '134.2'
        },

    {'cipher_name' : 'RC4-SHA',
        'cipher' : '{RC4-SHA}',
        'sslv3' : '{sslv3}',
        'tls1' : '{tls1}',
        'tls1_1' : '{tls1_1}',
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '45.2',
        'server_ip_prefix' : '135.2'
        },

    {'cipher_name' : 'DES-CBC-SHA',
        'cipher' : '{DES-CBC-SHA}',
        'sslv3' : '{sslv3}',
        'tls1' : '{tls1}',
        'tls1_1' : '{tls1_1}',
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '46.2',
        'server_ip_prefix' : '136.2'
        },

    {'cipher_name' : 'DES-CBC3-SHA',
        'cipher' : '{DES-CBC3-SHA}',
        'sslv3' : '{sslv3}',
        'tls1' : '{tls1}',
        'tls1_1' : '{tls1_1}',
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '47.2',
        'server_ip_prefix' : '137.2'
        },

    {'cipher_name' : 'SEED-SHA',
        'cipher' : '{SEED-SHA}',
        'sslv3' : '{sslv3}',
        'tls1' : '{tls1}',
        'tls1_1' : '{tls1_1}',
        'tls1_2' : '{tls1_2}',
        'tls1_3' : 0,
        'srv_cert' : '/rundir/certs/server.cert',
        'srv_key' : '/rundir/certs/server.key',
        'client_ip_prefix' : '48.2',
        'server_ip_prefix' : '138.2'}
]


def start_containers(pod_info, c_args):
    rundir_map = "--volume={}:{}".format (c_args.host_rundir
                                                , c_args.target_rundir)

    srcdir_map = "--volume={}:{}".format (c_args.host_srcdir
                                                , c_args.target_srcdir)

    for z_index in range( pod_info['containers']['count'] ):
        zone_cname = "{}-zone-{}".format (c_args.pod, z_index+1)

        cmd_str = "sudo docker run --cap-add=SYS_PTRACE --security-opt seccomp=unconfined --network=bridge --privileged --name {} -it -d {} {} tlspack/tgen:latest /bin/bash".format (zone_cname, rundir_map, srcdir_map)
        os.system (cmd_str)

        for network in pod_info['networks']:
            host_iface = network['host_iface']
            host_macvlan = network['host_macvlan']
            cmd_str = "sudo ip link set dev {} up".format(host_iface)
            os.system (cmd_str)
            cmd_str = "sudo docker network connect {} {}".format(host_macvlan, zone_cname)
            os.system (cmd_str)

        cmd_str = "sudo docker exec -d {} cp -f /rundir/bin/tlspack.exe /usr/local/bin".format(zone_cname)
        os.system (cmd_str)
        cmd_str = "sudo docker exec -d {} chmod +x /usr/local/bin/tlspack.exe".format(zone_cname)
        os.system (cmd_str)

        cmd_str = "sudo docker exec -d {} cp -f /rundir/bin/rpc_proxy_main.py /usr/local/bin".format(zone_cname)
        os.system (cmd_str)
        cmd_str = "sudo docker exec -d {} chmod +x /usr/local/bin/rpc_proxy_main.py".format(zone_cname)
        os.system (cmd_str)

        cmd_str = "docker inspect --format='{{.NetworkSettings.IPAddress}}' " + zone_cname
        zone_ipaddr = subprocess.check_output(cmd_str, shell=True, close_fds=True).strip()

        cmd_str = "sudo docker exec -d {} python3 /usr/local/bin/rpc_proxy_main.py {} {}".format(zone_cname, zone_ipaddr, 8081)
        os.system (cmd_str)


def stop_containers(pod_info, c_args):
    for z_index in range( pod_info['containers']['count'] ):
        zone_cname = "{}-zone-{}".format (c_args.pod, z_index+1)
        cmd_str = "sudo docker rm -f {}".format (zone_cname)
        os.system (cmd_str)


def restart_containers(pod_info, c_args):
    stop_containers(pod_info, c_args)
    start_containers(pod_info, c_args)

                                
def add_traffic_params (arg_parser):

    arg_parser.add_argument('--sysinit'
                                , action="store_true"
                                , default=False
                                , help = 'sysinit')

    arg_parser.add_argument('--host_rundir'
                                , action="store"
                                , default='/root/rundir'
                                , help = 'rundir path')

    arg_parser.add_argument('--target_rundir'
                                , action="store"
                                , default='/rundir'
                                , help = 'rundir path in container')

    arg_parser.add_argument('--host_srcdir'
                                , action="store"
                                , default='/root/tcpdash'
                                , help = 'host_srcdir')

    arg_parser.add_argument('--target_srcdir'
                                , action="store"
                                , default='/root/tcpdash'
                                , help = 'target_srcdir')

    arg_parser.add_argument('--pod'
                                , action="store"
                                , required=True
                                , help = 'pod name')

    arg_parser.add_argument('--runtag'
                                , action="store"
                                , required=True
                                , help = 'run id')

    arg_parser.add_argument('--na'
                                , action="store"
                                , required=True
                                , dest='na_iface'
                                , help = 'na_iface name')

    arg_parser.add_argument('--nb'
                                , action="store"
                                , required=True
                                , dest='nb_iface'
                                , help = 'nb_iface name')

    arg_parser.add_argument('--cps'
                                , action="store"
                                , type=int
                                , required=True
                                , help = 'tps : 1 - 10000')

    arg_parser.add_argument('--max_pipeline'
                                , action="store"
                                , type=int
                                , default=100
                                , help = 'max_pipeline : 1 - 10000')

    arg_parser.add_argument('--max_active'
                                , action="store"
                                , type=int
                                , default=100
                                , help = 'max_active : 1 - 2000000')

    arg_parser.add_argument('--cipher'
                                , action="store"
                                , help = 'command name'
                                , required=True)

    arg_parser.add_argument('--sslv3'
                                , action="store_true"
                                , default=False
                                , help = '0/1')

    arg_parser.add_argument('--tls1'
                                , action="store_true"
                                , default=False
                                , help = '0/1')
                                
    arg_parser.add_argument('--tls1_1'
                                , action="store_true"
                                , default=False
                                , help = '0/1')

    arg_parser.add_argument('--tls1_2'
                                , action="store_true"
                                , default=False
                                , help = '0/1')

    arg_parser.add_argument('--tls1_3'
                                , action="store_true"
                                , default=False
                                , help = '0/1')

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

    arg_parser.add_argument('--app_next_write'
                                , action="store"
                                , type=int
                                , default=0
                                , help = 'app_next_write')

    arg_parser.add_argument('--app_cs_data_len'
                                , action="store"
                                , type=int
                                , default=128
                                , help = 'app_cs_data_len')

    arg_parser.add_argument('--app_sc_data_len'
                                , action="store"
                                , type=int
                                , default=128
                                , help = 'app_sc_data_len')

    arg_parser.add_argument('--app_rcv_buff'
                                , action="store"
                                , type=int
                                , default=0
                                , help = 'app_rcv_buff')

    arg_parser.add_argument('--app_snd_buff'
                                , action="store"
                                , type=int
                                , default=0
                                , help = 'app_snd_buff')

    arg_parser.add_argument('--tcp_rcv_buff'
                                , action="store"
                                , type=int
                                , default=0
                                , help = 'tcp_rcv_buff')

    arg_parser.add_argument('--tcp_snd_buff'
                                , action="store"
                                , type=int
                                , default=0
                                , help = 'tcp_snd_buff')

    arg_parser.add_argument('--app_cs_starttls_len'
                                , action="store"
                                , type=int
                                , default=0
                                , help = 'app_cs_starttls_len')

    arg_parser.add_argument('--app_sc_starttls_len'
                            , action="store"
                            , type=int
                            , default=0
                            , help = 'app_sc_starttls_len')

    arg_parser.add_argument('--port_begin'
                            , action="store"
                            , type=int
                            , default=5000
                            , help = 'app_sc_starttls_len')


def add_proxy_params (arg_parser):

    arg_parser.add_argument('--sysinit'
                                , action="store_true"
                                , default=False
                                , help = 'sysinit')

    arg_parser.add_argument('--host_rundir'
                                , action="store"
                                , default='/root/rundir'
                                , help = 'rundir path')

    arg_parser.add_argument('--target_rundir'
                                , action="store"
                                , default='/rundir'
                                , help = 'rundir path in container')

    arg_parser.add_argument('--host_srcdir'
                                , action="store"
                                , default='/root/tcpdash'
                                , help = 'host_srcdir')

    arg_parser.add_argument('--target_srcdir'
                                , action="store"
                                , default='/root/tcpdash'
                                , help = 'target_srcdir')

    arg_parser.add_argument('--pod'
                                , action="store"
                                , required=True
                                , help = 'pod name')

    arg_parser.add_argument('--runtag'
                                , action="store"
                                , required=True
                                , help = 'run id')

    arg_parser.add_argument('--proxy_traffic_vlan'
                                , action="store"
                                , type=int
                                , required=True
                                , help = '1-4095')

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

    arg_parser.add_argument('--ta_macvlan'
                                , action="store"
                                , default=''
                                , help = 'ta host macvlan')

    arg_parser.add_argument('--tb_macvlan'
                                , action="store"
                                , default=''
                                , help = 'tb host macvlan')

    arg_parser.add_argument('--ta_iface_container'
                                , action="store"
                                , help = 'ta interface'
                                , default='eth1')

    arg_parser.add_argument('--tb_iface_container'
                                , action="store"
                                , help = 'tb interface'
                                , default='eth2')

    arg_parser.add_argument('--ta_subnet'
                                , action="store"
                                , help = 'ta subnet'
                                , required=True)

    arg_parser.add_argument('--tb_subnet'
                                , action="store"
                                , help = 'tb subnet'
                                , required=True)

    arg_parser.add_argument('--ta_tcpdump'
                                , action="store"
                                , help = 'ta tcpdump'
                                , default='-c 100')

    arg_parser.add_argument('--tb_tcpdump'
                                , action="store"
                                , help = 'tb tcpdump'
                                , default='-c 100')

    arg_parser.add_argument('--client_mac_seed'
                                , action="store"
                                , help = '5 bytes'
                                , default='02:42:ac:14:00')

    arg_parser.add_argument('--server_mac_seed'
                                , action="store"
                                , help = '5 bytes'
                                , default='02:42:ac:15:00')


def add_stop_params (arg_parser):

    arg_parser.add_argument('--host_rundir'
                                , action="store"
                                , default='/root/rundir'
                                , help = 'rundir path')

    arg_parser.add_argument('--runtag'
                                , action="store"
                                , required=True
                                , help = 'run id')

    arg_parser.add_argument('--force'
                                , action="store_true"
                                , default=False
                                , help = '0/1')


def zone_start_thread(pod_info, c_args, z_index):

    zone_cname = "{}-zone-{}".format (c_args.pod, z_index+1)

    cmd_str = "docker inspect --format='{{.NetworkSettings.IPAddress}}' " + zone_cname
    zone_ipaddr = subprocess.check_output(cmd_str, shell=True, close_fds=True).strip()

    cfg_file = os.path.join(c_args.target_rundir, 'traffic', c_args.runtag, 'config.json')

    requests.post('http://{}:8081/start'.format(zone_ipaddr)
                    , data = json.dumps({'cfg_file':'/rundir/traffic/cps1/config.json'
                                        , 'z_index' : z_index
                                        , 'net_ifaces' : map (lambda n : n['container_iface'], pod_info['networks']) })
                    , headers={'Content-type': 'application/json', 'Accept': 'text/plain'})


def start_run(c_args, traffic_s):
    registry_dir = os.path.join(c_args.host_rundir, 'registry')

    registry_dir_pod = os.path.join(registry_dir, 'pods', c_args.pod)
    registry_file_pod = os.path.join(registry_dir_pod, 'config.json')

    registry_dir_run = os.path.join(registry_dir, 'runs', c_args.runtag)
    registry_file_run = os.path.join(registry_dir_run, 'config.json')
    
    if os.path.exists(registry_file_run):
        with open (registry_file_run) as f:
            registry_run_info = json.load(f)
            print 'error: {} already running in pod {}'.format (c_args.runtag, registry_run_info['pod'])
            sys.exit(1)

    with open(registry_file_pod) as f:
        pod_info = json.load(f)

    if pod_info.get('runing'):
        print 'error: {} pod in use running {}'.format(c_args.pod, pod_info['runing'])
        sys.exit(1)

    # create config dir; file
    try:
        cfg_j = json.loads (traffic_s)
        traffic_s = json.dumps(cfg_j, indent=4)
    except:
        print traffic_s
        sys.exit(1)

    cfg_dir = os.path.join(c_args.host_rundir, 'traffic', c_args.runtag)
    cfg_file = os.path.join(cfg_dir, 'config.json')

    os.system ( 'rm -rf {}'.format(cfg_dir) )
    os.system ( 'mkdir -p {}'.format(cfg_dir) )
    os.system ( 'mkdir -p {}'.format(os.path.join(cfg_dir, 'pcaps')) )
    os.system ( 'mkdir -p {}'.format(os.path.join(cfg_dir, 'stats')) )
    os.system ( 'mkdir -p {}'.format(os.path.join(cfg_dir, 'logs')) )

    with open(cfg_file, 'w') as f:
        f.write(traffic_s)

    if c_args.sysinit or not pod_info.get('ready', 0):
        restart_containers (pod_info, c_args)
        pod_info['ready'] = 1
        time.sleep (5)

    pod_info['runing'] = c_args.runtag

    # create registry entries
    os.system ('mkdir -p {}'.format(registry_dir_run))

    with open(registry_file_run, 'w') as f:
        json.dump({'pod' : c_args.pod}, f)

    with open(registry_file_pod, 'w') as f:
        json.dump(pod_info, f)

    for next_step in range(1, 3):
        z_threads = []
        z_index = -1
        for zone in cfg_j['zones']:
            z_index += 1

            if not zone['enable']:
                continue

            if zone.get('step', 1) == next_step:
                thd = Thread(target=zone_start_thread, args=[pod_info, c_args, z_index])
                thd.daemon = True
                thd.start()
                z_threads.append(thd)
        if z_threads:
            for thd in z_threads:
                thd.join()
            time.sleep(1) 


def zone_stop_thread(pod_info, c_args, z_index):

    zone_cname = "{}-zone-{}".format (c_args.pod, z_index+1)

    cmd_str = "docker inspect --format='{{.NetworkSettings.IPAddress}}' " + zone_cname
    zone_ipaddr = subprocess.check_output(cmd_str, shell=True, close_fds=True).strip()

    requests.post('http://{}:8081/stop'.format(zone_ipaddr)
                    , data = json.dumps({'net_ifaces' : ['eth1', 'eth2' ] })
                    , headers={'Content-type': 'application/json', 'Accept': 'text/plain'})


def stop_run(pod_info, c_args):

    registry_dir = os.path.join(c_args.host_rundir, 'registry')

    registry_dir_pod = os.path.join(registry_dir, 'pods', c_args.pod)
    registry_file_pod = os.path.join(registry_dir_pod, 'config.json')

    registry_dir_run = os.path.join(registry_dir, 'runs', c_args.runtag)
    registry_file_run = os.path.join(registry_dir_run, 'config.json')

    if c_args.force:
        stop_containers (pod_info, c_args)
        pod_info['ready'] = 0
        pod_info['runing'] = ''
        with open(registry_file_pod, 'w') as f:
            json.dump(pod_info, f)
        os.system ( 'rm -rf {}'.format(registry_dir_run) )
        sys.exit(1)

    # check if config runing
    if not os.path.exists(registry_dir_run):
        print 'test {} not running'.format(pod_info['runing'])
        sys.exit(1)

    if not pod_info.get('runing'):
        print 'no test running on pod {}'.format (c_args.pod)
        sys.exit(1)

    cfg_dir = os.path.join(c_args.host_rundir, 'traffic', pod_info['runing'])
    cfg_file = os.path.join(cfg_dir, 'config.json')

    try:
        with open(cfg_file) as f:
            cfg_j = json.load(f)
    except:
        print 'invalid config file' 
        sys.exit(1)


    z_threads = []
    z_index = -1
    for zone in cfg_j['zones']:
        z_index += 1

        if not zone['enable']:
            continue

        thd = Thread(target=zone_stop_thread, args=[pod_info, c_args, z_index])
        thd.daemon = True
        thd.start()
        z_threads.append(thd)

    for thd in z_threads:
        thd.join()

    os.system ("rm -rf {}".format (registry_dir_run))
    pod_info['ready'] = 1
    pod_info['runing'] = ''
    with open(registry_file_pod, 'w') as f:
        json.dump(pod_info, f)


def add_cps_params (cmd_parser):
    cmd_parser.add_argument('--ecdsa_cert'
                                , action="store_true"
                                , default=False
                                , help = '0/1')


def process_cps_template (c_args):
    tlspack_cfg = jinja2.Template('''
    {
        "tgen_app" : "cps",
        "zones" : [
            {% set ns = namespace(cs_grp_count=0, srv_count=0) %}
            {%- for traffic_id in range(1, PARAMS.traffic_paths+1) %}
                {
                    "zone_label" : "zone-{{traffic_id}}-client",
                    "enable" : 1,
                    "step" : 2,
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
                                            "clnt_port_begin" : {{PARAMS.port_begin}},
                                            "clnt_port_end" : 65000,
                                            "cipher" : "{{PARAMS.cipher}}",
                                            "tls_version" : "{{tls_ver}}",
                                            "close_type" : "fin",
                                            "close_notify" : "no_send",
                                            "app_rcv_buff" : {{PARAMS.app_rcv_buff}},
                                            "app_snd_buff" : {{PARAMS.app_snd_buff}},
                                            "write_chunk" : {{PARAMS.app_next_write}},
                                            "tcp_rcv_buff" : {{PARAMS.tcp_rcv_buff}},
                                            "tcp_snd_buff" : {{PARAMS.tcp_snd_buff}},
                                            "cs_data_len" : {{PARAMS.app_cs_data_len}},
                                            "sc_data_len" : {{PARAMS.app_sc_data_len}},
                                            "cs_start_tls_len" : {{PARAMS.app_cs_starttls_len}},
                                            "sc_start_tls_len" : {{PARAMS.app_sc_starttls_len}}
                                        }
                                    {%- endif %}
                                {%- endfor %}                         
                            ]
                        }
                    ],

                    "zone_cmds" : [
                        "ip link set dev {{PARAMS.na_iface_container}} up",
                        "ifconfig {{PARAMS.na_iface_container}} hw ether {{PARAMS.client_mac_seed}}:{{'{:02x}'.format(traffic_id)}}",
                        "ip route add default dev {{PARAMS.na_iface_container}} table 200",
                        "ip -4 route add local 12.2{{traffic_id}}.51.0/24 dev lo",
                        "ip rule add from 12.2{{traffic_id}}.51.0/24 table 200",
                        "tcpdump -i {{PARAMS.na_iface_container}} {{PARAMS.tcpdump}} -w {{PARAMS.pcaps_dir_container.rstrip('/')}}/zone-{{traffic_id}}-client.pcap &"
                    ]
                }
                ,
                {
                    "zone_label" : "zone-{{traffic_id}}-server",
                    "enable" : 1,
                    "step" : 1,
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
                                            "emulation_id" : 0,
                                            "begin_cert_index" : {{traffic_id*2000}},
                                            "end_cert_index" : 100000, 
                                            "srv_ip" : "14.2{{traffic_id}}.51.{{loop.index}}",
                                            "srv_port" : 443,
                                            "srv_cert" : "{{PARAMS.server_cert}}",
                                            "srv_key" : "{{PARAMS.server_key}}",
                                            "cipher" : "{{PARAMS.cipher}}",
                                            "tls_version" : "{{tls_ver}}",
                                            "close_type" : "fin",
                                            "close_notify" : "no_send",
                                            "app_rcv_buff" : {{PARAMS.app_rcv_buff}},
                                            "app_snd_buff" : {{PARAMS.app_snd_buff}},
                                            "write_chunk" : {{PARAMS.app_next_write}},
                                            "tcp_rcv_buff" : {{PARAMS.tcp_rcv_buff}},
                                            "tcp_snd_buff" : {{PARAMS.tcp_snd_buff}},
                                            "cs_data_len" : {{PARAMS.app_cs_data_len}},
                                            "sc_data_len" : {{PARAMS.app_sc_data_len}},
                                            "cs_start_tls_len" : {{PARAMS.app_cs_starttls_len}},
                                            "sc_start_tls_len" : {{PARAMS.app_sc_starttls_len}}
                                        }
                                    {%- endif %}
                                {%- endfor %}
                            ]
                        }
                    ],

                    "zone_cmds" : [
                        "ip link set dev {{PARAMS.nb_iface_container}} up",
                        "ifconfig {{PARAMS.nb_iface_container}} hw ether {{PARAMS.server_mac_seed}}:{{'{:02x}'.format(traffic_id)}}",
                        "ip route add default dev {{PARAMS.nb_iface_container}} table 200",
                        "ip -4 route add local 14.2{{traffic_id}}.51.0/24 dev lo",
                        "ip rule add from 14.2{{traffic_id}}.51.0/24 table 200",
                        "tcpdump -i {{PARAMS.nb_iface_container}} {{PARAMS.tcpdump}} -w {{PARAMS.pcaps_dir_container.rstrip('/')}}/zone-{{traffic_id}}-server.pcap &"
                    ]
                }
                {{ "," if not loop.last }}
            {%- endfor %}
        ]
    }
    ''')
    if c_args.ecdsa_cert:
        c_args.server_cert = '/rundir/certs/server2.cert'
        c_args.server_key = '/rundir/certs/server2.key'
    else:
        c_args.server_cert = '/rundir/certs/server.cert'
        c_args.server_key = '/rundir/certs/server.key'
    return tlspack_cfg.render(PARAMS = c_args)


def add_bw_params (cmd_parser):
    cmd_parser.add_argument('--ecdsa_cert'
                                , action="store_true"
                                , default=False
                                , help = '0/1')


def process_bw_template (c_args):

    tlspack_cfg = jinja2.Template('''
    {
        "tgen_app" : "bw",
        "zones" : [
            {% set ns = namespace(cs_grp_count=0, srv_count=0) %}
            {%- for traffic_id in range(1, PARAMS.traffic_paths+1) %}
                {
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
                                            "srv_ip"   : "24.2{{traffic_id}}.51.{{loop.index}}",
                                            "srv_port" : 443,
                                            "clnt_ip_begin" : "22.2{{traffic_id}}.51.{{1+loop.index0*10}}",
                                            "clnt_ip_end" : "22.2{{traffic_id}}.51.{{loop.index*10}}",
                                            "clnt_port_begin" : {{PARAMS.port_begin}},
                                            "clnt_port_end" : 65000,
                                            "cipher" : "{{PARAMS.cipher}}",
                                            "tls_version" : "{{tls_ver}}",
                                            "close_type" : "reset",
                                            "close_notify" : "no_send",
                                            "app_rcv_buff" : {{PARAMS.app_rcv_buff}},
                                            "app_snd_buff" : {{PARAMS.app_snd_buff}},
                                            "write_chunk" : {{PARAMS.app_next_write}},
                                            "tcp_rcv_buff" : {{PARAMS.tcp_rcv_buff}},
                                            "tcp_snd_buff" : {{PARAMS.tcp_snd_buff}},
                                            "cs_data_len" : {{PARAMS.app_cs_data_len}},
                                            "sc_data_len" : {{PARAMS.app_sc_data_len}},
                                            "cs_start_tls_len" : {{PARAMS.app_cs_starttls_len}},
                                            "sc_start_tls_len" : {{PARAMS.app_sc_starttls_len}}
                                        }
                                    {%- endif %}
                                {%- endfor %}                         
                            ]
                        }
                    ],

                    "zone_cmds" : [
                        "ip link set dev {{PARAMS.na_iface_container}} up",
                        "ifconfig {{PARAMS.na_iface_container}} hw ether {{PARAMS.client_mac_seed}}:{{'{:02x}'.format(traffic_id)}}",
                        "ip route add default dev {{PARAMS.na_iface_container}} table 200",
                        "ip -4 route add local 22.2{{traffic_id}}.51.0/24 dev lo",
                        "ip rule add from 22.2{{traffic_id}}.51.0/24 table 200",
                        "tcpdump -i {{PARAMS.na_iface_container}} {{PARAMS.tcpdump}} -w {{PARAMS.pcaps_dir_container.rstrip('/')}}/zone-{{traffic_id}}-client.pcap &"
                    ]                    
                }
                ,
                {
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
                                            "srv_ip" : "24.2{{traffic_id}}.51.{{loop.index}}",
                                            "srv_port" : 443,
                                            "srv_cert" : "{{PARAMS.server_cert}}",
                                            "srv_key" : "{{PARAMS.server_key}}",
                                            "cipher" : "{{PARAMS.cipher}}",
                                            "tls_version" : "{{tls_ver}}",
                                            "close_type" : "reset",
                                            "close_notify" : "no_send",
                                            "app_rcv_buff" : {{PARAMS.app_rcv_buff}},
                                            "app_snd_buff" : {{PARAMS.app_snd_buff}},
                                            "write_chunk" : {{PARAMS.app_next_write}},
                                            "tcp_rcv_buff" : {{PARAMS.tcp_rcv_buff}},
                                            "tcp_snd_buff" : {{PARAMS.tcp_snd_buff}},
                                            "cs_data_len" : {{PARAMS.app_cs_data_len}},
                                            "sc_data_len" : {{PARAMS.app_sc_data_len}},
                                            "cs_start_tls_len" : {{PARAMS.app_cs_starttls_len}},
                                            "sc_start_tls_len" : {{PARAMS.app_sc_starttls_len}}
                                        }
                                    {%- endif %}
                                {%- endfor %}
                            ]
                        }
                    ],

                    "zone_cmds" : [
                        "ip link set dev {{PARAMS.nb_iface_container}} up",
                        "ifconfig {{PARAMS.nb_iface_container}} hw ether {{PARAMS.server_mac_seed}}:{{'{:02x}'.format(traffic_id)}}",
                        "ip route add default dev {{PARAMS.nb_iface_container}} table 200",
                        "ip -4 route add local 24.2{{traffic_id}}.51.0/24 dev lo",
                        "ip rule add from 24.2{{traffic_id}}.51.0/24 table 200",
                        "tcpdump -i {{PARAMS.nb_iface_container}} {{PARAMS.tcpdump}} -w {{PARAMS.pcaps_dir_container.rstrip('/')}}/zone-{{traffic_id}}-server.pcap &"
                    ]
                }
                {{ "," if not loop.last }}
            {%- endfor %}
        ]
    }
    ''')

    if c_args.ecdsa_cert:
        c_args.server_cert = '/rundir/certs/server2.cert'
        c_args.server_key = '/rundir/certs/server2.key'
    else:
        c_args.server_cert = '/rundir/certs/server.cert'
        c_args.server_key = '/rundir/certs/server.key'
    return tlspack_cfg.render(PARAMS = c_args)


def add_tproxy_params (cmd_parser):
    pass


def process_tproxy_template (c_args):
    tlspack_cfg = jinja2.Template ('''{
        "tgen_app" : "tproxy",
        "zones" : [
            {
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
                
                "host_cmds" : [
                    "sudo ip link set dev {{PARAMS.ta_iface}} up",
                    "sudo ip link set dev {{PARAMS.tb_iface}} up",
                    "sudo docker network connect {{PARAMS.ta_macvlan}} {{PARAMS.runtag}}-zone-1-proxy",
                    "sudo docker network connect {{PARAMS.tb_macvlan}} {{PARAMS.runtag}}-zone-1-proxy"
                ],

                "zone_cmds" : [
                    "sysctl net.ipv4.conf.all.rp_filter=0",
                    "sysctl net.ipv4.conf.default.rp_filter=0",

                    "ip link set dev {{PARAMS.ta_iface_container}} up",
                    "ifconfig {{PARAMS.ta_iface_container}} hw ether 00:50:56:8c:5a:54",
                    "sysctl net.ipv4.conf.{{PARAMS.ta_iface_container}}.rp_filter=0",
                    "ip link add link {{PARAMS.ta_iface_container}} name {{PARAMS.ta_iface_container}}.{{PARAMS.proxy_traffic_vlan}} type vlan id {{PARAMS.proxy_traffic_vlan}}",
                    "ip link set dev {{PARAMS.ta_iface_container}}.{{PARAMS.proxy_traffic_vlan}} up",
                    "ip addr add 1.1.1.1/24 dev {{PARAMS.ta_iface_container}}.{{PARAMS.proxy_traffic_vlan}}",
                    "arp -i {{PARAMS.ta_iface_container}}.{{PARAMS.proxy_traffic_vlan}} -s 1.1.1.254 00:50:56:8c:86:c3",
                    "ip route add {{PARAMS.ta_subnet}} via 1.1.1.254 dev {{PARAMS.ta_iface_container}}.{{PARAMS.proxy_traffic_vlan}}",

                    "ip link set dev {{PARAMS.tb_iface_container}} up",
                    "ifconfig {{PARAMS.tb_iface_container}} hw ether 00:50:56:8c:86:c3",
                    "sysctl net.ipv4.conf.{{PARAMS.tb_iface_container}}.rp_filter=0",
                    "ip link add link {{PARAMS.tb_iface_container}} name {{PARAMS.tb_iface_container}}.{{PARAMS.proxy_traffic_vlan}} type vlan id {{PARAMS.proxy_traffic_vlan}}",
                    "ip link set dev {{PARAMS.tb_iface_container}}.{{PARAMS.proxy_traffic_vlan}} up",
                    "ip addr add 2.2.2.1/24 dev {{PARAMS.tb_iface_container}}.{{PARAMS.proxy_traffic_vlan}}",
                    "arp -i {{PARAMS.tb_iface_container}}.{{PARAMS.proxy_traffic_vlan}} -s 2.2.2.254 00:50:56:8c:5a:54",
                    "ip route add {{PARAMS.tb_subnet}} via 2.2.2.254 dev {{PARAMS.tb_iface_container}}.{{PARAMS.proxy_traffic_vlan}}",

                    "iptables -t mangle -N DIVERT",
                    "iptables -t mangle -A PREROUTING -p tcp -m socket -j DIVERT",
                    "iptables -t mangle -A DIVERT -j MARK --set-mark 1",
                    "iptables -t mangle -A DIVERT -j ACCEPT",
                    "ip rule add fwmark 1 lookup 100",
                    "ip route add local 0.0.0.0/0 dev lo table 100",
                    "iptables -t mangle -A PREROUTING -i {{PARAMS.ta_iface_container}}.{{PARAMS.proxy_traffic_vlan}} -p tcp --dport 443 -j TPROXY --tproxy-mark 0x1/0x1 --on-port 883",
                    "iptables -t mangle -A PREROUTING -i {{PARAMS.tb_iface_container}}.{{PARAMS.proxy_traffic_vlan}} -p tcp --dport 443 -j TPROXY --tproxy-mark 0x1/0x1 --on-port 883",

                    "tcpdump -i {{PARAMS.ta_iface_container}} {{PARAMS.ta_tcpdump}} -w {{PARAMS.pcaps_dir_container.rstrip('/')}}/zone-1-proxy-ta.pcap &",
                    "tcpdump -i {{PARAMS.tb_iface_container}} {{PARAMS.tb_tcpdump}} -w {{PARAMS.pcaps_dir_container.rstrip('/')}}/zone-1-proxy-tb.pcap &"
                ]
            }
        ]
    }
    ''')

    return tlspack_cfg.render(PARAMS = c_args)


def add_mcert_params (cmd_parser):
    pass


def process_mcert_template (c_args):
    tlspack_cfg = jinja2.Template('''
    {
        "tgen_app" : "mcert",
        "zones" : [
            {% set ns = namespace(cs_grp_count=0, srv_count=0) %}
            {%- for traffic_id in range(1, PARAMS.traffic_paths+1) %}
                {
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
                                            "clnt_port_begin" : {{PARAMS.port_begin}},
                                            "clnt_port_end" : 65000,
                                            "cipher" : "{{PARAMS.cipher}}",
                                            "tls_version" : "{{tls_ver}}",
                                            "close_type" : "fin",
                                            "close_notify" : "no_send",
                                            "app_rcv_buff" : {{PARAMS.app_rcv_buff}},
                                            "app_snd_buff" : {{PARAMS.app_snd_buff}},
                                            "write_chunk" : {{PARAMS.app_next_write}},
                                            "tcp_rcv_buff" : {{PARAMS.tcp_rcv_buff}},
                                            "tcp_snd_buff" : {{PARAMS.tcp_snd_buff}},
                                            "cs_data_len" : {{PARAMS.app_cs_data_len}},
                                            "sc_data_len" : {{PARAMS.app_sc_data_len}},
                                            "cs_start_tls_len" : 0,
                                            "sc_start_tls_len" : 0
                                        }
                                    {%- endif %}
                                {%- endfor %}                         
                            ]
                        }
                    ],

                    "zone_cmds" : [
                        "ip link set dev {{PARAMS.na_iface_container}} up",
                        "ifconfig {{PARAMS.na_iface_container}} hw ether {{PARAMS.client_mac_seed}}:{{'{:02x}'.format(traffic_id)}}",
                        "ip route add default dev {{PARAMS.na_iface_container}} table 200",
                        "ip -4 route add local 12.2{{traffic_id}}.51.0/24 dev lo",
                        "ip rule add from 12.2{{traffic_id}}.51.0/24 table 200",
                        "tcpdump -i {{PARAMS.na_iface_container}} {{PARAMS.tcpdump}} -w {{PARAMS.pcaps_dir_container.rstrip('/')}}/zone-{{traffic_id}}-client.pcap &"
                    ]
                }
                ,
                {
                    "zone_label" : "zone-{{traffic_id}}-server",
                    "enable" : 1,
                    "iface" : "{{PARAMS.iface_container}}",
                    "tcpdump" : "{{PARAMS.tcpdump}}",
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
                                            "emulation_id" : 0,
                                            "srv_ip" : "14.2{{traffic_id}}.51.{{loop.index}}",
                                            "srv_port" : 443,
                                            "srv_cert" : "{{PARAMS.server_cert}}",
                                            "srv_key" : "{{PARAMS.server_key}}",
                                            "cipher" : "{{PARAMS.cipher}}",
                                            "tls_version" : "{{tls_ver}}",
                                            "close_type" : "fin",
                                            "close_notify" : "no_send",
                                            "app_rcv_buff" : {{PARAMS.app_rcv_buff}},
                                            "app_snd_buff" : {{PARAMS.app_snd_buff}},
                                            "write_chunk" : {{PARAMS.app_next_write}},
                                            "tcp_rcv_buff" : {{PARAMS.tcp_rcv_buff}},
                                            "tcp_snd_buff" : {{PARAMS.tcp_snd_buff}},
                                            "cs_data_len" : {{PARAMS.app_cs_data_len}},
                                            "sc_data_len" : {{PARAMS.app_sc_data_len}},
                                            "cs_start_tls_len" : 0,
                                            "sc_start_tls_len" : 0
                                        }
                                    {%- endif %}
                                {%- endfor %}
                            ]
                        }
                    ],

                    "zone_cmds" : [
                        "ip link set dev {{PARAMS.nb_iface_container}} up",
                        "ifconfig {{PARAMS.nb_iface_container}} hw ether {{PARAMS.server_mac_seed}}:{{'{:02x}'.format(traffic_id)}}",
                        "ip route add default dev {{PARAMS.nb_iface_container}} table 200",
                        "ip -4 route add local 14.2{{traffic_id}}.51.0/24 dev lo",
                        "ip rule add from 14.2{{traffic_id}}.51.0/24 table 200",
                        "tcpdump -i {{PARAMS.nb_iface_container}} {{PARAMS.tcpdump}} -w {{PARAMS.pcaps_dir_container.rstrip('/')}}/zone-{{traffic_id}}-server.pcap &"
                    ]
                }
                {{ "," if not loop.last }}
            {%- endfor %}
        ]
    }
    ''')

    return tlspack_cfg.render(PARAMS = c_args)


def get_arguments ():

    arg_parser = argparse.ArgumentParser(description = 'test commands')

    subparsers = arg_parser.add_subparsers(dest='cmd_name'
                                                    ,help='sub-command help')

    cps_parser = subparsers.add_parser('cps', help='cps help')
    add_traffic_params(cps_parser)
    add_cps_params (cps_parser)

    bw_parser = subparsers.add_parser('bw', help='bw help')
    add_traffic_params(bw_parser)
    add_bw_params (bw_parser)

    mcert_parser = subparsers.add_parser('mcert', help='mcert help')
    add_traffic_params(mcert_parser)
    add_mcert_params (mcert_parser)

    tproxy_parser = subparsers.add_parser('tproxy', help='tproxy help')
    add_proxy_params (tproxy_parser)
    add_tproxy_params (tproxy_parser)

    stop_parser = subparsers.add_parser('stop', help='stop help')
    add_stop_params (stop_parser)

    c_args = arg_parser.parse_args()

    return c_args


if __name__ == '__main__':

    try:
        c_args = get_arguments ()
    except Exception as er:
        print er
        sys.exit(1)

    if c_args.cmd_name in ['cps', 'bw', 'tproxy', 'mcert']:

        try:
            with open(os.path.join (c_args.host_rundir
                                    , 'registry'
                                    , 'pods'
                                    , c_args.pod
                                    , 'config.json') ) as f:
                pod_info = json.load(f)
        except Exception as er:
            print 'invalid pod {}'.format (c_args.pod)
            sys.exit(1)

        c_args.pcaps_dir_container = os.path.join(c_args.target_rundir, 'traffic', c_args.runtag, 'pcaps')

        if c_args.cmd_name in ['cps', 'bw', 'mcert']:
            c_args.na_iface_container = filter (lambda n : n['host_iface'] == c_args.na_iface, pod_info['networks'])[0]['container_iface']
            c_args.nb_iface_container = filter (lambda n : n['host_iface'] == c_args.nb_iface, pod_info['networks'])[0]['container_iface']

            c_args.traffic_paths = pod_info['containers']['count'] / 2

            c_args.cps = c_args.cps / c_args.traffic_paths
            c_args.max_active = c_args.max_active / c_args.traffic_paths
            c_args.max_pipeline = c_args.max_pipeline / c_args.traffic_paths


            supported_cipher_names = map(lambda x : x['cipher_name']
                                                    , supported_ciphers)

            if c_args.cmd_name == 'cipher':
                selected_ciphers = map(lambda x : x.strip(), c_args.cipher.split(':'))
                for ciph in selected_ciphers:
                    if ciph not in supported_cipher_names:
                        raise Exception ('unsupported cipher - ' + ciph)
            elif c_args.cmd_name == 'cps':
                if c_args.cipher not in supported_cipher_names:
                        raise Exception ('unsupported cipher - ' + c_args.cipher)

        elif c_args.cmd_name in ['tproxy']:
            c_args.ta_iface_container = filter (lambda n : n['host_iface'] == c_args.ta_iface, pod_info['networks'])[0]['container_iface']
            c_args.tb_iface_container = filter (lambda n : n['host_iface'] == c_args.tb_iface, pod_info['networks'])[0]['container_iface']

        if c_args.cmd_name == 'cps':
            traffic_s = process_cps_template(c_args)
        elif c_args.cmd_name == 'bw':
            traffic_s = process_bw_template(c_args)
        elif c_args.cmd_name == 'tproxy':
            traffic_s = process_tproxy_template(c_args)
        elif c_args.cmd_name == 'mcert':
            traffic_s = process_mcert_template(c_args)

        start_run(c_args, traffic_s)

    elif c_args.cmd_name == 'stop':
        try:
            with open(os.path.join (c_args.host_rundir
                                    , 'registry'
                                    , 'runs'
                                    , c_args.runtag
                                    , 'config.json') ) as f:
                runs_info = json.load(f)
        except Exception as er:
            print 'invalid runtag {}'.format(c_args.runtag)
            sys.exit(1)

        c_args.pod = runs_info['pod']

        try:
            with open(os.path.join (c_args.host_rundir
                                    , 'registry'
                                    , 'pods'
                                    , c_args.pod
                                    , 'config.json') ) as f:
                pod_info = json.load(f)
        except Exception as er:
            print 'invalid pod {}'.format (c_args.pod)
            sys.exit(1)

        stop_run (pod_info, c_args)


