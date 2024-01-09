
''' xtql grammar/builder, with most type/semantic checks
https://docs.xtdb.com/reference/main/xtql/queries.html
https://docs.xtdb.com/reference/main/stdlib.html
https://docs.xtdb.com/reference/main/stdlib/predicates.html
'''
from dataclasses import dataclass, InitVar, replace as dc_replace, KW_ONLY
from typing import Dict, List, Union, ForwardRef as _ForwardRef, _eval_type    #ClassVar TypeVar Optional, Any,
import datetime

dataclass = dataclass( frozen= True)

_forwards = []
def Forward( x):
    'use this instead of ForwardRef/str'
    f = _ForwardRef( x)
    _forwards.append( f)
    return f

#tx_time === system_time

def sym( x): return '%'+x
def kw( x):  return ':'+x
sym_wild = sym( '*')

def s( x, name_as_sym =False):
    if isinstance( x, (list,tuple)):
        return [ s( i, name_as_sym= name_as_sym) for i in x ]
    #if isinstance( x, dict): only 2 occassions
    #    return dict( (k,s(v)) for k,v in x.items())
    m = getattr( x, 's', None)
    if m: return m( name_as_sym= name_as_sym)
    return x
def s_sym( name, *args):
    return (sym( name), *s( args))
def _init_items( me, name, type, items, allow_empty =False, allow_these =()):
    if not allow_empty:
        assert items
    for i in items:
        assert isinstance( i, type) or i in allow_these, i
    object.__setattr__( me, name, items)    #dataclass.frozen
def _init_item( me, name, type, item, allow_empty =False, convert =False):
    if item is None:
        assert allow_empty
    else:
        if convert: item = type( item)
        assert isinstance( item, type), item
    object.__setattr__( me, name, item)     #dataclass.frozen
def _init_convert_items( me, name, type, items, *keep_these, allow_empty =False):
    _init_items( me, name, type,
            [ b if isinstance( b, type) or b in keep_these else type( b) for b in items ],
            allow_these= keep_these, allow_empty= allow_empty )


class Source: 'op/source'
class Transform: 'op/tail'

Name = str      #column-name or var-name
Column = str    #?? needed to differ or not? XXX
class Var( str):
    '-> symbol'
    def s( me, **kaignore): return sym( me)
class Param( str):
    '-> $symbol'
    def s( me, **kaignore): return sym( '$'+ me)

class Func: pass

Timestamp = Union[ datetime.date, datetime.datetime ] #.datetime either naive or timezoned
class TemporalFilter:
    '''
      (at Timestamp)
    | (from Timestamp)
    | (to Timestamp)
    | (in Timestamp Timestamp)
    | :all-time

    >>> test( at( datetime.date(2024, 1, 9) ))
    at(timestamp=datetime.date(2024, 1, 9))
     ('%at', datetime.date(2024, 1, 9))
    >>> test( since( datetime.datetime(2024, 1, 9, 15, 23) ))
    since(timestamp=datetime.datetime(2024, 1, 9, 15, 23))
     ('%from', datetime.datetime(2024, 1, 9, 15, 23))
    >>> test( since( 123))
    Traceback (most recent call last):
    ...
    AssertionError: 123
    '''

@dataclass
class _TemporalFilter1( TemporalFilter):
    timestamp: Timestamp
    def __init__( me, timestamp):
        _init_item( me, 'timestamp', Timestamp, timestamp)
    def s( me, **kaignore):
        return s_sym( me.xtql, me.timestamp)
class at(    _TemporalFilter1): xtql = 'at'
class since( _TemporalFilter1): xtql = 'from'
class until( _TemporalFilter1): xtql = 'to'
@dataclass
class between( TemporalFilter):
    since: Timestamp
    until: Timestamp
    def s( me, **kaignore):
        return s_sym( 'in', me.since, me.until)
@dataclass
class all_time( TemporalFilter):
    def s( me, **kaignore):
        return kw( 'all-time')
all_time = all_time()   #singleton


@dataclass
class _query:
    query: Forward( 'Query')
    args: List[ Forward( 'ArgSpec') ] =()
    def __init__( me, query, *argsargs, args= ()):
        #TODO args as dict ?
        if isinstance( args, dict):
            args = tuple( ArgSpec( k,v) for k,v in args.items())
        _init_item( me, 'query', Query, query)
        assert not (args and argsargs)
        _init_convert_items( me, 'args', ArgSpec, args or argsargs)
    def s( me, **kaignore):
        return s_sym( me.xtql, me.query, dict( args= s( me.args)))
class subquery( _query):
    '''
    >>> test( subquery( fromtable( 'tbl', 'a'), args= [ 'b', Name_Expr( 'c', 2) ] ))
    subquery(query=fromtable(table='tbl', binds=[Name_Expr(name='a', expr=None)], time_valid=None, time_tx=None), args=[Name_Expr(name='b', expr=None), Name_Expr(name='c', expr=2)])
     ('%q', ('%from', ':tbl', ['%a']), {'args': ['%b', {':c': 2}]})
    >>> test( subquery( fromtable( 'tbl', 'a'), args= dict( b=None, c=2) ))
    subquery(query=fromtable(table='tbl', binds=[Name_Expr(name='a', expr=None)], time_valid=None, time_tx=None), args=[Name_Expr(name='b', expr=None), Name_Expr(name='c', expr=2)])
     ('%q', ('%from', ':tbl', ['%a']), {'args': ['%b', {':c': 2}]})
    '''
    xtql = 'q'
