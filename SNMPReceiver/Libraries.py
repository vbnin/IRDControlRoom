#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Developeurs : VBNIN + CKAR - IPEchanges.
Ce fichier est une librairie requise par le script core.py
"""

import re
import csv
import logging
import threading
import subprocess
from logging.handlers import RotatingFileHandler
from pysnmp.hlapi import *
from pysnmp.carrier.asyncore.dgram import udp, unix
from pyasn1.codec.ber import decoder
from pysnmp.proto import api

# Activation du logger
handler = RotatingFileHandler('SNMPReceiver.log', maxBytes=10000000, backupCount=5)
handler.setFormatter(logging.Formatter('%(asctime)s : %(message)s'))
logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(message)s')
logger = logging.getLogger(__name__)
logger.addHandler(handler)

# Définition de la fonction PrintException
def PrintException(msg):
    print("*" * 40)
    print(msg)
    print("*" * 40)

# Définition de la fonction de remplissage du fichier CSV au démarrage
def Launcher(Data):
    DataCSV = []
    for i in range(1, 6):
        Position = "ird" + str(i)
        Model = "type" + str(i)
        SatName = "SAT-" + str(i)
        if Data[Model] == 'DR5000':
            DR5000state(Position, SatName, Data[Position], Data, DataCSV)
        elif Data[Model] == 'RX8200':
            RX8200state(Position, SatName, Data[Position], Data, DataCSV)
        elif Data[Model] == 'TT1260':
            TT1260state(Position, SatName, Data[Position], Data, DataCSV)
        else:
            NoSat(Position, SatName, Data[Position], Data[Model], DataCSV, Data)
    with open("fichier_status.csv", "w", newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerows(DataCSV)

# Fonction de récupération de l'état IRD
def IRDstate(Addr, Model, Data):
    DataCSV = []
    logger.info("Envoi d'une requete d'état sur le port 161.")
    for i in range(1, 36):
        Position = "ird" + str(i)
        SatName = "SAT-" + str(i)
        if Addr == Data[Position]:
            if Model == 'DR5000':
                DR5000state(Position, SatName, Addr, Data, DataCSV)
            elif Model == 'RX8200':
                RX8200state(Position, SatName, Addr, Data, DataCSV)
            elif Model == 'TT1260':
                TT1260state(Position, SatName, Addr, Data, DataCSV)
            else:
                return
            with open("fichier_status.csv") as f:
                reader = csv.reader(f, delimiter=';')
                lines = [l for l in reader]
                for item in lines:
                    try:
                        item.index(Position)
                        lines.remove(item)
                        lines.append(DataCSV[0])
                    except:
                        pass
            with open("fichier_status.csv", "w", newline='') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerows(lines)
        else:
            pass

# Définition de la commande 'SNMP Get'
def SNMPget(IPAddr, OID):
    try:
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                CommunityData('private', mpModel=0),
                UdpTransportTarget((IPAddr, 161), timeout=0.1),
                ContextData(),
                ObjectType(ObjectIdentity(OID))))
        if errorIndication or errorStatus:
            logger.error("No SNMP response before timeout")
            state = '0'
            return state
        else:
            for varBind in varBinds:
                state = (' = '.join([x.prettyPrint() for x in varBind]))
                m = re.search('(.*)\ =\ (.*)', state)
                state = m.group(2)
                return state
    except:
        logger.error("Impossible de récupérer les infos SNMP...")
        state = '0'
        return state

def DR5000state(Position, SatName, Addr, Data, DataCSV):
    Info = {'Position':Position,
            'Name':SatName,
            'Addr':Addr,
            'Model':"Ateme DR5000",
            'SvcName':SNMPget(Addr, Data['DR5000SvcName']),
            'Snr':int(SNMPget(Addr, Data['DR5000Snr']))/10,
            'Margin':int(SNMPget(Addr, Data['DR5000Margin']))/10,
           }
    d = []
    for key in Info:
        d.append(Info[key])
    logger.info(d)
    DataCSV.append(d)
    return DataCSV

def RX8200state(Position, SatName, Addr, Data, DataCSV):
    Info = {'Position':Position,
            'Name':SatName,
            'Addr':Addr,
            'Model':"Ericsson RX8200",
            'SvcName':SNMPget(Addr, Data['RX8200SvcName']),
            'Snr':SNMPget(Addr, Data['RX8200Snr'])[:4],
            'Margin':SNMPget(Addr, Data['RX8200Margin'])[2:6],
           }
    if Info['SvcName'][:7] == "No Such":
        Info['SvcName'] = ''
    d = []
    for key in Info:
        d.append(Info[key])
    logger.info(d)
    DataCSV.append(d)
    return DataCSV

def TT1260state(Position, SatName, Addr, Data, DataCSV):
    Info = {'Position':Position,
            'Name':SatName,
            'Addr':Addr,
            'Model':"Tandberg TT1260",
            'SvcName':SNMPget(Addr, Data['TT1260SvcName']),
            'Snr':int(SNMPget(Addr, Data['TT1260Snr']))/100,
            'Margin':int(SNMPget(Addr, Data['TT1260Margin']))/100,
           }
    if Info['Margin'] == 100.0:
        Info['Margin'] = 0.0
    d = []
    for key in Info:
        d.append(Info[key])
    logger.info(d)
    DataCSV.append(d)
    return DataCSV

def NoSat(Position, SatName, Addr, Model, DataCSV, Data):
    Info = {'Position':Position,
            'Name':SatName,
            'Addr':Addr,
            'Model':Model,
            'SvcName':'N/A',
            'Snr':'N/A',
            'Margin':'N/A',
           }
    d = []
    for key in Info:
        d.append(Info[key])
    logger.info(d)
    DataCSV.append(d)
    return DataCSV
