#!/bin/bash
KEEPEXTRA=${KEEPEXTRA:-1}
KEEP=$((1+($KEEPEXTRA<0 ? 1 : $KEEPEXTRA)))
echo all but $KEEP
#DOIT=
#name is like checkpoint-txid-....edn ; actual-data-dir is same without .edn ; only data-dirs with matching .edn are complete
#no spaces in names plz
for DIR in $@ ; do (
	cd $DIR
	pwd
	TODEL=`ls -1 ./checkpoint-*.edn | sort --field-separator=- -n -k 2 | head -n -$KEEP | sed -e 's/.edn$//'`
	for D in $TODEL ; do echo $DIR/$D ; test -n "$DOIT" && rm -rf $D* ; done
	)
done