class exists( _query):   xtql = 'exists'
@dataclass
class pull( _query):
    '''
    >>> test( pull( fromtable( 'tbl', 'a'), args= dict( b=None, c=2), many=True ))
    pull(query=fromtable(table='tbl', binds=[Name_Expr(name='a', expr=None)], time_valid=None, time_tx=None), args=[Name_Expr(name='b', expr=None), Name_Expr(name='c', expr=2)], many=True)
     ('%pull*', ('%from', ':tbl', ['%a']), {'args': ['%b', {':c': 2}]})
    '''
    many: bool =False
    @property
    def xtql( me):
        return 'pull*' if me.many else 'pull'
    def __init__( me, *args, many =False, **ka):
        _init_item( me, 'many', bool, many, convert= True)
        super().__init__( *args, **ka)


Expr = Union[ #None,    no None plz
            int, float, #decimal ?
            str, bool,
            #TODO Temporal, TemporalAmount,   #ObjectExpr ?? datetime / duration ??
            #TODO List[ Forward( 'Expr') ],             #VectorExpr
            #set[ Expr ] ?              #SetExpr
            #TODO Dict[ str, Forward( 'Expr') ],        #MapExpr -> {:str expr, ..}     XXX list-of-dicts is used in relation
            Param,                      #-> $symbol
            Var,                        #-> symbol
            Func,
            subquery,
            exists,
            pull,
            ]
Expr_or_None = Union[ Expr, None ]

@dataclass
class attrget( Func):
    '''fn/. i.e. getattr
    >>> test( attrget( 'a', 'b'))
    attrget(expr='a', attr='b')
     ('%.', 'a', '%b')
    '''
    expr: Expr
    attr: Name
    def s( me, **kaignore):
        return s_sym( '.', me.expr, sym( me.attr))

@dataclass
class _items( Func):
    items: List[ Expr ]
    def __init__( me, *items):
        _init_items( me, 'items', Expr, items)
        assert me.__class__ is not _items
    def s( me, **kaignore):
        return s_sym( me.xtql, *me.items)
@dataclass
class _item( Func):
    expr: Expr
    def __init__( me, expr):
        _init_item( me, 'expr', Expr, expr)     #XXX can it be None?
        assert me.__class__ is not _item
    def s( me, **kaignore):
        return s_sym( me.xtql, me.expr)
Predicate = Union[ _items, _item ]


@dataclass
class Name_Expr:
    '''name is keyword=column-or-param if expr, else a symbol=somevar
    >>> test( Name_Expr( 'a', 'b'))
    Name_Expr(name='a', expr='b')
     {':a': 'b'}
    >>> test( Name_Expr( 'a'))
    Name_Expr(name='a', expr=None)
     %a
    >>> test( Name_Expr( 'a', 'b'), name_as_sym=True)
    Name_Expr(name='a', expr='b')
     {'%a': 'b'}
    '''
    name: Name
    expr: Expr =None
    def s( me, name_as_sym =False):
        if me.expr is None: return sym( me.name)
        name = (sym if name_as_sym else kw)( me.name)
        return { name: s( me.expr) }

BindSpec = Name_Expr


@dataclass
class fromtable( Source):
    '''
    >>> test( fromtable( 'tbl', 'a', 'b'))
    fromtable(table='tbl', binds=[Name_Expr(name='a', expr=None), Name_Expr(name='b', expr=None)], time_valid=None, time_tx=None)
     ('%from', ':tbl', ['%a', '%b'])
    >>> test( fromtable( 'tbl', 'a', whole=True, time_valid= all_time, time_tx= at( datetime.date( 2024, 1, 5))))
    fromtable(table='tbl', binds=['%*', Name_Expr(name='a', expr=None)], time_valid=all_time(), time_tx=at(timestamp=datetime.date(2024, 1, 5)))
     ('%from', ':tbl', {'bind': ['%*', '%a'], 'for-valid-time': ':all-time', 'for-system-time': ('%at', datetime.date(2024, 1, 5))})
    >>> test( dc_replace( fromtable( 'tbl', 'a', whole=True),  binds= ['b','c']))
    fromtable(table='tbl', binds=[Name_Expr(name='b', expr=None), Name_Expr(name='c', expr=None)], time_valid=None, time_tx=None)
     ('%from', ':tbl', ['%b', '%c'])

    '''
    table:  str  #identifier?
    binds:  List[ BindSpec ]
    whole:  InitVar =False
    time_valid: TemporalFilter =None
    time_tx:    TemporalFilter =None
    def __init__( me, table, *argsbinds, binds= (), whole =False, time_valid =None, time_tx =None):
        _init_item( me, 'table', str, table)
        _init_item( me, 'time_valid', TemporalFilter, time_valid, allow_empty= True)
        _init_item( me, 'time_tx',    TemporalFilter, time_tx,    allow_empty= True)
        assert not (binds and argsbinds)
        binds = list( binds or argsbinds)
        if not binds: whole = True
        if whole and sym_wild not in binds:
            binds.insert( 0, sym_wild)
        _init_convert_items( me, 'binds', BindSpec, binds, sym_wild )
    def has_whole( me):
        return sym_wild in me.binds
    def s( me, **kaignore):
        if me.time_valid is None and me.time_tx is None:
            args = me.binds
        else:
            args = dict(
                bind = s( me.binds),
                **({} if me.time_valid is None else {'for-valid-time' : s( me.time_valid) }),
                **({} if me.time_tx    is None else {'for-system-time': s( me.time_tx) }),
                )
        return s_sym( 'from', kw( me.table), args )


