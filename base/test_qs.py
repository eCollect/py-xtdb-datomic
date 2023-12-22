from .qsyntax import edn_dumps, Keyword, Symbol
from .qsyntax import kw, kw2, sym, sym2, var, sym_ellipsis, var_attr_value, _text2maplines, qbase as q
from . import qsyntax as qs    #for all else
import unittest
import re

class Base:
    maxDiff = None

    def assert_dumps( me, input, exp, liner =False):
        res = edn_dumps( input)
        if liner: res,exp = (_text2maplines(x) for x in (res,exp))
        return me.assertEqual( res, exp)

    def assert_error( me, err):
        assert err
        return me.assertRaisesRegex( AssertionError, re.escape( err)) #, msg= f'case: {case}')
    def assert_error2( me, err):
        assert err
        return me.assertRaisesRegex( RuntimeError, re.escape( err))
    def assert_qserror( me, err, exact =True):
        assert err
        rerr = re.escape( err)
        if exact: rerr = '^'+rerr+'$'
        return me.assertRaisesRegex( qs.QSError, rerr)

class Primitives( Base, unittest.TestCase):
    def test_compare(me):
        any_cmp = qs.any_cmp
        me.assert_dumps( any_cmp.lt( sym.a, 5), '(< (compare a 5) 0)')

    def test_var_attr_value(me):
        # ok - len = 2
        me.assert_dumps( var_attr_value( sym.p123, kw.age), '[p123 :age]')
        me.assert_dumps( var_attr_value( var.p123, kw.age), '[?p123 :age]')
        me.assert_dumps( var_attr_value( 3, kw.age),        '[3 :age]')
        # ok - len = 3 (integer)
        me.assert_dumps( var_attr_value( sym.p, kw.age, 7), '[p :age 7]')
        me.assert_dumps( var_attr_value( var.p, kw.age, 7), '[?p :age 7]')
        me.assert_dumps( var_attr_value( 1, kw.age, 7),     '[1 :age 7]')
        # ok - len = 3 (string)
        me.assert_dumps( var_attr_value( sym.x, kw.y, 'z'), '[x :y "z"]')
        # ok - len = 3 (nil)
        me.assert_dumps( var_attr_value( sym.x, kw.y, None), '[x :y nil]')

        # invalid var
        with me.assert_qserror( 'pos0: needs variable or literal: [1]'):
            var_attr_value( [1], kw.age, 3)
        # invalid attr
        with me.assert_qserror( 'pos1: needs keyword: 2'):
            var_attr_value( var.x, 2, 3)
        with me.assert_qserror( 'pos1: needs keyword: Symbol(?y)'):
            var_attr_value( var.x, var.y, 3)
        # invalid len <=1 -> TypeError.. no need
        with me.assert_qserror( 'only one value allowed: (3, 2)'):
            var_attr_value( var.x, kw.age, 3, 2)

    def ztest_range_predicate(me):
        # TODO
        pass

    def test_pred3(me):
        predicate3 = qs.predicate3
        # ok
        me.assert_dumps( predicate3( sym.p123, sym.x, sym.y),   '[(p123 x y)]')
        me.assert_dumps( predicate3( sym.p123, sym.x, 1),       '[(p123 x 1)]')
        me.assert_dumps( predicate3( sym.p123, sym.x, None),    '[(p123 x nil)]')
        me.assert_dumps( predicate3( sym.p123, 2, 1),           '[(p123 2 1)]')

        with me.subTest( 'wrong op type'):
            with me.assert_qserror( "pos0/op: needs symbol: 'p123'"):
                predicate3( 'p123', sym.x, sym.y)
            with me.assert_qserror( 'pos0/op: needs symbol: 3'):
                predicate3( 3, sym.x, sym.y)
        with me.subTest( 'wrong arg type'):
            with me.assert_qserror( 'pos1: needs variable or literal: Keyword(x)'):
                predicate3( sym.a, kw.x, 3)
            with me.assert_qserror( 'pos1: needs variable or literal: [2]'):
                predicate3( sym.a, [2], 3)
            with me.assert_qserror( 'pos2: needs variable or literal: [3]'):
                predicate3( sym.a, 2, [3])

    def test_noop(me):
        noop = qs.noop
        # ok
        me.assert_dumps( noop( sym.p123), '[(any? p123)]')

        with me.subTest( 'invalid var - type'):
            with me.assert_qserror( "needs variable: 'p123'"):
                noop( "p123")
            with me.assert_qserror( "needs variable: 3"):
                noop( 3)
            with me.assert_qserror( "needs variable: Keyword(x)"):
                noop( kw.x)
            with me.assert_qserror( "needs variable: [Symbol(x)]"):
                noop( [ sym.x ])

    def _test_lister_no_scope( me, func, opname):
        # ok
        me.assert_dumps( func( [sym.x, sym.y]),     f'({opname} [x y])')
        me.assert_dumps( func( [sym.x], [sym.y]),   f'({opname} [x] [y])')
        me.assert_dumps( func( ["xyz"]),            f'({opname} ["xyz"])')
        me.assert_dumps( func( [3]),                f'({opname} [3])')

        with me.subTest( 'invalid clause - type'):
            with me.assert_qserror( 'needs clauses: Symbol(x)'):
                func( sym.x)
            with me.assert_qserror( "needs clauses: 'p123'"):
                func( 'p123')
        with me.subTest( 'invalid clause = empty'):
            with me.assert_qserror( "needs clauses: []"):
                func( [])

        with me.assert_qserror( "missing clauses"):
            func()

    def test_notall(me):
        me._test_lister_no_scope( qs.notall, 'not')
    def test_orany(me):
        me._test_lister_no_scope( qs.orany, 'or')

    def _test_joiner_scoped( me, func, opname):
        me.assert_dumps(
            func( [sym.x], [sym.p123]),
            f'({opname} [x] [p123])')
        me.assert_dumps(
            func( [sym.x], [sym.p123], ['sym.y']),
            f'({opname} [x] [p123] ["sym.y"])')
        me.assert_dumps(
            func( [sym.x], [sym.p123], [3]),
            f'({opname} [x] [p123] [3])')

        with me.assert_qserror( 'missing variables'):
            func( [], [sym.p123])
        with me.assert_qserror( 'missing clauses'):
            func( [sym.p123])
        with me.subTest( 'empty clause'):
            with me.assert_qserror( 'needs clauses: []'):
                func( [sym.p123], [])
        with me.subTest( 'invalid vars - type'):
            # [str]
            with me.assert_qserror( "needs variables: 'x'"):
                func( ['x'], [sym.p123])
            # [int]
            with me.assert_qserror( 'needs variables: 3'):
                func( [3], [sym.p123])
            # non-iterable
            with me.assert_qserror( "needs tuple/list of variables: Symbol(x)"):
                func( sym.x, [sym.p123])

    def test_notjoin(me):
        me._test_joiner_scoped( qs.notjoin, 'not-join')
    def test_orjoin(me):
        me._test_joiner_scoped( qs.orjoin, 'or-join')

    def test_pred_startswith(me):
        pred_startswith = qs.pred_startswith
        # ok
        me.assert_dumps(
            pred_startswith( sym.p123, sym.x),
            '[(clojure.string/starts-with? p123 x)]')
        # ok - with string
        me.assert_dumps(
            pred_startswith( 'sym.p123', 'x'),
            '[(clojure.string/starts-with? "sym.p123" "x")]')
        # ok - with integer
        me.assert_dumps(
            pred_startswith( 3, 3),
            '[(clojure.string/starts-with? 3 3)]')

    def test_add(me):
        add = qs.add
        # ok
        me.assert_dumps(
            add( sym.x, sym.y),
            '(+ x y)')
        # ok - with integer
        me.assert_dumps(
            add( 1, 3),
            '(+ 1 3)')
        # ok - with string
        me.assert_dumps(
            add( 'x', 'y'),
            '(+ "x" "y")')

    def test_if(me):
        if_ = qs.if_
        # ok
        me.assert_dumps(
            if_( sym.x, sym.y, sym.z),
            '(if x y z)')
        # ok - with integer
        me.assert_dumps(
            if_( 1, 2, 3),
            '(if 1 2 3)')
        # ok - with string
        me.assert_dumps(
            if_( 'sym.x', 'sym.y', 'sym.z'),
            '(if "sym.x" "sym.y" "sym.z")')

    def test_rule(me):
        rule = qs.rule
        #ok
        # one 1-clause
        me.assert_dumps(
            rule( sym.name, [sym.p1], [sym.x]),
            '[(name p1) [x]]')
        # one 2-clause
        me.assert_dumps(
            rule( sym.name, [sym.p1], (sym.x, sym.y)),
            '[(name p1) (x y)]')
        # two clauses
        me.assert_dumps(
            rule( sym.name, [sym.p1], [sym.x, sym.y], [sym.z] ),
            '[(name p1) [x y] [z]]')
        # ok - empty params
        me.assert_dumps(
            rule( sym.name, [], (sym.x, sym.y)),
            '[(name) (x y)]')
        # ok - many params
        me.assert_dumps(
            rule( sym.name, [sym.p1, sym.p2], (sym.x, sym.y)),
            '[(name p1 p2) (x y)]')
        # ok - bound param
        me.assert_dumps(
            rule( sym.name, [[sym.p1]], (sym.x, sym.y)),
            '[(name [p1]) (x y)]')
        # ok - normal + bound param
        me.assert_dumps(
            rule( sym.name, [[sym.p1], sym.p2], (sym.x, sym.y)),
            '[(name [p1] p2) (x y)]')

        #errors:

        # name not symbol=int/kw
        with me.assert_qserror( 'name needs symbol: 3'):
            rule( 3, [sym.p1], (sym.x, sym.y))
        with me.assert_qserror( 'name needs symbol: Keyword(x)'):
            rule( kw.x, [sym.p1], (sym.x, sym.y))
        # param not symbol=int/kw
        with me.assert_qserror( 'needs params: variables or vectors-of-one-variable/bound: 3'):
            rule( sym.name, [3], (sym.x, sym.y))
        with me.assert_qserror( 'needs params: variables or vectors-of-one-variable/bound: Keyword(x)'):
            rule( sym.name, [kw.x], (sym.x, sym.y))
        # bound param = longer-than-1-list
        with me.assert_qserror( 'needs params: variables or vectors-of-one-variable/bound: [Symbol(x), Symbol(y)]'):
            rule( sym.name, [[sym.x, sym.y]], (sym.x, sym.y))
        # params not list
        with me.assert_qserror( 'needs tuple/list of params: variables or vectors-of-one-variable/bound: Symbol(p1)'):
            rule( sym.name, sym.p1, (sym.x, sym.y))
        with me.assert_qserror( "needs tuple/list of params: variables or vectors-of-one-variable/bound: 'z'"):
            rule( sym.name, 'z', (sym.x, sym.y))
        # with invalid clause=int/sym/kw
        with me.assert_qserror( 'needs clauses: 2'):
            rule( sym.name, [sym.p1], 2)
        with me.assert_qserror( 'needs clauses: Symbol(x)'):
            rule( sym.name, [sym.p1], sym.x)
        with me.assert_qserror( 'needs clauses: Keyword(x)'):
            rule( sym.name, [sym.p1], kw.x)
        # with empty clause
        with me.assert_qserror( 'needs clauses: []'):
            rule( sym.name, [sym.p1], [])
        # missing clauses
        with me.assert_qserror( 'missing clauses'):
            rule( sym.name, [sym.p1] )

    def test_pull(me):
        me.assert_dumps(
            qs.pull( sym.eid, whole=True),
            '(pull eid [*])')
        me.assert_dumps(
            qs.pull( var.eid, whole=True),
            '(pull ?eid [*])')
        me.assert_dumps(
            qs.pull( var.x, kw.name, kw.age),
            '(pull ?x [:name :age])')
        me.assert_dumps(
            qs.pull( var.eid, kw.name, kw.age, whole=True),
            '(pull ?eid [* :name :age])')


        with me.assert_qserror( 'needs variable: 3'):
            qs.pull( 3, whole=True)
        if 0: #not anymore
          with me.assert_qserror( 'missing attr-specs: keywords or maps or expr/vectors'):
            qs.pull( sym.eid)
        else:
          me.assert_dumps(
            qs.pull( sym.xx),
            '(pull xx [*])')
        with me.assert_qserror( 'needs attr-specs: keywords or maps or expr/vectors: 4'):
            qs.pull( sym.name, 4)


