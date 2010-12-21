#!/bin/bash

dir="/var/lib/download"

rsync "$dir/$2" "$1:$dir"
ssh $1 "deluge-console \"add $dir/$2\""

