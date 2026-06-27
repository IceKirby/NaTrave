import os
import requests
import re
import NameTranslator
from urllib.parse import urlencode
from TournamentSources.BaseTournament import BaseTournament

class Tournament365Scores(BaseTournament):
    def __init__(self, tour_name):
        super().__init__(tour_name)
        self.api_url = self.find_api_url()
        self.is_valid = self.api_url != None
    
    def update_tour_data(self):
        data = self.get_raw_data()

        if not data:
            return
        
        self.reset_tour_data()

        standings = data["standings"][0]
        rows = standings["rows"]

        if rows:
            for r in rows:
                self.add_standing_row(
                    NameTranslator.get_standard_team_name(r["competitor"]["name"]),
                    r["position"],
                    r["points"],
                    r["gamesPlayed"],
                    r["gamesWon"],
                    r["gamesEven"],
                    r["gamesLost"],
                    r["for"],
                    r["against"],
                    r["ratio"],
                    r["trend"]
                )


    def get_raw_data(self):
        if not self.api_url:
            return
        
        response = requests.get(self.api_url)
        res = response.json()
        return res
    
    def find_api_url(self):
        all_tours = self.get_raw_tours()

        if not all_tours:
            return None
        
        competitions = all_tours["competitions"]
        for c in competitions:
            if NameTranslator.get_standard_tour_name(c["name"]) == self.tour_name:
                id = c["id"]
                return f"https://webws.365scores.com/web/standings/?appTypeId=5&langId=31&timezoneName=Etc/GMT+3&userCountryId=21&competitions={id}&live=false&withSeasonsFilter=true"
        
    
    def get_raw_tours(self):
        base_url = "https://webws.365scores.com/web/competitions/?"
        params = {
            'appTypeId': 5,
            # 'langId': 1, # English
            'langId': 31, # PT-BR
            'sports': 1,
            'timezoneName': 'Etc/GMT+3',
            'userCountryId': 21,
            'withSeasons': True,
            'type': 'stats'
        }
        response = requests.get(base_url + urlencode(params))
        sch = response.json()
        return sch