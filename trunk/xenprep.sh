#!/bin/bash
hostname=$1
#ssh "root@$hostname"
#echo -e "(xend-http-server no)\n(xend-unix-server yes)" >> /etc/xen/xend-config.sxp
#execute(command)
if [ $(ssh root@$hostname 'ls /boot/xen*.gz &> /dev/null && echo $?' ) ]
then

	if [ ! $(ssh root@$hostname 'grep -l "^[\s]*(xend-http-server no)[\s]*$" "/etc/xen/xend-config.sxp"') ]
	then
		ssh "root@$hostname" 'echo -e "(xend-http-server no)" >> /etc/xen/xend-config.sxp'
	fi

	if [ ! $(ssh root@$hostname 'grep -l "^[\s]*(xend-unix-server yes)[\s]*$" "/etc/xen/xend-config.sxp"') ]
	then
		ssh "root@$hostname" 'echo -e "(xend-unix-server yes)" >> /etc/xen/xend-config.sxp'
	fi
fi
