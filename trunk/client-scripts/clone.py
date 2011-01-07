#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import re
import subprocess
import shutil
import sys
import libvirt
import socket
import string
import random
import pickle
import time
from xml.dom.minidom import parseString

class VHost:
	a = "a"

def debugOut(output,debugLevel):
	if debug >= debugLevel:
		print 'Debug [' + str(debugLevel) + ']:' + output

def randomName(vmName):
	length = len(vmName) + 6
	chars = string.letters+string.digits
	name = vmName
	while(len(name) < int(length)):
		name += random.choice(chars)
	return name

def execute(command):
	s = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = s.communicate()
	debugOut(stderr, 1)
	debugOut(stdout, 3)
	return stdout

def prepareXml(xmlDescription):
	hList = []
	description = parseString(xmlDescription)
	hardDisks = description.getElementsByTagName("disk")
	for i in range(0,len(hardDisks)):
		if hardDisks[i].getAttribute("device") == "disk":
			hardDisk = hardDisks[i].getElementsByTagName("source")[0].getAttribute("file")
			newHddPath = config.imageDir + "/" + newVmName + "-" + os.path.basename(hardDisk)
			cloneHdd(hardDisk, newHddPath)
			hardDisks[i].getElementsByTagName("source")[0].setAttribute("file", newHddPath)
	description.getElementsByTagName("name")[0].childNodes[0].data = newVmName
	
	for removeTag in description.getElementsByTagName("mac"):
		removeTag.parentNode.removeChild(removeTag)
	
	for removeTag in description.getElementsByTagName("uuid"):
		removeTag.parentNode.removeChild(removeTag)
	return description

def cloneVm(vmName, vType):
	if vType == "xen":
		conn = libvirt.open('xen://')
	else:
		conn = libvirt.open('qemu:///system')
	vm = conn.lookupByName(vmName)

	#xmlFile = open(torrentDir + '/' + vmName + '.xml', 'w')
	#xmlFile = open('/tmp/' + vmName + '.xml', 'w')
	newVmXml = prepareXml(vm.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE))
	#save a temp copy, perhaps for debugging :)
	#newVmXml.writexml(xmlFile)
	#define the new VM in libvirt
	vm = conn.defineXML(newVmXml.toxml())
	if autostart:
		vm.create()
	#xmlFile.close()

def cloneHdd(hdd, newHddPath):
	cloneMethod = { 
		'kvm'  : cloneHddKvm,
		'xen'  : cloneHddXen,
		'qemu' : cloneHddQemu}
	cloneMethod[config.vType](hdd, newHddPath)

def cloneHddQemu(hdd, newHddPath):
	command = ['qemu-img', 'info' , hdd]
	baseFormat = re.search('file format: (?P<format>[\S]*)', execute(command)).groupdict()['format']
	command = ['qemu-img', 'create', '-f', 'qcow2', '-b', hdd, '-o','backing_fmt=' + baseFormat, newHddPath]
	execute(command)

def cloneHddKvm(hdd, newHddPath):
	command = ['kvm-img', 'info' , hdd]
	baseFormat = re.search('file format: (?P<format>[\S]*)', execute(command)).groupdict()['format']
	command = ['kvm-img', 'create', '-f', 'qcow2', '-b', hdd, '-o','backing_fmt=' + baseFormat, newHddPath]
	execute(command)

def cloneHddXen(hdd, newHddPath):
	command = ['vhd-util', 'snapshot', '-n', newHddPath, '-p', hdd]
	execute(command)

if len(sys.argv) == 5:
	startTimeSkript = time.time()
	configPickle = open(os.path.expanduser('~/.config/whoami.pickle'), 'r')
	config = pickle.load(configPickle)
	configPickle.close()

	vmName = sys.argv[1]
	cloneCount = int(sys.argv[2])
	if sys.argv[3] == 'y' or sys.argv[3] == 'Y' or sys.argv[3] == 'j' or sys.argv[3] == 'J':
		autostart = 'y'
	else:
		autostart = None
	debug = int(sys.argv[4])

	for i in range (0,cloneCount):
		startTimeClone = time.time()
		newVmName = randomName(vmName)
		cloneVm(vmName, config.vType)
		print 'Klon ' + str(i) + ': ' + newVmName
		debugOut('Time needed: ' + str(time.time() - startTimeClone) , 1)
	debugOut('Overall Time needed: ' + str(time.time() - startTimeSkript), 1)
