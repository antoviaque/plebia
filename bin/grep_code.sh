#!/bin/sh

CODE_FILES=`find -type f \( -name '*.py' -or -name '*.js' -or -name '*.sh' -or -name '*.html' \) -not -path '*/dist/*' -not -path '*/migrations/*' -not -path '*/jscoverage/*'`

grep "$1" $CODE_FILES

