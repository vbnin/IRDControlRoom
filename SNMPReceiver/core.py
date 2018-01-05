#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Developeurs : VBNIN + CKAR - IPEchanges.
Script de relevé des niveaux de réceptions des IRD nodal
"""

import logging
import configparser
import sys
import csv
import os
import time
import subprocess
from logging.handlers import RotatingFileHandler
from Libraries import PrintException, IRDInfo1, IRDInfo2
from multiprocessing import Process, Queue

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
    config.read(os.path.join(os.path.dirname(__file__), 'config.ini') if sys.platform.lower() == 'win32' else '/usr/local/bin/IRDControlRoom/SNMPReceiver/config.ini')
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

def InitCSV(Data):
    queue = Queue()
    plist = [Process(target=IRDInfo1, args=(i, Data, queue)) for i in range(1, 36)]
    for p in plist:
        p.start()
    for p in plist:
        p.join()
    DataCSV = [queue.get() for p in plist]
    logger.info(DataCSV)
    with open(Data['CSV'], "w", newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerows(DataCSV)
    time.sleep(0.01)
    logger.info("Fichier CSV mis à jour par InitCSV.")
    return

# Fonction de récupération d'état par script périodique
def IRDLockLoop(Data):
    queue = Queue()
    LockList = []
    plist = []
    with open(Data['CSV']) as f:
        reader = csv.reader(f, delimiter=';')
        lines = [l for l in reader]
    for item in lines:
        try:
            if item[7] == "Locked":
                plist.append(Process(target=IRDInfo2, args=(item, Data, queue)))
            else:
                pass
        except:
            logger.error("Erreur, statut Locked non trouvé !!!")
    if plist == []:
        logger.info('No active IRD')
        time.sleep(0.01)
        return
    else:
        for p in plist:
            p.start()
        for p in plist:
            p.join()
        DataCSV = [queue.get() for p in plist]
        with open(Data['CSV']) as f:
            reader = csv.reader(f, delimiter=';')
            lines = [l for l in reader]
        for item in lines:
            if item[7] == "Locked":
                lines.remove(item)
            else:
                pass
        lines = lines + DataCSV
        logger.info("4 - Ecriture des Informations")
        with open(Data['CSV'], "w", newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerows(lines)
        time.sleep(0.01)
        logger.info("5 - Fichier CSV mis à jour par IRDLockLoop")
        return

if __name__ == '__main__':
    try:
        logger.info("Initialisation du script...")
        # CBprocess = subprocess.Popen(['python', os.path.join(os.path.dirname(__file__), 'CallBack.py')], stdout = subprocess.PIPE )
        while True:
            InitCSV(Data)
            for i in range(4):
                IRDLockLoop(Data)
    except:
        logger.info("Fin du script.")
        raise
