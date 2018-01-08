#!/bin/bash

echo "*** Déplacement du dossier dans /usr/local/bin ***"
cd /home/nodal/
sudo mv -f IRDControlRoom/ /usr/local/bin/

echo "*** Ajout des droits d'exécution ***"
cd /usr/local/bin/IRDControlRoom/SNMPReceiver/
sudo chmod +x core.py
sudo chmod +x libraries.py

echo "*** Activation du script au reboot via sudo crontab ***"
echo -e "$(crontab -u root -l)\n@reboot /usr/bin/python3 /usr/local/bin/IRDControlRoom/SNMPReceiver/core.py | crontab -u root -l

echo "*** Installation des packages Python3 pré-requis ***"
sudo pip3 install configparser
sudo pip3 install pysnmp

echo "*** Installation terminée, reboot dans 30 secondes. Pour annuler, pressez 'Ctrl + C' ***"
sleep 30
sudo reboot
