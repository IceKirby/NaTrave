import requests
import NameTranslator
from ScheduleSources.ScheduleMatch import ScheduleMatch
from BotUtils import normalize_name
from ErrorPrinter import print_error

from thefuzz import fuzz
from thefuzz import process

class BaseSchedule:
    def __init__(self):
        self.acceptable_fuzz_rate = 150
        self.cached_schedules = {}

    def clear_cached(self):
        self.cached_schedules = {}

    def get_day_schedule(self, day):
        pass

    def find_match(self, day, home_team, away_team, is_youth=None, is_women=None):
        try:
            schedule = self.get_day_schedule(day)
        except Exception as e:
            print_error(e)
            return None
        
        if not schedule:
            return None
        
        home_team = normalize_name(home_team)
        away_team = normalize_name(away_team)
        
        # Looks for the best match without any sufix
        normal_match = self.find_best_match(schedule, home_team, away_team)
        
        # Looks for the best match using Youth and/or Women team sufix
        sufix_match = None
        if is_youth or is_women:
            sufix_match = self.find_best_match(schedule, home_team, away_team, is_youth, is_women)
        
        if not sufix_match:
            return normal_match[0]
        else:
            return normal_match[0] if normal_match[1] > sufix_match[1] else sufix_match[0]
    
    def find_best_match(self, schedule, home_team, away_team, is_youth=None, is_women=None):
        # If no exact match, check for a close one
        highest = self.acceptable_fuzz_rate
        match_found = None
        
        # Check each Schedule object for a match with the input names
        for s in schedule:
            # Skip this entry if it doesn't match the Youth/Women setting
            if is_youth and not s.is_youth_match:
                continue
            if is_women and not s.is_women_match:
                continue
            
            # Add sufix if it's a Youth/Women match
            home_sufix, away_sufix = "", ""
            if is_youth or is_women:
                home_sufix = " " + normalize_name(s.home_sufix)
                away_sufix = " " + normalize_name(s.away_sufix)
            
            # Check how close the input names are to match's names
            home_ratio = self.compare_with_alts(home_team + home_sufix, s.home_team_alts)
            away_ratio = self.compare_with_alts(away_team + away_sufix, s.away_team_alts)
            sum = home_ratio + away_ratio
            
            # If perfect match is found, just return it immediately
            if sum >= 200:
                return (s, sum)
            
            # If ratio is higher than current one, replace it
            if sum > highest:
                highest = sum
                match_found = s
        
        if match_found:
            return (match_found, highest)
        else:
            return (match_found, 0)
        
    
    def find_followed_match(self, day, team, tour):
        try:
            schedule = self.get_day_schedule(day)
        except Exception as e:
            print_error(e)
            return None
        
        if not schedule:
            return None
        
        if team == "" and tour == "":
            return None
        
        team = normalize_name(team)
        tour = normalize_name(tour)
        
        res = []
        
        for s in schedule:
            s_home = normalize_name(s.home_team)
            s_away = normalize_name(s.away_team)
            s_tour = normalize_name(s.tour)
            
            if team == "":
                if tour == s_tour:
                    res.append(s)
            elif tour == "":
                if team == s_home or team == s_away:
                    res.append(s)
            else:
                if tour == s_tour and (team == s_home or team == s_away):
                    res.append(s)
        return res
    
    def format_schedule(self, data):
        pass

    def compare_with_alts(self, name, alts):
        highest = 0
        for n in alts:
            f = fuzz.ratio(name, normalize_name(n))
            if f > highest:
                highest = f
        return highest
    
    def get_fixed_tour_name(self, tour_name):
        alt_names = NameTranslator.get_alt_tour_names(tour_name)
        if len(alt_names) == 0:
            return tour_name
        return alt_names[0]
