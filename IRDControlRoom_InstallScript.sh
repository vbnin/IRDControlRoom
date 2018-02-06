#!/bin/bash

echo "*** Déplacement du dossier dans /usr/local/bin ***"
DIRECTORY=$(cd `dirname $0` && pwd)
sudo mv -f $DIRECTORY /usr/local/bin/

echo "*** Ajout des droits d'exécution ***"
cd /usr/local/bin/IRDControlRoom/SNMPReceiver/
sudo chmod +x core.py
sudo chmod +x libraries.py

echo "*** Activation du script au reboot via sudo crontab ***"
<<<<<<< HEAD
echo -e "$(crontab -u root -l)\n@reboot /usr/bin/python3 /usr/local/bin/IRDControlRoom/SNMPReceiver/core.py 2&>1 /var/log/crontab.log | crontab -u root -l"
=======
echo -e "$(crontab -u root -e)\n@reboot /usr/bin/python3 /usr/local/bin/IRDControlRoom/SNMPReceiver/core.py 2&>1 /var/log/crontab.log | crontab -u root -l"
>>>>>>> 9c41a1838e68aac6126e5a7ca555ca95f94e9484

echo "*** Installation des packages Python3 requis ***"
sudo apt-get install python3-pip
sudo pip3 install configparser
sudo pip3 install pysnmp

echo "*** Installation terminée, reboot dans 30 secondes. Pour annuler, pressez 'Ctrl + C' ***"
sleep 30
sudo reboot
