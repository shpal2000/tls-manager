__author__ = 'Shirish Pal'

from .TlsCpsRun import TlsCpsRun

from .run import get_run_testbed, unregister_run, is_running, run_stats_iter

def force_testbed_free(testbed):
    test = TlsCpsRun (testbed)
    test.stop(force=True)

def force_run_stop(runid):
    if not is_running (runid):
        return
    try:
        testbed = get_run_testbed (runid)
        force_testbed_free (testbed)
    except:
        unregister_run (runid)

def stats_run_invalid():
    while False:
        yield {}

def get_stats (runid):
    if not is_running (runid):
        return stats_run_invalid ()
    return run_stats_iter (runid)
