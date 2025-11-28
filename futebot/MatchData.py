import math
from ErrorPrinter import print_error
from FormattingData.PostTemplate import match_template, post_match_template, post_title_template, aggregated_score_template, match_icons
from BotUtils import format_str, zero_pad, format_time, format_date

from MatchSources.SourceGE import SourceGE
from MatchSources.Source365Scores import Source365Scores
from MatchSources.BaseSource import PlayType
from Models import MatchPeriod

class Match:
    def __init__(self, url):
        self.is_match_over = False
        self.is_finished = False
        self.detailed = True
        self.last_stats = None
        self.urls = []
        self.sources = []
        self.update_urls(url)

    # Update Match Data based on content from tracked sources
    def update_data(self, url=None):
        # Update list of tracked URLs, if needed
        if url != None:
            self.update_urls(url)
        
        try:
            # Update sources' contents
            self.update_sources()
            
            # Abort if no source was updated
            if len(self.sources) == 0:
                # Data wasn't updated
                return False
            
            self.plays_feed = self.format_plays_feed()
            self.is_match_over = self.get_moment_status() == "Encerrado"
        except Exception as e:
            print_error(e)
            # Data wasn't updated
            return False
        
        # Data was updated successfully
        return True
    
    # Updates list of tracked URLs
    def update_urls(self, url):
        if isinstance(url, list):
            for u in url:
                self.update_urls(u)
        elif isinstance(url, str) and not url in self.urls:
            self.urls.append(url)
    
    # Create Source objects with content from URLs
    def update_sources(self):
        self.sources = []
        for url in self.urls:
            source = None
            # Check URL origin
            if "ge.globo.com" in url:
                source = SourceGE(url)
            elif "webws.365scores.com" in url:
                source = Source365Scores(url)
            
            # Update source's contents
            if source:
                source.get_data()
                
                # Add to list of sources if it was updated
                if source.was_updated:
                    self.sources.append(source)
    
    def choose_source(self, param):
        top = 0
        priority = 0
        current = None
        for source in self.sources:
            if top > 0 and source.filled_data[param] == top:
                if source.priority < priority:
                    current = source
                    priority = source.priority
            elif source.filled_data[param] > top:
                current = source
                top = source.filled_data[param]
                priority = source.priority
        return current

    def choose_value(self, param, path, default_value="N/D"):
        source = self.choose_source(param)
        
        if not source:
            return default_value
            
        return get_path_value(source, path, default_value)

    ### ############### ###
    ### Content Getters ###
    ### ############### ###
    
    # Get content for thread based
    def print_match(self, post_id, post_thread_url):
        post_match_thread_text = ""
        if post_thread_url:
            post_match_thread_text = "**Post-Match Thread:** " + post_thread_url
            
        return self.format_match_template(match_template, {
            "stream": "https://reddit-stream.com/comments/" + post_id,
            "post_match_ref": post_match_thread_text
        })
    
    # Get content for post-match thread
    def print_post_match(self, match_thread_url):
        match_thread_text = ""
        if match_thread_url:
            match_thread_text = "**Match Thread:** " + match_thread_url
        
        return self.format_match_template(post_match_template, {
            "match_ref": match_thread_text
        })
    
    # Get title for Post-Match Thread
    def print_post_match_title(self, template, db_match):
        source = self.choose_source("base")
        
        return format_str(template,
            Campeonato = self.choose_value("tour", "tour.name", "N/D"),
            CampeonatoFase = self.choose_value("tour", "tour.stage", "N/D"),
            CampeonatoRodada = self.choose_value("tour", "tour.round", "N/D"),
            Estadio = self.choose_value("stadium", "details.stadium", "N/D"),
            TimeCasa = db_match.home_team,
            Mandante = db_match.home_team,
            TimeFora = db_match.away_team,
            Visitante = db_match.away_team,
            PlacarFinal = self.get_final_score(),
            PlacarCasa = self.get_team_score("home"),
            PlacarFora = self.get_team_score("away"),
            PlacarMandante = self.get_team_score("home"),
            PlacarVisitante = self.get_team_score("away"),
            Data = format_date(source.details.date),
            Horario = format_time(source.details.time)
        )

    # Formats Match Template's placeholders with actual match data
    def format_match_template(self, template, extra):
        base_source = self.choose_source("base")
        
        home_team_starting, home_team_subs = self.get_team_list("home")
        away_team_starting, away_team_subs = self.get_team_list("away")
        
        period = self.get_match_period()
        match_time = self.choose_value("match_time", "state.time", "0")
        stats_source = self.choose_source("stats")


        home_aggregated = self.choose_value("aggregated_score", "state.home_aggregated", None)
        away_aggregated = self.choose_value("aggregated_score", "state.away_aggregated", None)
        aggregated_score = "" if home_aggregated == None else format_str(aggregated_score_template, 
            CasaAgregado=home_aggregated, 
            ForaAgregado=away_aggregated
        )

        return format_str(template, 
            Campeonato = self.choose_value("tour", "tour.name", "N/D"),
            CampeonatoFase = self.choose_value("tour", "tour.stage", "N/D"),
            CampeonatoRodada = self.choose_value("tour", "tour.round", "N/D"),
            Estadio = self.choose_value("stadium", "details.stadium", "N/D"),
            TimeCasa = base_source.home_team.name,
            Mandante = base_source.home_team.name,
            TimeFora = base_source.away_team.name,
            Visitante = base_source.away_team.name,
            EscalacaoTemporaria=" (Escalações não confirmadas)" if base_source.temp_squads else "",
            TimeCasaTitulares = home_team_starting,
            TimeCasaReservas = home_team_subs,
            TimeCasaTreinador = self.choose_value("tour", "home_team.coach", "N/D"),
            TimeForaTitulares = away_team_starting,
            TimeForaReservas = away_team_subs,
            TimeForaTreinador = self.choose_value("tour", "away_team.coach", "N/D"),
            TimeCasaGols = self.get_goals_list("home"),
            TimeForaGols = self.get_goals_list("away"),
            TimeCasaEsquema = self.choose_value("tour", "home_team.formation", "N/D"),
            TimeForaEsquema = self.choose_value("tour", "away_team.formation", "N/D"),
            PlacarAgregado = aggregated_score,
            Arbitragem = self.get_referees(),
            PlacarFinal = self.get_final_score(),
            PlacarCasa = self.get_team_score("home"),
            PlacarFora = self.get_team_score("away"),
            Data = format_date(base_source.details.date),
            Horario = format_time(base_source.details.time),
            Lances = self.plays_feed,
            Transmissao = self.get_broadcast(),
            Estatitiscas = "N/D" if not stats_source else stats_source.stats.print_as_table(),
            MomentoPartida = self.get_moment(period, match_time, True),
            Videos = self.get_videos_list(),
            
            RedditStream = "" if not "stream" in extra else extra["stream"],
            MatchThread = "" if not "match_ref" in extra else extra["match_ref"],
            PostMatchThread = "" if not "post_match_ref" in extra else extra["post_match_ref"],
            MatchThreadUrl = "" if not "match_ref" in extra else extra["match_ref"],
            LinkGE = "" if not "source_link" in extra else extra["source_link"],
        )
    
    def get_match_period(self):
        source = self.choose_source("period")
        return MatchPeriod.upcoming if not source else source.state.period
    
    def get_match_state(self):
        period = self.get_match_period()
        time = self.choose_value("match_time", "state.time", "0")
        moment = self.get_moment(period, time)
        
        if moment == "Pré-Jogo":
            return "PreMatch"
        elif moment == "Encerrado" or moment == "Fim de Jogo":
            return "Finished"
        elif moment == "Intervalo":
            return "Interval"
        else:
            return "Ongoing"
    
    # Get Match Stats
    def get_match_stats(self):
        source = self.choose_source("stats")
        if not source:
            return None
        
        try:
            stats = source.stats.print_as_table()
            if stats:
                self.last_stats = self.get_match_period()
            return stats
        except Exception as e:
            print_error(e)
            return None
    
    ### #################### ###
    ### Plays Feed Functions ###    
    ### #################### ###
    
    # Sorts plays in blocks for better spacing between each half and interval subs
    def format_plays_feed(self):
        feed = self.choose_value("feed", "feed", [])
        
        # Defines blocks
        period_blocks = [
            [MatchPeriod.upcoming, MatchPeriod.pre_match],
            [MatchPeriod.first_half],
            [MatchPeriod.interval],
            [MatchPeriod.second_half],
            [MatchPeriod.preparing_extra_time],
            [MatchPeriod.extra_first_half],
            [MatchPeriod.extra_interval],
            [MatchPeriod.extra_second_half],
            [MatchPeriod.preparing_penalties, MatchPeriod.penalties],
            [MatchPeriod.post_match, MatchPeriod.finished]
        ]
        # Get plays for each block (ignoring empty ones)
        blocks = list(map(lambda x: self.get_plays_from_period(feed, x), period_blocks))
        blocks = list(filter(lambda x: len(x) > 0, blocks))

        # Format plays
        blocks_text = []
        for block in blocks:
            block_translated = list(map(self.translate_play, block))
            blocks_text.append("  \n".join(block_translated))

        return "  \n&nbsp;  \n".join(blocks_text)
    
    def get_plays_from_period(self, play_list, periods):
        return list(filter(lambda x: x.period in periods and x.type != PlayType.normal, play_list))

    # Formats play's output text according to its type
    def translate_play(self, play):
        title = play.title
        moment = self.get_moment(play.period, play.time)
        if play.period not in [MatchPeriod.first_half, MatchPeriod.second_half, MatchPeriod.extra_first_half, MatchPeriod.extra_second_half]:
            moment = "["+moment+"]"
        
        if title and play.type in [PlayType.goal, PlayType.own_goal]:
            title = "**" + title + "**"
        
        icon = self.get_play_icon(play.type)
        
        if play.type == PlayType.period_start:
            line = "{Title}"
        elif play.type == PlayType.period_end:
            line = "**{Period}** {Icon}{Title}"
        elif play.type in [PlayType.penalty_scored, PlayType.penalty_missed]:
            line = "{Icon} **{Title}** | {Body}{Video}"
        else:
            line = "**{Period}** {Icon}{Title} {Body}{Video}"
            
        video = ""
        if play.video:
            video = " [[Video ({})]({})]".format(sec_to_min(play.video.duration), play.video.url)
        
        return line.format(
            Icon = icon,
            Period = moment,
            Title = title,
            Body = play.body,
            Video = video
        )
    
    # Get the moment description for a specific event
    def get_moment(self, period, time, alt_end = False):
        if period in [MatchPeriod.upcoming, MatchPeriod.pre_match]:
            return "Pré-Jogo"
        elif period in [MatchPeriod.post_match, MatchPeriod.finished]:
            return "Encerrado" if alt_end else "Fim de Jogo"
        elif period in [MatchPeriod.interval, MatchPeriod.preparing_extra_time, MatchPeriod.extra_interval]:
            return "Intervalo"
        elif period in [MatchPeriod.preparing_penalties, MatchPeriod.penalties]:
            return "Pênaltis"
        else:
            minutes = str(time).split(":")[0]
            if period == MatchPeriod.first_half:
                label = "1T"
            elif period == MatchPeriod.second_half:
                label = "2T"
            elif period == MatchPeriod.extra_first_half:
                label = "1P"
            elif period == MatchPeriod.extra_second_half:
                label = "2P"
            return zero_pad(minutes, 2) + "/" + label
    
    # Get the current moment description for the match
    def get_moment_status(self):
        period = self.get_match_period()
        if period in [MatchPeriod.upcoming, MatchPeriod.pre_match]:
            return "Pré-Jogo"
        elif period in [MatchPeriod.post_match, MatchPeriod.finished]:
            return "Encerrado"
        elif period in [MatchPeriod.interval, MatchPeriod.preparing_extra_time, MatchPeriod.extra_interval]:
            return "Intervalo"
        elif period in [MatchPeriod.preparing_penalties, MatchPeriod.penalties]:
            return "Pênaltis"
        elif period == MatchPeriod.first_half:
            return "1º Tempo"
        elif period == MatchPeriod.second_half:
            return "2º Tempo"
        elif period == MatchPeriod.extra_first_half:
            return "1º Tempo/Prorrogação"
        elif period == MatchPeriod.extra_second_half:
            return "2º Tempo/Prorrogação"
    
    def get_play_icon(self, type):
        if type == PlayType.goal or type == PlayType.own_goal:
            return match_icons["goal"] + " "
        elif type == PlayType.substitution:
            return match_icons["subs"] + " "
        elif type == PlayType.yellow_card:
            return match_icons["yellow_card"] + " "
        elif type == PlayType.red_card:
            return match_icons["red_card"] + " "
        elif type == PlayType.penalty_scored:
            return match_icons["penalty_scored"] + " "
        elif type == PlayType.penalty_missed:
            return match_icons["penalty_missed"] + " "
        elif type == PlayType.period_end:
            return match_icons["time_over"] + " "
        
        return ""

    ### ################### ###
    ### Formation Functions ###
    ### ################### ###
    
    # Get list of players for the team, with substitutions between brackets if needed
    def get_team_list(self, team):
        data = self.choose_source("events_subs")
        if not data:
            data = self.choose_source("base")
        
        if team == "home":
            starting_ids = data.home_team.starting
            sub_ids = data.home_team.substitutes
        else:
            starting_ids = data.away_team.starting
            sub_ids = data.away_team.substitutes
        
        starting, subs = [], []
        
        for p in starting_ids:
            name = self.get_player_with_subs(p, data.subs, data)
            starting.append(name)
        
        for p in sub_ids:
            if not self.was_subbed_in(p, data.subs):
                name = data.player_name(p)
                subs.append(name)
        
        starting = "N/D" if len(starting) == 0 else ", ".join(starting)
        subs = "N/D" if len(subs) == 0 else ", ".join(subs)
        
        return starting, subs

    def get_player_with_subs(self, player_id, subs, data):
        subbed = None
        
        for p in subs:
            if p.player_out == player_id:
                subbed = self.get_player_with_subs(p.player_in, subs, data)
                break
        
        if subbed:
            return data.player_name(player_id) + " (" + subbed + ")"
        else:
            return data.player_name(player_id)
    
    def was_subbed_in(self, player_id, subs):
        for p in subs:
            if p.player_in == player_id:
                return True
        return False

    ### ##################### ###
    ### Match Score Functions ###
    ### ##################### ###
    
    # Get score for a single team, with penalties added between brackets if needed
    # Format differs between teams to accomodate the 1 (5) x (4) 1 format
    # Output Format for Home team: 1 (5)
    # Output Format for Away team: (5) 1
    def get_team_score(self, team):
        try:
            # TODO: Check all sources for possible divergence
            source = self.choose_source("period")
            
            if not source:
                return "0"
            
            state = source.state
            
            score = state.home_score if team == "home" else state.away_score
            penalties = state.home_penalty if team == "home" else state.away_penalty
            
            if not penalties:
                return str(score)
            else:
                if team == "home":
                    return "{Placar} ({Penaltis})".format(Placar=score, Penaltis=penalties)
                else:
                    return "({Penaltis}) {Placar}".format(Placar=score, Penaltis=penalties)
        except Exception as e:
            print_error(e)
            return "0"

    # Get score for both teams, with the 1 (5) x (4) 1
    # x is already included, and penalties only show up if needed
    def get_final_score(self):
        source = self.choose_source("period")
        
        if not source:
            return "x"
        
        state = source.state
        
        if state.period in [MatchPeriod.upcoming, MatchPeriod.pre_match] or state.home_score == None:
            return "x"
        else:
            return "{PlacarCasa} x {PlacarFora}".format(PlacarCasa = self.get_team_score("home"), PlacarFora = self.get_team_score("away"))

    # Get lists of players who scored goals for the team
    def get_goals_list(self, team):
        source = self.choose_source("events_goals")
        if not source:
            return "N/D"
        
        goals = list(filter(lambda x: x.team == team, source.goals))

        if len(goals) == 0:
            return "N/D"
        
        scorers = {}
        goals_timing = {}
        for g in goals:
            id = g.player_id
            if not id in scorers:
                scorers[id] = []
                goals_timing[id] = []
            
            scorers[id].append(g)
            moment = self.get_moment(g.period, g.time)
            goals_timing[id].append(moment + (", contra" if g.own_goal else ""))

        out = []
        for key, val in scorers.items():
            player = val[0].player_name
            out.append(player + " (" + ", ".join(goals_timing[key]) + ")")
        return ", ".join(out)

    ### ################## ###
    ### Other Data Getters ###
    ### ################## ###
    
    # Gets list of referees and their roles
    def get_referees(self):
        data = self.choose_value("referees", "referees", [])
        
        referee_list = []
        for r in data:
            referee_list.append(r.name + " (" + r.role + ")")
        
        return "N/D" if len(referee_list) == 0 else ", ".join(referee_list)
        
    def get_broadcast(self):
        broadcast = self.choose_value("broadcast", "broadcast", [])
        
        if len(broadcast) == 0:
            return "N/D"
        
        return ", ".join(list(map(lambda x: x.name, broadcast)))
    
    def get_videos_list(self):
        videos = self.choose_value("video", "videos", [])
        
        output = []
        for v in videos:
            if v.type != PlayType.normal:
                moment = self.get_moment(v.period, v.time)
                icon = self.get_play_icon(v.type)
                output.append("**{Moment}** {Icon}[{Title} ({Duration})]({URL}) ".format(
                    Icon=icon,
                    Moment=moment,
                    Title=v.title,
                    Duration=sec_to_min(v.duration),
                    URL=v.url
                ))
        
        if len(videos) == 0:
            return "N/D"
        
        return "  \n".join(output)
    
def get_path_value(obj, path, default_value=None):
    for i in path.split("."):
        val = getattr(obj, i, None)
        if val == None:
            return default_value
        
        obj = val
    return obj

def sec_to_min(num):
    min = math.floor(num / 60)
    sec = num % 60
    if sec < 10:
        sec = "0" + str(sec)
    
    return "{}:{}".format(min, sec)
