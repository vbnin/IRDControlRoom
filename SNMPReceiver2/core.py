#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Developeurs : VBNIN + CKAR - IPEchanges.
Script de relevé des niveaux de réceptions des IRD nodal
"""

import logging
import configparser #Librairie externe à télécharger
import sys
import os
from logging.handlers import RotatingFileHandler
from Libraries import CheckLoop

# Activation du logger principal
try:
    LogPath = 'SNMPReceiver.log' if sys.platform.lower() == 'win32' else '/var/log/SNMPReceiver.log'
    handler = RotatingFileHandler(LogPath, maxBytes=10000000, backupCount=5)
    handler.setFormatter(logging.Formatter('%(asctime)s : %(message)s'))
    logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(message)s')
    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    logger.info("Initialisation du fichier de log dans " + LogPath)
except:
    print("Impossible d'initialiser le fichier de logs.")
    exit()

# Lecture du fichier de Configuration et attribution des variables
try:
    Data = {}
    logger.info("Lecture du fichier config.ini")
    config = configparser.SafeConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'config.ini') if sys.platform.lower() == 'win32' else '/usr/local/bin/IRDControlRoom/SNMPReceiver/config.ini')
    Data['CSV'] = config.get('GENERAL', 'CSVfile')
    Data['WinCSV'] = config.get('GENERAL', 'WinCSVfile')
    Data['MosaAddr'] = config.get('MOSAIQUE', 'IPAddress')
    Data['MosaTCPPort'] = int(config.get('MOSAIQUE', 'PortTCP'))
    Data['MosaBuffer'] = int(config.get('MOSAIQUE', 'BufferSize'))
    Data['MosaRoom'] = config.get('MOSAIQUE', 'Room')
    Data['DR5000Snr'] = config.get('DR5000', 'OidSnr')
    Data['DR5000Margin'] = config.get('DR5000', 'OidMargin')
    Data['DR5000SvcName'] = config.get('DR5000', 'OidServiceName')
    Data['RX8200Snr'] = config.get('RX8200', 'OidSnr')
    Data['RX8200Margin'] = config.get('RX8200', 'OidMargin')
    Data['RX8200SvcName'] = config.get('RX8200', 'OidServiceName')
    Data['TT1260Snr'] = config.get('TT1260', 'OidSnr')
    Data['TT1260Margin'] = config.get('TT1260', 'OidMargin')
    Data['TT1260SvcName'] = config.get('TT1260', 'OidServiceName')
    Data['RX1290Snr'] = config.get('RX1290', 'OidSnr')
    Data['RX1290Margin'] = config.get('RX1290', 'OidMargin')
    Data['RX1290SvcName'] = config.get('RX1290', 'OidServiceName')
    for i in range(1, 36):
        Position = "ird" + str(i)
        Model = "model" + str(i)
        Data[Position] = config.get('IRD', 'IRD' + str(i))
        Data[Model] = config.get('IRD', 'IRD' + str(i) + 'Model')
except:
    print("Fichier de configuration 'config.ini' invalide ou introuvable.")
    exit()

if __name__ == '__main__':
    try:
        logger.info("Initialisation de la boucle de vérification...")
        CheckLoop(Data)
    except:
        print("Fin inattendue du script.")
        raise
