#!/usr/bin/env python3
"""Count the total number of card images in resources/deck."""
import os
import re

DECK_DIR = os.path.join('resources', 'deck')

PATTERN = re.compile(r'^(\d+)\s+')

def count_deck(path=DECK_DIR):
    total = 0
    if not os.path.isdir(path):
        return total
    for fname in os.listdir(path):
        if fname.startswith('.'):
            continue
        m = PATTERN.match(fname)
        if m:
            total += int(m.group(1))
        else:
            total += 1
    return total

if __name__ == '__main__':
    print(count_deck())
