#!/bin/sh
echo moving $1 to $2 - should be run inside data/
pwd
mkdir -p $2
mv $1/* $2/
chall.pl "s,$1,$2," $2/*.edn
