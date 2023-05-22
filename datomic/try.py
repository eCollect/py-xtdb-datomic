#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dbclient import Datomic, log, edn_dumps, hacks
import datetime
from pprint import pprint, pformat
hacks.pprint_fix_immmutables()

###############################################################

db = Datomic( 'http://localhost:8992', 'devv', 'adbname')
log( db.list_storages)
log( db.list_databases_of_storage, 'devv')
log( db.create_db)
#db.debug=1
log( db.info)
log( db.entity, 1)
log( db.datoms, e= 1, limit= 5)
# print('----history') ??

def asslen( exp, res):
    lenres = len(res)
    assert exp == lenres, pformat( dict(locals()))

for post in (False, True):
    asslen( 1, db.query( '{:find [(pull ?x [*])] :where [[?x :db/doc]] }', limit=1, post=post ))
    asslen( 1, db.query( '{:find [(pull ?x [*])] :where [[?x :db/doc]] }', limit=1, post=post, as_of=133, ))
    asslen( 0, db.query( '{:find [(pull ?x [*])] :where [[?x :db/doc]] }', limit=1, post=post, as_of=3, ))
    asslen( 1, db.query( '{:find [(pull ?x [*])] :where [[?x :db/doc]] }', limit=1, post=post, as_of= datetime.datetime( year=2020, month=1, day=1)))
    asslen( 0, db.query( '{:find [(pull ?x [*])] :where [[?x :db/doc]] }', limit=1, post=post, as_of= datetime.datetime( year=1920, month=1, day=1)))

#2 dbargs - only post:
#[ ] == db.queryp( '{:find [(pull ?x [*])] :in [$a1 $a2]  :where [[ $a1 ?x :db/doc] [$a2 ?x :db/doc ]] }', '{:as-of 13  :db/alias "devv/adbname"}', limit=1, as_of=133, )
#[ ] == db.queryp( '{:find [(pull ?x [*])] :in [$a1 $a2]  :where [[ $a1 ?x :db/doc] [$a2 ?x :db/doc ]] }', '{:as-of 133 :db/alias "devv/adbname"}', limit=1, as_of=13,  )
#[1] == db.queryp( '{:find [(pull ?x [*])] :in [$a1 $a2]  :where [[ $a1 ?x :db/doc] [$a2 ?x :db/doc ]] }', '{:as-of 133 :db/alias "devv/adbname"}', limit=1, as_of=133, )

print( '======'*3)

import schema
if 0:
    sh_raw = dict(
            person = dict(
                ((k, schema.types.str) for k in 'name city state address email'.split()),
                date= schema.types.datetime,
                age = schema.types.int,
                #id_name = (schema.types.uuid, schema.options.identity),
                id_name = (schema.types.str, schema.options.identity),
                ),
            )
    sh_cooked = schema.cook( sh_raw)
    schema.check( sh_cooked)
    if 10:
        pprint( sh_cooked)
        log( db.tx, sh_cooked)

if 10:
    from faker import Faker
    import random
    fake = Faker()

    def fake_doc( fake, extra_fields ={}):
        r = dict(
            ((k,getattr( fake, k)()) for k in 'name city state address email'.split()),
            date= fake.date_time_between( start_date='-15yr', end_date='now'), #.isoformat(),
            age = fake.random_number(),
            **dict( (k,f( fake)) for k,f in extra_fields.items())
            )
        pprint(r)
        return dict( (schema.ns.person( k) if '/' not in k else k, v) for k,v in r.items())     #wrap in namespace/kw
    def fake_doc_da( fake):
        return fake_doc( fake, extra_fields= {
            #db.id_name: lambda fake: str(fake.uuid4()),    #XXX db.id_name will be auto-replaced, use another
            #WTF:works: '#a2': lambda fake: 'a2'+fake.name(),
            #WTF:works: ':#a3': lambda fake: 'a3'+fake.name(),
            })     #random.randint(1, 10),
    #db.debug=1
    for x in range( 1+0):
        docs = [fake_doc_da( fake) for _ in range(1*1+0)]
        log( db.tx, docs, keyword_keys=True)
        print( 11111, db.info())

