#!/usr/bin/env python

from operator import methodcaller

from .alonzo.church import sequential


def strip_whitespace(location_string):
    return methodcaller('strip')(location_string)


_flatten_sep_mapping = str.maketrans({'-': ',', '(': ',',
                                      ')': '', '/': ',',
                                      '&': ','})


def flatten_separators(location_string):
    flat = location_string.translate(_flatten_sep_mapping)
    flat = flat.replace(' or ', ',')
    flat = flat.replace(' and ', ',')
    return flat


def tokenize(location_string):
    tokens = methodcaller('split', ',')(location_string)
    tokens = map(methodcaller('strip'), tokens)
    tokens = tuple(tokens)
    return tokens


def split_into_groups(location_string):
    return methodcaller('split', ';')(location_string)



def make_nice(lrc):
    return {'@type': 'Place',
            'addressLocality': lrc['L'],
            'addressRegion': lrc['R'],
            'addressCountry': lrc['C']}

preprocess = sequential((strip_whitespace,
                         flatten_separators,
                         tokenize,))
