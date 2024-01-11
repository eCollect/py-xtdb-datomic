# trying xtdb / datomic - temporal immutable dbs

These are similar temporal immutable dbs, in clojure + ~datalog. 
Providing something like automatic event-sourcing + cqrs , on somewhat lower-level, and using external storage-layers underneath.

xtdb v2 introduces new architecture, new composable query language xtql, and sql-2011 compatibility.

* github.com/alexpetrov/datomic-xtdb-facts
* vvvvalvalval.github.io/posts/2018-11-12-datomic-event-sourcing-without-the-hassle.html
* https://xtdb.com/v2

status so far: 
 + datomic:
 	+ http-rest-api wrapper client, +edn - ok+tests 
 	+ query-builder for datalog + edn - ok+tests
 	+ schema - ok+tests
 	- multinode - no
 - xtdb/v1:
 	+ http-rest-api wrapper client, +edn+json - ok+tests
 	+ query-builder for datalog + edn , +lucene - ok+tests
 	+ multinode , dockers
		+ kafka, with kraft or zookeeper
		+ postgresql
		+ kafka+postgresql
		- partial-order in kafka ?
 + xtdb.v2.alpha:
	+ xtql query-builder - ok+doctests 
 	+ http-rest-api wrapper client, +transit-json - ok+tests
	- http-rest-api over json-ld - (not yet)
	- multinode etc non-local install?
 - other tests and examples exist, not very ordered
 - all else - higher level - is still in flux - schema, objmapper, unitofwork, etc
