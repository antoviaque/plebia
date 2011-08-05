#!/bin/bash

cd /var/www/plebia 

rm plebia/db/plebia.sqlite 
./plebia/manage.py syncdb 
./plebia/manage.py migrate

