#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Developeurs : VBNIN + CKAR - IPEchanges.
Script de relevé des niveaux de réceptions des IRD nodal
"""
#Librairies externe à télécharger
from pysnmp.hlapi import *
from pysnmp.carrier.asyncore.dgram import udp, unix
from pyasn1.codec.ber import decoder
from pysnmp.proto import api
from pysnmp.entity.rfc3413.oneliner import cmdgen
# from easysnmp import Session

#Import des librairies internes
import sys
import csv
import re
import os
import socket
import logging
import time
from logging.handlers import RotatingFileHandler

import configparser

# Activation du logger
LogPath = 'SNMPReceiver.log' if sys.platform.lower() == 'win32' else '/var/log/SNMPReceiver.log'
handler = RotatingFileHandler(LogPath, maxBytes=10000000, backupCount=5)
handler.setFormatter(logging.Formatter('%(asctime)s : %(message)s'))
logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(message)s')
logger = logging.getLogger(__name__)
logger.addHandler(handler)


Data = {}
ConfigPath = os.path.join(os.path.dirname(__file__), r'config.ini')
logger.info("Lecture du fichier config dans {}".format(ConfigPath))
config = configparser.SafeConfigParser()
config.read(ConfigPath)
Data['CSV'] = config.get('GENERAL', 'CSVfile')
Data['WinCSV'] = config.get('GENERAL', 'WinCSVfile')
Data['SupportedModels'] = config.get('GENERAL', 'SupportedModels').split(', ')
Data['CheckedInfos'] = config.get('GENERAL', 'CheckedInfos').split(', ')
Data['IRDModel'] = config.get('GENERAL', 'OidIRDModel')
Data['MosaAddr'] = config.get('MOSAIQUE', 'IPAddress')
Data['MosaTCPPort'] = int(config.get('MOSAIQUE', 'PortTCP'))
Data['MosaBuffer'] = int(config.get('MOSAIQUE', 'BufferSize'))
Data['MosaRoom'] = config.get('MOSAIQUE', 'Room')
for item in Data['SupportedModels']:
    for Oid in Data['CheckedInfos']:
        ModelCheck = item + Oid
        # OidCheck = 'Oid' + Oid
        Data[ModelCheck] = config.get(item, 'Oid' + Oid)
for i in range(1, 36):
    Position = "ird" + str(i)
    Data[Position] = config.get('IRD', 'IRD' + str(i))
logger.info(Data)

s = "Check value='This is a RX8200 Receiver' test"
m = re.search(r'(value=)\'(.*)\'\ (.*)', s)
logger.info(m.group(1))
logger.info(m.group(2))
for Model in Data['SupportedModels']:
    logger.info(Model[:3])
    if re.search(Model[:3], s):
        Modele = Model
        logger.info(Modele)
    else:
        logger.error('None')



OID1 = '.1.3.6.1.4.1.27338.5.5.3.3.2.0'
OID2 = '.1.3.6.1.4.1.27338.5.5.3.3.3.0'
OID3 = '.1.3.6.1.4.1.27338.5.5.1.5.1.1.9.1'
OID4 = '.1.3.6.1.4.1.27338.5.5.3.3'

# Définition de la commande 'SNMP Get'
def SNMPget(IPAddr, SNMPv, OID1, OID2, OID3):
    try:
        snmp = []
        OIDs = [OID1, OID2, OID3]
        session = Session(hostname=IPAddr, community='private', version=SNMPv)
        for item in OIDs:
            m = re.search(r'(value=)\'(.*)\'\ (.*)', session.get(item))
            snmp.append(m.group(2))
        logger.info(snmp)
        return snmp
    except Exception:
        logger.error(Exception)
        snmp = ['Erreur : SNMP timeout', 0.0, 0.0]
        return snmp

def EasySNMP(OID1, OID2, OID3):
    # Create an SNMP session to be used for all our requests
    session = Session(hostname='10.75.216.226', community='private', version=2)
    print(session.get(OID1))
    print(session.get(OID2))
    print(session.get(OID3))

# # Test avec Librairie EasySNMP
# start = time.time()
# for i in range(0,10):
#     EasySNMP(OID1, OID2, OID3)
# stop = time.time()-start
# logger.info(stop)

# Test avec pysnmp en version Get
start = time.time()
for i in range(0,10):
    SNMPget('10.75.216.4', 2, OID1, OID2, OID3)
stop = time.time()-start
logger.info(stop)

# # Test avec pysnmp en version Bulk
# start = time.time()
# for i in range(0,10):
#     SNMPbulk(OID4)
# stop = time.time()-start
# logger.info(stop)


