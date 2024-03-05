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
    def with_name( me, name):
        me.name = name
        return me

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
    '''link/substruct.. 2 aspects: representation and semantics
    - semantics: can/should child exist without parent
        - yes, independent - should/can be kept if parent is deleted
        - no, dependent - should be deleted if detached from parent or parent is deleted
    - representation:
        - independent: must be external/separate
            - the reference can be in parent, or in child, (or in intermediate?)
        - dependent:
            - inside parent (embeded) - can be also flattened, for db's which cannot search/index deep
            - external - all like independent except deletion/"ownership"
    '''
    class link( AttrType):
        '''many2one, ~many2many ; not own ; deleting parent should not delete the linked=child
        store refs to obj id's ; cannot be directly traversed back - linkeds do not know
        '''
        is_substruct = True
        is_forward   = True
        def __init__( me, typeorname, **ka):
            super().__init__( typeorname= typeorname, **ka)

    class component( AttrType):
        '''one2one, one2many ; own ; deleting parent should delete the linked
        flatten: convert into bunch-of-parent-attributes (only single/one2one, i.e. many=False), conflicts with embed
        embed: store whole inside parent (composite, substruct), conflicts with flatten
            xtdb1: any content/depth, not searchable/indexable
            xtdb2: any content/depth, searchable/indexable
            datomic: 1 level, up to 8 attributes, represented as tuple  TODO
        separate=default: store refs to obj id's, like link ; cannot be directly traversed back - linkeds do not know
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
    r = dictAttr( (k,v( name= k ) if callable( v) else v.with_name( k ) ) for k,v in ka.items())
    for k,v in r.items():
        assert isinstance( v, AttrType), k
    return r

t = s = types
# export: types, struct, EnumType, maybe AttrType
__all__ = '''
types t s struct EnumType AttrType
'''.split()

# vim:ts=4:sw=4:expandtab
