X_decoder_Keyword = 1

from base.rpc_json_http import BaseClient, log #dict_without_None

####### transit-json stuff

DEBUG = 0

import pprint
import datetime
from io import StringIO
from dataclasses import dataclass

from transit.transit_types import TaggedValue, Keyword, Symbol, frozendict
from transit import transit_types
X_keysym = getattr( transit_types, 'X_keysym', 0)
from transit import write_handlers
#+few others below

if 0:
  class List( tuple):
    def __new__( me, *a):
        return super().__new__( me, a)

@dataclass( frozen =True)
class TX_key_id:
    tx_id: int
    system_time: datetime.datetime

class txkey_handler:
    _tag = 'xtdb/tx-key'
    @classmethod
    def tag(me,_): return me._tag
    @staticmethod
    def rep( x):
        return { 'tx-id': x.tx_id, 'system-time': x.system_time }
    @staticmethod
    def from_rep( x):
        return TX_key_id( tx_id= x.tx_id, system_time= x.system_time)   #see below kebab2snake_case
        #return TX_key_id( tx_id= x[ 'tx-id'], system_time= x[ 'system-time'])

dt_tag = 'time/instant'

def tagval_repr( me):
    return me.tag+'::::\n   '+pprint.pformat( me.rep).replace('\n','\n   ')
if TaggedValue.__repr__ is not tagval_repr:
    TaggedValue.__repr__ = tagval_repr

def pprint_fix_immmutables():
    import pprint
    #see svdt_util/dicts.fix_pprint_dict
    pprint.PrettyPrinter._dispatch[ frozendict.__repr__] = pprint.PrettyPrinter._dispatch[ dict.__repr__]
    #also safe_repr?
pprint_fix_immmutables()

if not getattr( write_handlers, 'X_wHandler', 0):
 class wMapHandler_auto_keywordize( write_handlers.MapHandler):
    @staticmethod
    def rep(m):
        return { Keyword( k) if k.__class__ is not Keyword else k:v
                    for k,v in m.items() }
        return dict( (Keyword( k) if not isinstance( k, Keyword) else k,v)
                for k,v in m.items())
        #return dict( (Keyword( k) if k.__class__ is not Keyword else k,v)
 class wDatetimeHandler( write_handlers.VerboseDateTimeHandler):
    @staticmethod
    def tag(_): return dt_tag

 class wListHandler:
    @staticmethod
    def tag(_): return 'list'
    rep = list

else:
    wHandler = write_handlers.wHandler
    wMapHandler_auto_keywordize = wHandler.copy( write_handlers.MapHandler,
        rep= lambda m: {
                    (Keyword( k) if k.__class__ is not Keyword else k):v
                    for k,v in m.items() }
        )
    wDatetimeHandler = wHandler.copy( write_handlers.VerboseDateTimeHandler,
        tag= dt_tag
        )
    wListHandler = wHandler( tag= 'list',
        rep= list,
        str= write_handlers.rep_None
        )

def transit_dumps( x):
    from transit.writer import Writer
    buf = StringIO()
    w = Writer( buf, 'json' )
    w.register( dict, wMapHandler_auto_keywordize )
    w.register( datetime.datetime, wDatetimeHandler)
    if 1:
        #w.register( List, wListHandler)     #tuple==list==array/vector
        w.register( tuple, wListHandler)     #tuple -> xtdb/list i.e. sequence ; list -> vector

    w.register( TX_key_id, txkey_handler)

    w.write( x )
    value = buf.getvalue()
    if DEBUG:
        print( '\n  '.join( ['tj-dump',
        'in: '+ str(x),
        'out: '+ value,
        'und:'+ str( transit_loads( value)),
        ]))
    value = value.encode( 'utf8')
    return value

#auto de-keywordize dicts, also kebab2snake_case
from transit.decoder import Decoder
from transit import decoder
X_mapkeystr = getattr( decoder, 'X_mapkeystr', 0)
frozendict.__getattr__ = frozendict.__getitem__

if X_mapkeystr:
    class rh_mapkeystr:
        @staticmethod
        def from_rep(v):
            return v.replace( '-', '_')
    decoder.default_options['decoders']['mapkeystr'] = rh_mapkeystr

