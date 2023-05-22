from base import schema

def make_key( obj): return what?
def is_link_or_component_non_composite( subschema):
    return isinstance( subschema, schema.types.link) or isinstance( subschema, schema.types.component) and not subschema.embed #is_composite
def is_backref_or_forward_ref( subschema):
    return True #what?  #all become backrefs, i.e. using ForeignKey in subobj
def is_multi( subschema):
    return subschema.many
def set_parent_link_backref( obj, subschema, pointed):
    obj[ subschema.name ] = pointed
def del_forward_link( obj, subschema):
    del obj[ subschema.name ]
def walk_schema( obj):
    oschema = get_schema_by_obj_instance( obj)
    for subschema in oschema:
        yield subschema, obj.get( subschema.name)

##

class objset( dict):
    def add( me, level, *objs):
        for o in objs:
            me[ make_key( o) ] = dict( level=level, obj=o)

class unit_of_work:
    def __init__( me):
        me.ins = objset()
        me.results = objset()

    def add( me, *objs):
        'add-one-or-multiple-objects'
        me.ins.add( level=0, *objs)

    def build( me):
        '''
        if PREDEF_IDS, levels/order does not matter as long as all needed objects are pulled in
        else, this produces topology-levelled results ; smaller levels == earlier i.e. level: from before to after
        this is for adding, maybe updating ; but not deleting.. XXX
        '''
        PREDEF_IDS = True
        MAX_LOOPS = 30
        assert me.ins
        for count in range( MAX_LOOPS):
            if not me.ins: break
            ins = me.ins.copy()
            while ins:
                current = ins.popany()
                me.results.add( current['level'], current['obj'])
                for subobj, subschema in walk_schema( obj):
                    if not is_link_or_component_non_composite( subschema):
                        continue
                    is_backref = is_backref_or_forward_ref( subschema )

                    if PREDEF_IDS:
                        newlevel = level   #XXX-1 levels are unneeded - IF the id's are predefined
                    else:
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

                    sobjs = subobj if is_multi( subschema) else [ subobj ]
                    for so in sobjs:
                        if parent_link:
                            set_parent_link_backref( so, subschema, parent_link)
                        oldentry = me.results.get( key(so) )
                        if oldentry:
                            assert oldentry['obj'] is so, (so, key(so), oldentry)
                            if not PREDEF_IDS:
                                oldentry[ 'level'] = min( oldentry[ 'level'] , newlevel )
                        else:
                            me.ins.add( newlevel, so)
        else:   #no break
            assert 0, 'too many levels'

        if not PREDEF_IDS:
            me.results = sorted( me.results.values(), key= lambda x: x['level'],x['obj'] )
        else:
            me.results = list( me.results.values())
'''

https://stackoverflow.com/questions/6056683/practical-usage-of-the-unit-of-work-repository-patterns
https://stackoverflow.com/questions/67482155/what-are-standard-architectural-patterns-to-centrally-encapsulate-chain-of-orm-c
topology-sort ??? forward_ref needs subobj-first, backref needs obj first
'''


# vim:ts=4:sw=4:expandtab
