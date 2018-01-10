#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Developeurs : VBNIN + CKAR - IPEchanges.
Script de relevé des niveaux de réceptions des IRD nodal
"""

import logging
import sys
import csv
import time
import re
from logging.handlers import RotatingFileHandler
from pysnmp.hlapi import *
from pysnmp.carrier.asyncore.dgram import udp, unix
from pyasn1.codec.ber import decoder
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto import api

# Activation du logger
LogPath = 'SNMPReceiver.log' if sys.platform.lower() == 'win32' else '/var/log/SNMPReceiver.log'
handler = RotatingFileHandler(LogPath, maxBytes=10000000, backupCount=5)
handler.setFormatter(logging.Formatter('%(asctime)s : %(message)s'))
logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(message)s')
logger = logging.getLogger(__name__)
logger.addHandler(handler)

# # Fonction de lancement des Process et écriture du CSV
# def CheckLoop(DataDict):
#     while True:
#         DataCSV = []
#         for i in range(1, 36):
#             DataCSV.append(IRDInfo(i, DataDict))
#         with open(DataDict['CSV'], "w", newline='') as f:
#             writer = csv.writer(f, delimiter=';')
#             writer.writerows(DataCSV)
#         time.sleep(0.02)
#         logger.info("Fichier CSV mis à jour par InitCSV.")

# # Fonction de collection des informations par SNMP
# def IRDInfo(i, Data):
#     Position = "ird" + str(i)
#     Model = "model" + str(i)
#     SatName = "SAT-" + str(i)
#     logger.debug("Collecte des Infos pour " + SatName)
#     Info = [Position, SatName, Data[Position], Data[Model]]
#     if Data[Model] == "DR5000":
#         Snmp = SNMPget(Data[Position], 0, Data['DR5000SvcName'], Data['DR5000Snr'], Data['DR5000Margin'])
#         Info = Info + Snmp
#         Info[5] = int(Info[5])/10
#         Info[6] = int(Info[6])/10
#     elif Data[Model] == "RX8200":
#         Snmp = SNMPget(Data[Position], 1, Data['RX8200SvcName'], Data['RX8200Snr'], Data['RX8200Margin'])
#         Info = Info + Snmp
#         if Info[4][:7] == "No Such":
#             Info[4:6] = ['', 0, 0]
#             Info.remove(Info[7])
#         else:
#             try:
#                 Info[5:6] = [Info[5][:4], Info[6][2:6]]
#             except:
#                 Info[5:6] = [0, 0]
#                 Info.remove(Info[7])
#     elif Data[Model] == "TT1260":
#         Snmp = SNMPget(Data[Position], 0, Data['TT1260SvcName'], Data['TT1260Snr'], Data['TT1260Margin'])
#         Info = Info + Snmp
#         Info[5] = int(Info[5])/100
#         Info[6] = int(Info[6])/100
#         if Info[6] == 100.0:
#             Info[6] = 0.0
#     else:
#         Info = Info + ['N/A', 'N/A', 0]
#     return Info

# Définition de la commande 'SNMP Get'
def SNMPget(IPAddr, SNMPv, OID1, OID2, OID3):
    try:
        snmp = []
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                CommunityData('private', mpModel=SNMPv),
                UdpTransportTarget((IPAddr, 161)),
                ContextData(),
                ObjectType(ObjectIdentity(OID1)),
                # ObjectType(ObjectIdentity(OID2)),
                ObjectType(ObjectIdentity(OID3))))
        if errorIndication or errorStatus:
            logger.error("No SNMP response before timeout")
            snmp = ['', 0, 0]
            return snmp
        else:
            for varBind in varBinds:
                m = re.search('(.*)\ =\ (.*)', varBind.prettyPrint())
                state = m.group(2)
                snmp.append(state)
            print(snmp)
            return snmp
    except:
        logger.error("Impossible de récupérer les infos SNMP...")
        snmp = ['', 0, 0]
        return snmp

def SNMPbulk(IPAddr, SNMPv, OID1, OID2, OID3):
    snmp = []
    g = bulkCmd(SnmpEngine(),
                CommunityData('private', mpModel=SNMPv),
                UdpTransportTarget((IPAddr, 161)),
                ContextData(),
                0, 25,
                ObjectType(ObjectIdentity(OID1)))
    errorIndication, errorStatus, errorIndex, varBinds = next(g)
    for varBind in varBinds:
        m = re.search('(.*)\ =\ (.*)', varBind.prettyPrint())
        state = m.group(2)
        snmp.append(state)
    errorIndication, errorStatus, errorIndex, varBinds = g.send( [ ObjectType(ObjectIdentity(OID2)) ] )
    for varBind in varBinds:
        m = re.search('(.*)\ =\ (.*)', varBind.prettyPrint())
        state = m.group(2)
        snmp.append(state)
    errorIndication, errorStatus, errorIndex, varBinds = g.send( [ ObjectType(ObjectIdentity(OID3)) ] )
    for varBind in varBinds:
        m = re.search('(.*)\ =\ (.*)', varBind.prettyPrint())
        state = m.group(2)
        snmp.append(state)
    print(snmp)

def SNMPbulkv2(IPAddr, SNMPv, OID1):
    snmp = []
    cmdGen = cmdgen.CommandGenerator()
    errorIndication, errorStatus, errorIndex, varBinds = cmdGen.bulkCmd(
        cmdgen.CommunityData('private', mpModel=SNMPv),
        cmdgen.UdpTransportTarget((IPAddr, 161)),
        0, 50,
        OID1
    )
    if errorIndication or errorStatus:
        logger.error("No SNMP response before timeout")
        snmp = ['', 0, 0]
        return snmp
    else:
        logger.info(varBinds)
        for varBind in varBinds:
            for name, val in varBind:
            # m = re.search('(.*)\ =\ (.*)', varBind.prettyPrint())
            # state = m.group(2)
                print('%s = %s' % (name.prettyPrint(), val.prettyPrint()))



start = time.time()
for i in range(11):
    # SNMPget('10.75.216.4', 1, '.1.3.6.1.4.1.27338.5.5.3.3.2.0', '.1.3.6.1.4.1.27338.5.5.3.3.3.0', '.1.3.6.1.4.1.27338.5.5.1.5.1.1.9.1')
    SNMPbulkv2('10.75.216.4', 1, '.1.3.6.1.4.1.27338.5.5')
end = time.time() - start
logger.info('temps de traitement : ' + str(end))