import edn_format
import base.qsyntax as qs
ns = qs.kw2         #namespaced keyword
ns1 = qs.kw         #not-namespaced keyword
ns_db = db = ns.db
ns_db_type = db_type = ns( 'db.type')

class _func2attr:
    def __init__( me, func): me.func = func
    def __getattr__( me, k):
        if k[:2]=='__': return me.__getattribute__( k)
        return me.func( k)

# ~/.local/lib/python3.10/site-packages/datomic/schema.py
# gns24_pydatomic/pydatomic/schema.py
# https://docs.datomic.com/on-prem/schema/schema-modeling.html
# https://docs.datomic.com/on-prem/schema/identity.html
# https://docs.datomic.com/on-prem/schema/schema.html
_valueTypes = dict(
    str     = 'string',
    bool    = 'boolean',
    int     = 'long',
    float   = 'double',     #skip the float itself XXX
    bigint  = 'bigint',     #7N
    decimal = 'bigdec',     #7.2M
    datetime= 'instant',    #milliseconds since epoch/1970.1.1
    )
_valueTypes.update( (v,v) for v in list(_valueTypes.values()))
_valueTypes.update( (k,k) for k in dict(
    bytes   = None,
    uri     = None,
    uuid    = None,
    keyword = None,
    ref     = None,     # reference to another entity
    symbol  = None,
    tuple   = None,     # of scalar values
    ))
_valueTypes.update(
    enum    = 'ref',        # aliased
    )
db_type._translator = _valueTypes
def _valueType( k):
    '''
    >>> _valueType( 'str')
    {Keyword(db/valueType): Keyword(db.type/string)}
    >>> t.str
    {Keyword(db/valueType): Keyword(db.type/string)}
    >>> qs.edn_dumps( t.str)
    '{:db/valueType :db.type/string}'
    '''
    return { db.valueType: db_type( k) } #_valueTypes[k]) } in db_type._translator above
types = t = _func2attr( _valueType)

''' on .many:
value -> set i.e. unordered XXX
 add value= item -> add-item-to-set
 add value= sequence -> add items of sequence to set
again: order is lost !
'''

_options = dict(
    unique  = 'unique/value',
    identity= 'unique/identity',
    many    = 'cardinality/many',
    one     = 'cardinality/one',
    )
_options.update(
    uniq    = _options['unique'],
    ident   = _options['identity'],
    )
def _option( k):
    '''
    >>> _option( 'one')
    {Keyword(db/cardinality): Keyword(db.cardinality/one)}
    >>> o.one
    {Keyword(db/cardinality): Keyword(db.cardinality/one)}
    >>> qs.edn_dumps( o.one)
    '{:db/cardinality :db.cardinality/one}'
    '''
    opt = _options[ k]
    o_ns, o_name = opt.split('/')
    return { db( o_ns): ns( 'db.'+o_ns, o_name) }
options = o = _func2attr( _option)

_flags = dict( (k,k) for k in dict(
    index       =None,
    fulltext    =None,
    isComponent =None,  # https://docs.datomic.com/on-prem/schema/schema.html#component
    noHistory   =None
    ))
def _flag( k):
    '''
    >>> _flag('index')
    {Keyword(db/index): True}
    >>> f.index
    {Keyword(db/index): True}
    >>> qs.edn_dumps( f.index)
    '{:db/index true}'
    '''
    return { db( _flags[k]): True }
flags = f = _func2attr( _flag)
#TODO combine o+f
#TODO combine o+f+t
_combined = {}
_combined.update( (k,_flag(k)) for k in _flags)
_combined.update( (k,_option(k)) for k in _options)
_combined.update( (k,_valueType(k)) for k in _valueTypes)
s = combined = _func2attr( _combined.__getitem__)

