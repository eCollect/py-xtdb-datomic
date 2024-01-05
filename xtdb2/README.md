none of this works yet properly
at least for XTDB 2.x (pre-alpha) @ "dev-SNAPSHOT" @ 7ef8b33

https://docs.xtdb.com/index.html
https://docs.xtdb.com/reference/main.html

older:
 see: https://www.xtdb.com/blog/2x-early-access  and  https://www.xtdb.com/learn/what-is-xtdb 2.x :
 examples: https://www.xtdb.com/v2  


* https://github.com/xtdb/xtdb/blob/2.x/img/xtdb-node-1.svg
* built around https://arrow.apache.org/  - columnar store
* allows compression, vectorized processing, sparse data
* role of transaction-log/Kafka-or-else is reduced - just a 'Write-Ahead Log’ (i.e. no need of retention=forever, it is safe to truncate eventually) 
* new composable language - XTQL (Datalog-like , see unify)
* native SQL dialect
* full bitemporality in querying (time ranges)
* arbitrary nested data access/querying - match
* gradual schema (maybe, still schema-less)

* * transactions have has assert-exists/notexists-over-query as mechanism for constraints

some discussion: https://discuss.xtdb.com/t/several-questions-on-2-0/206 


findings:

* all operations require a tablename to associate the data with it
* nothing above bare functionality
* full-text-search would be external
* http-encoding is transit+json (and maybe json-LD later?):
  * Has own Keyword, Symbol , no auto-key-to-keyword convertions etc somewhat different from edn_format
  * python - https://github.com/cognitect/transit-python - not updated since py3.5 ~abandoned ; works ok after few patches of collections.abc namespace
    * updated fork (py3.6+) at https://github.com/3wnbr1/transit-python2/ - no semantical diffs
    * for whatever reason, list and tuple are both mapped to their Array, while their List is unmapped
  * tweaks so far:
    * reuse the edn-format tweaks, so convert keywords and frozendict into edn ones , then auto- convert dict keys into keywords , convert kebab-case to camel-case, etc

* NO http documentation, so it’s reverse engineering and MITMproxying between a Clojure Repl made with  , and the (docker) xtdb-server
  * client-my-playground-dev/user.clj - require xtdb.api instead of datalog, and check http-host+port there

ver.~jun14:

* GET /swagger.json → json : contains proper (?) stuff but without any further description
* GET /status → ts+json : works, yields dict with only lastCompleted / lastSubmitted xtdb/tx-key maps
* POST /tx ↔︎ ts+json : works (well, maybe, does not fail, cannot read back anything yet)
  * returns a xtdb/tx-key map : ["~#xtdb/tx-key",["^ ","~:tx-id",4117,"~:system-time",["~#time/instant","2023-06-14T09:05:58.349337Z"]]] 
  * which as camel-ized py-dict is: {'txId': 4117, 'systemTime': datetime.datetime(2023, 6, 14, 9, 5, 58, 349337, tzinfo=tzutc())}
* POST /query ↔︎ ts+json
  * it seems to guess - if query=dict then it’s Datalog, if query=text, it is Sql ; an old variant had separate /datalog + /sql instead
    * no datalog-query-as-text-sending anymore → text assumes sql
  * the representation of essential (operator …) constructs (match $, q, joins etc) seems unusable - instead of a structure, it makes a special xtdb.List tagged value containing textual-dump-of-clojure-code.. see xtdb/v2/query-match-txjson
    * so for now (14.jun) - that is emulated as List/Match over edn-dumps, and further dev is stopped - too early
  * also, with limit:1 it returns exactly one dict (not list of one dict) ; with limit:2 it returns space-delimted text of dicts - not even json-array anymore 
	*  ''' ["^ ","~:id",1] ["^ ","~:id",12] '''

* overall it seems too few common overlaps with v.1, so separated it into own db2.xtdb2 client. Note: tests need env-var XTDB2=something to switch between clients


version of nov.15:

* GET /openapi.yaml -> json
* GET /status → ts+json : works same
..

version of dec.2x: needs complete rework/redesign
* XTQL complete first-cut - https://docs.xtdb.com/reference/main.html
* GET /openapi.yaml -> yaml
* GET /status → ts+json or json

* /tx ~~ needs obj types "xtdb.tx/xtql" or type "xtdb.tx/put" .. then maybe works but something inside server dies - indexer or else
* /query ~~ does not - Request coercion failed. 

