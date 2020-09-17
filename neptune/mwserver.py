'''
Middleware server to make Jupyter API messages nicer to deal with in Neos.
When Neos gets better at parsing JSON, this may not be necessary, and should be removed for the real-time messages of nepcomm anyway, to reduce latency!
see nepcomm for placeholder
We can keep this for dealing with the less frequent Jupyter messages which are not dealing with real-time interactivity
things like execute_requests, error responses, stdout, opening notebooks, etc.
'''

import asyncio
import websockets
import requests
import nest_asyncio
nest_asyncio.apply()
import uuid, datetime
import json
import time

def send_execute_request(code,session_id=None):
    session_id = uuid.uuid1().hex if session_id is None else session_id
    msg_type = 'execute_request'
    id=uuid.uuid1().hex
    content = { 'code' : code, 'silent':False }
    hdr = { 'msg_id' : id,
        'username': 'username',
        'session': session_id,
        'data': datetime.datetime.now().isoformat(),
        'msg_type': msg_type,
        'version' : '5.0' }
    msg = { 'header': hdr, 'msg_id': id, 'parent_header': hdr,
        'metadata': {},
        'channel': 'shell',
        'content': content }
    return msg

def send_comm(data,comm_id,session_id):
    msg_type = 'comm_msg'
    id=uuid.uuid1().hex
    hdr = { 'msg_id' : id,
        'username': 'username',
        'session': session_id,
        'data': datetime.datetime.now().isoformat(),
        'msg_type': msg_type,
        'version' : '5.0' }
    content = {'comm_id': comm_id,
        'data': data }
    msg = { 'header': hdr, 'msg_id': id, 'parent_header': hdr,
        'metadata': {},
        'buffers':[],
        'channel':"shell",
        'content': content }
    return msg

def main(kernel,headers,comm_id):
    session_id=""
    neos_cell_msg_ids = {}
    async def loop1(neossocket,path):
        async with websockets.connect("ws://localhost:8888/api/kernels/"+kernel["id"]+"/channels",extra_headers=headers) as websocket:
            await websocket.send(json.dumps(send_execute_request(""))) # priming
            while 1:
                print("awaiting jupyter response")
                response = await websocket.recv()
                print(response)
                response = json.loads(response)
                session_id = response["header"]["session"]
                if response["msg_type"] == "comm_msg":
                    await neossocket.send(str(response["content"]["data"]))
                else:
                    try:
                        parent_msg_id = response["parent_header"]["msg_id"]
                        cellid = neos_cell_msg_ids[parent_msg_id]
                        if response["msg_type"] == "stream":
                            await neossocket.send("cell/"+cellid+"/"+response["content"]["text"])
                        if response["msg_type"] == "error":
                            await neossocket.send("cell/"+cellid+"/"+"<color=red>"+response["content"]["ename"]+": "+response["content"]["evalue"]+"</color>")
                        elif response["msg_type"] == "execute_result":
                            await neossocket.send("cell/"+cellid+"/"+response["content"]["data"]["text/plain"])
                            #TODO: treat execute_response differently too
                        elif response["msg_type"] == "status":
                            if response["content"]["execution_state"] == "idle":
                                if parent_msg_id in neos_cell_msg_ids:
                                    del neos_cell_msg_ids[parent_msg_id]
                    except:
                        pass

    async def loop2(neossocket,path):
        async with websockets.connect("ws://localhost:8888/api/kernels/"+kernel["id"]+"/channels",extra_headers=headers) as websocket:
            await websocket.send(json.dumps(send_execute_request(""))) # priming
            while 1:
                print("awaiting neos instruction")
                msg = await neossocket.recv()
                print(msg)
                i = msg.index("/")
                msg_type = msg[:i]
                msg_content = msg[i+1:]
                if msg_type == "updateVar": #update variable
                    await websocket.send(json.dumps(send_comm(msg_content,comm_id,session_id)))
                elif msg_type == "cell": #execute code
                    j = msg_content.index("/")
                    cellid = msg_content[:j]
                    code = msg_content[j+1:]
                    message = send_execute_request(code,session_id)
                    neos_cell_msg_ids[message["msg_id"]] = cellid
                    await websocket.send(json.dumps(message))
    async def func(neossocket,path):
        task1 = asyncio.create_task(loop1(neossocket,path))
        task2 = asyncio.create_task(loop2(neossocket,path))
        await task1
        await task2
    return func

def run_server(comm_id, base, notebook_path, auth_token, ws_port):
    headers = {'Authorization': auth_token}

    url = base + '/api/kernels'
    response = requests.get(url,headers=headers)
    kernels = json.loads(response.text)
    kernel = kernels[0]

    # loop = asyncio.get_event_loop()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    start_server = websockets.serve(main(kernel,headers, comm_id), "localhost", ws_port)
    loop.run_until_complete(start_server)
    loop.run_forever()
