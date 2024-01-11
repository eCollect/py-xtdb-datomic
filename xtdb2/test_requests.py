from xtdb2.dbclient import xtdb2, transit_dumps, transit_loads, tx_key
from xtdb2 import dbclient
dbclient.DEBUG = 0
from transit import transit_types
Symbol = transit_types.Symbol
Keyword= transit_types.Keyword

import base.rpc_json_http
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

dt_text = '2023-01-11T11:37:07.649000+00:00'      #with-tz-offset
dt_obj = datetime.datetime.fromisoformat( dt_text)
dt_ts = f'["~#time/instant","{dt_text}"]'
def dt_text_02z( x): return x.replace( '+00:00', 'Z')
def dt_text_z20( x): return x.replace( 'Z', '+00:00')

tk_obj= tx_key( tx_id= 123, system_time= datetime.datetime(2022, 2, 10, 20, 30, 40, 987242, tzinfo =datetime.UTC))
tk_ts = '["~#xtdb/tx-key",["^ ","~:tx-id",123,"~:system-time",["~#time/instant","2022-02-10T20:30:40.987242+00:00"]]]'

class transport( unittest.TestCase):
    def test_datetime( me):
        me.assertEqual( transit_dumps( dt_obj ), dt_ts)
        me.assertEqual( transit_loads( dt_ts), dt_obj)
        me.assertEqual( transit_loads( dt_text_02z( dt_ts)), dt_obj)
    def test_tuple( me):
        x = (1, 'a')
        ts = '["~#list",[1,"a"]]'
        me.assertEqual( transit_dumps( x), ts)
        me.assertEqual( transit_loads( ts), x)
    def test_tx_key( me):
        me.assertEqual( transit_dumps( tk_obj), tk_ts)
        me.assertEqual( transit_loads( tk_ts), tk_obj)
        me.assertEqual( transit_loads( dt_text_02z( tk_ts)), tk_obj)
    def test_dict_auto_keywordize( me):
        x = { 'a':1, ':b':2, 'xt/some': 'xt/other' }
        ts = '["^ ","~:a",1,"~::b",2,"~:xt/some","xt/other"]'
        me.assertEqual( transit_dumps( x), ts)
        loaded = transit_loads( ts)
        me.assertEqual( loaded, x)
        me.assertTrue( isinstance( loaded, transit_types.frozendict))
        with me.assertRaisesRegex( TypeError, "does not support item assignment"):
            loaded[ 3] = 4

URLROOT = 'http://localhost:3002'
URL = URLROOT.rstrip('/')
URLquery = f'{URL}/query'
URLsubmit_tx = f'{URL}/tx'

_app_transit_json = 'application/transit+json'
HEADERS = { 'accept': _app_transit_json, 'content-type': _app_transit_json }

class Gets( unittest.TestCase):
    def setUp(me):
        me.db = xtdb2( URLROOT)
        #me.fake = base.rpc_json_http.requests.get = MagicMock(return_value='x')
        me.fakeget = patch( 'base.rpc_json_http.requests.get') # = MagicMock(return_value='x')
        me.fake = me.fakeget.start()
    def tearDown(me):
        #me.fakesend.stop()
        me.fakeget.stop()

    def test_status(me):
        me.fake.return_value = 'y'
        me.db._response = lambda x:x

        me.db.status()
        # print(11111, fake.mock_calls)
        me.fake.assert_called_once_with( f'{URL}/status', headers=HEADERS)

class Posts(unittest.TestCase):
    def setUp( me):
        me.db = xtdb2( URLROOT)
        me.fake = base.rpc_json_http.requests.post = MagicMock( return_value= 'x')  #why not patch ??? XXX

    def assert_call_data_eq( me, data):
        me.fake.assert_called_with( URLquery, data= data, headers= HEADERS )

    def test_query( me):
        me.fake.return_value = 'f'
        me.db._response = lambda x,**ka: x
        query = me.db.query

        q_text = ' whatever text here '
        with me.subTest( 'text query'):
            query( q_text)
            #print(11111, me.fake.mock_calls)
            me.assert_call_data_eq(
                f'["^ ","~:query","{q_text}"]' )

        with me.subTest( 'text + valid_time_all'):
            query( q_text, valid_time_all= True)
            me.assert_call_data_eq(
                f'["^ ","~:query","{q_text}","~:default-all-valid-time?",true]' )

        with me.subTest( 'text + args'):
            query( q_text, args= dict( a= 1))
            me.assert_call_data_eq(
                f'["^ ","~:query","{q_text}","~:args",["^ ","~:a",1]]' )

        q_xtql = (Symbol( 'from'), Keyword( 'tbl'), [ Symbol( 'a') ] )
        q_ts = '["~#list",["~$from","~:tbl",["~$a"]]]'
        with me.subTest( 'xtql'):
            query( q_xtql)
            me.assert_call_data_eq(
                f'["^ ","~:query",{q_ts}]' )

        with me.subTest( 'xtql + after_tx'):
            query( q_xtql, after_tx= tk_obj)
            me.assert_call_data_eq(
                f'["^ ","~:query",{q_ts},"~:after-tx",{tk_ts}]' )

        with me.subTest( 'invalid query type/content'):
            with me.assertRaises( AssertionError):
                query( query= 123)
            with me.assertRaises( AssertionError):
                query( query= list( q_xtql))
            with me.assertRaises( AssertionError):
                query( query= dict( x=5) )
            # empty
            with me.assertRaises(TypeError):
                query()

        # unknown args
        with me.assertRaisesRegex( AssertionError, 'myarg'):
            query( q_xtql, myarg=4 )

if 0:
    def test_query_dict_inputs(me):
        me.fake.return_value = 'i'
        me.db._response = lambda x:x
        query = me.db.query
        qtxt = '{:query {:find [id] :where [[x :xt/id id]] :limit 1}}'
        q = qs.xtq().find( qs.sym.id
            ).where( qs.var_attr_value( qs.sym.x, me.db.id_kw, qs.sym.id)
            ).limit( 1)
        query( q, valid_time= me.datetime)
        #print(11111, me.fake.mock_calls)
        # ok
        me.fake.assert_called_once_with( URLquery, data= qtxt, headers= HEADERSedn, params= {'valid-time': me.datetext})

        query( q.copy().in_( qs.sym.x ), 23)
        qtxt2 = qtxt.replace( '}}', ' :in [x]} :in-args [23]}')
        me.fake.assert_called_with( URLquery, data= qtxt2, headers= HEADERSedn, params= {})

        with me.assertRaisesRegex( AssertionError, 'arg count mismatch'):
            query( q.copy().in_( qs.sym.y ))
        with me.assertRaisesRegex( AssertionError, 'arg count mismatch'):
            query( q, 12)


if __name__ == '__main__':
    unittest.main() #verbosity=2)

# vim:ts=4:sw=4:expandtab
