#!/usr/bin/env python3

"""
From a list of names, list of one-way fixes, and list of one-way blocks,
produce an appropriately matched pairing of name to name
Output is provided as a set of .zip files in the directory the script is called
from, each named after a participant. Unzipping that file will reveal a text
file which provides the name of the participant they are paired with.

Nomenclature:
    Names (list of name) - The names that will be paired with each other
    Pairs (name -> pick) - Final output, each name is given a pick
    Fixed (name -> pick) - A pair that must exist in the final set
    Block (name -> set of pick) - Name cannot be paired with any in the set

provide the name of a JSON file containing this info as an argument
It should be in the following format
'names' is the list of participants,
 - in the example, name1 and name2 are participants
'force' is a map of who must be given who,
 - in the example, name1 must be given name2
'block' is a map of who must not be given who,
 - in the example, name2 must NOT be given name1 or name3
'twoway_force' will force the those listed to be paired
 - in the example, name3 must be given name4 and name4 must be given name3
'twoway_block' will force those listed to not be paired
 - in the example, name4 will not be given name5, and name5 will not be given name4
{
  "names": [ "name1", "name2", ... ],
  "force": { "name1": "name2", ... },
  "block": { "name2": [ "name1", "name3", ... ], ... },
  "twoway_force": [ [ "name3", "name4" ], ... ],
  "twoway_block": [ [ "name4", "name5" ], ... ]
}
"""

import argparse
import json
import os
import random
import sys

from copy import deepcopy
from datetime import datetime
from functools import reduce
from zipfile import ZipFile

_debug = False

# For secrecy padding
BASE64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890+/='

# Validate that a given name is in names, and report if not
def check_name(name, names, member = None):
    if name not in names:
        if member is not None:
            sys.exit(name + " in '" + member + "' is not a participant");
        sys.exit("Invalid participant " + name);


# From the JSON file, load names, fixed, and block
def load_data(data):
    # Everyone who is participating
    names = data["names"]

    # One way enforcement: key must be paired with value
    fixed = data["force"]
    # Check validity
    for key,value in fixed.items():
        check_name(key, names, "force");
        check_name(value, names, "force");

    # One way enforcement: key must not be paired with value
    block = data["block"]
    # Check validity
    for key,value in block.items():
        check_name(key, names, "block");
        if type(value) is not list:
            value = [value];
        block[key] = set(value);
        for name in block[key]:
            check_name(name, names, "block");

    # Two way enforcement: Entries fixed to each other
    givens = data["twoway_force"]
    # Add a one way enforcement both ways
    for given in givens:
        left = given[0];
        right = given[1];
        # And check validity
        check_name(left, names, "twoway_force");
        check_name(right, names, "twoway_force");
        # If they've already been fixed, we'd overwrite it ahead
        if left in fixed or right in fixed:
            sys.exit("Conflicting force requirements with " + left + " and " + right)
        # Finally, add the enforcement
        fixed[left] = right;
        fixed[right] = left;

    # Two way enforcement: Entries must not be paired with eachother
    forbids = data["twoway_block"]
    for forbid in forbids:
        left = forbid[0];
        right = forbid[1];
        # Also, check validity!
        check_name(left, names, "twoway_block");
        check_name(right, names, "twoway_block");
        # Then set up blocks
        if left in block: block[left].add( right );
        else: block[left] = set([right]);
        if right in block: block[right].add( left );
        else: block[right] = set([left]);
    # TODO: Add more validation
    return (names,fixed,block)


# Given a name, a list of unchosen names, and the fix/block lists,
# return all the possible names they could be paired with
def eligible_for(name, picks, fixed, block):
    # If they've got someone who must go to them
    if name in fixed:
        return [fixed[name]]

    # Final list of eligible picks
    finals = [];
    for person in picks:
        # We can't pick ourselves
        if person == name:
            continue;
        # And we can't pick anyone who we blocked
        if name in block and person in block[name]:
            continue;
        finals.append(person);

    return finals;


# Given the names and fix/block lists, randomly generate pairs
def gen_pairs(names, fixed, block):
    unpaired = names.copy();
    picks_left = names.copy();
    for pick in fixed.values():
        picks_left.remove(pick)
    pairs = dict();
    ret = gen_pairs_rec(pairs, unpaired, picks_left, deepcopy(fixed), deepcopy(block));
    if ret is None:
        sys.exit("Pair generation failed! Too many constraints.");
    return ret;


