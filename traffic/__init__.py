__author__ = 'Shirish Pal'

def start (app_name, testbed, runid, **app_kwargs):
    from .TlsApp import TlsApp
    return TlsApp.start (__name__, app_name, testbed, runid, **app_kwargs)
  
def stop (runid):
    from .TlsApp import TlsApp
    TlsApp.stop_run (runid)

def stats_iter ():
    from .TlsApp import TlsApp
    return TlsApp.stats_iter (runid)