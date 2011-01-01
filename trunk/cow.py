#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import re
import subprocess
import shutil
import sys
import libvirt
import socket
import time
from xml.dom.minidom import parseString

vHostType = {1: 'kvm', 2: 'xen'}
downloadDir = '/var/lib/download'
imageDir = '/var/lib/libvirt/images'
binDir = '/opt/cow'

def debugOut(output,debugLevel):
	if debug >= debugLevel:
		print 'Debug [' + str(debugLevel) + ']:' + output

def hostList():
	hostList = []
	hosts = open(os.path.expanduser('~/.cow/vhosts'), 'r').readlines()
	for i in range(0,len(hosts)):
		host = hosts[i].split('\t')
		if len(host) == 2: #ignore malformed rows
			hostList.append([len(hostList), host[0], host[1].replace('\n','')])
	return hostList

def vmList(hostName, vType):
	try:
		vmList = vmOffList(hostName, vType) + vmOnList(hostName, vType)
		return vmList
	except libvirt.libvirtError:
		print 'Host ' + hostName + '(' + vType + ') nicht erreichbar'

def vmOffList(hostName, vType):
	vOffList = []
	if vType == 'xen':
		conn = libvirt.open('xen://' + hostName + '/')
	else:
		conn = libvirt.open('qemu://' + hostName + '/system')
	
	for name in conn.listDefinedDomains():
		vOffList.append(conn.lookupByName(name))
	
	return vOffList

def vmOnList(hostName, vType):
	#TODO filter DOM0
	vOnList = []
	if vType == 'xen':
		conn = libvirt.open('xen://' + hostName + '/')
	else:
		conn = libvirt.open('qemu://' + hostName + '/system')
	
	for id in conn.listDomainsID():
		vOnList.append(conn.lookupByID(id))
	
	return vOnList


def vHostExists(hostName):
	hList = hostList()
	for host in hList:
		if host[1] == hostName:
			return True
	return False

def newVServer():
	print 'Geben Sie die IP des Hosts ein'
	ip = raw_input('HostIP: ')

	print 'Virtualisierungstechnik'
	print ' 1: KVM'
	print ' 2: XEN'
	choice = intInput('')
	
	command = ['./hostname.sh', ip]
	hostName = execute(command).replace('\n', '')
	
	if vHostExists(hostName):
		print 'der Host ' + hostName + 'schon registriert'
	else :
		#append the new host
		vhosts = open(os.path.expanduser('~/.cow/vhosts'), 'a')
		vhosts.write('\n' + hostName + '\t' + vHostType[choice])
		vhosts.close()

		command = ['rsync', '-r', 'client-scripts/' ,'root@' + hostName + ':' + binDir]
		execute(command)
		
		command = ['ssh', 'root@' + hostName, '/opt/cow/packageinstall.py "deluged deluge-console mktorrent libvirt-bin python-libvirt dnsmasq-base"' ]
		execute(command)

		command = ['./cacert.sh', hostName]
		execute(command)

		command = ['./servercert.sh', hostName]
		execute(command)

		#command = ['./clientcert.sh', hostName]
		#execute(command)
		
		command = ['ssh', 'root@' + hostName, 'mkdir -p ' + binDir ]
		execute(command)

		command = ['ssh', 'root@' + hostName, binDir + '/whoami.py ' + ip + ' ' + downloadDir + ' ' + imageDir ]
		execute(command)

def clone():
	hostName, vType = chooseVHost()
	if hostName:
		try:
			vm = chooseVm(hostName,vType)
			if vm:
				cloneCount = raw_input('Anzahl der Klone: ')
				autostart = raw_input('Nach Erstellung starten? (j/n): ')
				command = ['ssh', 'root@' + hostName, '/opt/cow/clone.py ' + vm.name() + ' ' + cloneCount + ' ' + autostart + ' ' + str(debug)]
				execute(command)
			else:
				print 'keine passende VM vorhanden'
		except libvirt.libvirtError:
			print 'Host ' + hostName + '(' + vType + ') nicht erreichbar'

def overview():
	hList = hostList()
	if hList:
		for host in hList:
			vList = vmList(host[1], host[2])
			if vList:
				print '\nHost: ' + host[1] + ' (' + host[2] + ')\n'
				print 'ID\tName'
				for vm in vList:
					print vm.name() + '\t' + str(vm.info()[0])

def initialize():
	if not os.path.exists(os.path.expanduser('~/.cow/')):
		os.mkdir(os.path.expanduser('~/.cow/'))

	if not os.path.exists(os.path.expanduser('~/.cow/vhosts')):
		open(os.path.expanduser('~/.cow/vhosts'),'w').close()

	if not os.path.exists('/var/log/cow.log'):
		open('/var/log/cow.log', 'w').close()

def execute(command):
	s = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = s.communicate()
	debugOut(stdout, 3)
	debugOut(stderr, 1)
	return stdout

