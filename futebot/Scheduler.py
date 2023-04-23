import re
import Redditor
import PMResponse
import BotUtils
import SchedulerHelpers
import SubLockManager
import MatchManager
from ErrorPrinter import print_error
from psycopg2.errors import UniqueViolation
from prawcore.exceptions import Forbidden
from sqlalchemy import or_, and_
from Models import Match, Thread, Sub, Request, MatchPeriod, Follow, PendingUnpin, SuggestedSort
from DB import db_session
from datetime import datetime, timedelta, timezone
from FormattingData.PostTemplate import match_no_info
from ScheduleSources.ScheduleGE import ScheduleGE
from ScheduleSources.Schedule365Scores import Schedule365Scores
from ScheduleSources.ScheduleMatch import ScheduleState

scheduleGE = ScheduleGE()
schedule365 = Schedule365Scores()

def clear_cached():
    scheduleGE.clear_cached()
    schedule365.clear_cached()

def request_match(author, sub_name, lines, pm, silent=False):
    # Parse the PM
    requested_date, matches = parse_match_request(lines)

    # Check if a valid result was found
    if matches == None:
        PMResponse.add_response(author, "request_match_invalid_format", sub_name, pm)
        return True

    # Find requested matches on GE Agenda or 365Scores
    try:
        found_matches = find_requested_matches(requested_date, matches)
    except Exception as e:
        print_error(e)
        return False
    
    if len(found_matches) == 0:
        PMResponse.add_response(author, "request_match_no_match", sub_name, pm)
        return True
    
    # Creates Match, Thread and Request entries on database
    with db_session() as s:
        # Get sub info
        sub = s.query(Sub).filter(Sub.sub_name.ilike(sub_name)).first()
        
        all_matches = []
        all_threads = []
        all_requests = []
        
        for req in found_matches:
            # Get Match's kick-off time
            start_time = datetime.strptime(req.date + " " + req.time, "%Y-%m-%d %H:%M:%S")
            
            # Create/Get Match entry from DB
            match = SchedulerHelpers.find_or_create_db_match(s, req, start_time)
            all_matches.append(match)
            
            # Create/Get Thread entry from DB
            thread = SchedulerHelpers.find_or_create_db_thread(s, match, sub, start_time)
            all_threads.append(thread)
            
            # Check if Request is already in DB
            request = SchedulerHelpers.find_or_create_db_request(s, thread, author, silent)
            all_requests.append(request)
        
        # Formats list of matches for PM response
        requested_data = get_match_list_response(all_matches, all_threads, sub_name)
    
    if s.success:
        PMResponse.add_response(author, "request_match_success", requested_data, pm)
        return True
    else:
        if s.db_error and isinstance(s.db_error, UniqueViolation):
            print_error(s.db_error)
            PMResponse.add_response(author, "request_match_error", sub_name, pm)
        else:
            print_error(s.error)
            PMResponse.add_response(author, "request_match_error", sub_name, pm)
        return True

def request_match_silent(author, sub_name, lines, pm):
    return request_match(author, sub_name, lines, pm, True)
    

