#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from transit.reader import JsonUnmarshaler
#from transit.decoder import Decoder
from tt.decode import Decoder
from transit.writer import Writer, JsonMarshaler
from transit import write_handlers
from io import StringIO

from tt.encode import Encoder
from tt import encode
print( *( f'{k}={v}\n' for k,v in [*Encoder.__dict__.items(), *encode.__dict__.items()] if k[:2]=='X_' ))

json_cfg = dict(
    ensure_ascii= False,      #nonascii -> utf8, not \u430
    separators= (',', ':'),  #no whitespaces
    )


pj = Encoder()
def dump_py2ttpy( x):
    return pj.encode( x)
def dump_py2ttpy2json( x):
    ttpy = dump_py2ttpy( x)
    return json.dumps( ttpy, **json_cfg)

wrt = hasattr( JsonMarshaler, 'reset') and JsonMarshaler( None)

if 0:
    dt_tag = 'time/instant'
    if not getattr( write_handlers, 'X_wHandler', 0):
     class wMapHandler_auto_keywordize( write_handlers.MapHandler):
        @staticmethod
        def rep(m): return {
                        (Keyword( k) if k.__class__ is not Keyword else k):v
                        for k,v in m.items() }
     class wDatetimeHandler( write_handlers.VerboseDateTimeHandler):
        @staticmethod
        def tag(_): return dt_tag

     class wListHandler:
        @staticmethod
        def tag(_): return 'list'
        rep = list
    else:
        wHandler = write_handlers.wHandler
        wMapHandler_auto_keywordize = wHandler.copy( write_handlers.MapHandler,
            rep= lambda m: {
                        (Keyword( k) if k.__class__ is not Keyword else k):v
                        for k,v in m.items() }
            )
        wDatetimeHandler = wHandler.copy( write_handlers.VerboseDateTimeHandler,
            tag= dt_tag
            )
        wListHandler = wHandler( tag= 'list',
            rep= list,
            str= write_handlers.rep_None
            )
    import datetime
    wrt.register( dict, wMapHandler_auto_keywordize)
    wrt.register( datetime.datetime, wDatetimeHandler)
    #wrt.register( List, wListHandler)     #tuple==list==array/vector
    wrt.register( tuple, wListHandler)     #tuple -> xtdb/list i.e. sequence ; list -> vector

def dump_py2json( x): #OMG.. this produces text-as-out-of-json-dumps
    buf = StringIO()
    if not wrt:
        w = Writer( buf, 'json' )
        w.write( x )
    else:
        wrt.reset( buf)
        wrt.marshal_top( x)
    value = buf.getvalue()
    #valuebytes = value.encode( 'utf8')
    return value #bytes


rdr = Decoder()     #for small data, this Decoder() is slower than the .decode :/
def load_ttpy2py( ttpy):
    return rdr.decode( ttpy)
def load_json2ttpy2py( jstr):
    #x = x.decode( 'utf8')      #hope it's utf8 XXX ??
    ttpy = json.loads( jstr)
    return load_ttpy2py( ttpy)
def load_json2ttpy2py_org( jstr):
    from transit.reader import Reader
    rdr = Reader( protocol= 'json')
    #rdr.register( dt_tag, DateHandler)
    #rdr.register( txkey_handler._tag, txkey_handler)
    return rdr.read( StringIO( jstr))
def load_ttpy2py_org( ttpy):
    from transit.decoder import Decoder
    rdr = Decoder()
    #rdr.register( dt_tag, DateHandler)
    #rdr.register( txkey_handler._tag, txkey_handler)
    return rdr.decode( ttpy)

