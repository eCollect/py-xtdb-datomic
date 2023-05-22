#!/bin/bash
#trap "echo stopped" EXIT
TIMEOUT=30
echo looping..
while :
do
# sleep $TIMEOUT &
# wait $!
 #above spawns external sleep in background and that's cumbersome to stop too ; instead, use bash's read builtin, from stderr, with TIMEOUT:
 read -u 2 -t $TIMEOUT
 DOIT=1 KEEPEXTRA=0 /checkpointkeeper.sh $@
done

echo end-of-looping
# https://stackoverflow.com/questions/27694818/interrupt-sleep-in-bash-with-a-signal-trap

# vim:ts=4:sw=4:expandtab
