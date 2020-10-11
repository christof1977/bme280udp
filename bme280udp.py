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
udp_port = 6664

logging.basicConfig(level=logging.INFO)


class bme280udp(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        logging.info("Starting serverthread as " + threading.currentThread().getName())
        self.t_stop = threading.Event()
        self.hostname = socket.gethostname()
        self.basehost = self.hostname + '.local'
        
        self.bus = smbus2.SMBus(1)
        self.calibration_params = bme280.load_calibration_params(self.bus, bme280_address)
        
        self.udpServer()

    def udpServer(self):
        self.udpSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.udpSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.udpSock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udpSock.settimeout(0.1)

        udpT = threading.Thread(target=self._udpServer)
        udpT.setDaemon(True)
        udpT.start()

    def _udpServer(self):
        logging.info("Server laaft")
        store = 1
        message = {"measurement":{"tempFlur":{"Name":"Temperatur Flur","Floor":"EG","Value":0,"Type":"Temperature","Unit":"°C","Timestamp":"","Store":store},
                                  "pressFlur":{"Name":"Luftdruck Flur","Floor":"EG","Value":0,"Type":"Pressure","Unit":"mbar","Timestamp":"","Store":store},
                                  "humFlur":{"Name":"Luftfeuchte Flur","Floor":"EG","Value":0,"Type":"Humidity","Unit":"% rH","Timestamp":"","Store":store}
                                  }}
        while(not self.t_stop.is_set()):
            message["measurement"]["tempFlur"]["Value"] = self.get_temperature()
            message["measurement"]["tempFlur"]["Timestamp"] = time.strftime('%Y-%m-%d %H:%M:%S')
            message["measurement"]["pressFlur"]["Value"] = self.get_pressure()
            message["measurement"]["pressFlur"]["Timestamp"] = time.strftime('%Y-%m-%d %H:%M:%S')
            message["measurement"]["humFlur"]["Value"] = self.get_humidity()
            message["measurement"]["humFlur"]["Timestamp"] = time.strftime('%Y-%m-%d %H:%M:%S')
            logging.debug(message)

            self.udpSock.sendto(json.dumps(message).encode(), ("<broadcast>", udp_port))

            self.t_stop.wait(20)

    def get_sensor_data(self):
        data = bme280.sample(self.bus, bme280_address, self.calibration_params)
        return(data)

    def get_temperature(self):
        data = self.get_sensor_data()
        return(round(data.temperature,2))

    def get_humidity(self):
        data = self.get_sensor_data()
        return(round(data.humidity,2))

    def get_pressure(self):
        data = self.get_sensor_data()
        return(round(data.pressure,2))

    def get_temperature_str(self):
        data = self.get_sensor_data()
        ret = json.dumps({"answer":"getTemperature","value":str(round(data.temperature,2))+" C"})
        return(ret)

    def get_humidity_str(self):
        data = self.get_sensor_data()
        return(json.dumps({"answer":"getHumidity","value":str(round(data.humidity,2))+"% rH"}))

    def get_pressure_str(self):
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