@dataclass #( frozen= True)
class relation( Source):
    '''op/rel - can come from constant, query-argument, value-in-another-doc (as Transform?)
    >>> test( relation( 'myrel', 'a', 'b'))
    relation(expr='myrel', binds=[Name_Expr(name='a', expr=None), Name_Expr(name='b', expr=None)])
     ('%rel', 'myrel', ['%a', '%b'])

    #>>> test( relation( [ dict(a=1, b=2), dict( a=3,b=4)] ))
    #relation(expr=[{'a': 1, 'b': 2}, {'a': 3, 'b': 4}], binds=[])
    # ('%rel', [{:a 1, :b 2}, {:a 3, :b 4}])
    '''
    expr: Expr
    binds: List[ BindSpec ]
    def __init__( me, expr, *argsbinds, binds= ()):
        _init_item( me, 'expr', Expr, expr)
        assert not (binds and argsbinds)
        _init_convert_items( me, 'binds', BindSpec, binds or argsbinds)
    def s( me, **kaignore):
        return s_sym( 'rel', me.expr, me.binds )
rel = relation

ArgSpec = Name_Expr

@dataclass
class join:
    '''op/join
    >>> test( join( fromtable( 'tbl', whole=True), 'x'))
    join(query=fromtable(table='tbl', binds=['%*'], time_valid=None, time_tx=None), binds=[Name_Expr(name='x', expr=None)], args=[])
     ('%join', ('%from', ':tbl', ['%*']), ['%x'])
    '''
    xtql = 'join'
    query:  Forward( 'Query')
    binds:  List[ BindSpec ]
    args:   List[ ArgSpec ] =()
    def __init__( me, query, *argsbinds, binds =(), args =()):
        _init_item( me, 'query', Query, query)
        assert not (binds and argsbinds)
        _init_convert_items( me, 'binds', BindSpec, binds or argsbinds)
        _init_convert_items( me, 'args', ArgSpec, args, allow_empty= True)
    def s( me, **kaignore):
        return s_sym( me.__class__.xtql,
                me.query,
                me.binds if not me.args else
                    dict( bind= s( me.binds ), args= s( me.args))
                )
class leftjoin( join):
    xtql = 'left-join'


@dataclass
class where( Transform):
    '''op/where
    >>> test( where( p_gt( 'a', 'b'), p_min( 'a', 'b') ))
    where(predicates=(p_gt(items=('a', 'b')), p_min(items=('a', 'b'))))
     ('%where', ('%>', 'a', 'b'), ('%least', 'a', 'b'))
    '''
    predicates: List[ Predicate ]
    def __init__( me, *argspreds, predicates =()):
        _init_items( me, 'predicates', Predicate, predicates or argspreds)
    def s( me, **kaignore):
        return s_sym( 'where', *me.predicates)

@dataclass
class OrderSpec:
    '''expr     -> val= expr
     desc       -> dir= :desc or :asc
     nulls_last -> nulls= :last or :first
    '''
    expr: Expr
    _: KW_ONLY
    desc:       bool =None
    nulls_last: bool =None
    def s( me, **kaignore):
        if me.desc is None and me.nulls_last is None:
            return s( me.expr)      #shortcut
        return dict(
            val= s( me.expr),
            **({} if me.desc is None else dict( dir= kw( 'desc' if me.desc else 'asc'))),
            **({} if me.nulls_last is None else dict( nulls = kw( 'last' if me.nulls_last else 'first'))),
            )

@dataclass
class orderby( Transform):
    '''op/order-by
    >>> test( orderby( 'a', OrderSpec( 'c', desc=3), b=True, d= dict( desc=True, nulls_last=True) ))
    orderby(orders=[OrderSpec(expr='a', desc=None, nulls_last=None), OrderSpec(expr='c', desc=3, nulls_last=None), OrderSpec(expr='b', desc=True, nulls_last=None), OrderSpec(expr='d', desc=True, nulls_last=True)])
     ('%order-by', 'a', {'val': 'c', 'dir': ':desc'}, {'val': 'b', 'dir': ':desc'}, {'val': 'd', 'dir': ':desc', 'nulls': ':last'})
    '''
    orders: List[ OrderSpec ]
    def __init__( me, *argsorders, orders =(), **kargsorders):
        kaorders = tuple( OrderSpec( k, **(v if isinstance( v, dict) else dict( desc= v )))
                            for k,v in kargsorders.items() )
        _init_convert_items( me, 'orders', OrderSpec, (argsorders or orders) + kaorders)
    def s( me, **kaignore):
        return s_sym( 'order-by', *me.orders)

