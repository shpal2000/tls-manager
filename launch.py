__author__ = 'Shirish Pal'

import os
import sys
import argparse
import json
import time
from threading import Thread
from multiprocessing import Process
import pdb

def add_c_arguments (arg_parser):
    arg_parser.add_argument('--cfg_name'
                                , action="store"
                                , required=True
                                , help = 'cfg_name')

    arg_parser.add_argument('--host_run_dir'
                                , action="store"
                                , default='/root/rundir'
                                , help = 'host_run_dir')

    arg_parser.add_argument('--run_tag'
                                , action="store"
                                , default='latest'
                                , help = 'run_tag')


def get_arguments ():
    arg_parser = argparse.ArgumentParser(description = 'commands')

    subparsers = arg_parser.add_subparsers(dest='mode'
                                            ,help='start|stop')

    start_parser = subparsers.add_parser('start', help='start help')
    stop_parser = subparsers.add_parser('stop', help='stop help')

    # start arguments
    add_c_arguments (start_parser)


    arg_parser.add_argument('--target_run_dir'
                                , action="store"
                                , default='/rundir'
                                , help = 'target_run_dir')

    start_parser.add_argument('--is_debug'
                                , action="store"
                                , default=0
                                , type=int
                                , help = '0|1|2')

    start_parser.add_argument('--host_src_dir'
                                , action="store"
                                , default='/root/tcpdash'
                                , help = 'host_src_dir')

    start_parser.add_argument('--target_src_dir'
                                , action="store"
                                , default='/root/tcpdash'
                                , help = 'target_src_dir')
    # stop arguments
    add_c_arguments (stop_parser)

    return arg_parser.parse_args()


def zone_start_thread(host_info, c_args, zone, z_index):

    zone_cname = "tp-zone-{}".format (z_index+1)
    cmd_str = "sudo docker exec -d {} ip netns add {}".format(zone_cname, host_info['netns'])
    os.system (cmd_str)

    for netdev in host_info['net_iface_map'].values():
        cmd_str = "sudo docker exec -d {} ip link set dev {} netns {}".format(zone_cname,
                                                                netdev,
                                                                host_info['netns'])
        os.system (cmd_str)

    cmd_str = "sudo docker exec -d {} cp -f /rundir/bin/tlspack.exe /usr/local/bin".format(zone_cname)
    os.system (cmd_str)

    cmd_str = "sudo docker exec -d {} cp -f /rundir/bin/tlspack.py /usr/local/bin".format(zone_cname)
    os.system (cmd_str)


    cmd_ctrl_dir = os.path.join(c_args.target_run_dir, 'traffic', c_args.cfg_name, 'cmd_ctrl', zone['zone_label'])

    start_cmd_internal = '"ip netns exec {} tlspack.exe zone {} {} {} config_zone {}"'.format (host_info['netns']
                                                                                        , c_args.cfg_name
                                                                                        , c_args.run_tag
                                                                                        , z_index
                                                                                        , c_args.is_debug)
    stop_cmd_internal = ''
    for netdev in host_info['net_iface_map'].values():
        cmd = ' "ip netns exec {} ip link set {} netns 1"'.format (host_info['netns'], netdev)
        stop_cmd_internal += cmd

    cmd_str = 'sudo docker exec -d {} python3 /usr/local/bin/tlspack.py {} {} {}'.format (zone_cname,
                                                                        cmd_ctrl_dir,
                                                                        start_cmd_internal, 
                                                                        stop_cmd_internal)
    os.system (cmd_str)


