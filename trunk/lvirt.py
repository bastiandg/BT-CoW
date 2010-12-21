#!/usr/bin/python
import libvirt
conn = libvirt.open('xen://xen7/')
for name in conn.listDefinedDomains():
	dom = conn.lookupByName(name)
	print "Dom %s  State %s" % ( dom.name(), dom.info()[0] )
	print dom.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)