# Try to pick a pair, functional style
# On success, call recursively with the pair eliminated from the data
# If the recursive call fails, pick again, then try another recursive call
# If all recursive calls fail, fail up to the next level, and so on
def gen_pairs_rec(pairs, unpaired, picks_left, fixed, block):
    # Base case - all pairs chosen
    if len(unpaired) == 0 and len(picks_left) == 0:
        return pairs;

    # Who we'll try to match up
    who = random.choice(unpaired);
    # Give priority to those with fixed pairs
    for priority in fixed.keys():
        if priority in unpaired:
            who = priority;
            break;

    while True:
        # Valid picks. If we've exhausted all valid picks, fail and see if
        # a different configuration works
        options = eligible_for(who, picks_left, fixed, block)
        if len(options) == 0:
            if _debug:
                print("Found no options for " + who);
                print(str(pairs));
            return None

        # Pick a random valid choice
        pick = random.choice(options);

        # Copy all the data to give on to the next pick
        pairs_copy = pairs.copy();
        unpaired_copy = unpaired.copy();
        picks_left_copy = picks_left.copy();

        # Modify that data so it's correct for the next pick
        pairs_copy[who] = pick;
        if who in unpaired:
            unpaired_copy.remove(who);
        if pick in picks_left:
            picks_left_copy.remove(pick);


        if _debug:
            print("Paired " + who + " with: " + pick);
            print("\tPicks Left: " + str(picks_left_copy));
            print("\tUnpaired: " + str(unpaired_copy));
            print("\tfixes: " + str(fixed));
            print("\tblocks: " + str(block));
        ret = gen_pairs_rec(pairs_copy, unpaired_copy, picks_left_copy, deepcopy(fixed), deepcopy(block));
        # If the recursive call succeeded, we found our pairs, pass them up
        if ret is not None:
            return ret;

        # Otherwise, we failed! Block this pick and try a different one
        if _debug:
            print("Due to restrictions below " + who + " cannot pair with " + pick);
        if who in block:
            block[who].add(pick);
        else:
            block[who] = set([pick]);


def main():
    parser = argparse.ArgumentParser(description=
            "Anonymously and randomly generate pairs of people, with support "
            "for mandatory pairs and exclusion. Output generated as zip files "
            "named after each participant with their selected pair inside.");
    parser.add_argument("param_file", metavar="FILE", type=str,
            help='file containing data to generate pairs');
    parser.add_argument("-d", "--dry-run", help="generate no output files",
            action='store_true');
    parser.add_argument("-v", "--verbose", help="add some extra debug output",
            action='store_true');
    parser.add_argument("-vv", "--very-verbose", help="add lots of extra debug output",
            action='store_true');
    parser.add_argument("-c", "--cheat", help="show final results",
            action='store_true');
    parser.add_argument("-s", "--seed", metavar="SEED", type=int,
            help="Seed RNG with SEED",
            default=int(datetime.now().timestamp() * 1000000000))
    #parser.add_argument("-o", "--out", metavar="OUT", type=str,
    #        help='output directory for zip files', default="");
    args = parser.parse_args();

    random.seed(args.seed);

    start_time = datetime.now().timestamp();

    if args.very_verbose:
        global _debug;
        _debug = True;

    # Who's gonna be involved in selection
    # List of string. Everyone who is participating in pairing process
    names = []
    # Dictionary matching string to string. Each key and value will be in names
    # Pairs that must show up in the output
    fixed = {}
    # Dictionary matching string to set of string.
    # Each key will be in names, and each element of the set will be in names
    # In the final output, key cannot be matched with any element of value
    block = {}
    with open(args.param_file, "r", encoding="utf-8") as json_file:
        data = json.load(json_file);
        names,fixed,block = load_data(data);

    if _debug or args.verbose:
        print("RNG Seed is: " + str(args.seed));
    out = gen_pairs(names, fixed, block);

    if _debug or args.cheat:
        print(out);
    if args.dry_run:
        return;

    # How long each file must be, to ensure file size doesn't give away names
    # Length of longest name + 5
    pad_to = len(reduce(lambda l, r: l if len(l) > len(r) else r, out.values())) + 5;

    # Generate the output files
    for name, pair in out.items():
        # Write the given name into this file
        filename = str(os.getpid()) + "-assignment.txt";
        with open(filename, 'w') as writer:
            writer.write(pair)
            writer.write('\n')
            # Pad for secrecy
            writer.write('Secret Padding: ')
            for i in range(len(pair) + 1, pad_to):
                writer.write(random.choice(BASE64))
            writer.write('\n');
        # Zip this anonymous file into a zip file with the name of the person
        # who it was given to, to allow delivery
        zipname = name.replace(" ", "_") + ".zip";
        with ZipFile(zipname, "w") as azip:
                azip.write(filename);
        if _debug or args.verbose:
            print(f"Wrote result for {name} into {zipname}");
    delta_time = datetime.now().timestamp() - start_time;
    print(f"Wrote results for {len(out)} participants in {delta_time:0.5f}s");

if __name__ == "__main__":
    main()
