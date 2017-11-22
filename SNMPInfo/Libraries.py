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

def DR5000state(Addr, DR5000Model, DR5000Name, DR5000Snr, DR5000Margin, DR5000SvcName, c):
    Info = {'Model':DR5000Model,
            'Name':SNMPget(Addr, DR5000Name),
            'Snr':SNMPget(Addr, DR5000Snr),
            'Margin':SNMPget(Addr, DR5000Margin),
            'SvcName':SNMPget(Addr, DR5000SvcName),
            }
    
    for key in Info:
        print(Info[key])
        c.writerow(Info[key])