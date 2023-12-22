#this time, xtdb - document-centric
'''see ./todo
'''
import edn_format
edn_format.Keyword.__repr__ = edn_format.Keyword.__str__
#edn_format.Keyword.__hash__ = lambda me: hash( str(me))
edn_format.Keyword.__lt__ = lambda s,o: str(s)<str(o)

from base import astory, objmapper
from base.utils import dictAttr
from pprint import pprint, pformat
from base.qsyntax import kw2 as ns

enums = astory.enums
objattr_maps = objmapper.objmap.build_maps( astory.sh)
#pprint( objattr_maps)

AS_JSON = False

_keyer_cfg = {}
def key2json( nspc,name): return nspc+'/'+name
if AS_JSON: _keyer_cfg = dict( _keyer= key2json)

def make_obj( _oname, **attrs):
    return objattr_maps[ _oname].make_obj( **_keyer_cfg, **attrs)
#def db__id( x):
#    return objmapper.objmap.get_db_id( x, _keyer=key2json)

#create/update
import datetime

ac1 = make_obj( 'account',
        id= 'acc1',     #what if exists?
        name= 'acco1u',
        _id = 23,    #required =works
        )
e1 = make_obj( 'entity',
        id = 'uuid123',
        country_of_residence= enums.country_ISO3166.BG,
        territory= enums.territory_system.BG,
        person= dict(
            gender= enums.gender_type.m,
            given_names= 'pen cho',
            surname=  'surnamev',
            date_of_birth=  datetime.date( year=1999, day=14, month=4),
            ),
        account= ac1,   #TODO copied-as-is - ok for components but not for relations
        _id=12,
        )
pprint( ac1)
pprint( e1)

if 10:
 e1x= make_obj( 'entity',
        id = 'uuid124',
        territory= enums.territory_system.BG,
        person__given_names= 'pen cho',
        _id=13
        )
 pprint( e1x)

#1/0

adr1 = make_obj( 'address',
        country= enums.country_ISO3166.BG,
        lines=   [ 'lin1', 'lin 2.x' ],
        city=    'neidesi',
        primary= True,
        _id=14
        )
pho2 = make_obj( 'contact',
        country= enums.country_ISO3166.BG,
        type=    enums.contact_type.phone,
        value=   '33445566',
        confirmed= False,
        primary= True,
        _id=15
        )
ema3 = make_obj( 'contact',
        type=    enums.contact_type.email,
        value=   'em@ail.to',
        confirmed= True,
        _id=16
        )
e1upd1= make_obj( 'entity',   #XXX #update/add-substuff
        _id = 'e1', #None,   # needs db__id = some-entity1.dbid
        addresses= [ 'p2adr1' ],
        contacts = [ 'p2pho2', 'p2ema3' ],
        )
e1upd2= make_obj( 'entity',   #XXX #update/add-substuff
        _id = 'e1', #None,   # needs db__id = some-entity1.dbid
        relations= [ dict( type= enums.relation_type.is_sibling_of_sibling, entity1='e2') ], #XXX
        )
adr2 = make_obj( 'address',
        country= enums.country_ISO3166.NZ,
        lines=   [ 'lin5', 'lin3' ],
        city=    'tam',
        primary= True,
        _id=17
        )
e2 = make_obj( 'entity',
        id = 'uuid234',
        country_of_residence= enums.country_ISO3166.NZ,
        territory= enums.territory_system.ROW,
        person__gender= enums.gender_type.m,
        person__given_names= 'cho pen',
        person__surname=  'muzevv',
        person__date_of_birth=  datetime.date( year=1990, day=24, month=2),
        account= 'p2ac1',
        contacts = [ 'p2ema3' ],
        relations= [ dict( type= enums.relation_type.is_sibling_of_sibling, entity1='e1') ],
        _id=18
        )

#1/0

if 1:
    from xtdb.dbclient import xtdb, log, edn_dumps
    import os
    URL = os.getenv( 'XTDB') or 'http://localhost:3001'
    db = xtdb( URL)

#XXX enums .. nothing special db-wise. texts as usual.
# - maybe make a tool to findout all data in db that is supposed to be enum, and compare it to (current) code
# - maybe generate some clj funcs for schema-on-write checks, for each enum-field

if 1:
    from xtdb.qsyntax import xtq, var, sym, pull, var_attr_value

    if 10: #get all client-accounts, and get their pointed-by entities
        qacc = xtq().find(
            pull( var.accid, ns.account.id,
                ns.entity._account,    #v1a , backref
                #{ ns.entity._account: [ qs.sym_wild, ns.person.surname ] }     #v1b
                whole=True
                )
            ).where(
                var_attr_value( var.accid, ns.account.id),
            )
    if 10: #get some entity under some account
        qent1 = xtq().find(
            pull( var.entid, db.id_kw, ns.entity.id, ns.entity.is_organisation, ns.entity.country_of_residence),
            pull( var.accid),
            ).where(
                var_attr_value( var.entid, ns.entity.account, var.accid),
            )

    if 10: #get some entity under some account
        qentid = xtq().find(
            pull( var.inid, whole=True)
            ).in_( var.inid
            )