class Query( Base, unittest.TestCase):

    def test_equivalence_struct_vs_translate_vs_qbuild(me):
        struct_edn = {
            Keyword('find'): [ Symbol('p')] ,
            Keyword('where'): [
                [ Symbol('p'), Keyword('age'), 5  ]
            ] }
        struct_translate = { kw.find: [ sym.p ] , kw.where: [ [ sym.p, kw.age, 5 ],] }
        query = q().find( sym.p ).where( var_attr_value( sym.p, kw.age, 5  ))

        me.assertEqual( struct_edn, struct_translate)
        me.assertEqual( struct_translate, query)

        exp_text = '{:find [p] :where [[p :age 5]]}'

        me.assert_dumps( struct_edn, exp_text)
        me.assert_dumps( struct_translate, exp_text)
        me.assert_dumps( query, exp_text)

    def test_equivalence_struct_vs_translate_vs_qbuild2(me):
        struct_edn = {
            Keyword('find'): [ Symbol('p'), Symbol('?q')] ,
            Keyword('where'): [
                [ Symbol('p'), Keyword('age'), 5  ],
                [ Symbol('p'), Keyword('name'), Symbol('?q')  ]
            ] }
        struct_translate = {
                kw.find: [ sym.p, var.q ] ,
                kw.where: [ [ sym.p, kw.age, 5 ],
                            [ sym.p, kw.name, var.q]
                ] }
        query = q().find( sym.p, var.q ).where(
                var_attr_value( sym.p, kw.age, 5  ),
                var_attr_value( sym.p, kw.name, var.q ),
                )

        me.assertEqual( struct_edn, struct_translate)
        me.assertEqual( struct_translate, query)

        exp_text = '{:find [p ?q] :where [[p :age 5] [p :name ?q]]}'

        me.assert_dumps( struct_edn, exp_text)
        me.assert_dumps( struct_translate, exp_text)
        me.assert_dumps( query, exp_text)


    def test_oks(me):
        me.assert_dumps(  #syms ???
            { kw.find: [ sym.p ] , kw.where: ( ( sym2('?p').r, kw2.me.age, 8  ),) },
            '{:find [p] :where ((?p/r :me/age 8))}')

        me.assert_dumps( #range_pred
            q().find( sym.p ).where(
                var_attr_value( sym.p, kw.age, sym.a),
                qs.range_predicate.gt( sym.a, 5) ),
            '{:find [p] :where [[p :age a] [(> a 5)]]}')

    def test_find(me):
        me.assert_dumps( #vars
            q().find( var.x, var.y ),
            '{:find [?x ?y]}')
        me.assert_dumps( #syms
            q().find( sym.p123, sym.p1 ),
            '{:find [p123 p1]}')
        me.assert_dumps( #syms, one repeating
            q().find( sym.p123, sym.p1, sym.p123),
            '{:find [p123 p1 p123]}')
        me.assert_dumps( #syms + tuple
            q().find( sym.p123, [sym.p1, sym.qq]),
            '{:find [p123 [p1 qq]]}')
        me.assert_dumps( #syms + coll
            q().find( sym.p123, [sym.p1, sym_ellipsis]),
            '{:find [p123 [p1 ...]]}')
        me.assert_dumps( #syms + rel
            q().find( sym.p123, [[sym.p1, sym.qq]]),
            '{:find [p123 [[p1 qq]]]}')

        errmsg = 'needs vars or exprs or aggrs or pull-exprs'
        with me.subTest( 'invalid arg - type'):
            with me.assert_qserror( errmsg + ': 3'):
                q().find( sym.p1, 3)
            with me.assert_qserror( errmsg + ": 'p1'"):
                q().find( 'p1', sym.p2)
            with me.assert_qserror( errmsg + ": 'sym.p3'"):
                q().find( sym.p1, 'sym.p3')
            with me.assert_qserror( errmsg + ': None'):
                q().find( sym.p1, None)
            with me.assert_qserror( errmsg + ': {Keyword(x): 2}'):
                q().find( sym.p1, { kw.x: 2 })
        with me.assert_qserror( 'missing vars or exprs or aggrs or pull-exprs'):
            q().find()

        #TODO more invalids ..

    def test_where(me):
        #clause-2-vector/tuple
        me.assert_dumps(
            q().find( sym.x ).where( var_attr_value( sym.p123, kw.age)),
            '{:find [x] :where [[p123 :age]]}')
        me.assert_dumps(
            q().find( sym.x).where( ( sym.p123, kw.age)),
            '{:find [x] :where [(p123 :age)]}')
        #clause-3
        me.assert_dumps(
            q().where( var_attr_value( sym.p123, kw.age, 7)),
            '{:where [[p123 :age 7]]}')
        #clause-4 ??
        me.assert_dumps(
            q().where( [ sym.p123, kw.age, 7, 8]),
            '{:where [[p123 :age 7 8]]}')
        #clause-1 ??
        me.assert_dumps(
            q().where( [ sym.p123]),
            '{:where [[p123]]}')
        #clause-1 ??
        me.assert_dumps(
            q().where( [ 123]),
            '{:where [[123]]}')
        #2clauses
        me.assert_dumps(
            q().where(
                var_attr_value( sym.p, kw.size, 1),
                var_attr_value( sym.p, kw.k2)),
            '{:where [[p :size 1] [p :k2]]}')

        errmsg = 'needs clauses'
        with me.subTest( 'invalid clause type'):
            with me.assert_qserror( f'{errmsg}: 3'):
                q().find( sym.x).where( 3)
            with me.assert_qserror( f'{errmsg}: Symbol(p)'):
                q().find( sym.x).where( sym.p)
            with me.assert_qserror( f"{errmsg}: 'x'"):
                q().find( sym.x).where( [sym.p], 'x')
            with me.assert_qserror( f'{errmsg}: None'):
                q().find( sym.x).where( [sym.p, kw.age], None)
        with me.subTest( 'invalid clause =empty'):
            with me.assert_qserror( f'{errmsg}: []'):
                q().find( sym.x).where( [])
        with me.assert_qserror( 'missing clauses'):
            q().find( sym.x).where( )

        #TODO ??
        #with me.assert_qserror( 'needs find()'):
        #    q().where( ( sym.p123, kw.age))


    def test_into_keys(me):
        #"same" names =str
        me.assert_dumps(
            q().find( var.id, var.name ).into_keys( 'id', 'name'),
            '{:find [?id ?name] :keys [id name]}')
        #other names =str
        me.assert_dumps(
            q().find( var.a, var.b, var.c ).into_keys( 'id', 'name', 'city' ),
            '{:find [?a ?b ?c] :keys [id name city]}')

        #"same" names =sym
        me.assert_dumps(
            q().find( var.id, var.name ).into_keys( sym.id, sym.name),
            '{:find [?id ?name] :keys [id name]}')
        #other names =sym
        me.assert_dumps(
            q().find( var.a, var.b ).into_keys( sym.id, sym.name ),
            '{:find [?a ?b] :keys [id name]}')

        #same names =str ??
        me.assert_dumps(
            q().find( var.id, var.name ).into_keys( '?id', '?name'),
            '{:find [?id ?name] :keys [?id ?name]}')
        #all same =var ??
        me.assert_dumps(
            q().find( var.id, var.name ).into_keys( var.id, var.name),
            '{:find [?id ?name] :keys [?id ?name]}')
        #other names =var ??
        me.assert_dumps(
            q().find( var.id, var.name ).into_keys( var.a, var.b),
            '{:find [?id ?name] :keys [?a ?b]}')

        with me.assert_qserror( 'needs len(names)=1 to equal len(find-results)=2'):
            q().find( var.id, var.p ).into_keys( 'id', )
        with me.assert_qserror( 'needs len(names)=3 to equal len(find-results)=1'):
            q().find( var.id ).into_keys( 'a', 'b', 'c' )
        with me.assert_qserror( "repeating names: ('a', 'a')"):
            q().find( var.id, var.x ).into_keys( 'a', 'a', )

        # missing
        with me.assert_qserror( "missing names"):
            q().find( var.id, var.name ).into_keys()
        # invalid name =int
        with me.assert_qserror( 'needs names: strs or symbols: 1'):
            q().find( var.id, var.name ).into_keys( 'id', 1 )
        # invalid name =list
        with me.assert_qserror( "needs names: strs or symbols: ['name']"):
            q().find( var.id, var.name ).into_keys( 'id', ['name'] )
        # invalid name =empty str
        with me.assert_qserror( "needs names: strs or symbols: ''"):
            q().find( var.id, var.name ).into_keys( 'id', '' )
        # invalid name =kw
        with me.assert_qserror( 'needs names: strs or symbols: Keyword(id)'):
            q().find( var.id).into_keys( kw.id)

        #variants of into_*
        me.assert_dumps(
            q().find( var.id, var.name ).into_strs( 'id', 'name'),
            '{:find [?id ?name] :strs [id name]}')
        me.assert_dumps(
            q().find( var.id, var.name ).into_syms( 'id', 'name'),
            '{:find [?id ?name] :syms [id name]}')

    def test_in(me):
        # ERR?ok repeating var
        me.assert_dumps(
            q().in_( sym.x, sym.y, sym.x),
            '{:in [x y x]}')

        # ok - with len = 2
        me.assert_dumps(
            q().in_( sym.x, sym.y),
            '{:in [x y]}')

        # invalid =int
        with me.assert_qserror( 'needs input-specs: 1'):
            q().find( sym.p123, sym.x ).in_( sym.p123, 1)


# TODO
# - .rules
# clauses
# range_predicate

if __name__ == '__main__':
    unittest.main() #verbosity=2)

if 0:   #no, raising loses the ctx, points to line in contextlib
    import contextlib
    def er( casename, errmsg):
        stack = contextlib.ExitStack()
        stack.enter_context( me.subTest( casename))
        stack.enter_context( me.assert_qserror( errmsg))
        return stack
    with er( 'invalid clause', 'somerrmsg'):
        whatever( [sym.x], 3)
if 0:   #no, not obvious what is being called/tested
    def err( name, arg =0):
        ix_wrong = arg
        def case( *args):
            msg = errmsg + ': ' + repr( args[ ix_wrong])
            with me.subTest( name):
                with me.assert_qserror( msg):
                    q().find( sym.x).where( *args)
        return case
    err( 'invalid clause', arg=1)  ( [sym.x], 3)

# vim:ts=4:sw=4:expandtab
