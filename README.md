rate-limit
==========

Implementation of a Redis rate limiter in Python

## class __RateLimiter__
****************************************
RateLimiter is used to define one or more rate limit rules.
These rules are checked on .acquire() and we either return True or False based on if we can make the request,
or we can block until we make the request.
Manual blocks are also supported with the block method.


### __methods__
****************************************

#### def __\__init__\__(self, conditions=None, redis_host='localhost', redis_port=6379, redis_db=0, redis_password=None, redis_namespace='ratelimiter'):

Initalize an instance of a RateLimiter

conditions - list or tuple of rate limit rules
redis_host - Redis host to use
redis_port - Redis port (if different than default 6379)
redis_db   - Redis DB to use (if different than 0)
redis_password - Redis password (if needed)
redis_namespace - Redis key namespace

#### def __acquire__(self, key, block=True):

Tests whether we can make a request, or if we are currently being limited
key - key to track what to rate limit
block - Whether to wait until we can make the request

#### def __add_condition__(self, *conditions):

Adds one or more conditions to this RateLimiter instance
Conditions can be given as:
    add_condition(1, 10)
    add_condition((1, 10))
    add_condition((1, 10), (30, 600))
    add_condition({'requests': 1, 'seconds': 10})
    add_condition({'requests': 1, 'seconds': 10}, {'requests': 200, 'hours': 6})

    dict can contain 'seconds', 'minutes', 'hours', and 'days' time period parameters

#### def __block__(self, key, seconds=0, minutes=0, hours=0, days=0):

Set manual block for key for a period of time
key - key to track what to rate limit
Time parameters are added together and is the period to block for
    seconds
    minutes
    hours
    days
