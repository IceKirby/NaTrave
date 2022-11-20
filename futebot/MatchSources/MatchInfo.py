from collections import namedtuple

class MatchInfo:
    def __init__(self):
        
        # General Details
        InfoDetails = namedtuple('InfoDetails', 'date time stadium')
        self.details = InfoDetails(date="2000-01-01", time="00:00", stadium="N/D")
        
        # Match State
        InfoState = namedtuple('InfoState', 'period time home_score away_score')
        self.state = InfoState(period=None, time=0, home_score=0, away_score=0)
        
        # Competition Information
        InfoTour = namedtuple('InfoTour', 'name stage round')
        self.tour = InfoTour(name="N/D", stage=None, round=None)
        
        # Teams Information
        InfoTeam = namedtuple('InfoTeam', 'name players coach formation')
        self.home_team = InfoTeam(name="N/D", players=[], coach=None, formation="N/D")
        self.away_team = InfoTeam(name="N/D", players=[], coach=None, formation="N/D")
        
        # Referees
        self.referees = []
        
        # Plays Feed
        self.feed = []
    
    def add_player(self):
        pass
    
    def add_coach(self):
        pass
    
    def add_referee(self):
        pass
    
    def add_feed_entry(self):
        pass
        
        
