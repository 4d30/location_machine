#!/usr/bin/env python

import json
from functools import lru_cache

from alonzo.church import parallel

_filename = './data/countries+states+cities.json'
with open(_filename, 'r') as handle:
    countries = json.load(handle)


@lru_cache(maxsize=1024)
def is_country(token):
    for country in countries:
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
def is_region(token):
    for country in countries:
        for region in country['states']:
            if token == region['name']:
                return True
            if token == region['iso2']:
                return True
            if token == region['iso3166_2']:
                return True
    return False


@lru_cache(maxsize=1024)
def is_city(token):
    for country in countries:
        for region in country['states']:
            for city in region['cities']:
                if token == city['name']:
                    return True
    return False


def validate(lrc):
    l, r, c, d = lrc['L'], lrc['R'], lrc['C'], lrc['D']
    candidates = countries
    # 1. Filter by Country (C)
    if c:
        candidates = [cnt for cnt in candidates if
                      c in (cnt['name'], cnt['iso2'],
                            cnt['iso3'], cnt['native']) or
                      c in cnt['translations'].values()]
        if not candidates:
            return False
    # 2. Filter by Region (R)
    if r:
        valid_regions = []
        for cnt in candidates:
            for state in cnt['states']:
                if r in (state['name'], state['iso2'],
                         state['iso3166_2']):
                    # We keep track of the specific state objects
                    #  for the next step
                    valid_regions.append(state)
        if not valid_regions:
            return False
        state_candidates = valid_regions
    else:
        # If no R was provided, but we have L, we need all
        # states for city lookup
        state_candidates = [state for cnt in candidates
                            for state in cnt['states']]
    # 3. Filter by Locality (L)
    if l:
        # If D is True, we skip checking the database for L's
        # existence.
        if d:
            return True
        # Otherwise, check if L exists within our valid
        # state/country candidates
        for state in state_candidates:
            for city in state['cities']:
                if l == city['name']:
                    return True
        return False
    return True


def is_degraded(array):
    if array == (False, False, False,):
        return True
    return False


def degrade(array):
    if array == (False, False, False,):
        return (True, False, False,)
    return array

lookup_token = parallel((is_city,
                         is_region,
                         is_country,))
