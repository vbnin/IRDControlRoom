#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Developeurs : VBNIN + CKAR - IPEchanges.
Script de relevé des niveaux de réceptions des IRD nodal
Release v2.0 avec librairie EasySNMP
"""

#Librairies externe à télécharger
from easysnmp import Session, snmp_get

#Import des librairies internes
import sys
import csv
import re
import socket
import logging
import time
from logging.handlers import RotatingFileHandler

# Activation du logger
LogPath = 'SNMPReceiver.log' if sys.platform.lower() == 'win32' else '/var/log/SNMPReceiver.log'
handler = RotatingFileHandler(LogPath, maxBytes=10000000, backupCount=5, encoding="utf-8")
handler.setFormatter(logging.Formatter('%(asctime)s : %(message)s'))
logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(message)s')
logger = logging.getLogger(__name__)
logger.addHandler(handler)

# Définition de la fonction pour déterminer le modèle des IRD
def InitScript(Data):
    Dict = {}
    for i in range(1, 36):
        Position = "ird" + str(i)
        Model = "model" + str(i)
        try:
            s = snmp_get(Data['IRDModel'], hostname=Data[Position], community='private', version=1)
        except:
            logger.error("Impossible de communiquer avec : {} !!".format(Position))
            Dict[Model] = 'Inconnu'
            continue
        m = re.search(r'(value=)\'(.*)\'\ (.*)', str(s))
        for item in Data['SupportedModels']:
            if re.search(item[:3], m.group(2), re.IGNORECASE):
                Dict[Model] = item
                break
            elif re.search(r'armv7', m.group(2), re.IGNORECASE):
                Dict[Model] = item
                break
            else:
                Dict[Model] = 'NoMatch'
        if Dict[Model] == 'NoMatch':
            logger.error("Impossible de déterminer le modèle de : {} !!".format(Position))
            Dict[Model] = 'Inconnu'
    logger.debug(Dict)
    return Dict

# Fonction de lancement des Process et écriture du CSV
def CheckLoop(DataDict):
    while True:
        DataCSV = []
        for i in range(1, 36):
            DataCSV.append(IRDInfo(i, DataDict))
        TCPget(DataDict, DataCSV)
        logger.debug("Affichage Mosaique mis à jour par TCPget.")
        DataCSV.append(["LastUpdate", time.strftime("%d/%m/%Y, %H:%M:%S")])
        try:
            with open(DataDict['WinCSV'] if sys.platform.lower() == 'win32' else DataDict['CSV'], "w", encoding="utf-8", newline='') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerows(DataCSV)
        except:
            logger.error("Impossible de mettre à jour le fichier CSV !")
            continue
        logger.debug("Fichier CSV mis à jour par CheckLoop.")
        logger.info("Mise a jour page web et mosaique : OK")

# Fonction de collection des informations par SNMP
def IRDInfo(i, Data):
    Position = "ird" + str(i)
    Model = "model" + str(i)
    SatName = "SAT-" + str('%02d' % i)
    logger.debug("Collecte des Infos pour " + SatName)
    Info = [Position, SatName, Data[Position], Data[Model]]
    if Data[Model] == "DR5000":
        OidList = [Data['DR5000Lock'], Data['DR5000ServiceName'], Data['DR5000Snr'], Data['DR5000Margin']]
        Snmp = SNMPget(Data[Position], 2, OidList)
        Info = Info + Snmp
        if int(Info[4]) == 1:
            Info[4] = 'Locked'
            Info[6] = float(Info[6])/10
            Info[7] = float(Info[7])/10
        else:
            Info[4:8] = ['Unlocked', 'Unlocked', 0.0, 0.0]
    elif Data[Model] == "DR8400":
        OidList = [Data['DR8400Lock'], Data['DR8400ServiceName'], Data['DR8400Snr'], Data['DR8400Margin']]
        Snmp = SNMPget(Data[Position], 2, OidList)
        Info = Info + Snmp
        Info[6] = float(Info[6])/10
        Info[7] = float(Info[7])/10
        if int(Info[4]) == 1:
            Info[4] = 'Locked'
        else:
            Info[4:8] = ['Unlocked', 'Unlocked', 0.0, 0.0]
    elif Data[Model] == "TT1260":
        OidList = [Data['TT1260Lock'], Data['TT1260ServiceName'], Data['TT1260Snr'], Data['TT1260Margin']]
        Snmp = SNMPget(Data[Position], 1, OidList)
        Info = Info + Snmp
        Info[6] = float(Info[6])/100
        Info[7] = float(Info[7])/100
        if int(Info[4]) == 2:
            Info[4] = 'Locked'
        else:
            Info[4:8] = ['Unlocked', 'Unlocked', 0.0, 0.0]
    elif Data[Model] == "RX8200":
        OidList = [Data['RX8200Lock'], Data['RX8200ServiceName'], Data['RX8200Snr'], Data['RX8200Margin']]
        Snmp = SNMPget(Data[Position], 2, OidList)
        Info = Info + Snmp
        if Info[4] == 'LOCKED':
            Info[4] = 'Locked'            
            try:
                Info[6:8] = [float(Info[6][:4]), float(Info[7][2:6])]
            except:
                logger.error('Problème avec les valeurs renvoyés par le RX8200 : {}'.format(Position))
                Info[6:8] = [0.0, 0.0]
        else:
            Info[4:8] = ['Unlocked', 'Unlocked', 0.0, 0.0]
    elif Data[Model] == "RX1290":
        OidList = [Data['RX1290Lock'], Data['RX1290ServiceName'], Data['RX1290Snr'], Data['RX1290Margin']]
        Snmp = SNMPget(Data[Position], 1, OidList)
        Info = Info + Snmp
        Info[6] = float(Info[6])/100
        Info[7] = float(Info[7])/100
        if int(Info[4]) == 2:
            Info[4] = 'Locked'
        else:
            Info[4:8] = ['Unlocked', 'Unlocked', 0.0, 0.0]
    else:
        Info = Info + ['Unlocked', 'Non géré', 0.0, 0.0]
    return Info

# Définition de la commande 'SNMP Get'
def SNMPget(IPAddr, SNMPv, OidList):
    try:
        snmp = []
        session = Session(hostname=IPAddr, community='private', version=SNMPv)
        for Oid in OidList:
            m = re.search(r'(value=)\'(.*)\'\ (.*)', str(session.get(Oid)))
            snmp.append(m.group(2))
        return snmp
    except:
        logger.error("Impossible de récupérer les infos SNMP...")
        snmp = ['Erreur', 'Erreur : SNMP timeout', 0.0, 0.0]
        return snmp

# Définition de la fonction de connexion TCP à la mosaique
def TCPget(Data, DataCSV):
    # Open socket, send message, close socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.5)
    try :
        s.connect((Data['MosaAddr'], Data['MosaTCPPort']))
        s.settimeout(None)
    except:
        logger.error("Impossible de joindre la mosaique ({}) !".format(Data['MosaAddr']))
        time.sleep(0) if sys.platform.lower() == 'win32' else time.sleep(1.5)
        return
    OpenCmd = "<openID>{}</openID>\n".format(Data['MosaRoom'])
    s.send(OpenCmd.encode())
    Feedback = s.recv(Data['MosaBuffer'])
    if Feedback[:6].decode() == "<ack/>":
        logger.debug("Connexion établie avec la mosaique Miranda, upload des informations...")
    else:
        logger.error("Erreur de connexion avec la Mosaique !")
        return
    for Info in DataCSV:
        MosaName = Info[1].replace('-', '') + "_MARGIN"
        try:
            if Info[4] == 'Unlocked':
                SendCmd = '<setKStatusMessage>set id="{}" status="ERROR" message="Unlocked"</setKStatusMessage>\n'.format(MosaName)
            elif Info[7] <= 2.99:
                SendCmd = '<setKStatusMessage>set id="{}" status="WARNING" message="{}"</setKStatusMessage>\n'.format(MosaName, Info[7])
            elif Info[7] > 2.99 and Info[7] <= 7.0:
                SendCmd = '<setKStatusMessage>set id="{}" status="OK" message="{}"</setKStatusMessage>\n'.format(MosaName, Info[7])
            elif Info[7] > 7.0:
                SendCmd = '<setKStatusMessage>set id="{}" status="MAJOR" message="{}"</setKStatusMessage>\n'.format(MosaName, Info[7])
            else:
                SendCmd = '<setKStatusMessage>set id="{}" status="ERROR" message="Erreur"</setKStatusMessage>\n'.format(MosaName)
        except:
            SendCmd = '<setKStatusMessage>set id="{}" status="ERROR" message="Erreur"</setKStatusMessage>\n'.format(MosaName)
        s.send(SendCmd.encode())
    s.send("<closeID/>\n".encode())
    s.close()
