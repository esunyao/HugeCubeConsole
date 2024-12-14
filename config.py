import time

import paho.mqtt.client as mqtt

# MQTT configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_KEEPALIVE_INTERVAL = 60
MQTT_TOPIC = "superCube/callback"

# MQTT authentication
MQTT_USERNAME = "admin"
MQTT_PASSWORD = "2008"

{"reset":false,"DEBUG":false,"HTTPDEBUG":false,"MQTTDEBUG":false,"ID":"673a2","Internet":{"ssid":"inhand","passwd":"33336666"},"http":{"port":80},"Websocket":{"ip":"","port":80},"Mqtt":{"ip":"192.168.2.10","port":1883,"callback_topic":"superCube/callback","username":"SuperCube","password":"123456","topic":"superCube/topic","autoReconnected":false},"serverMode":"Mqtt","light":[{"command":"Server_NeoPixel","pin":1,"r":0,"g":0,"b":255,"bright":12,"num":["0-24"]},{"command":"Server_NeoPixel","pin":2,"r":255,"g":255,"b":255,"bright":12,"num":["0-24"]},{"command":"Server_NeoPixel","pin":3,"r":255,"g":30,"b":0,"bright":12,"num":["0-24"]}],"light_presets":{}}
config = [{
    "command": "Server_NeoPixel",
    "pin": 3,
    "r": 0,
    "g": 255,
    "b": 0,
    "bright": 12,
    "num": ["0-24"],
},
    {
        "command": "Server_NeoPixel",
        "pin": 2,
        "r": 255,
        "g": 0,
        "b": 0,
        "bright": 12,
        "num": ["0-24"],
    },
    {
        "command": "Server_NeoPixel",
        "pin": 1,
        "r": 255,
        "g": 255,
        "b": 255,
        "bright": 12,
        "num": ["0-24"],
    },
    {
        "command": "config Attitude enable set false"
    },
    {
        "command": "config Mqtt autoReconnected set true"
    }]

for item in config:
    if item["command"] == "Server_NeoPixel":
        item["save"] = True
    print(str(item).replace("'", '"').replace("True", "true").replace("False", "false"))