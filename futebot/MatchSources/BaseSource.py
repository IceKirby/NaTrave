import re
import enum
from collections import namedtuple
from ErrorPrinter import print_error
from RetryRequest import requests_retry_session
from Models import MatchPeriod
from MatchSources.Statistics import Statistics

InfoDetails = namedtuple('InfoDetails', 'date time stadium')
InfoState = namedtuple('InfoState', 'period time home_score away_score home_penalty away_penalty')
InfoTour = namedtuple('InfoTour', 'name stage round')
InfoTeam = namedtuple('InfoTeam', 'name id players coach formation starting substitutes')
InfoPlayer = namedtuple('InfoPlayer', 'name id shirt_num position team')
InfoReferee = namedtuple('InfoReferee', 'name role')
InfoFeedPlay = namedtuple('InfoFeedPlay', 'period time type title body video')
InfoEventGoal = namedtuple('InfoEventGoal', 'period time team player_id, player_name own_goal')
InfoEventSub = namedtuple('InfoEventSub', 'period time team player_out player_in player_out_name player_in_name')
InfoEventCard = namedtuple('InfoEventCard', 'period time team player_id, player_name type')
InfoBroadcast = namedtuple('InfoBroadcast', 'name')
InfoVideo = namedtuple('InfoVideo', 'type period time url title duration source')

class PlayType(enum.Enum):
    normal = 0
    important = 1
    goal = 2
    own_goal = 3
    penalty = 4
    penalty_scored = 5
    penalty_missed = 6
    substitution = 7
    yellow_card = 8
    red_card = 9
    period_start = 10
    period_end = 11

