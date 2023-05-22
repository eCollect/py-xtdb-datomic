class cfg:
    port = 3001
    index_path  = '{datadir}/index-store'
    tx_path     = '{datadir}/tx-log'
    doc_path    = '{datadir}/document-store'
    lucene_path = '{datadir}/lucene'

    datadir     = './data'
    reporter    = False
    memory      = False
    noindent    = False
    edn_format  = False
    lucene_multi= False         #https://docs.xtdb.com/extensions/full-text-search/
    lucene_memory= False
    nolucene    = False
    sql_calcite_port = 0        #for SQL-like syntax https://docs.xtdb.com/extensions/sql/

    #checkpointer       https://docs.xtdb.com/administration/1.23.1/checkpointing/
    #lucene_checkpointer ..

'''
deps.edn needs:
    lucene  :   com.xtdb/xtdb-lucene {:mvn/version "1.23.1"}
    calcite :   com.xtdb/xtdb-sql {:mvn/version "1.23.1"}
    xtdb    :   com.xtdb/xtdb-core {:mvn/version "1.23.1"}
    rocksdb :   com.xtdb/xtdb-rocksdb {:mvn/version "1.23.1"}
    metrics :   com.xtdb/xtdb-metrics {:mvn/version "1.23.1"}
    http    :   com.xtdb/xtdb-http-server {:mvn/version "1.23.1"}
    httpclient???: com.xtdb/xtdb-http-client {:mvn/version "1.23.1"}
    kafka   :   com.xtdb/xtdb-kafka {:mvn/version "1.23.1"}
    kafka-memory : com.xtdb/xtdb-kafka-embedded {:mvn/version "1.23.1"}
'''

import sys
for a in sys.argv[1:]:
    if a == '-h' or a == '--help':
        print( 'this.py k1=v1 k2=v2 k3bool ..  with defaults:')
        for k,v in cfg.__dict__.items():
            if k.startswith('__'): continue
            print( '  ', k, '=', v)
        raise SystemExit
    val = getattr( cfg, a, None)
    if isinstance( val, bool): setattr( cfg, a, True)
    if '=' in a:
        k,v = a.split('=')
        val = getattr( cfg, k, None)
        if k is not None:
            setattr( cfg, k, type( val)( v))
            continue
    assert 0, f'unknown arg {a}, run with -h'

class sym( str): pass
r = {}
if cfg.port:
    r.update({
        'xtdb.http-server/server' : { 'port': cfg.port }
        })
if cfg.sql_calcite_port:
    r.update({
        'xtdb.calcite/server': { 'port': cfg.sql_calcite_port }
        })

if not cfg.memory:
    # ;; NOTE Comment these to have an in-memory system:
    r.update({
        'xtdb/index-store'         : { 'kv-store': { 'xtdb/module' : sym('xtdb.rocksdb/->kv-store'), 'db-dir': cfg.index_path.format_map( cfg.__dict__) }},
        'xtdb/tx-log'              : { 'kv-store': { 'xtdb/module' : sym('xtdb.rocksdb/->kv-store'), 'db-dir': cfg.tx_path.format_map(    cfg.__dict__) }},
        'xtdb/document-store'      : { 'kv-store': { 'xtdb/module' : sym('xtdb.rocksdb/->kv-store'), 'db-dir': cfg.doc_path.format_map(   cfg.__dict__) }},
        })
if not cfg.nolucene:
    luc = {} if cfg.lucene_memory else { 'db-dir': cfg.lucene_path.format_map( cfg.__dict__) }
    if cfg.lucene_multi:
        luc.update({    #XXX BEWARE this produces different indexes with/without it
            'indexer': 'xtdb.lucene.multi-field/->indexer' #	;;for multi-field lucene-text-search
            })
    r.update({
        'xtdb.lucene/lucene-store' : luc
        })
if cfg.reporter:
    r.update({
        'xtdb.metrics.console/reporter' : { 'report-frequency': "PT10S" }
        })

if not cfg.edn_format:
    import json
    print( json.dumps( r , **({} if cfg.noindent else dict( indent=2))))
else:
    from edn_format import dumps, Symbol
    def sym2sym( x):
        if isinstance( x, dict):
            return dict( (k,sym2sym(v)) for k,v in x.items())
        if isinstance( x, sym): return Symbol(x)
        return x
    print( dumps( sym2sym( r), keyword_keys=True, **({} if cfg.noindent else dict( indent=2))))

# vim:ts=4:sw=4:expandtab