@dataclass
class limit( Transform):
    '''op/limit
    >>> test( limit( 34))
    limit(value=34)
     ('%limit', 34)
    '''
    xtql = 'limit'
    value: int #TODO non-negative
    def s( me, **kaignore):
        return (sym( me.xtql), me.value)
class offset( limit):
    xtql = 'offset'
    __docs__ = '''
    >>> test( offset( 4))
    offset(value=4)
     ('%offset', 4)
    '''


@dataclass
class unnest( Transform):
    '''op/unnest - differs in pipeline:name=col vs unify/name=var/logicvar
    >>> test( unnest( 'a', 'b'))
    unnest(name='a', expr='b')
     ('%unnest', {':a': 'b'})
    >>> test( unnest( 'a', 'b'), name_as_sym=True)
    unnest(name='a', expr='b')
     ('%unnest', {'%a': 'b'})
    >>> test( unnest( 'a'))
    Traceback (most recent call last):
    ...
    TypeError: unnest.__init__() missing 1 required positional argument: 'expr'
    '''
    name: Name
    expr: Expr
    def s( me, name_as_sym =False):
        name = (sym if name_as_sym else kw)( me.name)
        return (sym( 'unnest'), { name: s( me.expr) })


@dataclass
class without_columns( Transform):
    '''op/without
    >>> test( without_columns( 'a', 'b'))
    without_columns(columns=('a', 'b'))
     ('%without', ':a', ':b')
    >>> test( without_columns())
    Traceback (most recent call last):
    ...
    AssertionError
    '''
    columns: List[ Column ]
    def __init__( me, *columns):
        _init_items( me, 'columns', Column, columns)
    def s( me, **kaignore):
        return s_sym( 'without', *( kw(c) for c in me.columns))

def _init_convert_items2( me, name, type, items, kaitems):
    kaitems = tuple( type( k,v) for k,v in kaitems.items() )
    _init_convert_items( me, name, type, items + kaitems)

ReturnSpec = Name_Expr
@dataclass
class exact_columns( Transform):
    '''op/return - name=col if-expr-else =var
    >>> test( exact_columns( 'a', b= funcs.add( 'c', 1)))
    exact_columns(columns=[Name_Expr(name='a', expr=None), Name_Expr(name='b', expr=func_any(name='add', args=('c', 1)))])
     ('%return', '%a', {':b': ('%+', 'c', 1)})
    >>> test( exact_columns( 'a' ))
    exact_columns(columns=[Name_Expr(name='a', expr=None)])
     ('%return', '%a')
    >>> test( exact_columns())
    Traceback (most recent call last):
    ...
    AssertionError
    '''
    columns: List[ ReturnSpec ]
    def __init__( me, *columns, **kacolumns):
        _init_convert_items2( me, 'columns', ReturnSpec, columns, kacolumns)
    def s( me, **kaignore):
        return s_sym( 'return', *me.columns)

WithSpec = Name_Expr
@dataclass
class with_columns( Transform):
    '''op/with - differs in pipeline/name=col-if-expr vs unify/name=var-if-expr ; if no expr, name=var/withvar
    >>> test( with_columns( 'a', 'b'))
    with_columns(columns=[Name_Expr(name='a', expr=None), Name_Expr(name='b', expr=None)])
     ('%with', '%a', '%b')
    >>> test( with_columns( 'a', b= funcs.add( 'c', 1)))
    with_columns(columns=[Name_Expr(name='a', expr=None), Name_Expr(name='b', expr=func_any(name='add', args=('c', 1)))])
     ('%with', '%a', {':b': ('%+', 'c', 1)})
    >>> test( with_columns( 'a', b= funcs.add( 'c', 1)), name_as_sym=True)
    with_columns(columns=[Name_Expr(name='a', expr=None), Name_Expr(name='b', expr=func_any(name='add', args=('c', 1)))])
     ('%with', '%a', {'%b': ('%+', 'c', 1)})
    >>> test( with_columns())
    Traceback (most recent call last):
    ...
    AssertionError
    '''
    columns: List[ WithSpec ]
    def __init__( me, *columns, **kacolumns):
        _init_convert_items2( me, 'columns', WithSpec, columns, kacolumns)
    def s( me, name_as_sym =False):
        return (sym( 'with'), *s( me.columns, name_as_sym= name_as_sym))

AggrSpec = Name_Expr
@dataclass
class aggregate( Transform):    #TODO same as exact_columns/return?
    '''op/aggregate - name=col if-expr-else =var
    >>> test( aggregate( 'a', b= funcs.add( 'c', 1)))
    aggregate(items=[Name_Expr(name='a', expr=None), Name_Expr(name='b', expr=func_any(name='add', args=('c', 1)))])
     ('%aggregate', '%a', {':b': ('%+', 'c', 1)})
    >>> test( aggregate( 'a' ))
    aggregate(items=[Name_Expr(name='a', expr=None)])
     ('%aggregate', '%a')
    >>> test( aggregate())
    Traceback (most recent call last):
    ...
    AssertionError
    '''
    items: List[ AggrSpec ]
    def __init__( me, *items, **kaitems):
        _init_convert_items2( me, 'items', AggrSpec, items, kaitems)
    def s( me, **kaignore):
        return s_sym( 'aggregate', *me.items)
aggr = aggregate


