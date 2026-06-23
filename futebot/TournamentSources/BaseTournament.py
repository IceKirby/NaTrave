from collections import namedtuple

StandingPosition = namedtuple('StandingPosition', 'team position points played wins draws losses goals_scored goals_allowed goals_difference variation')

class BaseTournament:
    def __init__(self, tour_name):
        self.is_valid = False
        self.tour_name = tour_name
        self.reset_tour_data()

    def reset_tour_data(self):
        self.standings = []
        self.stage_name = ""
        self.current_round = 0
    
    def update_tour_data(self):
        pass

    def add_standing_row(self, team, position, points, played, wins, draws, losses, goals_scored, goals_allowed, goals_difference, variation):
        row = StandingPosition(team, position, points, played, wins, draws, losses, goals_scored, goals_allowed, goals_difference, variation)
        self.standings.append(row)

