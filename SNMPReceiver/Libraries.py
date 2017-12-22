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
from logging.handlers import RotatingFileHandler
from pysnmp.hlapi import *
from pysnmp.carrier.asyncore.dgram import udp, unix
from pyasn1.codec.ber import decoder
from pysnmp.proto import api
from multiprocessing import Process, Pool

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

# Définition de la fonction de remplissage du fichier CSV au démarrage
def Launcher(Data):
    DataCSV = []
    processes = []
    for i in range(1, 36):
        Position = "ird" + str(i)
        Model = "type" + str(i)
        SatName = "SAT-" + str(i)
        p = Process(target=IRDInfo, args=(Position, SatName, Data[Position], Data[Model], Data, DataCSV))
        processes.append(p)
        p.start()
    for p in processes:
        p.join()
    with open(Data['CSV'], "w", newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerows(DataCSV)
        logger.info("Fichier CSV mis à jour par Launcher.")

# Fonction de récupération d'état par script périodique
def SatPulse(Data):
    DataCSV = []
    processes = []
    for Addr in Data["Locked"]:
        for i in range(1, 36):
            Position = "ird" + str(i)
            Model = "type" + str(i)
            SatName = "SAT-" + str(i)
            if Addr == Data[Position]:
                p = Process(target=IRDInfo, args=(Position, SatName, Data[Position], Data[Model], Data, DataCSV))
                processes.append(p)
                p.start()
            else:
                pass
    for p in processes:
        p.join()
    for Addr in Data["Locked"]:
        with open(Data['CSV']) as f:
            reader = csv.reader(f, delimiter=';')
            lines = [l for l in reader]
            for item in lines:
                try:
                    item.index(Addr)
                    lines.remove(item)
                except:
                    pass
    with open(Data['CSV']) as f:
        reader = csv.reader(f, delimiter=';')
        lines = [l for l in reader]
        lines = lines + DataCSV
    with open(Data['CSV'], "w", newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerows(lines)
        logger.info("Fichier CSV mis à jour par SatPulse.")

# Fonction de récupération d'état via CallBack Function
def IRDstate(Addr, Model, Data):
    DataCSV = []
    for i in range(1, 36):
        Position = "ird" + str(i)
        SatName = "SAT-" + str(i)
        if Addr == Data[Position]:
            IRDInfo(Position, SatName, Data[Position], Data[Model], Data, DataCSV)
        else:
            pass
    with open(Data['CSV']) as f:
        reader = csv.reader(f, delimiter=';')
        lines = [l for l in reader]
        for item in lines:
            try:
                item.index(Position)
                lines.remove(item)
                lines.append(DataCSV[0])
            except:
                pass
    with open(Data['CSV'], "w", newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerows(lines)
        logger.info("Fichier CSV mis à jour par IRDstate.")
        
# Fonction de collection des informations par SNMP
def IRDInfo(Position, SatName, Addr, Model, Data, DataCSV):
    logger.info("1 - Collecte des Infos")
    Info = [Position, SatName, Addr, Model]
    logger.info(Info)
    if Model == "DR5000":
        Snmp = SNMPget(Addr, Data['DR5000SvcName'], Data['DR5000Snr'], Data['DR5000Margin'])
        logger.info(Snmp)
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
            Info[5] = Info[5][:4]
            Info[6] = Info[6][2:6]
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
    if Info[6] > 0 and Addr in Data["Locked"]:
        Info.append("Locked")
    elif Info[6] > 0 and Addr not in Data["Locked"]:
        Info.append("Locked")
        Data["Locked"].append(Addr)
    elif Info[6] <= 0 and Addr in Data["Locked"]:
        Info.append("Unlocked")
        Data["Locked"].remove(Addr)
    else:
        Info.append("Unlocked")
    logger.info(Info)
    DataCSV.append(Info)
    return DataCSV

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
