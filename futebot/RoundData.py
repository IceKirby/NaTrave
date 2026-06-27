import MatchManager
import TourManager
import Redditor
import BotUtils
import Scheduler
from ErrorPrinter import print_error
from Models import Sub, Match, Thread, MatchPeriod, Hub, SuggestedSort, PendingUnpin
from FormattingData.PostTemplate import round_template, round_match_template, round_table_header, round_table_separator, round_table_row, round_event_template, hub_match_link_untracked, hub_match_postponed_template, hub_match_creation_template
from datetime import timedelta
from sqlalchemy import or_
from prawcore.exceptions import Forbidden

class RoundData:
    def __init__(self, sub, round):
        self.tournament = round.tournament
        self.date = round.date
        self.thread_url = round.url
        self.needs_update = True
        self.pending_creation = False

        self.fill_eligible_matches(sub, round.supress_match_threads)
    
    # Makes sure the tracked matches are in the database
    def fill_eligible_matches(self, sub, supress_match_threads):
        Scheduler.fill_tour_matches(self.tournament, sub, not supress_match_threads)

    def find_tracked_matches(self, s):
        today = self.date
        tomorrow = self.date + timedelta(days=1)
        
        matches = s.query(Match)\
            .filter(Match.tournament == self.tournament)\
            .filter(Match.start_time >= today)\
            .filter(Match.start_time < tomorrow)\
            .all()
        
        found = []
        for m in matches:
            match = MatchManager.get_or_create_match_data(m.id)
            match.update_data()
            found.append(match)

        return found

    def update_thread(self, s, thread_url, sub):
        try:
            text = self.get_thread_content(s, sub, self.date)
            
            # Get thread id according to Reddit API
            thread_id = Redditor.url_to_thread_id(thread_url)
            
            # Actually update the thread's content
            Redditor.update_thread({
                "id": thread_id,
                "text": text
            })
        except Exception as e:
            print_error(e)

    def get_thread_content(self, s, sub, date):
        matches = self.find_tracked_matches(s)
        
        today = self.date
        tomorrow = self.date + timedelta(days=1)

        threads = s.query(Thread, Match)\
            .join(Match)\
            .filter(Thread.sub == sub.id)\
            .filter(Match.tournament == self.tournament)\
            .filter(Match.start_time > today)\
            .filter(Match.start_time < tomorrow)\
            .all()
        
        tour_data = TourManager.get_tour_data(self.tournament)

        tour_round_name = self.tournament + ("" if not tour_data.current_round else " - Rodada " + str(tour_data.current_round))

        text = BotUtils.format_str(round_template,
            TorneioRodada=tour_round_name,
            Data=BotUtils.translate_date(date, False),
            Partidas=self.get_formatted_match_list(threads),
            Tabela=self.format_standings_table(tour_data.standings),
            Lances=self.get_matches_feed(matches)
        )
        
        return text
    
    def get_formatted_match_list(self, threads):
        res = []

        for t, m in threads:
            res.append(self.format_match_line(m, t))

        return "\n\n".join(res)

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
            links = ""
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
            Links="" if links == "" else f"({links})"
        )
    
    def format_standings_table(self, standings, columns=2):
        lines = [ ]
        col_sep = " | │ | "

        # Creates the first two lines (header and separator), and
        # duplicates them if table is split into two columns
        header = []
        separator = []
        c = columns
        while c > 0:
            header.append(round_table_header)
            separator.append(round_table_separator)
            c -= 1

        lines.append(col_sep.join(header))
        lines.append(" | --- | ".join(separator))

        # Formats each team position
        rows = []
        for r in standings:
            rows.append(self.format_standings_row(r))
        
        # Calculates how many rows will be needed
        per_col = int(len(rows) / columns)

        # Concatenates team stats into multiple columns
        for i in range(per_col):
            line = []
            c = 0
            while c < columns:
                line.append(rows[i + (c * per_col)])
                c += 1
            lines.append(col_sep.join(line))

        return "  \n".join(lines)

    def format_standings_row(self, row):
        return BotUtils.format_str(round_table_row,
            Posicao=row.position,
            Time=row.team,
            Pontos=row.points,
            Vitorias=row.wins,
            Empates=row.draws,
            Derrotas=row.losses,
            GolsPro=row.goals_scored,
            GolsContra=row.goals_allowed,
            SaldoDeGols=row.goals_difference
        )
    
    def get_matches_feed(self, matches):
        plays = []
        for match in matches:
            plays = plays + match.get_plays_for_round()
        
        sorted_plays = sorted(plays, key=lambda p: p["time"])
        mapped_plays = list(map(lambda p: p["text"], sorted_plays))

        return "  \n".join(mapped_plays)
    
    def is_finished(self, s):
        today = self.date
        tomorrow = self.date + timedelta(days=1)
        
        matches = s.query(Match)\
            .filter(Match.tournament == self.tournament)\
            .filter(Match.start_time >= today)\
            .filter(Match.start_time < tomorrow)\
            .all()

        if len(matches) == 0:
            return True
        
        for m in matches:
            if not m.match_state.is_finished():
                return False
            
        return True