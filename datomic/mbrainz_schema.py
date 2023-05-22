from .schema import db, db_type, ns
db_cardinality = ns( 'db.cardinality')
db_unique = ns( 'db.unique')

mschema = [
  { db.valueType: db_type.string,
    db.ident: ns.country.name,
    db.cardinality: db_cardinality.one,
    db.unique: db_unique.value,
    db.doc: 'The name of the country'
  },
  { db.valueType: db_type.uuid,
    db.ident: ns.artist.gid,
    db.unique: db_unique.identity,
    db.index: True,
    db.doc: 'The globally unique MusicBrainz ID for an artist',
    db.cardinality: db_cardinality.one,
  },
  { db.valueType: db_type.string,
    db.ident: ns.artist.name,
    db.cardinality: db_cardinality.one,
    db.fulltext: True,
    db.index: True,
    db.doc: "The artist's name"
  },
  { db.ident: ns.artist.sortName,
    db.valueType: db_type.string,
    db.cardinality: db_cardinality.one,
    db.index: True,
    db.doc: "The artist's name for use in alphabetical sorting, e.g. Beatles, The"
  },
  { db.valueType: db_type.ref,
    db.ident: ns.artist.type,
    db.cardinality: db_cardinality.one,
    db.doc: 'Enum, one of :artist.type/person, :artist.type/other, :artist.type/group.'
  },
  { db.valueType: db_type.ref,
    db.ident: ns.artist.gender,
    db.cardinality: db_cardinality.one,
    db.doc: 'Enum, one of :artist.gender/male, :artist.gender/female, or :artist.gender/other.'
  },
  { db.valueType: db_type.ref,
    db.ident: ns.artist.country,
    db.cardinality: db_cardinality.one,
    db.doc: "The artist's country of origin"
  },
  { db.valueType: db_type.long,
    db.ident: ns.artist.startYear,
    db.cardinality: db_cardinality.one,
    db.index: True,
    db.doc: 'The year the artist started actively recording'
  },
  { db.valueType: db_type.long,
    db.ident: ns.artist.startMonth,
    db.cardinality: db_cardinality.one,
    db.doc: 'The month the artist started actively recording'
  },
  { db.valueType: db_type.long,
    db.ident: ns.artist.startDay,
    db.cardinality: db_cardinality.one,
    db.doc: 'The day the artist started actively recording'
  },
  { db.valueType: db_type.long,
    db.ident: ns.artist.endYear,
    db.cardinality: db_cardinality.one,
    db.doc: 'The year the artist stopped actively recording'
  },
  { db.valueType: db_type.long,
    db.ident: ns.artist.endMonth,
    db.cardinality: db_cardinality.one,
    db.doc: 'The month the artist stopped actively recording'
  },
  { db.valueType: db_type.long,
    db.ident: ns.artist.endDay,
    db.cardinality: db_cardinality.one,
    db.doc: 'The day the artist stopped actively recording'
  },
  { db.valueType: db_type.uuid,
    db.ident: ns.abstractRelease.gid,
    db.cardinality: db_cardinality.one,
    db.unique: db_unique.identity,
    db.index: True,
    db.doc: 'The globally unique MusicBrainz ID for the abstract release'
  },
  { db.valueType: db_type.string,
    db.ident: ns.abstractRelease.name,
    db.cardinality: db_cardinality.one,
    db.index: True,
    db.doc: 'The name of the abstract release'
  },
  { db.valueType: db_type.ref,
    db.ident: ns.abstractRelease.type,
    db.cardinality: db_cardinality.one,
    db.doc: 'Enum, one of: :release.type/album, :release.type/single, :release.type/ep, :release.type/audiobook, or :release.type/other'
  },
  { db.valueType: db_type.ref,
    db.ident: ns.abstractRelease.artists,
    db.cardinality: db_cardinality.many,
    db.doc: 'The set of artists contributing to the abstract release'
  },
  { db.valueType: db_type.string,
    db.ident: ns.abstractRelease.artistCredit,
    db.cardinality: db_cardinality.one,
    db.fulltext: True,
    db.doc: 'The string represenation of the artist(s) to be credited on the abstract release'
  },
  { db.valueType: db_type.uuid,
    db.ident: ns.release.gid,
    db.cardinality: db_cardinality.one,
    db.unique: db_unique.identity,
    db.index: True,
    db.doc: 'The globally unique MusicBrainz ID for the release'
  },
  { db.valueType: db_type.ref,
    db.ident: ns.release.country,
    db.cardinality: db_cardinality.one,
    db.doc: 'The country where the recording was released'
  },
  { db.valueType: db_type.string,
    db.ident: ns.release.barcode,
    db.cardinality: db_cardinality.one,
    db.doc: 'The barcode on the release packaging'
  },
  { db.valueType: db_type.string,
    db.ident: ns.release.name,
    db.cardinality: db_cardinality.one,
    db.fulltext: True,
    db.index: True,
    db.doc: 'The name of the release'
  },
  { db.valueType: db_type.ref,
    db.ident: ns.release.media,
    db.isComponent: True,
    db.cardinality: db_cardinality.many,
    db.doc: 'The various media (CDs, vinyl records, cassette tapes, etc.) included in the release.'
  },
  { db.valueType: db_type.ref,
    db.ident: ns.release.packaging,
    db.cardinality: db_cardinality.one,
    db.doc: 'The type of packaging used in the release, an enum, one of: :release.packaging/jewelCase, :release.packaging/slimJewelCase, :release.packaging/digipak, :release.packaging/other, :release.packaging/keepCase, :release.packaging/none, or :release.packaging/cardboardPaperSleeve'
  },
  { db.valueType: db_type.long,
    db.ident: ns.release.year,
    db.cardinality: db_cardinality.one,
    db.index: True,
    db.doc: 'The year of the release'
  },
  { db.valueType: db_type.long,
    db.ident: ns.release.month,
    db.cardinality: db_cardinality.one,
    db.doc: 'The month of the release'
  },
  { db.valueType: db_type.long,
    db.ident: ns.release.day,
    db.cardinality: db_cardinality.one,
    db.doc: 'The day of the release'
  },
  { db.valueType: db_type.string,
    db.ident: ns.release.artistCredit,
    db.cardinality: db_cardinality.one,
    db.fulltext: True,
    db.doc: 'The string represenation of the artist(s) to be credited on the release'
  },
  { db.valueType: db_type.ref,
    db.ident: ns.release.artists,
    db.cardinality: db_cardinality.many,
    db.doc: 'The set of artists contributing to the release'
  },
  { db.valueType: db_type.ref,
    db.ident: ns.release.abstractRelease,
    db.cardinality: db_cardinality.one,
    db.doc: 'This release is the physical manifestation of the associated abstract release, e.g. the the 1984 US vinyl release of "The Wall" by Columbia, as opposed to the 2000 US CD release of "The Wall" by Capitol Records.'
  },
  { db.valueType: db_type.string,
    db.ident: ns.release.status,
    db.cardinality: db_cardinality.one,
    db.index: True,
    db.doc: 'The status of the release'
  },
  { db.valueType: db_type.ref,
    db.ident: ns.medium.tracks,
    db.isComponent: True,
    db.cardinality: db_cardinality.many,
    db.doc: 'The set of tracks found on this medium'
  },
  { db.valueType: db_type.ref,
    db.ident: ns.medium.format,
    db.cardinality: db_cardinality.one,
    db.doc: 'The format of the medium. An enum with lots of possible values'
  },
  { db.valueType: db_type.long,
    db.ident: ns.medium.position,
    db.cardinality: db_cardinality.one,
    db.doc: 'The position of this medium in the release relative to the other media, i.e. disc 1'
  },
  { db.valueType: db_type.string,
    db.ident: ns.medium.name,
    db.cardinality: db_cardinality.one,
    db.fulltext: True,
    db.doc: 'The name of the medium itself, distinct from the name of the release'
  },
  { db.valueType: db_type.long,
    db.ident: ns.medium.trackCount,
    db.cardinality: db_cardinality.one,
    db.doc: 'The total number of tracks on the medium'
  },
  { db.valueType: db_type.ref,
    db.ident: ns.track.artists,
    db.cardinality: db_cardinality.many,
    db.doc: 'The artists who contributed to the track'
  },
  { db.valueType: db_type.long,
    db.ident: ns.track.position,
    db.cardinality: db_cardinality.one,
    db.doc: 'The position of the track relative to the other tracks on the medium'
  },
  { db.valueType: db_type.string,
    db.ident: ns.track.name,
    db.cardinality: db_cardinality.one,
    db.fulltext: True,
    db.index: True,
    db.doc: 'The track name'
  },
  { db.valueType: db_type.long,
    db.ident: ns.track.duration,
    db.cardinality: db_cardinality.one,
    db.index: True,
    db.doc: 'The duration of the track in msecs'
  },
]

