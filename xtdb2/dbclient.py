from base.rpc_json_http import BaseClient, log #dict_without_None
#XXX TODO does it need further hacks ? .. see dbclient.RESULT_EDN
import pprint
import datetime
from io import StringIO

if 0:
  class List( tuple):
    def __new__( me, *a):
        return super().__new__( me, a)
  class XTQLop( List):
    pass

from dataclasses import dataclass
@dataclass
class tx_key:
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
        return tx_key( tx_id= x[ 'tx-id'], system_time= x[ 'system-time'])

dt_tag = 'time/instant'

from transit.transit_types import TaggedValue, Keyword, Symbol

def tagval_repr( me):
    return me.tag+'::::\n   '+pprint.pformat( me.rep).replace('\n','\n   ')
if TaggedValue.__repr__ is not tagval_repr:
    TaggedValue.__repr__ = tagval_repr

def transit_dumps( x):
    from transit.writer import Writer
    from transit.write_handlers import KeywordHandler, MapHandler, VerboseDateTimeHandler
    buf = StringIO()
    w = Writer( buf, 'json' )
    if 0:
      class KeywordHandler2( KeywordHandler):
        @staticmethod
        def rep(k): return k.name
        string_rep = rep

    class MapHandler2( MapHandler):
        @staticmethod
        def rep(m):
            return dict( (Keyword( k) if not isinstance( k, Keyword) else k,v)
                    for k,v in m.items())
    w.register( dict,  MapHandler2 )

    class dtHandler( VerboseDateTimeHandler):
        @staticmethod
        def tag(_): return dt_tag
    w.register( datetime.datetime, dtHandler)

    class ListHandler:
        @staticmethod
        def tag(_): return 'list'
        @staticmethod
        def rep(s): return list(s)
    if 1:
        #w.register( List,  ListHandler)     #tuple==list==array/vector
        w.register( tuple, ListHandler)     #tuple -> xtdb/list i.e. sequence ; list -> vector

    if 0:
      class XTQLopHandler:
        @staticmethod
        def tag(s): return 'xtdb.tx/'+s[0]
        @staticmethod
        def rep(s): return s[1]
      w.register( XTQLop, XTQLopHandler)

    w.register( tx_key, txkey_handler)

    w.write( x )
    value = buf.getvalue()
    print( '\n  '.join( ['tj-dump',
        'in: '+ str(x),
        'out: '+ value,
        'und:'+ str( transit_loads( value)),
        ]))
    return value

from transit.decoder import Decoder
if not hasattr( Decoder, '_decode_list'):
    from collections.abc import Mapping
    def decode_list(self, node, cache, as_map_key):
        r = self._decode_list( node, cache, as_map_key)
        if isinstance( r, Mapping):
            r = r.__class__( (k.str if isinstance( k, Keyword) else k, v)  for k,v in r.items())
        return r
    Decoder._decode_list = Decoder.decode_list
    Decoder.decode_list = decode_list

def transit_loads( x, multi =False):
    from transit.reader import Reader
    #x = x.decode( 'utf8')      #hope it's utf8 XXX
    if multi:
        x = '[' + x.replace( '] [', '],[') + ']'    #jsonize a space-delimited stream of jsons XXX
    buf = StringIO( x)
    r = Reader( protocol= 'json')
    from transit.read_handlers import DateHandler
    r.register( dt_tag, DateHandler)
    r.register( txkey_handler._tag, txkey_handler)

    if 0:
        class MapHandler:
            @staticmethod
            def from_rep( cmap):    #CmapHandler
                return transit_types.frozendict(pairs(cmap))
        r.register( 'cmap', MapHandler)

    rr = r.read( buf)
    #rr = list( r.readeach( buf))   #hangs forever
    return rr

#sym_pipeline = Symbol( '->')

