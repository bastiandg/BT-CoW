#!/bin/bash

host="$1"

#make the libvirtd listen
ssh "root@$host" "sed -i 's;libvirtd_opts=\"-d\";libvirtd_opts=\"-d -l\";g' /etc/default/libvirt-bin"

#set rights
if [ ! $(ssh root@$host 'grep -l "user[ ]*=" "/etc/libvirt/qemu.conf"') ]
then
	ssh "root@$host" 'echo -e "user = \"root\"\ngroup = \"root\"" >> /etc/libvirt/qemu.conf'
fi

