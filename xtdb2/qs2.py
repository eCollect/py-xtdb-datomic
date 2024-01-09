
'''
https://docs.xtdb.com/reference/main/xtql/queries.html
https://docs.xtdb.com/reference/main/stdlib.html
https://docs.xtdb.com/reference/main/stdlib/predicates.html
'''
from dataclasses import dataclass, InitVar, replace as dc_replace, KW_ONLY
from typing import Dict, List, Optional, Any, Union, TypeVar, ForwardRef as _ForwardRef, _eval_type    #ClassVar

_forwards = []
def Forward( x):
    'use this instead of ForwardRef/str'
    f = _ForwardRef( x)
    _forwards.append( f)
    return f

import datetime
Timestamp = Union[ datetime.date, datetime.datetime ] #.datetime either naive or timezoned

#tx_time === system_time

#class xtql:
    #class thing( dict):

def sym(x): return '%'+x
def kw(x):  return ':'+x
sym_wild = sym('*')

def s( x, name_as_sym =False):
    if isinstance( x, (list,tuple)):
        return [ s( i, name_as_sym= name_as_sym) for i in x ]
    m = getattr( x, 's', None)
    if m: return m( name_as_sym= name_as_sym)
    return x
def s_sym( name, *args):
    return (sym( name), *s( args))
def _init_items( me, name, type, items, allow_empty =False):
    if not allow_empty: assert items
    for i in items:
        assert isinstance( i, type), i
    setattr( me, name, items)
def _init_item( me, name, type, item, allow_empty =False):
    if not allow_empty:
        assert item is not None
    if item is not None:
        assert isinstance( item, type), item
    setattr( me, name, item)

class Source: 'op/source'
class Transform: 'op/tail'

Name = str      #column-name or var-name
class Column( str): pass
class Var( str):
    '-> symbol'
    def s( me, **kaignore): return sym( me)
class Param( str):
    '-> $symbol'
    def s( me, **kaignore): return sym( '$'+ me)

class Func: pass

class TemporalFilter:
    '''
    (at Timestamp)
    | (from Timestamp)
    | (to Timestamp)
    | (in Timestamp Timestamp)
    | :all-time
    '''
@dataclass
class _TemporalFilter1( TemporalFilter):
    timestamp: Timestamp
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
    def __init__( me, *args):
        _init_items( me, 'args', ArgSpec, args)
class subquery( _query): 'fn/q'
class exists( _query): 'fn/exists'
@dataclass
class pull( _query):
    'fn/pull* if many else fn/pull'
    many: bool =False
    def __init__( me, *args, many =False):
        me.many = many
        super().__init__( *args)


Expr = Union[ #None,    no None plz
            int, float, #decimal ?
            str, bool,
            #TODO Temporal, TemporalAmount,   #ObjectExpr ?? datetime / duration ??
            #TODO List[ Forward( 'Expr') ],             #VectorExpr
            #set[ Expr ] ?              #SetExpr
            #TODO Dict[ str, Forward( 'Expr') ],        #MapExpr -> {:str expr, ..}
            Param,                      #-> $symbol
            Var,                        #-> symbol
            #Forward( 'attrget'),
            #Forward( 'Predicate'),
            Func,
            subquery,
            exists,
            pull,
            ]
Expr_or_None = Union[ Expr, None ]

@dataclass
class attrget( Func):
    'fn/. i.e. getattr'
    expr: Expr
    attr: Name
    def s( me, **kaignore):
        return s_sym( '.', expr, sym( me.attr))

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
    'name is keyword=column-or-param if expr, else a symbol=somevar'
    name: Name
    expr: Expr =None
    def s( me, name_as_sym =False):
        if me.expr is None: return sym( me.name)
        name = (sym if name_as_sym else kw)( me.name)
        return { name: s( me.expr) }
    @classmethod
    def convert( me, items, ignore =None):
        return [ b if isinstance( b, me) or b == ignore else me( b) for b in items ]

BindSpec = Name_Expr

@dataclass #( frozen= True)
class fromtable( Source):
    table:  str  #identifier?
    binds:  List[ BindSpec ]
    whole:  InitVar =False
    for_valid_time: TemporalFilter =None
    for_tx_time:    TemporalFilter =None
    def __init__( me, table, *argsbinds, binds= (), whole =False, for_valid_time =None, for_tx_time =None):
        me.table = table
        _init_item( me, 'for_valid_time', TemporalFilter, for_valid_time, allow_empty= True)
        _init_item( me, 'for_tx_time',    TemporalFilter, for_tx_time,    allow_empty= True)
        assert not (binds and argsbinds)
        binds = list( binds or argsbinds)
        if not binds: whole = True
        if whole and sym_wild not in binds:
            binds.insert( 0, sym_wild)
        me.binds = BindSpec.convert( binds, ignore= sym_wild )
    def has_whole( me):
        return sym_wild in me.binds
    def s( me, **kaignore):
        if me.for_valid_time is None and me.for_tx_time is None:
            args = me.binds
        else:
            args = dict(
                bind = s( me.binds),
                **({} if me.for_valid_time is None else dict( for_valid_time= s( me.for_valid_time))),
                **({} if me.for_tx_time    is None else dict( for_tx_time   = s( me.for_tx_time))),
                )
        return s_sym( 'from', kw( me.table), args )


