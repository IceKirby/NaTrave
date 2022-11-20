from datetime import date
from MatchData import Match as MatchData
from DB import db_session
from Models import Match, Thread, MatchPeriod, Sub, PendingUnpin, SuggestedSort
from ScheduleSources.ScheduleMatch import ScheduleState
from MatchSources.BaseSource import MatchPeriod
from datetime import datetime, timedelta, timezone
from collections import namedtuple
from ErrorPrinter import print_error
from sqlalchemy import or_
from prawcore.exceptions import Forbidden
from FormattingData.PostTemplate import simple_post_match_template
import BotUtils
import Scheduler
import Redditor
import SubLockManager

ongoing_matches = {}

def clear_match_objects():
    global ongoing_matches
    
    to_pop = []
    for id,match in ongoing_matches.items():
        if match.is_finished:
            to_pop.append(id)
    
    for p in to_pop:
        if p in ongoing_matches:
            ongoing_matches.pop(p)

# Changes Matches and Threads's state from upcoming to pre_match 60 minutes before kick-off
def start_pre_match():
    now = BotUtils.now()
    
    with db_session() as s:
        matches = s.query(Match, Thread)\
            .join(Thread)\
            .filter(Match.match_state == MatchPeriod.upcoming)\
            .filter(now >= Match.start_time - timedelta(minutes=60))\
            .all()
            
        for (match, thread) in matches:
            match.match_state = MatchPeriod.pre_match
            thread.state = MatchPeriod.pre_match
    
    if not s.success:
        print_error(s.error)

# Updates all ongoing match threads
def run_matches():
    with db_session() as s:
        # Finds active threads, as well as its respective Matches and Subs
        ongoing = s.query(Thread, Match, Sub)\
            .join(Match)\
            .join(Sub)\
            .filter(Thread.url != None)\
            .filter(or_(
                Match.ge_url != None,
                Match.s365_url != None,
            ))\
            .filter(Thread.state > MatchPeriod.upcoming)\
            .filter(Thread.state < MatchPeriod.post_match)\
            .filter(Sub.locked == False)\
            .all()
        
        if len(ongoing) == 0:
            return
        
        # Runs run_match_data on all matches in ongoing state
        execute_match_and_threads(s, ongoing, run_match_data)
    
    if not s.success:
        print_error(s.error)

# Marks matches as finished and update them one last time a few minutes after finished
def finish_matches():
    with db_session() as s:
        # Finds threads at post-match, as well as its respective Matches and Subs
        finished = s.query(Thread, Match, Sub)\
            .join(Match)\
            .join(Sub)\
            .filter(Thread.state == MatchPeriod.post_match)\
            .filter(Thread.post_match_thread != None)\
            .filter(or_(
                Match.ge_url != None,
                Match.s365_url != None,
            ))\
            .filter(Sub.locked == False)\
            .all()
        
        if len(finished) == 0:
            return
        
        # Runs finish_match_data on all matches in finished
        execute_match_and_threads(s, finished, finish_match_data)
    
    if not s.success:
        print_error(s.error)

# Finishes matches that don't contain any source URL
def finish_untracked_matches():
    now = BotUtils.now()
    
    with db_session() as s:
        # Finds threads at post-match, as well as its respective Matches and Subs
        pending = s.query(Thread, Match, Sub)\
            .join(Match)\
            .join(Sub)\
            .filter(Thread.url != None)\
            .filter(Match.match_state != MatchPeriod.finished)\
            .filter(Match.ge_url == None)\
            .filter(Match.s365_url == None)\
            .filter(now >= Match.start_time + timedelta(minutes=120))\
            .filter(Sub.locked == False)\
            .all()
        
        
        if len(pending) == 0:
            return
        
        # Runs finish_match_data on all matches in finished
        for (thread, match, sub) in pending:
            schedule_data = Scheduler.find_match(match.start_time, match.home_team, match.away_team)
            if schedule_data.state == ScheduleState.finished:
                match.match_state = MatchPeriod.finished
                match.end_time = now
                match.score = schedule_data.get_score()
                
                finish_untracked_match(s, schedule_data, thread, match, sub)
    
    if not s.success:
        print_error(s.error)
    
