#!/bin/bash

host="$1"
date="$(date +%s)"
tempdir="/tmp/catemplate$date"
mkdir -p "$tempdir"
echo -e "country = COW\nstate = COWntry\nlocality = COWn\norganization = COW Corp\ncn = $host\ntls_www_client\nencryption_key\nsigning_key" > "$tempdir/client.info"

certtool --generate-privkey > "$tempdir/clientkey.pem"
certtool --generate-certificate --load-privkey "$tempdir/clientkey.pem" \
  --load-ca-certificate /etc/pki/CA/cacert.pem --load-ca-privkey /etc/pki/CA/private/cakey.pem \
  --template "$tempdir/client.info" --outfile "$tempdir/clientcert.pem"

mkdir -p /etc/pki/libvirt/private/
mv "$tempdir/clientkey.pem" "/etc/pki/libvirt/private/clientkey.pem"
mv "$tempdir/clientcert.pem" "/etc/pki/libvirt/clientcert.pem"

rm -rf "$tempdir"
