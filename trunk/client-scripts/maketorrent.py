#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import re
import subprocess
import shutil
import sys
import libvirt
import socket
import pickle
from xml.dom.minidom import parseString

class VHost:
	a = "a"

def execute(command):
	s = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = s.communicate()
	if debug > 0:
		print stdout
		print stderr
	return stdout

def hddList(xmlDescription):
	hList = []
	description = parseString(xmlDescription)
	hardDisks = description.getElementsByTagName("disk")
	for i in range(0,len(hardDisks)):
		if hardDisks[i].getAttribute("device") == "disk":
			hardDisk = hardDisks[i].getElementsByTagName("source")[0].getAttribute("file")
			hList.append(hardDisk)
			"""hardDiskFile = hardDisks[i].getElementsByTagName("source")[0].getAttribute("file")
			hardDiskDev = hardDisks[i].getElementsByTagName("source")[0].getAttribute("dev")
			if hardDiskFile:
				hList.append(hardDiskFile)
			elif hardDiskDev:
				hList.append(hardDiskDev)"""
	return hList

def prepareXml(xmlDescription, vmName):
	hList = []
	description = parseString(xmlDescription)
	hardDisks = description.getElementsByTagName("disk")
	for i in range(0,len(hardDisks)):
		if hardDisks[i].getAttribute("device") == "disk":
			hardDisk = hardDisks[i].getElementsByTagName("source")[0].getAttribute("file")
			hardDisks[i].getElementsByTagName("source")[0].setAttribute("file", imageDir + "/" + vmName + "/" + os.path.basename(hardDisk))
	#remove uuid and mac address
	removeTag = description.getElementsByTagName("mac")[0]
	removeTag.parentNode.removeChild(removeTag)
	removeTag = description.getElementsByTagName("uuid")[0]
	removeTag.parentNode.removeChild(removeTag)
	return description

def makeTorrent(vmName):
	if vType == "xen":
		conn = libvirt.open('xen://')
	else:
		conn = libvirt.open('qemu:///system')
	vm = conn.lookupByName(vmName)
	
	torrentDir = downloadDir + '/' + vm.name()
	#make an empty torrent directory
	if os.path.exists(torrentDir):
		shutil.rmtree(torrentDir)
	os.makedirs(torrentDir)
	
	hdList = hddList(vm.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE))
	for hd in hdList:
		if not os.path.exists(hd):
			print 'Festplatte ' + hd + ' nicht vorhanden! \nVerteilen wird abgebrochen.'
			sys.exit(1)
	for hd in hdList:
		os.symlink(hd, torrentDir + '/' + os.path.basename(hd))
		print hd + "->" + torrentDir + '/' + os.path.basename(hd)
	xmlFile = open(torrentDir + '/' + vmName + '.xml', 'w')
	#xmlFile.write(modifedHddList(vm.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE), vmName))
	prepareXml(vm.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE), vmName).writexml(xmlFile)
	xmlFile.close()
	torrentFileName = config.downloadDir + "/" + vmName + '.torrent'
	if os.path.exists(torrentFileName):
		os.remove(torrentFileName)
	command = ['mktorrent', '-a', config.ip, '-o' , torrentFileName, torrentDir]
	execute(command)
	#add the announce server as a dht node
	torrentFile = open(torrentFileName, 'r')
	announce = '8:announce' + str(len(config.ip)) + ':' + config.ip
	addedDht = torrentFile.read().replace(announce , announce + '5:nodesll' + str(len(config.ip)) + ':' + config.ip + 'i6881eee')
	torrentFile.close()
	torrentFile = open(torrentFileName, 'w')
	torrentFile.write(addedDht)
	torrentFile.close()

if not os.path.exists(os.path.expanduser('~/.config/')):
	os.mkdir('~/.config/')
configPickle = open(os.path.expanduser('~/.config/whoami.pickle'), 'r')
config = pickle.load(configPickle)
configPickle.close()
vmName = sys.argv[1]
downloadDir = config.downloadDir
imageDir = config.imageDir
vType = config.vType
debug = 1
makeTorrent(vmName)

