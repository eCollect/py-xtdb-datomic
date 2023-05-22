#!/usr/bin/env python
from .qsyntax import xtq, var, sym, kw, pull
from base.qsyntax import edn_dumps, _text2maplines, _text2dumps1line
'''
https://docs.xtdb.com/extensions/full-text-search/
input string escaping - use org.apache.lucene.queryparser.classic.QueryParser/escape

https://lucene.apache.org/core/8_9_0/queryparser/org/apache/lucene/queryparser/classic/package-summary.html#package.description
abc* ab?c ab*c - wildcards, anywhere but in start
abc~  - fuzzy-dist=2
abc~3 - fuzzy-dist=3
'''

class qlucene:
    #funcname = ..
    #outs = ..
    @classmethod
    def func( me, sym =None, kw =None):
        f = me.funcname
        return f if not sym else [ getattr( sym, f) ]
    @classmethod
    def textq( me, x, limit =5, where_clauses ='', result_by_eid ='(pull ?eid [*])', **ka):
        outs = me.outs.split()
        vars = ' '.join(  '?'+a for a in outs)
        return '{ :query {' + f'''
            :find [ {vars}  {result_by_eid} ]
            :keys [ {me.outs}  result ]
            :where [
                [({me.func(**ka)} "{x}")  [[ ?eid {vars} ]]]
                {where_clauses} ]
            :order-by [[?score :desc]]
            :limit {limit}''' + '''
            }}'''
    @classmethod
    def xtq( me, x, limit =5, where_clauses =(), result_by_eid =None, **funcka): #field
        outs = me.outs.split()
        vars = [ getattr( var, a) for a in outs]
        return xtq(
            ).find( *vars, result_by_eid or pull( var.eid, whole=True)
            ).into_keys( *outs, 'result'
            ).where(
                [ (*me.func( sym=sym, kw=kw, **funcka), x), [[ var.eid, *vars ]]],
                *where_clauses
            ).orderby( (var.score, kw.desc)
            ).limit( limit
            )

class lucene_wildcard( qlucene):
    outs = 'value attr score' #.split()   #eid then these
    funcname = 'wildcard-text-search'

    example_whole = """{ :query {
:find [ ?value ?attr ?score  (pull ?eid [*])]
:keys [ value attr score  result]
:where [
    [(wildcard-text-search "jame~")  [[?eid ?value ?attr ?score]]]
    ]
:order-by [[?score :desc]]
:limit 5
}}"""

class lucene_text( qlucene):
    outs = 'value score' #.split()   #eid then these
    @classmethod
    def func( me, *, field, sym =None, kw =None):
        f = 'text-search'
        if not sym: return f'{f} :{field}'
        return [ getattr( sym, f), getattr( kw, field) ]

    example_whole = """{ :query {
:find [ ?value ?score  (pull ?eid [*])]
:keys [ value score  result]
:where [
    [(text-search :name "jame~")  [[?eid ?value ?score]]]
    ]
:order-by [[?score :desc]]
:limit 5
}}"""

class lucene_multifield( qlucene):
    outs = 'score' #.split()   #eid then these
    funcname = 'lucene-text-search'

    example_whole = """{ :query {
:find [ ?score  (pull ?eid [*]) ]
:keys [ score  result]
:where [
    [(lucene-text-search "name:james~2 AND state:ne*")  [[ ?eid ?score ]]]
    ]
:order-by [[?score :desc]]
:limit 5
}}"""

if __name__ == '__main__':
    #test syntax generating
    from pprint import pprint
    def testeq( res, exp):
        assert res == exp, pprint( locals())
    def testdump( res, exp):
        res = { kw.query: res } #hack
        xres = _text2maplines( edn_dumps( res))
        xexp = _text2maplines( exp)
        if 0: print( xres, '\n        ?????\n', xexp)
        testeq( xres, xexp)

    testeq(
        _text2maplines( lucene_text.textq( 'jame~', field= 'name')),
        _text2maplines( lucene_text.example_whole),
        )
    testdump(
        lucene_text.xtq(   'xyz', field= 'name'),
        lucene_text.textq( 'xyz', field= 'name'),
        )

    testeq(
        _text2maplines( lucene_wildcard.textq( 'jame~' )),
        _text2maplines( lucene_wildcard.example_whole),
        )
    testdump(
        lucene_wildcard.xtq( 'xyz' ),
        lucene_wildcard.textq( 'xyz' ),
        )

    testeq(
        _text2maplines( lucene_multifield.textq( 'name:james~2 AND state:ne*' )),
        _text2maplines( lucene_multifield.example_whole),
        )
    testdump(
        lucene_multifield.xtq( 'xyz' ),
        lucene_multifield.textq( 'xyz' ),
        )

    #just this one
    qlcw = xtq(
        ).find( var.value, var.attr, var.score,  pull( var.eid, whole=True)
        ).into_keys( 'value attr score result'
        ).where(
            [ (sym('wildcard-text-search'), 'jami~'), [[ var.eid, var.value, var.attr, var.score ]]],
        ).orderby( (var.score, kw.desc)
        ).limit( 5
        )
    testeq( qlcw, lucene_wildcard.xtq( 'jami~' ))

if 0:
    #test real querying
    '''
    - for each lucene_x:
        test real db+results
    '''

    rrt= db.query( lucene_text.xtq( 'jami~', field= 'name'))
    pprint( rrt)
    rrw= db.query( lucene_wildcard.xtq( 'jami~' ))
    pprint( rrw)

if 0:
    ''' needs different config
    :xtdb.lucene/lucene-store {:db-dir ...
        :indexer xtdb.lucene.multi-field/->indexer	;;for multi-field lucene-text-search
        '''
    rrm= db.query( lucene_multifield.xtq( "name:james~2 AND state:ne*" ))
    pprint( rrm)

# vim:ts=4:sw=4:expandtab
