from fastapi import FastAPI, Depends, WebSocket, BackgroundTasks

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from typing import Optional, List
from pydantic import BaseModel

from functools import lru_cache
import asyncio

import pdb
import time

import sqlite3
from . import crud
from . import config

from fastapi.responses import ORJSONResponse
from fastapi.responses import HTMLResponse


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@lru_cache
def get_settings():
    settings = config.Settings()
    crud.create_tables (settings.db_file)
    return settings

@app.on_event("startup")
def startup():
    print ("startup")


@app.on_event("shutdown")
def shutdown():
    print ("shutdown")

class StartCpsReq(BaseModel):
    runid: str
    cipher: str
    cps: int

class StopReq(BaseModel):
    runid: str

class RunInfo(BaseModel):
    id : str

class ShowRunsRes(BaseModel):
    runs: List [RunInfo]


@app.get('/', response_class=HTMLResponse)
def root(settings: config.Settings = Depends (get_settings)):
    response = '''
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:5000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
     '''
    return HTMLResponse(content=response, status_code=200)

@app.post('/start_cps', response_class=ORJSONResponse)
async def start_cps(params : StartCpsReq
                    , settings: config.Settings = Depends (get_settings)):

    crud.add_task(settings.db_file, params.runid, 'cps-run')
    return params

@app.post('/stop', response_class=ORJSONResponse)
async def stop(params : StopReq
                , settings: config.Settings = Depends (get_settings)):

    crud.del_task(settings.db_file, params.runid)
    return params

@app.get('/show_runs', response_class=ORJSONResponse, response_model=ShowRunsRes)
async def show_runs(settings: config.Settings = Depends (get_settings)):
    return {"runs" : crud.get_tasks(settings.db_file)}

# def write_notification():
#     print ('here')

# @app.get("/test")
# async def test(background_tasks: BackgroundTasks):
#     background_tasks.add_task(write_notification)
#     return {"message": "Notification sent in the background"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        await asyncio.sleep(0.1)
        await websocket.send_text(f"hi there")