UnifyClause = Union[ fromtable, relation, join, where, with_columns, unnest ]
@dataclass
class unify( Source):
    '''op/unify
    >>> test( unify(
    ...     fromtable( 'docs', 'my-nested-rel' ),
    ...     relation( 'my-nested-rel', 'a', 'b'),
    ...     where( p_gt( 'a', 'b'), p_min( 'a', 'b') ),
    ...     with_columns( 'a', x= 'b'),
    ...     ))
    unify(sources=(fromtable(table='docs', binds=[Name_Expr(name='my-nested-rel', expr=None)], time_valid=None, time_tx=None), relation(expr='my-nested-rel', binds=[Name_Expr(name='a', expr=None), Name_Expr(name='b', expr=None)]), where(predicates=(p_gt(items=('a', 'b')), p_min(items=('a', 'b')))), with_columns(columns=[Name_Expr(name='a', expr=None), Name_Expr(name='x', expr='b')])))
     ('%unify', ('%from', ':docs', ['%my-nested-rel']), ('%rel', 'my-nested-rel', ['%a', '%b']), ('%where', ('%>', 'a', 'b'), ('%least', 'a', 'b')), ('%with', '%a', {'%x': 'b'}))
    >>> test( unify(
    ...     fromtable( 'docs', whole=True ),
    ...     with_columns( 'a', x= 'b'),
    ...     ))
    Traceback (most recent call last):
    ...
        assert not i.has_whole(), i
    AssertionError: fromtable(table='docs', binds=['%*'], time_valid=None, time_tx=None)
    '''
    sources: List[ UnifyClause ]
    def __init__( me, *sources):
        _init_items( me, 'sources', UnifyClause, sources)
        for i in sources:
            #as of spec: cannot contain fromtable with whole/sym_wild'
            if isinstance( i, fromtable):
                assert not i.has_whole(), i
    def s( me, **kaignore):
        return (sym( 'unify'), *s( me.sources, name_as_sym= True))

@dataclass
class pipeline:
    '''op/->
    >>> test( pipeline(
    ...     fromtable( 'docs', 'a', 'b' ),
    ...     where( p_gt( 'a', 'b')),
    ...     ))
    pipeline(source=fromtable(table='docs', binds=[Name_Expr(name='a', expr=None), Name_Expr(name='b', expr=None)], time_valid=None, time_tx=None), transforms=(where(predicates=(p_gt(items=('a', 'b')),)),))
     ('%->', ('%from', ':docs', ['%a', '%b']), ('%where', ('%>', 'a', 'b')))
    >>> test( pipeline(
    ...     relation( 'a', 'b'),        #wrong i know
    ...     where( p_gt( 'a', 'b')),
    ...     ))
    pipeline(source=relation(expr='a', binds=[Name_Expr(name='b', expr=None)]), transforms=(where(predicates=(p_gt(items=('a', 'b')),)),))
     ('%->', ('%rel', 'a', ['%b']), ('%where', ('%>', 'a', 'b')))
    '''
    source: Source
    transforms: List[ Transform ] =()
    def __init__( me, source, *argstfs, transforms= ()):
        _init_item( me, 'source', Source, source)
        assert not (transforms and argstfs)
        _init_items( me, 'transforms', Transform, transforms or argstfs, allow_empty =True)
    def s( me, **kaignore):
        return s_sym( '->', me.source, *me.transforms)

Query = Union[ Source, pipeline ]

##############

class Comparator: pass
class p_lt( _items, Comparator): xtql= '<'
class p_le( _items, Comparator): xtql= '<='
class p_gt( _items, Comparator): xtql= '>'
class p_ge( _items, Comparator): xtql= '>='
class p_eq( _items, Comparator): xtql= '='
class p_ne( _items, Comparator): xtql= '<>'

class p_max( _items): xtql= 'greatest'
class p_min( _items): xtql= 'least'
p_greatest = p_max
p_least = p_min
class p_all( _items): xtql= 'and'
class p_any( _items): xtql= 'or'
p_and = p_all
p_or  = p_any
class p_not(    _item): xtql= 'not'
class p_true(   _item): xtql= 'true?'
class p_false(  _item): xtql= 'false?'
class p_null(   _item): xtql= 'nil?'

###############

