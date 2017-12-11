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
import threading
import subprocess
from logging.handlers import RotatingFileHandler
from pysnmp.hlapi import *
from pysnmp.carrier.asyncore.dgram import udp, unix
from pyasn1.codec.ber import decoder
from pysnmp.proto import api

# Activation du logger
handler = RotatingFileHandler('SNMPReceiver.log', maxBytes=10000000, backupCount=5)
handler.setFormatter(logging.Formatter('%(asctime)s : %(message)s'))
logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(message)s')
logger = logging.getLogger(__name__)
logger.addHandler(handler)

# Définition de la fonction PrintException
def PrintException(msg):
    print("*" * 30)
    print(msg)
    print("*" * 30)

def Launcher(Data):
    DataCSV = []
    Threads = []
    t = {}
    f = csv.writer(open("fichier_status.csv", "w", newline=''), delimiter = ';')
    for i in range(1, 6):
        Position = "ird" + str(i)
        Model = "type" + str(i)
        SatName = "SAT-" + str(i)
        if Data[Model] == 'DR5000':
            t[str(i)] = threading.Thread(target=DR5000state, args=(Position, SatName, Data, DataCSV))
            t[str(i)].start()
            Threads.append(t[str(i)])
        # elif Data[Model] == 'RX8200':
        #     t[str(i)] = threading.Thread(target=RX8200state, args=(Position, SatName, Data[Position], RX8200['SvcName'], RX8200['Snr'], RX8200['Margin'], DataCSV))
        #     t[str(i)].start()
        #     Threads.append(t[str(i)])
        # elif Data[Model] == 'TT1260':
        #     t[str(i)] = threading.Thread(target=TT1260state, args=(Position, SatName, Data[Position], TT1260['SvcName'], TT1260['Snr'], TT1260['Margin'], DataCSV))
        #     t[str(i)].start()
        #     Threads.append(t[str(i)])
        else:
            NoSat(Position, SatName, Data[Model], DataCSV)
    for t in Threads:
        try:
            t.join()
        except:
            logger.error("Thread already finished")     
    f.writerows(DataCSV)
    logger.info("Done")

# Fonction de récupération de l'état IRD
def IRDstate(Addr, Model, Data):
    logger.info("Sending new Query...")
    #
    #Faire un each pour chercher la bonne valeur dans Data
    #
    if Addr == Data["ird1"]:
    ird = 'ird ' + str(Addr[2:])
    sat = 'Sat ' + str(Addr[2:])
    d = []
    if Model == 'DR5000':
        Info = {'Position':ird,
            'Name':sat,
            'Addr':Addr,
            'Model':"Ateme DR5000",
            'SvcName':SNMPget(Addr, Data['DR5000SvcName']),
            'Snr':int(SNMPget(Addr, Data['DR5000Snr']))/10,
            'Margin':int(SNMPget(Addr, Data['DR5000Margin']))/10,
            }
    for key in Info:
        d.append(Info[key])
    f = csv.reader(open("fichier_status.csv"), delimiter=';')
    lines = [l for l in f]

#
# Réécrire CSV !
#
    
    # elif Model == 'TT1260':

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

def DR5000state(Position, SatName, Data, DataCSV):
    Info = {'Position':Position,
            'Name':SatName,
            'Addr':Data[Position],
            'Model':"Ateme DR5000",
            'SvcName':SNMPget(Data[Position], Data['DR5000SvcName']),
            'Snr':SNMPget(Data[Position], Data['DR5000Snr']),
            'Margin':SNMPget(Data[Position], Data['DR5000Margin']),
            }
    d = []
    for key in Info:
        d.append(Info[key])
    logger.info(d)
    DataCSV.append(d)
    return DataCSV

# def RX8200state(Position, Name, Addr, SvcName, Snr, Margin, DataCSV):
#     Info = {'Position':Position,
#             'Name':Name,
#             'Addr':Addr,
#             'Model':"Ericsson RX8200",
#             'SvcName':SNMPget(Addr, SvcName),
#             'Snr':SNMPget(Addr, Snr)[:4],
#             'Margin':SNMPget(Addr, Margin)[2:6],
#             }
#     if Info['SvcName'][:7] == "No Such":
#         Info['SvcName'] = ''
#     d = []
#     for key in Info:
#         d.append(Info[key])
#     print(d)
#     DataCSV.append(d)
#     return DataCSV

# def TT1260state(Position, Name, Addr, SvcName, Snr, Margin, DataCSV):
#     Info = {'Position':Position,
#             'Name':Name,
#             'Addr':Addr,
#             'Model':"Tandberg TT1260",
#             'SvcName':SNMPget(Addr, SvcName),
#             'Snr':int(SNMPget(Addr, Snr))/100,
#             'Margin':int(SNMPget(Addr, Margin))/100,
#             }
#     if Info['Margin'] == 100.0:
#         Info['Margin'] = 0.0
#     d = []
#     for key in Info:
#         d.append(Info[key])
#     print(d)
#     DataCSV.append(d)
#     return DataCSV

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
    logger.info(d)
    DataCSV.append(d)
    return DataCSV