class MatchSource:
    url = None

    def __init__(self, url=None):
        self.url = url
        self.priority = 0
        self.source_name = None
        self.reset_data()
    
    # Gets updated match data
    def get_data(self, url=None):
        if url == None:
            url = self.url
        self.url = url
        
        try:
            self.process_data(self.url)
        except Exception as e:
            print_error(e)
            return
    
    def fetch_data(self, url):
        try:
            response = requests_retry_session().get(url)
        except Exception as e:
            print_error(e)
            return
        
        if not response.ok:
            return
        
        return response.json()
    
    def reset_data(self):
        self.was_updated = False
        
        # Data Completion Tracking
        self.filled_data = {
            "base": 1,
            "date": 0,
            "time": 0,
            "stadium": 0,
            "tour": 0,
            "referees": 0,
            
            "score": 0,
            "period": 0,
            "match_time": 0,
            "stats": 0,
            
            "home_starting": 0,
            "home_subs": 0,
            "home_coach": 0,
            "home_formation": 0,
            
            "away_starting": 0,
            "away_subs": 0,
            "away_coach": 0,
            "away_formation": 0,
            
            "events_goals": 0,
            "events_cards": 0,
            "events_subs": 0,
            "feed": 0,
            
            "broadcast": 0,
            "video": 0
        }
        self.stats = Statistics()
        
        self.set_details()
        self.set_state()
        self.set_tour()
        self.set_team(True)
        self.set_team(False)
        self.players_ref = {}
        
        # Referees
        self.referees = []
        
        # Plays Feed
        self.feed = []
        
        # Events  
        self.goals = []
        self.subs = []
        self.cards = []
        
        # Misc
        self.broadcast = []
        self.videos = []
        
    
    def process_data(self, url):
        return None
    
    ### Main Properties Setters ###
    def set_details(self, date="2000-01-01", time="00:00", stadium="N/D"):
        self.details = InfoDetails(date, time, stadium)
        
        if stadium != "N/D":
            self.filled_data["stadium"] = 1
    
    def set_state(self, period=MatchPeriod.upcoming, time="0", home_score=0, away_score=0, home_penalty=None,  away_penalty=None):
        self.state = InfoState(period, time, home_score, away_score, home_penalty, away_penalty)
        
        self.filled_data["period"] = period.value
        self.filled_data["match_time"] = 1
        if home_score >= 0:
            self.filled_data["score"] += 1
        if home_penalty != None:
            self.filled_data["score"] += 1
        
    def set_tour(self, name="N/D", stage="N/D", round="N/D"):
        self.tour = InfoTour(name, stage, round)
        
        if name != "N/D":
            self.filled_data["tour"] += 1
        if stage != "N/D":
            self.filled_data["tour"] += 1
        if round != "N/D":
            self.filled_data["tour"] += 1
    
    def set_team(self, is_home, id=0, name="N/D", players=[], coach="N/D", formation="N/D", starting = [], substitutes = []):
        new_team = InfoTeam(name, id, players, coach, formation, starting, substitutes)
        if is_home:
            self.home_team = new_team
            self.stats.set_names(home=name)
        else:
            self.away_team = new_team
            self.stats.set_names(away=name)
        
        side = "home" if is_home else "away"
        self.filled_data[side + "_coach"] = 1 if coach != "N/D" else 0
        self.filled_data[side + "_formation"] = 1 if formation != "N/D" else 0
        self.filled_data[side + "_starting"] = len(starting)
        self.filled_data[side + "_subs"] = len(substitutes)
        
        
    ### Add People ###
    def add_player(self, team, name, position, id, shirt_num):
        player = InfoPlayer(name.strip(), id, shirt_num, position, team)
        self.players_ref[id] = player
        if team == "home":
            self.home_team.players.append(player)
        else:
            self.away_team.players.append(player)
    
    def add_referee(self, name, role):
        ref = InfoReferee(name, role)
        self.referees.append(ref)
        self.filled_data["referees"] += 1
    
    ### Add Events ###
    def add_feed_entry(self, type, period, time, title, body, video=None):
        play = InfoFeedPlay(period, time, type, title, body, video)
        self.feed.append(play)
        if type != PlayType.normal:
            self.filled_data["feed"] = 1
    
    def modify_feed_entry_type(self, entry, new_type):
        video = entry.video
        if video:
            video = self.modify_video_type(entry.video, new_type)
        
        play = InfoFeedPlay(entry.period, entry.time, new_type, entry.title, entry.body, video)
        
        index = self.feed.index(entry)
        self.feed[index] = play
        
        
    def add_event_goal(self, period, time, team, player_id, player_name, is_own_goal):
        if is_own_goal:
            team = self.invert_team_id(team)
        ev = InfoEventGoal(period, time, team, player_id, player_name, is_own_goal)
        self.goals.append(ev)
        
        self.filled_data["events_goals"] += 1 if player_name != "N/D" else 0.5
        
    def add_event_sub(self, period, time, team, player_out, player_in, player_out_name, player_in_name):
        ev = InfoEventSub(period, time, team, player_out, player_in, player_out_name, player_in_name)
        self.subs.append(ev)
        
        self.filled_data["events_subs"] += 0.5 if player_out != "N/D" else 0.25
        self.filled_data["events_subs"] += 0.5 if player_in != "N/D" else 0.25
        
    def add_event_card(self, period, time, team, player_id, player_name, type):
        ev = InfoEventCard(period, time, team, player_id, player_name, type)
        self.cards.append(ev)
        
        self.filled_data["events_cards"] += 1 if player_name != "N/D" else 0.5
    
    def add_broadcast(self, name):
        b = InfoBroadcast(name)
        self.broadcast.append(b)
        
        self.filled_data["broadcast"] += 1

    def add_video(self, type, period, time, url, title, duration, source):
        video = InfoVideo(type, period, time, url, title, duration, source)
        self.videos.append(video)
        self.filled_data["video"] += 1
        return video

    def modify_video_type(self, entry, new_type):
        video = InfoVideo(new_type, entry.period, entry.time, entry.url, entry.title, entry.duration, entry.source)
        
        index = self.videos.index(entry)
        self.videos[index] = video
        return video
    
    def add_period_transitions(self):
        count = len(self.feed)
        if count == 0:
            return
        
        # Compare each pair of entries to check if they have different periods
        transitions = {}
        for index in range(1, count):
            play = self.feed[index]
            prev = self.feed[index-1]
            
            if play.period != prev.period:
                if play.period.is_running():
                    # Add transition saying the period has started
                    title = self.period_desc("Começa ", play.period)
                    entry = InfoFeedPlay(play.period, "0:00", PlayType.period_start, title, "", None)
                    transitions[index] = entry
                elif prev.period.is_running():
                    # Add transition saying the period has ended
                    title = self.period_desc("Termina ", prev.period)
                    entry = InfoFeedPlay(prev.period, prev.time, PlayType.period_end, title, "", None)
                    transitions[index] = entry
        
        # Check last feed item manually, since it has no other entry for comparison
        last = self.feed[count-1]
        period = self.state.period
        if last.period.is_running() and last.period != period:
            title = self.period_desc("Termina ", last.period)
            entry = InfoFeedPlay(last.period, last.time, PlayType.period_end, title, "", None)
            transitions[count] = entry
        
        # Add End of Match entry if it's already finished
        if period.is_finished():
            entry = InfoFeedPlay(period, "0:00", PlayType.period_start, "Fim de Jogo!", "", None)
            transitions[count+1] = entry
        
        # Insert transition entries into the feed array
        if len(transitions) > 0:
            for index,value in reversed(transitions.items()):
                self.feed.insert(index, value)
    
    ### Helpers ###
    def invert_team_id(self, id):
        return "home" if id == "away" else "away"
    
    def period_desc(self, prefix, period):
        if period == MatchPeriod.first_half:
            return prefix + "o Primeiro Tempo!"
        elif period == MatchPeriod.second_half:
            return prefix + "o Segundo Tempo!"
        elif period == MatchPeriod.extra_first_half:
            return prefix + "o Primeiro Tempo da Prorrogação!"
        elif period == MatchPeriod.extra_second_half:
            return prefix + "o Segundo Tempo da Prorrogação!"
        elif period == MatchPeriod.penalties:
            return prefix + "a Decisão nos Pênaltis!"
        
    def player_name(self, id):
        if id in self.players_ref:
            return self.players_ref[id].name
        return "N/D"
    
    def player_team(self, id):
        if id in self.players_ref:
            return self.players_ref[id].team
        return "N/D"

    # Strips trailing spaces and adds period to the end of line if needed
    def beautify_title(self, str):
        if len(str) == 0:
            return str
        symbols = [",",".",":",";","!","?","(",")","[","]", "|"]
        str = re.sub(r' +', " ", str.strip())
        if str and len(str) > 1:
            punctuation = "" if str[-1] in symbols else "."
        else:
            punctuation = ""
        return str[0].upper() + str[1:] + punctuation
