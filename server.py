#!/usr/bin/env/python

import json
import unicornhat as unicorn
import threading
from time import sleep
from datetime import datetime
from gpiozero import CPUTemperature

from flask import Flask, jsonify, make_response, request
from random import randint

blinkThread = None
globalRed = 0
globalGreen = 0
globalBlue = 0
globalLastCalled = None
globalLastCalledApi = None

# Set the unicorn hat.
unicorn.set_layout(unicorn.AUTO)
unicorn.brightness(0.4)

# Get width and height of the hardware.
width, height = unicorn.get_shape()

app = Flask(__name__)

def set_colour(r, g, b, brightness, speed):
    global current_colours, globalBlue, globalGreen, globalRed
    globalRed = r
    globalGreen = g
    globalBlue = b

    if brightness != '':
        unicorn.brightness(brightness)

    for y in range(height):
        for x in range(width):
            unicorn.set_pixel(x, y, r, g, b)
    unicorn.show()

    if speed != '':
        sleep(speed)
        unicorn.clear()
        current_thread = threading.currentThread()
        while getattr(current_thread, "do_run", True):
            for y in range(height):
                for x in range(width):
                    unicorn.set_pixel(x, y, r, g, b)
            unicorn.show()
            sleep(speed)
            unicorn.clear()
            unicorn.show()
            sleep(speed)

def switch_on():
    red = randint(10, 255)
    green = randint(10, 255)
    blue = randint(10, 255)
    blinkThread = threading.Thread(target=set_colour, args=(red, green, blue, '', ''))
    blinkThread.do_run = True
    blinkThread.start()

def switch_off():
    global blinkThread, globalRed, globalGreen, globalBlue
    globalRed = 0
    globalGreen = 0
    globalBlue = 0
    if blinkThread != None:
        blinkThread.do_run = False
    unicorn.clear()
    unicorn.off()

def setTimestamp():
    global globalLastCalled
    globalLastCalled = datetime.now()

# API initialisation.
@app.route('/api/on', methods=['GET'])
def api_on():
    global globalLastCalledApi
    globalLastCalledApi = '/api/on'
    switch_off()
    switch_on()
    setTimestamp()
    return jsonify({})

@app.route('/api/off', methods=['GET'])
def api_off():
    global current_colours, globalLastCalledApi
    globalLastCalledApi = '/api/off'
    current_colours = None
    switch_off()
    setTimestamp()
    return jsonify({})

@app.route('/api/switch', methods=['POST'])
def api_switch():
    global blinkThread, globalLastCalledApi
    globalLastCalledApi = '/api/switch'
    switch_off()
    content = request.json
    red = content.get('red', '')
    green = content.get('green', '')
    blue = content.get('blue', '')
    brightness = content.get('brightness', '')
    speed = content.get('speed', '')
    blinkThread = threading.Thread(target=set_colour, args=(red, green, blue, brightness, speed))
    blinkThread.do_run = True
    blinkThread.start()
    setTimestamp()
    return make_response(jsonify())

@app.route('/api/status', methods=['GET'])
def api_status():
    global globalRed, globalGreen, globalBlue, globalLastCalled, globalLastCalledApi
    cpu = CPUTemperature()
    return jsonify({'red': globalRed,
                    'green': globalGreen,
                    'blue': globalBlue,
                    'last_called': globalLastCalled,
                    'last_called_api': globalLastCalledApi,
                    'cpu_temperature': cpu.temperature})

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=False)
