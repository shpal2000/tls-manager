__author__ = 'Shirish Pal'

import os
import sys
import argparse
import json
import time

from pymongo import MongoClient

from config import DB_CSTRING, RESULT_DB_NAME
from config import LIVE_STATS_TABLE


def get_arguments ():
    arg_parser = argparse.ArgumentParser(description = 'stats')


    arg_parser.add_argument('--runid'
                                , action="store"
                                , required=True
                                , help = 'run id')

    return arg_parser.parse_args()

if __name__ == '__main__':
    c_args = get_arguments ()

    mongoClient = MongoClient (DB_CSTRING)
    db = mongoClient[RESULT_DB_NAME]
    stats_col = db[LIVE_STATS_TABLE]

    while True:

        stats = stats_col.find({'runid' : c_args.runid})[0]

        print '{}-{}-{} : {} : {} : {}'.format(stats['tick']
                    , stats['client_stats']['tcpConnInitSuccessRate']
                    , stats['client_stats']['tcpConnInitInUse']
                    , stats['client_stats']['tcpConnInit']
                    , stats['client_stats']['tcpAcceptSuccess']
                    , stats['client_stats']['tcpConnInitSuccess'])

        time.sleep(0.1)
