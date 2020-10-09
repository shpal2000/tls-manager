__author__ = 'Shirish Pal'

import os
import sys
import argparse
import json

from run import stop_run

def get_arguments ():
    arg_parser = argparse.ArgumentParser(description = 'stop run')

    arg_parser.add_argument('--node_rundir'
                                , action="store"
                                , default='/root/rundir'
                                , help = 'rundir path')

    arg_parser.add_argument('--runid'
                                , action="store"
                                , required=True
                                , help = 'run id')

    arg_parser.add_argument('--force'
                                , action="store_true"
                                , default=False
                                , help = '0/1')

    return arg_parser.parse_args()

if __name__ == '__main__':
    c_args = get_arguments ()

    status, msg = stop_run (c_args.runid
                            , c_args.node_rundir
                            , 8081 #todo
                            , c_args.force)
    if status:
        print msg