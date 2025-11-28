import MatchManager
import Redditor
import BotUtils
import SubLockManager
from ErrorPrinter import print_error
from Models import Sub, Match, Thread, MatchPeriod, Hub, SuggestedSort, PendingUnpin
from FormattingData.PostTemplate import hub_template, hub_tour_group_template, hub_match_template, hub_match_creation_template, hub_match_postponed_template, hub_match_link_untracked, hub_previous_link
from datetime import timedelta
from sqlalchemy import or_
from prawcore.exceptions import Forbidden

class FollowedThread:
    def __init__(self, thread, match):
        self.thread_id = thread.id
        self.match_id = match.id
        self.score = match.score
        self.state = thread.state
        self.url = thread.url
        self.hub_only = thread.hub_only
        self.post_url = thread.post_match_thread
        

class HubData:
    def __init__(self, sub, date, thread_url):
        self.sub = sub
        self.date = date
        self.thread_url = thread_url
        self.threads = []
        self.needs_update = True
        self.pending_creation = False
    
    def find_tracked_matches(self, s):
        today = self.date
        tomorrow = self.date + timedelta(days=1)
        
        threads = s.query(Thread, Match)\
            .join(Match)\
            .filter(Thread.sub == self.sub)\
            .filter(Match.start_time > today)\
            .filter(Match.start_time < tomorrow)\
            .all()
        
        found = []
        for t,m in threads:
            f = FollowedThread(t, m)
            found.append(f)
        
        self.needs_update = self.was_changed(found)
        self.threads = found
    
    def create_thread(self, s, hub, sub):
        self.pending_creation = True
        text = self.get_thread_content(s, sub, hub.date)
        today = BotUtils.today()
        tomorrow = BotUtils.tomorrow()
        url = self.create_base_thread(sub, text, today)
        
        if url:
            self.pending_creation = False
            hub.url = url
            self.url = url
            
            if sub.hub_sort != SuggestedSort.blank:
                Redditor.set_thread_sort(Redditor.url_to_thread_id(url), sub.hub_sort.name)
            
            if sub.pin_hub:
                Redditor.set_thread_sticky(Redditor.url_to_thread_id(url))
            
                # Sets unpin timer for Hub Thread
                unpin_time = tomorrow + timedelta(hours=sub.unpin_hub)
                unpin = PendingUnpin(url=url, date=unpin_time)
                s.add(unpin)
        
    def update_thread(self, s, hub, sub):
        try:
            text = self.get_thread_content(s, sub, hub.date)
            
            # Get thread if according to Reddit API
            thread_id = Redditor.url_to_thread_id(hub.url)
            
            # Actually update the thread's content
            Redditor.update_thread({
                "id": thread_id,
                "text": text
            })
        except Exception as e:
            print_error(e)
    
    def was_changed(self, new_list):
        new_list.sort(key=lambda ft: ft.thread_id)
        old_list = self.threads
        
        if len(new_list) != len(old_list):
            return True
        
        for index in range(len(new_list)):
            new_item = new_list[index]
            old_item = old_list[index]
            
            if old_item.thread_id != new_item.thread_id:
                return True
            
            if old_item.state != new_item.state:
                return True
            
            if old_item.url != new_item.url:
                return True
            
            if old_item.post_url != new_item.post_url:
                return True
                
            if old_item.score != new_item.score:
                return True
            
        return False
    
    def get_thread_content(self, s, sub, date):
        ids = list(map(lambda t: t.thread_id, self.threads))
        
        threads = s.query(Thread, Match)\
            .join(Match)\
            .filter(Thread.id.in_(ids))\
            .all()
        
        tour_groups = self.group_threads_by_tour(threads)
        tours_text = self.format_tour_groups(tour_groups)


        prev_hub = self.find_previous_hub(s, sub, date)
        prev_hub_line = ""
        if prev_hub:
            prev_hub_line = BotUtils.format_str(hub_previous_link,
                Data=BotUtils.translate_date(prev_hub.date, False),
                Link=prev_hub.url
            )
        
        instr_link = "https://www.reddit.com/r/NaTrave/wiki/requisitar"
        if sub.instructions_link:
            instr_link = sub.instructions_link
        
        text = BotUtils.format_str(hub_template,
            Sub=sub.sub_name,
            Torneios=tours_text,
            HubAnterior=prev_hub_line,
            InstructionsLink=instr_link
        )
        
        return text
    
    def find_previous_hub(self, s, sub, current_date):
        prev_hub = s.query(Hub)\
            .filter(Hub.sub == sub.id)\
            .filter(Hub.date < current_date)\
            .filter(Hub.url != None)\
            .order_by(Hub.date.desc())\
            .first()
        
        return prev_hub

    def is_hub_finished(self):
        today = BotUtils.today()
        
        if self.date >= today:
            return False
        
        for t in self.threads:
            if t.state < MatchPeriod.finished:
                return False

        return True

    def create_base_thread(self, sub_data, text, today):
        title = BotUtils.format_str(sub_data.hub_title,
            Data=BotUtils.translate_date(today, False)
        )
        flair = None if sub_data.hub_flair == None else sub_data.hub_flair
        try:
            submission_url = Redditor.create_thread({
                "sub": sub_data.sub_name,
                "title": title,
                "text": text,
                "flair": flair
            })
            return submission_url
        except Forbidden as e:
            SubLockManager.add_forbidden_access_count(sub_data.sub_name)
            return None
        except Exception as e:
            print_error(e)
            return None
    
    def group_threads_by_tour(self, threads):
        tours = {}
        for data in threads:
            t = data[1].tournament
            
            if not t in tours:
                tours[t] = []
            
            tours[t].append(data)
        
        return tours
    
    def format_tour_groups(self, tours):
        groups = []
        
        order = list(tours.keys())
        order.sort(key=str.lower)
        
        for key in order:
            data = tours[key]
            text = BotUtils.format_str(hub_tour_group_template,
                Torneio=key,
                Partidas=self.list_matches(data)
            )
            groups.append(text)
        
        return "  \n  \n".join(groups)
    
    def list_matches(self, data):
        out = []
        
        data.sort(key=lambda match: match[1].start_time)
        
        for thread,match in data:
            out.append(self.format_match_line(thread, match))
        
        return "  \n".join(out)
        
    def format_match_line(self, thread, match):
        match_data = MatchManager.get_or_create_match_data(match.id)
        
        if match.postponed:
            state = "Adiado"
        elif match.match_state <= MatchPeriod.pre_match:
            state = match.start_time.strftime('%H:%M')
        elif match.match_state >= MatchPeriod.post_match:
            state = "Encerrado"
        else:
            state = "Em Andamento" if not match_data else match_data.get_moment_status()
        
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
        
        return BotUtils.format_str(hub_match_template,
            Estado=state,
            Mandante=match.home_team,
            Visitante=match.away_team,
            Placar=score,
            Links=links
        )