def abort_match_thread(author, sub_name, lines, pm):
    # Parse the PM
    requested_date, matches = parse_match_request(lines)

    # Check if a valid result was found
    if matches == None:
        PMResponse.add_response(author, "abort_match_invalid_format", sub_name, pm)
        return True

    # Find requested matches on GE Agenda or 365Scores
    try:
        found_matches = find_requested_matches(requested_date, matches)
    except Exception as e:
        print_error(e)
        return False
    
    if len(found_matches) == 0:
        PMResponse.add_response(author, "request_match_no_match", sub_name, pm)
        return True
        
    # Finds match entry and thread to abort
    with db_session() as s:
        # Get sub info
        sub = s.query(Sub).filter(Sub.sub_name.ilike(sub_name)).first()
        
        all_matches = []
        all_threads = []
        
        # Check each requested match
        for req in found_matches:
            # Get Match's kick-off time
            start_time = datetime.strptime(req.date + " " + req.time, "%Y-%m-%d %H:%M:%S")
            match = SchedulerHelpers.find_db_match(s, req, start_time)
            
            if match:
                thread = SchedulerHelpers.find_db_thread(s, match, sub)
                
                if thread:
                    thread.state = MatchPeriod.finished
                    all_matches.append(match)
                    all_threads.append(thread)
        
        # Formats list of matches for PM response
        requested_data = get_match_list_response(all_matches, all_threads, sub_name)
    
    if s.success:
        PMResponse.add_response(author, "abort_match_success", requested_data, pm)
        return True
    else:
        print_error(s.error)
        PMResponse.add_response(author, "abort_match_error", sub_name, pm)
        return True

def schedule_follows():
    today = BotUtils.today().strftime("%Y-%m-%d")
    
    with db_session() as s:
        follows = s.query(Follow, Sub)\
            .join(Sub)\
            .all()
        
        try:
            found_matches = []
            for follow,sub in follows:
                res = scheduleGE.find_followed_match(today, follow.team, follow.tour)
                if res == None:
                    return False
                    
                if len(res) > 0:
                    for sch in res:
                        # Ignore if no date or time found
                        if not res.date or not res.time:
                            continue
                        
                        # Get Match's kick-off time
                        start_time = datetime.strptime(sch.date + " " + sch.time, "%Y-%m-%d %H:%M:%S")
                        
                        # Create/Get Match entry from DB
                        match = SchedulerHelpers.find_or_create_db_match(s, sch, start_time)
                        
                        # Create/Get Thread entry from DB
                        thread = SchedulerHelpers.find_or_create_db_thread(s, match, sub, start_time)
                    
                    follow.last_used = today
                    
        except Exception as e:
            print_error(e)
            return False
    
    if not s.success:
        print_error(s.error)
        return False
    else:
        return True

def find_match_links():
    with db_session() as s:
        # Find matches without links that already started or are about to start 
        now = BotUtils.now()
        today = BotUtils.today()
        matches = s.query(Match)\
            .filter(now >= Match.start_time - timedelta(minutes=60))\
            .filter(Match.start_time >= today)\
            .filter(or_(
                Match.ge_url == None,
                Match.s365_url == None
            ))\
            .all()
        
        if len(matches) == 0:
            return
        
        try:
            # Today's date formatted as a string for the Schedule objects
            today = now.strftime("%Y-%m-%d")
            for m in matches:
                fill_match_links(m, today)
        except Exception as e:
            print_error(e)
        
    if not s.success:
        print_error(s.error)

def find_match(day, home_team, away_team):
    today = day.strftime("%Y-%m-%d")
    
    res = scheduleGE.find_match(today, home_team, away_team)
    if res:
        return res
    
    res = schedule365.find_match(today, home_team, away_team)
    if res:
        return res
    
    return None

def find_requested_matches(day, matches):
    found_matches = []
    for m in matches:
        res = find_match(day, m["home"], m["away"])
        if res and res.state != ScheduleState.finished:
            found_matches.append(res)
    return found_matches
    
