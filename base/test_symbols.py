from base.qsyntax import Keyword, Symbol
from base.qsyntax import sym, sym2, kw, kw2, check_sym_name_level, is_literal, is_symbol, is_keyword, is_clause, is_variable_or_clause, edn_factory2, QSError, edn_dumps
from base import qsyntax as qs
from base.test_qs import Base
import unittest, datetime

# https://github.com/edn-format/edn

e_empty     = 'naming: name-or-prefix needs non-empty string'
e_start     = 'naming: name-or-prefix cannot start with ":" or "#" or digit'
e_afterstart= 'naming: name-or-prefix cannot have digit after starting "." or "-" or "+"'
e_allowed   = 'naming: name-or-prefix allows alphanumerics and'    #...
e_1_slash   = 'naming: only one / allowed'
name_errors = [ e_empty, e_start, e_afterstart, e_allowed, e_1_slash ]

class kw_levels( Base, unittest.TestCase):
    def test_L1_ok_1_level(self):
        ka = Keyword( 'a')
        kw1tests = [ kw.a , kw('a') ]
        for i in kw1tests:
            self.assertIsInstance( i, Keyword)
            self.assertEqual( i, ka)
            self.assertEqual( str(i), ':a')
        self.assertEqual( len( set( [ka] + kw1tests)), 1)

    def test_L2_ok_1_level(self):
        level1 = kw2.a
        self.assertIsInstance( level1, edn_factory2._edn2_half)
        self.assertNotIsInstance( level1, Keyword)
        self.assertNotEqual( level1, kw.a)
        self.assertIn( 'edn_factory2._edn2_half', str(level1))
        kax = Keyword( 'a/x')
        l1tests = [ level1.x , level1('x') ]
        for i in l1tests:
            self.assertIsInstance( i, Keyword)
            self.assertEqual( i, kax)
            self.assertEqual( str(i), ':a/x')
        self.assertEqual( len( set( [kax] + l1tests)), 1)

    def test_L2_ok_2_levels(self):
        kw2tests = [ kw2.a.b , kw2('a', 'b') , kw2.a('b') , kw2('a').b , kw2('a')('b') ]
        kab = Keyword( 'a/b')
        for i in kw2tests:
            self.assertIsInstance( i, Keyword)
            self.assertEqual( i, kab)
            self.assertEqual( str(i), ':a/b')
        self.assertEqual( len( set( [kab] + kw2tests)), 1)

    def test_no_more_levels(self):
        with self.assertRaisesRegex(AttributeError, "'Keyword' object has no attribute 'b'"):
            kw.a.b
        with self.assertRaisesRegex(AttributeError, "'Keyword' object has no attribute 'c'"):
            kw2.a.b.c
        with self.assertRaisesRegex(TypeError, "'Keyword' object is not callable"):
            kw.a('b')
        with self.assertRaisesRegex(TypeError, "'Keyword' object is not callable"):
            kw2.a.b('x')

    def test_L1_names(self):
        doc='''
https://github.com/edn-format/edn

Symbols begin with a non-numeric character and can contain alphanumeric
characters and . * + ! - _ ? $ % & = < >. If -, + or . are the first character,
the second character (if any) must be non-numeric. Additionally, : # are
allowed as constituent characters in symbols other than as the first
character.

/ has special meaning in symbols. It can be used once only in the middle of a
symbol to separate the prefix (often a namespace) from the name.
/ by itself is a legal symbol, but otherwise neither the
prefix nor the name part can be empty when the symbol contains /.

If a symbol has a prefix and /, the following name component should follow the
first-character restrictions for symbols as a whole. This is to avoid ambiguity
in reading contexts where prefixes might be presumed as implicitly included
namespaces and elided thereafter.

Keywords are identifiers that typically designate themselves. They are
semantically akin to enumeration values. Keywords follow the rules of symbols,
except they must begin with : , which is disallowed for symbols.
Per the symbol rules above, :/ and :/anything are not legal keywords.
A keyword cannot begin with ::
(::some/name1 is Clojure shorthand for :someverylong/name1 if 'some' is aliased to :xyzlong)
'''


        def c( name , *, sym= 'result/ERR', kw= 'result/ERR', case= 'description'):
            if kw == 'result/ERR': kw = sym
            assert sym != 'result/ERR', sym
            assert kw != 'result/ERR', kw
            assert case and case != 'description', case
            for kind,okerr in dict( sym= sym, kw= kw ).items():
                func = getattr( qs, kind)
                with self.subTest( f'{case}::::: {kind} {name!r}'):
                    if okerr not in name_errors:
                        self.assertEqual( edn_dumps( func( name)), okerr)
                    else:
                        with self.assert_qserror( okerr, exact= False ):
                            func( name)
        # XXX =err?ok means it does err BUT spec allows it - e.g. names :a/:b and :# are spec-allowed

        #plain
        c( 'a',     sym= 'a',       kw=':a',    case= 'name')
        c( 'a1',    sym= 'a1',      kw=':a1',   case= 'name')
        c( '_',     sym= '_',       kw=':_',    case= 'name-_')
        c( '_a',    sym= '_a',      kw=':_a',   case= 'name-_')
        c( 'a_',    sym= 'a_',      kw=':a_',   case= 'name-_')
        c( '_1',    sym= '_1',      kw=':_1',   case= 'name-_')

        # 1 slash
        c( '/',     sym= '/',       kw=e_empty, case= 'only / =ok but :/ =err')
        c( 'a/b',   sym= 'a/b',     kw=':a/b',  case= 'namespace/name')
        c( 'a/_',   sym= 'a/_',     kw=':a/_',  case= 'namespace/name-_')
        c( 'a/_b',  sym= 'a/_b',    kw=':a/_b', case= 'namespace/name-_')
        c( 'a/b_',  sym= 'a/b_',    kw=':a/b_', case= 'namespace/name-_')
        c( 'a1/b2', sym= 'a1/b2',   kw=':a1/b2',case= 'namespace/name')
        c( 'a_/b_', sym= 'a_/b_',   kw=':a_/b_',case= 'namespace/name-_')
        c( '_a/_b', sym= '_a/_b',   kw=':_a/_b',case= 'namespace/name-_')
        c( '/a',    sym= e_empty,               case= '/a :/a =err')
        c( '/2',    sym= e_empty,               case= '/2 :/2 =err')
        c( 'a/',    sym= e_empty,               case= 'a/ :a/ =err')
        c( '1/',    sym= e_start,               case= '1/ :1/ =err')

        #start-with/with-many . - +
        c( '.',     sym= '.',       kw=':.',    case= 'name-start-.')
        c( '+a',    sym= '+a',      kw=':+a',   case= 'name-start-+')
        c( '.a',    sym= '.a',      kw=':.a',   case= 'name-start-.')
        c( '-a',    sym= '-a',      kw=':-a',   case= 'name-start--')
        c( '..',    sym= '..',      kw=':..',   case= 'name-start-.')
        c( '---',   sym= '---',     kw=':---',  case= 'name-start--')
        c( '.a/.b', sym= '.a/.b',   kw=':.a/.b', case= 'namespace/name-with-.')
        c( '.a/..', sym= '.a/..',   kw=':.a/..', case= 'namespace/name-with-.')
        c( 'a.b/.c.d', sym= 'a.b/.c.d', kw=':a.b/.c.d', case= 'namespace/name-with-.')
        c( 'a/+',   sym= 'a/+',     kw=':a/+',  case= 'namespace/name-start-+')
        c( '+/+',   sym= '+/+',     kw=':+/+',  case= 'namespace/name-start-+')

        # colon : --- hash #
        c( ':',     sym= e_start,               case= ': :: =err')
        c( ':a',    sym= e_start,               case= ':a ::a =err')
        c( 'a:',    sym= 'a:',      kw=':a:',   case= 'a: :a: =ok')
        c( '.:',    sym= '.:',      kw=':.:',   case= '.: :.: =ok')
        c( ':a/b',  sym= e_start,               case= ':a/b ::a/b =err')
        c( '#',     sym= e_start,               case= '# =err  :#  =err?ok')
        c( '#a',    sym= e_start,               case= '#a =err :#a =err?ok')
        c( 'a#',    sym= 'a#',      kw=':a#',   case= 'a#   :a# =ok')
        c( '.#',    sym= '.#',      kw=':.#',   case= '.#   :.# =ok')
        c( '/:',    sym= e_empty,               case= '/:   :/: =err')
        c( '/:a',   sym= e_empty,               case= '/:a  :/:a  =err')
        c( 'a/:',   sym= e_start,               case= 'a/:  :a/:  =err')
        c( 'a/:b',  sym= e_start,               case= 'a/:b :a/:b =err?ok')
        c( '/#',    sym= e_empty,               case= '/#   :/#   =err')
        c( '/#a',   sym= e_empty,               case= '/#a  :/#a  =err')
        c( 'a/#',   sym= e_start,               case= 'a/#  :a/#  =err?ok')
        c( 'a/#b',  sym= e_start,               case= 'a/#b :a/#b =err?ok')

        #empty/whitespace
        c( '',      sym= e_empty,               case= 'empty =err')
        c( ' ',     sym= e_allowed,             case= 'whitespace =err')
        c( ',',     sym= e_allowed,             case= ', is whitespace =err')
        c( ' x',    sym= e_allowed,             case= 'whitespace =err')
        c( 'x ',    sym= e_allowed,             case= 'whitespace =err')
        c( 'x y',   sym= e_allowed,             case= 'whitespace =err')
        c( ',',     sym= e_allowed,             case= ', is whitespace =err')
        c( ',x',    sym= e_allowed,             case= ', is whitespace =err')
        c( 'x,',    sym= e_allowed,             case= ', is whitespace =err')
        c( 'x,y',   sym= e_allowed,             case= ', is whitespace =err')
        #non-str
        c( 1,       sym= e_empty,               case= 'non-str:int   =err')
        c( None,    sym= e_empty,               case= 'non-str:None  =err')
        c( (),      sym= e_empty,               case= 'non-str:tuple =err')
        c( (1,2),   sym= e_empty,               case= 'non-str:tuple =err')
        c( [1],     sym= e_empty,               case= 'non-str:list  =err')
        #digit-start
        c( '1',     sym= e_start,               case= 'startdigit =err but err?ok')
        c( '1a',    sym= e_start,               case= 'startdigit =err but err?ok')
        c( '1+2',   sym= e_start,               case= 'startdigit =err but err?ok')
        c( '0x2',   sym= e_start,               case= 'startdigit =err but err?ok')
        c( '123',   sym= e_start,               case= 'startdigit =err but err?ok')
        c( '1/a',   sym= e_start,               case= 'startdigit =err but err?ok')
        c( 'a/1',   sym= e_start,               case= 'startdigit =err')
        c( '1/2',   sym= e_start,               case= 'startdigit =err')
        #2+ slashes
        c( 'a/b/c', sym= e_1_slash,             case= '2+ slashes =err')
        c( '//',    sym= e_1_slash,             case= '2+ slashes =err')
        c( 'a/b/',  sym= e_1_slash,             case= '2+ slashes =err')
        c( '/a/b',  sym= e_1_slash,             case= '2+ slashes =err')
        c( '/ab/',  sym= e_1_slash,             case= '2+ slashes =err')
        c( 'a/b/c/d', sym= e_1_slash,           case= '2+ slashes =err')
        #not in allowed
        c( '~',     sym= e_allowed,             case= 'disallowed:~ =err')
        c( 'a~',    sym= e_allowed,             case= 'disallowed:~ =err')
        c( '~a',    sym= e_allowed,             case= 'disallowed:~ =err')
        c( 'a/~',   sym= e_allowed,             case= 'disallowed:~ =err')
        c( 'a/~b',  sym= e_allowed,             case= 'disallowed:~ =err')
        c( 'a/b~',  sym= e_allowed,             case= 'disallowed:~ =err')
        c( '(a)',   sym= e_allowed,             case= 'disallowed:() =err')
        c( 'a[1',   sym= e_allowed,             case= 'disallowed:[  =err')
        c( 'a[1]',  sym= e_allowed,             case= 'disallowed:[] =err')
        #digits after starting .+-
        c( '+1',    sym= e_afterstart,          case= 'number-like =err')
        c( '-1',    sym= e_afterstart,          case= 'number-like =err')
        c( '.1',    sym= e_afterstart,          case= 'number-like =err')
        c( 'a/+1',  sym= e_afterstart,          case= 'number-like =err')
        c( 'a/.1',  sym= e_afterstart,          case= 'number-like =err')
        c( '-.1',   sym= '-.1',     kw= ':-.1', case= 'weird almost number-like =ok')
        c( '+.1',   sym= '+.1',     kw= ':+.1', case= 'weird almost number-like =ok')
        c( '+-1',   sym= '+-1',     kw= ':+-1', case= 'weird  =ok')
        c( '--1',   sym= '--1',     kw= ':--1', case= 'weird  =ok')
        c( '.-1',   sym= '.-1',     kw= ':.-1', case= 'weird  =ok')
        c( '.+1',   sym= '.+1',     kw= ':.+1', case= 'weird  =ok')
        c( '..1',   sym= '..1',     kw= ':..1', case= 'weird  =ok')

    def test_L2_names_level1(self):
        #TODO something around this + above table?
        for func in sym2, kw2:
            for err in [ '', ' ', 'a/', '/a',
                '1/a', 'a/2', '1/2', '1/',
                ':', ':a', 'a/:', 'a/+1', '#', '#1', '#x',
                'a/b', '/', 2, ' /', 'a/ ', ' /a'
                ]:
                #print( 222, repr(err))
                with self.assert_qserror( repr(err), exact= False):
                    func( err)
                if err:     #same at level2
                    with self.assert_qserror( repr(err), exact= False):
                        func( 'x', err)

    def test_L2_names_level2(self):
        level1 = kw2.a
        for err in [ '', ' ', 2, None, [1],
                    *' ,  a/  /a  /  a/b  1 1a  :  #  :a  #a  +1 .0  ~  [ '.split()]:
            with self.assert_qserror( repr(err), exact= False):
                level1( err)


