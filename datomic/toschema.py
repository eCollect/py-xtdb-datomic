from datomic import schema

def _doc4typeorname( d, pfx):
    return schema.doc( f'{pfx}{d.typeorname}' + (f' {d.doc}' if d.doc else ''))

def link( d, name):
    return [ schema.s.ref, _doc4typeorname( d, 'to:') ]
def component( d, name):
    assert not d.flatten, (name,d)
    return [ schema.s.ref, _doc4typeorname( d, 'of:'), schema.s.isComponent, ]   #isComponent: auto-pull/del-recursive
def enum( d, name):
    return [ schema.s.enum, _doc4typeorname( d, 'of enum:') ]
def UUID( d, name):
    return [ schema.s.uuid ]

types2da = dict( (f.__name__, f) for f in [ link, component, enum ])
with_docs = set( types2da)  #so far!
types2da.update( UUID = UUID)
for t in 'str int bool datetime'.split():
    typ = getattr( schema.s, t)
    types2da[ t ] = lambda *ignored, _typ=typ: [ _typ ]

_flags2da = dict( identity= 'ident', unique= 'uniq', uniq=0, ident=0, many=0, index=0, fulltext=0, )
def struct2recipe( struct_decl):
    'make datomic attr decls, flat'
    recipe = {}
    for k,vdecl in struct_decl.items():
        r = types2da[ vdecl.typename ]( vdecl, k)
        for vflag,daflag in _flags2da.items():
            if vdecl.get( vflag): r.append( getattr( schema.s, daflag or vflag))
        if vdecl.doc and vdecl.typename not in with_docs: r.append( schema.doc( vdecl.doc))
        recipe[ k ] = r
    return recipe

from base import objmapper
class objmap( objmapper.objmap):
    _db_id = ('db','id')
    _db_id_required = False
    _db_id_allowed_types = None #anything, if not actual int-entity-ids, deemed temporary
    ENUM_AS_KEYWORD = True

    @staticmethod
    def build_da_maps( o2a_maps):
        return dict( (k, struct2recipe( v.decl_flat )) for k,v in o2a_maps.items())
    @staticmethod
    def override_da_maps( obj2attrs, overrides):
        'in place!'
        for name,rc in overrides.items():
            oattr = obj2attrs[ name ]
            for k,v in rc.items():
                ov = oattr.pop( k)
                if isinstance( v, str): #rename
                    oattr[v] = ov
                elif isinstance( v, tuple):    #rename+replace
                    nk,nv = v
                    oattr[nk] = nv
                elif not v: #del
                    continue
                else:       #replace/add
                    #if isinstance( v, list):
                    oattr[k] = v

__all__ = '''
objmap
'''.split()

# vim:ts=4:sw=4:expandtab
