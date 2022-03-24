from random import randint
from threading import Lock
from flask import Flask, render_template, session
from flask_socketio import SocketIO, emit
import requests
import os
#import pyserial

async_mode = None
template_dir = os.path.abspath('.')

app = Flask(__name__, template_folder=template_dir)

socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()



def background_thread():
    try:
        while True:
            socketio.sleep(0.2) #dat 0.2

            speed = 33
            battery = 54
            tailLight = 1
            headLight = 1
            leftHazard = 1
            rightHazard = 0

            socketio.emit('my_response',
                        {'data': {
                            "speed": speed,
                            "battery": battery,
                            "taillight": tailLight,
                            "headlight": headLight,
                            "lefthazard": leftHazard,
                            "righthazard": rightHazard
                        }})
    except KeyboardInterrupt:
        exit()
    except:
        pass

@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

@socketio.event
def connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)

if __name__ == '__main__':
    socketio.run(app)