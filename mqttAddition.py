# -*- coding: utf-8 -*-
"""
Created on Sat Jan 28 18:39:28 2023

@author: Anastasiia
"""

# python 3.6

import random
from paho.mqtt import client as mqtt_client
import json
import ssl

# Opening JSON file
confFile = open('config.json')
  
# returns JSON object as 
# a dictionary
configDat = json.load(confFile)
  
# Iterating through the json
# list
broker = configDat["mqttConfig"]["host"]
port = configDat["mqttConfig"]["port"]
topic = configDat["pythonCode"]["pyResultsTopic"]
topicData = configDat["pythonCode"]["pyDataTopic"]
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 1000)}'
username = configDat["mqttConfig"]["username"]+client_id
password = configDat["mqttConfig"]["password"]
caFile = configDat["mqttConfig"]["caFile"]
certFile = configDat["mqttConfig"]["certFile"]
keyFile = configDat["mqttConfig"]["keyFile"]
sequre = configDat["mqttConfig"]["sequre"]
  
# Closing file
confFile.close()


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.tls_set(ca_certs=caFile, certfile=certFile, keyfile=keyFile,
                   cert_reqs=ssl.CERT_NONE)
    client.connect(broker, port)
    return client

def connect_mqtt_lite():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def publish(client,msg):
    # msg_count = 4
    # msg = f"messages: {msg_count}"
    result = client.publish(topic, msg)
    # result: [0, 1]
    status = result[0]
    if status != 0:
        print(f"Failed to send message to topic {topic}")
        
def publishID(client,msg,idPros):
    # msg_count = 4
    # msg = f"messages: {msg_count}"
    result = client.publish(topic+"/"+idPros, msg)
    # result: [0, 1]
    status = result[0]
    if status != 0:
        print(f"Failed to send message to topic {topic}")

        
def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

    client.subscribe(topicData)
    client.on_message = on_message

def subscribeWithUpdate(client: mqtt_client,updateFunc,idPros):
    def on_message(client, userdata, msg):
        #print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        updateFunc(msg.payload.decode())

    client.subscribe(topicData+"/"+idPros)
    client.on_message = on_message


# def run():
#     client = connect_mqtt()
#     client.loop_start()
#     subscribe(client)
#     publish(client,"1")


# if __name__ == '__main__':
#     run()
