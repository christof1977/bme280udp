#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys
import json
import select
import logging


#logging.basicConfig(level=logging.DEBUG)

udpTimeout = 4
ADDR = 'heizungeg'
PORT = 5023

def getcmds():
    valid_cmds = ['getTemperature',
                  'getHumidity',
                  'getPressure']

    return valid_cmds


def hilf():
    print('')
    print('*******************************')
    print('Test tool for BME280 UDP server')
    print('')
    print('Commands:')
    print('t  -> get Temperature')
    print('h  -> get Humidity')
    print('p  -> get Pressure')
    print('')
    print('?  -> This Text')
    print('q  -> Quit')


def getch():
    import sys, tty, termios
    fd = sys.stdin.fileno( )
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def tcpRemote(msg, **kwargs):
    # Todo
    pass


def udpRemote(msg, **kwargs):
    # Setzt einen JSON-String in Richtung Ampi per UDP ab
    # msg: JSON-String nach Ampi-Spec
    # udpSocket: wenn da ein Socket übergeben wird, wird halt der hergenommen
    # addr, port: Gibt's keinen Socket, wird einer mit addr, port aufgemacht
    # Wenn nix übergeben wird, gibt's halt einen Standard-Socket

    if('udpSocket' in kwargs):
        udpSocket = kwargs.get('udpSocket')
    else:
        if('addr' not in kwargs or 'port' not in kwargs):
            logging.info("Uiui, wohin soll ich mich nur verbinden? Naja, standard halt.")
            addr = ADDR
            port = PORT
        else:
            addr = kwargs.get('addr')
            port = kwargs.get('port')
        logging.info("Öffne Socket")
        try:
            udpSocket = socket.socket( socket.AF_INET,  socket.SOCK_DGRAM )
            udpSocket.setblocking(0)
        except Exception as e:
            logging.info(str(e))
    valid_cmds = getcmds()
    try:
        ret = -1
        logging.info("So laut des heit: %s", msg)
        ready = select.select([], [udpSocket], [], udpTimeout)
        if(ready[1]):
            udpSocket.sendto( msg.encode(), (addr,port) )
            logging.info("Gesendet")
        ready = select.select([udpSocket], [], [], udpTimeout)
        if(ready[0]):
            data, addr = udpSocket.recvfrom(1024)
            logging.info(data.decode())
            ret = data.decode()
            return(ret)
    except Exception as e:
        logging.info(str(e))
        return -1

def main():
    addr = 'heizung'
    port = 5005

    valid_cmds = getcmds()


    if len(sys.argv) == 1:
        hilf()
        while True:
            try:
                cmd = getch()
                valid = 1
                if cmd == "t":
                    json_string = '{"command" : "getTemperature"}\n'
                elif cmd == "h":
                    json_string = '{"command" : "getHumidity"}\n'
                elif cmd == "p":
                    json_string = '{"command" : "getPressure"}\n'
                elif cmd == "?":
                    hilf()
                elif cmd == "q":
                    logging.info("Bye")
                    break
                else:
                    logging.info("Invalid command")
                    valid = 0
                if valid:
                    ret = udpRemote(json_string, addr="heizungeg", port=5023)
                    if(ret!=-1):
                        try:
                            print(json.dumps(json.loads(ret),indent=4))
                        except Exception as e:
                            print("ups:", e)
            except KeyboardInterrupt:
                logging.info("Bye")
                break
    else:
        log = "Not a valid command"
        logging.info(log)
        syslog.syslog(log)
        return()



if __name__ == "__main__":
   main()



