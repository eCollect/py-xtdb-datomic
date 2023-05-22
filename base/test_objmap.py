from base.schema import s, struct, dictAttr, EnumType
# isComponent -> auto-retrieve ? maybe

sh = dictAttr(
    entity = struct(
        id      = s.str( identity=True ),  #id : "893R3PQ0"
        country = s.enum( 'country_ISO'),

        #component 1 flattened
        person = s.component( struct(
            given_names= s.str,
            surname = s.str,
            gender  = s.enum( 'gender_type'),   #: m f x none/u
            date_of_birth   = s.datetime, # "1991-04-22" ISO-8601
            ), flatten= True),
        surname = s.str,            #same as person.surname XXX
        #component 1 not-flattened
        organisation = s.component( struct(
            name    = s.str,
            type    = s.str,
            ), flatten= False),

        #o2m, type=named-external
        addresses   = s.component( 'address', many= True),
        #m2o
        parent      = s.link( 'entity'),

        #should be many2many-with-metadata=rel.type; a->b -> rel-type ; b->a -> reverse( rel.type)
        #but currently is just ref-to+type, and no auto-reverses - other side is unrelated
        #m2m type=embedded ???
        relations   = s.link( struct(
            type = s.str,
            entity = s.link( 'entity'),
            ), many= True),
        #o2m, type=embedded
        metadata    = s.component( struct(
            type = s.str,
            value = s.str,
            ), many= True),     # non-system classification ?
        ),
    address = struct(
        lines   = s.str( many=True), #[ "VIA QUADRONNO 34" ] ,
        city    = s.str,    #"MILANO" ,
        country = s.enum( 'country_ISO'),
        valid   = s.bool,
        ),
    )

enums = dictAttr(
    country_ISO = EnumType( 'country', 'NZ DE BG AU'),
    gender_type = EnumType( 'gender',  'm f x'),
    )

from base import objmapper
ns = objmapper.kw2

objattr_maps = objmapper.objmap.build_maps( sh)
def make_obj( _oname, **attrs):
    return objattr_maps[ _oname ].make_obj( **attrs)

enumv = objmapper.objmap.enum2enum

import datetime
import unittest
from unittest.mock import patch

