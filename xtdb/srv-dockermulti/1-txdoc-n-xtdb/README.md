so far this has these 3 combinations:
 * tx+docs in kafka - tx+docs-kafka-kraft/
 * tx+docs in postgresql - tx+docs-pg/
 * tx in kafka + docs in postgresql - tx-kafka-kraft+docs-pg/

they all start a checkpointer and 2 xtdb clones, on ports 3001 , 3002. (there are also clones 3/3003 4/3004 5/3005 but commented out)

to run, copy from appropriate directory:
 * cfg-xtdb.edn into ./ 
 * dc-extending.yaml into ./docker-compose.yml

then docker-compose build ; ... up ; ... stop ...etc 

use make (see makefile) to play with individual services, e.g. make logall

note/TODO: 
* don't know how to start another xtdb via docker-compose without stopping+editing
* actually, don't know how to use scaling of docker-compose with proper different GROUPID and port for each xtdb

[//]: #  vim:ts=4:sw=4:expandtab
