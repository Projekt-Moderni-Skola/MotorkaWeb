from random import randint
from threading import Lock
from flask import Flask, render_template
from flask_socketio import SocketIO
import requests
import os
import datetime
import hashlib
import serial
import math

async_mode = None
template_dir = os.path.abspath('.')

app = Flask(__name__, template_folder=template_dir)

socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

def filterGPS(text):
    lat, lot= text[2], text[4]
    latstart, latend= float(lat[:2]), float(lat[2:])
    degrees, minutes = latstart, latend
    tmp = lat[:4]
    tmp = tmp[2:]
    seconds = round(latend - float(tmp),5)
    ddlat = degrees + (minutes/60.0) + (seconds/3600.0)
    lotstart = float(lot[:3])
    lotend = float(lot[3:])
    degrees = lotstart
    minutes = lotend
    tmp = lot[:5]
    tmp = tmp[3:]
    seconds = round(latend - float(tmp),5)
    ddlot = degrees + (minutes/60.0) + (seconds/3600.0)
    
    final = "{0}N,{1}E".format(ddlat,ddlot)
    return final

def dataGPS(gps):
    while 1:
        if gps.in_waiting > 0:
            serialString = gps.readline()
            try:
                string = serialString.decode("Ascii")
                if string.startswith("$GNGGA"):
                    strings = string.split(",")
                    location = filterGPS(strings)
                    return location
                else:
                    pass
            except:
                pass

def dataController(controller):
        while 1:
            try:
                # Send bytes to get raw data
                controller.write(b"\x3B")
                controller.write(b"\x00")
                controller.write(b"\x3B")

                # Format data from hex and weird arrays
                formattedString = str(controller.readline()).split("'")
                formattedData = formattedString[1].split("\\x")
                decimalSpeedFromHex = int(formattedData[5], 16)

                # More formatting and clearing
                overturn = int(formattedData[4][:2], 16)

                # From raw to real data
                rpm = overturn * 256 + decimalSpeedFromHex + 1
                kmh = math.floor((((rpm))*2.2) *0.06)

                # TODO Define battery and get data for it b"\x3A\x00\x3A"
                return kmh
            except:
                pass

def postLocation(location, km, percentage):
    now = datetime.datetime.now()
    now = now.strftime("%Y-%m-%d %H:%M:%S")

    gps =  str(location)
    mileage = str(km)
    battery = str(percentage)
    string = "{0}|ZIDAN|{1}|{2}|{3}|Ad0oNkQWJi7LJBsQoCqV".format(now, mileage, battery, gps)

    string = str.encode(string)

    hash_object = hashlib.sha1(string)
    pbHash = hash_object.hexdigest()
    print(string)
    print(pbHash)

    r = requests.post("https://e-zidane.cz/api/add-log", json={
        "dttm": now,
        "vehicle_code": "ZIDAN",
        "mileage": mileage,
        "battery_capacity": battery,
        "gps": gps,
        "signature": pbHash
    })

    return r.json()

def background_thread():
    controller = serial.Serial(
    #/dev/ttyUSB0
        port="COM7", baudrate=19200, bytesize=8, timeout=1, stopbits=serial.STOPBITS_ONE
    )
    gps = serial.Serial(
    #/dev/ttyUSB0
        port="COM9", baudrate=9600, bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE
    )
    timer = 0
    try:

        while True:
            speed, battery = dataController(controller)
            gps = dataGPS(gps)

            socketio.sleep(0.2)
            if timer != 1500:
                timer += 1
            else:
                timer = 0
                postLocation(gps)

            socketio.emit('my_response',
                          {'data': {
                              "speed": speed,
                              "battery": battery,
                              "taillight": 0,
                              "headlight": 0,
                              "lefthazard": 0,
                              "righthazard": 0
                          }})
    except KeyboardInterrupt:
        exit()


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