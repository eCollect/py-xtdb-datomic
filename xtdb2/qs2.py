
'''
https://docs.xtdb.com/reference/main/xtql/queries.html
https://docs.xtdb.com/reference/main/stdlib.html
https://docs.xtdb.com/reference/main/stdlib/predicates.html
'''
from dataclasses import dataclass, InitVar, replace as dc_replace
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


sym_wild = 'sym*'

if 0:
  def _fromtable( table, *bindspecs, whole =False, for_valid_time =None, for_tx_time =None):
    #like qs1,pull
    if not bindspecs: whole = True
    if whole and sym_wild not in bindspecs:
        bindspecs = [ sym_wild, *bindspecs]
    return dict( table= table, bindspecs =bindspecs, for_valid_time =for_valid_time, for_tx_time= for_tx_time)

class Source: 'op/source'
class Transform: 'op/tail'

class Name( str): pass      #column-name or var-name
class Column( str): pass
class Var( str):    '-> symbol'
class Param( str):  '-> $symbol'

class Func: pass
@dataclass
class getattr:
    'fn/.'
    expr: 'Expr'
    what: Name

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

Expr = Union[ int, float, #decimal ?
            str, bool, None,
            #Temporal, TemporalAmount,   #ObjectExpr ?? datetime / duration ??
            list[ 'Expr' ],             #VectorExpr
            #set[ Expr ] ?              #SetExpr
            Dict[ str, 'Expr' ],        #MapExpr -> {:str expr, ..}
            Param,                      #-> $symbol
            Var,                        #-> symbol
            getattr,
            Func,
            subquery,
            exists,
            pull,
            ]

@dataclass
class _items:
    items: list[ Expr ]
@dataclass
class _item:
    expr: Expr

Predicate = Union[ _items, _item ]

@dataclass
class _name_maybe_expr:
    'name is keyword=column-or-param if expr, else a symbol=somevar'
    name: Name
    expr: Expr =None


BindSpec = _name_maybe_expr

@dataclass #( frozen= True)
class fromtable( Source):
    table:      str  #identifier
    bindspecs:  list[ BindSpec ]
    whole:      InitVar =False
    for_valid_time: TemporalFilter =None
    for_tx_time:    TemporalFilter =None
    def __post_init__( me, whole):
        if not me.bindspecs: whole = True
        if whole and sym_wild not in me.bindspecs:
            me.bindspecs = [ sym_wild, *me.bindspecs]


@dataclass #( frozen= True)
class relation( Source, Transform):
    'can come from constant, query-argument, value-in-another-doc (as Transform?)'
    expr: Expr
    bindspecs: list[ BindSpec ]
rel = relation

ArgSpec  = _name_maybe_expr

@dataclass
class join:
    query:      Any
    bindspecs:  list[ BindSpec ]
    args:       list[ ArgSpec ] =()
class leftjoin( join): pass


@dataclass
class where( Transform):
    'op/where'
    predicates: list[ Predicate ]

@dataclass
class _orderspec:
    '''expr     -> val= expr
     desc       -> dir= :desc or :asc
     nulls_last -> nulls= :last or :first
    '''
    expr: Expr
    desc:       bool =False
    nulls_last: bool =False

OrderSpec = Union[ Column, _orderspec ]
@dataclass
class orderby( Transform):
    'op/order-by'
    specs: list[ OrderSpec ]

@dataclass
class limit( Transform):
    'op/limit'
    value: int #non-negative
@dataclass
class offset( Transform):
    'op/offset'
    value: int #non-negative


@dataclass
class unnest( Transform):
    'op/unnest - differs in pipeline:name=col vs unify/name=var/logicvar'
    name: Name
    expr: Expr


@dataclass
class without_columns( Transform):
    'op/without'
    columns: list[ Column ]

ReturnSpec = _name_maybe_expr
@dataclass
class exact_columns( Transform):
    'op/return - name=col if-expr-else =var'
    columns: list[ ReturnSpec ]

WithSpec = _name_maybe_expr
@dataclass
class with_columns( Transform):
    'op/with - differs in pipeline/name=col-if-expr vs unify/name=var-if-expr ; if no expr, name=var/withvar'
    columns: list[ WithSpec ]

AggrSpec = _name_maybe_expr
@dataclass
class aggregate( Transform):
    'op/aggregate - name=col if-expr-else =var'
    items: list[ AggrSpec ]
