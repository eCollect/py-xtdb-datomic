# -*- coding: utf-8 -*-

class symkw_by_attr:
    ''' factory for symbol/keyword via attr.
    example: given kw = symkw_by_attr( Keyword)
        kw.a and kw('a') both produce Keyword( 'a')
        As funccall, name may contain one / , and whatever else allowed
        so kw('a/b') IS allowed ; kw('a/b/c') IS NOT allowed ; kw('=>>-?a.b.d/c.e') IS allowed
    '''
    def __init__( me, func, pfx =''):
        me.func = func
        me.pfx = pfx
        assert isinstance( pfx, str), pfx
    def __call__( me, k):
        assert k
        name = me.pfx + k
        assert name.count('/') <= 1, f'only one / allowed: {name}'
        if name != '/':     #special case: / alone is ok
            for p in name.split('/'): assert p
        return me.func( name)
    __getattr__ = __call__


class QSError( RuntimeError): pass
def qs_assert( cond, msg, *values):
    if not cond: raise QSError( ': '.join( [ msg ] + [repr(v) for v in values]))
def qs_assert_many( values, condfunc, what, allow_empty =False):
    assert callable( condfunc), condfunc
    qs_assert( isinstance( values, (tuple,list)), f'needs tuple/list of {what}', values)
    if not allow_empty: qs_assert( values, f'missing {what}')
    msg = f'needs {what}'
    for v in values:
        qs_assert( condfunc(v), msg, v)

def qs_assert_naming( cond, msg, *values, ):
    if not cond: raise QSError( ': '.join( [ 'naming', msg ] + [repr(v) for v in values]))
def qs_assert_naming_non_empty_str( x):
    qs_assert_naming( x and isinstance( x, str), 'name-or-prefix needs non-empty string', x)
_nonalnum = ''.join( '. * + ! - _ ? $ % & = < >   : #'.split())
def qs_check_sym_name_level( x):
    'single level, exclude /, cannot start with :#digit, ..'
    qs_assert_naming_non_empty_str( x )
    qs_assert_naming( x[0] not in ':#0123456789', 'name-or-prefix cannot start with ":" or "#" or digit', x)
    if x[0] in '-+.':
        qs_assert_naming( len(x) == 1 or not x[1].isdigit(), 'name-or-prefix cannot have digit after starting "." or "-" or "+"', x)
    qs_assert_naming( all( (c.isalnum() or c in _nonalnum) for c in x), 'name-or-prefix allows alphanumerics and '+repr(_nonalnum), x)

class symkw_by_attr_picky( symkw_by_attr):
    check_name_level = staticmethod( qs_check_sym_name_level)         #XXX eventualy override with something less-permissive..
    def is_symbol_func( me): return 'sym' in me.func.__name__.lower()
    def __call__( me, k):
        qs_assert_naming_non_empty_str( k )
        name = me.pfx + k
        qs_assert_naming( name.count('/') <= 1, 'only one / allowed', name)
        if not me.is_symbol_func() or name != '/':     #special case: Symbol(/) alone is ok
            for p in name.split('/'): me.check_name_level( p)
        return me.func( name)
    __getattr__ = __call__

# vim:ts=4:sw=4:expandtab