def make_enum( name, *items):
    ''' ;;https://docs.datomic.com/on-prem/schema/schema-modeling.html#enums
    >>> make_enum( 'names', 'a', 'bb')
    [{Keyword(db/ident): Keyword(names/a)}, {Keyword(db/ident): Keyword(names/bb)}]
    >>> qs.edn_dumps( make_enum( 'names', 'a', 'bb'))
    '[{:db/ident :names/a} {:db/ident :names/bb}]'
    '''
    if len( items) == 1: items = items[0].split()
    assert items
    return [ { db.ident: ns( name,i) } for i in items ]
#type.enum = ref .. hope/eventualy pointing to some of above

#tuple.. 2..8 scalars
_scalar_types4tuple = set( db_type( v) for v in set( _valueTypes.values()) - set(['tuple', 'bytes']) )

def tuple_composite( *attrs):
    ''' https://docs.datomic.com/on-prem/schema/schema.html#composite-tuples
    derived from other attributes of the same entity
    >>> tuple_composite( ns.a.b, ns.c.d )
    {Keyword(db/valueType): Keyword(db.type/tuple), Keyword(db/tupleAttrs): [Keyword(a/b), Keyword(c/d)]}
    >>> qs.edn_dumps( tuple_composite( ns.a.b, ns.c.d ))
    '{:db/valueType :db.type/tuple :db/tupleAttrs [:a/b :c/d]}'
    '''
    assert 2<= len( attrs) <= 8, attrs
    return types.tuple | { db.tupleAttrs: list( attrs) }

def tuple_same_type( type):
    ''' https://docs.datomic.com/on-prem/schema/schema.html#homogeneous-tuples
    >>> db_type.string
    Keyword(db.type/string)
    >>> db_type.str
    Keyword(db.type/string)

    >>> tuple_same_type( db_type.str )
    {Keyword(db/valueType): Keyword(db.type/tuple), Keyword(db/tupleType): Keyword(db.type/string)}
    >>> qs.edn_dumps( tuple_same_type( db_type.str ))
    '{:db/valueType :db.type/tuple :db/tupleType :db.type/string}'
    '''
    assert type in _scalar_types4tuple, type
    return types.tuple | { db.tupleType: type }

def tuple_many_types( *ttypes):
    ''' https://docs.datomic.com/on-prem/schema/schema.html#heterogeneous-tuples
    >>> tuple_many_types( db_type.int, db_type.str )
    {Keyword(db/valueType): Keyword(db.type/tuple), Keyword(db/tupleTypes): [Keyword(db.type/long), Keyword(db.type/string)]}
    >>> qs.edn_dumps( tuple_many_types( db_type.int, db_type.str ))
    '{:db/valueType :db.type/tuple :db/tupleTypes [:db.type/long :db.type/string]}'
    >>> tuple_many_types( t.int, t.str )
    {Keyword(db/valueType): Keyword(db.type/tuple), Keyword(db/tupleTypes): [Keyword(db.type/long), Keyword(db.type/string)]}
    '''
    assert 2<= len( ttypes) <= 8, ttypes
    ttypes = [ x[ db.valueType ] if isinstance( x, dict) else x for x in ttypes ]
    assert all( t in _scalar_types4tuple for t in ttypes), ttypes
    return types.tuple | { db.tupleTypes: list( ttypes) }

def doc( text):
    ''' https://docs.datomic.com/on-prem/best-practices.html#annotate-schema
    >>> doc( 'sometxt')
    {Keyword(db/doc): 'sometxt'}
    >>> qs.edn_dumps( doc( 'sometxt'))
    '{:db/doc "sometxt"}'
    '''
    assert isinstance( text, str) and text, text
    return { db.doc: text }

#XXX aliases: done, see dbclient.Datomic.make_tx_add_alias
# https://docs.datomic.com/on-prem/best-practices.html#use-aliases

#TODO
# https://docs.datomic.com/on-prem/schema/schema.html#entity-specs - attr-required-ness , cross-fact-constraints
# https://docs.datomic.com/on-prem/schema/schema.html#partitions

