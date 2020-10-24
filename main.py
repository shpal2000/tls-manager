from fastapi import FastAPI, BackgroundTasks
from typing import Optional, List
from pydantic import BaseModel

import asyncio
import uvicorn
import json
import sys
import os
import pdb
import time

from traffic.TlsCpsRun import TlsCpsRun
from traffic.admin import get_stats, stop_run, get_stats

app = FastAPI()

class StartTlsCps(BaseModel):
    testbed: str
    runid: str
    cps: int
    cipher: str
    version: str
    server_cert: str
    server_key: str
    total_conn_count: int

class StopTls(BaseModel):
    runid: str
    force: int

class StatsTls(BaseModel):
    runid: str

@app.get('/node_info')
async def node_info():
    return {}

@app.get('/testbed')
async def testbed_info():
    return {}

@app.post('/testbed')
async def add_testbed():
    return {}

@app.patch('/testbed')
async def update_testbed():
    return {}

@app.delete('/testbed')
async def delete_testbed():
    return {}


@app.post('/start_tls_cps')
async def start_tls_cps(params : StartTlsCps):
    # pdb.set_trace()
    nextRun = TlsCpsRun (params.testbed)
    status = nextRun.start (params.runid
                    , params.cps
                    , params.cipher
                    , params.version
                    , params.server_cert
                    , params.server_key
                    , params.total_conn_count)
    return status


@app.post('/stop_tls')
async def stop_tls(params : StopParam):
    stop_run (params.runid)
    return {}

@app.post('/stats_tls')
async def stp_tls(params : StopParam):
    return get_stats (params.runid)


if __name__ == '__main__':
    node_ip = sys.argv[1]
    node_port = int(sys.argv[2])
    asyncio.run (uvicorn.run(app
                                , host=node_ip
                                , port=node_port
                                , loop='asyncio'
                                , debug=False))