aggr = aggregate


UnifyClause = Union[ fromtable, relation, join, where, with_columns ]
@dataclass
class unify( Source):
    'note: cannot contain fromtable with whole/sym_wild'
    sources: list[ UnifyClause ]

@dataclass
class pipeline:
    source: Source
    transforms: list[ Transform ] =()

Query = Union[ Source, pipeline ]

##############

class Comparator: pass
class p_lt( _items, Comparator): 'op/<'
class p_le( _items, Comparator): 'op/<='
class p_gt( _items, Comparator): 'op/>'
class p_ge( _items, Comparator): 'op/>='
class p_eq( _items, Comparator): 'op/='
class p_ne( _items, Comparator): 'op/<>'

class p_max( _items): 'op/greatest'
class p_min( _items): 'op/least'
p_greatest = p_max
p_least = p_min
class p_all( _items): 'op/and'
class p_any( _items): 'op/or'
p_and = p_all
p_or  = p_any
class p_not(    _item): 'op/not'
class p_true(   _item): 'op/true?'
class p_false(  _item): 'op/false?'
class p_null(   _item): 'op/nil?'

###############

class func( Func):
    'fn/<name> - func-call name over args'
    _argsize = 1,None   #min=1
    def __init__( me, name: Name, *args):
    #name: Name
    #args: list[ 'Expr' ]
    #def __post_init__( me):
        me.name = name
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
        assert me.name in allowed, me.name
        assert all( isinstance( x, Expr) for x in args )
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
    def __init__( me, *a, precision: str =None):
        me.precision = precision
        super().__init__( *a)
    _allowed = dict( utc_datetime= 'current-timestamp', utc_date= 'current-date', utc_time= 'current-time',
                      local_datetime='local-timestamp', local_time= 'local-time')
class func_periods( func):
    _argsize = 2,2      #==2
    _allowed = 'equals overlaps '.split()
class func_periods1( func_periods):
    def __init__( me, *a, strictly: bool =False):
        me.strictly = strictly
        super().__init__( *a)
    _allowed = 'contains '.split()
class func_periods2( func_periods1):
    def __init__( me, *a, strictly: bool =False, immediately: bool =False ):
        assert not (strictly and immediately) #XXX: either immediately OR strictly, not both
        me.immediately = immediately
        super().__init__( *a, strictly= strictly)
    _allowed = 'lags leads precedes succeeds'.split()

class f_row_count( Func):
    'fn/row-count'
class func_aggr1( func):
    _argsize = 1,1      #==1
    _nums = dict( stddev_population= 'stddev-pop', stddev_sample= 'stddev-samp', variance_population= 'var-pop', variance_sample= 'var-samp')

class func_aggr2( func):
    _argsize = 1,1      #==1
    def __init__( me, *a, distinct: bool =False):
        me.distinct = distinct
        super().__init__( *a)
    _nums = 'avg count max min sum'.split()

@dataclass
class f_let( Func):
    'fn/let - eval .body(expr) for .name bound to .bind(expr)'
    name: Name  #-> bind-symbol
    bind: Expr  #-> bind-expr
    body: Expr  #-> body-expr
@dataclass
class f_if( Func):
    'fn/if'
    cond: Expr  #-> predicate ? must return boolean
    then: Expr
    orelse: Expr
@dataclass
class f_ifsome( Func):
    'fn/if-some - eval .then(expr) for name bound to .bind(expr) if it is non-null, else .orelse(expr)'
    name: Name  #-> bind-symbol
    bind: Expr  #-> bind-expr
    then: Expr  #-> then-expr
    orelse: Expr#-> else-expr

@dataclass
class _case:
    value: Expr     #=predicate inside cond
    result: Expr
@dataclass
class cond( Func):
    cases: list[ _case ]
    default: Expr =None
@dataclass
class case( Func):
    test: Expr
    cases: list[ _case ]
    default: Expr =None





if __name__ == '__main__':
    p = fromtable( 'tbl', 'a', whole=True,
        for_valid_time = all_time, for_tx_time= at( 'noww'))
    print(p)
    q = dc_replace( p, bindspecs= ['b','c'])
    print(q)
    u = unify( [ p, leftjoin( 'qqq', ['x']) ])
    print(u)

    func1( 'sinh', 4.5 )


# vim:ts=4:sw=4:expandtab
