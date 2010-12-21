#!/bin/bash

host="$1"
package="$2"

ssh "root@$1" "apt-get update"
ssh "root@$1" "apt-get install -y $package"
