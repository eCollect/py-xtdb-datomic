from . import dbclient
from . import db2
from .qsyntax import var, var2, sym, sym2, kw, kw2, xtq, var_attr_value, pull, range_predicate, predicate
from . import qsyntax as qs
from base.qsyntax import _text2dumps1line, edn_dumps, dictAttr
import edn_format
import unittest, re, time
'''

- test passing of datetimes over and back : with +-timezone , without timezone but with Z, without anything
    + as params, as *-edn params, as body/edn

t0
#- empty db
- status - empty db or not
- create objects a1_read, a2_upd, a3_del (regardless if already exist, these will be latest versions)
- status+lasttx
- sync - so above ARE latest
- status+lasttx

t1 - (create then) query-simple one obj
- query a1 simple
- query a1 simple pull
- entity a1
- compare

- (create then) modify obj, history ?
- (create then) modify obj with valid in future, history , q before change, q after change
- (create then) modify obj with valid in past,   history ?
- modify a2 . 1, sync, entity-history a2
    --> ???  how to ignore history before t0
        or how to create uniq objs without history in t0 ???
- modify a2 .2 , sync, entity-history a2
- modify a2 .3 valid = p1, sync, entity-history a2

independent:
- query raw edn-text ?? ->client?
- query
    - lucene-variants a123
    - keys
    - pull
    - inputs - scalar coll tuple rel
    - rules ??
- transactions: https://docs.xtdb.com/language-reference/1.22.1/datalog-transactions/
    - put , +- valid/tx-times
    - delete match evict fn


http://yellerapp.com/posts/2014-05-07-testing-datomic.html
https://vvvvalvalval.github.io/posts/2016-01-03-architecture-datomic-branching-reality.html
'''

import os
URL = os.getenv( 'XTDB') or 'http://localhost:3001'
V2 = os.getenv( 'XTDB2')

class base:
    maxDiff = None
    headers = {}
    IS_EDN = dbclient.RESULT_EDN
    @classmethod
    def setUpClass( me):
        me.db = (db2.xtdb2 if V2 else dbclient.xtdb )( URL, headers= me.headers)
        #me.IS_EMPTY = (me.db.stats() == {})
        #me.db.debug =0

    def result( me, *r):
        'edn-tuples are json-lists'     #TODO ?
        if not me.IS_EDN and isinstance( r, tuple): r = list( r)
        return r
    if 0:
        def _getAssertEqualityFunc(self, first, second):
            #print( type(first), type( second))
            #if isinstance(first,list) and isinstance(second,tuple): print( first, second)
            if (isinstance( first, (edn_format.ImmutableDict,dict))
                and isinstance( second, (edn_format.ImmutableDict,dict))):
                    return self.assertDictEqual #_type_equality_funcs( dict)
            return super()._getAssertEqualityFunc( first,second)

        def assertDictEqual(self, d1, d2, msg=None):
            assert 0
            if isinstance( d1, edn_format.ImmutableDict): d1 = dict(d1)
            if isinstance( d2, edn_format.ImmutableDict): d2 = dict(d2)
            return super().assertDictEqual( d1,d2,msg)


