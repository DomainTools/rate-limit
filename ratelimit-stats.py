#!/usr/bin/env python2.7

"""
This module gathers stats on running RateLimiter instances

To note. If we are not keeping keys for a whole day RateLimit entries will be cleaned up and not counted in this stats script.

"""
import sys
import time
import collections
import redis
import argparse
import logging

def ratelimiter_stats(redis_host, namespace='ratelimiter', min_daily_count=None):
    """
    Gather and show statistics on running RateLimiter instances
    """
    conn = redis.Redis(redis_host)
    now = time.time()
    log = logging.getLogger('stats.ratelimiter')

    # remove namespace leaving key
    l_namespace = len(namespace)

    all_keys = set()

    rl5m = collections.Counter()
    rl15m = collections.Counter()
    rl1h = collections.Counter()
    rl1d = collections.Counter()

    tot5m = 0
    tot15m = 0
    tot1h = 0
    tot1d = 0

    keys = conn.keys(namespace + '*:log')
    l_keys = len(keys)
    for i, wholekey in enumerate(keys, start=1):
        # remove namespace and :log
        key = wholekey[l_namespace:-4]

        # only print progress every 1000 keys
        if not i % 1000:
            log.debug('gathering stats (%d / %d)', i, l_keys)

        all_keys.add(key)

        timestamps = conn.lrange(wholekey, 0, -1)

        for request_time in timestamps:
            request_ago = now - float(request_time)
            if request_ago < 24 * 60 * 60.0:
                rl1d[key] += 1
                tot1d += 1
                if request_ago < 60 * 60.0:
                    rl1h[key] += 1
                    tot1h += 1
                    if request_ago < 15 * 60.0:
                        rl15m[key] += 1
                        tot15m += 1
                        if request_ago < 5 * 60.0:
                            rl5m[key] += 1
                            tot5m += 1


    # order keys by one day count
    stat_log = logging.getLogger('stats.ratelimiter.keys')
    if all_keys:
        all_keys = sorted(all_keys, key=lambda k: (rl1d[k], rl1h[k], rl15m[k], rl5m[k])) # sort most requested ascenting
        #all_keys = sorted(all_keys, key=lambda k: rl5m[k]*12*24 + rl15m[k]*4*24 + rl1h[k]*24 + rl1d[k]) # sort most requests ascenting weighted to show most recent last
        #all_keys = sorted(all_keys, key=lambda k: (rl5m[k], rl15m[k], rl1h[k], rl1d[k])) # sort most recent requests ascending
        max_key_length = max(len(key) for key in all_keys)
        stat_log.debug('%s\t   5m\t  15m\t   1h\t   1d', 'key'.ljust(max_key_length))
        for key in all_keys:
            if not min_daily_count or rl1d[key] >= min_daily_count: 
                stat_log.info('(%s)\t%5d\t%5d\t%5d\t%5d', key.ljust(max_key_length), rl5m[key], rl15m[key], rl1h[key], rl1d[key])

    stat_log = logging.getLogger('stats.ratelimiter.totals')
    stat_log.debug('   5m\t  15m\t   1h\t   1d')
    stat_log.info('%5d\t%5d\t%5d\t%5d', tot5m, tot15m, tot1h, tot1d)


def manual_blocks(redis_host, namespace):
    """
    Gather and show information on manual blocks
    """
    # manual blocks
    conn = redis.Redis(redis_host)
    l_namespace = len(namespace)
    blocks = {}
    log = logging.getLogger('stats.blocks')
    keys = conn.keys(namespace + '*:block')
    if keys:
        for wholekey in keys:
            # remove namespace and :block
            ttl = conn.ttl(wholekey)
            # ttl will be None for last second of its life
            if ttl is None:
                ttl = 1
            key = wholekey[l_namespace:-6]
            blocks[key] = ttl

        blocks = sorted(blocks.iteritems(), key=lambda k: k[1])

        log.debug('block_key    hours:minutes:seconds remaining')
        for key, seconds in blocks:

            hours = seconds // 3600
            seconds = seconds % 3600
            minutes = seconds // 60
            seconds = seconds % 60

            log.info('%s\t\t%02d:%02d:%02d', key, hours, minutes, seconds)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='RateLimiter Stats')
    parser.add_argument('--host', action='store', dest='host', default='localhost', help='Redis Server Host (default %(default)s)')
    parser.add_argument('--namespace', action='store', dest='namespace', default='ratelimiter:', help='ratelimiter key namespace (default "%(default)s")')
    parser.add_argument('-r', '--hide-ratelimit-stats', action='store_true', dest='hide_ratelimit', default=False, help='Hide stats on RateLimiter requests (default %(default)s)')
    parser.add_argument('-b', '--hide-manual-blocks', action='store_true', dest='hide_manual_block', default=False, help='Hide stats on force blocked requests (default %(default)s)')
    parser.add_argument('-c', '--min-daily-count', action='store', dest='min_daily_count', default=False, type=int, help='Hide requests with daily count less than n (default %(default)s)')

    args = parser.parse_args()
    logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s %(message)s', level=logging.DEBUG, stream=sys.stdout)

    log = logging.getLogger('stats')

    if not args.hide_ratelimit:
        try:
            ratelimiter_stats(args.host, args.namespace, args.min_daily_count)
        except Exception, e:
            log.exception(e)

    if not args.hide_manual_block:
        try:
            manual_blocks(args.host, args.namespace)
        except Exception, e:
            log.exception(e)
    
