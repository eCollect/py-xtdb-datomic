#!/usr/bin/env python
# -*- coding: utf-8 -*-
from xtdb.dbclient import xtdb, log, edn_dumps
from xtdb2.dbclient import xtdb2, Symbol
import datetime
from pprint import pprint

import os
PORT= os.getenv( 'PORT') or '3001'
URL = os.getenv( 'XTDB') or f'http://localhost:{PORT}'
V2 = bool( os.getenv( 'XTDB2'))
db = xtdb( URL) if not V2 else xtdb2( URL)
if V2:
    db.tx = lambda *a,**ka: db.submit_tx( table= 'trytbl', *a,**ka)
    db.stats = lambda: None
    #db.debug=1
    _sync = db.sync
    #db.sync = lambda: _sync( 'trytbl')
    #db._cache_now = {}
    def q_tx_first_n( n =125):  #125-126
        return db.sync( table= 'trytbl', n=n) #db.txs_table, n=n)

if 10:
    from faker import Faker
    import random
    fake = Faker()

    fakefields = 'name city state address email'.split()
    _models = 'bmw uno bus'.split()
    def fake_doc( fake, extra_fields ={}):
        return dict(
            [(k,getattr( fake, k)()) for k in fakefields ] + [
             (k,f( fake)) for k,f in extra_fields.items() ],
            date= fake.date_time_between( start_date='-15yr', end_date='now').astimezone().isoformat(),
            age = fake.random_number(),
            aliases = [ str(fake.uuid4()) for x in range(9 ) ],
            cars = [ dict( vin= fake.vin(), model= _models[ x % len(_models) ], mileage= fake.random_number(), plate= fake.license_plate()) for x in range( 7) ],
            **dict( ('x'+str(i), (i,bool(i),float(i)/3)) for i in range(10)),
            **dict( ('y'+str(i), [i,bool(i),float(i)/7]) for i in range(10)),
            **{ 'айде': 'беее' } #non-ascii
            )

    def fake_doc_xt( fake):
        return fake_doc( fake, extra_fields= {
            db.id_name: lambda fake: str(fake.uuid4()),
            #WTF:works: '#a2': lambda fake: 'a2'+fake.name(),
            #WTF:works: ':#a3': lambda fake: 'a3'+fake.name(),
            })     #random.randint(1, 10),

    if 10:
        from time import time
        def avgit( avg, t, isdt=False):
            dt = t if isdt else time()-t
            avg.append( int(1000*dt))
            avg = avg[-10:]
            return sum(avg)//len(avg)
        avg = []
        avgdt = []
        t0 = dt = None
        docs = [fake_doc_xt( fake) for _ in range(100)]

        # from xtdb import fail
        # docs = fail.success if 0 else fail.fail
        if 0:
            import json
            with open( 'tx100-9-7-19.json', 'w') as fo:
                json.dump( docs, fo)
            from xtdb2.dbclient import transit_dumps
            with open( 'tx100-9-7-19.jstx', 'w') as fo:
                fo.write( transit_dumps( docs, False))
            #assert 0
        for x in range( int( os.getenv('N') or 1+00)):
            #docs = [fake_doc_xt( fake) for _ in range(100)]
          if 10:
            if 10:
             for d in docs:
                xx = f':{x}'
                d['name'] = d['name'].split(':')[0] + xx
                d[ db.id_name] = d[ db.id_name].split(':')[0] + xx
                d['age'] += 1
            #log( db.tx, docs)
            t = time()
            if t0 is not None: dt = t-t0
            t0 = t
            #db.debug = 1
            if 10:
                db.tx( docs)
            print( 11111, x, avgit( avg,t),'ms', dt and avgit( avgdt, dt, True)) #db.stats())
            if 10 and x%2:
                for d in docs:
                    d['name'] += ':extt'
                t = time()
                db.tx( docs)
                print( 22222, x, avgit( avg,t),'ms')
          if 0: # and not x%4:
                t = time()
                q_tx_first_n(500+0)
                print( 33333, x, avgit( avg,t),'ms')

    if 0:   #valid_time +-
        last_tx = db.latest_completed_tx()
        print( '----', last_tx)
        last_tx_time = last_tx['txTime']

        for time in [
            #datetime.datetime.utcnow() - datetime.timedelta( seconds=5),   #XXX naive
            #datetime.datetime.now( datetime.timezone.utc) - datetime.timedelta( seconds=25),   #XXX aware
            last_tx_time + datetime.timedelta( seconds=3),
            None
            ]:
            docs = [ fake_doc_xt( fake) ]
            #db.debug=1
            log( db.tx, docs,
                #tx_time= time,
                put_valid_time = time and time - datetime.timedelta( seconds=100),
                put_end_valid_time = time
                )
            db.debug=0
            print( 11111, db.stats())

