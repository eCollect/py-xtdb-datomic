from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, validator


class User(BaseModel):
    id: int
    name = 'John Doe'
    signup_ts: Optional[datetime] = None
    friends: List[int] = []

    @validator('signup_ts')
    def date_only( cls, d):     # XXX !cls
    #def date_only( cls, d, values, config, field):
        assert isinstance( d, datetime), d
        return d


external_data = {
    'id': '123',
    'signup_ts': '2019-06-01 12:22',
    'friends': [1, 2, '3'],
}
user = User(**external_data)
print(user.id)
#> 123
print(repr(user.signup_ts))
#> datetime.datetime(2019, 6, 1, 12, 22)
print(user.friends)
#> [1, 2, 3]
print(user.dict())
"""
{
    'id': 123,
    'signup_ts': datetime.datetime(2019, 6, 1, 12, 22),
    'friends': [1, 2, 3],
    'name': 'John Doe',
}
"""

#user2 = User(**dict(external_data, signup_ts='-asdd5'))
#print( user2.dict())
user.signup_ts = 'asdf'
print( user.dict())
