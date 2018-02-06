#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Developeurs : VBNIN + CKAR - IPEchanges.
Script de relevé des niveaux de réceptions des IRD nodal
"""
#Librairies externe à télécharger
from pysnmp.hlapi import *
from pysnmp.carrier.asyncore.dgram import udp, unix
from pyasn1.codec.ber import decoder
from pysnmp.proto import api
from pysnmp.entity.rfc3413.oneliner import cmdgen
from easysnmp import Session

#Import des librairies internes
import sys
import csv
import re
import socket
import logging
import time
from logging.handlers import RotatingFileHandler


# Activation du logger
LogPath = 'SNMPReceiver.log' if sys.platform.lower() == 'win32' else '/var/log/SNMPReceiver.log'
handler = RotatingFileHandler(LogPath, maxBytes=10000000, backupCount=5)
handler.setFormatter(logging.Formatter('%(asctime)s : %(message)s'))
logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(message)s')
logger = logging.getLogger(__name__)
logger.addHandler(handler)

OID1 = '.1.3.6.1.4.1.27338.5.5.3.3.2.0'
OID2 = '.1.3.6.1.4.1.27338.5.5.3.3.3.0'
OID3 = '.1.3.6.1.4.1.27338.5.5.1.5.1.1.9.1'
OID4 = '.1.3.6.1.4.1.27338.5.5.3.3'

# Définition de la commande 'SNMP Get'
def SNMPget(OID1, OID2, OID3):
    try:
        snmp = []
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                CommunityData('private'),
                UdpTransportTarget(('10.75.216.4', 161)),
                ContextData(),
                # 0, 10,
                ObjectType(ObjectIdentity(OID1)),
                ObjectType(ObjectIdentity(OID2)),
                ObjectType(ObjectIdentity(OID3))))
        if errorIndication or errorStatus:
            logger.error("No SNMP response before timeout")
            snmp = ['Erreur : SNMP timeout', 0.0, 0.0]
            return snmp
        else:
            for varBind in varBinds:
                print(' = '.join([x.prettyPrint() for x in varBind]))
            return snmp
    except:
        logger.error("Impossible de récupérer les infos SNMP...")
        snmp = ['Erreur : SNMP timeout', 0.0, 0.0]
        return snmp

def SNMPbulk(OID):
    for (errorIndication,
        errorStatus,
        errorIndex,
        varBinds) in bulkCmd(SnmpEngine(),
            CommunityData('public'),
            UdpTransportTarget(('10.75.216.4', 161)),
            ContextData(),
            0, 25,  # fetch up to 25 OIDs one-shot
            ObjectType(ObjectIdentity(OID))):
        if errorIndication or errorStatus:
            print(errorIndication or errorStatus)
            break
        else:
            for varBind in varBinds:
                # print(' = '.join([x.prettyPrint() for x in varBind]))
                if re.match(r'SNMPv2-SMI::enterprises.27338.5.5.3.3.4.0', varBind.prettyPrint()):
                    return
                else:
                    print(varBind.prettyPrint())

def EasySNMP(OID1, OID2, OID3):
    # Create an SNMP session to be used for all our requests
    session = Session(hostname='10.75.216.226', community='private', version=2)
    print(session.get(OID1))
    print(session.get(OID2))
    print(session.get(OID3))

# Test avec Librairie EasySNMP
start = time.time()
for i in range(0,10):
    EasySNMP(OID1, OID2, OID3)
stop = time.time()-start
logger.info(stop)

# # Test avec pysnmp en version Get
# start = time.time()
# for i in range(0,10):
#     SNMPget(OID1, OID2, OID3)
# stop = time.time()-start
# logger.info(stop)

# # Test avec pysnmp en version Bulk
# start = time.time()
# for i in range(0,10):
#     SNMPbulk(OID4)
# stop = time.time()-start
# logger.info(stop)