#######

def cook( sh):
    '''
    >>> s = dict( \
            person= dict( age= t.int, \
                          names= (t.str, o.many),), \
            book= dict( name= t.str,), \
            )
    >>> s.update( { None: dict( justname= t.str )})
    >>> c = cook( s)
    >>> pprint( c, sort_dicts=False, width=150)
    [{Keyword(db/ident): Keyword(person/age), Keyword(db/valueType): Keyword(db.type/long), Keyword(db/cardinality): Keyword(db.cardinality/one)},
     {Keyword(db/ident): Keyword(person/names), Keyword(db/valueType): Keyword(db.type/string), Keyword(db/cardinality): Keyword(db.cardinality/many)},
     {Keyword(db/ident): Keyword(book/name), Keyword(db/valueType): Keyword(db.type/string), Keyword(db/cardinality): Keyword(db.cardinality/one)},
     {Keyword(db/ident): Keyword(justname), Keyword(db/valueType): Keyword(db.type/string), Keyword(db/cardinality): Keyword(db.cardinality/one)}]
    >>> print( qs.edn_dumps( c).replace( ' {', '\\n {'))
    [{:db/ident :person/age :db/valueType :db.type/long :db/cardinality :db.cardinality/one}
     {:db/ident :person/names :db/valueType :db.type/string :db/cardinality :db.cardinality/many}
     {:db/ident :book/name :db/valueType :db.type/string :db/cardinality :db.cardinality/one}
     {:db/ident :justname :db/valueType :db.type/string :db/cardinality :db.cardinality/one}]
    '''
    r = []
    for structname,fields in sh.items():
        for fieldname,decls in fields.items():
            if not isinstance( decls, (tuple,list)): decls = [ decls]
            assert fieldname
            itemprops = { db.ident: ns( structname, fieldname) if structname else ns1( fieldname) }
            for d in decls:
                overlap = set( d) & set( itemprops)
                assert not overlap, overlap
                itemprops.update( d)
            if db.cardinality not in itemprops:
                itemprops.update( options.one)
            r.append( itemprops )
    return r

def check( cooked_schema):
    nothing = object()
    possible_types = set( db_type( v) for v in set( _valueTypes.values()) )
    possible_cards = set([ *options.one.values(), *options.many.values() ])
    possible_uniqs = set([ nothing, *options.unique.values(), *options.identity.values() ])
    possible_flags = set( db( f) for f in _flags)
    tuple_keys  = [ db.tupleAttrs, db.tupleType, db.tupleTypes ]
    known_keys  = [ db.ident, db.valueType, db.cardinality, db.unique, db.doc,
                    *tuple_keys,
                    *possible_flags,
                    ]
    #more:
    #Keyword(db/id): [ Keyword(db.part/db) ],
    #Keyword(db.install/_attribute): Keyword(db.part/db)

    #print( locals())
    for itemprops in cooked_schema:
        db_ident = itemprops.get( db.ident )
        assert db_ident and qs.is_keyword( db_ident), (db_ident, itemprops)
        db_valueType = itemprops.get( db.valueType)
        assert db_valueType and db_valueType in possible_types, (db_valueType, itemprops)
        db_cardinality = itemprops.get( db.cardinality)
        assert db_cardinality and db_cardinality in possible_cards, (db_cardinality, itemprops)
        assert itemprops.get( db.unique, nothing) in possible_uniqs, itemprops

        #XXX 0.0 in { False:5 } -> True
        wrong_flags = dict( (k,v) for k,v in itemprops.items()
                        if k in possible_flags and v is not True and v is not False
                        )
        assert not wrong_flags, wrong_flags

        #components must be refs
        if itemprops.get( db.isComponent ):
            assert itemprops[ db.valueType ] == db_type.ref, itemprops

        #either a tuple with type-spec, or not a tuple and no type-spec
        is_tuple = itemprops[ db.valueType] == db_type.tuple
        which_tuple_keys = [ k for k in itemprops if k in tuple_keys ]
        assert int( is_tuple) == len( which_tuple_keys), itemprops
        if is_tuple:
            tkey = which_tuple_keys[0]
            ttype = itemprops[ tkey]
            if tkey == db.tupleTypes: tuple_many_types( *ttype )
            elif tkey == db.tupleAttrs: tuple_composite( *ttype )
            else: tuple_same_type( ttype )  #tkey == db.tupleType:

        unknowns = dict( (k,v) for k,v in itemprops.items()
                        if k not in known_keys )
        assert not unknowns, unknowns


