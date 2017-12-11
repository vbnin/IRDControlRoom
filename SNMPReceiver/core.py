#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Developeurs : VBNIN + CKAR - IPEchanges.
Script de relevé des niveaux de réceptions des IRD nodal
"""

from pysnmp.carrier.asyncore.dispatch import AsyncoreDispatcher
from pysnmp.carrier.asyncore.dgram import udp
from pyasn1.codec.ber import decoder
from pysnmp.proto import api
from logging.handlers import RotatingFileHandler
from Libraries import PrintException, IRDstate, Launcher
import logging
from argparse import ArgumentParser
import configparser
import csv

# Activation du logger principal
try:
    handler = RotatingFileHandler('SNMPReceiver.log', maxBytes=10000000, backupCount=5)
    handler.setFormatter(logging.Formatter('%(asctime)s : %(message)s'))
    logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(message)s')
    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
except:
    PrintException("Impossible d'initialiser le fichier de logs.")
    exit()

# Récupération des variables de démarrage
parser = ArgumentParser()
parser.add_argument("-c", "--config", dest="config", help="Préciser le chemin du fichier config.ini")
args = parser.parse_args()

# Lecture du fichier de Configuration et attribution des variables
try:
    Addresses = {}
    Data = {}
    config = configparser.ConfigParser()
    config.read(args.config)
    Addresses['DR5000'] = config.get('DR5000', 'Addr')
    Data['DR5000Snr'] = config.get('DR5000', 'OidSnr')
    Data['DR5000Margin'] = config.get('DR5000', 'OidMargin')
    Data['DR5000SvcName'] = config.get('DR5000', 'OidServiceName')
    Addresses['RX8200'] = config.get('RX8200', 'Addr')
    Data['RX8200Snr'] = config.get('RX8200', 'OidSnr')
    Data['RX8200Margin'] = config.get('RX8200', 'OidMargin')
    Data['RX8200SvcName'] = config.get('RX8200', 'OidServiceName')
    Addresses['TT1260'] = config.get('TT1260', 'Addr')
    Data['TT1260Snr'] = config.get('TT1260', 'OidSnr')
    Data['TT1260Margin'] = config.get('TT1260', 'OidMargin')
    Data['TT1260SvcName'] = config.get('TT1260', 'OidServiceName')
    for i in range(1, 36):
        Position = "ird" + str(i)
        Model = "type" + str(i)
        Data[Position] = config.get('IRD', 'IRD' + str(i))
        Data[Model] = config.get('IRD', 'IRD' + str(i) + 'Model')
except:
    PrintException("Fichier de configuration invalide ou non précisé.Pour rappel : core.py -c 'emplacement du fichier de configuration'")
    exit()

# CallBack function for receiving traps
def cbFun(transportDispatcher, transportDomain, transportAddress, wholeMsg):
    trap = {}
    global Addresses
    global Data
    while wholeMsg:
        msgVer = int(api.decodeMessageVersion(wholeMsg))
        pMod = api.protoModules[msgVer]
        reqMsg, wholeMsg = decoder.decode(
            wholeMsg, asn1Spec=pMod.Message(),
        )
        logger.info('Notification message from ' + str(transportAddress[0]))
        trap['Addr'] = transportAddress[0]
        reqPDU = pMod.apiMessage.getPDU(reqMsg)
        if reqPDU.isSameTypeWith(pMod.TrapPDU()):
            varBinds = pMod.apiPDU.getVarBinds(reqPDU)
            for oid, val in varBinds:
                trap[oid.prettyPrint()] = val.prettyPrint()
        if trap['Addr'] in Addresses['DR5000']:
            IRDstate(trap['Addr'], 'DR5000', Data)
        elif trap['Addr'] in Addresses['TT1260']:
            IRDstate(trap['Addr'], 'TT1260', Data)
        elif trap['Addr'] in Addresses['RX8200']:
            IRDstate(trap['Addr'], 'RX8200', Data)
    return trap  

# Ouverture du socket IPv4 SNMP
transportDispatcher = AsyncoreDispatcher()
transportDispatcher.registerRecvCbFun(cbFun)
transportDispatcher.registerTransport(
    udp.domainName, udp.UdpSocketTransport().openServerMode(('0.0.0.0', 162))
)
transportDispatcher.jobStarted(1)

try:
    # Dispatcher will never finish as job#1 never reaches zero
    #f = csv.writer(open("fichier_status.csv", "a", newline=''), delimiter = ';')
    logger.info("Initialisation du script...")
    Launcher(Data)
    transportDispatcher.runDispatcher()
except:
    transportDispatcher.closeDispatcher()
    raise