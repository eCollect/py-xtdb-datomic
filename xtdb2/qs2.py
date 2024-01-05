
'''
https://docs.xtdb.com/reference/main/xtql/queries.html
https://docs.xtdb.com/reference/main/stdlib.html
https://docs.xtdb.com/reference/main/stdlib/predicates.html
'''
from dataclasses import dataclass, InitVar, replace as dc_replace, KW_ONLY
from typing import Dict, List, Optional, Any, Union, TypeVar    #ClassVar

import datetime
Timestamp = Union[ datetime.date, datetime.datetime ] #.datetime either naive or timezoned

#tx_time === system_time

if 1:
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
    class at( _TemporalFilter1): pass
    class since( _TemporalFilter1): pass
    class until( _TemporalFilter1): pass
    @dataclass
    class between( TemporalFilter):
        since: Timestamp
        until: Timestamp
    @dataclass
    class all_time( TemporalFilter): pass
    all_time = all_time()


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
def _init_items( me, name, type, items, allow_empty =False):
    if not allow_empty: assert items
    for i in items:
        assert isinstance( i, type), i
    setattr( me, name, items)


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

@dataclass
class attrget:
    'fn/. i.e. getattr'
    expr: 'Expr'
    attr: Name
    def s( me, **kaignore):
        return (sym( '.'), s(expr), sym( me.attr))

@dataclass
class _query:
    query: 'Query'
    args: list[ 'ArgSpec' ] =()
class subquery( _query): 'fn/q'
class exists( _query): 'fn/exists'
@dataclass
class pull( _query):
    'fn/pull* if many else fn/pull'
    many: bool =False

@dataclass
class _items:
    items: list[ 'Expr' ]
    def __init__( me, *items):
        _init_items( me, 'items', Expr, items)
    def s( me, **kaignore):
        return (sym( me.xtql), *s( me.items))
@dataclass
class _item:
    expr: 'Expr'
    def __init__( me, expr):
        assert isinstance( expr, Expr), expr
        me.expr = expr
    def s( me, **kaignore):
        return (sym( me.xtql), s( me.expr))

Predicate = Union[ _items, _item ]

Expr = Union[ int, float, #decimal ?
            str, bool, None,
            #Temporal, TemporalAmount,   #ObjectExpr ?? datetime / duration ??
            list[ 'Expr' ],             #VectorExpr
            #set[ Expr ] ?              #SetExpr
            Dict[ str, 'Expr' ],        #MapExpr -> {:str expr, ..}
            Param,                      #-> $symbol
            Var,                        #-> symbol
            attrget,
            Predicate,
            Func,
            subquery,
            exists,
            pull,
            ]



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
    binds:  list[ BindSpec ]
    whole:  InitVar =False
    for_valid_time: TemporalFilter =None
    for_tx_time:    TemporalFilter =None
    def __init__( me, table, *argsbinds, binds= (), whole =False, for_valid_time =None, for_tx_time =None):
        me.table = table
        me.for_valid_time = for_valid_time
        me.for_tx_time = for_tx_time
        assert not (binds and argsbinds)
        binds = list( binds or argsbinds)
        if not binds: whole = True
        if whole and sym_wild not in binds:
            binds.insert( 0, sym_wild)
        me.binds = BindSpec.convert( binds, ignore= sym_wild )
    def has_whole( me):
       return sym_wild in me.binds
    def s( me, **kaignore):
        return (sym( 'from'), kw( me.table), s( me.binds ) )


@dataclass #( frozen= True)
class relation( Source, Transform):
    'can come from constant, query-argument, value-in-another-doc (as Transform?)'
    expr: Expr
    binds: list[ BindSpec ]
    def __init__( me, expr, *argsbinds, binds= ()):
        me.expr = expr
        assert not (binds and argsbinds)
        me.binds = BindSpec.convert( binds or argsbinds)
    def s( me, **kaignore):
        return (sym( 'rel'), me.expr, s( me.binds ) )
rel = relation

ArgSpec = Name_Expr

@dataclass
class join:
    query:  'Query'
    binds:  list[ BindSpec ]
    args:   list[ ArgSpec ] =()
    def __init__( me, query, *argsbinds, binds =(), args =()):
        assert isinstance( query, Query), query
        me.query = query
        assert not (binds and argsbinds)
        me.binds = BindSpec.convert( binds or argsbinds)
        me.args  = ArgSpec.convert( args)
    def s( me, **kaignore):
        return (sym( getattr( me.__class__, 'xtql', me.__class__.__name__)),
                s( me.query),
                s( me.binds ) if not me.args else
                    dict( bind= s( me.binds ), args= s( me.args))
                )
