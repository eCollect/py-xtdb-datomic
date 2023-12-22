from .dbclient import xtdb
from .db2      import xtdb2
from . import qsyntax as qs
import base.rpc_edn_json_http
import edn_format
import unittest
from unittest.mock import MagicMock, patch
import datetime
if 1:
    from unittest.mock import NonCallableMock
    _format_mock_failure_message = NonCallableMock._format_mock_failure_message
    def _myformat_mock_failure_message( *a,**ka):
        r = _format_mock_failure_message( *a,**ka)
        return r.replace( '\nExpected:', '\nExpect:')
    NonCallableMock._format_mock_failure_message = _myformat_mock_failure_message

import os
URLROOT = os.getenv( 'XTDB') or 'http://localhost:3001'
V2 = bool( os.getenv( 'XTDB2'))
URL = URLROOT.rstrip('/') + ('' if V2 else '/_xtdb')
HEADERS = {'accept': 'application/edn', 'content-type': 'application/json'}
xtdbx = xtdb2 if V2 else xtdb

class Gets( unittest.TestCase):
    datetext = '2023-01-11T11:37:07.649+00:00'      #with-tz
    datetime = datetime.datetime.fromisoformat( datetext)
    datetext_edn = f'#inst "'+datetext.replace( '+00:00', '000Z')+'"'
    assert edn_format.dumps( datetime) == datetext_edn

    def setUp(self):
        self.db = xtdbx( URLROOT)
        #self.fake = base.rpc_edn_json_http.requests.get = MagicMock(return_value='x')
        self.fakeget = patch( 'base.rpc_edn_json_http.requests.get') # = MagicMock(return_value='x')
        self.fake = self.fakeget.start()
    def tearDown(self):
        #self.fakesend.stop()
        self.fakeget.stop()

    def test_status(self):
        self.fake.return_value = 'y'
        self.db._response = lambda x:x

        self.db.status()
        # print(11111, fake.mock_calls)
        self.fake.assert_called_once_with( f'{URL}/status', headers=HEADERS)

    def test_entity(self, method ='entity', suburl ='entity'):
        ''' passing eid=non-str moves+converts it into eid-edn=.. - testing the _params_eid+_params_cleaner checker/converter'''
        entity = getattr( self.db, method)
        URLentity = f'{URL}/{suburl}'
        self.db._response = lambda x:x
        self.fake.return_value = 'f'

        count = 0
        def assert_params( params):
            nonlocal count
            count += 1
            self.assertEqual( self.fake.call_count, count)
            self.fake.assert_called_with( URLentity, headers= HEADERS, params= params)

        entity( eid=123, valid_time= self.datetime) #int->edn/int ; valid_time converted by isoformat
        assert_params( {'eid-edn': '123', 'valid-time': self.datetext})
        entity( eid='x123' )                        #str->str
        assert_params( {'eid': 'x123'})
        entity( eid='123' )                         #str->str
        assert_params( {'eid': '123'})
        entity( eid= qs.kw.xy)                      #keyword->edn/keyword
        assert_params( {'eid-edn': ':xy'})
        entity( eid= self.datetime)                 #datetime->edn/datetime
        assert_params( {'eid-edn': self.datetext_edn })   #ok converted by edn.dumps

        #XXX no auto-edn-dumps, and requests.get gets params as-is.. but that's misleading as params would be str()ed
        entity( eid_edn= 123)       #int -> int -> url/str() which as edn would be int - ok
        assert_params( {'eid-edn': 123})
        entity( eid_edn= 'x123')    #str -> str -> url/str which as edn would be symbol XXX
        assert_params( {'eid-edn': 'x123'})
        entity( eid_edn= '123')     #str -> str -> url/str which as edn would be int XXX
        assert_params( {'eid-edn': '123'})
        entity( eid_edn= qs.kw.xy)  #keyword -> edn/keyword -> url/str() -> ok
        assert_params( {'eid-edn': qs.kw.xy})
        entity( eid_edn= self.datetime) #datetime -> isoformat/datetime -> url/str() XXX
        assert_params( {'eid-edn': self.datetext})    #ERR XXX converted by isoformat
        #XXX maybe *-edn/*-json params should not be auto-converted in _params_cleaner() ?

        self.fakeget.stop()
        #XXX actual session.send turns params into url, which makes 123 and '123' same ...=123 - an edn-int
        with patch( 'base.rpc_edn_json_http.requests.Session.send') as fake:
            url_ednint_123 = f'{URLentity}?eid-edn=123'
            count = 0
            def assert_url( url):
                nonlocal count
                count += 1
                self.assertEqual( fake.call_count, count)
                self.assertEqual( fake.call_args.args[0].url, url)

            entity( eid= '123')     #str -> str
            assert_url( f'{URLentity}?eid=123')
            entity( eid_edn= '123')     #str -> edn/int XXX
            assert_url( url_ednint_123)

            entity( eid= 'x5')      #str -> str
            assert_url( f'{URLentity}?eid=x5')    #would be error - x5 is symbol, not str
            entity( eid_edn= 'x5')  #str -> edn/symbol XXX
            assert_url( f'{URLentity}?eid-edn=x5')    #would be error - x5 is symbol, not str

            entity( eid= 123)       #int -> edn/int - ok
            assert_url( url_ednint_123)
            entity( eid_edn= 123)   #int -> edn/int - ok
            assert_url( url_ednint_123)

            entity( eid= qs.kw.xy)  # kw -> edn/kw - ok
            assert_url( f'{URLentity}?eid-edn=%3Axy')
            entity( eid_edn= qs.kw.xy)  #kw -> edn/kw - ok
            assert_url( f'{URLentity}?eid-edn=%3Axy')

            entity( eid= qs.sym.xy)  # kw -> edn/kw - ok
            assert_url( f'{URLentity}?eid-edn=xy')
            entity( eid_edn= qs.sym.xy) #sym -> edn/sym - ok
            assert_url( f'{URLentity}?eid-edn=xy')


        #other stuff..
        self.fakeget.start()
        # wrong parameters
        with self.assertRaisesRegex( AssertionError, 'unknown params.*firstz'):
            entity( eid=123, firstz='x')
        with self.assertRaisesRegex( AssertionError, 'unknown params.*with_docs'):
            entity( eid=123, with_docs=True)    #from entity_history
        # dont use together
        with self.assertRaisesRegex( AssertionError, 'needs exactly one of'):
            entity( eid=123, eid_edn=123)
        # missing eid-args
        with self.assertRaisesRegex( AssertionError, 'needs exactly one of'):
            entity()

        # empty eid - #XXX maybe these should be allowed ?
        with self.assertRaisesRegex( AssertionError, 'needs non-empty value'):
            entity( eid='')
        with self.assertRaisesRegex( AssertionError, 'needs non-empty value'):
            entity( eid=0)  #XXX maybe this should be allowed ?


    def test_entity_tx(self):
        return self.test_entity( 'entity_tx', 'entity-tx')

    def test_entity_history(self):
        self.fake.return_value = 'f'
        self.db._response = lambda x:x
        URLentity = f'{URL}/entity'
        entity_history = self.db.entity_history

        entity_history( eid=123, start_valid_time= self.datetime)
        self.fake.assert_called_once_with( URLentity, headers=HEADERS, params={'history': 'true', 'sort-order': 'desc', 'eid-edn': '123', 'start-valid-time': self.datetext})

        entity_history( eid=123, with_docs= True, start_valid_time= self.datetime)
        self.fake.assert_called_with( URLentity, headers=HEADERS, params={ 'with-docs': 'true', 'history': 'true', 'sort-order': 'desc', 'eid-edn': '123', 'start-valid-time': self.datetext})

        entity_history( eid=123, with_docs= True )
        self.fake.assert_called_with( URLentity, headers=HEADERS, params={ 'with-docs': 'true', 'history': 'true', 'sort-order': 'desc', 'eid-edn': '123' })

        entity_history( eid=123)
        self.fake.assert_called_with( URLentity, headers=HEADERS, params={ 'history': 'true', 'sort-order': 'desc', 'eid-edn': '123' })

        entity_history( eid=123, ascending= True)
        self.fake.assert_called_with( URLentity, headers=HEADERS, params={ 'history': 'true', 'sort-order': 'asc', 'eid-edn': '123' })

        # wrong parameters
        with self.assertRaisesRegex( AssertionError, 'unknown params.*firstz'):
            entity_history( eid=123, firstz='x')
        # missing eid-args
        with self.assertRaisesRegex( AssertionError, 'needs exactly one of'):
            entity_history()