from base.schema import s, struct, dictAttr
msh = dictAttr(
    country= struct( #enum ??
        name = s.str( unique=True),
        ),
    artist = struct(
        gid = s.uuid( identity=True, index=True),
        name = s.str( fulltext=True, index=True),
        sortName = s.str( index=True),
        type = s.enum( 'artist_types'),
        gender = s.enum( 'artist_gender'),
        country= s.enum( 'country'),
        startYear = s.int( index=True),
        startMonth = s.int,
        startDay = s.int,
        endYear = s.int,
        endMonth = s.int,
        endDay = s.int,
        ),
    abstractRelease = struct(
        gid = s.uuid( identity=True, index=True),
        name = s.str( index=True),
        type = s.enum( 'release_type'),
        artists = s.link( 'artist', many=True),
        artistCredit = s.str( fulltext=True ),
        ),
    release = struct(
        gid = s.uuid( identity=True, index=True),
        country= s.enum( 'country'),
        barcode= s.str,
        name = s.str( fulltext=True, index=True),
        media = s.component( 'medium', many=True),
        packaging = s.enum( 'packaging_type'),
        year = s.int( index=True),
        month= s.int,
        day  = s.int,
        artistCredit = s.str( fulltext=True ),
        artists = s.link( 'artist', many=True),
        abstractRelease = s.link( 'abstractRelease'),
        status = s.str( index=True),
        ),
    medium = struct(
        tracks = s.component( 'track', many=True),
        format = s.enum( 'medium_format'),
        position = s.int,
        name = s.str( fulltext=True, ),
        trackCount = s.int,
        ),
    track = struct(
        artists = s.link( 'artist', many=True),
        position = s.int,
        name = s.str( fulltext=True, index=True),
        duration = s.int( index=True, doc= 'The duration of the track in msecs'),
        ),
    )


if __name__ == '__main__':
    from .schema import check, cook, cmp
    check( mschema)

    from .toschema import objmap
    o2a_maps = objmap.build_maps( msh)
    obj2attrs = objmap.build_da_maps( o2a_maps)
    mshc = cook( obj2attrs)   # -> list of dict-per-item
    check( mshc)

    import edn_format
    edn_format.Keyword.__lt__ = lambda s,o: str(s)<str(o)
    for m in mschema, mshc:
        for d in m: d.pop( db.doc, None)
        m.sort( key= lambda d: d[ db.ident] )

    diff = cmp( mshc, mschema, none_if_equal=True)
    if diff:
        print( *diff, sep='\n')
        assert not diff

# vim:ts=4:sw=4:expandtab
