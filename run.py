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

    while True:
        time.sleep(5)
        if not p.poll() == None:
            break

        try:
            stop_file = os.path.join (cmd_ctrl_dir, 'stop.txt')
            with open (stop_file) as f:
                p.kill()
                break
        except:
            pass

    for stop_cmd in stop_cmd_list:
        cmd_out = subprocess.check_output(stop_cmd, shell=True, close_fds=True)
        print (cmd_out)

    finish_file = os.path.join (cmd_ctrl_dir, 'finish.txt')
    with open (finish_file, 'w') as f:
        f.write('')
