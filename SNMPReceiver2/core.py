#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Developeurs : VBNIN + CKAR - IPEchanges.
Script de relevé des niveaux de réceptions des IRD nodal en DVB-S2 ou IP.
Ce script créé un fichier CSV alimentant une page web puis envoi ses relevés en TCP vers une Mosaique Miranda Kaleido
Release v2.0 avec librairie EasySNMP - Attention, non compatible Windows. Voir la doc de easysnmp pour son installation sous Linux
"""

title = 'SNMPReceiver2'
version = 'Version 2.4 - 09/01/2019'
author = 'IP-Echanges'

#Import des librairies internes
import logging
import sys
import csv
import os
import re
import time
import socket
from logging.handlers import RotatingFileHandler

#Librairie externe à télécharger
import configparser 

# Activation du logger principal
try:
    LogPath = 'SNMPReceiver.log' if sys.platform.lower() == 'win32' else '/var/log/SNMPReceiver.log'
    handler = RotatingFileHandler(LogPath, maxBytes=10000000, backupCount=5, encoding="utf-8")
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s : %(message)s'))
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s : %(message)s')
    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    logger.info("Initialisation du fichier de log dans " + LogPath)
except:
    sys.exit("Impossible d'initialiser le fichier de logs.")

class LoggerWriter():
    def __init__(self, writer):
        self._writer = writer
        self._msg = ''

    def write(self, message):
        self._msg = self._msg + message
        while '\n' in self._msg:
            pos = self._msg.find('\n')
            self._writer(self._msg[:pos])
            self._msg = self._msg[pos+1:]

    def flush(self):
        if self._msg != '':
            self._writer(self._msg)
            self._msg = ''

#Librairies externe à télécharger
if sys.platform.lower() != 'win32':
    from easysnmp import Session
else:
    logger.warning("** Warning ** La librairie Easysnmp n'est pas compatible Windows")

def parse_config(config_file):
    ''' Cette fonction analyse un fichier ini et rempli un dictionnaire '''
    try:
        config = configparser.ConfigParser()
        config.read(config_file)
        conf = {}
        for item in ['GENERAL', 'MOSAIQUE', 'DR5000', 'DR8400', 'RX8200', 'TT1260', 'RX1290', 'IRD']: #List of the main sections in the config file
            data = {}
            data[item] = dict(config.items(item))
            for key, value in data[item].items():
                if item == 'IRD':
                    ird_key = key
                    if ird_key[0] == '0':
                        ird_key = key[-1]   # We need to strip the zero number in ird name or the web page won't work
                    data['IRD'][key] = {'ird_ip':value, 'ird_name':'ird{}'.format(ird_key), 'sat_name':'SAT-{}'.format(key), 'model':'inconnu'}
                elif value.isdigit() is True:
                    data[item][key] = int(value)    # Transform all digit values in integers
                elif ', ' in value:
                    data[item][key] = value.split(', ')     # Transform all values with coma in lists
            conf = {**conf, **data}
        logger.debug('***\nDictionnaire conf mis à jour par parse_config : \n{}\n ***'.format(conf))
        return conf
    except Exception as e:
        logger.error("*** Erreur *** Impossible de parser le fichier de config : {}".format(e), exc_info=True)
        sys.exit("*** Erreur *** Impossible de parser le fichier de config : {}".format(e))

def is_server_alive(conf):
    ''' Fonction de vérification de l'accès réseau à l'équipement distant '''
    try:
        # connect to the host -- tells us if the host is actually reachable
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(60)
        sock.connect((conf['MOSAIQUE']['ip_address'], conf['MOSAIQUE']['tcp_port']))
        logger.info("Accès à la Mosaique Miranda OK")
        return True
    except Exception as e:
        logger.error("** Erreur ** Serveur distant {} injoignable ! - {}".format(conf['MOSAIQUE']['ip_address'], e))
        return False

def list_ird_model(conf):
    ''' Cette fonction détermine le modèle de chaque IRD '''
    for number, detail in sorted(conf['IRD'].items()):
        response = snmp_get(detail['ird_ip'], conf['GENERAL']['oid_get_ird_model'], snmp_version=1)
        if response is None:
            logger.error("** Erreur ** Impossible de déterminer le modèle de : {} ({}) !!".format(detail['ird_name'], detail['ird_ip']))
            detail['model'] = 'ERREUR SNMP'
        else:
            match = False
            for item in conf['GENERAL']['supported_models']:
                if re.search(item[:3], response, re.IGNORECASE) or re.search(r'armv7', response, re.IGNORECASE):
                    detail['model'] = item
                    logger.debug("{} est un modèle {}".format(detail['ird_name'], item))
                    match = True
                    break
                else:
                    match = False
            if match is False:
                logger.warning("** Warning ** Modèle d'IRD inconnu pour {} ({})".format(detail['ird_name'], detail['ird_ip']))
    logger.debug('***\nDictionnaire conf mis à jour par list_ird_model : \n{}\n ***'.format(conf))
    return conf

def loop(conf):
    '''Fonction principal lancant une boucle de vérification de chaque IRD puis mettant à jour la mosaique et le fichier CSV'''
    while True:
        csv_data = [['IRD Position', 'IRD Name', 'IP Adress', 'Model', 'Lock Status', 'Decoded Service', 'SNR or IP bitrate', 'Margin or IP bitrate']] # Creating the CSV header
        csv_file = conf['GENERAL']['csv_file'] if sys.platform.lower() != 'win32' else conf['GENERAL']['csv_file_win']  # Change the CSV file location depending on the OS used
        for number, detail in sorted(conf['IRD'].items()):
            try:
                csv_data.append(get_ird_info(number, detail, conf)) # CSV list is filled with infos for each equipment
            except Exception as e:
                logger.error("*** Erreur *** Impossible de récupérer les infos de {} - {}".format(detail['ird_name'], e), exc_info=True)
        update_mosaique(conf, csv_data)     # Update the Miranda Equipment
        update_csv(csv_file, csv_data)      # Update the CSV file
        logger.info("Mise a jour page web et mosaique terminée")
        time.sleep(conf['GENERAL']['refresh_rate'])

def get_ird_info(number, ird_info, conf):
    '''Fonction de collection des informations d'un IRD donné'''
    logger.debug("Collecte des infos pour " + ird_info['ird_name'])
    basic_stats = [ird_info['ird_name'], ird_info['sat_name'], ird_info['ird_ip'], ird_info['model']]
    if ird_info['model'] in conf['GENERAL']['supported_models']:
        oid_list = []
        for oid_name, oid_code in sorted(conf[ird_info['model']].items()):
            oid_list.append(oid_code)
        if ird_info['model'] in ['RX1290', 'TT1260']:
            snmp_version = 1
        else:
            snmp_version = 2
        response = snmp_get(ird_info['ird_ip'], oid_list, snmp_version=snmp_version)
        if response is not None:
            logger.debug('Réponse de {} : {}'.format(ird_info['ird_name'], response))
            if ird_info['model'] == "DR5000" and response[0] == 1.0:
                if response[-1] == 1.0:
                    response[0] = 'Locked (Mode IP)'
                    response[2] = response[4] / 1000
                    response[3] = response[4] / 1000
                else:
                    response[0] = 'Locked'
                    response[2] = response[2] / 10
                    response[3] = response[3] / 10
                if response[5] > 1:
                    logger.debug('Multistream, nombre de programmes : {}'.format(response[5]))
                    for i in range(1, int(response[5]) + 1):
                        service_index = conf['DR5000']['06_oid_get_service_select'][:-1] + '{}'.format(i)
                        service = snmp_get(ird_info['ird_ip'], service_index, snmp_version=2)
                        if service == 1.0:
                            service_name = conf['DR5000']['01_oid_get_servicename'][:-1] + '{}'.format(i)
                            response[1] = snmp_get(ird_info['ird_ip'], service_name, snmp_version=2)
                            logger.debug('Programme décodé numéro {}'.format(i))
                            break
                del response[4:]
            elif ird_info['model'] == "TT1260" or ird_info['model'] == "RX1290" and response[0] == 2.0:
                response[0] = 'Locked'
                response[2] = response[2] / 100
                response[3] = response[3] / 100
            elif ird_info['model'] == "RX8200" and response[0] == 'LOCKED':
                response[0] = 'Locked'
                try:
                    response[2] = float(response[2][:4])
                    response[3] = float(response[3][2:6])
                except:
                    pass
            else:
                response = ['Unlocked', 'Unlocked', 0.0, 0.0]
        else:
            response = ['Unlocked', 'ERREUR SNMP', 0.0, 0.0]
    elif ird_info['model'] == 'ERREUR SNMP':
        response = ['Unlocked', 'ERREUR SNMP', 0.0, 0.0]
    else:
        response = ['Unlocked', 'Non supporté', 0.0, 0.0]
    stats = basic_stats + response
    return stats

def update_mosaique(conf, csv_data):
    '''Définition de la fonction de connexion TCP à la mosaique puis transfert des données'''
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.5)
    try :
        s.connect((conf['MOSAIQUE']['ip_address'], conf['MOSAIQUE']['tcp_port']))
        s.settimeout(None)
    except Exception as e:
        logger.error("Impossible de joindre la mosaique ({})  - {}".format(conf['MOSAIQUE']['ip_address'], e))
        return
    OpenCmd = "<openID>{}</openID>\n".format(conf['MOSAIQUE']['room'])
    s.send(OpenCmd.encode())
    Feedback = s.recv(conf['MOSAIQUE']['buffersize'])
    if Feedback[:6].decode() != "<ack/>":
        logger.error("Mauvaise réponse reçue de la Mosaique ! - {}".format(Feedback.decode()))
        return
    else:
        logger.debug("Connexion établie avec la mosaique Miranda, upload des informations...") 
        for info in csv_data:
            sat_name_margin = info[1].replace('-', '') + "_MARGIN"
            status = info[4]
            margin_or_bitrate = info[7]
            try:
                if status == 'Unlocked':
                    SendCmd = '<setKStatusMessage>set id="{}" status="ERROR" message="Unlocked"</setKStatusMessage>\n'.format(sat_name_margin)
                elif status == 'Locked (Mode IP)' and margin_or_bitrate >= 4.0:
                    SendCmd = '<setKStatusMessage>set id="{}" status="OK" message="{} Mb"</setKStatusMessage>\n'.format(sat_name_margin, margin_or_bitrate)
                elif status == 'Locked (Mode IP)' and margin_or_bitrate < 4.0:
                    SendCmd = '<setKStatusMessage>set id="{}" status="WARNING" message="{} Mb"</setKStatusMessage>\n'.format(sat_name_margin, margin_or_bitrate)
                elif margin_or_bitrate < 3.0:
                    SendCmd = '<setKStatusMessage>set id="{}" status="WARNING" message="{} dB"</setKStatusMessage>\n'.format(sat_name_margin, margin_or_bitrate)
                elif margin_or_bitrate >= 3.0 and margin_or_bitrate <= 7.0:
                    SendCmd = '<setKStatusMessage>set id="{}" status="OK" message="{} dB"</setKStatusMessage>\n'.format(sat_name_margin, margin_or_bitrate)
                elif margin_or_bitrate > 7.0:
                    SendCmd = '<setKStatusMessage>set id="{}" status="MAJOR" message="{} dB"</setKStatusMessage>\n'.format(sat_name_margin, margin_or_bitrate)
                else:
                    raise Exception
            except Exception:
                SendCmd = '<setKStatusMessage>set id="{}" status="ERROR" message="Erreur"</setKStatusMessage>\n'.format(sat_name_margin)
            s.send(SendCmd.encode())
        s.send("<closeID/>\n".encode())
        s.close()
        logger.debug("Affichage Mosaique mis à jour par TCPget.")

def update_csv(csv_file, csv_data):
    '''Fonction de mise à jour du fichier CSV partagé avec le serveur Web'''
    csv_data.append(["ird888", "LastUpdate", time.strftime("%d/%m/%Y, %H:%M:%S")])      #Ajout d'un timestamp à la fin du fichier CSV
    try:
        with open(csv_file, "w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerows(csv_data)
        logger.debug("Fichier CSV mis à jour")
    except Exception as e:
        logger.error("Impossible de mettre à jour le fichier CSV - {}".format(e), exc_info=True)        

def snmp_get(ip_address, oid, snmp_version=1, community='private'):
    '''Commande SNMP permettant de récupérer les informations nécessaires au script
    Cette fonction peut accepter un OID unique ou une liste d'OIDs'''
    try:
        session = Session(hostname=ip_address, community=community, version=snmp_version, timeout=2)
        if type(oid) == str:
            response = re.search(r'(value=)\'(.*)\'\ (.*)', str(session.get(oid)))
            oid_result = response.group(2)
            if oid_result.isdigit() is True:
                oid_result = float(oid_result)
        elif type(oid) == list:
            oid_result = []
            for item in oid:
                response = re.search(r'(value=)\'(.*)\'\ (.*)', str(session.get(item)))
                if response.group(2).isdigit() is True:
                    response = float(response.group(2))
                else:
                    response = response.group(2)
                oid_result.append(response)
        else:
            raise Exception('Type de variable oid non reconnu : {}'.format(type(oid)))
        return oid_result
    except Exception as e:
        logger.error('** Erreur ** Echec de la requete SNMP de {} - {}'.format(ip_address, e), exc_info=True)
        return None


if __name__ == '__main__':
    logger.info("--- This is {} in version {} by {} ---".format(title, version, author))

    sys.stdout = LoggerWriter(logger.debug)
    sys.stderr = LoggerWriter(logger.error)

    config_file = os.path.join(os.path.dirname(__file__), r'config.ini')
    logger.info("Lecture du fichier config : {}".format(config_file))
    conf = parse_config(config_file)

    logger.info("Vérification des services réseaux...")
    i = 1
    total = 3
    while is_server_alive(conf) is False:
        logger.info("Nouvel essai {} sur {}...".format(i, total))
        time.sleep(3)
        i += 1
        if i > total + 1:
            logger.warning("Equipement distant introuvable, la mosaique Miranda ne recevra pas les informations")
            break    

    logger.info("Récupération des modèles d'IRD en cours...")
    conf = list_ird_model(conf)

    logger.info("Initialisation de la boucle de vérification...")
    loop(conf)
