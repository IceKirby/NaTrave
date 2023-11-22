import re
import hashlib
import requests
import NameTranslator
from ScheduleSources.GEQueryFormat import query_format
from ScheduleSources.ScheduleMatch import ScheduleMatch, ScheduleState
from ScheduleSources.BaseSchedule import BaseSchedule
from BotUtils import normalize_name

class ScheduleGE(BaseSchedule):
    
    def get_day_schedule(self, day):
        if not day in self.cached_schedules:
            sch = self.get_raw_schedule(day)
            formatted = self.format_schedule(sch)
            if formatted == None:
                return None
            self.cached_schedules[day] = formatted
        
        return self.cached_schedules[day]
    
    def get_raw_schedule(self, day):
        # query = query_format.encode('utf-8');
        # 
        # m = hashlib.sha256()
        # m.update(query)
        # hashed = m.hexdigest()
        hashed = "a216d962a6b843d5dcb6f60909368d07c6f666bd471e7f378638f0076d938dd4"
        
        req_url = 'https://geql.globo.com/graphql?variables={"params":"'+day+'"}&extensions={"persistedQuery":{"version":1,"sha256Hash":"'+hashed+'"}}'
        
        response = requests.get(req_url)
        return response.json()
        
    def format_schedule(self, data):
        try:
            data = data["data"]["championshipsAgenda"]
        except Exception as e:
            return None
        
        result = []
        
        for tour in data:
            matches = tour["past"] + tour["now"] + tour["future"]
            tour_name = tour["championship"]["name"]
            
            if not self.is_football_tour(tour_name):
                continue
            
            for obj in matches:
                m = obj["match"]
                
                match = ScheduleMatch()
                match.date = m["startDate"]
                match.time = m["startHour"]
                match.tour = tour_name
                
                
                if obj in tour["future"]:
                    match.state = ScheduleState.upcoming
                elif obj in tour["now"]:
                    match.state = ScheduleState.ongoing
                elif obj in tour["past"]:
                    match.state = ScheduleState.finished
                
                if m["transmission"] and m["transmission"]["period"] and m["transmission"]["period"]["id"]:
                    match.is_aborted = m["transmission"]["period"]["id"] in ["CANCELADO", "ADIADO", "ABORTADO"]
                
                match.is_youth_match = self.is_youth_tour(tour_name)
                match.is_women_match = self.is_women_tour(tour_name)
                
                match.home_team = m["homeTeam"]["popularName"]
                match.away_team = m["awayTeam"]["popularName"]
                
                match.home_team_alts = self.get_alt_names(match.home_team)
                match.away_team_alts = self.get_alt_names(match.away_team)
                
                match.home_score = m["scoreboard"]["home"]
                match.away_score = m["scoreboard"]["away"]
                
                if m["scoreboard"]["penalty"] != None:
                    match.home_penalty = m["scoreboard"]["penalty"]["home"]
                    match.away_penalty = m["scoreboard"]["penalty"]["away"]
                
                if m["transmission"] != None:
                    match.url = m["transmission"]["url"]
                
                match.source = "GE"
                
                result.append(match)
        
        return result
        
    def is_women_tour(self, tour):
        tour_name = normalize_name(tour)
        if re.search(r"feminin[ao]", tour_name):
            return True
        if re.search(r"ladies", tour_name):
            return True
        
        return False
    
    def is_youth_tour(self, tour):
        tour_name = normalize_name(tour)
        if re.search(r"sub-[0-9]+", tour_name):
            return True
        if re.search(r"junior", tour_name):
            return True
        if re.search(r"futebol\sjr", tour_name):
            return True
        
        return False
    
    def is_football_tour(self, tour):
        tour_name = normalize_name(tour)
        if tour_name in ["nbb", "cblol"]:
            return False
        if re.search(r"league of legends", tour_name):
            return False
        return True

    def get_alt_names(self, name):
        result = [name]
        alt_names = NameTranslator.get_alt_names(name)
        
        return list(set(result + alt_names))
