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
def is_backref_and_not_forward_ref( subschema):
    #return True #what?  #all become backrefs, i.e. using ForeignKey in subobj   XXX why?
    #not all.. see ./db-x2y.txt
    #m2o -> forward_ref
    #o2m -> backref (enforce the One)
    #o2o -> backref if component i.e. owned by parent ( more convenient, e.g. update a.b.c = 3 -> update b.c=3 where B._A_b==a.id )
    #m2m -> backref if indirect/via-submodel ; forward_ref if direct = list( id)
    if isinstance( subschema, schema.types.component): # and not subschema.embed and not subschema.flatten
        return True
    #( isinstance( subschema, schema.types.link)  #m2o, m2m
    return subschema.many and subschema.indirect #XXX

def is_multi( subschema):
    return subschema.many
def set_parent_link_backref( obj, subschema, parent):
    obj_set_attr( obj, subschema.name.backref, parent)     #XXX ?
def hide_forward_link( obj, subschema):
    obj_del_attr( obj, subschema.name)  #or mark it as non-saveable
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
            key = obj_key( o)
            if key in me:
                e = me[ key ]
                assert o is e.obj and level == e.level, (level, o, key, e)
            else:
                me[ key ] = me.objref( level=level, obj=o)
    def find( me, obj):
        return me.get( obj_key( o) )
    def sorted_values( me):
        return sorted( me.values(), key= lambda x: (x.level, obj_key( x.obj)) )
    def delete( me, obj):
        return me.pop( obj_key( o) )


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
            news = objset()
            while me.ins:
                current = me.ins.popany()
                level = current.level
                obj = current.obj
                results.add( level, obj)
                for subschema, subobj in walk_schema( obj):
                    if not is_link_or_component_non_composite( subschema):
                        continue
                    assert subobj
                    is_backref = is_backref_and_not_forward_ref( subschema )

                    if PREDEF_IDS:
                        newlevel = level   #XXX-1 levels are unneeded - IF the id's are predefined
                    else:
                        #topology-sort ??? forward_ref needs subobj-first, backref needs obj first
                        if is_backref: newlevel = level+1 # subobj-pointing-obj so subobj is after obj
                        else: newlevel = level-1 # obj-pointing-subobj so subobj is before obj

                    if is_backref:
                        # all subobj-pointing-obj
                        hide_forward_link( obj, subschema)
                        #parent_link = obj

                    subobjs = subobj if is_multi( subschema) else [ subobj ]
                    for sobj in subobjs:
                        if parent_link:
                            set_parent_link_backref( sobj, subschema, obj)
                        oldentry = results.find( sobj )
                        if oldentry:
                            assert oldentry.obj is sobj, (sobj, obj_key( sobj), oldentry)
                            if not PREDEF_IDS:
                                oldentry.level = min( oldentry.level, newlevel )
                        else:
                            news.add( newlevel, sobj)
            me.ins = news
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

#TODO tests.. seems needs TDD

####################

class unit_of_work2:
    'save together keeping constraints: unique + ref_integrity'
    def __init__( me):
        me.inputs = objset()
        #this will need obj_type also
        me.save = []
        #these will need obj_type but can be only id
        me.assert_exists = []
        me.assert_notexists = []

    def create_no_update( me, *objs):
        'unique - check inexisting beforehand'
        me.inputs.add( level= 'create', *objs)
    create_unique = create_inexisting = create_no_update

    def update_no_create( me, *objs):
        'ref integrity - check existing beforehand'
        me.inputs.add( level= 'update', *objs)
    update_existing = update_no_create

    def update_or_create( me, *objs):
        'no constraints'
        me.inputs.add( level= 'upsert', *objs)
    upsert = update_no_create

    #XXX ref integrity
    #def delete_and_cascade vs delete_no_cascade?? vs delete_and_set_null  XXX ??

    def build( me):
        '''
        PREDEF_IDS: levels/order does not matter as long as all needed objects are pulled in ;
        this is for adding, maybe updating ; but not deleting.. XXX
        - ??? global-above-obj_type constraints ????
        -Rc: for all create/_no_update: save + assert_notexists( all-uniq-keys-of-obj at least objid)
        -Ru: for all update/_no_create: save + assert_exists( objid)
        -Rs: for all update_or_create/upsert: just save
        -Rw: walk all sub/objs, collect all Links (forward_ref/FK)
        -Rl: for all links: assert_exists( Link)
        -Re: if link-obj is just-to-be-saved, assert_exists should be ignored
        -Rx: cannot have both assert_notexists and assert_exists for same obj
        '''
        assert me.inputs
        assert_notexists= {}
        assert_exists= {}
        for key, current in me.inputs.values():
            level = current.level
            obj = current.obj
            if level == 'create':   #Rc
                assert_notexists[ key] = obj
            elif level == 'update': #Ru
                assert_exists[ key] = obj
            elif level == 'upsert': #Rs
                pass
            else:
                assert 0, level

            #XXX Rw
            for subschema, subobj_or_many in walk_schema( obj):
                if not is_link_or_component_non_composite( subschema):
                    continue
                #XXX Rw
                is_backref = is_backref_and_not_forward_ref( subschema )
                if is_backref:
                    pass
                    # all subobj-pointing-obj
                    #hide_forward_link( obj, subschema)
                else:
                    #XXX Rl
                    subobjs = subobj_or_many if is_multi( subschema) else [ subobj_or_many ]
                    for sobj in subobjs:
                        assert sobj
                        assert_exists[ obj_key( sobj)] = sobj     #XXX is sobj THE id ???
                        #TODO and convert-to-just-id ???

        #XXX Rx these are mutually exclusive..
        both = set( assert_exists) & set( assert_notexists)
        assert not both, both

        for key, current in me.inputs.values():
            obj = current.obj
            #XXX Re assert-exists should be ignored if obj is just-to-be-saved - i.e. a->b & b->a
            assert_exists.pop( key, None)
            me.save.append( obj)
        me.assert_notexists = assert_notexists.values()
        me.assert_exists    = assert_exists.values()
        #me.asserts = dict( assert_exists= assert_exists, assert_notexists = assert_notexists)

# vim:ts=4:sw=4:expandtab