import sys, json, pprint #, os.path
import timeit #.timeit .repeat
for f in sys.argv[1:]:
    if f =='-':
        fi = sys.stdin
        f = 'stdin'
    else:
        fi = open( f)

    indata = fi.read()
    loaded = json.loads( indata)
    parsed = load_ttpy2py( loaded)
    outdata1= dump_py2json( parsed)
    dumped1 = json.loads( outdata1)
    dumped2 = dump_py2ttpy( parsed)
    outdata2= json.dumps( dumped2, **json_cfg)
    print( f,'..')
    def eqtest( **ka):
        (ka,a),(kb,b) = ka.items()
        sa = a.strip() if isinstance( a, str) else a
        sb = b.strip() if isinstance( b, str) else b
        if sa!=sb:
            print( f'XXXXXXXXXXX {ka} != {kb}:', )#sa, sb)
        return sa,sb
    si,so = eqtest( indata= indata, outdata1= outdata1)
    si,so = eqtest( indata= indata, outdata2= outdata2)
    si,so = eqtest( outdata1= outdata1, outdata2= outdata2)
    sl,sd = eqtest( loaded= loaded, dumped1= dumped1)
    sl,sd = eqtest( loaded= loaded, dumped2= dumped2)
    sl,sd = eqtest( dumped1= dumped1, dumped2= dumped2)
    if 0:
        from itertools import zip_longest
        for pos,(i,o) in enumerate( zip_longest( indata_strip, outdata_strip)):
            assert i==o, (pos,i,o)

    def ptimeit( func, arg, n):
        import gc
        gc.collect()
        print( ' ', func.__name__, n,
            round( sorted( timeit.repeat( lambda: func( arg),
            #timeit.timeit( lambda: func( arg),
                setup= 'gc.enable();gc.collect()',   #do not disable it
                repeat=8,
                number= n))[0]
            , 3))


    Nload = 200
    Ndump1= 200
    Ndump2= 200
    MANY=20
    parsed_many = [ parsed ] * MANY
    loaded_many = loaded * MANY

    ptimeit( load_ttpy2py,      loaded, Nload)
    #ptimeit( load_ttpy2py,      loaded_many, Nload//MANY)
    #ptimeit( load_json2ttpy2py, indata, Nload)
    #ptimeit( load_json2ttpy2py_org, indata, Nload)
    ptimeit( load_ttpy2py_org,  loaded, Nload)
    #ptimeit( dump_py2json,      parsed, Ndump1)
    ptimeit( dump_py2ttpy2json, parsed, Ndump2)
    ptimeit( dump_py2ttpy,      parsed, Ndump2)
    ptimeit( dump_py2ttpy,      parsed_many, Ndump2//MANY)

    fname = f.split('/')[-1]
    for stage in 'loaded parsed dumped1 dumped2 outdata1 outdata2'.split():
        with open( fname + '.' + stage, 'w') as fo:
            data = locals()[ stage ]
            fo.write( str(type(data))+'\n')
            fo.write( data if isinstance( data, (str, bytes)) else pprint.pformat( data))
    #print( ' loaded ?= dumped:', loaded == dumped)
#if 0:
    import cProfile
    def loaddump100():
        #for i in range(Nload): load_ttpy2py( loaded)
        #for i in range(Ndump1): dumps_py2json( parsed)
        for i in range(Ndump2): dump_py2ttpy( parsed)
        #for i in range(Ndump3): dump_py2ttpy( parsed_many)
    cProfile.run( 'loaddump100()', fname+'.profile')
    import pstats, os
    cwd = os.getcwd()
    def func_strip_path(func_name):
        filename, line, name = func_name
        if filename.startswith( cwd): filename = './'+filename[ len(cwd):]
        #if options.rootstrip:
        #    filename = re.sub( options.rootstrip, '##', filename)
        #if options.strip:
        #    filename = re.sub( options.strip, '.#', filename)
        return filename, line, name
    pstats.func_strip_path = func_strip_path
    p = pstats.Stats( fname+'.profile')
    p.strip_dirs()
    p.sort_stats('time')
    p.print_stats( 25)

#
# $ PYTHONPATH=. py bench*.py transit-format/examples/0.8/example.json

# vim:ts=4:sw=4:expandtab