class t_make_obj( unittest.TestCase):
    maxDiff = None
    def test_whole_component_to_flatten_ok( me):
        me.assertEqual( dict(make_obj( 'entity', _id=1,
            id = 'uuid123',
            country= ns.country.BG,
            person= dict(
                gender= ns.gender.m,
                given_names= 'pen cho',
                surname=  'surnamev',
                date_of_birth=  datetime.date( 1999, 4, 14),
                ),
        )), {
            ns.entity.id: 'uuid123',
            ns.entity.person__date_of_birth: datetime.datetime(1999, 4, 14),
            ns.entity.person__gender: enumv( enums.gender_type.m),
            ns.entity.person__given_names: 'pen cho',
            ns.entity.person__surname: 'surnamev',
            ns.entity.country: enumv( enums.country_ISO.BG),
            ns.xt.id: 1
        })

    def test_component_parts_flattened_ok( me):
        me.assertEqual( dict(make_obj( 'entity', _id=1,
            id = 'uuid124',
            country= ns.country.BG,
            person__given_names= 'pen cho',
        )), {
            ns.xt.id: 1,
            ns.entity.id: 'uuid124',
            ns.entity.person__given_names: 'pen cho',
            ns.entity.country: enumv( enums.country_ISO.BG),
        })

    def test_mixed_whole_component_and_flattened_parts_ok( me): # - maybe ERR maybe OK
        me.assertEqual( make_obj( 'entity', _id=1,
            id = 'uuid125',
            person= dict( given_names= 'pen cho',),
            person__surname=  'surnamev',
        ), {
            ns.xt.id: 1,
            ns.entity.id: 'uuid125',
            ns.entity.person__given_names: 'pen cho',
            ns.entity.person__surname: 'surnamev',
        })

    def test_lone_leaf_auto_pfx_err( me):
        #auto_pfx is DISABLED
        with me.assertRaisesRegex( AssertionError, "unknown in: entity: {'given_names': 'pen cho'}"):
          make_obj( 'entity', _id=1,
            id = 'uuid127',
            given_names=  'pen cho',
            )
    def test_root_name_overtakes_same_lone_leaf_ok( me):
        me.assertEqual( make_obj( 'entity', _id=1,
            id = 'uuid127',
            person= dict( given_names= 'pen cho',),
            surname=  'surnamev2',
            ), {
            ns.xt.id: 1,
            ns.entity.id: 'uuid127',
            ns.entity.person__given_names: 'pen cho',
            ns.entity.surname: 'surnamev2',
        })
    def test_mixed_whole_component_and_flattened_parts_err_duplicate( me):
        with me.assertRaisesRegex( AssertionError, 'duplicate2 in: entity: surname person__surname'):
          make_obj( 'entity', _id=1,
            id = 'uuid126',
            person= dict( surname= 'surnamev',),
            person__surname=  'surnamev2',
            )
    def test_mixed_whole_component_and_lone_leaf_part_duplicate_ok( me):
        #with me.assertRaisesRegex( AssertionError, 'duplicate2 in: entity: surname person__surname'):
        me.assertEqual( make_obj( 'entity', _id=1,
            id = 'uuid127',
            person= dict( surname= 'surnamev',),
            surname=  'surnamev2',
            ), {
            ns.entity.id: 'uuid127',
            ns.entity.person__surname: 'surnamev',
            ns.entity.surname: 'surnamev2',
            ns.xt.id: 1
        })
    def test_mixed_flattened_part_and_lone_leaf_part_duplicate_ok( me):
        #auto_pfx is DISABLED, no more err with me.assertRaisesRegex( AssertionError, 'duplicate1 in: entity: surname person__surname'):
        me.assertEqual( make_obj( 'entity', _id=1,
            id = 'uuid128',
            person__surname=  'surnamev',
            surname=  'surnamev2',
            ), {
            ns.entity.id: 'uuid128',
            ns.entity.person__surname: 'surnamev',
            ns.entity.surname: 'surnamev2',
            ns.xt.id: 1
        })

    def test_unknown_attr_err( me):
        with me.assertRaisesRegex( AssertionError, "unknown in: entity: {'kuk': 2, 'pip': 3}"):
          make_obj( 'entity', _id=1,
                id = 'uuid123',
                kuk= 2,
                pip= 3
                )
    def test_unknown_component_attr_err( me):
        with me.assertRaisesRegex( AssertionError, "unknown in: entity: {'person__pu': 5}"):
            make_obj( 'entity', _id=1,
                id = 'uuid123',
                person = dict( surname = 'su',
                    pu = 5)
                )
        with me.assertRaisesRegex( AssertionError, "unknown in: entity: {'person__ku': 4}"):
            make_obj( 'entity', _id=1,
                id = 'uuid123',
                person__ku= 4,
                )
    def test_missing_dbid_err( me):
        with me.assertRaisesRegex( AssertionError, "required _id in: entity"):
            make_obj( 'entity',
                id = 'uuid123',
                country= ns.country.BG,
                )

    def test_schema_disallow__namespaced_like_names_err( me):
        sh1 = dict(
                mid = s.str( identity=True ),
                bag__color = s.str,
                )
        sh2 = struct( **sh1)

        with me.assertRaisesRegex( AssertionError, 'cannot have __ inside names: bag__color'):
            omap = objmapper.objmap( 'ent2', sh1)
        with me.assertRaisesRegex( AssertionError, 'cannot have __ inside names: bag__color'):
            omap = objmapper.objmap( 'ent1', sh2)

        sh3a= dict(
                mid = 'somet',
                ok = s.bool,
                )
        with me.assertRaisesRegex( AssertionError, "needs AttrType, got <class 'str'>: mid"):
            omap = objmapper.objmap( 'ent1', sh3a)
        sh3b= dict(
                midd = str,
                ok = s.int,
                )
        with me.assertRaisesRegex( AssertionError, "needs AttrType, got <class 'str'>: midd"):
            omap = objmapper.objmap( 'ent2', sh3b)

        with me.assertRaisesRegex( AssertionError, "^midd$"):
            sh3c= struct(
                midd = str,
                ok = s.bool,
                )
            #omap = objmapper.objmap( 'ent2', sh3c)

        sh4 = dict(
                idname = s.str,
                person = dict( surname = s.str),
                )
        with me.assertRaisesRegex( AssertionError, "needs AttrType, got <class 'dict'>: person"):
            omap = objmapper.objmap( 'ent1', sh4)

    @patch.object( objmapper.objmap, '_enums', enums)
    def test_enums( me):
        assert objmapper.objmap._enums, objmapper.objmap._enums
        assert objmapper.objmap._enums == enums
        me.assertEqual( make_obj( 'entity', _id=1,
            id = 'uuid124',
            country= ns.country.BG,
            person__given_names= 'pen cho',
        ), {
            ns.entity.id: 'uuid124',
            ns.entity.person__given_names: 'pen cho',
            ns.entity.country: enumv( enums.country_ISO.BG),
            ns.xt.id: 1
        })
        me.assertEqual( dict(make_obj( 'entity', _id=1,
            id = 'uuid124',
            country= enums.country_ISO.BG,
            person__given_names= 'pen cho',
        )), {
            ns.xt.id: 1,
            ns.entity.id: 'uuid124',
            ns.entity.person__given_names: 'pen cho',
            ns.entity.country: enumv( enums.country_ISO.BG),
        })


