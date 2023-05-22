import edn_format
edn_format.Keyword.__repr__ = edn_format.Keyword.__str__
#edn_format.Keyword.__hash__ = lambda me: hash( str(me))
edn_format.Keyword.__lt__ = lambda s,o: str(s)<str(o)

from datomic.toschema import objmap as objmap2
from datomic import schema
#usage

from pprint import pprint
from base.utils import dictAttr

from base import astory
o2a_maps = objmap2.build_maps( astory.sh)
def make_obj( _oname, **attrs):
    return o2a_maps[ _oname ].make_obj( **attrs)

obj2attrs = objmap2.build_da_maps( o2a_maps)
#pprint( obj2attrs)
#print( '====='*6)

overrides = dict(
    entity = dict(
        relations= [ schema.tuple_many_types( schema.s.enum, schema.s.ref), schema.s.many, schema.doc( 'of enum=relation_type, ref=entity') ],
        metadata = [ schema.tuple_many_types( schema.s.enum, schema.s.str), schema.s.many, schema.doc( 'of enum=metadata_customer_types, value') ],     # non-system classification ?
    ))
objmap2.override_da_maps( obj2attrs, overrides)
pprint( obj2attrs)

sh1c = schema.cook( obj2attrs)   # -> list of dict-per-item
schema.check( sh1c)
#sh1c.sort( key= lambda x: x[ ns_db.ident] )
#pprint( sh1c)

import datetime
ns = schema.ns

if 10:
    pprint( make_obj( 'entity',
            id = 'uuid123',
            country_of_residence= ns.country.BG,
            territory= ns.territory.BG,
            person__gender= ns.gender.m,
            person__given_names= 'pen cho',
            person__surname=  'surnamev',
            person__date_of_birth=  datetime.date( year=1999, day=14, month=4),
            account= 'p2ac1',   #tmp-name for inside this tx
            ))

if 1:
    #create/update
    objs2 = dictAttr(
        e1 = make_obj( 'entity',
            id = 'uuid123',
            country_of_residence= ns.country.BG,
            territory= ns.territory.BG,
            person__gender= ns.gender.m,
            person__given_names= 'pen cho',
            person__surname=  'surnamev',
            person__date_of_birth=  datetime.date( year=1999, day=14, month=4),
            account= 'p2ac1',   #tmp-name for inside this tx
            ),
        ac1 = make_obj( 'account',
            _id= 'p2ac1',
            id= 'acc1',     #what if exists?
            ),
        e1b = make_obj( 'entity',   #XXX #update/add-substuff
            _id =None,   # needs _id = some-entity1.dbid
            addresses= [ 'p2adr1' ],
            contacts= [ 'p2pho2', 'p2ema3' ],
            relations= [ ns.relation_type.is_sibling_of_sibling, 'p2e2' ],
            ),
        adr1 = make_obj( 'address',
            _id= 'p2adr1',
            country= ns.country.BG,
            lines=   [ 'lin1', 'lin 2.x' ],
            city=    'neidesi',
            primary= True,
            ),
        adr2 = make_obj( 'address',
            _id= 'p2adr2',
            country= ns.country.NZ,
            lines=   [ 'lin5', 'lin3' ],
            city=    'tam',
            primary= True,
            ),
        pho2 = make_obj( 'contact',
            _id= 'p2pho2',
            country= ns.country.BG,
            type=    ns.contact_type.phone,
            value=   '33445566',
            confirmed= False,
            primary= True,
            ),
        ema3 = make_obj( 'contact',
            _id= 'p2ema3',
            type=    ns.contact_type.email,
            value=   'em@ail.to',
            confirmed= True,
            ),
        e2 = make_obj( 'entity',
            _id= 'p2e2',
            id = 'uuid234',
            country_of_residence= ns.country.NZ,
            territory= ns.territory.ROW,
            person__gender= ns.gender.m,
            person__given_names= 'cho pen',
            person__surname=  'muzevv',
            person__date_of_birth=  datetime.date( year=1990, day=24, month=2),
            account= 'p2ac1',
            contacts= [ 'p2ema3' ],
            relations= [ ns.relation_type.is_sibling_of_sibling, 'p2e1' ],
            ),
        )

    pprint( objs2.e1b)