elif not hasattr( Decoder, '_decode_list'):
    from collections.abc import Mapping
    def decode_list(self, node, cache, as_map_key):
        r = self._decode_list( node, cache, as_map_key)
        if isinstance( r, Mapping):
            if X_decoder_Keyword and X_keysym:
                r = r.__class__( ((k.__str__() if k.__class__ is Keyword else k).replace( '-', '_'), v)
                #r = r.__class__( ((str(k) if k.__class__ is Keyword else k).replace( '-', '_'), v)
                    for k,v in r.items())
            elif X_decoder_Keyword:
                r = r.__class__( ((k.str if k.__class__ is Keyword else k).replace( '-', '_'), v)
                    for k,v in r.items())
            else:
                r = r.__class__( ((k.str if isinstance( k, Keyword) else k).replace( '-', '_'), v)
                    for k,v in r.items())
        return r
    Decoder._decode_list = Decoder.decode_list
    Decoder.decode_list = decode_list

ijson=10
if ijson:
    import ijson        # https://pypi.org/project/ijson/
    print( 'ijson:', ijson.backend)
    rdr = Decoder()
    def readeach( input, multi =True):
        for o in ijson.items( input, prefix= '', multiple_values= multi):
            yield rdr.decode( o)
else:
    from transit.reader import Reader
    rdr = Reader( protocol= 'json')

from transit.read_handlers import DateHandler
rdr.register( dt_tag, DateHandler)
rdr.register( txkey_handler._tag, txkey_handler)
if 0:
    class rMapHandler:
        @staticmethod
        def from_rep( cmap):    #CmapHandler
            return frozendict(pairs(cmap))
    rdr.register( 'cmap', rMapHandler)


def transit_loads( x, multi =False):
    if not x: return
    if ijson:
        r = list( readeach( x, multi= multi))
        if not multi: return r[0]
        return r

    #x = x.decode( 'utf8')      #hope it's utf8 XXX
    #if 0: return list( rdr.readeach( StringIO( x)))   #hangs forever XXX

    if multi: #naively jsonize a space-delimited stream of jsons XXX
        xx = x.split( '] [')    #try.. many lists?
        if len(xx) < 2: multi = False   #nah, single
        xx = xx[:1] + ['['+a for a in xx[1:]]
        xx = [a+']' for a in xx[:-1]] + xx[-1:]
    else: xx = [ x ]

    rr = [ rdr.read( StringIO( a)) for a in xx ]
    if not multi: return rr[0]
    return rr

#sym_pipeline = Symbol( '->')

