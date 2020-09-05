__author__ = 'Shirish Pal'

import os
import sys
import argparse
import json
import time
import pdb

def add_c_arguments (arg_parser):
    arg_parser.add_argument('--host_run_dir'
                                , action="store"
                                , default='/root/rundir'
                                , help = 'host_run_dir')

def get_arguments ():
    arg_parser = argparse.ArgumentParser(description = 'commands')

    subparsers = arg_parser.add_subparsers(dest='mode'
                                            ,help='start|stop|restart')

    start_parser = subparsers.add_parser('start', help='start help')
    stop_parser = subparsers.add_parser('stop', help='stop help')
    restart_parser = subparsers.add_parser('restart', help='restart help')

    add_c_arguments (start_parser)
    add_c_arguments (stop_parser)
    add_c_arguments (restart_parser)

    start_parser.add_argument('--target_run_dir'
                                , action="store"
                                , default='/rundir'
                                , help = 'target_run_dir')
    restart_parser.add_argument('--target_run_dir'
                                , action="store"
                                , default='/rundir'
                                , help = 'target_run_dir')



    start_parser.add_argument('--host_src_dir'
                                , action="store"
                                , default='/root/tcpdash'
                                , help = 'host_src_dir')
    restart_parser.add_argument('--host_src_dir'
                                , action="store"
                                , default='/root/tcpdash'
                                , help = 'host_src_dir')



    start_parser.add_argument('--target_src_dir'
                                , action="store"
                                , default='/root/tcpdash'
                                , help = 'target_src_dir')
    restart_parser.add_argument('--target_src_dir'
                                , action="store"
                                , default='/root/tcpdash'
                                , help = 'target_src_dir')

    return arg_parser.parse_args()

def start_containers(host_info, c_args):
    rundir_map = "--volume={}:{}".format (c_args.host_run_dir
                                                , c_args.target_run_dir)

    srcdir_map = "--volume={}:{}".format (c_args.host_src_dir
                                                , c_args.target_src_dir)

    for z_index in range(host_info['cores']):
        zone_cname = "tp-zone-{}".format (z_index+1)

        cmd_str = "sudo docker run --cap-add=SYS_PTRACE --security-opt seccomp=unconfined --network=bridge --privileged --name {} -it -d {} {} tlspack/tgen:latest /bin/bash".format (zone_cname, rundir_map, srcdir_map)
        os.system (cmd_str)

        for netdev in host_info['net_dev_list']:
            cmd_str = "sudo ip link set dev {} up".format(netdev)
            os.system (cmd_str)
            cmd_str = "sudo docker network connect {} {}".format(host_info['net_macvlan_map'][netdev], zone_cname)
            os.system (cmd_str)



def stop_containers(host_info, c_args):
    for z_index in range(host_info['cores']):
        zone_cname = "tp-zone-{}".format (z_index+1)
        cmd_str = "sudo docker rm -f {}".format (zone_cname)
        os.system (cmd_str)


def restart_containers(host_info, c_args):
    stop_containers(host_info, c_args)
    start_containers(host_info, c_args)

if __name__ == '__main__':
    try:
        cmArgs = get_arguments ()
    except Exception as er:
        print er
        sys.exit(1)

    host_file = os.path.join (cmArgs.host_run_dir, 'sys/host')
    try:
        with open(host_file) as f:
            host_info = json.load(f)
    except Exception as er:
        print er
        sys.exit(1)

    if cmArgs.mode == 'start':
        start_containers(host_info, cmArgs)
    elif cmArgs.mode == 'stop':
        stop_containers(host_info, cmArgs)
    elif cmArgs.mode == 'restart':
        restart_containers(host_info, cmArgs)
