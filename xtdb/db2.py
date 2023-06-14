from . import dbclient as db1
import edn_format

class List( tuple):
    'for the query operators like match, subquery.. - ($ (q (left-join etc' # FIXME
    def __new__( me, *a):
        return super().__new__( me, a)
op_match = edn_format.Symbol( '$')
class Match( List):
    def __new__( me, *a):
        return super().__new__( me, op_match, *a)

def transit_dumps( x):
    #print( 333333, x)
    if 0:   #for original transit-python, not needed for transit-python2
        import collections.abc
        for c in 'MutableMapping Mapping Hashable'.split():
            setattr( collections, c, getattr( collections.abc, c))
    from transit.writer import Writer
    from transit.write_handlers import KeywordHandler, SymbolHandler, MapHandler, SetHandler, TaggedMap
    from transit.transit_types import Keyword, Symbol
    from io import StringIO
    buf = StringIO()
    w = Writer( buf, 'json' )
    class KeywordHandler2( KeywordHandler):
        @staticmethod
        def rep(k): return k.name
        string_rep = rep
    class MapHandler2( MapHandler):
        @staticmethod
        def rep(m):
            return dict( (Keyword( k) if not isinstance(k, edn_format.Keyword) else k,v)
                    for k,v in m.items())
    w.register( edn_format.Keyword, KeywordHandler2 ) #w.marshaler.handlers[
    w.register( edn_format.Symbol,  SymbolHandler ) #w.marshaler.handlers[
    w.register( dict,  MapHandler2 ) #w.marshaler.handlers[

    class ListHandler( SetHandler):
        @staticmethod
        def tag(_): return 'xtdb/list'
        @staticmethod
        def rep(s): return edn_format.dumps( s)
    w.register( List,  ListHandler)     #tuple==list==array/vector

    w.write( x )
    print( 'tj-dump\n  in', x, '\n  out', buf.getvalue(), '\n  edn', edn_format.dumps( x))
    return buf.getvalue()

def transit_loads( x):
    from transit.reader import Reader
    from io import StringIO
    #x = x.decode( 'utf8')      #hope it's utf8 XXX
    buf = StringIO( x)
    #from transit.reader import JsonUnmarshaler
    #r = JsonUnmarshaler().load( buf)
    r = Reader( protocol= 'json')
    from transit.transit_types import Keyword, Symbol
    from transit import transit_types
    from transit.read_handlers import KeywordHandler, SymbolHandler, CmapHandler, pairs, DateHandler
    if not getattr( KeywordHandler, '_dbclixed', 0):
        KeywordHandler._dbclixed = 1
        KeywordHandler.from_rep = edn_format.Keyword    #staticmethod
        #SymbolHandler.from_rep = staticmethod( edn_format.Symbol )
        #CmapHandler.from_rep = staticmethod( lambda cmap: dict( pairs( cmap))) not needed if below frozendict
        transit_types.frozendict = edn_format.ImmutableDict #dict   auto keyword2str, kebab2camel, etc
        r.register( 'time/instant', DateHandler)
        class txkey_dict( edn_format.ImmutableDict ): pass  #dict
        class txkey_handler: from_rep = txkey_dict
        r.register( 'xtdb/tx-key', txkey_handler)

    rr = r.read( buf)
    #print( 5555, rr)
    #if isinstance( rr, dict):
    #    for k,v in  list( rr.items()): print( k,'::', v, type(v))
    return rr
    #TODO
    # dict key/keywords -> text -> kebab2camel/ edn_response_Keyword_into_str above

if 0:
    import functools
    def nonv2( f ):
        @functools.wraps( f)
        def wrapper( me, *a,**ka):
            assert not me.is_v2
            return f( me, *a,**ka)
        return wrapper