#TODO pull recursive ref-docs ?

    def run( q, pfx='', limit =3, **ka):
        print( pfx, ':', edn_dumps( q), ka)
        r = db.query( q, limit= limit, **ka)
        pprint( r)
        return r
    #db.debug = 1
    log( db.save, ac1, as_json= AS_JSON)
    log( db.sync)
    run( qacc)
    pprint( ac1)
    #e1.account = db__id(ac1)
    e1.account = ac1._id
    pprint( e1)
    #/0
    log( db.save, e1, as_json= AS_JSON)
    log( db.sync)   #without this, below query may miss it

    r = run( qent1, 'uuid123' )
    entid = r[0][0][ str( db.id_name) ]
    if 0*'part2-update-add-addr1':
        fetch = db.entity
        ent = fetch( entid)
        ent.address += ( objs2.adr2, objs2.adr1 )
        log( db.save, ent, as_json= AS_JSON)

    pprint( db.entity( entid))
    pprint( db.query( qentid, entid ))

'''
PLAIN ATTRS: text numeric datetime bool enum
attr-features: nullable many (ordered?)  is_identity  auto-fill?
constraints: unique indexable?

in testdb.history.test_create:
t1  add ent1 = bunch-of-attrs at-once .name=x etc but no age
    get-whole-ent1          -> ent1 with all attrs but no age
    get-just-ent1.name      -> ent1.name
    get-id-of-entities-which-have-name=x    -> ent1.id    #i.e. search separate-with-characteristics
    get-id-of-entities-which-have-name=y    -> none       #i.e. search separate-with-characteristics
    get-whole-entities-which-have-name=x    -> ent1       #i.e. search separate-with-characteristics
    get-whole-entities-which-have-age       -> none       #i.e. search separate-with-characteristics
    get-whole-entities-which-have-age=None  -> ??none     #i.e. search separate-with-characteristics
    get-whole-entities-which-have-age > 3   -> none       #i.e. search separate-with-characteristics
    get-whole-entities-which-have-age < 3   -> none       #i.e. search separate-with-characteristics
    get history of ent1     -> 1 entry
t2  change/replace ent1.name=y
    get-id-of-entities-which-have-name=x    -> none       #i.e. search separate-with-characteristics
    get-id-of-entities-which-have-name=y    -> ent1.id    #i.e. search separate-with-characteristics
    get history of ent1     -> 2 entry
t3  change=add ent1.age=5
    get-whole-entities-which-have-age       -> ent1       #i.e. search separate-with-characteristics
    get-whole-entities-which-have-age > 3   -> ent1       #i.e. search separate-with-characteristics
    get-whole-entities-which-have-age < 3   -> none       #i.e. search separate-with-characteristics
    get history of ent1     -> 3 entries
t4  change=del ent1.something
    get-whole-ent1          -> ent1 without that something
    get history of ent1     -> 4 entries

    query as-of in time:
        as-of-t1=before-t2
            get-id-of-entities-which-have-name=x    -> as-of-t1
            get-id-of-entities-which-have-name=y    -> as-of-t1
            get-id-of-entities-which-have-age...
        as-of-t2=before-t3-after-t2
            get-id-of-entities-which-have-name=x    -> as-of-t2
            get-id-of-entities-which-have-name=y    -> as-of-t2
            get-id-of-entities-which-have-age...

    query in time: before t4 ; before t1 ?????


RELATIONS: ref=link=pointer
features: many: o2o-o2m-m2o-m2m  separate/component/composite
#separate/component/composite-features:
#   -       +       +   auto-retrieve/delete with parent
#   +       +       -   change-independently-of-parent
#   +       +       -   search-independently-of-parent: find component-with-characteristics
#   -       -       +   change-only-via-parent
#   -       -       +   inside-parent-history
#   +       +       -   parent-searchable: find-parent-which-has-component-with-characteristics
#   -       -       +   o2o
#   +       +       +   o2m
#   +       +       -   m2o
#   ~       ~       -   m2m

#XXX seems anything searchable needs be separate , and only marked as "component", for auto-retrieve/delete-with-parent etc
#   mongo can index/search on inner stuff ; xtdb does not ; datomic has all separated
# history: therefore = history of entity + histories of all components-mentioned-anywhere-and-anytime

t0  add account=acc1
t1  add ent1 of .account=acc1
    get-whole-ent1           -> ent1 , no addr etc + .account=just-id
    get-whole-ent1-with-account -> ent1 + .account= whole
    get-id-of-entities-of-acc1  -> ent1.id   #i.e. search who-points-at a separate
    get-whole-entities-of-acc1  -> ent1
    get-id-of-entities-which-have-account=acc1 -> ent1.id    #i.e. search who-points-at separate-with-characteristics
t2  add adr1 to ent1.addresses
    get-whole-ent1           -> ent1 with adr1
    get-id-of-entities-which-have-address.city=cy1 -> ent1.id    #i.e. search who-points-at component-with-characteristics
t3  add adr2 to ent1.addresses
    +add pho2 to ent1.contacts
    get-whole-ent1           -> ent1 with adr1,adr2,pho2
    get-whole-entities-which-have-phone -> ent1
    get-whole-entities-which-have-email -> none
    get-id-of-entities-which-have-phone.valid   -> ent1.id    #i.e. search who-points-at component-with-characteristics
t4  del adr1 from ent1.addresses
    get-whole-ent1           -> ent1 with adr2,pho2
t5  add ema3 to ent1.contacts
    +del pho2 from ent1.contacts
    get-whole-ent1           -> ent1 with adr2,ema3
    get-whole-entities-which-have-phone -> none
    get-whole-entities-which-have-email -> ent1

    get history of ent1 -> manualy! including components and excluding separates
'''


# vim:ts=4:sw=4:expandtab
