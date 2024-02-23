import edn_format
Keyword = edn_format.Keyword
Symbol  = edn_format.Symbol
edn_dumps = edn_format.dumps
from edn_format import edn_dump as d    #see edn_dump.udump
Literals = (bool, str, bytes,
        edn_format.Char, #edn_format.TaggedElement, ???
        int, float, d.decimal.Decimal, d.fractions.Fraction,
        d.datetime.datetime, d.datetime.date,
        d.uuid.UUID
        )

'''
https://github.com/edn-format/edn
WTF...
 comma , is considered whitespace
 semicolon ; starts a line-comment
 symbols begin with non-numeric and can contain alphanumeric and also:
    . * + ! - _ ? $ % & = < >
    If some of - + . is the first character, the second (if any) must be non-numeric;
    Also : # are allowed as non-first characters.
    Also There can be only one / delimiting prefix from name
 keywords start with : and all else like symbols
 1 != 1.0  ???
 -.1 is not a number but a symbol.. -0.1 is a number
 Strings are in "double quotes". May span multiple lines. Standard C/Java escape characters \t, \r, \n, \\ and \" are supported.
'''

#########
#XXX BEWARE XXX do not start db-attribute-names with _
# Leading underscores are used for reverse lookup in pull.
# If attribute has a leading underscore then cannot do reverse lookup with that attribute.
# both for datomic and xtdb
#   https://docs.datomic.com/on-prem/schema/schema.html
#   https://docs.xtdb.com/language-reference/datalog-queries/#pull
#########

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
def check_sym_name_level( x):
    'single level, exclude /, cannot start with :#digit, ..'
    qs_assert_naming_non_empty_str( x )
    qs_assert_naming( x[0] not in ':#0123456789', 'name-or-prefix cannot start with ":" or "#" or digit', x)
    if x[0] in '-+.':
        qs_assert_naming( len(x) == 1 or not x[1].isdigit(), 'name-or-prefix cannot have digit after starting "." or "-" or "+"', x)
    qs_assert_naming( all( (c.isalnum() or c in _nonalnum) for c in x), 'name-or-prefix allows alphanumerics and '+repr(_nonalnum), x)

class edn_factory1:
    ''' factory for item of edntype   (without explicit namespace)
    example: given kw = edn_factory1( Keyword)
        all these: kw.a  kw('a')
        produce Keyword( a) i.e. :a
        further level e.g. kw.a.b or kw.a('b') is not allowed.
        As funccall, name may contain one / , and whatever else allowed)
        so kw('a/b') IS allowed ; kw('a/b/c') IS NOT allowed ; kw('=>>-?a.b.d/c.e') IS allowed
    '''
    check_name_level = staticmethod( check_sym_name_level)         #XXX eventualy override with something less-permissive..
    def __init__( me, ednfunc, pfx =''):
        me.ednfunc = ednfunc
        me.pfx = pfx
        assert isinstance( pfx, str), pfx
    def __call__( me, k):
        qs_assert_naming_non_empty_str( k )
        name = me.pfx + k
        qs_assert_naming( name.count('/') <= 1, 'only one / allowed', name)
        if me.ednfunc != Symbol or name != '/':     #special case: / alone is ok
            for p in name.split('/'): me.check_name_level( p)
        return me.ednfunc( name)
    __getattr__ = __call__

class edn_factory2:
    ''' factory for item of edn_type WITH namespace - 2 level
    example: given kw2 = edn_factory2( Keyword)
        all these: kw2.a.b  kw2( 'a', 'b')  kw2.a('b')  kw2('a').b  kw2('a','b')
        produce Keyword( a/b) i.e. :a/b
        the intermediate half kw2.a is not an edn_type ;
        level-names cannot contain / , i.e. kw2('a/b') IS NOT allowed
    '''
    check_name_level = staticmethod( check_sym_name_level)         #XXX eventualy override with something less-permissive..
    __init__ = edn_factory1.__init__
    def __call__( me, k, k2 =None):
        qs_assert_naming_non_empty_str( k )
        name = me.pfx + k
        me.check_name_level( name)
        if not k2:
            return me._edn2_half( me.ednfunc, name)   #intermediate
        me.check_name_level( k2)
        return me.ednfunc( name + '/' + k2)
    __getattr__ = __call__

    class _edn2_half:
        'factory for 2nd level of edn_factory2 item of edn_type with namespace'
        _translator = {}
        def __init__( me, ednfunc, level1):
            me.ednfunc = ednfunc
            me.level1 = level1
            edn_factory2.check_name_level( level1)
        def __call__( me, level2):
            qs_assert_naming_non_empty_str( level2 )
            level2 = me._translator.get( level2, level2)
            edn_factory2.check_name_level( level2)
            return me.ednfunc( me.level1 + '/' + level2)
        __getattr__ = __call__

