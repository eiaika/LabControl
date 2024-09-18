# -*- coding: utf-8 -*-
"""
Created on Wed Sep 21 01:01:37 2022

@author: Anastasiia
"""
import sys
import paho.mqtt.client as mqttClient
import time
import json
from scipy.integrate import odeint
from simple_pid import PID
import numpy as np

# InstanceID Kp_pid Ki_pid Kd_pid setpoint_pid stateVar 
# v1 1.534 0.08 -0.35 20 7
try:
    InstanceID = sys.argv[1]
    Kp_pid = float(sys.argv[2])
    Ki_pid = float(sys.argv[3])
    Kd_pid = float(sys.argv[4])
    setpoint_pid = float(sys.argv[5])
    watertemp = float(sys.argv[6])
except:
    print ("Args error!")
    exit()



try:
    with open("instancesData/"+ InstanceID + "/initialData.json", "r") as read_file:
        initData = json.load(read_file)
        read_file.close()
except :
            print("Read instancesData file error!")
            sys.exit()
        
try:
    Kp_AP2 = initData["objData"]["Kp_AP2"]
    T1_AP2 = initData["objData"]["T1_AP2"]
    T2_AP2 = initData["objData"]["T2_AP2"]
    delayTime_AP2 = initData["objData"]["delayTime_AP2"]
    discTime_AP2 = initData["objData"]["discTime_AP2"]
    
    output_AP1 = initData["objData"]["output_AP1"]
    Kp_AP1 = initData["objData"]["Kp_AP1"]
    T_AP1 = initData["objData"]["T_AP1"]
    delayTime_AP1 = initData["objData"]["delayTime_AP1"]
    discTime_AP1  = initData["objData"]["discTime_AP1"]
    id_topic = initData["mqttTopic"] 
except :
    print("Read filed initial data error!")
    sys.exit()


start_time = time.time()
last_time = start_time
power = 1
ddt = 0.01

pid_auto_mode = True
pid = PID(Kp_pid, Ki_pid, Kd_pid, setpoint_pid)
pid.output_limits = (0, 100)
pid.auto_mode = pid_auto_mode
pv = 0
disturb_input = 0

def updatePID(strJSON):
        
    global Kp_pid
    global Ki_pid
    global Kd_pid
    global setpoint_pid
    global pid
    global pv
    global pid_auto_mode
    global disturb_input
    print (strJSON)
    try: 
        data = json.loads(strJSON)
        if "Kp" in data:
            Kp_pid = float(data["Kp"])
            pid.tunings=(float(data["Kp"]),Ki_pid,Kd_pid)            
        if "Ki" in data:
            Ki_pid = float(data["Ki"])
            pid.tunings=(Kp_pid,float(data["Ki"]),Kd_pid)
        if "Kd" in data:
            Kd_pid = float(data["Kd"])
            pid.tunings=(Kp_pid,Ki_pid,float(data["Kd"]))
        if "setpoint" in data:
            setpoint_pid = float(data["setpoint"])
            pid.setpoint =  float(data["setpoint"])
        if "pid_mode" in data:
            if data["pid_mode"] is True:
                pid_auto_mode = True
                pid.set_auto_mode(True, last_output=pv)
            if data["pid_mode"] is False:
                pid_auto_mode = False
                pid.set_auto_mode(False)
        if ("pv" in data) and (pid_auto_mode is False):
            pv = float(data["pv"])
        if "disturb" in data:
            disturb_input = float(data["disturb"])
    except:
        return

import mqttAddition as mqttClient

client = mqttClient.connect_mqtt_lite()
client.loop_start()
mqttClient.subscribeWithUpdate(client,updatePID,InstanceID)



class AP1:
    """
    Simple simulation of a water boiler which can heat up water
    and where the heat dissipates slowly over time
    """

    def __init__(self, output, Kp, T, delayTime, discTime):
        self.output = output
        self.Kp = Kp
        self.taup = T
        self.delayTime = delayTime
        self.discTime = discTime
        items = int(self.delayTime/self.discTime)-1
        self.delayStack = [0]*items


    def model3(self,y,t,u):
        return (-y + self.Kp * u)/self.taup

    def step (self,pv,dt):
        self.delayStack.append(pv)
        tspan = [0,dt]
        z = odeint(self.model3,self.output,tspan,(self.delayStack.pop(0),))
        self.output = z[1]
        
        return z[1]



class AP2:
    """
    Simple simulation of a water boiler which can heat up water
    and where the heat dissipates slowly over time
    """

    def __init__(self,output,Kp,T1,T2,delayTime,discTime):
        self.output = [output,0]
        self.Kp = Kp
        self.T1 = T1
        self.T2 = T2
        self.delayTime = delayTime
        self.discTime = discTime
        items = int(self.delayTime/self.discTime)-1
        self.delayStack = [0]*items


    def model3(self,x,t,u):
        tau1 = self.T1 * self.T2
        tau2 = self.T1 + self.T2
        y = x[0]
        dydt = x[1]
        dy2dt2 = (-tau2*dydt - y + self.Kp*u)/tau1

        return [dydt,dy2dt2]

    def step (self,pv,dt):
        self.delayStack.append(pv)
        tspan = [0,dt]
        z = odeint(self.model3,self.output,tspan,(self.delayStack.pop(0),))
        self.output = z[1,:]
        
        return z[1,0]





if __name__ == '__main__':

    plant = AP2(watertemp,Kp_AP2,T1_AP2,T2_AP2,delayTime_AP2,discTime_AP2)
    
    disturbance = AP1(output_AP1, Kp_AP1, T_AP1, delayTime_AP1, discTime_AP1)


    

    try:
        publish_time = 0
        while True:
            
            current_time = time.time()
            dt = current_time - last_time

            if pid_auto_mode is True:
                pv = pid(watertemp)
                if type(pv) is not float and type(pv) is not int:
                    try:
                        pv=float(pv.item())
                    except:
                        continue
    
    
            pantOut = plant.step(pv, dt)
            dist = disturbance.step(disturb_input,dt)
    
            watertemp = pantOut + dist
    
    
            last_time = current_time
            

            if (current_time - publish_time)>1:
                publish_time = current_time
                msg = json.dumps({"water": round(watertemp[0],2),
                         "PV": round(float(pv),2)
                         })
                mqttClient.publishID(client,msg,InstanceID)
    
            time.sleep(ddt)   
     
            
     
    except KeyboardInterrupt:
     
        client.disconnect()
        client.loop_stop()
