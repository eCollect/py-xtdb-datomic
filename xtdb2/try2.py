#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dbclient import xtdb2, log, Keyword, Symbol, TX_key_id
import datetime
#from pprint import pprint
import uuid

kw = Keyword
sym = Symbol
# or, from base.qsyntax import edn_factory1, edn_factory2 ;
#single :   kw.name or kw2('?name') ..
# kw  = edn_factory1( Keyword)
# sym = edn_factory1( Symbol)
#prefix/name :   kw2.pfx.name or kw2('?pfx','nm') or kw2('?pfx').nm ..
# kw2 = edn_factory2( Keyword)
# sym2= edn_factory2( Symbol)

import os
PORT= os.getenv( 'PORT') or '3002'
URL = os.getenv( 'XTDB') or f'http://localhost:{PORT}'
db = xtdb2( URL)

#log( db.status )
def makeid(): return { db.id_name: uuid.uuid4() }
def addid( d ):
    d.update( makeid())
    return d

docs = [
    dict( a=1, b='bb'),
    dict( a=2, c= 12.45 ),
    #dict( a=32, c= 12.4 ),
    ] #datetime.datetime.now() ) ]
for d in docs: addid( d)
txkey= None
if 0:
    txkey = log( db.tx, docs, table= 'atablename' )

from transit.transit_types import TaggedValue

#txkey = TX_key_id( tx_id= 121651, system_time= datetime.datetime(2024, 1, 10, 20, 46, 42, 987242, tzinfo =datetime.UTC))

from xtdb2 import qs
qs.sym = sym
qs.kw = kw
qs.sym_wild = sym( '*')
if 0:
 log( db.query,
    #'from :atablename [a b c]' -> plain text expects SQL
    ( sym('->'),
     ( sym('from'), kw('atablename'), [ sym('*') ] ) ,
     #( sym('from'), kw('atablename'), [ sym(x) for x in ['a', 'b', 'c' ]] ) ,
     ( sym('where'), (sym('='), sym('a'), 2 )),
     ( sym('limit'), 3),
    ),
#    )
#if 0: dict(
    tx_timeout_s = 2, #TaggedValue( 'time/duration', 'PT3S'),
    after_tx = txkey #TX_key_id( tx_id= 21651, system_time= datetime.datetime(2024, 1, 10, 20, 46, 42, 987242, tzinfo =datetime.UTC))
        #["~#xtdb/tx-key",["^ ","~:tx-id",612343,"~:system-time",["~#time/instant","2024-01-10T11:08:36.422964Z"]]]
    )
if 0:
 log( db.query, qs.s(
    qs.pipeline(
        qs.fromtable( 'atablename', ),
        qs.where( qs.funcs.eq( qs.Var('a'), 2 )),
        qs.with_columns( z= qs.funcs.add( qs.Var('a'), 1) ),
        qs.orderby( orders={ db.id_name: True } ),
        qs.limit( 3),
        #qs.funcs.substring( qs.Var( db.id_name), 1,1) ))
    )))

if 0:
    log( db.query, qs.s(
        qs.pipeline(
            qs.fromtable( db.txs_table, ),
            #qs.aggregate( qs.funcs.aggr_max( sym( db.id_name))), no
            qs.orderby(
                #db.id_name,
                #qs.OrderSpec( sym( db.id_name) , desc=True),
                orders= { db.id_name: True }
                ),
            qs.limit(1)
            )
        ))
if 0:
    log( db.query, qs.s(
        qs.fromtable( 'atablename', 'a', 'b' )
        ))

if 0:
    #assert-exists-or-not
    docs1 = [
        db.make_tx_assert_notexists( qs.s(
            qs.fromtable( 'nosuchtbl', 'a' ),
            )),
        dict( a=7, b='x', **makeid()),
        ]
    txkey = log( db.tx, docs1, table= 'btablename' )

    docs2 = [
        db.make_tx_assert_exists( qs.s(
            qs.pipeline(
                qs.fromtable( 'btablename', ),
                qs.where( qs.funcs.eq( qs.Var('a'), 17 )),
            ))),
        dict( a=8, b='x', **makeid()),
        ]
    txkey = log( db.tx, docs2, table= 'btablename' )

log( db.query, qs.s(
            qs.fromtable( 'btablename', )
            ), after_tx = txkey )
print('======')
docs3 = [
    db.make_tx_insert_many( qs.s(
            qs.fromtable( 'btablename', ),
        ), table= 'atablename'),
    dict( a=321, b='x', **makeid()),
    ]
txkey = log( db.tx, docs3, table= 'atablename' )
r = log( db.query, qs.s(
        qs.pipeline(
            qs.fromtable( 'atablename', ),
            qs.where( qs.funcs.eq( qs.Var('a'), 9 )),
        )), after_tx = txkey )

print('======')
docs4 = [
    db.make_tx_erase( r[0][ db.id_name ], table= 'atablename'),
    ]
txkey = log( db.tx, docs4 )
log( db.query, qs.s(
        qs.pipeline(
            qs.fromtable( 'atablename', ),
            qs.where( qs.funcs.eq( qs.Var('a'), 9 )),
        )), after_tx = txkey )

# vim:ts=4:sw=4:expandtab
