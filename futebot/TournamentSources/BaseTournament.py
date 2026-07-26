import enum
from collections import namedtuple

StandingPosition = namedtuple('StandingPosition', 'team position points played wins draws losses goals_scored goals_allowed goals_difference variation')
StandingGroup = namedtuple('StandingGroup', 'name standings')

class TourStageType(enum.Enum):
    league = 0
    groups = 1
    knockout = 2
    finals = 3
    friendly = 4

class BaseTournament:
    def __init__(self, tour_name):
        self.is_valid = False
        self.tour_name = tour_name
        self.reset_tour_data()

    def reset_tour_data(self):
        self.standings = []
        self.groups = []
        self.brackets = []
        self.stage_name = ""
        self.stage_type = None
        self.current_round = 0
    
    def update_tour_data(self):
        pass

    def add_standing_row(self, target, team, position, points, played, wins, draws, losses, goals_scored, goals_allowed, goals_difference, variation):
        row = StandingPosition(team, position, points, played, wins, draws, losses, goals_scored, goals_allowed, goals_difference, variation)
        target.append(row)
    
    def add_group(self, name):
        group = StandingGroup(name, [])
        self.group.append(group)
        return group
    
    def add_bracket(self, name):
        pass