# Creates Post-Match Thread for matches without a Match Thread
def run_isolated_post_match(s, match, thread, sub):
    match_data = get_or_create_match_data(match.id)
    if match_data.update_data():
        title = match_data.print_post_match_title(sub, match)
        text = match_data.print_post_match(thread.url)
        finish_thread(s, None, sub, title, text)

# Update a single match and all its related threads
def run_match_data(s, match, thread_set):
    half_time_stats = None
    db_match = thread_set[0].match
    now = BotUtils.now()
    
    # Update match data
    if not match.update_data([db_match.ge_url, db_match.s365_url]):
        return
    
    # Update score on DB
    db_match.score = match.get_final_score()
    
    # Update Match state
    match_period = match.get_match_period()
    if db_match.match_state != match_period:
        db_match.match_state = match_period
    
    # Mark match as finished if needed
    if match_period.is_finished():
        db_match.match_state = MatchPeriod.post_match
        db_match.end_time = now
    
    # Get match stats during half-time and before extra-time and penalties
    breaks_with_stats = [MatchPeriod.interval, MatchPeriod.preparing_extra_time, MatchPeriod.preparing_penalties]
    if match_period in breaks_with_stats and match_period > db_match.last_stats_period:
        half_time_stats = match.get_match_stats()
        if half_time_stats:
            db_match.last_stats_period = match_period
    
    # Updates content for each thread
    for (thread, match_db, sub) in thread_set:
        # Update Thread period (only if match not finished; if finished, this will be handled by the run_post_match_thread function)
        if not match_period.is_finished() and thread.state != match_period:
            thread.state = match_period
        
        # Create Post-Match Thread
        if match_period.is_finished():
            run_post_match_thread(s, match, db_match, thread, sub)
        
        # Update thread's content
        update_match_thread(thread, match, db_match)
        
        # Post Match Stats as a comment during Half-Time
        if half_time_stats and sub.half_time_stats:
            post_half_time_stats(thread, half_time_stats)

# Finish a single match and all its related threads
def finish_match_data(s, match, thread_set):
    now = BotUtils.now()
    db_match = thread_set[0].match
    
    # Update post-match threads every 5 minutes after match ends (up to 60 minutes)
    update_threshold = 65 - (5 * db_match.post_match_updates)
    if now < db_match.end_time + timedelta(minutes=update_threshold):
        return
    
    # Updated threads if there was an update to MatchData
    if match.update_data([db_match.ge_url, db_match.s365_url]):
        for (thread, match_db, sub) in thread_set:
            # Update Match Thread if needed
            update_match_thread(thread, match, db_match)
            
            # Skip thread without post-match
            if not thread.post_match_thread:
                continue
                
            try:
                # Get thread id
                thread_id = Redditor.url_to_thread_id(thread.post_match_thread)
                
                # Update thread's content
                Redditor.update_thread({
                    "id": thread_id,
                    "text": match.print_post_match(thread.url)
                })
            except Exception as e:
                print_error(e)
                continue
    
    # Tick down the counter
    db_match.post_match_updates -= 1
    
    # Mark match as finished
    if db_match.post_match_updates == 0:
        db_match.match_state = MatchPeriod.finished
        match.is_finished = True
        
        # Mark Threads as finished too
        for (thread, match_db, sub) in thread_set:
            thread.state = MatchPeriod.finished
        

def finish_untracked_match(s, schedule_data, thread, match, sub):
    title = schedule_data.get_post_title(sub.post_title)
    text = schedule_data.get_post_content(simple_post_match_template, thread.url)
    finish_thread(s, thread, sub, title, text)

