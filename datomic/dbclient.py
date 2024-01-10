from base.rpc_json_http import BaseClient, log
from base.edn import hacks, EDNClientMixin
import edn_format
from edn_format import dumps as edn_dumps
import datetime, urllib

hacks.edn_accept_naive_datetimes()
hacks.edn_response_dicts_Keyword_into_str( maps_keys= True, maps_values= False)
#XXX maybe needed, to loads stuff:
#edn_format.add_tag( 'db/id', lambda name: name )
hacks.pprint_fix_immmutables()  #not really needed but..


# https://docs.datomic.com/on-prem/best-practices.html

class Datomic_read( BaseClient):
    ''' append-only-db-in-clojure , 1-temporal, graph
    https://docs.datomic.com/on-prem/api/rest.html
    beware: it is picky about url's ending slash /

    WTF: Leading underscores are used for reverse lookup in pull.
    If attribute has a leading underscore then cannot do reverse lookup with that attribute.
    https://docs.datomic.com/on-prem/schema/schema.html
    '''

    #params validators
    is_eid = staticmethod( BaseClient.is_int)
    may_eid = may_aid = staticmethod( BaseClient.may_int)
    @staticmethod
    def may_t( x):
        assert x is None or isinstance( x, int) and x>0 or isinstance( x, datetime.datetime), x
        return x
    @staticmethod
    def may_value( x): return x

    @staticmethod   #overload
    def datetime_param_converter( v):
        return edn_dumps( v)    #no need for urllib.parse.quote_plus here

    _headers_base = {
        'accept': ', '.join([ EDNClientMixin._app_edn, 'text/plain' ]),    #text/html makes errors too fancy
        **EDNClientMixin._headers_content_edn,
        }

    def __init__( me, rooturl, storage =None, dbname =None, headers ={}):
        super().__init__( rooturl, headers)
        me.storage = storage
        me.dbname = dbname

    ##### rpc methods
    #XXX beware, it is picky about url's ending slash /

    def list_storages( me):
        ''' GET /data/
        return list of storages in the server
        '''
        return me._get( 'data/')

    def list_databases_of_storage( me, storage):
        ''' GET /data/<storage-alias>/
        return list of databases in the storage
        '''
        return me._get( f'data/{storage}/')

    def create_db( me, storage =None, dbname =None, set_as_default =True):
        ''' POST /data/<storage-alias>/
        create db if not existing, return list of databases in the storage
        '''
        if dbname  is None: dbname = me.dbname
        if storage is None: storage = me.storage
        r = me._post( f'data/{storage}/',
                data= edn_dumps( {'db-name': dbname }, keyword_keys= True,))
        #extra_ok_statuses= [201] if just created
        if set_as_default:
            me.storage = storage
            me.dbname = dbname
        return r

    @staticmethod
    def _vector_of_edn_or_obj( *docs, keyword_keys =False, force2edn =False ):
        '''beware: autoconvert dict-key into :key keywords applies in depth!
        '''
        dd = [ edn_dumps( x, keyword_keys= keyword_keys) if force2edn or not isinstance( x, str) else x
                for x in docs ]
        return '[ '+', '.join( dd) +' ]'

    id_name = 'db/id'
    id_kw   = edn_format.Keyword( id_name)

    tbasis_key = ':basis-t'
    @staticmethod
    def tbasis4url( tbasis):
        'inside url only'
        if tbasis is None: return '-'
        me.may_t( tbasis)
        r = edn_dumps( tbasis)
        r = urllib.parse.quote_plus( r)
        return r
    def _url_db_tbasis( me, tbasis =None, *url_levels):
        return me._url_join( 'data', me.storage, me.dbname, me.tbasis4url( tbasis), *url_levels)

    def info( me, tbasis =None):
        ''' GET /data/<storage-alias>/<db-name>/<basis-t>/
        return database info ; default is of current basis=-
        '''
        return me._get( me._url_db_tbasis( tbasis, '/'))

    def datoms( me, tbasis =None, index ='avet', **ka):
        ''' GET /data/<storage-alias>/<db-name>/<basis-t>/datoms?..
        return set or range of datoms from an index.
        expects params as edn, also tbasis
        '''
        index = index.lower()
        assert index in 'aevt eavt avet vaet'.split(), index
        params_other = me._params_taker( ka,
            #index - The index to use, one of aevt, eavt, avet or vaet; one or more leading components of the index can be supplied using e, a and v
            e     = me.may_eid,     # An entity id or ident (optional)
            a     = me.may_aid,     # An attribute id or ident (optional)
            v     = me.may_value,   # A specific value (optional)
            start = me.may_value,   # A starting value for an index range (optional)
            end   = me.may_value,   # An ending value for an index range (optional)
            limit = me.may_int_positive,     # Number of results to return (optional)
            offset= me.may_int_positive,     # First result to return (optional)
            as_of = me.may_t,       #as-of-t - A t value that filters the database to only include facts asserted as of that time (optional)
            since = me.may_t,       #since-t - A t value that filters the database to only include facts asserted since that time (optional)
            history = me.may_bool,  # Boolean whether to use a database value containing all historical facts (optional)
            )
        me._check_unknown_params( ka)
        return me._get( me._url_db_tbasis( tbasis, 'datoms'),
                **me._params( index= index, **params_other))

    def entity( me, eid, tbasis =None, **ka):
        ''' GET /data/<storage-alias/<db-name>/<basis-t>/entity?..
        return all attributes of specified entity.
        expects params as edn, also tbasis
        eid - entity-id or ident  ; takes int or ':someident' or 'someident'
        ?? as_of/since may be-  t or tx or datetime ??
        beware: returns empty entity {:db/id someint} for inexisting/non-time-valid entity !!!
            e.g. e=1212123  -> {:db/id 1212123}
            e.g. e=:db/add as-of=1960-11-11... -> {:db/id 1}    #seems made as valid after 1970-01-01..
        this does deref enums.. while query/pull does not, hence the ./enums-deref/
        '''
        params_other = me._params_taker( ka,
            as_of = me.may_t,       #as-of-t - A t value that filters the database to only include facts asserted as of that time (optional)
            since = me.may_t,       #since-t - A t value that filters the database to only include facts asserted since that time (optional)
            )
        me._check_unknown_params( ka)
        return me._get( me._url_db_tbasis( tbasis, 'entity'),
                **me._params( e= me.is_eid( eid), **params_other))

    @staticmethod
    def _map_of_edn( params):
        return '{ ' + ', '.join( f':{k} {v}' for k,v in params.items()) + ' }'

    def query( me, query, *in_args, post= False, auto_dbarg1 =True, **ka):
        ''' GET /api/query?    or   POST /api/query?
        return results of query against one or more databases.
        https://docs.datomic.com/on-prem/query/query.html
        https://docs.datomic.com/cloud/query/query-data-reference.html
        naming: variable = symbol starting with "?" (cannot be only ?)
            source-var/db - symbol starting with '$' (can be only $)
            rules-var - symbol starting with % (can be only %)
        first dbarg is always the .dbname ; in_args NOT checked at all
        GET: seems only one dbarg supported??
        '''
        params_other = me._params_taker( ka,
            limit = me.may_int_positive,     # Number of results to return (optional)
            offset= me.may_int_positive,     # First result to return (optional)
            )
        arg1 = me._params_taker( ka,
            as_of = me.may_t,       # :as-of-t - A t value that filters the database to only include facts asserted as of that time (optional)
            since = me.may_t,       # :since-t - A t value that filters the database to only include facts asserted since that time (optional)
            history = me.may_bool,  # :history - Boolean whether to use a database value containing all historical facts (optional)
            basis_t = me.may_t,     # :basis-t - t value or `-` for current database value (optional)
            )
        me._check_unknown_params( ka)
        arg1 = me._params_cleaner( arg1, autoconvert= False)
        if auto_dbarg1:
            arg1[ 'db/alias' ] = f'{me.storage}/{me.dbname}'
        if isinstance( query, dict):
            from datomic import qsyntax
            query = qsyntax.qbuilder( query)   #copy+check
            in_spec = query.match_args_to_spec( in_args)

            #put src_default for db/alias as first arg
            if auto_dbarg1:
                if in_spec:
                    qsyntax.qs_assert( qsyntax.src_default not in in_spec, 'cannot have auto_dbarg1=True with $-arg pre-specified', in_spec)
                in_spec = [ qsyntax.src_default, *in_spec ]

            #move rules into rule_default as last arg
            if query.kw_rules in query:
                if in_spec:
                    qsyntax.qs_assert( qsyntax.rule_default not in in_spec, 'cannot have .rules with %-arg pre-specified', in_spec)
                rules = query.pop( query.kw_rules)
                in_spec = list( in_spec) + [ qsyntax.rule_default ]
                in_args = in_args + ( rules ,)

            if in_spec:
                query[ query.kw_in ] = list( in_spec )
            query = edn_dumps( query)

        assert isinstance( query, str), query
        args = me._vector_of_edn_or_obj( arg1, keyword_keys= True, *in_args)
        params = me._params_cleaner( dict( q= query, args= args, **params_other))
        url = 'api/query'
        if post:
            return me._post( url, data= me._map_of_edn( params))
        return me._get( url, params= params)

    def queryp( me, *a,**ka):
        return me.query( post=True, *a, **ka)
    def queryg( me, *a,**ka):
        return me.query( post=False, *a, **ka)

    def events_subscribe( me):
        ''' GET /events/<storage-alias/<db-name>
        https://docs.datomic.com/on-prem/api/rest.html#subscribe-to-events
        in-browser: GET /data/<storage-alias>/<db-name>/<basis-t>/events
        '''
        return me._get( me._url_join( 'events', me.storage, me.dbname), headers= { 'accept': 'text/event-stream' })