class t_naming( unittest.TestCase):
    maxDiff = None
    def setUp( me):
        me.sh = dict(
                id = s.str( identity = True),   #inst..str
                country = s.enum( 'country'),   #inst..enum
                valid = s.bool,                 #functor, same_name as in non-flat-comp
                surname = s.str,                #same_name as in flat-comp
                person = s.component( dict(     #flat comp, dict, inst
                    name = s.str(),             #inst..str
                    surname = s.str,            #functor, same_name as root-name
                    ), flatten= True),
                org = s.component( struct(      #flat comp,struct
                    name = s.str,               #same_name as in other flat-comp
                    tip  = s.str,               #same_name as in other non-flat-comp
                    ), flatten= True),
                rope= s.component( dict(        #non-flat comp
                    valid = s.bool,             #same_name as in root
                    tip  = s.str,               #same_name as in other flat-comp
                    count = s.int,              #lone-leaf but in non-flat comp
                    ) ),
                address = s.component( 'adr'),  #non-flat comp, typename-only, inst
                )

    def test_take_dict_of_funcs_ok( me):
        omap = objmapper.objmap( 'ent31', me.sh)

        me.assertEqual( omap.typename, 'ent31')
        if 0:   #DISABLED
          me.assertEqual( omap.ambigious_names, set([ 'name' ])) # and not surname or tip
          me.assertEqual( omap.lone_name2pfx, dict(
            gender= 'person',
            surname= 'person',
            tip = 'org',
            #and no valid, name, count
            ))

        from pprint import pformat
        me.assertEqual( pformat( omap.decl), '''\
{'address': component( typeorname=adr, flatten=False, embed=False ),
 'country': enum( typeorname=country ),
 'id': str( identity=True ),
 'org': component( typeorname={'name': str, 'tip': str}, flatten=True, embed=False ),
 'person': component( typeorname={'name': str, 'surname': str}, flatten=True, embed=False ),
 'rope': component( typeorname={'valid': bool, 'tip': str, 'count': int}, flatten=False, embed=False ),
 'surname': str,
 'valid': bool}''')
        me.assertEqual( pformat( omap.decl_flat), '''\
{'address': component( typeorname=adr, flatten=False, embed=False ),
 'country': enum( typeorname=country ),
 'id': str( identity=True ),
 'org__name': str,
 'org__tip': str,
 'person__name': str,
 'person__surname': str,
 'rope': component( typeorname={'valid': bool, 'tip': str, 'count': int}, flatten=False, embed=False ),
 'surname': str,
 'valid': bool}''')

#####################
#relation
'''
###########
+unknown attr =ERR
+unknown component-attr =ERR
+missing db_id at root =ERR
##missing something required =ERR
ambigious leafname =ERR
unambigious leafname =OK
'''
if __name__ == '__main__':
    unittest.main() #verbosity=2)

# vim:ts=4:sw=4:expandtab
