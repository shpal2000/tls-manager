__author__ = 'Shirish Pal'

import os
import sys
import argparse
import json

from run import show_stats

def get_arguments ():
    arg_parser = argparse.ArgumentParser(description = 'stats')

    arg_parser.add_argument('--node_rundir'
                                , action="store"
                                , default='/root/rundir'
                                , help = 'rundir path')

    arg_parser.add_argument('--runid'
                                , action="store"
                                , required=True
                                , help = 'run id')

    return arg_parser.parse_args()

if __name__ == '__main__':
    c_args = get_arguments ()

    show_stats (c_args.runid
                , c_args.node_rundir)