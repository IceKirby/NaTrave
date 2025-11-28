from Models import Match, Thread, Request
from datetime import timedelta
from sqlalchemy import and_, or_

# MATCH FETCH FUNCTIONS
def find_or_create_db_match(s, req, start_time):
    # Check if Match is already in DB
    match = find_db_match(s, req, start_time)
    
    # Create Match DB entry if needed
    if not match:
        match = create_db_match(s, req, start_time)
    
    return match

def find_db_match(s, req, start_time):
    return s.query(Match).filter(
        Match.home_team == req.home_team,
        Match.away_team == req.away_team,
        Match.tournament == req.tour,
        Match.start_time == start_time
    ).first()

def create_db_match(s, req, start_time):
    match = Match(
        home_team=req.home_team,
        away_team=req.away_team,
        tournament=req.tour,
        start_time=start_time,
        ge_url=req.url if req.source == "GE" else None,
        s365_url=req.url if req.source == "365Scores" else None
    )
    s.add(match)
    return match

# THREAD FETCH FUNCTIONS
def find_or_create_db_thread(s, match, sub, start_time, with_thread):
    # Check if Thread is already in DB
    thread = find_db_thread(s, match, sub)

    if thread and with_thread == True:
        thread.hub_only = False
    
    # Create Thread DB entry if needed
    if not thread:
        thread = create_db_thread(s, match, sub, start_time, with_thread)
    
    return thread

def find_db_thread(s, match, sub):
    return s.query(Thread).filter(
        Thread.match_id == match.id,
        Thread.sub == sub.id
    ).first()

def create_db_thread(s, match, sub, start_time, with_thread):
    thread = Thread(
        sub=sub.id,
        match_id=match.id,
        creation_time=start_time - timedelta(minutes=sub.pre_match_time),
        hub_only=not with_thread
    )
    s.add(thread)
    return thread

# REQUEST FETCH FUNCTIONS
def find_or_create_db_request(s, thread, author, silent, with_thread):
    # Check if Request is already in DB
    request = find_db_request(s, thread, author)
    
    # Create Request DB entry if needed
    if not request:
        request = create_db_request(s, thread, author, with_thread)
    request.alert = not silent
    request.hub_only = not with_thread
    
    return request

def find_db_request(s, thread, author):
    return s.query(Request).filter(
        Request.thread == thread.id,
        Request.name == author
    ).first()

def create_db_request(s, thread, author, with_thread):
    request = Request(
        thread=thread.id,
        name=author
    )
    s.add(request)
    return request
