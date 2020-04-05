#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
UDP Serveri for aquiring data from the Bosch sensor BME280
Sensor is connected to Rapsi Pi via I2C Bus 1, Addr. 0x76.
Server opens an UDP socket on port 5023 (changeable) and waits for incoming JSON requests.

Valid requests:
{"command" : "getTemperature"}
{"command" : "getHumidity"}
{"command" : "getPressure"}

The answers are then:
{"answer":"getTemperature","value":"19.56 C"})
{"answer":"getHumidity","value":"32.15% rH"})
{"answer":"getPressure","value":"992.38 hPa"})
'''


import smbus2
import bme280
import socket
import time
import json
import syslog
import threading
from threading import Thread
import logging


bme280_address = 0x76
udp_port = 5023

logging.basicConfig(level=logging.INFO)




class bme280udp(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        logging.info("Starting serverthread as " + threading.currentThread().getName())
        self.t_stop = threading.Event()
        self.hostname = socket.gethostname()
        self.basehost = self.hostname 
        
        self.bus = smbus2.SMBus(1)
        self.calibration_params = bme280.load_calibration_params(self.bus, bme280_address)
        
        self.udpServer()

    def udpServer(self):
        logging.info("Starting BME280 UDP-Server at " + self.basehost + ":" + str(udp_port))
        self.udpSock = socket.socket( socket.AF_INET,  socket.SOCK_DGRAM )
        self.udpSock.bind( (self.basehost,udp_port) )

        #self.t_stop = threading.Event()
        udpT = threading.Thread(target=self._udpServer)
        udpT.setDaemon(True)
        udpT.start()

    def _udpServer(self):
        logging.info("Server laaft")
        while(not self.t_stop.is_set()):
            try:
                data, addr = self.udpSock.recvfrom( 1024 )# Puffer-Groesse ist 1024 Bytes.
                ret = self.parseCmd(data) # Abfrage der Fernbedienung (UDP-Server), der Rest passiert per Interrupt/Event
                self.udpSock.sendto(str(ret).encode('utf-8'), addr)
            except Exception as e:
                try:
                    self.udpSock.sendto(str('{"answer":"error"}').encode('utf-8'), addr)
                    logging.warning("Uiui, beim UDP senden/empfangen hat's kracht!" + str(e))
                except Exception as o:
                    logging.warning("Uiui, beim UDP senden/empfangen hat's richtig kracht!" + str(o))

    def timer_operation(self):
        logging.info("Starting Timeroperationthread as " + threading.currentThread().getName())
        while(not self.t_stop.is_set()):
            self.get_data()
            self.t_stop.wait(60)
            #print("tick")
        if self.t_stop.is_set():
            logging.info("Ausgetimed!")

    def parseCmd(self, data):
        data = data.decode()
        try:
            jcmd = json.loads(data)
        except:
            logging.warning("Das ist mal kein JSON, pff!")
            ret = json.dumps({"answer": "Kaa JSON Dings!"})
            return(ret)
        if(jcmd['command'] == "getTemperature"):
            ret = self.get_temperature()
        elif(jcmd['command'] == "getHumidity"):
            ret = self.get_humidity()
        elif(jcmd['command'] == "getPressure"):
            ret = self.get_pressure()
        else:
             ret = json.dumps({"answer":"Fehler","Wert":"Kein gültiges Kommando"})
        logging.debug(ret)
        return(ret)

    def get_sensor_data(self):
        data = bme280.sample(self.bus, bme280_address, self.calibration_params)
        return(data)

    def get_temperature(self):
        data = self.get_sensor_data()
        ret = json.dumps({"answer":"getTemperature","value":str(round(data.temperature,2))+" C"})
        return(ret)


    def get_humidity(self):
        data = self.get_sensor_data()
        return(json.dumps({"answer":"getHumidity","value":str(round(data.humidity,2))+"% rH"}))

    def get_pressure(self):
        data = self.get_sensor_data()
        return(json.dumps({"answer":"getPressure","value":str(round(data.pressure,2))+" hPa"}))

    def run(self):
        while True:
            try:
                time.sleep(1)
                pass
            except KeyboardInterrupt: # CTRL+C exiti
                self.stop()
                break



if __name__ == "__main__":
    Bme280udp = bme280udp()
    Bme280udp.start()
    #steuerung.run()