class xtdb2_read( BaseClient):
    '''
    https://docs.xtdb.com/reference/main.html
    XXX no luck in docs? some inspiration: <v2-branch>/api/src/main/clojure/xtdb/api.clj
    ./v2/openapi.yaml
    TODO: sql
    '''
    _app_transit_json = 'application/transit+json'
    _headers_content_tjson = { 'content-type': _app_transit_json }
    _headers_base = dict(
        _headers_content_tjson,
        #'accept' : BaseClient._app_json,   #text/plain text/html
        #**BaseClient._headers_content_json,
        accept= _app_transit_json,
        )
    _headers_json = dict(
        BaseClient._headers_content_json,
        accept= BaseClient._app_json,
        )

    id_name = 'xt/id'       #use in objs/dicts i/o data , in json
    id_sql  = id_name.replace( '/', '$')

    txs_table = 'xt/txs'    #special table containing states of all transactions

    ##### rpc methods
    debug = 0
    def status( me): return me._get( 'status')
    def latest_completed_tx( me): return me.status().latest_completed_tx
    def latest_submitted_tx( me): return me.status().latest_submitted_tx
    def openapi_yaml( me): return me._get( 'openapi.yaml')

    def query( me, query, *, args ={},
                    tz_default =None,       #= #time/zone "America/Los_Angeles" or "Z" , maybe a java.time/zone like
                    valid_time_is_all   =False, # default-all-valid-time?
                    after_tx :TX_key_id =None,  # as returned from submit_tx
                    at_tx    :TX_key_id =None,  # as returned from submit_tx ; overrides after_tx ; basis
                    current_time        =None,  # the-now-to-use ; basis
                    #basis   :dict = None
                    #   at_tx: as returned from submit_tx
                    #   current-time: the-now-to-use
                    explain= False,
                    tx_timeout_s :int =None,    # for after_tx/at_tx
                    #as_json =False,
                    ):
        ''' https://docs.xtdb.com/reference/main/xtql/queries.html
        '''
        assert isinstance( query, (str, tuple)), query
        query = dict( query= query,)
        if args:
            assert isinstance( args, dict), args
            query[ 'args'] = args
        if tz_default: query[ 'default-tz'] = tz_default    #??? TaggedValue( 'time/zone', 'Pacific/Fiji')
        if valid_time_is_all: query[ 'default-all-valid-time?'] = bool( valid_time_is_all)
        if explain: query[ 'explain?'] = bool( explain)
        if after_tx:
            assert isinstance( after_tx, TX_key_id), after_tx   #.. but can be TaggedValue too
            query[ 'after-tx'] = after_tx
        if at_tx:
            assert isinstance( at_tx, TX_key_id), at_tx         #.. but can be TaggedValue too
            query.setdefault( 'basis', {}).update( { 'at-tx': at_tx })
        if current_time:
            assert isinstance( current_time, datetime.datetime), current_time
            query.setdefault( 'basis', {}).update( { 'current-time': current_time })
        if tx_timeout_s:
            assert isinstance( tx_timeout_s, int), tx_timeout_s
            query[ 'tx-timeout'] = TaggedValue( 'time/duration', f'PT{tx_timeout_s}S')

        #assert not ka, ka

        query = transit_dumps( query)
        return me._post( 'query',
                data= query,
                ka_response= dict( tj_multi= True),     #XXX if not as_json
                #if as_json: headers= me._headers_json
                )
    #XXX HACK! XXX
    def sync( me, table =None, n =1):
        if table: q = (Symbol('->'), (Symbol('from'), Keyword( table), [ Symbol('*') ]), (Symbol('limit'), n))
        else: q = (Symbol('rel'), [], [])
        return me.query( q, after_tx= me.latest_submitted_tx(), tx_timeout_s= 55)

    def _content( me, r, tj_multi =False, **ka):
        contentype = r.headers.get( 'content-type', '')
        if me._app_transit_json in contentype:
            return transit_loads( r.text, multi= tj_multi)  #decode? utf-8? XXX
        return super()._content( r, **ka)

    def _post( me, *a,**ka):
        try:
            return super()._post( *a,**ka)
        except RuntimeError as e:
            r = e.response
            cooked = me._content( r)    #no multi here XXX
            if cooked:
                text = str( cooked)
                e.args = ( e.args[0] + '\n>>>> '+text.replace('\n','\n>>')+'\n', *e.args[1:] )
            raise

