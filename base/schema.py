from base.utils import dictAttr, strEnum

class AttrType( dictAttr):
    _flags_false = 'many required  identity unique'.split()
    _defaults = dict( dict.fromkeys( _flags_false, False), doc =None, )

    type = None
    is_substruct = False
    def __init__( me, type =None, **ka):
        super().__init__( me._defaults, **ka)
        me.type = type or me.type or me.__class__.__name__
        assert me.type != 'AttrType', me.type   #weak
    @property
    def typename( me):
        return me.type if isinstance( me.type, str) else me.type.__name__
    def check_type( me, v, name):
        assert me.type, (name, me.typename)
        assert not isinstance( me.type, str), (name, me.typename)
        assert isinstance( v, me.type), (name,v)
        return v
    def __str__( me):
        args = ', '.join( f'{k}={v}' for k,v in me.items()
            if k != 'type' and (k not in me._defaults or v != me._defaults[ k])
            )
        if args: args = '( '+args +' )'
        return me.typename + args
    __repr__ = __str__

if 0: #abandon, x.doc/x.unique is set-up in __init__
    #flags as methods
  def doc( me, t):
        me.doc = t
        return me
  for k in AttrType._flags_false:
    assert not hasattr( AttrType, k), k
    setattr( AttrType, k, lambda me, *, _k=k: (setattr( me, _k, True),me)[-1] )


import datetime, uuid

class types:
    class link( AttrType):
        '''many2one, ~many2many ; not own ; deleting this should not delete the linked
        store refs to obj id's ; cannot be traversed back - linkeds do not know
        '''
        is_substruct = True
        def __init__( me, typeorname, **ka):
            super().__init__( typeorname= typeorname, **ka)

    class component( AttrType):
        '''one2one, one2many ; own ; deleting this should delete the linked
        flatten: convert into bunch-of-parent-attributes (only single, i.e. many=False)
        embed: store whole inside parent (composite)
            xtdb: any content/depth, not searchable/indexable
            datomic: 1 level, up to 8 attributes, represented as tuple  TODO
        default: store refs to obj id's, like link ; cannot be traversed back - linkeds do not know
        only one of above 3, no combinations
        '''
        is_substruct = True
        def __init__( me, typeorname, *, flatten =False, embed =False, **ka):
            super().__init__( typeorname= typeorname, flatten= flatten, embed= embed, **ka)
            if me.flatten: assert not me.many, me
            assert not (me.flatten and me.embed), me

    class enum( AttrType):
        def __init__( me, typeorname, **ka):
            super().__init__( typeorname= typeorname, **ka)
            #keywords as ns.what.item ; or strs e_{what}__{item}

    class str( AttrType):  type = str
    class int( AttrType):  type = int
    class bool( AttrType): type = bool

    class float( AttrType):
        type = float
        def check_type( me, v, name):
            assert isinstance( v, (int,float)), (name,v)
            return float(v)     #convert

    class datetime( AttrType):
        type = datetime.datetime
        def check_type( me, v, name):
            if isinstance( v, datetime.date):   #convert
                return datetime.datetime.combine( v, datetime.time(0,0))
            return super().check_type( v, name)

    class uuid( AttrType): type = uuid.UUID

    #aliases
    ref = link
    text = str

EnumType = strEnum

def struct( **ka):
    r = dictAttr( (k,v() if callable( v) else v) for k,v in ka.items())
    for k,v in r.items():
        assert isinstance( v, AttrType), k
    return r

s = types
# export: types, struct, EnumType, maybe AttrType
__all__ = '''
types s struct EnumType AttrType
'''.split()

# vim:ts=4:sw=4:expandtab
