#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import re
import subprocess
import shutil
import sys
import libvirt
import socket
from xml.dom.minidom import parseString

configLines = open(os.path.expanduser('/etc/xen/xend-config.sxp'), 'r').readlines()

def httpNo():
	for line in configLines:
		if re.match('[\s]*\(xend-http-server no\)[\s]*',line):
			return
	
	config = open('/etc/xen/xend-config.sxp','a')
	config.write('\n(xend-http-server no)\n')
	config.close()

def unixYes():
	for line in configLines:
		if re.match('[\s]*\(xend-unix-server yes\)[\s]*',line):
			return

	config = open('/etc/xen/xend-config.sxp','a')
	config.write('\n(xend-unix-server yes)\n')
	config.close()

httpNo()
unixYes()
