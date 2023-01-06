import re
import requests
import NameTranslator
from datetime import datetime, timedelta
from BotUtils import normalize_name
from ScheduleSources.ScheduleMatch import ScheduleMatch, ScheduleState
from urllib.parse import urlencode
from ScheduleSources.BaseSchedule import BaseSchedule

class Schedule365Scores(BaseSchedule):

    def get_day_schedule(self, day):
        if not day in self.cached_schedules:
            sch = self.get_raw_schedule(day)
            self.cached_schedules[day] = self.format_schedule(sch)
        
        return self.cached_schedules[day]
    
    def get_raw_schedule(self, day):
        match_date = "/".join(day.split("-")[::-1])
        
        base_url = "https://webws.365scores.com/web/games/allscores/?"
        params = {
            'appTypeId': 5,
            # 'langId': 1, # English
            'langId': 31, # PT-BR
            'startDate': match_date,
            'endDate': match_date,
            'onlyMajorGames': 'false',
            'sports': 1,
            'timezoneName': 'Etc/GMT+3',
            'userCountryId': 21
        }
        # print(base_url + urlencode(params))
        response = requests.get(base_url + urlencode(params))
        sch = response.json()
        return sch

    def format_schedule(self, data):
        data = data["games"]
        result = []
        
        for m in data:
            match = ScheduleMatch()
            
            start_time = datetime.strptime(m["startTime"], "%Y-%m-%dT%H:%M:%S-03:00")
            # start_time -= timedelta(hours=3)
            
            match.date = start_time.strftime("%Y-%m-%d")
            match.time = start_time.strftime("%H:%M:00")
            match.tour = m["competitionDisplayName"]
            match.is_aborted = m["statusText"] in ["Adiado", "Cancelado", "Abortado"]
            
            if m["statusGroup"] == 2:
                match.state = ScheduleState.upcoming
            elif m["statusGroup"] == 3:
                match.state = ScheduleState.ongoing
            elif m["statusGroup"] == 4:
                if m["statusText"] == "Suspenso":
                    match.state = ScheduleState.ongoing
                else:
                    match.state = ScheduleState.finished
                
            home = m["homeCompetitor"]
            away = m["awayCompetitor"]
            
            match.home_team = home["name"]
            match.away_team = away["name"]
            
            match.is_youth_match = is_youth_team(match.home_team) or is_youth_team(match.away_team)
            match.is_women_match = is_women_team(match.home_team) or is_women_team(match.away_team)
            
            match.home_sufix = get_name_sufix(match.home_team)
            match.away_sufix = get_name_sufix(match.away_team)
            
            match.home_team_alts = get_alt_names(home, match.home_sufix)
            match.away_team_alts = get_alt_names(away, match.away_sufix)
            
            if home["score"] != -1:
                match.home_score = home["score"]
            if away["score"] != -1:
                match.away_score = away["score"]
            
            if "penaltyScore" in home:
                match.home_penalty = home["penaltyScore"]
            if "penaltyScore" in away:
                match.away_penalty = away["penaltyScore"]
            
            match.source = "365Scores"
            id = m["id"]
            match.url = f"https://webws.365scores.com/web/game/?gameId={id}&langId=31&userCountryId=21"
            
            result.append(match)
        
        return result
    
def is_women_team(name):
    name = normalize_name(name)
    if re.search(r"\s\((w|f)\)$", name):
        return True
    return False

def is_youth_team(name):
    name = normalize_name(name)
    if re.search(r"\s(junior|youth)$", name):
        return True
    if re.search(r"\su-?[0-9]+$", name):
        return True
    if re.search(r"\ssub-?[0-9]+$", name):
        return True
    
    return False
            
def get_alt_names(data, name_sufix):
    result = []
    
    if "name" in data:
        result.append(data["name"])
    if "shortName" in data:
        result.append(data["shortName"])
    if "longName" in data:
        result.append(data["longName"])
    
    # Get alternative names, adding sufix if necessary
    if name_sufix == "":
        alt_names = NameTranslator.get_alt_names(data["name"])
    else:
        alt_names = NameTranslator.get_alt_names(remove_name_sufix(data["name"]))
        alt_names = list(map(lambda x: x + name_sufix, alt_names))
    
    result = list(set(result + alt_names))
    
    return result

def get_name_sufix(str):
    found = re.search(r"\s(\((w|f)\)|(junior|júnior|youth)|u-?[0-9]+|sub-?[0-9]+)$", str, flags=re.IGNORECASE)
    
    if found:
        return found.group(0)
    else:
        return ""

def remove_name_sufix(str):
    str = re.sub(r'\s\((w|f)\)', "", str, flags=re.IGNORECASE)
    str = re.sub(r'\s(junior|júnior|youth)$', "", str, flags=re.IGNORECASE)
    str = re.sub(r'\su-?[0-9]+$', "", str, flags=re.IGNORECASE)
    str = re.sub(r'\ssub-?[0-9]+$', "", str, flags=re.IGNORECASE)
    return str
