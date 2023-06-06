from base.schema import s, struct, EnumType

from base.utils import dictAttr
import datetime
################################
#usage

enum_country_ISO3166 = s.enum( 'country_ISO3166')

aspects = dictAttr(
    ofclient = struct(
        your_reference = s.str,     #uniq-with-account?
        account = s.link( 'account', required= True) ,    #= _accounts ??
        ),
    metacontact = struct(
        #these.. common for address, contact, maybe relation, maybe bank_account might be part of has-contact relation
        #status      = s.enum, #active inactive -> bool ?
        active      = s.bool, #from status=active inactive -> bool ? is this used ?
        valid       = s.bool,
        confirmed   = s.bool,
        primary     = s.bool,
        #byCreditor = s.bool,
		#owner_label = s.enum, #:owner_label: personal employer parents relative lawyer legal_guardian consumer_protector debt_advisor workplace
        #source = s.str, #s.enum? : validation:phone validation:address
        #reason = s.str     #setContactConfirmed
        ),
    )
sh = dictAttr(
    entity = struct(
        person = s.component( struct(
            given_names= s.str,
            surname = s.str,
            title   = s.str,
            gender  = s.enum( 'gender_type'),   #: m f x none/u
            date_of_birth   = s.datetime, # "1991-04-22" ISO-8601
            date_of_death   = s.datetime, # "1991-04-22"
            #place_of_birth: { "city": "Prague", "country": "CH" },
            #place_of_death: { "city": "Prague", "country": "CH" },
            nationality     = enum_country_ISO3166, #: "IT" ISO-3166
            ), flatten= True),
        organisation = s.component( struct(
            name    = s.str,
            type    = s.str( doc= 'like: Ltd, GmbH, etc'),    #enum?? unlikely
            ), flatten= True),
        is_organisation = s.bool,
        #from person+organisation
        country_of_residence = enum_country_ISO3166, #: "IT"   ISO-3166
        #derived from country_of_residence but stored - as deriving-rules may change in time
        territory   = s.enum( 'territory_system'),   #: "IT" "ROW" : subset of ISO-3166 + EUZ NEZ ROW

        #from entity
        addresses   = s.component( 'address', many= True), ##isComponent: auto-pull/del-recursive
        contacts    = s.component( 'contact', many= True),
        #bank_accounts = s.component( 'bank_account, many=True)
        id          = s.str( identity=True ),  #id : "893R3PQ0"
        #should be many2many-with-metadata=rel.type; a->b -> rel-type ; b->a -> reverse( rel.type)
        #but currently is just ref-to+type, and no auto-reverses - other side is unrelated
        relations   = s.component( struct(
            type = s.enum( 'relation_type'),
            entity = s.link( 'entity'),
            #also: confirmed source reason... not a full metacontact
            ), many= True, embed=True),
        #others: _accounts _files _customers source

        #from customer
        custid      = s.str( identity=True),  #id : "cus-882GJAV28933STY0"
        metadata    = s.component( struct(
            type = s.enum( 'metadata_customer_types'),
            value = s.str,
            ), many= True, embed=True),     # non-system classification ?
        #events?

        **aspects.ofclient,
        #__include( 'ofclient')
        ),
    account = struct(
        id = s.str( identity=True),   #acc-882GJAV2
        name = s.str,
        active = s.bool,
        #... lots of.. ecollect-v2-core/app/crud/manage/account.js
        ),

    address = struct(  # validation/schemas/system/Address.system.schema.json
        lines   = s.str( many=True), #[ "VIA QUADRONNO 34" ] ,
        city    = s.str,    #"MILANO" ,
        country = enum_country_ISO3166,   #:country_ISO3166: "IT" ,
        zip     = s.str,    #"20122"    postalcode?
        #district= s.str,
        state   = s.str,
        type    = s.enum( 'address_type'), # "not_specified" "billing" "mailing" "delivery" "residence"
        #delivery_instruction = s.str,

        **aspects.metacontact,
        ),
    contact = struct(     # validation/schemas/system/Contact.system.schema.json
        type    = s.enum( 'contact_type'), #: phone , email
        value   = s.str,
        country = enum_country_ISO3166,   #:country_ISO3166: "IT" , ??     from address ?

        **aspects.metacontact,
        ),
    #bank_account = also kind of contact... #validation/schemas/bankAccount.json validation/schemas/system/BankAccount.system.schema.json
    )

'''
can be flat:
    *entity, *ofclient, *person, *organisation,
    -> can be both person and org
can be 2-level:
    *entity, *ofclient,
    person = component
    organisation = component
    -> can be both person and org
can be 2-level:
    *entity, *ofclient,
    who = ref to separate-person OR separate-organisation (and treat as isComponent?)
'''

# EnumType = plain enum.Enums
enums = dictAttr(
    #address_type    = EnumType( 'address', 'billing mailing delivery residence'),
    country_ISO3166 = EnumType( 'country', 'NZ IT DE BG RO AU'),
    gender_type     = EnumType( 'gender',  'm f x'),
    contact_type    = EnumType( 'contact', '''
        email phone cellphone''' + 0*''' sms fax
				skype facebook_messenger imessage whatsapp viber
				facebook google+ twitter linkedin xing badoo
				social_various website_url web_various other
                '''),
    #owner_label    = EnumType( 'owner_label', 'personal employer parents relative lawyer legal_guardian consumer_protector debt_advisor workplace'),  #non-system-classification ?
    territory_system= EnumType( 'territory', 'DE BG  EUZ NEZ ROW'), #derived from country_of_residence but stored in db ; as deriving-rules may change later
    relation_type   = EnumType( 'relation', # v2core/app/validation/schemas/relationType.json
                ''' is_parent_of_child    is_sibling_of_sibling
                ''')
    )

if __name__ == '__main__':
    from pprint import pprint
    #pprint( sh, sort_dicts=False)
    #pprint( enums)

    def test_s():
        '''
        >>> enum_country_ISO3166
        enum( typeorname=country_ISO3166 )
        >>> pprint( aspects)
        {'metacontact': {'active': bool,
                         'confirmed': bool,
                         'primary': bool,
                         'valid': bool},
         'ofclient': {'account': link( required=True, typeorname=account ),
                      'your_reference': str}}
        >>> sh.entity.organisation # doctest: +ELLIPSIS
        component( typeorname={'name': str, 'type': str( doc=... )}, flatten=True, embed=False )
       '''
    # enum_country_ISO3166 is unrelated to enums.country_ISO3166   XXX
    def test_e():
        ''' enum.Enums:
        >>> enums.country_ISO3166.NZ
        <country.NZ: 'NZ'>
        >>> enums.country_ISO3166.NZ.name
        'NZ'
        >>> list( enums.country_ISO3166.__members__)
        ['NZ', 'IT', 'DE', 'BG', 'RO', 'AU']
        >>> enums.country_ISO3166['NZ']
        <country.NZ: 'NZ'>
        >>> enums.country_ISO3166['x']
        Traceback (most recent call last):
        ...
        KeyError: 'x'
        '''

    import doctest
    doctest.testmod()

# vim:ts=4:sw=4:expandtab
