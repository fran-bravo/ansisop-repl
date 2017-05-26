import os, re
import socket
from ctypes import *


class t_socketHeader(Structure):
    _pack_ = 1
    _fields_ = [("tipoEstructura", c_uint8),
                ("length", c_uint16)]

HEADER_TYPE = 3

class Connection(object):

    def __init__(self, conf_file):
        self.conf = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.get_conf_data(conf_file)

    def get_conf_data(self, conf_file):
        file = open(conf_file, 'r')
        for line in file:
            key, value = line.split("=")
            if "port" in key:
                value = int(value)
            self.conf[key] = value

    def connect(self):
        try:
            self.socket.bind(("localhost", self.conf['self_port']))
            self.socket.connect((self.conf['cpu_ip'], self.conf['cpu_port']))
        except ConnectionRefusedError:
            print("No se puede conectar con el servidor")

    def send(self, data):
        try:
            header = t_socketHeader(HEADER_TYPE, len(data.encode()))
            self.socket.send(header)
            self.socket.send(data.encode())
        except BrokenPipeError:
            print("No se pueden enviar datos porque no hay una conexion")
