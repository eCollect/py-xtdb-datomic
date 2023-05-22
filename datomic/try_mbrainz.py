#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
https://github.com/Datomic/mbrainz-sample
https://github.com/Datomic/mbrainz-sample/wiki/Queries
'''
#TODO: edn_dumps to make a str-subclass (stredn?) to know when applied

from dbclient import Datomic, log, edn_dumps
from qsyntax import daq, eav, var, kw2, src_default, pull, eavt, rule, sym, rule_default
ns = kw2
nsdb = kw2.db


db = Datomic( 'http://localhost:8992', 'devv', 'mbrainz-1968-1973')

log( db.info)
#db.debug=1

print( 'id of artist.name - hardcoded')
log( db.query, daq(
        ).find( var.id,
        ).where(
            eav( var.e, ns.artist.name, 'Janis Joplin' ),
            eav( var.e, ns.artist.gid , var.id  ),
        ))

print( 'id,type,gender of artist.name - param')
log( db.query, daq(
        ).find( var.id, var.type, var.gender
        ).in_( var.name
        ).where(
            eav( var.e, ns.artist.name, var.name),
            eav( var.e, ns.artist.gid , var.id  ),
            eav( var.e, ns.artist.type, var.teid),
            eav( var.teid, nsdb.ident, var.type),
            eav( var.e, ns.artist.gender, var.geid),
            eav( var.geid, nsdb.ident, var.gender),
            ),
        edn_dumps( "Janis Joplin"),
    )
'''
[:find ?id ?type ?gender
   :in $ ?name
   :where
   [?e :artist/name ?name]
   [?e :artist/gid ?id]
   [?e :artist/type ?teid]
   [?teid :db/ident ?type]
   [?e :artist/gender ?geid]
   [?geid :db/ident ?gender]]
 db
 "Janis Joplin")
 '''

print( 'title of tracks of artist.name - param')
log( db.query, daq(
        ).find( var.title,
        ).in_( var.name
        ).where(
            eav( var.e, ns.artist.name, var.name),
            eav( var.t, ns.track.artists, var.e  ),
            eav( var.t, ns.track.name, var.title  ),
            ),
        edn_dumps( "Janis Joplin"),
        limit=3
    )

print( 'all-info of tracks of artist.name - param')
log( db.query, daq(
        ).find( pull( var.t, whole=True),
        ).in_( var.name
        ).where(
            eav( var.e, ns.artist.name, var.name),
            eav( var.t, ns.track.artists, var.e  ),
            #eav( var.t, ns.track.name, var.title  ),
            ),
        edn_dumps( "Janis Joplin"),
        limit=3
    )

print( 'title and album-title of tracks of artist.name - param')
log( db.query, daq(
        ).find( var.title, var.album
        ).in_( var.name
        ).where(
            eavt( var.e, ns.artist.name, var.name),
            eavt( var.t, ns.track.artists, var.e  ),
            eavt( var.t, ns.track.name, var.title  ),
            eavt( var.m, ns.medium.tracks, var.t),
            eavt( var.r, ns.release.media, var.m),
            eavt( var.r, ns.release.name, var.album),
            ),
        edn_dumps( "Janis Joplin"),
        limit=3
    )

'''
;; Given ?t bound to track entity-ids, binds ?r to the corresponding
;; set of album release entity-ids
[(track-release ?t ?r)
[?m :medium/tracks ?t]
[?r :release/media ?m]]
'''
rule4track_release = rule( sym.track_release, [var.t, var.r],
    eav( var.m, ns.medium.tracks, var.t),
    eav( var.r, ns.release.media, var.m),
    )

print( 'title and album-title of tracks of artist.name - param+rule')
qpr1 = daq(
        ).find( var.title, var.album
        ).where(
            eavt( var.e, ns.artist.name, var.name),
            eavt( var.t, ns.track.artists, var.e  ),
            eavt( var.t, ns.track.name, var.title  ),
            ( sym.track_release, var.t, var.r), # list or tuple, works either way
            eavt( var.r, ns.release.name, var.album),
            )

rqpr1a = log( db.query, qpr1.copy(
        ).in_( rule_default, var.name
        ),
        [ rule4track_release ],
        edn_dumps( "Janis Joplin"),
        limit=3
    )
#same with .rules
rqpr1b = log( db.query, qpr1.copy(
        ).in_( var.name
        ).rules( rule4track_release
        ),
        edn_dumps( "Janis Joplin"),
        limit=3
    )
assert rqpr1a == rqpr1b

'''
;; Fulltext search on track.  Supply the query string ?q, and ?track
;; will be bound to entity-ids of tracks whose title matches the search.
[(track-search ?q ?track)
[(fulltext $ :track/name ?q) [[?track ?tname]]]]
'''
rule4track_search = rule( sym.track_search, [var.q, var.track, var.tname],
    [ ( sym.fulltext, src_default, ns.track.name, var.q),
        [[var.track, var.tname]]
        ])
print( 'track+title+album of tracks with title matching some text - param+rule')
log( db.query, daq(
        ).find( var.tname, var.album
        ).in_( var.q
        ).where(
            ( sym.track_search, var.q, var.t, var.tname),
            ( sym.track_release, var.t, var.r), # list or tuple, works either way
            eavt( var.r, ns.release.name, var.album),
        ).rules(
            rule4track_search, rule4track_release
        ),
        edn_dumps( "always"),
        limit=3
    )

# vim:ts=4:sw=4:expandtab
