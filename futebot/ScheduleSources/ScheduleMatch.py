import enum
from BotUtils import format_str, format_time, format_date

class ScheduleState(enum.Enum):
    upcoming = 0
    ongoing = 1
    finished = 2

class ScheduleMatch:
    
    def __init__(self):
        self.date = None
        self.time = None
        self.tour = None
        self.state = ScheduleState.upcoming
        self.is_aborted = False
        
        self.is_women_match = False
        self.is_youth_match = False
        
        self.home_team = None
        self.away_team = None
        
        self.home_sufix = None
        self.away_sufix = None
        
        self.home_team_alts = []
        self.away_team_alts = []
        
        self.home_score = None
        self.away_score = None
        self.home_penalty = None
        self.away_penalty= None
        
        self.source = None
        self.url = None
    
    def get_score(self, team=None):
        if self.home_penalty != None and self.away_penalty != None:
            home_score = "{} ({})".format(self.home_score, self.home_penalty)
            away_score = "({}) {}".format(self.away_penalty, self.away_score)
        else:
            home_score = "{}".format(self.home_score)
            away_score = "{}".format(self.away_score)
            
        if team == None:
            return "{} x {}".format(self.home_score, self.away_score)
        elif team == "home":
            return home_score
        elif team == "away":
            return away_score
    
    def get_post_title(self, template):
        return format_str(template,
            Campeonato = self.tour,
            CampeonatoFase = "N/D",
            CampeonatoRodada = "N/D",
            Estadio = "N/D",
            TimeCasa = self.home_team,
            Mandante = self.home_team,
            TimeFora = self.away_team,
            Visitante = self.away_team,
            PlacarFinal = self.get_score(),
            PlacarCasa = self.get_score("home"),
            PlacarFora = self.get_score("away"),
            PlacarMandante = self.get_score("home"),
            PlacarVisitante = self.get_score("away"),
            Data = format_date(self.date),
            Horario = format_time(self.time)
        )
    
    def get_post_content(self, template, match_url):
        return format_str(template,
            Campeonato = self.tour,
            CampeonatoFase = "N/D",
            CampeonatoRodada = "N/D",
            Estadio = "N/D",
            TimeCasa = self.home_team,
            Mandante = self.home_team,
            TimeFora = self.away_team,
            Visitante = self.away_team,
            PlacarFinal = self.get_score(),
            PlacarCasa = self.get_score("home"),
            PlacarFora = self.get_score("away"),
            PlacarMandante = self.get_score("home"),
            PlacarVisitante = self.get_score("away"),
            Data = format_date(self.date),
            Horario = format_time(self.time),
            MatchThreadUrl = "" if not match_url else "**Match  Thread:** " + match_url
        )
    
    def __repr__(self):
        return "<ScheduleMatch ([{}] {} x {} ({}, {})) [Women: {}, Youth: {}]- URL: {}>"\
            .format(self.tour, self.home_team, self.away_team, self.date, self.time, self.is_women_match, self.is_youth_match, self.url)
