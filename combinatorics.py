#!/usr/bin/env python

from itertools import combinations, permutations


def assemble(tkns, arr, degraded_flags):
    # Zip tokens with their (L, R, C) bools
    items = tuple(zip(tkns, arr, degraded_flags))
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


def subsumption_filter(all_triplets):
    """
    Filters out redundant triplets.
    A triplet is redundant if another triplet 'covers' all its
    non-None values.
    """
    # 1. Sort triplets by the number of filled slots (descending)
    # This ensures we compare "smaller" triplets against "larger"
    # ones first
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
            # A cover means: for every slot in candidate,
            #  p has the same value
            match = True
            for slot in ['L', 'R', 'C']:
                val = candidate[slot]
                if val is not None and p[slot] != val:
                    match = False
                    break

            if match:
                is_subsumed = True
                break

        # If no existing 'prime' triplet covers this candidate,
        #  it's a new Prime
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
        r_score = sum(1 for slot in ['L', 'R', 'C']
                      if t[slot] is not None) * 100
        # Verification Bonus: If it's not degraded
        v_bonus = 50 if not t.get('D', False) else 0
        return r_score + v_bonus
    return sorted(primes, key=score, reverse=True)