def create_match_threads():
    now = BotUtils.now()
    with db_session() as s:
        pending = s.query(Thread, Match, Sub)\
            .join(Match)\
            .join(Sub)\
            .filter(Thread.url == None)\
            .filter(Thread.creation_time <= now)\
            .filter(Thread.state != MatchPeriod.finished)\
            .filter(Sub.locked == False)\
            .all()
            
        if len(pending) == 0:
            return
        
        # Use data from Threads, Matches and Subs to create Match Thread
        for (thread, match, sub) in pending:
            try:
                sch = find_match(match.start_time, match.home_team, match.away_team) 
                # Check if match was cancelled/postponed before the thread was created 
                if sch and sch.is_aborted: 
                    match.match_state = MatchPeriod.finished 
                    match.postponed = True 
                    thread.state = MatchPeriod.finished 
                    continue 
                 
                # Skip directly to Post-Match Thread if match started and finished while the bot was offline 
                if now > match.start_time + timedelta(minutes=105):
                    if sch and sch.state == ScheduleState.finished:
                        skip_to_post_match(s, sch, match, thread, sub)
                        continue
                
                # Create Match Thread
                url = create_base_thread(thread, match, sub)
                if url:
                    thread.url = url
                    
                    if sub.match_sort != SuggestedSort.blank:
                        Redditor.set_thread_sort(Redditor.url_to_thread_id(url), sub.match_sort.name)
                    
                    if sub.pin_match:
                        Redditor.set_thread_sticky(Redditor.url_to_thread_id(url))
                    
                    alert_requesters(s, thread, match, sub.sub_name)
            except Exception as e:
                print_error(e)
    
    if not s.success:
        print_error(s.error)

def find_aborted_matches():
    with db_session() as s:
        # Find matches 1 hour past its starting time that still didn't begin
        now = BotUtils.now()
        matches = s.query(Match, Thread)\
            .join(Thread)\
            .filter(now >= Match.start_time + timedelta(minutes=60))\
            .filter(Match.match_state <= MatchPeriod.pre_match)\
            .all()
        
        if len(matches) == 0:
            return
        
        for m,t in matches:
            try:
                res = find_match(now, m.home_team, m.away_team)
                if not res or res.is_aborted:
                    m.match_state = MatchPeriod.finished
                    m.postponed = True
                    t.state = MatchPeriod.finished
                    
            except Exception as e:
                print_error(e)
        
    if not s.success:
        print_error(s.error)

# Fills the 'score' column for Match DB entries that are already finished but 
# don't have that information registered
def get_finished_scores():
    today = BotUtils.today()
    
    with db_session() as s:
        matches = s.query(Match)\
            .filter(Match.match_state >= MatchPeriod.post_match)\
            .filter(or_(
                Match.score == None,
                Match.score == "x"
            ))\
            .all()
        
        if len(matches) == 0:
            return
        
        for m in matches:
            if m.ge_url or m.s365_url:
                match_data = MatchManager.get_or_create_match_data(m.id)
                if not match_data:
                    continue
                match_data.update_data([m.ge_url, m.s365_url])
                m.score = match_data.get_final_score()
            
    if not s.success:
        print_error(s.error)

def clear_old_matches():
    today = BotUtils.today()
    yesterday = BotUtils.yesterday()
    
    with db_session() as s:
        old = s.query(Match)\
            .filter(or_(
                and_(
                    Match.start_time < today,
                    Match.match_state == MatchPeriod.finished
                ),
                Match.start_time < yesterday
            ))\
            .delete(synchronize_session=False)
    
    if not s.success:
        print_error(s.error)

def unpin_threads():
    with db_session() as s:
        # Find threads that are already past their unpinning date
        now = BotUtils.now()
        threads = s.query(PendingUnpin)\
            .filter(now >= PendingUnpin.date)\
            .all()
        
        if len(threads) == 0:
            return
        
        # Unpin thread and remove unpin reminder from DB
        for t in threads:
            try:
                Redditor.set_thread_sticky(Redditor.url_to_thread_id(t.url), False)
                s.delete(t)
            except Exception as e:
                print_error(e)
        
    if not s.success:
        print_error(s.error)

