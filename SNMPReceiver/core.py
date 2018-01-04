#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Developeurs : VBNIN + CKAR - IPEchanges.
Script de relevé des niveaux de réceptions des IRD nodal
"""

import logging
import configparser
import os
import sys
import csv
from logging.handlers import RotatingFileHandler
from Libraries import PrintException, Launcher, SatPulse
from time import sleep

# Activation du logger principal
try:
    LogPath = 'SNMPReceiver.log' if sys.platform.lower() == 'win32' else '/var/log/SNMPReceiver.log'
    handler = RotatingFileHandler(LogPath, maxBytes=10000000, backupCount=5)
    handler.setFormatter(logging.Formatter('%(asctime)s : %(message)s'))
    logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(message)s')
    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
except:
    PrintException("Impossible d'initialiser le fichier de logs.")
    exit()

# Lecture du fichier de Configuration et attribution des variables
try:
    Data = {}
    config = configparser.SafeConfigParser()
    config.read('d:/_DATA Documents/Python/IRDControlRoom/SNMPReceiver/config.ini' if sys.platform.lower() == 'win32' else '/usr/local/bin/IRDControlRoom/SNMPReceiver/config.ini')
    Data["Locked"] = []
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
        Model = "type" + str(i)
        Data[Position] = config.get('IRD', 'IRD' + str(i))
        Data[Model] = config.get('IRD', 'IRD' + str(i) + 'Model')
except:
    PrintException("Fichier de configuration 'config.ini' invalide ou introuvable.")
    exit()

if __name__ == '__main__':
    try:
        logger.info("Initialisation du script...")
        with open(Data['CSV'], "w", newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerows('')
        Launcher(Data)
        logger.info("Lancement de la boucle de vérification")
        SatPulse(Data)
    except:
        logger.info("Fin du script.")
        raise
