from base import schema

def obj_key( obj):
    return what?
def obj_get_attr( obj, name):
    return obj.get( name )
def obj_set_attr( obj, name, value):
    obj[ name ] = value
def obj_del_attr( obj, name):
    del obj[ name ]

def is_link_or_component_non_composite( subschema):
    return (
        isinstance( subschema, schema.types.link) or
        isinstance( subschema, schema.types.component) and not subschema.embed and not subschema.flatten
        )
def is_backref_or_forward_ref( subschema):
    return True #what?  #all become backrefs, i.e. using ForeignKey in subobj   XXX why?
def is_multi( subschema):
    return subschema.many
def set_parent_link_backref( obj, subschema, pointed):
    obj_set_attr( obj, subschema.name, pointed)     #XXX ?
def del_forward_link( obj, subschema):
    obj_del_attr( obj, subschema.name)
def walk_schema( obj):
    oschema = get_schema_by_obj_instance( obj)
    for subschema in oschema:
        yield subschema, obj_get_attr( obj, subschema.name)

##

from dataclasses import dataclass

class objset( dict):
    @dataclass
    class objref:
        level: int
        obj: object

    def add( me, level, *objs):
        for o in objs:
            me[ obj_key( o) ] = me.objref( level=level, obj=o)
    def find( me, obj):
        return me.get( obj_key( o) )
    def sorted_values( me):
        return sorted( me.values(), key= lambda x: (x.level, obj_key( x.obj)) )


class unit_of_work:
    def __init__( me):
        me.ins = objset()
        me.results = []

    def add( me, *objs):
        'add-one-or-multiple-objects'
        me.ins.add( level=0, *objs)

    def build( me):
        '''
        if PREDEF_IDS, levels/order does not matter as long as all needed objects are pulled in ;
        else, this produces topology-levelled results ; smaller levels == earlier i.e. level: from before to after ;
        this is for adding, maybe updating ; but not deleting.. XXX
        '''
        results = objset()
        PREDEF_IDS = True
        MAX_LOOPS = 30
        assert me.ins
        for count in range( MAX_LOOPS):
            if not me.ins: break
            ins = me.ins.copy()
            while ins:
                current = ins.popany()
                level = current.level
                obj = current.obj
                results.add( level, obj)
                for subschema, subobj in walk_schema( obj):
                    if not is_link_or_component_non_composite( subschema):
                        continue
                    assert subobj
                    is_backref = is_backref_or_forward_ref( subschema )

                    if PREDEF_IDS:
                        newlevel = level   #XXX-1 levels are unneeded - IF the id's are predefined
                    else:
                        #topology-sort ??? forward_ref needs subobj-first, backref needs obj first
                        if is_backref: newlevel = level+1 # subobj-pointing-obj so subobj is after obj
                        else: newlevel = level-1 # obj-pointing-subobj so subobj is before obj

                    if is_backref:
                        # all subobj-pointing-obj
                        del_forward_link( obj, subschema)
                        parent_link = obj
                    else:
                        # obj-pointing-all-subobj
                        parent_link = None
                        pass

                    subobjs = subobj if is_multi( subschema) else [ subobj ]
                    for so in subobjs:
                        if parent_link:
                            set_parent_link_backref( so, subschema, parent_link)
                        oldentry = results.find( so )
                        if oldentry:
                            assert oldentry.obj is so, (so, obj_key( so), oldentry)
                            if not PREDEF_IDS:
                                oldentry.level = min( oldentry.level, newlevel )
                        else:
                            me.ins.add( newlevel, so)
        else:   #no break
            assert 0, 'too many levels'

        if not PREDEF_IDS:
            me.results = results.sorted_values()
        else:
            me.results = list( results.values())
'''

https://stackoverflow.com/questions/6056683/practical-usage-of-the-unit-of-work-repository-patterns
https://stackoverflow.com/questions/67482155/what-are-standard-architectural-patterns-to-centrally-encapsulate-chain-of-orm-c
topology-sort ??? forward_ref needs subobj-first, backref needs obj first
'''
#TODO check  graphlib.TopologicalSorter - since v3.9

    def build2( me):
        assert me.ins


#TODO tests.. seems needs TDD

# vim:ts=4:sw=4:expandtab