if 10:
    log( db.latest_completed_tx)
    db.sync()
    log( db.latest_completed_tx)
    #assert 0

log( db.status)
if log( db.stats):
    log( db.latest_completed_tx)
#log( db.tx_log)

1/0

print('----id1 - get id of first object ever')
rid1 = db.query( """ {:query
    {:find [ id ]
        :where [[x :xt/id id]]
        :limit 1
    }}""")
id1 = rid1[0][0]
print( id1, type(id1))

print('----r - get 3 objects which have .name and .address, via pull')
r1 = db.query( """ {:query
    {:find [ (pull ?id [*])]
        :where [
            [?id :name ?name]
            [?id :address ?address]]
        :limit 3
    }}""")
pprint(r1)

print('----r3 - get dict/id,name,city of 3 objects which have .name and .city')
r3 = db.query( """ {:query
    {:find [?id ?name ?city]
        :keys [id name city]
        :where [
            [?id :city ?city]
            [?id :name ?name]
            ]
        :limit 3
    }}""")
pprint(r3)



print('----doc', id1)
docid = dict( eid= id1)

doc = log( db.entity, id1)
#goes http://localhost:3001/_xtdb/entity?eid-edn=12 -> int/12 -> finds
#note http://localhost:3001/_xtdb/entity?eid=12 -> str/12 -> does not
db.debug=1

#note these both go http://localhost:3001/_xtdb/entity?eid-edn=12
log( db.entity, eid_edn=int(id1))
log( db.entity, eid_edn=str(id1))

#goes http://localhost:3001/_xtdb/entity?eid-edn="12" -> str/12 -> does not
#log( db.entity, eid_edn=f'"{id1}"') #fail

doctx = log( db.entity_tx, id1)

if 0:
    doc = dict(doc)     #edn -> ImmutableDict -> no setitem
    doc['kuku'] = 7     #edn -> :kuku != kuku
    print(1111, doc)
    tx = log( db.tx, doc)
if 0:
    log( db.entity, id1)
    log( db.entity_tx, id1)
    txid = tx['txId']
    try:
        log( db.tx_committed, txid)
    except:
        import traceback
        traceback.print_exc()
    log( db.await_tx, txid)
    log( db.tx_committed, txid)
    log( db.entity, id1)

    print('----history')
    log( db.entity_history, id1, with_docs= True, )

if 0:
    '''
    https://docs.xtdb.com/extensions/full-text-search/
    input string escaping - use org.apache.lucene.queryparser.classic.QueryParser/escape

    https://lucene.apache.org/core/8_9_0/queryparser/org/apache/lucene/queryparser/classic/package-summary.html#package.description
    abc* ab?c ab*c - wildcards, anywhere but in start
    abc~  - fuzzy-dist=2
    abc~3 - fuzzy-dist=3
    '''
    print('----qry_lucene')

import qsyntax as qs
from base.qsyntax import sym, kw, kw2, var

