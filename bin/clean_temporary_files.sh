#!/bin//bash

find -type f -name '*.pyc' -or -name '*~' -exec rm {} \;

rm -rf static/tests/*

