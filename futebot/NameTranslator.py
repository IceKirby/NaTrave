import configparser
from BotUtils import normalize_name
from rapidfuzz import fuzz, distance

alt_club_names = None
alt_tour_names = None

def get_alt_club_names(name):
    load_names()
    
    for entry in alt_club_names:
        for n in entry:
            if name == n:
                return entry
    return []

def get_alt_tour_names(name):
    load_names()
    
    for entry in alt_tour_names:
        for n in entry:
            if name == n:
                return entry
    return []

def split_entries(str):
    lines = str.split(',')
    lines = [x for x in lines if len(x.strip()) > 0]
    return [lines[0].strip()] + list(map(lambda x: normalize_name(x, True), lines))

def load_names():
    global alt_club_names
    global alt_tour_names
    
    if alt_club_names == None:
        alt_club_names = []
        with open('futebot/FormattingData/alt_club_names.ini', encoding='utf-8') as f:
            for line in f:
                if len(line.strip()) > 1 and line[0] != "#":
                    alt_club_names.append(split_entries(line))

    if alt_tour_names == None:
        alt_tour_names = []
        with open('futebot/FormattingData/alt_tour_names.ini', encoding='utf-8') as f:
            for line in f:
                if len(line.strip()) > 1 and line[0] != "#":
                    alt_tour_names.append(split_entries(line))

def get_standard_team_name(name):
    load_names()
    return find_matching_name(name, alt_club_names)

def get_standard_tour_name(name):
    load_names()
    return find_matching_name(name, alt_tour_names)

def find_matching_name(base_name, entries):
    fuzz_rate = 0.86
    match_found = None
    name = normalize_name(base_name, True)

    for entry in entries:
        val = compare_with_alts(name, entry)
        if val > fuzz_rate:
            fuzz_rate = val
            match_found = entry
            if val >= 1:
                break
    
    if match_found:
        return match_found[0]
    else:
        return base_name

def compare_with_alts(name, alts):
    highest = 0
    for n in alts:
        j = distance.Jaro.similarity(name, n)
        d = distance.DamerauLevenshtein.normalized_similarity(name, n)
        f = (j + d) / 2
        if f > highest:
            highest = f
    return highest