__all__ = '''
types options flags combined
t o f s
make_enum tuple_composite tuple_same_type tuple_many_types doc
cook check ns_db ns_db_type
'''.split()

import difflib
def cmp( x, y, none_if_equal =False):
    '''compare lists of dicts/string-lines
    use:
    import edn_format
    edn_format.Keyword.__lt__ = lambda s,o: str(s)<str(o)
    for m in sh1,sh2:
        for d in m: d.pop( db.doc, None)
        m.sort( key= lambda x: x[db.ident] )
    diff = cmp( sh1,sh2, none_if_equal=True)
    if diff: print( *diff, sep='\n')
    '''
    def liner( a):
        if isinstance( a, (dict, edn_format.ImmutableDict)):
            return edn_format.dumps( a, sort_keys=True)#, indent=2)
        return a.strip()
    x = [ liner( a) for a in x]
    y = [ liner( a) for a in y]
    x = [ a for a in x if a]
    y = [ a for a in y if a]
    if x == y and none_if_equal: return ()
    return list( difflib.ndiff( x,y)) #unified_diff?

################

if __name__ == '__main__':
    from pprint import pprint
    schema = dict(
            person = dict(
                name= t.str,
                date= t.datetime,
                age = t.int,
                idd = (t.int, o.identity),
                ),
            )
    #pprint( schema)
    #pprint( cook( schema))
    def test_1():
        '''
    >>> pprint( schema, sort_dicts=False)
    {'person': {'name': {Keyword(db/valueType): Keyword(db.type/string)},
                'date': {Keyword(db/valueType): Keyword(db.type/instant)},
                'age': {Keyword(db/valueType): Keyword(db.type/long)},
                'idd': ({Keyword(db/valueType): Keyword(db.type/long)},
                        {Keyword(db/unique): Keyword(db.unique/identity)})}}
    >>> pprint( cook( schema), sort_dicts=False)
    [{Keyword(db/ident): Keyword(person/name),
      Keyword(db/valueType): Keyword(db.type/string),
      Keyword(db/cardinality): Keyword(db.cardinality/one)},
     {Keyword(db/ident): Keyword(person/date),
      Keyword(db/valueType): Keyword(db.type/instant),
      Keyword(db/cardinality): Keyword(db.cardinality/one)},
     {Keyword(db/ident): Keyword(person/age),
      Keyword(db/valueType): Keyword(db.type/long),
      Keyword(db/cardinality): Keyword(db.cardinality/one)},
     {Keyword(db/ident): Keyword(person/idd),
      Keyword(db/valueType): Keyword(db.type/long),
      Keyword(db/unique): Keyword(db.unique/identity),
      Keyword(db/cardinality): Keyword(db.cardinality/one)}]
        '''

