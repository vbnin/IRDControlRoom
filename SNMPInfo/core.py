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
    DR5000Addr = config.get('DR5000','IPAddr')
    DR5000Model = config.get('DR5000','Model')
    DR5000Name = config.get('DR5000','OidName')
    DR5000Snr = config.get('DR5000','OidSnr')
    DR5000Margin = config.get('DR5000','OidMargin')
    DR5000SvcName = config.get('DR5000','OidServiceName')

except:
    PrintException("Fichier de configuration invalide ou non précisé.\n\033[1;31mPour rappel :\033[1;33m sudo ./core.py -c 'emplacement du fichier de configuration'\033[0m")
    exit()

# Démarrage de la boucle de vérification d'état de transmission
logger.info("Initialisation du script...")
c = csv.writer(open("D:\\fichier_status.csv", "w"))

for Addr in DR5000Addr.split(","):
    DR5000state(Addr, DR5000Model, DR5000Name, DR5000Snr, DR5000Margin, DR5000SvcName, c)