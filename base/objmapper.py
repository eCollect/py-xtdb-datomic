#xtdb
from base.utils import dictAttr
from base.schema import AttrType, types, EnumType
from base.qsyntax import kw2
from base.qsyntax import Keyword

def normalize( struct_decl):
    'overwrite in place: materialize functors, initial checks, recursively'
    for k,vdecl in struct_decl.items():
        assert '__' not in k, f'cannot have __ inside names: {k}' #disallow to avoid duplicating p__x and p.x
        if callable( vdecl): vdecl = vdecl()
        assert isinstance( vdecl, AttrType), f'needs AttrType, got {type(vdecl)}: {k}'
        if vdecl.is_substruct:
            if isinstance( vdecl.typeorname, dict):
                normalize( vdecl.typeorname)
        struct_decl[ k ] = vdecl

def struct2flat( struct_decl):
    'flatten components if declared so, recursively?'
    r = dictAttr()
    for k,vdecl in struct_decl.items():
        assert isinstance( k, str), k
        assert k[0] != '_', k #f'cannot startwith _ names: {k}' #disallow as that is the backref'ing in pull
        assert '__' not in k, k #f'cannot have __ inside names: {k}' #disallow to avoid duplicating p__x and p.x
        assert isinstance( vdecl, AttrType), k #f'needs AttrType, got {type(vdecl)}: {k}'
        if vdecl.typename == 'component' and vdecl.flatten:
            assert not vdecl.many, (k,vdecl)
            r.update( (k+'__'+rk,rvdecl) for rk,rvdecl in struct2flat( vdecl.typeorname).items())
        else:
            r[ k ] = vdecl
    return r

# DELETED auto-pfx'ing lone-leafs, allows for subtle-landmine future-errors

class objmap:
    def __init__( me, typename, struct_decl):
        # a: { b: int }, c: int -> a,c=branches ; b,c=leafs
        me.typename = typename
        normalize( struct_decl)
        me.decl = struct_decl                                       #a.b   c        - branches
        me.decl_flat = struct2flat( struct_decl)    #no namespaces  #a__b  c - leafs
    @classmethod
    def build_maps( klas, sh):
        return dict( (oname, klas( oname, attrdecls)) for oname,attrdecls in sh.items())

    _db_id = ('xt','id')
    _db_id_required = True
    _db_id_allowed_types = ( str, int, types.uuid.type, )
    _db_id_generator = None     #functor() ; having this disallows manual id-assignment
    #_components_embedding_allowed = True    #XXX TODO disallow? separating?
    @classmethod
    def get_db_id( me, obj, _keyer =kw2):
        return obj[ _keyer( *me._db_id) ]
    @classmethod
    def check_db_id( me, dbid, showerr =None):
        if me._db_id_allowed_types:
            assert isinstance( dbid, me._db_id_allowed_types), showerr or dbid

    _enums = {}     #name:EnumType
    ENUM_AS_KEYWORD = False
    def make_obj( _me, *, _keyer =kw2, **attrs):
        'works for person = dict( names= .. ) and for person__names'
        #TODO convert enums ; relations + separating non-flattened-components ; auto-ID ?
        me = _me
        _oname = _me.typename
        r = {}

        #dbid
        dbid = attrs.pop( '_id', None)
        if _me._db_id_required:
            if _me._db_id_generator:
                assert not dbid, f'do not override auto _id in: {_oname}'
                dbid = _me._db_id_generator()
            assert dbid, f'required _id in: {_oname}'
        if dbid:
            me.check_db_id( dbid)
            r[ '_id' ] = dbid

        #branches pure only
        for k,decl in me.decl.items():
            if k in me.decl_flat: continue
            if k not in attrs:
                #assert not decl.required, 'required in: {_oname}: {k}'
                continue
            v = attrs.pop( k)
            if decl.typename == 'component' and decl.flatten:
                #flatten these for decl_flat to pick
                for rk,rv in v.items():     #dict ; nonrecursive ! XXX
                    nk = k+'__'+rk
                    assert nk not in attrs, f'duplicate2 in: {_oname}: {rk} {nk}'
                    attrs[ nk ] = rv    #TODO valuer( nk,rv, decl-of-substruct??)
            else:
                assert k not in r, f'duplicate3 in: {_oname}: {k}'     #XXX cant happen?
                r[ k] = me.valuer( k,v,decl)

        #all else
        for k,decl in me.decl_flat.items():
            if k not in attrs:
                #assert not decl.required, 'required in: {_oname}: {k}'
                continue
            assert k not in r, f'duplicate4 in: {_oname}: {k}'  #XXX cant happen ?
            v = attrs.pop( k)
            r[ k] = me.valuer( k,v,decl)

        assert not attrs, f'unknown in: {_oname}: {attrs}'

        r = objbase( r, typename= _oname, _db_id= _me._db_id, keyer= _keyer)
        return r


    def valuer( me, k,v,decl):
        if v is None:
            assert not decl.required, (k,decl)
            return v
        if not decl.many:
            return me._valuer_single( k,v,decl)
        assert isinstance( v, (list,tuple)), (k,v,decl)
        return [ me._valuer_single( k, vi, decl) for vi in v ]

    def _valuer_single( me, k,v,decl):
        if v is None:           # XXX should many allow None's ?
            #assert not decl.required, k
            return v

        if decl.typename == 'link':     #deref
            if isinstance( v, objbase):
                print( 'warn: linked obj is not autosaved:', k)
                return v._id
            if isinstance( v, dict):
                print( 'warn: linked obj is not autosaved:', k)
                return me.get_db_id( v, _keyer=_keyer)
            me.check_db_id( v, (k,v,decl))

        elif decl.typename == 'component':     #deref.. all same as link ; flatten will not come here
            assert not decl.flatten, (k,decl)
            if not decl.embed:
                if isinstance( v, objbase):
                    print( 'warn: linked obj-comp is not autosaved:', k)
                    return v._id
                if isinstance( v, dict):
                    print( 'warn: linked obj-comp is not autosaved:', k)
                    return me.get_db_id( v, _keyer=_keyer)
                me.check_db_id( v, (k,v,decl))
            #else embed: no checks/converts whatsoever

        elif decl.typename == 'enum':   #check values, convert
            if 0 and me._enums:     #abandon checks
                enumtype = me._enums.get( decl.typeorname )
                assert enumtype, (k, decl)
                if isinstance( v, Keyword):
                    namespace,name = v.name.split('/')
                    assert namespace == enumtype.__name__, (k,v,decl)
                    assert name in enumtype.__members__, (k,v,decl)
                    return v
                if isinstance( v, str):
                    assert v in enumtype.__members__, (k,v,decl)
                else:       #enum
                    assert v in enumtype, (k,v,decl)
                #convert-to-kw2
                return kw2( enumtype.__name__, v.name)

            if isinstance( v, EnumType):
                return me.enum2enum( v)
            if me.ENUM_AS_KEYWORD:
                assert isinstance( v, Keyword), (k,v,decl)
            else: #'enum is str=namespace/name'
                if isinstance( v, Keyword):
                    return v.name
                assert isinstance( v, str), (k,v,decl)

        else:
            return decl.check_type( v, k)
        return v

    @classmethod
    def enum2enum( klas, v):
        assert isinstance( v, EnumType), v
        if klas.ENUM_AS_KEYWORD:
            return kw2( v.__class__.__name__, v.name)
        return v.__class__.__name__ + '/'+ v.name