@dataclass
class _func( Func):
    'fn/<name> - func-call name over args'
    name: Name
    args: List[ Expr ]
    _argsize = 1,None   #min=1
    _prefix = ''
    def __init__( me, name: Name, *args):
        _init_item( me, 'name', Name, name)
        amin,amax = me._argsize
        assert amin <= len( args ) <= (amax or 99), me._argsize
        assert name in me.get_allowed(), name
        _init_items( me, 'args', Expr, args, allow_empty= not amin)

    _allowed_flat = None
    @classmethod
    def get_allowed( klas):
        if klas._allowed_flat is not None:
            return klas._allowed_flat
        allowed = {}
        if isinstance( klas._allowed, dict):
            for k,v in klas._allowed.items():
                if isinstance( v, dict):    #category-dict
                    overlaps = set( v) & set( allowed)
                    assert not overlaps, overlaps
                    allowed.update( v)
                elif isinstance( v, list):  #category-list
                    overlaps = set( v) & set( allowed)
                    assert not overlaps, overlaps
                    allowed.update( dict.fromkeys( v))
                else: #direct-dict
                    assert k not in allowed, k
                    allowed[ k] = v
        elif isinstance( klas._allowed, list):  #direct-list
            overlaps = set( klas._allowed) & set( allowed)
            assert not overlaps, overlaps
            allowed.update( dict.fromkeys( klas._allowed))

        #also alias them to originals if usable
        for k,v in list( allowed.items()):
            if v and v != k and v.isalpha() and v.isascii(): #'-' not in v:
                assert v not in allowed, v
                allowed[ v] = v
        if klas._prefix:
            allowed = dict( (klas._prefix+k, v) for k,v in allowed.items())
        klas._allowed_flat = allowed
        return allowed

    def make_name( me):
        return me.get_allowed().get( me.name) or me.name
    def s( me, **kaignore):
        return s_sym( me.make_name(), *me.args)

    class Registry:
        def __init__( me):
            registry = {}
            for fc in _func.__subclasses__():   #XXX direct only!
                registry.update( dict.fromkeys( fc.get_allowed(), fc) )
            me._registry = registry
        def __getattr__( me, k):
            func = me._registry.get( k )
            if not func: raise AttributeError( k)
            return lambda *a,**ka: func( k, *a,**ka)

class func_any( _func):
    _allowed = dict(
        _arithmetic = dict( add= '+', sub= '-', mul= '*', div= '/'),
        _other      = 'coalesce'.split(),
        )
class func1( _func):
    _argsize = 1,1
    _allowed = dict(
        _numeric = 'abs ceil floor double exp ln log10 sqrt'.split(),
        _trigo   = 'sin cos tan  asin acos atan  sinh cosh tanh'.split(),
        _text    = dict( len= 'character-length', bytelen= 'octet-length', lower= None, upper= None, ), #TODO more octet-things
        )
class func2( _func):
    _argsize = 2,2
    _allowed = dict(
        _numeric = 'log mod power'.split(),
        _text    = 'like position trim trim_start trim_end'.split(),
        _other   = dict( null_if_eq= 'null-if'),
        _time    = dict( period= None, datetime_truncate= 'date-trunc', datetime_extract= 'extract'),
        )
class func23( _func):
    _argsize = 2,3
    _allowed = dict(
        _text    = dict( regex= 'like-regex', substr= 'substring'),
        )

class func_now( _func):
    _argsize = 0,0
    def __init__( me, *a, precision: str =None):
        _init_item( me, 'precision', str, precision)
        super().__init__( *a)
    def s( me, **kaignore):
        return s_sym( me.make_name(), *( [ me.precision ] if me.precision else ()))
    _allowed = dict( utc_datetime= 'current-timestamp', utc_date= 'current-date', utc_time= 'current-time',
                      local_datetime='local-timestamp', local_time= 'local-time')
class func_periods( _func):
    _argsize = 2,2
    _allowed = 'equals overlaps '.split()
class func_periods1( func_periods):
    def __init__( me, *a, strictly: bool =False):
        _init_item( me, 'strictly', bool, strictly, convert= True)
        super().__init__( *a)
    def make_name( me):
        return ('strictly-' if me.strictly else '') + super().make_name()
    _allowed = 'contains '.split()
class func_periods2( func_periods1):
    def __init__( me, *a, strictly: bool =False, immediately: bool =False ):
        assert not (strictly and immediately) #XXX: either immediately OR strictly, not both
        _init_item( me, 'immediately', bool, immediately, convert= True)
        super().__init__( *a, strictly= strictly)
    def make_name( me):
        return ('immediately-' if me.immediately else '') + super().make_name()
    _allowed = 'lags leads precedes succeeds'.split()

class func_aggr0( _func):
    _argsize = 0,0
    _allowed = dict( row_count= 'row-count')
    _prefix = 'aggr_'
class func_aggr1( _func):
    _argsize = 1,1
    _allowed = dict(
       _nums = dict( stddev_population= 'stddev-pop', stddev_sample= 'stddev-samp', variance_population= 'var-pop', variance_sample= 'var-samp'),
       _bools= 'all every any some'.split(),
       _comp = dict( array_aggr= 'array-agg'),
       )
    _prefix = 'aggr_'
class func_aggr2( _func):
    _argsize = 1,1
    def __init__( me, *a, distinct: bool =False):
        _init_item( me, 'distinct', bool, distinct, convert= True)
        super().__init__( *a)
    def make_name( me):
        return super().make_name() + ('-distinct' if me.distinct else '')
    _allowed = dict(
        _nums = dict( average= 'avg', **dict.fromkeys( 'count max min sum'.split()))    #XXX overlap max/min
        )
    _prefix = 'aggr_'

@dataclass
class f_let( Func):
    '''fn/let - eval .body(expr) for .name bound to .bind(expr)
    >>> test( f_let( 'a', 'b', 'c'))
    f_let(name='a', bind='b', body='c')
     ('%let', ['%a', 'b'], 'c')
    >>> test( funcs.let( 'a', 'b', 'c'))
    f_let(name='a', bind='b', body='c')
     ('%let', ['%a', 'b'], 'c')
    '''
    name: Name  #-> bind-symbol
    bind: Expr  #-> bind-expr
    body: Expr  #-> body-expr
    def s( me, **kaignore):
        return s_sym( 'let', [ sym( me.name), me.bind ], me.body )

