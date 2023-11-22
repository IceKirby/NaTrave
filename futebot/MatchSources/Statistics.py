stats_translations = {
    "expected_goals": "Gols Esperados (xG)",
    "ball_possession": "Posse de Bola",
    "shots": "Finalizações",
    "shots_on_target": "Finalizações Certas",
    "shots_off_target": "Finalizações Erradas",
    "woodwork": "Finalizações na Trave",
    "big_chances": "Chances Claras",
    "corners": "Escanteios",
    "dribbles": "Dribles Certos/Total",
    "crosses": "Cruzamentos",
    "accurate_crosses": "Cruzamentos Certos",
    "long_balls": "Bolas Longas Certas/Total",
    "offsides": "Impedimentos",
    "free_kicks": "Tiro Livre",
    "passes": "Passes",
    "passes_completed": "Passes Certos",
    "attacks": "Ataques",
    "dangerous_attacks": "Ataques Perigosos",
    "fouls": "Faltas",
    "saves": "Defesas de Goleiro",
    "tackles": "Desarmes",
    "tackles_won": "Desarmes Certos",
    "shots_blocked": "Chutes Bloqueados",
    "throwins": "Arremessos Laterais",
    "goal_kicks": "Tiro de Meta",
    "tackles_won": "Desarmes Certos",
    "yellow_cards": "Cartões Amarelos",
    "red_cards": "Cartões Vermelhos"
}
composite_translations = {
    "shots+shots_on_target": "Finalizações Certas/Total",
    "passes+passes_completed": "Passes Certos/Total",
    "tackles+tackles_won": "Desarmes Certos/Total",
    "crosses+accurate_crosses": "Cruzamentos Certos/Total"
}
table_row_template = "{home} | {stat} | {away}  \n"

class Statistics:
    def __init__(self):
        self.home_stats = {}
        self.away_stats = {}

    def set_names(self, home=None, away=None):
        if home:
            self.home_name = home
        if away:
            self.away_name = away
        

    def add_stats(self, team, key, value):
        target = self.home_stats if team == "home" else self.away_stats
        target[key] = value
    
    def count(self):
        return len(self.home_stats)
    
    def print_as_table(self):
        header = f"{self.home_name} | Estatística | {self.away_name}  \n"
        divider = ":---: | :---: | :---:  \n"
        lines = []
        
        # Possession
        self.simple_stat_line(lines, "ball_possession")
        
        # Offense
        self.simple_stat_line(lines, "expected_goals")
        self.accuracy_stat_line(lines, "shots", "shots_on_target")
        self.simple_stat_line(lines, "shots_off_target")
        self.simple_stat_line(lines, "woodwork")
        self.simple_stat_line(lines, "shots_blocked")
        self.simple_stat_line(lines, "saves")
        self.simple_stat_line(lines, "big_chances")
        
        # Build-up
        self.accuracy_stat_line(lines, "passes", "passes_completed")
        self.simple_stat_line(lines, "dribbles")
        self.simple_stat_line(lines, "long_balls")
        self.simple_stat_line(lines, "corners")
        self.accuracy_stat_line(lines, "crosses", "accurate_crosses")
        self.simple_stat_line(lines, "offsides")
        self.simple_stat_line(lines, "free_kicks")
        self.simple_stat_line(lines, "throwins")
        self.simple_stat_line(lines, "attacks")
        self.simple_stat_line(lines, "dangerous_attacks")
        
        # Defense
        self.simple_stat_line(lines, "fouls")
        self.accuracy_stat_line(lines, "tackles", "tackles_won")
        self.simple_stat_line(lines, "goal_kicks")
        self.simple_stat_line(lines, "yellow_cards")
        self.simple_stat_line(lines, "red_cards")
            
        if len(lines) > 0:
            lines = [header, divider] + lines
            return "".join(lines)
        else:
            return "N/D"
    
    def simple_stat_line(self, lines, stat):
        if stat in self.home_stats:
            lines.append(table_row_template.format(
                home=self.home_stats[stat],
                stat=stats_translations[stat],
                away=self.away_stats[stat]
            ))
    
    def accuracy_stat_line(self, lines, total, accurate):
        # Use simple stat if there's no data for the 2 stats needed
        if not total in self.home_stats or not accurate in self.home_stats:
            self.simple_stat_line(lines, total)
            self.simple_stat_line(lines, accurate)
            return
        
        # Gets composite stats name
        id = total +"+"+ accurate
        if id in composite_translations:
            name = composite_translations[id]
        else:
            name = stats_translations[accurate] + " / " + stats_translations[total]
        
        # Gets values
        home_val_total = to_int(self.home_stats[total])
        home_val_accurate = to_int(self.home_stats[accurate])
        home_percentage = 0 if home_val_total == 0 else home_val_accurate / home_val_total
        away_val_total = to_int(self.away_stats[total])
        away_val_accurate = to_int(self.away_stats[accurate])
        away_percentage = 0 if away_val_total == 0 else away_val_accurate / away_val_total
        
        # Formats values into lines
        lines.append(table_row_template.format(
            home="{}/{} ({:.0%})".format(home_val_accurate, home_val_total, home_percentage),
            stat=name,
            away="{}/{} ({:.0%})".format(away_val_accurate, away_val_total, away_percentage)
        ))
        
        
def to_int(val):
    if isinstance(val, str):
        return int(val)
    return val