#single :   kw.name or kw2('?name') ..
kw  = edn_factory1( Keyword)
sym = edn_factory1( Symbol)
#prefix/name :   kw2.pfx.name or kw2('?pfx','nm') or kw2('?pfx').nm ..
kw2 = edn_factory2( Keyword)
sym2= edn_factory2( Symbol)

#datomic insists on vars having ?, xtdb does not care
var = edn_factory1( Symbol, pfx= '?')
var2= edn_factory2( Symbol, pfx= '?')

#https://docs.xtdb.com/language-reference/datalog-queries/
#https://github.com/edn-format/edn

# lists: (1 2 3)
# vectors: [1 2 3]  ..supports random access
# ...sequences (lists and vectors) are equal to other sequences of same count of elements and with equal respective elements
# XXX hence seems completely interchangeable - except see orderby

#expr = tuple
vector = list
sequences = list,tuple

def is_literal(x):
    if isinstance( x, (set,frozenset)):
        return all( is_literal(a) for a in x)   #is it really recursive?
    return x is None or isinstance( x, Literals)

def is_keyword( x):
    return isinstance( x, Keyword)
def is_symbol( x):
    return isinstance( x, Symbol)
is_variable = is_symbol
def is_variable_datomic( x):
    return is_symbol(x) and x._name[0] == '?'
def is_sequence( x):
    return isinstance( x, sequences)
def is_clause( *args):
    return args and all( is_sequence( a) and a
        for a in args)   ##and 2 <= len(a) <= 3
def is_variable_or_clause( x):
    return is_variable( x) or is_clause( x)
def is_vector( x):
    return isinstance( x, vector)

#XXX quoting - seems needed inside Clojure only
# https://docs.xtdb.com/language-reference/datalog-queries/#_quoting

#############
# date/timestamps i.e. #inst "isoformat.here"
# use datetime.date or datetime.datetime with tzinfo=, e.g. datetime.timezone.utc

#datom = 5-tuple [entity attribute value transaction added?]

##clauses

def clause( *args): return vector( args )
def triple_clause( var, attr, *value): # =None):    #not just value=None, to allow for passing explicit None
    'make an entity_attr_value/triple_clause, see qbase.where'
    qs_assert( is_variable( var) or is_literal( var), 'pos0: needs variable or literal', var)
    qs_assert( is_keyword( attr), 'pos1: needs keyword', attr)
    if value:
        qs_assert( len( value) == 1, 'only one value allowed', value)
    return clause( var, attr, *value )
triple = var_attr_value = eav = entity_attr_value = triple_clause

# Predicate clauses must be placed in a clause, i.e. with a surrounding vector.
#def _predicate( func, val): return ( func, val )
def predicate( func, arg, *args): return [( func, arg, *args )]

#TODO - transform-funcs???

#comparisons..
from functools import partial
def _ops_declare( klas, ops_translator, func):
    for op, symbol in ops_translator.items():
        setattr( klas, op, partial( func, symbol))

from base.utils import dictAttr

_cmp = dictAttr(
    gt = sym( '>'),
    lt = sym( '<'),
    ge = sym( '>='),
    le = sym( '<='),
    eq = sym( '='),
#    ne = sym( 'not='), #no such thing??
    )
_cmp.update( gte= _cmp.ge, lte= _cmp.le)

# XXX beware xtdb: (< x y) range_predicate works on same-kind-of-numbers only - cannot compare int with float
# XXX beware: (clojure.core/< x y) works on any-kind-of-numbers only
# also see https://clojuredocs.org/clojure.core/=  :  (1 != 1.0) , and https://clojuredocs.org/clojure.core/==  : (1 == 1.0)
# for strings, dates etc use compare , then <0 or >0 - cannot compare string to number
class any_cmp:
    @staticmethod
    def _compare( op, x, y):
        return (op, (sym('compare'), x, y ), 0)
        #XXX this breaks xtdb, returns empty response
        #needs 2 clauses with temp-var. i.e  [(compare x y) c] [> c 0]
    @classmethod
    def _ops_declare( klas, ops_translator):
        _ops_declare( klas, ops_translator, klas._compare)