@dataclass #( frozen= True)
class relation( Source):
    'can come from constant, query-argument, value-in-another-doc (as Transform?)'
    expr: Expr
    binds: List[ BindSpec ]
    def __init__( me, expr, *argsbinds, binds= ()):
        _init_item( me, 'expr', Expr, expr)
        assert not (binds and argsbinds)
        me.binds = BindSpec.convert( binds or argsbinds)
    def s( me, **kaignore):
        return s_sym( 'rel', me.expr, me.binds )
rel = relation

ArgSpec = Name_Expr

@dataclass
class join:
    xtql = 'join'
    query:  Forward( 'Query')
    binds:  List[ BindSpec ]
    args:   List[ ArgSpec ] =()
    def __init__( me, query, *argsbinds, binds =(), args =()):
        _init_item( me, 'query', Query, query)
        assert not (binds and argsbinds)
        me.binds = BindSpec.convert( binds or argsbinds)
        me.args  = ArgSpec.convert( args)
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
    'op/where'
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
    'op/order-by'
    orders: List[ OrderSpec ]
    def __init__( me, *argsorders, orders =(), **kargsorders):
        orders = [ s if isinstance( s, OrderSpec) else OrderSpec( s)
                    for s in argsorders or orders ]
        kaorders = [ OrderSpec( k, **(v if isinstance( v, dict) else dict( desc= v )))
                    for k,v in kargsorders.items() ]
        _init_items( me, 'orders', OrderSpec, orders + kaorders)
    def s( me, **kaignore):
        return s_sym( 'order-by', *me.orders)

@dataclass
class limit( Transform):
    'op/limit'
    value: int #non-negative
    def s( me, **kaignore):
        return (sym( 'limit'), me.value)
@dataclass
class offset( Transform):
    'op/offset'
    value: int #non-negative
    def s( me, **kaignore):
        return (sym( 'offset'), me.value)


@dataclass
class unnest( Transform):
    'op/unnest - differs in pipeline:name=col vs unify/name=var/logicvar'
    name: Name
    expr: Expr
    def s( me, name_as_sym =False):
        name = (sym if name_as_sym else kw)( me.name)
        return (sym( 'unnest'), { name: s( me.expr) })


@dataclass
class without_columns( Transform):
    'op/without'
    columns: List[ Column ]
    def __init__( me, *columns):
        _init_items( me, 'columns', Column, columns)
    def s( me, **kaignore):
        return s_sym( 'without', *me.columns)

def _init_items2( me, name, type, items, kaitems):
    kaitems = [ type( k,v) for k,v in kaitems.items() ]
    items = type.convert( items)
    _init_items( me, name, type, items + kaitems)

ReturnSpec = Name_Expr
@dataclass
class exact_columns( Transform):
    'op/return - name=col if-expr-else =var'
    columns: List[ ReturnSpec ]
    def __init__( me, *columns, **kacolumns):
        _init_items2( me, 'columns', ReturnSpec, columns, kacolumns)
    def s( me, **kaignore):
        return s_sym( 'return', *me.columns)

WithSpec = Name_Expr
@dataclass
class with_columns( Transform):
    'op/with - differs in pipeline/name=col-if-expr vs unify/name=var-if-expr ; if no expr, name=var/withvar'
    columns: List[ WithSpec ]
    def __init__( me, *columns, **kacolumns):
        _init_items2( me, 'columns', WithSpec, columns, kacolumns)
    def s( me, name_as_sym =False):
        return (sym( 'with'), *s( me.columns, name_as_sym= name_as_sym))

AggrSpec = Name_Expr
@dataclass
class aggregate( Transform):
    'op/aggregate - name=col if-expr-else =var'
    items: List[ AggrSpec ]
    def __init__( me, *items, **kaitems):
        _init_items2( me, 'items', AggrSpec, items, kaitems)
    def s( me, **kaignore):
        return s_sym( 'aggregate', *me.items)
aggr = aggregate


