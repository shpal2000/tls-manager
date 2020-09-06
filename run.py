__author__ = 'Shirish Pal'

import os
import sys
import subprocess
import time
import re
import json

if __name__ == '__main__':

    cmd_ctrl_dir = sys.argv[1]

    start_cmd = sys.argv[2]
    start_cmd_args = re.sub(r'\s+', ' ', start_cmd).split()

    stop_cmd_list = sys.argv[3:]

    p = subprocess.Popen(start_cmd_args)

    started_file = os.path.join (cmd_ctrl_dir, 'started.txt')
    while True:
        time.sleep(1)
        if os.path.exists (started_file):
            break
        try:
            with open (started_file, 'w') as f:
                f.write('1')
        except:
            pass

    stop_file = os.path.join (cmd_ctrl_dir, 'stop.txt')
    while True:
        time.sleep(5)
        if not p.poll() == None:
            break

        if os.path.exists (stop_file):
            p.kill()
            while p.poll() == None:
                time.sleep(1)
            break

    for stop_cmd in stop_cmd_list:
        cmd_out = subprocess.check_output(stop_cmd, shell=True, close_fds=True)
        print (cmd_out)

    finish_file = os.path.join (cmd_ctrl_dir, 'finish.txt')
    while True:
        time.sleep(1)
        if os.path.exists (finish_file):
            break
        try:
            with open (finish_file, 'w') as f:
                f.write('1')
        except:
            pass
