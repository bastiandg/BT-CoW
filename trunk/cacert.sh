#!/bin/bash
host="$1"
if [ ! -e /etc/pki/CA/cacert.pem ]
then
	date="$(date +%s)"
	tempdir="/tmp/catemplate$date"
	#echo "$tempdir"
	mkdir -p "$tempdir"
	echo -e "cn = COW Corp\nca\ncert_signing_key" > "$tempdir/ca.info"

	mkdir -p /etc/pki/CA/private
	certtool --generate-privkey > /etc/pki/CA/private/cakey.pem
	certtool --generate-self-signed --load-privkey /etc/pki/CA/private/cakey.pem --template "$tempdir/ca.info" --outfile /etc/pki/CA/cacert.pem 2> /tmp/cacreate.log
	rm -r "$tempdir"
	clientcert.sh "$1"
fi
ssh "root@$host" "mkdir -p /etc/pki/CA/"
rsync "/etc/pki/CA/cacert.pem" "root@$host:/etc/pki/CA/cacert.pem"

