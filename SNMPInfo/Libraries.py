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
import subprocess
import platform
from logging.handlers import RotatingFileHandler
from pysnmp.hlapi import *

# Activation du logger
handler = RotatingFileHandler('SNMPInfo.log', maxBytes=10000000, backupCount=5)
handler.setFormatter(logging.Formatter('%(asctime)s : %(message)s'))
logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(message)s')
logger = logging.getLogger(__name__)
logger.addHandler(handler)

# Définition de la fonction PrintException
def PrintException(msg):
    print("***********************************************************************")
    print(msg)
    print("***********************************************************************")

# Définition de la fonction de vérification du type d'OS utilisé
def OSType(OS):
    if platform.system().lower() == OS.lower():
        return True
    else:
        return False

# Définition de la fonction de ping
def Ping(hostname, OS):
    try:
        subprocess.check_output("ping -{0} 2 -w 300 -{1} 255 {2}".format("n" if OSType(OS) is True else "c", "i" if OSType(OS) is True else "t", hostname))
    except:
        logger.error("L'IRD " + hostname + " est injoignable !!")
        return False
    return True

# Définition de la commande 'SNMP Get'
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
            state = 'Erreur'
            return state
        elif errorStatus:
            logger.error('%s at %s' % (errorStatus.prettyPrint(),
                            errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
            state = 'Erreur'
            return state
        else:
            for varBind in varBinds:
                state = (' = '.join([x.prettyPrint() for x in varBind]))
                logger.debug(state)
                m = re.search('(.*)\ =\ (.*)', state)
                state = m.group(2)
                return state
    except:
        logger.error("Impossible de récupérer les infos SNMP...")
        state = 'Erreur'
        return state

def DR5000state(Position, Name, Addr, SvcName, Snr, Margin, DataCSV):
    Info = {'Position':Position,
            'Name':SNMPget(Addr, Name),
            'Addr':Addr,
            'Model':"Ateme DR5000",
            'SvcName':SNMPget(Addr, SvcName),
            'Snr':int(SNMPget(Addr, Snr))/10,
            'Margin':int(SNMPget(Addr, Margin))/10,
            }
    d = []
    for key in Info:
        d.append(Info[key])
    DataCSV.append(d)
    return DataCSV

def RX8200state(Position, Name, Addr, SvcName, Snr, Margin, DataCSV):
    Info = {'Position':Position,
            'Name':Name,
            'Addr':Addr,
            'Model':"Ericsson RX8200",
            'SvcName':SNMPget(Addr, SvcName),
            'Snr':SNMPget(Addr, Snr)[:4],
            'Margin':SNMPget(Addr, Margin)[2:6],
            }
    if Info['SvcName'][:7] == "No Such":
        Info['SvcName'] = ''
    d = []
    for key in Info:
        d.append(Info[key])
    DataCSV.append(d)
    return DataCSV

def TT1260state(Position, Name, Addr, SvcName, Snr, Margin, DataCSV):
    Info = {'Position':Position,
            'Name':Name,
            'Addr':Addr,
            'Model':"Tandberg TT1260",
            'SvcName':SNMPget(Addr, SvcName),
            'Snr':int(SNMPget(Addr, Snr))/100,
            'Margin':int(SNMPget(Addr, Margin))/100,
            }
    if Info['Margin'] == 100.0:
        Info['Margin'] = 0.0
    d = []
    for key in Info:
        d.append(Info[key])
    DataCSV.append(d)
    return DataCSV

def RX1290state(Position, Name, Addr, SvcName, Snr, Margin, DataCSV):
    Info = {'Position':Position,
            'Name':Name,
            'Addr':Addr,
            'Model':"Ericsson RX1290",
            'SvcName':SNMPget(Addr, SvcName),
            'Snr':int(SNMPget(Addr, Snr))/100,
            'Margin':int(SNMPget(Addr, Margin))/100,
            }
    d = []
    for key in Info:
        d.append(Info[key])
    DataCSV.append(d)
    return DataCSV

def NoSat(Position, SatName, Model, DataCSV):
    Info = {'Position':Position,
            'Name':SatName,
            'Addr':'',
            'Model':Model,
            'SvcName':'',
            'Snr':'',
            'Margin':'',
            }
    d = []
    for key in Info:
        d.append(Info[key])
    DataCSV.append(d)
