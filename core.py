#!/usr/bin/env python

import sys
import json
from random import shuffle
from operator import methodcaller, itemgetter
from itertools import product, chain, combinations, permutations
from functools import lru_cache

from alonzo.church import sequential, parallel, branch



class Geocache():
    def __init__(self):
        with open('./data/countries+states+cities.json', 'r') as handle:
            self.countries = json.load(handle)

    @lru_cache(maxsize=1024)
    def is_country(self, token):
        for country in self.countries:
            if token == country['name']:
                return True
            if token == country['iso2']:
                return True
            if token == country['iso3']:
                return True
            if token == country['native']:
                return True
            for translation in country['translations'].values():
                if token == translation:
                    return True
        return False

    @lru_cache(maxsize=1024)
    def is_region(self, token):
        for country in self.countries:
            for region in country['states']:
                if token == region['name']:
                    return True
                if token == region['iso2']:
                    return True
                if token == region['iso3166_2']:
                    return True
        
        return False

    @lru_cache(maxsize=1024)
    def is_city(self, token):
        for country in self.countries:
            for region in country['states']:
                for city in region['cities']:
                    if token == city['name']:
                        return True
        return False

    def validate(self, lrc):
        l, r, c, d = lrc['L'], lrc['R'], lrc['C'], lrc['D']
        candidates = self.countries
        # 1. Filter by Country (C)
        if c:
            candidates = [cnt for cnt in candidates if 
                          c in (cnt['name'], cnt['iso2'], cnt['iso3'], cnt['native']) or 
                          c in cnt['translations'].values()]
            if not candidates: return False

        # 2. Filter by Region (R)
        if r:
            valid_regions = []
            for cnt in candidates:
                for state in cnt['states']:
                    if r in (state['name'], state['iso2'], state['iso3166_2']):
                        # We keep track of the specific state objects for the next step
                        valid_regions.append(state)
            
            if not valid_regions: return False
            state_candidates = valid_regions
        else:
            # If no R was provided, but we have L, we need all states for city lookup
            state_candidates = [state for cnt in candidates for state in cnt['states']]
        # 3. Filter by Locality (L)
        if l:
            # If D is True, we skip checking the database for L's existence.
            if d:
                return True
            # Otherwise, check if L exists within our valid state/country candidates
            for state in state_candidates:
                for city in state['cities']:
                    if l == city['name']:
                        return True
            return False
        return True


def location_generator():
    with open('train.txt') as handle:
        locs = list(handle)
    shuffle(locs)
    locs = map(methodcaller('strip'), locs)
    locs = map(methodcaller('strip', '"'), locs)
    yield from locs


def strip_whitespace(location_string):
    return methodcaller('strip')(location_string)


flatten_sep_mapping = str.maketrans({'-': ',', '(': ',',
                                     ')': '', 
                                     '/': ',', '&': ',',})
def flatten_separators(location_string):
    flat = location_string.translate(flatten_sep_mapping)
    flat = flat.replace(' or ', ',')
    flat = flat.replace(' and ', ',')
    return flat
    
def tokenize(location_string):
    tokens = methodcaller('split', ',')(location_string)
    tokens = map(methodcaller('strip'), tokens)
    tokens = tuple(tokens)
    return tokens 

def stop():
    vv = input('##########')
    if vv == 'q':
        sys.exit(0)
    elif vv == 'b':
        return breakpoint
    else:
        return bool


