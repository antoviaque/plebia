#!/bin/sh

for i in `deluge-console info |grep ID|sed -e 's/ID: //'`; do deluge-console "rm $i" ; done

