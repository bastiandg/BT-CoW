#!/bin/bash

if [ "$1" = "-h" -o $1 = "--help" ]
then
	echo "Usage: ssh.sh [user] host"
	echo "Default user is root"
	exit 0
fi

if [ ! -e ~/.ssh/id_rsa ]
then 
	ssh-keygen -t rsa -f ~/.ssh/id_rsa -N "" -q
fi

if [ ! $2 ]
then 
	user=root
	host=$1
else
	user=$1
	host=$2
fi

ssh-copy-id "$user@$host"

#ssh-keygen -f ~/.ssh/id_rsa -N "" -q
