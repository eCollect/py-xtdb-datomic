from base import schema

class uow_accessor:
    #obj-stuff
    def obj_key( me, obj):
        return obj[ 'id' ] #what?
    def obj_get_attr( me, obj, name):
        return obj.get( name )
    def obj_set_attr( me, obj, name, value):
        obj[ name ] = value
    def obj_del_attr( me, obj, name):
        del obj[ name ]
    def obj_get_schema( me, obj):
        return 'schema-of-obj'

    #schema-stuff
    def subschema_is_link_or_component_non_composite( me, subschema):
        return (
            isinstance( subschema, schema.types.link) or
            isinstance( subschema, schema.types.component) and not subschema.embed and not subschema.flatten
            )
    def subschema_is_backref_and_not_forward_ref( me, subschema):
        #return True #what?  #all become backrefs, i.e. using ForeignKey in subobj   XXX why?
        #not all.. see ./db-x2y.txt
        #m2o -> forward_ref
        #o2m -> backref (enforce the One)
        #o2o -> backref if component i.e. owned by parent ( more convenient, e.g. update a.b.c = 3 -> update B.c=3 where B._A_b==a.id )
        #m2m -> backref if indirect/via-submodel ; forward_ref if direct = list( id)
        assert me.subschema_is_link_or_component_non_composite( subschema), subschema
        if isinstance( subschema, schema.types.component): # and not subschema.embed and not subschema.flatten
            return True
        #( isinstance( subschema, schema.types.link)  #m2o, m2m
        return subschema.many and subschema.indirect #XXX

    def subschema_is_multi( me, subschema):
        return subschema.many

    #obj-with-schema
    def obj_set_parent_link_backref( me, obj, subschema, parent):
        me.obj_set_attr( obj, subschema.name.backref, parent)     #XXX ?
    def obj_hide_forward_link( me, obj, subschema):
        me.obj_del_attr( obj, subschema.name)  #or mark it as non-saveable
    def obj_walk_schema( me, obj):
        oschema = me.obj_get_schema( obj)
        for subschema in oschema.values():
            yield subschema, me.obj_get_attr( obj, subschema.name)

##

class objset( dict):
    @staticmethod
    def accessor_obj_key( obj):     #override this
        raise NotImplemented

    class objref:
        def __init__( me, obj, level):
            me.obj = obj
            me.level = level

    def add( me, *objs, level):
        for o in objs:
            key = me.accessor_obj_key( o)
            if key in me:
                e = me[ key ]
                assert o is e.obj and level == e.level, ('duplicate:',level, o, key, e)
            else:
                me[ key ] = me.objref( level=level, obj=o)
    def find( me, obj):
        return me.get( me.accessor_obj_key( o) )
    def sorted_values( me):
        return sorted( me.values(), key= lambda x: (x.level, me.accessor_obj_key( x.obj)) )
    def delete( me, obj):
        return me.pop( me.accessor_obj_key( o) )


