import json
import re
import random
import math
import requests
from datetime import datetime, timedelta, timezone
from BotUtils import zero_pad
from MatchSources.BaseSource import MatchSource, MatchPeriod, PlayType
from MatchSources.MatchInfo import MatchInfo
from ErrorPrinter import print_error

class SourceGE(MatchSource):
    def process_data(self, url):
        # Set source properties
        self.priority = 1
        self.source_name = "GloboEsporte"
        
        # Get main data
        target_url = self.url.replace("ge.globo.com/", "ge.globo.com/globo/raw/");
        data = self.fetch_data(target_url)
        
        if not data:
            return
        game = data["resource"]
        
        # General details
        self.set_details(
            date = self.get_path_value(game, "transmissao.jogo.dataRealizacao"),
            time = self.get_path_value(game, "transmissao.jogo.horaRealizacao"),
            stadium = self.get_path_value(game, "transmissao.jogo.estadio.nome", None)
        )
        
        if self.details.date != "-":
            self.filled_data["date"] = 1
        if self.details.time != "-":
            self.filled_data["time"] = 1
        
        # Competition
        self.set_tour(
            name = self.get_path_value(game, "transmissao.jogo.campeonato.nome", "N/D"),
            stage = self.get_path_value(game, "transmissao.jogo.fase.nome", "N/D"),
            round = self.get_path_value(game, "transmissao.jogo_sde.resultados.rodada", "N/D")
        )
        
        # Match State
        plays = self.fix_plays_order(game["lances"])
        self.set_state(
            period = self.get_match_period(game, plays),
            time = self.guess_match_time(game, self.get_path_value(game, "transmissao.periodo", "PRE_JOGO"), plays),
            home_score = self.get_path_value(game, "transmissao.jogo_sde.resultados.placar_oficial_mandante", 0),
            away_score = self.get_path_value(game, "transmissao.jogo_sde.resultados.placar_oficial_visitante", 0),
            home_penalty = self.get_path_value(game, "transmissao.jogo_sde.resultados.placar_penaltis_mandante", None),
            away_penalty = self.get_path_value(game, "transmissao.jogo_sde.resultados.placar_penaltis_visitante", None),
            home_aggregated = None,
            away_aggregated = None
        )
        
        # Teams
        self.set_team_data(True, game, "mandante")
        self.set_team_data(False, game, "visitante")
        
        # Referees
        referees = self.get_path_value(game, "transmissao.jogo.arbitragem", None)
        if referees:
            rolesDict = {"arbitroPrincipal": "Árbitro Principal", "arbitroAssistente1": "Assistente 1", "arbitroAssistente2": "Assistente 2", "quartoArbitro": "Quarto Árbitro"}
            for key,value in rolesDict.items():
                if key in referees and referees[key] and "nome_popular" in referees[key]:
                    self.add_referee(referees[key]["nome_popular"], value)
        
        # Plays Feed
        for p in plays:
            self.format_play_entry(game, p)
        self.fix_boring_feed()
        self.add_period_transitions()
        
        self.was_updated = True
        
    # Set team data
    def set_team_data(self, is_home, game, id):
        # Set General Team Information
        team = self.get_path_value(game, "transmissao.jogo." + id, {})
        
        formation_id = self.get_path_value(game, "transmissao.jogo_sde.resultados.escalacao_"+id+"_id", "N/D")
        team_data = self.get_path_value(game, "transmissao.jogo_sde.referencias.escalacao."+ str(formation_id), {})
        
        starting = self.get_players_id(self.get_path_value(team_data, "titulares", []))
        substitutes = self.get_players_id(self.get_path_value(team_data, "reservas", []))
        
        self.set_team(
            is_home = is_home,
            name = self.get_path_value(team, "nome", "N/D"),
            id = self.get_path_value(team, "equipe_id", "N/D"),
            players = [],
            coach = self.get_path_value(team, "tecnico.nome_popular", "N/D"),
            formation = self.get_formation(self.get_path_value(team, "esquema_tatico", None)),
            starting = starting,
            substitutes = substitutes
        )
        
        # Add Players
        side = "home" if is_home else "away"
        players = self.get_path_value(team, "atletas.titulares", []) + self.get_path_value(team, "atletas.reservas", [])
        for player in players:
            self.add_player(side, player["nome_popular"], player["posicao"]["descricao"], player["atleta_id"], player["camisa"])
        
        if len(self.get_path_value(team, "atletas.reservas", [])) > 0:
            self.temp_squads = False
    
    ### #################### ###
    ### Plays Feed Functions ###
    ### #################### ###
    
    def format_play_entry(self, game, play):
        type = self.convert_play_type(play["tipoLance"])
        period = self.convert_period(play["periodo"])
        time = play["momento"] if play["momento"] else "0:00"
        
        # Ignore plays that aren't relevant to the feed
        if type == None:
            return
            
        # Ignore polls
        if self.has_poll(play):
            return
        
        # Mark a Penalty Shootout play as scored or missed
        if type == PlayType.penalty:
            type = PlayType.penalty_scored if play["disputaPenalti"] == "penalti-convertido" else PlayType.penalty_missed
        
        title = self.get_play_title(game, type, play)
        body = self.get_play_body(game, type, play)
        
        video = None
        blocks = self.get_path_value(play, "corpo.blocks", [])
        for b in blocks:
            block_type = self.get_path_value(b, "data.type", None)
            if block_type == "backstage-video":
                video_url = "https://globoplay.globo.com/v/" + str(b["data"]["identifier"])
                duration = b["data"]["duration"]
                duration = 0 if not duration else round(duration / 1000)
                caption = self.remove_time_text(b["data"]["caption"])
                
                if period.is_running() and type == PlayType.normal:
                    type = PlayType.important
                
                video = self.add_video(type, period, time, video_url, caption, duration, "GE")
        
        # Actually add entry to feed
        self.add_feed_entry(type, period, time, title, body, video)
        
        # Add goal, card or sub event
        team = self.get_path_value(play, "time", None)
        player = self.get_path_value(play, "jogador", None)
        player_sub = self.get_path_value(play, "jogadorReserva", None)
        
        if team != None:
            team = "home" if team == self.home_team.id else "away"
            if type == PlayType.goal or type == PlayType.own_goal:
                self.add_event_goal(period, time, team, player, self.player_name(player), type == PlayType.own_goal)
            elif type == PlayType.substitution:
                if player and player_sub:
                    self.add_event_sub(period, time, team, player, player_sub, self.player_name(player), self.player_name(player_sub))
            elif type == PlayType.yellow_card or type == PlayType.red_card:
                color = "yellow" if type == PlayType.yellow_card else "red"
                if not player:
                    player = player_sub
                
                if player:
                    self.add_event_card(period, time, team, player, self.player_name(player), color)
    
    def has_poll(self, play):
        if "blocks" in play and play["blocks"]:
            for b in play["blocks"]:
                if b["data"]:
                    block = b["data"]
                    if block["type"] == "votacao":
                        return True
        return False
    
    # Fix plays' order in list since they are originally sorted by input time,
    # which may differ from the moment it actually happened
    def fix_plays_order(self, list):
        list.sort(key=self.play_moment_order)
        return list

    def play_moment_order(self, play):
        period_order = ["PRE_JOGO", "PRIMEIRO_TEMPO", "INTERVALO", "SEGUNDO_TEMPO", "AGUARDANDO_PRORROGACAO", "PRIMEIRO_TEMPO_PRORROGACAO", "INTERVALO_PRORROGACAO", "SEGUNDO_TEMPO_PRORROGACAO", "AGUARDANDO_PENALIDADES", "PENALIDADES", "FIM_DE_JOGO", "POS_JOGO", "POS_JOGO_AO_VIVO", "JOGO_ENCERRADO"]
        period_mod = str(period_order.index(play["periodo"]))

        if play["momento"] == "":
            minutes_mod, seconds_mod = "00", "00"
        else:
            minutes_mod, seconds_mod, *rest = list(map(lambda x: x.replace(r"[^0-9]", ""), play["momento"].split(":")))

        time = datetime.strptime(play["created"], "%Y-%m-%dT%H:%M:%S.%fZ")
        time_minutes_mod = zero_pad(str(time.hour * 60 + time.minute), 4)
        time_seconds = zero_pad(str(time.second), 2)
        
        time_raw = period_mod + minutes_mod + seconds_mod + time_minutes_mod + time_seconds
        return int(time_raw.replace(" ", ""))
    
    def fix_boring_feed(self):
        normal_count = 0
        important_count = 0
        
        # Count how many feed entries are Normal and Important Types
        for entry in self.feed:
            if not entry.period.is_running():
                continue
            if entry.type == PlayType.normal:
                normal_count += 1
            elif entry.type == PlayType.important:
                important_count += 1
        
        
        # Check if proportion of normal to important entries is too large
        if (important_count == 0 and normal_count > 10) or (important_count > 0 and normal_count > important_count*8):
            # Change Normal entries to important if they contain a video or a title
            for entry in self.feed:
                if entry.period.is_running() and entry.type == PlayType.normal:
                    if entry.title != None and len(entry.title) > 0:
                        self.modify_feed_entry_type(entry, PlayType.important)
    
    # Tries to guess current match time using some plays from the ongoing half as sample
    # It looks for the difference between the current time and the time the play was created
    # and adds the difference to the play's moment, then returns the lowest value from the sampled plays
    def guess_match_time(self, game, period, ordered_plays):
        if period not in ["PRIMEIRO_TEMPO", "SEGUNDO_TEMPO", "PRIMEIRO_TEMPO_PRORROGACAO", "SEGUNDO_TEMPO_PRORROGACAO"]:
            return 0
        
        # Filter plays by only getting those from the current half
        plays = list(filter(lambda x: x["periodo"] == period, ordered_plays))

        # Gets the first play, last and some other random one
        sample = []
        if len(plays) > 0:
            sample.append(plays[0])
        if len(plays) > 2:
            sample.append(random.choice(plays[1:-1]))
        if len(plays) > 1:
            sample.append(plays[-1])

        now = datetime.utcnow()
        minutes = 0
        seconds = 0
        diff = []

        # For each sample play, check how long ago it was added to the system, then
        # add that difference to the moment it happend in that half
        for s in sample:
            # Check how long ago the play was input into the system
            delta = now - datetime.strptime(s["created"], "%Y-%m-%dT%H:%M:%S.%fZ")

            # Add that difference to the moment the play was said to have happened
            raw = s["momento"].split(":")
            if len(raw) > 0 and len(raw[0]) > 0 and len(raw[1]) > 0:
                seconds = int(raw[1]) + (delta.seconds % 60)
                minutes = int(raw[0]) + math.floor(delta.seconds / 60)
                if seconds >= 60:
                    seconds = seconds % 60
                    minutes = minutes + 1

            # Save adjusted moment for later comparison
            diff.append({ "min":minutes, "sec":seconds })
        if len(diff) == 0:
            return "0"

        # Return the lowest value found in the sampled plays
        diff = sorted(diff, key=lambda x: x["min"]*60 + x["sec"])
        return str(diff[0]["min"])
    
    ### ################### ###
    ### Properties Fetchers ###
    ### ################### ###
    
    def get_match_period(self, game, plays):
        status = self.get_path_value(game, "transmissao.periodo", "PRE_JOGO")
        
        # Checks for possible late status changes by verifying latest plays' period
        if len(plays) > 1:
            if plays[0]["periodo"] == plays[1]["periodo"] and plays[0]["periodo"] in ["INTERVALO", "AGUARDANDO_PRORROGACAO", "INTERVALO_PRORROGACAO", "FIM_DE_JOGO", "POS_JOGO_AO_VIVO", "POS_JOGO"]:
                status = plays[0]["periodo"]
        
        period = self.convert_period(status)
        
        return period if period != None else MatchPeriod.upcoming
    
    def get_play_title(self, game, type, play):
        title = play["titulo"]
        if type == PlayType.goal:
            title = "Gol d{Article} {Team}!"
        elif type == PlayType.own_goal:
            title = "Gol d{Article} {Team}!"
        elif type == PlayType.substitution:
            title = "Substituição n{Article} {Team}:"
        elif type == PlayType.penalty_scored or type == PlayType.penalty_missed:
            title = "{Team}"
            
        if "time" in play:
            team_desc = "mandante" if self.home_team.id == play["time"] else "visitante"
            
            # Fix team name for Own Goals by checking the player who scored
            if type == PlayType.own_goal and "jogador" in play and play["jogador"] != None:
                team = self.player_team(play["jogador"])
                if team == "home" and team_desc == "mandante":
                    team_desc = "visitante"
                elif team == "away" and team_desc == "visitante":
                    team_desc = "mandante"
            
            obj = self.get_path_value(game, "transmissao.jogo."+team_desc, {})
            team_name = self.get_path_value(obj, "nome", "Time A")
            gender = self.get_path_value(obj, "genero", "M")
            article = "o" if gender == "M" else "a"
            
            title = title.format(Article=article, Team=team_name)
        
        return self.beautify_title(title)
    
    def get_play_body(self, game, type, play):
        body = []
        for b in play["corpo"]["blocks"]:
            t = b["text"].strip()
            body.append(t.replace("\n", ", "))
        body = ". ".join(list(filter(lambda x: len(x) > 0, body)))
        
        if type == PlayType.substitution:
            body = body.replace("Sai: ", "SAIU: ", 1).replace("Entra: ", "ENTROU: ", 1)
        
        return self.beautify_title(body)
    
    def get_formation(self, raw):
        if raw == None:
            return "N/D"
        else:
            return "-".join(list(raw.replace("-", "")))
    
    def get_players_id(self, players):
        result = map(lambda x: x["atleta_id"], players)
        return list(result)
    
    ### ####### ###
    ### Helpers ###
    ### ####### ###
    
    # Gets value from GE Match JSON; if value is not found, returns default_value
    def get_path_value(self, obj, path, default_value="-"):
        for i in path.split("."):
            if i in obj and obj[i] != None:
                obj = obj[i]
            else:
                return default_value
        return obj
    
    def convert_period(self, value):
        period_dict = {
            "PRE_JOGO": MatchPeriod.pre_match,
            "PRIMEIRO_TEMPO": MatchPeriod.first_half,
            "INTERVALO": MatchPeriod.interval,
            "SEGUNDO_TEMPO": MatchPeriod.second_half,
            "AGUARDANDO_PRORROGACAO": MatchPeriod.preparing_extra_time,
            "PRIMEIRO_TEMPO_PRORROGACAO": MatchPeriod.extra_first_half,
            "INTERVALO_PRORROGACAO": MatchPeriod.extra_interval,
            "SEGUNDO_TEMPO_PRORROGACAO": MatchPeriod.extra_second_half,
            "AGUARDANDO_PENALIDADES": MatchPeriod.preparing_penalties,
            "PENALIDADES": MatchPeriod.penalties,
            "FIM_DE_JOGO": MatchPeriod.post_match,
            "POS_JOGO": MatchPeriod.finished,
            "POS_JOGO_AO_VIVO": MatchPeriod.finished,
            "JOGO_ENCERRADO": MatchPeriod.finished
        }
        return None if value not in period_dict else period_dict[value]
    
    def convert_play_type(self, value):
        type_dict = {
            "NORMAL": PlayType.normal,
            "IMPORTANTE": PlayType.important,
            "GOL": PlayType.goal,
            "GOL_CONTRA": PlayType.own_goal,
            "PENALTI": PlayType.penalty,
            "SUBSTITUICAO": PlayType.substitution,
            "CARTAO_AMARELO": PlayType.yellow_card,
            "CARTAO_VERMELHO": PlayType.red_card
        }
        return None if value not in type_dict else type_dict[value]

    def remove_time_text(self, text):
        exp = r"Ao?s?\s[0-9]+(\smin|\sminutos|\sseg|\ssegundos|\'|\")\sdo\s([0-9]+º|primeiro|segundo)\s[Tt]empo\s(da\sprorrogação\s)?-\s"
        if re.match(exp, text):
            text = re.sub(exp, "", text)
        
        exp = r"[0-9]+(min|seg),\s[0-9]T\s-\s"
        if re.match(exp, text):
            text = re.sub(exp, "", text)
            
        text = text[0].upper() + text[1:]
        return text
