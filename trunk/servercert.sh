#!/bin/bash

host=$1
date="$(date +%s)"
tempdir="/tmp/catemplate$date"
mkdir -p "$tempdir"
echo -e "organization = COW Corp\ncn = $host\ntls_www_server\nencryption_key\nsigning_key" > "$tempdir/server.info"

certtool --generate-privkey > "$tempdir/serverkey.pem"
certtool --generate-certificate --load-privkey "$tempdir/serverkey.pem" \
  --load-ca-certificate /etc/pki/CA/cacert.pem --load-ca-privkey /etc/pki/CA/private/cakey.pem \
  --template "$tempdir/server.info" --outfile "$tempdir/servercert.pem" 2> "/var/log/cow.log"

ssh "root@$host" "mkdir -p /etc/pki/libvirt/private/"
rsync "$tempdir/serverkey.pem" "root@$host:/etc/pki/libvirt/private/serverkey.pem"
rsync "$tempdir/servercert.pem" "root@$host:/etc/pki/libvirt/servercert.pem"

rm -rf "$tempdir"