def hddList(xmlDescription):
	hList = []
	description = parseString(xmlDescription)
	hardDisks = description.getElementsByTagName('disk')
	for i in range(0,len(hardDisks)):
		if hardDisks[i].getAttribute('device') == 'disk':
			hardDisk = hardDisks[i].getElementsByTagName('source')[0].getAttribute('file')
		hList.append(hardDisk)
	return hList

def chooseVHost():
	hList = hostList()
	if hList:
		print 'Wählen Sie den Virtualisierungshost aus:'
		print 'ID\tHost\tTyp'
		for host in hList:
			print str(host[0]) + '\t' + host[1] + '\t' + host[2]
		hostId = intInput('ID: ')
		return [hList[hostId][1], hList[hostId][2]]
	else:
		print 'kein Virtualisierungshost vorhanden'
		return [None,None]

def chooseVHosts(filterName,filterVType):
	print 'Verteilen an Hosts:'
	hList = hostList()
	for host in hList:
		if host[2] == filterVType:
			print str(host[0]) + '\t' + host[1] + '\t' + host[2]
	targetHostIds = raw_input('IDs (z.B 0,2,3): ')
	#remove whitespaces and split the comma seperated value
	targetHostIds = targetHostIds.replace('\t', '').replace(' ', '').split(',')
	#remove duplicates 
	targetHostIds = list(set(targetHostIds))
	targetHosts = []
	for i in targetHostIds:
		if hList[int(i)][1] != filterName:
			targetHosts.append(hList[int(i)])
	return targetHosts

def chooseVm(hostName,vType):
	vOffList = vmOffList(hostName,vType)
	if vOffList:
		print 'Wählen Sie eine VM aus:'
		print 'ID\tName\tState'
		for i in range(0,len(vOffList)):
			print str(i) + '\t' + vOffList[i].name() + '\t' + str(vOffList[i].info()[0])
		vmId = intInput('ID: ')
		return vOffList[vmId]

def startDownload(vHostList, vmName):
	debugOut('start the deluge daemons on target hosts', 1)
	#start the deluge daemon
	for targetHost in vHostList:
		debugOut('starting deluge daemon on' + targetHost[1], 1)
		command = ['ssh', 'root@' + targetHost[1], 'deluged']
		s = subprocess.Popen(command)
	#waiting for the deluge daemon
	time.sleep(1)
	for targetHost in vHostList:
		debugOut('rsync to ' + targetHost[1], 2)
		command = ('rsync', '/tmp/' + vmName + '.torrent', 'root@' + targetHost[1] + ':' + downloadDir + '/' + vmName + '.torrent')
		debugOut(command,3)
		execute(command)
		debugOut('del torrent on ' + targetHost[1], 3)
		command = ['ssh', 'root@' + targetHost[1], 'deluge-console "del ' + vmName + '"']
		s = subprocess.Popen(command)
	#waiting for deletion of the old torrent
	time.sleep(0.5)
	#add the torrent and start downloading
	for targetHost in vHostList:
		debugOut('start torrent on' + targetHost[1],3)
		command = ['ssh', 'root@' + targetHost[1], 'deluge-console "add ' + downloadDir + '/' + vmName + '.torrent"']
		s = subprocess.Popen(command)


def shareImage():
	hostName, vType = chooseVHost()
	if hostName:
		try:
			vm = chooseVm(hostName,vType)
			if vm:
				targetHosts = chooseVHosts(hostName,vType)
				targetHosts.append([-1, hostName, vType])
				command = ['ssh', 'root@' + hostName, '/opt/cow/maketorrent.py ' + vm.name()]
				execute(command)
				command = ['rsync', 'root@' + hostName + ':' + downloadDir + '/' + vm.name() + '.torrent', '/tmp/' ]
				execute(command)
				startDownload(targetHosts, vm.name())
			else:
				print 'keine VM vorhanden'
		except libvirt.libvirtError:
			print 'Host ' + hostName + '(' + vType + ') nicht erreichbar'

def test():
	print 'test'

def intInput(output):
	tmpString = raw_input(output)
	try:
		intNum = int(tmpString)
	except ValueError:
		print 'Keine gültige Zahl'
		intNum = intInput(output)
	return intNum

options = {
 1 : newVServer,
 2 : shareImage, 
 3 : clone,
 4 : overview,
 0 : test}

initialize()

#set debugLevel
if len(sys.argv) > 1:
	try:
		debug = sys.argv[1]
	except ValueError:
		debug = 0
else:
	debug = 0

while (True):
	print 'Menü'
	print ' 1: neuer Virtualisierungsserver'
	print ' 2: Image verteilen'
	print ' 3: Virtuelle Maschine klonen'
	print ' 4: Übersicht aller virtuellen Maschinen'
	print ' 5: Beenden'

	choice = intInput('Auswahl: ')

	if choice <= 4 and choice >= 0:
		options[choice]()
	else:
		sys.exit(0)
