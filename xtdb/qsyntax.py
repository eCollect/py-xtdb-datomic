from base.qsyntax import *

''' https://docs.xtdb.com/language-reference/datalog-queries/
rpc.query()

+find           # https://docs.xtdb.com/language-reference/datalog-queries/#find
+pull-expr      # https://docs.xtdb.com/language-reference/datalog-queries/#pull
+keys/strs/syms # https://docs.xtdb.com/language-reference/datalog-queries/#return-maps
+where          # https://docs.xtdb.com/language-reference/datalog-queries/#where
+rules
+limit/offset/timeout inside { :query .. }
+in - binding external args (db is preset) # https://docs.xtdb.com/language-reference/datalog-queries/#in

+not / not-join     # https://docs.xtdb.com/language-reference/datalog-queries/#clause-not
+or / or-join / and # https://docs.xtdb.com/language-reference/datalog-queries/#clause-or
+var_attr_value
+predicate  # https://docs.xtdb.com/language-reference/datalog-queries/#clause-pred
+func-call  # https://docs.xtdb.com/language-reference/datalog-queries/#find-expressions
+subquery   # https://docs.xtdb.com/language-reference/datalog-queries/#where-subqueries
+unification_predicate # https://docs.xtdb.com/language-reference/datalog-queries/#clause-unification
+range_predicate = > < >= <= , BUT NO !=   # https://docs.xtdb.com/language-reference/datalog-queries/#clause-range
+add/sub/mul/div
 +all functions from the clojure.core namespace incl. eval, others need be fully qualified  https://docs.xtdb.com/language-reference/datalog-queries/#custom-functions
+aggregates # https://docs.xtdb.com/language-reference/datalog-queries/#find-aggregate
 - grouping - only implicit

also see:
https://docs.xtdb.com/language-reference/datalog-queries/#datascript-differences

'''

def subquery( q): return predicate( sym.q, q)

def _unification( op, x, y):
    '.. Literals (and sets of literals) can also be used in place of one of the logic variables.'
    qs_assert( is_symbol( x) or is_symbol(y), 'args needs be both symbols, or a symbol and literal', (x,y))     #one must be symbol, one can be literal
    qs_assert( x != y, 'args cannot be same', (x,y))
    return predicate3( op, x, y)
class unification_predicate:
    equ = partial( _unification, sym('=='))
    neu = partial( _unification, sym('!='))
unify = unification_predicate


class xtq( qbase):
    _allowed_kws = qbase._allowed_kws + [ kw( x) for x in 'limit offset order-by timeout'.split()]
    def orderby( me, *args):
        '''requires elements from .find ; docs: ..will automatically spill to disk when large..
        https://docs.xtdb.com/language-reference/datalog-queries/#ordering-and-pagination
        '''
        #TODO :desc :asc -- :order-by [[time :desc] [device-id :asc]]})
        #.orderby( +sym.time, -sym('device-id') __pos__ __neg__ ???
        finds = me[ kw.find]
        qs_assert_many( args, lambda a: (isinstance( a, sequences)
                and len(a) == 2
                and is_variable( a[0] )
                and a[1] in (kw.asc, kw.desc)
                and a[0] in finds
                ), 'tuples of (variable-from-find, keyword.asc-or-desc)')
        return me._set( kw( 'order-by'), vector( list(a) for a in args ))
        #XXX above complains on ().. so ()/[] are not always equivalent

    def limit( me, x):
        'https://docs.xtdb.com/language-reference/datalog-queries/#ordering-and-pagination'
        qs_assert( isinstance( x, int) and x>0, 'needs positive int', x)
        return me._set( kw.limit, x )
    def offset( me, x):
        '''docs: ..will naively walk..
        https://docs.xtdb.com/language-reference/datalog-queries/#ordering-and-pagination
        https://github.com/xtdb/xtdb/discussions/1514
        '''
        qs_assert( isinstance( x, int) and x>0, 'needs positive int', x)
        return me._set( kw.offset, x )
    def timeout_ms( me, x):
        qs_assert( isinstance( x, int) and x>0, 'needs positive int', x)
        return me._set( kw.timeout, x )

def order_ascending( x):  return [ x, kw.asc]
asc = order_ascending
def order_descending( x): return [ x, kw.desc]
desc = order_descending

qbuilder = xtq

# vim:ts=4:sw=4:expandtab
