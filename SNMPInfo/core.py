#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Developeurs : VBNIN + CKAR - IPEchanges.
Script de relevé des niveaux de réceptions des IRD nodal
"""

# Import des librairies
import time
import logging
import configparser
import csv
import threading
from logging.handlers import RotatingFileHandler
from argparse import ArgumentParser
from Libraries import PrintException, DR5000state, RX8200state, TT1260state, RX1290state, Ping, NoSat

# Activation du logger principal
try:
    handler = RotatingFileHandler('SNMPInfo.log', maxBytes=10000000, backupCount=5)
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
    ird = {}
    DR5000 = {} 
    RX8200 = {}
    TT1260 = {}
    RX1290 = {}
    config = configparser.ConfigParser()
    config.read(args.config)
    OS = config.get('GENERAL', 'OSType').lower()
    DR5000['Name'] = config.get('DR5000', 'OidName')
    DR5000['Snr'] = config.get('DR5000', 'OidSnr')
    DR5000['Margin'] = config.get('DR5000', 'OidMargin')
    DR5000['SvcName'] = config.get('DR5000', 'OidServiceName')
    RX8200['Snr'] = config.get('RX8200', 'OidSnr')
    RX8200['Margin'] = config.get('RX8200', 'OidMargin')
    RX8200['SvcName'] = config.get('RX8200', 'OidServiceName')
    TT1260['Snr'] = config.get('TT1260', 'OidSnr')
    TT1260['Margin'] = config.get('TT1260', 'OidMargin')
    TT1260['SvcName'] = config.get('TT1260', 'OidServiceName')
    RX1290['Snr'] = config.get('RX1290', 'OidSnr')
    RX1290['Margin'] = config.get('RX1290', 'OidMargin')
    RX1290['SvcName'] = config.get('RX1290', 'OidServiceName')
    for i in range(1, 36):
        Position = "ird" + str(i)
        Model = "type" + str(i)
        ird[Position] = config.get('IRD', 'IRD' + str(i))
        ird[Model] = config.get('IRD', 'IRD' + str(i) + 'Model')

except:
    PrintException("Fichier de configuration invalide ou non précisé.Pour rappel : sudo ./core.py -c 'emplacement du fichier de configuration'")
    exit()

# Démarrage de la boucle de vérification d'état de transmission
logger.info("Initialisation du script...")

while True:
    DataCSV = []
    f = csv.writer(open("fichier_status.csv", "w", newline=''), delimiter = ';')
    for i in range(1, 36):
        Position = "ird" + str(i)
        Model = "type" + str(i)
        SatName = "SAT-" + str(i)
        if ird[Model] == 'DR5000' and Ping(ird[Position], OS) is True:
            t = threading.Thread(target=DR5000state, args=(Position, DR5000['Name'], ird[Position], DR5000['SvcName'], DR5000['Snr'], DR5000['Margin'], DataCSV))
            t.start()
        elif ird[Model] == 'RX8200' and Ping(ird[Position], OS) is True:
            t = threading.Thread(target=RX8200state, args=(Position, SatName, ird[Position], RX8200['SvcName'], RX8200['Snr'], RX8200['Margin'], DataCSV))
            t.start()
        elif ird[Model] == 'TT1260' and Ping(ird[Position], OS) is True:
            t = threading.Thread(target=TT1260state, args=(Position, SatName, ird[Position], TT1260['SvcName'], TT1260['Snr'], TT1260['Margin'], DataCSV))
            t.start()
        elif ird[Model] == 'RX1290' and Ping(ird[Position], OS) is True:
            t = threading.Thread(target=RX1290state, args=(Position, SatName, ird[Position], RX1290['SvcName'], RX1290['Snr'], RX1290['Margin'], DataCSV))
            t.start()
        else:
            NoSat(Position, SatName, ird[Model], DataCSV)
    time.sleep(2)         
    f.writerows(DataCSV)
    logger.info("Done")