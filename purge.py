__author__ = 'Shirish Pal'

import os
import sys
import argparse
import json

from run import purge_testbed

def get_arguments ():
    arg_parser = argparse.ArgumentParser(description = 'purge resource')

    arg_parser.add_argument('--node_rundir'
                                , action="store"
                                , default='/root/rundir'
                                , help = 'rundir path')

    arg_parser.add_argument('--testbed'
                                , action="store"
                                , required=True
                                , help = 'testbed')

    arg_parser.add_argument('--force'
                                , action="store_true"
                                , default=False
                                , help = '0/1')

    return arg_parser.parse_args()

if __name__ == '__main__':
    c_args = get_arguments ()

    purge_testbed (c_args.testbed
                    , c_args.node_rundir
                    , c_args.force)