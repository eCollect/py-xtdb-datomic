# XTDB-based storage environment

each variant is in its own dir, e.g. 1-txdoc-n-xtdb/
For each, `cd that-dir`, then ./run_local.sh or ./stop.sh, 
which use ./docker-compose.yml ./Dockerfile ./cfg-xtdb.edn ./deps.edn

## Prerequisite

You must have docker + docker-compose installed & running 

on Mac: may use docker-desktop which brings the above:
https://docs.docker.com/desktop/install/mac-install/
beware, for M1, that's 2 extra layers: virtualization + emulation (images are not M1)
and.. is rather slow (like 10x-50x slower)

linux: just docker + docker-compose ; the docker-desktop is too much
then eventualy: https://docs.docker.com/engine/security/rootless/
see ./linux/ for more 

persistent data:
 - docker-compose will auto-create needed host folders/volumes under ./data/
 - on linux without docker-desktop, images roots are overlay-mounted inside /var/lib/docker/... 
 which is by default on / root host filesystem. If no space there.. 
 move the whole /var/lib/docker/ elsewhere-with-lots-of-space and symlink it as /var/lib/docker

## When changes are needed 

to add another xtdb node, ./stop.sh it all, edit the docker-compose, ./run_local.sh it all 

same for fiddling with volumes in ./data

- indexes of some node can be removed - will be rebuilt (from checkpoints). 
- If a node is too far behind in indexing, then stop + remove_index + restart->rebuild maybe much faster
- old checkpoints can be safely removed on-the-fly - TODO script for that

## notes

1. Sometimes on mac-M1, some xtdb nodes may not start properly - doing nothing on ~100% cpu - in which case, restart the container (from docker desktop, multiple times if needed)


## ./1-txdoc-n-xtdb/

has 3 variants of 1 transaction/doc (write) store and n- xtdb (read) stores:
- tx+docs-kafka-kraft/      : transaction/doc in kafka+kraft
- tx+docs-pg/               : transaction/doc in postgresql
- tx-kafka-kraft+docs-pg/   : transaction in kafka+kraft, docs in postgresql

(there is also config for kafka+zookeeper, not used anymore)

in all cases, xtdb keeps indexes in rocksdb ; all xtdb nodes write to same tx/doc store

after some benchmarking, on same 16 core machine: 
 - kafka alone is fastest option, xtdb indexing lags behind 
 - postgresql alone is slowest , and xtdb indexing almost manages to catch up 
 - kafka+postgresql is middle to slower

see also ./todo

[//]: #  vim:ts=4:sw=4:expandtab