any_cmp._ops_declare( _cmp)
# https://clojuredocs.org/clojure.core/compare
# https://stackoverflow.com/questions/58895698/how-to-compare-two-strings-alphabetically-in-clojure


def predicate3( op, x, y):
    'vector of list of op + two logic variables or literals'
    qs_assert( is_variable( x) or is_literal( x), 'pos1: needs variable or literal', x)
    qs_assert( is_variable( y) or is_literal( y), 'pos2: needs variable or literal', y)
    #if isinstance( op, str): op = sym(op)
    qs_assert( is_symbol( op), 'pos0/op: needs symbol', op)
    return predicate( op, x, y )

class range_predicate:
    @classmethod
    def _ops_declare( klas, ops_translator):
        _ops_declare( klas, ops_translator, predicate3)
range_predicate._ops_declare( _cmp)
cmp = range_predicate

#########

def notall( *clauses):
    'not-clause rejects a graph if all the clauses within it are true.'
    qs_assert_many( clauses, is_clause, 'clauses')
    return ( sym('not'), *clauses)

def _anyjoin( op, variables, *clauses):
    assert isinstance( op, str), op
    qs_assert_many( variables, is_variable, 'variables')
    qs_assert_many( clauses, is_clause, 'clauses')
    return ( sym( op), vector(variables), *clauses)

def notjoin( variables, *clauses):
    'not-join clause restricts the logic variables by asserting that there does not exist a match for a given sequence of clauses'
    return _anyjoin( 'not-join', variables, *clauses)

def orany( *clauses):
    '''or-clause is satisfied if any of its legs are satisfied.
    may need noops so all legs use all vars:
    Datomic: All clauses in 'or' must use same set of vars,
    https://docs.xtdb.com/language-reference/datalog-queries/#clause-or
    '''
    qs_assert_many( clauses, is_clause, 'clauses')
    return ( sym('or'), *clauses)
any_ = or_ = orany

def andall( *clauses):
    'and-clause is satisfied if all of its legs are satisfied.'
    qs_assert_many( clauses, is_clause, 'clauses')
    return ( sym('and'), *clauses)
all_ = and_ = andall

def orjoin( variables, *clauses):
    'similar to not-join but satisfied if any of its legs are satisfied.'
    return _anyjoin( 'or-join', variables, *clauses)

###############

def expr( op, *args):
    qs_assert( args, 'needs args')
    qs_assert( is_symbol( op), 'op needs symbol', op)
    return ( op, *args)

def if_( e_cond, e_then, e_else):
    return expr( sym('if'), e_cond, e_then, e_else)
def add( x,y): return expr( sym('+'), x,y)
def mul( x,y): return expr( sym('*'), x,y)
def div( x,y): return expr( sym('/'), x,y)
def sub( x,y): return expr( sym('-'), x,y)

def noop( var):
    '''for adding vars in a leg which does not need it, so all legs contain all vars - e.g. in orany.
    a predicate that is always true'''
    qs_assert( is_variable( var), 'needs variable', var)
    return predicate( sym('any?'), var)
def noops( *vars):
    return [ noop( var) for var in vars ]

#XXX any func: fully namespace-qualified unless in clojure.core
def pred_startswith( var, value):
    return predicate( sym2('clojure.string', 'starts-with?') , var, value)
#    https://clojuredocs.org/clojure.string


##Aggregates
# cannot be nested within another - e.g. (sum (count ?x)) is disallowed
def _aggregate1( name, var_or_expr):
    assert isinstance( name, str), name
    return expr( sym( name), var_or_expr)
def _aggregate2( name, n, var_or_expr):
    #print( locals())
    assert isinstance( name, str), name
    qs_assert( isinstance( n, int) and n>0, 'n needs be positive int', n)
    return expr( sym( name), n, var_or_expr)

class aggregate:
    @classmethod
    def _op_declare1( klas, name, funcname =None):
        for aname in set([ name, name.replace('-','_') ]):
            setattr( klas, aname, staticmethod( partial( _aggregate1, funcname or name)))
    @classmethod
    def _op_declare2( klas, name, funcname =None):
        for aname in set([ name, name.replace('-','_') ]):
            setattr( klas, aname, staticmethod( partial( _aggregate2, funcname or name)))
for a1 in 'sum min max count avg median variance stddev distinct count-distinct'.split():
    aggregate._op_declare1( a1)
