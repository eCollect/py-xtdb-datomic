import datetime
from pprint import pformat
import requests, urllib
import edn_format   #??? should it be after pyrfc3339 hacking
'''
base of client for RPC via http and (clojure)edn/json
'''

class hacks:

    @staticmethod
    def edn_accept_naive_datetimes():
        import functools
        import pyrfc3339.generator
        _generate = pyrfc3339.generator.generate
        @functools.wraps( _generate)
        def generate( *a,**ka):
            return _generate( *a,**dict( ka, accept_naive= True))
        pyrfc3339.generator.generate = pyrfc3339.generate = generate

    @staticmethod
    def keyword_into_str( k):
        return str(k) if isinstance( k, edn_format.Keyword) else k
    @staticmethod
    def kebab2camel( path, skip_first_level =False):
        return '/'.join(
                ''.join( ((x.capitalize() or '_') if i else x)
                    for i,x in enumerate( level.split('-')))
                for level in path.split('/')[ bool( skip_first_level):]
                )
        #weird testcases: https://stackoverflow.com/questions/4303492/how-can-i-simplify-this-conversion-from-underscore-to-camelcase-in-python

    @classmethod
    def edn_response_Keyword_into_str( me, *, maps_keys =True, maps_values =False, lists =False, keyword_into_str =keyword_into_str.__func__):
        #keyword_into_str = me.keyword_into_str if not kebab2camel else me.keyword_into_str_kebab2camel
        if maps_keys or maps_values:
            me.edn_response_dicts_Keyword_into_str( maps_keys, maps_values, keyword_into_str)
        if lists:
            me.edn_response_lists_Keyword_into_str( keyword_into_str)
    @classmethod
    def edn_response_dicts_Keyword_into_str( me, maps_keys =True, maps_values =False, keyword_into_str =keyword_into_str.__func__):
        from edn_format.immutable_dict import ImmutableDict
        ImmutableDict.__setitem__ = None    #XXX why is it there ?
        k_convert = keyword_into_str if maps_keys else lambda x:x
        v_convert = keyword_into_str if maps_values else lambda x:x
        def _init_( me, dct):
            if isinstance( dct, (dict,ImmutableDict)): dct = dct.items()
            me.dict = dict( (k_convert(k),v_convert(v)) for k,v in dct)
            me.hash = None
        ImmutableDict.__init__ = _init_
    @classmethod
    def edn_response_lists_Keyword_into_str( me, keyword_into_str =keyword_into_str.__func__):
        from edn_format.immutable_list import ImmutableList
        def _init_( me, lst, copy =True):
            me._list = [ keyword_into_str(x) for x in lst] if copy else lst
            me._hash = None
        ImmutableList.__init__ = _init_

    @staticmethod
    def pprint_fix_immmutables():
        import pprint
        from edn_format.immutable_dict import ImmutableDict
        from edn_format.immutable_list import ImmutableList
        #see svdt_util/dicts.fix_pprint_dict
        pprint.PrettyPrinter._dispatch[ ImmutableDict.__repr__] = pprint.PrettyPrinter._dispatch[ dict.__repr__]
        pprint.PrettyPrinter._dispatch[ ImmutableList.__repr__] = pprint.PrettyPrinter._dispatch[ list.__repr__]
        #also safe_repr?


def dict_without_None( kv):
    return dict( (k,v) for k,v in kv.items() if v is not None)

def log( f, *a,**ka):
    print( f.__name__, a,ka, '====')
    r = f( *a,**ka)
    print( ' ', pformat( r))
    return r