class symbols_keywords( Base, unittest.TestCase):

    def test_check_sym_name(self):
        'maybe this is redundant.. implementation-detgail ; above sym-vs-kw is the appropriate'

        # begin with non-numeric and can contain alphanumeric
        for ok in 'x x1 xy xy1 '.split():
            check_sym_name_level( ok)

        # also special characters without :#
        allowed_anywhere = '. * + ! - _ ? $ % & = < >'.split()
        for char in allowed_anywhere:
            check_sym_name_level( f'x{char}')   # as second char
            check_sym_name_level( f'{char}x')   # as first char
            check_sym_name_level( f'{char}{char}')   # both first+second char
            check_sym_name_level( char)   # alone
            if char not in '-+.':
                check_sym_name_level( f'{char}1')   # as first char then digit
            else:
                with self.assert_qserror( e_afterstart, exact= False):
                    check_sym_name_level( f'{char}1')

        # non-empty str
        for err in [ None, 1, '', ]:
            with self.assert_qserror( f'{e_empty}: {err!r}'):
                check_sym_name_level( err)
        #invalid chars
        for err in [
                ' ', ' x', 'x ', 'x y',
                ',', 'a,b', '(a)', 'a[2]',
                'x/y', '/', 'x/', '/x',     #does not allow /
                ' /', '/ ',
                ]:
            with self.assert_qserror( e_allowed, exact= False):
                check_sym_name_level( err)

        # !(begin with non-numeric)
        for err in [ '1', '102', '1x', '0.',]:
            with self.assert_qserror( e_start, exact= False):
                check_sym_name_level( err)

        allowed_not_first = ': #'.split()
        for char in allowed_not_first:
            check_sym_name_level( f'x{char}')   # ok as second char
            for err in [
                f'{char}x',     # err as first char
                f'{char}{char}',   # err both first+second char
                char ]:         # err alone
                with self.assert_qserror( e_start, exact= False):
                    check_sym_name_level( err)

        # If some of - + . is the first character, the second (if any) must be non-numeric
        for err in [ '.1', '-1', '+1', '+0', '.0' ]:
            with self.assert_qserror( e_afterstart, exact= False):
                check_sym_name_level( err)

        # weird but ok
        for sym in ['-.1', '..', '-.', '.', '.-', '-+']:
            check_sym_name_level( sym)

    def test_is_literal(self):
        for ok in [ None, 'x', 1, 2.5, 0, '0', '3', datetime.datetime.now(), datetime.datetime.today() ]:
            self.assertTrue( is_literal( ok), repr(ok) )
        for err in [ sym.x, sym2.a.b, kw.a, kw2.x.y, (), (1,2), [], [1,2], {} ]:
            self.assertFalse( is_literal( err), repr(err) )

    def test_is_symbol(self):
        for ok in [ sym.x, sym2.x.y, sym('a'), sym('a/b'), Symbol('x') ]:
            self.assertTrue( is_symbol( ok), repr(ok))
        for err in [ kw.x, 'sym.x', sym2.x, kw2.x, 3, 'x', ':x', [], (sym.x,), [sym.x], None ]:
            self.assertFalse( is_symbol( err), repr(err))

    def test_is_keyword(self):
        for ok in [ kw.x, kw2.x.y, kw('a'), kw('a/b'), Keyword('x') ]:
            self.assertTrue( is_keyword( ok), repr(ok))
        for err in [ sym.x, 'kw.x', sym2.x, kw2.x, 3, 'x', ':x', [], (kw.x,), [kw.x], None ]:
            self.assertFalse( is_keyword( err), repr(err))

    def test_is_clause(self):
        def is__clause( *x): self.assertTrue( is_clause( *x))
        def not_clause( *x): self.assertFalse( is_clause( *x))
        # one argument
        is__clause( [sym.x])
        is__clause( [kw.x])
        is__clause( ( 'x', 'y'))
        is__clause( [1, 2, 3])
        is__clause( [1, 2])
        not_clause( 'x')
        not_clause( 1,)
        not_clause( [])
        not_clause( ())
        not_clause( sym.x)

        # more arguments
        is__clause( ( 'x', 'y'), ('f', 'a'))
        is__clause( [1, 2, 3], [4, 5, 6])
        not_clause( 'x', 'y')
        not_clause( 'x', ( 'x', 'y'))
        not_clause( ( 'x', 'y'), 'x')
        not_clause( 1, 2)

    def test_is_variable_or_clause(self):
        # ok
        self.assertTrue( is_variable_or_clause( sym.x))
        self.assertTrue( is_variable_or_clause( ['x', 'y', 'f']))
        self.assertTrue( is_variable_or_clause( (1, 2 )))
        self.assertTrue( is_variable_or_clause( [sym.x]))
        self.assertTrue( is_variable_or_clause( [kw.x]))
        self.assertFalse( is_variable_or_clause( 'x'))
        self.assertFalse( is_variable_or_clause( kw.x))
        self.assertFalse( is_variable_or_clause( 1))

if __name__ == '__main__':
    unittest.main() #verbosity=2)

# vim:ts=4:sw=4:expandtab