class xtdb2( xtdb2_read):
    def submit_tx( me, docs,
                    table =None,                # the default for put, ignored for all else
                    valid_time_from_to =None,   # the default for put, ignored for all else
                    tz_default =None,
                    tx_time =None,
                    as_json =False
                    ):
        ''' https://docs.xtdb.com/reference/main/xtql/txs.html
        tx_time   = system-time: overrides system-time for the transaction, mustn’t be earlier than any previous system-time.
        tz_default= default-tz: overrides the default time zone for the transaction
        table + valid_time_from_to - defaults for making tx_puts from docs if dicts
        '''

        #TODO inside-doc valid/end-time that may or may not be funcs
        #TODO SQL is unclear - texts or what
        if 0:
            valid_time_from_to = [ datetime.datetime( 2023, 2, 3, 4, 5, tzinfo= datetime.UTC ), None ]
        valid_time_from_to = valid_time_from_to and [ me.may_time( x) for x in valid_time_from_to ]
        tx_time = me.may_time( tx_time)

        if isinstance( docs, dict): docs = [ docs ]
        assert isinstance( docs, (list,tuple)), docs

        txs = [ d if not isinstance( d, dict) else
                me.make_tx_put( d, table= table, valid_time_from_to= valid_time_from_to)
                for d in docs ]
        for op,tx in txs:
            assert op in me._transaction_types, op
            if isinstance( tx, dict):
                table = tx.pop( 'table', None)
                if table: tx[ 'table-name' ] = me._table_as_json( table, as_json)

        txs = [ TaggedValue( 'xtdb.tx/'+op if 'xtql' not in tx else 'xtdb.tx/xtql'
                    , tx ) for op,tx in txs ]    #xtql-jan24

        ops = { 'tx-ops': txs }
        if tx_time or tz_default:   #general for whole tx
            ops[ 'opts' ] = {
                'system-time': tx_time,     #XXX XTQL only?
                'default-tz':  tz_default,  #XXX XTQL only?
                #'default-all-valid-time?': bool # XXX ? SQL only??
                }
        data = transit_dumps( ops)
        return me._post( 'tx',
                data= data,
                #if as_json: headers= me._headers_json
                )

    write = save = tx = submit_tx

    _transaction_types = '''
        put delete erase
        insert
        assert-exists assert-not-exists
        call put-fn
        '''.split()    #call = v1.fn ; erase = v1.evict
        ##update-table delete-from erase-from

    _time_valid_from  = 'valid-from'
    _time_valid_to    = 'valid-to'
    @staticmethod
    def _kw_as_json( name, as_json):
        if as_json: return name
        return Keyword( 'xt/'+name)
    @classmethod
    def _use_valid_time( me, optx, valid_time_from_to =None, as_json =False):
        op,tx = optx
        if valid_time_from_to:
            time_valid_from, time_valid_to = valid_time_from_to
            if as_json: raise NotImplemented
            if time_valid_from:
                tx[ me._time_valid_from ] = time_valid_from
            if time_valid_to:
                tx[ me._time_valid_to ] = time_valid_to
        return optx

    _table_name = 'table-name'
    @classmethod
    def _use_table( me, optx, table, as_json =False):
        op,tx = optx
        assert table and isinstance( table, str), table
        if as_json:
            raise NotImplemented
        else:
            tx[ me._table_name ] = Keyword( table)
        return optx


    #TODO: put/delete/delete-from/update-table operations
    #      can be passed to `during`, `starting-from` or `until` to set the effective valid time of the operation.
    #       or ??? can use valid_time_from_to like `put` does ?? XXX


    @classmethod
    def make_tx_put( me, doc, *, table, valid_time_from_to =None, as_json =False):
        'put: one = upsert'
        assert doc.get( me.id_name), doc    #always, dicts are auto-key2keyworded later
        tx = [ 'put', dict( doc= dict( doc ))]  #copy.. just in case?
        me._use_table( tx, table, as_json)
        return me._use_valid_time( tx, valid_time_from_to, as_json)
    @classmethod
    def make_tx_delete( me, xtid, *, table, valid_time_from_to =None, as_json =False):
        'delete: one'
        tx = [ 'delete', { me.id_name: xtid }]
        me._use_table( tx, table, as_json)
        return me._use_valid_time( tx, valid_time_from_to, as_json)
    @classmethod
    def make_tx_erase( me, xtid, *, table, as_json =False):
        'erase: one completely, all valid time'
        assert table and isinstance( table, str), table
        tx = [ 'erase', { me.id_name: xtid }]
        return me._use_table( tx, table, as_json)

    @staticmethod
    def make_tx_insert_many( query, *, table):
        '''insert-into: copy-many-from-query-into-table
            To specify a valid-time range, the query may return xt/valid-from and/or xt/valid-to columns. If not provided, these will default as per put'''
        assert table and isinstance( table, str), table
        op = 'insert'   #hmmm, it's not ..-into
        return [ op, dict( xtql= (Symbol( op), Keyword( table), query ))]

    @staticmethod
    def make_tx_assert_exists( query):
        'stop transaction if fails'
        op = 'assert-exists'
        return [ op, dict( xtql= (Symbol( op), query)) ]
    @staticmethod
    def make_tx_assert_notexists( query):
        'stop transaction if fails'
        op = 'assert-not-exists'
        return [ op, dict( xtql= (Symbol( op), query)) ]

    #TODO
    #update_many = xtql, (update table opts unify_clauses)
    #delete_many = xtql, (delete table bind-or-opts unify_clauses)
    #erase_many  = xtql, (erase  table bind-or-opts unify_clauses)

    #these are unclear, untested
    @staticmethod
    def make_tx_func_decl( funcname, body):
        assert funcname and isinstance( funcname, str), funcname
        assert body     and isinstance( body, str), body
        return [ 'putFn', { 'fn-id': Keyword( funcname), 'tx-fn': body } ]  #maybe
    @staticmethod
    def make_tx_func_call( funcname, *args):
        assert funcname and isinstance( funcname, str), funcname
        return [ 'call', { 'fn-id': Keyword( funcname), 'args': args } ]  #maybe

# vim:ts=4:sw=4:expandtab
