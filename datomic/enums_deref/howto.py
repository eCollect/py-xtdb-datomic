'''
* put needed funcs in e.g. myns.clj
## e.g. (ns myns) (defn get_dbident [x] (get x :db/ident))
* list needed funcs in resources/datomic/extensions.edn under :xforms
## e.g.		{:xforms [ myns/xform1 myns/get_dbident ]}
* copy (not symlink) resources/datomic/extensions.edn to ../datomic-pro-1.0.6527/resources/datomic/extensions.edn
* copy (not symlink) myns.clj to ../datomic-pro-1.0.6527/samples/clj/
  or put its path into env DATOMIC_EXT_CLASSPATH ( used by bin/classpath , used by bin/rest-server)
#restart rest - pkill etc

for subdirs - my/ns.clj , use . instead of / in namespace:
* my/ns.clj - contains
*   (ns my.ns) (defn get_dbident [x] (get x :db/ident))
* resources/extensions contains:
*   {:xforms [ my.ns/get_dbident ]}

===========

enums made via db/ident... ok but always need deref

https://docs.datomic.com/on-prem/query/pull.html#xform
https://ask.datomic.com/index.php/606/recommended-way-to-handle-db-ident-enums-when-used-with-pull
https://clojurians-log.clojureverse.org/datomic/2021-04-14
https://forum.datomic.com/t/pull-xform-extensions/1525/3

'''
import base.qsyntax as qs

def deref_enum_attrs( objname, enum_attrs):
    'give this as *args to pull ; can be pre-generated once per objname'
    return [{ (qs.kw2( objname, k), qs.kw.xform, qs.sym('myns/get_dbident')) : [ qs.kw2.db.ident ]} for k in enum_attrs ]    #deref all enums

###### try find all enums - from shema variants
#print( [k for k,v in astory.sh.entity.items() if v.type =='enum'])  #this misses the flattened components
def get_enum_attrs( objname, obj2attrs):   #including flattened components
    from datomic import schema
    return [ k for k,v in obj2attrs[ objname ].items()
            if schema.types.enum in v and len(v)==2 and v[1].get( schema.ns_db.doc, '').startswith( 'of enum:')     #OMG XXX
            ]
def all_deref_enums( obj2attrs):   #including flattened components
    return dict( (oname, deref_enum_attrs( oname, get_enum_attrs( oname, obj2attrs))) for oname in obj2attrs)

if 0:   #plain - one
    q2 = daq().find( pull( var.eid,
                { (qs.kw2.entity.territory, qs.kw.xform, qs.sym('myns/get_dbident')) : [ qs.kw2.db.ident ]},
                whole=True) # which by default pulls only {:dbid ..} for refs
            ).in_( var.eid)
    db.query( q2, entid )

if 0:   #all enums: root + one relation
    deref_enums = all_deref_enums( obj2attrs)
    q3 = daq().find( pull( var.eid,
                *deref_enums['entity'],     #for root entity
                { qs.kw2.entity.address: [ qs.sym_wild, *deref_enums['address'] ]},  #for .address
                whole=True) # which by default pulls only {:dbid ..} for refs
            ) #...

# vim:ts=4:sw=4:expandtab
