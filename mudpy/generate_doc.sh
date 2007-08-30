#!/bin/sh

cd `dirname $0`

PROJECT="MudPy"
URL="http://mud.tuxsoft.net"
OUTPUTDIR="./doc"
FILES="Driver.py corelib driver mudlib reactor utils"

epydoc -v --name ${PROJECT} --url ${URL} --html --graph classtree -o ${OUTPUTDIR} ${FILES} 