class unit_of_work:
    def __init__( me, accessor):
        me.accessor = accessor
        me.ins = me._objset()
        me.results = []
    def _objset( me):
        r = objset()
        r.accessor_obj_key = me.accessor.obj_key
        return r
    def add( me, *objs):
        'add-one-or-multiple-objects'
        me.ins.add( level=0, *objs)

    def build( me):
        '''
        if PREDEF_IDS, levels/order does not matter as long as all needed objects are pulled in ;
        else, this produces topology-levelled results ; smaller levels == earlier i.e. level: from before to after ;
        this is for adding, maybe updating ; but not deleting.. XXX
        '''
        accessor = me.accessor
        results = me._objset()
        PREDEF_IDS = True
        MAX_LOOPS = 30
        assert me.ins
        for count in range( MAX_LOOPS):
            if not me.ins: break
            news = me._objset()
            while me.ins:
                current = me.ins.popany()
                level = current.level
                obj = current.obj
                results.add( level, obj)
                for subschema, subobj in accessor.obj_walk_schema( obj):
                    if not accessor.subschema_is_link_or_component_non_composite( subschema):
                        continue
                    assert subobj
                    is_backref = accessor.subschema_is_backref_and_not_forward_ref( subschema )

                    if PREDEF_IDS:
                        newlevel = level   #XXX-1 levels are unneeded - IF the id's are predefined
                    else:
                        #topology-sort ??? forward_ref needs subobj-first, backref needs obj first
                        if is_backref: newlevel = level+1 # subobj-pointing-obj so subobj is after obj
                        else: newlevel = level-1 # obj-pointing-subobj so subobj is before obj

                    if is_backref:
                        # all subobj-pointing-obj
                        accessor.obj_hide_forward_link( obj, subschema)
                        #parent_link = obj

                    subobjs = subobj if accessor.subschema_is_multi( subschema) else [ subobj ]
                    for sobj in subobjs:
                        if parent_link:
                            accessor.obj_set_parent_link_backref( sobj, subschema, obj)
                        oldentry = results.find( sobj )
                        if oldentry:
                            assert oldentry.obj is sobj, (sobj, accessor.obj_key( sobj), oldentry)
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
    def __init__( me, accessor):
        me.accessor = accessor
        me.inputs = objset()
        me.inputs.accessor_obj_key = accessor.obj_key
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
    upsert = put = update_no_create

    #XXX ref integrity
    #def delete_and_cascade vs delete_no_cascade?? vs delete_and_set_null  XXX ??

    def build( me):
        '''
        this is for adding, maybe updating ; but not deleting.. XXX/TODO
        - ??? global-above-obj_type constraints ????
        -Rc: for all create/_no_update: save + assert_notexists( all-uniq-keys-of-obj at least objid)
        -Ru: for all update/_no_create: save + assert_exists( objid)
        -Rs: for all update_or_create/upsert: just save
        -Rw: walk all sub/objs, collect all Links (forward_ref/FK)
        -Rl: for all links: assert_exists( Link)
        -Re: if link-obj is just-to-be-saved, assert_exists should be ignored
        -Rx: cannot have both assert_notexists and assert_exists for same obj
        '''
        accessor = me.accessor
        assert me.inputs
        assert_notexists= {}
        assert_exists= {}
        for key, current in me.inputs.items():
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
            for subschema, subobj_or_many in accessor.obj_walk_schema( obj):
                if not accessor.subschema_is_link_or_component_non_composite( subschema):
                    continue
                #XXX Rw
                is_backref = accessor.subschema_is_backref_and_not_forward_ref( subschema )
                if is_backref:
                    pass
                    # all subobj-pointing-obj
                    #accessor.obj_hide_forward_link( obj, subschema)
                else:
                    #XXX Rl
                    subobjs = ()
                    if accessor.subschema_is_multi( subschema): subobjs = subobj_or_many
                    elif subobj_or_many: subobjs = [ subobj_or_many ]
                    for sobj in subobjs:
                        assert sobj, (obj,subschema)
                        assert_exists[ accessor.obj_key( sobj)] = sobj     #XXX is sobj THE id ???
                        #TODO and convert-to-just-id ???


        for key, current in me.inputs.items():
            obj = current.obj
            me.save.append( obj)
            #XXX Re assert-exists should be ignored if obj is just-to-be-created-or-saved - i.e. a->b & b->a
            if current.level != 'update':
                assert_exists.pop( key, None)

        #XXX Rx these are mutually exclusive - but after ignoring just-to-be-saved
        both = set( assert_exists) & set( assert_notexists)
        assert not both, both

        me.assert_notexists = assert_notexists #.values()
        me.assert_exists    = assert_exists #.values()
        #me.asserts = dict( assert_exists= assert_exists, assert_notexists = assert_notexists)

