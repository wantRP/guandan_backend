import asyncio
import threading
import time
from flask import Flask, request, jsonify
import environment
import websockets
import subprocess
from flask_cors import CORS
hasDqnBackend=False
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
def start_asyncio_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

@app.route('/start_game', methods=['POST'])
def create_room():
    global hasDqnBackend
    
    position=request.json.get('position')
    if(position==None):
        position=0
    if(type(position)!=int or position>=4):
        return jsonify({'error':'badrequest'}),400
    server = environment.Server(actOrder=position)
    server.resetStatus()
    print("========",server.player_num)
    subprocess.Popen('ps aux|grep "clients/dqn/client"| grep -v grep|cut -c 9-16|xargs kill -9 > /dev/null 2>&1',shell=True)
    time.sleep(0.8)
    subprocess.Popen(["/home/zhaotianchang/miniconda3/envs/tf1/bin/python", "/home/zhaotianchang/code/guandan_backend/clients/dqn/client1.py"])
    subprocess.Popen(["/home/zhaotianchang/miniconda3/envs/tf1/bin/python", "/home/zhaotianchang/code/guandan_backend/clients/dqn/client2.py"])
    subprocess.Popen(["/home/zhaotianchang/miniconda3/envs/tf1/bin/python", "/home/zhaotianchang/code/guandan_backend/clients/dqn/client3.py"])
    
    loop = asyncio.new_event_loop()
    asyncio.run_coroutine_threadsafe(server.begin(), loop)
    thread = threading.Thread(target=start_asyncio_loop, args=(loop,), daemon=True)
    thread.start()
    subprocess.Popen(["python", "clients/client1.py"])
    #for i in range(3):
    #    subprocess.Popen(["python", "clients/client1.py"])
    
    if hasDqnBackend==False:
        subprocess.Popen(["/home/zhaotianchang/miniconda3/envs/tf1/bin/python", "/home/zhaotianchang/code/guandan_backend/clients/dqn/dqn_backend.py"])
        hasDqnBackend=True
    return jsonify({'message':'ok'}),200
@app.route('/hello')
def hello():
    return jsonify({'message':'hello'}),200
def foo():
    hasDqnBackend
if __name__ == '__main__':
    subprocess.Popen('ps aux|grep "clients/dqn/"| grep -v grep|cut -c 9-16|xargs kill -9 > /dev/null 2>&1',shell=True)
    app.run(host='0.0.0.0',port='23455',debug=True)