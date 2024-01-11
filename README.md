# trying xtdb / datomic - temporal immutable dbs

These are similar temporal immutable dbs, in clojure + ~datalog. 
Providing something like automatic event-sourcing + cqrs , on somewhat lower-level, and using external storage-layers underneath.

xtdb v2 introduces new architecture, new composable query language xtql, and sql-2011 compatibility.

* github.com/alexpetrov/datomic-xtdb-facts
* vvvvalvalval.github.io/posts/2018-11-12-datomic-event-sourcing-without-the-hassle.html
* https://xtdb.com/v2

status so far: 
 + http-rest api wrapper-drivers - ok+tests - datomic, xtdb/v1, xtdb/v2
 + representing edn-format + datalog query-builder - ok+tests - datomic+xtdb/v1
 - other tests exist, not very ordered
 - all else is still in flux.. - schema, objmapper, unitofwork, etc
 + xtdb.v1 multinode , dockers
 	+ kafka, with kraft or zookeeper
	+ postgresql
	+ kafka+postgresql
	- partial-order in kafka ?
 + datomic
 	+ schema - ok+tests
 	- multinode - no
 + xtdb.v2 (still alpha):
	+ xtql query-builder - ok+doctests 
	+ http-api over transit-json - only few tests
	- http-api over json-ld (not yet)
	- multinode etc non-local install?

