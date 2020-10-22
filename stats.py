__author__ = 'Shirish Pal'

import argparse
import pdb

from .run import collect_stats

def get_arguments ():
    arg_parser = argparse.ArgumentParser(description = 'stats')

    arg_parser.add_argument('--runid'
                                , action="store"
                                , required=True
                                , help = 'run id')
                                
    arg_parser.add_argument('--server_pod_ips'
                                , action="store"
                                , default=''
                                , help = 'run id')

    arg_parser.add_argument('--proxy_pod_ips'
                                , action="store"
                                , default=''
                                , help = 'run id')

    arg_parser.add_argument('--client_pod_ips'
                                , action="store"
                                , default=''
                                , help = 'run id')

    return arg_parser.parse_args()

if __name__ == '__main__':
    c_args = get_arguments ()

    server_pod_ips = c_args.server_pod_ips.split(':')
    proxy_pod_ips = c_args.proxy_pod_ips.split(':')
    client_pod_ips = c_args.client_pod_ips.split(':')

    # pdb.set_trace()
    collect_stats (c_args.runid
                    , server_pod_ips
                    , proxy_pod_ips
                    , client_pod_ips)