for a2 in 'rand sample'.split():
    aggregate._op_declare2( a2)
aggr = aggregate

sym_ellipsis = sym('...')
sym_star = sym_wild = sym('*')

class qbase( dict):

    _allowed_kws = [ kw( x) for x in 'find where in  keys strs syms  rules'.split()]

    def __init__( me, *a, **ka):
        super().__init__( *a, **ka)
        unknowns = set( me) - set( me._allowed_kws)
        qs_assert( not unknowns, 'unknown query-items', unknowns)

    def _set( me, k, v):
        assert k not in me, f'already set {(k,me)}'
        me[ k ] = v
        return me
    def copy( me, without= ()):
        q = me.__class__( me)
        for k in without: q.pop( k, None)
        return q


    def find( me, *args):
        'result objects/tuples will contain these vars/exprs/pull()s in same order'
        #TODO datomic - this is like single is_in_spec - but over (var | expr | pull)
        qs_assert_many( args, is_variable_or_clause, 'vars or exprs or aggrs or pull-exprs')
        return me._set( kw.find, vector( args ))
    def where( me, *clauses):
        'filter taking clauses - order is ignored'
        qs_assert_many( clauses, is_clause, 'clauses')
        return me._set( kw.where, vector( clauses))
    def into_keys( me, *names, as_what =kw.keys):
        '''result objects as maps/dicts with these keynames as keyword/symbol/str keys ;
        order/count must match those in .find ;
        XT: sym-only
        DA: allows "str" -> :str ; int-> nil??? ; sym -> :sym ; :kw -> :kw
        '''
        qs_assert( names, 'missing names')
        if len(names)==1 and isinstance( names[0], str): names = names[0].split()
        lnames = len( names)
        lfinds = len( me.get( kw.find) or ())
        qs_assert( lnames == lfinds, f'needs len(names)={lnames} to equal len(find-results)={lfinds}')
        qs_assert_many( names, lambda k: k and isinstance( k, (str, Symbol)),
            'names: strs or symbols')
        vnames = vector( sym( k) if isinstance( k, str) else k for k in names)
        qs_assert( len( vnames) == len( set( vnames)), 'repeating names', names)
        assert as_what in (kw.keys, kw.strs, kw.syms), as_what
        return me._set( as_what, vector(
            sym( k) if isinstance( k, str) else k for k in names))
    def into_strs( me, *names):
        ''' XT: sym-only
        DA: allows "str" -> "str" ; int -> "int" ; sym -> "sym" ; :kw -> ":kw" '''
        return me.into_keys( *names, as_what= kw.strs)
    def into_syms( me, *names):
        ''' XT: sym-only
        DA: allows "str" -> "str" ; int -> int ; sym -> sym ; :kw -> :kw '''
        return me.into_keys( *names, as_what= kw.syms)

    kw_in = kw('in')
    def in_( me, *args):
        '''declare inputs/parameters
        https://docs.xtdb.com/language-reference/datalog-queries/#in
        https://docs.datomic.com/on-prem/query/query.html#inputs
        https://docs.datomic.com/on-prem/query/query.html#grammar
        vector of combination of these:
        #scalar     : var1
        #collection : [ var1 ... ]       #var1 is either of the supplied ones i.e. OR-of-singles
        #tuple      : [ var1 var2 var3 ] # together i.e. AND
        #relation   : [ [ var1 var2 ] ]  #var1 and var2 are either of the supplied couples i.e. OR-of-tuples
        #TODO pull-pattern /da : sympattern  #to be used in pull-expr ???

        #XXX - actual passed in-args must match this spec. see match_args_to_spec
        '''
        qs_assert_many( args, lambda a: _is_in_spec( a, me._is_specs), 'input-specs')
        return me._set( me.kw_in, vector( args ))
    input = inputs = params = parameters = in_
    #_is_specs = ()     #defined below

    kw_rules = kw.rules
    def rules( me, *rules):
        '''use rule() to construct these ;
        Multiple rule bodies may be defined having same rule name/head.. works as orjoin'''
        qs_assert_many( rules, is_rule, 'rules')
        return me._set( me.kw_rules, vector( rules))

    @staticmethod
    def arg_spec_checker( arg, spec):
        if is_spec_scalar( spec):
            arg_scalar( arg)    #ignore result
        else:
            qs_assert( is_vector( spec), 'invalid arg-spec', spec)
            if is_spec_collection( spec):
                qs_assert_many( arg, is_arg_scalar, 'scalars')
            elif is_spec_tuple( spec):
                qs_assert_many( arg, is_arg_scalar, 'scalars')
            elif is_spec_relation( spec):
                qs_assert_many( arg, is_sequence, 'sequence of sequences of scalars')
                for titems in arg:
                    qs_assert_many( titems, is_arg_scalar, 'scalars')   #one-or-more tuples of scalars?
            else: qs_assert( False, 'invalid arg-spec', spec)

    def match_args_to_spec( me, in_args):
        'check whether input values match the spec - see qbase.in_'
        in_spec = me.get( me.kw_in ) or ()
        #https://docs.xtdb.com/language-reference/datalog-queries/#in
        #https://docs.datomic.com/on-prem/query/query.html#inputs
        assert is_sequence( in_args), in_args
        assert is_sequence( in_spec), in_spec
        assert len( in_spec) == len( in_args), f'arg count mismatch {(in_spec, in_args)}'
        for arg,spec in zip( in_args, in_spec):
            me.arg_spec_checker( arg, spec)
        return in_spec


