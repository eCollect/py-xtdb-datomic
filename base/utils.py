
class dictAttr( dict):
    '''attr-access == item-access ; i.e. self.a is self['a']
    >>> d = dictAttr( a=1, b=2)
    >>> d
    {'a': 1, 'b': 2}
    >>> d.a , d['b']
    (1, 2)
    >>> d.c = 3
    >>> d['c']
    3
    '''
    def __init__( me, *a, **k):
        dict.__init__( me, *a, **k)
        me.__dict__ = me

from enum import Enum
class strEnum( str, Enum):
    '''takes sequence of strings , or one string to be split by whitespace
    >>> s = strEnum( 'aname', ['a', 'bb', 'c'])
    >>> print( s, s.bb, s.bb.name)
    <enum 'aname'> aname.bb bb
    >>> t = strEnum( 'bname', 'a bb cc')
    >>> print( t, t.bb, t.cc.name)
    <enum 'bname'> bname.bb cc
    '''
    def _generate_next_value_(name, start, count, last_values): return name


if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim:ts=4:sw=4:expandtab