class Datomic( Datomic_read):
    '''
    note: there are also speculative transactions but not via REST:
    https://docs.datomic.com/on-prem/clojure/index.html#datomic.api/with
    https://docs.datomic.com/on-prem/time/filters.html#as-of-not-branch
    https://vvvvalvalval.github.io/posts/2016-01-03-architecture-datomic-branching-reality.html
    '''
    def transact( me, docs, keyword_keys =False, force2edn =False):
        ''' POST /data/<storage-alias>/<db-name>/
        transaction. takes list of list_forms-or-map_forms
        # https://docs.datomic.com/on-prem/transactions/transactions.html
        list_forms:
            [:db/add entity-id attribute value ]
            [:db/retract entity-id attribute value]
            [:db/retract entity-id attribute]
            [data-fn args*]         #see https://docs.datomic.com/on-prem/transactions/transaction-functions.html
        map_form:
            {:db/id entity-id  attr1 val1  attr2 val2 ... }
            each map_form is transformed into set of adding-list_forms, like
                [:db/add entity-id attr1 val1 ]
                [:db/add entity-id attr2 val2 ]
                ...
             the :db/id entity-id  is optional, defaults to new temporary-id (see result :tempids for resolves)
        if entity-id exists, will add updates ;
        else will create new entity (even for db/retract !), using the specified id only as grouping reference

        seems to accept {":someattr" value } same as {:someattr value }
        needs attrs to be entities i.e. predefined in schema or else

        returns: {  :db-before {:db/alias "devv/adbname", :basis-t 66},
                    :db-after {:db/alias "devv/adbname", :basis-t 1000},
                    :tx-data [{:e 13194139534312, :a 50, :v #inst "2022-12-22T10:17:51.871-00:00", :tx 13194139534312, :added true}],
                    :tempids {"myid" 17592186045417}}
        see also:
        https://docs.datomic.com/on-prem/best-practices.html#lookup-refs-to-specify-existing-entities
            i.e. entity-id can be lookup-ref-func - [:add [:user/email "xyz"] :user/age 22]
        https://docs.datomic.com/on-prem/best-practices.html#set-txinstant-on-imports
        https://docs.datomic.com/on-prem/best-practices.html#use-dbafter
        https://docs.datomic.com/on-prem/best-practices.html#optimistic-concurrency
        '''
        if isinstance( docs, dict): docs = [ docs ]
        assert isinstance( docs, (list,tuple)), docs
        for d in docs:
            assert isinstance( d, (dict,str,list,tuple)), d
            if isinstance( d, (list,tuple)):
                assert str( d[0]) in me._transaction_funcs + me._transaction_funcs_own , d[0]
        data = me._vector_of_edn_or_obj( *docs, keyword_keys =keyword_keys, force2edn =force2edn)
        return me._post( me._url_join( 'data', me.storage, me.dbname, '/'),
                    data= '{:tx-data ' + str(data) +'}' )
    write = save = tx = transact

    _transaction_funcs_own = ()
    _transaction_funcs = (  #https://docs.datomic.com/on-prem/transactions/transaction-functions.html
        ':db/add',          #add-attr-value: ( eid, attribute, value )
        ':db/retract',      #del-value-or-attr: ( eid, attribute, value ) or ( eid, attribute )
        ':db/retractEntity', #del-entity: eid   # recursive with components
        ':db/cas',          # compare-and-swap: eid, attribute, old-value, new-value  # https://docs.datomic.com/on-prem/best-practices.html#optimistic-concurrency
        )
    @staticmethod
    def make_tx_add( eid, attr, value):
        return [ schema.db.add, eid, attr, value ]
    @staticmethod
    def make_tx_del( eid, attr, value):
        return [ schema.db.retract, eid, attr, value ]
    @staticmethod
    def make_tx_del_attr( eid, attr):
        return [ schema.db.retract, eid, attr ]
    @staticmethod
    def make_tx_del_entity( eid):
        return [ schema.db.retractEntity, eid ]
    @staticmethod
    def make_tx_replace_if_equals( eid, attr, old_value, new_value):    #old_value can be None for no-value-yet
        return [ schema.db.cas, eid, attr, old_value, new_value ]

    @classmethod
    def make_tx_add_alias( klas, attr, new_attr):
        ''' https://docs.datomic.com/on-prem/best-practices.html#use-aliases
        produces list-form for inside tx-data
        >>> edn_dumps( make_tx_add_alias( qs.kw2.user.id, qs.kw2.user.email))
        '[:db/add :user/id :db/ident :user/email]'
        '''
        assert qs.is_keyword( attr), attr
        assert qs.is_keyword( new_attr), new_attr
        return klas.make_tx_add( attr, schema.db.ident, new_attr )
    @staticmethod
    def make_tx_db_func_decl( funcname, body):
        '''https://docs.datomic.com/on-prem/reference/database-functions.html#transaction-functions
        produces map-form of declaration, for inside tx-data
        '''
        if isinstance( funcname, str): funcname = qs.kw( funcname)
        assert qs.is_keyword( funcname), funcname
        #if not isinstance( body, str): body = edn_format.dumps( body)
        return { schema.db.ident: funcname, schema.db.fn: body }
    @staticmethod
    def make_tx_func_use( funcname, *args):
        '''https://docs.datomic.com/on-prem/reference/database-functions.html#transaction-functions
        produces list-form of usage, for inside tx-data
        '''
        if isinstance( funcname, str): funcname = qs.kw( funcname)
        assert qs.is_keyword( funcname), funcname
        return [ funcname, *args ]


''' on querying:
https://docs.datomic.com/on-prem/query/query-executing.html#clause-order
https://docs.datomic.com/on-prem/best-practices.html#most-selective-clauses-first
https://docs.datomic.com/on-prem/best-practices.html#join-along
https://docs.datomic.com/on-prem/best-practices.html#collections-as-inputs
https://docs.datomic.com/on-prem/best-practices.html#use-pull-to-retrieve-attribute-values
https://docs.datomic.com/on-prem/best-practices.html#parameterize-queries

unit-of-work = temporal-context:
https://docs.datomic.com/on-prem/best-practices.html#consistent-db-value-for-unit-of-work
https://docs.datomic.com/on-prem/best-practices.html#t-instead-of-txInstant
'''


# vim:ts=4:sw=4:expandtab
