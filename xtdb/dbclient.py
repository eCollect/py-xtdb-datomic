from base.rpc_edn_json_http import BaseClient, dict_without_None, hacks, log
import edn_format
kw = edn_format.Keyword
from edn_format import dumps as edn_dumps
import datetime, json

RESULT_EDN = True

if RESULT_EDN:
    #make it equivalent to json
    def kebab2camel_skip_system_no_colon( k):
        k = k.name  #without the initial ':'
        return hacks.kebab2camel( k, skip_first_level= k.startswith('xtdb.api/'))
    def keyword_into_str_kebab2camel( k):
        return kebab2camel_skip_system_no_colon( k) if isinstance( k, edn_format.Keyword) else k
    hacks.edn_response_Keyword_into_str( maps_keys= True, maps_values= True, lists= True, keyword_into_str= keyword_into_str_kebab2camel)
    edn_format.add_tag( 'xtdb/id', lambda name: name )
    hacks.pprint_fix_immmutables()  #not really needed but..
    #TODO json has no tuples ; so tuples in EDN would be lists in json - e.g. outmost result of query

hacks.edn_accept_naive_datetimes()  #tx-as-json

def transit_dumps( x):
    #print( 333333, x)
    import collections.abc
    for c in 'MutableMapping Mapping Hashable'.split():
        setattr( collections, c, getattr( collections.abc, c))
    from transit.writer import Writer
    from transit.write_handlers import KeywordHandler, SymbolHandler, MapHandler
    from transit.transit_types import Keyword, Symbol
    from io import StringIO
    io = StringIO()
    w = Writer( io, 'json' )
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
    w.write( x )
    return io.getvalue()


