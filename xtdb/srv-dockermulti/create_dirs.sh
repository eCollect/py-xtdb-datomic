#!/bin/sh
for a in `cat volumes.txt`; do mkdir -pv "data/$a" ; done

#while read -r line
#do
#  volume_dir='data/'$(echo $line)
#  if [ -d $volume_dir ];
#    then
#        echo "$volume_dir - directory already exists."
#    else
#        echo "creating directory: $volume_dir"
#        mkdir -p $volume_dir
#  fi
#done < volumes.txt