#print( 22222, db.stats())
if 10:
    qid1 = """
        {:find [ id ]
            :where [[x :db/id id]]
            :limit 1
        }"""
    if 0:
        print('----id1 - get id of first object ever')
        try: rid1 = db.query( qid1)
        except RuntimeError as e:
            assert 'Argument id in :find is not a variable' in str(e)
if 0:
    print( 'try again, vars need ? prefix like ?id')
    rid1 = db.query( qid1.replace( ' id', ' ?id').replace( 'x' , '?x'))
    assert ':db.error/not-an-entity Unable to resolve entity: :db/id' in str(e)

if 1:
    print( 'try again, for person/name')
    rid1 = db.query( qid1.replace( ' id', ' ?id').replace( 'x' , '?x')
        .replace( 'db/id', 'person/name'),
        limit=1
        )
    id1 = rid1[0][0]
    print( id1)

    print('----r - get 3 objects which have .name and .address, via pull')
    r1 = db.query( """
        {:find [ (pull ?id [*])]
            :where [
                [?id :person/name ?name]
                [?id :person/address ?address]]
        }""", limit=3)
    pprint(r1)

    print('----r3 - get dict/id,name,city of 3 objects which have .name and .city')
    r3 = db.query( """
        {:find [?id ?name ?city]
            :keys [id name city]
            :where [
                [?id :person/city ?city]
                [?id :person/name ?name]
                ]
        }""", limit=3)
    pprint(r3)


if 0:
    print('----doc', id1)
    docid = dict( eid= id1)
    doc = db.entity( id1)
    pprint( doc)

if 0:
    doc['kuku'] = 7
    tx = db.tx( doc)
    print(tx)

if 10:
    import qsyntax as qs
    from base.qsyntax import sym, kw, kw2, var
    person = kw2.person

    def qcheck( q, pfx, rorg, limit =3):
        print( pfx, ':', edn_dumps( q))
        r = db.query( q, limit= limit)
        pprint( r)
        if rorg is not None:
            assert rorg == r, dict( r=r, exp=rorg)

    q3 = qs.daq(
        ).find( var.id, var.name, var.city
        ).into_keys( 'id name city'
        ).where(
            qs.var_attr_value( var.id, person.city, var.city ),
            qs.var_attr_value( var.id, person.name, var.name ),
        )
    qcheck( q3, 'r3', r3)

    if 10:
     qid1 = qs.daq(
        ).find( var.id
        ).where(
            qs.var_attr_value( var.x, person.name, var.id),
        )
     qcheck( qid1, 'id1', rid1, limit=1)

    if 10:
     q1 = qs.daq(
        ).find( [sym.pull, var.x, [ sym('*')]]
        #        , (sym('*'), var.age, 3 ]]
        ).where(
            qs.var_attr_value( var.x, person.name, var.name ),
            qs.var_attr_value( var.x, person.address, var.address ),
        )
     qcheck( q1, 'r1a', r1)

     q1 = qs.daq(
        ).find( qs.pull( var.x, whole=True)
        ).where(
            qs.var_attr_value( var.x, person.name, var.name ),
            qs.var_attr_value( var.x, person.address, var.address ),
        )
     qcheck( q1, 'r1b', r1)

    q1 = qs.daq(
        ).find( #qs.pull( var.x, whole=True) ,
            var.name,
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
            qs.var_attr_value( var.x, person.name, var.name ),
            #qs.var_attr_value( var.x, kw.address, var.address ),
            #qs.var_attr_value( var.x, kw.date, var.date),
            #qs.cmp.gt( var.date, '2015' #datetime.datetime.now().replace( year=2015, tzinfo=datetime.timezone.utc)
            #    ),
        )
    qcheck( q1, 'r1c', None)


WTF = '''
[:find ?e ?v (min ?e)
:in $
:where [?e :db/doc ?v]
]
there's no order-by ; use min??
'''

# vim:ts=4:sw=4:expandtab