class xtdb_read( BaseClient):
    ''' bitemporal append-only-db-in-clojure, graph
    https://docs.xtdb.com/clients/http/
    https://docs.xtdb.com/clients/http/openapi/1.22.1/      beware, this has more stuff than above
    - All endpoints with query-parameters accept them in both kebab-case and camel-case, i.e. valid-time / validTime (without : prefix)
    - query-parameters expect bools as true/false, datetimes as iso-string ; if no +-timezone then always UTC - with or without Z !
    - edn takes/returns :kebab-case, :kebab-case/kebab-case and in particular, :xtdb.api/kebab-case for system-namespace
    - while json takes/returns camelCase, camelCase/camelCase, and camelCase for system (without :xtdb.api/ system-namespace prefix)
    - all input or output datetimes are UTC !
    '''
    #TODO
    '''TODO more:
    - returned json is camelcase.. sent json/edn is kebab-case..
    - errors return edn -> loads ???
    - submit_tx via edn ?
    - decide on camel vs kebab.. case

    - ?? rest-api-docs have extra method: DB( _params_valid_time_tx_id)
    - ?? entity & query rest-api-docs have extra param: link-entities? : boolean
    + check proper input values for True, None etc
    - tests
    '''

    #params validators
    @staticmethod
    def is_time( x):
        assert isinstance( x, datetime.datetime), x
        return x
    @staticmethod
    def may_time( x):
        assert x is None or isinstance( x, datetime.datetime), x
        return x
    is_tx_id  = staticmethod( BaseClient.is_int)
    may_tx_id = staticmethod( BaseClient.may_int)

    @staticmethod
    def datetime_param_converter( v):
        #v = v.astimezone()
        return v.isoformat( timespec= 'milliseconds')
        #XXX if needed:
        #localtz = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
        #https://stackoverflow.com/questions/2720319/python-figure-out-local-timezone

    @classmethod
    def _param_timeout_ms( me, timeout_ms):
        return dict( timeout= me.may_int_positive( timeout_ms))

    @staticmethod
    def _params_eid( eid =None, eid_edn =None, eid_json =None, **ka):
        ''' eid=.. if non-str, is moved + edn_dumps into eid_edn ;
        while eid_edn/eid_json are passed as-is - NOT auto-dumps - DIY.
        see tests of .entity: param -> final-url -> xt-wise:
        eid="5"      -> ...?eid=5      which means str="5"
        eid=5        -> ...?eid-edn=5  which means int=5
        eid=datetime -> ...?eid-edn=#inst...  which means datetime
        eid_edn="5"  -> ...?eid-edn=5  which means int=5 XXX
        eid_edn="x5" -> ...?eid-edn=x5 which means symbol XXX
        eid_edn=kw.x -> ...?eid-edn=Keyword(x) which means syntax-err
        '''
        eid_params0 = dict( eid= eid, eid_edn= eid_edn, eid_json= eid_json, )
        eid_params = dict_without_None( eid_params0)
        assert len( eid_params) == 1, f'needs exactly one of {eid_params0}'
        assert list( eid_params.values())[0], f'needs non-empty value {eid_params}'
        if eid and not isinstance( eid, str):
            eid_params = dict( eid_edn= edn_dumps( eid))
        return ( eid_params, ka)
    @classmethod
    def _params_valid_time_tx_id( me, **ka):
        return ( me._params_taker( ka,
            valid_time  = me.may_time,    #(date/string, defaulting to now)
            tx_time     = me.may_time,    #(date/string, defaulting to latest transaction time)
            tx_id       = me.may_tx_id,   #(int64, defaulting to latest transaction id)
            ), ka)

    ######

    _headers_base = {
        #'accept' : BaseClient._app_json,   #text/plain text/html
        'accept' : BaseClient._app_edn if RESULT_EDN else BaseClient._app_json,   #text/plain text/html
        **BaseClient._headers_content_json,
        }

    is_v2 = False
    def url( me, url ):
        if me.is_v2:
            return super().url( url )           #v2
        return super().url( '_xtdb', url )      #v1

    def __init__( me, rooturl, *, v2 =False, **ka):
        super().__init__( rooturl, **ka)
        me.is_v2 = bool( v2)

    ##### rpc methods

    def status( me): return me._get( 'status')
    def stats( me):  return me._get( 'attribute-stats')
    def latest_completed_tx( me):
        if me.is_v2:
            return me.status()[ kw( 'latest-completed-tx' ) ]
        return me._get( 'latest-completed-tx' )
    def latest_submitted_tx( me):
        if me.is_v2:
            return me.status()[ kw( 'latest-submitted-tx' ) ]
        return me._get( 'latest-submitted-tx' )
    def active_queries     ( me): return me._get( 'active-queries'      )
    def recent_queries     ( me): return me._get( 'recent-queries'      )
    def slowest_queries    ( me): return me._get( 'slowest-queries'     )
    def swagger_json       ( me): return me._get( 'swagger.json'        )

    kw_query = edn_format.Keyword( 'query')
    kw_in_args = edn_format.Keyword( 'in-args')
    def query_post( me, query, *in_args, post =True, keyword_keys =False, **ka):
        ''' POST /_xtdb/query
        https://docs.xtdb.com/clients/http/#post-query
        input data is edn-only; like { :query ... , :in-args ...values-optional }
        '''
        params_vti, ka = me._params_valid_time_tx_id( **ka)
        #XXX these DO NOT override whatever inside query ; TODO: override , incl. =None!
        params_other = dict_without_None( me._params_taker( ka,
            limit = me.may_int_positive,     # Number of results to return (optional)
            offset= me.may_int_positive,     # First result to return (optional)
            timeout_ms = me.may_int_positive,
            ))
        me._check_unknown_params( ka)
        if isinstance( query, dict):
            from xtdb import qsyntax
            query = qsyntax.qbuilder( query)   #copy+check
            in_spec = query.match_args_to_spec( in_args)

            #move limit etc into query
            for k,v in params_other.items():
                getattr( query, k)( v)

            data = { me.kw_query: query }
            if in_args:
                data[ me.kw_in_args ] = qsyntax.vector( in_args)
            data = edn_dumps( data, keyword_keys= keyword_keys)
        else:   #XXX must be complete, all-inside
            assert isinstance( query, str), query   #assume all is inside query-str
            assert ':query' in query, query         #XXX with :query outmost-level
            assert not in_args, f'cannot have text-query with separate {in_args=}'    #assume all is inside query-str
            assert not params_other, f'cannot have text-query with separate limit/offset/timeout {params_other}'    #assume all is inside query-str
            data = query

        assert isinstance( data, str), data
        return me._post( 'query' if not me.is_v2 else 'datalog',
                data= data,
                **me._params( **params_vti),
                headers= me._headers_content_edn )
    query = query_post
    if 0:
        def query_get( me, query, in_args ={}, **ka):
            ''' GET /_xtdb/query?query-edn=url-encoded-query-edn&in-args-edn= or &in-args-json=
            https://docs.xtdb.com/clients/http/#get-query
            query data is edn-only; like { :find .. } ; in-args can be edn or json
            '''
            assert 0

    def sync( me, timeout_ms =None):
        'Wait until the Kafka consumer lag is back to 0 (i.e. when it no longer has pending transactions to write). Returns the transaction time of the most recent transaction.'
        if me.is_v2: return
        return me._get( 'sync', **me._params(
                    **me._param_timeout_ms( timeout_ms)))
    def await_tx_id( me, tx_id, timeout_ms =None):
        'Wait until the node has indexed a transaction that is past the supplied tx-id. Returns the most recent tx indexed'
        return me._get( 'await-tx', **me._params(
                    tx_id= me.is_tx_id( tx_id),
                    **me._param_timeout_ms( timeout_ms )))
    await_tx = await_tx_id
    def await_tx_time( me, tx_time, timeout_ms =None):
        ''' https://docs.xtdb.com/clients/http/#await-tx-time
        Wait until the node has indexed a transaction that is past the supplied tx-time. Returns the most recent tx indexed'''
        return me._get( 'await-tx-time', **me._params(
                    tx_time= me.is_time( tx_time),
                    **me._param_timeout_ms( timeout_ms )))
    def tx_log( me, after_tx_id =None, with_ops =None):
        '''Get list of all transactions
        with_ops = with-operations
        '''
        return me._get( 'tx-log', **me._params(**{
                    'after_tx_id': me.may_tx_id( after_tx_id),
                    'with_ops?':   me.may_bool( with_ops),
                    }))
    def tx_committed( me, tx_id ):
        'Checks if a submitted transaction was successfully committed -> bool'
        rdict = me._get( 'tx-committed', **me._params(
                    tx_id= me.is_tx_id( tx_id) ))
        ##json { "txCommitted?": true } ; edn: {:tx-committed? true} XXX
        return rdict[ 'txCommitted?' ]  #ok for RESULT_EDN with keyword_into_str_kebab2camel

    def entity( me, eid =None, **ka):
        ''' GET /_xtdb/entity?...
        Get document-map for an entity
        https://docs.xtdb.com/clients/http/#entity
        https://docs.xtdb.com/clients/http/openapi/1.22.1/#/paths/~1_xtdb~1entity/get
        eid=.. is only for String IDs
        '''
        params_eid, ka = me._params_eid( eid= eid, **ka)
        params_vti, ka = me._params_valid_time_tx_id( **ka)
        me._check_unknown_params( ka)
        return me._get( 'entity', **me._params( **params_eid, **params_vti))

    def entity_tx( me, eid =None, **ka):
        'Get (last) transaction details for an entity - like tx-id and tx-timeinfo'
        params_eid, ka = me._params_eid( eid= eid, **ka)
        params_vti, ka = me._params_valid_time_tx_id( **ka)
        me._check_unknown_params( ka)
        return me._get( 'entity-tx', **me._params( **params_eid, **params_vti))

    def entity_history( me, eid =None, ascending =False, auto_inclusive_tx_id =False, **ka):
        ''' GET /_xtdb/entity?history=true...
        get history for an entity.
        https://docs.xtdb.com/clients/http/#entity-history
        https://docs.xtdb.com/language-reference/datalog-queries/#history-api
        https://docs.xtdb.com/clients/http/openapi/1.22.1/#/paths/~1_xtdb~1entity/get
        also see get-start-valid-time and get-end-valid-time predicates

        Beware: docs ...http/#entity-history say: start=incl, end=excl (and it works so)
        but docs ...datalog-queries/#history-api say: "All coordinates are inclusive."

        also : see testdb/time.check() about history..
            to filter inclusively by txid [tx1..tx2] where tx1<tx2,
            with sort_order=asc: start=tx1 , end=tx2+1 ;
            but with sort_order=desc: start=tx2, end=tx1-1
        '''
        params_eid, ka = me._params_eid( eid= eid, **ka)
        params_other = me._params_taker( ka,
            with_docs        =me.may_bool,      #boolean =false: includes the documents in the response sequence, under the doc key
            with_corrections =me.may_bool,      #boolean =false: includes bitemporal corrections in the response, inline, sorted by valid-time then tx-id
            start_valid_time =me.may_time,
            start_tx_time    =me.may_time,
            start_tx_id      =me.may_tx_id,     # (inclusive, default unbounded): bitemporal co-ordinates to start at
            end_valid_time   =me.may_time,
            end_tx_time      =me.may_time,
            end_tx_id        =me.may_tx_id,     # (exclusive, default unbounded): bitemporal co-ordinates to stop at
            )
        me._check_unknown_params( ka)
        sort_order = 'asc' if ascending else 'desc'
        #sort_order = { '+': 'asc', '-': 'desc' }.get( sort_order, sort_order)
        assert sort_order in ['desc', 'asc'], sort_order

        # see testdb/time.check() about history..
        if auto_inclusive_tx_id: #autocorrect for asc/desc
            if not ascending:
                swap = dict( start_tx_id= 'end_tx_id', end_tx_id= 'start_tx_id')
                params_other = dict( (swap.get(k,k),v) for k,v in params_other.items())
            if params_other['end_tx_id'] is not None:
                params_other['end_tx_id'] += (1 if ascending else -1)  #exclusive

        return me._get( 'entity',
                **me._params( history= True, sort_order= sort_order, **params_eid, **params_other,))

    #each document MUST have xt/id key
    #XXX further sub-struct levels may have that too but it is just data there (tested)
    id_name = 'xt/id'       #use in objs/dicts i/o data , in json
    id_kw   = edn_format.Keyword( id_name)

    #system-namespace
    ns_api_name = 'xtdb.api/'       #use in json
    @classmethod
    def ns_api_kw( klas, name):
        return edn_format.Keyword( klas.ns_api_name + name)