class xtdb2_read( BaseClient):
    '''
    https://docs.xtdb.com/reference/main.html
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

    if 0:
      def _response( me, r, tj_multi =False):
        result = super()._response( r)
        if isinstance( result, bytes):
            return transit_loads( result.decode( 'utf8'), multi= tj_multi)  #hope it is utf8 ?
        return result

    id_name = 'xt/id'       #use in objs/dicts i/o data , in json
    id_sql  = id_name.replace( '/', '$')
    id_kw   = Keyword( id_name)

    ##### rpc methods
    debug = 1
    def status( me): return me._get( 'status')
    def latest_completed_tx( me): return me.status()[ 'latestCompletedTx' ]
    def latest_submitted_tx( me): return me.status()[ 'latestSubmittedTx' ]
    def openapi_yaml( me): return me._get( 'openapi.yaml')

    def query( me, query, *in_args,
                    tz_default =None,
                    valid_time_all =False,
                    #basis = at_tx #as returned in submit_tx
                    #basis-timeout_s    ??
                    #as_json =False,
                    after_tx =None,
                            #TaggedValue( 'xtdb/tx-key', { 'tx-id': 612343,
                                        # 'system-time':
                                            #TaggedValue( 'time/instant',"2024-01-10T11:08:36.422964Z")
                                            #datetime.datetime( 2024, 1, 10, 11, 8, 36, 422964, tzinfo =datetime.UTC)
                    **ka):
        query = dict( query= query,)
        '''     {
                "query": xtdb/list( (from ..) ),
                "basis": null or { :at-tx: .. },
                "basis-timeout": null, ??
                "args": [ {} ], ??
                "default-all-valid-time?": true,
                "default-tz": null ??
                }
            https://docs.xtdb.com/reference/main/xtql/queries.html
            '''
        if in_args: query[ 'args'] = in_args
        if tz_default: query[ 'default-tz'] = tz_default
        if valid_time_all: query[ 'default-all-valid-time?'] = valid_time_all
        if after_tx: query[ 'after-tx'] = after_tx
        #..

        query = transit_dumps( query)

        assert not in_args  #TODO
        assert not ka       #TODO

        return me._post( 'query',
                data= query,
                ka_response= dict( tj_multi= True),     #XXX if not as_json
                #if as_json: headers= me._headers_json
                )

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
    def submit_tx( me, docs, tz_default =None, tx_time =None, valid_time_from_to =None, as_json =False):
        '''
        tx_time: system-time: overrides system-time for the transaction, mustn’t be earlier than any previous system-time.
        tz_default: default-tz: overrides the default time zone for the transaction
        '''
        #TODO inside-doc valid/end-time that may or may not be funcs
        #TODO SQL is unclear - texts or what
        if 10:
            import datetime
            valid_time_from_to = [ datetime.datetime( 2023, 2, 3, 4, 5, tzinfo= datetime.UTC ), None ]
        valid_time_from_to = valid_time_from_to and [ me.may_time( x) for x in valid_time_from_to ]
        tx_time = me.may_time( tx_time)

        if isinstance( docs, dict): docs = [ docs ]
        assert isinstance( docs, (list,tuple)), docs
        for d in docs:
            assert isinstance( d, dict), d

        txs = [ me.make_tx_put( d, valid_time_from_to= valid_time_from_to)
                 if isinstance( d, dict)
                 else d
                for d in docs ]
        for op,tx in txs:
            assert op in me._transaction_types, op
            table = tx.pop( 'table', None)
            if table: tx[ 'table-name' ] = me._table_as_json( table, as_json)

                 #XTQLop( op, dict...
        txs = [ TaggedValue( 'xtdb.tx/'+op, tx ) for op,tx in txs ]    #xtql-jan24

        ops = { 'tx-ops': txs }     #XXX assume auto key->keyword
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
        insert-into assert-exists assert-not-exists
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
    def _use_valid_time( me, optx, valid_time_from_to =None):
        op,tx = optx
        if valid_time_from_to:
            time_valid_from, time_valid_to = valid_time_from_to
            if time_valid_from:
                tx[ me._time_valid_from ] = time_valid_from
            if time_valid_to:
                tx[ me._time_valid_to ] = time_valid_to
        return optx

    @staticmethod
    def _table_as_json( table, as_json =False):
        if as_json:
            assert isinstance( table, str), table
        else:
            if isinstance( table, str): table = Keyword( table)
            assert isinstance( table, Keyword), table
        return table

    @classmethod
    def make_tx_put( me, doc, *, table ='atablename', **ka):
        assert doc.get( me.id_name), doc    #for json, and always, dicts are auto-keyworded later
        #else: assert doc.get( me.id_kw), doc      #for edn/transit
        tx = [ 'put', dict( table= table, doc= dict( doc ))]
        return me._use_valid_time( tx, **ka)
    @classmethod
    def make_tx_delete( me, eid, *, table ='atablename', **ka):
        'not proven'
        tx = [ 'delete', dict( table= table, eid= eid )]
        return me._use_valid_time( tx, **ka)
    @classmethod
    def make_tx_erase( me, eid, *, table ='atablename', **ka_ignore):
        'not proven'
        return [ 'erase', dict( table= table, eid= eid )]

    #TODO these dont match submit_tx protocol?
    @classmethod
    def make_tx_insert_into( me, query, table ='atablename', **ka):
        '''To specify a valid-time range, the query may return xt/valid-from and/or xt/valid-to columns. If not provided, these will default as per put'''
        table = me._table_as_json( table, **ka)
        return [ 'insert-into', dict( table= table, query= query )]
    @staticmethod
    def make_tx_assert_exists( query):
        return [ 'assert-exists', query ]
    @staticmethod
    def make_tx_assert_notexists( query):
        return [ 'assert-not-exists', query ]

    #TODO : update-table delete-from erase-from

    #these are unclear
    @staticmethod
    def make_tx_func_decl( funcname, body):
        if isinstance( funcname, str): funcname = Keyword( funcname)
        assert isinstance( funcname, Keyword), funcname
        return [ 'put-fn', funcname, body ]
    @staticmethod
    def make_tx_func_use( funcname, *args):
        if isinstance( funcname, str): funcname = Keyword( funcname)
        assert isinstance( funcname, Keyword), funcname
        return [ 'call', funcname, *args ]

# vim:ts=4:sw=4:expandtab
