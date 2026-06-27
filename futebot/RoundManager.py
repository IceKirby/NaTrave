from datetime import timedelta

import BotUtils
import Redditor
from RoundData import RoundData
from Models import Match, Thread, Round, Sub, SuggestedSort
from DB import db_session
from prawcore.exceptions import Forbidden
from praw.exceptions import RedditAPIException
from ErrorPrinter import print_error

ongoing_rounds = {}

# Removes old Hub entries from DB
def clear_old_rounds(cutoff):
    with db_session() as s:
        old = s.query(Round).filter(Round.date < cutoff).delete(synchronize_session=False)
    
    if not s.success:
        print_error(s.error)
    
    to_pop = []
    for id,round in ongoing_rounds.items():
        if round.date < cutoff:
            to_pop.append(id)
    
    for p in to_pop:
        if p in ongoing_rounds:
            ongoing_rounds.pop(p)

def create_round_threads():
    today = BotUtils.today()
    tomorrow = BotUtils.tomorrow()

    with db_session() as s:
        now = BotUtils.now()

        # Find Round Threads that need to be created
        rounds = s.query(Round, Sub)\
            .join(Sub)\
            .filter(now >= Round.date)\
            .filter(Round.url == None)\
            .all()
        
        if len(rounds) == 0:
            return
        
        try:
            for (round, sub) in rounds:
                url = create_base_thread(round.title, round.title, sub)

                if url:
                    round.url = url
                    
                    if sub.match_sort != SuggestedSort.blank:
                        Redditor.set_thread_sort(Redditor.url_to_thread_id(url), sub.match_sort.name)
                    
                    if sub.pin_match:
                        Redditor.set_thread_sticky(Redditor.url_to_thread_id(url))

                    if round.supress_match_threads:
                        matches = s.query(Match, Thread, Sub)\
                            .select_from(Match)\
                            .join(Thread)\
                            .join(Sub)\
                            .filter(Match.tournament == round.tournament)\
                            .filter(Match.start_time >= today)\
                            .filter(Match.start_time < tomorrow)\
                            .all()
                        
                        for m, t, s in matches:
                            t.hub_only = True
        except Exception as e:
            print_error(e)
        
    if not s.success:
        print_error(s.error)

def update_round_threads():
    with db_session() as s:
        now = BotUtils.now()

        # Find active Round Threads
        rounds = s.query(Round, Sub)\
            .join(Sub)\
            .filter(now >= Round.date)\
            .filter(Round.url != None)\
            .filter(Round.post_match_updates > 0)\
            .all()
        
        # Stop if no active Round Thread
        if len(rounds) == 0:
            return
        
        try:
            # Update Round Threads
            for (round, sub) in rounds:
                update_thread(round, sub, s)
        except Exception as e:
            print_error(e)
        
    if not s.success:
        print_error(s.error)

def create_base_thread(title, content, sub_data):
    placeholder_text = title

    flair = None if sub_data.match_flair == None else sub_data.match_flair

    try:
        submission_url = Redditor.create_thread({
            "sub": sub_data.sub_name,
            "title": content,
            "text": placeholder_text,
            "flair": flair
        })
        return submission_url
    except Forbidden as e:
        print("403 Token, Source: Create Round Thread")
        return None
    except RedditAPIException as e:
        for err in e.items:
            if err.error_type == "SUBREDDIT_NOTALLOWED":
                print("403 Token, Source: Create Round Thread")
        return None
    except Exception as e:
        print_error(e)
        return None

def update_thread(round_data, sub_data, s):
    if not round_data.id in ongoing_rounds:
        round = RoundData(sub_data, round_data)
        ongoing_rounds[round_data.id] = round
    round = ongoing_rounds[round_data.id]

    round.update_thread(s, round_data, sub_data)

    if round.is_finished(s) and not round_data.post_round_thread:
        post_url = create_base_thread(round_data.post_title, round_data.post_title, sub_data)
        if post_url:
            round_data.post_round_thread = post_url
            round_data.finished = True
            round_data.end_time = BotUtils.now()
            round.update_thread(s, round_data, sub_data)
            
    
    if round_data.post_round_thread and round_data.post_match_updates > 0:
        now = BotUtils.now()
        update_threshold = 65 - (5 * round_data.post_match_updates)
        if now >= round_data.end_time + timedelta(minutes=update_threshold):
            round.update_post_thread(s, round_data, sub_data)
            round_data.post_match_updates -= 1