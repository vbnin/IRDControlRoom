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
from time import sleep
from random import randint
from logging.handlers import RotatingFileHandler
from pysnmp.hlapi import *
from pysnmp.carrier.asyncore.dgram import udp, unix
from pyasn1.codec.ber import decoder
from pysnmp.proto import api
from multiprocessing import Process, Queue

# Activation du logger
LogPath = 'SNMPReceiver.log' if sys.platform.lower() == 'win32' else '/var/log/SNMPReceiver.log'
handler = RotatingFileHandler(LogPath, maxBytes=10000000, backupCount=5)
handler.setFormatter(logging.Formatter('%(asctime)s : %(message)s'))
logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(message)s')
logger = logging.getLogger(__name__)
logger.addHandler(handler)

# Définition de la fonction PrintException
def PrintException(msg):
    print("*" * 40)
    print(msg)
    print("*" * 40)

# Fonction de collection des informations par SNMP
def IRDInfo1(i, Data, queue):
    Position = "ird" + str(i)
    Model = "type" + str(i)
    SatName = "SAT-" + str(i)
    logger.info("1 - Collecte des Infos pour " + SatName)
    Info = [Position, SatName, Data[Position], Data[Model]]
    if Data[Model] == "DR5000":
        Snmp = SNMPget(Data[Position], Data['DR5000SvcName'], Data['DR5000Snr'], Data['DR5000Margin'])
        Info = Info + Snmp
        Info[5] = int(Info[5])/10
        Info[6] = int(Info[6])/10
    elif Data[Model] == "RX8200":
        Snmp = SNMPget(Data[Position], Data['RX8200SvcName'], Data['RX8200Snr'], Data['RX8200Margin'])
        Info = Info + Snmp
        if Info[4][:7] == "No Such":
            Info[4:6] = ['', 0, 0]
            Info.remove(Info[7])
        else:
            try:
                Info[5:6] = [Info[5][:4], Info[6][2:6]]
                # Info[6] = Info[6][2:6]
            except:
                Info[5:6] = [0, 0]
                Info.remove(Info[7])
    elif Data[Model] == "TT1260":
        Snmp = SNMPget(Data[Position], Data['TT1260SvcName'], Data['TT1260Snr'], Data['TT1260Margin'])
        Info = Info + Snmp
        Info[5] = int(Info[5])/100
        Info[6] = int(Info[6])/100
        if Info[6] == 100.0:
            Info[6] = 0.0
    else:
        Info = Info + ['N/A', 'N/A', 0]
    logger.info("2 - Ajout du statut Locked")
    if float(Info[6]) > 0.1:
        Info.append("Locked")
    else:
        Info.append("Unlocked")
    queue.put(Info)
    return Info
    
def IRDInfo2(item, Data, queue):
    logger.info("1 - Collecte des Infos")
    Model = item[3]
    Addr = item[2]
    Info = [item[0], item[1], item[2], item[3]]
    if Model == "DR5000":
        Snmp = SNMPget(Addr, Data['DR5000SvcName'], Data['DR5000Snr'], Data['DR5000Margin'])
        Info = Info + Snmp
        Info[5] = int(Info[5])/10
        Info[6] = int(Info[6])/10
    elif Model == "RX8200":
        Snmp = SNMPget(Addr, Data['RX8200SvcName'], Data['RX8200Snr'], Data['RX8200Margin'])
        Info = Info + Snmp
        if Info[4][:7] == "No Such":
            Info[4:6] = ['', 0, 0]
            Info.remove(Info[7])
        else:
            try:
                Info[5:6] = [Info[5][:4], Info[6][2:6]]
                # Info[6] = Info[6][2:6]
            except:
                Info[5:6] = [0, 0]
                Info.remove(Info[7])
    elif Model == "TT1260":
        Snmp = SNMPget(Addr, Data['TT1260SvcName'], Data['TT1260Snr'], Data['TT1260Margin'])
        Info = Info + Snmp
        Info[5] = int(Info[5])/100
        Info[6] = int(Info[6])/100
        if Info[6] == 100.0:
            Info[6] = 0.0
    else:
        Info = Info + ['N/A', 'N/A', 0]
    logger.info("2 - Ajout du statut Locked")
    if float(Info[6]) > 0.1:
        Info.append("Locked")
    else:
        Info.append("Unlocked")
    queue.put(Info)
    return Info
    

def IRDInfo3(i, Data):
    Position = "ird" + str(i)
    Model = "type" + str(i)
    SatName = "SAT-" + str(i)
    logger.info("1 - Collecte des Infos")
    Info = [Position, SatName, Data[Position], Data[Model]]
    if Data[Model] == "DR5000":
        Snmp = SNMPget(Data[Position], Data['DR5000SvcName'], Data['DR5000Snr'], Data['DR5000Margin'])
        Info = Info + Snmp
        Info[5] = int(Info[5])/10
        Info[6] = int(Info[6])/10
    elif Data[Model] == "RX8200":
        Snmp = SNMPget(Data[Position], Data['RX8200SvcName'], Data['RX8200Snr'], Data['RX8200Margin'])
        Info = Info + Snmp
        if Info[4][:7] == "No Such":
            Info[4:6] = ['', 0, 0]
            Info.remove(Info[7])
        else:
            try:
                Info[5:6] = [Info[5][:4], Info[6][2:6]]
                # Info[6] = Info[6][2:6]
            except:
                Info[5:6] = [0, 0]
    elif Data[Model] == "TT1260":
        Snmp = SNMPget(Data[Position], Data['TT1260SvcName'], Data['TT1260Snr'], Data['TT1260Margin'])
        Info = Info + Snmp
        Info[5] = int(Info[5])/100
        Info[6] = int(Info[6])/100
        if Info[6] == 100.0:
            Info[6] = 0.0
    else:
        Info = Info + ['N/A', 'N/A', 0]
    logger.info("2 - Ajout du statut Locked")
    if float(Info[6]) > 0.1:
        Info.append("Locked")
    else:
        Info.append("Unlocked")
    with open(Data['CSV']) as f:
        reader = csv.reader(f, delimiter=';')
        lines = [l for l in reader]
    for item in lines:
        if Info[0] == item[0]:
            lines.remove(item)
        else:
            pass
    lines.append(Info)
    logger.info("3 - Ecriture des Informations")
    with open(Data['CSV'], "w", newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerows(lines)
    logger.info("4 - Fichier CSV mis à jour par IRDInfo3")
    return Info

# Définition de la commande 'SNMP Get'
def SNMPget(IPAddr, OID1, OID2, OID3):
    try:
        snmp = []
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                CommunityData('private', mpModel=0),
                UdpTransportTarget((IPAddr, 161)),
                ContextData(),
                ObjectType(ObjectIdentity(OID1)),
                ObjectType(ObjectIdentity(OID2)),
                ObjectType(ObjectIdentity(OID3))))
        if errorIndication or errorStatus:
            logger.error("No SNMP response before timeout")
            snmp = ['', 0, 0]
            return snmp
        else:
            for varBind in varBinds:
                m = re.search('(.*)\ =\ (.*)', varBind.prettyPrint())
                state = m.group(2)
                snmp.append(state)
            return snmp
    except:
        logger.error("Impossible de récupérer les infos SNMP...")
        snmp = ['', 0, 0]
        return snmp