def create_base_thread(thread_data, match_data, sub_data):
    title = BotUtils.format_str(sub_data.match_title,
        Campeonato=match_data.tournament,
        TimeCasa=match_data.home_team,
        Mandante=match_data.home_team,
        TimeFora=match_data.away_team,
        Visitante=match_data.away_team,
        Data=match_data.start_time.strftime('%d/%m/%Y'),
        Horario=match_data.start_time.strftime('%H:%M')
    )
    text = BotUtils.format_str(match_no_info,
        Campeonato=match_data.tournament.strip(),
        TimeCasa=match_data.home_team.strip(),
        TimeFora=match_data.away_team.strip(),
        Data=match_data.start_time.strftime('%d/%m/%Y'),
        Horario=match_data.start_time.strftime('%H:%M')
    )
    flair = None if sub_data.match_flair == None else sub_data.match_flair
    try:
        submission_url = Redditor.create_thread({
            "sub": sub_data.sub_name,
            "title": title,
            "text": text,
            "flair": flair
        })
        return submission_url
    except Forbidden as e:
        print("403 Token, Source: Create Match Thread")
        SubLockManager.add_forbidden_access_count(sub_data.sub_name)
        return None
    except Exception as e:
        print_error(e)
        return None

# Finds and assigns URL for match
def fill_match_links(match, day):
    # Looks for match at GE, and assigns its URL if found
    is_youth_match = None
    is_women_match = None
    if match.ge_url == None:
        res = scheduleGE.find_match(day, match.home_team, match.away_team)
        if res:
            if res.url:
                match.ge_url = res.url
            is_youth_match = res.is_youth_match
            is_women_match = res.is_women_match
    
    # Looks for match at 365Scores, and assigns its URL if found
    if match.s365_url == None:
        # res = schedule365.find_match(day, match.home_team, match.away_team)
        res = schedule365.find_match(day, match.home_team, match.away_team, is_youth_match, is_women_match)
        if res and res.url:
            match.s365_url = res.url

# Marks Match and Thread as finished and creates Post-Match thread
def skip_to_post_match(s, schedule, match, thread, sub):
    fill_match_links(match, match.start_time.strftime("%Y-%m-%d"))
    
    match.state = MatchPeriod.finished
    match.score = schedule.get_score()
    thread.url = None
    thread.state = MatchPeriod.finished
    
    if sub.post_match:
        MatchManager.run_isolated_post_match(s, match, thread, sub)
    
def alert_requesters(s, thread, match, sub_name):
    requesters = s.query(Request)\
        .filter(Request.thread == thread.id)\
        .all()
    
    for r in requesters:
        requested_data = { 
            "match_id": match.id,
            "sub": sub_name,
            "home": match.home_team,
            "away": match.away_team,
            "tour": match.tournament,
            "time": BotUtils.to_datetime(match.start_time),
            "thread_time": BotUtils.to_datetime(thread.creation_time),
            "url": thread.url
        }
        if r.alert:
            PMResponse.add_response(r.name, "requested_match_created", requested_data, None)
        else:
            PMResponse.add_response(r.name, "requested_match_created_silent", requested_data, None)
            
        s.delete(r)

def get_match_list_response(matches, threads, sub_name):
    result = []
    
    for t in threads:
        for m in matches:
            if t.match_id == m.id:
                result.append({
                    "match_id": m.id,
                    "sub": sub_name,
                    "home": m.home_team,
                    "away": m.away_team,
                    "tour": m.tournament,
                    "time": BotUtils.to_datetime(m.start_time),
                    "thread_time": BotUtils.to_datetime(t.creation_time),
                    "url": t.url
                })
                continue
    
    return result

def parse_match_request(lines):
    matches, date = [], None
    date_re = r"[0-9]{1,2}\/[0-9]{1,2}(\/[0-9]{2,4})?"
    match_re = r"(.+)\s(vs|x)\s(.+)"

    for x in lines:
        line = x.strip()
        if date == None and re.match(date_re, line):
            date = line
            continue
        has_match = re.search(match_re, line, re.IGNORECASE)
        if has_match:
            matches.append({
                "home": has_match.group(1),
                "away": has_match.group(3)
            })

    if len(matches) > 0:
        if date == None:
            date = "0/0"
        date = BotUtils.convert_date(date)
        return date, matches
    return None, None
