import configparser

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
    return list(map(lambda x: x.strip(), lines))

def load_names():
    global alt_club_names
    global alt_tour_names
    
    if alt_club_names == None:
        alt_club_names = []
        with open('futebot/FormattingData/alt_club_names.ini', encoding='utf-8') as f:
            for line in f:
                if len(line) > 1:
                    alt_club_names.append(split_entries(line))

    if alt_tour_names == None:
        alt_tour_names = []
        with open('futebot/FormattingData/alt_tour_names.ini', encoding='utf-8') as f:
            for line in f:
                if len(line) > 1:
                    alt_tour_names.append(split_entries(line))