def assemble_all_possible_triplets(tkns, arr, degraded_flags):
    # Zip tokens with their (L, R, C) bools
    items = list(zip(tkns, arr, degraded_flags))
    slot_names = ['L', 'R', 'C']
    all_triplets = []

    for r in range(1, 4):
        # Pick a subset of tokens of length r
        for subset in combinations(items, r):
            # Pick r slots out of the 3 available (L, R, C)
            for slot_indices in permutations(range(3), r):
                
                # Validation: Does every token fit its assigned slot?
                if all(subset[i][1][slot_indices[i]] for i in range(r)):
                    # Create the LRC record
                    record = {"L": None, "R": None, "C": None, "D": False}
                    for i in range(r):
                        tkn_name = subset[i][0]
                        slot_name = slot_names[slot_indices[i]]
                        is_degraded = subset[i][2]
                        record[slot_name] = tkn_name
                        if slot_name == 'L' and is_degraded:
                            record['D'] = True
                    
                    all_triplets.append(record)
    
    return all_triplets

def is_degraded(array):
    if array == (False, False, False,):
        return True
    return False

def degrade(array):
    if array == (False, False, False,):
        return (True, False, False,)
    return array

def subsumption_filter(all_triplets):
    """
    Filters out redundant triplets. 
    A triplet is redundant if another triplet 'covers' all its non-None values.
    """
    # 1. Sort triplets by the number of filled slots (descending)
    # This ensures we compare "smaller" triplets against "larger" ones first
    sorted_triplets = sorted(
        all_triplets, 
        key=lambda x: sum(1 for v in x.values() if v is not None), 
        reverse=True
    )
    
    primes = []
    for candidate in sorted_triplets:
        is_subsumed = False
        
        for p in primes:
            # Check if 'p' covers 'candidate'
            # A cover means: for every slot in candidate, p has the same value
            match = True
            for slot in ['L', 'R', 'C']:
                val = candidate[slot]
                if val is not None and p[slot] != val:
                    match = False
                    break
            
            if match:
                is_subsumed = True
                break
        
        # If no existing 'prime' triplet covers this candidate, it's a new Prime
        if not is_subsumed:
            primes.append(candidate)
            
    return primes

def rank_triplets(primes):
    """
    Sorts primes so the record with the most data is at index 0.
    Does not delete any data.
    """
    def score(t):
        # Base score starts with density (r)
        # r=3 gets 300, r=2 gets 200, r=1 gets 100
        r_score = sum(1 for slot in ['L', 'R', 'C'] if t[slot] is not None) * 100
        # Verification Bonus: If it's not degraded, it's more 'solid'
        v_bonus = 50 if not t.get('D', False) else 0
        ## Tie-breaker: Favor triplets with a Country (C) as it's the strongest anchor
        #anchor_bonus = 25 if t['C'] is not None else 0
        return r_score + v_bonus
    return sorted(primes, key=score, reverse=True)

def make_nice(lrc):
    return {'@type': 'Place',
            'addressLocality': lrc['L'],
            'addressRegion': lrc['R'],
            'addressCountry': lrc['C'],}



def main():
    steps = (strip_whitespace,
             flatten_separators,
             tokenize,)
    proc = sequential(steps)           

    db = Geocache()
    is_fns = (db.is_city,
              db.is_region,
              db.is_country,)

    for ll in location_generator():
        print('---string')
        print(ll)
        print('---tokens')
        groups = methodcaller('split', ';')(ll)
        for tkns in groups:
            tkns = proc(tkns)
            print(tkns)
            arr = map(parallel(is_fns), tkns) 
            arr = tuple(arr)
            degraded_flags = map(is_degraded, arr)
            degraded_flags = tuple(degraded_flags)
            arr = map(degrade, arr)
            arr = tuple(arr)
            triplets = assemble_all_possible_triplets(tkns, arr, degraded_flags)
            print('---triplets')
            for each in triplets:
                print(each)
            triplets = filter(db.validate, triplets)
            triplets = tuple(triplets)
            print('---validated')
            for each in triplets:
                print(each)
            primes = subsumption_filter(triplets)
            print('---subsum')
            for pp in primes:
                 print(pp)
            primes = rank_triplets(primes)
            print('---ranked')
            for pp in primes:
                 print(pp)
            output = map(make_nice, primes)
            for each in output:
                print(each)
        stop()()

if __name__ == '__main__':
    main()
