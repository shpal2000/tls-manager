__author__ = 'Shirish Pal'

import os
import sys
import subprocess
import time
import re
import json
import traceback

if __name__ == '__main__':
    cmd_ctrl_dir = sys.argv[1]
    init_file = os.path.join (cmd_ctrl_dir, 'init.txt')
    stop_file = os.path.join (cmd_ctrl_dir, 'stop.txt')
    finish_file = os.path.join (cmd_ctrl_dir, 'finish.txt')
    try:        

        try:
            with open (init_file, 'w') as f:
                f.write(' '.join(sys.argv))
        except:
            pass

        start_cmd = sys.argv[2]
        stop_cmd_list = sys.argv[3:]

        start_cmd_args = re.sub(r'\s+', ' ', start_cmd).split()
        p = subprocess.Popen(start_cmd_args)

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
    except: 
        while True:
            time.sleep(1)
            if os.path.exists (finish_file):
                break
            try:
                with open (finish_file, 'w') as f:
                    traceback.print_exc(file=f)
            except:
                pass
    finally:
        while True:
            time.sleep(1)
            if os.path.exists (finish_file):
                break
            try:
                with open (finish_file, 'w') as f:
                    f.write('1')
            except:
                pass
