#!/bin/bash

cd /var/www/plebia 

cp -f plebia/db/plebia.sqlite.save.2 plebia/db/plebia.sqlite.save.3
cp -f plebia/db/plebia.sqlite.save plebia/db/plebia.sqlite.save.2
mv -f plebia/db/plebia.sqlite plebia/db/plebia.sqlite.save

./plebia/manage.py syncdb 
./plebia/manage.py migrate