class xtdb2_read( db1.BaseClient):
    '''
    https://www.xtdb.com/reference/
    v2/swagger-v2.json
    https://www.xtdb.com/reference/main/data-types

    https://www.xtdb.com/reference/main/datalog/queries
    https://www.xtdb.com/reference/main/datalog/txs

    TODO:
    https://www.xtdb.com/reference/main/sql/txs
    https://www.xtdb.com/reference/main/sql/queries
    '''

    _app_transit_json = 'application/transit+json'
    _headers_base = {
        #'accept' : BaseClient._app_json,   #text/plain text/html
        #**db1.BaseClient._headers_content_json,
        'accept' : _app_transit_json,
        'content-type': _app_transit_json,
        }

    def _response( me, r):
        result = super()._response( r)
        if isinstance( result, bytes):
            return transit_loads( result.decode( 'utf8'))  #hope it is utf8 ?
        return result
    may_time = staticmethod( db1.xtdb.may_time)
    _params_valid_time_tx_id = db1.xtdb._params_valid_time_tx_id
    id_name = db1.xtdb.id_name
    id_kw   = db1.xtdb.id_kw
    kw_query = edn_format.Keyword( 'query')
    kw_in_args = edn_format.Keyword( 'args')


    ##### rpc methods
    debug = 1
    def status( me): return me._get( 'status')
    def latest_completed_tx( me): return me.status()[ 'latestCompletedTx' ]
    def latest_submitted_tx( me): return me.status()[ 'latestSubmittedTx' ]
    def swagger_json( me): return me._get( 'swagger.json')

    def query_post( me, query, *in_args, keyword_keys =False, **ka):
        query = { me.kw_query: query
            #, args= [ 23 ]
            }
        query = transit_dumps( query)
        return db1.xtdb_read.query_post( me, query, *in_args, keyword_keys =keyword_keys, **ka)

    #query_post = db1.xtdb_read.query_post
    query_post_headers = _headers_base
        #return me._post( 'query' if not me.is_v2 else 'datalog',
    query = query_post

class xtdb2( xtdb2_read):
    def submit_tx( me, docs, tx_time =None, put_valid_time =None, put_end_valid_time =None):
        #TODO inside-doc valid/end-time that may or may not be funcs

        #valid_time/end_valid_time works via json ; tx_time does not
        valid_time, end_valid_time, tx_time = (
            me.may_time( x) and me.datetime_param_converter( x)
            for x in (put_valid_time, put_end_valid_time, tx_time)
            )

        if isinstance( docs, dict): docs = [ docs ]
        assert isinstance( docs, (list,tuple)), docs
        for d in docs:
            assert isinstance( d, (dict,list,tuple)), d

        docs = [ me.make_tx_put( d, valid_time= valid_time, end_valid_time= end_valid_time )
                            if isinstance( d, dict) else list( d)
                    for d in docs ]
        for d in docs:
            assert d[0] in me._transaction_types, d[0]

        kargs = {}
        #tx-type tablename ..all-else..
        docs = [ [ edn_format.Keyword( x) for x in d[:2] ] + d[2:] for d in docs ]    #keywordize
        ops = {'tx-ops': docs }     #XXX assume auto key->keyword
        #ops[ 'opts' ] = {}         #general for whole tx
        data = transit_dumps( ops)
        _headers_content_tjson = { 'content-type'  : me._app_transit_json }
        kargs.update( headers= _headers_content_tjson)

        return me._post( 'tx',
                data= data,
                **kargs)

    write = save = tx = submit_tx

    _transaction_types = 'put delete erase call put-fn'.split()    #call = v1.fn ; erase = v1.evict
    _check_tx_end_valid_time = db1.xtdb._check_tx_end_valid_time
    def make_tx_put( me, doc, valid_time =None, end_valid_time =None, table ='atablename'):
        r = db1.xtdb.make_tx_put( me, doc, valid_time, end_valid_time, as_json= False)
        return [ 'put', table, *r[1:]]
    @classmethod
    def make_tx_del( me, eid, valid_time =None, end_valid_time =None, table ='atablename'):
        r = super().make_tx_del( eid, valid_time, end_valid_time)
        return [ 'delete', table, *r[1:]]
    @classmethod
    def make_tx_erase( me, eid, valid_time =None, end_valid_time =None, table ='atablename'):
        r = me.make_tx_del( eid, valid_time, end_valid_time, table)
        return [ 'erase', *r[1:]]
    @staticmethod
    def make_tx_func_decl( funcname, body):
        if isinstance( funcname, str): funcname = qs.kw( funcname)
        assert qs.is_keyword( funcname), funcname
        return [ 'put-fn', funcname, *args ]
    @staticmethod
    def make_tx_func_use( funcname, *args):
        if isinstance( funcname, str): funcname = qs.kw( funcname)
        assert qs.is_keyword( funcname), funcname
        return [ 'call', funcname, *args ]



# vim:ts=4:sw=4:expandtab