UnifyClause = Union[ fromtable, relation, join, where, with_columns, unnest ]
@dataclass
class unify( Source):
    'note: cannot contain fromtable with whole/sym_wild'
    sources: List[ UnifyClause ]
    def __init__( me, *sources):
        _init_items( me, 'sources', UnifyClause, sources)
        for i in sources:
            if isinstance( i, fromtable):
                assert not i.has_whole(), i
    def s( me, **kaignore):
        return (sym( 'unify'), *s( me.sources, name_as_sym= True))

@dataclass
class pipeline:
    source: Source
    transforms: List[ Transform ] =()
    def __init__( me, source, *argstfs, transforms= ()):
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
class func( Func):
    'fn/<name> - func-call name over args'
    name: Name
    args: List[ Expr ]
    _argsize = 1,None   #min=1
    def __init__( me, name: Name, *args):
        _init_item( me, 'name', Name, name)
        amin,amax = me._argsize
        assert amin <= len( args ) <= (amax or 99)
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
                    allowed.update( v)
                elif isinstance( v, list):  #category-list
                    allowed.update( dict.fromkeys( v))
                else: allowed[ k] = v       #direct-dict
        elif isinstance( klas._allowed, list):  #direct-list
            allowed.update( dict.fromkeys( klas._allowed))
        klas._allowed_flat = allowed
        return allowed

    def make_name( me):
        return me.get_allowed().get( me.name) or me.name
    def s( me, **kaignore):
        return s_sym( me.make_name(), *me.args)

    class Registry:
        def __init__( me):
            registry = {}
            for fc in func.__subclasses__():
                registry.update( dict.fromkeys( fc.get_allowed(), fc) )
            me.all = registry
        def __getattr__( me, k):
            return lambda *a,**ka: me.all[ k ]( k, *a,**ka)

class func_any( func):
    _allowed = dict(
        _arithmetic = dict( add= '+', sub= '-', mul= '*', div= '/'),
        _other      = 'coalesce'.split(),
        )
class func1( func):
    _argsize = 1,1      #==1
    _allowed = dict(
        _numeric = 'abs ceil floor double exp ln log10 sqrt'.split(),
        _trigo   = 'sin cos tan  asin acos atan  sinh cosh tanh'.split(),
        _text    = dict( len= 'character-length', bytelen= 'octet-length', lower= None, upper= None, ), #TODO more octet-things
        )
class func2( func):
    _argsize = 2,2      #==2
    _allowed = dict(
        _numeric = 'log mod power'.split(),
        _text    = 'like position trim trim_start trim_end'.split(),
        _other   = dict( null_if_eq= 'null-if'),
        _time    = dict( period= None, datetime_truncate= 'date-trunc', datetime_extract= 'extract'),
        )
class func3( func):
    _argsize = 3,3      #==3
    _allowed = dict(
        _logic   = 'if let'.split(),    #XXX f_let/f_if ??
        )
class func23( func):
    _argsize = 2,3
    _allowed = dict(
        _text    = dict( regex= 'like-regex', substr= 'substring'),
        )

class func_now( func):
    _argsize = 0,0
    def __init__( me, *a, precision: str =None):
        me.precision = precision
        super().__init__( *a)
    def s( me, **kaignore):
        return s_sym( me.make_name(), *( [ me.precision ] if me.precision else ()))
    _allowed = dict( utc_datetime= 'current-timestamp', utc_date= 'current-date', utc_time= 'current-time',
                      local_datetime='local-timestamp', local_time= 'local-time')
class func_periods( func):
    _argsize = 2,2      #==2
    _allowed = 'equals overlaps '.split()
class func_periods1( func_periods):
    def __init__( me, *a, strictly: bool =False):
        me.strictly = strictly
        super().__init__( *a)
    def make_name( me):
        return ('strictly-' if me.strictly else '') + super().make_name()
    _allowed = 'contains '.split()
class func_periods2( func_periods1):
    def __init__( me, *a, strictly: bool =False, immediately: bool =False ):
        assert not (strictly and immediately) #XXX: either immediately OR strictly, not both
        me.immediately = immediately
        super().__init__( *a, strictly= strictly)
    def make_name( me):
        return ('immediately-' if me.immediately else '') + super().make_name()
    _allowed = 'lags leads precedes succeeds'.split()

class func_aggr0( func):
    _argsize = 0,0      #==0
    _allowed = dict( row_count= 'row-count')
class func_aggr1( func):
    _argsize = 1,1      #==1
    _allowed = dict(
       _nums = dict( stddev_population= 'stddev-pop', stddev_sample= 'stddev-samp', variance_population= 'var-pop', variance_sample= 'var-samp'),
       _bools= 'all every any some'.split(),
       _comp = dict( array_aggr= 'array-agg'),
       )
