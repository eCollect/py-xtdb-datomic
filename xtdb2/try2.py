#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dbclient import xtdb2, log
import datetime
from pprint import pprint
import uuid
from base.qsyntax import sym, kw, kw2, var

import os
PORT= os.getenv( 'PORT') or '3001'
URL = os.getenv( 'XTDB') or f'http://localhost:{PORT}'
db = xtdb2( URL)

#log( db.status )

docs = [
    dict( a=1, b='bb'),
    dict( a=2, c= 12.45 ),
    dict( a=32, c= 12.4 ),
    ] #datetime.datetime.now() ) ]
for d in docs: d.update( { db.id_name: uuid.uuid4() })
#no tablename - use single default, atablename

if 10:
    log( db.tx, docs  )

from transit.transit_types import TaggedValue

symFROM = sym('from')
log( db.query,
    #'from :atablename [a b c]' -> expects SQL
    #( sym('->'),
     ( symFROM, kw('atablename'), [ sym('*') ] ) ,
     #( symFROM, kw('atablename'), [ sym(x) for x in ['a', 'b', 'c' ]] ) ,
     #( sym('where'), (sym('='), sym('a'), 2 )),
    #)
    )
if 0: dict(
    after_tx = TaggedValue( 'xtdb/tx-key', {
        'tx-id': 612343,
        'system-time':
            #datetime.datetime( 2024, 1, 10, 11, 8, 36, 422964, tzinfo =datetime.UTC)
            TaggedValue( 'time/instant',"2024-01-10T11:08:36.422964Z")
        })
        #{Keyword(tx-id): 612343, Keyword(system-time): datetime.datetime(2024, 1, 10, 11, 8, 36, 422964, tzinfo=tzutc())}
        #["~#xtdb/tx-key",["^ ","~:tx-id",612343,"~:system-time",["~#time/instant","2024-01-10T11:08:36.422964Z"]]]
    )
if 10:
    from xtdb2 import qs2
    qs2.sym = sym
    qs2.kw = kw
    qs2.sym_wild = sym( '*')

    log( db.query, qs2.s(
        qs2.fromtable( 'xt/txs',  )
        ))
    log( db.query, qs2.s(
        qs2.pipeline(
            qs2.fromtable( 'xt/txs',  ),
            #qs2.aggregate( qs2.funcs.aggr_max( sym('xt/id'))), no
            qs2.orderby(
                #sym('xt/id') ,
                #qs2.OrderSpec( sym('xt/id') , desc=True),
                orders= { sym('xt/id'): True }
                ),
            qs2.limit(1)
            )
        ))
if 0:
    log( db.query, qs2.s(
        qs2.fromtable( 'atablename', 'a', 'b' )
        ))

# vim:ts=4:sw=4:expandtab