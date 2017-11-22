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
from logging.handlers import RotatingFileHandler
from argparse import ArgumentParser
from Libraries import PrintException

# Activation du logger principal
try:
    handler = RotatingFileHandler('/var/log/SNMPInfo.log', maxBytes=10000000, backupCount=5)
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
    DR5000Name = config.get('DR5000','OidName')
    DR5000Model = config.get('DR5000','OidModel')
    DR5000Power = config.get('DR5000','OidPower')
    DR5000Margin = config.get('DR5000','OidMargin')
    DR50000SvcName = config.get('DR5000','OidServiceName')

except:
    PrintException("Fichier de configuration invalide ou non précisé.\n\033[1;31mPour rappel :\033[1;33m sudo ./core.py -c 'emplacement du fichier de configuration'\033[0m")
    exit()

# Démarrage de la boucle de vérification d'état de transmission
logger.info("Initialisation du script...")
time.sleep(2)