class func_aggr2( func):
    _argsize = 1,1      #==1
    def __init__( me, *a, distinct: bool =False):
        me.distinct = distinct
        super().__init__( *a)
    def make_name( me):
        return super().make_name() + ('-distinct' if me.distinct else '')
    _allowed = dict(
        _nums = 'avg count max min sum'.split()     #XXX overlap max/min
        )

@dataclass
class f_let( Func):
    'fn/let - eval .body(expr) for .name bound to .bind(expr)'
    name: Name  #-> bind-symbol
    bind: Expr  #-> bind-expr
    body: Expr  #-> body-expr
    def s( me, **kaignore):
        return s_sym( 'let', [ me.name, me.bind ], me.body )

@dataclass
class f_if( Func):
    'fn/if'
    cond: Expr  #-> predicate ? must return boolean
    then: Expr
    orelse: Expr
    def s( me, **kaignore):
        return s_sym( 'if', cond, me.then, me.orelse )

@dataclass
class f_ifsome( Func):
    'fn/if-some - eval .then(expr) for name bound to .bind(expr) if it is non-null, else .orelse(expr)'
    name: Name  #-> bind-symbol
    bind: Expr  #-> bind-expr
    then: Expr  #-> then-expr
    orelse: Expr#-> else-expr
    def s( me, **kaignore):
        return s_sym( 'if-some', [ me.name, me.bind ], me.then, me.orelse )


@dataclass
class case:
    value: Expr     #=predicate inside cond
    result: Expr

import itertools
@dataclass
class f_cond( Func):
    'fn/cond'
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
                *( [ me.default ] if me.default is not None else ()))

@dataclass
class f_switch( Func):
    'fn/case'
    test: Expr
    cases: List[ case ]
    default: Expr =None
    def __init__( me, test: Expr, *cases, default: Expr =None):
        _init_item( me, 'test', Expr, test)
        f_cond.__init__( me, default= default, *cases)
    def s( me, **kaignore):
        return s_sym( 'case', me.test, *f_cond._scases( me))

funcs_registry = func.Registry()
funcs = fn = funcs_registry
for f in Func.__subclasses__():
    if f is Func or f is func: continue
    setattr( funcs_registry, f.__name__[2:], f)


if __name__ == '__main__':
    if 0*'dbg':
        import typing
        typing.issubclass = lambda *a: [print('isc',*a),issubclass(*a)][-1]

    if 10:
      for f in _forwards:
        print(f)
        f._evaluate( globals(), globals(), frozenset() )
    else:
        _eval_type( Expr, globals(), globals())
    if 0:
        def fw__subclasscheck__(me, cls):
            if 'dbg': print( 'fw', cls)
            return issubclass( cls, me.__forward_value__ if me.__forward_evaluated__ else _ForwardRef)
        _ForwardRef.__subclasscheck__ = fw__subclasscheck__

    def prn(e):
        print( e, '\n', s(e))

    p = fromtable( 'tbl', 'a', 'b')
    prn( p)
    p = fromtable( 'tbl', 'a', whole=True,
            for_valid_time = all_time, for_tx_time= at( 'noww'))
    prn( p)
    q = dc_replace( p, binds= ['b','c'])
    prn(q)
    u = unify( q, leftjoin( q, 'x') )
    prn(u)
    prn( leftjoin( q, 'x') )

    func1( 'sinh', 4.5 )

    u2= unify(
        fromtable( 'docs', 'my-nested-rel' ),
        relation( 'my-nested-rel', 'a', 'b'),
        where( p_gt( 'a', 'b'), p_min( 'a', 'b') ),
        with_columns( 'a', x= 'b'),
        )
    prn(u2)

    c = f_switch( p_gt( 'a', 2), case( 3, 45), case( 7, 0) , default= -34)
    prn(c)
    prn( case(3,4))
    d = f_cond( case( 3, 45), case( funcs.add(7,8), 0) , default= -34)
    prn(d)
    o = orderby( 'a', OrderSpec( 'c', desc=1), b=True, d=dict(desc=True, nulls_last=True) )
    prn( o)
    f = fn.row_count()
    prn( f)
    prn( funcs.add(3,4))
    prn( funcs.let('a','b','c'))
#    prn( funcs.max('a','b','c'))


#TODO:
# - see Expr TODOs
# - common register of all funcs
# - convert( bindspec ? )
    import dataclasses
    import pprint
    pprint.pprint( dataclasses.fields( f_switch))

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
                                    # (from table { :bind: ..binds , :for_valid_time .., :for_tx_time .. })
_table_name: Name
_table_binds: _table_bind+
_table_bind: Name_Expr | wildcard
_table_options: for_valid_time? for_tx_time?
for_valid_time+= TemporalFilter
for_tx_time+= TemporalFilter
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
