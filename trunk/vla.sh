#!/bin/bash

if [ "$1" = "-h" -o $1 = "--help" ]
then
	echo "Usage: vla.sh [user] host"
	echo "Default user is root"
	exit 0
fi

if [ ! $2 ]
then 
	user=root
	host=$1
else
	user=$1
	host=$2
fi

ssh "$user@$host" "virsh list --all"

#ssh-keygen -f ~/.ssh/id_rsa -N "" -q
