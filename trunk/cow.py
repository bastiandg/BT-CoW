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

vHostType = {1: "KVM", 2: "XEN"}
debug = 1
downloadDir = "/var/lib/download"
imageDir = "/var/lib/libvirt/images"
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
		#virsh net-autostart default
		command = ["./libvirtprep.sh", hostname]
		execute(command)

		command = ["./xenprep.sh", hostname]
		execute(command)
		
		command = ["./cacert.sh", hostname]
		execute(command)

		command = ["./servercert.sh", hostname]
		execute(command)

		command = ["./clientcert.sh", hostname]
		execute(command)
		
		command = ["./remoteinstall.sh", hostname, "rsync deluged deluge-console mktorrent libvirt-bin python-libvirt dnsmasq-base" ]
		execute(command)

def shareImage():
	print "Wählen Sie den Virtualisierungshost aus:"
	print "ID\tHost\tTyp"
	hList = hostList()
	for host in hList:
		print str(host[0]) + "\t" + host[1] + "\t" + host[2]
	hostID = raw_input("ID: ")
	hostName = hList[int(hostID)][1]
	print hostName
	
	vList = vmList(hostName)
	for i in range(0,len(vList)):
		print  str(i) + "\t" + vList[i][2] + "\t" + vList[i][3]

def clone():
	print "clone TODO"

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
		"""
		if not os.path.isfile(hardDisk):
			print "Skipping %s because it is no hard disk image" % hardDisk
		else:
			if description.getElementsByTagName("domain")[0].getAttribute("type") == "xen":
				hardDisks[i].getElementsByTagName("driver")[0].setAttribute("name", "phy")
				hardDisk = os.path.abspath(hardDisk)"""
	return hList

def test():
	print "Wählen Sie den Virtualisierungshost aus:"
	print "ID\tHost\tTyp"
	hList = hostList()
	for host in hList:
		print str(host[0]) + "\t" + host[1] + "\t" + host[2]
	hostId = raw_input("ID: ")
	hostName = hList[int(hostId)][1]
	
	vOffList = vmOffList(hostName,hList[int(hostId)][2])
	if vOffList:
		print "Wählen Sie eine VM aus:"
		print "ID\tName\tState"
		for i in range(0,len(vOffList)):
			print str(i) + "\t" + vOffList[i].name() + "\t" + str(vOffList[i].info()[0])
		vmId = raw_input("ID: ")
		vm = vOffList[int(vmId)]
		#makeTorrent(hostName, vm)
		command = ['ssh', 'root@' + hostName, '/opt/cow/maketorrent.py ' + vm.name()]
		execute(command)
		command = ['rsync', 'root@' + hostName + ':' + downloadDir + "/" + vm.name() + '.torrent', '/tmp/' ]
		execute(command)

		print "Verteilen an Hosts:"
		for host in hList:
			if host[2] == hList[int(hostId)][2]:
				print str(host[0]) + "\t" + host[1] + "\t" + host[2]
		targetHostIds = raw_input("IDs (z.B 0,2,3): ")
		targetHostIds = targetHostIds.replace("\t", "").replace(" ", "").split(",")
		targetHosts = []
		command = ['ssh', 'root@' + hostName, 'deluged']
		print command
		s = subprocess.Popen(command)
		#execute(command)
		
		command = ['ssh', 'root@' + hostName, 'deluge-console "add ' + downloadDir + "/" + vm.name() + '.torrent"']
		print command
		s2 = subprocess.Popen(command)
		#execute(command)

		#TODO Abfrage der korrekten Virtualisierungstechnik
		for i in targetHostIds:
			if hList[int(i)][1] != hostName:
				targetHosts.append(hList[int(i)])

	else:
		print "keine VM vorhanden"""

def makeTorrent(hostName, vm):
	print vm.name()
	torrentDir = downloadDir + '/' + vm.name()
	#make torrent directory and empty it
	command = ['ssh', 'root@' + hostName, 'mkdir -p "' + torrentDir  + '" && rm -rf "' + torrentDir + '/*"']
	execute(command)
	
	hdList = hddList(vm.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE))
	for hd in hdList:
		command = ['ssh', 'root@' + hostName, 'ln -s "' + hd  + '" "' + torrentDir + '/' + os.path.basename(hd) + '"']
		execute(command)
		print hd
		

def share(host,image,targetHosts):
	ip = socket.gethostbyname(host)
	print image + " auf " + host + " (" + ip + ")"
	print targetHosts
	torrentDest = '/var/lib/download/' + os.path.basename(image) + '.torrent'
	command = ['ssh', 'root@' + host, 
			'mktorrent -a ' + ip + ' -o ' + torrentDest + ' '  + image]
	execute(command)
	command = ['ssh', 'root@' + host,
			'deluge-console "add ' + torrentDest + '"' ]
	execute(command)

	for targetHost in targetHosts:
		command = ['ssh', 'root@' + targetHost[1], 'rsync ' + host + ':' + torrentDest + " " + downloadDir + '/']
		execute(command)
		command = ['ssh', 'root@' + targetHost[1],
				'deluge-console "add ' + torrentDest + '"' ]
		execute(command)
		command = ['ssh', 'root@' + targetHost[1],
				'deluge-console "start ' + torrentDest + '"' ]
		execute(command)
	
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