@dataclass
class f_if( Func):
    '''fn/if
    >>> test( f_if( funcs.gt( 'a', 4), 45, 56))
    f_if(cond=p_gt(items=('a', 4)), then=45, orelse=56)
     ('%if', ('%>', 'a', 4), 45, 56)
    >>> test( funcs.iff( funcs.gt( 'a', 4), 45, 56))
    f_if(cond=p_gt(items=('a', 4)), then=45, orelse=56)
     ('%if', ('%>', 'a', 4), 45, 56)
    '''
    _aliases = [ 'if_', 'iff' ]
    cond: Expr  #-> predicate ? must return boolean
    then: Expr
    orelse: Expr
    def s( me, **kaignore):
        return s_sym( 'if', me.cond, me.then, me.orelse )

@dataclass
class f_ifsome( Func):
    '''fn/if-some - eval .then(expr) for name bound to .bind(expr) if it is non-null, else .orelse(expr)
    >>> test( f_ifsome( 'a', 'b', 'c', 'd'))
    f_ifsome(name='a', bind='b', then='c', orelse='d')
     ('%if-some', ['%a', 'b'], 'c', 'd')
    '''
    name: Name  #-> bind-symbol
    bind: Expr  #-> bind-expr
    then: Expr  #-> then-expr
    orelse: Expr#-> else-expr
    def s( me, **kaignore):
        return s_sym( 'if-some', [ sym( me.name), me.bind ], me.then, me.orelse )


@dataclass
class case:
    value: Expr     #=predicate if inside cond
    result: Expr

import itertools
@dataclass
class f_cond( Func):
    '''fn/cond
    >>> test( f_cond( case( 3, 45), case( funcs.add(7,8), 9) , default= -34))
    f_cond(cases=(case(value=3, result=45), case(value=func_any(name='add', args=(7, 8)), result=9)), default=-34)
     ('%cond', 3, 45, ('%+', 7, 8), 9, -34)
    '''
    cases: List[ case ]
    default: Expr =None
    def __init__( me, *cases, default :Expr =None):
        assert default or cases
        _init_item( me, 'default', Expr, default, allow_empty= True)
        _init_items( me, 'cases', case, cases)
    def s( me, **kaignore):
        return s_sym( 'cond', *me._scases())
    def _scases( me):
        return (
                *itertools.chain( *((c.value, c.result) for c in me.cases)),
                *( [ me.default ] if me.default is not None else ())
                )

@dataclass
class f_switch( Func):
    '''fn/case
    >>> test( f_switch( p_gt( 'a', 2), case( 3, 45), case( funcs.add(7,8), 9) , default= -34))
    f_switch(test=p_gt(items=('a', 2)), cases=(case(value=3, result=45), case(value=func_any(name='add', args=(7, 8)), result=9)), default=-34)
     ('%case', ('%>', 'a', 2), 3, 45, ('%+', 7, 8), 9, -34)
    '''
    test: Expr
    cases: List[ case ]
    default: Expr =None
    def __init__( me, test: Expr, *cases, default: Expr =None):
        _init_item( me, 'test', Expr, test)
        f_cond.__init__( me, default= default, *cases)
    def s( me, **kaignore):
        return s_sym( 'case', me.test, *f_cond._scases( me))

############# eo xtql things

def _all_subclasses_of( klas):
    'ALL subclasses of klas but klas itself ; depth-first ; recursive'
    res = dict()    #set() does not keep order
    for sub in klas.__subclasses__():
        res[ sub ] = None
        res.update( dict.fromkeys( _all_subclasses_of( sub)))
    return res

#common register of *all* funcs
funcs_registry = _func.Registry()
funcs = fn = funcs_registry
for f in _all_subclasses_of( Func):
    if f in (Func, _func, _item, _items): continue
    funcnames = [ f.__name__[2:], *getattr( f, '_aliases', ()) ]
    #also alias them to originals if usable
    fxtql = getattr( f, 'xtql', None)
    if fxtql and fxtql not in funcnames and fxtql.isalpha() and fxtql.isascii(): #'-' not in v:
        funcnames.append( f.xtql)
    for fname in funcnames:
        overlaps = getattr( funcs_registry, fname, None)
        assert not overlaps, (f, overlaps)
        setattr( funcs_registry, fname, f)


