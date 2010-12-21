#!/bin/bash
ip=$1
hostname=$(ssh "root@$ip" 'echo "$HOSTNAME"')

if [ ! $(grep -l "$hostname[ ]*$" "/etc/hosts") ]
then
	echo -e "$ip\t$hostname" >> /etc/hosts
fi

echo $hostname
exit 0
