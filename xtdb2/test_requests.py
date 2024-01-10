from .dbclient import xtdb2
from . import qsyntax as qs
import base.rpc_json_http
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
URLROOT = os.getenv( 'XTDB') or 'http://localhost:3002'
URL = URLROOT.rstrip('/')


HEADERS = {'accept': 'application/edn', 'content-type': 'application/json'}

class Gets( unittest.TestCase):
    datetext = '2023-01-11T11:37:07.649+00:00'      #with-tz
    datetime = datetime.datetime.fromisoformat( datetext)
    datetext_edn = f'#inst "'+datetext.replace( '+00:00', '000Z')+'"'
    assert edn_format.dumps( datetime) == datetext_edn

    def setUp(self):
        self.db = xtdb2( URLROOT)
        #self.fake = base.rpc_json_http.requests.get = MagicMock(return_value='x')
        self.fakeget = patch( 'base.rpc_json_http.requests.get') # = MagicMock(return_value='x')
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


URLquery = f'{URL}/query'
HEADERSedn = {'accept': 'application/edn', 'content-type': 'application/edn'}

class Posts(unittest.TestCase):
    def setUp(self):
        self.db = xtdb2( URLROOT)
        self.fake = base.rpc_json_http.requests.post = MagicMock(return_value='x')
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


if __name__ == '__main__':
    unittest.main() #verbosity=2)

# vim:ts=4:sw=4:expandtab
