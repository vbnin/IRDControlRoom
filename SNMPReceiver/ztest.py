#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Developeurs : VBNIN + CKAR - IPEchanges.
Script de relevé des niveaux de réceptions des IRD nodal
"""

import logging
import configparser
import sys
import csv
import os
import time
import re
from logging.handlers import RotatingFileHandler
from multiprocessing import Process, Queue
from pysnmp.hlapi import *
from pysnmp.carrier.asyncore.dgram import udp, unix
from pyasn1.codec.ber import decoder
from pysnmp.proto import api
from ztest2 import IRDInfo1




# # Activation du logger principal
# try:
#     LogPath = 'SNMPReceiver.log' if sys.platform.lower() == 'win32' else '/var/log/SNMPReceiver.log'
#     handler = RotatingFileHandler(LogPath, maxBytes=10000000, backupCount=5)
#     handler.setFormatter(logging.Formatter('%(asctime)s : %(message)s'))
#     logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(message)s')
#     logger = logging.getLogger(__name__)
#     logger.addHandler(handler)
#     logger.info("*" * 40)
# except:
#     print("Impossible d'initialiser le fichier de logs.")
#     exit()

def DictCreate(Data):
    # Lecture du fichier de Configuration et attribution des variables
    try:
        # Data = {}
        print("*" * 40)
        config = configparser.SafeConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'config.ini') if sys.platform.lower() == 'win32' else '/usr/local/bin/IRDControlRoom/SNMPReceiver/config.ini')
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
            Model = "model" + str(i)
            Data[Position] = config.get('IRD', 'IRD' + str(i))
            Data[Model] = config.get('IRD', 'IRD' + str(i) + 'Model')
        print("*" * 40)
        return Data
    except:
        print("Fichier de configuration 'config.ini' invalide ou introuvable.")
        exit()

# Fonction de lancement des Process et écriture du CSV
def InitCSV(Datas):
    while True:
        print("Launching InitCSV")
        # queue = Queue()
        plist = []
        DataCSV = []
        for i in range(1, 36):
            DataCSV.append(IRDInfo1(i, Datas))
        # plist = [Process(target=IRDInfo1, args=(i, Datas, queue)) for i in range(1, 36)]
        # for p in plist:
        #     p.start()
        # for p in plist:
        #     p.join()
        #     DataCSV.append(queue.get())
        print(DataCSV)
        with open(Datas['CSV'], "w", newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerows(DataCSV)
        print("Fichier CSV mis à jour par InitCSV.")

if __name__ == '__main__':
    try:
        Dict = {}
        DictCreate(Dict)
        print("Initialisation du script...")
        InitCSV(Dict)
    except:
        print("Fin du script.")
        raise
