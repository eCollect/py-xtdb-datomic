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
    dict( a=2, c= 12.45 )
    ] #datetime.datetime.now() ) ]
for d in docs: d.update( { db.id_name: uuid.uuid4() })
#no tablename - use single default, atablename

log( db.tx, docs  )

kwFROM = kw('from')
symFROM = sym('from')
log( db.query,
    #'from :atablename [a b c]' -> expects SQL
    #{ 'from': 'atablename', 'bind': ['a', 'b', 'c'] }  #no
    ( sym('->'),
     ( symFROM, kw('atablename'), [ sym(x) for x in ['a', 'b', 'c' ]] ) ,
     ( sym('where'), (sym('='), sym('a'), 2 )),
    )

    #[ sym('->'),
    #    ( symFROM, kw('atablename'), [ sym(x) for x in ['a', 'b', 'c' ]] )
    #    ]
    )

# vim:ts=4:sw=4:expandtab
