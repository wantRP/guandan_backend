import asyncio
import threading
from flask import Flask, request, jsonify
import environment
import websockets
import subprocess
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
def start_asyncio_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

@app.route('/start_game', methods=['POST'])
def create_room():
    position=request.json.get('position')
    if(position==None):
        position=0
    if(type(position)!=int or position>=4):
        return jsonify({'error':'badrequest'}),400
    server = environment.Server(actOrder=position)
    loop = asyncio.new_event_loop()
    asyncio.run_coroutine_threadsafe(server.begin(), loop)
    thread = threading.Thread(target=start_asyncio_loop, args=(loop,), daemon=True)
    thread.start()
    for i in range(3):
        subprocess.Popen(["python", "clients/client1.py"])
    
    return jsonify({'message':'ok'}),200
@app.route('/hello')
def hello():
    return jsonify({'message':'hello'}),200
if __name__ == '__main__':
    app.run(host='0.0.0.0',port='23455',debug=True)