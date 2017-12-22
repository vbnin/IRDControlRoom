#!/bin/bash

echo "*** Déplacement du dossier dans /usr/local/bin ***"
cd /home/pi/
sudo mv -f IRDControlRoom/ /usr/local/bin/

echo "*** Ajout des droits d'exécution ***"
cd /usr/local/bin/IRDControlRoom/SNMPReceiver/
sudo chmod +x core.py
sudo chmod +x Libraries.py
sudo chmod +x CallBack.py
sudo chmod +x Launcher.sh

echo "*** Activation du script au reboot via sudo crontab ***"
echo -e "$(crontab -u pi -l)\n@reboot sudo /usr/local/bin/IRDControlRoom/SNMPReceiver/Launcher.sh | crontab -u pi -

echo "*** Installation des packages Python3 pré-requis ***"
sudo pip3 install configparser
sudo pip3 install pysnmp

echo "*** Installation terminée, reboot dans 30 secondes. Pour annuler, pressez 'Ctrl + C' ***"
sleep 30
sudo reboot