if __name__ == '__main__':
    import unittest
    class a( unittest.TestCase):
        def setUp( me):
            t = schema.t
            aschema = schema.dictAttr(
                aobj = schema.struct(
                        id = t.str( identity=True),
                        a = t.int,
                ))
            me.accessor = uow_accessor()
            me.accessor.obj_get_schema = lambda obj: aschema[ 'aobj' ]

        def test_123( me):
            u = unit_of_work2( me.accessor)
            a= dict( id=1, a=5)
            b= dict( id=2, a=6)
            c= dict( id=3, a=7)
            u.create_no_update( a)
            u.update_no_create( b)
            u.update_or_create( c)
            u.build()
            #print( f'{u.save=}')
            #print( f'{u.assert_notexists=}')
            #print( f'{u.assert_exists=}')
            me.assertEqual( u.save, [ a,b,c])                           #Rc Ru Rs
            me.assertEqual( list( u.assert_notexists.values()), [ a])   #Rc
            me.assertEqual( list( u.assert_exists.values()),    [ b])   #Re over Ru

        def test_add_twice( me):
            a= dict( id=1, a=5)
            b= dict( id=2, a=6)
            a2= dict( a, a=77)
            kinds = 'create_no_update update_no_create update_or_create'.split()
            for kind in kinds:
                u = unit_of_work2( me.accessor)
                getattr( u, kind)( a)

                with me.subTest( f'{kind=}, same id, same kind, same obj = ok'):
                    getattr( u, kind)( a)
                with me.subTest( f'{kind=}, same id, same kind, different obj = err'):
                    with me.assertRaisesRegex( AssertionError, 'duplicate:'):
                        getattr( u, kind)( a2)

                for okind in kinds:
                    if okind != kind:
                        with me.subTest( f'{kind=}, same id, other {okind=} = err'):
                            with me.assertRaisesRegex( AssertionError, 'duplicate:'):
                                getattr( u, okind)( a)

                for okind in kinds:
                    with me.subTest( f'{kind=}, other id, any {okind=} = ok'):
                        u2 = unit_of_work2( me.accessor)
                        getattr( u2, kind )( a)
                        getattr( u2, okind)( b)



    class b( unittest.TestCase):
        def setUp( me):
            t = schema.t
            aschema = schema.dictAttr(
                aleaf= schema.struct(
                        id = t.str( identity=True),
                        type = t.str,
                        a = t.int,
                        ),
                branch= schema.struct(
                        id = t.str( identity=True),
                        type = t.str,
                        b = t.int,
                        alink_1 = t.link( 'aleaf' ),                #m2o
                        alink_m = t.link( 'aleaf', many=True ),     #m2m,direct/forward
                        acomp_1 = t.component( 'aleaf'),
                        acomp_m = t.component( 'aleaf', many=True ),
                        acomp_1e= t.component( 'aleaf', embed=True),
                        acomp_me= t.component( 'aleaf', embed=True, many=True),
                        acomp_1f= t.component( 'aleaf', flatten=True),
                        ),
                croot= schema.struct(
                        id = t.str( identity=1),
                        type = t.str,
                        alink_1 = t.link( 'aleaf'),
                        blink_1 = t.link( 'branch'),
                        ),
                )
            me.accessor = uow_accessor()
            me.accessor.obj_get_schema = lambda obj: aschema[ obj[ 'type'] ]
            me.aleaf  = lambda **ka: dict( ka, type='aleaf',  id=1000+ka['id'])
            me.branch = lambda **ka: dict( ka, type='branch', id=2000+ka['id'])
            me.croot  = lambda **ka: dict( ka, type='croot',  id=3000+ka['id'])

            me.a1 = a1 = me.aleaf( id=11, a=1)
            me.a2 = a2 = me.aleaf( id=12, a=2)
            me.a3 = a3 = me.aleaf( id=13, a=3)
            me.a4 = a4 = me.aleaf( id=14, a=4)
            me.a5 = a5 = me.aleaf( id=14, a=5)

            me.b_link_0 = me.branch( id=11, b=1)
            me.b_link_1 = me.branch( id=12, b=2, alink_1= a1)
            me.b_link_m1= me.branch( id=13, b=3, alink_m= [a2])
            me.b_link_m2= me.branch( id=14, b=4, alink_m= [a2,a3])
            me.b_comp_1 = me.branch( id=15, b=5, alink_m= a4)
            me.b_comp_m = me.branch( id=16, b=6, acomp_m= [a4,a5])
            me.b_comp_1e= me.branch( id=17, b=7, alink_1e= a4)
            me.b_comp_me= me.branch( id=18, b=8, acomp_me= [a4,a5])
            me.b_comp_1f= me.branch( id=19, b=9, acomp_1f= a5)

            me.croot_a = me.croot( id=1, alink_1= a1)
            me.croot_b = me.croot( id=2, blink_1= me.b_link_m2)
            me.croot_ab= me.croot( id=3, alink_1= a1, blink_1= me.b_link_m2)

        def test_1( me):
            u = unit_of_work2( me.accessor)
            u.create_no_update( me.a1)
            u.create_no_update( me.a2)
            u.create_no_update( me.b_link_0)
            u.create_no_update( me.b_link_1)
            u.create_no_update( me.b_link_m1)
            u.create_no_update( me.b_link_m2)
            u.create_no_update( me.croot_a)
            u.create_no_update( me.croot_b)
            u.create_no_update( me.croot_ab)
            u.build()

            print( f'{u.save=}')
            print( f'{u.assert_notexists=}')
            print( f'{u.assert_exists=}')
            #me.assertEqual( u.save, [ a,b,c])                           #Rc Ru Rs
            #me.assertEqual( list( u.assert_notexists.values()), [ a])   #Rc
            #me.assertEqual( list( u.assert_exists.values()),    [ b])   #Re over Ru
            #TODO

        ##def link -> assert_exists (Rl)
        #TODO def obj-with-links -> assert_exists( all-links) (Rl,Rw)
        #TODO def obj-with-alink+links + alink as update_no_create -> same/ assert_exists( alink+links) (Rl,Rw,Re,Rx)
        #TODO def obj-with-alink+links + alink as create_no_update -> assert_not_exists( alink) assert_exists( links) (Rl,Rw,Re,Rx)
        #TODO def obj-with-alink+links + alink as update_or_create -> same/ assert_not_exists( alink) assert_exists( -links) (Rl,Rw,Re,Rx)


    unittest.main( verbosity=2)

# vim:ts=4:sw=4:expandtab