if 0:
    from datomic.dbclient import Datomic, log, edn_dumps
    from datomic.qsyntax import daq, var, sym, pull, eav
    from datomic import qsyntax as qs
    db = Datomic( 'http://localhost:8992', 'devv', 'cdbname')
    def query( q, pfx='', limit =3, **ka):
        print( pfx, ':', edn_dumps( q), ka)
        r = db.query( q, limit= limit, **ka)
        pprint( r)
        return r

    log( db.create_db)
    if 0:
        log( db.save, sh1c )
        #get-things-with-valueType
        query( daq().find( pull( var.x) ).where(
                eav( var.x, ns.db.valueType),
        ) , 'shema', limit=10)

    #for e in astory.enums.country_ISO3166: print(e)
    if 0:   #save enums
        for etype in astory.enums.values():
            evalues = schema.make_enum( etype.__name__, *etype.__members__) # (e.name for e in etype))
            #evalues = schema.make_enum( etype._name, *etype._items)    own EnumType
            log( db.save, evalues)

    def get_enums_ie_what_has_dbident_not_starting_with_db_and_has_no_dbvaluetype( q):
        return q.find( pull( var.x) ).where(
                    eav( var.x, ns.db.ident, var.idt),
                    qs.notall( qs.orany(
                        qs.andall( qs.pred_startswith( var.idt, ':db'), qs.noop( var.x) ),
                        qs.andall( eav( var.x, ns.db.valueType), qs.noop( var.idt)),
                    )))
    if 0:
        query( get_enums_ie_what_has_dbident_not_starting_with_db_and_has_no_dbvaluetype( daq()
                ) , 'enums', limit=120)

    if 0*'part1':
        log( db.save, [ objs2.e1, objs2.ac1] )
    def get_all_accounts_with_entities_pointing_them( q):
        return q.find(
                pull( var.acc, #ns.account.id,
                    #ns.entity._account     #v1a
                    { ns.entity._account: [ qs.sym_wild ] } ,# ns.person.surname ] }     #v1b
                    whole=True
                    )
                ).where(
                    eav( var.acc, ns.account.id),
                )
    if 0: query( get_all_accounts_with_entities_pointing_them( daq()), 'qacc')

    def get_all_entities_with_account_they_point_to( q, *pullargs, entid =None):
        return q.find(
                pull( var.ent,
                    { ns.entity.account: [ qs.sym_wild ]},    #v1a
                    #{ (ns.entity.territory, qs.kw.xform, qs.sym('myns/get_dbident')) : [ ns.db.ident ]},   #deref territory enum
                    *pullargs,
                    whole=True,
                    )
                ).where(
                    eav( var.ent, ns.entity.id, *((entid,) if entid else ())),
                )
    if 0: r = query( get_all_entities_with_account_they_point_to( daq()), 'qent')

    if 10:   #deref all enums
        #print( [k for k,v in astory.sh.entity.items() if v.type =='enum'])  #this misses the flattened components
        from datomic.enums_deref import howto as denums
        #entity_enums = get_enum_attrs( 'entity')
        #print( f'{entity_enums=}')
        #deref_entity_enums= [{ (ns.entity( k), qs.kw.xform, qs.sym('myns/get_dbident')) : [ ns.db.ident ]} for k in entity_enums ]    #deref all enums
        deref_enums = denums.all_deref_enums( obj2attrs)
    if 0: r = query( get_all_entities_with_account_they_point_to( daq(), *deref_enums['entity']), 'qent-deref')

    if 10*'part2-update-add-addr1':
        if 0:
            #entid = r[0][0][ db.id_kw ]
            entid = 'uuid123'
            addrs = [ objs2.adr2, objs2.adr1 ]
            log( db.save, [
                make_obj( 'entity',
                    _id= entid,
                    address= [ o[ db.id_kw ] for o in addrs]
                ), *addrs ])
        query( get_all_entities_with_account_they_point_to( daq(),
                *deref_enums['entity'],
                { ns.entity.address: [ qs.sym_wild, *deref_enums['address'] ]}
                ), 'qent-deref2')

        def test_get_all_entities_deref():
            '''
            >>> x=query( get_all_entities_with_account_they_point_to( daq(), \
                    *deref_enums['entity'], \
                    { ns.entity.address: [ qs.sym_wild, *deref_enums['address'] ]},  \
                    entid='uuid123', ), 'qent', limit=1)  # doctest: +REPORT_UDIFF +ELLIPSIS
            qent : {:find [(pull ?ent [* {:entity/account [*]} {(:entity/person__gender :xform myns/get_dbident) [:db/ident]} {(:entity/person__nationality :xform myns/get_dbident) [:db/ident]} {(:entity/country_of_residence :xform myns/get_dbident) [:db/ident]} {(:entity/territory :xform myns/get_dbident) [:db/ident]} {:entity/address [* {(:address/country :xform myns/get_dbident) [:db/ident]} {(:address/type :xform myns/get_dbident) [:db/ident]}]}])] :where [[?ent :entity/id "uuid123"]]} {}
            [[{':db/id': ...,
               ':entity/account': {':db/id': ..., ':account/id': 'acc1'},
               ':entity/address': [{':address/city': 'tam',
                                    ':address/country': :country/NZ,
                                    ':address/lines': ['lin3', 'lin5'],
                                    ':address/primary': True,
                                    ':db/id': ...},
                                   {':address/city': 'neidesi',
                                    ':address/country': :country/BG,
                                    ':address/lines': ['lin 2.x', 'lin1'],
                                    ':address/primary': True,
                                    ':db/id': ...}],
               ':entity/country_of_residence': :country/BG,
               ':entity/id': 'uuid123',
               ':entity/person__date_of_birth': datetime.datetime(1999, 4, 14, 0, 0, tzinfo=<UTC>),
               ':entity/person__gender': :gender/m,
               ':entity/person__given_names': 'pen cho',
               ':entity/person__surname': 'surnamev',
               ':entity/territory': :territory/BG}]]
            '''
            pass
    def test_get_all_entities():
        '''
        >>> x=query( get_all_entities_with_account_they_point_to( daq(), entid='uuid123', ), 'qent', limit=1)  # doctest: +REPORT_UDIFF +ELLIPSIS
        qent : {:find [(pull ?ent [* {:entity/account [*]}])] :where [[?ent :entity/id "uuid123"]]} {}
        [[{':db/id': ...,
           ':entity/account': {':db/id': ..., ':account/id': 'acc1'},
           ':entity/address': [{':address/city': 'tam',
                                ':address/country': {':db/id': ...},
                                ':address/lines': ['lin3', 'lin5'],
                                ':address/primary': True,
                                ':db/id': ...},
                               {':address/city': 'neidesi',
                                ':address/country': {':db/id': ...},
                                ':address/lines': ['lin 2.x', 'lin1'],
                                ':address/primary': True,
                                ':db/id': ...}],
           ':entity/country_of_residence': {':db/id': ...},
           ':entity/id': 'uuid123',
           ':entity/person__date_of_birth': datetime.datetime(1999, 4, 14, 0, 0, tzinfo=<UTC>),
           ':entity/person__gender': {':db/id': ...},
           ':entity/person__given_names': 'pen cho',
           ':entity/person__surname': 'surnamev',
           ':entity/territory': {':db/id': ...}}]]
        '''
        pass

    import doctest
    doctest.testmod()

# vim:ts=4:sw=4:expandtab