URLquery = f'{URL}/query'#if not V2 else f'{URL}/datalog'   #TODO only intermediate, future v2 should be /query again
HEADERSedn = {'accept': 'application/edn', 'content-type': 'application/edn'}

class Posts(unittest.TestCase):
    def setUp(self):
        self.db = xtdbx( URLROOT)
        self.fake = base.rpc_edn_json_http.requests.post = MagicMock(return_value='x')
        self.datetext = '2023-01-11T11:37:07.649'
        self.datetime = datetime.datetime.fromisoformat( self.datetext)

    def test_query_str(self):
        self.fake.return_value = 'f'
        self.db._response = lambda x:x
        q = ' {:query {:find [ id ] :where [[x :xt/id id]] :limit 1}} '
        query = self.db.query
        query( q, valid_time= self.datetime)
        #print(11111, self.fake.mock_calls)
        # ok
        self.fake.assert_called_once_with( URLquery, data= q, headers= HEADERSedn, params= {'valid-time': self.datetext})

        with self.subTest( 'invalid query type/content'):
            with self.assertRaises( AssertionError):
                query( query= 123)
            #with self.assertRaises( AssertionError):
            #    query( query= 'query')
            with self.assertRaises( AssertionError):
                query( query= [q])
            with self.assertRaisesRegex( qs.QSError, 'unknown query-items'):
                query( query= dict( x=5) )
            # empty
            with self.assertRaises(TypeError):
                query()

        # unknown args
        with self.assertRaisesRegex( AssertionError, 'unknown.*myarg'):
            query( q, myarg=4 )
        with self.subTest( 'query=str with separate in-args'):
            with self.assertRaisesRegex( AssertionError, 'with separate in_args='):
                query( q, 34)


    def test_query_dict_inputs(self):
        self.fake.return_value = 'i'
        self.db._response = lambda x:x
        query = self.db.query
        qtxt = '{:query {:find [id] :where [[x :xt/id id]] :limit 1}}'
        q = qs.xtq().find( qs.sym.id
            ).where( qs.var_attr_value( qs.sym.x, self.db.id_kw, qs.sym.id)
            ).limit( 1)
        query( q, valid_time= self.datetime)
        #print(11111, self.fake.mock_calls)
        # ok
        self.fake.assert_called_once_with( URLquery, data= qtxt, headers= HEADERSedn, params= {'valid-time': self.datetext})

        query( q.copy().in_( qs.sym.x ), 23)
        qtxt2 = qtxt.replace( '}}', ' :in [x]} :in-args [23]}')
        self.fake.assert_called_with( URLquery, data= qtxt2, headers= HEADERSedn, params= {})

        with self.assertRaisesRegex( AssertionError, 'arg count mismatch'):
            query( q.copy().in_( qs.sym.y ))
        with self.assertRaisesRegex( AssertionError, 'arg count mismatch'):
            query( q, 12)

    def test_query_dict_limits(self):
        self.fake.return_value = 'i'
        self.db._response = lambda x:x
        query = self.db.query
        qtxt = '{:query {:find [id] :where [[x :xt/id id]]}}'
        q = qs.xtq().find( qs.sym.id
            ).where( qs.var_attr_value( qs.sym.x, self.db.id_kw, qs.sym.id)
            )
        assert qs.kw.limit not in q
        #no limit
        query( q)
        self.fake.assert_called_with( URLquery, data= qtxt, headers= HEADERSedn, params= {})

        assert qs.kw.limit not in q
        #no limit in q, with extra limit
        query( q, limit=1)
        qtxt1 = qtxt.replace( '}}', ' :limit 1}}')
        self.fake.assert_called_with( URLquery, data= qtxt1, headers= HEADERSedn, params= {})

        query( q, timeout_ms=2)
        qtxt2 = qtxt.replace( '}}', ' :timeout 2}}')
        self.fake.assert_called_with( URLquery, data= qtxt2, headers= HEADERSedn, params= {})

        assert qs.kw.limit not in q
        #limit in q, no extra limit
        q = q.limit( 1)
        query( q)
        self.fake.assert_called_with( URLquery, data= qtxt1, headers= HEADERSedn, params= {})

        with self.assertRaisesRegex( AssertionError, 'already set \(Keyword\(limit\),'):
            query( q, limit=5)  #no overrides yet XXX

        q.pop( qs.kw.limit) #no overrides yet XXX
        assert qs.kw.limit not in q
        query( q, limit=5)
        qtxt5 = qtxt1.replace( 'limit 1', 'limit 5')
        self.fake.assert_called_with( URLquery, data= qtxt5, headers= HEADERSedn, params= {})


if __name__ == '__main__':
    unittest.main() #verbosity=2)

# vim:ts=4:sw=4:expandtab