if 0:
    def qcheck( q, pfx, rorg, **ka):
        print( pfx, ':', edn_dumps( q))
        r = db.query( q, **ka)
        pprint( r)
        if rorg is not None:
            assert rorg == r, dict( r=r, exp=rorg)

    q3 = qs.xtq(
        ).find( var.id, var.name, var.city
        ).into_keys( 'id name city'
        ).where(
            qs.var_attr_value( var.id, kw.city, var.city ),
            qs.var_attr_value( var.id, kw.name, var.name ),
        ).limit( 3
        )
    qcheck( q3, 'r3', r3)
    assert str(kw2.xt.id) == ':'+db.id_name
    assert kw2.xt.id == db.id_kw
    if 10:
     qid1 = qs.xtq(
        ).find( var.id
        ).where(
            qs.var_attr_value( var.x, db.id_kw, var.id),
        ).limit( 1
        )
     qcheck( qid1, 'id1', rid1)

     q1 = qs.xtq(
        ).find( [sym.pull, var.x, [ sym('*')]]
        #        , (sym('*'), var.age, 3 ]]
        ).where(
            qs.var_attr_value( var.x, db.id_kw ),
            qs.var_attr_value( var.x, kw.name, var.name ),
            qs.var_attr_value( var.x, kw.address, var.address ),
        ).limit( 3
        )
     qcheck( q1, 'r1', r1)

if 1:
    #import datetime
    q1 = qs.xtq(
        ).find( #qs.pull( var.x, whole=True) ,
            var.name,
            qs.pull( var.x, whole=True)
            #sym.xxz,
            #*qs.pred_startswith( var.name, 'M'),  #works ok
            # (if then) === (when then)
            # (< x y) works on numbers only .. use (compare XXX
            #(qs.sym2('clojure.core', 'if'), #qs.if_(   #XXX these ifs sometimes work, but mostly not - Invalid function in aggregate expr
            #    (sym('<'), (sym('compare'), var.name, 'E' ), 0),   #this alone works ok
            #    'bef1',
            #    'aft2'
            #    ),
        ).where(
            #qs.var_attr_value( var.x, db.id_kw ),
            qs.var_attr_value( var.x, kw.name, var.name ),
            #qs.var_attr_value( (sym.startswith, var.x), kw.name, var.inx),
            qs.var_attr_value( var.x, kw.state, sym.in_st),
            qs.var_attr_value( var.x, kw.city,  sym.in_cy),
            #qs.var_attr_value( var.x, kw.address, var.address ),
            #qs.var_attr_value( var.x, kw.date, var.date),
            #qs.cmp.gt( var.date, '2015' #datetime.datetime.now().replace( year=2015, tzinfo=datetime.timezone.utc)
            #    ),
#        ).in_( sym.inx    #scalars
#        ).in_( qs.in_collection( sym.in_st)
#        ).in_( qs.in_tuple( sym.in_st, sym.in_cy)
#        ).in_( qs.in_relation( sym.in_st, sym.in_cy)
        ).limit( 3
        )
    db.debug=1
    #relation
    q1.in_( qs.in_relation( sym.in_st, sym.in_cy))
    pprint( db.query( q1, [
        [ 'Alabama', 'Earlborough' ],
        [ 'Idaho', 'Hestermouth' ],
        ]))
    pprint( db.query( q1, qs.arg_relation(
        ( 'Alabama', 'Earlborough' ),
        [ 'Idaho', 'Hestermouth' ],
        )))

    #scalar
    qsc= q1.copy( without= [ q1.kw_in]) ; qsc.in_( sym.inx)
    pprint( db.query( qsc, 'Idaho' ))
    #collection
    qc = q1.copy( without= [ q1.kw_in]) ; qc.in_( qs.in_collection( sym.in_st))
    pprint( db.query( qc, [ 'Idaho', 'Alabama' ]))
    #tuple
    qt = q1.copy( without= [ q1.kw_in]) ; qt.in_( qs.in_tuple( sym.in_st, sym.in_cy))
    pprint( db.query( qt, [ 'Alabama', 'Earlborough' ]))

#TODO: mbrainz

# vim:ts=4:sw=4:expandtab