if __name__ == '__main__':
    if 0*'dbg':
        import typing
        typing.issubclass = lambda *a: [print('isc',*a),issubclass(*a)][-1]

    if 10:
      for f in _forwards:
        #if 'dbg': print(f)
        f._evaluate( globals(), globals(), frozenset() )
    else:
        _eval_type( Expr, globals(), globals())
    if 0:
        def fw__subclasscheck__( me, cls):
            if 'dbg': print( 'fw', cls)
            return issubclass( cls, me.__forward_value__ if me.__forward_evaluated__ else _ForwardRef)
        _ForwardRef.__subclasscheck__ = fw__subclasscheck__

    def test(e, name_as_sym =False):    #DO NOT TOUCH this
        print( str( e ) + '\n ' + str( s( e, name_as_sym= name_as_sym )))
    import doctest
    doctest.testmod( verbose=0*True, report=True, exclude_empty=True, optionflags = doctest.REPORT_NDIFF )
    #############

    def prn(e):
        print( f'{e}\n {s(e)}')

    p = fromtable( 'tbl', 'a', 'b')
    prn( p)

    p = fromtable( 'tbl', 'a', whole=True,
            time_valid = all_time, time_tx= at( datetime.date.today()))
    prn( p)
    q = dc_replace( p, binds= ['b','c'])
    prn(q)
    prn( leftjoin( q, 'x') )

    u2= unify(
        fromtable( 'docs', 'my-nested-rel' ),
        relation( 'my-nested-rel', 'a', 'b'),
        where( p_gt( 'a', 'b'), p_min( 'a', 'b') ),
        with_columns( 'a', x= 'b'),
        )
    prn(u2)

    c = f_switch( p_gt( 'a', 2), case( 3, 45), case( 7, 0) , default= -34)
    prn(c)
    o = orderby( 'a', OrderSpec( 'c', desc=1), b=True, d= dict( desc=True, nulls_last=True) )
    prn( o)
    prn( fn.aggr_row_count())
    prn( funcs.add(3,4))
    prn( funcs.let('a','b','c'))
    prn( funcs.aggr_max('a'))
    prn( funcs.max('a','b','c'))
    assert funcs.greatest('a','b','c') == funcs.max('a','b','c')


#TODO:
# - see Expr TODOs
# - specs as kargs fromtable( 'tbl', 'a', b=23)
# - .specs as dict(name:expr) and not list of Name_Expr ? helps for uniq-check
# - argsspecs and specs together? fromtable( 'tbl', 'a', binds= dict( b=23))
# + doctests
# + max/min all/any are both predicates and funcs
# + common register of all funcs


''' "grammar" - in somewhat lazy "syntax":
 * comments are  #... at eoline
 * usual grammar syntax of sequence a b c , and alternatives a | b | c , zero-or-more x* , one-or-more y+
 * grammatical classes are either Capitalized: or _underscored: , like X: y.. meaning "X is y.."
 * final elements are lowercase like some_name+= .. meaning they contain whats after that
 * actual packaging of multiples (list or map etc) is not represented

###############

query: Query _query_opt*
_query_opt: after_tx | _args | basis | tz_default | tx_timeout | explain | key_fn
#...

Query: Source | pipeline
Source: from_table | relation | unify

pipeline+= Source Transform*
Transform:
      where
    | limit | offset
    | unnest
    | without_columns | exact_columns | with_columns
    | aggregate

from_table+= _table_name _table_binds _table_options?
                                    # (from table { :bind: ..binds , :time_valid .., :time_tx .. })
_table_name: Name
_table_binds: _table_bind+
_table_bind: Name_Expr | wildcard
_table_options: time_valid? time_tx?
time_valid+= TemporalFilter
time_tx+= TemporalFilter
wildcard: '*'
TemporalFilter:
      at( Timestamp)                #  (at Timestamp)
    | since( Timestamp)             #| (from Timestamp)
    | until( Timestamp)             #| (to Timestamp)
    | between( Timestamp Timestamp) #| (in Timestamp Timestamp)
    | all_time                      #| :all-time

relation+= Expr _binds              # (rel expr [..binds])
_binds: Name_Expr+

unify+= _unify_item+
_unify_item: from_table | relation | join | join_left | where | with_columns | unnest

join+= Query _binds _args?          # (join      query { bind: ..binds, args: ..args })
join_left+= Query _binds _args?     # (left-join query { bind: ..binds, args: ..args })
_args: Name_Expr*

where+= F_predicate+

orderby+= _order_item+
_order_item: Expr _order_opt*
_order_opt: desc | nulls_last

limit+= int
offset+= int

unnest+= Name Expr

without_columns+= Name+          # (without ..
exact_columns+= Name_Expr+       # (return ..
with_columns+=  Name_Expr+       # (with ..

aggregate+= Name_Expr+

Name_Expr: Name Expr?

subquery+=   _query_with_args   # (q query ..args)
exists+=     _query_with_args   # (exists query ..args)
pull+=       _query_with_args   # (pull query ..args)
pull_many+=  _query_with_args   # (pull-many query ..args)
_query_with_args: Query _args?

Expr:           #note: no None/nil here
      int | float | decimal | str | bool
    | Param                     # $symbol
    | Var                       # symbol
    | Func
    | subquery
    | exists
    | pull
    | pull_many
    | Temporal | TemporalAmount,   #ObjectExpr ?? datetime / duration ??
    | VectorExpr
    | SetExpr    #is this needed?
    | MapExpr

Expr_or_None: Expr | None       #XXX where is this allowed?
Param: Name                     # $<name>
Var:   Name                     # <name>

Func: F_special | F_predicate | F_common | F_periods | F_aggregate
F_special: attrget | f_let | f_if | f_ifsome | f_cond | f_switch
#F_... all of them ...

Name: str

####################

implementation-wise:
 * join_left if a parameter over join, and pull_many is a parameter over pull ; funcs with sub-variants are done same way
 * inside unify, Name in Name_Expr in with_columns / unnest turns into column/symbol (but keyword if outside)
 * there are few other parametrized things
 * various shortcuts may be applied, i.e. yielding just list-of-bindnames instead of full form {:bind list-of-stuff } etc

'''

# vim:ts=4:sw=4:expandtab
