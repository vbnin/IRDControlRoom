#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Developeurs : VBNIN + CKAR - IPEchanges.
Ce fichier est une librairie requise par le script core.py
"""

# Import des librairies
import logging
import re
import csv
from logging.handlers import RotatingFileHandler
from pysnmp.hlapi import *

# Activation du logger
handler = RotatingFileHandler('D:\SNMPInfo.log', maxBytes=10000000, backupCount=5)
handler.setFormatter(logging.Formatter('%(asctime)s : %(message)s'))
logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(message)s')
logger = logging.getLogger(__name__)
logger.addHandler(handler)

# Définition de la fonction PrintException
def PrintException(msg):
    print("***********************************************************************")
    print(msg)
    print("***********************************************************************")

# Définition de la commande SNMP Get
def SNMPget(IPAddr, OID):
    try:
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                CommunityData('private', mpModel=0),
                UdpTransportTarget((IPAddr, 161)),
                ContextData(),
                ObjectType(ObjectIdentity(OID))))

        if errorIndication:
            logger.error(errorIndication)
            state = '2'
            return state
        elif errorStatus:
            logger.error('%s at %s' % (errorStatus.prettyPrint(),
                            errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
            state = '2'
            return state
        else:
            for varBind in varBinds:
                state = (' = '.join([x.prettyPrint() for x in varBind]))
                logger.debug(state)
                m = re.search('(.*)\ =\ (.*)', state)
                state = m.group(2)
                return state
    except:
        logger.error("Erreur générale...")
        state = '2'
        return state

def DR5000state(Position, DR5000Name, Addr, DR5000SvcName, DR5000Snr, DR5000Margin, c):
    DataCSV = []
    Info = {'Position':Position,
            'Name':SNMPget(Addr, DR5000Name),
            'Addr':Addr,
            'Model':"Ateme DR5000",
            'SvcName':SNMPget(Addr, DR5000SvcName),
            'Snr':int(SNMPget(Addr, DR5000Snr))/10,
            'Margin':int(SNMPget(Addr, DR5000Margin))/10,
            }
    
    for key in Info:
        DataCSV.append(Info[key])

    print(DataCSV)
    c.writerow(DataCSV)

# Dupliquer DR5000state et personnaliser par IRD