class leftjoin( join):
    xtql = 'left-join'


@dataclass
class where( Transform):
    'op/where'
    predicates: list[ Predicate ]
    def __init__( me, *predicates):
        _init_items( me, 'predicates', Predicate, predicates)
    def s( me, **kaignore):
        return (sym( 'where'), *s( me.predicates))

@dataclass
class _orderspec:
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
            return s( me.expr)
        return dict(
            val= s( me.expr),
            **({} if me.desc is None else dict( dir= kw( 'desc' if me.desc else 'asc'))),
            **({} if me.nulls_last is None else dict( nulls = kw( 'last' if me.nulls_last else 'first'))),
            )

OrderSpec = Union[ Column, _orderspec ]
@dataclass
class orderby( Transform):
    'op/order-by'
    specs: list[ OrderSpec ]
    def __init__( me, *specs):
        _init_items( me, 'specs', OrderSpec, specs)
    def s( me, **kaignore):
        return (sym( 'order-by'), *s( me.specs))

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
    columns: list[ Column ]
    def __init__( me, *columns):
        _init_items( me, 'columns', Column, columns)
    def s( me, **kaignore):
        return (sym( 'without'), *s( me.columns))

def _init_items2( me, name, type, items, kaitems):
    kaitems = [ type( k,v) for k,v in kaitems.items() ]
    items = type.convert( items)
    _init_items( me, name, type, items + kaitems)

ReturnSpec = Name_Expr
@dataclass
class exact_columns( Transform):
    'op/return - name=col if-expr-else =var'
    columns: list[ ReturnSpec ]
    def __init__( me, *columns, **kacolumns):
        _init_items2( me, 'columns', ReturnSpec, columns, kacolumns)
    def s( me, **kaignore):
        return (sym( 'return'), *s( me.columns))

WithSpec = Name_Expr
@dataclass
class with_columns( Transform):
    'op/with - differs in pipeline/name=col-if-expr vs unify/name=var-if-expr ; if no expr, name=var/withvar'
    columns: list[ WithSpec ]
    def __init__( me, *columns, **kacolumns):
        _init_items2( me, 'columns', WithSpec, columns, kacolumns)
    def s( me, name_as_sym =False):
        return (sym( 'with'), *s( me.columns, name_as_sym= name_as_sym))

AggrSpec = Name_Expr
@dataclass
class aggregate( Transform):
    'op/aggregate - name=col if-expr-else =var'
    items: list[ AggrSpec ]
    def __init__( me, *items, **kaitems):
        _init_items2( me, 'items', AggrSpec, items, kaitems)
    def s( me, **kaignore):
        return (sym( 'aggregate'), *s( me.items))
aggr = aggregate


UnifyClause = Union[ fromtable, relation, join, where, with_columns ]
@dataclass
class unify( Source):
    'note: cannot contain fromtable with whole/sym_wild'
    sources: list[ UnifyClause ]
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
    transforms: list[ Transform ] =()
    def __init__( me, source, *argstfs, transforms= ()):
        assert not (transforms and argstfs)
        _init_items( me, 'transforms', Transform, transforms or argstfs, allow_empty =True)
    def s( me, **kaignore):
        return (sym( '->'), s( me.source), *s( me.transforms))

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

class func( Func):
    'fn/<name> - func-call name over args'
    _argsize = 1,None   #min=1
    def __init__( me, name: Name, *args):
        me.name = name
        assert isinstance( name, Name), name
        me.args = args
        amin,amax = me._argsize
        assert amin <= len( me.args ) <= (amax or 99)
        allowed = {}
        if isinstance( me._allowed, dict):
            for k,v in me._allowed.items():
                if isinstance( v, dict):    #category-dict
                    allowed.update( v)
                elif isinstance( v, list):  #category-list
                    allowed.update( dict.fromkeys( v))
                else: allowed[ k] = v       #direct-dict
        elif isinstance( me._allowed, list):  #direct-list
            allowed.update( dict.fromkeys( me._allowed))
        assert name in allowed, name
        assert all( isinstance( x, Expr) for x in args ), args
    def make_name( me): return me.name
    def s( me, **kaignore):
        return (sym( me.make_name()), *s( me.args))

