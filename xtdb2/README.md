
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

discussions: 
 https://discuss.xtdb.com/t/several-questions-on-2-0/206 
 https://discuss.xtdb.com/g/XTQL-Feedback

findings:
* most operations require a tablename to associate the data with it
* full-text-search and similars would be external?
* http-encoding is transit+json (and maybe json-LD later?):
  * has own Keyword, Symbol .. etc, no more edn_format
  * use transit-python2 fork of abandoned cognitect/transit-python 
    * for whatever reason, list and tuple are both mapped to Array, while List is unmapped?
* NO http/transit documentation, so it’s reverse engineering and MITMproxying between a Clojure Repl (run clojure over deps.edn), and the (docker) xtdb-server

state of this wrapper - jan'24:
* completely new dbclient, separate from xtdb1
	* no more edn/edn_format ; base.qsyntax.sym/kw/kw2 should be copied if needed 
* tweaks for transit:
	* auto-keywordize/de-keywordize dicts
	* auto-convert datetime to/from #time/instant
	* more specifics below

* GET /openapi.yaml -> yaml
* GET /status → ts+json or json
	* returns dict with only lastCompleted / lastSubmitted #xtdb/tx-key maps
* POST /query ↔︎ ts+json
  * qyery-type is guessing - if query=dict then it’s XTQL, if query=text, it is SQL
  * needs sequences i.e. (<operator> ...) , to be special #list tagged value-lists 
  * needs datetimes to be #time/instant, does not understand m/t transit-types
  *	result ts+json is so-called streaming json, i.e. yields a "stream" of space delimited small jsons, not a json-array of those
  	* so, with limit:1 it returns exactly one dict (not list of one dict) ; with limit:2 it returns space-delimited text of dicts - not json-array 
		*  ''' ["^ ","~:id",1] ["^ ","~:id",12] '''
  * XXX giving wrong/inexisting after-tx may result in waiting-forever 
* POST /tx ↔︎ ts+json 
	* each tx-op need be dict tagged with #xtdb.tx/<op>
	* returns a #xtdb/tx-key map : ["~#xtdb/tx-key",["^ ","~:tx-id",4117,"~:system-time",["~#time/instant","2023-06-14T09:05:58.349337Z"]]] 
	* as in xtdb1, this is "async" i.e. tx-key is returned immediately, but actual processing of requested ops may be later
  * XXX BUG? - if there's no after-tx specified in some query, no transactions become indexed - returning last (indexed) state (which can be empty)
  * XXX no "sync" method?

