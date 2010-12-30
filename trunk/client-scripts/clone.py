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
from xml.dom.minidom import parseString

class VHost:
	a = "a"

def randomName(vmName):
	length = len(vmName) + 6
	chars = string.letters+string.digits
	name = vmName
	while(len(name) < int(length)):
		name += random.choice(chars)
	#TODO? Sicherheitsabfrage
	return name

def execute(command):
	s = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = s.communicate()
	if debug > 0:
		print stdout
		print stderr
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
	#remove uuid and mac address TODO mehrere Macs löschen
	removeTag = description.getElementsByTagName("mac")[0]
	removeTag.parentNode.removeChild(removeTag)
	removeTag = description.getElementsByTagName("uuid")[0]
	removeTag.parentNode.removeChild(removeTag)
	return description

def cloneVm(vmName, vType):
	if vType == "xen":
		conn = libvirt.open('xen://')
	else:
		conn = libvirt.open('qemu:///system')
	vm = conn.lookupByName(vmName)

	#xmlFile = open(torrentDir + '/' + vmName + '.xml', 'w')
	xmlFile = open('/tmp/' + vmName + '.xml', 'w')
	newVmXml = prepareXml(vm.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE))
	#save a temp copy, perhaps for debugging :)
	newVmXml.writexml(xmlFile)
	#define the new VM in libvirt
	conn.defineXML(newVmXml.toxml())
	xmlFile.close()

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
	command = ['vhd-util', 'info' , hdd]
	baseFormat = re.search('file format: (?P<format>[\S]*)', execute(command)).groupdict()['format']
	command = ['qemu-img', 'create', '-f', 'qcow2', '-b', hdd, '-o','backing_fmt=' + baseFormat, newHddPath]
	execute(command)

vmName = sys.argv[1]
configPickle = open(os.path.expanduser('~/.config/whoami.pickle'), 'r')
config = pickle.load(configPickle)
configPickle.close()
debug = 1 
newVmName = randomName(vmName)
cloneVm(vmName, config.vType)
