from base.qsyntax import kw, kw2, sym, sym2, var, _text2maplines, sym_ellipsis
from base import test_qs
from .qsyntax import xtq, aggregate, unification_predicate, var_attr_value, rule, pull, is_rule
import unittest

class Query( test_qs.Base, unittest.TestCase):

    def test_order_by( me):
        # one field desc
        me.assert_dumps(
            xtq().find( sym.p123, sym.id).orderby( ( sym.id, kw.desc)),
            '{:find [p123 id] :order-by [[id :desc]]}')
        # one field asc
        me.assert_dumps(
            xtq().find( sym.p123, sym.id).orderby( ( sym.id, kw.asc)),
            '{:find [p123 id] :order-by [[id :asc]]}')
        # multiple fields mixed
        me.assert_dumps(
            xtq().find( sym.p123, sym.id).orderby( [ sym.p123, kw.desc], [ sym.id, kw.asc]),
            '{:find [p123 id] :order-by [[p123 :desc] [id :asc]]}')

        errmsg = 'needs tuples of (variable-from-find, keyword.asc-or-desc)'
        def err( name, *args, ix_wrong =0):
            with me.subTest( name):
                with me.assert_qserror( errmsg + ': ' + repr( args[ ix_wrong])):
                    xtq().find( sym.p123, sym.id).orderby( *args)

        err( 'one invalid var', (sym.id, kw.asc), (1, kw.desc), ix_wrong=1)
        err( 'one valid var not in find-vars', (sym.id, kw.asc), (sym.x, kw.desc), ix_wrong=1)
        err( 'invalid asc/desc', (sym.id, kw.order))
        err( 'invalid asc/desc', (sym.id, '-'))
        err( 'swapped', (kw.asc, sym.id))

        err( 'tuple-len > 2', (sym.id, kw.desc, sym.p123))
        err( 'tuple-len > 2', (sym.id, kw.desc, kw.desc))
        err( 'tuple-len < 2', (sym.id, ))

    def _test_int( me, qfuncname, dboptname =None):
        dboptname = dboptname or qfuncname
        def q_with_option( value):
            q = xtq().find( sym.x)
            return getattr( q, qfuncname)( value)

        me.assert_dumps(
            q_with_option( 5),
            '{:find [x] :'+dboptname+' 5}')

        errmsg = 'needs positive int'
        def err( name, *args, ix_wrong =0):
            with me.subTest( name):
                with me.assert_qserror( f'{errmsg}: ' + repr( args[ ix_wrong])):
                    q_with_option( *args)

        err( 'invalid =str',    '5')
        err( 'invalid =0',      0)
        err( 'invalid =neg',    -2)
        err( 'invalid =float',  5.0)
        err( 'invalid =tuple',  (5,))

    def test_limit( me): me._test_int( 'limit')
    def test_offset( me): me._test_int( 'offset')
    def test_timeout_ms( me): me._test_int( 'timeout_ms', dboptname= 'timeout')

    def test_rules(me):
        r1 = rule( sym.name2, [sym.parm], (sym.p1, sym.p123))
        me.assert_dumps( r1, '[(name2 parm) (p1 p123)]')
        me.assertTrue( is_rule( r1))

        me.assert_dumps(
            xtq().rules( r1),
            '{:rules [[(name2 parm) (p1 p123)]]}')

        with me.assert_qserror( 'rule needs be vector', exact=False):
            is_rule( (1,2,3) )
        with me.assert_qserror( 'rule-head needs be clause', exact=False):
            is_rule( [1,2,3] )

        # TODO

    def test_r3(me):
        r3 = """
            {:find [?id ?name ?city]
                :keys [id name city]
                :where [[?id :city ?city]
                     [?id :name ?name]
                     ]
                :limit 5
            }"""
        r3flat = _text2maplines( r3)

        q1 = { kw.find: [ var.id, var.name, var.city ] ,
                kw.keys:  [ sym.id, sym.name, sym.city ],
                kw.where: [
                    [ var.id, kw.city, var.city ],
                    [ var.id, kw.name, var.name ],
                    ],
                kw.limit: 5
            }

        q2= xtq(
            ).find( var.id, var.name, var.city
            ).into_keys( 'id', 'name', 'city'    #corresponding to above vars
            ).where(
                var_attr_value( var.id, kw.city, var.city ),
                var_attr_value( var.id, kw.name, var.name ),
            ).limit( 5)

        # ok
        me.assertEqual( q1, q2)
        me.assert_dumps( q1, r3flat, liner=True)
        me.assert_dumps( q2, r3flat, liner=True)


class Primitives( test_qs.Base, unittest.TestCase):

    def test_unification_predicate(me):
        # ok, both syms
        me.assert_dumps( unification_predicate.equ( sym.x, sym.y), '[(== x y)]')
        me.assert_dumps( unification_predicate.neu( sym.x, sym.y), '[(!= x y)]')
        # ok - with one symbol and one literal
        me.assert_dumps( unification_predicate.equ( 1, sym.x), '[(== 1 x)]')
        me.assert_dumps( unification_predicate.neu( sym.x, 1), '[(!= x 1)]')
        me.assert_dumps( unification_predicate.neu( sym.x, 'y'), '[(!= x "y")]')
        me.assert_dumps( unification_predicate.neu( sym.x, None), '[(!= x nil)]')

        # without symbols
        with me.assert_qserror( 'args needs be both symbols, or a symbol and literal: (1, 6)'):
            unification_predicate.neu( 1,6)
        with me.assert_qserror( "args needs be both symbols, or a symbol and literal: ('x', 'y')"):
            unification_predicate.equ( 'x', 'y')
        with me.assert_qserror( "args needs be both symbols, or a symbol and literal: ('x', 2)"):
            unification_predicate.equ( 'x', 2)

        with me.assert_qserror( 'pos2: needs variable or literal: Keyword(y)'):
            unification_predicate.neu( sym.x, kw.y)

        #same left=right symbols
        with me.assert_qserror( 'args cannot be same: (Symbol(x), Symbol(x))'):
            unification_predicate.equ( sym.x, sym.x)
        with me.assert_qserror( 'args cannot be same: (Symbol(x), Symbol(x))'):
            unification_predicate.neu( sym.x, sym.x)

    def test_aggregate(me):
        # ok
        me.assert_dumps( aggregate.sum( sym.x), '(sum x)')
        me.assert_dumps( aggregate.rand( 1, sym.x), '(rand 1 x)')

        #err n= zero
        with me.assert_qserror( 'n needs be positive int: 0'):
            aggregate.rand( 0, sym.x)
        #err n= string
        with me.assert_qserror( "n needs be positive int: 'asd'"):
            aggregate.rand( 'asd', sym.x)
        #err n= sym
        with me.assert_qserror( 'n needs be positive int: Symbol(x)'):
            aggregate.rand( sym.x, sym.y)


#TODO:
# - rules
# clauses

if __name__ == '__main__':
    unittest.main() #verbosity=2)

# vim:ts=4:sw=4:expandtab
