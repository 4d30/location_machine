#!/usr/bin/env python

import sys
from random import shuffle
from operator import methodcaller

from . import text_utils
from . import geocache
from . import combinatorics



def extract_locations(location_string):
    groups = text_utils.split_into_groups(location_string)
    for tkns in groups:
        tkns = text_utils.preprocess(tkns)
        tkns = tuple(filter(bool, tkns))
        arr = tuple(map(geocache.lookup_token, tkns))

        degraded_flags = map(geocache.is_degraded, arr)
        degraded_flags = tuple(degraded_flags)
        arr = tuple(map(geocache.degrade, arr))

        triplets = combinatorics.assemble(tkns, arr, degraded_flags)
        triplets = tuple(filter(geocache.validate, triplets))

        primes = combinatorics.subsumption_filter(triplets)
        primes = combinatorics.rank_triplets(primes)
        output = map(text_utils.make_nice, primes)
        yield from output


if __name__ == '__main__':
    def main():
        import json
        for ll in location_generator():
            print(ll)
            out = process(ll)
            for each in out:
                print(json.dumps(each, indent=2))
            stop()()


    def _location_generator():
        with open('data/test.txt') as handle:
            locs = list(handle)
        shuffle(locs)
        locs = map(methodcaller('strip'), locs)
        locs = map(methodcaller('strip', '"'), locs)
        yield from locs


    def _stop():
        vv = input('##########')
        if vv == 'q':
            sys.exit(0)
        elif vv == 'b':
            return breakpoint
        else:
            return bool

    main()