class x( base, unittest.TestCase):
    #@classmethod
    #def setUp( me):
    #    me.db.debug =0

    def test_status( me):
        if V2:
            exp_keys = set('''
                latestCompletedTx
                latestSubmittedTx
                '''.split())
        elif me.IS_EDN:
            exp_keys = set('''
                xtdb.version/version
                xtdb.version/revision
                xtdb.kv/kvStore
                xtdb.kv/size
                xtdb.index/indexVersion

                ingesterFailed?
                xtdb.txLog/consumerState
                xtdb.kv/estimateNumKeys
                '''.split())
        else:
            exp_keys = set('''
                version
                revision
                kvStore
                size
                indexVersion

                ingesterFailed?
                consumerState
                estimateNumKeys
                '''.split())

        s = me.db.status()
        me.assertEqual( set(s) , exp_keys , s)  # & exp_keys
        if V2:
            txkeys = 'txId systemTime'.split()
            #these can be None if empty db
            for k in exp_keys:
                v = s[ k ]
                if v is not None:
                    me.assertEqual( set( v), set( txkeys), k)
        #import pprint
        #pprint.pprint( me.db.swagger_json())

    @unittest.skipIf( V2, 'not in v2')
    def itest_stats( me, IS_EMPTY =None):
        s = me.db.stats()
        if IS_EMPTY is None:
            IS_EMPTY = (s == {})
        else:
            me.assertEqual( (s=={}), bool(IS_EMPTY), )

        if IS_EMPTY: #empty db has no attr-stats or tx
            me.assertEqual( s, {})
            with me.assert_error2( '404: {:error "No latest-completed-tx found."}'):
                me.db.latest_completed_tx()
            with me.assert_error2( '404: {:error "No latest-submitted-tx found."}'):
                me.db.latest_submitted_tx()
        else:
            me.assertTrue( set([ 'xt/id' ]).issubset( s), s)

            txid, txtime = 'txId txTime'.split()    #both IS_EDN and not
            me.assertEqual( set( me.db.latest_completed_tx()), set([ txid, txtime ]))
            me.assertEqual( set( me.db.latest_submitted_tx()), set([ txid ]))

    def test_query_1_obj_whatever_it_is( me):
        if V2:
            q_flat_text = """
            {:find [ id ]
                :where [ ($ :atablename {:xt/id id } ) ]
                :limit 1
            }"""
            q_builder = xtq().find( sym.id
                ).where(    #FIXME only works as plain text inside
                    #db2.List( [ edn_format.dumps( *predicate( sym('$'), kw.atablename, { me.db.id_kw : sym.id } )) ])
                    db2.Match( kw.atablename, { me.db.id_kw : sym.id } )
                ).limit( 1
                )
            print( q_builder)
            r = me.db.query( q_builder)
            me.assertTrue( isinstance( r, (dict, edn_format.ImmutableDict)), (r, type(r)))
            me.assertTrue( 'id' in r, r)
            q_builder2 = q_builder.copy( without=[kw.limit]).limit( 2)
            r = me.db.query( q_builder2)    #fails, response not json but space-delimited text [..] [..]
            return

        s = me.db.stats()
        IS_EMPTY = (s == {})
        assert not IS_EMPTY

        q_flat_text = """ {:query
            {:find [ id ]
                :where [[x :xt/id id]]
                :limit 1
            }}"""
        rid1 = me.db.query( q_flat_text)
        id1 = rid1[0][0]

        q_builder = xtq().find( sym.id
                ).where( var_attr_value( sym.x, me.db.id_kw, sym.id )
                ).limit( 1
                )
        me.assertEqual( _text2dumps1line( edn_dumps({ kw.query: q_builder })), _text2dumps1line( q_flat_text))
        me.assertEqual( me.db.query( q_builder), rid1 )


    def test_create( me, with_AID =True, two_subobjs =False):
        #me.db.debug=1
        OID = 12
        AID = 221
        obj = dictAttr(
            name = 'myna',
            city = 'cit1',
            age  = 22,
            addresses = [ dictAttr( street = 'thisone' ) ],
            )
        obj[ me.db.id_name]= OID
        if two_subobjs:
            obj.addresses.append( dictAttr( street = 'thatone' ) )
        if with_AID:
            if with_AID is True: with_AID = me.db.id_name
            obj.addresses[0][ with_AID ]= AID
            if two_subobjs:
                obj.addresses[1][ with_AID ]= AID+1
        me.db.save( obj)
        if not V2:
            me.itest_stats( False)
            me.db.sync()

        me.assertEqual(
            me.db.query( xtq().find( pull( var.x, whole=True)
                ).where( var_attr_value( var.x, kw.name, obj.name)) )
            , me.result( [ obj ] ,) )
        me.db.debug=0
        me.assertEqual(
            me.db.query( xtq().find( pull( var.inid, whole=True)
                ).inputs( var.inid ), OID)
            , me.result( [ obj ] ,) )

        if with_AID is True:
        #sub-obj is not separated
          me.assertEqual(
            me.db.query( xtq().find( pull( var.inid, whole=True)
                ).inputs( var.inid ), AID)
            , me.result( [ None ] ,) )
          me.assertEqual(
            me.db.query( xtq().find( pull( var.inid, whole=True)
                ).inputs( qs.in_collection( var.inid)
                ), qs.arg_collection( OID, AID))
            , me.result( [ obj ], [ None ] ,) )
          me.assertEqual(
            me.db.query( xtq().find( pull( var.x, whole=True)
                ).where( var_attr_value( var.x, me.db.id_kw, var.inid )
                ).inputs( qs.in_collection( var.inid)
                ), qs.arg_collection( OID, AID))
            , me.result( [ obj ] ,) )
        return obj,OID,AID

    def test_search_inside_sub_vector_of_structs(me):
        # Nah. cannot. separate into root-level obj XXX
        # https://clojurians-log.clojureverse.org/xtdb/2020-07-30

        #me.db.debug=1

        #this works = vector of maps with 1 key
        obj,OID,AID = me.test_create( with_AID= None, two_subobjs= True)
        #me.db.debug=1
        me.assertEqual(
            me.db.query( xtq().find( pull( var.x, whole=True)
                ).where( var_attr_value( var.x, kw.addresses, obj.addresses[0] ),
                ), keyword_keys=True)
            , me.result( [ obj ], ) )

        #this does not works = vector of map with 2 keys
        obj,OID,AID = me.test_create( with_AID= 'number')
        #me.db.debug=1
        me.assertEqual(
            me.db.query( xtq().find( pull( var.x, whole=True)
                ).where( var_attr_value( var.x, kw.addresses, obj.addresses[0] ),
                ), keyword_keys=True)
            , me.result() )    # XXX
            #( [ obj ], ) )

        obj,OID,AID = me.test_create( with_AID= True)
        #me.db.debug=1
        me.assertEqual(
            me.db.query( xtq().find( pull( var.x, whole=True)
                ).where( var_attr_value( var.x, kw.addresses, obj.addresses[0] ),
                ), keyword_keys=True)
            , me.result() )    # XXX
            #( [ obj ], ) )

        if 0:
         print( 366,
            me.db.query( xtq().find( pull( var.x, whole=True)
                ).where( var_attr_value( var.x, kw.addresses, obj.addresses[0] ),
                     #qs.cmp.eq( (sym('get-attr'), var.adr, me.db.id_kw), var.inid),
                     #var_attr_value( var.adr, me.db.id_kw, var.inid),
                     #var_attr_value( var.adr, kw.street, obj.addresses[0].street ),
                ), keyword_keys=True),
            )
            #-> [obj, None]

