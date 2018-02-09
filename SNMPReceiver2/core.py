#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Developeurs : VBNIN + CKAR - IPEchanges.
Script de relevé des niveaux de réceptions des IRD nodal
Release v2.0 avec librairie EasySNMP
"""

#Librairie externe à télécharger
import configparser 

#Import des librairies internes
import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from Libraries import CheckLoop, InitScript

# Activation du logger principal
try:
    LogPath = 'SNMPReceiver.log' if sys.platform.lower() == 'win32' else '/var/log/SNMPReceiver.log'
    handler = RotatingFileHandler(LogPath, maxBytes=10000000, backupCount=5, encoding="utf-8")
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
            Data[ModelCheck] = config.get(item, 'Oid'+Oid)
    for i in range(1, 36):
        Position = "ird" + str(i)
        Data[Position] = config.get('IRD', 'IRD' + str(i))
except:
    print("Fichier de configuration 'config.ini' invalide ou introuvable.")
    exit()

if __name__ == '__main__':
    try:
        logger.info("Démarrage du script.")
        Dict = InitScript(Data)
        Data = {**Data, **Dict}
        logger.info("Initialisation de la boucle de vérification...")
        CheckLoop(Data)
    except:
        print("Fin inattendue du script.")
        raise
