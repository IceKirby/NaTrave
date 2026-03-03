import BotUtils
import Redditor
from RoundData import RoundData
from Models import Round, Sub, SuggestedSort
from DB import db_session
from prawcore.exceptions import Forbidden
from praw.exceptions import RedditAPIException
from ErrorPrinter import print_error

ongoing_rounds = {}

def create_round_threads():
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
                url = create_base_thread(round, sub)

                if url:
                    round.url = url
                    
                    if sub.match_sort != SuggestedSort.blank:
                        Redditor.set_thread_sort(Redditor.url_to_thread_id(url), sub.match_sort.name)
                    
                    if sub.pin_match:
                        Redditor.set_thread_sticky(Redditor.url_to_thread_id(url))

                    if round.supress_match_threads:
                        # TODO
                        # Find Threads that this Round would contain
                        # Mark them as HUB only
                        pass
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
            .filter(Round.finished == False)\
            .all()
        
        # Stop if no active Round Thread
        if len(rounds) == 0:
            return
        
        try:
            # Update Round Threads
            for (round, sub) in rounds:
                update_thread(round, sub)
        except Exception as e:
            print_error(e)
        
    if not s.success:
        print_error(s.error)

def create_base_thread(round_data, sub_data):
    placeholder_text = round_data.title

    flair = None if sub_data.match_flair == None else sub_data.match_flair

    try:
        submission_url = Redditor.create_thread({
            "sub": sub_data.sub_name,
            "title": round_data.title,
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

def update_thread(round_data, sub_data):
    if not round_data.id in ongoing_rounds:
        round = RoundData(sub_data, round_data)
        ongoing_rounds[round_data.id] = round_data
    round = ongoing_rounds[round_data.id]

    round.update_thread()