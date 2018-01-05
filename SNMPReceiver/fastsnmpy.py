#!/usr/bin/env python
# -*- coding: utf-8 -*-

import netsnmp
from fastsnmpy import *



hosts = ['10.191.5.1', '10.191.2.2', '10.191.5.3', '10.191.2.4']
oids = ['.1.3.6.1.4.1.27338.5.5.3.3.2.0', '.1.3.6.1.4.1.27338.5.5.3.3.3.0', '.1.3.6.1.4.1.27338.5.5.1.5.1.1.9.1']
newsession = SnmpSession ( targets = hosts, oidlist = oids, community='private' )
results = newsession.snmpbulkwalk(workers=3)
print(results)