#!/bin/sh

rm -rf /var/www/downloads/*$1*

for i in `deluge-console info | grep -A 1 "Name: $1 " | grep 'ID: ' |awk '{ print $2 }'` ; do deluge-console "rm $i" ; done

