import edn_format   #??? should it be after pyrfc3339 hacking
# (clojure)edn

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


class EDNClientMixin:
    @staticmethod
    def datetime_param_converter( v):
        #v = v.isoformat( timespec= 'milliseconds')
        #v = edn_format.dumps( v)    #no need for urllib.parse.quote_plus here
        return v

    _app_edn  = 'application/edn'
    _headers_content_edn  = { 'content-type'  : _app_edn + '; charset=utf-8' }
    #_headers_base = {'accept': 'application/edn, text/plain'}    #text/html makes errors too fancy

    def _content( me, r, **ka):
        contentype = r.headers.get( 'content-type', '')
        if me._app_edn in contentype:
            return edn_format.loads( r.content)     #or r.text?
        return super()._content( r, **ka)

# vim:ts=4:sw=4:expandtab
