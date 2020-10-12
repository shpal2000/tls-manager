__author__ = 'Shirish Pal'

import os
import sys
import argparse
import json
import jinja2

from run import start_run, is_valid_testbed, get_pcap_dir 
from run import get_pod_count, map_pod_interface


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

def get_arguments():
    arg_parser = argparse.ArgumentParser(description = 'tls : client - server')

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

    return arg_parser.parse_args()


def get_config (c_args):
    config_s = jinja2.Template('''
    {
        "tgen_app" : "cps",
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
    ''').render(PARAMS = c_args)

    try:
        config_j = json.loads(config_s)
    except:
        print config_s
        raise

    return config_j

if __name__ == '__main__':
    c_args = get_arguments ()

    if not is_valid_testbed(c_args.node_rundir, c_args.testbed):
        print 'invalid testbed {}'.format (c_args.testbed)
        sys.exit(1)

    supported_cipher_names = map(lambda x : x['cipher_name'], supported_ciphers)

    if c_args.cipher not in supported_cipher_names:
        print 'unsupported cipher {}'.format (c_args.cipher)
        sys.exit(1)

    selected_cipher = filter (lambda n : n['cipher_name'] == c_args.cipher
                                                        , supported_ciphers)[0]
    c_args.server_cert = selected_cipher['srv_cert']
    c_args.server_key = selected_cipher['srv_key']

    c_args.pod_pcap_dir = get_pcap_dir (c_args.pod_rundir, c_args.runid)

    c_args.pod_na_iface = map_pod_interface (c_args.node_rundir
                                                    , c_args.testbed
                                                    , c_args.na_iface)

    c_args.pod_nb_iface = map_pod_interface (c_args.node_rundir
                                                    , c_args.testbed
                                                    , c_args.nb_iface)

    c_args.traffic_paths = get_pod_count (c_args.node_rundir, c_args.testbed) / 2

    c_args.cps = c_args.cps / c_args.traffic_paths
    c_args.max_active = c_args.max_active / c_args.traffic_paths
    c_args.max_pipeline = c_args.max_pipeline / c_args.traffic_paths
    c_args.total_conn_count = c_args.total_conn_count / c_args.traffic_paths

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

