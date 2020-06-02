from threading import Lock
from flask import Flask, render_template, session, request, jsonify, url_for
from flask_socketio import SocketIO, emit, disconnect    
import time
import math
import random
import Adafruit_DHT as dht
import RPi.GPIO as GPIO
localtime = time.asctime( time.localtime(time.time()) )
GPIO.setmode(GPIO.BOARD)

Tmer = 4

async_mode = None

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock() 

def background_thread(args):
        count = 0             
        while True:
                h, t = dht.read_retry(dht.DHT11, Tmer)
                print 'Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(t, h)
                file2 = open("log_teplota.txt","a")
                file2.write(localtime +' Temp={0:0.1f} *C  Humidity={1:0.1f}%'.format(t, h)+'\n')
                file2.close()
                file3 = open("last_teplota.txt","w")
                file3.write(localtime +' Temp={0:0.1f} *C  Humidity={1:0.1f}%'.format(t, h))
                file3.close()
                if args:
                        A = dict(args).get('A')
                else:
                        A = 1
                cas = time.time()
                data = t
                dataHum = h
                socketio.sleep(0.5)
                count += 1
                socketio.emit('my_response', {'data': data,'dataHum':dataHum, 'count': count, 'time':cas}, namespace='/test')
       
@socketio.on('my_event', namespace='/test')
def test_message(message):   
    session['receive_count'] = session.get('receive_count', 0) + 1 
    session['A'] = message['value']    
    emit('my_response', {'data': message['value'], 'count': session['receive_count'], 'ampl':1})

@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread, args=session._get_current_object())
    emit('my_response', {'data': 'Connected', 'count': 0})

@app.route('/')
def index():
    return render_template('tabs.html', async_mode=socketio.async_mode)

@socketio.on('disconnect_request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=8080, debug=True)
