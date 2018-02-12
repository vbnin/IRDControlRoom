#!/bin/bash

echo "*** Ajout des droits d'exécution ***"
cd /usr/local/bin/IRDControlRoom/SNMPReceiver2/
chmod +x core.py
chmod +x Libraries.py

echo "*** Activation du script au reboot via sudo crontab ***"
#write out current crontab
crontab -l > mycron
#echo new cron into cron file
echo "@reboot /usr/bin/python3 /usr/local/bin/IRDControlRoom/SNMPReceiver2/core.py 2&>1 /var/log/crontab.log" >> mycron
#install new cron file
crontab mycron
rm mycron

echo "*** Installation terminée, reboot dans 30 secondes. Pour annuler, pressez 'Ctrl + C' ***"
sleep 30
reboot
