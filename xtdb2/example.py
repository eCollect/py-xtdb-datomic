from xtdb2.dbclient import xtdb2, Keyword, Symbol
import sys
db = xtdb2( [*sys.argv[1:2], 'http://localhost:3000' ][0] )
docs = [
    dict( a=1, b=2, **{ db.id_name: 15}) ,
    dict( a=2, b=3, **{ db.id_name: 16}) ,
    dict( a=2, b=4, **{ db.id_name: 18}) ,
    ]
txkey = db.tx( docs, table= 'atable' )

from xtdb2 import qs
qs.sym = Symbol
qs.kw = Keyword
qs.sym_wild = Symbol( '*')
from xtdb2.qs import *
print( *db.query( s(
    pipeline(
        fromtable( 'atable', ), #all of it
        where( funcs.eq( Var('a'), 2 )),
        with_columns( z= funcs.add( Var('b'), 1) ),
        orderby( orders={ db.id_name: True } ),
        limit( 3),
        )),
    after_tx= txkey,    #eh.. no db.sync yet
    ), sep='\n')

# vim:ts=4:sw=4:expandtab
