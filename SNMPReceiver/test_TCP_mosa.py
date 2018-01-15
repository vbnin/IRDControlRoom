#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Developeurs : VBNIN + CKAR - IPEchanges.
Script de relevé des niveaux de réceptions des IRD nodal
"""

import socket

# Prepare 3-byte control message for transmission
TCP_IP = '10.0.3.70'
TCP_PORT = 13000
BUFFER_SIZE = 1024
OpenCmd = "<openID>Régie</openID>\n".encode()
SendCmd = "<getKRoom/>\n".encode()
CloseCmd = "<closeID/>\n".encode()

 
# Open socket, send message, close socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
s.send(OpenCmd)
data = s.recv(BUFFER_SIZE)
print(data.decode())
s.send(SendCmd)
data = s.recv(BUFFER_SIZE)
print(data.decode())
s.send(CloseCmd)
data = s.recv(BUFFER_SIZE)
print(data.decode())
s.close()

