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

vHostType = {1: "kvm", 2: "xen"}
debug = 1
downloadDir = "/var/lib/download"
imageDir = "/var/lib/libvirt/images"
binDir = "/opt/cow"
def hostList():
	hostList = []
	hosts = open(os.path.expanduser("~/.cow/vhosts"), "r").readlines()
	for i in range(0,len(hosts)):
		host = hosts[i].split("\t")
		if len(host) == 2: #ignore malformed rows
			hostList.append([len(hostList), host[0], host[1].replace("\n","")])
	return hostList

def vmList(hostName):
	vmList = []
	s = subprocess.Popen(["./vla.sh", hostName], stdout=subprocess.PIPE, stdin= subprocess.PIPE)
	virshOut = s.communicate()[0].split("\n")
	for i in range(2,len(virshOut)-2):
		vm = re.split("[\ ]*", virshOut[i])
		vm[3] = vm[3].replace("shut","shut off")
		vmList.append(vm)
	return vmList

def vmOffList(hostName, vType):
	vOffList = []
	if vType == "xen":
		conn = libvirt.open('xen://' + hostName + '/')
	else:
		conn = libvirt.open('qemu://' + hostName + '/system')
	
	for name in conn.listDefinedDomains():
		vOffList.append(conn.lookupByName(name))
	
	return vOffList

def vmOnList(hostName, vType):
	#TODO filter DOM0
	vOnList = []
	if vType == "xen":
		conn = libvirt.open('xen://' + hostName + '/')
	else:
		conn = libvirt.open('qemu://' + hostName + '/system')
	
	for id in conn.listDomainsID():
		vOnList.append(conn.lookupByID(id))
	
	return vOnList


def vHostExists(hostname):
	hList = hostList()
	for host in hList:
		if host[1] == hostname:
			return True
	return False

def newVServer():
	print "Geben Sie die IP des Hosts ein"
	ip = raw_input("HostIP: ")

	command = ["./hostname.sh", ip]
	hostname = execute(command).replace("\n", "")
	
	if vHostExists(hostname):
		print "schon registriert"
	else :
		print "doesnt exist"
		print "Virtualisierungstechnik"
		print " 1: KVM"
		print " 2: XEN"
		choice = raw_input("")
		choice = int(choice)
		
		#append the new host
		vhosts = open(os.path.expanduser("~/.cow/vhosts"), "a")
		vhosts.write("\n" + hostname + "\t" + vHostType[choice])
		vhosts.close()
		#TODO virsh net-autostart default
		command = ['ssh', 'root@' + hostname, '"mkdir -p ' + binDir + '"']
		execute(command)

		command = ['rsync', 'client-scripts/*.py' ,'root@' + hostName + ':' + binDir]
		execute(command)
		
		command = ["./cacert.sh", hostname]
		execute(command)

		command = ["./servercert.sh", hostname]
		execute(command)

		command = ["./clientcert.sh", hostname]
		execute(command)
		
		command = ['ssh', 'root@' + hostname, '/opt/cow/packageinstall.py "rsync deluged deluge-console mktorrent libvirt-bin python-libvirt dnsmasq-base"' ]
		execute(command)

def shareImage():
	print  "a" #TODO auslagern

def clone():
	print "clone TODO" #TODO
	vHostName, vType = chooseVHost()
	vm = chooseVm(vHostName,vType)
	if vm:
		command = ['ssh', 'root@' + vHostName, '/opt/cow/clone.py ' + vm.name()]
		execute(command)
	else:
		print "keine passende VM vorhanden"

def overview():
	hList = hostList()
	for host in hList:
		print "\nHost: " + host[1] + " (" + host[2] + ")\n"
		vList = vmList(host[1])
		print "ID\tName"
		for vm in vList:
			print vm[1] + "\t" + vm[2]

def initialize():
	if not os.path.exists(os.path.expanduser("~/.cow/")):
		os.mkdir(os.path.expanduser("~/.cow/"))

	if not os.path.exists(os.path.expanduser("~/.cow/vhosts")):
		open(os.path.expanduser("~/.cow/vhosts"),"w").close()

	if not os.path.exists("/var/log/cow.log"):
		open("/var/log/cow.log", "w").close()

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
	return hList

def chooseVHost():
	print "Wählen Sie den Virtualisierungshost aus:"
	print "ID\tHost\tTyp"
	hList = hostList()
	for host in hList:
		print str(host[0]) + "\t" + host[1] + "\t" + host[2]
	hostId = int(raw_input("ID: "))
	return [hList[hostId][1], hList[hostId][2]]

def chooseVHosts(filterName,filterVType):
	print "Verteilen an Hosts:"
	hList = hostList()
	for host in hList:
		if host[2] == filterVType:
			print str(host[0]) + "\t" + host[1] + "\t" + host[2]
	targetHostIds = raw_input("IDs (z.B 0,2,3): ")
	#remove whitespaces and split the comma seperated value
	targetHostIds = targetHostIds.replace("\t", "").replace(" ", "").split(",")
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
		print "Wählen Sie eine VM aus:"
		print "ID\tName\tState"
		for i in range(0,len(vOffList)):
			print str(i) + "\t" + vOffList[i].name() + "\t" + str(vOffList[i].info()[0])
		vmId = int(raw_input("ID: "))
		return vOffList[vmId]

def startDownload(vHostList, vmName):
	print "start the deluge daemons on target hosts"
	#start the deluge daemon
	for targetHost in vHostList:
		command = ['ssh', 'root@' + targetHost[1], 'deluged']
		s = subprocess.Popen(command)
	#waiting for the deluge daemon
	time.sleep(1)
	for targetHost in vHostList:
		print "rsync to " + targetHost[1]
		command = ['rsync', '/tmp/' + vmName + '.torrent', 'root@' + targetHost[1] + ':' + downloadDir + "/" + vmName + '.torrent']
		print command
		execute(command)
		print "del torrent"
		command = ['ssh', 'root@' + targetHost[1], 'deluge-console "del ' + vmName + '"']
		s = subprocess.Popen(command)
	#waiting for deletion of the old torrent
	time.sleep(0.5)
	#add the torrent and start downloading
	for targetHost in vHostList:
		print "start torrent"
		command = ['ssh', 'root@' + targetHost[1], 'deluge-console "add ' + downloadDir + "/" + vmName + '.torrent"']
		s = subprocess.Popen(command)


def test():
	hostName, vType = chooseVHost()
	vm = chooseVm(hostName,vType)
	if vm:
		targetHosts = chooseVHosts(hostName,vType)
		targetHosts.append([-1, hostName, vType])
		command = ['ssh', 'root@' + hostName, '/opt/cow/maketorrent.py ' + vm.name()]
		execute(command)
		command = ['rsync', 'root@' + hostName + ':' + downloadDir + "/" + vm.name() + '.torrent', '/tmp/' ]
		execute(command)
		startDownload(targetHosts, vm.name())
	else:
		print "keine VM vorhanden"""

options = {
 1 : newVServer,
 2 : shareImage, 
 3 : clone,
 4 : overview,
 0 : test}

initialize()

print "Menü"
print " 1: neuer Virtualisierungsserver"
print " 2: Image verteilen"
print " 3: Virtuelle Maschine klonen"
print " 4: Übersicht aller virtuellen Maschinen"

choice = raw_input("")
choice = int(choice)

if choice <= 4 and choice >= 0:
	options[choice]()