# Gets a list of matches, groups them with their respective threads/subs and 
# run operator function on each of them
def execute_match_and_threads(s, thread_list, operator):
    # Maps matches with its corresponding threads and subs
    match_sets = group_match_thread_subs(thread_list)
    
    # Updates Match Threads
    for match,thread_set in match_sets.items():
        try:
            # Execute function on all matches/threads
            operator(s, match, thread_set)
        except Exception as e:
            print_error(e)

# Updates content for a single match thread
def update_match_thread(thread, match_data, match_db):
    try:
        if not thread.url:
            return
        # Get thread if according to Reddit API
        thread_id = Redditor.url_to_thread_id(thread.url)
        
        # Format text for thread's content
        text = match_data.print_match(thread_id, thread.post_match_thread)
        
        # Actually update the thread's content
        Redditor.update_thread({
            "id": thread_id,
            "text": text
        })
    except Exception as e:
        print_error(e)

# Post Half-Match stats to a thread as a comment
def post_half_time_stats(thread, stats_text):
    try:
        t_id = Redditor.url_to_thread_id(thread.url)
        Redditor.post_comment({
            "thread": t_id,
            "text": stats_text
        })
    except Exception as e:
        print_error(e)

# Creates Post-Match Thread and associates it with its respective match thread
def run_post_match_thread(s, match, db_match, thread, sub):
    title = match.print_post_match_title(sub.post_title, db_match)
    text = match.print_post_match(thread.url)
    finish_thread(s, thread, sub, title, text)

def finish_thread(s, thread, sub, title, text):
    now = BotUtils.now()
    
    # Sets unpin timer for Match Thread
    if thread and sub.pin_match:
        unpin = PendingUnpin(url=thread.url, date=now + timedelta(hours=sub.unpin_match))
        s.add(unpin)
    
    # Check if subreddit's settings allow for Post-Match Thread
    if thread and not sub.post_match:
        thread.state = MatchPeriod.finished
        return
    
    try:
        # Create Thread
        submission_url = Redditor.create_thread({
            "sub": sub.sub_name,
            "title": title,
            "text": text,
            "flair": None if sub.post_match_flair == None else sub.post_match_flair
        })
    except Forbidden as e:
        print("403 Token, Source: Create Post-Match Thread")
        SubLockManager.add_forbidden_access_count(sub.sub_name)
        return
    except Exception as e:
        print_error(e)
        return
    
    # Save thread's URL
    if thread:
        thread.post_match_thread = submission_url
        thread.state = MatchPeriod.post_match
    
    # Sets suggested sort for thread
    if sub.post_sort != SuggestedSort.blank:
        Redditor.set_thread_sort(Redditor.url_to_thread_id(submission_url), sub.post_sort.name)
    
    # Pins Post-Match Thread and sets timer for unpin
    if sub.pin_post:
        Redditor.set_thread_sticky(Redditor.url_to_thread_id(submission_url))
        
        unpin = PendingUnpin(url=submission_url, date=now + timedelta(hours=sub.unpin_post))
        s.add(unpin)

def get_or_create_match_data(id):
    if is_match_ongoing(id):
        return ongoing_matches[id]
    else:
        with db_session() as s:
            match = s.query(Match).filter(Match.id == id).first()
            
            if match:
                match_data = MatchData([match.ge_url, match.s365_url])
                ongoing_matches[match.id] = match_data
                return match_data
        
        if not s.success:
            print_error(s.error)
    
    return None

def is_match_ongoing(id):
    return id in ongoing_matches

# Groups together a Thread with its respective Match and Sub
ThreadSet = namedtuple('ThreadSet', 'thread match sub')

# Associates a Match with its DB Entry, plus its corresponding Threads/Subs
def group_match_thread_subs(ongoing):
    match_sets = {}
    
    for (thread, match, sub) in ongoing:
        # Retrieve the MatchData for this match, creating it if needed
        match_data = get_or_create_match_data(match.id)
        if not match_data in match_sets:
            match_sets[match_data] = []
        
        # Associates Thread, DB_Match and Sub to MatchData
        match_sets[match_data].append(ThreadSet(
            thread = thread,
            match = match,
            sub = sub
        ))
    return match_sets
