#!/bin/sh

#dont do these below, let docker-compose make them..
# ./create_dirs.sh
#for a in `cat volumes.txt`; do mkdir -pv "data/$a" ; done

#export DUID=`id -u` DGID=`id -g`
docker-compose down && docker-compose build && docker-compose up -d

