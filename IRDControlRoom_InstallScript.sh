#!/bin/bash

echo "*** Déplacement du dossier dans /usr/local/bin ***"
cd /home/pi/
sudo mv -f IRDControlRoom/ /usr/local/bin/

echo "*** Ajout des droits d'exécution ***"
cd /usr/local/bin/IRDControlRoom/SNMPReceiver/
sudo chmod +x core.py
sudo chmod +x Libraries.py

echo "*** Activation du script au reboot via sudo crontab ***"
echo -e "$(crontab -u pi -l)\n@reboot sudo /usr/bin/python3 /usr/local/bin/IRDControlRoom/SNMPReceiver/core.py -c '/usr/local/bin/IRDControlRoom/SNMPReceiver/config.ini'" | crontab -u pi -

echo "*** Installation des packages Python3 pré-requis ***"
sudo pip3 install configparser
sudo pip3 install argparse
sudo pip3 install pysnmp

echo "*** Installation terminée, reboot dans 30 secondes. Pour annuler, pressez 'Ctrl + C' ***"
sleep 30
sudo reboot