class func_any( func):
    _allowed = dict(
        _arithmetic = dict( add='+', sub='-', mul='*', div='/'),
        _other      = 'coalesce'.split(),
        )
class func1( func):
    _argsize = 1,1      #==1
    _allowed = dict(
        _numeric = 'abs ceil floor double exp ln log10 sqrt'.split(),
        _trigo   = 'sin cos tan  asin acos atan  sinh cosh tanh'.split(),
        _text    = dict( len= 'character-length', bytelen= 'octet-length', lower= None, upper= None, ),
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
        _logic   = 'if let'.split(),
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
        return (sym( me.make_name()), *( [ s( me.precision )] if me.precision else ()))
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
        return ('strictly-' if me.strictly else '') + me.name
    _allowed = 'contains '.split()
class func_periods2( func_periods1):
    def __init__( me, *a, strictly: bool =False, immediately: bool =False ):
        assert not (strictly and immediately) #XXX: either immediately OR strictly, not both
        me.immediately = immediately
        super().__init__( *a, strictly= strictly)
    def make_name( me):
        return ('immediately-' if me.immediately else '') + super().make_name()
    _allowed = 'lags leads precedes succeeds'.split()

class f_row_count( Func):
    'fn/row-count'
    def s( me, **kaignore):
        return (sym( 'row-count'),)
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
        return me.name + ('-distinct' if me.distinct else '')
    _allowed = dict(
        _nums = 'avg count max min sum'.split()
        )

@dataclass
class f_let( Func):
    'fn/let - eval .body(expr) for .name bound to .bind(expr)'
    name: Name  #-> bind-symbol
    bind: Expr  #-> bind-expr
    body: Expr  #-> body-expr
    def s( me, **kaignore):
        return (sym( 'let'), [ s( me.name), s( me.bind) ], s( me.body) )
@dataclass
class f_if( Func):
    'fn/if'
    cond: Expr  #-> predicate ? must return boolean
    then: Expr
    orelse: Expr
    def s( me, **kaignore):
        return (sym( 'if'), s( cond), s( me.then), s( me.orelse) )
@dataclass
class f_ifsome( Func):
    'fn/if-some - eval .then(expr) for name bound to .bind(expr) if it is non-null, else .orelse(expr)'
    name: Name  #-> bind-symbol
    bind: Expr  #-> bind-expr
    then: Expr  #-> then-expr
    orelse: Expr#-> else-expr
    def s( me, **kaignore):
        return (sym( 'if-some'), [ s( me.name), s( me.bind) ], s( me.then), s( me.orelse) )

@dataclass
class case:
    value: Expr     #=predicate inside cond
    result: Expr
    def s( me, **kaignore):
        return (s( me.value), s( me.result))

import itertools
@dataclass
class cond( Func):
    cases: list[ case ]
    default: Expr =None
    def s( me, **kaignore):
        return (sym( 'cond'), *me._scases())
    def _scases( me):
        return (
                *itertools.chain( *( c.s() for c in me.cases)),
                *( [ s( me.default) ] if me.default is not None else ()))
@dataclass
class switch( Func):
    'f/case'
    test: Expr
    cases: list[ case ]
    default: Expr =None
    def s( me, **kaignore):
        return (sym( 'case'), s( me.test), *cond._scases( me))





if __name__ == '__main__':
    p = fromtable( 'tbl', 'a', whole=True,
        for_valid_time = all_time, for_tx_time= at( 'noww'))
    print(p)
    q = dc_replace( p, binds= ['b','c'])
    print(q)
    u = unify( q, leftjoin( q, 'x') )
    print(u)
    print( s( leftjoin( q, 'x') ))

    func1( 'sinh', 4.5 )

    u2= unify(
        fromtable( 'docs', 'my-nested-rel' ),
        relation( 'my-nested-rel', 'a', 'b'),
        where( p_gt( 'a', 'b'), p_min( 'a', 'b') ),
        with_columns( 'a', x= 'b'),
        )
    print(u2)

    print(s(q))
    print(s(u))
    print(s(u2))

    c = switch( p_gt( 'a', 2), [ case( 3, 45), case( 7, 0) ], -34)
    print(c)
    print(s(c))

#TODO:
# - common register of all funcs
# - convert( bindspec ? )

# vim:ts=4:sw=4:expandtab