#spec-check
def is_spec_scalar( a):
    #this also goes for src-var and rules-var
    return is_variable( a)      #dereference globals; do not just isx=isy
def is_spec_tuple( a):
    return is_vector( a) and all( is_variable( t) for t in a)
def is_spec_collection( a):
    return is_vector( a) and len(a) == 2 and is_variable( a[0]) and a[1] == sym_ellipsis
def is_spec_relation( a):
    return is_vector( a) and len(a) == 1 and is_vector( a[0] ) and all( is_variable( r) for r in a[0] )
def _is_in_spec( a, is_specs):
    return a and any( f(a) for f in is_specs)

#spec-make
def in_scalar( a):
    qs_assert( is_variable( a), 'needs variable', a)
    return a
def in_collection( a):
    qs_assert( is_variable( a), 'needs variable', a)
    return [ a, sym_ellipsis ]
in_scalar_one_of = in_collection
def in_tuple( *args):
    qs_assert_many( args, is_variable, 'variables')
    return vector( args)
def in_relation( *args):
    qs_assert_many( args, is_variable, 'variables')
    return [ vector( args) ]
in_tuple_one_of = in_relation

#arg-value-make
is_arg_scalar = is_literal
def arg_scalar( a):
    qs_assert( is_arg_scalar( a), 'needs scalar', a)
    return a
def arg_collection( *items):
    qs_assert_many( items, is_arg_scalar, 'scalars')
    return vector( items)
arg_scalar_one_of = arg_collection
arg_tuple = arg_collection
def arg_relation( *tuples_or):
    qs_assert_many( tuples_or, is_sequence, 'sequence of sequences of scalars')
    for titems in tuples_or:
        qs_assert_many( titems, is_arg_scalar, 'scalars')   #one-or-more tuples of scalars?
    return [ vector( t) for t in tuples_or ]
arg_tuple_one_of = arg_relation

qbase._is_specs = [ #in this order
    is_spec_scalar, is_spec_collection, is_spec_tuple, is_spec_relation,
    #pull-pattern ??? TODO
    ]

###############

def rule( name, params, *clauses):
    '''make a rule:
    https://docs.datomic.com/on-prem/query/query.html#rules-grammar
    https://docs.xtdb.com/language-reference/datalog-queries/#rules
    '''
    qs_assert( is_symbol( name), 'name needs symbol', name)
    #bound-param: use [ param ] instead of just param
    if params:
        qs_assert_many( params, _is_rule_param_or_bound,
            'params: variables or vectors-of-one-variable/bound')
    qs_assert_many( clauses, is_clause, 'clauses')
    return [ ( name, *params), *clauses ]

def is_rule( r):
    qs_assert( is_vector( r), 'rule needs be vector', r)
    head,*body = r
    qs_assert( is_clause( head), 'rule-head needs be clause', head, r)
    name, *params = head
    qs_assert( is_symbol( name), 'rule-head-name needs be symbol', name, r)
    #bound-param: use [ param ] instead of just param
    if params:
        qs_assert_many( params, _is_rule_param_or_bound,
            'params: variables or vectors-of-one-variable/bound')
    qs_assert_many( body, is_clause, 'clauses')
    return True

def _is_rule_param_or_bound( x):
    return is_variable( x) or is_vector( x) and len(x)==1 and is_variable( x[0])

###############

