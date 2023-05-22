import base.qsyntax
base.qsyntax.is_variable = base.qsyntax.is_variable_datomic
from base.qsyntax import *


''' https://docs.datomic.com/on-prem/query/query.html#query
https://docs.datomic.com/on-prem/query/query.html#grammar
rpc.query() , using bin/rest peer

+find               # https://docs.datomic.com/on-prem/query/query.html#find-specifications
+pull-expr          # https://docs.datomic.com/on-prem/query/query.html#pull-expressions
+keys/strs/syms     # https://docs.datomic.com/on-prem/query/query.html#return-maps
+where
+rules              - with optional source-db INFRONT
       TODO.. qbase.rules is not usable as is ???
+in - binding dbargs and external args , dbarg0 is given by default in rpc.query # https://docs.datomic.com/on-prem/query/query.html#inputs
-orderby ; use min ?? :  [:find ?e ?v (min ?e)   :where [?e :db/doc ?v] ]
+limit/offset outside, in rpc.query
-timeout - none in bin/rest # https://docs.datomic.com/on-prem/query/query.html#timeout

+not / not-join     - with optional source-db INFRONT # https://docs.datomic.com/on-prem/query/query.html#not-clauses
+or / or-join / and - with optional source-db INFRONT # https://docs.datomic.com/on-prem/query/query.html#or-clauses
+var_attr_value     - with optional source-db INFRONT + 5-tuple
+predicate  # https://docs.datomic.com/on-prem/query/query.html#predicate-expressions
+func-call  # https://docs.datomic.com/on-prem/query/query.html#function-expressions
-subquery
-unification_predicate
+builtins:  # https://docs.datomic.com/on-prem/query/query.html#built-in-expressions
 +range_predicate = > < >= <=  !=
 +add/sub/mul/div
 +ground  fulltext  get-else  get-some  missing?  tuple / untuple
    --- tx-ids / tx-data - these need db.log as input ?? no way via REST
 +all functions from the clojure.core namespace excl. eval, others need be fully qualified and be on classpath
 +methods - static or instance - https://docs.datomic.com/on-prem/query/query.html#calling-java
+aggregates # https://docs.datomic.com/on-prem/query/query.html#aggregates
 +:with - grouping # https://docs.datomic.com/on-prem/query/query.html#with

'''

blank = anything = sym('_')  # https://docs.datomic.com/on-prem/best-practices.html#blanks-in-data-patterns  https://docs.datomic.com/on-prem/query/query.html#blanks
src_var  = edn_factory1( edn_format.Symbol, '$')
rule_var = edn_factory1( edn_format.Symbol, '%')
src_default = sym('$')
rule_default= sym('%')

range_predicate._ops_declare( dict(
    ne = sym( '!='),
    ))
#for a1 in 'count-distinct'.split():
#    aggregate._op_declare1( a1)
for a2 in 'min max'.split():
    aggregate._op_declare2( a2+'_n', a2)

def quadro_clause( var, attr, value =None, txtime= None):
    c = eav( var, attr, value)
    if not txtime: return c
    #TODO check txtime
    if len(c) == 2:
        return cl( *c, anything, txtime )   #???
    return cl( *c, txtime )
eavt = entity_attr_value_time = quadro_clause

def type_hint( classname):
    '''https://docs.datomic.com/on-prem/query/query.html#type-hinting
    ^ClassName preceding an argument
    '''
    if '.' in classname:
        assert all( a.isidentifier() for a in classname.split('.')), classname
    else:
        assert classname.isidentifier(), classname
    return sym( '^'+classname)

def is_spec_src_default( a):
    return a == src_default
def is_spec_rule_default( a):
    return a == rule_default

class daq( qbase):
    _allowed_kws = qbase._allowed_kws + [ kw('with') ]
    def with_( me, *args):
        'extra variables for aggregation/grouping'
        qs_assert( args, is_variable_datomic, 'variables')
        return me._set( kw('with'), vector( args ))

    _is_specs = [ is_spec_src_default, is_spec_rule_default, *qbase._is_specs ]
    @classmethod
    def arg_spec_checker( klas, arg, spec):
        if is_spec_src_default( spec):
            arg_scalar( arg)    #ignore result  #XXX ??? or isinstance( a, str) and a ?
        elif is_spec_rule_default( spec):
            qs_assert_many( arg, is_rule, 'rules')
        else:
            super().arg_spec_checker( arg, spec)


qbuilder = daq

# vim:ts=4:sw=4:expandtab
