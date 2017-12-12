#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Developeurs : VBNIN + CKAR - IPEchanges.
Script de relevé des niveaux de réceptions des IRD nodal
"""

import logging
import configparser
from pysnmp.proto import api
from pyasn1.codec.ber import decoder
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.carrier.asyncore.dispatch import AsyncoreDispatcher
from logging.handlers import RotatingFileHandler
from argparse import ArgumentParser
from Libraries import PrintException, IRDstate, Launcher

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
parser.add_argument("-c", "--config", dest="config", help="Fichier config.ini")
args = parser.parse_args()

# Lecture du fichier de Configuration et attribution des variables
try:
    Data = {}
    config = configparser.ConfigParser()
    config.read(args.config)
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
except:
    PrintException("Fichier de configuration invalide ou introuvable. "
                   "Pour rappel : core.py -c config.ini")
    exit()

# CallBack function for receiving traps
def cbFun(transportDispatcher, transportDomain, transportAddress, wholeMsg):
    global Addresses
    global Data
    while wholeMsg:
        msgVer = int(api.decodeMessageVersion(wholeMsg))
        pMod = api.protoModules[msgVer]
        reqMsg, wholeMsg = decoder.decode(
            wholeMsg, asn1Spec=pMod.Message())
        logger.info('Trap SNMP recu de : ' + str(transportAddress[0]))
        for i in range(1, 36):
            Position = "ird" + str(i)
            Model = "type" + str(i)
            if transportAddress[0] == Data[Position]:
                IRDstate(Data[Position], Data[Model], Data)
                return
            else:
                pass
        logger.error("Aucune correspondance trouvée avec la table des IRD !")
        return

# Ouverture du socket IPv4 SNMP
transportDispatcher = AsyncoreDispatcher()
transportDispatcher.registerRecvCbFun(cbFun)
transportDispatcher.registerTransport(
    udp.domainName, udp.UdpSocketTransport().openServerMode(('0.0.0.0', 162)))
transportDispatcher.jobStarted(1)

# Dispatcher will never finish as job#1 never reaches zero
try:
    logger.info("Initialisation du script...")
    Launcher(Data)
    logger.info("Initialisation terminée, écoute des traps sur le port 162...")
    transportDispatcher.runDispatcher()
except:
    transportDispatcher.closeDispatcher()
    logger.info("Fin du script.")
    raise