def pull( var, *attrs, whole =False):
    'make a pull descriptor, to be used in qbase.find'
    qs_assert( is_variable( var), 'needs variable', var)
    if not attrs: whole = True  #auto-assume..
    if whole and sym_wild not in attrs:
        attrs = [ sym_wild, *attrs ]    #so attrs override whole
    #TODO https://docs.xtdb.com/language-reference/datalog-queries/#_attribute_parameters
    # https://docs.datomic.com/on-prem/query/pull.html#attribute-with-options   -> may even be dict( tuple: list )
    qs_assert_many( attrs,
            lambda n: is_keyword( n) or n==sym_wild or isinstance( n, (dict,*sequences)) ,
            'attr-specs: keywords or maps or expr/vectors')
    return (sym.pull, var, vector( attrs))

def _text2dumps1line( x):
    return ' '.join( x.split()).replace(' ]', ']').replace( ' }', '}').replace('[ ', '[').replace( '{ ', '{')
def _text2maplines( x):
    return _text2dumps1line( x).replace( '{:', '{ :').replace( ' :','\n :')


if __name__ == '__main__':
    debug = 0
    def testeq( res, exp):
        assert res == exp, locals()
    def testdump( res, exp):
        if debug: print( repr(res), '    ??', exp)
        testeq( edn_dumps( res), exp)

    def testsame( these, exp):
        testdump( these[0], exp)
        #print( these[:1])
        assert 1==len( set( these)), set( these)

    kw1tests = [ kw.a , kw('a') ]  #should be all same
    testsame( kw1tests, ':a')

    try: kw.a.b
    except AttributeError as e:
        assert str(e) == "'Keyword' object has no attribute 'b'", e
    else: assert 0*'AttributeError not raised'

    kw2tests = [ kw2.a.b , kw2('a', 'b') , kw2.a('b') , kw2('a').b , kw2('a')('b') ]  #should be all same
    testsame( kw2tests, ':a/b')

    try: kw2.a.b.c
    except AttributeError as e:
        assert str(e) == "'Keyword' object has no attribute 'c'", e
    else: assert 0*'AttributeError not raised'

    testdump(
        { Keyword('find'): [ Symbol('p')] ,
          Keyword('where'): [
            [ Symbol('p'), Keyword('age'), 5  ]
            ] }
        , '{:find [p] :where [[p :age 5]]}'
        )

    testdump(
        { kw.find: [ sym.p ] , kw.where: [ ( sym.p, kw.age, 6 ),] }
        , '{:find [p] :where [(p :age 6)]}'
        )

    testdump(
        qbase().find( sym.p ).where( var_attr_value( sym.p, kw.age, 7  ))
        , '{:find [p] :where [[p :age 7]]}'
        )

    testdump(
        { kw.find: [ sym.p ] , kw.where: ( ( sym2('?p').r, kw2.me.age, 8  ),) }
        , '{:find [p] :where ((?p/r :me/age 8))}'
        )

    testdump(
        qbase().find( sym.p ).where( var_attr_value( sym.p, kw.age, sym.a), range_predicate.gt( sym.a, 5) )
        , '{:find [p] :where [[p :age a] [(> a 5)]]}'
        )

    def test_r3():
        ''' pyhuman-translation:
            for obj in all-objects:
                if exists obj.city and obj.name:
                    yield dict( id= obj.id, city= obj.city, name= obj.name)
        '''
        r3 = """
            {:find [?id ?name ?city]
                :keys [id name city]
                :where [[?id :city ?city]
                     [?id :name ?name]
                     ]
                }
        """
        if debug: print('----r3', r3)
        r3flat = _text2dumps1line( r3)

        q = { kw.find: [ var.id, var.name, var.city ] ,
                kw.keys:  [ sym.id, sym.name, sym.city ],
                kw.where: [
                    [ var.id, kw.city, var.city ],
                    [ var.id, kw.name, var.name ],
                    ],
            }
        testdump( q, r3flat)

        q2= qbase(
            ).find( var.id, var.name, var.city
            ).into_keys( 'id', 'name', 'city'    #corresponding to above vars
            ).where(
                var_attr_value( var.id, kw.city, var.city ),
                var_attr_value( var.id, kw.name, var.name ),
            )
        testdump( q2, r3flat)

    test_r3()
    testdump( any_cmp.lt( sym.a, 5), '(< (compare a 5) 0)')

# vim:ts=4:sw=4:expandtab
