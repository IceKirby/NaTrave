import re
import json
import requests
from datetime import datetime, timedelta, timezone
from BotUtils import now
from MatchSources.BaseSource import MatchSource, MatchPeriod, PlayType
from MatchSources.MatchInfo import MatchInfo

class Source365Scores(MatchSource):
    
    def process_data(self, url):
        # Set source properties
        self.priority = 2
        self.source_name = "365Scores"
        self.unknown_players = {}
        
        # Get main data
        # url = f"https://webws.365scores.com/web/game/?gameId={url}&langId=31"
        data = self.fetch_data(url)
        if not data:
            return
        
        game = data["game"]
        
        # Get feed data
        feed_url = self.get_path_value(game, "playByPlay.feedURL", None)
        if feed_url:
            feed_url = game["playByPlay"]["feedURL"].replace("&lang=1", "&lang=31")
            feed = self.fetch_data(feed_url)
            if "Messages" in feed:
                feed = feed["Messages"]
            else:
                feed = []
        else:
            feed = []
        
        # Date and Time
        if "startTime" in game and game["startTime"] != None:
            start_time = datetime.strptime(game["startTime"], "%Y-%m-%dT%H:%M:%S+00:00")
            start_time -= timedelta(hours=3)
            
            date_start = start_time.strftime("%Y-%m-%d")
            time_start = start_time.strftime("%H:%M")
            
            self.filled_data["date"] = 1
            self.filled_data["time"] = 1
        else:
            date_start = None
            time_start = None
            
        
        self.set_details(
            date = date_start,
            time = time_start,
            stadium = self.get_path_value(game, "venue.name", None)
        )
        
        # Competition
        tour_id = self.get_path_value(game, "competitionId")
        tour = self.get_tour_data(tour_id)
        self.set_tour(
            name = self.get_path_value(tour, "name", "N/D"),
            stage = self.find_tour_stage(tour, self.get_path_value(game, "stageNum")),
            round = self.get_path_value(game, "roundNum", "N/D")
        )
        
        # Match State
        state_period, state_time = self.get_period_and_time(game, start_time)
        home_penalty, away_penalty = self.get_penalties_score(game)
        home_aggregated, away_aggregated = self.get_aggregated_score(game)
        self.set_state(
            period = state_period,
            time = state_time,
            home_score = int(self.get_path_value(game, "homeCompetitor.score", 0)),
            away_score = int(self.get_path_value(game, "awayCompetitor.score", 0)),
            home_penalty = home_penalty,
            away_penalty = away_penalty,
            home_aggregated = home_aggregated,
            away_aggregated = away_aggregated
        )
        
        # Teams
        self.set_team_data(True, game, "home")
        self.set_team_data(False, game, "away")
        self.temp_squads = not self.get_path_value(game, "hasLineups", False)
        
        # Unknown players
        members = self.get_path_value(game, "members", [])
        for m in members:
            if "id" in m and m["id"] not in self.players_ref:
                self.unknown_players[m["id"]] = m["name"]
        
        # Referees
        referees = self.get_path_value(game, "officials", [])
        for r in referees:
            self.add_referee(r["name"], "Árbitro Principal")
        
        # Plays Feed
        feed = self.add_periods_to_feed(feed[::-1])
        for p in feed:
            self.format_play_entry(game, p)
        if state_period in [MatchPeriod.post_match, MatchPeriod.finished]:
            self.add_feed_entry(PlayType.period_start, MatchPeriod.post_match, "0:00", "Fim de Jogo!", "")
        
        # Match Events
        events = self.get_path_value(game, "events", [])
        for ev in events:
            self.add_match_event(ev)
        
        # TV Broadcast
        broadcast = self.get_path_value(game, "tvNetworks", [])
        for b in broadcast:
            if (b["name"] == "bet365"):
                continue
            self.add_broadcast(b["name"])
        
        # Statistics
        stats = self.fetch_data("https://webws.365scores.com/web/game/stats/?langId=31&games=" + str(self.get_path_value(game, "id", "")))
        if stats:
            home_id = self.get_path_value(game, "homeCompetitor.id", None)
            away_id = self.get_path_value(game, "awayCompetitor.id", None)
            self.set_statistics(home_id, away_id, self.get_path_value(stats, "statistics", []))
        self.filled_data["stats"] = self.stats.count()

        # Fixtures (a.k.a. next games)
        if stats:
            self.filled_data["fixtures_home"] = ", ".join(self.get_team_fixtures(game, home_id))
            self.filled_data["fixtures_away"] = ", ".join( self.get_team_fixtures(game, away_id))           
        
        self.was_updated = True
        
    ### ############### ###
    ### Teams Functions ###
    ### ############### ###
    
    def set_team_data(self, is_home, game, id):
        # Set General Team Information
        team = self.get_path_value(game, id + "Competitor", {})
        members = self.get_path_value(game, "members", [])
        
        players = self.get_path_value(team, "lineups.members", [])
        starting = list(map(lambda x: x["id"], list(filter(lambda x: x["status"] == 1, players))))
        substitutes = list(map(lambda x: x["id"], list(filter(lambda x: x["status"] == 2, players))))
        
        coaches = list(filter(lambda x: x["status"] == 4, players))
        manager_id = None if len(coaches) == 0 else coaches[0]["id"]
        manager = list(filter(lambda x: "id" in x and x["id"] == manager_id, members))
        manager = {} if len(manager) == 0 else manager[0]
        
        self.set_team(
            is_home = is_home,
            name = self.get_path_value(team, "name", "N/D"),
            id = self.get_path_value(team, "id", "N/D"),
            players = [],
            coach = self.get_path_value(manager, "name", "N/D"),
            formation = self.get_path_value(team, "lineups.formation", "N/D"),
            starting = starting,
            substitutes = substitutes
        )
        
        # Add Players
        all_ids = starting + substitutes
        for player in members:
            if "id" in player and player["id"] in all_ids:
                self.add_player(id, player["name"], self.find_player_position(player["id"], players), player["id"], player["jerseyNumber"])
    
    def find_player_position(self, id, players):
        for p in players:
            if p["id"] == id:
                return self.get_path_value(p, "formation.shortName", "N/D")
        return "N/D"
    
    ### #################### ###
    ### Tournament Functions ###
    ### #################### ###
    
    def get_tour_data(self, id):
        url = f"https://webws.365scores.com/web/competitions/?langId=31&competitions={id}&withSeasons=true"
        response = requests.get(url)
        data = response.json()
        tours = data["competitions"]
        for t in tours:
            if t["id"] == id:
                return t
        return {}
    
    def find_tour_stage(self, tour, stage_id):
        stages = tour["seasons"][0]["stages"]
        for s in stages:
            if s["num"] == stage_id:
                return s["name"]
        return "N/D"
    
    ### ##################### ###
    ### Match State Functions ###
    ### ##################### ###
    
    def get_period_and_time(self, game, start_time):
        status_group = self.get_path_value(game, "statusGroup", 2)
        status = self.get_path_value(game, "statusText", "N/D")
        
        if status_group == 2:
            current_time = now()
            if current_time - start_time > timedelta(seconds=0):
                return MatchPeriod.pre_match, "0"
            else:
                return MatchPeriod.upcoming, "0"
        elif status_group == 4:
            if self.get_path_value(game, "justEnded", False):
                return MatchPeriod.post_match, "0"
            elif status not in ["Suspenso", "Interrompido", "Atrasado"]:
                return MatchPeriod.finished, "0"
                
        minutes = self.get_path_value(game, "preciseGameTime.minutes", 0)
        clock_running = self.get_path_value(game, "preciseGameTime.autoProgress", None)
        if status == "Intervalo":
            if self.get_path_value(game, "gameTime", 45) == 115:
                return MatchPeriod.extra_interval, "0"
            else:
                return MatchPeriod.interval, "0"
        elif status == "Prorrog.": # English: "ET Break"
            return MatchPeriod.preparing_extra_time, "0"
        elif status == "Prorrogação": # English: "Extra Time"
            if clock_running == False and minutes == 105:
                return MatchPeriod.preparing_extra_time, "0"
        elif status == "Fim da Prorrogação" or status == "Pré penalt.":
            return MatchPeriod.preparing_penalties, "0"
        elif status == "Pênaltis":
            return MatchPeriod.penalties, "0"
        
        if status == "Suspenso": 
            raw_time = self.guess_suspended_gametime(game)
        else:
            raw_time = self.get_path_value(game, "gameTimeDisplay", "0")
        
        parts = raw_time.split("+")
        time_display = parts[0]
        additional_time = "0" if len(parts) < 2 else parts[1]
        has_additional = additional_time != None
        
        if minutes < 45 or (has_additional and time_display == "45"):
            return MatchPeriod.first_half, str(minutes)
        elif minutes < 90 or (has_additional and time_display == "90"):
            return MatchPeriod.second_half, str(minutes - 45)
        elif minutes < 105 or (has_additional and time_display == "105"):
            return MatchPeriod.extra_first_half, str(minutes - 90)
        elif minutes < 120 or (has_additional and time_display == "120"):
            return MatchPeriod.extra_second_half, str(minutes - 105)
        
        return MatchPeriod.upcoming, "0"
        
    # If game is currently suspended, try to guess the game time based on the Stages markers
    def guess_suspended_gametime(self, game):
        minutes = self.get_path_value(game, "preciseGameTime.minutes", 0)
        stages = self.get_path_value(game, "stages", [])
        
        interval_entry, end90_entry, extratime_entry, penalties_entry = None, None, None, None
        
        for entry in stages:
            if entry["id"] == 7:
                interval_entry = entry
            elif entry["id"] == 9:
                end90_entry = entry
            elif entry["id"] == 10:
                extratime_entry = entry
            elif entry["id"] == 11:
                extratime_entry = entry
        
        if interval_entry and interval_entry["homeCompetitorScore"] == -1:
            return str(minutes) if minutes < 45 else "45+" + str(minutes-45)
        elif end90_entry and end90_entry["homeCompetitorScore"] == -1:
            return str(minutes) if minutes < 90 else "90+" + str(minutes-90)
        else:
            return str(minutes) if minutes < 120 else "120+" + str(minutes-120)
            
    def get_penalties_score(self, game):
        stages = self.get_path_value(game, "stages", [])
        for s in stages:
            if s["id"] == 11:
                if "homeCompetitorExtraScore" in s:
                    return int(s["homeCompetitorExtraScore"]), int(s["awayCompetitorExtraScore"])
                elif "homeCompetitorScore" in s:
                    return int(s["homeCompetitorScore"]), int(s["awayCompetitorScore"])
        return None, None
    
    def get_aggregated_score(self, game):
        home_aggr = self.get_path_value(game, "homeCompetitor.aggregatedScore", None)
        away_aggr = self.get_path_value(game, "awayCompetitor.aggregatedScore", None)

        if home_aggr != None:
            return int(home_aggr), int(away_aggr)

        return None, None

    ### #################### ###
    ### Plays Feed Functions ###
    ### #################### ###
    
    def format_play_entry(self, game, play):
        type = self.convert_play_type(play["TypeName"], play["Period"])
        period = play["PeriodType"]
        time = self.get_play_time(play)

        title = self.get_play_title(play, type)
        body = self.get_play_body(play, type)
        
        # Actually add entry to feed
        self.add_feed_entry(type, period, time, title, body)
    
    def get_play_time(self, play):
        if not "Timeline" in play:
            return "0:00"
        
        if play["Timeline"] == "P":
            return "0:00"
        
        num = re.sub('[^0-9]','', play["Timeline"])
        minute = int(num)
        extra = "+0'" if not "TimeLineSecondaryText" in play else play["TimeLineSecondaryText"]
        extra = int(extra[1:-1])
        
        period = play["Period"]
        if period == "1":
            minute = minute + extra
        elif period == "2":
            minute = minute - 45 + extra
        elif period == "3":
            minute = minute - 90 + extra
        elif period == "4":
            minute = minute - 105 + extra
        
        return str(minute) + ":00"
    
    def get_play_title(self, play, type):
        if "Title" in play and play["Title"] != None and type in [PlayType.period_start, PlayType.period_end]:
            return self.beautify_title(play["Title"])
        
        title = ""
        comm = "" if not "Comment" in play else play["Comment"]
        
        team = self.get_path_value(play, "CompetitorNum", None)
        if team:
            if type == PlayType.own_goal:
                team = self.home_team.name if team == 2 else self.away_team.name
            else:
                team = self.home_team.name if team == 1 else self.away_team.name
        
        if type == PlayType.goal or type == PlayType.own_goal:
            if not team:
                res = re.search(r'\((.+)\)', comm)
                if res:
                    team = res.group(1)
            title = f"Gol! {team}!"
        elif type == PlayType.substitution:
            if not team:
                res = re.search(r'Substituição  (.+),', comm)
                if res:
                    team = res.group(1)
            title = f'Substituição ({team}):'
        elif type == PlayType.penalty_scored or type == PlayType.penalty_missed:
            if not team:
                res = re.search(r'\(([^0-9]+)\)', comm)
                if res:
                    team = res.group(1)
            title = f"{team}"
        
        return self.beautify_title(title)
    
    def get_play_body(self, play, type):
        if not "Comment" in play:
            return ""
        
        players = self.get_path_value(play, "Players", [])
        
        comm = play["Comment"]
        if type == PlayType.goal or type == PlayType.own_goal:
            res = re.search(r'Gol!+ (.+[0-9+]\. )(.+)', comm)
            if res:
                comm = res.group(2)
        elif type == PlayType.substitution:
            if len(players) > 1:
                player_in = players[0]["PlayerName"]
                player_out = players[1]["PlayerName"]
                comm = f'SAIU: {player_out}, ENTROU: {player_in}'
            else:
                res = re.search(r'entra em campo (.+) substituindo (.+)\.', comm)
                if res:
                    comm = f'SAIU: {res.group(2)}, ENTROU: {res.group(1)}'
        
        return self.beautify_title(comm)
    
    # Checks each feed entry in order and adds the appropriate MatchPeriod value
    # since 365scores doesn't specity intervals actions
    def add_periods_to_feed(self, feed):
        l = len(feed)
        current = MatchPeriod.pre_match
        
        # Checks if match has Extra Time and/or Penalties Shootout
        has_extra_time = len(list(filter(lambda x: x["Period"] in ["3", "4"], feed))) > 0
        has_penalties = len(list(filter(lambda x: x["Period"] == "5", feed))) > 0
        # Default Periods in a 90 minutes match
        period_order = [MatchPeriod.pre_match, MatchPeriod.first_half, MatchPeriod.interval, MatchPeriod.second_half]
        # Adds Extra Time periods if needed
        if has_extra_time:
            period_order = period_order + [MatchPeriod.preparing_extra_time, MatchPeriod.extra_first_half, MatchPeriod.extra_interval, MatchPeriod.extra_second_half]
        # Adds Penalties periods if needed
        if has_penalties:
            period_order = period_order + [MatchPeriod.preparing_penalties, MatchPeriod.penalties]
        # Adds Post Match period
        period_order.append(MatchPeriod.post_match)
            
        # Checks each feed entry and assign the current MatchPeriod to it
        period_length = len(period_order)
        for index in range(l):
            entry = feed[index]
            type = entry["TypeName"]
            
            timeline_added = False
            timeline_removed = False
            
            # Check possible match start/end by verifying if there's a time assigned to the entry
            if index > 0:
                previous = feed[index-1]
                timeline_added = "Timeline" not in previous and "Timeline" in entry
                timeline_removed = "Timeline" in previous and "Timeline" not in entry
            
            if (type in ["start", "kick off"] and not "delay" in type) or (timeline_added and current.is_interval()):
                # If entry is of a start type, change to the next MatchPeriod before assigning it
                p_index = period_order.index(current)
                current = period_order[p_index+1]
                entry["PeriodType"] = current
                entry["Title"] = self.period_desc("Começa ", current)
                entry["Comment"] = ""
                entry["TypeName"] = "start"
            elif ("end " in type and not "delay" in type) or type in ["half time", "half_time summary", "full time"] or (timeline_removed and current.is_running()):
                # Don't change current period if it's already the interval
                if type == "half_time summary" and current == MatchPeriod.interval:
                    entry["PeriodType"] = current
                    continue
                
                entry["Title"] = self.period_desc("Termina ", current)
                entry["Comment"] = ""
                
                # If entry is of a end type, change to the next MatchPeriod after assigning it
                p_index = period_order.index(current) + 1
                if p_index < period_length:
                    current = period_order[p_index]
                entry["PeriodType"] = current
            else:
                entry["PeriodType"] = current
        
        return feed
    
    ### ###################### ###
    ### Match Events Functions ###
    ### ###################### ###
    
    def add_match_event(self, ev):
        type = self.get_path_value(ev, "eventType.name", None)
        subtype = self.get_path_value(ev, "eventType.subTypeName", None)
        period, time = self.get_event_period_time(ev)
        
        if period == MatchPeriod.penalties:
            return
        
        team = self.get_path_value(ev, "competitorId", None)
        player = self.get_path_value(ev, "playerId", None)
        other_player = self.get_path_value(ev, "extraPlayers", [])
        other_player = None if len(other_player) == 0 else other_player[0]
        
        team = "home" if team == self.home_team.id else "away"
        if type == "Cartão Amarelo":
            self.add_event_card(period, time, team, player, self.player_name(player), "yellow")
        elif type == "Cartão Vermelho":
            self.add_event_card(period, time, team, player, self.player_name(player), "red")
        elif type == "Gol":
            if subtype == "Gol Contra":
                team = self.invert_team_id(team)
                self.add_event_goal(period, time, team, player, self.player_name(player), True)
            else:
                self.add_event_goal(period, time, team, player, self.player_name(player), False)
        elif type == "Substitution":
            self.add_event_sub(period, time, team, other_player, player, self.player_name(other_player), self.player_name(player))
    
    def get_event_period_time(self, ev):
        ev_period = MatchPeriod.pre_match
        
        # Get minute for running play
        minute = ev["gameTime"]
        extra_minute = ev["addedTime"]
        ev_time = 0
        if minute > 120:
            ev_period = MatchPeriod.penalties
        elif minute > 105:
            ev_period = MatchPeriod.extra_second_half
            ev_time = minute - 105 + extra_minute
        elif minute > 90:
            ev_period = MatchPeriod.extra_first_half
            ev_time = minute - 90 + extra_minute
        elif minute > 45:
            ev_period = MatchPeriod.second_half
            ev_time = minute - 45 + extra_minute
        else:
            ev_period = MatchPeriod.first_half
            ev_time = minute + extra_minute
        
        return ev_period, str(int(ev_time)) + ":00"
    
    def set_statistics(self, home_id, away_id, data):
        stats_map = {
            "1": "yellow_cards",
            "2": "red_cards",
            "3": "shots",
            "4": "shots_on_target",
            "5": "shots_off_target",
            "6": "shots_blocked",
            "7": "crosses",
            "8": "corners",
            "9": "offsides",
            "10": "ball_possession",
            "11": "attacks",
            "12": "fouls",
            "13": "free_kicks",
            "14": "goal_kicks",
            "15": "throwins",
            "16": "dangerous_attacks",
            "19": "passes_completed",
            "20": "tackles",
            "21": "passes",
            "23": "saves",
            "24": "big_chances",
            "25": "woodwork",
            "76": "expected_goals"
            # "": "tackles_won",
        }
        for d in data:
            id = str(d["id"])
            if id in stats_map:
                team = "home" if d["competitorId"] == home_id else "away"
                self.stats.add_stats(team, stats_map[id], d["value"])
    
    ### ####### ###
    ### Helpers ###
    ### ####### ###
    
    def convert_play_type(self, value, period):
        if period == "5":
            if value == "penalty miss":
                return PlayType.penalty_missed
            if value == "penalty goal":
                return PlayType.penalty_scored
        
        type_dict = {
            "miss": PlayType.important,
            "highlight": PlayType.important,
            "attempt saved": PlayType.important,
            "attempt blocked": PlayType.important,
            "post": PlayType.important,
            "penalty lost": PlayType.important,
            "goal": PlayType.goal,
            "penalty goal": PlayType.goal,
            "penalty miss": PlayType.important,
            "own goal": PlayType.own_goal,
            "substitution": PlayType.substitution,
            "yellow card": PlayType.yellow_card,
            "red card": PlayType.red_card,
            "start": PlayType.period_start,
            "kick off": PlayType.period_start,
            "end 1": PlayType.period_end,
            "end 2": PlayType.period_end,
            "end 3": PlayType.period_end,
            "end 4": PlayType.period_end,
            "end 5": PlayType.period_end,
            "half time": PlayType.period_end,
            "full time": PlayType.period_end,
        }
        return PlayType.normal if value not in type_dict else type_dict[value]
    
    # Gets value from JSON; if value is not found, returns default_value
    def get_path_value(self, obj, path, default_value="-"):
        for i in path.split("."):
            if i in obj and obj[i] != None:
                obj = obj[i]
            else:
                return default_value
        return obj
    
    def player_name(self, id):
        if id in self.unknown_players:
            return self.unknown_players[id]
        else:
            return super().player_name(id)

    def get_team_fixtures(self, current_game, team_id, max_results=3):
        #given a team 365score id (mineiro is 1209, ream madrid is 131 etc), returns a list of strings with the following format
        #(opponent_name{str} Casa|Fora{str})
        #containing the next {max_results} games for that team
        if not isinstance(team_id, int):
            return ("err","invalid team_id on get_team_fixtures")
        target_url = f"https://webws.365scores.com/web/games/fixtures/?appTypeId=5&langId=31&userCountryId=131&competitors={team_id}"
        response = requests.get(target_url)
        res_json = response.json()
        fixtures = []
        for game in res_json['games']:
            if game['id'] == current_game['id']: #means current tracked match still appears as fixture
                continue
            if (game['homeCompetitor']['id'] == team_id):
                fixtures.append((game['awayCompetitor']["name"]+" (Casa)"))
            else:
                fixtures.append((game['homeCompetitor']["name"]+" (Fora)"))
            
            if(len(fixtures) >= max_results):
                break
        return fixtures