if __name__ == '__main__':

    sh1 = dict( #all items become t.one unless t.many is specified
        student = dict(
            first   = t.str,
            last    = t.str,
            email   = (t.str, o.identity),
            ),
        semester = dict(
            year    = t.int,
            season  = t.keyword,
            **{ 'year+season': (tuple_composite( ns.semester.year, ns.semester.season), o.identity ),
            }),
        course  = dict(
            id      = (t.str, o.identity),
            name    = t.str,
            ),

        reg = dict(
            course  = t.ref,
            semester= t.ref,
            student = t.ref,
            **{ 'semester+course+student': (tuple_composite( ns.reg.course, ns.reg.semester, ns.reg.student ), o.identity),
            }),
        )
    #pprint( sh1, sort_dicts=False)
    sh1c = cook( sh1)   # -> list of dict-per-item

    sh2 = '''[
    ;;https://docs.datomic.com/on-prem/schema/schema.html#composite-tuples
    ;;cardinality is moved at end of each
     {:db/ident       :student/first
      :db/valueType     :db.type/string
      :db/cardinality   :db.cardinality/one}
     {:db/ident       :student/last
      :db/valueType     :db.type/string
      :db/cardinality   :db.cardinality/one}
     {:db/ident       :student/email
      :db/valueType     :db.type/string
      :db/unique        :db.unique/identity
      :db/cardinality   :db.cardinality/one}
    '''+1*'''
     {:db/ident       :semester/year
      :db/valueType     :db.type/long
      :db/cardinality   :db.cardinality/one}
     {:db/ident       :semester/season
      :db/valueType     :db.type/keyword
      :db/cardinality   :db.cardinality/one}
     {:db/ident       :semester/year+season
      :db/valueType     :db.type/tuple
      :db/tupleAttrs    [:semester/year :semester/season]
      :db/unique        :db.unique/identity
      :db/cardinality   :db.cardinality/one}

     {:db/ident       :course/id
      :db/valueType     :db.type/string
      :db/unique        :db.unique/identity
      :db/cardinality   :db.cardinality/one}
     {:db/ident       :course/name
      :db/valueType     :db.type/string
      :db/cardinality   :db.cardinality/one}

    ;;registration entity contains:
    {:db/ident        :reg/course
     :db/valueType      :db.type/ref
     :db/cardinality    :db.cardinality/one}
    {:db/ident        :reg/semester
     :db/valueType      :db.type/ref
     :db/cardinality    :db.cardinality/one}
    {:db/ident        :reg/student
     :db/valueType      :db.type/ref
     :db/cardinality    :db.cardinality/one}

    ;;registration course/semester/student combination is unique in the database
    {:db/ident        :reg/semester+course+student
     :db/valueType      :db.type/tuple
     :db/tupleAttrs     [:reg/course :reg/semester :reg/student]
     :db/unique         :db.unique/identity
     :db/cardinality    :db.cardinality/one}
    '''+'''
    ]'''

    sh3c = edn_format.loads( sh2)
    #print( 222222,sh3c)
    #sh2c = [ l for l in sh2.split('\n') if l.strip()[:2] != ';;' ] # del comment-lines
    #sh2c = ' '.join( ' '.join( sh2c).split() )  #one single line
    #sh2c = [ l.strip() for l in sh2c.replace( '{','\n{').strip().split('\n') ] # -> list of text-per-item like {..item-decl..}
#    ).replace('{','{\n'
#    ).replace('}','\n}'
#    ).replace('[','[ '
#    ).replace(']',' ]'

    check( sh1c)
    check( sh3c)

    diff = cmp( sh1c, sh3c, none_if_equal=True)
    if diff:
        print( *diff, sep='\n')
        assert not diff
    #def tcmp():
    #    ''' test if sh1c is same as sh2c
    #    >>> print( *cmp( sh1c, sh2c, none_if_equal=True), sep='\\n', end='ok')
    #    ok
    #    '''
    #    pass

    import doctest
    doctest.testmod()

    ''' ;;creating some:
    [{:semester/year 2018
      :semester/season :fall}
     {:course/id "BIO-101"}
     {:student/first "John"
      :student/last "Doe"
      :student/email "johndoe@university.edu"}]

    [{:reg/course [:course/id "BIO-101"]
      :reg/semester [:semester/year+season [2018 :fall]]
      :reg/student [:student/email "johndoe@university.edu"]}]
    '''

# vim:ts=4:sw=4:expandtab
