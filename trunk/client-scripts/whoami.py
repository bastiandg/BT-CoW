#!/usr/bin/python
# -*- coding: utf-8 -*-

import pickle
import os
import subprocess
import sys
import re

from socket import gethostname; 

class VHost:
	def __init__(self, ip, name, vType, imageDir, downloadDir):
		self.name = name
		self.ip = ip
		self.vType = vType
		self.imageDir = imageDir
		self.downloadDir = downloadDir

def execute(command):
	s = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
	#stdout, stderr = s.communicate()
	#if debug > 0:
	#print stdout
	#print stderr
	return s.communicate()

name = gethostname()
ip = sys.argv[1]
command = ['find', "/boot/","-name","xen*.gz"]
stdout = execute(command)

if stdout and re.match('[\S]*xen[\S]*',os.uname()[2]):
	vType = "xen"
else:
	vType = "kvm"

downloadDir = sys.argv[2]
imageDir = sys.argv[3]

obj = VHost(ip, name, vType, imageDir, downloadDir)
if not os.path.exists(os.path.expanduser('~/.config')):
	os.mkdir(os.path.expanduser('~/.config'))
cowpickle = open(os.path.expanduser('~/.config/whoami.pickle'), 'w')
pickle.dump(obj, cowpickle)
cowpickle.close()