class xtdb( xtdb_read):
    ''' +write
    https://docs.xtdb.com/language-reference/1.22.1/datalog-transactions
    https://docs.xtdb.com/language-reference/1.22.1/datalog-transactions/#document

    note: there are also speculative transactions, but not via http-API: with_tx()
    https://docs.xtdb.com/language-reference/1.22.1/datalog-transactions/#speculative-transactions
    '''
    #TODO
    ''' TODO more
    - submit_tx via edn ?
    - tests
    '''
    def submit_tx( me, docs, tx_time =None, put_valid_time =None, put_end_valid_time =None, as_json =True):
        ''' POST /_xtdb/submit-tx
        https://docs.xtdb.com/clients/http/#submit-tx
        https://docs.xtdb.com/clients/http/openapi/1.22.1/#/paths/~1_xtdb~1submit-tx/post       beware has more stuff than above
        https://docs.xtdb.com/language-reference/1.22.1/datalog-transactions/#transaction-time
        https://docs.xtdb.com/language-reference/1.22.1/datalog-transactions/#transaction-functions
        write; input content can be json or edn
        * json: dates are iso-strings
        * edn: tx-ops/names are like :tx-ops :xtdb.api/put ..
        see also kebab/camel case-trouble above
        '''
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

        if me.is_v2: as_json = False
        docs = [ me.make_tx_put( d, valid_time= valid_time, end_valid_time= end_valid_time, as_json= as_json)
                            if isinstance( d, dict) else list( d)
                    for d in docs ]
        for d in docs:
            assert d[0] in me._transaction_types, d[0]

        kargs = {}
        #TODO edn_dumps+headers
        #XXX returns extra_ok_statuses= [202] processing-offline

        if me.is_v2:    #tx-type tablename ..all-else..
            docs = [ [ edn_format.Keyword( x) for x in d[:2] ] + d[2:] for d in docs ]    #keywordize
            ops = {'tx-ops': docs }     #XXX assume auto key->keyword
            #ops[ 'opts' ] = {}         #general for whole tx
            data = transit_dumps( ops)
            _headers_content_tjson = { 'content-type'  : me._app_json.replace( 'json', 'transit+json') }
            kargs.update( headers= _headers_content_tjson)

        elif as_json:
            ops = {'tx-ops': docs }
            if tx_time:
                assert 0, 'this does not work via json' #TODO below edn_dumps.. then try again
                #tx_time = edn_dumps( tx_time)
                #tx_time = _tx_time.split( '+')[0]+'Z'#_edn_dumps( tx_time)
                ops.update( { me.ns_api_name+'submit-tx-opts': { me.ns_api_name+'tx-time': tx_time }} )
            data = json.dumps( ops )
        else:
            docs = [ [ me.ns_api_kw( d[0]), *d[1:]] for d in docs ]    #keywordize
            ops = { edn_format.Keyword('tx-ops'): docs }
            if tx_time:
                #assert 0, 'this does not work via json' #TODO below edn_dumps.. then try again
                #tx_time = edn_dumps( tx_time)
                #tx_time = _tx_time.split( '+')[0]+'Z'#_edn_dumps( tx_time)
                ops[ me.ns_api_kw('submit-tx-opts') ] = { me.ns_api_kw('tx-time'): tx_time }
            data = edn_dumps( ops)
            kargs.update( headers= me._headers_content_edn )

        return me._post( 'submit-tx' if not me.is_v2 else 'tx',
                data= data,
                **kargs)

    write = save = tx = submit_tx

    _transaction_types = 'put delete match evict fn'.split()
    @classmethod
    def _check_tx_end_valid_time( klas, valid_time =None, end_valid_time =None):
        if end_valid_time:
            #XXX valid_time can be None
            return [ valid_time, end_valid_time ]
        if valid_time:
            return [ valid_time ]
        return []
    #@classmethod
    #def ns_api( klas, name, as_json =True):
    #    if as_json: return name
    #    return klas.ns_api_kw( name)
    #@classmethod
    def make_tx_put( me, doc, valid_time =None, end_valid_time =None, as_json =True):
        ''' https://docs.xtdb.com/language-reference/1.22.1/datalog-transactions/#put
        https://docs.xtdb.com/language-reference/1.22.1/datalog-transactions/#document
        All documents must have xt/id - keyword, str, int, uuid, ..
        https://docs.xtdb.com/language-reference/1.22.1/datalog-transactions/#valid-ids
        no automatics
        #TODO some inside-doc valid/end-time that may or may not be funcs
        '''
        if as_json or 1:
            assert doc.get( me.id_name), doc    #for json
        else:
            assert doc.get( me.id_kw), doc    #for edn
        v2_table = [] if not me.is_v2 else [ 'atablename' ]
        return [ 'put', *v2_table, dict(doc), *me._check_tx_end_valid_time( valid_time, end_valid_time)]
    @classmethod
    def make_tx_del( klas, eid, valid_time =None, end_valid_time =None):
        return [ 'delete', eid, *klas._check_tx_end_valid_time( valid_time, end_valid_time)]
    @classmethod
    def make_tx_match( klas, eid, doc, valid_time =None):
        ''' only-if-matches guard - stops further processing of transaction if not matching.
        https://docs.xtdb.com/language-reference/1.22.1/datalog-transactions/#match
        similar to replace_if_equals/db.cas in datomic
        '''
        return [ 'match', eid, dict(doc), *klas._check_tx_end_valid_time( valid_time, None )]
    @classmethod
    def make_tx_evict( klas, eid ):
        return [ 'evict', eid ]

    @staticmethod
    def make_tx_db_func_decl( funcname, body):
        ''' https://docs.xtdb.com/language-reference/1.22.1/datalog-transactions/#_creating_updating
        https://docs.xtdb.com/language-reference/1.22.1/datalog-transactions/#transaction-functions
        produces document for inside tx ;
        body should be text defined in Clojure
        '''
        if isinstance( funcname, str): funcname = qs.kw( funcname)
        assert qs.is_keyword( funcname), funcname
        #if not isinstance( body, str): body = edn_format.dumps( body)
        return { qs.kw2.xt.id: funcname, qs.kw2.xt.fn: body }
    @staticmethod
    def make_tx_func_use( funcname, *args):
        ''' https://docs.xtdb.com/language-reference/1.22.1/datalog-transactions/#_usage
        https://docs.xtdb.com/language-reference/1.22.1/datalog-transactions/#transaction-functions
        produces fn-usage vector for inside tx
        '''
        if isinstance( funcname, str): funcname = qs.kw( funcname)
        assert qs.is_keyword( funcname), funcname
        return [ 'fn', funcname, *args ]

if 0:
  #from django/core/serializers/json.py
  class DjangoJSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time, decimal types, and
    UUIDs.
    """

    def default(self, o):
        # See "Date Time String Format" in the ECMA-262 specification.
        if isinstance(o, datetime.datetime):
            r = o.isoformat()
            if o.microsecond:
                r = r[:23] + r[26:]
            if r.endswith("+00:00"):
                r = r[:-6] + "Z"
            return r
        elif isinstance(o, datetime.date):
            return o.isoformat()
        elif isinstance(o, datetime.time):
            if is_aware(o):
                raise ValueError("JSON can't represent timezone-aware times.")
            r = o.isoformat()
            if o.microsecond:
                r = r[:12]
            return r
        elif isinstance(o, datetime.timedelta):
            return duration_iso_string(o)
        elif isinstance(o, (decimal.Decimal, uuid.UUID, Promise)):
            return str(o)
        else:
            return super().default(o)

# vim:ts=4:sw=4:expandtab
