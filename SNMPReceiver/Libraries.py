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

#Import des librairies internes
import sys
import csv
import re
import socket
import logging 
from logging.handlers import RotatingFileHandler


# Activation du logger
LogPath = 'SNMPReceiver.log' if sys.platform.lower() == 'win32' else '/var/log/SNMPReceiver.log'
handler = RotatingFileHandler(LogPath, maxBytes=10000000, backupCount=5)
handler.setFormatter(logging.Formatter('%(asctime)s : %(message)s'))
logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(message)s')
logger = logging.getLogger(__name__)
logger.addHandler(handler)

# Fonction de lancement des Process et écriture du CSV
def CheckLoop(DataDict):
    while True:
        DataCSV = []
        for i in range(1, 36):
            DataCSV.append(IRDInfo(i, DataDict))
        with open(DataDict['CSV'], "w", newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerows(DataCSV)
        logger.info("Fichier CSV mis à jour par InitCSV.")
        TCPget(DataDict, DataCSV)
        logger.info("Affichage Mosaique mis à jour par TCPget.")

# Fonction de collection des informations par SNMP
def IRDInfo(i, Data):
    Position = "ird" + str(i)
    Model = "model" + str(i)
    SatName = "SAT-" + str('%02d' % i)
    logger.debug("Collecte des Infos pour " + SatName)
    Info = [Position, SatName, Data[Position], Data[Model]]
    if Data[Model] == "DR5000":
        Snmp = SNMPget(Data[Position], 0, Data['DR5000SvcName'], Data['DR5000Snr'], Data['DR5000Margin'])
        Info = Info + Snmp
        Info[5] = int(Info[5])/10
        Info[6] = int(Info[6])/10
    elif Data[Model] == "TT1260":
        Snmp = SNMPget(Data[Position], 0, Data['TT1260SvcName'], Data['TT1260Snr'], Data['TT1260Margin'])
        Info = Info + Snmp
        Info[5] = int(Info[5])/100
        Info[6] = int(Info[6])/100
        if Info[6] == 100.0:
            Info[6] = 0.0
    elif Data[Model] == "RX8200":
        Snmp = SNMPget(Data[Position], 1, Data['RX8200SvcName'], Data['RX8200Snr'], Data['RX8200Margin'])
        Info = Info + Snmp
        if Info[4][:7] == "No Such":
            Info[4:6] = ['', 0.0, 0.0]
        else:
            try:
                Info[5:6] = [Info[5][:4], Info[6][2:6]]
            except:
                Info[5:6] = [0.0, 0.0]
    elif Data[Model] == "RX1290":
        Snmp = SNMPget(Data[Position], 0, Data['RX1290SvcName'], Data['RX1290Snr'], Data['RX1290Margin'])
        Info = Info + Snmp
        Info[5] = int(Info[5])/100
        Info[6] = int(Info[6])/100
        if Info[6] == 100.0:
            Info[6] = 0.0
    else:
        Info = Info + ['Non géré', 'Non géré', 'Non géré']
    return Info

# Définition de la commande 'SNMP Get'
def SNMPget(IPAddr, SNMPv, OID1, OID2, OID3):
    try:
        snmp = []
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                CommunityData('private', mpModel=SNMPv),
                UdpTransportTarget((IPAddr, 161)),
                ContextData(),
                ObjectType(ObjectIdentity(OID1)),
                ObjectType(ObjectIdentity(OID2)),
                ObjectType(ObjectIdentity(OID3))))
        if errorIndication or errorStatus:
            logger.error("No SNMP response before timeout")
            snmp = ['Erreur : SNMP timeout', 0.0, 0.0]
            return snmp
        else:
            for varBind in varBinds:
                m = re.search('(.*)\ =\ (.*)', varBind.prettyPrint())
                state = m.group(2)
                snmp.append(state)
            return snmp
    except:
        logger.error("Impossible de récupérer les infos SNMP...")
        snmp = ['Erreur : SNMP timeout', 0.0, 0.0]
        return snmp

def TCPget(Data, DataCSV):
    # Open socket, send message, close socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try :
        s.connect((Data['MosaAddr'], Data['MosaTCPPort']))
    except TimeoutError:
        logger.error(TimeoutError)
        return
    OpenCmd = "<openID>{}</openID>\n".format(Data['MosaRoom'])
    s.send(OpenCmd.encode())
    Feedback = s.recv(Data['MosaBuffer'])
    if Feedback[:6].decode() == "<ack/>":
        logger.info("Connexion établie avec la mosaique Miranda, upload des informations...")
    else:
        logger.error("Erreur de connexion avec la Mosaique !")
        return
    for Info in DataCSV:
        MosaName = Info[1].replace('-', '') + "_MARGIN"
        try:
            if int(Info[6]) > 0.1 and int(Info[6]) <= 2.99:
                SendCmd = '<setKStatusMessage>set id="{}" status="WARNING" message="{}"</setKStatusMessage>\n'.format(MosaName, Info[6])
            elif int(Info[6]) > 2.99 and int(Info[6]) <= 7.0:
                SendCmd = '<setKStatusMessage>set id="{}" status="OK" message="{}"</setKStatusMessage>\n'.format(MosaName, Info[6])
            elif int(Info[6]) > 7.0:
                SendCmd = '<setKStatusMessage>set id="{}" status="MAJOR" message="{}"</setKStatusMessage>\n'.format(MosaName, Info[6])
            else:
                SendCmd = '<setKStatusMessage>set id="{}" status="ERROR" message="Unlocked"</setKStatusMessage>\n'.format(MosaName)
        except:
            SendCmd = '<setKStatusMessage>set id="{}" status="ERROR" message="Erreur"</setKStatusMessage>\n'.format(MosaName)
        s.send(SendCmd.encode())
    s.send("<closeID/>\n".encode())
    s.close()
