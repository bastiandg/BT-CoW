#!/bin/bash
ip="$1"
host=$(ssh root@$ip 'echo "$HOSTNAME"')
ssh-copy-id root@$host > /dev/null

if [ ! $(grep -l "$host[ ]*$" "/etc/hosts") ]
then
	echo -e "$ip\t$host" >> /etc/hosts
fi

echo $host
exit 0
