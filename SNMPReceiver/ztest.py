#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Developeurs : VBNIN + CKAR - IPEchanges.
Ce fichier est une librairie requise par le script core.py
"""

import re
import csv
import sys
import logging
import os
import configparser
from time import sleep
from random import randint
from logging.handlers import RotatingFileHandler
from pysnmp.hlapi import *
from pysnmp.carrier.asyncore.dgram import udp, unix
from pyasn1.codec.ber import decoder
from pysnmp.proto import api
from multiprocessing import Process, Queue

# Lecture du fichier de Configuration et attribution des variables

Data = {}
config = configparser.SafeConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'config.ini') if sys.platform.lower() == 'win32' else '/usr/local/bin/IRDControlRoom/SNMPReceiver/config.ini')
Data["Locked"] = []
Data['CSV'] = config.get('GENERAL', 'CSVfile')
Data['DR5000Snr'] = config.get('DR5000', 'OidSnr')
Data['DR5000Margin'] = config.get('DR5000', 'OidMargin')
Data['DR5000SvcName'] = config.get('DR5000', 'OidServiceName')
Data['RX8200Snr'] = config.get('RX8200', 'OidSnr')
Data['RX8200Margin'] = config.get('RX8200', 'OidMargin')
Data['RX8200SvcName'] = config.get('RX8200', 'OidServiceName')
Data['TT1260Snr'] = config.get('TT1260', 'OidSnr')
Data['TT1260Margin'] = config.get('TT1260', 'OidMargin')
Data['TT1260SvcName'] = config.get('TT1260', 'OidServiceName')
for i in range(1, 36):
    Position = "ird" + str(i)
    Model = "type" + str(i)
    Data[Position] = config.get('IRD', 'IRD' + str(i))
    Data[Model] = config.get('IRD', 'IRD' + str(i) + 'Model')


# Define an output queue
output = Queue()

# define a example function
def IRD(i, Data, output):
    try:
        Position = "ird" + str(i)
        Info = [Data[Position], 'DR5000', 'Locked']
        output.put(Info)
    except:
        print('Error')
        return

if __name__ == '__main__':
    # Setup a list of processes that we want to run  
    processes = [Process(target=IRD, args=(i, Data, output)) for i in range(1, 36)]

    # Run processes
    for p in processes:
        p.start()
    # Exit the completed processes
    for p in processes:
        p.join()
    # Get process results from the output queue
    results = [output.get() for p in processes]

    print(results)