class BaseClient:
    #params validators

    @staticmethod
    def is_int( x):
        assert isinstance( x, int), x
        return x
    @staticmethod
    def may_int( x):
        assert x is None or isinstance( x, int), x
        return x
    @staticmethod
    def may_int_positive( x):
        assert x is None or isinstance( x, int) and x>0, x
        return x
    @staticmethod
    def is_bool( x):
        assert isinstance( x, bool), x
        return x
    @staticmethod
    def may_bool( x):
        assert x is None or isinstance( x, bool), x
        return x

    @staticmethod
    def is_time( x):
        assert isinstance( x, datetime.datetime), x
        return x
    @staticmethod
    def may_time( x):
        assert x is None or isinstance( x, datetime.datetime), x
        return x

    @staticmethod
    def datetime_param_converter( v):
        #v = v.isoformat( timespec= 'milliseconds')
        #v = edn_format.dumps( v)    #no need for urllib.parse.quote_plus here
        return v

    @staticmethod
    def _params_taker( ka, **params_decl):
        return dict( (k,checker( ka.pop( k,None))) for k,checker in params_decl.items())
    @staticmethod
    def _check_unknown_params( unknowns):
        assert not unknowns, f'unknown params: {unknowns}'

    @classmethod
    def _params_cleaner( me, params, autoconvert =True):
        r = {}
        for k,v in params.items():
            if v is None: continue
            if autoconvert:
                if isinstance( v, bool):
                    v = str(v).lower()
                elif isinstance( v, datetime.datetime):
                    v = me.datetime_param_converter( v)
            r[ k.replace('_','-') ] = v
        return r
    @classmethod
    def _params( me, **params):
        return dict( params= me._params_cleaner( params))

    ######

    #_headers_base = {'Accept': 'application/edn, text/plain'}    #text/html makes errors too fancy
    _headers_base = {
        #"content-type": "application/json",
        #"accept": "application/json"
        }
    _app_edn  = 'application/edn'
    _app_json = 'application/json'
    _headers_content_edn  = { 'content-type'  : _app_edn }
    _headers_content_json = { 'content-type'  : _app_json }

    def __init__( me, rooturl, headers ={}):
        me.rooturl = rooturl.rstrip('/')
        me.headers = headers
    def _headers( me, headers ={}):
        h = dict( me._headers_base)
        h.update( me.headers)
        h.update( headers)
        #print( 5555555, h)
        return dict( headers= h)

    @staticmethod
    def _url_join( *url_levels, end_slash =False ):
        end = '/' if end_slash else ''
        return '/'.join(
                [('' if x == '/' else x)
                    for x in url_levels
                    if x]
                )+end
    def url( me, *url_levels, end_slash =False ):
        return me._url_join( me.rooturl, *url_levels, end_slash= end_slash)

    @staticmethod
    def _pretty_req( r):
        rqurl = r.request.url
        #print( rqurl)
        purl = urllib.parse.urlparse( rqurl)._asdict()
        query = purl.pop( 'query', '')
        if query:
            params_l = urllib.parse.parse_qsl( query, strict_parsing= True, keep_blank_values= True)
            params = dict( params_l)
            assert len( params) == len( params_l), f'duplicate keys? {(params_l, query)}'
            purl['params'] = params
        purl.update(
            headers = dict( r.request.headers),
            url     = rqurl,
            method  = r.request.method,
            status_code = r.status_code,
            )
        purl.pop( 'netloc', '')
        purl.pop( 'scheme', '')
        if r.request.body:
            body = r.request.body
            if 'application/x-www-form-urlencoded' in r.request.headers.get( 'content-type','').lower():
                body = urllib.parse.unquote_plus( body)
            purl[ 'body'] = body
        return purl
        #pp_rqurl = pformat( purl)

    def _content( me, r, **ka_ignore):
        contentype = r.headers.get( 'content-type', '')
        if me._app_json in contentype:
            return r.json()
        if me._app_edn in contentype:
            return edn_format.loads( r.content)     #or r.text?

    debug = False
    def _response( me, r, **ka):
        raw = r.content
        cooked = me._content( r, **ka)
        if me.debug:
            purl = me._pretty_req( r)
            print( pformat( purl))
            print( r, r.headers, f'{raw=} {cooked=}')
        if r.ok: #status_code in (200, *extra_ok_statuses):
            #accept = r.request.headers[ 'accept']
            return cooked if cooked is not None else raw

        purl = me._pretty_req( r)
        pp_rqurl = pformat( purl)
        err = RuntimeError( f'{r.status_code}: {r.text} ; \n {pp_rqurl}', )
        err.response = r
        raise err

    def _get( me, url, *, headers ={}, ka_response ={}, **ka):
        r = requests.get( me.url( url), **me._headers( headers), **ka)
        return me._response( r, **ka_response)
    def _post( me, url, *, data, headers ={}, ka_response ={}, **ka):
        r = requests.post( me.url( url), data= data, **me._headers( headers), **ka)
        return me._response( r, **ka_response)

# vim:ts=4:sw=4:expandtab