if 10 and not V2:
 class y( x):
    IS_EDN = not x.IS_EDN
    headers = {
        'accept' : dbclient.BaseClient._app_edn if not dbclient.RESULT_EDN else dbclient.BaseClient._app_json,   #text/plain text/html
        }

class history( base, unittest.TestCase):
    #typ = 'e'   #object-types-distinguisher... or maybe PID ?
    def setUp( me):
        me.typ = time.time()
        super().setUp()
    def get_entity_whole( me, eid, **ka):
        '-> {..ent1..}'
        return me.db.entity( eid, **ka)
    #XXX beware: outmost query result is tuple if EDN, but list if json (has no tuples)
    def q_whole_entities_with_id( me, eid):
        '-> ([{..ent1..}],)'
        #return xtq().find( pull( var.eid, whole=True )).inputs( var.eid)  #XXX ??
        return xtq().find( pull( var.p, whole=True )
          ).where( var_attr_value( var.p, kw.typ, me.typ ),
            var_attr_value( var.p, me.db.id_kw, eid),
            )  #XXX ??

    def _q_var_of_typ_where( me, thevar, *where):
        return xtq().find( thevar ).where(
            var_attr_value( var.p, kw.typ, me.typ ),
            *where)
    def q_name_of_entities_with_id( me, eid):
        '-> ([["x"]],)'
        return me._q_var_of_typ_where( var.nm,
            var_attr_value( var.p, me.db.id_kw, eid),
            var_attr_value( var.p, kw.name, var.nm),
            )
    def q_id_of_entities_with_name_x( me): return me._q_var_of_typ_where( var.p,
            var_attr_value( var.p, kw.name, 'x'))
    def q_id_of_entities_with_name_y( me): return me._q_var_of_typ_where( var.p,
            var_attr_value( var.p, kw.name, 'y'))
    def q_id_of_entities_with_age_any( me): return me._q_var_of_typ_where( var.p,
            var_attr_value( var.p, kw.age))
    def q_id_of_entities_with_age_none( me): return me._q_var_of_typ_where( var.p,
            var_attr_value( var.p, kw.age, None))
    def q_id_of_entities_with_age_gt_3( me): return me._q_var_of_typ_where( var.p,
            var_attr_value( var.p, kw.age, var.age),
            range_predicate.gt( var.age, 3),
            )
    def q_id_of_entities_with_age_lt_3( me): return me._q_var_of_typ_where( var.p,
            var_attr_value( var.p, kw.age, var.age),
            range_predicate.lt( var.age, 3),
            )
    #########
    txid_key = 'txId' #me.db.ns_api_kw('tx-id')],
    def check( me, *, eid, tx=None, qargs ={}, pfx ='', history =(), as_of =None, expect_error_sync =False, **results):
        #obj = history[-1]
        ##print( me.db.latest_submitted_tx())   TODO
        ##print( me.db.latest_completed_tx())
        #me.db.await_tx_id( (as_of or tx)[ me.txid_key] )
        if not V2:
            me.db.sync()
        if as_of:
            qargs['tx_id'] = as_of[ me.txid_key]
        for k,v in results.items():
            with me.subTest( pfx+':'+k):
                fq = getattr( me, k)
                fargs = (eid,) if k.endswith( 'with_id') else ()
                rq = fq(*fargs)
                expv = () if v == () else (v,)
                if expect_error_sync:
                    with me.assertRaisesRegex( RuntimeError, 'Node out of sync'):
                        r = me.db.query( rq, **qargs)
                else:
                    r = me.db.query( rq, **qargs)
                    me.assertEqual( r, me.result( *expv ) )

        for ascending in True,False:
          with me.subTest( pfx+':history/'+('asc' if ascending else 'desc')):
            #print( me.t1)
            t1txid = me.t1[ me.txid_key]
            #ascending = 1
            if not ascending:
                history = list( reversed( history)) #copy

            since,until = 'start_tx_id', 'end_tx_id'
            if not ascending:
                since,until = until,since
            timecfg = dict(
                    ascending= bool(ascending),
                    **{ since: t1txid },
                    **({} if not as_of else { until: as_of[ me.txid_key] })
                    )
            if 'end_tx_id' in timecfg:
                timecfg['end_tx_id'] += (1 if ascending else -1)  #exclusive
            h = me.db.entity_history( eid,
                    with_docs =True,
                    **timecfg
                    )   #returns tuple
            me.assertEqual( [ a['doc'] for a in h], history)

            ##### same but auto-corrected inside
            timecfg_auto = dict(
                    auto_inclusive_tx_id =True,
                    ascending= ascending,
                    start_tx_id= t1txid,
                    **({} if not as_of else dict( end_tx_id= as_of[ me.txid_key]))
                    )
            h = me.db.entity_history( eid,
                    with_docs =True,
                    **timecfg_auto
                    )   #returns tuple
            me.assertEqual( [ a['doc'] for a in h], history)

    def test_create( me):
        eid = 1
        obj = dictAttr( a= 1, typ= me.typ, name= 'x')
        obj[ me.db.id_name] = eid

        me.t1 = tx = me.db.save( obj)
        me.c1 = dict(
            #get_entity_whole=eid            -> obj
            q_whole_entities_with_id        = [ obj ],
            q_name_of_entities_with_id      = [ 'x' ],
            q_id_of_entities_with_name_x    = [ eid ],
            q_id_of_entities_with_name_y    = (),
            q_id_of_entities_with_age_any   = (),
            q_id_of_entities_with_age_none  = (),
            q_id_of_entities_with_age_gt_3  = (),
            q_id_of_entities_with_age_lt_3  = (),
            history = [ obj ]
            )
        me.check( pfx= 't1-create', eid= eid, tx=tx, **me.c1)

        obj2 = dictAttr( obj, name= 'y')
        me.t2 = me.db.save( obj2)
        me.c2 = dict(
            q_whole_entities_with_id        = [ obj2 ],
            q_name_of_entities_with_id      = [ 'y' ],
            q_id_of_entities_with_name_x    = (),
            q_id_of_entities_with_name_y    = [ eid ],
            q_id_of_entities_with_age_any   = (),
            q_id_of_entities_with_age_none  = (),
            q_id_of_entities_with_age_gt_3  = (),
            q_id_of_entities_with_age_lt_3  = (),
            history = [ obj, obj2 ]
            )
        me.check( pfx= 't2-upd.name', eid= eid, tx=tx, **me.c2)

        obj3 = dictAttr( obj2, age= 5)
        me.t3 = me.db.save( obj3)
        me.c3 = dict(
            q_whole_entities_with_id        = [ obj3 ],
            q_name_of_entities_with_id      = [ 'y' ],
            q_id_of_entities_with_name_x    = (),
            q_id_of_entities_with_name_y    = [ eid ],
            q_id_of_entities_with_age_any   = [ eid ],
            q_id_of_entities_with_age_none  = (),
            q_id_of_entities_with_age_gt_3  = [ eid ],
            q_id_of_entities_with_age_lt_3  = (),
            history = [ obj, obj2, obj3 ]
            )
        me.check( pfx= 't3-add.age', eid= eid, tx=tx, **me.c3)

        obj4 = obj2 #no age again
        me.t4 = me.db.save( obj4)
        me.c4 = dict(
            #get_entity_whole=eid            -> obj
            q_whole_entities_with_id        = [ obj4 ],
            q_name_of_entities_with_id      = [ 'y' ],
            q_id_of_entities_with_name_x    = (),
            q_id_of_entities_with_name_y    = [ eid ],
            q_id_of_entities_with_age_any   = (),
            q_id_of_entities_with_age_none  = (),
            q_id_of_entities_with_age_gt_3  = (),
            q_id_of_entities_with_age_lt_3  = (),
            history = [ obj, obj2, obj3, obj4 ]
            )
        me.check( pfx= 't4-del.age', eid= eid, tx=tx, **me.c4)

        me.check( pfx= 't2-as-of',  eid= eid,
            as_of = me.t2, **me.c2,
            )
        me.check( pfx= 't1-as-of',  eid= eid,
            as_of = me.t1, **me.c1,
            )
        me.check( pfx= 't3-as-of',  eid= eid,
            as_of = me.t3, **me.c3,
            )
        me.check( pfx= 't4-as-of',  eid= eid,
            as_of = me.t4, **me.c4,
            )

        #before t1 , after t4
        me.check( pfx= 't1-before-as-of', eid= eid,
            as_of = { me.txid_key: me.t1[ me.txid_key] -1 },
            #get_entity_whole=eid            -> obj
            q_whole_entities_with_id        = (),
            q_name_of_entities_with_id      = (),
            q_id_of_entities_with_name_x    = (),
            q_id_of_entities_with_name_y    = (),
            q_id_of_entities_with_age_any   = (),
            q_id_of_entities_with_age_none  = (),
            q_id_of_entities_with_age_gt_3  = (),
            q_id_of_entities_with_age_lt_3  = (),
            history = []
            )
        me.check( pfx= 't4-after',  eid= eid,
            as_of = { me.txid_key: me.t4[ me.txid_key] +1 },
            expect_error_sync= True,
            **me.c4,
            )


if __name__ == '__main__':
    unittest.main( verbosity=2)

# vim:ts=4:sw=4:expandtab
