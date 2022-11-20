import BotUtils
import PMResponse
from DB import db_session
from Models import Sub
from datetime import datetime, timedelta
from ErrorPrinter import print_error

token_cooldown = 60
auto_lock_limit = 8
forbidden_access_log = []

class ForbiddenAccessToken:
    def __init__(self, sub, date):
        self.sub = sub
        self.date = date
    
    def __repr__(self):
        return "<ForbiddenAccessToken (sub_name='{}', date='{}')>"\
                .format(self.sub, self.date)

def add_forbidden_access_count(subname):
    subname = BotUtils.format_sub_name(subname).lower()
    now = BotUtils.now()
    
    token = ForbiddenAccessToken(subname, now)
    last = get_latest_token(subname)
    
    if not last or now > last.date + timedelta(seconds=token_cooldown):
        print("Adding 403 Token:", subname, now)
        forbidden_access_log.append(token)

def clear_old_tokens():
    one_hour_ago = BotUtils.now() - timedelta(hours=1)
    
    global forbidden_access_log
    forbidden_access_log = list(filter(lambda token: token.date > one_hour_ago, forbidden_access_log))

def check_for_locks():
    global forbidden_access_log
    subs_count = {}
    locked_list = []
    
    for t in forbidden_access_log:
        if not t.sub in subs_count:
            subs_count[t.sub] = 0
        subs_count[t.sub] += 1
    
    for sub,value in subs_count.items():
        if value >= auto_lock_limit:
            locked_list.append(sub)
            lock_sub(sub)
    
    if len(locked_list) > 0:
        forbidden_access_log = list(filter(lambda token: token.sub not in locked_list, forbidden_access_log))

def lock_sub(subname):
    # Mark sub as locked
    with db_session() as s:
        sub = s.query(Sub).filter(Sub.sub_name.ilike(subname)).first()
        if sub:
            sub.locked = True
    
    if s.success:
        PMResponse.add_response("r/"+subname, "sub_locked", subname, None)
    else:
        print_error(s.error)
    

def get_latest_token(subname):
    latest = None
    latest_date = None
    for t in forbidden_access_log:
        if t.sub == subname:
            if latest_date == None or t.date > latest_date:
                latest_date = t.date
                latest = t
    return latest
