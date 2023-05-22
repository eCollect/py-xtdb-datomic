# https://docs.xtdb.com/administration/installing/#clojure-cli
run:	#:3001 ?
	#XXX needs deps.edn ; if not -f specified, default cfg-file is xtdb.edn ; both *.edn are from ../py-xtdb
	clojure -m xtdb.main -f cfg-xtdb.edn &
	sleep 3
	pgrep -f -l clojure.main.*xtdb.main | grep java && until curl localhost:3001/_xtdb/status ; do sleep 2 ; done

stop:
	pkill -f clojure.*xtdb

run2:	#:3000
	java -jar ./xtdb-in-memory.jar &

check status ping:
	curl localhost:3001/_xtdb/status

#others:
# https://github.com/xtdb/xtdb-in-a-box
# https://github.com/xtdb/xtdb/releases
# https://github.com/xtdb/xtdb/releases/download/1.22.1/xtdb-in-memory.jar
# https://github.com/xtdb/xtdb/releases/download/1.22.1/xtdb-standalone-rocksdb.jar

####
# so... multiple xtdb nodes own only the index-store (rocksdb or whatever
# KeyValue thing), and they should share the tx-log and the doc-store, whatever
# they are (kafka/postgres/s3/... - single or cluster). They don't really know
# about each other, and only parallelize on the reading/query side ; the
# writing goes into same storage, from any node, and the write paralelism /
# congestion is there, not in xtdb. i.e. in our case we may one day start with
# single kafka/postgres/s3 - which gives the global ordering needed - but then
# turn that into partial-order thing (multi-kafka), so more writers are used.

# the tx-log/doc-store used from multiple nodes cannot be rocksdb - that's
# essentialy embedded db living in the process of the owner. So, use
# postgresql/kafka/s3/something-else-thats-separate (edited)

# in the deps.edn (which controls whole clojure thing) there is a
# :jvm-opts ["-Xmx2G"] - which controls how much memory the java host gets. May
# try increasing that to see if speed gets better. There are bunch of similar
# options ( like -Xms2G ) but go RTFM of java enterprise :/

# 1.23 should use many cores for the indexing of rocksdb, but that is yet
# to be proved - and should be configurable somehow..

# vim:ts=4:sw=4:noexpandtab