class objbase( dict):
    '''very primitive..
    >>> o = objbase( dict( a=2, b=3, _id=4), typename='ko')
    >>> o
    {Keyword(ko/a): 2, Keyword(ko/b): 3, Keyword(xt/id): 4}
    >>> isinstance( o, dict)
    True
    >>> o.a
    2
    >>> o._id
    4
    >>> o['a']
    Traceback (most recent call last):
    ...
    KeyError: 'a'
    >>> o[ kw2.ko.a]
    2
    >>> list( o )
    [Keyword(ko/a), Keyword(ko/b), Keyword(xt/id)]
    >>> list( o.items())
    [(Keyword(ko/a), 2), (Keyword(ko/b), 3), (Keyword(xt/id), 4)]
    >>> o.a = 3
    >>> o.a
    3
    >>> o.c
    Traceback (most recent call last):
    ...
    KeyError: 'c'
    >>> o.d = 8
    Traceback (most recent call last):
    ...
    KeyError: 'd'
    '''
    def __init__( me, kvdict, *, typename, _db_id =objmap._db_id, keyer =kw2, ):
        k2db = dict( (k, ( keyer( *_db_id) if k=='_id' else keyer( typename, k))) for k in kvdict)
        super().__init__( ( k2db[k], v) for k,v in kvdict.items())
        me._k2db = k2db
        #me._db2k = dict( (v,k) for k,v in k2db.items())
        #me._typename = typename _keyer _db_id ...
    def __getattr__( me, k):
        if k[0]=='_' and k!='_id': return super().__getattr__( k)
        return me.get( me._k2db[k])
    def __setattr__( me, k, v):
        if k[0]=='_' and k!='_id': super().__setattr__( k, v)
        else: me[ me._k2db[k] ] = v


if __name__ == '__main__':
    import doctest
    doctest.testmod()
# vim:ts=4:sw=4:expandtab
