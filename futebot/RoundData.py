import MatchManager
import Redditor
import BotUtils
import Scheduler
from ErrorPrinter import print_error
from Models import Sub, Match, Thread, MatchPeriod, Hub, SuggestedSort, PendingUnpin
from FormattingData.PostTemplate import round_template, round_match_template, round_table_header, round_event_template, hub_match_link_untracked, hub_match_postponed_template, hub_match_creation_template
from datetime import timedelta
from sqlalchemy import or_
from prawcore.exceptions import Forbidden

class RoundData:
    def __init__(self, sub, round):
        self.sub = sub
        self.round = round
        self.date = round.date
        self.thread_url = round.url
        self.needs_update = True
        self.pending_creation = False

        self.fill_eligible_matches()
    
    # Makes sure the tracked matches are in the database
    def fill_eligible_matches(self):
        Scheduler.fill_tour_matches(self.round.tournament)

    def find_tracked_matches(self, s):
        today = self.date
        tomorrow = self.date + timedelta(days=1)
        
        matches = s.query(Match)\
            .filter(Match.tournament == self.round.tournament)\
            .filter(Match.start_time > today)\
            .filter(Match.start_time < tomorrow)\
            .all()
        
        found = []
        for m, s in matches:
            match = MatchManager.get_or_create_match_data(m.id)
            match.update_data()
            found.append(match)
        
        self.update_thread(found)

    def update_thread(match_list):
        pass

    def get_thread_content(self, s, sub, date):
        ids = list(map(lambda t: t.thread_id, self.threads))
        
        threads = s.query(Thread, Match)\
            .join(Match)\
            .filter(Thread.id.in_(ids))\
            .all()
        
        tour_groups = self.group_threads_by_tour(threads)
        tours_text = self.format_tour_groups(tour_groups)

        text = BotUtils.format_str(round_template,
            TorneioRodada="",
            Data="",
            Partidas="",
            Tabela="",
            Lances=""
        )
        
        return text
    
    def format_match_line(self, match, thread):
        match_data = MatchManager.get_or_create_match_data(match.id)
        
        if match.postponed:
            state = "Adiado"
        elif match.match_state <= MatchPeriod.pre_match:
            state = match.start_time.strftime('%H:%M')
        elif match.match_state >= MatchPeriod.post_match:
            state = "Encerrado"
        else:
            state = "Em Andamento" if not match_data else match_data.get_current_moment()
        
        score = "x" if match.score == None else match.score
        
        if thread.hub_only:
            links = hub_match_link_untracked
        elif not thread.url:
            if match.postponed:
                links = hub_match_postponed_template
            else:
                links = BotUtils.format_str(hub_match_creation_template, Horario=thread.creation_time.strftime('%H:%M'))
        elif not thread.post_match_thread:
            links = "[Match Thread]({url})".format(url=thread.url)
        else:
            links = "[Match Thread]({url}) | [Post-Match Thread]({post_url})".format(url=thread.url, post_url=thread.post_match_thread)
        
        return BotUtils.format_str(round_match_template,
            Estado=state,
            Mandante=match.home_team,
            Visitante=match.away_team,
            Placar=score,
            Links=links
        )