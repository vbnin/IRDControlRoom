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
from logging.handlers import RotatingFileHandler
from argparse import ArgumentParser
from Libraries import PrintException, DR5000state

# Activation du logger principal
try:
    handler = RotatingFileHandler('D:\SNMPInfo.log', maxBytes=10000000, backupCount=5)
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
    config = configparser.ConfigParser()
    config.read(args.config)
    DR5000Name = config.get('DR5000', 'OidName')
    DR5000Snr = config.get('DR5000', 'OidSnr')
    DR5000Margin = config.get('DR5000', 'OidMargin')
    DR5000SvcName = config.get('DR5000', 'OidServiceName')
    RX8200Name = config.get('RX8200', 'OidName')
    RX8200Snr = config.get('RX8200', 'OidSnr')
    RX8200Margin = config.get('RX8200', 'OidMargin')
    RX8200SvcName = config.get('RX8200', 'OidServiceName')
    TT1260Name = config.get('TT1260', 'OidName')
    TT1260Snr = config.get('TT1260', 'OidSnr')
    TT1260Margin = config.get('TT1260', 'OidMargin')
    TT1260SvcName = config.get('TT1260', 'OidServiceName')
    RX1290Name = config.get('RX1290', 'OidName')
    RX1290Snr = config.get('RX1290', 'OidSnr')
    RX1290Margin = config.get('RX1290', 'OidMargin')
    RX1290SvcName = config.get('RX1290', 'OidServiceName')
    s = {}
    for i in range(1, 36):
        Name = "ird" + str(i)
        Model = "type" + str(i)
        s[Name] = config.get('IRD', 'IRD' + str(i))
        s[Model] = config.get('IRD', 'IRD' + str(i) + 'Model')

except:
    PrintException("Fichier de configuration invalide ou non précisé.Pour rappel : sudo ./core.py -c 'emplacement du fichier de configuration'")
    exit()

# Démarrage de la boucle de vérification d'état de transmission
logger.info("Initialisation du script...")

while True:
    c = csv.writer(open("D:\\fichier_status.csv", "w", newline=''), delimiter = ';')
    for i in range(1, 36):
        Name = "ird" + str(i)
        Model = "type" + str(i)
        if s[Model] == 'DR5000':
            DR5000state(Name, DR5000Name, s[Name], DR5000SvcName, DR5000Snr, DR5000Margin, c)
        elif s[Model] == 'RX8200':
            print('RX8200state')
        elif s[Model] == 'TT1260':
            print('TT1260state')
        elif s[Model] == 'RX1290':
            print('RX1290state')
        else:
            pass
    time.sleep(1)
# Définir les fonctions pour chaque cas