def start_traffic(host_info, c_args):
    registry_dir = os.path.join(c_args.host_run_dir, 'registry', c_args.cfg_name)
    registry_file = os.path.join(registry_dir, 'tag.txt')

    # check if config runing
    if os.path.exists(registry_file):
        print '{} running'.format(c_args.cfg_name)
        sys.exit(1)

    # create registry entries
    cfg_dir = os.path.join(c_args.host_run_dir, 'traffic', c_args.cfg_name)
    cfg_file = os.path.join(cfg_dir, 'config.json')

    try:
        with open(cfg_file) as f:
            cfg_j = json.load(f)
    except:
        print 'invalid config file' 
        sys.exit(1)

    os.system ('mkdir -p {}'.format(registry_dir))

    with open(registry_file, 'w') as f:
        f.write(c_args.run_tag)

    for zone in cfg_j['zones']:
        if not zone['enable']:
            continue
        is_app_enable = False
        for app in zone['app_list']:
            if app['enable']:
                is_app_enable = True;
                break
        if not is_app_enable:
            continue
    
        zone_file = os.path.join(registry_dir, zone['zone_label'])  
        with open(zone_file, 'w') as f:
            f.write('0')
    
    master_file = os.path.join(registry_dir, 'master')
    with open(master_file, 'w') as f:
        f.write('0')  

    # create cmd_ctrl entries
    cmd_ctrl_dir = os.path.join(c_args.host_run_dir, 'traffic', c_args.cfg_name, 'cmd_ctrl')
    os.system ('rm -rf {}'.format(cmd_ctrl_dir))
    os.system ('mkdir -p {}'.format(cmd_ctrl_dir))
    for zone in cfg_j['zones']:
        if not zone['enable']:
            continue
        zone_dir = os.path.join (cmd_ctrl_dir, zone['zone_label'])
        os.system ('mkdir -p {}'.format(zone_dir))


    # create resullt entries
    result_dir = os.path.join(c_args.host_run_dir, 'traffic', c_args.cfg_name
                                                , 'results', c_args.run_tag)
    os.system ('rm -rf {}'.format(result_dir))
    os.system ('mkdir -p {}'.format(result_dir))

    for zone in cfg_j['zones']:
        if not zone['enable']:
            continue
        zone_dir = os.path.join (result_dir, zone['zone_label'])
        os.system ('mkdir -p {}'.format(zone_dir))

        for app in zone['app_list']:
            if not app['enable']:
                continue
            app_dir = os.path.join (zone_dir, app['app_label'])
            os.system ('mkdir -p {}'.format(app_dir))

            if app.get('srv_list'):
                for srv in app['srv_list']:
                    if not srv['enable']:
                        continue
                    srv_dir = os.path.join (app_dir, srv['srv_label'])
                    os.system ('mkdir -p {}'.format(srv_dir))

            if app.get('proxy_list'):
                for proxy in app['proxy_list']:
                    if not proxy['enable']:
                        continue
                    proxy_dir = os.path.join (app_dir, proxy['proxy_label'])
                    os.system ('mkdir -p {}'.format(proxy_dir))

            if app.get('cs_grp_list'):
                for cs_grp in app['cs_grp_list']:
                    if not cs_grp['enable']:
                        continue
                    cs_grp_dir = os.path.join (app_dir, cs_grp['cs_grp_label'])
                    os.system ('mkdir -p {}'.format(cs_grp_dir))

    # start zones
    for netdev in host_info['net_dev_list']:
        cmd_str = "sudo ip link set dev {} up".format(netdev)
        os.system (cmd_str)

    z_threads = []
    z_index = -1
    for zone in cfg_j['zones']:
        z_index += 1

        if not zone['enable']:
            continue

        thd = Thread(target=zone_start_thread, args=[host_info, c_args, zone, z_index])
        thd.daemon = True
        thd.start()
        z_threads.append(thd)

    for thd in z_threads:
        thd.join()


def stop_traffic(host_info, c_args):
    registry_dir = os.path.join(c_args.host_run_dir, 'registry', c_args.cfg_name)
    registry_file = os.path.join(registry_dir, 'tag.txt')

    # check if config runing
    if not os.path.exists(registry_file):
        print '{} not running'.format(c_args.cfg_name)
        sys.exit(1)    

    cfg_dir = os.path.join(c_args.host_run_dir, 'traffic', c_args.cfg_name)
    cfg_file = os.path.join(cfg_dir, 'config.json')

    try:
        with open(cfg_file) as f:
            cfg_j = json.load(f)
    except:
        print 'invalid config file' 
        sys.exit(1)
        
    zone_stop_status_list = []
    for zone in cfg_j['zones']:

        if not zone['enable']:
            continue

        zone_stop_status_list.append ([zone, False])
        cmd_ctrl_dir = os.path.join(c_args.host_run_dir, 'traffic', c_args.cfg_name, 'cmd_ctrl', zone['zone_label'])
        stop_file = os.path.join(cmd_ctrl_dir, 'stop.txt')
        with open(stop_file, 'w') as f:
            f.write('')

    # while True:
    #     all_zone_stopped = True
    #     for zone_info in zone_stop_status_list:
    #         zone = zone_info[0]
    #         zone_stop_status = zone_info[1]
    #         if not zone_stop_status:
    #             all_zone_stopped = False
    #             cmd_ctrl_dir = os.path.join(c_args.host_run_dir, 'traffic', c_args.cfg_name, 'cmd_ctrl', zone['zone_label'])
    #             finish_file = os.path.join(cmd_ctrl_dir, 'finish.txt')
    #             try:
    #                 with open(finish_file) as f:
    #                     zone_info[1] = True
    #             except:
    #                 pass
    #     if all_zone_stopped:
    #         break

    time.sleep (10)
    os.system ("rm -rf {}".format (registry_dir))





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
        start_traffic(host_info, cmArgs)
    elif cmArgs.mode == 'stop':
        stop_traffic(host_info, cmArgs)
    else:
        print 'unknown mode'
        sys.exit(1)